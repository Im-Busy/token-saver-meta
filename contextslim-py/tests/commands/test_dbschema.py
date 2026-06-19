"""Tests for contextslim.commands.db.dbschema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from contextslim.commands.db.dbschema import dbschema_command


@pytest.fixture
def sample_db(tmp_path: Path) -> str:
    """Create a SQLite DB with two tables."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT)")
    conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT, user_id INTEGER)")
    conn.execute("CREATE INDEX idx_posts_user ON posts(user_id)")
    conn.commit()
    conn.close()
    return db_path


class TestDbschemaCommand:
    """Compact schema tree display."""

    def test_shows_tables_and_columns(self, sample_db: str, capsys) -> None:
        """Given: DB with tables. When: dbschema. Then: tree with columns."""
        dbschema_command(sample_db)
        out = capsys.readouterr().out
        assert "users" in out
        assert "posts" in out
        assert "id" in out
        assert "name" in out
        assert "TEXT" in out
        assert "INTEGER" in out
        assert "PK" in out

    def test_shows_indexes(self, sample_db: str, capsys) -> None:
        """Given: indexed table. When: dbschema. Then: index shown."""
        dbschema_command(sample_db)
        out = capsys.readouterr().out
        assert "idx_posts_user" in out or "indexes" in out

    def test_filters_by_name(self, sample_db: str, capsys) -> None:
        """Given: multiple tables. When: filter 'user'. Then: only users."""
        dbschema_command(sample_db, name_filter="user")
        out = capsys.readouterr().out
        assert "users" in out
        assert "posts" not in out

    def test_filter_no_match(self, sample_db: str, capsys) -> None:
        """Given: tables. When: filter 'zzz'. Then: 'No tables'."""
        dbschema_command(sample_db, name_filter="zzz")
        out = capsys.readouterr().out
        assert "No tables" in out

    def test_db_not_found(self, capsys) -> None:
        """Given: non-existent file. When: dbschema. Then: error."""
        dbschema_command("/nonexistent/test.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_empty_db(self, tmp_path: Path, capsys) -> None:
        """Given: empty DB. When: dbschema. Then: 'No tables'."""
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.close()
        dbschema_command(db_path)
        out = capsys.readouterr().out
        assert "No tables" in out
