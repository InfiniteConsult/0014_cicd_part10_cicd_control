import logging
import sys
import json
from datetime import datetime, UTC

from logging.handlers import RotatingFileHandler
from pathlib import Path


from cicd_control.constants import LOG_DIR_NAME
from cicd_control.logging.masking import RedactionFilter


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, str | int] = {
            "@timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
        }

        if record.exc_info:
            log_record["stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging() -> RedactionFilter:
    log_dir_path: Path = Path(LOG_DIR_NAME)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    logger: logging.Logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    redaction_filter: RedactionFilter = RedactionFilter()

    stream_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    file_handler: RotatingFileHandler = RotatingFileHandler(
        log_dir_path / "cicd_control.log",
        maxBytes=1024 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    console_formatter: logging.Formatter = logging.Formatter("%(levelname)s: %(message)s")
    json_formatter: JsonFormatter = JsonFormatter()

    stream_handler.addFilter(redaction_filter)
    file_handler.addFilter(redaction_filter)
    stream_handler.setFormatter(console_formatter)
    file_handler.setFormatter(json_formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return redaction_filter