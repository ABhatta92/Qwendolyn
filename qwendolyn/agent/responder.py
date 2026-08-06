"""Generate the final user response from verified execution evidence."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


RESPONDER_RULES = """
You are Qwendolyn.

You are responsible only for communicating verified outcomes.

Rules:

- Never invent work that was not verified.
- Never claim success unless capability evidence proves it.
- Never claim files, tables or views exist unless they appear in the evidence.
- Never invent row counts or metrics.
- If a task failed, explain why using the verified error.
- If work is incomplete, clearly state what remains.
- Summarize what was actually accomplished.
- Use concise, professional language.
"""


class Responder:

    def __init__(
        self,
        llm: Any,
    ) -> None:

        self.llm = llm

    def _build_prompt(
        self,
        objective: str,
        history: list[Any],
        completed: bool,
        failure_reason: str | None,
    ) -> str:

        sections = [
            RESPONDER_RULES,
            "",
            "==================================================",
            "OBJECTIVE",
            "==================================================",
            objective,
            "",
            "==================================================",
            "TASK STATUS",
            "==================================================",
            "Completed" if completed else "Incomplete",
            "",
        ]

        if failure_reason:

            sections.extend(
                [
                    "Failure Reason",
                    failure_reason,
                    "",
                ]
            )

        sections.extend(
            [
                "==================================================",
                "VERIFIED EXECUTION EVIDENCE",
                "==================================================",
            ]
        )

        if not history:

            sections.append(
                "No capability executions were performed."
            )

        else:

            for index, record in enumerate(history, start=1):

                sections.extend(
                    [
                        f"Step {index}",
                        str(record),
                        "",
                    ]
                )

        sections.extend(
            [
                "==================================================",
                "FINAL RESPONSE",
                "==================================================",
                "Generate a response using ONLY the verified evidence above.",
            ]
        )

        return "\n".join(sections)

    def respond(
        self,
        objective: str,
        history: list[Any],
        completed: bool,
        failure_reason: str | None = None,
    ) -> str:

        logger.info(
            "Generating final response (completed=%s, steps=%d).",
            completed,
            len(history),
        )

        response = self.llm.invoke(
            messages=[
                HumanMessage(
                    content=self._build_prompt(
                        objective=objective,
                        history=history,
                        completed=completed,
                        failure_reason=failure_reason,
                    )
                )
            ],
            role="responder",
        )

        logger.info(
            "Final response generated."
        )

        return str(response.content)