"""T3 benchmark: npm install + type errors. Tests T2 (shell output)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.benchmarks.runner import TaskConfig

FIXTURE = Path(__file__).parent.parent / "fixtures" / "npm_error"

PROMPT = """Run npm install and then fix the TypeScript type errors.
The project has intentional type errors — find and fix them all.
After fixing, verify with npx tsc --noEmit."""

def get_config(agent: str = "opencode", saver_enabled: bool = True) -> TaskConfig:
    return TaskConfig(
        task_id="t3_shell_output",
        agent=agent,
        prompt=PROMPT,
        fixture_path=FIXTURE,
        saver_enabled=saver_enabled,
    )
