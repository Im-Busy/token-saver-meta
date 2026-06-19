# standalone-repo-setup - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** A standalone git repo for token-saver-meta with dual-remote (private source + public curated mirror), complete gitignore, MIT license, README, and automated sync infrastructure. Ready for Phase 09 npm/PyPI publishing.

**Why this approach:** Standalone repo is required for `npx create-token-saver` and `pip install token-saver-meta`. Dual-remote (filtered public branch via `git rm --cached`) keeps internal docs private while publishing the package cleanly — the same pattern already proven at workspace level.

**What it will NOT do:** Will NOT touch C:\Dev's git state. Will NOT split sub-packages into separate repos. Will NOT push to remotes until user provides URLs. Will NOT track `useful_repos/` on any branch.

**Effort:** Short (~9 sequenced todos, 1-2 tool calls each)
**Risk:** Low — git operations only, no code changes, fully reversible before push
**Decisions to sanity-check:** Apache-2.0 license (matching all 3 sub-projects), monorepo sub-packages (tscg-py + token-saver-mem + contextslim-py stay as subdirectories), `useful_repos/` gitignored entirely

Your next move: approve or run high-accuracy review. Full execution detail follows below.

---

> TL;DR (machine): Short | Low risk | Standalone git repo + dual-remote + sync infra. 11 todos across 4 waves. Apache-2.0 license matching all sub-projects.

## Scope
### Must have
- `git init` in `C:\Dev\projects\token-saver-meta` (standalone, not using `C:\Dev\.git`)
- Complete root `.gitignore` covering all generated/venv/cache files with `**/` sub-project patterns
- Individual `.gitignore` files in each sub-project (tscg-py, token-saver-mem, contextslim-py)
- `.gitattributes` for cross-platform line ending handling (Windows CRLF → LF on commit)
- Apache-2.0 `LICENSE` file and `license` field added to root `pyproject.toml`
- User-facing `README.md` (architecture summary, quick-start)
- Initial commit on `master` branch with all current files (minus gitignored)
- `public` branch curated via `git rm --cached` (filtered public branch pattern — files stay on disk, only stripped from public tracking)
- Dual remote configuration (user provides URLs)
- Sync agent + slash command for ongoing private→public merge
- "Repository Architecture" section in AGENTS.md

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do NOT modify C:\Dev\.git or C:\Dev git state
- Do NOT create `.git` in sub-packages (tscg-py, token-saver-mem, contextslim-py stay monorepo)
- Do NOT push to any remote until remotes are explicitly configured and user confirms
- Do NOT delete any files from disk — curation is via `git rm --cached` on public branch only
- Do NOT add `progress_docs/`, `MEMORY.md`, `.omo/`, `.kilo/` to `.gitignore` — they are tracked on private branch, stripped on public branch
- Do NOT track `useful_repos/` on ANY branch — gitignore entirely (contains cloned third-party repos)
- Do NOT move, rename, or restructure project directories

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after (git verification commands, no unit tests)
- Evidence: `.omo/evidence/task-<N>-standalone-repo-setup.txt`

## Execution strategy
### Parallel execution waves
| Wave | Todos | Description |
|------|-------|-------------|
| W1 | 1, 2, 3, 4, 5 | Foundation: git init, root .gitignore, sub-project .gitignore, .gitattributes, LICENSE/README |
| W2 | 6, 7 | Branch setup: create public branch + whitelist |
| W3 | 8 | Remote config (user provides URLs) |
| W4 | 9, 10, 11 | Sync infra + AGENTS.md update |

Todos 2,3,4,5 run first in parallel (all create independent files). Todo 1 runs AFTER 2-5 complete — `git init + add + commit` requires `.gitignore`, `.gitattributes`, LICENSE, README, and sub-project `.gitignore` files to exist first so no build artifacts or third-party repos are committed. W2 depends on W1 (needs .git). W3 depends on W2 (needs branches). W4 depends on W3 (sync agent needs remote names).

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | 2,3,4,5 | 6,7 | — (waits for W1 peers) |
| 2 | — | 1 | 3,4,5 |
| 3 | — | 1 | 2,4,5 |
| 4 | — | 1 | 2,3,5 |
| 5 | — | 1 | 2,3,4 |
| 6 | 1 | 7,8 | — |
| 7 | 6 | 8 | — |
| 8 | 6,7 | 9,10,11 | — |
| 9 | 8 | — | 10,11 |
| 10 | 8 | — | 9,11 |
| 11 | 8 | — | 9,10 |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->

- [ ] 1. Initialize standalone git repo + initial commit
  What to do: Run `git init` in `C:\Dev\projects\token-saver-meta`. Stage ALL current files except gitignored patterns with `git add .`. Create initial commit: `feat: initial token-saver-meta — standalone repo with 3 sub-packages, 1K+ tests, Phase 07-08 complete`.
  Must NOT do: Do NOT use `C:\Dev\.git`. Do NOT touch C:\Dev git state. Do NOT `git add` until root .gitignore is written (todo 2) — this todo runs WITH todo 2 in same wave, so execute todo 2 FIRST, then git add. Verify `git init` creates `.git` inside token-saver-meta, not using parent.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 6,7. MUST run after todo 2 in same wave (gitignore must exist before git add).
  References: Current directory at `C:\Dev\projects\token-saver-meta`. Draft: `.omo/drafts/standalone-repo-setup.md` for file classification.
  Acceptance criteria (agent-executable):
    - `git -C C:\Dev\projects\token-saver-meta rev-parse --show-toplevel` equals `C:\Dev\projects\token-saver-meta`
    - `git -C C:\Dev\projects\token-saver-meta log --oneline` shows exactly 1 commit
    - `git -C C:\Dev\projects\token-saver-meta status` is clean (no untracked, no modified)
    - `git -C C:\Dev\projects\token-saver-meta ls-files | grep -E '\.venv/|\.pytest_cache/'` returns empty (no build artifacts tracked)
    - `git -C C:\Dev\projects\token-saver-meta ls-files | grep useful_repos` returns empty (useful_repos gitignored)
  QA scenarios:
    - Happy: git init → (todo 2 writes .gitignore) → git add . → git commit → git status clean → git ls-files verified. Evidence: `.omo/evidence/task-1-standalone-repo-setup.txt` (git status + git log + git ls-files output)
    - Failure: `useful_repos/` files appear in tracked → .gitignore missing → fix pattern, re-add. Failure: `.venv/` files tracked → gitignore incomplete → amend.
  Commit: Y | feat(repo): initialize standalone git repo for token-saver-meta

- [ ] 2. Write root .gitignore with complete exclusions
  What to do: Overwrite `.gitignore` at `C:\Dev\projects\token-saver-meta\.gitignore` with comprehensive exclusion patterns. Include both root-level and `**/` sub-project patterns.
  Must NOT do: Do NOT add private-only files (MEMORY.md, progress_docs/, .omo/, .kilo/, kilo.json, opencode.jsonc, token-saver-meta.md) to .gitignore — they are tracked on private branch, stripped only on public branch. Do NOT add root config files (package.json, pyproject.toml, cli.js, uv.lock, BESTS.md, AGENTS.md) — they are tracked on both branches.
  Must INCLUDE (verbatim copy):
    ```
    # Python
    __pycache__/
    *.py[cod]
    *.egg-info/
    dist/
    .pytest_cache/
    .ruff_cache/
    .venv/
    # Node
    node_modules/
    # Tool output
    CODESIGHT.md
    repomix-output.*
    .repomixignore
    .bak-*
    .codegraph/
    # Cloned reference repos (never track)
    useful_repos/
    # Sub-project coverage
    **/__pycache__/
    **/*.pyc
    **/.pytest_cache/
    **/.venv/
    **/dist/
    **/*.egg-info/
    ```
  Parallelization: Wave 1 | Blocked by: — | Blocks: 1 (must exist before git add)
  References: Current `.gitignore` at `C:\Dev\projects\token-saver-meta\.gitignore` (12 lines, missing .venv/.codegraph/useful_repos). Sub-projects: `tscg-py/`, `token-saver-mem/`, `contextslim-py/` each have `.venv/` and `.pytest_cache/`.
  Acceptance criteria (agent-executable):
    - File contains all patterns listed in "Must INCLUDE" above
    - `git status` shows `.venv/` and `.pytest_cache/` NOT in untracked (proves gitignore works)
    - `MEMORY.md`, `progress_docs/`, `.omo/`, `.kilo/` ARE in git status untracked (proves NOT gitignored)
    - `useful_repos/` NOT in git status untracked (proves gitignored)
  QA scenarios:
    - Happy: Write .gitignore → `git status` → verify above patterns. Evidence: `.omo/evidence/task-2-standalone-repo-setup.txt` (cat .gitignore + git status output)
    - Failure: Missing `**/` pattern → sub-project .venv appears in git status → add pattern, re-verify
  Commit: Y | chore(repo): add comprehensive .gitignore with sub-project coverage

- [ ] 3. Create .gitignore files for sub-projects (tscg-py, token-saver-mem, contextslim-py)
  What to do: Create `.gitignore` in each sub-project directory. Minimal content: `.venv/`, `.pytest_cache/`, `__pycache__/`, `dist/`, `*.egg-info/`, `*.pyc`. Redundant with root `**/` patterns but provides defense-in-depth for IDEs and sub-project-level git operations.
  Must NOT do: Do NOT add project-specific paths (src/, tests/) — these are tracked.
  Parallelization: Wave 1 | Blocked by: — | Blocks: —
  References: Each sub-project has `.venv/` and `.pytest_cache/` directories. Root pyproject.toml `[tool.hatch.build.targets.wheel]`.
  Acceptance criteria (agent-executable):
    - `tscg-py/.gitignore`, `token-saver-mem/.gitignore`, `contextslim-py/.gitignore` all exist
    - Each contains: `.venv/`, `.pytest_cache/`, `__pycache__/`, `dist/`, `*.egg-info/`, `*.pyc`
  QA scenarios:
    - Happy: Create 3 files → grep each for required patterns → all match. Evidence: `.omo/evidence/task-3-standalone-repo-setup.txt`
    - Failure: Missing a file → `git status` would catch it during todo 1's add step
  Commit: Y | chore(repo): add .gitignore files to sub-projects

- [ ] 4. Create .gitattributes for cross-platform line endings
  What to do: Create `.gitattributes` at `C:\Dev\projects\token-saver-meta\.gitattributes`. Windows host (CRLF working tree) → LF on commit. Standard Python/JS patterns.
  Content:
    ```
    * text=auto
    *.py text eol=lf
    *.js text eol=lf
    *.md text eol=lf
    *.json text eol=lf
    *.toml text eol=lf
    *.txt text eol=lf
    *.yml text eol=lf
    *.yaml text eol=lf
    ```
  Must NOT do: Do NOT add binary file patterns (no *.png, *.whl, etc. in this repo).
  Parallelization: Wave 1 | Blocked by: — | Blocks: —
  References: Standard GitHub `.gitattributes` for Python projects on Windows. Git docs: `gitattributes(5)`.
  Acceptance criteria (agent-executable):
    - `.gitattributes` exists at project root
    - Contains `* text=auto` on first non-comment line
    - Contains `*.py text eol=lf`
  QA scenarios:
    - Happy: Create file → verify content. Evidence: `.omo/evidence/task-4-standalone-repo-setup.txt`
  Commit: Y | chore(repo): add .gitattributes for cross-platform line endings

- [ ] 5. Create LICENSE (Apache-2.0), add license to root pyproject.toml, create README.md
  What to do: (a) Create `LICENSE` with Apache License 2.0 text from `https://www.apache.org/licenses/LICENSE-2.0.txt`. (b) Add `license = {text = "Apache-2.0"}` under `[project]` in root `pyproject.toml` (matching all 3 sub-projects). (c) Create `README.md` with: project title + tagline ("Token Saving for the Masses"), one-sentence purpose, architecture summary (Base/Intelligence/Compression/Optional layers), quick-start (`npx create-token-saver`), link to docs/architecture-v2.md, license badge.
  Must NOT do: Do NOT use MIT — all sub-projects already declare Apache-2.0. Do NOT mention internal files (MEMORY.md, progress_docs). Do NOT include installation instructions that don't work yet (Phase 09 not done).
  Parallelization: Wave 1 | Blocked by: — | Blocks: —
  References:
    - tscg-py/pyproject.toml: `license = {text = "Apache-2.0"}`
    - token-saver-mem/pyproject.toml: `license = {text = "Apache-2.0"}`
    - contextslim-py/pyproject.toml: `license = {text = "Apache-2.0"}`
    - Root pyproject.toml has NO license field — must add
    - AGENTS.md §Purpose for tagline, §Current Architecture for 4-layer summary
    - package.json `"name": "create-token-saver"`, `"bin"` field
    - pyproject.toml `[project.scripts] token-saver = "src.installer:main"`
    - Apache-2.0 template: `https://www.apache.org/licenses/LICENSE-2.0.txt`
  Acceptance criteria (agent-executable):
    - `LICENSE` exists, contains "Apache License, Version 2.0" and "http://www.apache.org/licenses/LICENSE-2.0"
    - `pyproject.toml` contains `license = {text = "Apache-2.0"}` under `[project]`
    - `README.md` exists, contains "Token Saving for the Masses", "create-token-saver", "token-saver-meta"
    - All 3 files ≤3KB each
  QA scenarios:
    - Happy: Create files + edit pyproject.toml → verify content keywords. Evidence: `.omo/evidence/task-5-standalone-repo-setup.txt` (cat LICENSE + grep README keywords + grep pyproject.toml license)
    - Failure: License mismatch (APACHE vs MIT) → grep all pyproject.toml files for license field → all must match
  Commit: Y | docs(repo): add Apache-2.0 LICENSE, README.md, and root license field

- [ ] 6. Create and curate public branch
  What to do: `git checkout -b public`. Strip private files from public tracking using `git rm --cached -r`. Commit the curation. Switch back to `master`.
  Must NOT do: Do NOT `git rm` without `--cached` — files must remain on disk. Do NOT include `useful_repos/` in rm command — it's already gitignored (never tracked). Do NOT delete files from filesystem.
  Mechanism: Filtered public branch (`git rm --cached`). Files stay on disk on both branches; only the public branch's git index excludes them. This preserves full history on private branch while publishing a clean subset.
  Commands:
    1. `git checkout -b public`
    2. `git rm --cached -r MEMORY.md kilo.json opencode.jsonc token-saver-meta.md`
    3. `git rm --cached -r .kilo/ .omo/ .codegraph/ progress_docs/`
    4. `git commit -m "curate: remove private files for public mirror"`
    5. `git checkout master`
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 7,8
  References: dual-repo-setup skill Step 7 (filtered public branch pattern). Draft: `.omo/drafts/standalone-repo-setup.md` for public/private classification.
  Acceptance criteria (agent-executable):
    - `git checkout public && git ls-tree -r --name-only HEAD` does NOT contain: MEMORY.md, kilo.json, opencode.jsonc, token-saver-meta.md, progress_docs/, .kilo/, .omo/, .codegraph/
    - `git checkout public && git ls-tree -r --name-only HEAD` DOES contain: src/, tests/, docs/, AGENTS.md, BESTS.md, package.json, pyproject.toml, cli.js, LICENSE, README.md, .gitignore, .gitattributes
    - `git checkout public && git ls-tree -r --name-only HEAD` DOES contain all 3 sub-projects: tscg-py/, token-saver-mem/, contextslim-py/
    - `git checkout master && Test-Path MEMORY.md` returns True — file still exists on disk
  QA scenarios:
    - Happy: Create public branch → rm --cached private files → commit → verify ls-tree for both branches. Evidence: `.omo/evidence/task-6-standalone-repo-setup.txt` (git ls-tree output for master and public)
    - Failure: Used `git rm` without `--cached` → file deleted from disk → restore from master, retry with `--cached`
  Commit: N (committed within branch creation as `curate: remove private files for public mirror`)

- [ ] 7. Create whitelist.txt for sync agent
  What to do: Create `whitelist.txt` at `C:\Dev\projects\token-saver-meta\whitelist.txt` listing all public paths with section comments. Follow dual-repo-setup skill Step 3 pattern.
  Must NOT do: Do NOT list private files (MEMORY.md, progress_docs/, .kilo/, .omo/, .codegraph/). Do NOT list gitignored files (.venv/, __pycache__/, useful_repos/). Do NOT list sub-project internal .gitignore files individually — the parent dir `/` covers them.
  Must INCLUDE:
    - Source: `src/`, `cli.js`
    - Tests: `tests/`
    - Docs: `docs/`, `AGENTS.md`, `BESTS.md`, `README.md`
    - Config: `package.json`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.gitattributes`
    - Assets: `templates/`, `skills/`, `platforms/`, `dashboard/`
    - License: `LICENSE`
    - Sub-projects: `tscg-py/`, `token-saver-mem/`, `contextslim-py/`
    - Sync infra: `whitelist.txt`
  Parallelization: Wave 2 | Blocked by: 6 | Blocks: 8
  References: dual-repo-setup skill Step 3. Cross-reference with todo 6 acceptance criteria for verified public files on public branch.
  Acceptance criteria (agent-executable):
    - `whitelist.txt` exists, non-empty
    - Count of non-comment, non-empty lines ≥ 18 (covers all public dirs + files)
    - Every dir entry ends with `/`
    - `Select-String -Pattern "(MEMORY|progress_docs|\.kilo|\.omo|\.venv|useful_repos)" whitelist.txt` returns zero matches
  QA scenarios:
    - Happy: Create whitelist.txt → grep for private/gitignored paths → zero matches → count ≥ 18 lines. Evidence: `.omo/evidence/task-7-standalone-repo-setup.txt`
    - Failure: Missing a public directory → cross-reference with `git ls-tree -r --name-only HEAD` from public branch
  Commit: Y | chore(repo): add whitelist.txt for public mirror curation

- [ ] 8. Configure dual remotes and push branches
  What to do: Add `private` and `public` git remotes. Push `master` to private, `public` branch to public. Remote URLs provided by user or adopted as placeholder.
  Must NOT do: Do NOT push `master` to public remote. Do NOT push `public` branch to private remote. Do NOT configure remotes that don't exist yet — if user hasn't provided URLs, add placeholders and mark this todo as BLOCKED.
  Commands:
    1. `git remote add private <private-url>` (user provides)
    2. `git remote add public <public-url>` (user provides)
    3. `git push -u private master`
    4. `git push -u public public`
  Parallelization: Wave 3 | Blocked by: 6,7 | Blocks: 9,10,11
  References: dual-repo-setup skill Steps 5, 9. User must create repos on GitHub/GitLab first.
  Acceptance criteria (agent-executable):
    - `git remote -v` shows both `private` and `public` with correct URLs
    - `git ls-remote private` shows `refs/heads/master`
    - `git ls-remote public` shows `refs/heads/public` ONLY (no master/main on public)
  QA scenarios:
    - Happy: Add remotes → push both branches → verify ls-remote. Evidence: `.omo/evidence/task-8-standalone-repo-setup.txt` (git remote -v + git ls-remote both)
    - Failure: Remote URL invalid → git push fails → verify URL, retry. Failure: master pushed to public → `git push public --delete master`
  Commit: N (git operations only, no file changes)

- [ ] 9. Create sync agent definition (.kilo/agent/repo-syncer.md)
  What to do: Create `.kilo/agent/repo-syncer.md` with dual-repo sync workflow. Pattern: verify remotes → `git checkout public` → `git merge master` → safety check (no private files on public via whitelist.txt) → `git checkout master` → `git push public public`. Include private files exclusion list.
  Must NOT do: Do NOT create a command file — that's todo 10. Do NOT hardcode remote URLs — use `private` and `public` remote names. Do NOT reference `useful_repos/` in exclusion list (it's gitignored, never tracked).
  Private files exclusion list: MEMORY.md, kilo.json, opencode.jsonc, token-saver-meta.md, .kilo/, .omo/, .codegraph/, progress_docs/
  Parallelization: Wave 4 | Blocked by: 8 | Blocks: —
  References: dual-repo-setup skill Step 8. Draft `.omo/drafts/standalone-repo-setup.md`. Existing pattern: `C:\Dev\.kilo/agent/repo-syncer.md`.
  Acceptance criteria (agent-executable):
    - `.kilo/agent/repo-syncer.md` exists, ≥20 lines
    - Contains: `git checkout public`, `git merge master`, safety check for private files, `git push public public`
    - Contains all 8 private paths listed above
    - Does NOT contain `useful_repos`
  QA scenarios:
    - Happy: Create agent def → grep for 5 workflow steps + 8 private paths → zero matches for useful_repos. Evidence: `.omo/evidence/task-9-standalone-repo-setup.txt`
    - Failure: Missing a private path in exclusion list → sync would leak → cross-reference with todo 6 rm --cached list
  Commit: Y | feat(repo): add repo-syncer agent for dual-repo sync workflow

- [ ] 10. Create sync slash command (.kilo/command/repo-sync.md)
  What to do: Create `.kilo/command/repo-sync.md` with three sub-commands: `check` (safety check only), `status` (show branch state + remote config), and full sync (invoke repo-syncer agent). Include usage examples.
  Must NOT do: Do NOT duplicate the sync workflow — delegate to agent. Do NOT make the command do the sync directly.
  Parallelization: Wave 4 | Blocked by: 8 | Blocks: —
  References: dual-repo-setup skill Step 8. Existing pattern: `C:\Dev\AGENTS.md` §Slash Commands.
  Acceptance criteria (agent-executable):
    - `.kilo/command/repo-sync.md` exists, ≥15 lines
    - Contains: `/repo-sync` (full sync), `/repo-sync check` (safety check), `/repo-sync status` (show state)
    - References repo-syncer agent for the full sync action
  QA scenarios:
    - Happy: Create command def → grep for 3 sub-commands + agent reference. Evidence: `.omo/evidence/task-10-standalone-repo-setup.txt`
  Commit: Y | feat(repo): add repo-sync slash command with check/status/sync

- [ ] 11. Update AGENTS.md with Repository Architecture section
  What to do: Add `## Repository Architecture — Dual-Repo (Private → Public)` section to `AGENTS.md` at `C:\Dev\projects\token-saver-meta\AGENTS.md`. Insert after §Key Documents, before §Quick Reference. Document: remotes (private/public), branches (master/public), what goes public vs stays private, sync commands.
  Must NOT do: Do NOT remove or modify any existing section. Do NOT add duplicate sections. Do NOT mention `useful_repos/`.
  Content: Remotes table (private → master, public → public), public branch contents (src, tests, docs, configs, 3 sub-projects), what stays private (MEMORY, progress_docs, .kilo, .omo, .codegraph, kilo.json, opencode.jsonc), sync commands (`/repo-sync`, `/repo-sync check`, `/repo-sync status`).
  Parallelization: Wave 4 | Blocked by: 8 | Blocks: —
  References: C:\Dev\AGENTS.md §Repository Architecture section as template. Draft `.omo/drafts/standalone-repo-setup.md`. Sync commands from todo 10.
  Acceptance criteria (agent-executable):
    - AGENTS.md contains `## Repository Architecture` section header
    - Section mentions `private` and `public` remotes, `master` and `public` branches
    - Section lists `/repo-sync`, `/repo-sync check`, `/repo-sync status` commands
    - Section states private files: MEMORY.md, progress_docs/, .kilo/, .omo/, .codegraph/
    - Section does NOT mention `useful_repos/`
  QA scenarios:
    - Happy: Insert section → grep AGENTS.md for all required keywords → zero matches for useful_repos. Evidence: `.omo/evidence/task-11-standalone-repo-setup.txt`
  Commit: Y | docs(repo): document dual-remote Repository Architecture in AGENTS.md

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit: Every todo (1-11) completed, all acceptance criteria met, all evidence files exist under `.omo/evidence/` (11 files: task-1 through task-11)
- [ ] F2. Code quality review: Root `.gitignore` + 3 sub-project `.gitignore` + `.gitattributes` verified. `whitelist.txt` cross-referenced with `git ls-tree public`. Sync agent exclusion list matches todo 6's `rm --cached` list. No `useful_repos/` in any tracked file or exclusion list.
- [ ] F3. Real manual QA: `git clone` private remote to temp dir → verify MEMORY.md present, progress_docs/ present, full source. `git clone --branch public` public remote to temp dir → verify no MEMORY.md, no progress_docs/, no .kilo/, no .omo/, no useful_repos/. Both clones: `uv run pytest` passes for root + all 3 sub-projects.
- [ ] F4. Scope fidelity: C:\Dev git state unchanged (still zero commits, no remotes). No `.git` created in tscg-py/, token-saver-mem/, contextslim-py/. No files deleted from disk. No directories moved/renamed. `.gitignore` does NOT gitignore private files (MEMORY.md, progress_docs/).

## Commit strategy
| Todo | Commit? | Message |
|------|---------|---------|
| 1 | Y | `feat(repo): initialize standalone git repo for token-saver-meta` |
| 2 | Y | `chore(repo): add comprehensive .gitignore with sub-project coverage` |
| 3 | Y | `chore(repo): add .gitignore files to sub-projects` |
| 4 | Y | `chore(repo): add .gitattributes for cross-platform line endings` |
| 5 | Y | `docs(repo): add Apache-2.0 LICENSE, README.md, and root license field` |
| 6 | N | (committed within branch creation: `curate: remove private files for public mirror`) |
| 7 | Y | `chore(repo): add whitelist.txt for public mirror curation` |
| 8 | N | (remote operations, no file changes) |
| 9 | Y | `feat(repo): add repo-syncer agent for dual-repo sync workflow` |
| 10 | Y | `feat(repo): add repo-sync slash command with check/status/sync` |
| 11 | Y | `docs(repo): document dual-remote Repository Architecture in AGENTS.md` |

Execution order within Wave 1: Todos 2,3,4,5 run in parallel FIRST. Todo 1's `git add .` + `git commit` runs AFTER 2-5 complete, ensuring `.gitignore` and all new files exist before the initial commit. The dependency matrix now correctly reflects this: todo 1 depends on todos 2,3,4,5.

## Success criteria
1. `git -C C:\Dev\projects\token-saver-meta remote -v` shows `private` and `public`
2. `git -C C:\Dev\projects\token-saver-meta branch -a` shows `master` and `public`
3. `git ls-files | grep -E '\.venv/\|\.pytest_cache/\|useful_repos'` returns empty (no build artifacts or cloned repos tracked)
4. `Select-String -Path "pyproject.toml","tscg-py\pyproject.toml","token-saver-mem\pyproject.toml","contextslim-py\pyproject.toml" -Pattern "Apache-2.0"` returns 4 matches (root + 3 sub-projects, PowerShell-native)
5. Private remote has `refs/heads/master` with full source (MEMORY.md, progress_docs/ present)
6. Public remote has `refs/heads/public` ONLY — no master/main, no private files, no useful_repos/
7. `whitelist.txt` lists all public paths, cross-verified against public branch `ls-tree`
8. `/repo-sync` command invokes sync agent correctly
9. C:\Dev git state unchanged (zero commits, no remotes, no new .git files outside token-saver-meta)
