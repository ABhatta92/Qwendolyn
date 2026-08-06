from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from qwendolyn import config


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

        self.timeout = timeout
        self.port = port

    def execute(
        self,
        files: dict[str, str],
    ) -> dict:

        before = {
            path.relative_to(self.working_directory)
            for path in self.working_directory.rglob("*")
        }

        written_files: list[str] = []

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

            written_files.append(
                str(
                    destination.relative_to(
                        self.working_directory
                    )
                )
            )

        start = time.perf_counter()

        npm = shutil.which("npm")

        if npm is None:

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

                install = subprocess.run(
                    [npm, "install"],
                    cwd=self.project_directory,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                if install.returncode != 0:

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

            return {
                "success": process.poll() is None,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.poll(),
                "execution_time": time.perf_counter() - start,
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
        )

        return {
            "success": True,
            "stdout": "",
            "stderr": "",
            "return_code": 0,
            "execution_time": time.perf_counter() - start,
            "created_files": created,
            "url": None,
        }