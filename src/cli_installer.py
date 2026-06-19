"""CLI tools installer (ContextSlimAI)."""

from pathlib import Path
import subprocess


def install_cli_tools(project_path: Path) -> dict:
    """Install CLI wrapper tools (ContextSlimAI)."""
    result = {"contextslimai": {"status": "skip", "message": "npm package not found (not published yet)"}}

    try:
        proc = subprocess.run(
            ["npx", "contextslim", "init"],
            capture_output=True, text=True, timeout=60
        )
        if proc.returncode == 0:
            # Check what files were generated
            generated = []
            for candidate in [".cursorrules", "CLAUDE.md"]:
                if (project_path / candidate).exists():
                    generated.append(candidate)
            result["contextslimai"] = {"status": "ok", "files": generated}
        elif "404" in proc.stderr or "Not found" in proc.stderr:
            result["contextslimai"] = {"status": "warn", "message": "npm package contextslim not found (404)"}
        else:
            result["contextslimai"] = {"status": "warn", "message": proc.stderr.strip()[:200]}
    except subprocess.TimeoutExpired:
        result["contextslimai"] = {"status": "warn", "message": "contextslim init timed out"}
    except FileNotFoundError:
        result["contextslimai"] = {"status": "warn", "message": "npx not available"}
    except Exception as e:
        result["contextslimai"] = {"status": "warn", "message": str(e)}

    return result
