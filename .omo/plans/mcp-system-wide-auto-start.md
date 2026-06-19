# mcp-system-wide-auto-start - Work Plan

## TL;DR (For humans)

**What you'll get:** All 22 MCP servers auto-start on Windows boot, survive crashes via auto-restart, and are monitored continuously. A one-command health dashboard shows status. Every project in C:\Dev inherits MCPs from the global config — no per-project setup.

**Why this approach:** The heavy lifting is already done — 10/14 tasks from the MCP Layered Reliability migration are complete. The remaining work is the last 5%: NSSM auto-start (Task 13 never finished), health monitoring daemon, system-wide policy docs, and a start-all-mcp shortcut. The architecture (process-compose supervising 20 servers with auto-restart, plus Docker MCPs, plus hosted remotes) was decided and built already.

**What it will NOT do:** Will NOT add new MCP servers. Will NOT change the architecture (process-compose stays, mcp-hub stays legacy). Will NOT containerize anything. Will NOT create a startup UI or tray icon. Will NOT auto-update MCP packages.

**Effort:** Short (2-4 hours)
**Risk:** Low — all components exist; only wiring + documentation needed
**Decisions I made for you:**
- **process-compose auto-start via Windows Task Scheduler** (not NSSM) — avoids admin requirement, uses existing mechanism, works for user-session processes
- **mcp-hub stays LEGACY** — NOT started automatically. The per-server mcp-proxy bridge architecture in process-compose.yaml is the current production path
- **Health monitoring via Scheduled Task** — existing check-mcp-health.ps1, triggered every 10 min
- **System-wide policy via global opencode.jsonc** — already works; just needs documentation in AGENTS.md

Your next move: Approve to write the full detailed plan, or say "no" to any decision above. Full execution detail follows below.

---

> TL;DR (machine): Short, Low risk — wire NSSM/scheduled-task auto-start for process-compose + health daemon + policy docs. Infrastructure already built; just needs persistence.

## Scope
### Must have
- **Auto-start**: process-compose + Docker MCP services start automatically on boot/login
- **Auto-restart**: process-compose already handles restarting crashed MCPs; ensure process-compose itself restarts if it crashes
- **Health monitoring**: automated health check runs periodically, results logged
- **System-wide policy**: documentation in AGENTS.md explaining how MCPs are managed globally
- **Fix process-compose command syntax** in `/start-all-mcp` skill (outdated `-f` flag)
- **Port mismatch fix**: mcp-hub.json port 8081 → 9090 (or mark mcp-hub as legacy)

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO new MCP servers added — this is infrastructure-only
- NO architecture changes — process-compose is the production path
- NO Docker for stdio MCPs — npx/uvx through process-compose is correct
- NO mcp-hub revival — it's a Rust project at Phase 2 P1 that was replaced by process-compose
- NO tray icon, GUI, or system-tray app
- NO auto-update of MCP packages — version pins stay locked
- NO modification to individual MCP server code

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after — infrastructure configs, not application code
- Framework: PowerShell + curl + process-compose CLI
- Evidence: .omo/evidence/task-<N>-mcp-system-wide-auto-start.<ext>

## Execution strategy
### Parallel execution waves

Wave 0: Fix immediate issues (3 tasks, parallel)
Wave 1: Auto-start infrastructure (2 tasks, sequential)
Wave 2: Monitoring + documentation (3 tasks, parallel)
Wave 3: Health check + policy enforcement (2 tasks, sequential)

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
|------|-----------|--------|---------------------|
| 1. Fix skill command syntax | None | None | 2, 3 |
| 2. Fix mcp-hub port + mark legacy | None | None | 1, 3 |
| 3. process-compose auto-start (Task Scheduler) | 1 | 4, 5 | None (sequential) |
| 4. Docker MCP services auto-start | 3 | 8 | None (runs after 3) |
| 5. Health monitoring daemon | None | 8 | 6, 7 |
| 6. Add start-all-mcp AGENTS.md shortcut | None | 8 | 5, 7 |
| 7. Consolidate MCP entries in opencode.jsonc | 2 | 8 | 5, 6 |
| 8. End-to-end verification | 3, 4, 5, 6, 7 | F1-F4 | None (sequential) |
| F1. Plan compliance audit | 8 | None | F2, F3, F4 |
| F2. Code quality review | 8 | None | F1, F3, F4 |
| F3. Real QA — kill-test + health check | 8 | None | F1, F2, F4 |
| F4. Scope fidelity check | 8 | None | F1, F2, F3 |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Fix `/start-all-mcp` skill command syntax and add process-compose to auto-start script
  What to do:
    In `C:\Dev\skills\start-all-mcp\SKILL.md` Phase 2.5, replace `-f` flag with `--config`:
    FROM: `process-compose.exe up -f C:\Dev\mcp\process-compose.yaml -p 11999 -t=false`
    TO:   `process-compose.exe up --config C:\Dev\mcp\process-compose.yaml --port 11999 --tui=false`
    
    In `C:\Dev\scripts\start-mcp-services.ps1`:
    - Update Start-ProcessCompose function line 135 to use `--config` and `--port` flags (not short forms)
    - Update process list commands to use `--port` not `-p` (line 152: `process list --port 11999` with no config flag)
    - Add `--keep-project` flag to prevent process-compose from cleaning up on exit
    
  Must NOT do:
    - Do NOT change the port numbers or server configuration
    - Do NOT add new MCP servers
    - Do NOT remove the `--tui=false` or `--keep-project` flags
    
  Parallelization: Wave 0 | Blocked by: None | Blocks: None
    
  References:
    - C:\Dev\skills\start-all-mcp\SKILL.md:95-98 (Phase 2.5 commands)
    - C:\Dev\scripts\start-mcp-services.ps1:133-145 (Start-ProcessCompose, Stop-ProcessCompose)
    - C:\Dev\scripts\start-mcp-services.ps1:147-170 (Get-ProcessComposeStatus)
    - process-compose --help output shows: `--port int`, `--config string`, no `-f` or `-p` shorthand
    
  Acceptance criteria:
    - `grep "process-compose.exe.*-f" C:\Dev\skills\start-all-mcp\SKILL.md` returns zero matches
    - `grep "process-compose.exe.*--config" C:\Dev\skills\start-all-mcp\SKILL.md` returns matches
    - `grep '"-f"' C:\Dev\scripts\start-mcp-services.ps1` returns zero matches
    - All process-compose command references use long-form `--config` and `--port` flags
    
  QA scenarios:
    Happy: Run `Get-Content C:\Dev\skills\start-all-mcp\SKILL.md | Select-String "process-compose"` → all flags are long-form (`--config`, `--port`, `--tui=false`). No short flags `-f`, `-p`, `-t`.
      Evidence: .omo/evidence/task-1-skill-syntax-fixed.txt
    Happy: Run `Get-Content C:\Dev\scripts\start-mcp-services.ps1 | Select-String "process-compose"` → all command invocations use long-form flags.
      Evidence: .omo/evidence/task-1-script-flags-fixed.txt
  
  Commit: Y | fix(mcp): correct process-compose command syntax to long-form flags

- [ ] 2. Fix mcp-hub port mismatch and mark as legacy
  What to do:
    In `C:\Dev\projects\mcp-hub\mcp-hub.json` line 131, change port from 8081 to 9090:
    FROM: `"port": 8081,`
    TO:   `"port": 9090,`
    
    Add a LEGACY.md note at `C:\Dev\projects\mcp-hub\LEGACY.md`:
    ```markdown
    # mcp-hub — LEGACY (superseded 2026-06-18)
    mcp-hub was the original MCP aggregation proxy (Phase 1+D2 P0 complete, Phase 2 P1+ stubbed).
    It was superseded by the process-compose + per-server mcp-proxy bridge architecture in:
    - C:\Dev\mcp\process-compose.yaml (20 supervised MCP servers)
    - C:\Users\Joey Chiu\.config\opencode\opencode.jsonc (17 remote + 8 local MCP entries)
    
    mcp-hub's Rust code (proxy aggregation, tool search, clipboard memory) is retained for
    reference and potential Phase 2 P1+ resurrection, but it is NOT part of the active
    MCP infrastructure. Do NOT start it. Do NOT add it to auto-start.
    ```
    
    Also update `C:\Dev\projects\mcp-hub\MEMORY.md` "mcp-hub running" line to show "LEGACY — not running".
    
  Must NOT do:
    - Do NOT delete mcp-hub code — it's retained for reference
    - Do NOT modify any mcp-hub Rust source code
    - Do NOT change any other mcp-hub.json settings
    
  Parallelization: Wave 0 | Blocked by: None | Blocks: None
    
  References:
    - C:\Dev\projects\mcp-hub\mcp-hub.json:131 ("port": 8081)
    - C:\Dev\projects\mcp-hub\MEMORY.md:23 ("mcp-hub running: 18/18 servers, 173 tools, port 9090")
    - C:\Dev\.omo\plans\mcp-layered-reliability.md:1-14 (migration plan that replaced mcp-hub)
    - C:\Dev\mcp\process-compose.yaml (current production MCP supervisor)
    
  Acceptance criteria:
    - `grep "port.. 8081" C:\Dev\projects\mcp-hub\mcp-hub.json` returns zero matches
    - `grep "port.. 9090" C:\Dev\projects\mcp-hub\mcp-hub.json` matches on the http_server.port line
    - `C:\Dev\projects\mcp-hub\LEGACY.md` exists with correct legacy notice
    - MEMORY.md line 23 updated to reflect legacy status
    
  QA scenarios:
    Happy: `Get-Content C:\Dev\projects\mcp-hub\mcp-hub.json | ConvertFrom-Json | Select-Object -ExpandProperty http_server | Select-Object -ExpandProperty port` → output is 9090
      Evidence: .omo/evidence/task-2-port-fixed.txt
    Happy: `Test-Path C:\Dev\projects\mcp-hub\LEGACY.md` → True
      Evidence: .omo/evidence/task-2-legacy-doc.txt
  
  Commit: Y | fix(mcp): fix mcp-hub port 8081→9090, mark as legacy

- [ ] 3. Configure process-compose auto-start via Windows Task Scheduler
  What to do:
    Create a Windows Scheduled Task that starts process-compose on user login. Task Scheduler is preferred over NSSM because:
    - No admin required (NSSM service creation needs elevation)
    - User-session processes need user context (MCPs need access to user's npm cache, env vars, API keys)
    - Task Scheduler has built-in retry on failure
    
    Create task XML at `C:\Dev\mcp\process-compose-startup.xml`:
    ```xml
    <?xml version="1.0" encoding="UTF-16"?>
    <Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
      <RegistrationInfo>
        <Description>Start MCP process-compose supervisor on user login. Manages 20 MCP servers with auto-restart.</Description>
      </RegistrationInfo>
      <Triggers>
        <LogonTrigger>
          <Enabled>true</Enabled>
          <UserId>Joey Chiu</UserId>
        </LogonTrigger>
      </Triggers>
      <Principals>
        <Principal id="Author">
          <UserId>Joey Chiu</UserId>
          <LogonType>InteractiveToken</LogonType>
          <RunLevel>LeastPrivilege</RunLevel>
        </Principal>
      </Principals>
      <Settings>
        <Enabled>true</Enabled>
        <AllowStartOnDemand>true</AllowStartOnDemand>
        <RestartOnFailure>
          <Interval>PT1M</Interval>
          <Count>3</Count>
        </RestartOnFailure>
        <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
        <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
      </Settings>
      <Actions>
        <Exec>
          <Command>C:\Dev\tools\process-compose.exe</Command>
          <Arguments>up --config C:\Dev\mcp\process-compose.yaml --port 11999 --tui=false --keep-project</Arguments>
          <WorkingDirectory>C:\Dev\mcp</WorkingDirectory>
        </Exec>
      </Actions>
    </Task>
    ```
    
    Also create a `C:\Dev\mcp\start-process-compose.ps1` helper script for manual start:
    ```powershell
    # Manual start for process-compose MCP supervisor
    $pc = Get-Process -Name "process-compose" -ErrorAction SilentlyContinue
    if ($pc) {
        Write-Host "process-compose already running (PID $($pc.Id))" -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Starting MCP process supervisor..." -ForegroundColor Cyan
    Start-Process -FilePath "C:\Dev\tools\process-compose.exe" -ArgumentList "up --config C:\Dev\mcp\process-compose.yaml --port 11999 --tui=false --keep-project" -NoNewWindow
    Start-Sleep -Seconds 5
    Write-Host "MCP supervisor started." -ForegroundColor Green
    ```
    
  Must NOT do:
    - Do NOT use NSSM — Task Scheduler is sufficient and avoids admin requirement
    - Do NOT set trigger as "At startup" — use "At logon" so user env vars are available
    - Do NOT start process-compose twice (check for existing process first in helper script)
    
  Parallelization: Wave 1 | Blocked by: 3 (start-mcp-services.ps1 must have updated process-compose flags) | Blocks: 5 (Docker auto-start), 7 (verification)
    
  References:
    - C:\Dev\.omo\plans\mcp-layered-reliability.md:877-955 (Task 13 — original NSSM plan, never completed)
    - C:\Dev\mcp\process-compose.yaml (20-server supervision config)
    - C:\Dev\scripts\start-mcp-services.ps1:133-145 (existing Start-ProcessCompose function)
    - process-compose --help (flags: --port, --config, --tui, --keep-project)
    
  Acceptance criteria:
    - `Test-Path C:\Dev\mcp\process-compose-startup.xml` → True
    - `Test-Path C:\Dev\mcp\start-process-compose.ps1` → True
    - Task XML validates: `$task = [xml](Get-Content C:\Dev\mcp\process-compose-startup.xml)` succeeds
    - Task XML command path: `C:\Dev\tools\process-compose.exe` (verified exists)
    - Task XML uses `--config` and `--port` long-form flags (no short flags)
    - Helper script checks for existing process before starting
    
  QA scenarios:
    Happy: Run `C:\Dev\mcp\start-process-compose.ps1` → process-compose starts, `Get-Process process-compose` returns a process. Run it again → "already running" message, no second instance.
      Evidence: .omo/evidence/task-4-startup-script.txt
    Happy: Register task: `schtasks /create /xml C:\Dev\mcp\process-compose-startup.xml /tn "MCP-ProcessCompose" /f` → returns success. Then `schtasks /query /tn "MCP-ProcessCompose"` → shows task as Ready.
      Evidence: .omo/evidence/task-4-task-registered.txt
  
  Commit: Y | feat(mcp): add process-compose auto-start via Windows Task Scheduler

- [ ] 4. Configure Docker MCP services auto-start
  What to do:
    Create a Scheduled Task or update the existing start-mcp-services.ps1 to ensure Docker MCP services start alongside process-compose. Since Docker Desktop already auto-starts on login, the MCP Docker services just need `docker compose up -d` on login.
    
    Create `C:\Dev\mcp\start-docker-mcps.ps1`:
    ```powershell
    # Start all Docker MCP backend services
    $ErrorActionPreference = "Continue"
    
    # Check Docker is running
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker not running. Start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    $services = @(
        @{ Name="graphiti";   Dir="C:\Dev\docker-stuff\graphiti";   Port=8000 },
        @{ Name="trendradar"; Dir="C:\Dev\docker-stuff\trendradar"; Port=3334 },
        @{ Name="langfuse";   Dir="C:\Dev\docker-stuff\langfuse";   Port=3030 },
        @{ Name="searxng";    Dir="C:\Dev\docker-stuff\searxng-docker"; Port=8080 }
    )
    
    foreach ($svc in $services) {
        Write-Host "Starting $($svc.Name)..." -ForegroundColor Yellow
        docker compose -f "$($svc.Dir)\docker-compose.yml" up -d 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  $($svc.Name) started (port $($svc.Port))" -ForegroundColor Green
        } else {
            Write-Host "  $($svc.Name) FAILED" -ForegroundColor Red
        }
    }
    ```
    
    Register as a 30-second-delayed logon task (Docker needs time to initialize):
    ```powershell
    schtasks /create /tn "MCP-DockerServices" /tr "powershell -ExecutionPolicy Bypass -File C:\Dev\mcp\start-docker-mcps.ps1" /sc onlogon /delay 0000:30 /f
    ```
    
  Must NOT do:
    - Do NOT try to start Docker Desktop itself — it auto-starts
    - Do NOT override existing docker-compose files
    - Do NOT use `docker compose` on files that don't exist (check dirs first)
    
  Parallelization: Wave 1 | Blocked by: 3 (process-compose auto-start must work first) | Blocks: 8
    
  References:
    - C:\Dev\scripts\start-mcp-services.ps1:28-51 (Docker service definitions)
    - C:\Dev\docker-stuff\graphiti\docker-compose.yml
    - C:\Dev\docker-stuff\trendradar\docker-compose.yml
    - C:\Dev\docker-stuff\langfuse\docker-compose.yml
    - C:\Dev\docker-stuff\searxng-docker\docker-compose.yaml
    
  Acceptance criteria:
    - `Test-Path C:\Dev\mcp\start-docker-mcps.ps1` → True
    - Script references all 4 Docker MCP services with correct compose paths
    - `schtasks /query /tn "MCP-DockerServices"` shows registered task
    
  QA scenarios:
    Happy: `Test-Path C:\Dev\docker-stuff\graphiti\docker-compose.yml` → True, `Test-Path C:\Dev\docker-stuff\trendradar\docker-compose.yml` → True, etc. All 4 compose files exist.
      Evidence: .omo/evidence/task-5-compose-files.txt
    Happy: Script runs without Docker: `powershell -File C:\Dev\mcp\start-docker-mcps.ps1` → "Docker not running" message, exit code 1 (expected — Docker may not be running at check time).
      Evidence: .omo/evidence/task-5-script-runs.txt
  
  Commit: Y | feat(mcp): add Docker MCP services auto-start on login

- [ ] 5. Configure health monitoring daemon
  What to do:
    Create a Scheduled Task that runs `check-mcp-health.ps1` every 10 minutes and logs results. The task should:
    - Run check-mcp-health.ps1 with `-Format text`
    - Log output to `C:\Dev\mcp\health-logs\health-YYYY-MM-DD-HHmm.txt`
    - On degraded/unhealthy status, write a WARNING event to Windows Event Log
    
    Create `C:\Dev\mcp\health-monitor.ps1`:
    ```powershell
    # MCP Health Monitor — runs every 10 min via Task Scheduler
    $logDir = "C:\Dev\mcp\health-logs"
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    
    $timestamp = Get-Date -Format "yyyy-MM-dd-HHmm"
    $logFile = "$logDir\health-$timestamp.txt"
    
    # Run health check (use text format for human-readable logs)
    $result = & "C:\Dev\scripts\check-mcp-health.ps1" -Format text 2>&1
    
    # Save to log file
    $result | Out-File -FilePath $logFile -Encoding UTF8
    
    # Parse JSON summary for alerting
    $jsonResult = & "C:\Dev\scripts\check-mcp-health.ps1" -Format json 2>&1 | ConvertFrom-Json
    
    if ($jsonResult.summary.overall -eq "degraded") {
        $broken = $jsonResult.summary.brokenMcp
        Write-EventLog -LogName Application -Source "MCP-Health" -EntryType Warning -EventId 1001 -Message "MCP Health: $broken servers broken — see $logFile"
    }
    if ($jsonResult.summary.overall -eq "unhealthy") {
        Write-EventLog -LogName Application -Source "MCP-Health" -EntryType Error -EventId 1002 -Message "MCP Health: CRITICAL — see $logFile"
    }
    
    # Cleanup: keep only last 48 hours of logs
    Get-ChildItem $logDir -Filter "health-*.txt" | 
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-48) } |
        Remove-Item -Force
    ```
    
    Register as recurring task:
    ```powershell
    schtasks /create /tn "MCP-HealthMonitor" /tr "powershell -ExecutionPolicy Bypass -File C:\Dev\mcp\health-monitor.ps1" /sc minute /mo 10 /f
    ```
    
    Also create a one-shot manual health dashboard script at `C:\Dev\mcp\health-dashboard.ps1`:
    ```powershell
    # Quick MCP health dashboard — run anytime
    Write-Host "=== MCP Health Dashboard ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
    Write-Host ""
    & "C:\Dev\scripts\check-mcp-health.ps1" -Format text
    ```
    
  Must NOT do:
    - Do NOT send desktop notifications — output to log files only
    - Do NOT auto-remediate — monitoring only, no automated fixes
    - Do NOT retain logs > 48 hours
    
  Parallelization: Wave 2 | Blocked by: None (can run independently) | Blocks: 8
    
  References:
    - C:\Dev\scripts\check-mcp-health.ps1 (existing health checker)
    - C:\Dev\.omo\plans\mcp-layered-reliability.md:75 (DoD mentions check-mcp-health.ps1)

  Acceptance criteria:
    - `Test-Path C:\Dev\mcp\health-monitor.ps1` → True
    - `Test-Path C:\Dev\mcp\health-dashboard.ps1` → True
    - Running `health-monitor.ps1` creates a log file at `C:\Dev\mcp\health-logs\health-*.txt`
    - Log file contains MCP status output (not empty)
    - `schtasks /query /tn "MCP-HealthMonitor"` shows registered task
    
  QA scenarios:
    Happy: `powershell -File C:\Dev\mcp\health-monitor.ps1` → creates log file. `Get-Content C:\Dev\mcp\health-logs\health-*.txt` → contains "OpenCode MCP Health Dashboard" header.
      Evidence: .omo/evidence/task-6-health-log.txt
    Happy: `powershell -File C:\Dev\mcp\health-dashboard.ps1` → displays health table with MCP count, enabled/healthy/broken summary.
      Evidence: .omo/evidence/task-6-dashboard.txt
  
  Commit: Y | feat(mcp): add health monitoring daemon with 10-min check interval

- [ ] 6. Add `/start-all-mcp` shortcut to AGENTS.md and document system-wide policy
  What to do:
    Create a SYSTEM-WIDE AGENTS.md addendum at `C:\Dev\.opencode\standards\mcp-policy.md`:
    ```markdown
    # MCP Policy — System-Wide (ALL projects)
    
    ## How MCPs Work
    
    All MCP servers are defined ONCE in your global OpenCode config:
    `C:\Users\Joey Chiu\.config\opencode\opencode.jsonc`
    
    Every project inherits these MCPs automatically. You do NOT need per-project MCP configuration.
    
    ## Starting MCPs
    
    MCPs auto-start on login. If they aren't running:
    ```
    Run `/start-all-mcp` in any OpenCode session.
    Or: `powershell -File C:\Dev\mcp\start-process-compose.ps1`
    ```
    
    ## Checking MCP Health
    
    ```
    Run: `powershell -File C:\Dev\mcp\health-dashboard.ps1`
    Or: `/start-all-mcp` (Phase 4 shows health dashboard)
    ```
    
    ## Architecture
    
    - **process-compose** (auto-start on login): supervises 20 MCP servers with auto-restart
    - **Docker** (auto-start on login): graphiti, trendradar, langfuse, searxng
    - **Hosted remote**: tavily, exa (always available via internet)
    - **All MCPs use `type: "remote"`** in opencode.jsonc — no stdio processes spawned by OpenCode
    
    ## Troubleshooting
    
    | Symptom | Fix |
    |---------|-----|
    | MCP tools unavailable | Run `/start-all-mcp` |
    | Port conflicts | Check `C:\Dev\mcp\PORT-REGISTRY.md` |
    | process-compose not running | `powershell -File C:\Dev\mcp\start-process-compose.ps1` |
    | Health check failing | `powershell -File C:\Dev\mcp\health-dashboard.ps1` |
    | Docker services down | `docker compose -f C:\Dev\docker-stuff\[service]\docker-compose.yml up -d` |
    ```
    
    Also update `C:\Dev\projects\token-saver-meta\AGENTS.md` to add under "Session Start Protocol":
    ```
    0. **`C:\Dev\.opencode\standards\mcp-policy.md`** — System-wide MCP management policy
    
    And add as a session-start action:
    - **Check MCP health**: Run `powershell -File C:\Dev\mcp\health-dashboard.ps1` at session start if MCP tools appear unavailable
    ```
    
  Must NOT do:
    - Do NOT add per-project MCP configuration to individual project AGENTS.md files
    - Do NOT modify the existing AGENTS.md structure — append only
    - Do NOT add troubleshooting steps for problems this plan doesn't fix
    
  Parallelization: Wave 2 | Blocked by: None | Blocks: None (documentation only)
    
  References:
    - C:\Dev\.opencode\standards\workspace-conventions.md (existing global standards)
    - C:\Dev\projects\token-saver-meta\AGENTS.md:17-18 (session start protocol)
    - C:\Dev\skills\start-all-mcp\SKILL.md (skill reference)
    - C:\Dev\mcp\PORT-REGISTRY.md (port reference)
    
  Acceptance criteria:
    - `Test-Path C:\Dev\.opencode\standards\mcp-policy.md` → True
    - Policy doc includes: How MCPs Work, Starting MCPs, Checking Health, Architecture, Troubleshooting sections
    - Policy doc mentions `/start-all-mcp` as the primary start command
    - AGENTS.md session start protocol references mcp-policy.md
    
  QA scenarios:
    Happy: `Get-Content C:\Dev\.opencode\standards\mcp-policy.md | Select-String "process-compose"` → matches for architecture section.
      Evidence: .omo/evidence/task-6a-policy-doc.txt
    Happy: `Get-Content C:\Dev\projects\token-saver-meta\AGENTS.md | Select-String "mcp-policy"` → matches (reference in session start protocol).
      Evidence: .omo/evidence/task-6a-agents-updated.txt
  
  Commit: Y | docs(mcp): add system-wide MCP policy and /start-all-mcp shortcut

- [ ] 7. Consolidate overlapping MCP entries in opencode.jsonc
  What to do:
    The current opencode.jsonc has ALL 20 servers as direct entries PLUS `mcp-hub` as an aggregator. Since mcp-hub is now legacy (not running), and all servers are already direct, there's nothing to fix — the architecture is correct. This task is verification-only.
    
    Verify the current state is correct:
    - 10 HTTP-native MCPs on ports 9001-9010: all enabled, all type: "remote"
    - 8 mcp-proxy bridge MCPs on ports 9012-9019: all enabled, all type: "remote"  
    - 2 hosted remote (tavily, exa): all enabled
    - 1 mcp-hub on port 9090: enabled (but will show "container_down" since it's not running — expected)
    
    Add a comment in opencode.jsonc above the mcp-hub entry:
    ```jsonc
    // LEGACY — mcp-hub is superseded by per-server mcp-proxy bridges in process-compose.yaml.
    // Keep as disabled unless resurrecting the Rust proxy. See C:\Dev\projects\mcp-hub\LEGACY.md.
    ```
    
    Optionally: set `"enabled": false` on mcp-hub to silence health check warnings.
    
  Must NOT do:
    - Do NOT remove the mcp-hub entry — keep it as disabled reference
    - Do NOT change any other MCP entries
    - Do NOT disable the critical 5 servers
    
  Parallelization: Wave 2 | Blocked by: None | Blocks: None
    
  References:
    - C:\Users\Joey Chiu\.config\opencode\opencode.jsonc:69 (mcp-hub entry)
    - C:\Dev\projects\mcp-hub\LEGACY.md (created in Todo 2)
    
  Acceptance criteria:
    - opencode.jsonc mcp-hub entry has legacy comment referencing LEAGACY.md
    - mcp-hub entry has `"enabled": false` (optional — only if user agrees)
    - All 20 other MCP entries remain unchanged
    
  QA scenarios:
    Happy: Count enabled MCPs in opencode.jsonc → 20 (not 21, if mcp-hub disabled).
      Evidence: .omo/evidence/task-6b-mcp-count.txt
  
  Commit: Y | fix(mcp): mark mcp-hub as legacy in opencode.jsonc

- [ ] 8. End-to-end verification — auto-start + health + kill-test
  What to do:
    Run comprehensive verification that the auto-start system works end-to-end:
    
    1. **Clean state**: Stop all MCP services
       ```powershell
       Stop-Process -Name "process-compose" -Force -ErrorAction SilentlyContinue
       docker compose -f C:\Dev\docker-stuff\graphiti\docker-compose.yml down 2>&1 | Out-Null
       docker compose -f C:\Dev\docker-stuff\trendradar\docker-compose.yml down 2>&1 | Out-Null
       docker compose -f C:\Dev\docker-stuff\langfuse\docker-compose.yml down 2>&1 | Out-Null
       ```
    
    2. **Manual start**: Run start-process-compose.ps1
       ```powershell
       powershell -File C:\Dev\mcp\start-process-compose.ps1
       # Wait 30s for MCP initialization
       Start-Sleep -Seconds 30
       ```
    
    3. **Verify all MCPs**: Run health check
       ```powershell
       powershell -File C:\Dev\mcp\health-dashboard.ps1
       ```
    
    4. **Kill-test**: Kill one MCP, verify auto-restart
       ```powershell
       # Find playwright PID
       $proc = Get-Process -Name "node" | Where-Object { $_.CommandLine -match "playwright" }
       Stop-Process -Id $proc.Id -Force
       # Wait 15s for process-compose restart
       Start-Sleep -Seconds 15
       curl http://localhost:9001/mcp  # → should respond
       ```
    
    5. **Health monitor**: Run health-monitor.ps1, verify log created
       ```powershell
       powershell -File C:\Dev\mcp\health-monitor.ps1
       Get-ChildItem C:\Dev\mcp\health-logs\health-*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Head 5
       ```
    
    6. **Docker services**: Start Docker MCPs, verify
       ```powershell
       powershell -File C:\Dev\mcp\start-docker-mcps.ps1
       docker ps --filter "name=graphiti" --filter "name=trendradar" --filter "name=langfuse" --filter "name=searxng"
       ```
    
  Must NOT do:
    - Do NOT skip the kill-test — it proves auto-restart works
    - Do NOT test on a production session — this is a verification sweep, not normal usage
    - Do NOT leave Docker containers running if Docker isn't normally used
    
  Parallelization: Wave 3 | Blocked by: 4, 5, 6, 6a, 6b | Blocks: F1-F4
    
  References:
    - All files created/modified in Todos 1-6b
    - C:\Dev\.omo\plans\mcp-layered-reliability.md:957-1039 (Task 14 — original verification plan)
    
  Acceptance criteria:
    - [ ] process-compose starts and shows Running processes
    - [ ] 20 MCP processes show as Running in process-compose process list
    - [ ] Health dashboard shows all enabled MCPs as healthy or degraded (not unavailable)
    - [ ] Kill-test: playwright (or any MCP) auto-restarts within 15 seconds
    - [ ] Health monitor log file created with timestamp ≤ 2 minutes old
    - [ ] Docker MCP services start (if Docker is running) or gracefully report Docker unavailable
    
  QA scenarios:
    Happy: Full end-to-end: start → health check → kill-test → health monitor → all pass.
      Evidence: .omo/evidence/task-8-e2e-health.txt
    Happy: Kill-test evidence: playwright PID before/after kill → different PID, endpoint responds.
      Evidence: .omo/evidence/task-8-kill-test.txt
    Happy: Health monitor log contains the health dashboard output.
      Evidence: .omo/evidence/task-8-monitor-log.txt
  
  Commit: Y | test(mcp): end-to-end verification of auto-start and health monitoring

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — Verify every "Must have" is met: auto-start configs exist, health monitor runs, policy doc created. Verify every "Must NOT have" is absent: no architecture changes, no new servers, no Docker for stdio, no mcp-hub revival, no GUI/tray, no auto-update.
- [ ] F2. Code quality review — Verify all script files: no hardcoded secrets, correct PowerShell syntax, no dangling references to old flags (`-f`, `-p`), all file paths absolute and verified, all Task Scheduler XML well-formed.
- [ ] F3. Real manual QA — Start from clean state (no process-compose, no Docker MCPs). Run start-process-compose.ps1 → verify 20 MCPs running. Run health-dashboard.ps1 → verify healthy/degraded status. Kill playwright → verify restart within 15s. Run health-monitor.ps1 → verify log file created. Check Task Scheduler tasks registered.
- [ ] F4. Scope fidelity — Verify no scope creep: count new files created (should be ~6-7 scripts/docs), count modified files (should be ~4-5), verify no MCP server code changed, verify no new dependencies installed, verify mcp-hub marked legacy but NOT deleted.

## Commit strategy
One commit per todo (8 commits total). Types: fix (1, 2), feat (4, 5, 6), docs (6a), test (7). Scope: mcp. Messages short and specific.

## Success criteria
1. process-compose auto-starts on user login (via Task Scheduler)
2. Docker MCP services auto-start on user login (via Task Scheduler)
3. Health monitoring runs every 10 minutes, logs to C:\Dev\mcp\health-logs\
4. Any killed MCP auto-restarts within 15 seconds (process-compose restart:always)
5. `/start-all-mcp` skill commands use correct long-form flags
6. System-wide MCP policy documented at C:\Dev\.opencode\standards\mcp-policy.md
7. mcp-hub marked as legacy, port fixed
8. All 20 process-compose MCPs + 2 hosted remote MCPs accessible from any OpenCode project
9. Zero manual intervention needed to start MCPs when beginning work
