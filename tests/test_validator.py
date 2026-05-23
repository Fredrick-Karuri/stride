import pytest
from ordo.config import parse
from ordo.validator import Validator


def test_valid_config_returns_no_errors(tmp_config):
    config = parse(tmp_config())
    errors = Validator.validate(config)
    assert errors == []

def test_empty_groups_returns_error(tmp_config):
    config = parse(tmp_config("""
groups:
  dev:
    commands:
      start:
        run: "echo hi"
"""))
    # manually clear groups to simulate empty
    config.groups = {}
    errors = Validator.validate(config)
    assert any("No groups" in str(e) for e in errors)

def test_group_with_no_commands_returns_error(tmp_config):
    config = parse(tmp_config("""
groups:
  dev:
    description: Dev
    commands:
      start:
        run: "echo hi"
"""))
    config.groups["dev"].commands = {}
    errors = Validator.validate(config)
    assert any("dev" in str(e) for e in errors)

def test_command_with_empty_run_returns_error(tmp_config):
    config = parse(tmp_config("""
groups:
  dev:
    commands:
      start:
        run: "echo hi"
"""))
    config.groups["dev"].commands["start"].run = ""
    errors = Validator.validate(config)
    assert any("run" in str(e) for e in errors)

def test_multiple_errors_all_returned(tmp_config):
    config = parse(tmp_config("""
groups:
  dev:
    commands:
      start:
        run: "echo hi"
  test:
    commands:
      run:
        run: "pytest"
"""))
    config.groups["dev"].commands["start"].run = ""
    config.groups["test"].commands = {}
    errors = Validator.validate(config)
    assert len(errors) >= 2