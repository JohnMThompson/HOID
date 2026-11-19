# HOID — Project Summary

> **Status (November 18, 2026):** HOID has a working, intentionally initiated telephone assistant on Pileated. A Cisco SPA303 registers with Asterisk; dialing the assistant extension (`2000`) starts a FastAGI session using local Whisper speech recognition, Home Assistant Assist for conversation and approved actions, and local Kokoro speech synthesis (Lewis voice). A Home Assistant timer can ring the office phone and play a prerecorded spoken notification. A general-question call and a 20-second timer/callback were successfully tested end to end. The standalone Python CLI and recorded-file workflows remain available. The latest reported Python test run passed **87 tests**.
>
> **Purpose:** Public overview of project direction, design principles, and verified milestones—not a deployment runbook or complete implementation specification. See [Architecture](architecture.md) for component boundaries and runtime details.

## 1. Project overview

**HOID** stands for **Home Office Interface Device**. It is a personal, local-first, personality-driven assistant for a home office, with potential expansion into a garage woodshop and other spaces.

The goal is not a generic always-listening smart speaker. HOID is deliberately contacted through a **physical SIP desk telephone**. It should answer questions, help with work and hobbies, interact with authorized home automation, and ring a phone for selected user-requested events.

The project takes playful inspiration from Hoid/Wit in Brandon Sanderson's Cosmere, but is an independent personal project, not an official or affiliated adaptation. Personality should enhance usefulness without becoming excessive roleplay.

The initial working implementation now includes a telephone voice session, local speech processing, Home Assistant Assist integration, and a timer callback. The original allowlisted Python Home Assistant client and recorded-file speech-to-action workflow remain separate development and diagnostic interfaces; they are **not** the live telephone orchestration path.

## 2. Experience and product vision

### Office: HOID

- The physical Cisco SPA303 SIP desk phone is the current office interface.
- The user dials assistant extension `2000` to start an intentional session; hanging up ends the call. Automatic off-hook dialing is a possible refinement, not a verified feature.
- HOID can respond to general questions and use actions exposed through Home Assistant Assist. Exact action availability depends on Home Assistant configuration.
- A user-created Home Assistant timer can ring the office phone and play a spoken notification after answer. The callback was tested successfully.
- The phone rings rather than speaking unsolicited into the room; the current timer callback uses prerecorded Kokoro speech.
- Text/web interfaces may be added later, but the telephone remains the defining experience.

### Workshop: WIT

A future second phone in the garage woodshop may use the name **WIT (Workshop Interface Technology)**. It would connect to the same underlying assistant, with endpoint-specific context, permissions, and tools determined when implemented.

- Likely workshop uses include measurements, conversions, woodworking notes, reminders, and safe environmental controls.
- A physical handset is attractive in a noisy, dusty workspace.
- HOID and WIT would be contextual identities, not separate AI personalities or model stacks.
- Never remotely activate hazardous machinery or power tools.

### Ordinary telephone functionality

Asterisk is independent of assistant inference. SIP registration and ordinary PBX routing must not require a working AI service. The office phone is currently extension `101`; the assistant is `2000`. A workshop extension has **not** been deployed or assigned as a final decision. Intercom and auto-answer are deferred.

## 3. Design principles

### 3.1 Automation is additive — foundational rule

**Automation must add capability without replacing or degrading intuitive physical/manual control.**

- Household members should be able to operate ordinary lighting without HOID, an app, or voice commands.
- Physical controls should remain discoverable and predictable.
- Prefer useful local fallback when Home Assistant, the network, or the assistant is unavailable.
- A smart-bulb/detached-mode switch is not inherently outage-proof: verify independent control or suitable local binding before assuming normal-switch behavior.
- Do not automate dangerous power tools.

### 3.2 Local-first, private by default

- Prefer on-premises speech, inference, and automation; keep SIP/PBX access on the home LAN rather than exposing telephony to the internet.
- Sessions are initiated deliberately by phone, not through ambient always-on listening.
- Allow household members and visitors with physical access to use initial low-risk capabilities without voice recognition, PINs, or personal accounts. Exclude sensitive actions and private household information from initial scope.
- **Design intent:** no persistent conversational memory, saved audio, or retained transcripts. Process speech for the active call and discard it afterward. Actual retention also depends on Asterisk, speech-service, Home Assistant, and logging configuration; verify these settings during operational reviews.
- Operational logs may retain non-content metadata such as component health, errors, and call timing. Avoid logging conversation content.
- Stable facts belong in configuration; live state belongs in authoritative systems. Timers and scheduled actions belong in Home Assistant or another persistent service, not LLM memory.
- Initial capabilities are low risk: general questions, calculations, lighting, and timers. Locks, garage doors, alarms, purchases, and other consequential actions remain out of scope.
- Fail safely: do not report unconfirmed success, silently substitute actions, or automatically retry potentially consequential commands after an uncertain timeout.
- Outbound calls should correspond to explicit timers, alarms, reminders, or configured events—not unsolicited proactive check-ins.

### 3.3 Modular and model-independent

- Keep telephony, speech recognition, conversation orchestration, inference, and home automation responsibilities separate.
- Avoid unnecessary coupling to one LLM, speech engine, or accelerator.
- Integrations are controlled interfaces, not unrestricted execution privileges.
- Prefer small, reliable, maintainable increments over maximal features.

### 3.4 Character serves usefulness

- Shared personality: dry, witty, mischievous, insightful, and warm when appropriate.
- Routine commands should get short, direct responses.
- Humor and lore references should be occasional, not constant.
- HOID and future WIT are contextual names for the same underlying character.

## 4. Deployed architecture

```text
Cisco SPA303 SIP phone (extension 101)
             |
             v
Asterisk PBX (separate Docker service on Pileated)
             |
             | call assistant extension 2000
             v
FastAGI Assist service (Python, port 4574)
     |           |               |
     v           v               v
Whisper STT   Assist bridge   Kokoro TTS (Lewis)
                 |
                 v
        Home Assistant Assist
                 |
         +-------+-------+
         |               |
    Exposed HA       Local LLM via
    actions/scripts  Ollama integration
         |
    Home Assistant devices and automations
```

The FastAGI session records an utterance, transcribes it locally, sends text and conversation context to Home Assistant Assist, synthesizes the returned response locally, and plays it through Asterisk. The deployed flow is turn-based, not a verified streaming/barge-in system. Home Assistant Assist determines which exposed actions are available; it does **not** use the standalone CLI's device allowlist.

**Timer callback path:** Home Assistant Assist invokes a configured timer script → Home Assistant timer completes → automation creates an Asterisk call file → Asterisk rings office extension `101` → the answered call plays one of ten prerecorded Lewis announcements. This has been tested with a 20-second timer.

| Component | Verified role / current status |
| --- | --- |
| Cisco SPA303 | Registered SIP desk phone; handset/speakerphone and ringing used for assistant calls |
| Asterisk | Deployed independently in Docker; handles SIP registration, dialplan, FastAGI invocation, and outbound callback calls |
| HOID FastAGI Assist | Active Python systemd service; connects telephony audio, local STT/TTS, and Home Assistant Assist |
| Whisper / Kokoro | Local speech-to-text and text-to-speech in the telephone workflow; Kokoro uses Lewis voice |
| Home Assistant Assist | Conversation and exposed home-action orchestration; uses configured Ollama integration for LLM reasoning |
| Home Assistant | Deployed device/automation layer; first desk-lamp outlet physically verified; owns current timer lifecycle |
| Standalone Python CLI | Separate allowlisted HA client, deterministic intent routing, recorded-file transcription, and speech testing |

The former direct Ollama conversation implementation and custom scheduler services were retired. A legacy FastAGI service/extension was also disabled and removed from the active dialplan. Shared FastAGI support code remains in use by the active Assist service. See [Architecture](architecture.md) for details.

## 5. Hosting and homelab integration

**Host:** Pileated, an always-on private Ubuntu Server machine.

- Asterisk runs in its own Docker/Compose deployment, separate from the HOID Python application.
- The active FastAGI Assist service is managed by systemd on the host.
- Home Assistant runs separately and is the authority for exposed smart-home actions, scripts, and timers.
- Local Whisper, Kokoro, and Ollama components are part of the speech/inference path; measure real-world latency and resource use before expanding functionality.
- PBX independence matters: assistant failures should not disable ordinary telephone routing.
- A Pileated outage also affects services hosted there; that is an acceptable initial tradeoff for this convenience-oriented project.

Deployment paths, credentials, host-specific device identifiers, and infrastructure configuration belong in the private [homelab repository](https://github.com/JohnMThompson/homelab), not in this public HOID repository. This summary deliberately omits private runtime configuration.

## 6. Telephony hardware and network

### Office phone

The Cisco SPA303 is installed, powered, and registered with Asterisk as extension `101`. Dialing `2000` reaches the working assistant. An incoming timer callback successfully rang the phone and played an announcement. An off-hook hotline/auto-dial experience is **not** yet established; ordinary dialing is the verified interaction.

### Workshop phone

No WIT phone or garage connection has been deployed. Options to investigate later include a Wi-Fi-to-Ethernet bridge for a SIP phone, a Wi-Fi-capable SIP phone, or wired Ethernet. Evaluate garage Wi-Fi stability, dust, seasonal temperature, and handset usability before selecting equipment.

### Future call behavior

- Maintain direct PBX extension routing independently of the assistant.
- Consider an easier assistant dialing experience without preventing ordinary extension calls.
- Defer intercom, auto-answer, multiple endpoints, and sophisticated call interruption until justified by use.
- Keep assistant-originated calls tied to deliberate, identifiable events.

## 7. Smart-home scope and candidates

### Initial physical scope

Home office and its en-suite bathroom, with potential later expansion to the basement and garage.

### Office lighting

**First verified device (October 19, 2026):** a Wi-Fi smart outlet powers the desk lamp. Home Assistant UI and authenticated REST API commands physically switched the lamp on and off. The standalone HOID CLI subsequently verified lamp control and spoken confirmation in a recorded-file workflow. The telephone assistant now accesses approved smart-home functionality through **Home Assistant Assist**, which has its own exposed-action configuration.

Existing office lighting described during planning:

- Four recessed overhead lights on one wall switch.
- One floor lamp and one desk lamp.
- Neutral and ground reportedly available at house switches.

Desired future behavior includes brightness, color temperature, and possibly color control, while preserving useful manual switching. Earlier exploration considered Hue White & Color Ambiance BR30/A19 bulbs, a Hue Bridge, and suitable physical wall controls. These are **candidates, not purchases or final architecture decisions**; verify fixture compatibility and fallback behavior first.

### Bathroom and other possibilities

A conventional smart dimmer with compatible LED bulbs may be simpler for the bathroom; presence-aware nighttime lighting remains exploratory. Other optional additions include mmWave presence sensing, environmental sensors, safe smart plugs, and motorized blinds. Avoid buying a large device ecosystem before demonstrating concrete value.

## 8. Functional capabilities

### Verified

- Dial the office assistant extension and converse through a physical SIP phone.
- Ask a general question and receive a locally synthesized spoken answer through the telephone.
- Request a timer through Home Assistant Assist; have the office phone ring when it finishes and play a prerecorded spoken notification.
- Control the first desk-lamp outlet through Home Assistant and the standalone allowlisted Python CLI; recorded-file voice-to-action-to-speech was also validated.
- Run local Whisper transcription and Kokoro (Lewis) synthesis for telephone and CLI workflows.

### Potential next improvements

- Better turn-taking, latency measurement, interruption handling, and conversational reliability.
- More exposed low-risk Home Assistant capabilities with deliberate scope review.
- Better call failure behavior, observability, and operational recovery checks.
- More convenient dialing behavior on the office phone.
- Additional timer/reminder lifecycle features where Home Assistant supports them.

### Later possibilities, not committed

- Workshop WIT endpoint and context.
- Direct office-to-workshop calls, then optional intercom behavior.
- Web/text interface, additional rooms and devices, and carefully selected notifications.
- Persistent conversational memory remains **unplanned** unless a specific use case justifies revisiting the decision.

## 9. Current direction and open decisions

### Established

- HOID is local-first and voice-first, without ambient always-on listening.
- The physical office SIP phone and Asterisk PBX are deployed and operational.
- Assistant calls use FastAGI, local STT/TTS, Home Assistant Assist, and its configured Ollama integration.
- Home Assistant owns the current timer and outbound callback automation.
- Home Assistant is the smart-device authority; the CLI's allowlisted client is a separate tool, not the telephone action authorization path.
- Ordinary telephone behavior remains separate from AI service availability.
- Automation is additive, and sensitive or hazardous actions are outside initial scope.
- No persistent conversation memory or content retention is intended; configuration and logs should be audited to ensure the deployed system matches that policy.
- WIT remains a future extension, not a second deployed endpoint.

### Open / deferred

- Measure and improve full call latency and interruption behavior.
- Confirm operational retention settings across the complete call and Assist stack.
- Review production logging, monitoring, backup/recovery, and failure paths.
- Decide whether to configure automatic assistant dialing when lifting the handset.
- Determine WIT connectivity, equipment, and endpoint-specific permissions if pursued.
- Validate any additional lighting equipment and independent manual controls before purchase.
- Define boundaries for any future web-assisted research capability or sensitive household information.

## 10. Milestones and progress

| Milestone | Status |
| --- | --- |
| Document vision and privacy/safety principles | Established; living documentation |
| Home Assistant and physical desk-lamp control | **Verified October 19, 2026** |
| Standalone CLI, recorded-file Whisper → action → Kokoro response | **Verified October 26, 2026** |
| SIP phone registration and Asterisk assistant call routing | **Verified** |
| Live telephone Assist conversation using local STT/TTS | **Verified** |
| Home Assistant timer and Asterisk phone callback | **Verified** with a 20-second timer |
| Legacy scheduler/direct conversation cleanup | **Completed** on current feature branch |
| Reliability, documentation, and integration refinement | **In progress** |
| WIT workshop endpoint | **Deferred** |

Latest reported automated test result after cleanup: **87 passed**. This is not a claim that all operational error paths or privacy settings have been tested.

## 11. Guidance for future AI coding agents

- **Read this summary and [Architecture](architecture.md) before proposing changes.** Inspect current code and deployment configuration before claiming a behavior is implemented.
- Distinguish **verified**, **implemented but not fully tested**, **proposed**, and **deferred**.
- Do not reintroduce the retired custom scheduler or direct Ollama conversation engine without a specific architectural decision.
- Do not confuse the CLI allowlist with Home Assistant Assist's exposed entities/actions.
- Preserve **Automation is additive**, local privacy boundaries, and independent PBX operation.
- Do not commit credentials, private entity mappings, household topology, or runtime configuration to the public repository; follow [AGENTS.md](../AGENTS.md).
- Ask before enabling remote access, making purchases, implementing sensitive actions, or automating hazardous devices.
- Prefer small, testable changes, and record architectural decisions with rationale.
- Update this document when material decisions change without silently rewriting the original project intent.

---

*Originally drafted October 8, 2026. Updated November 18, 2026 to distinguish the deployed telephone assistant and Home Assistant timer callbacks from the earlier CLI prototype and future plans.*
