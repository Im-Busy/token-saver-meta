# Token Saver Meta — AGENTS.md

> "Token Saving for the Masses"  
> A meta-package that bundles token-saving tools across ALL layers of LLM token consumption.  
> **Infrastructure patterns adopted from `investment_trying`** — BESTS.md, SOURCE_MANIFEST, insight_registry, progress_docs.

---

## Purpose

Build a single installable package that gives any AI coding tool (on any platform) the full stack of token-saving capabilities — with zero configuration from the user.

---

## Session Start Protocol

Every new AI session MUST read these files in order:

1. **`MEMORY.md`** — Persistent handover state, current phase, next actions
2. **`progress_docs/current.md`** — Most recent session log
3. **`progress_docs/plans/full.md`** — Master plan, all phases, deferred items
4. **`docs/insights_and_synergies.md`** — ⭐ COMPLETE: 39 insights + 24 synergies from all 63 sources
5. **`BESTS.md`** — Tool ranking leaderboard (46 tools, 4 tiers)
6. **`docs/architecture-v2.md`** — ⭐ AUTHORITATIVE architecture (Hybrid: Base + Intelligence + Compression + Optional)
7. **`docs/rewrite-strategy.md`** — Which tools we bundle, which we rewrite, vendoring decisions

---

## Current Architecture (v2 — Hybrid)

> ⭐ **AUTHORITATIVE:** Full architecture at `docs/architecture-v2.md`. This section is a summary only.

### Base Layer (instant, zero deps — SKILL.md text, always active)
| # | Tool | Token Types | Stars | Mechanism |
|---|------|:----------:|------:|-----------|
| 1 | **caveman** | T3 | 74K | Prose terseness (~75%) |
| 2 | **ponytail** | T3 | 35K | YAGNI code minimalism (~54% LOC) |
| 3 | **LG-token-saver** | T1+T2+T3 | 23 | Operational efficiency (8 rules) |
| 4 | **kevin-copilot** | T3 | 5 | Structured terseness (4 modes) |

→ All 4 vendored as text → merged into a single 55-line AGENTS.md block. Active in <1s. Saves ~40% on T3+T7.

### Intelligence Layer (auto-install, Node.js first)
| # | Tool | Token Types | Stars | Mechanism |
|---|------|:----------:|------:|-----------|
| 5 | **CGC/codegraph** | T1 | 51K | SQLite+FTS5 graph queries (MCP, npx) |
| 6 | **codesight** | T1 | 1.1K | Context map generator (7x-91x, one-shot, npx) |
| 7 | **Repomix** | T1 | 26K | Repo packing (~70%, one-shot, npx) |

→ GitNexus (42K stars) moved to Optional — PolyForm Noncommercial license.

### Compression Layer (auto-install)
| # | Tool | Token Types | Stars | Mechanism |
|---|------|:----------:|------:|-----------|
| 8 | **RTK** | T2 | 63K | Shell compression (PreToolUse hook, binary) |
| 9 | **ContextSlimAI** | T2 | 0 | CLI wrappers + rules generation (🔴 Python rewrite) |

### Optional Modules (one-click enable)
| # | Tool | Token Types | Stars | Why Optional |
|---|------|:----------:|------:|-------------|
| 10 | **TSCG** | T6 | 18 | Schema compression 50-72% (🔴 Python rewrite) |
| 11 | **Unified T5 Memory** | T5 | — | Merge codex-agent-mem + Loom (🔴 Python rewrite) |
| 12 | **LLMLingua-2** | T4 | 6K | Prompt compression (GPU auto-detect) |
| 13 | **SkillOpt** | T7 | 8K | Skill document optimization |
| 14 | **GitNexus** | T1 | 42K | Non-commercial only (PolyForm NC license) |

---

## Architecture Decisions (DO NOT REVISIT)

- **Architecture v2 is authoritative** — `docs/architecture-v2.md`. Hybrid: Base (SKILL.md) + Intelligence (MCP) + Compression (binary/CLI) + Optional (one-click).
- **Base layer is 4 vendored SKILL.md rules** — merged into a single 55-line AGENTS.md block. Instant, zero deps, works everywhere.
- **6 micro-tools (<1K stars) require rewrite or vendoring** — ContextSlimAI, TSCG, codex-agent-mem, Loom rewritten; LG-token-saver, kevin-copilot vendored as text.
- **Only 1 genuine conflict** — RTK shell hook vs lean-ctx shell hook. RTK wins, lean-ctx gets shell hook disabled.
- **CGC uses SQLite+FTS5+SQL+BFS, NOT Neo4j+Cypher** — corrected 2026-06-18 from earlier architecture docs.
- **GitNexus uses PolyForm Noncommercial** — cannot bundle in any commercial distribution. Moved to Optional.
- **All savings claims must cite source** — benchmarked / self-reported / unverified.
- **T4/T5/T6 are optional-only in v1** — heaviest types (T1+T2) get core coverage first.

---

## Agent Protocol

### After Phase 07a: Base Layer is Always Active
The token-saving protocol is injected into this AGENTS.md below. All development agents working on this project must follow the protocol.

### When Building or Modifying Code
1. Follow YAGNI ladder (ponytail Rule 12) — stdlib first, minimal code
2. Use SubAgents for exploration across >3 files (LG-token-saver Rule 19)
3. Batch independent tool calls (LG-token-saver Rule 21)
4. Never search the same thing twice (LG-token-saver Rule 22)

### When Researching or Evaluating Tools
1. Clone everything first, filter later (Insight I36)
2. Classify as TOOL / AGGREGATOR / DISCUSSION / IRRELEVANT
3. Only exclude tools with same mechanism AND same token type
4. Always cite savings claims with source label

### When Updating Project State
1. Update `progress_docs/current.md` with session log
2. Update `MEMORY.md` if phase changes
3. Update `BESTS.md` if tool rankings change
4. Update `docs/insight_registry.md` if new actionable insights found
5. Write handovers for major phase completions

---

## Key Documents

| Document | Purpose |
|----------|---------|
| **`MEMORY.md`** | Persistent handover state, current phase |
| **`BESTS.md`** | Tool ranking leaderboard (46 tools, 4 tiers) |
| **`docs/insight_registry.md`** | 24 actionable insights from 63 sources |
| **`docs/insights_and_synergies.md`** | 39 insights + 24 synergies |
| **`docs/architecture-v2.md`** | ⭐ AUTHORITATIVE — Hybrid architecture, full design |
| **`docs/rewrite-strategy.md`** | ⭐ AUTHORITATIVE — Bundle vs rewrite vs vendor decisions |
| **`progress_docs/plans/full.md`** | Master plan (all phases) |
| **`progress_docs/current.md`** | Session log |
| **`templates/agents_md_section.md`** | The merged AGENTS.md injection block (55 lines) |

---

## Quick Reference: Token Types (T1-T7)

| Type | What It Is | Heavy Tools |
|:----:|-----------|-------------|
| T1 | Exploration (reading files) | CGC, codesight, Repomix |
| T2 | Shell output (CLI results) | RTK, ContextSlimAI |
| T3 | Agent output (what agent says) | caveman, ponytail, LG-token-saver, kevin-copilot |
| T4 | Prompt input (API requests) | LLMLingua-2 |
| T5 | Repeated knowledge (cross-session) | Unified T5 Memory |
| T6 | Tool schema (MCP definitions) | TSCG |
| T7 | Instructions (AGENTS.md, rules) | caveman, ponytail, LG-token-saver, kevin-copilot, SkillOpt |


<!-- TOKEN_SAVER_START -->
## Token Saving Protocol

> Auto-generated by Token Saver Meta. Active every response. No mode switching â€” all rules always active.
> Sources: caveman (prose style), ponytail (code minimalism), LG-token-saver (operations), kevin-copilot (structure).

### Output Style (caveman + kevin-copilot)

1. **No preamble.** Never "Sure!", "Certainly", "I'd be happy to", "Here is", "Let me".
2. **No closing filler.** Never "Hope that helps", "Let me know", "Happy coding".
3. **No hedging.** Drop "might", "perhaps", "it seems", "basically", "actually", "simply".
4. **No articles** where meaning survives. Fragments OK.
5. **Code leads when it answers the question.** Prose only if required.
6. **Never restate the question. Never explain what you're about to do â€” just do it.**
7. **No self-reference.** Never name or announce the style. No "Here's a terse response."
8. **Plain declarative sentences.** Dry, neutral tone. Senior engineer in a hurry. Not rude.
9. **Technical terms exact.** Code blocks unchanged. Errors quoted exact.
10. **No tool-call narration, no decorative tables/emoji, no dumping long raw error logs** unless asked â€” quote the shortest decisive line.
11. **Response target:** under 60 words of prose for typical questions. Code blocks don't count.

### Code Minimalism (ponytail)

12. **YAGNI ladder.** Before writing code, stop at the first rung that holds:
    1. Does this need to be built at all?
    2. Does the standard library already do this? Use it.
    3. Does a native platform feature cover it? Use it.
    4. Does an already-installed dependency solve it? Use it.
    5. Can this be one line? Make it one line.
    6. Only then: write the minimum code that works.
13. **No abstractions unrequested.** No new dependency if avoidable. No boilerplate.
14. **Deletion over addition. Boring over clever. Fewest files possible.**
15. **Question complex requests.** "Do you actually need X, or does Y cover it?"
16. **Pick the edge-case-correct option** when two stdlib approaches are the same size.
17. **Mark intentional simplifications** with a `ponytail:` comment. If the shortcut has a known ceiling (global lock, O(nÂ²) scan, naive heuristic), name the ceiling and the upgrade path.
18. **Non-trivial logic leaves ONE runnable check** â€” the smallest thing that fails if the logic breaks (assert-based demo or small test). Trivial one-liners need no test.

### Operational Efficiency (LG-token-saver)

19. **SubAgent for exploration.** When searching across >3 files, dispatch an Explore subagent. Main session receives only the summary.
20. **Grep before Read.** Before reading any file >500 lines, Grep for the target symbol first. Read only relevant lines (â‰¤30). Exception: files <500 lines with clear context need.
21. **Batch independent calls.** When 2+ tool calls have no dependency, send them in a single message. Never serialize what can be parallelized.
22. **Never search the same thing twice.** If a file or pattern was already searched, reference the result directly.
23. **Filter Bash output.** Pipe verbose commands through filters:
    - `npm install` â†’ `2>&1 | tail -20`
    - `cargo build` â†’ `2>&1 | tail -20`
    - `pytest` â†’ `2>&1 | grep -E "PASSED|FAILED|ERROR"`
    - Failure: last 50 lines. Success: last 5.
24. **Compact after large reads.** If a single Read or Bash output exceeds 500 lines or 50KB, suggest compaction immediately.
25. **Limit SubAgent output.** All subagent prompts must include: "Report findings in under 200 words. Show only file paths and key conclusions. Omit raw data."

### Safety Overrides (all sources)

26. **Correctness always wins.** Never trade accuracy for brevity.
27. **Preserve full clarity for:** security warnings, irreversible actions, multi-step sequences where fragments risk misread, anything explicitly requested with detail.
28. **Always verbatim:** file paths, exact commands, exact error messages, code symbols, API names, commit-type keywords (feat/fix/docs/test/chore), input validation at trust boundaries, error handling that prevents data loss.
<!-- TOKEN_SAVER_END -->

