from pathlib import Path
from typing import Any

import duckdb

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability, CapabilityResult
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class DatabaseCapability(BaseCapability):

    def __init__(
        self,
        database: str | Path | None = None,
    ):

        super().__init__(
            name="database",
            description="Execute SQL and manage Parquet data using DuckDB.",
        )

        self.database = Path(
            database or config.DB / "qwendolyn.duckdb"
        ).resolve()

        self.database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Initialized Database capability for %s",
            self.database,
        )

    @property
    def functions(self) -> list[dict]:

        return [
            {
                "type": "function",
                "function": {
                    "name": "run_sql",
                    "description": "Execute arbitrary SQL against the DuckDB database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL statement to execute."
                            }
                        },
                        "required": ["sql"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tables",
                    "description": "List every table in the database.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_views",
                    "description": "List every view in the database.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "describe_table",
                    "description": "Describe the schema of a table.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string"
                            }
                        },
                        "required": ["table"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "table_exists",
                    "description": "Check whether a table exists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string"
                            }
                        },
                        "required": ["table"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "drop_table",
                    "description": "Drop a table if it exists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string"
                            }
                        },
                        "required": ["table"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_parquet",
                    "description": "Load a Parquet file into a DuckDB table.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string"
                            },
                            "table_name": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "path",
                            "table_name",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "append_parquet",
                    "description": "Append a Parquet file to an existing DuckDB table.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string"
                            },
                            "table_name": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "path",
                            "table_name",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_parquet",
                    "description": "Export a DuckDB table to a Parquet file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string"
                            },
                            "path": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "table_name",
                            "path",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "query_parquet",
                    "description": "Execute SQL directly against a Parquet file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string"
                            },
                            "sql": {
                                "type": "string",
                                "description": "SQL using '{parquet}' as the table placeholder."
                            }
                        },
                        "required": [
                            "path",
                            "sql",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_view",
                    "description": "Create or replace a SQL view.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "view_name": {
                                "type": "string"
                            },
                            "sql": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "view_name",
                            "sql",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "vacuum",
                    "description": "Run VACUUM.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "checkpoint",
                    "description": "Checkpoint the database.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]

    def _connect(self):

        return duckdb.connect(str(self.database))

    def _success(
        self,
        message: str,
        *,
        data: Any = None,
        tables: list[str] | None = None,
        views: list[str] | None = None,
        files: list[str] | None = None,
        metrics: dict | None = None,
    ) -> CapabilityResult:

        return CapabilityResult(
            success=True,
            message=message,
            data=data,
            artifacts={
                "files": files or [],
                "tables": tables or [],
                "views": views or [],
                "vectors": [],
            },
            metrics=metrics or {},
        )

    def run_sql(
        self,
        sql: str,
    ) -> CapabilityResult:

        logger.info("Executing SQL")

        with self._connect() as conn:

            result = conn.execute(sql)

            try:

                df = result.fetchdf()

                return self._success(
                    "SQL executed successfully.",
                    data=df.to_dict("records"),
                    metrics={
                        "rows": len(df),
                    },
                )

            except Exception:

                return self._success(
                    "SQL executed successfully."
                )

    def list_tables(self):

        return self.run_sql("SHOW TABLES")

    def list_views(self):

        return self.run_sql(
            """
            SELECT table_name
            FROM information_schema.views
            """
        )

    def describe_table(
        self,
        table: str,
    ):

        return self.run_sql(
            f"DESCRIBE {table}"
        )

    def table_exists(
        self,
        table: str,
    ):

        result = self.run_sql(
            f"""
            SELECT COUNT(*) AS cnt
            FROM information_schema.tables
            WHERE table_name='{table}'
            """
        )

        exists = bool(
            result.data[0]["cnt"]
        )

        return self._success(
            f"Table '{table}' {'exists' if exists else 'does not exist'}.",
            data=exists,
        )

    def drop_table(
        self,
        table: str,
    ):

        self.run_sql(
            f"DROP TABLE IF EXISTS {table}"
        )

        return self._success(
            f"Dropped table '{table}'."
        )

    def read_parquet(
        self,
        path: str,
        table_name: str,
    ):

        self.run_sql(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *
            FROM read_parquet('{path}')
            """
        )

        return self._success(
            f"Loaded '{path}' into table '{table_name}'.",
            tables=[table_name],
        )

    def append_parquet(
        self,
        path: str,
        table_name: str,
    ):

        self.run_sql(
            f"""
            INSERT INTO {table_name}
            SELECT *
            FROM read_parquet('{path}')
            """
        )

        return self._success(
            f"Appended '{path}' to '{table_name}'.",
            tables=[table_name],
        )

    def write_parquet(
        self,
        table_name: str,
        path: str,
    ):

        self.run_sql(
            f"""
            COPY {table_name}
            TO '{path}'
            (FORMAT PARQUET)
            """
        )

        return self._success(
            f"Exported '{table_name}' to '{path}'.",
            files=[path],
        )

    def query_parquet(
        self,
        path: str,
        sql: str,
    ):

        sql = sql.replace(
            "{parquet}",
            f"read_parquet('{path}')",
        )

        return self.run_sql(sql)

    def create_view(
        self,
        view_name: str,
        sql: str,
    ):

        self.run_sql(
            f"""
            CREATE OR REPLACE VIEW {view_name} AS
            {sql}
            """
        )

        return self._success(
            f"Created view '{view_name}'.",
            views=[view_name],
        )

    def vacuum(self):

        self.run_sql("VACUUM")

        return self._success(
            "VACUUM completed."
        )

    def checkpoint(self):

        self.run_sql("CHECKPOINT")

        return self._success(
            "Checkpoint completed."
        )

    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> CapabilityResult:

        functions = {
            "run_sql": self.run_sql,
            "list_tables": self.list_tables,
            "list_views": self.list_views,
            "describe_table": self.describe_table,
            "table_exists": self.table_exists,
            "drop_table": self.drop_table,
            "read_parquet": self.read_parquet,
            "append_parquet": self.append_parquet,
            "write_parquet": self.write_parquet,
            "query_parquet": self.query_parquet,
            "create_view": self.create_view,
            "vacuum": self.vacuum,
            "checkpoint": self.checkpoint,
        }

        if function_name not in functions:
            raise ValueError(
                f"Unknown database function '{function_name}'."
            )

        return functions[function_name](**kwargs)