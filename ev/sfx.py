"""Realistic sound effects (owner, 2026-11-03: "use real sound effects").

Every SFX is a realistic recording-style clip made with the ElevenLabs Sound Effects API (same account and
key as the narrator; ElevenLabs' paid plans include commercial use) and CACHED AS A FILE IN THE REPO, so it is
generated once and reused:

  ev/sfx/<name>.wav             house library (whooshes, impacts, mechanical clunks, ticks, air hiss, ...)
  episodes/<slug>/sfx/<name>.wav  episode-specific sounds declared in scene.SFX_PROMPTS, e.g. a V10 revving
                                  {"v10_rev": ("high revving naturally aspirated V10 engine, free rev to 9000 rpm, "
                                               "exterior recording, no music", 3.0)}
                                  and used in sound() as (t, "v10_rev", gain).

No licensed or downloaded recordings of real cars, no music. Prompts describe a generic engine type, never a
specific recording. Generate/refresh the house library:  python -m ev.sfx --library
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(ROOT, "ev", "sfx")
SR = 48000

LIBRARY = {
    "whoosh_up": ("quick clean cinematic air whoosh, rising swish transition, close, no music, no voice", 1.0),
    "whoosh_down": ("quick clean cinematic air whoosh, falling swoosh transition, no music, no voice", 1.0),
    "whoosh_big": ("big cinematic whoosh sweep passing by, powerful air movement transition, no music", 1.3),
    "impact": ("deep punchy cinematic impact hit, sub boom with short tail, no music", 1.6),
    "impact_long": ("deep cinematic boom impact with long rumbling reverb tail, trailer hit, no music", 2.6),
    "clunk": ("heavy steel machine parts locking together, solid metal clunk, close-up mechanical foley", 0.7),
    "tick": ("single small precise metal click, mechanical switch tick, close foley, very short", 0.5),
    "spool": ("turbocharger spooling up, rising turbine whistle, car engine bay, no music", 2.0),
    "hiss": ("short burst of compressed air release, pneumatic hiss, blow off valve psssh", 0.8),
    "ratchet": ("mechanical ratchet clicking several times, metal gears engaging, close foley", 0.8),
    "spark": ("electric spark snap, ignition spark crackle, close, very short", 0.5),
    "rumble": ("low mechanical rumble of a big engine idling in a garage, steady, no music", 3.0),
}


def _trim_norm(x, sr, thr=0.004):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx):
        x = x[max(0, idx[0] - int(0.005 * sr)): idx[-1] + int(0.05 * sr)]
    pk = np.max(np.abs(x)) + 1e-9
    x = x / pk * 0.9
    n = min(len(x), int(0.02 * sr))
    if n > 1:
        x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def generate_clip(prompt, duration, path, influence=0.45):
    from .voice import _post, decode_mp3
    dur = float(min(22.0, max(0.5, duration)))
    data = _post("/sound-generation?output_format=mp3_44100_128",
                 {"text": prompt, "duration_seconds": dur, "prompt_influence": influence}, accept="audio/mpeg")
    x = decode_mp3(data, SR)
    x = _trim_norm(x, SR)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, x, SR)
    with open(path + ".json", "w") as fh:
        json.dump({"prompt": prompt, "duration": dur, "source": "ElevenLabs Sound Effects API"}, fh)
    return x


def _load(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr).astype(np.float32)
    return x


def get(name, episode_dir=None, prompts=None):
    """Return the clip for `name` (generating and caching it if it has a prompt but no file yet)."""
    cands = []
    if episode_dir:
        cands.append(os.path.join(episode_dir, "sfx", f"{name}.wav"))
    cands.append(os.path.join(LIB_DIR, f"{name}.wav"))
    for p in cands:
        if os.path.exists(p):
            return _load(p)
    if prompts and name in prompts:
        prompt, dur = prompts[name]
        return generate_clip(prompt, dur, os.path.join(episode_dir, "sfx", f"{name}.wav"))
    if name in LIBRARY:
        prompt, dur = LIBRARY[name]
        return generate_clip(prompt, dur, os.path.join(LIB_DIR, f"{name}.wav"))
    raise KeyError(f"unknown sound effect {name!r}: add it to ev.sfx.LIBRARY or scene.SFX_PROMPTS")


def build_library(force=False):
    for name, (prompt, dur) in LIBRARY.items():
        p = os.path.join(LIB_DIR, f"{name}.wav")
        if os.path.exists(p) and not force:
            continue
        generate_clip(prompt, dur, p)
        print("generated", name)


if __name__ == "__main__":
    if "--library" in sys.argv:
        build_library(force="--force" in sys.argv)
