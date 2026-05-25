"""PhotoCarousel 위젯 단위 테스트.

detail_panel에서 분리된 PhotoCarousel을 단위로 테스트. 실제 사진 파일은
load_thumbnail mock으로 대체해 격리.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtGui import QPixmap


@pytest.fixture
def carousel(qapp, monkeypatch):
    """PhotoCarousel + load_thumbnail mock."""
    from src.views.widgets import photo_carousel as mod
    monkeypatch.setattr(mod, "load_thumbnail", lambda path, size: QPixmap(size, size))
    c = mod.PhotoCarousel()
    yield c
    c.deleteLater()


class TestPhotoCounter:
    def test_counter_shows_index_and_total(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        assert carousel.counter_label.text() == "1 / 3"

    def test_counter_zero_for_no_photos(self, carousel):
        carousel.set_photos([])
        assert carousel.counter_label.text() == "0 / 0"

    def test_counter_single_photo(self, carousel):
        carousel.set_photos(["only.jpg"])
        assert carousel.counter_label.text() == "1 / 1"


class TestNavigation:
    def test_prev_wraps_at_start(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._prev()
        assert carousel.current_index() == 2  # wrap to last
        assert carousel.counter_label.text() == "3 / 3"

    def test_next_advances(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._next()
        assert carousel.current_index() == 1
        assert carousel.counter_label.text() == "2 / 3"

    def test_next_wraps_at_end(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._photo_index = 2
        carousel._render()
        carousel._next()
        assert carousel.current_index() == 0

    def test_nav_buttons_disabled_for_single_photo(self, carousel):
        carousel.set_photos(["only.jpg"])
        assert carousel.prev_btn.isEnabled() is False
        assert carousel.next_btn.isEnabled() is False

    def test_nav_buttons_disabled_for_no_photos(self, carousel):
        carousel.set_photos([])
        assert carousel.prev_btn.isEnabled() is False
        assert carousel.next_btn.isEnabled() is False
        assert carousel.primary_btn.isEnabled() is False


class TestSetPrimary:
    def test_set_primary_emits_signal(self, carousel):
        emitted = []
        carousel.set_primary_requested.connect(emitted.append)
        carousel.set_editing(True)
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._photo_index = 2  # c.jpg
        carousel._render()
        carousel._on_set_primary()
        assert emitted == ["c.jpg"]

    def test_primary_button_disabled_when_already_primary(self, carousel):
        carousel.set_editing(True)
        carousel.set_photos(["a.jpg", "b.jpg"])
        # index 0 = primary
        assert carousel.primary_btn.isEnabled() is False

    def test_primary_button_disabled_in_read_only(self, carousel):
        carousel.set_editing(False)
        carousel.set_photos(["a.jpg", "b.jpg"])
        carousel._photo_index = 1
        carousel._render()
        assert carousel.primary_btn.isEnabled() is False

    def test_jump_to_first_moves_to_index_zero(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._photo_index = 2
        carousel.jump_to_first()
        assert carousel.current_index() == 0


class TestAddRemoveSignals:
    def test_add_photo_signal(self, carousel):
        emitted = []
        carousel.add_photo_requested.connect(lambda: emitted.append(1))
        carousel.select_btn.click()
        assert emitted == [1]

    def test_remove_photo_signal_emits_current_path(self, carousel):
        emitted = []
        carousel.remove_photo_requested.connect(emitted.append)
        carousel.set_editing(True)
        carousel.set_photos(["a.jpg", "b.jpg"])
        carousel._photo_index = 1
        carousel._render()
        carousel._on_remove()
        assert emitted == ["b.jpg"]

    def test_remove_does_not_emit_when_not_editing(self, carousel):
        emitted = []
        carousel.remove_photo_requested.connect(emitted.append)
        carousel.set_editing(False)
        carousel.set_photos(["a.jpg"])
        carousel._on_remove()
        assert emitted == []


class TestJumpToLast:
    def test_jumps_to_last_index(self, carousel):
        carousel.set_photos(["a.jpg", "b.jpg", "c.jpg"])
        carousel._photo_index = 0
        carousel.jump_to_last()
        assert carousel.current_index() == 2

    def test_no_op_on_empty(self, carousel):
        carousel.set_photos([])
        carousel.jump_to_last()
        assert carousel.current_index() == 0


class TestPhotoClickSignal:
    def test_clicking_thumbnail_emits_path(self, carousel):
        emitted = []
        carousel.photo_clicked.connect(emitted.append)
        carousel.set_photos(["a.jpg", "b.jpg"])
        carousel._on_photo_clicked()
        assert emitted == ["a.jpg"]

    def test_no_emit_when_empty(self, carousel):
        emitted = []
        carousel.photo_clicked.connect(emitted.append)
        carousel.set_photos([])
        carousel._on_photo_clicked()
        assert emitted == []
