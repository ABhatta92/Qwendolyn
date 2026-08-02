from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="llm")


class OllamaLLM:

    def __init__(
        self,
        model_name: str = "qwen3",
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.temperature = temperature

        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
        )

        self.prompts = {
            "developer": self._load_prompt("developer.txt"),
            "analyst": self._load_prompt("analyst.txt"),
        }

        logger.info(
            "Initialized Ollama LLM for model '%s'",
            model_name,
        )

    def _load_prompt(self, filename: str) -> str:

        prompt_path = Path(__file__).parent / "prompts" / filename

        logger.info("Loading prompt '%s'", filename)

        return prompt_path.read_text(encoding="utf-8")

    def invoke(
        self,
        messages: list,
        persona: str = "developer",
        tools: list | None = None,
    ):
        """
        Invoke the model.

        Parameters
        ----------
        messages
            Conversation messages excluding the system prompt.

        persona
            developer | analyst

        tools
            OpenAI/Qwen-compatible tool definitions.
        """

        logger.info(
            "Invoking LLM (persona=%s, tools=%d)",
            persona,
            len(tools) if tools else 0,
        )

        full_messages = [
            SystemMessage(
                content=self.prompts[persona]
            ),
            *messages,
        ]

        if tools:

            response = self.llm.bind_tools(
                tools
            ).invoke(full_messages)

        else:

            response = self.llm.invoke(full_messages)

        logger.info(
            "Received response (tool_calls=%d)",
            len(response.tool_calls),
        )

        return response