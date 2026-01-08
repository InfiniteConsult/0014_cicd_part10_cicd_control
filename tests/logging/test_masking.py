from logging import LogRecord


import pytest


from cicd_control.logging.masking import RedactionFilter
from cicd_control.errors import InvalidSecretError


class TestRedactionFilter:
    def test_init(self):
        redaction_filter: RedactionFilter = RedactionFilter()
        assert redaction_filter.secrets == set()

    def test_add_secrets(self):
        redaction_filter: RedactionFilter = RedactionFilter()
        redaction_filter.add_secret("secret")
        assert redaction_filter.secrets == {"secret"}

    def test_filter_bad_message(self):
        redaction_filter: RedactionFilter = RedactionFilter()
        log_record: LogRecord = LogRecord("a", 1, "a/b/c", 1, {}, ("",), None, None, None)
        assert redaction_filter.filter(log_record)

    def test_filter_redaction(self):
        redaction_filter: RedactionFilter = RedactionFilter()
        log_record: LogRecord = LogRecord("a", 1, "a/b/c", 1, "I said 'hello world'", ("",), None, None, None)
        redaction_filter.add_secret("hello world")
        redaction_filter.filter(log_record)
        assert log_record.msg == "I said '[REDACTED]'"

    def test_add_bad_secret(self):
        redaction_filter: RedactionFilter = RedactionFilter()
        with pytest.raises(InvalidSecretError, match="secret must be at least 5 characters long"):
            redaction_filter.add_secret("a")

        with pytest.raises(InvalidSecretError, match="secret must be a str"):
            redaction_filter.add_secret({})