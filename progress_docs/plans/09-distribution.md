---
type: phase
phase: "09"
name: "Distribution & Packaging"
status: pending
depends_on: ["07", "08"]
blocks: ["10"]
---

# Phase 09: Distribution & Packaging

## Overview

Package token-saver-meta for all major distribution channels: npm (npx), Python (uvx/pip), VS Code extension, and optionally a Tauri desktop app.

## Tasks

| Priority | # | Task | Description | LOC |
|----------|---|------|-------------|-----|
| **P0** | P09-1 | `npx create-token-saver` | npm starter (follow create-react-app pattern) | 120 |
| **P0** | P09-2 | `uvx token-saver-meta setup` | Python distribution (follow combo's uvx pattern) | 100 |
| **P1** | P09-3 | PyPI package | `pip install token-saver-meta` | 60 |
| **P1** | P09-4 | GitHub repo | Public with README, docs, getting started guide | 80 |
| **P2** | P09-5 | VS Code extension | Status bar + one-click setup | 150 |
| **P2** | P09-6 | Desktop app (Tauri) | GUI installer for non-technical users | 500 |

**Total: 6 tasks, ~1010 LOC, ~6 new files.**
