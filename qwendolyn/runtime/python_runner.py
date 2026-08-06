from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path


class PythonRunner:

    def __init__(
        self,
        working_directory: str | Path,
        timeout: int = 300,
    ):

        self.working_directory = Path(
            working_directory
        ).resolve()

        self.working_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.scripts_directory = (
            self.working_directory / "scripts"
        )

        self.scripts_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.timeout = timeout

    def execute(
        self,
        code: str,
    ) -> dict:

        start = time.perf_counter()

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            dir=self.scripts_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as file:

            file.write(code)
            script = Path(file.name)

        before = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        try:

            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

        except subprocess.TimeoutExpired:

            after = {
                path.relative_to(self.working_directory)
                for path in self.working_directory.rglob("*")
            }

            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds.",
                "execution_time": time.perf_counter() - start,
                "script": str(
                    script.relative_to(
                        self.working_directory
                    )
                ),
                "created_files": sorted(
                    str(path)
                    for path in (after - before)
                ),
            }

        after = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        created = sorted(
            str(path)
            for path in (after - before)
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": time.perf_counter() - start,
            "script": str(
                script.relative_to(
                    self.working_directory
                )
            ),
            "created_files": created,
        }