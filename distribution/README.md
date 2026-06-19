# Distribution Channels — for AI Coding Agents

Token Saver Meta distributes the token-saving protocol across all major AI coding agent platforms.

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/Im-Busy/token-saver-meta/main/install.sh | sh
```

Or install manually:
```bash
# npm
npx token-saver-meta@latest

# Python / uv
uvx token-saver-meta
```

## Per-Platform Files

Copy the appropriate file to your project root. The content is identical — only the file path matters for each tool's discovery mechanism.

| AI Coding Tool | File to place | Discovery |
|---------------|---------------|-----------|
| **AGENTS.md-compatible** (60+ tools) | `distribution/agnostic/AGENTS.md` → project root `AGENTS.md` | Auto-loaded at session start |
| **Claude Code** | `distribution/claude-code/CLAUDE.md` → project root `CLAUDE.md` | Auto-loaded + symlink to AGENTS.md |
| **Cursor** | `distribution/cursor/.cursor/rules/token-saver.md` → `.cursor/rules/token-saver.md` | Cursor rules directory |
| **GitHub Copilot** | `distribution/copilot/.github/copilot-instructions.md` → `.github/copilot-instructions.md` | Copilot instructions path |
| **Windsurf** | `distribution/windsurf/.windsurfrules` → `.windsurfrules` | Windsurf rules file |
| **OpenCode** | `distribution/opencode/AGENTS.md` → project root `AGENTS.md` | OpenCode AGENTS.md |

## What's Included

All files contain the **Token Saving Protocol** — 28 rules merging caveman (prose terseness), ponytail (YAGNI code minimalism), LG-token-saver (operational efficiency), and kevin-copilot (structured terseness).

The protocol reduces token consumption by ~40% on agent output (T3) and agent instructions (T7). Active every response. No mode switching required.

## Canonical Source

`templates/agents_md_section.md` — the authoritative copy. All distribution files are derived from this template.
