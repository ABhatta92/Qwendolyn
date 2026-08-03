import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability, CapabilityResult
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class PythonCapability(BaseCapability):
    """
    Executes Python code inside an isolated interpreter with the
    workspace as the current working directory.
    """

    def __init__(
        self,
        working_directory: str | Path | None = None,
    ):
        super().__init__(
            name="python",
            description="Execute Python code in an isolated interpreter.",
        )

        self.working_directory = Path(
            working_directory or config.WORKSPACE
        ).resolve()

        self.working_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Initialized Python capability for %s",
            self.working_directory,
        )

    @property
    def functions(self) -> list[dict]:

        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": (
                        "Execute Python code. "
                        "The current working directory is the workspace."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python source code."
                            }
                        },
                        "required": [
                            "code"
                        ],
                    },
                },
            }
        ]

    def _scan_workspace(self) -> set[str]:

        return {
            str(
                file.relative_to(
                    self.working_directory
                )
            )
            for file in self.working_directory.rglob("*")
            if file.is_file()
        }

    def execute_python(
        self,
        code: str,
    ) -> CapabilityResult:

        before = self._scan_workspace()

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            dir=self.working_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as file:

            file.write(code)
            script = Path(file.name)

        start = time.perf_counter()

        try:

            logger.info(
                "Executing Python snippet in %s",
                self.working_directory,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                ],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = round(
                time.perf_counter() - start,
                3,
            )

            after = self._scan_workspace()

            created_files = sorted(
                list(after - before)
            )

            if result.returncode == 0:

                return CapabilityResult(
                    success=True,
                    message="Python executed successfully.",
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode,
                    },
                    artifacts={
                        "files": created_files,
                        "tables": [],
                        "views": [],
                        "vectors": [],
                    },
                    metrics={
                        "execution_time_seconds": duration,
                    },
                    logs=[
                        "Python execution completed."
                    ],
                )

            return CapabilityResult(
                success=False,
                message="Python execution failed.",
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                },
                artifacts={
                    "files": created_files,
                    "tables": [],
                    "views": [],
                    "vectors": [],
                },
                metrics={
                    "execution_time_seconds": duration,
                },
                error={
                    "type": "PythonExecutionError",
                    "message": result.stderr,
                },
            )

        except subprocess.TimeoutExpired:

            duration = round(
                time.perf_counter() - start,
                3,
            )

            logger.exception(
                "Python execution timed out."
            )

            return CapabilityResult(
                success=False,
                message="Python execution timed out.",
                metrics={
                    "execution_time_seconds": duration,
                },
                error={
                    "type": "TimeoutError",
                    "message": "Execution timed out after 300 seconds.",
                },
            )

        except Exception as ex:

            duration = round(
                time.perf_counter() - start,
                3,
            )

            logger.exception(
                "Python execution failed."
            )

            return CapabilityResult(
                success=False,
                message="Python execution failed.",
                metrics={
                    "execution_time_seconds": duration,
                },
                error={
                    "type": type(ex).__name__,
                    "message": str(ex),
                },
            )

        finally:

            script.unlink(
                missing_ok=True,
            )

    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> CapabilityResult:

        functions = {
            "execute_python": self.execute_python,
        }

        if function_name not in functions:
            raise ValueError(
                f"Unknown Python function '{function_name}'."
            )

        return functions[
            function_name
        ](**kwargs)