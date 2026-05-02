import os
import pytest
from pathlib import Path
from stride.config import parse, discover, Command, Group, Config
from stride.errors import ConfigNotFoundError, ConfigParseError


# --- STRIDE-003: dataclasses ---

def test_command_dataclass():
    cmd = Command(name="start", run="uvicorn app:app")
    assert cmd.name == "start"
    assert cmd.run == "uvicorn app:app"
    assert cmd.description is None

def test_command_with_description():
    cmd = Command(name="start", run="uvicorn app:app", description="Start server")
    assert cmd.description == "Start server"

def test_group_dataclass():
    cmd = Command(name="start", run="uvicorn")
    group = Group(name="dev", commands={"start": cmd}, description="Dev commands")
    assert group.name == "dev"
    assert group.commands["start"] is cmd

def test_config_dataclass(tmp_path):
    config = Config(groups={}, config_dir=tmp_path)
    assert config.config_dir == tmp_path


# --- STRIDE-004: config parser ---

def test_parse_valid_config(tmp_config):
    path = tmp_config()
    config = parse(path)
    assert "dev" in config.groups
    assert "test" in config.groups
    assert config.groups["dev"].commands["start"].run == "uvicorn app.main:app --reload"
    assert config.groups["dev"].description == "Local development"

def test_parse_sets_config_dir(tmp_config, tmp_path):
    path = tmp_config()
    config = parse(path)
    assert config.config_dir == tmp_path

def test_parse_optional_description_missing(tmp_config):
    path = tmp_config("""
groups:
  dev:
    commands:
      start:
        run: "echo hi"
""")
    config = parse(path)
    assert config.groups["dev"].description is None
    assert config.groups["dev"].commands["start"].description is None

def test_parse_missing_run_raises(tmp_config):
    path = tmp_config("""
groups:
  dev:
    commands:
      start:
        description: "no run field here"
""")
    with pytest.raises(ConfigParseError, match="missing required field `run`"):
        parse(path)

def test_parse_invalid_yaml_raises(tmp_config):
    path = tmp_config("groups: [this: is: broken: yaml")
    with pytest.raises(ConfigParseError, match="Invalid YAML"):
        parse(path)

def test_parse_missing_groups_key_raises(tmp_config):
    path = tmp_config("something: else")
    with pytest.raises(ConfigParseError, match="groups"):
        parse(path)


# --- STRIDE-005: config discovery ---

def test_discover_in_cwd(tmp_config, tmp_path):
    path = tmp_config()
    found = discover(start=tmp_path)
    assert found == path

def test_discover_walks_up(tmp_config, tmp_path):
    path = tmp_config()
    subdir = tmp_path / "a" / "b"
    subdir.mkdir(parents=True)
    found = discover(start=subdir)
    assert found == path

def test_discover_stops_at_git_boundary(tmp_path):
    (tmp_path / ".git").mkdir()
    subdir = tmp_path / "src"
    subdir.mkdir()
    # No stride.yaml anywhere, .git is at tmp_path
    with pytest.raises(ConfigNotFoundError) as exc:
        discover(start=subdir)
    assert str(tmp_path / "stride.yaml") in exc.value.checked

def test_discover_respects_env_var(tmp_config, monkeypatch):
    path = tmp_config()
    monkeypatch.setenv("STRIDE_CONFIG", str(path))
    found = discover()
    assert found == path

def test_discover_not_found_lists_checked_paths(tmp_path):
    (tmp_path / ".git").mkdir()  # stop walking here
    with pytest.raises(ConfigNotFoundError) as exc:
        discover(start=tmp_path)
    assert len(exc.value.checked) >= 1
    assert "stride.yaml" in exc.value.checked[0]