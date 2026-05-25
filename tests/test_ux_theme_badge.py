"""테마-인지 카드 색상 + 편집 모드 배지 회귀 가드."""
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


class TestThemeCardIconColors:
    """카드 성별 아이콘 색상이 theme_manager에서 동적으로 공급되는지."""

    def test_light_theme_has_card_icon_colors(self, qapp):
        from src.utils.theme_manager import get_theme_manager
        tm = get_theme_manager()
        tm.set_theme("light")
        colors = tm.get_tree_colors()
        for k in ("card_icon_bg_male", "card_icon_fg_male",
                  "card_icon_bg_female", "card_icon_fg_female"):
            assert k in colors
            assert colors[k].startswith("#")

    def test_dark_theme_has_card_icon_colors(self, qapp):
        from src.utils.theme_manager import get_theme_manager
        tm = get_theme_manager()
        tm.set_theme("dark")
        colors = tm.get_tree_colors()
        for k in ("card_icon_bg_male", "card_icon_fg_male",
                  "card_icon_bg_female", "card_icon_fg_female"):
            assert k in colors

    def test_light_dark_colors_differ(self, qapp):
        from src.utils.theme_manager import get_theme_manager
        tm = get_theme_manager()
        tm.set_theme("light")
        light = tm.get_tree_colors()["card_icon_bg_male"]
        tm.set_theme("dark")
        dark = tm.get_tree_colors()["card_icon_bg_male"]
        assert light != dark


class TestEditModeBadge:
    def test_badge_hidden_by_default(self, main_window):
        # 인물 없을 때 — 배지는 보이지 않음 (panel은 표시되지만 _is_editing=False)
        assert main_window.detail_panel.edit_mode_badge.isHidden() is True

    def test_badge_visible_on_edit_mode(self, main_window):
        from src.models.person import Person
        person = Person(id="p1", name="홍길동")
        main_window.family_tree.add_person(person)
        main_window.detail_panel.set_person(person, main_window.family_tree)
        main_window.detail_panel.start_edit()
        # show()는 부모가 visible할 때만 — isHidden()의 반대로 검증
        assert main_window.detail_panel.edit_mode_badge.isHidden() is False

    def test_badge_hidden_after_save(self, main_window):
        from src.models.person import Person
        person = Person(id="p1", name="홍길동")
        main_window.family_tree.add_person(person)
        main_window.detail_panel.set_person(person, main_window.family_tree)
        main_window.detail_panel.start_edit()
        # 저장 동작 시뮬레이션 — _save가 _is_editing=False 설정 + badge 숨김
        main_window.detail_panel._save()
        assert main_window.detail_panel.edit_mode_badge.isHidden() is True

    def test_badge_hidden_after_cancel(self, main_window):
        from src.models.person import Person
        person = Person(id="p1", name="홍길동")
        main_window.family_tree.add_person(person)
        main_window.detail_panel.set_person(person, main_window.family_tree)
        main_window.detail_panel.start_edit()
        main_window.detail_panel._cancel_edit()
        assert main_window.detail_panel.edit_mode_badge.isHidden() is True

    def test_badge_text_is_localized(self, main_window):
        from src.i18n import tr
        text = main_window.detail_panel.edit_mode_badge.text()
        # tr("label.editing_badge")가 비어있지 않은 문자열을 반환했어야
        assert text != ""
        assert text == tr("label.editing_badge")
