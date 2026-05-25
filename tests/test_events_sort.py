"""EventsTab 정렬 토글 회귀 가드.

분리 후 정렬 상태는 events_tab 위젯이 소유. DetailPanel에서 events_tab으로 위임.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QLabel

from src.models.person import Person
from src.models.event import Event
from src.models.family_tree import FamilyTree


@pytest.fixture
def panel_with_events(qapp):
    from src.views.detail_panel import DetailPanel
    panel = DetailPanel()
    tree = FamilyTree()
    person = Person(id="p1", name="홍길동")
    person.events = [
        Event(title="졸업", year=2010, month=3, day=1),
        Event(title="결혼", year=2020, month=6, day=15),
        Event(title="출생", year=1985, month=1, day=20),
    ]
    tree.add_person(person)
    panel.set_person(person, tree)
    yield panel
    panel.deleteLater()


def _event_titles_in_order(panel):
    """events_tab 내부 리스트에서 이벤트 제목을 순서대로 추출."""
    candidates = ("졸업", "결혼", "출생")
    titles = []
    layout = panel.events_tab._list_layout
    for i in range(layout.count()):
        w = layout.itemAt(i).widget()
        if w is None:
            continue
        for child in w.findChildren(QLabel):
            text = child.text()
            for c in candidates:
                if f">{c}<" in text or text.strip() == c:
                    titles.append(c)
                    break
            else:
                continue
            break
    return titles


class TestEventSortToggle:
    def test_default_is_ascending_oldest_first(self, panel_with_events):
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["출생", "졸업", "결혼"]
        # events_tab의 sort_btn 라벨
        btn_text = panel_with_events.events_tab.sort_btn.text()
        assert "↑" in btn_text or "Oldest" in btn_text or "오래된" in btn_text

    def test_toggle_reverses_order(self, panel_with_events):
        panel_with_events.events_tab._toggle_sort()
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["결혼", "졸업", "출생"]

    def test_toggle_updates_button_label(self, panel_with_events):
        before = panel_with_events.events_tab.sort_btn.text()
        panel_with_events.events_tab._toggle_sort()
        after = panel_with_events.events_tab.sort_btn.text()
        assert before != after
        panel_with_events.events_tab._toggle_sort()
        assert panel_with_events.events_tab.sort_btn.text() == before

    def test_toggle_persists_through_refresh(self, panel_with_events):
        panel_with_events.events_tab._toggle_sort()
        panel_with_events.events_tab.refresh()
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["결혼", "졸업", "출생"]

    def test_initial_state_descending_flag(self, panel_with_events):
        # _sort_descending는 EventsTab 내부 attribute
        assert panel_with_events.events_tab._sort_descending is False
