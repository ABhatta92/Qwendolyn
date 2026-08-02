from langchain_ollama import ChatOllama


class OllamaLLM:
    """
    Simple wrapper exposing an Ollama-hosted LLM.
    """

    def __init__(self, model_name: str = "qwen3", temperature: float = 0.2):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature
        )

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content
