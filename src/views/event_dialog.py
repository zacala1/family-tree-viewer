"""Dialog for adding/editing events."""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from ..models.event import Event, EventType, EVENT_TYPES
from ..models.validators import EventValidator
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
)


class EventDialog(QDialog):
    """Dialog for creating or editing an event."""

    def __init__(self, event: Optional[Event] = None, parent=None):
        super().__init__(parent)
        self.event = event
        self.is_edit_mode = event is not None

        self.setWindowTitle(tr("button.edit_event") if self.is_edit_mode else tr("button.add_event"))
        self.setMinimumWidth(500)
        self.setModal(True)

        self._setup_ui()
        if self.event:
            self._load_event_data()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Form layout
        form = QFormLayout()
        form.setSpacing(8)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(tr("event.title"))
        self.title_input.setMaxLength(MAX_NAME_LENGTH)
        form.addRow(tr("event.title") + ":", self.title_input)

        # Event Type — 모델의 EVENT_TYPES 단일 소스 사용 (UI/검증/직렬화 동기화 보장)
        self.type_combo = QComboBox()
        for event_type in EVENT_TYPES:
            self.type_combo.addItem(tr(f"event.types.{event_type}"), event_type)
        form.addRow(tr("event.type") + ":", self.type_combo)

        # Date
        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(4)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(YEAR_MIN, YEAR_MAX)
        self.year_spin.setSpecialValueText("-")
        self.year_spin.setValue(YEAR_MIN)
        date_layout.addWidget(self.year_spin)
        date_layout.addWidget(QLabel(tr("label.year")))

        self.month_spin = QSpinBox()
        self.month_spin.setRange(MONTH_MIN, MONTH_MAX)
        self.month_spin.setSpecialValueText("-")
        date_layout.addWidget(self.month_spin)
        date_layout.addWidget(QLabel(tr("label.month")))

        self.day_spin = QSpinBox()
        self.day_spin.setRange(DAY_MIN, DAY_MAX)
        self.day_spin.setSpecialValueText("-")
        date_layout.addWidget(self.day_spin)
        date_layout.addWidget(QLabel(tr("label.day")))

        self.is_lunar_check = QCheckBox(tr("label.lunar"))
        date_layout.addWidget(self.is_lunar_check)

        form.addRow(tr("event.date") + ":", date_widget)

        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText(tr("event.location"))
        self.location_input.setMaxLength(MAX_TEXT_LENGTH)
        form.addRow(tr("event.location") + ":", self.location_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(tr("event.description"))
        self.description_input.setMaximumHeight(120)
        form.addRow(tr("event.description") + ":", self.description_input)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton(tr("button.cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton(tr("button.save"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_event_data(self):
        """Load event data into form."""
        if not self.event:
            return

        self.title_input.setText(self.event.title)
        self.description_input.setPlainText(self.event.description)
        self.location_input.setText(self.event.location)

        # Set event type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.event.event_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Set date
        if self.event.year:
            self.year_spin.setValue(self.event.year)
        if self.event.month:
            self.month_spin.setValue(self.event.month)
        if self.event.day:
            self.day_spin.setValue(self.event.day)
        self.is_lunar_check.setChecked(self.event.is_lunar)

    def _save(self):
        """Validate and save event — delegates to EventValidator."""
        title = self.title_input.text().strip()
        event_type = self.type_combo.currentData() or "other"

        year_val = self.year_spin.value()
        month_val = self.month_spin.value()
        day_val = self.day_spin.value()

        year = year_val if year_val != YEAR_MIN else None
        month = month_val if month_val != MONTH_MIN else None
        day = day_val if day_val != DAY_MIN else None

        is_valid, err = EventValidator.validate_all(
            title=title,
            event_type=event_type,
            year=year,
            month=month,
            day=day,
        )
        if not is_valid:
            self.title_input.setFocus()
            self.title_input.selectAll()
            QMessageBox.warning(
                self,
                tr("error.validation_title"),
                err,
            )
            return

        # Create or update event
        if not self.event:
            self.event = Event()

        self.event.title = title
        self.event.description = self.description_input.toPlainText().strip()
        self.event.event_type = event_type
        self.event.location = self.location_input.text().strip()
        self.event.year = year
        self.event.month = month
        self.event.day = day
        self.event.is_lunar = self.is_lunar_check.isChecked()

        self.accept()

    def get_event(self) -> Optional[Event]:
        """Get the created/edited event."""
        return self.event
