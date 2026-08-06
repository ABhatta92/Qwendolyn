"""Arbitrary Python execution inside Qwendolyn's workspace."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability, CapabilityError, CapabilityResult, empty_artifacts
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


class PythonCapability(BaseCapability):
    def __init__(self, working_directory: str | Path | None = None, timeout_seconds: int = 300) -> None:
        super().__init__("python", "Execute arbitrary Python in the workspace; use it for data engineering work.")
        self.working_directory = Path(working_directory or config.WORKSPACE).resolve()
        self.working_directory.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        logger.info("Python capability initialized (workspace=%s, timeout=%ss).", self.working_directory, timeout_seconds)

    @property
    def functions(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": "execute_python", "description": "Execute Python source in the workspace. Print concise verification evidence to stdout.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}}]

    def _files(self) -> set[str]:
        return {str(path.relative_to(self.working_directory)) for path in self.working_directory.rglob("*") if path.is_file()}

    def execute_python(self, code: str) -> CapabilityResult:
        before = self._files()
        script: Path | None = None
        start = time.perf_counter()
        try:
            logger.info("Starting Python process (source_length=%d).", len(code))
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".py", dir=self.working_directory, delete=False) as handle:
                handle.write(code)
                script = Path(handle.name)
            process = subprocess.run([sys.executable, str(script)], cwd=self.working_directory, capture_output=True, text=True, timeout=self.timeout_seconds)
            created = sorted(self._files() - before - {script.name})
            artifacts = empty_artifacts()
            artifacts["files"] = created
            data = {"stdout": process.stdout, "stderr": process.stderr, "return_code": process.returncode}
            if process.returncode == 0:
                logger.info("Python process exited successfully (created_files=%d).", len(created))
                return CapabilityResult(True, "Python executed successfully.", data=data, artifacts=artifacts, logs=["Python process completed."])
            logger.warning("Python process exited with return code %d.", process.returncode)
            return CapabilityResult(False, "Python execution failed.", data=data, artifacts=artifacts, error=CapabilityError("PythonExecutionError", process.stderr or process.stdout))
        except subprocess.TimeoutExpired as exc:
            logger.warning("Python process timed out after %s seconds.", self.timeout_seconds)
            return CapabilityResult(False, "Python execution timed out.", error=CapabilityError("TimeoutError", f"Execution exceeded {self.timeout_seconds} seconds.", traceback.format_exc()), data={"stdout": exc.stdout, "stderr": exc.stderr})
        except Exception as exc:
            logger.exception("Python execution failed")
            return CapabilityResult(False, "Python execution failed.", error=CapabilityError(type(exc).__name__, str(exc), traceback.format_exc()))
        finally:
            if script:
                script.unlink(missing_ok=True)
            # Metrics are attached in execute to cover every path.

    def execute(self, function_name: str, **kwargs: Any) -> CapabilityResult:
        start = time.perf_counter()
        if function_name != "execute_python":
            result = CapabilityResult(False, "Unknown Python operation.", error=CapabilityError("ValueError", f"Unknown Python operation '{function_name}'."))
        else:
            result = self.execute_python(**kwargs)
        result.metrics.setdefault("execution_time_seconds", round(time.perf_counter() - start, 3))
        logger.info("Python operation finished: %s (success=%s, duration=%ss).", function_name, result.success, result.metrics["execution_time_seconds"])
        return result
