"""테마 관리자 - 라이트/다크 모드 전환."""
import os
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal


class ThemeManager(QObject):
    """앱 테마를 관리하는 클래스."""

    theme_changed = pyqtSignal(str)  # 'light' or 'dark'

    def __init__(self):
        super().__init__()
        self._current_theme = 'light'
        self._styles_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'styles'
        )

    @property
    def current_theme(self) -> str:
        """현재 테마 반환."""
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """다크 모드 여부."""
        return self._current_theme == 'dark'

    def set_theme(self, theme: str) -> bool:
        """테마 설정.

        Args:
            theme: 'light' 또는 'dark'

        Returns:
            성공 여부
        """
        if theme not in ('light', 'dark'):
            return False

        if theme == self._current_theme:
            return True

        stylesheet = self._load_stylesheet(theme)
        if stylesheet is None:
            return False

        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            self._current_theme = theme
            self.theme_changed.emit(theme)
            return True

        return False

    def toggle_theme(self) -> str:
        """테마 토글.

        Returns:
            새 테마 이름
        """
        new_theme = 'dark' if self._current_theme == 'light' else 'light'
        self.set_theme(new_theme)
        return new_theme

    def _load_stylesheet(self, theme: str) -> Optional[str]:
        """스타일시트 파일 로드."""
        filename = 'dark_style.qss' if theme == 'dark' else 'modern_style.qss'
        filepath = os.path.join(self._styles_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            from .logger import error
            error(f"Stylesheet not found: {filepath}")
            return None

    def get_tree_colors(self) -> dict:
        """현재 테마에 맞는 트리 캔버스 색상 반환."""
        if self._current_theme == 'dark':
            return {
                'background': '#181825',
                'card_bg': '#1E1E2E',
                'card_border': '#45475A',
                'card_selected_border': '#89B4FA',
                'card_highlighted_border': '#74C7EC',
                'text': '#CDD6F4',
                'text_secondary': '#6C7086',
                'line': '#585B70',
                'line_highlighted': '#89B4FA',
                'spouse_line': '#74C7EC',
                'spouse_line_divorced': '#45475A',
                'shadow': '#11111B',
            }
        else:
            return {
                'background': '#FAF6F1',
                'card_bg': '#FFFFFF',
                'card_border': '#D4C4B5',
                'card_selected_border': '#8B7355',
                'card_highlighted_border': '#A08060',
                'text': '#4A4A4A',
                'text_secondary': '#888888',
                'line': '#C4B4A5',
                'line_highlighted': '#8B7355',
                'spouse_line': '#B09080',
                'spouse_line_divorced': '#CCCCCC',
                'shadow': '#00000020',
            }


# 전역 인스턴스
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """테마 관리자 인스턴스 반환 (싱글톤)."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
