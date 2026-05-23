"""상태바 영구 카운트 회귀 가드.

count_label(구성원)과 rel_count_label(관계) 두 라벨이
- 항상 statusbar에 영구 위젯으로 표시되고
- _update_person_list 후 정확한 값을 반영하는지 검증.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person


@pytest.fixture
def main_window(qapp):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


class TestStatusCounts:
    def test_initial_counts_zero(self, main_window):
        assert "0" in main_window.count_label.text()
        assert "0" in main_window.rel_count_label.text()

    def test_member_count_updates(self, main_window):
        main_window.family_tree.add_person(Person(id="p1", name="A"))
        main_window.family_tree.add_person(Person(id="p2", name="B"))
        main_window._update_person_list()
        assert "2" in main_window.count_label.text()

    def test_relationship_count_updates(self, main_window):
        main_window.family_tree.add_person(Person(id="h", name="H"))
        main_window.family_tree.add_person(Person(id="w", name="W"))
        main_window.family_tree.set_spouse("h", "w")
        main_window._update_person_list()
        assert "1" in main_window.rel_count_label.text()

    def test_counts_decrease_on_delete(self, main_window):
        main_window.family_tree.add_person(Person(id="p1", name="A"))
        main_window.family_tree.add_person(Person(id="p2", name="B"))
        main_window._update_person_list()
        assert "2" in main_window.count_label.text()

        main_window.family_tree.remove_person("p1")
        main_window._update_person_list()
        assert "1" in main_window.count_label.text()

    def test_both_labels_in_statusbar(self, main_window):
        """두 카운트 라벨이 모두 영구 위젯으로 등록됐는지."""
        # QStatusBar.children에 두 라벨 모두 포함
        children = main_window.statusbar.children()
        assert main_window.count_label in children
        assert main_window.rel_count_label in children
