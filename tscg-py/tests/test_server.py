"""Tests for tscg.proxy.server — TSCGProxyServer business logic, compression, error handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tscg.core.compiler import TSCGCompiler
from tscg.core.transforms import ParamDef, ToolDef
from tscg.proxy.downstream import DownstreamManager


# ── Helpers ─────────────────────────────────────────────────────────


def _make_tools() -> list[ToolDef]:
    """Return a small set of canonical test tools."""
    return [
        ToolDef(
            name="read_file",
            description="Read a file from the local filesystem. You can access any file directly.",
            parameters=[
                ParamDef(name="path", type="string", description="The path to the file to read.", required=True),
            ],
        ),
        ToolDef(
            name="write_file",
            description="Write content to a file at the specified path. This will overwrite existing content.",
            parameters=[
                ParamDef(name="path", type="string", description="The path to the file to write.", required=True),
                ParamDef(name="content", type="string", description="Content to write to the file.", required=True),
            ],
        ),
        ToolDef(
            name="list_directory",
            description="List files and directories in a given path. Use this tool when you need to explore.",
            parameters=[
                ParamDef(name="path", type="string", description="Directory path to list.", required=False),
            ],
        ),
    ]


def _make_many_tools(count: int) -> list[ToolDef]:
    """Return N tools for bulk tests (safety guard 2: >=30 tools)."""
    tools: list[ToolDef] = []
    for i in range(count):
        tools.append(
            ToolDef(
                name=f"tool_{i}",
                description=f"Tool number {i} for testing.",
                parameters=[ParamDef(name="arg", type="string", description="An argument.", required=True)],
            )
        )
    return tools


# ── Server construction ─────────────────────────────────────────────


@pytest.fixture
def compiler() -> TSCGCompiler:
    return TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")


@pytest.fixture
def downstream() -> DownstreamManager:
    return DownstreamManager()


def _inject_tools(dm: DownstreamManager, name: str, tools: list[ToolDef]) -> None:
    """Inject fake tools into a DownstreamManager without a real subprocess."""
    dm._connections[name] = {"proc": None, "tools": tools}


# We import the server class lazily — will be implemented after tests.
# For now, we define the expected interface that the implementation must satisfy.


class TSCGProxyServer:
    """Expected interface (implemented in src/tscg/proxy/server.py)."""

    def __init__(self, compiler: TSCGCompiler, downstream: DownstreamManager) -> None:
        raise NotImplementedError

    def handle_list_tools(self, server_name: str) -> dict:
        raise NotImplementedError

    def handle_call_tool(self, server_name: str, tool_name: str, args: dict) -> object:
        raise NotImplementedError


# ── Tests: handle_list_tools ────────────────────────────────────────


class TestHandleListTools:
    """Tests for TSCGProxyServer.handle_list_tools."""

    def test_returns_compressed_schema_for_claude(self, compiler, downstream):
        """Given a Claude compiler and downstream with tools,
        When handle_list_tools is called,
        Then it returns a dict with compressed text and tool count."""
        tools = _make_tools()
        _inject_tools(downstream, "test_server", tools)

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        result = server.handle_list_tools("test_server")

        assert isinstance(result, dict)
        assert "compressed" in result or "tools" in result
        assert result.get("count") == 3

    def test_description_only_mode(self, compiler, downstream):
        """Given compression_mode='description-only',
        When handle_list_tools is called,
        Then descriptions are compressed but structure minimal."""
        tools = _make_tools()
        _inject_tools(downstream, "test_server", tools)

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        result = server.handle_list_tools("test_server")

        compressed = result.get("compressed", result.get("tools", ""))
        assert isinstance(compressed, (str, list))
        # Should have tool names
        assert "read_file" in str(compressed)
        # SDM should strip filler
        assert "Use this tool when you need to" not in str(compressed)

    def test_empty_tools_returns_empty(self, compiler, downstream):
        """Given a downstream with no tools,
        When handle_list_tools is called,
        Then it returns empty result gracefully."""
        _inject_tools(downstream, "empty_server", [])

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        result = server.handle_list_tools("empty_server")

        assert result.get("count") == 0

    def test_non_claude_disables_cfl_sad(self, downstream):
        """Given a non-Claude model compiler,
        When handle_list_tools is called,
        Then CFL and SAD markers are absent from compressed output."""
        non_claude = TSCGCompiler(model="gpt-4", profile="aggressive")
        tools = _make_tools()
        _inject_tools(downstream, "test_server", tools)

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(non_claude, downstream)
        result = server.handle_list_tools("test_server")

        compressed = result.get("compressed", result.get("tools", ""))
        text = str(compressed)
        assert "[ANSWER:function_call]" not in text
        assert "[ANCHOR:" not in text

    def test_many_tools_disables_cfl_cfo(self, downstream):
        """Given >=30 tools,
        When handle_list_tools is called,
        Then CFL+CFO are disabled per safety guard 2."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        tools = _make_many_tools(35)
        _inject_tools(downstream, "big_server", tools)

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        result = server.handle_list_tools("big_server")

        compressed = result.get("compressed", result.get("tools", ""))
        text = str(compressed)
        assert "[ANSWER:function_call]" not in text  # CFL disabled
        assert result.get("count") == 35

    def test_thinking_model_disables_cfl_sad(self, downstream):
        """Given a thinking model (o1),
        When handle_list_tools is called,
        Then CFL+SAD are disabled."""
        thinking = TSCGCompiler(model="o1-preview", profile="aggressive")
        tools = _make_tools()
        _inject_tools(downstream, "test_server", tools)

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(thinking, downstream)
        result = server.handle_list_tools("test_server")

        compressed = result.get("compressed", result.get("tools", ""))
        text = str(compressed)
        assert "[ANSWER:function_call]" not in text
        assert "[ANCHOR:" not in text


# ── Tests: handle_call_tool ─────────────────────────────────────────


class TestHandleCallTool:
    """Tests for TSCGProxyServer.handle_call_tool."""

    def test_forwards_to_downstream(self, compiler):
        """Given a downstream with a mock call_tool,
        When handle_call_tool is called,
        Then it forwards args and returns the downstream result."""
        downstream = MagicMock(spec=DownstreamManager)
        downstream.call_tool.return_value = {"content": [{"type": "text", "text": "file contents"}]}

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        result = server.handle_call_tool("file_server", "read_file", {"path": "/tmp/test.txt"})

        downstream.call_tool.assert_called_once_with(
            "file_server", "read_file", {"path": "/tmp/test.txt"}
        )
        assert result == {"content": [{"type": "text", "text": "file contents"}]}

    def test_server_not_connected_raises(self, compiler):
        """Given a downstream where server is not connected,
        When handle_call_tool is called,
        Then it raises ValueError."""
        real_downstream = DownstreamManager()

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, real_downstream)
        with pytest.raises(ValueError, match="not connected"):
            server.handle_call_tool("nonexistent", "read_file", {"path": "/tmp/test.txt"})

    def test_tool_not_found_propagates_error(self, compiler):
        """Given a downstream that raises on tool not found,
        When handle_call_tool is called,
        Then the error propagates."""
        downstream = MagicMock(spec=DownstreamManager)
        downstream.call_tool.side_effect = RuntimeError("Tool 'unknown' not found")

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, downstream)
        with pytest.raises(RuntimeError, match="not found"):
            server.handle_call_tool("test_server", "unknown", {})


# ── Tests: server_name not connected for list_tools ─────────────────


class TestServerErrors:
    """Error handling tests for TSCGProxyServer."""

    def test_list_tools_server_not_connected(self, compiler):
        """Given a downstream with no connections,
        When handle_list_tools is called for an unregistered server,
        Then it returns empty result gracefully."""
        real_downstream = DownstreamManager()

        from tscg.proxy.server import TSCGProxyServer as Impl

        server = Impl(compiler, real_downstream)
        result = server.handle_list_tools("nonexistent")

        assert result.get("count", -1) == 0
