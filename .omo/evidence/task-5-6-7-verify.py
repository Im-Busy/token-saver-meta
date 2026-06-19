"""Verify Tasks 5, 6, 7 extensions."""
from src.config_gen import (
    get_tool_categories, get_one_shot_tools, get_skill_tools,
    get_binary_tools, get_cli_tools, get_core_tool_list,
    merge_token_saver_entries, remove_token_saver_entries,
    has_token_saver_entries, detect_all_markers,
    detect_platform_skills_dir, detect_platform_instructions_file,
)
from pathlib import Path

# 1. Categories
cats = get_tool_categories()
assert len(cats) == 5, f"Expected 5 cats, got {len(cats)}"
print(f"1. Categories: {list(cats.keys())}")

# 2. Tool counts
ot = get_one_shot_tools()
print(f"2. One-shot: {[t['name'] for t in ot]}")
bt = get_binary_tools()
print(f"3. Binary: {[t['name'] for t in bt]}")
st = get_skill_tools()
print(f"4. Skill: {[t['name'] for t in st]}")
ct = get_cli_tools()
print(f"5. CLI: {[t['name'] for t in ct]}")
cl = get_core_tool_list()
print(f"6. Core tools: {cl}")

# 3. Merge
existing = {"mcpServers": {"user-server": {"cmd": "echo"}}}
merged = merge_token_saver_entries(existing, "kilo")
assert "user-server" in merged["mcpServers"]
print("7. Merge: user-server preserved")

# 4. Remove
removed = remove_token_saver_entries({"mcpServers": {"gitnexus": {}, "user-server": {}}})
assert "gitnexus" not in removed["mcpServers"]
assert "user-server" in removed["mcpServers"]
print("8. Remove: token-saver removed, user preserved")

# 5. Has
assert not has_token_saver_entries({"mcpServers": {"user-server": {}}})
assert has_token_saver_entries({"mcpServers": {"gitnexus": {}}})
print("9. Has: detection correct")

# 6. Detection helpers
markers = detect_all_markers(Path("."))
assert isinstance(markers, dict) and len(markers) > 0
print(f"10. All markers: {len(markers)} entries")

sd = detect_platform_skills_dir("kilo")
print(f"11. Kilo skills dir: {sd}")

ins = detect_platform_instructions_file("kilo")
print(f"12. Kilo instructions: {ins}")

print("\nALL CHECKS PASSED")