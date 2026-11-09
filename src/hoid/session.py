"""Ephemeral conversational sessions for HOID."""

from __future__ import annotations

from .conversation import SYSTEM_PROMPT, TOOLS
from .ollama import OllamaClient, OllamaError
from .requests import DeviceController
from .tools import ToolError, execute_tool
from .authorization import authorize_action


class SessionClosed(Exception):
    """The conversation session has ended."""


class ConversationSession:
    """Maintain conversational context for one active session."""

    def __init__(
        self,
        model: OllamaClient,
        controller: DeviceController,
        max_turns: int = 10,
    ):
        if max_turns < 1:
            raise ValueError("max_turns must be positive")

        self.model = model
        self.controller = controller
        self.max_turns = max_turns
        self.history = []
        self.closed = False

    def ask(self, text: str) -> str:
        """Process one conversational turn."""

        if self.closed:
            raise SessionClosed("Conversation session is closed.")

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Conversation text must not be empty.")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.history,
            {"role": "user", "content": text},
        ]

        response = self.model.chat(messages, tools=TOOLS)

        if not isinstance(response, dict):
            raise OllamaError("Invalid model response.")

        calls = response.get("tool_calls") or []

        if calls:
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

            authorize_action(text, name)

            result = execute_tool(
                name,
                arguments,
                self.controller,
            )

            messages.append(response)
            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                }
            )

            final = self.model.chat(messages, tools=[])

            if not isinstance(final, dict):
                raise OllamaError("Invalid final response.")

            if final.get("tool_calls"):
                raise ToolError("Unexpected additional tool request.")

            answer = final.get("content")

            if not isinstance(answer, str) or not answer.strip():
                raise OllamaError("Invalid final conversational response.")

            self.history.extend([
                {"role": "user", "content": text},
                response,
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                },
                {"role": "assistant", "content": answer},
            ])

        else:
            answer = response.get("content")

            if not isinstance(answer, str) or not answer.strip():
                raise OllamaError("Invalid conversational response.")

            self.history.extend([
                {"role": "user", "content": text},
                {"role": "assistant", "content": answer},
            ])

        # Retain complete turns rather than trimming arbitrary messages.
        # A tool result must never be separated from its tool call.
        user_positions = [
            index
            for index, message in enumerate(self.history)
            if message["role"] == "user"
        ]

        if len(user_positions) > self.max_turns:
            cutoff = user_positions[-self.max_turns]
            self.history = self.history[cutoff:]

        return answer

    def close(self) -> None:
        """Discard conversation context when the session ends."""
        self.history.clear()
        self.closed = True
