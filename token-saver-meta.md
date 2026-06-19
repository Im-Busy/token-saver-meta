# token-saver-meta — "Token Saving for the Masses" Meta-Package

> Brainstorm document. A project that packages token-saving developer tools into one coherent, zero-thought-required install for non-technical users. Think: "I downloaded this and it just works."

---

## Vision Statement

A single installable package that gives any AI coding tool (on any platform) the full stack of token-saving capabilities — graph-based code intelligence, output compression, context engineering, and intelligent repo packing — with zero configuration from the user. The user downloads one thing, clicks one button, says one sentence to their agent, and their token usage drops 50-80% immediately.

---

## What We're Building On (Existing Foundation)

The `gitnexus_CGC_combo` project already solves the hardest infrastructure problems:

| Already Solved | How |
|---------------|-----|
| Platform detection | Filesystem marker scanning — 17 platforms, zero user prompting |
| MCP config generation | 3 format families (`mcpServers`, `mcp`, `servers`), idempotent merge |
| Agent protocol injection | AGENTS.md injection via `<!-- gitnexus:start -->` markers |
| Skill distribution | 8 operational skills, multi-platform copy |
| Two-path architecture | Agent path (AGENTS.md protocol) + Manual path (`uvx combo-setup setup ./`) |
| Cross-platform watcher | systemd, launchd, PowerShell background process |
| Uninstall protocol | Inverse operations, dry-run support |

**Core design principle we inherit:** The agent IS the runtime. AGENTS.md is the program. Scripts exist only where agents are weak (structured JSON generation).

---

## Layer 1: What Tools to Bundle — The Full Token-Saving Stack

The existing combo only bundles GitNexus + CGC (Layer 2). For a meta-package, we need to bundle ALL layers:

```
┌──────────────────────────────────────────────────────────┐
│  Layer 6: One-Click Installer / Desktop App               │
│  (hatch3r, Drodo, kivun-terminal patterns)               │
│  Zero terminal required. GUI wizard → done.              │
├──────────────────────────────────────────────────────────┤
│  Layer 5: MCP Aggregator                                  │
│  MetaMCP / @curatedmcp/launcher                          │
│  Collapses N MCP servers into constant schema tokens      │
│  (~1,300 tokens vs 15K+ for separate servers)            │
├──────────────────────────────────────────────────────────┤
│  Layer 4: API-Level Proxy Compression                     │
│  Kompact / ContextPilot                                  │
│  Transparent HTTP proxy — just repoint the agent's        │
│  base URL. Compresses full API payloads.                 │
├──────────────────────────────────────────────────────────┤
│  Layer 3: Shell Output Compression                        │
│  RTK / lean-ctx / context-compress                       │
│  Hook-based, transparent, 60-90% token savings            │
│  on every tool call.                                     │
├──────────────────────────────────────────────────────────┤
│  Layer 2: Code Intelligence MCP Servers                   │
│  GitNexus + CodeGraphContext + Repomix + LVM             │
│  Graph-based selective retrieval instead of               │
│  dumping entire files into context.                      │
├──────────────────────────────────────────────────────────┤
│  Layer 1: Agent Protocol (AGENTS.md)                       │
│  Always/Never rules, tool selection guidance,             │
│  impact-analysis-before-edit discipline.                 │
└──────────────────────────────────────────────────────────┘
```

### Layer 1: Agent Protocol (ALREADY DONE)
> The existing AGENTS.md injection in `gitnexus_CGC_combo` handles this. "Always run impact analysis before editing." "Never grep when you can query the graph." Extend with rules for the new tools.

### Layer 2: Code Intelligence MCP Servers (PARTIALLY DONE)

| Tool | Status | Bundle Strategy |
|------|--------|----------------|
| **GitNexus** | ✅ Already bundled | `npx -y gitnexus@latest` — auto-fetched, no install |
| **CodeGraphContext** | ✅ Already bundled | `uv pip install codegraphcontext` or `uv sync` |
| **Repomix** | ❌ New | `npx repomix` — already has MCP server mode. Add MCP config entry. Add to AGENTS.md: "Before starting, run repomix for initial codebase load" |
| **LVM / Context-Condenser** | ❌ New | `npx context-condenser` — tree-sitter skeleton + lazy hydrate. Saves ~70% tokens on code reads |

### Layer 3: Shell Output Compression (NEW)

| Tool | Bundle Strategy | Why |
|------|----------------|-----|
| **lean-ctx** (Rust) | Binary download + MCP config | Most comprehensive. 90+ command patterns, cached reads (~13 tokens), CCP cross-session memory. 60-99% savings. |
| **RTK** (Rust) | Binary download | Lighter alternative. PreToolUse hook rewrites commands. <10ms. |
| **context-compress** (Python) | `uv pip install` | Pure Python. Good fallback where Rust binaries won't run. |

**Preference:** lean-ctx (most capabilities) or RTK (simplest). These are hook-based and zero-config — they just work once installed.

### Layer 4: API-Level Proxy Compression (NEW, DEFERRED)

| Tool | Bundle Strategy | Why |
|------|----------------|-----|
| **Kompact** | `uv pip install` | Transparent HTTP proxy. Dashboard. 8 transforms. |
| **ContextPilot** | Deferred | Quality-gated fallback. More complex setup. |

**Decision:** Defer Layer 4 to v2. It adds complexity (proxy configuration) for a layer the user shouldn't need to configure. Layer 3 (shell output compression) handles most of the same savings with zero config.

### Layer 5: MCP Aggregator (NEW)

| Tool | Bundle Strategy | Why |
|------|----------------|-----|
| **MetaMCP** | `npx metamcp` or config | Collapses N MCP servers into 6 constant-size tools (~1,300 tokens). Curated gallery of 122 servers. |

**Critical for token efficiency:** Each MCP server adds ~3K tokens of tool schema to every request. With 5+ servers (GitNexus + CGC + Repomix + lean-ctx + maybe more), that's 15K+ tokens burned before the agent even starts thinking. MetaMCP collapses all of them into 6 tools at a constant ~1,300 token overhead.

### Layer 6: One-Click Installer (NEW — THE KEY LAYER)

This is the "for the masses" part. The existing combo assumes the user has an AI coding tool and knows how to say `/combo-setup`. For non-technical users, none of that is true.

See **Idea Block 3** below for full details.

---

## Idea Block 1: "It Just Works" — The Zero-Thought Install Experience

### Problem Statement
The current combo project requires the user to:
1. Have an AI coding tool installed
2. Know what "MCP" or "slash commands" are
3. Open the project in that tool
4. Type `/combo-setup`
5. Wait for 8 phases to complete

None of this works for someone who just wants their AI tool to use fewer tokens.

### The "It Just Works" Flow

```
User downloads token-saver-meta.exe (or .dmg, or .AppImage)
   │
   ├── [Auto-detect phase]
   │   ├── Scans for installed AI coding tools
   │   │   (Claude Code, Cursor, VS Code + Copilot, Windsurf, etc.)
   │   ├── Checks which tools are already installed
   │   │   (Node.js, Python, uv, git — reports missing ones)
   │   ├── Checks what's already configured
   │   │   (existing MCP servers, existing AGENTS.md, existing skills)
   │   └── Builds a "what will change" preview
   │
   ├── [One-click install]
   │   ├── Installs missing dependencies (offers: "Node.js not found. Install? Y/N")
   │   ├── Sets up all MCP configs (merges, never overwrites)
   │   ├── Indexes the project with GitNexus + CGC
   │   ├── Writes AGENTS.md protocol
   │   ├── Copies skills to platform directories
   │   └── Starts CGC watcher
   │
   └── [Post-install]
       ├── Shows "✅ Done! Your agent now saves ~60% tokens."
       ├── Shows: "Next time you talk to your AI, say: 'help me understand this codebase'"
       └── Optional: "Watch a 60-second demo"
```

### Key UX Principles

1. **Never show a terminal unless absolutely necessary.** If `npx` needs to run, run it silently and show progress in the GUI.
2. **Never ask "which platform do you use?"** Auto-detect via filesystem markers (already implemented in `config_gen.py`).
3. **Never ask "do you have X installed?"** Auto-detect and offer to install. Don't make the user check versions themselves.
4. **Never fail silently.** If indexing fails, say "GitNexus indexing failed. This means: [plain English]. Fix: click here to retry, or skip (code intelligence will be limited)."
5. **Show token savings.** After install, show estimated savings based on project size. "With 5,000 files, your agent would normally read ~200K tokens of code. With code intelligence, it reads ~40K. That's $X saved per session."

---

## Idea Block 2: "What's Already There?" — Dependency Discovery & Smart Merge

### Problem Statement
The current combo writes MCP configs and AGENTS.md sections. But it doesn't check if the user already has:
- GitNexus or CGC installed (globally or in another project)
- Repomix installed
- lean-ctx configured
- Other MCP servers that might conflict
- An existing AGENTS.md with its own behavioral rules

### Smart Discovery System

```
Token-Saver Discovery Engine
│
├── [Phase 1: Environment Scan]
│   ├── which gitnexus → already installed? version?
│   ├── which cgc → already installed? version?
│   ├── which repomix → already installed?
│   ├── npm list -g --depth=0 → any globally installed MCP tools?
│   ├── uv pip list | grep -i context → any context tools?
│   └── ls ~/.lean-ctx → lean-ctx configured?
│
├── [Phase 2: Configuration Scan]
│   ├── Parse all detected platform MCP configs
│   │   (Cursor .cursor/mcp.json, Claude .mcp.json, etc.)
│   ├── Check for existing gitnexus/cgc entries → already configured?
│   ├── Check for conflicting tool names
│   │   (e.g., both lean-ctx and RTK provide "compress" — conflict)
│   └── Check for existing AGENTS.md sections
│       (<!-- gitnexus:start --> markers → update, don't duplicate)
│
├── [Phase 3: Project Analysis]
│   ├── What language(s) does this project use?
│   │   → skip Python-specific tools for JS projects
│   ├── How many files? → estimate index time, token savings
│   ├── Is there a src/ directory? → watcher target
│   └── Git repo? → commit hash for stale index detection
│
└── [Phase 4: Recommendation Engine]
    ├── "Found: GitNexus v1.5.2 (global). CGC not installed. Repomix not installed."
    ├── "Recommended: Install CGC + Repomix. Skip: RTK (lean-ctx already configured)."
    └── "Estimated token savings: 65% → ~$12/session"
```

### What the Agent Should Do in Each Situation

| Discovery | Action |
|-----------|--------|
| Tool already installed (global) | Skip install. Add MCP config entry only. Verify version compatibility. |
| Tool already installed (different version) | Offer: "Found GitNexus v1.5.2 (you have v1.3.0). Update? Y/N" |
| Tool already in MCP config (another project) | "This tool is configured for another project. Add to this project as well? Y/N" |
| Tool not installed | Install silently with progress bar |
| Conflicting tool detected | "Found lean-ctx (covers output compression). Installing RTK would create a conflict. Skip RTK? Y/N [Recommended]" |
| AGENTS.md exists with user content | Merge around markers. Never overwrite user's own sections. |
| No AI coding tool detected | "No supported AI tool detected. Install one? [List with download links]" |

---

## Idea Block 3: "Make It Default" — Teaching Agentic Environments

### Problem Statement
Even after installing the tools, the user's agent won't use them unless it knows to. The current combo solves this with AGENTS.md injection — but that only works if the agent reads AGENTS.md. Some platforms don't. Some users disable it. Some agents are configured differently.

### Multi-Channel Behavior Injection

```
Teaching the Agent to Use Token-Saving Tools by Default
│
├── [Channel A: AGENTS.md Injection] (ALREADY DONE)
│   ├── "Always run impact analysis before editing"
│   ├── "Never grep when you can query the code graph"
│   ├── "Before committing, run detect_changes"
│   └── Extended rules for new tools:
│       "Before reading files, check if lean-ctx has a cached version (~13 tokens)"
│       "For initial codebase understanding, use Repomix compressed pack"
│       "When reading large files, use context-condenser skeleton mode first"
│
├── [Channel B: Platform-Specific Instruction Files] (PARTIALLY DONE)
│   ├── CLAUDE.md → append: "CRITICAL: GitNexus + CGC + [tools] are active. See AGENTS.md."
│   ├── .cursorrules → append: same directive
│   ├── .clinerules → append: same directive
│   ├── .roorules → append: same directive
│   ├── .windsurfrules → append: same directive
│   └── .github/copilot-instructions.md → append: same directive
│
├── [Channel C: Skill Files] (ALREADY DONE for GitNexus+CGC)
│   ├── Existing: gitnexus-* (6 skills), cgc-guide (1), combo-workflow (1)
│   ├── NEW: token-saver-meta/SKILL.md — unified token-saving workflow
│   ├── NEW: repomix-pack/SKILL.md — how to use Repomix in agent workflows
│   └── NEW: context-compression/SKILL.md — when to compress/compact/externalize
│
├── [Channel D: System Prompt Hook] (NEW)
│   └── For platforms that support it (Claude Code, Kilo):
│       Inject into system prompt: "You have GitNexus + CGC + Repomix + lean-ctx.
│       These tools reduce token usage by 60-80%. Always prefer these tools over
│       raw file reads and grep. See AGENTS.md for full protocol."
│
└── [Channel E: MCP Tool Descriptions] (NEW)
    └── Ensure every bundled MCP tool has a description that explicitly says
        "Use this instead of grep/glob for [task]. Saves ~X tokens."
        The agent's tool selection model will naturally prefer
        the more efficient tool when the description guides it.
```

### The "Token Saving by Default" Protocol

Add to every injected AGENTS.md:

```markdown
<!-- token-saver:start -->
# Token-Saving Protocol — AUTOMATIC

This project is equipped with a token-saving toolkit. Your agent MUST follow this protocol:

## Always Do (Token Efficiency)
- **Before reading any file >100 lines:** Check if lean-ctx has it cached (~13 tokens vs full read)
- **Before exploring unfamiliar code:** Use GitNexus `query()` or CGC `find_code()` instead of grep
- **Before editing any function:** Run `gitnexus_impact()` — don't read the whole file
- **For initial project understanding:** Load the Repomix compressed pack instead of reading individual files
- **When context exceeds 64%:** Trigger lean-ctx session compaction BEFORE hitting the limit
- **After significant changes:** Run `npx gitnexus detect_changes` to verify blast radius

## Never Do (Token Waste)
- NEVER `grep` for code structure — GitNexus/CGC graph queries are 10-100x more token-efficient
- NEVER read entire large files (>500 lines) — use context-condenser skeleton mode first
- NEVER keep stale tool output in context — lean-ctx compresses automatically
- NEVER ignore impact analysis warnings — fixing a broken dependency costs more tokens than preventing it

## Token Savings Estimate (This Project)
- Without tools: ~200K tokens per complex task
- With tools: ~60K tokens per complex task
- Savings: ~70% (roughly $3-5 saved per session, depending on model)
<!-- token-saver:end -->
```

---

## Idea Block 4: "Why Didn't This Work?" — Failure Prevention & Diagnostics

### Problem Statement
The #1 complaint about developer tools: "I installed it and it didn't work." For non-technical users, this means the tool is dead to them. They won't debug. They won't read logs. They won't open a terminal.

### Failure Prevention Architecture

```
Pre-Flight Check (runs BEFORE installation)
├── "Can I write to this directory?" → check filesystem permissions
├── "Is Node.js reachable?" → test with node --version
├── "Is the internet available?" → test npmjs.org + pypi.org reachability
├── "Is there enough disk space?" → check free space vs estimated need
├── "Can I modify the MCP config?" → test read/write on config file
└── [If any check fails] → "Before I continue, [plain English]: You need [X]"

Runtime Verification (runs AFTER each tool install)
├── npx gitnexus --version → "✅ GitNexus installed"
├── npx repomix --version → "✅ Repomix installed"
├── uv run cgc --version → "✅ CodeGraphContext installed"
├── lean-ctx --version → "✅ lean-ctx installed"
└── [If any fails] → "❌ [Tool] failed to install. Try: [one-click fix button]"

Post-Install Verification (runs BEFORE showing "Done!")
├── npx gitnexus status → must show "up-to-date"
├── uv run cgc stats ./ → must show >0 files indexed
├── Test MCP connectivity → actually call a tool to verify it works
├── Check AGENTS.md was injected → verify markers exist
├── Start CGC watcher and verify → process check
├── Test that agent can use the tools → run gitnexus_query("test") and check response
└── [If any fails] → "⚠️ [Component] not working. This means: [plain English].
    Auto-fix: retry. Manual fix: [simple instructions with screenshots]."
```

### User-Facing Error Messages (NOT agent-facing)

| Current (agent-facing) | New (user-facing) |
|------------------------|-------------------|
| `config_gen.py: write_mcp_config returned status='error', message='Unknown platform: xyz'` | "Couldn't detect your AI tool. Which one do you use? [Dropdown with icons]" |
| `subprocess.CalledProcessError: npx gitnexus analyze returned exit code 1` | "GitNexus couldn't index your project. This usually means: 1) Node.js not installed, or 2) network issue. [Fix button: Install Node.js] [Fix button: Retry]" |
| `FileNotFoundError: uv` | "Python package manager not found. I'll install it now. [Install uv] [Skip — limited functionality]" |
| `pgrep: no process found (cgc watch)` | (Don't show — just restart it. Only show if restart fails 3x.) |
| `MCP config merge: existing JSON invalid` | "Your AI tool's config file seems corrupted. I can: [Fix automatically (backup original)] [Show me what's wrong] [Skip]" |

### Diagnostic Dashboard (Desktop App / Web UI)

A single page showing:

```
┌─────────────────────────────────────────────────┐
│  Token-Saver Status                              │
│                                                  │
│  🟢 GitNexus         indexed · 5,234 symbols     │
│  🟢 CGC              indexed · 312 files      │
│  🟡 Repomix           not indexed (click to run) │
│  🟢 lean-ctx          active · shell hook      │
│  🟢 MetaMCP           aggregating 4 servers    │
│  🟢 CGC Watcher       running · 2 min ago      │
│                                                  │
│  Estimated Token Savings: 67%                    │
│  This session (est.): $4.20 saved                │
│  All time (est.): $89.40 saved                   │
│                                                  │
│  [Reindex All] [Restart Watcher] [Diagnose]      │
└─────────────────────────────────────────────────┘
```

---

## Idea Block 5: "1+1>2" — Synergy Between Tools

### Why Tools Together Outperform Tools Alone

The existing combo project already demonstrates this: GitNexus + CGC together cover each other's gaps. For the meta-package, the synergy extends further:

```
                    ┌────────────┐
                    │  Repomix   │ ← Initial bulk load (once per session)
                    └─────┬──────┘
                          │ "what does this project look like?"
                          ▼
              ┌───────────────────────┐
              │  GitNexus + CGC       │ ← Ongoing: graph-selected retrieval
              │  (code intelligence)  │    "who calls this function?"
              └───────────┬───────────┘
                          │ tool output (still verbose)
                          ▼
              ┌───────────────────────┐
              │  lean-ctx / RTK       │ ← Compresses tool output by 60-90%
              │  (output compression) │    "git status" → compact summary
              └───────────┬───────────┘
                          │ compressed output
                          ▼
              ┌───────────────────────┐
              │  MetaMCP              │ ← Reduces schema overhead
              │  (MCP aggregation)    │    4 servers → 6 tools (~1,300 tokens)
              └───────────┬───────────┘
                          │
                          ▼
                   [LLM API Call]
                Total context: ~40K tokens
         (vs ~200K without any of these tools)
```

### Specific Synergy Examples

1. **GitNexus impact → Repomix pack → lean-ctx cache**
   - Agent needs to understand `PaymentService.process()`
   - GitNexus `impact("process")` → returns called functions list (50 tokens)
   - Repomix `--compress` on those specific files → skeleton (200 tokens)
   - lean-ctx caches the skeleton → next session costs 13 tokens
   - **Total: 263 tokens vs 5,000+ reading raw files**

2. **CGC dead-code → GitNexus impact → safe delete**
   - CGC `find_dead_code` → list of unreferenced functions (100 tokens)
   - For each candidate, GitNexus `impact()` → confirm no runtime callers (20 tokens each)
   - Agent safely removes confirmed dead code
   - **Without both: agent reads every file looking for references (10K+ tokens)**

3. **MetaMCP → all tools available in constant overhead**
   - Without MetaMCP: GitNexus (3K) + CGC (3K) + Repomix (3K) + lean-ctx (3K) = 12K tokens burned just for tool schemas
   - With MetaMCP: 6 tools at ~1,300 tokens total
   - **Savings: ~10K tokens per request — compounds across the entire session**

4. **lean-ctx CCP → cross-session tool index persistence**
   - After first session, lean-ctx CCP remembers which GitNexus/CGC resources are most useful
   - Next session: agent loads cached resource map instead of re-exploring
   - **Saves 5-10 minutes of exploration tokens per new session**

### Tool Compatibility Matrix

| Tool A | Tool B | Synergy? | Notes |
|--------|--------|----------|-------|
| GitNexus | CGC | ✅ Strong | GitNexus: impact/flows. CGC: hierarchy/dead-code. Non-overlapping strengths. |
| GitNexus | Repomix | ✅ Moderate | Repomix for initial load, GitNexus for ongoing queries |
| GitNexus | lean-ctx | ✅ Strong | lean-ctx compresses GitNexus tool output (often verbose) |
| GitNexus | MetaMCP | ✅ Strong | MetaMCP reduces the schema cost of GitNexus's 7 tools |
| CGC | Repomix | ✅ Moderate | Repomix packs, CGC queries. Less synergistic than GitNexus+Repomix |
| CGC | lean-ctx | ✅ Strong | CGC graph queries can be verbose — lean-ctx compresses |
| lean-ctx | RTK | ❌ Conflict | Both do shell output compression. Pick ONE. |
| Repomix | lean-ctx | ✅ Weak | Different layers. Repomix is bulk, lean-ctx is per-call. No conflict. |
| MetaMCP | everything | ✅ Universal | Reduces schema overhead for ALL bundled tools |
| Kompact | lean-ctx | ⚠️ Overlap | Both compress, different layers. Kompact (API), lean-ctx (shell). Can coexist but adds complexity. |

---

## Idea Block 6: Native Platform Support (17+ Platforms)

### The Existing Matrix (ALREADY SOLVED)

The `platforms/matrix.json` already handles 17 platforms with 3 MCP format families:

| Family | Platforms |
|--------|-----------|
| `mcpServers` | Claude Code, Codex, Cursor, Cline, Roo Code, Continue.dev, Windsurf, Augment, Copilot CLI, Factory, Gemini, Hermes, Mastra, Pi |
| `mcp` | Kilo, Opencode, Kiro |
| `servers` | Copilot VS Code |

### What Needs to Be Added for the Meta-Package

For each new tool (Repomix, lean-ctx, MetaMCP), we need to add server entries to the matrix:

```json
{
  "repomix_server": {
    "mcpServers_format": {
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    },
    "mcp_format": {
      "type": "local",
      "command": ["npx", "-y", "repomix", "--mcp"]
    },
    "servers_format": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    }
  },
  "leanctx_server": {
    "mcpServers_format": {
      "command": "lean-ctx",
      "args": ["mcp"]
    },
    ...
  },
  "metamcp_server": {
    "mcpServers_format": {
      "command": "npx",
      "args": ["-y", "metamcp"]
    },
    ...
  }
}
```

### Platform-Specific Considerations

| Platform | What Changes | Notes |
|----------|-------------|-------|
| **Windsurf** | Manual paste required | Show the JSON + copy button in the desktop app. Guide: "Paste this into Settings → MCP" |
| **Augment** | Manual paste required | Same as Windsurf |
| **Continue.dev** | Standalone file per server | Create separate `.continue/mcpServers/{gitnexus,cgc,repomix,leanctx}-cgc.json` files |
| **Non-skill platforms** | Inline rules in AGENTS.md | Cursor, Cline, Roo Code, Continue, Windsurf, Augment, Copilot get behavioral rules embedded directly |
| **Skill platforms** | Copy skills to platform dirs | Kilo → `.kilo/skills/`, Claude → `.claude/skills/`, Codex → `.codex/skills/`, etc. |

### The "Teach the Agent" Pattern (Extended)

For platforms WITH AGENTS.md reading:
- The existing injection (Phase 6) covers this
- Extend with token-saver protocol from Idea Block 3

For platforms WITHOUT AGENTS.md reading (or where user disabled it):
- Write rules into multiple instruction files:
  - `.cursorrules` / `.cursor/rules/combo.md`
  - `.clinerules`
  - `.roorules`
  - `.windsurfrules`
  - `.github/copilot-instructions.md`
- Also write to platform-specific config files where they support embedded instructions:
  - `opencode.json` → embed in the config
  - `.mcp.json` → some platforms read embedded documentation

---

## Idea Block 7: Suggested Initialization — "You Haven't Set This Up Yet"

### Problem Statement

A user installs the tools, but their project isn't indexed. The agent doesn't know to suggest indexing. The user doesn't know indexing exists. Result: tools installed, zero benefit.

### Proactive Initialization Prompts

```
After installation, the desktop app / installer:

1. [Immediately] "Would you like to index your project now?
   This takes ~30 seconds and enables code intelligence and token savings."
   [Index Now] [Later]

2. [If user clicks "Later"] Store a reminder. Next time the app opens:
   "Your project still isn't indexed. Without indexing, token-saving tools
   can't work. Index now? [Index Now] [Remind Me Tomorrow] [Don't Ask Again]"

3. [After first agent session without tools used]
   Detect that no GitNexus/CGC tool was called.
   "Your agent didn't use any token-saving tools this session.
   This might mean the tools aren't configured correctly.
   [Run Diagnostic] [Show Setup Guide]"

4. [Periodic freshness check]
   "Your code index is 3 days old (12 files changed since last index).
   Re-index for accurate results? [Reindex] [Remind Later]"
```

### Agent-Side: Teaching the Agent to Suggest Initialization

Add to AGENTS.md:

```markdown
## Initialization Awareness

If you are the agent and detect that:
- GitNexus index is stale or missing
- CGC index is stale or missing
- Repomix pack hasn't been generated
- lean-ctx cache is empty

**You MUST suggest initialization to the user:**
"I notice your code intelligence tools aren't set up yet. This means
I'm reading raw files instead of using graph queries, which costs
about 3-5x more tokens. Would you like me to set them up now?
It takes ~30 seconds and saves ~$2-5 per session."

**If the user says yes:**
Run: `npx gitnexus analyze --embeddings --skills`
Run: `uv run cgc index ./`
Run: `npx repomix --compress`
Then: "✅ All tools initialized. Estimated token savings: 65%"
```

### Auto-Initialization (Opt-in)

For truly non-technical users, add a "Set Everything Up Automatically" checkbox during install. When checked:

1. After install, immediately trigger indexing (don't wait for the user to say go)
2. If indexing fails, retry once (with exponential backoff), then show a clear error
3. If indexing succeeds, start the watcher automatically
4. Show a "✅ Everything is ready. Your AI agent now saves tokens automatically."

---

## Idea Block 8: "Token Savings Dashboard" — Make It Visible

### Problem Statement

Token savings are invisible. The user installs the tools and... nothing changes in their experience. They don't see the money saved. They don't know if it's working. Without visible value, they won't recommend it, won't maintain it, won't care.

### Token Savings Visualization

```
┌──────────────────────────────────────────────────────────┐
│  📊 Token Saver — Dashboard                               │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Today's Savings                                     │ │
│  │                                                      │ │
│  │  Tokens used:  ████████░░  45,230                    │ │
│  │  Without tools: ████████████████████  198,400        │ │
│  │  Saved:          153,170 tokens (77%)                 │ │
│  │                                                      │ │
│  │  💰 Estimated cost saved: $4.59 (Claude Opus rates)  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Where Tokens Were Saved                              │ │
│  │                                                      │ │
│  │  GitNexus impact analysis:  ████████  32,000 saved   │ │
│  │  lean-ctx compression:       ██████    28,000 saved   │ │
│  │  CGC graph queries:          █████     18,000 saved   │ │
│  │  Repomix compressed pack:    ████      15,000 saved   │ │
│  │  MetaMCP aggregation:        ██        10,000 saved   │ │
│  │  Code not needing raw read:  █████████ 50,000 saved   │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  This month: $42.30 saved  |  All time: $189.40 saved     │
│  [Share on Twitter] [Leave a Review] [Upgrade Plan]       │
└──────────────────────────────────────────────────────────┘
```

### Token Savings Calculation

To calculate savings, the dashboard needs to know:

1. **How many tokens each tool call saved vs raw file reads:**
   - GitNexus `context("foo")` → returned 500 tokens of focused code. Raw read of all files containing `foo` would be ~8,000 tokens. Saved: 7,500.
   - lean-ctx `ctx_read(path, mode="map")` → 200 tokens. Raw read: 4,500 tokens. Saved: 4,300.
   - Repomix `--compress` pack → 800 tokens vs reading 20 files raw: 15,000 tokens. Saved: 14,200.

2. **Token pricing:**
   - Track the user's model (Claude Opus, GPT-4, etc.)
   - Apply per-model pricing to convert tokens → dollars

3. **Baseline estimation:**
   - When tools are NOT used, estimate what the agent WOULD have done (grep, raw file reads)
   - This is an estimate — mark it as "estimated savings"

### Social Proof / Virality

- "Share your savings" button → generates a tweet: "My AI coding agent saves me $42/month with token-saver-meta 🚀 #AICoding"
- Leaderboard (opt-in): "You're in the top 5% of savers this week!"
- Referral: "Refer a friend, both get 1 month free Premium"

---

## Idea Block 9: Distribution — How Non-Technical Users Get It

### Current State (gitnexus_CGC_combo)

- **Agent path:** `/combo-setup` slash command → agent provisions everything
- **Manual path:** `uvx gitnexus-cgc-combo setup ./` → CLI provisions everything
- Both require: terminal, uv, Python, Node.js knowledge

### New Distribution Channels (For the Masses)

| Channel | Target | Effort | Description |
|---------|--------|--------|-------------|
| **Desktop App** (Tauri/Electron) | Complete beginners | High (2 weeks) | Download .exe/.dmg/.AppImage. GUI wizard. One click. |
| **VS Code Extension** | VS Code / Cursor users | Medium (3 days) | Status bar indicator + one-click setup. Huge user base. |
| **GitHub Codespaces** | GitHub users | Low (1 hour) | Pre-configured devcontainer. Click "Open in Codespaces" → ready. |
| **Homebrew / Chocolatey / Scoop** | Mac/Windows users | Low (2 hours) | `brew install token-saver-meta` → done. |
| **`npx create-token-saver`** | JS developers | Medium (2 days) | Familiar `create-*` pattern. Scaffolds into any project. |
| **Standalone Binary** (PyInstaller) | Zero-dependency | Medium (1 day) | Single .exe file. No Python, Node, or uv needed. Bundles everything. |
| **Web UI** (localhost dashboard) | Browser-native | Medium (3 days) | `token-saver open` → opens browser dashboard. Status, setup, savings. |

### Recommended Rollout Order

1. **Standalone Binary** (P0 — 1 day) → Covers 90% of use cases. One download, one click.
2. **VS Code Extension** (P1 — 3 days) → Largest user base. Status bar builds trust.
3. **Homebrew/Chocolatey/Scoop** (P1 — 2 hours) → Easy discovery. Low effort.
4. **GitHub Codespaces** (P2 — 1 hour) → Zero-local-install for GitHub users.
5. **Desktop App** (P2 — 2 weeks) → Polished experience. Defer until core is stable.

---

## Idea Block 10: Auto-Update & Maintenance — "Set It and Forget It"

### Problem Statement

Tools evolve. GitNexus gets new features. CGC fixes bugs. lean-ctx improves compression. If the user installed v1.0 six months ago, they're on stale tools with worse token savings and maybe broken configs.

### Auto-Update Architecture

```
Token-Saver Update Engine
│
├── [Check on Launch]
│   ├── npx gitnexus --version → compare with latest npm registry
│   ├── uv pip list --outdated → check cgc, context-compress
│   ├── lean-ctx --version → check GitHub releases
│   └── Token-Saver itself → check PyPI/GitHub for new version
│
├── [Update Policy]
│   ├── DEFAULT: Auto-update patch versions (1.0.0 → 1.0.1)
│   ├── PROMPT: Minor versions (1.0 → 1.1) — "New features available. Update?"
│   ├── WARN: Major versions (1.x → 2.0) — "Breaking changes. Review before updating."
│   └── NEVER: Don't update during active agent sessions (risk of tool disconnection)
│
├── [Index Freshness]
│   ├── Watcher handles CGC auto-updates on file changes
│   ├── GitNexus: periodic check — "12 files changed since last index. Re-index?"
│   ├── Repomix: detect git changes → "Repomix pack is stale. Regenerate?"
│   └── lean-ctx cache: auto-invalidated on file changes (handled by watcher)
│
└── [Config Migration]
    ├── If matrix.json adds new platforms → auto-detect and add MCP configs
    ├── If a tool changes its MCP format → auto-migrate config entries
    └── If a tool is deprecated → warn + offer removal
```

### "Update Everything" Button

In the desktop app / dashboard:
```
┌──────────────────────────────────────────┐
│  🔄 Updates Available                     │
│                                           │
│  GitNexus:    1.5.2 → 1.6.0  (minor)    │
│  CGC:         0.4.11 → 0.5.0  (minor)    │
│  lean-ctx:    2.1.0 → 2.1.1  (patch)    │
│  Token-Saver: 1.0.0 → 1.1.0  (minor)    │
│                                           │
│  [Update All]  [Review Changes]  [Later] │
└──────────────────────────────────────────┘
```

---

## Idea Block 11: The "Token-Saving Marketplace" — Extensibility

### Problem Statement

We can't bundle every token-saving tool. New ones emerge monthly. Users have different needs (Python devs want different tools than React devs). How do we support discovery without bloating the base install?

### Plugin / Bundle Architecture

```
Base Install (always included):
├── GitNexus
├── CodeGraphContext
├── MetaMCP (aggregator)
├── Token-Saver Core (config engine, dashboard, updater)
└── AGENTS.md protocol

Optional Bundles (one-click install):
├── "JavaScript Bundle" → +Repomix, +ESLint MCP
├── "Python Bundle" → +Ruff MCP, +pytest MCP
├── "Enterprise Bundle" → +security-review, +compliance checks
├── "Context Max Bundle" → +lean-ctx, +Kompact, +ContextLens
├── "Data Science Bundle" → +Jupyter tools, +pandas context
└── "Custom" → user picks individual tools from a marketplace
```

### Community Contributions

- Recipe format (JSON) for tool bundles: what to install, what config to write, what AGENTS.md rules to add
- Submit via GitHub PR or in-app "Suggest a Tool"
- Verified badges for community-reviewed bundles

---

## Idea Block 12: "For the Agent Itself" — Token Efficiency for the Combo's Own Agent

### Problem

The meta-package's own setup agent (the one running `/combo-setup`) also burns tokens. Each phase involves reading AGENTS.md, running commands, checking outputs. For a 8-phase setup, the agent itself uses 30-50K tokens just to do the installation.

### Self-Referential Token Optimization

```
Token-Saver Meta-Package's Own Agent Efficiency:

1. Cached AGENTS.md:
   - The setup protocol is embedded in the agent's system prompt
   - No need to read AGENTS.md — agent already knows the protocol
   - Saves ~5K tokens per setup

2. Compressed tool output:
   - lean-ctx hook compresses `npx gitnexus analyze` output
   - Instead of 2,000 lines of progress, agent sees 50-line summary
   - Saves ~3K tokens per phase

3. Phase skipping:
   - If a phase is already done (config exists, index fresh), skip immediately
   - No "checking if X is installed... checking... yes it is" overhead

4. Parallel execution:
   - Phase 4 (index both tools) runs GitNexus and CGC indexing in parallel
   - Instead of sequential "index GitNexus → wait → index CGC → wait"

5. Minimal output mode:
   - --quiet flag on all commands
   - Agent only reads exit codes and structured output, not raw stdout
```

---

## Idea Block 13: Pricing & Sustainability

### Free Tier (Always)
- All core tools (GitNexus, CGC, Repomix, MetaMCP)
- Basic AGENTS.md injection
- Manual indexing
- Community support

### Pro Tier ($5/month or $50/year)
- Auto-indexing (scheduled + on-change)
- Token savings dashboard
- Priority support
- Advanced diagnostics
- Bundle marketplace access
- Custom AGENTS.md rules

### Enterprise Tier ($20/user/month)
- Team dashboard (see team-wide token savings)
- Centralized config management
- SSO / SAML
- Custom tool bundles
- SLA
- On-premise option

### Open Source Model
- Core tools are open source (already are)
- The meta-package wrapper (installer, dashboard, updater) is the commercial layer
- Community can add tool bundles
- Revenue funds maintenance of the open source core

---

## Idea Block 14: Competitive Analysis — What Exists vs What We'd Build

| Feature | gitnexus_CGC_combo | hatch3r | Drodo | kivun | maestro-bundle | Token-Saver Meta |
|---------|-------------------|---------|-------|-------|----------------|-----------------|
| Bundles code intelligence tools | ✅ (2) | ❌ | ❌ | ❌ | ❌ | ✅ (5+) |
| Bundles output compression | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (lean-ctx) |
| MCP aggregation (token-aware) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (MetaMCP) |
| Desktop installer (no terminal) | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Platform auto-detection | ✅ (17) | ❌ | ❌ | ❌ | ❌ | ✅ (17+) |
| Token savings dashboard | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| AGENTS.md injection | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Smart dependency discovery | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Auto-update | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Plugin marketplace | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-tool synergy | ✅ (2 tools) | ❌ | ❌ | ❌ | ❌ | ✅ (5+ tools) |
| Non-developer UX | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Cross-platform | ✅ | Windows | Cross | Windows | Cross | ✅ |

**Key differentiator:** No existing project bundles ALL token-saving layers. Each focuses on one slice (output compression OR code intelligence OR installer). Token-Saver Meta is the ONLY project that combines all layers with a non-technical user experience.

---

## Priority Roadmap

### Phase 1: Core Meta-Package (2-3 weeks)
1. Extend `config_gen.py` to handle Repomix + lean-ctx + MetaMCP server entries
2. Extend `platforms/matrix.json` with new server definitions
3. Extend AGENTS.md injection with token-saver protocol
4. Add dependency discovery (Idea Block 2)
5. Add failure prevention + user-facing error messages (Idea Block 4)
6. Standalone binary distribution (PyInstaller)
7. VS Code extension scaffold

### Phase 2: "For the Masses" (2-3 weeks)
8. Desktop installer with GUI wizard (Tauri)
9. Token savings dashboard (Idea Block 8)
10. Proactive initialization prompts (Idea Block 7)
11. Auto-update engine (Idea Block 10)

### Phase 3: Ecosystem (3-4 weeks)
12. Plugin marketplace (Idea Block 11)
13. Team/enterprise features
14. Homebrew/Chocolatey/Scoop distribution
15. GitHub Codespaces pre-config

### Phase 4: Polish (ongoing)
16. Social proof / virality features
17. Community bundle contributions
18. Multi-language support
19. Accessibility improvements
20. Performance optimization

---

## Open Questions to Discuss

1. **Lean-ctx vs RTK:** lean-ctx has more capabilities (CCP, 7 read modes, delta compression). RTK is simpler (just hook-based shell compression). Which to bundle as the default? Or both (lean-ctx default, RTK as lightweight alternative)?

2. **MetaMCP vs mcp-unify:** MetaMCP is token-conscious (~1,300 token constant overhead). mcp-unify is more feature-rich (role-based filtering, Python @tool plugins). Which philosophy: maximum token savings or maximum features?

3. **Desktop app framework:** Tauri (Rust, small binary) vs Electron (JS, larger but more developers familiar)? Tauri produces smaller binaries and uses less memory — better for "for the masses." But Electron has more UI component libraries.

4. **Open source model:** MIT (permissive, any use) vs AGPL (copyleft, forces contributions back) vs BSL (source available, commercial use requires license)? MIT maximizes adoption. BSL protects the commercial layer.

5. **Tool discovery vs curation:** Should we auto-detect what tools would help a specific project (Python → suggest Ruff MCP) or curate a fixed set (everyone gets the same 5 tools)? Auto-detection is better UX but more complex.

6. **"Token savings" as primary metric vs feature parity:** Should we optimize ruthlessly for token savings (cut features that don't save tokens) or aim for the best overall developer experience? The token savings angle is our unique differentiator.

7. **Naming:** "Token-Saver Meta" is a working title. Alternatives: "TokenForge", "ContextVault", "PromptPack", "TokenKit", "AICodeBoost", "LLM-Thrift"? The name should convey "saves money" and "easy" to non-technical users.

---

## References

- `C:\Dev\projects\gitnexus_CGC_combo\` — Existing combo project (foundation)
- `C:\Dev\projects\gitnexus_CGC_combo\docs\DESIGN_RATIONALE.md` — Design philosophy
- `C:\Dev\projects\gitnexus_CGC_combo\progress_docs\plans\full.md` — Full implementation plan
- `C:\Dev\projects\gitnexus_CGC_combo\progress_docs\plans\09-distribution-channels.md` — Prior distribution channels plan
- See librarian research above for external tool references

---

*Brainstorm started: 2026-06-13. Next: discuss with the AI and refine scope.*
