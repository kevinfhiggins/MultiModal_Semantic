from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from typing import Optional
import os
from pathlib import Path

from .config import get_settings
from .database import init_database, close_database, get_database
from .embeddings import init_embeddings, get_embeddings
from .search import create_search_service
from .ingestion import DataIngestion
from .storage import resolve_file
from .transcription import transcribe_audio_file
from .pdf_pages import find_pages_with_text, get_pdf_page_count
from .models import (
    SearchRequest,
    SearchResponse,
    SearchTrailStep,
    HealthResponse,
    ConfigStatusResponse,
    Modality
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info("Starting MoD Semantic Search API...")
    try:
        init_database(settings)
        init_embeddings(settings)
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    close_database()


app = FastAPI(
    title="MoD Semantic Search API",
    description="Semantic search across multimodal military data (embeddings + file links)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve files with CORS headers for PDF.js.
# Files resolve from the local storage path, or are fetched from S3 on demand
# (see app/storage.py) when S3_BUCKET is configured.

@app.options("/files/{file_path:path}")
async def serve_file_options(file_path: str):
    """Handle CORS preflight for file serving"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/files/{file_path:path}")
async def serve_file(file_path: str):
    """Serve files with CORS headers for PDF.js compatibility"""
    from fastapi.responses import FileResponse
    full_path = resolve_file(settings, file_path)

    if full_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        full_path,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cross-Origin-Resource-Policy": "cross-origin",
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db = get_database()

    return HealthResponse(
        status="healthy",
        mongodb_connected=db.is_connected(),
        voyage_configured=bool(settings.voyage_api_key),
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/config-status", response_model=ConfigStatusResponse)
async def config_status():
    """Configuration status endpoint"""
    return ConfigStatusResponse(
        mongodb_uri_set=bool(settings.mongodb_uri),
        mongodb_database=settings.mongodb_database,
        mongodb_collection=settings.mongodb_collection,
        voyage_api_key_set=bool(settings.voyage_api_key),
        voyage_model=settings.voyage_model,
        vector_index_name=settings.vector_index_name,
        vector_dimension=settings.vector_dimension
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search endpoint with hybrid multimodal + text embeddings

    Accepts a natural language query and returns relevant documents
    from the MoD_Data collection using vector similarity search.
    """
    try:
        db = get_database()
        embeddings = get_embeddings()
        search_service = create_search_service(db, embeddings, settings)

        results = search_service.search(request)

        # Generate search info explanation
        image_count = sum(1 for r in results if r.modality == "image")
        text_count = len(results) - image_count

        if request.modality == Modality.IMAGE:
            search_info = "🎨 Image search using Voyage-3 embeddings (VLM caption matching)"
        elif request.modality in [Modality.PDF, Modality.AUDIO, Modality.VIDEO]:
            search_info = f"📄 Text search using Voyage-3 embeddings (semantic text matching)"
        else:
            search_info = f"🔄 Unified search: {image_count} images + {text_count} documents (all Voyage-3 embeddings)"

        # Build search trail
        trail = []
        trail.append(SearchTrailStep(
            label="Query",
            detail=f'"{request.query}"',
            icon="query"
        ))
        trail.append(SearchTrailStep(
            label="Embedding",
            detail="Voyage-3 multilingual (1024-dim vector, 100+ languages)",
            icon="embedding"
        ))

        num_candidates = max(200, request.top_k * 10)
        modality_label = request.modality.value if request.modality != Modality.ALL else "all modalities"
        trail.append(SearchTrailStep(
            label="Vector Search",
            detail=f"{num_candidates} candidates scanned across {modality_label} via cosine similarity",
            icon="search"
        ))

        if results:
            top_score = results[0].normalized_score or (results[0].score * 100 if results[0].score else 0)
            modalities_found = list(set(r.modality for r in results))
            trail.append(SearchTrailStep(
                label="Results",
                detail=f"{len(results)} matches returned (top confidence: {top_score:.0f}%) from {', '.join(modalities_found)}",
                icon="results"
            ))
        else:
            trail.append(SearchTrailStep(
                label="Results",
                detail="No matches found",
                icon="results"
            ))

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            modality_filter=request.modality.value if request.modality != Modality.ALL else None,
            search_info=search_info,
            search_trail=trail
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/pdf-pages/{document_id}")
async def get_pdf_pages(document_id: str, query: str):
    """
    Find pages in a PDF that contain the search query

    Args:
        document_id: MongoDB document _id
        query: Search query text

    Returns:
        List of matching pages with excerpts
    """
    try:
        db = get_database()

        # Get the PDF document from MongoDB
        from bson import ObjectId
        doc = db.collection.find_one({'_id': ObjectId(document_id)})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.get('modality') != 'pdf':
            raise HTTPException(status_code=400, detail="Document is not a PDF")

        # Find the PDF file path. Resolve via the storage layer (local first,
        # then S3 on demand), trying the stored relative path, the source
        # filename, and the uploads subdir.
        source_file = doc.get('source_file', '')
        stored_path = doc.get('file_path', '') or ''

        resolved = (
            (resolve_file(settings, stored_path) if stored_path else None)
            or resolve_file(settings, source_file)
            or resolve_file(settings, f"uploads/{source_file}")
        )

        # Last resort: an absolute path that happens to exist on this machine.
        if resolved is None and stored_path and Path(stored_path).is_absolute():
            p = Path(stored_path)
            if p.exists():
                resolved = p

        if resolved is None:
            raise HTTPException(status_code=404, detail="PDF file not found on disk")

        pdf_path = str(resolved)

        # Find matching pages
        matching_pages = find_pages_with_text(pdf_path, query)
        total_pages = get_pdf_page_count(pdf_path)

        return {
            "document_id": document_id,
            "source_file": source_file,
            "total_pages": total_pages,
            "matching_pages": matching_pages,
            "match_count": len(matching_pages)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF page extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract pages: {str(e)}")


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    modality: str = Form(...),
    tags: str = Form(""),
    caption: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None)
):
    """
    Manual document upload endpoint

    Allows users to upload documents with metadata through the frontend.
    """
    try:
        db = get_database()
        embeddings = get_embeddings()
        ingestion = DataIngestion(db, embeddings)

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Save uploaded file to uploads directory
        import os
        from pathlib import Path as FilePath

        uploads_dir = FilePath(settings.file_storage_path) / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        file_path = uploads_dir / file.filename

        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        try:
            # Process based on modality
            text_content = None
            transcript_text = None
            image_caption = None
            audio_duration = None

            if modality == "pdf":
                text_content = ingestion.extract_pdf_text(str(file_path))
            elif modality == "audio":
                # Auto-transcribe if no transcript provided
                if not transcript or transcript.strip() == "":
                    logger.info(f"Auto-transcribing audio: {file.filename}")
                    try:
                        transcription_result = transcribe_audio_file(str(file_path))
                        transcript_text = transcription_result['text']
                        audio_duration = transcription_result['duration']
                        logger.info(f"Transcription complete: {len(transcript_text)} characters")
                    except Exception as e:
                        logger.error(f"Auto-transcription failed: {e}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Audio transcription failed: {str(e)}. Please provide a manual transcript."
                        )
                else:
                    transcript_text = transcript
            elif modality == "image":
                image_caption = caption or ""
            elif modality == "video":
                # Video processing happens during ingestion (extracts audio + keyframes)
                logger.info(f"Processing video: {file.filename}")
                # No preprocessing needed - handled in ingestion._create_video_chunks
                pass

            # Generate file URL
            file_url = f"http://localhost:8000/files/uploads/{file.filename}"

            # Prepare metadata
            upload_metadata = {
                "uploaded_at": datetime.utcnow().isoformat(),
                "auto_transcribed": modality == "audio" and (not transcript or transcript.strip() == "")
            }
            if audio_duration:
                upload_metadata["duration"] = audio_duration

            # Ingest document (text content used for embedding only, not stored)
            doc_id = ingestion.ingest_document(
                title=title,
                modality=modality,
                source_file=file.filename,
                file_path=str(file_path),
                tags=tag_list,
                metadata=upload_metadata,
                text_content=text_content,
                transcript=transcript_text,
                image_caption=image_caption,
                file_url=file_url,
                stored_path=f"uploads/{file.filename}"
            )

            return JSONResponse(
                content={
                    "status": "success",
                    "document_id": doc_id,
                    "message": f"Document '{title}' uploaded successfully"
                }
            )

        finally:
            # File saved permanently, no cleanup needed
            pass

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents")
async def list_all_documents():
    """
    List all documents in the database

    Returns all documents with their metadata for browsing.
    """
    try:
        db = get_database()
        collection = db.collection

        # Retrieve all documents, excluding embeddings and audio_chunks
        documents = list(collection.find(
            {},
            {
                "_id": 1,
                "title": 1,
                "modality": 1,
                "source_file": 1,
                "file_url": 1,
                "tags": 1,
                "metadata": 1,
                "preview": 1,
                "ingested_at": 1
            }
        ))

        # Convert ObjectId to string
        for doc in documents:
            doc["_id"] = str(doc["_id"])

        return JSONResponse(
            content={
                "total": len(documents),
                "documents": documents
            }
        )

    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the database

    Removes the document and optionally its associated file.
    """
    try:
        from bson import ObjectId
        db = get_database()
        collection = db.collection

        # Find the document first to get file info
        doc = collection.find_one({"_id": ObjectId(document_id)})

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database
        result = collection.delete_one({"_id": ObjectId(document_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        # Optionally delete the file from disk
        if doc.get("metadata", {}).get("file_path"):
            file_path = doc["metadata"]["file_path"]
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")

        logger.info(f"Deleted document: {document_id} - {doc.get('title')}")

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Document '{doc.get('title')}' deleted successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MoD Semantic Search API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "config": "/config-status",
            "search": "POST /search",
            "upload": "POST /upload",
            "documents": "GET /documents"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
