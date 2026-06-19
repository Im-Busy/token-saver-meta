"""CGC (CodeGraphContext) installer — Node.js MCP server via npx."""
from pathlib import Path
import subprocess
import shutil

from src import config_gen


def install_cgc(project_path: Path, platforms: list[str]) -> dict:
    """Install CGC MCP server per platform. Returns structured result.

    Returns:
        dict with keys: status("ok"|"warn"|"error"|"skip"),
        platforms({pid: {"status": ..., "message": ...}}), message(str).
    """
    # 1. npx availability
    if not shutil.which("npx"):
        return {
            "status": "warn", "platforms": {},
            "message": "npx not found. Install Node.js >= 18.",
        }

    # 2. CGC accessibility via npx
    try:
        result = subprocess.run(
            ["npx", "-y", "codegraph", "--version"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {
                "status": "warn", "platforms": {},
                "message": "CGC not available via npx.",
            }
    except FileNotFoundError:
        return {
            "status": "warn", "platforms": {},
            "message": "npx not found. Install Node.js >= 18.",
        }
    except Exception:
        return {
            "status": "warn", "platforms": {},
            "message": "CGC not available via npx.",
        }

    # 3. Platform check
    if not platforms:
        return {
            "status": "skip", "platforms": {},
            "message": "No platforms detected.",
        }

    # 4. Per-platform config generation (failure-isolated)
    platforms_result: dict = {}
    has_ok = False
    has_error = False

    for platform_id in platforms:
        try:
            config = config_gen.generate_cgc_only_config(platform_id, str(project_path))
            if config is None:
                platforms_result[platform_id] = {
                    "status": "error",
                    "message": f"Unknown platform: {platform_id}",
                }
                has_error = True
                continue

            cfg_status, cfg_message = config_gen.write_mcp_config(
                platform_id, project_path, force=False,
            )
            status_map = {
                "created": "ok", "merged": "ok",
                "skipped": "skipped", "manual": "error", "error": "error",
            }
            mapped = status_map.get(cfg_status, "error")
            platforms_result[platform_id] = {"status": mapped, "message": cfg_message}

            if mapped == "ok":
                has_ok = True
            elif mapped == "error":
                has_error = True
        except Exception as exc:
            platforms_result[platform_id] = {"status": "error", "message": str(exc)}
            has_error = True

    # 5. Aggregate status
    if has_error and has_ok:
        overall = "warn"
    elif has_error:
        overall = "error"
    elif has_ok:
        overall = "ok"
    else:
        overall = "skip"

    ok_count = sum(1 for v in platforms_result.values() if v["status"] == "ok")

    return {
        "status": overall,
        "platforms": platforms_result,
        "message": f"CGC configured for {ok_count}/{len(platforms)} platforms",
    }
