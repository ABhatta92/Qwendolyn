from pathlib import Path

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
        logger.info("Initialized filesystem tool for %s", self.workspace)

    def _resolve(self, path: str) -> Path:

        target = (self.workspace / path).resolve()

        if self.workspace not in target.parents and target != self.workspace:
            raise ValueError("Cannot access files outside workspace.")

        return target

    def list_files(self):

        return [
            str(f.relative_to(self.workspace))
            for f in self.workspace.rglob("*")
            if f.is_file()
        ]

    def read_file(self, path: str):

        return self._resolve(path).read_text(encoding="utf-8")

    def write_file(self, path: str, content: str):

        file = self._resolve(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

    def delete_file(self, path: str):

        self._resolve(path).unlink(missing_ok=True)

    def exists(self, path: str):

        return self._resolve(path).exists()

    def run(self, operation: str, **kwargs):

        operations = {
            "list": self.list_files,
            "read": self.read_file,
            "write": self.write_file,
            "delete": self.delete_file,
            "exists": self.exists,
        }

        if operation not in operations:
            raise ValueError(f"Unknown filesystem operation: {operation}")

        return operations[operation](**kwargs)