import json
import ssl
import http.client


import pytest


from urllib.request import Request, urlopen


from conftest import MockServer


def test_mock_server_get(mock_server, client_context):
    addr: str
    port: int
    addr, port =mock_server.get_server_address()

    req: Request = Request(f"https://{addr}:{port}")

    def callback(server: MockServer, sock: ssl.SSLSocket):
        message: bytes  = server.read_full_message(sock)
        assert message.find(b"GET / HTTP/1.1\r\n") != -1
        sock.sendall(b"HTTP/1.1 200 OK\r\nX-Auth: something\r\n\r\n")

    mock_server.set_server_callback(callback)

    response: http.client.HTTPResponse
    with urlopen(req, context=client_context) as response:
        assert dict(response.headers.items()) == {"X-Auth": "something"}
        assert response.status == 200


def test_mock_server_post(mock_server, client_context):
    addr: str
    port: int
    addr, port =mock_server.get_server_address()

    req: Request = Request(f"https://{addr}:{port}", data=json.dumps({"hello": "world"}).encode())

    def callback(server: MockServer, sock: ssl.SSLSocket):
        a = server.read_full_message(sock)
        assert a.find(b'hello') != -1
        assert a.find(b'world') != -1
        sock.sendall(b"HTTP/1.1 200 OK\r\n")

    mock_server.set_server_callback(callback)

    response: http.client.HTTPResponse
    with urlopen(req, context=client_context) as response:
        assert  response.status == 200