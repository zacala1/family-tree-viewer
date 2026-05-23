"""좌측 인물 목록의 빈 상태 안내 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QLabel

from src.models.person import Person


@pytest.fixture
def main_window(qapp):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


def _find_hint_label(layout) -> QLabel:
    """person_list_layout에서 빈 상태 안내 QLabel 찾기."""
    for i in range(layout.count()):
        w = layout.itemAt(i).widget()
        if isinstance(w, QLabel) and w.objectName() == "personListEmptyHint":
            return w
    return None


class TestEmptyListHint:
    def test_empty_tree_shows_no_members_hint(self, main_window):
        """빈 트리 → '구성원 없음 + 추가하세요' 안내."""
        main_window._update_person_list()
        label = _find_hint_label(main_window.person_list_layout)
        assert label is not None
        # 한글 또는 영문 키워드 — 정확한 문자열 대신 키워드 부분 일치로
        text = label.text()
        assert any(k in text for k in ("구성원", "members", "Member"))

    def test_no_search_results_shows_no_match_hint(self, main_window):
        """트리에 데이터 있지만 검색에 안 걸리면 '결과 없음 + 다시 시도' 안내."""
        main_window.family_tree.add_person(Person(id="p1", name="홍길동"))
        main_window.search_input.setText("ZZZZZ존재하지않는이름")
        main_window._on_search()
        label = _find_hint_label(main_window.person_list_layout)
        assert label is not None
        text = label.text()
        assert any(k in text for k in ("결과", "match", "results"))

    def test_populated_tree_no_hint(self, main_window):
        """데이터가 있고 검색 없으면 안내 없음."""
        main_window.family_tree.add_person(Person(id="p1", name="홍길동"))
        main_window._update_person_list()
        label = _find_hint_label(main_window.person_list_layout)
        assert label is None

    def test_hint_replaced_when_data_added(self, main_window):
        """빈 → 데이터 추가 후 갱신 시 안내 사라짐."""
        main_window._update_person_list()
        assert _find_hint_label(main_window.person_list_layout) is not None

        main_window.family_tree.add_person(Person(id="p1", name="홍길동"))
        main_window._update_person_list()
        assert _find_hint_label(main_window.person_list_layout) is None


class TestHasAdvancedFiltersSet:
    def test_default_state_no_filters(self, main_window):
        assert main_window._has_advanced_filters_set() is False

    def test_gender_filter_detected(self, main_window):
        # 인덱스 1 = male
        main_window.adv_gender_combo.setCurrentIndex(1)
        assert main_window._has_advanced_filters_set() is True

    def test_year_filter_detected(self, main_window):
        main_window.adv_year_from.setValue(1980)
        assert main_window._has_advanced_filters_set() is True

    def test_location_filter_detected(self, main_window):
        main_window.adv_location_input.setText("서울")
        assert main_window._has_advanced_filters_set() is True
