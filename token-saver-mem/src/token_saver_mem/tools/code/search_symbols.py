"""search_symbols — FTS5 full-text search across code_nodes.

Creates and maintains a lazily-initialized FTS5 virtual table for
searching node names, kinds, and summaries.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from token_saver_mem.code_memory.db import get_connection

FTS5_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS code_nodes_fts USING fts5(
    node_id UNINDEXED,
    name,
    kind,
    summary,
    tokenize='porter unicode61'
);
"""


def _ensure_fts5(conn: sqlite3.Connection) -> None:
    """Create FTS5 table if missing, and populate if empty."""
    conn.execute(FTS5_SCHEMA)

    # Check if FTS5 table is empty — if so, populate from code_nodes
    count = conn.execute("SELECT COUNT(*) FROM code_nodes_fts").fetchone()[0]
    if count == 0:
        conn.execute("DELETE FROM code_nodes_fts")  # safety
        conn.executemany(
            "INSERT INTO code_nodes_fts(node_id, name, kind, summary) VALUES (?, ?, ?, ?)",
            conn.execute(
                """SELECT id, name, kind, COALESCE(summary, '')
                   FROM code_nodes
                   WHERE deleted_at IS NULL"""
            ).fetchall(),
        )
        conn.commit()


def search_symbols(db_path: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Full-text search across code_nodes via FTS5.

    Args:
        db_path: Path to the SQLite database.
        query: Search query string (FTS5 MATCH syntax).
        limit: Maximum number of results to return.

    Returns:
        List of dicts with node fields plus a 'snippet' key
        (first 200 chars of summary or name).
    """
    if not query or not query.strip():
        return []

    conn = get_connection(db_path)
    try:
        _ensure_fts5(conn)

        # Build FTS5 MATCH query with prefix support
        cleaned = query.strip().replace('"', '""')
        fts_query = f'"{cleaned}"*'

        rows = conn.execute(
            """SELECT cn.id, cn.kind, cn.name, cn.path,
                      cn.start_line, cn.end_line,
                      cn.summary, cn.summary_hash, cn.content_hash,
                      cn.metadata, cn.updated_at
               FROM code_nodes cn
               JOIN code_nodes_fts fts ON cn.id = fts.node_id
               WHERE code_nodes_fts MATCH ?
                 AND cn.deleted_at IS NULL
               ORDER BY rank
               LIMIT ?""",
            (fts_query, limit),
        ).fetchall()

        import json

        results: list[dict[str, Any]] = []
        for r in rows:
            summary = r["summary"] or r["name"] or ""
            snippet = summary[:200]
            results.append({
                "id": r["id"],
                "kind": r["kind"],
                "name": r["name"],
                "path": r["path"],
                "start_line": r["start_line"],
                "end_line": r["end_line"],
                "summary": r["summary"],
                "content_hash": r["content_hash"],
                "summary_hash": r["summary_hash"],
                "updated_at": r["updated_at"],
                "snippet": snippet,
            })
        return results
    finally:
        conn.close()
