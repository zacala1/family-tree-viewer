"""Photo management utilities for Family Tree application.

This module provides functions for managing person photos:
- Creating photo storage folder
- Saving and copying photos
- Loading thumbnails
- Path resolution
"""

import re
import shutil
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from ..config import (
    PHOTOS_FOLDER,
    PHOTO_THUMBNAIL_SIZE,
    SUPPORTED_IMAGE_FORMATS,
    MAX_PHOTO_SIZE,
    APP_ROOT,
)
from ..utils import logger


def _photos_abs_path() -> Path:
    """PHOTOS_FOLDER를 APP_ROOT 기준 절대경로로 변환."""
    return Path(APP_ROOT) / PHOTOS_FOLDER


def ensure_photos_folder() -> Path:
    """Create photos folder if it doesn't exist.

    Returns:
        Path: Absolute path to photos folder
    """
    photos_path = _photos_abs_path()
    photos_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Photos folder ensured at: {photos_path}")
    return photos_path


def save_photo(source_path: str, person_id: str) -> Optional[str]:
    """Copy photo to photos folder and return relative path.

    Args:
        source_path: Absolute path to source photo file
        person_id: Unique ID of person (used for filename)

    Returns:
        Optional[str]: Relative path to saved photo, or None if failed

    Raises:
        ValueError: If file format not supported or file too large
        FileNotFoundError: If source file doesn't exist
    """
    source = Path(source_path)

    if not source.exists():
        raise FileNotFoundError(f"Source photo not found: {source_path}")

    ext = source.suffix.lower()
    if ext not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(
            f"Unsupported image format: {ext}. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
        )

    file_size = source.stat().st_size
    if file_size > MAX_PHOTO_SIZE:
        raise ValueError(
            f"Photo file too large: {file_size / (1024*1024):.1f} MB. "
            f"Maximum: {MAX_PHOTO_SIZE / (1024*1024):.0f} MB"
        )

    photos_folder = ensure_photos_folder()
    # Sanitize person_id: only allow UUID-safe characters to prevent path traversal
    safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', person_id)
    dest_filename = f"{safe_id}{ext}"
    dest_path = photos_folder / dest_filename

    # Verify destination is within photos folder
    if not dest_path.resolve().is_relative_to(photos_folder.resolve()):
        logger.error(f"Path traversal attempt blocked: {dest_filename}")
        return None

    try:
        shutil.copy2(source, dest_path)
        logger.info(f"Photo saved: {source_path} -> {dest_path}")

        relative_path = str(Path(PHOTOS_FOLDER) / dest_filename)
        return relative_path

    except Exception as e:
        logger.error(f"Failed to save photo: {e}")
        return None


def get_photo_path(relative_path: str) -> Optional[Path]:
    """Convert relative photo path to absolute path.

    Args:
        relative_path: Relative path stored in Person.photo_path

    Returns:
        Optional[Path]: Absolute path if file exists, None otherwise
    """
    if not relative_path:
        return None

    path = Path(relative_path)
    # 이미 절대경로면 그대로, 상대경로면 APP_ROOT 기준으로 해석
    abs_path = path.resolve() if path.is_absolute() else (Path(APP_ROOT) / relative_path).resolve()
    photos_folder = _photos_abs_path().resolve()

    # Verify resolved path is within photos folder to prevent path traversal
    if not abs_path.is_relative_to(photos_folder):
        logger.warning(f"Photo path outside photos folder: {relative_path}")
        return None

    if abs_path.exists() and abs_path.is_file():
        return abs_path

    logger.warning(f"Photo file not found: {relative_path}")
    return None


def load_thumbnail(photo_path: str, size: int = PHOTO_THUMBNAIL_SIZE) -> Optional[QPixmap]:
    """Load photo and create thumbnail with preserved aspect ratio.

    Args:
        photo_path: Relative or absolute path to photo
        size: Thumbnail size in pixels (default from config)

    Returns:
        Optional[QPixmap]: Thumbnail pixmap, or None if failed
    """
    abs_path = get_photo_path(photo_path)
    if not abs_path:
        return None

    try:
        pixmap = QPixmap(str(abs_path))

        if pixmap.isNull():
            logger.warning(f"Failed to load image: {photo_path}")
            return None

        thumbnail = pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        return thumbnail

    except Exception as e:
        logger.error(f"Error loading thumbnail: {e}")
        return None


def delete_photo(photo_path: str) -> bool:
    """Delete photo file from photos folder.

    Args:
        photo_path: Relative path to photo

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    abs_path = get_photo_path(photo_path)
    if not abs_path:
        return False

    try:
        abs_path.unlink()
        logger.info(f"Photo deleted: {photo_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete photo: {e}")
        return False
