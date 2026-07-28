import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from PyPDF2 import PdfReader

from .database import MongoDB
from .embeddings import VoyageEmbeddings
from .models import DocumentRecord
from .audio_processing import AudioChunker
from .video_processing import VideoProcessor
from .transcription import transcribe_audio_file
from .storage import resolve_file
from .config import get_settings

logger = logging.getLogger(__name__)


class DataIngestion:
    """Data ingestion service for multimodal documents"""

    def __init__(self, db: MongoDB, embeddings: VoyageEmbeddings):
        self.db = db
        self.embeddings = embeddings
        self.audio_chunker = AudioChunker(chunk_duration=15, overlap=3)
        self.video_processor = VideoProcessor(keyframe_interval=5)  # Extract frame every 5 seconds

    def ingest_document(
        self,
        title: str,
        modality: str,
        source_file: str,
        file_path: str,
        tags: List[str],
        metadata: Dict[str, Any],
        text_content: Optional[str] = None,
        transcript: Optional[str] = None,
        image_caption: Optional[str] = None,
        file_url: Optional[str] = None,
        stored_path: Optional[str] = None
    ) -> str:
        """
        Ingest a single document into MoD_Data collection

        Note: Only stores embeddings, metadata, and file references.
        Full text/transcript/caption are used for embedding generation then discarded.

        Args:
            title: Document title
            modality: Type (pdf, audio, image)
            source_file: Original filename
            file_path: Path to file on disk (used for processing; NOT stored)
            tags: List of tags
            metadata: Additional metadata
            text_content: Extracted text (for PDFs) - used for embedding only
            transcript: Audio transcript - used for embedding only
            image_caption: Image description - used for embedding only
            file_url: Optional URL to access the file
            stored_path: Portable path (relative to the storage root) to persist
                as the document's file_path. Defaults to source_file so the stored
                value is machine-independent rather than an absolute local path.

        Returns:
            Inserted document ID
        """

        # Determine searchable text based on modality
        searchable_text = self._get_searchable_text(
            modality=modality,
            text_content=text_content,
            transcript=transcript,
            image_caption=image_caption,
            title=title,
            tags=tags
        )

        # Generate embedding from searchable text
        embedding = self.embeddings.embed_text(searchable_text)

        # Create preview from searchable text
        preview = self._create_preview(searchable_text, max_length=200)

        # For audio files, create semantic chunks with individual embeddings
        audio_chunks = None
        video_chunks = None

        if modality == "audio" and transcript:
            audio_chunks = self._create_audio_chunks(transcript, metadata)

        # For video files, create multimodal chunks (audio + visual)
        if modality == "video":
            video_chunks = self._create_video_chunks(file_path, metadata)

        # Store a portable, machine-independent path (relative to the storage
        # root), not the absolute local path used for processing.
        record_path = stored_path if stored_path is not None else source_file

        # Build document record - NOTE: text_content, transcript, caption NOT stored
        doc = DocumentRecord(
            title=title,
            modality=modality,
            source_file=source_file,
            file_path=record_path,
            file_url=file_url,
            preview=preview,
            tags=tags,
            metadata=metadata,
            embedding=embedding,
            audio_chunks=audio_chunks,
            video_chunks=video_chunks,
            created_at=datetime.utcnow()
        )

        # Insert into MongoDB (only embeddings, metadata, and file reference)
        result = self.db.collection.insert_one(doc.dict())
        doc_id = str(result.inserted_id)

        logger.info(
            f"Ingested document: id={doc_id}, title='{title}', modality={modality}, "
            f"file_path={file_path}"
        )

        return doc_id

    def _get_searchable_text(
        self,
        modality: str,
        text_content: Optional[str],
        transcript: Optional[str],
        image_caption: Optional[str],
        title: str,
        tags: List[str]
    ) -> str:
        """Construct searchable text from available fields"""

        parts = [title]
        parts.extend(tags)

        if modality == "pdf" and text_content:
            parts.append(text_content)
        elif modality == "audio" and transcript:
            parts.append(transcript)
        elif modality == "image" and image_caption:
            parts.append(image_caption)

        return " ".join(parts)

    def _create_preview(self, text: str, max_length: int = 200) -> str:
        """Create preview snippet from text"""
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(" ", 1)[0] + "..."

    def _create_audio_chunks(
        self,
        transcript: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create semantic chunks with embeddings for audio transcript

        Args:
            transcript: Full transcript text
            metadata: Audio metadata (may contain duration)

        Returns:
            List of chunks with embeddings
        """
        logger.info("Creating semantic audio chunks...")

        # Get duration from metadata if available
        duration = metadata.get('duration')

        # Chunk the transcript
        chunks = self.audio_chunker.chunk_transcript_by_time(
            transcript=transcript,
            duration=duration
        )

        if not chunks:
            logger.warning("No chunks created from transcript")
            return []

        # Generate embeddings for each chunk
        chunk_texts = [chunk['text'] for chunk in chunks]
        chunk_embeddings = self.embeddings.embed_texts(chunk_texts)

        # Combine chunks with embeddings
        audio_chunks = []
        for chunk, chunk_embedding in zip(chunks, chunk_embeddings):
            audio_chunks.append({
                'start': chunk['start'],
                'end': chunk['end'],
                'text': chunk['text'],
                'embedding': chunk_embedding
            })

        logger.info(f"Created {len(audio_chunks)} audio chunks with embeddings")
        return audio_chunks

    def _create_video_chunks(
        self,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create multimodal chunks for video (audio transcript + visual keyframes)

        Args:
            video_path: Path to video file
            metadata: Video metadata

        Returns:
            List of video chunks with both audio and visual embeddings
        """
        logger.info("Processing video for multimodal search...")

        try:
            # Step 1: Extract audio and transcribe
            logger.info("Extracting audio from video...")
            audio_path = self.video_processor.extract_audio(video_path)

            logger.info("Transcribing video audio...")
            transcription = transcribe_audio_file(audio_path)
            transcript_text = transcription['text']
            duration = transcription['duration']
            segments = transcription['segments']

            # Step 2: Extract keyframes
            logger.info("Extracting keyframes from video...")
            keyframes = self.video_processor.extract_keyframes(video_path)

            # Step 3: Create audio chunks from transcript
            audio_chunks = self.audio_chunker.chunk_transcript_with_timestamps(segments)

            if not audio_chunks:
                logger.warning("No audio chunks created from video")
                return []

            # Step 4: Match keyframes to audio chunks and create multimodal embeddings
            video_chunks = []

            for chunk in audio_chunks:
                chunk_start = chunk['start']
                chunk_end = chunk['end']
                chunk_text = chunk['text']

                # Find keyframes within this chunk's timespan
                matching_keyframes = [
                    kf for kf in keyframes
                    if chunk_start <= kf['timestamp'] < chunk_end
                ]

                # Generate text embedding for audio
                text_embedding = self.embeddings.embed_text(chunk_text)

                # Generate visual embeddings for keyframes
                visual_embeddings = []
                keyframe_data = []

                for kf in matching_keyframes:
                    try:
                        # Use Voyage AI multimodal embedding (image + text context)
                        visual_emb = self.embeddings.embed_image(
                            kf['file_path'],
                            caption=chunk_text  # Use audio as caption context
                        )
                        visual_embeddings.append(visual_emb)
                        keyframe_data.append({
                            'timestamp': kf['timestamp'],
                            'file_path': kf['file_path']
                        })
                    except Exception as e:
                        logger.warning(f"Failed to embed keyframe at {kf['timestamp']}s: {e}")

                # Average visual embeddings if multiple keyframes in chunk
                if visual_embeddings:
                    import numpy as np
                    avg_visual_embedding = np.mean(visual_embeddings, axis=0).tolist()
                else:
                    avg_visual_embedding = None

                # Combine text and visual embeddings (weighted average)
                if avg_visual_embedding:
                    import numpy as np
                    # 50% text, 50% visual
                    combined_embedding = (
                        0.5 * np.array(text_embedding) +
                        0.5 * np.array(avg_visual_embedding)
                    ).tolist()
                else:
                    # Text only if no keyframes
                    combined_embedding = text_embedding

                video_chunks.append({
                    'start': chunk_start,
                    'end': chunk_end,
                    'text': chunk_text,
                    'keyframes': keyframe_data,
                    'embedding': combined_embedding,
                    'text_embedding': text_embedding,
                    'visual_embedding': avg_visual_embedding
                })

            logger.info(f"Created {len(video_chunks)} multimodal video chunks")

            # Clean up temporary audio file
            try:
                os.remove(audio_path)
            except:
                pass

            return video_chunks

        except Exception as e:
            logger.error(f"Failed to create video chunks: {e}")
            raise

    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting PDF text from {pdf_path}: {e}")
            return ""

    def ingest_from_manifest(self, manifest_path: str, data_dir: str, base_url: str = None) -> Dict[str, Any]:
        """
        Ingest documents from manifest file

        Extracts text/transcript/caption for embedding generation,
        but only stores file references, embeddings, and metadata in MongoDB.

        Args:
            manifest_path: Path to manifest.json
            data_dir: Base directory containing data files
            base_url: Base URL for file access (optional)

        Returns:
            Ingestion statistics
        """

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "by_modality": {"pdf": 0, "audio": 0, "image": 0}
        }

        for item in manifest.get("documents", []):
            stats["total"] += 1

            try:
                modality = item["modality"]
                file_path = os.path.join(data_dir, item["file"])

                # Resolve the file locally, or fetch it from S3 on demand.
                # For pdf/video we need the bytes on disk to extract text/frames.
                if not os.path.exists(file_path):
                    resolved = resolve_file(get_settings(), item["file"])
                    if resolved is not None:
                        file_path = str(resolved)

                # Extract content for embedding generation ONLY
                # This content will NOT be stored in MongoDB
                text_content = None
                transcript = None
                image_caption = None

                if modality == "pdf":
                    if os.path.exists(file_path):
                        text_content = self.extract_pdf_text(file_path)
                    else:
                        logger.warning(f"PDF file not found: {file_path}, using title/tags only")
                elif modality == "audio":
                    transcript = item.get("transcript", "")
                elif modality == "image":
                    image_caption = item.get("caption", "")

                # Generate file URL if base_url provided
                file_url = None
                if base_url:
                    file_url = f"{base_url}/{item['file']}"

                # Ingest document (text used for embedding, then discarded)
                self.ingest_document(
                    title=item["title"],
                    modality=modality,
                    source_file=item["file"],
                    file_path=file_path,
                    tags=item.get("tags", []),
                    metadata=item.get("metadata", {}),
                    text_content=text_content,
                    transcript=transcript,
                    image_caption=image_caption,
                    file_url=file_url,
                    stored_path=item["file"]
                )

                stats["success"] += 1
                stats["by_modality"][modality] += 1

            except Exception as e:
                logger.error(f"Failed to ingest {item.get('file', 'unknown')}: {e}")
                stats["failed"] += 1

        logger.info(f"Ingestion complete: {stats}")
        return stats
