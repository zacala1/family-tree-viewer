"""Person 모델 다중 사진 지원 회귀 가드.

핵심 보장:
- photo_path / photo_paths 양방향 동기화 (__post_init__)
- 구버전 JSON(photo_path만)을 신버전 모델로 로드 시 자동 마이그레이션
- 신버전 저장 시 양쪽 필드 모두 작성 (구버전 로더 호환)
- 추가/제거/primary 변경 helper 정확성
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person


class TestPostInitSync:
    def test_only_photo_path_promotes_to_list(self):
        """구버전 코드: photo_path만 set → photo_paths의 첫 항목으로 자동 승격."""
        p = Person(name="A", photo_path="photos/a.jpg")
        assert p.photo_paths == ["photos/a.jpg"]
        assert p.photo_path == "photos/a.jpg"
        assert p.primary_photo == "photos/a.jpg"

    def test_only_photo_paths_sets_alias(self):
        """신버전 코드: photo_paths만 set → photo_path 자동으로 첫 항목."""
        p = Person(name="A", photo_paths=["a.jpg", "b.jpg"])
        assert p.photo_path == "a.jpg"
        assert p.primary_photo == "a.jpg"

    def test_no_photo_both_empty(self):
        p = Person(name="A")
        assert p.photo_path is None
        assert p.photo_paths == []
        assert p.primary_photo is None

    def test_both_set_photo_paths_wins(self):
        """둘 다 set된 경우 photo_paths가 우선 (더 풍부한 신버전 데이터)."""
        p = Person(name="A", photo_path="old.jpg", photo_paths=["new1.jpg", "new2.jpg"])
        assert p.photo_path == "new1.jpg"  # alias가 첫 항목으로 정렬됨
        assert p.photo_paths == ["new1.jpg", "new2.jpg"]


class TestPhotoHelpers:
    def test_add_photo_appends(self):
        p = Person(name="A", photo_paths=["a.jpg"])
        p.add_photo("b.jpg")
        assert p.photo_paths == ["a.jpg", "b.jpg"]
        assert p.photo_path == "a.jpg"  # primary 변경 없음

    def test_add_photo_dedup(self):
        p = Person(name="A", photo_paths=["a.jpg"])
        p.add_photo("a.jpg")
        assert p.photo_paths == ["a.jpg"]

    def test_add_photo_empty_string_ignored(self):
        p = Person(name="A")
        p.add_photo("")
        assert p.photo_paths == []

    def test_add_photo_to_empty_sets_primary(self):
        p = Person(name="A")
        p.add_photo("first.jpg")
        assert p.photo_paths == ["first.jpg"]
        assert p.photo_path == "first.jpg"

    def test_remove_photo_not_primary(self):
        p = Person(name="A", photo_paths=["a.jpg", "b.jpg", "c.jpg"])
        p.remove_photo("b.jpg")
        assert p.photo_paths == ["a.jpg", "c.jpg"]
        assert p.photo_path == "a.jpg"

    def test_remove_primary_promotes_next(self):
        p = Person(name="A", photo_paths=["a.jpg", "b.jpg"])
        p.remove_photo("a.jpg")
        assert p.photo_paths == ["b.jpg"]
        assert p.photo_path == "b.jpg"  # 다음이 primary 승격

    def test_remove_last_clears_primary(self):
        p = Person(name="A", photo_paths=["only.jpg"])
        p.remove_photo("only.jpg")
        assert p.photo_paths == []
        assert p.photo_path is None

    def test_remove_missing_is_noop(self):
        p = Person(name="A", photo_paths=["a.jpg"])
        p.remove_photo("ghost.jpg")
        assert p.photo_paths == ["a.jpg"]

    def test_set_primary_moves_to_front(self):
        p = Person(name="A", photo_paths=["a.jpg", "b.jpg", "c.jpg"])
        p.set_primary_photo("c.jpg")
        assert p.photo_paths == ["c.jpg", "a.jpg", "b.jpg"]
        assert p.photo_path == "c.jpg"

    def test_set_primary_adds_if_missing(self):
        p = Person(name="A", photo_paths=["a.jpg"])
        p.set_primary_photo("new.jpg")
        assert p.photo_paths == ["new.jpg", "a.jpg"]


class TestSerializationCompat:
    """직렬화 라운드트립과 신구 형식 호환."""

    def test_legacy_only_photo_path_loads(self):
        """구버전 JSON (photo_path만) 로드."""
        data = {
            "name": "A",
            "photo_path": "old/single.jpg",
            # photo_paths 필드 없음 — 구버전
        }
        p = Person.from_dict(data)
        assert p.photo_path == "old/single.jpg"
        assert p.photo_paths == ["old/single.jpg"]

    def test_new_only_photo_paths_loads(self):
        """신버전 JSON (photo_paths만)도 동작."""
        data = {
            "name": "A",
            "photo_paths": ["new1.jpg", "new2.jpg"],
        }
        p = Person.from_dict(data)
        assert p.photo_paths == ["new1.jpg", "new2.jpg"]
        assert p.photo_path == "new1.jpg"

    def test_to_dict_writes_both_fields(self):
        """신버전 저장은 photo_path + photo_paths 모두 작성 (구버전 로더 호환)."""
        p = Person(name="A", photo_paths=["a.jpg", "b.jpg"])
        data = p.to_dict()
        assert "photo_path" in data
        assert "photo_paths" in data
        assert data["photo_path"] == "a.jpg"
        assert data["photo_paths"] == ["a.jpg", "b.jpg"]

    def test_roundtrip_multi_photo(self):
        original = Person(name="A", photo_paths=["a.jpg", "b.jpg", "c.jpg"])
        restored = Person.from_dict(original.to_dict())
        assert restored.photo_paths == ["a.jpg", "b.jpg", "c.jpg"]
        assert restored.photo_path == "a.jpg"

    def test_roundtrip_no_photo(self):
        original = Person(name="A")
        restored = Person.from_dict(original.to_dict())
        assert restored.photo_paths == []
        assert restored.photo_path is None

    def test_photo_paths_filters_empty_entries(self):
        """JSON 데이터에 빈 문자열·None이 섞여 있어도 정상 로드."""
        data = {"name": "A", "photo_paths": ["a.jpg", "", None, "b.jpg"]}
        p = Person.from_dict(data)
        assert p.photo_paths == ["a.jpg", "b.jpg"]

    def test_empty_photo_paths_falls_back_to_photo_path(self):
        """photo_paths=[] (빈 list)이지만 photo_path가 있으면 photo_path 사용."""
        data = {"name": "A", "photo_path": "old.jpg", "photo_paths": []}
        p = Person.from_dict(data)
        # 빈 list는 falsy 처리 → photo_path 단일 사용
        assert p.photo_paths == ["old.jpg"]


class TestBackwardCompatibility:
    """기존 photo_path 기반 코드가 새 모델과 충돌 없이 동작."""

    def test_legacy_setter_pattern_still_works(self):
        """기존 코드가 person.photo_path = X로 변경하는 패턴.

        photo_path attribute 직접 할당은 photo_paths를 자동 업데이트하지 않음
        (dataclass에는 property setter 없음). 마이그레이션 가이드 — 신코드는
        add_photo/set_primary_photo 사용.
        """
        p = Person(name="A", photo_path="initial.jpg")
        # 직접 할당
        p.photo_path = "new.jpg"
        # photo_paths는 자동 동기화 안 됨 — 의도된 동작 (post_init만 동기화)
        # 신코드는 set_primary_photo 사용해야 함
        assert p.photo_path == "new.jpg"

    def test_set_primary_photo_is_safe_replacement(self):
        """set_primary_photo가 photo_path 직접 할당의 안전한 대체."""
        p = Person(name="A", photo_path="initial.jpg")
        p.set_primary_photo("new.jpg")
        assert p.photo_path == "new.jpg"
        assert p.photo_paths == ["new.jpg", "initial.jpg"]
