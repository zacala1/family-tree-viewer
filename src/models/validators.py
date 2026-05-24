"""Validation logic for Person data (Business Logic Layer).

This module separates validation rules from the UI layer,
making them reusable and testable independently.
"""

import re
from typing import Tuple, Optional
from datetime import date
import calendar

from ..config import (
    MIN_NAME_LENGTH,
    MAX_NAME_LENGTH,
    EMAIL_PATTERN,
    PHONE_PATTERN,
    YEAR_MIN,
    YEAR_MAX,
    MONTH_MIN,
    MONTH_MAX,
    DAY_MIN,
    DAY_MAX,
    MAX_AGE_AT_DEATH,
)
from ..i18n import tr


class PersonValidator:
    """Validator for Person data with business rules."""

    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate person name.

        Args:
            name: Name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or len(name.strip()) < MIN_NAME_LENGTH:
            return False, tr("error.name_required")

        if len(name) > MAX_NAME_LENGTH:
            return False, tr("error.name_too_long")

        return True, ""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not email.strip():
            return True, ""

        if not re.match(EMAIL_PATTERN, email):
            return False, tr("error.invalid_email")

        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone or not phone.strip():
            return True, ""

        if not re.match(PHONE_PATTERN, phone):
            return False, tr("error.invalid_phone")

        return True, ""

    @staticmethod
    def validate_date(
        year: Optional[int],
        month: Optional[int],
        day: Optional[int]
    ) -> Tuple[bool, str]:
        """Validate date components.

        Args:
            year: Year value (or None)
            month: Month value (or None)
            day: Day value (or None)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if year is None:
            return True, ""

        if year < YEAR_MIN or year > YEAR_MAX:
            return False, tr("error.date_out_of_range", min_year=YEAR_MIN, max_year=YEAR_MAX)

        if day is not None and month is None:
            return False, tr("error.day_without_month", fallback="Day requires month to be set")

        if month is not None:
            if month < 1 or month > 12:
                return False, tr("error.invalid_month")

            if day is not None:
                if day < 1:
                    return False, tr("error.invalid_day", month=month, max_day=31)

                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    return False, tr("error.invalid_day", month=month, max_day=max_day)

        return True, ""

    @staticmethod
    def validate_lifespan(
        birth_year: Optional[int],
        birth_month: Optional[int],
        birth_day: Optional[int],
        death_year: Optional[int],
        death_month: Optional[int],
        death_day: Optional[int]
    ) -> Tuple[bool, str]:
        """Validate birth and death dates relationship.

        Args:
            birth_year, birth_month, birth_day: Birth date components
            death_year, death_month, death_day: Death date components

        Returns:
            Tuple of (is_valid, error_message)
        """
        if birth_year is None or death_year is None:
            return True, ""

        try:
            birth_date = date(
                birth_year,
                birth_month or 1,
                birth_day or 1
            )

            d_month = death_month or 12
            d_max_day = calendar.monthrange(death_year, d_month)[1]
            d_day = min(death_day or d_max_day, d_max_day)
            death_date = date(death_year, d_month, d_day)

            if death_date < birth_date:
                return False, tr("error.death_before_birth")

            age_years = death_year - birth_year
            if age_years > MAX_AGE_AT_DEATH:
                return False, tr("error.age_exceeds_maximum")

        except ValueError:
            return False, tr("error.invalid_date_combination", fallback="Invalid date values")

        return True, ""

    @staticmethod
    def validate_all(
        name: str,
        email: str = "",
        phone: str = "",
        birth_year: Optional[int] = None,
        birth_month: Optional[int] = None,
        birth_day: Optional[int] = None,
        death_year: Optional[int] = None,
        death_month: Optional[int] = None,
        death_day: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Validate all person data at once.

        Args:
            name: Person name
            email: Email address (optional)
            phone: Phone number (optional)
            birth_year, birth_month, birth_day: Birth date components
            death_year, death_month, death_day: Death date components

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
            If invalid, returns first error encountered
        """
        valid, error = PersonValidator.validate_name(name)
        if not valid:
            return False, error

        valid, error = PersonValidator.validate_email(email)
        if not valid:
            return False, error

        valid, error = PersonValidator.validate_phone(phone)
        if not valid:
            return False, error

        valid, error = PersonValidator.validate_date(birth_year, birth_month, birth_day)
        if not valid:
            return False, error

        valid, error = PersonValidator.validate_date(death_year, death_month, death_day)
        if not valid:
            return False, error

        valid, error = PersonValidator.validate_lifespan(
            birth_year, birth_month, birth_day,
            death_year, death_month, death_day
        )
        if not valid:
            return False, error

        return True, ""


class EventValidator:
    """Validator for Event data — title, type, date.

    Mirrors PersonValidator's static-method pattern so UI code never
    inlines validation rules.
    """

    @staticmethod
    def validate_title(title: str) -> Tuple[bool, str]:
        """Event title — required, length-capped (same MAX_NAME_LENGTH as Person)."""
        if not title or not title.strip():
            return False, tr("error.event_title_required")
        if len(title) > MAX_NAME_LENGTH:
            return False, tr("error.name_too_long")
        return True, ""

    @staticmethod
    def validate_event_type(event_type: str) -> Tuple[bool, str]:
        """Event type must be one of the canonical EVENT_TYPES."""
        from .event import EVENT_TYPES
        if event_type not in EVENT_TYPES:
            return False, tr(
                "error.invalid_event_type",
                fallback=f"Invalid event type: {event_type}",
            )
        return True, ""

    @staticmethod
    def validate_all(
        title: str,
        event_type: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Validate the full event payload — first failure short-circuits."""
        valid, error = EventValidator.validate_title(title)
        if not valid:
            return False, error

        valid, error = EventValidator.validate_event_type(event_type)
        if not valid:
            return False, error

        # 날짜는 PersonValidator의 범위 검증을 재사용
        valid, error = PersonValidator.validate_date(year, month, day)
        if not valid:
            return False, error

        return True, ""
