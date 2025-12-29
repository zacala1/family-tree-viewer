"""Photo management utilities for Family Tree application.

This module provides functions for managing person photos:
- Creating photo storage folder
- Saving and copying photos
- Loading thumbnails
- Path resolution
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from src.config import (
    PHOTOS_FOLDER,
    PHOTO_THUMBNAIL_SIZE,
    SUPPORTED_IMAGE_FORMATS,
    MAX_PHOTO_SIZE,
)
from src.utils.logger import Logger

logger = Logger()


def ensure_photos_folder() -> Path:
    """Create photos folder if it doesn't exist.

    Returns:
        Path: Absolute path to photos folder
    """
    photos_path = Path(PHOTOS_FOLDER)
    photos_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Photos folder ensured at: {photos_path.absolute()}")
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

    # Validate source file exists
    if not source.exists():
        raise FileNotFoundError(f"Source photo not found: {source_path}")

    # Validate file extension
    ext = source.suffix.lower()
    if ext not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(
            f"Unsupported image format: {ext}. "
            f"Supported: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
        )

    # Validate file size
    file_size = source.stat().st_size
    if file_size > MAX_PHOTO_SIZE:
        raise ValueError(
            f"Photo file too large: {file_size / (1024*1024):.1f} MB. "
            f"Maximum: {MAX_PHOTO_SIZE / (1024*1024):.0f} MB"
        )

    # Ensure photos folder exists
    photos_folder = ensure_photos_folder()

    # Create destination filename: {person_id}{extension}
    dest_filename = f"{person_id}{ext}"
    dest_path = photos_folder / dest_filename

    try:
        # Copy file to photos folder
        shutil.copy2(source, dest_path)
        logger.info(f"Photo saved: {source_path} -> {dest_path}")

        # Return relative path for storage in JSON
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

    # Convert to absolute path (resolve relative to current working directory)
    abs_path = Path(relative_path).resolve()

    # Check if file exists
    if abs_path.exists() and abs_path.is_file():
        return abs_path

    logger.warning(f"Photo file not found: {relative_path}")
    return None


def load_thumbnail(photo_path: str, size: int = PHOTO_THUMBNAIL_SIZE) -> Optional[QPixmap]:
    """Load photo and create thumbnail.

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
        # Load image
        pixmap = QPixmap(str(abs_path))

        if pixmap.isNull():
            logger.warning(f"Failed to load image: {photo_path}")
            return None

        # Create square thumbnail with aspect ratio preserved
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
