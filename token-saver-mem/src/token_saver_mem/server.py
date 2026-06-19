"""Unified MCP Server — registers and dispatches all token-saver-mem tools.

Architecture:
  - UnifiedMCPServer: In-memory tool registry with read-only guard.
  - register_tool(name, schema, handler, mutating=False)
  - list_tools() → dict[name, schema]
  - call_tool(name, args) → handler(**args)
  - read_only flag blocks mutating tools unless --write is set.
"""

from __future__ import annotations

from typing import Any, Callable


class UnifiedMCPServer:
    """Lightweight in-memory MCP server for tool registration and dispatch.

    Does NOT implement stdio/HTTP transport — deferred to integration layer.
    Tools are registered by name with JSON Schema and a handler callable.
    """

    def __init__(self, *, read_only: bool = True) -> None:
        """Initialize server.

        Args:
            read_only: If True, mutating tools raise PermissionError on call.
        """
        self.read_only = read_only
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._mutating: dict[str, bool] = {}

    def register_tool(
        self,
        name: str,
        schema: dict[str, Any],
        handler: Callable[..., Any],
        *,
        mutating: bool = False,
    ) -> None:
        """Register a tool with its JSON Schema and handler.

        Args:
            name: Tool name (unique identifier).
            schema: JSON Schema dict describing the tool's input.
            handler: Callable that receives **kwargs from call_tool.
            mutating: True if this tool writes/mutates state (blocked in read_only mode).
        """
        self._tools[name] = schema
        self._handlers[name] = handler
        self._mutating[name] = mutating

    def list_tools(self) -> dict[str, dict[str, Any]]:
        """Return all registered tool names and their schemas.

        Returns:
            Dict mapping tool name → JSON Schema dict. Safe to read; a shallow copy.
        """
        return dict(self._tools)

    def call_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Dispatch a tool call by name with keyword arguments.

        Args:
            name: Registered tool name.
            args: Keyword arguments to pass to the handler.

        Returns:
            Whatever the handler returns.

        Raises:
            ValueError: If tool name is not registered.
            PermissionError: If tool is mutating and server is in read_only mode.
        """
        if name not in self._handlers:
            raise ValueError(f"Unknown tool: {name!r}")

        if self.read_only and self._mutating.get(name, False):
            raise PermissionError(
                f"Tool {name!r} is mutating but server is in read-only mode. "
                f"Use --write to enable writes."
            )

        handler = self._handlers[name]
        return handler(**args)
