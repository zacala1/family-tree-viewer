"""자동 백업 컨트롤러 — 타이머·정리·복구 흐름을 한 곳에서 관리.

MainWindow는 시작/종료만 호출하면 되도록 캡슐화. 시작 시 1시간 이내 백업이
있으면 사용자에게 복구 제안, N분 주기로 수정된 트리를 autosave_*.json으로 저장,
N개를 초과하면 가장 오래된 것부터 정리.

MainWindow는 다음을 노출해야 한다:
- `family_tree`, `file_io` (FileIOController — is_saving 동기 가드)
- `_check_save()`, `_update_title()`, `_flash_status(msg)`, `current_file_path`
- 자식 Qt 부모로 사용되므로 QObject 인스턴스
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from ..config import AUTO_BACKUP_INTERVAL_MINUTES, MAX_BACKUP_COUNT, BACKUP_DIR
from ..utils.file_handler import FileHandler
from ..i18n import tr


class BackupController:
    """자동 백업 + 복구 다이얼로그 + 정리 흐름 조율자."""

    def __init__(self, main_window):
        self._win = main_window
        self._timer: QTimer | None = None

    # === 라이프사이클 ===

    def start(self) -> None:
        """주기적 백업 타이머 시작."""
        self._timer = QTimer(self._win)
        self._timer.timeout.connect(self.perform_auto_backup)
        self._timer.start(AUTO_BACKUP_INTERVAL_MINUTES * 60 * 1000)

    def stop(self) -> None:
        """창 닫기 시 타이머 정지 + 명시적 deleteLater로 lifecycle 명확화.

        MainWindow가 parent라서 결국 정리되지만, stop() 직후 perform_auto_backup
        tick이 큐에 남아있을 가능성을 차단하려면 즉시 deleteLater가 안전.
        """
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None

    # === 경로 ===

    @staticmethod
    def get_backup_dir() -> str:
        """백업 디렉토리 경로 (~/<BACKUP_DIR>)."""
        return os.path.join(os.path.expanduser("~"), BACKUP_DIR)

    # === 자동 백업 ===

    def perform_auto_backup(self) -> None:
        """현재 트리를 autosave_*.json으로 저장 (수정된 경우에만).

        file_io.is_saving 가드로 사용자 수동 저장 / 동시 백업 tick과 충돌 방지.
        실패 시 조용히 패스 (사용자 흐름 차단 X) — 다음 tick에 재시도.
        """
        win = self._win
        if win.file_io.is_saving:
            return
        if not win.family_tree.is_modified:
            return
        if not win.family_tree.get_all_persons():
            return

        win.file_io.is_saving = True
        try:
            backup_dir = self.get_backup_dir()
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"autosave_{timestamp}.json")

            FileHandler.save_json(win.family_tree, backup_path)
            self._cleanup_old_backups()
        finally:
            win.file_io.is_saving = False

    def _cleanup_old_backups(self) -> None:
        """가장 오래된 백업 정리 — MAX_BACKUP_COUNT 개만 유지."""
        backup_dir = self.get_backup_dir()
        if not os.path.exists(backup_dir):
            return

        backups = sorted(
            [
                f for f in os.listdir(backup_dir)
                if f.startswith("autosave_") and f.endswith(".json")
            ],
            reverse=True,
        )

        for old_backup in backups[MAX_BACKUP_COUNT:]:
            try:
                os.remove(os.path.join(backup_dir, old_backup))
            except OSError:
                pass

    # === 사용자 액션 ===

    def open_manager(self) -> None:
        """백업 관리 다이얼로그 — 복구/삭제/폴더 열기."""
        from .backup_manager_dialog import BackupManagerDialog

        win = self._win
        dlg = BackupManagerDialog(self.get_backup_dir(), win)
        if dlg.exec() == BackupManagerDialog.DialogCode.Accepted and dlg.selected_path:
            if win._check_save():
                if win.file_io.load(dlg.selected_path):
                    # 백업에서 복구한 경우 현재 파일 경로는 비워서 다음 저장이
                    # Save As로 가도록 (실수 덮어쓰기 방지)
                    win.current_file_path = None
                    win._update_title()
                    win._flash_status(tr("status.recovered_from_backup"))

    def check_startup_recovery(self) -> None:
        """앱 시작 시 1시간 이내 백업이 있으면 복구 제안."""
        win = self._win
        backup_dir = self.get_backup_dir()
        if not os.path.exists(backup_dir):
            return

        backups = sorted(
            [
                f for f in os.listdir(backup_dir)
                if f.startswith("autosave_") and f.endswith(".json")
            ],
            reverse=True,
        )
        if not backups:
            return

        latest = backups[0]
        latest_path = os.path.join(backup_dir, latest)

        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(latest_path))
            if datetime.now() - mtime > timedelta(hours=1):
                return  # 1시간 초과 → 무시
        except OSError:
            return

        time_str = mtime.strftime("%Y-%m-%d %H:%M")
        reply = QMessageBox.question(
            win,
            tr("dialog.recovery_title"),
            tr("dialog.recovery_message", time=time_str),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            win.file_io.load(latest_path)
            win.current_file_path = None  # 백업이므로 파일 경로 초기화
            win._update_title()
            win._flash_status(tr("status.recovered_from_backup"))
