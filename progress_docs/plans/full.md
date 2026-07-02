---
project: Token Saver Meta
last_updated: 2026-06-13
phases_total: 10
phases_complete: 8
enhancement_tracks:
  - research
  - architecture
  - implementation
  - distribution
---

# Full Implementation Plan

## Phase Status

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 01 | Research & Discovery (Batch 1 — 25 sources) | ✅ Complete | 18 repos cloned, 3 discussions, initial brainstorm |
| 02 | Deep Evaluation (Batch 1 — 18 repos) | ✅ Complete | 6 parallel agents, per-repo analysis |
| 03 | Conflict Resolution & Architecture | ✅ Complete | Sequential thinking, max coexistence set |
| 04 | Research & Discovery (Batch 2 — 36 sources) | ✅ Complete | 28 repos, 8 discussions, tier-1 finds |
| 05 | Insight Extraction & Synthesis | ✅ Complete | Insight registry (22), BESTS leaderboard (44) |
| 06 | Project Scaffolding & Infrastructure | ✅ Complete | AGENTS.md rewrite, progress_docs, docs/ |
| 07 | Core Bundle Implementation | ✅ Complete | 10 core tools installer |
| 08 | Optional Module Integration | ✅ Complete | 8 optional one-click modules |
| 09 | Distribution & Packaging | 🔄 In Progress | npx + uvx + PyPI |
| 10 | Testing & Verification | ⏳ Pending | Benchmark suite, integration tests |

---

## Phase 01-05: Research ✅ COMPLETE

> 61 sources studied across 2 batches. 44 repos cloned. Architecture established. All conflicts resolved.

### Key Outputs

| Output | Location |
|--------|----------|
| Source Inventory (61 sources) | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-source-inventory.md` |
| Evaluation Notes | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-evaluation-notes.md` |
| Conflict Resolution | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-conflict-resolution.md` |
| Maximum Coexistence Set | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-max-coexistence.md` |
| Savings Audit | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-savings-audit.md` |
| Insight Registry (22 insights) | `docs/insight_registry.md` |
| Tool Leaderboard (44 tools) | `BESTS.md` |
| Brainstorm (14 idea blocks) | `C:\Dev\ideas\project-ideas_structured\token-saver-meta.md` |

### Key Decisions

- **Core bundle:** 10 tools (GitNexus, CGC, RTK, codesight, Repomix, caveman, LG-token-saver, ContextSlimAI, kevin-copilot, installer)
- **Optional modules:** 8 tools (TSCG, lean-ctx, LLMLingua, codex-agent-mem, Loom, Deblank, toon, orchestkit-extracted)
- **Deep study queue:** 8 tools (tokensave, opentoken, omni, trace-mcp, jcodemunch, sdl-mcp, racs, code-context-engine)
- **Only 1 genuine conflict** across all 44 tools (RTK shell hook vs lean-ctx shell hook — resolved)

---

## Phase 06: Project Scaffolding ✅ COMPLETE

> Set up infrastructure adopting patterns from investment_trying.

### Adopted Infrastructure

| Pattern | Source | Implemented As |
|---------|--------|---------------|
| Tool leaderboard | investment_trying/BESTS.md | `BESTS.md` (44 tools, 4 tiers) |
| Insight registry | investment_trying docs/ | `docs/insight_registry.md` (22 insights) |
| Progress documentation | investment_trying/progress_docs/ | `progress_docs/` (README, current.md, plans/full.md) |
| Source manifest | investment_trying/SOURCE_MANIFEST.md | `C:\Dev\ideas\...\token-saver-meta-source-inventory.md` |
| Plan type system | investment_trying progress_docs | phase, study, eval, setup, enhancement |
| AGENTS.md protocol | investment_trying/AGENTS.md | Full rewrite with insight finding process |

---

## Phase 07: Core Bundle Implementation ✅ Complete

> Completed 2026-06-19: AGENTS.md injection block merged, installer pipeline operational, CGC + codesight + RTK + ContextSlim AI installers functional.

### Tasks

| Priority | Task | Description |
|----------|------|-------------|
| P0 | Create installer scaffold | Python-based unified installer (inherit from gitnexus_CGC_combo) |
| P0 | Platform detection | Filesystem marker scanning (from combo's config_gen.py) |
| P0 | MCP config generation | Multi-format JSON generation (from combo's matrix.json) |
| P0 | GitNexus + CGC integration | Copy existing combo setup logic |
| P0 | RTK integration | Auto-detect + `rtk init -g` hooks |
| P0 | codesight integration | Auto-run `npx codesight` on project |
| P0 | SKILL.md bundling | Bundle caveman + LG-token-saver + kevin-copilot skills |
| P0 | AGENTS.md injection | Token-saving protocol injection (from combo's Phase 6) |
| P1 | ContextSlimAI integration | Run `contextslim init` for rules generation |
| P1 | Repomix integration | Auto-run `npx repomix` on first setup |
| P1 | Dashboard scaffold | Status page showing tool health and savings |

---

## Phase 08: Optional Module Integration ✅ Complete

> Completed 2026-06-19: TSCG Python rewrite, Unified T5 Memory (332 tests), ContextSlimAI rewrite (473 tests).

| Priority | Task | Description |
|----------|------|-------------|
| P1 | TSCG MCP proxy | Drop-in `@tscg/mcp-proxy` for schema compression |
| P1 | lean-ctx integration | MCP config + AGENTS.md rules (shell hook disabled) |
| P1 | LLMLingua GPU detection | Auto-detect GPU, advise user, optional install |
| P2 | codex-agent-mem integration | MCP config for continuity packs |
| P2 | Loom integration | MCP config for persistent symbol index |
| P2 | Deblank integration | REST API wrapper for whitespace stripping |
| P2 | toon integration | Serialization transform module |
| P2 | orchestkit skills extraction | Package universal skills as platform-agnostic SKILL.md files |

---

## Phase 09: Distribution & Packaging 🔄 In Progress

> npm v0.1.1 published, PyPI v0.1.0 published, dual-remote configured. Phase 09 task list still in progress.

| Priority | Task | Description |
|----------|------|-------------|
| P0 | `npx token-saver-meta` | npm starter |
| P0 | `uvx token-saver-meta setup` | Python distribution (follow combo's uvx pattern) |
| P1 | PyPI package | `pip install token-saver-meta` |
| P1 | GitHub repo | Public with README, docs, getting started guide |
| P2 | VS Code extension | Status bar + one-click setup |
| P2 | Desktop app (Tauri) | GUI installer for non-technical users |

---

## Phase 10: Testing & Verification ⏳ PENDING

| Priority | Task | Description |
|----------|------|-------------|
| P0 | Standard benchmark task | Define "add a CRUD endpoint" benchmark for savings measurement |
| P0 | Baseline measurement | Measure token usage without any tools |
| P0 | Individual tool measurement | Measure each core tool's savings on benchmark |
| P0 | Combined measurement | Measure full stack savings on benchmark |
| P1 | Cross-platform testing | Test on Windows, macOS, Linux |
| P1 | Cross-agent testing | Test with Claude Code, Cursor, OpenCode, Copilot |
| P2 | Long-session testing | Multi-hour sessions with compaction events |

---

## Deferred Items

| Item | Reason | Revisit When |
|------|--------|-------------|
| Deep study of 8 tier-3 tools | Core architecture must be stable first | After Phase 07 |
| flowork_Router integration | AI gateway is complex, RTK suffices for now | v2 |
| CometCLI bundling | GPL-3.0 copyleft concern | If demand emerges |
| supamem integration | Requires Qdrant Docker — too heavy for v1 | v2 |
| AgentGuard bundling | Mac-first, Windows "coming soon" | When Windows support lands |
| Desktop app (Tauri) | Highest effort distribution channel | After core is stable |

---

## Immediate Next Actions

**Phase 07 — Core Bundle Implementation:**
1. Study `gitnexus_CGC_combo/src/config_gen.py` + `platforms/matrix.json` as foundation
2. Extend matrix.json with new tool entries (RTK, codesight, Repomix, ContextSlimAI)
3. Build unified installer that auto-detects and sets up all 10 core tools
4. Write AGENTS.md injection with full token-saving protocol
5. Create `npx token-saver-meta` entry point
