from typing import Protocol


from cicd_control.services.volumes import VolumeMount


class ServiceOperator(Protocol):

    def stop(self) -> bool:
        ...

    def start(self) -> bool:
        ...

    def restart(self) -> bool:
        ...

    def reload(self) -> bool:
        ...

    def remove(self) -> bool:
        ...

    def storage(self) -> list[VolumeMount]:
        ...
