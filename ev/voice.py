"""The Expanded View narrator. FIXED BRAND VOICE: Kokoro `am_michael`, speed 1.0. Do not change.

generate(lines, out_dir) writes <key>.wav per line (24 kHz mono, silence-trimmed).
Model files are downloaded once from GitHub releases into ~/.cache/expanded-view/models.
"""
import os
import subprocess

import numpy as np
import soundfile as sf

VOICE = "am_michael"
SPEED = 1.0
LANG = "en-us"

MODEL_DIR = os.path.expanduser("~/.cache/expanded-view/models")
MODEL_URLS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}


def ensure_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_URLS.items():
        path = os.path.join(MODEL_DIR, name)
        if not os.path.exists(path) or os.path.getsize(path) < 1_000_000:
            tmp = path + ".part"
            subprocess.run(["curl", "-sSL", "--retry", "3", "-o", tmp, url], check=True)
            os.replace(tmp, path)
    return os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin")


_k = None


def _engine():
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        m, v = ensure_models()
        _k = Kokoro(m, v)
    return _k


def trim(s, sr):
    idx = np.where(np.abs(s) > 0.01)[0]
    return s[max(0, idx[0] - int(0.02 * sr)): idx[-1] + int(0.08 * sr)]


def say(text):
    s, sr = _engine().create(text, voice=VOICE, speed=SPEED, lang=LANG)
    return trim(np.asarray(s, np.float32), sr), sr


def phonemes(text):
    """Check pronunciation of tricky words (acronyms, part names) before generating."""
    return _engine().tokenizer.phonemize(text, LANG)


def generate(lines, out_dir, keys=None, force=False):
    os.makedirs(out_dir, exist_ok=True)
    total = 0.0
    for key, text in lines:
        path = os.path.join(out_dir, f"{key}.wav")
        stamp = path + ".txt"
        if keys and key not in keys:
            continue
        same = os.path.exists(stamp) and open(stamp).read() == f"{VOICE}|{SPEED}|{text}"
        if os.path.exists(path) and same and not force:
            total += sf.info(path).duration
            continue
        s, sr = say(text)
        sf.write(path, s, sr)
        with open(stamp, "w") as fh:
            fh.write(f"{VOICE}|{SPEED}|{text}")
        total += len(s) / sr
    return total
