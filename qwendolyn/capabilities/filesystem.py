"""Workspace-only file management capability."""

from __future__ import annotations

import shutil
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability, CapabilityError, CapabilityResult, empty_artifacts
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


class FileSystemCapability(BaseCapability):
    """Owns paths and text files, without interpreting their contents."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        super().__init__("filesystem", "Manage files and directories inside the workspace.")
        self.workspace = Path(workspace or config.WORKSPACE).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        logger.info("Filesystem capability initialized (workspace=%s).", self.workspace)

    @property
    def functions(self) -> list[dict[str, Any]]:
        return [
            self._schema("list_files", "List workspace files using an optional glob pattern.", {"pattern": {"type": "string", "default": "*"}}),
            self._schema("read_text", "Read a UTF-8 text file.", {"path": {"type": "string"}}, ["path"]),
            self._schema("write_text", "Create or overwrite a UTF-8 text file.", {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
            self._schema("delete", "Delete a file or empty directory.", {"path": {"type": "string"}}, ["path"]),
            self._schema("move", "Move a file or directory.", {"source": {"type": "string"}, "destination": {"type": "string"}}, ["source", "destination"]),
            self._schema("copy", "Copy a file or directory.", {"source": {"type": "string"}, "destination": {"type": "string"}}, ["source", "destination"]),
            self._schema("create_directory", "Create a directory.", {"path": {"type": "string"}}, ["path"]),
            self._schema("exists", "Check whether a workspace path exists.", {"path": {"type": "string"}}, ["path"]),
        ]

    @staticmethod
    def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
        parameters: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            parameters["required"] = required
        return {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}

    def _path(self, value: str) -> Path:
        path = (self.workspace / value).resolve()
        if path != self.workspace and self.workspace not in path.parents:
            raise ValueError("Path must stay inside the workspace.")
        return path

    def _ok(self, message: str, *, data: Any = None, files: list[str] | None = None) -> CapabilityResult:
        artifacts = empty_artifacts()
        artifacts["files"] = files or []
        return CapabilityResult(True, message, data=data, artifacts=artifacts)

    def list_files(self, pattern: str = "*") -> CapabilityResult:
        files = sorted(str(path.relative_to(self.workspace)) for path in self.workspace.glob(pattern) if path.is_file())
        return self._ok(f"Found {len(files)} file(s).", data=files, files=files)

    def read_text(self, path: str) -> CapabilityResult:
        return self._ok(f"Read '{path}'.", data=self._path(path).read_text(encoding="utf-8"), files=[path])

    def write_text(self, path: str, content: str) -> CapabilityResult:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return self._ok(f"Wrote '{path}'.", files=[path], data={"bytes": len(content.encode('utf-8'))})

    def delete(self, path: str) -> CapabilityResult:
        target = self._path(path)
        if target.is_dir():
            target.rmdir()
        else:
            target.unlink(missing_ok=True)
        return self._ok(f"Deleted '{path}'.", files=[path])

    def move(self, source: str, destination: str) -> CapabilityResult:
        target = self._path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self._path(source)), str(target))
        return self._ok(f"Moved '{source}' to '{destination}'.", files=[destination])

    def copy(self, source: str, destination: str) -> CapabilityResult:
        source_path, target = self._path(source), self._path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir():
            shutil.copytree(source_path, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, target)
        return self._ok(f"Copied '{source}' to '{destination}'.", files=[destination])

    def create_directory(self, path: str) -> CapabilityResult:
        self._path(path).mkdir(parents=True, exist_ok=True)
        return self._ok(f"Created directory '{path}'.")

    def exists(self, path: str) -> CapabilityResult:
        present = self._path(path).exists()
        return self._ok(f"Path '{path}' {'exists' if present else 'does not exist'}.", data=present)

    def execute(self, function_name: str, **kwargs: Any) -> CapabilityResult:
        operations: dict[str, Callable[..., CapabilityResult]] = {name: getattr(self, name) for name in ("list_files", "read_text", "write_text", "delete", "move", "copy", "create_directory", "exists")}
        start = time.perf_counter()
        logger.info("Filesystem operation started: %s (argument_keys=%s).", function_name, sorted(kwargs))
        try:
            result = operations[function_name](**kwargs)
        except Exception as exc:
            logger.exception("Filesystem operation failed: %s", function_name)
            result = CapabilityResult(False, f"Filesystem operation '{function_name}' failed.", error=CapabilityError(type(exc).__name__, str(exc), traceback.format_exc()))
        result.metrics.setdefault("execution_time_seconds", round(time.perf_counter() - start, 3))
        log_method = logger.info if result.success else logger.warning
        log_method("Filesystem operation finished: %s (success=%s, duration=%ss).", function_name, result.success, result.metrics["execution_time_seconds"])
        return result
