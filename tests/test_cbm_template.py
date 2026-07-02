import pytest
from pathlib import Path

TEMPLATE = Path(__file__).parent.parent / "templates" / "cbm_agents_md_block.md"


def test_template_exists():
    assert TEMPLATE.exists()


def test_template_under_1500_chars():
    content = TEMPLATE.read_text()
    assert len(content) <= 1500, f"Template is {len(content)} chars"


def test_template_valid_markdown():
    content = TEMPLATE.read_text()
    assert "<!-- cbm:start -->" in content
    assert "<!-- cbm:end -->" in content
    assert "search_graph" in content
    assert "trace_path" in content
    assert "get_architecture" in content


def test_template_no_conflict_with_token_rules():
    content = TEMPLATE.read_text()
    assert "prose terseness" not in content.lower()
    assert "code minimalism" not in content.lower()
