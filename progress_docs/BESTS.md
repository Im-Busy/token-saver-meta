# Token Saver Meta — Tool Leaderboard

> Pattern adopted from `investment_trying/BESTS.md`.  
> Ranks all 49 repos by token-saving effectiveness. Updated 2026-07-02.

---

## Ranking Methodology

Each tool scored on 3 axes (1-10 each):

| Axis | What It Measures |
|------|-----------------|
| **Savings** | Claimed token reduction (from READMEs) × verified benchmarks |
| **Coverage** | Token types covered (T1-T7) × agent platforms supported |
| **Maturity** | Stars, version, tests, CI, license clarity |

**Final Score = Savings × 0.5 + Coverage × 0.3 + Maturity × 0.2**

---

## Tier S — Production-Ready, Maximum Impact

| # | Tool | Savings | Coverage | Maturity | Score | License |
|---|------|:-------:|:--------:|:--------:|:-----:|---------|
| 1 | **codebase-memory-mcp (CBM)** | 9 | 9 | 10 | **9.2** | MIT |
| 2 | **RTK** | 9 | 8 | 10 | **8.9** | Apache 2.0 |
| 3 | **TSCG** | 10 | 7 | 7 | **8.5** | MIT |
| 4 | **tokensave** | 9 | 9 | 8 | **8.7** | MIT |
| 5 | **codesight** | 10 | 6 | 8 | **8.4** | MIT |
| 6 | **trace-mcp** | 7 | 10 | 7 | **7.9** | MIT |

---

## Tier A — High Impact, Some Caveats

| # | Tool | Savings | Coverage | Maturity | Score | Caveat |
|---|------|:-------:|:--------:|:--------:|:-----:|--------|
| 7 | **jcodemunch-mcp** | 9 | 7 | 6 | **7.8** | Commercial license for teams |
| 8 | **opentoken** | 8 | 7 | 7 | **7.5** | RTK competitor, evaluate overlap |
| 9 | **Loom** | 9 | 6 | 7 | **7.7** | Cross-session compound effect |
| 10 | **code-context-engine** | 9 | 6 | 7 | **7.7** | Best-benchmarked retrieval |
| 11 | **omni** | 8 | 6 | 7 | **7.2** | opentoken competitor |
| 12 | **sdl-mcp** | 8 | 6 | 6 | **7.0** | Source-available license |
| 13 | **codex-agent-mem** | 9 | 5 | 7 | **7.4** | Continuity packs, zero infra |
| 14 | **LLMLingua** | 10 | 3 | 6 | **7.1** | GPU required |

---

## Tier B — Solid, Narrower Scope

| # | Tool | Savings | Coverage | Maturity | Score | Notes |
|---|------|:-------:|:--------:|:--------:|:-----:|-------|
| 15 | **caveman** | 7 | 5 | 6 | **6.2** | SKILL.md only, zero deps |
| 16 | **LG-token-saver** | 8 | 5 | 4 | **6.3** | Self-reported savings |
| 17 | **kevin-copilot** | 7 | 4 | 7 | **6.1** | CI-gated evals |
| 18 | **racs** | 7 | 4 | 8 | **6.3** | Cache optimization only |
| 19 | **ContextSlimAI** | 7 | 5 | 5 | **5.9** | CLI wrappers + rules gen |
| 20 | **lowfat** | 6 | 5 | 6 | **5.7** | Complements RTK |
| 21 | **Deblank** | 5 | 4 | 8 | **5.3** | Academic validation [deferred to v2] |
| 22 | **toon** | 4 | 6 | 5 | **4.8** | Data format only [deferred to v2] |
| 23 | **ponytail** | 7 | 5 | 6 | **6.2** | YAGNI ladder, ~22% tokens, ~54% LOC |
| 24 | **SkillOpt** | 6 | 4 | 7 | **5.6** | Skill optimization, 300-2K tok artifacts |

---

## Tier C — Reference / Pattern Value

| # | Tool | Why Not Higher |
|---|------|---------------|
| 25 | **MOS** | Aggregator — value is the architecture pattern, not the code |
| 26 | **orchestkit** | Claude Code-specific hooks. Skills extracted as universal. |
| 27 | **MemOS** | Heavy infra (Neo4j + Qdrant). Pattern value only. |
| 28 | **supamem** | Needs Qdrant Docker. Defer to v2. |
| 29 | **flowork_Router** | AI gateway — compressor is one feature. Defer. |
| 30 | **CometCLI** | GPL-3.0 copyleft. Separate install only. |
| 31 | **savethetokens** | Session hygiene scripts. Requires agent discipline. |
| 32 | **ClaudeCode-Token-Guard** | Monitoring dashboard. Doesn't save tokens itself. |
| 33 | **houtini-lm** | Task delegation. Complementary but not core. |
| 34 | **save-my-tokens** | Free API delegation. Simple. |
| 35 | **froggy-aura** | Project memory. Cursor-focused. |
| 36 | **AgentGuard** | Mac-first Tauri app. Windows support "coming soon." |
| 37 | **architect-loop** | Orchestration pattern (spec-before-build, fresh contexts). Indirect token-efficiency patterns. |

---

## Tier D — Excluded

| # | Tool | Reason |
|---|------|--------|
| 38 | **prompt-optimizer** | Too heavy (torch 2GB) |
| 39 | **TokenSage-CLI** | Alpha quality, no benchmarks |
| 40 | **AI-Sanctuary-Protocol** | Security risk |
| 41 | **Contextual-Compression** | Research, not a tool |
| 42 | **txbbs** | WeChat automation, not AI tokens |
| 43 | **git-courer** | Git tool, no token saving |
| 44 | **save-the-tokens** | Config infra, not token saver |
| 45 | **memorybridge** | Too experimental (v0.1.0) |
| 46 | **boost** | Proprietary (JFrog) |
| 47 | **OnlyCLI** | Defer (niche: API-only MCP replacement) |
| 48 | **token-saver-sirugao** | Too lightweight (single SKILL.md) |

---

## Historical — Replaced or Decommissioned

| # | Tool | Replacement | Details |
|---|------|-------------|---------|
| 49 | **GitNexus** | CBM (codebase-memory-mcp) | GitNexus replaced by CBM v0.8.1 (codebase-memory-mcp). MIT license, 24k stars, pure C, 158 languages. Formerly Tier A — graph-based code intelligence with impact analysis.
