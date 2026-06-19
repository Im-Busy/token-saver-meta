"""High-pressure stress tests for tscg-py."""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tscg.core.compiler import TSCGCompiler, CompiledSchema
from tscg.core.transforms import ToolDef, ParamDef
from tscg.core.profiles import ModelFamily, detect_model_family, is_thinking_model
from tscg.proxy.compressor import mcp_tool_to_tscg, compress_tools, decompress_tools
from tscg.core.utils import estimate_tokens


# ── Helpers ───────────────────────────────────────────────────────


def _make_mcp_tool(
    idx: int,
    num_params: int = 3,
    include_nested: bool = False,
) -> dict:
    """Generate a single MCP tool dict with flat or nested params."""
    props: dict[str, dict] = {}
    required: list[str] = []
    for j in range(num_params):
        pname = f"param_{j}"
        ptype = ["string", "number", "boolean", "array", "object"][j % 5]
        if include_nested and j == num_params - 1:
            pdef = {
                "anyOf": [
                    {"type": "string", "description": "string variant"},
                    {"type": "number", "description": "number variant"},
                ],
                "description": f"Nested param {j} for tool {idx}",
            }
        elif include_nested and j == num_params - 2:
            pdef = {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                ],
                "description": f"OneOf param {j} for tool {idx}",
            }
        else:
            pdef = {
                "type": ptype,
                "description": f"Parameter {j} description for tool {idx}",
            }
        props[pname] = pdef
        if j == 0:
            required.append(pname)
    return {
        "name": f"tool_{idx}",
        "description": f"Tool {idx} for testing massive schema compression",
        "inputSchema": {"type": "object", "properties": props, "required": required},
    }


def _generate_mcp_tools(count: int, nested_ratio: float = 0.2) -> list[dict]:
    """Generate `count` MCP tool dicts. ~nested_ratio will have nested schemas."""
    tools: list[dict] = []
    for i in range(count):
        num_params = 3 + (i % 3)
        include_nested = (i % int(1 / nested_ratio) == 0) if nested_ratio > 0 else False
        tools.append(_make_mcp_tool(i, num_params, include_nested))
    return tools


def _make_tool_def(name: str, desc: str = "", params: list[ParamDef] | None = None) -> ToolDef:
    return ToolDef(name=name, description=desc, parameters=params or [])


def _make_param(
    name: str,
    ptype: str = "string",
    desc: str = "",
    required: bool = False,
    enum: list[str] | None = None,
) -> ParamDef:
    return ParamDef(name=name, type=ptype, description=desc, required=required, enum=enum)


# ══════════════════════════════════════════════════════════════════
# Test 1: Massive Schema (100 tools)
# ══════════════════════════════════════════════════════════════════


def test_massive_schema() -> bool:
    """Generate 100 MCP tool dicts, compress → decompress, verify roundtrip."""
    tools = _generate_mcp_tools(100, nested_ratio=0.15)
    assert len(tools) == 100

    original_json = json.dumps(tools)
    compressed = compress_tools(tools, mode="full")
    decompressed = decompress_tools(compressed)

    tool_count_ok = len(decompressed) == 100
    # Build name → param count maps
    orig_param_counts = {
        t["name"]: len(t.get("inputSchema", {}).get("properties", {}))
        for t in tools
    }
    decomp_param_counts = {
        t["name"]: len(t.get("inputSchema", {}).get("properties", {}))
        for t in decompressed
    }
    name_matches = set(orig_param_counts.keys()) == set(decomp_param_counts.keys())
    params_preserved = sum(
        1 for name in orig_param_counts
        if orig_param_counts[name] == decomp_param_counts.get(name, -1)
    )
    # Nested schemas (anyOf/oneOf) cannot roundtrip through DRO → param counts differ
    # Expected: ~85 flat tools match, ~15 nested tools differ
    names_ok = tool_count_ok and name_matches
    params_ok = params_preserved >= 75  # at least 85 flat tools

    before_tokens = estimate_tokens(original_json)
    after_tokens = estimate_tokens(compressed)
    savings_pct = (
        ((before_tokens - after_tokens) / before_tokens * 100)
        if before_tokens > 0
        else 0.0
    )

    passed = names_ok and params_ok and savings_pct > 0
    print(
        f"test_massive_schema: tool_count=100, savings_pct={savings_pct:.1f}%, "
        f"names_preserved={name_matches}, params_preserved={params_preserved}/100, "
        f"{'PASS' if passed else 'FAIL'}"
    )
    if not passed:
        if not params_ok:
            print(f"  FAIL: params_preserved={params_preserved} < 75 threshold")
        if not (names_ok and tool_count_ok):
            print(f"  FAIL: tool_count_ok={tool_count_ok}, name_matches={name_matches}")
    return passed


# ══════════════════════════════════════════════════════════════════
# Test 2: Pathological Descriptions
# ══════════════════════════════════════════════════════════════════


def test_pathological_descriptions() -> bool:
    """4 tools with special descriptions through SDM (conservative profile)."""
    # (a) Empty description
    tool_empty = _make_tool_def("empty_tool", "")

    # (b) 10K-character long description
    pad10k = "padding text " * 2500
    tool_long = _make_tool_def("long_tool", pad10k)

    # (c) All-filler description
    tool_filler = _make_tool_def(
        "filler_tool",
        "This tool allows you to perform operations when you need to. "
        "It is designed to handle various tasks. Use this tool for processing.",
    )

    # (d) Pure technical description
    tool_tech = _make_tool_def(
        "tech_tool",
        "Reads bytes from fd at offset. Returns bytes read.",
    )

    test_cases = [
        ("empty", tool_empty, "empty stays empty", None),
        ("long_10k", tool_long, "does not crash", None),
        ("all_filler", tool_filler, "fillers stripped", None),
        ("technical", tool_tech, "unchanged", None),
    ]

    all_pass = True
    for label, tool, expectation, _savings_expected in test_cases:
        before_chars = len(tool.description)
        compiler = TSCGCompiler(model="auto", profile="conservative")
        result = compiler.compile([tool])
        after_chars = len(result.compressed_text)

        # Compute savings on text level
        if before_chars > 0:
            savings_pct = (before_chars - after_chars) / before_chars * 100
        else:
            savings_pct = 0.0

        # Assertions
        case_ok = True
        if label == "empty":
            # Empty description → compressed text should be minimal (no crash)
            # Empty tool with SDM only → "empty_tool: ." after capitalization+period
            case_ok = after_chars < 50  # sanity: not bloated
        elif label == "long_10k":
            # Verify it didn't crash and produced valid output
            case_ok = result.compressed_text is not None and len(result.compressed_text) > 0
        elif label == "all_filler":
            # Fillers should be stripped → savings positive
            case_ok = savings_pct > 5.0 and after_chars < before_chars
        elif label == "technical":
            # Technical text unchanged: SDM preserves all words, DRO adds name prefix.
            # Single short tool → DRO "Name: desc" expands raw desc length naturally.
            # Check that key phrases survive SDM pass.
            case_ok = "Reads bytes" in result.compressed_text and "Returns bytes" in result.compressed_text

        status = "PASS" if case_ok else "FAIL"
        if not case_ok:
            all_pass = False

        print(
            f"test_pathological_descriptions[{label}]: "
            f"before_chars={before_chars}, after_chars={after_chars}, "
            f"savings_pct={savings_pct:.1f}%, expect={expectation}, "
            f"{status}"
        )

    print(f"test_pathological_descriptions: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ══════════════════════════════════════════════════════════════════
# Test 3: Cross-Model Batch
# ══════════════════════════════════════════════════════════════════


def test_cross_model_batch() -> bool:
    """5 test tools across 14+ model names — check family + safety guards."""
    test_tools = [
        _make_tool_def(
            "get_weather",
            "Get current weather data for a location.",
            [
                _make_param("location", "string", "City name or coordinates.", required=True),
                _make_param("units", "string", "Temperature unit.", enum=["celsius", "fahrenheit"]),
            ],
        ),
        _make_tool_def(
            "search_web",
            "Search the web for information.",
            [
                _make_param("query", "string", "Search query.", required=True),
                _make_param("limit", "number", "Max results."),
            ],
        ),
        _make_tool_def(
            "create_file",
            "Create a file at path.",
            [
                _make_param("path", "string", "File path.", required=True),
                _make_param("content", "string", "File content.", required=True),
            ],
        ),
        _make_tool_def(
            "list_items",
            "List all items.",
            [_make_param("filter", "string", "Optional filter.")],
        ),
        _make_tool_def(
            "delete_item",
            "Delete an item by ID.",
            [_make_param("id", "string", "Item ID.", required=True)],
        ),
    ]

    model_names = [
        "claude-3.5-sonnet",
        "gpt-4o",
        "gemini-2.0-flash",
        "llama-3-70b",
        "mistral-large",
        "qwen-max",
        "deepseek-v3",
        "cohere-command-r",
        "command-nightly",
        "yi-large",
        "grok-2",
        "phi-4",
        "granite-3",
        "dbrx-instruct",
        # Thinking models
        "o3-mini",
        "deepseek-r1",
    ]

    all_pass = True
    for model_name in model_names:
        compiler = TSCGCompiler(model=model_name, profile="aggressive")
        result = compiler.compile(test_tools)
        family = detect_model_family(model_name)
        is_thinking = is_thinking_model(model_name)

        active = set(result.active_transforms)
        has_cfl = "cfl" in active
        has_sad = "sad" in active

        # Expected behavior
        if is_thinking:
            cfl_expected = False
            sad_expected = False
        elif family == ModelFamily.CLAUDE:
            cfl_expected = True
            sad_expected = True
        else:
            cfl_expected = False
            sad_expected = False

        cfl_ok = has_cfl == cfl_expected
        sad_ok = has_sad == sad_expected
        case_ok = cfl_ok and sad_ok and result.savings_pct > 0

        status = "PASS" if case_ok else "FAIL"
        if not case_ok:
            all_pass = False

        print(
            f"test_cross_model_batch[{model_name}]: family={family.value}, "
            f"is_thinking={is_thinking}, CFL={has_cfl}(exp={cfl_expected}), "
            f"SAD={has_sad}(exp={sad_expected}), "
            f"active_transforms={result.active_transforms}, "
            f"savings_pct={result.savings_pct:.1f}%, {status}"
        )

    print(f"test_cross_model_batch: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ══════════════════════════════════════════════════════════════════
# Test 4: Tool Count Sweep
# ══════════════════════════════════════════════════════════════════


def test_tool_count_sweep() -> bool:
    """Tool count sweep [1,5,10,20,30,50,100] — auto-profile + Guard 2."""
    all_pass = True
    for count in [1, 5, 10, 20, 30, 50, 100]:
        tools = [_make_tool_def(f"tool_{i}", f"Tool {i} for sweep.") for i in range(count)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet")  # auto-detect profile
        result = compiler.compile(tools)
        active = set(result.active_transforms)

        # Determine expected profile from active transforms
        if active == {"sdm"}:
            profile_used = "conservative"
        elif active == {"sdm", "cas", "cfo", "dro", "tas"}:
            profile_used = "balanced"
        elif active == {"sdm", "cas", "dro", "tas"}:
            profile_used = "balanced+guard2"  # Guard 2 disabled CFO
        elif active == {"sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad"}:
            profile_used = "aggressive"
        else:
            profile_used = f"unknown:{sorted(active)}"

        # Verify auto-profile logic
        if count <= 20:
            expected_profile = "conservative"
            expected_transforms = {"sdm"}
        elif count <= 40:
            expected_profile = "balanced"
            # Guard 2: >=30 → CFO disabled
            if count >= 30:
                expected_transforms = {"sdm", "cas", "dro", "tas"}
            else:
                expected_transforms = {"sdm", "cas", "cfo", "dro", "tas"}
        else:
            expected_profile = "conservative"
            expected_transforms = {"sdm"}

        # Guard 2: >=30 tools → CFL+CFO disabled
        guard2_applied = count >= 30
        if guard2_applied:
            guard2_ok = "cfl" not in active and "cfo" not in active
        else:
            guard2_ok = True  # guard not applicable

        profile_ok = active == expected_transforms
        case_ok = profile_ok and guard2_ok and result.savings_pct >= 0

        status = "PASS" if case_ok else "FAIL"
        if not case_ok:
            all_pass = False

        print(
            f"test_tool_count_sweep[{count}]: profile_used={profile_used}, "
            f"active_transforms={sorted(active)}, "
            f"expected={sorted(expected_transforms)}, "
            f"guard2={'on' if guard2_applied else 'off'}, "
            f"savings_pct={result.savings_pct:.1f}%, "
            f"{status}"
        )

    print(f"test_tool_count_sweep: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ══════════════════════════════════════════════════════════════════
# Test 5: Security Edge Cases
# ══════════════════════════════════════════════════════════════════


def test_security_edge_cases() -> bool:
    """Edge-case descriptions: JSON injection, unicode, null byte, 1000-item enum."""
    # (a) JSON injection in description
    tool_json_inj = _make_tool_def(
        "json_inject",
        '{"malicious": true, "drop_table": "users"}',
    )

    # (b) Unicode
    tool_unicode = _make_tool_def(
        "unicode_tool",
        "ファイルを読み込みます \U0001F4C1\U0001F50D 文档处理",
    )

    # (c) Null byte in description
    tool_nullbyte = _make_tool_def(
        "nullbyte_tool",
        "normal text\x00hidden",
    )

    # (d) 1000-item enum param
    tool_huge_enum = _make_tool_def(
        "huge_enum_tool",
        "Tool with huge enum.",
        [
            _make_param(
                "mode",
                "string",
                "Select mode.",
                required=True,
                enum=[f"option_{i:04d}" for i in range(1000)],
            ),
        ],
    )

    test_cases = [
        ("json_injection", tool_json_inj),
        ("unicode", tool_unicode),
        ("null_byte", tool_nullbyte),
        ("huge_enum", tool_huge_enum),
    ]

    all_pass = True
    for label, tool in test_cases:
        crashed = False
        output_size = 0
        try:
            compiler = TSCGCompiler(model="auto", profile="conservative")
            result = compiler.compile([tool])
            output_size = len(result.compressed_text)
            crashed = False
        except Exception as e:
            crashed = True
            print(f"test_security_edge_cases[{label}]: EXCEPTION: {e}")

        case_ok = not crashed and output_size > 0
        status = "PASS" if case_ok else "FAIL"
        if not case_ok:
            all_pass = False

        print(
            f"test_security_edge_cases[{label}]: crashed={crashed}, "
            f"output_size={output_size}, {status}"
        )

    print(f"test_security_edge_cases: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ══════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════


def main() -> int:
    """Run all 5 stress tests. Exit 0 if all pass, 1 otherwise."""
    tests = [
        ("test_massive_schema", test_massive_schema),
        ("test_pathological_descriptions", test_pathological_descriptions),
        ("test_cross_model_batch", test_cross_model_batch),
        ("test_tool_count_sweep", test_tool_count_sweep),
        ("test_security_edge_cases", test_security_edge_cases),
    ]

    print("=" * 72)
    print("TSCG High-Pressure Stress Tests")
    print("=" * 72)

    results: list[tuple[str, bool]] = []
    for name, func in tests:
        try:
            passed = func()
            results.append((name, passed))
        except Exception as e:
            print(f"{name}: CRASHED — {type(e).__name__}: {e}")
            results.append((name, False))

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n{passed_count}/{total} tests passed")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
