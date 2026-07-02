# Token Saver Meta

> **"Token Saving for the Masses"**

[![npm](https://img.shields.io/npm/v/token-saver-meta?color=blue)](https://www.npmjs.com/package/token-saver-meta)
[![PyPI](https://img.shields.io/pypi/v/token-saver-meta?color=blue)](https://pypi.org/project/token-saver-meta)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-18%20AI%20agents-brightgreen)](#multi-platform-support)
[![npm downloads](https://img.shields.io/npm/dm/token-saver-meta)](https://www.npmjs.com/package/token-saver-meta)

![divider](https://readme-svg-wave-divider-generator.vercel.app/wave?type=sine&width=1200&height=100&amplitude=20&frequency=2&layers=2&color_top=1a1a2e&color_bottom=16213e&opacity=1&flip=false&gradient=false&mirror=false&animate=false)

A meta-package that bundles token-saving tools across ALL layers of LLM token consumption — with zero configuration.

## Why Token Saver Meta?

AI coding agents spend **40–60% of their token budget** reading files and processing verbose output — not solving problems. Token Saver Meta installs a full stack of tools that slash consumption at every layer: agent behavior, code exploration, shell output, and tool schemas. No config. One install. All platforms.

![divider](https://readme-svg-wave-divider-generator.vercel.app/wave?type=sine&width=1200&height=100&amplitude=20&frequency=2&layers=2&color_top=1a1a2e&color_bottom=16213e&opacity=1&flip=false&gradient=false&mirror=false&animate=false)

## Architecture

Hybrid across 4 layers:

```mermaid
---
config:
  theme: neutral
  htmlLabels: false
---
graph TB
    subgraph LAYER4 [Layer 4 — Power Tools • One-click enable]
        L4["`Schema compression · Cross-session memory\nPrompt optimization · Skill tuning\n<b>~62% savings on tool schemas</b>`"]
    end
    subgraph LAYER3 [Layer 3 — Output Compression • Auto-install]
        L3["`Shell filtering · CLI optimization\n<b>~70% savings on shell output</b>`"]
    end
    subgraph LAYER2 [Layer 2 — Code Intelligence • Auto-install]
        L2["`Code graph queries · Context mapping\nRepo packing\n<b>~85% savings on file exploration</b>`"]
    end
    subgraph LAYER1 [Layer 1 — Agent Behavior • Instant, zero config]
        L1["`Prose terseness · Code minimalism\nOperational efficiency · Structured output\n<b>~40% savings on agent output</b>`"]
    end
    L1 --> L2 --> L3 --> L4

    style LAYER1 fill:#1a1a2e,stroke:#0f3460,color:#e0e0e0
    style LAYER2 fill:#16213e,stroke:#0f3460,color:#e0e0e0
    style LAYER3 fill:#0f3460,stroke:#533483,color:#e0e0e0
    style LAYER4 fill:#533483,stroke:#0f3460,color:#e0e0e0
    style L1 fill:#1a1a2e,stroke:#0f3460,color:#e0e0e0
    style L2 fill:#16213e,stroke:#0f3460,color:#e0e0e0
    style L3 fill:#0f3460,stroke:#533483,color:#e0e0e0
    style L4 fill:#533483,stroke:#0f3460,color:#e0e0e0
```

| Layer | Capabilities | Install |
|-------|-------------|---------|
| **Agent Behavior** | Prose terseness, code minimalism, operational efficiency, structured output | Instant, zero config |
| **Code Intelligence** | Smart navigation, context mapping, repo packing | Auto-install |
| **Output Compression** | Shell filtering, CLI optimization | Auto-install |
| **Power Tools** | Schema compression, cross-session memory, prompt optimization, skill tuning | One-click enable |

Covers all 7 token consumption types: exploration, shell output, agent output, prompt input, repeated knowledge, tool schemas, and instructions.

![divider](https://readme-svg-wave-divider-generator.vercel.app/wave?type=sine&width=1200&height=100&amplitude=20&frequency=2&layers=2&color_top=1a1a2e&color_bottom=16213e&opacity=1&flip=false&gradient=false&mirror=false&animate=false)

## Quick Start

```bash
# npm
npx token-saver-meta

# Python
uvx token-saver-meta

# curl (single command, no package manager needed)
curl -fsSL https://raw.githubusercontent.com/Im-Busy/token-saver-meta/main/install.sh | sh
```

Full architecture: [docs/architecture-v2.md](docs/architecture-v2.md)

## Multi-Platform Support

Supports 18 AI coding platforms out of the box:

**Kilo · Claude Code · Codex · Cursor · Cline · Roo Code · Continue.dev · OpenCode · GitHub Copilot · Windsurf · Augment · FactoryAI · Gemini · Hermes · Kiro · Mastra · Pi**

## License

Apache-2.0
