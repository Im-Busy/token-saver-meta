"""Test NodeRepo, ObsRepo, and SessionRepo CRUD operations."""

import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

from token_saver_mem.store.db import get_db, init_db
from token_saver_mem.store.repository.node_repo import NodeRepo
from token_saver_mem.store.repository.obs_repo import ObsRepo
from token_saver_mem.store.repository.session_repo import SessionRepo
from token_saver_mem.store.repository import RepoSet


@pytest.fixture
def db_path() -> str:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(b"")
    return f.name


@pytest.fixture
def db(db_path: str) -> sqlite3.Connection:
    conn = get_db(db_path)
    init_db(conn)
    yield conn
    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def node_repo(db: sqlite3.Connection) -> NodeRepo:
    return NodeRepo(db)


@pytest.fixture
def obs_repo(db: sqlite3.Connection) -> ObsRepo:
    return ObsRepo(db)


@pytest.fixture
def session_repo(db: sqlite3.Connection) -> SessionRepo:
    return SessionRepo(db)


@pytest.fixture
def repo_set(db: sqlite3.Connection) -> RepoSet:
    return RepoSet(
        node=NodeRepo(db),
        obs=ObsRepo(db),
        session=SessionRepo(db),
    )


# ═══════════════════════════════════════════════════════════════════
# NodeRepo tests
# ═══════════════════════════════════════════════════════════════════

class TestNodeRepoInsert:
    """Given: empty nodes table. When: upsert() a node. Then: node is stored."""

    def test_upsert_returns_dict(self, node_repo: NodeRepo) -> None:
        """Then: upsert returns a dict with the node data."""
        result = node_repo.upsert(
            path="/test/file.py",
            name="file",
            kind="module",
        )
        assert isinstance(result, dict)
        assert result["path"] == "/test/file.py"
        assert result["name"] == "file"
        assert result["kind"] == "module"
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result

    def test_upsert_sets_id(self, node_repo: NodeRepo) -> None:
        """Then: upsert assigns an auto-increment id."""
        n1 = node_repo.upsert(path="/a.py", name="a", kind="module")
        n2 = node_repo.upsert(path="/b.py", name="b", kind="module")
        assert n1["id"] == 1
        assert n2["id"] == 2

    def test_upsert_with_full_fields(self, node_repo: NodeRepo) -> None:
        """Then: upsert stores all provided fields."""
        result = node_repo.upsert(
            path="/full.py",
            name="full",
            kind="class",
            content_hash="abc123",
            summary_hash="def456",
            summary="This is a summary.",
            metadata='{"tags": ["util"]}',
        )
        assert result["content_hash"] == "abc123"
        assert result["summary_hash"] == "def456"
        assert result["summary"] == "This is a summary."
        assert result["metadata"] == '{"tags": ["util"]}'


class TestNodeRepoUpdate:
    """Given: an existing node. When: upsert() with same path. Then: update, not insert."""

    def test_upsert_updates_existing_by_path(self, node_repo: NodeRepo) -> None:
        """Then: upsert on existing path updates the row."""
        n1 = node_repo.upsert(path="/x.py", name="x", kind="module", summary="old")
        n2 = node_repo.upsert(path="/x.py", name="x_renamed", kind="function", summary="new")
        assert n1["id"] == n2["id"], "Same row should be updated, not inserted"
        assert n2["name"] == "x_renamed"
        assert n2["kind"] == "function"
        assert n2["summary"] == "new"

    def test_updated_at_changes_on_content_hash_change(self, node_repo: NodeRepo) -> None:
        """Then: updated_at bumps only when content_hash differs."""
        n1 = node_repo.upsert(path="/y.py", name="y", kind="module", content_hash="hash1")
        n2 = node_repo.upsert(path="/y.py", name="y", kind="module", content_hash="hash1")
        assert n2["updated_at"] == n1["updated_at"], (
            "updated_at should NOT change when content_hash is same"
        )

        n3 = node_repo.upsert(path="/y.py", name="y", kind="module", content_hash="hash2")
        assert n3["updated_at"] > n1["updated_at"], (
            "updated_at should bump when content_hash differs"
        )


class TestNodeRepoGet:
    """Given: nodes in the database. When: get() or get_by_path(). Then: correct node returned."""

    def test_get_by_id(self, node_repo: NodeRepo) -> None:
        """Then: get(id) returns the node."""
        created = node_repo.upsert(path="/get.py", name="get_test", kind="module")
        fetched = node_repo.get(created["id"])
        assert fetched is not None
        assert fetched["path"] == "/get.py"

    def test_get_by_id_missing(self, node_repo: NodeRepo) -> None:
        """Then: get(id) returns None for non-existent id."""
        assert node_repo.get(999) is None

    def test_get_by_path(self, node_repo: NodeRepo) -> None:
        """Then: get_by_path(path) returns the node."""
        created = node_repo.upsert(path="/bypath.py", name="bp", kind="module")
        fetched = node_repo.get_by_path("/bypath.py")
        assert fetched is not None
        assert fetched["id"] == created["id"]

    def test_get_by_path_missing(self, node_repo: NodeRepo) -> None:
        """Then: get_by_path(path) returns None for non-existent path."""
        assert node_repo.get_by_path("/nonexistent.py") is None


class TestNodeRepoBulkUpsert:
    """Given: a list of node dicts. When: bulk_upsert(). Then: all stored."""

    def test_bulk_upsert_inserts_all(self, node_repo: NodeRepo) -> None:
        """Then: bulk_upsert inserts all new nodes."""
        nodes = [
            {"path": "/a/b1.py", "name": "b1", "kind": "module"},
            {"path": "/a/b2.py", "name": "b2", "kind": "class"},
            {"path": "/a/b3.py", "name": "b3", "kind": "function"},
        ]
        results = node_repo.bulk_upsert(nodes)
        assert len(results) == 3
        paths = {r["path"] for r in results}
        assert paths == {"/a/b1.py", "/a/b2.py", "/a/b3.py"}

    def test_bulk_upsert_mixed_insert_update(self, node_repo: NodeRepo) -> None:
        """Then: bulk_upsert handles mix of new and existing nodes."""
        # Pre-insert one
        node_repo.upsert(path="/mix/existing.py", name="existing", kind="module")

        nodes = [
            {"path": "/mix/existing.py", "name": "existing_updated", "kind": "function"},
            {"path": "/mix/new.py", "name": "new", "kind": "module"},
        ]
        results = node_repo.bulk_upsert(nodes)
        assert len(results) == 2
        existing = node_repo.get_by_path("/mix/existing.py")
        # ponytail: name is key to tell update vs insert
        assert existing["name"] == "existing_updated"


class TestNodeRepoSearchFTS:
    """Given: nodes with summaries. When: search_fts(query). Then: matching nodes returned."""

    def test_search_finds_by_name(self, node_repo: NodeRepo) -> None:
        node_repo.upsert(path="/s/a.py", name="unique_name_42", kind="module")
        results = node_repo.search_fts("unique_name_42")
        assert len(results) == 1
        assert results[0]["name"] == "unique_name_42"

    def test_search_finds_by_kind(self, node_repo: NodeRepo) -> None:
        node_repo.upsert(path="/s/a.py", name="a", kind="class")
        results = node_repo.search_fts("class")
        assert any(r["path"] == "/s/a.py" for r in results)

    def test_search_finds_by_summary(self, node_repo: NodeRepo) -> None:
        node_repo.upsert(
            path="/s/auth.py", name="auth",
            kind="module", summary="handles token authentication"
        )
        results = node_repo.search_fts("token")
        assert len(results) == 1
        assert results[0]["path"] == "/s/auth.py"

    def test_search_no_results(self, node_repo: NodeRepo) -> None:
        results = node_repo.search_fts("zzz_nonexistent_zzz")
        assert results == []

    def test_search_respects_limit(self, node_repo: NodeRepo) -> None:
        for i in range(5):
            node_repo.upsert(
                path=f"/s/limit{i}.py", name=f"limit_{i}",
                kind="module", summary=f"test token {i}"
            )
        results = node_repo.search_fts("token", limit=3)
        assert len(results) == 3


class TestNodeRepoMarkStale:
    """Given: a node. When: mark_stale(node_id). Then: updated_at is bumped."""

    def test_mark_stale_bumps_updated_at(self, node_repo: NodeRepo) -> None:
        n = node_repo.upsert(path="/stale.py", name="stale", kind="module")
        original_ts = n["updated_at"]
        time.sleep(0.01)  # Ensure time difference
        node_repo.mark_stale(n["id"])
        fetched = node_repo.get(n["id"])
        assert fetched["updated_at"] > original_ts


# ═══════════════════════════════════════════════════════════════════
# ObsRepo tests
# ═══════════════════════════════════════════════════════════════════

class TestObsRepoInsert:
    """Given: empty observations table. When: add(). Then: observation is stored."""

    def test_add_returns_dict(self, obs_repo: ObsRepo) -> None:
        result = obs_repo.add(
            entity_name="UserService",
            obs_type="fact",
            content="UserService handles authentication",
            confidence=0.9,
        )
        assert isinstance(result, dict)
        assert result["entity_name"] == "UserService"
        assert result["obs_type"] == "fact"
        assert result["content"] == "UserService handles authentication"
        assert result["confidence"] == 0.9
        assert "id" in result
        assert "created_at" in result

    def test_add_with_session(self, obs_repo: ObsRepo, session_repo: SessionRepo) -> None:
        """Then: observation can be linked to a session."""
        session_repo.create("sid1")
        result = obs_repo.add(
            entity_name="AuthModule",
            obs_type="decision",
            content="Use JWT tokens",
            confidence=1.0,
            session_id="sid1",
        )
        assert result["session_id"] == "sid1"


class TestObsRepoQuery:
    """Given: observations in the database. When: query. Then: correct results."""

    def test_get_by_entity(self, obs_repo: ObsRepo) -> None:
        obs_repo.add(entity_name="E1", obs_type="fact", content="c1", confidence=0.5)
        obs_repo.add(entity_name="E1", obs_type="fact", content="c2", confidence=0.6)
        obs_repo.add(entity_name="E2", obs_type="fact", content="c3", confidence=0.7)

        e1_results = obs_repo.get_by_entity("E1")
        assert len(e1_results) == 2
        assert all(r["entity_name"] == "E1" for r in e1_results)

    def test_get_by_entity_missing(self, obs_repo: ObsRepo) -> None:
        assert obs_repo.get_by_entity("does_not_exist") == []

    def test_get_by_session(self, obs_repo: ObsRepo, session_repo: SessionRepo) -> None:
        session_repo.create("sA")
        session_repo.create("sB")

        obs_repo.add(entity_name="E", obs_type="fact", content="in_sA", confidence=0.5, session_id="sA")
        obs_repo.add(entity_name="E", obs_type="fact", content="in_sB", confidence=0.6, session_id="sB")
        obs_repo.add(entity_name="E", obs_type="fact", content="no_session", confidence=0.7)

        sA_results = obs_repo.get_by_session("sA")
        assert len(sA_results) == 1
        assert sA_results[0]["content"] == "in_sA"

    def test_get_by_session_missing(self, obs_repo: ObsRepo) -> None:
        assert obs_repo.get_by_session("nonexistent_session") == []


# ═══════════════════════════════════════════════════════════════════
# SessionRepo tests
# ═══════════════════════════════════════════════════════════════════

class TestSessionRepoCreate:
    """Given: empty sessions table. When: create(sid). Then: session is stored."""

    def test_create_returns_dict(self, session_repo: SessionRepo) -> None:
        result = session_repo.create("my_session")
        assert isinstance(result, dict)
        assert result["id"] == "my_session"
        assert result["started_at"] is not None
        assert result["ended_at"] is None

    def test_create_with_metadata(self, session_repo: SessionRepo) -> None:
        result = session_repo.create("meta_ses", model="gpt-4", agent="builder")
        assert result["model"] == "gpt-4"
        assert result["agent"] == "builder"

    def test_create_duplicate_session_fails(self, session_repo: SessionRepo) -> None:
        session_repo.create("dup")
        with pytest.raises(sqlite3.IntegrityError):
            session_repo.create("dup")


class TestSessionRepoClose:
    """Given: an active session. When: close(sid). Then: ended_at is set."""

    def test_close_sets_ended_at(self, session_repo: SessionRepo) -> None:
        session_repo.create("close_test")
        result = session_repo.close("close_test")
        assert result["ended_at"] is not None

    def test_close_missing_returns_none(self, session_repo: SessionRepo) -> None:
        result = session_repo.close("no_such_session")
        assert result is None


class TestSessionRepoGetDelta:
    """Given: observations across time. When: get_delta(sid, since_ts). Then: correct delta."""

    def test_get_delta_empty_session(self, session_repo: SessionRepo) -> None:
        session_repo.create("empty_delta")
        delta = session_repo.get_delta("empty_delta", "2020-01-01")
        assert delta["changed"] == 0
        assert delta["deleted"] == 0
        assert delta["total"] == 0

    def test_get_delta_all_within_window(
        self, session_repo: SessionRepo, obs_repo: ObsRepo
    ) -> None:
        session_repo.create("delta_ses")
        obs_repo.add(entity_name="D1", obs_type="fact", content="d1_c", confidence=0.5, session_id="delta_ses")
        obs_repo.add(entity_name="D2", obs_type="fact", content="d2_c", confidence=0.6, session_id="delta_ses")

        # Query with a timestamp before all observations
        delta = session_repo.get_delta("delta_ses", "2000-01-01")
        assert delta["changed"] == 2
        assert delta["total"] == 2

    def test_get_delta_respects_since_ts(
        self, session_repo: SessionRepo, obs_repo: ObsRepo
    ) -> None:
        session_repo.create("ts_delta")
        # Add one observation now
        obs_repo.add(entity_name="E", obs_type="fact", content="old", confidence=0.5, session_id="ts_delta")
        time.sleep(0.01)
        # Microsecond-precision cutoff — guarantees the first observation is before cutoff
        now = time.time()
        cutoff = time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime(now)) + f"{int(now * 1_000_000) % 1_000_000:06d}Z"

        # Add another after cutoff
        obs_repo.add(entity_name="E", obs_type="fact", content="new", confidence=0.6, session_id="ts_delta")

        delta = session_repo.get_delta("ts_delta", cutoff)
        assert delta["changed"] == 1


class TestRepoSet:
    """Given: RepoSet. When: accessing repos. Then: all three repos are accessible."""

    def test_repo_set_has_all_repos(self, repo_set: RepoSet) -> None:
        assert isinstance(repo_set.node, NodeRepo)
        assert isinstance(repo_set.obs, ObsRepo)
        assert isinstance(repo_set.session, SessionRepo)

    def test_repos_share_same_connection(self, repo_set: RepoSet, db: sqlite3.Connection) -> None:
        """ponytail: simple sanity check — write through node, read through obs.
        Since they share the same db connection, writes are visible."""
        repo_set.node.upsert(path="/shared.py", name="shared", kind="module")
        session_repo = repo_set.session
        session_repo.create("rs_ses")
        repo_set.obs.add(entity_name="Shared", obs_type="fact", content="ok", confidence=1.0)
        results = repo_set.obs.get_by_entity("Shared")
        assert len(results) == 1
