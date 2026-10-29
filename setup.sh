#!/usr/bin/env bash
# One-time setup for a fresh workspace. Safe to re-run.
set -e
cd "$(dirname "$0")"

pip install --quiet --break-system-packages skia-python kokoro-onnx soundfile scipy numpy pillow pyyaml 2>/dev/null \
  || pip install --quiet skia-python kokoro-onnx soundfile scipy numpy pillow pyyaml

command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }

# Brand fonts are bundled in ev/fonts. Voice model (Kokoro v1.0) goes to ~/.cache/expanded-view/models.
python3 -c "import ev.gfx; print('fonts ok')"
python3 -c "from ev import voice; voice.ensure_models(); print('voice model ready')"
echo "setup complete"
