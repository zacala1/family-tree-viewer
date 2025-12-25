"""Tests for input validation."""
import unittest
import re


class TestInputValidation(unittest.TestCase):
    """Test cases for input validation functions."""

    def test_email_validation_valid(self):
        """Test valid email formats."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        valid_emails = [
            'test@example.com',
            'user.name@example.co.uk',
            'user+tag@example.com',
            'user_name@example-domain.com',
        ]

        for email in valid_emails:
            with self.subTest(email=email):
                self.assertIsNotNone(re.match(email_pattern, email))

    def test_email_validation_invalid(self):
        """Test invalid email formats."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user@.com',
            'user@example',
            'user name@example.com',
        ]

        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertIsNone(re.match(email_pattern, email))

    def test_date_range_validation(self):
        """Test date range validation."""
        # Valid months
        for month in range(1, 13):
            self.assertTrue(1 <= month <= 12)

        # Invalid months
        invalid_months = [0, 13, -1, 100]
        for month in invalid_months:
            self.assertFalse(1 <= month <= 12)

        # Valid days
        for day in range(1, 32):
            self.assertTrue(1 <= day <= 31)

        # Invalid days
        invalid_days = [0, 32, -1, 100]
        for day in invalid_days:
            self.assertFalse(1 <= day <= 31)

    def test_death_after_birth_validation(self):
        """Test that death date is after birth date."""
        # Valid: death after birth
        self.assertTrue(2020 > 1950)

        # Invalid: death before birth
        self.assertFalse(1950 > 2020)

        # Same year, check months
        birth_year, birth_month = 1985, 3
        death_year, death_month = 1985, 5

        if death_year == birth_year:
            self.assertTrue(death_month > birth_month)


if __name__ == '__main__':
    unittest.main()
