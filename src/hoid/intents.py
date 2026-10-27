"""Conservative, deterministic interpretation of a few approved lamp requests.

Only entire recognized phrases are accepted; arbitrary natural language is not
translated into Home Assistant API calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    device: str
    action: str


# Keep this deliberately narrow. Unsupported, negated, or ambiguous requests
# must not trigger an action. Expand patterns only with explicit tests.
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:turn|switch) (?:the )?desk lamp on|turn on (?:the )?desk lamp|switch on (?:the )?desk lamp"), "turn_on"),
    (re.compile(r"(?:turn|switch) (?:the )?desk lamp off|turn off (?:the )?desk lamp|switch off (?:the )?desk lamp"), "turn_off"),
    (re.compile(r"(?:is (?:the )?desk lamp (?:on|off)|what(?: is|'s) (?:the )?desk lamp(?:'s)? (?:status|state)|(?:check|get) (?:the )?desk lamp (?:status|state))\??"), "get_state"),
)


def parse_intent(text: str) -> Intent | None:
    """Return an allowlisted intent, or None; never infer from a substring."""
    normalized = re.sub(r"\s+", " ", text.strip().lower()).rstrip(".!").strip()
    for pattern, action in _PATTERNS:
        if pattern.fullmatch(normalized):
            return Intent(device="desk_lamp", action=action)
    return None
