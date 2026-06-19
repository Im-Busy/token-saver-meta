"""Uninstall token-saver-meta — reverse all changes."""

from pathlib import Path
from datetime import datetime
import shutil
import sys


def _backup_file(filepath: Path) -> str | None:
    if not filepath.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = filepath.with_name(f"{filepath.name}.bak-{timestamp}")
    shutil.copy2(str(filepath), str(bak))
    return str(bak)


def uninstall_cgc_mcp(project_path: Path, platforms: list[str]) -> dict:
    """Remove only CGC (codegraphcontext) MCP entries from project configs."""
    import json

    result = {}
    for platform_id in platforms:
        from src.config_gen import load_matrix
        matrix = load_matrix()
        pdef = matrix["platforms"].get(platform_id)
        if not pdef:
            result[platform_id] = {"status": "skip", "reason": "unknown platform"}
            continue
        mcp_file = pdef.get("mcp_file")
        if not mcp_file:
            result[platform_id] = {"status": "skip", "reason": "no mcp_file"}
            continue
        mcp_path = project_path / mcp_file
        if not mcp_path.exists():
            result[platform_id] = {"status": "skip", "reason": "mcp file not found"}
            continue

        backup = _backup_file(mcp_path)
        try:
            content = json.loads(mcp_path.read_text(encoding="utf-8"))
            cleaned = {}
            for wrapper_key, servers in content.items():
                cleaned[wrapper_key] = {
                    k: v for k, v in servers.items()
                    if not k.startswith("codegraphcontext")
                }
            mcp_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
            result[platform_id] = {"status": "ok", "file": str(mcp_path), "backup": backup}
        except Exception as e:
            result[platform_id] = {"status": "error", "message": str(e)}

    return result


def uninstall_all(project_path: Path, force: bool = False) -> dict:
    """Remove all token-saver modifications from a project."""
    from src.config_gen import detect_platforms, remove_token_saver_entries, detect_platform_instructions_file

    result = {"backups": [], "mcp_removed": {}, "agents_md_removed": {}, "files_removed": []}
    project_root = project_path.resolve()

    if not force:
        print("This will remove token-saver entries from MCP configs, AGENTS.md sections, and generated files.")
        print("Backups will be created. Continue? [y/N]")
        confirm = input().strip().lower()
        if confirm not in ("y", "yes"):
            print("Cancelled.")
            return {"status": "cancelled"}

    # Detect platforms
    platforms = detect_platforms(project_root)

    # Remove MCP entries
    for platform_id in platforms:
        from src.config_gen import load_matrix
        matrix = load_matrix()
        pdef = matrix["platforms"].get(platform_id)
        if not pdef:
            continue
        mcp_file = pdef.get("mcp_file")
        if not mcp_file:
            continue
        mcp_path = project_root / mcp_file
        if not mcp_path.exists():
            continue
        
        import json
        backup = _backup_file(mcp_path)
        if backup:
            result["backups"].append(backup)
        
        try:
            content = json.loads(mcp_path.read_text(encoding="utf-8"))
            cleaned = remove_token_saver_entries(content)
            mcp_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
            result["mcp_removed"][platform_id] = {"status": "ok", "file": str(mcp_path)}
        except Exception as e:
            result["mcp_removed"][platform_id] = {"status": "warn", "message": str(e)}

    # Remove AGENTS.md sections
    for platform_id in platforms:
        instr_file = detect_platform_instructions_file(platform_id)
        if instr_file is None:
            continue
        target = project_root / instr_file if not instr_file.is_absolute() else instr_file
        if not target.exists():
            continue
        
        content = target.read_text(encoding="utf-8")
        start_marker = "<!-- TOKEN_SAVER_START -->"
        end_marker = "<!-- TOKEN_SAVER_END -->"
        
        if start_marker in content and end_marker in content:
            backup = _backup_file(target)
            if backup:
                result["backups"].append(backup)
            start_idx = content.index(start_marker)
            end_idx = content.index(end_marker) + len(end_marker)
            new_content = content[:start_idx] + content[end_idx:].lstrip("\n")
            target.write_text(new_content, encoding="utf-8")
            result["agents_md_removed"][platform_id] = {"status": "ok"}

    # Remove generated files
    for pattern in ["CODESIGHT.md", "repomix-output.*", ".repomixignore"]:
        for f in list(project_root.glob(pattern)):
            f.unlink()
            result["files_removed"].append(str(f))

    result["status"] = "ok"
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Token Saver Meta — Uninstall")
    parser.add_argument("project_path", nargs="?", default=".", help="Project directory")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    args = parser.parse_args()
    
    result = uninstall_all(Path(args.project_path).resolve(), force=args.force)
    
    print(f"\nUninstall {'complete' if result.get('status') == 'ok' else result.get('status', 'failed')}")
    print(f"  MCP configs cleaned: {len(result.get('mcp_removed', {}))}")
    print(f"  AGENTS.md sections removed: {len(result.get('agents_md_removed', {}))}")
    print(f"  Files removed: {len(result.get('files_removed', []))}")
    print(f"  Backups created: {len(result.get('backups', []))}")


if __name__ == "__main__":
    main()
