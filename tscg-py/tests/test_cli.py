"""Tests for tscg.cli — Click CLI compress, proxy, estimate subcommands."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from tscg.cli import cli


# ── Helpers ─────────────────────────────────────────────────────────


def _sample_tools_json() -> list[dict]:
    """Return sample MCP tools in dict format for compress/estimate tests."""
    return [
        {
            "name": "read_file",
            "description": "Read a file from the local filesystem.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to read."},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to a file at the specified path.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to write."},
                    "content": {"type": "string", "description": "Content to write to the file."},
                },
                "required": ["path", "content"],
            },
        },
    ]


def _write_tools_json(tools: list[dict]) -> str:
    """Write tools to a temp JSON file and return the path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(tools, tmp)
    tmp.close()
    return tmp.name


# ── Runner fixture ──────────────────────────────────────────────────


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ── Tests: CLI group ────────────────────────────────────────────────


class TestCliGroup:
    """Tests for the top-level 'tscg' CLI group."""

    def test_help_shows_subcommands(self, runner):
        """Given the tscg CLI,
        When --help is invoked,
        Then it shows compress, proxy, and estimate subcommands."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "compress" in result.output
        assert "proxy" in result.output
        assert "estimate" in result.output

    def test_no_args_shows_usage(self, runner):
        """Given no arguments,
        When CLI is invoked,
        Then it shows missing command error."""
        result = runner.invoke(cli)
        assert result.exit_code != 0
        assert "Usage:" in result.output or "Commands:" in result.output


# ── Tests: compress subcommand ──────────────────────────────────────


class TestCompressCommand:
    """Tests for 'tscg compress' subcommand."""

    def test_compress_basic(self, runner):
        """Given a tools.json file,
        When compress is invoked,
        Then it outputs compressed text to stdout."""
        path = _write_tools_json(_sample_tools_json())
        try:
            result = runner.invoke(cli, ["compress", path])
            assert result.exit_code == 0
            assert "read_file" in result.output
        finally:
            Path(path).unlink(missing_ok=True)

    def test_compress_with_model(self, runner):
        """Given --model claude-3.5-sonnet,
        When compress is invoked,
        Then compression uses Claude-specific transforms."""
        path = _write_tools_json(_sample_tools_json())
        try:
            result = runner.invoke(cli, ["compress", "--model", "claude-3.5-sonnet", path])
            assert result.exit_code == 0
            assert "read_file" in result.output
        finally:
            Path(path).unlink(missing_ok=True)

    def test_compress_aggressive_profile(self, runner):
        """Given --profile aggressive,
        When compress is invoked,
        Then aggressive transforms are applied."""
        path = _write_tools_json(_sample_tools_json())
        try:
            result = runner.invoke(cli, ["compress", "--profile", "aggressive", path])
            assert result.exit_code == 0
            assert "read_file" in result.output
        finally:
            Path(path).unlink(missing_ok=True)

    def test_compress_output_to_file(self, runner):
        """Given --output flag,
        When compress is invoked,
        Then result is written to the specified file."""
        path = _write_tools_json(_sample_tools_json())
        out_path = None
        try:
            out_path = str(Path(path).parent / "compressed.txt")
            result = runner.invoke(cli, ["compress", "--output", out_path, path])
            assert result.exit_code == 0
            written = Path(out_path).read_text(encoding="utf-8")
            assert "read_file" in written
        finally:
            Path(path).unlink(missing_ok=True)
            if out_path:
                Path(out_path).unlink(missing_ok=True)

    def test_compress_file_not_found(self, runner):
        """Given a nonexistent file path,
        When compress is invoked,
        Then it exits with non-zero and shows error."""
        result = runner.invoke(cli, ["compress", "nonexistent_file.json"])
        assert result.exit_code != 0

    def test_compress_invalid_json(self, runner):
        """Given a file with invalid JSON,
        When compress is invoked,
        Then it exits with non-zero and shows error."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        tmp.write("not valid json {{{")
        tmp.close()
        try:
            result = runner.invoke(cli, ["compress", tmp.name])
            assert result.exit_code != 0
        finally:
            Path(tmp.name).unlink(missing_ok=True)


# ── Tests: estimate subcommand ──────────────────────────────────────


class TestEstimateCommand:
    """Tests for 'tscg estimate' subcommand."""

    def test_estimate_shows_savings(self, runner):
        """Given a tools.json file,
        When estimate is invoked,
        Then it shows a savings percentage report."""
        path = _write_tools_json(_sample_tools_json())
        try:
            result = runner.invoke(cli, ["estimate", path])
            assert result.exit_code == 0
            assert "savings" in result.output.lower() or "%" in result.output
        finally:
            Path(path).unlink(missing_ok=True)

    def test_estimate_file_not_found(self, runner):
        """Given a nonexistent file path,
        When estimate is invoked,
        Then it exits with non-zero."""
        result = runner.invoke(cli, ["estimate", "nonexistent_file.json"])
        assert result.exit_code != 0


# ── Tests: proxy subcommand ─────────────────────────────────────────


class TestProxyCommand:
    """Tests for 'tscg proxy' subcommand."""

    def test_proxy_parses_config(self, runner):
        """Given --downstream-url,
        When proxy is invoked,
        Then it prints the parsed configuration."""
        result = runner.invoke(cli, ["proxy", "--downstream-url", "http://localhost:8080"])
        assert result.exit_code == 0
        assert "http://localhost:8080" in result.output

    def test_proxy_with_model_and_profile(self, runner):
        """Given --model and --profile,
        When proxy is invoked,
        Then configuration includes those values."""
        result = runner.invoke(
            cli,
            [
                "proxy",
                "--downstream-url", "http://localhost:9999",
                "--model", "claude-3.5-sonnet",
                "--profile", "aggressive",
            ],
        )
        assert result.exit_code == 0
        assert "http://localhost:9999" in result.output
        assert "claude-3.5-sonnet" in result.output.lower()
        assert "aggressive" in result.output.lower()

    def test_proxy_help(self, runner):
        """Given 'tscg proxy --help',
        When invoked,
        Then it shows proxy options."""
        result = runner.invoke(cli, ["proxy", "--help"])
        assert result.exit_code == 0
        assert "--downstream-url" in result.output
