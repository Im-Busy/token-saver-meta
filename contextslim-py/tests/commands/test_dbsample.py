"""Tests for contextslim.commands.db.dbsample."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from contextslim.commands.db.dbsample import dbsample_command


@pytest.fixture
def sample_db(tmp_path: Path) -> str:
    """Create a SQLite DB with test data."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'alpha')")
    conn.execute("INSERT INTO items VALUES (2, 'beta')")
    conn.execute("INSERT INTO items VALUES (3, 'gamma')")
    conn.commit()
    conn.close()
    return db_path


class TestDbsampleCommand:
    """Sample rows from a table."""

    def test_samples_rows(self, sample_db: str, capsys) -> None:
        """Given: table with 3 rows. When: dbsample. Then: up to 5 shown."""
        dbsample_command("items", db_path=sample_db)
        out = capsys.readouterr().out
        assert "id" in out
        assert "name" in out
        assert "alpha" in out
        assert "beta" in out
        assert "gamma" in out

    def test_no_db_path(self, capsys) -> None:
        """Given: no --db. When: dbsample. Then: error."""
        dbsample_command("users", db_path=None)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_db_not_found(self, capsys) -> None:
        """Given: nonexistent DB. When: dbsample. Then: error."""
        dbsample_command("users", db_path="/no/such.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_table_not_found(self, sample_db: str, capsys) -> None:
        """Given: valid DB, wrong table. When: dbsample. Then: error."""
        dbsample_command("nonexistent", db_path=sample_db)
        out = capsys.readouterr().out
        assert "not found" in out

    def test_empty_table(self, sample_db: str, capsys) -> None:
        """Given: empty table. When: dbsample. Then: 'empty' message."""
        # Create empty table
        conn = sqlite3.connect(sample_db)
        conn.execute("CREATE TABLE empty_tbl (x INTEGER)")
        conn.commit()
        conn.close()
        dbsample_command("empty_tbl", db_path=sample_db)
        out = capsys.readouterr().out
        assert "empty" in out
