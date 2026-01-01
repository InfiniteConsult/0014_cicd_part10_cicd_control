import pytest
import queue
import socket
import ssl
import threading


from pathlib import Path


class MockServer:
    def __init__(self, key_path: Path, cert_path: Path):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) # NOSONAR
        self.ssl_ctx.load_cert_chain(cert_path, key_path)


@pytest.fixture(scope="function")
def mock_server(tmp_path: Path):
    cert_dir = Path(__file__).parent
    key_path = cert_dir / "key.pem"
    cert_path = cert_dir / "cert.pem"

    server = MockServer(key_path, cert_path)

    yield server
