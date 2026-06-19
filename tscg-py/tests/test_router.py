"""Tests for tscg.proxy.router — tool registration, routing, wildcard matching."""

import pytest
from tscg.proxy.router import ToolRouter


class TestAddLookup:
    """Given: ToolRouter. When: add_server then route. Then: correct mapping."""

    def test_route_returns_correct_url(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["read_file", "write_file", "list_dir"])
        assert router.route("read_file") == "http://fs:3000/mcp"
        assert router.route("write_file") == "http://fs:3000/mcp"
        assert router.route("list_dir") == "http://fs:3000/mcp"

    def test_unknown_tool_returns_none(self):
        router = ToolRouter()
        assert router.route("nonexistent") is None

    def test_multiple_servers(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["read_file"])
        router.add_server("db", "http://db:3000/mcp", tools=["query_db"])
        assert router.route("read_file") == "http://fs:3000/mcp"
        assert router.route("query_db") == "http://db:3000/mcp"


class TestRemove:
    """Given: ToolRouter with servers. When: remove_server. Then: tools unregistered."""

    def test_remove_clears_tools(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["read_file", "write_file"])
        router.remove_server("fs")
        assert router.route("read_file") is None
        assert router.route("write_file") is None

    def test_remove_only_target_server(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["read_file"])
        router.add_server("db", "http://db:3000/mcp", tools=["query_db"])
        router.remove_server("fs")
        assert router.route("read_file") is None
        assert router.route("query_db") == "http://db:3000/mcp"

    def test_remove_nonexistent_server_no_error(self):
        router = ToolRouter()
        router.remove_server("ghost")  # no error


class TestWildcard:
    """Given: ToolRouter with wildcard pattern. When: route. Then: match."""

    def test_wildcard_prefix_match(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["file_*"])
        assert router.route("file_read") == "http://fs:3000/mcp"
        assert router.route("file_write") == "http://fs:3000/mcp"
        assert router.route("file_delete") == "http://fs:3000/mcp"

    def test_wildcard_suffix_match(self):
        router = ToolRouter()
        router.add_server("db", "http://db:3000/mcp", tools=["*_db"])
        assert router.route("query_db") == "http://db:3000/mcp"
        assert router.route("migrate_db") == "http://db:3000/mcp"

    def test_wildcard_middle_match(self):
        router = ToolRouter()
        router.add_server("api", "http://api:3000/mcp", tools=["api_*_v2"])
        assert router.route("api_user_v2") == "http://api:3000/mcp"
        assert router.route("api_order_v2") == "http://api:3000/mcp"

    def test_exact_match_wins_over_wildcard(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["file_*"])
        router.add_server("special", "http://special:3000/mcp", tools=["file_important"])
        assert router.route("file_important") == "http://special:3000/mcp"
        assert router.route("file_read") == "http://fs:3000/mcp"

    def test_wildcard_remove_clears(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["file_*"])
        router.remove_server("fs")
        assert router.route("file_anything") is None


class TestOverwrite:
    """Given: server with tools. When: same tool re-registered. Then: last wins."""

    def test_re_add_overwrites(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["read_file"])
        router.add_server("fs2", "http://fs2:3000/mcp", tools=["read_file"])
        assert router.route("read_file") == "http://fs2:3000/mcp"


class TestListServers:
    """Given: ToolRouter. When: list_servers. Then: return server names."""

    def test_list_servers(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["a"])
        router.add_server("db", "http://db:3000/mcp", tools=["b"])
        servers = router.list_servers()
        assert set(servers) == {"fs", "db"}

    def test_list_tools(self):
        router = ToolRouter()
        router.add_server("fs", "http://fs:3000/mcp", tools=["a", "b", "c"])
        tools = router.list_tools()
        assert set(tools) == {"a", "b", "c"}
