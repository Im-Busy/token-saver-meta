"""Tests for contextslim.commands.db.dbstats."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from contextslim.commands.db.dbstats import dbstats_command


@pytest.fixture
def sample_db(tmp_path: Path) -> str:
    """Create a SQLite DB with tables and an index."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT, user_id INTEGER)")
    conn.execute("CREATE INDEX idx_posts_user ON posts(user_id)")
    conn.execute("INSERT INTO users VALUES (1, 'alice')")
    conn.execute("INSERT INTO users VALUES (2, 'bob')")
    conn.execute("INSERT INTO posts VALUES (1, 'hello', 1)")
    conn.commit()
    conn.close()
    return db_path


class TestDbstatsCommand:
    """Table stats: row counts + index counts."""

    def test_shows_row_counts(self, sample_db: str, capsys) -> None:
        """Given: DB with data. When: dbstats. Then: row counts shown."""
        dbstats_command(sample_db)
        out = capsys.readouterr().out
        assert "users" in out
        assert "2" in out  # users has 2 rows
        assert "posts" in out
        assert "1" in out  # posts has 1 row

    def test_shows_index_counts(self, sample_db: str, capsys) -> None:
        """Given: indexed table. When: dbstats. Then: index count shown."""
        dbstats_command(sample_db)
        out = capsys.readouterr().out
        assert "Indexes" in out
        # posts should show 1 index
        lines = out.splitlines()
        found = [line for line in lines if "posts" in line]
        assert len(found) >= 1

    def test_filters_by_name(self, sample_db: str, capsys) -> None:
        """Given: multiple tables. When: filter 'user'. Then: only users."""
        dbstats_command(sample_db, name_filter="user")
        out = capsys.readouterr().out
        assert "users" in out
        assert "posts" not in out

    def test_db_not_found(self, capsys) -> None:
        """Given: nonexistent path. When: dbstats. Then: error."""
        dbstats_command("/no/such.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_empty_db(self, tmp_path: Path, capsys) -> None:
        """Given: empty DB. When: dbstats. Then: 'No tables'."""
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.close()
        dbstats_command(db_path)
        out = capsys.readouterr().out
        assert "No tables" in out
