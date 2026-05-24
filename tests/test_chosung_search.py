"""한글 초성 검색 회귀 가드.

"홍길동" 인물을 "ㅎㄱㄷ"으로 검색하는 것이 한국 사용자 워크플로.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.utils.search_index import (
    PersonSearchIndex,
    _chosung_only,
    _is_chosung_query,
)


class TestChosungOnly:
    def test_basic_hangul(self):
        assert _chosung_only("홍길동") == "ㅎㄱㄷ"

    def test_mixed_english_korean(self):
        assert _chosung_only("홍Hong") == "ㅎhong"

    def test_pure_english_lowercased(self):
        assert _chosung_only("Hong Gildong") == "hong gildong"

    def test_complex_hangul(self):
        # "쀍" 같은 복잡한 글자도 ㅃ 초성
        assert _chosung_only("쀍") == "ㅃ"

    def test_empty(self):
        assert _chosung_only("") == ""

    def test_already_chosung_preserved(self):
        # 초성만 들어오면 그대로 (초성 자체는 U+3131 영역 — 변환 대상 아님)
        assert _chosung_only("ㅎㄱㄷ") == "ㅎㄱㄷ"


class TestIsChosungQuery:
    def test_pure_chosung(self):
        assert _is_chosung_query("ㅎㄱㄷ") is True

    def test_with_space(self):
        assert _is_chosung_query("ㅎ ㄱㄷ") is True

    def test_full_hangul_syllable_is_not(self):
        assert _is_chosung_query("홍") is False

    def test_english_is_not(self):
        assert _is_chosung_query("abc") is False

    def test_empty_is_not(self):
        assert _is_chosung_query("") is False


class TestChosungSearch:
    @pytest.fixture
    def populated_index(self):
        idx = PersonSearchIndex()
        persons = [
            Person(id="p1", name="홍길동"),
            Person(id="p2", name="김철수"),
            Person(id="p3", name="이영희"),
            Person(id="p4", name="홍순신"),  # 초성 ㅎㅅㅅ
            Person(id="p5", name="Hong Gildong"),  # 영문
        ]
        idx.index_persons(persons)
        return idx

    def test_chosung_finds_korean_name(self, populated_index):
        """ㅎㄱㄷ 입력 → 홍길동."""
        results = populated_index.search("ㅎㄱㄷ")
        ids = {p.id for p in results}
        assert "p1" in ids

    def test_chosung_partial_matches(self, populated_index):
        """ㅎ 단독으로 ㅎ로 시작하는 이름 모두 찾음."""
        results = populated_index.search("ㅎ")
        ids = {p.id for p in results}
        assert "p1" in ids  # 홍길동
        assert "p4" in ids  # 홍순신

    def test_chosung_middle_substring(self, populated_index):
        """ㄱㄷ → 길동(ㄱㄷ) 부분 매칭 (substring 인덱스)."""
        results = populated_index.search("ㄱㄷ")
        ids = {p.id for p in results}
        assert "p1" in ids

    def test_full_name_still_works(self, populated_index):
        """초성 추가 후에도 원본 이름 검색 정상."""
        results = populated_index.search("홍길동")
        assert any(p.id == "p1" for p in results)

    def test_korean_substring_still_works(self, populated_index):
        results = populated_index.search("길동")
        assert any(p.id == "p1" for p in results)

    def test_english_unaffected(self, populated_index):
        results = populated_index.search("hong")
        ids = {p.id for p in results}
        assert "p5" in ids  # Hong Gildong

    def test_no_matches(self, populated_index):
        results = populated_index.search("ㅋㅌㅍ")
        assert results == []


class TestRemoveCleansChosung:
    def test_remove_purges_chosung_index(self):
        idx = PersonSearchIndex()
        idx.add_person(Person(id="p1", name="홍길동"))
        assert idx.search("ㅎㄱㄷ")  # 추가 후 검색 성공
        idx.remove_person("p1")
        # 초성 인덱스에서도 사라져야
        assert idx.search("ㅎㄱㄷ") == []

    def test_update_reflects_new_chosung(self):
        idx = PersonSearchIndex()
        p = Person(id="p1", name="홍길동")
        idx.add_person(p)
        assert idx.search("ㅎㄱㄷ")

        # 이름 변경
        p.name = "김철수"
        idx.update_person(p)
        # 옛 초성으로 검색 안 됨
        assert idx.search("ㅎㄱㄷ") == []
        # 새 초성으로 찾음
        assert any(person.id == "p1" for person in idx.search("ㄱㅊㅅ"))


class TestNullSafeSort:
    def test_search_with_empty_name_no_crash(self):
        """인덱스에 들어간 후 person.name이 어쩌다 None이 되어도 정렬 안전."""
        idx = PersonSearchIndex()
        p = Person(id="p1", name="홍길동")
        idx.add_person(p)
        # name을 강제로 None으로 (외부 코드가 stale 참조를 갖는 시나리오)
        p.name = None
        # 크래시 없이 search 가능 (None 정렬 키 처리됨)
        results = idx.search("홍")
        # name None 이면 빈 string 키로 정렬돼 결과에 포함되거나 빠질 수 있지만 크래시 금지
        assert isinstance(results, list)
