"""Turbo visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (one 3/4 ortho camera, yaw 70 / pitch 22, shaft along X):
  rotating group  turbine wheel (exhaust side, left) + shaft + compressor wheel (intake side, right),
                  one rigid body: both wheels always turn together (negative spin about +X)
  turbine         exhaust enters the volute tangentially, spirals inward with the spin, leaves axially (left)
  compressor      air enters axially at the nose (right), is flung outward, collected in the volute,
                  leaves tangentially at the top -> intercooler -> intake port
  engine          one cylinder stands for the engine: 4-stroke cycle from a crank/rod model
  wastegate       flap on a bypass from the turbine inlet to the turbine outlet
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, wheel, spline, pipe, flow, arrow_head, resample, path_len, point_at

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic

# ================================================================== cue times
T_HOOK_OUT = current.hook_out
T_RPM = F("hook", "rpm")
T_WHAT = L("what")["start"]
T_WHEELS = F("what", "wheels")
T_SHAFT1 = F("what", "shaft")
T_LBL_TURB = F("what", "turbine")
T_EXH_SIDE = F("what", "exhaust")
T_LBL_COMP = F("what", "compressor")
T_INT_SIDE = F("what", "intake")
T_PROB = L("problem")["start"]
T_AIR = F("problem", "air")
T_MORE_AIR = F("problem", "more")
T_FUEL = F("problem", "fuel")
T_POWER = F("problem", "power", 1)
T_ATM = F("problem", "atmospheric")
T_SYS = L("turbine")["start"]
T_EXH = F("turbine", "exhaust")
T_HOT = F("turbine", "hot")
T_HOUSING = F("turbine", "housing")
T_SPIN = F("turbine", "spins")
T_TWHEEL = F("turbine", "wheel")
T_COMPL = L("comp")["start"]
T_SHAFT2 = F("comp", "shaft")
T_COMP2 = F("comp", "compressor")
T_PULL = F("comp", "pulls")
T_SQUEEZE = F("comp", "squeezes")
T_BOOST = F("comp", "boost")
T_COOL = L("cooler")["start"]
T_HEATS = F("cooler", "heats")
T_IC = F("cooler", "intercooler")
T_DENSER = F("cooler", "denser")
T_EACH = F("cooler", "each")
T_GATE = L("gate")["start"]
T_G_BOOST2 = F("gate", "boost", 1)
T_WG = F("gate", "wastegate")
T_OPEN = F("gate", "opens")
T_BYPASS = F("gate", "bypass")
T_HOLD = F("gate", "holding")
T_OUT = L("outro")["start"]
T_O_TURB = F("outro", "turbine", 1)
T_O_COMP = F("outro", "compressor", 1)

# ================================================================== state (deterministic)
# visual shaft speed, revolutions per second of the drawing (slow motion; real shafts are far faster)
OMEGA_KEYS = [(0.0, 1.9), (T_HOOK_OUT, 1.9), (T_WHAT + 0.7, 0.42), (T_PROB + 0.2, 0.42), (T_PROB + 1.2, 0.0),
              (T_HOUSING - 0.1, 0.0), (T_SPIN + 0.7, 0.85), (L("gate")["start"] + 0.2, 0.85),
              (T_G_BOOST2 + 0.3, 1.2), (T_OPEN + 0.15, 1.2), (T_HOLD + 0.3, 1.0), (T_TOTAL, 1.0)]
BOOST_KEYS = [(0, 0.0), (T_PULL + 0.4, 0.0), (T_BOOST + 0.2, 0.62), (L("gate")["start"] + 0.1, 0.62),
              (T_G_BOOST2 + 0.35, 0.97), (T_OPEN + 0.1, 0.99), (T_HOLD + 0.2, 0.62), (T_TOTAL, 0.62)]
GATE_KEYS = [(0, 0.0), (T_OPEN - 0.05, 0.0), (T_OPEN + 0.45, 1.0), (T_TOTAL, 1.0)]
CRANK_RPS = 0.55          # engine animation: one 4-stroke cycle every 3.6 s


def _theta_series():
    dt = 1.0 / 600
    ts = np.arange(0, T_TOTAL + 1.0, dt)
    om = np.array([smooth(x, OMEGA_KEYS) for x in ts])
    th = -np.concatenate([[0.0], np.cumsum(om[:-1]) * dt]) * 2 * np.pi + 0.35
    return ts, th


_TS, _TH = _theta_series()


def theta(t):
    return float(np.interp(t, _TS, _TH))


def omega(t):
    return smooth(t, OMEGA_KEYS)


def boost(t):
    return smooth(t, BOOST_KEYS)


def gate(t):
    return smooth(t, GATE_KEYS)


def atm(t):
    """Absolute intake pressure shown on the readout (illustrative: 1.0 atm -> 1.8 atm, runaway 2.4)."""
    return 1.0 + 1.3 * boost(t)


def check_physics():
    bad = []
    # both wheels are one rigid body: same theta function is used for both (by construction)
    if omega(T_HOT) > 1e-6:
        bad.append("shaft spins before exhaust reaches it")
    if boost(T_PULL) > 1e-3:
        bad.append("boost before the compressor moves air")
    if gate(T_OPEN - 0.1) > 0:
        bad.append("wastegate opens before narration")
    return bad


# ================================================================== geometry (model units)
def sstep(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


TURB = dict(nose=-178.0, back=-112.0, hub=lambda s: 12 + 46 * s ** 2.0,
            tip=lambda s: 44 + 18 * sstep((s - 0.35) / 0.5), nb=11, bp=62.0)
COMP = dict(nose=192.0, back=112.0, hub=lambda s: 13 + 58 * s ** 2.2,
            tip=lambda s: 50 + 26 * sstep((s - 0.3) / 0.6), nb=7, bp=76.0)
T_HOUSE = ([-232, -185, -172, -160, -142, -122, -108, -100], [34, 34, 52, 84, 98, 96, 78, 50])
C_HOUSE = ([100, 108, 122, 142, 160, 176, 195, 290], [50, 82, 110, 112, 88, 66, 58, 58])
CTR_HOUSE = ([-100, -88, 88, 100], [44, 50, 50, 44])
AX = (0.0, 0.0)
TURB_C = hx("#6c6866")
COMP_C = hx("#a9b6c8")
ENG_X, ENG_Y = 40.0, 300.0          # cylinder local origin (head gasket centre) in system coordinates


def draw_rotating_group(cv, pj, t, a=1.0, glow_hot=0.0, blur=0, hl=None, center_housing=False):
    """Turbine + shaft + compressor. hl: dict of highlight strengths {turbine, shaft, compressor}."""
    if a <= 0:
        return
    hl = hl or {}
    th = theta(t)
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(a)))
    bstep = 0.09
    # turbine (far / left end), glowing hot when exhaust drives it
    tb = mix(TURB_C, hx("#c0552a"), 0.35 * glow_hot)
    if glow_hot > 0:
        c0 = pj(-145, 0, 0)
        cv.drawCircle(c0[0], c0[1], 95 * pj.s, paint(hx("#ff6a1a"), a=0.22 * glow_hot, blur=40 * pj.s))
    wheel(cv, pj, "x", AX, TURB["nose"], TURB["back"], TURB["hub"], TURB["tip"], TURB["nb"], th, tb,
          blade=mix(hx("#8c8784"), hx("#ff9a4a"), 0.45 * glow_hot), twist=-0.5, bp_r=TURB["bp"],
          rim=mix(AMBER, YEL, hl.get("turbine", 0)), rim_a=0.45 + 0.5 * max(glow_hot, hl.get("turbine", 0)),
          blur=blur, blur_step=-bstep)
    rev(cv, pj, "x", AX, [-112, 112], [9, 9], STEEL, edge=mix(shade(STEEL, 0.3), YEL, hl.get("shaft", 0)),
        edge_w=1.5 + 2 * hl.get("shaft", 0), glow=hl.get("shaft", 0))
    if center_housing:
        rev(cv, pj, "x", AX, *CTR_HOUSE, hx("#3e4a5e"))
    wheel(cv, pj, "x", AX, COMP["nose"], COMP["back"], COMP["hub"], COMP["tip"], COMP["nb"], th, COMP_C,
          blade=hx("#d3dcea"), twist=0.75, splitters=True, bp_r=COMP["bp"],
          rim=mix(CYAN, YEL, hl.get("compressor", 0)), rim_a=0.45 + 0.5 * hl.get("compressor", 0),
          blur=blur, blur_step=-bstep)
    if a < 1:
        cv.restore()


# ------------------------------------------------------------------ camera
PJ_HOOK = (525.0, 800.0, 2.05)
PJ_SYS = (515.0, 640.0, 1.2)


def make_pj(ox, oy, s):
    return Proj(ox, oy, s, yaw=70, pitch=22)


def turbo_pj(t):
    k = ease(lin(t, T_PROB - 0.1, T_PROB + 1.0))
    return make_pj(*(np.array(PJ_HOOK) * (1 - k) + np.array(PJ_SYS) * k))


PJS = make_pj(*PJ_SYS)


def P(X, Y, z):
    """System-view screen point of a model point."""
    return PJS(X, Y, z)


def P3(pts):
    pts = np.asarray(pts, float)
    return PJS(pts[:, 0], pts[:, 1], pts[:, 2])


# ------------------------------------------------------------------ flow paths (system coordinates)
def _spiral(x0, x1, r0, r1, th0, dth, n=80):
    u = np.linspace(0, 1, n)
    th = th0 + dth * u
    r = r0 + (r1 - r0) * u
    x = x0 + (x1 - x0) * u
    return np.stack([x, r * np.cos(th), r * np.sin(th)], 1)


EXH_PORT = np.array([ENG_X - 95, ENG_Y - 25, 0.0])
INT_PORT = np.array([ENG_X + 95, ENG_Y - 25, 0.0])
TH_IN_T = -math.pi / 2               # turbine volute entry (front side), flow moving up (-Y)
EXH_PIPE_3D = spline([EXH_PORT, [-95, 262, -12], [-128, 220, -60], [-140, 150, -95], [-140, 70, -98], [-140, 2, -98]],
                     60)


def _turbine_path(dr=0.0, phase=0.0):
    vol = _spiral(-140, -146, 98 + dr, 66 + dr * 0.5, TH_IN_T, -2 * math.pi * 0.8 + phase, 90)
    inw = _spiral(-146, -158, 66 + dr * 0.5, 40, vol[-1, 0] * 0 + TH_IN_T - 2 * math.pi * 0.8 + phase, -0.5, 20)
    exi = _spiral(-158, -236, 40, 26 + dr * 0.3, TH_IN_T - 2 * math.pi * 0.8 + phase - 0.5, -0.9, 40)
    return np.vstack([vol, inw, exi])


OUT_PIPE_3D = spline([[-236, 0, 0], [-275, 6, -4], [-305, 60, -14], [-322, 150, -20], [-328, 238, -20]], 60)
BYPASS_A = 0.42                       # where on the inlet pipe the bypass branches (fraction of length)
BYP_3D = spline([EXH_PIPE_3D[int(BYPASS_A * 59)], [-190, 150, -95], [-245, 110, -60], [-292, 40, -12]], 40)


def _join(*parts):
    return np.vstack(parts)


def _outlet_from(p3):
    """Outlet pipe beginning at the point nearest p3 (screen polyline)."""
    d = np.linalg.norm(OUT_PIPE_3D - p3, axis=1)
    i = int(np.argmin(d))
    return OUT_PIPE_3D[i:]


EXH_PATHS = [resample(P3(_join(EXH_PIPE_3D, _turbine_path(dr, ph), OUT_PIPE_3D)), 400)
             for dr, ph in ((0, 0.0), (-10, 0.35), (8, -0.3))]
EXH_SPLIT_U = [path_len(P3(EXH_PIPE_3D)) / path_len(p) for p in EXH_PATHS]
BYP_PATH = resample(P3(_join(EXH_PIPE_3D[:int(BYPASS_A * 59) + 1], BYP_3D, _outlet_from(BYP_3D[-1]))), 220)
BYP_START = path_len(P3(EXH_PIPE_3D[:int(BYPASS_A * 59) + 1]))

TH_OUT_C = math.pi                    # compressor volute exit (top), flow moving +z
AIR_IN_3D = np.stack([np.linspace(345, 196, 30), np.zeros(30), np.zeros(30)], 1)


def _compressor_path(r_in=26.0, phase=0.0):
    dth_vol = -2 * math.pi * 0.85
    th_end = TH_OUT_C
    th_vol0 = th_end - dth_vol
    th_w0 = th_vol0 + 1.2 + phase
    inlet = np.stack([np.linspace(345, 196, 30), r_in * np.cos(np.full(30, th_w0)), r_in * np.sin(np.full(30, th_w0))], 1)
    whl = _spiral(196, 124, r_in, 84, th_w0, th_vol0 - th_w0, 30)
    vol = _spiral(124, 128, 84, 112, th_vol0, dth_vol, 90)
    return np.vstack([inlet, whl, vol])


IC_BOX = dict(x0=272, x1=330, y0=92, y1=232, z0=32, z1=90)
IC_TOP = np.array([301, IC_BOX["y0"], 61])
IC_BOT = np.array([301, IC_BOX["y1"], 61])
C_OUT_3D = spline([[128, -112, 0], [132, -122, 38], [188, -130, 66], [262, -102, 66], [300, -10, 61], IC_TOP], 60)
IC_THRU_3D = np.stack([np.full(20, 301.0), np.linspace(IC_BOX["y0"], IC_BOX["y1"], 20), np.full(20, 61.0)], 1)
INTAKE_3D = spline([IC_BOT, [296, 268, 52], [250, 296, 26], [185, 290, 6], INT_PORT], 50)
AIR_SEGS = []                         # (screen path, spacing, speed, color role) per stream
for r_in, ph in ((24, 0.0), (36, 0.5)):
    pre = P3(_compressor_path(r_in, ph))
    AIR_SEGS.append(resample(np.vstack([pre, P3(C_OUT_3D)]), 360))
AIR_HOT_U = [path_len(P3(_compressor_path(r, p))) / path_len(s) for (r, p), s in zip(((24, 0.0), (36, 0.5)), AIR_SEGS)]
AIR_IN_LEN = [path_len(P3(_compressor_path(r, p)[:30])) for r, p in ((24, 0.0), (36, 0.5))]
COOL_PATH = resample(np.vstack([P3(IC_THRU_3D), P3(INTAKE_3D)]), 200)

# pipes (screen polylines)
PIPE_EXH = P3(EXH_PIPE_3D)
PIPE_OUT = P3(OUT_PIPE_3D)
PIPE_BYP = P3(BYP_3D)
PIPE_CIN = P3(np.stack([np.linspace(345, 290, 10), np.zeros(10), np.zeros(10)], 1))
PIPE_COUT = P3(C_OUT_3D)
PIPE_INT = P3(INTAKE_3D)
GATE_PT = P3(BYP_3D)[-6]

# speeds (screen px/s) and spacings; flux = speed / spacing
EXH_SPEED, EXH_SP = 170.0, 30.0
AIR_SPEED, AIR_SP = 150.0, 34.0
COOL_SP = 20.0
COOL_SPEED = 150.0 * COOL_SP / 26.0


# ================================================================== engine cylinder (local coordinates)
RB = 70.0
CR_Y, CR_R, ROD = 292.0, 58.0, 190.0
V_X = 38.0


def crank(t):
    return 2 * math.pi * CRANK_RPS * t


def piston_top(phi):
    pin = CR_Y - (CR_R * math.cos(phi) + math.sqrt(ROD ** 2 - (CR_R * math.sin(phi)) ** 2))
    return pin - 20.0, pin


def valve_lifts(phi):
    cyc = phi % (4 * math.pi)
    li = 13 * math.sin(cyc) if cyc < math.pi else 0.0
    le = 13 * math.sin(cyc - 3 * math.pi) if cyc >= 3 * math.pi else 0.0
    return max(li, 0), max(le, 0), cyc


_rng = np.random.default_rng(7)
DOTS = np.stack([np.sqrt(_rng.uniform(0.02, 0.85, 48)), _rng.uniform(0, 2 * np.pi, 48), _rng.uniform(0.06, 0.94, 48)], 1)


def cyl_pj(t):
    sys_o = P(ENG_X, ENG_Y, 0)
    k = ease(lin(t, T_SYS - 0.5, T_SYS + 0.6))
    ox = 540 * (1 - k) + sys_o[0] * k
    oy = 640 * (1 - k) + sys_o[1] * k
    s = 1.75 * (1 - k) + 1.2 * k
    return make_pj(ox, oy, s)


def density(t):
    """Charge density in the cylinder relative to atmospheric (drives the dot count)."""
    d = 1.0 + 0.55 * clamp(boost(t) / 0.62) * ease(lin(t, T_SQUEEZE, T_BOOST + 0.4))
    d += 0.45 * ease(lin(t, T_DENSER, T_EACH + 0.4))
    return d


def draw_cylinder(cv, pj, t, a):
    if a <= 0:
        return
    phi = crank(t)
    top, pin = piston_top(phi)
    li, le, cyc = valve_lifts(phi)
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    # crank + rod (behind)
    cp = pj(0, CR_Y, 0)
    rev(cv, pj, "z", (0, CR_Y), [8, 30], [CR_R + 14, CR_R + 14], hx("#3a4456"))
    cpin = (CR_R * math.sin(phi), CR_Y - CR_R * math.cos(phi))
    p_rod0, p_rod1 = pj(cpin[0], cpin[1], 0), pj(0, pin, 0)
    cv.drawLine(*p_rod0, *p_rod1, paint(shade(STEEL, 0.35), stroke=22 * pj.s, cap=skia.Paint.kRound_Cap))
    cv.drawLine(*p_rod0, *p_rod1, paint(STEEL_D, stroke=17 * pj.s, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(*p_rod0, 10 * pj.s, paint(STEEL))
    cv.drawCircle(*cp, 12 * pj.s, paint(shade(STEEL, 0.6)))
    # liner back wall (glass)
    rev(cv, pj, "y", (0, 0), [0, 250], [RB + 6, RB + 6], hx("#2a3446"), fill_a=0.35, edge=hx("#4b5a72"), caps=False)
    # charge (dots)
    dens = density(t)
    n = int(round(12 * dens))
    fresh = cyc < 2 * math.pi
    if cyc < math.pi:
        n_vis = int(round(n * clamp(cyc / (0.85 * math.pi))))
    else:
        n_vis = n
    burnt = clamp((cyc - 2 * math.pi) / 0.4) if not fresh else 0.0
    if cyc >= 3 * math.pi:
        n_vis = int(round(n * (1 - 0.75 * clamp((cyc - 3 * math.pi) / math.pi))))
    for i in range(n_vis):
        r, an, h = DOTS[i]
        X, z = r * (RB - 10) * math.cos(an), r * (RB - 10) * math.sin(an)
        Y = 4 + h * (top - 10)
        q = pj(X, Y, z)
        c = mix(CYAN, hx("#ff6a3a"), burnt)
        cv.drawCircle(q[0], q[1], 8 * pj.s, paint(c, a=0.3, blur=4 * pj.s))
        cv.drawCircle(q[0], q[1], 4.6 * pj.s, paint(c))
    # combustion flash
    if 2 * math.pi <= cyc < 2 * math.pi + 0.9:
        k = 1 - (cyc - 2 * math.pi) / 0.9
        q = pj(0, top * 0.45, 0)
        cv.drawCircle(q[0], q[1], 80 * pj.s, paint(hx("#ffb020"), a=0.55 * k, blur=26 * pj.s))
        cv.drawCircle(q[0], q[1], 38 * pj.s, paint(hx("#fff2c0"), a=0.6 * k, blur=10 * pj.s))
    # piston
    rev(cv, pj, "y", (0, 0), [top, top + 52], [RB - 2, RB - 2], STEEL)
    for yy in (top + 12, top + 22):
        ring_front(cv, pj, "y", (0, 0), yy, RB - 1, shade(STEEL, 0.45), width=2.2)
    # valves
    for vx, lift, cc in ((V_X, li, CYAN), (-V_X, le, AMBER)):
        rev(cv, pj, "y", (vx, 0), [-78, lift - 4], [4.5, 4.5], STEEL)
        rev(cv, pj, "y", (vx, 0), [lift - 7, lift], [16, 25], STEEL, edge=cc if lift > 0.5 else None)
    # liner front edge + head (glass)
    ring_front(cv, pj, "y", (0, 0), 250, RB + 6, hx("#6b7c96"), width=2)
    head = np.array([[-95, -52], [95, -52], [95, 0], [-95, 0]], float)
    extrude(cv, pj, head, -80, 80, hx("#3a4658"), alpha=0.55)
    cv.restore()


# ================================================================== scene blocks
def draw_hook(cv, t):
    if t > T_PROB + 1.2:
        return
    a = 1.0
    pj = turbo_pj(t)
    if t < T_SYS:
        blur = 3 if t < T_HOOK_OUT + 0.3 else 0
        hl = {"turbine": win(t, T_LBL_TURB - 0.1, T_EXH_SIDE + 0.9, 0.2, 0.4),
              "shaft": win(t, T_SHAFT1 - 0.1, T_SHAFT1 + 0.9, 0.2, 0.4),
              "compressor": win(t, T_LBL_COMP - 0.1, T_INT_SIDE + 0.9, 0.2, 0.4)}
        k_fade = 1 - 0.85 * ease(lin(t, T_PROB, T_PROB + 1.0))
        glow = 1.0 - ease(lin(t, T_HOOK_OUT, T_WHAT + 0.5)) * 0.7
        draw_rotating_group(cv, pj, t, a=a * k_fade, glow_hot=glow, blur=blur, hl=hl)
    # shaft-speed counter
    k = 1 - ease(lin(t, T_HOOK_OUT - 0.1, T_HOOK_OUT + 0.35))
    if k > 0:
        v = 200000 * ease(lin(t, 0.15, T_RPM + 0.25)) ** 1.4
        txt = f"{int(round(v / 1000) * 1000):,}"
        draw_text(cv, "SHAFT SPEED · UP TO", 540, 1095, font("inter_sb", 30), MUTED, a=k, align="center", tracking=4)
        draw_text(cv, txt, 540, 1215, font("inter_blk", 128), INK, a=k, align="center")
        draw_text(cv, "RPM", 540, 1275, font("inter_xb", 40), AMBER, a=k, align="center", tracking=8)


def draw_what_labels(cv, t):
    if t > T_PROB + 0.4:
        return
    pj = make_pj(*PJ_HOOK)
    t1 = T_PROB + 0.1
    brand.label(cv, t, "TURBINE", pj(-150, -40, -60), (90, 560), AMBER, T_LBL_TURB - 0.05, t1)
    brand.label(cv, t, "SHAFT", pj(0, -9, 0), (420, 560), STEEL, T_SHAFT1 - 0.05, t1)
    brand.label(cv, t, "COMPRESSOR", pj(160, -70, -20), (930, 560), CYAN, T_LBL_COMP - 0.05, t1, align="right")
    for txt, x, c, t0 in (("EXHAUST SIDE", 240, AMBER, T_EXH_SIDE), ("INTAKE SIDE", 830, CYAN, T_INT_SIDE)):
        k = win(t, t0 - 0.05, t1, 0.25, 0.3)
        if k > 0:
            draw_text(cv, txt, x, 1060, font("inter_xb", 30), c, a=k, align="center", tracking=4)
            cv.drawLine(x - 80, 1078, x + 80, 1078, paint(c, a=0.6 * k, stroke=3))


def draw_problem(cv, t):
    k_in = ease(lin(t, T_PROB + 0.2, T_PROB + 0.8))
    if k_in <= 0:
        return
    pj = cyl_pj(t)
    draw_cylinder(cv, pj, t, k_in)
    # problem-only overlays (gone once the system builds)
    k = k_in * (1 - ease(lin(t, T_SYS - 0.6, T_SYS)))
    if k <= 0:
        return
    # short intake runner with atmospheric air
    run = np.array([pj(95, -25, 0), pj(150, -40, 0), pj(215, -45, 0)])
    rpath = resample(spline(run, 40), 60)[::-1]
    pipe(cv, rpath, 34 * pj.s / 1.2, hx("#3a4658"), a=k, glass=True)
    open_k = 1.0 if (crank(t) % (4 * math.pi)) < math.pi else 0.25
    flow(cv, rpath, t, 70, 30, CYAN, r=5, a=k * open_k)
    draw_text(cv, "AIR", rpath[0][0] + 8, rpath[0][1] - 34, font("inter_xb", 30), CYAN, a=k, tracking=3)
    # air -> fuel -> power chips
    items = [("MORE AIR", eout(lin(t, T_MORE_AIR, T_MORE_AIR + 0.25))),
             ("MORE FUEL", eout(lin(t, T_FUEL, T_FUEL + 0.25))),
             ("MORE POWER", eout(lin(t, T_POWER, T_POWER + 0.25)))]
    kc = k * ease(lin(t, T_MORE_AIR - 0.3, T_MORE_AIR))
    if kc > 0:
        brand.chips(cv, kc, 1320, items, center=True)
    ka = win(t, T_ATM - 0.05, T_SYS - 0.3, 0.25, 0.3)
    if ka > 0:
        pill(cv, 540, 470, "ATMOSPHERIC PRESSURE · 1 ATM", font("inter_xb", 30), INK, border=CYAN, a=ka,
             align="center", tracking=2)


def draw_system(cv, t):
    k_sys = ease(lin(t, T_SYS - 0.2, T_SYS + 0.7))
    if k_sys <= 0:
        return
    kE = 1 - current.ending_k(t)
    a = k_sys * kE
    if a <= 0:
        return
    pj = PJS
    th = theta(t)
    om = omega(t)
    hot = clamp(om / 0.85)
    hl_out = {"turbine": win(t, T_O_TURB - 0.6, T_O_TURB + 0.6, 0.2, 0.3) + win(t, T_TWHEEL - 0.1, T_TWHEEL + 1.0, 0.2, 0.3),
              "shaft": win(t, T_SHAFT2 - 0.1, T_SHAFT2 + 1.0, 0.2, 0.3) + win(t, T_O_TURB, T_O_COMP, 0.2, 0.3),
              "compressor": win(t, T_COMP2 - 0.1, T_COMP2 + 1.0, 0.2, 0.3) + win(t, T_O_COMP - 0.3, T_O_COMP + 0.9, 0.2, 0.3)}
    hl_out = {k: clamp(v) for k, v in hl_out.items()}
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    # --- ducts behind the turbo
    k_cpipe = ease(lin(t, T_PULL - 0.6, T_PULL))
    pipe(cv, PIPE_COUT, 30, hx("#3a4658"), glass=True, a=k_cpipe)
    k_byp = ease(lin(t, T_WG - 0.4, T_WG + 0.2))
    pipe(cv, PIPE_BYP, 22, hx("#3a4658"), glass=True, a=k_byp)
    # --- rotating group (x-ray) + housings
    blur = 2 if om > 0.95 else 0
    draw_rotating_group(cv, pj, t, a=1.0, glow_hot=hot * ease(lin(t, T_HOT, T_SPIN)), blur=blur, hl=hl_out,
                        center_housing=True)
    k_h = ease(lin(t, T_SYS + 0.2, T_SYS + 0.9))
    rev(cv, pj, "x", AX, *T_HOUSE, hx("#5a4a3e"), fill_a=0.30 * k_h, edge=mix(AMBER, YEL, win(t, T_HOUSING - 0.1, T_HOUSING + 1.0)),
        edge_w=2.2, glow=0.35 * k_h, alpha=k_h)
    rev(cv, pj, "x", AX, *C_HOUSE, hx("#45566e"), fill_a=0.26 * k_h, edge=CYAN, edge_w=2.2, glow=0.3 * k_h, alpha=k_h)
    # --- ducts in front
    k_epipe = ease(lin(t, T_SYS + 0.1, T_EXH + 0.3))
    pipe(cv, PIPE_EXH, 32, hx("#3a4658"), glass=True, a=1.0, prog=k_epipe)
    pipe(cv, PIPE_OUT, 30, hx("#3a4658"), glass=True, a=1.0, prog=ease(lin(t, T_HOT, T_HOT + 0.8)))
    pipe(cv, PIPE_CIN, 30, hx("#3a4658"), glass=True, a=k_cpipe)
    k_ipipe = ease(lin(t, T_SQUEEZE - 0.3, T_SQUEEZE + 0.4))
    pipe(cv, PIPE_INT, 30, hx("#3a4658"), glass=True, a=k_ipipe)
    draw_intercooler(cv, t, k_cpipe)
    draw_gate(cv, t, k_byp)
    # --- flows
    gt = gate(t)
    sp = EXH_SPEED * (0.8 + 0.4 * clamp(om / 1.2))
    for i, path in enumerate(EXH_PATHS):
        col_at = (lambda u, su=EXH_SPLIT_U[i]: mix(hx("#ff7a2a"), hx("#ff4a3a"), clamp((u - su) / 0.5)))
        flow(cv, path, t, sp, EXH_SP * (1 + 0.6 * gt) * (1.0 + 0.25 * i), AMBER, r=5.2, t_start=T_HOT + 0.12 * i,
             color_at=col_at, offset=9 * i)
    if gt > 0:
        flow(cv, BYP_PATH, t, sp, EXH_SP * 1.3, AMBER, r=5.2, a=gt, t_start=T_OPEN + 0.05, offset=BYP_START % 30,
             color_at=lambda u: hx("#ff7a2a"))
    heat = ease(lin(t, T_HEATS - 0.2, T_HEATS + 0.4))
    for i, path in enumerate(AIR_SEGS):
        hu = AIR_HOT_U[i]

        def ca(u, hu=hu):
            return mix(CYAN, mix(CYAN, hx("#ff9a3a"), heat), clamp((u - hu * 0.92) / 0.08))
        flow(cv, path, t, AIR_SPEED, AIR_SP * (1.0 + 0.3 * i), CYAN, r=5.0, t_start=T_PULL + 0.15 * i,
             color_at=ca, offset=11 * i)
    t_cool0 = T_PULL + path_len(AIR_SEGS[0]) / AIR_SPEED
    flow(cv, COOL_PATH, t, COOL_SPEED, COOL_SP * (1.35 - 0.35 * ease(lin(t, T_DENSER - 0.2, T_DENSER + 0.4))), CYAN,
         r=5.0, t_start=t_cool0)
    # --- outro recap: trace the exhaust path, then the intake path
    k1 = win(t, T_OUT - 0.1, T_END, 0.2, 0.3)
    if k1 > 0:
        su = EXH_SPLIT_U[0]
        n1 = int(len(EXH_PATHS[0]) * min(1.0, su + 0.55))
        brand.curve(cv, EXH_PATHS[0][:n1], AMBER, a=0.8 * k1, prog=eout(lin(t, T_OUT, T_O_TURB)), width=5)
    k3 = win(t, T_O_COMP - 0.3, T_END, 0.2, 0.3)
    if k3 > 0:
        ap = np.vstack([AIR_SEGS[0], COOL_PATH])
        brand.curve(cv, ap, CYAN, a=0.8 * k3, prog=eout(lin(t, T_O_COMP - 0.2, T_END - 0.3)), width=5)
    cv.restore()
    # --- engine
    draw_cylinder(cv, cyl_pj(t), t, kE * ease(lin(t, T_SYS - 0.5, T_SYS)) if t >= T_SYS - 0.5 else 0)
    if t >= T_SYS - 0.5:
        pass


def draw_intercooler(cv, t, k):
    if k <= 0:
        return
    b = IC_BOX
    hl = win(t, T_IC - 0.1, T_IC + 1.6, 0.2, 0.4)
    prof = np.array([[b["x0"], b["y0"]], [b["x1"], b["y0"]], [b["x1"], b["y1"]], [b["x0"], b["y1"]]], float)
    cv.saveLayerAlpha(None, int(255 * clamp(k)))
    F_, B_ = extrude(cv, PJS, prof, b["z0"], b["z1"], hx("#2c3a50"), alpha=0.75,
                     rim=mix(hx("#5d7ea8"), YEL, hl), rim_w=2.0, rim_glow=hl)
    # fins on the front face
    for i in range(1, 12):
        y = b["y0"] + (b["y1"] - b["y0"]) * i / 12
        p0, p1 = PJS(b["x0"] + 4, y, b["z0"]), PJS(b["x1"] - 4, y, b["z0"])
        cv.drawLine(*p0, *p1, paint(hx("#7f9cc4"), a=0.45, stroke=1.6))
    cv.restore()


def draw_gate(cv, t, k):
    if k <= 0:
        return
    g = gate(t)
    x, y = GATE_PT
    hl = win(t, T_WG - 0.1, T_HOLD + 0.8, 0.2, 0.4)
    cv.drawCircle(x, y, 20, paint(hx("#0b111c"), a=k))
    cv.drawCircle(x, y, 20, paint(mix(AMBER, YEL, hl), a=k, stroke=3))
    ang = math.radians(-20 - 70 * g)
    L_ = 26
    cv.drawLine(x - L_ * math.cos(ang) * 0.1, y - L_ * math.sin(ang) * 0.1, x + L_ * math.cos(ang), y + L_ * math.sin(ang),
                paint(INK, a=k, stroke=6, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(x, y, 5, paint(AMBER, a=k))


def draw_sys_labels(cv, t):
    if t < T_SYS:
        return
    tE = T_END
    exh_mid = PIPE_EXH[len(PIPE_EXH) // 2]
    brand.label(cv, t, "EXHAUST", tuple(exh_mid), (90, 1080), AMBER, T_EXH - 0.05, T_COMPL)
    brand.label(cv, t, "TURBINE HOUSING", tuple(P(-140, -100, 0)), (90, 440), AMBER, T_HOUSING - 0.05, T_COMPL)
    brand.label(cv, t, "SHAFT", tuple(P(0, -50, 0)), (470, 440), STEEL, T_SHAFT2 - 0.05, T_PULL)
    brand.label(cv, t, "COMPRESSOR", tuple(P(150, -110, 0)), (930, 440), CYAN, T_COMP2 - 0.05, T_BOOST - 0.3, align="right")
    brand.label(cv, t, "FRESH AIR", tuple(P(330, 0, 0)), (930, 560), CYAN, T_PULL - 0.05, T_BOOST - 0.3, align="right")
    brand.label(cv, t, "INTERCOOLER", tuple(PJS(272, 160, 32)), (930, 1035), CYAN, T_IC - 0.05, T_GATE, align="right")
    brand.label(cv, t, "HOT", tuple(PIPE_COUT[len(PIPE_COUT) // 2]), (660, 430), AMBER, T_HEATS - 0.05, T_GATE)
    brand.label(cv, t, "COOL + DENSE", tuple(PIPE_INT[len(PIPE_INT) // 3]), (930, 1110), CYAN, T_DENSER - 0.05, T_GATE,
                align="right")
    brand.label(cv, t, "WASTEGATE", tuple(GATE_PT), (90, 520), AMBER, T_WG - 0.05, T_OUT + 0.4)
    k = win(t, T_HOT - 0.1, T_COMPL, 0.3, 0.3)
    if k > 0:
        p = PIPE_OUT[-1]
        draw_text(cv, "TO TAILPIPE", p[0] - 10, p[1] + 52, font("inter_xb", 24), MUTED, a=k, align="left", tracking=2)


def draw_header(cv, t):
    k = win(t, T_SYS + 0.3, T_END, 0.3, 0.3)
    if k <= 0:
        return
    b = boost(t)
    p = atm(t)
    over = clamp((b - 0.7) / 0.25) * (1 - gate(t))
    if t < T_GATE and boost(t) < 0.08:
        txt, c = "NO BOOST", CYAN
    elif t < T_GATE + 0.3:
        txt, c = "BOOST", AMBER
    elif t < T_OPEN:
        txt, c = "BOOST CLIMBING", RED
    elif t < T_HOLD:
        txt, c = "WASTEGATE OPEN", AMBER
    else:
        txt, c = "BOOST HELD", AMBER
    brand.status_pill(cv, k, txt, c)
    brand.readout(cv, k, f"{p:.1f}", "ATM INTAKE PRESSURE", frac=b, bar_color=mix(AMBER, RED, over),
                  marker_frac=0.62 if t > T_WG - 0.2 else None)
    brand.note(cv, "ANIMATION SLOWED", k * 0.9)


def draw_stamps(cv, t):
    brand.stamp(cv, t, "BOOST", T_BOOST, center=(540, 405), color=AMBER, bg=hx("#2a1c05"))
    brand.stamp(cv, t, "BYPASS", T_BYPASS, center=(540, 405), color=AMBER, bg=hx("#2a1c05"))


def draw(cv, t):
    draw_hook(cv, t)
    draw_what_labels(cv, t)
    if t < T_SYS - 0.5:
        draw_problem(cv, t)
    else:
        draw_problem(cv, t) if t < T_SYS + 0.1 else None
    draw_system(cv, t)
    draw_sys_labels(cv, t)
    draw_header(cv, t)
    draw_stamps(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_BOOST
MUSIC_START = T_WHAT


def sound():
    sfx = [(0.05, "spool", 0.55), (T_HOOK_OUT - 0.1, "whoosh_big", 0.6),
           (T_PROB - 0.35, "whoosh_down", 0.45), (T_SYS - 0.4, "whoosh_up", 0.45),
           (T_HOT, "hiss", 0.4), (T_SPIN, "spool", 0.5), (T_BOOST, "impact", 0.5),
           (T_IC - 0.05, "tick", 0.25), (T_OPEN, "clunk", 0.55), (T_BYPASS, "hiss", 0.45)]
    sfx += [(F("problem", w) + 0.03, "tick", 0.2) for w in ("fuel",)] + [(T_MORE_AIR + 0.03, "tick", 0.2),
                                                                         (T_POWER + 0.03, "tick", 0.2)]
    return {"build": (T_COMPL, T_BOOST), "drop": (T_BOOST, T_OUT - 0.05), "sfx": sfx}
