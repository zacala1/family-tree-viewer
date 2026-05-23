"""Relationship model for Family Tree application."""

from enum import Enum
from typing import Optional, Dict, Any
import uuid


class RelationType(Enum):
    """관계 유형."""

    PARENT_CHILD = "parent_child"  # 부모-자녀
    SPOUSE = "spouse"  # 배우자


class RelationshipRequestType:
    """관계 추가 요청 타입 (매직 스트링 방지)."""

    PARENT = "parent"
    SPOUSE = "spouse"
    CHILD = "child"


class Relationship:
    """두 사람 간의 관계를 나타냄."""

    __slots__ = (
        "id",
        "person1_id",
        "person2_id",
        "rel_type",
        "marriage_year",
        "marriage_month",
        "marriage_day",
        "is_lunar_marriage",
        "divorce_year",
        "divorce_month",
        "divorce_day",
    )

    def __init__(
        self,
        person1_id: str,
        person2_id: str,
        rel_type: RelationType,
        id: Optional[str] = None,
        marriage_year: Optional[int] = None,
        marriage_month: Optional[int] = None,
        marriage_day: Optional[int] = None,
        is_lunar_marriage: bool = False,
        divorce_year: Optional[int] = None,
        divorce_month: Optional[int] = None,
        divorce_day: Optional[int] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.person1_id = person1_id
        self.person2_id = person2_id
        self.rel_type = rel_type
        self.marriage_year = marriage_year
        self.marriage_month = marriage_month
        self.marriage_day = marriage_day
        self.is_lunar_marriage = is_lunar_marriage
        self.divorce_year = divorce_year
        self.divorce_month = divorce_month
        self.divorce_day = divorce_day

    def __repr__(self) -> str:
        return (
            f"Relationship(id={self.id!r}, person1_id={self.person1_id!r}, "
            f"person2_id={self.person2_id!r}, rel_type={self.rel_type})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Relationship):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def is_divorced(self) -> bool:
        """이혼 여부."""
        return self.divorce_year is not None

    def is_valid_marriage_order(self) -> bool:
        """결혼일 ≤ 이혼일 검증.

        - 둘 다 None이거나 한쪽만 있으면 True (검증 불가)
        - 년/월/일을 튜플로 비교 (None은 0 또는 12/31로 보수적 처리)
        """
        if self.marriage_year is None or self.divorce_year is None:
            return True
        # 결혼은 가장 늦은 가능 시점, 이혼은 가장 이른 가능 시점으로 비교 — 의문 시 통과
        marriage = (
            self.marriage_year,
            self.marriage_month or 12,
            self.marriage_day or 31,
        )
        divorce = (
            self.divorce_year,
            self.divorce_month or 1,
            self.divorce_day or 1,
        )
        return marriage <= divorce

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "person1_id": self.person1_id,
            "person2_id": self.person2_id,
            "rel_type": self.rel_type.value,
            "marriage_year": self.marriage_year,
            "marriage_month": self.marriage_month,
            "marriage_day": self.marriage_day,
            "is_lunar_marriage": self.is_lunar_marriage,
            "divorce_year": self.divorce_year,
            "divorce_month": self.divorce_month,
            "divorce_day": self.divorce_day,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """딕셔너리에서 Relationship 객체 생성."""
        # Validate required fields to prevent KeyError on corrupted data
        person1_id = data.get("person1_id")
        person2_id = data.get("person2_id")
        rel_type_str = data.get("rel_type")
        if not person1_id or not person2_id or not rel_type_str:
            raise ValueError(
                f"Missing required fields in relationship data: "
                f"person1_id={person1_id}, person2_id={person2_id}, rel_type={rel_type_str}"
            )
        try:
            rel_type = RelationType(rel_type_str)
        except ValueError:
            raise ValueError(
                f"Invalid relationship type: '{rel_type_str}'. "
                f"Valid types: {[e.value for e in RelationType]}"
            )
        def _safe_int(val):
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        return cls(
            id=data.get("id"),
            person1_id=person1_id,
            person2_id=person2_id,
            rel_type=rel_type,
            marriage_year=_safe_int(data.get("marriage_year")),
            marriage_month=_safe_int(data.get("marriage_month")),
            marriage_day=_safe_int(data.get("marriage_day")),
            is_lunar_marriage=data.get("is_lunar_marriage", False),
            divorce_year=_safe_int(data.get("divorce_year")),
            divorce_month=_safe_int(data.get("divorce_month")),
            divorce_day=_safe_int(data.get("divorce_day")),
        )
