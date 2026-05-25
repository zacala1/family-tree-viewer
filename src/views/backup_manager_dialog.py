"""백업 관리 다이얼로그 — 자동 백업 목록 조회·복구·삭제·폴더 열기."""

import os
from datetime import datetime
from typing import Optional

from ..utils.theme_manager import get_theme_manager

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QDialogButtonBox,
)

from ..i18n import tr


class BackupManagerDialog(QDialog):
    """자동 백업 파일을 목록으로 보여주고 복구/삭제/폴더 열기 제공.

    선택된 백업 경로를 `selected_path` 속성에 저장. 호출자가
    `exec()` 결과가 Accepted면 `selected_path`를 받아 로드 수행.
    """

    def __init__(self, backup_dir: str, parent=None):
        super().__init__(parent)
        self.backup_dir = backup_dir
        self.selected_path: Optional[str] = None

        self.setWindowTitle(tr("dialog.backup_manager_title"))
        self.resize(560, 380)

        self._build_ui()
        self._reload_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 백업 폴더 경로 표시
        self.path_label = QLabel(
            tr("dialog.backup_folder_label", path=self.backup_dir)
        )
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.path_label)

        # 백업 목록
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_restore)
        layout.addWidget(self.list_widget)

        # 정보 라벨 (빈 상태 안내) — theme의 text_muted (WCAG AA 대비 보장)
        self.info_label = QLabel("")
        _muted = get_theme_manager().get_tree_colors().get("text_muted", "#777777")
        self.info_label.setStyleSheet(f"color: {_muted};")
        layout.addWidget(self.info_label)

        # 액션 버튼 행
        action_row = QHBoxLayout()

        self.restore_btn = QPushButton(tr("button.restore"))
        self.restore_btn.clicked.connect(self._on_restore)
        action_row.addWidget(self.restore_btn)

        self.delete_btn = QPushButton(tr("context.delete"))
        self.delete_btn.clicked.connect(self._on_delete)
        action_row.addWidget(self.delete_btn)

        self.open_folder_btn = QPushButton(tr("button.open_folder"))
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        action_row.addWidget(self.open_folder_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

        # 닫기 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _reload_list(self):
        """백업 폴더 스캔 → 목록 갱신."""
        self.list_widget.clear()

        if not os.path.exists(self.backup_dir):
            self.info_label.setText(tr("message.no_backups"))
            self._set_actions_enabled(False)
            return

        try:
            entries = [
                f for f in os.listdir(self.backup_dir)
                if f.startswith("autosave_") and f.endswith(".json")
            ]
        except OSError:
            entries = []

        if not entries:
            self.info_label.setText(tr("message.no_backups"))
            self._set_actions_enabled(False)
            return

        # 최신순 정렬 (파일명에 ISO 타임스탬프 포함되므로 역정렬로 충분)
        entries.sort(reverse=True)
        self.info_label.setText(
            tr("message.backup_count", count=len(entries))
        )

        for name in entries:
            full_path = os.path.join(self.backup_dir, name)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                size_kb = os.path.getsize(full_path) / 1024
                label = f"{mtime.strftime('%Y-%m-%d %H:%M:%S')}    ({size_kb:.1f} KB)    {name}"
            except OSError:
                label = name

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            self.list_widget.addItem(item)

        self._set_actions_enabled(True)
        self.list_widget.setCurrentRow(0)

    def _set_actions_enabled(self, enabled: bool):
        self.restore_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def _selected_path(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_restore(self):
        path = self._selected_path()
        if not path:
            return
        # 현재 수정사항 손실 경고는 호출자(main_window)가 _check_save로 처리
        self.selected_path = path
        self.accept()

    def _on_delete(self):
        path = self._selected_path()
        if not path:
            return

        confirm = QMessageBox.question(
            self,
            tr("dialog.delete_backup_title"),
            tr("dialog.delete_backup_message", filename=os.path.basename(path)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            os.remove(path)
        except OSError as exc:
            # 사용자에게 친화적 메시지 (원본 OSError 문자열 노출 회피)
            QMessageBox.warning(
                self,
                tr("dialog.delete_backup_title"),
                tr("error.backup_delete_failed", filename=os.path.basename(path)),
            )
            return

        self._reload_list()

    def _on_open_folder(self):
        """OS 파일 탐색기로 백업 폴더 열기."""
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir, exist_ok=True)
            except OSError as exc:
                QMessageBox.warning(self, self.windowTitle(), str(exc))
                return
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.backup_dir))
