"""
File storage abstraction.

Resolves data files (PDFs, images, audio, video) to a local path so the rest
of the app can read them from disk. Files can live in one of two places:

  1. A local directory (``FILE_STORAGE_PATH``) - the classic layout, e.g. a
     checked-out ``sample_data/`` folder.
  2. An S3 bucket (``S3_BUCKET`` / ``S3_PREFIX``) - the media assets live in
     S3 and are fetched on demand into a local cache the first time they are
     requested.

Local files always win. When a file is missing locally and S3 is configured,
it is downloaded into ``FILE_CACHE_PATH`` (defaults to the storage path) and
served from there on every subsequent request.
"""

import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Guards concurrent downloads of the same file.
_download_locks_guard = threading.Lock()
_download_locks: dict = {}

_s3_client = None
_s3_client_lock = threading.Lock()


def _get_s3_client(settings):
    """Lazily build a shared boto3 S3 client (thread-safe)."""
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    with _s3_client_lock:
        if _s3_client is None:
            import boto3

            region = getattr(settings, "aws_region", None) or None
            _s3_client = boto3.client("s3", region_name=region)
    return _s3_client


def _s3_enabled(settings) -> bool:
    return bool(getattr(settings, "s3_bucket", "") or "")


def _cache_root(settings) -> Path:
    cache = getattr(settings, "file_cache_path", "") or getattr(
        settings, "file_storage_path", "sample_data"
    )
    return Path(cache)


def _s3_key(settings, relative_path: str) -> str:
    prefix = (getattr(settings, "s3_prefix", "") or "").strip("/")
    rel = relative_path.lstrip("/")
    return f"{prefix}/{rel}" if prefix else rel


def _lock_for(key: str) -> threading.Lock:
    with _download_locks_guard:
        lock = _download_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _download_locks[key] = lock
        return lock


def _download_from_s3(settings, relative_path: str, dest: Path) -> bool:
    """Download ``relative_path`` from S3 into ``dest``. Returns True on success."""
    bucket = settings.s3_bucket
    key = _s3_key(settings, relative_path)
    lock = _lock_for(key)

    with lock:
        # Another thread may have fetched it while we waited on the lock.
        if dest.exists():
            return True

        client = _get_s3_client(settings)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            logger.info(f"Fetching s3://{bucket}/{key} -> {dest}")
            client.download_file(bucket, key, str(tmp))
            tmp.replace(dest)
            return True
        except Exception as e:
            logger.warning(f"S3 download failed for s3://{bucket}/{key}: {e}")
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            return False


def resolve_file(settings, relative_path: str) -> Optional[Path]:
    """
    Resolve a data file to a local path, fetching from S3 if needed.

    Args:
        settings: application settings (provides storage paths / S3 config)
        relative_path: path relative to the storage root, e.g. "2.jpg" or
            "uploads/report.pdf"

    Returns:
        Local ``Path`` to the file, or ``None`` if it cannot be found.
    """
    relative_path = relative_path.lstrip("/")

    # 1) Local storage path (checked-out sample_data or previous download).
    storage_root = Path(getattr(settings, "file_storage_path", "sample_data"))
    local = storage_root / relative_path
    if local.exists():
        return local

    # 2) Local cache (may differ from storage path).
    cache_root = _cache_root(settings)
    cached = cache_root / relative_path
    if cached.exists():
        return cached

    # 3) Fetch from S3 into the cache.
    if _s3_enabled(settings):
        if _download_from_s3(settings, relative_path, cached):
            return cached

    return None
