from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
import subprocess
import json
import time
import shutil
from .measurement import TokenCounter

class AgentAdapter(Protocol):
    """Protocol for invoking an AI coding agent via subprocess CLI."""
    def invoke(self, prompt: str, project_path: Path) -> dict:
        """Invoke agent. Returns {stdout, stderr, tool_calls, exit_code}."""
        ...

class OpenCodeAdapter:
    """Invokes OpenCode CLI."""
    def __init__(self):
        self.binary = shutil.which("opencode") or "opencode"
    
    def invoke(self, prompt: str, project_path: Path) -> dict:
        result = subprocess.run(
            [self.binary, "run", prompt],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "tool_calls": []  # Parse from stdout if feasible
        }

class ClaudeCodeAdapter:
    """Invokes Claude Code CLI."""
    def __init__(self):
        self.binary = shutil.which("claude") or "claude"
    
    def invoke(self, prompt: str, project_path: Path) -> dict:
        result = subprocess.run(
            [self.binary, "-p", prompt],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "tool_calls": []
        }

class CodexAdapter:
    """Invokes Codex CLI (OpenAI). Stub — raises NotImplementedError."""
    def __init__(self):
        self.binary = shutil.which("codex") or "codex"
    
    def invoke(self, prompt: str, project_path: Path) -> dict:
        raise NotImplementedError(
            "Codex CLI not found. Install from https://github.com/openai/codex"
        )

class GeminiAdapter:
    """Invokes Gemini CLI (Google). Stub — raises NotImplementedError."""
    def __init__(self):
        self.binary = shutil.which("gemini") or "gemini"
    
    def invoke(self, prompt: str, project_path: Path) -> dict:
        raise NotImplementedError(
            "Gemini CLI not found. Install from https://github.com/google-gemini/gemini-cli"
        )

class AiderAdapter:
    """Invokes Aider CLI. Stub — raises NotImplementedError."""
    def __init__(self):
        self.binary = shutil.which("aider") or "aider"
    
    def invoke(self, prompt: str, project_path: Path) -> dict:
        raise NotImplementedError(
            "Aider CLI not found. Install from https://aider.chat/"
        )

@dataclass
class TaskConfig:
    task_id: str
    agent: str  # "opencode" or "claude"
    prompt: str
    fixture_path: Path
    saver_enabled: bool

@dataclass
class TrialResult:
    task_id: str
    agent: str
    trial: int
    mode: str  # "with_saver" or "without_saver"
    tokens_out: int
    tokens_instructions: int
    total_tokens: int
    raw_bytes_t2: int = 0
    read_calls: int = 0
    grep_calls: int = 0
    tokens_exploration: int = 0
    tokens_schema: int = 0
    found_bug: bool = False
    exit_code: int = 0

class BenchmarkRunner:
    def __init__(self, evidence_dir: Path):
        self.counter = TokenCounter()
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self._adapters = {
            "opencode": OpenCodeAdapter(),
            "claude": ClaudeCodeAdapter(),
            "codex": CodexAdapter(),
            "gemini": GeminiAdapter(),
            "aider": AiderAdapter(),
        }
    
    def run_task(self, config: TaskConfig) -> list[TrialResult]:
        """Run 3 trials with saver + 3 trials without saver. Returns 6 results."""
        results = []
        adapter = self._adapters.get(config.agent)
        if adapter is None:
            raise ValueError(f"Unknown agent: {config.agent}")
        
        for trial in range(1, 4):
            # With saver
            result_with = self._run_trial(adapter, config, trial, "with_saver")
            results.append(result_with)
            # Without saver
            result_without = self._run_trial(adapter, config, trial, "without_saver")
            results.append(result_without)
        
        self._save_results(config.task_id, results)
        return results
    
    def _run_trial(self, adapter, config: TaskConfig, trial: int, mode: str) -> TrialResult:
        # Set saver env based on mode
        env = {}
        if mode == "without_saver":
            env["TOKEN_SAVER_DISABLED"] = "1"
        
        output = adapter.invoke(config.prompt, config.fixture_path)
        stdout = output.get("stdout", "")
        
        return TrialResult(
            task_id=config.task_id,
            agent=config.agent,
            trial=trial,
            mode=mode,
            tokens_out=self.counter.count_tokens(stdout),
            tokens_instructions=0,
            total_tokens=self.counter.count_tokens(stdout),
            exit_code=output.get("exit_code", 0),
        )
    
    def _save_results(self, task_id: str, results: list[TrialResult]):
        path = self.evidence_dir / f"{task_id}.json"
        data = [r.__dict__ for r in results]
        path.write_text(json.dumps(data, indent=2))
