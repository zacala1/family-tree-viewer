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
    delete_photo,
    get_photo_path,
    load_pixmap_oriented,
)


# _ClickableLabel은 widgets/photo_carousel.py로 이동.
# 본 모듈에서 더 이상 사용 안 함.


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

    def showEvent(self, event):
        """다이얼로그 표시 시 부드러운 fade-in (180ms)."""
        super().showEvent(event)
        from ..utils.animation import fade_in_widget
        fade_in_widget(self)
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


# DateInputGroup 헬퍼는 widgets/date_input_group.py로 이동됨.
from .widgets.date_input_group import DateInputGroup, create_date_input_widget


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
        """create_date_input_widget의 thin wrapper — 외부 호출 호환용."""
        return create_date_input_widget()

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

        # 편집 모드 배지 — 평소 숨김, 편집 모드 진입 시 표시
        self.edit_mode_badge = QLabel(tr("label.editing_badge"))
        self.edit_mode_badge.setObjectName("editModeBadge")
        self.edit_mode_badge.setVisible(False)
        header_layout.addWidget(self.edit_mode_badge)

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

        # 사진 — PhotoCarousel 위젯에 위임 (사진 표시·네비·primary 변경)
        from .widgets.photo_carousel import PhotoCarousel
        self.photo_carousel = PhotoCarousel()
        # 호스트로서 파일 I/O는 detail_panel이 수행
        self.photo_carousel.add_photo_requested.connect(self._on_carousel_add_photo)
        self.photo_carousel.remove_photo_requested.connect(self._on_carousel_remove_photo)
        self.photo_carousel.set_primary_requested.connect(self._on_carousel_set_primary)
        self.photo_carousel.photo_clicked.connect(self._on_carousel_photo_clicked)

        self.photo_container_label = QLabel(tr("label.photo") + ":")
        self.extra_layout.addRow(self.photo_container_label, self.photo_carousel)

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

        # === 이벤트 탭 — EventsTab 위젯에 위임 ===
        from .widgets.events_tab import EventsTab as _EventsTab
        self.events_tab = _EventsTab()
        self.events_tab.events_changed.connect(self._emit_person_copy)
        self.tabs.addTab(self.events_tab, tr("tab.events"))

        # === 관계 탭 — RelationshipsTab 위젯에 위임 ===
        from .widgets.relationships_tab import RelationshipsTab as _RelationshipsTab
        self.rel_tab = _RelationshipsTab()
        # add_relationship_requested signal을 detail_panel의 signal로 forward
        self.rel_tab.add_relationship_requested.connect(self._request_add_relationship)
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
        self.edit_mode_badge.setText(tr("label.editing_badge"))
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
        # 사진 캐러셀의 모든 버튼·툴팁은 위젯 자체가 관리
        self.photo_carousel.update_ui_texts()

        # 메모 탭
        self.notes_input.setPlaceholderText(tr("label.notes_placeholder"))

        # 관계 탭 — 위젯 자체가 관리
        self.rel_tab.update_ui_texts()

        # 버튼
        self.cancel_btn.setText(tr("button.cancel"))
        self.save_btn.setText(tr("button.save"))

        # 이벤트 탭 버튼 (정렬 토글 라벨은 현재 방향에 맞춰)
        # 이벤트 탭의 모든 라벨·툴팁은 위젯이 관리
        self.events_tab.update_ui_texts()

        # 관계 정보 업데이트
        self._update_relationships()

    def set_person(self, person: Person, family_tree: FamilyTree):
        """표시할 Person 설정."""
        self.current_person = person
        self.family_tree = family_tree
        # 사진 카로셀 + 이벤트 탭에 새 인물 전달
        self.photo_carousel.set_photos(person.photo_paths if person else [])
        self.events_tab.set_person(person)
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

        # 사진 — carousel이 알아서 표시 (set_person에서 set_photos로 이미 전달)
        # 외부에서 person.photo_paths를 직접 수정한 경우를 위해 refresh
        self.photo_carousel.set_photos(p.photo_paths)

        # 이벤트
        self.events_tab.refresh()

    def _update_relationships(self):
        """관계 탭에 현재 person + family_tree 전달."""
        self.rel_tab.set_context(self.current_person, self.family_tree)

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

        # 관계 탭은 context 초기화로 정리
        self.rel_tab.set_context(None, None)

    def _toggle_edit(self):
        """편집 모드 토글."""
        self._is_editing = not self._is_editing
        self._set_read_only(not self._is_editing)

        if self._is_editing:
            self.edit_btn.setText(tr("button.cancel"))
            self.button_frame.show()
            self.edit_mode_badge.setVisible(True)
        else:
            self.edit_btn.setText(tr("button.edit"))
            self.button_frame.hide()
            self.edit_mode_badge.setVisible(False)
            self._load_person_data()  # 변경 취소

        # 빈 이벤트 상태의 CTA 활성/비활성을 편집 모드와 동기화
        self.events_tab.refresh()

    def _cancel_edit(self):
        """편집 취소."""
        self._is_editing = False
        self._set_read_only(True)
        self.edit_btn.setText(tr("button.edit"))
        self.button_frame.hide()
        self.edit_mode_badge.setVisible(False)
        self._load_person_data()
        self.events_tab.refresh()

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

        # 사진 카로셀 — edit mode 전달 (carousel이 자체 버튼 상태 관리)
        self.photo_carousel.set_editing(not read_only)

        # 이벤트 버튼
        # 이벤트 탭은 자체 edit 모드 관리
        self.events_tab.set_editing(not read_only)

        # 관계 탭 (배우자 결혼/이혼일 input)도 edit mode 전달
        self.rel_tab.set_editing(not read_only)

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
        self.edit_mode_badge.setVisible(False)

    def _save_spouse_relationships(self):
        """RelationshipsTab에 저장 위임. 결혼>이혼 순서 위반 시 경고 표시."""
        invalid_names = self.rel_tab.save_spouse_dates()
        if invalid_names:
            QMessageBox.warning(
                self,
                tr("dialog.marriage_order_title"),
                tr(
                    "dialog.marriage_order_message",
                    names=", ".join(invalid_names),
                ),
            )

    def _request_add_relationship(self, rel_type: str):
        """관계 추가 요청."""
        if self.current_person:
            self.add_relationship_requested.emit(self.current_person.id, rel_type)

    # 사진 표시·네비게이션은 PhotoCarousel 위젯이 담당.
    # 아래 4개 핸들러는 carousel의 signal을 받아 파일 I/O + person 모델 변경.

    def _on_carousel_set_primary(self, path: str):
        """Carousel set_primary_requested 핸들러."""
        if not self.current_person or not self._is_editing:
            return
        self.current_person.set_primary_photo(path)
        self.photo_carousel.set_photos(self.current_person.photo_paths)
        self.photo_carousel.jump_to_first()
        self._emit_person_copy()

    # 이벤트 정렬 토글 + 추가/편집/삭제는 EventsTab 위젯에 위임

    def _on_carousel_photo_clicked(self, path: str):
        """Carousel photo_clicked 핸들러 — 풀사이즈 lightbox 표시."""
        if not self.current_person:
            return
        name = self.current_person.name or tr("label.no_name")
        total = self.photo_carousel.total_count()
        if total > 1:
            name = f"{name}  ({self.photo_carousel.current_index() + 1} / {total})"
        dlg = _PhotoLightbox(path, name, self)
        dlg.exec()
        dlg.deleteLater()

    def _on_carousel_add_photo(self):
        """Carousel add_photo_requested 핸들러 — 파일 다이얼로그 + save_photo."""
        if not self.current_person or not self._is_editing:
            return

        formats = " ".join([f"*{ext}" for ext in SUPPORTED_IMAGE_FORMATS])
        filter_str = f"{tr('file_filter.image_files')} ({formats})"
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.select_photo_title"), "", filter_str,
        )
        if not file_path:
            return

        try:
            relative_path = save_photo(file_path, self.current_person.id)
            if relative_path:
                self.current_person.add_photo(relative_path)
                # 추가된 사진을 즉시 표시
                self.photo_carousel.set_photos(self.current_person.photo_paths)
                self.photo_carousel.jump_to_last()
                self._emit_person_copy()
                logger.info(f"Photo added for {self.current_person.name}: {relative_path}")
            else:
                QMessageBox.warning(
                    self,
                    tr("error.photo_save_failed_title"),
                    tr("error.photo_save_failed"),
                )
        except ValueError as e:
            QMessageBox.warning(self, tr("error.photo_invalid_title"), str(e))
        except Exception as e:
            from ..utils.error_mapper import humanize_exception
            logger.error(f"Failed to select photo: {e!r}")
            QMessageBox.critical(
                self,
                tr("error.photo_error_title"),
                humanize_exception(e, context=tr("error.context_add_photo")),
            )

    def _on_carousel_remove_photo(self, path: str):
        """Carousel remove_photo_requested 핸들러 — 확인 + delete + model 갱신."""
        if not self.current_person or not self._is_editing:
            return
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
            delete_photo(path)
            self.current_person.remove_photo(path)
            self.photo_carousel.set_photos(self.current_person.photo_paths)
            self._emit_person_copy()
            logger.info(f"Photo removed for {self.current_person.name}: {path}")
        except Exception as e:
            from ..utils.error_mapper import humanize_exception
            logger.error(f"Failed to remove photo: {e!r}")
            QMessageBox.critical(
                self,
                tr("error.photo_error_title"),
                humanize_exception(e, context=tr("error.context_remove_photo")),
            )

    def _emit_person_copy(self):
        """현재 person의 deepcopy를 emit (Undo/Redo 정합성 보장)."""
        from copy import deepcopy
        self.person_updated.emit(deepcopy(self.current_person))

    # 이벤트 추가·편집·삭제·렌더링은 모두 EventsTab 위젯이 담당
