"""
Downstream manager — connects to MCP servers via stdio.

Manages connections to downstream MCP servers. Supports:
- connect(server_name, subprocess_or_command) for real and test usage
- list_tools(server_name) → list of ToolDef
- call_tool(server_name, tool_name, args) → result
- disconnect(server_name)

For tests: pass a subprocess.Popen instance directly.
For production: use connect_by_command() which spawns via MCP SDK.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Optional

from tscg.core.transforms import ToolDef, ParamDef


class DownstreamManager:
    """Manages connections to downstream MCP servers.

    Each connection is keyed by a server name. Tools are discovered
    via MCP JSON-RPC ``tools/list`` and routed via an internal router.
    """

    def __init__(self) -> None:
        self._connections: dict[str, dict[str, Any]] = {}

    # ── Connection management ────────────────────────────────────

    def connect(self, name: str, proc: subprocess.Popen) -> None:
        """Connect to a downstream MCP server via an existing subprocess.

        Performs MCP initialize handshake + tools/list discovery.

        Args:
            name: Server identifier.
            proc: A running subprocess.Popen with stdin/stdout pipes
                  in text mode. The subprocess must speak MCP JSON-RPC.

        Raises:
            Exception: On handshake failure, timeout, or protocol error.
        """
        self._ensure_readable(proc)

        # MCP initialize handshake
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tscg-proxy", "version": "0.1.0"},
            },
        }
        self._send_message(proc, init_msg)
        init_resp = self._recv_message(proc, timeout=5)
        if "error" in init_resp:
            raise RuntimeError(f"MCP initialize failed: {init_resp['error']}")

        # tools/list
        tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        self._send_message(proc, tools_msg)
        tools_resp = self._recv_message(proc, timeout=5)
        if "error" in tools_resp:
            raise RuntimeError(f"MCP tools/list failed: {tools_resp['error']}")

        raw_tools = tools_resp.get("result", {}).get("tools", [])
        tool_defs = [self._parse_mcp_tool(t) for t in raw_tools]

        self._connections[name] = {
            "proc": proc,
            "tools": tool_defs,
        }

    def connect_by_command(
        self, name: str, command: str, args: list[str] | None = None
    ) -> None:
        """Connect by spawning a subprocess from a command string.

        Args:
            name: Server identifier.
            command: Executable path (e.g. ``sys.executable``).
            args: Command-line arguments (list of strings).
        """
        proc = subprocess.Popen(
            [command] + (args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.connect(name, proc)

    # ── Tool operations ──────────────────────────────────────────

    def list_tools(self, server_name: str) -> list[ToolDef]:
        """Get all tools from a downstream server.

        Args:
            server_name: Registered server identifier.

        Returns:
            List of ToolDef objects. Empty list if server not connected.
        """
        conn = self._connections.get(server_name)
        if conn is None:
            return []
        return list(conn["tools"])

    def call_tool(
        self, server_name: str, tool_name: str, args: dict[str, Any]
    ) -> Any:
        """Call a tool on a downstream server via MCP tools/call.

        Args:
            server_name: Registered server identifier.
            tool_name: Name of the tool to invoke.
            args: Tool arguments (dict).

        Returns:
            Tool execution result (parsed from MCP response).

        Raises:
            ValueError: If server is not connected.
        """
        conn = self._connections.get(server_name)
        if conn is None:
            raise ValueError(f"Server '{server_name}' is not connected")

        proc: subprocess.Popen = conn["proc"]

        call_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args},
        }
        self._send_message(proc, call_msg)
        call_resp = self._recv_message(proc, timeout=5)

        if "error" in call_resp:
            raise RuntimeError(f"MCP tools/call failed: {call_resp['error']}")

        return call_resp.get("result")

    # ── Disconnection ────────────────────────────────────────────

    def disconnect(self, server_name: str) -> None:
        """Disconnect from a server and clean up its subprocess.

        Args:
            server_name: Server identifier. No-op if not connected.
        """
        conn = self._connections.pop(server_name, None)
        if conn is None:
            return

        proc: subprocess.Popen = conn["proc"]
        try:
            if proc.poll() is None:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is currently connected."""
        return server_name in self._connections

    # ── Internal helpers ─────────────────────────────────────────

    @staticmethod
    def _send_message(proc: subprocess.Popen, msg: dict) -> None:
        """Send a JSON-RPC message to the subprocess stdin."""
        if proc.stdin is None or proc.stdin.closed:
            raise RuntimeError("Subprocess stdin is closed")
        proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        proc.stdin.flush()

    @staticmethod
    def _recv_message(proc: subprocess.Popen, timeout: float = 5) -> dict:
        """Receive a JSON-RPC message from subprocess stdout."""
        if proc.stdout is None or proc.stdout.closed:
            raise RuntimeError("Subprocess stdout is closed")
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("Subprocess stdout closed unexpectedly")
        return json.loads(line.strip())

    @staticmethod
    def _ensure_readable(proc: subprocess.Popen) -> None:
        """Verify the subprocess is still alive."""
        ret = proc.poll()
        if ret is not None:
            stderr_data = ""
            if proc.stderr:
                try:
                    stderr_data = proc.stderr.read()
                except Exception:
                    pass
            raise RuntimeError(
                f"Subprocess exited with code {ret}. stderr: {stderr_data}"
            )

    @staticmethod
    def _parse_mcp_tool(raw: dict) -> ToolDef:
        """Parse an MCP tool dict into a ToolDef."""
        input_schema = raw.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required_list: list[str] = input_schema.get("required", [])

        params: list[ParamDef] = []
        for pname, pdef in properties.items():
            param_raw = dict(pdef)  # shallow copy for nested schema preservation
            params.append(
                ParamDef(
                    name=pname,
                    type=pdef.get("type", "string"),
                    description=pdef.get("description", ""),
                    required=(pname in required_list),
                    enum=pdef.get("enum"),
                    raw_json=param_raw,
                )
            )

        return ToolDef(
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            parameters=params,
        )
