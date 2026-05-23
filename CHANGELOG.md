# Changelog

All notable changes to the Family Tree Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (UX / UI)
- **Photo lightbox**: click a person's thumbnail in the detail panel to open a modal viewer scaled to ~80% of the screen, dismissed by click or Esc
- **EXIF orientation**: smartphone photos with rotated EXIF metadata are now rendered upright in thumbnails and the lightbox via Pillow's `ImageOps.exif_transpose`
- **Photo on cards**: tree cards show the person's photo (round-masked) in the icon slot when available; cached per `(photo_path, size)` to avoid repeated disk reads, with explicit `invalidate_photo_cache()` after edits
- **Arrow-key canvas navigation**: ↑ first parent, ↓ first child, ←/→ same-generation sibling; events are explicitly accepted to prevent parent-widget side effects
- **F1 keyboard shortcuts dialog**: categorized HTML reference (File / Edit / View / Canvas Nav / Mouse) opens via Help → Keyboard Shortcuts
- **Recent Files submenu**: File → Recent Files persists last 5 opened/saved paths via `QSettings`, with auto-prune of missing files and a "Clear Recent Files" action
- **Solar↔Lunar inline conversion**: birth and death date inputs show the corresponding date on the other calendar next to the field, updating live; uses `korean-lunar-calendar`
- **Empty-state hints**: tree canvas shows "no members yet" guidance instead of a blank canvas; person list panel shows context-aware messages for empty tree vs. no search results vs. no filter matches; events tab shows a centered "+ Add First Event" CTA
- **Event sort toggle**: events list has an ↑/↓ button to flip between oldest-first and newest-first orderings; selection persists across refresh
- **Esc in search**: clears the search query and immediately restores the full list (`WidgetShortcut` context — doesn't swallow Esc elsewhere)
- **Drag-drop status hint**: dragging a supported file over the window updates the status bar with the incoming filename
- **Permanent relationship count**: status bar always shows `Relationships: N` next to `Members: N`
- **Empty events CTA**: centered "+ Add First Event" button in an empty events list, disabled when not in edit mode with explanatory tooltip
- **WCAG-AA disabled styling**: dark and light themes now include centralized `:disabled` rules for all common widgets (contrast ≥ 4.5:1)

### Performance
- **Live search debounce**: search input runs at most every 200 ms (Trie lookup + list re-render); Enter still triggers immediately
- **Viewport culling**: tree canvas skips drawing nodes outside the visible scene rect, with a 50px safety margin to avoid pop-in during pan/zoom

### Fixed
- **Critical**: restored `_load_file()` helper that drag-drop and backup-recovery paths still called after the previous refactor — was an AttributeError crash on either path
- **Critical**: `log_action()` raised `KeyError: "Attempt to overwrite 'name' in LogRecord"` whenever a caller passed any `LogRecord` reserved attribute name as a kwarg (the entire Service layer did via `name=person.name`). Reserved keys are now prefixed `ctx_`
- `family_tree.remove_relationship()` cleared the `Relationship` row but left dangling `spouse_ids` / `father_id` / `mother_id` / `children_ids` on the involved Persons; now consistently cleans up both sides
- `DeletePersonCommand.undo()` wrote directly into `_persons` without holding the FamilyTree lock; now goes through a lock-aware path
- `SetSpouseCommand` and `RemoveRelationshipCommand` added so spouse and relationship removals join the undo/redo history (previously bypassed)
- `_on_undo`/`_on_redo` now re-sync the detail panel and tree selection so stale data doesn't outlive a reverted change
- Detail panel validation error: on failure the panel now switches to the basic-info tab, focuses `name_input`, and `selectAll`s its contents
- Tree card name labels: long names are elided with `ElideRight` and the full name + lifespan is available via tooltip
- `LineageReportDialog`: recursion is now capped at `MAX_REPORT_DEPTH=100` (default 1000-frame stack) and emits a localized "truncated" marker; a 300-generation chain no longer crashes the dialog
- 9 previously fallback-only i18n keys now resolve cleanly in both `en.json` and `ko.json` (`button.close`, `dialog.save_failed_continue`, `error.{file_not_found_title,file_not_found_message,operation_failed,validation_title,person_not_found,day_without_month,invalid_date_combination}`)
- `tr(..., fallback="(이름 없음)")` no longer hardcodes a Korean fallback in `tree_canvas.py` and `person_card.py`

### Refactor
- `duplicate_detector.normalize_name()` applies NFC normalization and strips parenthesized annotations (`(故)`, `[Jr.]`, etc.) before Levenshtein matching — catches Korean name variants the old space-only/lowercase normalization missed
- Removed dead constants `ANIMATION_EASING` and `MIN_AGE_AT_DEATH` from `src/config.py`

### Tests
- Coverage expanded from 206 to **409 passed** (+203 tests). New files: `test_repository.py`, `test_service.py`, `test_logger.py`, `test_tree_canvas.py`, `test_search_debounce.py`, `test_empty_list_hint.py`, `test_shortcuts_dialog.py`, `test_events_sort.py`, `test_recent_files.py`, `test_status_counts.py`, `test_date_conversion.py`, `test_lineage_report.py`, plus expansions to `test_command.py`, `test_family_tree.py`, `test_file_handler.py`, `test_validators.py`, `test_photo_manager.py`
- Shared fixtures in `conftest.py`: `empty_tree`, `sample_family` (3-gen mini tree), `tmp_json_path`, `tmp_excel_path`

### Documentation
- `.claude/skills/family-tree-viewer.md`: one-page project guide for Claude Code sessions covering 5-layer boundaries, design patterns, absolute rules, common commands, file format matrix, and feature checklist
- `.gitignore`: exclude `.claude/settings.local.json` per-user settings; keep `.claude/skills/` tracked for sharing


### Added
- **Duplicate Person Detection**: Levenshtein-based similar name detection when adding/editing persons
  - `src/utils/duplicate_detector.py` — `find_similar_persons()`, `levenshtein_distance()`, `normalize_name()`
  - Threshold of 2 edits by default; warns user via confirmation dialog before proceeding
  - Helps prevent accidental duplicates when the same person is entered with slight name variations
- **PDF Export**: Export the entire family tree canvas to PDF
  - `src/utils/pdf_exporter.py` — `PdfExporter` class using PyQt6 `QtPrintSupport`
  - File menu → "Export PDF" (shortcut: `Ctrl+P`)
  - Landscape orientation, auto-fit scaling (max 3×), 15mm margins, antialiased rendering
  - No extra dependencies; uses PyQt6's built-in print support
- **Lineage Report Dialog**: Text-based descendant/ancestor report for any person
  - `src/views/lineage_report_dialog.py` — `LineageReportDialog`
  - Right-click a person → "Show Descendants" or "Show Ancestors"
  - Recursive traversal with cycle protection (visited set)
  - Tree-style indentation with lifespan annotations
- **UI Component Tests**: `tests/test_ui_components.py` covering dialogs and widget smoke tests
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
