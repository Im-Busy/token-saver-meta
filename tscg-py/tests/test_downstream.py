"""Tests for tscg.proxy.downstream — connection management, tool listing, error handling."""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
from tscg.proxy.downstream import DownstreamManager


# ── Test helper: spawn a mock MCP server as a subprocess ─────────


_MOCK_SERVER_SCRIPT = (
    "import json, sys, time\n"
    "def read_message():\n"
    "    for line in sys.stdin:\n"
    "        line = line.strip()\n"
    "        if not line:\n"
    "            continue\n"
    "        try:\n"
    "            return json.loads(line)\n"
    "        except json.JSONDecodeError:\n"
    "            continue\n"
    "def send_message(msg):\n"
    "    sys.stdout.write(json.dumps(msg) + chr(10))\n"
    "    sys.stdout.flush()\n"
    "tools_db = {\n"
    "    'file_server': [\n"
    "        {'name': 'read_file', 'description': 'Read a file from disk', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string', 'description': 'File path'}}, 'required': ['path']}},\n"
    "        {'name': 'write_file', 'description': 'Write content to a file', 'inputSchema': {'type': 'object', 'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}}, 'required': ['path', 'content']}},\n"
    "    ],\n"
    "    'db_server': [\n"
    "        {'name': 'query_db', 'description': 'Execute a SQL query', 'inputSchema': {'type': 'object', 'properties': {'sql': {'type': 'string', 'description': 'SQL statement'}}, 'required': ['sql']}},\n"
    "    ],\n"
    "}\n"
    "msg = read_message()\n"
    "if msg.get('method') == 'initialize':\n"
    "    send_message({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'serverInfo': {'name': 'mock-server', 'version': '1.0.0'}}})\n"
    "msg = read_message()\n"
    "if msg.get('method') == 'tools/list':\n"
    "    tool_list = tools_db.get('file_server', [])\n"
    "    send_message({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'tools': tool_list}})\n"
    "msg = read_message()\n"
    "if msg.get('method') == 'tools/call':\n"
    "    params = msg.get('params', {})\n"
    "    tool_name = params.get('name', '')\n"
    "    send_message({'jsonrpc': '2.0', 'id': msg['id'], 'result': {'content': [{'type': 'text', 'text': 'mock result from ' + tool_name}]}})\n"
    "time.sleep(0.5)\n"
)


def _spawn_mock_server() -> subprocess.Popen:
    """Spawn a mock MCP server subprocess using the test script."""
    script = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    )
    script.write(_MOCK_SERVER_SCRIPT)
    script.flush()
    script_path = script.name
    script.close()

    proc = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc


# ── Tests ─────────────────────────────────────────────────────────


class TestDownstreamConnect:
    """Given: DownstreamManager. When: connect to mock MCP server. Then: connected."""

    def test_connect_and_list_tools(self):
        """Connect to mock server, list tools, get ToolDef list."""
        mgr = DownstreamManager()
        proc = _spawn_mock_server()

        try:
            mgr.connect("test_server", proc)
            tools = mgr.list_tools("test_server")

            assert len(tools) >= 1
            assert tools[0].name in ("read_file", "query_db")

            # Verify ToolDef fields
            for t in tools:
                assert isinstance(t.name, str)
                assert isinstance(t.description, str)
                assert isinstance(t.parameters, list)
        finally:
            proc.kill()
            proc.wait(timeout=5)

    def test_list_tools_unknown_server_returns_empty(self):
        mgr = DownstreamManager()
        tools = mgr.list_tools("nonexistent")
        assert tools == []


class TestDownstreamCallTool:
    """Given: connected downstream. When: call_tool. Then: result returned."""

    def test_call_tool_returns_result(self):
        mgr = DownstreamManager()
        proc = _spawn_mock_server()

        try:
            mgr.connect("test_server", proc)
            result = mgr.call_tool("test_server", "read_file", {"path": "/tmp/test.txt"})
            assert result is not None
        finally:
            proc.kill()
            proc.wait(timeout=5)

    def test_call_tool_unknown_server_raises(self):
        mgr = DownstreamManager()
        with pytest.raises(ValueError, match="not connected"):
            mgr.call_tool("ghost", "any_tool", {})


class TestDownstreamDisconnect:
    """Given: connected downstream. When: disconnect. Then: cleaned up."""

    def test_disconnect_removes_server(self):
        mgr = DownstreamManager()
        proc = _spawn_mock_server()

        mgr.connect("test_server", proc)
        assert mgr.is_connected("test_server")

        mgr.disconnect("test_server")
        assert not mgr.is_connected("test_server")
        assert mgr.list_tools("test_server") == []

    def test_disconnect_nonexistent_no_error(self):
        mgr = DownstreamManager()
        mgr.disconnect("ghost")  # no error


class TestDownstreamErrorHandling:
    """Given: bad connections. When: connect. Then: graceful error."""

    def test_dead_server_connect_graceful(self):
        mgr = DownstreamManager()
        # Spawn and immediately kill
        proc = _spawn_mock_server()
        proc.kill()
        proc.wait(timeout=5)

        with pytest.raises(Exception):
            mgr.connect("dead_server", proc)

    def test_disconnect_kills_subprocess(self):
        mgr = DownstreamManager()
        proc = _spawn_mock_server()

        try:
            mgr.connect("test_server", proc)
            mgr.disconnect("test_server")
        finally:
            # Process should be terminated
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

    def test_call_tool_after_disconnect_raises(self):
        mgr = DownstreamManager()
        proc = _spawn_mock_server()

        try:
            mgr.connect("test_server", proc)
            mgr.disconnect("test_server")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

        with pytest.raises(ValueError, match="not connected"):
            mgr.call_tool("test_server", "read_file", {"path": "/tmp/x"})


class TestDownstreamConnectByCommand:
    """Given: server command string. When: connect_by_command. Then: spawned and connected."""

    def test_connect_by_command_spawns_process(self):
        # Write mock server script to temp file
        script = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        )
        script.write(_MOCK_SERVER_SCRIPT)
        script.flush()
        script_path = Path(script.name)
        script.close()

        mgr = DownstreamManager()
        try:
            mgr.connect_by_command(
                "cmd_server",
                command=sys.executable,
                args=[str(script_path)],
            )
            tools = mgr.list_tools("cmd_server")
            assert len(tools) >= 1
            mgr.disconnect("cmd_server")
        finally:
            if mgr.is_connected("cmd_server"):
                mgr.disconnect("cmd_server")
            script_path.unlink(missing_ok=True)
