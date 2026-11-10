"""ABS visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  ROAD    (hook, what, problem) side-on wet night road, generic sedan, rain. The driver pumps the brakes (pedal inset,
                          brake lights flash), then the x-ray shows the front brake. On "stomp" both wheels lock:
                          spokes freeze while the road keeps sliding past, skid streaks grow; CAR vs WHEEL speed bars.
  SENSOR  (parts)         tone ring spinning under a sensor; every tooth makes a pulse on the trace (slowed);
                          then a top view with four sensors wired to the computer, a speed bar per wheel.
  TOPV    (how, 1st half) one wheel's bar drops far faster than the car's: ABOUT TO LOCK.
  CIRCUIT (how, 2nd half) one brake channel: master cylinder -> inlet valve -> caliper; outlet valve -> accumulator ->
                          pump -> back into the line. Inlet closes (HOLD), outlet opens (RELEASE); caliper pressure and
                          wheel speed traced live.
  GRIP    (rehook, key)   "WHY LET GO?" then grip vs wheel slip: braking grip peaks while the tire still turns
                          (~10-20 % slip band) and is lower when sliding; sideways grip falls to almost nothing at lock;
                          top-view inset: front wheels turned, car goes straight.
  CYCLE   (pump)          the circuit again, pump pushing fluid back; HOLD / RELEASE / REAPPLY sawtooth trace, wheel
                          speed hovering just under car speed; pedal buzz.
  1978    (history)       year counter, first electronic four-wheel ABS, four sensors light up on the top view.
  DRIVE   (drive)         top view on a wet road: brake hard, ABS lamp on, steer around a stopped car; do/don't list.

Model: illustrative one-channel ABS. Pressure / wheel speed are keyframed to the narration in the CIRCUIT beat and
procedural (period 1.25 s, labelled ANIMATION SLOWED) in the CYCLE beat. Grip curves: a Pacejka-style braking curve
peaking near 15 % slip with ~70 % of peak when locked, and a sideways-grip curve that falls to ~5 % at lock
(research.md facts 2-3); they are labelled ILLUSTRATIVE.
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
T_SKID = F("hook", "skid,")
T_PUMPH = F("hook", "pump")
T_LETTING = F("hook", "letting")
T_STOPQ = F("hook", "stop?")
T_WHAT = L("what")["start"]
T_ANTI = F("what", "anti-lock")
T_PROB = L("problem")["start"]
T_STOMP = F("problem", "stomp")
T_WET = F("problem", "wet")
T_STOPT = F("problem", "stop")
T_KEEPS = F("problem", "keeps")
T_LOCKUP = F("problem", "lock")
T_PARTS = L("parts")["start"]
T_TOOTHED = F("parts", "toothed")
T_SENSOR = F("parts", "sensor")
T_TEETH = F("parts", "teeth.")
T_COMPUTER = F("parts", "computer")
T_FOUR = F("parts", "four.")
T_HOW = L("how")["start"]
T_SLOWS = F("how", "slows")
T_LOCKW = F("how", "lock.")
T_VALVE = F("how", "valve")
T_CLOSES = F("how", "closes")
T_HOLD = F("how", "hold")
T_ANOTHER = F("how", "another")
T_OPENS = F("how", "opens")
T_OUT = F("how", "out.")
T_RE = L("rehook")["start"]
T_KEY = L("key")["start"]
T_TURNING = F("key", "turning")
T_GRIPS = F("key", "grips")
T_SLIDING = F("key", "sliding.")
T_SIDEWAYS = F("key", "sideways")
T_STEERING = F("key", "steering")
T_NOTHING = F("key", "nothing.")
T_PUMP = L("pump")["start"]
T_PUMPW = F("pump", "pump")
T_BACK = F("pump", "back,")
T_DOZEN = F("pump", "dozen")
T_BUZZ = F("pump", "buzz")
T_PEDAL = F("pump", "pedal")
T_WORKING = F("pump", "working.")
T_HIST = L("history")["start"]
T_BOSCH = F("history", "bosch")
T_FIRST = F("history", "first")
T_NINETEEN = F("history", "nineteen")
T_DRIVE = L("drive")["start"]
T_DONT = F("drive", "don't")
T_PRESS = F("drive", "press")
T_HOLDIT = F("drive", "hold")
T_STEER = F("drive", "steer")
T_OUTRO = L("outro")["start"]

S_ROAD = (0.0, T_PARTS + 0.25)
S_SENSOR = (T_PARTS - 0.15, T_COMPUTER + 0.25)
S_TOPV = (T_COMPUTER - 0.15, T_VALVE + 0.2)
S_CIRCUIT = (T_VALVE - 0.1, T_RE + 0.25)
S_GRIP = (T_RE - 0.15, T_PUMP + 0.25)
S_CYCLE = (T_PUMP - 0.15, T_HIST + 0.25)
S_HIST = (T_HIST - 0.15, T_DRIVE + 0.25)
S_DRIVE = (T_DRIVE - 0.15, T_TOTAL + 1)


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


# ================================================================== ROAD: car / wheel kinematics (precomputed)
V0 = 760.0                       # px/s of road scroll at cruise
_DT = 1 / 120
_TS = np.arange(0.0, S_ROAD[1] + 0.5, _DT)


def _road_v(t):
    v = V0
    if t > T_STOMP:                      # sliding: slow, steady deceleration
        v = V0 * max(0.32, 1 - 0.11 * (t - T_STOMP))
    return v


def _wheel_w(t):
    """Wheel surface speed / car speed (1 = rolling, 0 = locked)."""
    lock = ease(lin(t, T_STOMP + 0.05, T_STOMP + 0.45))
    return 1 - lock


_VS = np.array([_road_v(t) for t in _TS])
_DIST = np.concatenate([[0], np.cumsum(_VS[:-1] * _DT)])
_ROLL = np.concatenate([[0], np.cumsum((_VS * np.array([_wheel_w(t) for t in _TS]))[:-1] * _DT)])
T_LOCKED = T_STOMP + 0.45


def dist_at(t):
    return float(np.interp(t, _TS, _DIST))


def roll_at(t):
    return float(np.interp(t, _TS, _ROLL))


GROUND = 1080.0
C_BODY = hx("#2f6fb0")
C_TIRE = hx("#15171b")
CAR = np.array([(-228, -32), (-232, -84), (-200, -100), (-120, -112), (-70, -158), (70, -160), (128, -112),
                (214, -100), (232, -72), (228, -32)], float)
GLASS = np.array([(-112, -116), (-64, -150), (64, -152), (114, -116)], float)
WHEELS = (-148.0, 148.0)
WR = 34.0


def draw_side_car(cv, pj, roll, brake=0.0, xray=0.0, locked=0.0):
    zf, zb = -80.0, 80.0
    for x in WHEELS:
        cyl3(cv, pj, (x, -WR, zb - 30), (x, -WR, zb), WR, C_TIRE, n=36, edge=hx("#000000"))
    ba = 1 - 0.75 * xray
    extrude(cv, pj, CAR, zf, zb, C_BODY, alpha=ba)
    if xray > 0:
        extrude(cv, pj, CAR, zf, zb, CYAN, alpha=0.16 * xray)
        cv.drawPath(poly_path(pj.pts(CAR, zf)), paint(CYAN, a=0.9 * xray, stroke=2.5))
    g = pj.pts(GLASS, zf - 1)
    gp = skia.Paint(AntiAlias=True)
    gp.setShader(lin_grad(tuple(g[1]), tuple(g[3]), [hx("#7fa6d6"), hx("#0f1a2b")]))
    gp.setAlphaf(0.9 * ba)
    cv.drawPath(poly_path(g), gp)
    b = pj.pts(np.array([[0, -158], [0, -114]]), zf - 1)
    cv.drawLine(*b[0], *b[1], paint(hx("#0b111c"), a=ba, stroke=6 * pj.s))
    hl = pj(228, -76, zf - 2)
    look.bloom(cv, hl[0], hl[1], 7 * pj.s / 0.6, hx("#fff4d6"), a=0.9)
    tl_ = pj(-230, -80, zf - 2)
    look.bloom(cv, tl_[0], tl_[1], (5 + 5 * brake) * pj.s / 0.6, RED, a=0.55 + 0.45 * brake)
    for x in WHEELS:
        cyl3(cv, pj, (x, -WR, zf - 2), (x, -WR, zf + 26), WR, C_TIRE, n=36, edge=hx("#000000"))
        hub = pj(x, -WR, zf - 3)
        if xray > 0:   # brake disc + caliper behind the spokes
            cv.drawCircle(*hub, 25 * pj.s, paint(hx("#9aa4b2"), a=0.9 * xray))
            cv.drawCircle(*hub, 25 * pj.s, paint(hx("#4b5566"), a=xray, stroke=2))
            cal = skia.Rect.MakeXYWH(hub[0] + 14 * pj.s, hub[1] - 16 * pj.s, 15 * pj.s, 32 * pj.s)
            cv.drawRoundRect(cal, 4 * pj.s, 4 * pj.s, paint(mix(hx("#6a7486"), RED, brake), a=xray))
            if brake > 0.05:
                cv.drawRoundRect(cal, 4 * pj.s, 4 * pj.s, paint(RED, a=0.5 * brake * xray, blur=8))
        cv.drawCircle(*hub, 17 * pj.s, paint(hx("#9aa4b2"), a=1 - 0.5 * xray))
        for i in range(5):
            a = roll / WR + i * 2 * math.pi / 5
            cv.drawLine(hub[0], hub[1], hub[0] + 15 * pj.s * math.cos(a), hub[1] + 15 * pj.s * math.sin(a),
                        paint(mix(hx("#4b5566"), RED, locked), stroke=3 * pj.s))
        # a white tick on the tyre shows rotation clearly
        a = roll / WR
        p1 = (hub[0] + 24 * pj.s * math.cos(a), hub[1] + 24 * pj.s * math.sin(a))
        p2 = (hub[0] + 32 * pj.s * math.cos(a), hub[1] + 32 * pj.s * math.sin(a))
        cv.drawLine(*p1, *p2, paint(mix(INK, RED, locked), stroke=4 * pj.s))
    return hl


def pedal_inset(cv, x, y, press, a=1.0, buzz=0.0, label=None, lc=AMBER):
    """Small brake-pedal inset: press 0..1."""
    if a <= 0:
        return
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, 200, 210), 22, 22)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.88 * a))
    cv.drawRRect(rr, paint(hx("#2a3446"), a=a, stroke=2))
    draw_text(cv, "BRAKE PEDAL", x + 100, y + 36, font("inter_xb", 20), MUTED, a=a, align="center", tracking=2)
    px, py = x + 150, y + 62
    ang = math.radians(98 - 26 * clamp(press))
    jx = 0.0
    ln = 120
    ex, ey = px + ln * math.cos(ang) + jx, py + ln * math.sin(ang)
    cv.drawLine(px, py, ex, ey, paint(STEEL, a=a, stroke=10, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(px, py, 9, paint(STEEL_D, a=a))
    cv.save()
    cv.translate(ex, ey)
    cv.rotate(math.degrees(ang) - 90)
    cv.drawRoundRect(skia.Rect.MakeXYWH(-34, -6, 68, 18), 6, 6, paint(hx("#2b313c"), a=a))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-34, -6, 68, 18), 6, 6, paint(mix(MUTED, RED, press), a=a, stroke=2.5))
    cv.restore()
    if label:
        pill(cv, x + 100, y + 186, label, font("inter_xb", 22), INK, border=lc, a=a, align="center", tracking=2)


def draw_road(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, GROUND - 80, t=t, glow_a=0.22)
    d = dist_at(t)
    # far city silhouettes (parallax)
    rng = np.random.default_rng(2)
    for i in range(24):
        bx = (i * 120 - d * 0.12) % 2880 - 200
        bh = 60 + 140 * rng.random()
        cv.drawRect(skia.Rect.MakeLTRB(bx, GROUND - 80 - bh, bx + 100, GROUND - 80), paint(hx("#0c1426")))
    look.haze(cv, GROUND - 300, GROUND - 40, a=0.10)
    # road
    gp = skia.Paint()
    gp.setShader(lin_grad((0, GROUND - 80), (0, H), [hx("#1a1f29"), hx("#07090d")]))
    cv.drawRect(skia.Rect.MakeLTRB(0, GROUND - 80, W, H), gp)
    # street lamps + wet reflections
    for i in range(-1, 4):
        lx = (i * 520 - d * 0.9) % 2080 - 260
        cv.drawRect(skia.Rect.MakeLTRB(lx - 5, GROUND - 420, lx + 5, GROUND - 70), paint(hx("#3b4556")))
        look.bloom(cv, lx + 30, GROUND - 420, 9, hx("#ffd59a"), a=0.85)
        look.beam(cv, (lx + 30, GROUND - 418), (lx + 30, GROUND - 60), 12, 120, c=hx("#ffd59a"), a=0.08)
        look.wet_reflection(cv, lx + 30, GROUND - 60, GROUND + 260, 22, hx("#ffd59a"), a=0.25)
    # lane dashes
    for i in range(-1, 9):
        x = (i * 200 - d) % 1800 - 200
        cv.drawRect(skia.Rect.MakeLTRB(x, GROUND + 120, x + 110, GROUND + 132), paint(hx("#cfd6e2"), a=0.55))
    # car
    s = 1.55
    cx, cy = 540, GROUND + 40
    xray = win(t, T_ANTI - 0.3, T_PROB + 0.2, 0.35, 0.4)
    # skid streaks: from where each tyre locked to where it is now
    if t > T_LOCKED:
        dl = dist_at(T_LOCKED)
        for x in WHEELS:
            x_now = cx + x * s * 0.99
            x0 = x_now - (d - dl)
            sp = skia.Paint(AntiAlias=True)
            cols = [skia.Color4f(0, 0, 0, 0), skia.Color4f(0.02, 0.02, 0.03, 0.85)]
            sp.setShader(skia.GradientShader.MakeLinear([skia.Point(max(x0, x_now - 900), 0), skia.Point(x_now, 0)],
                                                        cols))
            cv.drawRect(skia.Rect.MakeLTRB(max(-20, x0), cy - 4, x_now, cy + 10), sp)
    pj = Proj(cx, cy, s, yaw=86, pitch=6)
    look.soft_shadow(cv, cx, cy + 4, 470 * s, 40 * s, a=0.6)
    brake = brake_at(t)
    locked = ease(lin(t, T_STOMP + 0.1, T_LOCKED))
    hl = draw_side_car(cv, pj, roll_at(t), brake=brake, xray=xray, locked=locked)
    look.beam(cv, hl, (hl[0] + 520, hl[1] + 70), 8, 120, a=0.22)
    look.wet_reflection(cv, hl[0], hl[1] + 30, hl[1] + 300, 26, hx("#fff4d6"), a=0.25)
    tlp = pj(-230, -80, -82)
    look.wet_reflection(cv, tlp[0], tlp[1] + 30, tlp[1] + 280, 20, RED, a=0.2 + 0.25 * brake)
    # rain
    rng = np.random.default_rng(5)
    n = 90
    xs, ys, sp_ = rng.uniform(0, W + 300, n), rng.uniform(0, H, n), rng.uniform(1300, 1900, n)
    for x0, y0, v in zip(xs, ys, sp_):
        y = (y0 + v * t) % (H + 100) - 50
        x = (x0 - 0.35 * v * t - d * 0.6) % (W + 300) - 150
        cv.drawLine(x, y, x - 10, y + 32, paint(hx("#a9c4ee"), a=0.22, stroke=1.6))
    look.vignette(cv, 0.45)
    cv.restore()


def brake_at(t):
    """How hard the brake is pressed (0..1) in the road scene."""
    b = 0.0
    if T_PUMPH - 0.1 < t < T_LETTING + 0.2:   # pumping
        ph = (t - (T_PUMPH - 0.1)) / 0.5
        b = 0.5 + 0.5 * math.cos(2 * math.pi * ph) if ph > 0 else 0
        b = 1 - b
    if t >= T_LETTING + 0.2:
        b = 0.0
    if t >= T_STOMP - 0.1:
        b = ease(lin(t, T_STOMP - 0.1, T_STOMP + 0.1))
    return clamp(b)


def draw_road_overlays(cv, t, k):
    if k <= 0:
        return
    # pedal inset
    pk = k * win(t, T_PUMPH - 0.4, T_PARTS, 0.25, 0.3) * (1 - win(t, T_ANTI - 0.3, T_PROB, 0.2, 0.2))
    lab = None
    if T_PUMPH - 0.2 < t < T_LETTING + 0.3:
        lab, lc = "PUMP", AMBER
    elif T_LETTING + 0.3 <= t < T_STOMP:
        lab, lc = "LET GO", CYAN
    elif t >= T_STOMP - 0.1:
        lab, lc = "STOMP", RED
    pedal_inset(cv, 80, 1150, brake_at(t), a=pk, label=lab, lc=lc if lab else AMBER)
    # name pill in "what"
    nk = k * win(t, T_ANTI - 0.15, T_PROB + 0.1, 0.25, 0.3)
    if nk > 0:
        pill(cv, 540, 560, "ANTI-LOCK BRAKES  ·  ABS", font("inter_xb", 34), INK, border=CYAN, a=nk, align="center",
             tracking=3, dot=CYAN)
        label_xy = (720, 820)
        brand.label(cv, t, "BRAKE", (540 + WHEELS[1] * 1.55, GROUND + 40 - WR * 1.55 * 0.99), label_xy, RED,
                    T_ANTI + 0.2, T_PROB + 0.1)
    # car vs wheel speed bars (problem)
    bk = k * win(t, T_STOMP - 0.3, T_PARTS + 0.2, 0.3, 0.3)
    if bk > 0:
        v = _road_v(t) / V0
        w = v * _wheel_w(t)
        x0, x1 = 300, 900
        rows = (("CAR", v, CYAN, 520), ("WHEELS", w, RED if w < 0.05 else CYAN, 600))
        for name, val, c, y in rows:
            draw_text(cv, name, 280, y + 12, font("inter_xb", 30), INK, a=bk, align="right", tracking=2)
            cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y - 16, x1, y + 16), 16, 16, paint(hx("#1a2232"), a=bk))
            cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y - 16, x0 + max(32, (x1 - x0) * val), y + 16), 16, 16,
                             paint(c, a=bk))
            draw_text(cv, "MOVING" if val > 0.05 else "STOPPED", x1, y + 56, font("inter_sb", 22),
                      MUTED if val > 0.05 else RED, a=bk, align="right", tracking=2)
        brand.stamp(cv, t, "LOCKED UP", T_LOCKUP - 0.1, dur=1.6, center=(540, 760))


# ================================================================== SENSOR: tone ring
N_TEETH = 40
RING_R0, RING_R1 = 150.0, 176.0
OMEGA = 2 * math.pi * 7.0 / N_TEETH          # 7 teeth per second past the sensor (slowed)


def ring_prof(theta):
    pts = []
    for i in range(N_TEETH):
        a0 = theta + 2 * math.pi * i / N_TEETH
        da = 2 * math.pi / N_TEETH
        for f, r in ((0.0, RING_R0), (0.08, RING_R1), (0.45, RING_R1), (0.53, RING_R0)):
            a = a0 + f * da
            pts.append((r * math.cos(a), r * math.sin(a)))
    return np.array(pts)


def ring_angle(t):
    return OMEGA * (t - T_PARTS)


def tooth_under(theta):
    """1 if a tooth is under the sensor (at the top, angle -90 deg) for ring angle theta."""
    da = 2 * math.pi / N_TEETH
    rel = ((-math.pi / 2) - theta) % da / da
    return 1.0 if 0.06 < rel < 0.47 else 0.0


def draw_sensor(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cx, cy = 540, 820
    th = ring_angle(t)
    pj = Proj(cx, cy, 1.45, yaw=68, pitch=12)
    rk = eout(lin(t, T_TOOTHED - 0.3, T_TOOTHED + 0.3))
    # axle/hub behind
    cyl3(cv, pj, (0, 0, 70), (0, 0, 10), 60, STEEL_D, n=40)
    if rk > 0:
        prof = ring_prof(th)
        extrude(cv, pj, prof, -12 * rk, 12 * rk, hx("#aeb8c6"), alpha=rk, rim=hx("#d9e2ee"), rim_w=1.4)
        hole = circle_prof(0, 0, 112, 48)
        cv.drawPath(poly_path(pj.pts(hole, -12 * rk)), paint(hx("#0b111c"), a=rk))
        cyl3(cv, pj, (0, 0, 10), (0, 0, -30), 70, STEEL, n=40)
        for i in range(5):
            a = th + i * 2 * math.pi / 5
            p = pj(48 * math.cos(a), 48 * math.sin(a), -31)
            cv.drawCircle(p[0], p[1], 9, paint(hx("#2a313c")))
    # sensor pickup at the top
    sk = eout(lin(t, T_SENSOR - 0.3, T_SENSOR + 0.3))
    if sk > 0:
        tip = pj(0, -RING_R1 - 8, 0)
        top = pj(0, -RING_R1 - 120, 0)
        dy = (1 - sk) * -60
        cyl3(cv, pj, (0, -RING_R1 - 120 - (1 - sk) * 60, 0), (0, -RING_R1 - 10 - (1 - sk) * 60, 0), 22,
             hx("#3b4556"), alpha=sk, edge=AMBER, edge_w=1.5)
        on = tooth_under(th) * eout(lin(t, T_SENSOR, T_SENSOR + 0.4))
        if on > 0:
            cv.drawCircle(tip[0], tip[1] + dy, 34, paint(AMBER, a=0.55 * on * sk, blur=12))
        # wire to the trace
        wire = spline(np.array([[top[0], top[1] + dy], [top[0] + 10, top[1] - 60], [820, 520], [860, 1110]]), 60)
        cv.drawPath(poly_path(wire, close=False), paint(AMBER, a=0.7 * sk, stroke=3))
    brand.label(cv, t, "TOOTHED RING", tuple(pj(RING_R1 * 0.7, RING_R1 * 0.75, -12)), (150, 1060), CYAN,
                T_TOOTHED + 0.1, S_SENSOR[1])
    brand.label(cv, t, "SENSOR", tuple(pj(-20, -RING_R1 - 70, 0)), (150, 560), AMBER, T_SENSOR + 0.1, S_SENSOR[1])
    # pulse trace
    gk = eout(lin(t, T_COUNTING - 0.2, T_COUNTING + 0.3))
    if gk > 0:
        gx, gy, gw, gh = 150, 1180, 740, 110
        cv.saveLayerAlpha(None, int(255 * gk))
        brand.graph_box(cv, (gx, gy, gw, gh), "SENSOR SIGNAL · ONE PULSE PER TOOTH")
        ts = np.linspace(t - 2.0, t, 300)
        ys = np.array([tooth_under(ring_angle(x)) if x > T_SENSOR else 0.0 for x in ts])
        pts = np.stack([gx + (ts - (t - 2.0)) / 2.0 * gw, gy + gh - 10 - ys * (gh - 30)], 1)
        brand.curve(cv, pts, AMBER, width=4)
        cv.restore()
        n = int(max(0, t - T_SENSOR) * 7.0)
        pill(cv, 870, 1080, f"TEETH COUNTED  {n}", font("inter_xb", 26), INK, border=AMBER, a=gk,
             align="right", tracking=2)
    brand.note(cv, "ANIMATION SLOWED", 0.9 * k)
    cv.restore()


T_COUNTING = F("parts", "counting")

# ================================================================== TOP VIEW car (sensors, how, history, inset)
TV_WHEELS = [(-118, -170, "FL"), (118, -170, "FR"), (-118, 180, "RL"), (118, 180, "RR")]


def top_car(cv, cx, cy, s=1.0, steer=0.0, a=1.0, glow=None, body=C_BODY, rot=0.0, xray=0.0, wheel_c=None):
    """Top view car, nose up (rot in degrees, clockwise). glow: dict wheel -> (color, k)."""
    if a <= 0:
        return
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    cv.scale(s, s)
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    for wx, wy, nm in TV_WHEELS:
        cv.save()
        cv.translate(wx, wy)
        if wy < 0:
            cv.rotate(steer)
        c = (wheel_c or {}).get(nm, hx("#15171b"))
        cv.drawRoundRect(skia.Rect.MakeXYWH(-17, -38, 34, 76), 8, 8, paint(c))
        cv.drawRoundRect(skia.Rect.MakeXYWH(-17, -38, 34, 76), 8, 8, paint(hx("#3a4252"), stroke=2))
        if glow and nm in glow:
            gc, gk = glow[nm]
            if gk > 0:
                cv.drawRoundRect(skia.Rect.MakeXYWH(-21, -42, 42, 84), 10, 10, paint(gc, a=0.6 * gk, blur=10))
                cv.drawRoundRect(skia.Rect.MakeXYWH(-17, -38, 34, 76), 8, 8, paint(gc, a=gk, stroke=3))
        cv.restore()
    body_r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-110, -265, 220, 530), 70, 70)
    cv.drawRRect(body_r, paint(hx("#000000"), a=0.5, blur=18))
    bp = skia.Paint(AntiAlias=True)
    bp.setShader(lin_grad((-110, 0), (110, 0), [shade(body, 0.7), shade(body, 1.15), shade(body, 0.7)]))
    bp.setAlphaf(1 - 0.8 * xray)
    cv.drawRRect(body_r, bp)
    if xray > 0:
        cv.drawRRect(body_r, paint(CYAN, a=0.15 * xray))
        cv.drawRRect(body_r, paint(CYAN, a=0.9 * xray, stroke=2.5))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-86, -130, 172, 70), 20, 20, paint(hx("#7fa6d6"), a=0.85 * (1 - 0.7 * xray)))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-80, 120, 160, 50), 18, 18, paint(hx("#4f6f9a"), a=0.85 * (1 - 0.7 * xray)))
    cv.drawRoundRect(skia.Rect.MakeXYWH(-92, -50, 184, 160), 16, 16, paint(shade(body, 0.85), a=1 - 0.8 * xray))
    for x in (-62, 62):
        look.bloom(cv, x, -262, 6, hx("#fff4d6"), a=0.8)
    cv.restore()
    cv.restore()


def wheel_speeds_how(t):
    """Per-wheel speed fraction during the top-view/how beat: FL drops way faster than the car."""
    car = keys(t, [(T_COMPUTER, 1.0), (T_SLOWS, 0.92), (T_VALVE, 0.80)])
    fl = car * (1 - 0.62 * ease(lin(t, T_SLOWS, T_LOCKW + 0.1)))
    return car, {"FL": fl, "FR": car, "RL": car, "RR": car}


def draw_topv(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cx, cy = 540, 900
    car, ws = wheel_speeds_how(t)
    danger = ease(lin(t, T_SLOWS + 0.2, T_LOCKW))
    top_car(cv, cx, cy, 0.95, a=1, xray=1.0,
            glow={"FL": (mix(CYAN, RED, danger), 1.0), "FR": (CYAN, 1.0), "RL": (CYAN, 1.0), "RR": (CYAN, 1.0)})
    # ECU in the middle, wires to each wheel sensor
    ek = eout(lin(t, T_COMPUTER - 0.1, T_COMPUTER + 0.4))
    for i, (wx, wy, nm) in enumerate(TV_WHEELS):
        p = (cx + wx * 0.95, cy + wy * 0.95)
        pe = (cx, cy - 10)
        prog = eout(lin(t, T_COMPUTER + 0.1 * i, T_COMPUTER + 0.4 + 0.1 * i))
        c = mix(AMBER, RED, danger) if nm == "FL" else AMBER
        cv.drawLine(p[0], p[1], p[0] + (pe[0] - p[0]) * prog, p[1] + (pe[1] - p[1]) * prog, paint(c, a=0.8, stroke=3))
        # pulses travelling to the ECU
        for j in range(3):
            u = ((t * ws[nm] * 1.6) + j / 3) % 1
            if prog > 0.99:
                cv.drawCircle(p[0] + (pe[0] - p[0]) * u, p[1] + (pe[1] - p[1]) * u, 6, paint(c, a=0.9))
        # speed bar beside the wheel
        left = wx < 0
        bx = cx + wx * 0.95 + (-60 if left else 60)
        by = cy + wy * 0.95
        bw = 190
        x0 = bx - bw if left else bx
        fr = ws[nm]
        bc = mix(CYAN, RED, danger) if nm == "FL" else CYAN
        cv.drawRoundRect(skia.Rect.MakeXYWH(x0, by - 12, bw, 24), 12, 12, paint(hx("#1a2232"), a=ek))
        fw = bw * fr
        cv.drawRoundRect(skia.Rect.MakeXYWH(bx - fw if left else bx, by - 12, max(24, fw), 24), 12, 12,
                         paint(bc, a=ek))
        draw_text(cv, f"{nm}  {int(round(60 * fr))}", (x0 + bw if left else x0), by - 26, font("inter_xb", 24),
                  INK, a=ek, align="right" if left else "left", tracking=1.5)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 70, cy - 50, 140, 80), 14, 14)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=ek))
    cv.drawRRect(rr, paint(GREEN, a=ek, stroke=3))
    draw_text(cv, "ABS", cx, cy + 4, font("inter_blk", 34), INK, a=ek, align="center", tracking=4)
    draw_text(cv, "COMPUTER", cx, cy + 22, font("inter_sb", 13), MUTED, a=ek, align="center", tracking=2)
    pill(cv, 540, 560, "CAR SPEED  " + str(int(round(60 * car))), font("inter_xb", 28), INK, border=CYAN, a=ek,
         align="center", tracking=2, dot=CYAN)
    brand.stamp(cv, t, "ABOUT TO LOCK", T_LOCKW - 0.15, dur=1.6, center=(540, 1290))
    cv.restore()


# ================================================================== CIRCUIT (one brake channel)
MC = (170, 800, 330, 870)           # master cylinder rect
P_MAIN = np.array([[330, 835], [620, 835], [620, 905]], float)
IV = (620, 945)                     # inlet valve centre (vertical pipe)
P_TOCAL = np.array([[620, 985], [620, 1190], [712, 1190]], float)
DISC = (830, 1190, 108)
NODE_OUT = (620, 1100)
P_OUT1 = np.array([[620, 1100], [470, 1100]], float)
OV = (420, 1100)                    # outlet valve centre (horizontal pipe)
P_OUT2 = np.array([[370, 1100], [300, 1100], [300, 1200]], float)
ACC = (300, 1250)
P_RET1 = np.array([[255, 1270], [205, 1270]], float)
PUMP = (160, 1270)
P_RET2 = np.array([[160, 1225], [160, 975], [460, 975], [460, 835]], float)


def valve(cv, c, vertical, open_k, name, a=1.0, col_open=CYAN):
    x, y = c
    w, h = (78, 80) if vertical else (100, 70)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), 14, 14)
    cc = mix(RED, col_open, open_k)
    cv.drawRRect(rr, paint(hx("#141b28"), a=a))
    cv.drawRRect(rr, paint(cc, a=a, stroke=3.5))
    # gate: a bar that slides across the passage
    if vertical:
        gx = x - 22 + 44 * (1 - open_k) * 0 + 0
        cv.drawLine(x - 30, y, x - 30 + 60 * (1 - open_k), y, paint(cc, a=a, stroke=12, cap=skia.Paint.kRound_Cap))
    else:
        cv.drawLine(x, y - 26, x, y - 26 + 52 * (1 - open_k), paint(cc, a=a, stroke=12, cap=skia.Paint.kRound_Cap))
    return cc


def draw_circuit(cv, t, k, P, iv, ov, pump, pump_phase, out_phase, in_phase, ret_phase, press=1.0, buzz=0.0,
                 show_labels=None):
    """P: caliper pressure 0..1, iv/ov: valve open 0..1, pump: running 0..1. phases: cumulative flow distances."""
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    jit = buzz * 3.0 * math.sin(2 * math.pi * 31 * t)
    # pipes
    hi = mix(hx("#5a3a0a"), AMBER, 0.35 + 0.65 * P)
    for pts in (P_MAIN, P_TOCAL, P_OUT1, P_OUT2, P_RET1, P_RET2):
        pipe(cv, pts, 22, STEEL_D, glass=True)
    for pts, phase, c, on in ((P_MAIN, in_phase, AMBER, iv), (P_TOCAL, in_phase, hi, iv),
                              (P_OUT1, out_phase, AMBER, ov), (P_OUT2, out_phase, AMBER, ov),
                              (P_RET1, ret_phase, AMBER, pump), (P_RET2, ret_phase, AMBER, pump)):
        flow(cv, pts, phase, 1.0, 30, c, r=5.5, a=0.25 + 0.75 * on)
    # master cylinder + pedal
    x0, y0, x1, y1 = MC
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), 14, 14, paint(hx("#3b4556")))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0 + 40, y0 + 18, x1 - 10, y1 - 18), 8, 8, paint(AMBER, a=0.75))
    rodx = x0 + 10 + 30 * press + jit
    cv.drawRect(skia.Rect.MakeLTRB(x0 + 10, y0 + 22, rodx + 30, y1 - 22), paint(STEEL))
    pv = (96 + jit, 760)
    cv.drawLine(pv[0], pv[1], x0 + 10 + jit, (y0 + y1) / 2, paint(STEEL, stroke=9, cap=skia.Paint.kRound_Cap))
    cv.drawLine(x0 + 10 + jit - 24, (y0 + y1) / 2 + 30, x0 + 10 + jit + 6, (y0 + y1) / 2 - 2,
                paint(hx("#2b313c"), stroke=16, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(pv[0], pv[1], 8, paint(STEEL_D))
    if buzz > 0:
        for i in range(3):
            r = 30 + 14 * i + 10 * ((t * 6) % 1)
            cv.drawArc(skia.Rect.MakeXYWH(x0 - 10 - r, (y0 + y1) / 2 + 20 - r, 2 * r, 2 * r), 140, 80, False,
                       paint(YEL, a=buzz * (0.8 - 0.2 * i), stroke=3))
    # valves
    valve(cv, IV, True, iv, "INLET")
    valve(cv, OV, False, ov, "OUTLET", col_open=AMBER)
    # accumulator
    ax, ay = ACC
    cv.drawRoundRect(skia.Rect.MakeXYWH(ax - 45, ay - 50, 90, 100), 16, 16, paint(hx("#141b28")))
    lvl = clamp(0.15 + 0.7 * acc_level_now[0])
    cv.drawRoundRect(skia.Rect.MakeXYWH(ax - 40, ay + 45 - 90 * lvl, 80, 90 * lvl), 12, 12, paint(AMBER, a=0.7))
    cv.drawRoundRect(skia.Rect.MakeXYWH(ax - 45, ay - 50, 90, 100), 16, 16, paint(hx("#5d7499"), stroke=3))
    # pump
    px, py = PUMP
    cv.drawCircle(px, py, 45, paint(hx("#141b28")))
    cv.drawCircle(px, py, 45, paint(mix(hx("#5d7499"), GREEN, pump), stroke=3.5))
    for i in range(3):
        a = pump_phase * 0.05 + i * 2 * math.pi / 3
        cv.drawLine(px, py, px + 32 * math.cos(a), py + 32 * math.sin(a), paint(mix(STEEL, GREEN, pump), stroke=6,
                                                                                 cap=skia.Paint.kRound_Cap))
    if pump > 0:
        cv.drawCircle(px, py, 52, paint(GREEN, a=0.35 * pump, blur=12))
    # disc + caliper (front view)
    dx, dy, dr = DISC
    cv.drawCircle(dx, dy, dr, paint(hx("#9aa4b2")))
    cv.drawCircle(dx, dy, dr, paint(hx("#4b5566"), stroke=3))
    cv.drawCircle(dx, dy, 44, paint(hx("#5a6577")))
    for i in range(5):
        a = i * 2 * math.pi / 5 + wheel_rot_now[0]
        cv.drawCircle(dx + 26 * math.cos(a), dy + 26 * math.sin(a), 6, paint(hx("#2a313c")))
    for i in range(12):
        a = i * 2 * math.pi / 12 + wheel_rot_now[0]
        cv.drawCircle(dx + 78 * math.cos(a), dy + 78 * math.sin(a), 5, paint(hx("#6a7486")))
    cal = skia.Rect.MakeXYWH(dx - dr - 22, dy - 70, 54, 140)
    cv.drawRoundRect(cal, 12, 12, paint(mix(hx("#4a5262"), RED, P)))
    if P > 0.05:
        cv.drawRoundRect(cal, 12, 12, paint(RED, a=0.45 * P, blur=14))
    cv.drawRoundRect(cal, 12, 12, paint(hx("#1b2130"), stroke=3))
    # labels
    lab = show_labels or {}
    f = font("inter_xb", 22)
    for key, (txt, x, y, c, al) in {"mc": ("MASTER CYL.", 250, 905, MUTED, "center"),
                                    "iv": ("INLET VALVE", 680, 945, mix(RED, CYAN, iv), "left"),
                                    "ov": ("OUTLET VALVE", 420, 1170, mix(RED, AMBER, ov), "center"),
                                    "acc": ("STORE", 300, 1330, MUTED, "center"),
                                    "pump": ("PUMP", 160, 1350, mix(MUTED, GREEN, pump), "center"),
                                    "cal": ("CALIPER", 830, 1340, RED if P > 0.5 else MUTED, "center")}.items():
        a = lab.get(key, 1.0)
        if a > 0:
            draw_text(cv, txt, x, y + 8, f, c, a=a, align=al, tracking=2)
    cv.restore()


acc_level_now = [0.0]
wheel_rot_now = [0.0]


# --- CIRCUIT beat (how): keyframes
def how_state(t):
    iv = 1 - ease(lin(t, T_CLOSES - 0.05, T_CLOSES + 0.25))
    ov = ease(lin(t, T_OPENS - 0.05, T_OPENS + 0.25))
    P = keys(t, [(T_VALVE - 0.2, 0.95), (T_CLOSES + 0.2, 0.95), (T_OPENS, 0.95), (T_OUT + 0.4, 0.35)])
    car = keys(t, [(T_VALVE - 0.2, 0.80), (T_RE, 0.72)])
    w = keys(t, [(T_VALVE - 0.2, 0.30), (T_OPENS, 0.26), (T_OUT + 0.7, 0.66)])
    acc = keys(t, [(T_OPENS, 0.0), (T_OUT + 0.4, 0.8)])
    return P, iv, ov, car, w, acc


_HT = np.arange(S_CIRCUIT[0] - 0.5, S_CIRCUIT[1] + 0.5, 1 / 60)
_HS = np.array([how_state(x) for x in _HT])
_IN_PH = np.concatenate([[0], np.cumsum(260 * _HS[:-1, 1] / 60 * 0.4)])
_OUT_PH = np.concatenate([[0], np.cumsum(260 * _HS[:-1, 2] / 60)])
_HROT = np.concatenate([[0], np.cumsum(_HS[:-1, 4] * 6 / 60)])


def trace_graph(cv, t, a, t0, t1, fn, rect, title, now_t, legends):
    """Rolling-in graph over [t0, t1]: fn(x) -> list of (value, color, dashed)."""
    gx, gy, gw, gh = rect
    cv.saveLayerAlpha(None, int(255 * a))
    brand.graph_box(cv, rect, title, "TIME")
    xs = np.linspace(t0, min(now_t, t1), 160)
    if len(xs) > 1 and now_t > t0:
        vals = [fn(x) for x in xs]
        for j in range(len(vals[0])):
            c, dashed = vals[0][j][1], vals[0][j][2]
            pts = np.stack([gx + (xs - t0) / (t1 - t0) * gw,
                            gy + gh - np.array([v[j][0] for v in vals]) * (gh - 12)], 1)
            brand.curve(cv, pts, c, dashed=dashed, width=4)
            if not dashed:
                brand.dot(cv, pts[-1][0], pts[-1][1], c)
    lx = gx + gw
    for txt, c in legends[::-1]:
        lx -= draw_text(cv, txt, lx, gy - 12, font("inter_xb", 20), c, align="right", tracking=2) + 26
    cv.restore()


def draw_circuit_how(cv, t, k):
    if k <= 0:
        return
    P, iv, ov, car, w, acc = how_state(t)
    acc_level_now[0] = acc
    wheel_rot_now[0] = float(np.interp(t, _HT, _HROT))
    draw_circuit(cv, t, k, P, iv, ov, 0.0, 0.0, float(np.interp(t, _HT, _OUT_PH)), float(np.interp(t, _HT, _IN_PH)),
                 0.0)
    gk = k
    trace_graph(cv, t, gk, S_CIRCUIT[0], S_CIRCUIT[1], lambda x: [(how_state(x)[3], INK, True),
                                                                  (how_state(x)[4], CYAN, False),
                                                                  (how_state(x)[0], RED, False)],
                (130, 500, 760, 170), "", t, [("CAR", INK), ("WHEEL", CYAN), ("PRESSURE", RED)])
    brand.stamp(cv, t, "HOLD", T_HOLD - 0.1, dur=T_ANOTHER - T_HOLD + 0.1, center=(790, 770), color=YEL,
                bg=hx("#2a2205"))
    brand.stamp(cv, t, "RELEASE", T_OPENS + 0.05, dur=1.5, center=(770, 770), color=AMBER, bg=hx("#2a1a05"))
    brand.note(cv, "ONE WHEEL'S CIRCUIT · SIMPLIFIED", 0.9 * k, dy=-50)


# ================================================================== GRIP graph
G_RECT = (150, 600, 740, 470)


def mu_brake(s):
    s = np.asarray(s, float)
    B, C, D = 9.0, 1.9, 1.0
    return D * np.sin(C * np.arctan(B * s))


_S = np.linspace(0, 1, 400)
_MB = mu_brake(_S)
_MB = _MB / _MB.max()
S_PEAK = float(_S[np.argmax(_MB)])


def mu_b(s):
    return float(np.interp(s, _S, _MB))


def mu_lat(s):
    return 0.05 + 0.95 * (1 - s) ** 2.2


def g_xy(s, m):
    gx, gy, gw, gh = G_RECT
    return gx + s * gw, gy + gh - m * (gh - 40)


def draw_grip(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    # rehook question
    qk = win(t, T_RE - 0.1, T_KEY + 0.15, 0.25, 0.35)
    if qk > 0:
        s = 0.8 + 0.2 * eback(lin(t, T_RE - 0.1, T_RE + 0.3))
        cv.save()
        cv.translate(540, 820)
        cv.scale(s, s)
        draw_text(cv, "WHY LET GO?", 0, 30, font("pop_b", 120), YEL, a=qk, align="center", glow=16)
        cv.restore()
        pedal_inset(cv, 440, 940, 1 - ease(lin(t, T_RE + 0.2, T_RE + 0.9)), a=qk, label="RELEASE", lc=CYAN)
    gk = eout(lin(t, T_KEY - 0.1, T_KEY + 0.4))
    if gk > 0:
        gx, gy, gw, gh = G_RECT
        cv.saveLayerAlpha(None, int(255 * gk))
        brand.graph_box(cv, G_RECT, "GRIP")
        draw_text(cv, "ROLLING", gx, gy + gh + 34, font("inter_sb", 20), CYAN, tracking=2)
        draw_text(cv, "WHEEL SLIP  →", gx + gw * 0.5, gy + gh + 34, font("inter_sb", 20), MUTED, align="center",
                  tracking=2)
        draw_text(cv, "LOCKED", gx + gw, gy + gh + 34, font("inter_sb", 20), RED, align="right", tracking=2)
        draw_text(cv, "ILLUSTRATIVE CURVES", gx + gw, gy - 12, font("inter_sb", 18), MUTED, a=0.8, align="right",
                  tracking=2)
        # peak band
        bk = eout(lin(t, T_TURNING - 0.1, T_TURNING + 0.4))
        if bk > 0:
            x0, _ = g_xy(0.10, 0)
            x1, _ = g_xy(0.20, 0)
            cv.drawRect(skia.Rect.MakeLTRB(x0, gy, x1, gy + gh), paint(GREEN, a=0.16 * bk))
            cv.drawLine(x0, gy, x0, gy + gh, paint(GREEN, a=0.5 * bk, stroke=2))
            cv.drawLine(x1, gy, x1, gy + gh, paint(GREEN, a=0.5 * bk, stroke=2))
            draw_text(cv, "~10-20%", (x0 + x1) / 2, gy + gh - 12, font("inter_xb", 18), GREEN, a=bk, align="center")
        prog = eout(lin(t, T_KEY + 0.1, T_TURNING + 0.2))
        pts = np.array([g_xy(s, m * 0.92) for s, m in zip(_S, _MB)])
        brand.curve(cv, pts, CYAN, prog=prog)
        draw_text(cv, "BRAKING GRIP", g_xy(0.42, 0)[0], g_xy(0.42, mu_b(0.42) * 0.92)[1] - 30, font("inter_xb", 22),
                  CYAN, a=prog, align="left", tracking=2)
        lk = eout(lin(t, T_SIDEWAYS - 0.1, T_SIDEWAYS + 0.8))
        if lk > 0:
            pl = np.array([g_xy(s, mu_lat(s) * 0.92) for s in _S])
            brand.curve(cv, pl, AMBER, prog=lk)
            draw_text(cv, "SIDEWAYS GRIP", gx + 20, g_xy(0, 0.95)[1] - 10, font("inter_xb", 22), AMBER, a=lk,
                      tracking=2)
            if t > T_STEERING:
                ek = eout(lin(t, T_STEERING, T_STEERING + 0.3))
                p = g_xy(1, mu_lat(1) * 0.92)
                cv.drawCircle(p[0], p[1], 22, paint(AMBER, a=0.5 * ek, blur=8))
                draw_text(cv, "ALMOST ZERO", p[0] - 10, p[1] - 30, font("inter_xb", 22), AMBER, a=ek, align="right",
                          tracking=2)
        # the dot: rolling at the peak, then sliding at lock
        if t > T_TURNING - 0.1:
            sv = keys(t, [(T_TURNING, S_PEAK), (T_SLIDING - 0.3, S_PEAK), (T_SLIDING + 0.3, 1.0)])
            p = g_xy(sv, mu_b(sv) * 0.92)
            c = mix(GREEN, RED, lin(sv, S_PEAK, 1.0))
            brand.dot(cv, p[0], p[1], c)
            if t < T_SLIDING - 0.1:
                pill(cv, p[0] + 30, p[1] - 50, "STILL TURNING · MOST GRIP", font("inter_xb", 22), INK, border=GREEN,
                     a=eout(lin(t, T_TURNING, T_TURNING + 0.3)), tracking=1.5)
            else:
                pill(cv, p[0] - 20, p[1] - 50, "SLIDING · LESS GRIP", font("inter_xb", 22), INK, border=RED,
                     a=eout(lin(t, T_SLIDING, T_SLIDING + 0.3)), align="right", tracking=1.5)
        cv.restore()
        # steering inset: front wheels turned, car goes straight
        ik = win(t, T_STEERING - 0.2, S_GRIP[1], 0.3, 0.3)
        if ik > 0:
            cx, cy = 300, 1290
            u = (t - T_STEERING) % 1.6 / 1.6
            top_car(cv, cx + 330 * u, cy, 0.28, steer=-28, a=ik * (1 - lin(u, 0.85, 1)), rot=90,
                    wheel_c={"FL": hx("#5a1414"), "FR": hx("#5a1414")})
            cv.drawLine(cx + 80, cy, cx + 420, cy, paint(INK, a=0.6 * ik, stroke=3))
            arrow = skia.Path()
            arrow.moveTo(cx + 440, cy); arrow.lineTo(cx + 418, cy - 12); arrow.lineTo(cx + 418, cy + 12); arrow.close()
            cv.drawPath(arrow, paint(INK, a=0.6 * ik))
            # steer intent (dashed curve)
            pts = spline(np.array([[cx + 80, cy], [cx + 200, cy - 10], [cx + 320, cy - 70], [cx + 400, cy - 120]]), 30)
            brand.curve(cv, pts, AMBER, a=ik, dashed=True)
            draw_text(cv, "WHERE YOU STEER", cx + 410, cy - 128, font("inter_xb", 18), AMBER, a=ik, align="right",
                      tracking=1.5)
        brand.stamp(cv, t, "NO STEERING", T_NOTHING - 0.15, dur=1.6, center=(540, 470))
    cv.restore()


# ================================================================== CYCLE (pump)
CYC = 1.25          # seconds per hold/release/reapply cycle on screen (slowed)


def cyc_state(t):
    """Procedural ABS cycle: returns P, iv, ov, pump, wheel, car."""
    t0 = T_PUMP - 0.2
    u = ((t - t0) / CYC) % 1.0 if t > t0 else 0.0
    # 0-0.40 reapply (inlet open, pump pushes), 0.40-0.55 hold, 0.55-0.85 release, 0.85-1 hold
    if u < 0.40:
        P = 0.35 + 0.6 * ease(u / 0.40)
        iv, ov = 1.0, 0.0
    elif u < 0.55:
        P, iv, ov = 0.95, 0.0, 0.0
    elif u < 0.85:
        P = 0.95 - 0.6 * ease((u - 0.55) / 0.30)
        iv, ov = 0.0, 1.0
    else:
        P, iv, ov = 0.35, 0.0, 0.0
    pump = 1.0
    car = keys(t, [(T_PUMP, 0.72), (T_HIST, 0.45)])
    w = car * (0.86 - 0.12 * (P - 0.35) / 0.6)
    return P, iv, ov, pump, w, car, u


def cyc_phase(u):
    if u < 0.40:
        return "REAPPLY", GREEN
    if u < 0.55 or u >= 0.85:
        return "HOLD", YEL
    return "RELEASE", AMBER


_CT = np.arange(S_CYCLE[0] - 0.5, S_CYCLE[1] + 0.5, 1 / 60)
_CS = np.array([cyc_state(x)[:6] for x in _CT])
_C_IN = np.concatenate([[0], np.cumsum(220 * _CS[:-1, 1] / 60)])
_C_OUT = np.concatenate([[0], np.cumsum(220 * _CS[:-1, 2] / 60)])
_C_RET = np.concatenate([[0], np.cumsum(160 * _CS[:-1, 3] / 60)])
_C_ROT = np.concatenate([[0], np.cumsum(_CS[:-1, 4] * 6 / 60)])


def draw_cycle(cv, t, k):
    if k <= 0:
        return
    P, iv, ov, pump, w, car, u = cyc_state(t)
    pump_k = eout(lin(t, T_PUMPW - 0.1, T_PUMPW + 0.3))
    acc_level_now[0] = 0.6 - 0.4 * pump_k * math.sin(2 * math.pi * u) * 0.5
    wheel_rot_now[0] = float(np.interp(t, _CT, _C_ROT))
    buzz = win(t, T_BUZZ - 0.1, T_HIST, 0.15, 0.3)
    draw_circuit(cv, t, k, P, iv, ov, pump * pump_k, float(np.interp(t, _CT, _C_RET)) * 3,
                 float(np.interp(t, _CT, _C_OUT)), float(np.interp(t, _CT, _C_IN)),
                 float(np.interp(t, _CT, _C_RET)) * pump_k, buzz=buzz)
    trace_graph(cv, t, k, S_CYCLE[0], S_CYCLE[1], lambda x: [(cyc_state(x)[5], INK, True), (cyc_state(x)[4], CYAN, False),
                                                              (cyc_state(x)[0], RED, False)],
                (130, 500, 760, 170), "", t, [("CAR", INK), ("WHEEL", CYAN), ("PRESSURE", RED)])
    ph, pc = cyc_phase(u)
    pill(cv, 780, 880, ph, font("inter_blk", 30), INK, border=pc, a=k * pump_k, align="center", tracking=3, dot=pc)
    dk = win(t, T_DOZEN - 0.1, S_CYCLE[1], 0.3, 0.3)
    brand.readout(cv, dk * k, "12+", "TIMES A SECOND (REAL SPEED)", dy=0)
    if t < T_DOZEN - 0.1:
        brand.note(cv, "ANIMATION SLOWED", 0.9 * k, dy=-50)
    else:
        brand.note(cv, "ANIMATION SLOWED", 0.9 * k)
    bk = win(t, T_BUZZ - 0.1, S_CYCLE[1], 0.2, 0.3)
    if bk > 0:
        pill(cv, 640, 770, "PEDAL BUZZ = ABS WORKING", font("inter_xb", 24), INK, border=GREEN, a=bk * k,
             align="center", tracking=2, dot=GREEN)


# ================================================================== 1978
def draw_hist(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    yk = eout(lin(t, T_HIST, T_NINETEEN + 0.8))
    year = int(round(1950 + 28 * yk))
    s = 1.0 + 0.08 * eback(lin(t, T_NINETEEN + 0.6, T_NINETEEN + 1.0)) * (yk >= 1)
    cv.save()
    cv.translate(540, 640)
    cv.scale(s, s)
    draw_text(cv, str(year), 0, 60, font("inter_blk", 200), RED if yk >= 1 else INK, align="center", glow=20 if yk >= 1
              else None, tracking=8)
    cv.restore()
    fk = eout(lin(t, T_FIRST - 0.1, T_FIRST + 0.4))
    draw_text(cv, "FIRST ELECTRONIC FOUR-WHEEL ABS", 540, 760, font("inter_xb", 34), INK, a=fk, align="center",
              tracking=2)
    bk = eout(lin(t, T_BOSCH - 0.1, T_BOSCH + 0.4))
    brand.chips(cv, bk, 840, [("BOSCH", bk), ("MERCEDES S-CLASS", bk)], center=True)
    glow = {nm: (CYAN, eout(lin(t, T_FIRST + 0.1 * i, T_FIRST + 0.3 + 0.1 * i))) for i, (_, _, nm) in
            enumerate(TV_WHEELS)}
    top_car(cv, 540, 1130, 0.58, rot=90, a=1, glow=glow, body=hx("#55606f"))
    cv.restore()


# ================================================================== DRIVE (top view, wet road)
def drive_state(t):
    t0 = T_DRIVE - 0.2
    d = t - t0
    v = 900 * max(0.25, 1 - 0.16 * max(0, d))
    swerve = keys(t, [(T_STEER - 0.2, 0.0), (T_STEER + 0.7, -210.0), (T_STEER + 1.9, -230.0)])
    steer = keys(t, [(T_STEER - 0.2, 0.0), (T_STEER + 0.25, -16.0), (T_STEER + 0.9, 8.0), (T_STEER + 1.5, 0.0)])
    head = keys(t, [(T_STEER - 0.2, 0.0), (T_STEER + 0.45, -12.0), (T_STEER + 1.2, 2.0), (T_STEER + 1.7, 0.0)])
    return v, swerve, steer, head


_DT2 = np.arange(S_DRIVE[0] - 0.5, S_DRIVE[1] + 0.5, 1 / 60)
_DD = np.concatenate([[0], np.cumsum(np.array([drive_state(x)[0] for x in _DT2])[:-1] / 60)])


def draw_drive(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    d = float(np.interp(t, _DT2, _DD))
    v, sw, st, hd = drive_state(t)
    # road
    cv.drawRect(skia.Rect.MakeLTRB(180, 660, 900, 1420), paint(hx("#161b24")))
    for x in (180, 900):
        cv.drawRect(skia.Rect.MakeLTRB(x - 4, 660, x + 4, 1420), paint(hx("#cfd6e2"), a=0.7))
    for i in range(-1, 8):
        y = (i * 150 + d) % 1050 + 560
        if 660 < y < 1400:
            cv.drawRect(skia.Rect.MakeLTRB(536, y, 544, min(1420, y + 80)), paint(hx("#cfd6e2"), a=0.5))
    # wet sheen
    rng = np.random.default_rng(8)
    for i in range(30):
        x = rng.uniform(200, 880)
        y = (rng.uniform(0, 900) + d) % 900 + 600
        if 680 < y < 1400:
            cv.drawOval(skia.Rect.MakeXYWH(x, y, 70, 14), paint(hx("#6f8fbf"), a=0.12))
    # stopped car ahead in our lane (comes down the screen)
    oy = keys(t, [(T_DRIVE - 0.2, 640.0), (T_STEER + 0.4, 980.0), (T_STEER + 1.8, 1300.0)])
    if oy < 1500:
        top_car(cv, 720, oy, 0.42, a=1, body=hx("#6a7486"))
        look.bloom(cv, 720 - 26, oy + 112, 5, RED, a=0.9)
        look.bloom(cv, 720 + 26, oy + 112, 5, RED, a=0.9)
    # our car
    cx = 720 + sw
    abs_on = win(t, T_DRIVE + 0.2, S_DRIVE[1], 0.1, 0.3)
    flick = 0.5 + 0.5 * math.sin(2 * math.pi * 1.6 * t)
    top_car(cv, cx, 1240, 0.42, steer=st, rot=hd, a=1,
            glow={"FL": (AMBER, abs_on * flick), "FR": (AMBER, abs_on * flick), "RL": (AMBER, abs_on * flick),
                  "RR": (AMBER, abs_on * flick)})
    cv.restore()
    # do / don't panel
    pk = eout(lin(t, T_DONT - 0.2, T_DONT + 0.3))
    if pk > 0:
        brand.panel(cv, 100, 440, 880 - 100, 200, "WITH ABS", AMBER, a=pk * k)
        brand.bullet(cv, 140, 590, "PUMP", False, a=pk * k, size=34)
        brand.bullet(cv, 330, 590, "PRESS HARD", True, a=eout(lin(t, T_PRESS - 0.1, T_PRESS + 0.3)) * k, size=34)
        brand.bullet(cv, 640, 590, "STEER", True, a=eout(lin(t, T_STEER - 0.1, T_STEER + 0.3)) * k, size=34)
        brand.lamp(cv, 780, 503, "ABS", abs_on * (0.6 + 0.4 * flick) * pk * k, w=150, h=50)


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(0, "THE SKID", RED), (T_PARTS, "WHEEL SENSOR", AMBER), (T_COMPUTER, "THE COMPUTER", GREEN),
           (T_VALVE, "THE VALVES", CYAN), (T_RE, "THE QUESTION", YEL), (T_KEY, "THE ANSWER", RED),
           (T_PUMP, "THE CYCLE", AMBER), (T_HIST, "HISTORY", INK), (T_DRIVE, "WHAT TO DO", GREEN)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    if T_DRIVE - 0.1 < t:
        k *= 1 - eout(lin(t, T_DONT - 0.3, T_DONT))
    brand.status_pill(cv, k, txt, c)


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    ks = scene_k(t, S_ROAD, 0.0, 0.3)
    draw_road(cv, t, ks)
    draw_sensor(cv, t, scene_k(t, S_SENSOR))
    draw_topv(cv, t, scene_k(t, S_TOPV))
    draw_circuit_how(cv, t, scene_k(t, S_CIRCUIT))
    draw_grip(cv, t, scene_k(t, S_GRIP))
    draw_cycle(cv, t, scene_k(t, S_CYCLE))
    draw_hist(cv, t, scene_k(t, S_HIST))
    draw_drive(cv, t, scene_k(t, S_DRIVE) * kE)
    draw_road_overlays(cv, t, ks)
    draw_header(cv, t)


# ================================================================== sound (synthesized here)
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _bp(x, f0, f1):
    from scipy import signal
    b, a = signal.butter(2, [f0 / (SR / 2), f1 / (SR / 2)], btype="band")
    return signal.lfilter(b, a, x)


def _lp(x, fc):
    from scipy import signal
    b, a = signal.butter(2, fc / (SR / 2))
    return signal.lfilter(b, a, x)


def _norm(x, pk=0.9):
    x = np.asarray(x, np.float64)
    x = x / (np.abs(x).max() + 1e-9) * pk
    n = int(0.02 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def _rain(dur):
    rng = np.random.default_rng(3)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = _bp(rng.standard_normal(n), 1500, 9000) * 0.6 + _lp(rng.standard_normal(n), 500) * 0.5
    drops = np.zeros(n)
    for i in rng.integers(0, n - 400, int(dur * 40)):
        drops[i:i + 300] += np.exp(-np.arange(300) / 40) * rng.uniform(0.3, 1)
    x += _bp(drops * rng.standard_normal(n), 2000, 8000)
    return _norm(x * np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.6), 0.6)


def _screech(dur):
    rng = np.random.default_rng(6)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 1150 + 90 * np.sin(2 * np.pi * 5.5 * tt) + 40 * rng.standard_normal(n).cumsum() / np.sqrt(SR) / 3
    ph = np.cumsum(f) / SR
    x = np.sin(2 * np.pi * ph) + 0.5 * np.sin(2 * np.pi * 2 * ph) + 0.25 * np.sin(2 * np.pi * 3.1 * ph)
    x = x * (0.7 + 0.3 * _lp(rng.standard_normal(n), 30) * 3) + 0.6 * _bp(rng.standard_normal(n), 800, 4000)
    env = np.minimum(1, tt / 0.08) * np.minimum(1, (dur - tt) / 0.5)
    return _norm(np.tanh(1.5 * x) * env, 0.7)


def _abs_buzz(dur, rate=15.0):
    rng = np.random.default_rng(12)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    motor = sum(np.sin(2 * np.pi * f * tt) / (i + 1) for i, f in enumerate((180, 360, 540, 900)))
    clicks = np.zeros(n)
    for tc in np.arange(0.05, dur, 1 / rate):
        i = int(tc * SR)
        m = min(n - i, 900)
        clicks[i:i + m] += np.exp(-np.arange(m) / 120)
    x = 0.4 * motor + 1.2 * _bp(clicks * rng.standard_normal(n), 300, 3000) + 0.6 * _lp(clicks, 200)
    env = np.minimum(1, tt / 0.1) * np.minimum(1, (dur - tt) / 0.4)
    return _norm(x * env, 0.75)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    clips = {"rain": _rain(max(2.0, T_PARTS + 0.5)), "tyre_screech": _screech(max(1.5, T_PARTS - T_STOMP - 0.2)),
             "abs_buzz": _abs_buzz(max(2.0, T_HIST - T_BUZZ + 0.2)),
             "abs_pump": _abs_buzz(max(2.0, T_BUZZ - T_PUMPW), rate=1 / CYC)}
    for name, x in clips.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_TURNING
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(0.0, "rain", 0.35), (T_PUMPH, "tick", 0.3), (T_PUMPH + 0.5, "tick", 0.3), (T_PUMPH + 1.0, "tick", 0.3),
           (T_HOOK_OUT - 0.1, "whoosh_big", 0.45), (T_ANTI, "whoosh_up", 0.3), (T_STOMP, "clunk", 0.45),
           (T_STOMP + 0.1, "tyre_screech", 0.5), (T_LOCKUP - 0.05, "impact", 0.4),
           (T_PARTS - 0.05, "whoosh_down", 0.35), (T_TOOTHED, "tick", 0.3), (T_SENSOR, "tick", 0.3),
           (T_COMPUTER, "whoosh_up", 0.3), (T_LOCKW - 0.1, "impact", 0.35), (T_VALVE - 0.05, "whoosh_down", 0.3),
           (T_CLOSES, "clunk", 0.45), (T_OPENS, "hiss", 0.35), (T_RE, "whoosh_big", 0.35),
           (T_TURNING, "impact", 0.45), (T_SLIDING, "tyre_screech", 0.25), (T_NOTHING - 0.1, "impact", 0.4),
           (T_PUMPW, "abs_pump", 0.35), (T_BUZZ - 0.05, "abs_buzz", 0.5), (T_HIST - 0.05, "whoosh_up", 0.3),
           (T_NINETEEN + 0.6, "impact", 0.35), (T_DRIVE - 0.05, "whoosh_down", 0.3), (T_PRESS, "abs_buzz", 0.3),
           (T_STEER, "whoosh_up", 0.3)]
    return {"build": (T_RE, T_TURNING), "drop": (T_TURNING, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
