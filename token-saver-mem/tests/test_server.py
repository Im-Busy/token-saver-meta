"""Tests for server.py — UnifiedMCPServer with tool registration, dispatch, read-only guard."""

from __future__ import annotations

import pytest

from token_saver_mem.server import UnifiedMCPServer


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def server() -> UnifiedMCPServer:
    """A fresh server with no tools registered."""
    return UnifiedMCPServer(read_only=True)


@pytest.fixture
def server_writeable() -> UnifiedMCPServer:
    """A server with write mode enabled."""
    return UnifiedMCPServer(read_only=False)


# ── Helpers: sample tool handlers ───────────────────────────────────

def _unique_entities(text: str) -> dict:
    return {"entities": ["e1", "e2"]}


def _store_understanding(entity_name: str, obs_type: str, content: str) -> dict:
    return {"status": "stored", "entity": entity_name}


def _context_pack_handler(session_text: str, budget: str = "auto") -> dict:
    return {"text": "pack", "stats": {}, "hash": "abc123"}


def _noop(**kwargs) -> dict:
    return {"ok": True}


# ── Tests: register_tool ────────────────────────────────────────────

class TestRegisterTool:
    """register_tool(name, schema, handler, mutating=False)."""

    def test_register_single_tool(self, server: UnifiedMCPServer) -> None:
        """Given a server, When a tool is registered, Then it appears in list_tools."""
        server.register_tool(
            name="unique_entities",
            schema={"type": "object", "properties": {"text": {"type": "string"}}},
            handler=_unique_entities,
        )
        tools = server.list_tools()
        assert "unique_entities" in tools

    def test_register_multiple_tools(self, server: UnifiedMCPServer) -> None:
        """Given a server, When multiple tools registered, Then all appear in list."""
        server.register_tool("tool_a", {}, _noop)
        server.register_tool("tool_b", {}, _noop)
        server.register_tool("tool_c", {}, _noop)
        tools = server.list_tools()
        assert len(tools) >= 3

    def test_register_tool_with_schema(self, server: UnifiedMCPServer) -> None:
        """Given a tool with schema, When registered, Then schema is stored."""
        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Input text"},
            },
            "required": ["text"],
        }
        server.register_tool("my_tool", schema, _noop)
        tools = server.list_tools()
        assert tools["my_tool"] == schema

    def test_register_tool_overwrites_existing(self, server: UnifiedMCPServer) -> None:
        """Given a server with tool X, When X is re-registered, Then overwrites."""
        server.register_tool("dup", {"old": True}, _noop)
        server.register_tool("dup", {"new": True}, _noop)
        tools = server.list_tools()
        assert tools["dup"] == {"new": True}


# ── Tests: list_tools ───────────────────────────────────────────────

class TestListTools:
    """list_tools() returns dict of name → schema."""

    def test_empty_server_returns_empty_dict(self, server: UnifiedMCPServer) -> None:
        """Given empty server, When list_tools called, Then returns empty dict."""
        assert server.list_tools() == {}

    def test_returns_dict_of_names_to_schemas(self, server: UnifiedMCPServer) -> None:
        """Given registered tools, When list_tools called, Then returns name→schema mapping."""
        server.register_tool("a", {"p": "int"}, _noop)
        server.register_tool("b", {"p": "str"}, _noop)
        result = server.list_tools()
        assert isinstance(result, dict)
        assert result == {"a": {"p": "int"}, "b": {"p": "str"}}

    def test_list_tools_is_not_mutated_by_caller(self, server: UnifiedMCPServer) -> None:
        """Given server with tools, When caller modifies returned dict, Then server unchanged."""
        server.register_tool("safe", {"x": 1}, _noop)
        result = server.list_tools()
        result["injected"] = {"bad": True}
        assert "injected" not in server.list_tools()


# ── Tests: call_tool ────────────────────────────────────────────────

class TestCallTool:
    """call_tool(name, args) dispatches to handler."""

    def test_call_registered_tool(self, server: UnifiedMCPServer) -> None:
        """Given registered tool, When called, Then returns handler result."""
        server.register_tool(
            "unique_entities",
            {"properties": {"text": {"type": "string"}}},
            _unique_entities,
        )
        result = server.call_tool("unique_entities", {"text": "foo bar baz"})
        assert result == {"entities": ["e1", "e2"]}

    def test_call_tool_with_kwargs(self, server: UnifiedMCPServer) -> None:
        """Given tool with kwargs, When called, Then handler receives kwargs."""
        calls: list[dict] = []

        def track(**kwargs) -> dict:
            calls.append(kwargs)
            return {"tracked": True}

        server.register_tool("tracker", {"properties": {"x": {"type": "int"}}}, track)
        result = server.call_tool("tracker", {"x": 42, "y": "hello"})
        assert result == {"tracked": True}
        assert calls[0] == {"x": 42, "y": "hello"}

    def test_call_unknown_tool_raises(self, server: UnifiedMCPServer) -> None:
        """Given unknown tool name, When called, Then raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            server.call_tool("nonexistent", {})

    def test_call_with_no_args(self, server: UnifiedMCPServer) -> None:
        """Given tool with no required args, When called with empty dict, Then succeeds."""
        server.register_tool("noop", {}, _noop)
        result = server.call_tool("noop", {})
        assert result == {"ok": True}


# ── Tests: read_only guard ──────────────────────────────────────────

class TestReadOnlyGuard:
    """Read-only mode blocks mutating tools."""

    def test_read_only_blocks_mutating(self, server: UnifiedMCPServer) -> None:
        """Given read_only=True, When mutating tool called, Then raises PermissionError."""
        server.register_tool(
            "store_understanding",
            {},
            _store_understanding,
            mutating=True,
        )
        with pytest.raises(PermissionError, match="read-only"):
            server.call_tool("store_understanding", {
                "entity_name": "e1", "obs_type": "TODO", "content": "test"
            })

    def test_read_only_allows_non_mutating(self, server: UnifiedMCPServer) -> None:
        """Given read_only=True, When non-mutating tool called, Then succeeds."""
        server.register_tool("unique_entities", {}, _unique_entities, mutating=False)
        result = server.call_tool("unique_entities", {"text": "test"})
        assert "entities" in result

    def test_write_mode_allows_mutating(self, server_writeable: UnifiedMCPServer) -> None:
        """Given read_only=False, When mutating tool called, Then succeeds."""
        server_writeable.register_tool(
            "store_understanding",
            {},
            _store_understanding,
            mutating=True,
        )
        result = server_writeable.call_tool("store_understanding", {
            "entity_name": "e1", "obs_type": "TODO", "content": "test"
        })
        assert result["status"] == "stored"

    def test_non_mutating_by_default(self, server: UnifiedMCPServer) -> None:
        """Given tool registered without mutating flag, When called, Then allowed in read-only."""
        server.register_tool("ctx_pack", {}, _context_pack_handler)
        # Should not raise PermissionError
        result = server.call_tool("ctx_pack", {"session_text": "hello"})
        assert "text" in result


# ── Tests: full server tool registration ────────────────────────────

class TestFullServer:
    """Integration: register all 8-10 tools."""

    def test_all_tools_registered(self, server: UnifiedMCPServer) -> None:
        """Given a server with all tools registered, When list_tools called, Then 8+ tools present."""
        from token_saver_mem.tools.code import register_code_tools
        from token_saver_mem.tools.session import register_session_tools

        register_code_tools(server)
        register_session_tools(server)

        tools = server.list_tools()
        assert len(tools) >= 8, f"Expected 8+ tools, got {len(tools)}"

    def test_session_tools_present(self, server: UnifiedMCPServer) -> None:
        """Given registered tools, When list_tools called, Then session tools are present."""
        from token_saver_mem.tools.session import register_session_tools

        register_session_tools(server)
        tools = server.list_tools()
        assert "context_pack" in tools
        assert "bootstrap_context" in tools
        assert "open_work" in tools
        assert "completion_check" in tools

    def test_code_tools_present(self, server: UnifiedMCPServer) -> None:
        """Given registered tools, When list_tools called, Then code tools are present."""
        from token_saver_mem.tools.code import register_code_tools

        register_code_tools(server)
        tools = server.list_tools()
        expected_code_tools = [
            "unique_entities",
            "store_understanding",
            "list_entities",
            "get_entity",
        ]
        for t in expected_code_tools:
            assert t in tools, f"Missing code tool: {t}"
