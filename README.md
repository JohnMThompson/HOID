# HOID

HOID (Home Office Interface Device) is a local-first, personality-driven assistant project for a home office, with a possible future workshop presence called WIT (Workshop Interface Technology). The defining interaction is a physical SIP desk phone; ordinary telephone calling and physical lighting controls should remain useful without the assistant.

**Status (October 19, 2026):** The first infrastructure milestone is complete: Home Assistant on Pileated controls an office desk lamp through a Shelly smart outlet, and authenticated REST API ON/OFF commands were physically verified. **HOID application code, telephone integration, speech, and LLM orchestration have not yet been implemented.**

This repository documents the intended HOID application, architecture, and eventual code. Deployment paths, Docker configuration, network security, and operations for Pileated are maintained in the separate [homelab repository](https://github.com/JohnMThompson/homelab). Local-only planning notes are kept in `docs/planning/`, which is Git-ignored.

## Project documentation

- [Project summary](docs/project-summary.md) — product vision, privacy and safety principles, conceptual architecture, and current direction.
- [Home Assistant integration](docs/home-assistant-integration.md) — verified first physical-control milestone and proposed allowlisted Python client contract.

## Next implementation milestone

Build a small independently testable Home Assistant client supporting `get_state`, `turn_on`, and `turn_off` for explicitly approved devices, with readback verification and clear failure handling. SIP/Asterisk and voice capabilities follow separately.
