---
type: phase
phase: "10"
name: "Testing & Verification"
status: pending
depends_on: ["09"]
---

# Phase 10: Testing & Verification

## Overview

Benchmark the full stack against a standard task, measure individual and combined savings, and test across platforms and agents.

## Tasks

| Priority | # | Task | Description | LOC |
|----------|---|------|-------------|-----|
| **P0** | P10-1 | Standard benchmark task | Define "add a CRUD endpoint" benchmark for savings measurement | 50 |
| **P0** | P10-2 | Baseline measurement | Measure token usage without any tools | 30 |
| **P0** | P10-3 | Individual tool measurement | Measure each core tool's savings on benchmark | 80 |
| **P0** | P10-4 | Combined measurement | Measure full stack savings on benchmark | 40 |
| **P1** | P10-5 | Cross-platform testing | Test on Windows, macOS, Linux | 60 |
| **P1** | P10-6 | Cross-agent testing | Test with Claude Code, Cursor, OpenCode, Copilot | 60 |
| **P2** | P10-7 | Long-session testing | Multi-hour sessions with compaction events | 50 |

**Total: 7 tasks, ~370 LOC, ~3 new files.**
