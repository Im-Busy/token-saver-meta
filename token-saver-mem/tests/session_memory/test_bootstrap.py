"""Tests for session_memory.bootstrap — one-call context bootstrap."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from token_saver_mem.session_memory.continuity import ContextPack
from token_saver_mem.session_memory.bootstrap import (
    BootstrapResult,
    bootstrap_context,
    scope_resolve,
)

# ── Helpers ───────────────────────────────────────────────────────


SESS_BASIC = """\
Objective: Build a FastAPI backend for user management.

TODO: Set up database schema for users table.
TODO: Implement password hashing with bcrypt.
Decision: Will use PostgreSQL for persistence.
"""


def _make_project_dir(contents: dict[str, str | dict], dirs: list[str] | None = None) -> Path:
    """Create a temp project dir with given file contents and optional subdirs."""
    tmp = tempfile.mkdtemp(prefix="tsm_test_")
    project = Path(tmp) / "project"
    project.mkdir(parents=True)
    for relpath, content in contents.items():
        filepath = project / relpath
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            filepath.write_text(content, encoding="utf-8")
        # dict values are directories — just ensure they exist
    for d in (dirs or []):
        (project / d).mkdir(parents=True, exist_ok=True)
    return project


# ── BootstrapResult ───────────────────────────────────────────────


class TestBootstrapResult:
    """BootstrapResult dataclass tests."""

    def test_all_fields_present(self) -> None:
        """Given BootstrapResult, both scope and context_pack are accessible."""
        from token_saver_mem.session_memory.state import OperationalState
        from token_saver_mem.session_memory.continuity import PackStats
        stats = PackStats(session_id="test")
        cp = ContextPack(text="# test", stats=stats, operational_state=OperationalState())
        result = BootstrapResult(scope={"language": "python"}, context_pack=cp)
        assert result.scope == {"language": "python"}
        assert isinstance(result.context_pack, ContextPack)


# ── scope_resolve ─────────────────────────────────────────────────


class TestScopeResolve:
    """scope_resolve() tests."""

    def test_detects_python_and_fastapi(self) -> None:
        """Given a project with main.py + requirements.txt, When resolved,
        Then language=python, project_type=fastapi."""
        project = _make_project_dir({
            "main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "requirements.txt": "fastapi\nuvicorn\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert scope["language"] == "python"
            assert scope["project_type"] == "web"  # FastAPI → web
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_detects_django_project(self) -> None:
        """Given a project with manage.py, When resolved, Then project_type includes django."""
        project = _make_project_dir({
            "manage.py": "#!/usr/bin/env python\nfrom django.core.management import execute_from_command_line\n",
            "requirements.txt": "django>=4.2\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert scope["language"] == "python"
            assert "django" in str(scope.get("frameworks", []))
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_detects_typescript_project(self) -> None:
        """Given a project with package.json + tsconfig.json, When resolved,
        Then language=typescript."""
        project = _make_project_dir({
            "package.json": '{"name": "test", "dependencies": {"typescript": "^5.0"}}',
            "tsconfig.json": '{"compilerOptions": {"strict": true}}',
            "src/index.ts": "export const hello = 'world';\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert scope["language"] == "typescript"
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_detects_rust_project(self) -> None:
        """Given a project with Cargo.toml, When resolved, Then language=rust."""
        project = _make_project_dir({
            "Cargo.toml": '[package]\nname = "test"\nversion = "0.1.0"\n',
            "src/main.rs": "fn main() { println!(\"hello\"); }\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert scope["language"] == "rust"
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_unknown_project_type_when_no_markers(self) -> None:
        """Given an empty directory, When resolved, Then language=unknown."""
        project = _make_project_dir({})
        try:
            scope = scope_resolve(str(project))
            assert scope["language"] == "unknown"
            assert scope["project_type"] == "unknown"
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_returns_key_files(self) -> None:
        """Given a Python project, When resolved, Then key_files includes main.py."""
        project = _make_project_dir({
            "main.py": "print('hello')\n",
            "requirements.txt": "fastapi\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert len(scope["key_files"]) >= 1
            assert any("main.py" in f for f in scope["key_files"])
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_framework_detection_in_python(self) -> None:
        """Given Python project with frameworks, When resolved, Then frameworks list populated."""
        project = _make_project_dir({
            "main.py": "from fastapi import FastAPI\n",
            "requirements.txt": "fastapi\npydantic\nsqlalchemy\n",
            "pyproject.toml": "[project]\nname = 'test'\n",
        })
        try:
            scope = scope_resolve(str(project))
            assert "frameworks" in scope
            assert len(scope["frameworks"]) >= 1
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_key_files_filtered_to_relevant(self) -> None:
        """Given a project, When resolved, Then key_files only include meaningful files."""
        project = _make_project_dir(
            {
                "main.py": "pass\n",
                "README.md": "# docs\n",
            },
            dirs=["__pycache__"],
        )
        try:
            scope = scope_resolve(str(project))
            # Should include main.py, not README or pycache
            key_files_str = " ".join(scope["key_files"])
            assert "main.py" in key_files_str
            assert "README" not in key_files_str
            assert "__pycache__" not in key_files_str
        finally:
            import shutil
            shutil.rmtree(project.parent)


# ── bootstrap_context ─────────────────────────────────────────────


class TestBootstrapContext:
    """bootstrap_context() tests."""

    def test_returns_bootstrap_result(self) -> None:
        """Given session_text, When bootstrap_context called, Then BootstrapResult returned."""
        result = bootstrap_context(SESS_BASIC)
        assert isinstance(result, BootstrapResult)
        assert "language" in result.scope
        assert isinstance(result.context_pack, ContextPack)

    def test_text_based_scope_from_session(self) -> None:
        """Given session_text mentioning FastAPI, When bootstrap_context with no project_path,
        Then scope detection works from text."""
        result = bootstrap_context(SESS_BASIC)
        scope = result.scope
        assert scope["language"] == "python"
        assert "web" in scope["project_type"] or "fastapi" in str(scope.get("frameworks", []))

    def test_file_based_scope_when_project_path_given(self) -> None:
        """Given a project_path with Python files, When bootstrap_context called,
        Then file-based scope resolution is used."""
        project = _make_project_dir({
            "main.py": "from fastapi import FastAPI\n",
            "requirements.txt": "fastapi\n",
        })
        try:
            result = bootstrap_context("some session text", project_path=str(project))
            scope = result.scope
            assert scope["language"] == "python"
            # Should have key_files from filesystem
            assert len(scope["key_files"]) >= 1
        finally:
            import shutil
            shutil.rmtree(project.parent)

    def test_one_call_does_both(self) -> None:
        """Given session_text, When bootstrap_context called once,
        Then both scope and context_pack are populated."""
        result = bootstrap_context("Task: Fix login bug. Decision: Use JWT.")
        # Both should be present — no need for separate calls
        assert "language" in result.scope
        assert len(result.context_pack.text) > 0

    def test_context_pack_has_meaningful_content(self) -> None:
        """Given session_text with decisions and todos, When bootstrap_context called,
        Then context_pack has content."""
        result = bootstrap_context(SESS_BASIC)
        pack = result.context_pack
        assert "Objective" in pack.text or "objective" in pack.text.lower()
        assert pack.stats.observation_count > 0

    def test_empty_project_path_works(self) -> None:
        """Given empty project_path, When bootstrap_context called, Then no crash."""
        result = bootstrap_context(SESS_BASIC, project_path=None)
        assert result.scope["language"] is not None
        assert len(result.context_pack.text) > 0

    def test_non_existent_project_path(self) -> None:
        """Given a non-existent project_path, When bootstrap_context called,
        Then falls back to text-based scope."""
        result = bootstrap_context(SESS_BASIC, project_path="/nonexistent/path/xyz")
        # Should still return results (falls back to text-based)
        assert "language" in result.scope

    def test_pack_budget_defaults_to_auto(self) -> None:
        """Given any session, When bootstrap_context called,
        Then context_pack uses auto-budget."""
        result = bootstrap_context(SESS_BASIC)
        assert result.context_pack.stats.budget_used == "micro"
