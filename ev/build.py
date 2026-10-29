"""Build an episode:  python -m ev.build episodes/<slug> [--stills 1.2,30.5] [--jobs 2]

Pipeline: narration (fixed voice) -> word timeline -> frames (brand + episode scene) -> soundtrack
-> loudness-normalized MP4 (-14 LUFS) -> QA contact sheet + checks -> meta.json for posting.
Outputs go to out/<slug>/.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

import numpy as np
import skia

from . import brand, current, voice
from .gfx import W, H
from .timeline import Timeline

FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def prepare(ep_dir):
    ep_dir = os.path.abspath(ep_dir)
    if ep_dir not in sys.path:
        sys.path.insert(0, ep_dir)
    ep = _load(os.path.join(ep_dir, "episode.py"), "episode")
    vo_dir = os.path.join(ep_dir, "vo")
    voice.generate(ep.LINES, vo_dir)
    tl = Timeline(ep.LINES, vo_dir, gaps=getattr(ep, "GAPS", None))
    current.tl, current.ep = tl, ep
    current.t_end = tl.find(*ep.END_WORD) - 0.15
    current.t_topic = tl.find(*ep.TOPIC_WORD) - 0.2
    current.hook_out = getattr(ep, "HOOK_OUT", None) or (tl.line(ep.LINES[0][0])["end"] - 0.44)
    scene = _load(os.path.join(ep_dir, "scene.py"), "scene")
    return ep, tl, scene


def draw_frame(cv, t, ep, tl, scene):
    cv.drawImage(brand.background(), 0, 0)
    scene.draw(cv, t)
    if getattr(ep, "HOOK_TITLE", None):
        brand.hook_title(cv, t, ep.HOOK_TITLE, current.hook_out)
    brand.end_card(cv, t, ep.PUNCH, ep.TOPIC, getattr(ep, "SUBTITLE", None), current.t_end, current.t_topic)
    brand.captions(cv, t, tl, current.t_end - 0.05)


def cuts(ep, tl):
    c = [0.0] + [tl.line(k)["start"] - 0.02 for k, _ in ep.LINES[1:]] + [tl.total]
    return c


def render_segments(ep_dir, out_dir, idxs):
    ep, tl, scene = prepare(ep_dir)
    cs = cuts(ep, tl)
    surf = skia.Surface.MakeRaster(INFO)
    cv = surf.getCanvas()
    buf = np.empty((H, W, 4), np.uint8)
    for i in idxs:
        f0, f1 = int(round(cs[i] * FPS)), int(round(cs[i + 1] * FPS))
        tmp, final = f"{out_dir}/seg_{i:02d}.tmp.mp4", f"{out_dir}/seg_{i:02d}.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
               "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "60", "-bf", "2",
               "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", tmp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(f0, f1):
            cv.clear(skia.ColorBLACK)
            draw_frame(cv, f / FPS, ep, tl, scene)
            cv.readPixels(INFO, buf)
            pr.stdin.write(buf.tobytes())
        pr.stdin.close()
        if pr.wait() == 0:
            os.replace(tmp, final)
        else:
            raise RuntimeError(f"segment {i} failed")


def stills(ep_dir, times, out_dir):
    ep, tl, scene = prepare(ep_dir)
    surf = skia.Surface.MakeRaster(INFO)
    cv = surf.getCanvas()
    paths = []
    for t in times:
        cv.clear(skia.ColorBLACK)
        draw_frame(cv, t, ep, tl, scene)
        p = f"{out_dir}/still_{t:06.2f}.jpg"
        surf.makeImageSnapshot().save(p, skia.kJPEG, 90)
        paths.append(p)
    return paths


def _loudnorm(video, wav, out):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    d = json.loads(txt)
    mi = (f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:"
          f"measured_thresh={d['input_thresh']}:offset={d['target_offset']}")
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:{mi}:linear=true,aresample=48000",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", tmp],
                   check=True)
    os.replace(tmp, out)


def qa(out_mp4, ep, tl, out_dir):
    """Checks + a 12-frame contact sheet. Returns (ok, report)."""
    from PIL import Image, ImageDraw
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out_mp4],
                        capture_output=True, text=True)
    dur = float(pr.stdout.strip())
    lo = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out_mp4, "-af", "ebur128", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    lufs = None
    for line in lo.splitlines()[::-1]:
        if line.strip().startswith("I:"):
            lufs = float(line.split()[1])
            break
    problems = []
    if dur < 61:
        problems.append(f"duration {dur:.1f}s < 61s (TikTok Creator Rewards only pays for videos over 1 minute)")
    if dur > 80:
        problems.append(f"duration {dur:.1f}s > 80s (house style is 61-75 s)")
    if lufs is None or abs(lufs + 14) > 1.5:
        problems.append(f"loudness {lufs} LUFS (target -14)")
    # contact sheet: start, each line's midpoint, end card, topic title
    times = [0.5] + [(tl.line(k)["start"] + tl.line(k)["end"]) / 2 for k, _ in ep.LINES]
    times += [current.t_end + 0.6, min(tl.total - 0.2, current.t_topic + 0.8)]
    times = sorted(set(round(x, 2) for x in times))[:16]
    cols = 6
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 500), "black")
    for i, t in enumerate(times):
        fp = f"{out_dir}/qa_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", out_mp4, "-frames:v", "1",
                        "-vf", "scale=270:480", fp], check=True)
        im = Image.open(fp)
        x, y = (i % cols) * 270, (i // cols) * 500
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + 482), f"{t:.1f}s", fill="white")
        os.remove(fp)
    sheet_path = f"{out_dir}/qa_sheet.jpg"
    sheet.save(sheet_path, quality=88)
    rep = {"duration": round(dur, 2), "lufs": lufs, "problems": problems, "sheet": sheet_path}
    return not problems, rep


def build(ep_dir, jobs=2):
    t0 = time.time()
    ep, tl, scene = prepare(ep_dir)
    print(tl.report(), flush=True)
    slug = ep.SLUG
    out_dir = os.path.join(ROOT, "out", slug)
    os.makedirs(out_dir, exist_ok=True)
    cs = cuts(ep, tl)
    nseg = len(cs) - 1
    # longest segments first, spread over workers
    order = sorted(range(nseg), key=lambda i: -(cs[i + 1] - cs[i]))
    groups = [order[k::jobs] for k in range(jobs)]
    procs = [subprocess.Popen([sys.executable, "-m", "ev.build", ep_dir, "--worker", out_dir, ",".join(map(str, g))],
                              cwd=ROOT) for g in groups if g]
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError("render worker failed")
    with open(f"{out_dir}/concat.txt", "w") as fh:
        for i in range(nseg):
            fh.write(f"file 'seg_{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{out_dir}/concat.txt",
                    "-c", "copy", f"{out_dir}/video_only.mp4"], check=True)
    from .audio import build_mix
    plan = scene.sound() if hasattr(scene, "sound") else {}
    music_start = getattr(scene, "MUSIC_START", None) or tl.line(ep.LINES[1][0])["start"]
    build_mix(tl, plan, f"{out_dir}/mix.wav", music_start, current.t_end, current.t_topic,
              beat_anchor=getattr(scene, "BEAT_ANCHOR", None))
    final = f"{out_dir}/{slug}.mp4"
    _loudnorm(f"{out_dir}/video_only.mp4", f"{out_dir}/mix.wav", final)
    ok, rep = qa(final, ep, tl, out_dir)
    meta = dict(getattr(ep, "META", {}))
    meta.update({"slug": slug, "topic": ep.TOPIC, "file": final, "qa": rep})
    with open(f"{out_dir}/meta.json", "w") as fh:
        json.dump(meta, fh, indent=2)
    for f in os.listdir(out_dir):
        if f.startswith("seg_") or f in ("concat.txt",):
            os.remove(os.path.join(out_dir, f))
    print(json.dumps({"ok": ok, **rep, "seconds": round(time.time() - t0)}, indent=2))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--stills", default=None, help="comma-separated times; renders JPGs only")
    ap.add_argument("--worker", nargs=2, default=None)
    a = ap.parse_args()
    if a.worker:
        render_segments(a.episode, a.worker[0], [int(x) for x in a.worker[1].split(",")])
        return
    if a.stills is not None:
        ep, tl, scene = prepare(a.episode)
        print(tl.report())
        out = os.path.join(ROOT, "out", ep.SLUG)
        os.makedirs(out, exist_ok=True)
        times = [float(x) for x in a.stills.split(",") if x]
        for p in stills(a.episode, times, out):
            print(p)
        return
    sys.exit(0 if build(a.episode, a.jobs) else 2)


if __name__ == "__main__":
    main()
