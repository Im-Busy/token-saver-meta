"""Integration tests for CBM sidecar tools against real CBM-indexed data."""
import pytest
import os
from pathlib import Path

REAL_DB = Path.home() / ".cache" / "codebase-memory-mcp" / "C-Dev-projects-token-saver-meta.db"


@pytest.fixture(autouse=True)
def _set_cbm_db():
    """Set CBM_DB_PATH for integration tests, restore after each test."""
    old = os.environ.get("CBM_DB_PATH")
    if REAL_DB.exists():
        os.environ["CBM_DB_PATH"] = str(REAL_DB)
    yield
    if old:
        os.environ["CBM_DB_PATH"] = old
    else:
        os.environ.pop("CBM_DB_PATH", None)


@pytest.mark.skipif(not REAL_DB.exists(), reason="CBM database not indexed — run Task 18 first")
def test_integration_context_known_symbol():
    """context tool finds install_cgc in real CBM data."""
    from tools.context import context
    result = context("install_cgc")
    assert result["status"] == "ok"
    assert result.get("outgoing_calls") is not None
    assert result.get("incoming_calls") is not None
    assert result.get("implementations") is not None
    assert "note" in result


@pytest.mark.skipif(not REAL_DB.exists(), reason="CBM database not indexed")
def test_integration_context_not_found():
    """context tool returns empty references for nonexistent symbol."""
    from tools.context import context
    result = context("this_symbol_does_not_exist_xyz")
    assert result["status"] == "ok"
    assert result["references"] == []
    assert "No references found" in result["note"]


@pytest.mark.skipif(not REAL_DB.exists(), reason="CBM database not indexed")
def test_integration_rename_dry():
    """rename dry_run works against real data."""
    from cbm_sidecar.tools.rename import rename
    result = rename("install_cgc", "install_codegraph", dry_run=True)
    assert result["dry_run"] is True
    assert result["total"] >= 1


@pytest.mark.skipif(not REAL_DB.exists(), reason="CBM database not indexed")
def test_integration_route_map():
    """route_map returns routes from real CBM data."""
    from cbm_sidecar.tools.route_map import route_map
    result = route_map()
    assert result["status"] == "ok"
    assert "total" in result
    assert "note" in result


@pytest.mark.skipif(not REAL_DB.exists(), reason="CBM database not indexed")
def test_integration_concurrent_reads():
    """Multiple context calls don't cause SQLite lock errors."""
    from tools.context import context
    results = []
    for symbol in ["install_cgc", "context", "detect_platform"]:
        result = context(symbol)
        results.append(result["status"])
    assert all(r == "ok" for r in results)
