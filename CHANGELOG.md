# Changelog

All notable changes to the Family Tree Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Structured Logging System**: JSON-formatted logs for analysis and debugging
  - JSONFormatter class for structured log output
  - Console: Human-readable format (INFO+)
  - File: JSON format at ~/.familytree/logs/familytree.log (DEBUG+)
  - log_action() for structured action logging with context
  - set_log_level() for dynamic log level configuration
- **Performance Monitoring System**: Built-in profiling and metrics collection
  - PerformanceMonitor class for tracking operation durations
  - @profile() decorator for automatic function timing
  - measure_time() context manager for block timing
  - MemoryTracker for memory usage analysis
  - Automatic warnings for slow operations (>0.5s)
- **Undo/Redo System**: Full 50-level history with Command pattern
  - UndoRedoManager with undo/redo stack management
  - AddPersonCommand, DeletePersonCommand, UpdatePersonCommand
  - AddRelationshipCommand for parent-child relationships
  - Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Y (redo)
- **Event System**: Life event tracking and timeline visualization
  - Event model with 10 event types (birth, death, marriage, divorce, etc.)
  - EventDialog for adding/editing events
  - TimelineView for chronological visualization
  - Event tab in detail panel
- **Magic String Elimination**: RelationshipRequestType constants class
  - PARENT, SPOUSE, CHILD constants
  - Type-safe relationship request handling
  - IDE autocomplete support
- **Enhanced Thread Safety**: Complete RLock protection in FamilyTree
  - Protected all data access methods with RLock
  - Thread-safe is_modified, mark_modified, mark_saved
  - Thread-safe relationship queries
- **Improved Cycle Detection**: BFS-based algorithm with visited set
  - Eliminates false positives from depth-based detection
  - Supports legitimate deep family trees (>50 generations)
  - Warning logged when exceeding MAX_CYCLE_DEPTH, but continues checking
- **API Documentation**: Comprehensive docs/API.md covering all components
  - Complete API reference for models, utilities, patterns
  - Code examples and usage patterns
  - Thread safety documentation
  - Security considerations
- **Configuration Constants**: Centralized all hardcoded values in src/config.py
  - Layout constants (card dimensions, spacing)
  - Date validation ranges (year, month, day)
  - Text input length limits (name, email, phone, notes, etc.)
  - File handler limits (max file size, max GEDCOM lines)
  - Animation settings (duration, easing)
  - HTML sanitization limits
- **Validation Rules & Error Messages**: Comprehensive validation configuration
  - EMAIL_PATTERN: RFC 5322-compliant email validation
  - PHONE_PATTERN: Flexible phone number validation (supports international formats)
  - MIN_NAME_LENGTH, MAX_NAME_LENGTH_UNICODE: Name length constraints
  - MIN_AGE_AT_DEATH, MAX_AGE_AT_DEATH: Lifespan validation (0-150 years)
  - ERROR_MESSAGES: Centralized, user-friendly error messages
  - REQUIRED_FIELDS: List of mandatory fields
- **Relationship Add Dialog**: Implemented missing feature to add parent/spouse/child relationships
  - New SelectPersonDialog with search functionality
  - Support for adding parents, spouses, and children through UI
  - Error handling for relationship conflicts (cycles, duplicates)
  - Full i18n support for both English and Korean
- **Search Functionality**: Implemented person search by name
  - Real-time filtering of person list
  - Search results count display
  - Automatic list restoration when search is cleared

### Fixed
#### Critical Algorithm Fixes
- **Cycle Detection False Positives**: Fixed depth-based detection causing false cycles
  - Changed from depth-based (MAX_CYCLE_DEPTH as hard limit) to proper BFS with visited set
  - Now correctly identifies actual cycles vs. deep family trees
  - Warning logged when exceeding MAX_CYCLE_DEPTH, but continues checking
  - Eliminates false positives for legitimate deep genealogies

#### Critical Missing Features
- **Relationship Add Dialog** (Issue #1 from architecture audit)
  - Previously non-functional "Set Parent", "Add Spouse", "Add Child" buttons now work
  - Users can now add relationships through the UI
- **Search Function** (Issue #2 from architecture audit)
  - Previously non-functional search field now filters person list
  - Real-time search with result count
  - Fixed incorrect variable reference (person_list → person_list_layout)

#### Critical Data Integrity & Security Fixes
- **Person ID Uniqueness**: Added validation to prevent duplicate Person IDs in add_person()
  - Prevents silent data loss from ID collisions
  - Raises ValueError with clear error message
- **Import Merge Safety**: Added pre-validation before import merge operations
  - Prevents partial data corruption when MAX_PERSONS limit exceeded
  - Shows detailed error with current/import counts
  - Advises file reload on merge failure for recovery
- **Photo Path Traversal**: Added os.path.basename() sanitization in Person.from_dict()
  - Blocks directory traversal attacks (e.g., "../../../etc/passwd")
  - Extracts filename only for security

#### High Priority UX & Performance Fixes
- **Delete Cascade Warning**: Enhanced delete confirmation to show affected relationship count
  - Prevents accidental data loss from cascade deletes
  - Shows breakdown of spouse/parent-child/sibling relationships
  - Added translations for both English and Korean
- **Animation Memory Leak**: Added explicit cleanup on widget destruction
  - Prevents memory leaks from orphaned QVariantAnimation objects
  - Properly disconnects signals and calls deleteLater()
- **GEDCOM Memory Efficiency**: Refactored to streaming line-by-line processing
  - Eliminates loading entire file into memory
  - Reduces memory footprint for large GEDCOM files

### Changed
- Applied Black code formatter to entire codebase (line length 100)
- Fixed Ruff linting violations (import order, unused variables)
- Improved code style consistency (PEP 8 compliance)
- Enhanced type safety with strict type hints (Dict[str, Any], return types)
- Refactored GEDCOM parser to reduce cyclomatic complexity (49 → 25)
- **Refactored hardcoded values**: Moved all magic numbers to centralized configuration
  - Improved maintainability by centralizing constants in src/config.py
  - Easier to adjust limits, ranges, and UI parameters in one place
  - Better code readability with named constants instead of magic numbers
- **Removed code duplication in date formatting**: LunarCalendarUtil.format_date() now reuses date_formatter.format_date()
  - Eliminated 15 lines of duplicated date formatting logic
  - Single source of truth for date formatting rules
- **Enhanced date validation**: Added year range validation using config constants
  - Validates year is between YEAR_MIN (1800) and YEAR_MAX (2100)
  - Prevents invalid dates outside acceptable historical range
- **Improved input validation**: Comprehensive validation with better error messages
  - Phone number validation with PHONE_PATTERN (supports international formats)
  - Maximum lifespan validation (MAX_AGE_AT_DEATH = 150 years)
  - Centralized error messages from ERROR_MESSAGES config
  - More specific validation for name length (MIN_NAME_LENGTH, MAX_NAME_LENGTH)
  - Better email validation with EMAIL_PATTERN constant

### Removed
- **SIBLING Relationship Type**: Removed unused RelationType.SIBLING
  - Was defined but never created or used in the codebase
  - Simplified relationship model to only PARENT_CHILD and SPOUSE

### Added
- Custom Claude Code skills for development automation:
  - pytest-coverage: Run tests with coverage reporting
  - code-formatting: Auto-format with Black and Ruff
  - mypy-checking: Static type checking
  - pyinstaller-build: Build executables
  - quality-checks: Comprehensive quality workflow
  - test-scaffold: Generate test templates
- Comprehensive type hints for all core modules (Person, Relationship, Logger)
- Helper functions for GEDCOM parsing (_parse_gedcom_line, _process_indi_record, etc.)
- Widget cleanup handler (_cleanup_all_animations) connected to destroyed signal

## [0.1.0] - 2025-12-25

### Added
- Initial release of Family Tree Application
- Modern PyQt6-based UI with dark mode support
- Smooth animations with easing curves for zoom and pan
- SVG icon set for all UI elements
- Multilingual support (English and Korean)
- Multiple file format support:
  - JSON (native format with full data preservation)
  - Excel (.xlsx) import/export
  - GEDCOM (.ged) import for genealogy data
- Marriage and divorce tracking with dates
- Current spouse highlighting in tree view
- Divorced spouse visual distinction (dashed gray lines)
- Smart family tree layout by generation
- Person detail panel with tabs:
  - Basic information (name, gender, birth/death dates)
  - Additional information (address, occupation, education, contact)
  - Notes and relationship management
- Input validation:
  - Email format validation
  - Date range validation
  - Death date must be after birth date
  - Required field validation
  - Maximum length validation for all text fields
- Comprehensive error handling and logging
- Atomic file writes to prevent data corruption
- Thread-safe singleton patterns
- 96 unit tests covering critical functionality
- Project metadata and setup.py for package distribution

### Security
- HTML injection vulnerability fixed by escaping user input
- Safe exception handling with proper logging
- Input length validation to prevent buffer issues
- Atomic file operations to prevent data corruption

### Performance
- Memory leak fixes in animation system
- Depth limit (50 generations) to prevent infinite loops in cycle detection
- Optimized file I/O with error recovery
- Efficient layout calculation for family trees

### Changed
- Replaced all print statements with centralized logging system
- Improved error messages for better user experience
- Set English as default language (Korean still fully supported)

### Fixed
- AttributeError in detail panel spouse display
- Circular import issues using TYPE_CHECKING
- Animation memory leaks with proper cleanup
- Silent exception handling now logs all errors
- Thread safety in singleton patterns

[0.1.0]: https://github.com/zacala1/family-tree-viewer/releases/tag/v0.1.0
