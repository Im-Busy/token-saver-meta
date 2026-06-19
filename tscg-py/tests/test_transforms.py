"""
Tests for tscg/core/transforms.py — ported from TypeScript _engine.ts.

All 8 paper transforms tested:
  SDM, CAS, CFO, DRO, TAS, CFL, CCP, SAD-F

Plus roundtrip tests (compress→decompress fidelity).
"""

import pytest

from tscg.core.transforms import (
    ToolDef,
    ParamDef,
    apply_sdm,
    apply_cas,
    apply_cfo,
    apply_dro,
    apply_tas,
    apply_cfl,
    apply_ccp,
    apply_sad,
    optimize_tool_definitions,
)


# ── Helper factories ────────────────────────────────────────────


def _tool(
    name: str,
    desc: str,
    params: list[ParamDef] | None = None,
    freq: float = 0.5,
) -> ToolDef:
    return ToolDef(name=name, description=desc, parameters=params or [], usageFrequency=freq)


def _param(
    name: str,
    ptype: str = "string",
    desc: str = "",
    required: bool = False,
    enum: list[str] | None = None,
) -> ParamDef:
    return ParamDef(name=name, type=ptype, description=desc, required=required, enum=enum)


# ── Shared test fixtures ─────────────────────────────────────────


@pytest.fixture
def weather_tool() -> ToolDef:
    return _tool(
        name="get_weather",
        desc="Use this tool when you need to get current weather data for a location. This tool allows you to fetch temperature, humidity, and conditions.",
        params=[
            _param("location", "string", "Specifies the city name or coordinates.", required=True),
            _param("units", "string", "The temperature unit to use if needed.", enum=["celsius", "fahrenheit"]),
            _param("include_hourly", "boolean", "Determines whether to include hourly forecast data if applicable."),
        ],
        freq=0.9,
    )


@pytest.fixture
def search_tool() -> ToolDef:
    return _tool(
        name="search_web",
        desc="This tool is designed to search the web for information that may have changed since your training cutoff.",
        params=[
            _param("query", "string", "The search query string.", required=True),
            _param("max_results", "number", "Maximum number of results to return. Indicates the limit.", enum=["5", "10", "20"]),
        ],
        freq=0.8,
    )


@pytest.fixture
def create_tool() -> ToolDef:
    return _tool(
        name="create_file",
        desc="Creates a new file at the specified path. Please note that the file will be overwritten if it already exists.",
        params=[
            _param("path", "string", "The path of the file to create.", required=True),
            _param("content", "string", "The content to write to the file.", required=True),
            _param("encoding", "string", "File encoding when available.", enum=["utf-8", "ascii"]),
        ],
        freq=0.7,
    )


@pytest.fixture
def delete_tool() -> ToolDef:
    return _tool(
        name="delete_file",
        desc="Deletes a file at the specified path. Represents a destructive operation.",
        params=[
            _param("path", "string", "Path to delete.", required=True),
            _param("recursive", "boolean", "Whether to delete recursively as needed."),
        ],
        freq=0.3,
    )


@pytest.fixture
def list_tool() -> ToolDef:
    return _tool(
        name="list_files",
        desc="Lists all files in a directory. You can use this tool to browse directory contents.",
        params=[
            _param("directory", "string", "The directory path to list.", required=True),
            _param("pattern", "string", "A glob pattern to filter results."),
            _param("recursive", "boolean", "Whether to search subdirectories."),
        ],
        freq=0.6,
    )


@pytest.fixture
def transform_tool() -> ToolDef:
    return _tool(
        name="summarize_text",
        desc="Summarizes the given text into a concise paragraph. This tool can be used to compress long documents.",
        params=[
            _param("text", "string", "The text to summarize.", required=True),
            _param("max_length", "number", "Maximum summary length in words."),
        ],
        freq=0.4,
    )


# ══════════════════════════════════════════════════════════════════
# SDM: Semantic Density Maximization (~8 tests)
# ══════════════════════════════════════════════════════════════════


class TestSDM:
    """Test SDM — filler phrase stripping + capitalize + trailing period."""

    def test_strips_use_this_tool_when_you_need_to(self):
        """'Use this tool when you need to' prefix removed."""
        tools = [_tool("t1", "Use this tool when you need to fetch data.", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Fetch data."

    def test_strips_this_tool_allows_you_to(self):
        """'This tool allows you to' prefix removed."""
        tools = [_tool("t1", "This tool allows you to search the web.", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Search the web."

    def test_strips_this_tool_is_designed_to(self):
        """'This tool is designed to' prefix removed."""
        tools = [_tool("t1", "This tool is designed to optimize queries.", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Optimize queries."

    def test_strips_specifies_the(self):
        """'Specifies the' prefix removed from param descriptions."""
        tools = [
            _tool("t1", "Does something.", [
                _param("x", "string", "Specifies the target URL."),
            ]),
        ]
        result = apply_sdm(tools)
        assert result[0].parameters[0].description == "Target URL."

    def test_strips_indicates_and_determines(self):
        """Indicates/Determines the/whether stripped per algorithm order."""
        tools = [
            _tool("t1", "Desc.", [
                _param("verbose", "boolean", "Indicates whether to show details."),
                _param("force", "boolean", "Determines the overwrite behavior."),
            ]),
        ]
        result = apply_sdm(tools)
        # "Indicates whether " stripped → "to show details." → capitalize → "To show details."
        assert result[0].parameters[0].description == "To show details."
        # "Determines the " stripped → "overwrite behavior." → capitalize → "Overwrite behavior."
        assert result[0].parameters[1].description == "Overwrite behavior."

    def test_strips_trailing_if_needed(self):
        """'if needed', 'if applicable', 'as needed', 'when available' stripped from end."""
        tests = [
            # "Specifies" only stripped when followed by "the", so "Specifies units if needed." → "Specifies units."
            ("Specifies units if needed.", "Specifies units."),
            ("Show details if applicable.", "Show details."),
            ("Recurse as needed.", "Recurse."),
            ("Use cache when available.", "Use cache."),
        ]
        for inp, expected in tests:
            tools = [_tool("t1", "desc", [_param("p", "string", inp)])]
            result = apply_sdm(tools)
            assert result[0].parameters[0].description == expected, f"Failed on: {inp}"

    def test_strips_you_can_use_this_to(self):
        """Pattern 2 (Use this tool to) fires before pattern 4, leaving 'You can'."""
        tools = [_tool("t1", "You can use this tool to send messages.", [])]
        result = apply_sdm(tools)
        # Pattern 2: "\bUse this (?:tool|function) (?:to|for)\s*" strips "use this tool to "
        # Result: "You can send messages." → capitalize → "You can send messages."
        assert result[0].description == "You can send messages."

    def test_capitalize_first_letter(self):
        """First lowercase letter capitalized after stripping."""
        tools = [_tool("t1", "  sends a message  ", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Sends a message."

    def test_adds_trailing_period(self):
        """Trailing period added when missing."""
        tools = [_tool("t1", "Sends a message", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Sends a message."

    def test_preserves_ending_punctuation(self):
        """No extra period when already ends with . ! ?"""
        for end in [".", "!", "?"]:
            desc = f"Sends a message{end}"
            tools = [_tool("t1", desc, [])]
            result = apply_sdm(tools)
            assert result[0].description == desc

    def test_sdm_applied_to_param_descriptions(self):
        """SDM strips filler from parameter descriptions in pattern order."""
        tools = [
            _tool("t1", "desc.", [
                _param("x", "string", "Specifies the input file."),
                _param("y", "number", "Indicates the max retries if needed."),
            ]),
        ]
        result = apply_sdm(tools)
        # Pattern 10 (\bThe input...) matches "The input " before pattern 11 (\bSpecifies the)
        # → "Specifies file." → capitalize → "Specifies file."
        assert result[0].parameters[0].description == "Specifies file."
        # Pattern 12 (\bIndicates the) strips "Indicates the " → "max retries if needed."
        # Pattern 15 (\s*\bif needed\.?) strips trailing " if needed." → "Max retries."
        assert result[0].parameters[1].description == "Max retries."

    def test_collapses_multiple_spaces(self):
        """Multiple spaces collapsed to single space."""
        tools = [_tool("t1", "Sends   a   message.", [])]
        result = apply_sdm(tools)
        assert result[0].description == "Sends a message."

    def test_cleans_double_comma(self):
        """Double comma collapsed to single; first letter capitalized."""
        tools = [_tool("t1", "foo,, bar.", [])]
        result = apply_sdm(tools)
        # ",," → "," via regex; capitalize first letter → "Foo"
        assert "Foo, bar." == result[0].description

    def test_empty_description_returns_empty(self):
        """Empty string stays empty."""
        tools = [_tool("t1", "", [])]
        result = apply_sdm(tools)
        assert result[0].description == ""


# ══════════════════════════════════════════════════════════════════
# CAS: Causal Access Score (~6 tests)
# ══════════════════════════════════════════════════════════════════


class TestCAS:
    """Test CAS — U-shape frequency reorder."""

    def test_u_shape_reorder_basic(self):
        """Highest freq at edges, lowest in middle."""
        tools = [
            _tool("A", "a", freq=0.1),
            _tool("B", "b", freq=0.3),
            _tool("C", "c", freq=0.5),
            _tool("D", "d", freq=0.9),
        ]
        result = apply_cas(tools)
        names = [t.name for t in result]
        # Sorted by freq desc: D(0.9), C(0.5), B(0.3), A(0.1)
        # Interleave: D→pos0, C→pos3, B→pos1, A→pos2
        assert names == ["D", "B", "A", "C"]

    def test_u_shape_odd_count(self):
        """5 tools: edges high-freq, middle low-freq."""
        tools = [
            _tool("A", "a", freq=0.1),
            _tool("B", "b", freq=0.2),
            _tool("C", "c", freq=0.3),
            _tool("D", "d", freq=0.4),
            _tool("E", "e", freq=0.5),
        ]
        result = apply_cas(tools)
        names = [t.name for t in result]
        # Sorted desc: E(0.5), D(0.4), C(0.3), B(0.2), A(0.1)
        # i=0 even → pos 0: E
        # i=1 odd → pos 4: D
        # i=2 even → pos 1: C
        # i=3 odd → pos 3: B
        # i=4 even → pos 2: A
        assert names == ["E", "C", "A", "B", "D"]

    def test_default_frequency_05(self):
        """Missing usageFrequency defaults to 0.5."""
        tools = [
            ToolDef("B", "b", [], usageFrequency=0.3),
            ToolDef("A", "a", []),  # no usageFrequency → 0.5
            ToolDef("C", "c", [], usageFrequency=0.1),
        ]
        result = apply_cas(tools)
        # Sorted desc: A(0.5), B(0.3), C(0.1)
        # i=0 even → pos 0: A
        # i=1 odd → pos 2: B
        # i=2 even → pos 1: C
        names = [t.name for t in result]
        assert names == ["A", "C", "B"]

    def test_stable_sort_same_frequency(self):
        """Same frequency preserves original order."""
        tools = [
            _tool("A", "a", freq=0.5),
            _tool("B", "b", freq=0.5),
            _tool("C", "c", freq=0.5),
            _tool("D", "d", freq=0.5),
        ]
        result = apply_cas(tools)
        names = [t.name for t in result]
        # All same freq, so sorted order = original: A,B,C,D
        # i=0 even → pos 0: A
        # i=1 odd → pos 3: B
        # i=2 even → pos 1: C
        # i=3 odd → pos 2: D
        assert names == ["A", "C", "D", "B"]

    def test_two_or_fewer_tools_identity(self):
        """CAS leaves 1-2 tools unchanged."""
        tools = [_tool("A", "a", freq=0.1), _tool("B", "b", freq=0.9)]
        result = apply_cas(tools)
        assert result[0].name == "A"
        assert result[1].name == "B"

    def test_single_tool_identity(self):
        """Single tool unchanged."""
        tools = [_tool("Only", "only", freq=0.7)]
        result = apply_cas(tools)
        assert result[0].name == "Only"


# ══════════════════════════════════════════════════════════════════
# CFO: Causal-Forward Ordering (~7 tests)
# ══════════════════════════════════════════════════════════════════


class TestCFO:
    """Test CFO — READ → TRANSFORM → WRITE ordering."""

    def test_read_before_write(self):
        """READ tools come before WRITE tools."""
        tools = [
            _tool("create_file", "create something", []),
            _tool("get_weather", "get something", []),
            _tool("delete_file", "delete something", []),
            _tool("search_web", "search something", []),
        ]
        result = apply_cfo(tools)
        names = [t.name for t in result]
        assert names == ["get_weather", "search_web", "create_file", "delete_file"]

    def test_transform_in_middle(self):
        """TRANSFORM tools between READ and WRITE."""
        tools = [
            _tool("create_x", "create", []),
            _tool("get_x", "get", []),
            _tool("transform_x", "transform", []),
        ]
        result = apply_cfo(tools)
        names = [t.name for t in result]
        assert names == ["get_x", "transform_x", "create_x"]

    def test_all_same_class_identity(self):
        """All tools in same CFO class → identity (original order preserved)."""
        tools = [
            _tool("create_a", "create a", []),
            _tool("create_b", "create b", []),
            _tool("create_c", "create c", []),
        ]
        result = apply_cfo(tools)
        names = [t.name for t in result]
        assert names == ["create_a", "create_b", "create_c"]

    def test_fallback_to_description_first_word(self):
        """Fallback classification via first word of description."""
        tools = [
            _tool("x1", "Read the configuration file", []),
            _tool("x2", "Update the database", []),
            _tool("x3", "Parse the input text", []),
        ]
        result = apply_cfo(tools)
        names = [t.name for t in result]
        # read: x1 ("Read"), transform: x3 ("Parse"), write: x2 ("Update")
        assert names == ["x1", "x3", "x2"]

    def test_stable_sort_within_class(self):
        """Tools within same class preserve input order."""
        tools = [
            _tool("get_c", "get c", []),
            _tool("create_b", "create b", []),
            _tool("get_a", "get a", []),
            _tool("create_a", "create a", []),
        ]
        result = apply_cfo(tools)
        names = [t.name for t in result]
        assert names == ["get_c", "get_a", "create_b", "create_a"]

    def test_single_tool(self):
        """Single tool unchanged."""
        tools = [_tool("get_x", "get", [])]
        result = apply_cfo(tools)
        assert result[0].name == "get_x"

    def test_multiple_read_prefixes(self):
        """Various READ prefixes all classified as read."""
        read_prefixes = ["get_data", "read_file", "list_users", "search_repos",
                         "find_user", "query_db", "fetch_url", "view_page",
                         "describe_issue", "show_help"]
        for name in read_prefixes:
            tools = [_tool(name, "desc", []), _tool("create_z", "create", [])]
            result = apply_cfo(tools)
            assert result[0].name == name, f"{name} should be read"


# ══════════════════════════════════════════════════════════════════
# DRO: Delimiter-Role Optimization (~5 tests)
# ══════════════════════════════════════════════════════════════════


class TestDRO:
    """Test DRO — compact parameter format."""

    def test_basic_format(self):
        """DRO formats tool with name, description, and parameters."""
        tools = [_tool("get_data", "Fetches data.", [
            _param("url", "string", "Target URL.", required=True),
            _param("timeout", "number", "Request timeout in seconds.", enum=["10", "30", "60"]),
        ])]
        result = apply_dro(tools)
        assert len(result) == 1
        line = result[0]
        assert line.startswith("get_data:")
        assert "url* (str): Target URL." in line
        assert "timeout (num: 10|30|60): Request timeout in seconds." in line

    def test_required_marked_with_star(self):
        """Required params have * after name."""
        tools = [_tool("t", "desc", [
            _param("a", "string", "Required param.", required=True),
            _param("b", "string", "Optional param.", required=False),
        ])]
        result = apply_dro(tools)
        assert "a* (str): Required param." in result[0]
        assert "b (str): Optional param." in result[0]

    def test_type_abbreviations(self):
        """Types abbreviated: string→str, number→num, boolean→bool, array→arr, object→obj."""
        tools = [_tool("t", "desc", [
            _param("a", "string", "String param."),
            _param("b", "number", "Number param."),
            _param("c", "boolean", "Boolean param."),
            _param("d", "array", "Array param."),
            _param("e", "object", "Object param."),
            _param("f", "customtype", "Custom type stays as-is."),
        ])]
        result = apply_dro(tools)
        assert "(str):" in result[0]
        assert "(num):" in result[0]
        assert "(bool):" in result[0]
        assert "(arr):" in result[0]
        assert "(obj):" in result[0]
        assert "(customtype):" in result[0]

    def test_enum_formatting(self):
        """Enum values joined with pipe."""
        tools = [_tool("t", "desc", [
            _param("mode", "string", "Operation mode.", enum=["read", "write", "append"]),
        ])]
        result = apply_dro(tools)
        assert "mode (str: read|write|append): Operation mode." in result[0]

    def test_no_parameters(self):
        """Tool with no parameters has no param line."""
        tools = [_tool("simple", "Does something simple.", [])]
        result = apply_dro(tools)
        assert result[0] == "simple: Does something simple."


# ══════════════════════════════════════════════════════════════════
# TAS: Tokenizer-Aligned Syntax (~6 tests)
# ══════════════════════════════════════════════════════════════════


class TestTAS:
    """Test TAS — BPE-optimized delimiters."""

    def test_arrow_replacement(self):
        """=> and --> replaced with :"""
        lines = ["param: desc => value", "other: text --> result"]
        result = apply_tas(lines)
        assert "=>" not in result
        assert "-->" not in result

    def test_pipe_normalization(self):
        """Whitespace around | normalized to single spaces."""
        lines = ["param1|param2", "a  |  b", "c|d"]
        result = apply_tas(lines)
        lines_out = result.split("\n")
        # collapsed: "param1 | param2", "a | b", "c | d"
        assert "param1 | param2" in lines_out[0]
        assert "a | b" in lines_out[1]
        assert "c | d" in lines_out[2]

    def test_collapse_multiple_spaces_after_colon(self):
        """Multiple spaces after colon collapsed to single space."""
        lines = ["name:    long description here"]
        result = apply_tas(lines)
        assert "name: long description" in result

    def test_single_newline_between_tools(self):
        """Tools separated by single newline, no blank lines."""
        lines = ["tool_a: desc", "tool_b: desc", "tool_c: desc"]
        result = apply_tas(lines)
        assert result == "tool_a: desc\ntool_b: desc\ntool_c: desc"

    def test_empty_lines_preserved_as_is(self):
        """Empty lines in input pass through."""
        lines = ["tool_a: desc", "", "tool_b: desc"]
        result = apply_tas(lines)
        assert result == "tool_a: desc\n\ntool_b: desc"

    def test_combined_transformations(self):
        r"""Multiple transforms applied: =>, -->, |, :\s{2,} — TAS does NOT trim leading spaces."""
        lines = ["  get_data   =>   fetch_data -->  result    |   backup  "]
        result = apply_tas(lines)
        assert "=>" not in result
        assert "-->" not in result
        assert " | " in result
        # :\\s{2,} collapsed after colons; leading spaces preserved; trailing spaces preserved
        # Output: "  get_data   : fetch_data : result | backup  "
        assert "result | backup" in result


# ══════════════════════════════════════════════════════════════════
# CFL: Constraint-First Layout (~3 tests)
# ══════════════════════════════════════════════════════════════════


class TestCFL:
    """Test CFL — prepend [ANSWER:function_call]."""

    def test_prepends_answer_tag(self):
        """CFL prepends [ANSWER:function_call] to text."""
        result = apply_cfl("some compressed text")
        assert result.startswith("[ANSWER:function_call]\n")
        assert result.endswith("some compressed text")

    def test_empty_text(self):
        """CFL works on empty text."""
        result = apply_cfl("")
        assert result == "[ANSWER:function_call]\n"

    def test_preserves_existing_content(self):
        """Original content appears after newline."""
        result = apply_cfl("tool_a: desc\ntool_b: desc")
        lines = result.split("\n")
        assert lines[0] == "[ANSWER:function_call]"
        assert lines[1] == "tool_a: desc"
        assert lines[2] == "tool_b: desc"


# ══════════════════════════════════════════════════════════════════
# CCP: Causal Closure Principle (~6 tests)
# ══════════════════════════════════════════════════════════════════


class TestCCP:
    """Test CCP — append [CLOSURE:...] recap."""

    def test_closure_with_required_params(self):
        """CCP appends closure with required params."""
        tools = [
            _tool("search", "search", [
                _param("query", "string", "Query.", required=True),
                _param("limit", "number", "Limit."),
            ]),
            _tool("fetch", "fetch", [
                _param("url", "string", "URL.", required=True),
            ]),
        ]
        result = apply_ccp("compressed text", tools)
        assert result.endswith("\n[CLOSURE:search(query),fetch(url)]")

    def test_tool_without_required_params(self):
        """Tool with no required params has empty parens."""
        tools = [
            _tool("ping", "ping", []),
            _tool("list", "list", [_param("filter", "string", "Optional filter.")]),
        ]
        result = apply_ccp("text", tools)
        assert "[CLOSURE:ping(),list()]" in result

    def test_empty_tools_list(self):
        """CCP with no tools returns text unchanged."""
        result = apply_ccp("some text", [])
        assert result == "some text"

    def test_multiple_required_params(self):
        """Multiple required params joined with commas."""
        tools = [
            _tool("move", "move", [
                _param("from", "string", "Source.", required=True),
                _param("to", "string", "Destination.", required=True),
                _param("overwrite", "boolean", "Overwrite flag."),
            ]),
        ]
        result = apply_ccp("text", tools)
        assert "[CLOSURE:move(from,to)]" in result

    def test_closure_uses_original_tool_name(self):
        """Closure entry uses unchanged tool name."""
        tools = [_tool("get_weather", "desc", [
            _param("city", "string", "City.", required=True),
        ])]
        result = apply_ccp("text", tools)
        assert "get_weather(city)" in result

    def test_no_trailing_modifications(self):
        """Only closure appended, no other changes."""
        tools = [_tool("t", "d", [_param("x", "string", "x", required=True)])]
        result = apply_ccp("original", tools)
        assert result == "original\n[CLOSURE:t(x)]"


# ══════════════════════════════════════════════════════════════════
# SAD-F: Selective Anchor Duplication (~7 tests)
# ══════════════════════════════════════════════════════════════════


class TestSAD:
    """Test SAD-F — anchor extraction from DRO-compressed text."""

    def test_extracts_tool_names(self):
        """Strategy 1: extracts tool names from DRO-format text."""
        dro_text = "get_weather: Gets weather.\n  city* (str): City name.\nsearch_web: Searches.\n  query* (str): Query."
        result = apply_sad(dro_text, topK=4)
        assert "[ANCHOR:" in result
        assert "get_weather" in result
        assert "search_web" in result

    def test_extracts_required_params(self):
        """Strategy 2: extracts required param names (marked with *)."""
        dro_text = "tool: desc\n  name* (str): Name.\n  email* (str): Email.\n  age (num): Age."
        result = apply_sad(dro_text, topK=5)
        assert "name*" in result
        assert "email*" in result
        assert "age" not in result or ("age" in result and "age*" not in result)

    def test_extracts_enum_values(self):
        """Strategy 3: extracts TYPE:enumID patterns from DRO format (matches type abbrev, not param name)."""
        dro_text = "tool: desc\n  mode (str: read|write|append): Mode."
        result = apply_sad(dro_text, topK=5)
        # The regex matches \w+:\s*[\w]+(?:\|[\w]+)+ → finds "str: read|write|append"
        assert "str" in result
        assert "read|write|append" in result.replace(" ", "")

    def test_dedup_anchors(self):
        """Duplicate anchors removed."""
        dro_text = "get: Gets.\n  id* (str): ID.\nget: Gets.\n  id* (str): ID."
        result = apply_sad(dro_text, topK=10)
        # Count occurrences of "get"
        anchor_part = result.split("[ANCHOR:")[1].rstrip("]")
        anchors = anchor_part.split(",")
        assert anchors.count("get") == 1
        assert anchors.count("id*") == 1

    def test_top_k_limit(self):
        """Only top-K anchors included."""
        dro_text = "\n".join([f"tool_{i}: desc\n  p{i}* (str): P{i}." for i in range(10)])
        result = apply_sad(dro_text, topK=3)
        anchor_part = result.split("[ANCHOR:")[1].rstrip("]")
        anchors = anchor_part.split(",")
        assert len(anchors) == 3

    def test_no_anchors_no_tag(self):
        """No [ANCHOR:] tag when no anchors found."""
        result = apply_sad("plain text without any DRO patterns", topK=4)
        assert "[ANCHOR:" not in result

    def test_preserves_original_text(self):
        """Original text preserved before anchor tag."""
        dro_text = "get_weather: desc\n  city* (str): City."
        result = apply_sad(dro_text, topK=4)
        assert result.startswith(dro_text)


# ══════════════════════════════════════════════════════════════════
# Roundtrip & Integration (~4 tests)
# ══════════════════════════════════════════════════════════════════


class TestRoundtrip:
    """Compress→decompress must preserve all tool information."""

    def test_roundtrip_preserves_tool_names(self):
        """All tool names survive compression pipeline."""
        tools = [
            _tool("get_weather", "Use this tool when you need to get weather.", [
                _param("city", "string", "City name.", required=True),
                _param("units", "string", "Temperature units.", enum=["celsius", "fahrenheit"]),
            ], freq=0.9),
            _tool("create_report", "Creates a report.", [
                _param("title", "string", "Report title.", required=True),
                _param("content", "string", "Report body.", required=True),
            ], freq=0.5),
        ]
        result = optimize_tool_definitions(tools, useSDM=True, useDRO=True, useTAS=True,
                                           useCFO=False, useCAS=False,
                                           useCFL=False, useSAD=False, useCCP=False)
        # All tool names should be in the compressed text
        assert "get_weather" in result.text
        assert "create_report" in result.text

    def test_roundtrip_preserves_required_params(self):
        """Required parameters identifiable in compressed output."""
        tools = [
            _tool("search", "Searches.", [
                _param("query", "string", "Search query.", required=True),
                _param("limit", "number", "Max results."),
            ], freq=0.8),
        ]
        result = optimize_tool_definitions(tools, useSDM=True, useDRO=True, useTAS=True)
        # Required params marked with *
        assert "query*" in result.text

    def test_roundtrip_preserves_enum_values(self):
        """Enum values preserved in compressed output (TAS-normalized with spaces around |)."""
        tools = [
            _tool("set_mode", "Sets mode.", [
                _param("mode", "string", "Mode.", enum=["A", "B", "C"], required=True),
            ], freq=0.5),
        ]
        result = optimize_tool_definitions(tools, useSDM=True, useDRO=True, useTAS=True)
        # TAS normalizes | spacing: A|B|C → A | B | C
        assert "A" in result.text
        assert "B" in result.text
        assert "C" in result.text
        assert " | " in result.text

    def test_full_pipeline_saves_tokens(self):
        """Full pipeline with all transforms produces savings."""
        tools = [
            _tool("get_weather", "Use this tool when you need to fetch current weather data for a given location. This tool allows you to get temperature, humidity, wind speed, and atmospheric conditions.",
                  [_param("location", "string", "Specifies the city name or geographic coordinates for the weather query.", required=True),
                   _param("units", "string", "Determines the temperature unit system to use for the response if needed.", enum=["celsius", "fahrenheit", "kelvin"]),
                   _param("include_forecast", "boolean", "Indicates whether to include a multi-day forecast in the response when available.")], freq=0.9),
            _tool("create_report", "Creates a weather report file with formatted content. Please note that existing files will be overwritten.",
                  [_param("title", "string", "The report title.", required=True),
                   _param("format", "string", "Output format.", enum=["pdf", "html", "text"], required=True)], freq=0.6),
        ]
        result = optimize_tool_definitions(tools, useSDM=True, useDRO=True, useTAS=True,
                                           useCAS=True, useCFO=True,
                                           useCFL=False, useSAD=False, useCCP=False)
        assert result.savingsPercent > 0
        assert result.originalTokenEstimate > result.optimizedTokenEstimate

    def test_optimize_respects_disabled_transforms(self):
        """Disabling all transforms preserves verbatim content."""
        tools = [_tool("get_x", "Use this tool when you need to get x.", [])]
        result = optimize_tool_definitions(tools, useSDM=False, useDRO=False, useTAS=False,
                                           useCFO=False, useCAS=False)
        # Verbatim mode: filler not stripped
        assert "Use this tool when you need to" in result.text
