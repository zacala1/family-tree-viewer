"""키보드 단축키 도움말 다이얼로그(F1) 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch
from PyQt6.QtGui import QKeySequence


@pytest.fixture
def main_window(qapp):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


class TestShortcutsActionWired:
    def test_action_exists_on_help_menu(self, main_window):
        actions = main_window.help_menu.actions()
        texts = [a.text() for a in actions]
        # & accelerator marker는 다이얼로그에서 stripped 될 수 있어 substring 검색
        assert any("Shortcut" in t or "단축키" in t for t in texts)

    def test_action_has_f1_shortcut(self, main_window):
        seq = main_window.shortcuts_action.shortcut()
        assert seq == QKeySequence("F1")

    def test_dialog_shown_when_triggered(self, main_window):
        """about() static call이 한 번 호출됐는지로 다이얼로그 호출 검증."""
        with patch("src.views.main_window.QMessageBox.about") as mock_about:
            main_window._on_shortcuts()
            assert mock_about.called
            args = mock_about.call_args[0]
            # 두 번째 인자는 title — 'Keyboard' or '단축키' 포함
            title = args[1]
            assert "Shortcut" in title or "단축키" in title
            # 세 번째 인자는 HTML body — 캔버스 화살표 키 안내 포함 (회귀 가드)
            body = args[2]
            assert "Ctrl+Z" in body
            assert "F1" in body
            # 캔버스 화살표 탐색 안내가 포함됐는지 (회귀 가드)
            assert "↑" in body or "↓" in body


class TestShortcutsRetranslation:
    def test_text_updates_with_language(self, main_window):
        """언어 전환 시 단축키 액션 텍스트도 갱신."""
        # 초기 텍스트 저장
        before = main_window.shortcuts_action.text()
        # 다른 언어로 전환 후 _update_menu_texts 호출
        from src.i18n import set_language, get_current_language
        original_lang = get_current_language()
        try:
            other = "en" if original_lang == "ko" else "ko"
            set_language(other)
            main_window._update_menu_texts()
            after = main_window.shortcuts_action.text()
            assert before != after
        finally:
            set_language(original_lang)
            main_window._update_menu_texts()
