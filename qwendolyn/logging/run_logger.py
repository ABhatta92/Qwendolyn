from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qwendolyn.logging.database import DB_PATH, initialize_database


class RunLogger:

    def __init__(
        self,
        agent: str,
        objective: str,
        db_path: str | Path = DB_PATH,
    ):

        self.run_id = str(
            uuid.uuid4()
        )

        self.agent = agent
        self.objective = objective
        self.db_path = Path(db_path)

        initialize_database(
            self.db_path
        )

        self._create_run()

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def _connect(self):
        return sqlite3.connect(
            self.db_path
        )

    # -------------------------------------------------------------------------
    # Timestamp
    # -------------------------------------------------------------------------

    @staticmethod
    def _timestamp() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()

    # -------------------------------------------------------------------------
    # Run
    # -------------------------------------------------------------------------

    def _create_run(self) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO runs (
                    id,
                    agent,
                    objective,
                    started_at,
                    finished_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.run_id,
                    self.agent,
                    self.objective,
                    self._timestamp(),
                    None,
                    "RUNNING",
                ),
            )

            connection.commit()

    def complete(self) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                UPDATE runs
                SET
                    finished_at = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    self._timestamp(),
                    "SUCCESS",
                    self.run_id,
                ),
            )

            connection.commit()

    def fail(
        self,
        message: str,
    ) -> None:

        self.event(
            event_type="RUN_FAILED",
            status="FAILED",
            message=message,
        )

        with self._connect() as connection:

            connection.execute(
                """
                UPDATE runs
                SET
                    finished_at = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    self._timestamp(),
                    "FAILED",
                    self.run_id,
                ),
            )

            connection.commit()

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def event(
        self,
        event_type: str,
        *,
        step: int | None = None,
        attempt: int | None = None,
        status: str | None = None,
        duration: float | None = None,
        message: str | None = None,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO events (
                    run_id,
                    timestamp,
                    step,
                    attempt,
                    event_type,
                    status,
                    duration,
                    message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.run_id,
                    self._timestamp(),
                    step,
                    attempt,
                    event_type,
                    status,
                    duration,
                    message,
                ),
            )

            connection.commit()

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    def plan_created(
        self,
        message: str,
    ) -> None:

        self.event(
            event_type="PLAN_CREATED",
            status="SUCCESS",
            message=message,
        )

    def step_started(
        self,
        step: int,
        description: str,
    ) -> None:

        self.event(
            event_type="STEP_STARTED",
            step=step,
            status="RUNNING",
            message=description,
        )

    def step_completed(
        self,
        step: int,
        description: str,
        *,
        duration: float | None = None,
    ) -> None:

        self.event(
            event_type="STEP_COMPLETED",
            step=step,
            status="SUCCESS",
            duration=duration,
            message=description,
        )

    def step_failed(
        self,
        step: int,
        message: str,
    ) -> None:

        self.event(
            event_type="STEP_FAILED",
            step=step,
            status="FAILED",
            message=message,
        )

    def llm_call(
        self,
        step: int | None = None,
        *,
        attempt: int | None = None,
        duration: float | None = None,
        success: bool = True,
        message: str | None = None,
    ) -> None:

        self.event(
            event_type="LLM_CALL",
            step=step,
            attempt=attempt,
            status=(
                "SUCCESS"
                if success
                else "FAILED"
            ),
            duration=duration,
            message=message,
        )

    def execution(
        self,
        step: int | None = None,
        *,
        attempt: int | None = None,
        duration: float | None = None,
        success: bool,
        message: str | None = None,
    ) -> None:

        self.event(
            event_type="PYTHON_EXECUTION",
            step=step,
            attempt=attempt,
            status=(
                "SUCCESS"
                if success
                else "FAILED"
            ),
            duration=duration,
            message=message,
        )

    def validation(
        self,
        step: int | None = None,
        *,
        success: bool,
        message: str | None = None,
    ) -> None:

        self.event(
            event_type="VALIDATION",
            step=step,
            status=(
                "SUCCESS"
                if success
                else "FAILED"
            ),
            message=message,
        )