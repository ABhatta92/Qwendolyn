from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from qwendolyn import config
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="runner")


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

        self.temp_directory = config.TEMP.resolve()

        self.temp_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.timeout = timeout

        logger.info(
            "Initialized PythonRunner (workspace=%s, temp=%s)",
            self.working_directory,
            self.temp_directory,
        )

    def execute(
        self,
        code: str,
    ) -> dict:

        logger.info("=" * 80)
        logger.info("PYTHON EXECUTION")
        logger.info("=" * 80)

        start = time.perf_counter()

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            prefix="run_",
            dir=self.temp_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as file:

            file.write(code)
            script = Path(file.name)

        logger.info("Temporary script: %s", script)

        before = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        try:

            logger.info("Executing Python...")

            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

        except subprocess.TimeoutExpired:

            logger.exception("Python execution timed out.")

            after = {
                path.relative_to(self.working_directory)
                for path in self.working_directory.rglob("*")
            }

            created = sorted(
                str(path)
                for path in (after - before)
                if not str(path).startswith("temp/")
            )

            script.unlink(missing_ok=True)

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
                "created_files": created,
            }

        finally:

            script.unlink(
                missing_ok=True,
            )

        after = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        created = sorted(
            str(path)
            for path in (after - before)
            if not str(path).startswith("temp/")
        )

        execution_time = time.perf_counter() - start

        logger.info("Return Code : %s", result.returncode)
        logger.info("Success     : %s", result.returncode == 0)
        logger.info("Time        : %.2f sec", execution_time)

        if created:

            logger.info("Created Files:")

            for file in created:
                logger.info("  + %s", file)

        else:

            logger.info("Created Files: None")

        if result.stdout.strip():

            logger.info("-" * 80)
            logger.info("STDOUT")
            logger.info("-" * 80)
            logger.info(result.stdout)

        if result.stderr.strip():

            logger.info("-" * 80)
            logger.info("STDERR")
            logger.info("-" * 80)
            logger.info(result.stderr)

        logger.info("=" * 80)

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time,
            "script": str(
                script.relative_to(
                    self.working_directory
                )
            ),
            "created_files": created,
        }