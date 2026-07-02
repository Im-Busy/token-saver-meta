import pytest
from pathlib import Path
from . import t1_csv_cli, t2_exploration, t3_shell_output, t4_endpoint, t5_debug

def test_t1_config_valid():
    cfg = t1_csv_cli.get_config()
    assert cfg.task_id == "t1_csv_cli"
    assert "CSV" in cfg.prompt
    assert cfg.fixture_path.name == "csv_cli"
    assert cfg.saver_enabled is True

def test_t2_config_valid():
    cfg = t2_exploration.get_config()
    assert cfg.task_id == "t2_exploration"
    assert "processPayment" in cfg.prompt
    assert cfg.fixture_path.name == "payment_app"

def test_t3_config_valid():
    cfg = t3_shell_output.get_config()
    assert cfg.task_id == "t3_shell_output"
    assert "npm install" in cfg.prompt.lower()
    assert cfg.fixture_path.name == "npm_error"

def test_t4_config_valid():
    cfg = t4_endpoint.get_config()
    assert cfg.task_id == "t4_endpoint"
    assert "/api/users" in cfg.prompt
    assert cfg.fixture_path.name == "api_app"

def test_t5_config_valid():
    cfg = t5_debug.get_config()
    assert cfg.task_id == "t5_debug"
    assert "500" in cfg.prompt
    assert cfg.fixture_path.name == "auth_bug"

def test_all_fixture_paths_exist():
    for mod in [t1_csv_cli, t2_exploration, t3_shell_output, t4_endpoint, t5_debug]:
        cfg = mod.get_config()
        assert cfg.fixture_path.exists(), f"Missing: {cfg.fixture_path}"

def test_t5_prompt_does_not_reveal_bug():
    cfg = t5_debug.get_config()
    assert "null check" not in cfg.prompt.lower()
    assert "user.email" not in cfg.prompt
    assert "findUser" not in cfg.prompt
