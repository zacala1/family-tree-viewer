"""Event model for tracking life events and milestones."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
import uuid


EventType = Literal[
    "birth",
    "death",
    "marriage",
    "divorce",
    "graduation",
    "employment",
    "retirement",
    "relocation",
    "achievement",
    "other"
]


@dataclass
class Event:
    """Represents a life event or milestone for a person."""

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Event details
    title: str = ""
    description: str = ""
    event_type: EventType = "other"

    # Date information
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    is_lunar: bool = False

    # Location
    location: str = ""

    # Related person ID (owner of this event)
    person_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "is_lunar": self.is_lunar,
            "location": self.location,
            "person_id": self.person_id,
        }

    # 유효한 event_type 값 목록
    _VALID_EVENT_TYPES = {
        "birth", "death", "marriage", "divorce", "graduation",
        "employment", "retirement", "relocation", "achievement", "other"
    }

    @staticmethod
    def _safe_int(val) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        raw_type = data.get("event_type", "other")
        event_type = raw_type if raw_type in cls._VALID_EVENT_TYPES else "other"
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            event_type=event_type,
            year=cls._safe_int(data.get("year")),
            month=cls._safe_int(data.get("month")),
            day=cls._safe_int(data.get("day")),
            is_lunar=data.get("is_lunar", False),
            location=data.get("location", ""),
            person_id=data.get("person_id"),
        )

    @property
    def date_str(self) -> str:
        """Get formatted date string."""
        from ..utils.date_formatter import format_date
        return format_date(self.year, self.month, self.day, self.is_lunar)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.title} ({self.date_str})"
