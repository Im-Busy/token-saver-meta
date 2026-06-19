"""Shared test fixtures for code_memory tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from token_saver_mem.code_memory.db import init_schema, get_connection, upsert_nodes


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create a temporary SQLite database with schema initialized."""
    db_path = str(tmp_path / "test_code_memory.db")
    init_schema(db_path)
    return db_path


@pytest.fixture
def sample_py_files(tmp_path: Path) -> Path:
    """Create a directory with sample Python files for indexer testing."""
    src_dir = tmp_path / "sample_project"
    src_dir.mkdir()

    # Simple module with one function
    (src_dir / "utils.py").write_text(
        '''"""Utility functions."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y
''',
        encoding="utf-8",
    )

    # Module with a class
    (src_dir / "models.py").write_text(
        '''"""Data models."""

from dataclasses import dataclass


@dataclass
class User:
    """A user entity."""
    name: str
    age: int

    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}"


def create_user(name: str, age: int) -> User:
    """Factory for User."""
    return User(name=name, age=age)
''',
        encoding="utf-8",
    )

    # File with a syntax error
    (src_dir / "broken.py").write_text(
        "def broken(:\n    pass\n",
        encoding="utf-8",
    )

    # Non-Python file that should be skipped
    (src_dir / "README.txt").write_text("This is not Python.", encoding="utf-8")

    # Subdirectory with nested module
    (src_dir / "subpkg").mkdir()
    (src_dir / "subpkg" / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "subpkg" / "helpers.py").write_text(
        '''"""Helper functions."""


def normalize(text: str) -> str:
    """Strip and lowercase."""
    return text.strip().lower()
''',
        encoding="utf-8",
    )

    return src_dir


@pytest.fixture
def populated_db(temp_db: str) -> str:
    """A database pre-populated with sample code nodes."""
    conn = get_connection(temp_db)
    try:
        import hashlib
        import json
        import time

        now = time.time()
        nodes = [
            {
                "id": "function:utils.py:add",
                "kind": "function",
                "name": "add",
                "path": "utils.py",
                "start_line": 4,
                "end_line": 7,
                "content_hash": "f5a5c9d4e",
                "summary": "Add two numbers.",
                "summary_hash": "f5a5c9d4e",  # matches content_hash → fresh
                "metadata": json.dumps({"params": ["a:int", "b:int"], "return_type": "int"}),
                "updated_at": now,
                "deleted_at": None,
            },
            {
                "id": "function:utils.py:multiply",
                "kind": "function",
                "name": "multiply",
                "path": "utils.py",
                "start_line": 10,
                "end_line": 13,
                "content_hash": "a1b2c3d4e",
                "summary": "Multiply two numbers.",
                "summary_hash": "a1b2c3d4e",  # matches content_hash → fresh
                "metadata": json.dumps({"params": ["x:float", "y:float"], "return_type": "float"}),
                "updated_at": now - 3600,  # 1 hour ago
                "deleted_at": None,
            },
            {
                "id": "class:models.py:User",
                "kind": "class",
                "name": "User",
                "path": "models.py",
                "start_line": 6,
                "end_line": 13,
                "content_hash": "b9d8c7e6f",
                "summary": "A user entity.",
                "summary_hash": "b9d8c7e6f",  # matches content_hash → fresh
                "metadata": json.dumps({"bases": [], "decorators": ["dataclass"]}),
                "updated_at": now - 7200,  # 2 hours ago
                "deleted_at": None,
            },
            # Stale node: summary_hash != content_hash
            {
                "id": "function:stale_example.py:old_func",
                "kind": "function",
                "name": "old_func",
                "path": "stale_example.py",
                "start_line": 1,
                "end_line": 2,
                "content_hash": hashlib.sha256(b"def old_func():pass").hexdigest(),
                "summary": "Does something.",
                "summary_hash": hashlib.sha256(b"Different content hash").hexdigest(),
                "metadata": "{}",
                "updated_at": now,
                "deleted_at": None,
            },
            # Fresh node: summary_hash == None (never summarized)
            {
                "id": "function:stale_example.py:unsynced",
                "kind": "function",
                "name": "unsynced",
                "path": "stale_example.py",
                "start_line": 3,
                "end_line": 4,
                "content_hash": hashlib.sha256(b"def unsynced():pass").hexdigest(),
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "updated_at": now,
                "deleted_at": None,
            },
            # Deleted node
            {
                "id": "function:old_file.py:removed_func",
                "kind": "function",
                "name": "removed_func",
                "path": "old_file.py",
                "start_line": 1,
                "end_line": 2,
                "content_hash": hashlib.sha256(b"def removed_func():pass").hexdigest(),
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "updated_at": now - 86400,
                "deleted_at": now - 3600,  # deleted 1 hour ago
            },
        ]
        upsert_nodes(conn, nodes)
        conn.commit()
    finally:
        conn.close()
    return temp_db
