"""Family Tree Service - Business logic layer.

This service layer sits between the UI and repositories,
containing all business logic and validation.
Thread safety is delegated to the underlying repositories/FamilyTree model.
"""

from typing import List, Optional, Tuple

from ..models.person import Person
from ..models.relationship import Relationship
from ..models.validators import PersonValidator
from ..repositories.person_repository import PersonRepository
from ..repositories.relationship_repository import RelationshipRepository
from ..utils.search_index import PersonSearchIndex
from ..utils.logger import log_action, warning


class FamilyTreeService:
    """Service for family tree business logic operations.

    This class:
    - Coordinates operations across multiple repositories
    - Applies business validation rules
    - Maintains search index
    - Logs business events

    Thread safety: Delegated to FamilyTree (single lock strategy).
    """

    def __init__(
        self,
        person_repo: PersonRepository,
        relationship_repo: RelationshipRepository,
    ):
        self._person_repo = person_repo
        self._relationship_repo = relationship_repo
        self._search_index = PersonSearchIndex()

        # Build initial search index
        self._rebuild_search_index()

    # === Person Operations ===

    def add_person(self, person: Person) -> Tuple[bool, str]:
        """Add a new person with validation."""
        # Validate person data
        is_valid, error_msg = PersonValidator.validate_all(
            name=person.name,
            email=person.email,
            phone=person.phone,
            birth_year=person.birth_year,
            birth_month=person.birth_month,
            birth_day=person.birth_day,
            death_year=person.death_year,
            death_month=person.death_month,
            death_day=person.death_day,
        )

        if not is_valid:
            return False, error_msg

        try:
            self._person_repo.add(person)
            self._search_index.add_person(person)
            log_action("person_added", person_id=person.id, name=person.name)
            return True, ""
        except ValueError as e:
            return False, str(e)

    def update_person(self, person: Person) -> Tuple[bool, str]:
        """Update an existing person with validation."""
        is_valid, error_msg = PersonValidator.validate_all(
            name=person.name,
            email=person.email,
            phone=person.phone,
            birth_year=person.birth_year,
            birth_month=person.birth_month,
            birth_day=person.birth_day,
            death_year=person.death_year,
            death_month=person.death_month,
            death_day=person.death_day,
        )

        if not is_valid:
            return False, error_msg

        try:
            self._person_repo.update(person)
            self._search_index.update_person(person)
            log_action("person_updated", person_id=person.id, name=person.name)
            return True, ""
        except Exception as e:
            return False, str(e)

    def delete_person(self, person_id: str) -> Tuple[bool, str]:
        """Delete a person and all related relationships."""
        try:
            person = self._person_repo.find_by_id(person_id)
            if not person:
                return False, "Person not found"

            self._person_repo.delete(person_id)
            self._search_index.remove_person(person_id)
            log_action("person_deleted", person_id=person_id, name=person.name)
            return True, ""
        except Exception as e:
            return False, str(e)

    def get_person(self, person_id: str) -> Optional[Person]:
        return self._person_repo.find_by_id(person_id)

    def get_all_persons(self) -> List[Person]:
        return self._person_repo.find_all()

    def search_persons(self, query: str) -> List[Person]:
        """Search for persons by name (optimized with Trie).

        Performance: O(m + k) where m = query length, k = number of results
        """
        return self._search_index.search(query)

    # === Relationship Operations ===

    def add_parent_child_relationship(
        self, parent_id: str, child_id: str
    ) -> Tuple[bool, str]:
        """Add parent-child relationship with validation."""
        parent = self._person_repo.find_by_id(parent_id)
        child = self._person_repo.find_by_id(child_id)

        if not parent:
            return False, "Parent not found"
        if not child:
            return False, "Child not found"

        rel = self._relationship_repo.create_parent_child(parent_id, child_id)

        if not rel:
            return False, "Cannot create relationship (cycle detected or invalid)"

        log_action(
            "relationship_added",
            relationship_type="parent_child",
            parent_id=parent_id,
            child_id=child_id,
        )
        return True, ""

    def add_spouse_relationship(
        self,
        person1_id: str,
        person2_id: str,
        marriage_year: Optional[int] = None,
        marriage_month: Optional[int] = None,
        marriage_day: Optional[int] = None,
        is_lunar: bool = False,
    ) -> Tuple[bool, str]:
        """Add spouse relationship with validation."""
        person1 = self._person_repo.find_by_id(person1_id)
        person2 = self._person_repo.find_by_id(person2_id)

        if not person1:
            return False, "First person not found"
        if not person2:
            return False, "Second person not found"

        # Validate marriage date if provided
        if marriage_year or marriage_month or marriage_day:
            is_valid, error_msg = PersonValidator.validate_date(
                marriage_year, marriage_month, marriage_day
            )
            if not is_valid:
                return False, error_msg

        rel = self._relationship_repo.create_spouse(
            person1_id,
            person2_id,
            marriage_year,
            marriage_month,
            marriage_day,
            is_lunar,
        )

        if not rel:
            return False, "Cannot create spouse relationship"

        log_action(
            "relationship_added",
            relationship_type="spouse",
            person1_id=person1_id,
            person2_id=person2_id,
        )
        return True, ""

    def get_family_members(self, person_id: str) -> dict:
        """Get all family members of a person."""
        return {
            "parents": self._person_repo.find_parents(person_id),
            "spouses": self._person_repo.find_spouses(person_id),
            "children": self._person_repo.find_children(person_id),
            "siblings": self._person_repo.find_siblings(person_id),
        }

    # === Search Index Management ===

    def _rebuild_search_index(self) -> None:
        """Rebuild the entire search index."""
        all_persons = self._person_repo.find_all()
        self._search_index.index_persons(all_persons)
        log_action(
            "search_index_rebuilt",
            person_count=self._search_index.size,
        )

    def get_search_index_stats(self) -> dict:
        return self._search_index.get_stats()

    # === Statistics ===

    def get_statistics(self) -> dict:
        from ..models.relationship import RelationType

        return {
            "total_persons": self._person_repo.count(),
            "total_relationships": self._relationship_repo.count(),
            "parent_child_relationships": self._relationship_repo.count_by_type(
                RelationType.PARENT_CHILD
            ),
            "spouse_relationships": self._relationship_repo.count_by_type(
                RelationType.SPOUSE
            ),
            "search_index": self.get_search_index_stats(),
        }
