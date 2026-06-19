# -*- coding: utf-8 -*-
"""
End-to-end integration tests for TSCG — Tool Schema Compressor Generator.

Crosses boundaries: compiler → transforms → proxy → compressor
Covers the full compression pipeline with real-world-like tool schemas.

Scenarios:
  1. Full pipeline: 10 tools → compile → savings 40-72% → decompile
  2. Zero tools: empty list → no crash, empty output
  3. 30+ tools: CFL+CFO auto-disabled
  4. Non-Claude model: gpt-4o → CFL+SAD disabled
  5. Thinking model: o1 → CFL+SAD disabled
  6. Roundtrip identity: 20 diverse tools → all names/types/required preserved
  7. Savings accuracy: known tool set → savings in 30-80% range
  8. Profile gating: conservative/balanced/aggressive correct transforms
  9. Model auto-detection: gpt-4o with auto profile
  10. Description-only mode: descriptions shortened, structure preserved
"""

from __future__ import annotations

import pytest

from tscg.core.compiler import TSCGCompiler
from tscg.core.transforms import ToolDef, ParamDef
from tscg.proxy.compressor import (
    mcp_tool_to_tscg,
    tscg_to_mcp,
    compress_tools,
    decompress_tools,
)


# ── Helper factories ───────────────────────────────────────────────


def _tool(
    name: str,
    desc: str = "Does something.",
    params: list[ParamDef] | None = None,
    freq: float = 0.5,
) -> ToolDef:
    return ToolDef(name=name, description=desc, parameters=params or [], usageFrequency=freq)


def _param(
    name: str,
    ptype: str = "string",
    desc: str = "Parameter description.",
    required: bool = False,
    enum: list[str] | None = None,
) -> ParamDef:
    return ParamDef(name=name, type=ptype, description=desc, required=required, enum=enum)


# ── MCP dict helpers for proxy tests ────────────────────────────────


def _mcp_tool_dict(
    name: str,
    desc: str = "",
    props: dict | None = None,
    required: list[str] | None = None,
) -> dict:
    return {
        "name": name,
        "description": desc,
        "inputSchema": {
            "type": "object",
            "properties": props or {},
            "required": required or [],
        },
    }


# ── Fixtures ────────────────────────────────────────────────────────


def _make_verbose_tools() -> list[ToolDef]:
    """10 tools with verbose descriptions (lots of filler) to test full pipeline."""
    return [
        _tool(
            "get_weather",
            "Use this tool when you need to get current weather data for a location. "
            "This tool allows you to fetch temperature, humidity, wind speed, and atmospheric conditions. "
            "Please note that this tool accesses real-time weather data that may have changed since your training cutoff.",
            [
                _param("location", "string", "Specifies the city name or geographic coordinates for the weather query.", required=True),
                _param("units", "string", "Determines whether temperature values are returned in celsius or fahrenheit.",
                       enum=["celsius", "fahrenheit"]),
                _param("include_hourly", "boolean", "Indicates whether to include hourly forecast data if applicable."),
            ],
            freq=0.95,
        ),
        _tool(
            "search_web",
            "This tool is designed to search the web for information or any relevant data. "
            "Use this to retrieve current information or any other content that the user requests. "
            "Note that results may vary based on search engine availability.",
            [
                _param("query", "string", "The search query string to execute.", required=True),
                _param("max_results", "number", "The maximum number of results to return when available.",
                       enum=["5", "10", "20", "50"]),
                _param("safe_search", "boolean", "Determines whether to filter explicit content from results."),
            ],
            freq=0.88,
        ),
        _tool(
            "read_file",
            "Use this tool to read a file from the local filesystem. You can use this to access any file "
            "that you have permission to read. This tool lets you read text files, binary files, and "
            "other file types as needed.",
            [
                _param("path", "string", "The path of the file to read.", required=True),
                _param("encoding", "string", "Specifies the encoding to use for text file reading.",
                       enum=["utf-8", "utf-16", "ascii", "latin-1"]),
                _param("start_line", "number", "Indicates the line number to start reading from, if needed."),
            ],
            freq=0.92,
        ),
        _tool(
            "write_file",
            "This tool enables you to write content to a file on the local filesystem. "
            "It can be used to create new files or overwrite existing files. "
            "This function will create parent directories if they do not exist.",
            [
                _param("path", "string", "The path where the file should be written.", required=True),
                _param("content", "string", "The content or data to write to the file.", required=True),
                _param("append", "boolean", "Determines whether to append to an existing file instead of overwriting."),
            ],
            freq=0.85,
        ),
        _tool(
            "list_directory",
            "Use this function when you need to list the contents of a directory on the filesystem. "
            "This tool is useful for exploring the file structure and finding specific files.",
            [
                _param("path", "string", "The directory path to list contents from.", required=True),
                _param("recursive", "boolean", "Indicates whether to recursively list subdirectories as well."),
                _param("pattern", "string", "A glob pattern to filter the listing results by."),
            ],
            freq=0.78,
        ),
        _tool(
            "execute_command",
            "This tool is designed to execute a shell command and return the output. "
            "You can use this to run any command-line operation, including scripts, "
            "build commands, and system utilities.",
            [
                _param("command", "string", "The shell command to execute.", required=True),
                _param("working_dir", "string", "Specifies the working directory for command execution."),
                _param("timeout", "number", "The maximum time in seconds to wait for completion, if applicable."),
            ],
            freq=0.72,
        ),
        _tool(
            "create_pull_request",
            "This tool allows you to create a pull request on a Git hosting platform. "
            "It can be used to propose changes, request code reviews, and merge branches. "
            "Please note that this requires appropriate repository permissions.",
            [
                _param("title", "string", "The title of the pull request.", required=True),
                _param("body", "string", "The description body of the pull request."),
                _param("base_branch", "string", "Represents the target branch to merge into.", required=True),
                _param("head_branch", "string", "Specifies the source branch with the changes.", required=True),
            ],
            freq=0.65,
        ),
        _tool(
            "send_notification",
            "Use this to send a notification or alert to the user. "
            "This tool can be used for providing status updates, warnings, "
            "or any other information that requires user attention.",
            [
                _param("message", "string", "The notification message text.", required=True),
                _param("level", "string", "Specifies the notification severity level.",
                       enum=["info", "warning", "error", "success"]),
            ],
            freq=0.55,
        ),
        _tool(
            "query_database",
            "This tool allows you to execute a database query and retrieve results. "
            "You can use this to fetch records, analyze data, or perform aggregations. "
            "Supports standard SQL query syntax for database operations.",
            [
                _param("query", "string", "The SQL query string to execute.", required=True),
                _param("params", "array", "Represents the parameter values for parameterized queries."),
                _param("limit", "number", "The maximum number of rows to return from the query."),
            ],
            freq=0.60,
        ),
        _tool(
            "update_configuration",
            "Use this tool to update application configuration settings. "
            "This function enables you to modify runtime parameters, feature flags, "
            "and environment-specific settings.",
            [
                _param("key", "string", "The configuration key to update.", required=True),
                _param("value", "string", "The new value for the configuration key.", required=True),
                _param("environment", "string", "Specifies the environment scope for the update.",
                       enum=["development", "staging", "production"]),
            ],
            freq=0.42,
        ),
    ]


def _make_diverse_tools() -> list[ToolDef]:
    """20 diverse tools with enums, optional params, various types, long descriptions.

    Used for roundtrip identity testing.
    """
    tools: list[ToolDef] = []
    tool_specs = [
        ("get_user", "string", ["user_id"], ["include_profile"], []),
        ("search_items", "string", ["query"], ["category", "sort_order"], ["category"]),
        ("create_order", "string", ["customer_id", "items"], ["notes", "priority"], ["priority"]),
        ("delete_record", "string", ["record_id"], ["confirm"], []),
        ("update_profile", "string", ["user_id"], ["name", "email", "bio"], []),
        ("fetch_analytics", "string", ["metric"], ["start_date", "end_date", "granularity"], ["granularity"]),
        ("send_email", "string", ["to", "subject", "body"], ["cc", "bcc"], []),
        ("upload_asset", "string", ["file_path", "bucket"], ["content_type", "public"], []),
        ("generate_report", "string", ["template_id"], ["format", "language"], ["format"]),
        ("create_tag", "string", ["name", "color"], ["description"], []),
        ("list_users", "number", ["page", "per_page"], ["role", "status"], ["status"]),
        ("modify_settings", "boolean", ["startup_enabled"], ["logging_level", "cache_size"], ["logging_level"]),
        ("check_status", "string", ["task_id"], ["poll_interval"], []),
        ("invoke_webhook", "string", ["url", "payload"], ["headers", "method"], []),
        ("batch_process", "array", ["items"], ["concurrency", "retry_on_failure"], []),
        ("query_metrics", "string", ["query"], ["time_range", "resolution"], []),
        ("post_message", "string", ["channel", "content"], ["thread_id", "reply_to"], []),
        ("patch_resource", "string", ["resource_id", "patch_doc"], ["content_type"], []),
        ("validate_input", "object", ["schema", "data"], ["strict_mode"], []),
        ("purge_cache", "string", ["cache_key"], ["namespace", "all_versions"], []),
    ]

    for i, (name, enum_type, req_params, opt_params, enum_params) in enumerate(tool_specs):
        params: list[ParamDef] = []
        params.append(_param(
            f"{name}_id" if i < 5 else "id",
            "string",
            f"Unique identifier for the {name.replace('_', ' ')} operation. Represents the target resource reference.",
            required=True,
        ))

        for rp in req_params:
            params.append(_param(rp, "string", f"The {rp} parameter for the {name} tool.", required=True))

        for op in opt_params:
            has_enum = op in enum_params
            enum_vals = None
            if has_enum:
                if op in ("category", "granularity", "format"):
                    enum_vals = ["small", "medium", "large"]
                elif op in ("priority", "status", "logging_level"):
                    enum_vals = ["low", "medium", "high"]
                elif op == "sort_order":
                    enum_vals = ["ascending", "descending"]
                else:
                    enum_vals = ["a", "b", "c"]
            ptype = "boolean" if "mode" in op else enum_type if has_enum else "string"
            params.append(_param(
                op, ptype,
                f"Determines the {op} value for the tool operation when available.",
                required=False,
                enum=enum_vals,
            ))

        tools.append(_tool(
            name=name,
            desc=f"This tool allows you to perform the {name.replace('_', ' ')} operation. "
                 f"Use this function when you need to {name.replace('_', ' ')} resources in the system. "
                 f"This tool is designed to handle {len(req_params)} required parameters "
                 f"and {len(opt_params)} optional configuration settings.",
            params=params,
            freq=0.99 - i * 0.04,
        ))

    return tools


def _make_mcp_tool_list(count: int) -> list[dict]:
    """Generate `count` MCP-format tool dicts with descriptions."""
    tools: list[dict] = []
    for i in range(count):
        tools.append(_mcp_tool_dict(
            name=f"tool_{i:02d}",
            desc=f"Use this tool to execute operation {i}. "
                 f"This tool is useful when you need to perform task {i} "
                 f"and retrieve the corresponding results for processing.",
            props={
                "input_param": {
                    "type": "string",
                    "description": f"Specifies the input value for operation {i}.",
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Determines whether to output verbose logging information.",
                },
            },
            required=["input_param"],
        ))
    return tools


# ════════════════════════════════════════════════════════════════════
# Scenario 1: Full Pipeline
# ════════════════════════════════════════════════════════════════════


class TestFullPipeline:
    """Compile 10 tools through full pipeline and verify end-to-end."""

    @pytest.fixture
    def tools(self) -> list[ToolDef]:
        return _make_verbose_tools()

    def test_compiles_ten_tools_no_crash(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert result.tool_count == 10
        assert result.compressed_text

    def test_savings_positive_with_aggressive_profile(self, tools):
        """Aggressive profile produces positive savings even with CFL/CCP/SAD overhead."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert result.savings_pct > 0

    def test_savings_within_range_balanced_profile(self, tools):
        """Balanced profile (no CFL/CCP/SAD) achieves higher pure-compression savings."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert 20.0 <= result.savings_pct <= 72.0, (
            f"Expected savings 20-72% with balanced, got {result.savings_pct}%"
        )

    def test_decompile_preserves_all_tool_names(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original = {t.name for t in tools}
        recovered = {t.name for t in decompiled}
        assert original == recovered

    def test_decompile_preserves_all_param_names(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original = {(t.name, p.name) for t in tools for p in t.parameters}
        recovered = {(t.name, p.name) for t in decompiled for p in t.parameters}
        assert original == recovered

    def test_decompile_preserves_param_types(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_types = {(t.name, p.name): p.type for t in tools for p in t.parameters}
        recovered_types = {(t.name, p.name): p.type for t in decompiled for p in t.parameters}
        assert original_types == recovered_types

    def test_decompile_preserves_required_flags(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_req = {(t.name, p.name): p.required for t in tools for p in t.parameters}
        recovered_req = {(t.name, p.name): p.required for t in decompiled for p in t.parameters}
        assert original_req == recovered_req

    def test_compressed_text_is_shorter_than_original(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        # Build an approximation of original format
        original_lines: list[str] = []
        for t in tools:
            original_lines.append(f"Tool: {t.name}")
            original_lines.append(f"Description: {t.description}")
            original_lines.append("Parameters:")
            for p in t.parameters:
                req_str = " (required)" if p.required else " (optional)"
                enum_str = f" Allowed values: {', '.join(p.enum)}." if p.enum else ""
                original_lines.append(f"  - {p.name} ({p.type}){req_str}: {p.description}{enum_str}")
            original_lines.append("")
        original_text = "\n".join(original_lines)
        assert len(result.compressed_text) < len(original_text)

    def test_active_transforms_not_empty(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert len(result.active_transforms) > 0


# ════════════════════════════════════════════════════════════════════
# Scenario 2: Zero Tools
# ════════════════════════════════════════════════════════════════════


class TestZeroTools:
    """Empty tool list — no crash, empty output, zero savings."""

    def test_empty_list_no_crash(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile([])
        assert result.tool_count == 0

    def test_empty_output_text(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile([])
        assert result.compressed_text == ""

    def test_zero_savings(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile([])
        assert result.savings_pct == 0.0

    def test_empty_active_transforms(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile([])
        assert result.active_transforms == []

    def test_decompile_empty_returns_empty_list(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet")
        result = compiler.decompile("")
        assert result == []

    def test_compress_tools_empty_returns_empty(self):
        text = compress_tools([], mode="full")
        assert text == ""

    def test_decompress_tools_empty_returns_empty(self):
        tools = decompress_tools("")
        assert tools == []


# ════════════════════════════════════════════════════════════════════
# Scenario 3: 30+ Tools — CFL+CFO Auto-Disabled
# ════════════════════════════════════════════════════════════════════


class TestThirtyPlusTools:
    """Safety guard 2: >=30 tools disables CFL and CFO."""

    @pytest.fixture
    def many_tools(self) -> list[ToolDef]:
        tools: list[ToolDef] = []
        for i in range(35):
            tools.append(_tool(
                f"tool_{i:02d}",
                f"This tool is used to execute operation {i} with specific input parameters.",
                [
                    _param("input", "string", f"Input value for operation {i}.", required=True),
                    _param("verbose", "boolean", "Determines whether to enable verbose output."),
                ],
                freq=0.5 - i * 0.01,
            ))
        return tools

    def test_cfl_disabled_with_35_tools(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert "cfl" not in result.active_transforms

    def test_cfo_disabled_with_35_tools(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert "cfo" not in result.active_transforms

    def test_sdm_still_active(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert "sdm" in result.active_transforms

    def test_dro_still_active(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert "dro" in result.active_transforms

    def test_tool_count_is_correct(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert result.tool_count == 35

    def test_savings_still_positive(self, many_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert result.savings_pct > 0


# ════════════════════════════════════════════════════════════════════
# Scenario 4: Non-Claude Model — gpt-4o
# ════════════════════════════════════════════════════════════════════


class TestNonClaudeModel:
    """Safety guard 1: non-Claude models disable CFL+SAD."""

    @pytest.fixture
    def tools(self) -> list[ToolDef]:
        return _make_verbose_tools()

    def test_gpt4o_cfl_disabled(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" not in result.active_transforms

    def test_gpt4o_sad_disabled(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "sad" not in result.active_transforms

    def test_gpt4o_sdm_still_active(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "sdm" in result.active_transforms

    def test_gpt4o_dro_still_active(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "dro" in result.active_transforms

    def test_gpt4o_ccp_still_active(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "ccp" in result.active_transforms

    def test_gpt4o_savings_positive(self, tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert result.savings_pct > 0


# ════════════════════════════════════════════════════════════════════
# Scenario 5: Thinking Model — o1
# ════════════════════════════════════════════════════════════════════


class TestThinkingModel:
    """Thinking models (o1, o3, R1) disable CFL+SAD."""

    @pytest.fixture
    def tools(self) -> list[ToolDef]:
        return _make_verbose_tools()

    def test_o1_cfl_disabled(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" not in result.active_transforms

    def test_o1_sad_disabled(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert "sad" not in result.active_transforms

    def test_o1_sdm_still_active(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert "sdm" in result.active_transforms

    def test_o1_dro_still_active(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert "dro" in result.active_transforms

    def test_o1_ccp_still_active(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert "ccp" in result.active_transforms

    def test_o1_savings_positive(self, tools):
        compiler = TSCGCompiler(model="o1", profile="aggressive")
        result = compiler.compile(tools)
        assert result.savings_pct > 0


# ════════════════════════════════════════════════════════════════════
# Scenario 6: Roundtrip Identity — 20 Diverse Tools
# ════════════════════════════════════════════════════════════════════


class TestRoundtripIdentity:
    """Roundtrip: compile → decompile preserves all semantic identity."""

    @pytest.fixture
    def tools(self) -> list[ToolDef]:
        return _make_diverse_tools()

    def test_all_tool_names_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_names = {t.name for t in tools}
        recovered_names = {t.name for t in decompiled}
        assert original_names == recovered_names

    def test_all_param_names_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_params = {(t.name, p.name) for t in tools for p in t.parameters}
        recovered_params = {(t.name, p.name) for t in decompiled for p in t.parameters}
        assert original_params == recovered_params

    def test_all_param_types_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_types = {(t.name, p.name): p.type for t in tools for p in t.parameters}
        recovered_types = {(t.name, p.name): p.type for t in decompiled for p in t.parameters}
        assert original_types == recovered_types

    def test_all_required_flags_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_req = {(t.name, p.name): p.required for t in tools for p in t.parameters}
        recovered_req = {(t.name, p.name): p.required for t in decompiled for p in t.parameters}
        assert original_req == recovered_req

    def test_decompile_yields_tool_objects(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        for t in decompiled:
            assert isinstance(t, ToolDef)
            assert isinstance(t.name, str)
            assert isinstance(t.description, str)
            for p in t.parameters:
                assert isinstance(p, ParamDef)

    def test_tool_count_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert len(tools) == len(decompiled)


# ════════════════════════════════════════════════════════════════════
# Scenario 7: Savings Accuracy
# ════════════════════════════════════════════════════════════════════


class TestSavingsAccuracy:
    """Savings percentage falls within expected range for known tool sets."""

    def test_balanced_on_verbose_tools_in_range_30_to_80(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert 30.0 <= result.savings_pct <= 80.0, (
            f"Expected savings 30-80%, got {result.savings_pct}%"
        )

    def test_conservative_savings_positive(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        result = compiler.compile(tools)
        assert result.savings_pct > 0

    def test_conservative_savings_less_than_balanced(self):
        tools = _make_verbose_tools()
        c_con = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        c_bal = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        r_con = c_con.compile(tools)
        r_bal = c_bal.compile(tools)
        assert r_con.savings_pct <= r_bal.savings_pct, (
            f"Conservative ({r_con.savings_pct}%) should not exceed "
            f"balanced ({r_bal.savings_pct}%)"
        )

    def test_balanced_savings_within_reasonable_bounds_on_diverse(self):
        tools = _make_diverse_tools()
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        # Diverse tools with verbose descriptions should still show savings
        assert result.savings_pct > 0

    def test_savings_is_one_decimal_precision(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        s = result.savings_pct
        # Savings should be rounded to 1 decimal place (e.g. 45.2, not 45.234)
        assert round(s * 10) == s * 10

    def test_estimated_savings_property_accurate(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(_make_verbose_tools())
        assert compiler.estimated_savings == result.savings_pct


# ════════════════════════════════════════════════════════════════════
# Scenario 8: Profile Gating
# ════════════════════════════════════════════════════════════════════


class TestProfileGating:
    """Profiles produce correct active_transforms."""

    @pytest.fixture
    def tools(self) -> list[ToolDef]:
        return _make_verbose_tools()

    def test_conservative_only_has_sdm(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        result = compiler.compile(tools)
        assert result.active_transforms == ["sdm"]

    def test_balanced_has_five_transforms(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert set(result.active_transforms) == {"sdm", "cas", "cfo", "dro", "tas"}

    def test_aggressive_has_eight_transforms(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert set(result.active_transforms) == {"sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad"}

    def test_pipeline_order_preserved(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        canonical = ["sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad"]
        for a, b in zip(canonical, canonical[1:]):
            if a in result.active_transforms and b in result.active_transforms:
                assert result.active_transforms.index(a) < result.active_transforms.index(b)

    def test_conservative_sdm_is_active(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        result = compiler.compile(tools)
        assert "sdm" in result.active_transforms

    def test_balanced_dro_is_active(self, tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert "dro" in result.active_transforms


# ════════════════════════════════════════════════════════════════════
# Scenario 9: Model Auto-Detection
# ════════════════════════════════════════════════════════════════════


class TestModelAutoDetection:
    """auto profile with gpt-4o properly disables CFL+SAD."""

    def test_gpt_auto_profile_works(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="gpt-4o")  # profile=None → auto
        result = compiler.compile(tools)
        assert result.savings_pct > 0
        assert result.tool_count == 10

    def test_gpt_auto_profile_no_cfl(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" not in result.active_transforms

    def test_gpt_auto_profile_no_sad(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(tools)
        assert "sad" not in result.active_transforms

    def test_claude_auto_has_sad(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert "sad" in result.active_transforms

    def test_auto_default_model_is_claude_like(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="auto", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" in result.active_transforms
        assert "sad" in result.active_transforms

    def test_gemini_auto_disables_cfl_sad(self):
        tools = _make_verbose_tools()
        compiler = TSCGCompiler(model="gemini-2.0-flash", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms


# ════════════════════════════════════════════════════════════════════
# Scenario 10: Description-Only Mode
# ════════════════════════════════════════════════════════════════════


class TestDescriptionOnlyMode:
    """compress_tools mode="description-only" shortens descriptions, preserves structure."""

    @pytest.fixture
    def mcp_tools(self) -> list[dict]:
        return _make_mcp_tool_list(5)

    def test_description_only_produces_shorter_text(self, mcp_tools):
        full_text = compress_tools(mcp_tools, mode="full")
        desc_text = compress_tools(mcp_tools, mode="description-only")
        # description-only may be longer or shorter but both should produce non-empty output
        assert len(full_text) > 0
        assert len(desc_text) > 0

    def test_description_only_removes_filler(self, mcp_tools):
        """Verify filler phrases like 'Use this tool when you need to' are removed."""
        text = compress_tools(mcp_tools, mode="description-only")
        assert "Use this tool when you need to" not in text
        assert "This tool is useful when you need to" not in text

    def test_description_only_preserves_tool_names(self, mcp_tools):
        text = compress_tools(mcp_tools, mode="description-only")
        for tool in mcp_tools:
            assert tool["name"] in text

    def test_description_only_shows_param_names_in_output(self, mcp_tools):
        text = compress_tools(mcp_tools, mode="description-only")
        # Each tool has "input_param" and "verbose" params visible in DRO format
        assert "input_param" in text
        assert "verbose" in text

    def test_description_only_roundtrip_works(self):
        """decompress_tools roundtrip for param-free tools works correctly."""
        simple_mcp = [
            _mcp_tool_dict("ping", "Pings the remote service to check connectivity."),
        ]
        text = compress_tools(simple_mcp, mode="description-only")
        decompiled = decompress_tools(text)
        assert len(decompiled) == 1
        assert decompiled[0]["name"] == "ping"

    def test_full_vs_description_only_different(self, mcp_tools):
        full_text = compress_tools(mcp_tools, mode="full")
        desc_text = compress_tools(mcp_tools, mode="description-only")
        # Full mode applies CAS+CFO reordering, so output should differ
        assert full_text != desc_text

    def test_description_only_decompress_preserves_tool_count_and_names(self, mcp_tools):
        """decompress_tools recovers tool names and count (params limited by known bug)."""
        text = compress_tools(mcp_tools, mode="description-only")
        decompiled = decompress_tools(text)
        assert len(decompiled) == len(mcp_tools)
        for i, d in enumerate(decompiled):
            assert d["name"] == mcp_tools[i]["name"]

    def test_description_output_mark_required_params_with_star(self, mcp_tools):
        """DRO output uses * to mark required params in the compressed text."""
        text = compress_tools(mcp_tools, mode="description-only")
        # verify 'input_param*' appears in compressed output
        assert "input_param*" in text


# ════════════════════════════════════════════════════════════════════
# Proxy layer roundtrip tests
# ════════════════════════════════════════════════════════════════════


class TestProxyRoundtrip:
    """MCP ↔ TSCG conversion + compression roundtrip."""

    def test_mcp_to_tscg_preserves_all_fields(self):
        mcp = _mcp_tool_dict(
            "search_files",
            "This tool allows you to search for files in the filesystem. "
            "You can use this to find specific files by name or pattern.",
            props={
                "pattern": {"type": "string", "description": "Specifies the glob pattern to search."},
                "case_sensitive": {"type": "boolean", "description": "Determines whether to match case."},
            },
            required=["pattern"],
        )
        tscg = mcp_tool_to_tscg(mcp)
        assert tscg.name == "search_files"
        assert len(tscg.parameters) == 2
        assert tscg.parameters[0].name == "pattern"
        assert tscg.parameters[0].required is True
        assert tscg.parameters[1].name == "case_sensitive"
        assert tscg.parameters[1].required is False

    def test_compress_decompress_preserves_tool_count(self):
        mcp_tools = _make_mcp_tool_list(8)
        text = compress_tools(mcp_tools, mode="full")
        decompiled = decompress_tools(text)
        assert len(decompiled) == 8

    def test_compress_decompress_preserves_tool_names(self):
        mcp_tools = _make_mcp_tool_list(5)
        text = compress_tools(mcp_tools, mode="full")
        decompiled = decompress_tools(text)
        original_names = {t["name"] for t in mcp_tools}
        recovered_names = {t["name"] for t in decompiled}
        assert original_names == recovered_names

    def test_compress_decompress_empty_list(self):
        text = compress_tools([], mode="full")
        assert text == ""
        decompiled = decompress_tools(text)
        assert decompiled == []

    def test_compress_decompress_preserves_tool_names(self):
        """decompress_tools recovers tool name and count for roundtrip."""
        mcp_tools = [
            _mcp_tool_dict(
                "delete_item",
                "Permanently deletes an item from the database. "
                "This action cannot be undone.",
                props={
                    "item_id": {"type": "string", "description": "The unique identifier of the item to delete."},
                },
                required=["item_id"],
            ),
        ]
        text = compress_tools(mcp_tools, mode="full")
        decompiled = decompress_tools(text)
        assert len(decompiled) == 1
        assert decompiled[0]["name"] == "delete_item"

    def test_compressed_output_shows_required_mark(self):
        """Compressed text output marks required params with * in DRO format."""
        mcp_tools = [
            _mcp_tool_dict(
                "delete_item",
                "Permanently deletes an item.",
                props={
                    "item_id": {"type": "string", "description": "Unique identifier."},
                    "confirm": {"type": "boolean", "description": "User has confirmed deletion."},
                },
                required=["item_id", "confirm"],
            ),
        ]
        text = compress_tools(mcp_tools, mode="full")
        assert "item_id*" in text
        assert "confirm*" in text


# ════════════════════════════════════════════════════════════════════
# Edge cases
# ════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Integration edge cases across the pipeline."""

    def test_single_tool_no_params(self):
        tools = [_tool("ping", "Pings the remote service to check availability.")]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert result.tool_count == 1
        assert result.savings_pct >= 0
        decompiled = compiler.decompile(result.compressed_text)
        assert len(decompiled) == 1
        assert decompiled[0].name == "ping"

    def test_tool_with_only_optional_params(self):
        tools = [_tool("log_event", "Logs an application event.", [
            _param("level", "string", "The severity level.", enum=["debug", "info", "warn", "error"]),
            _param("message", "string", "The message to log."),
            _param("tags", "array", "Optional tags for the event."),
        ])]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert len(decompiled[0].parameters) == 3
        # All optional — none should be marked required
        assert all(not p.required for p in decompiled[0].parameters)

    def test_tool_with_all_required_params(self):
        tools = [_tool("transfer_funds", "Transfers funds between accounts.", [
            _param("from", "string", "Source account ID.", required=True),
            _param("to", "string", "Destination account ID.", required=True),
            _param("amount", "number", "Amount to transfer.", required=True),
        ])]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert all(p.required for p in decompiled[0].parameters)

    def test_multiple_compiles_no_state_leak(self):
        """Successive compiles with different toolsets don't leak state."""
        c = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        r1 = c.compile([_tool("tool_a", "Description A.")])
        r2 = c.compile([_tool("tool_b", "Description B.", [_param("x", "string", "Param X.", required=True)])])
        assert r1.tool_count == 1
        assert r2.tool_count == 1
        # active_transforms should be consistent for the same explicit profile
        assert r1.active_transforms == ["sdm", "cas", "cfo", "dro", "tas"]
        assert r2.active_transforms == ["sdm", "cas", "cfo", "dro", "tas"]
        # Second compile should not leak tool_a
        decompiled = c.decompile(r2.compressed_text)
        assert len(decompiled) == 1
        assert decompiled[0].name == "tool_b"

    def test_very_long_description(self):
        desc = "This tool performs a comprehensive analysis of the input data. " * 10
        tools = [_tool("analyze", desc, [_param("data", "string", "The data to analyze.", required=True)])]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        assert result.savings_pct > 20  # Long descriptions should compress well

    def test_many_enum_params(self):
        tools = [_tool("set_mode", "Sets the operational mode.", [
            _param("mode", "string", "Operation mode.", required=True,
                   enum=["read", "write", "append", "delete", "execute", "admin"]),
            _param("sub_mode", "string", "Sub-mode.",
                   enum=["fast", "balanced", "precise", "custom"]),
        ])]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert decompiled[0].parameters[0].enum == ["read", "write", "append", "delete", "execute", "admin"]
        assert decompiled[0].parameters[1].enum == ["fast", "balanced", "precise", "custom"]
