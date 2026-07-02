"""CBM sidecar context tool — 360° symbol view."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from cbm_sidecar.db import open_cbm_db

EDGE_TYPES = {"CALLS", "IMPLEMENTS", "INHERITS", "IMPORTS"}

def context(name: str, file_path: str = None) -> dict:
    """Get 360° context for a code symbol. Returns categorized references."""
    try:
        conn = open_cbm_db(readonly=True)
    except FileNotFoundError:
        return {"status": "error", "message": "CBM database not found"}

    query = """
        SELECT 'outgoing' as direction, e.type as edge_type,
               other.name as symbol_name, other.file_path as file_path
        FROM edges e
        JOIN nodes src ON e.source_id = src.id
        JOIN nodes other ON e.target_id = other.id
        WHERE src.name = ? AND e.type IN ('CALLS','IMPLEMENTS','INHERITS','IMPORTS')
        UNION ALL
        SELECT 'incoming' as direction, e.type as edge_type,
               other.name as symbol_name, other.file_path as file_path
        FROM edges e
        JOIN nodes tgt ON e.target_id = tgt.id
        JOIN nodes other ON e.source_id = other.id
        WHERE tgt.name = ? AND e.type = 'CALLS'
    """
    rows = conn.execute(query, [name, name]).fetchall()
    conn.close()

    if not rows:
        return {"status": "ok", "name": name, "references": [], "note": "No references found"}

    incoming_calls = []
    outgoing_calls = []
    implementations = []
    imports_list = []

    for row in rows:
        ref = {"symbol": row["symbol_name"], "file": row["file_path"]}
        direction = row["direction"]
        edge = row["edge_type"]

        if direction == "incoming":
            incoming_calls.append(ref)
        elif edge == "CALLS":
            outgoing_calls.append(ref)
        elif edge == "IMPLEMENTS":
            implementations.append(ref)
        elif edge == "INHERITS":
            outgoing_calls.append(ref)
        elif edge == "IMPORTS":
            imports_list.append(ref)

    return {
        "status": "ok",
        "name": name,
        "incoming_calls": incoming_calls[:50],
        "outgoing_calls": outgoing_calls[:50],
        "implementations": implementations[:20],
        "imports": imports_list[:20],
        "note": "Missing edge types (HAS_METHOD, METHOD_OVERRIDES, ACCESSES) — not tracked by CBM"
    }
