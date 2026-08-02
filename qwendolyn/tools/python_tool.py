import contextlib
import io
import subprocess
import sys
from pathlib import Path


class PythonTool:
    """
    Executes Python code inside the Qwendolyn workspace.
    """

    def __init__(self, workspace: str = "workspace"):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(exist_ok=True)

    def execute(self, code: str) -> dict:
        """
        Executes Python code.

        Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str
        }
        """

        script = self.workspace / "_temp_script.py"
        script.write_text(code, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=self.workspace,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }