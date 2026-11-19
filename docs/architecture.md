# HOID architecture — deployed telephone assistant

**Status: November 18, 2026.** The telephone-to-Home Assistant Assist workflow and timer callback have been tested successfully on Pileated. This document distinguishes the deployed system from legacy test interfaces and future plans. For product goals and constraints, see [project summary](project-summary.md); for the standalone Home Assistant client, see [Home Assistant integration](home-assistant-integration.md).

## Guiding principles

**Voice is how HOID is experienced, not a requirement for every HOID utility.** HOID is local-first and voice-first, initiated deliberately from a physical SIP telephone rather than an always-listening microphone. The CLI and recorded-audio commands remain useful for development and diagnostics, but they are distinct from the deployed telephone conversation path.

The PBX, Home Assistant, and speech components have separate responsibilities. Ordinary telephony and manual smart-home controls should not depend on the assistant being available. Audio and conversational content should be ephemeral; persistent recording, transcript retention, and conversational memory are not design goals.

## Deployed telephone conversation path

```text
Cisco SPA303 (SIP extension 101)
             |
             v
Asterisk PBX (Docker; extension 2000)
             |
             | AGI(agi://127.0.0.1:4574/assist)
             v
HOID FastAGI Assist (systemd: hoid-fastagi-assist.service)
  scripts/fastagi_assist.py
  shared telephone/AGI functionality: scripts/fastagi.py
             |
             +--> local speech-to-text (Whisper) --> transcript
             |                                      |
             |                                      v
             |                          scripts/assist_bridge.py
             |                                      |
             |                                      v
             |                         Home Assistant Assist
             |                           |              |
             |                           |              +--> exposed Home Assistant actions
             |                           v
             |                         Ollama (local LLM)
             |                                      |
             +<------------- spoken response text <-+
             |
             +--> Kokoro TTS (Lewis voice) --> Asterisk --> SIP phone
```

The diagram represents component responsibilities and the general request/response flow, not a packet-level sequence. Home Assistant Assist is the conversational orchestration boundary. HOID handles telephone media, local transcription, and speech synthesis; it does **not** run a second, direct Ollama conversation engine for the live phone workflow.

The Assist handler imports shared functionality from `scripts/fastagi.py`. **Do not delete `scripts/fastagi.py` simply because its original standalone service has been retired.**

## Timer creation and completion

Timer requests travel through the same telephone and Assist path. Home Assistant owns the timer lifecycle rather than a HOID-specific scheduler.

```text
Spoken timer request
    -> HOID STT -> Home Assistant Assist
    -> script.hoid_start_timer (seconds)
    -> timer.hoid_office
    -> Home Assistant timer.finished automation
    -> Home Assistant shell command creates an Asterisk .call file
    -> Asterisk originates call to PJSIP/101
    -> extension 203 plays a randomly selected prerecorded timer message
    -> hangup
```

The timer script accepts a duration in seconds (configured range: 1–86,400). Asterisk's callback extension `203` selects one of ten pre-generated Kokoro/Lewis announcements (`timers-01` through `timers-10`). The telephone rings for the callback; HOID does not speak unsolicited audio into the room. A spoken timer request and subsequent callback were verified after the legacy FastAGI cleanup on November 18, 2026.

The callback depends on Home Assistant's timer and automation state and on Asterisk being available when the timer finishes. Do not describe this as an independent HOID scheduler or assume delivery guarantees that have not been tested.

## Components and operational boundaries

| Component | Responsibility | Verified/current state |
| --- | --- | --- |
| Cisco SPA303 | Physical handset/speakerphone and SIP endpoint | Registered as extension `101`; live assistant call and callback verified |
| Asterisk (`homelab-asterisk`) | SIP registration, dialplan, AGI routing, outbound callback | Extension `2000` routes to Assist on port `4574`; extension `203` handles timer playback |
| `hoid-fastagi-assist.service` | Live telephone conversation handler | Running and enabled at boot |
| `scripts/fastagi_assist.py` | Telephone interaction, STT and TTS coordination | Active Assist handler |
| `scripts/fastagi.py` | Shared FastAGI/telephone implementation and legacy standalone entry point | Shared code retained; original `hoid-fastagi.service` stopped and disabled |
| `scripts/assist_bridge.py` | Exchange conversation text and conversation identifier with Home Assistant Assist | Used by active Assist handler |
| `src/hoid/stt.py` | Local speech recognition | Used by active Assist handler |
| `src/hoid/tts.py` | Local speech synthesis | Used by active Assist handler; Kokoro/Lewis voice |
| Home Assistant Assist | Conversation orchestration and access to exposed actions | Used for live questions, device control, and timer requests |
| Ollama | Local LLM behind the Assist conversation integration | Used through Home Assistant, not called directly by the live HOID handler |
| Home Assistant timer/automation | Persist timer state and initiate completion notification | Timer callback tested |

**Deployment ownership:** Asterisk and Home Assistant are separate homelab services. Their live configuration, secrets, and operational backups belong to the homelab infrastructure, not this application repository. See the [homelab Home Assistant documentation](https://github.com/JohnMThompson/homelab/blob/main/infrastructure/home-assistant.md).

## Other interfaces and retired components

The `hoid` CLI and recorded-file utilities are still useful for independently exercising Home Assistant client operations, deterministic intent routing, STT, and TTS. They should **not** be mistaken for the active telephone conversation architecture; in particular, their deterministic routing and allowlisted Python client are separate from Home Assistant Assist's live conversation/action path.

The following legacy telephone and scheduling paths have been retired:

- `hoid-fastagi.service` on port `4573`: stopped and disabled; its former Asterisk extension `202` was removed.
- The earlier HOID-specific scheduler services and direct Ollama conversation implementation: removed from the active application architecture.

Asterisk still contains some historical test extensions (`100`, `200`, `201`), which are not part of the live Assist workflow. Do not treat those test extensions as production assistant endpoints.

## Home Assistant-first automation principle

**Prefer native Home Assistant capabilities before building custom HOID tools or services.** HOID provides conversational and telephone access to household capabilities; it should not duplicate Home Assistant's automation platform.

Evaluate new capabilities in this order:

1. **Native Home Assistant:** Use an existing integration, entity, helper, or script.
2. **Home Assistant orchestration:** Combine capabilities using automations and events.
3. **Small HOID integration:** Implement only the missing interface, such as an Asterisk telephone callback.
4. **Custom HOID subsystem:** Build a separate service only when the existing platform cannot reasonably meet the requirement.

Home Assistant owns household device state, timers, and automations wherever practical. HOID owns telephone interaction, speech processing, and the integration boundaries needed to communicate with Home Assistant.

The deployed timer implementation demonstrates this principle: Home Assistant manages the countdown and completion event; Asterisk handles the resulting telephone notification. No independent HOID scheduler is required.

See [ADR 001 — Home Assistant timers](adr/001-home-assistant-timers.md) for the recorded decision.

## Privacy, safety, and failure behavior

- Sessions are user-initiated by telephone; no ambient always-listening mode is intended.
- Do not deliberately retain audio, transcripts, or persistent conversation history. Confirm actual runtime logging and retention settings before making a stronger privacy guarantee.
- Treat transcribed speech and model output as untrusted. Expose only appropriate Home Assistant entities and actions to Assist; do not grant broad control simply because a request arrived through the phone.
- Exclude high-risk actions such as locks, garage doors, security systems, and purchases from the initial scope.
- Never log or commit access tokens, SIP credentials, household topology, or private entity identifiers. Follow [AGENTS.md](../AGENTS.md).
- Distinguish verified success, failure, and uncertain outcomes. If speech recognition, Assist, the LLM, Home Assistant, or speech synthesis fails, do not claim an action succeeded without evidence.
- Preserve physical/manual device controls and PBX functions independently of the assistant where possible.

## Verified capabilities and future work

**Verified as of November 18, 2026:** a live call to extension `2000` completed successfully after retirement of the original FastAGI service; the user confirmed the telephone conversation and a spoken timer request with a subsequent ringing callback. Earlier CLI, STT, TTS, and lamp-control milestones were separately verified during development.

**Future work / not established by this document:** interruption or barge-in support, multi-phone/WIT operation, richer reminder and alarm behavior, comprehensive recovery and delivery guarantees, and security/privacy auditing of every runtime log or retained artifact. Do not present these as already deployed.
