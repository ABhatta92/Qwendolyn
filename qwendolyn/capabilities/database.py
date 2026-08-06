"""DuckDB metadata and SQL capability."""

from __future__ import annotations

import re
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import duckdb

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability, CapabilityError, CapabilityResult, empty_artifacts


class DatabaseCapability(BaseCapability):
    def __init__(self, database: str | Path | None = None) -> None:
        super().__init__("database", "Manage DuckDB SQL, metadata, views, and Parquet import/export.")
        self.database = Path(database or config.DB / "qwendolyn.duckdb").resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)

    @property
    def functions(self) -> list[dict[str, Any]]:
        return [
            self._schema("execute_sql", "Execute SQL and return rows for statements with result sets.", {"sql": {"type": "string"}}, ["sql"]),
            self._schema("list_tables", "List database tables."),
            self._schema("describe_table", "Return a table schema.", {"table": {"type": "string"}}, ["table"]),
            self._schema("drop_table", "Drop a table if it exists.", {"table": {"type": "string"}}, ["table"]),
            self._schema("create_view", "Create or replace a view from a SELECT query.", {"view": {"type": "string"}, "query": {"type": "string"}}, ["view", "query"]),
            self._schema("list_views", "List database views."),
            self._schema("import_parquet", "Import a Parquet file into a table.", {"path": {"type": "string"}, "table": {"type": "string"}}, ["path", "table"]),
            self._schema("export_parquet", "Export a table or query to Parquet.", {"source": {"type": "string"}, "path": {"type": "string"}}, ["source", "path"]),
        ]

    @staticmethod
    def _schema(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"type": "object", "properties": properties or {}}
        if required:
            params["required"] = required
        return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}

    @staticmethod
    def _identifier(value: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("Database identifiers must contain only letters, digits, and underscores.")
        return value

    @staticmethod
    def _literal_path(value: str) -> str:
        return value.replace("'", "''")

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.database))

    def _ok(self, message: str, *, data: Any = None, tables: list[str] | None = None, views: list[str] | None = None, files: list[str] | None = None, metrics: dict[str, Any] | None = None) -> CapabilityResult:
        artifacts = empty_artifacts()
        artifacts.update(files=files or [], tables=tables or [], views=views or [])
        return CapabilityResult(True, message, data=data, artifacts=artifacts, metrics=metrics or {})

    def execute_sql(self, sql: str) -> CapabilityResult:
        with self._connect() as connection:
            cursor = connection.execute(sql)
            if cursor.description is None:
                return self._ok("SQL executed successfully.")
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return self._ok("SQL query executed successfully.", data=rows, metrics={"rows": len(rows)})

    def list_tables(self) -> CapabilityResult:
        result = self.execute_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_type = 'BASE TABLE' ORDER BY table_name")
        tables = [row["table_name"] for row in result.data or []]
        result.artifacts["tables"] = tables
        return result

    def describe_table(self, table: str) -> CapabilityResult:
        table = self._identifier(table)
        result = self.execute_sql(f"DESCRIBE {table}")
        result.artifacts["tables"] = [table]
        return result

    def drop_table(self, table: str) -> CapabilityResult:
        table = self._identifier(table)
        self.execute_sql(f"DROP TABLE IF EXISTS {table}")
        return self._ok(f"Dropped table '{table}'.", tables=[table])

    def create_view(self, view: str, query: str) -> CapabilityResult:
        view = self._identifier(view)
        self.execute_sql(f"CREATE OR REPLACE VIEW {view} AS {query}")
        return self._ok(f"Created view '{view}'.", views=[view])

    def list_views(self) -> CapabilityResult:
        result = self.execute_sql("SELECT table_name FROM information_schema.views WHERE table_schema = 'main' ORDER BY table_name")
        result.artifacts["views"] = [row["table_name"] for row in result.data or []]
        return result

    def import_parquet(self, path: str, table: str) -> CapabilityResult:
        table = self._identifier(table)
        self.execute_sql(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_parquet('{self._literal_path(path)}')")
        count = self.execute_sql(f"SELECT count(*) AS row_count FROM {table}")
        return self._ok(f"Imported '{path}' into '{table}'.", tables=[table], metrics={"rows": count.data[0]["row_count"]})

    def export_parquet(self, source: str, path: str) -> CapabilityResult:
        self.execute_sql(f"COPY ({source}) TO '{self._literal_path(path)}' (FORMAT PARQUET)")
        return self._ok(f"Exported Parquet to '{path}'.", files=[path])

    def execute(self, function_name: str, **kwargs: Any) -> CapabilityResult:
        operations: dict[str, Callable[..., CapabilityResult]] = {name: getattr(self, name) for name in ("execute_sql", "list_tables", "describe_table", "drop_table", "create_view", "list_views", "import_parquet", "export_parquet")}
        start = time.perf_counter()
        try:
            result = operations[function_name](**kwargs)
        except Exception as exc:
            result = CapabilityResult(False, f"Database operation '{function_name}' failed.", error=CapabilityError(type(exc).__name__, str(exc), traceback.format_exc()))
        result.metrics.setdefault("execution_time_seconds", round(time.perf_counter() - start, 3))
        return result
