# Token Saver Meta — Tool Leaderboard

> Pattern adopted from `investment_trying/BESTS.md`.  
> Ranks all 46 repos by token-saving effectiveness. Updated 2026-06-18.

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
| 1 | **RTK** | 9 | 8 | 10 | **8.9** | Apache 2.0 |
| 2 | **TSCG** | 10 | 7 | 7 | **8.5** | MIT |
| 3 | **tokensave** | 9 | 9 | 8 | **8.7** | MIT |
| 4 | **codesight** | 10 | 6 | 8 | **8.4** | MIT |
| 5 | **trace-mcp** | 7 | 10 | 7 | **7.9** | MIT |

---

## Tier A — High Impact, Some Caveats

| # | Tool | Savings | Coverage | Maturity | Score | Caveat |
|---|------|:-------:|:--------:|:--------:|:-----:|--------|
| 6 | **jcodemunch-mcp** | 9 | 7 | 6 | **7.8** | Commercial license for teams |
| 7 | **opentoken** | 8 | 7 | 7 | **7.5** | RTK competitor, evaluate overlap |
| 8 | **Loom** | 9 | 6 | 7 | **7.7** | Cross-session compound effect |
| 9 | **code-context-engine** | 9 | 6 | 7 | **7.7** | Best-benchmarked retrieval |
| 10 | **omni** | 8 | 6 | 7 | **7.2** | opentoken competitor |
| 11 | **sdl-mcp** | 8 | 6 | 6 | **7.0** | Source-available license |
| 12 | **codex-agent-mem** | 9 | 5 | 7 | **7.4** | Continuity packs, zero infra |
| 13 | **LLMLingua** | 10 | 3 | 6 | **7.1** | GPU required |

---

## Tier B — Solid, Narrower Scope

| # | Tool | Savings | Coverage | Maturity | Score | Notes |
|---|------|:-------:|:--------:|:--------:|:-----:|-------|
| 14 | **caveman** | 7 | 5 | 6 | **6.2** | SKILL.md only, zero deps |
| 15 | **LG-token-saver** | 8 | 5 | 4 | **6.3** | Self-reported savings |
| 16 | **kevin-copilot** | 7 | 4 | 7 | **6.1** | CI-gated evals |
| 17 | **racs** | 7 | 4 | 8 | **6.3** | Cache optimization only |
| 18 | **ContextSlimAI** | 7 | 5 | 5 | **5.9** | CLI wrappers + rules gen |
| 19 | **lowfat** | 6 | 5 | 6 | **5.7** | Complements RTK |
| 20 | **Deblank** | 5 | 4 | 8 | **5.3** | Academic validation [deferred to v2] |
| 21 | **toon** | 4 | 6 | 5 | **4.8** | Data format only [deferred to v2] |
| 22 | **ponytail** | 7 | 5 | 6 | **6.2** | YAGNI ladder, ~22% tokens, ~54% LOC |
| 23 | **SkillOpt** | 6 | 4 | 7 | **5.6** | Skill optimization, 300-2K tok artifacts |

---

## Tier C — Reference / Pattern Value

| # | Tool | Why Not Higher |
|---|------|---------------|
| 24 | **MOS** | Aggregator — value is the architecture pattern, not the code |
| 25 | **orchestkit** | Claude Code-specific hooks. Skills extracted as universal. |
| 26 | **MemOS** | Heavy infra (Neo4j + Qdrant). Pattern value only. |
| 27 | **supamem** | Needs Qdrant Docker. Defer to v2. |
| 28 | **flowork_Router** | AI gateway — compressor is one feature. Defer. |
| 29 | **CometCLI** | GPL-3.0 copyleft. Separate install only. |
| 30 | **savethetokens** | Session hygiene scripts. Requires agent discipline. |
| 31 | **ClaudeCode-Token-Guard** | Monitoring dashboard. Doesn't save tokens itself. |
| 32 | **houtini-lm** | Task delegation. Complementary but not core. |
| 33 | **save-my-tokens** | Free API delegation. Simple. |
| 34 | **froggy-aura** | Project memory. Cursor-focused. |
| 35 | **AgentGuard** | Mac-first Tauri app. Windows support "coming soon." |
| 36 | **architect-loop** | Orchestration pattern (spec-before-build, fresh contexts). Indirect token-efficiency patterns. |

---

## Tier D — Excluded

| # | Tool | Reason |
|---|------|--------|
| 37 | **prompt-optimizer** | Too heavy (torch 2GB) |
| 38 | **TokenSage-CLI** | Alpha quality, no benchmarks |
| 39 | **AI-Sanctuary-Protocol** | Security risk |
| 40 | **Contextual-Compression** | Research, not a tool |
| 41 | **txbbs** | WeChat automation, not AI tokens |
| 42 | **git-courer** | Git tool, no token saving |
| 43 | **save-the-tokens** | Config infra, not token saver |
| 44 | **memorybridge** | Too experimental (v0.1.0) |
| 45 | **boost** | Proprietary (JFrog) |
| 46 | **OnlyCLI** | Defer (niche: API-only MCP replacement) |
| 47 | **token-saver-sirugao** | Too lightweight (single SKILL.md) |
