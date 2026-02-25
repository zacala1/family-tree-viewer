"""Shared test fixtures."""

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure QApplication instance exists for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
