"""
TSCG transform functions — ported from TypeScript _engine.ts.

All 8 paper operators implemented as pure functions:
  SDM, CAS, CFO, DRO, TAS, CFL, CCP, SAD-F

Each transform preserves algorithmic fidelity with the canonical TS source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Data Types ───────────────────────────────────────────────────


@dataclass
class ParamDef:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    enum: list[str] | None = None
    raw_json: dict[str, object] | None = None


@dataclass
class ToolDef:
    """Tool definition."""
    name: str
    description: str
    parameters: list[ParamDef] = field(default_factory=list)
    usageFrequency: float = 0.5


@dataclass
class OptimizedToolDefs:
    """Result of the optimize pipeline."""
    text: str
    originalTokenEstimate: int
    optimizedTokenEstimate: int
    savingsPercent: float


# ══════════════════════════════════════════════════════════════════
# SDM: Semantic Density Maximization
# ══════════════════════════════════════════════════════════════════

# Filler patterns — VERBATIM port from _engine.ts lines 61-91.
# Each tuple is (regex_pattern, replacement).
# All patterns use re.IGNORECASE to match the JS /gi flag.
# Python re.ASCII ensures \w = [a-zA-Z0-9_] matching JS behavior.

_FILLER_PATTERNS: list[tuple[str, str]] = [
    (r"\bUse this tool when you need to\s*", ""),
    (r"\bUse this (?:tool|function) (?:to|for)\s*", ""),
    (r"\bThis tool (?:allows you to|lets you|enables you to|is used to|can be used to|will)\s*", ""),
    (r"\bYou can use this (?:tool )? ?to\s*", ""),
    (r"\bThis (?:tool|function) (?:is designed|was designed) to\s*", ""),
    (r"\bPlease note that\s*", ""),
    (r"\bNote that\s*", ""),
    (r"\bIt (?:is|can be) (?:useful|helpful) (?:for|when)\s*", ""),
    (r"\bThis is (?:a|the) tool (?:for|that)\s*", ""),
    (r"\bThe (?:value|name|text|content|data|input|output) (?:of |for )?(?:the |a )?", ""),
    (r"\bSpecifies the\s*", ""),
    (r"\bIndicates (?:the|whether)\s*", ""),
    (r"\bDetermines (?:the|whether)\s*", ""),
    (r"\bRepresents (?:the|a)\s*", ""),
    (r"\s*\bif needed\.?\s*$", ""),
    (r"\s*\bif applicable\.?\s*$", ""),
    (r"\s*\bas needed\.?\s*$", ""),
    (r"\s*\bwhen available\.?\s*$", ""),
    (r"\bthat may have changed since your training cutoff\b", ""),
    (r"\bsince (?:the|your) (?:training|knowledge) cutoff\b", ""),
    (r"\bor any (?:other )?(?:current |relevant )?(?:data|information)\b", ""),
    (r"\bor any (?:other )?\w+ that (?:you |might |may )?\w+\b", ""),
    (r"\bto execute\b", ""),
    (r"\bto perform\b", ""),
    (r"\bto carry out\b", ""),
    (r"\s{2,}", " "),
    (r"\s+\.", "."),
    (r",\s*\.", "."),
    (r",\s*,", ","),
    (r"^\s*,\s*", ""),
]


def _strip_filler(text: str) -> str:
    """Strip filler phrases from a text string (SDM core)."""
    result = text
    for pattern, replacement in _FILLER_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE | re.ASCII)
    result = result.strip()
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    if result and not result[-1] in ".!?":
        result += "."
    return result


def apply_sdm(tools: list[ToolDef]) -> list[ToolDef]:
    """Apply SDM: strip filler from tool and parameter descriptions."""
    return [
        ToolDef(
            name=t.name,
            description=_strip_filler(t.description),
            parameters=[
                ParamDef(
                    name=p.name,
                    type=p.type,
                    description=_strip_filler(p.description),
                    required=p.required,
                    enum=p.enum,
                    raw_json=p.raw_json,
                )
                for p in t.parameters
            ],
            usageFrequency=t.usageFrequency,
        )
        for t in tools
    ]


# ══════════════════════════════════════════════════════════════════
# DRO: Delimiter-Role Optimization
# ══════════════════════════════════════════════════════════════════

_TYPE_ABBREV: dict[str, str] = {
    "string": "str",
    "number": "num",
    "boolean": "bool",
    "array": "arr",
    "object": "obj",
}


def apply_dro(tools: list[ToolDef]) -> list[str]:
    """Apply DRO: compact parameter format. Returns list of formatted lines."""
    result: list[str] = []
    for tool in tools:
        param_parts: list[str] = []
        for p in tool.parameters:
            req_mark = "*" if p.required else ""
            type_abbrev = _TYPE_ABBREV.get(p.type, p.type)
            enum_str = f": { '|'.join(p.enum) }" if (p.enum and len(p.enum) > 0) else ""
            type_str = f"{type_abbrev}{enum_str}"
            param_parts.append(f"{p.name}{req_mark} ({type_str}): {p.description}")
        param_line = f"\n  {' | '.join(param_parts)}" if param_parts else ""
        result.append(f"{tool.name}: {tool.description}{param_line}")
    return result


# ══════════════════════════════════════════════════════════════════
# CAS: Causal Access Score — U-shape reorder
# ══════════════════════════════════════════════════════════════════


def apply_cas(tools: list[ToolDef]) -> list[ToolDef]:
    """Apply CAS: U-shape reorder by usage frequency (highest→edges, low→middle)."""
    if len(tools) <= 2:
        return list(tools)

    # Sort by usageFrequency descending, stable by original index
    indexed = [(tool, idx) for idx, tool in enumerate(tools)]
    indexed.sort(key=lambda x: (-(x[0].usageFrequency or 0.5), x[1]))
    sorted_tools = [entry[0] for entry in indexed]

    # Interleave: even indices go left, odd indices go right
    n = len(sorted_tools)
    result: list[ToolDef | None] = [None] * n
    left = 0
    right = n - 1
    for i, tool in enumerate(sorted_tools):
        if i % 2 == 0:
            result[left] = tool
            left += 1
        else:
            result[right] = tool
            right -= 1

    return [t for t in result if t is not None]


# ══════════════════════════════════════════════════════════════════
# TAS: Tokenizer-Aligned Syntax
# ══════════════════════════════════════════════════════════════════


def apply_tas(tool_lines: list[str]) -> str:
    """Apply TAS: BPE-optimized delimiters on DRO output lines."""
    transformed: list[str] = []
    for line in tool_lines:
        result = line
        result = result.replace("=>", ":")
        result = result.replace("-->", ":")
        result = re.sub(r"\s*\|\s*", " | ", result)
        result = re.sub(r":\s{2,}", ": ", result)
        transformed.append(result)
    return "\n".join(transformed)


# ══════════════════════════════════════════════════════════════════
# CFO: Causal-Forward Ordering
# ══════════════════════════════════════════════════════════════════

_CFO_READ_PREFIXES = [
    "get_", "read_", "list_", "search_", "find_", "query_", "fetch_", "view_",
    "describe_", "show_", "load_", "retrieve_", "check_", "lookup_",
]

_CFO_WRITE_PREFIXES = [
    "create_", "send_", "update_", "delete_", "write_", "execute_",
    "modify_", "remove_", "post_", "put_", "patch_", "destroy_",
    "insert_", "publish_", "upload_", "save_", "run_",
]

_CFO_READ_VERBS = {
    "get", "read", "list", "search", "find", "query", "fetch", "retrieve",
}

_CFO_WRITE_VERBS = {
    "create", "send", "update", "delete", "write", "execute", "modify", "remove", "run",
}


def _classify_cfo(tool: ToolDef) -> str:
    """Classify a tool as 'read', 'write', or 'transform' for CFO."""
    name = tool.name.lower()
    for prefix in _CFO_READ_PREFIXES:
        if name.startswith(prefix):
            return "read"
    for prefix in _CFO_WRITE_PREFIXES:
        if name.startswith(prefix):
            return "write"
    # Fallback: inspect first verb of description
    first_word = tool.description.strip().lower().split()[0] if tool.description.strip() else ""
    if first_word in _CFO_READ_VERBS:
        return "read"
    if first_word in _CFO_WRITE_VERBS:
        return "write"
    return "transform"


def apply_cfo(tools: list[ToolDef]) -> list[ToolDef]:
    """Apply CFO: reorder tools READ → TRANSFORM → WRITE. Identity if all same class."""
    if len(tools) <= 1:
        return list(tools)

    reads: list[ToolDef] = []
    transforms: list[ToolDef] = []
    writes: list[ToolDef] = []

    for t in tools:
        cls = _classify_cfo(t)
        if cls == "read":
            reads.append(t)
        elif cls == "write":
            writes.append(t)
        else:
            transforms.append(t)

    # Identity if all tools share one class
    if len(reads) == len(tools) or len(transforms) == len(tools) or len(writes) == len(tools):
        return list(tools)

    return reads + transforms + writes


# ══════════════════════════════════════════════════════════════════
# CFL: Constraint-First Layout
# ══════════════════════════════════════════════════════════════════


def apply_cfl(text: str) -> str:
    """Apply CFL: prepend [ANSWER:function_call] attention-sink token. Claude-only."""
    return f"[ANSWER:function_call]\n{text}"


# ══════════════════════════════════════════════════════════════════
# CCP: Causal Closure Principle
# ══════════════════════════════════════════════════════════════════


def apply_ccp(text: str, tools: list[ToolDef]) -> str:
    """Apply CCP: append [CLOSURE:tool1(req1,req2),tool2(),...] recap."""
    if not tools:
        return text
    entries = [
        f"{t.name}({ ','.join(p.name for p in t.parameters if p.required) })"
        for t in tools
    ]
    return f"{text}\n[CLOSURE:{ ','.join(entries) }]"


# ══════════════════════════════════════════════════════════════════
# SAD-F: Selective Anchor Duplication with Fragility Weighting
# ══════════════════════════════════════════════════════════════════


def apply_sad(text: str, topK: int = 4) -> str:
    """Apply SAD-F: extract top-K anchors from DRO-compressed text. Claude-only."""
    anchors: list[str] = []

    # Strategy 1: Extract tool names from DRO format lines
    # DRO format: "ToolName: description\n  param* (type): desc | ..."
    lines = text.split("\n")
    for line in lines:
        if re.match(r"^\w+:", line) and not line.startswith(" "):
            m = re.match(r"^(\w+):", line)
            if m:
                anchors.append(m.group(1))

    # Strategy 2: Extract required params (marked with *)
    for m in re.finditer(r"\b(\w+)\*\s*\(", text):
        anchors.append(f"{m.group(1)}*")

    # Strategy 3: Extract enum values (format: "type: val1|val2|val3")
    for m in re.finditer(r"\b\w+:\s*[\w]+(?:\|[\w]+)+", text):
        anchors.append(re.sub(r"\s+", "", m.group(0)))

    if not anchors:
        return text

    # Deduplicate preserving order, take top-K
    seen: set[str] = set()
    unique: list[str] = []
    for a in anchors:
        if a not in seen:
            seen.add(a)
            unique.append(a)

    top = unique[:topK]
    return f"{text}\n[ANCHOR:{ ','.join(top) }]"


# ══════════════════════════════════════════════════════════════════
# Full pipeline — optimize_tool_definitions
# ══════════════════════════════════════════════════════════════════


def optimize_tool_definitions(
    tools: list[ToolDef],
    *,
    useSDM: bool = True,
    useCAS: bool = True,
    useCFO: bool = True,
    useDRO: bool = True,
    useTAS: bool = True,
    useCFL: bool = False,
    useSAD: bool = False,
    useCCP: bool = False,
    sadTopK: int = 4,
) -> OptimizedToolDefs:
    """Execute the full TSCG compression pipeline.

    Execution order: SDM → CAS → CFO → DRO → TAS → CFL → SAD-F → CCP
    """
    # Original token estimate (raw format)
    original_lines: list[str] = []
    for tool in tools:
        original_lines.append(f"Tool: {tool.name}")
        original_lines.append(f"Description: {tool.description}")
        original_lines.append("Parameters:")
        for p in tool.parameters:
            req_str = " (required)" if p.required else " (optional)"
            enum_str = f" Allowed values: {', '.join(p.enum)}." if p.enum else ""
            original_lines.append(f"  - {p.name} ({p.type}){req_str}: {p.description}{enum_str}")
        original_lines.append("")
    original_text = "\n".join(original_lines)
    original_token_estimate = -(-len(original_text) // 4)  # ceil division

    processed = list(tools)
    if useSDM:
        processed = apply_sdm(processed)
    if useCAS:
        processed = apply_cas(processed)
    if useCFO:
        processed = apply_cfo(processed)

    if useDRO:
        tool_lines = apply_dro(processed)
    else:
        tool_lines = []
        for tool in processed:
            params_lines = "\n".join(
                f"  - {p.name} ({p.type}){' (required)' if p.required else ' (optional)'}: {p.description}"
                + (f" Allowed values: {', '.join(p.enum)}." if p.enum else "")
                for p in tool.parameters
            )
            tool_lines.append(f"{tool.name}: {tool.description}\n{params_lines}")

    if useTAS:
        text = apply_tas(tool_lines)
    else:
        text = "\n\n".join(tool_lines)

    if useCFL:
        text = apply_cfl(text)

    if useSAD:
        text = apply_sad(text, sadTopK)

    if useCCP:
        text = apply_ccp(text, processed)

    optimized_token_estimate = -(-len(text) // 4)  # ceil division
    savings_percent = (
        round(((original_token_estimate - optimized_token_estimate) / original_token_estimate) * 1000) / 10
        if original_token_estimate > 0
        else 0.0
    )

    return OptimizedToolDefs(
        text=text,
        originalTokenEstimate=original_token_estimate,
        optimizedTokenEstimate=optimized_token_estimate,
        savingsPercent=savings_percent,
    )
