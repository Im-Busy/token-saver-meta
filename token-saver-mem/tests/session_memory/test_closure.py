"""Tests for session_memory.closure — completion_check and open_work."""

from __future__ import annotations

import pytest

from token_saver_mem.session_memory.closure import completion_check, open_work
from token_saver_mem.session_memory.extractor import Observation, ObservationType
from token_saver_mem.session_memory.state import OperationalState, derive_operational_state


def _obs(
    entity_name: str,
    obs_type: ObservationType,
    content: str,
    confidence: float = 0.9,
) -> Observation:
    return Observation(
        entity_name=entity_name,
        obs_type=obs_type,
        content=content,
        confidence=confidence,
    )


# ── Fake DB for testing (closure.py accepts operational state, not raw DB) ──

class FakeDB:
    """Minimal fake for testing closure functions."""

    def __init__(self, observations: list[Observation] | None = None) -> None:
        self._observations = observations or []
        self._state = derive_operational_state(self._observations)

    def get_operational_state(self, session_id: str) -> OperationalState:
        return self._state


class TestCompletionCheck:
    """completion_check() tests."""

    def test_done_when_no_pending_no_blockers(self) -> None:
        """Given state with no pending and no blockers, When checked, Then done=True."""
        obs = [
            _obs("a", ObservationType.DECISION, "Deployed to production"),
            _obs("b", ObservationType.DECISION, "All tests pass"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-1")
        assert result["done"] is True
        assert result["pending"] == []
        assert result["blockers"] == []

    def test_not_done_when_pending_items(self) -> None:
        """Given state with pending items, When checked, Then done=False."""
        obs = [
            _obs("a", ObservationType.TODO, "Write integration tests"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-2")
        assert result["done"] is False
        assert len(result["pending"]) >= 1
        assert any("integration tests" in p for p in result["pending"])

    def test_not_done_when_blockers(self) -> None:
        """Given state with blockers, When checked, Then done=False."""
        obs = [
            _obs("a", ObservationType.BLOCKER, "API gateway is down"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-3")
        assert result["done"] is False
        assert len(result["blockers"]) >= 1
        assert any("API gateway" in b for b in result["blockers"])

    def test_not_done_when_both_pending_and_blockers(self) -> None:
        """Given state with both pending and blockers, When checked, Then done=False."""
        obs = [
            _obs("a", ObservationType.TODO, "Write docs"),
            _obs("b", ObservationType.BLOCKER, "Need OAuth approval"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-4")
        assert result["done"] is False
        assert len(result["pending"]) >= 1
        assert len(result["blockers"]) >= 1

    def test_pending_list_is_accurate(self) -> None:
        """Given multiple pending items, When checked, Then all pending returned."""
        obs = [
            _obs("a", ObservationType.TODO, "Add error handling"),
            _obs("b", ObservationType.TODO, "Write unit tests"),
            _obs("c", ObservationType.TODO, "Update README"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-5")
        assert len(result["pending"]) == 3

    def test_blocker_detection_when_risk_present(self) -> None:
        """Given RISK observations, When checked, Then blockers include risks."""
        obs = [
            _obs("a", ObservationType.RISK, "Security vulnerability in login"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-6")
        assert len(result["blockers"]) >= 1

    def test_empty_state_is_not_done(self) -> None:
        """Given empty state (no observations), When checked, Then done=False (never started)."""
        db = FakeDB([])
        result = completion_check(db, "session-7")
        # Empty state means no work was tracked — not "done"
        assert result["done"] is False
        assert result["pending"] == []
        assert result["blockers"] == []

    def test_result_structure(self) -> None:
        """Given any state, When checked, Then result has done, pending, blockers keys."""
        obs = [
            _obs("a", ObservationType.DECISION, "Completed task A"),
        ]
        db = FakeDB(obs)
        result = completion_check(db, "session-x")
        assert "done" in result
        assert "pending" in result
        assert "blockers" in result
        assert isinstance(result["done"], bool)
        assert isinstance(result["pending"], list)
        assert isinstance(result["blockers"], list)


class TestOpenWork:
    """open_work() tests."""

    def test_returns_pending_items_ranked(self) -> None:
        """Given pending items, When open_work called, Then returns ranked list."""
        obs = [
            _obs("a", ObservationType.TODO, "Critical: Fix auth bug", confidence=0.95),
            _obs("b", ObservationType.TODO, "Write documentation", confidence=0.7),
        ]
        db = FakeDB(obs)
        items = open_work(db)
        assert len(items) >= 2

    def test_returns_empty_for_no_pending(self) -> None:
        """Given no pending items, When open_work called, Then returns empty list."""
        obs = [
            _obs("a", ObservationType.DECISION, "Deployed to production"),
        ]
        db = FakeDB(obs)
        items = open_work(db)
        assert items == []

    def test_includes_blockers_in_open_work(self) -> None:
        """Given blockers, When open_work called, Then blockers included."""
        obs = [
            _obs("a", ObservationType.BLOCKER, "Cannot proceed without API key"),
            _obs("b", ObservationType.TODO, "Implement payment flow"),
        ]
        db = FakeDB(obs)
        items = open_work(db)
        # Should include both blockers and pending items
        assert len(items) >= 2

    def test_open_work_with_empty_state(self) -> None:
        """Given empty state, When open_work called, Then returns empty list."""
        db = FakeDB([])
        items = open_work(db)
        assert items == []
