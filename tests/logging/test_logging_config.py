import logging
import json
import sys
from unittest.mock import patch


from logging.handlers import RotatingFileHandler


import pytest


from cicd_control.logging.config import JsonFormatter, configure_logging
from cicd_control.logging.masking import RedactionFilter


@pytest.fixture
def clean_logging():
    """
    Fixture to reset the Root Logger before and after tests.
    This prevents 'handler pollution' where one test's config affects another.
    """
    logger = logging.getLogger()

    original_handlers = logger.handlers[:]
    original_filters = logger.filters[:]

    # Clear existing
    logger.handlers = []
    logger.filters = []

    yield

    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)

    for filter_obj in logger.filters:
        logger.removeFilter(filter_obj)

    logger.handlers = original_handlers
    logger.filters = original_filters


class TestJsonFormatter:
    def test_format_structure(self):
        """Verify the JSON structure contains all required ELK fields."""
        formatter = JsonFormatter()

        # Create a dummy log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="User %s logged in",
            args=("admin",),
            exc_info=None
        )

        json_output = formatter.format(record)
        log_dict = json.loads(json_output)

        # Assertions
        assert log_dict["message"] == "User admin logged in"
        assert log_dict["level"] == "INFO"
        assert log_dict["name"] == "test_logger"
        assert "@timestamp" in log_dict
        assert "process_id" in log_dict

    def test_format_exception(self):
        """Verify stack traces are captured in the JSON object."""
        formatter = JsonFormatter()

        try:
            1 / 0
        except ZeroDivisionError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_error",
            level=logging.ERROR,
            pathname=__file__,
            lineno=20,
            msg="Crash occurred",
            args=(),
            exc_info=exc_info
        )

        json_output = formatter.format(record)
        log_dict = json.loads(json_output)

        assert log_dict["message"] == "Crash occurred"
        assert "stack_trace" in log_dict
        assert "ZeroDivisionError" in log_dict["stack_trace"]


@pytest.mark.usefixtures("clean_logging")
class TestLoggingConfig:

    def test_configure_logging_wiring(self, tmp_path):
        with patch("cicd_control.logging.config.LOG_DIR_NAME", str(tmp_path)):
            filter_instance = configure_logging()

        root = logging.getLogger()

        assert isinstance(filter_instance, RedactionFilter)

        stream_handler = next(
            h for h in root.handlers
            if type(h) is logging.StreamHandler
        )

        file_handler = next(
            h for h in root.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        )

        assert filter_instance in stream_handler.filters
        assert filter_instance in file_handler.filters

        assert root.level == logging.DEBUG
        assert stream_handler.level == logging.INFO
        assert file_handler.level == logging.DEBUG

        assert isinstance(file_handler.formatter, JsonFormatter)

    def test_end_to_end_redaction_and_output(self, tmp_path, capsys):
        with patch("cicd_control.logging.config.LOG_DIR_NAME", str(tmp_path)):
            redaction_filter = configure_logging()

        secret = "super_secret_password" # NOSONAR
        redaction_filter.add_secret(secret)

        logger = logging.getLogger("test_e2e")
        logger.info(f"Connecting with {secret} now.")

        captured = capsys.readouterr()
        assert "[REDACTED]" in captured.out
        assert secret not in captured.out
        assert "INFO: Connecting with [REDACTED] now." in captured.out

        log_file = tmp_path / "cicd_control.log"
        assert log_file.exists()

        content = log_file.read_text()
        log_entry = json.loads(content)

        assert log_entry["message"] == "Connecting with [REDACTED] now."
        assert log_entry["level"] == "INFO"
        assert secret not in content