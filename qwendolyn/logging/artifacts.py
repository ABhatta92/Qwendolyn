from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:

    def __init__(
        self,
        root: str | Path,
    ):

        self.root = Path(root)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write_text(
        self,
        name: str,
        content: str,
    ) -> Path:

        path = self.root / name

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            content,
            encoding="utf-8",
        )

        return path

    def write_json(
        self,
        name: str,
        data: Any,
    ) -> Path:

        path = self.root / name

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                data,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        return path

    def write_code(
        self,
        iteration: int,
        extension: str,
        code: str,
    ) -> Path:

        return self.write_text(
            f"script_{iteration:03d}.{extension}",
            code,
        )

    def write_prompt(
        self,
        iteration: int,
        prompt: str,
    ) -> Path:

        return self.write_text(
            f"prompt_{iteration:03d}.txt",
            prompt,
        )

    def write_response(
        self,
        iteration: int,
        response: str,
    ) -> Path:

        return self.write_text(
            f"response_{iteration:03d}.txt",
            response,
        )

    def write_execution(
        self,
        iteration: int,
        result: dict,
    ) -> Path:

        return self.write_json(
            f"execution_{iteration:03d}.json",
            result,
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            self.root / name
        ).exists()

    def read_text(
        self,
        name: str,
    ) -> str:

        return (
            self.root / name
        ).read_text(
            encoding="utf-8",
        )

    def list(self) -> list[Path]:

        return sorted(
            path
            for path in self.root.rglob("*")
            if path.is_file()
        )

    def clear(self) -> None:

        for path in self.root.rglob("*"):

            if path.is_file():
                path.unlink()

        for path in sorted(
            self.root.rglob("*"),
            reverse=True,
        ):

            if path.is_dir() and path != self.root:
                path.rmdir()