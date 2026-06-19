"""Verify matrix.json restructured correctly."""
import json

m = json.load(open("platforms/matrix.json"))

# Check 5 sections
sections = ["mcp_servers","one_shot_tools","skill_tools","binary_tools","cli_tools"]
for s in sections:
    assert s in m, f"Missing section: {s}"
    print(f"  {s}: OK")

print("\nALL 5 SECTIONS FOUND")

# Check version
assert m["version"] == "2.0.0", f"Expected 2.0.0, got {m['version']}"
print(f"Version: {m['version']} OK")

# Check platforms
assert "platforms" in m
print(f"Platforms: {len(m['platforms'])}")

# Check mcp_families
assert "mcp_families" in m
print(f"Families: {len(m['mcp_families'])}")

# Check token_saver_meta
tsm = m["token_saver_meta"]
core = tsm["core_bundle_tools"]
print(f"Core bundle tools: {len(core)}")
for t in core:
    print(f"  - {t}")

# Check existing entries still at top level
print(f"\nGitNexus at top: {'gitnexus_server' in m}")
print(f"CGC at top: {'codegraphcontext_server' in m}")

print("\nALL CHECKS PASSED")