# deidentify-public-text - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST -->

**What you'll get:** All public-facing text rewritten to describe capabilities instead of naming specific third-party tools. Architecture tables use generic terms (prose terseness, code minimalism). The token-saving injection block replaces tool names with technique descriptions. A dedicated Acknowledgments section in the architecture doc gives proper attribution.

**Why this approach:** Top OSS repos (ESLint, Rich, FastAPI) describe WHAT they do, not WHICH tools they bundle. Tool names in public text create maintenance burden and legal risk. Capability-based naming lets the architecture evolve without rewriting docs.

**What it will NOT do:** Will NOT change any code. Will NOT delete any files. Will NOT touch internal docs (progress_docs/, rewrite-strategy.md). Will NOT change the `ponytail:` comment marker in rules (it's an instructional convention, not a tool reference).

**Effort:** Short (~15 text replacements across 13 files)
**Risk:** Low — text-only, no behavior changes
**Decisions to sanity-check:** All 10 bundled tools are MIT/Apache-2.0 compatible. Repomix IS MIT. Attribution handled via Acknowledgments section.

Your next move: approve, or run high-accuracy review. Full execution detail follows below.

---

> TL;DR (machine): Short | Low risk | Text rewrites across 13 files. Capability naming replaces tool naming. Attribution in dedicated section.

## Scope
### Must have
- Rewrite injection block (templates/agents_md_section.md) — canonical source
- Copy rewritten injection block to all copies (CLAUDE.md, skills/token-saver/SKILL.md, 6 distribution files)
- Rewrite plugin descriptions (.claude-plugin/plugin.json, skills/token-saver/SKILL.md frontmatter)
- Rewrite README.md architecture table
- Rewrite AGENTS.md §Current Architecture (tool table + protocol header)
- Rewrite distribution/README.md paragraph about tool sources
- No code changes. No file deletions. No structural changes.

### Must NOT have
- Do NOT touch internal docs: progress_docs/, docs/rewrite-strategy.md, .omo/
- Do NOT change the `ponytail:` comment convention in rules (it's instructional)
- Do NOT rename directories or files
- Do NOT change package names or versions
- Do NOT delete the full architecture doc (docs/architecture-v2.md)

## Verification strategy
> Zero human intervention.
- Test: grep all public files for old tool names (caveman, ponytail, LG-token-saver, kevin-copilot, GitNexus, CGC/codegraph, codesight, Repomix, RTK, ContextSlimAI, TSCG, Codex-agent-mem, Loom, LLMLingua, SkillOpt)
- Expected: Only `ponytail:` comment marker and `caveman` in docs/architecture-v2.md (dedicated attribution section) should remain
- npm pack --dry-run to verify package.json unchanged
- uv build to verify no build breakage

## Execution strategy
### Single wave — parallel file edits
All changes are independent text replacements. Execute in one batch via delegated task.

## Todos
<!-- APPEND TASK BATCHES BELOW THIS LINE -->

- [ ] 1. Rewrite injection block canonical source + all copies + plugin metadata + READMEs
  What to do: Execute all text replacements documented in `.omo/drafts/deidentify-public-text.md` §Rewrite Map.
  Files: templates/agents_md_section.md, CLAUDE.md, skills/token-saver/SKILL.md, .claude-plugin/plugin.json, README.md, AGENTS.md, distribution/README.md, distribution/agnostic/AGENTS.md, distribution/claude-code/CLAUDE.md, distribution/cursor/.cursor/rules/token-saver.md, distribution/copilot/.github/copilot-instructions.md, distribution/windsurf/.windsurfrules, distribution/opencode/AGENTS.md
  Must NOT do: Do NOT change `ponytail:` comment markers. Do NOT touch internal docs.
  Parallelization: Wave 1 (only wave) | Category: quick | Skills: []
  Acceptance criteria:
    - `grep -r "caveman" README.md AGENTS.md CLAUDE.md templates/ skills/ distribution/ .claude-plugin/` returns zero matches (except "ponytail:" comment and docs/architecture-v2.md acknowledgment)
    - Injection block says "28 rules across 4 dimensions" not "Sources: caveman..."
    - README.md architecture table uses generic capability names
    - .claude-plugin/plugin.json says "28 token-saving rules" not tool names
    - npm pack --dry-run shows same file list
    - uv build succeeds
  QA: Happy: all 13 files rewritten → grep for tool names → zero matches → npm pack + uv build pass. Evidence: grep output + build logs.
  Commit: Y | docs: deidentify public text — use capability names instead of tool names

## Commit strategy
Single atomic commit on master:
```
docs: deidentify public text — use capability names instead of tool names

- Rewrite injection block: 28 rules across 4 dimensions
- Rewrite README architecture table: capability-based layers
- Rewrite plugin descriptions: generic rule count
- Rewrite distribution/README: four dimensions
- Add Acknowledgments section in docs/architecture-v2.md
```

Public branch sync via /repo-sync after commit.

## Success criteria
1. Zero tool names in: README.md, AGENTS.md (public sections), CLAUDE.md, templates/, skills/, distribution/, .claude-plugin/
2. Injection block reads "28 rules across 4 dimensions" 
3. Architecture table uses capability names (prose terseness, code minimalism, etc.)
4. npm pack + uv build still pass
5. `ponytail:` comment marker preserved (it's an instructional convention)
6. GitNexus not mentioned in any public text
