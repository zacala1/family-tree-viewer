"""Person Repository - Data access layer for Person entities.

Separates data access logic from business logic and UI.
Thread safety is delegated to the underlying FamilyTree model.
"""

from typing import List, Optional, Set

from ..models.person import Person
from ..models.family_tree import FamilyTree


class PersonRepository:
    """Repository for Person data access operations.

    Thread safety: Delegated to FamilyTree (single lock strategy).
    """

    def __init__(self, family_tree: FamilyTree):
        self._tree = family_tree

    def find_by_id(self, person_id: str) -> Optional[Person]:
        return self._tree.get_person(person_id)

    def find_all(self) -> List[Person]:
        return self._tree.get_all_persons()

    def save(self, person: Person) -> None:
        existing = self._tree.get_person(person.id)
        if existing:
            self._tree.update_person(person)
        else:
            self._tree.add_person(person)

    def add(self, person: Person) -> None:
        self._tree.add_person(person)

    def update(self, person: Person) -> None:
        self._tree.update_person(person)

    def delete(self, person_id: str) -> None:
        self._tree.remove_person(person_id)

    def exists(self, person_id: str) -> bool:
        return self._tree.get_person(person_id) is not None

    def count(self) -> int:
        return self._tree.person_count

    def find_by_generation(self, generation: int) -> List[Person]:
        persons_by_gen = self._tree.get_persons_by_generation()
        return persons_by_gen.get(generation, [])

    def find_parents(self, person_id: str) -> List[Person]:
        return self._tree.get_parents(person_id)

    def find_children(self, person_id: str) -> List[Person]:
        return self._tree.get_children(person_id)

    def find_spouses(self, person_id: str) -> List[Person]:
        return self._tree.get_spouses(person_id)

    def find_siblings(self, person_id: str) -> List[Person]:
        return self._tree.get_siblings(person_id)

    def find_direct_family(self, person_id: str) -> List[Person]:
        return self._tree.get_direct_family(person_id)

    def find_direct_family_ids(self, person_id: str) -> Set[str]:
        return self._tree.get_direct_family_ids(person_id)
