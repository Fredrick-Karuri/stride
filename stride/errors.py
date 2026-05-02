class StrideError(Exception):
    """Base exception for all Stride errors."""

class ConfigNotFoundError(StrideError):
    def __init__(self, checked: list[str]):
        self.checked = checked
        paths = "\n  ".join(checked)
        super().__init__(
            f"No config file found.\n\n"
            f"  Looked in:\n  {paths}\n\n"
            f"  Create a stride.yaml file or set STRIDE_CONFIG=/path/to/file.yaml"
        )

class ConfigParseError(StrideError):
    pass

class UnknownCommandError(StrideError):
    def __init__(self, input_cmd: str, suggestion: str | None = None):
        self.input_cmd = input_cmd
        self.suggestion = suggestion
        msg = f"Unknown command: {input_cmd}"
        if suggestion:
            msg += f"\n  Did you mean: {suggestion}?"
        msg += "\n\n  Run `stride list` to see all available commands."
        super().__init__(msg)

class ValidationError(StrideError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"[{field}] {message}")