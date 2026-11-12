"""TPMS visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  DRIVE   (hook)      a frosty driveway at dawn, a parked car; we push in on the rear tire, which sits a little low.
                      "no pressure sensor": x-ray of the tire, an empty cavity, SENSOR? crossed out; the dash lamp lights.
  KINDS   (what)      two cards: DIRECT (a sensor and radio arcs) and INDIRECT (a big "?" that glows on "sneaky").
  LEAK    (problem)   one big tire face-on: 35 -> 26 PSI while the outline barely changes (ghost of the full tire);
                      then the US rule card (FMVSS 138, 25 % low, within 20 min) with a stopwatch filling to 20.
  SENSOR  (parts)     3D wheel cutaway: rim, x-ray tire, valve stem through the rim, the sensor on the back of the stem
                      with its coin battery.
  RADIO   (how)       the wheel turns (slowed); every revolution group the sensor sends a packet (arcs + ID/PSI pill) to
                      the receiver; a pressure-vs-time graph with the 25 %-low line; the lamp comes on when it's crossed.
  RE      (rehook)    the sensor is removed (crossed out): "WHAT IS IT MEASURING?"
  ROLL    (key)       two tires rolling on the same road at the same car speed: full vs low (squashed, smaller rolling
                      radius). Turn counters: the low one pulls ahead. Difference exaggerated (labelled).
  COUNT   (result)    four wheel rows (FL FR RL RR): tone ring, turns counted, speed vs the average; RR creeps ahead ->
                      SOFT TIRE, lamp on.
  CATCH   (catch)     all four sag together: bars stay equal -> NOTHING TO COMPARE; then the RESET button + relearn bar.
  OUTRO   (outro)     two halves: ASKS THE TIRE (radio) / WATCHES IT SPIN (counter), fading into the end card.

Model: rolling without slip, wheel angular speed = car speed / rolling radius. The full tire's rolling radius is R, the
low tire's is 0.93 R on screen (exaggerated for visibility; the real difference is a fraction of a percent). Pressure
example: 35 PSI placard, warning line at 26 PSI (25 % low, FMVSS 138). See research.md.
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, rev

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_NO = F("hook", "no")
T_SENSORH = F("hook", "sensor")
T_LIGHTH = F("hook", "light")
T_LOWH = F("hook", "low?")
T_WHAT = L("what")["start"]
T_TWO = F("what", "two")
T_SNEAKY = F("what", "sneaky.")
T_PROB = L("problem")["start"]
T_QUARTER = F("problem", "quarter")
T_FINE = F("problem", "fine.")
T_US = F("problem", "us,")
T_SEVEN = F("problem", "seven")
T_TWENTY = F("problem", "twenty")
T_PARTS = L("parts")["start"]
T_DIRECT = F("parts", "direct.")
T_VALVE = F("parts", "valve")
T_INSIDE = F("parts", "inside")
T_SENSORP = F("parts", "sensor")
T_BATTERY = F("parts", "battery.")
T_HOW = L("how")["start"]
T_MEASURES = F("how", "measures")
T_RADIOS = F("how", "radios")
T_THIRTY = F("how", "thirty")
T_DROP = F("how", "drop")
T_LIGHT = F("how", "light")
T_RE = L("rehook")["start"]
T_NOSENS = F("rehook", "sensor")
T_WHATM = F("rehook", "what")
T_KEY = L("key")["start"]
T_SPEED = F("key", "speed.")
T_SQUASH = F("key", "squashes")
T_SMALLER = F("key", "smaller.")
T_SPIN = F("key", "spin")
T_FASTER = F("key", "faster")
T_RES = L("result")["start"]
T_COUNT = F("result", "count")
T_WHEN = F("result", "when")
T_FASTER2 = F("result", "faster")
T_SOFT = F("result", "soft.")
T_CATCH = L("catch")["start"]
T_ALL = F("catch", "all")
T_NOTHING = F("catch", "nothing")
T_RESET = F("catch", "reset")
T_NEW = F("catch", "new")
T_OUTRO = L("outro")["start"]
T_ASKS = F("outro", "asks")
T_WATCHES = F("outro", "watches")

S_DRIVE = (0.0, T_WHAT + 0.3)
S_KINDS = (T_WHAT - 0.1, T_PROB + 0.3)
S_LEAK = (T_PROB - 0.1, T_PARTS + 0.3)
S_SENSOR = (T_PARTS - 0.1, T_RE + 0.35)
S_RE = (T_RE - 0.1, T_KEY + 0.3)
S_ROLL = (T_KEY - 0.1, T_RES + 0.3)
S_COUNT = (T_RES - 0.1, T_CATCH + 0.3)
S_CATCH = (T_CATCH - 0.1, T_OUTRO + 0.3)
S_OUTRO = (T_OUTRO - 0.1, T_TOTAL + 1)


def scene_k(t, s, fin=0.3, fout=0.3):
    return win(t, s[0], s[1], fin, fout)


def keys(t, ks):
    """Piecewise eased keyframes [(t, v), ...]."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease(lin(t, t0, t1))
    return ks[-1][1]


C_TIRE = hx("#1a1d23")
C_TIRE_E = hx("#3a414e")
C_RIM = hx("#a9b3c2")
C_BODY = hx("#6b7f99")


# ================================================================== a face-on tire (2D profile, rolling)
def tire_outline(cx, cy, R, squash, n=180):
    """Outer tire contour: radius R with the bottom flattened by `squash` (0..0.2 of R) and the sidewall bulging
    just above the contact patch, the way a soft tire sits."""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = np.cos(th)
    y = np.sin(th)
    low = np.clip(y, 0, 1) ** 6
    x = x * (1 + 0.55 * squash * low * 2.2)
    yy = np.minimum(y, 1 - squash)
    return np.stack([cx + R * x, cy + R * yy], 1)


def draw_tire(cv, cx, cy, R, ang, squash=0.0, a=1.0, rim_c=C_RIM, tread_c=C_TIRE, edge=C_TIRE_E, marker=INK,
              xray=0.0, glow=None):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    out = tire_outline(cx, cy, R, squash)
    if glow is not None:
        cv.drawPath(poly_path(out), paint(glow[0], a=0.5 * glow[1], stroke=14, blur=12))
    cv.drawPath(poly_path(out), paint(tread_c, a=1 - 0.75 * xray))
    cv.drawPath(poly_path(out), paint(edge if glow is None else mix(edge, glow[0], glow[1]), stroke=3))
    # tread blocks
    for i in range(28):
        th = ang + i * 2 * math.pi / 28
        r0, r1 = R * 0.93, R * 0.99
        ys = math.sin(th)
        if ys > 0.85 and squash > 0.01:
            continue
        cv.drawLine(cx + r0 * math.cos(th), cy + r0 * ys, cx + r1 * math.cos(th), cy + r1 * ys,
                    paint(hx("#2b313b"), a=1 - 0.6 * xray, stroke=4))
    # sidewall ring
    cv.drawCircle(cx, cy, R * 0.80, paint(hx("#262b34"), a=1 - 0.7 * xray, stroke=2))
    # rim
    rr = R * 0.64
    gp = skia.Paint(AntiAlias=True)
    gp.setShader(lin_grad((cx - rr, cy - rr), (cx + rr, cy + rr), [shade(rim_c, 1.2), shade(rim_c, 0.7)]))
    cv.drawCircle(cx, cy, rr, gp)
    cv.drawCircle(cx, cy, rr * 0.9, paint(hx("#20262f")))
    for i in range(5):
        th = ang + i * 2 * math.pi / 5
        p = skia.Path()
        for s_ in (-0.17, 0.17):
            pass
        q = [(cx + rr * 0.24 * math.cos(th - 0.5), cy + rr * 0.24 * math.sin(th - 0.5)),
             (cx + rr * 0.9 * math.cos(th - 0.16), cy + rr * 0.9 * math.sin(th - 0.16)),
             (cx + rr * 0.9 * math.cos(th + 0.16), cy + rr * 0.9 * math.sin(th + 0.16)),
             (cx + rr * 0.24 * math.cos(th + 0.5), cy + rr * 0.24 * math.sin(th + 0.5))]
        cv.drawPath(poly_path(np.array(q)), paint(shade(rim_c, 0.95)))
    cv.drawCircle(cx, cy, rr * 0.26, paint(shade(rim_c, 0.8)))
    for i in range(5):
        th = ang + (i + 0.5) * 2 * math.pi / 5
        cv.drawCircle(cx + rr * 0.15 * math.cos(th), cy + rr * 0.15 * math.sin(th), max(2, rr * 0.03),
                      paint(hx("#20262f")))
    # rotation marker on the sidewall
    if marker is not None:
        th = ang - math.pi / 2
        cv.drawLine(cx + R * 0.68 * math.cos(th), cy + R * 0.68 * math.sin(th), cx + R * 0.86 * math.cos(th),
                    cy + R * 0.86 * math.sin(th), paint(marker, stroke=max(4, R * 0.04), cap=skia.Paint.kRound_Cap))
    cv.restore()


def tire_lamp(cv, cx, cy, on, s=1.0, a=1.0):
    """Our own generic low-tire lamp: a tire section (U shape, flat tread at the bottom) with '!' (amber)."""
    if a <= 0:
        return
    c = mix(hx("#3d4556"), AMBER, on)
    cv.save()
    cv.translate(cx, cy)
    cv.scale(s, s)
    if on > 0:
        cv.drawCircle(0, 4, 62, paint(AMBER, a=0.35 * on * a, blur=24))
    p = skia.Path()
    p.moveTo(-44, -40)
    p.cubicTo(-58, -6, -54, 26, -40, 40)
    p.lineTo(40, 40)
    p.cubicTo(54, 26, 58, -6, 44, -40)
    cv.drawPath(p, paint(c, a=a, stroke=8, cap=skia.Paint.kRound_Cap, join=skia.Paint.kRound_Join))
    for x in (-30, -15, 0, 15, 30):
        cv.drawLine(x, 40, x - 5, 52, paint(c, a=a, stroke=6, cap=skia.Paint.kRound_Cap))
    cv.drawLine(0, -26, 0, 10, paint(c, a=a, stroke=9, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(0, 26, 5.5, paint(c, a=a))
    cv.restore()


def radio_arcs(cv, x, y, t, t0, c=AMBER, a=1.0, dirn=-90, n=3, r0=26, spread=70):
    """Expanding arcs from (x, y) starting at t0 (one packet)."""
    u = t - t0
    if u < 0 or u > 1.0 or a <= 0:
        return
    for i in range(n):
        uu = u - i * 0.12
        if uu < 0:
            continue
        r = r0 + 170 * uu
        aa = a * (1 - uu) * 0.9
        rect = skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r)
        cv.drawArc(rect, dirn - spread / 2, spread, False, paint(c, a=aa, stroke=5, cap=skia.Paint.kRound_Cap))


# ================================================================== DRIVE (hook)
GROUND = 1180.0
CAR = np.array([(-330, -50), (-336, -120), (-300, -150), (-180, -166), (-100, -236), (110, -238), (190, -166),
                (310, -150), (340, -110), (334, -50)], float)
WIN = np.array([(-165, -170), (-95, -224), (100, -226), (170, -170)], float)
WX = (-210.0, 215.0)
WR = 62.0


def sag_rear(t):
    return 0.11 * ease(lin(t, 0.2, T_LOWH))


def draw_drive(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, GROUND - 120, glow=hx("#ff9a5a"), glow_a=0.28, t=t, stars=60)
    # push in on the rear wheel
    z = keys(t, [(0.0, 1.3), (T_SENSORH - 0.3, 1.4), (T_SENSORH + 0.4, 2.0)])
    tx = keys(t, [(0.0, 0.0), (T_SENSORH - 0.3, 0.0), (T_SENSORH + 0.4, 1.0)])
    fx, fy = 540 + (540 + WX[0] - 540) * tx, 960 + (GROUND - WR - 960) * tx
    sx_, sy_ = 540 + (380 - 540) * tx, 960 + (900 - 960) * tx
    cv.save()
    cv.translate(sx_, sy_)
    cv.scale(z, z)
    cv.translate(-fx, -fy)
    # driveway
    cv.drawRect(skia.Rect.MakeLTRB(-400, GROUND, 1500, 2400), paint(hx("#141a24")))
    for i in range(30):
        x = -300 + i * 70
        cv.drawLine(x, GROUND + 6, x - 40, GROUND + 300, paint(hx("#1e2633"), stroke=2))
    rng = np.random.default_rng(4)
    for i in range(140):   # frost sparkle
        x, y = rng.uniform(-300, 1400), rng.uniform(GROUND + 4, GROUND + 260)
        tw = 0.5 + 0.5 * math.sin(3 * t + i)
        cv.drawCircle(x, y, 1.6, paint(hx("#cfe3ff"), a=0.25 + 0.35 * tw))
    # garage door + house wall
    cv.drawRect(skia.Rect.MakeLTRB(-200, GROUND - 520, 1300, GROUND), paint(hx("#1b2230")))
    cv.drawRect(skia.Rect.MakeLTRB(110, GROUND - 430, 980, GROUND), paint(hx("#232c3b")))
    for i in range(6):
        y = GROUND - 430 + i * 72
        cv.drawLine(110, y, 980, y, paint(hx("#2f394b"), stroke=3))
    look.bloom(cv, 60, GROUND - 470, 16, hx("#ffd9a0"), a=0.9)
    # car (2D side view)
    cx, cy = 540, GROUND
    look.soft_shadow(cv, cx, cy + 4, 720, 46, a=0.7)
    body = poly_path(CAR + [cx, cy])
    bp = skia.Paint(AntiAlias=True)
    bp.setShader(lin_grad((0, cy - 240), (0, cy - 40), [shade(C_BODY, 1.25), shade(C_BODY, 0.75)]))
    cv.drawPath(body, bp)
    cv.drawPath(body, paint(hx("#0b111c"), stroke=3))
    g = WIN + [cx, cy]
    gp = skia.Paint(AntiAlias=True)
    gp.setShader(lin_grad(tuple(g[1]), tuple(g[3]), [hx("#9cc0ea"), hx("#16243a")]))
    cv.drawPath(poly_path(g), gp)
    cv.drawLine(cx + 5, cy - 226, cx + 5, cy - 170, paint(hx("#0b111c"), stroke=8))
    # frost on the glass
    for i in range(50):
        x, y = rng.uniform(-150, 160), rng.uniform(-220, -175)
        cv.drawCircle(cx + x, cy + y, rng.uniform(1, 3), paint(hx("#e6f1ff"), a=0.35))
    for x in WX:
        sq = sag_rear(t) if x < 0 else 0.0
        xr = ease(lin(t, T_SENSORH - 0.2, T_SENSORH + 0.4)) if x < 0 else 0.0
        draw_tire(cv, cx + x, cy - WR * (1 - sq), WR, 0.4, squash=sq, xray=xr)
        if x < 0 and xr > 0:
            c0 = (cx + x, cy - WR * (1 - sq))
            p = paint(CYAN, a=0.9 * xr, stroke=1.6)
            p.setPathEffect(skia.DashPathEffect.Make([5, 4], 0))
            cv.drawCircle(c0[0], c0[1], WR * 0.82, p)
    cv.restore()
    # overlays (screen space)
    xk = win(t, T_SENSORH - 0.1, S_DRIVE[1], 0.25, 0.3)
    if xk > 0:
        pill(cv, 380, 640, "PRESSURE SENSOR?", font("inter_xb", 34), INK, border=CYAN, a=xk, align="center",
             tracking=2)
        cross_icon(cv, 380 + 205, 640, 54, RED, a=xk * eout(lin(t, T_SENSORH + 0.3, T_SENSORH + 0.6)))
        leader(cv, 380, 666, 380, 820, CYAN, a=xk * 0.8)
    lk = win(t, T_LIGHTH - 0.3, S_DRIVE[1], 0.25, 0.3)
    if lk > 0:
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(600, 1180, 300, 210), 26, 26)
        cv.drawRRect(rr, paint(hx("#06090f"), a=0.92 * lk))
        cv.drawRRect(rr, paint(hx("#2a3446"), a=lk, stroke=2))
        draw_text(cv, "DASH", 750, 1218, font("inter_xb", 18), MUTED, a=lk, align="center", tracking=3)
        on = eout(lin(t, T_LIGHTH, T_LIGHTH + 0.2))
        tire_lamp(cv, 750, 1300, on, s=0.85, a=lk)
    cv.restore()


# ================================================================== KINDS (what)
def draw_kinds(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    k1 = eback(lin(t, T_WHAT + 0.1, T_WHAT + 0.55))
    k2 = eback(lin(t, T_TWO - 0.1, T_TWO + 0.35))
    nk = eout(lin(t, T_WHAT - 0.1, T_WHAT + 0.3))
    pill(cv, 540, 540, "TIRE PRESSURE MONITORING · TPMS", font("inter_xb", 30), INK, border=CYAN, a=nk,
         align="center", tracking=2, dot=CYAN)
    sn = eout(lin(t, T_SNEAKY - 0.15, T_SNEAKY + 0.3))
    for i, (kk, title, c) in enumerate(((k1, "DIRECT", AMBER), (k2, "INDIRECT", mix(CYAN, YEL, sn)))):
        if kk <= 0:
            continue
        x0 = 90 + i * 460
        y0 = 620 + (1 - kk) * 80
        cv.saveLayerAlpha(None, int(255 * clamp(kk)))
        brand.panel(cv, x0, y0, 420, 560, title, c)
        draw_text(cv, f"KIND {i + 1}", x0 + 36, y0 + 100, font("inter_sb", 22), MUTED, tracking=3)
        cx, cy = x0 + 210, y0 + 340
        draw_tire(cv, cx, cy, 130, 0.25 * t * (i + 1), squash=0.0, a=0.95, xray=0.4 if i == 0 else 0)
        if i == 1 and t < T_TWO - 0.1:
            pass
        if i == 0:
            sx, sy = cx, cy - 130 * 0.68
            cv.drawRoundRect(skia.Rect.MakeXYWH(sx - 22, sy - 14, 44, 24), 6, 6, paint(AMBER))
            radio_arcs(cv, sx, sy - 16, t, T_TWO + 0.3 + ((t - T_TWO) // 1.0) * 1.0, a=1.0)
        else:
            q = 1 + 0.12 * sn * math.sin(8 * t)
            draw_text(cv, "?", cx, cy + 70, font("pop_b", 200 * q), mix(INK, YEL, sn), align="center",
                      glow=24 * sn if sn > 0.01 else None, glow_c=YEL)
        cv.restore()
    if sn > 0:
        pill(cv, 760, 1240, "SNEAKY", font("inter_blk", 34), INK, border=YEL, a=sn, align="center", tracking=5,
             dot=YEL)
    cv.restore()


# ================================================================== LEAK (problem)
PSI0, PSI_LOW = 35.0, 26.0


def leak_psi(t):
    return keys(t, [(T_PROB, PSI0), (T_FINE + 0.2, PSI_LOW)])


def draw_leak(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    rk = 1 - ease(lin(t, T_US - 0.2, T_US + 0.4))
    psi = leak_psi(t)
    sq = 0.045 * (PSI0 - psi) / (PSI0 - PSI_LOW)
    cx, cy, R = 540, 900 - 140 * (1 - rk), 300 - 100 * (1 - rk)
    # ground
    gy = cy + R * (1 - sq)
    cv.drawLine(120, gy, 960, gy, paint(hx("#3a4559"), a=rk, stroke=3))
    draw_tire(cv, cx, cy + R * sq * 0, R, 0.0, squash=sq, a=1.0)
    # ghost of the full tire
    gk = win(t, T_QUARTER, T_US, 0.3, 0.3)
    if gk > 0:
        p = paint(CYAN, a=0.9 * gk, stroke=3)
        p.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
        cv.drawPath(poly_path(tire_outline(cx, cy, R, 0.0)), p)
        pill(cv, 540, cy - R - 60, "FULL (DASHED) VS 25% LOW", font("inter_xb", 26), INK, border=CYAN, a=gk,
             align="center", tracking=2)
    fk = win(t, T_FINE - 0.2, T_US, 0.25, 0.3)
    if fk > 0:
        pill(cv, 540, 1300, "LOOKS ALMOST THE SAME", font("inter_blk", 34), INK, border=YEL, a=fk, align="center",
             tracking=3, dot=YEL)
    lowc = mix(CYAN, AMBER, lin(psi, PSI0, PSI_LOW))
    brand.readout(cv, win(t, T_PROB, T_US, 0.2, 0.3), f"{psi:.0f}", "PSI · EXAMPLE TIRE", frac=psi / 40,
                  bar_color=lowc, marker_frac=PSI_LOW / 40)
    # the rule card
    ck = eout(lin(t, T_US - 0.15, T_US + 0.35))
    if ck > 0:
        y0 = 1000 + (1 - ck) * 60
        brand.panel(cv, 90, y0, 900, 330, "US RULE · FMVSS 138", CYAN, a=ck)
        sk = eout(lin(t, T_SEVEN - 0.2, T_SEVEN + 0.2))
        draw_text(cv, "NEW LIGHT VEHICLES SINCE 2007", 126, y0 + 130, font("inter_xb", 30), INK, a=ck * sk,
                  tracking=1)
        draw_text(cv, "TIRE 25% LOW", 126, y0 + 190, font("inter_xb", 30), INK, a=ck * sk, tracking=1)
        wk = eout(lin(t, T_TWENTY - 0.2, T_TWENTY + 0.2))
        draw_text(cv, "WARN WITHIN", 126, y0 + 250, font("inter_xb", 30), INK, a=ck * wk, tracking=1)
        draw_text(cv, "20 MIN", 126, y0 + 300, font("inter_blk", 44), AMBER, a=ck * wk, tracking=3)
        # stopwatch
        sx, sy, sr = 790, y0 + 200, 92
        cv.drawCircle(sx, sy, sr, paint(hx("#0b111c"), a=ck))
        cv.drawCircle(sx, sy, sr, paint(hx("#3a4559"), a=ck, stroke=8))
        fill = keys(t, [(T_TWENTY - 0.1, 0.0), (T_TWENTY + 1.1, 1.0)])
        if fill > 0:
            cv.drawArc(skia.Rect.MakeLTRB(sx - sr, sy - sr, sx + sr, sy + sr), -90, 360 * fill, False,
                       paint(AMBER, a=ck, stroke=8, cap=skia.Paint.kRound_Cap))
        ang = -math.pi / 2 + 2 * math.pi * fill
        cv.drawLine(sx, sy, sx + sr * 0.75 * math.cos(ang), sy + sr * 0.75 * math.sin(ang), paint(INK, a=ck, stroke=5))
        cv.drawRect(skia.Rect.MakeXYWH(sx - 14, sy - sr - 26, 28, 18), paint(hx("#3a4559"), a=ck))
        draw_text(cv, f"{int(round(20 * fill))}", sx, sy + 56, font("inter_blk", 34), INK, a=ck * (fill > 0),
                  align="center")
        draw_text(cv, "MIN", sx, sy + 80, font("inter_sb", 16), MUTED, a=ck * (fill > 0), align="center", tracking=2)
    cv.restore()


# ================================================================== SENSOR + RADIO (parts, how) — 3D wheel cutaway
PJ = Proj(480, 840, 1.7, yaw=38, pitch=22)
R_BEAD, R_WELL, R_TREAD = 150.0, 132.0, 232.0
SENS_X0, SENS_X1 = -52.0, 44.0


def wheel_spin(t):
    """Wheel angle in the RADIO beat (slowed): stopped in parts, turning in how."""
    w = 1.15   # rad/s on screen
    u = max(0.0, t - (T_HOW - 0.3))
    return -w * u


def how_psi(t):
    return keys(t, [(T_MEASURES, PSI0), (T_DROP - 0.2, 32.0), (T_LIGHT - 0.05, 25.6)])


PACKET_DT = 1.55   # on-screen seconds between packets (real life: every 30-60 s)
_P_T0 = T_RADIOS - 0.15


def packets(t):
    """Times of packets sent so far."""
    if t < _P_T0:
        return []
    n = int((t - _P_T0) / PACKET_DT) + 1
    return [_P_T0 + i * PACKET_DT for i in range(n)]


def rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def draw_sensor_scene(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    re_k = ease(lin(t, T_RE - 0.1, T_RE + 0.5))
    a = wheel_spin(t)
    pj = PJ
    # tire (x-ray), back half first
    tk = eout(lin(t, T_PARTS - 0.1, T_PARTS + 0.4))
    zs = np.linspace(-78, 78, 9)
    rs = R_TREAD - 30 * (zs / 78) ** 4
    rev(cv, pj, "z", (0, 0), zs, rs, hx("#2a3140"), alpha=tk, fill_a=0.45, edge=hx("#55617a"), edge_w=1.4,
        caps=False)
    # rim barrel
    zr = np.array([-74, -66, -52, -20, 20, 52, 66, 74], float)
    rr = np.array([R_BEAD + 14, R_BEAD, R_BEAD, R_WELL, R_WELL, R_BEAD, R_BEAD, R_BEAD + 14], float)
    rev(cv, pj, "z", (0, 0), zr, rr, C_RIM, alpha=tk, edge=hx("#5a6577"), edge_w=1.2)
    # face spokes (front face at z = -74)
    for i in range(5):
        th = a + i * 2 * math.pi / 5
        p0 = pj(28 * math.cos(th), 28 * math.sin(th), -60)
        p1 = pj((R_BEAD - 6) * math.cos(th), (R_BEAD - 6) * math.sin(th), -74)
        cv.drawLine(*p0, *p1, paint(shade(C_RIM, 0.9), a=tk, stroke=26, cap=skia.Paint.kRound_Cap))
        cv.drawLine(*p0, *p1, paint(shade(C_RIM, 1.25), a=tk, stroke=8, cap=skia.Paint.kRound_Cap))
    hub = pj(0, 0, -60)
    cv.drawCircle(*hub, 40 * pj.s, paint(shade(C_RIM, 0.75), a=tk))
    cv.drawCircle(*hub, 40 * pj.s, paint(hx("#20262f"), a=tk, stroke=2))
    # valve stem + sensor at angle -90 deg (top) rotated by a
    vk = eout(lin(t, T_VALVE - 0.2, T_VALVE + 0.3))
    sk_ = eout(lin(t, T_SENSORP - 0.25, T_SENSORP + 0.25)) * (1 - re_k)
    base = rot(0, -R_BEAD, a)
    if vk > 0:
        # stem goes through the rim and out toward the face, the sensor sits on its inner end
        out_ = rot(0, -R_BEAD + 36, a)
        cyl3(cv, pj, (out_[0], out_[1], -86), (base[0], base[1], -40), 8, hx("#23272e"), alpha=vk,
             edge=AMBER if t < T_INSIDE + 0.6 else None)
        tip = pj(out_[0], out_[1], -86)
        cv.drawCircle(*tip, 9 * pj.s, paint(STEEL, a=vk))
    if sk_ > 0:
        # sensor body: a box from the stem base along the rim surface, inside the tire cavity
        corners = []
        for xx, yy in ((SENS_X0, -R_BEAD - 2), (SENS_X1, -R_BEAD - 2), (SENS_X1, -R_BEAD - 40), (SENS_X0 + 10, -R_BEAD - 40)):
            corners.append(rot(xx, yy, a))
        prof = np.array(corners)
        extrude(cv, pj, prof, -40 - 22, -40 + 22, hx("#3b4556"), alpha=sk_, rim=AMBER, rim_w=1.6,
                rim_glow=0.6 * win(t, T_SENSORP, T_BATTERY + 0.6, 0.2, 0.3))
        bk = eout(lin(t, T_BATTERY - 0.25, T_BATTERY + 0.2)) * sk_
        if bk > 0:
            bc = rot(-6, -R_BEAD - 21, a)
            p = pj(bc[0], bc[1], -63)
            cv.drawCircle(*p, 14 * pj.s, paint(hx("#d6dde8"), a=bk))
            cv.drawCircle(*p, 14 * pj.s, paint(hx("#5a6577"), a=bk, stroke=2))
            draw_text(cv, "+", p[0], p[1] + 9, font("inter_blk", 26), hx("#2a313c"), a=bk, align="center")
    # front half rim of tire (glass edge)
    cv.restore()
    cv.saveLayerAlpha(None, int(255 * k))
    # labels
    p_stem = pj(*rot(0, -R_BEAD + 36, a), -86)
    p_sens = pj(*rot(0, -R_BEAD - 16, a), -56)
    p_bat = pj(*rot(-6, -R_BEAD - 21, a), -63)
    p_in = pj(0, R_BEAD + 40, -78)
    brand.label(cv, t, "VALVE STEM", tuple(p_stem), (630, 560), AMBER, T_VALVE + 0.05, T_HOW + 0.2)
    brand.label(cv, t, "INSIDE THE TIRE", tuple(p_in), (560, 1240), CYAN, T_INSIDE, T_SENSORP + 0.6)
    brand.label(cv, t, "SENSOR", tuple(p_sens), (120, 560), AMBER, T_SENSORP + 0.05, T_HOW + 0.2)
    brand.label(cv, t, "BATTERY", tuple(p_bat), (110, 660), INK, T_BATTERY + 0.05, T_HOW + 0.2)
    # ---- RADIO (how)
    hk = win(t, T_HOW - 0.1, T_RE + 0.2, 0.3, 0.3) * (1 - re_k)
    if hk > 0:
        # receiver
        rx, ry = 790, 560
        rrr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(rx - 120, ry - 50, 240, 100), 18, 18)
        cv.drawRRect(rrr, paint(hx("#0b111c"), a=hk))
        cv.drawRRect(rrr, paint(GREEN, a=hk, stroke=3))
        draw_text(cv, "RECEIVER", rx, ry - 6, font("inter_blk", 28), INK, a=hk, align="center", tracking=3)
        draw_text(cv, "IN THE CAR", rx, ry + 26, font("inter_sb", 18), MUTED, a=hk, align="center", tracking=2)
        sp = pj(*rot(0, -R_BEAD - 30, a), -40)
        for tp in packets(t):
            radio_arcs(cv, sp[0], sp[1], t, tp, a=hk, dirn=-60, spread=90)
            u = clamp((t - tp) / 0.9)
            if 0 < u < 1:
                x = sp[0] + (rx - sp[0]) * ease(u)
                y = sp[1] + (ry + 92 - sp[1]) * ease(u) - 60 * math.sin(math.pi * u)
                pill(cv, x, y, f"ID 3F2A · {how_psi(tp):.0f} PSI", font("inter_xb", 22), INK, border=AMBER,
                     a=hk * (1 - lin(u, 0.7, 1.0)), align="center", tracking=1)
        # pressure graph
        gx, gy, gw, gh = 140, 1140, 760, 150
        gk = eout(lin(t, T_MEASURES - 0.2, T_MEASURES + 0.3)) * hk
        cv.saveLayerAlpha(None, int(255 * gk))
        brand.graph_box(cv, (gx, gy, gw, gh), "TIRE PRESSURE · EACH DOT = ONE MESSAGE")

        def ymap(p):
            return gy + gh - (p - 20) / 18 * gh

        yl = ymap(PSI_LOW)
        dp = paint(RED, a=0.9, stroke=3)
        dp.setPathEffect(skia.DashPathEffect.Make([12, 8], 0))
        cv.drawLine(gx, yl, gx + gw, yl, dp)
        draw_text(cv, "25% LOW · WARNING", gx + gw, yl - 10, font("inter_xb", 20), RED, align="right", tracking=2)
        t0g, t1g = T_MEASURES - 0.2, T_RE + 0.2
        pk = [tp for tp in packets(t)]
        pts = [(gx + (tp - t0g) / (t1g - t0g) * gw, ymap(how_psi(tp))) for tp in pk]
        if len(pts) > 1:
            brand.curve(cv, np.array(pts), AMBER, width=3)
        for (x, y), tp in zip(pts, pk):
            cv.drawCircle(x, y, 8, paint(RED if how_psi(tp) < PSI_LOW else AMBER))
        cv.restore()
        brand.readout(cv, hk * eout(lin(t, T_MEASURES, T_MEASURES + 0.3)), f"{how_psi(t):.0f}", "PSI · SENSOR READS")
        tk2 = win(t, T_THIRTY - 0.1, T_DROP, 0.2, 0.3) * hk
        if tk2 > 0:
            pill(cv, 870, 400, "EVERY 30-60 S (REAL TIME)", font("inter_xb", 22), INK, border=CYAN, a=tk2,
                 align="right", tracking=2)
        brand.note(cv, "ANIMATION SLOWED", 0.9 * hk * (1 - tk2), dy=0)
        lon = eout(lin(t, T_LIGHT - 0.1, T_LIGHT + 0.15))
        if lon > 0:
            rr2 = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(rx - 120, 650, 240, 170), 22, 22)
            cv.drawRRect(rr2, paint(hx("#06090f"), a=0.92 * hk))
            cv.drawRRect(rr2, paint(AMBER, a=hk * lon, stroke=2))
            tire_lamp(cv, rx, 730, lon, s=0.8, a=hk)
    cv.restore()


# ================================================================== RE (rehook)
def draw_re(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    draw_tire(cv, 540, 900, 250, -0.6 * (t - T_RE), xray=0.55)
    p = paint(CYAN, a=0.9, stroke=3)
    p.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
    cv.drawCircle(540, 900, 250 * 0.82, p)
    nk = eout(lin(t, T_NOSENS - 0.2, T_NOSENS + 0.2))
    pill(cv, 540, 900 - 250 * 0.72, "NO SENSOR", font("inter_blk", 30), INK, border=RED, a=nk, align="center",
         tracking=3)
    cross_icon(cv, 540, 900 - 250 * 0.72 - 70, 50, RED, a=nk)
    brand.stamp(cv, t, "MEASURING WHAT?", T_WHATM - 0.05, dur=max(1.0, T_KEY - T_WHATM + 0.2), center=(540, 1260),
                color=YEL, bg=hx("#2a2205"))
    cv.restore()


# ================================================================== ROLL (key) — rolling radius
R_ROLL = 165.0
R_LOW = 0.93          # rolling radius of the low tire on screen (exaggerated)
V_CAR = 260.0         # px/s road speed (slowed)
ROAD_Y = 1150.0


def roll_k(t):
    return ease(lin(t, T_SQUASH - 0.2, T_SQUASH + 0.6))


_RT = np.arange(S_ROLL[0] - 0.5, S_ROLL[1] + 0.6, 1 / 120)
_RV = np.array([V_CAR * ease(lin(x, T_KEY - 0.1, T_KEY + 0.5)) for x in _RT])
_RD = np.concatenate([[0], np.cumsum(_RV[:-1] / 120)])
_RLOW = np.array([1 - (1 - R_LOW) * roll_k(x) for x in _RT])
_A_FULL = _RD / R_ROLL
_A_LOW = np.concatenate([[0], np.cumsum((_RV / (R_ROLL * _RLOW))[:-1] / 120)])


def draw_roll(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    d = float(np.interp(t, _RT, _RD))
    af = float(np.interp(t, _RT, _A_FULL))
    al = float(np.interp(t, _RT, _A_LOW))
    rl = float(np.interp(t, _RT, _RLOW))
    rk = roll_k(t)
    # road
    cv.drawRect(skia.Rect.MakeLTRB(60, ROAD_Y, 1020, ROAD_Y + 26), paint(hx("#1e2633")))
    cv.drawLine(60, ROAD_Y, 1020, ROAD_Y, paint(hx("#5a6577"), stroke=3))
    for i in range(-1, 14):
        x = (i * 80 - d) % 1040 - 40
        if 60 < x < 1000:
            cv.drawLine(x, ROAD_Y + 13, x + 36, ROAD_Y + 13, paint(hx("#cfd6e2"), a=0.4, stroke=4))
    xs = (300, 780)
    for j, (x, ang, low) in enumerate(((xs[0], af, False), (xs[1], al, True))):
        Rr = R_ROLL * (rl if low else 1.0)
        sq = (1 - rl) * 1.0 if low else 0.0
        cy = ROAD_Y - Rr
        # draw the tire with nominal R and squash so its bottom sits on the road
        R0 = R_ROLL
        sq_draw = 1 - Rr / R0 if low else 0.0
        draw_tire(cv, x, ROAD_Y - R0 * (1 - sq_draw), R0, ang, squash=sq_draw,
                  glow=(RED, 0.8 * rk * win(t, T_FASTER - 0.2, S_ROLL[1], 0.2, 0.3)) if low else None)
        # rolling radius arrow
        ak = eout(lin(t, T_SMALLER - 0.6, T_SMALLER - 0.1)) if low else eout(lin(t, T_SQUASH, T_SQUASH + 0.4))
        if ak > 0:
            c = RED if low else CYAN
            hub_y = ROAD_Y - R0 * (1 - sq_draw)
            cv.drawLine(x + 30, hub_y, x + 30, ROAD_Y - 2, paint(c, a=ak, stroke=5))
            cv.drawLine(x + 18, ROAD_Y - 4, x + 42, ROAD_Y - 4, paint(c, a=ak, stroke=5))
            pill(cv, x + 46, (hub_y + ROAD_Y) / 2, "SMALLER" if low else "RADIUS", font("inter_xb", 22), INK, border=c,
                 a=ak, tracking=2)
        # turn counter
        turns = ang / (2 * math.pi)
        lab = "LOW TIRE" if low else "FULL TIRE"
        c = RED if (low and rk > 0.5) else CYAN
        pill(cv, x, 640, lab, font("inter_xb", 28), INK, border=c, a=1, align="center", tracking=2, dot=c)
        draw_text(cv, f"{turns:4.2f}", x, 760, font("inter_blk", 72), INK, align="center")
        draw_text(cv, "TURNS", x, 796, font("inter_sb", 20), MUTED, align="center", tracking=3)
    sk = win(t, T_SPEED - 0.15, T_SQUASH - 0.1, 0.2, 0.3)
    if sk > 0:
        pill(cv, 540, 1250, "SAME ROAD · SAME CAR SPEED", font("inter_xb", 28), INK, border=GREEN, a=sk, align="center",
             tracking=2)
    brand.stamp(cv, t, "WHEEL SPEED", T_SPEED - 0.1, dur=1.2, center=(540, 1320), color=YEL, bg=hx("#2a2205"))
    brand.stamp(cv, t, "SPINS FASTER", T_FASTER - 0.05, dur=max(1.2, T_RES - T_FASTER + 0.1), center=(540, 1300))
    brand.note(cv, "DIFFERENCE EXAGGERATED · SLOWED", 0.9, dy=-60)
    cv.restore()


# ================================================================== COUNT / CATCH — four wheels
ROWS = ["FL", "FR", "RL", "RR"]


def wheel_rates(t):
    """Speed of each wheel relative to the car (1 = normal) in the COUNT and CATCH beats (exaggerated)."""
    soft = 0.07 * ease(lin(t, T_WHEN - 0.2, T_FASTER2 + 0.3))
    allk = ease(lin(t, T_ALL - 0.1, T_ALL + 0.8))
    r = {nm: 1.0 for nm in ROWS}
    if t < T_CATCH:
        r["RR"] = 1.0 + soft
    else:
        for nm in ROWS:   # all four equally low: every wheel turns faster by the same amount
            r[nm] = 1.0 + 0.07 * allk
    return r


_CT = np.arange(S_COUNT[0] - 0.5, S_CATCH[1] + 0.6, 1 / 60)
_CR = {nm: np.array([wheel_rates(x)[nm] for x in _CT]) for nm in ROWS}
_CA = {nm: np.concatenate([[0], np.cumsum(_CR[nm][:-1] / 60)]) * 1.4 for nm in ROWS}


def tone_icon(cv, x, y, r, ang, c, a=1.0):
    n = 24
    pts = []
    for i in range(n):
        a0 = ang + 2 * math.pi * i / n
        da = 2 * math.pi / n
        for f, rr in ((0.0, r * 0.82), (0.1, r), (0.45, r), (0.55, r * 0.82)):
            pts.append((x + rr * math.cos(a0 + f * da), y + rr * math.sin(a0 + f * da)))
    cv.drawPath(poly_path(np.array(pts)), paint(hx("#aeb8c6"), a=a))
    cv.drawCircle(x, y, r * 0.6, paint(hx("#0b111c"), a=a))
    cv.drawRect(skia.Rect.MakeXYWH(x - 6, y - r - 26, 12, 20), paint(c, a=a))


def draw_rows(cv, t, k, mode):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    rates = wheel_rates(t)
    avg = sum(rates.values()) / 4
    y0, dy = 640, 160
    ck = eout(lin(t, T_COUNT - 0.2, T_COUNT + 0.3)) if mode == "count" else 1.0
    for i, nm in enumerate(ROWS):
        y = y0 + i * dy
        rk = eback(lin(t, S_COUNT[0] + 0.05 * i, S_COUNT[0] + 0.4 + 0.05 * i)) if mode == "count" else 1.0
        if rk <= 0:
            continue
        rel = rates[nm] / avg
        hot = clamp((rel - 1.0) / 0.03)
        c = mix(CYAN, RED, hot)
        ang = float(np.interp(t, _CT, _CA[nm])) * 2 * math.pi
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(90, y - 62, 900, 124), 24, 24)
        cv.drawRRect(rr, paint(hx("#0e1625"), a=0.92 * clamp(rk)))
        cv.drawRRect(rr, paint(c, a=0.6 * clamp(rk), stroke=2.5))
        draw_text(cv, nm, 130, y + 16, font("inter_blk", 46), INK, a=clamp(rk), tracking=3)
        # small tire with sag in the catch beat
        sag = 0.06 * ease(lin(t, T_ALL - 0.1, T_ALL + 0.8)) if mode == "catch" else (
            0.06 * ease(lin(t, T_WHEN - 0.2, T_FASTER2 + 0.3)) if nm == "RR" else 0.0)
        draw_tire(cv, 290, y + 2 - 46 * sag, 46, ang, squash=sag, a=clamp(rk), marker=c)
        tone_icon(cv, 400, y + 6, 34, ang, AMBER, a=clamp(rk) * ck)
        turns = float(np.interp(t, _CT, _CA[nm])) - float(np.interp(S_COUNT[0], _CT, _CA[nm]))
        draw_text(cv, f"{turns * 10:5.1f}", 600, y + 14, font("inter_blk", 46), INK, a=clamp(rk) * ck, align="right")
        draw_text(cv, "TURNS", 600, y + 40, font("inter_sb", 16), MUTED, a=clamp(rk) * ck, align="right", tracking=2)
        # bar vs average
        bx0, bx1 = 640, 950
        cv.drawRoundRect(skia.Rect.MakeLTRB(bx0, y - 12, bx1, y + 12), 12, 12, paint(hx("#1a2232"), a=clamp(rk) * ck))
        mid = (bx0 + bx1) / 2
        cv.drawLine(mid, y - 22, mid, y + 22, paint(MUTED, a=clamp(rk) * ck, stroke=2))
        w = (rel - 1.0) / 0.05 * (bx1 - mid)
        x_ = mid + w
        cv.drawRoundRect(skia.Rect.MakeLTRB(min(mid, x_) - 8, y - 12, max(mid, x_) + 8, y + 12), 12, 12,
                         paint(c, a=clamp(rk) * ck))
    hk = clamp(ck)
    draw_text(cv, "VS THE OTHER WHEELS", 795, 560, font("inter_xb", 20), MUTED, a=hk, align="center", tracking=2)
    draw_text(cv, "ABS WHEEL SENSORS", 400, 560, font("inter_xb", 20), MUTED, a=hk, align="center", tracking=2)
    if mode == "count":
        brand.stamp(cv, t, "RR IS SOFT", T_SOFT - 0.1, dur=max(1.2, T_CATCH - T_SOFT + 0.2), center=(540, 1290))
        lon = eout(lin(t, T_SOFT - 0.1, T_SOFT + 0.15))
        brand.note(cv, "DIFFERENCE EXAGGERATED", 0.9, dy=-60)
        if lon > 0:
            tire_lamp(cv, 860, 280, lon, s=0.7)
    else:
        nk = T_NOTHING
        brand.stamp(cv, t, "NOTHING TO COMPARE", nk - 0.1, dur=max(1.2, T_RESET - nk - 0.1), center=(540, 1290),
                    color=YEL, bg=hx("#2a2205"))
        rk2 = eout(lin(t, T_RESET - 0.2, T_RESET + 0.25))
        if rk2 > 0:
            press = 1 - 0.12 * win(t, T_RESET, T_RESET + 0.35, 0.08, 0.15)
            cv.save()
            cv.translate(540, 1290)
            cv.scale(press, press)
            cv.drawCircle(0, 0, 70, paint(AMBER, a=0.4 * rk2, blur=16))
            cv.drawCircle(0, 0, 64, paint(hx("#1b1406"), a=rk2))
            cv.drawCircle(0, 0, 64, paint(AMBER, a=rk2, stroke=5))
            draw_text(cv, "RESET", 0, 12, font("inter_blk", 30), INK, a=rk2, align="center", tracking=3)
            cv.restore()
            prog = keys(t, [(T_RESET + 0.3, 0.0), (T_OUTRO - 0.2, 1.0)])
            draw_text(cv, "NEW TIRES: RELEARN", 650, 1262, font("inter_xb", 24), INK, a=rk2, tracking=2)
            cv.drawRoundRect(skia.Rect.MakeLTRB(650, 1290, 940, 1310), 10, 10, paint(hx("#1a2232"), a=rk2))
            cv.drawRoundRect(skia.Rect.MakeLTRB(650, 1290, 650 + 290 * prog, 1310), 10, 10, paint(GREEN, a=rk2))
    cv.restore()


# ================================================================== OUTRO
def draw_outro(cv, t, k):
    if k <= 0:
        return
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k * kE))
    a1 = eout(lin(t, T_ASKS - 0.3, T_ASKS + 0.2))
    a2 = eout(lin(t, T_WATCHES - 0.3, T_WATCHES + 0.2))
    for i, (aa, title, c) in enumerate(((a1, "ASKS THE TIRE", AMBER), (a2, "WATCHES IT SPIN", CYAN))):
        if aa <= 0:
            continue
        x0 = 90 + i * 460
        cv.saveLayerAlpha(None, int(255 * aa))
        brand.panel(cv, x0, 640, 420, 560, "", c)
        draw_text(cv, title, x0 + 210, 710, font("inter_blk", 34), c, align="center", tracking=2)
        cx, cy = x0 + 210, 950
        ang = 1.2 * (t - T_OUTRO) * (1 + i)
        draw_tire(cv, cx, cy, 140, ang, xray=0.4 if i == 0 else 0)
        if i == 0:
            sx, sy = cx, cy - 140 * 0.68
            cv.drawRoundRect(skia.Rect.MakeXYWH(sx - 22, sy - 14, 44, 24), 6, 6, paint(AMBER))
            radio_arcs(cv, sx, sy - 16, t, T_ASKS + ((t - T_ASKS) // 0.9) * 0.9)
        else:
            draw_text(cv, f"{ang / (2 * math.pi):4.1f} TURNS", cx, 1150, font("inter_xb", 28), INK, align="center",
                      tracking=2)
        cv.restore()
    cv.restore()


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(0, "TWO KINDS", INK), (T_PROB, "THE RULE", CYAN), (T_PARTS, "KIND 1: DIRECT", AMBER),
           (T_RE, "KIND 2: INDIRECT", YEL), (T_CATCH, "THE CATCH", RED), (T_OUTRO, "TPMS", GREEN)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)


# ================================================================== draw
def draw(cv, t):
    draw_drive(cv, t, scene_k(t, S_DRIVE, 0.0, 0.3))
    draw_kinds(cv, t, scene_k(t, S_KINDS))
    draw_leak(cv, t, scene_k(t, S_LEAK))
    draw_sensor_scene(cv, t, scene_k(t, S_SENSOR))
    draw_re(cv, t, scene_k(t, S_RE))
    draw_roll(cv, t, scene_k(t, S_ROLL))
    draw_rows(cv, t, scene_k(t, S_COUNT), "count")
    draw_rows(cv, t, scene_k(t, S_CATCH), "catch")
    draw_outro(cv, t, scene_k(t, S_OUTRO))
    draw_header(cv, t)


# ================================================================== sound (synthesized here)
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _norm(x, pk=0.9):
    x = np.asarray(x, np.float64)
    x = x / (np.abs(x).max() + 1e-9) * pk
    n = int(0.01 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def _chirp():
    """Short digital data chirp for one radio packet."""
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    bits = (np.floor(tt * 90) % 3 != 1).astype(float)
    f = np.where(bits > 0, 2400, 1800)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.12)
    return _norm(x, 0.5)


def _chime():
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt / d) / (i + 1)
            for i, (f, d) in enumerate(((880, 0.5), (1320, 0.35), (1760, 0.25))))
    return _norm(x, 0.6)


def _leak():
    from scipy import signal
    rng = np.random.default_rng(9)
    n = int(2.2 * SR)
    tt = np.arange(n) / SR
    b, a = signal.butter(2, [3000 / (SR / 2), 9000 / (SR / 2)], "band")
    x = signal.lfilter(b, a, rng.standard_normal(n)) * np.minimum(1, tt / 0.15) * np.exp(-tt / 1.4)
    return _norm(x, 0.45)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, x in (("tpms_chirp", _chirp()), ("tpms_chime", _chime()), ("tire_leak", _leak())):
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_SPEED
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(T_SENSORH, "whoosh_up", 0.3), (T_LIGHTH, "tpms_chime", 0.45), (T_HOOK_OUT - 0.1, "whoosh_big", 0.4),
           (T_TWO - 0.1, "tick", 0.3), (T_TWO + 0.15, "tick", 0.3), (T_SNEAKY, "impact", 0.3),
           (T_PROB - 0.05, "whoosh_down", 0.3), (T_QUARTER - 0.2, "tire_leak", 0.4), (T_US - 0.1, "clunk", 0.35),
           (T_TWENTY, "tick", 0.3), (T_PARTS - 0.05, "whoosh_up", 0.3), (T_VALVE, "tick", 0.3),
           (T_SENSORP, "clunk", 0.35), (T_BATTERY, "tick", 0.3), (T_LIGHT, "tpms_chime", 0.5),
           (T_RE - 0.05, "whoosh_big", 0.35), (T_WHATM, "impact", 0.35), (T_SPEED - 0.05, "impact", 0.45),
           (T_FASTER, "whoosh_up", 0.35), (T_RES - 0.05, "whoosh_down", 0.3), (T_SOFT - 0.1, "tpms_chime", 0.45),
           (T_CATCH - 0.05, "whoosh_down", 0.3), (T_NOTHING - 0.1, "impact", 0.35), (T_RESET, "clunk", 0.4),
           (T_ASKS, "tpms_chirp", 0.35), (T_WATCHES, "whoosh_up", 0.3)]
    for tp in packets(T_RE - 0.2):
        if tp < T_RE - 0.2:
            sfx.append((tp, "tpms_chirp", 0.3))
    return {"build": (T_RE, T_SPEED), "drop": (T_SPEED, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
