"""The Expanded View narrator. FIXED BRAND VOICE (owner, 2026-11-03): ElevenLabs "Brian" (voice B),
model eleven_multilingual_v2. Used for EVERY video (Shorts and long-form). Do not change.

generate(lines, out_dir, lexicon=None) writes, per line:
  <key>.wav   narration (44.1 kHz mono, silence-trimmed)
  <key>.json  {"words": [{"w", "start", "end"}, ...]} exact word times from ElevenLabs' character alignment,
              one entry per caption word (text.split()), so captions and cues sync to the real speech.
Lines are generated with previous_text/next_text so the delivery flows from line to line (no choppy joins).

Pronunciation: the CAPTION text stays as written ("VTEC", "2JZ"); only the text sent to the voice is respelled
using LEXICON (+ an episode's SAY dict). Each caption word maps to one spoken phrase, so timings stay exact.

Setup (owner): ELEVENLABS_API_KEY in the task environment and api.elevenlabs.io in the allowed domains
(docs/SETUP_ACCOUNTS.md). If either is missing, generate() raises NarratorNotConfigured: the run must stop
(status needs_review) and tell the owner. NEVER publish with another voice.

EV_VOICE=kokoro selects the old free Kokoro voice for LOCAL PREVIEWS ONLY; ev.build marks such builds
not-ok so they can never pass the QA gate.
"""
import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request

import numpy as np
import soundfile as sf

VOICE_NAME = "Brian"
VOICE_ID = "nPczCjzI2devNBz1zQrb"           # ElevenLabs premade "Brian - Deep, Resonant and Comforting"
MODEL_ID = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True, "speed": 1.0}
API = "https://api.elevenlabs.io/v1"
SR = 44100

# caption word (normalised: lowercase, punctuation stripped) -> what the narrator should say
LEXICON = {
    "vtec": "V-tec", "i-vtec": "eye V-tec", "nsx": "N S X", "lfa": "L F A", "jdm": "J D M",
    "2jz": "two J Z", "2jz-gte": "two J Z, G T E", "1jz": "one J Z", "rb26": "R B twenty six",
    "rb26dett": "R B twenty six, D E T T", "1lr-gue": "one L R, G U E", "13b": "thirteen B", "20b": "twenty B",
    "r26b": "R twenty six B", "787b": "seven eight seven B", "f20c": "F twenty C", "c30a": "C thirty A",
    "c32b": "C thirty two B", "k20": "K twenty", "b18c": "B eighteen C", "ls": "L S", "ls1": "L S one",
    "ls3": "L S three", "v6": "V six", "v8": "V eight", "v10": "V ten", "v12": "V twelve", "w16": "W sixteen",
    "amg": "A M G", "bmw": "B M W", "e63": "E sixty three", "m3": "M three", "m5": "M five", "gt-r": "G T R",
    "gtr": "G T R", "rx-7": "R X seven", "rx7": "R X seven", "rx-8": "R X eight", "s2000": "S two thousand",
    "cvt": "C V T", "abs": "A B S", "ecu": "E C U", "rpm": "R P M", "hp": "horsepower", "mph": "miles per hour",
    "km/h": "kilometres per hour", "dohc": "D O H C", "sohc": "S O H C", "vvt": "V V T", "awd": "all wheel drive",
    "rwd": "rear wheel drive", "fwd": "front wheel drive", "suv": "S U V", "f1": "F one",
}


class NarratorNotConfigured(RuntimeError):
    pass


def _norm(w):
    return re.sub(r"[^a-z0-9'/\-]", "", w.lower()).strip("-'")


def spoken_tokens(text, lexicon=None):
    """Caption tokens -> list of (caption_token, spoken_phrase)."""
    lex = dict(LEXICON)
    lex.update({_norm(k): v for k, v in (lexicon or {}).items()})
    out = []
    for tok in text.split():
        core = _norm(tok)
        if core in lex:
            lead = re.match(r"^[^A-Za-z0-9]*", tok).group(0)
            trail = re.search(r"[^A-Za-z0-9]*$", tok).group(0)
            out.append((tok, lead + lex[core] + trail))
        else:
            out.append((tok, tok))
    return out


def backend():
    return "kokoro" if os.environ.get("EV_VOICE", "").lower() == "kokoro" else "elevenlabs"


def check_configured():
    """Raise NarratorNotConfigured with a clear reason if the narrator can't run."""
    if backend() == "kokoro":
        return
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise NarratorNotConfigured("ELEVENLABS_API_KEY is not set in this environment")
    req = urllib.request.Request(f"{API}/user/subscription", headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            info = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise NarratorNotConfigured(f"ElevenLabs rejected the API key (HTTP {e.code})")
    except Exception as e:  # proxy denial / DNS / timeout
        raise NarratorNotConfigured(f"cannot reach api.elevenlabs.io ({e}); add it to the allowed domains")
    left = info.get("character_limit", 0) - info.get("character_count", 0)
    return {"characters_left": left, "tier": info.get("tier")}


def _post(path, body, accept="application/json"):
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise NarratorNotConfigured("ELEVENLABS_API_KEY is not set in this environment")
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:400]
        if e.code in (401, 403):
            raise NarratorNotConfigured(f"ElevenLabs HTTP {e.code}: {msg}")
        raise RuntimeError(f"ElevenLabs HTTP {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise NarratorNotConfigured(f"cannot reach api.elevenlabs.io ({e.reason}); add it to the allowed domains")


def decode_mp3(data, sr=SR):
    """MP3 bytes -> float32 mono at sr (via ffmpeg)."""
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(sr), "-f", "f32le",
                        "pipe:1"], input=data, capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def _tts(spoken, prev_text, next_text):
    body = {"text": spoken, "model_id": MODEL_ID, "voice_settings": SETTINGS, "seed": 7}
    if prev_text:
        body["previous_text"] = prev_text
    if next_text:
        body["next_text"] = next_text
    res = json.loads(_post(f"/text-to-speech/{VOICE_ID}/with-timestamps?output_format=mp3_44100_128", body))
    audio = decode_mp3(base64.b64decode(res["audio_base64"]))
    al = res.get("alignment") or res.get("normalized_alignment")
    return audio, al


def word_times(pairs, alignment):
    """Map each caption token to (start, end) using the character alignment of the spoken text."""
    chars = alignment["characters"]
    st = alignment["character_start_times_seconds"]
    en = alignment["character_end_times_seconds"]
    spoken = "".join(chars)
    out, pos = [], 0
    for cap, sp in pairs:
        i = spoken.find(sp, pos)
        if i < 0:                       # tolerate small normalisation differences: fall back to a word search
            core = re.sub(r"[^A-Za-z0-9]", "", sp)[:6]
            i = spoken.lower().find(core.lower(), pos) if core else -1
        if i < 0:
            out.append(None)
            continue
        j = i + len(sp) - 1
        # skip punctuation at either end for timing
        while i < j and not chars[i].isalnum():
            i += 1
        while j > i and not chars[j].isalnum():
            j -= 1
        out.append((st[i], en[j]))
        pos = j + 1
    # fill gaps by interpolation
    for k, v in enumerate(out):
        if v is None:
            a = next((out[q][1] for q in range(k - 1, -1, -1) if out[q]), 0.0)
            b = next((out[q][0] for q in range(k + 1, len(out)) if out[q]), a + 0.3)
            out[k] = (a, max(a + 0.05, b))
    return out


def trim_offsets(s, sr, thr=0.01, pre=0.02, post=0.08):
    idx = np.where(np.abs(s) > thr)[0]
    if len(idx) == 0:
        return 0, len(s)
    return max(0, idx[0] - int(pre * sr)), min(len(s), idx[-1] + int(post * sr))


def generate(lines, out_dir, keys=None, force=False, lexicon=None):
    os.makedirs(out_dir, exist_ok=True)
    if backend() == "kokoro":
        return _kokoro_generate(lines, out_dir, keys, force)
    spoken = [" ".join(sp for _, sp in spoken_tokens(text, lexicon)) for _, text in lines]
    total = 0.0
    for n, (key, text) in enumerate(lines):
        if keys and key not in keys:
            continue
        path, meta = os.path.join(out_dir, f"{key}.wav"), os.path.join(out_dir, f"{key}.json")
        prev_t = " ".join(spoken[max(0, n - 2):n])
        next_t = spoken[n + 1] if n + 1 < len(spoken) else ""
        stamp = f"{VOICE_ID}|{MODEL_ID}|{json.dumps(SETTINGS, sort_keys=True)}|{prev_t}|{spoken[n]}|{next_t}"
        if os.path.exists(path) and os.path.exists(meta) and not force:
            try:
                m = json.load(open(meta))
                if m.get("stamp") == stamp and len(m.get("words", [])) == len(text.split()):
                    total += sf.info(path).duration
                    continue
            except Exception:
                pass
        pairs = spoken_tokens(text, lexicon)
        audio, al = _tts(spoken[n], prev_t, next_t)
        wt = word_times(pairs, al)
        a, b = trim_offsets(audio, SR)
        off = a / SR
        audio = audio[a:b]
        dur = len(audio) / SR
        words = [{"w": cap, "start": max(0.0, s - off), "end": min(dur, max(s - off + 0.04, e - off))}
                 for (cap, _), (s, e) in zip(pairs, wt)]
        sf.write(path, audio, SR)
        with open(meta, "w") as fh:
            json.dump({"stamp": stamp, "voice": VOICE_NAME, "spoken": spoken[n], "words": words}, fh, indent=1)
        total += dur
    return total


def phonemes(text, lexicon=None):
    """Show what the narrator will actually be sent for each caption word (pronunciation check)."""
    return " | ".join(f"{c}->{s}" if c != s else c for c, s in spoken_tokens(text, lexicon))


# ------------------------------------------------------------------ local preview only (never publish)
KOKORO_VOICE = "am_michael"
MODEL_DIR = os.path.expanduser("~/.cache/expanded-view/models")
MODEL_URLS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
_k = None


def ensure_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_URLS.items():
        path = os.path.join(MODEL_DIR, name)
        if not os.path.exists(path) or os.path.getsize(path) < 1_000_000:
            tmp = path + ".part"
            subprocess.run(["curl", "-sSL", "--retry", "3", "-o", tmp, url], check=True)
            os.replace(tmp, path)
    return os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin")


def _kokoro_generate(lines, out_dir, keys, force):
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(*ensure_models())
    total = 0.0
    for key, text in lines:
        if keys and key not in keys:
            continue
        path = os.path.join(out_dir, f"{key}.wav")
        meta = os.path.join(out_dir, f"{key}.json")
        stamp = f"kokoro|{KOKORO_VOICE}|{text}"
        if os.path.exists(path) and not force and os.path.exists(meta) and json.load(open(meta)).get("stamp") == stamp:
            total += sf.info(path).duration
            continue
        s, sr = _k.create(text, voice=KOKORO_VOICE, speed=1.0, lang="en-us")
        s = np.asarray(s, np.float32)
        a, b = trim_offsets(s, sr)
        sf.write(path, s[a:b], sr)
        with open(meta, "w") as fh:            # no word times: Timeline estimates them
            json.dump({"stamp": stamp, "voice": "kokoro-preview"}, fh)
        total += (b - a) / sr
    return total
