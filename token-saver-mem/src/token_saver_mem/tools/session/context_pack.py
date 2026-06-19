"""context_pack tool — wraps build_context_pack with hash caching for MCP."""

from __future__ import annotations

from token_saver_mem.session_memory.caching import stable_hash
from token_saver_mem.session_memory.continuity import build_context_pack


def context_pack_tool(session_text: str, *, budget: str = "auto") -> dict:
    """Build a context pack from session text with caching hash.

    Args:
        session_text: Raw agent session/conversation text.
        budget: Budget tier ("micro", "normal", "full", "auto"). Default "auto".

    Returns:
        Dict with keys:
          - text: str — Markdown-formatted context pack
          - stats: dict — serialized PackStats (session_id, budget_used, char_count,
            token_estimate, observation_count)
          - hash: str — 64-char SHA-256 hex digest of pack text (for caching)
    """
    pack = build_context_pack(session_text, budget=budget)
    return {
        "text": pack.text,
        "stats": {
            "session_id": pack.stats.session_id,
            "budget_used": pack.stats.budget_used,
            "char_count": pack.stats.char_count,
            "token_estimate": pack.stats.token_estimate,
            "observation_count": pack.stats.observation_count,
        },
        "hash": stable_hash(pack.text),
    }
