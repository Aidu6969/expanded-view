"""Voice-over placement, word timings and caption chunks (global seconds).

The whole video is timed off the narration: every visual cue should be tied to a word time
via `tl.find(line_key, word)` rather than a hard-coded second.
"""
import math
import os
import re
from functools import lru_cache

import numpy as np
import soundfile as sf

FPS = 30
DEFAULT_GAP = 0.22


def _pauses(s, sr):
    hop = int(0.01 * sr)
    n = len(s) // hop
    rms = np.array([np.sqrt(np.mean(s[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    thr = max(0.006, 0.06 * np.percentile(rms, 95))
    sil = rms < thr
    runs, i = [], 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            if j - i >= 9 and i > 0 and j < n:
                runs.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return runs


def _weight(w):
    core = re.sub(r"[^A-Za-z0-9']", "", w)
    if core.isupper() and 2 <= len(core) <= 5:      # acronyms are spelled/said slower
        return len(core) * 1.2 + 1.5
    return len(core) + 1.5


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


class Timeline:
    """lines: [(key, text), ...]; vo_dir holds <key>.wav for each line."""

    def __init__(self, lines, vo_dir, gaps=None, first=0.10, tail=0.85):
        self.LINES = list(lines)
        self.vo_dir = vo_dir
        self.gaps = dict(gaps or {})
        self.first = first
        self.lines, self.words = {}, []
        self._build()
        last = self.LINES[-1][0]
        self.total = math.ceil((self.lines[last]["end"] + tail) * FPS) / FPS
        self.chunks = self._chunks()

    # ------------------------------------------------------------------ build
    def _build(self):
        t = self.first
        for idx, (key, text) in enumerate(self.LINES):
            if idx > 0:
                t += self.gaps.get(key, DEFAULT_GAP)
            s, sr = sf.read(os.path.join(self.vo_dir, f"{key}.wav"))
            if s.ndim > 1:
                s = s.mean(1)
            dur = len(s) / sr
            runs = _pauses(s, sr)
            toks = text.split()
            bidx = [i for i, w in enumerate(toks[:-1]) if re.search(r"[.,?:;!]$", w)]
            wts = [_weight(w) for w in toks]
            tot = sum(wts)
            cum = np.cumsum(wts)
            exp_b = [cum[i] / tot * dur for i in bidx]
            m, n = len(exp_b), len(runs)

            @lru_cache(None)
            def best(i, j):
                if i == m:
                    return 0.0, ()
                c0, a0 = best(i + 1, j)
                opt = (c0 + 0.35, (None,) + a0)
                for k in range(j, n):
                    mid = (runs[k][0] + runs[k][1]) / 2
                    ck, ak = best(i + 1, k + 1)
                    c = ck + (mid - exp_b[i]) ** 2 - 0.15 * (runs[k][1] - runs[k][0])
                    if c < opt[0]:
                        opt = (c, (k,) + ak)
                return opt

            _, assign = best(0, 0)
            bounds = [None if k is None else runs[k] for k in assign]
            for i, bnd in enumerate(bounds):
                if bnd is None:
                    lo_t = bounds[i - 1][1] if i > 0 and bounds[i - 1] else 0.0
                    lo_w = cum[bidx[i - 1]] if i > 0 else 0.0
                    hi_i = next((k for k in range(i + 1, m) if bounds[k]), None)
                    hi_t = bounds[hi_i][0] if hi_i is not None else dur
                    hi_w = cum[bidx[hi_i]] if hi_i is not None else tot
                    x = lo_t + (hi_t - lo_t) * (cum[bidx[i]] - lo_w) / max(1e-6, hi_w - lo_w)
                    bounds[i] = (x, x)
            edges = [0.0]
            for a, b in bounds:
                edges += [a, b]
            edges.append(dur)
            segs = [(edges[2 * i], edges[2 * i + 1]) for i in range(len(bounds) + 1)]
            groups, start = [], 0
            for bi in bidx + [len(toks) - 1]:
                groups.append(list(range(start, bi + 1)))
                start = bi + 1
            for (sa, sb), g in zip(segs, groups):
                gw = [wts[i] for i in g]
                gt = sum(gw)
                acc = sa
                for i, w in zip(g, gw):
                    d = (sb - sa) * w / gt
                    self.words.append({"line": key, "i": i, "w": toks[i], "start": t + acc, "end": t + acc + d})
                    acc += d
            self.lines[key] = {"start": t, "end": t + dur, "dur": dur}
            t += dur

    def _chunks(self, maxw=3, maxc=17):
        out = []
        for key, _ in self.LINES:
            lw = [w for w in self.words if w["line"] == key]
            cur = []
            for w in lw:
                cand = cur + [w]
                text = " ".join(x["w"] for x in cand)
                if cur and (len(cand) > maxw or len(text) > maxc):
                    out.append(cur)
                    cur = [w]
                else:
                    cur = cand
                if re.search(r"[.,?:;!]$", w["w"]):
                    out.append(cur)
                    cur = []
            if cur:
                out.append(cur)
        res = []
        for k, c in enumerate(out):
            s = c[0]["start"] - 0.05
            nxt = out[k + 1][0]["start"] - 0.05 if k + 1 < len(out) else self.total
            e = min(nxt, c[-1]["end"] + 0.45)
            res.append({"start": s, "end": e, "words": c})
        return res

    # ------------------------------------------------------------------ queries
    def line(self, key):
        return self.lines[key]

    def find(self, key, word, nth=0, which="start"):
        """Time of the nth occurrence of `word` in line `key` (case/punctuation-insensitive)."""
        c = 0
        for w in self.words:
            if w["line"] == key and _norm(w["w"]) == _norm(word):
                if c == nth:
                    return w[which]
                c += 1
        raise KeyError(f"word {word!r} (#{nth}) not found in line {key!r}")

    def wt(self, key, i, which="start"):
        for w in self.words:
            if w["line"] == key and w["i"] == i:
                return w[which]
        raise KeyError((key, i))

    def report(self):
        rows = [f"{k:10s} {v['start']:6.2f} -> {v['end']:6.2f}" for k, v in self.lines.items()]
        rows.append(f"TOTAL {self.total:.2f}s")
        return "\n".join(rows)
