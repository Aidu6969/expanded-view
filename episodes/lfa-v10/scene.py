"""LFA V10 visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (ortho 3/4 view; X across the engine, Y down, z along the crankshaft; units mm, 1LR-GUE where sourced):
  72-degree V10: left bank axis at -36 deg from vertical, right bank at +36 deg
  bore 88, stroke 79 (throw 39.5); rod length 140 is illustrative (not published)
  five crank throws at 144-degree spacing (0, 144, 288, 72, 216), each shared by one left and one right rod
  -> every cylinder's TDC falls on a multiple of 72 deg, and over 720 deg the ten firing TDCs are exactly
     72 deg apart (checked in check_physics). Exact slider-crank kinematics on each tilted bank.
  valves: intake opens on the intake stroke, exhaust on the exhaust stroke of each cylinder's own cycle.
The firing order on screen follows this model; the real 1LR-GUE firing order is not claimed.
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, pipe, flow, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_NEEDLE = F("hook", "needle")
T_KEEP = F("hook", "keep")
T_WHAT = L("what")["start"]
T_FOUR = F("what", "four")
T_LITRE = F("what", "litre")
T_V10 = F("what", "v10")
T_LEXUS = F("what", "lexus")
T_WHY = F("what", "why")
T_SOUNDS = F("what", "sounds")
T_LIGHT = L("light")["start"]
T_MOVING = F("light", "moving")
T_LIGHTW = F("light", "light.")
T_VALVES = F("light", "valves")
T_TITAN = F("light", "titanium,")
T_EVERY = F("light", "every")
T_THROTTLE = F("light", "throttle,")
T_INTAKE1 = F("light", "intake.")
T_ANGLE = L("angle")["start"]
T_ANGLE_W = F("angle", "angle")
T_BANKS = F("angle", "banks.")
T_72A = F("angle", "seventy")
T_RANDOM = F("angle", "random.")
T_MATH = L("math")["start"]
T_TURNS = F("math", "turns,")
T_720 = F("math", "seven")
T_ONCE = F("math", "once.")
T_DIVIDE = F("math", "divide")
T_TEN = F("math", "ten")
T_72B = F("math", "seventy")
T_EVEN = L("even")["start"]
T_FIRES = F("even", "fires")
T_EVENLY = F("even", "evenly.")
T_LUMPY = F("even", "lumpy")
T_SMOOTH = F("even", "smooth,")
T_SCREAM = F("even", "scream.")
T_YAM = L("yamaha")["start"]
T_YAMW = F("yamaha", "yamaha's")
T_SURGE = F("yamaha", "surge")
T_RESON = F("yamaha", "resonate")
T_INSTR = F("yamaha", "instrument,")
T_DUCTS = F("yamaha", "ducts")
T_CABIN = F("yamaha", "cabin.")
T_KEY = L("key")["start"]
T_FLOOR = F("key", "floor")
T_SWEEP = F("key", "idle")              # the real-time idle -> 9,000 sweep starts on "idle"
T_IDLE = F("key", "idle")
T_9000 = F("key", "nine")
T_SIX = F("key", "six")
T_750 = F("key", "seven")
T_FIRINGS = F("key", "firings")
T_LEX2 = F("key", "lexus")
T_DIGITAL = F("key", "digital")
T_TACH = F("key", "tach.")
T_OUTRO = L("outro")["start"]

# ================================================================== geometry (mm)
R_CR, ROD = 39.5, 140.0
BORE_R = 44.0
PIN_H, PIST_H = 28.0, 46.0
DECK = R_CR + ROD + PIN_H + 6.0            # crank axis -> deck along the bank axis
HEAD_H = 70.0
PITCH = 105.0
NROW = 5
ZROW = [(j - 2) * PITCH for j in range(NROW)]
ZOFF = 13.0                                 # left rod in front of right rod on each shared pin
BETA = {0: math.radians(-36.0), 1: math.radians(36.0)}     # 0 = left bank, 1 = right bank
THROW = [math.radians((144.0 * j) % 360) for j in range(NROW)]
C_ROD = hx("#7d889b")
C_TI = hx("#b9c7dc")                        # titanium valves: light blue-steel


def bank_u(b):
    be = BETA[b]
    return np.array([math.sin(be), -math.cos(be)])


def bank_v(b):
    be = BETA[b]
    return np.array([math.cos(be), math.sin(be)])


def inner(b):
    """Lateral sign (along bank_v) pointing into the valley of the V."""
    return 1.0 if b == 0 else -1.0


def bank_pt(b, s, w):
    return s * bank_u(b) + w * bank_v(b)


def cyl_z(b, j):
    return ZROW[j] + (-ZOFF if b == 0 else ZOFF)


def pin_dist(a, b):
    """Crank centre -> piston pin distance along bank b's axis for crank pin angle a (from vertical, clockwise)."""
    d = a - BETA[b]
    return R_CR * math.cos(d) + math.sqrt(ROD ** 2 - (R_CR * math.sin(d)) ** 2)


# firing: cylinder (b, j) is at TDC when phi + THROW[j] == BETA[b] (mod 360). Left bank fires on that TDC,
# right bank on the TDC one turn later -> ten firings exactly 72 deg apart over 720 deg.
CYLS = [(b, j) for b in (0, 1) for j in range(NROW)]
FIRE_AT = {}
for b, j in CYLS:
    base = (BETA[b] - THROW[j]) % (2 * math.pi)
    FIRE_AT[(b, j)] = base + (0.0 if b == 0 else 2 * math.pi)
ORDER = sorted(CYLS, key=lambda c: FIRE_AT[c])
CYL_NO = {c: (c[1] + 1 if c[0] == 0 else c[1] + 6) for c in CYLS}   # 1-5 left bank, 6-10 right bank


def check_physics():
    bad = []
    fa = sorted(FIRE_AT.values())
    gaps = np.diff(fa + [fa[0] + 4 * math.pi])
    if np.max(np.abs(gaps - math.radians(72.0))) > 1e-9:
        bad.append("firing not even at 72 deg")
    for b, j in CYLS:
        if abs(pin_dist(FIRE_AT[(b, j)] + THROW[j], b) - (R_CR + ROD)) > 1e-6:
            bad.append("firing not at TDC")
    if abs(math.degrees(BETA[1] - BETA[0]) - 72.0) > 1e-9:
        bad.append("bank angle not 72")
    if R_CR + ROD + PIN_H >= DECK:
        bad.append("piston hits head")
    return bad


assert not check_physics(), check_physics()

# ================================================================== crank angle vs time (visual, slowed)
REV = 2 * math.pi


def _w(t):
    return smooth(t, [(0.0, REV * 0.6), (T_WHAT, REV * 0.6), (T_LIGHT, REV * 0.35), (T_ANGLE, REV * 0.12),
                      (T_ANGLE + 0.6, REV * 0.05), (T_720 - 0.3, REV * 0.05), (T_720 + 0.5, REV * 0.25),
                      (T_EVEN, REV * 0.3), (T_SMOOTH, REV * 0.5), (T_YAM, REV * 0.6), (T_KEY, REV * 1.2),
                      (T_TOTAL, REV * 1.2)])


def _build():
    dt = 1 / 600
    ts = np.arange(0, T_TOTAL + 1, dt)
    w = np.array([_w(x) for x in ts])
    ph = np.concatenate([[0.0], np.cumsum(w[:-1]) * dt]) + 0.2
    return ts, ph


_TS, _PH = _build()


def phi_at(t):
    return float(np.interp(t, _TS, _PH))


def cyc(t, c):
    """Cylinder c's own cycle angle 0..4pi, 0 = firing TDC (power 0..pi, exhaust pi..2pi, intake 2pi..3pi,
    compression 3pi..4pi)."""
    return (phi_at(t) - FIRE_AT[c]) % (4 * math.pi)


def rpm_display(t):
    """Engine speed the scene stands for (the animation is slowed). Hook: rev blips idle -> 9,000 in 0.6 s."""
    if t < T_WHAT:
        r = 1000.0
        for tb in (0.35, 2.15):
            x = t - tb
            if 0 <= x < 0.6:
                r = 1000 + 8000 * (x / 0.6) ** 0.8
            elif 0.6 <= x < 1.5:
                r = 9000 - 8000 * ease(lin(x, 0.6, 1.5))
        return r
    if t < T_SWEEP - 0.05:
        return smooth(t, [(T_WHAT, 1000), (T_WHAT + 1.0, 3500), (T_ANGLE, 3000), (T_ANGLE + 1.0, 1100),
                          (T_EVEN, 1100), (T_SMOOTH, 6000), (T_YAM + 0.8, 4500), (T_CABIN, 4500), (T_KEY - 0.2, 1000),
                          (T_SWEEP - 0.05, 1000)])
    x = t - T_SWEEP
    if x < 0.6:
        return 1000 + 8000 * clamp(x / 0.6) ** 0.8
    if t < T_TACH + 0.4:
        return 9000.0
    return smooth(t, [(T_TACH + 0.4, 9000), (T_OUTRO + 0.6, 3000), (T_TOTAL, 2500)])


# ================================================================== camera
CAM_HOOK = (530.0, 960.0, 1.40, 72.0, 20.0)
CAM_MAIN = (530.0, 975.0, 1.45, 72.0, 20.0)
CAM_FRONT = (540.0, 985.0, 1.58, 86.0, 10.0)
CAM_TOP = (540.0, 1010.0, 1.40, 70.0, 28.0)


def cam_v(t):
    keys = [(0.0, CAM_HOOK), (T_WHAT, CAM_HOOK), (T_WHAT + 1.2, CAM_MAIN), (T_ANGLE - 0.2, CAM_MAIN),
            (T_ANGLE + 0.9, CAM_FRONT), (T_EVEN - 0.3, CAM_FRONT), (T_EVEN + 0.9, CAM_MAIN), (T_YAM - 0.1, CAM_MAIN),
            (T_YAM + 0.9, CAM_TOP), (T_TOTAL, CAM_TOP)]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease(lin(t, t0, t1))
            return np.array(a) * (1 - k) + np.array(b) * k
    return np.array(keys[-1][1])


def cam(t):
    ox, oy, s, yw, pt = cam_v(t)
    return Proj(ox, oy, s, yaw=yw, pitch=pt)


def P3(b, s, w, z):
    q = bank_pt(b, s, w)
    return (q[0], q[1], z)


# ================================================================== highlight helpers
def hl(t, t0, t1):
    return win(t, t0 - 0.1, t1, 0.2, 0.4)


def engine_k(t):
    """Engine visibility: hidden under the hook (gauge) and during the digital-tach beat."""
    k_in = eout(lin(t, T_HOOK_OUT - 0.1, T_WHAT + 0.4))
    k_out = 1 - ease(lin(t, T_KEY - 0.3, T_KEY + 0.3))
    return k_in * k_out * (1 - current.ending_k(t))


def flash_k(t, c):
    a = cyc(t, c)
    return clamp(1 - a / math.radians(60)) if a < math.radians(60) else 0.0


def valve_lift(t, c):
    a = cyc(t, c)
    li = math.sin(a - 2 * math.pi) if 2 * math.pi < a < 3 * math.pi else 0.0
    le = math.sin(a - math.pi) if math.pi < a < 2 * math.pi else 0.0
    return 9.0 * li, 9.0 * le


def order_light(t, c):
    """Cylinders light one by one in firing order on 'divide by ten'."""
    i = ORDER.index(c)
    t0 = T_TEN - 0.2 + 0.09 * i
    return eout(lin(t, t0, t0 + 0.2)) * win(t, T_TEN - 0.3, T_EVEN + 0.2, 0.1, 0.4)


# ================================================================== engine
def web_prof(ang, n=56):
    prof = []
    for th in np.linspace(0, 2 * np.pi, n, endpoint=False):
        d = (th - ang) % (2 * np.pi)
        r = 22 + (R_CR + 4) * max(0.0, math.cos(d)) ** 6 + 38 * max(0.0, -math.cos(d)) ** 0.7
        prof.append((r * math.cos(th), r * math.sin(th)))
    return np.array(prof)


def head_prof(b):
    s0, s1 = DECK, DECK + HEAD_H
    return np.array([bank_pt(b, s0, -58), bank_pt(b, s0, 58), bank_pt(b, s1, 58), bank_pt(b, s1, -58)])


def runner_pts(pj, b, j):
    """Intake runner for cylinder (b, j): from the head's valley side up into the surge tank."""
    z = cyl_z(b, j)
    p0 = bank_pt(b, DECK + HEAD_H * 0.55, inner(b) * 58)
    sx = -1 if b == 0 else 1
    pts3 = [(p0[0], p0[1]), (p0[0] - sx * 18, p0[1] - 40), (sx * 40, -296), (sx * 34, -318)]
    return spline(pj(np.array([p[0] for p in pts3]), np.array([p[1] for p in pts3]), np.full(4, z)), 40)


TANK = np.array([[-70, -345], [70, -345], [70, -306], [-70, -306]], float)
TANK_Z = (ZROW[0] - 70, ZROW[-1] + 70)


def throttle_k(t, c):
    i = ORDER.index(c)
    t0 = T_THROTTLE - 0.25 + 0.06 * i
    return eout(lin(t, t0, t0 + 0.2)) * win(t, T_THROTTLE - 0.3, T_ANGLE + 0.2, 0.1, 0.4)


def draw_engine(cv, t):
    pj = cam(t)
    kE = engine_k(t)
    if kE <= 0:
        return pj
    ph = phi_at(t)
    cv.saveLayerAlpha(None, int(255 * kE))
    h_mov = hl(t, T_MOVING, T_VALVES)
    h_val = hl(t, T_VALVES, T_EVERY + 0.4)
    h_tank = hl(t, T_SURGE, T_KEY)
    ang_k = win(t, T_ANGLE_W - 0.2, T_EVEN + 0.3, 0.3, 0.4)

    # ---- block front face (glass V) at the front of the engine
    zf = ZROW[0] - 70
    vpoly = [bank_pt(0, DECK, -58), bank_pt(0, 60, -60), (-40, 70), (40, 70), bank_pt(1, 60, 60),
             bank_pt(1, DECK, 58), bank_pt(1, DECK, -58), (0, -40), bank_pt(0, DECK, 58)]
    vpoly = np.array(vpoly, float)

    # ---- far glass: back face + liners
    vb = pj(vpoly[:, 0], vpoly[:, 1], np.full(len(vpoly), ZROW[-1] + 70))
    cv.drawPath(poly_path(vb), paint(hx("#6f86a8"), a=0.06))
    cv.drawPath(poly_path(vb), paint(hx("#7d8aa0"), a=0.35, stroke=1.3 * pj.s))

    # ---- moving parts, painter-sorted per row (far rows first)
    items = []
    for j in range(NROW):
        zc = ZROW[j]
        dz = pj.depth(0, 0, zc)
        items.append((dz + 0.2, "row", j))
    items.sort(key=lambda x: -x[0])
    for _, _, j in items:
        zc = ZROW[j]
        a = ph + THROW[j]
        cpin = np.array([R_CR * math.sin(a), -R_CR * math.cos(a)])
        ang = math.atan2(cpin[1], cpin[0])
        web_c = mix(STEEL_D, YEL, 0.3 * h_mov)
        # main journals between rows
        cyl3(cv, pj, (0, 0, zc + PITCH / 2 - 10), (0, 0, zc + 34), 15, STEEL, n=24)
        extrude(cv, pj, web_prof(ang), zc + 26, zc + 38, web_c)
        cyl3(cv, pj, (cpin[0], cpin[1], zc + 27), (cpin[0], cpin[1], zc - 27), 12, STEEL, n=24)
        # the two rods + pistons on this pin: right bank (behind on the pin) first
        for b in (1, 0):
            c = (b, j)
            z = cyl_z(b, j)
            sd = pin_dist(a, b)
            ppin = bank_pt(b, sd, 0)
            v = ppin - cpin
            v /= np.linalg.norm(v)
            nrm = np.array([-v[1], v[0]])
            ol = order_light(t, c)
            rod_c = mix(C_ROD, YEL, 0.5 * h_mov)
            rod = [cpin + nrm * 12, ppin + nrm * 7, ppin - nrm * 7, cpin - nrm * 12]
            extrude(cv, pj, np.array(rod), z - 6, z + 6, rod_c)
            extrude(cv, pj, circle_prof(cpin[0], cpin[1], 17, 28), z - 6, z + 6, rod_c)
            fk = flash_k(t, c)
            pc = mix(STEEL, YEL, 0.35 * max(h_mov, ol))
            pc = mix(pc, AMBER, 0.5 * fk)
            edge = AMBER if fk > 0.05 else (YEL if max(h_mov, ol) > 0.02 else None)
            top = sd + PIN_H
            cyl3(cv, pj, P3(b, top - PIST_H, 0, z), P3(b, top, 0, z), BORE_R - 2, pc, edge=edge,
                 edge_w=2 + 1.5 * max(fk, ol), glow=max(fk, ol, h_mov), n=36)
            # combustion flash between crown and head
            if fk > 0:
                q = pj(*P3(b, (top + DECK) / 2 + 3, 0, z))
                cv.drawCircle(q[0], q[1], 40 * pj.s, paint(hx("#ff7a2a"), a=0.65 * fk, blur=16 * pj.s))
                cv.drawCircle(q[0], q[1], 16 * pj.s, paint(hx("#ffe2a8"), a=0.9 * fk, blur=5 * pj.s))
            # liner (glass)
            cyl3(cv, pj, P3(b, 120, 0, z), P3(b, DECK, 0, z), BORE_R + 3, hx("#6b7c96"), fill_a=0.10,
                 edge=hx("#6b7c96"), edge_w=1.0, cap=False, n=36)
        extrude(cv, pj, web_prof(ang), zc - 38, zc - 26, web_c)
        if j == 0:
            cyl3(cv, pj, (0, 0, zc - 34), (0, 0, zc - PITCH / 2 - 20), 15, STEEL, n=24)

    # ---- heads (glass) and valves
    for b in (0, 1):
        hc = mix(hx("#55606f"), YEL, 0.25 * h_val)
        extrude(cv, pj, head_prof(b), ZROW[0] - 62, ZROW[-1] + 62, hc, alpha=0.42,
                rim=YEL if h_val > 0.02 else None, rim_w=1.4, rim_glow=h_val)
    for b in (0, 1):
        for j in range(NROW):
            c = (b, j)
            z = cyl_z(b, j)
            li, le = valve_lift(t, c)
            for w, lift, isint in ((inner(b) * 19, li, True), (-inner(b) * 19, le, False)):
                vc = mix(C_TI, YEL, 0.6 * h_val)
                if isint and lift > 0.5:
                    vc = mix(vc, CYAN, 0.5)
                if (not isint) and lift > 0.5:
                    vc = mix(vc, AMBER, 0.5)
                s_face = DECK + 3 - lift
                q0, q1 = pj(*P3(b, s_face, w, z)), pj(*P3(b, DECK + 58, w, z))
                cv.drawLine(q0[0], q0[1], q1[0], q1[1], paint(vc, stroke=3.2 * pj.s))
                cyl3(cv, pj, P3(b, s_face - 3, w, z), P3(b, s_face, w, z), 14, vc, n=24,
                     edge=YEL if h_val > 0.02 else None, glow=h_val)

    # ---- intake: runners with throttles, surge tank
    for b in (0, 1):
        for j in range(NROW):
            c = (b, j)
            pts = runner_pts(pj, b, j)
            tk = throttle_k(t, c)
            li, _ = valve_lift(t, c)
            pipe(cv, pts, 16 * pj.s, mix(hx("#6b7c96"), YEL, 0.5 * tk), glass=True)
            if li > 0.5:
                flow(cv, pts[::-1], t, 160, 22, CYAN, r=3.5 * pj.s, a=clamp(li / 9))
            m = pts[len(pts) // 2]
            ang = math.radians(35 + 50 * clamp(rpm_display(t) / 9000))
            dx, dy = 10 * pj.s * math.cos(ang), 10 * pj.s * math.sin(ang)
            cv.drawLine(m[0] - dx, m[1] - dy, m[0] + dx, m[1] + dy, paint(mix(STEEL, YEL, tk), stroke=4 * pj.s))
            if tk > 0:
                cv.drawCircle(m[0], m[1], 15 * pj.s, paint(YEL, a=0.6 * tk, stroke=3 * pj.s, blur=3 * pj.s))
    tank_c = mix(hx("#4a5568"), AMBER, 0.55 * h_tank)
    extrude(cv, pj, TANK, TANK_Z[0], TANK_Z[1], tank_c, alpha=0.38 + 0.3 * h_tank,
            rim=AMBER if h_tank > 0.02 else None, rim_w=1.8, rim_glow=h_tank)

    # ---- near glass: front face of the block
    vf = pj(vpoly[:, 0], vpoly[:, 1], np.full(len(vpoly), zf))
    cv.drawPath(poly_path(vf), paint(hx("#6f86a8"), a=0.08))
    cv.drawPath(poly_path(vf), paint(hx("#8a9ab4"), a=0.6, stroke=1.5 * pj.s))

    # ---- 72-degree bank angle overlay on the front face
    if ang_k > 0:
        o = pj(0, 0, zf)
        for b in (0, 1):
            e = pj(*P3(b, DECK + HEAD_H + 30, 0, zf))
            p = paint(YEL, a=ang_k, stroke=4)
            p.setPathEffect(skia.DashPathEffect.Make([16, 10], 0))
            cv.drawLine(o[0], o[1], e[0], e[1], p)
        prog = eout(lin(t, T_72A - 0.3, T_72A + 0.5))
        th = np.linspace(BETA[0], BETA[0] + (BETA[1] - BETA[0]) * prog, 40)
        rr = 150.0
        P = pj(rr * np.sin(th), -rr * np.cos(th), np.full(40, zf))
        if prog > 0.02:
            cv.drawPath(poly_path(P, close=False), paint(YEL, a=0.5 * ang_k, stroke=12, blur=6))
            cv.drawPath(poly_path(P, close=False), paint(YEL, a=ang_k, stroke=5))
        kt = ang_k * eout(lin(t, T_72A, T_72A + 0.3))
        if kt > 0:
            q = pj(0, -rr - 40, zf)
            pill(cv, q[0], q[1], "72°", font("inter_blk", 46), INK, border=YEL, a=kt, align="center")
    cv.restore()
    return pj


# ================================================================== overlays
GC = (540.0, 870.0, 250.0)


def needle_rpm(t):
    """Illustration of a lagging needle: first-order lag (tau 0.35 s) behind the engine speed."""
    tau, dt = 0.35, 1 / 120
    n = 1000.0
    x = 0.0
    while x < t:
        n += (rpm_display(x) - n) * dt / tau
        x += dt
    return n


_NT = np.arange(0, 6.0, 1 / 60)
_NV = np.array([needle_rpm(x) for x in _NT])


def draw_hook(cv, t):
    k = 1 - ease(lin(t, T_HOOK_OUT + 0.1, T_WHAT + 0.5))
    if k <= 0:
        return
    cx, cy, R = GC
    r_eng = rpm_display(t)
    r_need = float(np.interp(t, _NT, _NV))
    brand.gauge(cv, cx, cy, R, r_need, vmax=10000, redline=9000, alpha=k,
                readout=f"{int(round(r_eng / 100) * 100):,}")
    ka0 = k
    rect = skia.Rect.MakeLTRB(cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8)
    cv.drawArc(rect, 135, 270 * r_eng / 10000, False, paint(AMBER, a=0.5 * ka0, stroke=16, blur=8))
    cv.drawArc(rect, 135, 270 * r_eng / 10000, False, paint(AMBER, a=ka0, stroke=9))
    lag = clamp((r_eng - r_need) / 2500)
    ka = k * eout(lin(t, T_NEEDLE - 0.2, T_NEEDLE + 0.2))
    pill(cv, 300, 1255, "ENGINE", font("inter_xb", 30), INK, border=AMBER, a=k, align="center", tracking=3,
         dot=AMBER)
    pill(cv, 780, 1255, "NEEDLE", font("inter_xb", 30), INK, border=mix(MUTED, RED, lag), a=ka, align="center",
         tracking=3, dot=hx("#ff6a3a"))
    kl = ka * win(t, T_KEEP - 0.3, T_HOOK_OUT + 0.4, 0.2, 0.3)
    if kl > 0:
        pill(cv, 540, 1350, "THE NEEDLE CAN'T KEEP UP", font("inter_xb", 32), INK, border=RED, a=kl,
             align="center", tracking=2)
    draw_text(cv, "ILLUSTRATION", 540, 1205, font("inter_sb", 19), MUTED, a=0.8 * k, align="center", tracking=3)


def draw_what(cv, t):
    k = win(t, T_FOUR - 0.2, T_LIGHT + 0.1, 0.3, 0.3)
    if k > 0:
        items = [("4.8 LITRE", eout(lin(t, T_LITRE - 0.2, T_LITRE + 0.1))),
                 ("V10", eout(lin(t, T_V10, T_V10 + 0.25))),
                 ("LEXUS LFA", eout(lin(t, T_LEXUS, T_LEXUS + 0.25)))]
        brand.chips(cv, k, 1290, items, center=True)
    kw = win(t, T_WHY - 0.1, T_LIGHT + 0.1, 0.25, 0.3)
    if kw > 0:
        pill(cv, 540, 1370, "WHY IT SOUNDS LIKE THAT", font("inter_xb", 30), INK, border=RED, a=kw, align="center",
             tracking=3)
    pj = cam(t)
    for b, j in CYLS:
        kn = eout(lin(t, T_V10 + 0.06 * CYL_NO[(b, j)], T_V10 + 0.06 * CYL_NO[(b, j)] + 0.25)) * \
            win(t, T_V10, T_MOVING, 0.1, 0.4) * engine_k(t)
        if kn > 0:
            q = pj(*P3(b, DECK + HEAD_H + 26, 0, cyl_z(b, j)))
            pill(cv, q[0], q[1], str(CYL_NO[(b, j)]), font("inter_blk", 26), INK, border=YEL, a=kn, align="center")


def draw_light(cv, t):
    brand.stamp(cv, t, "LIGHTWEIGHT", T_LIGHTW, dur=1.2, center=(540, 1300), color=YEL, bg=hx("#2a2205"))
    k = win(t, T_TITAN - 0.2, T_EVERY + 0.2, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "TITANIUM VALVES", font("inter_xb", 34), INK, border=C_TI, a=k, align="center",
             tracking=3)
    k = win(t, T_THROTTLE - 0.35, T_ANGLE + 0.1, 0.2, 0.35)
    if k > 0:
        pill(cv, 540, 1300, "10 THROTTLES", font("inter_xb", 34), INK, border=YEL, a=k, align="center",
             tracking=3)
        pill(cv, 540, 1376, "ONE PER CYLINDER", font("inter_xb", 26), INK, border=MUTED, a=k, align="center",
             tracking=3)


def draw_labels(cv, t):
    pj = cam(t)
    kE = engine_k(t)
    if kE <= 0:
        return
    pv = pj(*P3(0, DECK + 40, -inner(0) * 19, cyl_z(0, 0)))
    brand.label(cv, t, "TITANIUM VALVES", tuple(pv), (80, 560), C_TI, T_VALVES - 0.1, T_EVERY + 0.2)
    m = runner_pts(pj, 1, 0)
    m = m[len(m) // 2]
    brand.label(cv, t, "THROTTLE", tuple(m), (940, 600), YEL, T_THROTTLE - 0.1, T_ANGLE, align="right")
    a = phi_at(t) + THROW[0]
    sd = pin_dist(a, 0)
    pp = pj(*P3(0, sd + PIN_H, -BORE_R, cyl_z(0, 0)))
    brand.label(cv, t, "PISTONS + RODS", tuple(pp), (80, 1180), YEL, T_MOVING - 0.05, T_VALVES)
    q = pj(-92, -330, TANK_Z[0])
    brand.label(cv, t, "SURGE TANK", tuple(q), (80, 560), AMBER, T_SURGE - 0.05, T_DUCTS)
    brand.label(cv, t, "LEFT BANK", tuple(pj(*P3(0, DECK + HEAD_H, -58, ZROW[0] - 62))), (80, 470), CYAN,
                T_BANKS - 0.6, T_72A)
    brand.label(cv, t, "RIGHT BANK", tuple(pj(*P3(1, DECK + HEAD_H, 58, ZROW[0] - 62))), (940, 470), CYAN,
                T_BANKS - 0.4, T_72A, align="right")


def draw_angle(cv, t):
    brand.stamp(cv, t, "72 DEGREES", T_72A + 0.2, dur=1.5, center=(540, 1300), color=YEL, bg=hx("#2a2205"))
    k = win(t, T_RANDOM - 0.15, T_MATH + 0.1, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "NOT RANDOM", font("inter_xb", 34), INK, border=RED, a=k, align="center", tracking=4)


# ---- firing timeline (math + even beats)
BX0, BX1, BY = 120.0, 900.0, 1290.0


def fx(deg):
    return BX0 + (BX1 - BX0) * deg / 720.0


def draw_math(cv, t):
    k = win(t, T_MATH - 0.1, T_YAM + 0.1, 0.35, 0.4) * (1 - current.ending_k(t))
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(BX0 - 40, BY - 185, BX1 + 40, BY + 70), 22, 22)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.86))
    cv.drawRRect(rr, paint(hx("#2a3446"), stroke=2))
    # two crank turns
    k2 = eout(lin(t, T_TURNS - 0.3, T_TURNS + 0.3))
    for i, lab in enumerate(("TURN 1", "TURN 2")):
        x0, x1 = fx(360 * i) + 4, fx(360 * (i + 1)) - 4
        cv.drawLine(x0, BY, x0 + (x1 - x0) * k2, BY, paint(mix(CYAN, YEL, 0.2 * i), stroke=10,
                                                          cap=skia.Paint.kRound_Cap))
        draw_text(cv, lab, (x0 + x1) / 2, BY - 22, font("inter_xb", 22), MUTED, a=k2, align="center", tracking=3)
    k7 = eout(lin(t, T_720 - 0.1, T_720 + 0.3))
    draw_text(cv, "0°", fx(0), BY + 44, font("inter_b", 24), MUTED, a=k7, align="center")
    draw_text(cv, "360°", fx(360), BY + 44, font("inter_b", 24), MUTED, a=k7, align="center")
    draw_text(cv, "720°", fx(720), BY + 44, font("inter_b", 24), INK, a=k7, align="center")
    draw_text(cv, "2 TURNS = 720°", BX0, BY - 140, font("inter_xb", 30), INK, a=k7 * (1 - eout(lin(t, T_DIVIDE, T_DIVIDE + 0.3))),
              tracking=2)
    kd = eout(lin(t, T_DIVIDE - 0.1, T_DIVIDE + 0.3)) * (1 - eout(lin(t, T_FIRES - 0.2, T_FIRES + 0.2)))
    if kd > 0:
        draw_text(cv, "720° ÷ 10 = 72°", BX0, BY - 140, font("inter_xb", 30), YEL, a=kd, tracking=2)
    # ten ticks, one every 72 degrees, each = one cylinder firing
    for i in range(10):
        ti = T_TEN - 0.2 + 0.09 * i
        kt = eback(lin(t, ti, ti + 0.3))
        if kt <= 0:
            continue
        x = fx(36 + 72 * i)
        cv.drawLine(x, BY - 62, x, BY - 40 - 22 * clamp(kt), paint(YEL, stroke=4))
    # moving marker: current crank angle within the 720-degree cycle (model firing at 36 + 72i)
    km = eout(lin(t, T_720 + 0.3, T_720 + 0.8))
    if km > 0:
        deg = math.degrees((phi_at(t) - FIRE_AT[ORDER[0]]) % (4 * math.pi)) + 36.0
        deg = deg % 720
        cv.drawLine(fx(deg), BY - 70, fx(deg), BY + 18, paint(INK, a=km, stroke=3))
        cv.drawCircle(fx(deg), BY, 10, paint(INK, a=km))
    cv.restore()


def pulse_trace(even, n=600):
    xs = np.linspace(0, 720, n)
    ys = np.zeros(n)
    fires = [36 + 72 * i for i in range(10)] if even else [20, 70, 200, 250, 290, 400, 450, 470, 610, 640]
    for f in fires:
        d = xs - f
        ys += np.where(d >= 0, np.exp(-d / 18.0) * (1 - np.exp(-d / 4.0)), 0.0)
    return xs, ys


_XE, _YE = pulse_trace(True)
_XU, _YU = pulse_trace(False)


def draw_even(cv, t):
    k = win(t, T_FIRES - 0.2, T_YAM + 0.1, 0.35, 0.4) * (1 - current.ending_k(t))
    if k <= 0:
        return
    base = BY - 50
    ku = win(t, T_LUMPY - 0.2, T_SMOOTH + 0.1, 0.2, 0.35)
    if ku > 0:
        pts = np.stack([fx(_XU), base - 58 * _YU / _YU.max()], 1)
        brand.curve(cv, pts, MUTED, a=k * ku, prog=eout(lin(t, T_LUMPY - 0.1, T_LUMPY + 0.5)), width=3)
        draw_text(cv, "UNEVEN = LUMPY", BX1, BY - 140, font("inter_xb", 24), MUTED, a=k * ku, align="right",
                  tracking=2)
    ke = eout(lin(t, T_FIRES - 0.1, T_FIRES + 0.8))
    pts = np.stack([fx(_XE), base - 58 * _YE / _YE.max()], 1)
    brand.curve(cv, pts, GREEN, a=k, prog=ke, width=4)
    kv = win(t, T_EVENLY - 0.1, T_YAM + 0.1, 0.2, 0.3) * (1 - ku)
    if kv > 0:
        draw_text(cv, "EVEN: EVERY 72°", BX0, BY - 140, font("inter_xb", 30), GREEN, a=k * kv, align="left",
                  tracking=2)
    brand.stamp(cv, t, "SMOOTH", T_SMOOTH, dur=1.3, center=(540, 1035), color=GREEN, bg=hx("#06281a"))


# ---- sound path (yamaha beat)
CABIN = (220.0, 1290.0)


def draw_yamaha(cv, t):
    k = win(t, T_YAMW - 0.2, T_KEY + 0.1, 0.3, 0.35) * (1 - current.ending_k(t))
    if k <= 0:
        return
    pj = cam(t)
    ky = win(t, T_YAMW - 0.1, T_SURGE + 0.3, 0.2, 0.3)
    if ky > 0:
        pill(cv, 540, 1300, "TUNED BY YAMAHA'S SOUND ENGINEERS", font("inter_xb", 27), INK, border=AMBER,
             a=k * ky, align="center", tracking=2)
    # resonance rings around the tank
    kr = k * win(t, T_RESON - 0.2, T_KEY, 0.3, 0.3)
    c = pj(0, -326, (TANK_Z[0] + TANK_Z[1]) / 2)
    if kr > 0:
        for i in range(3):
            ph = ((t - T_RESON) * 0.9 + i / 3) % 1.0
            cv.drawOval(skia.Rect.MakeXYWH(c[0] - (180 + 160 * ph), c[1] - (60 + 70 * ph), 2 * (180 + 160 * ph),
                                           2 * (60 + 70 * ph)), paint(AMBER, a=kr * (1 - ph) * 0.8, stroke=4))
    ki = k * win(t, T_INSTR - 0.2, T_DUCTS + 0.2, 0.2, 0.3)
    if ki > 0:
        pill(cv, 540, 1300, "SHAPED TO RESONATE", font("inter_xb", 32), INK, border=AMBER, a=ki, align="center",
             tracking=3)
    # duct from the front of the tank to the cabin
    kd = eout(lin(t, T_DUCTS - 0.2, T_DUCTS + 0.8))
    if kd > 0:
        s = pj(-60, -320, TANK_Z[0])
        pts = spline(np.array([s, s + np.array([-90, 120]), (CABIN[0] + 60, CABIN[1] - 170),
                               (CABIN[0] + 40, CABIN[1] - 70)]), 60)
        pipe(cv, pts, 22, AMBER, a=k, prog=kd, glass=True)
        flow(cv, pts, t, 320, 30, AMBER, r=6, a=k * kd, t_start=T_DUCTS + 0.2)
        kc = k * eout(lin(t, T_DUCTS + 0.3, T_DUCTS + 0.7))
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(CABIN[0] - 150, CABIN[1] - 70, 300, 140), 24, 24)
        cv.drawRRect(rr, paint(hx("#0b111c"), a=0.92 * kc))
        cv.drawRRect(rr, paint(AMBER, a=kc, stroke=3))
        # steering wheel icon
        wx, wy = CABIN[0] - 80, CABIN[1]
        cv.drawCircle(wx, wy, 38, paint(INK, a=kc, stroke=6))
        cv.drawLine(wx - 36, wy, wx + 36, wy, paint(INK, a=kc, stroke=6))
        cv.drawLine(wx, wy, wx, wy + 36, paint(INK, a=kc, stroke=6))
        draw_text(cv, "CABIN", CABIN[0] + 50, CABIN[1] + 13, font("inter_blk", 40), INK, a=kc, align="center",
                  tracking=3)
        kw = eout(lin(t, T_CABIN - 0.1, T_CABIN + 0.4))
        for i in range(3):
            ph = ((t - T_CABIN) * 1.2 + i / 3) % 1.0
            rad = 30 + 60 * ph
            cv.drawArc(skia.Rect.MakeXYWH(CABIN[0] + 150 - rad, CABIN[1] - rad, 2 * rad, 2 * rad), -50, 100, False,
                       paint(AMBER, a=k * kw * (1 - ph), stroke=4))
    brand.stamp(cv, t, "SOUND DUCT", T_DUCTS + 0.1, dur=1.4, center=(690, 1300), color=AMBER, bg=hx("#2a1c05"))


# ---- digital tach (key beat)
TC = (540.0, 800.0, 250.0)
NSEG = 45


def draw_tach(cv, t):
    k = win(t, T_KEY - 0.1, T_END + 0.05, 0.4, 0.3) * (1 - current.ending_k(t))
    if k <= 0:
        return
    cx, cy, R = TC
    r = rpm_display(t)
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawCircle(cx, cy, R + 40, paint(hx("#070a10"), a=0.95))
    cv.drawCircle(cx, cy, R + 40, paint(hx("#2a3446"), stroke=3))
    for i in range(NSEG):
        v = 10000 * (i + 0.5) / NSEG
        a0 = 135 + 270 * i / NSEG
        on = r >= v
        c = RED if v >= 9000 else (YEL if v >= 7000 else CYAN)
        rect = skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R)
        if on:
            cv.drawArc(rect, a0 + 0.8, 270 / NSEG - 1.6, False, paint(c, a=0.5, stroke=44, blur=8,
                                                                      cap=skia.Paint.kButt_Cap))
        cv.drawArc(rect, a0 + 0.8, 270 / NSEG - 1.6, False, paint(c if on else hx("#1a2130"), stroke=40,
                                                                  cap=skia.Paint.kButt_Cap))
    for v in range(0, 10001, 1000):
        a = math.radians(135 + 270 * v / 10000)
        rn = R - 62
        draw_text(cv, str(v // 1000), cx + rn * math.cos(a), cy + rn * math.sin(a) + 12, font("inter_b", 32),
                  RED if v >= 9000 else MUTED, align="center")
    draw_text(cv, f"{int(round(r / 100) * 100):,}", cx, cy + 30, font("inter_blk", 96), INK, align="center")
    draw_text(cv, "RPM", cx, cy + 76, font("inter_sb", 26), MUTED, align="center", tracking=4)
    # stopwatch from idle to redline (real time)
    if t >= T_SWEEP - 0.1:
        el = clamp((t - T_SWEEP) / 0.6) * 0.6
        kk = eout(lin(t, T_SWEEP - 0.1, T_SWEEP + 0.1))
        draw_text(cv, f"{el:.2f} s", cx, cy + R + 105, font("inter_blk", 64), YEL if el >= 0.6 else INK, a=kk,
                  align="center")
        draw_text(cv, "IDLE → 9,000 RPM", cx, cy + R + 145, font("inter_sb", 24), MUTED, a=kk, align="center",
                  tracking=3)
    cv.restore()
    k7 = k * win(t, T_750 - 0.1, T_LEX2, 0.25, 0.3)
    if k7 > 0:
        pill(cv, 540, 1300, "750 FIRINGS / SECOND", font("inter_xb", 36), INK, border=RED, a=k7, align="center",
             tracking=2)
        pill(cv, 540, 1376, "9,000 RPM ÷ 60 × 5 PER TURN", font("inter_xb", 24), INK, border=MUTED, a=k7,
             align="center", tracking=2)
    kd = k * win(t, T_DIGITAL - 0.1, T_END + 0.05, 0.2, 0.3)
    if kd > 0:
        pill(cv, 540, 1300, "NO NEEDLE TO LAG", font("inter_xb", 34), INK, border=CYAN, a=kd, align="center",
             tracking=3)
    brand.stamp(cv, t, "DIGITAL TACH", T_DIGITAL, dur=1.6, center=(540, 470), color=CYAN, bg=hx("#05202a"))
    brand.stamp(cv, t, "9,000 RPM", T_9000 + 0.25, dur=1.2, center=(540, 470))


def draw_header(cv, t):
    k = win(t, T_WHAT + 0.4, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(T_LIGHT, "LIGHT TO REV", YEL), (T_ANGLE, "THE BANK ANGLE", YEL), (T_MATH, "THE MATH", YEL),
           (T_EVEN, "EVEN FIRING", GREEN), (T_YAM, "THE INTAKE SOUND", AMBER), (T_KEY, "FLOOR IT", RED)]
    txt, c = "1LR-GUE · 72° V10", CYAN
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    if t < T_KEY - 0.1:
        r = rpm_display(t)
        kr = k * (1 - ease(lin(t, T_KEY - 0.4, T_KEY - 0.1)))
        brand.readout(cv, kr, f"{int(round(r / 100) * 100):,}", "ENGINE RPM", frac=r / 9500, bar_color=c)
        brand.note(cv, "ANIMATION SLOWED", kr * 0.9)


def draw(cv, t):
    draw_engine(cv, t)
    draw_labels(cv, t)
    draw_hook(cv, t)
    draw_what(cv, t)
    draw_light(cv, t)
    draw_angle(cv, t)
    draw_math(cv, t)
    draw_even(cv, t)
    draw_yamaha(cv, t)
    draw_tach(cv, t)
    draw_header(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_SWEEP
MUSIC_START = T_WHAT


def sound():
    sfx = [(0.33, "whoosh_up", 0.35), (2.13, "whoosh_up", 0.3), (T_HOOK_OUT - 0.1, "whoosh_big", 0.6),
           (T_V10, "impact", 0.4), (T_LIGHTW, "clunk", 0.35), (T_TITAN, "tick", 0.3)]
    sfx += [(T_THROTTLE - 0.25 + 0.06 * i, "tick", 0.14) for i in range(10)]
    sfx += [(T_72A + 0.2, "impact", 0.5), (T_RANDOM, "clunk", 0.3), (T_720, "whoosh_up", 0.3)]
    sfx += [(T_TEN - 0.2 + 0.09 * i, "tick", 0.16) for i in range(10)]
    sfx += [(T_SMOOTH, "whoosh_up", 0.35), (T_RESON, "whoosh_down", 0.3), (T_DUCTS + 0.1, "impact", 0.35),
            (T_9000 + 0.25, "impact", 0.55), (T_DIGITAL, "impact", 0.5)]
    eng = {"rpm": rpm_display, "bright": lambda t: 0.9 if (t < T_WHAT or T_SMOOTH < t < T_OUTRO) else 0.4,
           "orders": {0.5: 0.06, 2.5: 0.22, 5.0: 1.0, 7.5: 0.18, 10.0: 0.5, 15.0: 0.22, 20.0: 0.1},
           "pulse_order": 5.0,
           "env": [(0, 0.9), (T_HOOK_OUT, 0.9), (T_WHAT + 0.5, 0.3), (T_ANGLE, 0.15), (T_EVEN, 0.15),
                   (T_SMOOTH, 0.5), (T_YAM + 0.8, 0.3), (T_SWEEP - 0.1, 0.3), (T_SWEEP, 0.95), (T_TACH + 0.4, 0.8),
                   (T_OUTRO + 0.5, 0.25), (T_END, 0.2), (T_END + 0.6, 0.0), (T_TOTAL, 0.0)]}
    return {"build": (T_YAM, T_SWEEP), "drop": (T_SWEEP, T_OUTRO - 0.05), "sfx": sfx, "engine": eng}
