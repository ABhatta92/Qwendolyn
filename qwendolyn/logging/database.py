from __future__ import annotations

import sqlite3
from pathlib import Path

from qwendolyn import config


DB_PATH = config.LOGS / "runs.db"


def initialize_database(
    db_path: str | Path = DB_PATH,
) -> Path:

    db_path = Path(db_path)

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(db_path) as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                objective TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                step INTEGER,
                attempt INTEGER,
                event_type TEXT NOT NULL,
                status TEXT,
                duration REAL,
                message TEXT,
                stdout TEXT,
                stderr TEXT,

                FOREIGN KEY (
                    run_id
                )
                REFERENCES runs(id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_run_id
            ON events(run_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON events(timestamp)
            """
        )

        connection.commit()

    return db_path


if __name__ == "__main__":

    path = initialize_database()

    print(
        f"Initialized SQLite database: {path}"
    )