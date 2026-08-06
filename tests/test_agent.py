from __future__ import annotations

from dataclasses import dataclass, field

from qwendolyn.agent.agent import Agent
from qwendolyn.capabilities.base import CapabilityResult
from qwendolyn.capabilities.registry import CapabilityRegistry


@dataclass
class Response:
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)


class FakeLLM:
    def __init__(self) -> None:
        self.count = 0

    def invoke(self, messages, role, tools=None):
        if role == "responder":
            return Response("Verified work summary.")
        self.count += 1
        return Response(tool_calls=[{"id": "call-1", "name": "success", "args": {}}] if self.count == 1 else [])


class Capability:
    name = "test"
    description = "test"
    functions = [{"type": "function", "function": {"name": "success", "description": "success", "parameters": {"type": "object", "properties": {}}}}]

    def execute(self, function_name, **kwargs):
        return CapabilityResult(True, "Verified.")


def test_agent_executes_then_responds() -> None:
    registry = CapabilityRegistry()
    registry.register(Capability())
    assert Agent(FakeLLM(), registry).run("Do work") == "Verified work summary."
