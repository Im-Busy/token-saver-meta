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

1. **`C:\Dev\.opencode\standards\mcp-policy.md`** — System-wide MCP management policy
2. **`MEMORY.md`** — Persistent handover state, current phase, next actions
3. **`progress_docs/current.md`** — Most recent session log
4. **`progress_docs/plans/full.md`** — Master plan, all phases, deferred items
5. **`docs/insights_and_synergies.md`** — ⭐ COMPLETE: 39 insights + 24 synergies from all 63 sources
6. **`BESTS.md`** — Tool ranking leaderboard (46 tools, 4 tiers)
7. **`docs/architecture-v2.md`** — ⭐ AUTHORITATIVE architecture (Hybrid: Base + Intelligence + Compression + Optional)
8. **`docs/rewrite-strategy.md`** — Which tools we bundle, which we rewrite, vendoring decisions

---

## Current Architecture (v2 — Hybrid)

> ⭐ **AUTHORITATIVE:** Full architecture at `docs/architecture-v2.md`. This section is a summary only.

### Agent Behavior Layer (instant, zero deps — SKILL.md text, always active)
| Dimension | Mechanism |
|-----------|-----------|
| **Prose terseness** | Concise language, no filler, no hedging |
| **Code minimalism** | YAGNI ladder: stdlib → native → dep → one-liner → minimal |
| **Operational efficiency** | Parallel execution, grep-first, batch calls, no repeats |
| **Structured output** | Consistent formatting, technical terms exact |

→ 4 vendored SKILL.md rules merged into a single AGENTS.md block. Active in <1s. Saves ~40% on agent output and instructions.

### Intelligence Layer (auto-install)
| Capability | Mechanism |
|-----------|-----------|
| **Code graph queries** | SQLite+FTS5 semantic search |
| **Context mapping** | Pre-built project structure maps (7x-91x compression) |
| **Repo packing** | Full repo → single file (~70% compression) |

→ Auto-installed via package manager. One-shot or on-demand.

### Compression Layer (auto-install)
| Capability | Mechanism |
|-----------|-----------|
| **Shell output filtering** | Pre-execution hook rewrites commands |
| **CLI optimization** | Slim command replacements + rule generation |

→ Auto-installed. Transparent to the user.

### Optional Modules (one-click enable)
| Capability | Why Optional |
|-----------|-------------|
| **Schema compression** | 50-72% on MCP tool definitions |
| **Cross-session memory** | Indexed code + session continuity |
| **Prompt optimization** | ML-based token removal (GPU auto-detect) |
| **Skill tuning** | Document optimization |


---

## Architecture Decisions (DO NOT REVISIT)

- **Architecture v2 is authoritative** — `docs/architecture-v2.md`. Hybrid: Base (SKILL.md) + Intelligence (MCP) + Compression (binary/CLI) + Optional (one-click).
- **Base layer is 4 vendored SKILL.md rules** — merged into a single 55-line AGENTS.md block. Instant, zero deps, works everywhere.
- **Only 1 genuine conflict** — RTK shell hook vs lean-ctx shell hook. RTK wins, lean-ctx gets shell hook disabled.
- **All savings claims must cite source** — benchmarked / self-reported / unverified.
- **T4/T5/T6 are optional-only in v1** — heaviest types (T1+T2) get core coverage first.

---

## Agent Protocol

### After Phase 07a: Base Layer is Always Active
The token-saving protocol is injected into this AGENTS.md below. All development agents working on this project must follow the protocol.

### When Building or Modifying Code
1. Follow YAGNI ladder (code minimalism) — stdlib first, minimal code
2. Use SubAgents for exploration across >3 files (operational efficiency)
3. Batch independent tool calls
4. Never search the same thing twice

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

## Repository Architecture — Dual-Repo (Private → Public)

This project uses a **dual-remote** Git architecture to publish a curated subset to a public mirror while keeping internal files private.

| Remote | Branch | Purpose |
|--------|--------|---------|
| `private` | `master` | All files, full history |
| `public` | `public` | Curated files only |

### What Goes Public

Source code (`src/`, `cli.js`), tests (`tests/`), documentation (`docs/`, `AGENTS.md`, `BESTS.md`, `README.md`), configs (`package.json`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.gitattributes`), assets (`templates/`, `skills/`, `platforms/`, `dashboard/`), license (`LICENSE`), and all sub-projects (`tscg-py/`, `token-saver-mem/`, `contextslim-py/`).

### What Stays Private

`MEMORY.md`, `kilo.json`, `opencode.jsonc`, `token-saver-meta.md`, `.kilo/`, `.omo/`, `.codegraph/`, `progress_docs/`

### Sync Commands

| Command | Usage |
|---------|-------|
| `/repo-sync` | Full sync: merge master → public → safety check → push |
| `/repo-sync check` | Safety check only — verify no private files on public branch |
| `/repo-sync status` | Show current branch state and remote config |

---

## Quick Reference: Token Types (T1-T7)

| Type | What It Is | Heavy Tools |
|:----:|-----------|-------------|
| T1 | Exploration (reading files) | Code graph, context maps, repo packing |
| T2 | Shell output (CLI results) | Shell filtering, CLI optimization |
| T3 | Agent output (what agent says) | Prose terseness, code minimalism, operational efficiency, structured output |
| T4 | Prompt input (API requests) | Prompt optimization |
| T6 | Tool schema (MCP definitions) | Schema compression |
| T7 | Instructions (AGENTS.md, rules) | Prose terseness, code minimalism, operational efficiency, structured output, skill tuning |


<!-- TOKEN_SAVER_START -->
## Token Saving Protocol

> Auto-generated by Token Saver Meta. Active every response. No mode switching â€” all rules always active.
> 28 rules across four dimensions: prose style, code minimalism, operational efficiency, and structured output.

### Output Style

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

### Code Minimalism

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

### Operational Efficiency

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

<!-- cbm:start -->
## CBM — Codebase Memory

CBM integration pending — see `templates/cbm_agents_md_block.md`.

Generated skill references preserved below for platform compatibility:
<!-- cbm:end -->

<!-- cbm-leanctx:start -->
## Code Intelligence + Context Persistence

CBM integration with lean-ctx is deferred. CBM handles codebase memory natively;
lean-ctx cross-session persistence will be re-evaluated after CBM bootstrap.
<!-- cbm-leanctx:end -->
