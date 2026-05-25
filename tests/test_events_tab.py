"""EventsTab 위젯 회귀 가드 — set_person/set_editing/refresh/정렬/signal."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.event import Event
from src.models.person import Person


@pytest.fixture
def tab(qapp):
    from src.views.widgets.events_tab import EventsTab
    w = EventsTab()
    yield w
    w.deleteLater()


@pytest.fixture
def person_with_events():
    p = Person(id="p1", name="홍길동")
    p.events = [
        Event(id="e1", title="결혼", event_type="marriage", year=1990, month=5, day=10),
        Event(id="e2", title="졸업", event_type="graduation", year=1985, month=2, day=1),
        Event(id="e3", title="은퇴", event_type="retirement", year=2020, month=12, day=31),
    ]
    return p


class TestStateApi:
    def test_initial_editing_flag_is_false(self, tab):
        # 호스트가 set_editing(True)를 호출하기 전에는 편집 작업 차단
        assert tab._is_editing is False

    def test_set_editing_enables_add_button(self, tab):
        tab.set_editing(True)
        assert tab.add_event_btn.isEnabled() is True

    def test_set_editing_false_disables_again(self, tab):
        tab.set_editing(True)
        tab.set_editing(False)
        assert tab.add_event_btn.isEnabled() is False

    def test_set_person_none_renders_empty(self, tab):
        tab.set_person(None)
        # 빈 상태 (person 없음 → no_events 라벨만, CTA 버튼 없음)
        assert tab._list_layout.count() >= 1


class TestEmptyState:
    def test_person_no_events_renders_cta(self, tab):
        p = Person(id="p2", name="빈 이벤트")
        tab.set_person(p)
        # CTA 버튼이 컨테이너로 추가됨 (empty 라벨 + container + stretch)
        from PyQt6.QtWidgets import QPushButton
        # widgets 트리에서 add_first_event 버튼 찾기
        buttons = tab.findChildren(QPushButton)
        # add_event_btn + sort_btn + CTA = 3개 이상
        assert len(buttons) >= 3

    def test_empty_state_cta_disabled_outside_edit(self, tab):
        p = Person(id="p3", name="비편집 모드")
        tab.set_person(p)
        # edit mode가 아니면 CTA는 disabled여야 함
        from PyQt6.QtWidgets import QPushButton
        ctas = [
            b for b in tab.findChildren(QPushButton)
            if b is not tab.add_event_btn and b is not tab.sort_btn
        ]
        # CTA 존재 + 비활성
        assert ctas
        assert all(not b.isEnabled() for b in ctas)


class TestSorting:
    def test_default_sort_ascending(self, tab, person_with_events):
        tab.set_person(person_with_events)
        # ascending: 1985, 1990, 2020 순서. refresh 후 list_layout 자식 위젯 순서로 확인
        # (stretch 제외하면 3개 위젯)
        ordered = []
        for i in range(tab._list_layout.count()):
            w = tab._list_layout.itemAt(i).widget()
            if w:
                # 위젯 내 QLabel 텍스트 중 제목 추출
                from PyQt6.QtWidgets import QLabel
                for lbl in w.findChildren(QLabel):
                    text = lbl.text()
                    if "졸업" in text or "결혼" in text or "은퇴" in text:
                        ordered.append(text)
                        break
        # 최소 3개 — 순서 검증: 졸업(1985) → 결혼(1990) → 은퇴(2020)
        assert len(ordered) >= 3
        assert "졸업" in ordered[0]
        assert "결혼" in ordered[1]
        assert "은퇴" in ordered[2]

    def test_toggle_sort_flips_order_and_label(self, tab, person_with_events):
        tab.set_person(person_with_events)
        original_label = tab.sort_btn.text()
        tab._toggle_sort()
        # 라벨이 바뀌어야 함 (oldest_first ↔ newest_first)
        assert tab.sort_btn.text() != original_label
        # _sort_descending 토글
        assert tab._sort_descending is True

    def test_toggle_sort_renders_descending(self, tab, person_with_events):
        tab.set_person(person_with_events)
        tab._toggle_sort()
        # descending: 은퇴(2020) → 결혼(1990) → 졸업(1985)
        ordered = []
        from PyQt6.QtWidgets import QLabel
        for i in range(tab._list_layout.count()):
            w = tab._list_layout.itemAt(i).widget()
            if w:
                for lbl in w.findChildren(QLabel):
                    text = lbl.text()
                    if "졸업" in text or "결혼" in text or "은퇴" in text:
                        ordered.append(text)
                        break
        assert "은퇴" in ordered[0]
        assert "졸업" in ordered[2]


class TestSignals:
    def test_delete_emits_events_changed(self, tab, person_with_events, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        # 삭제 확인 다이얼로그를 자동으로 Yes로
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes,
        )

        tab.set_person(person_with_events)
        tab.set_editing(True)

        emitted = []
        tab.events_changed.connect(lambda: emitted.append(True))

        target = person_with_events.events[0]
        tab._delete_event(target)

        assert emitted == [True]
        assert target.id not in [e.id for e in person_with_events.events]

    def test_delete_no_emits_when_user_cancels(self, tab, person_with_events, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.No,
        )

        tab.set_person(person_with_events)
        tab.set_editing(True)

        emitted = []
        tab.events_changed.connect(lambda: emitted.append(True))

        before = len(person_with_events.events)
        tab._delete_event(person_with_events.events[0])

        assert emitted == []  # signal 미발행
        assert len(person_with_events.events) == before  # 삭제 안 됨

    def test_delete_ignored_outside_edit_mode(self, tab, person_with_events):
        tab.set_person(person_with_events)
        # set_editing(True) 호출 X — read-only
        before = len(person_with_events.events)
        tab._delete_event(person_with_events.events[0])
        assert len(person_with_events.events) == before  # 변화 없음

    def test_add_ignored_outside_edit_mode(self, tab, person_with_events):
        tab.set_person(person_with_events)
        # _add_event는 _is_editing=False면 즉시 return → dialog 안 뜸
        emitted = []
        tab.events_changed.connect(lambda: emitted.append(True))
        tab._add_event()
        assert emitted == []


class TestLocalizationHook:
    def test_update_ui_texts_refreshes_labels(self, tab, person_with_events):
        tab.set_person(person_with_events)
        # 단순 호출이 예외 없이 끝나는지 — i18n 키 누락 시 KeyError가 났을 것
        tab.update_ui_texts()
        assert tab.add_event_btn.text()  # 비어있지 않음
        assert tab.sort_btn.text()
