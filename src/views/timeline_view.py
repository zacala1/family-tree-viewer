"""Timeline view for displaying events chronologically."""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models.person import Person
from ..models.event import Event
from ..models.family_tree import FamilyTree
from ..utils.theme_manager import get_theme_manager
from ..i18n import tr
from .detail_panel import sanitize_html


class TimelineItem(QFrame):
    """Visual representation of a single event on the timeline."""

    event_clicked = pyqtSignal(str)  # event_id

    def __init__(self, event: Event, person_name: str = "", parent=None):
        super().__init__(parent)
        self.event = event
        self.person_name = person_name

        self.setObjectName("timelineItem")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        colors = get_theme_manager().get_tree_colors()

        # Date
        date_label = QLabel(f"<b>{sanitize_html(self.event.date_str)}</b>")
        date_label.setStyleSheet(f"color: {colors['accent_secondary']}; font-size: 14px;")
        layout.addWidget(date_label)

        # Title and Type
        title_layout = QHBoxLayout()
        title_label = QLabel(f"<b>{sanitize_html(self.event.title)}</b>")
        title_label.setStyleSheet("font-size: 16px;")
        title_layout.addWidget(title_label)

        type_label = QLabel(f"[{sanitize_html(self.event.event_type)}]")
        type_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
        title_layout.addWidget(type_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Person name (if provided)
        if self.person_name:
            person_label = QLabel(f"👤 {sanitize_html(self.person_name)}")
            person_label.setStyleSheet(f"color: {colors['text_body']}; font-size: 13px;")
            layout.addWidget(person_label)

        # Description
        if self.event.description:
            desc_label = QLabel(sanitize_html(self.event.description))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {colors['text_body']}; font-size: 13px;")
            layout.addWidget(desc_label)

        # Location
        if self.event.location:
            location_label = QLabel(f"📍 {sanitize_html(self.event.location)}")
            location_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
            layout.addWidget(location_label)

    def mousePressEvent(self, event):
        """Handle mouse click."""
        self.event_clicked.emit(self.event.id)
        super().mousePressEvent(event)


class TimelineView(QWidget):
    """Timeline view widget for displaying events chronologically."""

    event_selected = pyqtSignal(str, str)  # person_id, event_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.family_tree: Optional[FamilyTree] = None
        self.current_person: Optional[Person] = None
        self._timeline_items: List[TimelineItem] = []

        self._setup_ui()

        # Theme change support
        get_theme_manager().theme_changed.connect(lambda _: self._on_theme_changed())

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        colors = get_theme_manager().get_tree_colors()

        # Header
        header = QFrame()
        header.setObjectName("timelineHeader")
        header_layout = QHBoxLayout(header)

        self.header_label = QLabel("📅 " + tr("view.timeline"))
        self.header_label.setStyleSheet(f"color: {colors['header_text']}; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.header_label)

        header_layout.addStretch()

        # View mode toggle
        self.show_all_btn = QPushButton(tr("button.show_all_events"))
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.clicked.connect(self._toggle_view_mode)
        header_layout.addWidget(self.show_all_btn)

        layout.addWidget(header)

        # Scroll area for timeline
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {colors['scroll_bg']}; }}")

        # Timeline container
        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(16, 16, 16, 16)
        self.timeline_layout.setSpacing(8)
        self.timeline_layout.addStretch()

        self.scroll.setWidget(self.timeline_container)
        layout.addWidget(self.scroll)

    def _on_theme_changed(self):
        """Update colors when theme changes."""
        colors = get_theme_manager().get_tree_colors()
        self.header_label.setStyleSheet(f"color: {colors['header_text']}; font-size: 18px; font-weight: bold;")
        self.scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {colors['scroll_bg']}; }}")
        self.refresh()

    def set_family_tree(self, family_tree: FamilyTree):
        """Set the family tree data source."""
        self.family_tree = family_tree
        self.refresh()

    def set_person(self, person: Person):
        """Set the current person and show their timeline."""
        self.current_person = person
        self.refresh()

    def _toggle_view_mode(self):
        """Toggle between showing current person only and all family events."""
        self.refresh()

    def refresh(self):
        """Refresh the timeline display."""
        # Clear all widgets from layout (single pass, no double-delete)
        self._timeline_items.clear()
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not self.family_tree:
            self.timeline_layout.addStretch()
            return

        # Collect events
        events_with_person = []

        if self.show_all_btn.isChecked():
            # Show all family events
            for person in self.family_tree.get_all_persons():
                for event in person.events:
                    events_with_person.append((event, person))
        elif self.current_person:
            # Show only current person's events
            for event in self.current_person.events:
                events_with_person.append((event, self.current_person))

        # Sort by date
        def get_sort_key(item):
            event, _ = item
            return (
                event.year or 9999,
                event.month or 12,
                event.day or 31,
            )

        events_with_person.sort(key=get_sort_key)

        # Create timeline items
        for event, person in events_with_person:
            person_name = person.name if self.show_all_btn.isChecked() else ""
            item = TimelineItem(event, person_name)
            item.event_clicked.connect(lambda eid, pid=person.id: self.event_selected.emit(pid, eid))
            self._timeline_items.append(item)
            self.timeline_layout.addWidget(item)

        if not events_with_person:
            # Show empty message
            colors = get_theme_manager().get_tree_colors()
            empty_label = QLabel(tr("message.no_events"))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 16px; padding: 40px;")
            self.timeline_layout.addWidget(empty_label)

        self.timeline_layout.addStretch()

    def update_ui_texts(self):
        """Update UI texts for language change."""
        self.header_label.setText("📅 " + tr("view.timeline"))
        self.show_all_btn.setText(tr("button.show_all_events"))
        self.refresh()
