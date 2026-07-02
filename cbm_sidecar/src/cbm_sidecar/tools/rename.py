"""CBM sidecar rename tool — multi-file coordinated rename."""
import sys, subprocess
from pathlib import Path

# Allow import from parent package (cbm_sidecar/)
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import open_cbm_db


def rename(symbol_name: str, new_name: str, file_path: str = None, dry_run: bool = True) -> dict:
    """Find and optionally rename a symbol across the codebase."""
    matches = []

    # Phase 1: Graph search
    try:
        conn = open_cbm_db(readonly=True)
        query = "SELECT DISTINCT n.name, n.file FROM nodes n WHERE n.name = ?"
        rows = conn.execute(query, [symbol_name]).fetchall()
        for row in rows:
            matches.append({
                "symbol": row["name"],
                "file": row["file"],
                "confidence": "graph"
            })
        conn.close()
    except FileNotFoundError:
        pass

    # Phase 2: Text fallback
    try:
        result = subprocess.run(
            ["rg", "-l", "--glob", "!tests/**", "--glob", "!.venv/**",
             "--glob", "!__pycache__/**", "--glob", "!.pytest_cache/**",
             symbol_name],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.strip().split("\n"):
            f = line.strip()
            if f and f not in {m["file"] for m in matches}:
                matches.append({"symbol": symbol_name, "file": f, "confidence": "text_search"})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    result = {
        "symbol_name": symbol_name,
        "new_name": new_name,
        "dry_run": dry_run,
        "matches": matches,
        "total": len(matches)
    }

    if not dry_run and matches:
        applied = []
        for m in matches:
            try:
                path = Path(m["file"])
                if path.exists():
                    content = path.read_text()
                    if symbol_name in content:
                        path.write_text(content.replace(symbol_name, new_name))
                        applied.append(m["file"])
            except Exception:
                pass
        result["applied"] = applied

    return result
