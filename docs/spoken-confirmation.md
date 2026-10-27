# Spoken confirmation for recorded commands

HOID can optionally synthesize a verified Home Assistant response after processing a recorded command.

```bash
hoid ask-audio /tmp/turn-on-lamp.wav \
  --speak \
  --model /opt/hoid/models/kokoro/kokoro-v1.0.onnx \
  --voices /opt/hoid/models/kokoro/voices-v1.0.bin \
  --output /tmp/hoid-reply.wav
```

Listen on Loon (outside the SSH session):

```bash
ssh john@pileated 'cat /tmp/hoid-reply.wav' | ffplay -autoexit -nodisp -
```

The audio input must already exist. `--speak` requires all three of `--model`, `--voices`, and `--output`; `--dry-run` cannot be combined with `--speak`. Existing output files are never overwritten. Choose a fresh output filename for each test.

Speech synthesis runs **after** the action and its state verification. If synthesis fails, the command reports a warning but preserves the successful action's exit code and text response. If transcription, intent parsing, configuration, or the device action fails, no speech synthesis is attempted.

No recordings or transcripts are automatically retained by HOID, but input recordings and generated WAV files remain on disk until the operator deletes them. Keep credentials, local paths, device mappings, and recordings out of the public repository.
