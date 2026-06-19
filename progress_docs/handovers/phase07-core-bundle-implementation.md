# Token Saver Meta — Next Session Handover

> **To the next AI agent (or human):** This document contains everything you need to begin implementing Token Saver Meta. Read it in full before writing any code.

---

## 1. WHAT THIS PROJECT IS

**Token Saver Meta** is a meta-package that bundles token-saving developer tools into one zero-config install for non-technical users. Think: "I downloaded this and it just works — my AI agent now uses 60-90% fewer tokens."

The project builds on the existing **gitnexus_CGC_combo** project (which already handles multi-platform MCP config generation, AGENTS.md injection, and agent protocol enforcement) and extends it with many more tools.

---

## 2. CURRENT STATE (2026-06-13)

### Research: COMPLETE
- **61 sources** studied (44 repos + 17 discussions)
- **44 repos** cloned to `useful-repos/`
- **37 insights** extracted and catalogued
- **22 synergies** identified
- **Only 1 genuine conflict** found across all tools (RTK shell hook vs lean-ctx shell hook)
- **All savings claims fact-checked** against actual READMEs

### Architecture: FINALIZED
- **Core bundle:** 10 tools (see §4)
- **Optional modules:** 8 tools
- **Deep study queue:** 8 tools for v2
- **Design principles** inherited from gitnexus_CGC_combo (idempotent merge, detect-don't-assume, agent-is-the-runtime)

### Infrastructure: SET UP
- `BESTS.md` — tool leaderboard (44 tools, 4 tiers)
- `docs/insight_registry.md` — selected insights
- `docs/insights_and_synergies.md` — complete 37 insights + 22 synergies
- `progress_docs/` — phase tracking (README, current.md, plans/full.md)
- `AGENTS.md` — full agent protocol with insight finding process
- `MEMORY.md`, `kilo.json`, `opencode.jsonc` — scaffold files

---

## 3. REFERENCE DOCUMENTS — READ THESE FIRST

### Authoritative Architecture (MUST read)
| Document | Path | What It Contains |
|----------|------|-----------------|
| **Maximum Coexistence Set** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-max-coexistence.md` | 15 tools, 3 tiers, only 1 conflict. THIS IS THE ARCHITECTURE. |
| **Complete Insights & Synergies** | `docs/insights_and_synergies.md` | 37 insights + 22 synergies. How tools compound. |
| **Conflict Resolution** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-conflict-resolution.md` | Why certain tools were chosen over others. |
| **Savings Audit** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-savings-audit.md` | Fact-checked claims. NEVER publish unverified aggregate savings. |

### Foundation Project (MUST study)
| Document | Path | What It Contains |
|----------|------|-----------------|
| **gitnexus_CGC_combo AGENTS.md** | `C:\Dev\projects\gitnexus_CGC_combo\AGENTS.md` | 8-phase bootstrap protocol — the FOUNDATION we build on |
| **config_gen.py** | `C:\Dev\projects\gitnexus_CGC_combo\src\config_gen.py` | MCP config generation engine (~354 LOC). We extend this. |
| **matrix.json** | `C:\Dev\projects\gitnexus_CGC_combo\platforms\matrix.json` | Platform registry (17 platforms, 3 MCP families). We add new tools. |
| **DESIGN_RATIONALE.md** | `C:\Dev\projects\gitnexus_CGC_combo\docs\DESIGN_RATIONALE.md` | The philosophy: "agent IS the runtime, AGENTS.md is the program" |

### Source Inventory
| Document | Path |
|----------|------|
| **Source Inventory (61 sources)** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-source-inventory.md` |
| **Evaluation Notes (batch 1)** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-evaluation-notes.md` |
| **Brainstorm (historical)** | `C:\Dev\ideas\project-ideas_structured\token-saver-meta.md` |

---

## 4. THE ARCHITECTURE — WHAT TO BUILD

### Core Bundle (10 tools — always installed, zero config)

| # | Tool | Token Types | Install Method | What You Need to Implement |
|---|------|:----------:|----------------|---------------------------|
| 1 | **GitNexus** | T1 | `npx -y gitnexus@latest mcp` | Copy from combo's config_gen.py. MCP config entry. |
| 2 | **CGC** | T1 | `uv run cgc mcp` (or `uv pip install cgc`) | Copy from combo. MCP config entry with workdir. |
| 3 | **RTK** | T2 | Binary download (brew/cargo/curl) | Auto-detect OS → download binary → run `rtk init -g` for each detected agent. |
| 4 | **codesight** | T1 | `npx codesight` | Run `npx codesight` on project. Add CODESIGHT.md to .gitignore. |
| 5 | **Repomix** | T1 | `npx repomix` | Run `npx repomix` on first setup. Add .repomixignore. |
| 6 | **caveman** | T3 | SKILL.md only (zero deps) | Copy SKILL.md from `useful-repos/caveman/skills/caveman/SKILL.md` to platform's skills dir. |
| 7 | **LG-token-saver** | T1+T2+T3 | SKILL.md only (zero deps) | Copy SKILL.md from `useful-repos/LG-token-saver/SKILL.md`. |
| 8 | **ContextSlimAI** | T2 | `npx contextslim` | Run `contextslim init` for AI rules + ignore files generation. |
| 9 | **kevin-copilot** | T3 | Instruction files | Copy instruction files from `useful-repos/kevin-copilot/`. |
| 10 | **Token Saver Meta** | — | `npx create-token-saver` or `uvx` | **THIS IS WHAT YOU BUILD.** Unified installer + AGENTS.md injection. |

### Optional Modules (8 tools — one-click enable)

| # | Tool | Enable Command | Notes |
|---|------|---------------|-------|
| 11 | **TSCG** | `token-saver enable tscg` | `@tscg/mcp-proxy` — wrap all MCP servers |
| 12 | **lean-ctx MCP** | `token-saver enable lean-ctx` | Shell hook DISABLED (conflicts with RTK) |
| 13 | **LLMLingua-2** | `token-saver enable llmlingua` | GPU auto-detect. CPU: warn and ask. |
| 14 | **codex-agent-mem** | `token-saver enable codex-agent-mem` | MCP config for continuity packs |
| 15 | **Loom** | `token-saver enable loom` | MCP config for persistent symbol index |
| 16 | **Deblank** | `token-saver enable deblank` | REST API wrapper for whitespace stripping |
| 17 | **toon** | `token-saver enable toon` | Serialization transform module |
| 18 | **orchestkit-skills** | `token-saver enable orchestkit-skills` | Universal skills extracted from orchestkit |

---

## 5. IMPLEMENTATION PHASES (Priority Order)

### Phase 07: Core Bundle Installer ⏳ (THIS SESSION'S TASK)

**Goal:** Build the unified installer that sets up all 10 core tools with zero user configuration.

#### Step 7.1 — Extend MCP Config Engine
- **File:** `src/config_gen.py` (copy from gitnexus_CGC_combo/src/config_gen.py and extend)
- **Add new tool entries to `platforms/matrix.json`:**
  ```json
  {
    "rtk_server": {
      "description": "RTK — CLI output compression (60-90% savings). Binary must be pre-installed.",
      "mcpServers_format": {},  // RTK doesn't have MCP — it's hook-based
      "mcp_format": {},
      "servers_format": {},
      "install_strategy": "binary-download"  // NEW strategy
    },
    "codesight_server": {
      "mcpServers_format": {
        "command": "npx", "args": ["-y", "codesight", "--mcp"]
      },
      "mcp_format": {
        "type": "local", "command": ["npx", "-y", "codesight", "--mcp"]
      },
      "servers_format": {
        "type": "stdio", "command": "npx", "args": ["-y", "codesight", "--mcp"]
      }
    }
    // ... repeat for Repomix, etc.
  }
  ```
- **Challenge:** RTK is NOT an MCP server — it's a hook-based CLI tool. Need a NEW strategy: `install_strategy: "binary-download"` that detects OS, downloads binary, runs `rtk init -g` per detected agent.

#### Step 7.2 — Build the Unified Installer
- **File:** `src/installer.py` (new)
- **Flow:**
  ```
  1. DETECT: Scan project for agent platforms (reuse config_gen.py detect_platforms)
  2. ENV-CHECK: Node.js, Python, uv, git versions (reuse combo AGENTS.md Phase 1 commands)
  3. PRE-FLIGHT: Check disk space, network, file permissions
  4. INSTALL-CORE:
     a. GitNexus: `npx gitnexus --version` (auto-fetches)
     b. CGC: `uv sync` or `uv pip install codegraphcontext`
     c. RTK: Detect OS → download binary → `rtk init -g` per agent
     d. codesight: `npx codesight` (generates CODESIGHT.md)
     e. Repomix: `npx repomix` (generates repomix output)
     f. caveman: Copy SKILL.md to skills dir
     g. LG-token-saver: Copy SKILL.md to skills dir
     h. ContextSlimAI: `npx contextslim init`
     i. kevin-copilot: Copy instruction files
  5. INDEX: `npx gitnexus analyze --embeddings --skills` + `uv run cgc index .`
  6. INJECT: Write AGENTS.md protocol (reuse combo AGENTS.md Phase 6 pattern)
  7. VERIFY: Check all tools working, print status dashboard
  ```

#### Step 7.3 — Write AGENTS.md Injection
- **File:** `src/inject_agents_md.py` (or have the agent handle it — per the design principle "agent IS the runtime")
- **Content to inject** (between `<!-- token-saver:start -->` markers):
  ```markdown
  # Token Saver Meta Protocol
  This project uses Token Saver Meta (10 token-saving tools).
  
  ## Always Do
  - Prefer GitNexus/CGC graph queries over grep/glob for code exploration
  - Use `npx codesight` context map at session start
  - Run `gitnexus_impact()` before editing any symbol
  - Use RTK-aware commands (rtk automatically wraps CLI output)
  - Speak tersely (caveman protocol active)
  - Follow LG-token-saver operational rules (parallelism, dedup, compaction)
  
  ## Never Do
  - NEVER grep for code structure — use graph queries
  - NEVER read entire large files — use codesight wiki articles
  - NEVER ignore impact analysis warnings
  - NEVER commit without running `gitnexus_detect_changes()`
  
  ## Token Savings Estimate (This Project)
  | Tool | What It Saves | Claim (from README) |
  |------|--------------|---------------------|
  | codesight | Code exploration | 7x-91x (benchmarked on 3 projects) |
  | RTK | CLI output | 60-90% by category |
  | caveman | Agent output | ~75% (single example) |
  | LG-token-saver | Session-level | 87% claimed (self-reported) |
  ```

#### Step 7.4 — Create Distribution Entry Point
- **File:** `pyproject.toml` (new)
  ```toml
  [project]
  name = "token-saver-meta"
  version = "0.1.0"
  description = "Token Saving for the Masses — zero-config token-saving toolkit"
  requires-python = ">=3.10"
  
  [project.scripts]
  token-saver = "src.installer:main"
  
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```
- **File:** `package.json` (new, for `npx create-token-saver`)
  ```json
  {
    "name": "create-token-saver",
    "version": "0.1.0",
    "bin": { "create-token-saver": "./cli.js" }
  }
  ```
- **File:** `cli.js` (new — bridge to Python, like combo's cli.js)

#### Step 7.5 — Build Dashboard Scaffold
- **Goal:** A single HTML page showing tool status and estimated savings
- **Shows:** GitNexus status (indexed/stale), CGC stats (file count), RTK (installed/not), codesight (generated/stale), Repomix (packed/stale), watcher status
- **Pattern:** Study ClaudeCode-Token-Guard's `dashboard.html` for inspiration
- **Implementation:** Simple HTML file served by Python `http.server`; launched by `token-saver dashboard`

---

## 6. DESIGN DECISIONS — DO NOT REVISIT

These were resolved through extensive sequential thinking. Do not re-litigate unless you find genuinely new evidence.

| Decision | Rationale |
|----------|-----------|
| **RTK as primary output compressor** | 62K stars, 14 agents, transparent hooks, benchmarked by category. lean-ctx MCP optional (shell hook disabled). opentoken/omni deferred to v2. |
| **All 4 code intelligence tools (GitNexus, CGC, codesight, token-savior code index)** | Progression: overview→symbol→structure→impact. NOT competitors. |
| **All 3 behavior tools (caveman, LG-token-saver, kevin-copilot)** | Different dimensions: style, operations, structure. All zero-dependency. |
| **LLMLingua optional with GPU auto-detect** | Needs GPU. Agent auto-detects, advises user. CPU: warn and ask. |
| **orchestkit extracted as universal skills only** | 210 hooks are Claude Code-specific and not portable. Skills are portable. |
| **Default to INCLUDE, prove conflict** | Only 1 genuine conflict across 44 tools. Most "conflicts" were tools at different depths. |
| **Never publish aggregate savings without benchmark** | All claims must cite source with label (benchmarked/self-reported/unverified). |
| **Inherit combo's merge-don't-replace philosophy** | MCP configs merged into existing files. AGENTS.md sections use markers. Idempotent. |

---

## 7. KEY TECHNICAL PATTERNS TO FOLLOW

### From gitnexus_CGC_combo (MUST inherit)
1. **platforms/matrix.json** — Declarative platform registry. Add new tools as `{toolname}_server` entries.
2. **config_gen.py merge logic** — `merge_into_existing()` preserves user's MCP servers. NEVER overwrite.
3. **3 MCP format families** — `mcpServers`, `mcp`, `servers`. New tools auto-generated for all 3.
4. **AGENTS.md injection markers** — `<!-- token-saver:start -->` / `<!-- token-saver:end -->`. Idempotent.
5. **Two-path architecture** — Agent path (AGENTS.md protocol) + Manual path (`uvx token-saver-meta setup ./`).

### From Our Research (New patterns)
6. **Complexity scoring (inspired by MOS)** — Future: 0-140 engine → mode selection. v1: simple "install all core tools."
7. **GPU auto-detect for LLMLingua** — `import torch; torch.cuda.is_available()`. Auto-install if available. Warn if CPU-only.
8. **Binary download strategy** — For Rust binaries (RTK, lean-ctx): detect OS/arch → check if binary exists → download if not → verify.
9. **Skills bundling** — SKILL.md files copied to `{platform_skills_dir}/token-saver/`. Works for Kilo, Claude Code, Codex, OpenCode, etc.

---

## 8. FILE STRUCTURE TO CREATE

```
token-saver-meta/
├── src/
│   ├── config_gen.py          # Extended from combo — handles ALL tools, not just GitNexus+CGC
│   ├── installer.py           # NEW — unified 10-tool installer
│   └── dashboard.py           # NEW — simple HTTP dashboard
├── platforms/
│   └── matrix.json            # Extended with new tool entries
├── skills/                    # NEW — bundled SKILL.md files
│   ├── caveman/
│   │   └── SKILL.md           # From useful-repos/caveman/
│   ├── lg-token-saver/
│   │   └── SKILL.md           # From useful-repos/LG-token-saver/
│   ├── kevin-copilot/
│   │   └── *.md               # From useful-repos/kevin-copilot/
│   └── combo-workflow/        # Unified token-saving workflow
│       └── SKILL.md
├── templates/
│   └── agents_md_section.md   # The AGENTS.md content to inject
├── dashboard/
│   └── index.html             # Status dashboard
├── pyproject.toml             # Python package
├── package.json               # npm package (for npx)
├── cli.js                     # npm→Python bridge
├── AGENTS.md                  # Updated with architecture
├── BESTS.md                   # Tool leaderboard
├── MEMORY.md                  # Persistent state
└── progress_docs/             # Phase tracking
```

---

## 9. AGENT PROTOCOL — HOW THE AGENT PROVISIONS EVERYTHING

Inherit from combo's 8-phase protocol but extend:

| Phase | What the Agent Does |
|-------|-------------------|
| **0** | Self-identify platform (from combo) |
| **1** | Detect environment (Node, Python, uv, git) |
| **2** | Install tools: GitNexus (npx), CGC (uv), RTK (binary download), codesight (npx), Repomix (npx) |
| **3** | Generate MCP configs for ALL detected platforms with ALL tool entries |
| **4** | Copy SKILL.md files to platform skills dirs |
| **5** | Run `npx codesight` and `npx repomix` on the project |
| **6** | Index project: `npx gitnexus analyze --embeddings --skills` + `uv run cgc index .` |
| **7** | Inject AGENTS.md sections with token-saver protocol |
| **8** | Verify everything works: gitnexus status, cgc stats, RTK version, codesight file exists, etc. |
| **9** | Print dashboard summary showing what was installed and estimated savings |

---

## 10. OPEN QUESTIONS (Defer to v2)

These were identified but NOT resolved — do not try to solve them now:

| # | Question | Why Deferred |
|---|----------|-------------|
| Q1 | **tokensave vs GitNexus** — Which code intelligence engine is better? | Need side-by-side benchmark. v2. |
| Q2 | **opentoken vs omni** — Which output compression pipeline to adopt as alternative? | Both are deep-study tier. v2. |
| Q3 | **Desktop app framework** — Tauri (Rust, small) vs Electron (JS, more devs)? | Premature — CLI first. |
| Q4 | **Open source license** — MIT vs BSL? | Depends on which tools are bundled (their licenses constrain us). |
| Q5 | **Aggregate savings benchmark** — What's the real combined number? | Need to build and measure first. |
| Q6 | **flowork_Router integration** — Does its proxy model add value beyond RTK? | RTK suffices for v1. Evaluate in v2. |
| Q7 | **orchestkit skills extraction** — Which exact skills are most valuable? | Need to analyze 111 skills. 8 token-relevant ones identified; deeper study needed. |
| Q8 | **TSCG vs OnlyCLI** — Schema compression or MCP elimination? | TSCG chosen as simpler. Revisit if MCP overhead is still too high. |

---

## 11. GOTCHAS — THINGS THAT WENT WRONG BEFORE

| # | Gotcha | What Happened | Lesson |
|---|--------|---------------|--------|
| G1 | **Fabricated savings claims** | Claimed "82% total savings" by adding percentages from different token types. User called it out. | NEVER add percentages across token types. Cite source for every claim. |
| G2 | **False conflicts** | Initially labeled 6 tool pairs as "conflicts." On deeper analysis, only 1 was genuine. | Map to token types first. Same type + same mechanism = conflict. Different = complement. |
| G3 | **Skipped lean-ctx comparison** | Recommended RTK without comparing to lean-ctx. User asked "why not lean-ctx?" | Compare systematically. Sequential thinking for all pairs. |
| G4 | **Ignored aggregator repos** | Focused only on tools, missed MOS/discussions as valuable data sources. User reminded us. | Classify EVERY source: TOOL / AGGREGATOR / DISCUSSION. |
| G5 | **Assumed "txbbs" was token tool** | Name sounded like token-saver. Was WeChat automation. | Clone everything. Read README. Then classify. |

---

## 12. IMMEDIATE NEXT ACTION

**Start with Step 7.1:** Copy `gitnexus_CGC_combo/src/config_gen.py` to `src/config_gen.py`. Copy `gitnexus_CGC_combo/platforms/matrix.json` to `platforms/matrix.json`. Add new tool entries for all 10 core tools. Test that existing GitNexus+CGC config generation still works. Then add RTK, codesight, and Repomix entries.

**Verification checklist for this step:**
- [ ] `uv run python src/config_gen.py --list-platforms` — shows all platforms
- [ ] `uv run python src/config_gen.py --detect --project-path .` — detects current project's platforms
- [ ] Generated MCP configs include new tool entries for ALL 3 format families
- [ ] Existing GitNexus+CGC entries still generate correctly (regression test)
- [ ] RTK entry uses `install_strategy: "binary-download"` — no MCP config generated
- [ ] codesight entry generates valid MCP config in all 3 format families
