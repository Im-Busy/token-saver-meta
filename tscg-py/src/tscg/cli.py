"""TSCG CLI — compress, estimate, and proxy MCP tool schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from tscg.core.compiler import TSCGCompiler
from tscg.core.transforms import ParamDef, ToolDef
from tscg.proxy.config import ProxyConfig, get_config


def _load_tools(path: str) -> list[dict]:
    """Load tool definitions from a JSON file.

    Accepts either a JSON array of MCP tool dicts or an MCP tools/list response
    dict with a ``tools`` key.
    """
    raw = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON in {path}: {exc}") from exc

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "tools" in data:
        return data["tools"]
    raise click.ClickException(
        f"Expected a JSON array of tools or an object with 'tools' key, got {type(data).__name__}"
    )


def _mcp_dict_to_tooldef(d: dict) -> ToolDef:
    """Convert a single MCP tool dict to a ToolDef."""
    input_schema = d.get("inputSchema", {})
    properties = input_schema.get("properties", {}) or {}
    required_list: list[str] = input_schema.get("required", []) or []

    params: list[ParamDef] = []
    for pname, pdef in properties.items():
        params.append(
            ParamDef(
                name=pname,
                type=pdef.get("type", "string"),
                description=pdef.get("description", ""),
                required=(pname in required_list),
                enum=pdef.get("enum"),
            )
        )

    return ToolDef(
        name=d.get("name", ""),
        description=d.get("description", ""),
        parameters=params,
    )


# ── CLI group ──────────────────────────────────────────────────────


@click.group()
def cli() -> None:
    """Tool Schema Compression Gateway — compress MCP tool schemas."""
    pass  # pragma: no cover — tested via CliRunner


# ── compress ───────────────────────────────────────────────────────


@cli.command()
@click.option(
    "--model",
    default="auto",
    help="Target model for tokenizer alignment (default: auto).",
    show_default=True,
)
@click.option(
    "--profile",
    default=None,
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    help="Compression profile. Auto-detected from tool count if omitted.",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(writable=True),
    help="Write compressed output to file instead of stdout.",
)
@click.argument("tools_file", type=click.Path(exists=True, dir_okay=False))
def compress(model: str, profile: str | None, output: str | None, tools_file: str) -> None:
    """Compress MCP tool schemas from TOOLS_FILE.

    TOOLS_FILE is a JSON file containing an array of MCP tool definitions
    or an MCP tools/list response object with a 'tools' key.
    """
    tools = _load_tools(tools_file)
    if not tools:
        click.echo("No tools found in input file.", err=True)
        sys.exit(1)

    tool_defs = [_mcp_dict_to_tooldef(t) for t in tools]
    compiler = TSCGCompiler(model=model, profile=profile)
    compiled = compiler.compile(tool_defs)

    if output:
        Path(output).write_text(compiled.compressed_text, encoding="utf-8")
        click.echo(f"Compressed {compiled.tool_count} tools → {output}")
    else:
        click.echo(compiled.compressed_text)


# ── estimate ───────────────────────────────────────────────────────


@cli.command()
@click.option(
    "--model",
    default="auto",
    help="Target model for estimation.",
    show_default=True,
)
@click.option(
    "--profile",
    default=None,
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    help="Compression profile. Auto-detected if omitted.",
)
@click.argument("tools_file", type=click.Path(exists=True, dir_okay=False))
def estimate(model: str, profile: str | None, tools_file: str) -> None:
    """Estimate token savings from compressing TOOLS_FILE.

    Prints a summary report with estimated token savings percentage
    and active transforms.
    """
    tools = _load_tools(tools_file)
    if not tools:
        click.echo("No tools found in input file.", err=True)
        sys.exit(1)

    tool_defs = [_mcp_dict_to_tooldef(t) for t in tools]
    compiler = TSCGCompiler(model=model, profile=profile)
    compiled = compiler.compile(tool_defs)

    click.echo(f"Tools: {compiled.tool_count}")
    click.echo(f"Estimated savings: {compiled.savings_pct:.1f}%")
    click.echo(f"Active transforms: {', '.join(compiled.active_transforms) or '(none)'}")


# ── proxy ──────────────────────────────────────────────────────────


@cli.command()
@click.option(
    "--downstream-url",
    default=None,
    help="URL of the downstream MCP server.",
)
@click.option(
    "--model",
    default=None,
    help="Target model (overrides TSCG_MODEL env var).",
)
@click.option(
    "--profile",
    default=None,
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    help="Compression profile (overrides TSCG_PROFILE env var).",
)
def proxy(downstream_url: str | None, model: str | None, profile: str | None) -> None:
    """Start the TSCG MCP proxy (configuration-only mode).

    Prints the resolved configuration. The actual stdio proxy loop
    is deferred to a future integration.
    """
    config = get_config()

    # CLI options override env vars
    final_model = model or config.model
    final_profile = profile or config.profile
    final_downstream = downstream_url or config.downstream_url

    click.echo("TSCG Proxy Configuration")
    click.echo("========================")
    click.echo(f"  Model:          {final_model}")
    click.echo(f"  Profile:        {final_profile or 'auto (by tool count)'}")
    click.echo(f"  Downstream URL: {final_downstream or '(not set)'}")
    click.echo(f"  Max Tools:      {config.max_tools}")

    if not final_downstream:
        click.echo(
            "\nWarning: No downstream URL configured. Set --downstream-url or TSCG_DOWNSTREAM_URL.",
            err=True,
        )
