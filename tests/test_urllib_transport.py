from cicd_control.urllib_transport import UrllibTransport


class TestUrllibTransport:
    def test_init(self, mock_server):
        print(mock_server)
        print(mock_server.ssl_ctx)
