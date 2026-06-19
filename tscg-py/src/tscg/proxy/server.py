"""
TSCG Proxy Server — business logic for compressing MCP tool schemas.

Not a full MCP stdio server. Handles tool list compression and
tool call forwarding through the downstream manager. All safety
guards from TSCGCompiler are respected.
"""

from __future__ import annotations

from typing import Any

from tscg.core.compiler import TSCGCompiler
from tscg.proxy.downstream import DownstreamManager


class TSCGProxyServer:
    """Compress MCP tool schemas and forward tool calls.

    Usage::

        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        downstream = DownstreamManager()
        downstream.connect_by_command("files", sys.executable, ["-m", "mcp_server"])
        server = TSCGProxyServer(compiler, downstream)
        result = server.handle_list_tools("files")
    """

    def __init__(self, compiler: TSCGCompiler, downstream: DownstreamManager) -> None:
        """Create a proxy server.

        Args:
            compiler: TSCGCompiler configured with model and profile.
            downstream: DownstreamManager for tool discovery and execution.
        """
        self._compiler = compiler
        self._downstream = downstream

    def handle_list_tools(self, server_name: str) -> dict[str, Any]:
        """Fetch tools from a downstream server and compress them.

        Args:
            server_name: Registered server identifier in the downstream manager.

        Returns:
            Dict with ``compressed`` (str), ``count`` (int), and ``savings`` (float).
            Returns ``{"compressed": "", "count": 0, "savings": 0.0}`` if the server
            has no tools or is not connected.
        """
        tool_defs = self._downstream.list_tools(server_name)
        if not tool_defs:
            return {"compressed": "", "count": 0, "savings": 0.0}

        compiled = self._compiler.compile(tool_defs)

        return {
            "compressed": compiled.compressed_text,
            "count": compiled.tool_count,
            "savings": compiled.savings_pct,
        }

    def handle_call_tool(
        self, server_name: str, tool_name: str, args: dict[str, Any]
    ) -> Any:
        """Forward a tool call to the downstream server.

        Args:
            server_name: Registered server identifier.
            tool_name: Name of the tool to invoke.
            args: Tool arguments dict.

        Returns:
            Tool execution result from the downstream server.

        Raises:
            ValueError: If the server is not connected.
            RuntimeError: If the downstream tool call fails.
        """
        return self._downstream.call_tool(server_name, tool_name, args)
