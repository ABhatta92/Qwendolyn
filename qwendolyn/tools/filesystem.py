from pathlib import Path


class FileSystemTool:
    """
    Provides safe access to a predefined workspace.

    All paths are resolved relative to the workspace directory.
    """

    def __init__(self, workspace: str = "workspace"):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        """
        Resolve a relative path inside the workspace.

        Raises:
            ValueError if the path escapes the workspace.
        """

        target = (self.workspace / path).resolve()

        if self.workspace not in target.parents and target != self.workspace:
            raise ValueError("Access outside workspace is not allowed.")

        return target

    def list_files(self, recursive: bool = True) -> list[str]:
        """
        Returns all files in the workspace.
        """

        pattern = "**/*" if recursive else "*"

        return [
            str(file.relative_to(self.workspace))
            for file in self.workspace.glob(pattern)
            if file.is_file()
        ]

    def read_file(self, path: str) -> str:
        """
        Reads a text file.
        """

        file = self._resolve(path)

        if not file.exists():
            raise FileNotFoundError(path)

        return file.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str):
        """
        Creates or overwrites a file.
        """

        file = self._resolve(path)

        file.parent.mkdir(parents=True, exist_ok=True)

        file.write_text(content, encoding="utf-8")

    def append_file(self, path: str, content: str):
        """
        Appends text to a file.
        """

        file = self._resolve(path)

        file.parent.mkdir(parents=True, exist_ok=True)

        with open(file, "a", encoding="utf-8") as f:
            f.write(content)

    def delete_file(self, path: str):
        """
        Deletes a file.
        """

        file = self._resolve(path)

        if file.exists():
            file.unlink()

    def exists(self, path: str) -> bool:
        """
        Returns True if the file exists.
        """

        return self._resolve(path).exists()

    def make_directory(self, path: str):
        """
        Creates a directory.
        """

        self._resolve(path).mkdir(parents=True, exist_ok=True)