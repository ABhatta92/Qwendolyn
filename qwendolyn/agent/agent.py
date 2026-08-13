from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage

from qwendolyn.logging.logging import get_logger
from qwendolyn.logging.run_logger import RunLogger


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
                        (
                            "Execution Success: "
                            f"{result.get('execution_success', False)}"
                        ),
                        (
                            "Return Code: "
                            f"{result.get('return_code')}"
                        ),
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
                    (
                        "Execution Success: "
                        f"{result.get('execution_success', False)}"
                    ),
                    (
                        "Return Code: "
                        f"{result.get('return_code')}"
                    ),
                    (
                        "Execution Time: "
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
                "EXECUTION CONTRACT",
                "------------------",
                "Complete the current step by performing the required work.",
                "Inspect the workspace and available data when necessary.",
                "",
                "When action is required:",
                "- Generate exactly one complete executable Python program.",
                "- Output exactly one fenced Python code block.",
                "- The code must perform the current step.",
                "",
                "Do not merely describe what should be done.",
                "Do not provide multiple solutions.",
                "Do not claim the step is complete without evidence.",
                "",
                "IMPORTANT:",
                "A successful Python return code only means that the program "
                "executed without an unhandled exception.",
                "It does NOT mean that the current step was successfully "
                "completed.",
                "",
                "Inspect stdout, stderr, created files, and other available "
                "evidence after execution.",
                "If the program executes successfully but does not actually "
                "accomplish the current step, treat the step as unsuccessful.",
                "Modify the approach and execute again.",
                "",
                "When practical, generated Python should validate its own "
                "expected outputs and raise an error when required results "
                "are missing, empty, malformed, or otherwise invalid.",
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
        *,
        run: RunLogger,
        step_number: int,
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

            # -------------------------------------------------------------
            # LLM
            # -------------------------------------------------------------

            llm_start = time.perf_counter()

            try:

                response = self.llm.invoke(
                    [
                        HumanMessage(
                            content=prompt,
                        )
                    ]
                )

                llm_duration = (
                    time.perf_counter()
                    - llm_start
                )

                run.llm_call(
                    step=step_number,
                    attempt=attempt,
                    duration=llm_duration,
                    success=True,
                )

            except Exception as ex:

                llm_duration = (
                    time.perf_counter()
                    - llm_start
                )

                run.llm_call(
                    step=step_number,
                    attempt=attempt,
                    duration=llm_duration,
                    success=False,
                    message=str(ex),
                )

                raise

            content = str(
                response.content
            ).strip()

            code = self._extract_code(
                content,
            )

            # -------------------------------------------------------------
            # No executable action
            # -------------------------------------------------------------

            if code is None:

                logger.warning(
                    "Model returned no executable code."
                )

                run.event(
                    event_type="STEP_FAILED",
                    step=step_number,
                    attempt=attempt,
                    status="FAILED",
                    message=(
                        "Model did not provide executable Python code."
                    ),
                )

                return {
                    "success": False,
                    "execution_success": False,
                    "return_code": None,
                    "stdout": content,
                    "stderr": (
                        "Model did not provide executable Python code."
                    ),
                    "execution_time": 0.0,
                    "created_files": [],
                    "model_response": content,
                }

            # -------------------------------------------------------------
            # Prevent identical retries
            # -------------------------------------------------------------

            if previous_code == code:

                logger.warning(
                    "Model generated identical code twice."
                )

                run.event(
                    event_type="STEP_FAILED",
                    step=step_number,
                    attempt=attempt,
                    status="FAILED",
                    message=(
                        "Model generated identical code twice."
                    ),
                )

                return {
                    "success": False,
                    "execution_success": False,
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

            # -------------------------------------------------------------
            # Python execution
            # -------------------------------------------------------------

            logger.info(
                "Executing generated %s code.",
                self.language,
            )

            result = self.runner.execute(
                code,
            )

            state.last_result = result

            execution_success = result.get(
                "execution_success",
                result.get(
                    "success",
                    False,
                ),
            )

            # Keep both names available internally for compatibility.
            result["execution_success"] = (
                execution_success
            )

            result["success"] = (
                execution_success
            )

            # -------------------------------------------------------------
            # Record complete execution evidence
            # -------------------------------------------------------------

            run.execution(
                step=step_number,
                attempt=attempt,
                duration=result.get(
                    "execution_time",
                    0.0,
                ),
                success=execution_success,
                message=(
                    f"Return code: "
                    f"{result.get('return_code')}"
                ),
                stdout=result.get(
                    "stdout",
                    "",
                ),
                stderr=result.get(
                    "stderr",
                    "",
                ),
            )

            # -------------------------------------------------------------
            # Validation
            # -------------------------------------------------------------

            if self.validator is not None:

                validation_start = time.perf_counter()

                validation = self.validator.validate(
                    step_description,
                    result,
                )

                validation_duration = (
                    time.perf_counter()
                    - validation_start
                )

                result["validation"] = validation

                run.validation(
                    step=step_number,
                    success=validation.success,
                    message=(
                        f"Validation completed in "
                        f"{validation_duration:.2f}s"
                    ),
                )

                logger.info(
                    "Validation success: %s",
                    validation.success,
                )

                for warning in validation.warnings:

                    logger.warning(
                        "Validation warning: %s",
                        warning,
                    )

                for error in validation.errors:

                    logger.error(
                        "Validation error: %s",
                        error,
                    )

                if validation.success:

                    result["model_response"] = content

                    return result

                # Validation failed.
                #
                # Keep the result in state so the next LLM call can see
                # exactly what went wrong.
                state.last_result = result

                continue

            # -------------------------------------------------------------
            # No validator
            # -------------------------------------------------------------

            if execution_success:

                result["model_response"] = content

                return result

            # Execution failed. The next attempt receives stdout/stderr
            # through state.last_result.

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
    # Final Response
    # -------------------------------------------------------------------------

    def _build_final_response(
        self,
        state: AgentState,
    ) -> str:

        artifacts: list[str] = []

        for result in state.step_results:

            artifacts.extend(
                result.get(
                    "created_files",
                    [],
                )
            )

        artifacts = list(
            dict.fromkeys(
                artifacts
            )
        )

        lines = [
            "TASK COMPLETE",
            "",
            (
                f"Completed {len(state.completed_steps)} "
                "planned step(s)."
            ),
        ]

        if artifacts:

            lines.extend(
                [
                    "",
                    "Created artifacts:",
                ]
            )

            lines.extend(
                f"- {artifact}"
                for artifact in artifacts
            )

        return "\n".join(
            lines
        )

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

        run = RunLogger(
            agent=self.language,
            objective=objective,
        )

        state = AgentState(
            objective=objective,
        )

        try:

            plan = self._create_plan(
                objective,
            )

            # -------------------------------------------------------------
            # Direct execution mode
            # -------------------------------------------------------------

            if plan is None:

                result = self._execute_step(
                    state,
                    objective,
                    run=run,
                    step_number=1,
                )

                if not result.get(
                    "success"
                ):

                    raise RuntimeError(
                        result.get(
                            "stderr",
                            "Execution failed.",
                        )
                    )

                state.completed_steps.append(
                    objective
                )

                state.step_results.append(
                    {
                        "step": objective,
                        "success": result.get(
                            "success",
                            False,
                        ),
                        "execution_success": result.get(
                            "execution_success",
                            result.get(
                                "success",
                                False,
                            ),
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

                run.step_completed(
                    step=1,
                    description=objective,
                    duration=result.get(
                        "execution_time",
                        0.0,
                    ),
                )

                run.complete()

                return self._build_final_response(
                    state,
                )

            # -------------------------------------------------------------
            # Record plan
            # -------------------------------------------------------------

            run.plan_created(
                message="\n".join(
                    f"{index}. {step.description}"
                    for index, step in enumerate(
                        plan.steps,
                        start=1,
                    )
                )
            )

            # -------------------------------------------------------------
            # Planned execution mode
            # -------------------------------------------------------------

            for index, step in enumerate(
                plan.steps,
                start=1,
            ):

                state.current_step = index

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

                run.step_started(
                    step=index,
                    description=step.description,
                )

                step_start = time.perf_counter()

                result = self._execute_step(
                    state,
                    step.description,
                    run=run,
                    step_number=index,
                )

                step_duration = (
                    time.perf_counter()
                    - step_start
                )

                if not result.get(
                    "success"
                ):

                    error = (
                        f"Plan step {index} failed: "
                        f"{step.description}\n\n"
                        f"{result.get('stderr', '')}"
                    )

                    run.step_failed(
                        step=index,
                        message=error,
                    )

                    raise RuntimeError(
                        error
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
                        "execution_success": result.get(
                            "execution_success",
                            result.get(
                                "success",
                                False,
                            ),
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

                run.step_completed(
                    step=index,
                    description=step.description,
                    duration=step_duration,
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

            run.complete()

            return self._build_final_response(
                state,
            )

        except Exception as ex:

            logger.exception(
                "%s agent failed.",
                self.language,
            )

            run.fail(
                str(ex)
            )

            raise