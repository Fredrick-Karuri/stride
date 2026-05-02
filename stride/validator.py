from stride.config import Config
from stride.errors import ValidationError


class Validator:
    @staticmethod
    def validate(config: Config) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not config.groups:
            errors.append(ValidationError("groups", "No groups defined"))
            return errors

        for group_name, group in config.groups.items():
            if not group.commands:
                errors.append(ValidationError(f"groups.{group_name}", "No commands defined"))
                continue

            seen = set()
            for cmd_name, cmd in group.commands.items():
                if cmd_name in seen:
                    errors.append(ValidationError(
                        f"groups.{group_name}.{cmd_name}",
                        "Duplicate command name"
                    ))
                seen.add(cmd_name)

                if not cmd.run or not cmd.run.strip():
                    errors.append(ValidationError(
                        f"groups.{group_name}.{cmd_name}",
                        "Missing required field `run`"
                    ))

        return errors