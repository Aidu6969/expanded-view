"""Make the tighter YouTube cut of a built Short by dropping whole narration beats.

    python tools/yt_cut.py episodes/<slug>            # drops episode.YT_DROP, writes out/<slug>/<slug>_yt.mp4
    python tools/yt_cut.py episodes/<slug> --drop light,math

Why: TikTok only pays for videos over 1 minute, but YouTube Shorts rewards the share of the video people watch.
The YouTube version can skip beats that are nice-to-have (target 40-50 s). Cuts land exactly on line
boundaries (same cut points the renderer uses), so captions never get chopped; each joint gets a 40 ms audio
fade. The hook, the key beat and the outro are never dropped.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PROTECTED = {"hook", "key", "outro"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--drop", default=None)
    a = ap.parse_args()
    ep_dir = os.path.abspath(a.episode)
    spec = importlib.util.spec_from_file_location("episode", os.path.join(ep_dir, "episode.py"))
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    drop = [x for x in (a.drop.split(",") if a.drop else getattr(ep, "YT_DROP", [])) if x]
    bad = [d for d in drop if d in PROTECTED or d not in dict(ep.LINES)]
    if bad:
        sys.exit(f"cannot drop {bad}: unknown or protected beat")
    if not drop:
        sys.exit("nothing to drop (set YT_DROP in episode.py or pass --drop)")
    from ev.timeline import Timeline
    tl = Timeline(ep.LINES, os.path.join(ep_dir, "vo"), gaps=getattr(ep, "GAPS", None))
    keys = [k for k, _ in ep.LINES]
    bounds = [0.0] + [tl.line(k)["start"] - 0.02 for k in keys[1:]] + [tl.total]
    keep = [(bounds[i], bounds[i + 1]) for i, k in enumerate(keys) if k not in drop]
    merged = []
    for s, e in keep:
        if merged and abs(merged[-1][1] - s) < 1e-6:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    src = os.path.join(ROOT, "out", ep.SLUG, f"{ep.SLUG}.mp4")
    out = os.path.join(ROOT, "out", ep.SLUG, f"{ep.SLUG}_yt.mp4")
    tmp = []
    for i, (s, e) in enumerate(merged):
        d = e - s
        seg = os.path.join(ROOT, "out", ep.SLUG, f"_ytseg{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.3f}", "-i", src, "-t", f"{d:.3f}",
                        "-af", f"afade=t=in:st=0:d=0.04,afade=t=out:st={max(0, d - 0.04):.3f}:d=0.04",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", seg], check=True)
        tmp.append(seg)
    lst = os.path.join(ROOT, "out", ep.SLUG, "_ytlist.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in tmp)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    for p in tmp + [lst]:
        os.remove(p)
    dur = sum(e - s for s, e in merged)
    print(json.dumps({"file": out, "duration": round(dur, 2), "dropped": drop}))


if __name__ == "__main__":
    main()
