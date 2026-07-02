"""CBM sidecar route_map tool — API route handler to consumer mapping."""
import subprocess
from cbm_sidecar.db import open_cbm_db


def route_map(route: str = None) -> dict:
    """Map API routes to handlers and consumers. Heuristic-based."""
    routes = []

    # Phase 1: Find Route nodes from CBM
    try:
        conn = open_cbm_db(readonly=True)
        query = "SELECT DISTINCT n.name, n.file FROM nodes n WHERE n.label = 'Route'"
        params = []
        if route:
            query += " AND n.name LIKE ?"
            params.append(f"%{route}%")
        rows = conn.execute(query, params).fetchall()

        for row in rows:
            route_entry = {
                "route": row["name"],
                "handler_file": row["file"],
                "consumers": [],
                "confidence": "graph",
            }
            routes.append(route_entry)
        conn.close()
    except FileNotFoundError:
        pass

    # Phase 2: Find consumers via text search
    for entry in routes:
        route_path = entry["route"]
        try:
            result = subprocess.run(
                ["rg", "-l", route_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            for line in result.stdout.strip().split("\n"):
                f = line.strip()
                if f and f != entry["handler_file"]:
                    entry["consumers"].append(
                        {"file": f, "confidence": "text"}
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return {
        "status": "ok",
        "routes": routes,
        "total": len(routes),
        "note": (
            "⚠️ Heuristic — regex-based URL matching. "
            "No indirect consumers, no tree-shaking awareness."
        ),
    }
