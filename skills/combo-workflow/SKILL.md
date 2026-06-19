# Token Saver Combo Workflow

## Quick Reference
| Tool | When to Use |
|------|-------------|
| **codesight** | Session start — project overview via CODESIGHT.md (200 tok vs 40K+ file reads) |
| **GitNexus** | Before editing any symbol — impact analysis, execution flows |
| **CGC** | Dead code detection, Cypher queries, hierarchy analysis |
| **RTK** | Any shell command — auto-compressed output via hooks |
| **Repomix** | Full codebase context dump for agent prompts |
| **caveman** | Always active — ultra-terse agent output style |
| **LG-token-saver** | Always active — parallelism, dedup, compaction rules |
| **kevin-copilot** | Always active — terseness instructions |
| **ContextSlimAI** | Pre-configured in rules files — no manual action needed |

## Priority Flow
1. **codesight FIRST** — Read CODESIGHT.md for project overview (~200 tok)
2. **GitNexus** — Impact analysis before editing symbols
3. **CGC** — Structural queries and dead code detection
4. **Repomix** — When you need full-codebase context
5. **RTK** — Wraps every shell call automatically

## Anti-Patterns
- grep before querying a graph — costs 10-100x more tokens
- read_file() on >200 line files without codesight context first
- Sequential shell calls you could batch with &&
- Editing without impact analysis
- Ignoring index freshness warnings