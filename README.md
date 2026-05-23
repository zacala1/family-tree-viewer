# Family Tree Application

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-409%20passed-brightgreen.svg)]()

A modern family tree visualization application with dark mode, animations, and multilingual support.

![Family Tree Application](https://via.placeholder.com/800x450.png?text=Family+Tree+Application+Screenshot)

## Features

### ✨ User Interface
- **Modern UI**: Drop shadows, smooth animations, and gradient effects
- **Dark Mode**: Toggle between light and dark themes (Ctrl+T)
- **WCAG-AA disabled-state styling**: legible disabled controls in both themes (≥ 4.5:1 contrast)
- **SVG Icons**: Professional icon set for all UI elements
- **Multilingual**: English and Korean language support with runtime switching
- **Photo lightbox**: click any thumbnail to view at ~80% of screen size
- **F1 Keyboard Shortcuts dialog**: discover every binding from one place
- **Recent Files** menu: jump back into the last 5 trees you worked on
- **Arrow-key canvas navigation**: ↑ parent, ↓ child, ←/→ sibling
- **Empty-state hints**: contextual guidance for new files and empty search results

### 👨‍👩‍👧‍👦 Family Management
- **Person Details**: Track birth/death dates, occupation, education, contact info
- **Photos**: Attach and display photos for each person
- **Events**: Record life events (graduation, marriage, retirement, etc.)
- **Timeline View**: Chronological visualization of family events
- **Marriage/Divorce Tracking**: Record marriage and divorce dates for spouses
- **Smart Layout**: Automatically organizes family members by generation

### 🔧 Advanced Features
- **Undo/Redo**: Full undo/redo support with 50-level history (Ctrl+Z/Ctrl+Y); covers person edits, parent-child links, spouse links, and relationship removals
- **Solar↔Lunar inline conversion**: live conversion preview next to every date input (uses `korean-lunar-calendar`)
- **Duplicate Detection**: Levenshtein-based similar name warning with NFC normalization (catches Korean variants with `(故)` / hanja markers)
- **Lineage Reports**: Descendant/ancestor text reports with cycle protection and depth cap to handle 300+ generation chains safely
- **Cycle Detection**: Prevents invalid family relationships (no circular references)
- **Thread-Safe**: RLock protection for all data operations
- **Performance Monitoring**: Built-in profiling and performance tracking
- **Live-search debounce**: 200ms debounced search avoids re-rendering on every keystroke; Enter / Esc bypass for explicit commit/clear
- **Viewport culling**: tree canvas only paints visible nodes — large trees pan smoothly
- **Structured Logging**: JSON-formatted logs for analysis and debugging

### 💾 Import/Export
- **Export/Import**: Save and load family trees in multiple formats
  - JSON (complete data preservation)
  - Excel (spreadsheet view)
  - **PDF** (printable tree canvas snapshot, via `Ctrl+P`)
  - GEDCOM (standard genealogy format - import only)

## Quick Start

### Option 1: Run Executable (Recommended)

1. Download `FamilyTree.exe` from the `dist` folder
2. Double-click to run
3. No installation required!

### Option 2: Run from Source

1. Install Python 3.9 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Building from Source

To create a standalone executable:

```bash
python build.py
```

The executable will be created in the `dist` folder.

## Usage

### Keyboard Shortcuts

#### File Operations
- **Ctrl+N**: New family tree
- **Ctrl+O**: Open family tree file
- **Ctrl+S**: Save family tree
- **Ctrl+Shift+S**: Save As
- **Ctrl+P**: Export tree to PDF

#### Editing
- **Ctrl+Shift+N**: Add new family member
- **Delete**: Delete selected member
- **Ctrl+Z**: Undo last action
- **Ctrl+Y**: Redo last undone action

#### View
- **Ctrl+T**: Toggle dark/light theme
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+0**: Reset zoom

### Mouse Controls

- **Left Click**: Select person
- **Double Click**: Edit person details
- **Drag**: Pan the tree view
- **Mouse Wheel**: Zoom in/out

## File Formats

Supported file formats:
- **JSON** (`.json`): Native format, preserves all data
- **Excel** (`.xlsx`): Spreadsheet format for easy viewing
- **PDF** (`.pdf`): Printable snapshot of the tree canvas (export only)
- **GEDCOM** (`.ged`): Standard genealogy format (import only)

## Sample Data

Open `data/sample.json` to see an example family tree.

## Advanced Features

### Input Validation
- Email format validation
- Date range validation (months 1-12, days 1-31)
- Death date must be after birth date
- Required field validation

### Data Safety
- **Automatic Backups**: Automatic directory creation when saving
- **Error Handling**: Comprehensive error handling for file operations
- **Type Safety**: Safe type conversion when loading Excel files
- **Detailed Logging**: JSON-formatted logs at `~/.familytree/logs/familytree.log`
- **Path Traversal Protection**: Security validation on file paths
- **Size Limits**: Maximum 50,000 persons, 100MB files, 5MB photos

### Performance
- **Smart Caching**: BFS generation calculation with caching (O(V+E))
- **Thread Safety**: RLock protection for all shared data
- **Memory Optimization**: `__slots__` usage in Relationship class (-40% memory)
- **Smooth Animations**: Easing curves with 300ms duration
- **Performance Profiling**: Built-in @profile decorator for monitoring
- **Lazy Loading**: On-demand generation calculation

## Development

### Running Tests

Run the full test suite:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_date_formatter.py -v
```

### Code Quality

- **409+ unit tests** covering models, services, repositories, validators, UI components, and integration paths
- **Input validation** on all user inputs (centralized in `models/validators.py`)
- **Type hints** throughout the codebase
- **Structured logging** with JSON format for analysis; `log_action()` safely handles `LogRecord` reserved attribute names
- **Design patterns**: Command (undo/redo), Factory, Singleton, Observer (Signal-Slot), Strategy (file format dispatch), Validator, Decorator (`@profile`)
- **Thread safety**: Full RLock protection in `FamilyTree`; command undo paths acquire the same lock
- **Test coverage**: Models, services, repositories, command, file handler, lineage report, photo manager, search debounce, recent files, status counts — all covered with regression guards

### Project Structure

```
FamilyTree/
├── src/
│   ├── models/         # Data models (Person, FamilyTree, Relationship)
│   ├── views/          # UI components (MainWindow, TreeCanvas, DetailPanel)
│   ├── utils/          # Utilities (FileHandler, Logger, DateFormatter)
│   ├── i18n/           # Internationalization (English, Korean)
│   ├── styles/         # QSS stylesheets (light, dark themes)
│   └── resources/      # Icons and images
├── tests/              # Unit tests
├── data/               # Sample data files
└── dist/               # Built executable

```

## Technical Details

- **Framework**: PyQt6
- **Language**: Python 3.13
- **Build Tool**: PyInstaller
- **Testing**: pytest
- **Dependencies**: openpyxl, PyQt6

## Troubleshooting

### Application won't start
- Ensure Python 3.9 or higher is installed
- Try running from command line to see error messages
- Check log file at `~/.familytree/logs/familytree.log`

### File won't load
- Ensure file format is supported (JSON, Excel, GEDCOM)
- Check file permissions
- View error details in log file

### Build fails
- Install all dependencies: `pip install -r requirements.txt`
- Ensure PyInstaller is installed: `pip install pyinstaller`
- Clean build folders: delete `build/` and `dist/` directories

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
