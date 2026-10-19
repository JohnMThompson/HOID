# Home Assistant integration — first verified capability

**As of October 19, 2026:** The underlying Home Assistant integration works, but **there is no HOID application or Python client yet**. This page is the starting contract for implementation, not a claim that HOID can currently accept commands.

## Working end-to-end proof

On the private Ubuntu/Docker homelab host, Home Assistant Container communicates locally with a Wi-Fi smart outlet through its local smart-device integration. A user authenticated from the homelab host with a Home Assistant long-lived access token, read the outlet state, issued ON and OFF REST service calls, and confirmed the physical office desk lamp responded to both commands. The final state read was `off`.

```text
Future SIP phone → Future HOID intent router → Future allowlisted device-control client
                                                        |
                                                        | Home Assistant REST API
                                                        v
                                          Home Assistant on a private homelab host [WORKING]
                                                        |
                                                        | Local smart-device integration
                                                        v
                                          Office Desk Lamp outlet [WORKING]
```

The authoritative deployment paths, Docker/network configuration, operational runbook considerations, and host credentials **belong to the separate [homelab documentation](https://github.com/JohnMThompson/homelab/blob/main/infrastructure/home-assistant.md)**. Do not duplicate server configuration or commit any access tokens to this repository.

## Illustrative entity mapping (not live configuration)

The following identifiers are **synthetic examples**, not the actual household entity mapping. Actual entity IDs and device inventory belong in private runtime configuration.

| Field | Value |
| --- | --- |
| Logical device name | `example_lamp` |
| Natural language alias | “example lamp” |
| Home Assistant area | Example room |
| Home Assistant entity | `switch.example_lamp` |
| Entity domain | `switch` |
| Device class | `outlet` |
| Physical device | Example smart outlet supplying a lamp |
| Allowed actions for MVP | Read state; turn on; turn off |

The `switch` domain is correct for a smart outlet in Home Assistant. The outlet device class describes the hardware; it does not change the entity's API domain. A logical device name or voice alias is not itself an authorized Home Assistant entity ID.

## First Python client — intended behavior

The proposed device-control module should expose simple operations, without making telephony, speech engines, or an LLM dependencies:

- `get_state("example_lamp")` — return the Home Assistant state or an explicit error/unavailable result.
- `turn_on("example_lamp")` — request ON, then read back the entity state.
- `turn_off("example_lamp")` — request OFF, then read back the entity state.

Use an **explicit allowlist** mapping stable logical names to permitted Home Assistant entity IDs and actions. Never accept an arbitrary entity ID, service domain, or free-form action from an LLM or user speech and forward it unchecked.

### REST endpoint shapes (sanitized examples; actual paths verified manually)

- `GET /api/states/switch.example_lamp`
- `POST /api/services/switch/turn_on` with JSON `{"entity_id":"switch.example_lamp"}`
- `POST /api/services/switch/turn_off` with the same entity ID

Home Assistant's empty `[]` response to a service call is **not** confirmation that the lamp changed state. The client must check the subsequent entity state. State readback reflects Home Assistant's reported state, not an independent electrical measurement. If an outcome is unknown, say so rather than claiming success.

### Safety, privacy, and reliability constraints

- Only low-risk, explicitly approved devices in the first iteration; no locks, alarms, garage doors, purchases, or power tools.
- Use local HTTP access within the trusted host/LAN; do not expose the Home Assistant API publicly for HOID.
- Read the access token from runtime secret configuration outside version control. Long-lived Home Assistant tokens inherit their user's permissions and are **not** entity-scoped by default.
- Use reasonable connection/read timeouts; distinguish authentication, unreachable service, missing entity, unavailable state, and state-verification failure.
- Do not silently substitute a different device. Avoid blind retries after ambiguous results; read state before considering a repeat.
- No conversation transcripts or voice recordings are needed for this client. Operational logs should omit tokens, authorization headers, and private content.
- Keep manual lamp operation and the Home Assistant UI functional independently of HOID.

## Definition of done for first code milestone (not yet implemented)

1. Local Python client implements the three operations against the configured Home Assistant endpoint.
2. Tests use a fake HTTP API or mocks and cover success, rejected/unknown device, timeouts, unavailable entity, and unsuccessful verification.
3. A real integration smoke test toggles the desk lamp and verifies reported state and physical response.
4. No token appears in code, repository history, test output, or logs.
5. Errors are returned as explicit outcomes suitable for a short spoken response.
6. Documentation clearly distinguishes local proof of concept from deployed HOID service.

## Next interfaces

A deterministic intent router will eventually translate an utterance such as “turn on the example lamp” into an approved logical device/action pair. Asterisk, local speech recognition, text-to-speech, and an Ollama-based fallback remain separate future components. The initial API module should be independently testable without any of them.
