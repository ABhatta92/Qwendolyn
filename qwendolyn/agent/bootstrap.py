from qwendolyn.agent.agent import Agent
from qwendolyn.llm import LLM


def create_agent() -> Agent:

    llm = LLM(
        model_name="qwen3",
        temperature=0.2,
    )

    return Agent(
        llm=llm,
    )