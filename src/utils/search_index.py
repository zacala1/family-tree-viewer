"""Optimized search index using Trie data structure.

Performance: O(m) search time where m is query length
Memory: O(n*k) where n is number of persons, k is average name length
"""

from typing import List, Dict, Set, Optional
from ..models.person import Person


# 한글 초성 19개 (현대 한글 음절 = 초성×588 + 중성×28 + 종성)
_CHOSUNG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_CHOSUNG_SET = frozenset(_CHOSUNG)
_HANGUL_START = 0xAC00
_HANGUL_END = 0xD7A3


def _chosung_only(text: str) -> str:
    """한글 음절을 초성으로 변환. 비한글 문자는 lowercase 유지.

    예: "홍길동" → "ㅎㄱㄷ", "Hong" → "hong", "홍Hong" → "ㅎhong"
    """
    out = []
    for ch in text:
        code = ord(ch)
        if _HANGUL_START <= code <= _HANGUL_END:
            out.append(_CHOSUNG[(code - _HANGUL_START) // 588])
        else:
            out.append(ch.lower())
    return "".join(out)


def _is_chosung_query(query: str) -> bool:
    """query가 초성만으로 구성됐는지 (공백 허용)."""
    if not query:
        return False
    return all(ch in _CHOSUNG_SET or ch.isspace() for ch in query)


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
        # 한글 초성 인덱스 — "홍길동" → "ㅎㄱㄷ"로 substring index
        # 같은 trie를 공유하므로 query 형태에 따라 자연스럽게 매칭
        self._indexed_chosung: Dict[str, str] = {}
        self._indexed_count: int = 0

    def index_persons(self, persons: List[Person]) -> None:
        """Build search index from person list."""
        self.root = TrieNode()
        self._person_map.clear()
        self._indexed_names.clear()
        self._indexed_chosung.clear()
        self._indexed_count = 0

        for person in persons:
            self.add_person(person)

    def add_person(self, person: Person) -> None:
        """Add a single person to the index.

        한글 이름은 원본 + 초성 두 표현으로 indexed:
        - 원본: "홍길동" → substrings "홍길동", "길동", "동"
        - 초성: "ㅎㄱㄷ" → substrings "ㅎㄱㄷ", "ㄱㄷ", "ㄷ"
        같은 Trie에 들어가지만 키 집합이 분리(Hangul syllable vs Jamo)되어 충돌 없음.
        """
        if not person.name:
            return

        self._person_map[person.id] = person

        # 원본 substring 인덱스 (기존 동작)
        name = person.name.lower()
        self._indexed_names[person.id] = name
        for i in range(len(name)):
            self._insert_substring(name[i:], person.id)

        # 초성 substring 인덱스 — 한글이 포함된 경우만 (영문 등은 동일하여 무의미)
        chosung = _chosung_only(person.name)
        if chosung != name:
            self._indexed_chosung[person.id] = chosung
            for i in range(len(chosung)):
                self._insert_substring(chosung[i:], person.id)

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

        # Sort by name — None/empty name 안전 처리 (인덱스 stale 시점 방어)
        return sorted(results, key=lambda p: (p.name or "").lower())

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

        # 원본 인덱스 제거
        indexed_name = self._indexed_names.get(person_id)
        if indexed_name:
            for i in range(len(indexed_name)):
                self._remove_from_trie(indexed_name[i:], person_id)

        # 초성 인덱스 제거
        indexed_chosung = self._indexed_chosung.get(person_id)
        if indexed_chosung:
            for i in range(len(indexed_chosung)):
                self._remove_from_trie(indexed_chosung[i:], person_id)

        del self._person_map[person_id]
        self._indexed_names.pop(person_id, None)
        self._indexed_chosung.pop(person_id, None)
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
        self._indexed_chosung.clear()
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
