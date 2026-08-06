"""Role-specific Ollama invocations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaLLM:
    def __init__(self, model_name: str = "qwen3", temperature: float = 0.2) -> None:
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        prompt_dir = Path(__file__).parent / "prompts"
        self.prompts = {role: (prompt_dir / f"{role}.txt").read_text(encoding="utf-8") for role in ("planner", "responder")}
        logger.info("Initialized Ollama LLM (model=%s, temperature=%s).", model_name, temperature)

    def invoke(self, messages: list[Any], role: str, tools: list[dict[str, Any]] | None = None) -> Any:
        if role not in self.prompts:
            raise ValueError(f"Unknown LLM role '{role}'.")
        logger.info("Invoking LLM role '%s' (messages=%d, tools=%d).", role, len(messages), len(tools or []))
        request = [SystemMessage(content=self.prompts[role]), *messages]
        response = self.llm.bind_tools(tools).invoke(request) if tools else self.llm.invoke(request)
        logger.info("LLM role '%s' returned %d tool call(s).", role, len(getattr(response, "tool_calls", [])))
        return response
