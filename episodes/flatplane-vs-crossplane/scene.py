"""Flat plane vs cross plane V8 visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  HOOK   (hook)        night road, two generic V8 cars: a muscle coupe throwing uneven rumble rings, a low mid-engine
                       car throwing fast even rings. BURBLE / SCREAM tags.
  CRANK  (what..cost)  big 3D crankshaft, four throws on one shaft. Pin angles morph cross (0/90/270/180) -> flat
                       (0/180/180/0); counterweights shrink on the flat crank. End-on pin clock in the middle.
  DIALS  (even..scream) one 720-degree firing dial per bank. The hand is the real crank angle / 2; marks are the bank's
                       firing angles (cross: per-bank 90/180/270/180, flat: every 180). Gap labels on the arcs.
  COST   (cost)        the flat crank bounces at twice crank speed (second-order shake); morph back to cross; then a
                       tach sweeps to 8,600 for the Corvette Z06.
Audio: engine notes synthesized from the same firing model in _engine() (no recordings).
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import rev

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_EIGHT = F("hook", "eight")
T_FERRARI = F("hook", "Ferrari")
T_SCREAM0 = F("hook", "scream,")
T_MUSCLE0 = F("hook", "muscle")
T_BURBLES = F("hook", "burbles?")
T_WHAT = L("what")["start"]
T_FLAT0 = F("what", "flat")
T_CROSS0 = F("what", "cross")
T_CROSS = L("cross")["start"]
T_CRANKS = F("cross", "crank's")
T_PINS = F("cross", "pins")
T_NINETY = F("cross", "ninety")
T_ENDV = F("cross", "end,")
T_ACROSS = F("cross", "cross.")
T_EVEN = L("even")["start"]
T_FIRES = F("even", "fires")
T_EV90 = F("even", "ninety")
T_PERF = F("even", "Perfectly")
T_RE = L("rehook")["start"]
T_WHERE = F("rehook", "where")
T_KEY = L("key")["start"]
T_OWN = F("key", "own")
T_ONESIDE = F("key", "one")
T_UNEVEN = F("key", "uneven")
T_SHORT = F("key", "short")
T_LONG = F("key", "long")
T_LONGER = F("key", "longer")
T_STUMBLE = F("key", "stumble")
T_BURBLE = F("key", "burble.")
T_FLAT = L("flat")["start"]
T_FLATTEN = F("flat", "flatten")
T_PLANE = F("flat", "plane,")
T_HALF = F("flat", "half")
T_ALT = F("flat", "alternates.")
LR_WORDS = [(F("flat", "left"), 0), (F("flat", "right"), 1), (F("flat", "left", nth=1), 0), (F("flat", "right", nth=1), 1)]
T_SCR = L("scream")["start"]
T_EVENLY = F("scream", "evenly,")
T_FOUR = F("scream", "four")
T_LIGHTER = F("scream", "lighter")
T_REVS = F("scream", "revs")
T_SCREAM = F("scream", "scream.")
T_COST = L("cost")["start"]
T_CATCH = F("cost", "catch?")
T_SHAKES = F("cost", "shakes")
T_STAYED = F("cost", "stayed")
T_CORV = F("cost", "Corvette")
T_WENT = F("cost", "went")
T_EIGHTY = F("cost", "eighty")
T_RPM = F("cost", "RPM.")
T_OUTRO = L("outro")["start"]

# ================================================================== crank model
CROSS_PINS = np.array([0.0, 90.0, 270.0, 180.0])
FLAT_PINS = np.array([0.0, 180.0, 180.0, 360.0])
FIRE = {  # 720-degree firing angles per bank (research.md)
    "cross": ([0.0, 270.0, 450.0, 540.0], [90.0, 180.0, 360.0, 630.0]),
    "flat": ([0.0, 180.0, 360.0, 540.0], [90.0, 270.0, 450.0, 630.0]),
}


def flat_k(t):
    """0 = cross-plane, 1 = flat-plane."""
    k = ease(lin(t, T_FLATTEN - 0.05, T_FLATTEN + 1.1))
    k *= 1 - ease(lin(t, T_STAYED - 0.1, T_STAYED + 0.8))
    k += ease(lin(t, T_WENT - 0.2, T_WENT + 0.6)) * (1 if t > T_STAYED else 0)
    return clamp(k)


def mode(t):
    return "flat" if flat_k(t) > 0.5 else "cross"


def cw_k(t):
    """Counterweight size: heavy on the cross crank, shrinks when the flat crank is called lighter."""
    f = flat_k(t)
    light = ease(lin(t, T_LIGHTER - 0.1, T_LIGHTER + 0.6))
    return 1.0 - 0.5 * f * max(light, 1.0 if t > T_COST else 0.0)


def omega(t):
    """Crank speed in deg/s (animation slowed). Spins up when the flat crank 'revs higher', and for the Z06."""
    base = 200.0
    up = ease(lin(t, T_REVS - 0.1, T_REVS + 0.9)) * (1 - ease(lin(t, T_COST - 0.2, T_CATCH + 0.3)))
    z = ease(lin(t, T_EIGHTY - 0.4, T_RPM + 0.2))
    return base * (1 + 2.2 * up + 2.6 * z)


DT = 1 / 240
_TS = np.arange(-1.0, T_TOTAL + 2.0, DT)
_CUM = np.concatenate([[0.0], np.cumsum([omega(x) * DT for x in _TS[:-1]])])


def crank_deg(t):
    return float(np.interp(t, _TS, _CUM))


def t_at_deg(d):
    return float(np.interp(d, _CUM, _TS))


def pin_angles(t):
    f = flat_k(t)
    return (1 - f) * CROSS_PINS + f * FLAT_PINS + crank_deg(t)


def last_fire_age(t, mark):
    """Seconds since the dial hand last passed `mark` (720-degree cycle)."""
    d = crank_deg(t)
    back = (d - mark) % 720.0
    return t - t_at_deg(d - back)


# ================================================================== drawing: crank
PJ0 = Proj(510, 650, 1.12, dx=0.46, dy=-0.30)
THROW_X = [-225.0, -75.0, 75.0, 225.0]
R_T = 68.0
WEB_T = 16.0
STEEL_C = hx("#9aa8bd")
PIN_C = hx("#c9d4e3")


def shake_dy(t):
    k = win(t, T_SHAKES - 0.1, T_STAYED + 0.2, 0.2, 0.4) * flat_k(t)
    return 13.0 * k * math.sin(math.radians(2 * crank_deg(t)))


def _yz(th, r):
    a = math.radians(th)
    return -r * math.cos(a), r * math.sin(a)


def _web_face(pj, x, th, cw):
    py, pz = _yz(th, R_T)
    # capsule from axis to pin
    a = math.radians(th)
    nY, nZ = math.sin(a), math.cos(a)   # perpendicular in the (Y, z) plane
    pts = []
    for ang in np.linspace(-90, 90, 13):
        b = math.radians(th + ang)
        pts.append((py - 32 * math.cos(b), pz + 32 * math.sin(b)))
    # counterweight sector, opposite the pin
    rr = 40 + 50 * cw
    for ang in np.linspace(180 - 62 * (0.6 + 0.4 * cw), 180 + 62 * (0.6 + 0.4 * cw), 15):
        b = math.radians(th + 180 + (ang - 180))
        pts.append((-rr * math.cos(b), rr * math.sin(b)))
    P = np.array([pj(x, Y, Z) for Y, Z in pts])
    return P


def draw_crank(cv, t, a, glow_pins=0.0, flat_col=0.0):
    if a <= 0:
        return
    pj = PJ0.shifted(dy=shake_dy(t))
    ths = pin_angles(t)
    cw = cw_k(t)
    items = []
    # main journals between throws (+ nose and flange)
    mains = [(-330, THROW_X[0] - 40), (THROW_X[0] + 40, THROW_X[1] - 40), (THROW_X[1] + 40, THROW_X[2] - 40),
             (THROW_X[2] + 40, THROW_X[3] - 40), (THROW_X[3] + 40, 318)]
    for x0, x1 in mains:
        items.append((0.0, ("main", x0, x1)))
    items.append((0.0, ("flange",)))
    for i, xt in enumerate(THROW_X):
        th = ths[i]
        py, pz = _yz(th, R_T)
        items.append((pz, ("pin", i, xt, py, pz)))
        for sx in (-1, 1):
            items.append((pz * 0.5 - 1e-3 * sx, ("web", i, xt + sx * 32, th)))
    items.sort(key=lambda e: -e[0])
    pin_edge = mix(CYAN, RED, flat_col)
    for _, it in items:
        kind = it[0]
        if kind == "main":
            rev(cv, pj, "x", (0.0, 0.0), [it[1], it[2]], [24, 24], STEEL_C, alpha=a, edge=hx("#5b6b84"), edge_w=1.2)
        elif kind == "flange":
            rev(cv, pj, "x", (0.0, 0.0), [318, 342], [92, 92], hx("#6f7d93"), alpha=a, edge=hx("#9fb6d8"), edge_w=1.2)
        elif kind == "pin":
            _, i, xt, py, pz = it
            rev(cv, pj, "x", (py, pz), [xt - 26, xt + 26], [22, 22], PIN_C, alpha=a, edge=mix(pin_edge, YEL, glow_pins),
                edge_w=2.2, glow=0.3 + glow_pins)
        else:
            _, i, x, th = it
            for j in range(5):
                P = _web_face(pj, x - WEB_T / 2 + WEB_T * j / 4, th, cw)
                c = shade(hx("#7d8ba1"), 0.55 + 0.12 * j)
                cv.drawPath(poly_path(P), paint(c, a=a))
            cv.drawPath(poly_path(P), paint(hx("#b7c4d6"), a=a * 0.9, stroke=1.6))


def cw_anchor(t):
    pj = PJ0.shifted(dy=shake_dy(t))
    py, pz = _yz(pin_angles(t)[2], R_T)
    return tuple(pj(THROW_X[2] + 32, -py * 1.0, -pz * 1.0))


def pin_anchor(t, i):
    pj = PJ0.shifted(dy=shake_dy(t))
    py, pz = _yz(pin_angles(t)[i], R_T)
    return tuple(pj(THROW_X[i], py, pz))


# ================================================================== drawing: end view + dials
DIAL_Y = 1060
END_C = (540, DIAL_Y)
DIAL_C = [(262, DIAL_Y), (818, DIAL_Y)]
DIAL_R = 118


def draw_end_view(cv, t, a):
    if a <= 0:
        return
    cx, cy = END_C
    cv.drawCircle(cx, cy, 86, paint(hx("#0a1220"), a=0.9 * a))
    cv.drawCircle(cx, cy, 86, paint(hx("#3a4a66"), a=a, stroke=2.5))
    draw_text(cv, "END VIEW", cx, cy - 102, font("inter_xb", 22), MUTED, a=a, align="center", tracking=2)
    ths = pin_angles(t)
    f = flat_k(t)
    c = mix(CYAN, RED, f)
    for i, th in enumerate(ths):
        b = math.radians(th)
        x, y = cx + 60 * math.sin(b), cy - 60 * math.cos(b)
        cv.drawLine(cx, cy, x, y, paint(c, a=a * 0.85, stroke=8, cap=skia.Paint.kRound_Cap))
    for i, th in enumerate(ths):
        b = math.radians(th)
        x, y = cx + 60 * math.sin(b), cy - 60 * math.cos(b)
        cv.drawCircle(x, y, 13, paint(PIN_C, a=a))
        cv.drawCircle(x, y, 13, paint(c, a=a, stroke=2.5))
    cv.drawCircle(cx, cy, 9, paint(INK, a=a))


GAP_COL = {90: AMBER, 180: CYAN, 270: RED}


def draw_dial(cv, t, side, a, focus=1.0):
    if a <= 0:
        return
    cx, cy = DIAL_C[side]
    m = mode(t)
    marks = FIRE[m][side]
    aa = a * (0.35 + 0.65 * focus)
    cv.drawCircle(cx, cy, DIAL_R + 8, paint(hx("#0a1220"), a=0.92 * a))
    cv.drawCircle(cx, cy, DIAL_R, paint(hx("#3a4a66"), a=aa, stroke=3))
    for k in range(8):
        b = math.radians(k * 45)
        cv.drawLine(cx + (DIAL_R - 10) * math.sin(b), cy - (DIAL_R - 10) * math.cos(b),
                    cx + DIAL_R * math.sin(b), cy - DIAL_R * math.cos(b), paint(MUTED, a=aa * 0.6, stroke=2))
    name = ["LEFT BANK", "RIGHT BANK"][side]
    draw_text(cv, name, cx, cy - DIAL_R - 24, font("inter_xb", 24), INK, a=aa, align="center", tracking=2)
    # gap labels on the arcs
    kg = win(t, T_UNEVEN - 0.3, T_FLATTEN, 0.3, 0.3) if m == "cross" else win(t, T_EVENLY - 0.3, T_CATCH, 0.3, 0.3)
    if m == "cross" and side == 1:
        hl = [(T_SHORT, 90.0), (T_LONG, 180.0), (T_LONGER, 360.0)]
    else:
        hl = []
    if kg > 0:
        for i, m0 in enumerate(marks):
            m1 = marks[(i + 1) % 4] + (720 if i == 3 else 0)
            gap = int(round(m1 - m0))
            mid = math.radians((m0 + m1) / 4)
            c = GAP_COL.get(gap, CYAN) if m == "cross" else GREEN
            big = 0.0
            for tw, mm in hl:
                if abs(mm - m0) < 1:
                    big = win(t, tw - 0.1, T_STUMBLE + 0.6, 0.15, 0.3)
            if gap and m == "cross" and side == 1:
                rr = skia.Rect.MakeLTRB(cx - DIAL_R + 14, cy - DIAL_R + 14, cx + DIAL_R - 14, cy + DIAL_R - 14)
                cv.drawArc(rr, -90 + m0 / 2 + 3, (m1 - m0) / 2 - 6, False, paint(c, a=a * kg * (0.35 + 0.65 * big), stroke=7 + 5 * big))
            fs = 22 + 8 * big
            draw_text(cv, f"{gap}°", cx + 72 * math.sin(mid), cy - 72 * math.cos(mid) + 9, font("inter_xb", int(fs)), c,
                      a=aa * kg, align="center")
    # firing marks
    for mk in marks:
        b = math.radians(mk / 2)
        x, y = cx + DIAL_R * math.sin(b), cy - DIAL_R * math.cos(b)
        age = last_fire_age(t, mk)
        fk = math.exp(-age / 0.16) if age < 0.8 else 0.0
        cv.drawCircle(x, y, 11 + 9 * fk, paint(mix(hx("#7a5a20"), YEL, fk), a=aa))
        if fk > 0.03:
            cv.drawCircle(x, y, 26 + 30 * (1 - fk), paint(AMBER, a=aa * fk, stroke=4))
            cv.drawCircle(cx, cy, DIAL_R + 6, paint(AMBER, a=aa * 0.5 * fk, stroke=6, blur=6))
    # hand = crank angle / 2
    b = math.radians((crank_deg(t) % 720) / 2)
    cv.drawLine(cx, cy, cx + (DIAL_R - 18) * math.sin(b), cy - (DIAL_R - 18) * math.cos(b),
                paint(INK, a=aa, stroke=6, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(cx, cy, 10, paint(INK, a=aa))
    # exhaust puffs under the dial
    for mk in marks:
        age = last_fire_age(t, mk)
        look.puff(cv, cx, cy + DIAL_R + 26, age, life=0.8, size=22, c=hx("#c9b38a"), a=0.45 * aa * win(t, T_OWN - 0.2, T_CATCH, 0.3, 0.3),
                  drift=(0, 70))


# ================================================================== hook (world)
MUSCLE = np.array([[-1.0, 0.1], [-0.99, -0.32], [-0.9, -0.46], [-0.52, -0.5], [-0.36, -0.88], [0.06, -0.92],
                   [0.28, -0.54], [0.94, -0.47], [1.0, -0.22], [1.01, 0.12], [0.93, 0.24], [-0.95, 0.24]])
MUSCLE_W = np.array([[-0.47, -0.52], [-0.33, -0.83], [0.04, -0.86], [0.22, -0.54]])
SUPER = np.array([[-1.0, 0.04], [-0.99, -0.36], [-0.64, -0.5], [-0.32, -0.84], [0.08, -0.88], [0.44, -0.42],
                  [0.97, -0.2], [1.03, 0.04], [0.95, 0.22], [-0.95, 0.22]])
SUPER_W = np.array([[-0.28, -0.78], [0.06, -0.82], [0.36, -0.44], [-0.1, -0.5]])


def draw_car(cv, x, y, s, prof, wprof, body_c, rim_c, a=1.0, H=175):
    W_, H_ = 690 * s, H * s
    body = np.stack([x + prof[:, 0] * W_ / 2, y - 62 * s + prof[:, 1] * H_], 1)
    from ev.parts import spline
    pth = poly_path(spline(np.vstack([body, body[:1]]), 110))
    cv.drawPath(pth, paint(rim_c, a=a * 0.42, stroke=14 * s, blur=14 * s))
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((x, y - H_ - 62 * s), (x, y + 30), [body_c, hx("#1a2436"), hx("#0d1320")]))
    p.setAlphaf(a)
    cv.drawPath(pth, p)
    cv.drawPath(pth, paint(rim_c, a=a * 0.85, stroke=2.5 * s))
    w = np.stack([x + wprof[:, 0] * W_ / 2, y - 62 * s + wprof[:, 1] * H_], 1)
    cv.drawPath(poly_path(spline(np.vstack([w, w[:1]]), 60)), paint(hx("#0a1220"), a=a))
    for wx in (-0.60, 0.62):
        cx, cy, r = x + wx * W_ / 2, y - 26 * s, 60 * s
        cv.drawCircle(cx, cy, r, paint(hx("#0a0f18"), a=a))
        cv.drawCircle(cx, cy, r, paint(hx("#3a4456"), a=a, stroke=5 * s))
        cv.drawCircle(cx, cy, r * 0.56, paint(hx("#5a6577"), a=a))
    head = (x + 0.96 * W_ / 2, y - 62 * s - 0.2 * H_)
    cv.drawCircle(head[0], head[1], 26 * s, paint(hx("#ffe9a8"), a=a * 0.55, blur=14 * s))
    tail = (x - 0.97 * W_ / 2, y - 62 * s - 0.18 * H_)
    cv.drawCircle(tail[0], tail[1], 16 * s, paint(RED, a=a * 0.8, blur=10 * s))
    return np.array([x - 1.0 * W_ / 2 + 4, y - 50 * s])


def rings(cv, t, tp, times, col, speed, life, a, width):
    for tr in times:
        age = t - tr
        if 0 < age < life:
            r = 22 + speed * age
            cv.drawArc(skia.Rect.MakeLTRB(tp[0] - r, tp[1] - r * 0.8, tp[0] + r, tp[1] + r * 0.8), 120, 120, False,
                       paint(col, a=a * 0.7 * (1 - age / life), stroke=width))


# per-bank cross-plane pattern (fractions of a 720 cycle) for the muscle car rings
_CROSS_FR = [x / 720 for x in FIRE["cross"][1]]
MUSCLE_RINGS = [c * 0.95 + f * 0.95 for c in range(-1, 12) for f in _CROSS_FR]
SUPER_RINGS = [k * 0.085 for k in range(-5, 120)]


def draw_hook(cv, t):
    if t > T_CROSS:
        return
    a = clamp(1 - lin(t, T_WHAT + 0.3, T_WHAT + 0.8))
    if a <= 0:
        return
    zoom = 1 + 2.0 * ease(lin(t, T_WHAT, T_WHAT + 0.8))
    cv.saveLayerAlpha(None, int(255 * a))
    look.night_sky(cv, horizon=760, t=t)
    cv.drawRect(skia.Rect.MakeLTRB(0, 760, 1080, 1920), paint(hx("#0b101a")))
    cv.drawRect(skia.Rect.MakeLTRB(0, 760, 1080, 763), paint(hx("#3b6fb5"), a=0.45))
    for k in range(7):  # lane dashes, scrolling (the cars are cruising)
        x = (k * 200 - (t * 520) % 200)
        cv.drawRect(skia.Rect.MakeXYWH(x, 1090, 110, 8), paint(hx("#c9d2e0"), a=0.35))
    cv.save()
    cv.translate(560, 1180)
    cv.scale(zoom, zoom)
    cv.translate(-560, -1180)
    sh = 2.5 * math.sin(t * 41) * math.sin(t * 13)
    tp1 = draw_car(cv, 560, 990 + sh, 0.78, MUSCLE, MUSCLE_W, hx("#4a3a5a"), hx("#9a86c2"))
    rings(cv, t, tp1, MUSCLE_RINGS, AMBER, 300, 1.0, 1.0, 6)
    tp2 = draw_car(cv, 520, 1290 + 0.6 * math.sin(t * 90), 0.98, SUPER, SUPER_W, hx("#5a2a2a"), hx("#ff7a6a"), H=150)
    rings(cv, t, tp2, SUPER_RINGS, RED, 700, 0.45, 1.0, 3)
    cv.restore()
    kv = win(t, T_EIGHT - 0.1, T_WHAT + 0.2, 0.2, 0.3)
    if kv > 0:
        pill(cv, 820, 860, "V8", font("inter_blk", 34), INK, border=CYAN, a=kv, align="center", tracking=3)
        pill(cv, 820, 1150, "V8", font("inter_blk", 34), INK, border=CYAN, a=kv, align="center", tracking=3)
    ks = win(t, T_SCREAM0 - 0.1, T_WHAT + 0.2, 0.2, 0.3)
    if ks > 0:
        pill(cv, 250, 1150, "SCREAM", font("inter_xb", 34), INK, border=RED, a=ks, align="center", tracking=3, dot=RED)
    kb = win(t, T_BURBLES - 0.1, T_WHAT + 0.2, 0.2, 0.3)
    if kb > 0:
        pill(cv, 250, 860, "BURBLE", font("inter_xb", 34), INK, border=AMBER, a=kb, align="center", tracking=3, dot=AMBER)
    cv.restore()
    brand.stamp(cv, t, "WHY?", T_BURBLES + 0.05, dur=1.3, center=(540, 1340), color=YEL, bg=hx("#2a2405"))


# ================================================================== overlays
def draw_top(cv, t):
    k = win(t, T_CROSS + 0.1, T_OUTRO - 0.05, 0.3, 0.3)
    if k <= 0:
        return
    f = flat_k(t)
    brand.status_pill(cv, k, "FLAT PLANE" if f > 0.5 else "CROSS PLANE", RED if f > 0.5 else CYAN)
    kr = k * win(t, T_NINETY - 0.1, T_RE, 0.3, 0.3)
    if kr > 0:
        brand.readout(cv, kr, "90°", "BETWEEN PINS")
    kr2 = k * win(t, T_HALF - 0.1, T_REVS, 0.3, 0.3)
    if kr2 > 0:
        brand.readout(cv, kr2, "180°", "BETWEEN PINS")
    brand.note(cv, "ANIMATION SLOWED · SOUNDS SYNTHESIZED", k * win(t, T_CROSS + 0.3, T_EIGHTY - 0.3, 0.3, 0.3))


def draw_labels(cv, t):
    brand.label(cv, t, "CRANKSHAFT", (300, 640), (90, 470), INK, T_CRANKS - 0.15, T_PINS + 0.2)
    brand.label(cv, t, "CRANK PINS", pin_anchor(t, 2), (600, 470), YEL, T_PINS - 0.1, T_ENDV)
    brand.label(cv, t, "COUNTERWEIGHTS", cw_anchor(t), (560, 470), AMBER, T_LIGHTER - 0.1, T_SCREAM)


def draw_mid_pills(cv, t):
    k = win(t, T_FLAT0 - 0.1, T_CROSS + 0.2, 0.2, 0.3)
    if k > 0:
        pill(cv, 330, 1030, "CROSS PLANE", font("inter_xb", 36), INK, border=CYAN, a=k * eout(lin(t, T_CROSS0 - 0.1, T_CROSS0 + 0.1)),
             align="center", tracking=2, dot=CYAN)
        pill(cv, 760, 1030, "FLAT PLANE", font("inter_xb", 36), INK, border=RED, a=k, align="center", tracking=2, dot=RED)
    k2 = win(t, T_EV90 - 0.1, T_RE + 0.3, 0.2, 0.3)
    if k2 > 0:
        pill(cv, 540, 1232, "ALL 8 TOGETHER: A BANG EVERY 90°", font("inter_xb", 28), INK, border=GREEN, a=k2, align="center",
             tracking=1.5, dot=GREEN)
    k3 = win(t, T_OWN - 0.1, T_UNEVEN, 0.2, 0.3)
    if k3 > 0:
        pill(cv, 540, 1232, "ONE EXHAUST PER BANK", font("inter_xb", 28), INK, border=AMBER, a=k3, align="center", tracking=1.5, dot=AMBER)
    k4 = win(t, T_FOUR - 0.1, T_LIGHTER + 0.1, 0.2, 0.3)
    if k4 > 0:
        pill(cv, 540, 1232, "EACH BANK = AN INLINE FOUR", font("inter_xb", 28), INK, border=GREEN, a=k4, align="center", tracking=1.5, dot=GREEN)
    k5 = win(t, T_STAYED - 0.1, T_CORV - 0.05, 0.2, 0.2)
    if k5 > 0:
        pill(cv, 540, 1232, "MOST BIG V8s: CROSS PLANE", font("inter_xb", 28), INK, border=CYAN, a=k5, align="center", tracking=1.5, dot=CYAN)
    k6 = win(t, T_CORV - 0.05, T_OUTRO, 0.2, 0.3)
    if k6 > 0:
        pill(cv, 540, 1290, "2023 CORVETTE Z06 · FLAT PLANE", font("inter_xb", 28), INK, border=RED, a=k6, align="center", tracking=1.5, dot=RED)
    # LEFT / RIGHT call-outs
    for tw, side in LR_WORDS:
        kk = win(t, tw - 0.05, tw + 0.45, 0.08, 0.2)
        if kk > 0:
            cx, cy = DIAL_C[side]
            draw_text(cv, "L" if side == 0 else "R", cx, cy + 22, font("inter_blk", 88), RED, a=kk, align="center", glow=10, glow_c=RED)


def draw_shake(cv, t):
    k = win(t, T_SHAKES - 0.1, T_STAYED, 0.2, 0.3) * flat_k(t)
    if k <= 0:
        return
    for x in (92,):
        y0 = 650 + shake_dy(t)
        cv.drawLine(x, y0 - 70, x, y0 + 70, paint(RED, a=k, stroke=6))
        for s in (-1, 1):
            cv.drawPath(poly_path([(x - 16, y0 + s * 52), (x + 16, y0 + s * 52), (x, y0 + s * 76)]), paint(RED, a=k))


def draw_gauge(cv, t):
    k = win(t, T_CORV - 0.1, T_OUTRO + 0.4, 0.35, 0.3)
    if k <= 0:
        return
    v = 900 + 7700 * ease(lin(t, T_EIGHTY - 0.4, T_RPM + 0.1))
    v += 25 * math.sin(t * 40) * (1 if t > T_RPM else 0)
    brand.gauge(cv, 540, 900, 250, min(v, 8600), vmax=9000, redline=8600, alpha=k)


def draw(cv, t):
    kE = 1 - current.ending_k(t)
    cv.saveLayerAlpha(None, int(255 * clamp(kE)))
    draw_hook(cv, t)
    ka = win(t, T_WHAT + 0.35, T_CORV + 0.1, 0.45, 0.35)
    glow = win(t, T_PINS - 0.1, T_ENDV, 0.2, 0.3)
    draw_crank(cv, t, ka, glow_pins=glow, flat_col=flat_k(t))
    kd = win(t, T_ENDV - 0.15, T_CORV - 0.05, 0.3, 0.3)
    draw_end_view(cv, t, kd)
    kdi = win(t, T_FIRES - 0.2, T_CORV - 0.05, 0.3, 0.3)
    focus_r = win(t, T_ONESIDE - 0.1, T_FLATTEN - 0.2, 0.25, 0.3)
    draw_dial(cv, t, 0, kdi, focus=1 - focus_r)
    draw_dial(cv, t, 1, kdi, focus=1.0)
    draw_gauge(cv, t)
    draw_shake(cv, t)
    draw_labels(cv, t)
    draw_top(cv, t)
    draw_mid_pills(cv, t)
    brand.stamp(cv, t, "A CROSS", T_ACROSS - 0.05, dur=1.4, center=(540, 1318), color=CYAN, bg=hx("#07202a"))
    brand.stamp(cv, t, "PERFECTLY EVEN", T_PERF - 0.05, dur=1.5, center=(540, 1318), color=GREEN, bg=hx("#07261a"))
    brand.stamp(cv, t, "WHERE'S THE BURBLE?", T_WHERE - 0.05, dur=1.7, center=(540, 1318), color=YEL, bg=hx("#2a2405"))
    brand.stamp(cv, t, "THAT'S THE BURBLE", T_STUMBLE - 0.05, dur=1.9, center=(540, 1318), color=RED)
    brand.stamp(cv, t, "HALF A TURN APART", T_HALF - 0.05, dur=1.5, center=(540, 1318), color=RED)
    brand.stamp(cv, t, "THAT'S THE SCREAM", T_SCREAM - 0.05, dur=1.5, center=(540, 1318), color=RED)
    brand.stamp(cv, t, "IT SHAKES", T_SHAKES - 0.05, dur=1.3, center=(540, 1318), color=AMBER, bg=hx("#2a1a05"))
    cv.restore()


# ================================================================== sound
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _engine(dur, kind, rpm0, rpm1=None, seed=3):
    """V8 exhaust note from the firing model. kind 'cross': per-bank uneven pulses, one bank louder (as heard from
    one side), low-passed -> burble. kind 'flat': both banks even, alternating -> fast, even buzz."""
    from scipy import signal
    rpm1 = rpm0 if rpm1 is None else rpm1
    N = int(dur * SR)
    tt = np.arange(N) / SR
    rpm = rpm0 + (rpm1 - rpm0) * (tt / dur) ** 1.4
    ang = np.cumsum(rpm * 6.0 / SR)          # crank degrees
    x = np.zeros(N)
    rng = np.random.default_rng(seed)
    left, right = FIRE[kind]
    gains = (1.0, 0.55) if kind == "cross" else (1.0, 0.95)
    for marks, g in ((left, gains[0]), (right, gains[1])):
        for m in marks:
            k = np.floor((ang - m) / 720.0)
            idx = np.where(np.diff(k) > 0)[0] + 1
            for j in idx:
                interval = 60.0 / rpm[j] / 4.0           # time per 90 crank degrees
                tau = min(0.022, 0.55 * interval)
                n = min(N - j, int(6 * tau * SR))
                e = np.exp(-np.arange(n) / (tau * SR))
                x[j:j + n] += g * rng.uniform(0.85, 1.1) * e * (0.7 + 0.3 * rng.standard_normal(n))
    if kind == "cross":
        b, a = signal.butter(2, [30 / (SR / 2), 380 / (SR / 2)], "band")
        x = signal.lfilter(b, a, x)
    else:
        b, a = signal.butter(2, [120 / (SR / 2), 5200 / (SR / 2)], "band")
        x = np.tanh(2.2 * signal.lfilter(b, a, x) / (np.abs(x).max() + 1e-9))
    n = int(0.06 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return (x / (np.abs(x).max() + 1e-9) * 0.85).astype(np.float32)


CUES = {
    "burble_hook": (0.0, T_SCREAM0, "cross", 900, None),
    "scream_hook": (T_SCREAM0, T_MUSCLE0 + 0.2, "flat", 7200, 8200),
    "burble_hook2": (T_MUSCLE0 + 0.2, T_WHAT + 0.5, "cross", 950, None),
    "burble_key": (T_UNEVEN - 0.2, T_FLAT + 0.3, "cross", 850, None),
    "scream_flat": (T_EVENLY - 0.2, T_SCREAM + 1.0, "flat", 6000, 7600),
    "scream_z06": (T_EIGHTY - 0.4, T_RPM + 0.9, "flat", 3000, 8600),
}


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for i, (name, (t0, t1, kind, r0, r1)) in enumerate(CUES.items()):
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), _engine(max(t1 - t0, 0.5), kind, r0, r1, seed=11 + i), SR)


BEAT_ANCHOR = T_STUMBLE
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    gains = {"burble_hook": 0.75, "scream_hook": 0.55, "burble_hook2": 0.7, "burble_key": 0.7, "scream_flat": 0.42,
             "scream_z06": 0.5}
    sfx = [(CUES[n][0], n, gains[n]) for n in CUES]
    sfx += [(T_WHAT + 0.05, "whoosh_big", 0.35), (T_PINS, "tick", 0.3), (T_ACROSS, "impact", 0.3), (T_FIRES, "whoosh_up", 0.25),
            (T_PERF, "tick", 0.3), (T_WHERE, "impact", 0.3), (T_SHORT, "tick", 0.3), (T_LONG, "tick", 0.3),
            (T_LONGER, "tick", 0.3), (T_STUMBLE, "impact_long", 0.38), (T_FLATTEN, "clunk", 0.3), (T_HALF, "whoosh_down", 0.25),
            (T_SCREAM, "impact", 0.3), (T_SHAKES, "clunk", 0.25), (T_STAYED, "whoosh_down", 0.25), (T_CORV, "whoosh_up", 0.3)]
    return {"build": (T_RE, T_KEY), "drop": (T_KEY, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.6}
