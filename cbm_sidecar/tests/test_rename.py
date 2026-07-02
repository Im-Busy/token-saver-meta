import pytest, tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cbm_sidecar"))
from tools.rename import rename as rename_symbol


def test_rename_dry_run_default():
    """Dry run should be True by default."""
    result = rename_symbol("zz_nonexistent_func_42a7b3c1", "newFunc")
    assert result["dry_run"] is True
    assert result["total"] == 0


def test_rename_no_matches():
    result = rename_symbol("zz_this_definitely_does_not_exist_xyz_9f2e", "new")
    assert result["matches"] == []
    assert result["total"] == 0


def test_rename_structure():
    result = rename_symbol("testFunc", "newFunc", dry_run=True)
    assert "symbol_name" in result
    assert "new_name" in result
    assert "matches" in result
    assert "total" in result


def test_rename_apply_no_matches():
    """Applying rename with no matches should not crash."""
    result = rename_symbol("zz_no_matches_here_8d4a", "new", dry_run=False)
    assert "applied" not in result or result.get("applied", []) == []


def test_rename_confidence_tags():
    """Any matches from graph should have confidence tag."""
    result = rename_symbol("zz_test_symbol_71fe", "zz_new_symbol_a3c8")
    for m in result["matches"]:
        assert "confidence" in m
        assert m["confidence"] in ("graph", "text_search")
