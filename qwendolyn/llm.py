"""Role-specific Ollama invocations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama


class OllamaLLM:
    def __init__(self, model_name: str = "qwen3", temperature: float = 0.2) -> None:
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        prompt_dir = Path(__file__).parent / "prompts"
        self.prompts = {role: (prompt_dir / f"{role}.txt").read_text(encoding="utf-8") for role in ("planner", "responder")}

    def invoke(self, messages: list[Any], role: str, tools: list[dict[str, Any]] | None = None) -> Any:
        if role not in self.prompts:
            raise ValueError(f"Unknown LLM role '{role}'.")
        request = [SystemMessage(content=self.prompts[role]), *messages]
        return self.llm.bind_tools(tools).invoke(request) if tools else self.llm.invoke(request)
