# Ordo

A structured command runner — a clean alternative to `make`.

Ordo reads an `ordo.yaml` config, groups your commands logically, and runs them with a simple `group:command` syntax. No more flat Makefiles. No more guessing what commands exist.

---

## Why not make?

| | `make` | Ordo |
|---|---|---|
| Grouped commands | ✗ | ✓ |
| Built-in discovery | ✗ | ✓ |
| Per-command descriptions | ✗ | ✓ |
| Readable config | Makefiles | YAML |
| Typo suggestions | ✗ | ✓ |

---

## Installation

**Standalone binary — no Python required:**

Download the binary for your platform from the [latest release](https://github.com/fredrick-karuri/ordo/releases/latest) and put it on your PATH.

| Platform | File |
|---|---|
| macOS | `ordo-macos` |
| Linux | `ordo-linux` |
| Windows | `ordo-windows.exe` |

**Via PyPI:**

```bash
pip install ordo-cli
# or
pipx install ordo-cli
```

---

## Quick start

Create an `ordo.yaml` at your project root:

```yaml
groups:
  dev:
    description: Local development
    commands:
      start:
        description: Start the API server
        run: "uvicorn app.main:app --reload"
      reset:
        description: Reset local database
        run: "python scripts/reset_db.py"

  test:
    description: Test suite
    commands:
      run:
        description: Run all tests
        run: "pytest"
      watch:
        description: Run tests in watch mode
        run: "pytest --watch"
```

Then:

```bash
ordo list          # see all commands
ordo dev:start     # run one
ordo validate      # check your config
```

---

## CLI reference

```
ordo list                     List all commands
ordo list --verbose           Also show raw run strings
ordo <group:command>          Execute a command
ordo validate                 Validate ordo.yaml
ordo --version                Print version
ordo --help                   Print help
```

---

## ordo.yaml reference

```yaml
groups:
  <group-name>:
    description: string        # optional — shown in ordo list
    commands:
      <command-name>:
        description: string    # optional — shown in ordo list
        run: string            # required — shell command to execute
```

**Naming rules:**
- Group and command names: lowercase letters, numbers, hyphens only
- No spaces
- Names must be unique within their scope

**All `run` strings execute via `sh -c`** — pipes, redirects, `&&`, and env vars all work as expected.

---

## Config discovery

Ordo finds `ordo.yaml` in this order:

1. `ORDO_CONFIG` environment variable
2. `--config` CLI flag
3. `ordo.yaml` in current directory
4. Walk up the directory tree until `.git` is found

You can run `ordo` from any subdirectory in your repo — it will find the config.

---

## Error behaviour

- All errors exit with code 1
- Child process exit codes are forwarded exactly
- Typos get a fuzzy suggestion: `Did you mean: dev:start?`
- `Ctrl+C` cleanly stops the child process — no zombie processes

---

## License

MIT