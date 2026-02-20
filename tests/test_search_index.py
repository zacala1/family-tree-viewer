"""Tests for PersonSearchIndex (Trie-based search)."""

import pytest
from src.models.person import Person
from src.utils.search_index import PersonSearchIndex


class TestPersonSearchIndex:
    """Test suite for PersonSearchIndex."""

    def test_empty_index_search(self):
        """Empty index returns no results."""
        index = PersonSearchIndex()
        results = index.search("홍길동")
        assert results == []

    def test_add_single_person(self):
        """Adding a person allows searching."""
        index = PersonSearchIndex()
        person = Person(name="홍길동", gender="M")
        index.add_person(person)

        results = index.search("홍")
        assert len(results) == 1
        assert results[0].name == "홍길동"

    def test_prefix_search(self):
        """Prefix search returns all matching persons."""
        index = PersonSearchIndex()
        p1 = Person(name="홍길동", gender="M")
        p2 = Person(name="홍길순", gender="F")
        p3 = Person(name="김철수", gender="M")

        index.add_person(p1)
        index.add_person(p2)
        index.add_person(p3)

        results = index.search("홍")
        assert len(results) == 2
        names = [p.name for p in results]
        assert "홍길동" in names
        assert "홍길순" in names

    def test_substring_search(self):
        """Substring search works (not just prefix)."""
        index = PersonSearchIndex()
        person = Person(name="홍길동", gender="M")
        index.add_person(person)

        # Should find "길" in middle of name
        results = index.search("길")
        assert len(results) == 1
        assert results[0].name == "홍길동"

        # Should find "동" at end of name
        results = index.search("동")
        assert len(results) == 1

    def test_case_insensitive_search(self):
        """Search is case-insensitive."""
        index = PersonSearchIndex()
        person = Person(name="John Doe", gender="M")
        index.add_person(person)

        results = index.search("john")
        assert len(results) == 1
        assert results[0].name == "John Doe"

        results = index.search("JOHN")
        assert len(results) == 1

        results = index.search("JoHn")
        assert len(results) == 1

    def test_empty_query(self):
        """Empty query returns no results."""
        index = PersonSearchIndex()
        person = Person(name="홍길동", gender="M")
        index.add_person(person)

        results = index.search("")
        assert results == []

        results = index.search("   ")
        assert results == []

    def test_no_match(self):
        """No match returns empty list."""
        index = PersonSearchIndex()
        person = Person(name="홍길동", gender="M")
        index.add_person(person)

        results = index.search("xyz")
        assert results == []

    def test_results_sorted_by_name(self):
        """Results are sorted alphabetically."""
        index = PersonSearchIndex()
        p1 = Person(name="홍철수", gender="M")
        p2 = Person(name="홍길동", gender="M")
        p3 = Person(name="홍길순", gender="F")

        index.add_person(p1)
        index.add_person(p2)
        index.add_person(p3)

        results = index.search("홍")
        assert len(results) == 3
        # Should be sorted: 홍길동, 홍길순, 홍철수
        assert results[0].name == "홍길동"
        assert results[1].name == "홍길순"
        assert results[2].name == "홍철수"

    def test_index_persons_bulk(self):
        """Bulk indexing with index_persons()."""
        index = PersonSearchIndex()
        persons = [
            Person(name="홍길동", gender="M"),
            Person(name="김철수", gender="M"),
            Person(name="이영희", gender="F"),
        ]

        index.index_persons(persons)

        assert index.size == 3
        results = index.search("홍")
        assert len(results) == 1

    def test_update_person(self):
        """Updating a person updates the index."""
        index = PersonSearchIndex()
        person = Person(name="홍길동", gender="M", id="test-id")
        index.add_person(person)

        # Original search works
        results = index.search("홍")
        assert len(results) == 1

        # Update name
        person.name = "김철수"
        index.update_person(person)

        # Old name no longer found
        results = index.search("홍")
        assert len(results) == 0

        # New name found
        results = index.search("김")
        assert len(results) == 1
        assert results[0].name == "김철수"

    def test_remove_person(self):
        """Removing a person removes from index."""
        index = PersonSearchIndex()
        p1 = Person(name="홍길동", gender="M", id="id1")
        p2 = Person(name="홍길순", gender="F", id="id2")

        index.add_person(p1)
        index.add_person(p2)

        # Both found
        results = index.search("홍")
        assert len(results) == 2

        # Remove one
        index.remove_person("id1")

        # Only one found
        results = index.search("홍")
        assert len(results) == 1
        assert results[0].name == "홍길순"

    def test_clear(self):
        """Clearing index removes all persons."""
        index = PersonSearchIndex()
        persons = [
            Person(name="홍길동", gender="M"),
            Person(name="김철수", gender="M"),
        ]
        index.index_persons(persons)

        assert index.size == 2

        index.clear()

        assert index.size == 0
        results = index.search("홍")
        assert results == []

    def test_person_with_empty_name(self):
        """Person with empty name is skipped."""
        index = PersonSearchIndex()
        person = Person(name="", gender="M")
        index.add_person(person)

        assert index.size == 0

    def test_get_stats(self):
        """Statistics are accurate."""
        index = PersonSearchIndex()
        persons = [
            Person(name="홍길동", gender="M"),
            Person(name="김철수", gender="M"),
        ]
        index.index_persons(persons)

        stats = index.get_stats()
        assert stats["indexed_persons"] == 2
        assert stats["unique_persons"] == 2
        assert stats["trie_nodes"] > 0  # At least root node

    def test_long_query(self):
        """Long query works correctly."""
        index = PersonSearchIndex()
        person = Person(name="Very Long Name For Testing", gender="M")
        index.add_person(person)

        results = index.search("Very Long Name")
        assert len(results) == 1

    def test_special_characters(self):
        """Names with special characters work."""
        index = PersonSearchIndex()
        person = Person(name="O'Brien-Smith", gender="M")
        index.add_person(person)

        results = index.search("o'brien")
        assert len(results) == 1

    def test_unicode_characters(self):
        """Unicode characters work correctly."""
        index = PersonSearchIndex()
        persons = [
            Person(name="José García", gender="M"),
            Person(name="François Dupont", gender="M"),
            Person(name="李明", gender="M"),
        ]

        for p in persons:
            index.add_person(p)

        results = index.search("josé")
        assert len(results) == 1
        assert results[0].name == "José García"

        results = index.search("李")
        assert len(results) == 1
        assert results[0].name == "李明"


class TestSearchIndexPerformance:
    """Performance tests for search index."""

    def test_large_dataset_indexing(self):
        """Index can handle large datasets."""
        index = PersonSearchIndex()
        persons = [
            Person(name=f"Person{i:05d}", gender="M")
            for i in range(1000)
        ]

        index.index_persons(persons)
        assert index.size == 1000

    def test_large_dataset_search_speed(self):
        """Search is fast on large datasets."""
        import time

        index = PersonSearchIndex()
        persons = [
            Person(name=f"Person{i:05d}", gender="M")
            for i in range(10000)
        ]
        index.index_persons(persons)

        start = time.perf_counter()
        results = index.search("Person0")
        duration = time.perf_counter() - start

        # Should complete in less than 10ms
        assert duration < 0.01
        # Should find all persons starting with "Person0"
        assert len(results) > 0
