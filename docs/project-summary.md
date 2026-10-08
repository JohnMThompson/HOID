# HOID — Project Summary

> **Status:** Planning and architectural exploration. No implementation has begun.
> **Purpose:** Public overview of the project direction and planning status. This is a living summary, **not** a complete implementation specification.

## 1. Project overview

**HOID** stands for **Home Office Interface Device**. It is a personal, local-first, personality-driven AI assistant for a home office, with potential expansion into a garage woodshop and other spaces.

The goal is not to recreate a generic always-listening smart speaker. HOID should feel like a distinct, useful presence that can be **called on a physical desk telephone**. It should answer questions, assist with work and hobbies, interact with home automation through controlled interfaces, and initiate phone calls for selected reminders or notifications.

The project takes playful inspiration from Hoid/Wit in Brandon Sanderson's Cosmere, but it is an independent personal project, not an official or affiliated adaptation. The acronym and practical functionality should make sense without knowing the reference. Personality is a subtle layer over a reliable assistant, not an excuse for excessive roleplay.

The project remains in the planning and documentation phase. No application or infrastructure implementation has begun. Keep candidate technologies and hardware distinct from established direction.

## 2. Experience and product vision

### Office: HOID

- A physical SIP desk phone in the home office is the defining voice interface.
- A call to the assistant starts an intentional session; the exact off-hook dialing behavior remains to be validated with phone hardware.
- Hanging up ends the voice session.
- HOID can answer questions, assist with productivity and research, and control authorized smart-home devices.
- HOID may place an **incoming call to the office phone** for selected reminders, timers, or events. The phone rings; the assistant does **not** spontaneously speak into the room.
- Text/web interfaces may be added, but the telephone interaction is the defining experience.

### Workshop: WIT

A future, secondary workshop effort may add a second phone in the garage woodshop. It would reach the **same underlying system**, with the endpoint name **WIT (Workshop Interface Technology)**.

- WIT is intended to share the underlying orchestration and personality foundation with HOID. Endpoint-specific context, tools, and permissions will be defined when WIT becomes active; persistent conversational memory is not part of the initial architecture.
- Workshop context emphasizes measurements, conversions, woodworking project notes, reminders, and safe shop environmental controls.
- The persona may have context-sensitive greetings and behavior, but HOID and WIT are **not separate AI personalities or model stacks**.
- The workshop is noisy and dusty; a physical handset is attractive for voice interaction.
- Never remotely activate hazardous machinery or power tools.

### Ordinary telephone functionality

The phones must also work as ordinary internal extensions **without involving AI**:

| Proposed extension | Endpoint |
| --- | --- |
| `100` | AI assistant |
| `101` | Office phone (HOID) |
| `102` | Workshop phone (WIT) |

These numbers are illustrative, not final configuration. Ordinary extension calls should be routed by the PBX independently of the assistant. The first assistant experience targets one SIP phone; intercom and auto-answer are outside initial scope and deferred until multi-phone deployment.

## 3. Design principles

### 3.1 Automation is additive — foundational rule

**Automation must add capability without replacing or degrading intuitive physical/manual control.**

- Anyone in the household should be able to operate ordinary lighting without using an AI assistant, app, or voice command.
- Physical controls should remain discoverable and predictable.
- Prefer reasonable local fallback when Home Assistant, the network, or the assistant is unavailable.
- A smart-bulb/detached-mode switch is **not automatically outage-proof**: verify direct Zigbee binding, local fallback, or another independent control path before treating it as equivalent to a normal switch.
- Do not automate dangerous power tools.

### 3.2 Local-first, private by default

- Prefer on-premises operation and local communication.
- Keep SIP/PBX access on the home LAN; do not expose telephony ports to the public internet by default.
- Design for deliberate, opt-in voice sessions rather than ambient always-on listening.
- Allow household members and visitors with physical access to a HOID phone to use initial low-risk capabilities without accounts, PINs, voice recognition, or speaker identification. Sensitive actions and private household information are outside initial scope.
- Initial architecture has no persistent conversational memory, audio recordings, or transcript retention: process content in memory for the active session and discard it at hangup. Do not log conversational content or enable Asterisk recording/voicemail or independent speech-service retention by default.
- Operational logs may contain non-content metadata such as errors, component health, call duration, and performance metrics.
- Use static configuration for stable assistant/endpoint facts and query authoritative services for live state. Delegate reminders, timers, and scheduled actions to appropriate persistent services rather than conversational memory.
- Recording or transcript retention is not planned; reconsider only if a specific use case justifies revisiting the decision.
- Initial low-risk capabilities may include lighting control, general questions, calculations, timers, and basic reminders. Exclude locks, garage doors, alarms, purchases, and private household information.
- Fail safely when a capability is unavailable: communicate clearly, never claim an unconfirmed outcome, avoid unauthorized substitutions or deferred execution, and keep unrelated capabilities available. Treat timed-out action outcomes as uncertain and avoid automatic retries for potentially consequential or non-idempotent actions.
- Outbound calls are explicitly opt-in for user-created timers, alarms, reminders, or deliberately configured events. Each has a clear source and destination (defaulting to the originating phone), rings normally until answered, and does not force speakerphone. Do not initiate proactive check-ins, duplicate calls, or automatic rerouting; detailed ringing and scheduling behavior remains to be prototyped.

### 3.3 Modular and model-independent

- The HOID application should not be tightly coupled to one LLM, speech engine, or hardware accelerator.
- Keep telephony, speech, orchestration, inference, and home automation responsibilities separate.
- Treat integrations as controlled interfaces, not unrestricted execution privileges.
- Start small; prioritize low latency, reliability, and maintainability over maximal features.

### 3.4 Character serves usefulness

- Shared personality: dry, witty, mischievous, insightful, warm when appropriate.
- Routine commands should receive short, direct responses.
- Humor and lore references should be occasional rewards, not constant interruptions.
- HOID and WIT are contextual names for the same underlying character.

## 4. Conceptual architecture

```text
Office SIP phone (HOID / ext. 101) ──┐
                                    ├── Local LAN ── Candidate PBX (Asterisk preferred)
Future garage SIP phone (WIT / ext. 102) ─┘                    │
                                                        ├── Direct extension-to-extension calls
                                                        │   (no AI required)
                                                        └── Assistant call endpoint
                                                                  │
                                                            HOID orchestrator
                                                             /     |      \
                                                           STT    LLM     TTS
                                                                  │
                                                         Controlled tools/APIs
                                                                  │
                                                           Home Assistant
                                                                  │
                                                          Smart-home devices
```

**Responsibility boundaries:**

| Component | Responsibility | Current status |
| --- | --- | --- |
| SIP phone | Physical calling, handset/speakerphone, ringing | One phone is in initial scope; model not selected or purchased |
| PBX | SIP registration, call routing, RTP/media, internal extensions | Asterisk is preferred; selection and deployment not validated |
| HOID orchestrator | Session management, persona/context, tool routing, notifications, memory policy | Conceptual |
| STT / TTS | Speech recognition and synthesis | Local processing selected as direction; engines and voice deferred to prototyping |
| Local LLM | Conversational reasoning | Ollama selected as initial runtime; model and compute capacity remain to be validated |
| Home Assistant | Source of truth and abstraction for smart devices/automation | Intended integration |

Asterisk is the preferred PBX candidate, pending validation in a working phone prototype. Keep the PBX independent from HOID orchestration so ordinary SIP routing remains available if the assistant fails. The SIP/RTP bridge mechanism is deferred until prototyping establishes a working bidirectional audio path to a simple test application and local STT/TTS. ARI and External Media are possibilities to evaluate, not selected mechanisms. The prototype should measure end-to-end latency and assess interruption support; advanced streaming/barge-in is not required at first.

## 5. Hosting and homelab integration

**Preferred host:** `pileated`, the existing always-on Ubuntu Server homelab machine, using Docker Compose.

- Run Asterisk in its **own Compose project**, separate from the HOID application.
- Docker host networking is a reasonable starting candidate for SIP/RTP on Linux, to reduce NAT/port-mapping complexity; validate security and compatibility during implementation.
- SIP signaling commonly uses UDP 5060, and RTP commonly uses a configurable UDP range (often 10000–20000). These are **examples, not finalized port allocations**.
- Persist Asterisk configuration and relevant state/logs using mounted volumes.
- Asterisk's resource needs for a few internal extensions should be modest; **local model inference is likely to dominate compute requirements**.
- The Raspberry Pi (`nuthatch`) is an alternative host or possible future fallback, but is **not preferred** for the initial PBX deployment.
- If `pileated` is down, its hosted PBX and internal calls are down; that availability tradeoff is acceptable for this convenience-oriented system initially.

Potential future directory layout (illustrative only):

```text
/opt/homelab/
  asterisk/
  hoid/
  homeassistant/
```

Do not assume all these services are already installed or that the eventual inference stack can run acceptably on current hardware.

## 6. Telephony hardware and network

### Office phone

One potential candidate is the **Cisco CP-8841-3PC-K9** with 3PCC/MPP third-party SIP firmware. No phone has been purchased, and the eventual model may differ. Defer model selection and provisioning/dialing validation until hardware is in hand.

### Workshop phone

A second SIP desk phone is a possible later WIT effort. The garage currently lacks a dedicated Ethernet/coax connection. Connectivity options have not been selected and are deferred until that effort begins. Possibilities include:

1. A **Wi-Fi-to-Ethernet client bridge** connected to an Ethernet-only SIP phone, with separate compatible power or PoE injection as needed.
2. A SIP desk phone with built-in Wi-Fi.
3. A future wired Ethernet run.

Test Wi-Fi signal quality, latency, packet loss, and roaming stability in the garage. Consider dust and seasonal temperature conditions. No bridge model or second phone has been selected.

### Dialing and call behavior to validate

- Standard extension dialing between phones should work without the assistant.
- An AI extension can be dialed like another SIP endpoint.
- Desired experience: lifting the handset can reach HOID easily **without preventing dialing other extensions**. Hotline/off-hook auto-dial and dialing delays require deliberate design and phone-specific validation.
- Assistant-originated calls are limited to explicitly requested or deliberately configured notifications; delivery mechanics remain to be prototyped.
- Intercom and auto-answer are not part of the initial implementation.

## 7. Smart-home scope and candidates

### Initial physical scope

**Home office and its en-suite bathroom**, with potential later expansion into the basement and garage.

### Office lighting

Existing setup:

- Four overhead recessed/can lights on one wall switch.
- One floor lamp.
- One desk lamp.
- House switches reportedly have neutral and ground available.

Desired capability: adjustable brightness, **color temperature, and color** for the overhead lights, while retaining practical physical control.

Leading *proposal*, not a purchase decision:

- Four **Philips Hue White & Color Ambiance BR30** bulbs, **if** fixture dimensions and sockets are compatible (verify BR30/E26 assumptions).
- Two Hue A19 bulbs for lamps, subject to fixture compatibility.
- Hue Bridge.
- Smart wall control with appropriate smart-bulb/detached functionality and robust local physical behavior.
- Optional Hue dimmer/buttons or other accessible controls for lamps.

A conventional smart dimmer with ordinary bulbs would not provide tunable color/color temperature. The exact switch/bulb/bridge combination must be assessed for compatibility and fallback behavior before buying.

### Bathroom

Likely simpler: smart wall dimmer with normal compatible LED bulbs, optionally a presence sensor and dim nighttime behavior. Still exploratory.

### Other optional devices

- mmWave presence sensing.
- Temperature/humidity sensors.
- One or two smart plugs for safe, nonhazardous loads.
- Motorized blinds at a later stage.

No need to buy a large device ecosystem before the first useful workflow is demonstrated.

## 8. Functional capabilities to explore

**Possible capabilities, not a committed backlog:**

- Call HOID from office phone and have a responsive voice conversation.
- Call WIT from workshop phone with workshop-specific context.
- Make direct office↔workshop telephone calls with no AI path.
- Query and control authorized office lights via Home Assistant.
- Ask for conversions, measurements, notes, and reminders.
- Ring a phone for selected reminders/timers instead of speaking unsolicited into the room.

**Later possibilities:**

- Web/text interface.
- Persistent conversational memory is not planned; reconsider only if a concrete use case justifies changing that decision.
- More rooms and additional SIP endpoints.
- Optional intercom behavior after WIT is introduced.
- Presence-informed notifications and richer automations.

Capabilities above are product ideas, **not a committed backlog**.

## 9. Current direction and status

### Established direction

- The project and repository are named **HOID**.
- The primary voice interaction is a physical SIP desk phone, not an always-listening smart speaker.
- The workshop variant is named **WIT** and is a secondary effort intended to share the underlying system.
- Workshop-specific context, tools, permissions, and connectivity will be considered when WIT becomes active.
- HOID is a shared assistant platform with multiple physical endpoints; endpoints may use distinct context, tools, permissions, and behavior.
- Normal extension-to-extension calls must bypass AI.
- A phone-originated call starts an intentional assistant interaction; off-hook dialing behavior still needs phone validation.
- Assistant-originated calls are only for explicitly requested or configured notifications; no proactive check-ins.
- SIP telephony is the intended phone interface, but Asterisk remains a preferred candidate rather than a final PBX selection.
- The first assistant experience targets one SIP phone. A separate initial telephony validation milestone is ordinary calls between two SIP extensions before adding AI.
- **Automation is additive** is a non-negotiable design principle.
- Home Assistant is the intended smart-device control layer.
- Local-first, modular architecture with replaceable model/speech components.
- No persistent conversational memory, audio recording, or transcript retention in the initial architecture. Active session context is discarded at hangup.
- Low-risk household access does not require speaker authentication; sensitive actions are outside initial scope.
- Fail safely when dependencies or integrations are unavailable; never claim unconfirmed success.
- Local STT/TTS processing is the initial direction; engine and voice selection are deferred to prototyping.
- Ollama is the selected initial LLM runtime; the model and required compute capacity remain open.
- Prefer `pileated` for the PBX; keep the PBX independently deployable from HOID.

### Preferred candidates, not final selections

- Asterisk as PBX, deployed via Docker Compose with host networking.
- Cisco CP-8841-3PC-K9 with 3PCC/MPP firmware as one possible phone.
- Hue-based office lighting.
- Wi-Fi client bridge for a workshop Ethernet SIP phone.
- Example extension numbers `100`/`101`/`102`.

### Deferred validation and planning

- Validate the preferred PBX and select a SIP/RTP bridge through a working phone/audio prototype.
- Select the LLM, quantization, and compute capacity after verifying the host and benchmarking local inference.
- Select local STT/TTS engines, voice, and audio pipeline through prototyping.
- Validate the phone model, provisioning, and off-hook behavior when phone hardware is available.
- Define detailed notification delivery, timeout, health-check, and retry behavior during prototyping.
- Select and validate smart-lighting hardware when the items are available.
- Define monitoring, secrets, updates, backups, and recovery during deployment planning.
- Revisit WIT connectivity and endpoint-specific behavior when the workshop effort begins.
- Define authorization and confirmation only if sensitive capabilities are proposed; such capabilities are outside initial scope.
- Choose which persistent service owns timers/reminders and define their creation, cancellation, and delivery lifecycle.
- Clarify which household/endpoint configuration can be version-controlled and which information or secrets must remain local.
- Clarify whether the initial "research" capability may use internet sources while speech and inference remain local.

## 10. Suggested milestones (nonbinding)

1. **Document the concept:** Repository README, this summary, vision, design principles, and lightweight decision records.
2. **Validate telephony:** Use the preferred PBX candidate on `pileated` to verify ordinary calling between two SIP extensions before adding AI. This is separate from the initial assistant scope, which targets one SIP phone. WIT and multi-phone deployment are secondary.
3. **Prototype assistant calls:** Connect a minimal voice assistant endpoint to the PBX; measure end-to-end latency.
4. **Introduce controlled home actions:** Integrate Home Assistant and test a small, safe lighting workflow with physical fallback.
5. **Refine character and reliability:** Persona, short responses, session lifecycle, logging, failure handling, and notifications.
6. **Extend to WIT:** Garage connectivity, second endpoint, workshop context and safe tool permissions.

Milestones are sequencing ideas, not dates or commitments. Hardware selection and experimentation may change the order.

## 11. Guidance for future AI coding agents

- **Read this document before proposing architecture or generating code.**
- Do **not** interpret candidate technologies, example extension numbers, folder layouts, or milestone ideas as final requirements.
- Preserve the distinction between **decided**, **proposed**, and **open**.
- Respect **Automation is additive**, physical controls, and local privacy boundaries.
- Keep Asterisk/PBX operationally separate from the assistant so basic calls do not depend on AI availability.
- Ask before making irreversible purchases, enabling remote access, choosing long-term platforms, or implementing hazardous device controls.
- Prefer small, testable experiments over prematurely building the whole system.
- Record meaningful architecture decisions with rationale as the design evolves.
- Update this document when decisions materially change; do not silently rewrite project intent.

---

*This document captures planning discussions as of October 8, 2026. It is intended to seed the repository and evolve with the project.*
