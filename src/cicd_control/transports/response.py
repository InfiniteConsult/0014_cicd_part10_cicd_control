from typing import Any


from dataclasses import dataclass


@dataclass(frozen=True)
class HttpResponse:
    """
    Data container for a completed HTTP request.
    """
    status_code: int
    headers: dict[str, str]
    body: bytes | dict[str, Any]


@dataclass(frozen=True)
class CommandResult:
    """
    Data container for a completed shell/process execution.
    Normalizes output from subprocess/docker/ssh.
    """
    exit_code: int
    stdout: str
    stderr: str
    command: str

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0
