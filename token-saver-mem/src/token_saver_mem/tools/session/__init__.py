"""Session MCP tools — context pack, bootstrap, open work, completion check.

Provides the register_session_tools(mcp_server) function that registers
all 4 session tools on a UnifiedMCPServer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from token_saver_mem.server import UnifiedMCPServer

from .bootstrap_context import bootstrap_context_tool
from .completion_check import completion_check_tool
from .context_pack import context_pack_tool
from .open_work import open_work_tool

__all__ = [
    "bootstrap_context_tool",
    "completion_check_tool",
    "context_pack_tool",
    "open_work_tool",
    "register_session_tools",
]


def register_session_tools(mcp_server: "UnifiedMCPServer") -> None:
    """Register all 4 session tools on the given MCP server.

    Tools:
        context_pack(session_text, budget="auto") → {text, stats, hash}
        bootstrap_context(session_text, project_path=None) → {scope, context_pack}
        open_work(session_text) → {pending, blockers, has_open_work}
        completion_check(session_text) → {done, pending, blockers}
    """
    mcp_server.register_tool(
        name="context_pack",
        schema={
            "type": "object",
            "properties": {
                "session_text": {
                    "type": "string",
                    "description": "Raw agent session/conversation text",
                },
                "budget": {
                    "type": "string",
                    "enum": ["micro", "normal", "full", "auto"],
                    "description": "Budget tier for context pack size",
                    "default": "auto",
                },
            },
            "required": ["session_text"],
        },
        handler=context_pack_tool,
        mutating=False,
    )

    mcp_server.register_tool(
        name="bootstrap_context",
        schema={
            "type": "object",
            "properties": {
                "session_text": {
                    "type": "string",
                    "description": "Raw agent session/conversation text",
                },
                "project_path": {
                    "type": "string",
                    "description": "Optional path to project root for filesystem scope",
                },
            },
            "required": ["session_text"],
        },
        handler=bootstrap_context_tool,
        mutating=False,
    )

    mcp_server.register_tool(
        name="open_work",
        schema={
            "type": "object",
            "properties": {
                "session_text": {
                    "type": "string",
                    "description": "Raw agent session/conversation text",
                },
            },
            "required": ["session_text"],
        },
        handler=open_work_tool,
        mutating=False,
    )

    mcp_server.register_tool(
        name="completion_check",
        schema={
            "type": "object",
            "properties": {
                "session_text": {
                    "type": "string",
                    "description": "Raw agent session/conversation text",
                },
            },
            "required": ["session_text"],
        },
        handler=completion_check_tool,
        mutating=False,
    )
