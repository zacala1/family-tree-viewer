"""Tests for date_formatter utility."""
import unittest
from src.utils.date_formatter import format_date, format_lifespan


class TestDateFormatter(unittest.TestCase):
    """Test cases for date formatting utilities."""

    def test_format_date_full(self):
        """Test formatting with year, month, and day."""
        result = format_date(1985, 3, 15, False)
        self.assertEqual(result, "1985.03.15")

    def test_format_date_lunar(self):
        """Test formatting with lunar calendar indicator."""
        result = format_date(1985, 3, 15, True)
        self.assertEqual(result, "1985.03.15 (음력)")

    def test_format_date_year_only(self):
        """Test formatting with year only."""
        result = format_date(1985, None, None, False)
        self.assertEqual(result, "1985")

    def test_format_date_year_month(self):
        """Test formatting with year and month."""
        result = format_date(1985, 3, None, False)
        self.assertEqual(result, "1985.03")

    def test_format_date_no_year(self):
        """Test formatting with no year returns empty string."""
        result = format_date(None, 3, 15, False)
        self.assertEqual(result, "")

    def test_format_lifespan_both_dates(self):
        """Test lifespan formatting with birth and death years."""
        result = format_lifespan(1950, 2020)
        self.assertEqual(result, "1950 - 2020")

    def test_format_lifespan_birth_only(self):
        """Test lifespan formatting with birth year only (living person)."""
        result = format_lifespan(1985, None)
        self.assertEqual(result, "1985 -")

    def test_format_lifespan_no_birth(self):
        """Test lifespan formatting with no birth year returns empty string."""
        result = format_lifespan(None, 2020)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
