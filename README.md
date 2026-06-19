# Token Saver Meta

> **"Token Saving for the Masses"**

A meta-package that bundles token-saving tools across ALL layers of LLM token consumption — with zero configuration.

## Architecture

Hybrid across 4 layers:

| Layer | Tools | Mechanism |
|-------|-------|-----------|
| **Base** | caveman, ponytail, LG-token-saver, kevin-copilot | SKILL.md text (instant, zero deps) |
| **Intelligence** | CGC/codegraph, codesight, Repomix | Auto-install via npx |
| **Compression** | RTK, ContextSlimAI | Binary + CLI wrappers |
| **Optional** | TSCG, Unified T5 Memory, LLMLingua-2, SkillOpt, GitNexus | One-click enable |

Covers all 7 token types (T1-T7): exploration, shell output, agent output, prompt input, repeated knowledge, tool schemas, and instructions.

## Quick Start

```bash
# npm
npx create-token-saver

# Python
uvx token-saver-meta setup
```

Full architecture: [docs/architecture-v2.md](docs/architecture-v2.md)

## License

Apache-2.0
