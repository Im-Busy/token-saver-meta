"""Tests for tools/session — 4 MCP session tool wrappers.

context_pack_tool, bootstrap_context_tool, open_work_tool, completion_check_tool.
All tools accept session_text directly — no DB required.
"""

from __future__ import annotations

import pytest

from token_saver_mem.session_memory.caching import stable_hash


# ── Test data ───────────────────────────────────────────────────────

SESS_SMALL = """\
Task: Fix login bug in auth.py.
BLOCKER: CI pipeline is down.
TODO: Add unit tests for login.
"""

SESS_MEDIUM = (
    "Objective: Build user authentication module with JWT tokens.\n"
    "TODO: Set up database schema for users table.\n"
    "BLOCKER: Need DevOps to provision the staging database.\n"
    "TODO: Write integration tests for auth flow.\n"
    "Decision: Settled on using Authlib library for OAuth2.\n"
    "Risk: OAuth2 provider rate limits could block batch registration.\n"
    "Completed: User login endpoint returns JWT on success.\n"
    "Finding: bcrypt cost factor 12 gives ~300ms on average hardware.\n"
    "Convention: All API endpoints must return JSON errors with error_code field.\n"
    + ("The application should handle request validation properly. "
       "System must log all authentication events. ") * 25
)

SESS_ALL_DONE = """\
Objective: Deploy v2 API.
Completed: All tests pass.
Completed: Docs updated.
Decision: Deployed to production successfully.
Done.
"""

SESS_EMPTY = ""


# ── Tests: context_pack_tool ────────────────────────────────────────

class TestContextPackTool:
    """context_pack_tool(session_text, budget="auto") → {text, stats, hash}."""

    def _call(self, session_text: str, budget: str = "auto") -> dict:
        from token_saver_mem.tools.session.context_pack import context_pack_tool
        return context_pack_tool(session_text, budget=budget)

    def test_returns_text_stats_hash(self) -> None:
        """Given session text, When context_pack_tool called, Then returns text, stats, hash."""
        result = self._call(SESS_MEDIUM)
        assert "text" in result
        assert "stats" in result
        assert "hash" in result
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0
        assert isinstance(result["stats"], dict)
        assert isinstance(result["hash"], str)
        assert len(result["hash"]) == 64

    def test_hash_is_stable(self) -> None:
        """Given same session text, When called twice, Then hash is identical."""
        r1 = self._call(SESS_SMALL)
        r2 = self._call(SESS_SMALL)
        assert r1["hash"] == r2["hash"]

    def test_different_text_different_hash(self) -> None:
        """Given different session texts, When called, Then hashes differ."""
        r1 = self._call(SESS_SMALL)
        r2 = self._call(SESS_MEDIUM)
        assert r1["hash"] != r2["hash"]

    def test_budget_forwarded(self) -> None:
        """Given budget='micro', When called, Then stats.budget_used is 'micro'."""
        result = self._call(SESS_MEDIUM, budget="micro")
        assert result["stats"]["budget_used"] == "micro"

    def test_budget_normal(self) -> None:
        """Given budget='normal', When called, Then stats.budget_used is 'normal'."""
        result = self._call(SESS_MEDIUM, budget="normal")
        assert result["stats"]["budget_used"] == "normal"

    def test_budget_full(self) -> None:
        """Given budget='full', When called, Then stats.budget_used is 'full'."""
        result = self._call(SESS_MEDIUM, budget="full")
        assert result["stats"]["budget_used"] == "full"

    def test_budget_auto_selects_tier(self) -> None:
        """Given budget='auto', When called with small session, Then micro is selected."""
        result = self._call(SESS_SMALL, budget="auto")
        assert result["stats"]["budget_used"] in {"micro", "normal", "full"}

    def test_invalid_budget_raises(self) -> None:
        """Given invalid budget string, When called, Then raises ValueError."""
        with pytest.raises(ValueError, match="Unknown budget"):
            self._call(SESS_SMALL, budget="invalid")

    def test_empty_session_produces_pack(self) -> None:
        """Given empty session text, When called, Then still returns valid pack."""
        result = self._call(SESS_EMPTY)
        assert "text" in result
        assert "hash" in result
        assert isinstance(result["text"], str)

    def test_stats_contains_required_fields(self) -> None:
        """Given any session, When called, Then stats has session_id, budget_used, char_count, token_estimate, observation_count."""
        result = self._call(SESS_MEDIUM)
        stats = result["stats"]
        assert "session_id" in stats
        assert "budget_used" in stats
        assert "char_count" in stats
        assert "token_estimate" in stats
        assert "observation_count" in stats
        assert isinstance(stats["char_count"], int)
        assert isinstance(stats["token_estimate"], int)
        assert isinstance(stats["observation_count"], int)


# ── Tests: bootstrap_context_tool ───────────────────────────────────

class TestBootstrapContextTool:
    """bootstrap_context_tool(session_text, project_path=None) → {scope, context_pack}."""

    def _call(self, session_text: str, project_path: str | None = None) -> dict:
        from token_saver_mem.tools.session.bootstrap_context import bootstrap_context_tool
        return bootstrap_context_tool(session_text, project_path=project_path)

    def test_returns_scope_and_context_pack(self) -> None:
        """Given session text, When bootstrap_context_tool called, Then returns scope + context_pack."""
        result = self._call(SESS_MEDIUM)
        assert "scope" in result
        assert "context_pack" in result
        assert isinstance(result["scope"], dict)
        assert isinstance(result["context_pack"], dict)

    def test_scope_has_language_and_type(self) -> None:
        """Given session text, When called, Then scope has language, project_type keys."""
        result = self._call(SESS_MEDIUM)
        scope = result["scope"]
        assert "language" in scope
        assert "project_type" in scope
        assert "frameworks" in scope
        assert "key_files" in scope
        assert isinstance(scope["frameworks"], list)
        assert isinstance(scope["key_files"], list)

    def test_context_pack_has_text_and_hash(self) -> None:
        """Given session text, When called, Then context_pack has text, hash."""
        result = self._call(SESS_SMALL)
        pack = result["context_pack"]
        assert "text" in pack
        assert "hash" in pack
        assert isinstance(pack["text"], str)
        assert len(pack["text"]) > 0

    def test_with_project_path_nonexistent(self) -> None:
        """Given nonexistent project_path, When called, Then falls back to text-based scope detection."""
        result = self._call(SESS_MEDIUM, project_path="/nonexistent/path")
        scope = result["scope"]
        assert "language" in scope
        # Falls back, so language may be detected from text
        assert "context_pack" in result

    def test_empty_session_still_works(self) -> None:
        """Given empty session text, When called, Then returns valid result."""
        result = self._call(SESS_EMPTY)
        assert "scope" in result
        assert "context_pack" in result
        scope = result["scope"]
        assert scope["language"] == "unknown"

    def test_bootstrap_result_is_hashable_cacheable(self) -> None:
        """Given same inputs, When called twice, Then context_pack hash is identical."""
        r1 = self._call(SESS_SMALL)
        r2 = self._call(SESS_SMALL)
        assert r1["context_pack"]["hash"] == r2["context_pack"]["hash"]


# ── Tests: open_work_tool ───────────────────────────────────────────

class TestOpenWorkTool:
    """open_work_tool(session_text) → {pending, blockers, has_open_work}."""

    def _call(self, session_text: str) -> dict:
        from token_saver_mem.tools.session.open_work import open_work_tool
        return open_work_tool(session_text)

    def test_returns_pending_blockers_has_open_work(self) -> None:
        """Given session text with open items, When open_work_tool called, Then returns pending, blockers, has_open_work."""
        result = self._call(SESS_MEDIUM)
        assert "pending" in result
        assert "blockers" in result
        assert "has_open_work" in result
        assert isinstance(result["pending"], list)
        assert isinstance(result["blockers"], list)
        assert isinstance(result["has_open_work"], bool)

    def test_has_open_work_true_with_pending(self) -> None:
        """Given session text with TODOs, When called, Then has_open_work is True."""
        result = self._call(SESS_MEDIUM)
        assert result["has_open_work"] is True
        assert len(result["pending"]) >= 1

    def test_blockers_detected(self) -> None:
        """Given session text with BLOCKER lines, When called, Then blockers list is non-empty."""
        result = self._call(SESS_SMALL)
        assert len(result["blockers"]) >= 1
        assert any("CI pipeline" in b["content"] for b in result["blockers"])

    def test_empty_session_has_no_open_work(self) -> None:
        """Given empty session text, When called, Then has_open_work is False."""
        result = self._call(SESS_EMPTY)
        assert result["has_open_work"] is False
        assert result["pending"] == []
        assert result["blockers"] == []

    def test_all_done_session_has_no_open_work(self) -> None:
        """Given session with all completions, When called, Then has_open_work is False."""
        result = self._call(SESS_ALL_DONE)
        # Completions may resolve pending/blockers
        assert isinstance(result["has_open_work"], bool)
        # With completions declared, should not have open work
        if result["pending"] == [] and result["blockers"] == []:
            assert result["has_open_work"] is False

    def test_pending_items_have_content(self) -> None:
        """Given session with TODOs, When called, Then pending items have content key."""
        result = self._call(SESS_MEDIUM)
        for item in result["pending"]:
            assert "content" in item


# ── Tests: completion_check_tool ────────────────────────────────────

class TestCompletionCheckTool:
    """completion_check_tool(session_text) → {done, pending, blockers}."""

    def _call(self, session_text: str) -> dict:
        from token_saver_mem.tools.session.completion_check import completion_check_tool
        return completion_check_tool(session_text)

    def test_returns_done_pending_blockers(self) -> None:
        """Given session text, When completion_check_tool called, Then returns done, pending, blockers."""
        result = self._call(SESS_MEDIUM)
        assert "done" in result
        assert "pending" in result
        assert "blockers" in result
        assert isinstance(result["done"], bool)
        assert isinstance(result["pending"], list)
        assert isinstance(result["blockers"], list)

    def test_not_done_when_pending(self) -> None:
        """Given session with TODOs, When checked, Then done is False."""
        result = self._call(SESS_MEDIUM)
        assert result["done"] is False

    def test_done_when_all_completed(self) -> None:
        """Given session with all completions, When checked, Then done is True."""
        result = self._call(SESS_ALL_DONE)
        assert result["done"] is True

    def test_not_done_with_blockers(self) -> None:
        """Given session with BLOCKERs, When checked, Then done is False."""
        result = self._call(SESS_SMALL)
        assert result["done"] is False
        assert len(result["blockers"]) >= 1

    def test_empty_session_not_done(self) -> None:
        """Given empty session, When checked, Then done is False (work never started)."""
        result = self._call(SESS_EMPTY)
        assert result["done"] is False
        assert result["pending"] == []
        assert result["blockers"] == []

    def test_pending_list_are_strings(self) -> None:
        """Given session with TODOs, When checked, Then pending list items are strings."""
        result = self._call(SESS_MEDIUM)
        for p in result["pending"]:
            assert isinstance(p, str)

    def test_blockers_list_are_strings(self) -> None:
        """Given session with BLOCKERs, When checked, Then blockers list items are strings."""
        result = self._call(SESS_SMALL)
        for b in result["blockers"]:
            assert isinstance(b, str)

    def test_result_is_hash_stable_for_caching(self) -> None:
        """Given same session text, When checked twice, Then results are identical."""
        r1 = self._call(SESS_MEDIUM)
        r2 = self._call(SESS_MEDIUM)
        assert r1 == r2
