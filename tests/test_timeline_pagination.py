"""TimelineView 페이지네이션 회귀 가드.

PAGE_SIZE 초과 시:
- 한 페이지에 최대 PAGE_SIZE개 위젯만 인스턴스화
- 페이지네이션 strip 자동 노출
- prev/next 페이지 전환 정확
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.event import Event
from src.models.family_tree import FamilyTree


@pytest.fixture
def timeline(qapp):
    from src.views.timeline_view import TimelineView
    t = TimelineView()
    yield t
    t.deleteLater()


def _person_with_events(n: int) -> Person:
    """n개의 이벤트를 가진 인물 생성 (각 다른 연도)."""
    person = Person(id="p1", name="홍길동")
    for i in range(n):
        person.events.append(Event(title=f"E{i}", year=2000 + i))
    return person


class TestPaginationStripVisibility:
    def test_strip_hidden_when_few_events(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(50)  # PAGE_SIZE(100) 이하
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        assert timeline.pagination_frame.isHidden() is True

    def test_strip_visible_when_many_events(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        assert timeline.pagination_frame.isHidden() is False
        # 250 / 100 = 3 페이지
        assert timeline.page_label.text() == "1 / 3"

    def test_strip_hidden_for_empty(self, timeline):
        tree = FamilyTree()
        timeline.set_family_tree(tree)
        assert timeline.pagination_frame.isHidden() is True


class TestPagination:
    def test_initial_page_first(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        assert timeline._current_page == 0

    def test_next_page_advances(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        timeline._next_page()
        assert timeline._current_page == 1
        assert timeline.page_label.text() == "2 / 3"

    def test_next_page_stops_at_last(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        timeline._next_page()
        timeline._next_page()  # last page
        timeline._next_page()  # 더 이상 안 감
        assert timeline._current_page == 2
        assert timeline.next_page_btn.isEnabled() is False

    def test_prev_page_stops_at_first(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        timeline._prev_page()  # 이미 0
        assert timeline._current_page == 0
        assert timeline.prev_page_btn.isEnabled() is False

    def test_page_size_widgets_rendered(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        # 첫 페이지는 100개 widget
        assert len(timeline._timeline_items) == timeline.PAGE_SIZE

    def test_last_page_renders_remainder(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        timeline._next_page()
        timeline._next_page()  # 마지막 페이지 (50개)
        assert len(timeline._timeline_items) == 50

    def test_view_mode_toggle_resets_page(self, timeline):
        tree = FamilyTree()
        person = _person_with_events(250)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        timeline._next_page()
        assert timeline._current_page == 1
        # show_all 토글 → 첫 페이지로 리셋
        timeline.show_all_btn.setChecked(True)
        timeline._toggle_view_mode()
        assert timeline._current_page == 0


class TestPagePerformance:
    def test_10k_events_only_pagesize_widgets(self, timeline):
        """10K 이벤트라도 첫 페이지엔 PAGE_SIZE개만 인스턴스화."""
        tree = FamilyTree()
        person = _person_with_events(10000)
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        # 10K개 위젯 인스턴스화하지 않음
        assert len(timeline._timeline_items) == timeline.PAGE_SIZE
        assert len(timeline._all_events) == 10000
        assert timeline._total_pages() == 100


class TestEmptyState:
    def test_empty_shows_no_events_message(self, timeline):
        tree = FamilyTree()
        person = Person(id="p", name="A")
        tree.add_person(person)
        timeline.set_family_tree(tree)
        timeline.set_person(person)
        # 위젯 0개, 페이지네이션 숨김
        assert len(timeline._timeline_items) == 0
        assert timeline.pagination_frame.isHidden() is True
