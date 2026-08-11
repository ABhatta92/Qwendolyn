from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ValidationResult:
    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Validator:

    def __init__(
        self,
        workspace: str | Path,
    ):
        self.workspace = Path(workspace).resolve()

    def validate(
        self,
        step_description: str,
        execution_result: dict,
    ) -> ValidationResult:
        """
        MVP validator.

        Validates basic execution health and reports observable
        problems. Task-specific validation can be added later.
        """

        errors: list[str] = []
        warnings: list[str] = []

        return_code = execution_result.get(
            "return_code"
        )

        if return_code is None:

            errors.append(
                "Execution did not produce a return code."
            )

        elif return_code != 0:

            errors.append(
                f"Process exited with return code {return_code}."
            )

        stderr = execution_result.get(
            "stderr",
            "",
        )

        if stderr.strip():

            warnings.append(
                "Execution produced stderr output."
            )

        created_files = execution_result.get(
            "created_files",
            [],
        )

        if not created_files:

            warnings.append(
                "No files were reported as created."
            )

        success = not errors

        return ValidationResult(
            success=success,
            errors=errors,
            warnings=warnings,
        )