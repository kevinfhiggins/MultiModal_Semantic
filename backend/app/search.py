from typing import List, Dict, Any, Optional
import logging

from .database import MongoDB
from .embeddings import VoyageEmbeddings
from .models import SearchRequest, SearchResult, Modality
from .config import Settings
from .audio_search import search_audio_chunks

logger = logging.getLogger(__name__)


class VectorSearch:
    """Vector search operations against MongoDB Atlas"""

    def __init__(self, db: MongoDB, embeddings: VoyageEmbeddings, settings: Settings):
        self.db = db
        self.embeddings = embeddings
        self.settings = settings

    def search(self, request: SearchRequest) -> List[SearchResult]:
        """
        Perform vector search against MoD_Data collection.
        All assets use voyage-3 text embeddings.
        """
        try:
            # All assets use voyage-3 text embeddings
            text_query_embedding = self.embeddings.embed_query(request.query, use_multimodal=False)

            # Single unified search - all assets use voyage-3 text embeddings
            pipeline = self._build_search_pipeline(
                query_embedding=text_query_embedding,
                modality=request.modality,
                top_k=request.top_k
            )
            all_results = list(self.db.collection.aggregate(pipeline))

            # FIX 3: Apply min-max normalization to scores
            # HARDCODED NORMALIZATION FLOOR: If score distribution is collapsed (< 0.01 range),
            # cap confidence readout to prevent misleading percentages
            if all_results:
                scores = [r.get('score', 0) for r in all_results]
                min_score = min(scores)
                max_score = max(scores)
                score_range = max_score - min_score

                # Check if distribution is collapsed (< 0.01 range)
                if score_range < 0.01:
                    # Collapsed distribution - set narrow confidence bands to show uncertainty
                    # Top result gets 100%, rest get proportional but capped confidence
                    for i, result in enumerate(all_results):
                        if i == 0:
                            result['normalized_score'] = 100.0
                        else:
                            # Rank-based decay: 90, 80, 70, 60, 55, 50, 45, 40, 35, 30...
                            result['normalized_score'] = max(30.0, 100.0 - (i * 10))
                    logger.warning(
                        f"Collapsed score distribution detected (range={score_range:.6f}). "
                        f"Applied rank-based normalization to prevent misleading confidence."
                    )
                elif score_range > 0:
                    # Normal distribution - use min-max normalization
                    for result in all_results:
                        raw_score = result.get('score', 0)
                        # Map to 0-100 scale
                        normalized = ((raw_score - min_score) / score_range) * 100
                        result['normalized_score'] = normalized
                else:
                    # All scores identical
                    for result in all_results:
                        result['normalized_score'] = 100.0

            logger.info(
                f"Search completed: query='{request.query}', "
                f"results={len(all_results)}, modality={request.modality}"
            )

            # Convert to SearchResult models
            return [self._parse_result(result, text_query_embedding) for result in all_results]

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

    def _search_chunks(
        self,
        query_embedding: List[float],
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Search audio/video chunks directly to return multiple matches per file

        Args:
            query_embedding: Query vector
            request: Search request

        Returns:
            List of chunk-level results (multiple per file)
        """
        from .audio_search import search_audio_chunks
        import numpy as np

        # Get all audio/video documents
        filter_query = {"modality": request.modality.value}
        documents = list(self.db.collection.find(filter_query))

        all_chunk_results = []

        for doc in documents:
            # Determine chunk field based on modality
            chunk_field = "audio_chunks" if request.modality == Modality.AUDIO else "video_chunks"
            chunks = doc.get(chunk_field, [])

            if not chunks:
                continue

            # Search chunks and get top matches
            chunk_matches = search_audio_chunks(
                audio_chunks=chunks,
                query_embedding=query_embedding,
                top_k=request.top_k,  # Get top N from each file
                context_before=0.0
            )

            # Convert each chunk match to a SearchResult
            for chunk_match in chunk_matches:
                result = SearchResult(
                    _id=str(doc["_id"]),
                    title=doc.get("title", "Untitled"),
                    modality=doc.get("modality", "unknown"),
                    score=chunk_match.get("score"),
                    preview=chunk_match.get("matched_text", "")[:200],
                    tags=doc.get("tags", []),
                    source_file=doc.get("source_file", ""),
                    file_url=doc.get("file_url"),
                    metadata=doc.get("metadata", {}),
                    timestamp=chunk_match.get("timestamp"),
                    matched_text=chunk_match.get("matched_text")
                )
                all_chunk_results.append(result)

        # Sort by score descending and limit to top_k
        all_chunk_results.sort(key=lambda x: x.score or 0, reverse=True)
        final_results = all_chunk_results[:request.top_k]

        # FIX 3: Apply min-max normalization to chunk scores with collapsed distribution handling
        if final_results:
            scores = [r.score for r in final_results if r.score is not None]
            if scores:
                min_score = min(scores)
                max_score = max(scores)
                score_range = max_score - min_score

                # Check if distribution is collapsed (< 0.01 range)
                if score_range < 0.01:
                    # Collapsed distribution - use rank-based confidence
                    for i, result in enumerate(final_results):
                        if result.score is not None:
                            if i == 0:
                                result.normalized_score = 100.0
                            else:
                                result.normalized_score = max(30.0, 100.0 - (i * 10))
                    logger.warning(
                        f"Collapsed chunk score distribution (range={score_range:.6f}). "
                        f"Applied rank-based normalization."
                    )
                elif score_range > 0:
                    # Normal distribution - use min-max normalization
                    for result in final_results:
                        if result.score is not None:
                            normalized = ((result.score - min_score) / score_range) * 100
                            result.normalized_score = normalized
                else:
                    # All scores identical
                    for result in final_results:
                        if result.score is not None:
                            result.normalized_score = 100.0

        logger.info(
            f"Chunk-level search completed: query='{request.query}', "
            f"results={len(final_results)}, modality={request.modality}"
        )

        return final_results

    def _build_search_pipeline(
        self,
        query_embedding: List[float],
        modality: Modality,
        top_k: int,
        exclude_images: bool = False
    ) -> List[Dict[str, Any]]:
        """Build MongoDB aggregation pipeline for vector search"""

        # Base vector search stage
        # FIX 3: Use high numCandidates (200) to overcome narrow noise floor
        # This prevents geometric shapes (oil tanks) from saturating HNSW graph
        vector_search_stage = {
            "$vectorSearch": {
                "index": self.settings.vector_index_name,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": max(200, top_k * 10),  # At least 200 candidates
                "limit": top_k
            }
        }

        # Add modality filter if specified
        if modality != Modality.ALL:
            vector_search_stage["$vectorSearch"]["filter"] = {
                "modality": modality.value
            }
        elif exclude_images:
            # Exclude images when doing text-only search
            vector_search_stage["$vectorSearch"]["filter"] = {
                "modality": {"$ne": "image"}
            }

        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "title": 1,
                    "modality": 1,
                    "preview": 1,
                    "tags": 1,
                    "source_file": 1,
                    "file_url": 1,
                    "metadata": 1,
                    "audio_chunks": 1,  # Include audio chunks for semantic search within
                    "video_chunks": 1,  # Include video chunks for multimodal search
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        return pipeline

    def _parse_result(self, result: Dict[str, Any], query_embedding: List[float] = None) -> SearchResult:
        """Parse MongoDB result into SearchResult model"""

        timestamp = None
        matched_text = None

        # For audio files with chunks, find the best matching chunk
        if result.get("modality") == "audio" and result.get("audio_chunks") and query_embedding:
            logger.info(f"Searching audio chunks for document: {result.get('title')}, chunks: {len(result.get('audio_chunks', []))}")
            chunk_match = search_audio_chunks(
                audio_chunks=result["audio_chunks"],
                query_embedding=query_embedding,
                context_before=0.0  # Start exactly at the matched chunk
            )
            if chunk_match:
                timestamp = chunk_match['timestamp']
                matched_text = chunk_match['matched_text']
                logger.info(f"Found chunk match at timestamp {timestamp}: {matched_text[:50]}...")
            else:
                logger.warning(f"No chunk match found for audio document: {result.get('title')}")

        # For video files with multimodal chunks, find the best matching chunk
        if result.get("modality") == "video" and result.get("video_chunks") and query_embedding:
            logger.info(f"Searching video chunks for document: {result.get('title')}, chunks: {len(result.get('video_chunks', []))}")
            chunk_match = search_audio_chunks(
                audio_chunks=result["video_chunks"],  # Reuse audio search (works with embeddings)
                query_embedding=query_embedding,
                context_before=0.0
            )
            if chunk_match:
                timestamp = chunk_match['timestamp']
                matched_text = chunk_match['matched_text']
                logger.info(f"Found video chunk match at timestamp {timestamp}: {matched_text[:50]}...")
            else:
                logger.warning(f"No chunk match found for video document: {result.get('title')}")

        return SearchResult(
            _id=result.get("_id", ""),
            title=result.get("title", "Untitled"),
            modality=result.get("modality", "unknown"),
            score=result.get("score"),
            normalized_score=result.get("normalized_score"),  # FIX 3: Pass through normalized score
            preview=result.get("preview", ""),
            tags=result.get("tags", []),
            source_file=result.get("source_file", ""),
            file_url=result.get("file_url"),
            metadata=result.get("metadata", {}),
            timestamp=timestamp,
            matched_text=matched_text
        )


def create_search_service(
    db: MongoDB,
    embeddings: VoyageEmbeddings,
    settings: Settings
) -> VectorSearch:
    """Factory function to create VectorSearch service"""
    return VectorSearch(db, embeddings, settings)
