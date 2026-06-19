# Tool Assumptions — Phase 07 Core Bundle
> Generated 2026-06-14
> Each tool's CLI interface, platform support, and source paths validated BEFORE implementation.

## codesight
- **Type**: one-shot CLI (NOT an MCP server)
- **Evidence**: .omo/evidence/task-00-codesight-help.txt
- **Command**: `npx codesight [options] [directory]`
- **Options**: `-o/--output <dir>` (default: .codesight), `-d/--depth`, `--wiki`, `--init`, `--watch`, `--hook`, `--html`
- **Output**: CODESIGHT.md + .codesight/ directory with wiki/knowledge base
- **--mcp flag exists?**: No — confirmed. No server mode. Pure one-shot CLI.

## repomix
- **Type**: one-shot CLI (NOT an MCP server)
- **Evidence**: .omo/evidence/task-00-repomix-help.txt
- **Command**: `npx repomix [options] [directories...]`
- **Output**: repomix-output.txt (default) or via --stdout
- **--mcp flag exists?**: No — confirmed. No server mode.

## RTK
- **GitHub repo**: `https://github.com/rtk-ai/rtk` (NOT rtk-lang/rtk)
- **Windows binary**: No — no Windows target in releases (macOS Intel + ARM, Linux x86_64 + aarch64 only)
- **Homebrew**: brew install rtk (macOS)
- **Quick install (Linux/macOS)**: `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`
- **Cargo (cross-platform)**: `cargo install --git https://github.com/rtk-ai/rtk`
- **Fallback strategy**: Binary download (macOS/Linux) → cargo install (any platform with Rust) → skip with warning
- **Evidence**: .omo/evidence/task-00-rtk-releases.json (404 — repo is rtk-ai/rtk, not rtk-lang/rtk)

## ContextSlimAI
- **CLI interface**: npm package `contextslim` NOT FOUND (404 from registry.npmjs.org)
- **init command**: Not available via npx
- **Notes**: The source repo at `useful-repos/ContextSlimAI/` has TypeScript source. May need alternative install (e.g., clone + build, or the package name is different). **TODO: verify package name (contextslim vs context-slim vs contextslim-ai)**.
- **Evidence**: .omo/evidence/task-00-contextslim.txt

## caveman
- **Core SKILL.md path**: `useful-repos/caveman/skills/caveman/SKILL.md`
- **Claims**: ~75% token reduction by ultra-terse communication style
- **Supports**: levels (lite, full, ultra, wenyan variants)
- **Notes**: Only bundle `skills/caveman/SKILL.md` — NOT the 7 additional variant SKILL.md files
- **Evidence**: .omo/evidence/task-00-caveman-paths.txt

## kevin-copilot
- **copilot-instructions.md path**: `useful-repos/kevin-copilot/.github/copilot-instructions.md` — project conventions, NOT token-saving
- **unslop/SKILL.md path**: `useful-repos/kevin-copilot/.github/skills/unslop/SKILL.md`
- **Notes**: The copilot-instructions.md is about project workflows (ATV Starter Kit), not token-saving. The primary token-saving value is toon (TOON format) and unslop (clean instructions). Bundle: `.github/copilot-instructions.md` + `.github/skills/unslop/SKILL.md`.
- **Evidence**: .omo/evidence/task-00-kevin-paths.txt

## LG-token-saver
- **SKILL.md exists**: YES
- **Path**: `useful-repos/LG-token-saver/SKILL.md`
- **Claims**: 87% token savings, 8 rules, 6 months production verified
- **Evidence**: .omo/evidence/task-00-lg.txt