# HOID

HOID (Home Office Interface Device) is a local-first, personality-driven assistant project for a home office, with a possible future workshop presence called WIT (Workshop Interface Technology). The defining interaction is a physical SIP desk phone; ordinary telephone calling and physical lighting controls should remain useful without the assistant.

**Status (October 26, 2026):** Home Assistant controls a test lamp through a smart outlet. The first HOID Python Home Assistant client and CLI have passed 20 mocked tests on Python 3.12 and were installed successfully on the homelab host using Python 3.14. The user verified live CLI state reads, ON/OFF commands, subsequent state readback, and the lamp's physical response. **The complete telephone-driven assistant is not deployed.** SIP/Asterisk, speech, and LLM orchestration remain future work.

**Public repository policy:** HOID is intentionally public for shareable application code and sanitized documentation. Agents and contributors must follow [AGENTS.md](AGENTS.md) to keep credentials, real device mappings, household topology, and runtime configuration out of public commits.

This repository contains HOID's initial application code and documents its architecture and future direction. Deployment paths, Docker configuration, network security, and operations for Pileated are maintained in the separate [homelab repository](https://github.com/JohnMThompson/homelab). Local-only planning notes are kept in `docs/planning/`, which is Git-ignored.

## Project documentation

- [Project summary](docs/project-summary.md) — product vision, privacy and safety principles, conceptual architecture, and current direction.
- [Home Assistant integration](docs/home-assistant-integration.md) — verified live Python client, device-control contract, and safety constraints.

## Next implementation milestone

Containerize the working HOID CLI, validate its Home Assistant connectivity and lamp control from inside Docker, and keep credentials and household mappings outside version control. SIP/Asterisk and voice capabilities follow separately. No always-running HOID service is required for the current CLI.

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

On October 26, 2026, all 20 mocked tests passed on Python 3.12.15. The package then installed and the CLI launched on Python 3.14.4 on the homelab host. A user-observed live smoke test returned the correct initial OFF state, verified ON and OFF after CLI commands, and matched the physical lamp's behavior. This does not establish automated tests under Python 3.14, failure-path behavior against live Home Assistant, or Docker deployment.
