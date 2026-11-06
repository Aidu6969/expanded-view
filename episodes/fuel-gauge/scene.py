"""Fuel gauge visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  STATION (hook, what)    night gas station, generic hatchback filling up; fuel flows down the hose, the dash gauge
                          climbs to F and the nozzle clicks off. The car drives away (background scrolls), miles
                          count up while the needle stays on F. Both ends of the dial flash; the body turns to
                          glass over the tank and the camera pushes in.
  TANK    (sender, how)   oddly shaped tank cutaway (glass), fuel volume -> surface level from the real profile,
                          float on a pivoting arm (stops at top and bottom), wiper on a resistor card (magnified
                          bubble), signal wire to the gauge; fuel is drawn off to the engine and everything follows.
  SLOSH   (slosh)         the fuel surface rocks on BRAKE and TURN; the float bobs; raw sender signal (amber, jumpy)
                          vs the averaged signal that drives the needle (cyan, smooth), traced live.
  CURVE   (rehook, key2)  needle vs fuel in the tank: a linear gauge (dashed) vs the real one: flat at F, then
                          faster; regions FLOAT PINNED + TUNED ON PURPOSE; Ford's 20-30 miles on F.
  PINNED  (key1)          full tank, float against its top stop; fuel drops, float and needle don't move.
  EMPTY   (empty)         float on its bottom stop, gauge on E, fuel still in the tank; "real empty" tick past E.
  DIAL    (outro)         big gauge, the hidden fuel at BOTH ends glowing (pays off "what's it hiding?").

Model (illustrative, not one specific car): the tank profile's area gives level <-> volume (non-linear because
the tank is oddly shaped). Float centre = surface + 3; arm angle from the float height, clamped to the stops.
Raw sender position n = 1 at the top stop, 0 at the bottom stop; the gauge reads (n - 0.03) / 0.85 clamped, so it
reads F before the float even leaves the top and E slightly before the float reaches the bottom.
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, flow, pipe, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_LYING = F("hook", "lying")
T_PURPOSE = F("hook", "purpose.")
T_HIDING = F("hook", "hiding?")
T_WHAT = L("what")["start"]
T_ENDS = F("what", "ends")
T_DIAL1 = F("what", "dial.")
T_GAUGE1 = F("what", "gauge")
T_SENDER = L("sender")["start"]
T_TANK = F("sender", "tank,")
T_FLOAT = F("sender", "float")
T_TOPF = F("sender", "fuel.")
T_ARM = F("sender", "arm,")
T_DRAGS = F("sender", "drags")
T_WIPER = F("sender", "wiper")
T_RES = F("sender", "resistors.")
T_HOW = L("how")["start"]
T_DOWN = F("how", "down,")
T_SINKS = F("how", "sinks,")
T_RESIST = F("how", "resistance")
T_TURNS = F("how", "turns")
T_NEEDLE = F("how", "needle")
T_SLOSH = L("slosh")["start"]
T_SLOSHES = F("slosh", "sloshes")
T_BRAKE = F("slosh", "brake")
T_TURN = F("slosh", "turn.")
T_AVG = F("slosh", "averages")
T_SLOWLY = F("slosh", "slowly")
T_RE = L("rehook")["start"]
T_SIT = F("rehook", "full")
T_RACE = F("rehook", "race")
T_KEY = L("key")["start"]
T_PINNED = F("key", "pinned")
T_FIRST = F("key", "first")
T_REST = F("key", "rest")
T_TUNING = F("key", "tuning.")
T_DRIVERS = F("key", "drivers")
T_LIKE = F("key", "like")
T_READS = F("key", "reads")
T_STAYS = F("key", "stays")
T_FORD = F("key", "ford")
T_TWENTY = F("key", "twenty")
T_EMPTY = L("empty")["start"]
T_NOTEMPTY = F("empty", "isn't")
T_SECRET = F("empty", "secret")
T_REAL = F("empty", "real")
T_MARKED = F("empty", "marked")
T_OUTRO = L("outro")["start"]
T_BROKEN = F("outro", "broken.")

# scene windows
S_STATION = (0.0, T_SENDER + 0.25)
S_TANK = (T_SENDER - 0.15, T_RE + 0.25)
S_CURVE1 = (T_RE - 0.15, T_KEY + 0.25)
S_PINNED = (T_KEY - 0.15, T_REST + 0.25)
S_CURVE2 = (T_REST - 0.15, T_EMPTY + 0.25)
S_EMPTY = (T_EMPTY - 0.15, T_OUTRO + 0.25)
S_DIAL = (T_OUTRO - 0.15, T_TOTAL + 1)


def scene_k(t, s, fin=0.3, fout=0.3):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== tank + sender model
TANK = np.array([(-300, -200), (120, -200), (160, -150), (300, -150), (300, -22), (278, 0), (-278, 0), (-300, -22)],
                float)
TZ0, TZ1 = -110.0, 110.0
PIV = np.array([60.0, -190.0])
ARM = 175.0
TH_TOP, TH_BOT = math.radians(9.0), math.radians(80.0)
FLOAT_R = 15.0
WIPER_R = 34.0


def clip_half(poly, a, b, c):
    """Sutherland-Hodgman: keep the part of poly where a*x + b*y + c >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            s = fp / (fp - fq)
            out.append(p + (q - p) * s)
    return np.array(out) if out else np.zeros((0, 2))


def area(poly):
    if len(poly) < 3:
        return 0.0
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


A_TOT = area(TANK)


def fuel_poly(level, tilt=0.0, xc=0.0):
    """Fuel region below the surface y = level + tan(tilt) * (x - xc) (Y is down)."""
    s = math.tan(tilt)
    # keep y - level - s*(x - xc) >= 0
    return clip_half(TANK, -s, 1.0, -level + s * xc)


_LV = np.linspace(-200.0, 0.0, 401)
_VOL = np.array([area(fuel_poly(y)) / A_TOT for y in _LV])   # decreasing in y


def level_of(vol):
    return float(np.interp(vol, _VOL[::-1], _LV[::-1]))


def arm_angle(surf_y):
    fy = surf_y + 3.0
    sn = clamp((fy - PIV[1]) / ARM, -1, 1)
    return clamp(math.asin(sn), TH_TOP, TH_BOT)


def float_pos(th):
    return PIV + ARM * np.array([-math.cos(th), math.sin(th)])


def n_raw(th):
    return (TH_BOT - th) / (TH_BOT - TH_TOP)


def reading_of_n(n):
    return clamp((n - 0.03) / 0.85)


def reading_of_vol(vol):
    return reading_of_n(n_raw(arm_angle(level_of(vol))))


V_PIN = float(np.interp(1.0 - 1e-6, [0, 1], [0, 1]))
# volume where the float leaves its top stop, and where the gauge leaves F / reaches E
_vs = np.linspace(1, 0, 2001)
_ns = np.array([n_raw(arm_angle(level_of(v))) for v in _vs])
V_PIN = float(_vs[np.argmax(_ns < 0.999)])
_rs = np.array([reading_of_n(n) for n in _ns])
V_F = float(_vs[np.argmax(_rs < 0.999)])
V_E = float(_vs[np.argmax(_rs <= 0.001)])
V_STOP = float(_vs[np.argmax(_ns <= 0.001)])


def check_model():
    bad = []
    if not (1.0 > V_PIN > V_F > V_E > 0.0):
        bad.append(f"order of pin/F/E wrong {V_PIN, V_F, V_E}")
    if np.any(np.diff(_rs) > 1e-9):
        bad.append("gauge reading rises while fuel drops")
    if V_STOP <= 0.02:
        bad.append("no fuel left when the float hits the bottom stop")
    fp = float_pos(TH_TOP)
    if fp[1] - FLOAT_R < -200 + 2:
        bad.append("float hits the roof")
    fb = float_pos(TH_BOT)
    if fb[1] + FLOAT_R > -2:
        bad.append("float hits the floor")
    return bad


assert not check_model(), check_model()


# ================================================================== fuel volume timeline
VOL_KEYS = [(0.0, 0.12), (0.55, 0.12), (T_PURPOSE + 0.2, 0.97), (T_HIDING + 0.2, 1.0), (T_SENDER - 0.3, 0.985),
            (T_SENDER - 0.15, 0.70), (T_DOWN - 0.1, 0.70), (T_SLOSH - 0.3, 0.42), (T_RE, 0.42),
            (T_KEY - 0.15, 1.0), (T_FIRST, 1.0), (T_REST, V_PIN + 0.01),
            (T_EMPTY - 0.15, 0.13), (T_REAL, V_STOP + 0.004), (T_OUTRO, V_STOP + 0.004)]


def vol_at(t):
    ts = [k[0] for k in VOL_KEYS]
    vs = [k[1] for k in VOL_KEYS]
    i = int(np.searchsorted(ts, t))
    if i <= 0:
        return vs[0]
    if i >= len(ts):
        return vs[-1]
    t0, t1, v0, v1 = ts[i - 1], ts[i], vs[i - 1], vs[i]
    if t1 - t0 < 0.2 + 1e-9 and abs(v1 - v0) > 0.05:      # hard cut between scenes
        return v1
    return v0 + (v1 - v0) * ease(lin(t, t0, t1))


# slosh: surface tilt (rad) after BRAKE and TURN
def tilt_at(t):
    a = 0.0
    for te, amp in ((T_BRAKE, 0.20), (T_TURN, -0.24), (T_SLOSHES, 0.08)):
        d = t - te
        if d > 0:
            a += amp * math.exp(-d / 1.3) * math.sin(2 * math.pi * d / 1.05) * min(1, d / 0.12)
    return a


def float_on_surface(level, tilt, xc=0.0):
    th = arm_angle(level)
    for _ in range(4):
        fx = float_pos(th)[0]
        th = arm_angle(level + math.tan(tilt) * (fx - xc))
    return th


# precompute raw vs averaged signal through the slosh beat
SL_T0, SL_T1 = T_SLOSH - 0.2, T_RE + 0.2
_ST = np.arange(SL_T0, SL_T1, 1 / 60)
_RAW = []
for _t in _ST:
    _RAW.append(reading_of_n(n_raw(float_on_surface(level_of(vol_at(_t)), tilt_at(_t)))))
_RAW = np.array(_RAW)
_AVG = np.zeros_like(_RAW)
_AVG[0] = _RAW[0]
for _i in range(1, len(_RAW)):
    _AVG[_i] = _AVG[_i - 1] + (_RAW[_i] - _AVG[_i - 1]) * (1 / 60) / 2.5


def sig_at(t):
    return float(np.interp(t, _ST, _RAW)), float(np.interp(t, _ST, _AVG))


def needle_at(t):
    """What the dash needle shows at time t."""
    if SL_T0 <= t <= SL_T1:
        return sig_at(t)[1]
    return reading_of_vol(vol_at(t))


# ================================================================== fuel gauge dial
A_E, A_F = 150.0, 30.0


def dial_ang(r):
    return math.radians(A_E - (A_E - A_F) * r)


def fuel_dial(cv, cx, cy, R, reading, a=1.0, ends_k=0.0, hidden_k=0.0, real_empty_k=0.0, lamp=0.0):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    s = R / 150.0
    box = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - R - 70 * s, cy - R - 55 * s, cx + R + 70 * s, cy + 70 * s),
                                40 * s, 40 * s)
    face = skia.Paint(AntiAlias=True)
    face.setShader(lin_grad((cx, cy - R), (cx, cy + 70 * s), [hx("#141c2b"), hx("#070a11")]))
    cv.drawRRect(box, paint(hx("#000000"), a=0.6, blur=24 * s))
    cv.drawRRect(box, face)
    cv.drawRRect(box, paint(hx("#3a4456"), stroke=4 * s))

    def P(ang, r):
        return cx + r * math.cos(ang), cy - r * math.sin(ang)

    # red zone near E
    rect = skia.Rect.MakeLTRB(cx - R + 14 * s, cy - R + 14 * s, cx + R - 14 * s, cy + R - 14 * s)
    cv.drawArc(rect, -A_E, (A_E - A_F) * 0.12, False, paint(RED, stroke=12 * s, cap=skia.Paint.kButt_Cap))
    # hidden zones past each end
    if hidden_k > 0:
        for a0, sweep in ((-A_F, 16.0), (-A_E, -16.0)):
            cv.drawArc(rect, a0, sweep, False, paint(AMBER, a=0.45 * hidden_k, stroke=30 * s, blur=10 * s))
            cv.drawArc(rect, a0, sweep, False, paint(AMBER, a=hidden_k, stroke=12 * s, cap=skia.Paint.kButt_Cap))
    for i in range(9):
        r = i / 8
        ang = dial_ang(r)
        major = i % 2 == 0
        r1 = R - (40 if major else 24) * s
        c = INK
        cv.drawLine(*P(ang, r1), *P(ang, R - 6 * s), paint(c, a=0.95 if major else 0.5, stroke=(6 if major else 3) * s,
                                                         cap=skia.Paint.kButt_Cap))
    for x, y, txt, c, fs in ((cx - R * 0.74, cy + 34 * s, "E", RED, 54), (cx + R * 0.74, cy + 34 * s, "F", INK, 54)):
        draw_text(cv, txt, x, y, font("inter_blk", fs * s), c, align="center")
    # end flashes
    if ends_k > 0:
        for r in (0.0, 1.0):
            x, y = P(dial_ang(r), R - 20 * s)
            cv.drawCircle(x, y, 44 * s, paint(YEL, a=0.5 * ends_k, blur=16 * s))
            cv.drawCircle(x, y, 40 * s, paint(YEL, a=ends_k, stroke=4 * s))
    # real empty tick past E
    if real_empty_k > 0:
        ang = math.radians(A_E + 14)
        cv.drawLine(*P(ang, R - 46 * s), *P(ang, R + 4 * s), paint(AMBER, a=real_empty_k, stroke=6 * s))
        cv.drawLine(*P(ang, R - 46 * s), *P(ang, R + 4 * s), paint(AMBER, a=0.5 * real_empty_k, stroke=16 * s,
                                                                  blur=6 * s))
    # pump icon
    ix, iy = cx, cy - R * 0.30
    cv.drawRoundRect(skia.Rect.MakeXYWH(ix - 16 * s, iy - 22 * s, 28 * s, 42 * s), 4 * s, 4 * s, paint(MUTED))
    cv.drawRect(skia.Rect.MakeXYWH(ix - 11 * s, iy - 16 * s, 18 * s, 12 * s), paint(hx("#070a11")))
    cv.drawLine(ix + 12 * s, iy - 12 * s, ix + 24 * s, iy - 4 * s, paint(MUTED, stroke=4 * s))
    cv.drawLine(ix + 24 * s, iy - 4 * s, ix + 24 * s, iy + 14 * s, paint(MUTED, stroke=4 * s))
    # low fuel lamp
    if lamp > 0:
        lx, ly = cx - R * 0.42, cy + 26 * s
        cv.drawCircle(lx, ly, 18 * s, paint(AMBER, a=0.6 * lamp, blur=10 * s))
        cv.drawCircle(lx, ly, 12 * s, paint(AMBER, a=lamp))
    # needle
    ang = dial_ang(reading)
    tip = P(ang, R - 22 * s)
    base = P(ang + math.pi, 26 * s)
    cv.drawLine(*base, *tip, paint(hx("#ff5a2a"), a=0.6, stroke=14 * s, blur=10 * s))
    cv.drawLine(*base, *tip, paint(hx("#ff6a3a"), stroke=8 * s, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(cx, cy, 26 * s, paint(hx("#1c2330")))
    cv.drawCircle(cx, cy, 26 * s, paint(hx("#5a6577"), stroke=3 * s))
    cv.restore()


# ================================================================== STATION scene
GROUND = 1020.0
C_BODY = hx("#2f6fb0")
C_TIRE = hx("#15171b")
C_CHROME = hx("#d9e2ee")
CAR = np.array([(-218, -32), (-222, -88), (-176, -106), (-112, -150), (22, -152), (88, -106), (196, -94),
                (220, -66), (216, -32)], float)
GLASS = np.array([(-162, -110), (-106, -142), (16, -142), (72, -108)], float)
CAR_TANK = np.array([(-150, -62), (-40, -62), (-34, -40), (-150, -40)], float)
FILLER = (-196.0, -96.0)
WHEELS = (-140.0, 140.0)
SPEED = 640.0


def draw_car(cv, pj, t, roll, xray=0.0, fuel_k=0.0):
    zf, zb = -80.0, 80.0
    ba = 1 - 0.8 * xray
    # far wheels
    for x in WHEELS:
        cyl3(cv, pj, (x, -32, zb - 30), (x, -32, zb), 32, C_TIRE, n=36, edge=hx("#000000"))
    extrude(cv, pj, CAR, zf, zb, C_BODY, alpha=ba)
    if xray > 0:
        extrude(cv, pj, CAR, zf, zb, CYAN, alpha=0.18 * xray)
        Fq = pj.pts(CAR, zf)
        cv.drawPath(poly_path(Fq), paint(CYAN, a=0.9 * xray, stroke=2.5))
        # tank under the rear seat
        extrude(cv, pj, CAR_TANK, -60, 60, hx("#3a4352"), alpha=0.9 * xray)
        lvl = CAR_TANK.copy()
        lvl[0:2, 1] = -40 - 22 * clamp(fuel_k)
        extrude(cv, pj, lvl, -58, 58, AMBER, alpha=0.85 * xray)
        c = pj.pts(np.array([[-95, -51]]), 0)[0]
        cv.drawCircle(c[0], c[1], 70 * pj.s, paint(AMBER, a=0.25 * xray, blur=24))
        # fuel line to the engine
        line = pj(np.array([-40, 60, 150]), np.array([-40, -38, -60]), np.zeros(3))
        cv.drawPath(poly_path(line, close=False), paint(AMBER, a=0.7 * xray, stroke=3))
    # windows
    g = pj.pts(GLASS, zf - 1)
    gp = skia.Paint(AntiAlias=True)
    gp.setShader(lin_grad(tuple(g[1]), tuple(g[3]), [hx("#7fa6d6"), hx("#0f1a2b")]))
    gp.setAlphaf(0.9 * ba)
    cv.drawPath(poly_path(g), gp)
    b = pj.pts(np.array([[-46, -150], [-46, -108]]), zf - 1)
    cv.drawLine(*b[0], *b[1], paint(hx("#0b111c"), a=ba, stroke=6 * pj.s))
    # lights
    hl = pj(214, -78, zf - 2)
    look.bloom(cv, hl[0], hl[1], 7 * pj.s / 0.6, hx("#fff4d6"), a=0.9)
    tl_ = pj(-219, -80, zf - 2)
    look.bloom(cv, tl_[0], tl_[1], 5 * pj.s / 0.6, RED, a=0.8)
    # near wheels
    for x in WHEELS:
        cyl3(cv, pj, (x, -32, zf - 2), (x, -32, zf + 26), 32, C_TIRE, n=36, edge=hx("#000000"))
        hub = pj(x, -32, zf - 3)
        cv.drawCircle(*hub, 17 * pj.s, paint(hx("#9aa4b2")))
        for i in range(5):
            a = roll + i * 2 * math.pi / 5
            cv.drawLine(hub[0], hub[1], hub[0] + 15 * pj.s * math.cos(a), hub[1] + 15 * pj.s * math.sin(a),
                        paint(hx("#4b5566"), stroke=3 * pj.s))
    return hl


def drive_x(t):
    """Distance the car has driven (px) since it pulled away."""
    t0 = T_WHAT - 0.1
    if t < t0:
        return 0.0
    d = t - t0
    return SPEED * (d - 0.6 * (1 - math.exp(-d / 0.6)))


def draw_station(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, GROUND - 60, t=t, glow_a=0.25)
    look.haze(cv, GROUND - 260, GROUND, a=0.08)
    # ground
    gp = skia.Paint()
    gp.setShader(lin_grad((0, GROUND), (0, H), [hx("#20252f"), hx("#090b0f")]))
    cv.drawRect(skia.Rect.MakeLTRB(0, GROUND, W, H), gp)
    dx = drive_x(t)
    push = ease(lin(t, T_GAUGE1 - 0.2, T_SENDER + 0.2))
    # canopy + pump slide away as the car drives off
    sx = -dx
    if sx > -1400:
        cy0 = 560.0
        cv.drawRect(skia.Rect.MakeLTRB(-200 + sx, cy0, 980 + sx, cy0 + 46), paint(hx("#d7dde6")))
        cv.drawRect(skia.Rect.MakeLTRB(-200 + sx, cy0 + 46, 980 + sx, cy0 + 58), paint(RED))
        for x in (40, 360, 680):
            look.bloom(cv, x + sx, cy0 + 70, 10, hx("#f3f7ff"), a=0.9)
            look.beam(cv, (x + sx, cy0 + 70), (x + sx, GROUND), 20, 170, c=hx("#e8f0ff"), a=0.10)
        for x in (60, 900):
            cv.drawRect(skia.Rect.MakeLTRB(x - 14 + sx, cy0 + 58, x + 14 + sx, GROUND), paint(hx("#5b6575")))
        # pump
        px0 = 70 + sx
        cv.drawRoundRect(skia.Rect.MakeLTRB(px0, 760, px0 + 120, GROUND), 10, 10, paint(hx("#c9d0da")))
        cv.drawRect(skia.Rect.MakeLTRB(px0 + 16, 790, px0 + 104, 850), paint(hx("#0b111c")))
        filling = win(t, 0.5, T_PURPOSE + 0.3, 0.1, 0.1)
        draw_text(cv, f"{min(1.0, max(0.0, (t - 0.5) / (T_PURPOSE - 0.3))) * 11.6:4.1f}", px0 + 60, 836,
                  font("inter_b", 30), mix(MUTED, GREEN, filling), align="center")
        cv.drawRect(skia.Rect.MakeLTRB(px0 - 10, GROUND - 14, px0 + 130, GROUND), paint(hx("#8d97ab")))
    # car (camera pushes in on the tank during "how a fuel gauge works")
    s = 1.55 * (1 + 1.9 * push)
    cx = (1 - push) * 540 + push * (540 + 95 * s)
    cy = (1 - push) * (GROUND - 2) + push * (830 + 51 * s)
    pj = Proj(cx, cy, s, yaw=86, pitch=6)
    look.soft_shadow(cv, cx, cy + 4, 470 * s, 40 * s, a=0.6)
    xray = eout(lin(t, T_GAUGE1 - 0.3, T_GAUGE1 + 0.4))
    hl = draw_car(cv, pj, t, roll=dx / (32 * s), xray=xray, fuel_k=vol_at(t))
    look.beam(cv, hl, (hl[0] + 600, hl[1] + 40), 8, 120, a=0.25 * (1 - push))
    # hose + nozzle while filling
    hk = 1 - ease(lin(t, T_PURPOSE + 0.1, T_PURPOSE + 0.5))
    if hk > 0 and sx > -400:
        fpt = pj(*FILLER, -82)
        hose = spline(np.array([[150 + sx, 800], [120 + sx, 960], [fpt[0] - 70, fpt[1] + 120], [fpt[0], fpt[1]]]), 50)
        pipe(cv, hose, 14, hx("#2a2f38"), a=hk)
        if t < T_PURPOSE:
            flow(cv, hose, t, 420, 22, AMBER, r=5, a=hk * win(t, 0.5, T_PURPOSE, 0.2, 0.1))
        cv.drawRoundRect(skia.Rect.MakeXYWH(fpt[0] - 46, fpt[1] - 16, 50, 30), 8, 8, paint(hx("#3a4250"), a=hk))
    # click!
    brand.stamp(cv, t, "CLICK", T_PURPOSE - 0.1, dur=0.9, center=(560, 690), color=GREEN, bg=hx("#06281a"))
    look.vignette(cv, 0.5)
    cv.restore()


def draw_station_overlays(cv, t, k):
    if k <= 0:
        return
    push = ease(lin(t, T_GAUGE1 - 0.2, T_SENDER + 0.1))
    a = k * (1 - push)
    ends = win(t, T_ENDS - 0.1, T_GAUGE1, 0.15, 0.3)
    fuel_dial(cv, 540, 1330, 160, needle_at(t), a=a, ends_k=ends)
    # miles since the fill-up
    mk = win(t, T_WHAT - 0.1, T_GAUGE1 + 0.3, 0.3, 0.3) * k
    if mk > 0:
        mi = max(0.0, drive_x(t) / 260.0)
        pill(cv, 540, 1068, f"MILES SINCE FILL-UP  {mi:4.1f}   ·   STILL ON F", font("inter_xb", 28), INK,
             border=AMBER, a=mk, align="center", tracking=2, dot=AMBER)
    # hook chip (under the title, over the scene)
    hk = win(t, T_LYING - 0.1, T_HOOK_OUT + 0.2, 0.2, 0.3)
    if hk > 0:
        pill(cv, 540, 1068, "FILLED TO THE CLICK", font("inter_xb", 28), INK, border=GREEN, a=hk, align="center",
             tracking=2, dot=GREEN)


# ================================================================== TANK scene
def tank_proj(t, ox=470.0, oy=900.0, s=1.3):
    yaw = 66 + 4 * math.sin(t * 0.3)
    return Proj(ox, oy, s, yaw=yaw, pitch=20)


def draw_tank(cv, pj, t, vol, tilt=0.0, k=1.0, show_card=True, glow_bottom=0.0, glow_top=0.0, out_flow=0.0,
              stop_k=0.0, sig_k=1.0):
    """Tank cutaway. Returns screen anchors for labels."""
    if k <= 0:
        return {}
    cv.saveLayerAlpha(None, int(255 * clamp(k)))
    level = level_of(vol)
    th = float_on_surface(level, tilt)
    fp = float_pos(th)
    # tank shell (glass)
    extrude(cv, pj, TANK, TZ0, TZ1, hx("#55606f"), alpha=0.32, rim=hx("#9fb6d8"), rim_w=1.6)
    # fuel
    fpoly = fuel_poly(level, tilt)
    if len(fpoly) >= 3:
        extrude(cv, pj, fpoly, TZ0 + 3, TZ1 - 3, AMBER, alpha=0.55, outline=False, face_hi=1.05, face_lo=0.7)
        # surface sheen
        xs = np.linspace(TANK[:, 0].min() + 4, TANK[:, 0].max() - 4, 40)
        ys = level + math.tan(tilt) * xs + 1.6 * np.sin(xs / 25 + t * 5)
        sp = pj(xs, ys, np.full_like(xs, TZ0 + 3))
        inside = [_inside(x, y) for x, y in zip(xs, ys)]
        sp = sp[np.array(inside)] if any(inside) else sp[:0]
        if len(sp) > 1:
            cv.drawPath(poly_path(sp, close=False), paint(hx("#ffd27a"), a=0.9, stroke=3))
    if glow_bottom > 0 and len(fpoly) >= 3:
        q = pj.pts(fpoly, 0)
        cv.drawPath(poly_path(q), paint(AMBER, a=0.5 * glow_bottom, blur=18))
        cv.drawPath(poly_path(pj.pts(fpoly, TZ0 + 3)), paint(YEL, a=glow_bottom, stroke=4))
    if glow_top > 0 and len(fpoly) >= 3:
        pin_poly = clip_half(fpoly, 0, -1, level_of(V_PIN))
        if len(pin_poly) >= 3:
            cv.drawPath(poly_path(pj.pts(pin_poly, TZ0 + 3)), paint(YEL, a=0.35 * glow_top))
            cv.drawPath(poly_path(pj.pts(pin_poly, TZ0 + 3)), paint(YEL, a=glow_top, stroke=3))
    # pump pickup + fuel line out to the engine
    pick = pj(np.array([-200, -200, -200]), np.array([-12, -120, -200]), np.array([30, 30, 30]))
    outl = pj(np.array([-200, -200, -340]), np.array([-200, -222, -222]), np.array([30, 30, 30]))
    pipe(cv, np.vstack([pick, outl[1:]]), 10, hx("#7a8496"), glass=True)
    if out_flow > 0:
        flow(cv, spline(np.vstack([pick, outl[1:]]), 60), t, 220, 18, AMBER, r=4, a=out_flow)
    # sender: flange, bracket, card, arm, float
    fl = pj(PIV[0], -200, 0)
    cyl3(cv, pj, (PIV[0], -206, 0), (PIV[0], -198, 0), 40, hx("#9aa4b2"), n=40)
    br = pj(np.array([PIV[0] - 6, PIV[0] + 6, PIV[0] + 6, PIV[0] - 6]), np.array([-200, -200, PIV[1], PIV[1]]),
            np.zeros(4))
    cv.drawPath(poly_path(br), paint(hx("#8c96a8")))
    # resistor card (arc of pads around the pivot)
    if show_card:
        angs = np.linspace(TH_TOP, TH_BOT, 30)
        arc = np.array([PIV + WIPER_R * np.array([-math.cos(a), math.sin(a)]) for a in angs])
        ap = pj(arc[:, 0], arc[:, 1], np.full(len(arc), -6))
        cv.drawPath(poly_path(ap, close=False), paint(hx("#1b2230"), stroke=10 * pj.s, cap=skia.Paint.kRound_Cap))
        cv.drawPath(poly_path(ap, close=False), paint(AMBER, a=0.8, stroke=3 * pj.s))
    # arm
    a0 = pj(PIV[0], PIV[1], -8)
    a1 = pj(fp[0], fp[1], -8)
    cv.drawLine(*a0, *a1, paint(hx("#c8d2e2"), stroke=4.5 * pj.s, cap=skia.Paint.kRound_Cap))
    wp = PIV + WIPER_R * np.array([-math.cos(th), math.sin(th)])
    w = pj(wp[0], wp[1], -8)
    cv.drawCircle(*w, 6 * pj.s, paint(YEL))
    cv.drawCircle(*w, 12 * pj.s, paint(YEL, a=0.5, blur=6))
    cv.drawCircle(*a0, 7 * pj.s, paint(hx("#e6ebf3")))
    # stops
    if stop_k > 0:
        for thx, c in ((TH_TOP, RED), (TH_BOT, RED)):
            sp_ = PIV + (WIPER_R + 12) * np.array([-math.cos(thx), math.sin(thx)])
            q = pj(sp_[0], sp_[1], -8)
            cv.drawCircle(*q, 7 * pj.s, paint(c, a=stop_k))
    # float
    cyl3(cv, pj, (fp[0], fp[1], -40), (fp[0], fp[1], 26), FLOAT_R, hx("#e9e3cf"), n=36)
    # signal wire to the gauge
    wire = None
    if sig_k > 0:
        wire = pj(np.array([PIV[0] + 20, PIV[0] + 20, 340]), np.array([-206, -226, -226]), np.zeros(3))
        pipe(cv, wire, 6, AMBER, a=sig_k, glass=True)
    cv.restore()
    return {"float": tuple(pj(fp[0] - 10, fp[1] - 12, -40)), "arm": tuple(pj(*((PIV + fp) / 2), -8)),
            "wiper": tuple(w), "flange": tuple(fl), "fuel": tuple(pj(-150, (level - 10) / 2 - 5, TZ0)),
            "pivot": tuple(a0), "wire": wire, "th": th, "level": level, "pick": tuple(pick[0])}


def _inside(x, y):
    """Point-in-polygon for the tank profile."""
    c = False
    n = len(TANK)
    for i in range(n):
        x1, y1 = TANK[i]
        x2, y2 = TANK[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


BUB = (770.0, 470.0, 128.0)


def draw_bubble(cv, t, th, anchor, k):
    """Magnified resistor card: wiper position along the pads; amber = resistor length in the circuit."""
    if k <= 0:
        return
    bx, by, br = BUB
    cv.saveLayerAlpha(None, int(255 * clamp(k)))
    cv.drawLine(anchor[0], anchor[1], bx - br * 0.7, by + br * 0.7, paint(YEL, a=0.6, stroke=2))
    cv.drawCircle(bx, by, br + 6, paint(hx("#000000"), a=0.5, blur=14))
    cv.drawCircle(bx, by, br, paint(hx("#0b111c")))
    cv.save()
    cv.clipPath(skia.Path.Circle(bx, by, br - 2), doAntiAlias=True)
    pvx, pvy = bx + 70, by - 80
    Rr = 165
    angs = np.linspace(TH_TOP, TH_BOT, 22)
    for i, a in enumerate(angs):
        on = a >= th
        x0, y0 = pvx - (Rr - 18) * math.cos(a), pvy + (Rr - 18) * math.sin(a)
        x1, y1 = pvx - (Rr + 18) * math.cos(a), pvy + (Rr + 18) * math.sin(a)
        cv.drawLine(x0, y0, x1, y1, paint(AMBER if on else hx("#4b5566"), stroke=6, cap=skia.Paint.kButt_Cap))
    # wiper
    wx, wy = pvx - (Rr + 4) * math.cos(th), pvy + (Rr + 4) * math.sin(th)
    cv.drawLine(pvx, pvy, wx, wy, paint(hx("#c8d2e2"), stroke=8, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(wx, wy, 14, paint(YEL, a=0.6, blur=8))
    cv.drawCircle(wx, wy, 8, paint(YEL))
    cv.restore()
    cv.drawCircle(bx, by, br, paint(YEL, stroke=3))
    draw_text(cv, "RESISTOR CARD", bx, by + br + 34, font("inter_xb", 22), MUTED, align="center", tracking=3)
    # resistance bar
    n = n_raw(th)
    x0, x1, y = bx - br, bx + br, by + br + 62
    cv.drawLine(x0, y, x1, y, paint(hx("#263043"), stroke=12, cap=skia.Paint.kRound_Cap))
    cv.drawLine(x0, y, x0 + (x1 - x0) * (0.1 + 0.9 * (1 - n)), y, paint(AMBER, stroke=12, cap=skia.Paint.kRound_Cap))
    draw_text(cv, "RESISTANCE", x0, y + 36, font("inter_xb", 20), MUTED, tracking=3)
    cv.restore()


def draw_tank_scene(cv, t, k):
    if k <= 0:
        return
    pj = tank_proj(t)
    vol = vol_at(t)
    tilt = tilt_at(t) if t > T_SLOSH - 0.3 else 0.0
    out = win(t, T_DOWN - 0.3, T_SLOSH, 0.3, 0.3)
    anc = draw_tank(cv, pj, t, vol, tilt=tilt, k=k, out_flow=out)
    cv.saveLayerAlpha(None, int(255 * k))
    th = anc["th"]
    # labels
    brand.label(cv, t, "TANK", (pj(-300, -120, TZ0)[0] + 4, pj(-300, -120, TZ0)[1]), (90, 560), MUTED,
                T_TANK - 0.1, T_FLOAT + 0.2)
    brand.label(cv, t, "FLOAT", anc["float"], (90, 640), YEL, T_FLOAT - 0.1, T_SLOSH)
    brand.label(cv, t, "ARM", anc["arm"], (90, 560), YEL, T_ARM - 0.1, T_HOW)
    brand.label(cv, t, "WIPER", anc["wiper"], (330, 470), YEL, T_WIPER - 0.1, T_HOW)
    bk = win(t, T_WIPER - 0.2, T_SLOSH + 0.2, 0.3, 0.3)
    draw_bubble(cv, t, th, anc["wiper"], bk)
    brand.label(cv, t, "TO THE ENGINE", anc["pick"], (90, 560), AMBER, T_DOWN - 0.1, T_SLOSH)
    # signal along the wire
    if anc["wire"] is not None and t > T_RES:
        flow(cv, spline(anc["wire"], 40), t, 300, 26, AMBER, r=4, a=win(t, T_RES, T_SLOSH, 0.2, 0.2))
    # how-chain chips
    ck = win(t, T_DOWN - 0.2, T_SLOSH, 0.25, 0.3)
    if ck > 0:
        brand.chips(cv, ck, 1060, [("FUEL", eout(lin(t, T_DOWN, T_DOWN + 0.3))),
                                   ("FLOAT", eout(lin(t, T_SINKS, T_SINKS + 0.3))),
                                   ("RESISTANCE", eout(lin(t, T_RESIST, T_RESIST + 0.3))),
                                   ("NEEDLE", eout(lin(t, T_NEEDLE, T_NEEDLE + 0.3)))], center=True)
    cv.restore()
    # gauge (then the slosh graph takes its place)
    dk = k * (1 - ease(lin(t, T_SLOSH - 0.2, T_SLOSH + 0.3)))
    fuel_dial(cv, 540, 1330, 160, needle_at(t), a=dk)
    draw_slosh(cv, t, k)


GX2, GY2, GW2, GH2 = 160.0, 1150.0, 760.0, 170.0


def draw_slosh(cv, t, k):
    kg = k * win(t, T_SLOSH - 0.1, T_RE + 0.3, 0.3, 0.3)
    if kg <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * kg))
    brand.graph_box(cv, (GX2, GY2, GW2, GH2), "SENDER SIGNAL", xlabel="TIME")
    t0, t1 = SL_T0 + 0.2, T_RE

    def pts(arr):
        m = (_ST >= t0) & (_ST <= min(t, t1))
        xs = GX2 + GW2 * (_ST[m] - t0) / (t1 - t0)
        lo, hi = 0.15, 0.75
        ys = GY2 + GH2 - GH2 * (arr[m] - lo) / (hi - lo)
        return np.stack([xs, np.clip(ys, GY2 - 10, GY2 + GH2)], 1)
    raw, avg = pts(_RAW), pts(_AVG)
    if len(raw) > 2:
        brand.curve(cv, raw, AMBER, width=3)
        brand.curve(cv, avg, CYAN, width=5)
        brand.dot(cv, *avg[-1], CYAN)
    draw_text(cv, "RAW", GX2 + GW2, GY2 - 12, font("inter_xb", 22), AMBER, align="right", tracking=3)
    ka = eout(lin(t, T_AVG - 0.1, T_AVG + 0.4))
    draw_text(cv, "AVERAGED → NEEDLE", GX2 + GW2 - 90, GY2 - 12, font("inter_xb", 22), CYAN, a=ka, align="right",
              tracking=3)
    cv.restore()
    brand.stamp(cv, t, "BRAKE", T_BRAKE, dur=1.0, center=(300, 470), color=AMBER, bg=hx("#2a1d05"))
    brand.stamp(cv, t, "TURN", T_TURN, dur=1.0, center=(300, 470), color=AMBER, bg=hx("#2a1d05"))
    brand.stamp(cv, t, "AVERAGED", T_AVG, dur=1.6, center=(540, 1060), color=CYAN, bg=hx("#05202a"))
    k2 = win(t, T_SLOWLY - 0.2, T_RE + 0.2, 0.25, 0.3)
    if k2 > 0:
        pill(cv, 540, 1060, "SLOW NEEDLE = ON PURPOSE", font("inter_xb", 28), INK, border=CYAN, a=k2 * kg,
             align="center", tracking=2, dot=CYAN)


# ================================================================== CURVE scene (needle vs fuel)
GX, GY, GW, GH = 190.0, 560.0, 720.0, 430.0
_CV = np.linspace(1, 0, 300)
_CR = np.array([reading_of_vol(v) for v in _CV])


def gx(v):
    return GX + GW * (1 - v)


def gy(r):
    return GY + GH - (GH - 40) * r


def draw_curve_scene(cv, t, k, phase):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    brand.graph_box(cv, (GX, GY, GW, GH), "FUEL GAUGE vs FUEL IN THE TANK")
    draw_text(cv, "F", GX - 40, gy(1) + 14, font("inter_blk", 40), INK, align="center")
    draw_text(cv, "E", GX - 40, gy(0) + 14, font("inter_blk", 40), RED, align="center")
    draw_text(cv, "TANK FULL", GX, GY + GH + 34, font("inter_sb", 20), MUTED, tracking=2)
    draw_text(cv, "TANK EMPTY", GX + GW, GY + GH + 34, font("inter_sb", 20), MUTED, align="right", tracking=2)
    lin_pts = np.array([[gx(1), gy(1)], [gx(0), gy(0)]])
    brand.curve(cv, np.array([lin_pts[0] + (lin_pts[1] - lin_pts[0]) * u for u in np.linspace(0, 1, 50)]), CYAN,
                dashed=True)
    draw_text(cv, "IF IT WERE LINEAR", gx(0.72) + 14, gy(0.72) + 44, font("inter_xb", 20), CYAN, a=0.8, tracking=2)
    pts = np.stack([gx(_CV), gy(_CR)], 1)
    if phase == 1:
        prog = ease(lin(t, T_SIT - 0.2, T_RACE + 0.9))
        brand.curve(cv, pts, RED, prog=prog)
        i = max(0, min(len(pts) - 1, int(prog * (len(pts) - 1))))
        brand.dot(cv, *pts[i], RED)
        r_needle = _CR[i]
        brand.stamp(cv, t, "WHY?", T_RACE + 0.6, dur=1.6, center=(560, 470), color=YEL, bg=hx("#2a2405"))
    else:
        brand.curve(cv, pts, RED)
        # regions: float pinned (yellow), tuned (red)
        kp = eout(lin(t, T_REST - 0.1, T_REST + 0.4))
        kt = eout(lin(t, T_READS - 0.2, T_READS + 0.4))
        for v0, v1, c, txt, kk, yy in ((1.0, V_PIN, YEL, "FLOAT PINNED", kp, gy(0.5)),
                                       (V_PIN, V_F, RED, "TUNED", kt, gy(0.35))):
            if kk > 0:
                r = skia.Rect.MakeLTRB(gx(v0), GY, gx(v1), GY + GH)
                cv.drawRect(r, paint(c, a=0.18 * kk))
                cv.drawLine(gx(v1), GY, gx(v1), GY + GH, paint(c, a=kk, stroke=2))
        if kp > 0:
            draw_text(cv, "FLOAT", gx(1) + 12, gy(0.62), font("inter_xb", 22), YEL, a=kp, tracking=2)
            draw_text(cv, "PINNED", gx(1) + 12, gy(0.62) + 28, font("inter_xb", 22), YEL, a=kp, tracking=2)
        if kt > 0:
            draw_text(cv, "TUNED", gx(V_PIN) + 12, gy(0.42), font("inter_xb", 22), RED, a=kt, tracking=2)
        # the "full reserve" span on F
        ks = eout(lin(t, T_STAYS - 0.1, T_STAYS + 0.4))
        if ks > 0:
            y = gy(1) + 24
            cv.drawLine(gx(1), y, gx(V_F), y, paint(RED, a=ks, stroke=6, cap=skia.Paint.kRound_Cap))
            cv.drawLine(gx(1), y, gx(V_F), y, paint(RED, a=0.5 * ks, stroke=14, blur=6))
        kd = win(t, T_DRIVERS - 0.2, T_EMPTY, 0.25, 0.3)
        if kd > 0:
            pill(cv, GX + 150, GY + GH - 70, "DRIVERS SAID THEY LIKE IT", font("inter_xb", 24), INK, border=GREEN,
                 a=kd * (1 - ease(lin(t, T_FORD - 0.3, T_FORD))), tracking=2, dot=GREEN)
        kf = win(t, T_TWENTY - 0.15, T_EMPTY, 0.25, 0.3)
        if kf > 0:
            pill(cv, GX + 150, GY + GH - 70, "FORD: ~20–30 MILES ON F", font("inter_xb", 28), INK, border=RED,
                 a=kf, tracking=2, dot=RED)
        # dot rides along the plateau while "stays there"
        u = ease(lin(t, T_READS, T_TWENTY + 0.6))
        v = 1 - (1 - V_F) * u
        brand.dot(cv, gx(v), gy(reading_of_vol(v)), RED)
        r_needle = reading_of_vol(v)
        brand.stamp(cv, t, "ON PURPOSE", T_TUNING - 0.05, dur=1.5, center=(560, 470))
    cv.restore()
    fuel_dial(cv, 540, 1330, 160, r_needle, a=k)


# ================================================================== PINNED scene (full tank)
def draw_pinned(cv, t, k):
    if k <= 0:
        return
    pj = tank_proj(t, oy=930.0, s=1.35)
    vol = vol_at(t)
    out = win(t, T_FIRST - 0.3, T_REST + 0.2, 0.3, 0.2)
    gt = win(t, T_PINNED - 0.2, T_REST + 0.2, 0.3, 0.2)
    anc = draw_tank(cv, pj, t, vol, k=k, out_flow=out, stop_k=gt, glow_top=gt, show_card=True)
    cv.saveLayerAlpha(None, int(255 * k))
    brand.label(cv, t, "FLOAT AT ITS TOP STOP", anc["float"], (90, 600), YEL, T_KEY + 0.3, T_REST + 0.2)
    kf = win(t, T_FIRST - 0.2, T_REST + 0.2, 0.25, 0.3)
    if kf > 0:
        pill(cv, 540, 1080, "FIRST GALLONS: NEEDLE DOESN'T MOVE", font("inter_xb", 27), INK, border=YEL, a=kf,
             align="center", tracking=2, dot=YEL)
    cv.restore()
    brand.stamp(cv, t, "PINNED", T_PINNED, dur=1.4, center=(560, 470), color=YEL, bg=hx("#2a2405"))
    fuel_dial(cv, 540, 1330, 160, needle_at(t), a=k)


# ================================================================== EMPTY scene
def draw_empty(cv, t, k):
    if k <= 0:
        return
    pj = tank_proj(t, oy=930.0, s=1.35)
    vol = vol_at(t)
    gb = win(t, T_REAL - 0.2, T_OUTRO + 0.3, 0.3, 0.2)
    anc = draw_tank(cv, pj, t, vol, k=k, glow_bottom=gb, stop_k=win(t, T_NOTEMPTY, T_OUTRO, 0.3, 0.2),
                    out_flow=win(t, T_EMPTY, T_REAL, 0.3, 0.3))
    cv.saveLayerAlpha(None, int(255 * k))
    brand.label(cv, t, "FLOAT ON ITS BOTTOM STOP", anc["float"], (90, 600), YEL, T_NOTEMPTY - 0.2, T_REAL)
    brand.label(cv, t, "STILL FUEL HERE", anc["fuel"], (90, 600), AMBER, T_REAL - 0.1, T_OUTRO + 0.2)
    ks = win(t, T_SECRET - 0.2, T_OUTRO + 0.2, 0.25, 0.3)
    if ks > 0:
        brand.bullet(cv, 330, 1100, "NO RESERVE TANK", False, a=ks)
    cv.restore()
    brand.stamp(cv, t, "E IS NOT EMPTY", T_NOTEMPTY - 0.05, dur=1.5, center=(560, 470))
    re = eout(lin(t, T_MARKED - 0.3, T_MARKED + 0.2))
    fuel_dial(cv, 540, 1330, 160, needle_at(t), a=k, real_empty_k=re, lamp=1.0)
    if re > 0:
        draw_text(cv, "REAL EMPTY", 250, 1300, font("inter_xb", 22), AMBER, a=re * k, align="center", tracking=2)
        draw_text(cv, "NOT MARKED", 250, 1328, font("inter_xb", 22), AMBER, a=re * k, align="center", tracking=2)


# ================================================================== DIAL (outro)
def draw_dial_scene(cv, t, k):
    if k <= 0:
        return
    hk = eout(lin(t, T_OUTRO + 0.2, T_OUTRO + 0.8))
    fuel_dial(cv, 540, 1000, 300, 0.5 + 0.02 * math.sin(t * 1.3), a=k, hidden_k=hk)
    if hk > 0:
        for x, txt in ((300, "HIDDEN BELOW E"), (780, "HIDDEN ABOVE F")):
            pill(cv, x, 1195, txt, font("inter_xb", 26), INK, border=AMBER, a=hk * k, align="center", tracking=2,
                 dot=AMBER)
    brand.stamp(cv, t, "NOT BROKEN", T_BROKEN - 0.4, dur=1.3, center=(540, 470), color=GREEN, bg=hx("#06281a"))


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(0, "FUEL GAUGE", AMBER), (T_SENDER, "THE SENDER", YEL), (T_HOW, "HOW IT READS", CYAN),
           (T_SLOSH, "THE SLOSH", AMBER), (T_RE, "THE QUESTION", YEL), (T_KEY, "THE ANSWER", RED),
           (T_EMPTY, "THE OTHER END", RED), (T_OUTRO, "BOTH ENDS", AMBER)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    if t > T_SENDER - 0.2 and not (T_WIPER - 0.2 < t < T_SLOSH + 0.3):
        brand.note(cv, "ILLUSTRATION · NOT TO SCALE", 0.9 * k, dy=-40)


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    ks = scene_k(t, S_STATION, 0.0, 0.3)
    draw_station(cv, t, ks)
    draw_tank_scene(cv, t, scene_k(t, S_TANK))
    draw_curve_scene(cv, t, scene_k(t, S_CURVE1), 1)
    draw_pinned(cv, t, scene_k(t, S_PINNED))
    draw_curve_scene(cv, t, scene_k(t, S_CURVE2), 2)
    draw_empty(cv, t, scene_k(t, S_EMPTY))
    draw_dial_scene(cv, t, scene_k(t, S_DIAL) * kE)
    draw_station_overlays(cv, t, ks)
    draw_header(cv, t)


# ================================================================== sound (synthesized here)
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _lp(x, fc):
    from scipy import signal
    b, a = signal.butter(2, fc / (SR / 2))
    return signal.lfilter(b, a, x)


def _bp(x, f0, f1):
    from scipy import signal
    b, a = signal.butter(2, [f0 / (SR / 2), f1 / (SR / 2)], btype="band")
    return signal.lfilter(b, a, x)


def _norm(x, pk=0.9):
    x = np.asarray(x, np.float64)
    x = x / (np.abs(x).max() + 1e-9) * pk
    n = int(0.02 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def _pour(dur):
    rng = np.random.default_rng(11)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = _bp(rng.standard_normal(n), 300, 2600)
    x += 0.5 * _bp(rng.standard_normal(n), 1800, 5000) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt))
    pitch = 0.7 + 0.3 * tt / dur                           # tank filling: the gurgle rises
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * 9 * pitch * tt)
    return _norm(x * np.minimum(1, tt / 0.2) * np.minimum(1, (dur - tt) / 0.1), 0.7)


def _slosh(dur):
    rng = np.random.default_rng(4)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = _lp(rng.standard_normal(n), 900) + 0.3 * _bp(rng.standard_normal(n), 1500, 4000)
    env = np.exp(-tt / (dur * 0.45)) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * tt / 1.05 * 2)))
    return _norm(x * env * np.minimum(1, tt / 0.05), 0.8)


def _drive(dur):
    rng = np.random.default_rng(9)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = 45 + 35 * np.minimum(1, tt / 2.0)
    ph = np.cumsum(f0) / SR
    x = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 8))
    x = x + 0.6 * _lp(rng.standard_normal(n), 600)
    env = np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.8)
    return _norm(_lp(np.tanh(1.4 * x), 2500) * env, 0.75)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    clips = {"fuel_pour": _pour(max(1.0, T_PURPOSE - 0.6)), "fuel_slosh": _slosh(2.2), "car_away": _drive(4.0)}
    for name, x in clips.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_TUNING
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(0.5, "fuel_pour", 0.5), (T_PURPOSE - 0.1, "clunk", 0.55), (T_HOOK_OUT - 0.1, "whoosh_big", 0.5),
           (T_WHAT, "car_away", 0.4), (T_ENDS, "tick", 0.35), (T_GAUGE1 - 0.2, "whoosh_up", 0.35),
           (T_SENDER - 0.05, "whoosh_down", 0.3), (T_FLOAT, "tick", 0.25), (T_WIPER, "tick", 0.3),
           (T_RES, "tick", 0.2), (T_DOWN, "whoosh_down", 0.25), (T_NEEDLE, "tick", 0.3),
           (T_BRAKE, "fuel_slosh", 0.55), (T_TURN, "fuel_slosh", 0.55), (T_AVG, "whoosh_up", 0.25),
           (T_RE, "whoosh_big", 0.35), (T_RACE + 0.6, "impact", 0.35), (T_PINNED, "clunk", 0.45),
           (T_REST, "whoosh_up", 0.25), (T_TUNING - 0.05, "impact", 0.5), (T_TWENTY, "tick", 0.3),
           (T_EMPTY, "whoosh_down", 0.3), (T_NOTEMPTY, "impact", 0.4), (T_REAL, "fuel_slosh", 0.35),
           (T_OUTRO, "whoosh_big", 0.3)]
    return {"build": (T_RE, T_TUNING), "drop": (T_TUNING, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
