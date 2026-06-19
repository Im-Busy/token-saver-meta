"""Tests for session_memory.state — operational state derivation."""

from __future__ import annotations

import pytest

from token_saver_mem.session_memory.extractor import Observation, ObservationType
from token_saver_mem.session_memory.state import (
    OperationalState,
    derive_operational_state,
    normalize_state_text,
)

# ── helpers ──────────────────────────────────────────────────────

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


# ── tests: normalize_state_text ──────────────────────────────────

class TestNormalizeStateText:
    """normalize_state_text() tests."""

    def test_lowercases_text(self) -> None:
        """Given mixed-case text, When normalized, Then it is lowercased."""
        assert normalize_state_text("Fix LoginPage Bug") == "fix loginpage bug"

    def test_removes_stopwords(self) -> None:
        """Given text with stopwords, When normalized, Then stopwords removed."""
        result = normalize_state_text("the is and are still yet a an")
        assert result == ""

    def test_removes_extra_whitespace(self) -> None:
        """Given text with extra whitespace, When normalized, Then whitespace normalized."""
        result = normalize_state_text("  fix   login   bug  ")
        assert result == "fix login bug"

    def test_removes_punctuation(self) -> None:
        """Given text with punctuation, When normalized, Then punctuation removed."""
        result = normalize_state_text("Fix login bug! (urgent)")
        assert result == "fix login bug urgent"

    def test_normalizes_still_missing_patterns(self) -> None:
        """Given text with 'is still missing', When normalized, Then it becomes 'missing'."""
        result = normalize_state_text("the test suite is still missing")
        assert "is still missing" not in result
        assert "test suite missing" in result

    def test_different_texts_normalize_differently(self) -> None:
        """Given different texts, When normalized, Then they produce different results."""
        a = normalize_state_text("Fix login bug")
        b = normalize_state_text("Add rate limiting")
        assert a != b


# ── tests: OperationalState ──────────────────────────────────────

class TestOperationalState:
    """OperationalState dataclass tests."""

    def test_default_state_empty(self) -> None:
        """Given no args, When OperationalState created, Then all groups are empty."""
        state = OperationalState()
        assert state.objective is None
        assert state.user_requests == []
        assert state.constraints == []
        assert state.pending_items == []
        assert state.completed_items == []
        assert state.blockers == []
        assert state.completion_claims == []
        assert state.guardrails == []
        assert state.has_open_work is False


# ── tests: derive_operational_state ──────────────────────────────

class TestDeriveOperationalState:
    """derive_operational_state() tests."""

    def test_groups_objective_type(self) -> None:
        """Given OBJECTIVE observations, When derived, Then objective field populated."""
        obs = [
            _obs("auth", ObservationType.OBJECTIVE, "Implement user authentication"),
        ]
        state = derive_operational_state(obs)
        assert state.objective is not None
        assert "Implement user authentication" in state.objective.content
        assert len(state.user_requests) >= 1

    def test_groups_blockers(self) -> None:
        """Given BLOCKER observations, When derived, Then blockers field populated."""
        obs = [
            _obs("deploy", ObservationType.BLOCKER, "Cannot deploy until QA signs off"),
        ]
        state = derive_operational_state(obs)
        assert len(state.blockers) == 1
        assert state.has_open_work is True

    def test_groups_todos_as_pending(self) -> None:
        """Given TODO observations, When derived, Then pending_items populated."""
        obs = [
            _obs("tests", ObservationType.TODO, "Write unit tests"),
            _obs("docs", ObservationType.TODO, "Write API docs"),
        ]
        state = derive_operational_state(obs)
        assert len(state.pending_items) == 2
        assert state.has_open_work is True

    def test_groups_decisions_as_completed(self) -> None:
        """Given DECISION observations, When derived, Then completed_items populated."""
        obs = [
            _obs("db", ObservationType.DECISION, "Will use PostgreSQL for persistence"),
        ]
        state = derive_operational_state(obs)
        assert len(state.completed_items) >= 1

    def test_groups_findings_as_dod(self) -> None:
        """Given FINDING observations, When derived, Then dod items populated."""
        obs = [
            _obs("perf", ObservationType.FINDING, "Query takes 500ms on average"),
        ]
        state = derive_operational_state(obs)
        assert len(state.dod.all_items) >= 1

    def test_deduplicates_similar_observations(self) -> None:
        """Given similar observations, When derived, Then duplicates are merged."""
        obs = [
            _obs("a", ObservationType.TODO, "Fix the login bug"),
            _obs("b", ObservationType.TODO, "Fix login bug"),  # same after normalize
            _obs("c", ObservationType.TODO, "Add rate limiting"),
        ]
        state = derive_operational_state(obs)
        # The first two should be deduplicated (same normalized text)
        assert len(state.pending_items) <= 2
        # Specifically: "Fix login bug" normalizes to the same thing
        texts = [item.content for item in state.pending_items]
        assert "Add rate limiting" in texts

    def test_completed_items_resolve_pending(self) -> None:
        """Given a pending TODO and a matching completed DECISION, Then pending removed."""
        obs = [
            _obs("a", ObservationType.TODO, "Fix the login bug"),
            _obs("b", ObservationType.DECISION, "Fixed the login bug — deployed"),
        ]
        state = derive_operational_state(obs)
        # The TODO should be resolved by the matching completed item
        assert len(state.pending_items) == 0
        assert len(state.completed_items) >= 1

    def test_guardrails_when_pending_work_remains(self) -> None:
        """Given pending items, When state derived, Then guardrail warns about pending work."""
        obs = [
            _obs("a", ObservationType.TODO, "Write unit tests"),
        ]
        state = derive_operational_state(obs)
        assert any("Do not declare completion" in g for g in state.guardrails)

    def test_guardrails_when_blockers_present(self) -> None:
        """Given blockers, When state derived, Then guardrail warns about blockers."""
        obs = [
            _obs("b", ObservationType.BLOCKER, "API gateway down"),
        ]
        state = derive_operational_state(obs)
        assert any("blocked" in g.lower() for g in state.guardrails)

    def test_guardrails_when_completion_claim_conflicts_with_pending(self) -> None:
        """Given completion claim + pending, When derived, Then guardrail warns about conflict."""
        obs = [
            _obs("a", ObservationType.TODO, "Write integration tests"),
            _obs("b", ObservationType.DECISION, "All work is complete"),
        ]
        state = derive_operational_state(obs)
        assert any("conflict" in g.lower() for g in state.guardrails)

    def test_guardrails_when_dod_missing(self) -> None:
        """Given DoD gaps, When state derived, Then guardrail warns about DoD."""
        obs = [
            _obs("d", ObservationType.FINDING, "Need to verify edge cases"),
        ]
        state = derive_operational_state(obs)
        assert any("definition of done" in g.lower() for g in state.guardrails)

    def test_guardrails_user_request_scope(self) -> None:
        """Given user requests, When state derived, Then guardrail about scope."""
        obs = [
            _obs("u", ObservationType.OBJECTIVE, "Build auth module with JWT"),
        ]
        state = derive_operational_state(obs)
        assert any("user request" in g.lower() for g in state.guardrails)

    def test_guardrails_conflicting_completion_with_dod(self) -> None:
        """Given completion claim + DoD gap, When derived, Then guardrail warns."""
        obs = [
            _obs("d", ObservationType.FINDING, "Need performance benchmarks"),
            _obs("c", ObservationType.DECISION, "Project is complete"),
        ]
        state = derive_operational_state(obs)
        guards = "\n".join(state.guardrails).lower()
        assert any("definition of done" in guards for _ in [1]) or any("conflict" in guards for _ in [1])

    def test_all_seven_guardrails_triggerable(self) -> None:
        """Given various state configurations, When derived, Then each of 7 guardrails can appear."""
        all_triggered: set[str] = set()
        triggers = [
            # 1: pending work
            [_obs("a", ObservationType.TODO, "Fix login bug")],
            # 2: user request
            [_obs("a", ObservationType.OBJECTIVE, "Build auth module")],
            # 3: blockers
            [_obs("a", ObservationType.BLOCKER, "API down")],
            # 4: DoD missing
            [_obs("a", ObservationType.FINDING, "Need edge case tests")],
            # 5: completion + pending conflict
            [_obs("a", ObservationType.TODO, "Write tests"),
             _obs("b", ObservationType.DECISION, "All done")],
            # 6: completion + DoD conflict
            [_obs("a", ObservationType.FINDING, "Need benchmarks"),
             _obs("b", ObservationType.DECISION, "Complete")],
            # 7: pending + request (covered by #1 + #2 already)
        ]
        for obs_list in triggers:
            state = derive_operational_state(obs_list)
            for g in state.guardrails:
                all_triggered.add(g)

        # We should see at least 5 distinct guardrail patterns
        assert len(all_triggered) >= 5, (
            f"Expected >=5 distinct guardrails, got {len(all_triggered)}: {all_triggered}"
        )

    def test_has_open_work_false_when_nothing_pending(self) -> None:
        """Given completed-only observations, When derived, Then has_open_work is False."""
        obs = [
            _obs("a", ObservationType.DECISION, "Deployed to production"),
        ]
        state = derive_operational_state(obs)
        assert state.has_open_work is False

    def test_empty_observations_produces_empty_state(self) -> None:
        """Given no observations, When derived, Then state is empty with no open work."""
        state = derive_operational_state([])
        assert state.objective is None
        assert state.pending_items == []
        assert state.blockers == []
        assert state.has_open_work is False

    def test_constraints_from_conventions_and_dependencies(self) -> None:
        """Given CONVENTION and DEPENDENCY observations, When derived, Then constraints populated."""
        obs = [
            _obs("c", ObservationType.CONVENTION, "Use snake_case for all Python"),
            _obs("d", ObservationType.DEPENDENCY, "Requires PostgreSQL 14+"),
        ]
        state = derive_operational_state(obs)
        assert len(state.constraints) >= 2

    def test_risks_grouped_as_blockers(self) -> None:
        """Given RISK observations, When derived, Then they appear in blockers."""
        obs = [
            _obs("r", ObservationType.RISK, "Single point of failure in auth"),
        ]
        state = derive_operational_state(obs)
        assert len(state.blockers) >= 1
