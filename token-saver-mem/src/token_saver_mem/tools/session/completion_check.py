"""completion_check tool — determine if session work is complete."""

from __future__ import annotations

from token_saver_mem.session_memory.extractor import extract_observations
from token_saver_mem.session_memory.state import derive_operational_state


def completion_check_tool(session_text: str) -> dict:
    """Check whether a session's work is complete based on session text.

    Derives OperationalState from text. Done = no pending items AND no blockers.
    Empty state (no observations at all) is NOT done (work was never tracked).

    Args:
        session_text: Raw agent session/conversation text.

    Returns:
        Dict with keys:
          - done: bool — True if all work complete
          - pending: list[str] — Pending item content strings
          - blockers: list[str] — Blocker content strings
    """
    observations = extract_observations(session_text)
    state = derive_operational_state(observations)

    pending = [item.content for item in state.pending_items]
    blockers = [item.content for item in state.blockers]

    # Empty state (no objective, no pending, no blockers, no completed) = not done
    if (
        state.objective is None
        and not pending
        and not blockers
        and not state.completed_items
    ):
        return {"done": False, "pending": [], "blockers": []}

    done = not pending and not blockers

    return {
        "done": done,
        "pending": pending,
        "blockers": blockers,
    }
