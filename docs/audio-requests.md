# Recorded-audio request pipeline

`hoid ask-audio <file.wav>` transcribes an existing recording locally with faster-whisper, parses its text using the deterministic intent router, and uses the existing allowlisted Home Assistant client to execute recognized requests. This is a one-shot command, **not** a microphone listener, SIP integration, or TTS response.

## Safe first test

```sh
python -m pytest -q
hoid ask-audio /path/to/recording.wav --dry-run
```

The `--dry-run` option reports the recognized device and action **without loading credentials or contacting Home Assistant**. A recognized command without `--dry-run` can physically switch the approved lamp:

```sh
hoid ask-audio /path/to/recording.wav
```

Start with a recording of `Is the desk lamp on?` for a read-only live test. A recording saying `Turn on the desk lamp.` **will turn on the lamp** when run without `--dry-run`.

Unsupported and empty transcripts perform no action and return exit code 2. Transcription, configuration, and Home Assistant failures return exit code 1. As with `hoid ask`, state-changing success is only reported after the existing client verifies the state.

The command does not print or persist the transcript by default, and does not retain audio. The **input audio file is pre-existing** and is not deleted by HOID; manage its lifecycle yourself. Model files may be downloaded by faster-whisper on first use. Runtime tokens and device mappings remain private.
