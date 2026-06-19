"""store_understanding — persist a human-readable summary for a code node.

Sets summary text and copies content_hash to summary_hash to mark the node
as fresh (summary is up-to-date with current content).
"""

from __future__ import annotations

from token_saver_mem.code_memory.db import get_connection


def store_understanding(db_path: str, node_id: str, summary: str) -> bool:
    """Store a summary/annotation for a code node.

    Updates the node's summary and sets summary_hash = content_hash,
    marking it as freshly understood (convention from staleness.py mark_fresh).

    Args:
        db_path: Path to the SQLite database.
        node_id: Exact node ID (e.g. "function:utils.py:add").
        summary: Human-readable summary text to associate with the node.

    Returns:
        True if the node was found and updated, False if node not found.
    """
    # Normalize Windows backslashes to POSIX forward slashes.
    # The indexer stores all paths with forward slashes (e.g. "C:/Dev/...").
    node_id = node_id.replace("\\", "/")

    conn = get_connection(db_path)
    try:
        # Check node exists and get current content_hash
        row = conn.execute(
            "SELECT id, content_hash FROM code_nodes WHERE id = ? AND deleted_at IS NULL",
            (node_id,),
        ).fetchone()

        if row is None:
            return False

        conn.execute(
            """UPDATE code_nodes
               SET summary = ?, summary_hash = ?
               WHERE id = ?""",
            (summary, row["content_hash"], node_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()
