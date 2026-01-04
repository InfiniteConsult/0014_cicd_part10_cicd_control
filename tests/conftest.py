import re

import pytest
import socket
import ssl
import threading

from collections.abc import Callable
from pathlib import Path


CERT_DIR = Path(__file__).parent
KEY_PATH = CERT_DIR / "key.pem"
CERT_PATH = CERT_DIR / "cert.pem"


class MockServer:
    def __init__(self, key_path: Path, cert_path: Path):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.addr: str
        self.port: int
        self.addr, self.port = self.socket.getsockname()
        self.socket.listen(5)

        self.ssl_ctx: ssl.SSLContext= ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_ctx.load_cert_chain(cert_path, key_path)

        self.deal_with_client: Callable[["MockServer", ssl.SSLSocket], None] | None = None

        self.content_length_re: re.Pattern[bytes] = re.compile(rb"Content-Length: (\d+)\r\n", re.IGNORECASE)


    def get_server_address(self) -> tuple[str, int]:
        return self.addr, self.port


    def set_server_callback(self, callback: Callable[["MockServer", ssl.SSLSocket], None]):
        self.deal_with_client = callback

    def handle_accept(self):
        new_socket: socket.socket
        conn_stream: ssl.SSLSocket
        new_socket, _ = self.socket.accept()
        conn_stream = self.ssl_ctx.wrap_socket(new_socket, server_side=True)
        try:
            assert self.deal_with_client is not None
            self.deal_with_client(self, conn_stream)
        finally:
            conn_stream.shutdown(socket.SHUT_RDWR)
            conn_stream.close()

    def read_full_message(self, conn_stream: ssl.SSLSocket) -> bytes:
        response: list[bytes] = []
        header_end_found: bool = False
        content_length_found: bool = False
        content_length: int = 0
        header_bytes: int = -1
        full_response: bytes | None = None

        while True:
            response.append(conn_stream.recv(1024))
            full_response = b"".join(response)
            if not content_length_found:
                content_length_check: list[bytes] = self.content_length_re.findall(full_response)

                if content_length_check:
                    content_length = int(content_length_check[0])
                    content_length_found = True

            if not header_end_found:
                header_end: int = full_response.find(b"\r\n\r\n")
                if header_end != -1:
                    header_end_found = True
                    header_bytes = header_end + 4

            if header_end_found and not content_length_found:
                break

            if header_end_found and content_length_found:
                total_needed: int = header_bytes + content_length
                if len(full_response) >= total_needed:
                    break

        return full_response

@pytest.fixture(scope="function")
def mock_server(tmp_path: Path):
    server: MockServer = MockServer(KEY_PATH, CERT_PATH)
    threading.Thread(target=server.handle_accept).start()
    yield server


@pytest.fixture(scope="function")
def client_context():
    ctx: ssl.SSLContext = ssl.create_default_context()
    ctx.load_verify_locations(CERT_PATH)
    yield ctx