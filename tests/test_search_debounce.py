"""SearchPanel 디바운스 + Esc 클리어 회귀 가드.

이전엔 main_window 내부 _search_debounce_timer를 직접 검증했지만, 분리 후엔
SearchPanel 위젯이 자체 디바운스를 갖고 main_window는 filters_changed signal만 받음.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from src.utils.search_index import PersonSearchIndex


@pytest.fixture
def panel(qapp):
    from src.views.widgets.search_panel import SearchPanel
    idx = PersonSearchIndex()
    p = SearchPanel(idx)
    yield p
    p.deleteLater()


class TestSearchDebounce:
    def test_debounce_timer_configured(self, panel):
        assert panel._debounce.isSingleShot() is True
        assert panel._debounce.interval() == panel.DEBOUNCE_MS

    def test_typing_does_not_emit_immediately(self, panel):
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel.search_input.setText("홍")
        # 디바운스 안 기다림 → 0회
        assert emitted == []
        # 타이머 활성
        assert panel._debounce.isActive()

    def test_consecutive_input_keeps_timer_pending(self, panel):
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel.search_input.setText("홍")
        panel.search_input.setText("홍길")
        panel.search_input.setText("홍길동")
        assert emitted == []
        assert panel._debounce.isActive()

    def test_enter_key_triggers_immediately(self, panel):
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel.search_input.setText("홍")
        panel.search_input.returnPressed.emit()
        assert emitted == [1]

    def test_timer_timeout_emits_filters_changed(self, panel):
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel._debounce.timeout.emit()
        assert emitted == [1]


class TestClearSearch:
    def test_clear_empties_input_and_emits(self, panel):
        panel.search_input.setText("홍")
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel.clear_search()
        assert panel.search_input.text() == ""
        assert emitted == [1]
        assert not panel._debounce.isActive()

    def test_clear_noop_on_empty(self, panel):
        panel.search_input.setText("")
        emitted = []
        panel.filters_changed.connect(lambda: emitted.append(1))
        panel.clear_search()
        assert emitted == []  # noop

    def test_esc_shortcut_bound_to_search_input(self, panel):
        sc = panel._esc_shortcut
        assert sc.key() == QKeySequence("Esc")
        assert sc.context() == Qt.ShortcutContext.WidgetShortcut


class TestMainWindowIntegration:
    def test_main_window_has_search_panel(self, qapp):
        from src.views.main_window import MainWindow
        from src.views.widgets.search_panel import SearchPanel
        win = MainWindow()
        try:
            assert isinstance(win.search_panel, SearchPanel)
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()

    def test_filters_changed_triggers_list_update(self, qapp):
        from src.views.main_window import MainWindow
        from src.models.person import Person
        win = MainWindow()
        try:
            win.family_tree.add_person(Person(id="p1", name="홍길동"))
            win._update_person_list()
            # 검색어 입력 → returnPressed → 즉시 emit → _update_person_list 호출
            win.search_panel.search_input.setText("홍")
            win.search_panel.search_input.returnPressed.emit()
            # status_label에 검색 결과 메시지
            text = win.status_label.text()
            assert "1" in text or "홍" in text
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()
