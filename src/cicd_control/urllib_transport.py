import json
import socket
import ssl

from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from http.client import HTTPResponse


from cicd_control.transport import HttpResponse
from cicd_control.errors import CicdDnsError, CicdTlsError, CicdConnectionError, CicdTransportError


class UrllibTransport:
    def request(
            self,
            method: str,
            url: str,
            headers: dict[str, str] | None = None,
            body: bytes | None = None
    ) -> HttpResponse:
        request: Request = Request(method=method, url=url, headers=headers or {}, data=body)
        http_e: HTTPError
        url_e: URLError

        try:
            response: HTTPResponse
            with urlopen(request) as response:
                return self._extract_http_response(response)

        except HTTPError as http_e:
            return self._extract_http_error(http_e)

        except URLError as url_e:
            match url_e.reason:
                case socket.gaierror():
                    raise CicdDnsError(f"DNS resolution failed for {url}") from url_e

                case ConnectionRefusedError() | socket.timeout():
                    raise CicdConnectionError(f"Connection failed: {url_e.reason}") from url_e

                case ssl.SSLError():
                    raise CicdTlsError(f"SSL Handshake failed: {url_e.reason}") from url_e

                case _:
                    raise CicdTransportError(f"Network error: {url_e.reason}") from url_e


    @staticmethod
    def _parse_body(raw_body: bytes) -> bytes | dict[str, Any]:
        try:
            return json.loads(raw_body)
        except json.decoder.JSONDecodeError:
            return raw_body

    def _extract_http_response(self, response: HTTPResponse) -> HttpResponse:
        status_code: int = response.getcode()
        response_headers: dict[str, str] = dict(response.getheaders())
        raw_response_body: bytes = response.read()
        return HttpResponse(status_code=status_code, headers=response_headers, body=self._parse_body(raw_response_body))

    def _extract_http_error(self, err: HTTPError) -> HttpResponse:
        status_code: int = err.code
        response_headers: dict[str, str] = dict(err.headers)
        raw_response_body: bytes = err.read()
        return HttpResponse(status_code=status_code, headers=response_headers, body=self._parse_body(raw_response_body))

