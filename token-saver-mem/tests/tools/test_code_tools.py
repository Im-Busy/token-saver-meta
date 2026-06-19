"""Tests for MCP code tools: search_symbols, get_context, store_understanding, get_delta."""

from __future__ import annotations

import time

import pytest

from token_saver_mem.code_memory.db import get_connection


# ============================================================
# TestSearchSymbols
# ============================================================


class TestSearchSymbols:
    """search_symbols(db_path, query, limit=10) -> list[dict]"""

    @pytest.fixture(autouse=True)
    def _import(self):
        from token_saver_mem.tools.code.search_symbols import search_symbols

        self.search = search_symbols

    def test_finds_matching_node_by_name(self, populated_db):
        """Given a DB with 'add' function, query='add' returns it."""
        results = self.search(populated_db, "add")
        ids = [r["id"] for r in results]
        assert "function:utils.py:add" in ids

    def test_finds_matching_node_by_summary(self, populated_db):
        """Given a DB with summary 'Multiply two numbers', query='multiply' returns it."""
        results = self.search(populated_db, "multiply")
        ids = [r["id"] for r in results]
        assert any("multiply" in r["name"] for r in results)

    def test_finds_matching_node_by_kind(self, populated_db):
        """Given a DB with 'class' kind, query='class' returns class nodes."""
        results = self.search(populated_db, "class")
        assert any(r["kind"] == "class" for r in results)

    def test_empty_query_returns_empty(self, populated_db):
        """Given empty query string, returns empty list."""
        results = self.search(populated_db, "")
        assert results == []

    def test_respects_limit(self, populated_db):
        """Given limit=2, returns at most 2 results (even if more match)."""
        results = self.search(populated_db, "function", limit=2)
        assert len(results) <= 2

    def test_returns_snippets(self, populated_db):
        """Given matching results, each dict includes 'snippet' key."""
        results = self.search(populated_db, "add")
        assert len(results) > 0
        for r in results:
            assert "snippet" in r

    def test_does_not_return_deleted_nodes(self, populated_db):
        """Given a soft-deleted node, it does NOT appear in search results."""
        results = self.search(populated_db, "removed_func")
        ids = [r["id"] for r in results]
        assert "function:old_file.py:removed_func" not in ids

    def test_returns_empty_for_no_match(self, populated_db):
        """Given query matching nothing, returns empty list."""
        results = self.search(populated_db, "zzzzz_nonexistent_zzzzz")
        assert results == []

    def test_empty_database(self, temp_db):
        """Given an empty DB, search returns empty list (no crash)."""
        results = self.search(temp_db, "anything")
        assert results == []


# ============================================================
# TestGetContext
# ============================================================


class TestGetContext:
    """get_context(db_path, node_id) -> dict"""

    @pytest.fixture(autouse=True)
    def _import(self):
        from token_saver_mem.tools.code.get_context import get_context

        self.get_ctx = get_context

    def test_returns_full_context_for_fresh_node(self, populated_db):
        """Given a node with matching summary_hash==content_hash, staleness='fresh'."""
        ctx = self.get_ctx(populated_db, "function:utils.py:add")
        assert ctx["name"] == "add"
        assert ctx["path"] == "utils.py"
        assert ctx["kind"] == "function"
        assert ctx["staleness_status"] == "fresh"
        assert ctx["summary_text"] == "Add two numbers."

    def test_returns_stale_for_divergent_hash(self, populated_db):
        """Given a node with summary_hash != content_hash, staleness='stale'."""
        ctx = self.get_ctx(populated_db, "function:stale_example.py:old_func")
        assert ctx["staleness_status"] == "stale"

    def test_returns_stale_for_null_summary(self, populated_db):
        """Given a node with summary=None, staleness='stale'."""
        ctx = self.get_ctx(populated_db, "function:stale_example.py:unsynced")
        assert ctx["staleness_status"] == "stale"
        assert ctx["summary_text"] is None

    def test_missing_node_returns_error(self, populated_db):
        """Given a nonexistent node_id, raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            self.get_ctx(populated_db, "function:nope.py:none")

    def test_includes_node_id(self, populated_db):
        """Given context dict, includes 'id' field."""
        ctx = self.get_ctx(populated_db, "function:utils.py:add")
        assert ctx["id"] == "function:utils.py:add"

    def test_includes_line_info(self, populated_db):
        """Given a node with line numbers, context includes start_line/end_line."""
        ctx = self.get_ctx(populated_db, "function:utils.py:add")
        assert ctx["start_line"] == 4
        assert ctx["end_line"] == 7


# ============================================================
# TestStoreUnderstanding
# ============================================================


class TestStoreUnderstanding:
    """store_understanding(db_path, node_id, summary_text) -> bool"""

    @pytest.fixture(autouse=True)
    def _import(self):
        from token_saver_mem.tools.code.store_understanding import store_understanding

        self.store = store_understanding

    def test_updates_summary_for_existing_node(self, populated_db):
        """Given a stale node, store_understanding updates summary and marks fresh."""
        target = "function:stale_example.py:old_func"
        new_summary = "Updated: does something completely different now."

        result = self.store(populated_db, target, new_summary)
        assert result is True

        # Verify in database: summary updated, summary_hash = content_hash (mark_fresh convention)
        conn = get_connection(populated_db)
        try:
            row = conn.execute(
                "SELECT summary, summary_hash, content_hash FROM code_nodes WHERE id=?",
                (target,),
            ).fetchone()
            assert row["summary"] == new_summary
            assert row["summary_hash"] == row["content_hash"], (
                "summary_hash should equal content_hash (mark_fresh convention)"
            )
        finally:
            conn.close()

    def test_returns_false_for_missing_node(self, populated_db):
        """Given nonexistent node_id, returns False."""
        result = self.store(populated_db, "function:ghost.py:phantom", "some summary")
        assert result is False

    def test_after_store_get_context_returns_fresh(self, populated_db):
        """Given store_understanding, subsequent get_context shows status='fresh'."""
        from token_saver_mem.tools.code.get_context import get_context

        target = "function:stale_example.py:old_func"
        self.store(populated_db, target, "Fresh summary now.")
        ctx = get_context(populated_db, target)
        assert ctx["staleness_status"] == "fresh"
        assert ctx["summary_text"] == "Fresh summary now."

    def test_clears_staleness_for_unsynced_node(self, populated_db):
        """Given a node with null summary_hash, store makes it fresh."""
        target = "function:stale_example.py:unsynced"
        result = self.store(populated_db, target, "First annotation.")
        assert result is True

        from token_saver_mem.tools.code.get_context import get_context

        ctx = get_context(populated_db, target)
        assert ctx["staleness_status"] == "fresh"


# ============================================================
# TestGetDelta
# ============================================================


class TestGetDelta:
    """get_delta(db_path, since_ts) -> dict"""

    @pytest.fixture(autouse=True)
    def _import(self):
        from token_saver_mem.tools.code.get_delta import get_delta

        self.get_delta = get_delta

    def test_returns_delta_dict(self, populated_db):
        """Given a DB, returns dict with total, changed, deleted."""
        payload = self.get_delta(populated_db, 0)
        assert "total" in payload
        assert "changed" in payload
        assert "deleted" in payload
        assert payload["total"] == payload["changed"] + payload["deleted"]

    def test_delegates_to_core_delta_module(self, populated_db):
        """Given a populated DB, get_delta delegates to code_memory.delta.get_delta_payload.

        Verifies by checking that results are identical to calling get_delta_payload directly.
        """
        from token_saver_mem.code_memory.delta import get_delta_payload

        now = time.time()
        since = now - 3600
        tool_result = self.get_delta(populated_db, since)
        core_result = get_delta_payload(populated_db, since)
        assert tool_result == core_result

    def test_future_timestamp_returns_empty(self, populated_db):
        """Given a timestamp in the future, returns zero counts."""
        payload = self.get_delta(populated_db, time.time() + 10000)
        assert payload["changed"] == 0
        assert payload["deleted"] == 0
        assert payload["total"] == 0

    def test_empty_database_returns_zeros(self, temp_db):
        """Given an empty DB, returns zero counts."""
        payload = self.get_delta(temp_db, 0)
        assert payload["changed"] == 0
        assert payload["deleted"] == 0
        assert payload["total"] == 0
