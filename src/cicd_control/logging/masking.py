from logging import Filter, LogRecord


from cicd_control.errors import InvalidSecretError, LoggingError


class RedactionFilter(Filter):
    def __init__(self):
        super().__init__()
        self.secrets: set[str] = set()

    def filter(self, record: LogRecord) -> bool:
        """
        Modifies the log record in-place to redact known secrets.

        :param LogRecord record: The log record to check.
        :return: Always True (allow the log to proceed, even if redacted).
        """
        if not isinstance(record.msg, str):
            return True

        secret: str
        for secret in self.secrets:
            if secret in record.msg:
                record.msg = record.msg.replace(secret, "[REDACTED]")

        return super().filter(record)

    def add_secret(self, secret: str) -> None:
        """
        Registers a new secret to be redacted from future log records.

        This method allows the Vault or Service Clients to dynamically update the
        redaction registry at runtime.

        :param str secret: The sensitive string to add to the redaction registry.
        :raises InvalidSecretError: If the secret is not a string or is shorter than
                                    5 characters (to prevent accidental redaction of common words).
        """
        if not isinstance(secret, str):
            raise InvalidSecretError("secret must be a str")

        if len(secret) < 5:
            raise InvalidSecretError("secret must be at least 5 characters long")

        self.secrets.add(secret)