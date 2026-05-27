"""Pytest configuration — shared fixtures for GUI and non-GUI tests."""
from __future__ import annotations

import os

# Force offscreen rendering before any Qt import
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest


@pytest.fixture(scope='session')
def qapp():
    """Session-scoped QApplication instance for GUI tests."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        pytest.skip('PySide6 not installed')

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Cleanup: process pending events
    app.processEvents()
