import logging

import breez_sdk
from config import settings


class BreezLogger(breez_sdk.LogStream):
    def __init__(self, level=logging.INFO):
        super().__init__()
        self.log_level = level

    def log(self, record, *args, **kwargs):
        """
        Processes a log entry using a string-based log level.
        The record is expected to have a 'level' attribute (a string like "TRACE", "INFO", etc.).
        """
        # Map the string level to a numeric logging level
        level_map = {
            "TRACE": logging.DEBUG,  # Map TRACE to DEBUG
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        record_level_str = record.level.upper() if hasattr(record, "level") else "INFO"
        mapped_level = level_map.get(record_level_str, logging.INFO)

        # Only process the message if its mapped level is >= the configured level.
        if mapped_level < self.log_level:
            return

        # Retrieve the message text.
        message = record.getMessage() if hasattr(record, "getMessage") else str(record)
        print(message)
