"""Workspace and directory fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Clean temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def workspace():
    """Test workspace with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_dir = Path(tmpdir) / "workspace"
        workspace_dir.mkdir()

        # Create test files
        (workspace_dir / "test.txt").write_text("Test content")
        (workspace_dir / "data.json").write_text('{"test": true}')

        yield workspace_dir


@pytest.fixture
def docs_dir():
    """Test documents for retrieval testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()

        # Create test documents
        (docs_dir / "readme.md").write_text(
            "# Project Documentation\nThis is a test project with authentication features."
        )
        (docs_dir / "auth.md").write_text(
            "# Authentication\nUsers can login with username and password. JWT tokens are used for sessions."
        )
        (docs_dir / "api.md").write_text(
            "# API Reference\nThe API supports rate limiting at 1000 requests per hour."
        )

        yield docs_dir
