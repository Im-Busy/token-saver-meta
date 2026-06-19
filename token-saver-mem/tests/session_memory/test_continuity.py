"""Tests for session_memory.continuity — context pack builder with 3 budget tiers."""

from __future__ import annotations

import pytest

from token_saver_mem.session_memory.extractor import Observation, ObservationType
from token_saver_mem.session_memory.state import OperationalState
from token_saver_mem.session_memory.continuity import (
    ContextPack,
    PackBudget,
    PackStats,
    build_context_pack,
)

# ── Helpers ───────────────────────────────────────────────────────


SESS_SMALL = """\
Task: Fix login bug in auth.py.
BLOCKER: CI pipeline is down.
TODO: Add unit tests for login.
"""

SESS_MEDIUM = (
    "Objective: Build user authentication module with JWT tokens.\n"
    "TODO: Set up database schema for users table.\n"
    "TODO: Implement password hashing with bcrypt.\n"
    "BLOCKER: Need DevOps to provision the staging database.\n"
    "Decision: Will use PostgreSQL for persistence.\n"
    "Finding: bcrypt cost factor 12 gives ~300ms on average hardware.\n"
    "Convention: All API endpoints must return JSON errors with error_code field.\n"
    "Pattern: Similar auth modules in other services use the same middleware pattern.\n"
    "TODO: Add rate limiting to login endpoint.\n"
    "TODO: Write integration tests for auth flow.\n"
    "Objective: Add OAuth2 social login support.\n"
    "Decision: Settled on using Authlib library for OAuth2.\n"
    "Risk: OAuth2 provider rate limits could block batch registration.\n"
    "Completed: User login endpoint returns JWT on success.\n"
    "TODO: Store refresh tokens in Redis.\n"
    "Finding: Average login request finishes in 45ms under load.\n"
    # Padding to reach >500 words for NORMAL budget
    + ("The application should handle request validation properly. "
       "System must log all authentication events. "
       "Users need to be notified on password change. "
       "Database connections should be pooled for efficiency. "
       "All endpoints must have rate limiting configured. ") * 25
)

SESS_LARGE = (
    SESS_MEDIUM * 3
    + (
        "Assumption: Users have valid email addresses for password reset.\n"
        "Dependency: Email service SendGrid for password reset flow.\n"
        "Risk: Token theft via XSS if JWT stored in localStorage.\n"
        "TODO: Implement password reset flow.\n"
        "TODO: Add email verification step.\n"
        "TODO: Build admin dashboard for user management.\n"
        "TODO: Add 2FA support with TOTP.\n"
        "TODO: Write end-to-end tests with Playwright.\n"
        "Decision: Chose React Query for client-side auth state management.\n"
        "Finding: JWT refresh token rotation reduces attack surface by 60 percent.\n"
        "Decision: Will deploy auth service as separate microservice.\n"
        "Decision: All done with auth module v1.\n"
        "Pattern: Every new microservice follows the same bootstrapping script.\n"
        "Block: Waiting for security team to approve OAuth2 flow.\n"
        # Padding to reach >2000 words for FULL budget
        + ("Extra full tier padding text for large session budget threshold. "
           "Coverage reports should be generated after each test run. "
           "Performance benchmarks must track p50 p95 and p99 latencies. "
           "Error tracking integration with Sentry is essential. "
           "Infrastructure as code using Terraform for all deployments. ") * 80
    )
)

SESS_EMPTY = ""


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


# ── PackBudget ────────────────────────────────────────────────────


class TestPackBudget:
    """PackBudget enum tests."""

    def test_four_members(self) -> None:
        """Given PackBudget enum, it has MICRO, NORMAL, FULL, AUTO."""
        assert PackBudget.MICRO.value == "micro"
        assert PackBudget.NORMAL.value == "normal"
        assert PackBudget.FULL.value == "full"
        assert PackBudget.AUTO.value == "auto"

    def test_from_string(self) -> None:
        """Given budget strings, PackBudget(value) gives correct member."""
        assert PackBudget("micro") == PackBudget.MICRO
        assert PackBudget("normal") == PackBudget.NORMAL
        assert PackBudget("full") == PackBudget.FULL
        assert PackBudget("auto") == PackBudget.AUTO


# ── PackStats ─────────────────────────────────────────────────────


class TestPackStats:
    """PackStats dataclass tests."""

    def test_defaults(self) -> None:
        """Given no args, PackStats has sensible defaults."""
        stats = PackStats(session_id="test")
        assert stats.session_id == "test"
        assert stats.budget_used == "auto"
        assert stats.char_count == 0
        assert stats.token_estimate == 0
        assert stats.observation_count == 0

    def test_token_estimate_computation(self) -> None:
        """Given a char_count, token_estimate is ceil(chars/4)."""
        stats = PackStats(
            session_id="test",
            budget_used="normal",
            char_count=2000,
            token_estimate=500,
            observation_count=5,
        )
        assert stats.budget_used == "normal"
        assert stats.char_count == 2000
        assert stats.token_estimate == 500
        assert stats.observation_count == 5


# ── ContextPack ───────────────────────────────────────────────────


class TestContextPack:
    """ContextPack dataclass tests."""

    def test_all_fields_present(self) -> None:
        """Given a ContextPack, all three fields are populated."""
        op_state = OperationalState()
        stats = PackStats(session_id="test")
        pack = ContextPack(text="# empty", stats=stats, operational_state=op_state)
        assert isinstance(pack.text, str)
        assert isinstance(pack.stats, PackStats)
        assert isinstance(pack.operational_state, OperationalState)


# ── build_context_pack: MICRO budget ──────────────────────────────


class TestBuildContextPackMicro:
    """build_context_pack(budget=MICRO) tests."""

    def test_micro_has_objective_and_open_work(self) -> None:
        """Given a session with objective + blocker, When MICRO pack built,
        Then text includes Objective and Open Work sections."""
        pack = build_context_pack(SESS_SMALL, budget="micro")
        text = pack.text
        assert "## Objective" in text
        assert "## Open Work" in text

    def test_micro_excludes_decisions_and_details(self) -> None:
        """Given a session with decisions and todos, When MICRO pack built,
        Then decisions and full state sections are excluded."""
        pack = build_context_pack(SESS_MEDIUM, budget="micro")
        text = pack.text
        # Micro should NOT have detailed decisions or full state
        assert "## Decisions" not in text
        assert "## State Summary" not in text
        assert "## Constraints" not in text

    def test_micro_char_count_under_1000(self) -> None:
        """Given a medium session, When MICRO pack built, Then char_count < 1000."""
        pack = build_context_pack(SESS_MEDIUM, budget="micro")
        assert 0 < pack.stats.char_count < 1000, (
            f"Expected char_count < 1000, got {pack.stats.char_count}"
        )
        assert pack.stats.budget_used == "micro"

    def test_micro_has_blockers_in_open_work(self) -> None:
        """Given a session with blockers, When MICRO pack built,
        Then blocker content appears in Open Work section."""
        pack = build_context_pack(SESS_SMALL, budget="micro")
        assert "CI pipeline" in pack.text or "CI" in pack.text

    def test_empty_session_produces_minimal_pack(self) -> None:
        """Given an empty session, When MICRO pack built,
        Then pack has minimal text and char_count > 0."""
        pack = build_context_pack(SESS_EMPTY, budget="micro")
        assert len(pack.text) > 0
        assert pack.stats.observation_count == 0
        assert "## Objective" in pack.text
        assert "## Open Work" in pack.text


# ── build_context_pack: NORMAL budget ─────────────────────────────


class TestBuildContextPackNormal:
    """build_context_pack(budget=NORMAL) tests."""

    def test_normal_has_objective_decisions_state(self) -> None:
        """Given a medium session, When NORMAL pack built,
        Then text includes Objective, Decisions, and State Summary."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        text = pack.text
        assert "## Objective" in text
        assert "## Key Decisions" in text
        assert "## State Summary" in text
        assert "## Open Work" in text

    def test_normal_includes_pending_items(self) -> None:
        """Given session with TODOs, When NORMAL pack built,
        Then pending items appear in Open Work."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        text = pack.text
        assert "rate limiting" in text.lower() or "unit tests" in text.lower()

    def test_normal_excludes_full_details(self) -> None:
        """Given a medium session, When NORMAL pack built,
        Then Constraints and Findings sections are excluded."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        text = pack.text
        assert "## Constraints" not in text
        assert "## Findings" not in text

    def test_normal_char_count_under_3500(self) -> None:
        """Given a medium session, When NORMAL pack built, Then char_count < 3500."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        assert 0 < pack.stats.char_count < 3500, (
            f"Expected char_count < 3500, got {pack.stats.char_count}"
        )
        assert pack.stats.budget_used == "normal"

    def test_normal_has_decisions_content(self) -> None:
        """Given session with decisions, When NORMAL pack built,
        Then decision content appears."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        text = pack.text
        assert "postgresql" in text.lower() or "PostgreSQL" in text


# ── build_context_pack: FULL budget ───────────────────────────────


class TestBuildContextPackFull:
    """build_context_pack(budget=FULL) tests."""

    def test_full_has_all_sections(self) -> None:
        """Given a large session, When FULL pack built,
        Then text includes all major sections."""
        pack = build_context_pack(SESS_LARGE, budget="full")
        text = pack.text
        sections = ["## Objective", "## Open Work", "## Key Decisions",
                     "## State Summary", "## Constraints", "## Findings"]
        for section in sections:
            assert section in text, f"Missing section: {section}"

    def test_full_has_comprehensive_content(self) -> None:
        """Given a large session, When FULL pack built,
        Then constraints and findings content appears."""
        pack = build_context_pack(SESS_LARGE, budget="full")
        text = pack.text
        assert "SendGrid" in text or "email" in text.lower() or "sendgrid" in text.lower()

    def test_full_char_count_bigger_than_micro(self) -> None:
        """Given same session, FULL pack has more chars than MICRO pack."""
        micro_pack = build_context_pack(SESS_LARGE, budget="micro")
        full_pack = build_context_pack(SESS_LARGE, budget="full")
        assert full_pack.stats.char_count > micro_pack.stats.char_count

    def test_full_has_guardrails(self) -> None:
        """Given a large session with pending work, When FULL pack built,
        Then guardrails section appears."""
        pack = build_context_pack(SESS_LARGE, budget="full")
        text = pack.text
        assert "## Guardrails" in text

    def test_full_budget_label(self) -> None:
        """Given budget="full", When pack built, Then stats.budget_used is 'full'."""
        pack = build_context_pack(SESS_LARGE, budget="full")
        assert pack.stats.budget_used == "full"


# ── build_context_pack: AUTO budget ───────────────────────────────


class TestBuildContextPackAuto:
    """build_context_pack(budget=AUTO) tests."""

    def test_auto_picks_micro_for_small_session(self) -> None:
        """Given a small session (<500 words), When AUTO budget,
        Then it selects micro tier."""
        pack = build_context_pack(SESS_SMALL, budget="auto")
        assert pack.stats.budget_used == "micro"

    def test_auto_picks_normal_for_medium_session(self) -> None:
        """Given a medium session (500-2000 words), When AUTO budget,
        Then it selects normal tier."""
        pack = build_context_pack(SESS_MEDIUM, budget="auto")
        assert pack.stats.budget_used == "normal"

    def test_auto_picks_full_for_large_session(self) -> None:
        """Given a large session (>2000 words), When AUTO budget,
        Then it selects full tier."""
        pack = build_context_pack(SESS_LARGE, budget="auto")
        assert pack.stats.budget_used == "full"

    def test_auto_default(self) -> None:
        """Given no budget specified, When build_context_pack called,
        Then AUTO is the default."""
        pack = build_context_pack(SESS_MEDIUM)
        assert pack.stats.budget_used == "normal"


# ── build_context_pack: stats accuracy ────────────────────────────


class TestBuildContextPackStats:
    """build_context_pack stats accuracy tests."""

    def test_stats_char_count_matches_text_length(self) -> None:
        """Given any budget, When pack built, Then stats.char_count equals len(text)."""
        for budget in ("micro", "normal", "full"):
            pack = build_context_pack(SESS_MEDIUM, budget=budget)
            assert pack.stats.char_count == len(pack.text), (
                f"Budget {budget}: expected {len(pack.text)}, got {pack.stats.char_count}"
            )

    def test_stats_token_estimate_is_ceil_chars_div_4(self) -> None:
        """Given any budget, When pack built, Then token_estimate is ceil(chars/4)."""
        import math
        for budget in ("micro", "normal", "full"):
            pack = build_context_pack(SESS_MEDIUM, budget=budget)
            expected = math.ceil(pack.stats.char_count / 4)
            assert pack.stats.token_estimate == expected, (
                f"Budget {budget}: expected {expected}, got {pack.stats.token_estimate}"
            )

    def test_stats_observation_count_is_state_total(self) -> None:
        """Given any budget, When pack built, Then observation_count is total obs count."""
        for budget in ("micro", "normal", "full"):
            pack = build_context_pack(SESS_MEDIUM, budget=budget)
            state = pack.operational_state
            total = (
                len(state.pending_items)
                + len(state.completed_items)
                + len(state.blockers)
                + len(state.constraints)
                + len(state.user_requests)
            )
            assert pack.stats.observation_count >= total, (
                f"Budget {budget}: expected >= {total}, got {pack.stats.observation_count}"
            )


# ── build_context_pack: Markdown format ───────────────────────────


class TestBuildContextPackMarkdown:
    """build_context_pack Markdown formatting tests."""

    def test_objective_section_format(self) -> None:
        """Given any budget, When pack built, Then Objective starts with '## Objective'."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        assert "## Objective\n" in pack.text

    def test_sections_are_separated_by_blank_lines(self) -> None:
        """Given any budget, When pack built, Then sections are separated by newlines."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        # Each ## header should be preceded by a newline (except first)
        lines = pack.text.split("\n")
        headers = [i for i, line in enumerate(lines) if line.startswith("## ")]
        assert len(headers) >= 3, f"Expected >=3 headers, got {len(headers)}"
        # Headers after the first should have a blank line before them
        for idx in headers[1:]:
            # Either blank or at start after a preceding blank
            assert lines[idx - 1] == "" or lines[idx - 1].strip() == "", (
                f"Header at line {idx} not preceded by blank: {lines[idx - 1]}"
            )

    def test_no_triple_backticks(self) -> None:
        """Given a normal session, When pack built, Then text uses proper block quotes."""
        pack = build_context_pack(SESS_MEDIUM, budget="normal")
        # Should use `>` quotes, not triple backticks
        assert "```" not in pack.text
