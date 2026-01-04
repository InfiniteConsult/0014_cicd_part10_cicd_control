"""
Common fixtures for testing.

Note, certificates are not supplied with packaged versions of this library (neither is the tests directory itself). To
generate a certificate pair, run

.. code-block:: shell

   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes \\
     -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=localhost"  \\
     -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"


"""
import re
import socket
import ssl
import threading


from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any


import pytest


CERT_DIR = Path(__file__).parent
"""
Finds the location of this file's directory. The certificates are located as siblings to the file.
"""

KEY_PATH = CERT_DIR / "key.pem"
"""
The private key for the :class:`MockServer` to use.
"""

CERT_PATH = CERT_DIR / "cert.pem"
"""
The publick key for the :class:`MockServer` to use.
"""


class MockServer:
    """
    A programmable mock server for testing. Yielded from :func:`mock_server` by default but can be used as a standalone
    test server.

    For fixture usage:

    .. code-block:: python

       def test_mock_server_get(mock_server: MockServer, client_context: ssl.SSLContext):
           addr: str
           port: int
           addr, port = mock_server.get_server_address()

           req: Request = Request(f"https://{addr}:{port}")

           def callback(server: MockServer, sock: ssl.SSLSocket):
               message: bytes  = server.read_full_message(sock)
               sock.sendall(b"HTTP/1.1 200 OK\r\nX-Auth: something\r\n\r\n")

           mock_server.set_server_callback(callback)

    For usage as a class:

    .. code-block:: python

       server: MockServer = MockServer(KEY_PATH, CERT_PATH)
       handle: threading.Thread = threading.Thread(target=server.handle_accept)
       handle.start()

    Note the pattern of defining the callback within the test function. This effectively creates a closure because
    the callback has local scope of the variables within the function.
    """
    def __init__(self, key_path: Path, cert_path: Path) -> None:
        """
        Binds and listens for incoming connections. To handle connections, start the :meth:`handle_accept` method on a
        new thread.

        :param Path key_path: Path to the private key file.
        :param Path cert_path: Path to the public key file.
        """
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.addr: str
        self.port: int
        self.addr, self.port = self.socket.getsockname()
        self.socket.listen(5)
        self.socket.settimeout(5)

        self.ssl_ctx: ssl.SSLContext= ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_ctx.load_cert_chain(cert_path, key_path)

        self.deal_with_client: Callable[["MockServer", ssl.SSLSocket], None] | None = None

        self.content_length_re: re.Pattern[bytes] = re.compile(rb"Content-Length: (\d+)\r\n", re.IGNORECASE)


    def get_server_address(self) -> tuple[str, int]:
        """
        Returns the tuple (addr, port), allowing clients to bind to the randomly selected port that the server
        is listening on.

        :rtype: tuple[str, int]
        :return: The address as a string (localhost) and the port as an integer.
        """
        return self.addr, self.port


    def set_server_callback(self, callback: Callable[["MockServer", ssl.SSLSocket], None]) -> None:
        """
        Sets the callback to run for testing. This must be supplied. It takes an instance of :class:`MockServer` and
        :class:`SSLSocket` as parameters so you can access the methods of this fixture. The first call should always
        be `:meth:`MockServer.read_full_message` to read the client's first message unless testing client's ability to
        handle abnormal closures.

        :param Callable[["MockServer", ssl.SSLSocket], None] callback: The logic to run server side.
        """
        self.deal_with_client = callback

    def handle_accept(self) -> None:
        """
        Handle's one client then shuts down the connection. You can handle a keep alive scenario through the callback
        you supply to the server.
        """
        new_socket: socket.socket
        conn_stream: ssl.SSLSocket
        try:
            new_socket, _ = self.socket.accept()
        except TimeoutError:
            return

        conn_stream = self.ssl_ctx.wrap_socket(new_socket, server_side=True)
        try:
            assert self.deal_with_client is not None
            self.deal_with_client(self, conn_stream)
        finally:
            conn_stream.shutdown(socket.SHUT_RDWR)
            conn_stream.close()

    def read_full_message(self, conn_stream: ssl.SSLSocket) -> bytes:
        """
        Convenience function to read the full message and return it. It handles the client supplying a content length
        for POST requests or normal GET requests that don't supply a body.

        Call multiple times in a callback to read subsequent messages and keep the connection alive.

        :param ssl.SSLSocket conn_stream: a TLS wrapped socket (supplied in the callback)
        :rtype: bytes
        :return: A byte string representing a single message from the client.
        """
        response: list[bytes] = []
        header_end_found: bool = False
        content_length_found: bool = False
        content_length: int = 0
        header_bytes: int = -1
        full_response: bytes | None

        while True:
            # Read in a piece of the response.
            response.append(conn_stream.recv(1024))

            # Highly inefficient but okay for small tests.
            full_response = b"".join(response)

            # Check if we have found a content length header or have reached the end of the headers.
            if not content_length_found:
                content_length, content_length_found = self._check_content_length(full_response)

            if not header_end_found:
                header_bytes, header_end_found = self._check_header_length(full_response)

            # In the case of a GET request, we won't have content length since the client does not submit a body.
            if header_end_found and not content_length_found:
                break

            # Check if we have read the full message and return if so.
            if header_end_found and content_length_found:
                total_needed: int = header_bytes + content_length
                if len(full_response) >= total_needed:
                    break

        return full_response

    def _check_content_length(self, full_response: bytes) -> tuple[int, bool]:
        """
        Checks for the existence of a content length header, extracts its value and signals that content length has
        been found.

        :param bytes full_response: The client's request.
        :rtype: tuple[int, bool]
        :return: The content length and a flag signaling if it was found. If not found, content length returns 0.
        """
        content_length_found: bool
        content_length: int

        content_length_check: list[bytes] = self.content_length_re.findall(full_response)

        if content_length_check:
            content_length = int(content_length_check[0])
            content_length_found = True
        else:
            content_length = 0
            content_length_found = False

        return content_length, content_length_found

    @staticmethod
    def _check_header_length(full_response: bytes) -> tuple[int, bool]:
        """
        Checks if we have received the full set of headers.

        :param bytes full_response: The client's request.
        :rtype: tuple[int, bool]
        :return: The index in the string that represents the end of the header HTTP headers and a flag denoting if the
                 end was found. The index defaults to -1 if not found.
        """
        header_end_found: bool
        header_bytes: int

        header_end: int = full_response.find(b"\r\n\r\n")
        if header_end != -1:
            header_end_found = True
            header_bytes = header_end + 4
        else:
            header_end_found = False
            header_bytes = -1

        return header_bytes, header_end_found


@pytest.fixture(scope="function")
def mock_server() -> Generator[MockServer, Any, None]:
    """
    Yields the :class:`MockServer` fixture, already running the accept loop on a separate thread.

    :rtype: Generator[MockServer, Any, None]
    :return: The mock server fixture to which test logic can be assigned.
    """
    server: MockServer = MockServer(KEY_PATH, CERT_PATH)
    handle: threading.Thread = threading.Thread(target=server.handle_accept)
    handle.start()
    yield server
    handle.join()


@pytest.fixture(scope="function")
def client_context() -> Generator[ssl.SSLContext, Any, None]:
    """
    A client context that trusts the development certificates in the tests folder and hence instances of
    :class:`MockServer`.

    :rtype: Generator[ssl.SSLContext, Any, None]
    :return: An SSLContext that can be used with libraries.
    """
    ctx: ssl.SSLContext = ssl.create_default_context()
    ctx.load_verify_locations(CERT_PATH)
    yield ctx