# Publishing Strategy

## Channels

| Channel | Package | Command | URL |
|---------|---------|---------|-----|
| npm | `token-saver-meta` | `npx token-saver-meta` | `npmjs.com/package/token-saver-meta` |
| PyPI | `token-saver-meta` | `pip install token-saver-meta` | `pypi.org/project/token-saver-meta` |

The PyPI package bundles 3 sub-packages as vendored code: `tscg`, `token-saver-mem`, `contextslim`. These are NOT independently published — they ship inside `token-saver-meta`.

## Publish Order

| Step | Package | Channel | Command |
|------|---------|---------|---------|
| 1 | token-saver-meta | PyPI | `uv build && uv publish` |
| 2 | token-saver-meta | npm | `npm publish --access public` |

Steps 1 and 2 can run in parallel.

## OIDC Trusted Publishing

### PyPI Setup

1. Go to `pypi.org/manage/project/token-saver-meta/settings/publishing`
2. Add publisher: GitHub → owner `Im-Busy`, repo `token-saver-meta-private`, workflow `publish-pypi.yml`
3. Environment: leave blank (default)

### npm Setup

1. Go to `npmjs.com/settings/Im-Busy/tokens`
2. Create an Automation token with read+write access
3. Add to GitHub: repo Settings → Secrets → `NPM_TOKEN`

## Manual Publish (Fallback)

```bash
# PyPI
uv build && uv publish

# npm
npm publish --access public
```

## Dual-Repo Notes

- CI/CD workflows (`.github/workflows/`) live on **private** repo (`token-saver-meta-private`, `master` branch)
- The public mirror (`token-saver-meta`, `public` branch) receives workflows via sync but won't activate without OIDC config
- Secrets (`NPM_TOKEN`, OIDC trust) are configured on the **private** repo only
- Publishing always runs from the private repo's `master` branch
