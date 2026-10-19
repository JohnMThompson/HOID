# Agent instructions — HOID

These instructions apply to all files in this repository and to AI coding assistants, automated agents, and human contributors. Read [docs/project-summary.md](docs/project-summary.md) before proposing architectural changes.

## Repository visibility and security boundary

**HOID is intentionally PUBLIC, with safeguards.** Its purpose is to share application source, architecture, tests, and sanitized examples. Treat every committed file, branch, pull request, issue, CI log, and commit-history entry as potentially public and permanently retained.

**The separate `homelab` repository is PRIVATE** and owns the real Pileated deployment, network topology, host paths, operational procedures, and actual device inventory. Do not copy its sensitive contents into HOID or assume that a private repository URL makes copied information private.

**Runtime secrets stay on the host or in an approved secret store, never in either repository.** This includes Home Assistant long-lived access tokens, passwords, API keys, certificates/private keys, session tokens, SIP credentials, and private household data.

## Safe content policy

Safe to commit:
- Generic Python application code, protocol abstractions, allowlisted action logic, unit tests, and documentation.
- Synthetic fixtures and redacted log examples.
- `.env.example` and sample YAML/JSON with **obviously fake** values and no real host identifiers.
- Generic logical device aliases such as `desk_lamp` or `example_lamp`.

Do not commit or paste into public artifacts:
- Real credentials, auth headers, tokens, cookies, secrets, private keys, or live environment files.
- Actual Home Assistant configuration directories or backups, `.storage/` contents, databases, logs, recordings, transcripts, or device discovery exports.
- Real LAN/WAN IPs, MAC addresses, DNS names, router/firewall rules, exposed port inventories, physical addresses, or detailed home topology.
- Real Home Assistant entity IDs or a comprehensive list of household devices. Use examples such as `switch.example_lamp` in public docs/tests; keep live mappings in private runtime configuration.
- Personal data, household schedules, presence/occupancy information, or sensitive automation routines.

A public repo does not become safe merely because the code is open source or a file is in `.gitignore`.

## Before changing files or publishing anything

1. Identify whether the task involves **generic HOID code** or **real homelab operations**. Keep the former here; document/deploy the latter privately.
2. Read relevant existing files and preserve the distinction between **verified**, **planned**, and **example** behavior.
3. Use environment variables, mounted secret files, or an approved secret manager. Never hardcode tokens or default to real credentials. Keep examples inert.
4. Check the entire diff, including new files, for secrets and private topology. Run a secret scanner (for example, Gitleaks) when available; manual review is still required.
5. Avoid printing credentials in command output, debug logs, exception messages, screenshots, test snapshots, CI artifacts, or pull request descriptions.
6. Prefer a pull request for review over committing directly to the default branch. Do not push local operational data or run production-altering commands without explicit approval.
7. Do not weaken `.gitignore`, security checks, or access restrictions merely to make a development workflow pass.

## Home Assistant integration rules

- Home Assistant is an external control API; HOID must not depend on or embed its deployment configuration.
- Configure the API endpoint, token, and actual entity mappings **at runtime**, outside this repository. Document only sanitized examples.
- An access token is not necessarily scoped to the one device HOID intends to control. Enforce an explicit **application-level allowlist** of approved logical devices and actions.
- Never pass arbitrary spoken text or LLM-generated entity IDs, service domains, or service payloads directly to Home Assistant.
- Validate action results by reading state back; do not claim success solely from a successful HTTP response. Clearly communicate unavailable, failed, or uncertain outcomes.
- Start with low-risk lighting/outlet controls. No locks, garage doors, alarms, purchases, hazardous tools, or unapproved devices.
- Keep physical/manual operation available independently of HOID.

## Local-first privacy and architecture

- A SIP desk phone is the intentional interface; do not introduce ambient always-on listening as a default.
- Do not persist audio, transcripts, or conversational memory in the initial architecture.
- Keep Asterisk/ordinary telephony independent of AI orchestration.
- Keep local speech, inference, and Home Assistant modules replaceable and independently testable.
- Fail safely and do not silently perform alternate actions or claim unverified outcomes.

## If sensitive information is exposed

**Stop publishing immediately.** Do not merely delete the file in a follow-up commit or assume `.gitignore` fixes history. Notify the repository owner, revoke/rotate exposed credentials, assess affected access, and coordinate any Git history cleanup. Never repeat the exposed value in the incident report.

## Scope and authority

These instructions guide contributors and agents; they do not grant permission to access private infrastructure, rotate credentials, expose services, or make purchases. Ask before making security-sensitive changes or changing privacy/design principles. Prefer small, reviewable changes with tests and accurate documentation.
