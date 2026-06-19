"""
Compressor — MCP tool schema ↔ TSCG format conversion and compression.

Provides:
- MCP JSON-RPC tool format ↔ TSCG ToolDef conversion
- Compression pipeline (SDM → CAS → CFO → DRO → TAS)
- Decompression (DRO text → MCP tool dicts)
- Nested schema support (anyOf/oneOf/allOf, nested objects)
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from tscg.core.transforms import (
    ToolDef,
    ParamDef,
    apply_sdm,
    apply_cas,
    apply_cfo,
    apply_dro,
    apply_tas,
)


# ── Format conversion ────────────────────────────────────────────


def mcp_tool_to_tscg(tool: dict[str, Any]) -> ToolDef:
    """Convert a single MCP JSON-RPC tool dict to a TSCG ToolDef.

    Handles MCP format: ``{name, description?, inputSchema: {type, properties?, required?}}``

    Args:
        tool: MCP tool dict from ``tools/list`` response.

    Returns:
        Equivalent ToolDef with parsed parameters.
    """
    name = tool.get("name", "")
    description = tool.get("description", "")
    input_schema = tool.get("inputSchema", {})

    properties = input_schema.get("properties", {}) or {}
    required_list: list[str] = input_schema.get("required", []) or []

    params: list[ParamDef] = []
    for pname, pdef in properties.items():
        # Preserve raw JSON for nested schemas (anyOf/oneOf/allOf, nested objects, items)
        raw = deepcopy(pdef)
        params.append(
            ParamDef(
                name=pname,
                type=pdef.get("type", "string"),
                description=pdef.get("description", ""),
                required=(pname in required_list),
                enum=pdef.get("enum"),
                raw_json=raw,
            )
        )

    return ToolDef(
        name=name,
        description=description,
        parameters=params,
    )


def tscg_to_mcp(tool: ToolDef) -> dict[str, Any]:
    """Convert a TSCG ToolDef back to MCP JSON-RPC tool dict format.

    Preserves all parameter types, descriptions, required flags, and enum values.
    Nested schemas (anyOf/oneOf/allOf) are not preserved in this conversion
    since ToolDef flattens parameters — use the original MCP dict for full fidelity.

    Args:
        tool: TSCG ToolDef instance.

    Returns:
        MCP-compatible tool dict.
    """
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []

    for p in tool.parameters:
        if p.raw_json is not None:
            # Use raw JSON for fidelity — preserves nested schemas, anyOf/oneOf/allOf, etc.
            prop = deepcopy(p.raw_json)
        else:
            prop = {
                "type": p.type,
                "description": p.description,
            }
            if p.enum is not None:
                prop["enum"] = list(p.enum)
        properties[p.name] = prop
        if p.required:
            required.append(p.name)

    result: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }
    return result


# ── Compression / Decompression ──────────────────────────────────


def compress_tools(
    tools: list[dict[str, Any]],
    mode: str = "full",
) -> str:
    """Compress a list of MCP tool schemas into TSCG compressed text.

    Args:
        tools: List of MCP tool dicts.
        mode: Compression mode — ``"full"`` applies SDM+CAS+CFO+DRO+TAS,
              ``"description-only"`` applies SDM only.

    Returns:
        Compressed text string. Empty string for empty input.

    In full mode, the pipeline is: SDM → CAS → CFO → DRO → TAS.
    In description-only mode: SDM → DRO → TAS.
    """
    if not tools:
        return ""

    tool_defs = [mcp_tool_to_tscg(t) for t in tools]

    if mode == "description-only":
        # SDM only for descriptions
        compressed = apply_sdm(tool_defs)
        lines = apply_dro(compressed)
        text = apply_tas(lines)
    else:
        # Full pipeline
        compressed = apply_sdm(tool_defs)
        compressed = apply_cas(compressed)
        compressed = apply_cfo(compressed)
        lines = apply_dro(compressed)
        text = apply_tas(lines)

    return text


def decompress_tools(text: str) -> list[dict[str, Any]]:
    """Decompress TSCG text back into MCP tool dicts.

    Parses DRO-format text (output of compress_tools) and reconstructs
    MCP tool dicts with parameter types, descriptions, and required flags.

    DRO format::

        ToolName: description
          param* (type): description | param (type): description

    Where ``*`` marks required parameters and types may include::

        str, num, bool, arr, obj, string, number, boolean, array, object

    Args:
        text: DRO-formatted compressed text.

    Returns:
        List of MCP-compatible tool dicts. Empty list for empty input.
    """
    if not text.strip():
        return []

    # Reverse type abbreviation mapping
    _REV_TYPE: dict[str, str] = {
        "str": "string",
        "num": "number",
        "bool": "boolean",
        "arr": "array",
        "obj": "object",
    }

    tools: list[dict[str, Any]] = []
    lines = text.split("\n")

    current_tool: dict[str, Any] | None = None
    current_params: list[dict[str, Any]] = []
    current_required: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Blank line between tools — finalize current
            if current_tool is not None:
                current_tool["inputSchema"]["properties"] = _params_to_props(current_params)
                current_tool["inputSchema"]["required"] = current_required
                tools.append(current_tool)
                current_tool = None
                current_params = []
                current_required = []
            continue

        # Tool header: "ToolName: description"
        tool_match = re.match(r"^(\w+):\s*(.*)", stripped)
        if tool_match and not line.startswith(" ") and not line.startswith("  "):
            # Finalize previous tool
            if current_tool is not None:
                current_tool["inputSchema"]["properties"] = _params_to_props(current_params)
                current_tool["inputSchema"]["required"] = current_required
                tools.append(current_tool)
                current_params = []
                current_required = []

            current_tool = {
                "name": tool_match.group(1),
                "description": tool_match.group(2).rstrip("."),
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            }
            continue

        # Parameter line: "  name* (type): description | name (type): description | ..."
        if line.startswith("  "):
            param_text = stripped.strip()
            # Split on " | " to get individual params
            param_segments = param_text.split(" | ")
            for seg in param_segments:
                seg = seg.strip()
                param_match = re.match(
                    r"^(\w+)(\*?)\s*\((\w+)(?::\s*([^)]+))?\)\s*:\s*(.*)$",
                    seg,
                )
                if param_match:
                    pname = param_match.group(1)
                    is_req = param_match.group(2) == "*"
                    ptype_abbrev = param_match.group(3)
                    ptype = _REV_TYPE.get(ptype_abbrev, ptype_abbrev)
                    pdesc = param_match.group(5).rstrip(".")

                    current_params.append({
                        "name": pname,
                        "type": ptype,
                        "description": pdesc,
                    })
                    if is_req and pname not in current_required:
                        current_required.append(pname)
                else:
                    # Simpler fallback: "name* (type): desc" without enum
                    alt_match = re.match(
                        r"^(\w+)(\*?)\s*\((\w+)\)\s*:\s*(.*)$",
                        seg,
                    )
                    if alt_match:
                        pname = alt_match.group(1)
                        is_req = alt_match.group(2) == "*"
                        ptype_abbrev = alt_match.group(3)
                        ptype = _REV_TYPE.get(ptype_abbrev, ptype_abbrev)
                        pdesc = alt_match.group(4).rstrip(".")

                        current_params.append({
                            "name": pname,
                            "type": ptype,
                            "description": pdesc,
                        })
                        if is_req and pname not in current_required:
                            current_required.append(pname)

    # Finalize last tool
    if current_tool is not None:
        current_tool["inputSchema"]["properties"] = _params_to_props(current_params)
        current_tool["inputSchema"]["required"] = current_required
        tools.append(current_tool)

    return tools


def _params_to_props(params: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Convert internal param dicts to MCP properties format."""
    props: dict[str, dict[str, Any]] = {}
    for p in params:
        props[p["name"]] = {
            "type": p["type"],
            "description": p["description"],
        }
    return props
