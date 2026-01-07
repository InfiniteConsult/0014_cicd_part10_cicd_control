from collections.abc import Iterable
from typing import Protocol


class VaultProtocol(Protocol):
    def get(self, key: str) -> str:
        """


        :raises: CicdSecretNotFoundError

        :param str key: The key to look up
        :return: The secret for the given key
        """
        ...

    def store(self, key: str, value: str) -> bool:
        ...

    def overwrite(self, key: str, value: str) -> bool:
        ...

    def iter_secrets(self) -> Iterable[str]:
        ...
