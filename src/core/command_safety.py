"""Validation helpers for potentially dangerous shell commands."""

import re

from src.config import config


def _split_chained_commands(command: str) -> list[str]:
    """Split shell command chains without splitting operators inside quotes."""
    segments = []
    start = 0
    quote = None
    escaped = False
    index = 0

    while index < len(command):
        character = command[index]

        if escaped:
            escaped = False
        elif character == "\\" and quote != "'":
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in {"'", '"'}:
            quote = character
        elif command.startswith(("&&", "||"), index):
            segments.append(command[start:index])
            index += 1
            start = index + 1
        elif character in {";", "|"}:
            segments.append(command[start:index])
            start = index + 1

        index += 1

    segments.append(command[start:])
    return segments


def is_dangerous_command(command: str, patterns: list[str] | None = None) -> bool:
    """Return whether a command or any command in its shell chain matches a pattern."""
    if patterns is None:
        patterns = config.DEFAULT_DANGEROUS_PATTERNS

    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    if any(pattern.search(command) for pattern in compiled_patterns):
        return True

    return any(pattern.search(segment) for segment in _split_chained_commands(command) for pattern in compiled_patterns)
