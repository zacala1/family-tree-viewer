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

    # 사진 — 다중 사진 지원
    # photo_path: 단일 사진 (deprecated alias; primary_photo와 동의어, 하위 호환용)
    # photo_paths: 전체 사진 목록. UI는 첫 항목(primary)을 기본 표시.
    photo_path: Optional[str] = None
    photo_paths: List[str] = field(default_factory=list)

    # 이벤트 (생애 주요 사건)
    events: List[Event] = field(default_factory=list)

    # 관계 (ID 참조)
    father_id: Optional[str] = None
    mother_id: Optional[str] = None
    spouse_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)

    # 세대 정보 (그래프 레이아웃용)
    generation: int = 0

    def __post_init__(self):
        """dataclass 초기화 후 photo_path ↔ photo_paths 양방향 동기화.

        - 구버전 코드/JSON: photo_path만 set → photo_paths의 첫 항목으로 자동 승격
        - 신버전 코드: photo_paths만 set → photo_path를 첫 항목으로 set (구버전 코드 호환)
        둘 다 set된 경우 photo_paths가 우선 (신버전 데이터가 더 풍부).
        """
        if self.photo_paths:
            # 신버전 우선 — photo_path는 첫 사진 alias로 정렬
            self.photo_path = self.photo_paths[0]
        elif self.photo_path:
            # 구버전 fallback — photo_path 단일을 list의 첫 항목으로
            self.photo_paths = [self.photo_path]

    @property
    def primary_photo(self) -> Optional[str]:
        """주 사진 (UI 카드/썸네일 기본 표시용). 없으면 None."""
        return self.photo_paths[0] if self.photo_paths else None

    def add_photo(self, path: str) -> None:
        """사진 추가 (중복 제외). primary는 변경하지 않음."""
        if path and path not in self.photo_paths:
            self.photo_paths.append(path)
            self.photo_path = self.photo_paths[0]

    def remove_photo(self, path: str) -> None:
        """사진 제거. 제거된 사진이 primary였다면 다음 사진이 primary로 승격."""
        if path in self.photo_paths:
            self.photo_paths.remove(path)
            self.photo_path = self.photo_paths[0] if self.photo_paths else None

    def set_primary_photo(self, path: str) -> None:
        """주 사진 변경 — path를 photo_paths의 맨 앞으로 이동.

        path가 list에 없으면 새로 추가하면서 맨 앞에 위치.
        """
        if not path:
            return
        if path in self.photo_paths:
            self.photo_paths.remove(path)
        self.photo_paths.insert(0, path)
        self.photo_path = path

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
            # 사진 — 신구 필드 모두 작성 (구버전 로더 호환)
            "photo_path": self.photo_path,
            "photo_paths": list(self.photo_paths),
            "events": [event.to_dict() for event in self.events],
            "father_id": self.father_id,
            "mother_id": self.mother_id,
            "spouse_ids": list(self.spouse_ids),
            "children_ids": list(self.children_ids),
            "generation": self.generation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Person":
        """딕셔너리에서 Person 객체 생성.

        사진 마이그레이션:
        - 신버전 JSON: photo_paths 사용 (photo_path도 있으면 무시 — __post_init__이 정렬)
        - 구버전 JSON: photo_paths 없음, photo_path만 → __post_init__이 list 승격
        """
        # photo_path: preserve relative path as saved (photo_manager handles security)
        photo_path = data.get("photo_path")
        photo_paths_data = data.get("photo_paths")
        # 신버전 우선; 비어있거나 누락이면 구버전 photo_path만 사용 (post_init이 승격)
        if isinstance(photo_paths_data, list) and photo_paths_data:
            # 빈 항목·None 필터링
            photo_paths = [p for p in photo_paths_data if p]
        else:
            photo_paths = []

        # Validate gender
        gender = data.get("gender", "M")
        if gender not in ("M", "F"):
            from ..utils.logger import warning
            warning(
                f"Person.from_dict: Invalid gender '{gender}' for "
                f"'{data.get('name', 'unknown')}' (id={data.get('id', 'unknown')}). "
                f"Defaulting to 'M'."
            )
            gender = "M"

        # events 역직렬화
        events_data = data.get("events", [])
        events = [Event.from_dict(event_dict) for event_dict in events_data]

        def _safe_int(val: Any) -> Optional[int]:
            """JSON에서 읽은 값을 안전하게 int 또는 None으로 변환."""
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            gender=gender,
            birth_year=_safe_int(data.get("birth_year")),
            birth_month=_safe_int(data.get("birth_month")),
            birth_day=_safe_int(data.get("birth_day")),
            is_lunar_birth=data.get("is_lunar_birth", False),
            death_year=_safe_int(data.get("death_year")),
            death_month=_safe_int(data.get("death_month")),
            death_day=_safe_int(data.get("death_day")),
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
            photo_paths=photo_paths,
            events=events,
            father_id=data.get("father_id"),
            mother_id=data.get("mother_id"),
            spouse_ids=list(data.get("spouse_ids", [])),
            children_ids=list(data.get("children_ids", [])),
            generation=data.get("generation", 0),
        )
