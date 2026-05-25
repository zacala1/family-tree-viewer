"""이벤트 탭 위젯.

detail_panel에서 분리. 인물의 events 목록 표시 + add/edit/delete + 정렬 토글
+ 빈 상태 CTA. 변경 발생 시 events_changed signal로 host에 알려 deepcopy 발행.
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...models.event import Event
from ...models.person import Person
from ...i18n import tr
from ...utils.theme_manager import get_theme_manager
from ..event_dialog import EventDialog


def _sanitize(text: str, limit: int = 1000) -> str:
    import html as _html
    if not text:
        return ""
    return _html.escape(str(text))[:limit]


class EventsTab(QWidget):
    """인물 events 표시·편집 탭.

    Signals:
        events_changed(): events 리스트가 변경됨 — host가 _emit_person_copy 등 후처리.
    """

    events_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._person: Optional[Person] = None
        self._is_editing: bool = False
        self._sort_descending: bool = False
        # 빠른 더블 클릭으로 EventDialog가 두 번 열리는 race 가드.
        # _add_event / _edit_event 모두 single-shot 유지.
        self._dialog_open: bool = False
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 12, 8, 8)

        # events 목록 (스크롤 영역)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._list_widget)
        outer.addWidget(scroll)

        # 하단 버튼 row — Add + Sort toggle
        btn_row = QHBoxLayout()
        self.add_event_btn = QPushButton(tr("button.add_event"))
        self.add_event_btn.clicked.connect(self._add_event)
        btn_row.addWidget(self.add_event_btn)
        btn_row.addStretch()

        self.sort_btn = QPushButton(tr("button.sort_oldest_first"))
        self.sort_btn.setObjectName("eventsSortBtn")
        self.sort_btn.setToolTip(tr("tooltip.toggle_event_sort"))
        self.sort_btn.setAccessibleName(tr("tooltip.toggle_event_sort"))
        self.sort_btn.clicked.connect(self._toggle_sort)
        btn_row.addWidget(self.sort_btn)
        outer.addLayout(btn_row)

    # === Public API ===

    def set_person(self, person: Optional[Person]):
        """표시할 person 설정 + 목록 refresh."""
        self._person = person
        self.refresh()

    def set_editing(self, is_editing: bool):
        """edit mode 토글 — add 버튼 활성화 + 빈 상태 CTA 갱신."""
        self._is_editing = is_editing
        self.add_event_btn.setEnabled(is_editing)
        self.refresh()

    def refresh(self):
        """현재 person의 events 다시 렌더링."""
        # 기존 위젯 제거 — Qt 권장 순서: deleteLater 먼저 (pending queue 등록),
        # 그 다음 부모-자식 관계 분리. 반대 순서면 deleteLater 대기 중 dangling
        # parent change가 일부 Qt 빌드에서 경고를 발생시킴.
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
                w.setParent(None)

        if not self._person or not self._person.events:
            self._render_empty_state()
            return

        sorted_events = sorted(
            self._person.events,
            key=lambda e: (e.year or 9999, e.month or 12, e.day or 31),
            reverse=self._sort_descending,
        )
        for event in sorted_events:
            self._list_layout.addWidget(self._create_event_widget(event))
        self._list_layout.addStretch()

    def update_ui_texts(self):
        """언어 변경 시 — 버튼 라벨 + 툴팁 + 정렬 방향 라벨."""
        self.add_event_btn.setText(tr("button.add_event"))
        self.sort_btn.setText(
            tr("button.sort_newest_first") if self._sort_descending
            else tr("button.sort_oldest_first")
        )
        self.sort_btn.setToolTip(tr("tooltip.toggle_event_sort"))
        self.refresh()  # 빈 상태 CTA 텍스트도 재번역

    # === Internal handlers ===

    def _add_event(self):
        if not self._person or not self._is_editing or self._dialog_open:
            return
        self._dialog_open = True
        try:
            dlg = EventDialog(parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                event = dlg.get_event()
                if event:
                    event.person_id = self._person.id
                    self._person.events.append(event)
                    self.refresh()
                    self.events_changed.emit()
        finally:
            self._dialog_open = False

    def _edit_event(self, event: Event):
        if not self._person or not self._is_editing or self._dialog_open:
            return
        self._dialog_open = True
        try:
            dlg = EventDialog(event=event, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
                self.events_changed.emit()
        finally:
            self._dialog_open = False

    def _delete_event(self, event: Event):
        if not self._person or not self._is_editing:
            return
        reply = QMessageBox.question(
            self,
            tr("button.delete_event"),
            f"{tr('button.delete_event')}: {event.title}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._person.events = [e for e in self._person.events if e.id != event.id]
            self.refresh()
            self.events_changed.emit()

    def _toggle_sort(self):
        self._sort_descending = not self._sort_descending
        self.sort_btn.setText(
            tr("button.sort_newest_first") if self._sort_descending
            else tr("button.sort_oldest_first")
        )
        self.refresh()

    # === 렌더링 ===

    def _render_empty_state(self):
        empty = QLabel(tr("message.no_events"))
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colors = get_theme_manager().get_tree_colors()
        empty.setStyleSheet(
            f"color: {colors['text_muted']}; padding: 20px 20px 8px 20px;"
        )
        self._list_layout.addWidget(empty)

        if self._person:
            cta = QPushButton("+  " + tr("button.add_first_event"))
            cta.setEnabled(self._is_editing)
            if not self._is_editing:
                cta.setToolTip(tr("tooltip.enter_edit_mode_first"))
            cta.clicked.connect(self._add_event)
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addStretch()
            row.addWidget(cta)
            row.addStretch()
            container = QWidget()
            container.setLayout(row)
            self._list_layout.addWidget(container)

        self._list_layout.addStretch()

    def _create_event_widget(self, event: Event) -> QWidget:
        widget = QFrame()
        widget.setObjectName("eventItem")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 제목 + 타입
        title_row = QHBoxLayout()
        title_label = QLabel(f"<b>{_sanitize(event.title)}</b>")
        title_row.addWidget(title_label)
        colors = get_theme_manager().get_tree_colors()
        type_label = QLabel(f"[{tr(f'event.types.{event.event_type}')}]")
        type_label.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
        title_row.addWidget(type_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        if event.date_str:
            date_label = QLabel(f"📅 {event.date_str}")
            date_label.setStyleSheet(f"color: {colors['accent']}; font-size: 13px;")
            layout.addWidget(date_label)

        if event.location:
            loc = QLabel(f"📍 {_sanitize(event.location)}")
            loc.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px;")
            layout.addWidget(loc)

        if event.description:
            desc = QLabel(_sanitize(event.description))
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {colors['text_body']}; font-size: 13px;")
            layout.addWidget(desc)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        edit_btn = QPushButton(tr("button.edit_event"))
        # event를 default arg로 명시 캡처 — late-binding 함정 회피.
        # checked는 QPushButton.clicked가 전달하는 bool (무시).
        edit_btn.clicked.connect(lambda checked=False, e=event: self._edit_event(e))
        btn_row.addWidget(edit_btn)
        del_btn = QPushButton(tr("button.delete_event"))
        del_btn.clicked.connect(lambda checked=False, e=event: self._delete_event(e))
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        return widget
