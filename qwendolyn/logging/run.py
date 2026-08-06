from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from qwendolyn import config


@dataclass(slots=True)
class Run:

    agent: str

    objective: str

    run_id: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + "_"
        + uuid4().hex[:8]
    )

    started_at: datetime = field(
        default_factory=datetime.now
    )

    completed_at: datetime | None = None

    iterations: int = 0

    success: bool | None = None

    root: Path = field(init=False)

    def __post_init__(self) -> None:

        self.root = (
            config.LOGS
            / "runs"
            / self.run_id
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.save_metadata()

    @property
    def artifacts(self) -> Path:

        path = self.root / "artifacts"
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def save_metadata(self) -> None:

        payload = {
            "run_id": self.run_id,
            "agent": self.agent,
            "objective": self.objective,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
            "iterations": self.iterations,
            "success": self.success,
        }

        (
            self.root
            / "run.json"
        ).write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

    def next_iteration(self) -> int:

        self.iterations += 1
        self.save_metadata()

        return self.iterations

    def save_prompt(
        self,
        iteration: int,
        prompt: str,
    ) -> None:

        (
            self.artifacts
            / f"prompt_{iteration:03d}.txt"
        ).write_text(
            prompt,
            encoding="utf-8",
        )

    def save_response(
        self,
        iteration: int,
        response: str,
    ) -> None:

        (
            self.artifacts
            / f"response_{iteration:03d}.txt"
        ).write_text(
            response,
            encoding="utf-8",
        )

    def save_script(
        self,
        iteration: int,
        extension: str,
        code: str,
    ) -> None:

        (
            self.artifacts
            / f"script_{iteration:03d}.{extension}"
        ).write_text(
            code,
            encoding="utf-8",
        )

    def save_execution(
        self,
        iteration: int,
        result: dict,
    ) -> None:

        (
            self.artifacts
            / f"execution_{iteration:03d}.json"
        ).write_text(
            json.dumps(
                result,
                indent=2,
            ),
            encoding="utf-8",
        )

    def finish(
        self,
        success: bool,
    ) -> None:

        self.success = success
        self.completed_at = datetime.now()

        self.save_metadata()