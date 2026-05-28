"""Tests for product input validation rules."""

import unittest

from src.i18n import tr
from src.models.validators import PersonValidator


class TestInputValidation(unittest.TestCase):
    """Validate through the production PersonValidator, not copied rules."""

    def test_email_validation_valid(self):
        """Valid email formats accepted by product validator."""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "user_name@example-domain.com",
            "",
        ]

        for email in valid_emails:
            with self.subTest(email=email):
                valid, error = PersonValidator.validate_email(email)
                self.assertTrue(valid)
                self.assertEqual(error, "")

    def test_email_validation_invalid(self):
        """Invalid email formats rejected by product validator."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
            "user name@example.com",
        ]

        for email in invalid_emails:
            with self.subTest(email=email):
                valid, error = PersonValidator.validate_email(email)
                self.assertFalse(valid)
                self.assertEqual(error, tr("error.invalid_email"))

    def test_date_range_validation(self):
        """Date component checks use the same validator as save/edit flows."""
        valid_dates = [
            (1990, None, None),
            (1990, 1, None),
            (2000, 2, 29),
            (2100, 12, 31),
        ]
        invalid_dates = [
            (1700, 1, 1),
            (1990, 0, 1),
            (1990, 13, 1),
            (1990, None, 1),
            (1900, 2, 29),
            (1990, 4, 31),
        ]

        for year, month, day in valid_dates:
            with self.subTest(date=(year, month, day)):
                valid, error = PersonValidator.validate_date(year, month, day)
                self.assertTrue(valid)
                self.assertEqual(error, "")

        for year, month, day in invalid_dates:
            with self.subTest(date=(year, month, day)):
                valid, error = PersonValidator.validate_date(year, month, day)
                self.assertFalse(valid)
                self.assertNotEqual(error, "")

    def test_death_after_birth_validation(self):
        """Lifespan validation rejects death dates before birth dates."""
        valid, error = PersonValidator.validate_lifespan(1950, 1, 1, 2020, 12, 31)
        self.assertTrue(valid)
        self.assertEqual(error, "")

        valid, error = PersonValidator.validate_lifespan(1985, 3, 1, 1985, 5, 1)
        self.assertTrue(valid)
        self.assertEqual(error, "")

        valid, error = PersonValidator.validate_lifespan(1990, 5, 15, 1989, 3, 10)
        self.assertFalse(valid)
        self.assertEqual(error, tr("error.death_before_birth"))


if __name__ == "__main__":
    unittest.main()
