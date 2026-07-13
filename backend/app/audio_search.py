"""
Semantic search within audio chunks
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


def search_audio_chunks(
    audio_chunks: List[Dict[str, Any]],
    query_embedding: List[float],
    top_k: int = 1,
    context_before: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Search audio chunks using semantic similarity

    Args:
        audio_chunks: List of chunks with embeddings
        query_embedding: Query vector from Voyage AI
        top_k: Number of results to return
        context_before: Seconds to start before the match

    Returns:
        List of matching chunks with playback timestamps (sorted by score)
    """
    if not audio_chunks:
        return [] if top_k > 1 else None

    # Calculate cosine similarity for each chunk
    query_vec = np.array(query_embedding)
    scored_chunks = []

    for chunk in audio_chunks:
        chunk_vec = np.array(chunk['embedding'])

        # Cosine similarity
        similarity = np.dot(query_vec, chunk_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
        )

        playback_time = max(0, chunk['start'] - context_before)

        scored_chunks.append({
            'timestamp': playback_time,
            'matched_text': chunk['text'],
            'score': float(similarity),
            'chunk_start': chunk['start'],
            'chunk_end': chunk['end']
        })

    # Sort by score descending
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)

    # Return top_k results
    results = scored_chunks[:top_k]

    # For backward compatibility: if top_k=1, return single dict or None
    if top_k == 1:
        return results[0] if results else None

    return results
