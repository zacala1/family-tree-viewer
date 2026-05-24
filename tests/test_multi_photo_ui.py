"""detail_panel 다중 사진 UI 회귀 가드.

prev/next 네비, 카운터 라벨, set primary, _photo_index 동기화를 검증.
실제 사진 파일 IO는 load_thumbnail을 mock해 격리.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtGui import QPixmap

from src.models.person import Person
from src.models.family_tree import FamilyTree


@pytest.fixture
def panel(qapp, monkeypatch):
    """DetailPanel + load_thumbnail mock (실제 파일 없이 동작)."""
    from src.views.detail_panel import DetailPanel

    # detail_panel은 src.utils.photo_manager.load_thumbnail을 import해 사용
    monkeypatch.setattr(
        "src.views.detail_panel.load_thumbnail",
        lambda path, size: QPixmap(size, size),
    )
    p = DetailPanel()
    yield p
    p.deleteLater()


@pytest.fixture
def person_with_3_photos(panel):
    """photo_paths=[a,b,c]가 로드된 detail_panel."""
    tree = FamilyTree()
    person = Person(id="p1", name="홍길동", photo_paths=["a.jpg", "b.jpg", "c.jpg"])
    tree.add_person(person)
    panel.set_person(person, tree)
    return panel, person


class TestPhotoCounter:
    def test_counter_shows_index_and_total(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        assert panel.photo_counter_label.text() == "1 / 3"

    def test_counter_zero_for_no_photos(self, panel):
        tree = FamilyTree()
        person = Person(id="p", name="A")
        tree.add_person(person)
        panel.set_person(person, tree)
        assert panel.photo_counter_label.text() == "0 / 0"

    def test_counter_single_photo(self, panel):
        tree = FamilyTree()
        person = Person(id="p", name="A", photo_paths=["only.jpg"])
        tree.add_person(person)
        panel.set_person(person, tree)
        assert panel.photo_counter_label.text() == "1 / 1"


class TestNavigation:
    def test_prev_wraps_at_start(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        # index 0에서 prev → index 2 (3개 wrap)
        panel._prev_photo()
        assert panel._photo_index == 2
        assert panel.photo_counter_label.text() == "3 / 3"

    def test_next_advances(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        panel._next_photo()
        assert panel._photo_index == 1
        assert panel.photo_counter_label.text() == "2 / 3"

    def test_next_wraps_at_end(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        panel._photo_index = 2
        panel._load_photo()
        panel._next_photo()
        assert panel._photo_index == 0  # wrap

    def test_nav_buttons_disabled_for_single_photo(self, panel):
        tree = FamilyTree()
        person = Person(id="p", name="A", photo_paths=["only.jpg"])
        tree.add_person(person)
        panel.set_person(person, tree)
        assert panel.prev_photo_btn.isEnabled() is False
        assert panel.next_photo_btn.isEnabled() is False

    def test_nav_buttons_disabled_for_no_photos(self, panel):
        tree = FamilyTree()
        person = Person(id="p", name="A")
        tree.add_person(person)
        panel.set_person(person, tree)
        assert panel.prev_photo_btn.isEnabled() is False
        assert panel.next_photo_btn.isEnabled() is False
        assert panel.set_primary_photo_btn.isEnabled() is False


class TestSetPrimary:
    def test_set_primary_moves_to_index_zero(self, person_with_3_photos):
        panel, person = person_with_3_photos
        panel._is_editing = True
        panel._photo_index = 2  # c.jpg
        panel._set_primary_photo()
        # c가 맨 앞으로
        assert person.photo_paths == ["c.jpg", "a.jpg", "b.jpg"]
        assert person.photo_path == "c.jpg"
        # 인덱스는 0 (primary)으로
        assert panel._photo_index == 0

    def test_set_primary_disabled_when_already_primary(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        panel._is_editing = True
        panel._photo_index = 0  # 이미 primary
        panel._update_photo_nav_controls()
        assert panel.set_primary_photo_btn.isEnabled() is False

    def test_set_primary_disabled_in_read_only(self, person_with_3_photos):
        panel, _ = person_with_3_photos
        panel._is_editing = False
        panel._photo_index = 1
        panel._update_photo_nav_controls()
        assert panel.set_primary_photo_btn.isEnabled() is False


class TestRemoveAdjustsIndex:
    def test_remove_last_photo_decrements_index(self, person_with_3_photos, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        # 확인 다이얼로그 자동 Yes
        monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)
        # delete_photo 실제 파일 삭제는 mock
        monkeypatch.setattr("src.views.detail_panel.delete_photo", lambda p: True)
        panel, person = person_with_3_photos
        panel._is_editing = True
        panel._photo_index = 2  # 마지막 c.jpg
        panel._load_photo()
        panel._remove_photo()
        # c.jpg 제거 → 인덱스가 1로 보정
        assert person.photo_paths == ["a.jpg", "b.jpg"]
        assert panel._photo_index == 1

    def test_remove_only_photo_clears(self, panel, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)
        monkeypatch.setattr("src.views.detail_panel.delete_photo", lambda p: True)
        tree = FamilyTree()
        person = Person(id="p", name="A", photo_paths=["only.jpg"])
        tree.add_person(person)
        panel.set_person(person, tree)
        panel._is_editing = True
        panel._load_photo()
        panel._remove_photo()
        assert person.photo_paths == []
        assert panel._photo_index == 0
        assert panel.photo_counter_label.text() == "0 / 0"


class TestSwitchPersonResetsIndex:
    def test_index_resets_to_zero(self, panel):
        tree = FamilyTree()
        p1 = Person(id="p1", name="A", photo_paths=["a.jpg", "b.jpg"])
        p2 = Person(id="p2", name="B", photo_paths=["x.jpg", "y.jpg", "z.jpg"])
        tree.add_person(p1)
        tree.add_person(p2)

        panel.set_person(p1, tree)
        panel._photo_index = 1
        panel._load_photo()

        # 다른 인물로 전환 → index 0으로 초기화
        panel.set_person(p2, tree)
        assert panel._photo_index == 0
        assert panel.photo_counter_label.text() == "1 / 3"
