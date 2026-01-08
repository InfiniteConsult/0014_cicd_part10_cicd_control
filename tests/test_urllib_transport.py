import socket
import ssl
import time


from urllib.error import URLError
from unittest.mock import patch


import pytest


from cicd_control.urllib_transport import UrllibTransport, HttpResponse
from cicd_control.errors import CicdDnsError, CicdTlsError, CicdConnectionError, CicdTransportError
from cicd_control.fixtures import MockServer


def get_mock_server_url(server: MockServer) -> str:
    addr: str
    port: int
    addr, port = server.get_server_address()
    url: str = f"https://{addr}:{port}"
    return url


def set_single_response_callback(server: MockServer, server_response: bytes) -> None:
    def callback(callback_server: MockServer, sock: ssl.SSLSocket):
        try:
            _: bytes = callback_server.read_full_message(sock)
            sock.sendall(server_response)
        except Exception as exc:
            print(exc)
    server.set_server_callback(callback)


def get_response(
        ctx: ssl.SSLContext,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None
) -> HttpResponse | None:
    transport: UrllibTransport = UrllibTransport(ctx)
    response: HttpResponse = transport.request(method, url, headers, body)
    return response


expected_and_http_error_paths: list[tuple[bytes, bytes, bytes, int, bytes | dict[str, str]]] = [
    (
        b"HTTP/1.1 200 OK",
        b"Content-Type: application/json\r\nContent-Length: 18",
        b'{"status": "json"}',
        200,
        {"status": "json"}
    ),
    # Case 2: Happy Path Text
    (
        b"HTTP/1.1 200 OK",
        b"Content-Type: text/plain\r\nContent-Length: 10",
        b"Just bytes",
        200,
        b"Just bytes"
    ),
    # Case 3: 404 Not Found (Handled by except HTTPError branch)
    (
        b"HTTP/1.1 404 Not Found",
        b"Content-Type: application/json\r\nContent-Length: 15",
        b'{"err": "oops"}',
        404,
        {"err": "oops"}
    ),
    # Case 4: 500 Server Error
    (
        b"HTTP/1.1 500 Server Error",
        b"Content-Type: text/plain\r\nContent-Length: 12",
        b"Server crash",
        500,
        b"Server crash"
    )
]

class TestUrllibTransport:
    def test_init(self, client_context):
        transport: UrllibTransport = UrllibTransport()
        assert transport.context is not None
        assert transport.context != client_context

        transport = UrllibTransport(client_context)
        assert transport.context is not None
        assert transport.context == client_context

    @pytest.mark.parametrize(
        "status_line, headers, body_bytes, expected_status, expected_body",
        expected_and_http_error_paths
    )
    def test_http_responses(
            self,
            mock_server,
            client_context,
            status_line,
            headers,
            body_bytes,
            expected_status,
            expected_body
    ):
        full_response: bytes = status_line + b"\r\n" + headers + b"\r\n\r\n" + body_bytes

        set_single_response_callback(mock_server, full_response)

        url: str = get_mock_server_url(mock_server)
        transport: UrllibTransport = UrllibTransport(client_context)
        response: HttpResponse = transport.request("GET", url)
        cleaned_headers: dict[str, str] = {
            k.decode(): v.decode().strip() for k, v in [x.split(b":") for x in headers.split(b"\r\n")]
        }
        assert response.status_code == expected_status
        assert response.body == expected_body
        assert response.headers == cleaned_headers

    def test_connection_failures(self, mock_server, client_context):
        transport: UrllibTransport = UrllibTransport()

        url: str = "https://this-domain-does-not-exist.invalid"
        with pytest.raises(CicdDnsError, match=f"DNS resolution failed for {url}"):
            transport.request("GET", url)

        url = "https://localhost:0"
        with pytest.raises(CicdConnectionError, match="Connection failed:"):
            transport.request("GET", url)

        url: str = get_mock_server_url(mock_server)
        with pytest.raises(CicdTlsError, match="SSL Handshake failed: "):
            transport.request("GET", url)

        original_timeout: float | None= socket.getdefaulttimeout()
        if original_timeout is None:
            original_timeout = 5.0

        socket.setdefaulttimeout(0.1)
        def callback(server: MockServer, sock: ssl.SSLSocket):
            _: bytes = server.read_full_message(sock)
            time.sleep(0.2)
            sock.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

        mock_server.set_server_callback(callback)
        transport = UrllibTransport(client_context)
        with pytest.raises(CicdConnectionError, match="The handshake operation timed out"):
            transport.request("GET", url)
        socket.setdefaulttimeout(original_timeout)

        with pytest.raises(CicdTransportError, match="Request error unknown url type: '#! /usr/bin/env python'"):
            transport.request("GET", "#! /usr/bin/env python")

    def test_unhandled_url_error(self, client_context):
        transport = UrllibTransport(client_context)
        url = "https://example.com"

        unhandled_reason = BrokenPipeError("Connection reset by peer")

        with patch("cicd_control.urllib_transport.urlopen", side_effect=URLError(reason=unhandled_reason)):
            with pytest.raises(CicdTransportError, match=f"Network error: {unhandled_reason}"):
                transport.request("GET", url)

    def test_protocol_violation(self, mock_server, client_context):
        def callback(server: MockServer, sock: ssl.SSLSocket):
            server.read_full_message(sock)
            sock.sendall(b"NOT_HTTP_PROTOCOL_GARBAGE\r\n\r\n")
        mock_server.set_server_callback(callback)

        url: str = get_mock_server_url(mock_server)
        transport = UrllibTransport(client_context)

        with pytest.raises(CicdTransportError, match="General error: NOT_HTTP_PROTOCOL_GARBAGE"):
            transport.request("GET", url)