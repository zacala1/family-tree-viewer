# Contributing to Family Tree Application

Thank you for your interest in contributing to the Family Tree Application! This document provides guidelines for contributing to the project.

## Code of Conduct

This is a personal project, but all interactions should be respectful and constructive.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details**:
  - OS and version
  - Python version
  - PyQt6 version
  - Application version

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Clear description** of the proposed feature
- **Use case** - why would this be useful?
- **Mockups or examples** if applicable
- **Implementation ideas** if you have them

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding style** used in the project
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass**: `python -m pytest tests/ -v`
6. **Write clear commit messages**

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zacala1/family-tree-viewer.git
   cd family-tree-viewer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_family_tree.py -v
```

### Building Executable

Build standalone executable:
```bash
python build.py
```

The executable will be in the `dist/` folder.

## Coding Guidelines

### Python Style

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Code Organization

- **Models** (`src/models/`): Data structures and business logic
- **Views** (`src/views/`): UI components and PyQt6 widgets
- **Utils** (`src/utils/`): Helper functions and utilities
- **i18n** (`src/i18n/`): Translation files and i18n utilities
- **Tests** (`tests/`): Unit tests mirroring the source structure

### Testing

- Write tests for all new features
- Aim for high test coverage
- Test edge cases and error conditions
- Use descriptive test names

Example test structure:
```python
class TestFeatureName:
    """Test cases for feature name."""

    def test_specific_behavior(self):
        """Test specific behavior description."""
        # Arrange
        # Act
        # Assert
```

### Documentation

- Add docstrings to all public functions and classes
- Update README.md for user-facing changes
- Update USER_GUIDE.md for new features
- Add entries to CHANGELOG.md

### Commit Messages

Follow conventional commits format:

```
type(scope): brief description

Detailed explanation (optional)

- List of changes
- Another change
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(ui): add export to PDF feature

- Implement PDF generation using reportlab
- Add export button to menu
- Add tests for PDF export
```

```
fix(validation): prevent negative birth years

Fixes issue #42 where users could enter negative years,
causing crashes in date calculations.
```

## Project Structure

```
FamilyTree/
├── src/
│   ├── models/         # Data models
│   ├── views/          # UI components
│   ├── utils/          # Utilities
│   ├── i18n/           # Translations
│   ├── styles/         # QSS stylesheets
│   └── resources/      # Icons and images
├── tests/              # Unit tests
├── data/               # Sample data
└── dist/               # Built executables
```

## Translation Contributions

To add a new language:

1. Create `src/i18n/[lang_code].json` (e.g., `fr.json` for French)
2. Copy structure from `en.json`
3. Translate all strings
4. Update `Translator.get_available_languages()` in `src/i18n/translator.py`
5. Test all UI elements in the new language

## Security

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email the maintainer directly (check GitHub profile)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Questions?

Feel free to open an issue with the `question` label for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
