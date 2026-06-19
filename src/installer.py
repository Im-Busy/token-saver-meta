"""
Token Saver Meta — Multi-platform AI agent installer.

7-phase installation pipeline:
  1. BASE LAYER      — inject AGENTS.md token-saver protocol
  2. PLATFORM DETECT — scan project for platform markers
  3. PREREQUISITES   — check node, npm, npx, internet
  4. CGC MCP         — npx codegraph mcp install + config gen
  5. ONE-SHOT TOOLS  — codesight + Repomix
  6. RTK             — binary download + hook init
  7. SUMMARY         — terminal report with per-tool status

Per-tool failure isolation: any tool can fail without aborting the pipeline.
Idempotent: running twice produces the same result.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Callable


def run_phase(phase_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Run a phase, catch ALL exceptions. Never crashes.

    Returns:
        {phase_name: {"status": "ok"|"warn"|"error", "result": ...}}
    """
    try:
        result = fn(*args, **kwargs)
        return {phase_name: {"status": "ok", "result": result}}
    except Exception as e:
        return {phase_name: {"status": "error", "result": str(e)}}


def _collect_phase_result(results: dict[str, Any], phase_output: dict[str, Any]) -> None:
    """Merge a phase's output dict into results. Handles dict and non-dict results."""
    results.update(phase_output)


def main(project_path: Path | None = None) -> dict[str, Any]:
    """Run the full 7-phase installation pipeline.

    Args:
        project_path: Path to the target project. Defaults to cwd.

    Returns:
        Nested dict with all phase results, structured for summary.print_summary().
    """
    if project_path is None:
        project_path = Path.cwd()
    project_path = project_path.resolve()

    results: dict[str, Any] = {}

    # --- Phase 1: Base Layer ---
    from src.config_gen import detect_platforms
    from src.agents_injector import inject_agents_md_section

    platforms = detect_platforms(project_path)
    _collect_phase_result(results, run_phase("base_layer", inject_agents_md_section, project_path, platforms))
    # Normalize base_layer result for summary compatibility
    bl = results.get("base_layer", {}).get("result", {})
    results["base_layer"] = {
        "status": "ok" if bl else "warn",
        "platforms": platforms,
    }

    # --- Phase 2: Platform Detection (record) ---
    results["platforms"] = {"status": "ok", "detected": platforms}

    # --- Phase 3: Prerequisites ---
    from src.prerequisites import check_prerequisites

    _collect_phase_result(results, run_phase("prerequisites", check_prerequisites, project_path))
    pre = results.get("prerequisites", {}).get("result", {})
    results["node_only_fallback"] = pre.get("node_only_fallback", False) if isinstance(pre, dict) else False

    # --- Phase 4: CGC MCP ---
    npx_ok = isinstance(pre, dict) and pre.get("npx", {}).get("status") == "ok"
    if npx_ok:
        from src.cgc_installer import install_cgc

        _collect_phase_result(results, run_phase("cgc", install_cgc, project_path, platforms))
    else:
        results["cgc"] = {"status": "warn", "result": {"status": "warn", "message": "npx not available"}}

    # --- Phase 5: One-Shot Tools ---
    from src.oneshot_installer import install_one_shot_tools

    _collect_phase_result(results, run_phase("oneshot", install_one_shot_tools, project_path))

    # --- Phase 6: RTK ---
    from src.rtk_installer import install_rtk

    _collect_phase_result(results, run_phase("rtk", install_rtk, project_path, platforms))

    # --- Phase 7: Summary ---
    from src.summary import print_summary

    summary_dict = _build_summary(results)
    print_summary(summary_dict)

    return results


def _build_summary(results: dict[str, Any]) -> dict[str, Any]:
    """Build a summary dict compatible with src.summary.print_summary()."""
    intelligence: dict[str, dict[str, Any]] = {}

    # CGC
    cgc_raw = results.get("cgc", {}).get("result", {})
    if isinstance(cgc_raw, dict):
        intelligence["cgc"] = cgc_raw
    else:
        intelligence["cgc"] = {"status": "error", "message": str(cgc_raw)}

    # codesight + repomix
    oneshot_raw = results.get("oneshot", {}).get("result", {})
    if isinstance(oneshot_raw, dict):
        for tool_key in ("codesight", "repomix"):
            intelligence[tool_key] = oneshot_raw.get(tool_key, {"status": "error", "message": "not reported"})
    else:
        intelligence["codesight"] = {"status": "error", "message": str(oneshot_raw)}
        intelligence["repomix"] = {"status": "error", "message": str(oneshot_raw)}

    # RTK
    rtk_raw = results.get("rtk", {}).get("result", {})
    compression: dict[str, dict[str, Any]] = {}
    if isinstance(rtk_raw, dict):
        compression["rtk"] = rtk_raw
    else:
        compression["rtk"] = {"status": "error", "message": str(rtk_raw)}

    return {
        "base_layer": results.get("base_layer", {}),
        "intelligence": intelligence,
        "compression": compression,
        "node_only_fallback": results.get("node_only_fallback", False),
    }


def entry_point() -> None:
    """CLI entry point registered via pyproject.toml [project.scripts]."""
    parser = argparse.ArgumentParser(description="Token Saver Meta v0.1.0")
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="token-saver-meta 0.1.0",
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()

    print("=" * 49)
    print("  Token Saver Meta v0.1.0")
    print("  Token Saving for the Masses")
    print("=" * 49)
    print()

    try:
        main(project_path)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"\nFatal: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
