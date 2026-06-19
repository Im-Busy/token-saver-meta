# Token Saver Meta — Insight Registry

> **NOTE:** This file contains 24 selected insights. For the COMPLETE list of 37 insights and 22 synergies, see `docs/insights_and_synergies.md`.  
> Pattern adopted from `investment_trying`. Generated 2026-06-13.

**Total Sources:** 61 (44 repos + 17 discussions/additional)
**Total Insights:** Catalogued below

## Insight Format

```
### I{NN} — {Insight Name}
- **Source:** {Source ID from Source Manifest}
- **Category:** {token type or layer}
- **Actionable?** {YES / Pattern / Reference}
- **Summary:** One sentence.
```

---

## Layer 2: Code Intelligence

### I01 — Graph Retrieval Beats File Reading
- **Source:** GitNexus, CGC, tokensave, jcodemunch-mcp, trace-mcp, code-context-engine
- **Category:** T1 (Exploration)
- **Actionable?** YES — core architecture decision
- **Summary:** All 6 code intelligence tools converge on the same insight: query a pre-built graph instead of reading files. Savings: 7x-1507x depending on tool and task.

### I02 — Different Depths, Not Competitors
- **Source:** Our sequential-thinking analysis
- **Category:** T1 (Exploration)
- **Actionable?** YES — tool selection logic
- **Summary:** Code intelligence tools operate at different depths (overview→symbol→structure→impact). They form a PROGRESSION, not alternatives.

### I03 — Static Maps Compress First Sessions
- **Source:** codesight
- **Category:** T1 (Exploration)
- **Actionable?** YES — always generate context map first
- **Summary:** A pre-compiled context map (CODESIGHT.md) saves 7x-91x on first-session exploration. Generate it once, read it every session.

### I04 — Schema Compression Is the #1 Win
- **Source:** TSCG
- **Category:** T6 (Tool Schema)
- **Actionable?** YES — bundle TSCG as first priority
- **Summary:** MCP tool schemas cost ~3K tokens per server per request. TSCG compresses 50-72%. At scale, this is $30K+/month saved.

### I05 — Cards-First Escalation Beats All-Or-Nothing
- **Source:** sdl-mcp
- **Category:** T1 (Exploration)
- **Actionable?** Pattern — Iris Gate Ladder
- **Summary:** Four-rung escalation: Symbol Cards (100 tok) → Graph Slicing → Delta Packs → Raw Code. Only pay for what you need.

### I06 — Cross-Session Memory Compounds
- **Source:** Loom, codex-agent-mem, trace-mcp
- **Category:** T5 (Repeated Knowledge)
- **Actionable?** YES — bundle cross-session memory
- **Summary:** Store symbol summaries across sessions. Loom claims 51x-1507x per session over time. Codex-agent-mem: ~95% on repeated context via hash caching.

---

## Layer 4: Output Compression

### I07 — Hook-Based Compression Is Transparent
- **Source:** RTK, opentoken, omni
- **Category:** T2 (Shell Output)
- **Actionable?** YES — core architecture decision
- **Summary:** Shell output compression via hooks is transparent to the user. No behavior change needed. RTK (62K stars) is the most mature; opentoken (35 stages) is the most comprehensive.

### I08 — Pre-Execution Rewrite > Post-Execution Compression
- **Source:** RTK (PreToolUse)
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — prefer pre-execution
- **Summary:** Making commands denser BEFORE execution (RTK's `rtk git status`) achieves better compression than filtering after. Both can coexist (pre + post).

### I09 — CLI Replacement Complements Compression
- **Source:** ContextSlimAI
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — two approaches, not one
- **Summary:** ContextSlimAI replaces commands entirely (`contextslim grep` vs `grep`). RTK compresses existing commands. Different mechanisms, both useful.

### I10 — Adaptive Compression Responds to Retrieval
- **Source:** omni
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — adaptive softening
- **Summary:** omni tracks when agents retrieve omitted output and softens compression. This prevents over-compression without manual tuning.

---

## Layer 6: Agent Behavior

### I11 — Behavioral Rules Are the Cheapest Win
- **Source:** LG-token-saver, kevin-copilot
- **Category:** T3 (Agent Output) + T7 (Instructions)
- **Actionable?** YES — zero-dependency core
- **Summary:** SKILL.md files with behavioral rules cost nothing to install and save 66-89% on output tokens. Bundle both LG-token-saver and kevin-copilot.

### I12 — Output Style vs Operational Efficiency Are Different
- **Source:** caveman vs LG-token-saver analysis
- **Category:** T3 (Agent Output)
- **Actionable?** Pattern — both needed
- **Summary:** caveman compresses HOW the agent speaks (style). LG-token-saver compresses HOW the agent operates (parallelism, dedup, compaction). Different dimensions.

### I13 — On-Demand Skill Loading Saves 30-40%
- **Source:** PAI #714, graphify #1045
- **Category:** T7 (Instructions)
- **Actionable?** YES — tiered AGENTS.md
- **Summary:** Split large instruction files into core loader (~4K tokens) + on-demand sections. This is the #1 token optimization technique.

### I14 — Mode-Based Tool Loading
- **Source:** opencode #1573, MOS
- **Category:** T6 (Tool Schema) + T7 (Instructions)
- **Actionable?** Pattern — complexity scoring
- **Summary:** "hi" costs 17.7K tokens with all tools loaded. MOS's complexity scoring (0-140) maps task type → tool selection. Token Saver Meta needs light/medium/full modes.

---

## Layer 3: Prompt Compression

### I15 — ML Prompt Compression Requires GPU
- **Source:** LLMLingua
- **Category:** T4 (Prompt Input)
- **Actionable?** YES — optional module with auto-detect
- **Summary:** LLMLingua compresses prompts up to 20x but needs GPU. Make optional. Auto-detect GPU, advise user. LLMLingua-2 (XLM-RoBERTa) is lighter (~1.5GB).

### I16 — Whitespace Removal Is Academically Validated
- **Source:** Deblank (ICSE'26 Distinguished Paper)
- **Category:** T4 (Prompt Input)
- **Actionable?** YES — bundle
- **Summary:** Removing code formatting does NOT degrade LLM accuracy (academically proven). Saves ~34% on C-family, ~9% on Python. Deblank + reformat is bidirectional.

---

## Design Patterns (From Aggregators & Discussions)

### I17 — The Meta-Layer: Complexity Scoring → Config
- **Source:** MOS
- **Category:** Architecture Pattern
- **Actionable?** YES — adopt for Token Saver Meta
- **Summary:** MOS scores task complexity (0-140) and maps to model+thinking+subagent config. This is EXACTLY the meta-layer Token Saver Meta needs.

### I18 — Tiered Memory Architecture
- **Source:** MemOS
- **Category:** Architecture Pattern
- **Actionable?** Pattern — adopt L1→L4 hierarchy
- **Summary:** L1 (raw traces) → L2 (policies) → L3 (world model) → L4 (crystallized skills). Each tier is more compressed. Retrieve at the right abstraction level.

### I19 — Ephemeral Pre-Request Compression
- **Source:** Hermes #14948
- **Category:** Architecture Pattern
- **Actionable?** Pattern — adopt for old tool results
- **Summary:** Compress old tool results to one-line regex summaries BEFORE each API call. Ephemeral (API copy only, doesn't mutate history). 17-82% savings.

### I20 — Externalize Plans to Files
- **Source:** opencode #7579
- **Category:** Agent Protocol
- **Actionable?** YES — AGENTS.md guidance
- **Summary:** Agents should save plans to files, not hold in context. Compaction loses fidelity. Re-read plan after compaction. Built-in tool for plan display.

### I21 — Lazy Spawning — Don't Bootstrap Without Work
- **Source:** Paperclip #373
- **Category:** Agent Protocol
- **Actionable?** YES — setup optimization
- **Summary:** Don't index/spawn tools unless the project needs them. 22 idle agents burned hundreds of thousands of tokens. Pre-check relevance before setup.

### I22 — Provider Cache Optimization
- **Source:** racs
- **Category:** Architecture Pattern
- **Actionable?** Pattern — cache-breakpoint placement
- **Summary:** Arrange prompts to maximize provider-level cache hits. racs achieves 88.1% savings vs naive prompts. Breakpoint placement is non-trivial (timestamps kill cache).

---

## Layer 10: Code Generation Compression (T3) *(Added 2026-06-18)*

### I23 — YAGNI-Ladder Output Compression
- **Source:** ponytail (DietrichGebert)
- **Category:** T3 (Agent Output)
- **Actionable?** YES — bundle alongside caveman
- **Summary:** A YAGNI enforcement ladder (stdlib→native→dependency→one-liner→minimal) cuts ~54% LOC and ~22% tokens across 13 agent platforms. Complements caveman's prose terseness with code minimalism — caveman compresses HOW the agent speaks, ponytail compresses WHAT code it generates. Different mechanisms on same token type = complementary.

## Layer 11: Instruction Optimization (T7) *(Added 2026-06-18)*

### I24 — Skill Document Optimization as Trainable State
- **Source:** SkillOpt (Microsoft)
- **Category:** T7 (Instructions)
- **Actionable?** YES — optional module for skill optimization
- **Summary:** Agent skills can be treated as trainable artifacts via epochs/mini-batches/validation gates. Output: compact `best_skill.md` (300-2,000 tokens) with zero inference-time cost. +23.5pt accuracy gain on GPT-5.5 while producing minimal-token artifacts. "Sleep" preview enables nightly offline self-evolution — skills optimize themselves while you sleep.
