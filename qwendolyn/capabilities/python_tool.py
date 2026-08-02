import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class PythonCapability(BaseCapability):
    """
    Executes Python code in an isolated Python interpreter.
    """

    def __init__(self, working_directory: str | Path | None = None):
        super().__init__(
            name="python",
            description="Execute Python code in an isolated Python interpreter.",
        )

        self.working_directory = Path(
            working_directory or config.WORKSPACE
        ).resolve()

        self.working_directory.mkdir(parents=True, exist_ok=True)

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
                        "Execute a Python script in an isolated interpreter. "
                        "The current working directory is the workspace."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python source code to execute.",
                            }
                        },
                        "required": ["code"],
                    },
                },
            }
        ]

    def execute_python(self, code: str) -> dict:

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            dir=self.working_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as file:

            file.write(code)
            script = Path(file.name)

        try:

            logger.info(
                "Executing Python snippet in %s",
                self.working_directory,
            )

            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:

            logger.error(
                "Python execution timed out."
            )

            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "Execution timed out after 300 seconds.",
            }

        finally:

            script.unlink(missing_ok=True)

    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> Any:

        functions = {
            "execute_python": self.execute_python,
        }

        if function_name not in functions:
            raise ValueError(
                f"Unknown Python function '{function_name}'."
            )

        return functions[function_name](**kwargs)