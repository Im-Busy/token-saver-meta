"""T1 benchmark: CSV→JSON CLI creation. Tests T3 (agent output) + T7 (instructions)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.benchmarks.runner import TaskConfig

FIXTURE = Path(__file__).parent.parent / "fixtures" / "csv_cli"

PROMPT = """Create a Python CLI tool that reads a CSV file and outputs a JSON summary.
The CSV has columns: name, age, city.
The JSON should have: total_count, average_age, by_city (count per city).
Write the code to csv_cli.py in the project root. Keep it under 50 lines. No comments."""

def get_config(agent: str = "opencode", saver_enabled: bool = True) -> TaskConfig:
    return TaskConfig(
        task_id="t1_csv_cli",
        agent=agent,
        prompt=PROMPT,
        fixture_path=FIXTURE,
        saver_enabled=saver_enabled,
    )
