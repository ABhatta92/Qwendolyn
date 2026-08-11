from __future__ import annotations

import re
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage

from qwendolyn.logging.logging import get_logger


logger = get_logger(__name__)


@dataclass(slots=True)
class AgentState:
    objective: str
    current_step: int = 0
    last_result: dict | None = None
    completed_steps: list[str] = field(
        default_factory=list
    )
    step_results: list[dict] = field(
        default_factory=list
    )


class Agent:

    def __init__(
        self,
        llm,
        runner,
        language: str,
        planner=None,
        validator=None,
        max_iterations: int = 3,
    ):

        self.llm = llm
        self.runner = runner
        self.language = language
        self.planner = planner
        self.validator = validator
        self.max_iterations = max_iterations

    # -------------------------------------------------------------------------
    # Planning
    # -------------------------------------------------------------------------

    def _create_plan(
        self,
        objective: str,
    ):

        if self.planner is None:

            logger.info(
                "No planner configured. Running directly."
            )

            return None

        logger.info(
            "Creating execution plan."
        )

        plan = self.planner.plan(
            objective,
        )

        logger.info(
            "Plan created with %d step(s).",
            len(plan.steps),
        )

        for index, step in enumerate(
            plan.steps,
            start=1,
        ):

            logger.info(
                "  %d. %s",
                index,
                step.description,
            )

        return plan

    # -------------------------------------------------------------------------
    # Prompt Construction
    # -------------------------------------------------------------------------

    def _build_prompt(
        self,
        state: AgentState,
        step_description: str,
    ) -> str:

        sections = [
            "OBJECTIVE",
            "---------",
            state.objective,
            "",
            "CURRENT STEP",
            "------------",
            step_description,
            "",
        ]

        if state.completed_steps:

            sections.extend(
                [
                    "COMPLETED STEPS",
                    "---------------",
                    "\n".join(
                        f"- {step}"
                        for step in state.completed_steps
                    ),
                    "",
                ]
            )

        if state.step_results:

            sections.extend(
                [
                    "PREVIOUS STEP RESULTS",
                    "---------------------",
                ]
            )

            for result in state.step_results:

                sections.extend(
                    [
                        f"Step: {result['step']}",
                        f"Success: {result['success']}",
                        f"Return Code: {result['return_code']}",
                        "",
                        "Created Files",
                        "-------------",
                        "\n".join(
                            result.get(
                                "created_files",
                                [],
                            )
                        )
                        or "None",
                        "",
                        "STDOUT",
                        "------",
                        result.get(
                            "stdout",
                            "",
                        )
                        or "<empty>",
                        "",
                        "STDERR",
                        "------",
                        result.get(
                            "stderr",
                            "",
                        )
                        or "<empty>",
                        "",
                    ]
                )

        if state.last_result is not None:

            result = state.last_result

            sections.extend(
                [
                    "LAST EXECUTION",
                    "--------------",
                    f"Success: {result.get('success')}",
                    f"Return Code: {result.get('return_code')}",
                    (
                        f"Execution Time: "
                        f"{result.get('execution_time', 0):.2f} sec"
                    ),
                    "",
                    "STDOUT",
                    "------",
                    result.get(
                        "stdout",
                        "",
                    )
                    or "<empty>",
                    "",
                    "STDERR",
                    "------",
                    result.get(
                        "stderr",
                        "",
                    )
                    or "<empty>",
                    "",
                ]
            )

        sections.extend(
            [
                "INSTRUCTIONS",
                "------------",
                "Complete the current step.",
                "Inspect the workspace and available data when necessary.",
                "Generate ONE complete executable program.",
                "Do not explain your reasoning.",
                "Do not output multiple solutions.",
                "If execution is required, output exactly one fenced Python code block.",
                "Do not claim completion unless the current step has actually been completed.",
            ]
        )

        return "\n".join(
            sections
        )

    # -------------------------------------------------------------------------
    # Step Execution
    # -------------------------------------------------------------------------

    def _execute_step(
        self,
        state: AgentState,
        step_description: str,
    ) -> dict:

        previous_code: str | None = None

        for attempt in range(
            1,
            self.max_iterations + 1,
        ):

            logger.info(
                "Step attempt %d/%d",
                attempt,
                self.max_iterations,
            )

            prompt = self._build_prompt(
                state,
                step_description,
            )

            response = self.llm.invoke(
                [
                    HumanMessage(
                        content=prompt,
                    )
                ]
            )

            content = str(
                response.content
            ).strip()

            code = self._extract_code(
                content
            )

            # -----------------------------------------------------------------
            # Model claims completion without executable code.
            # Do NOT automatically treat this as success.
            # -----------------------------------------------------------------

            if code is None:

                logger.warning(
                    "Model returned no executable code."
                )

                if (
                    "TASK COMPLETE" in content.upper()
                    or "STEP COMPLETE" in content.upper()
                ):

                    return {
                        "success": True,
                        "return_code": 0,
                        "stdout": content,
                        "stderr": "",
                        "execution_time": 0.0,
                        "created_files": [],
                        "model_response": content,
                    }

                return {
                    "success": False,
                    "return_code": None,
                    "stdout": content,
                    "stderr": (
                        "Model did not provide executable Python code."
                    ),
                    "execution_time": 0.0,
                    "created_files": [],
                    "model_response": content,
                }

            # -----------------------------------------------------------------
            # Prevent identical retries.
            # -----------------------------------------------------------------

            if previous_code == code:

                logger.warning(
                    "Model generated identical code twice."
                )

                return {
                    "success": False,
                    "return_code": None,
                    "stdout": "",
                    "stderr": (
                        "Model generated identical code twice."
                    ),
                    "execution_time": 0.0,
                    "created_files": [],
                    "model_response": content,
                }

            previous_code = code

            logger.info(
                "Executing generated %s code.",
                self.language,
            )

            result = self.runner.execute(
                code,
            )

            state.last_result = result

            # -----------------------------------------------------------------
            # No validator: successful process execution is sufficient.
            # -----------------------------------------------------------------

            if self.validator is None:

                if result.get(
                    "return_code"
                ) == 0:

                    result["model_response"] = content

                    return result

                continue

            # -----------------------------------------------------------------
            # Validate execution.
            # -----------------------------------------------------------------

            validation = self.validator.validate(
                step_description,
                result,
            )

            result["validation"] = validation
            result["model_response"] = content

            logger.info(
                "Validation success: %s",
                validation.success,
            )

            for warning in validation.warnings:

                logger.warning(
                    "Validation warning: %s",
                    warning,
                )

            if validation.success:

                return result

            for error in validation.errors:

                logger.error(
                    "Validation error: %s",
                    error,
                )

        raise RuntimeError(
            f"Maximum attempts ({self.max_iterations}) "
            f"exceeded for step: {step_description}"
        )

    # -------------------------------------------------------------------------
    # Code Extraction
    # -------------------------------------------------------------------------

    def _extract_code(
        self,
        response: str,
    ) -> str | None:

        pattern = re.compile(
            r"```(?:python)?\s*(.*?)```",
            flags=re.DOTALL | re.IGNORECASE,
        )

        match = pattern.search(
            response,
        )

        if match is None:
            return None

        return match.group(1).strip()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def run(
        self,
        objective: str,
    ) -> str:

        logger.info(
            "=" * 80
        )

        logger.info(
            "Starting %s agent.",
            self.language,
        )

        logger.info(
            "Objective: %s",
            objective,
        )

        state = AgentState(
            objective=objective,
        )

        plan = self._create_plan(
            objective,
        )

        # ---------------------------------------------------------------------
        # Direct execution mode
        # ---------------------------------------------------------------------

        if plan is None:

            result = self._execute_step(
                state,
                objective,
            )

            if result.get(
                "model_response"
            ):

                return result[
                    "model_response"
                ]

            return (
                "TASK COMPLETE\n\n"
                "Execution completed successfully."
            )

        # ---------------------------------------------------------------------
        # Planned execution mode
        # ---------------------------------------------------------------------

        for index, step in enumerate(
            plan.steps,
            start=1,
        ):

            state.current_step = index

            # Only clear the immediate execution result.
            # Historical step results remain available to the worker.
            state.last_result = None

            logger.info(
                "=" * 80
            )

            logger.info(
                "Executing plan step %d/%d: %s",
                index,
                len(plan.steps),
                step.description,
            )

            result = self._execute_step(
                state,
                step.description,
            )

            if not result.get(
                "success"
            ):

                raise RuntimeError(
                    f"Plan step {index} failed: "
                    f"{step.description}\n\n"
                    f"{result.get('stderr', '')}"
                )

            state.completed_steps.append(
                step.description
            )

            state.step_results.append(
                {
                    "step": step.description,
                    "success": result.get(
                        "success",
                        False,
                    ),
                    "return_code": result.get(
                        "return_code"
                    ),
                    "execution_time": result.get(
                        "execution_time",
                        0.0,
                    ),
                    "created_files": result.get(
                        "created_files",
                        [],
                    ),
                    "stdout": result.get(
                        "stdout",
                        "",
                    ),
                    "stderr": result.get(
                        "stderr",
                        "",
                    ),
                }
            )

            logger.info(
                "Plan step %d completed.",
                index,
            )

        logger.info(
            "=" * 80
        )

        logger.info(
            "%s agent completed objective.",
            self.language,
        )

        return (
            "TASK COMPLETE\n\n"
            f"Completed {len(plan.steps)} planned step(s)."
        )