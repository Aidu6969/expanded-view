"""Expanded View "real-world" look (style upgrade, 2026-11-03): lit environments for the opening scene and
cinematic finishing (bloom, soft shadows, haze, light beams, wet-road reflections). Same palette as ev.gfx.

Use these for the 2-3 s real-world opening (the thing in its setting) before cutting inside the mechanism,
and for "back in the world" result beats. Everything is drawn procedurally: no photos, no logos.
"""
import math

import numpy as np
import skia

from .gfx import W, H, clamp, ease, hx, lin, lin_grad, mix, paint, poly_path

NIGHT_TOP, NIGHT_MID, NIGHT_LOW = hx("#050913"), hx("#0b1830"), hx("#1d2f52")


def night_sky(cv, horizon=900, glow=hx("#ff7a3d"), glow_a=0.35, seed=3, stars=140, t=0.0):
    p = skia.Paint()
    p.setShader(lin_grad((0, 0), (0, horizon), [NIGHT_TOP, NIGHT_MID, NIGHT_LOW], [0, 0.6, 1]))
    cv.drawRect(skia.Rect.MakeWH(W, horizon + 4), p)
    # horizon glow (distant town / last light)
    g = skia.Paint()
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(W * 0.65, horizon), 700,
                                               [skia.Color4f(*[c / 255 for c in glow[:3]], glow_a),
                                                skia.Color4f(0, 0, 0, 0)]))
    cv.drawRect(skia.Rect.MakeWH(W, horizon + 4), g)
    rng = np.random.default_rng(seed)
    xs, ys = rng.uniform(0, W, stars), rng.uniform(0, horizon * 0.75, stars) ** 1.0
    sz, ph = rng.uniform(0.6, 2.2, stars), rng.uniform(0, 6.28, stars)
    for x, y, s, f in zip(xs, ys, sz, ph):
        a = 0.35 + 0.35 * math.sin(t * 1.3 + f)
        cv.drawCircle(x, y, s, paint(hx("#dfe8ff"), a=a * (1 - y / horizon)))


def mountains(cv, horizon, layers=3, offset=0.0, seed=5):
    """Layered ridgelines with atmospheric haze; offset scrolls them (parallax: far layers move less)."""
    rng = np.random.default_rng(seed)
    for li in range(layers):
        far = 1 - li / max(1, layers)
        base = horizon - 40 - 160 * far + 60 * li
        amp = 90 + 120 * far
        freq = rng.uniform(0.004, 0.007, 4)
        phs = rng.uniform(0, 6.28, 4)
        xs = np.linspace(-20, W + 20, 90)
        sh = offset * (0.15 + 0.35 * (1 - far))
        y = base - amp * (0.5 + 0.25 * np.sin((xs + sh) * freq[0] + phs[0]) + 0.15 * np.sin((xs + sh) * freq[1] + phs[1])
                          + 0.1 * np.sin((xs + sh) * freq[2] * 2.3 + phs[2]))
        pts = np.vstack([np.stack([xs, y], 1), [[W + 20, horizon + 400], [-20, horizon + 400]]])
        c = mix(hx("#0a1426"), hx("#2a3d63"), 0.7 * far)
        cv.drawPath(poly_path(pts), paint(c))
        cv.drawPath(poly_path(np.stack([xs, y], 1), close=False), paint(hx("#5b78a8"), a=0.18 * far, stroke=2))


def haze(cv, y0, y1, c=hx("#9fb6e0"), a=0.12):
    p = skia.Paint()
    p.setShader(lin_grad((0, y0), (0, y1), [c, c], None))
    p.setAlphaf(1.0)
    cols = [skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, 0), skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a),
            skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, 0)]
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], cols, [0, 0.5, 1]))
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), p)


def soft_shadow(cv, cx, cy, w, h, a=0.5):
    cv.drawOval(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), paint(hx("#000000"), a=a, blur=h * 0.6))


def beam(cv, p0, p1, w0, w1, c=hx("#fff1c9"), a=0.35):
    """Light cone from p0 (narrow) to p1 (wide), fading out."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9)
    quad = np.array([p0 + n * w0, p1 + n * w1, p1 - n * w1, p0 - n * w0])
    pt = skia.Paint(AntiAlias=True)
    cl = [skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a), skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, 0)]
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], cl))
    pt.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    cv.drawPath(poly_path(quad), pt)


def bloom(cv, x, y, r, c, a=0.8):
    """Bright light source: hot core + wide glow."""
    cv.drawCircle(x, y, r * 4.0, paint(c, a=0.18 * a, blur=r * 2.4))
    cv.drawCircle(x, y, r * 1.8, paint(c, a=0.45 * a, blur=r * 0.9))
    cv.drawCircle(x, y, r * 0.7, paint(mix(c, hx("#ffffff"), 0.7), a=a))


def puff(cv, x, y, age, life=0.9, size=40, c=hx("#c9d2e0"), a=0.55, drift=(-60, -140)):
    """Exhaust / steam puff: grows, drifts and fades over `life` seconds."""
    if age < 0 or age > life:
        return
    k = age / life
    r = size * (0.4 + 1.6 * k ** 0.6)
    cv.drawCircle(x + drift[0] * k, y + drift[1] * k, r, paint(c, a=a * (1 - k) ** 1.5, blur=r * 0.45))


def wet_reflection(cv, x, y_top, y_bot, w, c, a=0.35):
    """Vertical streak reflection of a light on a wet road."""
    pt = skia.Paint(AntiAlias=True)
    cl = [skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a), skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, 0)]
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y_top), skia.Point(x, y_bot)], cl))
    pt.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.35))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y_top, x + w / 2, y_bot), pt)


def vignette(cv, a=0.6):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.45), H * 0.75,
                                               [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, a)], [0.5, 1.0]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)


def road_sign(cv, x, y, lines, w=230, h=150, c_bg=hx("#f2f2ee"), c_fg=hx("#111111"), a=1.0, post=260):
    """Generic rectangular road sign on a post (black on white), lit by headlights."""
    cv.drawRect(skia.Rect.MakeXYWH(x - 6, y, 12, post), paint(hx("#5b6575"), a=a))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h, w, h), 10, 10)
    cv.drawRRect(rr, paint(c_bg, a=a))
    cv.drawRRect(rr, paint(c_fg, a=a, stroke=5))
    from .gfx import draw_text, font
    n = len(lines)
    for i, ln in enumerate(lines):
        fs = 40 if n <= 2 else 32
        draw_text(cv, ln, x, y - h + (h / (n + 1)) * (i + 1) + fs * 0.36, font("inter_blk", fs), c_fg, a=a,
                  align="center")
