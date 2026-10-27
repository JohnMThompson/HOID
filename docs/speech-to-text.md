# Offline speech-to-text prototype

HOID supports file-based English transcription using the optional `stt` dependency group.

## Install

```sh
python -m pip install -e '.[dev,stt]'
python -m pip check
python -m pytest -q
```

The tested host combination is Python 3.14.4, faster-whisper 1.2.1 and PyAV 16.0.1. The PyAV pin avoids an observed incompatible `metadata_errors` argument in PyAV 19.0.2.

## Transcribe

```sh
hoid transcribe /path/to/sample.wav
```

The default model is `tiny.en` on CPU with INT8 computation. The first invocation may download model weights from Hugging Face; later invocations reuse the local model cache. The CLI prints recognized text to stdout, or a generic error to stderr with a nonzero exit status. A blank result is possible when no speech is detected.

This command does **not** execute any Home Assistant action. It is a standalone input adapter milestone, not an always-listening service or SIP integration.

## Privacy and scope

Do not commit recordings, transcripts, or local model caches. The adapter does not intentionally persist recordings or transcripts. Avoid logging recognized text or audio paths. Keep any test audio outside the public repository. The optional dependency group keeps existing lamp commands independent of STT libraries.

## Validation

The adapter and CLI have mocked unit tests. After merging, run the real audio smoke test on the target host; GitHub changes alone do not prove runtime transcription.
