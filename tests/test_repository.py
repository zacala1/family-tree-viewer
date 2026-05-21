"""Repository 계층 유닛 테스트.

PersonRepository, RelationshipRepository는 FamilyTree에 위임하지만
- PersonRepository.save() 의 add/update 분기
- RelationshipRepository.count_by_type / find_by_type / find_by_person 의 컬렉션 처리
는 자체 로직이라 회귀 가드 필요.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.models.relationship import RelationType
from src.repositories.person_repository import PersonRepository
from src.repositories.relationship_repository import RelationshipRepository


# === PersonRepository ===

class TestPersonRepositorySave:
    def test_save_new_person_adds(self):
        tree = FamilyTree()
        repo = PersonRepository(tree)
        repo.save(Person(id="p1", name="홍길동"))
        assert repo.exists("p1")
        assert repo.count() == 1

    def test_save_existing_person_updates(self):
        tree = FamilyTree()
        repo = PersonRepository(tree)
        repo.save(Person(id="p1", name="홍길동"))
        repo.save(Person(id="p1", name="홍길동(改名)"))
        assert repo.count() == 1
        assert repo.find_by_id("p1").name == "홍길동(改名)"

    def test_save_idempotent_for_unchanged(self):
        tree = FamilyTree()
        repo = PersonRepository(tree)
        p = Person(id="p1", name="홍길동")
        repo.save(p)
        repo.save(p)
        assert repo.count() == 1


class TestPersonRepositoryDelegation:
    def test_find_methods_delegate_to_tree(self, sample_family):
        tree, ids = sample_family
        repo = PersonRepository(tree)
        assert repo.find_by_id(ids["father"]).name == "아버지"
        assert len(repo.find_all()) == 6
        parents = repo.find_parents(ids["child1"])
        assert {p.id for p in parents} == {ids["father"], ids["mother"]}
        children = repo.find_children(ids["father"])
        assert {c.id for c in children} == {ids["child1"], ids["child2"]}
        spouses = repo.find_spouses(ids["father"])
        assert spouses[0].id == ids["mother"]

    def test_exists_returns_false_for_missing(self, empty_tree):
        repo = PersonRepository(empty_tree)
        assert repo.exists("nonexistent") is False

    def test_count_starts_at_zero(self, empty_tree):
        assert PersonRepository(empty_tree).count() == 0


# === RelationshipRepository ===

class TestRelationshipRepositoryCountByType:
    def test_counts_parent_child_relationships(self, sample_family):
        tree, _ = sample_family
        repo = RelationshipRepository(tree)
        # 부모-자녀 6건 (조부→부, 조모→부, 부→자1, 모→자1, 부→자2, 모→자2)
        assert repo.count_by_type(RelationType.PARENT_CHILD) == 6

    def test_counts_spouse_relationships(self, sample_family):
        tree, _ = sample_family
        repo = RelationshipRepository(tree)
        # 배우자 2건 (조부+조모, 부+모)
        assert repo.count_by_type(RelationType.SPOUSE) == 2

    def test_empty_tree_counts_zero(self, empty_tree):
        repo = RelationshipRepository(empty_tree)
        assert repo.count_by_type(RelationType.SPOUSE) == 0
        assert repo.count_by_type(RelationType.PARENT_CHILD) == 0


class TestRelationshipRepositoryFindByPerson:
    def test_returns_relationships_touching_person(self, sample_family):
        tree, ids = sample_family
        repo = RelationshipRepository(tree)
        rels = repo.find_by_person(ids["father"])
        # 부모로부터 2건, 자녀로 2건, 배우자 1건 = 5건
        assert len(rels) == 5

    def test_returns_empty_for_unrelated_person(self):
        tree = FamilyTree()
        tree.add_person(Person(id="solo", name="외톨이"))
        repo = RelationshipRepository(tree)
        assert repo.find_by_person("solo") == []


class TestRelationshipRepositoryFindByType:
    def test_filters_by_type(self, sample_family):
        tree, _ = sample_family
        repo = RelationshipRepository(tree)
        spouses = repo.find_by_type(RelationType.SPOUSE)
        assert len(spouses) == 2
        assert all(r.rel_type == RelationType.SPOUSE for r in spouses)


class TestRelationshipRepositoryCreate:
    def test_create_parent_child_returns_relationship(self, empty_tree):
        empty_tree.add_person(Person(id="f", name="부", gender="M"))
        empty_tree.add_person(Person(id="c", name="자", gender="F"))
        repo = RelationshipRepository(empty_tree)
        rel = repo.create_parent_child("f", "c")
        assert rel is not None
        assert rel.person1_id == "f"
        assert rel.person2_id == "c"

    def test_create_parent_child_returns_none_for_cycle(self, empty_tree):
        # f -> c, then c -> f (cycle)
        empty_tree.add_person(Person(id="f", name="부", gender="M"))
        empty_tree.add_person(Person(id="c", name="자", gender="M"))
        repo = RelationshipRepository(empty_tree)
        repo.create_parent_child("f", "c")
        rel = repo.create_parent_child("c", "f")
        assert rel is None  # cycle 방지

    def test_create_spouse_with_marriage_date(self, empty_tree):
        empty_tree.add_person(Person(id="h", name="남편", gender="M"))
        empty_tree.add_person(Person(id="w", name="아내", gender="F"))
        repo = RelationshipRepository(empty_tree)
        rel = repo.create_spouse("h", "w", marriage_year=2020, marriage_month=6, marriage_day=15)
        assert rel is not None
        assert rel.marriage_year == 2020
        assert rel.marriage_month == 6
        assert rel.marriage_day == 15
