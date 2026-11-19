# Telephone Assist MVP — live validation (November 6, 2026)

This document describes the **observed running prototype**, not a fully reproducible installation from the public repository. The original recorded-audio CLI and allowlisted Home Assistant client remain distinct, independently useful capabilities.

## Verified user experience

- A Cisco SPA303 IP desk phone registers with a local Asterisk PBX as a SIP extension.
- An experimental assistant dialplan destination (extension `2000` in the observed deployment) connects to a **separate FastAGI service** using Home Assistant Assist.
- The user can converse over multiple turns, ask general questions, and request control of an approved office desk lamp. The lamp was physically controlled in a live call.
- The phone's third line key was configured as a dedicated **HOID** speed dial to this assistant destination. Pressing it on-hook opens a speakerphone call; pressing it with the handset off-hook uses the handset. Normal calling on other line keys was preserved.
- A spoken farewell can end the call; ordinary hangup also ends the session.
- The recording prompt beep was removed for a more natural experience. Turn-taking is still sequential, not full-duplex/streaming; short silence-detection waits and inference can produce noticeable response latency.
- A separate earlier assistant path was left intact to avoid disrupting the working prototype.

The exact extension assignments, network topology, SIP credentials, physical device identifiers, host paths, and service unit definitions belong in private operational documentation, **not** in this public repository.

## Live component sequence

```text
Physical SIP desk phone
        |
        v
Asterisk PBX (registration, dialplan, call/media handling)
        |
        v
FastAGI telephone adapter (session/turn loop and temporary audio)
        |
        v
Home Assistant Assist pipeline
        |-- Local STT (Whisper)
        |-- Conversational agent (Ollama, local small model)
        |-- Local TTS (Kokoro, Lewis voice)
        |
        v
Approved Home Assistant integration / smart device
        |
        v
Speech response back through FastAGI / Asterisk / phone
```

The above reflects observed local integration; it is not a claim that the repository's existing Python CLI modules are the implementation of every stage. Keep the existing allowlisted API client and experimental Assist integration distinct unless code review establishes a shared authorization boundary. In particular, **LLM-generated actions must not bypass approved control policies**; review Home Assistant tool exposure before expanding beyond low-risk devices.

## Privacy and service boundaries

- The telephone activates the session deliberately; there is **no ambient always-on listening**.
- Temporary telephone-turn audio is used for processing and cleaned up after use. The current design does not intentionally retain recordings, transcripts, or persistent conversational memory.
- Operational diagnostics may capture non-content metadata (such as stage durations or errors); do not log utterances, answers, tokens, audio files, or sensitive Home Assistant state.
- Ordinary SIP/PBX functionality should remain separate from the experimental assistant.
- The initial scope is low-risk household control; manual device controls remain functional.

## Source and deployment synchronization

**Attention:** Live FastAGI Assist changes were made and exercised on the homelab host. The public `main` branch originally documented only the CLI/recorded-file prototype. A documentation PR **does not ship or deploy these running scripts**.

Before publishing the host-local implementation:

1. On the host, inspect `git status --short --branch`, `git remote -v`, and `git diff` in the HOID checkout. Confirm whether the running `scripts/fastagi_assist.py` and related service/dialplan configuration are tracked, untracked, or outside the checkout.
2. Compare changes against the public default branch and separate reusable code/tests from environment-specific operations, credentials, and local topology. Do **not** blindly `git add -A` or push the entire host working tree.
3. Preserve the working original telephone path and Assist service separately, including clean farewell detection and no recording beep. Add mocked tests for normalized farewell phrases and session cleanup, without test recordings or conversation logs.
4. Put generic code and sanitized examples in a **separate reviewable branch/PR**; place host-specific runbooks and configuration in the private homelab repository.
5. Only after reviewing the diff and tests, merge and intentionally reconcile/deploy. A GitHub push by itself does not update the running service.

## Next improvements (not yet implemented)

- Shorten end-of-speech detection (currently a noticeable pause) only after testing reliability.
- Improve brief spoken answers and measure processing-stage latency using content-free metrics.
- Consider voice activity detection or streaming later if timing measurements warrant it.
- Define whether the experimental Assist pipeline and original application-level intent router should converge, without weakening the explicit device/action allowlist.
