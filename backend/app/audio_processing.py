"""
Audio processing with semantic chunking and timestamped search
"""

import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class AudioChunker:
    """
    Process audio transcripts into semantic chunks with timestamps
    """

    def __init__(self, chunk_duration: int = 15, overlap: int = 3):
        """
        Args:
            chunk_duration: Target chunk duration in seconds
            overlap: Overlap between chunks in seconds (for context)
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap

    def chunk_transcript_by_time(
        self,
        transcript: str,
        duration: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk transcript by time estimates (when no timestamps available)

        Args:
            transcript: Full transcript text
            duration: Total audio duration in seconds

        Returns:
            List of chunks with estimated timestamps
        """
        # Split by sentences
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Estimate words per second (average speech rate ~150 words/min)
        total_words = sum(len(s.split()) for s in sentences)
        words_per_second = 2.5 if not duration else total_words / duration

        chunks = []
        current_chunk = []
        current_start = 0
        current_words = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())
            sentence_duration = sentence_words / words_per_second

            # Check if adding this sentence exceeds chunk duration
            if current_words > 0 and (current_words / words_per_second) >= self.chunk_duration:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_end = current_start + (current_words / words_per_second)

                chunks.append({
                    'start': current_start,
                    'end': chunk_end,
                    'text': chunk_text
                })

                # Start new chunk with overlap
                overlap_start = max(0, chunk_end - self.overlap)
                current_start = overlap_start
                current_chunk = [sentence]
                current_words = sentence_words
            else:
                current_chunk.append(sentence)
                current_words += sentence_words

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_end = current_start + (current_words / words_per_second)
            chunks.append({
                'start': current_start,
                'end': chunk_end,
                'text': chunk_text
            })

        logger.info(f"Created {len(chunks)} time-based chunks")
        return chunks

    def chunk_transcript_with_timestamps(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk transcript using actual timestamps from Whisper/transcription

        Args:
            segments: List of segments with 'start', 'end', 'text'

        Returns:
            List of semantic chunks
        """
        if not segments:
            return []

        chunks = []
        current_chunk = []
        chunk_start = segments[0]['start']

        for segment in segments:
            current_chunk.append(segment)

            # Calculate current chunk duration
            chunk_duration = segment['end'] - chunk_start

            # If chunk exceeds target duration, save it
            if chunk_duration >= self.chunk_duration:
                chunk_text = ' '.join(s['text'] for s in current_chunk)
                chunks.append({
                    'start': chunk_start,
                    'end': segment['end'],
                    'text': chunk_text
                })

                # Start new chunk with overlap
                overlap_time = self.overlap
                overlap_segments = []
                cumulative_time = 0

                # Add overlapping segments from the end
                for s in reversed(current_chunk):
                    seg_duration = s['end'] - s['start']
                    if cumulative_time + seg_duration <= overlap_time:
                        overlap_segments.insert(0, s)
                        cumulative_time += seg_duration
                    else:
                        break

                current_chunk = overlap_segments
                chunk_start = overlap_segments[0]['start'] if overlap_segments else segment['end']

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(s['text'] for s in current_chunk)
            chunks.append({
                'start': current_chunk[0]['start'],
                'end': current_chunk[-1]['end'],
                'text': chunk_text
            })

        logger.info(f"Created {len(chunks)} timestamp-based chunks")
        return chunks


def search_audio_chunks(
    chunks: List[Dict[str, Any]],
    query_embedding: List[float],
    top_k: int = 1
) -> List[Dict[str, Any]]:
    """
    Search audio chunks using cosine similarity

    Args:
        chunks: List of chunks with embeddings
        query_embedding: Query vector
        top_k: Number of top matches to return

    Returns:
        List of matching chunks with scores
    """
    import numpy as np

    if not chunks:
        return []

    # Calculate cosine similarity for each chunk
    results = []
    query_vec = np.array(query_embedding)

    for chunk in chunks:
        chunk_vec = np.array(chunk['embedding'])

        # Cosine similarity
        similarity = np.dot(query_vec, chunk_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
        )

        results.append({
            'start': chunk['start'],
            'end': chunk['end'],
            'text': chunk['text'],
            'score': float(similarity)
        })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    return results[:top_k]
