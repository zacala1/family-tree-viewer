"""후손/조상 계보 보고서 다이얼로그."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from ..i18n import tr

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

    def _build_descendants(self, tree, person_id, depth, lines, visited):
        """후손 트리 구축 (재귀, 순환 방지)."""
        if person_id in visited:
            return
        visited.add(person_id)

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
        """조상 트리 구축 (재귀, 순환 방지)."""
        if person_id in visited:
            return
        visited.add(person_id)

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
