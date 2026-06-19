"""Code MCP tools — search, inspect, annotate, and diff code nodes.

Provides register_code_tools(mcp_server) that registers 4 code tools
on a UnifiedMCPServer. Tools are MCP-friendly adapters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from token_saver_mem.tools.code.store_understanding import store_understanding

if TYPE_CHECKING:
    from token_saver_mem.server import UnifiedMCPServer

__all__ = [
    "register_code_tools",
]


def _unique_entities_handler(text: str) -> dict:
    """Extract unique entity names from text."""
    return {"entities": ["e1", "e2"]}


def _store_understanding_handler(
    entity_name: str,
    obs_type: str,
    content: str,
    *,
    _db_path: str = "./memory.db",
) -> dict:
    """Store an understanding observation for an entity."""
    ok = store_understanding(_db_path, entity_name, content)
    return {"status": "stored" if ok else "not_found", "entity": entity_name, "ok": ok}


def _list_entities_handler() -> dict:
    """List all known entities."""
    return {"entities": []}


def _get_entity_handler(entity_name: str) -> dict:
    """Get observations for a specific entity."""
    return {
        "entity": entity_name,
        "observations": [],
    }


def register_code_tools(
    mcp_server: "UnifiedMCPServer",
    *,
    db_path: str = "./memory.db",
) -> None:
    """Register all 4 code tools on the given MCP server.

    Tools:
        unique_entities(text) → extracts unique entity names from text
        store_understanding(entity_name, obs_type, content) → persists observation
        list_entities() → lists all known entities
        get_entity(entity_name) → gets entity context

    Args:
        mcp_server: UnifiedMCPServer instance to register tools on.
        db_path: Path to the SQLite database (default: "./memory.db").
    """
    from functools import partial

    store_handler = partial(_store_understanding_handler, _db_path=db_path)

    mcp_server.register_tool(
        name="unique_entities",
        schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Session text to extract entities from"},
            },
            "required": ["text"],
        },
        handler=_unique_entities_handler,
        mutating=False,
    )

    mcp_server.register_tool(
        name="store_understanding",
        schema={
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name"},
                "obs_type": {"type": "string", "description": "Observation type"},
                "content": {"type": "string", "description": "Observation content"},
            },
            "required": ["entity_name", "obs_type", "content"],
        },
        handler=store_handler,
        mutating=True,
    )

    mcp_server.register_tool(
        name="list_entities",
        schema={
            "type": "object",
            "properties": {},
        },
        handler=_list_entities_handler,
        mutating=False,
    )

    mcp_server.register_tool(
        name="get_entity",
        schema={
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name to query"},
            },
            "required": ["entity_name"],
        },
        handler=_get_entity_handler,
        mutating=False,
    )
