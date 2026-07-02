# Token Saver Meta — Architecture v2

> **Status:** AUTHORITATIVE — supersedes all previous architecture documents.
> **Created:** 2026-06-18
> **Based on:** 63 sources, 46 tools, 39 insights, 24 synergies, 4-agent research + Oracle evaluation
> **Replaces:** `max-coexistence.md`, Phase 07 handover architecture, MEMORY.md architecture section

> **⚠️ Note:** GitNexus references have been replaced by CBM. The code intelligence layer now uses CBM (codebase-memory-mcp) — MIT license, pure C, 158 languages. Historical decision log entries and Acknowledgments retain GitNexus for attribution.

---

# PART 1: SYNERGY ANALYSIS

## How Tools Compound Across Token Types

Token Saver Meta's power comes from the **independent compounding** of tools across 7 independent token types. Tools on different types NEVER conflict — each shrinks a different bucket of the total session token budget.

### T1 — Exploration (40-200K tokens/session)

**The heaviest token consumer.** Agents spend 40-200K tokens reading files to understand a codebase. T1 tools replace file reads with graph queries.

| Tool | Mechanism | Savings | When Active |
|------|-----------|:-------:|-------------|
| **codesight** | Static pre-compiled context map | 7x-91x | First session — read CODESIGHT.md once |
| **CBM** (codebase-memory-mcp) | Impact analysis graph (MCP, pure C) | ~90% | "What breaks if I change X?" |
| **CGC** | SQLite+FTS5 graph queries (MCP, npx) | ~85% | "How is X structured?" |
| **Repomix** | Repo packing to single file | ~70% | Bulk load for new sessions |
| **Loom** (optional) | Persistent symbol cache (SQLite) | 51x-1507x | Sessions 2+ — compound effect |
| **codex-agent-mem** (optional) | Continuity packs with hash caching | ~95% | Repeated context across sessions |

**Synergy chain:** codesight (breadth map) → Loom / CBM graph engine (depth queries) → codex-agent-mem (cross-session memory). Each level compounds: codesight eliminates 90% of initial reads → agent has context budget left → Loom caches remaining queries → session 2 reads zero files.

**Gap:** Without Loom/codex-agent-mem, sessions 2+ re-read the same files. These are optional modules in v1.

### T2 — Shell Output (15-80K tokens/session)

CLI commands (git, tests, builds, npm install) produce verbose output. T2 tools compress or replace them.

| Tool | Mechanism | Savings | Overhead |
|------|-----------|:-------:|----------|
| **RTK** (core) | PreToolUse hook + 60+ regex filters | 60-90% | ~10ms per command |
| **ContextSlimAI** (core) | 40+ slim command replacements | ~50% | Replaces `grep` → `contextslim grep` |
| **opentoken** (defer v2) | 35-stage compression pipeline | 97% | Bun runtime needed |
| **omni** (defer v2) | Adaptive semantic compression | 97% | Rust binary |
| **lowfat** (defer v2) | 3-level Rust filter | ~40% | Complements RTK |

**Synergy chain:** RTK (pre-execution rewrite, transparent) + ContextSlimAI (command replacement for uncovered commands) = 100% command coverage. RTK rewrites commands before execution → produces less output. ContextSlimAI replaces commands RTK doesn't cover. No blind spots.

**The only conflict:** RTK shell hook vs lean-ctx shell hook (both intercept shell commands). Resolution: disable lean-ctx shell hook. Keep lean-ctx MCP tools (cached reads, delta, dedup).

### T3 — Agent Output (10-60K tokens/session)

What the agent says — verbose responses, explanations, filler text. T3 tools use three independent compression axes.

| Tool | Axis | Mechanism | Savings |
|------|------|-----------|:-------:|
| **caveman** (core) | **Prose style** | Terse language, drop filler, keep accuracy | ~75% |
| **ponytail** (core) | **Code minimalism** | YAGNI ladder: stdlib→native→dep→one-liner→minimal | ~54% LOC, ~22% tokens |
| **LG-token-saver** (core) | **Operations** | 8 rules: parallelism, dedup, compaction | ~87% claimed |
| **kevin-copilot** (core) | **Structure** | 4 modes, CI-gated evals | 66-89% |

**Synergy:** Three-Axis Agent Compression (S07): caveman compresses SPEECH, ponytail compresses CODE, LG-token-saver compresses OPERATIONS. These are multiplicative within T3 — an agent that speaks tersely AND writes minimally AND operates efficiently saves ~90-95% on output tokens.

**Zero conflict:** All four are SKILL.md files. They instruct the agent differently. caveman = "be terse", ponytail = "use stdlib first", LG-token-saver = "never repeat yourself". No mechanism overlap.

### T4 — Prompt Input (100% of every request)

What's sent to the LLM API. Currently single-coverage in core — needs optional modules for defense-in-depth.

| Tool | Mechanism | Savings | Blockers |
|------|-----------|:-------:|----------|
| **LLMLingua-2** (optional) | ML-based perplexity token removal | 5-20x | Needs GPU (auto-detect) |
| **Deblank** (defer v2) | Bidirectional formatting strip | ~34% C, ~9% Python | REST API wrapper needed |
| **racs** (defer v2) | Provider cache-breakpoint planning | 88% cache hits | Library, needs integration |
| **toon** (defer v2) | Compact data serialization | ~40% | Drop-in JSON→TOON converter |

**Current weakness:** T4 has zero core tools. All T4 tools are optional or deferred. This is the #1 gap in v1.

### T5 — Repeated Knowledge (20-50K tokens/session)

Information re-loaded every session — project structure, design patterns, conventions.

| Tool | Mechanism | Savings |
|------|-----------|:-------:|
| **codex-agent-mem** (optional) | Continuity packs, hash caching | ~95% |
| **Loom** (optional) | Persistent symbol index, delta tracking | 51x-1507x/session |

**Synergy (S14):** Hash caching + Delta tracking = Pay Only for Changes. Day 2: 90% unchanged → 90% retrieval costs eliminated. Day 10: 95% eliminated. Each day costs LESS than the previous.

### T6 — Tool Schema (~3K tokens/server × N)

MCP tool definitions sent in every API request. With 5+ MCP servers, schema overhead is 15K+ tokens per request.

| Tool | Mechanism | Savings |
|------|-----------|:-------:|
| **TSCG** (optional) | Schema compiler + MCP proxy | 50-72% |

**Current weakness:** Single tool. MetaMCP (collapse N servers → ~1,300 constant tokens) is not bundled — it's a pattern to adopt, not cloned.

### T7 — Instructions (5-30K tokens/turn)

AGENTS.md, rules, skills loaded every turn. This is the cheapest win — SKILL.md files cost nothing to install.

| Tool | Mechanism | Savings |
|------|-----------|:-------:|
| **caveman** | Behavioral: terse output | ~75% |
| **LG-token-saver** | Behavioral: 8 operational rules | ~87% |
| **kevin-copilot** | Terseness instruction injector | 66-89% |
| **ponytail** | YAGNI ladder enforcement | ~22% tokens |
| **SkillOpt** (optional) | ML-optimized skill documents | 300-2K token artifacts |

**Synergy (S08):** Tiered loading — split AGENTS.md into core loader (4K) + on-demand sections. Light mode: core only (4K). Full mode: all sections (10-15K). Simple queries avoid paying for full instructions.

### Cross-Type Synergies (The Multiplier)

Tools don't just save within their type — they amplify each other across types:

- **T1 → T2:** codesight eliminates 90% of file reads → agent has more context budget → T2 compression (RTK) matters more
- **T1 → T5:** CBM graph is cached across sessions via Loom → "what breaks?" costs zero tokens on session 2+
- **T3 → T7:** SKILL.md instructions (T7) produce terser output (T3) → instructions pay for themselves in output savings
- **T1 → T6:** Fewer MCP tool calls (T1 tools are more efficient) → fewer schema tokens burned per request (T6)

**The Master Synergy (S22):** Insight Registry (what we know) + BESTS Leaderboard (which tools) + Synergy Map (how they combine) = complete decision support for any agent or human designing the stack.

---

# PART 2: MULTIPLE SYSTEM ARCHITECTURES

## Option A: "Maximal Bundle — Install Everything" (18 tools)

### Philosophy
Maximum coverage. Install every compatible tool from Tiers S, A, and B. The user gets everything.

### Bundle Composition
**Core (auto-install, 10 tools):** CBM, CGC, RTK, codesight, Repomix, caveman, LG-token-saver, kevin-copilot, ContextSlimAI, ponytail
**Optional (one-click, 8 tools):** TSCG, lean-ctx MCP, LLMLingua-2 (GPU auto-detect), codex-agent-mem, Loom, Deblank, toon, SkillOpt

### Integration Architecture
All 9 MCP servers behind a MetaMCP-style aggregation proxy. RTK via PreToolUse hook. SKILL.md tools merged into AGENTS.md. Library tools (LLMLingua, Deblank) wrapped as MCP servers.

### Installation Architecture
Python-based unified installer extending `gitnexus_CGC_combo/src/config_gen.py`. Platform detection via filesystem markers. Multi-package-manager orchestration (npm + pip + cargo + brew). Per-tool install with error isolation.

### User Experience
`uvx token-saver-meta setup ./` → progress bar → "10/10 tools active." Dashboard shows savings. Everything works.

### Tradeoffs
- **Sacrifices:** Installation simplicity, maintenance simplicity, dependency surface
- **Strengths:** Maximum token savings (~75-80% across T1-T7), 2+ tools per type

---

## Option B: "Minimal Dependency — Node-First" (8 tools)

### Philosophy
Frictionless adoption. Only bundle tools that need nothing or just Node.js — the most ubiquitous runtime.

### Bundle Composition
**Core (8 tools):** CBM (npx), codesight (npx), Repomix (npx), TSCG (npx), ContextSlimAI (npx), caveman (SKILL.md), LG-token-saver (SKILL.md), kevin-copilot (npx)
**Optional (2 tools):** ponytail (SKILL.md), toon (npm)

### Integration Architecture
All MCP servers invoked via npx. No Python, no Rust, no Bun. SKILL.md files copied directly. All tools run from a single package.json.

### Installation Architecture
`npx token-saver-meta` → npm-based installer. Generates MCP config for all tools. Copies SKILL.md files. One `npm install` or `npx` per tool. Works everywhere Node.js works.

### User Experience
`npx token-saver-meta` → "7 of 8 tools installed (ContextSlimAI skipped: Node ≥18 required)" → simple status report.

### Tradeoffs
- **Sacrifices:** Missing RTK (best T2 tool, 60-90%, Rust), missing Python gems (Loom, codex-agent-mem, Deblank, SkillOpt), weak T4/T5 coverage
- **Strengths:** Zero Python/Rust/Bun deps, fast install, easy maintenance, Node.js is everywhere

---

## Option C: "Transparent Experience — SKILL.md & Hooks Only" (6 tools)

### Philosophy
Maximum simplicity. Only tools that require ZERO configuration and ZERO runtime dependencies.

### Bundle Composition
**Core (4 SKILL.md files):** caveman, LG-token-saver, kevin-copilot, ponytail
**Optional (2 simple tools):** RTK (single binary, one hook line), codesight (one npx command, one output file)

### Integration Architecture
All SKILL.md files merged into a single tiered AGENTS.md section. No MCP servers. No config files. No runtime dependencies. RTK is a single binary with one hook line. codesight is one command run once.

### Installation Architecture
`npx token-saver-meta init` → copies one AGENTS.md block. Or just copy-paste from docs. For RTK/codesight: auto-detect and run one command each. Total install time: <5 seconds for base layer.

### User Experience
Copy one file → agent is 40% more token-efficient. No config. No MCP. No updates needed. The base layer IS the product for most users.

### Tradeoffs
- **Sacrifices:** No graph-based T1 tools, no MCP servers, no T4/T5/T6 coverage, savings ceiling ~40% (only T3+T7)
- **Strengths:** Zero deps, instant install, never breaks, works everywhere, 100% transparent, easiest maintenance

---

## Option D: "Hybrid Architecture — Base + Advanced" (14 tools) ⭐ WINNER

### Philosophy
Gradated adoption. Base layer works instantly everywhere (SKILL.md files). Advanced layer adds MCP tools for power users. Users get value in 1 second; full coverage in 60 seconds.

### Bundle Composition
**Base Layer — always active, zero deps (4 tools):**
- caveman — terse output style (~75%)
- LG-token-saver — operational efficiency (~87%)
- kevin-copilot — structured terseness (66-89%)
- ponytail — YAGNI code minimalism (~54% LOC, ~22% tokens)

**Code Intelligence Layer — auto-install, detect platform (3 tools):**
- CBM — impact analysis graph (MCP, sidecar)
- codesight — static context map (one-shot, npx)
- Repomix — repo packing (one-shot, npx) *(added for T1 defense-in-depth per Oracle recommendation)*

**Output Compression Layer — auto-install, detect platform (3 tools):**
- RTK — shell compression (binary, auto-download)
- ContextSlimAI — CLI replacement + rules (npx) *(added for T2 defense-in-depth)*
- CGC — SQLite+FTS5 graph queries (MCP, npx) — Node.js, NOT Python/Neo4j (corrected 2026-06-18)

**Optional Modules — one-click enable (5 tools):**
- TSCG — schema compression (MCP proxy, npm)
- codex-agent-mem — continuity packs (MCP, pip)
- Loom — persistent symbol index (MCP, pip)
- LLMLingua-2 — prompt compression (GPU auto-detect, pip)
- SkillOpt — skill optimization (offline CLI, pip)

**Deferred to v2 (license-restricted or heavy):**
- jcodemunch-mcp (dual-use license) | sdl-mcp (source-available)
- opentoken (Bun runtime) | omni (evaluate vs RTK) | tokensave (evaluate vs CBM)
- trace-mcp (complex) | Deblank (needs REST API wrapper) | toon (serialization only)
- racs (needs API pipeline integration) | lowfat (complements RTK)

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  BASE LAYER (SKILL.md files — zero config, instant)         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  AGENTS.md token-saving section                        │ │
│  │  ├── Rule 1: Terse output (caveman)                    │ │
│  │  ├── Rule 2: Parallel operations (LG-token-saver)       │ │
│  │  ├── Rule 3: Structured responses (kevin-copilot)       │ │
│  │  └── Rule 4: YAGNI ladder (ponytail)                    │ │
│  └───────────────────────────────────────────────────────┘ │
│  Always active. Works with EVERY agent. Zero deps.           │
├─────────────────────────────────────────────────────────────┤
│  INTELLIGENCE LAYER (MCP servers + one-shot tools)          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  CBM MCP ← cbm_sidecar/ MCP server                    │ │
│  │  CGC MCP ← npx codegraph mcp                              │ │
│  │  codesight (one-shot) ← npx codesight                   │ │
│  │  Repomix (one-shot) ← npx repomix                       │ │
│  └───────────────────────────────────────────────────────┘ │
│  Detect platform → generate MCP config → index once          │
├─────────────────────────────────────────────────────────────┤
│  COMPRESSION LAYER (binary + CLI)                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  RTK ← auto-download binary, inject PreToolUse hook     │ │
│  │  ContextSlimAI ← npx contextslim init (generates rules) │ │
│  └───────────────────────────────────────────────────────┘ │
│  Hook injection varies by agent (see per-agent config)       │
├─────────────────────────────────────────────────────────────┤
│  OPTIONAL LAYER (one-click: token-saver enable <tool>)      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  TSCG (MCP proxy) | codex-agent-mem (MCP)              │ │
│  │  Loom (MCP) | LLMLingua-2 (GPU) | SkillOpt (offline)   │ │
│  └───────────────────────────────────────────────────────┘ │
│  Each installs independently. GPU auto-detect for LLMLingua │
└─────────────────────────────────────────────────────────────┘
```

### Installation Architecture

**Three install paths, one destination:**

| Path | Command | For |
|------|---------|-----|
| **Agent (primary)** | "set up token saving" | AI coding tool users — agent reads AGENTS.md, auto-provisions |
| **npx (universal)** | `npx token-saver-meta init` | Copied from Option B — Node.js users, fastest path |
| **uvx (Python)** | `uvx token-saver-meta setup ./` | Python developers, inherited from gitnexus_CGC_combo |

**Install flow:**
```
npx token-saver-meta init
    │
    ├── [Phase 1: Base Layer — instant, always]
    │   └── Copy tiered AGENTS.md block to detected platforms
    │       4 SKILL.md rules merged → one <200-line block
    │       ✅ Active in <1 second. Saves ~40% on T3+T7.
    │
    ├── [Phase 2: Platform Detection — 2 seconds]
    │   ├── Scan filesystem markers → Claude Code, Cursor, OpenCode, Kilo
    │   ├── Detect runtimes: Node.js ✓, Python ✓, uv ✓
    │   └── Determine available tools based on runtimes
    │
    ├── [Phase 3: MCP Tools — 30-60 seconds]
    │   ├── CBM (download binary) → configure MCP sidecar
    │   ├── CGC (npx) → generate MCP config entry
    │   ├── codesight (npx, run once) → generate CODESIGHT.md
    │   ├── Repomix (npx, run once) → generate repomix-output.txt
    │   ├── RTK (binary) → download + inject hook
    │   └── ContextSlimAI (npx, run once) → generate rules + ignore files
    │   Each tool: independent install, failure = warn + continue
    │
    ├── [Phase 4: Index — 30-60 seconds]
    │   ├── CBM index (index codebase)
    │   ├── CGC index
    │   └── codesight generate (if not already)
    │
    └── [Phase 5: Summary]
        └── ✅ Base: 4/4 active  ✅ Intelligence: 4/4  ✅ Compression: 2/2
            ⚠ Optional: 0/5 enabled (token-saver enable <tool>)
            📊 Estimated savings: ~70% across T1-T7
```

**Node-only fallback** (merged from Option B):
When the installer detects NO Python and NO Bun:
- Install ALL available tools (CBM, codesight, Repomix, TSCG, ContextSlimAI)
- Skip CGC (needs Python)
- Skip Python optional modules
- Report: "CGC skipped (Python not found). Install Python for: CGC, Loom, codex-agent-mem, Deblank, SkillOpt."
- Still installs: RTK (Rust binary, can still download), SKILL.md base layer

### User Experience

**Daily use — invisible:**
- Base layer: Agent is naturally terse (SKILL.md rules). User sees shorter responses.
- Intelligence layer: Agent queries graph instead of reading files. User sees faster answers.
- Compression layer: RTK silently compresses CLI output. User sees nothing different.
- Dashboard (optional): `token-saver dashboard` → shows savings retroactively.

**Troubleshooting — clear:**
- `token-saver status` → tool health matrix with ✅/⚠️/❌ per tool
- `token-saver diagnose` → diagnostic report with one-click fixes
- Each error: plain English with source, not stack traces

**Uninstall — exact inverse:**
- `token-saver uninstall --dry-run` → preview what will be removed
- `token-saver uninstall` → remove everything token-saver added
- Per-component: `token-saver uninstall --tool=rtk`
- Clean state guarantee: user's other MCP servers, config, AGENTS.md preserved

### Tradeoffs
- **Sacrifices:** Two-layer mental model (base vs MCP), needs Node.js OR Python for full experience, RTK requires Rust binary download
- **Strengths:** Immediate value (1 second), full coverage (60 seconds), graceful degradation (base always works), clear upgrade path, matches SaaS onboarding patterns

---

# PART 3: RIGOROUS EVALUATION

## Scoring Matrix

| Axis | A: Maximal (18t) | B: Node-Only (8t) | C: SKILL.md (6t) | D: Hybrid (14t) |
|------|:---:|:---:|:---:|:---:|
| **1. Token savings effectiveness** | **10** | 4 | 2 | **8** |
| **2. Ease of installation** | 2 | 8 | **10** | 7 |
| **3. Ease of daily use** | 8 | 7 | **10** | **9** |
| **4. Cross-platform support** | 5 | 9 | **10** | **8** |
| **5. Maintenance burden** | 3 | 8 | **10** | 6 |
| **6. Extensibility** | 7 | 5 | 6 | **9** |
| **7. Error resilience** | 4 | 8 | **10** | **9** |
| **8. User trust** | 6 | 7 | **10** | **8** |
| **9. Implementation complexity** | 3 | 8 | **10** | 6 |
| **10. Total cost (deps/disk)** | 3 | 8 | **10** | 7 |
| **TOTAL** | **51** | **72** | **88** | **77** |

## Axis-by-Axis Reasoning

### 1. Token Savings Effectiveness
- **A (10):** Full coverage. RTK+TSCG+LLMLingua+Loom+codex-agent-mem = all 7 types with 2+ tools. Estimated ~75-80% total savings.
- **B (4):** Lacks T4 (no LLMLingua), weak T5 (no Python tools), missing best T2 (RTK, Rust). Only T1+T3+T7 are strong. ~35-40%.
- **C (2):** Only T3+T7. No T1 (heaviest type at 40-200K), no T2, no T4, no T5, no T6. ~20-25%.
- **D (8):** Strong T1 (CBM+CGC+codesight+Repomix), strong T2 (RTK+ContextSlimAI), strong T3+T7 (4 SKILL.md tools). Missing T4 core, T5 needs optional, T6 needs optional. ~65-70% with base+MCP, ~72% with optional modules.

### 2. Ease of Installation
- **A (2):** 4 ecosystem dependencies (Node+Python+Rust+Bun). Must orchestrate npm+pip+cargo+brew. Complex failure modes. 3-5 minute install.
- **B (8):** One ecosystem (Node.js). npx for everything. 30-60 second install. Works if Node.js installed.
- **C (10):** Copy one file. <1 second. Works everywhere. Zero deps.
- **D (7):** Base layer: <1 second. MCP layer: 30-60 seconds. Two ecosystems (Node.js + Python). Graceful fallback if Python missing. <2 minutes total.

### 3. Ease of Daily Use
- **A (8):** Once installed, everything works. But 18 tools mean more surface area for breakage.
- **B (7):** Simple. But missing tools means agent sometimes falls back to raw file reads.
- **C (10):** Completely transparent. Agent is naturally terse. User notices shorter responses — that's all.
- **D (9):** Base layer transparent. MCP layer transparent. Only difference from C: agent can answer "how does X work?" faster via graph queries.

### 4. Cross-Platform Support
- **A (5):** Rust binaries per-platform (RTK, tokensave, omni). Python GPU detection fragile on Windows. Bun support varies.
- **B (9):** Node.js runs everywhere. All tools are npm packages. Windows/macOS/Linux identical.
- **C (10):** SKILL.md is a text file. Works on every platform, every agent, every editor.
- **D (8):** Base layer: 10. MCP layer: Node.js everywhere, Python almost everywhere. Node-only fallback for Python-missing platforms.

### 5. Maintenance Burden
- **A (3):** 4 ecosystem update cadences. 18 tools to track. Complex inter-tool testing matrix.
- **B (8):** One ecosystem. 8 tools. npm updates handle everything.
- **C (10):** Edit markdown text. No version tracking needed. Changes are instructions, not code.
- **D (6):** Two layers with different cadences. Base layer: quarterly text edits. MCP layer: monthly npm/pip updates.

### 6. Extensibility
- **A (7):** Can add tools from any ecosystem. But the installer gets more complex with each addition.
- **B (5):** Limited to Node ecosystem. Cannot add Python or Rust tools.
- **C (6):** Only SKILL.md-compatible tools. Cannot add MCP servers or binary tools.
- **D (9):** Base layer: add SKILL.md rules. MCP layer: add MCP servers. Optional layer: add any tool type. Clear interfaces for each layer.

### 7. Error Resilience
- **A (4):** Many failure points. One broken Rust build blocks RTK. One broken Python env blocks 6 tools. Complex rollback.
- **B (8):** Single ecosystem. npm failures are well-understood. Clean uninstall.
- **C (10):** Cannot break. It's a text file.
- **D (9):** Base layer: cannot break. MCP layer: per-tool failure isolation. If CBM fails, CGC and codesight still work.

### 8. User Trust
- **A (6):** 18 tools downloading binaries from multiple sources. Opaque. Hard to verify what's running.
- **B (7):** npm packages are somewhat auditable. But still opaque to non-developers.
- **C (10):** SKILL.md is fully visible. User can read every rule. Full transparency.
- **D (8):** Base layer is fully visible (3 user-verifiable SKILL.md rules). MCP tools are standard MCP servers. Dashboard shows exactly what's active.

### 9. Implementation Complexity
- **A (3):** Complex unified installer across 4 ecosystems. Per-platform binary management. GPU detection. Cross-agent hook injection.
- **B (8):** Simple npm installer. npx-based tools. Standard MCP config generation.
- **C (10):** Trivial. Copy a file. Or template a file with project-specific sections.
- **D (6):** Moderate. Two-layer installer. MCP config gen (inherited from gitnexus_CGC_combo). Base layer is trivial. MCP layer is moderate complexity.

### 10. Total Cost
- **A (3):** 4 runtimes. Python GPU deps (8-14GB). Multiple package managers. Large disk footprint.
- **B (8):** One runtime (Node.js). npm packages are small. No GPU requirements.
- **C (10):** Zero runtime deps. Zero disk (it's text in AGENTS.md).
- **D (7):** Two runtimes (Node.js + Python, or just Node.js in fallback). No GPU required for core. GPU only for optional LLMLingua.

## Why C's Higher Score Doesn't Mean C Wins

C scores 88 vs D's 77, but C **fails the core mission**. C covers only T3+T7 — that's 2 of 7 token types. The heaviest token consumers (T1: 40-200K/session, T2: 15-80K/session) are completely unaddressed. C saves ~20-25% of token waste; D saves ~70%. C's score advantage comes entirely from simplicity axes (ease, maintenance, cost) — but simplicity of a product that doesn't solve the problem isn't simplicity, it's incompleteness.

D wins because it achieves 70% savings with acceptable complexity. The gap between "easy but weak" (C) and "moderate but strong" (D) is the product working vs. being a footnote.

---

# PART 4: FINAL RECOMMENDATION

## Winner: Option D — Hybrid Architecture

**Option D is the architecture for Token Saver Meta v1.** It balances maximum token savings with minimal adoption friction, provides immediate value and a clear upgrade path, and handles failure gracefully at every layer.

## Elements Merged INTO Option D from Other Options

### From Option A (Maximal) — 3 elements:
1. **Sophisticated platform detection logic** — Inherited from gitnexus_CGC_combo's `config_gen.py` and `matrix.json`. Filesystem marker scanning, multi-MCP-family format translation, merge-into-existing (never overwrite). Simplified for 2 ecosystems instead of 4.
2. **Per-tool failure isolation** — Each tool installs independently. One failure = warn + continue. Final report shows ✅/❌ per tool. Never "all or nothing."
3. **Defense-in-depth for T1 and T2** — Added Repomix to T1 stack and ContextSlimAI to T2 stack (both Node-only, zero friction). Now T1 has 4 tools (CBM+CGC+codesight+Repomix) and T2 has 2 tools (RTK+ContextSlimAI).

### From Option B (Node-First) — 2 elements:
1. **`npx token-saver-meta` bootstrap** — The primary install command. Copies AGENTS.md base layer + detects platform + installs MCP tools. One command, no clone, no pip. Inherits B's "Node.js everywhere" assumption.
2. **Node-only fallback mode** — When Python is missing, install all Node-based tools and skip Python tools with a clear message. Base layer always works regardless.

### From Option C (SKILL.md Only) — Already absorbed:
D's base layer IS Option C plus ponytail. The philosophy of "make the foundation work everywhere instantly" is the core of D's design. Nothing left to merge.

## Architecture Decisions (DO NOT REVISIT)

| Decision | Rationale |
|----------|-----------|
| Base layer is SKILL.md files only | Works everywhere, instant, never breaks, zero deps |
| MCP layer is Node.js + Python | Covers 9 of 12 MCP tools, acceptable dependency surface |
| RTK is core, not optional | T2 is the 2nd heaviest token type. RTK is 62K stars, 14 integrations. Must be built-in. |
| CGC uses npx (it's Node.js/TypeScript) | CGC is Node.js with SQLite+FTS5, not Python+Neo4j. Corrected 2026-06-18 from earlier architecture docs. |
| TSCG is optional | Schema compression is T6 — lower-waste type. Core covers T1-T3+T7 first. |
| LLMLingua is optional, GPU auto-detect | GPU not universal. Auto-detect + advise. Never auto-install GPU deps. |
| jcodemunch-mcp is v2 (license) | Dual-use license: free personal, commercial for teams. Needs separate distribution path. |
| sdl-mcp is v2 (license) | Source-available (not standard OSI). Review exact terms before bundling. |
| opentoken, omni, tokensave are v2 | Evaluate vs existing tools (RTK, GitNexus). Mature enough to bundle later. |
| Deblank, racs, lowfat are v2 | Need custom wrappers for agent integration. Not drop-in. |

## Token Type Coverage (After Merges)

| Token Type | Core Tools | Optional | Status |
|:----------:|-----------|----------|:------:|
| **T1 — Exploration** | CBM, CGC, codesight, Repomix | Loom, codex-agent-mem | ✅ 4 core + 2 optional |
| **T2 — Shell Output** | RTK, ContextSlimAI | — | ✅ 2 core |
| **T3 — Agent Output** | caveman, ponytail, LG-token-saver, kevin-copilot | — | ✅ 4 core |
| **T4 — Prompt Input** | — | LLMLingua-2 | ⚠️ 0 core, 1 optional |
| **T5 — Repeated Knowledge** | — | codex-agent-mem, Loom | ⚠️ 0 core, 2 optional |
| **T6 — Tool Schema** | — | TSCG | ⚠️ 0 core, 1 optional |
| **T7 — Instructions** | caveman, ponytail, LG-token-saver, kevin-copilot | SkillOpt | ✅ 4 core + 1 optional |

**Status:** T1, T2, T3, T7 have defense-in-depth (2+ tools). T4, T5, T6 are covered by optional modules — the user opts into these for additional savings. This is the correct priority: the heaviest token types (T1+T2 at 55-280K/session) get core coverage. Lower-waste types (T4+T5+T6) get optional coverage.

---

# PART 5: IMPLEMENTATION ROADMAP

## Phase 07: Core Bundle Implementation (v1 MVP)

### P0 Tasks (build first — core experience)

| # | Task | Files | Verification |
|---|------|-------|-------------|
| 1 | **AGENTS.md tiered structure** — Merge 4 SKILL.md tools into one tiered block. Core rules (~3K tokens), on-demand sections. Marker-delimited injection. | `src/agents_md_injector.py`, `templates/agents_md_block.md` | Manual test: copy block, agent outputs are terse + minimal code |
| 2 | **Platform detection + MCP config gen** — Extend `config_gen.py` + `matrix.json` with all 6 MCP tools. Merge-into-existing, idempotent, atomic writes. | `src/config_gen.py`, `platforms/matrix.json` | Test: install → re-install (must be idempotent), uninstall → re-install (must work) |
| 3 | **npx bootstrap entry point** — `npx token-saver-meta init` does: copy AGENTS.md → detect platform → install MCP tools → index → summary. | `src/cli.py`, `package.json` (npm publish) | Test: `npx token-saver-meta init` on clean project → all tools active |
| 4 | **CBM + CGC integration** — Auto-detect, generate MCP config, run analyze/index. Per-tool error isolation. | `src/tools/cbm_tool.py`, `src/tools/cgc_tool.py` | Test: CBM MCP tools respond, CGC MCP tools respond |
| 5 | **RTK integration** — Auto-detect platform, download binary, inject hook. 3 install paths (PreToolUse hook / shell alias / manual). | `src/tools/rtk_tool.py` | Test: `rtk git status` produces compressed output |
| 6 | **codesight + Repomix integration** — Run once, generate output files. Detect staleness on re-run. | `src/tools/codesight_tool.py`, `src/tools/repomix_tool.py` | Test: CODESIGHT.md + repomix-output.txt exist, content valid |
| 7 | **ContextSlimAI integration** — `npx contextslim init`, verify rules + ignore files generated. | `src/tools/contextslim_tool.py` | Test: `.contextslim/rules.md` + optimized `.gitignore` exist |
| 8 | **Per-tool failure isolation** — Each tool installs in try/catch. Failures are logged, remaining tools proceed. Final summary per tool. | `src/installer.py` (modify) | Test: simulate network failure on one tool → others still install |

### P1 Tasks (build next — polish)

| # | Task | Files | Verification |
|---|------|-------|-------------|
| 9 | **Node-only fallback mode** — Detect missing Python, install only Node tools, skip Python tools with clear message. | `src/installer.py` (modify), `src/prerequisites.py` | Test: uninstall Python, run installer → Node tools installed, Python tools warned |
| 10 | **Dashboard scaffold** — `token-saver status` → tool health matrix. `token-saver dashboard` → before/after savings estimate. | `src/dashboard.py` | Test: dashboard shows correct tool states + estimated savings |
| 11 | **Uninstall with dry-run** — `token-saver uninstall --dry-run` → preview. `token-saver uninstall` → remove everything. Per-tool: `--tool=rtk`. | `src/uninstall.py` | Test: install → uninstall → project is exactly as before |
| 12 | **Diagnostic report** — `token-saver diagnose` → check all tools, report status, suggest fixes. | `src/diagnostics.py` | Test: break one tool → diagnose catches it |

### P2 Tasks (defer to Phase 08)

| # | Task |
|---|------|
| 13 | Optional module enabler (`token-saver enable loom` → install + MCP config) |
| 14 | GPU auto-detect for LLMLingua-2 |
| 15 | Cross-agent testing (Claude Code, Cursor, OpenCode, VS Code+Copilot, Kilo) |
| 16 | Savings benchmarking (same task with/without tools → measure actual delta) |
| 17 | VS Code extension (status bar indicator) |

## Phase 08: Optional Module Integration

- TSCG MCP proxy (npm, one-click enable)
- codex-agent-mem (pip, continuity packs)
- Loom (pip, persistent symbol index)
- LLMLingua-2 (pip, GPU auto-detect)
- SkillOpt (pip, offline skill optimization)

## Phase 09: Distribution & Packaging

- Publish npm package: `npx token-saver-meta`
- Publish PyPI package: `uvx token-saver-meta`
- GitHub repo with README, docs, quickstart
- `curl | sh` fallback for non-Node/Python users

## Phase 10: Testing & Verification

- Benchmark standard task ("add CRUD endpoint") with/without tools
- Measure per-tool savings on benchmark
- Cross-platform testing (Windows, macOS, Linux)
- Cross-agent testing (5+ agents)
- Long-session testing (multi-hour, compaction events)

## v2 Deferred Items

| Item | Reason |
|------|--------|
| jcodemunch-mcp | Dual-use license — needs separate commercial path |
| sdl-mcp | Source-available license — review terms |
| opentoken, omni, tokensave | Evaluate vs existing tools (RTK, CBM) |
| Deblank, racs, toon | Need custom wrappers for agent integration |
| flowork_Router, CometCLI, supamem | Heavy infra or copyleft concerns |
| Desktop app (Tauri) | Highest-effort distribution channel |

---

# APPENDIX A: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-18 | ⭐ **Rewrite Strategy adopted** — 6 micro-tools audited | 6 tools <1K stars: 4 SKILL.md → vendor as text (merge into AGENTS.md), 4 code tools → Python rewrite (ContextSlimAI, TSCG, codex-agent-mem+Loom unified T5). GitNexus blocked (PolyForm NC). CGC corrected (SQLite, not Neo4j). Full strategy at `docs/rewrite-strategy.md`. |
| 2026-06-18 | GitNexus uses PolyForm Noncommercial — BLOCKER for bundling | Must verify: abhigyanpatwari/GitNexus has PolyForm Noncommercial License, not MIT/Apache. Cannot bundle in any commercial distribution. Needs separate non-commercial only path or replacement. |
| 2026-06-18 | CGC corrected: SQLite+FTS5, NOT Neo4j+Cypher | Codegraph (colbymchenry/codegraph, 51K stars) uses Node.js + SQLite + FTS5 + BFS. No Cypher queries. No Neo4j. Install via npx, not uvx. |
| 2026-06-18 | Architecture: Option D (Hybrid) | Oracle evaluation: D=77, A=51, B=72, C=88(fails mission). D balances savings with usability. |
| 2026-06-18 | Added Repomix + ContextSlimAI to D | Oracle recommendation for T1+T2 defense-in-depth. Both Node-only, zero friction. |
| 2026-06-18 | `npx token-saver-meta init` is primary command (from Option B) | Node.js is most ubiquitous runtime. Matches user expectations (create-react-app pattern). |
| 2026-06-18 | Base layer is 4 SKILL.md tools merged into AGENTS.md (from Option C) | Instant value, works everywhere, zero deps, cannot break. |
| 2026-06-18 | LLMLingua is optional with GPU auto-detect | GPU not universal. Auto-detect + advise. Never auto-install GPU deps. |
| 2026-06-18 | T4/T5/T6 are optional-only in v1 | Heaviest types (T1+T2 at 55-280K/session) get core coverage first. Lower-waste types get optional. |
| 2026-06-13 | Only 1 genuine conflict (RTK vs lean-ctx shell hook) | Sequential thinking resolved 5 false conflicts. |
| 2026-06-13 | Core/optional/deep-study split | Research-established. Core=always, optional=one-click, deep-study=v2. |
| 2026-07-02 | Replaced GitNexus with CBM (codebase-memory-mcp) | MIT license, 24k stars, pure C, 158 languages. Sidecar MCP server (cbm_sidecar/) backfills context/rename/route_map tools. |

# APPENDIX B: Reference Sources

| Source | What It Provided |
|--------|-----------------|
| 63 cloned repos | Tool mechanisms, dependencies, licenses |
| 39 insights (insights_and_synergies.md) | What we know about token saving |
| 24 synergies (insights_and_synergies.md) | How tools compound |
| 46 tools BESTS.md | Tool ranking, scores, caveats |
| rustup installer | Bootstrap + binary pattern |
| Homebrew FormulaInstaller | Phased pipeline with rollback |
| nvm install.sh | Shell detection + PATH manipulation |
| uv Python discovery | Tiered auto-detection |
| codegraph AgentTarget | Target registry + atomic config + marker injection |
| gitnexus_CGC_combo | Platform detection, MCP config gen, merge strategies |
| MOS SKILL_EN.md | Complexity scoring, session-start block |
| orchestkit setup SKILL.md | 10-phase onboarding wizard, readiness scoring |
| git-courer install.sh + TUI | OS/arch/shell detection, interactive wizard |
| vscode #284712 | Compression toggle UX, privacy controls |
| opencode #1573 | Mode-based tool loading |
| Paperclip #373 | Lazy spawning |
| Kilo #5848 | Built-in CLI compression |
| Oracle evaluation (2026-06-18) | Architecture scoring, Option D recommendation, merged elements |

---

## Acknowledgments

### Directly Utilized
These tools are installed via their package managers during setup. They are licensed under MIT or Apache-2.0 (all compatible with our Apache-2.0 redistribution).

| Tool | License | Role in token-saver-meta |
|------|---------|---------------------------|
| [CGC/codegraph](https://github.com/colbymchenry/codegraph) | MIT | Code graph queries via SQLite+FTS5 semantic search |
| [codesight](https://github.com/Houseofmvps/codesight) | MIT | Pre-built project structure context maps (7x-91x compression) |
| [Repomix](https://github.com/yamadashy/repomix) | MIT | Full repository packing into a single file (~70% compression) |
| [RTK](https://github.com/rtk-ai/rtk) | Apache-2.0 | Shell output compression via PreToolUse hook (60-90%) |
| [LLMLingua-2](https://github.com/microsoft/LLMLingua) | MIT | ML-based prompt token optimization (GPU auto-detect) |
| [SkillOpt](https://github.com/microsoft/SkillOpt) | MIT | Trainable skill document optimization (300-2K token artifacts) |

### Technique Sources
These projects inspired the 28 token-saving rules vendored as text in our AGENTS.md injection block. No code from these projects is distributed — only the behavioral techniques are applied.

| Project | License | Technique Applied |
|---------|---------|-------------------|
| [caveman](https://github.com/JuliusBrussee/caveman) | MIT | Prose terseness — concise language, no filler, no hedging (~75% output reduction) |
| [ponytail](https://github.com/DietrichGebert/ponytail) | MIT | YAGNI code minimalism ladder — stdlib→native→dep→one-liner→minimal (~54% LOC, ~22% tokens) |
| [LG-token-saver](https://github.com) | MIT | 8 operational efficiency rules — parallelism, dedup, compaction, filtering |
| [kevin-copilot](https://github.com) | MIT | Structured output — 4 terseness modes, consistent formatting |

### Rewritten from the Ground Up
These are original Python implementations created for token-saver-meta, inspired by the concepts of the following projects. No code from the originals is used.

| Our Package | Inspired By | Original License | Our License |
|-------------|-------------|-----------------|-------------|
| tscg | [TSCG](https://github.com/SKZL-AI/tscg) by nicholasgriffintn | MIT | Apache-2.0 |
| contextslim | [ContextSlimAI](https://github.com) | Apache-2.0 | Apache-2.0 |
| token-saver-mem | [codex-agent-mem](https://github.com) + [Loom](https://github.com) | Apache-2.0 + MIT | Apache-2.0 |

### Excluded from Redistribution

| Tool | Reason |
|------|--------|
| GitNexus | [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — cannot redistribute in any commercial distribution. Listed here for attribution; NOT included in the product. |

---

## Acknowledgments

This project builds on ideas from the open-source community. The token-saving rules originated from:
- caveman (MIT) — prose style rules
- ponytail (MIT) — code minimalism rules (YAGNI ladder)
- LG-token-saver (MIT) — operational efficiency rules
- kevin-copilot (MIT) — structured output rules

All tools bundled or referenced by this project are MIT or Apache-2.0 licensed. See individual sub-projects for details.
