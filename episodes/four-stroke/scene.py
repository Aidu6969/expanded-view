"""Four-stroke engine visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (oblique section view: X right, Y down, z depth receding up-right; one cylinder, units ~mm):
  crank      main journal at (0, CR_Y), throw CR_R, turns clockwise on screen; phi = 0 at TDC
  rod        length ROD; piston pin from exact slider-crank kinematics
  piston     crown CLR below the deck at TDC; swept + clearance volume set to exactly 10:1
  valves     intake (left, X=-VX) and exhaust (right, X=+VX); lift = 12 sin^2 over their stroke
  camshafts  DOHC, direct buckets; cam angle = phi / 2 (2:1 belt drive: 20T crank, 40T cam sprockets);
             lobe radius in the follower direction = base + 12 sin^2(...), i.e. the same lift as the valve
  cycle      cyc = phi mod 720 deg: 0-180 intake, 180-360 compression, 360-540 power, 540-720 exhaust;
             spark at 20 deg before TDC of compression
  flywheel   on the crank, behind it
Crank motion: free-running in the hook, slowed, then stopped and stepped stroke by stroke in sync with
the narration, then free-running (slow) again for the camshaft / outro beats.
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, spline, pipe, flow, resample

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_RPM = F("hook", "rpm")
T_TWENTY = F("hook", "twenty")
T_SECOND = F("hook", "second.", which="end")
T_WHAT = L("what")["start"]
T_SLOWED = F("what", "slowed")
T_FOUR_W = F("what", "four", 1)
T_STROKES_W = F("what", "strokes")
T_TWO = F("what", "two")
T_PARTS = L("parts")["start"]
T_PISTON = F("parts", "piston")
T_CYL = F("parts", "cylinder.")
T_ROD = F("parts", "connecting")
T_CRANK = F("parts", "crankshaft,")
T_TURNING = F("parts", "turning")
T_ROTATION = F("parts", "rotation.")
T_UPTOP = F("parts", "top,")
T_VALVES = F("parts", "valves")
T_PLUG = F("parts", "spark")
T_INTAKE = L("intake")["start"]
T_IN_VALVE = F("intake", "intake", 1)
T_OPENS = F("intake", "opens,")
T_DROPS = F("intake", "drops,")
T_AIR = F("intake", "air")
T_FUEL_E = F("intake", "fuel.", which="end")
T_COMP = L("compress")["start"]
T_BOTH = F("compress", "both")
T_CLOSE = F("compress", "close,")
T_SQUEEZES = F("compress", "squeezes")
T_TEN = F("compress", "ten")
T_SMALLER_E = F("compress", "smaller.", which="end")
T_KEY = L("key")["start"]
T_BEFORE = F("key", "before")
T_FIRES = F("key", "fires.")
T_EXPANDS = F("key", "expands")
T_DOWN_E = F("key", "down.", which="end")
T_ONLY = F("key", "only")
T_EXH = L("exhaust")["start"]
T_EX_OPENS = F("exhaust", "opens,")
T_PUSHES = F("exhaust", "pushes")
T_OUT_E = F("exhaust", "out.", which="end")
T_CAM = L("cam")["start"]
T_FLYWHEEL = F("cam", "flywheel")
T_THREE = F("cam", "three.")
T_CAMSHAFT = F("cam", "camshaft")
T_HALF = F("cam", "half")
T_EACH = F("cam", "each")
T_TWO_T = F("cam", "two")
T_OUTRO = L("outro")["start"]
T_OTTO = F("outro", "otto")
T_1876 = F("outro", "eighteen")

# ================================================================== geometry
RB = 66.0                          # bore radius
CR_R, ROD = 52.0, 190.0            # crank throw, rod length (stroke 104)
CLR = 2 * CR_R / 9.0               # clearance so (swept + clearance) / clearance = 10
PIN_H = 36.0                       # crown above the piston pin
CR_Y = CLR + PIN_H + CR_R + ROD    # crank centre so the crown sits CLR below the deck at TDC
PISTON_H = 58.0
LINER_Y1 = 196.0
VX = 40.0                          # valve x
VR = 22.0                          # valve head radius
LIFT = 12.0
CAM_Y = -142.0
CAM_BASE = 20.0
BUCKET_TOP0 = CAM_Y + CAM_BASE     # bucket top when closed
HEAD_TOP = -70.0
FLY_R = 100.0
SPK_CR, SPK_CC = 18.0, 36.0        # timing sprocket radii (20T / 40T)
SPARK_ADV = math.radians(20)

C_HEAD = hx("#3a4658")
C_ROD = hx("#7d889b")
C_FLY = hx("#535e70")


def pin_y(phi):
    return CR_Y - (CR_R * math.cos(phi) + math.sqrt(ROD ** 2 - (CR_R * math.sin(phi)) ** 2))


def crown_y(phi):
    return pin_y(phi) - PIN_H


def lifts(phi):
    cyc = phi % (4 * math.pi)
    li = LIFT * math.sin(cyc) ** 2 if cyc < math.pi else 0.0
    le = LIFT * math.sin(cyc) ** 2 if cyc >= 3 * math.pi else 0.0
    return li, le, cyc


def volume_ratio(phi):
    """Cylinder volume relative to the TDC (clearance) volume."""
    return crown_y(phi) / CLR


# ================================================================== crank angle vs time
W_HOOK = 2 * math.pi * 1.3        # visual crank speed in the hook (rad/s; the real thing is far faster)
W_SLOW = 2 * math.pi * 0.32
W_CAM = 2 * math.pi * 0.42


def _free_w(t):
    return smooth(t, [(0.0, W_HOOK), (T_SLOWED, W_HOOK), (T_SLOWED + 1.6, W_SLOW), (T_INTAKE, W_SLOW)])


def _build():
    dt = 1.0 / 600
    ts = np.arange(0.0, T_TOTAL + 1.0, dt)
    phi = np.zeros_like(ts)
    i_a = int(T_INTAKE / dt)
    for i in range(1, i_a + 1):
        phi[i] = phi[i - 1] + _free_w(ts[i - 1]) * dt
    pa = phi[i_a]
    B = 4 * math.pi * math.ceil((pa + 0.6) / (4 * math.pi))      # next intake TDC ahead of us
    keys = [(T_INTAKE, pa), (T_OPENS - 0.05, B), (T_DROPS - 0.1, B + 0.15), (T_FUEL_E, B + math.pi),
            (T_CLOSE, B + math.pi), (T_SMALLER_E, B + 2 * math.pi - SPARK_ADV),
            (T_FIRES + 0.05, B + 2 * math.pi - SPARK_ADV), (T_EXPANDS - 0.05, B + 2 * math.pi + 0.15),
            (T_DOWN_E, B + 3 * math.pi), (T_EX_OPENS, B + 3 * math.pi), (T_OUT_E, B + 4 * math.pi)]
    # first segment eases in from the free-running speed: use linear-blend of free-run and keys
    i_k = int(T_OUT_E / dt)
    for i in range(i_a + 1, i_k + 1):
        phi[i] = smooth(ts[i], keys)
    # free-run again: ramp from rest to W_CAM, faster in the outro
    wk = [(T_OUT_E, 0.0), (T_CAM + 0.2, 0.0), (T_CAM + 1.2, W_CAM), (T_OUTRO, W_CAM), (T_OTTO + 1.5, W_HOOK),
          (T_TOTAL + 2, W_HOOK)]
    for i in range(i_k + 1, len(ts)):
        phi[i] = phi[i - 1] + smooth(ts[i - 1], wk) * dt
    return ts, phi, B


_TS, _PHI, B0 = _build()


def phi_at(t):
    return float(np.interp(t, _TS, _PHI))


def omega(t):
    return (phi_at(t + 0.01) - phi_at(t - 0.01)) / 0.02


def spark_k(t):
    """Spark flash strength. Fires 20 deg before TDC of every compression stroke."""
    if T_KEY - 0.5 < t < T_CAM:
        return win(t, T_FIRES - 0.02, T_FIRES + 0.55, 0.04, 0.3)
    # free-running sections: find the time since the last crossing of spark angle
    ph = phi_at(t)
    base = (ph + SPARK_ADV) % (4 * math.pi)            # 2pi at the spark
    d = (base - 2 * math.pi) / max(abs(omega(t)), 1e-6)  # seconds since spark (approx)
    if 0 <= d < 0.18:
        return 1 - d / 0.18
    return 0.0


def burn_k(t):
    """Combustion glow during the start of the power stroke."""
    ph = phi_at(t)
    cyc = ph % (4 * math.pi)
    if 2 * math.pi - SPARK_ADV <= cyc < 3 * math.pi:
        if T_KEY - 0.5 < t < T_CAM and t < T_FIRES:
            return 0.0
        return clamp(1 - (cyc - 2 * math.pi) / math.pi) ** 1.5 if cyc >= 2 * math.pi else 0.6
    return 0.0


def check_physics():
    bad = []
    for ph in np.linspace(0, 4 * math.pi, 1441):
        li, le, _ = lifts(ph)
        if max(li, le) > crown_y(ph) - 1.0:
            bad.append(f"valve hits piston at {math.degrees(ph):.0f} deg")
            break
    if abs(volume_ratio(math.pi) - 10.0) > 0.05:
        bad.append(f"compression ratio {volume_ratio(math.pi):.2f}")
    if abs(phi_at(T_OPENS) % (4 * math.pi)) > 1e-3 and abs(phi_at(T_OPENS) % (4 * math.pi) - 4 * math.pi) > 1e-3:
        bad.append("intake does not start at TDC on 'opens'")
    c = phi_at(T_FIRES) % (4 * math.pi)
    if abs(c - (2 * math.pi - SPARK_ADV)) > 1e-3:
        bad.append("spark not 20 deg BTDC")
    if np.any(np.diff(_PHI) < -1e-9):
        bad.append("crank runs backwards")
    return bad


assert not check_physics(), check_physics()

# ================================================================== camera
DX, DY = 0.42, -0.30
CAM_MAIN = (522.0, 706.0, 1.60)
CAM_HOOK = (528.0, 760.0, 1.22)
CAM_HEAD = (522.0, 690.0, 1.70)     # slight push-in on the chamber for the spark


def cam(t):
    k_h = ease(lin(t, T_PARTS - 0.5, T_PARTS + 0.5))
    p = np.array(CAM_HOOK) * (1 - k_h) + np.array(CAM_MAIN) * k_h
    k_z = ease(lin(t, T_KEY - 0.2, T_KEY + 0.8)) * (1 - ease(lin(t, T_ONLY - 0.4, T_ONLY + 0.5)))
    p = p * (1 - k_z) + np.array(CAM_HEAD) * k_z
    return Proj(p[0], p[1], p[2], dx=DX, dy=DY)


# ================================================================== charge (gas dots)
_rng = np.random.default_rng(11)
NDOT = 46
DOTS = np.stack([np.sqrt(_rng.uniform(0.0, 0.9, NDOT)), _rng.uniform(0, 2 * np.pi, NDOT),
                 _rng.uniform(0.04, 0.96, NDOT)], 1)
C_FRESH = CYAN
C_HOT = hx("#ff5a2a")
C_BURNT = hx("#8a7a6a")


def gas_state(t, cyc):
    """(visible fraction, colour) of the charge."""
    if cyc < math.pi:
        return clamp(cyc / (0.9 * math.pi)), C_FRESH
    if cyc < 2 * math.pi - SPARK_ADV or (T_KEY - 0.5 < t < T_FIRES and cyc < 2 * math.pi + 0.1):
        squeeze = clamp((cyc - math.pi) / math.pi)
        return 1.0, mix(C_FRESH, hx("#bff4ff"), 0.8 * squeeze)
    if cyc < 3 * math.pi:
        k = clamp((cyc - (2 * math.pi - SPARK_ADV)) / 0.35)
        return 1.0, mix(hx("#bff4ff"), C_HOT, k) if cyc < 2.3 * math.pi else mix(C_HOT, C_BURNT,
                                                                                               0.45 * clamp((cyc - 2.3 * math.pi) / (0.7 * math.pi)))
    return 1.0 - 0.9 * clamp((cyc - 3 * math.pi) / math.pi), C_BURNT


# ================================================================== ports (model polylines at z = 0)
IN_PORT = np.array([(-235, -58), (-170, -56), (-110, -48), (-70, -30), (-VX - 4, -6)], float)
EX_PORT = np.array([(VX + 4, -6), (70, -30), (110, -48), (170, -56), (235, -58)], float)


def cam_prof(cx, cy, ang, n=72):
    """Cam lobe; `ang` = direction of the nose (screen angle, Y down)."""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rel = (th - ang + math.pi) % (2 * math.pi) - math.pi
    r = CAM_BASE + np.where(np.abs(rel) < math.pi / 4, LIFT * np.cos(2 * rel) ** 2, 0.0)
    return np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1)


def sprocket_pts(pj, cx, cy, z, r, n_teeth, ang):
    pts = []
    for k in range(n_teeth):
        a = ang + 2 * math.pi * k / n_teeth
        p = 2 * math.pi / n_teeth
        for da, rr in ((-0.5, r - 3), (-0.2, r - 3), (-0.1, r + 3), (0.1, r + 3), (0.2, r - 3)):
            pts.append((cx + rr * math.cos(a + da * p), cy + rr * math.sin(a + da * p)))
    pts = np.array(pts)
    return pj(pts[:, 0], pts[:, 1], np.full(len(pts), z))


def belt_path(pj, z):
    """Outer belt around the crank sprocket and the two cam sprockets (sampled hull)."""
    pts = []
    for (cx, cy, r) in ((0.0, CR_Y, SPK_CR + 4), (-VX, CAM_Y, SPK_CC + 4), (VX, CAM_Y, SPK_CC + 4)):
        th = np.linspace(0, 2 * np.pi, 90, endpoint=False)
        pts.append(np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1))
    h = hull(np.vstack(pts))
    h = np.vstack([h, h[:1]])
    return pj(h[:, 0], h[:, 1], np.full(len(h), z))


# ================================================================== the engine
def draw_engine(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return pj
    ph = phi_at(t)
    li, le, cyc = lifts(ph)
    top = crown_y(ph)
    pin = pin_y(ph)
    cpin = (CR_R * math.sin(ph), CR_Y - CR_R * math.cos(ph))
    ang_cam_i = -math.pi / 2 + (ph / 2 - math.pi / 4)
    ang_cam_e = -math.pi / 2 + (ph / 2 - 1.75 * math.pi)
    hl = lambda t0, t1: win(t, t0 - 0.1, t1, 0.2, 0.4)
    h_piston = hl(T_PISTON, T_ROD + 0.2)
    h_cyl = hl(T_CYL, T_ROD + 0.4)
    h_rod = hl(T_ROD, T_TURNING + 0.6)
    h_crank = hl(T_CRANK, T_UPTOP)
    h_valves = hl(T_VALVES, T_INTAKE + 0.3)
    h_plug = hl(T_PLUG, T_INTAKE + 0.5) + hl(T_BEFORE, T_EXPANDS)
    h_fly = hl(T_FLYWHEEL, T_CAMSHAFT + 0.2)
    h_cam = hl(T_CAMSHAFT, T_OUTRO + 0.4)
    h_iv = hl(T_IN_VALVE, T_FUEL_E + 0.3)
    h_ev = hl(T_EX_OPENS, T_OUT_E + 0.3)

    cv.saveLayerAlpha(None, int(255 * kE))
    # ---- flywheel (behind the crank)
    fz0, fz1 = 34.0, 54.0
    rev(cv, pj, "z", (0.0, CR_Y), [fz0, fz1], [FLY_R, FLY_R], C_FLY, n=96,
        edge=YEL if h_fly > 0.02 else None, edge_w=2.0 + 1.5 * h_fly, glow=h_fly)
    for k in range(6):                                   # spokes so its rotation reads
        a = ph + k * math.pi / 3
        p0 = pj(30 * math.cos(a), CR_Y + 30 * math.sin(a), fz0)
        p1 = pj((FLY_R - 18) * math.cos(a), CR_Y + (FLY_R - 18) * math.sin(a), fz0)
        cv.drawLine(*p0, *p1, paint(shade(C_FLY, 0.6), stroke=6 * pj.s))
    a = ph - math.pi / 2
    mk = pj((FLY_R - 9) * math.cos(a), CR_Y + (FLY_R - 9) * math.sin(a), fz0)
    cv.drawCircle(*mk, 5 * pj.s, paint(YEL, a=0.9))
    # ---- crank: main journal, back web, pin, rod, front web
    rev(cv, pj, "z", (0.0, CR_Y), [-40, fz0], [15, 15], STEEL, n=36)

    def web(z0, z1):
        prof = []
        for th in np.linspace(0, 2 * np.pi, 60, endpoint=False):
            # throw towards the pin, counterweight opposite
            d = (th - (ph - math.pi / 2)) % (2 * math.pi)
            r = 22 + (CR_R - 4) * max(0.0, math.cos(d)) ** 6 + 52 * max(0.0, -math.cos(d)) ** 0.7
            prof.append((r * math.cos(th), CR_Y + r * math.sin(th)))
        extrude(cv, pj, np.array(prof), z0, z1, mix(STEEL_D, YEL, 0.25 * h_crank),
                rim=YEL if h_crank > 0.02 else None, rim_w=2.0, rim_glow=h_crank)
    web(10.0, 22.0)
    rev(cv, pj, "z", cpin, [-12, 12], [12, 12], STEEL, n=28)
    # rod (tapered beam from the crank pin to the piston pin)
    v = np.array([0.0 - cpin[0], pin - cpin[1]])
    v /= np.linalg.norm(v)
    n = np.array([-v[1], v[0]])
    big, small = np.array(cpin), np.array([0.0, pin])
    rod = [big + n * 16, small + n * 10, small - n * 10, big - n * 16]
    extrude(cv, pj, np.array(rod), -7, 7, mix(C_ROD, YEL, 0.3 * h_rod), rim=YEL if h_rod > 0.02 else None,
            rim_w=2.0, rim_glow=h_rod)
    extrude(cv, pj, circle_prof(big[0], big[1], 22, 32), -7, 7, mix(C_ROD, YEL, 0.3 * h_rod))
    web(-22.0, -10.0)
    # ---- liner back wall (glass)
    rev(cv, pj, "y", (0.0, 0.0), [0, LINER_Y1], [RB + 6, RB + 6], hx("#2a3446"), fill_a=0.32,
        edge=mix(hx("#4b5a72"), YEL, h_cyl), edge_w=1.6 + 1.4 * h_cyl, glow=h_cyl, caps=False)
    # ---- charge
    frac, gc = gas_state(t, cyc)
    nv = int(round(NDOT * frac))
    for i in range(nv):
        r, an, h = DOTS[i]
        X, z = r * (RB - 10) * math.cos(an), r * (RB - 10) * math.sin(an)
        Y = 3 + h * (top - 6)
        q = pj(X, Y, z)
        cv.drawCircle(q[0], q[1], 7 * pj.s, paint(gc, a=0.28, blur=4 * pj.s))
        cv.drawCircle(q[0], q[1], 3.8 * pj.s, paint(gc))
    bk = burn_k(t)
    if bk > 0:
        q = pj(0, top * 0.5, 0)
        cv.drawCircle(q[0], q[1], (40 + top * 0.6) * pj.s, paint(hx("#ff7a2a"), a=0.5 * bk, blur=22 * pj.s))
    # ---- piston
    rev(cv, pj, "y", (0.0, 0.0), [top, top + PISTON_H], [RB - 2, RB - 2], mix(STEEL, YEL, 0.25 * h_piston),
        edge=YEL if h_piston > 0.02 else None, edge_w=2 + 1.5 * h_piston, glow=h_piston)
    for yy in (top + 9, top + 17, top + 25):
        ring_front(cv, pj, "y", (0.0, 0.0), yy, RB - 1, shade(STEEL, 0.45), width=2.0)
    # combustion bloom in front of the chamber right after the spark
    if bk > 0:
        q = pj(0, top * 0.5, -20)
        cv.drawCircle(q[0], q[1], (55 + top * 0.5) * pj.s, paint(hx("#ff8a2a"), a=0.35 * bk, blur=26 * pj.s))
        cv.drawCircle(q[0], q[1], (22 + top * 0.25) * pj.s, paint(hx("#ffe2a0"), a=0.35 * bk, blur=12 * pj.s))
    # ---- valves, springs, buckets
    for vx, lift, cc, hv in ((-VX, li, CYAN, max(h_iv, h_valves)), (VX, le, AMBER, max(h_ev, h_valves))):
        open_k = clamp(lift / 2.0)
        rev(cv, pj, "y", (vx, 0.0), [-100 + lift, lift - 4], [4.5, 4.5], STEEL, n=24)
        rev(cv, pj, "y", (vx, 0.0), [lift - 7, lift], [10, VR], STEEL, n=40,
            edge=cc if (open_k > 0.05 or hv > 0.02) else None, edge_w=2.2, glow=max(open_k, hv))
        draw_spring(cv, pj, vx, 0.0, 13, -100 + lift, HEAD_TOP, 5, STEEL_D, width=3.2)
        rev(cv, pj, "y", (vx, 0.0), [BUCKET_TOP0 + lift, -100 + lift], [16, 16], STEEL, n=36,
            edge=cc if hv > 0.02 else None, glow=hv)
    # ---- camshafts + lobes
    for vx, ang, cc in ((-VX, ang_cam_i, CYAN), (VX, ang_cam_e, AMBER)):
        rev(cv, pj, "z", (vx, CAM_Y), [-30, 60], [8, 8], STEEL_D, n=24)
        extrude(cv, pj, cam_prof(vx, CAM_Y, ang), -14, 14, STEEL, rim=YEL if h_cam > 0.02 else None,
                rim_w=2.0, rim_glow=h_cam)
        nose = pj(vx + (CAM_BASE + LIFT - 3) * math.cos(ang), CAM_Y + (CAM_BASE + LIFT - 3) * math.sin(ang), -14)
        cv.drawCircle(*nose, 3.5 * pj.s, paint(cc, a=0.9))
    # ---- head (glass) with ports
    head = np.array([[-118, HEAD_TOP], [118, HEAD_TOP], [118, 0], [-118, 0]], float)
    extrude(cv, pj, head, -60, 60, C_HEAD, alpha=0.45)
    in_pts = resample(spline(pj(IN_PORT[:, 0], IN_PORT[:, 1], np.zeros(len(IN_PORT))), 60), 80)
    ex_pts = resample(spline(pj(EX_PORT[:, 0], EX_PORT[:, 1], np.zeros(len(EX_PORT))), 60), 80)
    pipe(cv, in_pts, 26 * pj.s, CYAN, glass=True)
    pipe(cv, ex_pts, 26 * pj.s, AMBER, glass=True)
    k_in = clamp(li / 3.0)
    k_ex = clamp(le / 3.0)
    sp = 140 * pj.s * max(0.4, abs(omega(t)) / W_SLOW) ** 0.5
    flow(cv, in_pts, t, sp, 22 * pj.s, CYAN, r=4.2 * pj.s, a=k_in)
    flow(cv, ex_pts, t, sp, 22 * pj.s, C_BURNT, r=4.2 * pj.s, a=k_ex)
    # ---- spark plug
    rev(cv, pj, "y", (0.0, 0.0), [-150, -90], [9, 9], hx("#e8ecf2"), n=28,
        edge=YEL if h_plug > 0.02 else None, glow=h_plug)
    rev(cv, pj, "y", (0.0, 0.0), [-90, -72], [13, 13], STEEL, n=6)
    rev(cv, pj, "y", (0.0, 0.0), [-72, -2], [7, 7], STEEL_D, n=24)
    sk = spark_k(t)
    if sk > 0:
        q = pj(0, 2, 0)
        cv.drawCircle(q[0], q[1], 26 * pj.s, paint(hx("#bfe8ff"), a=0.8 * sk, blur=10 * pj.s))
        cv.drawCircle(q[0], q[1], 7 * pj.s, paint(INK, a=sk))
        rng = np.random.default_rng(int(t * 30))
        for _ in range(5):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(8, 22)
            cv.drawLine(q[0], q[1], q[0] + r * math.cos(a) * pj.s, q[1] + r * math.sin(a) * pj.s,
                        paint(hx("#dff4ff"), a=sk, stroke=2 * pj.s))
    # ---- liner front edge
    ring_front(cv, pj, "y", (0.0, 0.0), LINER_Y1, RB + 6, hx("#6b7c96"), width=2)
    # ---- timing drive (x-ray outline at the front), shown for the camshaft beat
    kt = win(t, T_CAMSHAFT - 0.3, T_END + 0.2, 0.4, 0.3)
    if kt > 0:
        zt = -60.0
        bp_ = belt_path(pj, zt)
        cv.drawPath(poly_path(bp_, close=False), paint(YEL, a=0.35 * kt, stroke=10 * pj.s, blur=5 * pj.s))
        cv.drawPath(poly_path(bp_, close=False), paint(hx("#20283a"), a=0.85 * kt, stroke=6 * pj.s))
        bpaint = paint(YEL, a=0.9 * kt, stroke=2.0 * pj.s)
        bpaint.setPathEffect(skia.DashPathEffect.Make([8 * pj.s, 6 * pj.s], -(ph * SPK_CR * pj.s) % (14 * pj.s)))
        cv.drawPath(poly_path(bp_, close=False), bpaint)
        for cx, cy, r, nt, ang in ((0.0, CR_Y, SPK_CR, 20, ph), (-VX, CAM_Y, SPK_CC, 40, ph / 2),
                                   (VX, CAM_Y, SPK_CC, 40, ph / 2)):
            sp_ = sprocket_pts(pj, cx, cy, zt, r, nt, ang)
            cv.drawPath(poly_path(sp_), paint(hx("#0b111c"), a=0.55 * kt))
            cv.drawPath(poly_path(sp_), paint(STEEL, a=kt, stroke=1.8 * pj.s))
            m = pj(cx + (r - 9) * math.cos(ang - math.pi / 2), cy + (r - 9) * math.sin(ang - math.pi / 2), zt)
            c0 = pj(cx, cy, zt)
            cv.drawLine(*c0, *m, paint(YEL, a=kt, stroke=3 * pj.s))
            cv.drawCircle(*m, 4.5 * pj.s, paint(YEL, a=kt))
    cv.restore()
    return pj


# ================================================================== overlays
def draw_hook(cv, t):
    k = 1 - ease(lin(t, T_HOOK_OUT + 0.1, T_WHAT + 0.4))
    if k <= 0:
        return
    # 25 spark dots firing in a ripple, one every 1/25 s (real time)
    n = 25
    k_in = eout(lin(t, T_TWENTY - 0.4, T_TWENTY))
    x0, dx = 540 - 12 * 33, 33
    for i in range(n):
        ph = (t * 25 - i) % 25
        lit = clamp(1 - ph / 6.0) if t > T_TWENTY - 0.4 else 0.0
        c = mix(hx("#2a3446"), hx("#bfe8ff"), lit)
        x = x0 + i * dx
        if lit > 0.05:
            cv.drawCircle(x, 1300, 13, paint(hx("#7fd4ff"), a=0.6 * lit * k * k_in, blur=8))
        cv.drawCircle(x, 1300, 9, paint(c, a=k * max(0.35, k_in)))
    a2 = k * eout(lin(t, T_TWENTY - 0.1, T_TWENTY + 0.3))
    draw_text(cv, "25 SPARKS EVERY SECOND", 540, 1362, font("inter_xb", 34), INK, a=a2, align="center", tracking=3)
    a3 = k * eout(lin(t, T_RPM - 0.4, T_RPM))
    pill(cv, 540, 1236, "3,000 RPM · ONE CYLINDER", font("inter_xb", 26), INK, border=AMBER, a=a3, align="center",
         tracking=2)


STROKES = [("INTAKE", CYAN), ("COMPRESSION", YEL), ("POWER", RED), ("EXHAUST", AMBER)]


def draw_what(cv, t):
    k = win(t, T_FOUR_W - 0.2, T_PARTS + 0.2, 0.3, 0.3)
    if k <= 0:
        return
    items = []
    for i, (nm, _) in enumerate(STROKES):
        tt = T_FOUR_W + (T_TWO - T_FOUR_W) * i / 4
        items.append((nm, eout(lin(t, tt, tt + 0.25))))
    brand.chips(cv, k, 1290, items, center=True)
    k2 = k * eout(lin(t, T_TWO - 0.1, T_TWO + 0.25))
    if k2 > 0:
        pill(cv, 540, 1360, "= 2 CRANK TURNS · 720°", font("inter_xb", 30), INK, border=YEL, a=k2, align="center",
             tracking=2)


def draw_labels(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return
    ph = phi_at(t)
    top = crown_y(ph)
    t_out = T_INTAKE + 0.2
    brand.label(cv, t, "PISTON", tuple(pj(-RB + 6, top + 30, -20)), (80, 760), STEEL, T_PISTON - 0.05, T_ROD)
    brand.label(cv, t, "CYLINDER", tuple(pj(RB + 4, 150, -30)), (930, 760), hx("#6b7c96"), T_CYL - 0.05, T_ROD + 0.4,
                align="right")
    cpin = (CR_R * math.sin(ph), CR_Y - CR_R * math.cos(ph))
    mid = ((cpin[0]) / 2, (cpin[1] + pin_y(ph)) / 2)
    brand.label(cv, t, "CONNECTING ROD", tuple(pj(mid[0] - 8, mid[1], -7)), (80, 900), C_ROD, T_ROD - 0.05,
                T_UPTOP)
    brand.label(cv, t, "CRANKSHAFT", tuple(pj(0, CR_Y + 40, -22)), (930, 1100), STEEL, T_CRANK - 0.05, T_UPTOP,
                align="right")
    k = win(t, T_TURNING - 0.1, T_UPTOP, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "UP-AND-DOWN → ROTATION", font("inter_xb", 28), INK, border=YEL, a=k, align="center",
             tracking=2)
    brand.label(cv, t, "VALVES", tuple(pj(-VX - 12, -86, 0)), (80, 560), STEEL, T_VALVES - 0.05, t_out)
    brand.label(cv, t, "SPARK PLUG", tuple(pj(8, -130, 0)), (930, 560), INK, T_PLUG - 0.05, t_out + 0.4,
                align="right")
    brand.label(cv, t, "INTAKE VALVE", tuple(pj(-VX - 14, -86, 0)), (80, 560), CYAN, T_IN_VALVE - 0.05, T_COMP)
    brand.label(cv, t, "AIR + FUEL", tuple(pj(-200, -60, 0)), (80, 690), CYAN, T_AIR - 0.05, T_COMP)
    brand.label(cv, t, "EXHAUST VALVE", tuple(pj(VX + 14, -86, 0)), (930, 560), AMBER, T_EX_OPENS - 0.25, T_CAM,
                align="right")
    brand.label(cv, t, "BURNT GAS OUT", tuple(pj(200, -60, 0)), (930, 690), C_BURNT, T_PUSHES - 0.05, T_CAM,
                align="right")
    brand.label(cv, t, "FLYWHEEL", tuple(pj(-FLY_R + 10, CR_Y + 40, 34)), (80, 1240), YEL, T_FLYWHEEL - 0.05,
                T_CAMSHAFT + 0.1)
    brand.label(cv, t, "CAMSHAFTS", tuple(pj(-VX - 24, CAM_Y - 10, -14)), (80, 520), YEL, T_CAMSHAFT - 0.05,
                T_OUTRO + 0.3)
    k = win(t, T_HALF - 0.1, T_OUTRO + 0.3, 0.25, 0.3) * kE
    if k > 0:
        pill(cv, 540, 1372, "40 TEETH : 20 TEETH  =  CAM AT HALF SPEED", font("inter_xb", 26), INK, border=YEL, a=k,
             align="center", tracking=1.5)


def draw_beats(cv, t):
    kE = 1 - current.ending_k(t)
    k = win(t, T_TEN - 0.2, T_KEY + 0.2, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "SQUEEZED TO 1/10 THE VOLUME", font("inter_xb", 30), INK, border=YEL, a=k, align="center",
             tracking=2)
    k = win(t, T_BEFORE - 0.1, T_FIRES + 0.4, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "SPARK · 20° BEFORE THE TOP", font("inter_xb", 30), INK, border=INK, a=k, align="center",
             tracking=2)
    k = win(t, T_ONLY - 0.1, T_EXH + 0.2, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "THE ONLY STROKE THAT MAKES POWER", font("inter_xb", 30), INK, border=RED, a=k,
             align="center", tracking=2)
    k = win(t, T_THREE - 0.6, T_CAMSHAFT, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "STORED SPIN · CARRIES 3 STROKES", font("inter_xb", 28), INK, border=YEL, a=k,
             align="center", tracking=2)
    k = win(t, T_OTTO - 0.2, T_END + 0.05, 0.25, 0.25) * kE
    if k > 0:
        pill(cv, 540, 1372, "OTTO ENGINE · 1876", font("inter_xb", 30), INK, border=MUTED, a=k, align="center",
             tracking=3)


def stroke_of(t):
    if t < T_INTAKE:
        return None
    if t < T_COMP:
        return 0
    if t < T_KEY:
        return 1
    if t < T_EXH:
        return 2
    if t < T_CAM:
        return 3
    return None


def draw_header(cv, t):
    k = win(t, T_WHAT + 0.3, T_END, 0.3, 0.3)
    if k <= 0:
        return
    s = stroke_of(t)
    if s is None:
        cyc = phi_at(t) % (4 * math.pi)
        s_live = int(cyc // math.pi)
        nm, c = STROKES[s_live]
        txt = nm
    else:
        nm, c = STROKES[s]
        txt = f"STROKE {s + 1} · {nm}"
    brand.status_pill(cv, k, txt, c)
    cyc = phi_at(t) % (4 * math.pi)
    deg = math.degrees(cyc)
    brand.readout(cv, k, f"{int(round(deg)) % 720}°", "CRANK ANGLE / 720", frac=cyc / (4 * math.pi), bar_color=c)
    brand.note(cv, "ANIMATION SLOWED", k * 0.9)


def draw_stamps(cv, t):
    brand.stamp(cv, t, "BANG!", T_FIRES + 0.02, center=(800, 880))


def draw(cv, t):
    draw_engine(cv, t)
    draw_hook(cv, t)
    draw_what(cv, t)
    draw_labels(cv, t)
    draw_beats(cv, t)
    draw_header(cv, t)
    draw_stamps(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_FIRES
MUSIC_START = T_WHAT


def _rpm(t):
    return smooth(t, [(0, 3000), (T_SLOWED, 3000), (T_SLOWED + 1.6, 900), (T_OTTO, 900), (T_OTTO + 1.5, 2400)])


def sound():
    sfx = [(T_HOOK_OUT - 0.1, "whoosh_big", 0.6), (T_SLOWED, "whoosh_down", 0.45),
           (T_PISTON, "tick", 0.2), (T_ROD, "tick", 0.2), (T_CRANK, "tick", 0.2), (T_VALVES, "tick", 0.2),
           (T_OPENS, "clunk", 0.3), (T_DROPS, "hiss", 0.35), (T_CLOSE, "clunk", 0.4),
           (T_FIRES, "impact", 0.65), (T_EXPANDS, "whoosh_down", 0.45), (T_EX_OPENS, "clunk", 0.3),
           (T_PUSHES, "hiss", 0.4), (T_FLYWHEEL, "whoosh_up", 0.3), (T_HALF, "tick", 0.25)]
    eng = {"rpm": _rpm, "bright": lambda t: 0.3,
           "env": [(0, 0.9), (T_SLOWED, 0.9), (T_SLOWED + 1.2, 0.0), (T_OTTO, 0.0), (T_OTTO + 1.2, 0.35),
                   (T_END, 0.35), (T_END + 0.6, 0.0), (T_TOTAL, 0.0)]}
    return {"build": (T_COMP, T_FIRES), "drop": (T_FIRES, T_OUTRO - 0.05), "sfx": sfx, "engine": eng}
