from pathlib import Path
from typing import Any

from qwendolyn import config
from qwendolyn.capabilities.base import BaseCapability
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="app")


class FileSystemCapability(BaseCapability):

    def __init__(self, workspace: str | Path | None = None):
        super().__init__(
            name="filesystem",
            description="Read, write and manage files inside the workspace.",
        )

        self.workspace = Path(workspace or config.WORKSPACE).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initialized filesystem capability for %s",
            self.workspace,
        )

    @property
    def functions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a UTF-8 text file from the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path inside the workspace.",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Create or overwrite a UTF-8 text file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path inside the workspace.",
                            },
                            "content": {
                                "type": "string",
                                "description": "File contents.",
                            },
                        },
                        "required": [
                            "path",
                            "content",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Delete a file from the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path inside the workspace.",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_exists",
                    "description": "Check whether a file exists in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path inside the workspace.",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
        ]

    def _resolve(self, path: str) -> Path:

        target = (self.workspace / path).resolve()

        if self.workspace not in target.parents and target != self.workspace:
            raise ValueError("Cannot access files outside the workspace.")

        return target

    def list_files(self) -> list[str]:

        logger.info("Listing files")

        return [
            str(file.relative_to(self.workspace))
            for file in self.workspace.rglob("*")
            if file.is_file()
        ]

    def read_file(self, path: str) -> str:

        file = self._resolve(path)

        logger.info("Reading %s", file)

        return file.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> dict:

        file = self._resolve(path)

        logger.info("Writing %s", file)

        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": path,
        }

    def delete_file(self, path: str) -> dict:

        file = self._resolve(path)

        logger.info("Deleting %s", file)

        file.unlink(missing_ok=True)

        return {
            "success": True,
            "path": path,
        }

    def file_exists(self, path: str) -> bool:

        return self._resolve(path).exists()

    def execute(
        self,
        function_name: str,
        **kwargs: Any,
    ) -> Any:

        functions = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "delete_file": self.delete_file,
            "file_exists": self.file_exists,
        }

        if function_name not in functions:
            raise ValueError(f"Unknown filesystem function '{function_name}'.")

        return functions[function_name](**kwargs)