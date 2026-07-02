# Token Saver Meta — Benchmarks

Measure token savings across 5 standard tasks against any AI coding agent.

## Quick Start

```bash
uv run python -m tests.benchmarks.tasks --task t1 --agent opencode
```

## Supported Agents

Token Saver Meta supports 18 AI coding platforms. The benchmark harness has adapters for:

| Agent | Adapter | Status | CLI |
|-------|---------|--------|-----|
| OpenCode | `OpenCodeAdapter` | ✅ Working | `opencode` |
| Claude Code | `ClaudeCodeAdapter` | ⬜ Stub | `claude` |
| Codex CLI | `CodexAdapter` | ⬜ Stub | `codex` |
| Gemini CLI | `GeminiAdapter` | ⬜ Stub | `gemini` |
| Aider | `AiderAdapter` | ⬜ Stub | `aider` |

For IDE-based platforms (Cursor, Windsurf, Copilot VS Code, Kilo, Cline, Roo Code, Continue.dev, Augment, FactoryAI, Hermes, Kiro, Mastra, Pi) — these cannot be automated via CLI. Test manually:

1. Install token-saver-meta: `uvx token-saver-meta`
2. Open the IDE with one of our benchmark fixture projects
3. Run the benchmark prompt manually
4. Compare session token usage (where available) with and without token-saver-meta

## Adding Your Agent

Implement the `AgentAdapter` protocol in `tests/benchmarks/runner.py`:

```python
class YourAgentAdapter:
    def __init__(self):
        self.binary = shutil.which("your-agent-binary") or "your-agent-binary"

    def invoke(self, prompt: str, project_path: Path) -> dict:
        result = subprocess.run(
            [self.binary, "-p", prompt],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
```

Then register it in `BenchmarkRunner._adapters` and add a CLI to the benchmark runner.

## Tasks

| Task | Fixture | Token Types | Prompt |
|------|---------|-------------|--------|
| T1 | csv_cli/ | T3+T7 | Create CSV→JSON CLI |
| T2 | payment_app/ | T1 | Trace processPayment() 3 levels |
| T3 | npm_error/ | T2 | npm install + fix type errors |
| T4 | api_app/ | T1+T6 | Add /api/users/:id/posts endpoint |
| T5 | auth_bug/ | T1+T3 | Debug login 500 |

## Methodology

Token counting uses tikToken `cl100k_base` encoding (OpenAI GPT-4 tokenizer). Shell output measured in raw UTF-8 bytes. Each task runs 3 trials with saver + 3 trials without.

## Contributing Results

PRs welcome. Add your agent adapter and contribute benchmark results. Include your `omo/evidence/task-*-phase10-*-benchmark.json` files.
