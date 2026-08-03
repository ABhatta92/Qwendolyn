from qwendolyn.utils.logging import get_logger

logger = get_logger(__name__, log_file="executor")


class Executor:

    def __init__(
        self,
        registry,
    ):

        self.registry = registry

    def execute(
        self,
        plan: dict,
    ) -> dict:

        logger.info(
            "Executing %d tool(s).",
            len(plan["tool_calls"]),
        )

        execution = {
            "assistant": plan["assistant"],
            "tools": [],
            "created_files": [],
            "success": True,
        }

        for tool_call in plan["tool_calls"]:

            function_name = tool_call["name"]
            arguments = tool_call.get("args", {})

            logger.info(
                "Executing function '%s' with args=%s",
                function_name,
                arguments,
            )

            try:

                result = self.registry.execute(
                    function_name=function_name,
                    **arguments,
                )

                execution["tools"].append(
                    {
                        "tool_call_id": tool_call["id"],
                        "function_name": function_name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                if isinstance(result, dict):

                    created = result.get(
                        "created_files",
                        [],
                    )

                    if created:
                        execution["created_files"].extend(
                            created
                        )

            except Exception as ex:

                logger.exception(
                    "Execution failed for '%s'",
                    function_name,
                )

                execution["success"] = False

                execution["tools"].append(
                    {
                        "tool_call_id": tool_call["id"],
                        "function_name": function_name,
                        "arguments": arguments,
                        "result": {
                            "success": False,
                            "error": str(ex),
                        },
                    }
                )

        return execution