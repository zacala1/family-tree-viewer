"""중복 인물 감지 유닛 테스트.

회귀 방지 대상:
- normalize_name의 괄호 제거·NFC 정규화
- levenshtein_distance 기본 동작
- find_similar_persons 임계값·exclude_id 처리
"""
import unittest
import sys
import os
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.person import Person
from src.utils.duplicate_detector import (
    normalize_name,
    levenshtein_distance,
    find_similar_persons,
)


class TestNormalizeName(unittest.TestCase):
    def test_removes_spaces_and_lowercases(self):
        self.assertEqual(normalize_name("John Doe"), "johndoe")
        self.assertEqual(normalize_name("  HELLO  "), "hello")

    def test_strips_parenthesized_annotations(self):
        # 한자 변형
        self.assertEqual(normalize_name("김철수 (鐵秀)"), "김철수")
        # 고인 표시
        self.assertEqual(normalize_name("김철수 (故)"), "김철수")
        # 대괄호
        self.assertEqual(normalize_name("Lee Cheolsu [Jr.]"), "leecheolsu")
        # 전각 괄호
        self.assertEqual(normalize_name("김철수（鐵秀）"), "김철수")

    def test_nfc_unifies_decomposed_hangul(self):
        # NFD로 분해된 한글이 NFC와 같게 정규화돼야 함
        composed = "김"  # NFC (완성형)
        decomposed = unicodedata.normalize("NFD", composed)  # 자모 분해
        self.assertEqual(normalize_name(composed), normalize_name(decomposed))

    def test_handles_empty_string(self):
        self.assertEqual(normalize_name(""), "")
        self.assertEqual(normalize_name("   "), "")


class TestLevenshteinDistance(unittest.TestCase):
    def test_identical_strings(self):
        self.assertEqual(levenshtein_distance("abc", "abc"), 0)

    def test_single_edit(self):
        self.assertEqual(levenshtein_distance("kitten", "sitten"), 1)
        self.assertEqual(levenshtein_distance("abc", "ab"), 1)

    def test_classic_example(self):
        # kitten -> sitting: 3 edits
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)

    def test_empty_strings(self):
        self.assertEqual(levenshtein_distance("", ""), 0)
        self.assertEqual(levenshtein_distance("abc", ""), 3)
        self.assertEqual(levenshtein_distance("", "abc"), 3)


class TestFindSimilarPersons(unittest.TestCase):
    def setUp(self):
        self.persons = [
            Person(id="p1", name="홍길동"),
            Person(id="p2", name="홍길순"),
            Person(id="p3", name="김철수"),
            Person(id="p4", name="김철수 (故)"),
        ]

    def test_finds_exact_match(self):
        results = find_similar_persons("홍길동", self.persons, threshold=2)
        # 자기 자신 포함 + 비슷한 이름
        ids = [p.id for p, _ in results]
        self.assertIn("p1", ids)

    def test_excludes_self_via_exclude_id(self):
        results = find_similar_persons("홍길동", self.persons, threshold=2, exclude_id="p1")
        ids = [p.id for p, _ in results]
        self.assertNotIn("p1", ids)
        # 1 글자 차이인 홍길순은 포함되어야 함
        self.assertIn("p2", ids)

    def test_bracket_annotated_name_matches_base(self):
        # "김철수"로 검색했을 때 "김철수 (故)"도 같은 이름으로 매칭
        results = find_similar_persons("김철수", self.persons, threshold=0, exclude_id="p3")
        ids = [p.id for p, _ in results]
        self.assertIn("p4", ids)

    def test_threshold_filters_results(self):
        # 임계 0은 정확히 일치만
        results = find_similar_persons("홍길동", self.persons, threshold=0, exclude_id="p1")
        ids = [p.id for p, _ in results]
        self.assertNotIn("p2", ids)  # 1 글자 차이 제외

    def test_results_sorted_by_distance(self):
        results = find_similar_persons("홍길동", self.persons, threshold=3)
        distances = [d for _, d in results]
        self.assertEqual(distances, sorted(distances))

    def test_empty_name_returns_empty(self):
        self.assertEqual(find_similar_persons("", self.persons), [])
        self.assertEqual(find_similar_persons("   ", self.persons), [])


if __name__ == "__main__":
    unittest.main()
