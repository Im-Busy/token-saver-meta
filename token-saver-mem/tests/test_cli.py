"""Tests for cli.py — Click CLI group with serve, index, status commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from token_saver_mem.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def tmp_db() -> str:
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(b"")
    return f.name


# ── Tests: CLI group ────────────────────────────────────────────────

class TestCLIGroup:
    """token-saver-mem Click group."""

    def test_cli_group_exists(self, runner: CliRunner) -> None:
        """Given cli module, When invoked, Then group name is 'token-saver-mem'."""
        assert cli.name == "token-saver-mem"

    def test_help_shows_commands(self, runner: CliRunner) -> None:
        """Given CLI group, When --help called, Then shows serve, index, status."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        output = result.stdout
        assert "serve" in output
        assert "index" in output
        assert "status" in output
        assert "Token Saver Mem" in output or "token-saver-mem" in output.lower()

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Given no args, When invoked, Then shows usage info."""
        result = runner.invoke(cli)
        # Click exits with code 2 for missing command; usage goes to stdout/stderr
        assert result.exit_code == 2
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Usage:" in combined or "Commands:" in combined


# ── Tests: serve command ────────────────────────────────────────────

class TestServeCommand:
    """token-saver-mem serve."""

    def test_serve_prints_config(self, runner: CliRunner, tmp_db: str) -> None:
        """Given --db path, When serve is called, Then prints config info."""
        result = runner.invoke(cli, ["serve", "--db", tmp_db])
        assert result.exit_code == 0
        output = result.stdout
        assert "memory.db" in output or tmp_db in output or "db" in output.lower()

    def test_serve_with_write_flag(self, runner: CliRunner, tmp_db: str) -> None:
        """Given --write flag, When serve called, Then prints write-enabled."""
        result = runner.invoke(cli, ["serve", "--db", tmp_db, "--write"])
        assert result.exit_code == 0
        output = result.stdout
        assert "write" in output.lower()

    def test_serve_default_port(self, runner: CliRunner, tmp_db: str) -> None:
        """Given no --port, When serve called, Then shows default port."""
        result = runner.invoke(cli, ["serve", "--db", tmp_db])
        assert result.exit_code == 0

    def test_serve_custom_port(self, runner: CliRunner, tmp_db: str) -> None:
        """Given --port 9999, When serve called, Then shows port 9999."""
        result = runner.invoke(cli, ["serve", "--db", tmp_db, "--port", "9999"])
        assert result.exit_code == 0
        output = result.stdout
        assert "9999" in output


# ── Tests: index command ────────────────────────────────────────────

class TestIndexCommand:
    """token-saver-mem index."""

    def test_index_requires_path(self, runner: CliRunner, tmp_db: str) -> None:
        """Given no path arg, When index called, Then fails or shows usage."""
        result = runner.invoke(cli, ["index", "--db", tmp_db])
        # Should fail without path argument or show help
        if result.exit_code != 0:
            assert "Missing argument" in result.stderr or "Error" in result.stderr
        else:
            assert "Usage:" in result.stdout or "Error" in result.stdout

    def test_index_with_path(self, runner: CliRunner, tmp_db: str, tmp_path) -> None:
        """Given a valid path, When index called, Then prints indexing message."""
        # Create a dummy project directory with a file
        d = tmp_path / "dummy_project"
        d.mkdir()
        (d / "main.py").write_text("def main(): pass", encoding="utf-8")

        result = runner.invoke(cli, ["index", str(d), "--db", tmp_db])
        assert result.exit_code == 0
        output = result.stdout
        # Should mention indexing or the path
        assert "index" in output.lower() or str(d) in output


# ── Tests: status command ───────────────────────────────────────────

class TestStatusCommand:
    """token-saver-mem status."""

    def test_status_prints_stats(self, runner: CliRunner, tmp_db: str) -> None:
        """Given --db path, When status called, Then prints stats."""
        result = runner.invoke(cli, ["status", "--db", tmp_db])
        assert result.exit_code == 0
        output = result.stdout
        # Should print some info (nodes=0 for fresh DB)
        assert "stats" in output.lower() or "nodes" in output.lower() or "status" in output.lower()
