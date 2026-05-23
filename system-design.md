# Ordo — System Design

**Version:** 1.0  
**Project:** Ordo (v1 Python, v2 Go)  
**Last updated:** May 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Folder Structure](#3-folder-structure)
4. [Component Breakdown](#4-component-breakdown)
5. [Config Resolution](#5-config-resolution)
6. [Command Execution](#6-command-execution)
7. [Error Handling Strategy](#7-error-handling-strategy)
8. [CLI Design](#8-cli-design)
9. [Key Design Decisions](#9-key-design-decisions)
10. [Go Rewrite Notes](#10-go-rewrite-notes)

---

## 1. Overview

Ordo is a CLI tool that reads an `ordo.yaml` config, groups shell commands, and runs them via `ordo run group:command`. It has no daemon, no network, no state. Every invocation is stateless and self-contained.

```
ordo.yaml  →  Ordo CLI  →  sh -c "<run string>"
```

---

## 2. Architecture

```
┌─────────────────────────────────────────────┐
│                  CLI Layer                  │
│         (argument parsing, routing)         │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │      Command Router     │
        │  list / run / validate  │
        └────────────┬────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐   ┌──────▼──────┐  ┌────▼──────┐
│  Lister │   │   Runner    │  │ Validator │
└────┬────┘   └──────┬──────┘  └────┬──────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
          ┌──────────▼──────────┐
          │    Config Loader    │
          │  (discover, parse)  │
          └─────────────────────┘
```

All components are thin. Business logic lives in the config loader and runner. The CLI layer only handles I/O.

---

## 3. Folder Structure

```
ordo/
├── ordo/                    # main package
│   ├── __init__.py
│   ├── cli.py               # entry point, argument parsing (Click)
│   ├── config.py            # discovery, parsing, validation
│   ├── runner.py            # command execution, signal handling
│   ├── lister.py            # tool list formatting
│   ├── validator.py         # config validation logic
│   └── errors.py            # custom exception classes
│
├── tests/
│   ├── test_config.py
│   ├── test_runner.py
│   ├── test_lister.py
│   └── test_validator.py
│
├── ordo.yaml                # dogfood: ordo's own dev commands
├── pyproject.toml           # packaging, deps, entry point
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 4. Component Breakdown

### 4.1 `cli.py`
- Entry point registered via `pyproject.toml`
- Uses [Click](https://click.palletsprojects.com/) for argument parsing
- Responsible for: reading flags, calling the right component, printing top-level errors
- No business logic — delegates everything

### 4.2 `config.py`

**`ConfigLoader`**
- `discover(start_dir) -> Path` — finds `ordo.yaml`
- `load(path) -> Config` — reads and parses YAML into a typed dataclass
- `Config` dataclass holds groups → commands → run strings

```python
@dataclass
class Command:
    name: str
    run: str
    description: str | None = None

@dataclass
class Group:
    name: str
    commands: dict[str, Command]
    description: str | None = None

@dataclass
class Config:
    groups: dict[str, Group]
    config_dir: Path          # used to set CWD on execution
```

### 4.3 `runner.py`

**`Runner`**
- `execute(config, group, command, verbose) -> int`
- Sets CWD to `config.config_dir`
- Spawns child via `subprocess.Popen(["sh", "-c", cmd.run])`
- Streams stdout/stderr without buffering
- Registers `SIGINT` handler to forward signal to child
- Returns child exit code

### 4.4 `lister.py`

**`Lister`**
- `list(config, verbose=False)` — prints grouped commands to stdout
- Default: group name + description + command name + description
- Verbose: also prints the raw `run` string

### 4.5 `validator.py`

**`Validator`**
- `validate(config_path) -> list[ValidationError]`
- Checks: valid YAML, required fields, unknown fields, duplicate names, empty groups
- Returns structured errors with line numbers where possible

### 4.6 `errors.py`

```python
class OrdoError(Exception): ...
class ConfigNotFoundError(OrdoError): ...
class ConfigParseError(OrdoError): ...
class UnknownCommandError(OrdoError): ...
class ValidationError(OrdoError): ...
```

---

## 5. Config Resolution

Discovery order (first match wins):

```
1. ORDO_CONFIG env var
2. --config CLI flag
3. ordo.yaml in CWD
4. Walk up directories until .git is found
5. → ConfigNotFoundError with all checked paths listed
```

```python
def discover(start: Path) -> Path:
    for env_var in [os.environ.get("ORDO_CONFIG")]:
        if env_var:
            return Path(env_var)
    current = start
    while True:
        candidate = current / "ordo.yaml"
        if candidate.exists():
            return candidate
        if (current / ".git").exists() or current == current.parent:
            raise ConfigNotFoundError(checked=[...])
        current = current.parent
```

---

## 6. Command Execution

```
ordo run dev:start
     │
     ├── parse "dev:start" → group="dev", command="start"
     ├── load config
     ├── look up config.groups["dev"].commands["start"]
     ├── set CWD = config.config_dir
     ├── register SIGINT handler
     ├── Popen(["sh", "-c", cmd.run], cwd=config_dir)
     ├── stream stdout/stderr
     └── sys.exit(process.returncode)
```

### Signal handling

```python
import signal, subprocess, sys

proc = subprocess.Popen(...)

def handle_sigint(sig, frame):
    proc.send_signal(signal.SIGINT)
    proc.wait()
    sys.exit(proc.returncode)

signal.signal(signal.SIGINT, handle_sigint)
proc.wait()
sys.exit(proc.returncode)
```

### Fuzzy matching for unknown commands

When `group:command` is not found:
1. Build list of all known `group:command` strings
2. Compute [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) against input
3. Suggest closest match if distance ≤ 2
4. Use `difflib.get_close_matches` from stdlib — no extra dependency

---

## 7. Error Handling Strategy

| Scenario | Behaviour |
|---|---|
| Config not found | Exit 1, list all paths checked |
| Invalid YAML | Exit 1, show line/column of parse error |
| Missing `run` field | Exit 1, show field + line number |
| Unknown command | Exit 1, suggest closest match |
| Command exits non-zero | Exit with same code, print `✗ group:cmd exited with code N` |
| Ctrl+C during run | Forward SIGINT to child, exit with child code |

**Rule:** Never exit 0 on an error. Never swallow exceptions silently.

---

## 8. CLI Design

```
ordo                        # shows help
ordo list                   # list all commands
ordo list --verbose         # list with raw run strings
ordo run <group:command>    # execute a command
ordo validate               # validate ordo.yaml
ordo --version              # print version
ordo --help                 # print help
```

Output conventions:
- `✓` prefix for success messages
- `✗` prefix for errors
- Muted group headers, clear command names
- No colour by default; ANSI only if `isatty()` is true

---

## 9. Key Design Decisions

### Why Click over argparse?
Click gives cleaner subcommand routing, automatic `--help` generation, and better error messages with minimal boilerplate. Easy to remove if needed.

### Why `sh -c` instead of `shlex.split`?
Users expect pipes, redirects, and `&&` to work. Shell string execution supports all of this. Documenting it explicitly sets clear expectations.

### Why CWD = config dir, not invocation dir?
Relative paths in `run` strings are almost always relative to the project root, not wherever the dev happens to be. This makes configs portable and predictable.

### Why no plugin system / hooks in v1?
Hooks (pre/post command) add complexity around error handling and exit codes that isn't justified for v1. Add in v2 once the base is stable.

### Why dataclasses over dicts for config?
Type safety, IDE autocompletion, and cleaner access patterns. Makes the Go rewrite easier to reason about since the schema is explicit.

### Why `ordo.yaml` not `tool.yaml`?
The tool has a name now. `ordo.yaml` is self-documenting when you see it in a repo.

---

## 10. Go Rewrite Notes

When you're ready to rewrite in Go, the Python version will have proven the design. Key mappings:

| Python | Go equivalent |
|---|---|
| `dataclass` | `struct` |
| `click` | `cobra` or `flag` stdlib |
| `pyyaml` | `gopkg.in/yaml.v3` |
| `subprocess.Popen` | `os/exec` `Cmd` |
| `difflib.get_close_matches` | `agnivade/levenshtein` or hand-roll |
| `signal.signal` | `os/signal` + `signal.Notify` |
| `sys.exit(code)` | `os.Exit(code)` |

The folder structure maps cleanly:

```
ordo/
├── cmd/ordo/main.go         # entry point
├── internal/
│   ├── config/              # config.py → config/
│   ├── runner/              # runner.py → runner/
│   ├── lister/              # lister.py → lister/
│   └── validator/           # validator.py → validator/
├── go.mod
└── ordo.yaml
```

The Go version will produce a single static binary with no runtime, distributable via `brew`, `curl | sh`, or GitHub releases. That's the payoff for doing v1 in Python first.