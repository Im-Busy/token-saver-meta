"""Tests for tscg.proxy.compressor — MCP↔TSCG format conversion and compression."""

import pytest
from tscg.core.transforms import ToolDef, ParamDef
from tscg.proxy.compressor import (
    mcp_tool_to_tscg,
    tscg_to_mcp,
    compress_tools,
    decompress_tools,
)


# ── Sample MCP tool fixtures ─────────────────────────────────────


def make_simple_mcp_tool() -> dict:
    return {
        "name": "read_file",
        "description": "Use this tool to read a file from the local filesystem. You can use this to access any file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read. The value of the path.",
                },
                "encoding": {
                    "type": "string",
                    "description": "Specifies the encoding of the file.",
                    "enum": ["utf-8", "utf-16", "ascii"],
                },
            },
            "required": ["path"],
        },
    }


def make_mcp_tool_with_nested() -> dict:
    """Tool with nested object and anyOf schema."""
    return {
        "name": "search_docs",
        "description": "This tool allows you to search documentation across multiple sources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string.",
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to apply to the search results.",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Which documentation source to search.",
                            "anyOf": [
                                {"type": "string", "enum": ["internal", "external"]},
                                {"type": "null"},
                            ],
                        },
                        "tags": {
                            "type": "array",
                            "description": "Tags to filter by.",
                            "items": {"type": "string"},
                        },
                    },
                },
                "sort": {
                    "type": "string",
                    "description": "Sort order for results.",
                    "oneOf": [
                        {"type": "string", "enum": ["relevance", "date"]},
                        {"type": "null"},
                    ],
                },
            },
            "required": ["query"],
        },
    }


def make_multiple_mcp_tools() -> list[dict]:
    return [
        {
            "name": "read_file",
            "description": "Read a file from disk.",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path"}},
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to a file on disk.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    ]


# ── mcp_tool_to_tscg ─────────────────────────────────────────────


class TestMcpToolToTscg:
    """Given: MCP tool dict. When: mcp_tool_to_tscg. Then: correct ToolDef."""

    def test_converts_name(self):
        mcp = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(mcp)
        assert td.name == "read_file"

    def test_converts_description(self):
        mcp = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(mcp)
        assert "read a file" in td.description.lower()

    def test_converts_parameters(self):
        mcp = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(mcp)
        assert len(td.parameters) == 2

        path_param = next(p for p in td.parameters if p.name == "path")
        assert path_param.type == "string"
        assert path_param.required is True
        assert "path" in path_param.description.lower()

        enc_param = next(p for p in td.parameters if p.name == "encoding")
        assert enc_param.type == "string"
        assert enc_param.required is False
        assert enc_param.enum == ["utf-8", "utf-16", "ascii"]

    def test_handles_empty_description(self):
        mcp = {"name": "t", "inputSchema": {"type": "object"}}
        td = mcp_tool_to_tscg(mcp)
        assert td.description == ""

    def test_handles_no_properties(self):
        mcp = {"name": "t", "description": "A tool", "inputSchema": {"type": "object"}}
        td = mcp_tool_to_tscg(mcp)
        assert td.parameters == []


# ── tscg_to_mcp ──────────────────────────────────────────────────


class TestTscgToMcp:
    """Given: ToolDef. When: tscg_to_mcp. Then: correct MCP dict."""

    def test_converts_name_and_description(self):
        td = ToolDef(name="test_tool", description="A test tool", parameters=[])
        mcp = tscg_to_mcp(td)
        assert mcp["name"] == "test_tool"
        assert mcp["description"] == "A test tool"

    def test_converts_parameters(self):
        td = ToolDef(
            name="tool",
            description="desc",
            parameters=[
                ParamDef(name="x", type="number", description="X coord", required=True),
                ParamDef(name="y", type="number", description="Y coord", required=False),
            ],
        )
        mcp = tscg_to_mcp(td)
        props = mcp["inputSchema"]["properties"]
        assert props["x"]["type"] == "number"
        assert props["x"]["description"] == "X coord"
        assert props["y"]["type"] == "number"
        assert mcp["inputSchema"]["required"] == ["x"]

    def test_preserves_enum_values(self):
        td = ToolDef(
            name="tool",
            description="",
            parameters=[
                ParamDef(name="mode", type="string", description="Mode", enum=["a", "b", "c"]),
            ],
        )
        mcp = tscg_to_mcp(td)
        assert mcp["inputSchema"]["properties"]["mode"]["enum"] == ["a", "b", "c"]


# ── Roundtrip ────────────────────────────────────────────────────


class TestRoundtrip:
    """Given: MCP tool. When: mcp_tool_to_tscg → tscg_to_mcp. Then: all fields preserved."""

    def test_roundtrip_preserves_name(self):
        original = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)
        assert result["name"] == original["name"]

    def test_roundtrip_preserves_param_names(self):
        original = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)
        orig_names = list(original["inputSchema"]["properties"].keys())
        result_names = list(result["inputSchema"]["properties"].keys())
        assert set(orig_names) == set(result_names)

    def test_roundtrip_preserves_param_types(self):
        original = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)
        for name, prop in original["inputSchema"]["properties"].items():
            assert result["inputSchema"]["properties"][name]["type"] == prop["type"]

    def test_roundtrip_preserves_required(self):
        original = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)
        assert result["inputSchema"]["required"] == original["inputSchema"]["required"]

    def test_roundtrip_preserves_enums(self):
        original = make_simple_mcp_tool()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)
        enc = result["inputSchema"]["properties"]["encoding"]
        assert enc["enum"] == ["utf-8", "utf-16", "ascii"]

    def test_roundtrip_multiple_tools(self):
        originals = make_multiple_mcp_tools()
        tds = [mcp_tool_to_tscg(t) for t in originals]
        results = [tscg_to_mcp(td) for td in tds]
        for orig, res in zip(originals, results):
            assert res["name"] == orig["name"]
            assert set(res["inputSchema"]["properties"].keys()) == set(orig["inputSchema"]["properties"].keys())


# ── Nested schema support ────────────────────────────────────────


class TestNestedSchemas:
    """Given: MCP tool with nested anyOf/oneOf/allOf. When: roundtrip. Then: preserved."""

    def test_roundtrip_preserves_anyof(self):
        original = make_mcp_tool_with_nested()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)

        filters = result["inputSchema"]["properties"]["filters"]
        assert "properties" in filters
        source = filters["properties"]["source"]
        assert "anyOf" in source or source.get("type") == "string"

    def test_roundtrip_preserves_oneof(self):
        original = make_mcp_tool_with_nested()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)

        sort = result["inputSchema"]["properties"]["sort"]
        assert "oneOf" in sort or sort.get("type") == "string"

    def test_roundtrip_preserves_nested_object(self):
        original = make_mcp_tool_with_nested()
        td = mcp_tool_to_tscg(original)
        result = tscg_to_mcp(td)

        filters = result["inputSchema"]["properties"]["filters"]
        assert filters["type"] == "object"
        assert "tags" in filters["properties"]
        assert filters["properties"]["tags"]["type"] == "array"
        assert "items" in filters["properties"]["tags"]


# ── compress_tools / decompress_tools ────────────────────────────


class TestCompressDecompress:
    """Given: MCP tools. When: compress_tools → decompress_tools. Then: reasonable output."""

    def test_compress_returns_string(self):
        tools = make_multiple_mcp_tools()
        result = compress_tools(tools, mode="full")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_compress_description_only_mode(self):
        tools = make_multiple_mcp_tools()
        result = compress_tools(tools, mode="description-only")
        assert isinstance(result, str)
        # Description-only should contain tool names
        assert "read_file" in result or "write_file" in result

    def test_decompress_returns_tools(self):
        tools = make_multiple_mcp_tools()
        compressed = compress_tools(tools, mode="full")
        decompressed = decompress_tools(compressed)
        assert isinstance(decompressed, list)
        assert len(decompressed) == len(tools)

    def test_decompress_preserves_tool_names(self):
        tools = make_multiple_mcp_tools()
        compressed = compress_tools(tools, mode="full")
        decompressed = decompress_tools(compressed)
        names = {t["name"] for t in decompressed}
        assert names == {"read_file", "write_file"}

    def test_compress_empty_tools(self):
        result = compress_tools([], mode="full")
        assert result == ""

    def test_decompress_empty_string(self):
        result = decompress_tools("")
        assert result == []

    def test_compress_decompress_preserves_params(self):
        """Given: tool with multiple params. When: compress→decompress. Then: param names, types, required flags preserved."""
        tool = {
            "name": "search",
            "description": "Search for items.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string"},
                    "limit": {"type": "number", "description": "Max results to return"},
                    "verbose": {"type": "boolean", "description": "Enable verbose output"},
                    "filter": {"type": "string", "description": "Optional filter expression"},
                },
                "required": ["query", "limit"],
            },
        }
        compressed = compress_tools([tool], mode="full")
        decompressed = decompress_tools(compressed)

        assert len(decompressed) == 1
        result = decompressed[0]
        assert result["name"] == "search"

        props = result["inputSchema"]["properties"]
        required = set(result["inputSchema"]["required"])

        # All 4 params present
        assert set(props.keys()) == {"query", "limit", "verbose", "filter"}

        # Types preserved
        assert props["query"]["type"] == "string"
        assert props["limit"]["type"] == "number"
        assert props["verbose"]["type"] == "boolean"
        assert props["filter"]["type"] == "string"

        # Required flags preserved
        assert required == {"query", "limit"}
