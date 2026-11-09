"""Local conversational orchestration for HOID."""

from __future__ import annotations

from .ollama import OllamaClient, OllamaError
from .requests import DeviceController
from .tools import ToolError, execute_tool


SYSTEM_PROMPT = (
    "You are HOID, a concise, personable home assistant. "
    "You are having a natural spoken conversation with the user. "
    "Answer ordinary questions directly without calling tools. "
    "A discussion about tools, equipment, or how to perform a task "
    "is not a request to execute a software tool. "
    "Only request an action tool when the user explicitly asks you "
    "to perform that action. "
    "Never initiate timers, device changes, or other real-world "
    "actions merely because they are mentioned in conversation. "
    "Never claim an action succeeded unless a tool confirms it. "
    "If a tool fails, explain that the action was not verified. "
    "Keep spoken responses brief."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_timer",
            "description": (
                "Start a countdown timer that rings the user's telephone "
                "when it expires. Use only when the user explicitly asks "
                "you to start a timer, remind them after a duration, "
                "or ring them after a specified amount of time. "
                "Do not use for questions about tools, woodworking, "
                "or general conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_seconds": {
                        "type": "integer",
                        "description": (
                            "Timer duration in seconds, "
                            "between 1 and 86400."
                        ),
                    }
                },
                "required": ["duration_seconds"],
            },
        },
    }
]


def converse(
    text: str,
    model: OllamaClient,
    controller: DeviceController,
) -> str:
    """Process one user turn, allowing at most one tool call."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    response = model.chat(messages, tools=TOOLS)
    calls = response.get("tool_calls") or []

    if not calls:
        content = response.get("content")
        if not isinstance(content, str):
            raise OllamaError("Invalid conversational response.")
        return content

    if not isinstance(calls, list) or len(calls) != 1:
        raise ToolError("Expected exactly one tool call.")

    call = calls[0]
    if not isinstance(call, dict):
        raise ToolError("Invalid tool call.")

    function = call.get("function")
    if not isinstance(function, dict):
        raise ToolError("Invalid tool function.")

    name = function.get("name")
    arguments = function.get("arguments")

    if not isinstance(name, str):
        raise ToolError("Invalid tool name.")

    try:
        result = execute_tool(name, arguments, controller)
    except Exception:
        # Never present a failed or uncertain action as verified.
        raise

    messages.append(response)
    messages.append(
        {
            "role": "tool",
            "tool_name": name,
            "content": result,
        }
    )

    final = model.chat(messages, tools=[])

    if final.get("tool_calls"):
        raise ToolError("Unexpected additional tool request.")

    content = final.get("content")
    if not isinstance(content, str) or not content.strip():
        raise OllamaError("Invalid final conversational response.")

    return content
