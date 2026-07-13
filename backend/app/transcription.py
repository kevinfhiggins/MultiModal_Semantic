"""
Automatic audio transcription using Whisper
"""

import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Automatic audio transcription with Whisper"""

    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper transcriber

        Args:
            model_size: Model size (tiny, base, small, medium, large)
                       - tiny: fastest, least accurate (~1GB)
                       - base: good balance (~1GB) - DEFAULT
                       - small: better accuracy (~2GB)
                       - medium: very good (~5GB)
        """
        self.model_size = model_size
        self.model = None

    def load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model ({self.model_size})...")
                self.model = whisper.load_model(self.model_size)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise

    def transcribe_audio(
        self,
        audio_path: str,
        language: str = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file with timestamps

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr') or None for auto-detect

        Returns:
            Dict with 'text', 'segments', and 'duration'
        """
        self.load_model()

        logger.info(f"Transcribing audio: {audio_path}")

        try:
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=False,  # Segment-level is faster and sufficient
                verbose=False
            )

            segments = []
            for segment in result['segments']:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })

            full_text = result['text']
            duration = segments[-1]['end'] if segments else 0

            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"{duration:.1f}s duration, {len(full_text)} characters"
            )

            return {
                'text': full_text,
                'segments': segments,
                'duration': duration,
                'language': result.get('language', 'unknown')
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def get_full_transcript(self, segments: List[Dict[str, Any]]) -> str:
        """Get full text from segments"""
        return ' '.join(seg['text'] for seg in segments)


# Global transcriber instance
_transcriber = None


def get_transcriber() -> WhisperTranscriber:
    """Get global Whisper transcriber instance"""
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber(model_size="base")
    return _transcriber


def transcribe_audio_file(audio_path: str) -> Dict[str, Any]:
    """
    Convenience function to transcribe an audio file

    Args:
        audio_path: Path to audio file

    Returns:
        Transcription result with text, segments, duration
    """
    transcriber = get_transcriber()
    return transcriber.transcribe_audio(audio_path)
