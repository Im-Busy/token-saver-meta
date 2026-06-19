# Draft: standalone-repo-setup

> **status:** generating-plan
> **created:** 2026-06-19

## Decision Ledger

| Decision | Rationale | Default |
|----------|-----------|---------|
| **Standalone repo** | Required for `npx create-token-saver` + `pip install token-saver-meta` (Phase 09). C:\Dev is a private workspace monorepo that intentionally excludes `projects/` from its public mirror. | User-approved |
| **Monorepo sub-packages** | Current layout has tscg-py, token-saver-mem, contextslim-py as subdirectories. No .git in any sub-project. Phase 09 targets single package. Splitting to polyrepo is v2. | Adopted default |
| **Dual-remote** | Private source + public curated mirror. Follows dual-repo-setup pattern. User explicitly chose dual-remote. | User-approved |
| **MIT License** | Most bundled tools use MIT. caveman, ponytail, LG-token-saver, kevin-copilot, TSCG, CGC, codesight are MIT. | Adopted default |
| **Public AGENTS.md** | User-facing documentation + token-saving protocol injection block = product content. Internal references (MEMORY.md, progress_docs/) are documentation, not secrets. | Adopted default |
| **Private MEMORY.md** | Internal handover state, session-to-session state. No user value. | Adopted default |
| **Private progress_docs/** | Handover notes, session logs. Internal. | Adopted default |
| **Private useful_repos/** | 46 cloned reference repos with varying licenses. Research artifacts, not distributable. | Evidence-resolved |
| **Private .kilo/ .omo/ .codegraph/** | Agent runtime artifacts, plan artifacts, local indexes. | Evidence-resolved |

## Public/Private Classification

### PUBLIC (public remote branch)
```
src/               — Core installer code
tests/             — Test suite
docs/              — Architecture, rewrite strategy, insights
templates/         — AGENTS.md injection block
skills/            — Vendored SKILL.md tools
platforms/         — Platform detection matrix
dashboard/         — Status page
contextslim-py/    — Python rewrite (src/, tests/, pyproject.toml, uv.lock)
tscg-py/           — Python rewrite (src/, tests/, pyproject.toml, uv.lock)
token-saver-mem/   — Python rewrite (src/, tests/, pyproject.toml, uv.lock)
cli.js             — npm entry point
package.json       — npm config
pyproject.toml     — Python config
uv.lock            — Python lockfile
.gitignore         — Required for both branches
LICENSE            — MIT (to create)
README.md          — (to create)
AGENTS.md          — Project docs + protocol injection
BESTS.md           — Tool leaderboard
```

### PRIVATE (private branch only)
```
.kilo/             — Kilo agent configs with local paths
.omo/              — Plan artifacts
.codegraph/        — Local codegraph index
MEMORY.md          — Agent handover state
kilo.json          — Kilo platform config
opencode.jsonc     — OpenCode config
progress_docs/     — Handovers, logs, internal plans
useful_repos/      — 46 cloned reference repos
token-saver-meta.md — Brainstorm doc
```

### GITIGNORED (never on any branch)
```
.venv/, .pytest_cache/, .ruff_cache/, __pycache__/, *.pyc
dist/, *.egg-info/, node_modules/
.codegraph/, CODESIGHT.md, repomix-output.*, .repomixignore
.bak-*
```

## Sub-project .gitignore Status

Sub-projects (tscg-py, token-saver-mem, contextslim-py) have their own `.venv/` and `.pytest_cache/`. Root `.gitignore` with `**/` patterns covers all subdirectories. No individual `.gitignore` files needed.

## Remote URLs

User must provide:
- `private` remote: e.g. `git@github.com:<user>/token-saver-meta.git` (or https)
- `public` remote: e.g. `git@github.com:<user>/token-saver-meta-public.git`

## Gap Analysis (Metis — 2026-06-19)

| Gap | Severity | Resolution |
|-----|----------|------------|
| License contradiction: root planned MIT, subs declare Apache-2.0 | CRITICAL | Resolved: adopt Apache-2.0 globally. Root pyproject.toml gets `license = {text = "Apache-2.0"}`. Todo 5 updated. |
| Root .gitignore missing .venv/ | HIGH | Already planned in todo 2. Confirmed included. |
| Sub-projects missing .gitignore | HIGH | Added todo 3: create `.gitignore` per sub-project with venv/cache patterns (defense-in-depth). |
| useful_repos/ classification ambiguous | HIGH | Resolved: gitignore entirely. Never tracked on any branch. Contains cloned third-party repos. Todo 2 updated, removed from all private file lists. |
| AGENTS.md hardcoded C:\Dev paths | LOW | False alarm — project AGENTS.md uses relative paths (`docs/architecture-v2.md`). Workspace AGENTS.md is separate. No fix needed. |
| dual-remote filter mechanism undefined | MEDIUM | Resolved: made explicit in todo 6 — filtered public branch via `git rm --cached`. Mechanism documented in todo description. |
| BESTS.md unclassified | LOW | Confirmed public in todo 7 whitelist. Present in both branch acceptance criteria. |
| stress_high_pressure.py unclassified | LOW | Public (test utility in sub-project tests/). Covered by sub-project dir entry in whitelist. |
| No .gitattributes for line endings | MEDIUM | Added todo 4: `.gitattributes` with `* text=auto`, `*.py text eol=lf`, etc. for Windows→LF. |
| npm "files" excludes docs/ | LOW | Deferred to Phase 09. Not a repo setup concern. |
| No CI/CD config | LOW | Deferred to Phase 09. Not a repo setup concern. |

## Files to Create

| File | Purpose |
|------|---------|
| `LICENSE` | Apache-2.0 (matching all 3 sub-projects) |
| `README.md` | Getting started, architecture summary, usage |
| `.gitattributes` | Cross-platform line ending normalization |
| `tscg-py/.gitignore` | Sub-project defense-in-depth |
| `token-saver-mem/.gitignore` | Sub-project defense-in-depth |
| `contextslim-py/.gitignore` | Sub-project defense-in-depth |
| `whitelist.txt` | Public paths for sync agent |
| `.kilo/agent/repo-syncer.md` | Sync agent definition |
| `.kilo/command/repo-sync.md` | Sync slash command |

## Plan Status

**status:** complete
**plan:** `.omo/plans/standalone-repo-setup.md` (11 todos, 4 waves)
**next:** present summary → ask start-work-or-review question → stop
