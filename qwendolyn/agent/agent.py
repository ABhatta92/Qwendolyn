from __future__ import annotations

import re

from langchain_core.messages import AIMessage, HumanMessage

from qwendolyn import config
from qwendolyn.runtime.python_runner import PythonRunner
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


PYTHON_BLOCK = re.compile(
    r"```python\s*(.*?)```",
    flags=re.DOTALL | re.IGNORECASE,
)


class Agent:

    def __init__(
        self,
        llm,
        max_iterations: int = 20,
    ):

        self.llm = llm
        self.workspace = config.WORKSPACE
        self.scripts = config.SCRIPTS

        self.runner = PythonRunner(
            working_directory=config.WORKSPACE,
        )

        self.max_iterations = max_iterations

    def _extract_python(
        self,
        response: str,
    ) -> str | None:

        match = PYTHON_BLOCK.search(response)

        if match is None:
            return None

        return match.group(1).strip()

    def _execution_message(
        self,
        result: dict,
    ) -> HumanMessage:

        return HumanMessage(
            content=f"""
Python execution completed.

Script
------
{result["script"]}

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
{chr(10).join(result["created_files"]) if result["created_files"] else "None"}

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

        logger.info("Starting task.")

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

            response = self.llm.invoke(messages)

            messages.append(
                AIMessage(
                    content=response.content,
                )
            )

            code = self._extract_python(
                response.content,
            )

            if code is None:

                logger.info(
                    "No Python generated. Task complete."
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