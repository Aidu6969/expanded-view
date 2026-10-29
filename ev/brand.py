"""Expanded View brand layer. Everything here is FIXED across episodes — do not restyle per episode.

Fixed elements (drawn by ev.build, not by episodes):
  background()      dark navy blueprint grid + vignette
  hook_title()      "HOW <TOPIC> ACTUALLY WORKS" two-line title over the hook
  captions()        word-by-word yellow-highlight captions at y=1462
  end_card()        punchline (2 lines, 2nd in red)  ->  "<TOPIC>" big red title + subtitle

Reusable widgets for episodes: gauge, label, stamp, status_pill, readout, note, chips,
graph_box, curve, panel, bullet, acronym_rows.
Layout safe zone (TikTok/Shorts UI): keep content in x 60..940, y 150..1520.
"""
import math

import numpy as np
import skia

from .gfx import *

CAP_Y = 1462
SAFE = (60, 150, 940, 1520)

# ------------------------------------------------------------------ background
_bg = None


def background():
    global _bg
    if _bg is None:
        s = skia.Surface(W, H)
        c = s.getCanvas()
        p = skia.Paint()
        p.setShader(lin_grad((0, 0), (0, H), [BG1, BG0, hx("#05070b")], [0, 0.6, 1]))
        c.drawRect(skia.Rect.MakeWH(W, H), p)
        g = skia.Paint()
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 760), 700,
                                                   [col(hx("#1b3a66", 0.35)), col(hx("#1b3a66", 0.0))]))
        c.drawRect(skia.Rect.MakeWH(W, H), g)
        gp = paint(hx("#5f8fd6"), a=0.055, stroke=1.2)
        for x in range(0, W + 1, 54):
            c.drawLine(x, 0, x, H, gp)
        for y in range(0, H + 1, 54):
            c.drawLine(0, y, W, y, gp)
        gp2 = paint(hx("#5f8fd6"), a=0.09, stroke=1.4)
        for x in range(0, W + 1, 270):
            c.drawLine(x, 0, x, H, gp2)
        for y in range(0, H + 1, 270):
            c.drawLine(0, y, W, y, gp2)
        v = skia.Paint()
        v.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 860), 1250,
                                                   [col(hx("#000000", 0)), col(hx("#000000", 0)), col(hx("#000000", 0.75))],
                                                   [0, 0.55, 1]))
        c.drawRect(skia.Rect.MakeWH(W, H), v)
        _bg = s.makeImageSnapshot()
    return _bg


# ------------------------------------------------------------------ hook title
def hook_title(cv, t, lines, t_out):
    """lines: [[(text, color), ...], [(text, color), ...]] — e.g. [[("HOW ",INK),("VTEC",RED)],[("ACTUALLY WORKS",INK)]].
    Visible from frame 0 (thumbnail-safe); slides up and fades around t_out."""
    ta = 1 - ease(lin(t, t_out - 0.35, t_out + 0.15))
    if ta <= 0:
        return
    f1 = font("pop_b", 96)
    for i, parts in enumerate(lines):
        y = 320 + 110 * i
        k = eback(lin(t, -0.22 + 0.08 * i, 0.16 + 0.08 * i))
        a = ta * clamp(k)
        dy = (1 - k) * 40 - 60 * ease(lin(t, t_out - 0.35, t_out + 0.15))
        total = sum(text_w(s, f1) for s, _ in parts)
        fs = min(1.0, 940 / max(1, total))
        f = font("pop_b", 96 * fs)
        total = sum(text_w(s, f) for s, _ in parts)
        x = 540 - total / 2
        for s, c in parts:
            x += draw_text(cv, s, x, y + dy, f, c, a=a, glow=14 if c == RED else None)


# ------------------------------------------------------------------ captions
def captions(cv, t, tl, stop):
    if t >= stop:
        return
    cur = None
    for c in tl.chunks:
        if c["start"] <= t < c["end"]:
            cur = c
            break
    if cur is None:
        return
    f = font("pop_b", 64)
    words = [w["w"].upper() for w in cur["words"]]
    space = f.measureText(" ")
    widths = [f.measureText(w) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    sc = min(1.0, 860 / total)
    pop = eback(lin(t, cur["start"], cur["start"] + 0.14), 2.0)
    s = sc * (0.86 + 0.14 * pop)
    cv.save()
    cv.translate(520, CAP_Y)
    cv.scale(s, s)
    x = -total / 2
    for w, wd, wobj in zip(words, widths, cur["words"]):
        c = YEL if (wobj["start"] - 0.03 <= t < wobj["end"] + 0.05) else INK
        cv.drawString(w, x + 4, 6, f, paint(hx("#000000"), a=0.55, blur=6))
        cv.drawString(w, x, 0, f, paint(hx("#06080d"), stroke=14))
        cv.drawString(w, x, 0, f, paint(c))
        x += wd + space
    cv.restore()


# ------------------------------------------------------------------ the ending (fixed formula)
def end_card(cv, t, punch, topic, subtitle, t_end, t_topic):
    """punch: ("TWO CAMS", "IN ONE.") shown from t_end; topic: "VTEC" shown from t_topic with subtitle lines."""
    if t < t_end:
        return
    f = font("pop_b", 124)
    k1 = eback(lin(t, t_end + 0.05, t_end + 0.45))
    o1 = ease(lin(t, t_topic - 0.05, t_topic + 0.3))
    a1 = clamp(k1) * (1 - o1)
    if a1 > 0:
        dy = (1 - clamp(k1)) * 50 - 80 * o1
        for i, (line, c) in enumerate(zip(punch, (INK, RED))):
            fs = min(124, 124 * 940 / max(1, text_w(line, f)))
            draw_text(cv, line, 540, 720 + 140 * i + dy, font("pop_b", fs), c, a=a1, align="center",
                      glow=16 if c == RED else None)
    k2 = eback(lin(t, t_topic, t_topic + 0.45), 1.3)
    if k2 > 0:
        s = 0.7 + 0.3 * k2
        size = 250
        while size > 90 and text_w(topic, font("inter_blk", size), 14) > 960:
            size -= 6
        fv = font("inter_blk", size)
        cv.save()
        cv.translate(540, 800)
        cv.scale(s, s)
        base = 85 * size / 250
        draw_text(cv, topic, 0, base, fv, RED, a=clamp(k2), align="center", glow=34, tracking=14 * size / 250)
        draw_text(cv, topic, 0, base, fv, hx("#ff5050"), a=clamp(k2), align="center", tracking=14 * size / 250)
        cv.restore()
        ka = eout(lin(t, t_topic + 0.3, t_topic + 0.7))
        fs = font("inter_sb", 34)
        top = 800 + 135 * size / 250
        cv.drawLine(380, top, 700, top, paint(RED, a=ka, stroke=4))
        for i, line in enumerate(subtitle or ["EXPANDED VIEW"]):
            draw_text(cv, line, 540, top + 65 + 48 * i, fs, INK, a=ka, align="center", tracking=1)


# ------------------------------------------------------------------ widgets
def gauge(cv, cx, cy, R, value, vmax=9000, redline=7500, step_minor=250, step_major=1000,
          label="x1000 r/min", unit="RPM", marker=None, digits_div=1000, readout=None, alpha=1.0):
    """Analog dial (tachometer, boost gauge, speedometer...). 270° sweep, 0 at lower-left."""
    def ang(v):
        return math.radians(135 + 270 * v / vmax)
    cv.saveLayerAlpha(None, int(255 * clamp(alpha)))
    cv.drawCircle(cx, cy, R + 26, paint(hx("#0a0f18")))
    rp = skia.Paint(AntiAlias=True)
    rp.setShader(lin_grad((cx, cy - R), (cx, cy + R), [hx("#5a6577"), hx("#1a2130"), hx("#3a4456")]))
    rp.setStyle(skia.Paint.kStroke_Style); rp.setStrokeWidth(10)
    cv.drawCircle(cx, cy, R + 22, rp)
    face = skia.Paint(AntiAlias=True)
    face.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy - 60), R * 1.2,
                                                  [col(hx("#141c2b")), col(hx("#080b12"))]))
    cv.drawCircle(cx, cy, R + 16, face)
    if redline is not None:
        rect = skia.Rect.MakeLTRB(cx - R + 18, cy - R + 18, cx + R - 18, cy + R - 18)
        cv.drawArc(rect, 135 + 270 * redline / vmax, 270 * (vmax - redline) / vmax, False,
                   paint(RED, stroke=16, cap=skia.Paint.kButt_Cap))
    if marker is not None:
        a = ang(marker)
        cv.drawLine(cx + (R - 4) * math.cos(a), cy + (R - 4) * math.sin(a),
                    cx + (R + 14) * math.cos(a), cy + (R + 14) * math.sin(a), paint(AMBER, stroke=6))
    fnum = font("inter_b", 40)
    n = int(round(vmax / step_minor))
    per = int(round(step_major / step_minor))
    for i in range(0, n + 1):
        v = i * step_minor
        a = ang(v)
        major = i % per == 0
        r1 = R - (44 if major else 26)
        c = RED if (redline is not None and v >= redline) else INK
        cv.drawLine(cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + (R - 6) * math.cos(a), cy + (R - 6) * math.sin(a),
                    paint(c, a=0.95 if major else 0.55, stroke=6 if major else 3, cap=skia.Paint.kButt_Cap))
        if major:
            rn = R - 82
            draw_text(cv, str(int(v // digits_div)), cx + rn * math.cos(a), cy + rn * math.sin(a) + 14, fnum, c,
                      align="center")
    if label:
        draw_text(cv, label, cx, cy - 95, font("inter_sb", 24), MUTED, align="center", tracking=1)
    txt = readout if readout is not None else f"{int(round(value / 10) * 10):,}"
    draw_text(cv, txt, cx, cy + 92, font("inter_blk", 64), INK, align="center")
    if unit:
        draw_text(cv, unit, cx, cy + 128, font("inter_sb", 24), MUTED, align="center", tracking=3)
    a = ang(value)
    tipx, tipy = cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a)
    bx, by = cx - 40 * math.cos(a), cy - 40 * math.sin(a)
    cv.drawLine(bx, by, tipx, tipy, paint(hx("#ff5a2a"), a=0.6, stroke=14, blur=10))
    cv.drawLine(bx, by, tipx, tipy, paint(hx("#ff6a3a"), stroke=8))
    cv.drawCircle(cx, cy, 30, paint(hx("#1c2330")))
    cv.drawCircle(cx, cy, 30, paint(hx("#5a6577"), stroke=3))
    cv.restore()


def lamp(cv, cx, cy, text, on, w=200, h=60):
    """Dash warning-lamp style badge that lights up red (on: 0..1)."""
    lr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), 14, 14)
    cv.drawRRect(lr, paint(mix(hx("#1a1f2a"), hx("#3a0b0b"), on)))
    if on > 0:
        cv.drawRRect(lr, paint(RED, a=0.55 * on, blur=22))
    cv.drawRRect(lr, paint(mix(hx("#3a4252"), RED, on), stroke=3))
    draw_text(cv, text, cx, cy + 15, font("inter_blk", 42), mix(hx("#3d4556"), hx("#ffe9e6"), on),
              align="center", tracking=4, glow=10 * on if on > 0.01 else None, glow_c=RED)


def label(cv, t, text, anchor, lpos, c, t0, t1, align="left"):
    """Leader line from a projected anchor point to a pill label, visible t0..t1."""
    k = win(t, t0, t1, 0.3, 0.3)
    if k <= 0:
        return
    f = font("inter_xb", 27)
    x, y = lpos
    leader(cv, anchor[0], anchor[1], x, y, c, a=k, prog=eout(lin(t, t0, t0 + 0.3)))
    pill(cv, x + (8 if align == "left" else -8), y, text, f, INK, border=c, a=k, align=align, tracking=1.5)


def stamp(cv, t, text, t0, dur=1.35, center=(540, 1262), color=RED, bg=hx("#2a0707")):
    """Big punchy badge (e.g. LOCKED, BOOST, ENGAGED) popping in at t0."""
    k = win(t, t0 - 0.05, t0 + dur - 0.05, 0.15, 0.4)
    if k <= 0:
        return
    s = 1 + 0.25 * (1 - eback(lin(t, t0 - 0.05, t0 + 0.3)))
    cv.save()
    cv.translate(*center)
    cv.scale(s, s)
    f = font("inter_blk", 58)
    w = text_w(text, f, 8)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 - 34, -50, w + 68, 92), 20, 20)
    cv.drawRRect(rr, paint(color, a=0.5 * k, blur=20))
    cv.drawRRect(rr, paint(bg, a=0.92 * k))
    cv.drawRRect(rr, paint(color, a=k, stroke=4))
    draw_text(cv, text, 0, 23, f, INK, a=k, align="center", tracking=8)
    cv.restore()


def status_pill(cv, k, text, color, dy=0.0, bg=hx("#0b111c")):
    """Top-left mode pill (e.g. LOW-RPM CAM / VTEC ENGAGED)."""
    if k <= 0:
        return
    pill(cv, 70, 236 + dy, text, font("inter_xb", 32), INK, bg=bg, border=color, a=k, dot=color, tracking=2)


def readout(cv, k, value, unit, frac=None, bar_color=CYAN, marker_frac=None, dy=0.0):
    """Top-right big number + unit + optional progress bar."""
    if k <= 0:
        return
    draw_text(cv, value, 870, 258 + dy, font("inter_blk", 64), INK, a=k, align="right")
    draw_text(cv, unit, 870, 292 + dy, font("inter_sb", 22), MUTED, a=k, align="right", tracking=3)
    if frac is not None:
        bx0, bx1, by = 600, 870, 316 + dy
        cv.drawLine(bx0, by, bx1, by, paint(hx("#263043"), a=k, stroke=10))
        cv.drawLine(bx0, by, bx0 + (bx1 - bx0) * clamp(frac), by, paint(bar_color, a=k, stroke=10))
        if marker_frac is not None:
            xs = bx0 + (bx1 - bx0) * marker_frac
            cv.drawLine(xs, by - 12, xs, by + 12, paint(AMBER, a=k, stroke=3))


def note(cv, text, a, dy=0.0):
    """Small right-aligned note under the readout, e.g. ANIMATION SLOWED."""
    draw_text(cv, text, 870, 354 + dy, font("inter_sb", 19), MUTED, a=a, align="right", tracking=2)


def chips(cv, k, y, items, lead=None, x=70, center=False):
    """Row of check-chips. items: [(name, ok 0..1)]; lead: (text, on 0..1) badge at the start.
    center=True centres the row (no lead) on the screen. Returns the lead badge's (x0, width, height) or None."""
    if k <= 0:
        return None
    f = font("inter_xb", 26)
    if center and not lead:
        tot = sum(text_w(n, f, 1.5) + 70 for n, _ in items) + 10 * (len(items) - 1)
        x = (W - tot) / 2
    lead_box = None
    if lead:
        on = lead[1]
        lead_box = pill(cv, x, y, lead[0], font("inter_blk", 28), INK, bg=mix(hx("#0b111c"), hx("#3a2a05"), on),
                        border=mix(MUTED, AMBER, on), a=k, tracking=3)
        x = lead_box[0] + lead_box[1] + 14
    for name, ok in items:
        w = text_w(name, f, 1.5) + 70
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y - 25, w, 50), 25, 25)
        cv.drawRRect(rr, paint(hx("#0b111c"), a=0.9 * k))
        cv.drawRRect(rr, paint(mix(hx("#3a4252"), GREEN, ok), a=k, stroke=2.4))
        draw_text(cv, name, x + 18, y + 10, f, mix(MUTED, INK, ok), a=k, tracking=1.5)
        if ok > 0:
            check_icon(cv, x + w - 28, y, 24, GREEN, a=k * ok)
        x += w + 10
    return lead_box


def graph_box(cv, rect, title, xlabel=None):
    """Rounded panel with a title and baseline; rect = (gx, gy, gw, gh) of the plot area."""
    gx, gy, gw, gh = rect
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(gx - 30, gy - 46, gw + 60, gh + 92), 22, 22)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.85))
    cv.drawRRect(rr, paint(hx("#2a3446"), stroke=2))
    draw_text(cv, title, gx, gy - 12, font("inter_xb", 22), MUTED, tracking=3)
    if xlabel:
        draw_text(cv, xlabel, gx + gw, gy + gh + 34, font("inter_sb", 20), MUTED, align="right", tracking=2)
    cv.drawLine(gx, gy + gh, gx + gw, gy + gh, paint(hx("#3a4559"), stroke=2))


def curve(cv, pts, c, a=1.0, prog=1.0, dashed=False, width=5):
    """Glowing polyline (graph curve). pts: (N,2) screen points; prog draws a prefix."""
    pts = np.asarray(pts)
    n = max(2, int(len(pts) * clamp(prog)))
    path = poly_path(pts[:n], close=False)
    if dashed:
        p = paint(c, a=0.5 * a, stroke=3)
        p.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
        cv.drawPath(path, p)
        return
    cv.drawPath(path, paint(c, a=0.5 * a, stroke=width * 2, blur=6))
    cv.drawPath(path, paint(c, a=a, stroke=width))


def dot(cv, x, y, c):
    cv.drawCircle(x, y, 16, paint(c, a=0.55, blur=7))
    cv.drawCircle(x, y, 8, paint(INK))


def panel(cv, x0, y0, w, h, title, c, a=1.0):
    """Card with coloured border + title (used for side-by-side comparisons)."""
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y0, w, h), 28, 28)
    cv.drawRRect(rr, paint(hx("#0e1625"), a=0.92 * a))
    cv.drawRRect(rr, paint(c, a=0.55 * a, stroke=2.5))
    draw_text(cv, title, x0 + 36, y0 + 62, font("inter_xb", 38), c, a=a, tracking=4)


def bullet(cv, x, y, text, good, a=1.0, size=32):
    if a <= 0:
        return
    if good:
        check_icon(cv, x + 12, y - 12, 30, GREEN, a=a)
    else:
        cross_icon(cv, x + 12, y - 12, 30, RED, a=a)
    draw_text(cv, text, x + 38, y, font("inter_b", size), INK, a=a)


def acronym_rows(cv, t, header, rows, t_in, t_out, highlight=None, x=190, y0=560, dy=165):
    """Letter tiles that light up as each word is spoken. rows: [(letter, words, t_word)]."""
    a_in = eout(lin(t, t_in, t_in + 0.45))
    if header:
        draw_text(cv, header, x, y0 - 130, font("inter_xb", 36), MUTED, a=a_in * (1 - lin(t, t_out, t_out + 0.4)),
                  tracking=6)
    for i, (letter, words, tr) in enumerate(rows):
        y = y0 + i * dy
        tr -= 0.08
        k = eback(lin(t, tr, tr + 0.38))
        ko = ease(lin(t, t_out + 0.07 * i, t_out + 0.5 + 0.07 * i))
        ddx = -700 * ko
        a = a_in * (1 - ko)
        if a <= 0:
            continue
        lit = eout(lin(t, tr, tr + 0.2))
        box = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + ddx, y - 66, 132, 132), 22, 22)
        bp = skia.Paint(AntiAlias=True)
        bp.setShader(lin_grad((0, y - 66), (0, y + 66), [mix(hx("#262c38"), hx("#ff4d4d"), lit),
                                                         mix(hx("#161b25"), hx("#c41d1d"), lit)]))
        cv.saveLayerAlpha(None, int(255 * a))
        if lit > 0:
            cv.drawRRect(box, paint(RED, a=0.45 * lit, blur=18))
        cv.drawRRect(box, bp)
        cv.drawRRect(box, paint(mix(hx("#3a4252"), hx("#ff8a8a"), lit), stroke=2.5))
        draw_text(cv, letter, x + 66 + ddx, y + 36, font("pop_b", 100), mix(hx("#7a8396"), INK, lit), align="center")
        wc = YEL if highlight == i else INK
        draw_text(cv, words, x + 170 + ddx + (1 - k) * 80, y + 24, font("pop_b", 66), wc, a=clamp(k))
        cv.restore()
