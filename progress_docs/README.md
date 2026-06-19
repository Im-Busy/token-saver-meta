# Progress Documentation

**Project:** Token Saver Meta — "Token Saving for the Masses"
**Last Updated:** 2026-06-14

---

## Quick Start for Agents

1. **Read `current.md`** — know what was happening when the last session ended
2. **Read `handovers/`** — latest handover file for session continuity
3. **Read `plans/full.md`** — see all phases, evaluations, and deferred items
4. **Read `../docs/insight_registry.md`** — 22 actionable insights from 61 sources
5. **Resume** from the first incomplete action

---

## Phase Map

| # | Phase | Plan | Status |
|---|-------|------|--------|
| 01 | Research & Discovery (Batch 1 — 25 sources) | [plan](plans/01-discovery-batch1.md) | ✅ Complete |
| 02 | Deep Evaluation (Batch 1 — 18 repos) | [plan](plans/02-evaluation-batch1.md) | ✅ Complete |
| 03 | Conflict Resolution & Architecture | [plan](plans/03-architecture.md) | ✅ Complete |
| 04 | Research & Discovery (Batch 2 — 36 sources) | [plan](plans/04-discovery-batch2.md) | ✅ Complete |
| 05 | Insight Extraction & Synthesis | [plan](plans/05-synthesis.md) | ✅ Complete |
| 06 | Project Scaffolding & Infrastructure | [plan](plans/06-scaffold.md) | ✅ Complete |
| 07 | Core Bundle Implementation | [plan](plans/07-core-bundle.md) | ⏳ Pending |
| 08 | Optional Module Integration | [plan](plans/08-optional-modules.md) | ⏳ Pending |
| 09 | Distribution & Packaging | [plan](plans/09-distribution.md) | ⏳ Pending |
| 10 | Testing & Verification | [plan](plans/10-testing.md) | ⏳ Pending |

## Evaluations

| Name | Plan | Status | Decision |
|------|------|--------|----------|
| RTK vs lean-ctx vs opentoken vs omni | — | ✅ Done | RTK primary; lean-ctx MCP optional; opentoken/omni deep study |
| token-savior vs GitNexus | — | ✅ Done | Complementary (different depths) |
| LG-token-saver vs caveman vs kevin-copilot | — | ✅ Done | All three (different dimensions) |
| codesight vs code-context-engine vs Loom | — | ✅ Done | All complementary (static map vs retrieval vs cache) |

---

## Known Plan Types

| Type | Prefix | When To Use |
|------|--------|-------------|
| `phase` | `NN-` | Multi-step implementation with deliverables and checkpoints |
| `study` | `study-` | Reading papers, studying repos, knowledge acquisition |
| `eval` | `eval-` | Comparing tools/approaches, making a go/no-go choice |
| `setup` | `setup-` | Environment, tooling, infrastructure changes |
| `enhancement` | `enhance-` | Cross-cutting capability improvements |
| `migration` | `migration-` | One-off system/data migrations (e.g., pip→uv, Python 3.11→3.12) |

**Agent Self-Extension:** When encountering a new activity type not in the catalog above:
1. Determine a short `type` name (lowercase, no spaces)
2. Create the plan file with `{type}-{descriptor}.md` naming
3. Add the new type to this catalog table
4. Add a new section in `plans/full.md` for the type

---

## File Conventions

| Convention | Rule |
|------------|------|
| **Folder** | `progress_docs/` — single entry point for all progress tracking |
| **Naming** | Phases: `NN-short-name.md`. Non-phases: `{type}-{descriptor}.md`. All kebab-case. |
| **Plan format** | Markdown + YAML frontmatter for metadata + Markdown tables for tasks |
| **Log format** | Markdown tables — append-only, chronological |
| **Session recovery** | `current.md` + `handovers/` — read first |
| **Completion marker** | `status: complete` — never rename files |
| **Deferral marker** | YAML `status: deferred` + `deferred_reason` + `revisit_when` |
| **Aggregation** | `plans/full.md` has all phases, deferred items, and pending work |

## Related Files

- `../AGENTS.md` — project-wide agent instructions (AUTHORITATIVE)
- `../BESTS.md` — tool ranking leaderboard (44 tools)
- `../SOURCE_MANIFEST.md` — external source catalogue (via C:\Dev\ideas\...)
- `../docs/insight_registry.md` — 22 actionable insights from 61 sources
- `../useful-repos/` — 44 cloned reference repos
