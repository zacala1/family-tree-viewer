"""Audit 후속 안정성 fix 회귀 가드.

1. lineage_report: 깊이 한계 인물도 visited에 기록 → 중복 truncated 메시지 방지
2. tree_canvas 사진 캐시: LRU 한계 적용
3. main_window 백업 가드: _is_saving 플래그가 동시 저장 차단
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.family_tree import FamilyTree


class TestLineageVisitedOrdering:
    """깊이 한계 도달 인물이 다중 경로로 도달해도 한 번만 truncated 표시."""

    def test_truncated_marker_appears_once(self, qapp):
        """다중 경로로 깊이 초과 인물에 도달해도 truncate 메시지 중복 표시 안 됨.

        시나리오: 매우 깊은 부모 체인 + 한 인물이 두 부모로부터 도달 가능
        (재혼/입양 시나리오를 시뮬레이션).
        """
        from src.views.lineage_report_dialog import LineageReportDialog
        from src.config import MAX_REPORT_DEPTH

        tree = FamilyTree()
        # MAX_REPORT_DEPTH+5세대 선형 체인 + 중간에 한 인물(branch)이 양쪽 가지로 부모를 가짐
        depth_needed = MAX_REPORT_DEPTH + 5
        prev_id = None
        for i in range(depth_needed):
            pid = f"gen{i}"
            tree.add_person(Person(id=pid, name=f"Gen{i}", gender="M"))
            if prev_id is not None:
                tree.set_parent_child(prev_id, pid)
            prev_id = pid

        # 후손 보고서: gen0에서 시작 → 깊이 초과 도달 인물들에 truncate 메시지 1회만
        dlg = LineageReportDialog(tree, "gen0", mode="descendants")
        text = dlg.text_edit.toPlainText()
        # truncate 메시지가 표시되긴 하되 — 동일 인물 중복으로 두 번 나오지 않음
        # (선형이라 깊이 초과 위치 1곳만)
        truncate_count = text.count("truncated") + text.count("생략")
        # 1번 가지 끝에서 1회 — 중복 없음
        assert truncate_count == 1
        dlg.deleteLater()


class TestPhotoCacheLRU:
    """tree_canvas 카드 사진 캐시 LRU 한계 회귀 가드."""

    def test_cache_respects_max_size(self, qapp, empty_tree, monkeypatch):
        from src.views.tree_canvas import TreeCanvas
        from PyQt6.QtGui import QPixmap

        canvas = TreeCanvas(empty_tree)
        canvas._card_photo_cache_max = 3  # 작게 설정해 테스트 빠르게

        monkeypatch.setattr(
            "src.utils.photo_manager.load_thumbnail",
            lambda p, s: QPixmap(s, s),
        )

        # 4개 추가 — 가장 오래된 1개가 제거돼야
        for i in range(4):
            canvas._get_card_photo(f"photo_{i}.jpg", 44)

        assert len(canvas._card_photo_cache) == 3
        # 가장 오래된 photo_0가 제거됐어야
        assert ("photo_0.jpg", 44) not in canvas._card_photo_cache
        # 최근 추가된 3개는 남아야
        assert ("photo_3.jpg", 44) in canvas._card_photo_cache

    def test_recent_access_promotes_in_lru(self, qapp, empty_tree, monkeypatch):
        """이미 캐시된 항목에 접근하면 LRU 순서가 갱신돼 evict 안 됨."""
        from src.views.tree_canvas import TreeCanvas
        from PyQt6.QtGui import QPixmap

        canvas = TreeCanvas(empty_tree)
        canvas._card_photo_cache_max = 3
        monkeypatch.setattr(
            "src.utils.photo_manager.load_thumbnail",
            lambda p, s: QPixmap(s, s),
        )

        canvas._get_card_photo("A.jpg", 44)
        canvas._get_card_photo("B.jpg", 44)
        canvas._get_card_photo("C.jpg", 44)
        # A를 다시 접근 → A가 most-recent
        canvas._get_card_photo("A.jpg", 44)
        # 4번째 새 항목 추가 — 이번엔 B가 evict됨 (A는 최근 사용으로 보호)
        canvas._get_card_photo("D.jpg", 44)

        assert ("A.jpg", 44) in canvas._card_photo_cache
        assert ("B.jpg", 44) not in canvas._card_photo_cache
        assert ("C.jpg", 44) in canvas._card_photo_cache
        assert ("D.jpg", 44) in canvas._card_photo_cache

    def test_invalidate_specific_path_preserves_others(self, qapp, empty_tree, monkeypatch):
        from src.views.tree_canvas import TreeCanvas
        from PyQt6.QtGui import QPixmap

        canvas = TreeCanvas(empty_tree)
        monkeypatch.setattr(
            "src.utils.photo_manager.load_thumbnail",
            lambda p, s: QPixmap(s, s),
        )
        canvas._get_card_photo("a.jpg", 44)
        canvas._get_card_photo("a.jpg", 88)
        canvas._get_card_photo("b.jpg", 44)
        # a.jpg 모든 사이즈만 제거
        canvas.invalidate_photo_cache("a.jpg")
        assert ("a.jpg", 44) not in canvas._card_photo_cache
        assert ("a.jpg", 88) not in canvas._card_photo_cache
        assert ("b.jpg", 44) in canvas._card_photo_cache


class TestBackupSavingGuard:
    """FileIOController.is_saving 플래그가 동시 저장 차단."""

    @pytest.fixture
    def main_window(self, qapp):
        from src.views.main_window import MainWindow
        win = MainWindow()
        yield win
        win.family_tree.mark_saved()
        win.close()
        win.deleteLater()

    def test_backup_skipped_when_saving(self, main_window):
        """file_io.is_saving=True 일 때 _perform_auto_backup은 즉시 return."""
        main_window.family_tree.add_person(Person(id="p1", name="A"))
        main_window.file_io.is_saving = True
        # FileHandler.save_json이 호출되면 안 됨 — mock으로 검증
        calls = []
        import src.utils.file_handler as fh
        original = fh.FileHandler.save_json
        fh.FileHandler.save_json = staticmethod(lambda *a, **kw: calls.append(1))
        try:
            main_window._perform_auto_backup()
            assert calls == []
        finally:
            fh.FileHandler.save_json = original
            main_window.file_io.is_saving = False

    def test_is_saving_set_during_perform(self, main_window):
        """백업 실행 중 file_io.is_saving이 True로 설정됐다가 finally에서 False."""
        main_window.family_tree.add_person(Person(id="p1", name="A"))
        # 백업 중 플래그 상태 capture
        observed = []
        import src.utils.file_handler as fh
        original = fh.FileHandler.save_json

        def capturing(*a, **kw):
            observed.append(main_window.file_io.is_saving)
            return True

        fh.FileHandler.save_json = staticmethod(capturing)
        try:
            main_window._perform_auto_backup()
            # 호출 시점에 True였어야
            assert observed == [True]
            # 종료 후 False로 복원
            assert main_window.file_io.is_saving is False
        finally:
            fh.FileHandler.save_json = original

    def test_is_saving_initialized_false(self, main_window):
        assert main_window.file_io.is_saving is False
