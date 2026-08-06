from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama


class LLM:

    def __init__(
        self,
        model_name: str = "qwen3",
        temperature: float = 0.2,
        system_prompt: str | Path | None = None,
    ):

        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
        )

        if system_prompt is None:

            system_prompt = (
                Path(__file__).parent
                / "prompts"
                / "python.txt"
            )

        self.system_prompt = Path(system_prompt).read_text(
            encoding="utf-8",
        )

    def invoke(
        self,
        messages: list,
    ):

        return self.llm.invoke(
            [
                SystemMessage(
                    content=self.system_prompt,
                ),
                *messages,
            ]
        )