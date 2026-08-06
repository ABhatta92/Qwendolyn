from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage

from qwendolyn.logging.run import Run
from qwendolyn.logging.logger import get_logger

logger = get_logger(__name__)


CODE_BLOCK = re.compile(
    r"```(?:python|html|javascript|js|json)?\s*(.*?)```",
    flags=re.DOTALL | re.IGNORECASE,
)


@dataclass(slots=True)
class ExecutionState:
    objective: str
    iteration: int = 0
    last_result: dict | None = None


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

    def _build_prompt(
        self,
        state: ExecutionState,
    ) -> str:

        sections = [
            "OBJECTIVE",
            "---------",
            state.objective,
            "",
        ]

        if state.last_result is None:

            sections.extend(
                [
                    "STATUS",
                    "------",
                    "No code has been executed yet.",
                    "",
                ]
            )

        else:

            result = state.last_result

            sections.extend(
                [
                    "LAST EXECUTION",
                    "--------------",
                    f"Success: {result['success']}",
                    f"Return Code: {result['return_code']}",
                    f"Execution Time: {result['execution_time']:.2f} sec",
                    "",
                    "Created Files",
                    "-------------",
                    "\n".join(result["created_files"])
                    if result["created_files"]
                    else "None",
                    "",
                    "STDOUT",
                    "------",
                    result["stdout"] or "<empty>",
                    "",
                    "STDERR",
                    "------",
                    result["stderr"] or "<empty>",
                    "",
                ]
            )

        sections.extend(
            [
                "INSTRUCTIONS",
                "------------",
                "Generate ONE complete executable program.",
                "Do not explain your reasoning.",
                "Do not output multiple solutions.",
                "If another execution is required, output exactly one fenced code block.",
                "If the objective has been completely achieved and no further execution is required, do NOT output a code block.",
                "Instead respond with:",
                "",
                "TASK COMPLETE",
                "<concise summary>",
            ]
        )

        return "\n".join(sections)

    def run(
        self,
        prompt: str,
    ) -> str:

        logger.info(
            "Starting %s task.",
            self.language,
        )

        run = Run(
            agent=self.language,
            objective=prompt,
        )

        state = ExecutionState(
            objective=prompt,
        )

        previous_code: str | None = None

        try:

            for _ in range(
                self.max_iterations,
            ):

                iteration = run.next_iteration()
                state.iteration = iteration

                logger.info(
                    "Iteration %d",
                    iteration,
                )

                prompt_text = self._build_prompt(
                    state,
                )

                response = self.llm.invoke(
                    [
                        HumanMessage(
                            content=prompt_text,
                        )
                    ],
                    run=run,
                    iteration=iteration,
                )

                content = str(
                    response.content,
                ).strip()

                if content.startswith(
                    "TASK COMPLETE"
                ):

                    logger.info(
                        "Task completed."
                    )

                    run.finish(
                        success=True,
                    )

                    return content

                code = self._extract_code(
                    content,
                )

                if code is None:

                    logger.info(
                        "No executable code returned."
                    )

                    run.finish(
                        success=True,
                    )

                    return content

                if previous_code == code:

                    run.finish(
                        success=False,
                    )

                    raise RuntimeError(
                        "Agent generated identical code twice. Possible infinite loop."
                    )

                previous_code = code

                logger.info(
                    "Executing generated %s program.",
                    self.language,
                )

                result = self.runner.execute(
                    code,
                    run=run,
                    iteration=iteration,
                )

                state.last_result = result

            run.finish(
                success=False,
            )

            raise RuntimeError(
                f"Maximum iterations ({self.max_iterations}) exceeded."
            )

        except Exception:

            run.finish(
                success=False,
            )

            raise