"""최근 파일 메뉴 관리자.

main_window에서 분리된 모듈 — QSettings 기반 영속화, 자동 정리,
메뉴 동기 렌더링을 한 책임으로 묶음.

사용 예:
    rfm = RecentFilesManager(parent_widget)
    rfm.file_selected.connect(self._load_file)
    rfm.bind_menu(self.recent_menu)  # menu reference 보관 + 즉시 갱신
    # 사용자가 파일 열기/저장 성공 시:
    rfm.add(path)
"""
from __future__ import annotations

import os
from typing import List, Optional

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMessageBox

from ...i18n import tr


_SETTINGS_ORG = "FamilyTree"
_SETTINGS_APP = "FamilyTree"
_RECENT_FILES_KEY = "recentFiles"


class RecentFilesManager(QObject):
    """QSettings 기반 최근 파일 목록 + 메뉴 렌더링.

    Signals:
        file_selected(str): 사용자가 메뉴에서 항목 클릭 시 절대 경로 emit.
                            존재하지 않는 파일은 자동 정리 후 emit 안 함.
    """

    file_selected = pyqtSignal(str)

    DEFAULT_MAX = 5

    def __init__(self, parent: Optional[QObject] = None, max_count: int = DEFAULT_MAX):
        super().__init__(parent)
        self._max = max_count
        self._menu: Optional[QMenu] = None
        self._parent_widget = parent  # QMessageBox 부모용

    # === Public API ===

    def bind_menu(self, menu: QMenu) -> None:
        """메뉴 reference 보관 + 즉시 항목 채움. add/clear 시 자동 갱신."""
        self._menu = menu
        self.refresh_menu()

    def add(self, file_path: str) -> None:
        """최근 파일 목록에 추가 (중복 제거, 최신을 맨 앞으로, 최대 N개)."""
        if not file_path:
            return
        abs_path = os.path.abspath(file_path)
        settings = self._settings()
        paths = settings.value(_RECENT_FILES_KEY, [], type=list)
        # 대소문자 무시 (Windows 경로)
        paths = [p for p in paths if os.path.normcase(p) != os.path.normcase(abs_path)]
        paths.insert(0, abs_path)
        paths = paths[: self._max]
        settings.setValue(_RECENT_FILES_KEY, paths)
        self.refresh_menu()

    def load(self) -> List[str]:
        """현재 목록 — 존재하지 않는 파일은 자동 제거."""
        settings = self._settings()
        paths = settings.value(_RECENT_FILES_KEY, [], type=list)
        existing = [p for p in paths if os.path.exists(p)]
        if len(existing) != len(paths):
            settings.setValue(_RECENT_FILES_KEY, existing)
        return existing

    def clear(self) -> None:
        """전체 목록 삭제 + 메뉴 갱신."""
        self._settings().setValue(_RECENT_FILES_KEY, [])
        self.refresh_menu()

    def refresh_menu(self) -> None:
        """bound된 메뉴를 현재 목록으로 다시 렌더링."""
        if self._menu is None:
            return
        self._menu.clear()
        paths = self.load()
        if not paths:
            empty = QAction(tr("menu_item.recent_empty"), self._menu)
            empty.setEnabled(False)
            self._menu.addAction(empty)
            return
        for i, path in enumerate(paths, 1):
            display = f"{i}. {os.path.basename(path)}"
            action = QAction(display, self._menu)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._on_pick(p))
            self._menu.addAction(action)
        self._menu.addSeparator()
        clear_action = QAction(tr("menu_item.recent_clear"), self._menu)
        clear_action.triggered.connect(self.clear)
        self._menu.addAction(clear_action)

    def menu_title(self) -> str:
        """메뉴 제목용 i18n key (외부에서 setTitle 호출에 사용)."""
        return tr("menu_item.recent_files")

    # === Internal ===

    def _on_pick(self, file_path: str) -> None:
        """메뉴 항목 클릭 — 존재 확인 후 file_selected emit (또는 자동 정리)."""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self._parent_widget,
                tr("error.file_not_found_title"),
                tr("error.file_not_found_message", path=file_path),
            )
            self.refresh_menu()  # 사라진 파일 자동 정리
            return
        self.file_selected.emit(file_path)

    @staticmethod
    def _settings() -> QSettings:
        return QSettings(_SETTINGS_ORG, _SETTINGS_APP)
