"""PyInstaller build script for FamilyTree application."""
import PyInstaller.__main__
import os
import shutil

# Clean previous builds
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

# PyInstaller arguments
PyInstaller.__main__.run([
    'main.py',
    '--name=FamilyTree',
    '--onefile',  # Single EXE file
    '--windowed',  # No console window
    '--icon=NONE',  # No icon for now
    '--add-data=src/i18n;src/i18n',  # Include translation files
    '--add-data=src/styles;src/styles',  # Include stylesheets
    '--add-data=src/resources;src/resources',  # Include icons
    '--add-data=data;data',  # Include sample data
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--collect-all=PyQt6',
    '--noconfirm',  # Overwrite without asking
])

print("\nBuild complete! EXE file is in the 'dist' folder.")
print(f"Location: {os.path.abspath('dist/FamilyTree.exe')}")
