"""Optimized search index using Trie data structure.

Performance: O(m) search time where m is query length
Memory: O(n*k) where n is number of persons, k is average name length
"""

from typing import List, Dict, Set, Optional
from ..models.person import Person


class TrieNode:
    """Node in the Trie data structure."""

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.person_ids: Set[str] = set()  # Person IDs whose names pass through this node
        self.is_end: bool = False


class PersonSearchIndex:
    """Trie-based search index for fast person name lookup.

    Features:
    - O(m) search time (m = query length)
    - Prefix matching support
    - Case-insensitive search
    - Automatic index rebuilding

    Example:
        index = PersonSearchIndex()
        index.index_persons(all_persons)
        results = index.search("홍")  # Returns all persons with "홍" in name
    """

    def __init__(self):
        self.root = TrieNode()
        self._person_map: Dict[str, Person] = {}  # person_id -> Person
        self._indexed_names: Dict[str, str] = {}  # person_id -> indexed name (lowercase)
        self._indexed_count: int = 0

    def index_persons(self, persons: List[Person]) -> None:
        """Build search index from person list.

        Args:
            persons: List of Person objects to index
        """
        # Clear existing index
        self.root = TrieNode()
        self._person_map.clear()
        self._indexed_count = 0

        # Index each person
        for person in persons:
            self.add_person(person)

    def add_person(self, person: Person) -> None:
        """Add a single person to the index.

        Args:
            person: Person object to add
        """
        if not person.name:
            return

        # Store person in map
        self._person_map[person.id] = person

        # Normalize name (lowercase for case-insensitive search)
        name = person.name.lower()
        self._indexed_names[person.id] = name

        # Index all substrings for partial matching
        # Example: "홍길동" -> "홍", "홍길", "홍길동", "길", "길동", "동"
        for i in range(len(name)):
            self._insert_substring(name[i:], person.id)

        self._indexed_count += 1

    def _insert_substring(self, substring: str, person_id: str) -> None:
        """Insert a substring into the Trie.

        Args:
            substring: Substring to insert
            person_id: ID of the person this substring belongs to
        """
        node = self.root

        for char in substring:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.person_ids.add(person_id)

        node.is_end = True

    def search(self, query: str) -> List[Person]:
        """Search for persons by name prefix.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching Person objects, sorted by name

        Performance:
            Time: O(m + k) where m = query length, k = number of results
            Space: O(k)
        """
        if not query:
            return []

        query = query.lower().strip()
        if not query:
            return []

        # Traverse Trie to find matching person IDs
        node = self.root
        for char in query:
            if char not in node.children:
                return []  # No matches
            node = node.children[char]

        # Collect all persons from this node and its descendants
        person_ids = node.person_ids

        # Convert IDs to Person objects
        results = [
            self._person_map[pid]
            for pid in person_ids
            if pid in self._person_map
        ]

        # Sort by name
        return sorted(results, key=lambda p: p.name.lower())

    def _remove_from_trie(self, substring: str, person_id: str) -> None:
        """Trie 노드에서 person_id를 증분 제거."""
        node = self.root
        for char in substring:
            if char not in node.children:
                return
            node = node.children[char]
            node.person_ids.discard(person_id)

    def remove_person(self, person_id: str) -> None:
        """Remove a person from the index (incremental, no rebuild).

        Performance: O(k^2) where k = name length (vs O(n*k) for full rebuild)
        """
        if person_id not in self._person_map:
            return

        # Use the stored indexed name (not the current person.name which may have changed)
        indexed_name = self._indexed_names.get(person_id)
        if indexed_name:
            for i in range(len(indexed_name)):
                self._remove_from_trie(indexed_name[i:], person_id)

        del self._person_map[person_id]
        self._indexed_names.pop(person_id, None)
        self._indexed_count -= 1

    def update_person(self, person: Person) -> None:
        """Update a person in the index (incremental remove + add)."""
        self.remove_person(person.id)
        self.add_person(person)

    def clear(self) -> None:
        """Clear the entire index."""
        self.root = TrieNode()
        self._person_map.clear()
        self._indexed_names.clear()
        self._indexed_count = 0

    @property
    def size(self) -> int:
        """Return the number of indexed persons."""
        return self._indexed_count

    def get_stats(self) -> Dict[str, int]:
        """Get index statistics.

        Returns:
            Dictionary with statistics
        """
        def count_nodes(node: TrieNode) -> int:
            """Recursively count nodes in Trie."""
            count = 1
            for child in node.children.values():
                count += count_nodes(child)
            return count

        return {
            "indexed_persons": self._indexed_count,
            "trie_nodes": count_nodes(self.root),
            "unique_persons": len(self._person_map),
        }
