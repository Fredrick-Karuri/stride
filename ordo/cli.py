import sys
import click
from ordo import __version__

@click.group()
@click.version_option(__version__, prog_name="ordo")
def main():
    """Ordo — structured command runner."""
    pass

@main.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show raw run strings.")
@click.option("--config", "config_path", default=None, help="Path to ordo.yaml.")
def list_cmd(verbose, config_path):
    """List all available commands."""
    from ordo.config import load_config
    from ordo.lister import Lister
    try:
        config = load_config(config_path)
        Lister.list(config, verbose=verbose)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)

@main.command("run")
@click.argument("command")
@click.option("--config", "config_path", default=None, help="Path to ordo.yaml.")
def run_cmd(command, config_path):
    """Run a command using group:command syntax."""
    from ordo.config import load_config
    from ordo.runner import Runner
    try:
        config = load_config(config_path)
        code = Runner.execute(config, command)
        sys.exit(code)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)

@main.command("validate")
@click.option("--config", "config_path", default=None, help="Path to ordo.yaml.")
def validate_cmd(config_path):
    """Validate ordo.yaml before runtime."""
    from ordo.config import load_config
    from ordo.validator import Validator
    try:
        config = load_config(config_path)
        errors = Validator.validate(config)
        if errors:
            click.echo(f"✗ ordo.yaml has {len(errors)} error(s):\n", err=True)
            for e in errors:
                click.echo(f"  {e}", err=True)
            sys.exit(1)
        total_commands = sum(len(g.commands) for g in config.groups.values())
        click.echo(f"✓ ordo.yaml is valid ({len(config.groups)} groups, {total_commands} commands)")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)