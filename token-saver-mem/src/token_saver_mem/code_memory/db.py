"""Database module for code_memory — SQLite schema, connection, init."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS code_nodes (
    id              TEXT PRIMARY KEY,
    kind            TEXT NOT NULL,
    name            TEXT NOT NULL,
    path            TEXT NOT NULL,
    start_line      INTEGER,
    end_line        INTEGER,
    content_hash    TEXT,
    summary         TEXT,
    summary_hash    TEXT,
    metadata        TEXT NOT NULL DEFAULT '{}',
    updated_at      REAL NOT NULL,
    deleted_at      REAL
);

CREATE INDEX IF NOT EXISTS idx_code_nodes_path ON code_nodes(path);
CREATE INDEX IF NOT EXISTS idx_code_nodes_kind ON code_nodes(kind);
CREATE INDEX IF NOT EXISTS idx_code_nodes_updated ON code_nodes(updated_at);

CREATE TABLE IF NOT EXISTS file_fingerprints (
    file_path    TEXT PRIMARY KEY,
    content_sha  TEXT NOT NULL,
    mtime_ns     INTEGER NOT NULL,
    indexed_at   REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fp_path ON file_fingerprints(file_path);

CREATE TABLE IF NOT EXISTS node_visits (
    node_id     TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    visited_at  REAL NOT NULL,
    PRIMARY KEY (node_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_node_visits_node ON node_visits(node_id);
"""


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Open SQLite connection with WAL mode and optimized pragmas.

    Uses a simple factory — not a connection pool. Each call opens a new
    connection (suitable for threaded usage within a single mutex).
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(db_path: str | Path) -> None:
    """Initialize the code_memory schema. Idempotent."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def upsert_nodes(conn: sqlite3.Connection, nodes: list) -> None:
    """Upsert code nodes into the database. Only bumps updated_at on content_hash change.

    Nodes are plain dicts with keys matching code_nodes columns.
    Uses a transaction — caller must commit.
    """
    if not nodes:
        return
    now = time.time()
    rows = [
        (
            n["id"],
            n["kind"],
            n["name"],
            n["path"],
            n.get("start_line"),
            n.get("end_line"),
            n.get("content_hash"),
            n.get("summary"),
            n.get("summary_hash"),
            n.get("metadata", "{}"),
            now,
            n.get("deleted_at"),
        )
        for n in nodes
    ]
    conn.executemany(
        """INSERT INTO code_nodes
             (id, kind, name, path, start_line, end_line, content_hash,
              summary, summary_hash, metadata, updated_at, deleted_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             kind=excluded.kind,
             name=excluded.name,
             path=excluded.path,
             start_line=excluded.start_line,
             end_line=excluded.end_line,
             content_hash=excluded.content_hash,
             summary=CASE
                 WHEN excluded.summary IS NOT NULL AND code_nodes.summary IS NULL
                 THEN excluded.summary
                 ELSE code_nodes.summary
             END,
             summary_hash=excluded.summary_hash,
             metadata=excluded.metadata,
             updated_at=CASE
                 WHEN excluded.content_hash IS NOT NULL
                      AND excluded.content_hash != COALESCE(code_nodes.content_hash, '')
                 THEN excluded.updated_at
                 ELSE code_nodes.updated_at
             END,
             deleted_at=excluded.deleted_at""",
        rows,
    )


def upsert_fingerprint(conn: sqlite3.Connection, file_path: str, content_sha: str, mtime_ns: int) -> None:
    """Upsert a single file fingerprint."""
    conn.execute(
        """INSERT INTO file_fingerprints (file_path, content_sha, mtime_ns, indexed_at)
           VALUES (?,?,?,?) ON CONFLICT(file_path) DO UPDATE SET
             content_sha=excluded.content_sha,
             mtime_ns=excluded.mtime_ns,
             indexed_at=excluded.indexed_at""",
        (file_path, content_sha, mtime_ns, time.time()),
    )


def get_all_fingerprints(conn: sqlite3.Connection) -> dict[str, tuple[str, int]]:
    """Return {file_path: (content_sha, mtime_ns)} for all indexed files."""
    rows = conn.execute(
        "SELECT file_path, content_sha, mtime_ns FROM file_fingerprints"
    ).fetchall()
    return {r["file_path"]: (r["content_sha"], r["mtime_ns"]) for r in rows}


def soft_delete_nodes(conn: sqlite3.Connection, path: str) -> int:
    """Mark all active nodes for a file path as deleted. Returns count."""
    cur = conn.execute(
        "UPDATE code_nodes SET deleted_at = ? WHERE path = ? AND deleted_at IS NULL",
        (time.time(), path),
    )
    return cur.rowcount
