# Draft: deidentify-public-text

> **status:** generating-plan
> **created:** 2026-06-19

## Decision Ledger

| Decision | Rationale |
|----------|-----------|
| **Repomix IS MIT** | Verified via GitHub API. User's concern unfounded. Safe to reference. |
| **All 10 bundled tools are compatible** | MIT/Apache-2.0, all compatible with our Apache-2.0 package. Only GitNexus is PolyForm NC (already Optional). |
| **Rename all tool references** | Use capability-based naming: "prose terseness" not "caveman", "code minimalism" not "ponytail" |
| **Pattern B (capability enumeration)** | Primary pattern for architecture tables — list what each layer does, not which tools |
| **Pattern C (meta-signals)** | Use "out of the box", "zero-config", "batteries included" |
| **Pattern E (separate attribution)** | Add dedicated Acknowledgments section in docs/architecture-v2.md |
| **Sub-packages stay unnamed** | tscg, contextslim, token-saver-mem are our Python rewrites. Don't mention originals. |
| **Internal docs unchanged** | progress_docs/ and docs/rewrite-strategy.md stay as-is (private/internal) |

## License Audit

| Tool | License | Compatible |
|------|---------|:---:|
| caveman | MIT | ✅ |
| ponytail | MIT | ✅ |
| LG-token-saver | MIT | ✅ |
| kevin-copilot | MIT | ✅ |
| CGC/codegraph | MIT | ✅ |
| codesight | MIT | ✅ |
| Repomix | MIT | ✅ |
| RTK | Apache-2.0 | ✅ |
| TSCG | MIT | ✅ |
| SkillOpt | MIT | ✅ |
| LLMLingua-2 | MIT | ✅ |
| GitNexus | PolyForm NC | ❌ |

## Rewrite Map

### Injection Block Rewrites

| Old | New |
|-----|-----|
| `> Sources: caveman (prose style), ponytail (code minimalism), LG-token-saver (operations), kevin-copilot (structure).` | `> 28 rules across 4 dimensions: prose style, code minimalism, operational efficiency, and structured output.` |
| `### Output Style (caveman + kevin-copilot)` | `### Output Style` |
| `### Code Minimalism (ponytail)` | `### Code Minimalism` |
| `### Operational Efficiency (LG-token-saver)` | `### Operational Efficiency` |
| `ponytail:` (in rule 17) | (keep — this is an instructional marker, not a tool name reference) |

### Plugin Rewrites

| File | Old | New |
|------|-----|-----|
| `.claude-plugin/plugin.json` line 4 | `injects caveman + ponytail + LG-token-saver + kevin-copilot rules` | `injects 28 token-saving rules for AI coding agents` |
| `skills/token-saver/SKILL.md` YAML | `Injects caveman + ponytail + LG-token-saver + kevin-copilot token-saving rules.` | `28 token-saving rules: prose terseness, code minimalism, operational efficiency, structured output.` |

### README Architecture Table Rewrite

Old (README.md lines 13-16):
```
| Base | caveman, ponytail, LG-token-saver, kevin-copilot | SKILL.md text (instant, zero deps) |
| Intelligence | CGC/codegraph, codesight, Repomix | Auto-install via npx |
| Compression | RTK, ContextSlimAI | Binary + CLI wrappers |
| Optional | TSCG, Unified T5 Memory, LLMLingua-2, SkillOpt, GitNexus | One-click enable |
```

New:
```
| Agent Behavior | Prose terseness, code minimalism, operational efficiency, structured output | Instant, zero config |
| Code Intelligence | Smart file navigation, context mapping, repo packing | Auto-install |
| Output Compression | Shell output filtering, CLI optimization | Auto-install |
| Power Tools | Schema compression, cross-session memory, prompt optimization, skill tuning | One-click enable |
```

### AGENTS.md §Current Architecture Rewrite

Replace the 4-layer table (Base/Intelligence/Compression/Optional) with capability-based descriptions. Remove star counts. Remove tool names from the table.

### distribution/README.md Rewrite

Line 35: `"merging caveman (prose terseness), ponytail (YAGNI code minimalism), LG-token-saver (operational efficiency), and kevin-copilot (structured terseness)"` → `"across four dimensions: prose terseness, code minimalism, operational efficiency, and structured output"`
