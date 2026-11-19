# ADR-001: Use Home Assistant's timer helper for the HOID MVP

- **Date:** 2026-11-13
- **Status:** Accepted (implementation pending)
- **Decision:** Prefer Home Assistant's existing timer capability over a custom HOID scheduler for the initial office assistant.

## Context

HOID is a user-initiated, phone-based office assistant. The actual timer use case is occasional: interrupt focused work before a meeting or other commitment. Multiple overlapping, independently named timers are not an important MVP requirement. Other contexts, such as cooking, already have suitable timer tools.

We implemented and tested a native scheduler backed by SQLite, a local HTTP API, a polling service, and Asterisk phone notifications. It successfully created and dispatched multiple timers, including overlapping timers, and handled invalid duration requests. Development also surfaced and resolved a SQLite connection-lifecycle bug.

The implementation demonstrated technical feasibility, but required extra services, database state, custom intent handling, and operational maintenance. The Home Assistant timer helper and a timer-finished automation had already demonstrated phone notification capability.

## Decision

Use one Home Assistant timer helper for the MVP, controlled through Assist and connected to an automation that calls the SPA303 via Asterisk when the timer finishes. Keep Home Assistant as the source of truth for timer state.

Retire the custom scheduler and API from the **active runtime after** the Home Assistant path has been restored and verified end-to-end. Retain their code and tests in version control as a learning artifact, not as a parallel production timer system.

For the MVP, a new timer request may replace the existing office timer; this behavior should be communicated clearly and verified during implementation.

## Consequences and trade-offs

- **Benefits:** Fewer moving parts, simpler troubleshooting, less state duplication, and faster progress toward the office-assistant experience.
- **Trade-off:** A single timer helper does not support arbitrary overlapping named timers. Home Assistant timer restoration also has limitations; a timer that expires while Home Assistant is offline may not emit a normal completion event after restart.
- **Not solved by this decision:** Reliable speech transcription and routing through the SPA303 Assist pipeline still require separate testing.
- **Revisit if:** Real usage establishes a need for overlapping named timers, durable missed-expiration delivery, or more general scheduled jobs that Home Assistant cannot support cleanly.

## Product and engineering learning

The custom scheduler was valuable as a practical exercise in test-driven development, atomicity, service orchestration, API integration, and resource management. A working technical implementation is not, by itself, evidence that its complexity is justified by user value.

**Guiding principle:** Prefer the simplest existing capability that satisfies a demonstrated user need. Introduce custom infrastructure only when a concrete requirement justifies its operational complexity.
