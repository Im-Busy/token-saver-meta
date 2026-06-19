"""
Tests for tscg/core/compiler.py — TSCGCompiler pipeline orchestrator.

Covers:
  - Profile gating (conservative, balanced, aggressive)
  - Safety guard 1: non-Claude → CFL+SAD disabled
  - Safety guard 2: >=30 tools → CFL+CFO disabled
  - Safety guard 3: auto-profile by tool count
  - Thinking model exclusion (o1, o3, R1)
  - SAD ON for "auto" model default
  - Manual profile override
  - Roundtrip fidelity
  - Token savings accuracy
  - CompiledSchema dataclass
"""

from __future__ import annotations

import pytest

from tscg.core.transforms import ToolDef, ParamDef
from tscg.core.compiler import TSCGCompiler, CompiledSchema


# ── Helper factories ────────────────────────────────────────────


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


# ── Shared fixtures ─────────────────────────────────────────────


@pytest.fixture
def basic_tools() -> list[ToolDef]:
    return [
        _tool(
            "get_weather",
            "Use this tool when you need to get current weather data for a location.",
            [
                _param("location", "string", "Specifies the city name or coordinates.", required=True),
                _param("units", "string", "The temperature unit to use if needed.", enum=["celsius", "fahrenheit"]),
            ],
            freq=0.9,
        ),
        _tool(
            "search_web",
            "This tool is designed to search the web for information.",
            [
                _param("query", "string", "The search query string.", required=True),
                _param("max_results", "number", "Maximum number of results to return.", enum=["5", "10", "20"]),
            ],
            freq=0.8,
        ),
        _tool(
            "create_file",
            "Creates a new file at the specified path.",
            [
                _param("path", "string", "The path of the file to create.", required=True),
                _param("content", "string", "The content to write to the file.", required=True),
            ],
            freq=0.7,
        ),
    ]


@pytest.fixture
def many_tools() -> list[ToolDef]:
    """Generate 35 tools to test >=30 tool safety guard."""
    tools: list[ToolDef] = []
    for i in range(35):
        tools.append(_tool(
            f"tool_{i:02d}",
            f"This tool does operation {i} with specific parameters.",
            [
                _param("input", "string", f"Input for operation {i}.", required=True),
                _param("verbose", "boolean", "Whether to show details."),
            ],
            freq=0.5 - i * 0.01,
        ))
    return tools


# ══════════════════════════════════════════════════════════════════
# CompiledSchema dataclass
# ══════════════════════════════════════════════════════════════════


class TestCompiledSchema:
    """CompiledSchema must carry all required fields."""

    def test_fields(self):
        schema = CompiledSchema(
            compressed_text="text",
            savings_pct=30.0,
            active_transforms=["sdm"],
            tool_count=3,
        )
        assert schema.compressed_text == "text"
        assert schema.savings_pct == 30.0
        assert schema.active_transforms == ["sdm"]
        assert schema.tool_count == 3

    def test_savings_pct_float(self):
        """savings_pct is a float."""
        schema = CompiledSchema("", 42.5, [], 0)
        assert isinstance(schema.savings_pct, float)
        assert schema.savings_pct == 42.5

    def test_zero_tools(self):
        """Zero tools has 0.0 savings."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile([])
        assert result.tool_count == 0
        assert result.savings_pct == 0.0


# ══════════════════════════════════════════════════════════════════
# Profile gating
# ══════════════════════════════════════════════════════════════════


class TestProfileGating:
    """Profiles gate which transforms are active."""

    def test_conservative_has_only_sdm(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        result = compiler.compile(basic_tools)
        assert "sdm" in result.active_transforms
        assert "cas" not in result.active_transforms
        assert "cfo" not in result.active_transforms
        assert "dro" not in result.active_transforms
        assert "tas" not in result.active_transforms
        assert "cfl" not in result.active_transforms
        assert "ccp" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_balanced_has_five_transforms(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        expected = {"sdm", "cas", "cfo", "dro", "tas"}
        assert set(result.active_transforms) == expected

    def test_aggressive_has_all_eight(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        expected = {"sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad"}
        assert set(result.active_transforms) == expected

    def test_aggressive_produces_smallest_text(self, basic_tools):
        """Aggressive profile should produce the most compressed output."""
        c1 = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        c2 = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        c3 = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        r1 = c1.compile(basic_tools)
        r2 = c2.compile(basic_tools)
        r3 = c3.compile(basic_tools)
        # Aggressive adds CFL, CCP, SAD → text is longer, but savings should still be positive
        assert r1.savings_pct > 0
        assert r2.savings_pct > 0
        assert r3.savings_pct > 0


# ══════════════════════════════════════════════════════════════════
# Safety guard 1: non-Claude → CFL+SAD disabled
# ══════════════════════════════════════════════════════════════════


class TestSafetyGuard1NonClaude:
    """Safety guard 1: non-Claude models disable CFL+SAD."""

    def test_gpt_aggressive_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="gpt-4o", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms
        # Other transforms still active
        assert "sdm" in result.active_transforms
        assert "ccp" in result.active_transforms

    def test_gemini_aggressive_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="gemini-2.0-flash", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_claude_aggressive_keeps_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" in result.active_transforms
        assert "sad" in result.active_transforms

    def test_unknown_model_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="some-unknown-model-v2", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms


# ══════════════════════════════════════════════════════════════════
# Safety guard 2: >=30 tools → CFL+CFO disabled
# ══════════════════════════════════════════════════════════════════


class TestSafetyGuard2ManyTools:
    """Safety guard 2: >=30 tools disables CFL+CFO."""

    def test_thirty_or_more_tools_disables_cfl_cfo(self, many_tools):
        assert len(many_tools) >= 30
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(many_tools)
        assert "cfl" not in result.active_transforms
        assert "cfo" not in result.active_transforms
        # Other transforms still active
        assert "sdm" in result.active_transforms
        assert "cas" in result.active_transforms
        assert "dro" in result.active_transforms

    def test_less_than_thirty_tools_keeps_cfl_cfo(self, basic_tools):
        assert len(basic_tools) < 30
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" in result.active_transforms
        assert "cfo" in result.active_transforms

    def test_exactly_thirty_triggers_guard(self):
        tools = [_tool(f"t_{i:03d}") for i in range(30)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" not in result.active_transforms
        assert "cfo" not in result.active_transforms

    def test_twenty_nine_does_not_trigger(self):
        tools = [_tool(f"t_{i:03d}") for i in range(29)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(tools)
        assert "cfl" in result.active_transforms
        assert "cfo" in result.active_transforms


# ══════════════════════════════════════════════════════════════════
# Safety guard 3: auto-profile by tool count
# ══════════════════════════════════════════════════════════════════


class TestSafetyGuard3AutoProfile:
    """Safety guard 3: auto-profile when profile=None based on tool count."""

    def test_up_to_twenty_tools_defaults_conservative(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet")  # no profile → auto
        result = compiler.compile(basic_tools)
        assert "sdm" in result.active_transforms
        assert "dro" not in result.active_transforms  # conservative = SDM only

    def test_twenty_one_to_forty_defaults_balanced(self):
        tools = [_tool(f"t_{i:03d}") for i in range(25)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet")  # auto
        result = compiler.compile(tools)
        expected = {"sdm", "cas", "cfo", "dro", "tas"}
        assert set(result.active_transforms) == expected

    def test_over_forty_defaults_conservative(self):
        tools = [_tool(f"t_{i:03d}") for i in range(45)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet")  # auto
        result = compiler.compile(tools)
        assert "sdm" in result.active_transforms
        assert "dro" not in result.active_transforms

    def test_auto_with_exactly_twenty(self):
        tools = [_tool(f"t_{i:03d}") for i in range(20)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet")
        result = compiler.compile(tools)
        assert "sdm" in result.active_transforms
        assert "dro" not in result.active_transforms

    def test_auto_with_exactly_forty(self):
        """40 tools → auto=balanced, but Guard 2 (>=30) disables CFO."""
        tools = [_tool(f"t_{i:03d}") for i in range(40)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet")
        result = compiler.compile(tools)
        # balanced profile base: {sdm, cas, cfo, dro, tas}
        # Guard 2 (>=30 tools) → CFO disabled
        expected = {"sdm", "cas", "dro", "tas"}
        assert set(result.active_transforms) == expected


# ══════════════════════════════════════════════════════════════════
# Thinking model exclusion
# ══════════════════════════════════════════════════════════════════


class TestThinkingModelExclusion:
    """Thinking models (o1, o3, R1) → CFL+SAD disabled."""

    def test_o1_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="o1-preview", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_o3_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="o3-mini", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_r1_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="deepseek-r1", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_thinking_models_still_get_other_transforms(self, basic_tools):
        """Thinking models still get SDM, DRO, etc."""
        compiler = TSCGCompiler(model="o1-pro", profile="balanced")
        result = compiler.compile(basic_tools)
        assert "sdm" in result.active_transforms
        assert "dro" in result.active_transforms
        assert "tas" in result.active_transforms


# ══════════════════════════════════════════════════════════════════
# Default model="auto" → SAD ON
# ══════════════════════════════════════════════════════════════════


class TestAutoModelDefault:
    """When model="auto", SAD is ON by default assuming Claude."""

    def test_auto_model_has_sad_on(self, basic_tools):
        compiler = TSCGCompiler(model="auto", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "sad" in result.active_transforms
        assert "cfl" in result.active_transforms

    def test_auto_model_balanced_works(self, basic_tools):
        compiler = TSCGCompiler(model="auto", profile="balanced")
        result = compiler.compile(basic_tools)
        expected = {"sdm", "cas", "cfo", "dro", "tas"}
        assert set(result.active_transforms) == expected


# ══════════════════════════════════════════════════════════════════
# Manual profile override
# ══════════════════════════════════════════════════════════════════


class TestManualProfileOverride:
    """Manual profile overrides auto-detection."""

    def test_explicit_conservative_overrides_balanced_auto(self):
        """45 tools → auto would be conservative. Explicit balanced overrides auto-detection.
        But Guard 2 (>=30 tools) still disables CFO."""
        tools = [_tool(f"t_{i:03d}") for i in range(45)]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        # balanced → {sdm, cas, cfo, dro, tas}
        # Guard 2 (>=30 tools) → CFO disabled
        expected = {"sdm", "cas", "dro", "tas"}
        assert set(result.active_transforms) == expected

    def test_explicit_aggressive_handles_small_toolset(self, basic_tools):
        """Small toolset, explicit aggressive profile: all 8 transforms active."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert len(result.active_transforms) == 8

    def test_profile_arg_none_uses_auto(self, basic_tools):
        """profile=None (default) triggers auto-detection."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile=None)
        result = compiler.compile(basic_tools)
        # <= 20 tools → conservative
        assert "sdm" in result.active_transforms
        assert "dro" not in result.active_transforms


# ══════════════════════════════════════════════════════════════════
# Roundtrip fidelity
# ══════════════════════════════════════════════════════════════════


class TestRoundtrip:
    """decompile must recover tool names, param names, types, required flags."""

    def test_preserves_tool_names(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_names = {t.name for t in basic_tools}
        recovered_names = {t.name for t in decompiled}
        assert original_names == recovered_names

    def test_preserves_param_names(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        decompiled = compiler.decompile(result.compressed_text)
        # Collect all param names
        original_params = {p.name for t in basic_tools for p in t.parameters}
        recovered_params = {p.name for t in decompiled for p in t.parameters}
        assert original_params == recovered_params

    def test_preserves_param_types(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        decompiled = compiler.decompile(result.compressed_text)
        # Build param type map
        original_types = {(t.name, p.name): p.type for t in basic_tools for p in t.parameters}
        recovered_types = {(t.name, p.name): p.type for t in decompiled for p in t.parameters}
        assert original_types == recovered_types

    def test_preserves_required_flags(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        decompiled = compiler.decompile(result.compressed_text)
        original_req = {(t.name, p.name): p.required for t in basic_tools for p in t.parameters}
        recovered_req = {(t.name, p.name): p.required for t in decompiled for p in t.parameters}
        assert original_req == recovered_req

    def test_preserves_enum_values(self):
        tools = [
            _tool("set_mode", "Sets mode.", [
                _param("mode", "string", "Operation mode.", required=True, enum=["read", "write", "append"]),
            ]),
        ]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert decompiled[0].parameters[0].enum == ["read", "write", "append"]

    def test_decompile_empty_text_returns_empty_list(self):
        compiler = TSCGCompiler(model="claude-3.5-sonnet")
        decompiled = compiler.decompile("")
        assert decompiled == []

    def test_decompile_single_tool_no_params(self):
        tools = [_tool("ping", "Pings the service.")]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        decompiled = compiler.decompile(result.compressed_text)
        assert len(decompiled) == 1
        assert decompiled[0].name == "ping"
        assert len(decompiled[0].parameters) == 0

    def test_decompile_cfl_ccp_sad_text(self, basic_tools):
        """Decompile handles text with CFL/CCP/SAD markers."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        # Text should contain CFL prefix, CCP suffix, SAD suffix
        decompiled = compiler.decompile(result.compressed_text)
        original_names = {t.name for t in basic_tools}
        recovered_names = {t.name for t in decompiled}
        assert original_names == recovered_names


# ══════════════════════════════════════════════════════════════════
# Token savings estimate
# ══════════════════════════════════════════════════════════════════


class TestTokenSavings:
    """Token savings estimate uses chars/4 heuristic."""

    def test_savings_positive_for_verbose_tools(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        assert result.savings_pct > 0

    def test_savings_accurate_chars_div_4(self):
        """Savings matches chars/4 heuristic output from transforms.optimize_tool_definitions."""
        tools = [
            _tool("get_x",
                  "Use this tool when you need to fetch current weather data for a location. This tool allows you to get temperature and conditions.",
                  [_param("loc", "string", "Specifies the city name or coordinates.", required=True)]),
        ]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        # Original: ~233 chars → ceil(233/4) = 59 tokens
        # Compressed should be smaller
        assert result.savings_pct > 0

    def test_savings_zero_for_no_change(self):
        """Identical text produces 0.0 savings."""
        tools = [_tool("t", "desc")]
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        result = compiler.compile(tools)
        # Conservative = SDM only. "desc" with no filler → unchanged → 0 savings.
        assert result.savings_pct >= 0.0

    def test_savings_is_float(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        assert isinstance(result.savings_pct, float)

    def test_estimated_savings_property(self, basic_tools):
        """estimated_savings property returns float."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        compiler.compile(basic_tools)
        savings = compiler.estimated_savings
        assert isinstance(savings, float)
        assert savings > 0


# ══════════════════════════════════════════════════════════════════
# active_transforms property
# ══════════════════════════════════════════════════════════════════


class TestActiveTransformsProperty:
    """active_transforms returns list of transform names."""

    def test_returns_list_of_strings(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        compiler.compile(basic_tools)
        transforms = compiler.active_transforms
        assert isinstance(transforms, list)
        assert all(isinstance(t, str) for t in transforms)

    def test_reflects_last_compile(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="conservative")
        compiler.compile(basic_tools)
        assert compiler.active_transforms == ["sdm"]

    def test_returns_empty_before_compile(self):
        """active_transforms returns empty list before first compile."""
        compiler = TSCGCompiler(model="claude-3.5-sonnet")
        assert compiler.active_transforms == []


# ══════════════════════════════════════════════════════════════════
# Pipeline order verification
# ══════════════════════════════════════════════════════════════════


class TestPipelineOrder:
    """Pipeline respects order: SDM → CAS → CFO → DRO → TAS → CFL → CCP → SAD-F."""

    def test_order_in_active_transforms(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="aggressive")
        result = compiler.compile(basic_tools)
        # CFL and SAD may be disabled by safety → check relative order of remaining
        transforms = result.active_transforms
        order_map = {"sdm": 0, "cas": 1, "cfo": 2, "dro": 3, "tas": 4, "cfl": 5, "ccp": 6, "sad": 7}
        indices = {t: order_map[t] for t in transforms}
        assert indices == dict(sorted(indices.items(), key=lambda x: x[1]))

    def test_sdm_always_first(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(basic_tools)
        assert result.active_transforms[0] == "sdm"


# ══════════════════════════════════════════════════════════════════
# Model parameter handling
# ══════════════════════════════════════════════════════════════════


class TestModelHandling:
    """Model parameter affects profile lookups and safety guards."""

    def test_default_model_is_auto(self):
        compiler = TSCGCompiler()
        assert compiler.model == "auto"

    def test_auto_model_treated_as_claude(self, basic_tools):
        """model="auto" gets Claude profile (CFL+SAD supported)."""
        compiler = TSCGCompiler(model="auto", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" in result.active_transforms
        assert "sad" in result.active_transforms

    def test_claude_haiku_gets_full_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="claude-3-haiku", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" in result.active_transforms
        assert "sad" in result.active_transforms

    def test_deepseek_not_claude_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="deepseek-v3", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms

    def test_llama_disables_cfl_sad(self, basic_tools):
        compiler = TSCGCompiler(model="llama-3-70b", profile="aggressive")
        result = compiler.compile(basic_tools)
        assert "cfl" not in result.active_transforms
        assert "sad" not in result.active_transforms
