"""Tests for gaps.py — annotation gap detection and visit logging."""

from __future__ import annotations

import pytest

from token_saver_mem.code_memory.db import get_connection
from token_saver_mem.code_memory.gaps import get_annotation_gaps, log_visit


class TestGetAnnotationGaps:
    """get_annotation_gaps(db_path, limit=N) -> list[dict]"""

    def test_returns_unsummarized_nodes_first(self, populated_db):
        """Given nodes without summaries, they appear ranked first."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        assert len(gaps) > 0
        # First item should be a node without summary (unsynced has summary=NULL)
        first = gaps[0]
        assert first["has_summary"] is False

    def test_returns_stale_nodes(self, populated_db):
        """Given nodes with stale summaries, they appear in results."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        ids = [g["node_id"] for g in gaps]
        assert "function:stale_example.py:old_func" in ids

    def test_respects_limit(self, populated_db):
        """Given a populated DB, limit parameter caps result count."""
        gaps = get_annotation_gaps(populated_db, limit=1)
        assert len(gaps) <= 1

    def test_returns_empty_for_fresh_db(self, temp_db):
        """Given an empty database, returns empty list."""
        assert get_annotation_gaps(temp_db) == []

    def test_ranks_nulls_before_stale(self, populated_db):
        """Given both null-summary and stale-summary nodes, nulls rank first."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        # Find positions
        positions = {g["node_id"]: i for i, g in enumerate(gaps)}
        unsynced_pos = positions.get("function:stale_example.py:unsynced")
        old_func_pos = positions.get("function:stale_example.py:old_func")
        assert unsynced_pos is not None, "null-summary node should appear"
        assert old_func_pos is not None, "stale node should appear"
        assert unsynced_pos < old_func_pos, "null-summary ranks before stale"

    def test_excludes_deleted_nodes(self, populated_db):
        """Given a deleted node, it is NOT returned as a gap."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        ids = [g["node_id"] for g in gaps]
        assert "function:old_file.py:removed_func" not in ids

    def test_excludes_fresh_nodes(self, populated_db):
        """Given nodes where summary_hash == content_hash, they are NOT in gaps."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        ids = [g["node_id"] for g in gaps]
        assert "function:utils.py:add" not in ids
        assert "function:utils.py:multiply" not in ids
        assert "class:models.py:User" not in ids

    def test_result_keys_match_spec(self, populated_db):
        """Given rows, each dict has required keys."""
        gaps = get_annotation_gaps(populated_db, limit=10)
        for g in gaps:
            assert "node_id" in g
            assert "name" in g
            assert "path" in g
            assert "kind" in g
            assert "stale_reason" in g
            assert "has_summary" in g


class TestLogVisit:
    """log_visit(db_path, node_id, session_id) -> None"""

    def test_stores_visit_record(self, populated_db):
        """Given a valid node and session, a visit row is inserted."""
        log_visit(populated_db, "function:utils.py:add", "ses_test_001")

        conn = get_connection(populated_db)
        try:
            row = conn.execute(
                "SELECT node_id, session_id, visited_at FROM node_visits "
                "WHERE node_id = ? AND session_id = ?",
                ("function:utils.py:add", "ses_test_001"),
            ).fetchone()
            assert row is not None
            assert row["node_id"] == "function:utils.py:add"
            assert row["session_id"] == "ses_test_001"
            assert row["visited_at"] > 0
        finally:
            conn.close()

    def test_upserts_on_duplicate(self, populated_db):
        """Given a second log_visit for the same node+session, it's an upsert not error."""
        log_visit(populated_db, "function:utils.py:add", "ses_test_002")
        log_visit(populated_db, "function:utils.py:add", "ses_test_002")  # same call

        conn = get_connection(populated_db)
        try:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM node_visits "
                "WHERE node_id = ? AND session_id = ?",
                ("function:utils.py:add", "ses_test_002"),
            ).fetchone()["cnt"]
            assert count == 1  # upsert, not duplicate
        finally:
            conn.close()
