import subprocess
import sys
import tempfile
from pathlib import Path

from qwendolyn.tools.base import BaseTool


class PythonTool(BaseTool):

    def __init__(self, workspace: str = "workspace"):
        super().__init__(
            name="python",
            description="Execute Python code inside the workspace.",
        )

        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def execute(self, code: str):

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            dir=self.workspace,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as f:

            f.write(code)
            script = Path(f.name)

        try:

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

        finally:

            script.unlink(missing_ok=True)

    def run(self, code: str, **kwargs):

        return self.execute(code)