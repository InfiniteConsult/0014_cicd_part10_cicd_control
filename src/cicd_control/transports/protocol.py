from typing import Protocol


from cicd_control.constants import SUBPROCESS_TIMEOUT
from cicd_control.transports.response import HttpResponse, CommandResult



class HttpTransport(Protocol):
    """
    Interface for making HTTP requests.
    """
    def request(
            self,
            method: str,
            url: str,
            headers: dict[str, str] | None = None,
            body: bytes | None = None
    ) -> HttpResponse:
        """
        Performs the specified HTTP request and returns the response.

        :param method: HTTP verb (GET, POST, PUT, DELETE)
        :param url: The full target URL
        :param headers: Optional dictionary of HTTP headers
        :param body: Optional raw bytes payload (for POST/PUT)

        :raises CicdDnsError: If host resolution fails.
        :raises CicdTlsError: If SSL/TLS handshake fails.
        :raises CicdConnectionError: If TCP connection is refused or timed out.
        :raises CicdTransportError: For generic network failures.

        :rtype: HttpResponse
        :return: A structured HttpResponse object (even for 4xx/5xx status codes)
        """
        ...


class ExecutorProtocol(Protocol):
    """
    Interface for running shell commands.
    """
    def run(
            self,
            command: list[str],
            cwd: str | None = None,
            env: dict[str, str] | None = None,
            timeout: int = SUBPROCESS_TIMEOUT
    ) -> CommandResult:
        """
        Runs a shell command and returns the result.

        :param list[str] command: The command broken into a list of strings to prevent shell injection attacks
        :param [str] | None cwd: The directory to run the command in.
        :param dict[str, str] | None env: A dictionary of environment variables to pass to the subprocess environment.
        :param int timeout: Maximum time to wait for a response before giving up.

        :raises CicdSubprocessError: General subprocess failures not caught.
        :raises CicdCommandError: For commands that exit with a failure status.
        :raises CicdExecutableNotFoundError: For executable not found on PATH.


        :rtype: CommandResult
        :return: A structured object representing the status code, stdout and stderr streams and the string of the
                 command itself.
        """
        ...
