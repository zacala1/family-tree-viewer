"""애니메이션 헬퍼 + dialog fade 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QWidget, QDialog


class TestAnimationHelper:
    def test_fade_in_attaches_animation(self, qapp):
        from src.utils.animation import fade_in_widget
        w = QWidget()
        fade_in_widget(w)
        # GC 방지용 attribute가 설정돼 있어야
        assert hasattr(w, "_fade_in_anim")
        # 시작 opacity는 0이었어야
        # (animation이 시작됐으므로 현재는 transition 중 — 정확한 값보다 attribute 존재만 확인)
        w.deleteLater()

    def test_fade_in_property_returns_anim(self, qapp):
        from src.utils.animation import fade_in_property
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect()
        anim = fade_in_property(effect, b"opacity", end_value=1.0, start_value=0.0)
        assert anim is not None
        # 시작 후 state는 Running
        from PyQt6.QtCore import QAbstractAnimation
        assert anim.state() == QAbstractAnimation.State.Running

    def test_default_duration(self, qapp):
        from src.utils.animation import fade_in_widget, _DEFAULT_FADE_DURATION_MS
        w = QWidget()
        fade_in_widget(w)
        assert w._fade_in_anim.duration() == _DEFAULT_FADE_DURATION_MS


class TestDialogShowEventTriggersFade:
    def test_event_dialog_attaches_fade(self, qapp):
        from src.views.event_dialog import EventDialog
        dlg = EventDialog()
        dlg.show()  # showEvent 트리거
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()

    def test_lineage_dialog_attaches_fade(self, qapp, sample_family):
        from src.views.lineage_report_dialog import LineageReportDialog
        tree, ids = sample_family
        dlg = LineageReportDialog(tree, ids["father"], mode="descendants")
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()

    def test_backup_manager_dialog_attaches_fade(self, qapp, tmp_path):
        from src.views.backup_manager_dialog import BackupManagerDialog
        dlg = BackupManagerDialog(str(tmp_path))
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()

    def test_photo_lightbox_attaches_fade(self, qapp, tmp_path):
        from src.views.detail_panel import _PhotoLightbox
        # 빈 path로 호출 — pixmap이 null이어도 dialog는 뜸
        img = tmp_path / "test.png"
        from PIL import Image
        Image.new("RGB", (10, 10)).save(img)
        dlg = _PhotoLightbox(str(img), "test")
        dlg.show()
        try:
            assert hasattr(dlg, "_fade_in_anim")
        finally:
            dlg.close()
            dlg.deleteLater()


class TestTimelinePageFade:
    def test_page_change_attaches_fade(self, qapp):
        from src.views.timeline_view import TimelineView
        from src.models.person import Person
        from src.models.event import Event
        from src.models.family_tree import FamilyTree

        tree = FamilyTree()
        person = Person(id="p1", name="A")
        for i in range(250):  # PAGE_SIZE(100) 초과 → 페이지 네비 가능
            person.events.append(Event(title=f"E{i}", year=2000 + i))
        tree.add_person(person)

        tl = TimelineView()
        tl.set_family_tree(tree)
        tl.set_person(person)

        # next_page 호출 → fade animation 시작
        tl._next_page()
        assert hasattr(tl, "_page_fade_anim")
        tl.deleteLater()
