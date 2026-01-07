from typing import Protocol


from cicd_control.transports.protocol import HttpTransport, ExecutorProtocol
from cicd_control.services.protocol import ServiceOperator


class ServiceClientProtocol(Protocol):
    """
    The universal contract that all service integrations (Gitlab, Jenkins, etc.) must implement
    """
    http: HttpTransport
    executor: ExecutorProtocol
    operator: ServiceOperator

    def __init__(
            self,
            http_transport: HttpTransport,
            executor_transport: ExecutorProtocol,
            service_operator: ServiceOperator
    ) -> None:
        """
        Injects the standardized network, shell executors and operators

        :param HttpTransport http_transport: Underlying transport to interact with APIs
        :param ExecutorProtocol executor_transport:  Underlying transport to interact with shell based commands
        :param ServiceOperator service_operator: Underlying operator to manage lifecycle of services
        """
        ...

    def is_healthy(self) -> bool:
        ...

    def get_version(self) -> str:
        ...

    def harvest_credentials(self) -> dict[str, str]:
        ...

    def configure(self, secrets: dict[str, str]) -> None:
        ...