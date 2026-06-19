"""Session closure detection — determine if work is complete.

Port of codex-agent-mem's completion_check and open_work logic.

completion_check: done=True when no pending items AND no blockers remain.
open_work: list all pending items and blockers ranked by priority.
"""

from __future__ import annotations

from typing import Any, Protocol

from token_saver_mem.session_memory.extractor import Observation
from token_saver_mem.session_memory.state import OperationalState, derive_operational_state


# ── DB interface (minimal protocol) ──────────────────────────────


class HasOperationalState(Protocol):
    """Protocol for any DB/repository that can provide operational state."""

    def get_operational_state(self, session_id: str) -> OperationalState:
        """Return the operational state for a session."""
        ...


# ── completion_check ─────────────────────────────────────────────


def completion_check(
    db: HasOperationalState,
    session_id: str,
) -> dict[str, Any]:
    """Check whether a session's work is complete.

    Done = no pending items AND no blockers remain.
    An empty state (no observations at all) is considered NOT done
    (work was never started/tracked).

    Args:
        db: Object implementing get_operational_state(session_id).
        session_id: Session identifier.

    Returns:
        Dict with keys:
          - done: bool — True if all work complete
          - pending: list[str] — Pending item content strings
          - blockers: list[str] — Blocker content strings
    """
    state = db.get_operational_state(session_id)

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


# ── open_work ────────────────────────────────────────────────────


def open_work(db: HasOperationalState) -> list[dict[str, Any]]:
    """List all open work items ranked by priority.

    Includes both pending items and blockers.
    Ranked by: confidence (higher first), then blocker status (blockers first).

    Args:
        db: Object implementing get_operational_state(session_id). Uses a
            default session lookup (implementation-specific).

    Returns:
        List of dicts with keys:
          - content: str
          - is_blocker: bool
          - confidence: float
    """
    # Obtain state — use a sentinel session_id for global open work
    state = db.get_operational_state("__open_work__")

    items: list[dict[str, Any]] = []

    for item in state.blockers:
        items.append({
            "content": item.content,
            "is_blocker": True,
            "confidence": item.confidence,
            "entity_name": item.entity_name,
        })

    for item in state.pending_items:
        items.append({
            "content": item.content,
            "is_blocker": False,
            "confidence": item.confidence,
            "entity_name": item.entity_name,
        })

    # Sort: blockers first, then by confidence descending
    items.sort(key=lambda x: (not x["is_blocker"], -x["confidence"]))

    return items
