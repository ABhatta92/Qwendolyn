from __future__ import annotations

from qwendolyn.agent.planner import Planner
from qwendolyn.llm.llm import LLM


def main():

    llm = LLM(
        model_name="qwen2.5:1.5b",
        temperature=0.1,
        system_prompt=r"qwendolyn/llm/prompts/planner.txt",
    )

    planner = Planner(
        llm=llm,
    )

    objective = input(
        "\nObjective: "
    ).strip()

    if not objective:
        print("No objective provided.")
        return

    plan = planner.plan(
        objective,
    )

    print("\n")
    print("=" * 80)
    print("PLAN")
    print("=" * 80)

    print(
        f"\nObjective:\n{plan.objective}\n"
    )

    for index, step in enumerate(
        plan.steps,
        start=1,
    ):

        dependencies = (
            ", ".join(step.depends_on)
            if step.depends_on
            else "None"
        )

        print(
            f"\nStep {index}: {step.id}"
        )

        print(
            f"Description: {step.description}"
        )

        print(
            f"Depends on: {dependencies}"
        )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()