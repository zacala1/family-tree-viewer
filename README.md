# Family Tree Application

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-9.0%2F10-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-96%20passed-brightgreen.svg)]()

A modern family tree visualization application with dark mode, animations, and multilingual support.

![Family Tree Application](https://via.placeholder.com/800x450.png?text=Family+Tree+Application+Screenshot)

## Features

- **Modern UI**: Drop shadows, smooth animations, and gradient effects
- **Dark Mode**: Toggle between light and dark themes (Ctrl+T)
- **SVG Icons**: Professional icon set for all UI elements
- **Multilingual**: English and Korean language support
- **Marriage/Divorce Tracking**: Record marriage and divorce dates for spouses
- **Smart Layout**: Automatically organizes family members by generation
- **Export/Import**: Save and load family trees in JSON or Excel format

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

- **Ctrl+N**: Add new family member
- **Ctrl+O**: Open family tree file
- **Ctrl+S**: Save family tree
- **Ctrl+T**: Toggle dark/light theme
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+0**: Reset zoom
- **Delete**: Delete selected member

### Mouse Controls

- **Left Click**: Select person
- **Double Click**: Edit person details
- **Drag**: Pan the tree view
- **Mouse Wheel**: Zoom in/out

## File Formats

Supported file formats:
- **JSON** (`.json`): Native format, preserves all data
- **Excel** (`.xlsx`): Spreadsheet format for easy viewing
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
- Automatic directory creation when saving
- Comprehensive error handling for file operations
- Safe type conversion when loading Excel files
- Detailed error logging to `~/.familytree/logs/familytree.log`

### Performance
- Smooth animations with easing curves
- Proper memory management (no memory leaks)
- Optimized file I/O with error recovery

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

- **96 unit tests** covering all critical functionality
- **Input validation** on all user inputs
- **Type hints** throughout the codebase
- **Centralized logging** for debugging
- **Code quality score**: 9.0/10

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

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- How to report bugs
- How to suggest enhancements
- Development setup and workflow
- Coding guidelines and standards
- Pull request process

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- 📖 [User Guide](USER_GUIDE.md) - Comprehensive usage documentation
- 🐛 [Issue Tracker](https://github.com/zacala1/family-tree-viewer/issues) - Report bugs or request features
- 💬 [Discussions](https://github.com/zacala1/family-tree-viewer/discussions) - Ask questions and share ideas

## Roadmap

Future enhancements being considered:

- [ ] PDF export for family trees
- [ ] Photo attachments for family members
- [ ] Advanced search and filtering
- [ ] Statistics and analytics
- [ ] Family tree sharing/collaboration
- [ ] Mobile app version
- [ ] Cloud backup integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Icons from various open-source icon sets
- Korean lunar calendar support from [korean-lunar-calendar](https://github.com/usingsky/korean_lunar_calendar_py)

## Author

**zacala1**

- GitHub: [@zacala1](https://github.com/zacala1)
- Project Link: [https://github.com/zacala1/family-tree-viewer](https://github.com/zacala1/family-tree-viewer)
