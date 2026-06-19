# MEMORY.md — Persistent Handover State

> **Last Updated:** 2026-06-19 (Phase 08 stress testing complete)
> **Current Phase:** 07 — Core Bundle Implementation (✅ COMPLETE) | 08 — Optional Module Integration (✅ COMPLETE + STRESS TESTED)

---

## Project State

**Phases Complete:** 01-06 (Research, Evaluation, Architecture, Scaffolding)
**Phases Remaining:** 09-10 (Distribution, Testing)
**Phases Complete:** 01-08

### Phase 08 Results (2026-06-19)
- **TSCG Python rewrite (tscg-py/)**: 348 tests passing. 8 transforms ported verbatim from TypeScript. 3 safety guards (non-Claude CFL/SAD off, ≥30 tools CFL/CFO off, thinking model exclusion). Best profile: balanced at 21.6% savings on 34 real MCP tools. MCP proxy + Click CLI.
- **Unified T5 Memory (token-saver-mem/)**: 332 tests passing. Code memory (indexer/delta/staleness/auto_summary) + session memory (extractor/state/caching/closure/continuity/bootstrap). Zero C dependencies (ast stdlib replaces tree-sitter). Unified MCP server with 8 tools, read-only by default.
- **2 bugs found + fixed** during stress testing: decompress_tools param parsing + store_understanding MCP wiring
- **10 high-pressure stress tests**: both projects pass at scale (100 tools / 100 files, 20-cycle delta cycling, 5-thread concurrent indexing, full lifecycle marathon)

### What We Have

- **63 sources** studied across 3 batches (46 repos cloned to `useful-repos/`)
- **46 tools** ranked in `BESTS.md` (4 tiers) — +2 from Batch 3 (ponytail, SkillOpt)
- **39 insights + 24 synergies** in `docs/insights_and_synergies.md` — +2 each from Batch 3
- **24 actionable insights** in `docs/insight_registry.md` — +2 from Batch 3
- **Architecture settled:** 10 core tools + 8 optional + 8 deep study (v2)
- **Only 1 genuine conflict** across all tools (RTK shell hook vs lean-ctx — resolved)
- **All savings claims** fact-checked against READMEs
- **Infrastructure adopted** from investment_trying: BESTS.md, progress_docs/, insight_registry

### Batch 3 Findings (2026-06-18)
- **ponytail** — YAGNI-ladder code compression. ~22% tokens, ~54% LOC, 13 platforms. Tier B (score 6.2). Complementary to caveman for T3. Candidate for Core or Optional.
- **SkillOpt** — Microsoft: trainable skill documents → compact artifacts (300-2K tokens). Tier B (score 5.6). Unique T7 coverage. Candidate for Optional.
- **architect-loop** — Orchestration patterns (spec-before-build, fresh contexts). Tier C. Indirect value.

## Architecture (v2 — 2026-06-18, Updated with Rewrite Strategy)

### CORE LAYER (instant, zero deps — SKILL.md text)
  caveman (T3) | ponytail (T3) | LG-token-saver (T1+T2+T3) | kevin-copilot (T3)
  → All 4 vendored as text → merged into single <300-line AGENTS.md block

### INTELLIGENCE LAYER (auto-install, Node.js)
  CGC/codegraph (T1, npx, SQLite+FTS5) | codesight (T1, npx) | Repomix (T1, npx)
  → GitNexus moved to Optional (PolyForm NC license)

### COMPRESSION LAYER (auto-install)
  RTK (T2, binary) | ContextSlimAI (T2, ✅ Python rewrite complete — contextslim-py/)

### OPTIONAL MODULES (one-click enable)
  TSCG (T6, 🔴 Python rewrite pending) | Unified T5 Memory (🔴 merge pending)
  LLMLingua-2 (T4) | SkillOpt (T7) | GitNexus (T1, non-commercial only)

---

## Next Session Agent Must

1. **Read** `MEMORY.md` → `AGENTS.md` → `docs/architecture-v2.md` → `docs/rewrite-strategy.md`
2. **Phase 07 is COMPLETE.** Base layer (AGENTS.md merge), Core installer (7-phase pipeline), ContextSlimAI rewrite (35 commands, 473 tests).
3. **Phase 08 is COMPLETE.** TSCG Python rewrite (348 tests, 8 transforms, MCP proxy) + Unified T5 Memory (332 tests, 8 MCP tools, zero C deps). 10 stress tests pass.
4. **Test suite:** `uv run pytest tests/` must pass (currently **680 tests** across both projects: 348 tscg-py + 332 token-saver-mem)
5. **Stress tests:** `uv run python stress_high_pressure.py` in both projects (10/10 pass)
6. **Encoding rule:** ALL file I/O MUST use `encoding="utf-8"`
7. **NEXT: Phase 09** — Distribution & Packaging (npm publish, PyPI publish, GitHub repo)

---

## Key Design Decisions (DO NOT REVISIT)

- **Architecture v2 is authoritative** — `docs/architecture-v2.md`. Hybrid: Base (SKILL.md) + Intelligence (MCP) + Compression (binary/CLI) + Optional (one-click).
- **Base layer is 4 merged SKILL.md tools** — caveman (prose) + ponytail (code minimalism) + LG-token-saver (operations) + kevin-copilot (structure). Instant, zero deps, works everywhere.
- **Only 1 genuine conflict** — RTK shell hook vs lean-ctx shell hook. RTK wins, lean-ctx gets shell hook disabled.
- **All savings claims must cite source** — benchmarked / self-reported / unverified.
- **T4/T5/T6 are optional-only in v1** — heaviest types (T1+T2) get core coverage first.
- **Deferred to v2**: jcodemunch-mcp (license), sdl-mcp (license), opentoken/omni/tokensave (evaluate), Deblank/racs/toon (wrappers needed).
