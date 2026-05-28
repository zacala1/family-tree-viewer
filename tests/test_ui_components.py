"""UI 컴포넌트 및 유틸리티 테스트."""

import unittest
import unittest.mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QGridLayout

from src.models.family_tree import FamilyTree
from src.models.person import Person


class TestDetailPanel(unittest.TestCase):
    """상세 패널 테스트."""

    def setUp(self):
        from src.views.detail_panel import DetailPanel
        self.panel = DetailPanel()
        self.tree = FamilyTree()

    def tearDown(self):
        self.panel.close()

    def test_panel_creation(self):
        """패널이 정상적으로 생성되는지 확인."""
        self.assertIsNotNone(self.panel)

    def test_tab_count(self):
        """탭 수 확인 (기본정보, 추가정보, 메모, 관계, 이벤트)."""
        self.assertEqual(self.panel.tabs.count(), 5)

    def test_detail_tabs_are_configured_to_fit_narrow_width(self):
        """좁은 상세 패널에서 탭 버튼이 스크롤 버튼/긴 라벨로 밀리지 않도록 고정."""
        self.assertFalse(self.panel.tabs.usesScrollButtons())
        self.assertFalse(self.panel.tabs.tabBar().expanding())
        self.assertFalse(self.panel.tabs.tabBar().drawBase())
        self.assertEqual(self.panel.tabs.elideMode(), Qt.TextElideMode.ElideRight)

    def test_detail_date_inputs_use_compact_layout(self):
        """생년/사망일 입력은 1024px 폭에서도 잘리지 않도록 compact 폭을 유지."""
        for group in (self.panel.birth_date_group, self.panel.death_date_group):
            with self.subTest(group=group):
                self.assertIsInstance(group.year.parentWidget().layout(), QGridLayout)
                self.assertEqual(group.year.objectName(), "compactDateSpin")
                self.assertEqual(group.month.objectName(), "compactDateSpin")
                self.assertEqual(group.day.objectName(), "compactDateSpin")
                self.assertEqual(group.year.minimumWidth(), 82)
                self.assertEqual(group.year.maximumWidth(), 82)
                self.assertEqual(group.month.minimumWidth(), 56)
                self.assertEqual(group.month.maximumWidth(), 56)
                self.assertEqual(group.day.minimumWidth(), 56)
                self.assertEqual(group.day.maximumWidth(), 56)
                self.assertTrue(group.year_label.isHidden())
                self.assertTrue(group.month_label.isHidden())
                self.assertTrue(group.day_label.isHidden())
                self.assertTrue(group.conversion_label.wordWrap())

    def test_load_person(self):
        """인물 로드 테스트."""
        person = Person(name="홍길동", gender="M", birth_year=1990)
        self.tree.add_person(person)

        self.panel.set_person(person, self.tree)

        self.assertEqual(self.panel.name_input.text(), "홍길동")
        self.assertEqual(self.panel.gender_combo.currentData(), "M")

    def test_edit_mode(self):
        """편집 모드 전환 테스트."""
        person = Person(name="홍길동", gender="M")
        self.tree.add_person(person)
        self.panel.set_person(person, self.tree)

        self.panel.start_edit()
        self.assertTrue(self.panel.name_input.isEnabled())

    def test_clear(self):
        """패널 초기화 테스트."""
        person = Person(name="홍길동", gender="M")
        self.tree.add_person(person)
        self.panel.set_person(person, self.tree)

        self.panel.clear()
        self.assertIsNone(self.panel.current_person)

    def test_extended_relations_display(self):
        """확대 관계 표시 테스트."""
        grandpa = Person(name="할아버지", gender="M")
        father = Person(name="아버지", gender="M")
        child = Person(name="자녀", gender="M")
        for p in [grandpa, father, child]:
            self.tree.add_person(p)
        self.tree.set_parent_child(grandpa.id, father.id)
        self.tree.set_parent_child(father.id, child.id)

        self.panel.set_person(child, self.tree)
        # 관계 탭이 RelationshipsTab 위젯으로 분리됨
        self.assertIn("할아버지", self.panel.rel_tab.grandparents_label.text())

    def test_extended_relations_empty(self):
        """확대 관계가 없는 경우 테스트."""
        person = Person(name="홀로", gender="M")
        self.tree.add_person(person)
        self.panel.set_person(person, self.tree)
        self.assertIn("-", self.panel.rel_tab.grandparents_label.text())

    def test_save_signal(self):
        """저장 시그널 테스트."""
        person = Person(name="홍길동", gender="M")
        self.tree.add_person(person)
        self.panel.set_person(person, self.tree)

        received = []
        self.panel.person_updated.connect(lambda p: received.append(p))

        self.panel.start_edit()
        self.panel.name_input.setText("김철수")
        self.panel._save()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].name, "김철수")


class TestTreeCanvas(unittest.TestCase):
    """트리 캔버스 테스트."""

    def setUp(self):
        from src.views.tree_canvas import TreeCanvas
        self.tree = FamilyTree()
        self.canvas = TreeCanvas(self.tree)

    def tearDown(self):
        self.canvas.close()

    def test_canvas_creation(self):
        """캔버스가 정상적으로 생성되는지 확인."""
        self.assertIsNotNone(self.canvas)
        self.assertGreaterEqual(self.canvas.minimumWidth(), 480)
        self.assertGreaterEqual(self.canvas.minimumHeight(), 350)

    def test_set_family_tree(self):
        """가계도 설정 테스트."""
        new_tree = FamilyTree()
        person = Person(name="홍길동", gender="M")
        new_tree.add_person(person)

        self.canvas.set_family_tree(new_tree)
        self.assertEqual(self.canvas.family_tree, new_tree)

    def test_select_person(self):
        """인물 선택 테스트."""
        person = Person(name="홍길동", gender="M")
        self.tree.add_person(person)
        self.canvas.set_family_tree(self.tree)

        self.canvas.select_person(person.id)
        self.assertEqual(self.canvas.selected_person_id, person.id)

    def test_zoom_direct(self):
        """줌 직접 설정 테스트 (애니메이션 우회)."""
        self.canvas.scale = 2.0
        self.assertAlmostEqual(self.canvas.scale, 2.0)
        self.canvas.scale = 1.0

    def test_initial_scale(self):
        """초기 줌 스케일 테스트."""
        self.assertAlmostEqual(self.canvas.scale, 1.0, places=1)


class TestSearchPanelLayout(unittest.TestCase):
    """검색 패널 compact 레이아웃 회귀 테스트."""

    def setUp(self):
        from src.utils.search_index import PersonSearchIndex
        from src.views.widgets.search_panel import SearchPanel

        self.panel = SearchPanel(PersonSearchIndex())

    def tearDown(self):
        self.panel.close()

    def test_advanced_year_range_uses_compact_spinboxes(self):
        """고급 검색 연도 범위가 좁은 사이드바에서 라벨/입력 겹침 없이 유지."""
        self.assertEqual(self.panel.adv_year_from.objectName(), "compactSearchSpin")
        self.assertEqual(self.panel.adv_year_to.objectName(), "compactSearchSpin")
        self.assertEqual(self.panel.adv_year_from.minimumWidth(), 82)
        self.assertEqual(self.panel.adv_year_from.maximumWidth(), 82)
        self.assertEqual(self.panel.adv_year_to.minimumWidth(), 82)
        self.assertEqual(self.panel.adv_year_to.maximumWidth(), 82)
        self.assertGreaterEqual(self.panel._year_label.sizeHint().width(), 1)


class TestDuplicateDetector(unittest.TestCase):
    """중복 인물 감지 테스트."""

    def test_normalize_name(self):
        """이름 정규화 테스트."""
        from src.utils.duplicate_detector import normalize_name
        self.assertEqual(normalize_name("홍 길 동"), "홍길동")
        self.assertEqual(normalize_name("  Hong GilDong  "), "honggildong")

    def test_levenshtein_distance(self):
        """레벤슈타인 거리 테스트."""
        from src.utils.duplicate_detector import levenshtein_distance
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("abc", "abc"), 0)
        self.assertEqual(levenshtein_distance("", "abc"), 3)

    def test_find_similar_persons(self):
        """유사 인물 찾기 테스트."""
        from src.utils.duplicate_detector import find_similar_persons
        persons = [
            Person(name="홍길동", gender="M"),
            Person(name="홍길순", gender="F"),
            Person(name="김철수", gender="M"),
        ]
        results = find_similar_persons("홍길동", persons, threshold=2)
        names = [p.name for p, dist in results]
        self.assertIn("홍길동", names)
        self.assertIn("홍길순", names)
        self.assertNotIn("김철수", names)

    def test_exclude_id(self):
        """제외 ID 테스트."""
        from src.utils.duplicate_detector import find_similar_persons
        person = Person(name="홍길동", gender="M")
        results = find_similar_persons("홍길동", [person], threshold=0, exclude_id=person.id)
        self.assertEqual(len(results), 0)

    def test_empty_name(self):
        """빈 이름 테스트."""
        from src.utils.duplicate_detector import find_similar_persons
        persons = [Person(name="홍길동", gender="M")]
        results = find_similar_persons("", persons, threshold=2)
        self.assertEqual(len(results), 0)


class TestPdfExporter(unittest.TestCase):
    """PDF 내보내기 유틸리티 테스트."""

    def test_is_available(self):
        """PDF 내보내기 가능 여부 확인."""
        from src.utils.pdf_exporter import PdfExporter
        # QPrinter is available in this test environment
        self.assertTrue(PdfExporter.is_available())

    def test_bounding_rect_empty(self):
        """빈 캔버스의 바운딩박스 테스트."""
        from src.utils.pdf_exporter import PdfExporter
        from src.views.tree_canvas import TreeCanvas
        tree = FamilyTree()
        canvas = TreeCanvas(tree)
        rect = PdfExporter._get_bounding_rect(canvas)
        self.assertTrue(rect.isEmpty())
        canvas.close()


class TestFileHandlerLastError(unittest.TestCase):
    """FileHandler _last_error 메커니즘 테스트."""

    def test_get_last_error_initial(self):
        """초기 에러 메시지 확인."""
        from src.utils.file_handler import FileHandler
        # Reset for test isolation
        FileHandler._last_error = ""
        self.assertEqual(FileHandler.get_last_error(), "")

    def test_set_error(self):
        """에러 설정 테스트."""
        from src.utils.file_handler import FileHandler
        FileHandler._set_error("test error message")
        self.assertEqual(FileHandler.get_last_error(), "test error message")
        FileHandler._last_error = ""  # cleanup

    def test_load_nonexistent_sets_error(self):
        """존재하지 않는 파일 로드 시 에러 설정 확인."""
        from src.utils.file_handler import FileHandler
        FileHandler._last_error = ""
        result = FileHandler.load_json("/nonexistent/path/file.json")
        self.assertIsNone(result)
        self.assertIn("not found", FileHandler.get_last_error().lower())

    def test_save_filters_include_gedcom(self):
        """저장 필터에 GEDCOM 포함 확인."""
        from src.utils.file_handler import FileHandler
        filters = FileHandler.get_save_filters()
        self.assertIn("ged", filters.lower())


if __name__ == '__main__':
    unittest.main()
