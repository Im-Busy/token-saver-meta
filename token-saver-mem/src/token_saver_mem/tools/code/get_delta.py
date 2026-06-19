"""get_delta — compute what changed since a given timestamp.

Thin MCP-tool wrapper around code_memory.delta.get_delta_payload.
"""

from __future__ import annotations

from typing import Any

from token_saver_mem.code_memory.delta import get_delta_payload


def get_delta(db_path: str, since_ts: float) -> dict[str, Any]:
    """Compute what changed in the code_nodes table since a given Unix timestamp.

    Args:
        db_path: Path to the SQLite database.
        since_ts: Unix timestamp — return nodes with updated_at > this.

    Returns:
        Dict with keys: changed, deleted, total.
    """
    return get_delta_payload(db_path, since_ts)
