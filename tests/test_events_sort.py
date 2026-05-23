"""이벤트 목록 정렬 토글 회귀 가드."""
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
    """3개 이벤트가 있는 인물을 detail_panel에 로드."""
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


def _event_titles_in_order(panel) -> list:
    """events_list_layout에서 이벤트 위젯의 제목을 순서대로 추출.

    title_label은 <b>제목</b> HTML 포함 — substring으로 검출.
    """
    candidates = ("졸업", "결혼", "출생")
    titles = []
    for i in range(panel.events_list_layout.count()):
        w = panel.events_list_layout.itemAt(i).widget()
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
        """기본 정렬은 오래된 → 최근."""
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["출생", "졸업", "결혼"]
        # 버튼 라벨도 오래된 순 표시
        assert "↑" in panel_with_events.events_sort_btn.text() or "Oldest" in panel_with_events.events_sort_btn.text() or "오래된" in panel_with_events.events_sort_btn.text()

    def test_toggle_reverses_order(self, panel_with_events):
        panel_with_events._toggle_events_sort()
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["결혼", "졸업", "출생"]

    def test_toggle_updates_button_label(self, panel_with_events):
        before = panel_with_events.events_sort_btn.text()
        panel_with_events._toggle_events_sort()
        after = panel_with_events.events_sort_btn.text()
        assert before != after
        # 두 번째 클릭 → 원상 복귀
        panel_with_events._toggle_events_sort()
        assert panel_with_events.events_sort_btn.text() == before

    def test_toggle_persists_through_refresh(self, panel_with_events):
        """정렬 방향을 바꾼 뒤 _refresh_events_list 재호출에서도 유지."""
        panel_with_events._toggle_events_sort()
        panel_with_events._refresh_events_list()
        titles = _event_titles_in_order(panel_with_events)
        assert titles == ["결혼", "졸업", "출생"]

    def test_initial_state_descending_flag(self, panel_with_events):
        """내부 플래그가 명시적으로 False (오름차순)로 시작."""
        assert panel_with_events._events_sort_descending is False
