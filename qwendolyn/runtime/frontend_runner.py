from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from qwendolyn import config
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="runner")


class FrontendRunner:

    def __init__(
        self,
        working_directory: str | Path = config.WORKSPACE,
        timeout: int = 300,
        port: int = 3000,
    ):

        self.working_directory = Path(
            working_directory
        ).resolve()

        self.project_directory = (
            self.working_directory / "web"
        )

        self.project_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.temp_directory = config.TEMP.resolve()

        self.temp_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.timeout = timeout
        self.port = port

        logger.info(
            "Initialized FrontendRunner (workspace=%s, web=%s)",
            self.working_directory,
            self.project_directory,
        )

    def execute(
        self,
        files: dict[str, str],
    ) -> dict:

        logger.info("=" * 80)
        logger.info("FRONTEND EXECUTION")
        logger.info("=" * 80)

        start = time.perf_counter()

        before = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        written_files: list[str] = []

        logger.info(
            "Writing %d frontend file(s).",
            len(files),
        )

        for relative_path, content in files.items():

            destination = (
                self.project_directory / relative_path
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_text(
                content,
                encoding="utf-8",
            )

            relative = str(
                destination.relative_to(
                    self.working_directory
                )
            )

            written_files.append(relative)

            logger.info("  + %s", relative)

        npm = shutil.which("npm")

        if npm is None:

            logger.error("npm not found on PATH.")

            return {
                "success": False,
                "stdout": "",
                "stderr": "npm was not found on PATH.",
                "return_code": None,
                "execution_time": 0.0,
                "created_files": written_files,
                "url": None,
            }

        package_json = (
            self.project_directory / "package.json"
        )

        if package_json.exists():

            node_modules = (
                self.project_directory / "node_modules"
            )

            if not node_modules.exists():

                logger.info("Running npm install...")

                install = subprocess.run(
                    [npm, "install"],
                    cwd=self.project_directory,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                if install.stdout.strip():

                    logger.info("-" * 80)
                    logger.info("NPM STDOUT")
                    logger.info("-" * 80)
                    logger.info(install.stdout)

                if install.stderr.strip():

                    logger.info("-" * 80)
                    logger.info("NPM STDERR")
                    logger.info("-" * 80)
                    logger.info(install.stderr)

                if install.returncode != 0:

                    logger.error(
                        "npm install failed (%d).",
                        install.returncode,
                    )

                    return {
                        "success": False,
                        "stdout": install.stdout,
                        "stderr": install.stderr,
                        "return_code": install.returncode,
                        "execution_time": time.perf_counter() - start,
                        "created_files": written_files,
                        "url": None,
                    }

        server = (
            self.project_directory / "server.js"
        )

        if server.exists():

            logger.info("Starting Node server...")

            process = subprocess.Popen(
                ["node", "server.js"],
                cwd=self.project_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            time.sleep(2)

            stdout = ""

            stderr = ""

            if process.stdout:
                stdout = process.stdout.read()

            if process.stderr:
                stderr = process.stderr.read()

            execution_time = (
                time.perf_counter() - start
            )

            logger.info(
                "PID         : %s",
                process.pid,
            )

            logger.info(
                "Running     : %s",
                process.poll() is None,
            )

            logger.info(
                "Time        : %.2f sec",
                execution_time,
            )

            if stdout.strip():

                logger.info("-" * 80)
                logger.info("STDOUT")
                logger.info("-" * 80)
                logger.info(stdout)

            if stderr.strip():

                logger.info("-" * 80)
                logger.info("STDERR")
                logger.info("-" * 80)
                logger.info(stderr)

            logger.info("=" * 80)

            return {
                "success": process.poll() is None,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.poll(),
                "execution_time": execution_time,
                "created_files": written_files,
                "url": f"http://localhost:{self.port}",
                "pid": process.pid,
            }

        after = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        created = sorted(
            str(path)
            for path in (after - before)
            if not str(path).startswith("temp/")
        )

        execution_time = (
            time.perf_counter() - start
        )

        logger.info("Execution completed.")
        logger.info("Time : %.2f sec", execution_time)

        if created:

            logger.info("Created Files:")

            for file in created:
                logger.info("  + %s", file)

        else:

            logger.info("Created Files: None")

        logger.info("=" * 80)

        return {
            "success": True,
            "stdout": "",
            "stderr": "",
            "return_code": 0,
            "execution_time": execution_time,
            "created_files": created,
            "url": None,
        }