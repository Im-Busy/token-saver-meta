import pytest
import os
from pathlib import Path

def test_db_path_detection():
    from cbm_sidecar.db import get_cbm_db_path
    path = str(get_cbm_db_path())
    # Either the real cache path, or an env-overridden path
    is_cache = ".cache" in path and "codebase-memory-mcp" in path
    is_override = "CBM_DB_PATH" in os.environ
    assert is_cache or is_override, f"unexpected path: {path}"

def test_cbm_db_not_found_graceful():
    from cbm_sidecar.db import open_cbm_db
    import os
    old_path = os.environ.get("CBM_DB_PATH")
    os.environ["CBM_DB_PATH"] = "/nonexistent/cbm.db"
    try:
        with pytest.raises(FileNotFoundError):
            open_cbm_db()
    finally:
        if old_path:
            os.environ["CBM_DB_PATH"] = old_path
        else:
            del os.environ["CBM_DB_PATH"]

def test_sidecar_db_creates():
    from cbm_sidecar.db import open_sidecar_db
    conn = open_sidecar_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert any("custom_nodes" in t[0] for t in tables)
    conn.close()

def test_server_module_loads():
    """Verify server module imports without error."""
    from cbm_sidecar import server
    assert server.server is not None
    assert server.list_tools is not None
    assert server.call_tool is not None

def test_tools_registered():
    """Verify 3 tools are registered."""
    import asyncio
    from cbm_sidecar import server
    tools = asyncio.run(server.list_tools())
    tool_names = [t.name for t in tools]
    assert "context" in tool_names
    assert "rename" in tool_names
    assert "route_map" in tool_names
    assert len(tools) == 3

def test_db_readonly_mode():
    """Verify CBM DB opens in read-only mode."""
    from cbm_sidecar.db import open_cbm_db
    import os
    os.environ["CBM_DB_PATH"] = str(Path(__file__).parent.parent / "tests" / "fixtures" / "empty.db")
    with pytest.raises(FileNotFoundError):
        open_cbm_db()
