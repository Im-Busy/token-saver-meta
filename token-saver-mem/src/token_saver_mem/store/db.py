"""Database connection and initialization for token-saver-mem."""

import sqlite3
from pathlib import Path
from typing import Optional


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _load_schema_sql() -> str:
    """Load the schema SQL from the bundled schema.sql file."""
    return _SCHEMA_PATH.read_text(encoding="utf-8")


SCHEMA_SQL: str = _load_schema_sql()
"""The full schema SQL, loaded once at import time."""


def get_db(db_path: str, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a SQLite connection at *db_path*.

    Args:
        db_path: Path to the SQLite database file.
        read_only: If True, open in read-only mode.

    Returns:
        A sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    uri = f"file:{db_path}?mode=ro" if read_only else db_path
    conn = sqlite3.connect(uri, uri=bool(read_only))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema (idempotent — safe to call multiple times).

    Uses IF NOT EXISTS on every CREATE statement.
    """
    conn.executescript(SCHEMA_SQL)
    conn.commit()
