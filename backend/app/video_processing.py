"""
Video processing for multimodal search
Extracts audio (for transcription) and keyframes (for visual search)
"""

import logging
import subprocess
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos for multimodal search"""

    def __init__(self, keyframe_interval: int = 5):
        """
        Args:
            keyframe_interval: Extract keyframe every N seconds
        """
        self.keyframe_interval = keyframe_interval

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio track from video using ffmpeg

        Args:
            video_path: Path to video file
            output_path: Optional output path for audio file

        Returns:
            Path to extracted audio file
        """
        if output_path is None:
            # Create temp file for audio
            fd, output_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)

        logger.info(f"Extracting audio from video: {video_path}")

        try:
            # Use ffmpeg to extract audio
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'mp3',
                '-ar', '16000',  # 16kHz sample rate (good for Whisper)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                output_path
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            logger.info(f"Audio extracted to: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio: {e.stderr.decode()}")
            raise Exception(f"Audio extraction failed: {e}")
        except FileNotFoundError:
            raise Exception("ffmpeg not found - please install ffmpeg")

    def extract_keyframes(
        self,
        video_path: str,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract keyframes from video at regular intervals

        Args:
            video_path: Path to video file
            output_dir: Optional directory for keyframe images

        Returns:
            List of keyframes with timestamps and file paths
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()

        logger.info(f"Extracting keyframes from video: {video_path}")

        try:
            # First, get video duration
            duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]

            duration_result = subprocess.run(
                duration_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            duration = float(duration_result.stdout.decode().strip())
            logger.info(f"Video duration: {duration:.1f}s")

            # Extract keyframes at intervals
            keyframes = []
            frame_count = 0

            for timestamp in range(0, int(duration), self.keyframe_interval):
                output_file = os.path.join(output_dir, f"frame_{frame_count:04d}.jpg")

                command = [
                    'ffmpeg',
                    '-ss', str(timestamp),  # Seek to timestamp
                    '-i', video_path,
                    '-vframes', '1',  # Extract 1 frame
                    '-q:v', '2',  # High quality
                    '-y',
                    output_file
                ]

                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )

                if os.path.exists(output_file):
                    keyframes.append({
                        'timestamp': timestamp,
                        'frame_number': frame_count,
                        'file_path': output_file
                    })
                    frame_count += 1

            logger.info(f"Extracted {len(keyframes)} keyframes")
            return keyframes

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract keyframes: {e.stderr.decode()}")
            raise Exception(f"Keyframe extraction failed: {e}")
        except FileNotFoundError:
            raise Exception("ffmpeg/ffprobe not found - please install ffmpeg")

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video metadata

        Args:
            video_path: Path to video file

        Returns:
            Dict with duration, resolution, etc.
        """
        try:
            command = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            import json
            info = json.loads(result.stdout.decode())

            # Extract info
            stream = info.get('streams', [{}])[0]
            format_info = info.get('format', {})

            return {
                'width': stream.get('width'),
                'height': stream.get('height'),
                'duration': float(format_info.get('duration', 0))
            }

        except Exception as e:
            logger.warning(f"Failed to get video info: {e}")
            return {}


def extract_video_audio(video_path: str) -> str:
    """
    Convenience function to extract audio from video

    Args:
        video_path: Path to video file

    Returns:
        Path to extracted audio file
    """
    processor = VideoProcessor()
    return processor.extract_audio(video_path)


def extract_video_keyframes(video_path: str, interval: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to extract keyframes from video

    Args:
        video_path: Path to video file
        interval: Extract frame every N seconds

    Returns:
        List of keyframes with timestamps
    """
    processor = VideoProcessor(keyframe_interval=interval)
    return processor.extract_keyframes(video_path)
