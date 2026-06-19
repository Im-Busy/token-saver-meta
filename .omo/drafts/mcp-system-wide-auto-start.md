# Draft: mcp-system-wide-auto-start

## Routing
- **Intent routing**: UNCLEAR — outcome "MCPs properly managed system-wide" is fuzzy; solution shape undefined
- **Rationale**: User knows they want a policy/tool across the whole system, but the specific mechanism (auto-start, service, monitoring, consolidation) is the open design question
- **Classify**: Architecture — spans 5+ modules, affects entire C:\Dev system, involves infrastructure decisions

## Ground Truth — What Exists

### 1. Global MCP Config
- **File**: `C:\Users\Joey Chiu\.config\opencode\opencode.jsonc`
- 21 MCP servers defined (all type: "remote")
- 5 critical: github, filesystem, context7, tavily, exa (direct to OpenCode)
- 16 via mcp-hub proxy at `http://127.0.0.1:9090/mcp`
- All enabled=true

### 2. process-compose (19 servers, ports 9000-9019)
- **File**: `C:\Dev\mcp\process-compose.yaml` (160 lines)
- 9 HTTP-native MCPs: playwright(9001), context7(9002), google-maps(9003), penpot(9004), firecrawl(9005), duckduckgo(9006), markitdown(9007), serena(9008), mcp-searxng(9009)
- 1 github-mcp(9010)
- 1 composer-trade(9011)
- 8 mcp-proxy bridges(9012-9019): time, memory, sequential-thinking, filesystem, chrome-devtools, task-master, fetch, lean-ctx
- All with `restart: always, max_restarts: 10, backoff_seconds: 5`
- **STATUS: NOT RUNNING** — no process-compose process, no services on ports 9000-9019

### 3. mcp-hub (Rust proxy project)
- **Dir**: `C:\Dev\projects\mcp-hub`
- Aggregates 21 MCP servers behind single endpoint
- Phase 1+D2 P0: Complete (proxy, HTTP server, transports, tools)
- Phase 2 P1+: Stubbed (BearerAuthClient, smart caching, encryption)
- **Config file**: `mcp-hub.json` — lists 21 servers, port 8081
- **MEMORY.md says port 9090** — mcp-hub.json still has 8081 → **PORT MISMATCH**
- **STATUS: NOT RUNNING** — port 9090 closed
- **opencode.jsonc expects port 9090** — would fail even if started with current config

### 4. Docker MCP Services
- **Script**: `C:\Dev\scripts\start-mcp-services.ps1` (268 lines)
- graphiti(8000), trendradar(3334), langfuse(3000)
- **STATUS: UNKNOWN** — check-mcp-health.ps1 timed out; Docker status unconfirmed

### 5. Management Scripts
- `start-mcp-services.ps1` — Start/Stop/Status for Docker + process-compose
- `check-mcp-health.ps1` — Parse opencode.jsonc, enable all MCPs, pre-cache packages, health check
- `/start-all-mcp` skill — 4-phase orchestration
- **SKILL.md has bug**: process-compose command uses `-f` flag (not supported), needs `--config`

### 6. Other MCP-Aware Projects (from background tasks)
- `investment_trying` — has `src/mcp/` directory
- `token-saver-meta` — has `mcp_installer.py`, `config_examples/opencode-mcp.json`, MCP servers referenced throughout
- `browser-goat` — has `mcp_server.py`, `auto_start_recipes/`, `src/servers/mcp_server_with_*
- `skills_arsenal_for_publishing` — has `mcp-search-strategy` skill
- `gitnexus_CGC_combo` — has `docs/MCP_CONFIGS.md`
- `C:\Dev\tools\cline-MCP\` — has `.mcp.json`, 8 source files
- `C:\Dev\tools\mcp-stress-test\` — has `stress-mcp.ps1`

### 7. Port Registry
- **File**: `C:\Dev\mcp\PORT-REGISTRY.md`
- Documents all 24 MCP server ports

## Core Problems Identified

| # | Problem | Severity | Evidence |
|---|---------|----------|----------|
| P1 | **No auto-start mechanism** — nothing starts MCPs on boot/project-open | CRITICAL | process-compose not running, mcp-hub not running, no Windows Service |
| P2 | **Two overlapping systems** — process-compose AND mcp-hub both manage same servers | HIGH | process-compose.yaml manages 19 servers, mcp-hub.json manages same 21 |
| P3 | **Config mismatch** — mcp-hub.json port 8081 vs MEMORY.md + opencode.jsonc port 9090 | HIGH | mcp-hub.json:131 "port": 8081 
| P4 | **Skill command syntax outdated** — SKILL.md uses `-f` flag, process-compose expects `--config` | MEDIUM | process-compose --help shows no -f shorthand |
| P5 | **No health monitoring daemon** — health checks are manual, no continuous monitoring | MEDIUM | check-mcp-health.ps1 is one-shot, not a daemon |
| P6 | **System-wide policy not documented** — global opencode.jsonc works but projects don't know | MEDIUM | No AGENTS.md section explaining inheritance |
| P7 | **mcp-hub incomplete** — Phase 2 P1+ missing (BearerAuth, caching, encryption) | LOW | MEMORY.md lists pending P1 tasks |

## Architecture Decision (from mcp-hub MEMORY.md)

> "Hybrid: 5 critical servers (github, filesystem, context7, tavily, exa) connect directly to OpenCode. 16 remaining servers managed by mcp-hub proxy at localhost:9090/mcp."

**This is the already-decided target architecture. The problem is it was never fully deployed.**

## Components (Topology Lock)

1. **mcp-hub** — The Rust proxy that aggregates 16 non-critical MCP servers at port 9090
2. **Critical servers** — 5 servers connecting directly to OpenCode (via process-compose or direct)
3. **Auto-start service** — Windows mechanism to launch everything on boot
4. **Health monitoring** — Daemon that checks MCP health and reports status
5. **System-wide policy documentation** — AGENTS.md section explaining how MCPs work across projects
6. **process-compose consolidation** — Migrate/eliminate process-compose in favor of mcp-hub

## Open Assumptions (adopted defaults with rationale)

| # | Assumption | Default Adopted | Rationale | Reversible? |
|---|-----------|----------------|-----------|-------------|
| A1 | mcp-hub is the canonical proxy | Yes — adopt the already-decided hybrid architecture | The architecture decision was already made; it just wasn't deployed | Yes — can revert to process-compose-only |
| A2 | Windows Service via nssm | Use nssm (Non-Sucking Service Manager) to run mcp-hub as a Windows Service | Industry standard for wrapping arbitrary executables as Windows Services; zero code changes needed | Yes — can switch to Scheduled Task or sc.exe |
| A3 | process-compose eliminated for non-critical servers | All 16 non-critical servers move to mcp-hub management | Avoids dual-management complexity; mcp-hub provides better tool search, prefixing, graceful degradation | Yes — can keep process-compose as fallback |
| A4 | Critical servers stay in process-compose | 5 critical servers (github, filesystem, context7, tavily, exa) stay process-compose managed | MEMORY.md explicitly marks these as "connect directly to OpenCode for maximum stability" | Yes |
| A5 | Health check daemon via Scheduled Task | PowerShell script triggered every 5 minutes via Task Scheduler | Windows-native, no extra dependency, uses existing check-mcp-health.ps1 | Yes — can switch to systemd timer (WSL) or service |
| A6 | mcp-hub port fixed to 9090 | Set mcp-hub.json port to 9090 | MEMORY.md and opencode.jsonc already agree on 9090 | No — port 8081 is wrong |
| A7 | No Docker for mcp-hub servers | Servers run via npx/uvx (stdio), managed by mcp-hub | Current mcp-hub config already uses stdio transport; Docker layer unnecessary until Phase 3 | Yes — can add Docker later |

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| mcp-hub has bugs at scale | Medium | Phase 2 P0 tested with real transport; 18/18 servers confirmed working in MEMORY.md. Verify before deploying. |
| nssm requires admin | Low | One-time `nssm install` needs admin; service auto-starts thereafter |
| Port conflicts | Low | PORT-REGISTRY.md documents all 24 ports; mcp-hub at 9090 is clear |
| process-compose removal breaks critical servers | Medium | Keep critical 5 in process-compose; only remove non-critical overlap |

## Pending Approval Gates
- status: awaiting-approval
- pending action: present brief, wait for user okay
- approach: 8 tasks over 4 waves — Fix skills + legacy status (Wave 0) → Auto-start configs (Wave 1) → Monitoring + docs + MCP consolidation (Wave 2) → E2E verification (Wave 3) → Final review (F1-F4)

## Metis Gap Analysis
Complete. 4 contradictions (C1-C4), 6 missing constraints (M1-M6), 4 scope-creep risks (S1-S4), 6 unvalidated assumptions (A1-A6) identified.

**Already addressed in final plan:**
- C1 (port mismatch): Task 2 fixes mcp-hub.json 8081→9090 ✅
- C2 (hybrid 6 vs 21 entries): Task 7 consolidates, marks mcp-hub legacy ✅
- C3 (start-all-mcp no mcp-hub awareness): By design — mcp-hub is legacy. Skill correctly references process-compose ✅
- S1 (NSSM scope creep): Plan uses Task Scheduler, not NSSM ✅
- S2 (health daemon creep): Plan uses Scheduled Task with existing check-mcp-health.ps1, not a daemon ✅
- S3 (migration scope creep): Explicitly NOT doing — "Must NOT have" section blocks architecture changes ✅
- Self-grill (Startup folder > NSSM): Task Scheduler chosen as middle ground — logon trigger like Startup folder, but with retry-on-failure ✅

**Folded into plan:**
- C4 (process-compose count 11→19): Task 1 scope expanded to fix count in SKILL.md
- M4 (port 9090 availability): Task 2 QA adds `netstat` verification

## Momus Review
Will run dual Momus + Codex CLI after user approves (UNCLEAR path = auto high-accuracy).
