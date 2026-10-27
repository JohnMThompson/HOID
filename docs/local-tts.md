# Local text-to-speech (experimental)

HOID's `speak` command converts supplied text to a mono 16-bit PCM WAV file using Kokoro ONNX. It does **not** contact Home Assistant, interpret commands, or change device state. Speech is an output adapter, never a prerequisite for actions.

Install on Pileated in the existing virtual environment:

```sh
python -m pip install -e '.[dev,stt,tts]'
python -m pytest -q
```

Obtain a compatible Kokoro ONNX model and `voices.bin` from the upstream kokoro-onnx project and store them in a private local directory (not in Git). Verify the selected voice exists in your voices file. Default voice `bm_lewis` uses British English.

```sh
hoid speak 'The desk lamp is on.' --model /private/path/kokoro-v1.0.onnx --voices /private/path/voices-v1.0.bin --output /tmp/hoid-response.wav
```

Run on **Loon**, outside the SSH session:

```sh
ssh john@pileated 'cat /tmp/hoid-response.wav' | ffplay -autoexit -nodisp -
```

If hostname resolution fails, substitute Pileated's LAN address. `ffplay` is part of the `ffmpeg` package on Linux Mint. Existing output files are never overwritten. This command does not retain text or audio beyond the operator-selected WAV output. Delete the WAV yourself when no longer needed.

This milestone is **standalone TTS only**. It does not yet speak `ask-audio` responses or stream into Asterisk. Phone audio formats will be addressed during SIP integration.
