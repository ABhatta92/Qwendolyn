from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
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
            "dev": self._load_prompt("developer.txt"),
            "analyst": self._load_prompt("analyst.txt"),
        }

        logger.info("Initialized Ollama LLM for model %s", model_name)

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(__file__).parent / "prompts" / filename
        logger.info("Loading prompt file %s", filename)
        return prompt_path.read_text(encoding="utf-8")

    def invoke(self, prompt: str, mode: str = "dev") -> str:
        logger.info("Invoking LLM in %s mode", mode)

        messages = [
            SystemMessage(content=self.prompts[mode]),
            HumanMessage(content=prompt),
        ]

        response = self.llm.invoke(messages)
        logger.info("Received LLM response for %s mode", mode)

        return response.content