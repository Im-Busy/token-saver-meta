"""Entry point for running benchmark tasks from the command line.

Usage:
    uv run python -m tests.benchmarks.tasks --task t1 --agent opencode
    uv run python -m tests.benchmarks.tasks --task t3 --agent claude
"""
import argparse
import importlib
import sys
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).parent.parent
EVIDENCE_DIR = Path(__file__).parent.parent.parent.parent / "omo" / "evidence"

TASK_MODULES = {
    "t1": "tests.benchmarks.tasks.t1_csv_cli",
    "t2": "tests.benchmarks.tasks.t2_exploration",
    "t3": "tests.benchmarks.tasks.t3_shell_output",
    "t4": "tests.benchmarks.tasks.t4_endpoint",
    "t5": "tests.benchmarks.tasks.t5_debug",
}

VALID_AGENTS = {"opencode", "claude", "codex", "gemini", "aider"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run token-saver-meta benchmark tasks."
    )
    parser.add_argument(
        "--task",
        required=True,
        choices=list(TASK_MODULES),
        help="Benchmark task to run (t1-t5)",
    )
    parser.add_argument(
        "--agent",
        default="opencode",
        choices=sorted(VALID_AGENTS),
        help="AI coding agent to benchmark (default: opencode)",
    )
    args = parser.parse_args()

    task_name = args.task
    agent_name = args.agent

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    try:
        module = importlib.import_module(TASK_MODULES[task_name])
    except ImportError as exc:
        print(f"Error: Could not import task module for {task_name}: {exc}")
        sys.exit(1)

    config = module.get_config(agent=agent_name, saver_enabled=True)

    from tests.benchmarks.runner import BenchmarkRunner

    runner = BenchmarkRunner(EVIDENCE_DIR)
    results = runner.run_task(config)

    with_saver = [r for r in results if r.mode == "with_saver"]
    without_saver = [r for r in results if r.mode == "without_saver"]

    avg_with = sum(r.total_tokens for r in with_saver) / len(with_saver)
    avg_without = sum(r.total_tokens for r in without_saver) / len(without_saver)

    if avg_without > 0:
        savings = (1 - avg_with / avg_without) * 100
    else:
        savings = 0.0

    print(f"\nBenchmark: {task_name} @ {agent_name}")
    print(f"  With saver:    {avg_with:.0f} tokens (avg of {len(with_saver)} trials)")
    print(f"  Without saver: {avg_without:.0f} tokens (avg of {len(without_saver)} trials)")
    print(f"  Savings:       {savings:.1f}%")
    print(f"  Evidence:      {EVIDENCE_DIR / f'{task_name}.json'}")


if __name__ == "__main__":
    main()
