"""관계 탭 위젯.

detail_panel에서 분리. 부모/배우자/자녀/확대관계 표시 + 배우자별 결혼·이혼일
입력 + "Set parent / Add spouse / Add child" 액션. 호스트(detail_panel)는
add_relationship_requested signal을 main_window로 forward.
"""
from __future__ import annotations

import html as _html
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...models.family_tree import FamilyTree
from ...models.person import Person
from ...models.relationship import RelationshipRequestType
from ...i18n import tr
from .date_input_group import create_date_input_widget


def _sanitize(text: str, limit: int = 1000) -> str:
    if not text:
        return ""
    return _html.escape(str(text))[:limit]


class RelationshipsTab(QWidget):
    """관계 탭 — 부모/배우자/자녀/확대관계 표시 + 배우자 date 편집.

    Signals:
        add_relationship_requested(str): rel_type ("parent"/"spouse"/"child")
            사용자 액션 — host는 main_window로 forward.
    """

    add_relationship_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._person: Optional[Person] = None
        self._family_tree: Optional[FamilyTree] = None
        self._is_editing: bool = False
        # 배우자 위젯 참조 (spouse_id → dict with marriage/divorce groups)
        self._spouse_widgets: Dict = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 12, 8, 8)

        # 부모
        self.parents_group = QGroupBox(tr("label.parents"))
        parents_layout = QVBoxLayout(self.parents_group)
        self.father_title_label = QLabel(tr("label.father") + ":")
        self.father_label = QLabel(tr("label.none"))
        parents_layout.addWidget(self.father_title_label)
        parents_layout.addWidget(self.father_label)
        self.mother_title_label = QLabel(tr("label.mother") + ":")
        self.mother_label = QLabel(tr("label.none"))
        parents_layout.addWidget(self.mother_title_label)
        parents_layout.addWidget(self.mother_label)

        self.set_parent_btn = QPushButton(tr("button.set_parent"))
        self.set_parent_btn.clicked.connect(
            lambda: self.add_relationship_requested.emit(RelationshipRequestType.PARENT)
        )
        parents_layout.addWidget(self.set_parent_btn)
        outer.addWidget(self.parents_group)

        # 배우자
        self.spouse_group = QGroupBox(tr("label.spouse"))
        self.spouse_group_layout = QVBoxLayout(self.spouse_group)
        self.spouse_list_widget = QWidget()
        self.spouse_list_layout = QVBoxLayout(self.spouse_list_widget)
        self.spouse_list_layout.setContentsMargins(0, 0, 0, 0)
        self.spouse_group_layout.addWidget(self.spouse_list_widget)

        self.add_spouse_btn = QPushButton(tr("button.add_spouse"))
        self.add_spouse_btn.clicked.connect(
            lambda: self.add_relationship_requested.emit(RelationshipRequestType.SPOUSE)
        )
        self.spouse_group_layout.addWidget(self.add_spouse_btn)
        outer.addWidget(self.spouse_group)

        # 자녀
        self.children_group = QGroupBox(tr("label.children"))
        children_layout = QVBoxLayout(self.children_group)
        self.children_label = QLabel(tr("label.none"))
        children_layout.addWidget(self.children_label)

        self.add_child_btn = QPushButton(tr("button.add_child"))
        self.add_child_btn.clicked.connect(
            lambda: self.add_relationship_requested.emit(RelationshipRequestType.CHILD)
        )
        children_layout.addWidget(self.add_child_btn)
        outer.addWidget(self.children_group)

        # 확대 관계
        self.extended_group = QGroupBox(tr("label.extended_relations"))
        extended_layout = QVBoxLayout(self.extended_group)
        self.grandparents_title = QLabel(tr("label.grandparents") + ":")
        self.grandparents_label = QLabel(tr("label.none"))
        self.grandchildren_title = QLabel(tr("label.grandchildren") + ":")
        self.grandchildren_label = QLabel(tr("label.none"))
        self.uncles_aunts_title = QLabel(tr("label.uncles_aunts") + ":")
        self.uncles_aunts_label = QLabel(tr("label.none"))
        self.cousins_title = QLabel(tr("label.cousins") + ":")
        self.cousins_label = QLabel(tr("label.none"))
        self.in_laws_title = QLabel(tr("label.in_laws") + ":")
        self.in_laws_label = QLabel(tr("label.none"))
        for title, label in [
            (self.grandparents_title, self.grandparents_label),
            (self.grandchildren_title, self.grandchildren_label),
            (self.uncles_aunts_title, self.uncles_aunts_label),
            (self.cousins_title, self.cousins_label),
            (self.in_laws_title, self.in_laws_label),
        ]:
            row = QHBoxLayout()
            row.addWidget(title)
            row.addWidget(label, 1)
            extended_layout.addLayout(row)
        outer.addWidget(self.extended_group)
        outer.addStretch()

    # === Public API ===

    def set_context(self, person: Optional[Person], family_tree: Optional[FamilyTree]):
        """표시할 person + family_tree 설정 + 즉시 refresh."""
        self._person = person
        self._family_tree = family_tree
        self.refresh()

    def set_editing(self, is_editing: bool):
        """edit mode 토글 — 결혼/이혼 date input을 read_only로 전환."""
        self._is_editing = is_editing
        for sid, widgets in self._spouse_widgets.items():
            if sid == "_none":
                continue
            mg = widgets.get("marriage_group")
            dg = widgets.get("divorce_group")
            if mg:
                mg.set_read_only(not is_editing)
            if dg:
                dg.set_read_only(not is_editing)

    def refresh(self):
        """현재 person·family_tree로 모든 관계 라벨 다시 렌더."""
        none_text = tr("label.none")
        self._clear_spouse_widgets()

        if not self._person or not self._family_tree:
            self.father_label.setText(none_text)
            self.mother_label.setText(none_text)
            self.children_label.setText(none_text)
            self.grandparents_label.setText(none_text)
            self.grandchildren_label.setText(none_text)
            self.uncles_aunts_label.setText(none_text)
            self.cousins_label.setText(none_text)
            self.in_laws_label.setText(none_text)
            return

        # 부모
        father = (
            self._family_tree.get_person(self._person.father_id)
            if self._person.father_id else None
        )
        mother = (
            self._family_tree.get_person(self._person.mother_id)
            if self._person.mother_id else None
        )
        self.father_label.setText(father.name if father else none_text)
        self.mother_label.setText(mother.name if mother else none_text)

        # 배우자
        spouses = self._family_tree.get_spouses(self._person.id)
        current = self._family_tree.get_current_spouse(self._person.id)
        if spouses:
            for spouse in spouses:
                self._create_spouse_widget(spouse, spouse == current)
        else:
            label = QLabel(none_text)
            self.spouse_list_layout.addWidget(label)
            self._spouse_widgets["_none"] = {"label": label}

        # 자녀
        children = self._family_tree.get_children(self._person.id)
        self.children_label.setText(
            ", ".join(c.name for c in children) if children else none_text
        )

        # 확대 관계
        pid = self._person.id
        for persons, lbl in [
            (self._family_tree.get_grandparents(pid), self.grandparents_label),
            (self._family_tree.get_grandchildren(pid), self.grandchildren_label),
            (self._family_tree.get_uncles_aunts(pid), self.uncles_aunts_label),
            (self._family_tree.get_cousins(pid), self.cousins_label),
            (self._family_tree.get_in_laws(pid), self.in_laws_label),
        ]:
            lbl.setText(", ".join(p.name for p in persons) if persons else none_text)

    def save_spouse_dates(self) -> List[str]:
        """배우자 dialog의 marriage/divorce 입력값을 Relationship에 저장.

        Returns:
            결혼일이 이혼일보다 늦은 배우자들의 이름 list (host가 경고 표시용).
            모두 정상이면 빈 list.
        """
        if not self._family_tree:
            return []
        invalid_names: List[str] = []
        for spouse_id, widgets in self._spouse_widgets.items():
            if spouse_id == "_none":
                continue
            rel = widgets.get("relationship")
            if not rel:
                continue
            mg = widgets.get("marriage_group")
            dg = widgets.get("divorce_group")
            if mg:
                year, month, day, is_lunar = mg.get_values()
                rel.marriage_year = year
                rel.marriage_month = month
                rel.marriage_day = day
                rel.is_lunar_marriage = is_lunar
            if dg:
                year, month, day, _ = dg.get_values()
                rel.divorce_year = year
                rel.divorce_month = month
                rel.divorce_day = day
            if not rel.is_valid_marriage_order():
                spouse = self._family_tree.get_person(spouse_id)
                if spouse:
                    invalid_names.append(spouse.name or tr("label.no_name"))
        self._family_tree.mark_modified()
        return invalid_names

    def update_ui_texts(self):
        """언어 변경 시 모든 라벨·버튼·그룹 제목 재번역 + refresh."""
        self.parents_group.setTitle(tr("label.parents"))
        self.father_title_label.setText(tr("label.father") + ":")
        self.mother_title_label.setText(tr("label.mother") + ":")
        self.spouse_group.setTitle(tr("label.spouse"))
        self.children_group.setTitle(tr("label.children"))
        self.extended_group.setTitle(tr("label.extended_relations"))
        self.grandparents_title.setText(tr("label.grandparents") + ":")
        self.grandchildren_title.setText(tr("label.grandchildren") + ":")
        self.uncles_aunts_title.setText(tr("label.uncles_aunts") + ":")
        self.cousins_title.setText(tr("label.cousins") + ":")
        self.in_laws_title.setText(tr("label.in_laws") + ":")
        self.set_parent_btn.setText(tr("button.set_parent"))
        self.add_spouse_btn.setText(tr("button.add_spouse"))
        self.add_child_btn.setText(tr("button.add_child"))
        # 배우자 위젯 안의 date label도 갱신 — 통째 refresh가 가장 안전
        self.refresh()

    # === Internal ===

    def _clear_spouse_widgets(self):
        while self.spouse_list_layout.count():
            item = self.spouse_list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._spouse_widgets.clear()

    def _create_spouse_widget(self, spouse: Person, is_current: bool):
        rel = self._family_tree.get_spouse_relationship(self._person.id, spouse.id)

        container = QFrame()
        container.setObjectName("spouseItem")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 이름 + 상태
        name_row = QHBoxLayout()
        name_label = QLabel(f"<b>{_sanitize(spouse.name)}</b>")
        if is_current:
            status_label = QLabel(
                f"<span style='color: green;'>● {_sanitize(tr('label.current_spouse'))}</span>"
            )
        elif rel and rel.is_divorced:
            status_label = QLabel(
                f"<span style='color: gray;'>{_sanitize(tr('label.divorced'))}</span>"
            )
        else:
            status_label = QLabel("")
        name_row.addWidget(name_label)
        name_row.addWidget(status_label)
        name_row.addStretch()
        layout.addLayout(name_row)

        # 결혼일
        marriage_row = QHBoxLayout()
        marriage_title = QLabel(tr("label.marriage_date") + ":")
        marriage_row.addWidget(marriage_title)
        marriage_widget, marriage_group = create_date_input_widget()
        if rel:
            marriage_group.set_values(
                rel.marriage_year, rel.marriage_month,
                rel.marriage_day, rel.is_lunar_marriage,
            )
        marriage_group.set_read_only(not self._is_editing)
        marriage_row.addWidget(marriage_widget)
        layout.addLayout(marriage_row)

        # 이혼일
        divorce_row = QHBoxLayout()
        divorce_title = QLabel(tr("label.divorce_date") + ":")
        divorce_row.addWidget(divorce_title)
        divorce_widget, divorce_group = create_date_input_widget()
        if rel:
            divorce_group.set_values(
                rel.divorce_year, rel.divorce_month, rel.divorce_day, False
            )
        divorce_group.is_lunar.hide()  # 이혼일은 음력 불필요
        divorce_group.set_read_only(not self._is_editing)
        divorce_row.addWidget(divorce_widget)
        layout.addLayout(divorce_row)

        self.spouse_list_layout.addWidget(container)
        self._spouse_widgets[spouse.id] = {
            "container": container,
            "name_label": name_label,
            "status_label": status_label,
            "marriage_title": marriage_title,
            "marriage_group": marriage_group,
            "divorce_title": divorce_title,
            "divorce_group": divorce_group,
            "relationship": rel,
        }
