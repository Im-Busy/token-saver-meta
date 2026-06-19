"""Integration tests for token-saver-mem — end-to-end session lifecycle scenarios.

Tests the full flow across code_memory and session_memory subsystems,
including index, search, delta, staleness, context packs, and bootstrap.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import pytest

from token_saver_mem.code_memory.db import (
    get_connection,
    init_schema,
    upsert_nodes,
)
from token_saver_mem.code_memory.delta import get_delta_payload
from token_saver_mem.code_memory.indexer import index_directory
from token_saver_mem.code_memory.staleness import check_staleness, mark_fresh
from token_saver_mem.code_memory.work_plan import get_work_plan
from token_saver_mem.session_memory.bootstrap import bootstrap_context
from token_saver_mem.session_memory.caching import stable_hash
from token_saver_mem.session_memory.continuity import build_context_pack
from token_saver_mem.tools.code.get_context import get_context
from token_saver_mem.tools.code.get_delta import get_delta
from token_saver_mem.tools.code.search_symbols import search_symbols
from token_saver_mem.tools.code.store_understanding import store_understanding
from token_saver_mem.tools.session.bootstrap_context import bootstrap_context_tool
from token_saver_mem.tools.session.completion_check import completion_check_tool
from token_saver_mem.tools.session.context_pack import context_pack_tool
from token_saver_mem.tools.session.open_work import open_work_tool


# ── Session text samples ──────────────────────────────────────────

_SESSION_A = (
    "I'm working on the auth module. The login function needs to return proper "
    "JWT tokens.\n"
    "Completed: set up database schema.\n"
    "Pending: add password hashing.\n"
    "Blocker: waiting for security review approval.\n"
    "Blocker: need API key from third-party service.\n"
)

_SESSION_B = (
    "Building a CLI tool for file processing. Need to add recursive directory "
    "walk.\n"
    "Completed: basic argument parsing.\n"
    "Pending: implement file watcher.\n"
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create a temporary SQLite database with schema initialized."""
    db_path = str(tmp_path / "test_code_memory.db")
    init_schema(db_path)
    return db_path


@pytest.fixture
def sample_py_files(tmp_path: Path) -> Path:
    """Create a directory with sample Python files for indexer testing."""
    src_dir = tmp_path / "sample_project"
    src_dir.mkdir()

    (src_dir / "utils.py").write_text(
        '''"""Utility functions."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y
''',
        encoding="utf-8",
    )

    (src_dir / "models.py").write_text(
        '''"""Data models."""


@dataclass
class User:
    """A user entity."""
    name: str
    age: int

    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}"


def create_user(name: str, age: int) -> User:
    """Factory for User."""
    return User(name=name, age=age)
''',
        encoding="utf-8",
    )

    (src_dir / "broken.py").write_text(
        "def broken(:\n    pass\n",
        encoding="utf-8",
    )

    (src_dir / "README.txt").write_text("This is not Python.", encoding="utf-8")

    (src_dir / "subpkg").mkdir()
    (src_dir / "subpkg" / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "subpkg" / "helpers.py").write_text(
        '''"""Helper functions."""


def normalize(text: str) -> str:
    """Strip and lowercase."""
    return text.strip().lower()
''',
        encoding="utf-8",
    )

    return src_dir


@pytest.fixture
def populated_db(temp_db: str) -> str:
    """A database pre-populated with sample code nodes."""
    import json

    conn = get_connection(temp_db)
    try:
        now = time.time()
        nodes = [
            {
                "id": "function:utils.py:add",
                "kind": "function",
                "name": "add",
                "path": "utils.py",
                "start_line": 4,
                "end_line": 7,
                "content_hash": "f5a5c9d4e",
                "summary": "Add two numbers.",
                "summary_hash": "f5a5c9d4e",
                "metadata": json.dumps({"params": ["a:int", "b:int"], "return_type": "int"}),
                "updated_at": now,
                "deleted_at": None,
            },
            {
                "id": "function:utils.py:multiply",
                "kind": "function",
                "name": "multiply",
                "path": "utils.py",
                "start_line": 10,
                "end_line": 13,
                "content_hash": "a1b2c3d4e",
                "summary": "Multiply two numbers.",
                "summary_hash": "a1b2c3d4e",
                "metadata": json.dumps({"params": ["x:float", "y:float"], "return_type": "float"}),
                "updated_at": now - 3600,
                "deleted_at": None,
            },
            {
                "id": "class:models.py:User",
                "kind": "class",
                "name": "User",
                "path": "models.py",
                "start_line": 6,
                "end_line": 13,
                "content_hash": "b9d8c7e6f",
                "summary": "A user entity.",
                "summary_hash": "b9d8c7e6f",
                "metadata": json.dumps({"bases": [], "decorators": ["dataclass"]}),
                "updated_at": now - 7200,
                "deleted_at": None,
            },
            {
                "id": "function:stale_example.py:old_func",
                "kind": "function",
                "name": "old_func",
                "path": "stale_example.py",
                "start_line": 1,
                "end_line": 2,
                "content_hash": hashlib.sha256(b"def old_func():pass").hexdigest(),
                "summary": "Does something.",
                "summary_hash": hashlib.sha256(b"Different content hash").hexdigest(),
                "metadata": "{}",
                "updated_at": now,
                "deleted_at": None,
            },
            {
                "id": "function:stale_example.py:unsynced",
                "kind": "function",
                "name": "unsynced",
                "path": "stale_example.py",
                "start_line": 3,
                "end_line": 4,
                "content_hash": hashlib.sha256(b"def unsynced():pass").hexdigest(),
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "updated_at": now,
                "deleted_at": None,
            },
            {
                "id": "function:old_file.py:removed_func",
                "kind": "function",
                "name": "removed_func",
                "path": "old_file.py",
                "start_line": 1,
                "end_line": 2,
                "content_hash": hashlib.sha256(b"def removed_func():pass").hexdigest(),
                "summary": None,
                "summary_hash": None,
                "metadata": "{}",
                "updated_at": now - 86400,
                "deleted_at": now - 3600,
            },
        ]
        upsert_nodes(conn, nodes)
        conn.commit()
    finally:
        conn.close()
    return temp_db


@pytest.fixture
def five_py_project(tmp_path: Path) -> Path:
    """Create a directory with 5 valid Python files for large-project testing."""
    proj = tmp_path / "big_project"
    proj.mkdir()
    (proj / "a.py").write_text("def alpha():\n    return 'alpha'\n\nclass AlphaClass:\n    pass\n", encoding="utf-8")
    (proj / "b.py").write_text("def beta():\n    return 'beta'\n\ndef gamma():\n    return 'gamma'\n", encoding="utf-8")
    (proj / "c.py").write_text("def delta():\n    return 'delta'\n\nclass DeltaClass:\n    def method(self):\n        pass\n", encoding="utf-8")
    (proj / "d.py").write_text("def epsilon():\n    return 'epsilon'\n\nasync def zeta():\n    return 'zeta'\n", encoding="utf-8")
    (proj / "e.py").write_text("def eta():\n    return 'eta'\n\ndef theta():\n    return 'theta'\n", encoding="utf-8")
    return proj


@pytest.fixture
def three_file_project(tmp_path: Path) -> Path:
    """Create a directory with exactly 3 Python files for delta testing."""
    proj = tmp_path / "three_file"
    proj.mkdir()
    (proj / "one.py").write_text("def func_one():\n    return 1\n", encoding="utf-8")
    (proj / "two.py").write_text("def func_two():\n    return 2\n", encoding="utf-8")
    (proj / "three.py").write_text("def func_three():\n    return 3\n", encoding="utf-8")
    return proj


# ── Scenario 1: Full session lifecycle ────────────────────────────


class TestFullSessionLifecycle:
    """End-to-end session lifecycle: index → search → get_context →
    store_understanding → delta → open_work → context_pack →
    bootstrap → completion_check."""

    def test_full_lifecycle(self, temp_db, sample_py_files):
        """Given a test project, exercise the full session lifecycle."""
        # 1. Index the project — capture timestamp BEFORE index for get_delta
        before_index = time.time()
        result = index_directory(str(sample_py_files), temp_db)
        assert result["files_found"] >= 3  # at least utils.py, models.py, helpers.py
        assert result["nodes_written"] > 0

        # 2. search_symbols finds a function
        results = search_symbols(temp_db, "add")
        assert len(results) > 0
        found = [r["name"] for r in results]
        assert "add" in found

        # 3. get_context returns summary (fresh or stale)
        node_id = results[0]["id"]
        ctx = get_context(temp_db, node_id)
        assert ctx["id"] == node_id
        assert ctx["kind"] in ("function", "class", "method")
        assert ctx["name"] in found
        assert "staleness_status" in ctx

        # 4. store_understanding on a node
        succ = store_understanding(temp_db, node_id, "Test summary for lifecycle.")
        assert succ is True

        # 5. get_delta shows changes since before indexing
        delta = get_delta(temp_db, before_index)
        assert delta["total"] > 0
        assert "changed" in delta
        assert "deleted" in delta

        # 6. open_work from session text shows gaps
        ow = open_work_tool(_SESSION_A)
        assert ow["has_open_work"] is True
        assert len(ow["blockers"]) >= 1
        assert len(ow["pending"]) >= 1

        # 7. context_pack with hash caching
        cp = context_pack_tool(_SESSION_A)
        assert "text" in cp
        assert "hash" in cp
        assert len(cp["text"]) > 0
        assert len(cp["hash"]) == 64

        # 8. bootstrap_context recovery
        bt = bootstrap_context_tool(_SESSION_A, project_path=str(sample_py_files))
        assert "scope" in bt
        assert "context_pack" in bt
        scope = bt["scope"]
        assert scope["language"] == "python"
        assert len(bt["context_pack"]["text"]) > 0

        # 9. completion_check
        cc = completion_check_tool(_SESSION_A)
        assert cc["done"] is False
        assert len(cc["blockers"]) >= 1
        assert len(cc["pending"]) >= 1


# ── Scenario 2: Hash caching ─────────────────────────────────────


class TestHashCaching:
    """context_pack_tool returns same hash for identical session text."""

    def test_same_session_same_hash(self):
        """Given the same session text twice, context_pack_tool returns same hash."""
        cp1 = context_pack_tool(_SESSION_A)
        cp2 = context_pack_tool(_SESSION_A)
        assert cp1["hash"] == cp2["hash"]
        assert len(cp1["hash"]) == 64

    def test_stable_hash_deterministic(self):
        """stable_hash is deterministic across calls."""
        h1 = stable_hash(_SESSION_A)
        h2 = stable_hash(_SESSION_A)
        assert h1 == h2
        assert len(h1) == 64


# ── Scenario 3: Delta tracking ───────────────────────────────────


class TestDeltaTracking:
    """Index → modify → re-index → get_delta shows changed count."""

    def test_delta_tracks_one_change(self, temp_db, three_file_project):
        """Given a project with 3 files, modifying 1 file produces delta count=1."""
        # First index
        result1 = index_directory(str(three_file_project), temp_db)
        assert result1["files_indexed"] == 3
        assert result1["nodes_written"] == 3  # one func per file

        before_mod = time.time()

        # Modify one file
        f = three_file_project / "two.py"
        f.write_text("def func_two():\n    return 42\n", encoding="utf-8")

        # Re-index
        result2 = index_directory(str(three_file_project), temp_db)
        assert result2["files_indexed"] == 1  # only the modified file

        # get_delta shows 1 changed
        delta = get_delta(temp_db, before_mod)
        assert delta["changed"] == 1, f"Expected 1 changed, got {delta}"
        assert delta["deleted"] == 0

    def test_unchanged_files_no_delta(self, temp_db, three_file_project):
        """Re-index without modification produces zero delta."""
        index_directory(str(three_file_project), temp_db)
        before_reindex = time.time()
        result2 = index_directory(str(three_file_project), temp_db)
        assert result2["files_indexed"] == 0  # all unchanged

        delta = get_delta(temp_db, before_reindex)
        assert delta["total"] == 0


# ── Scenario 4: Read-only guard ──────────────────────────────────


class TestReadOnlyGuard:
    """store_understanding succeeds — it's a tool, not server-gated."""

    def test_store_understanding_succeeds(self, populated_db):
        """Given a populated DB, store_understanding writes a summary."""
        node_id = "function:utils.py:add"
        succ = store_understanding(populated_db, node_id, "Adds two integers together.")
        assert succ is True

    def test_store_understanding_on_nonexistent_node(self, populated_db):
        """Given a nonexistent node ID, returns False."""
        succ = store_understanding(populated_db, "function:ghost.py:missing", "Summary.")
        assert succ is False


# ── Scenario 5: Cross-session continuity ─────────────────────────


class TestCrossSessionContinuity:
    """Different session texts produce different context pack hashes."""

    def test_different_sessions_produce_different_hashes(self):
        """Given two different session texts, hashes differ."""
        cp_a = context_pack_tool(_SESSION_A)
        cp_b = context_pack_tool(_SESSION_B)
        assert cp_a["hash"] != cp_b["hash"]

    def test_different_sessions_different_pack_text(self):
        """Given two different session texts, context pack text differs."""
        cp_a = context_pack_tool(_SESSION_A)
        cp_b = context_pack_tool(_SESSION_B)
        assert cp_a["text"] != cp_b["text"]

    def test_build_context_pack_reproducible(self):
        """build_context_pack returns same text for same session."""
        pack1 = build_context_pack(_SESSION_A)
        pack2 = build_context_pack(_SESSION_A)
        assert pack1.text == pack2.text
        assert pack1.stats.session_id == pack2.stats.session_id


# ── Scenario 6: Work plan priority ───────────────────────────────


class TestWorkPlanPriority:
    """Unannotated nodes → DOCUMENT; annotated → lower priority."""

    def test_unannotated_yields_document_priority(self, temp_db, sample_py_files):
        """Given unannotated nodes, get_work_plan returns DOCUMENT priority."""
        index_directory(str(sample_py_files), temp_db)
        plan = get_work_plan(temp_db)
        assert plan.priority == "DOCUMENT"
        assert len(plan.tasks) > 0
        assert all(t["priority"] == "DOCUMENT" for t in plan.tasks)

    def test_fully_annotated_yields_lower_or_nothing(self, temp_db, sample_py_files):
        """Given all nodes annotated, get_work_plan returns EXPLORE or NOTHING."""
        index_directory(str(sample_py_files), temp_db)

        # Store summaries for all indexed nodes
        conn = get_connection(temp_db)
        try:
            rows = conn.execute(
                "SELECT id FROM code_nodes WHERE deleted_at IS NULL"
            ).fetchall()
            for row in rows:
                store_understanding(temp_db, row["id"], f"Summary for {row['id']}.")
        finally:
            conn.close()

        plan = get_work_plan(temp_db)
        # After annotation, priority should be EXPLORE or NOTHING (not DOCUMENT)
        assert plan.priority in ("EXPLORE", "NOTHING"), (
            f"Expected EXPLORE or NOTHING, got {plan.priority}"
        )


# ── Scenario 7: Staleness flow ───────────────────────────────────


class TestStalenessFlow:
    """mark_fresh → check_staleness empty; modify content → check_staleness returns."""

    def test_staleness_flow(self, temp_db, sample_py_files):
        """Full staleness lifecycle: fresh → mark → check empty → modify → check returns."""
        index_directory(str(sample_py_files), temp_db)

        conn = get_connection(temp_db)
        try:
            rows = conn.execute(
                "SELECT id FROM code_nodes WHERE deleted_at IS NULL"
            ).fetchall()
            node_ids = [r["id"] for r in rows]
        finally:
            conn.close()

        assert len(node_ids) > 0

        # Step 1: Mark all nodes fresh
        for nid in node_ids:
            ok = mark_fresh(temp_db, nid)
            assert ok is True

        # Step 2: check_staleness returns empty after marking fresh
        stale = check_staleness(temp_db)
        assert len(stale) == 0, f"Expected 0 stale, got {len(stale)}: {stale}"

        # Step 3: Directly modify content_hash to simulate content change
        conn = get_connection(temp_db)
        try:
            new_hash = hashlib.sha256(b"modified content").hexdigest()
            conn.execute(
                "UPDATE code_nodes SET content_hash = ? WHERE id = ?",
                (new_hash, node_ids[0]),
            )
            conn.commit()
        finally:
            conn.close()

        # Step 4: check_staleness now returns the changed node
        stale_after = check_staleness(temp_db)
        assert len(stale_after) >= 1
        found = [s["id"] for s in stale_after]
        assert node_ids[0] in found

    def test_mark_fresh_nonexistent_node(self, temp_db):
        """mark_fresh returns False for nonexistent node."""
        ok = mark_fresh(temp_db, "function:ghost.py:phantom")
        assert ok is False


# ── Scenario 8: Large-ish project (5 Python files) ───────────────


class TestLargeProject:
    """Index a directory with 5 Python files, verify all are searchable."""

    def test_all_five_files_indexed(self, temp_db, five_py_project):
        """Given 5 Python files, index_directory indexes all of them."""
        result = index_directory(str(five_py_project), temp_db)
        assert result["files_found"] == 5
        assert result["files_indexed"] == 5
        assert result["nodes_written"] >= 8  # functions + classes + methods
        assert result["errors"] == 0

    def test_search_finds_functions_across_files(self, temp_db, five_py_project):
        """Given indexed 5 files, search_symbols finds expected functions."""
        index_directory(str(five_py_project), temp_db)

        # Search for individual functions
        assert len(search_symbols(temp_db, "alpha")) >= 1
        assert len(search_symbols(temp_db, "beta")) >= 1
        assert len(search_symbols(temp_db, "gamma")) >= 1
        assert len(search_symbols(temp_db, "delta")) >= 1  # function delta, not class
        assert len(search_symbols(temp_db, "epsilon")) >= 1
        assert len(search_symbols(temp_db, "zeta")) >= 1
        assert len(search_symbols(temp_db, "eta")) >= 1
        assert len(search_symbols(temp_db, "theta")) >= 1

    def test_all_nodes_present_in_db(self, temp_db, five_py_project):
        """Given indexed project, DB contains all expected nodes by kind."""
        index_directory(str(five_py_project), temp_db)

        conn = get_connection(temp_db)
        try:
            funcs = conn.execute(
                "SELECT COUNT(*) FROM code_nodes WHERE kind='function' AND deleted_at IS NULL"
            ).fetchone()[0]
            classes = conn.execute(
                "SELECT COUNT(*) FROM code_nodes WHERE kind='class' AND deleted_at IS NULL"
            ).fetchone()[0]
            methods = conn.execute(
                "SELECT COUNT(*) FROM code_nodes WHERE kind='method' AND deleted_at IS NULL"
            ).fetchone()[0]
        finally:
            conn.close()

        # Expected: 8 functions (alpha, beta, gamma, delta, epsilon, zeta, eta, theta)
        # + 2 classes (AlphaClass, DeltaClass)
        # + 1 method (DeltaClass.method)
        assert funcs >= 8, f"Expected >=8 functions, got {funcs}"
        assert classes == 2, f"Expected 2 classes, got {classes}"
        assert methods >= 1, f"Expected >=1 methods, got {methods}"
