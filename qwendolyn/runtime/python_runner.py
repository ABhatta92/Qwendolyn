from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from qwendolyn import config
from qwendolyn.logging.logging import get_logger


logger = get_logger(
    __name__,
    log_file="runner",
)


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

        self.temp_directory = (
            config.TEMP.resolve()
        )

        self.temp_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.timeout = timeout

        logger.info(
            "Initialized PythonRunner "
            "(workspace=%s, temp=%s)",
            self.working_directory,
            self.temp_directory,
        )

    # =========================================================================
    # Execute
    # =========================================================================

    def execute(
        self,
        code: str,
    ) -> dict:

        logger.info("=" * 80)
        logger.info("PYTHON EXECUTION")
        logger.info("=" * 80)

        start = time.perf_counter()

        # ---------------------------------------------------------------------
        # Create temporary script
        # ---------------------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            prefix="run_",
            dir=self.temp_directory,
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as file:

            file.write(code)

            script = Path(
                file.name
            )

        logger.info(
            "Temporary script: %s",
            script,
        )

        # ---------------------------------------------------------------------
        # Workspace snapshot
        # ---------------------------------------------------------------------

        before = self._workspace_snapshot()

        try:

            logger.info(
                "Executing Python..."
            )

            process = subprocess.run(
                [
                    sys.executable,
                    str(script),
                ],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

        except subprocess.TimeoutExpired:

            execution_time = (
                time.perf_counter()
                - start
            )

            after = (
                self._workspace_snapshot()
            )

            created = self._created_files(
                before,
                after,
            )

            logger.exception(
                "Python execution timed out."
            )

            result = {
                # Python did NOT successfully execute.
                "success": False,

                # More explicit than a normal return code.
                "execution_success": False,

                "return_code": None,
                "stdout": "",
                "stderr": (
                    f"Execution timed out after "
                    f"{self.timeout} seconds."
                ),
                "execution_time": execution_time,
                "script": self._relative_path(
                    script
                ),
                "created_files": created,
            }

            return result

        finally:

            script.unlink(
                missing_ok=True,
            )

        # ---------------------------------------------------------------------
        # Workspace changes
        # ---------------------------------------------------------------------

        after = self._workspace_snapshot()

        created = self._created_files(
            before,
            after,
        )

        execution_time = (
            time.perf_counter()
            - start
        )

        execution_success = (
            process.returncode == 0
        )

        # ---------------------------------------------------------------------
        # Logging
        # ---------------------------------------------------------------------

        logger.info(
            "Return Code : %s",
            process.returncode,
        )

        logger.info(
            "Execution  : %s",
            execution_success,
        )

        logger.info(
            "Time       : %.2f sec",
            execution_time,
        )

        if created:

            logger.info(
                "Created Files:"
            )

            for file in created:

                logger.info(
                    "  + %s",
                    file,
                )

        else:

            logger.info(
                "Created Files: None"
            )

        if process.stdout.strip():

            logger.info("-" * 80)
            logger.info("STDOUT")
            logger.info("-" * 80)
            logger.info(
                process.stdout
            )

        if process.stderr.strip():

            logger.info("-" * 80)
            logger.info("STDERR")
            logger.info("-" * 80)
            logger.info(
                process.stderr
            )

        logger.info("=" * 80)

        # ---------------------------------------------------------------------
        # Result
        # ---------------------------------------------------------------------

        return {
            # Backwards-compatible field.
            "success": execution_success,

            # Explicit semantic name.
            #
            # IMPORTANT:
            # This means ONLY that Python executed successfully.
            # It does NOT mean that the agent completed the task.
            "execution_success": execution_success,

            "return_code": process.returncode,

            "stdout": process.stdout,

            "stderr": process.stderr,

            "execution_time": execution_time,

            "script": self._relative_path(
                script
            ),

            "created_files": created,
        }

    # =========================================================================
    # Workspace Helpers
    # =========================================================================

    def _workspace_snapshot(
        self,
    ) -> set[Path]:

        return {
            path.relative_to(
                self.working_directory
            )
            for path in self.working_directory.rglob(
                "*"
            )
        }

    def _created_files(
        self,
        before: set[Path],
        after: set[Path],
    ) -> list[str]:

        return sorted(
            str(path)
            for path in (after - before)
            if not str(path).startswith(
                "temp/"
            )
        )

    def _relative_path(
        self,
        path: Path,
    ) -> str:

        try:

            return str(
                path.relative_to(
                    self.working_directory
                )
            )

        except ValueError:

            return str(path)