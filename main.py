#!/usr/bin/env python3
"""Family Tree Application - 가족관계도 프로그램."""
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.views.main_window import MainWindow


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
        print(f"스타일시트를 찾을 수 없습니다: {style_path}")
        return ""


def main():
    """메인 함수."""
    # High DPI 지원
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 앱 정보
    app.setApplicationName("Family Tree")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FamilyTree")

    # 기본 폰트 설정
    font = QFont("맑은 고딕", 10)
    app.setFont(font)

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
            window.family_tree = tree
            window.tree_canvas.set_family_tree(tree)
            window._update_person_list()
            window.status_label.setText("샘플 데이터 로드됨")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
