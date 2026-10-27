# Deterministic intent routing

The `hoid ask "Turn on the desk lamp"` command interprets a small set of **whole-phrase** English requests. It is intentionally not a general natural-language understanding system.

## Supported requests

- `Turn on the desk lamp.` / `Turn the desk lamp on.`
- `Turn off the desk lamp.` / `Turn the desk lamp off.`
- `Is the desk lamp on?` / `What's the desk lamp status?`

Limited equivalent `switch` and `check` phrasings are also supported. Unknown, negated, combined, or ambiguous requests are rejected without any device operation (exit code 2). Adding supported phrases requires tests.

## Boundaries

`parse_intent(text)` returns an `Intent(device, action)` or `None`. It never accepts arbitrary device IDs or API service names.

`process_text(text, controller)` accepts text and a controller implementing `get_state`, `turn_on`, and `turn_off`. It returns a structured `Response(text, status)`. It does not depend on speech recognition, CLI argument parsing, or telephony.

The CLI loads private runtime configuration only after recognizing a supported intent, then delegates to the existing allowlisted Home Assistant client. The client enforces configured permissions and state verification. Errors remain explicit; an unverified action is never described as successful.

`hoid ask` **can control a real device** when a recognized action is supplied. For non-actuating validation, test with `hoid ask "Is the desk lamp on?"` or an unsupported phrase first. This milestone does not automatically connect `hoid transcribe` to `hoid ask`, and does not enable a microphone, SIP session, or LLM.

## Test

```sh
python -m pytest -q
hoid ask "Is the desk lamp on?"
hoid ask "Don't turn on the desk lamp"
```

No transcripts, recordings, credentials, or live entity mappings belong in this public repository.
