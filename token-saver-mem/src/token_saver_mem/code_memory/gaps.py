"""gaps.py — annotation gap detection and visit logging for code_memory.

Identifies code nodes that need annotation (missing or stale summaries)
and records agent visits for usage tracking.
"""

from __future__ import annotations

import time

from token_saver_mem.code_memory.db import get_connection


def get_annotation_gaps(db_path: str, limit: int = 10) -> list[dict]:
    """Return ranked list of nodes needing annotation work.

    Ranking:
      1. No summary at all (has_summary=False) — highest priority
      2. Stale summary (summary_hash != content_hash) — medium priority
    Within each tier, ordered by most-recently-updated first.

    Args:
        db_path: Path to the SQLite database.
        limit: Maximum number of results to return.

    Returns:
        List of dicts: {node_id, name, path, kind, stale_reason, has_summary}.
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT id, name, path, kind, summary, summary_hash, content_hash
               FROM code_nodes
               WHERE deleted_at IS NULL
                 AND (summary IS NULL OR summary_hash != content_hash)
               ORDER BY
                 CASE WHEN summary IS NULL THEN 0 ELSE 1 END,
                 updated_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

        return [
            {
                "node_id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "kind": r["kind"],
                "stale_reason": _reason(r["summary"], r["summary_hash"], r["content_hash"]),
                "has_summary": r["summary"] is not None,
            }
            for r in rows
        ]
    finally:
        conn.close()


def _reason(summary: str | None, summary_hash: str | None, content_hash: str | None) -> str:
    """Build a human-readable staleness reason string."""
    if summary is None:
        return "never summarized"
    if summary_hash != content_hash:
        return "content changed since last summary"
    return "unknown"


def log_visit(db_path: str, node_id: str, session_id: str) -> None:
    """Record that an agent visited a code node during a session.

    Uses upsert (INSERT OR REPLACE) so repeated visits update the timestamp.

    Args:
        db_path: Path to the SQLite database.
        node_id: Exact node ID (e.g. "function:utils.py:add").
        session_id: Agent session identifier.
    """
    conn = get_connection(db_path)
    try:
        conn.execute(
            """INSERT INTO node_visits (node_id, session_id, visited_at)
               VALUES (?, ?, ?)
               ON CONFLICT(node_id, session_id) DO UPDATE SET
                 visited_at = excluded.visited_at""",
            (node_id, session_id, time.time()),
        )
        conn.commit()
    finally:
        conn.close()
