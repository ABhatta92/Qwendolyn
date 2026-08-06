"""LLM planner responsible for selecting the next capability call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


PLANNER_RULES = """
You are the planning component of Qwendolyn.

You are NOT the assistant.
You NEVER answer the user.
You NEVER explain your reasoning.
You NEVER summarize work.

Your only responsibility is to determine the SINGLE best next action.

Follow this workflow:

1. Understand the objective.
2. Determine what information is missing.
3. Gather missing information using capabilities.
4. Never assume schemas.
5. Never assume join keys.
6. Never assume database tables exist.
7. Never assume files exist.
8. Never assume Python execution succeeded.
9. Use capability evidence only.
10. Execute ONE meaningful capability call.
11. Wait for the result before planning again.

Rules:

- Inspect before transforming.
- Verify before declaring success.
- If Python failed, fix the failure before continuing.
- If outputs have not been verified, continue planning.
- Do not request multiple unrelated operations in one step.
- Prefer execute_python for data engineering tasks.
- Use filesystem only for workspace management.
- Use database only for SQL and metadata operations.

If no further capability call is required because the objective has been completely achieved using verified evidence, return no tool calls.
"""


@dataclass(slots=True)
class PlannedCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class Plan:
    calls: list[PlannedCall]
    planner_note: str


class Planner:

    def __init__(
        self,
        llm: Any,
        registry: Any,
    ) -> None:

        self.llm = llm
        self.registry = registry

    def _build_prompt(
        self,
        objective: str,
        history: list[Any],
    ) -> str:

        sections = [
            PLANNER_RULES,
            "",
            "==================================================",
            "OBJECTIVE",
            "==================================================",
            objective,
            "",
            "==================================================",
            "VERIFIED EVIDENCE",
            "==================================================",
        ]

        if not history:

            sections.append(
                "No capability executions have been performed yet."
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
                "NEXT ACTION",
                "==================================================",
                "Determine the SINGLE best next capability call.",
                "If the objective has already been achieved using VERIFIED evidence, return no tool calls.",
            ]
        )

        return "\n".join(sections)

    def plan(
        self,
        objective: str,
        history: list[Any],
    ) -> Plan:

        logger.info(
            "Planning next action (history=%d, functions=%d).",
            len(history),
            len(self.registry.schemas()),
        )

        response = self.llm.invoke(
            messages=[
                HumanMessage(
                    content=self._build_prompt(
                        objective=objective,
                        history=history,
                    )
                )
            ],
            role="planner",
            tools=self.registry.schemas(),
        )

        calls = [
            PlannedCall(
                id=call["id"],
                name=call["name"],
                arguments=call.get("args", {}),
            )
            for call in response.tool_calls
        ]

        logger.info(
            "Planner selected %d operation(s): %s",
            len(calls),
            ", ".join(call.name for call in calls) or "none",
        )

        return Plan(
            calls=calls,
            planner_note=str(response.content or ""),
        )