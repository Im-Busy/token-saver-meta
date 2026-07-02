"""T2 benchmark: processPayment call chain. Tests T1 (exploration)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.benchmarks.runner import TaskConfig

FIXTURE = Path(__file__).parent.parent / "fixtures" / "payment_app"

PROMPT = """Find all functions that call processPayment() and trace the call chain 3 levels deep.
Report the exact file:line for each function in the chain."""

def get_config(agent: str = "opencode", saver_enabled: bool = True) -> TaskConfig:
    return TaskConfig(
        task_id="t2_exploration",
        agent=agent,
        prompt=PROMPT,
        fixture_path=FIXTURE,
        saver_enabled=saver_enabled,
    )
