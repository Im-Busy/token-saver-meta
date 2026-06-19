"""delta.py — SQL-based delta payload computation.

Ported from Loom's query/delta.py. Pure SQL — no async, no tree-sitter.
Computes what changed since a given Unix timestamp.
"""

from __future__ import annotations

import json
from typing import Any

from token_saver_mem.code_memory.db import get_connection


def get_delta_payload(
    db_path: str,
    since_ts: float,
    *,
    include_details: bool = False,
) -> dict[str, Any]:
    """Compute what changed since a given Unix timestamp.

    Args:
        db_path: Path to the SQLite database.
        since_ts: Unix timestamp — return nodes with updated_at > this.
        include_details: If True, include full node dicts in 'nodes' and
            'deleted_nodes' keys. Default False returns summary counts only.

    Returns:
        Dict with keys: changed, deleted, total, (nodes, deleted_nodes if details).
    """
    conn = get_connection(db_path)
    try:
        changed_count = conn.execute(
            """SELECT COUNT(*) FROM code_nodes
               WHERE updated_at > ?
                 AND deleted_at IS NULL""",
            (since_ts,),
        ).fetchone()[0]

        deleted_count = conn.execute(
            """SELECT COUNT(*) FROM code_nodes
               WHERE deleted_at IS NOT NULL
                 AND deleted_at > ?""",
            (since_ts,),
        ).fetchone()[0]

        result: dict[str, Any] = {
            "changed": changed_count,
            "deleted": deleted_count,
            "total": changed_count + deleted_count,
        }

        if include_details:
            changed_rows = conn.execute(
                """SELECT id, name, path, kind, start_line, end_line,
                          content_hash, summary_hash, metadata
                   FROM code_nodes
                   WHERE updated_at > ?
                     AND deleted_at IS NULL
                   ORDER BY updated_at DESC""",
                (since_ts,),
            ).fetchall()

            deleted_rows = conn.execute(
                """SELECT id, name, path, kind, deleted_at
                   FROM code_nodes
                   WHERE deleted_at IS NOT NULL
                     AND deleted_at > ?
                   ORDER BY deleted_at DESC""",
                (since_ts,),
            ).fetchall()

            result["nodes"] = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "path": r["path"],
                    "kind": r["kind"],
                    "start_line": r["start_line"],
                    "end_line": r["end_line"],
                    "content_hash": r["content_hash"],
                    "summary_hash": r["summary_hash"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "change_type": "modified",
                }
                for r in changed_rows
            ]

            result["deleted_nodes"] = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "path": r["path"],
                    "kind": r["kind"],
                    "deleted_at": r["deleted_at"],
                    "change_type": "deleted",
                }
                for r in deleted_rows
            ]

        return result
    finally:
        conn.close()
