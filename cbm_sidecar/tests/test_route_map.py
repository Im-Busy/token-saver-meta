import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from cbm_sidecar.tools.route_map import route_map


@pytest.fixture
def mock_cbm_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute(
        "CREATE TABLE nodes ("
        "id INTEGER PRIMARY KEY, name TEXT, file TEXT, label TEXT)"
    )
    conn.execute(
        "INSERT INTO nodes VALUES (1, '/api/users', 'server.js', 'Route')"
    )
    conn.execute(
        "INSERT INTO nodes VALUES (2, '/api/login', 'auth.js', 'Route')"
    )
    conn.commit()
    conn.close()
    old = os.environ.get("CBM_DB_PATH")
    os.environ["CBM_DB_PATH"] = tmp.name
    yield
    if old:
        os.environ["CBM_DB_PATH"] = old
    else:
        del os.environ["CBM_DB_PATH"]
    try:
        Path(tmp.name).unlink()
    except PermissionError:
        pass


def test_route_map_all_routes(mock_cbm_db):
    result = route_map()
    assert result["status"] == "ok"
    assert result["total"] >= 2


def test_route_map_filter(mock_cbm_db):
    result = route_map(route="users")
    assert result["total"] >= 1


def test_route_map_no_routes():
    os.environ["CBM_DB_PATH"] = "/nonexistent/db"
    result = route_map()
    assert result["total"] == 0
    assert result["routes"] == []


def test_heuristic_warning_present():
    result = route_map()
    assert "heuristic" in result.get("note", "").lower()


def test_route_structure():
    result = route_map()
    assert "routes" in result
    assert "total" in result
    assert "note" in result
