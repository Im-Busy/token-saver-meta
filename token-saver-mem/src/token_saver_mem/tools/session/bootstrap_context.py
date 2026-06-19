"""bootstrap_context tool — scope resolve + context pack in one MCP call."""

from __future__ import annotations

from token_saver_mem.session_memory.bootstrap import bootstrap_context
from token_saver_mem.session_memory.caching import stable_hash


def bootstrap_context_tool(
    session_text: str,
    *,
    project_path: str | None = None,
) -> dict:
    """Bootstrap context: detect project scope + build context pack.

    Args:
        session_text: Raw agent session/conversation text.
        project_path: Optional path to project root for filesystem scope detection.
                      Falls back to text-based detection if None or nonexistent.

    Returns:
        Dict with keys:
          - scope: dict with language, project_type, frameworks, key_files
          - context_pack: dict with text, stats, hash
    """
    result = bootstrap_context(session_text, project_path=project_path)
    return {
        "scope": dict(result.scope),
        "context_pack": {
            "text": result.context_pack.text,
            "stats": {
                "session_id": result.context_pack.stats.session_id,
                "budget_used": result.context_pack.stats.budget_used,
                "char_count": result.context_pack.stats.char_count,
                "token_estimate": result.context_pack.stats.token_estimate,
                "observation_count": result.context_pack.stats.observation_count,
            },
            "hash": stable_hash(result.context_pack.text),
        },
    }
