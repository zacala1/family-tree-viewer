"""Person Card 위젯 - 목록용 간단한 카드."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush

from ..models.person import Person
from ..utils.theme_manager import get_theme_manager
from ..i18n import tr


class PersonCard(QFrame):
    """가족 목록에서 사용하는 간단한 카드 위젯."""

    clicked = pyqtSignal(str)  # person_id
    double_clicked = pyqtSignal(str)  # person_id

    def __init__(self, person: Person, parent=None):
        super().__init__(parent)

        self.person = person
        self._is_selected = False

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성."""
        self.setObjectName("personCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 아이콘
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setObjectName("personIcon")
        self._update_icon()
        layout.addWidget(self.icon_label)

        # 정보
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self.name_label = QLabel(self.person.name or tr("label.no_name", fallback="(이름 없음)"))
        self.name_label.setObjectName("personName")
        info_layout.addWidget(self.name_label)

        self.date_label = QLabel(self.person.lifespan_str or "")
        self.date_label.setObjectName("personDate")
        info_layout.addWidget(self.date_label)

        layout.addLayout(info_layout)
        layout.addStretch()

    def _update_icon(self):
        """아이콘 업데이트."""
        # 원형 아이콘 생성
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경 원
        colors = get_theme_manager().get_tree_colors()
        painter.setBrush(QBrush(QColor(colors['icon_bg'])))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 40, 40)

        # 사람 실루엣
        painter.setBrush(QBrush(QColor(colors['icon_fg'])))
        # 머리
        painter.drawEllipse(14, 6, 12, 12)
        # 몸통
        from PyQt6.QtGui import QPainterPath

        body = QPainterPath()
        body.moveTo(8, 38)
        body.quadTo(20, 18, 32, 38)
        painter.drawPath(body)

        painter.end()

        self.icon_label.setPixmap(pixmap)

    def update_person(self, person: Person):
        """Person 정보 업데이트."""
        self.person = person
        self.name_label.setText(person.name or "(이름 없음)")
        self.date_label.setText(person.lifespan_str or "")

    def set_selected(self, selected: bool):
        """선택 상태 설정."""
        self._is_selected = selected
        if selected:
            self.setProperty("selected", True)
        else:
            self.setProperty("selected", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        """마우스 클릭."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.person.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """더블클릭."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.person.id)
        super().mouseDoubleClickEvent(event)
