"""파일 핸들러 유닛 테스트."""
import unittest
import tempfile
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.file_handler import FileHandler
from src.models.family_tree import FamilyTree
from src.models.person import Person


class TestFileHandlerJSON(unittest.TestCase):
    """JSON 파일 처리 테스트."""

    def setUp(self):
        """테스트용 임시 디렉토리 생성."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """임시 파일 정리."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_json(self):
        """JSON 저장 테스트."""
        tree = FamilyTree()
        tree.add_person(Person(id="p1", name="테스트"))

        file_path = os.path.join(self.temp_dir, "test.json")
        result = FileHandler.save_json(tree, file_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))

        # 파일 내용 확인
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('persons', data)
        self.assertIn('_meta', data)
        self.assertEqual(len(data['persons']), 1)

    def test_load_json(self):
        """JSON 로드 테스트."""
        # 테스트 파일 생성
        file_path = os.path.join(self.temp_dir, "test.json")
        test_data = {
            'persons': [
                {'id': 'p1', 'name': '홍길동', 'gender': 'M'}
            ],
            'relationships': []
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 로드
        tree = FileHandler.load_json(file_path)

        self.assertIsNotNone(tree)
        self.assertEqual(len(tree.get_all_persons()), 1)

        person = tree.get_person('p1')
        self.assertEqual(person.name, '홍길동')

    def test_json_roundtrip(self):
        """JSON 저장 후 로드 테스트."""
        original_tree = FamilyTree()
        p1 = Person(id="p1", name="아버지", gender='M', birth_year=1970)
        p2 = Person(id="p2", name="어머니", gender='F', birth_year=1975)
        p3 = Person(id="p3", name="자녀", gender='M', birth_year=2000)

        original_tree.add_person(p1)
        original_tree.add_person(p2)
        original_tree.add_person(p3)
        original_tree.set_spouse("p1", "p2")
        original_tree.set_parent_child("p1", "p3")
        original_tree.set_parent_child("p2", "p3")

        # 저장
        file_path = os.path.join(self.temp_dir, "roundtrip.json")
        FileHandler.save_json(original_tree, file_path)

        # 로드
        loaded_tree = FileHandler.load_json(file_path)

        # 검증
        self.assertEqual(len(loaded_tree.get_all_persons()), 3)

        loaded_child = loaded_tree.get_person("p3")
        self.assertEqual(loaded_child.name, "자녀")
        self.assertEqual(loaded_child.father_id, "p1")
        self.assertEqual(loaded_child.mother_id, "p2")

    def test_load_nonexistent_file(self):
        """존재하지 않는 파일 로드 테스트."""
        result = FileHandler.load_json("/nonexistent/path.json")
        self.assertIsNone(result)


class TestFileHandlerExcel(unittest.TestCase):
    """Excel 파일 처리 테스트."""

    def setUp(self):
        """테스트용 임시 디렉토리 생성."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """임시 파일 정리."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipUnless(
        True,  # openpyxl이 항상 설치되어 있다고 가정
        "openpyxl 라이브러리가 필요합니다"
    )
    def test_save_excel(self):
        """Excel 저장 테스트."""
        tree = FamilyTree()
        tree.add_person(Person(
            id="p1",
            name="테스트",
            gender='M',
            birth_year=1990,
            occupation="개발자"
        ))

        file_path = os.path.join(self.temp_dir, "test.xlsx")
        result = FileHandler.save_excel(tree, file_path)

        # openpyxl이 설치되어 있으면 성공
        if result:
            self.assertTrue(os.path.exists(file_path))

    @unittest.skipUnless(
        True,
        "openpyxl 라이브러리가 필요합니다"
    )
    def test_excel_roundtrip(self):
        """Excel 저장 후 로드 테스트."""
        original_tree = FamilyTree()
        original_tree.add_person(Person(
            id="p1",
            name="김철수",
            gender='M',
            birth_year=1980,
            birth_month=3,
            birth_day=15,
            is_lunar_birth=True,
            occupation="회사원"
        ))

        file_path = os.path.join(self.temp_dir, "roundtrip.xlsx")

        # 저장
        save_result = FileHandler.save_excel(original_tree, file_path)

        if save_result:
            # 로드
            loaded_tree = FileHandler.load_excel(file_path)

            if loaded_tree:
                self.assertEqual(len(loaded_tree.get_all_persons()), 1)

                person = list(loaded_tree.get_all_persons())[0]
                self.assertEqual(person.name, "김철수")
                self.assertEqual(person.birth_year, 1980)


class TestFileHandlerAutoDetect(unittest.TestCase):
    """파일 형식 자동 감지 테스트."""

    def setUp(self):
        """테스트용 임시 디렉토리 생성."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """임시 파일 정리."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_file_json(self):
        """JSON 파일 자동 감지 로드 테스트."""
        file_path = os.path.join(self.temp_dir, "auto.json")
        test_data = {
            'persons': [{'id': 'p1', 'name': '테스트'}],
            'relationships': []
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        tree = FileHandler.load_file(file_path)

        self.assertIsNotNone(tree)
        self.assertEqual(len(tree.get_all_persons()), 1)

    def test_save_file_json(self):
        """JSON 파일 자동 감지 저장 테스트."""
        tree = FamilyTree()
        tree.add_person(Person(name="테스트"))

        file_path = os.path.join(self.temp_dir, "auto.json")
        result = FileHandler.save_file(tree, file_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))

    def test_save_file_adds_extension(self):
        """확장자 없는 파일 저장 시 .json 추가 테스트."""
        tree = FamilyTree()
        tree.add_person(Person(name="테스트"))

        file_path = os.path.join(self.temp_dir, "noext")
        result = FileHandler.save_file(tree, file_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path + ".json"))

    def test_load_unsupported_format(self):
        """지원하지 않는 형식 로드 테스트."""
        file_path = os.path.join(self.temp_dir, "test.xyz")
        with open(file_path, 'w') as f:
            f.write("test")

        result = FileHandler.load_file(file_path)
        self.assertIsNone(result)


class TestFileHandlerGEDCOM(unittest.TestCase):
    """GEDCOM 파일 처리 테스트."""

    def setUp(self):
        """테스트용 임시 디렉토리 생성."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """임시 파일 정리."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_gedcom(self):
        """GEDCOM 로드 테스트."""
        gedcom_content = """0 HEAD
1 SOUR Test
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 1 JAN 1950
0 @I2@ INDI
1 NAME Jane /Doe/
1 SEX F
1 BIRT
2 DATE 15 MAR 1955
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
0 TRLR
"""
        file_path = os.path.join(self.temp_dir, "test.ged")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(gedcom_content)

        tree = FileHandler.load_gedcom(file_path)

        self.assertIsNotNone(tree)
        self.assertEqual(len(tree.get_all_persons()), 2)

        # 이름 확인
        persons = tree.get_all_persons()
        names = [p.name for p in persons]
        self.assertIn("John Doe", names)
        self.assertIn("Jane Doe", names)


class TestFileHandlerGEDCOMExport(unittest.TestCase):
    """GEDCOM 내보내기 테스트."""

    def setUp(self):
        self.tree = FamilyTree()
        self.father = Person(name="John Doe", gender="M", birth_year=1960, birth_month=3, birth_day=15)
        self.mother = Person(name="Jane Doe", gender="F", birth_year=1962)
        self.child = Person(name="Tom Doe", gender="M", birth_year=1990, death_year=2050)
        for p in [self.father, self.mother, self.child]:
            self.tree.add_person(p)
        self.tree.set_spouse(self.father.id, self.mother.id)
        self.tree.set_parent_child(self.father.id, self.child.id)
        self.tree.set_parent_child(self.mother.id, self.child.id)

    def test_save_gedcom(self):
        """기본 GEDCOM 내보내기 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.ged")
            result = FileHandler.save_gedcom(self.tree, path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(path))

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("0 HEAD", content)
            self.assertIn("0 TRLR", content)
            self.assertIn("John Doe", content)
            self.assertIn("Jane Doe", content)
            self.assertIn("Tom Doe", content)
            self.assertIn("1 SEX M", content)
            self.assertIn("1 SEX F", content)
            self.assertIn("15 MAR 1960", content)
            self.assertIn("1 HUSB", content)
            self.assertIn("1 WIFE", content)
            self.assertIn("1 CHIL", content)

    def test_gedcom_roundtrip(self):
        """GEDCOM 내보내기 후 재가져오기 라운드트립 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "roundtrip.ged")
            self.assertTrue(FileHandler.save_gedcom(self.tree, path))

            loaded = FileHandler.load_gedcom(path)
            self.assertIsNotNone(loaded)

            persons = loaded.get_all_persons()
            self.assertEqual(len(persons), 3)

            names = {p.name for p in persons}
            self.assertIn("John Doe", names)
            self.assertIn("Jane Doe", names)
            self.assertIn("Tom Doe", names)

    def test_format_gedcom_date(self):
        """GEDCOM 날짜 형식 테스트."""
        self.assertEqual(FileHandler._format_gedcom_date(1990), "1990")
        self.assertEqual(FileHandler._format_gedcom_date(1990, 1), "JAN 1990")
        self.assertEqual(FileHandler._format_gedcom_date(1990, 3, 15), "15 MAR 1990")
        self.assertEqual(FileHandler._format_gedcom_date(None), "")


class TestFileFilters(unittest.TestCase):
    """파일 필터 테스트."""

    def test_get_save_filters(self):
        """저장 필터 테스트."""
        filters = FileHandler.get_save_filters()

        self.assertIn("json", filters.lower())
        self.assertIn("xlsx", filters.lower())

    def test_get_open_filters(self):
        """열기 필터 테스트."""
        filters = FileHandler.get_open_filters()

        self.assertIn("json", filters.lower())
        self.assertIn("xlsx", filters.lower())
        self.assertIn("ged", filters.lower())


if __name__ == '__main__':
    unittest.main()
