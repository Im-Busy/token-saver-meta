---
type: phase
phase: "08"
name: "Optional Module Integration"
status: pending
depends_on: ["07"]
blocks: ["09"]
---

# Phase 08: Optional Module Integration

## Overview

Integrate 8 optional tools as one-click enable modules. Each gets MCP config + AGENTS.md rules. No shell hook conflicts (lean-ctx shell hook disabled per conflict resolution).

## Tasks

| Priority | # | Task | Description | LOC |
|----------|---|------|-------------|-----|
| **P1** | P08-1 | TSCG MCP proxy | Drop-in `@tscg/mcp-proxy` for schema compression | 50 |
| **P1** | P08-2 | lean-ctx integration | MCP config + AGENTS.md rules (shell hook disabled) | 40 |
| **P1** | P08-3 | LLMLingua GPU detection | Auto-detect GPU, advise user, optional install | 60 |
| **P2** | P08-4 | codex-agent-mem integration | MCP config for continuity packs | 30 |
| **P2** | P08-5 | Loom integration | MCP config for persistent symbol index | 30 |
| **P2** | P08-6 | Deblank integration | REST API wrapper for whitespace stripping | 50 |
| **P2** | P08-7 | toon integration | Serialization transform module | 40 |
| **P2** | P08-8 | orchestkit skills extraction | Package universal skills as platform-agnostic SKILL.md files | 80 |

**Total: 8 tasks, ~380 LOC, ~8 new files.**
