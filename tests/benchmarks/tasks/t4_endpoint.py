"""T4 benchmark: new endpoint + frontend. Tests T1 (exploration) + T6 (schema)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.benchmarks.runner import TaskConfig

FIXTURE = Path(__file__).parent.parent / "fixtures" / "api_app"

PROMPT = """Add a new endpoint GET /api/users/:id/posts that returns posts for a user.
Then update the frontend UserList component to show post counts next to each user.
Use the existing Express server and React patterns already in the project."""

def get_config(agent: str = "opencode", saver_enabled: bool = True) -> TaskConfig:
    return TaskConfig(
        task_id="t4_endpoint",
        agent=agent,
        prompt=PROMPT,
        fixture_path=FIXTURE,
        saver_enabled=saver_enabled,
    )
