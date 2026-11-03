"""Long-form (16:9, 1920x1080) builder for Expanded View history / comparison videos.

    python -m ev.long.build long/<slug> --stills 5,60,300      # quick look
    python -m ev.long.build long/<slug>                        # full render -> out/<slug>/<slug>.mp4 + meta.json

Episode folder long/<slug>/:
  episode.py   SLUG, TITLE, LINES [(key, paragraph)], SHOTS {key: [shot, ...]}, CHAPTERS [(key, title)],
               META (title, description, tags, first_comment), optional SAY (pronunciations), SFX [(key, word, kind, gain)]
  research.md  every fact with a source
  assets/      manifest.yaml (licensed sources, see ev/long/assets.py) + cached media

Shots (each starts at line start, or at word `at` in that line, and runs until the next shot):
  {"type": "title", "text": "...", "sub": "..."}                          cold-open / end title
  {"type": "chapter", "no": 2, "title": "THE ENGINE", "asset": id}       chapter card (also a YouTube chapter)
  {"type": "photo", "asset": id, "move": "push|pull|pan_l|pan_r|up|down", "focus": (x, y), "label": "1990 NSX"}
  {"type": "clip", "asset": id, "start": 3.0, "label": "..."}             licensed video clip, muted
  {"type": "specs", "title": "...", "rows": [("Engine", "3.0 V6"), ...], "asset": id (optional backdrop)}
  {"type": "timeline", "title": "...", "items": [("1984", "Project starts"), ...]}
  {"type": "compare", "left": ("BMW M3", id), "right": ("Mercedes E63", id),
                      "rows": [("Power", "473 hp", "603 hp", "R"), ...]}     "L"/"R"/"" marks the better value
  {"type": "fact", "text": "Big statement", "sub": "...", "asset": id (optional backdrop)}
Every photo/clip on screen shows its credit (author, license) bottom-left; the description gets the full list.
"""
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia
import yaml

from .. import voice
from ..gfx import (AMBER, CYAN, GREEN, INK, MUTED, RED, YEL, clamp, draw_text, ease, eout, font, hx, lin,
                   lin_grad, paint, pill, text_w)
from ..timeline import Timeline

W, H = 1920, 1080
FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
XF = 0.45   # cross-fade between shots
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


# ------------------------------------------------------------------ loading
def load_episode(ep_dir):
    ep_dir = os.path.abspath(ep_dir)
    spec = importlib.util.spec_from_file_location("long_episode", os.path.join(ep_dir, "episode.py"))
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    voice.generate(ep.LINES, os.path.join(ep_dir, "vo"), lexicon=getattr(ep, "SAY", None))
    tl = Timeline(ep.LINES, os.path.join(ep_dir, "vo"), gaps=getattr(ep, "GAPS", None) or
                  {k: 0.55 for k, _ in ep.LINES[1:]}, tail=1.5)
    mp = os.path.join(ep_dir, "assets", "manifest.yaml")
    manifest = (yaml.safe_load(open(mp)) or {}) if os.path.exists(mp) else {}
    shots = []
    for key, _ in ep.LINES:
        for sh in ep.SHOTS.get(key, [{"type": "fact", "text": ""}]):
            t0 = tl.find(key, sh["at"]) - 0.15 if sh.get("at") else tl.line(key)["start"] - 0.1
            shots.append(dict(sh, key=key, t0=max(0.0, t0)))
    shots.sort(key=lambda s: s["t0"])
    shots[0]["t0"] = 0.0
    for a, b in zip(shots, shots[1:]):
        a["t1"] = b["t0"]
    shots[-1]["t1"] = tl.total
    return ep, ep_dir, tl, manifest, shots


class Ctx:
    def __init__(self, ep, ep_dir, tl, manifest, shots):
        self.ep, self.ep_dir, self.tl, self.manifest, self.shots = ep, ep_dir, tl, manifest, shots
        self._img = {}
        self._clips = {}

    def image(self, aid):
        if aid not in self._img:
            a = self.manifest[aid]
            data = open(os.path.join(self.ep_dir, a["file"]), "rb").read()
            self._img[aid] = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(data))
        return self._img[aid]

    def clip_frame(self, aid, tt):
        """Sequential clip reader (frames requested in increasing time within a segment)."""
        st = self._clips.get(aid)
        if st is None or tt < st["t"] - 1e-6:
            if st:
                st["p"].kill()
            path = os.path.join(self.ep_dir, self.manifest[aid]["file"])
            p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{max(0.0, tt):.3f}", "-i", path,
                                  "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                                  "-f", "rawvideo", "-pix_fmt", "rgba", "-an", "pipe:1"], stdout=subprocess.PIPE)
            st = self._clips[aid] = {"p": p, "t": tt, "img": None}
            st["img"] = self._read(st)
        while st["t"] + 1 / FPS <= tt + 1e-6:
            nxt = self._read(st)
            if nxt is None:
                break
            st["img"] = nxt
            st["t"] += 1 / FPS
        return st["img"]

    @staticmethod
    def _read(st):
        buf = st["p"].stdout.read(W * H * 4)
        if len(buf) < W * H * 4:
            return st["img"]
        arr = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
        return skia.Image.fromarray(arr.copy(), colorType=skia.kRGBA_8888_ColorType)


# ------------------------------------------------------------------ drawing helpers
BG0, BG1 = hx("#070b12"), hx("#0f1a2c")


def background(cv):
    p = skia.Paint()
    p.setShader(lin_grad((0, 0), (0, H), [BG1, BG0]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)
    gp = paint(hx("#5f8fd6"), a=0.05, stroke=1.2)
    for x in range(0, W + 1, 60):
        cv.drawLine(x, 0, x, H, gp)
    for y in range(0, H + 1, 60):
        cv.drawLine(0, y, W, y, gp)


def cover(cv, img, k, move="push", focus=(0.5, 0.5), alpha=1.0, dim=0.0):
    """Ken Burns: fill the frame with img, slowly moving (k = 0..1 through the shot)."""
    iw, ih = img.width(), img.height()
    base = max(W / iw, H / ih)
    z0, z1, dx, dy = 1.04, 1.16, 0.0, 0.0
    if move == "pull":
        z0, z1 = 1.16, 1.04
    elif move in ("pan_l", "pan_r", "up", "down"):
        z0 = z1 = 1.14
        d = (k - 0.5) * 0.10
        dx = d if move == "pan_l" else (-d if move == "pan_r" else 0.0)
        dy = d if move == "up" else (-d if move == "down" else 0.0)
    z = z0 + (z1 - z0) * ease(k)
    s = base * z
    vw, vh = W / s, H / s
    cx = clamp(focus[0] * iw + dx * iw, vw / 2, iw - vw / 2)
    cy = clamp(focus[1] * ih + dy * ih, vh / 2, ih - vh / 2)
    src = skia.Rect.MakeXYWH(cx - vw / 2, cy - vh / 2, vw, vh)
    pnt = skia.Paint(AntiAlias=True)
    pnt.setAlphaf(clamp(alpha))
    cv.drawImageRect(img, src, skia.Rect.MakeWH(W, H), SAMPLING, pnt)
    if dim > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(hx("#000000"), a=dim * alpha))


def vignette(cv, a=0.55):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75,
                                               [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, a)], [0.55, 1.0]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)


def credit(cv, ctx, aid, a):
    m = ctx.manifest.get(aid, {})
    if not m or m.get("source") == "own" or a <= 0:
        return
    who = m.get("author", "")[:60]
    txt = f"{'Video' if m.get('kind') == 'clip' else 'Photo'}: {who} · {m.get('license', '')}"
    draw_text(cv, txt, 40, H - 34, font("inter_sb", 20), INK, a=0.75 * a, stroke=3, stroke_c=hx("#000000"))


def lower_third(cv, text, k, a):
    if not text or a <= 0:
        return
    f = font("inter_xb", 40)
    w = text_w(text, f, 3) + 70
    x = 80 - (1 - eout(k)) * 60
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, H - 210, w, 76), 12, 12)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.88 * a))
    cv.drawRect(skia.Rect.MakeXYWH(x, H - 210, 8, 76), paint(RED, a=a))
    draw_text(cv, text, x + 36, H - 158, f, INK, a=a, tracking=3)


def brand_mark(cv, a=0.8):
    draw_text(cv, "EXPANDED VIEW", W - 40, 56, font("inter_xb", 22), INK, a=0.55 * a, align="right", tracking=6)


# ------------------------------------------------------------------ shots
def shot_alpha(t, sh):
    a_in = 1.0 if sh["t0"] <= 0 else eout(lin(t, sh["t0"], sh["t0"] + XF))
    return a_in


def draw_shot(cv, t, sh, ctx):
    k = lin(t, sh["t0"], sh["t1"])
    lt = t - sh["t0"]
    typ = sh["type"]
    if typ == "photo":
        cover(cv, ctx.image(sh["asset"]), k, sh.get("move", "push"), sh.get("focus", (0.5, 0.5)))
        vignette(cv, 0.45)
        lower_third(cv, sh.get("label"), lin(lt, 0.3, 0.9), clamp((lt - 0.3) / 0.4) * (1 - lin(t, sh["t1"] - 0.6, sh["t1"])))
        credit(cv, ctx, sh["asset"], 1.0)
    elif typ == "clip":
        img = ctx.clip_frame(sh["asset"], sh.get("start", 0.0) + lt)
        if img is not None:
            cv.drawImage(img, 0, 0)
        vignette(cv, 0.4)
        lower_third(cv, sh.get("label"), lin(lt, 0.3, 0.9), clamp((lt - 0.3) / 0.4))
        credit(cv, ctx, sh["asset"], 1.0)
    elif typ in ("title", "fact", "chapter", "specs", "timeline", "compare"):
        background(cv)
        if sh.get("asset"):
            cover(cv, ctx.image(sh["asset"]), k, sh.get("move", "push"), sh.get("focus", (0.5, 0.5)), dim=0.62)
            credit(cv, ctx, sh["asset"], 1.0)
        vignette(cv, 0.6)
        globals()[f"_draw_{typ}"](cv, t, lt, sh, ctx)
    brand_mark(cv)


def _draw_title(cv, t, lt, sh, ctx):
    k = eout(lin(lt, 0.1, 0.8))
    f = font("pop_b", 110)
    while text_w(sh["text"], f) > W - 200 and f.getSize() > 50:
        f = font("pop_b", f.getSize() - 6)
    draw_text(cv, sh["text"], W / 2, H / 2 + 20 + (1 - k) * 30, f, INK, a=k, align="center")
    if sh.get("sub"):
        ks = eout(lin(lt, 0.6, 1.3))
        draw_text(cv, sh["sub"], W / 2, H / 2 + 100, font("inter_sb", 40), RED, a=ks, align="center", tracking=4)


def _draw_fact(cv, t, lt, sh, ctx):
    if not sh.get("text"):
        return
    k = eout(lin(lt, 0.1, 0.7))
    lines = sh["text"].split("\n")
    f = font("pop_b", 84)
    y0 = H / 2 - (len(lines) - 1) * 50
    for i, ln in enumerate(lines):
        draw_text(cv, ln, W / 2, y0 + i * 100, f, RED if i == len(lines) - 1 and len(lines) > 1 else INK,
                  a=k, align="center")
    if sh.get("sub"):
        draw_text(cv, sh["sub"], W / 2, y0 + len(lines) * 100 + 10, font("inter_sb", 36), MUTED,
                  a=eout(lin(lt, 0.5, 1.1)), align="center", tracking=2)


def _draw_chapter(cv, t, lt, sh, ctx):
    k = eout(lin(lt, 0.1, 0.7))
    draw_text(cv, f"PART {sh['no']}", W / 2, H / 2 - 70, font("inter_xb", 40), RED, a=k, align="center", tracking=12)
    draw_text(cv, sh["title"], W / 2, H / 2 + 50 + (1 - k) * 20, font("pop_b", 110), INK, a=k, align="center")
    cv.drawLine(W / 2 - 160 * k, H / 2 + 100, W / 2 + 160 * k, H / 2 + 100, paint(RED, a=k, stroke=5))


def _draw_specs(cv, t, lt, sh, ctx):
    k = eout(lin(lt, 0.1, 0.6))
    draw_text(cv, sh["title"], 160, 220, font("pop_b", 68), INK, a=k)
    rows = sh["rows"]
    for i, (lab, val) in enumerate(rows):
        kr = eout(lin(lt, 0.5 + 0.35 * i, 0.9 + 0.35 * i))
        y = 330 + i * 105
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(160 - (1 - kr) * 40, y, W - 320, 84), 14, 14)
        cv.drawRRect(rr, paint(hx("#0b111c"), a=0.85 * kr))
        cv.drawRRect(rr, paint(hx("#2a3446"), a=kr, stroke=2))
        draw_text(cv, lab.upper(), 200, y + 54, font("inter_xb", 32), MUTED, a=kr, tracking=3)
        draw_text(cv, val, W - 200, y + 56, font("inter_blk", 44), YEL if i == sh.get("highlight") else INK, a=kr,
                  align="right")


def _draw_timeline(cv, t, lt, sh, ctx):
    k = eout(lin(lt, 0.1, 0.6))
    draw_text(cv, sh["title"], 160, 200, font("pop_b", 64), INK, a=k)
    items = sh["items"]
    n = len(items)
    x0, x1, y = 200, W - 200, 560
    prog = clamp(lin(lt, 0.4, 0.4 + 0.6 * n))
    cv.drawLine(x0, y, x1, y, paint(hx("#2a3446"), stroke=6))
    cv.drawLine(x0, y, x0 + (x1 - x0) * prog, y, paint(RED, stroke=6))
    for i, (yr, txt) in enumerate(items):
        x = x0 + (x1 - x0) * (i / max(1, n - 1))
        ki = eout(lin(lt, 0.4 + 0.6 * i, 0.8 + 0.6 * i))
        cv.drawCircle(x, y, 14 * ki, paint(RED if ki > 0.5 else MUTED))
        draw_text(cv, yr, x, y - 40, font("inter_blk", 44), INK, a=ki, align="center")
        words, lines, cur = txt.split(), [], ""
        for w in words:
            if len(cur + " " + w) > 18 and cur:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        for j, ln in enumerate(lines[:4]):
            draw_text(cv, ln, x, y + 70 + j * 40, font("inter_sb", 28), MUTED, a=ki, align="center")


def _draw_compare(cv, t, lt, sh, ctx):
    (ln, la), (rn, ra) = sh["left"], sh["right"]
    k = eout(lin(lt, 0.1, 0.7))
    for side, (name, aid) in enumerate(((ln, la), (rn, ra))):
        x = 0 if side == 0 else W / 2
        cv.save()
        cv.clipRect(skia.Rect.MakeXYWH(x, 0, W / 2, 470))
        if aid:
            img = ctx.image(aid)
            iw, ih = img.width(), img.height()
            s = max((W / 2) / iw, 470 / ih) * (1.04 + 0.06 * lin(t, sh["t0"], sh["t1"]))
            dst = skia.Rect.MakeXYWH(x + W / 4 - iw * s / 2, 235 - ih * s / 2, iw * s, ih * s)
            pnt = skia.Paint(AntiAlias=True)
            pnt.setAlphaf(k)
            cv.drawImageRect(img, dst, SAMPLING, pnt)
        cv.restore()
        draw_text(cv, name.upper(), x + W / 4, 520, font("pop_b", 52), CYAN if side == 0 else RED, a=k, align="center")
    cv.drawLine(W / 2, 0, W / 2, 470, paint(hx("#000000"), stroke=6))
    for i, (lab, lv, rv, better) in enumerate(sh["rows"]):
        kr = eout(lin(lt, 0.8 + 0.4 * i, 1.2 + 0.4 * i))
        y = 600 + i * 78
        draw_text(cv, lab.upper(), W / 2, y + 40, font("inter_xb", 26), MUTED, a=kr, align="center", tracking=3)
        draw_text(cv, lv, W / 2 - 260, y + 44, font("inter_blk", 40), GREEN if better == "L" else INK, a=kr, align="right")
        draw_text(cv, rv, W / 2 + 260, y + 44, font("inter_blk", 40), GREEN if better == "R" else INK, a=kr)
    used = [a for _, a in (sh["left"], sh["right"]) if a]
    if used:
        m = [ctx.manifest[a] for a in used if a in ctx.manifest and ctx.manifest[a].get("source") != "own"]
        txt = " | ".join(f"{x['author'][:40]} · {x['license']}" for x in m)
        if txt:
            draw_text(cv, f"Photos: {txt}", 40, H - 34, font("inter_sb", 18), INK, a=0.7, stroke=3, stroke_c=hx("#000000"))


def draw_frame(cv, t, ctx):
    cur = [s for s in ctx.shots if s["t0"] <= t < s["t1"] + XF]
    if not cur:
        cur = [ctx.shots[-1]]
    for i, sh in enumerate(cur):
        a = 1.0 if i == 0 else shot_alpha(t, sh)
        if a >= 1.0 or i == 0:
            draw_shot(cv, t, sh, ctx)
        else:
            cv.saveLayerAlpha(None, int(255 * a))
            draw_shot(cv, t, sh, ctx)
            cv.restore()
    # fade from / to black
    fb = max(1 - lin(t, 0, 0.6), lin(t, ctx.tl.total - 0.8, ctx.tl.total))
    if fb > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(hx("#000000"), a=fb))


# ------------------------------------------------------------------ render
def render_range(ep_dir, out_path, f0, f1):
    ctx = Ctx(*load_episode(ep_dir))
    surf = skia.Surface.MakeRaster(INFO)
    cv = surf.getCanvas()
    buf = np.empty((H, W, 4), np.uint8)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "60",
           out_path + ".tmp.mp4"]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        cv.clear(skia.ColorBLACK)
        draw_frame(cv, f / FPS, ctx)
        cv.readPixels(INFO, buf)
        pr.stdin.write(buf.tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        raise RuntimeError("segment encode failed")
    os.replace(out_path + ".tmp.mp4", out_path)


def chapters(ep, tl):
    out = [("0:00", "Intro")]
    for key, title in getattr(ep, "CHAPTERS", []):
        s = int(tl.line(key)["start"])
        out.append((f"{s // 60}:{s % 60:02d}", title))
    if len(out) > 1 and out[1][0] == "0:00":
        out = out[1:]
    return out


def write_srt(tl, path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as fh:
        for i, c in enumerate(tl.chunks, 1):
            fh.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w['w'] for w in c['words'])}\n\n")


def build(ep_dir, jobs=2):
    t0 = time.time()
    ep, ep_dir, tl, manifest, shots = load_episode(ep_dir)
    print(tl.report(), flush=True)
    used = sorted({s[k] for s in shots for k in ("asset",) if s.get(k)} |
                  {a for s in shots if s["type"] == "compare" for _, a in (s["left"], s["right"]) if a})
    missing = [a for a in used if a not in manifest]
    if missing:
        raise SystemExit(f"assets not in manifest: {missing}")
    from .assets import credits, license_ok
    bad = [a for a in used if manifest[a]["source"] != "own" and not (license_ok(manifest[a]["license"]) or
                                                                       manifest[a]["source"] == "pexels")]
    if bad:
        raise SystemExit(f"assets without a free license: {bad}")
    out_dir = os.path.join(ROOT, "out", ep.SLUG)
    os.makedirs(out_dir, exist_ok=True)
    nfr = int(round(tl.total * FPS))
    nseg = max(jobs * 4, 8)
    edges = [int(nfr * i / nseg) for i in range(nseg + 1)]
    segs = [(f"{out_dir}/seg_{i:03d}.mp4", edges[i], edges[i + 1]) for i in range(nseg)]
    procs = []
    for w in range(jobs):
        mine = ",".join(str(i) for i in range(w, nseg, jobs))
        procs.append(subprocess.Popen([sys.executable, "-m", "ev.long.build", ep_dir, "--worker", out_dir, mine,
                                       str(nfr), str(nseg)], cwd=ROOT))
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError("render worker failed")
    with open(f"{out_dir}/concat.txt", "w") as fh:
        fh.writelines(f"file '{os.path.basename(s[0])}'\n" for s in segs)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{out_dir}/concat.txt",
                    "-c", "copy", f"{out_dir}/video_only.mp4"], check=True)
    from ..audio import build_mix
    plan = {"sfx": [(tl.find(k, w), kind, g) for k, w, kind, g in getattr(ep, "SFX", [])],
            "music_gain": 0.55, "_ep_dir": ep_dir, "_prompts": getattr(ep, "SFX_PROMPTS", None)}
    build_mix(tl, plan, f"{out_dir}/mix.wav", tl.line(ep.LINES[0][0])["start"], tl.total - 0.4, tl.total + 5,
              beat_anchor=None)
    from ..build import _loudnorm
    final = f"{out_dir}/{ep.SLUG}.mp4"
    _loudnorm(f"{out_dir}/video_only.mp4", f"{out_dir}/mix.wav", final)
    write_srt(tl, f"{out_dir}/{ep.SLUG}.srt")
    dur = tl.total
    problems = []
    if voice.backend() != "elevenlabs":
        problems.append("preview voice: publishing requires the ElevenLabs narrator")
    if not 480 <= dur <= 760:
        problems.append(f"duration {dur:.0f}s outside 8-12 min")
    lo = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-af", "ebur128", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    lufs = next((float(l.split()[1]) for l in lo.splitlines()[::-1] if l.strip().startswith("I:")), None)
    if lufs is None or abs(lufs + 14) > 1.5:
        problems.append(f"loudness {lufs}")
    ch = chapters(ep, tl)
    meta = dict(getattr(ep, "META", {}))
    desc = meta.get("description", "")
    desc += "\n\nChapters:\n" + "\n".join(f"{a} {b}" for a, b in ch)
    cr = credits(ep_dir, used)
    if cr:
        desc += "\n\n" + cr
    meta.update({"description": desc, "slug": ep.SLUG, "file": final, "srt": f"{out_dir}/{ep.SLUG}.srt",
                 "duration": round(dur, 1), "lufs": lufs, "problems": problems})
    json.dump(meta, open(f"{out_dir}/meta.json", "w"), indent=2)
    sheet(final, out_dir, dur)
    for s in segs:
        os.remove(s[0])
    print(json.dumps({"ok": not problems, "duration": round(dur, 1), "lufs": lufs, "problems": problems,
                      "sheet": f"{out_dir}/qa_sheet.jpg", "seconds": round(time.time() - t0)}, indent=2))
    return not problems


def sheet(video, out_dir, dur, n=12):
    from PIL import Image
    ims = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        p = f"{out_dir}/_q{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", "scale=480:270", p], check=True)
        ims.append(Image.open(p).copy())
        os.remove(p)
    sh = Image.new("RGB", (480 * 4, 270 * 3))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % 4) * 480, (i // 4) * 270))
    sh.save(f"{out_dir}/qa_sheet.jpg", quality=85)


def stills(ep_dir, times):
    ctx = Ctx(*load_episode(ep_dir))
    out_dir = os.path.join(ROOT, "out", ctx.ep.SLUG)
    os.makedirs(out_dir, exist_ok=True)
    surf = skia.Surface.MakeRaster(INFO)
    cv = surf.getCanvas()
    for t in times:
        cv.clear(skia.ColorBLACK)
        draw_frame(cv, t, ctx)
        p = f"{out_dir}/still_{t:07.2f}.jpg"
        surf.makeImageSnapshot().save(p, skia.kJPEG, 88)
        print(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--stills")
    ap.add_argument("--worker", nargs=4)
    a = ap.parse_args()
    if a.worker:
        out_dir, mine, nfr, nseg = a.worker
        nfr, nseg = int(nfr), int(nseg)
        edges = [int(nfr * i / nseg) for i in range(nseg + 1)]
        for i in map(int, mine.split(",")):
            render_range(a.episode, f"{out_dir}/seg_{i:03d}.mp4", edges[i], edges[i + 1])
        return
    if a.stills:
        stills(a.episode, [float(x) for x in a.stills.split(",")])
        return
    sys.exit(0 if build(a.episode, a.jobs) else 2)


if __name__ == "__main__":
    main()
