"""Keyless entry visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes (one overhead driveway map, tilted 3/4 from above; the camera pans/zooms per beat)
  DRIVEWAY (hook)    night driveway: a figure walks up with the key in a pocket -> door unlocks; the key on the roof
                     instead -> nothing; "it can't see it" -> HOW? (open loop)
  XRAY     (what)    the car turns see-through: five antenna points blink.
  RANGE    (problem) zoom out: the key button's ~100 m ring covers the whole lot -> who's at the door?
  BUBBLES  (parts)   zoom back in: door, bumper, cabin antennas light as named; low-frequency bubbles on the
                     ground, 125 kHz readout, 1-2 m dimension.
  HANDSHAKE(how)     figure grabs the handle -> wake-up rings -> CHALLENGE packet to the key -> the key scrambles
                     it (secret code) -> ANSWER packet back on the long-range (UHF) radio.
  REHOOK   (rehook)  two ghost keys, one just outside the window, one on the seat: both in the door bubble.
  STRENGTH (key)     live signal-strength bars (door / cabin / bumper) computed from the key's position; the key
                     moves in (cabin loud -> INSIDE) and out (door only -> OUTSIDE). Payoff of the hook.
  RELAY    (relay)   zoom out to the house: relay box at the car, relay box at the house wall, the door bubble is
                     re-created in the hallway around the key -> UNLOCKED. 10 models / 50 m chips.
  FIX      (fix)     the key falls asleep (Zzz) -> link dead; time-of-flight pulse -> RELAY SPOTTED, LOCKED.
  OUTRO    (outro)   the hook shot again, now understood.

Model: field strength of antenna i at the key = (1 - d / R_i) ** 0.7 (illustrative: LF near-field falls off fast;
real cars calibrate thresholds per antenna). Inside = a cabin antenna is heard. Geometry in metres, not to scale
in the relay beat (noted on screen).
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import flow

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_POCKET = F("hook", "pocket,")
T_ROOF = F("hook", "roof.")
T_CANT = F("hook", "can't")
T_KNOW = F("hook", "know?")
T_WHAT = L("what")["start"]
T_KEYLESS0 = F("what", "keyless")
T_PROB = L("problem")["start"]
T_BUTTON = F("problem", "button")
T_HUNDRED = F("problem", "hundred")
T_FAR = F("problem", "far")
T_DOOR0 = F("problem", "door.")
T_PARTS = L("parts")["start"]
T_SECOND = F("parts", "second")
T_HANDLES = F("parts", "handles,")
T_BUMPER = F("parts", "bumper")
T_CABIN = F("parts", "cabin")
T_WEAK = F("parts", "weak,")
T_KHZ = F("parts", "kilohertz,")
T_METER = F("parts", "meter")
T_HOW = L("how")["start"]
T_GRAB = F("how", "grab")
T_WAKE = F("how", "wake")
T_CHAL = F("how", "challenge.")
T_SCRAM = F("how", "scrambles")
T_SECRET = F("how", "secret")
T_ANSWERS = F("how", "answers")
T_LONG = F("how", "long")
T_RE = L("rehook")["start"]
T_INSIDE = F("rehook", "inside")
T_OUTSIDE = F("rehook", "outside?")
T_KEY = L("key")["start"]
T_MEASURES = F("key", "measures")
T_REPORTS = F("key", "reports")
T_LOUD = F("key", "loud", nth=1)
T_CABIN2 = F("key", "cabin?")
T_IN = F("key", "in.")
T_ONLY = F("key", "only")
T_OUT = F("key", "out.")
T_RELAY = L("relay")["start"]
T_WEAKSPOT = F("relay", "weak")
T_BOXES = F("relay", "boxes")
T_STRETCH = F("relay", "stretch")
T_HALLWAY = F("relay", "hallway.")
T_TEN = F("relay", "ten")
T_FIFTY = F("relay", "fifty")
T_FIX = L("fix")["start"]
T_SLEEP = F("fix", "sleep")
T_MOVING = F("fix", "moving,")
T_TIME = F("fix", "time")
T_LIGHT = F("fix", "light")
T_GIVES = F("fix", "gives")
T_OUTRO = L("outro")["start"]
T_NEVER = F("outro", "never")
T_LISTENS = F("outro", "listens")


# ================================================================== camera + projection
KY, KZ = 0.62, 0.62          # ground foreshortening, height scale (3/4 view from above)
OX, OY = 500.0, 1050.0       # screen point the camera looks at

CAR = (-0.2, -0.55, 168.0)
CAR_TIGHT = (-0.2, -0.75, 178.0)
WIDE = (0.0, 6.0, 3.3)
HOUSE_VIEW = (-5.0, 2.0, 56.0)


def cam(t):
    keys = [
        (0.0, (-0.6, -0.9, 150.0)),
        (T_PROB - 0.2, CAR),
        (T_BUTTON + 0.1, CAR),
        (T_HUNDRED + 0.5, WIDE),
        (T_DOOR0 - 0.3, WIDE),
        (T_PARTS + 0.4, CAR),
        (T_GRAB - 0.3, CAR),
        (T_GRAB + 0.4, CAR_TIGHT),
        (T_RELAY - 0.1, CAR_TIGHT),
        (T_RELAY + 0.9, HOUSE_VIEW),
        (T_OUTRO - 0.2, HOUSE_VIEW),
        (T_OUTRO + 0.7, CAR),
    ]
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease(lin(t, t0, t1))
            # zoom in log space so big zooms feel even
            s = math.exp(math.log(v0[2]) + (math.log(v1[2]) - math.log(v0[2])) * u)
            return (v0[0] + (v1[0] - v0[0]) * u, v0[1] + (v1[1] - v0[1]) * u, s)
    return keys[-1][1]


class View:
    def __init__(self, t):
        self.cx, self.cy, self.s = cam(t)

    def __call__(self, x, y, z=0.0):
        x, y, z = (np.asarray(v, float) for v in (x, y, z))
        sx = OX + self.s * (x - self.cx)
        sy = OY - self.s * ((y - self.cy) * KY + z * KZ)
        return np.stack(np.broadcast_arrays(sx, sy), -1)


def ground_ellipse(V, x, y, r):
    c = V(x, y)
    return skia.Rect.MakeXYWH(c[0] - r * V.s, c[1] - r * V.s * KY, 2 * r * V.s, 2 * r * V.s * KY)


# ================================================================== prisms (tapered, convex footprints)
def prism(cv, V, bot, top, z0, z1, side_c, top_c, a=1.0, side_cs=None, edge=None):
    """Footprint `bot` at height z0 and `top` at z1 (same vertex count, CCW in world x/y). Draws the faces that
    face the camera (outward normal with a -y component or upward) then the top."""
    bot, top = np.asarray(bot, float), np.asarray(top, float)
    n = len(bot)
    B = V(bot[:, 0], bot[:, 1], z0)
    T = V(top[:, 0], top[:, 1], z1)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        q = np.array([B[i], B[j], T[j], T[i]])
        area = np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
        if area < -1e-6:      # CCW world footprint -> screen (y flipped) clockwise == facing camera
            ex, ey = bot[j] - bot[i]
            nx, ny = ey, -ex
            lam = clamp(0.55 + 0.45 * (-ny / (math.hypot(nx, ny) + 1e-9)) * 0.6 - 0.25 * nx / (math.hypot(nx, ny) + 1e-9))
            c = side_cs[i] if side_cs is not None else side_c
            faces.append((q, shade(c, 0.55 + 0.6 * lam)))
    for q, c in faces:
        cv.drawPath(poly_path(q), paint(c, a=a))
        cv.drawPath(poly_path(q), paint(shade(c, 0.45), a=a, stroke=1.4))
    cv.drawPath(poly_path(T), paint(top_c, a=a))
    if edge is not None:
        cv.drawPath(poly_path(T), paint(edge, a=a, stroke=1.6))
    return B, T


def rrect_fp(x0, x1, y0, y1, c):
    """Chamfered rectangle footprint, CCW."""
    return np.array([(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1),
                     (x0, y1 - c), (x0, y0 + c)])


# ================================================================== the car (front = -x, driver side = near, -y)
CAR_BODY = (rrect_fp(-2.3, 2.3, -0.92, 0.92, 0.32), rrect_fp(-2.22, 2.25, -0.86, 0.86, 0.30))
CAB_BOT = np.array([(-1.0, -0.84), (1.3, -0.84), (1.3, 0.84), (-1.0, 0.84)])
CAB_TOP = np.array([(-0.35, -0.66), (0.95, -0.66), (0.95, 0.66), (-0.35, 0.66)])
C_BODY = hx("#2f6fb0")
C_GLASS = hx("#14243c")

# antennas: name, (x, y), LF reach R (m)
ANT = {
    "door":   ((-0.35, -0.95), 1.7),
    "door_r": ((-0.35, 0.95), 1.7),
    "bumper": ((2.32, 0.0), 1.6),
    "cab_f":  ((-0.55, 0.0), 1.15),
    "cab_r":  ((0.75, 0.0), 1.15),
}
ANT_Z = {"door": 0.8, "door_r": 0.8, "bumper": 0.5, "cab_f": 0.6, "cab_r": 0.6}


def strength(name, p):
    (ax, ay), R = ANT[name]
    d = math.hypot(p[0] - ax, p[1] - ay)
    return clamp(1 - d / R) ** 0.7


def draw_car(cv, t, V, xray=0.0, unlock=0.0, a=1.0):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    # shadow
    cv.drawOval(ground_ellipse(V, 0, 0, 2.5), paint(hx("#000000"), a=0.55, blur=0.25 * V.s))
    # near wheels (far ones hidden under the body)
    for wx in (-1.45, 1.45):
        c = V(wx, -0.82, 0.34)
        r = 0.34 * V.s
        cv.drawOval(skia.Rect.MakeXYWH(c[0] - r, c[1] - r * KZ, 2 * r, 2 * r * KZ), paint(hx("#0d0f14")))
        cv.drawOval(skia.Rect.MakeXYWH(c[0] - r * 0.5, c[1] - r * 0.5 * KZ, r, r * KZ), paint(hx("#3b4352")))
    ba = 1 - 0.68 * xray
    cv.saveLayerAlpha(None, int(255 * ba))
    prism(cv, V, CAR_BODY[0], CAR_BODY[1], 0.22, 0.95, C_BODY, shade(C_BODY, 1.12), edge=shade(C_BODY, 1.5))
    # cabin: front slope (windshield) + sides are glass, roof is body colour
    side_cs = [C_GLASS, C_GLASS, C_GLASS, C_GLASS]
    prism(cv, V, CAB_BOT, CAB_TOP, 0.95, 1.45, C_GLASS, shade(C_BODY, 1.05), side_cs=side_cs,
          edge=shade(C_BODY, 1.4))
    # windshield (front slope, seen from above) drawn explicitly
    ws = np.vstack([V([-1.0, -1.0], [-0.84, 0.84], [0.95, 0.95]), V([-0.35, -0.35], [0.66, -0.66], [1.45, 1.45])])
    cv.drawPath(poly_path(ws), paint(mix(C_GLASS, hx("#3c5a80"), 0.35)))
    rw = np.vstack([V([1.3, 1.3], [-0.84, 0.84], [0.95, 0.95]), V([0.95, 0.95], [0.66, -0.66], [1.45, 1.45])])
    cv.drawPath(poly_path(rw), paint(mix(C_GLASS, hx("#3c5a80"), 0.25)))
    # beltline highlight + window sheen + wheel arches (near side)
    p = V([-2.1, 2.1], [-0.92, -0.92], [0.9, 0.9])
    cv.drawLine(*p[0], *p[1], paint(shade(C_BODY, 1.6), a=0.7, stroke=2.5))
    for x0 in (-0.85, 0.45):
        p = V([x0, x0 + 0.35], [-0.8, -0.72], [1.0, 1.4])
        cv.drawLine(*p[0], *p[1], paint(hx("#9fc2e6"), a=0.35, stroke=0.05 * V.s))
    for wx in (-1.45, 1.45):
        c = V(wx, -0.93, 0.34)
        r = 0.44 * V.s
        arch = skia.Rect.MakeXYWH(c[0] - r, c[1] - r * KZ, 2 * r, 2 * r * KZ)
        cv.drawArc(arch, 180, 180, False, paint(shade(C_BODY, 0.45), stroke=0.06 * V.s))
    # B-pillar on the near side
    p = V([0.25, 0.25], [-0.84, -0.66], [0.95, 1.45])
    cv.drawLine(*p[0], *p[1], paint(shade(C_BODY, 0.9), stroke=0.08 * V.s))
    # door seam + handle (near side)
    p = V([0.25, 0.25], [-0.92, -0.92], [0.3, 0.95])
    cv.drawLine(*p[0], *p[1], paint(shade(C_BODY, 0.5), stroke=2))
    h = V(-0.35, -0.95, 0.8)
    hw = 0.22 * V.s
    cv.drawRoundRect(skia.Rect.MakeXYWH(h[0] - hw / 2, h[1] - 0.035 * V.s, hw, 0.07 * V.s), 4, 4,
                     paint(hx("#c9d2e0")))
    cv.restore()
    # head / tail lights
    for y in (-0.6, 0.6):
        q = V(-2.3, y, 0.7)
        look.bloom(cv, q[0], q[1], 0.05 * V.s, hx("#fff4d6"), a=0.25 + 0.7 * unlock)
        q = V(2.3, y, 0.72)
        look.bloom(cv, q[0], q[1], 0.04 * V.s, AMBER if unlock > 0 else RED, a=0.35 + 0.6 * unlock)
    # x-ray interior: seats + antennas
    if xray > 0:
        for sx in (-0.45, 0.6):
            for sy in (-0.42, 0.42):
                seat = np.array([(sx - 0.25, sy - 0.22), (sx + 0.25, sy - 0.22), (sx + 0.25, sy + 0.22),
                                 (sx - 0.25, sy + 0.22)])
                prism(cv, V, seat, seat, 0.35, 0.55, hx("#3a4250"), hx("#4b5566"), a=0.85 * xray)
    cv.restore()


def draw_antennas(cv, t, V, lit, a=1.0):
    """lit: {name: 0..1}. Small glowing chips at each antenna."""
    if a <= 0:
        return
    for name, ((x, y), R) in ANT.items():
        k = lit.get(name, 0.0)
        q = V(x, y, ANT_Z[name])
        cv.drawCircle(q[0], q[1], 0.06 * V.s + 4, paint(hx("#0b111c"), a=0.9 * a))
        cv.drawCircle(q[0], q[1], 0.06 * V.s + 4, paint(mix(STEEL_D, AMBER, k), a=a, stroke=2.5))
        if k > 0:
            cv.drawCircle(q[0], q[1], 0.05 * V.s, paint(AMBER, a=a * k))
            cv.drawCircle(q[0], q[1], 0.16 * V.s, paint(AMBER, a=0.4 * a * k, blur=0.08 * V.s))


def draw_bubble(cv, t, V, name, k, c=AMBER, R=None, center=None, pulse=True):
    if k <= 0:
        return
    (x, y), R0 = ANT[name] if name else (center, R)
    R = R if R is not None else R0
    if center is not None:
        x, y = center
    rect = ground_ellipse(V, x, y, R * eout(k))
    gp = skia.Paint(AntiAlias=True)
    cxy = V(x, y)
    gp.setShader(skia.GradientShader.MakeRadial(skia.Point(*cxy), R * V.s,
                                                [col(c, 0.0), col(c, 0.10 * k), col(c, 0.28 * k)], [0.0, 0.75, 1.0]))
    cv.save()
    cv.translate(cxy[0], cxy[1])
    cv.scale(1.0, KY)
    cv.translate(-cxy[0], -cxy[1])
    rr = R * eout(k) * V.s
    cv.drawCircle(cxy[0], cxy[1], rr, gp)
    cv.drawCircle(cxy[0], cxy[1], rr, paint(c, a=0.75 * k, stroke=2.5 / 1.0))
    if pulse:
        ph = (t * 0.9) % 1.0
        cv.drawCircle(cxy[0], cxy[1], rr * ph, paint(c, a=0.45 * k * (1 - ph), stroke=2.0))
    cv.restore()
    del rect


# ================================================================== people, keys, house
def draw_figure(cv, V, x, y, a=1.0, key=0.0, reach=0.0):
    """Generic standing figure (no face): capsule body + head. key>0: key fob shown at the pocket."""
    if a <= 0:
        return None
    cv.drawOval(ground_ellipse(V, x, y, 0.3), paint(hx("#000000"), a=0.5 * a, blur=0.06 * V.s))
    b0, b1 = V(x, y, 0.0), V(x, y, 1.42)
    w = 0.42 * V.s
    body = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(b0[0] - w / 2, b1[1], b0[0] + w / 2, b0[1]), w / 2, w / 2)
    cv.drawRRect(body, paint(hx("#5d6b80"), a=a))
    cv.drawRRect(body, paint(hx("#93a3ba"), a=a, stroke=2))
    hd = V(x, y, 1.66)
    cv.drawCircle(hd[0], hd[1], 0.13 * V.s, paint(hx("#93a3ba"), a=a))
    if reach > 0:   # arm toward the door handle (+y = toward the car)
        s0 = V(x + 0.12, y, 1.15)
        s1 = V(x + 0.05, y + 0.62 * reach, 0.85)
        cv.drawLine(*s0, *s1, paint(hx("#93a3ba"), a=a, stroke=0.1 * V.s, cap=skia.Paint.kRound_Cap))
    pk = V(x + 0.14, y - 0.12, 0.85)
    return pk


def draw_fob(cv, x, y, s, a=1.0, glow=0.0, asleep=0.0, tint=None):
    if a <= 0:
        return
    if glow > 0:
        cv.drawCircle(x, y, 1.4 * s, paint(AMBER, a=0.45 * glow * a, blur=0.6 * s))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 0.45 * s, y - 0.7 * s, 0.9 * s, 1.4 * s), 0.38 * s, 0.38 * s)
    cv.drawRRect(rr, paint(hx("#1a1f2a"), a=a))
    cv.drawRRect(rr, paint(tint or mix(hx("#c9d2e0"), AMBER, glow), a=a, stroke=max(2.0, 0.09 * s)))
    for dy in (-0.28, 0.08):
        cv.drawCircle(x, y + dy * s, 0.17 * s, paint(hx("#4b5566"), a=a))
    cv.drawCircle(x, y + 0.42 * s, 0.07 * s, paint(mix(hx("#3a4252"), AMBER, max(glow, 0.0)), a=a))
    if asleep > 0:
        for i, (dx, dy, sz) in enumerate(((0.7, -0.9, 0.5), (1.1, -1.4, 0.65), (1.55, -2.0, 0.8))):
            draw_text(cv, "z", x + dx * s, y + dy * s, font("pop_b", max(10, sz * s)), CYAN,
                      a=a * asleep * clamp(asleep * 3 - i))


def draw_house(cv, t, V, a=1.0, key_glow=0.0):
    """Floor-plan house to the upper left (walls drawn low so the hallway is visible)."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    fp = np.array([(-12.5, 4.5), (-5.5, 4.5), (-5.5, 10.5), (-12.5, 10.5)])
    q = V(fp[:, 0], fp[:, 1])
    cv.drawPath(poly_path(q), paint(hx("#0e1520"), a=0.95))
    walls = [((-12.5, 4.5), (-8.0, 4.5)), ((-6.9, 4.5), (-5.5, 4.5)), ((-5.5, 4.5), (-5.5, 10.5)),
             ((-5.5, 10.5), (-12.5, 10.5)), ((-12.5, 10.5), (-12.5, 4.5)), ((-9.6, 4.5), (-9.6, 10.5)),
             ((-9.6, 7.8), (-5.5, 7.8))]
    for (x0, y0), (x1, y1) in walls:
        poly = np.vstack([V([x0, x1], [y0, y1], [0, 0]), V([x1, x0], [y1, y0], [0.9, 0.9])])
        cv.drawPath(poly_path(poly), paint(hx("#2a3446")))
        p = V([x0, x1], [y0, y1], [0.9, 0.9])
        cv.drawLine(*p[0], *p[1], paint(hx("#8d97ab"), stroke=2.5))
    # hall table + key
    tb = np.array([(-9.4, 5.8), (-8.2, 5.8), (-8.2, 6.6), (-9.4, 6.6)])
    prism(cv, V, tb, tb, 0.0, 0.8, hx("#5a4632"), hx("#7a6045"))
    c = V(-8.8, 6.2, 0.8)
    draw_text(cv, "HOUSE", *V(-12.2, 10.0, 0.9), font("inter_xb", 24), MUTED, tracking=3)
    cv.restore()
    return c


def packet(cv, p0, p1, u, text, c, a=1.0):
    if a <= 0 or u <= 0 or u >= 1:
        return
    p = np.asarray(p0) + (np.asarray(p1) - np.asarray(p0)) * ease(u)
    pill(cv, p[0], p[1], text, font("inter_xb", 26), INK, border=c, a=a, align="center", tracking=2, dot=c)


def dashed(cv, p0, p1, c, a=1.0, w=4, on=14, off=10, phase=0.0):
    pt = paint(c, a=a, stroke=w, cap=skia.Paint.kRound_Cap)
    pt.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    cv.drawLine(p0[0], p0[1], p1[0], p1[1], pt)


HEX0 = "7F 3A 91 C2"
HEX1 = "C4 1E 08 9B"


def scramble(t, t0, t1):
    u = lin(t, t0, t1)
    if u <= 0:
        return HEX0
    if u >= 1:
        return HEX1
    rng = np.random.default_rng(int(t * 24))
    chars = "0123456789ABCDEF"
    out = []
    for i, ch in enumerate(HEX1):
        if ch == " ":
            out.append(" ")
        elif i / len(HEX1) < u:
            out.append(ch)
        else:
            out.append(chars[rng.integers(16)])
    return "".join(out)


# ================================================================== where things are, per beat
DOOR_OUT = (-0.35, -1.55)     # standing at the driver door
SEAT = (-0.45, -0.42)         # driver seat
WALK0 = (-3.0, -2.5)


def person_pos(t):
    if t < T_ROOF - 0.3:
        u = ease(lin(t, 0.0, T_POCKET + 0.2))
        return (WALK0[0] + (DOOR_OUT[0] - WALK0[0]) * u, WALK0[1] + (DOOR_OUT[1] - WALK0[1]) * u)
    if T_HOW - 0.3 <= t < T_RE:
        u = ease(lin(t, T_HOW - 0.3, T_GRAB - 0.1))
        return (WALK0[0] + (DOOR_OUT[0] - WALK0[0]) * u, WALK0[1] + (DOOR_OUT[1] - WALK0[1]) * u)
    if t >= T_OUTRO:
        u = ease(lin(t, T_OUTRO, T_NEVER + 0.3))
        return (WALK0[0] + (DOOR_OUT[0] - WALK0[0]) * u, WALK0[1] + (DOOR_OUT[1] - WALK0[1]) * u)
    return None


def person_a(t):
    return (win(t, -1, T_ROOF - 0.1, 0.01, 0.3) + win(t, T_HOW - 0.4, T_RE + 0.1, 0.3, 0.3)
            + win(t, T_OUTRO - 0.1, T_TOTAL + 1, 0.3, 0.01))


def key_world(t):
    """The key's position during the strength beat (outside -> inside -> outside)."""
    u_in = ease(lin(t, T_LOUD - 0.5, T_CABIN2 + 0.1))
    u_out = ease(lin(t, T_ONLY - 0.35, T_ONLY + 0.35))
    p_out = np.array(DOOR_OUT) + np.array([0.0, 0.1])
    p_in = np.array(SEAT)
    p = p_out + (p_in - p_out) * u_in
    p = p + (p_out - p) * u_out
    return p


def scene_k(t, t0, t1, fin=0.3, fout=0.3):
    return win(t, t0, t1, fin, fout)


# ================================================================== drawing blocks
def draw_ground(cv, t, V):
    # lawn, driveway, kerb lines (subtle, lets the blueprint grid through)
    lawn = np.array([(-40, -30), (40, -30), (40, 40), (-40, 40)])
    cv.drawPath(poly_path(V(lawn[:, 0], lawn[:, 1])), paint(hx("#06100c"), a=0.55))
    dw = np.array([(-5.0, -4.5), (5.5, -4.5), (5.5, 3.2), (-5.0, 3.2)])
    cv.drawPath(poly_path(V(dw[:, 0], dw[:, 1])), paint(hx("#1a1f28"), a=0.85))
    for y in (-4.5, 3.2):
        p = V([-5.0, 5.5], [y, y])
        cv.drawLine(*p[0], *p[1], paint(hx("#3a4252"), a=0.8, stroke=3))
    # path to the house
    pth = np.array([(-5.0, 1.0), (-5.0, 2.4), (-7.0, 4.5), (-8.0, 4.5)])
    cv.drawPath(poly_path(V(pth[:, 0], pth[:, 1])), paint(hx("#1a1f28"), a=0.85))


def draw_range(cv, t, V):
    """Problem beat: the key button's ~100 m ring."""
    k = scene_k(t, T_BUTTON - 0.1, T_PARTS + 0.2, 0.3, 0.4)
    if k <= 0:
        return
    g = eout(lin(t, T_BUTTON + 0.1, T_HUNDRED + 0.8))
    c = V(0, 0)
    R = 100 * g * V.s
    cv.save()
    cv.translate(*c)
    cv.scale(1, KY)
    cv.drawCircle(0, 0, R, paint(YEL, a=0.10 * k))
    cv.drawCircle(0, 0, R, paint(YEL, a=0.9 * k, stroke=4))
    for j in range(3):
        ph = ((t - T_BUTTON) * 0.7 + j / 3) % 1.0
        cv.drawCircle(0, 0, R * ph, paint(YEL, a=0.35 * k * (1 - ph), stroke=3))
    cv.restore()
    # other people around the lot
    rng = np.random.default_rng(4)
    pk = k * eout(lin(t, T_FAR - 0.4, T_FAR + 0.3))
    for i in range(14):
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(15, 92)
        q = V(r * math.cos(ang), r * math.sin(ang))
        cv.drawCircle(q[0], q[1], 9, paint(hx("#93a3ba"), a=pk))
        draw_text(cv, "?", q[0], q[1] - 16, font("pop_b", 30), YEL, a=pk, align="center")
    # scale callout
    if g > 0.2:
        e = V(100 * g, 0)
        cv.drawLine(c[0], c[1], e[0], e[1], paint(YEL, a=k, stroke=3))
        pill(cv, (c[0] + e[0]) / 2, c[1] + 40, "≈ 100 m", font("inter_xb", 30), INK, border=YEL, a=k * g,
             align="center", tracking=2)


def draw_parts_labels(cv, t, V):
    k_end = T_HOW + 0.2
    q = V(*ANT["door"][0], ANT_Z["door"])
    brand.label(cv, t, "DOOR HANDLE", tuple(q), (110, 1290), AMBER, T_HANDLES - 0.15, k_end)
    q = V(*ANT["bumper"][0], ANT_Z["bumper"])
    brand.label(cv, t, "BUMPER", tuple(q), (900, 1290), AMBER, T_BUMPER - 0.15, k_end, align="right")
    q = V(*ANT["cab_f"][0], ANT_Z["cab_f"])
    brand.label(cv, t, "CABIN", tuple(q), (300, 720), AMBER, T_CABIN - 0.15, k_end)
    # 1-2 m dimension from the door antenna
    dk = scene_k(t, T_METER - 0.2, T_HOW + 0.2, 0.3, 0.3)
    if dk > 0:
        (x, y), R = ANT["door"]
        p0 = V(x, y)
        p1 = V(x - R, y)
        cv.drawLine(*p0, *p1, paint(YEL, a=dk, stroke=4))
        for p in (p0, p1):
            cv.drawLine(p[0], p[1] - 14, p[0], p[1] + 14, paint(YEL, a=dk, stroke=4))
        pill(cv, (p0[0] + p1[0]) / 2, p0[1] + 46, "1–2 m", font("inter_xb", 30), INK, border=YEL, a=dk,
             align="center", tracking=2)
    rk = scene_k(t, T_KHZ - 0.6, T_HOW + 0.1, 0.3, 0.3)
    brand.readout(cv, rk, "125 kHz", "LOW FREQUENCY · SHORT RANGE")


def draw_handshake(cv, t, V, pk):
    """How beat: wake-up rings, challenge to the key, scramble, answer back."""
    k = scene_k(t, T_GRAB - 0.2, T_RE + 0.15, 0.25, 0.3)
    if k <= 0 or pk is None:
        return
    door = V(*ANT["door"][0], ANT_Z["door"])
    # touch ring on the handle
    tk = win(t, T_GRAB - 0.05, T_GRAB + 0.9, 0.1, 0.4)
    if tk > 0:
        ph = lin(t, T_GRAB, T_GRAB + 0.7)
        cv.drawCircle(door[0], door[1], 20 + 50 * ph, paint(INK, a=tk * (1 - ph), stroke=4))
        pill(cv, door[0] - 20, door[1] - 120, "HANDLE TOUCHED", font("inter_xb", 26), INK, border=INK, a=tk,
             align="center", tracking=2)
    # wake-up rings from the door antenna
    wk = scene_k(t, T_WAKE - 0.1, T_SCRAM, 0.2, 0.3)
    if wk > 0:
        for j in range(3):
            ph = ((t - T_WAKE) * 1.4 + j / 3) % 1.0
            cv.save()
            cv.translate(*door)
            cv.scale(1, KY)
            cv.drawCircle(0, 0, ph * ANT["door"][1] * V.s, paint(AMBER, a=0.8 * wk * (1 - ph), stroke=4))
            cv.restore()
    # challenge packet -> key
    u = lin(t, T_CHAL - 0.2, T_CHAL + 0.6)
    packet(cv, door + np.array([0, -40]), pk + np.array([-60, -60]), u, "CHALLENGE", AMBER, a=k)
    # key panel (close-up of the fob, top area)
    fk = scene_k(t, T_CHAL + 0.4, T_RE + 0.15, 0.25, 0.3)
    if fk > 0:
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(90, 480, 910, 700), 26, 26)
        cv.drawRRect(rr, paint(hx("#0b111c"), a=0.92 * fk))
        cv.drawRRect(rr, paint(AMBER, a=0.7 * fk, stroke=2.5))
        glow = win(t, T_CHAL + 0.4, T_ANSWERS + 0.8, 0.2, 0.4)
        draw_fob(cv, 175, 590, 70, a=fk, glow=glow)
        draw_text(cv, "THE KEY", 270, 535, font("inter_xb", 24), MUTED, a=fk, tracking=3)
        sc = scramble(t, T_SCRAM - 0.05, T_SECRET + 0.5)
        done = lin(t, T_SECRET + 0.45, T_SECRET + 0.5)
        draw_text(cv, sc, 270, 610, font("inter_blk", 58), mix(AMBER, YEL, done), a=fk, tracking=6)
        st = "SCRAMBLED WITH THE SECRET CODE" if t > T_SECRET - 0.1 else "CHALLENGE RECEIVED"
        draw_text(cv, st, 270, 662, font("inter_sb", 24), INK, a=fk, tracking=2)
    # answer back on the long-range radio
    ak = scene_k(t, T_ANSWERS - 0.1, T_RE + 0.15, 0.2, 0.3)
    if ak > 0:
        dashed(cv, pk, door, YEL, a=ak, w=4, phase=-(t * 80) % 24)
        u = lin(t, T_ANSWERS - 0.05, T_ANSWERS + 0.7)
        packet(cv, pk + np.array([60, 30]), door + np.array([80, 40]), u, "ANSWER", YEL, a=ak)
        lk = scene_k(t, T_LONG - 0.1, T_RE + 0.15, 0.2, 0.3)
        if lk > 0:
            pill(cv, 500, 1300, "LONG-RANGE RADIO · 315 / 433 MHz", font("inter_xb", 26), INK, border=YEL,
                 a=lk, align="center", tracking=2, dot=YEL)


def draw_ghosts(cv, t, V):
    k = scene_k(t, T_RE - 0.1, T_MEASURES + 0.2, 0.25, 0.3)
    if k <= 0:
        return
    po = V(DOOR_OUT[0], DOOR_OUT[1] + 0.1, 0.9)
    pi = V(SEAT[0], SEAT[1], 0.7)
    s = 0.17 * V.s
    ko = k * eback(lin(t, T_OUTSIDE - 0.3, T_OUTSIDE + 0.1))
    ki = k * eback(lin(t, T_INSIDE - 0.2, T_INSIDE + 0.2))
    draw_fob(cv, pi[0], pi[1], s, a=clamp(ki), glow=0.5)
    draw_fob(cv, po[0], po[1], s, a=clamp(ko), glow=0.5)
    pill(cv, pi[0] + 50, pi[1] - 90, "INSIDE?", font("inter_xb", 28), INK, border=GREEN, a=clamp(ki),
         tracking=2)
    pill(cv, po[0] - 40, po[1] + 80, "OUTSIDE?", font("inter_xb", 28), INK, border=CYAN, a=clamp(ko),
         align="center", tracking=2)


BARS = [("DOOR", ("door",)), ("CABIN", ("cab_f", "cab_r")), ("BUMPER", ("bumper",))]


def draw_strength(cv, t, V):
    k = scene_k(t, T_MEASURES - 0.2, T_RELAY + 0.1, 0.3, 0.3)
    if k <= 0:
        return
    p = key_world(t)
    q = V(p[0], p[1], 0.8)
    # lines from each antenna to the key, thickness = strength
    for name in ANT:
        s = strength(name, p)
        if s <= 0.01:
            continue
        a_ = V(*ANT[name][0], ANT_Z[name])
        cv.drawLine(*a_, *q, paint(AMBER, a=k * (0.25 + 0.7 * s), stroke=2 + 9 * s, cap=skia.Paint.kRound_Cap))
    draw_fob(cv, q[0], q[1], 0.17 * V.s, a=k, glow=0.6)
    # bars panel
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(90, 470, 910, 700), 26, 26)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.92 * k))
    cv.drawRRect(rr, paint(AMBER, a=0.6 * k, stroke=2.5))
    draw_text(cv, "WHAT THE KEY HEARS", 120, 518, font("inter_xb", 24), MUTED, a=k, tracking=3)
    for i, (lab, names) in enumerate(BARS):
        y = 562 + i * 50
        s = max(strength(n, p) for n in names)
        draw_text(cv, lab, 120, y + 11, font("inter_xb", 30), INK, a=k, tracking=2)
        x0, x1 = 330, 870
        cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y - 14, x1, y + 14), 14, 14, paint(hx("#263043"), a=k))
        if s > 0.005:
            c = GREEN if lab == "CABIN" else AMBER
            cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y - 14, x0 + (x1 - x0) * s, y + 14), 14, 14, paint(c, a=k))
    # verdict
    inside = max(strength("cab_f", p), strength("cab_r", p)) > 0.15
    brand.stamp(cv, t, "INSIDE", T_IN - 0.05, dur=1.4, center=(500, 770), color=GREEN, bg=hx("#06281a"))
    brand.stamp(cv, t, "OUTSIDE", T_OUT - 0.05, dur=1.4, center=(500, 770), color=CYAN, bg=hx("#05202a"))
    ck = scene_k(t, T_IN + 0.2, T_RELAY + 0.1, 0.2, 0.3)
    if ck > 0:
        txt = "ENGINE START: OK" if inside else "ENGINE START: NO"
        pill(cv, 500, 1300, txt, font("inter_xb", 28), INK, border=GREEN if inside else RED, a=ck, align="center",
             tracking=2, dot=GREEN if inside else RED)


RELAY_A = (-1.6, -2.0)       # box next to the car
RELAY_B = (-7.0, 3.6)        # box outside the house wall
KEY_HOUSE = (-8.8, 6.2)


def draw_relay(cv, t, V):
    k = scene_k(t, T_RELAY + 0.3, T_OUTRO + 0.1, 0.3, 0.4)
    if k <= 0:
        return
    hk = draw_house(cv, t, V, a=1.0)
    sleep = ease(lin(t, T_SLEEP - 0.2, T_SLEEP + 0.4))
    alive = 1 - sleep
    bk = k * eout(lin(t, T_BOXES - 0.3, T_BOXES + 0.2))
    a_ = V(RELAY_A[0], RELAY_A[1], 0.0)
    b_ = V(RELAY_B[0], RELAY_B[1], 0.0)
    # link
    lk = k * ease(lin(t, T_STRETCH - 0.2, T_STRETCH + 0.6))
    if lk > 0:
        pts = np.array([a_ + (b_ - a_) * u for u in np.linspace(0, 1, 30)])
        c = mix(RED, STEEL_D, sleep)
        cv.drawLine(*a_, *b_, paint(c, a=0.5 * lk, stroke=5))
        if alive > 0.05:
            flow(cv, pts, t, 500, 40, RED, r=6, a=lk * alive)
            flow(cv, pts[::-1], t, 500, 40, YEL, r=5, a=lk * alive, offset=20)
    # copied bubble at the house around the key
    hb = lk * eout(lin(t, T_HALLWAY - 0.5, T_HALLWAY + 0.2)) * alive
    draw_bubble(cv, t, V, None, hb, c=RED, R=2.0, center=(RELAY_B[0] - 0.9, RELAY_B[1] + 1.7))
    # key on the hall table
    kq = V(KEY_HOUSE[0], KEY_HOUSE[1], 0.85)
    draw_fob(cv, kq[0], kq[1], 26, a=k, glow=0.8 * hb, asleep=sleep * k)
    if hk is not None:
        pass
    # relay boxes
    for p, lab in ((a_, "RELAY 1"), (b_, "RELAY 2")):
        if bk <= 0:
            continue
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(p[0] - 22, p[1] - 30, 44, 34), 6, 6)
        cv.drawRRect(r, paint(hx("#2a0707"), a=bk))
        cv.drawRRect(r, paint(RED, a=bk, stroke=3))
        cv.drawLine(p[0] + 12, p[1] - 30, p[0] + 18, p[1] - 58, paint(RED, a=bk, stroke=3))
        cv.drawCircle(p[0] + 18, p[1] - 58, 5, paint(RED, a=bk))
        pill(cv, p[0], p[1] + 34, lab, font("inter_xb", 24), INK, border=RED, a=bk, align="center", tracking=2)
    brand.stamp(cv, t, "UNLOCKED", T_HALLWAY + 0.15, dur=1.5, center=(500, 600))
    ck = scene_k(t, T_TEN - 0.15, T_FIX + 0.1, 0.25, 0.3)
    if ck > 0:
        pill(cv, 500, 560, "10 CAR MODELS · 8 MAKERS · 2011 STUDY", font("inter_xb", 27), INK, border=YEL, a=ck,
             align="center", tracking=2, dot=YEL)
    fk = scene_k(t, T_FIFTY - 0.15, T_FIX + 0.1, 0.25, 0.3)
    brand.readout(cv, fk, "50 m", "KEY TO CAR · RELAYED")
    nk = scene_k(t, T_RELAY + 0.8, T_OUTRO, 0.3, 0.3)
    draw_text(cv, "MAP NOT TO SCALE", 900, 1340, font("inter_sb", 20), MUTED, a=0.9 * nk, align="right",
              tracking=2)
    # fix: asleep chip, then time-of-flight
    sk = scene_k(t, T_SLEEP - 0.1, T_TIME, 0.25, 0.3)
    if sk > 0:
        pill(cv, 500, 560, "KEY NOT MOVING → ASLEEP", font("inter_xb", 28), INK, border=CYAN, a=sk,
             align="center", tracking=2, dot=CYAN)
    tk = scene_k(t, T_TIME - 0.1, T_OUTRO + 0.05, 0.25, 0.3)
    if tk > 0:
        ph = ((t - T_TIME) * 0.8) % 1.0
        u = ph * 2 if ph < 0.5 else 2 - ph * 2
        pts = a_ + (b_ - a_) * u
        cv.drawCircle(pts[0], pts[1], 12, paint(CYAN, a=tk))
        cv.drawCircle(pts[0], pts[1], 26, paint(CYAN, a=0.4 * tk, blur=8))
        ns = 333 * eout(lin(t, T_TIME, T_GIVES))
        brand.readout(cv, tk, f"{ns:.0f} ns", "TIME OF FLIGHT · MEASURED")
        pill(cv, 500, 560, "PULSE TIMED AT LIGHT SPEED", font("inter_xb", 28), INK, border=CYAN,
             a=tk * (1 - lin(t, T_GIVES - 0.3, T_GIVES)), align="center", tracking=2, dot=CYAN)
    brand.stamp(cv, t, "RELAY SPOTTED", T_GIVES - 0.05, dur=1.6, center=(500, 600))
    lk2 = scene_k(t, T_GIVES + 0.5, T_OUTRO + 0.05, 0.2, 0.3)
    if lk2 > 0:
        pill(cv, 500, 1300, "DOOR STAYS LOCKED", font("inter_xb", 28), INK, border=GREEN, a=lk2, align="center",
             tracking=2, dot=GREEN)


def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(0, "KEYLESS ENTRY", YEL), (T_PROB, "THE PROBLEM", RED), (T_PARTS, "THE SECOND RADIO", AMBER),
           (T_HOW, "THE HANDSHAKE", AMBER), (T_RE, "THE QUESTION", YEL), (T_KEY, "THE ANSWER", GREEN),
           (T_RELAY, "THE WEAK SPOT", RED), (T_FIX, "THE FIX", CYAN), (T_OUTRO, "KEYLESS ENTRY", RED)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    V = View(t)
    cv.saveLayerAlpha(None, int(255 * clamp(kE)))
    draw_ground(cv, t, V)
    look.vignette(cv, 0.35)
    draw_range(cv, t, V)

    # ----- bubbles on the ground (under the car)
    bub = {}
    b_parts = scene_k(t, T_WEAK - 0.2, T_RELAY + 0.4, 0.4, 0.4)
    for n in ("door", "door_r", "bumper", "cab_f", "cab_r"):
        bub[n] = b_parts
    if T_HOW - 0.2 < t < T_RE:
        for n in ("door_r", "bumper", "cab_f", "cab_r"):
            bub[n] = b_parts * 0.35
    outro_b = scene_k(t, T_NEVER - 0.3, T_TOTAL + 1, 0.4, 0.01)
    hook_b = scene_k(t, T_POCKET - 0.5, T_ROOF + 0.3, 0.3, 0.3)
    bub["door"] = max(bub["door"], outro_b, hook_b * 0.8)
    for n in ("door", "door_r", "bumper", "cab_f", "cab_r"):
        draw_bubble(cv, t, V, n, bub[n])

    # ----- car
    xray = max(scene_k(t, T_KEYLESS0 - 0.3, T_RELAY + 0.6, 0.4, 0.4),
               scene_k(t, T_NEVER - 0.2, T_TOTAL + 1, 0.4, 0.01))
    xray *= 1 - scene_k(t, T_PROB + 0.1, T_PARTS + 0.1, 0.3, 0.3)
    unlock = (win(t, T_POCKET + 0.1, T_POCKET + 1.0, 0.1, 0.4) + win(t, T_ANSWERS + 0.6, T_ANSWERS + 1.6, 0.1, 0.4)
              + win(t, T_HALLWAY + 0.1, T_HALLWAY + 1.1, 0.1, 0.4) + win(t, T_LISTENS, T_LISTENS + 1.0, 0.1, 0.4))
    # driveway figures are drawn before the car only if they stand behind it (they never do: near side)
    draw_car(cv, t, V, xray=xray, unlock=clamp(unlock))
    lit = {}
    al = scene_k(t, T_KEYLESS0 - 0.2, T_RELAY + 0.6, 0.3, 0.3) * (1 - scene_k(t, T_PROB + 0.1, T_PARTS + 0.1))
    blink = 0.5 + 0.5 * math.sin(t * 9)
    for n in ANT:
        lit[n] = al * (blink if t < T_PARTS else 0.0)
    for n, tn in (("door", T_HANDLES), ("door_r", T_HANDLES), ("bumper", T_BUMPER), ("cab_f", T_CABIN),
                  ("cab_r", T_CABIN)):
        if t >= T_PARTS:
            lit[n] = al * eout(lin(t, tn - 0.2, tn + 0.1))
    lit["door"] = max(lit["door"], outro_b, hook_b)
    draw_antennas(cv, t, V, lit, a=max(al, outro_b, hook_b))

    # ----- people + keys
    pp = person_pos(t)
    pk = None
    if pp is not None:
        reach = (eout(lin(t, T_GRAB - 0.3, T_GRAB)) * (1 - lin(t, T_RE - 0.4, T_RE)) if T_HOW < t < T_RE else
                 eout(lin(t, T_POCKET - 0.2, T_POCKET + 0.1)) * (1 - lin(t, T_POCKET + 1.2, T_POCKET + 1.5))
                 if t < T_ROOF else eout(lin(t, T_NEVER, T_NEVER + 0.3)))
        pk = draw_figure(cv, V, pp[0], pp[1], a=clamp(person_a(t)), reach=reach)
        if pk is not None:
            g = max(win(t, T_WAKE, T_ANSWERS + 0.8, 0.2, 0.3), win(t, T_POCKET - 0.4, T_POCKET + 0.8, 0.2, 0.3),
                    outro_b)
            draw_fob(cv, pk[0], pk[1], 0.11 * V.s, a=clamp(person_a(t)), glow=g)
    # hook: key in pocket chip, key on the roof
    k1 = win(t, 0.3, T_ROOF - 0.15, 0.25, 0.25)
    if k1 > 0 and pk is not None:
        pill(cv, max(pk[0], 200), pk[1] + 70, "KEY IN POCKET", font("inter_xb", 26), INK, border=GREEN, a=k1,
             align="center", tracking=2, dot=GREEN)
        uk = win(t, T_POCKET + 0.1, T_ROOF - 0.15, 0.15, 0.2)
        pill(cv, 520, 1300, "UNLOCKED", font("inter_xb", 28), INK, border=GREEN, a=uk, align="center",
             tracking=2, dot=GREEN)
    rk = scene_k(t, T_ROOF - 0.2, T_WHAT + 0.3, 0.25, 0.3)
    if rk > 0:
        drop = eout(lin(t, T_ROOF - 0.25, T_ROOF + 0.2))
        q = V(0.3, -0.2, 1.45 + 0.8 * (1 - drop))
        draw_fob(cv, q[0], q[1], 0.11 * V.s, a=rk)
        pill(cv, q[0] + 60, q[1] - 70, "KEY ON THE ROOF", font("inter_xb", 26), INK, border=RED, a=rk, tracking=2,
             dot=RED)
        pill(cv, 520, 1300, "STILL LOCKED", font("inter_xb", 28), INK, border=RED, a=rk * eout(lin(t, T_ROOF, T_ROOF + 0.3)),
             align="center", tracking=2, dot=RED)
    brand.stamp(cv, t, "IT CAN'T SEE IT", T_CANT - 0.05, dur=1.3, center=(500, 600), color=CYAN, bg=hx("#05202a"))
    brand.stamp(cv, t, "SO HOW?", T_KNOW - 0.1, dur=1.4, center=(500, 600), color=YEL, bg=hx("#2a2405"))

    # ----- beat overlays
    brand.stamp(cv, t, "WHO'S AT THE DOOR?", T_FAR, dur=1.8, center=(500, 600), color=YEL, bg=hx("#2a2405"))
    rk2 = scene_k(t, T_HUNDRED - 0.2, T_PARTS, 0.3, 0.3)
    brand.readout(cv, rk2, "≈ 100 m", "KEY BUTTON RANGE")
    draw_parts_labels(cv, t, V)
    draw_handshake(cv, t, V, pk)
    draw_ghosts(cv, t, V)
    brand.stamp(cv, t, "INSIDE OR OUT?", T_INSIDE - 0.1, dur=1.5, center=(500, 600), color=YEL, bg=hx("#2a2405"))
    draw_strength(cv, t, V)
    draw_relay(cv, t, V)
    # outro chips
    ok = scene_k(t, T_LISTENS - 0.1, T_TOTAL + 1, 0.25, 0.01)
    if ok > 0:
        pill(cv, 520, 1300, "HEARD · INSIDE THE BUBBLE · UNLOCKED", font("inter_xb", 26), INK, border=GREEN, a=ok,
             align="center", tracking=2, dot=GREEN)
    cv.restore()
    draw_header(cv, t)


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


def _chirp():
    """Car unlock: two short horn-ish chirps + lock actuator thunk."""
    tt = np.arange(int(0.42 * SR)) / SR
    x = np.zeros_like(tt)
    for t0 in (0.0, 0.2):
        m = (tt >= t0) & (tt < t0 + 0.09)
        u = tt[m] - t0
        x[m] += (np.sign(np.sin(2 * np.pi * 420 * u)) * 0.5 + np.sin(2 * np.pi * 840 * u)) * np.sin(np.pi * u / 0.09)
    rng = np.random.default_rng(2)
    th = rng.standard_normal(len(tt)) * np.exp(-tt / 0.01) * 0.6
    return _norm(x + th, 0.8)


def _ping():
    """Low-frequency wake-up: soft sine ping with a quick decay."""
    tt = np.arange(int(0.5 * SR)) / SR
    x = np.sin(2 * np.pi * 1250 * tt) * np.exp(-tt / 0.08) + 0.3 * np.sin(2 * np.pi * 2500 * tt) * np.exp(-tt / 0.04)
    return _norm(x, 0.7)


def _data():
    """Digital packet: fast FSK blips."""
    rng = np.random.default_rng(9)
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    bits = rng.integers(0, 2, 40)
    f = np.where(bits[(tt / 0.35 * 40).astype(int).clip(0, 39)] > 0, 2600, 1900)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6
    return _norm(x, 0.55)


def _zap():
    rng = np.random.default_rng(5)
    n = int(0.3 * SR)
    tt = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-tt / 0.03) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 60 * tt)))
    return _norm(x, 0.75)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, x in {"chirp": _chirp(), "ping": _ping(), "data": _data(), "zap": _zap()}.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_IN
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(T_POCKET + 0.1, "chirp", 0.45), (T_ROOF, "tick", 0.35), (T_CANT - 0.05, "impact", 0.35),
           (T_KNOW - 0.1, "impact", 0.4), (T_HOOK_OUT - 0.1, "whoosh_big", 0.4), (T_KEYLESS0, "ping", 0.3),
           (T_BUTTON, "whoosh_up", 0.35), (T_HUNDRED, "ping", 0.3), (T_FAR, "impact", 0.3),
           (T_PARTS + 0.1, "whoosh_down", 0.35), (T_HANDLES, "tick", 0.3), (T_BUMPER, "tick", 0.3),
           (T_CABIN, "tick", 0.3), (T_WEAK, "ping", 0.3), (T_METER, "tick", 0.3), (T_GRAB, "clunk", 0.35),
           (T_WAKE, "ping", 0.4), (T_CHAL - 0.2, "data", 0.35), (T_SCRAM, "data", 0.3),
           (T_ANSWERS, "data", 0.35), (T_ANSWERS + 0.6, "chirp", 0.4), (T_RE, "whoosh_big", 0.35),
           (T_INSIDE - 0.1, "impact", 0.3), (T_MEASURES, "ping", 0.3), (T_IN - 0.05, "impact", 0.4),
           (T_OUT - 0.05, "impact", 0.3), (T_RELAY, "whoosh_big", 0.35), (T_BOXES, "zap", 0.35),
           (T_STRETCH, "zap", 0.4), (T_HALLWAY + 0.15, "chirp", 0.45), (T_TEN, "tick", 0.3),
           (T_FIFTY, "tick", 0.3), (T_SLEEP, "whoosh_down", 0.3), (T_TIME, "ping", 0.35),
           (T_GIVES - 0.05, "impact", 0.4), (T_OUTRO, "whoosh_big", 0.3), (T_LISTENS, "chirp", 0.35)]
    return {"build": (T_RE, T_IN), "drop": (T_IN, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
