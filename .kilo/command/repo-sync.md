# repo-sync Command

Slash command for dual-repo sync management.

## Usage

### Full Sync
```
/repo-sync
```
Invokes the `repo-syncer` agent: merge `master` → `public` → safety check → push.

### Safety Check Only
```
/repo-sync check
```
Runs the safety verification without pushing: checks `public` branch for any private files.

### Status
```
/repo-sync status
```
Shows current branch, remote configuration, and last sync state.

## Examples

```
/repo-sync           # Full sync: merge + check + push
/repo-sync check     # Verify no private files on public branch
/repo-sync status    # Show current state
```
