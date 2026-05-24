"""상세 정보 패널."""

from typing import Optional
import html
from pathlib import Path
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
    QFileDialog,
    QDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from ..models.person import Person
from ..models.family_tree import FamilyTree
from ..models.validators import PersonValidator
from ..models.event import Event
from ..models.relationship import RelationshipRequestType
from .event_dialog import EventDialog
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
    SUPPORTED_IMAGE_FORMATS,
    PHOTO_THUMBNAIL_SIZE,
)
from ..utils.photo_manager import (
    save_photo,
    load_thumbnail,
    delete_photo,
    get_photo_path,
    load_pixmap_oriented,
)


class _ClickableLabel(QLabel):
    """클릭 가능한 QLabel — 사진 썸네일을 lightbox로 확대하기 위한 헬퍼."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _PhotoLightbox(QDialog):
    """사진 풀사이즈 보기 다이얼로그.

    화면 80% 크기로 사진을 비율 유지하여 표시. 좌클릭·ESC로 닫기.
    """

    def __init__(self, photo_path: str, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title or tr("label.photo"))
        self.setModal(True)

        # 화면 80% 크기
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            target_w = max(400, int(geom.width() * 0.8))
            target_h = max(300, int(geom.height() * 0.8))
        else:
            target_w, target_h = 800, 600
        self.resize(target_w, target_h)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        abs_path = get_photo_path(photo_path)
        # EXIF orientation을 반영해 풀사이즈에서도 옳은 방향 표시
        pixmap = load_pixmap_oriented(abs_path) if abs_path else QPixmap()

        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if pixmap.isNull():
            label.setText(tr("error.photo_error_message"))
        else:
            label.setPixmap(
                pixmap.scaled(
                    target_w,
                    target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.accept()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
from ..utils.theme_manager import get_theme_manager
from ..utils import logger


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
        conversion_label: Optional[QLabel] = None,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.is_lunar = is_lunar
        self.year_label = year_label
        self.month_label = month_label
        self.day_label = day_label
        self.conversion_label = conversion_label

        # 값 변경 시 양력↔음력 변환 라벨 자동 갱신
        if conversion_label is not None:
            year.valueChanged.connect(self._update_conversion)
            month.valueChanged.connect(self._update_conversion)
            day.valueChanged.connect(self._update_conversion)
            is_lunar.toggled.connect(self._update_conversion)
            self._update_conversion()

    def _update_conversion(self):
        """현재 값의 반대 캘린더 표기를 conversion_label에 표시.

        - 음력 입력 → "→ 양력 YYYY.MM.DD" 표시
        - 양력 입력 → "→ 음력 YYYY.MM.DD" (윤달이면 끝에 *)
        - 라이브러리 미설치, 값 불완전, 변환 실패 시 빈 문자열
        """
        if self.conversion_label is None:
            return
        from ..utils.lunar_calendar import LunarCalendarUtil

        if not LunarCalendarUtil.is_available():
            self.conversion_label.setText("")
            return

        year, month, day, is_lunar = self.get_values()
        if not (year and month and day):
            self.conversion_label.setText("")
            return

        if is_lunar:
            solar = LunarCalendarUtil.lunar_to_solar(year, month, day)
            if solar:
                self.conversion_label.setText(
                    f"→ {tr('label.solar')} {solar[0]}.{solar[1]:02d}.{solar[2]:02d}"
                )
            else:
                self.conversion_label.setText("")
        else:
            lunar = LunarCalendarUtil.solar_to_lunar(year, month, day)
            if lunar:
                leap_mark = "*" if lunar[3] else ""
                self.conversion_label.setText(
                    f"→ {tr('label.lunar')} {lunar[0]}.{lunar[1]:02d}{leap_mark}.{lunar[2]:02d}"
                )
            else:
                self.conversion_label.setText("")

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
        year_val = self.year.value()
        month_val = self.month.value()
        day_val = self.day.value()

        # YEAR_MIN, MONTH_MIN, DAY_MIN are sentinel values meaning "not set"
        year = year_val if year_val != YEAR_MIN else None
        month = month_val if month_val != MONTH_MIN else None
        day = day_val if day_val != DAY_MIN else None

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
        # 변환 라벨도 새 언어로 다시 계산
        self._update_conversion()


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

        # 음력↔양력 자동 변환 표시 라벨 (값 변경 시 자동 갱신)
        conversion_label = QLabel("")
        conversion_label.setObjectName("dateConversionLabel")
        # theme의 text_muted 사용 (WCAG AA 대비 보장 — gray는 다크/라이트 모두 미달)
        _conv_color = get_theme_manager().get_tree_colors().get("text_muted", "#777777")
        conversion_label.setStyleSheet(f"color: {_conv_color}; padding-left: 8px;")
        layout.addWidget(conversion_label)
        layout.addStretch()

        group = DateInputGroup(
            year, month, day, is_lunar,
            year_label, month_label, day_label,
            conversion_label,
        )
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
        self.name_input.setAccessibleName(tr("label.name"))
        self.name_label = QLabel(tr("label.name") + ":")
        self.basic_layout.addRow(self.name_label, self.name_input)

        # 성별
        self.gender_combo = QComboBox()
        self.gender_combo.setObjectName("detailCombo")
        self.gender_combo.addItem(tr("label.male"), "M")
        self.gender_combo.addItem(tr("label.female"), "F")
        self.gender_combo.setAccessibleName(tr("label.gender"))
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

        self.nationality_input = QLineEdit()
        self.nationality_input.setMaxLength(MAX_TEXT_LENGTH)
        self.nationality_label = QLabel(tr("label.nationality") + ":")
        self.extra_layout.addRow(self.nationality_label, self.nationality_input)

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

        # 사진
        photo_container = QWidget()
        photo_layout = QVBoxLayout(photo_container)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        photo_layout.setSpacing(8)

        # 사진 썸네일 (클릭 시 lightbox 확대)
        self.photo_label = _ClickableLabel()
        self.photo_label.setObjectName("photoThumbnail")
        self.photo_label.setFixedSize(PHOTO_THUMBNAIL_SIZE, PHOTO_THUMBNAIL_SIZE)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Styled via QSS #photoThumbnail selector
        self.photo_label.setText(tr("label.no_photo"))
        self.photo_label.clicked.connect(self._on_photo_clicked)
        photo_layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 사진 캐러셀 네비게이션 — ◀ [n/N] ▶
        self._photo_index = 0
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        self.prev_photo_btn = QPushButton("◀")
        self.prev_photo_btn.setFixedWidth(30)
        self.prev_photo_btn.setToolTip(tr("tooltip.previous_photo"))
        self.prev_photo_btn.setAccessibleName(tr("tooltip.previous_photo"))
        self.prev_photo_btn.clicked.connect(self._prev_photo)
        nav_layout.addWidget(self.prev_photo_btn)

        self.photo_counter_label = QLabel("0 / 0")
        self.photo_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_counter_label.setMinimumWidth(50)
        self.photo_counter_label.setAccessibleName(tr("accessibility.photo_counter"))
        nav_layout.addWidget(self.photo_counter_label)

        self.next_photo_btn = QPushButton("▶")
        self.next_photo_btn.setFixedWidth(30)
        self.next_photo_btn.setToolTip(tr("tooltip.next_photo"))
        self.next_photo_btn.setAccessibleName(tr("tooltip.next_photo"))
        self.next_photo_btn.clicked.connect(self._next_photo)
        nav_layout.addWidget(self.next_photo_btn)
        nav_layout.addStretch()
        photo_layout.addLayout(nav_layout)

        # 사진 버튼 — add / remove / set as primary
        photo_buttons = QHBoxLayout()
        self.select_photo_btn = QPushButton(tr("button.select_photo"))
        self.select_photo_btn.clicked.connect(self._select_photo)
        photo_buttons.addWidget(self.select_photo_btn)

        self.remove_photo_btn = QPushButton(tr("button.remove_photo"))
        self.remove_photo_btn.clicked.connect(self._remove_photo)
        self.remove_photo_btn.setEnabled(False)
        photo_buttons.addWidget(self.remove_photo_btn)

        self.set_primary_photo_btn = QPushButton(tr("button.set_primary_photo"))
        self.set_primary_photo_btn.setToolTip(tr("tooltip.set_primary_photo"))
        self.set_primary_photo_btn.setAccessibleName(tr("button.set_primary_photo"))
        self.set_primary_photo_btn.clicked.connect(self._set_primary_photo)
        self.set_primary_photo_btn.setEnabled(False)
        photo_buttons.addWidget(self.set_primary_photo_btn)

        photo_layout.addLayout(photo_buttons)

        self.photo_container_label = QLabel(tr("label.photo") + ":")
        self.extra_layout.addRow(self.photo_container_label, photo_container)

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

        # === 이벤트 탭 ===
        self.events_tab = QWidget()
        events_layout = QVBoxLayout(self.events_tab)
        events_layout.setContentsMargins(8, 12, 8, 8)

        # 이벤트 목록
        self.events_list_widget = QWidget()
        self.events_list_layout = QVBoxLayout(self.events_list_widget)
        self.events_list_layout.setContentsMargins(0, 0, 0, 0)
        self.events_list_layout.setSpacing(8)

        events_scroll = QScrollArea()
        events_scroll.setWidgetResizable(True)
        events_scroll.setWidget(self.events_list_widget)
        events_layout.addWidget(events_scroll)

        # 이벤트 버튼
        events_button_layout = QHBoxLayout()
        self.add_event_btn = QPushButton(tr("button.add_event"))
        self.add_event_btn.clicked.connect(self._add_event)
        events_button_layout.addWidget(self.add_event_btn)
        events_button_layout.addStretch()
        # 정렬 토글 — 기본은 오래된 순(↑). 클릭 시 최근 순(↓)으로 반전
        self._events_sort_descending = False
        self.events_sort_btn = QPushButton(tr("button.sort_oldest_first"))
        self.events_sort_btn.setObjectName("eventsSortBtn")
        self.events_sort_btn.setToolTip(tr("tooltip.toggle_event_sort"))
        self.events_sort_btn.setAccessibleName(tr("tooltip.toggle_event_sort"))
        self.events_sort_btn.clicked.connect(self._toggle_events_sort)
        events_button_layout.addWidget(self.events_sort_btn)
        events_layout.addLayout(events_button_layout)

        self.tabs.addTab(self.events_tab, tr("tab.events"))

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
        self.set_parent_btn.clicked.connect(lambda: self._request_add_relationship(RelationshipRequestType.PARENT))
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
        self.add_spouse_btn.clicked.connect(lambda: self._request_add_relationship(RelationshipRequestType.SPOUSE))
        self.spouse_group_layout.addWidget(self.add_spouse_btn)

        rel_layout.addWidget(self.spouse_group)

        # 자녀
        self.children_group = QGroupBox(tr("label.children"))
        children_layout = QVBoxLayout(self.children_group)
        self.children_label = QLabel(tr("label.none"))
        children_layout.addWidget(self.children_label)

        self.add_child_btn = QPushButton(tr("button.add_child"))
        self.add_child_btn.clicked.connect(lambda: self._request_add_relationship(RelationshipRequestType.CHILD))
        children_layout.addWidget(self.add_child_btn)

        rel_layout.addWidget(self.children_group)

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

        rel_layout.addWidget(self.extended_group)
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
        self.tabs.setTabText(3, tr("tab.events"))
        self.tabs.setTabText(4, tr("tab.relationships"))

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
        self.nationality_label.setText(tr("label.nationality") + ":")
        self.occupation_label.setText(tr("label.occupation") + ":")
        self.education_label.setText(tr("label.education") + ":")
        self.phone_label.setText(tr("label.phone") + ":")
        self.email_label.setText(tr("label.email") + ":")
        self.photo_container_label.setText(tr("label.photo") + ":")
        self.select_photo_btn.setText(tr("button.select_photo"))
        self.remove_photo_btn.setText(tr("button.remove_photo"))
        self.set_primary_photo_btn.setText(tr("button.set_primary_photo"))
        self.set_primary_photo_btn.setToolTip(tr("tooltip.set_primary_photo"))
        self.prev_photo_btn.setToolTip(tr("tooltip.previous_photo"))
        self.next_photo_btn.setToolTip(tr("tooltip.next_photo"))

        # 메모 탭
        self.notes_input.setPlaceholderText(tr("label.notes_placeholder"))

        # 관계 탭
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

        # 버튼
        self.cancel_btn.setText(tr("button.cancel"))
        self.save_btn.setText(tr("button.save"))

        # 이벤트 탭 버튼 (정렬 토글 라벨은 현재 방향에 맞춰)
        self.add_event_btn.setText(tr("button.add_event"))
        if self._events_sort_descending:
            self.events_sort_btn.setText(tr("button.sort_newest_first"))
        else:
            self.events_sort_btn.setText(tr("button.sort_oldest_first"))
        self.events_sort_btn.setToolTip(tr("tooltip.toggle_event_sort"))

        # 관계 정보 업데이트
        self._update_relationships()

    def set_person(self, person: Person, family_tree: FamilyTree):
        """표시할 Person 설정."""
        self.current_person = person
        self.family_tree = family_tree
        # 새 인물 선택 시 항상 primary 사진부터 표시
        self._photo_index = 0
        self._load_person_data()
        self._update_relationships()

    def load_person(self, person_id: str):
        """ID로 Person을 조회하여 패널에 로드."""
        if not self.family_tree:
            return
        person = self.family_tree.get_person(person_id)
        if person:
            self.set_person(person, self.family_tree)

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

        # 추가 정보 (None 안전)
        self.birth_place_input.setText(p.birth_place or "")
        self.current_address_input.setText(p.current_address or "")
        self.nationality_input.setText(p.nationality or "")
        self.occupation_input.setText(p.occupation or "")
        self.education_input.setText(p.education or "")
        self.phone_input.setText(p.phone or "")
        self.email_input.setText(p.email or "")
        self.notes_input.setText(p.notes or "")

        # 사진
        self._load_photo()

        # 이벤트
        self._refresh_events_list()

    def _update_relationships(self):
        """관계 정보 업데이트."""
        none_text = tr("label.none")

        # 기존 배우자 위젯 정리
        self._clear_spouse_widgets()

        if not self.current_person or not self.family_tree:
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

        # 확대 관계
        pid = self.current_person.id
        for persons, label in [
            (self.family_tree.get_grandparents(pid), self.grandparents_label),
            (self.family_tree.get_grandchildren(pid), self.grandchildren_label),
            (self.family_tree.get_uncles_aunts(pid), self.uncles_aunts_label),
            (self.family_tree.get_cousins(pid), self.cousins_label),
            (self.family_tree.get_in_laws(pid), self.in_laws_label),
        ]:
            if persons:
                label.setText(", ".join(p.name for p in persons))
            else:
                label.setText(none_text)

    def _clear_spouse_widgets(self):
        """배우자 위젯들 정리."""
        # Remove all widgets from layout (sufficient — no second pass needed)
        while self.spouse_list_layout.count():
            item = self.spouse_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        self._spouse_widgets.clear()

    def _create_spouse_widget(self, spouse: Person, is_current: bool):
        """배우자 항목 위젯 생성."""
        rel = self.family_tree.get_spouse_relationship(self.current_person.id, spouse.id)

        container = QFrame()
        container.setObjectName("spouseItem")
        # Styled via QSS #spouseItem selector
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
        self.nationality_input.clear()
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

        # 빈 이벤트 상태의 CTA 활성/비활성을 편집 모드와 동기화
        self._refresh_events_list()

    def _cancel_edit(self):
        """편집 취소."""
        self._is_editing = False
        self._set_read_only(True)
        self.edit_btn.setText(tr("button.edit"))
        self.button_frame.hide()
        self._load_person_data()
        self._refresh_events_list()

    def _set_read_only(self, read_only: bool):
        """읽기 전용 모드 설정."""
        self.name_input.setReadOnly(read_only)
        self.gender_combo.setEnabled(not read_only)
        self.birth_date_group.set_read_only(read_only)
        self.death_date_group.set_read_only(read_only)
        self.birth_place_input.setReadOnly(read_only)
        self.current_address_input.setReadOnly(read_only)
        self.nationality_input.setReadOnly(read_only)
        self.occupation_input.setReadOnly(read_only)
        self.education_input.setReadOnly(read_only)
        self.phone_input.setReadOnly(read_only)
        self.email_input.setReadOnly(read_only)
        self.notes_input.setReadOnly(read_only)

        # 사진 버튼 — read_only일 때 모두 disable, 편집 시에는 사진 존재 여부에 따라
        self.select_photo_btn.setEnabled(not read_only)
        has_photo = (
            self.current_person is not None and len(self.current_person.photo_paths) > 0
        )
        self.remove_photo_btn.setEnabled((not read_only) and has_photo)
        # set primary는 _update_photo_nav_controls가 더 정밀한 조건 평가
        self._update_photo_nav_controls()

        # 이벤트 버튼
        self.add_event_btn.setEnabled(not read_only)

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


    def _validate_input(self) -> tuple[bool, str]:
        """입력 데이터 검증 (비즈니스 로직 레이어 사용)."""
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()

        birth_year, birth_month, birth_day, _ = self.birth_date_group.get_values()
        death_year, death_month, death_day, _ = self.death_date_group.get_values()

        return PersonValidator.validate_all(
            name=name,
            email=email,
            phone=phone,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            death_year=death_year,
            death_month=death_month,
            death_day=death_day
        )

    def _save(self):
        """변경사항 저장."""
        if not self.current_person:
            return

        # 입력 검증 — 실패 시 기본 정보 탭으로 이동 + 첫 필드 포커스
        is_valid, error_msg = self._validate_input()
        if not is_valid:
            # 검증 실패는 대부분 기본 정보 탭의 필드들 (이름·이메일·전화·생몰일)
            # 사용자가 즉시 수정할 수 있도록 해당 탭으로 자동 이동 + 첫 입력에 포커스
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()
            self.name_input.selectAll()
            QMessageBox.warning(
                self,
                tr("error.validation_title", fallback="Validation Error"),
                error_msg,
            )
            return

        # deepcopy로 새 Person 생성하여 원본 보존 (Undo/Redo 정합성)
        from copy import deepcopy
        updated = deepcopy(self.current_person)

        updated.name = self.name_input.text().strip()[:MAX_NAME_LENGTH]
        updated.gender = self.gender_combo.currentData()

        # 생년월일
        updated.birth_year, updated.birth_month, updated.birth_day, updated.is_lunar_birth = (
            self.birth_date_group.get_values()
        )

        # 사망일
        updated.death_year, updated.death_month, updated.death_day, updated.is_lunar_death = (
            self.death_date_group.get_values()
        )

        # 추가 정보
        updated.birth_place = self.birth_place_input.text().strip()[:MAX_TEXT_LENGTH]
        updated.current_address = self.current_address_input.text().strip()[:MAX_TEXT_LENGTH]
        updated.nationality = self.nationality_input.text().strip()[:MAX_TEXT_LENGTH]
        updated.occupation = self.occupation_input.text().strip()[:MAX_TEXT_LENGTH]
        updated.education = self.education_input.text().strip()[:MAX_TEXT_LENGTH]
        updated.phone = self.phone_input.text().strip()[:MAX_PHONE_LENGTH]
        updated.email = self.email_input.text().strip()[:MAX_EMAIL_LENGTH]
        updated.notes = self.notes_input.toPlainText().strip()[:MAX_NOTES_LENGTH]

        # 배우자 관계 결혼일/이혼일 저장
        self._save_spouse_relationships()

        self.person_updated.emit(updated)

        self._is_editing = False
        self._set_read_only(True)
        self.edit_btn.setText(tr("button.edit"))
        self.button_frame.hide()

    def _save_spouse_relationships(self):
        """배우자 관계의 결혼일/이혼일 저장.

        저장 후 marriage ≤ divorce 순서가 깨지면 사용자에게 경고 (저장은 차단 안 함 —
        오탈자 가능성과 재혼 등의 복잡한 케이스를 고려).
        """
        if not self.family_tree:
            return

        invalid_spouse_names = []

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

            # 저장 후 검증 — 결혼일이 이혼일보다 늦은 경우
            if not rel.is_valid_marriage_order():
                spouse = self.family_tree.get_person(spouse_id)
                if spouse:
                    invalid_spouse_names.append(spouse.name or tr("label.no_name"))

        self.family_tree.mark_modified()

        if invalid_spouse_names:
            QMessageBox.warning(
                self,
                tr("dialog.marriage_order_title"),
                tr(
                    "dialog.marriage_order_message",
                    names=", ".join(invalid_spouse_names),
                ),
            )

    def _request_add_relationship(self, rel_type: str):
        """관계 추가 요청."""
        if self.current_person:
            self.add_relationship_requested.emit(self.current_person.id, rel_type)

    def _current_photo_path(self) -> Optional[str]:
        """현재 표시 중인 사진의 path. photo_paths가 비어있으면 None."""
        if not self.current_person or not self.current_person.photo_paths:
            return None
        # 인덱스 안전 범위 보정
        if self._photo_index >= len(self.current_person.photo_paths):
            self._photo_index = max(0, len(self.current_person.photo_paths) - 1)
        if self._photo_index < 0:
            self._photo_index = 0
        return self.current_person.photo_paths[self._photo_index]

    def _update_photo_nav_controls(self):
        """카운터 라벨과 prev/next/primary 버튼의 활성화 상태 갱신."""
        if not self.current_person:
            self.photo_counter_label.setText("0 / 0")
            self.prev_photo_btn.setEnabled(False)
            self.next_photo_btn.setEnabled(False)
            self.set_primary_photo_btn.setEnabled(False)
            return
        total = len(self.current_person.photo_paths)
        if total == 0:
            self.photo_counter_label.setText("0 / 0")
            self.prev_photo_btn.setEnabled(False)
            self.next_photo_btn.setEnabled(False)
            self.set_primary_photo_btn.setEnabled(False)
        else:
            self.photo_counter_label.setText(f"{self._photo_index + 1} / {total}")
            self.prev_photo_btn.setEnabled(total > 1)
            self.next_photo_btn.setEnabled(total > 1)
            # primary 변경 버튼: 사진 2장 이상이고 현재가 primary가 아닐 때만
            is_currently_primary = self._photo_index == 0
            self.set_primary_photo_btn.setEnabled(
                self._is_editing and total > 1 and not is_currently_primary
            )

    def _load_photo(self):
        """현재 _photo_index의 사진을 thumbnail에 로드."""
        current_path = self._current_photo_path()
        if not current_path:
            self.photo_label.clear()
            self.photo_label.setText(tr("label.no_photo"))
            self.photo_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.photo_label.setToolTip("")
            self.remove_photo_btn.setEnabled(False)
            self._update_photo_nav_controls()
            return

        # 썸네일 로드
        thumbnail = load_thumbnail(current_path, PHOTO_THUMBNAIL_SIZE)

        if thumbnail:
            self.photo_label.setPixmap(thumbnail)
            self.photo_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self.photo_label.setToolTip(tr("tooltip.click_to_enlarge"))
            self.remove_photo_btn.setEnabled(self._is_editing)
        else:
            self.photo_label.clear()
            self.photo_label.setText(tr("label.no_photo"))
            self.photo_label.setCursor(Qt.CursorShape.ArrowCursor)
            self.photo_label.setToolTip("")
            self.remove_photo_btn.setEnabled(False)
            logger.warning(f"Failed to load photo: {current_path}")

        self._update_photo_nav_controls()

    def _prev_photo(self):
        """이전 사진."""
        if not self.current_person or len(self.current_person.photo_paths) < 2:
            return
        total = len(self.current_person.photo_paths)
        self._photo_index = (self._photo_index - 1) % total
        self._load_photo()

    def _next_photo(self):
        """다음 사진."""
        if not self.current_person or len(self.current_person.photo_paths) < 2:
            return
        total = len(self.current_person.photo_paths)
        self._photo_index = (self._photo_index + 1) % total
        self._load_photo()

    def _set_primary_photo(self):
        """현재 표시 중인 사진을 primary(첫 번째)로 설정."""
        if not self.current_person or not self._is_editing:
            return
        current = self._current_photo_path()
        if not current:
            return
        self.current_person.set_primary_photo(current)
        # primary는 항상 인덱스 0
        self._photo_index = 0
        self._load_photo()
        self._emit_person_copy()

    def _toggle_events_sort(self):
        """이벤트 정렬 방향 토글."""
        self._events_sort_descending = not self._events_sort_descending
        # 버튼 라벨 업데이트
        if self._events_sort_descending:
            self.events_sort_btn.setText(tr("button.sort_newest_first"))
        else:
            self.events_sort_btn.setText(tr("button.sort_oldest_first"))
        self._refresh_events_list()

    def _on_photo_clicked(self):
        """사진 썸네일 클릭 → 현재 표시 중인 사진을 풀사이즈 lightbox로."""
        current_path = self._current_photo_path()
        if not current_path:
            return
        # 사진이 여러 장이면 제목에 인덱스 표시 (예: "홍길동 (2 / 5)")
        name = self.current_person.name or tr("label.no_name")
        total = len(self.current_person.photo_paths)
        if total > 1:
            name = f"{name}  ({self._photo_index + 1} / {total})"
        dlg = _PhotoLightbox(current_path, name, self)
        dlg.exec()
        dlg.deleteLater()

    def _select_photo(self):
        """사진 선택 다이얼로그."""
        if not self.current_person or not self._is_editing:
            return

        # 지원 이미지 형식
        formats = " ".join([f"*{ext}" for ext in SUPPORTED_IMAGE_FORMATS])
        filter_str = f"{tr('file_filter.image_files')} ({formats})"

        # 파일 선택 다이얼로그
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.select_photo_title"),
            "",
            filter_str,
        )

        if not file_path:
            return

        try:
            # 사진 저장
            relative_path = save_photo(file_path, self.current_person.id)

            if relative_path:
                # Person 모델에 추가 — 기존 사진들은 유지, 새 사진은 list 끝에
                self.current_person.add_photo(relative_path)
                # 추가된 사진을 즉시 표시 (가장 마지막 인덱스로 이동)
                self._photo_index = len(self.current_person.photo_paths) - 1
                self._load_photo()

                # 변경사항 저장 신호 발생
                self._emit_person_copy()

                logger.info(f"Photo added for {self.current_person.name}: {relative_path}")
            else:
                QMessageBox.warning(
                    self,
                    tr("error.photo_save_failed_title"),
                    tr("error.photo_save_failed"),
                )

        except ValueError as e:
            QMessageBox.warning(
                self,
                tr("error.photo_invalid_title"),
                str(e),
            )
        except Exception as e:
            logger.error(f"Failed to select photo: {e}")
            QMessageBox.critical(
                self,
                tr("error.photo_error_title"),
                tr("error.photo_error_message"),
            )

    def _remove_photo(self):
        """현재 표시 중인 사진 제거 (다른 사진은 유지)."""
        current_path = self._current_photo_path()
        if not current_path or not self._is_editing:
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            tr("dialog.remove_photo_title"),
            tr("dialog.remove_photo_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 파일 삭제 (실패해도 모델에서는 제거)
            delete_photo(current_path)

            # Person 모델에서 제거 — 다음 사진이 자동으로 primary가 됨
            self.current_person.remove_photo(current_path)

            # 인덱스 보정: 마지막 사진을 지웠으면 한 칸 앞으로
            if self._photo_index >= len(self.current_person.photo_paths):
                self._photo_index = max(0, len(self.current_person.photo_paths) - 1)

            self._load_photo()
            self._emit_person_copy()

            logger.info(f"Photo removed for {self.current_person.name}: {current_path}")

        except Exception as e:
            logger.error(f"Failed to remove photo: {e}")
            QMessageBox.critical(
                self,
                tr("error.photo_error_title"),
                tr("error.photo_error_message"),
            )

    def _emit_person_copy(self):
        """현재 person의 deepcopy를 emit (Undo/Redo 정합성 보장)."""
        from copy import deepcopy
        self.person_updated.emit(deepcopy(self.current_person))

    def _add_event(self):
        """이벤트 추가."""
        if not self.current_person or not self._is_editing:
            return

        dialog = EventDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event = dialog.get_event()
            if event:
                event.person_id = self.current_person.id
                self.current_person.events.append(event)
                self._refresh_events_list()
                self._emit_person_copy()

    def _edit_event(self, event: Event):
        """이벤트 편집."""
        if not self.current_person or not self._is_editing:
            return

        dialog = EventDialog(event=event, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_events_list()
            self._emit_person_copy()

    def _delete_event(self, event: Event):
        """이벤트 삭제."""
        if not self.current_person or not self._is_editing:
            return

        reply = QMessageBox.question(
            self,
            tr("button.delete_event"),
            f"{tr('button.delete_event')}: {event.title}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_person.events = [
                e for e in self.current_person.events if e.id != event.id
            ]
            self._refresh_events_list()
            self._emit_person_copy()

    def _refresh_events_list(self):
        """이벤트 목록 새로고침."""
        # 기존 위젯 제거
        while self.events_list_layout.count():
            item = self.events_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not self.current_person or not self.current_person.events:
            # 빈 상태: 안내 + CTA 버튼 중앙 배치 (한 클릭에 추가 가능하도록)
            empty_label = QLabel(tr("message.no_events"))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            colors = get_theme_manager().get_tree_colors()
            empty_label.setStyleSheet(
                f"color: {colors['text_muted']}; padding: 20px 20px 8px 20px;"
            )
            self.events_list_layout.addWidget(empty_label)

            if self.current_person:
                cta_btn = QPushButton("+  " + tr("button.add_first_event"))
                cta_btn.setEnabled(self._is_editing)
                if not self._is_editing:
                    cta_btn.setToolTip(tr("tooltip.enter_edit_mode_first"))
                cta_btn.clicked.connect(self._add_event)
                btn_row = QHBoxLayout()
                btn_row.setContentsMargins(0, 0, 0, 0)
                btn_row.addStretch()
                btn_row.addWidget(cta_btn)
                btn_row.addStretch()
                btn_container = QWidget()
                btn_container.setLayout(btn_row)
                self.events_list_layout.addWidget(btn_container)

            self.events_list_layout.addStretch()
            return

        # 날짜순 정렬 (토글 가능: 오래된→최근 vs 최근→오래된)
        sorted_events = sorted(
            self.current_person.events,
            key=lambda e: (e.year or 9999, e.month or 12, e.day or 31),
            reverse=self._events_sort_descending,
        )

        # 이벤트 위젯 생성
        for event in sorted_events:
            event_widget = self._create_event_widget(event)
            self.events_list_layout.addWidget(event_widget)

        self.events_list_layout.addStretch()

    def _create_event_widget(self, event: Event) -> QWidget:
        """이벤트 위젯 생성."""
        widget = QFrame()
        widget.setObjectName("eventItem")
        # Styled via QSS #eventItem selector

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 제목 및 타입
        title_layout = QHBoxLayout()
        title_label = QLabel(f"<b>{sanitize_html(event.title)}</b>")
        title_layout.addWidget(title_label)

        type_label = QLabel(f"[{tr(f'event.types.{event.event_type}')}]")
        colors = get_theme_manager().get_tree_colors()
        type_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
        title_layout.addWidget(type_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # 날짜
        if event.date_str:
            date_label = QLabel(f"📅 {event.date_str}")
            date_label.setStyleSheet(f"color: {colors['accent']}; font-size: 13px;")
            layout.addWidget(date_label)

        # 장소
        if event.location:
            location_label = QLabel(f"📍 {sanitize_html(event.location)}")
            location_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
            layout.addWidget(location_label)

        # 설명
        if event.description:
            desc_label = QLabel(sanitize_html(event.description))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {colors['text_body']}; font-size: 13px;")
            layout.addWidget(desc_label)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        edit_btn = QPushButton(tr("button.edit_event"))
        edit_btn.clicked.connect(lambda: self._edit_event(event))
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton(tr("button.delete_event"))
        delete_btn.clicked.connect(lambda: self._delete_event(event))
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        return widget
