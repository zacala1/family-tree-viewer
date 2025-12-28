# Changelog

All notable changes to the Family Tree Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Applied Black code formatter to entire codebase (line length 100)
- Fixed Ruff linting violations (import order, unused variables)
- Improved code style consistency (PEP 8 compliance)
- Enhanced type safety with strict type hints (Dict[str, Any], return types)
- Refactored GEDCOM parser to reduce cyclomatic complexity (49 → 25)

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
