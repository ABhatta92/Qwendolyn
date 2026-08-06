from __future__ import annotations

import json
import logging
from pprint import pformat
from typing import Any


class QwendolynFormatter(logging.Formatter):

    default_time_format = "%Y-%m-%d %H:%M:%S"

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        timestamp = self.formatTime(
            record,
            self.default_time_format,
        )

        header = (
            f"{timestamp} | "
            f"{record.levelname:<8} | "
            f"{record.name}"
        )

        message = record.msg

        if record.args:
            message = message % record.args

        if isinstance(
            message,
            dict,
        ):
            message = json.dumps(
                message,
                indent=2,
                default=str,
            )

        elif isinstance(
            message,
            (list, tuple, set),
        ):
            message = pformat(message)

        else:
            message = str(message)

        if record.exc_info:

            message += (
                "\n\n"
                + self.formatException(
                    record.exc_info,
                )
            )

        return f"{header}\n{message}\n"