"""Operational state derivation from extracted observations.

Port of codex-agent-mem's operational_state.py with:
  - 10 observation types → operational state groups
  - Text normalization + stopword removal for dedup
  - 7 guardrail patterns for scope safety
  - OperationalState dataclass for type-safe state
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from token_saver_mem.session_memory.extractor import Observation, ObservationType

# ── Stopwords for text normalization ─────────────────────────────

_STATE_TEXT_STOPWORDS: set[str] = {"a", "an", "the", "is", "are", "still", "yet", "and"}


def normalize_state_text(value: str) -> str:
    """Normalize observation text for deduplication.

    Steps:
      1. Compact whitespace
      2. Lowercase
      3. Basic stemming (strip common suffixes for english)
      4. Normalize "still missing" → "missing", "no X yet" → "X missing"
      5. Strip punctuation
      6. Remove stopwords
      7. Normalize whitespace

    Args:
        value: Raw observation content text.

    Returns:
        Normalized, dedup-ready text string.
    """
    compact = " ".join((value or "").split()).casefold()

    # Normalize "is still missing" / "still missing" → " missing"
    compact = re.sub(r"\bis still missing\b", " missing", compact)
    compact = re.sub(r"\bstill missing\b", " missing", compact)
    compact = re.sub(r"\bno\s+(.+?)\s+yet\b", r"\1 missing", compact)

    # Remove punctuation
    compact = re.sub(r"[^\w\s]", " ", compact)
    compact = re.sub(r"\s+", " ", compact).strip()

    # Remove stopwords
    tokens = [t for t in compact.split() if t not in _STATE_TEXT_STOPWORDS]
    # Basic stemming: strip common suffixes for dedup matching.
    # Skip words where stemming would change meaning (e.g., "missing" → "miss").
    _STEM_SKIP: set[str] = {"missing", "finding", "testing", "processing", "building", "running"}
    stemmed: list[str] = []
    for token in tokens:
        if token in _STEM_SKIP:
            stemmed.append(token)
        elif token.endswith("ing") and len(token) > 5 and token[:-3] not in {"miss", "find", "test", "process", "build", "run"}:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("ly") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
            token = token[:-1]
        stemmed.append(token)
    return " ".join(stemmed)


def _state_token_set(value: str) -> set[str]:
    """Tokenize normalized text into a set for subset matching."""
    return set(normalize_state_text(value).split())


def _state_text_matches(left: str, right: str) -> bool:
    """Check if two normalized texts are semantically equivalent.

    Rules:
      1. Exact match
      2. Long text (≥18 chars) substring containment
      3. Token set equality
      4. Token set subset containment
    """
    if not left or not right:
        return False
    if left == right:
        return True
    if len(left) >= 18 and left in right:
        return True
    if len(right) >= 18 and right in left:
        return True
    left_tokens = _state_token_set(left)
    right_tokens = _state_token_set(right)
    if left_tokens and right_tokens:
        if left_tokens == right_tokens:
            return True
        if left_tokens.issubset(right_tokens) or right_tokens.issubset(left_tokens):
            return True
    return False


# ── OperationalState dataclass ───────────────────────────────────


@dataclass
class DodGroup:
    """Definition of Done items — what needs to be completed."""

    project_items: list[Observation] = field(default_factory=list)
    mission_items: list[Observation] = field(default_factory=list)
    session_items: list[Observation] = field(default_factory=list)

    @property
    def all_items(self) -> list[Observation]:
        return self.project_items + self.mission_items + self.session_items


@dataclass
class DodMissingGroup:
    """DoD items NOT yet completed."""

    project_items: list[Observation] = field(default_factory=list)
    mission_items: list[Observation] = field(default_factory=list)
    session_items: list[Observation] = field(default_factory=list)

    @property
    def all_items(self) -> list[Observation]:
        return self.project_items + self.mission_items + self.session_items


@dataclass
class OperationalState:
    """Full operational state derived from observations.

    Groups observations into operational categories and computes
    derived fields (guardrails, has_open_work, DoD gaps).
    """

    objective: Observation | None = None
    user_requests: list[Observation] = field(default_factory=list)
    constraints: list[Observation] = field(default_factory=list)
    dod: DodGroup = field(default_factory=DodGroup)
    dod_missing: DodMissingGroup = field(default_factory=DodMissingGroup)
    pending_items: list[Observation] = field(default_factory=list)
    completed_items: list[Observation] = field(default_factory=list)
    blockers: list[Observation] = field(default_factory=list)
    completion_claims: list[Observation] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    has_open_work: bool = False


# ── Deduplication ────────────────────────────────────────────────


def _dedupe_latest(items: list[Observation], limit: int) -> list[Observation]:
    """Deduplicate observations, keeping the most recent N.

    Uses normalize_state_text + _state_text_matches for semantic dedup.
    Stores normalized_text as a transient attribute on the Observation
    (via object.__setattr__ since it's frozen).
    """
    result: list[Observation] = []
    seen: list[str] = []
    for item in items:
        normalized = normalize_state_text(item.content)
        if not normalized:
            continue
        if any(_state_text_matches(normalized, existing) for existing in seen):
            continue
        seen.append(normalized)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _is_resolved(pending_content: str, completed_contents: set[str]) -> bool:
    """Check if a pending item has been resolved by a completed item."""
    for completed in completed_contents:
        if _state_text_matches(pending_content, completed):
            return True
    return False


def _unresolved_items(
    items: list[Observation],
    completed_contents: set[str],
) -> list[Observation]:
    """Filter items to only those not resolved by completed items."""
    return [
        item
        for item in items
        if not _is_resolved(normalize_state_text(item.content), completed_contents)
    ]


# ── Main derivation function ─────────────────────────────────────


def derive_operational_state(observations: list[Observation]) -> OperationalState:
    """Derive operational state from a list of observations.

    Mapping of ObservationType → state group:
      - OBJECTIVE → objective, user_requests
      - BLOCKER, RISK → blockers
      - TODO → pending_items, dod.session_items
      - DECISION (completion) → completed_items, completion_claims
      - DECISION (non-completion) → dod.project_items
      - FINDING → dod.mission_items
      - CONVENTION, PATTERN, ASSUMPTION, DEPENDENCY → constraints

    Args:
        observations: List of extracted Observations.

    Returns:
        OperationalState with grouped, deduplicated observations and guardrails.
    """
    if not observations:
        return OperationalState()

    # Group by observation type
    objectives: list[Observation] = []
    blockers_raw: list[Observation] = []
    todos: list[Observation] = []
    decisions: list[Observation] = []
    completions: list[Observation] = []
    findings: list[Observation] = []
    constraints_raw: list[Observation] = []

    _COMPLETION_KW = (
        "completed", "done", "finished", "deployed", "resolved", "merged",
        "complete", "fixed", "all work is", "all done",
    )

    for obs in observations:
        if obs.obs_type == ObservationType.OBJECTIVE:
            objectives.append(obs)
        elif obs.obs_type == ObservationType.BLOCKER:
            blockers_raw.append(obs)
        elif obs.obs_type == ObservationType.RISK:
            blockers_raw.append(obs)  # Risks are treated as potential blockers
        elif obs.obs_type == ObservationType.TODO:
            todos.append(obs)
        elif obs.obs_type == ObservationType.DECISION:
            decisions.append(obs)  # All decisions are completed thoughts
            content_lower = obs.content.lower()
            if any(kw in content_lower for kw in _COMPLETION_KW):
                completions.append(obs)
        elif obs.obs_type == ObservationType.FINDING:
            findings.append(obs)
        elif obs.obs_type in (
            ObservationType.CONVENTION,
            ObservationType.PATTERN,
            ObservationType.ASSUMPTION,
            ObservationType.DEPENDENCY,
        ):
            constraints_raw.append(obs)

    # Deduplicate each group
    objective_candidates = _dedupe_latest(objectives, limit=1)
    request_candidates = _dedupe_latest(objectives, limit=4)
    constraints = _dedupe_latest(constraints_raw, limit=4)
    pending_candidates = _dedupe_latest(todos, limit=6)
    completed_items = _dedupe_latest(decisions, limit=6)  # All decisions = completed
    blockers = _dedupe_latest(blockers_raw, limit=4)
    completion_claims = _dedupe_latest(completions, limit=3)
    project_dod = _dedupe_latest(decisions, limit=6)
    mission_dod = _dedupe_latest(findings, limit=6)
    session_dod = _dedupe_latest(todos, limit=6)

    # Resolve pending against completed
    completed_contents = {normalize_state_text(item.content) for item in completed_items}
    pending_items = _unresolved_items(pending_candidates, completed_contents)
    project_dod_missing = _unresolved_items(project_dod, completed_contents)
    mission_dod_missing = _unresolved_items(mission_dod, completed_contents)
    session_dod_missing = _unresolved_items(session_dod, completed_contents)
    all_dod_missing = project_dod_missing + mission_dod_missing + session_dod_missing

    # Pick objective
    objective = None
    if objective_candidates:
        objective = objective_candidates[0]
    elif request_candidates:
        objective = request_candidates[0]

    # ── Compute guardrails (7 patterns) ──────────────────────────

    guardrails: list[str] = []

    # 1: Pending work remains
    if pending_items:
        guardrails.append("Do not declare completion while pending work remains.")
        guardrails.append("Before closing, confirm each pending item explicitly.")

    # 2: Active user request scope
    if request_candidates:
        guardrails.append("Keep the active user request in scope; do not silently narrow it.")

    # 3: Blockers present
    if blockers:
        guardrails.append("If blockers remain, say blocked and list them instead of saying done.")

    # 4: DoD gaps
    if all_dod_missing:
        guardrails.append("Do not declare completion while Definition of Done items are still missing.")

    # 5: Completion claim conflicts with pending
    if completion_claims and pending_items:
        guardrails.append("A recent completion claim conflicts with open pending work. Re-check scope before closing.")

    # 6: Completion claim conflicts with DoD gaps
    if completion_claims and all_dod_missing:
        guardrails.append("A recent completion claim conflicts with Definition of Done gaps. Re-check closure before closing.")

    # 7: User request + pending (scope discipline)
    if request_candidates and pending_items:
        guardrails.append("Ensure pending items align with the active user request scope.")

    # Deduplicate guardrails while preserving order
    seen_guardrails: set[str] = set()
    unique_guardrails: list[str] = []
    for g in guardrails:
        if g not in seen_guardrails:
            seen_guardrails.add(g)
            unique_guardrails.append(g)

    has_open = bool(pending_items or blockers or all_dod_missing)

    return OperationalState(
        objective=objective,
        user_requests=request_candidates,
        constraints=constraints,
        dod=DodGroup(
            project_items=project_dod,
            mission_items=mission_dod,
            session_items=session_dod,
        ),
        dod_missing=DodMissingGroup(
            project_items=project_dod_missing,
            mission_items=mission_dod_missing,
            session_items=session_dod_missing,
        ),
        pending_items=pending_items,
        completed_items=completed_items,
        blockers=blockers,
        completion_claims=completion_claims,
        guardrails=unique_guardrails,
        has_open_work=has_open,
    )
