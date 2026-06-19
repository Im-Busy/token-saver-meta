"""get_context — retrieve full context packet for a code node.

Returns node metadata plus staleness assessment based on
summary_hash vs content_hash comparison.
"""

from __future__ import annotations

import json
from typing import Any

from token_saver_mem.code_memory.db import get_connection


def get_context(db_path: str, node_id: str) -> dict[str, Any]:
    """Retrieve full context information for a code node.

    Args:
        db_path: Path to the SQLite database.
        node_id: Exact node ID (e.g. "function:utils.py:add").

    Returns:
        Dict with keys: id, name, path, kind, start_line, end_line,
        summary_text, staleness_status, content_hash, summary_hash, metadata.

    Raises:
        ValueError: If node_id is not found in the database.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT id, kind, name, path, start_line, end_line,
                      summary, summary_hash, content_hash, metadata, updated_at
               FROM code_nodes
               WHERE id = ? AND deleted_at IS NULL""",
            (node_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"node not found: {node_id}")

        # Determine staleness
        if row["summary"] is None or row["summary_hash"] is None:
            staleness = "stale"
        elif row["summary_hash"] == row["content_hash"]:
            staleness = "fresh"
        else:
            staleness = "stale"

        return {
            "id": row["id"],
            "name": row["name"],
            "path": row["path"],
            "kind": row["kind"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "summary_text": row["summary"],
            "staleness_status": staleness,
            "content_hash": row["content_hash"],
            "summary_hash": row["summary_hash"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()
