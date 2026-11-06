"""Matrix headlights visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  ROAD   (hook, what)      driver's-eye night road; our high beam drawn on the road as 25 slices; an oncoming car
                           drives through it with a dark gap around it (unexplained: the open loop).
  REACH  (problem)         low beam pool vs high beam reaching far (roadside posts light up); an oncoming car
                           gets the full high beam -> DAZZLED; the driver dips; IIHS 18 % card.
  SPLIT  (parts start)     the high beam splits into its 25 slices on the road.
  LAMP   (parts)           headlamp cutaway (3/4 ortho): 25 LEDs + lenses, each LED wired by a ray to its slice
                           tile; wave lights on "twenty five", one LED + slice highlighted on "its own slice".
  CAMERA (camera)          viewfinder over the road: detection boxes on the oncoming car and the car ahead.
  REHOOK (rehook)          full beam (no masking): light streams along the slices into the oncoming car -> glare.
  KEY    (key)             the slices aimed at each car switch off (LED strip tiles go dark), a dark gap wraps
                           around each car and slides with it as it moves.
  RESULT (result)          dense traffic -> mostly low beam; empty road -> every slice on; US legal 2022 chip.
  OUTRO  (outro)           the hook shot again, now understood.

Model (illustrative): pinhole camera at the driver's eye (height HC, focal FOC); the high beam is 25 equal angular
slices from the car's centre between -A_MAX and +A_MAX, out to BEAM_FAR. A slice switches off when it is within
a car's angular half-width plus a margin (soft edge one slice wide). Brightness of anything on the road =
low-beam pool + sum of the slice it sits in, faded with distance.
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, flow, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_HIGH = F("hook", "high")
T_AIMED0 = F("hook", "aimed")
T_ISNT = F("hook", "isn't")
T_LIGHT0 = F("hook", "light")
T_WHAT = L("what")["start"]
T_MATRIX0 = F("what", "matrix")
T_PROB = L("problem")["start"]
T_FARTHER = F("problem", "farther")
T_DAZZLE = F("problem", "dazzle")
T_BARELY = F("problem", "barely")
T_EIGHTEEN = F("problem", "eighteen")
T_ALONE = F("problem", "alone")
T_PARTS = L("parts")["start"]
T_SLICES = F("parts", "slices.")
T_AUDI = F("parts", "audi")
T_HEADLIGHT = F("parts", "headlight")
T_25 = F("parts", "twenty", nth=1)
T_LEDS = F("parts", "leds,")
T_SLICE = F("parts", "slice")
T_CAM = L("camera")["start"]
T_CAMERA = F("camera", "camera")
T_COMING = F("camera", "coming")
T_AHEAD = F("camera", "ahead")
T_RE = L("rehook")["start"]
T_STOP = F("rehook", "stop")
T_FLYING = F("rehook", "flying")
T_KEY = L("key")["start"]
T_DONT = F("key", "don't.")
T_NEVER = F("key", "never")
T_OFF = F("key", "off")
T_EVERY = F("key", "every")
T_GAP = F("key", "gap")
T_SLIDES = F("key", "slides")
T_RES = L("result")["start"]
T_TRAFFIC = F("result", "traffic?")
T_LOW = F("result", "low")
T_EMPTY = F("result", "empty")
T_FULLHB = F("result", "high")
T_AMERICA = F("result", "america,")
T_LEGAL = F("result", "legal")
T_OUTRO = L("outro")["start"]
T_NEVER2 = F("outro", "never")

S_LAMP = (T_AUDI - 0.15, T_CAM + 0.25)


def scene_k(t, s, fin=0.3, fout=0.3):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== road + beam model
# Elevated chase camera (long lens, mild perspective). World units are compressed along the road (not to scale):
# Z forward from our headlights, X right, Y up.
_PHI = math.radians(15.0)
_R, _ZT = 150.0, 20.0
CAM_H = _R * math.sin(_PHI)
CAM_D = _R * math.cos(_PHI) - _ZT
CAMX = -1.8          # camera centred on the road (our lane centre is X = 0)
_S, _C = math.sin(_PHI), math.cos(_PHI)


def _raw(X, Z, Y=0.0):
    X, Z, Y = (np.asarray(v, float) for v in (X, Z, Y))
    zc = -(Y - CAM_H) * _S + (Z + CAM_D) * _C
    yc = (Y - CAM_H) * _C + (Z + CAM_D) * _S
    return (X - CAMX) / zc, -yc / zc


_y0, _y1 = float(_raw(0, -6)[1]), float(_raw(0, 46)[1])
FOC = (1420 - 600) / (_y0 - _y1)
CY = 1420 - FOC * _y0

N_SEG = 25
A_MAX = 10.0         # high beam spans -A_MAX..+A_MAX degrees
SEG_W = 2 * A_MAX / N_SEG
SEG_C = np.array([-A_MAX + SEG_W * (i + 0.5) for i in range(N_SEG)])
BEAM_NEAR, BEAM_FAR = 0.3, 62.0
LOW_FAR = 13.0
X_ONC = -3.6         # oncoming lane centre
ROAD_L, ROAD_R = -5.6, 1.9
C_BEAM = hx("#fff1c9")
SPEED = 6.0          # our speed for road markings (units/s)
Z_FOG0, Z_FOG1 = 55.0, 75.0


def P(X, Z, Y=0.0):
    x, y = _raw(X, Z, Y)
    return np.stack(np.broadcast_arrays(540 + FOC * x, CY + FOC * y), -1)


def fog(Z):
    return clamp(1 - (Z - Z_FOG0) / (Z_FOG1 - Z_FOG0))


def ang_of(X, Z):
    return math.degrees(math.atan2(X, Z))


def seg_of(X, Z):
    if Z <= 0:
        return None
    a = ang_of(X, Z)
    if a < -A_MAX or a > A_MAX:
        return None
    return int(min(N_SEG - 1, (a + A_MAX) / SEG_W))


# ---------------------------------------------------------------- traffic per beat
def _ease_track(t, t0, t1, z0, z1):
    return z0 + (z1 - z0) * ease(lin(t, t0, t1))


def cars_at(t):
    """[(X, Z, kind)] Z = the car's end nearest to us. kind: 'onc' (oncoming, headlights) or 'ahead' (tail lights)."""
    cars = []
    if t < T_PROB:
        z = 50.0 - (50.0 - 4.0) * lin(t, 0.0, T_PROB - 0.1) ** 1.15
        cars.append((X_ONC, z, "onc"))
    elif t < T_PARTS:
        if T_DAZZLE - 0.6 <= t < T_EIGHTEEN - 0.2:
            z = 44.0 - (44.0 - 3.0) * lin(t, T_DAZZLE - 0.6, T_EIGHTEEN - 0.2)
            cars.append((X_ONC, z, "onc"))
    elif t < T_CAM:
        pass
    elif t < T_RE:
        cars.append((X_ONC, _ease_track(t, T_CAM, T_RE + 0.2, 64.0, 34.0), "onc"))
        cars.append((0.0, _ease_track(t, T_CAM, T_RE, 34.0, 24.0), "ahead"))
    elif t < T_KEY:
        cars.append((X_ONC, _ease_track(t, T_RE - 0.2, T_KEY, 34.0, 29.0), "onc"))
        cars.append((0.0, 24.0, "ahead"))
    elif t < T_RES:
        z = 29.0 - (29.0 - 2.0) * lin(t, T_KEY, T_RES - 0.1) ** 1.1
        cars.append((X_ONC, z, "onc"))
        cars.append((0.0, _ease_track(t, T_KEY, T_RES, 24.0, 21.0), "ahead"))
    elif t < T_EMPTY - 0.1:
        d = t - T_RES
        for j in range(8):
            z = 6.0 + 8.5 * j - 7.0 * d
            if 1.0 < z < 70.0:
                cars.append((X_ONC, z, "onc"))
        cars.append((0.0, 9.0, "ahead"))
        cars.append((0.0, 26.0, "ahead"))
    elif t < T_OUTRO:
        pass
    else:
        z = 48.0 - (48.0 - 14.0) * lin(t, T_OUTRO, T_END + 0.6)
        cars.append((X_ONC, z, "onc"))
    return [c for c in cars if c[1] > -4.0]


def mask_k(t):
    """1 = matrix active (slices around cars off), 0 = plain high beam."""
    if t < T_PROB:
        return 1.0
    if t < T_KEY:
        return 0.0
    return ease(lin(t, T_OFF - 0.05, T_OFF + 0.35))


def high_k(t):
    """High beam level (0 = low beam only)."""
    if T_PROB - 0.1 <= t < T_PARTS - 0.2:
        up = ease(lin(t, T_FARTHER - 0.25, T_FARTHER + 0.25))
        down = ease(lin(t, T_BARELY - 0.1, T_BARELY + 0.3))
        return up * (1 - down)
    return 1.0


CAR_HW = 0.92


def seg_bright(t, cars=None):
    cars = cars_at(t) if cars is None else cars
    hk = high_k(t)
    mk = mask_k(t)
    on = np.ones(N_SEG)
    for X, Z, kind in cars:
        if Z > BEAM_FAR or Z <= 0.5:
            continue
        a_l = ang_of(X - CAR_HW, Z)
        a_r = ang_of(X + CAR_HW, Z)
        d = np.maximum(a_l - SEG_C, SEG_C - a_r) - 0.25
        on = np.minimum(on, np.clip(d / SEG_W, 0, 1))
    return hk * (1 - mk * (1 - on))


def dist_fade(Z):
    return clamp(1 - (Z - 34) / (BEAM_FAR - 34)) * clamp(Z / 1.5)


def low_light(X, Z):
    if Z <= 0:
        return 0.0
    a = ang_of(X, Z)
    reach = LOW_FAR + (5 if a > 0 else 0)
    if a < -40 or a > 50:
        return 0.0
    return 0.7 * clamp(1 - Z / reach) ** 0.8


def light_at(X, Z, sb):
    s = seg_of(X, Z)
    hi = sb[s] * dist_fade(Z) if s is not None else 0.0
    return min(1.0, low_light(X, Z) + hi)


# ---------------------------------------------------------------- drawing: world
def draw_world(cv, t, sb, split=0.0, a=1.0):
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    # ground (lets the blueprint grid show faintly) + road
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(hx("#04060a"), a=0.55))
    zz = np.linspace(-8, Z_FOG1, 40)
    road = np.vstack([P(np.full_like(zz, ROAD_L), zz), P(np.full_like(zz, ROAD_R), zz[::-1])])
    gp = skia.Paint(AntiAlias=True)
    yt, yb = P(0, Z_FOG1)[1], P(0, -8)[1]
    yf0 = float(P(0, Z_FOG0)[1])
    gp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, yt), skia.Point(0, yb)],
                                                [col(hx("#151a23"), 0.0), col(hx("#151a23"), 1.0),
                                                 col(hx("#1b212c"), 1.0)], [0, (yf0 - yt) / (yb - yt), 1]))
    cv.drawPath(poly_path(road), gp)
    # low beam pool (asymmetric: reaches farther on the right)
    lp = []
    for a_ in np.linspace(-28, 38, 46):
        reach = LOW_FAR + (5 if a_ > 0 else 0)
        lp.append((math.tan(math.radians(a_)) * reach, reach))
    lp = np.array(lp)
    pool = np.vstack([P(np.array([-1.0, 1.0]), np.array([0.2, 0.2])), P(lp[::-1, 0], lp[::-1, 1])])
    pp = skia.Paint(AntiAlias=True)
    y0, y1 = P(0, 0.2)[1], P(0, LOW_FAR + 5)[1]
    pp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                                [col(C_BEAM, 0.24), col(C_BEAM, 0.09), col(C_BEAM, 0.0)],
                                                [0, 0.55, 1]))
    pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    pp.setBlendMode(skia.BlendMode.kScreen)
    cv.drawPath(poly_path(pool), pp)
    # high beam slices
    yn, yf = P(0, BEAM_NEAR)[1], P(0, BEAM_FAR)[1]
    zs = np.linspace(BEAM_NEAR, BEAM_FAR, 12)
    for i in range(N_SEG):
        b = sb[i]
        if b <= 0.01:
            continue
        a0, a1 = math.radians(SEG_C[i] - SEG_W / 2), math.radians(SEG_C[i] + SEG_W / 2)
        quad = np.vstack([P(np.tan(a0) * zs, zs), P(np.tan(a1) * zs[::-1], zs[::-1])])
        sp = skia.Paint(AntiAlias=True)
        tint = mix(C_BEAM, hx("#ffd98a") if i % 2 else hx("#cfe6ff"), 0.45 * split)
        sp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, yn), skia.Point(0, yf)],
                                                    [col(tint, 0.10 * b), col(tint, 0.30 * b), col(tint, 0.0)],
                                                    [0, 0.55, 1]))
        sp.setBlendMode(skia.BlendMode.kScreen)
        cv.drawPath(poly_path(quad), sp)
    if split > 0:
        for i in range(N_SEG + 1):
            a_ = math.radians(-A_MAX + SEG_W * i)
            zz2 = np.array([2.0, BEAM_FAR * 0.85])
            q = P(np.tan(a_) * zz2, zz2)
            cv.drawLine(*q[0], *q[1], paint(hx("#0b111c"), a=0.7 * split, stroke=2.5))
    # lane markings (brightness from the light that hits them)
    off = (t * SPEED) % 6.0
    for X, dashed, c in ((ROAD_L + 0.15, False, hx("#e8edf5")), (ROAD_R - 0.15, False, hx("#e8edf5")),
                         (-1.8, True, hx("#ffcf3a"))):
        z = -8.0 - (off if dashed else 0.0)
        step = 6.0 if dashed else 2.0
        while z < Z_FOG1:
            z0, z1 = z, z + (2.5 if dashed else 2.0)
            lt = 0.12 + 0.88 * light_at(X, (z0 + z1) / 2, sb)
            q = P([X, X], [z0, z1])
            cv.drawLine(*q[0], *q[1], paint(c, a=(0.1 + 0.85 * lt) * fog(z1), stroke=6))
            z += step
    # reflector posts on both shoulders
    poff = (t * SPEED) % 8.0
    for X in (ROAD_R + 1.0, ROAD_L - 1.0):
        z = -8.0 - poff
        while z < Z_FOG1:
            lt = light_at(X, z, sb)
            b, tp = P(X, z), P(X, z, 1.0)
            fa = fog(z)
            cv.drawLine(*b, *tp, paint(mix(hx("#2a2f38"), hx("#c9d0da"), lt), a=fa, stroke=5))
            if lt > 0.05:
                q = P(X, z, 0.85)
                cv.drawCircle(*q, 9, paint(AMBER, a=0.5 * lt * fa, blur=6))
                cv.drawCircle(*q, 5, paint(hx("#ffd27a"), a=lt * fa))
            z += 8.0
    cv.restore()


def box_faces(X, Z, hw, y0, y1, z0, z1):
    """Visible faces of an axis-aligned box seen from the chase camera: side (toward camera X), near end, top."""
    xs = X - hw if X > CAMX else X + hw
    side = P([xs, xs, xs, xs], [z0, z1, z1, z0], [y0, y0, y1, y1])
    near = P([X - hw, X + hw, X + hw, X - hw], [z0, z0, z0, z0], [y0, y0, y1, y1])
    top = P([X - hw, X + hw, X + hw, X - hw], [z0, z0, z1, z1], [y1, y1, y1, y1])
    return side, near, top


def draw_box(cv, X, Z, hw, y0, y1, z0, z1, c, a=1.0, near_c=None):
    side, near, top = box_faces(X, Z, hw, y0, y1, z0, z1)
    cv.drawPath(poly_path(side), paint(shade(c, 0.6), a=a))
    cv.drawPath(poly_path(near), paint(near_c if near_c is not None else shade(c, 0.85), a=a))
    cv.drawPath(poly_path(top), paint(shade(c, 1.15), a=a))
    return near, top


def car_bbox(X, Z):
    pts = np.vstack([P([X - CAR_HW, X + CAR_HW], [Z, Z], [0.25, 0.25]), P([X - CAR_HW, X + CAR_HW], [Z + 4.5, Z + 4.5],
                                                                          [1.42, 1.42])])
    return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()


def car_anchor(X, Z):
    return tuple(P(X, Z, 1.9))


def draw_car3(cv, X, Z, kind, lit, glare=0.0, a=1.0, body=None):
    """kind 'onc': its front faces us (headlights); 'ahead'/'own': its rear faces us (tail lights)."""
    fa = a * fog(Z)
    if fa <= 0:
        return
    base = body if body is not None else hx("#3a4250")
    c = mix(base, hx("#e6dfca"), 0.7 * lit)
    sh = np.vstack([P([X - 1.1, X + 1.1, X + 1.1, X - 1.1], [Z - 0.2, Z - 0.2, Z + 4.7, Z + 4.7])])
    cv.drawPath(poly_path(sh), paint(hx("#000000"), a=0.55 * fa, blur=6))
    draw_box(cv, X, Z, CAR_HW, 0.25, 0.9, Z, Z + 4.5, c, a=fa)
    cz0, cz1 = (Z + 1.3, Z + 3.4) if kind == "onc" else (Z + 0.9, Z + 3.1)
    near, top = draw_box(cv, X, Z, 0.78, 0.9, 1.42, cz0, cz1, c, a=fa,
                         near_c=mix(hx("#0d1626"), hx("#7f93ad"), 0.6 * lit))
    if kind == "onc":
        for sx in (-0.62, 0.62):
            q = P(X + sx, Z, 0.62)
            look.bloom(cv, q[0], q[1], 7, hx("#f4f8ff"), a=0.95 * fa)
        if glare > 0 and lit > 0.2:
            g = glare * clamp((lit - 0.2) / 0.5) * fa
            cen = near.mean(0)
            cv.drawCircle(*cen, 60, paint(C_BEAM, a=0.6 * g, blur=26))
            cv.drawPath(poly_path(near), paint(RED, a=g, stroke=4))
    else:
        for sx in (-0.68, 0.68):
            q = P(X + sx, Z, 0.7)
            look.bloom(cv, q[0], q[1], 5, RED, a=0.9 * fa)


def car_lit(X, Z, sb):
    segs = [seg_of(X + dx, Z + 0.5) for dx in (-0.9, 0.0, 0.9)]
    lit = max([sb[s] for s in segs if s is not None] + [0.0]) * dist_fade(Z)
    return max(lit, low_light(X, Z))


def draw_cars(cv, t, cars, sb, glare=0.0, a=1.0):
    if a <= 0:
        return
    for X, Z, kind in sorted(cars, key=lambda c: -c[1]):
        draw_car3(cv, X, Z, kind, car_lit(X, Z, sb), glare=glare, a=a)


def draw_own_car(cv, t, a=1.0):
    """Our car, seen from behind: front bumper at Z = 0."""
    if a <= 0:
        return
    draw_car3(cv, 0.0, -4.5, "own", 0.0, a=a, body=hx("#2f6fb0"))
    for sx in (-0.62, 0.62):
        q = P(sx, 0.05, 0.6)
        look.bloom(cv, q[0], q[1], 6, hx("#fff4d6"), a=0.7 * a)


def draw_strip(cv, sb, y, a=1.0, title="HIGH BEAM · 25 LEDs", tw=30.0, gap=3.0, hl=None, x0=None):
    """Row of the 25 high-beam LEDs as tiles (left = left of the road)."""
    if a <= 0:
        return []
    tot = N_SEG * tw + (N_SEG - 1) * gap
    x0 = (W - tot) / 2 if x0 is None else x0
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    box = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - 22, y - 74, x0 + tot + 22, y + tw * 1.4 + 18), 18, 18)
    cv.drawRRect(box, paint(hx("#0b111c"), a=0.88))
    cv.drawRRect(box, paint(hx("#2a3446"), stroke=2))
    if title:
        draw_text(cv, title, x0, y - 30, font("inter_xb", 22), MUTED, tracking=3)
    cent = []
    for i in range(N_SEG):
        b = float(sb[i])
        x = x0 + i * (tw + gap)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, tw, tw * 1.4), 6, 6)
        if b > 0.02:
            cv.drawRRect(r, paint(C_BEAM, a=0.55 * b, blur=8))
        cv.drawRRect(r, paint(mix(hx("#141a24"), hx("#fff6dc"), b)))
        cv.drawRRect(r, paint(YEL if hl == i else mix(hx("#3a4252"), hx("#ffe7a8"), b), stroke=3 if hl == i else 1.5))
        cent.append((x + tw / 2, y))
    cv.restore()
    return cent


# ================================================================== LAMP scene (cutaway)
LED_X = np.linspace(-240, 240, N_SEG)


def draw_lamp(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(k)))
    pj = Proj(500, 700, 1.45, yaw=72, pitch=22)
    wave = [eout(lin(t, T_25 + 0.04 * i, T_25 + 0.04 * i + 0.25)) for i in range(N_SEG)]
    base_on = 0.25
    on = [max(base_on * (1 - ease(lin(t, T_25 - 0.3, T_25))), w) for w in wave]
    hl = 12 if t > T_SLICE - 0.2 else None
    # housing back shell + board
    shell = np.array([(-290, -95), (290, -95), (300, -60), (300, 70), (280, 95), (-280, 95), (-300, 60), (-300, -60)])
    extrude(cv, pj, shell, 0, 150, hx("#2a3140"), alpha=0.85, rim=hx("#7f93ad"), rim_w=1.5)
    board = np.array([(-262, -26), (262, -26), (262, 26), (-262, 26)])
    extrude(cv, pj, board, 110, 122, hx("#16301f"), alpha=1.0, rim=hx("#3ee08f"), rim_w=1.0)
    # LEDs + lenses (far to near in z)
    led = np.array([(-7, -7), (7, -7), (7, 7), (-7, 7)])
    for i, x in enumerate(LED_X):
        c = mix(hx("#4b5566"), hx("#fff6dc"), on[i])
        extrude(cv, pj, led + np.array([x, 0]), 100, 110, c, alpha=1.0)
        if on[i] > 0.05:
            q = pj(x, 0, 100)
            look.bloom(cv, q[0], q[1], 6, hx("#fff1c9"), a=on[i])
    lens_pts = []
    for i, x in enumerate(LED_X):
        cyl3(cv, pj, (x, 0, 62), (x, 0, 54), 9.5, hx("#9fc2e6"), alpha=0.55, n=24,
             edge=YEL if hl == i else hx("#cfe0f5"))
        lens_pts.append(pj(x, 0, 54))
    # glass front
    extrude(cv, pj, shell, -2, 0, hx("#9fb6d8"), alpha=0.10, rim=hx("#cfe0f5"), rim_w=1.5)
    cv.restore()
    # rays to the slice strip
    sb_lamp = np.array(on)
    ys = 1150.0
    ck = k * eout(lin(t, T_AUDI + 0.2, T_AUDI + 0.8))
    cents = draw_strip(cv, sb_lamp, ys, a=ck, title="THE ROAD AHEAD · 25 SLICES", hl=hl)
    if cents:
        for i, (lp_, (cx, cy)) in enumerate(zip(lens_pts, cents)):
            b = on[i]
            if b <= 0.03:
                continue
            c = YEL if hl == i else C_BEAM
            aa = ck * (0.9 if hl == i else 0.25 * b * (0.35 if hl is not None else 1.0))
            cv.drawLine(lp_[0], lp_[1] + 8, cx, cy - 4, paint(c, a=aa, stroke=3 if hl == i else 1.6))
    # labels
    q0 = pj(-300, -60, 0)
    brand.label(cv, t, "HEADLIGHT", (q0[0] + 6, q0[1]), (90, 540), MUTED, T_HEADLIGHT - 0.15, T_25)
    if len(lens_pts):
        brand.label(cv, t, "LED + LENS", tuple(pj(LED_X[3], -10, 100)), (90, 540), YEL, T_LEDS - 0.2, T_SLICE - 0.1)
    if hl is not None:
        lp = lens_pts[hl]
        brand.label(cv, t, "ONE LED = ONE SLICE", (cents[hl][0], cents[hl][1] - 6) if cents else tuple(lp),
                    (330, 1060), YEL, T_SLICE - 0.15, T_CAM + 0.2)
    rk = k * eout(lin(t, T_25 - 0.1, T_25 + 0.3))
    n_on = sum(1 for w in wave if w > 0.5)
    brand.readout(cv, rk, f"{n_on}", "LEDs PER HEADLIGHT", frac=n_on / N_SEG, bar_color=YEL)
    brand.note(cv, "AUDI A8 · 2013 · SIMPLIFIED", 0.9 * rk)


# ================================================================== overlays per beat
def corner_brackets(cv, x0, y0, x1, y1, c, a, L_=60):
    p = paint(c, a=a, stroke=5, cap=skia.Paint.kRound_Cap)
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        cv.drawLine(x, y, x + dx * L_, y, p)
        cv.drawLine(x, y, x, y + dy * L_, p)


def draw_camera_overlay(cv, t, cars):
    k = win(t, T_CAM - 0.1, T_RE + 0.1, 0.3, 0.3)
    if k <= 0:
        return
    corner_brackets(cv, 80, 470, 1000 - 80, 1250, INK, 0.85 * k)
    pill(cv, 110, 520, "CAMERA VIEW", font("inter_xb", 26), INK, border=CYAN, a=k, tracking=3, dot=RED)
    for X, Z, kind in cars:
        tk = T_COMING if kind == "onc" else T_AHEAD
        kk = k * eback(lin(t, tk - 0.1, tk + 0.25)) * fog(Z)
        if kk <= 0:
            continue
        x0, y0, x1, y1 = car_bbox(X, Z)
        pad = 14
        c = YEL if kind == "onc" else CYAN
        r = skia.Rect.MakeLTRB(x0 - pad, y0 - pad, x1 + pad, y1 + pad)
        cv.drawRect(r, paint(c, a=clamp(kk), stroke=3))
        txt = "ONCOMING" if kind == "onc" else "AHEAD"
        pill(cv, r.left(), r.top() - 26, txt, font("inter_xb", 22), INK, border=c, a=clamp(kk), tracking=2)


def draw_streams(cv, t, cars, sb):
    k = win(t, T_RE - 0.1, T_KEY + 0.2, 0.3, 0.3)
    if k <= 0:
        return
    for X, Z, kind in cars:
        if kind != "onc":
            continue
        for j, sx in enumerate((-0.62, 0.62)):
            p0 = P(sx, 0.1, 0.6)
            p1 = P(X + 0.3 * sx, Z, 1.15)
            pts = np.array([p0 + (p1 - p0) * u for u in np.linspace(0, 1, 20)])
            flow(cv, pts, t, 700, 55, C_BEAM, r=5, a=0.85 * k, offset=27 * j)


def draw_stat(cv, t):
    k = win(t, T_EIGHTEEN - 0.15, T_PARTS + 0.1, 0.25, 0.3)
    if k <= 0:
        return
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(120, 470, 960, 790), 28, 28)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.9 * k))
    cv.drawRRect(rr, paint(YEL, a=0.7 * k, stroke=2.5))
    n = 18 * eout(lin(t, T_EIGHTEEN - 0.1, T_EIGHTEEN + 0.5))
    draw_text(cv, f"{n:.0f}%", 540, 640, font("pop_b", 170), YEL, a=k, align="center", glow=16)
    draw_text(cv, "OF DRIVERS ALONE ON THE ROAD", 540, 705, font("inter_xb", 32), INK, a=k, align="center",
              tracking=2)
    draw_text(cv, "HAD THEIR HIGH BEAMS ON  ·  IIHS STUDY", 540, 750, font("inter_sb", 24), MUTED, a=k,
              align="center", tracking=2)


def draw_reach(cv, t):
    k = win(t, T_FARTHER - 0.1, T_DAZZLE - 0.1, 0.3, 0.3)
    if k <= 0:
        return
    x = 900.0
    y_lo = P(0, LOW_FAR)[1]
    y_hi = P(0, BEAM_FAR * 0.85)[1]
    g = eout(lin(t, T_FARTHER - 0.1, T_FARTHER + 0.6))
    ye = y_lo + (y_hi - y_lo) * g
    cv.drawLine(x, y_lo, x, ye, paint(YEL, a=k, stroke=5))
    cv.drawLine(x - 14, y_lo, x + 14, y_lo, paint(CYAN, a=k, stroke=5))
    cv.drawLine(x - 14, ye, x + 14, ye, paint(YEL, a=k, stroke=5))
    draw_text(cv, "LOW", x - 24, y_lo + 9, font("inter_xb", 24), CYAN, a=k, align="right", tracking=2)
    draw_text(cv, "HIGH", x - 24, ye + 9, font("inter_xb", 24), YEL, a=k * g, align="right", tracking=2)


def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    hb = high_k(t)
    sec = [(0, "MATRIX HEADLIGHTS", YEL), (T_PROB, "LOW BEAM", CYAN), (T_FARTHER, "HIGH BEAM", YEL),
           (T_BARELY, "BACK TO LOW BEAM", CYAN), (T_EIGHTEEN, "THE PROBLEM", RED), (T_PARTS, "THE SLICES", YEL),
           (T_CAM, "THE CAMERA", CYAN), (T_RE, "THE QUESTION", YEL), (T_KEY, "THE ANSWER", RED),
           (T_RES, "BUSY ROAD", CYAN), (T_EMPTY, "EMPTY ROAD", YEL), (T_OUTRO, "MATRIX HEADLIGHTS", RED)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    if T_PROB < t < T_KEY and not (S_LAMP[0] < t < S_LAMP[1]):
        brand.note(cv, "ILLUSTRATION · NOT TO SCALE", 0.9 * k, dy=-40)
    del hb


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    lamp_k = scene_k(t, S_LAMP, 0.25, 0.3)
    road_k = (1 - lamp_k) * kE
    cars = cars_at(t)
    sb = seg_bright(t, cars)
    split = win(t, T_SLICES - 0.3, T_CAM + 0.3, 0.3, 0.3)
    if road_k > 0:
        draw_world(cv, t, sb, split=split, a=road_k)
        glare = win(t, T_DAZZLE - 0.2, T_BARELY + 0.3, 0.2, 0.3) + win(t, T_STOP - 0.2, T_OFF + 0.1, 0.3, 0.2)
        draw_cars(cv, t, cars, sb, glare=clamp(glare), a=road_k)
        draw_streams(cv, t, cars, sb)
        draw_own_car(cv, t, a=road_k)
        look.vignette(cv, 0.45)
    draw_lamp(cv, t, lamp_k)
    if road_k > 0:
        draw_camera_overlay(cv, t, cars)
        draw_reach(cv, t)
        draw_stat(cv, t)
        # live LED strip from the key beat on
        sk = road_k * win(t, T_KEY - 0.2, T_END + 0.2, 0.3, 0.3) * kE
        draw_strip(cv, sb, 400, a=sk)
        sk2 = road_k * win(t, T_SLICES - 0.2, T_AUDI + 0.1, 0.3, 0.2)
        draw_strip(cv, sb, 400, a=sk2, title="25 SLICES")
    # hook chips
    hk = win(t, T_HIGH - 0.1, T_ISNT - 0.05, 0.2, 0.2)
    if hk > 0:
        pill(cv, 540, 540, "HIGH BEAMS: ON", font("inter_xb", 30), INK, border=YEL, a=hk, align="center",
             tracking=2, dot=YEL)
    nk = win(t, T_ISNT - 0.1, T_WHAT + 0.4, 0.2, 0.3)
    if nk > 0:
        pill(cv, 540, 540, "ONCOMING DRIVER: NOT BLINDED", font("inter_xb", 30), INK, border=GREEN, a=nk,
             align="center", tracking=2, dot=GREEN)
    brand.stamp(cv, t, "WHERE DID IT GO?", T_LIGHT0 - 0.05, dur=1.6, center=(540, 580), color=YEL,
                bg=hx("#2a2405"))
    brand.stamp(cv, t, "DAZZLED", T_DAZZLE, dur=1.4, center=(540, 580))
    brand.stamp(cv, t, "HOW?", T_FLYING, dur=1.3, center=(540, 580), color=YEL, bg=hx("#2a2405"))
    brand.stamp(cv, t, "YOU DON'T", T_DONT - 0.05, dur=1.0, center=(540, 580))
    brand.stamp(cv, t, "SWITCHED OFF", T_OFF - 0.05, dur=1.5, center=(540, 580))
    brand.stamp(cv, t, "≈ LOW BEAM", T_LOW - 0.05, dur=1.3, center=(540, 580), color=CYAN, bg=hx("#05202a"))
    brand.stamp(cv, t, "FULL HIGH BEAM", T_FULLHB - 0.05, dur=1.3, center=(540, 580), color=YEL, bg=hx("#2a2405"))
    lk = win(t, T_AMERICA - 0.1, T_OUTRO + 0.1, 0.25, 0.3)
    if lk > 0:
        pill(cv, 540, 580, "US: LEGAL SINCE 2022 · NHTSA RULE", font("inter_xb", 30), INK, border=GREEN, a=lk,
             align="center", tracking=2, dot=GREEN)
    # key-beat label on the gap
    gk = win(t, T_GAP - 0.1, T_RES, 0.25, 0.3)
    if gk > 0:
        for X, Z, kind in cars:
            if kind == "onc":
                f_ = (Z + 9.0) / max(Z, 1.0)
                q = P(X * f_, Z * f_)
                brand.label(cv, t, "DARK GAP", tuple(q), (90, 640), RED, T_GAP - 0.1, T_RES)
                break
    ek = win(t, T_EVERY - 0.1, T_GAP - 0.1, 0.25, 0.25)
    if ek > 0:
        pill(cv, 540, 560, "EVERY OTHER SLICE: FULL", font("inter_xb", 28), INK, border=YEL, a=ek, align="center",
             tracking=2, dot=YEL)
    draw_header(cv, t)


# ================================================================== sound (synthesized here)
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


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


def _passby(dur):
    """Car passing in the other lane: tyre/wind noise swelling and falling, with a slight pitch drop."""
    rng = np.random.default_rng(21)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    tc = dur * 0.62
    env = 1.0 / (1.0 + ((tt - tc) / (dur * 0.16)) ** 2)
    noise = rng.standard_normal(n)
    lo = _lp(noise, 700)
    hi = _lp(noise, 2600) - _lp(noise, 900)
    f0 = np.where(tt < tc, 95.0, 78.0)
    ph = np.cumsum(f0) / SR
    hum = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 5))
    return _norm((lo * 0.8 + hi * 0.5 * env + 0.25 * hum) * env, 0.75)


def _relay(dur=0.25):
    rng = np.random.default_rng(5)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-tt / 0.006) + 0.4 * np.sin(2 * np.pi * 2100 * tt) * np.exp(-tt / 0.02)
    return _norm(x, 0.8)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, x in {"car_pass": _passby(4.0), "relay": _relay()}.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_OFF
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(0.0, "car_pass", 0.45), (T_LIGHT0 - 0.05, "impact", 0.4), (T_HOOK_OUT - 0.1, "whoosh_big", 0.45),
           (T_FARTHER - 0.2, "whoosh_up", 0.35), (T_DAZZLE - 0.6, "car_pass", 0.4), (T_DAZZLE, "impact", 0.35),
           (T_BARELY, "relay", 0.4), (T_EIGHTEEN - 0.1, "whoosh_down", 0.3), (T_SLICES - 0.1, "tick", 0.35),
           (T_AUDI - 0.15, "whoosh_big", 0.35), (T_25, "tick", 0.25), (T_25 + 0.5, "tick", 0.2),
           (T_SLICE, "tick", 0.3), (T_CAM - 0.1, "whoosh_down", 0.3), (T_COMING, "tick", 0.3),
           (T_AHEAD, "tick", 0.3), (T_RE, "whoosh_big", 0.35), (T_FLYING, "impact", 0.35),
           (T_DONT - 0.05, "impact", 0.3), (T_OFF - 0.05, "relay", 0.5), (T_OFF + 0.05, "impact", 0.45),
           (T_KEY + 0.3, "car_pass", 0.35), (T_RES - 0.1, "whoosh_down", 0.3), (T_LOW, "relay", 0.35),
           (T_EMPTY - 0.1, "whoosh_up", 0.3), (T_FULLHB, "relay", 0.35), (T_LEGAL, "tick", 0.3),
           (T_OUTRO, "whoosh_big", 0.3)]
    return {"build": (T_RE, T_OFF), "drop": (T_OFF, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
