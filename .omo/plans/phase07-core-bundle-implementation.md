# Phase 07 — Core Bundle Implementation

## TL;DR

> **Quick Summary**: Build a zero-config, single-command installer (`npx create-token-saver` / `uvx token-saver-meta setup`) that auto-detects the user's AI agent platform, installs 10 token-saving tools, generates MCP configs, injects AGENTS.md behavioral rules, and displays a status dashboard.
>
> **Deliverables**:
> - Extended `platforms/matrix.json` with 5 tool categories across 18 platforms
> - Extended `src/config_gen.py` with category-aware config generation
> - `src/installer.py` — unified 10-tool installer (detect → install → index → inject → verify)
> - `src/uninstall.py` — automated cleanup command
> - `src/dashboard.py` — static HTML status page
> - `skills/combo-workflow/SKILL.md` — unified tool priority order for agents
> - Bundled SKILL.md files (caveman, LG-token-saver, kevin-copilot)
> - AGENTS.md injection content (<500 tokens)
> - `pyproject.toml` + `package.json` + `cli.js` — distribution entry points
> - `.gitignore` — Python/Node/uv standard entries
> - `tests/` — pytest test suite with fixtures for all 18 platforms
>
> **Estimated Effort**: Large (20 tasks, 5 implementation waves)
> **Parallel Execution**: YES — 5 waves, max concurrency 7
> **Critical Path**: Task 0 → Task 1 → Task 2 → Tasks 3,4 → Tasks 5,6,7 → Tasks 8,9,10,11,12,13,14 → Tasks 15,19 → F1-F4

---

## Context

### Original Request
User's handover document: "Build the unified installer that sets up all 10 core tools with zero user configuration." Phase 07 is the first implementation phase — all 6 prior phases were research and architecture.

### Interview Summary
**Key Decisions**:
- **Test strategy**: pytest, TDD (test-first). RED → GREEN → REFACTOR per task.
- **Scope**: ALL 5 steps (7.1-7.5) in ONE plan. Phases 08-10 are separate.
- **Matrix.json**: Full restructure — 5 distinct tool categories (mcp_servers, one_shot_tools, skill_tools, binary_tools, cli_tools).
- **Tool #10**: Installer binary + combo-workflow SKILL.md (teaches agents tool priority/ordering).
- **Uninstall**: Automated `token-saver uninstall` command.
- **Caveman**: Bundle only core `caveman/SKILL.md` (not all 7 variants).
- **Kevin-copilot**: Bundle `copilot-instructions.md` + `unslop/SKILL.md` only.
- **AGENTS.md injection**: <500 tokens. Behavioral rules only. Savings table in dashboard.
- **RTK Windows**: `cargo install rtk` fallback. Skip-with-warning if Rust unavailable.

**Research Findings**:
- Foundation project `gitnexus_CGC_combo` has working config_gen.py (354 LOC, 9 functions) and matrix.json (18 platforms, 3 MCP families)
- Project is documentation-only — no src/, no build system, no test infrastructure
- LG-token-saver has SKILL.md ready; caveman/kevin-copilot need extraction
- codesight and Repomix are one-shot CLI tools, NOT MCP servers (critical finding from Metis)
- Only GitNexus and CGC are true MCP servers among the 10 core tools

### Metis Review
**Identified Gaps** (all addressed):
- **Matrix.json architecture mismatch**: Resolved — full restructure with 5 categories
- **codesight/Repomix MCP assumption**: Resolved — classified as one_shot_tools, not mcp_servers
- **No test infrastructure**: Resolved — Task 0 adds pytest + fixtures + regression tests
- **Tool assumption unvalidated**: Resolved — Task 0.5 verifies actual CLIs before writing configs
- **No failure mode defined**: Resolved — each tool has failure mode: ABORT / SKIP / WARN
- **RTK Windows binary unverified**: Resolved — cargo fallback, skip-with-warning if no Rust
- **AGENTS.md injection bloat**: Resolved — <500 token limit
- **Caveman/kevin-copilot file bloat**: Resolved — bundle only core files

---

## Work Objectives

### Core Objective
Build a zero-config, idempotent installer that provisions all 10 token-saving tools for any of 18 supported AI agent platforms — with no user configuration required.

### Concrete Deliverables
- `platforms/matrix.json` — restructured with 5 tool categories, all 10 core tools, 18 platforms
- `src/config_gen.py` — extended for 5 categories with category-aware generation
- `src/installer.py` — unified installer: detect → env-check → install-core → index → inject → verify
- `src/uninstall.py` — reverse all changes: MCP entries, AGENTS.md sections, generated files
- `src/dashboard.py` — static HTML dashboard: tool status, version, est. savings, index freshness
- `skills/combo-workflow/SKILL.md` — agent protocol for using all 10 tools as a system
- `skills/{caveman,lg-token-saver,kevin-copilot}/SKILL.md` — bundled from useful-repos/
- `templates/agents_md_section.md` — AGENTS.md injection template (<500 tokens)
- `pyproject.toml` + `package.json` + `cli.js` — distribution entry points
- `tests/` — pytest suite: regression, idempotency, missing-tools, empty-project, platform fixtures
- `.gitignore` — Python/Node/uv standard entries

### Definition of Done
- [ ] `uv run pytest` — ALL tests pass (regression + idempotency + edge cases)
- [ ] `uvx token-saver-meta setup ./test-project` — installs all 10 tools, zero errors
- [ ] `npx create-token-saver ./test-project` — npm entry point works
- [ ] `token-saver uninstall ./test-project` — reverses all changes
- [ ] `token-saver dashboard` — serves HTML dashboard on port 8080
- [ ] Running installer twice produces identical results (idempotency verified)

### Must Have
- **5-tool-category matrix.json** with `mcp_servers`, `one_shot_tools`, `skill_tools`, `binary_tools`, `cli_tools` sections
- **merge-into-existing-json** strategy: never overwrite user's existing MCP configs
- **Idempotent install**: running twice = no-op (all servers already present)
- **Per-tool failure isolation**: one tool's install failure doesn't block the other 9
- **AGENTS.md injection** using `<!-- token-saver:start -->` / `<!-- token-saver:end -->` markers
- **Regression gate**: combo's existing GitNexus+CGC config generation produces identical output
- **Backup before mutation**: `.bak-YYYYMMDD-HHMMSS` of any config file before modification
- **All savings claims cited**: per-tool, with source label (benchmarked/self-reported/unverified)
- **Every task has Agent-Executed QA scenarios** with exact commands and expected output

### Must NOT Have (Guardrails)
- **NO MCP config entries for non-MCP tools**: codesight and Repomix generate files, not server configs
- **NO aggregate savings numbers**: only per-tool estimates with source labels
- **NO Phase 08 features**: no `token-saver enable` / `token-saver disable` for optional modules
- **NO interactive dashboard**: Phase 07 dashboard is static HTML with status columns only
- **NO hard fail on install**: all failures are SKIP (continue) or WARN (note), never ABORT
- **NO overwriting user configs**: merge-into-existing-json preserves ALL existing MCP entries
- **NO installing all 7 caveman variants or all 30+ kevin-copilot files**: bundle only core files
- **NO AGENTS.md injection >500 tokens**: behavioral rules only, savings table in dashboard
- **NO skipping .bak backup before config modification**: always create timestamped backup
- **NO unbounded subprocess calls**: all install commands have 120s timeout, captured stderr

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (will be created in Task 0)
- **Automated tests**: TDD (test-first) — RED → GREEN → REFACTOR
- **Framework**: pytest
- **One task = one test file + one implementation file**: paired

### QA Policy
Every task MUST include agent-executed QA scenarios (see TODO template below).
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI/Backend**: Use Bash — run commands, assert exit codes, grep output
- **API/Files**: Use Bash (curl, Test-Path, Get-Content) — assert file existence, content matches
- **Dashboard**: Use curl — assert HTTP 200, grep for expected content
- **MCP Config**: Use Bash (jq) — assert valid JSON, server entries present

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 0 (Foundation — sequential prerequisites):
├── Task 0: Test infrastructure + .gitignore [quick]
├── Task 0.5: Tool assumption validation [quick]
└── Task 1: Copy foundation code from gitnexus_CGC_combo [quick]

Wave 1 (Matrix & Config — MAX PARALLEL, after Wave 0):
├── Task 2: Restructure matrix.json for 5 categories [unspecified-low]
├── Task 3: Add MCP server entries (GitNexus, CGC) [quick]
├── Task 4: Add non-MCP tool entries (RTK, codesight, Repomix, etc.) [unspecified-low]
├── Task 5: Extend config_gen.py for category awareness [deep]
├── Task 6: Implement category-aware merge logic [deep]
└── Task 7: Extend platform detection for all platforms [unspecified-low]

Wave 2 (Installer Engine — MAX PARALLEL, after Wave 1):
├── Task 8: Build installer.py scaffold (detect, env-check, pre-flight) [deep]
├── Task 9: Implement MCP server installer (GitNexus + CGC) [unspecified-high]
├── Task 10: Implement RTK installer (binary-download strategy) [unspecified-high]
├── Task 11: Implement one-shot tools (codesight + Repomix) [unspecified-high]
├── Task 12: Implement skill tools (caveman, LG-token-saver, kevin-copilot) [unspecified-low]
├── Task 13: Implement CLI tools (ContextSlimAI) [unspecified-high]
└── Task 14: Implement indexing + verification phase [unspecified-high]

Wave 3 (Injection & Distribution — MAX PARALLEL, after Wave 2):
├── Task 15: AGENTS.md injection (<500 tokens, combo-workflow rules) [unspecified-low]
├── Task 16: Create combo-workflow SKILL.md [unspecified-low]
├── Task 17: Extract and copy tool SKILL.md files [unspecified-low]
└── Task 18: Build system & distribution entry points [quick]

Wave 4 (Final Features — MAX PARALLEL, after Wave 3):
├── Task 19: Build uninstall command [unspecified-high]
└── Task 20: Dashboard scaffold [visual-engineering]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
→ Present results → Get explicit user okay
```

### Dependency Matrix

| Tasks | Depends On | Blocks | Wave |
|-------|-----------|--------|------|
| 0, 0.5 | — | 1 | 0 |
| 1 | 0, 0.5 | 2-7 | 0 |
| 2-4 | 1 | 5,6,7 | 1 |
| 5,6,7 | 2,3,4 | 8-14 | 1 |
| 8 | 5,6,7 | 9-14 | 2 |
| 9-14 | 8 | 15,16,17,19 | 2 |
| 15,16,17,18 | 9-14 | 19 | 3 |
| 19 | 15 | — | 4 |
| 20 | — | — | 4 |
| F1-F4 | ALL | — | FINAL |

**Critical Path**: Task 0 → Task 1 → Task 2 → Tasks 3,4 → Tasks 5,6,7 → Task 8 → Tasks 9-14 → Task 15 → Task 19 → F1-F4

### Agent Dispatch Summary

- **0**: 3 tasks — T0 → `quick`, T0.5 → `quick`, T1 → `quick`
- **1**: 6 tasks — T2 → `unspecified-low`, T3 → `quick`, T4 → `unspecified-low`, T5 → `deep`, T6 → `deep`, T7 → `unspecified-low`
- **2**: 7 tasks — T8 → `deep`, T9 → `unspecified-high`, T10 → `unspecified-high`, T11 → `unspecified-high`, T12 → `unspecified-low`, T13 → `unspecified-high`, T14 → `unspecified-high`
- **3**: 4 tasks — T15 → `unspecified-low`, T16 → `unspecified-low`, T17 → `unspecified-low`, T18 → `quick`
- **4**: 2 tasks — T19 → `unspecified-high`, T20 → `visual-engineering`
- **FINAL**: 4 tasks — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 0. Set up test infrastructure + .gitignore

  **What to do**:
  - Create `pyproject.toml` with `[project]` metadata (name, version 0.1.0, requires-python >=3.10), `[project.scripts]` stub, `[build-system]` (hatchling), `[tool.pytest.ini_options]` (testpaths, pythonpath)
  - Create `tests/conftest.py` with fixtures: `temp_project(tmp_path)` creates a dir with platform markers (`.kilo/`, `CLAUDE.md`, `.cursor/`, etc.), `sample_mcp_config(tmp_path)` returns a dict with existing MCP servers, `matrix_data()` loads matrix.json
  - Create `tests/test_combo_regression.py` with test: `test_gitnexus_cgc_config_unchanged()` — compares gitnexus_CGC_combo's config_gen.py output with our extended version (must be identical for GitNexus+CGC)
  - Create `.gitignore` with: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `dist/`, `*.egg-info/`, `node_modules/`, `.bak-*`, `CODESIGHT.md`, `repomix-output.*`, `.repomixignore`
  - Run `uv run pytest --collect-only` to verify test collection works

  **Must NOT do**:
  - Don't add `[project.dependencies]` yet (will be determined as we build)
  - Don't add test dependencies beyond pytest (no mock, no tox)
  - Don't add complex fixture factories — keep conftest.py simple

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Python project setup — pyproject.toml, conftest, .gitignore, one regression test
  - **Skills**: [`cli-tools`]
    - `cli-tools`: For uv commands (uv run, uv add)

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential prerequisite)
  - **Parallel Group**: Wave 0 (with Task 0.5, Task 1 — sequential)
  - **Blocks**: Task 1 (foundation code needs test infra in place)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `C:\Dev\projects\gitnexus_CGC_combo\pyproject.toml` — reference pyproject.toml structure from combo
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:29-31` — `load_matrix()` for fixture design
  - `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json:1-50` — platform structure for test fixtures

  **Acceptance Criteria**:
  - [ ] Test file created: `tests/test_combo_regression.py`
  - [ ] `uv run pytest --collect-only` → collects at least 1 test
  - [ ] `.gitignore` exists with all listed patterns

  **QA Scenarios**:
  ```
  Scenario: Test infrastructure is functional
    Tool: Bash
    Preconditions: pyproject.toml, tests/conftest.py, tests/test_combo_regression.py exist
    Steps:
      1. uv run pytest --collect-only
      2. Assert output contains "test_combo_regression.py"
      3. Assert exit code is 0
    Expected Result: pytest collects tests without errors
    Evidence: .omo/evidence/task-0-pytest-collect.txt

  Scenario: .gitignore covers Python artifacts
    Tool: Bash
    Preconditions: .gitignore exists
    Steps:
      1. Get-Content .gitignore | Select-String "__pycache__"
      2. Get-Content .gitignore | Select-String "*.pyc"
      3. Get-Content .gitignore | Select-String ".pytest_cache"
    Expected Result: All three patterns match
    Evidence: .omo/evidence/task-0-gitignore.txt
  ```

  **Commit**: YES
  - Message: `chore(scaffold): add test infrastructure, pyproject.toml, and .gitignore`
  - Files: `pyproject.toml`, `tests/conftest.py`, `tests/test_combo_regression.py`, `.gitignore`

- [x] 00. Validate tool assumptions before implementation

  **What to do**:
  - Run `npx codesight --help` (or `npx codesight -h`) — verify it's a one-shot CLI, NOT an MCP server. Check for `--mcp` flag existence. Document actual arguments.
  - Run `npx repomix --help` — verify one-shot packer. Check for `--mcp` flag. Document format/arguments.
  - Check RTK GitHub Releases (`https://github.com/rtk-lang/rtk/releases`) for Windows binaries (`.exe`, `.msi`, or `x86_64-pc-windows-msvc`). Document available platforms.
  - Run `npx contextslim --help` or `npx contextslim init --help` — verify init subcommand exists.
  - Check caveman's `useful-repos/caveman/skills/` directory — identify the core SKILL.md (not all 7 variants).
  - Check kevin-copilot's `.github/skills/` or `skills/` directory — identify `copilot-instructions.md` and `unslop/SKILL.md`.
  - Check LG-token-saver's `useful-repos/LG-token-saver/SKILL.md` — verify it exists and is the correct file.
  - Create `docs/tool-assumptions.md` documenting ALL findings: which tools have MCP servers, which are one-shot, RTK platform support, SKILL.md paths.

  **Must NOT do**:
  - Don't write any code yet — this is purely validation
  - Don't assume `--mcp` flag exists just because handover says it does
  - Don't skip RTK Windows check — this determines binary-download fallback strategy

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: CLI discovery — running help commands, checking releases, reading file trees
  - **Skills**: [`cli-tools`]
    - `cli-tools`: For npx commands and file operations

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential with Task 0, before Task 1)
  - **Parallel Group**: Wave 0
  - **Blocks**: Task 1 (foundation code)
  - **Blocked By**: None

  **References**:
  - `useful-repos/codesight/` — README for CLI documentation
  - `useful-repos/repomix/` — (if exists) or `npx repomix --help`
  - `useful-repos/rtk/` — README for install methods
  - `useful-repos/caveman/skills/` — caveman skill directory
  - `useful-repos/kevin-copilot/` — .github/skills/ or skills/ directory
  - `useful-repos/ContextSlimAI/` — README for CLI usage

  **Acceptance Criteria**:
  - [ ] `docs/tool-assumptions.md` created with all 7 tool findings
  - [ ] codesight: documented as one-shot CLI or MCP server with evidence
  - [ ] RTK: Windows binary availability documented with release link
  - [ ] Caveman: core SKILL.md path identified
  - [ ] Kevin-copilot: copilot-instructions.md + unslop/SKILL.md paths identified

  **QA Scenarios**:
  ```
  Scenario: codesight is a one-shot CLI (not MCP server)
    Tool: Bash
    Preconditions: Node.js installed
    Steps:
      1. npx codesight --help 2>&1 | Out-File -FilePath .omo/evidence/task-0.5-codesight-help.txt
      2. Get-Content .omo/evidence/task-0.5-codesight-help.txt
      3. Assert output shows one-shot usage (generate/analyze), NOT "start server" or "listen on port"
    Expected Result: codesight help shows one-shot CLI usage, no --mcp flag or server mode
    Evidence: .omo/evidence/task-0.5-codesight-help.txt

  Scenario: RTK Windows binary check
    Tool: Bash
    Preconditions: Internet access
    Steps:
      1. Invoke-WebRequest -Uri "https://api.github.com/repos/rtk-lang/rtk/releases/latest" | Select-Object -ExpandProperty Content | Out-File .omo/evidence/task-0.5-rtk-releases.json
      2. Get-Content .omo/evidence/task-0.5-rtk-releases.json | Select-String "windows"
      3. Assert: either windows binary found OR documented as unavailable
    Expected Result: Evidence file documents RTK platform availability
    Evidence: .omo/evidence/task-0.5-rtk-releases.json
  ```

  **Commit**: YES
  - Message: `docs(assumptions): validate tool CLIs and platform support before implementation`
  - Files: `docs/tool-assumptions.md`

- [x] 1. Copy foundation code from gitnexus_CGC_combo

  **What to do**:
  - Copy `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py` → `src/config_gen.py` (verbatim, no changes)
  - Copy `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json` → `platforms/matrix.json` (verbatim)
  - Copy `C:\Dev\projects\gitnexus_CGC_combo\cli.js` → `cli.js` (verbatim)
  - Test: `uv run python src/config_gen.py --list-platforms` → lists all 17 platforms from combo
  - Test: `uv run python src/config_gen.py --detect --project-path .` → detects this project's platforms (OpenCode + Kilo)
  - Test: `uv run pytest tests/test_combo_regression.py` → PASS (regression gate verifies copied code works)

  **Must NOT do**:
  - Don't modify any copied files yet — verbatim copies only
  - Don't add new tool entries to matrix.json
  - Don't refactor config_gen.py

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: File copy + verification — no code changes
  - **Skills**: [`cli-tools`]
    - `cli-tools`: For file operations (Copy-Item, uv run)

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential)
  - **Parallel Group**: Wave 0
  - **Blocks**: Tasks 2, 3, 4, 5, 6, 7 (everything depends on foundation)
  - **Blocked By**: Task 0, Task 0.5

  **References**:
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py` — source (354 lines, 9 functions)
  - `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json` — source (293 lines, 18 platforms)
  - `C:\Dev\projects\gitnexus_CGC_combo\cli.js` — source (JS→Python bridge)

  **Acceptance Criteria**:
  - [ ] `src/config_gen.py` copied verbatim from combo
  - [ ] `platforms/matrix.json` copied verbatim from combo
  - [ ] `cli.js` copied verbatim from combo
  - [ ] `uv run python src/config_gen.py --list-platforms` → lists 17 platforms
  - [ ] `uv run pytest tests/test_combo_regression.py` → PASS

  **QA Scenarios**:
  ```
  Scenario: Copied config_gen.py produces identical output to original
    Tool: Bash
    Preconditions: src/config_gen.py exists
    Steps:
      1. uv run python src/config_gen.py --list-platforms
      2. Assert output contains "kilo", "claude-code", "cursor", "opencode" (combo platforms)
      3. Assert exit code is 0
    Expected Result: Lists all 17 combo platforms
    Evidence: .omo/evidence/task-1-list-platforms.txt

  Scenario: Copied matrix.json is valid JSON
    Tool: Bash
    Preconditions: platforms/matrix.json exists
    Steps:
      1. python -c "import json; json.load(open('platforms/matrix.json')); print('VALID')"
      2. Assert output is "VALID"
    Expected Result: matrix.json is valid JSON
    Evidence: .omo/evidence/task-1-matrix-valid.txt
  ```

  **Commit**: YES
  - Message: `chore(scaffold): copy foundation code from gitnexus_CGC_combo`
  - Files: `src/config_gen.py`, `platforms/matrix.json`, `cli.js`

- [x] 2. Restructure matrix.json for 5 tool categories

  **What to do**:
  - Read current `platforms/matrix.json` (18 platforms, 2 MCP servers, 3 format families)
  - Create 5 new top-level sections: `mcp_servers`, `one_shot_tools`, `skill_tools`, `binary_tools`, `cli_tools`
  - Each section follows its own schema:
    - `mcp_servers`: same as current format — `{toolname}_server` with `mcpServers_format`, `mcp_format`, `servers_format`
    - `one_shot_tools`: `{toolname}_tool` with `command` (list), `run_strategy: "once"`, `output_file` (what it generates)
    - `skill_tools`: `{toolname}_skill` with `source_path` (from useful-repos/), `dest_filename`, `install_strategy: "copy-skill"`
    - `binary_tools`: `{toolname}_binary` with `download_url_template` (OS/arch substitution), `verify_command`, `init_command`, `install_strategy: "binary-download"`
    - `cli_tools`: `{toolname}_cli` with `init_command`, `generated_files` (list of files created), `install_strategy: "cli-init"`
  - Preserve EXISTING `mcp_families` section (unchanged — still needed for MCP server format mapping)
  - Preserve EXISTING `platforms` section (unchanged — 18 platforms with detection_markers, merge_strategy, etc.)
  - Add `version: "2.0.0"` and update `description` to reflect Token Saver Meta scope
  - Add `token_saver_meta` top-level entry with `version`, `core_bundle_tools` (list of 10), `optional_modules` (list of 8)
  - Test: `python -c "import json; json.load(open('platforms/matrix.json')); print('VALID')"` → VALID

  **Must NOT do**:
  - Don't change `mcp_families` structure (3 format families with wrapper_key, server_format, platforms)
  - Don't remove any existing platforms (all 18 must stay)
  - Don't remove existing `gitnexus_server` or `codegraphcontext_server` entries — they'll be MIGRATED in Task 3
  - Don't add tool-specific entries yet (that's Tasks 3 and 4)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: JSON restructuring — schema design, no complex logic
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 3, 4, 5, 6, 7)
  - **Blocks**: Tasks 3, 4 (need restructured schema to add entries)
  - **Blocked By**: Task 1 (need copied matrix.json)

  **References**:
  - `platforms/matrix.json` — current structure (293 lines, 18 platforms, 3 MCP families)
  - `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json:1-40` — top-level schema reference
  - `docs/tool-assumptions.md` — validated tool CLIs from Task 00

  **Acceptance Criteria**:
  - [ ] `platforms/matrix.json` has 5 new top-level sections: `mcp_servers`, `one_shot_tools`, `skill_tools`, `binary_tools`, `cli_tools`
  - [ ] Existing `mcp_families` section unchanged
  - [ ] Existing `platforms` section (18 platforms) unchanged
  - [ ] File is valid JSON with `version: "2.0.0"`
  - [ ] `token_saver_meta` entry exists with `core_bundle_tools` list (10 items)

  **QA Scenarios**:
  ```
  Scenario: Restructured matrix.json is valid JSON with 5 new sections
    Tool: Bash
    Preconditions: platforms/matrix.json exists
    Steps:
      1. python -c "import json; m = json.load(open('platforms/matrix.json')); sections = ['mcp_servers','one_shot_tools','skill_tools','binary_tools','cli_tools']; assert all(s in m for s in sections), f'Missing: {[s for s in sections if s not in m]}'; print('ALL SECTIONS PRESENT')"
      2. Assert output is "ALL SECTIONS PRESENT"
    Expected Result: All 5 new sections exist
    Evidence: .omo/evidence/task-2-sections.txt

  Scenario: Existing platforms and mcp_families are preserved
    Tool: Bash
    Preconditions: platforms/matrix.json exists
    Steps:
      1. python -c "import json; m = json.load(open('platforms/matrix.json')); assert 'platforms' in m; assert 'mcp_families' in m; print(f'Platforms: {len(m[\"platforms\"])}'); print(f'Families: {len(m[\"mcp_families\"])}')"
      2. Assert platforms count >= 17
      3. Assert families count == 3
    Expected Result: 17+ platforms, 3 MCP families preserved
    Evidence: .omo/evidence/task-2-preserved.txt
  ```

  **Commit**: YES
  - Message: `feat(matrix): restructure for 5 tool categories (mcp, one-shot, skill, binary, cli)`
  - Files: `platforms/matrix.json`

- [x] 3. Add MCP server entries to matrix.json (GitNexus, CGC)

  **What to do**:
  - Move existing `gitnexus_server` and `codegraphcontext_server` entries from top-level into `mcp_servers` section
  - Keep ALL 3 format variants for each: `mcpServers_format`, `mcp_format`, `servers_format`
  - Add `description` field to each: "GitNexus — graph-based code intelligence and impact analysis (T1)", "CGC — Cypher queries, dead code detection, hierarchy analysis (T1)"
  - Add `failure_mode: "warn"` to both — if GitNexus/CGC install fails, warn but continue
  - Add `required_binaries: ["node"]` to GitNexus, `required_binaries: ["python", "uv"]` to CGC
  - Test: `python -c "import json; m = json.load(open('platforms/matrix.json')); assert 'gitnexus_server' in m['mcp_servers']; print('MCP SERVERS OK')"` → MCP SERVERS OK

  **Must NOT do**:
  - Don't change the format variant structures (command, args, cwd, workdir — keep identical to combo)
  - Don't change CGC's `cwd: "<CGC_INSTALL_PATH>"` placeholder — this is resolved at install time

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: JSON migration — move existing entries, add metadata fields
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 4, 5, 6, 7)
  - **Blocks**: Tasks 5, 6, 7 (config gen needs entries)
  - **Blocked By**: Task 2 (restructured matrix)

  **References**:
  - `platforms/matrix.json` — existing `gitnexus_server` and `codegraphcontext_server` entries
  - `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json:187-293` — source server definitions

  **Acceptance Criteria**:
  - [ ] `gitnexus_server` and `codegraphcontext_server` are in `mcp_servers` section
  - [ ] Both have `description`, `failure_mode`, and `required_binaries` fields
  - [ ] All 3 format variants preserved unchanged
  - [ ] `uv run pytest tests/test_combo_regression.py` → still PASSES

  **QA Scenarios**:
  ```
  Scenario: MCP server entries are accessible and complete
    Tool: Bash
    Preconditions: platforms/matrix.json restructured
    Steps:
      1. python -c "import json; m = json.load(open('platforms/matrix.json')); gs = m['mcp_servers']['gitnexus_server']; assert 'mcpServers_format' in gs; assert 'mcp_format' in gs; assert 'servers_format' in gs; assert gs['failure_mode'] == 'warn'; print('GITNEXUS OK')"
      2. python -c "import json; m = json.load(open('platforms/matrix.json')); cgs = m['mcp_servers']['codegraphcontext_server']; assert 'mcpServers_format' in cgs; assert cgs['required_binaries'] == ['python', 'uv']; print('CGC OK')"
      3. Assert both commands output "GITNEXUS OK" and "CGC OK"
    Expected Result: Both MCP servers have 3 formats + metadata
    Evidence: .omo/evidence/task-3-mcp-servers.txt
  ```

  **Commit**: YES (groups with Task 4)
  - Message: `feat(matrix): add MCP server entries for GitNexus and CGC`
  - Files: `platforms/matrix.json`

- [x] 4. Add non-MCP tool entries to matrix.json (RTK, codesight, Repomix, caveman, LG-token-saver, kevin-copilot, ContextSlimAI)

  **What to do**:
  - **`one_shot_tools`**: Add `codesight_tool` and `repomix_tool` entries
    - codesight: `command: ["npx", "-y", "codesight"]`, `run_strategy: "once"`, `output_file: "CODESIGHT.md"`, `failure_mode: "warn"`, `required_binaries: ["node"]`
    - repomix: `command: ["npx", "-y", "repomix"]`, `run_strategy: "once"`, `output_file: "repomix-output.txt"`, `failure_mode: "warn"`, `required_binaries: ["node"]`
  - **`skill_tools`**: Add `caveman_skill`, `lg_token_saver_skill`, `kevin_copilot_skill` entries
    - caveman: `source_path: "useful-repos/caveman/skills/caveman/SKILL.md"`, `dest_filename: "SKILL.md"`, `install_strategy: "copy-skill"`, `failure_mode: "warn"`
    - LG-token-saver: `source_path: "useful-repos/LG-token-saver/SKILL.md"`, `dest_filename: "SKILL.md"`, `install_strategy: "copy-skill"`, `failure_mode: "warn"`
    - kevin-copilot: `source_paths: [...]` (copilot-instructions.md + unslop/SKILL.md), `dest_filename: "copilot-instructions.md"`, `install_strategy: "copy-skill"`, `failure_mode: "warn"`
  - **`binary_tools`**: Add `rtk_binary` entry
    - rtk: `download_url_template: "https://github.com/rtk-lang/rtk/releases/latest/download/rtk-{os}-{arch}.{ext}"`, `verify_command: ["rtk", "--version"]`, `init_command: ["rtk", "init", "-g"]`, `install_strategy: "binary-download"`, `failure_mode: "warn"`, `fallback: "cargo install rtk"`, `required_binaries: []` (self-contained binary)
  - **`cli_tools`**: Add `contextslimai_cli` entry
    - contextslimai: `init_command: ["npx", "contextslim", "init"]`, `generated_files: [".cursorrules", "CLAUDE.md"]`, `install_strategy: "cli-init"`, `failure_mode: "warn"`, `required_binaries: ["node"]`

  **Must NOT do**:
  - Don't create MCP server entries for codesight or Repomix (they are NOT MCP servers)
  - Don't use the RTK download URL template if Task 00 found it doesn't exist — use actual release URL
  - Don't add TSCG, lean-ctx, LLMLingua, or other optional modules (Phase 08 only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: JSON data entry — adding structured entries based on validated assumptions
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 5, 6, 7)
  - **Blocks**: Tasks 5, 6, 7 (config gen needs entries)
  - **Blocked By**: Task 2 (restructured matrix), Task 00 (validated tool assumptions)

  **References**:
  - `docs/tool-assumptions.md` — validated CLIs and paths from Task 00
  - `useful-repos/rtk/README.md` — install methods and release URLs
  - `useful-repos/codesight/README.md` — CLI arguments
  - `useful-repos/caveman/skills/` — core SKILL.md path
  - `useful-repos/kevin-copilot/` — copilot-instructions.md path
  - `useful-repos/LG-token-saver/SKILL.md` — verified path
  - `useful-repos/ContextSlimAI/README.md` — init command

  **Acceptance Criteria**:
  - [ ] `one_shot_tools` has `codesight_tool` and `repomix_tool` entries
  - [ ] `skill_tools` has `caveman_skill`, `lg_token_saver_skill`, `kevin_copilot_skill` entries
  - [ ] `binary_tools` has `rtk_binary` entry
  - [ ] `cli_tools` has `contextslimai_cli` entry
  - [ ] All entries have `failure_mode: "warn"` (no tool is critical)
  - [ ] File is valid JSON

  **QA Scenarios**:
  ```
  Scenario: All 7 non-MCP tool entries exist with correct fields
    Tool: Bash
    Preconditions: platforms/matrix.json has all 5 sections
    Steps:
      1. python -c "import json; m = json.load(open('platforms/matrix.json')); ot = m['one_shot_tools']; assert 'codesight_tool' in ot and 'repomix_tool' in ot, f'one_shot: {list(ot.keys())}'; st = m['skill_tools']; assert 'caveman_skill' in st and 'lg_token_saver_skill' in st and 'kevin_copilot_skill' in st, f'skill: {list(st.keys())}'; bt = m['binary_tools']; assert 'rtk_binary' in bt; ct = m['cli_tools']; assert 'contextslimai_cli' in ct; print('ALL 7 TOOLS PRESENT')"
      2. Assert output is "ALL 7 TOOLS PRESENT"
    Expected Result: All 7 non-MCP tools registered
    Evidence: .omo/evidence/task-4-tools.txt

  Scenario: No MCP entries for non-MCP tools
    Tool: Bash
    Preconditions: platforms/matrix.json complete
    Steps:
      1. python -c "import json; m = json.load(open('platforms/matrix.json')); ms = m['mcp_servers']; assert 'codesight_tool' not in ms and 'repomix_tool' not in ms; print('NO MCP LEAKAGE')"
      2. Assert output is "NO MCP LEAKAGE"
    Expected Result: Non-MCP tools correctly excluded from mcp_servers
    Evidence: .omo/evidence/task-4-no-leak.txt
  ```

  **Commit**: YES (groups with Task 3)
  - Message: `feat(matrix): add non-MCP tool entries for all 7 remaining core tools`
  - Files: `platforms/matrix.json`

- [x] 5. Extend config_gen.py for 5-category awareness

  **What to do**:
  - Add function `get_tool_categories() -> dict` — reads matrix.json and returns the 5 category sections
  - Add function `generate_mcp_server_entries(platform_id: str) -> dict` — generates MCP config entries for GitNexus and CGC using existing `generate_server_entry()` logic (same as combo)
  - Add function `get_one_shot_tools() -> list[dict]` — returns all one_shot_tools entries (codesight, Repomix) with their commands and output files
  - Add function `get_skill_tools() -> list[dict]` — returns all skill_tools entries with source paths and destinations
  - Add function `get_binary_tools() -> list[dict]` — returns all binary_tools entries with download URLs and verify commands
  - Add function `get_cli_tools() -> list[dict]` — returns all cli_tools entries with init commands
  - Add function `get_core_tool_list() -> list[str]` — returns all 10 tool names from `token_saver_meta.core_bundle_tools`
  - Keep ALL existing functions unchanged: `load_matrix()`, `detect_platforms()`, `generate_server_entry()`, `generate_mcp_config()`, `merge_into_existing()`, `write_mcp_config()`, `validate_platform()`, `cmd_setup()`, `main()`
  - Test: `uv run python -c "from src.config_gen import get_tool_categories; cats = get_tool_categories(); assert len(cats) == 5; print('OK')"` → OK

  **Must NOT do**:
  - Don't modify existing `generate_mcp_config()` (still used for regression compatibility)
  - Don't delete or rename any existing function
  - Don't change function signatures of existing functions
  - Don't add the tool install logic here — that goes in installer.py (Task 8)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Extending existing codebase — needs to understand combo's architecture deeply, add functions without breaking existing ones
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 6, 7)
  - **Blocks**: Tasks 8-14 (installer needs config gen functions)
  - **Blocked By**: Tasks 3, 4 (matrix entries needed)

  **References**:
  - `src/config_gen.py:29-31` — `load_matrix()` pattern for accessing matrix data
  - `src/config_gen.py:51-54` — `generate_server_entry()` — reuse this for MCP server entries
  - `src/config_gen.py:57-73` — `generate_mcp_config()` — reference for how format families work
  - `platforms/matrix.json` — the restructured data source

  **Acceptance Criteria**:
  - [ ] `get_tool_categories()` returns dict with 5 keys
  - [ ] `get_one_shot_tools()` returns list with codesight + Repomix entries
  - [ ] `get_skill_tools()` returns list with caveman, LG-token-saver, kevin-copilot entries
  - [ ] `get_binary_tools()` returns list with RTK entry
  - [ ] `get_cli_tools()` returns list with ContextSlimAI entry
  - [ ] `get_core_tool_list()` returns 10 items
  - [ ] All existing functions unchanged and still work
  - [ ] `uv run pytest tests/test_combo_regression.py` → PASS

  **QA Scenarios**:
  ```
  Scenario: New functions return correct data from matrix.json
    Tool: Bash
    Preconditions: src/config_gen.py extended, platforms/matrix.json restructured
    Steps:
      1. uv run python -c "from src.config_gen import get_tool_categories, get_one_shot_tools, get_skill_tools, get_binary_tools, get_cli_tools, get_core_tool_list; cats = get_tool_categories(); assert len(cats) == 5; ot = get_one_shot_tools(); assert len(ot) == 2; st = get_skill_tools(); assert len(st) == 3; bt = get_binary_tools(); assert len(bt) == 1; ct = get_cli_tools(); assert len(ct) == 1; cl = get_core_tool_list(); assert len(cl) == 10; print('ALL OK')"
      2. Assert output is "ALL OK"
    Expected Result: All 5 category accessor functions return correct counts
    Evidence: .omo/evidence/task-5-categories.txt

  Scenario: Existing functions still work (regression)
    Tool: Bash
    Preconditions: src/config_gen.py extended
    Steps:
      1. uv run pytest tests/test_combo_regression.py -v
      2. Assert exit code is 0
      3. Assert "PASSED" in output
    Expected Result: Regression test passes — existing functionality unchanged
    Evidence: .omo/evidence/task-5-regression.txt
  ```

  **Commit**: YES
  - Message: `feat(config): add 5-category tool accessor functions to config_gen.py`
  - Files: `src/config_gen.py`

- [x] 6. Implement category-aware merge logic

  **What to do**:
  - Add `generate_all_mcp_entries(platform_id: str) -> dict` — combines GitNexus + CGC MCP entries for a platform (wraps existing `generate_mcp_config()`)
  - Extend `merge_into_existing()` to handle the case where existing config is empty (no `mcpServers` key at all)
  - Add `merge_token_saver_entries(existing: dict, platform_id: str) -> dict` — new function that merges ALL token-saver MCP entries (not just GitNexus+CGC) into existing config
  - Add `remove_token_saver_entries(existing: dict) -> dict` — removes ALL token-saver entries (for uninstall). Identifies entries by prefix: `gitnexus`, `codegraphcontext`
  - Add `has_token_saver_entries(existing: dict) -> bool` — checks if any token-saver MCP entries exist
  - Test: create a test MCP config with existing servers, call merge, verify existing servers preserved + new ones added

  **Must NOT do**:
  - Don't change the core merge logic (preserve existing, add missing)
  - Don't remove user's existing MCP servers during merge
  - Don't merge non-MCP tools into MCP configs

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Critical merge logic — needs careful implementation to avoid destroying user configs
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 7)
  - **Blocks**: Tasks 8, 9, 19 (installer and uninstall need merge functions)
  - **Blocked By**: Tasks 3, 4, 5 (matrix entries + accessor functions needed)

  **References**:
  - `src/config_gen.py:76-84` — existing `merge_into_existing()` to extend
  - `src/config_gen.py:87-139` — `write_mcp_config()` for status handling pattern
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:76-84` — original merge logic

  **Acceptance Criteria**:
  - [ ] `generate_all_mcp_entries("kilo")` returns dict with both GitNexus and CGC in `mcp` format
  - [ ] `merge_token_saver_entries()` preserves existing MCP servers
  - [ ] `remove_token_saver_entries()` removes all token-saver entries, leaves others
  - [ ] `has_token_saver_entries()` correctly detects presence/absence
  - [ ] `uv run pytest tests/test_combo_regression.py` → PASS

  **QA Scenarios**:
  ```
  Scenario: Merge preserves user's existing MCP servers
    Tool: Bash
    Preconditions: src/config_gen.py extended
    Steps:
      1. uv run python -c "from src.config_gen import merge_token_saver_entries; existing = {'mcpServers': {'user-server': {'command': 'echo', 'args': ['hello']}}}; merged = merge_token_saver_entries(existing, 'claude-code'); assert 'user-server' in merged['mcpServers']; assert 'gitnexus' in merged['mcpServers']; print('MERGE OK')"
      2. Assert output is "MERGE OK"
    Expected Result: User's 'user-server' preserved, 'gitnexus' added
    Evidence: .omo/evidence/task-6-merge.txt

  Scenario: Remove removes all token-saver entries only
    Tool: Bash
    Preconditions: src/config_gen.py extended
    Steps:
      1. uv run python -c "from src.config_gen import remove_token_saver_entries; config = {'mcpServers': {'gitnexus': {}, 'codegraphcontext': {}, 'user-server': {}}}; cleaned = remove_token_saver_entries(config); assert 'gitnexus' not in cleaned['mcpServers']; assert 'codegraphcontext' not in cleaned['mcpServers']; assert 'user-server' in cleaned['mcpServers']; print('REMOVE OK')"
      2. Assert output is "REMOVE OK"
    Expected Result: Token-saver entries removed, user entries preserved
    Evidence: .omo/evidence/task-6-remove.txt
  ```

  **Commit**: YES
  - Message: `feat(config): add category-aware merge logic with token-saver entry management`
  - Files: `src/config_gen.py`

- [x] 7. Extend platform detection for all 18 platforms

  **What to do**:
  - Verify existing `detect_platforms()` works correctly for this project (should detect OpenCode + Kilo)
  - Add `detect_all_markers(project_path: Path) -> dict[str, bool]` — returns ALL marker presence, not just first match per platform. Example: `{".kilo/": true, "kilo.json": false, ".opencode/": true, ...}`
  - Add `detect_platform_skills_dir(platform_id: str) -> Path | None` — returns platform-specific skills directory path (e.g., `.kilo/skills/`, `.claude/skills/`, etc.)
  - Add `detect_platform_instructions_file(platform_id: str) -> Path | None` — returns the primary instructions file for a platform (e.g., `AGENTS.md`, `CLAUDE.md`, `.cursorrules`)
  - Test: `uv run python -c "from src.config_gen import detect_platforms; print(detect_platforms(Path('.')))"` → lists detected platforms

  **Must NOT do**:
  - Don't modify existing `detect_platforms()` logic (it works correctly)
  - Don't add support for platforms not in matrix.json

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Adding helper functions to existing detection logic
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: Tasks 8, 12, 15 (installer, skill tools, AGENTS.md injection need platform info)
  - **Blocked By**: Task 1 (need copied config_gen.py)

  **References**:
  - `src/config_gen.py:34-48` — existing `detect_platforms()` to extend
  - `platforms/matrix.json` — `platforms[platform_id].detection_markers` for marker lists
  - `platforms/matrix.json` — `platforms[platform_id].instructions_files` for instructions file paths
  - `platforms/matrix.json` — `platforms[platform_id].skills_dir` for skills directory paths

  **Acceptance Criteria**:
  - [ ] `detect_platforms(Path("."))` detects OpenCode + Kilo on this project
  - [ ] `detect_all_markers(Path("."))` returns dict with all marker states
  - [ ] `detect_platform_skills_dir("kilo")` returns `.kilo/skills/` or similar
  - [ ] `detect_platform_instructions_file("kilo")` returns `AGENTS.md` or similar
  - [ ] `uv run pytest tests/test_combo_regression.py` → PASS

  **QA Scenarios**:
  ```
  Scenario: Platform detection works on this project
    Tool: Bash
    Preconditions: src/config_gen.py extended
    Steps:
      1. uv run python -c "from src.config_gen import detect_platforms; from pathlib import Path; platforms = detect_platforms(Path('.')); print(platforms)"
      2. Assert output contains "kilo" or "opencode" (this project's platforms)
    Expected Result: Detects at least 1 platform on this project
    Evidence: .omo/evidence/task-7-detect.txt
  ```

  **Commit**: YES
  - Message: `feat(config): extend platform detection with marker scanning and skills/instructions helpers`
  - Files: `src/config_gen.py`

- [x] 8. Build installer.py scaffold (detect, env-check, pre-flight)

  **What to do**:
  - Create `src/installer.py` with `main()` entry point
  - Implement `detect_phase(project_path: Path) -> dict` — calls `detect_platforms()` from config_gen, returns `{"platforms": [...], "platform_count": N}`
  - Implement `env_check_phase() -> dict` — checks: Node.js (`node --version`), Python (`python --version`), uv (`uv --version`), git (`git --version`). Returns `{"node": "v22.x", "python": "3.12.x", "uv": "0.x", "git": "2.x", "all_ok": bool, "issues": [...]}`
  - Implement `preflight_phase(project_path: Path) -> dict` — checks: disk space (>100MB free), file permissions (can write to project dir), no existing broken install. Returns `{"disk_ok": bool, "perm_ok": bool, "clean": bool}`
  - Implement `run_phase(phase_name: str, phase_fn, *args) -> tuple[str, dict]` — wrapper that prints `[....] {phase_name}` then `[ OK ]` or `[FAIL]` with result
  - Implement `main()` orchestrator (placeholder for now — will call phases 1-7 sequentially):
    1. Print ASCII art banner "Token Saver Meta v0.1.0"
    2. DETECT phase
    3. ENV-CHECK phase
    4. PRE-FLIGHT phase
    5. INSTALL-CORE phase (placeholder — Tasks 9-14)
    6. INDEX phase (placeholder — Task 14)
    7. INJECT phase (placeholder — Task 15)
    8. VERIFY phase (placeholder — Task 14)
    9. Print summary dashboard
  - Test: `uv run python -m src.installer --detect-only` → prints detected platforms

  **Must NOT do**:
  - Don't implement install logic yet — scaffolding only
  - Don't hardcode platform names — use matrix.json detection
  - Don't fail on missing tools in env_check — produce report, let later phases decide

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core orchestrator — sets the pattern for ALL installation phases
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (blocks all Wave 2 tasks)
  - **Parallel Group**: Wave 2 (sequential with Task 8 first, then 9-14 in parallel)
  - **Blocks**: Tasks 9, 10, 11, 12, 13, 14
  - **Blocked By**: Tasks 5, 6, 7 (config gen functions needed)

  **References**:
  - `src/config_gen.py:150-221` — `cmd_setup()` orchestrator pattern from combo
  - `src/config_gen.py:34-48` — `detect_platforms()` for detection phase
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:150-221` — setup flow pattern

  **Acceptance Criteria**:
  - [ ] `src/installer.py` created with `main()` function
  - [ ] `detect_phase()` returns detected platforms for this project
  - [ ] `env_check_phase()` returns tool versions dict
  - [ ] `preflight_phase()` returns disk/permission status
  - [ ] `uv run python -c "from src.installer import main"` → no import errors

  **QA Scenarios**:
  ```
  Scenario: Installer detects platforms on this project
    Tool: Bash
    Preconditions: src/installer.py exists
    Steps:
      1. uv run python -c "from src.installer import detect_phase; from pathlib import Path; result = detect_phase(Path('.')); print(f'Platforms: {result[\"platforms\"]}')"
      2. Assert output contains detected platform names
    Expected Result: Detects at least 1 platform (OpenCode or Kilo)
    Evidence: .omo/evidence/task-8-detect.txt

  Scenario: Environment check returns tool versions
    Tool: Bash
    Preconditions: Node.js, Python, uv installed
    Steps:
      1. uv run python -c "from src.installer import env_check_phase; result = env_check_phase(); print(f'Node: {result.get(\"node\", \"N/A\")}'); print(f'Python: {result.get(\"python\", \"N/A\")}')"
      2. Assert output contains version strings for Node and Python
    Expected Result: Returns version info for installed tools
    Evidence: .omo/evidence/task-8-env.txt
  ```

  **Commit**: YES
  - Message: `feat(installer): build installer scaffold with detect, env-check, and pre-flight phases`
  - Files: `src/installer.py`

- [x] 9. Implement MCP server installer (GitNexus + CGC)

  **What to do**:
  - Create `src/mcp_installer.py` with `install_mcp_servers(project_path: Path, platforms: list[str]) -> dict`
  - For GitNexus:
    - Check if `npx gitnexus --version` works → if yes, skip install
    - Generate MCP config entries for all detected platforms using `generate_server_entry()`
    - Call `write_mcp_config()` for each platform (from config_gen.py)
    - Track status per platform: `{"kilo": "created", "claude-code": "merged", ...}`
  - For CGC:
    - Check if `uv run cgc --version` or `uv pip show codegraphcontext` works → if yes, skip
    - If not installed: `uv pip install codegraphcontext` (or `uv sync` if pyproject.toml has it)
    - Generate MCP config entries with `cgc_path` resolved to actual install location
  - Return `{"gitnexus": {"status": "ok", "platforms": {...}}, "cgc": {"status": "ok", "platforms": {...}}}`
  - On failure per tool: return `"status": "warn"` with error message (never ABORT)

  **Must NOT do**:
  - Don't overwrite existing MCP configs — use merge_into_existing()
  - Don't fail the entire install if one platform fails — per-platform error isolation
  - Don't attempt CGC install if uv not available

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Subprocess orchestration with multi-platform MCP config generation — moderate complexity
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 10, 11, 12, 13, 14 — all after Task 8)
  - **Blocks**: Tasks 15, 19 (need MCP servers installed)
  - **Blocked By**: Task 8 (installer scaffold)

  **References**:
  - `src/config_gen.py:51-54` — `generate_server_entry()` for generating MCP entries
  - `src/config_gen.py:87-139` — `write_mcp_config()` for writing/merging configs
  - `platforms/matrix.json` → `mcp_servers.gitnexus_server` — server definitions
  - `platforms/matrix.json` → `mcp_servers.codegraphcontext_server` — server definitions
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:150-221` — cmd_setup() for subprocess pattern

  **Acceptance Criteria**:
  - [ ] `src/mcp_installer.py` created with `install_mcp_servers()` function
  - [ ] GitNexus generates MCP configs for all detected platforms
  - [ ] CGC resolves `cgc_path` and generates configs with correct `cwd`/`workdir`
  - [ ] Existing user MCP servers preserved after merge
  - [ ] Test: `uv run python -c "from src.mcp_installer import install_mcp_servers; print('IMPORT OK')"` → IMPORT OK

  **QA Scenarios**:
  ```
  Scenario: GitNexus MCP config generated for test platform
    Tool: Bash
    Preconditions: src/mcp_installer.py exists, Node.js available
    Steps:
      1. uv run python -c "from src.mcp_installer import install_mcp_servers; from pathlib import Path; import tempfile, os; tmp = tempfile.mkdtemp(); Path(tmp, '.kilo').mkdir(); result = install_mcp_servers(Path(tmp), ['kilo']); print(f'GitNexus: {result[\"gitnexus\"][\"status\"]}')"
      2. Assert result["gitnexus"]["status"] is "ok" or "warn"
    Expected Result: GitNexus install reports ok or warn (not error)
    Evidence: .omo/evidence/task-9-mcp-install.txt
  ```

  **Commit**: YES
  - Message: `feat(installer): implement MCP server installer for GitNexus and CGC`
  - Files: `src/mcp_installer.py`

- [x] 10. Implement RTK installer (binary-download strategy)

  **What to do**:
  - Create `src/rtk_installer.py` with `install_rtk() -> dict`
  - Implement OS detection: `platform.system()` → `"Windows"`, `"Darwin"`, `"Linux"`
  - Implement architecture detection: `platform.machine()` → `"x86_64"`, `"arm64"`, `"aarch64"`
  - Check if RTK already installed: `shutil.which("rtk")` or `rtk --version`
  - If not installed:
    - **macOS**: Try `brew install rtk` first, fallback to curl download
    - **Linux**: Download binary from GitHub Releases, install to `~/.local/bin/`
    - **Windows**: Check Task 00 findings. If .exe available: download. If not: try `cargo install rtk` (needs Rust). If no Rust: return `{"status": "warn", "message": "RTK not available for Windows without Rust. Install Rust and run: cargo install rtk"}`
  - After install: Run `rtk init -g` for each detected agent platform (from installer's platform list)
  - Verify: `rtk --version` returns exit code 0
  - Return `{"status": "ok", "version": "x.y.z", "platforms_configured": [...], "install_method": "brew|curl|cargo|skip"}`

  **Must NOT do**:
  - Don't download binaries without verifying checksums (if available)
  - Don't fail the entire install if RTK unavailable on Windows — warn and continue
  - Don't run `rtk init` without `-g` flag (global — per the handover)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Cross-platform binary management with OS detection, fallback chains, and subprocess verification
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 9, 11, 12, 13, 14)
  - **Blocks**: None (RTK is independent)
  - **Blocked By**: Task 8 (installer scaffold)

  **References**:
  - `platforms/matrix.json` → `binary_tools.rtk_binary` — download URL template and commands
  - `docs/tool-assumptions.md` — RTK platform availability from Task 00
  - `useful-repos/rtk/README.md` — install methods per platform

  **Acceptance Criteria**:
  - [ ] `src/rtk_installer.py` created with `install_rtk()` function
  - [ ] OS detection works correctly for Windows, macOS, Linux
  - [ ] `rtk init -g` runs for each detected platform
  - [ ] Windows fallback chain: binary download → cargo install → warn
  - [ ] Test: `uv run python -c "from src.rtk_installer import install_rtk; print('IMPORT OK')"` → IMPORT OK

  **QA Scenarios**:
  ```
  Scenario: RTK installer detects OS and reports status
    Tool: Bash
    Preconditions: src/rtk_installer.py exists
    Steps:
      1. uv run python -c "from src.rtk_installer import install_rtk; import platform; result = install_rtk(); print(f'OS: {platform.system()}'); print(f'Status: {result[\"status\"]}'); print(f'Version: {result.get(\"version\", \"N/A\")}')"
      2. Assert result["status"] is "ok" or "warn" or "skip"
    Expected Result: Reports OS, status, and version (or skip reason)
    Evidence: .omo/evidence/task-10-rtk.txt
  ```

  **Commit**: YES
  - Message: `feat(installer): implement RTK installer with binary-download strategy and OS detection`
  - Files: `src/rtk_installer.py`

- [x] 11. Implement one-shot tools installer (codesight + Repomix)

  **What to do**:
  - Create `src/oneshot_installer.py` with `install_one_shot_tools(project_path: Path) -> dict`
  - For codesight:
    - Check if `CODESIGHT.md` already exists in project root → if yes, skip
    - Run `npx -y codesight` in project directory with 120s timeout
    - Verify: `Test-Path "CODESIGHT.md"` returns true
    - Add `CODESIGHT.md` to `.gitignore` if not already present
  - For Repomix:
    - Check if `repomix-output.txt` or `repomix-output.xml` exists → if yes, skip
    - Check if `.repomixignore` exists → if no, create with sensible defaults (skip node_modules, .git, __pycache__, CODESIGHT.md)
    - Run `npx -y repomix` in project directory with 180s timeout
    - Verify: output file exists
    - Add `repomix-output.*` and `.repomixignore` to `.gitignore`
  - Return `{"codesight": {"status": "ok|skip|warn", "file": "CODESIGHT.md"}, "repomix": {"status": "ok|skip|warn", "file": "repomix-output.txt"}}`

  **Must NOT do**:
  - Don't generate MCP config entries for codesight or Repomix (they are NOT MCP servers)
  - Don't overwrite existing CODESIGHT.md or repomix output (skip if present)
  - Don't fail if npx not available — warn and skip

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Subprocess execution with timeout handling, file verification, .gitignore management
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 9, 10, 12, 13, 14)
  - **Blocks**: None
  - **Blocked By**: Task 8 (installer scaffold)

  **References**:
  - `platforms/matrix.json` → `one_shot_tools.codesight_tool` — command and output file
  - `platforms/matrix.json` → `one_shot_tools.repomix_tool` — command and output file
  - `docs/tool-assumptions.md` — verified CLI arguments from Task 00

  **Acceptance Criteria**:
  - [ ] `src/oneshot_installer.py` created with `install_one_shot_tools()` function
  - [ ] codesight generates CODESIGHT.md in test project
  - [ ] repomix generates output file in test project
  - [ ] Both tools respect skip-if-exists logic
  - [ ] `.gitignore` updated with CODESIGHT.md and repomix patterns

  **QA Scenarios**:
  ```
  Scenario: codesight generates CODESIGHT.md
    Tool: Bash
    Preconditions: src/oneshot_installer.py exists, Node.js available
    Steps:
      1. $tmp = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString(); New-Item -ItemType Directory -Path $tmp; Set-Content -Path "$tmp\test.py" -Value "print('hello')"
      2. uv run python -c "from src.oneshot_installer import install_one_shot_tools; from pathlib import Path; result = install_one_shot_tools(Path('$tmp')); print(result['codesight']['status'])"
      3. Test-Path "$tmp\CODESIGHT.md"
      4. Assert codesight status is "ok" or "warn"
      5. Remove-Item -Recurse -Force $tmp
    Expected Result: CODESIGHT.md generated or install skipped with reason
    Evidence: .omo/evidence/task-11-codesight.txt
  ```

  **Commit**: YES
  - Message: `feat(installer): implement one-shot tools installer for codesight and Repomix`
  - Files: `src/oneshot_installer.py`, `.gitignore` (if updated)

- [x] 12. Implement skill tools installer (caveman, LG-token-saver, kevin-copilot)

  **What to do**:
  - Create `src/skill_installer.py` with `install_skill_tools(project_path: Path, platforms: list[str]) -> dict`
  - Implement `copy_skill_to_platform(source_path: Path, platform_id: str, dest_filename: str) -> dict`:
    - Get platform skills directory via `detect_platform_skills_dir(platform_id)` from config_gen
    - Create `{skills_dir}/token-saver/` subdirectory
    - Copy skill file to `{skills_dir}/token-saver/{dest_filename}`
    - Return `{"status": "ok|skip|warn", "dest": "path/to/file"}`
  - For caveman: Copy `useful-repos/caveman/skills/caveman/SKILL.md` → `token-saver/caveman/SKILL.md` (verified path from Task 00)
  - For LG-token-saver: Copy `useful-repos/LG-token-saver/SKILL.md` → `token-saver/lg-token-saver/SKILL.md`
  - For kevin-copilot: Copy `copilot-instructions.md` and `unslop/SKILL.md` → `token-saver/kevin-copilot/`
  - For combo-workflow: Copy `skills/combo-workflow/SKILL.md` → `token-saver/combo-workflow/SKILL.md` (created in Task 16)
  - Handle platforms without skills support gracefully (check `platforms[platform_id].skills_supported`)

  **Must NOT do**:
  - Don't copy all 7 caveman variants — core SKILL.md only
  - Don't copy all 30+ kevin-copilot files — copilot-instructions.md + unslop/SKILL.md only
  - Don't fail if platform doesn't support skills — skip silently

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: File copy operations with platform routing — straightforward
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 9, 10, 11, 13, 14)
  - **Blocks**: None
  - **Blocked By**: Task 8 (installer scaffold), Task 7 (platform skills dir detection)

  **References**:
  - `platforms/matrix.json` → `skill_tools.*` — source paths and dest filenames
  - `platforms/matrix.json` → `platforms[platform_id].skills_dir` — skills directory per platform
  - `platforms/matrix.json` → `platforms[platform_id].skills_supported` — whether platform supports skills
  - `src/config_gen.py` — `detect_platform_skills_dir()` from Task 7
  - `docs/tool-assumptions.md` — verified SKILL.md paths from Task 00

  **Acceptance Criteria**:
  - [ ] `src/skill_installer.py` created with `install_skill_tools()` function
  - [ ] Caveman SKILL.md copied to correct platform subdirectory
  - [ ] LG-token-saver SKILL.md copied
  - [ ] Kevin-copilot files (2 files) copied
  - [ ] Platforms without skills support handled gracefully

  **QA Scenarios**:
  ```
  Scenario: Skills copied to test project's skills directory
    Tool: Bash
    Preconditions: src/skill_installer.py, useful-repos/LG-token-saver/SKILL.md exist
    Steps:
      1. $tmp = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString(); New-Item -ItemType Directory -Path $tmp; New-Item -ItemType Directory -Path "$tmp\.kilo\skills"
      2. uv run python -c "from src.skill_installer import install_skill_tools; from pathlib import Path; result = install_skill_tools(Path('$tmp'), ['kilo']); print(result['lg-token-saver']['status'])"
      3. Test-Path "$tmp\.kilo\skills\token-saver\lg-token-saver\SKILL.md"
      4. Assert file exists
      5. Remove-Item -Recurse -Force $tmp
    Expected Result: LG-token-saver SKILL.md copied to platform skills dir
    Evidence: .omo/evidence/task-12-skills.txt
  ```

  **Commit**: YES (groups with Tasks 13, 14)
  - Message: `feat(installer): implement skill tools installer for caveman, LG-token-saver, and kevin-copilot`
  - Files: `src/skill_installer.py`

- [x] 13. Implement CLI tools installer (ContextSlimAI)

  **What to do**:
  - Create `src/cli_installer.py` with `install_cli_tools(project_path: Path) -> dict`
  - For ContextSlimAI:
    - Check if `.cursorrules` or `CLAUDE.md` already have ContextSlimAI content → if yes, skip
    - Run `npx contextslim init` in project directory with 60s timeout
    - Verify: generated files exist (`.cursorrules`, `CLAUDE.md`, or whatever Task 00 confirmed)
    - Return `{"contextslimai": {"status": "ok|skip|warn", "files": [...]}}`
  - On failure: `return {"contextslimai": {"status": "warn", "message": "error details"}}`

  **Must NOT do**:
  - Don't fail the install if npx not available — warn and skip
  - Don't overwrite existing .cursorrules or CLAUDE.md without checking for ContextSlimAI markers

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Subprocess execution with generated file verification and marker detection
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 9, 10, 11, 12, 14)
  - **Blocks**: None
  - **Blocked By**: Task 8 (installer scaffold)

  **References**:
  - `platforms/matrix.json` → `cli_tools.contextslimai_cli` — init command and generated files
  - `docs/tool-assumptions.md` — verified CLI from Task 00

  **Acceptance Criteria**:
  - [ ] `src/cli_installer.py` created with `install_cli_tools()` function
  - [ ] ContextSlimAI init runs and generates rules files
  - [ ] Skip logic works when files already exist

  **QA Scenarios**:
  ```
  Scenario: ContextSlimAI generates rules files
    Tool: Bash
    Preconditions: src/cli_installer.py exists, Node.js available
    Steps:
      1. $tmp = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString(); New-Item -ItemType Directory -Path $tmp
      2. uv run python -c "from src.cli_installer import install_cli_tools; from pathlib import Path; result = install_cli_tools(Path('$tmp')); print(result['contextslimai']['status'])"
      3. Assert result status is "ok" or "warn"
      4. Remove-Item -Recurse -Force $tmp
    Expected Result: ContextSlimAI init completes or reports skip
    Evidence: .omo/evidence/task-13-cli.txt
  ```

  **Commit**: YES (groups with Tasks 12, 14)
  - Message: `feat(installer): implement CLI tools installer for ContextSlimAI`
  - Files: `src/cli_installer.py`

- [x] 14. Implement indexing + verification phase

  **What to do**:
  - Create `src/indexer.py` with `run_indexing(project_path: Path) -> dict` and `run_verification(project_path: Path) -> dict`
  - **Indexing**:
    - GitNexus: `npx gitnexus analyze --embeddings --skills` with 300s timeout
    - CGC: `uv run cgc index .` with 180s timeout
    - Both run in parallel if possible (subprocess.Popen)
    - Return `{"gitnexus": {"status": "ok|warn", "output": "..."}, "cgc": {"status": "ok|warn", "output": "..."}}`
  - **Verification**:
    - Check GitNexus: `npx gitnexus status` → verify it responds
    - Check CGC: `uv run cgc stats` → verify it returns file count
    - Check RTK: `rtk --version` → verify exit code 0
    - Check codesight: `Test-Path "CODESIGHT.md"` → verify file exists
    - Check Repomix: `Test-Path "repomix-output.*"` → verify file exists
    - Check skills: verify skills directory has `token-saver/` with SKILL.md files
    - Check ContextSlimAI: verify generated rules files exist
    - Return status dashboard dict with all 9 tools + installer
    - Print formatted status table to stdout

  **Must NOT do**:
  - Don't fail if indexing takes too long — timeout and warn
  - Don't run indexing if GitNexus or CGC install failed (Task 9)
  - Don't print token consumption during verification — just tool status

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Parallel subprocess orchestration with timeout handling and multi-tool verification
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 9, 10, 11, 12, 13)
  - **Blocks**: None
  - **Blocked By**: Task 8 (installer scaffold), Tasks 9, 10, 11, 12, 13 (tools must be installed)

  **References**:
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:194-215` — indexing subprocess pattern
  - `platforms/matrix.json` → `token_saver_meta.core_bundle_tools` — tool list for verification

  **Acceptance Criteria**:
  - [ ] `src/indexer.py` created with `run_indexing()` and `run_verification()` functions
  - [ ] Indexing runs GitNexus analyze and CGC index (possibly in parallel)
  - [ ] Verification checks all 9 tools + prints status table

  **QA Scenarios**:
  ```
  Scenario: Verification produces a status dashboard dict
    Tool: Bash
    Preconditions: src/indexer.py exists, at least some tools installed
    Steps:
      1. uv run python -c "from src.indexer import run_verification; from pathlib import Path; result = run_verification(Path('.')); print(f'Tools checked: {len(result)}'); print(f'Keys: {list(result.keys())}')"
      2. Assert result is a dict with tool names as keys
    Expected Result: Returns dict with status per tool
    Evidence: .omo/evidence/task-14-verify.txt
  ```

  **Commit**: YES (groups with Tasks 12, 13)
  - Message: `feat(installer): implement indexing (GitNexus + CGC) and verification phases`
  - Files: `src/indexer.py`

- [x] 15. Implement AGENTS.md injection (<500 tokens)

  **What to do**:
  - Create `src/agents_injector.py` with `inject_agents_md_section(project_path: Path, platforms: list[str]) -> dict`
  - Create `templates/agents_md_section.md` — the injection template (<500 tokens):
    ```markdown
    <!-- token-saver:start -->
    ## Token Saver Protocol
    This project has 10 token-saving tools installed.
    ### Priority Order
    1. codesight: Read CODESIGHT.md first (~200 tok vs 40K+ file reads)
    2. GitNexus: Impact analysis before editing any symbol
    3. CGC: Dead code and hierarchy queries
    4. RTK: Shell output auto-compressed — use `rtk <cmd>`
    ### Always
    - Query graphs over grepping files
    - Check impact before editing
    - Speak tersely (caveman protocol)
    ### Never
    - Never grep for code structure — use graph queries
    - Never read large files whole — use codesight wiki articles
    - Never ignore impact analysis warnings
    <!-- token-saver:end -->
    ```
  - Implement 3-way inject logic per platform:
    - **File exists WITH `<!-- token-saver:start -->` marker**: Replace content between markers
    - **File exists WITHOUT marker**: Append the full block at end of file
    - **File does not exist**: Create file with block
  - Get the target file per platform via `detect_platform_instructions_file()` (Task 7)
  - Create `.bak-YYYYMMDD-HHMMSS` backup before modifying any file
  - Return `{"kilo": "created|updated|skipped", "claude-code": "created|updated|skipped", ...}`

  **Must NOT do**:
  - Don't exceed 500 tokens for the injection content (verify: run through token counter)
  - Don't inject savings claims — those go in the dashboard
  - Don't inject per-tool documentation — only combo-workflow rules
  - Don't modify files without creating .bak backup

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: File parsing with marker detection and content injection — straightforward text manipulation
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 16, 17, 18)
  - **Blocks**: Task 19 (uninstall needs to know injection structure)
  - **Blocked By**: Tasks 9-14 (tools must be installed before injection)

  **References**:
  - `C:\Dev\projects\gitnexus_CGC_combo\AGENTS.md` — marker injection pattern (`<!-- gitnexus:start -->` / `<!-- gitnexus:end -->`)
  - `src/config_gen.py` — `detect_platform_instructions_file()` from Task 7
  - `progress_docs/handovers/phase07-core-bundle-implementation.md:159-184` — injection content draft

  **Acceptance Criteria**:
  - [ ] `src/agents_injector.py` created with `inject_agents_md_section()` function
  - [ ] `templates/agents_md_section.md` created with <500 tokens
  - [ ] 3-way inject logic works: update markers, append, create
  - [ ] .bak backup created before any file modification
  - [ ] Running inject twice on same file produces identical result (idempotent)

  **QA Scenarios**:
  ```
  Scenario: Injection creates backup and writes markers
    Tool: Bash
    Preconditions: src/agents_injector.py, templates/agents_md_section.md exist
    Steps:
      1. $tmp = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString(); New-Item -ItemType Directory -Path $tmp; Set-Content -Path "$tmp\AGENTS.md" -Value "# Test Project"
      2. uv run python -c "from src.agents_injector import inject_agents_md_section; from pathlib import Path; result = inject_agents_md_section(Path('$tmp'), ['kilo']); print(result['kilo'])"
      3. Get-Content "$tmp\AGENTS.md" | Select-String "token-saver:start"
      4. Get-ChildItem "$tmp\*.bak-*" | Select-Object -First 1
      5. Assert marker found in AGENTS.md
      6. Assert at least one .bak file exists
      7. Remove-Item -Recurse -Force $tmp
    Expected Result: AGENTS.md has token-saver markers, backup created
    Evidence: .omo/evidence/task-15-inject.txt
  ```

  **Commit**: YES
  - Message: `feat(injection): implement AGENTS.md injection with combo-workflow rules (<500 tokens)`
  - Files: `src/agents_injector.py`, `templates/agents_md_section.md`

- [x] 16. Create combo-workflow SKILL.md

  **What to do**:
  - Create `skills/combo-workflow/SKILL.md` — the master skill teaching agents to use all 10 tools as a system
  - Content structure (keep under 3,000 tokens — it's loaded on-demand, not every turn):
    ```markdown
    # Token Saver Combo Workflow
    ## Quick Reference
    | Tool | Command | When to Use |
    |------|---------|-------------|
    | codesight | Read CODESIGHT.md | Session start — project overview |
    | GitNexus | gitnexus_impact() | Before editing any symbol |
    | CGC | cgc_query() | Dead code, hierarchy, Cypher |
    | RTK | rtk <cmd> | Any shell command — auto-compressed |
    | Repomix | Read repomix-output | Need full codebase context |
    | caveman | Speak tersely | Always active (style) |
    | LG-token-saver | Parallelize, dedup | Always active (operations) |
    | kevin-copilot | Follow instructions | Always active (structure) |
    | ContextSlimAI | — | Already configured in rules files |

    ## Priority Flow
    1. codesight FIRST (200 tok overview vs 40K+ file reads)
    2. GitNexus for impact analysis
    3. CGC for structural queries
    4. Repomix for full-context dumps
    5. RTK wraps every shell call

    ## Anti-Patterns
    - ❌ grep before querying Graph — 10-100x more tokens
    - ❌ read_file() on >200 line files — use codesight wiki articles
    - ❌ sequential shell calls — batch with `&&` for RTK compression
    ```
  - Include tool priority order, anti-patterns, and quick reference table
  - This file gets copied to platform skills dirs by Task 12

  **Must NOT do**:
  - Don't exceed 3,000 tokens (on-demand load, not injected into every session)
  - Don't duplicate AGENTS.md injection content — AGENTS.md has behavioral rules only, SKILL.md has full workflow
  - Don't include savings claims (dashboard only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Writing structured markdown documentation — no code
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 15, 17, 18)
  - **Blocks**: Task 12 (skill installer copies this file)
  - **Blocked By**: None (can write independently)

  **References**:
  - `AGENTS.md` — project architecture for tool descriptions
  - `BESTS.md` — tool rankings for priority ordering
  - `docs/insight_registry.md` — I02 (different depths), I03 (static maps first), I11 (behavioral rules)

  **Acceptance Criteria**:
  - [ ] `skills/combo-workflow/SKILL.md` created
  - [ ] Includes quick reference table with all 9 tools (excluding installer)
  - [ ] Includes priority flow (1-5)
  - [ ] Includes anti-patterns section
  - [ ] Under 3,000 tokens

  **QA Scenarios**:
  ```
  Scenario: Combo-workflow SKILL.md is valid and complete
    Tool: Bash
    Preconditions: skills/combo-workflow/SKILL.md exists
    Steps:
      1. Get-Content skills/combo-workflow/SKILL.md | Select-String "Quick Reference"
      2. Get-Content skills/combo-workflow/SKILL.md | Select-String "Priority Flow"
      3. Get-Content skills/combo-workflow/SKILL.md | Select-String "Anti-Patterns"
      4. Assert all three sections exist
    Expected Result: All required sections present
    Evidence: .omo/evidence/task-16-skill.txt
  ```

  **Commit**: YES
  - Message: `feat(skills): create combo-workflow SKILL.md with tool priority order and anti-patterns`
  - Files: `skills/combo-workflow/SKILL.md`

- [x] 17. Extract and copy tool SKILL.md files from useful-repos/

  **What to do**:
  - Create `skills/caveman/SKILL.md` — copy from `useful-repos/caveman/skills/caveman/SKILL.md` (path from Task 00)
  - Create `skills/lg-token-saver/SKILL.md` — copy from `useful-repos/LG-token-saver/SKILL.md`
  - Create `skills/kevin-copilot/` directory with:
    - `copilot-instructions.md` — copy from `useful-repos/kevin-copilot/...` (path from Task 00)
    - `unslop/SKILL.md` — copy from `useful-repos/kevin-copilot/...` (path from Task 00)
  - Verify each copied file: non-empty, valid markdown (has `#` heading)
  - If any source file doesn't exist (Task 00 would have caught this), note in a README: "Skills pending extraction from [source]"

  **Must NOT do**:
  - Don't copy all caveman variants — core SKILL.md only
  - Don't copy all kevin-copilot files — 2 files only
  - Don't modify source files — verbatim copies

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: File copy operations with verification
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 15, 16, 18)
  - **Blocks**: Task 12 (skill installer uses these files)
  - **Blocked By**: Task 00 (validated source paths)

  **References**:
  - `docs/tool-assumptions.md` — verified SKILL.md paths from Task 00
  - `useful-repos/caveman/skills/caveman/SKILL.md` — caveman source
  - `useful-repos/LG-token-saver/SKILL.md` — LG source
  - `useful-repos/kevin-copilot/` — kevin-copilot source directory

  **Acceptance Criteria**:
  - [ ] `skills/caveman/SKILL.md` exists (non-empty)
  - [ ] `skills/lg-token-saver/SKILL.md` exists (non-empty)
  - [ ] `skills/kevin-copilot/copilot-instructions.md` exists
  - [ ] `skills/kevin-copilot/unslop/SKILL.md` exists
  - [ ] All files are valid markdown (contain `#` heading)

  **QA Scenarios**:
  ```
  Scenario: All skill files are present and valid
    Tool: Bash
    Preconditions: skills/ directory populated
    Steps:
      1. Test-Path "skills/caveman/SKILL.md"; Test-Path "skills/lg-token-saver/SKILL.md"; Test-Path "skills/kevin-copilot/copilot-instructions.md"; Test-Path "skills/kevin-copilot/unslop/SKILL.md"
      2. Get-Content "skills/caveman/SKILL.md" | Select-String "^#" 
      3. Assert all 4 files exist
      4. Assert caveman SKILL.md has at least one heading
    Expected Result: All 4 skill files present with markdown headings
    Evidence: .omo/evidence/task-17-skills.txt
  ```

  **Commit**: YES (groups with Task 16)
  - Message: `feat(skills): extract caveman, LG-token-saver, and kevin-copilot SKILL.md files`
  - Files: `skills/caveman/SKILL.md`, `skills/lg-token-saver/SKILL.md`, `skills/kevin-copilot/copilot-instructions.md`, `skills/kevin-copilot/unslop/SKILL.md`

- [x] 18. Create build system & distribution entry points

  **What to do**:
  - Update `pyproject.toml` (created in Task 0) with:
    - `[project.dependencies]`: none (zero-dependency core — uses stdlib only)
    - `[project.optional-dependencies]`: `dev = ["pytest", "ruff"]`
    - `[project.scripts]`: `token-saver = "src.installer:main"`
    - `[tool.ruff]`: line-length 120, target-version py310
  - Create `package.json`:
    ```json
    {
      "name": "create-token-saver",
      "version": "0.1.0",
      "description": "Token Saving for the Masses — zero-config token-saving toolkit",
      "bin": { "create-token-saver": "./cli.js" },
      "files": ["cli.js", "src/", "platforms/", "skills/", "templates/", "dashboard/"]
    }
    ```
  - Update `cli.js` (copied in Task 1) to bridge to Python installer:
    - Try: `uvx token-saver-meta setup <project_path>` first
    - Fallback: `uv run python -m src.installer <project_path>`
    - Fallback: `python -m src.installer <project_path>`
  - Create `src/__init__.py` (empty, signals package)
  - Test: `uvx token-saver-meta --help` → shows usage (or `uv run token-saver --help`)

  **Must NOT do**:
  - Don't add npm dependencies — cli.js is vanilla Node.js
  - Don't add Python dependencies beyond stdlib — zero-dependency core
  - Don't publish to npm or PyPI — that's Phase 09

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: JSON/TOML configuration + JS bridge update — no complex logic
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 15, 16, 17)
  - **Blocks**: None
  - **Blocked By**: Task 8 (installer.py must exist for entry point)

  **References**:
  - `C:\Dev\projects\gitnexus_CGC_combo\pyproject.toml` — reference pyproject.toml
  - `C:\Dev\projects\gitnexus_CGC_combo\package.json` — reference package.json (if exists)
  - `C:\Dev\projects\gitnexus_CGC_combo\cli.js` — JS→Python bridge pattern
  - `pyproject.toml` (local) — created in Task 0, update now

  **Acceptance Criteria**:
  - [ ] `pyproject.toml` has `[project.scripts]` with `token-saver` entry point
  - [ ] `package.json` has `bin` pointing to `cli.js`
  - [ ] `cli.js` bridges to Python installer with fallback chain
  - [ ] `src/__init__.py` exists
  - [ ] `uv run token-saver --help` works (or at minimum: `uv run python -m src.installer --help`)

  **QA Scenarios**:
  ```
  Scenario: pyproject.toml is valid and installable
    Tool: Bash
    Preconditions: pyproject.toml updated
    Steps:
      1. uv pip install -e . --dry-run 2>&1 | Select-String "Would install"
      2. python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('VALID')"
      3. Assert pyproject.toml is valid TOML
    Expected Result: pyproject.toml valid, package installable
    Evidence: .omo/evidence/task-18-pyproject.txt

  Scenario: package.json is valid JSON
    Tool: Bash
    Preconditions: package.json exists
    Steps:
      1. python -c "import json; p = json.load(open('package.json')); assert p['name'] == 'create-token-saver'; print('VALID')"
      2. Assert output is "VALID"
    Expected Result: package.json is valid JSON with correct name
    Evidence: .omo/evidence/task-18-package.txt
  ```

  **Commit**: YES
  - Message: `feat(distribution): add pyproject.toml, package.json, cli.js, and src/__init__.py`
  - Files: `pyproject.toml`, `package.json`, `cli.js`, `src/__init__.py`

- [x] 19. Build uninstall command

  **What to do**:
  - Create `src/uninstall.py` with `uninstall_all(project_path: Path) -> dict` and CLI entry point
  - **Phase 1 — Confirm**: Print what will be removed (list all MCP entries, AGENTS.md sections, generated files) and ask confirmation (unless `--force` flag)
  - **Phase 2 — Backup**: Create `.bak-YYYYMMDD-HHMMSS` of every file that will be modified
  - **Phase 3 — Remove MCP entries**:
    - For each platform detected, read MCP config file
    - Call `remove_token_saver_entries()` (Task 6) to strip all token-saver entries
    - Write back (preserving non-token-saver entries)
  - **Phase 4 — Remove AGENTS.md sections**:
    - For each platform's instructions file, detect `<!-- token-saver:start -->` / `<!-- token-saver:end -->`
    - Remove everything between (and including) the markers
  - **Phase 5 — Remove generated files**:
    - CODESIGHT.md (if exists)
    - repomix-output.* (if exists)
    - .repomixignore (if created by installer)
    - Remove CODESIGHT.md and repomix patterns from .gitignore
  - **Phase 6 — Remove RTK binary**:
    - Check `rtk --version` → if installed by us (tracked), offer to uninstall
    - Print manual uninstall instructions per platform
  - **Phase 7 — Summary**: Print what was removed, files backed up, and what remains

  **Must NOT do**:
  - Don't delete without confirmation (unless `--force`)
  - Don't remove user's existing MCP servers — only token-saver entries
  - Don't delete AGENTS.md files — only remove the injected section
  - Don't remove RTK if it was pre-existing (can't distinguish, so always print manual instructions)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multi-phase reversible cleanup with backup creation, config parsing, and cross-platform file handling
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 20)
  - **Blocks**: None
  - **Blocked By**: Task 15 (needs injection structure to reverse)

  **References**:
  - `src/config_gen.py` — `remove_token_saver_entries()` from Task 6
  - `src/agents_injector.py` — marker pattern for removal
  - `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py:76-84` — merge logic (reverse of)

  **Acceptance Criteria**:
  - [ ] `src/uninstall.py` created with `uninstall_all()` function
  - [ ] Confirmation prompt (unless `--force`)
  - [ ] Removes MCP entries without touching user's servers
  - [ ] Removes AGENTS.md token-saver section, leaves rest
  - [ ] Creates .bak backup before any modification
  - [ ] Prints summary of removed items
  - [ ] `uv run token-saver uninstall --force` works end-to-end

  **QA Scenarios**:
  ```
  Scenario: Uninstall reverses AGENTS.md injection
    Tool: Bash
    Preconditions: src/uninstall.py exists
    Steps:
      1. $tmp = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString(); New-Item -ItemType Directory -Path $tmp
      2. Set-Content -Path "$tmp\AGENTS.md" -Value "# Original Content`n<!-- token-saver:start -->`n## Token Saver Protocol`n<!-- token-saver:end -->`n# More Content"
      3. uv run python -c "from src.uninstall import uninstall_all; from pathlib import Path; result = uninstall_all(Path('$tmp'), force=True); print(result['agents_md']['status'])"
      4. $content = Get-Content "$tmp\AGENTS.md" -Raw
      5. Assert $content -notmatch "token-saver:start"
      6. Assert $content -match "Original Content"
      7. Assert $content -match "More Content"
      8. Remove-Item -Recurse -Force $tmp
    Expected Result: Token-saver section removed, original content preserved
    Evidence: .omo/evidence/task-19-uninstall.txt
  ```

  **Commit**: YES
  - Message: `feat(uninstall): implement automated uninstall with backup, MCP cleanup, and AGENTS.md restoration`
  - Files: `src/uninstall.py`

- [x] 20. Build dashboard scaffold

  **What to do**:
  - Create `dashboard/index.html` — static HTML status page
  - **Layout**: 4-column table with Tool, Status, Version, Savings columns
  - **Content per tool**:
    - GitNexus: Status (Indexed/Stale/Not Installed), Version, Savings "7x-91x*"
    - CGC: Status, Version, Savings "File count: N"
    - RTK: Status, Version, Savings "60-90%†"
    - codesight: Status (CODESIGHT.md stale/fresh), N/A, Savings "~70%"
    - Repomix: Status (Packed/Stale), N/A, Savings "~70%"
    - caveman: Status, N/A, Savings "~75%*"
    - LG-token-saver: Status, N/A, Savings "87% claimed*"
    - kevin-copilot: Status, N/A, Savings "66-89%‡"
    - ContextSlimAI: Status, N/A, Savings "N/A"
    - Token Saver Meta: Status (All tools ok / N issues), v0.1.0, "—"
  - **Footer**: Disclaimer — "* self-reported, † benchmarked by category, ‡ CI-gated evals. Do not add percentages."
  - Style: Minimalist, dark background, green/red status dots, monospace font
  - Create `src/dashboard.py`:
    - `serve_dashboard(port: int = 8080) -> None` — starts `http.server` on `dashboard/` directory
    - CLI entry point: `token-saver dashboard [--port PORT]`
  - Add `[project.scripts]` entry: `token-saver-dashboard = "src.dashboard:main"`

  **Must NOT do**:
  - Don't make it interactive — static HTML only in Phase 07
  - Don't include aggregate savings numbers
  - Don't use external CSS/JS frameworks — vanilla HTML/CSS
  - Don't require JavaScript to render — basic HTML table

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Static HTML dashboard with status indicators — visual layout with dark theme
  - **Skills**: [`ui-ux-pro-max`]
    - `ui-ux-pro-max`: For color palette and status indicator design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Task 19)
  - **Blocks**: None
  - **Blocked By**: None (can build independently)

  **References**:
  - `useful-repos/ClaudeCode-Token-Guard/dashboard.html` — inspiration for token dashboard
  - `BESTS.md` — savings claims per tool (only use verified claims)
  - `docs/insight_registry.md` — I11, I12 for behavioral rules context

  **Acceptance Criteria**:
  - [ ] `dashboard/index.html` created with 10-tool table
  - [ ] Each tool has Status, Version, and Savings columns
  - [ ] Disclaimer footer present
  - [ ] `src/dashboard.py` created with `serve_dashboard()` function
  - [ ] `uv run python -m http.server 8080 -d dashboard/` serves the page
  - [ ] `curl -s http://localhost:8080/ | findstr "Token Saver"` returns match

  **QA Scenarios**:
  ```
  Scenario: Dashboard serves and contains tool names
    Tool: Bash
    Preconditions: dashboard/index.html exists
    Steps:
      1. Start-Process -NoNewWindow python -ArgumentList "-m","http.server","8080","-d","dashboard/"
      2. Start-Sleep -Seconds 2
      3. $response = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing
      4. Assert $response.StatusCode -eq 200
      5. Assert $response.Content -match "GitNexus"
      6. Assert $response.Content -match "RTK"
      7. Assert $response.Content -match "Token Saver"
      8. Stop-Process -Name python -Force -ErrorAction SilentlyContinue
    Expected Result: Dashboard serves with 200, contains tool names
    Evidence: .omo/evidence/task-20-dashboard.txt
  ```

  **Commit**: YES
  - Message: `feat(dashboard): add static HTML status dashboard with tool health and savings`
  - Files: `dashboard/index.html`, `src/dashboard.py`

---

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command, curl endpoint). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run ruff check src/` + `uv run pytest`. Review all changed files for: `# type: ignore`, bare `except:`, `print()` instead of logging, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration: full install → uninstall → reinstall (idempotency). Test edge cases: empty project, missing tools, Windows RTK fallback, AGENTS.md with and without markers. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **0**: `chore(scaffold): add test infrastructure, .gitignore, and copy foundation code` — pyproject.toml, tests/, .gitignore, src/config_gen.py, platforms/matrix.json
- **1**: `feat(matrix): restructure for 5 tool categories with all 10 core tools` — platforms/matrix.json
- **2**: `feat(installer): build unified 10-tool installer engine` — src/installer.py, src/config_gen.py, src/*_setup.py
- **3**: `feat(injection): add AGENTS.md protocol and combo-workflow SKILL.md` — templates/, skills/, src/inject_agents_md.py
- **4**: `feat(distribution): add pyproject.toml, package.json, cli.js, uninstall, dashboard` — pyproject.toml, package.json, cli.js, src/uninstall.py, src/dashboard.py
- **Pre-commit**: `uv run ruff check src/ && uv run pytest`

---

## Success Criteria

### Verification Commands
```bash
# Test suite
uv run pytest                          # All tests pass
uv run pytest -v                       # Verbose: see all test names

# Installer
uvx token-saver-meta setup ./test-project    # Zero errors, all 10 tools
npx create-token-saver ./test-project         # npm entry point works

# Idempotency
uvx token-saver-meta setup ./test-project    # Second run: "All tools already installed"

# Uninstall
token-saver uninstall ./test-project         # All MCP entries removed, .bak created

# Dashboard
token-saver dashboard                         # Serves on port 8080
curl -s http://localhost:8080/ | findstr "Token Saver"  # Dashboard loads
```

### Final Checklist
- [ ] All 20 tasks completed with evidence
- [ ] F1-F4 all return VERDICT: APPROVE
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All pytest tests pass
- [ ] Idempotency verified (install twice = same result)
- [ ] Combo regression verified (existing GitNexus+CGC output unchanged)
- [ ] Dashboard serves on port 8080 with tool status
