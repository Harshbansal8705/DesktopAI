import pytest

from src.core.command_safety import is_dangerous_command


@pytest.mark.parametrize(
    "command",
    [
        "ls -la",
        "echo hello",
        "git status",
        "python app.py",
    ],
)
def test_safe_commands_are_not_flagged(command: str) -> None:
    assert not is_dangerous_command(command)


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "sudo apt update",
        "mkfs.ext4 /dev/sda",
        "dd if=/dev/zero of=/dev/sda",
        "chmod -R 777 /",
    ],
)
def test_dangerous_commands_are_flagged(command: str) -> None:
    assert is_dangerous_command(command)


@pytest.mark.parametrize(
    "command",
    [
        "rm    -rf /",
        "echo hello && sudo apt update",
        "git status; rm -rf /tmp/data",
        "echo hello && mkfs.ext4 /dev/sda",
        "echo hello; chmod -R 777 /tmp",
    ],
)
def test_dangerous_syntax_is_detected_with_spacing_and_chains(command: str) -> None:
    assert is_dangerous_command(command)
