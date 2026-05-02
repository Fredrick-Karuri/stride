import difflib
import signal
import subprocess
import sys
from stride.config import Config
from stride.errors import UnknownCommandError


class Runner:
    @staticmethod
    def execute(config: Config, group_command: str) -> int:
        # Parse group:command
        if ":" not in group_command:
            raise UnknownCommandError(group_command)

        group_name, cmd_name = group_command.split(":", 1)

        # Look up command
        group = config.groups.get(group_name)
        cmd = group.commands.get(cmd_name) if group else None

        if not cmd:
            # Fuzzy suggestion
            all_cmds = [
                f"{g}:{c}"
                for g, grp in config.groups.items()
                for c in grp.commands
            ]
            matches = difflib.get_close_matches(group_command, all_cmds, n=1, cutoff=0.6)
            suggestion = matches[0] if matches else None
            raise UnknownCommandError(group_command, suggestion)

        # Execute
        proc = subprocess.Popen(
            ["sh", "-c", cmd.run],
            cwd=config.config_dir,
        )

        def handle_sigint(sig, frame):
            proc.send_signal(signal.SIGINT)
            proc.wait()
            code = proc.returncode
            if code != 0:
                print(f"\n✗ {group_command} exited with code {code}", file=sys.stderr)
            sys.exit(code)

        signal.signal(signal.SIGINT, handle_sigint)
        proc.wait()

        if proc.returncode != 0:
            print(f"✗ {group_command} exited with code {proc.returncode}", file=sys.stderr)

        return proc.returncode