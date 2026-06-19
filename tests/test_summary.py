"""Tests for src/summary.py terminal report formatter."""

from src.summary import format_summary, _count_active


def _all_ok_results() -> dict:
    return {
        "base_layer": {"status": "ok", "platforms": ["claude-code", "kilo"]},
        "intelligence": {
            "cgc": {"status": "ok", "platforms": 2},
            "codesight": {"status": "ok"},
            "repomix": {"status": "ok"},
        },
        "compression": {
            "rtk": {"status": "ok", "version": "1.2.3"},
            "contextslim": {"status": "ok"},
        },
        "node_only_fallback": False,
    }


def test_format_all_ok():
    out = format_summary(_all_ok_results())
    assert "6/6 tools active" in out
    for tool in ("cgc", "codesight", "repomix", "rtk", "contextslim"):
        assert f"✅" in out


def test_format_with_warnings():
    results = _all_ok_results()
    results["compression"]["contextslim"] = {"status": "skip", "reason": "Python rewrite pending"}
    results["intelligence"]["repomix"] = {"status": "error"}
    out = format_summary(results)
    assert "4/6 tools active" in out
    assert "⚠️" in out
    assert "Python rewrite pending" in out
    assert "❌" in out


def test_format_node_only_fallback():
    results = _all_ok_results()
    results["node_only_fallback"] = True
    out = format_summary(results)
    assert "Node-only mode" in out


def test_count_active():
    assert _count_active(_all_ok_results()) == 6

    results = _all_ok_results()
    results["compression"]["contextslim"] = {"status": "skip", "reason": "..."}
    assert _count_active(results) == 5
