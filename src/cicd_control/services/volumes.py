from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeMount:
    host_path: str
    container_path: str
    mode: str = "rw"