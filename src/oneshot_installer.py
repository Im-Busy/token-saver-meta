"""One-shot CLI tools installer (codesight, Repomix)."""

from pathlib import Path
import shutil
import subprocess


def _git_latest_commit_timestamp(project_path: Path) -> float | None:
    """Get timestamp of latest git commit. Returns None if not a git repo or git unavailable."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10,
            cwd=str(project_path),
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _check_staleness(file_path: Path, project_path: Path) -> str | None:
    """If file exists and is older than latest git commit, return warning message."""
    if not file_path.exists():
        return None
    commit_ts = _git_latest_commit_timestamp(project_path)
    if commit_ts is None:
        return None
    if file_path.stat().st_mtime < commit_ts:
        return f"existing {file_path.name} is older than latest commit (may be stale)"
    return None


def _update_gitignore(project_path: Path, entries: list[str]) -> bool:
    """Add entries to .gitignore if not present. Returns True if changes made."""
    gitignore = project_path / ".gitignore"
    if not gitignore.exists():
        return False
    content = gitignore.read_text(encoding="utf-8")
    lines = content.splitlines()
    changed = False
    for entry in entries:
        if entry not in lines:
            lines.append(entry)
            changed = True
    if changed:
        gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def install_one_shot_tools(project_path: Path) -> dict:
    """Run one-shot CLI tools to generate context files (CODESIGHT.md, repomix-output.*)."""
    # Pre-check: npx availability
    if shutil.which("npx") is None:
        return {
            "codesight": {"status": "warn", "message": "npx not found in PATH"},
            "repomix": {"status": "warn", "message": "npx not found in PATH"},
            "gitignore_updated": False,
        }

    result: dict = {}

    # --- codesight ---
    codesight_out = project_path / "CODESIGHT.md"
    if codesight_out.exists():
        stale_msg = _check_staleness(codesight_out, project_path)
        msg = "CODESIGHT.md already exists"
        if stale_msg:
            result["codesight"] = {"status": "warn", "message": f"{msg} — {stale_msg}"}
        else:
            result["codesight"] = {"status": "skip", "message": msg}
    else:
        try:
            subprocess.run(
                ["npx", "-y", "codesight"],
                capture_output=True, text=True, timeout=180,
                cwd=str(project_path),
            )
            if codesight_out.exists() or (project_path / ".codesight").exists():
                result["codesight"] = {"status": "ok", "message": "CODESIGHT.md generated"}
            else:
                result["codesight"] = {"status": "warn", "message": "codesight ran but no output found"}
        except subprocess.TimeoutExpired:
            result["codesight"] = {"status": "warn", "message": "codesight timed out (180s)"}
        except FileNotFoundError:
            result["codesight"] = {"status": "warn", "message": "npx not available"}

    # --- Repomix ---
    repomix_files = list(project_path.glob("repomix-output.*"))
    if repomix_files:
        existing = repomix_files[0]
        stale_msg = _check_staleness(existing, project_path)
        msg = f"repomix output already exists: {existing.name}"
        if stale_msg:
            result["repomix"] = {"status": "warn", "message": f"{msg} — {stale_msg}"}
        else:
            result["repomix"] = {"status": "skip", "message": msg}
    else:
        try:
            subprocess.run(
                ["npx", "-y", "repomix"],
                capture_output=True, text=True, timeout=180,
                cwd=str(project_path),
            )
            new_files = list(project_path.glob("repomix-output.*"))
            if new_files:
                result["repomix"] = {"status": "ok", "message": f"repomix output generated: {new_files[0].name}"}
            else:
                result["repomix"] = {"status": "warn", "message": "repomix ran but no output found"}
        except subprocess.TimeoutExpired:
            result["repomix"] = {"status": "warn", "message": "repomix timed out (180s)"}
        except FileNotFoundError:
            result["repomix"] = {"status": "warn", "message": "npx not available"}

    # --- .gitignore update ---
    changed = _update_gitignore(project_path, ["CODESIGHT.md", "repomix-output.*"])
    result["gitignore_updated"] = changed

    return result
