#!/usr/bin/env python3
"""Family Tree Application - 가족관계도 프로그램."""
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.views.main_window import MainWindow
from src.i18n import tr


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """Global exception handler to prevent silent crashes."""
    from src.utils.logger import critical
    import traceback
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    critical(f"Unhandled exception:\n{tb_str}")
    # Call default handler (prints to stderr)
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def load_stylesheet() -> str:
    """스타일시트 로드."""
    style_path = os.path.join(
        os.path.dirname(__file__),
        'src', 'styles', 'modern_style.qss'
    )

    try:
        with open(style_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        from src.utils.logger import error
        error(f"Stylesheet not found: {style_path}")
        return ""


def _get_system_font() -> QFont:
    """Get appropriate system font based on OS."""
    preferred_fonts = ["Malgun Gothic", "맑은 고딕", "Microsoft YaHei", "Segoe UI", "Arial"]
    available = QFontDatabase.families()
    for font_name in preferred_fonts:
        if font_name in available:
            return QFont(font_name, 10)
    return QFont("", 10)


def main():
    """메인 함수."""
    sys.excepthook = _global_exception_handler

    app = QApplication(sys.argv)

    # 앱 정보
    app.setApplicationName("Family Tree")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FamilyTree")

    # 기본 폰트 설정 (OS에 맞는 폰트 자동 선택)
    app.setFont(_get_system_font())

    # 스타일시트 적용
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 샘플 데이터 로드 (옵션)
    sample_path = os.path.join(
        os.path.dirname(__file__),
        'data', 'sample.json'
    )
    if os.path.exists(sample_path):
        from src.utils.file_handler import FileHandler
        tree = FileHandler.load_json(sample_path)
        if tree:
            window.load_tree(tree)
            window.status_label.setText(tr("status.sample_loaded"))

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
