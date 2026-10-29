"""Soundtrack: narration + synthesized music bed + SFX + optional engine note. Loudness: -14 LUFS (done at mux).

Episodes return a plan from scene.sound():
  {
    "build": (t0, t1),            # optional: beat intensifies (e.g. while something winds up)
    "drop":  (t1, t2),            # optional: full groove (e.g. after the key moment)
    "sfx": [(t, kind, gain), ...] # kinds: impact, whoosh_up, whoosh_down, clunk, tick, spool, hiss
    "engine": {                   # optional engine note that follows an RPM curve
        "rpm": callable t->rpm, "bright": callable t->0..1 (harder timbre), "env": [(t, level), ...]
    },
  }
The brand adds automatically: music from the 2nd line to the end card, a whoosh into the end card and
the final impact on the topic title.
"""
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
_rng = np.random.default_rng(7)


def _place(buf, x, start, gain=1.0):
    i = int(round(start * SR))
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += gain * x[:n]


def _env_ad(n, a, d):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    e[na:] = np.exp(-np.arange(n - na) / (d * SR))
    return e


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, x)


# ------------------------------------------------------------------ instruments
def kick():
    n = int(0.42 * SR)
    tt = np.arange(n) / SR
    f = 46 + 110 * np.exp(-tt / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.16)
    x += 0.25 * hp(_rng.standard_normal(n), 3000) * np.exp(-tt / 0.004)
    return x


def hat(dec=0.035):
    n = int(0.15 * SR)
    return 0.6 * hp(_rng.standard_normal(n), 7000, 4) * np.exp(-np.arange(n) / (dec * SR))


def bass(f0, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f0 * tt) + 0.22 * np.sin(4 * np.pi * f0 * tt)) * _env_ad(n, 0.008, 0.32)


def pad(freqs, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.6, 0.6):
            x += np.sin(2 * np.pi * (f + det) * tt + _rng.uniform(0, 6.28))
    a = np.minimum(1, tt / 0.6) * np.minimum(1, (dur - tt) / 0.6)
    return x * a / (2 * len(freqs))


PROG = [(55.00, [220.0, 261.63, 329.63]), (43.65, [174.61, 220.0, 261.63]),
        (65.41, [196.0, 261.63, 329.63]), (49.00, [196.0, 246.94, 293.66])]


# ------------------------------------------------------------------ sfx
def whoosh(dur=0.6, f0=300, f1=3500):
    n = int(dur * SR)
    tt = np.arange(n) / n
    x = _rng.standard_normal(n)
    out = np.zeros(n)
    for i in range(0, n, 1024):
        fc = f0 * (f1 / f0) ** tt[i]
        out[i:i + 1024] = bp(x[i:i + 1024], fc * 0.6, min(fc * 1.6, 20000))
    return out * np.sin(np.pi * tt) ** 2


def impact(dur=1.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 38 + 70 * np.exp(-tt / 0.08)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.45)
    x += 0.35 * lp(_rng.standard_normal(n), 1800) * np.exp(-tt / 0.12)
    x += 0.08 * hp(_rng.standard_normal(n), 4000) * np.exp(-tt / 0.5)
    return x


def clunk():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    x = 0.7 * np.sin(2 * np.pi * 130 * tt) * np.exp(-tt / 0.05)
    for f, d, a in ((2150, 0.03, 0.35), (3420, 0.022, 0.25), (5100, 0.015, 0.15)):
        x += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d)
    x += 0.2 * hp(_rng.standard_normal(n), 2500) * np.exp(-tt / 0.006)
    return x


def tick():
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt / 0.012)


def spool(dur=1.8, f0=600, f1=4200):
    """Rising turbine whine (turbochargers, fans, motors)."""
    n = int(dur * SR)
    tt = np.arange(n) / n
    f = f0 + (f1 - f0) * tt ** 1.6
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + 0.15 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x += 0.25 * bp(_rng.standard_normal(n), 1500, 6000)
    return x * np.minimum(1, tt * 6) * np.minimum(1, (1 - tt) * 8)


def hiss(dur=0.5):
    """Air/steam release (blow-off valves, pneumatics)."""
    n = int(dur * SR)
    tt = np.arange(n) / n
    return bp(_rng.standard_normal(n), 2500, 9000) * np.exp(-tt * 3.5) * np.minimum(1, tt * 40)


SFX = {
    "impact": lambda: impact(), "impact_long": lambda: impact(2.2),
    "whoosh_up": lambda: whoosh(0.6, 300, 3000), "whoosh_down": lambda: whoosh(0.6, 3000, 300),
    "whoosh_big": lambda: whoosh(0.75, 250, 4200),
    "clunk": clunk, "tick": tick, "spool": spool, "hiss": hiss,
}


# ------------------------------------------------------------------ mix
def build_mix(tl, plan, out_wav, music_start, t_end, t_topic, beat_anchor=None):
    T = tl.total
    N = int(T * SR)
    t = np.arange(N) / SR

    vo = np.zeros(N)
    for key, _ in tl.LINES:
        x, sr = sf.read(f"{tl.vo_dir}/{key}.wav")
        if x.ndim > 1:
            x = x.mean(1)
        _place(vo, signal.resample_poly(x, SR, sr), tl.line(key)["start"])
    vo = vo + 0.25 * hp(vo, 2500)
    vo /= np.max(np.abs(vo)) + 1e-9
    vo *= 0.85
    act = lp(np.abs(vo), 6.0, 1)
    act = np.clip(act / (np.percentile(act[act > 1e-3], 60) + 1e-9), 0, 1)

    # music bed
    beat = 60 / 110
    build = plan.get("build")
    drop = plan.get("drop")
    anchor = beat_anchor if beat_anchor is not None else (drop[0] if drop else music_start)
    grid0 = anchor - beat * round(anchor / beat)
    bar = 4 * beat
    drums, bassl, pads = np.zeros(N), np.zeros(N), np.zeros(N)
    K, Hh = kick(), hat()
    tb = grid0 + bar * np.ceil((music_start - 0.05 - grid0) / bar)
    end_beat = t_end - 0.05
    b = 0
    while tb < end_beat:
        root, chord = PROG[b % 4]
        _place(pads, pad(chord, bar + 0.3), tb)
        for i in range(4):
            tk = tb + i * beat
            if tk >= end_beat:
                break
            in_build = bool(build) and build[0] <= tk < build[1]
            in_drop = bool(drop) and drop[0] <= tk < drop[1]
            bk = (tk - build[0]) / max(1e-6, build[1] - build[0]) if in_build else 0
            if (i in (0, 2)) or in_build or in_drop:
                g = 0.95 if in_drop else (0.5 + 0.4 * bk if in_build else 0.55)
                _place(drums, K, tk, g)
            _place(drums, Hh, tk + beat / 2, 0.55 if in_drop else 0.35)
            if in_build or in_drop:
                gh = 0.18 + 0.2 * (1.0 if in_drop else bk)
                _place(drums, Hh, tk + beat / 4, gh)
                _place(drums, Hh, tk + 3 * beat / 4, gh)
            _place(bassl, bass(root, beat * 0.95), tk, 0.9 if (in_drop or in_build) else 0.7)
            if in_drop:
                _place(bassl, bass(root, beat * 0.45), tk + beat / 2, 0.5)
        tb += bar
        b += 1
    music = drums * 0.55 + bassl * 0.55 + pads * 0.16
    if drop:
        t_rise = max(music_start, drop[0] - 5.9)
        n_r = int((drop[0] - t_rise) * SR)
        if n_r > SR:
            tr = np.arange(n_r) / n_r
            nz = _rng.standard_normal(n_r)
            riser = np.zeros(n_r)
            for i in range(0, n_r, 2048):
                fc = 400 + 5200 * tr[i] ** 2
                riser[i:i + 2048] = bp(nz[i:i + 2048], fc * 0.7, min(fc * 1.4, 20000))
            riser *= tr ** 2 * 0.5
            riser += 0.12 * np.sin(2 * np.pi * np.cumsum(180 + 520 * tr ** 2) / SR) * tr ** 2
            _place(music, riser, t_rise, 0.45)

    # sfx (episode cues + fixed ending)
    sfx = np.zeros(N)
    cues = list(plan.get("sfx", []))
    cues += [(t_end - 0.25, "whoosh_up", 0.35), (t_topic + 0.05, "impact_long", 0.5)]
    for cue in cues:
        tt_, kind, g = cue[0], cue[1], (cue[2] if len(cue) > 2 else 0.5)
        _place(sfx, SFX[kind](), tt_, g)

    # engine note
    eng = np.zeros(N)
    e = plan.get("engine")
    if e:
        ts = t[::48]
        rpm = np.interp(t, ts, np.array([e["rpm"](x) for x in ts]))
        vt = np.interp(t, ts, np.array([e.get("bright", lambda _: 0.0)(x) for x in ts]))
        ph = 2 * np.pi * np.cumsum(rpm / 60.0) / SR
        orders = {0.5: 0.12, 1.0: 0.18, 1.5: 0.1, 2.0: 1.0, 3.0: 0.25, 4.0: 0.45, 5.0: 0.12, 6.0: 0.3, 8.0: 0.18, 10.0: 0.1}
        for o, a in orders.items():
            eng += a * (1.0 + (1.6 if o >= 4 else 0.3) * vt) * np.sin(o * ph + o * 1.3)
        eng += bp(_rng.standard_normal(N), 500, 3500) * (0.5 + 0.5 * np.cos(2 * ph)) ** 3 * (0.6 + 1.2 * vt)
        eng = lp(np.tanh(0.8 * eng), 5500)
        keys = e.get("env", [(0, 0.3), (T, 0.3)])
        eng *= np.interp(t, [k[0] for k in keys], [k[1] for k in keys]) * (0.55 + 0.45 * np.clip(rpm / 7300, 0, 1))

    music_env = np.interp(t, [0, music_start - 0.25, music_start + 0.35, T - 1.0, T], [0.0, 0.0, 1.0, 1.0, 0.0])
    mix = vo + music * 0.16 * (1 - 0.55 * act) * music_env + eng * 0.16 * (1 - 0.45 * act) + sfx * 0.42
    mix = lp(mix, 16000, 2)
    fade = np.ones(N)
    fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR))
    mix *= fade
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89
    sf.write(out_wav, np.stack([mix, mix], 1), SR, subtype="PCM_24")
    return out_wav
