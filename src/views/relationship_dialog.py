"""관계 추가/선택 다이얼로그."""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
)
from PyQt6.QtCore import Qt

from ..models.family_tree import FamilyTree
from ..models.person import Person
from ..i18n.translator import tr


class SelectPersonDialog(QDialog):
    """기존 사람 선택 다이얼로그."""

    def __init__(self, family_tree: FamilyTree, title: str, parent=None):
        super().__init__(parent)
        self.family_tree = family_tree
        self.selected_person_id: Optional[str] = None

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 500)

        self._init_ui()

    def _init_ui(self):
        """UI 초기화."""
        layout = QVBoxLayout(self)

        # 검색창
        search_label = QLabel(tr("panel.search_placeholder"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("panel.search_placeholder"))
        self.search_input.textChanged.connect(self._filter_persons)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)

        # 사람 목록
        self.person_list = QListWidget()
        self.person_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.person_list)

        # 버튼
        button_layout = QHBoxLayout()
        self.select_button = QPushButton(tr("button.select"))
        self.select_button.clicked.connect(self.accept)
        self.select_button.setEnabled(False)

        cancel_button = QPushButton(tr("button.cancel"))
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 사람 목록 채우기
        self._populate_list()

        # 선택 이벤트
        self.person_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _populate_list(self, filter_text: str = ""):
        """사람 목록 채우기."""
        self.person_list.clear()

        persons = self.family_tree.get_all_persons()
        # 이름순 정렬
        persons.sort(key=lambda p: p.name.lower())

        for person in persons:
            # 필터 적용
            if filter_text and filter_text.lower() not in person.name.lower():
                continue

            # 표시 텍스트 생성
            display_text = person.name
            if person.birth_year:
                display_text += f" ({person.lifespan_str})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, person.id)
            self.person_list.addItem(item)

    def _filter_persons(self, text: str):
        """검색어로 사람 필터링."""
        self._populate_list(text)

    def _on_selection_changed(self):
        """선택 변경 시."""
        items = self.person_list.selectedItems()
        if items:
            self.selected_person_id = items[0].data(Qt.ItemDataRole.UserRole)
            self.select_button.setEnabled(True)
        else:
            self.selected_person_id = None
            self.select_button.setEnabled(False)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """항목 더블클릭 시."""
        self.selected_person_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def get_selected_person_id(self) -> Optional[str]:
        """선택된 사람 ID 반환."""
        return self.selected_person_id
