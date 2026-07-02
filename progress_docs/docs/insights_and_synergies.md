# Token Saver Meta — Complete Insights & Synergies

> Generated 2026-06-13. Updated 2026-06-18 (Batch 3: ponytail + SkillOpt). Every actionable insight from 61+ sources, plus how they combine and compound.

---

# PART 1: ALL INSIGHTS (39)

---

## Layer 1: Architecture & Design Principles

### I01 — Graph Retrieval Beats File Reading
- **Source:** GitNexus, CGC, tokensave, jcodemunch-mcp, trace-mcp, code-context-engine, Loom
- **Category:** T1 (Exploration)
- **Actionable?** YES — core architecture decision
- **Evidence:** 6 independent tools converge on same insight. Measured: 7x-1507x depending on tool.
- **Summary:** Pre-built code graph queries replace raw file reads. Agent asks "who calls X?" instead of grepping.

### I02 — Different Depths, Not Competitors
- **Source:** Sequential-thinking analysis (23 steps)
- **Category:** T1 (Exploration)
- **Actionable?** YES — tool selection logic for AGENTS.md
- **Evidence:** codesight (breadth) → token-savior (symbol) → CGC (structure) → GitNexus (impact). Each answers different question.
- **Summary:** Code intelligence tools form a PROGRESSION: overview→symbol→structure→impact. Never pick one — use all.

### I03 — Static Maps Compress First Sessions
- **Source:** codesight README benchmarks (3 real projects)
- **Category:** T1 (Exploration)
- **Actionable?** YES — always generate first
- **Evidence:** SaaS A: 46,020→3,936 tokens (11.7x). SaaS C: 47,450→4,162 (11.4x). With wiki: 83.7x-131.8x.
- **Summary:** One `npx codesight` command replaces 40K+ tokens of manual file exploration every session.

### I04 — Schema Compression Is the #1 Win at Scale
- **Source:** TSCG (SKZL-AI)
- **Category:** T6 (Tool Schema)
- **Actionable?** YES — bundle TSCG MCP proxy
- **Evidence:** 50-72% on JSON Schema. At 5 servers × 20 tools × ~3K tokens each = 15K+ tokens burned per request. TSCG drops to ~7K.
- **Summary:** MCP schema overhead is the single largest token cost in multi-tool setups. Compress it first.

### I05 — Cards-First Escalation Beats All-Or-Nothing
- **Source:** sdl-mcp (GlitterKill)
- **Category:** T1 (Exploration)
- **Actionable?** Pattern
- **Evidence:** Symbol Cards (100 tok) → Graph Slicing → Delta Packs → Raw Code. Agent pays incrementally.
- **Summary:** Don't send full context. Send the smallest useful card. Escalate only if needed.

### I06 — Cross-Session Memory Compounds Over Time
- **Source:** Loom, codex-agent-mem, trace-mcp
- **Category:** T5 (Repeated Knowledge)
- **Actionable?** YES — bundle cross-session memory
- **Evidence:** Loom: 51x-1507x per session (grows richer). codex-agent-mem: ~95% on repeated context via hash caching.
- **Summary:** Knowledge stored across sessions eliminates re-exploration. Gets BETTER over time, not worse.

### I07 — Only 1 Genuine Conflict Exists Across 44 Tools
- **Source:** Conflict resolution analysis (sequential thinking, 23 steps)
- **Category:** Architecture Principle
- **Actionable?** YES — default to INCLUDE, prove conflict
- **Evidence:** Evaluated all 44 tools. Found 6 apparent conflicts. On deeper analysis, only 1 is genuine (RTK shell hook vs lean-ctx shell hook, resolved by disabling lean-ctx hook).
- **Summary:** Tools at different depths or on different token types NEVER conflict. Default to bundling.

### I08 — Token Types Are Independent — Never Add Percentages
- **Source:** Savings audit
- **Category:** Methodology
- **Actionable?** YES — enforce in all claims
- **Evidence:** RTK saves 60-90% on T2 (shell output). caveman saves 75% on T3 (agent output). These are DIFFERENT buckets and CANNOT be added.
- **Summary:** Each tool saves tokens from its own bucket. Savings compound across buckets but percentages are per-bucket.

### I09 — Savings Claims Require Citations
- **Source:** Savings audit (fact-checked every README)
- **Category:** Methodology
- **Actionable?** YES — policy enforced in AGENTS.md
- **Evidence:** LG-token-saver claims 87% but is self-reported. codesight claims 91x but is benchmarked on real projects.
- **Summary:** Every claim must cite source. Label: benchmarked / self-reported / unverified / single-example.

### I10 — All 7 Token Types Need Defense-in-Depth
- **Source:** Maximum coexistence analysis
- **Category:** Architecture Principle
- **Actionable?** YES — verify coverage in final architecture
- **Evidence:** Core bundle covers T1-T7 with 2+ tools each. Only T4 (prompt) and T6 (schema) have single coverage in core — compensated by optional modules.
- **Summary:** No token type should have zero coverage. Ideal: 2+ tools per type for defense-in-depth.

### I11 — Aggregators Teach Architecture; Discussions Teach Pain
- **Source:** AGENTS.md design lessons section
- **Category:** Research Methodology
- **Actionable?** YES — classify every source
- **Evidence:** MOS taught us complexity scoring. PAI #714 taught us tiered loading. vscode #284712 taught us dashboard UX. Paperclip #373 taught us lazy spawning.
- **Summary:** Always classify sources as TOOL / AGGREGATOR / DISCUSSION. Extract different lesson types from each.

---

## Layer 2: Output Compression (T2)

### I12 — Hook-Based Compression Is Transparent to Users
- **Source:** RTK, opentoken, omni
- **Category:** T2 (Shell Output)
- **Actionable?** YES — core architecture
- **Evidence:** RTK: 62K stars, 14 agent integrations, zero user awareness. Hook intercepts command → rewrites → compressed output reaches LLM.
- **Summary:** Best compression is invisible compression. User never knows RTK exists — it just works.

### I13 — Pre-Execution Rewrite > Post-Execution Filter Alone
- **Source:** RTK PreToolUse hook mechanism
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — prefer pre-execution
- **Evidence:** `git status` → `rtk git status`. Denser command produces less output. Combine with PostToolUse filter for max savings.
- **Summary:** Make the command produce less output (pre-execution) AND filter what remains (post-execution). Two-stage compression.

### I14 — CLI Replacement Is a Different Mechanism, Not a Competitor
- **Source:** ContextSlimAI
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — bundle alongside RTK
- **Evidence:** `contextslim grep` replaces `grep` entirely. RTK compresses `grep` output. Both save tokens but via different paths. ContextSlimAI also generates AI rules (`contextslim init`).
- **Summary:** Replacement and compression are complementary, not competing. Bundle both.

### I15 — Adaptive Compression Prevents Over-Compression
- **Source:** omni (fajarhide)
- **Category:** T2 (Shell Output)
- **Actionable?** Pattern — adaptive softening
- **Evidence:** omni tracks when agents retrieve omitted output and softens compression for those patterns. 97.3% all-time savings without losing critical info.
- **Summary:** Track what agents re-retrieve. Soften compression on those patterns. Don't over-compress.

### I16 — Ephemeral Pre-Request Compression Is Zero-Cost
- **Source:** Hermes #14948
- **Category:** T2 (Shell Output) + Architecture
- **Actionable?** Pattern — adopt for old tool results
- **Evidence:** Regex-based summaries on API copy only (doesn't mutate history). 17-82% savings. Works on old tool results that agent no longer needs verbatim.
- **Summary:** Before each API call, compress old tool results to one-line summaries. Ephemeral (API copy), zero cost (regex), reversible.

---

## Layer 3: Agent Behavior (T3, T7)

### I17 — Behavioral Rules Are the Cheapest Win (Zero Install Cost)
- **Source:** LG-token-saver, kevin-copilot
- **Category:** T3 (Agent Output) + T7 (Instructions)
- **Actionable?** YES — zero-dependency core
- **Evidence:** LG-token-saver: 5.3KB SKILL.md, 8 rules, 87% claimed. kevin-copilot: 4 modes, CI-gated evals (must beat generic-terse by ≥5pp). caveman: 75% output reduction, zero deps.
- **Summary:** SKILL.md files cost nothing to install, work everywhere, and save 66-89% on output tokens.

### I18 — Output Style vs Operational Efficiency Are Different Dimensions
- **Source:** caveman vs LG-token-saver analysis
- **Category:** T3 (Agent Output)
- **Actionable?** Pattern — bundle both
- **Evidence:** caveman: compresses HOW agent speaks (drops filler, keeps accuracy). LG-token-saver: compresses HOW agent operates (parallelism, dedup, compaction). kevin-copilot: compresses output structure (terseness levels with CI gates).
- **Summary:** Three independent axes of agent behavior compression. All three needed.

### I19 — On-Demand Skill Loading Saves 30-40% of Input Cost
- **Source:** PAI #714, graphify #1045
- **Category:** T7 (Instructions)
- **Actionable?** YES — tiered AGENTS.md for Token Saver Meta itself
- **Evidence:** SKILL.md at 83KB → 20,750 tokens every turn. Split: core loader (4K) + on-demand sections. Saves 15-18K per turn.
- **Summary:** The #1 token optimization technique. Applies to Token Saver Meta's own AGENTS.md.

### I20 — Mode-Based Tool Loading Eliminates Idle Schema Cost
- **Source:** opencode #1573, MOS
- **Category:** T6 (Tool Schema) + T7 (Instructions)
- **Actionable?** YES — implement light/medium/full modes
- **Evidence:** "hi" costs 17.7K tokens with all tools loaded. MOS: 0-140 complexity scoring → config mapping. TRIVIAL tasks need zero tools.
- **Summary:** Don't load all tools for every task. Score complexity → select tools → strip unused schemas.

### I21 — Externalize Plans to Files, Not Context
- **Source:** opencode #7579
- **Category:** Agent Protocol
- **Actionable?** YES — AGENTS.md guidance
- **Evidence:** Plans in context lost on compaction. Files survive. Agent re-reads plan from file after compaction. Built-in tool for plan display avoids re-loading into context.
- **Summary:** Agents should save plans to files. Compaction loses context but files persist.

### I22 — Lazy Spawning — Don't Bootstrap Without Work
- **Source:** Paperclip #373
- **Category:** Agent Protocol
- **Actionable?** YES — setup optimization
- **Evidence:** 22 idle agents burned hundreds of thousands of tokens with zero tasks assigned. Pre-check if agent has work before spawning.
- **Summary:** Don't index/spawn tools unless the project needs them. Relevance check before initialization.

---

## Layer 4: Prompt Compression (T4)

### I23 — ML Prompt Compression Requires GPU → Make Optional
- **Source:** LLMLingua (Microsoft)
- **Category:** T4 (Prompt Input)
- **Actionable?** YES — optional module with auto-detect
- **Evidence:** Up to 20x compression. Needs GPU (8-14GB for Llama-2-7B, ~1.5GB for XLM-RoBERTa). CPU: 10-50x slower.
- **Summary:** Auto-detect GPU → install if available. CPU: warn and ask. LLMLingua-2 lighter variant.

### I24 — Whitespace Removal Doesn't Degrade LLM Accuracy
- **Source:** Deblank (ICSE'26 Distinguished Paper)
- **Category:** T4 (Prompt Input)
- **Actionable?** YES — bundle [deferred to v2]
- **Evidence:** Academically proven across FIM tasks. ~34% on C-family, ~9% on Python. Bidirectional (unformat → send → reformat output).
- **Summary:** Strip formatting before sending code to LLM. Reformatted after. Accuracy preserved. ICSE'26 validated.

### I25 — Provider Cache Optimization Saves Without Compression
- **Source:** racs
- **Category:** T4 (Prompt Input)
- **Actionable?** Pattern — cache-breakpoint placement
- **Evidence:** 16 provider profiles. 88.1% savings vs naive prompts. 187 tests, 92% coverage. 9 lint codes catching cache-killers.
- **Summary:** Arrange prompts to maximize provider cache hits. Timestamps in stable segments kill cache. Place breakpoints correctly.

---

## Layer 5: Memory & Persistence (T5)

### I26 — Tiered Memory Architecture Compresses Across Abstraction Levels
- **Source:** MemOS
- **Category:** Architecture Pattern
- **Actionable?** Pattern — adopt L1→L4 hierarchy
- **Evidence:** L1 (raw traces, cheap) → L2 (policies, compressed) → L3 (world model, highly compressed) → L4 (crystallized skills, most compressed).
- **Summary:** Not all context is equal. Retrieve at the right abstraction level. Compress through tiers.

### I27 — Continuity Packs Eliminate Re-Contexting Entirely
- **Source:** codex-agent-mem
- **Category:** T5 (Repeated Knowledge) + Architecture
- **Actionable?** YES — bundle
- **Evidence:** 22,950 tokens of repeated session context → 1,068 token pack (95.35% reduction). Hash caching: unchanged packs return 304-style status (zero token transfer). Three budget levels: micro/normal/full.
- **Summary:** Pack session state into compact continuity packs. Hash-check before sending. Unchanged → zero tokens.

### I28 — Symbol Index Caching Compounds Over Sessions
- **Source:** Loom
- **Category:** T5 (Repeated Knowledge) + T1 (Exploration)
- **Actionable?** YES — bundle
- **Evidence:** 51x-1507x per session. Agent-written summaries persist. Session delta tracking (only re-read changed functions). SQLite + tree-sitter, zero infra.
- **Summary:** Index symbols once. Cache across sessions. Only re-read changed functions. Compounds over time.

---

## Layer 6: Data Format & Serialization (T4, T6)

### I29 — Data Format Choice Affects Token Count by 40%
- **Source:** toon (toon-format)
- **Category:** T4 (Prompt Input) + T6 (Tool Schema)
- **Actionable?** YES — bundle as serialization module [deferred to v2]
- **Evidence:** ~40% fewer tokens vs JSON. Header-declared tabular arrays: declare field names once, stream data rows. Slightly better accuracy (76.4% vs 75.0%).
- **Summary:** Compact serialization format saves tokens on every structured data exchange.

### I30 — Replace MCP Entirely with CLI for API Interactions
- **Source:** OnlyCLI
- **Category:** T6 (Tool Schema)
- **Actionable?** Pattern — alternative to MCP for REST APIs
- **Evidence:** OpenAPI spec → standalone Go CLI. Agent calls `./cli --help` (~200 tokens) instead of loading 55K-token MCP schema. 35x token reduction.
- **Summary:** For REST API tools, CLI binaries eliminate MCP schema overhead entirely.

---

## Layer 7: Monitoring & Observability

### I31 — Visible Savings Build User Trust
- **Source:** ClaudeCode-Token-Guard, vscode #284712
- **Category:** UX
- **Actionable?** YES — dashboard must show savings
- **Evidence:** vscode #284712: users want visible compression toggle, editable summaries, privacy controls. ClaudeCode-Token-Guard: dashboard with 8 diagnosis rules.
- **Summary:** Token savings must be VISIBLE. Dashboard with before/after, cost saved, per-tool breakdown. UX toggle with manual/auto modes.

### I32 — Users Don't Know Their Tools Exist
- **Source:** Kilo #5848, gstack #689
- **Category:** UX
- **Actionable?** YES — transparent defaults
- **Evidence:** Users request "add RTK" (gstack #689) — they don't want to install RTK, they want CLI compression built-in. Kilo #5848: user saved 10M tokens with RTK as separate tool, requested it be built-in.
- **Summary:** Token-saving tools should be TRANSPARENT defaults. User shouldn't know RTK exists — it should just work.

---

## Layer 8: Integration & Aggregation (Meta-Layer)

### I33 — Complexity Scoring → Config Mapping Is the Meta-Layer
- **Source:** MOS (Yula-Digital)
- **Category:** Architecture Pattern — THE META-LAYER
- **Actionable?** YES — adopt for Token Saver Meta
- **Evidence:** 0-140 score → TRIVIAL/SIMPLE/MEDIUM/HARD/EXPERT. Each level maps to: model, compression level, thinking tokens, subagents. Companion tools list with claimed savings.
- **Summary:** Token Saver Meta needs a scoring engine. Map task complexity → tool selection → config. This is the meta-layer.

### I34 — Constant Schema Overhead Is Essential at Scale
- **Source:** MetaMCP
- **Category:** T6 (Tool Schema)
- **Actionable?** Pattern — MCP aggregation
- **Evidence:** Collapses N MCP servers into 6 constant-size tools (~1,300 tokens). Without: N × 3K tokens. With 10 tools: 30K → 1.3K schema tokens.
- **Summary:** Aggregate all bundled MCP tools behind a single constant-overhead gateway.

### I35 — Delegation to Cheaper Models Saves Money, Not Tokens
- **Source:** houtini-lm, save-my-tokens
- **Category:** Cost Optimization (not token savings)
- **Actionable?** Pattern — model routing
- **Evidence:** Route simple tasks (formatting, commit messages, test stubs) to free/cheap models. Claude orchestrates (~50-100 tokens), free models execute. 19x more workflows per Claude budget.
- **Summary:** Model routing saves MONEY, not tokens. Complementary to token-saving tools. Both needed.

---

## Layer 9: Research Methodology (Meta-Insights)

### I36 — Clone Everything First, Filter Later
- **Source:** Batch 2 research
- **Category:** Research Methodology
- **Actionable?** YES — always `git clone --depth 1` ALL repos
- **Evidence:** "txbbs" sounded like a token tool — was WeChat automation. "racs" sounded irrelevant — was cache optimization genius (187 tests, 92% coverage). Names are misleading.
- **Summary:** Never judge a repo by its name. Clone everything. Read the README. Then classify.

### I37 — Sequential Thinking Resolves False Conflicts
- **Source:** Our own process (23 steps of sequential thinking)
- **Category:** Research Methodology
- **Actionable?** YES — use for all conflict resolution
- **Evidence:** Initial pass found ~6 conflicts. Sequential thinking revealed only 1 genuine conflict across 44 tools. Token type mapping was the key insight.
- **Summary:** Map tools to token types (T1-T7) BEFORE evaluating conflicts. Same type + same mechanism = conflict. Different types = complement.

---

## Layer 10: Code Generation Minimalism (T3) *(Added 2026-06-18)*

### I38 — YAGNI-Ladder Output Compression Complements Style Compression
- **Source:** ponytail (DietrichGebert/ponytail)
- **Category:** T3 (Agent Output)
- **Actionable?** YES — bundle alongside caveman as complementary T3 compressor
- **Evidence:** Ladder enforces: stdlib → native → dependency → one-liner → minimal. Benchmarked across 13 agent platforms: ~54% less code, ~22% fewer tokens, ~20% lower cost, 100% safety rate (no breaking changes). Forces agent to exhaust simpler options before writing complex code.
- **Summary:** caveman compresses agent SPEECH (prose terseness). ponytail compresses agent CODE (YAGNI minimalism). Two independent mechanisms on T3. Together: agent that both speaks tersely AND writes minimally = compound T3 savings.

## Layer 11: Instruction Optimization (T7) *(Added 2026-06-18)*

### I39 — Skills Are Trainable State, Not Static Instructions
- **Source:** SkillOpt (microsoft/SkillOpt)
- **Category:** T7 (Instructions)
- **Actionable?** YES — optional module for offline skill optimization
- **Evidence:** Trains skill documents through epochs/mini-batches with validation gates. Produces compact `best_skill.md` artifacts (300-2,000 tokens). +23.5pt accuracy gain on GPT-5.5. "Sleep" preview: nightly offline self-evolution. Skills shrink over time while effectiveness INCREASES.
- **Summary:** Skill documents can be optimized like ML models. Output is minimal-token artifacts that run with zero inference-time overhead. Nightly optimization means skills get better AND smaller over time.

---

# PART 2: ALL SYNERGIES (24)

---

## How to Read Synergies

Each synergy shows how two or more insights COMBINE to produce effects greater than either alone. Format:

```
S{NN} — {Name}
Insights: {I numbers}
Mechanism: {how they compound}
Effect: {what the combination achieves}
```

---

## Synergy Block A: The Complete Code Intelligence Stack (T1)

### S01 — Static Map + Dynamic Graph = No Blind Exploration
- **Insights:** I03 (static maps) + I01 (graph retrieval) + I02 (progression)
- **Mechanism:** codesight generates the "what's here" map (3.6K tokens). Agent reads it once. Then GitNexus/CGC answer "how does X work?" via graph queries (200-500 tokens each). Never reads raw files blindly.
- **Effect:** First-session exploration drops from 40K tokens to ~4K tokens. Every subsequent query costs ~300 tokens instead of ~5K. **Compounding: each query saves ~4.7K tokens, and there are typically 5-10 queries per session = 23-47K saved.**

### S02 — Symbol Index Caching + Static Map = Zero Re-Exploration
- **Insights:** I06 (cross-session memory) + I28 (symbol index caching) + I03 (static maps)
- **Mechanism:** codesight generates the map once. Loom caches symbol summaries across sessions. Next session: agent reads cached map (13 tokens with lean-ctx) + queries cached symbols (no file reads).
- **Effect:** Session 1: codesight + index = still expensive. Session 2+: nearly free. Session 10+: almost zero exploration cost. **Compound effect over days of usage = 50x-1500x savings.**

### S03 — Cards-First + Graph Retrieval = Pay Only for Depth
- **Insights:** I05 (cards-first escalation) + I01 (graph retrieval)
- **Mechanism:** Agent starts with Symbol Cards (~100 tokens) from sdl-mcp's Ladder. If insufficient, escalates to Graph Slicing. If still insufficient, queries GitNexus/CGC for full impact analysis. Only pays for the depth actually needed.
- **Effect:** Most queries stop at rung 1 or 2 (~100-500 tokens). Rarely need full impact analysis (~2K tokens). **90% of queries save 80-90% vs always-query-graph approach.**

---

## Synergy Block B: The Complete Output Compression Stack (T2)

### S04 — Pre-Execution Rewrite + Post-Execution Filter = Two-Stage Compression
- **Insights:** I13 (pre-execution rewrite) + I12 (hook-based compression)
- **Mechanism:** RTK rewrites command pre-execution → produces denser output. token-savior PostToolUse compresses remaining output. Result passes through two filters.
- **Effect:** Command that would produce 5K tokens of output: RTK rewrite → 1K token output → PostToolUse filter → 200 tokens. **96% reduction vs raw. Pre-execution alone: 80%. Post alone: 70%. Together: 96%.**

### S05 — CLI Replacement + Output Compression = Coverage for All Commands
- **Insights:** I14 (CLI replacement) + I12 (hook compression)
- **Mechanism:** ContextSlimAI provides slim alternatives for commands RTK doesn't have filters for. RTK compresses everything else. Agent uses whichever path is available.
- **Effect:** No command goes uncompressed. RTK covers 60+ patterns; ContextSlimAI covers 40+ commands. Combined: 100+ command patterns covered. **Blind spot coverage: 100%.**

### S06 — Adaptive Compression + Ephemeral Pre-Request = No Over-Compression
- **Insights:** I15 (adaptive compression) + I16 (ephemeral pre-request)
- **Mechanism:** omni tracks re-retrievals and softens compression. Hermes pattern compresses old results one-line before API calls. Together: current output stays detailed, old output gets summarized.
- **Effect:** Critical recent output preserved verbatim. Stale output compressed to one-liner. Agent always has what it needs, never pays for what it doesn't. **No information loss + maximum compression.**

---

## Synergy Block C: The Complete Agent Behavior Stack (T3, T7)

### S07 — Style + Operations + Structure = Three-Axis Agent Compression
- **Insights:** I17 (behavioral rules) + I18 (style vs operations)
- **Mechanism:** caveman compresses agent SPEECH (75% fewer words). LG-token-saver compresses agent OPERATIONS (parallelism, dedup, compaction). kevin-copilot compresses agent OUTPUT STRUCTURE (lite/full/ultra modes with CI gates).
- **Effect:** Three independent compression axes work simultaneously. Speech: -75%. Operations: -87% (claimed). Structure: -66-89%. **Not additive (different buckets) but multiplicative: agent that operates efficiently AND speaks tersely AND structures compactly = ~90-95% output token reduction.**

### S08 — Tiered Loading + Mode-Based Tools = Instruction Budget Control
- **Insights:** I19 (tiered loading) + I20 (mode-based tools)
- **Mechanism:** Split AGENTS.md into core loader (4K) + on-demand sections. Only load sections for the current mode (light/medium/full). Light mode: core only. Full mode: all sections.
- **Effect:** "hi" in light mode: 4K instructions + zero tool schemas = ~5K tokens total vs 17.7K currently. **65%+ reduction on simple queries. Complex tasks get full instructions only when needed.**

### S09 — Externalize Plans + Cross-Session Memory = Survive Compaction
- **Insights:** I21 (externalize plans) + I06 (cross-session memory)
- **Mechanism:** Agent saves plan to file (survives compaction). codex-agent-mem stores continuity pack (survives sessions). On compaction or new session: agent reads plan from file + restores project state from continuity pack.
- **Effect:** Compaction no longer destroys project context. New session starts in seconds, not minutes. **Zero re-contexting cost across compaction boundaries and session boundaries.**

---

## Synergy Block D: The Complete Prompt Compression Stack (T4)

### S10 — ML Compression + Whitespace Removal = Complementary Prompt Reduction
- **Insights:** I23 (ML compression) + I24 (whitespace removal)
- **Mechanism:** Deblank strips formatting from code (34% on C, 9% on Python) — lossless, bidirectional. LLMLingua removes low-information tokens via perplexity — lossy but up to 20x. Apply Deblank first (lossless), then LLMLingua (lossy). Order matters.
- **Effect:** Code prompt: formatting stripped (lossless ~20% avg) → low-info tokens removed (lossy, 5-20x on remaining). Combined: **30-40% lossless + 5-20x lossy = massive compound effect with accuracy preserved by Deblank's academic validation.**

### S11 — Cache Optimization + Schema Compression = Maximum API Efficiency
- **Insights:** I25 (cache optimization) + I04 (schema compression)
- **Mechanism:** TSCG compresses tool schemas (50-72% fewer tokens). racs places cache breakpoints optimally (88.1% cache hits vs naive). Smaller schemas = more likely to fit in cache. Better breakpoints = fewer cache misses.
- **Effect:** Without: 15K schema tokens per request × 20 requests = 300K tokens, 30% cache hit rate. With: 7K schema tokens × 20 = 140K tokens, 88% cache hit rate. **Combined: ~80% total API token reduction (schema compression + cache optimization compound).**

---

## Synergy Block E: Session Lifecycle Optimizations

### S12 — Lazy Spawning + Mode-Based Tools = Zero Idle Overhead
- **Insights:** I22 (lazy spawning) + I20 (mode-based tools)
- **Mechanism:** Setup: pre-check which tools are needed (project language, task complexity). Spawn only relevant tools. Light mode: zero MCP servers. Full mode: all servers.
- **Effect:** Simple Q&A session: zero tools spawned = zero schema overhead = zero idle token burn. Complex coding session: all tools available. **20 idle agents with zero tasks = zero tokens burned (Paperclip pattern solved).**

### S13 — Continuity Packs + Tiered Memory = Right Context at Right Abstraction
- **Insights:** I27 (continuity packs) + I26 (tiered memory)
- **Mechanism:** MemOS L1-L4 tiers determine WHAT abstraction to retrieve. codex-agent-mem packs it into compact continuity format. Agent gets: relevant skill patterns (L4, most compressed) + current task state (continuity pack, ~1K tokens).
- **Effect:** Agent receives exactly what it needs: crystallized skills from past sessions + current task context. **No raw traces. No redundant re-loading. Abstracted knowledge + specific state = minimal context, maximal usefulness.**

### S14 — Hash Caching + Delta Tracking = Pay Only for Changes
- **Insights:** I27 (continuity packs hash) + I28 (symbol index delta)
- **Mechanism:** codex-agent-mem: hash-check continuity pack before sending. Unchanged → 304, zero tokens. Loom: delta tracking — only re-read functions that changed since last session.
- **Effect:** Day 2 of project: 90% of code unchanged → 90% of retrieval costs eliminated. Day 10: 95% unchanged → 95% eliminated. **Compound effect: each day costs less than the previous.**

---

## Synergy Block F: The Meta-Layer

### S15 — Complexity Scoring Orchestrates ALL Tools
- **Insights:** I33 (complexity scoring) + I07 (only 1 conflict) + I10 (defense-in-depth)
- **Mechanism:** MOS-style 0-140 scoring engine evaluates the task. Maps score → tool selection across all token types. TRIVIAL: no tools. SIMPLE: RTK only. MEDIUM: RTK + codesight. HARD: full stack. EXPERT: full stack + GPU-accelerated options.
- **Effect:** One engine selects from all 10+ tools based on actual need. **User never configures anything. The meta-layer IS the product.**

### S16 — On-Demand Loading + Mode-Based Tools + Complexity Scoring = The Full Meta-Layer
- **Insights:** I19 (tiered loading) + I20 (mode-based tools) + I33 (complexity scoring)
- **Mechanism:** Complexity score determines mode. Mode determines which AGENTS.md sections load. Only loaded sections reference tools. Tools spawned lazily based on loaded sections.
- **Effect:** Three-layer cascading optimization: score → mode → instructions → tools. **Each layer gates the next. Simple task: score=0, mode=light, core instructions only, zero tools. Complex task: score=120, mode=expert, full instructions, all tools.**

---

## Synergy Block G: Cross-Cutting Optimizations

### S17 — Cache-Aware Prompting + Schema Compression + Ephemeral Compression = Every API Call Optimized
- **Insights:** I25 (cache optimization) + I04 (schema compression) + I16 (ephemeral compression)
- **Mechanism:** Before each API call: (1) compress schemas via TSCG → fewer tokens. (2) place cache breakpoints via racs → higher cache hit rate. (3) compress old tool results to one-liners via Hermes pattern → fewer tokens. All three fire on every request.
- **Effect:** Every single API call pays less and caches better. **Per-request token budget: 50-80% smaller. Cache hit rate: 3x higher. Combined: 70-90% reduction in API costs.**

### S18 — Data Format + Schema Compression = Every Structured Exchange Optimized
- **Insights:** I29 (data format) + I04 (schema compression)
- **Mechanism:** toon format reduces JSON token count by 40%. TSCG compresses JSON Schema definitions by 50-72%. Together: data payload AND schema definition both compressed.
- **Effect:** Tool definitions: 50-72% smaller. Tool outputs: 40% smaller. **Every tool interaction saves tokens on both definition and data sides.**

### S19 — Visible Savings + Transparent Tools = User Adoption Without Effort
- **Insights:** I31 (visible savings) + I32 (transparent tools) + I12 (hook-based transparency)
- **Mechanism:** RTK works invisibly (user never knows). Dashboard shows savings from ALL tools. User sees "Saved 10M tokens this month ($300)" but never configured anything.
- **Effect:** Zero adoption friction. Tools work automatically. Dashboard builds trust retroactively. **"I didn't do anything and I saved $300" = viral word-of-mouth.**

---

## Synergy Block H: Research Methodology Synergies

### S20 — Clone Everything + Sequential Thinking = Zero Missed Insights
- **Insights:** I36 (clone everything) + I37 (sequential thinking)
- **Mechanism:** Clone all repos regardless of name. Classify by TOOL/AGGREGATOR/DISCUSSION. Map to token types T1-T7. Use sequential thinking to resolve apparent conflicts.
- **Effect:** "txbbs" = irrelevant. "racs" = genius. "MOS" = meta-layer pattern. Without cloning everything, we'd miss 3 of our top 5 insights. **Methodology prevents hasty exclusion.**

### S21 — Savings Audit + Token Type Mapping = Honest Claims
- **Insights:** I09 (savings citations) + I08 (independent token types)
- **Mechanism:** Every savings claim cites source with label (benchmarked/self-reported/unverified). Claims are per-token-type, never aggregated across types. "RTK saves 60-90% on T2 (benchmarked by category). caveman saves ~75% on T3 (single example)."
- **Effect:** No fabricated "82% total savings." No misleading aggregate claims. Every number traceable to source with caveat. **Credibility preserved. Users can verify every claim.**

### S22 — Insight Registry + BESTS Leaderboard + Synergy Map = Complete Knowledge Graph
- **Insights:** I36 + I37 + I11 (aggregators teach architecture)
- **Mechanism:** Three documents form a knowledge graph: (1) Insight Registry — WHAT we know (37 insights). (2) BESTS.md — WHICH tools rank highest (44 tools). (3) Synergy Map (this document) — HOW insights combine (22 synergies).
- **Effect:** Any agent or human can navigate: insight → tool → synergy → architecture. **Complete decision support system for tool selection and architecture design.**

---

## Synergy Block I: Code Generation + Instruction Optimization *(Added 2026-06-18)*

### S23 — YAGNI-Ladder + Prose Terseness = Complete T3 Defense-in-Depth
- **Insights:** I38 (YAGNI-ladder) + I17 (behavioral rules) + I18 (style vs operations)
- **Mechanism:** caveman compresses agent SPEECH (75% fewer words). ponytail compresses agent CODE (54% fewer LOC via YAGNI ladder). LG-token-saver compresses agent OPERATIONS (parallelism, dedup). Three independent T3 compression axes.
- **Effect:** Agent that speaks tersely (caveman) + writes minimally (ponytail) + operates efficiently (LG-token-saver) = **maximum T3 compression. Not additive across buckets, but multiplicative within the output stream. An agent that writes 54% less code and speaks 75% fewer words is operating at ~90%+ T3 token reduction.**

### S24 — Skill Optimization + On-Demand Loading = Self-Optimizing Instruction Budget
- **Insights:** I39 (trainable skills) + I19 (tiered loading)
- **Mechanism:** SkillOpt produces minimal-token skill documents (300-2,000) from larger originals. AGENTS.md tiered loading only sends the core loader (~4K) + on-demand skill sections. Together: the skills themselves shrink AND only load when needed.
- **Effect:** Nightly SkillOpt "Sleep" run: all skills re-optimized to minimal effective form. Session: core loader (4K) + optimized skill requested (300-2K) = **instructions budget stays under 6K tokens even in full mode. Without: 20K+ per turn. Self-optimizing: skills get better AND smaller over time — every night they shrink while accuracy improves.**
