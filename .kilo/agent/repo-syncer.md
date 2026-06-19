# repo-syncer Agent

Safely syncs the private `master` branch to the public `public` branch for the curated public mirror.

## Workflow

1. **Verify remotes**: Confirm `private` and `public` remotes are configured
2. **Checkout public**: `git checkout public`
3. **Merge master**: `git merge master` — bring all private branch changes in
4. **Safety check**: Verify NO private files exist on public branch after merge:
   - `git ls-tree --name-only HEAD | grep -E "MEMORY\.md|kilo\.json|opencode\.jsonc|token-saver-meta\.md|progress_docs/|\.kilo/|\.omo/|\.codegraph/"` must return empty
5. **Checkout master**: `git checkout master`
6. **Push public**: `git push public public`

## Private Files (must never appear on public branch)

- `MEMORY.md` — Agent handover state
- `kilo.json` — Kilo platform config
- `opencode.jsonc` — OpenCode config
- `token-saver-meta.md` — Brainstorm doc
- `.kilo/` — Agent definitions
- `.omo/` — Plan artifacts
- `.codegraph/` — Local codegraph index
- `progress_docs/` — Handover notes, session logs

## Emergency: If private files appear on public remote

```bash
git checkout public
git rm --cached -r <leaked-file-or-dir>
git commit -m "emergency: remove leaked private files"
git push public public
```
Then review why the safety check failed.
