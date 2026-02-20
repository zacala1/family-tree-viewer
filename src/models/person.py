"""Person model for Family Tree application."""

from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any
import uuid

from ..utils.date_formatter import format_date, format_lifespan
from ..config import DEFAULT_NATIONALITY
from .event import Event


@dataclass
class Person:
    """Represents a person in the family tree."""

    # 기본 정보
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    gender: Literal["M", "F"] = "M"

    # 생년월일
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    is_lunar_birth: bool = False  # 음력 여부

    # 사망일
    death_year: Optional[int] = None
    death_month: Optional[int] = None
    death_day: Optional[int] = None
    is_lunar_death: bool = False

    # 추가 정보
    birth_place: str = ""  # 출생지
    current_address: str = ""  # 현주소
    nationality: str = field(default_factory=lambda: DEFAULT_NATIONALITY)  # 국적
    occupation: str = ""  # 직업
    education: str = ""  # 학력
    phone: str = ""  # 연락처
    email: str = ""  # 이메일
    notes: str = ""  # 메모

    # 사진
    photo_path: Optional[str] = None

    # 이벤트 (생애 주요 사건)
    events: List[Event] = field(default_factory=list)

    # 관계 (ID 참조)
    father_id: Optional[str] = None
    mother_id: Optional[str] = None
    spouse_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)

    # 세대 정보 (그래프 레이아웃용)
    generation: int = 0

    @property
    def birth_date_str(self) -> str:
        """생년월일 문자열 반환."""
        return format_date(self.birth_year, self.birth_month, self.birth_day, self.is_lunar_birth)

    @property
    def death_date_str(self) -> str:
        """사망일 문자열 반환."""
        return format_date(self.death_year, self.death_month, self.death_day, self.is_lunar_death)

    @property
    def lifespan_str(self) -> str:
        """생몰년 문자열 반환."""
        return format_lifespan(self.birth_year, self.death_year)

    @property
    def is_alive(self) -> bool:
        """생존 여부."""
        return self.death_year is None

    def get_direct_family_ids(self) -> List[str]:
        """직계 가족 ID 목록 반환 (부모, 배우자, 자녀)."""
        family_ids = []
        if self.father_id:
            family_ids.append(self.father_id)
        if self.mother_id:
            family_ids.append(self.mother_id)
        family_ids.extend(self.spouse_ids)
        family_ids.extend(self.children_ids)
        return family_ids

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "birth_year": self.birth_year,
            "birth_month": self.birth_month,
            "birth_day": self.birth_day,
            "is_lunar_birth": self.is_lunar_birth,
            "death_year": self.death_year,
            "death_month": self.death_month,
            "death_day": self.death_day,
            "is_lunar_death": self.is_lunar_death,
            "birth_place": self.birth_place,
            "current_address": self.current_address,
            "nationality": self.nationality,
            "occupation": self.occupation,
            "education": self.education,
            "phone": self.phone,
            "email": self.email,
            "notes": self.notes,
            "photo_path": self.photo_path,
            "events": [event.to_dict() for event in self.events],
            "father_id": self.father_id,
            "mother_id": self.mother_id,
            "spouse_ids": list(self.spouse_ids),
            "children_ids": list(self.children_ids),
            "generation": self.generation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Person":
        """딕셔너리에서 Person 객체 생성."""
        import os

        # photo_path 보안 검증
        photo_path = data.get("photo_path")
        if photo_path:
            # 경로 traversal 방지: 파일명만 추출
            photo_path = os.path.basename(photo_path)

        # events 역직렬화
        events_data = data.get("events", [])
        events = [Event.from_dict(event_dict) for event_dict in events_data]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            gender=data.get("gender", "M"),
            birth_year=data.get("birth_year"),
            birth_month=data.get("birth_month"),
            birth_day=data.get("birth_day"),
            is_lunar_birth=data.get("is_lunar_birth", False),
            death_year=data.get("death_year"),
            death_month=data.get("death_month"),
            death_day=data.get("death_day"),
            is_lunar_death=data.get("is_lunar_death", False),
            birth_place=data.get("birth_place", ""),
            current_address=data.get("current_address", ""),
            nationality=data.get("nationality", ""),
            occupation=data.get("occupation", ""),
            education=data.get("education", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            notes=data.get("notes", ""),
            photo_path=photo_path,
            events=events,
            father_id=data.get("father_id"),
            mother_id=data.get("mother_id"),
            spouse_ids=data.get("spouse_ids", []),
            children_ids=data.get("children_ids", []),
            generation=data.get("generation", 0),
        )
