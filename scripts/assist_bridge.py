"""Experimental Home Assistant Assist conversation bridge."""

import json
import os
import urllib.request
from pathlib import Path

AGENT_ID = "conversation.hoid_experimental"
HA_URL = "http://127.0.0.1:8123"


def get_token():
    token_file = os.environ.get("HOID_HA_TOKEN_FILE")

    if token_file:
        return Path(token_file).read_text().strip()

    token = os.environ.get("HOID_HA_TOKEN")

    if token:
        return token

    raise RuntimeError("Home Assistant token is not configured")


def converse(text, conversation_id=None):
    payload = {
        "agent_id": AGENT_ID,
        "text": text,
        "language": "en",
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    request = urllib.request.Request(
        f"{HA_URL}/api/conversation/process",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)

    speech = (
        result.get("response", {})
        .get("speech", {})
        .get("plain", {})
        .get("speech", "")
    )

    return speech, result.get("conversation_id")
