"""신규 SVG 아이콘 + tinted load 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestSvgFilesExist:
    """이모지 대체용 SVG가 resources/icons에 존재."""

    @pytest.mark.parametrize("name", ["search", "calendar", "location", "person"])
    def test_icon_file_exists(self, name):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "resources", "icons", f"{name}.svg",
        )
        assert os.path.exists(path), f"{name}.svg missing in src/resources/icons"


class TestSearchIconIntegration:
    def test_search_input_has_leading_action(self, qapp):
        """검색 placeholder에서 🔍 이모지 제거 + leading action으로 SVG icon."""
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            placeholder = win.search_input.placeholderText()
            # 이모지 제거됐는지
            assert "🔍" not in placeholder
            # leading action으로 등록됐는지 (action 1개 이상)
            assert len(win.search_input.actions()) >= 1
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()


class TestTimelineHeaderIcon:
    def test_header_text_has_no_emoji(self, qapp):
        from src.views.timeline_view import TimelineView
        tv = TimelineView()
        try:
            text = tv.header_label.text()
            assert "📅" not in text
        finally:
            tv.deleteLater()

    def test_tinted_icon_returns_pixmap(self, qapp):
        from src.views.timeline_view import TimelineView
        pix = TimelineView._load_header_icon("calendar", 24, "#FFFFFF")
        assert pix is not None
        assert not pix.isNull()
        assert pix.width() == 24

    def test_unknown_icon_returns_none(self, qapp):
        from src.views.timeline_view import TimelineView
        pix = TimelineView._load_header_icon("nonexistent_icon_xyz", 24, "#000")
        assert pix is None
