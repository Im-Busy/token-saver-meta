# Publishing Strategy

## Channels

| Channel | Package | Command | URL |
|---------|---------|---------|-----|
| npm | `create-token-saver` | `npx create-token-saver` | `npmjs.com/package/create-token-saver` |
| PyPI | `tscg` | `pip install tscg` | `pypi.org/project/tscg` |
| PyPI | `token-saver-mem` | `pip install token-saver-mem` | `pypi.org/project/token-saver-mem` |
| PyPI | `contextslim` | `pip install contextslim` | `pypi.org/project/contextslim` |
| PyPI | `token-saver-meta` | `pip install token-saver-meta` | `pypi.org/project/token-saver-meta` |

## Publish Order

| Step | Package | Channel | Command |
|------|---------|---------|---------|
| 1a | tscg | PyPI | `cd tscg-py && uv build && uv publish` |
| 1b | token-saver-mem | PyPI | `cd token-saver-mem && uv build && uv publish` |
| 1c | contextslim | PyPI | `cd contextslim-py && uv build && uv publish` |
| 2 | token-saver-meta | PyPI | `uv build && uv publish` |
| 3 | create-token-saver | npm | `npm publish --access public` |

Steps 1a, 1b, 1c can run in parallel. Steps 2 and 3 can run in parallel after 1a-1c complete.

## OIDC Trusted Publishing

### PyPI Setup (per package)

1. Go to `pypi.org/manage/project/<name>/settings/publishing`
2. Add publisher: GitHub → owner `Im-Busy`, repo `token-saver-meta-private`, workflow `publish-pypi.yml`
3. Environment: leave blank (default)
4. Repeat for all 4 packages: `tscg`, `token-saver-mem`, `contextslim`, `token-saver-meta`

### npm Setup

1. Go to `npmjs.com/settings/Im-Busy/tokens`
2. Create an Automation token with read+write access
3. Add to GitHub: repo Settings → Secrets → `NPM_TOKEN`

## Manual Publish (Fallback)

```bash
# PyPI — leaf packages (parallel)
cd tscg-py && uv build && uv publish
cd token-saver-mem && uv build && uv publish
cd contextslim-py && uv build && uv publish

# PyPI — meta package
cd .. && uv build && uv publish

# npm
npm publish --access public
```

## Dual-Repo Notes

- CI/CD workflows (`.github/workflows/`) live on **private** repo (`token-saver-meta-private`, `master` branch)
- The public mirror (`token-saver-meta`, `public` branch) receives workflows via sync but won't activate without OIDC config
- Secrets (`NPM_TOKEN`, OIDC trust) are configured on the **private** repo only
- Publishing always runs from the private repo's `master` branch
