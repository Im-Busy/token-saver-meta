<!-- cbm:start -->
## Codebase-Memory — Code Intelligence

This project is indexed by Codebase-Memory MCP (codebase-memory-mcp). Use CBM tools to understand code, trace call chains, and explore structure.

### Always Do
- Use `search_graph` or `query_graph` before grep+read when exploring unfamiliar code
- Use `trace_path` to follow call chains instead of reading files sequentially
- Use `get_architecture` for project overview instead of reading directory trees
- Use `search_code` for text search within indexed files only

### Never Do
- NEVER grep+read across multiple files without first checking CBM for structural information
- NEVER trace call chains by reading files — use `trace_path` instead
- NEVER explore project structure manually — use `get_architecture`

### Resources
| Resource | Use for |
|----------|---------|
| CBM MCP tools | `search_graph`, `query_graph`, `trace_path`, `get_architecture`, `search_code`, `get_code_snippet` |
| DB path | `~/.cache/codebase-memory-mcp/` |

### Quick Reference
- Find symbol: `search_graph(name_pattern="functionName")`
- Trace calls: `trace_path(function_name="processPayment", direction="inbound", depth=3)`
- Architecture: `get_architecture()`
<!-- cbm:end -->
