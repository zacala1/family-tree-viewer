"""Relationship Repository - Data access layer for Relationship entities.

Thread safety is delegated to the underlying FamilyTree model.
"""

from typing import List, Optional

from ..models.relationship import Relationship, RelationType
from ..models.family_tree import FamilyTree
from ..models.person import Person


class RelationshipRepository:
    """Repository for Relationship data access operations.

    Thread safety: Delegated to FamilyTree (single lock strategy).
    """

    def __init__(self, family_tree: FamilyTree):
        self._tree = family_tree

    def find_by_id(self, relationship_id: str) -> Optional[Relationship]:
        return self._tree.get_relationship(relationship_id)

    def find_all(self) -> List[Relationship]:
        return self._tree.get_all_relationships()

    def save(self, relationship: Relationship) -> None:
        self._tree.add_relationship(relationship)

    def delete(self, relationship_id: str) -> None:
        self._tree.remove_relationship(relationship_id)

    def find_spouse_relationship(
        self, person1_id: str, person2_id: str
    ) -> Optional[Relationship]:
        return self._tree.get_spouse_relationship(person1_id, person2_id)

    def find_spouse_relationships(self, person_id: str) -> List[Relationship]:
        return self._tree.get_spouse_relationships(person_id)

    def find_current_spouse(self, person_id: str) -> Optional[Person]:
        return self._tree.get_current_spouse(person_id)

    def find_current_spouse_id(self, person_id: str) -> Optional[str]:
        return self._tree.get_current_spouse_id(person_id)

    def create_parent_child(
        self, parent_id: str, child_id: str
    ) -> Optional[Relationship]:
        return self._tree.set_parent_child(parent_id, child_id)

    def create_spouse(
        self,
        person1_id: str,
        person2_id: str,
        marriage_year: Optional[int] = None,
        marriage_month: Optional[int] = None,
        marriage_day: Optional[int] = None,
        is_lunar: bool = False,
    ) -> Optional[Relationship]:
        return self._tree.set_spouse(
            person1_id,
            person2_id,
            marriage_year,
            marriage_month,
            marriage_day,
            is_lunar,
        )

    def find_by_type(self, rel_type: RelationType) -> List[Relationship]:
        all_rels = self._tree.get_all_relationships()
        return [r for r in all_rels if r.rel_type == rel_type]

    def find_by_person(self, person_id: str) -> List[Relationship]:
        all_rels = self._tree.get_all_relationships()
        return [
            r
            for r in all_rels
            if r.person1_id == person_id or r.person2_id == person_id
        ]

    def count(self) -> int:
        return self._tree.relationship_count

    def count_by_type(self, rel_type: RelationType) -> int:
        # 전체 리스트 생성 없이 직접 카운트
        return sum(1 for r in self._tree.get_all_relationships() if r.rel_type == rel_type)
