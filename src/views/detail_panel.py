"""상세 정보 패널."""

from typing import Optional
import re
import html
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QSpinBox,
    QPushButton,
    QFrame,
    QScrollArea,
    QGroupBox,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models.person import Person
from ..models.family_tree import FamilyTree
from ..i18n import tr
from ..config import (
    YEAR_MIN,
    YEAR_MAX,
    MONTH_MIN,
    MONTH_MAX,
    DAY_MIN,
    DAY_MAX,
    MAX_NAME_LENGTH,
    MAX_TEXT_LENGTH,
    MAX_EMAIL_LENGTH,
    MAX_PHONE_LENGTH,
    MAX_NOTES_LENGTH,
    HTML_SANITIZE_MAX_LENGTH,
)


def sanitize_html(text: str, max_length: int = HTML_SANITIZE_MAX_LENGTH) -> str:
    """HTML 표시용 텍스트 정제 (XSS 방지).

    Args:
        text: 정제할 텍스트
        max_length: 최대 길이

    Returns:
        정제된 안전한 텍스트
    """
    if not text:
        return ""
    # HTML 이스케이프 및 길이 제한
    cleaned = html.escape(str(text))
    return cleaned[:max_length]


class DateInputGroup:
    """날짜 입력 필드 그룹을 관리하는 헬퍼 클래스."""

    def __init__(
        self,
        year: QSpinBox,
        month: QSpinBox,
        day: QSpinBox,
        is_lunar: QCheckBox,
        year_label: QLabel,
        month_label: QLabel,
        day_label: QLabel,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.is_lunar = is_lunar
        self.year_label = year_label
        self.month_label = month_label
        self.day_label = day_label

    def set_values(
        self,
        year_val: Optional[int],
        month_val: Optional[int],
        day_val: Optional[int],
        is_lunar_val: bool,
    ):
        """날짜 값 설정."""
        self.year.setValue(year_val or YEAR_MIN)
        self.month.setValue(month_val or MONTH_MIN)
        self.day.setValue(day_val or DAY_MIN)
        self.is_lunar.setChecked(is_lunar_val)

    def get_values(self) -> tuple:
        """날짜 값 반환 (year, month, day, is_lunar)."""
        year = self.year.value() if self.year.value() > YEAR_MIN else None
        month = self.month.value() if self.month.value() > MONTH_MIN else None
        day = self.day.value() if self.day.value() > DAY_MIN else None
        return year, month, day, self.is_lunar.isChecked()

    def clear(self):
        """입력 필드 초기화."""
        self.year.setValue(YEAR_MIN)
        self.month.setValue(MONTH_MIN)
        self.day.setValue(DAY_MIN)
        self.is_lunar.setChecked(False)

    def set_read_only(self, read_only: bool):
        """읽기 전용 모드 설정."""
        self.year.setReadOnly(read_only)
        self.month.setReadOnly(read_only)
        self.day.setReadOnly(read_only)
        self.is_lunar.setEnabled(not read_only)

    def update_labels(self):
        """레이블 텍스트 업데이트."""
        self.year_label.setText(tr("label.year"))
        self.month_label.setText(tr("label.month"))
        self.day_label.setText(tr("label.day"))
        self.is_lunar.setText(tr("label.lunar"))


class DetailPanel(QFrame):
    """사람의 상세 정보를 표시하고 편집하는 패널."""

    person_updated = pyqtSignal(Person)
    add_relationship_requested = pyqtSignal(str, str)  # person_id, rel_type

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_person: Optional[Person] = None
        self.family_tree: Optional[FamilyTree] = None
        self._is_editing = False

        self._setup_ui()

    def _create_date_input_widget(self) -> tuple:
        """날짜 입력 위젯 생성. (widget, DateInputGroup) 튜플 반환."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        year = QSpinBox()
        year.setRange(YEAR_MIN, YEAR_MAX)
        year.setSpecialValueText("-")
        year.setValue(YEAR_MIN)
        layout.addWidget(year)
        year_label = QLabel(tr("label.year"))
        layout.addWidget(year_label)

        month = QSpinBox()
        month.setRange(MONTH_MIN, MONTH_MAX)
        month.setSpecialValueText("-")
        layout.addWidget(month)
        month_label = QLabel(tr("label.month"))
        layout.addWidget(month_label)

        day = QSpinBox()
        day.setRange(DAY_MIN, DAY_MAX)
        day.setSpecialValueText("-")
        layout.addWidget(day)
        day_label = QLabel(tr("label.day"))
        layout.addWidget(day_label)

        is_lunar = QCheckBox(tr("label.lunar"))
        layout.addWidget(is_lunar)

        group = DateInputGroup(year, month, day, is_lunar, year_label, month_label, day_label)
        return widget, group

    def _setup_ui(self):
        """UI 구성."""
        self.setObjectName("detailPanel")
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더
        header = QFrame()
        header.setObjectName("detailHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.header_label = QLabel(tr("panel.detail_info"))
        self.header_label.setObjectName("sectionHeader")
        header_layout.addWidget(self.header_label)

        header_layout.addStretch()

        self.edit_btn = QPushButton(tr("button.edit"))
        self.edit_btn.setObjectName("editBtn")
        self.edit_btn.clicked.connect(self._toggle_edit)
        header_layout.addWidget(self.edit_btn)

        layout.addWidget(header)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setObjectName("detailScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(12, 8, 12, 12)
        self.content_layout.setSpacing(12)

        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.setObjectName("detailTabs")

        # === 기본 정보 탭 ===
        self.basic_tab = QWidget()
        self.basic_layout = QFormLayout(self.basic_tab)
        self.basic_layout.setContentsMargins(8, 12, 8, 8)
        self.basic_layout.setSpacing(8)

        # 이름
        self.name_input = QLineEdit()
        self.name_input.setObjectName("detailInput")
        self.name_input.setMaxLength(MAX_NAME_LENGTH)
        self.name_label = QLabel(tr("label.name") + ":")
        self.basic_layout.addRow(self.name_label, self.name_input)

        # 성별
        self.gender_combo = QComboBox()
        self.gender_combo.setObjectName("detailCombo")
        self.gender_combo.addItem(tr("label.male"), "M")
        self.gender_combo.addItem(tr("label.female"), "F")
        self.gender_label = QLabel(tr("label.gender") + ":")
        self.basic_layout.addRow(self.gender_label, self.gender_combo)

        # 생년월일
        birth_widget, self.birth_date_group = self._create_date_input_widget()
        self.birth_date_label = QLabel(tr("label.birth_date") + ":")
        self.basic_layout.addRow(self.birth_date_label, birth_widget)

        # 사망일
        death_widget, self.death_date_group = self._create_date_input_widget()
        self.death_date_label = QLabel(tr("label.death_date") + ":")
        self.basic_layout.addRow(self.death_date_label, death_widget)

        self.tabs.addTab(self.basic_tab, tr("tab.basic_info"))

        # === 추가 정보 탭 ===
        self.extra_tab = QWidget()
        self.extra_layout = QFormLayout(self.extra_tab)
        self.extra_layout.setContentsMargins(8, 12, 8, 8)
        self.extra_layout.setSpacing(8)

        self.birth_place_input = QLineEdit()
        self.birth_place_input.setMaxLength(MAX_TEXT_LENGTH)
        self.birth_place_label = QLabel(tr("label.birth_place") + ":")
        self.extra_layout.addRow(self.birth_place_label, self.birth_place_input)

        self.current_address_input = QLineEdit()
        self.current_address_input.setMaxLength(MAX_TEXT_LENGTH)
        self.current_address_label = QLabel(tr("label.current_address") + ":")
        self.extra_layout.addRow(self.current_address_label, self.current_address_input)

        self.occupation_input = QLineEdit()
        self.occupation_input.setMaxLength(MAX_TEXT_LENGTH)
        self.occupation_label = QLabel(tr("label.occupation") + ":")
        self.extra_layout.addRow(self.occupation_label, self.occupation_input)

        self.education_input = QLineEdit()
        self.education_input.setMaxLength(MAX_TEXT_LENGTH)
        self.education_label = QLabel(tr("label.education") + ":")
        self.extra_layout.addRow(self.education_label, self.education_input)

        self.phone_input = QLineEdit()
        self.phone_input.setMaxLength(MAX_PHONE_LENGTH)
        self.phone_label = QLabel(tr("label.phone") + ":")
        self.extra_layout.addRow(self.phone_label, self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setMaxLength(MAX_EMAIL_LENGTH)
        self.email_label = QLabel(tr("label.email") + ":")
        self.extra_layout.addRow(self.email_label, self.email_input)

        self.tabs.addTab(self.extra_tab, tr("tab.extra_info"))

        # === 메모 탭 ===
        self.memo_tab = QWidget()
        memo_layout = QVBoxLayout(self.memo_tab)
        memo_layout.setContentsMargins(8, 12, 8, 8)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(tr("label.notes_placeholder"))
        self.notes_input.textChanged.connect(self._limit_notes_length)
        memo_layout.addWidget(self.notes_input)

        self.tabs.addTab(self.memo_tab, tr("tab.memo"))

        # === 관계 탭 ===
        self.rel_tab = QWidget()
        rel_layout = QVBoxLayout(self.rel_tab)
        rel_layout.setContentsMargins(8, 12, 8, 8)

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
        self.set_parent_btn.clicked.connect(lambda: self._request_add_relationship("parent"))
        parents_layout.addWidget(self.set_parent_btn)

        rel_layout.addWidget(self.parents_group)

        # 배우자
        self.spouse_group = QGroupBox(tr("label.spouse"))
        self.spouse_group_layout = QVBoxLayout(self.spouse_group)

        # 배우자 목록 컨테이너 (동적 생성)
        self.spouse_list_widget = QWidget()
        self.spouse_list_layout = QVBoxLayout(self.spouse_list_widget)
        self.spouse_list_layout.setContentsMargins(0, 0, 0, 0)
        self.spouse_list_layout.setSpacing(8)
        self.spouse_group_layout.addWidget(self.spouse_list_widget)

        # 배우자 항목 위젯들을 저장 (spouse_id -> widgets dict)
        self._spouse_widgets: dict = {}

        self.add_spouse_btn = QPushButton(tr("button.add_spouse"))
        self.add_spouse_btn.clicked.connect(lambda: self._request_add_relationship("spouse"))
        self.spouse_group_layout.addWidget(self.add_spouse_btn)

        rel_layout.addWidget(self.spouse_group)

        # 자녀
        self.children_group = QGroupBox(tr("label.children"))
        children_layout = QVBoxLayout(self.children_group)
        self.children_label = QLabel(tr("label.none"))
        children_layout.addWidget(self.children_label)

        self.add_child_btn = QPushButton(tr("button.add_child"))
        self.add_child_btn.clicked.connect(lambda: self._request_add_relationship("child"))
        children_layout.addWidget(self.add_child_btn)

        rel_layout.addWidget(self.children_group)
        rel_layout.addStretch()

        self.tabs.addTab(self.rel_tab, tr("tab.relationships"))

        self.content_layout.addWidget(self.tabs)

        # 저장/취소 버튼
        self.button_frame = QFrame()
        self.button_frame.setObjectName("buttonFrame")
        button_layout = QHBoxLayout(self.button_frame)
        button_layout.setContentsMargins(0, 8, 0, 0)

        button_layout.addStretch()

        self.cancel_btn = QPushButton(tr("button.cancel"))
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self._cancel_edit)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(tr("button.save"))
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self._save)
        button_layout.addWidget(self.save_btn)

        self.content_layout.addWidget(self.button_frame)
        self.button_frame.hide()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 초기 상태: 읽기 전용
        self._set_read_only(True)

    def update_ui_texts(self):
        """UI 텍스트 업데이트 (언어 변경 시)."""
        # 헤더
        self.header_label.setText(tr("panel.detail_info"))
        self.edit_btn.setText(tr("button.cancel") if self._is_editing else tr("button.edit"))

        # 탭 제목
        self.tabs.setTabText(0, tr("tab.basic_info"))
        self.tabs.setTabText(1, tr("tab.extra_info"))
        self.tabs.setTabText(2, tr("tab.memo"))
        self.tabs.setTabText(3, tr("tab.relationships"))

        # 기본 정보 탭
        self.name_label.setText(tr("label.name") + ":")
        self.gender_label.setText(tr("label.gender") + ":")
        self.gender_combo.setItemText(0, tr("label.male"))
        self.gender_combo.setItemText(1, tr("label.female"))
        self.birth_date_label.setText(tr("label.birth_date") + ":")
        self.death_date_label.setText(tr("label.death_date") + ":")
        self.birth_date_group.update_labels()
        self.death_date_group.update_labels()

        # 추가 정보 탭
        self.birth_place_label.setText(tr("label.birth_place") + ":")
        self.current_address_label.setText(tr("label.current_address") + ":")
        self.occupation_label.setText(tr("label.occupation") + ":")
        self.education_label.setText(tr("label.education") + ":")
        self.phone_label.setText(tr("label.phone") + ":")
        self.email_label.setText(tr("label.email") + ":")

        # 메모 탭
        self.notes_input.setPlaceholderText(tr("label.notes_placeholder"))

        # 관계 탭
        self.parents_group.setTitle(tr("label.parents"))
        self.father_title_label.setText(tr("label.father") + ":")
        self.mother_title_label.setText(tr("label.mother") + ":")
        self.spouse_group.setTitle(tr("label.spouse"))
        self.children_group.setTitle(tr("label.children"))
        self.set_parent_btn.setText(tr("button.set_parent"))
        self.add_spouse_btn.setText(tr("button.add_spouse"))
        self.add_child_btn.setText(tr("button.add_child"))

        # 버튼
        self.cancel_btn.setText(tr("button.cancel"))
        self.save_btn.setText(tr("button.save"))

        # 관계 정보 업데이트
        self._update_relationships()

    def set_person(self, person: Person, family_tree: FamilyTree):
        """표시할 Person 설정."""
        self.current_person = person
        self.family_tree = family_tree
        self._load_person_data()
        self._update_relationships()

    def clear(self):
        """패널 초기화."""
        self.current_person = None
        self.family_tree = None
        self._clear_inputs()

    def start_edit(self):
        """편집 모드 시작."""
        if not self._is_editing:
            self._toggle_edit()

    def _load_person_data(self):
        """Person 데이터를 UI에 로드."""
        if not self.current_person:
            self._clear_inputs()
            return

        p = self.current_person

        self.name_input.setText(p.name)
        self.gender_combo.setCurrentIndex(0 if p.gender == "M" else 1)

        # 생년월일
        self.birth_date_group.set_values(p.birth_year, p.birth_month, p.birth_day, p.is_lunar_birth)

        # 사망일
        self.death_date_group.set_values(p.death_year, p.death_month, p.death_day, p.is_lunar_death)

        # 추가 정보
        self.birth_place_input.setText(p.birth_place)
        self.current_address_input.setText(p.current_address)
        self.occupation_input.setText(p.occupation)
        self.education_input.setText(p.education)
        self.phone_input.setText(p.phone)
        self.email_input.setText(p.email)
        self.notes_input.setText(p.notes)

    def _update_relationships(self):
        """관계 정보 업데이트."""
        none_text = tr("label.none")

        # 기존 배우자 위젯 정리
        self._clear_spouse_widgets()

        if not self.current_person or not self.family_tree:
            self.father_label.setText(none_text)
            self.mother_label.setText(none_text)
            self.children_label.setText(none_text)
            return

        # 부모
        father = (
            self.family_tree.get_person(self.current_person.father_id)
            if self.current_person.father_id
            else None
        )
        mother = (
            self.family_tree.get_person(self.current_person.mother_id)
            if self.current_person.mother_id
            else None
        )

        self.father_label.setText(father.name if father else none_text)
        self.mother_label.setText(mother.name if mother else none_text)

        # 배우자 (개별 항목으로 표시)
        spouses = self.family_tree.get_spouses(self.current_person.id)
        current_spouse = self.family_tree.get_current_spouse(self.current_person.id)

        if spouses:
            for spouse in spouses:
                self._create_spouse_widget(spouse, spouse == current_spouse)
        else:
            no_spouse_label = QLabel(none_text)
            self.spouse_list_layout.addWidget(no_spouse_label)
            self._spouse_widgets["_none"] = {"label": no_spouse_label}

        # 자녀
        children = self.family_tree.get_children(self.current_person.id)
        if children:
            children_names = [c.name for c in children]
            self.children_label.setText(", ".join(children_names))
        else:
            self.children_label.setText(none_text)

    def _clear_spouse_widgets(self):
        """배우자 위젯들 정리."""
        # 레이아웃에서 모든 위젯 제거 (메모리 누수 방지)
        while self.spouse_list_layout.count():
            item = self.spouse_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # 추적 중인 위젯들도 정리
        for widgets in self._spouse_widgets.values():
            for widget in widgets.values():
                if widget is not None and not widget.isHidden():
                    widget.setParent(None)
                    widget.deleteLater()

        self._spouse_widgets.clear()

    def _create_spouse_widget(self, spouse: Person, is_current: bool):
        """배우자 항목 위젯 생성."""
        rel = self.family_tree.get_spouse_relationship(self.current_person.id, spouse.id)

        container = QFrame()
        container.setObjectName("spouseItem")
        container.setStyleSheet(
            """
            #spouseItem {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
        """
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 이름 및 상태 (XSS 방지)
        name_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{sanitize_html(spouse.name)}</b>")

        if is_current:
            status_label = QLabel(
                f"<span style='color: green;'>● {sanitize_html(tr('label.current_spouse'))}</span>"
            )
        elif rel and rel.is_divorced:
            status_label = QLabel(
                f"<span style='color: gray;'>{sanitize_html(tr('label.divorced'))}</span>"
            )
        else:
            status_label = QLabel("")

        name_layout.addWidget(name_label)
        name_layout.addWidget(status_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # 결혼일
        marriage_layout = QHBoxLayout()
        marriage_title = QLabel(tr("label.marriage_date") + ":")
        marriage_layout.addWidget(marriage_title)

        marriage_widget, marriage_group = self._create_date_input_widget()
        if rel:
            marriage_group.set_values(
                rel.marriage_year, rel.marriage_month, rel.marriage_day, rel.is_lunar_marriage
            )
        marriage_group.set_read_only(not self._is_editing)
        marriage_layout.addWidget(marriage_widget)
        layout.addLayout(marriage_layout)

        # 이혼일
        divorce_layout = QHBoxLayout()
        divorce_title = QLabel(tr("label.divorce_date") + ":")
        divorce_layout.addWidget(divorce_title)

        divorce_widget, divorce_group = self._create_date_input_widget()
        if rel:
            divorce_group.set_values(
                rel.divorce_year, rel.divorce_month, rel.divorce_day, False
            )  # 이혼일은 음력 없음
        divorce_group.is_lunar.hide()  # 이혼일은 음력 체크박스 숨김
        divorce_group.set_read_only(not self._is_editing)
        divorce_layout.addWidget(divorce_widget)
        layout.addLayout(divorce_layout)

        self.spouse_list_layout.addWidget(container)

        # 위젯 참조 저장
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

    def _clear_inputs(self):
        """입력 필드 초기화."""
        self.name_input.clear()
        self.gender_combo.setCurrentIndex(0)
        self.birth_date_group.clear()
        self.death_date_group.clear()
        self.birth_place_input.clear()
        self.current_address_input.clear()
        self.occupation_input.clear()
        self.education_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.notes_input.clear()

        none_text = tr("label.none")
        self.father_label.setText(none_text)
        self.mother_label.setText(none_text)
        self._clear_spouse_widgets()
        self.children_label.setText(none_text)

    def _toggle_edit(self):
        """편집 모드 토글."""
        self._is_editing = not self._is_editing
        self._set_read_only(not self._is_editing)

        if self._is_editing:
            self.edit_btn.setText(tr("button.cancel"))
            self.button_frame.show()
        else:
            self.edit_btn.setText(tr("button.edit"))
            self.button_frame.hide()
            self._load_person_data()  # 변경 취소

    def _cancel_edit(self):
        """편집 취소."""
        self._is_editing = False
        self._set_read_only(True)
        self.edit_btn.setText(tr("button.edit"))
        self.button_frame.hide()
        self._load_person_data()

    def _set_read_only(self, read_only: bool):
        """읽기 전용 모드 설정."""
        self.name_input.setReadOnly(read_only)
        self.gender_combo.setEnabled(not read_only)
        self.birth_date_group.set_read_only(read_only)
        self.death_date_group.set_read_only(read_only)
        self.birth_place_input.setReadOnly(read_only)
        self.current_address_input.setReadOnly(read_only)
        self.occupation_input.setReadOnly(read_only)
        self.education_input.setReadOnly(read_only)
        self.phone_input.setReadOnly(read_only)
        self.email_input.setReadOnly(read_only)
        self.notes_input.setReadOnly(read_only)

        # 배우자 관계 날짜 입력 필드
        for spouse_id, widgets in self._spouse_widgets.items():
            if spouse_id == "_none":
                continue
            if "marriage_group" in widgets:
                widgets["marriage_group"].set_read_only(read_only)
            if "divorce_group" in widgets:
                widgets["divorce_group"].set_read_only(read_only)

    def _limit_notes_length(self):
        """메모 길이 제한 (UI 성능 보호)."""
        current_text = self.notes_input.toPlainText()
        if len(current_text) > MAX_NOTES_LENGTH:
            cursor = self.notes_input.textCursor()
            cursor.setPosition(MAX_NOTES_LENGTH)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()

    def _validate_date(self, year: int, month: int, day: int, label: str) -> tuple[bool, str]:
        """날짜 유효성 검증 (윤년 및 월별 일수 체크).

        Args:
            year: 연도
            month: 월 (1-12)
            day: 일
            label: 에러 메시지용 라벨 (예: "Birth", "Death")

        Returns:
            (성공 여부, 에러 메시지)
        """
        # 월별 일수 (윤년 아닌 경우)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # 윤년 체크
        is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if is_leap_year:
            days_in_month[1] = 29

        # 일수 유효성 검사
        if month < 1 or month > 12:
            return False, f"{label} month must be between 1 and 12"

        max_day = days_in_month[month - 1]
        if day < 1 or day > max_day:
            return False, f"{label} day must be between 1 and {max_day} for month {month}"

        return True, ""

    def _validate_input(self) -> tuple[bool, str]:
        """입력 데이터 검증. (성공 여부, 에러 메시지) 반환."""
        # 이름 검증
        name = self.name_input.text().strip()
        if not name:
            return False, (
                tr("error.name_required") if "error.name_required" in dir() else "Name is required"
            )

        # 이메일 검증
        email = self.email_input.text().strip()
        if email:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                return False, (
                    tr("error.invalid_email")
                    if "error.invalid_email" in dir()
                    else "Invalid email format"
                )

        # 날짜 검증
        birth_year, birth_month, birth_day, _ = self.birth_date_group.get_values()
        death_year, death_month, death_day, _ = self.death_date_group.get_values()

        # 생년월일 유효성 검사
        if birth_month and (birth_month < 1 or birth_month > 12):
            return False, "Birth month must be between 1 and 12"

        if birth_year and birth_month and birth_day:
            is_valid, error_msg = self._validate_date(birth_year, birth_month, birth_day, "Birth")
            if not is_valid:
                return False, error_msg
        elif birth_day and birth_day < 1:
            return False, "Birth day must be at least 1"

        # 사망일 유효성 검사
        if death_month and (death_month < 1 or death_month > 12):
            return False, "Death month must be between 1 and 12"

        if death_year and death_month and death_day:
            is_valid, error_msg = self._validate_date(death_year, death_month, death_day, "Death")
            if not is_valid:
                return False, error_msg
        elif death_day and death_day < 1:
            return False, "Death day must be at least 1"

        # 생년월일과 사망일 비교
        if birth_year and death_year:
            if death_year < birth_year:
                return False, "Death date cannot be before birth date"
            elif death_year == birth_year and birth_month and death_month:
                if death_month < birth_month:
                    return False, "Death date cannot be before birth date"
                elif death_month == birth_month and birth_day and death_day:
                    if death_day < birth_day:
                        return False, "Death date cannot be before birth date"

        return True, ""

    def _save(self):
        """변경사항 저장."""
        if not self.current_person:
            return

        # 입력 검증
        is_valid, error_msg = self._validate_input()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        p = self.current_person

        p.name = self.name_input.text().strip()[:MAX_NAME_LENGTH]
        p.gender = self.gender_combo.currentData()

        # 생년월일
        p.birth_year, p.birth_month, p.birth_day, p.is_lunar_birth = (
            self.birth_date_group.get_values()
        )

        # 사망일
        p.death_year, p.death_month, p.death_day, p.is_lunar_death = (
            self.death_date_group.get_values()
        )

        # 추가 정보
        p.birth_place = self.birth_place_input.text().strip()[:MAX_TEXT_LENGTH]
        p.current_address = self.current_address_input.text().strip()[:MAX_TEXT_LENGTH]
        p.occupation = self.occupation_input.text().strip()[:MAX_TEXT_LENGTH]
        p.education = self.education_input.text().strip()[:MAX_TEXT_LENGTH]
        p.phone = self.phone_input.text().strip()[:MAX_PHONE_LENGTH]
        p.email = self.email_input.text().strip()[:MAX_EMAIL_LENGTH]
        p.notes = self.notes_input.toPlainText().strip()[:MAX_NOTES_LENGTH]

        # 배우자 관계 결혼일/이혼일 저장
        self._save_spouse_relationships()

        self.person_updated.emit(p)

        self._is_editing = False
        self._set_read_only(True)
        self.edit_btn.setText(tr("button.edit"))
        self.button_frame.hide()

    def _save_spouse_relationships(self):
        """배우자 관계의 결혼일/이혼일 저장."""
        if not self.family_tree:
            return

        for spouse_id, widgets in self._spouse_widgets.items():
            if spouse_id == "_none":
                continue

            rel = widgets.get("relationship")
            if not rel:
                continue

            marriage_group = widgets.get("marriage_group")
            divorce_group = widgets.get("divorce_group")

            if marriage_group:
                year, month, day, is_lunar = marriage_group.get_values()
                rel.marriage_year = year
                rel.marriage_month = month
                rel.marriage_day = day
                rel.is_lunar_marriage = is_lunar

            if divorce_group:
                year, month, day, _ = divorce_group.get_values()
                rel.divorce_year = year
                rel.divorce_month = month
                rel.divorce_day = day

        self.family_tree.mark_modified()

    def _request_add_relationship(self, rel_type: str):
        """관계 추가 요청."""
        if self.current_person:
            self.add_relationship_requested.emit(self.current_person.id, rel_type)
