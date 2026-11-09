"""Independent authorization checks for proposed HOID actions."""

import re


class ActionNotAuthorized(Exception):
    """A proposed action lacks sufficient user authorization."""


_TIMER_REQUEST = re.compile(
    r"\b("
    r"(?:set|start|begin|create|run)\s+(?:a\s+)?timer"
    r"|(?:ring|call|remind|notify|alert|buzz)\s+me\b"
    r"|(?:give\s+me|wait)\s+.+\s+(?:before|then)\s+"
    r"(?:ringing|calling|reminding|notifying|alerting|buzzing|ring|call|remind|notify|alert|buzz)"
    r")",
    re.IGNORECASE,
)

_DURATION = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"fifteen|twenty|thirty|forty|forty-five|sixty|half)\b"
    r".{0,25}\b(?:seconds?|minutes?|hours?)\b",
    re.IGNORECASE,
)


def authorize_action(
    user_text: str,
    tool_name: str,
) -> None:
    """Reject tool execution without recognizable user authorization."""

    if tool_name != "start_timer":
        raise ActionNotAuthorized(
            f"No authorization policy exists for {tool_name!r}."
        )

    if not isinstance(user_text, str):
        raise ActionNotAuthorized("Invalid user request.")

    if not _TIMER_REQUEST.search(user_text):
        raise ActionNotAuthorized(
            "The user did not explicitly request a timer or callback."
        )

    if not _DURATION.search(user_text):
        raise ActionNotAuthorized(
            "The timer request does not contain a recognizable duration."
        )
