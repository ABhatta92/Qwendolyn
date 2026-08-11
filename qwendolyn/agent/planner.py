from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage


@dataclass(slots=True)
class PlanStep:
    id: str
    description: str
    depends_on: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class Plan:
    objective: str
    steps: list[PlanStep] = field(
        default_factory=list
    )


class Planner:

    def __init__(self, llm):
        self.llm = llm

    def plan(
        self,
        objective: str,
    ) -> Plan:

        prompt = f"""
Create a concise execution plan for the following objective.

## Objective

{objective}

## Requirements

- Break the objective into clear, executable steps.
- Keep the number of steps small.
- Order steps by dependency.
- Do not execute anything.
- Do not write implementation code.
- Return only the plan.

Format exactly as:

1. Step description
2. Step description
3. Step description
""".strip()

        response = self.llm.invoke(
            [
                HumanMessage(
                    content=prompt,
                )
            ]
        )

        steps = self._parse_steps(
            response.content,
        )

        return Plan(
            objective=objective,
            steps=steps,
        )

    def _parse_steps(
        self,
        content: str,
    ) -> list[PlanStep]:

        steps: list[PlanStep] = []

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            if not line[0].isdigit():
                continue

            if "." not in line:
                continue

            number, description = line.split(
                ".",
                1,
            )

            description = description.strip()

            if not description:
                continue

            step_id = f"step_{int(number)}"

            dependencies: list[str] = []

            if steps:
                dependencies.append(
                    steps[-1].id
                )

            steps.append(
                PlanStep(
                    id=step_id,
                    description=description,
                    depends_on=dependencies,
                )
            )

        if not steps:
            raise ValueError(
                "Planner failed to produce a valid execution plan."
            )

        return steps