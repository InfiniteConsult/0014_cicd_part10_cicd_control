from typing import Protocol, Any
from dataclasses import dataclass


@dataclass
class HttpResponse:
    """
    Data container for a completed HTTP request.
    """
    status_code: int
    headers: dict[str, str]
    body: bytes | dict[str, Any]


class HttpTransport(Protocol):
    def request(
            self,
            method: str,
            url: str,
            headers: dict[str, str] | None = None,
            body: bytes | None = None
    ) -> HttpResponse:
        """
        Executes an HTTP request.

        :param method: HTTP verb (GET, POST, PUT, DELETE)
        :param url: The full target URL
        :param headers: Optional dictionary of HTTP headers
        :param body: Optional raw bytes payload (for POST/PUT)

        :raises CicdDnsError: If host resolution fails.
        :raises CicdTlsError: If SSL/TLS handshake fails.
        :raises CicdConnectionError: If TCP connection is refused or timed out.
        :raises CicdTransportError: For generic network failures.

        :return: A structured HttpResponse object (even for 4xx/5xx status codes)
        """
        ...