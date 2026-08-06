from pathlib import Path

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_ollama import ChatOllama

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="llm")


class LLM:

    def __init__(
        self,
        model_name: str = "qwen3",
        temperature: float = 0.1,
        system_prompt: str | Path | None = None,
    ):

        self.model_name = model_name
        self.temperature = temperature

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

        system_prompt = Path(system_prompt)

        self.system_prompt = system_prompt.read_text(
            encoding="utf-8",
        )

        logger.info(
            "Initialized model='%s' temperature=%s prompt='%s'",
            self.model_name,
            self.temperature,
            system_prompt,
        )

    def invoke(
        self,
        messages: list[BaseMessage],
    ):

        prompt = [
            SystemMessage(
                content=self.system_prompt,
            ),
            *messages,
        ]

        logger.info("=" * 80)
        logger.info("LLM INVOCATION")
        logger.info("=" * 80)

        logger.info(
            "Model: %s | Temperature: %.2f | Messages: %d",
            self.model_name,
            self.temperature,
            len(prompt),
        )

        for index, message in enumerate(prompt, start=1):

            logger.info("-" * 80)
            logger.info(
                "MESSAGE %d (%s)",
                index,
                message.__class__.__name__,
            )
            logger.info(message.content)

        response = self.llm.invoke(prompt)

        logger.info("-" * 80)
        logger.info("MODEL RESPONSE")
        logger.info("-" * 80)
        logger.info(response.content)

        logger.info("=" * 80)

        return response