from qwendolyn.agent.frontend_agent import FrontendAgent
from qwendolyn.agent.python_agent import PythonAgent
from qwendolyn.llm.llm import LLM


def create_python_agent() -> PythonAgent:

    llm = LLM(
        model_name="qwen3",
        temperature=0.1,
        system_prompt="qwendolyn/llm/prompts/python.txt",
    )

    return PythonAgent(
        llm=llm,
    )


def create_frontend_agent() -> FrontendAgent:

    llm = LLM(
        model_name="qwen3",
        temperature=0.3,
        system_prompt="qwendolyn/llm/prompts/frontend.txt",
    )

    return FrontendAgent(
        llm=llm,
    )


def create_agents() -> dict[str, object]:

    return {
        "Python": create_python_agent(),
        "Frontend": create_frontend_agent(),
    }