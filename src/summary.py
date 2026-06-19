"""Terminal summary report formatter for Token Saver Meta installation results."""

_SEP = "-" * 49

_TOOL_LABELS: dict[str, str] = {
    "cgc": "CGC MCP configured",
    "codesight": "codesight → CODESIGHT.md",
    "repomix": "Repomix → repomix-output.txt",
    "rtk": "RTK",
    "contextslim": "ContextSlimAI",
}


def _icon(status: str) -> str:
    return {"ok": "✅", "warn": "⚠️", "skip": "⚠️", "error": "❌"}.get(status, "❓")


def _count_active(results: dict) -> int:
    """Count tools with status='ok' across all sections."""
    count = 0
    for section in ("base_layer", "intelligence", "compression"):
        value = results.get(section, {})
        if section == "base_layer":
            if value.get("status") == "ok":
                count += 1
        elif isinstance(value, dict):
            for tool in value.values():
                if isinstance(tool, dict) and tool.get("status") == "ok":
                    count += 1
    return count


def _count_total(results: dict) -> int:
    """Count all tools across all sections."""
    total = 0
    for section in ("base_layer", "intelligence", "compression"):
        value = results.get(section, {})
        if section == "base_layer":
            total += 1
        elif isinstance(value, dict):
            total += len(value)
    return total


def _format_tool(section: str, key: str, info: dict) -> str:
    """Format a single tool line."""
    icon = _icon(info.get("status", "ok"))
    label = _TOOL_LABELS.get(key, key)

    if key == "rtk" and "version" in info:
        label = f"{label} v{info['version']} (pre-installed)"
    elif section == "base_layer" and "platforms" in info:
        platforms = ", ".join(info["platforms"])
        label = f"AGENTS.md injected ({platforms})"
    elif key == "cgc" and "platforms" in info:
        label = f"CGC MCP configured ({info['platforms']} platforms)"
    elif info.get("status") in ("warn", "skip") and "reason" in info:
        label = f"{label} \u2014 ({info['reason']})"

    return f"  {icon} {label}"


def format_summary(results: dict) -> str:
    """Format installation results as a terminal summary string."""
    lines: list[str] = []
    lines.append(_SEP)
    lines.append("  Token Saver Meta \u2014 Installation Summary")
    lines.append(_SEP)

    # Base Layer
    bl = results.get("base_layer", {})
    lines.append(f"  Base Layer:      {_format_tool('base_layer', 'base_layer', bl)}")

    # Intelligence
    intel = results.get("intelligence", {})
    first = True
    for key, info in intel.items():
        if first:
            lines.append(f"  Intelligence:    {_format_tool('intelligence', key, info)}")
            first = False
        else:
            lines.append(f"                   {_format_tool('intelligence', key, info)}")

    # Compression
    comp = results.get("compression", {})
    first = True
    for key, info in comp.items():
        if first:
            lines.append(f"  Compression:     {_format_tool('compression', key, info)}")
            first = False
        else:
            lines.append(f"                   {_format_tool('compression', key, info)}")

    # Node-only fallback notice
    if results.get("node_only_fallback"):
        lines.append("  \u2139\ufe0f  Node-only mode (Python/uv not found)")

    lines.append(_SEP)

    active = _count_active(results)
    total = _count_total(results)
    lines.append(f"  {active}/{total} tools active. Estimated token savings: ~60%")
    lines.append(_SEP)

    return "\n".join(lines)


def print_summary(results: dict) -> None:
    """Print formatted summary to stdout."""
    print(format_summary(results))
