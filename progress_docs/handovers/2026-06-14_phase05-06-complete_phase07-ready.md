# Handover: Research Complete → Implementation Ready (2026-06-14)

## Session Summary

Two things completed this session:

1. **37 Insights + 22 Synergies extracted** from all 61 sources → written to `docs/insights_and_synergies.md`. This is the authoritative reference for ALL findings across 9 layers (Architecture, Output Compression, Agent Behavior, Prompt Compression, Memory, Data Format, Monitoring, Meta-Layer, Research Methodology). The Master Synergy (S22) ties Insight Registry + BESTS Leaderboard + Synergy Map into a complete decision support system.

2. **Progress system audit** — compared token-saver-meta's `progress_docs/` against investment_trying's mature system. Identified 3 critical gaps: no per-phase plan files, no per-phase log files, empty handovers directory. This handover is the first to fill that gap.

### Verified Working

- Phases 01-06: All COMPLETE (see `progress_docs/current.md` for the 7-entry log)
- Architecture: 10 core tools + 8 optional + 8 deep study = 26 tools mapped
- Only 1 genuine conflict across all 44 tools (RTK shell hook vs lean-ctx shell hook)
- All savings claims fact-checked against READMEs (see savings audit)
- BESTS.md: 44 tools ranked across 4 tiers

### Key Outputs (research phase)

| Output | Location |
|--------|----------|
| Source Inventory (61 sources) | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-source-inventory.md` |
| Maximum Coexistence Set | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-max-coexistence.md` |
| Savings Audit | `C:\Dev\ideas\project-ideas_structured\token-saver-meta-savings-audit.md` |
| Insight Registry (22 actionable) | `docs/insight_registry.md` |
| Complete Insights (37 + 22 synergies) | `docs/insights_and_synergies.md` |
| Tool Leaderboard (44 tools) | `BESTS.md` |
| Master Plan | `progress_docs/plans/full.md` |

---

## Next Session Agent MUST

### Step 1: Read these files in order

1. `MEMORY.md` — stale, but shows project intent
2. `AGENTS.md` — full architecture, token types T1-T7, AGENTS.md protocol
3. `progress_docs/README.md` — plan type system, file conventions
4. `progress_docs/plans/full.md` — Phase 07-10 task tables

### Step 2: Update stale files BEFORE starting work

**MEMORY.md is stale** — still says "Research phase — repos cloned, evaluation pending." Must be rewritten to reflect: Phases 01-06 COMPLETE, Phase 07 (Core Bundle Implementation) is the next action.

**progress_docs/README.md** is missing:
- `migration` plan type (investment_trying has it)
- "Agent Self-Extension" protocol (so agents can add new plan types)
- `deferred_reason` + `revisit_when` in file conventions

### Step 3: Initialize progress system hygiene (P0 before implementation)

These were identified as gaps vs investment_trying. Do these BEFORE starting Phase 07:

1. **Create per-phase plan files** — Extract phase 07-10 from `plans/full.md` into:
   - `progress_docs/plans/07-core-bundle.md` (YAML frontmatter: type=phase, phase="07", name, status=pending, tasks from full.md)
   - `progress_docs/plans/08-optional-modules.md`
   - `progress_docs/plans/09-distribution.md`
   - `progress_docs/plans/10-testing.md`

2. **Create per-phase log files** — Retrospectively log completed phases:
   - `progress_docs/logs/01-05-research.md` (summarize phases 01-05 from current.md)
   - `progress_docs/logs/06-scaffold.md`

3. **Update `current.md`** — Add entry for this handover, bump "last action" to "Phase 07 ready"

4. **Rewrite `MEMORY.md`** — Reflect completed research + implementation phase

### Step 4: Phase 07 — Core Bundle Implementation

From `progress_docs/plans/full.md` Phase 07:

| Priority | Task |
|----------|------|
| **P0** | Create installer scaffold (Python-based, inherit from `gitnexus_CGC_combo`) |
| **P0** | Platform detection (filesystem marker scanning from combo's `config_gen.py`) |
| **P0** | MCP config generation (multi-format JSON from combo's `matrix.json`) |
| **P0** | GitNexus + CGC integration (copy existing combo setup logic) |
| **P0** | RTK integration (auto-detect + `rtk init -g` hooks) |
| **P0** | codesight integration (auto-run `npx codesight` on project) |
| **P0** | SKILL.md bundling (caveman + LG-token-saver + kevin-copilot skills) |
| **P0** | AGENTS.md injection (token-saving protocol injection) |
| **P1** | ContextSlimAI integration (`contextslim init` for rules generation) |
| **P1** | Repomix integration (`npx repomix` on first setup) |
| **P1** | Dashboard scaffold (status page: tool health + savings) |

**Foundation reference:** `C:\Dev\projects\token-saver-meta\useful-repos\gitnexus_CGC_combo\` — study `src/config_gen.py` and `platforms/matrix.json` as the installer backbone.

### Key Design Decisions (DO NOT REVISIT)

- Core bundle = 10 tools. Optional = 8. Deep study = 8. These are settled.
- Only 1 real conflict (RTK shell hook vs lean-ctx shell hook — RTK wins, lean-ctx gets shell hook disabled)
- Tier 3 tools (tokensave, opentoken, omni, etc.) are for v2 — do not implement now
- All savings claims must cite source (see savings audit)

### Architecture Summary

```
Core (Tier 1 — always installed):
  GitNexus (T1) + CGC (T1) + RTK (T2) + codesight (T1) + Repomix (T1)
  + caveman (T3) + LG-token-saver (T1+T2+T3) + ContextSlimAI (T2)
  + kevin-copilot (T3) + Token Saver Meta (installer)

Optional (Tier 2 — one-click enable):
  TSCG (T6) + lean-ctx MCP (T1, shell hook disabled) + LLMLingua-2 (T4)
  + codex-agent-mem (T5) + Loom (T5) + Deblank (T4) + toon (T4+T6)
  + orchestkit-extracted (T5)
```

---

## Quick Reference: All Relevant Files

| File | Purpose |
|------|---------|
| `C:\Dev\projects\token-saver-meta\AGENTS.md` | AUTHORITATIVE — full architecture, token types, protocol |
| `C:\Dev\projects\token-saver-meta\BESTS.md` | 44-tool leaderboard, 4 tiers |
| `C:\Dev\projects\token-saver-meta\MEMORY.md` | STALE — needs rewrite |
| `C:\Dev\projects\token-saver-meta\docs\insights_and_synergies.md` | 37 insights + 22 synergies |
| `C:\Dev\projects\token-saver-meta\docs\insight_registry.md` | 22 actionable insights |
| `C:\Dev\projects\token-saver-meta\progress_docs\plans\full.md` | Master plan all phases |
| `C:\Dev\projects\token-saver-meta\progress_docs\current.md` | Session log (7 entries) |
| `C:\Dev\projects\token-saver-meta\progress_docs\README.md` | Progress system conventions |
| `C:\Dev\ideas\project-ideas_structured\token-saver-meta-max-coexistence.md` | ⭐ AUTHORITATIVE — 15 tools, 3 tiers, 1 conflict |
| `C:\Dev\ideas\project-ideas_structured\token-saver-meta-savings-audit.md` | Fact-checked savings claims |
| `C:\Dev\projects\token-saver-meta\useful-repos\gitnexus_CGC_combo\` | Foundation code for installer |
