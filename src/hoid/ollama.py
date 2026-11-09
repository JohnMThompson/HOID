"""Local Ollama API client for HOID."""

from __future__ import annotations

import httpx


class OllamaError(Exception):
    """The local language model could not complete a request."""


class OllamaClient:
    """Minimal client for local conversational inference."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:3b",
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Request one conversational turn from Ollama."""

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        if tools is not None:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(
                "Local language model request failed."
            ) from exc

        message = result.get("message")

        if not isinstance(message, dict):
            raise OllamaError(
                "Local language model returned an invalid response."
            )

        return message
