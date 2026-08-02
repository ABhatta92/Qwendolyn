import subprocess
import sys
import tempfile
from pathlib import Path

from qwendolyn.tools.base import BaseTool


class PythonTool(BaseTool):
    """
    Executes Python code in an isolated Python process.

    The tool is unaware of the overall workspace layout. It simply executes
    code in the configured working directory.
    """

    def __init__(self, working_directory: str | Path):
        super().__init__(
            name="python",
            description="Execute Python code in an isolated interpreter.",
        )

        self.working_directory = Path(working_directory).resolve()
        self.working_directory.mkdir(parents=True, exist_ok=True)

    def execute(self, code: str) -> dict:

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            dir=self.working_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as f:

            f.write(code)
            script = Path(f.name)

        try:

            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300,          # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:

            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "Execution timed out after 300 seconds.",
            }

        finally:

            script.unlink(missing_ok=True)

    def run(self, code: str, **kwargs):

        return self.execute(code)