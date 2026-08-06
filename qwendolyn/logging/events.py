from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Event:

    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    component: str = ""

    event: str = ""

    data: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


class EventStore:

    def __init__(
        self,
        path: str | Path,
    ):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.path.exists():

            self.path.write_text(
                "",
                encoding="utf-8",
            )

    def emit(
        self,
        component: str,
        event: str,
        **data: Any,
    ) -> Event:

        record = Event(
            component=component,
            event=event,
            data=data,
        )

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    record.to_dict(),
                    default=str,
                )
            )

            file.write("\n")

        return record

    def read(
        self,
    ) -> list[Event]:

        events: list[Event] = []

        if not self.path.exists():
            return events

        with self.path.open(
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                payload = json.loads(line)

                events.append(
                    Event(
                        timestamp=payload["timestamp"],
                        component=payload["component"],
                        event=payload["event"],
                        data=payload.get(
                            "data",
                            {},
                        ),
                    )
                )

        return events

    def clear(
        self,
    ) -> None:

        self.path.write_text(
            "",
            encoding="utf-8",
        )