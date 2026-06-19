"""Tests for contextslim.commands.db.dbquery."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from contextslim.commands.db.dbquery import dbquery_command


@pytest.fixture
def sample_db(tmp_path: Path) -> str:
    """Create a SQLite DB with test data."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'alpha')")
    conn.execute("INSERT INTO items VALUES (2, 'beta')")
    conn.commit()
    conn.close()
    return db_path


class TestDbqueryCommand:
    """Execute SQL with truncated output."""

    def test_select_query(self, sample_db: str, capsys) -> None:
        """Given: DB with rows. When: SELECT *. Then: rows displayed."""
        dbquery_command("SELECT * FROM items", db_path=sample_db)
        out = capsys.readouterr().out
        assert "id" in out
        assert "name" in out
        assert "alpha" in out
        assert "beta" in out

    def test_no_db_path(self, capsys) -> None:
        """Given: no --db. When: dbquery. Then: error."""
        dbquery_command("SELECT 1", db_path=None)
        out = capsys.readouterr().out
        assert "Error" in out
        assert "--db" in out

    def test_db_not_found(self, capsys) -> None:
        """Given: nonexistent DB. When: dbquery. Then: error."""
        dbquery_command("SELECT 1", db_path="/no/such.db")
        out = capsys.readouterr().out
        assert "Error" in out

    def test_non_select(self, sample_db: str, capsys) -> None:
        """Given: UPDATE. When: dbquery. Then: rowcount shown."""
        dbquery_command("UPDATE items SET name='gamma' WHERE id=1", db_path=sample_db)
        out = capsys.readouterr().out
        assert "row(s) affected" in out

    def test_zero_rows(self, sample_db: str, capsys) -> None:
        """Given: no matches. When: SELECT. Then: '0 rows'."""
        dbquery_command("SELECT * FROM items WHERE id=999", db_path=sample_db)
        out = capsys.readouterr().out
        assert "0 rows" in out

    def test_sql_from_file(self, tmp_path: Path, sample_db: str, capsys) -> None:
        """Given: .sql file. When: dbquery. Then: executes file contents."""
        sql_file = tmp_path / "query.sql"
        sql_file.write_text("SELECT * FROM items WHERE id=1")
        dbquery_command(str(sql_file), db_path=sample_db)
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" not in out  # only id=1

    def test_sql_error(self, sample_db: str, capsys) -> None:
        """Given: invalid SQL. When: dbquery. Then: error shown."""
        dbquery_command("SELECT * FROM nonexistent", db_path=sample_db)
        out = capsys.readouterr().out
        assert "Error" in out
