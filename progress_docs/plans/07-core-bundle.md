---
type: phase
phase: "07"
name: "Core Bundle Implementation"
status: pending
depends_on: ["06"]
blocks: ["08"]
sub_phases:
  - name: "Installer Foundation"
    status: pending
  - name: "Platform Detection & Config"
    status: pending
  - name: "Tool Integration"
    status: pending
  - name: "Dashboard Scaffold"
    status: pending
---

# Phase 07: Core Bundle Implementation

## Overview

Build the unified installer that auto-detects the user's platform and sets up all 10 core tools with zero configuration. Foundation code from `useful-repos/gitnexus_CGC_combo/`.

## Foundation Reference

- `useful-repos/gitnexus_CGC_combo/src/config_gen.py` — MCP config generation
- `useful-repos/gitnexus_CGC_combo/platforms/matrix.json` — tool matrix (extend with new tools)
- `useful-repos/gitnexus_CGC_combo/` — full installer pattern

## Tasks

| Priority | # | Task | Description | LOC |
|----------|---|------|-------------|-----|
| **P0** | P07-1 | Create installer scaffold | Python-based unified installer (inherit from gitnexus_CGC_combo) | 150 |
| **P0** | P07-2 | Platform detection | Filesystem marker scanning (from combo's config_gen.py) | 80 |
| **P0** | P07-3 | MCP config generation | Multi-format JSON generation (from combo's matrix.json) | 120 |
| **P0** | P07-4 | GitNexus + CGC integration | Copy existing combo setup logic | 60 |
| **P0** | P07-5 | RTK integration | Auto-detect + `rtk init -g` hooks | 50 |
| **P0** | P07-6 | codesight integration | Auto-run `npx codesight` on project | 40 |
| **P0** | P07-7 | SKILL.md bundling | Bundle caveman + LG-token-saver + kevin-copilot skills | 90 |
| **P0** | P07-8 | AGENTS.md injection | Token-saving protocol injection (from combo's Phase 6) | 100 |
| **P1** | P07-9 | ContextSlimAI integration | Run `contextslim init` for rules generation | 40 |
| **P1** | P07-10 | Repomix integration | Auto-run `npx repomix` on first setup | 30 |
| **P1** | P07-11 | Dashboard scaffold | Status page showing tool health and savings | 150 |

**Total: 11 tasks, ~910 LOC, ~9 new files.**
