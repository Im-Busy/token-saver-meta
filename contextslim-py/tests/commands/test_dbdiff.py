"""Tests for contextslim.commands.db.dbdiff."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from contextslim.commands.db.dbdiff import dbdiff_command


@pytest.fixture
def db1(tmp_path: Path) -> str:
    """Create first test DB."""
    db_path = str(tmp_path / "db1.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def db2_identical(tmp_path: Path) -> str:
    """Create second DB identical to db1."""
    db_path = str(tmp_path / "db2.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def db2_different(tmp_path: Path) -> str:
    """Create second DB with different schema."""
    db_path = str(tmp_path / "db3.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, body TEXT)")
    conn.commit()
    conn.close()
    return db_path


class TestDbdiffCommand:
    """Schema comparison via difflib."""

    def test_identical_schemas(self, db1: str, db2_identical: str, capsys) -> None:
        """Given: two identical DBs. When: dbdiff. Then: 'identical'."""
        dbdiff_command(db1, db2_identical)
        out = capsys.readouterr().out
        assert "identical" in out

    def test_different_schemas(self, db1: str, db2_different: str, capsys) -> None:
        """Given: different tables. When: dbdiff. Then: diff shown."""
        dbdiff_command(db1, db2_different)
        out = capsys.readouterr().out
        assert "posts" in out or "comments" in out  # one will be + or -
        # Should have diff markers
        assert "+" in out or "-" in out

    def test_first_file_not_found(self, capsys) -> None:
        """Given: schema1 missing. When: dbdiff. Then: error."""
        dbdiff_command("/no/such1.db", "/no/such2.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_second_file_not_found(self, tmp_path: Path, capsys) -> None:
        """Given: schema2 missing. When: dbdiff. Then: error."""
        empty = str(tmp_path / "exists.db")
        sqlite3.connect(empty).close()
        dbdiff_command(empty, "/no/such2.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_empty_databases(self, tmp_path: Path, capsys) -> None:
        """Given: two empty DBs. When: dbdiff. Then: 'no schema' message."""
        db1 = str(tmp_path / "e1.db")
        db2 = str(tmp_path / "e2.db")
        sqlite3.connect(db1).close()
        sqlite3.connect(db2).close()
        dbdiff_command(db1, db2)
        out = capsys.readouterr().out
        assert "no schema" in out
