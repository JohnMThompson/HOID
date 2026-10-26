# HOID

HOID (Home Office Interface Device) is a local-first, personality-driven assistant project for a home office, with a possible future workshop presence called WIT (Workshop Interface Technology). The defining interaction is a physical SIP desk phone; ordinary telephone calling and physical lighting controls should remain useful without the assistant.

**Status (October 26, 2026):** The first infrastructure milestone is complete: Home Assistant on a private homelab host controls a test lamp through a smart outlet, and authenticated REST API ON/OFF commands were physically verified. The first HOID Python Home Assistant client and minimal CLI are implemented and tested locally with mocked responses; **the client has not yet been deployed or validated against the live lamp**. Telephone integration, speech, and LLM orchestration remain unimplemented.

**Public repository policy:** HOID is intentionally public for shareable application code and sanitized documentation. Agents and contributors must follow [AGENTS.md](AGENTS.md) to keep credentials, real device mappings, household topology, and runtime configuration out of public commits.

This repository contains HOID's initial application code and documents its architecture and future direction. Deployment paths, Docker configuration, network security, and operations for Pileated are maintained in the separate [homelab repository](https://github.com/JohnMThompson/homelab). Local-only planning notes are kept in `docs/planning/`, which is Git-ignored.

## Project documentation

- [Project summary](docs/project-summary.md) — product vision, privacy and safety principles, conceptual architecture, and current direction.
- [Home Assistant integration](docs/home-assistant-integration.md) — verified first physical-control milestone and allowlisted Python client contract.

## Next implementation milestone

Deploy and manually validate the Python Home Assistant client against the approved desk lamp, including readback verification and safe failure behavior. SIP/Asterisk and voice capabilities follow separately.

## Python Home Assistant client

The first HOID application component is a Python client for controlling approved Home Assistant switch entities through logical device names.

### Development setup

Requires Python 3.12 or newer.

    python3.12 -m venv .venv
    . .venv/bin/activate
    python -m pip install -e '.[dev]'
    python -m pytest

### Runtime configuration

Copy the synthetic configuration example:

    cp hoid.example.json hoid.json

Set the Home Assistant token using the HOID_HA_TOKEN environment variable. Do not store credentials in the JSON file or commit them.

The application reads hoid.json by default. HOID_CONFIG overrides the configuration path, and HOID_HA_URL can override the Home Assistant URL.

Replace the example .invalid URL and switch.example_lamp mapping only in your local configuration. Each device must explicitly list permitted actions.

### CLI

    hoid lamp status
    hoid lamp on
    hoid lamp off

The lamp alias refers to the configured logical device desk_lamp.

Commands use bounded HTTP and state-verification timeouts. State-changing commands issue one service request, then verify the reported state. They do not blindly retry an action.

A successful readback confirms Home Assistant's reported state, not independent physical operation.

### Testing status

The initial 17 tests passed locally under Python 3.12.15 using mocked HTTP responses and synthetic credentials. Additional regression tests cover inaccessible readback after an accepted command; run the suite again to validate these changes. Live integration and physical device validation remain outstanding.
