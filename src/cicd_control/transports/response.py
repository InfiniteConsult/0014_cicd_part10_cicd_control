from typing import Any


from dataclasses import dataclass


@dataclass
class HttpResponse:
    """
    Data container for a completed HTTP request.
    """
    status_code: int
    headers: dict[str, str]
    body: bytes | dict[str, Any]