"""파일 I/O 컨트롤러 — MainWindow의 새로 만들기/열기/저장/가져오기/내보내기 흐름.

UI 다이얼로그 + 백그라운드 task + 사용자 피드백을 한 곳에서 조율한다.
MainWindow는 얇은 메뉴/툴바 wiring만 남기고 실제 흐름은 이 컨트롤러로 위임.

코어 책임:
- 파일 확장자 보정 (json/xlsx/ged)
- 동시 저장 방지 플래그 (`is_saving`)
- 실패 시 사용자 친화적 에러 메시지 표시
- 가져오기 병합/대체 사용자 선택 다이얼로그
- PDF 내보내기 가능 여부 확인

MainWindow는 다음 메서드/속성을 노출해야 한다:
- `family_tree`, `current_file_path` (set/get)
- `undo_manager`, `tree_canvas`, `detail_panel`, `status_label`
- `_check_save()`, `_run_with_progress(title, msg, fn)`
- `_rebuild_service_for_tree(tree)`, `_update_person_list()`,
  `_update_title()`, `_add_to_recent_files(path)`
"""
from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from ..models.family_tree import FamilyTree
from ..utils.file_handler import FileHandler
from ..i18n import tr


class FileIOController:
    """파일 I/O 흐름 조율자."""

    def __init__(self, main_window):
        self._win = main_window
        # 자동 백업과 사용자 수동 저장이 동시에 쓰지 않도록 가드
        self.is_saving: bool = False

    # === 공개 API ===

    def new_tree(self) -> None:
        """새 트리로 초기화."""
        win = self._win
        if not win._check_save():
            return

        win.family_tree = FamilyTree()
        win._rebuild_service_for_tree(win.family_tree)
        win.current_file_path = None
        win.undo_manager.clear()
        win._update_undo_redo_state()
        win.tree_canvas.set_family_tree(win.family_tree)
        win.detail_panel.clear()
        win._update_person_list()
        win._update_title()
        win.status_label.setText(tr("status.new_created"))

    def open(self) -> None:
        """파일 열기 대화상자 → 로드."""
        win = self._win
        if not win._check_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            win, tr("dialog.open_title"), "", FileHandler.get_open_filters()
        )
        if file_path:
            self.load(file_path)

    def save(self) -> None:
        """저장 — 경로가 있으면 덮어쓰기, 없으면 Save As."""
        win = self._win
        if win.current_file_path:
            self._do_save(win.current_file_path)
        else:
            self.save_as()

    def save_as(self) -> None:
        """다른 이름으로 저장."""
        win = self._win
        file_path, selected_filter = QFileDialog.getSaveFileName(
            win, tr("dialog.save_title"), "", FileHandler.get_save_filters()
        )
        if file_path:
            file_path = self._ensure_file_extension(file_path, selected_filter)
            self._do_save(file_path)

    def import_file(self) -> None:
        """가져오기 — 기존 데이터에 병합 또는 대체."""
        win = self._win
        file_path, _ = QFileDialog.getOpenFileName(
            win, tr("dialog.import_title"), "", FileHandler.get_open_filters()
        )
        if not file_path:
            return

        tree = win._run_with_progress(
            tr("dialog.import_title"),
            tr("status.importing"),
            lambda: FileHandler.load_file(file_path),
        )
        if not tree:
            return

        # 기존 데이터가 비어 있으면 단순 대체
        if not win.family_tree.get_all_persons():
            win.family_tree = tree
        else:
            if not self._prompt_import_merge(tree):
                return

        win.tree_canvas.set_family_tree(win.family_tree)
        win._update_person_list()
        win._update_title()
        win.status_label.setText(tr("status.import_complete", path=file_path))

    def export(self) -> None:
        """파일로 내보내기."""
        win = self._win
        file_path, selected_filter = QFileDialog.getSaveFileName(
            win, tr("dialog.export_title"), "", FileHandler.get_save_filters()
        )
        if not file_path:
            return

        file_path = self._ensure_file_extension(file_path, selected_filter)
        result = win._run_with_progress(
            tr("dialog.export_title"),
            tr("status.exporting"),
            lambda: FileHandler.save_file(win.family_tree, file_path),
        )
        if result:
            win.status_label.setText(tr("status.export_complete", path=file_path))
        else:
            detail = FileHandler.get_last_error()
            msg = tr("error.export_failed")
            if detail:
                msg += f"\n\n{detail}"
            QMessageBox.warning(win, tr("error.export_failed"), msg)

    def export_pdf(self) -> None:
        """PDF로 내보내기 — ReportLab 미설치 시 안내."""
        win = self._win
        from ..utils.pdf_exporter import PdfExporter

        if not PdfExporter.is_available():
            QMessageBox.warning(
                win, tr("error.pdf_not_available"), tr("error.pdf_not_available")
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            win, tr("dialog.export_pdf_title"), "", "PDF (*.pdf)"
        )
        if not file_path:
            return

        if not file_path.endswith(".pdf"):
            file_path += ".pdf"

        result = win._run_with_progress(
            tr("dialog.export_pdf_title"),
            tr("status.exporting"),
            lambda: PdfExporter.export(win.tree_canvas, file_path),
        )
        if result:
            win.status_label.setText(tr("status.pdf_exported", path=file_path))
        else:
            QMessageBox.warning(
                win, tr("error.pdf_export_failed"), tr("error.pdf_export_failed")
            )

    def load(self, file_path: str) -> bool:
        """주어진 경로의 파일을 로드하고 UI를 갱신.

        드래그앤드롭·백업 복구·대화상자 공통 진입점.
        성공 시 True, 실패 시 사용자에게 경고 표시 후 False.
        """
        win = self._win
        tree = win._run_with_progress(
            tr("dialog.open_title"),
            tr("status.loading_file"),
            lambda: FileHandler.load_file(file_path),
        )
        if tree:
            win.family_tree = tree
            win.current_file_path = file_path
            win._rebuild_service_for_tree(win.family_tree)
            win.undo_manager.clear()
            win._update_undo_redo_state()
            win.tree_canvas.set_family_tree(win.family_tree)
            win.detail_panel.clear()
            win._update_person_list()
            win._update_title()
            win._add_to_recent_files(file_path)
            win.status_label.setText(tr("status.file_opened", path=file_path))
            return True

        detail = FileHandler.get_last_error()
        msg = tr("error.file_open_failed")
        if detail:
            msg += f"\n\n{detail}"
        QMessageBox.warning(win, tr("error.file_open_failed"), msg)
        return False

    # === 내부 ===

    @staticmethod
    def _ensure_file_extension(file_path: str, selected_filter: str) -> str:
        """파일 경로에 적절한 확장자가 있는지 확인 후 추가."""
        if not file_path.endswith((".json", ".xlsx", ".ged")):
            if "Excel" in selected_filter:
                file_path += ".xlsx"
            elif "GEDCOM" in selected_filter:
                file_path += ".ged"
            else:
                file_path += ".json"
        return file_path

    def _do_save(self, file_path: str) -> None:
        """실제 저장 — is_saving 플래그로 자동 백업과 충돌 방지."""
        win = self._win
        self.is_saving = True
        try:
            success = win._run_with_progress(
                tr("dialog.save_title"),
                tr("status.saving_file"),
                lambda: FileHandler.save_file(win.family_tree, file_path),
            )
            if success:
                win.current_file_path = file_path
                win.family_tree.mark_saved()
                win._update_title()
                win._add_to_recent_files(file_path)
                win.status_label.setText(tr("status.saved", path=file_path))
            else:
                detail = FileHandler.get_last_error()
                msg = tr("error.save_failed")
                if detail:
                    msg += f"\n\n{detail}"
                QMessageBox.warning(win, tr("error.save_failed"), msg)
        finally:
            self.is_saving = False

    def _prompt_import_merge(self, tree: FamilyTree) -> bool:
        """가져온 트리를 현재와 어떻게 합칠지 사용자에게 묻고 적용.

        Yes → 병합 (검증 후 추가), No → 대체, Cancel → 취소.
        진행하면 True, 취소(또는 검증 실패)면 False 반환.
        """
        win = self._win
        buttons = (
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel
        )
        reply = QMessageBox.question(
            win,
            tr("dialog.import_merge_title"),
            tr("dialog.import_merge_message"),
            buttons,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return False

        if reply == QMessageBox.StandardButton.No:
            win.family_tree = tree
            return True

        # 병합 — 사이즈 검증 먼저
        current_count = len(win.family_tree.get_all_persons())
        import_count = len(tree.get_all_persons())
        if current_count + import_count > win.family_tree.MAX_PERSONS:
            QMessageBox.warning(
                win,
                tr("dialog.import_merge_title"),
                tr("error.file_too_large", max_size=win.family_tree.MAX_PERSONS),
                QMessageBox.StandardButton.Ok,
            )
            return False

        try:
            for person in tree.get_all_persons():
                win.family_tree.add_person(person)
            for relationship in tree.get_all_relationships():
                win.family_tree.add_relationship(relationship)
        except ValueError as e:
            QMessageBox.critical(
                win,
                tr("dialog.import_merge_title"),
                tr("dialog.relationship_error_message", error=str(e)),
                QMessageBox.StandardButton.Ok,
            )
            return False

        return True
