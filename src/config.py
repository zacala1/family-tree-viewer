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

# Easing curve type for animations (options: Linear, InOutQuad, OutCubic, etc.)
# See PyQt6.QtCore.QEasingCurve.Type for all options
ANIMATION_EASING = "OutCubic"


# =============================================================================
# HTML Sanitization
# =============================================================================

# Maximum length for HTML-sanitized text to prevent XSS attacks
HTML_SANITIZE_MAX_LENGTH = 200
