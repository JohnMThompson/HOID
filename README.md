# HOID

HOID (Home Office Interface Device) is a local-first, personality-driven assistant for a home office, with a possible future workshop endpoint called WIT (Workshop Interface Technology). Its primary interface is a physical SIP desk telephone. Ordinary telephone calling and physical lighting controls should remain useful independently of the assistant.

**Status (November 18, 2026):** HOID has a working, manually verified telephone voice-assistant path on the homelab host. A Cisco SPA303 SIP phone connects through Asterisk to a Python FastAGI service. HOID uses local Whisper speech-to-text and Kokoro text-to-speech (Lewis voice), with Home Assistant Assist handling conversational requests through a locally configured Ollama integration. Home Assistant also manages a timer that can ring the telephone on completion. A live telephone conversation and timer callback were successfully tested after retiring the previous FastAGI service. A dedicated line key on the Cisco SPA303 provides convenient access using either the handset or speakerphone.

**Public repository policy:** HOID is intentionally public for shareable application code and sanitized documentation. Agents and contributors must follow [AGENTS.md](AGENTS.md). Never commit credentials, real device mappings, household topology, or private runtime configuration.

This repository contains HOID application code and design documentation. Deployment paths, Docker configuration, network security, and host operations are maintained separately in the [homelab repository](https://github.com/JohnMThompson/homelab). Local-only planning notes belong in Git-ignored `docs/planning/`.

## How the live telephone assistant works

```text
Cisco SPA303 (SIP extension 101)
             |
          Asterisk
             |
   assistant extension 2000
             |
   FastAGI Assist (port 4574)
       /             \
  Whisper STT     Kokoro TTS
       \             /
      Home Assistant Assist
             |
           Ollama
             |
   Home Assistant actions
```

The diagram is conceptual: FastAGI coordinates speech recognition, calls the Home Assistant Assist conversation API, and synthesizes spoken responses. Home Assistant determines which exposed actions are available; Ollama is used through Home Assistant, **not** through a separate HOID-owned conversation engine.

For timer notifications, Home Assistant starts and tracks the timer, then its completion automation stages an Asterisk call file. Asterisk calls the office phone and plays one of ten prerecorded timer announcements through extension `203`.

The active telephone service is `hoid-fastagi-assist.service`, which uses `scripts/fastagi_assist.py` and shared utilities from `scripts/fastagi.py`. The earlier standalone FastAGI service on port `4573` and its dialplan extension `202` have been retired. **Do not delete `scripts/fastagi.py`: the active service imports from it.**

See [architecture](docs/architecture.md) for responsibilities, boundaries, and the distinction between deployed and planned capabilities. The telephone workflow is not the same execution path as the CLI utilities below.

## Project documentation

- [Telephone Assist MVP](docs/telephone-assist-mvp.md) — original live telephone validation and implementation notes.
- [Architecture](docs/architecture.md) — deployed telephone request and timer callback flows, component boundaries, and design principles.
- [Project summary](docs/project-summary.md) — product vision, privacy and safety principles, and roadmap. Some historical implementation-status sections may still describe earlier milestones.
- [Home Assistant integration](docs/home-assistant-integration.md) — original physically verified lamp-control milestone and the allowlisted Python client contract.
- [Intent routing](docs/intent-routing.md) — deterministic CLI request handling, distinct from the live Home Assistant Assist pipeline.
- [Audio requests](docs/audio-requests.md) — recorded-file CLI workflow.
- [Spoken confirmation](docs/spoken-confirmation.md) — recorded command, verified action, and synthesized response.
- [Speech-to-text](docs/speech-to-text.md) and [local TTS](docs/local-tts.md) — standalone speech adapter milestones.

## Development and diagnostic CLI

The repository also includes a Python Home Assistant client for controlling approved switch entities through configured logical device names. This is useful for development and diagnostics; it is **not** the orchestration layer for live telephone conversations.

### Development setup

Requires Python 3.12 or newer.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

**Testing status (November 18, 2026):** The remaining automated suite passed **87 tests** after the removal of obsolete scheduler and direct-Ollama modules. This is not a substitute for live integration testing; the telephone conversation and timer callback were separately verified on the host.

### Runtime configuration

Copy the synthetic configuration example:

```bash
cp hoid.example.json hoid.json
```

Set the Home Assistant token using either `HOID_HA_TOKEN` or `HOID_HA_TOKEN_FILE` pointing to a readable token file (not both). Do not store credentials in the JSON file or commit them.

The CLI reads `hoid.json` by default. `HOID_CONFIG` overrides the configuration path, and `HOID_HA_URL` can override the Home Assistant URL.

Replace the example `.invalid` URL and `switch.example_lamp` mapping **only in local configuration**. Each device must explicitly list permitted actions.

### CLI examples

```bash
hoid lamp status
hoid lamp on
hoid lamp off
```

The `lamp` alias refers to the configured logical device `desk_lamp`.

Commands use bounded HTTP and state-verification timeouts. State-changing commands issue one service request, then verify the reported state; they do not blindly retry an action. Successful readback confirms Home Assistant's **reported** state, not independent physical operation.

Additional development commands include `hoid transcribe`, `hoid ask`, `hoid ask-audio`, and `hoid speak`. See the corresponding documentation for usage and limitations.

## Docker CLI (validated October 26, 2026)

The repository includes a minimal Dockerfile and Compose definition for **one-shot CLI execution**, not the live telephone daemon. Docker Compose uses host networking so the container can access a Home Assistant API listening on the Docker host's loopback interface. This trades away network isolation; no ports are published, and the container drops Linux capabilities, has a read-only filesystem, and uses no-new-privileges.

Create a private, Git-ignored `hoid.json` using the synthetic example. Set `HOID_TOKEN_FILE` to the absolute path of a host-side, owner-readable token file. The Compose definition mounts both files read-only and sets `HOID_HA_TOKEN_FILE` inside the container; it does **not** inject token contents into Compose environment variables.

For persistent configuration, create a private, Git-ignored `.env` alongside `compose.yml` containing `HOID_TOKEN_FILE=/absolute/path/to/private/ha-token` (the **path**, not the token contents), and restrict it with `chmod 600 .env`. Compose loads this file automatically. Run as the host user that owns the token file (defaults to UID/GID 1000; override `HOID_UID` and `HOID_GID` as needed).

```bash
docker compose build
docker compose run --rm cli lamp status
docker compose run --rm cli lamp on
docker compose run --rm cli lamp off
```

The CLI runs in temporary containers; it is not a background daemon. The current Compose definition requires `HOID_TOKEN_FILE` even for `docker compose build`; the private `.env` file satisfies this requirement. Removing that build-time requirement remains future cleanup.

Do not commit `hoid.json`, the token file, or any host-specific environment files. Avoid enabling shell tracing when working with secrets. The Docker image contains only generic application code; it does not contain local configuration or credentials.

**Historical validation (October 26, 2026):** The container built successfully on Pileated, authenticated to Home Assistant, and completed lamp status, ON, and OFF checks with physical confirmation. The private `.env` configuration was also verified.

## Design principles and next steps

HOID uses deliberate, user-initiated telephone sessions rather than an always-listening microphone. Its design calls for no persistent audio recordings, transcripts, or conversational memory by default. Keep credentials and private household information out of the public repository, preserve independent manual controls and PBX functions, and treat uncertain action outcomes as uncertain rather than claiming success.

Next work includes keeping the remaining project documentation aligned with the deployed architecture, improving reliability and failure-path testing, and evaluating additional capabilities without expanding access to sensitive home controls by default. A second workshop endpoint (WIT) remains a future possibility.
