import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from tools.context import context

@pytest.fixture
def mock_cbm_db():
    """Create a mock CBM database with test data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    conn.execute("CREATE TABLE nodes (id INTEGER PRIMARY KEY, name TEXT, file_path TEXT)")
    conn.execute("CREATE TABLE edges (source_id INTEGER, target_id INTEGER, type TEXT)")
    conn.execute("INSERT INTO nodes VALUES (1, 'processPayment', 'src/payment.js')")
    conn.execute("INSERT INTO nodes VALUES (2, 'validatePayment', 'src/validate.js')")
    conn.execute("INSERT INTO edges VALUES (1, 2, 'CALLS')")
    conn.commit()
    conn.close()

    old_path = os.environ.get("CBM_DB_PATH")
    os.environ["CBM_DB_PATH"] = tmp.name
    yield tmp.name
    if old_path:
        os.environ["CBM_DB_PATH"] = old_path
    Path(tmp.name).unlink(missing_ok=True)


def test_context_single_match(mock_cbm_db):
    result = context("processPayment")
    assert result["status"] == "ok"
    assert len(result["outgoing_calls"]) >= 1
    assert result["outgoing_calls"][0]["symbol"] == "validatePayment"


def test_context_not_found(mock_cbm_db):
    result = context("nonexistent")
    assert result["references"] == []


def test_context_edge_types_present():
    """Verify edge type constants."""
    from tools.context import EDGE_TYPES
    assert "CALLS" in EDGE_TYPES
    assert "IMPLEMENTS" in EDGE_TYPES
    assert len(EDGE_TYPES) == 4


def test_context_note_about_missing_edges(mock_cbm_db):
    result = context("processPayment")
    assert "HAS_METHOD" in result.get("note", "")


def test_context_incoming_call(mock_cbm_db):
    """validatePayment is called by processPayment — should appear as incoming."""
    result = context("validatePayment")
    assert result["status"] == "ok"
    assert len(result["incoming_calls"]) >= 1
    assert result["incoming_calls"][0]["symbol"] == "processPayment"


def test_context_db_not_found(monkeypatch):
    monkeypatch.setenv("CBM_DB_PATH", "/nonexistent/path/cbm.db")
    result = context("someSymbol")
    assert result["status"] == "error"
    assert "not found" in result["message"]
