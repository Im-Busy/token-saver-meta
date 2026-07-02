"""T5 benchmark: debug login 500 error. Tests T1 (exploration) + T3 (output)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.benchmarks.runner import TaskConfig

FIXTURE = Path(__file__).parent.parent / "fixtures" / "auth_bug"

PROMPT = """The POST /api/login endpoint returns 500. Debug and fix the issue.
The server is an Express app in server.js. Do NOT read the entire file first —
use targeted exploration to find the bug."""

def get_config(agent: str = "opencode", saver_enabled: bool = True) -> TaskConfig:
    return TaskConfig(
        task_id="t5_debug",
        agent=agent,
        prompt=PROMPT,
        fixture_path=FIXTURE,
        saver_enabled=saver_enabled,
    )
