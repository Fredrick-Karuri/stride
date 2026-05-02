from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from stride.errors import ConfigNotFoundError, ConfigParseError


@dataclass
class Command:
    name: str
    run: str
    description: str | None = None


@dataclass
class Group:
    name: str
    commands: dict[str, Command] = field(default_factory=dict)
    description: str | None = None


@dataclass
class Config:
    groups: dict[str, Group]
    config_dir: Path


def discover(start: Path | None = None) -> Path:
    """Find stride.yaml by env var or walking up from start dir."""
    env = os.environ.get("STRIDE_CONFIG")
    if env:
        p = Path(env)
        if p.exists():
            return p
        raise ConfigNotFoundError([str(p)])

    current = Path(start or Path.cwd()).resolve()
    checked = []

    while True:
        candidate = current / "stride.yaml"
        checked.append(str(candidate))
        if candidate.exists():
            return candidate
        if (current / ".git").exists() or current == current.parent:
            raise ConfigNotFoundError(checked)
        current = current.parent


def parse(path: Path) -> Config:
    """Parse stride.yaml into a Config dataclass."""
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ConfigParseError(f"Invalid YAML in {path}: {e}")

    if not isinstance(raw, dict) or "groups" not in raw:
        raise ConfigParseError("Missing required top-level key: `groups`")

    groups: dict[str, Group] = {}
    for group_name, group_data in raw["groups"].items():
        if not isinstance(group_data, dict):
            raise ConfigParseError(f"Group `{group_name}` must be a map")

        commands: dict[str, Command] = {}
        raw_commands = group_data.get("commands", {}) or {}
        for cmd_name, cmd_data in raw_commands.items():
            if not isinstance(cmd_data, dict) or "run" not in cmd_data:
                raise ConfigParseError(
                    f"Command `{group_name}.{cmd_name}` is missing required field `run`"
                )
            commands[cmd_name] = Command(
                name=cmd_name,
                run=cmd_data["run"],
                description=cmd_data.get("description"),
            )

        groups[group_name] = Group(
            name=group_name,
            commands=commands,
            description=group_data.get("description"),
        )

    return Config(groups=groups, config_dir=path.parent)


def load_config(config_path: str | None = None) -> Config:
    """Discover (or use provided path) and parse config."""
    path = Path(config_path) if config_path else discover()
    return parse(path)