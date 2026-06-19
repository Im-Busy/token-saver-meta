"""open_work tool — list pending items and blockers from session text."""

from __future__ import annotations

from token_saver_mem.session_memory.extractor import extract_observations
from token_saver_mem.session_memory.state import derive_operational_state


def open_work_tool(session_text: str) -> dict:
    """List all open work items from session text.

    Derives OperationalState from text, then extracts pending items
    and blockers, ranked by priority (blockers first, then by confidence).

    Args:
        session_text: Raw agent session/conversation text.

    Returns:
        Dict with keys:
          - pending: list[dict] — pending items with content, confidence, entity_name
          - blockers: list[dict] — blockers with content, confidence, entity_name
          - has_open_work: bool — True if any pending or blockers remain
    """
    observations = extract_observations(session_text)
    state = derive_operational_state(observations)

    pending = [
        {
            "content": item.content,
            "confidence": item.confidence,
            "entity_name": item.entity_name,
            "is_blocker": False,
        }
        for item in state.pending_items
    ]

    blockers = [
        {
            "content": item.content,
            "confidence": item.confidence,
            "entity_name": item.entity_name,
            "is_blocker": True,
        }
        for item in state.blockers
    ]

    return {
        "pending": pending,
        "blockers": blockers,
        "has_open_work": state.has_open_work,
    }
