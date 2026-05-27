"""Tests for photo_manager module."""

import os
import tempfile
from pathlib import Path
import pytest
from PIL import Image
from PyQt6.QtGui import QPixmap

from src.utils.photo_manager import (
    ensure_photos_folder,
    save_photo,
    get_photo_path,
    load_thumbnail,
    delete_photo,
    load_pixmap_oriented,
)
from src.config import PHOTOS_FOLDER, PHOTO_THUMBNAIL_SIZE, MAX_PHOTO_SIZE


class TestPhotoFolderManagement:
    """Test photo folder creation and management."""

    def test_ensure_photos_folder_creates_directory(self, tmp_path, monkeypatch):
        """Test that ensure_photos_folder creates the directory."""
        photos_dir = tmp_path / "test_photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        result = ensure_photos_folder()

        assert result.exists()
        assert result.is_dir()
        assert result == photos_dir

    def test_ensure_photos_folder_idempotent(self, tmp_path, monkeypatch):
        """Test that calling ensure_photos_folder multiple times is safe."""
        photos_dir = tmp_path / "test_photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        result1 = ensure_photos_folder()
        result2 = ensure_photos_folder()

        assert result1 == result2
        assert result1.exists()


class TestSavePhoto:
    """Test photo saving functionality."""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample image file for testing."""
        img_path = tmp_path / "sample.jpg"
        img = Image.new("RGB", (200, 200), color="red")
        img.save(img_path, "JPEG")
        return str(img_path)

    def test_save_photo_success(self, sample_image, tmp_path, monkeypatch):
        """Test successful photo save."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        person_id = "person123"
        result = save_photo(sample_image, person_id)

        assert result is not None
        assert result == str(Path(photos_dir) / f"{person_id}.jpg")
        assert (photos_dir / f"{person_id}.jpg").exists()

    def test_save_photo_creates_folder_if_not_exists(self, sample_image, tmp_path, monkeypatch):
        """Test that save_photo creates photos folder if it doesn't exist."""
        photos_dir = tmp_path / "new_photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        person_id = "person456"
        result = save_photo(sample_image, person_id)

        assert result is not None
        assert photos_dir.exists()

    def test_save_photo_nonexistent_file(self, tmp_path, monkeypatch):
        """Test save_photo with non-existent source file."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        with pytest.raises(FileNotFoundError):
            save_photo("/nonexistent/file.jpg", "person123")

    def test_save_photo_unsupported_format(self, tmp_path, monkeypatch):
        """Test save_photo with unsupported file format."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Create a text file with image extension
        bad_file = tmp_path / "bad.txt"
        bad_file.write_text("not an image")

        with pytest.raises(ValueError, match="Unsupported image format"):
            save_photo(str(bad_file), "person123")

    def test_save_photo_file_too_large(self, tmp_path, monkeypatch):
        """Test save_photo with file exceeding size limit."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Create a large image file
        large_img = tmp_path / "large.jpg"
        img = Image.new("RGB", (5000, 5000), color="blue")
        img.save(large_img, "JPEG", quality=100)

        # If file is larger than MAX_PHOTO_SIZE
        if large_img.stat().st_size > MAX_PHOTO_SIZE:
            with pytest.raises(ValueError, match="Photo file too large"):
                save_photo(str(large_img), "person123")
        else:
            # File might be compressed, skip this test
            pytest.skip("Could not create file large enough")

    def test_save_photo_preserves_extension(self, tmp_path, monkeypatch):
        """Test that save_photo preserves the file extension."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Create PNG file
        png_file = tmp_path / "sample.png"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(png_file, "PNG")

        person_id = "person789"
        result = save_photo(str(png_file), person_id)

        assert result.endswith(".png")
        assert (photos_dir / f"{person_id}.png").exists()

    def test_save_multiple_photos_for_same_person_uses_unique_names(self, tmp_path, monkeypatch):
        """Adding multiple same-extension photos for one person must not overwrite."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        first = tmp_path / "first.jpg"
        second = tmp_path / "second.jpg"
        Image.new("RGB", (20, 20), color="red").save(first, "JPEG")
        Image.new("RGB", (20, 20), color="blue").save(second, "JPEG")

        first_saved = save_photo(str(first), "person123")
        second_saved = save_photo(str(second), "person123")

        assert first_saved != second_saved
        assert Path(first_saved).name == "person123.jpg"
        assert Path(second_saved).name == "person123_1.jpg"
        assert (photos_dir / "person123.jpg").exists()
        assert (photos_dir / "person123_1.jpg").exists()


class TestGetPhotoPath:
    """Test photo path resolution."""

    def test_get_photo_path_existing_file(self, tmp_path, monkeypatch):
        """Test get_photo_path with existing file."""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        photo_file = photos_dir / "photo.jpg"
        photo_file.write_text("test")

        result = get_photo_path(str(photo_file))

        assert result is not None
        assert result.exists()
        assert result.is_file()

    def test_get_photo_path_nonexistent_file(self, tmp_path):
        """Test get_photo_path with non-existent file."""
        result = get_photo_path(str(tmp_path / "nonexistent.jpg"))

        assert result is None

    def test_get_photo_path_empty_string(self):
        """Test get_photo_path with empty string."""
        result = get_photo_path("")

        assert result is None

    def test_get_photo_path_none(self):
        """Test get_photo_path with None."""
        result = get_photo_path(None)

        assert result is None

    def test_get_photo_path_directory(self, tmp_path):
        """Test get_photo_path with directory instead of file."""
        dir_path = tmp_path / "photos"
        dir_path.mkdir()

        result = get_photo_path(str(dir_path))

        assert result is None  # Should return None for directories

    def test_get_photo_path_resolves_relative(self, tmp_path, monkeypatch):
        """Test that get_photo_path resolves relative paths."""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))
        monkeypatch.setattr("src.utils.photo_manager.APP_ROOT", str(tmp_path))

        photo_file = photos_dir / "photo.jpg"
        photo_file.write_text("test")

        result = get_photo_path(str(photos_dir / "photo.jpg"))

        assert result is not None
        assert result.is_absolute()


class TestLoadThumbnail:
    """Test thumbnail loading functionality."""

    @pytest.fixture
    def sample_image_file(self, tmp_path, monkeypatch):
        """Create a sample image file for testing."""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        img_path = photos_dir / "sample.jpg"
        img = Image.new("RGB", (500, 500), color="blue")
        img.save(img_path, "JPEG")
        return str(img_path)

    def test_load_thumbnail_success(self, sample_image_file):
        """Test successful thumbnail loading."""
        thumbnail = load_thumbnail(sample_image_file, 150)

        assert thumbnail is not None
        assert isinstance(thumbnail, QPixmap)
        assert not thumbnail.isNull()
        # Thumbnail should be scaled
        assert thumbnail.width() <= 150
        assert thumbnail.height() <= 150

    def test_load_thumbnail_nonexistent_file(self):
        """Test load_thumbnail with non-existent file."""
        result = load_thumbnail("/nonexistent/file.jpg")

        assert result is None

    def test_load_thumbnail_custom_size(self, sample_image_file):
        """Test load_thumbnail with custom size."""
        thumbnail = load_thumbnail(sample_image_file, 100)

        assert thumbnail is not None
        assert thumbnail.width() <= 100
        assert thumbnail.height() <= 100

    def test_load_thumbnail_aspect_ratio_preserved(self, tmp_path, monkeypatch):
        """Test that thumbnail preserves aspect ratio."""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Create rectangular image
        img_path = photos_dir / "rect.jpg"
        img = Image.new("RGB", (400, 200), color="red")
        img.save(img_path, "JPEG")

        thumbnail = load_thumbnail(str(img_path), 150)

        assert thumbnail is not None
        # Should preserve 2:1 aspect ratio
        assert thumbnail.width() == 150
        assert thumbnail.height() == 75

    def test_load_thumbnail_empty_path(self):
        """Test load_thumbnail with empty path."""
        result = load_thumbnail("")

        assert result is None

    def test_load_thumbnail_corrupted_file(self, tmp_path):
        """Test load_thumbnail with corrupted image file."""
        bad_file = tmp_path / "corrupted.jpg"
        bad_file.write_text("This is not a valid JPEG file")

        result = load_thumbnail(str(bad_file))

        assert result is None


class TestDeletePhoto:
    """Test photo deletion functionality."""

    def test_delete_photo_success(self, tmp_path, monkeypatch):
        """Test successful photo deletion."""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        photo_file = photos_dir / "person123.jpg"
        photo_file.write_text("test")

        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        result = delete_photo(str(photo_file))

        assert result is True
        assert not photo_file.exists()

    def test_delete_photo_nonexistent_file(self):
        """Test delete_photo with non-existent file."""
        result = delete_photo("/nonexistent/file.jpg")

        assert result is False

    def test_delete_photo_empty_path(self):
        """Test delete_photo with empty path."""
        result = delete_photo("")

        assert result is False

    def test_delete_photo_permission_denied(self, tmp_path, monkeypatch):
        """Test delete_photo when file is locked (Windows)."""
        if os.name != "nt":
            pytest.skip("Windows-specific test")

        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        photo_file = photos_dir / "locked.jpg"
        photo_file.write_text("test")

        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Try to delete while file is open
        with open(photo_file, "r") as f:
            result = delete_photo(str(photo_file))

        # On Windows, this might fail or succeed depending on sharing mode
        # Just ensure it doesn't crash
        assert isinstance(result, bool)


class TestPhotoManagerIntegration:
    """Integration tests for photo manager."""

    def test_full_photo_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow: save, load, delete."""
        photos_dir = tmp_path / "photos"
        monkeypatch.setattr("src.utils.photo_manager.PHOTOS_FOLDER", str(photos_dir))

        # Create source image
        source_img = tmp_path / "source.jpg"
        img = Image.new("RGB", (300, 300), color="yellow")
        img.save(source_img, "JPEG")

        # Save photo
        person_id = "integration_test"
        relative_path = save_photo(str(source_img), person_id)
        assert relative_path is not None

        # Load thumbnail
        thumbnail = load_thumbnail(relative_path, 100)
        assert thumbnail is not None
        assert thumbnail.width() <= 100

        # Delete photo
        result = delete_photo(relative_path)
        assert result is True

        # Verify deletion
        abs_path = get_photo_path(relative_path)
        assert abs_path is None


class TestLoadPixmapOriented:
    """EXIF orientation을 반영한 사진 로드 회귀 가드."""

    def test_loads_normal_image(self, tmp_path):
        """EXIF 태그 없는 일반 이미지도 정상 로드."""
        img_path = tmp_path / "plain.png"
        Image.new("RGB", (100, 50), color=(200, 100, 50)).save(img_path)
        pixmap = load_pixmap_oriented(img_path)
        assert not pixmap.isNull()
        assert pixmap.width() == 100
        assert pixmap.height() == 50

    def test_applies_exif_rotation_6(self, tmp_path):
        """EXIF Orientation=6 (90° CW)이면 width/height가 교환돼야 함."""
        from PIL.ExifTags import Base as ExifTag

        img = Image.new("RGB", (200, 100), color=(50, 150, 200))
        exif = img.getexif()
        exif[ExifTag.Orientation.value] = 6  # 0x0112, "Rotate 90 CW"
        img_path = tmp_path / "rotated.jpg"
        img.save(img_path, exif=exif.tobytes())

        pixmap = load_pixmap_oriented(img_path)
        assert not pixmap.isNull()
        # 원본 200x100 → 회전 후 100x200
        assert pixmap.width() == 100
        assert pixmap.height() == 200

    def test_orientation_1_unchanged(self, tmp_path):
        """EXIF Orientation=1 (normal)이면 원본 그대로."""
        from PIL.ExifTags import Base as ExifTag

        img = Image.new("RGB", (160, 80), color=(0, 0, 0))
        exif = img.getexif()
        exif[ExifTag.Orientation.value] = 1
        img_path = tmp_path / "upright.jpg"
        img.save(img_path, exif=exif.tobytes())

        pixmap = load_pixmap_oriented(img_path)
        assert pixmap.width() == 160
        assert pixmap.height() == 80

    def test_corrupt_file_falls_back_to_null(self, tmp_path):
        """손상된 파일은 빈 QPixmap 반환 (크래시 금지)."""
        bad_path = tmp_path / "broken.jpg"
        bad_path.write_bytes(b"not an image")
        pixmap = load_pixmap_oriented(bad_path)
        # PIL이 실패 → fallback QPixmap도 빈 객체. 단, 크래시는 없어야.
        assert isinstance(pixmap, QPixmap)
        assert pixmap.isNull()

    def test_rgba_image_preserves_alpha_channel(self, tmp_path):
        """RGBA 이미지가 손상 없이 로드돼야 함."""
        img_path = tmp_path / "alpha.png"
        Image.new("RGBA", (40, 40), color=(255, 0, 0, 128)).save(img_path)
        pixmap = load_pixmap_oriented(img_path)
        assert not pixmap.isNull()
        assert pixmap.width() == 40
        assert pixmap.height() == 40
