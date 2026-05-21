"""FamilyTreeService 통합 테스트.

이 계층은 validation → repository → search_index 동기화를 조율하므로
end-to-end 흐름과 인덱스 동기화 회귀 가드가 핵심.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.repositories.person_repository import PersonRepository
from src.repositories.relationship_repository import RelationshipRepository
from src.services.family_tree_service import FamilyTreeService


@pytest.fixture
def service(empty_tree):
    person_repo = PersonRepository(empty_tree)
    rel_repo = RelationshipRepository(empty_tree)
    return FamilyTreeService(person_repo, rel_repo)


class TestAddPerson:
    def test_returns_success_for_valid(self, service):
        ok, err = service.add_person(Person(name="홍길동"))
        assert ok is True
        assert err == ""
        assert len(service.get_all_persons()) == 1

    def test_returns_failure_for_empty_name(self, service):
        ok, err = service.add_person(Person(name=""))
        assert ok is False
        assert err != ""
        assert len(service.get_all_persons()) == 0

    def test_returns_failure_for_invalid_email(self, service):
        ok, err = service.add_person(Person(name="홍길동", email="not-an-email"))
        assert ok is False
        assert "email" in err.lower() or "@" in err

    def test_search_index_updated_after_add(self, service):
        service.add_person(Person(id="p1", name="홍길동"))
        results = service.search_persons("홍")
        assert any(p.id == "p1" for p in results)


class TestUpdatePerson:
    def test_updates_existing_person(self, service):
        service.add_person(Person(id="p1", name="홍길동"))
        ok, err = service.update_person(Person(id="p1", name="홍길순"))
        assert ok is True
        assert service.get_person("p1").name == "홍길순"

    def test_search_index_reflects_updated_name(self, service):
        service.add_person(Person(id="p1", name="홍길동"))
        service.update_person(Person(id="p1", name="김철수"))
        # 새 이름으로 검색 가능
        results = service.search_persons("김철수")
        assert any(p.id == "p1" for p in results)

    def test_rejects_update_with_invalid_data(self, service):
        service.add_person(Person(id="p1", name="홍길동"))
        ok, err = service.update_person(Person(id="p1", name=""))
        assert ok is False


class TestDeletePerson:
    def test_deletes_and_removes_from_index(self, service):
        service.add_person(Person(id="p1", name="홍길동"))
        ok, err = service.delete_person("p1")
        assert ok is True
        assert service.get_person("p1") is None
        assert service.search_persons("홍") == []

    def test_returns_failure_for_missing(self, service):
        ok, err = service.delete_person("nonexistent")
        assert ok is False


class TestRelationshipOperations:
    def test_add_parent_child(self, service):
        service.add_person(Person(id="f", name="부", gender="M"))
        service.add_person(Person(id="c", name="자", gender="F"))
        ok, err = service.add_parent_child_relationship("f", "c")
        assert ok is True
        family = service.get_family_members("c")
        assert any(p.id == "f" for p in family["parents"])

    def test_add_parent_child_rejects_missing_parent(self, service):
        service.add_person(Person(id="c", name="자"))
        ok, err = service.add_parent_child_relationship("ghost", "c")
        assert ok is False
        assert "not found" in err.lower()

    def test_add_parent_child_rejects_cycle(self, service):
        service.add_person(Person(id="a", name="A", gender="M"))
        service.add_person(Person(id="b", name="B", gender="M"))
        service.add_parent_child_relationship("a", "b")
        ok, err = service.add_parent_child_relationship("b", "a")
        assert ok is False

    def test_add_spouse_with_invalid_marriage_date(self, service):
        service.add_person(Person(id="h", name="남편", gender="M"))
        service.add_person(Person(id="w", name="아내", gender="F"))
        ok, err = service.add_spouse_relationship(
            "h", "w", marriage_year=99999, marriage_month=1, marriage_day=1
        )
        assert ok is False


class TestStatistics:
    def test_statistics_count_correctly(self, service):
        service.add_person(Person(id="f", name="부", gender="M"))
        service.add_person(Person(id="m", name="모", gender="F"))
        service.add_person(Person(id="c", name="자", gender="F"))
        service.add_spouse_relationship("f", "m")
        service.add_parent_child_relationship("f", "c")
        service.add_parent_child_relationship("m", "c")

        stats = service.get_statistics()
        assert stats["total_persons"] == 3
        assert stats["total_relationships"] == 3
        assert stats["spouse_relationships"] == 1
        assert stats["parent_child_relationships"] == 2


class TestSearchIndexRebuild:
    def test_rebuild_on_init_picks_up_existing_data(self, empty_tree):
        # 트리에 미리 데이터 추가 후 service 생성 → 인덱스 자동 빌드 확인
        empty_tree.add_person(Person(id="p1", name="홍길동"))
        empty_tree.add_person(Person(id="p2", name="김철수"))
        person_repo = PersonRepository(empty_tree)
        rel_repo = RelationshipRepository(empty_tree)
        svc = FamilyTreeService(person_repo, rel_repo)

        assert any(p.id == "p1" for p in svc.search_persons("홍"))
        assert any(p.id == "p2" for p in svc.search_persons("김"))
