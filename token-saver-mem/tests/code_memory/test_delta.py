"""Tests for delta.py — SQL-based delta payload computation."""

from __future__ import annotations

import time

import pytest

from token_saver_mem.code_memory.delta import get_delta_payload


class TestGetDeltaPayload:
    """get_delta_payload(db_path, since_ts) -> dict"""

    def test_returns_correct_counts(self, populated_db):
        """Given a DB with nodes at various updated_at times."""
        now = time.time()
        since = now - 1800  # 30 min ago — should catch the stale/unsummarized nodes
        payload = get_delta_payload(populated_db, since)

        assert "changed" in payload
        assert "deleted" in payload
        assert "total" in payload
        assert payload["changed"] >= 0
        assert payload["deleted"] >= 0
        assert payload["total"] == payload["changed"] + payload["deleted"]

    def test_returns_empty_delta_for_recent_ts(self, populated_db):
        """Given a timestamp after all updates, nothing changed."""
        now = time.time()
        since = now + 3600  # 1 hour in the future
        payload = get_delta_payload(populated_db, since)
        assert payload["changed"] == 0
        assert payload["deleted"] == 0
        assert payload["total"] == 0

    def test_returns_deleted_nodes(self, populated_db):
        """Given a DB with soft-deleted nodes."""
        # The deleted node is at now - 3600
        now = time.time()
        since = now - 7200  # 2 hours ago — should include the deleted node
        payload = get_delta_payload(populated_db, since)
        assert payload["deleted"] >= 1

    def test_all_nodes_in_far_past(self, populated_db):
        """Given a very old timestamp, all nodes are returned."""
        payload = get_delta_payload(populated_db, 0)
        # Should have at least the active nodes (5 nodes minus 1 deleted)
        assert payload["changed"] >= 4
        assert payload["deleted"] >= 1

    def test_includes_change_details(self, populated_db):
        """Given changed nodes, payload includes node details."""
        now = time.time()
        since = now - 3600
        payload = get_delta_payload(populated_db, since, include_details=True)
        if payload["changed"] > 0:
            assert "nodes" in payload
            assert "deleted_nodes" in payload
            # Check structure of a changed node
            if payload["nodes"]:
                node = payload["nodes"][0]
                for key in ("id", "name", "kind", "path", "change_type"):
                    assert key in node

    def test_no_details_by_default(self, populated_db):
        """Given default call, details are not included to save tokens."""
        payload = get_delta_payload(populated_db, 0)
        assert "nodes" not in payload  # default: summary mode only

    def test_empty_database(self, temp_db):
        """Given an empty database, returns zero counts."""
        payload = get_delta_payload(temp_db, 0)
        assert payload["changed"] == 0
        assert payload["deleted"] == 0
        assert payload["total"] == 0
