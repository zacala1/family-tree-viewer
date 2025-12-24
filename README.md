# Family Tree Application

A modern family tree visualization application with dark mode, animations, and multilingual support.

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

## Technical Details

- **Framework**: PyQt6
- **Language**: Python 3.13
- **Build Tool**: PyInstaller
