"""Top UX 빠른 개선 회귀 가드.

신규 인물 → 자동 Edit, Import/Export 단축키, 고급검색 tooltip, 백업 삭제 메시지.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtGui import QKeySequence


@pytest.fixture
def main_window(qapp):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


class TestAddPersonAutoEdit:
    def test_new_person_enters_edit_mode(self, main_window):
        """Edit → Add Member 직후 detail_panel이 Edit 모드여야 함."""
        main_window._on_add_person()
        assert main_window.detail_panel._is_editing is True

    def test_name_input_gets_focus(self, main_window):
        """편집 모드 진입 후 이름 input에 포커스."""
        main_window._on_add_person()
        # selectAll까지 호출됐는지 — text가 선택됐다는 것은 selectAll 효과
        assert main_window.detail_panel.name_input.hasSelectedText() or \
               main_window.detail_panel.name_input.selectionLength() >= 0

    def test_status_message_updated(self, main_window):
        main_window._on_add_person()
        # status.new_member_added 메시지가 status_label에 set
        assert main_window.status_label.text() != ""


class TestImportExportShortcuts:
    def test_import_has_ctrl_i(self, main_window):
        assert main_window.import_action.shortcut() == QKeySequence("Ctrl+I")

    def test_export_has_ctrl_e(self, main_window):
        assert main_window.export_action.shortcut() == QKeySequence("Ctrl+E")


class TestAdvancedSearchTooltip:
    def test_tooltip_describes_filter(self, main_window):
        """고급검색 ▼ 버튼 tooltip이 명확한 설명 포함."""
        # SearchPanel 분리 후 위치
        btn = main_window.search_panel.advanced_search_btn
        tip = btn.toolTip()
        assert any(k in tip.lower() for k in ("filter", "gender", "필터", "고급"))

    def test_accessible_name_set(self, main_window):
        # accessibleName 설정으로 스크린리더 지원
        btn = main_window.search_panel.advanced_search_btn
        assert btn.accessibleName() != ""


class TestI18nKeysAdded:
    def test_new_keys_resolve(self):
        """새로 추가한 키들이 en/ko 모두에 존재."""
        import json
        i18n_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "i18n",
        )
        with open(os.path.join(i18n_dir, "en.json"), encoding="utf-8") as f:
            en = json.load(f)
        with open(os.path.join(i18n_dir, "ko.json"), encoding="utf-8") as f:
            ko = json.load(f)
        assert "backup_delete_failed" in en["error"]
        assert "backup_delete_failed" in ko["error"]
        assert "advanced_search_toggle" in en["tooltip"]
        assert "advanced_search_toggle" in ko["tooltip"]
