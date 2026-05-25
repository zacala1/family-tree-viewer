"""후손/조상 계보 보고서 다이얼로그."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from ..i18n import tr
from ..config import MAX_REPORT_DEPTH

from typing import TYPE_CHECKING, Set
if TYPE_CHECKING:
    from ..models.family_tree import FamilyTree


class LineageReportDialog(QDialog):
    """후손 또는 조상 보고서 다이얼로그."""

    def __init__(self, family_tree: "FamilyTree", person_id: str,
                 mode: str = "descendants", parent=None):
        super().__init__(parent)

        person = family_tree.get_person(person_id)
        self._valid = person is not None
        if not person:
            self.setWindowTitle(tr("error.person_not_found", fallback="Error"))
            layout = QVBoxLayout(self)
            layout.addWidget(QTextEdit(tr("error.person_not_found", fallback="Person not found")))
            close_btn = QPushButton(tr("button.close", fallback="Close"))
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)
            return

        if mode == "descendants":
            self.setWindowTitle(tr("report.descendants_title", name=person.name))
        else:
            self.setWindowTitle(tr("report.ancestors_title", name=person.name))

        self.setMinimumSize(400, 500)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(tr("button.close", fallback="Close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # 보고서 생성
        visited: Set[str] = set()
        lines = []

        if mode == "descendants":
            self._build_descendants(family_tree, person_id, 0, lines, visited)
        else:
            self._build_ancestors(family_tree, person_id, 0, lines, visited)

        self.text_edit.setPlainText("\n".join(lines) if lines else tr("message.no_events"))

    def showEvent(self, event):
        """Dialog 표시 시 부드러운 fade-in."""
        super().showEvent(event)
        from ..utils.animation import fade_in_widget
        fade_in_widget(self)

    def _build_descendants(self, tree, person_id, depth, lines, visited):
        """후손 트리 구축 (재귀, 순환 + 깊이 제한 방지).

        깊이 한계: MAX_REPORT_DEPTH. 매우 깊은 선형 계보에서 Python의
        재귀 한계(~1000)에 닿기 전에 안전하게 차단.

        visited.add는 깊이 검사보다 먼저 실행 — 같은 인물이 여러 경로로
        도달하는 경우에도 truncate 메시지가 한 번만 출력되도록 보장.
        """
        if person_id in visited:
            return
        visited.add(person_id)
        if depth >= MAX_REPORT_DEPTH:
            indent = "  " * depth
            lines.append(f"{indent}{tr('report.truncated_too_deep')}")
            return

        person = tree.get_person(person_id)
        if not person:
            return

        indent = "  " * depth
        lifespan = person.lifespan_str
        name_str = person.name or tr("label.no_name")
        if lifespan:
            lines.append(f"{indent}├─ {name_str} ({lifespan})")
        else:
            lines.append(f"{indent}├─ {name_str}")

        for child in tree.get_children(person_id):
            self._build_descendants(tree, child.id, depth + 1, lines, visited)

    def _build_ancestors(self, tree, person_id, depth, lines, visited):
        """조상 트리 구축 (재귀, 순환 + 깊이 제한 방지).

        descendants와 동일하게 visited.add를 깊이 검사 전에 호출.
        """
        if person_id in visited:
            return
        visited.add(person_id)
        if depth >= MAX_REPORT_DEPTH:
            indent = "  " * depth
            lines.append(f"{indent}{tr('report.truncated_too_deep')}")
            return

        person = tree.get_person(person_id)
        if not person:
            return

        indent = "  " * depth
        lifespan = person.lifespan_str
        name_str = person.name or tr("label.no_name")
        if lifespan:
            lines.append(f"{indent}├─ {name_str} ({lifespan})")
        else:
            lines.append(f"{indent}├─ {name_str}")

        for parent in tree.get_parents(person_id):
            self._build_ancestors(tree, parent.id, depth + 1, lines, visited)
