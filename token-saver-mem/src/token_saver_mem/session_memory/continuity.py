"""Context pack builder — session continuity with 3 budget tiers.

Builds a Markdown-formatted context pack from session text, using
existing extractor + state modules. Three budget tiers control
what's included: micro (~500 chars), normal (~2000), full (~5000).

Architecture:
  - PackBudget: MICRO, NORMAL, FULL, AUTO
  - PackStats: metadata about the generated pack
  - ContextPack: text + stats + operational_state
  - build_context_pack(): main entry point
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from token_saver_mem.session_memory.extractor import extract_observations
from token_saver_mem.session_memory.state import OperationalState, derive_operational_state


# ── Budget tiers ──────────────────────────────────────────────────


class PackBudget(str, Enum):
    """Context pack budget tier.

    MICRO  — bare essentials (~500 chars): objective + open work
    NORMAL — key information (~2000 chars): micro + decisions + state
    FULL   — everything (~5000 chars): all observations, all details
    AUTO   — selects tier based on session word count
    """

    MICRO = "micro"
    NORMAL = "normal"
    FULL = "full"
    AUTO = "auto"


# ── Data classes ──────────────────────────────────────────────────


@dataclass
class PackStats:
    """Metadata about a generated context pack.

    Attributes:
        session_id: Session identifier (hash of session text).
        budget_used: Which budget tier was actually used.
        char_count: Number of characters in the pack text.
        token_estimate: Rough token count (ceil(chars/4)).
        observation_count: Total observations extracted.
    """

    session_id: str
    budget_used: str = "auto"
    char_count: int = 0
    token_estimate: int = 0
    observation_count: int = 0


@dataclass
class ContextPack:
    """A built context pack for session continuity.

    Attributes:
        text: Markdown-formatted context pack string.
        stats: PackStats with metadata.
        operational_state: Derived OperationalState from the session.
    """

    text: str
    stats: PackStats
    operational_state: OperationalState = field(default_factory=OperationalState)


# ── Budget selection ──────────────────────────────────────────────


def _select_budget(session_text: str, requested: str) -> str:
    """Select the actual budget tier based on session complexity.

    AUTO rules:
      - micro  if < 500 words
      - normal if < 2000 words
      - full   otherwise
    """
    if requested != "auto":
        return requested

    word_count = len(session_text.split())
    if word_count < 500:
        return "micro"
    elif word_count < 2000:
        return "normal"
    else:
        return "full"


def _estimate_tokens(char_count: int) -> int:
    """Rough token estimate: ceil(char_count / 4)."""
    return math.ceil(char_count / 4)


def _total_observations(state: OperationalState) -> int:
    """Count total observations in an OperationalState."""
    return (
        (1 if state.objective else 0)
        + len(state.user_requests)
        + len(state.constraints)
        + len(state.dod.all_items)
        + len(state.dod_missing.all_items)
        + len(state.pending_items)
        + len(state.completed_items)
        + len(state.blockers)
        + len(state.completion_claims)
    )


# ── Markdown section builders ─────────────────────────────────────


def _format_observation_list(items: list, *, prefix: str = "- ") -> str:
    """Format a list of observations as markdown bullet points.

    Args:
        items: Observation objects or plain content strings.
        prefix: Bullet prefix (default: "- ").

    Returns:
        Markdown-formatted bullet list, or "_(none)_" if empty.
    """
    if not items:
        return "_(none)_\n"

    parts: list[str] = []
    for item in items:
        if hasattr(item, "content"):
            parts.append(f"{prefix}{item.content}")
        else:
            parts.append(f"{prefix}{item}")
    return "\n".join(parts) + "\n"


def _build_section(title: str, body: str) -> str:
    """Build a Markdown section with ## header and body."""
    return f"## {title}\n{body}"


def _build_micro_pack(state: OperationalState) -> str:
    """Build a micro-tier pack: objective + open work only."""
    sections: list[str] = []

    # Objective
    obj_text = state.objective.content if state.objective else "_(none)_"
    sections.append(_build_section("Objective", f"{obj_text}\n"))

    # Open Work: blockers + pending
    open_parts: list[str] = []
    if state.blockers:
        open_parts.append("### Blockers")
        for b in state.blockers:
            open_parts.append(f"- {b.content}")
    if state.pending_items:
        open_parts.append("### Pending")
        for p in state.pending_items:
            open_parts.append(f"- {p.content}")
    if state.dod_missing.all_items:
        open_parts.append("### DoD Missing")
        for d in state.dod_missing.all_items:
            open_parts.append(f"- {d.content}")

    if open_parts:
        sections.append(_build_section("Open Work", "\n".join(open_parts) + "\n"))
    else:
        sections.append(_build_section("Open Work", "_(none)_\n"))

    return "\n".join(sections)


def _build_normal_pack(state: OperationalState) -> str:
    """Build a normal-tier pack: micro + key decisions + state summary."""
    sections: list[str] = []

    # Objective
    obj_text = state.objective.content if state.objective else "_(none)_"
    sections.append(_build_section("Objective", f"{obj_text}\n"))

    # Key Decisions
    if state.completed_items:
        dec_lines = "\n".join(f"- {d.content}" for d in state.completed_items)
        sections.append(_build_section("Key Decisions", f"{dec_lines}\n"))
    else:
        sections.append(_build_section("Key Decisions", "_(none)_\n"))

    # State Summary
    summary_lines: list[str] = []
    completed_count = len(state.completed_items)
    pending_count = len(state.pending_items)
    blocker_count = len(state.blockers)
    dod_missing_count = len(state.dod_missing.all_items)
    summary_lines.append(f"- Completed: {completed_count} items")
    summary_lines.append(f"- Pending: {pending_count} items")
    if blocker_count:
        summary_lines.append(f"- Blockers: {blocker_count}")
    if dod_missing_count:
        summary_lines.append(f"- DoD Missing: {dod_missing_count} items")
    if state.has_open_work:
        summary_lines.append("- Status: **OPEN WORK REMAINS**")
    else:
        summary_lines.append("- Status: all work complete")
    sections.append(_build_section("State Summary", "\n".join(summary_lines) + "\n"))

    # Open Work
    open_parts: list[str] = []
    if state.blockers:
        open_parts.append("### Blockers")
        for b in state.blockers:
            open_parts.append(f"- {b.content}")
    if state.pending_items:
        open_parts.append("### Pending Items")
        for p in state.pending_items:
            open_parts.append(f"- {p.content}")
    if state.dod_missing.all_items:
        open_parts.append("### DoD Missing")
        for d in state.dod_missing.all_items:
            open_parts.append(f"- {d.content}")

    if open_parts:
        sections.append(_build_section("Open Work", "\n".join(open_parts) + "\n"))
    else:
        sections.append(_build_section("Open Work", "_(none)_\n"))

    return "\n".join(sections)


def _build_full_pack(state: OperationalState) -> str:
    """Build a full-tier pack: everything — all observations, full state."""
    sections: list[str] = []

    # Objective
    obj_text = state.objective.content if state.objective else "_(none)_"
    sections.append(_build_section("Objective", f"{obj_text}\n"))

    # Open Work (blockers + pending + DoD missing)
    open_parts: list[str] = []
    if state.blockers:
        open_parts.append("### Blockers")
        for b in state.blockers:
            open_parts.append(f"- {b.content}")
    if state.pending_items:
        open_parts.append("### Pending Items")
        for p in state.pending_items:
            open_parts.append(f"- {p.content}")
    if state.dod_missing.all_items:
        open_parts.append("### DoD Missing")
        for d in state.dod_missing.all_items:
            open_parts.append(f"- {d.content}")
    if open_parts:
        sections.append(_build_section("Open Work", "\n".join(open_parts) + "\n"))
    else:
        sections.append(_build_section("Open Work", "_(none)_\n"))

    # Key Decisions
    if state.completed_items:
        dec_lines = "\n".join(f"- {d.content}" for d in state.completed_items)
        sections.append(_build_section("Key Decisions", f"{dec_lines}\n"))
    else:
        sections.append(_build_section("Key Decisions", "_(none)_\n"))

    # State Summary
    summary_lines: list[str] = []
    summary_lines.append(f"- Completed: {len(state.completed_items)} items")
    summary_lines.append(f"- Pending: {len(state.pending_items)} items")
    if state.blockers:
        summary_lines.append(f"- Blockers: {len(state.blockers)}")
    if state.dod_missing.all_items:
        summary_lines.append(f"- DoD Missing: {len(state.dod_missing.all_items)} items")
    if state.has_open_work:
        summary_lines.append("- Status: **OPEN WORK REMAINS**")
    else:
        summary_lines.append("- Status: all work complete")
    sections.append(_build_section("State Summary", "\n".join(summary_lines) + "\n"))

    # Constraints
    if state.constraints:
        con_lines = "\n".join(f"- {c.content}" for c in state.constraints)
        sections.append(_build_section("Constraints", f"{con_lines}\n"))
    else:
        sections.append(_build_section("Constraints", "_(none)_\n"))

    # Findings (from DoD mission_items = FINDING observations)
    if state.dod.mission_items:
        find_lines = "\n".join(f"- {d.content}" for d in state.dod.mission_items)
        sections.append(_build_section("Findings", f"{find_lines}\n"))

    # Completed Items (detailed)
    if state.completed_items:
        comp_lines = "\n".join(f"- {c.content}" for c in state.completed_items)
        sections.append(_build_section("Completed Items", f"{comp_lines}\n"))

    # Guardrails
    if state.guardrails:
        grd_lines = "\n".join(f"- {g}" for g in state.guardrails)
        sections.append(_build_section("Guardrails", f"{grd_lines}\n"))

    return "\n".join(sections)


# ── Main entry point ──────────────────────────────────────────────


def build_context_pack(
    session_text: str,
    *,
    budget: str = "auto",
) -> ContextPack:
    """Build a context pack from session text.

    Extracts observations, derives operational state, and formats
    a Markdown context pack according to the selected budget tier.

    Budget tiers:
      - micro:  objective + open work (blockers, pending, DoD missing)
      - normal: micro + key decisions + state summary
      - full:   everything — all observations, constraints, findings,
                completed items, guardrails
      - auto:   selects tier based on session word count
                (<500 words → micro, <2000 → normal, else full)

    Args:
        session_text: Raw agent session/conversation text.
        budget: Budget tier string ("micro", "normal", "full", "auto").
                Defaults to "auto".

    Returns:
        ContextPack with Markdown text, stats, and operational state.
    """
    # Validate budget
    if budget not in ("micro", "normal", "full", "auto"):
        raise ValueError(
            f"Unknown budget '{budget}'. "
            f"Must be one of: micro, normal, full, auto"
        )

    # Select actual budget
    actual_budget = _select_budget(session_text, budget)

    # Extract observations and derive state
    observations = extract_observations(session_text)
    state = derive_operational_state(observations)

    # Build pack text by tier
    if actual_budget == "micro":
        text = _build_micro_pack(state)
    elif actual_budget == "normal":
        text = _build_normal_pack(state)
    else:
        text = _build_full_pack(state)

    # Compute stats
    char_count = len(text)
    token_estimate = _estimate_tokens(char_count)
    total_obs = _total_observations(state)

    # Session ID from stable hash of text
    from token_saver_mem.session_memory.caching import stable_hash
    session_id = stable_hash(session_text)[:16]

    stats = PackStats(
        session_id=session_id,
        budget_used=actual_budget,
        char_count=char_count,
        token_estimate=token_estimate,
        observation_count=total_obs,
    )

    return ContextPack(text=text, stats=stats, operational_state=state)
