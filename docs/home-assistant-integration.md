# Home Assistant integration — verified Python client

**Status (October 26, 2026):** The HOID Python client and CLI are implemented, 20 mocked tests passed on Python 3.12.15, and the user successfully ran live status, ON, and OFF commands on the homelab host under Python 3.14.4. The lamp's physical response matched Home Assistant's reported state. Telephone, speech, and LLM integration remain unimplemented.

## Verified integration

The Python CLI uses an allowlisted logical device mapping and a runtime Home Assistant token to communicate with Home Assistant's local REST API. Home Assistant controls the office lamp through a locally integrated Wi-Fi smart outlet.

```text
Future SIP phone → Future intent router → HOID Python client [WORKING]
                                              |
                                              | Home Assistant REST API
                                              v
                                  Home Assistant [WORKING]
                                              |
                                              v
                                  Office lamp outlet [WORKING]
```

**October 19:** A manual authenticated REST API proof of concept confirmed physical ON/OFF behavior.

**October 26:** The HOID package installed on the host and its CLI launched on Python 3.14.4. The user reported an initial OFF state matching the physical lamp, followed by CLI output confirming ON, state ON, OFF, and state OFF; both physical transitions were observed. These are user-observed integration tests, not continuous health monitoring or automated live failure-path tests.

Deployment paths, network settings, and credentials belong to the separate [homelab documentation](https://github.com/JohnMThompson/homelab/blob/main/applications/hoid.md). Do not copy household entity IDs, server addresses, tokens, or runtime configuration into this public repository.

## Illustrative entity mapping (not live configuration)

All identifiers below are synthetic.

| Field | Value |
| --- | --- |
| Logical device name | `example_lamp` |
| Natural language alias | “example lamp” |
| Home Assistant area | Example room |
| Home Assistant entity | `switch.example_lamp` |
| Entity domain | `switch` |
| Device class | `outlet` |
| Physical device | Example smart outlet supplying a lamp |
| Allowed actions | Read state; turn on; turn off |

The `switch` domain is correct for a smart outlet. A logical device name or spoken alias is not itself an authorized Home Assistant entity ID.

## Python client contract

- `get_state("example_lamp")` reads Home Assistant's state.
- `turn_on("example_lamp")` issues one authorized ON service call and checks state readback.
- `turn_off("example_lamp")` issues one authorized OFF service call and checks state readback.
- A device/action allowlist prevents arbitrary entity IDs or services from being forwarded to Home Assistant.
- Typed errors distinguish authentication, missing/unavailable entities, unreachable service, and uncertain outcomes. A successful command followed by inaccessible readback is treated as uncertain rather than confidently successful.

### REST endpoint shapes (synthetic examples)

- `GET /api/states/switch.example_lamp`
- `POST /api/services/switch/turn_on` with JSON `{"entity_id":"switch.example_lamp"}`
- `POST /api/services/switch/turn_off` with the same entity ID

An HTTP success response or empty `[]` service response alone does not prove physical action. Readback reflects Home Assistant's reported state, not an independent electrical measurement.

### Safety and reliability

- Only low-risk, explicitly approved devices; no locks, alarms, garage doors, purchases, or power tools.
- Use local Home Assistant connectivity, not a public API endpoint.
- Load the token from a runtime environment variable, outside Git. Long-lived tokens inherit their Home Assistant user's permissions; they are not entity-scoped by default.
- Use bounded connection/read and state-verification timeouts. Never blindly repeat an action after an ambiguous result.
- Do not silently substitute devices or allow an LLM to invoke arbitrary actions.
- Do not persist audio, transcripts, or conversational memory for this client. Omit tokens and authorization headers from logs.
- Manual lamp control and Home Assistant must remain usable independently of HOID.

## Validation status

- **Passed:** 20 mocked tests under Python 3.12.15, including uncertain-outcome readback regression coverage.
- **Passed:** Host package installation and CLI startup under Python 3.14.4.
- **Passed:** Live read-only state check, ON/OFF service calls, readback, and user-observed physical lamp behavior.
- **Not yet validated:** Automated test suite under Python 3.14, live failure cases, container networking, and Docker execution.

## Next interfaces

Containerize the client and repeat the live smoke test from Docker. Later, a deterministic intent router will translate spoken requests into approved logical device/action pairs. Asterisk, local speech recognition, TTS, and an Ollama fallback remain separate future components.
