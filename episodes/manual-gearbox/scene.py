"""Manual gearbox visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (oblique view: gear faces true shape, shafts recede up-right along z):
  input shaft   (Y=0,  z<30)   engine side, carries the input gear (13 teeth)
  countershaft  (Y=90)          one rigid shaft: input-driven gear (17t) + 1st/2nd/3rd drive gears, all fixed
  output shaft  (Y=0,  z>40)    1st/2nd/3rd driven gears ride FREE on it; the collar is splined to it
  every pair is a real mesh: same module (6), centre distance 90, angles from tooth counts
  collar (+ fork on a rail) slides along z: synchro ring -> cone on 1st gear -> dog teeth on 1st gear
Story: neutral idle (all gears turn, output shaft still) -> clutch in -> collar slides -> synchro friction
drags the clutch-free input side to the collar's speed (zero, car standing) -> teeth lock -> clutch out:
engine drives 1st gear -> output shaft; 2nd and 3rd keep freewheeling.
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, spline, resample

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_EVEN = F("hook", "even")
T_WHAT = L("what")["start"]
T_NEVER = F("what", "never")
T_MESHED = F("what", "meshed")
T_PARTS = L("parts")["start"]
T_ENGINE = F("parts", "engine")
T_COUNTER = F("parts", "countershaft")
T_EVERY = F("parts", "every")
T_OUTPUT = F("parts", "output")
T_ATTACHED = F("parts", "attached")
T_FREELY = F("parts", "freely")
T_RATIO = L("ratio")["start"]
T_RATIO_W = F("ratio", "ratio")
T_SMALL = F("ratio", "small")
T_BIG = F("ratio", "big")
T_TRADES = F("ratio", "trades")
T_NEUTRAL = F("ratio", "neutral")
T_COLLAR = L("collar")["start"]
T_COLLAR_W = F("collar", "collar")
T_LOCKED_W = F("collar", "locked")
T_PRESS = F("collar", "press")
T_FIRST = F("collar", "first")
T_FORK = F("collar", "fork")
T_SLIDES = F("collar", "slides")
T_GRIND = L("grind")["start"]
T_STILL = F("grind", "still")
T_SPINNING = F("grind", "spinning")
T_SLAM = F("grind", "slam")
T_GRINDING = F("grind", "grinding")
T_KEY = L("key")["start"]
T_SYNCHRO = F("key", "synchro")
T_RUBS = F("key", "rubs")
T_FRICTION = F("key", "friction")
T_SAME = F("key", "same")
T_SPEED_END = F("key", "speed", which="end")
T_SLIDE_IN = F("key", "slide")
T_LOCK = F("key", "lock")
T_RESULT = L("result")["start"]
T_OUT_W = F("result", "out")
T_DRIVES = F("result", "drives")
T_WHEELS = F("result", "wheels")
T_EVERY2 = F("result", "every")
T_OUTRO = L("outro")["start"]
T_DOUBLE = F("outro", "double")

# ================================================================== gear train (model units, module 6)
CD = 90.0                     # centre distance output/input axis (Y=0) <-> countershaft (Y=90)
GW = 28.0                     # gear face width (z)
# station z, output-side gear (radius, teeth), counter gear (radius, teeth)
IN = dict(z=0.0, o=(39.0, 13), c=(51.0, 17))
G3 = dict(z=110.0, o=(42.0, 14), c=(48.0, 16))
G2 = dict(z=210.0, o=(51.0, 17), c=(39.0, 13))
G1 = dict(z=390.0, o=(60.0, 20), c=(30.0, 10))
for g in (IN, G3, G2, G1):
    assert abs(g["o"][0] + g["c"][0] - CD) < 1e-6 and abs(2 * g["o"][0] / g["o"][1] - 6) < 1e-6
    assert abs(2 * g["c"][0] / g["c"][1] - 6) < 1e-6

C_COUNTER = hx("#77839a")
C_OUT = hx("#aab7ca")
C_BRASS = hx("#c49a4c")
C_COLLAR = hx("#8fa0b8")

# ------------------------------------------------------------------ speeds (visual rev/s, slowed)
W_IDLE = 0.42
W_KEYS = [(0.0, W_IDLE), (T_PRESS, W_IDLE), (T_SLIDES + 0.6, W_IDLE * 0.82), (T_RUBS - 0.05, W_IDLE * 0.82),
          (T_SPEED_END, 0.0), (T_OUT_W - 0.05, 0.0), (T_OUT_W + 1.4, W_IDLE), (T_TOTAL + 1, W_IDLE)]


def w_in(t):
    return max(0.0, smooth(t, W_KEYS))


def _series():
    dt = 1.0 / 600
    ts = np.arange(0, T_TOTAL + 1.0, dt)
    w = np.array([w_in(x) for x in ts])
    th = np.concatenate([[0.0], np.cumsum(w[:-1]) * dt]) * 2 * np.pi + 0.3
    return ts, th


_TS, _TH = _series()


def theta_in(t):
    return float(np.interp(t, _TS, _TH))


def mesh_bottom(phi_top, n_top, n_bot):
    """Angle of the lower gear meshing with an upper gear (contact at the upper gear's +90° / lower's -90°)."""
    return -math.pi / 2 + math.pi / n_bot - (phi_top - math.pi / 2) * n_top / n_bot


def mesh_top(phi_bot, n_bot, n_top):
    return math.pi / 2 + math.pi / n_top - (phi_bot + math.pi / 2) * n_bot / n_top


def angles(t):
    a = {"in": theta_in(t)}
    a["c"] = mesh_bottom(a["in"], IN["o"][1], IN["c"][1])          # countershaft angle (input pair)
    # all counter gears share the shaft: their own tooth phase is set so they start meshed (rigid shaft)
    for k, g in (("3", G3), ("2", G2), ("1", G1)):
        a["c" + k] = a["c"] * 1.0
        a["o" + k] = mesh_top(a["c" + k], g["c"][1], g["o"][1])
    return a


A_LOCK = angles(T_LOCK)["o1"]


def out_angle(t):
    """Output shaft angle: still until 1st gear is locked, then turns with 1st gear."""
    if t < T_LOCK:
        return 0.0
    return angles(t)["o1"] - A_LOCK


def speed_gap(t):
    """1st gear speed relative to its idle speed while the collar is at rest (1 -> 0 during sync)."""
    return clamp(w_in(t) / W_IDLE) if t < T_LOCK else 0.0


# ------------------------------------------------------------------ collar / synchro positions (z)
Z_COLLAR_HOME, Z_COLLAR_TOUCH, Z_COLLAR_LOCK = 300.0, 327.0, 357.0
COLLAR_KEYS = [(0, Z_COLLAR_HOME), (T_SLIDES - 0.05, Z_COLLAR_HOME), (T_SLIDES + 0.6, Z_COLLAR_TOUCH),
               (T_RUBS - 0.1, Z_COLLAR_TOUCH), (T_RUBS + 0.25, Z_COLLAR_TOUCH + 2), (T_SLIDE_IN - 0.05, Z_COLLAR_TOUCH + 2),
               (T_LOCK + 0.1, Z_COLLAR_LOCK), (T_TOTAL + 1, Z_COLLAR_LOCK)]
RING_KEYS = [(0, 344.0), (T_RUBS - 0.1, 344.0), (T_RUBS + 0.25, 346.0), (T_TOTAL + 1, 346.0)]


def z_collar(t):
    return smooth(t, COLLAR_KEYS)


def z_ring(t):
    return smooth(t, RING_KEYS)


def rubbing(t):
    return win(t, T_RUBS + 0.1, T_SPEED_END + 0.3, 0.2, 0.3)


def check_physics():
    bad = []
    if out_angle(T_LOCK - 0.5) != 0.0:
        bad.append("output turns before a gear is locked")
    if w_in(T_LOCK) > 1e-3:
        bad.append("teeth lock before speeds match")
    if z_collar(T_SPEED_END - 0.2) > Z_COLLAR_TOUCH + 3:
        bad.append("collar engages before sync")
    return bad


assert not check_physics(), check_physics()

# ================================================================== camera
OVER = (299.0, 900.0, 1.9)
HOOKC = (320.0, 955.0, 1.8)
ZOOM_PT = (0.0, 30.0, 345.0)
ZOOM_S = 2.35
DX, DY = 0.62, -0.40


def _zoom_params():
    s = ZOOM_S
    X, Y, z = ZOOM_PT
    return (540 - s * (X + z * DX), 860 - s * (Y + z * DY), s)


ZOOMC = _zoom_params()


def cam(t):
    k_h = ease(lin(t, T_HOOK_OUT - 0.2, T_WHAT + 0.6))
    p = np.array(HOOKC) * (1 - k_h) + np.array(OVER) * k_h
    k_z = ease(lin(t, T_PRESS - 0.3, T_PRESS + 0.9)) * (1 - ease(lin(t, T_OUT_W - 0.6, T_OUT_W + 0.6)))
    p = p * (1 - k_z) + np.array(ZOOMC) * k_z
    return Proj(p[0], p[1], p[2], dx=DX, dy=DY)


# ================================================================== drawing helpers
def gear_prof(cx, cy, R, N, ang, h=6.6):
    p = 2 * math.pi / N
    pts = []
    for k in range(N):
        a = ang + k * p
        for da, r in ((-0.5, R - h * 0.55), (-0.3, R - h * 0.55), (-0.17, R + h * 0.45), (0.17, R + h * 0.45),
                      (0.3, R - h * 0.55)):
            pts.append((cx + r * math.cos(a + da * p), cy + r * math.sin(a + da * p)))
    return np.array(pts)


def draw_gear(cv, pj, cx, cy, z, R, N, ang, base, rim=None, glow=0.0, bore_c=None, bore_a=0.0, w=GW):
    rim_c = rim if rim is not None else None
    extrude(cv, pj, gear_prof(cx, cy, R, N, ang), z - w / 2, z + w / 2, base, rim=rim_c, rim_w=2.2, rim_glow=glow)
    # web recess + spokes marks so rotation reads
    c = pj(cx, cy, z - w / 2)
    r_in = (R - 10) * pj.s
    cv.drawCircle(c[0], c[1], r_in, paint(shade(base, 0.55), a=0.55, stroke=2.0 * pj.s))
    for k in range(3):
        a = ang + k * 2 * math.pi / 3
        p0 = pj(cx + 16 * math.cos(a), cy + 16 * math.sin(a), z - w / 2)
        p1 = pj(cx + (R - 14) * math.cos(a), cy + (R - 14) * math.sin(a), z - w / 2)
        cv.drawLine(*p0, *p1, paint(shade(base, 0.6), a=0.6, stroke=3.0 * pj.s))
    if bore_c is not None and bore_a > 0:
        cv.drawCircle(c[0], c[1], 15 * pj.s, paint(bore_c, a=0.45 * bore_a, blur=6 * pj.s))
        cv.drawCircle(c[0], c[1], 15 * pj.s, paint(bore_c, a=bore_a, stroke=3 * pj.s))


def shaft_items(pj, Y, z0, z1, r, base, ang=None, step=24.0):
    items = []
    zs = np.arange(z0, z1, step)
    for za in zs:
        zb = min(z1, za + step)

        def fn(cv, za=za, zb=zb):
            rev(cv, pj, "z", (0.0, Y), [za, zb], [r, r], base, n=28)
            if ang is not None:
                for zz in np.arange(za + 4, zb, 12.0):
                    pass
        items.append(((za + zb) / 2, fn))
    if ang is not None:
        # a painted stripe along the shaft so its rotation is visible
        def stripe(cv):
            if math.sin(ang) < -0.2:     # stripe on the hidden side
                return
            X, Yy = r * math.cos(ang), Y + r * math.sin(ang) * 0.0 - r * abs(math.sin(ang)) * 0.0
            P = pj(np.full(2, r * math.cos(ang)), np.full(2, Y - r * 0.2 + r * math.sin(ang) * 0.6), np.array([z0 + 4, z1 - 4]))
            cv.drawLine(*P[0], *P[1], paint(YEL, a=0.75, stroke=2.4 * pj.s))
        items.append((z0 - 1e-3 if False else (z0 + z1) / 2 + 0.01, stripe))
    return items


def fork_prof(r_in=27.0, r_out=37.0, top=-104.0):
    pts = []
    th = np.linspace(math.pi + 0.35, 1.5 * math.pi - 0.17, 10)
    pts += [(r_out * math.cos(a), r_out * math.sin(a)) for a in th]
    pts += [(-7.0, top), (7.0, top)]
    th = np.linspace(1.5 * math.pi + 0.17, 2 * math.pi - 0.35, 10)
    pts += [(r_out * math.cos(a), r_out * math.sin(a)) for a in th]
    th = np.linspace(2 * math.pi - 0.35, math.pi + 0.35, 20)
    pts += [(r_in * math.cos(a), r_in * math.sin(a)) for a in th]
    return np.array(pts)


FORK = fork_prof()


# ================================================================== the gearbox
def draw_gearbox(cv, t, a=1.0):
    if a <= 0:
        return
    pj = cam(t)
    an = angles(t)
    ao = out_angle(t)
    zc, zr = z_collar(t), z_ring(t)
    rub = rubbing(t)
    kE = 1 - current.ending_k(t)
    a *= kE
    if a <= 0:
        return
    # highlight strengths
    h_even = win(t, T_EVEN - 0.1, T_HOOK_OUT + 0.7, 0.2, 0.4)
    h_cnt = win(t, T_COUNTER - 0.1, T_EVERY + 1.1, 0.2, 0.4)
    h_free = win(t, T_OUTPUT - 0.1, T_FREELY + 1.2, 0.2, 0.4)
    h_small = win(t, T_SMALL - 0.1, T_TRADES + 1.2, 0.2, 0.4)
    h_big = win(t, T_BIG - 0.1, T_TRADES + 1.2, 0.2, 0.4)
    h_drive = clamp(ease(lin(t, T_OUT_W, T_OUT_W + 0.5)))
    h_idle_others = win(t, T_EVERY2 - 0.1, T_OUTRO + 0.6, 0.2, 0.4)
    h_meshed = win(t, T_MESHED - 0.1, T_PARTS + 0.3, 0.2, 0.3)

    items = []
    # shafts
    items += shaft_items(pj, 0.0, -60.0, 26.0, 11.0, STEEL)
    items += shaft_items(pj, 0.0, 40.0, 470.0, 10.0, mix(STEEL, hx("#ff8080"), 0.35 * h_drive))
    items += shaft_items(pj, CD, -26.0, 420.0, 10.0, STEEL_D)
    # output-shaft stripe (rotation indicator)
    def stripe(cv):
        for zz0, zz1 in ((420.0, 466.0),):
            ph = ao % (2 * math.pi)
            if not (0.1 < ph < math.pi - 0.1 or True):
                return
            vis = math.sin(ph)
            if vis < 0:
                continue
            x = 10 * math.cos(ph)
            P = pj(np.array([x, x]), np.array([-10 * vis * 0.8, -10 * vis * 0.8]), np.array([zz0, zz1]))
            cv.drawLine(*P[0], *P[1], paint(YEL, a=0.8 * vis, stroke=2.6 * pj.s))
    items.append((445.0, stripe))

    # gears
    def g_items(st, key, rim_o=None, glow_o=0.0, rim_c=None, glow_c=0.0, bore=0.0, bore_c=AMBER):
        z = st["z"]
        (ro, no), (rc, nc) = st["o"], st["c"]
        ang_o = an["in"] if key == "in" else an["o" + key]
        ang_c = an["c"] if key == "in" else an["c" + key]
        base_o = STEEL if key == "in" else C_OUT
        items.append((z + 0.2, lambda cv: draw_gear(cv, pj, 0.0, CD, z, rc, nc, ang_c, C_COUNTER, rim=rim_c, glow=glow_c)))
        items.append((z, lambda cv: draw_gear(cv, pj, 0.0, 0.0, z, ro, no, ang_o, base_o, rim=rim_o, glow=glow_o,
                                              bore_c=bore_c, bore_a=bore)))

    rim_hook = YEL if h_even > 0.02 else None
    for key, st in (("in", IN), ("3", G3), ("2", G2), ("1", G1)):
        out_side = key != "in"
        ho = 0.0
        rim_o = rim_c = None
        go = gc = 0.0
        if out_side and h_even > 0.02:
            rim_o, go = YEL, h_even
        if h_cnt > 0.02:
            rim_c, gc = YEL, h_cnt
        if out_side and h_free > 0.02:
            rim_o, go = AMBER, h_free * 0.6
        if key == "1" and h_small > 0.02:
            rim_c, gc = YEL, h_small
        if key == "1" and h_big > 0.02:
            rim_o, go = YEL, h_big
        if key == "1" and h_drive > 0.02 and t > T_OUT_W:
            rim_o, go = RED, 0.6 * h_drive * (1 - current.ending_k(t))
            rim_c, gc = RED, 0.6 * h_drive
        if key in ("2", "3") and h_idle_others > 0.02:
            rim_o, go = CYAN, h_idle_others * 0.7
        if h_meshed > 0.02 and rim_o is None:
            rim_o, go = GREEN, h_meshed * 0.5
            rim_c, gc = GREEN, h_meshed * 0.5
        bore = h_free if out_side else 0.0
        g_items(st, key, rim_o, go, rim_c, gc, bore)

    # 1st gear: synchro cone + dog teeth on its near face
    z1f = G1["z"] - GW / 2
    def dog(cv):
        heat = rub
        extrude(cv, pj, gear_prof(0.0, 0.0, 27.0, 14, an["o1"], h=5.0), z1f - 10, z1f, C_OUT,
                rim=mix(C_OUT, RED, win(t, T_SLAM - 0.1, T_GRINDING + 0.6)), rim_w=1.6,
                rim_glow=win(t, T_SLAM - 0.1, T_GRINDING + 0.6))
    items.append((z1f - 5, dog))

    def cone(cv):
        rev(cv, pj, "z", (0.0, 0.0), [z1f - 16, z1f - 10], [21.0, 25.0], mix(C_OUT, hx("#ff9a3a"), 0.6 * rub), n=40,
            edge=mix(shade(C_OUT, 0.3), AMBER, rub), glow=rub)
    items.append((z1f - 13, cone))

    def ring(cv):
        hl = win(t, T_SYNCHRO - 0.1, T_SAME + 0.6, 0.2, 0.4)
        rev(cv, pj, "z", (0.0, 0.0), [zr, zr + 12], [30.0, 30.0], mix(C_BRASS, hx("#ffcf7a"), 0.4 * rub), n=48,
            edge=mix(shade(C_BRASS, 0.35), YEL, hl), edge_w=1.6 + 1.4 * hl, glow=hl)
    items.append((zc + 1.0, ring))     # always just beyond the collar

    def collar(cv):
        hl = win(t, T_COLLAR_W - 0.1, T_LOCKED_W + 1.0, 0.2, 0.4) + win(t, T_SLIDES - 0.1, T_SLIDES + 0.9, 0.2, 0.3)
        hl = clamp(hl)
        lk = clamp(ease(lin(t, T_LOCK, T_LOCK + 0.3)))
        edge = mix(mix(shade(C_COLLAR, 0.3), YEL, hl), RED, lk * (1 - current.ending_k(t)))
        rev(cv, pj, "z", (0.0, 0.0), [zc - 17, zc - 8, zc - 8, zc + 8, zc + 8, zc + 17], [33, 33, 27.5, 27.5, 33, 33],
            C_COLLAR, n=56, edge=edge, edge_w=1.6 + 1.2 * max(hl, lk), glow=max(hl, lk) * 0.8)
        # spline marks on the visible face so its rotation reads
        for k in range(10):
            th = ao + 2 * math.pi * k / 10
            p0 = pj(29 * math.cos(th), 29 * math.sin(th), zc - 17)
            p1 = pj(33 * math.cos(th), 33 * math.sin(th), zc - 17)
            cv.drawLine(*p0, *p1, paint(shade(C_COLLAR, 0.45), stroke=2 * pj.s))
    items.append((zc, collar))

    def fork(cv):
        k = ease(lin(t, T_FORK - 0.4, T_FORK))
        if k <= 0:
            return
        hl = win(t, T_FORK - 0.1, T_SLIDES + 1.0, 0.2, 0.4)
        extrude(cv, pj, FORK, zc - 4, zc + 4, hx("#5d6b80"), alpha=k, rim=mix(hx("#7d8ba0"), YEL, hl), rim_w=1.6,
                rim_glow=hl)
    items.append((zc - 0.5, fork))

    def rail(cv):
        k = ease(lin(t, T_FORK - 0.4, T_FORK))
        if k > 0:
            rev(cv, pj, "z", (0.0, -110.0), [230, 430], [6, 6], STEEL_D, alpha=k, n=24)
    items.append((431.0, rail))

    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    for _, fn in sorted(items, key=lambda x: -x[0]):
        fn(cv)
    # sparks / friction heat at the synchro contact
    if rub > 0:
        rng = np.random.default_rng(int(t * 30))
        c = pj(0.0, 0.0, z1f - 12)
        for _ in range(14):
            th = rng.uniform(0, 2 * np.pi)
            rr = rng.uniform(26, 44)
            p = pj(rr * math.cos(th), rr * math.sin(th), z1f - 12)
            cv.drawCircle(p[0], p[1], rng.uniform(1.5, 3.2) * pj.s, paint(hx("#ffcf6a"), a=rub * rng.uniform(0.4, 1)))
        cv.drawCircle(c[0], c[1], 40 * pj.s, paint(AMBER, a=0.25 * rub, blur=18 * pj.s))
    # grind flash (what would happen without a synchro)
    kg = win(t, T_SLAM - 0.05, T_GRINDING + 0.5, 0.1, 0.4)
    if kg > 0:
        c = pj(0.0, 0.0, z1f - 6)
        flick = 0.6 + 0.4 * math.sin(t * 60)
        cv.drawCircle(c[0], c[1], 46 * pj.s, paint(RED, a=0.35 * kg * flick, blur=16 * pj.s))
    # power path once in gear
    kp = ease(lin(t, T_DRIVES - 0.2, T_WHEELS + 0.4)) * (1 - ease(lin(t, T_EVERY2 + 0.2, T_EVERY2 + 0.9)))
    kp += win(t, T_OUTRO + 0.2, T_END, 0.3, 0.3) * 0.0
    if kp > 0:
        path = np.array([pj(0, 0, -60), pj(0, 0, 0), pj(0, 39, 0), pj(0, CD, 0), pj(0, CD, 390), pj(0, 60, 390),
                         pj(0, 0, 390), pj(0, 0, 470)])
        brand.curve(cv, resample(path, 200), RED, a=0.85 * clamp(kp), prog=eout(lin(t, T_DRIVES - 0.2, T_WHEELS + 0.3)),
                    width=5)
    cv.restore()
    return pj


# ================================================================== overlays
def draw_labels(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return
    t_parts_out = T_RATIO + 0.2
    brand.label(cv, t, "INPUT · FROM ENGINE", tuple(pj(0, 0, -45)), (80, 1270), STEEL, T_ENGINE - 0.05, t_parts_out)
    brand.label(cv, t, "COUNTERSHAFT", tuple(pj(0, CD + 10, 300)), (560, 1270), C_COUNTER, T_COUNTER - 0.05, t_parts_out)
    brand.label(cv, t, "OUTPUT SHAFT", tuple(pj(0, -10, 455)), (930, 400), C_OUT, T_OUTPUT - 0.05, t_parts_out,
                align="right")
    k = win(t, T_FREELY - 0.05, t_parts_out + 0.4, 0.25, 0.3)
    if k > 0:
        for st in (G3, G2, G1):
            p = pj(0, -st["o"][0] - 14, st["z"] - GW / 2)
            pill(cv, p[0], p[1] - 10, "FREE", font("inter_xb", 22), INK, border=AMBER, a=k, align="center", tracking=2)
    # gear names during the ratio beat
    k = win(t, T_RATIO_W - 0.1, T_COLLAR + 0.4, 0.25, 0.3)
    if k > 0:
        for st, nm in ((G3, "3RD"), (G2, "2ND"), (G1, "1ST")):
            p = pj(0, -st["o"][0] - 14, st["z"] - GW / 2)
            pill(cv, p[0], p[1] - 10, nm, font("inter_xb", 24), INK, border=YEL if nm == "1ST" else MUTED, a=k,
                 align="center", tracking=2)
    t_cl_out = T_GRIND
    brand.label(cv, t, "COLLAR", tuple(pj(0, -33, Z_COLLAR_HOME - 17)), (90, 470), C_COLLAR, T_COLLAR_W - 0.05,
                T_PRESS + 0.2)
    brand.label(cv, t, "SPLINED TO OUTPUT SHAFT", tuple(pj(0, -12, 280)), (90, 1270), C_COLLAR, T_LOCKED_W - 0.05,
                T_PRESS + 0.2)
    brand.label(cv, t, "SHIFT FORK", tuple(pj(-6, -85, z_collar(t))), (90, 520), YEL, T_FORK - 0.05, t_cl_out + 0.3)
    brand.label(cv, t, "SYNCHRO RING", tuple(pj(-30 * 0.7, 30 * 0.7, z_ring(t))), (90, 1270), C_BRASS, T_SYNCHRO - 0.05,
                T_SLIDE_IN)
    brand.label(cv, t, "DOG TEETH", tuple(pj(20, 18, G1["z"] - GW / 2 - 6)), (930, 1270), C_OUT, T_GRIND + 0.1,
                T_SLIDE_IN + 0.8, align="right")
    k = win(t, T_FRICTION - 0.05, T_SLIDE_IN, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1345, "FRICTION MATCHES THE SPEEDS", font("inter_xb", 28), INK, border=AMBER, a=k, align="center",
             tracking=2)
    k = win(t, T_EVERY2 - 0.1, T_OUTRO + 0.6, 0.25, 0.3)
    if k > 0:
        for st in (G3, G2):
            p = pj(0, -st["o"][0] - 14, st["z"] - GW / 2)
            pill(cv, p[0], p[1] - 10, "FREEWHEELING", font("inter_xb", 20), INK, border=CYAN, a=k * kE, align="center",
                 tracking=1.5)
    k = win(t, T_WHEELS - 0.2, T_OUTRO + 0.6, 0.25, 0.3) * kE
    if k > 0:
        pass
    brand.label(cv, t, "TO THE WHEELS", tuple(pj(0, 0, 468)), (930, 540), RED, T_WHEELS - 0.2, T_OUTRO + 0.6,
                align="right")


def draw_hook(cv, t):
    k = 1 - ease(lin(t, T_HOOK_OUT + 0.1, T_WHAT + 0.4))
    if k <= 0:
        return
    n = 8
    lit = eout(lin(t, 0.15, T_EVEN + 0.2))
    draw_text(cv, f"{int(round(n * lit))} / 8", 540, 1270, font("inter_blk", 96), INK, a=k, align="center")
    draw_text(cv, "GEARS TURNING · IN NEUTRAL", 540, 1322, font("inter_xb", 28), AMBER, a=k, align="center",
              tracking=4)


def draw_what(cv, t):
    k = win(t, T_NEVER - 0.1, T_PARTS + 0.1, 0.25, 0.3)
    if k <= 0:
        return
    k2 = eout(lin(t, T_MESHED - 0.1, T_MESHED + 0.2))
    brand.bullet(cv, 300, 1300, "GEARS SLIDE IN AND OUT", False, a=k)
    brand.bullet(cv, 300, 1365, "ALWAYS MESHED IN PAIRS", True, a=k * k2)


def draw_ratio(cv, t):
    k = win(t, T_TRADES - 0.1, T_NEUTRAL - 0.1, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1295, "SMALL TURNS BIG", font("inter_xb", 30), INK, border=YEL, a=k, align="center", tracking=2)
        pill(cv, 540, 1360, "LESS SPEED · MORE PULLING POWER", font("inter_xb", 28), INK, border=YEL, a=k,
             align="center", tracking=2)


def draw_header(cv, t):
    k = win(t, T_PARTS + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    if t < T_PRESS:
        txt, c = "NEUTRAL", CYAN
    elif t < T_RUBS:
        txt, c = "CLUTCH IN", AMBER
    elif t < T_LOCK:
        txt, c = "SYNCING", AMBER
    elif t < T_OUT_W:
        txt, c = "1ST LOCKED", RED
    else:
        txt, c = "IN GEAR · DRIVING", RED
    brand.status_pill(cv, k, txt, c)
    kr = win(t, T_STILL - 0.1, T_LOCK + 1.2, 0.3, 0.3) * k
    if kr > 0:
        g = speed_gap(t)
        brand.readout(cv, kr, f"{int(round(g * 100))}%", "SPEED DIFFERENCE", frac=g, bar_color=mix(GREEN, RED, g))
    brand.note(cv, "ANIMATION SLOWED", k * 0.9, dy=0 if kr <= 0 else 0)


def draw_outro(cv, t):
    k = win(t, T_DOUBLE - 0.3, T_END + 0.1, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1330, "NO SYNCHRO = DOUBLE CLUTCHING", font("inter_xb", 30), INK, border=MUTED, a=k,
             align="center", tracking=2)


def draw_stamps(cv, t):
    brand.stamp(cv, t, "NEUTRAL", T_NEUTRAL, center=(540, 1320), color=CYAN, bg=hx("#06202a"))
    brand.stamp(cv, t, "GRIND!", T_SLAM + 0.15, center=(540, 1320))
    brand.stamp(cv, t, "LOCKED", T_LOCK, center=(540, 1320))


def draw(cv, t):
    a = 1.0
    draw_gearbox(cv, t, a)
    draw_hook(cv, t)
    draw_what(cv, t)
    draw_ratio(cv, t)
    draw_labels(cv, t)
    draw_header(cv, t)
    draw_outro(cv, t)
    draw_stamps(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_LOCK
MUSIC_START = T_WHAT


def sound():
    sfx = [(0.05, "spool", 0.35), (T_HOOK_OUT - 0.1, "whoosh_big", 0.6),
           (T_NEVER + 0.05, "tick", 0.25), (T_MESHED + 0.05, "tick", 0.25),
           (T_COUNTER, "tick", 0.2), (T_OUTPUT, "tick", 0.2),
           (T_NEUTRAL, "impact", 0.35), (T_PRESS - 0.3, "whoosh_up", 0.45), (T_SLIDES + 0.4, "clunk", 0.4),
           (T_SLAM + 0.1, "hiss", 0.55), (T_RUBS + 0.1, "hiss", 0.35), (T_LOCK, "clunk", 0.65), (T_LOCK, "impact", 0.5),
           (T_OUT_W - 0.4, "whoosh_down", 0.4), (T_OUT_W, "spool", 0.45)]
    return {"build": (T_KEY, T_LOCK), "drop": (T_LOCK, T_OUTRO - 0.05), "sfx": sfx}
