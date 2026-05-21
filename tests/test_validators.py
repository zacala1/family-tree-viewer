"""Tests for validators module."""

import pytest
from src.models.validators import PersonValidator
from src.i18n import tr


class TestPersonValidator:
    """Test PersonValidator class."""

    def test_validate_name_success(self):
        """Test successful name validation."""
        valid, error = PersonValidator.validate_name("John Doe")
        assert valid is True
        assert error == ""

    def test_validate_name_empty(self):
        """Test empty name validation."""
        valid, error = PersonValidator.validate_name("")
        assert valid is False
        assert error == tr("error.name_required")

    def test_validate_name_too_long(self):
        """Test name that exceeds maximum length."""
        long_name = "A" * 101
        valid, error = PersonValidator.validate_name(long_name)
        assert valid is False
        assert error == tr("error.name_too_long")

    def test_validate_name_single_char(self):
        """Test single character name (minimum valid)."""
        valid, error = PersonValidator.validate_name("A")
        assert valid is True
        assert error == ""

    def test_validate_email_success(self):
        """Test successful email validation."""
        valid, error = PersonValidator.validate_email("user@example.com")
        assert valid is True
        assert error == ""

    def test_validate_email_empty(self):
        """Test empty email (should be valid)."""
        valid, error = PersonValidator.validate_email("")
        assert valid is True
        assert error == ""

    def test_validate_email_invalid_format(self):
        """Test invalid email format."""
        valid, error = PersonValidator.validate_email("invalid-email")
        assert valid is False
        assert error == tr("error.invalid_email")

    def test_validate_email_missing_at(self):
        """Test email without @ symbol."""
        valid, error = PersonValidator.validate_email("userexample.com")
        assert valid is False

    def test_validate_phone_success(self):
        """Test successful phone validation."""
        valid, error = PersonValidator.validate_phone("010-1234-5678")
        assert valid is True
        assert error == ""

    def test_validate_phone_international(self):
        """Test international phone format."""
        valid, error = PersonValidator.validate_phone("+82-10-1234-5678")
        assert valid is True
        assert error == ""

    def test_validate_phone_empty(self):
        """Test empty phone (should be valid)."""
        valid, error = PersonValidator.validate_phone("")
        assert valid is True
        assert error == ""

    def test_validate_phone_invalid_format(self):
        """Test invalid phone format."""
        valid, error = PersonValidator.validate_phone("abc-def")
        assert valid is False
        assert error == tr("error.invalid_phone")

    def test_validate_date_success(self):
        """Test successful date validation."""
        valid, error = PersonValidator.validate_date(1990, 5, 15)
        assert valid is True
        assert error == ""

    def test_validate_date_year_only(self):
        """Test year-only date."""
        valid, error = PersonValidator.validate_date(1990, None, None)
        assert valid is True
        assert error == ""

    def test_validate_date_year_out_of_range(self):
        """Test year outside valid range."""
        valid, error = PersonValidator.validate_date(1700, 5, 15)
        assert valid is False
        assert "1800" in error or "2100" in error

    def test_validate_date_invalid_month(self):
        """Test invalid month."""
        valid, error = PersonValidator.validate_date(1990, 13, 15)
        assert valid is False
        assert error == tr("error.invalid_month")

    def test_validate_date_invalid_day(self):
        """Test invalid day."""
        valid, error = PersonValidator.validate_date(1990, 2, 30)
        assert valid is False
        assert error == tr("error.invalid_day", month=2, max_day=28)

    def test_validate_date_leap_year(self):
        """Test February 29 on leap year."""
        valid, error = PersonValidator.validate_date(2000, 2, 29)
        assert valid is True
        assert error == ""

    def test_validate_date_non_leap_year(self):
        """Test February 29 on non-leap year."""
        valid, error = PersonValidator.validate_date(1900, 2, 29)
        assert valid is False

    def test_validate_lifespan_success(self):
        """Test successful lifespan validation."""
        valid, error = PersonValidator.validate_lifespan(1950, 1, 1, 2020, 12, 31)
        assert valid is True
        assert error == ""

    def test_validate_lifespan_death_before_birth(self):
        """Test death date before birth date."""
        valid, error = PersonValidator.validate_lifespan(1990, 5, 15, 1989, 3, 10)
        assert valid is False
        assert error == tr("error.death_before_birth")

    def test_validate_lifespan_exceeds_maximum(self):
        """Test lifespan exceeding maximum age."""
        valid, error = PersonValidator.validate_lifespan(1800, 1, 1, 2000, 1, 1)
        assert valid is False
        assert error == tr("error.age_exceeds_maximum")

    def test_validate_lifespan_none_values(self):
        """Test lifespan with None values (should be valid)."""
        valid, error = PersonValidator.validate_lifespan(None, None, None, None, None, None)
        assert valid is True
        assert error == ""

    def test_validate_all_success(self):
        """Test validate_all with all valid data."""
        valid, error = PersonValidator.validate_all(
            name="John Doe",
            email="john@example.com",
            phone="010-1234-5678",
            birth_year=1990,
            birth_month=5,
            birth_day=15
        )
        assert valid is True
        assert error == ""

    def test_validate_all_invalid_name(self):
        """Test validate_all with invalid name."""
        valid, error = PersonValidator.validate_all(
            name="",
            email="john@example.com"
        )
        assert valid is False
        assert error == tr("error.name_required")

    def test_validate_all_invalid_email(self):
        """Test validate_all with invalid email."""
        valid, error = PersonValidator.validate_all(
            name="John Doe",
            email="invalid-email"
        )
        assert valid is False
        assert error == tr("error.invalid_email")

    def test_validate_all_minimal_data(self):
        """Test validate_all with minimal required data."""
        valid, error = PersonValidator.validate_all(name="John")
        assert valid is True
        assert error == ""


class TestPersonValidatorEdgeCases:
    """Test edge cases for PersonValidator."""

    def test_name_whitespace_only(self):
        """Test name with only whitespace."""
        valid, error = PersonValidator.validate_name("   ")
        assert valid is False

    def test_email_with_plus(self):
        """Test email with + symbol (valid in RFC 5322)."""
        valid, error = PersonValidator.validate_email("user+tag@example.com")
        assert valid is True

    def test_phone_with_spaces(self):
        """Test phone with spaces."""
        valid, error = PersonValidator.validate_phone("+82 10 1234 5678")
        assert valid is True

    def test_date_year_2100(self):
        """Test maximum year boundary."""
        valid, error = PersonValidator.validate_date(2100, 12, 31)
        assert valid is True

    def test_date_year_1800(self):
        """Test minimum year boundary."""
        valid, error = PersonValidator.validate_date(1800, 1, 1)
        assert valid is True

    def test_lifespan_exactly_150_years(self):
        """Test lifespan of exactly 150 years."""
        valid, error = PersonValidator.validate_lifespan(1850, 1, 1, 2000, 1, 1)
        assert valid is True

    def test_lifespan_151_years(self):
        """Test lifespan of 151 years (should fail)."""
        valid, error = PersonValidator.validate_lifespan(1850, 1, 1, 2001, 1, 2)
        assert valid is False

    def test_unicode_korean_name(self):
        """한글 이름이 유효해야 함."""
        valid, error = PersonValidator.validate_name("홍길동")
        assert valid is True
        valid, error = PersonValidator.validate_name("김 영희")
        assert valid is True

    def test_unicode_emoji_name(self):
        """이모지가 포함된 이름도 빈 문자열이 아니면 허용 (정책 검증)."""
        # 현재 정책: 빈 문자열만 거부. 이모지 허용. 이 동작이 변하면 의도적 변경 필요.
        valid, error = PersonValidator.validate_name("👨‍👩‍👧‍👦")
        assert valid is True

    def test_unicode_apostrophe_name(self):
        """O'Brien 같은 영문 이름의 어포스트로피 허용."""
        valid, error = PersonValidator.validate_name("O'Brien")
        assert valid is True

    def test_name_none_raises(self):
        """None 이름은 명확히 실패 처리되어야 (AttributeError 아닌 invalid)."""
        # 현재 구현: `not name` 체크가 None을 잡아 invalid 반환
        valid, error = PersonValidator.validate_name(None)
        assert valid is False
