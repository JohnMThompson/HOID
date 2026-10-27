# HOID architecture — interface-agnostic, voice-first

**Status: October 26, 2026.** This is an architectural direction and an inventory of verified code, not a claim that a voice assistant is already deployed. See [project summary](project-summary.md) for product principles and [Home Assistant integration](home-assistant-integration.md) for the verified device-control boundary.

## Guiding principle

**Voice is how HOID is meant to be experienced, not a dependency of how HOID works.**

HOID is **interface-agnostic by architecture and voice-first by experience**. Its core should accept normalized requests and return structured outcomes without depending on SIP, a microphone, speech engines, or a particular user interface. The preferred user experience is an intentional, responsive spoken conversation using a desk telephone. Typed commands and recorded audio are equally valid development and diagnostic inputs.

Voice-first does **not** mean always listening. Sessions are deliberate, with no default ambient microphone monitoring or persistent audio, transcript, or conversational-memory storage.

## Conceptual flow (target, not yet implemented)

```text
SIP phone -> Asterisk -----------+
Microphone / recorded audio -----+--> input adapters --> normalized request
CLI / text ----------------------+                           |
                                                            v
                                                  HOID request processor
                                               deterministic intent routing
                                               optional local LLM fallback
                                                            |
                                                   approved tools / APIs
                                                            |
                                                     Home Assistant
                                                            |
                                                   structured outcome
                                                            |
                                      +---------------------+------------------+
                                      |                                        |
                                  text / CLI                         local TTS -> audio
                                                                        |
                                                               phone / speaker
```

Asterisk owns SIP registration, calls, and media transport, not assistant reasoning. An eventual Asterisk-to-HOID audio adapter may use ARI and External Media, but that mechanism is **not selected or tested**. Ordinary telephone calling should continue without HOID.

Audio adapters will normalize media for speech recognition. A working assumption for the future STT boundary is mono 16-bit PCM at 16 kHz; this is a proposed internal format, not a deployed contract. Telephone audio may require decoding and resampling. Speech synthesis output likewise requires conversion for its destination. Neither conversion belongs in the assistant core.

## Responsibilities and boundaries

| Component | Responsibility | Implementation status |
| --- | --- | --- |
| Input adapters | Accept CLI text, audio files, microphones, or telephone media; normalize requests | CLI argument parsing exists; audio and SIP adapters planned |
| STT | Convert audio to text locally, independent of source | Planned; engine not selected or benchmarked |
| Request processor | Interpret normalized text, route known intents, manage outcomes | Planned; no natural-language intent router yet |
| Approved tools | Enforce permitted actions and execute against external services | Home Assistant allowlisted client implemented |
| LLM fallback | Handle requests outside deterministic patterns using constrained tools | Planned; no model integration yet |
| TTS | Turn response text into local speech | Planned; Kokoro/Lewis is a preferred candidate, not validated |
| Output adapters | Render structured outcomes as CLI text or destination-specific audio | CLI prints messages; spoken output planned |
| Session manager | Control conversational turn-taking, timeouts, and hangup cleanup | Planned |
| Asterisk | Independent PBX and SIP/RTP transport | Separate `homelab-asterisk` deployment; telephone registration/audio not yet validated |

## Current code review (October 26, 2026)

- `src/hoid/cli.py` parses the fixed commands `hoid lamp status|on|off`, maps them to `get_state`, `turn_on`, or `turn_off`, calls `HomeAssistantClient`, and prints a message. **It is not a natural-language interface or reusable request processor yet.**
- `src/hoid/client.py` implements the approved Home Assistant operations. It checks configured device/action permissions, handles API errors, and verifies reported state after state-changing commands. **Preserve this boundary.**
- `src/hoid/config.py` loads private runtime configuration and a secret supplied through an environment variable or token file. It validates device names, switch entity IDs, and permitted actions.
- `pyproject.toml` defines a Python 3.12+ package, the `hoid` CLI entry point, and pytest as a development dependency.
- The one-shot Docker CLI and physical lamp control have been manually verified. There is **no always-running HOID service, STT, TTS, voice gateway, or LLM integration**. The README reports 20 earlier passing mocked tests and four additional tests whose rerun has not been reported.

### Refactoring guidance

Do not make speech recognition call `cli.main()` or manufacture command-line arguments. When we implement natural-language routing, introduce a small callable request-processing boundary that can be used by the CLI, audio-file prototype, and future telephone adapter. Reuse `HomeAssistantClient` and its existing allowlist and verification logic rather than creating a second Home Assistant control path.

A **proposed**, not yet implemented, interface could resemble:

```python
request = {
    "text": "Turn on the desk lamp",
    "session_id": "ephemeral-session-id",
    "source": "audio_file",
}
response = {
    "text": "The desk lamp is on.",
    "status": "verified",
}
```

The `source` and session information are metadata for authorization, routing, and response presentation; device-specific behavior must not leak into tool execution. These dictionaries are illustrative, not stable Python types or a published API. A response must distinguish verified success, failure, and uncertain outcomes. A transcription is untrusted input; it cannot authorize arbitrary device identifiers or actions.

## Privacy, safety, and failure behavior

- No default audio recording, transcript retention, or persistent conversational memory. Dispose of session media and text when the session ends.
- Only approved, low-risk device actions. Do not grant an LLM unrestricted Home Assistant access.
- Do not infer permissions solely from a claimed input source; source metadata is not authentication.
- Preserve ordinary physical/manual controls and independent PBX functionality.
- If STT, TTS, LLM, or Home Assistant fails, return an explicit failure or uncertain outcome; never invent a successful action or silently substitute another device.
- Keep credentials, household topology, and real entity IDs out of this public repository. See [AGENTS.md](../AGENTS.md).

## Next implementation milestone: audio-file STT

1. Define a small, replaceable speech-to-text adapter accepting a local audio file and returning text or an explicit error.
2. Test transcription on a synthetic or locally recorded command without any telephone dependency.
3. Measure CPU latency and recognition accuracy on the intended host before committing to an engine/model.
4. **Only after STT works independently**, connect its output to a deterministic natural-language request processor that reuses the existing allowlisted Home Assistant client.
5. Add local TTS and later the Asterisk media adapter as independently testable components.

The telephone and audio-file workstreams can progress independently and converge at the adapter boundary. No speech or phone integration is implemented by this document.
