"""UI 텍스트 갱신 + 언어 메뉴 + 테마 토글 조율자.

언어 전환 시 메뉴·패널·상태바·DetailPanel·인물 목록의 모든 텍스트를 한 번에
재번역. MainWindow가 보유한 UI 컴포넌트 참조에 의존하므로 main_window를
넘겨받아 직접 호출.
"""
from __future__ import annotations

from PyQt6.QtGui import QAction

from ..i18n import (
    tr,
    set_language,
    get_available_languages,
    get_current_language,
)
from ..utils.theme_manager import get_theme_manager


class LocalizationManager:
    """언어 메뉴 + 텍스트 cascade refresh + 테마 토글 조율자."""

    def __init__(self, main_window):
        self._win = main_window

    # === 언어 메뉴 ===

    def setup_language_menu(self) -> None:
        """언어 메뉴를 현재 가용 언어로 채움 (현재 언어에 체크)."""
        win = self._win
        win.language_menu.clear()
        win.language_actions = {}

        current_lang = get_current_language()
        for lang_code, lang_name in get_available_languages().items():
            action = QAction(lang_name, win)
            action.setCheckable(True)
            action.setChecked(lang_code == current_lang)
            action.triggered.connect(
                lambda checked, lc=lang_code: self.change_language(lc)
            )
            win.language_menu.addAction(action)
            win.language_actions[lang_code] = action

    def change_language(self, lang_code: str) -> None:
        """언어 변경 + 메뉴 체크 표시 갱신 + 모든 UI 텍스트 refresh."""
        set_language(lang_code)
        self.update_all_texts()
        for code, action in self._win.language_actions.items():
            action.setChecked(code == lang_code)

    # === 텍스트 cascade ===

    def update_all_texts(self) -> None:
        """언어 변경 시 호출되는 최상위 entry. 모든 하위 갱신 트리거."""
        win = self._win
        win._update_title()
        self._update_menu_texts()
        self._update_panel_texts()
        self._update_statusbar_texts()
        win.detail_panel.update_ui_texts()
        win._update_person_list()

    def _update_menu_texts(self) -> None:
        win = self._win
        win.file_menu.setTitle(tr("menu.file"))
        win.edit_menu.setTitle(tr("menu.edit"))
        win.view_menu.setTitle(tr("menu.view"))
        win.help_menu.setTitle(tr("menu.help"))

        win.new_action.setText(tr("menu_item.new"))
        win.open_action.setText(tr("menu_item.open"))
        win.save_action.setText(tr("menu_item.save"))
        win.save_as_action.setText(tr("menu_item.save_as"))
        win.import_action.setText(tr("menu_item.import"))
        win.export_action.setText(tr("menu_item.export"))
        win.export_pdf_action.setText(tr("menu_item.export_pdf"))
        win.exit_action.setText(tr("menu_item.exit"))
        win.add_person_action.setText(tr("menu_item.add_person"))
        win.delete_person_action.setText(tr("menu_item.delete_person"))
        win.undo_action.setText(tr("button.undo"))
        win.redo_action.setText(tr("button.redo"))
        win.zoom_in_action.setText(tr("menu_item.zoom_in"))
        win.zoom_out_action.setText(tr("menu_item.zoom_out"))
        win.zoom_reset_action.setText(tr("menu_item.zoom_reset"))
        win.theme_action.setText(tr("menu_item.toggle_theme"))
        win.about_action.setText(tr("menu_item.about"))
        win.shortcuts_action.setText(tr("menu_item.shortcuts"))
        win.welcome_action.setText(tr("menu_item.welcome"))
        win.recent_menu.setTitle(tr("menu_item.recent_files"))
        win._refresh_recent_menu()
        win.language_menu.setTitle(tr("menu_item.language"))

    def _update_panel_texts(self) -> None:
        win = self._win
        win.list_header.setText(tr("panel.family_members"))
        win.add_person_btn.setText(tr("button.add_member"))
        # SearchPanel이 placeholder·콤보·라벨·툴팁 재번역
        win.search_panel.update_ui_texts()

    def _update_statusbar_texts(self) -> None:
        win = self._win
        win.status_label.setText(tr("status.ready"))
        count = len(win.family_tree.get_all_persons())
        win.count_label.setText(tr("status.member_count", count=count))
        if hasattr(win, "rel_count_label"):
            win.rel_count_label.setText(
                tr("status.relationship_count", count=win.family_tree.relationship_count)
            )

    # === 테마 ===

    def toggle_theme(self) -> None:
        """라이트/다크 테마 전환 + 상태바 안내."""
        win = self._win
        new_theme = get_theme_manager().toggle_theme()
        win.status_label.setText(tr("status.theme_changed", theme=new_theme))
