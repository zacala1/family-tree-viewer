"""_run_with_progress의 progress callback 인프라 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def main_window(qapp):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


class TestRunWithProgressBackwardCompat:
    """기존 호출 (supports_progress=False) 동작 보존."""

    def test_legacy_signature_still_works(self, main_window):
        """task() 호출 — callback 없음."""
        result = main_window._run_with_progress(
            "test", "running...", lambda: "done"
        )
        assert result == "done"

    def test_legacy_exception_path(self, main_window, monkeypatch):
        """예외 발생 시 None 반환 — 기존 동작."""
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: None)

        def fails():
            raise ValueError("test")

        result = main_window._run_with_progress("test", "...", fails)
        assert result is None


class TestProgressCallback:
    """supports_progress=True에서 task가 callback을 받고 호출 가능."""

    def test_task_receives_callback(self, main_window):
        captured = []

        def task_with_progress(progress_cb):
            # callback이 callable이어야
            assert callable(progress_cb)
            progress_cb(0, 10, "starting")
            progress_cb(5, 10, "halfway")
            progress_cb(10, 10, "done")
            captured.append("called")
            return "result"

        result = main_window._run_with_progress(
            "test", "running...", task_with_progress, supports_progress=True
        )
        assert result == "result"
        assert captured == ["called"]

    def test_callback_does_not_crash_on_zero_total(self, main_window):
        """total=0이어도 callback 안전 (division by zero 방지)."""
        def task(progress_cb):
            progress_cb(0, 0, "")
            return "ok"

        result = main_window._run_with_progress(
            "test", "...", task, supports_progress=True
        )
        assert result == "ok"

    def test_label_only_update_supported(self, main_window):
        """label 변경 callback 호출도 안전."""
        def task(progress_cb):
            progress_cb(50, 100, "Phase 1")
            return "done"

        result = main_window._run_with_progress(
            "test", "initial", task, supports_progress=True
        )
        assert result == "done"

    def test_exception_in_progress_task_propagated(self, main_window, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "critical", lambda *a, **kw: None)

        def fails(progress_cb):
            progress_cb(0, 10, "starting")
            raise RuntimeError("boom")

        result = main_window._run_with_progress(
            "test", "...", fails, supports_progress=True
        )
        assert result is None
