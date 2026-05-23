import sys
from ordo.config import Config


class Lister:
    @staticmethod
    def list(config: Config, verbose: bool = False) -> None:
        use_color = sys.stdout.isatty()

        def bold(text: str) -> str:
            return f"\033[1m{text}\033[0m" if use_color else text

        def muted(text: str) -> str:
            return f"\033[2m{text}\033[0m" if use_color else text

        for group in config.groups.values():
            header = f"[{group.name}]"
            if group.description:
                header += f"  {group.description}"
            print(bold(header))

            for cmd in group.commands.values():
                desc = f"  {cmd.description}" if cmd.description else ""
                print(f"  {cmd.name:<16}{muted(desc)}")
                if verbose:
                    print(f"  {' ' * 16}{muted('→ ' + cmd.run)}")
            print()