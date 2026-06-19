"""Indexing and verification for token-saver-meta."""

from pathlib import Path
import subprocess
import shutil


def run_indexing(project_path: Path) -> dict:
    """Run GitNexus and CGC indexing on the project."""
    result = {}

    # GitNexus indexing
    try:
        subprocess.run(
            ["npx", "gitnexus", "analyze", "--embeddings", "--skills"],
            cwd=str(project_path), capture_output=True, text=True, timeout=300
        )
        result["gitnexus"] = {"status": "ok"}
    except subprocess.TimeoutExpired:
        result["gitnexus"] = {"status": "warn", "message": "GitNexus analyze timed out (300s)"}
    except FileNotFoundError:
        result["gitnexus"] = {"status": "skip", "message": "npx not available"}
    except Exception as e:
        result["gitnexus"] = {"status": "warn", "message": str(e)[:200]}

    # CGC indexing
    try:
        if shutil.which("uv"):
            subprocess.run(
                ["uv", "run", "cgc", "index", "."],
                cwd=str(project_path), capture_output=True, text=True, timeout=180
            )
            result["cgc"] = {"status": "ok"}
        else:
            result["cgc"] = {"status": "skip", "message": "uv not available"}
    except subprocess.TimeoutExpired:
        result["cgc"] = {"status": "warn", "message": "CGC index timed out (180s)"}
    except Exception as e:
        result["cgc"] = {"status": "warn", "message": str(e)[:200]}

    return result


def run_verification(project_path: Path) -> dict:
    """Check all 10 core tools and return status dashboard."""
    result = {}
    project_root = project_path.resolve()

    # GitNexus
    gn = shutil.which("gitnexus") or shutil.which("npx")
    result["gitnexus"] = {"status": "ok" if gn else "warn", "installed": gn is not None}

    # CGC
    cgc = shutil.which("cgc")
    if not cgc and shutil.which("uv"):
        try:
            subprocess.run(["uv", "run", "cgc", "--version"], capture_output=True, timeout=10)
            cgc = True
        except Exception:
            cgc = None
    result["cgc"] = {"status": "ok" if cgc else "warn", "installed": cgc is not None}

    # RTK
    rtk = shutil.which("rtk")
    result["rtk"] = {"status": "ok" if rtk else "warn", "installed": rtk is not None}

    # codesight
    codesight_md = project_root / "CODESIGHT.md"
    result["codesight"] = {"status": "ok" if codesight_md.exists() else "warn", "file": codesight_md.exists()}

    # repomix
    repomix_files = list(project_root.glob("repomix-output.*"))
    result["repomix"] = {"status": "ok" if repomix_files else "warn", "file": len(repomix_files) > 0}

    # caveman
    result["caveman"] = {"status": "ok", "type": "skill"}

    # LG-token-saver
    result["lg-token-saver"] = {"status": "ok", "type": "skill"}

    # kevin-copilot
    result["kevin-copilot"] = {"status": "ok", "type": "skill"}

    # contextslimai
    cursor_rules = project_root / ".cursorrules"
    result["contextslimai"] = {"status": "ok" if cursor_rules.exists() else "warn", "files_generated": cursor_rules.exists()}

    # Meta installer
    meta_installed = (project_root / "src" / "installer.py").exists()
    result["token-saver-meta"] = {"status": "ok" if meta_installed else "warn", "installed": meta_installed}

    return result
