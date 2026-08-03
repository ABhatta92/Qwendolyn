from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="planner")


class Planner:

    def __init__(
        self,
        llm,
        registry,
    ):

        self.llm = llm
        self.registry = registry

    def plan(self, context: dict):

        logger.info("Planning next action.")

        messages = [
            HumanMessage(
                content=context["prompt"]
            )
        ]

        # Replay execution history
        for result in context["results"]:

            messages.append(result["assistant"])

            for tool in result["tools"]:

                messages.append(
                    ToolMessage(
                        content=str(tool["result"]),
                        tool_call_id=tool["tool_call_id"],
                    )
                )

        response = self.llm.invoke(
            messages=messages,
            persona=context["persona"],
            tools=self.registry.schemas(),
        )

        logger.info(
            "Planner produced %d tool call(s).",
            len(response.tool_calls),
        )

        return {
            "assistant": response,
            "tool_calls": response.tool_calls,
            "complete": len(response.tool_calls) == 0,
        }