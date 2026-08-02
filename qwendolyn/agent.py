from langchain_core.messages import HumanMessage, ToolMessage

from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="agent")


class Agent:

    def __init__(
        self,
        llm,
        registry,
    ):

        self.llm = llm
        self.registry = registry

    def run(
        self,
        prompt: str,
        persona: str = "developer",
    ) -> str:

        logger.info("Received prompt")

        messages = [
            HumanMessage(content=prompt),
        ]

        # Initial LLM call
        response = self.llm.invoke(
            messages=messages,
            persona=persona,
            tools=self.registry.schemas(),
        )

        messages.append(response)

        # No tool requested
        if not response.tool_calls:

            logger.info("No tool calls requested.")

            return response.content

        logger.info(
            "LLM requested %d tool(s).",
            len(response.tool_calls),
        )

        # Execute all requested tools
        for tool_call in response.tool_calls:

            function_name = tool_call["name"]
            arguments = tool_call.get("args", {})

            logger.info(
                "Executing function '%s' with args=%s",
                function_name,
                arguments,
            )

            result = self.registry.execute(
                function_name=function_name,
                **arguments,
            )

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )

        # Final LLM call with tool results
        final_response = self.llm.invoke(
            messages=messages,
            persona=persona,
        )

        logger.info("Returning final response.")

        return final_response.content