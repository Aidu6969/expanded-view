"""Turbo flutter visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  HOOK    (hook)     night road, a boosted car lifts off: STU TU TU TU pops off the engine bay; WHAT'S MAKING IT?
  SYSTEM  (what..key) x-ray cut to the air path: inlet -> spinning compressor -> charge pipe -> throttle -> engine.
                     The throttle snaps shut; particles pile up; pressure bar climbs; pipe glows.
  KEY     (key)      air reverses through the wheel, a live pressure trace below prints one STU per bounce.
  MAP     (surge)    compressor map with the operating point falling off the left edge and orbiting.
  MYTH    (myth)     close-up: wheel keeps its direction (green arrow), air leaves backwards (red).
  HARM    (harm)     bearing cut-away: shaft walks axially, collar slams the thrust plates.
  FIX     (fix)      same air path + blow-off valve; vacuum hose lights, piston lifts, air vents, PSSH.

Model: Greitzer lumped surge model (duct inertia, plenum, cubic compressor characteristic, throttle), integrated
below. Everything that moves in the air path follows phi(t) and psi(t). Non-dimensional; slowed (noted on screen).
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import _axmap, arrow_head, cyl3, flow, path_len, pipe, point_at, rev, spline, wheel

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_STU = F("hook", "Stu")
T_TU = [F("hook", "tu", nth=i) for i in range(3)]
T_LOVES = F("hook", "loves")
T_MAKING = F("hook", "making")
T_WHAT = L("what")["start"]
T_FL0 = F("what", "flutter")
T_PROB = L("problem")["start"]
T_WHEEL = F("problem", "wheel")
T_HUNDRED = F("problem", "hundred")
T_RAM = F("problem", "ramming")
T_ENGINE = F("problem", "engine.")
T_LIFT = L("lift")["start"]
T_THROT = F("lift", "throttle")
T_SHUT = F("lift", "snaps")
T_NOWHERE = F("lift", "nowhere")
T_PILES = F("lift", "piles")
T_SPIKES = F("lift", "spikes.")
T_RE = L("rehook")["start"]
T_STOP = F("rehook", "stop.")
T_WHERE = F("rehook", "where")
T_KEY = L("key")["start"]
T_BACK = F("key", "backwards.")
T_BEATS = F("key", "beats")
T_BLASTS = F("key", "blasts")
T_DROPS = F("key", "drops,")
T_GRAB = F("key", "grab")
T_REPEATS = F("key", "repeats.")
T_EVERY = F("key", "every")
T_BOUNCES = F("key", "bounces.")
T_SURGE = L("surge")["start"]
T_CALL = F("surge", "compressor")
T_MAP = F("surge", "map,")
T_LEFT = F("surge", "left")
T_MYTH = L("myth")["start"]
T_NEVER = F("myth", "never")
T_REV = F("myth", "reverses.")
T_AIR2 = F("myth", "air")
T_HARM = L("harm")["start"]
T_LITTLE = F("harm", "little")
T_MODERN = F("harm", "modern")
T_GARRETT = F("harm", "Garrett")
T_HAMMER = F("harm", "hammering")
T_THRUST = F("harm", "thrust")
T_FIX = L("fix")["start"]
T_BOV = F("fix", "blow")
T_VAC = F("fix", "vacuum")
T_OPEN = F("fix", "open")
T_ESC = F("fix", "escapes.")
T_PSSH = F("fix", "pssh.")
T_OUTRO = L("outro")["start"]

# ================================================================== surge model (Greitzer)
_W, _H, _P0, _B = 0.25, 0.18, 0.3, 1.8
GAM_OPEN, GAM_SHUT = 0.8, 0.2
XI_RATE = 11.0            # non-dimensional time per video second in surge (slowed)


def psic(phi):
    u = phi / _W - 1
    return _P0 + _H * (1 + 1.5 * u - 0.5 * u ** 3)


def _sim():
    dt = 0.02
    x, y = 0.75, 0.5
    for _ in range(int(400 / dt)):                 # settle at the open-throttle point
        x, y = x + dt * _B * (psic(x) - y), y + dt * (x - GAM_OPEN * math.sqrt(max(y, 0))) / _B
    steady = (x, y)
    n = int(650 / dt)
    xs, ph, ps = np.arange(n) * dt, np.zeros(n), np.zeros(n)
    for i in range(n):
        ph[i], ps[i] = x, y
        x, y = x + dt * _B * (psic(x) - y), y + dt * (x - GAM_SHUT * math.sqrt(max(y, 0))) / _B
    return steady, xs, ph, ps


STEADY, XS, PH, PS = _sim()
XI_STAR = float(XS[np.argmax(PH < 0.46)])          # just before the stall: held there across the "rehook" beat


def xi_of(t):
    if t <= T_SHUT:
        return 0.0
    if t <= T_BACK:
        return XI_STAR * lin(t, T_SHUT, T_BACK)
    return XI_STAR + XI_RATE * (t - T_BACK)


def phi(t):
    return STEADY[0] if t <= T_SHUT else float(np.interp(xi_of(t), XS, PH))


def psi(t):
    return STEADY[1] if t <= T_SHUT else float(np.interp(xi_of(t), XS, PS))


def press(t):
    return clamp((psi(t) - 0.42) / (0.92 - 0.42))


_TG = np.arange(0, T_TOTAL + 1, 1 / 120)
_PHI = np.array([phi(float(x)) for x in _TG])
_D = np.cumsum(_PHI) / 120


def D_of(t):
    return float(np.interp(t, _TG, _D))


_cr = np.where((_PHI[:-1] > 0) & (_PHI[1:] <= 0))[0]
BOUNCES = [float(_TG[i]) for i in _cr if T_BACK - 0.2 < _TG[i] < T_SURGE - 0.1]


_X0 = np.where(np.sign(_PHI[:-1]) != np.sign(_PHI[1:]))[0]
CROSS = np.array([float(_TG[i]) for i in _X0])


def hit_k(t):
    """1 just after the shaft is thrown the other way (a flow reversal), decays fast."""
    past = CROSS[CROSS <= t - 0.06]
    return math.exp(-(t - 0.06 - float(past[-1])) / 0.09) if len(past) else 0.0


def shut_k(t):
    return eout(lin(t, T_SHUT - 0.05, T_SHUT + 0.16))


def rev_k(t):
    """1 while the air is flowing backwards."""
    return clamp(-phi(t) * 10)


def p_col(p):
    return mix(mix(CYAN, AMBER, clamp(p * 2)), RED, clamp(p * 2 - 1))


# ================================================================== layout of the air path
PJ = Proj(270, 770, 2.0)
AXC = (0.0, 0.0)
INLET = np.array([[599, 990], [520, 937], [440, 884], [316, 801]], float)
DIS_A = spline([(290, 650), (345, 590), (445, 556), (560, 555), (690, 555)], 90)
DIS_B = spline([(690, 555), (790, 572), (830, 650), (830, 900)], 90)
BOV_X = 505
_iB = int(np.argmin(np.abs(DIS_A[:, 0] - BOV_X)))
DIS_TO_BOV = DIS_A[:_iB + 1]
HOSE = spline([(775, 590), (690, 450), (610, 366), (BOV_X + 30, 372)], 80)
VENT_L = spline([(BOV_X, 540), (BOV_X, 498), (BOV_X - 40, 478), (BOV_X - 110, 440)], 40)
VENT_R = spline([(BOV_X, 540), (BOV_X, 498), (BOV_X + 40, 478), (BOV_X + 110, 440)], 40)


def stream(cv, pts, d, spacing, col_fn, r, a=1.0, cluster=0.0):
    if a <= 0:
        return
    Ln = path_len(pts)
    n = int(Ln / spacing) + 1
    for k in range(n):
        s = (k * spacing + d) % Ln
        u = s / Ln
        if cluster > 0:
            u = u ** (1 / (1 + cluster))
        p, _ = point_at(pts, u * Ln)
        c = col_fn(u)
        cv.drawCircle(p[0], p[1], r * 2.2, paint(c, a=0.32 * a, blur=r * 0.9))
        cv.drawCircle(p[0], p[1], r, paint(c, a=a))


STEEL = hx("#8d9bb0")


def draw_cwheel(cv, pj, th, a=1.0, nb=7):
    """Compressor wheel: hub flares to a backplate; blades sweep to the backplate edge (matches the turbo episode)."""
    wheel(cv, pj, "x", AXC, 36, -14, lambda s: 9 + 10 * s ** 2.2 + 8 * s, lambda s: 36 + 28 * s ** 2.4, nb, th,
          hx("#c7d2e0"), blade=hx("#d3dcea"), twist=0.75, splitters=True, bp_r=64, alpha=a, blur=1,
          rim=CYAN, rim_a=0.35, bp_t=4.0)


def draw_compressor(cv, t, pj, a=1.0, nb=7):
    th = 11.0 * t
    rev(cv, pj, "x", AXC, [-30, -22, 34, 42], [58, 72, 72, 46], STEEL, alpha=a, fill_a=0.16, edge=hx("#9fb6d8"), edge_w=1.4)
    draw_cwheel(cv, pj, th, a=a, nb=nb)


def draw_throttle(cv, t, a):
    cx, cy = DIS_A[-1]
    k = shut_k(t)
    ang = math.radians(90 * k * 0.92)
    r = 37
    dx, dy = r * math.cos(ang), r * math.sin(ang)
    c = mix(hx("#d6dee9"), RED, k)
    if k > 0:
        cv.drawLine(cx - dx, cy - dy, cx + dx, cy + dy, paint(RED, a=a * 0.5 * k, stroke=20, blur=9))
    cv.drawLine(cx - dx, cy - dy, cx + dx, cy + dy, paint(c, a=a, stroke=9, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(cx, cy, 9, paint(hx("#0b111c"), a=a))
    cv.drawCircle(cx, cy, 9, paint(c, a=a, stroke=3))


def draw_engine(cv, a):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(735, 900, 190, 160), 20, 20)
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((0, 900), (0, 1060), [hx("#3a4557"), hx("#161c28")]))
    p.setAlphaf(a)
    cv.drawRRect(rr, p)
    cv.drawRRect(rr, paint(hx("#5c6b82"), a=a, stroke=2.5))
    for i in range(4):
        x = 762 + i * 45
        cv.drawCircle(x, 944, 16, paint(hx("#0b111c"), a=a))
        cv.drawCircle(x, 944, 16, paint(hx("#7f8ea6"), a=a, stroke=2))
    draw_text(cv, "ENGINE", 830, 1022, font("inter_xb", 30), INK, a=a, align="center", tracking=3)


def draw_air_path(cv, t, a):
    """Inlet + wheel + charge pipe + throttle + engine, air state from the surge model."""
    if a <= 0:
        return
    p = press(t)
    sh = shut_k(t)
    c = p_col(p)
    pipe(cv, INLET, 62, hx("#5d7499"), a=a, glass=True)
    glow = clamp(sh * 0.9 * p)
    if glow > 0:
        cv.drawPath(poly_path(DIS_A, close=False), paint(RED, a=a * 0.42 * glow, stroke=96, blur=22))
    pipe(cv, DIS_A, 74, hx("#5d7499"), a=a, glass=True)
    pipe(cv, DIS_B, 74, hx("#5d7499"), a=a, glass=True)
    draw_engine(cv, a)
    d = D_of(t) * 900
    cl = sh * p * 1.8 * (1 - 0.9 * rev_k(t))
    stream(cv, DIS_A, d, 36, lambda u: p_col(p * (0.3 + 0.7 * u)), 7.5, a=a, cluster=cl)
    if a > 0 and t < T_SHUT + 0.4:
        stream(cv, DIS_B, d, 36, lambda u: CYAN, 7.5, a=a * (1 - lin(t, T_SHUT, T_SHUT + 0.4)))
    stream(cv, INLET, d, 44, lambda u: mix(CYAN, RED, rev_k(t)), 7, a=a)
    draw_compressor(cv, t, PJ, a=a)
    draw_throttle(cv, t, a)
    if rev_k(t) > 0.02:
        k = rev_k(t)
        q0, tv = point_at(INLET, 90)
        tip = q0 + tv * 150
        cv.drawLine(tip[0], tip[1], q0[0], q0[1], paint(RED, a=a * k, stroke=11))
        arrow_head(cv, np.array([tip, q0]), RED, size=34, a=a * k)


def draw_pressure_trace(cv, t):
    k = scene_k(t, T_BLASTS - 0.2, T_SURGE - 0.05, 0.35, 0.3)
    if k <= 0:
        return
    rect = (140, 1205, 800, 130)
    cv.saveLayerAlpha(None, int(255 * k))
    brand.graph_box(cv, rect, "PRESSURE IN THE PIPE")
    gx, gy, gw, gh = rect
    span = 2.6
    u = np.linspace(0, 1, 200)
    tt = t - span + span * u
    tt = np.maximum(tt, T_BACK - 0.5)
    ps = np.array([psi(float(x)) for x in tt])
    pts = np.stack([gx + gw * u, gy + gh - (ps - 0.2) / 0.75 * (gh - 34)], 1)
    brand.curve(cv, pts, RED, width=4)
    brand.dot(cv, pts[-1, 0], pts[-1, 1], RED)
    for tb in BOUNCES:
        if tb <= t and t - tb < span:
            x = gx + gw * (1 - (t - tb) / span)
            ka = eout(lin(t, tb, tb + 0.12))
            draw_text(cv, "STU", x, gy + 26, font("pop_b", 32), YEL, a=ka, align="center")
    cv.restore()


def scene_k(t, t0, t1, fin=0.3, fout=0.3):
    return win(t, t0, t1, fin, fout)


def draw_system_labels(cv, t):
    k = scene_k(t, T_PROB, T_KEY + 0.5)
    if k <= 0:
        return
    C = (150, 540)
    brand.label(cv, t, "COMPRESSOR WHEEL", (245, 725), (90, 535), CYAN, T_WHEEL - 0.1, T_RE - 0.1)
    brand.label(cv, t, "THROTTLE PLATE", (690, 555), (690, 450), RED, T_THROT - 0.1, T_SPIKES + 1.2, align="left")
    brand.label(cv, t, "ENGINE", (830, 900), (760, 820), CYAN, T_ENGINE - 0.1, T_THROT - 0.1)
    # still spinning arrow during the rehook
    ks = scene_k(t, T_RE, T_BACK, 0.25, 0.25)
    if ks > 0:
        pill(cv, 90, 535, "STILL SPINNING", font("inter_xb", 27), INK, border=YEL, a=ks, tracking=1.5, dot=YEL)


def draw_top(cv, t):
    k = scene_k(t, T_PROB + 0.1, T_SURGE - 0.1, 0.3, 0.3)
    if k <= 0:
        return
    sh = shut_k(t)
    p = press(t)
    if t < T_SHUT:
        txt, c = "FULL BOOST", CYAN
    elif t < T_BACK:
        txt, c = "THROTTLE SHUT", AMBER
    elif rev_k(t) > 0.3:
        txt, c = "AIR REVERSED", RED
    else:
        txt, c = "BLADES GRAB", YEL
    brand.status_pill(cv, k, txt, c)
    val = "≈100,000" if t < T_LIFT else ("PEAK" if t >= T_SPIKES - 0.1 and t < T_BACK else ("≈100,000" if t < T_SHUT else "RISING"))
    unit = "RPM" if t < T_SHUT else "PRESSURE IN THE PIPE"
    if t >= T_BACK:
        val = "BOUNCING"
    brand.readout(cv, k * eout(lin(t, T_HUNDRED - 0.2, T_HUNDRED + 0.2)), val, unit,
                  frac=p if t >= T_SHUT else None, bar_color=p_col(p), marker_frac=None)
    if t >= T_BACK:
        brand.note(cv, "ANIMATION SLOWED", k)


# ------------------------------------------------------------------ map
def draw_map(cv, t):
    k = scene_k(t, T_SURGE - 0.25, T_MYTH - 0.05, 0.3, 0.3)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    rect = (150, 640, 780, 600)
    gx, gy, gw, gh = rect
    x0, x1 = -0.32, 0.95
    y0, y1 = 0.05, 1.0

    def X(p):
        return gx + (p - x0) / (x1 - x0) * gw

    def Y(q):
        return gy + gh - (q - y0) / (y1 - y0) * gh
    brand.graph_box(cv, rect, "COMPRESSOR MAP", xlabel="AIRFLOW  →")
    # surge line: left of the peak of the speed line
    xs = 0.5
    edge = np.array([[X(xs - 0.05), Y(0.92)], [X(xs + 0.02), Y(0.66)], [X(xs + 0.04), Y(0.12)]])
    lb = eout(lin(t, T_MAP - 0.15, T_MAP + 0.2))
    fill = np.vstack([[[gx, Y(0.92)]], edge, [[gx, gy + gh]]])
    cv.drawPath(poly_path(fill), paint(RED, a=0.13 * lb))
    brand.curve(cv, spline(edge, 50), RED, width=5, prog=lb)
    draw_text(cv, "SURGE", X(0.08), Y(0.86), font("pop_b", 46), RED, a=lb, align="center", glow=8)
    draw_text(cv, "STABLE", X(0.78), Y(0.20), font("pop_b", 40), CYAN, a=lb, align="center")
    draw_text(cv, "PRESSURE  ↑", gx + 8, gy + 36, font("inter_sb", 20), MUTED, a=lb, tracking=2)
    ph_ = np.linspace(-0.28, 0.80, 140)
    pts = np.stack([X(ph_), Y(np.clip(psic(ph_), y0, y1))], 1)
    brand.curve(cv, pts, CYAN, dashed=True)
    # operating point: replay the lift-off, then orbit
    Tgo = T_LEFT - 0.4
    u = ease(lin(t, T_SURGE + 0.2, Tgo))
    def op(tt):
        if tt < Tgo:
            uu = ease(lin(tt, T_SURGE + 0.2, Tgo))
            xi = XI_STAR * uu
        else:
            xi = XI_STAR + XI_RATE * (tt - Tgo) * 0.6
        return float(np.interp(xi, XS, PH)), float(np.interp(xi, XS, PS))
    n = 60
    trail = np.array([op(max(T_SURGE + 0.2, t - 1.6 * (1 - i / n))) for i in range(n + 1)])
    tp = np.stack([X(trail[:, 0]), Y(np.clip(trail[:, 1], y0, y1))], 1)
    brand.curve(cv, tp, AMBER, a=0.9, width=4)
    phn, psn = trail[-1]
    brand.dot(cv, X(phn), Y(min(psn, y1)), RED if phn < 0.45 else CYAN)
    ka = eout(lin(t, T_LEFT - 0.05, T_LEFT + 0.25))
    if ka > 0:
        pill(cv, X(0.3), Y(0.98), "OFF THE LEFT EDGE", font("inter_xb", 25), INK, border=RED, a=ka, align="center",
             tracking=2, dot=RED)
    cv.restore()


# ------------------------------------------------------------------ myth close-up
def draw_myth(cv, t):
    k = scene_k(t, T_MYTH - 0.2, T_HARM - 0.05, 0.3, 0.3)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    pj = Proj(500, 730, 4.6)
    th = 11.0 * t
    # wheel
    draw_cwheel(cv, pj, th)
    # green spin arrow (same direction as theta)
    a0 = th % (2 * math.pi)
    angs = a0 + np.linspace(0, 1.9, 50)
    pts = pj(*_axmap("x", 40.0, 66.0, angs, AXC))
    ga = eout(lin(t, T_NEVER - 0.1, T_NEVER + 0.25))
    cv.drawPath(poly_path(pts, close=False), paint(GREEN, a=0.5 * ga, stroke=20, blur=6))
    cv.drawPath(poly_path(pts, close=False), paint(GREEN, a=ga, stroke=9))
    arrow_head(cv, pts, GREEN, size=34, a=ga)
    # air leaving backward
    ra = eout(lin(t, T_AIR2 - 0.15, T_AIR2 + 0.2))
    if ra > 0:
        for i in range(-1, 2):
            base = np.array(pj(40.0, 0.0, 16.0 * i)) + np.array([0, 0])
            p0 = base
            p1 = base + np.array([0.832, 0.555]) * 430
            pts2 = np.linspace(p0, p1, 40)
            flow(cv, pts2, t, 520, 62, RED, r=11, a=ra, seed=i + 5)
            arrow_head(cv, pts2, RED, size=38, a=ra)
    # chips
    b1 = eout(lin(t, T_NEVER, T_NEVER + 0.25))
    b2 = eout(lin(t, T_AIR2 - 0.05, T_AIR2 + 0.2))
    brand.bullet(cv, 160, 1195, "THE WHEEL REVERSES", False, a=b1, size=44)
    brand.bullet(cv, 160, 1275, "THE AIR REVERSES", True, a=b2, size=44)
    cv.restore()


# ------------------------------------------------------------------ bearing cut-away
def draw_harm(cv, t):
    k = scene_k(t, T_HARM - 0.2, T_FIX - 0.05, 0.3, 0.3)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    pj = Proj(530, 770, 3.5)
    shake = 3.4 * math.tanh(phi(t) * 16)
    hit = hit_k(t)
    A = shake
    # turbine stub, shaft, housing, plates, collar, compressor
    wheel(cv, pj, "x", AXC, -126 + A, -80 + A, lambda s: 10 + 18 * (1 - s), lambda s: 34 + 8 * s, 9, 11.0 * t,
          hx("#a98360"), twist=-0.6, blur=1)
    rev(cv, pj, "x", AXC, [-82 + A, 82 + A], [11, 11], hx("#c7d2e0"))
    rev(cv, pj, "x", AXC, [-60, 60], [44, 44], STEEL, fill_a=0.14, edge=hx("#9fb6d8"), edge_w=1.4)
    rev(cv, pj, "x", AXC, [-16, -9], [34, 34], hx("#b98d3a"))
    rev(cv, pj, "x", AXC, [-3 + A, 3 + A], [26, 26], mix(hx("#d6dee9"), RED, hit), edge=RED if hit > 0.4 else None,
        glow=hit, edge_w=2.2)
    rev(cv, pj, "x", AXC, [9, 16], [34, 34], hx("#b98d3a"))
    wheel(cv, pj, "x", AXC, 128 + A, 82 + A, lambda s: 10 + 13 * s, lambda s: 24 + 22 * s ** 1.6, 7, 11.0 * t,
          hx("#c7d2e0"), twist=0.75, splitters=True, blur=1)
    if hit > 0.25:
        s = 13 if shake > 0 else -13
        c0 = np.array(pj(s, 0, 0))
        rng = np.random.default_rng(int(t * 30))
        for _ in range(14):
            ang = rng.uniform(0, 6.28)
            r0, r1 = rng.uniform(40, 80), rng.uniform(100, 160)
            d = np.array([math.cos(ang), math.sin(ang) * 0.75])
            a_ = c0 + d * r0
            b_ = c0 + d * r1
            cv.drawLine(a_[0], a_[1], b_[0], b_[1], paint(YEL, a=0.8 * hit, stroke=3))
    brand.label(cv, t, "THRUST BEARING", tuple(pj(-12, -34, 0)), (540, 475), RED, T_THRUST - 0.15, T_FIX - 0.2)
    ga = eout(lin(t, T_LITTLE, T_LITTLE + 0.25))
    pill(cv, 540, 1200, "A LITTLE FLUTTER: PROBABLY FINE", font("inter_xb", 30), INK, border=GREEN, a=ga, align="center",
         tracking=1.5, dot=GREEN)
    gb = eout(lin(t, T_GARRETT - 0.05, T_GARRETT + 0.25))
    pill(cv, 540, 1290, "STAYING IN SURGE: EARLY FAILURE", font("inter_xb", 30), INK, border=RED, a=gb, align="center",
         tracking=1.5, dot=RED)
    brand.status_pill(cv, gb, "GARRETT'S WARNING", YEL)
    brand.note(cv, "ANIMATION SLOWED", k, dy=-90)
    cv.restore()


# ------------------------------------------------------------------ BOV
def bov_open(t):
    return ease(lin(t, T_OPEN - 0.1, T_OPEN + 0.25))


def draw_fix(cv, t):
    k = scene_k(t, T_FIX - 0.2, T_END + 0.2, 0.35, 0.3)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    op = bov_open(t)
    d = D_of(t) * 0 + (t - T_FIX) * 620
    # pipes
    pipe(cv, INLET, 62, hx("#5d7499"), glass=True)
    pipe(cv, DIS_A, 74, hx("#5d7499"), glass=True)
    pipe(cv, DIS_B, 74, hx("#5d7499"), glass=True)
    draw_engine(cv, 1.0)
    # hose
    hk = eout(lin(t, T_VAC - 0.1, T_VAC + 0.25))
    p_hose = paint(mix(hx("#3a4559"), AMBER, hk), stroke=7)
    p_hose.setPathEffect(skia.DashPathEffect.Make([14, 10], -t * 80))
    cv.drawPath(poly_path(HOSE, close=False), p_hose)
    if hk > 0:
        flow(cv, HOSE, t, 340, 42, AMBER, r=6, a=hk)
    # flows
    pres = 1 - 0.9 * op
    stream(cv, INLET, d, 44, lambda u: CYAN, 7, a=1.0)
    stream(cv, DIS_TO_BOV, d, 36, lambda u: p_col(pres * 0.9 * u + 0.1 * op), 7.5)
    if op < 1:
        stream(cv, DIS_A[_iB:], d, 36, lambda u: p_col(pres * (0.5 + 0.5 * u)), 7.5, a=1 - op, cluster=1.2)
    draw_compressor(cv, t, PJ)
    draw_throttle(cv, T_SHUT + 1, 1.0)
    # valve body
    x = BOV_X
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 44, 380, x + 44, 526), 14, 14), paint(hx("#0b111c"), a=0.82))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 44, 380, x + 44, 526), 14, 14), paint(hx("#9fb6d8"), stroke=3))
    for sx in (-1, 1):
        cv.drawRect(skia.Rect.MakeLTRB(x + sx * 44 - 4, 462, x + sx * 44 + 4, 502), paint(hx("#0b111c")))
    y_p = 512 - op * 78
    # spring
    ys = np.linspace(392, y_p - 14, 40)
    xs = x + 26 * np.sin(np.linspace(0, 6 * np.pi * 2, 40))
    cv.drawPath(poly_path(np.stack([xs, ys], 1), close=False), paint(hx("#c7d2e0"), stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 38, y_p - 14, x + 38, y_p + 14), 7, 7),
                 paint(mix(hx("#7f8ea6"), GREEN, op)))
    # vents
    if op > 0.2:
        vk = clamp((op - 0.2) / 0.8) * (1 - lin(t, T_OUTRO + 0.1, T_OUTRO + 0.6))
        flow(cv, VENT_L, t, 560, 26, AMBER, r=7.5, a=vk, seed=2)
        flow(cv, VENT_R, t, 560, 26, AMBER, r=7.5, a=vk, seed=4)
        cv.drawPath(poly_path(np.array([[x - 62, 528], [x + 62, 528]]), close=False), paint(hx("#5d7499"), stroke=2))
    lab1 = scene_k(t, T_BOV - 0.1, T_END, 0.25, 0.3)
    pill(cv, x - 40, 348, "BLOW OFF VALVE", font("inter_xb", 27), INK, border=GREEN, a=lab1, align="center", tracking=1.5, dot=GREEN)
    lab2 = scene_k(t, T_VAC - 0.1, T_ESC + 0.6, 0.25, 0.3)
    pill(cv, 780, 410, "ENGINE VACUUM", font("inter_xb", 27), INK, border=AMBER, a=lab2, align="center", tracking=1.5, dot=AMBER)
    brand.status_pill(cv, scene_k(t, T_FIX + 0.1, T_ESC + 0.5), "THROTTLE SHUT", AMBER)
    brand.stamp(cv, t, "NO BOUNCE", T_ESC - 0.05, dur=1.6, center=(540, 1240), color=GREEN, bg=hx("#07261a"))
    # PSSH
    sz = eback(lin(t, T_PSSH - 0.1, T_PSSH + 0.2))
    if sz > 0:
        ka = sz * (1 - lin(t, T_OUTRO - 0.1, T_OUTRO + 0.3))
        f_ = font("pop_b", 118 * (0.6 + 0.4 * sz))
        draw_text(cv, "PSSH", 450, 750, f_, YEL, a=clamp(ka), align="left", glow=14, glow_c=AMBER)
    cv.restore()


# ------------------------------------------------------------------ hook (world)
def draw_car(cv, x, y, s, t, a=1.0, lift=0.0):
    """Generic hatchback, side view (no badges). x, y: ground under the centre."""
    W_, H_ = 620 * s, 200 * s
    prof = np.array([[-1.0, 0.18], [-1.0, -0.12], [-0.96, -0.52], [-0.82, -0.88], [-0.4, -1.0], [0.1, -0.96],
                     [0.4, -0.62], [0.86, -0.42], [1.0, -0.20], [1.02, 0.12], [0.95, 0.24], [-0.95, 0.24]])
    body = np.stack([x + prof[:, 0] * W_ / 2, y - 62 * s + prof[:, 1] * H_], 1)
    glow = paint(hx("#3b6fb5"), a=a * 0.45, stroke=14 * s, blur=14 * s)
    pth = poly_path(spline(np.vstack([body, body[:1]]), 90))
    cv.drawPath(pth, glow)
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((x, y - H_ - 62 * s), (x, y + 30), [hx("#3a4a66"), hx("#1a2436"), hx("#0d1320")]))
    p.setAlphaf(a)
    cv.drawPath(pth, p)
    cv.drawPath(pth, paint(hx("#7f9ac2"), a=a * 0.8, stroke=2.5 * s))
    win_pts = np.array([[-0.88, -0.46], [-0.76, -0.78], [-0.4, -0.90], [0.08, -0.86], [0.30, -0.56], [-0.82, -0.46]])
    w = np.stack([x + win_pts[:, 0] * W_ / 2, y - 62 * s + win_pts[:, 1] * H_], 1)
    cv.drawPath(poly_path(spline(np.vstack([w, w[:1]]), 60)), paint(hx("#0a1220"), a=a))
    cv.drawPath(poly_path(w), paint(hx("#5d7499"), a=a * 0.5, stroke=2 * s))
    cv.drawLine(x - 62 * s, y - 62 * s - 0.46 * H_, x - 62 * s, y - 62 * s - 0.90 * H_, paint(hx("#5d7499"), a=a * 0.5, stroke=2 * s))
    # lights
    head = np.array([x + 0.96 * W_ / 2, y - 62 * s - 0.20 * H_])
    cv.drawCircle(head[0], head[1], 26 * s, paint(hx("#ffe9a8"), a=a * 0.5, blur=14 * s))
    cv.drawCircle(head[0], head[1], 9 * s, paint(hx("#fff6d6"), a=a))
    tail = np.array([x - 0.96 * W_ / 2, y - 62 * s - 0.16 * H_])
    brk = lift
    cv.drawCircle(tail[0], tail[1], 18 * s, paint(RED, a=a * (0.4 + 0.5 * brk), blur=10 * s))
    cv.drawCircle(tail[0], tail[1], 7 * s, paint(RED, a=a))
    # wheels
    for wx in (-0.62, 0.60):
        cx, cy, r = x + wx * W_ / 2, y - 26 * s, 62 * s
        cv.drawCircle(cx, cy, r, paint(hx("#0a0f18"), a=a))
        cv.drawCircle(cx, cy, r, paint(hx("#3a4456"), a=a, stroke=5 * s))
        cv.drawCircle(cx, cy, r * 0.56, paint(hx("#5a6577"), a=a))
        for i in range(5):
            ang = 7.0 * t + i * 2 * math.pi / 5
            cv.drawLine(cx, cy, cx + r * 0.52 * math.cos(ang), cy + r * 0.52 * math.sin(ang), paint(hx("#1a2130"), a=a, stroke=8 * s))
        cv.drawCircle(cx, cy, r * 0.12, paint(hx("#c7d2e0"), a=a))


def draw_world(cv, t, a, zoom=1.0):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    look.night_sky(cv, horizon=1030, t=t)
    road_y = 1110
    cv.drawRect(skia.Rect.MakeLTRB(0, 1030, 1080, 1920), paint(hx("#0b101a")))
    cv.drawRect(skia.Rect.MakeLTRB(0, 1030, 1080, 1034), paint(hx("#3b6fb5"), a=0.45))
    speed = 1450 * (1 - 0.35 * lin(t, 0.0, 2.0))
    of = (speed * t) % 280
    for i in range(-1, 6):
        x = -of + i * 280
        cv.drawRect(skia.Rect.MakeXYWH(x, 1200, 170, 12), paint(hx("#c7d2e0"), a=0.55))
    # motion streaks in the sky
    rng = np.random.default_rng(4)
    for i in range(14):
        y0 = rng.uniform(560, 1000)
        xo = rng.uniform(0, 1080)
        l = rng.uniform(70, 170)
        x = (xo - 1500 * t) % 1250 - 100
        cv.drawLine(x, y0, x + l, y0, paint(hx("#7f9ac2"), a=0.13, stroke=2.5))
    cx, cy = 720, road_y - 30
    cv.save()
    cv.translate(540, 900)
    cv.scale(zoom, zoom)
    cv.translate(-540, -900)
    shake = 2.0 * math.sin(t * 41) * math.sin(t * 17)
    draw_car(cv, 500, 1120 + shake, 1.15, t, lift=1.0)
    cv.restore()
    cv.restore()


def draw_hook(cv, t):
    if t > T_WHAT + 0.8:
        return
    zoom = 1 + 2.6 * ease(lin(t, T_WHAT - 0.1, T_WHAT + 0.55))
    a = 1 - lin(t, T_WHAT + 0.15, T_WHAT + 0.55)
    draw_world(cv, t, clamp(a), zoom=zoom)
    # STU pops
    for i, tt in enumerate([T_STU] + T_TU):
        k = eback(lin(t, tt - 0.03, tt + 0.13))
        o = lin(t, tt + 0.55, tt + 1.05)
        if k <= 0 or o >= 1:
            continue
        x = 690 - 30 * (i % 2) + 26 * i
        y = 900 - 95 * i - 50 * lin(t, tt, tt + 1.05)
        word = "STU" if i == 0 else "TU"
        draw_text(cv, word, x, y, font("pop_b", 96 - 6 * i), YEL, a=clamp(k) * (1 - clamp(o)), align="center", glow=10,
                  glow_c=AMBER)
    # engine-bay highlight on the question
    ka = win(t, T_MAKING - 0.15, T_WHAT + 0.5, 0.2, 0.3)
    if ka > 0:
        cv.drawCircle(760, 930, 112 + 8 * math.sin(t * 8), paint(YEL, a=0.75 * ka, stroke=5))
        cv.drawCircle(760, 930, 40, paint(RED, a=0.5 * ka, blur=20))
    brand.stamp(cv, t, "WHAT'S MAKING IT?", T_MAKING - 0.1, dur=1.35, center=(540, 1290), color=YEL, bg=hx("#2a2405"))


def draw(cv, t):
    kE = 1 - current.ending_k(t)
    cv.saveLayerAlpha(None, int(255 * clamp(kE)))
    draw_hook(cv, t)
    k_sys = scene_k(t, T_WHAT + 0.15, T_SURGE - 0.05, 0.45, 0.3)
    draw_air_path(cv, t, k_sys)
    draw_system_labels(cv, t)
    draw_top(cv, t)
    brand.stamp(cv, t, "SNAPPED SHUT", T_SHUT + 0.1, dur=1.2, center=(540, 1240), color=RED)
    brand.stamp(cv, t, "NOWHERE TO GO", T_NOWHERE, dur=1.3, center=(540, 1240), color=AMBER, bg=hx("#2a1c05"))
    brand.stamp(cv, t, "WHERE DOES IT GO?", T_WHERE - 0.05, dur=1.5, center=(540, 1240), color=YEL, bg=hx("#2a2405"))
    brand.stamp(cv, t, "BACKWARDS", T_BACK - 0.05, dur=1.3, center=(540, 1240), color=RED)
    draw_pressure_trace(cv, t)
    if T_FL0 - 0.1 < t < T_PROB + 0.3:
        pill(cv, 540, 1240, "TURBO FLUTTER", font("inter_xb", 34), INK, border=RED,
             a=win(t, T_FL0 - 0.1, T_PROB + 0.3, 0.2, 0.3), align="center", tracking=3, dot=RED)
    brand.stamp(cv, t, "COMPRESSOR SURGE", T_CALL - 0.05, dur=1.8, center=(540, 480), color=RED)
    draw_map(cv, t)
    draw_myth(cv, t)
    draw_harm(cv, t)
    draw_fix(cv, t)
    cv.restore()


# ================================================================== sound (synthesized here)
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _norm(x, pk=0.9):
    x = np.asarray(x, np.float64)
    x = x / (np.abs(x).max() + 1e-9) * pk
    n = int(0.005 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def _flutter(n_burst=8, per=0.145):
    """Compressor surge: chain of soft fluttering air bursts with a falling pitch."""
    from scipy import signal
    rng = np.random.default_rng(3)
    N = int((n_burst * per + 0.4) * SR)
    tt = np.arange(N) / SR
    x = np.zeros(N)
    b, a = signal.butter(2, [260 / (SR / 2), 2400 / (SR / 2)], "band")
    nz = signal.lfilter(b, a, rng.standard_normal(N))
    for i in range(n_burst):
        t0 = i * per * (1 + 0.04 * i)
        e = np.where(tt >= t0, np.exp(-(tt - t0) / 0.05), 0.0)
        tone = np.sin(2 * np.pi * (420 - 22 * i) * tt)
        x += (nz + 0.35 * tone) * e * (1 - 0.06 * i)
    return _norm(x, 0.85)


def _stu():
    """One bounce."""
    from scipy import signal
    rng = np.random.default_rng(8)
    N = int(0.18 * SR)
    tt = np.arange(N) / SR
    b, a = signal.butter(2, [320 / (SR / 2), 2600 / (SR / 2)], "band")
    x = signal.lfilter(b, a, rng.standard_normal(N)) * np.exp(-tt / 0.045) + 0.35 * np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / 0.035)
    return _norm(x, 0.8)


def _pssh():
    """Blow-off valve vent: bright air hiss with a sharp attack."""
    from scipy import signal
    rng = np.random.default_rng(6)
    N = int(1.0 * SR)
    tt = np.arange(N) / SR
    b, a = signal.butter(2, [1800 / (SR / 2), 11000 / (SR / 2)], "band")
    e = (1 - np.exp(-tt / 0.012)) * np.exp(-tt / 0.28)
    return _norm(signal.lfilter(b, a, rng.standard_normal(N)) * e, 0.8)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, x in {"flutter": _flutter(), "stu": _stu(), "pssh": _pssh()}.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_BACK
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(T_STU - 0.02, "flutter", 0.5), (T_MAKING - 0.1, "impact", 0.35), (T_WHAT + 0.05, "whoosh_big", 0.4),
           (T_WHEEL, "whoosh_up", 0.25), (T_HUNDRED, "tick", 0.25), (T_RAM, "whoosh_up", 0.25),
           (T_SHUT, "clunk", 0.45), (T_SHUT + 0.02, "impact", 0.35), (T_NOWHERE, "tick", 0.25),
           (T_SPIKES, "whoosh_up", 0.3), (T_WHERE, "impact", 0.3), (T_BACK - 0.02, "impact_long", 0.4),
           (T_REPEATS + 0.1, "whoosh_down", 0.2), (T_SURGE, "whoosh_big", 0.3), (T_LEFT, "impact", 0.3),
           (T_MYTH, "whoosh_down", 0.25), (T_REV, "tick", 0.3), (T_HARM, "whoosh_big", 0.3), (T_HAMMER, "clunk", 0.3),
           (T_THRUST, "clunk", 0.3), (T_FIX, "whoosh_big", 0.3), (T_VAC, "tick", 0.3), (T_OPEN, "clunk", 0.3),
           (T_ESC - 0.05, "pssh", 0.5), (T_PSSH - 0.05, "pssh", 0.75)]
    sfx += [(tb, "stu", 0.45 if tb < T_EVERY + 2 else 0.3) for tb in BOUNCES]
    sfx += [(tb, "stu", 0.25) for tb in BOUNCES if tb < T_EVERY - 1 and tb > T_BACK + 2.0][:0]
    return {"build": (T_RE, T_BACK), "drop": (T_BACK, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.75}
