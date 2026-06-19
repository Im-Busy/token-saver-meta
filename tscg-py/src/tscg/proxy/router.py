"""
Tool router — maps tool names to downstream server URLs.

Supports wildcard patterns for flexible tool routing.
Exact matches take precedence over wildcard matches.
"""

from __future__ import annotations

import fnmatch
import re
from typing import Optional


class ToolRouter:
    """Maps tool names to their originating downstream server URL.

    Supports:
        - Exact tool name mapping
        - Wildcard patterns (fnmatch-style: ``file_*``, ``*_db``, ``api_*_v2``)
        - Exact matches take priority over wildcard matches
    """

    def __init__(self) -> None:
        self._exact: dict[str, str] = {}           # tool_name → url
        self._wildcard: list[tuple[str, str]] = []  # (pattern, url)
        self._server_tools: dict[str, set[str]] = {}  # server_name → {tool_patterns}
        self._server_urls: dict[str, str] = {}       # server_name → url
        self._server_wildcards: dict[str, set[str]] = {}  # server_name → {wildcard_patterns}

    # ── Registration ─────────────────────────────────────────────

    def add_server(self, name: str, url: str, tools: list[str]) -> None:
        """Register a server with its tool names or wildcard patterns.

        Args:
            name: Server identifier.
            url: Downstream URL for this server.
            tools: List of tool names. Names containing ``*`` are
                   treated as fnmatch wildcard patterns.

        Wildcard examples:
            ``"file_*"`` matches ``file_read``, ``file_write``, etc.
            ``"*_db"`` matches ``query_db``, ``migrate_db``, etc.
        """
        # Remove previous registration for this server (if re-adding)
        self.remove_server(name)

        self._server_urls[name] = url
        self._server_wildcards[name] = set()
        all_patterns: set[str] = set()

        for tool_pattern in tools:
            all_patterns.add(tool_pattern)
            if self._is_wildcard(tool_pattern):
                self._wildcard.append((tool_pattern, url))
                self._server_wildcards[name].add(tool_pattern)
            else:
                self._exact[tool_pattern] = url

        self._server_tools[name] = all_patterns

    # ── Lookup ───────────────────────────────────────────────────

    def route(self, tool_name: str) -> Optional[str]:
        """Determine which server URL handles a tool name.

        Exact matches take priority over wildcard matches.
        Among wildcards, the first registered match wins.

        Args:
            tool_name: The tool name to look up.

        Returns:
            Server URL string, or None if no match.
        """
        # Exact match first
        if tool_name in self._exact:
            return self._exact[tool_name]

        # Wildcard match
        for pattern, url in self._wildcard:
            if fnmatch.fnmatch(tool_name, pattern):
                return url

        return None

    # ── Removal ──────────────────────────────────────────────────

    def remove_server(self, name: str) -> None:
        """Remove a server and all its tool registrations.

        Args:
            name: Server identifier. No-op if not registered.
        """
        if name not in self._server_tools:
            return

        # Remove exact matches
        for tool_pattern in self._server_tools[name]:
            if not self._is_wildcard(tool_pattern):
                self._exact.pop(tool_pattern, None)

        # Remove wildcard entries
        wildcards = self._server_wildcards.get(name, set())
        self._wildcard = [
            (p, u) for p, u in self._wildcard
            if p not in wildcards or u != self._server_urls.get(name)
        ]

        self._server_tools.pop(name, None)
        self._server_urls.pop(name, None)
        self._server_wildcards.pop(name, None)

    # ── Introspection ────────────────────────────────────────────

    def list_servers(self) -> list[str]:
        """Return all registered server names."""
        return list(self._server_tools.keys())

    def list_tools(self) -> list[str]:
        """Return all registered tool names/patterns across all servers."""
        result: list[str] = []
        for patterns in self._server_tools.values():
            result.extend(patterns)
        return result

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _is_wildcard(pattern: str) -> bool:
        return "*" in pattern
