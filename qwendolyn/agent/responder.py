from langchain_core.messages import AIMessage, HumanMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="responder")


class Responder:

    def __init__(
        self,
        llm,
    ):

        self.llm = llm

    def respond(
        self,
        context: dict,
    ) -> str:

        logger.info("Generating final response.")

        messages = [
            HumanMessage(
                content=context["prompt"],
            )
        ]

        for execution in context["results"]:

            messages.append(
                execution["assistant"]
            )

            for tool in execution["tools"]:

                messages.append(
                    AIMessage(
                        content=f"""
Capability: {tool['function_name']}

Arguments:
{tool['arguments']}

Result:
{tool['result']}
""".strip()
                    )
                )

        messages.append(
            HumanMessage(
                content="""
The task has completed.

Summarize what you accomplished for the user.

If files or tables were created, mention them.

Do not generate Python code.

Do not suggest how the user could perform the task.

Only describe what was actually completed.
""".strip()
            )
        )

        response = self.llm.invoke(
            messages=messages,
            persona=context["persona"],
        )

        logger.info("Final response generated.")

        return response.content