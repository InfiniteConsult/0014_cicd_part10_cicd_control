"""
Common fixtures for testing.

Note, certificates are not supplied with packaged versions of this library (neither is the tests directory itself). To
generate a certificate pair, run

.. code-block:: shell

   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes \\
     -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=localhost"  \\
     -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"


"""
import ssl


from collections.abc import Generator
from pathlib import Path
from typing import Any


import pytest


from cicd_control.fixtures import MockServer


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


@pytest.fixture(scope="function")
def mock_server() -> Generator[MockServer, Any, None]:
    """
    Yields the :class:`MockServer` fixture, already running the accept loop on a separate thread.

    :rtype: Generator[MockServer, Any, None]
    :return: The mock server fixture to which test logic can be assigned.
    """
    server: MockServer = MockServer(KEY_PATH, CERT_PATH)
    handle = server.start_thread()
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