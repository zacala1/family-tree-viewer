"""Configuration constants for Family Tree application.

This module centralizes all configuration values used throughout the application,
making them easier to maintain and modify.
"""

# =============================================================================
# Data Model Limits
# =============================================================================

# Maximum number of persons allowed in a family tree
MAX_PERSONS = 50000

# Maximum depth for cycle detection (generations)
MAX_CYCLE_DEPTH = 50


# =============================================================================
# Tree Canvas Layout
# =============================================================================

# Card dimensions for person nodes in the tree view
CARD_WIDTH = 120
CARD_HEIGHT = 80

# Spacing between cards
CARD_SPACING_X = 40
CARD_SPACING_Y = 100

# Spacing between spouse cards
SPOUSE_SPACING = 30


# =============================================================================
# Date Input Validation
# =============================================================================

# Valid year range for birth/death dates
YEAR_MIN = 1800
YEAR_MAX = 2100

# Valid month range (0 = unknown, 1-12 = January-December)
MONTH_MIN = 0
MONTH_MAX = 12

# Valid day range (0 = unknown, 1-31 = day of month)
DAY_MIN = 0
DAY_MAX = 31


# =============================================================================
# Text Input Length Limits
# =============================================================================

# Person name field
MAX_NAME_LENGTH = 100

# Standard text fields (address, occupation, education, etc.)
MAX_TEXT_LENGTH = 500

# Email field
MAX_EMAIL_LENGTH = 100

# Phone number field
MAX_PHONE_LENGTH = 50

# Notes/memo field
MAX_NOTES_LENGTH = 5000


# =============================================================================
# File Handler Limits
# =============================================================================

# Maximum file size for GEDCOM imports (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Maximum number of lines in GEDCOM file
MAX_GEDCOM_LINES = 1000000


# =============================================================================
# Animation Settings
# =============================================================================

# Duration for scroll/zoom animations (milliseconds)
ANIMATION_DURATION = 300


# =============================================================================
# HTML Sanitization
# =============================================================================

# Maximum length for HTML-sanitized text to prevent XSS attacks
HTML_SANITIZE_MAX_LENGTH = 200


# =============================================================================
# Photo Settings
# =============================================================================

# Directory for storing person photos (relative to project root)
PHOTOS_FOLDER = "data/photos"

# Application root directory (for resolving relative paths)
import os as _os
APP_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

# Thumbnail size for photo display in detail panel (pixels)
PHOTO_THUMBNAIL_SIZE = 150

# Supported image file formats (immutable tuple)
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

# Maximum photo file size (5 MB)
MAX_PHOTO_SIZE = 5 * 1024 * 1024


# =============================================================================
# Search Settings
# =============================================================================

# Maximum search query length (prevent performance issues)
MAX_SEARCH_QUERY_LENGTH = 100


# =============================================================================
# Default Values
# =============================================================================

# Default nationality for new persons
DEFAULT_NATIONALITY = "한국"


# =============================================================================
# Validation Rules
# =============================================================================

# Email validation pattern (RFC 5322 simplified)
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Phone number validation (allows various formats)
# Accepts: 010-1234-5678, 02-123-4567, +82-10-1234-5678, etc.
PHONE_PATTERN = r"^[\+\d][\d\-\s\(\)]{7,48}$"

# Name validation rules
MIN_NAME_LENGTH = 1  # At least 1 character required

# Date validation rules
MAX_AGE_AT_DEATH = 150  # Reasonable maximum human lifespan

# Required field markers
REQUIRED_FIELDS = ["name"]  # Fields that cannot be empty


# =============================================================================
# Auto-Backup Settings
# =============================================================================

# Backup interval in minutes
AUTO_BACKUP_INTERVAL_MINUTES = 5

# Maximum number of backup files to keep
MAX_BACKUP_COUNT = 10

# Backup directory (relative to user home)
BACKUP_DIR = ".familytree/backups"


# =============================================================================
# Error Messages
# =============================================================================

# Validation error messages (English - can be overridden by i18n)
ERROR_MESSAGES = {
    "name_required": "Name is required",
    "name_too_long": f"Name must be {MAX_NAME_LENGTH} characters or less",
    "invalid_email": "Invalid email format (example: user@example.com)",
    "invalid_phone": "Invalid phone number format",
    "date_out_of_range": "Date must be between {min_year} and {max_year}",
    "invalid_month": "Month must be between 1 and 12",
    "invalid_day": "Day must be between 1 and {max_day} for month {month}",
    "death_before_birth": "Death date cannot be before birth date",
    "age_exceeds_maximum": f"Age at death cannot exceed {MAX_AGE_AT_DEATH} years",
    "file_too_large": "File is too large (max {max_size} MB)",
    "file_not_found": "File not found: {path}",
    "permission_denied": "Permission denied: {path}",
    "unsupported_format": "Unsupported file format: {format}",
}
