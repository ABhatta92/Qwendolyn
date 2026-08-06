from __future__ import annotations

import re

from langchain_core.messages import AIMessage, HumanMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


CODE_BLOCK = re.compile(
    r"```(?:python|html|javascript|js|json)?\s*(.*?)```",
    flags=re.DOTALL | re.IGNORECASE,
)


class Agent:

    def __init__(
        self,
        llm,
        runner,
        language: str,
        max_iterations: int = 20,
    ):

        self.llm = llm
        self.runner = runner
        self.language = language
        self.max_iterations = max_iterations

    def _extract_code(
        self,
        response: str,
    ) -> str | None:

        match = CODE_BLOCK.search(response)

        if match is None:
            return None

        return match.group(1).strip()

    def _execution_message(
        self,
        result: dict,
    ) -> HumanMessage:

        created_files = result.get(
            "created_files",
            [],
        )

        return HumanMessage(
            content=f"""
Execution completed.

Success
-------
{result["success"]}

Return Code
-----------
{result["return_code"]}

Execution Time
--------------
{result["execution_time"]:.2f} seconds

Created Files
-------------
{chr(10).join(created_files) if created_files else "None"}

STDOUT
------
{result["stdout"]}

STDERR
------
{result["stderr"]}
""".strip()
        )

    def run(
        self,
        prompt: str,
    ) -> str:

        logger.info(
            "Starting %s task.",
            self.language,
        )

        messages = [
            HumanMessage(
                content=prompt,
            )
        ]

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):

            logger.info(
                "Iteration %d",
                iteration,
            )

            response = self.llm.invoke(
                messages,
            )

            messages.append(
                AIMessage(
                    content=response.content,
                )
            )

            code = self._extract_code(
                response.content,
            )

            if code is None:

                logger.info(
                    "Task completed."
                )

                return response.content

            result = self.runner.execute(
                code,
            )

            messages.append(
                self._execution_message(
                    result,
                )
            )

        raise RuntimeError(
            f"Maximum iterations ({self.max_iterations}) exceeded."
        )