"""LLM planner; it can select work but cannot produce the user response."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class PlannedCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class Plan:
    calls: list[PlannedCall]
    complete: bool
    planner_note: str


class Planner:
    def __init__(self, llm: Any, registry: Any) -> None:
        self.llm = llm
        self.registry = registry

    def plan(self, objective: str, history: list[Any]) -> Plan:
        logger.info("Requesting plan (history_records=%d, available_operations=%d).", len(history), len(self.registry.schemas()))
        messages: list[Any] = [HumanMessage(content=objective)]
        for record in history:
            messages.append(HumanMessage(content=f"Verified capability result:\n{record.to_dict()}"))
        response = self.llm.invoke(messages=messages, role="planner", tools=self.registry.schemas())
        calls = [PlannedCall(call["id"], call["name"], call.get("args", {})) for call in response.tool_calls]
        logger.info("Planner returned %d operation(s): %s", len(calls), ", ".join(call.name for call in calls) or "none")
        # The planner can finish only after it has observed capability evidence, except for a task requiring no work.
        return Plan(calls=calls, complete=not calls, planner_note=str(response.content or ""))
