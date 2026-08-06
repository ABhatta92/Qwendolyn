from __future__ import annotations

from pathlib import Path

from qwendolyn.capabilities.database import DatabaseCapability
from qwendolyn.capabilities.filesystem import FileSystemCapability
from qwendolyn.capabilities.python_tool import PythonCapability
from qwendolyn.capabilities.registry import CapabilityRegistry


def test_filesystem_operations_return_standard_result(tmp_path: Path) -> None:
    capability = FileSystemCapability(tmp_path)
    written = capability.execute("write_text", path="notes/hello.txt", content="hello")
    read = capability.execute("read_text", path="notes/hello.txt")
    copied = capability.execute("copy", source="notes/hello.txt", destination="copy.txt")

    assert written.success and read.success and copied.success
    assert read.data == "hello"
    assert set(written.to_dict()) == {"success", "message", "data", "artifacts", "metrics", "logs", "error"}


def test_python_reports_created_artifacts(tmp_path: Path) -> None:
    result = PythonCapability(tmp_path).execute("execute_python", code="from pathlib import Path\nPath('output.txt').write_text('ok')\nprint('verified')")

    assert result.success
    assert result.data["stdout"].strip() == "verified"
    assert result.artifacts["files"] == ["output.txt"]


def test_database_exposes_metadata_and_parquet(tmp_path: Path) -> None:
    database = DatabaseCapability(tmp_path / "agent.duckdb")
    assert database.execute("execute_sql", sql="CREATE TABLE events AS SELECT 1 AS id").success
    tables = database.execute("list_tables")
    schema = database.execute("describe_table", table="events")
    exported = database.execute("export_parquet", source="SELECT * FROM events", path=str(tmp_path / "events.parquet"))

    assert tables.success and tables.artifacts["tables"] == ["events"]
    assert schema.success and schema.metrics["rows"] == 1
    assert exported.success and (tmp_path / "events.parquet").exists()


def test_registry_converts_unknown_operation_to_result() -> None:
    registry = CapabilityRegistry()
    result = registry.execute("missing")
    assert not result.success
    assert result.error is not None
