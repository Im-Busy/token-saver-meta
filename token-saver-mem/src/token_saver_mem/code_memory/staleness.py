"""staleness.py — summary_hash vs content_hash divergence detection.

Ported from Loom's query/delta.py staleness logic. Pure SQL + Python.
"""

from __future__ import annotations

import json

from token_saver_mem.code_memory.db import get_connection


def check_staleness(db_path: str) -> list[dict]:
    """Return list of nodes where summary_hash != content_hash (stale summaries).

    A node is stale when:
    - summary_hash IS NOT NULL and summary_hash != content_hash (content changed)
    - summary_hash IS NULL (never summarized)

    Args:
        db_path: Path to the SQLite database.

    Returns:
        List of dicts with keys: id, name, path, kind, summary_hash, content_hash.
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT id, name, path, kind, summary_hash, content_hash, metadata
               FROM code_nodes
               WHERE deleted_at IS NULL
                 AND (summary_hash IS NULL
                      OR summary_hash != content_hash)
               ORDER BY updated_at DESC"""
        ).fetchall()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "kind": r["kind"],
                "summary_hash": r["summary_hash"],
                "content_hash": r["content_hash"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
            }
            for r in rows
        ]
    finally:
        conn.close()


def mark_fresh(db_path: str, node_id: str) -> bool:
    """Set summary_hash = content_hash for a node, marking it as fresh.

    Args:
        db_path: Path to the SQLite database.
        node_id: Exact node ID (e.g. "function:utils.py:add").

    Returns:
        True if the node was found and updated, False if node not found.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT content_hash FROM code_nodes WHERE id = ? AND deleted_at IS NULL",
            (node_id,),
        ).fetchone()

        if row is None:
            return False

        conn.execute(
            "UPDATE code_nodes SET summary_hash = content_hash WHERE id = ?",
            (node_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()
