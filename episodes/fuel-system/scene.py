"""Fuel system visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Two views:
  OVERVIEW  exploded 3/4 (oblique) view of the whole system, engine stacked above the tank (schematic, not to scale):
            tank (glass, fuel inside) -> in-tank electric pump module with a returnless regulator on top ->
            line -> in-line filter -> fuel rail -> four injectors into the cylinder head. Filler neck on the tank;
            EVAP charcoal canister between tank and engine (vapour line in, purge line to the engine).
  CLOSE-UP  section through ONE cylinder: intake port with air flowing to the intake valve, solenoid injector aimed
            into the port, cylinder + piston from a slider-crank model, exhaust valve + port with the oxygen sensor,
            and (direct beat) a direct injector in the combustion chamber fed by an engine-driven high-pressure pump.
Engine cycle (close-up): crank angle th (deg, 0 = TDC start of intake, 720 per cycle). Intake valve open over
  ~0..200, exhaust valve open over ~520..720, spark/combustion at 360. Port injection happens while the intake valve
  is open and air is flowing (narrated); the pulse width (ms-ish, schematic) grows on "longer pulse".
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, pipe, flow, spline, resample, arrow_head, path_len, point_at

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_FILL = F("hook", "fill")
T_WHAT = L("what")["start"]
T_PRESS_W = F("what", "pressurized")
T_PIPELINE = F("what", "pipeline")
T_EVERY = F("what", "every")
T_PROB = L("problem")["start"]
T_LOW = F("problem", "low")
T_FRONT = F("problem", "front,")
T_UNDER = F("problem", "pressure,")
T_RIGHT = F("problem", "right")
T_PARTS = L("parts")["start"]
T_PUMP = F("parts", "electric")
T_SUBM = F("parts", "submerged")
T_COOL = F("parts", "cool.")
T_LINE = F("parts", "line")
T_FILTER = F("parts", "filter")
T_RAIL = F("parts", "rail,")
T_INJ = F("parts", "injector")
T_HOW = L("how")["start"]
T_PUSHES = F("how", "pushes")
T_FORTY = F("how", "forty")
T_REG = F("how", "regulator")
T_STEADY = F("how", "steady.")
T_KEY = L("key")["start"]
T_COMPUTER = F("key", "computer")
T_PULSE = F("key", "pulse")
T_MAGNET = F("key", "electromagnet")
T_PULLS = F("key", "pulls")
T_BURSTS = F("key", "bursts")
T_MIST = F("key", "mist,")
T_AIR = F("key", "air")
T_VALVE = F("key", "valve.")
T_RESULT = L("result")["start"]
T_LONGER = F("result", "longer")
T_MORE = F("result", "more")
T_OXY = F("result", "oxygen")
T_RICH = F("result", "rich")
T_LEAN = F("result", "lean,")
T_CORRECTS = F("result", "corrects")
T_DIRECT = L("direct")["start"]
T_SECOND = F("direct", "second")
T_PUMP2 = F("direct", "pump")
T_SPRAY = F("direct", "spray")
T_STRAIGHT = F("direct", "straight")
T_HIGHER = F("direct", "higher")
T_OUTRO = L("outro")["start"]
T_FUMES = F("outro", "fumes?")
T_CHARCOAL = F("outro", "charcoal")
T_BURNS = F("outro", "burns")

# view switch
T_CU_IN = T_KEY - 0.35
T_CU_OUT = T_OUTRO - 0.15


def cu_k(t):
    """0 = overview, 1 = close-up."""
    return ease(lin(t, T_CU_IN, T_CU_IN + 0.6)) * (1 - ease(lin(t, T_CU_OUT, T_CU_OUT + 0.6)))


# ================================================================== overview geometry (world units)
Z0 = 60.0                                   # depth plane of the fuel path
TANK_X0, TANK_X1, TANK_Y0, TANK_Y1, TANK_Z1 = -300.0, 300.0, 150.0, 360.0, 160.0
PUMP_X, PUMP_Y0, PUMP_Y1, PUMP_R = -150.0, 175.0, 345.0, 30.0
HEAD_X0, HEAD_X1, HEAD_Y0, HEAD_Y1, HEAD_Z1 = -300.0, 300.0, -400.0, -260.0, 140.0
RAIL_Y, RAIL_R = -505.0, 17.0
INJ_X = [-225.0, -75.0, 75.0, 225.0]
INJ_TOP, INJ_TIP = -492.0, -400.0
FILT_X, FILT_Y0, FILT_Y1, FILT_R = -390.0, -150.0, -50.0, 28.0
CAN_X, CAN_Y0, CAN_Y1, CAN_R = 190.0, -60.0, 50.0, 34.0
FIRING = [0, 2, 3, 1]                        # 1-3-4-2 firing order


def level_y(t):
    """Fuel surface (Y down): rises while filling in the hook."""
    return 245.0 - 22.0 * ease(lin(t, 0.0, T_HOOK_OUT + 0.5))


def cam_ov(t):
    k = ease(lin(t, T_HOOK_OUT - 0.3, T_WHAT + 0.6))
    ox, oy, s = 525.0 + 15 * k, 1010.0, 0.96 + 0.04 * k
    # zoom toward injector 2 as we cut to the close-up, and back out for the outro
    kz = ease(lin(t, T_CU_IN - 0.15, T_CU_IN + 0.6)) * (1 - ease(lin(t, T_CU_OUT, T_CU_OUT + 0.6)))
    if kz <= 0:
        return Proj(ox, oy, s, dx=0.42, dy=-0.30)
    f = Proj(ox, oy, s, dx=0.42, dy=-0.30)(-75, INJ_TIP, Z0)
    s2 = s * (1 + 1.8 * kz)
    return Proj(f[0] - (f[0] - ox) * s2 / s, f[1] - (f[1] - oy) * s2 / s, s2, dx=0.42, dy=-0.30)


def fuel_path(pj):
    """Pump outlet -> up out of the tank -> left -> filter -> up -> rail (screen polyline)."""
    pts = [(PUMP_X, PUMP_Y0 - 8), (PUMP_X, 95), (PUMP_X - 40, 70), (FILT_X + 30, 70), (FILT_X, 40),
           (FILT_X, FILT_Y1), (FILT_X, FILT_Y0), (FILT_X, -440), (FILT_X + 30, RAIL_Y), (HEAD_X0 - 10, RAIL_Y)]
    P = np.array([pj(x, y, Z0) for x, y in pts])
    return resample(P, 160)


def rail_path(pj):
    return resample(np.array([pj(HEAD_X0 - 10, RAIL_Y, Z0), pj(HEAD_X1 - 20, RAIL_Y, Z0)]), 80)


def inj_pulse(t, i):
    """0..1 open state of overview injector i: sequential pulses in firing order (schematic speed)."""
    per = 0.62
    ph = (t / per - FIRING.index(i) / 4.0) % 1.0
    return 1.0 if ph < 0.16 else 0.0


# ================================================================== close-up geometry (screen px)
CYL_X0, CYL_X1 = 450.0, 830.0
DECK_Y = 900.0                     # head / cylinder joint (valve seats)
STROKE = 230.0
ROD = 380.0
TDC_Y = 925.0                      # piston crown at TDC
IV_X, EV_X = 545.0, 735.0          # valve centre lines
VALVE_R = 62.0
IV_LIFT, EV_LIFT = 46.0, 40.0
INJ_TIP_CU = np.array([395.0, 742.0])
INJ_BACK_CU = np.array([215.0, 470.0])
DI_TIP = np.array([478.0, 893.0])
DI_BACK = np.array([262.0, 846.0])
CYL_BOT = 1250.0
ECU = (428.0, 386.0, 100.0, 60.0)


def piston_y(th):
    a = math.radians(th)
    r = STROKE / 2
    x = r * math.cos(a) + math.sqrt(ROD ** 2 - (r * math.sin(a)) ** 2)
    return TDC_Y + (r + ROD - x)


def bump(th, a0, a1):
    u = ((th % 720) - a0) / (a1 - a0)
    return math.sin(math.pi * u) ** 1.2 if 0 < u < 1 else 0.0


def iv_lift(th):
    return IV_LIFT * bump(th, -10, 210)


def ev_lift(th):
    return EV_LIFT * bump(th % 720, 510, 730)


# crank-angle schedule: slowed intake stroke narrated over the key line, then free cycles
T_TH0 = T_KEY - 0.4
T_TH1 = T_RESULT
PER_CU = 1.35                       # seconds per 720 deg after the narrated stroke (animation slowed)


def theta(t):
    if t < T_TH0:
        return -20.0
    if t < T_TH1:
        return -20.0 + 200.0 * ease(lin(t, T_COMPUTER, T_VALVE + 0.6)) * 1.0 + 0.0
    return 180.0 + 720.0 * (t - T_TH1) / PER_CU


def pulse_ms(t):
    """Schematic injector pulse width in ms: grows on 'longer', settles a touch on 'corrects'."""
    w = 3.0 + 2.2 * ease(lin(t, T_LONGER, T_MORE + 0.3)) - 0.7 * ease(lin(t, T_CORRECTS, T_CORRECTS + 0.6))
    return w


def port_inj_open(t):
    """Open state 0..1 of the close-up port injector."""
    if t < T_RESULT:
        k = ease(lin(t, T_PULLS - 0.05, T_PULLS + 0.2)) * (1 - ease(lin(t, T_AIR + 0.3, T_VALVE)))
        return k
    if t > T_SECOND + 0.3:
        return 0.0
    th = theta(t) % 720
    dur = pulse_ms(t) * 14.0          # deg of crank per ms (schematic)
    return 1.0 if 20 <= th < 20 + dur else 0.0


def di_open(t):
    if t < T_SPRAY - 0.2:
        return 0.0
    th = theta(t) % 720
    return 1.0 if 60 <= th < 120 else 0.0


def coil_k(t):
    if t < T_RESULT:
        return ease(lin(t, T_PULSE - 0.05, T_PULSE + 0.25)) * (1 - ease(lin(t, T_AIR + 0.3, T_VALVE)))
    return port_inj_open(t)


def check_physics():
    bad = []
    for t in np.arange(T_KEY, T_OUTRO, 0.02):
        th = theta(t)
        if port_inj_open(t) > 0.5 and iv_lift(th) < 5 and t < T_RESULT:
            bad.append(f"narrated spray with the intake valve shut at {t:.2f}")
            break
        if iv_lift(th) > 1 and ev_lift(th) > 1 and not (th % 720 > 700 or th % 720 < 20):
            bad.append(f"valves overlap mid-cycle at {t:.2f}")
            break
        py = piston_y(th)
        if py - 4 < DECK_Y + max(iv_lift(th), ev_lift(th)) and iv_lift(th) > 10:
            bad.append(f"valve hits piston at {t:.2f}")
            break
    if iv_lift(theta(T_BURSTS + 0.2)) < 20:
        bad.append("intake valve not open on 'bursts'")
    return bad


assert not check_physics(), check_physics()


# ================================================================== helpers
def hl(t, t0, t1):
    return win(t, t0 - 0.1, t1, 0.2, 0.4)


def box_faces(pj, x0, x1, y0, y1, z0, z1):
    c = lambda x, y, z: pj(x, y, z)
    front = np.array([c(x0, y0, z0), c(x1, y0, z0), c(x1, y1, z0), c(x0, y1, z0)])
    top = np.array([c(x0, y0, z0), c(x1, y0, z0), c(x1, y0, z1), c(x0, y0, z1)])
    right = np.array([c(x1, y0, z0), c(x1, y0, z1), c(x1, y1, z1), c(x1, y1, z0)])
    return front, top, right


def glass_box(cv, pj, x0, x1, y0, y1, z1, edge, a=1.0, fill=hx("#0e1a2c"), fill_a=0.55, glow=0.0):
    fr, tp, rt = box_faces(pj, x0, x1, y0, y1, 0, z1)
    sil = np.vstack([fr, tp, rt])
    from ev.gfx import _hull
    hp = poly_path(_hull(sil))
    cv.drawPath(hp, paint(fill, a=fill_a * a))
    return fr, tp, rt, hp


def glass_edges(cv, fr, tp, rt, edge, a=1.0, w=2.2, glow=0.0):
    for poly in (tp, rt, fr):
        pth = poly_path(poly)
        if glow > 0:
            cv.drawPath(pth, paint(edge, a=0.5 * glow * a, stroke=w * 3, blur=6))
        cv.drawPath(pth, paint(edge, a=a, stroke=w))


def arrow(cv, p0, p1, c, a=1.0, w=10):
    if a <= 0:
        return
    p0, p1 = np.array(p0, float), np.array(p1, float)
    v = p1 - p0
    n = np.linalg.norm(v)
    v /= n
    base = p1 - v * w * 2.2
    cv.drawLine(*p0, *base, paint(c, a=a, stroke=w))
    nrm = np.array([-v[1], v[0]])
    cv.drawPath(poly_path(np.array([p1, base + nrm * w * 1.4, base - nrm * w * 1.4])), paint(c, a=a))


def mist(cv, tip, d, t, k, spread=0.45, length=150, n=46, seed=1, r=3.2, color=AMBER, carry=None):
    """Cone of fine droplets from tip along direction d. carry: extra drift vector (air carrying the mist)."""
    if k <= 0:
        return
    rng = np.random.default_rng(seed)
    d = np.array(d, float) / np.linalg.norm(d)
    nrm = np.array([-d[1], d[0]])
    for j in range(n):
        u = (rng.uniform(0, 1) + t * 2.4) % 1.0
        ang = rng.uniform(-spread, spread)
        dd = d * math.cos(ang) + nrm * math.sin(ang)
        p = np.array(tip) + dd * length * u
        if carry is not None:
            p = p + np.array(carry) * u * u
        a = k * (1 - 0.7 * u)
        cv.drawCircle(p[0], p[1], r * (0.7 + 0.8 * u), paint(color, a=a))
    cv.drawCircle(tip[0], tip[1], 18, paint(color, a=0.35 * k, blur=10))


# ================================================================== overview
def draw_overview(cv, t):
    kv = (1 - cu_k(t)) * (1 - current.ending_k(t))
    if kv <= 0.01:
        return
    pj = cam_ov(t)
    S = pj.s
    cv.saveLayerAlpha(None, int(255 * kv))

    h_pump = hl(t, T_PUMP, T_LINE) + hl(t, T_PUSHES, T_FORTY)
    h_filt = hl(t, T_FILTER, T_RAIL)
    h_rail = hl(t, T_RAIL, T_INJ)
    h_inj = hl(t, T_INJ, T_HOW)
    h_reg = hl(t, T_REG, T_KEY)
    h_tank = hl(t, T_LOW, T_FRONT)
    h_eng = hl(t, T_FRONT, T_RIGHT + 0.6)
    pumping = 1.0
    flow_sp = (150 + 160 * ease(lin(t, T_PUSHES, T_PUSHES + 0.5))) * S

    # ---------- cylinder head (x-ray) with four ports
    fr, tp, rt, _ = glass_box(cv, pj, HEAD_X0, HEAD_X1, HEAD_Y0, HEAD_Y1, HEAD_Z1, STEEL, fill=hx("#1a2333"),
                              fill_a=0.85)
    for i, x in enumerate(INJ_X):
        port = np.array([pj(x - 38, HEAD_Y0 + 30, Z0), pj(x + 38, HEAD_Y0 + 30, Z0), pj(x + 38, HEAD_Y1 - 10, Z0),
                         pj(x - 38, HEAD_Y1 - 10, Z0)])
        cv.drawPath(poly_path(port), paint(hx("#0a0f18"), a=0.9))
        cv.drawPath(poly_path(port), paint(hx("#3a4559"), stroke=1.6))
    # mist puffs inside the ports, firing order
    for i, x in enumerate(INJ_X):
        k = inj_pulse(t, i)
        if k > 0:
            tip = pj(x, INJ_TIP + 6, Z0)
            mist(cv, tip, (0, 1), t, k, spread=0.32, length=95 * S, n=22, seed=i + 3, r=2.6 * S)
    glass_edges(cv, fr, tp, rt, mix(hx("#4b5a72"), YEL, clamp(h_eng)), w=2.0, glow=clamp(h_eng))

    # ---------- injectors
    for i, x in enumerate(INJ_X):
        k = inj_pulse(t, i)
        base = mix(hx("#5d6b82"), AMBER, 0.6 * k)
        base = mix(base, YEL, 0.3 * clamp(h_inj))
        rev(cv, pj, "y", (x, Z0), [INJ_TOP, INJ_TIP - 20, INJ_TIP - 8, INJ_TIP], [13, 13, 8, 5], base,
            edge=YEL if h_inj > 0.02 else None, edge_w=1.6, glow=clamp(h_inj))
        q = pj(x, INJ_TOP + 22, Z0)
        cv.drawCircle(q[0] - 14 * S, q[1], 4 * S, paint(AMBER if k else hx("#3a4252")))

    # ---------- fuel line + rail
    fp = fuel_path(pj)
    rp = rail_path(pj)
    pipe(cv, fp, 15 * S, AMBER, glass=True)
    flow(cv, fp, t, flow_sp, 22 * S, AMBER, r=4.2 * S, a=pumping)
    rev(cv, pj, "x", (RAIL_Y, Z0), [HEAD_X0 - 12, HEAD_X1 - 18], [RAIL_R, RAIL_R],
        mix(hx("#7d8798"), YEL, 0.3 * clamp(h_rail)), edge=YEL if h_rail > 0.02 else None, edge_w=2,
        glow=clamp(h_rail), fill_a=0.55)
    flow(cv, rp, t, flow_sp * 0.6, 22 * S, AMBER, r=4.0 * S, a=0.9)
    # pressurized pipeline trace ("what")
    kt = win(t, T_PRESS_W - 0.1, T_PROB, 0.2, 0.4)
    if kt > 0:
        prog = ease(lin(t, T_PIPELINE - 0.1, T_EVERY + 0.3))
        full = np.vstack([fp, rp])
        m = max(2, int(len(full) * prog))
        cv.drawPath(poly_path(full[:m], close=False), paint(YEL, a=0.45 * kt, stroke=22 * S, blur=8))
        cv.drawPath(poly_path(full[:m], close=False), paint(YEL, a=0.9 * kt, stroke=4 * S))
        for i, x in enumerate(INJ_X):
            ki = kt * ease(lin(t, T_EVERY + 0.05 * i, T_EVERY + 0.3 + 0.05 * i))
            if ki > 0:
                q = pj(x, INJ_TIP, Z0)
                cv.drawCircle(q[0], q[1], 16 * S, paint(YEL, a=0.6 * ki, blur=6))

    # ---------- filter
    rev(cv, pj, "y", (FILT_X, Z0), [FILT_Y0, FILT_Y0 + 10, FILT_Y1 - 10, FILT_Y1], [12, FILT_R, FILT_R, 12],
        mix(hx("#9aa5b6"), YEL, 0.3 * clamp(h_filt)), edge=YEL if h_filt > 0.02 else None, edge_w=2,
        glow=clamp(h_filt))
    for yy in np.linspace(FILT_Y0 + 22, FILT_Y1 - 22, 5):
        ring_front(cv, pj, "y", (FILT_X, Z0), yy, FILT_R, hx("#56607a"), width=1.6)

    # ---------- EVAP canister + lines (outro)
    kc = ease(lin(t, T_FUMES - 0.3, T_CHARCOAL + 0.2))
    if kc > 0:
        vap = resample(np.array([pj(CAN_X, TANK_Y0, Z0), pj(CAN_X, CAN_Y1 + 4, Z0)]), 30)
        purge = resample(np.array([pj(CAN_X, CAN_Y0 - 4, Z0), pj(CAN_X, HEAD_Y1 + 2, Z0)]), 30)
        pipe(cv, vap, 10 * S, hx("#9fb3a0"), a=kc, glass=True)
        pipe(cv, purge, 10 * S, hx("#9fb3a0"), a=kc, glass=True)
        h_can = hl(t, T_CHARCOAL, T_END)
        rev(cv, pj, "y", (CAN_X, Z0), [CAN_Y0, CAN_Y1], [CAN_R, CAN_R], mix(hx("#2f3a36"), YEL, 0.25 * h_can),
            alpha=kc, edge=YEL if h_can > 0.02 else None, edge_w=2, glow=clamp(h_can))
        kv1 = win(t, T_FUMES - 0.1, T_END, 0.3, 0.3)
        flow(cv, vap, t, 80 * S, 16 * S, hx("#b9c9bd"), r=3.4 * S, a=kv1 * kc)
        kp = win(t, T_BURNS - 0.2, T_END, 0.3, 0.3)
        flow(cv, purge, t, 110 * S, 16 * S, hx("#b9c9bd"), r=3.4 * S, a=kp * kc)

    # ---------- tank (glass) + fuel + pump module
    fr, tp, rt, _ = glass_box(cv, pj, TANK_X0, TANK_X1, TANK_Y0, TANK_Y1, TANK_Z1, STEEL, fill=hx("#0c1626"),
                              fill_a=0.75)
    ly = level_y(t)
    # pump module (submerged), regulator on top
    rev(cv, pj, "y", (PUMP_X, Z0), [TANK_Y0 + 2, PUMP_Y0], [16, 16], STEEL_D)
    rev(cv, pj, "y", (PUMP_X, Z0), [PUMP_Y0, PUMP_Y0 + 14, PUMP_Y1 - 30, PUMP_Y1], [PUMP_R + 4, PUMP_R, PUMP_R, 18],
        mix(hx("#7b8698"), YEL, 0.3 * clamp(h_pump)), edge=YEL if h_pump > 0.02 else None, edge_w=2,
        glow=clamp(h_pump))
    # motor windings hint
    for yy in np.linspace(PUMP_Y0 + 30, PUMP_Y1 - 45, 4):
        ring_front(cv, pj, "y", (PUMP_X, Z0), yy, PUMP_R + 0.5, hx("#c77a2a"), width=2.2)
    reg = np.array([[PUMP_X + 34, PUMP_Y0 + 2], [PUMP_X + 70, PUMP_Y0 + 2], [PUMP_X + 70, PUMP_Y0 + 34],
                    [PUMP_X + 34, PUMP_Y0 + 34]])
    extrude(cv, pj, reg, Z0 - 14, Z0 + 14, mix(hx("#6d7890"), YEL, 0.35 * clamp(h_reg)),
            rim=YEL if h_reg > 0.02 else None, rim_w=1.6, rim_glow=clamp(h_reg))
    # intake sock at the bottom
    q0 = pj(PUMP_X - 40, TANK_Y1 - 8, Z0)
    q1 = pj(PUMP_X + 40, TANK_Y1 - 8, Z0)
    cv.drawLine(*q0, *q1, paint(hx("#c9cfd8"), a=0.7, stroke=6 * S))
    # fuel volume (translucent, over the pump so it reads as submerged)
    vol = np.vstack(box_faces(pj, TANK_X0 + 3, TANK_X1 - 3, ly, TANK_Y1 - 3, 3, TANK_Z1 - 3))
    from ev.gfx import _hull
    cv.drawPath(poly_path(_hull(vol)), paint(mix(AMBER, hx("#7a4a00"), 0.4), a=0.34))
    surf = np.array([pj(TANK_X0 + 3, ly, 3), pj(TANK_X1 - 3, ly, 3), pj(TANK_X1 - 3, ly, TANK_Z1 - 3),
                     pj(TANK_X0 + 3, ly, TANK_Z1 - 3)])
    cv.drawPath(poly_path(surf), paint(AMBER, a=0.22))
    wob = 3 * math.sin(t * 3.0)
    cv.drawLine(*pj(TANK_X0 + 3, ly + wob * 0.3, 3), *pj(TANK_X1 - 3, ly - wob * 0.3, 3), paint(AMBER, a=0.9, stroke=3))
    # cooling shimmer around the pump on "cool"
    kco = win(t, T_SUBM - 0.1, T_LINE, 0.3, 0.4)
    if kco > 0:
        for j in range(3):
            rr = PUMP_R + 12 + 22 * ((t * 0.9 + j / 3) % 1.0)
            ring = np.array([pj(PUMP_X + rr * math.cos(a), PUMP_Y0 + 80, Z0 + rr * math.sin(a))
                             for a in np.linspace(0, 2 * np.pi, 40)])
            cv.drawPath(poly_path(ring), paint(CYAN, a=kco * (1 - ((t * 0.9 + j / 3) % 1.0)), stroke=2.5))
    # bubbles rising from the sock (fuel drawn in)
    rng = np.random.default_rng(7)
    for j in range(10):
        u = (rng.uniform() + t * 0.8) % 1.0
        x = PUMP_X + rng.uniform(-30, 30)
        y = TANK_Y1 - 10 - u * 40
        q = pj(x, y, Z0 + rng.uniform(-20, 20))
        cv.drawCircle(q[0], q[1], 2.4 * S, paint(AMBER, a=0.7 * (1 - u)))
    # filler neck + fill stream (hook)
    neck = resample(np.array([pj(255, TANK_Y0, Z0), pj(300, 95, Z0), pj(345, 40, Z0)]), 40)
    pipe(cv, neck, 26 * S, STEEL_D)
    cap = pj(345, 40, Z0)
    cv.drawCircle(cap[0], cap[1], 18 * S, paint(hx("#9aa5b6")))
    kf = win(t, -1, T_HOOK_OUT + 0.4, 0.1, 0.5)
    if kf > 0:
        flow(cv, neck[::-1], t, 240 * S, 14 * S, AMBER, r=4.5 * S, a=kf)
        st = resample(np.array([pj(275, TANK_Y0 + 4, Z0), pj(262, ly, Z0)]), 12)
        flow(cv, st, t, 240 * S, 12 * S, AMBER, r=4.0 * S, a=kf)
    glass_edges(cv, fr, tp, rt, mix(hx("#5d7499"), YEL, clamp(h_tank)), w=2.2, glow=clamp(h_tank))
    cv.restore()


# ================================================================== close-up section
C_WALL = hx("#2a3446")
C_AIR = CYAN
C_BURNT = hx("#8a7a6a")
AIR_PATH = None


def air_path():
    return spline([(40, 700), (220, 716), (360, 760), (470, 820), (IV_X - 30, 880), (IV_X, 960), (IV_X + 40, 1040)],
                  120)


def exh_path():
    return spline([(EV_X, 990), (EV_X + 10, 900), (EV_X + 60, 820), (900, 760), (960, 745)], 80)


def draw_closeup(cv, t):
    kv = cu_k(t)
    if kv <= 0.01:
        return
    th = theta(t)
    sc = 0.9 + 0.1 * kv
    cv.saveLayerAlpha(None, int(255 * kv))
    cv.save()
    cv.translate(540, 900)
    cv.scale(sc, sc)
    cv.translate(-540, -900)

    il, el = iv_lift(th), ev_lift(th)
    py = piston_y(th)
    ph = th % 720

    # ---------- head metal (hatched block) with port + exhaust channels cut out
    head = skia.Path()
    head.addRect(skia.Rect.MakeLTRB(60, 610, 940, DECK_Y))
    port = skia.Path()
    ptop = [(40, 640), (240, 650), (380, 700), (480, 780), (IV_X - VALVE_R - 6, DECK_Y)]
    pbot = [(IV_X + VALVE_R + 6, DECK_Y), (600, 840), (560, 800), (440, 760), (230, 780), (40, 780)]
    port = poly_path(np.array(ptop + pbot))
    expo = poly_path(np.array([(EV_X - VALVE_R - 6, DECK_Y), (EV_X - 30, 830), (820, 760), (960, 700), (960, 820),
                               (870, 850), (EV_X + VALVE_R + 6, DECK_Y)]))
    hp = skia.Paint(AntiAlias=True)
    hp.setShader(lin_grad((0, 610), (0, DECK_Y), [hx("#3b475c"), hx("#262f3f")]))
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(60, 610, 940, DECK_Y))
    cv.clipPath(port, skia.ClipOp.kDifference, True)
    cv.clipPath(expo, skia.ClipOp.kDifference, True)
    cv.drawRect(skia.Rect.MakeLTRB(60, 610, 940, DECK_Y), hp)
    hatch = paint(hx("#5f6f8a"), a=0.25, stroke=2)
    for x in range(0, 1100, 26):
        cv.drawLine(x, DECK_Y, x + 290, 610, hatch)
    cv.restore()
    cv.drawPath(port, paint(hx("#0a1220"), a=0.85))
    cv.drawPath(port, paint(hx("#6b7c96"), stroke=2.5))
    cv.drawPath(expo, paint(hx("#0a1220"), a=0.85))
    cv.drawPath(expo, paint(hx("#6b7c96"), stroke=2.5))
    cv.drawLine(60, 610, 940, 610, paint(hx("#6b7c96"), stroke=2))

    # ---------- cylinder
    cv.drawRect(skia.Rect.MakeLTRB(CYL_X0, DECK_Y, CYL_X1, CYL_BOT), paint(hx("#0a1220"), a=0.9))
    for x0 in (CYL_X0 - 40, CYL_X1):
        cv.drawRect(skia.Rect.MakeLTRB(x0, DECK_Y, x0 + 40, CYL_BOT), paint(hx("#2a3446")))
        for yy in range(int(DECK_Y), int(CYL_BOT) - 22, 22):
            cv.drawLine(x0, yy + 22, x0 + 40, yy, paint(hx("#5f6f8a"), a=0.25, stroke=2))
    # gas in the cylinder
    burnt = 300 <= ph < 700
    fl = clamp(1 - (ph - 360) / 120) if 360 <= ph < 480 else 0.0
    if 340 <= ph < 360:
        fl = (ph - 340) / 20
    gas_c = mix(C_BURNT, hx("#ff6a2a"), fl) if burnt else mix(C_AIR, AMBER, 0.35 * clamp(lin(t, T_BURSTS, T_VALVE)))
    gas_a = 0.18 + 0.4 * fl
    cv.drawRect(skia.Rect.MakeLTRB(CYL_X0 + 2, DECK_Y + 2, CYL_X1 - 2, py), paint(gas_c, a=gas_a))
    if fl > 0:
        cv.drawCircle(640, (DECK_Y + py) / 2, 120, paint(hx("#ffcf7a"), a=0.5 * fl, blur=40))
    # piston
    pp = skia.Paint(AntiAlias=True)
    pp.setShader(lin_grad((CYL_X0, 0), (CYL_X1, 0), [hx("#6c778a"), hx("#c3cbd8"), hx("#8a95a8"), hx("#5a6477")],
                          [0, 0.35, 0.6, 1]))
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(0, 0, W, CYL_BOT))
    cv.drawLine(640, py + 60, 640 + 30 * math.sin(math.radians(th)), CYL_BOT, paint(hx("#7b8698"), stroke=26))
    cv.drawRect(skia.Rect.MakeLTRB(CYL_X0 + 3, py, CYL_X1 - 3, py + 95), pp)
    for k in range(3):
        cv.drawLine(CYL_X0 + 3, py + 18 + 14 * k, CYL_X1 - 3, py + 18 + 14 * k, paint(hx("#3a4252"), stroke=3))
    cv.restore()
    cv.drawRect(skia.Rect.MakeLTRB(CYL_X0 - 40, CYL_BOT, CYL_X1 + 40, CYL_BOT + 5), paint(hx("#6b7c96")))

    # ---------- air through the port (flows while the intake valve is open)
    ap = air_path()
    ka = clamp(il / 12.0)
    flow(cv, ap, t, 260, 26, C_AIR, r=5.0, a=0.95 * ka)
    flow(cv, ap[:60], t, 260, 26, C_AIR, r=5.0, a=0.35 * (1 - ka), offset=13)
    # mist carried along with the air into the cylinder
    km = 0.0
    if t < T_RESULT:
        km = ease(lin(t, T_BURSTS - 0.05, T_BURSTS + 0.25)) * (1 - ease(lin(t, T_VALVE + 0.2, T_RESULT + 0.3)))
    if km > 0:
        flow(cv, ap[55:], t, 240, 18, AMBER, r=3.4, a=km * ka, seed=4, jitter=14)
    # ---------- exhaust out past the O2 sensor
    xp = exh_path()
    ke = clamp(el / 10.0)
    flow(cv, xp, t, 300, 24, C_BURNT, r=5.0, a=ke)

    # ---------- valves
    for vx, lift, c in ((IV_X, il, hx("#c3cbd8")), (EV_X, el, hx("#b7a99a"))):
        yh = DECK_Y + lift
        cv.drawLine(vx, 560, vx, yh - 8, paint(c, stroke=14))
        poppet = np.array([(vx - 8, yh - 30), (vx + 8, yh - 30), (vx + VALVE_R, yh - 4), (vx + VALVE_R, yh + 6),
                           (vx - VALVE_R, yh + 6), (vx - VALVE_R, yh - 4)])
        cv.drawPath(poly_path(poppet), paint(c))
        cv.drawPath(poly_path(poppet), paint(hx("#3a4252"), stroke=2))
        # spring + retainer above the head
        draw_spring_2d(cv, vx, 545, 610, 26, 6, lift)

    # ---------- engine computer + wire to the injector
    ex, ey, ew, eh = ECU
    ka_e = ease(lin(t, T_COMPUTER - 0.3, T_COMPUTER + 0.2))
    if ka_e > 0:
        plug = INJ_BACK_CU + (INJ_TIP_CU - INJ_BACK_CU) * 0.45
        wire = spline([(ex + ew / 2, ey + eh), (ex + 10, ey + eh + 40), (plug[0] - 10, plug[1] - 40)], 40)
        pipe(cv, wire, 7, hx("#2d2d2d"), a=ka_e)
        kpz = win(t, T_PULSE - 0.1, T_PULLS + 0.2, 0.1, 0.3)
        if kpz > 0:
            flow(cv, wire, t, 300, 30, AMBER, r=4, a=kpz)
        cv.drawRoundRect(skia.Rect.MakeXYWH(ex, ey, ew, eh), 10, 10, paint(hx("#1c2533"), a=ka_e))
        cv.drawRoundRect(skia.Rect.MakeXYWH(ex, ey, ew, eh), 10, 10, paint(AMBER, a=ka_e, stroke=2.5))
        draw_text(cv, "ECU", ex + ew / 2, ey + eh / 2 + 11, font("inter_blk", 30), INK, a=ka_e, align="center",
                  tracking=4)

    # ---------- port injector (solenoid) aimed into the port
    kdi = ease(lin(t, T_SECOND - 0.2, T_SECOND + 0.4))
    a_pi = 1 - 0.65 * kdi
    draw_injector(cv, INJ_BACK_CU, INJ_TIP_CU, coil_k(t), port_inj_open(t), a_pi, t)
    po = port_inj_open(t)
    if po > 0:
        mist(cv, INJ_TIP_CU, INJ_TIP_CU - INJ_BACK_CU, t, po * a_pi, spread=0.30, length=170, n=50, seed=2,
             carry=(80, 60))

    # ---------- direct injector + high-pressure pump (direct beat)
    if kdi > 0:
        kg = win(t, T_STRAIGHT - 0.1, T_OUTRO - 0.2, 0.25, 0.3)
        if kg > 0:
            cv.drawLine(*DI_BACK, *DI_TIP, paint(RED, a=0.6 * kg * kdi, stroke=44, blur=12))
        draw_injector(cv, DI_BACK, DI_TIP, di_open(t), di_open(t), kdi, t, slim=True)
        dk = di_open(t) * kdi
        if dk > 0:
            mist(cv, DI_TIP, (1.0, 0.75), t, dk, spread=0.25, length=230, n=60, seed=9, r=2.6)
        # high-pressure pump driven by a cam lobe, with a hard line to the injector
        kp = ease(lin(t, T_PUMP2 - 0.2, T_PUMP2 + 0.3))
        if kp > 0:
            px, pyy = 160, 1010
            line = spline([(px, pyy - 50), (170, 900), (DI_BACK[0] - 10, DI_BACK[1] - 4)], 40)
            pipe(cv, line, 10, RED, a=kp)
            flow(cv, line, t, 380, 14, AMBER, r=3.0, a=kp)
            cv.drawRoundRect(skia.Rect.MakeXYWH(px - 50, pyy - 50, 100, 110), 14, 14, paint(hx("#4b5566"), a=kp))
            cv.drawRoundRect(skia.Rect.MakeXYWH(px - 50, pyy - 50, 100, 110), 14, 14, paint(RED, a=kp, stroke=3))
            lobe_a = math.radians(th * 0.5)
            cx, cy = px, pyy + 108
            cv.drawLine(px, pyy + 60, cx + 46 * 0, cy - 34 - 14 * max(0, math.cos(-math.pi / 2 - lobe_a)) ** 3,
                        paint(hx("#c3cbd8"), a=kp, stroke=10))
            lobe = np.array([(cx + (34 + 14 * max(0, math.cos(a - lobe_a)) ** 3) * math.cos(a),
                              cy + (34 + 14 * max(0, math.cos(a - lobe_a)) ** 3) * math.sin(a))
                             for a in np.linspace(0, 2 * np.pi, 48)])
            cv.drawPath(poly_path(lobe), paint(hx("#8f9aab"), a=kp))

    # ---------- oxygen sensor in the exhaust + rich/lean meter
    ko = ease(lin(t, T_OXY - 0.2, T_OXY + 0.3))
    if ko > 0:
        sx, sy = 880, 735
        cv.drawLine(sx, sy - 6, sx + 30, sy - 86, paint(hx("#c3cbd8"), a=ko, stroke=18))
        cv.drawLine(sx, sy - 6, sx - 8, sy + 22, paint(hx("#8f9aab"), a=ko, stroke=10))
        cv.drawCircle(sx - 8, sy + 22, 12, paint(GREEN, a=0.5 * ko, blur=6))
    cv.restore()
    cv.restore()
    draw_meter(cv, t, kv)
    draw_pulse_graph(cv, t, kv)


def draw_spring_2d(cv, x, y0, y1, r, turns, lift):
    y0 = y0 + lift
    pts = []
    n = 80
    for i in range(n + 1):
        u = i / n
        pts.append((x + r * math.sin(u * turns * 2 * math.pi), y0 + (y1 - y0) * u))
    cv.drawPath(poly_path(np.array(pts), close=False), paint(hx("#9aa5b6"), stroke=4))
    cv.drawLine(x - r - 6, y0, x + r + 6, y0, paint(hx("#c3cbd8"), stroke=7))


def draw_injector(cv, back, tip, coil, open_, a, t, slim=False):
    if a <= 0:
        return
    back, tip = np.array(back, float), np.array(tip, float)
    d = tip - back
    Ln = np.linalg.norm(d)
    u = d / Ln
    n = np.array([-u[1], u[0]])
    w = 26 if not slim else 20
    ang = math.degrees(math.atan2(u[1], u[0]))
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cv.save()
    cv.translate(*back)
    cv.rotate(ang)
    # body: inlet, coil housing, nozzle
    bp = skia.Paint(AntiAlias=True)
    bp.setShader(lin_grad((0, -w), (0, w), [hx("#5d6b82"), hx("#b9c3d3"), hx("#4b5566")]))
    cv.drawRoundRect(skia.Rect.MakeLTRB(0, -w * 0.55, Ln * 0.25, w * 0.55), 6, 6, bp)
    cv.drawRoundRect(skia.Rect.MakeLTRB(Ln * 0.22, -w, Ln * 0.72, w), 10, 10, bp)
    cv.drawRoundRect(skia.Rect.MakeLTRB(Ln * 0.7, -w * 0.45, Ln, w * 0.45), 6, 6, bp)
    # coil windings (glow when energised)
    cc = mix(hx("#b86a2a"), AMBER, coil)
    for k in range(9):
        x = Ln * 0.27 + k * (Ln * 0.4 / 8)
        cv.drawLine(x, -w + 6, x, w - 6, paint(cc, stroke=5))
    if coil > 0:
        cv.drawRoundRect(skia.Rect.MakeLTRB(Ln * 0.22, -w, Ln * 0.72, w), 10, 10,
                         paint(AMBER, a=0.45 * coil, blur=14))
    # needle (pintle): pulled back toward the coil when open
    nb = -14 * open_
    cv.drawLine(Ln * 0.35 + nb, 0, Ln * 0.985 + nb, 0, paint(hx("#e6ebf2"), stroke=7))
    cv.drawCircle(Ln * 0.985 + nb, 0, 5, paint(hx("#e6ebf2")))
    # spring behind the needle
    pts = [(Ln * 0.22 + (Ln * 0.13 + nb) * i / 30, 9 * math.sin(i * 1.3)) for i in range(31)]
    cv.drawPath(poly_path(np.array(pts), close=False), paint(hx("#9aa5b6"), stroke=2.5))
    # wire + plug
    cv.drawLine(Ln * 0.45, -w, Ln * 0.45 - 30, -w - 60, paint(hx("#2d2d2d"), stroke=10))
    cv.drawLine(Ln * 0.45, -w, Ln * 0.45 - 30, -w - 60, paint(AMBER, a=0.8 * coil, stroke=4))
    cv.restore()
    cv.restore()


def draw_meter(cv, t, kv):
    """RICH / LEAN bar driven by the oxygen sensor (result beat)."""
    k = kv * win(t, T_OXY, T_DIRECT + 0.2, 0.3, 0.4)
    if k <= 0:
        return
    x0, x1, y = 560, 920, 470
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0 - 24, y - 80, x1 + 24, y + 56), 20, 20, paint(hx("#0b111c"), a=0.9 * k))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0 - 24, y - 80, x1 + 24, y + 56), 20, 20, paint(hx("#2a3446"), a=k, stroke=2))
    draw_text(cv, "OXYGEN SENSOR", x0, y - 44, font("inter_xb", 22), MUTED, a=k, tracking=3)
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((x0, 0), (x1, 0), [RED, GREEN, CYAN], [0, 0.5, 1]))
    p.setAlphaf(k)
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0, y - 8, x1, y + 8), 8, 8, p)
    draw_text(cv, "RICH", x0, y + 42, font("inter_xb", 22), RED, a=k, tracking=2)
    draw_text(cv, "LEAN", x1, y + 42, font("inter_xb", 22), CYAN, a=k, align="right", tracking=2)
    draw_text(cv, "OK", (x0 + x1) / 2, y + 42, font("inter_xb", 22), GREEN, a=k, align="center", tracking=2)
    # mixture: lean before, swings rich after the longer pulses, corrected to the middle
    m = smooth(t, [(T_OXY, 0.78), (T_RICH, 0.78), (T_RICH + 0.4, 0.2), (T_LEAN, 0.2), (T_LEAN + 0.4, 0.8),
                   (T_CORRECTS, 0.75), (T_CORRECTS + 0.8, 0.5), (T_DIRECT + 1, 0.5)])
    xm = x0 + (x1 - x0) * m
    cv.drawCircle(xm, y, 18, paint(INK, a=k))
    cv.drawCircle(xm, y, 18, paint(hx("#0b111c"), a=k, stroke=4))


def draw_pulse_graph(cv, t, kv):
    """Injector pulses (square waves) during the result beat: longer pulse = more fuel."""
    k = kv * win(t, T_RESULT - 0.1, T_DIRECT + 0.2, 0.3, 0.4)
    if k <= 0:
        return
    gx, gy, gw, gh = 110, 1300, 820, 58
    cv.saveLayerAlpha(None, int(255 * k))
    brand.graph_box(cv, (gx, gy, gw, gh), "INJECTOR PULSE", "TIME")
    pts = []
    tt = np.linspace(t - 3.0, t, 400)
    for i, ti in enumerate(tt):
        x = gx + gw * i / (len(tt) - 1)
        on = port_inj_open(ti) if ti >= T_RESULT else 0.0
        pts.append((x, gy + gh - 10 - (gh - 30) * on))
    brand.curve(cv, np.array(pts), AMBER, width=4)
    w = pulse_ms(t)
    draw_text(cv, "WIDER PULSE = MORE FUEL", gx + gw, gy - 12, font("inter_xb", 22), AMBER,
              a=ease(lin(t, T_LONGER, T_MORE + 0.2)), align="right", tracking=2)
    cv.restore()


# ================================================================== overlays
def draw_problem(cv, t):
    k = win(t, T_LOW - 0.2, T_PARTS + 0.1, 0.3, 0.35)
    if k <= 0:
        return
    items = [("UP FRONT", eout(lin(t, T_FRONT - 0.1, T_FRONT + 0.2))),
             ("UNDER PRESSURE", eout(lin(t, T_UNDER - 0.1, T_UNDER + 0.2))),
             ("RIGHT MOMENT", eout(lin(t, T_RIGHT, T_RIGHT + 0.3)))]
    brand.chips(cv, k, 345, items, center=True)
    pj = cam_ov(t)
    ka = k * eout(lin(t, T_FRONT - 0.2, T_FRONT + 0.3))
    if ka > 0:
        p0 = pj(60, TANK_Y0 - 30, Z0)
        p1 = pj(60, HEAD_Y1 + 40, Z0)
        arrow(cv, p0, p1, YEL, a=ka, w=12)


def draw_labels(cv, t):
    kE = 1 - current.ending_k(t)
    kv = (1 - cu_k(t)) * kE
    pj = cam_ov(t)
    if kv > 0:
        cv.saveLayerAlpha(None, int(255 * kv))
        brand.label(cv, t, "GAS TANK", tuple(pj(TANK_X0, 210, 0)), (80, 1060), STEEL, T_LOW - 0.05, T_FRONT + 0.3)
        brand.label(cv, t, "ENGINE", tuple(pj(HEAD_X1, -300, 0)), (930, 860), STEEL, T_FRONT - 0.05, T_RIGHT + 0.6,
                    align="right")
        brand.label(cv, t, "ELECTRIC FUEL PUMP", tuple(pj(PUMP_X - PUMP_R, 280, Z0)), (80, 1060), YEL,
                    T_PUMP - 0.05, T_LINE + 0.2)
        k = win(t, T_SUBM - 0.05, T_LINE + 0.3, 0.25, 0.3)
        if k > 0:
            pill(cv, 930, 1060, "SUBMERGED = COOLED", font("inter_xb", 28), INK, border=CYAN, a=k, align="right",
                 tracking=2)
        brand.label(cv, t, "FILTER", tuple(pj(FILT_X - FILT_R, -100, Z0)), (80, 820), YEL, T_FILTER - 0.05,
                    T_HOW + 0.3)
        brand.label(cv, t, "FUEL RAIL", tuple(pj(-330, RAIL_Y, Z0)), (80, 380), YEL, T_RAIL - 0.05, T_KEY - 0.4)
        brand.label(cv, t, "INJECTORS", tuple(pj(225, INJ_TOP + 30, Z0)), (930, 380), YEL, T_INJ - 0.05,
                    T_KEY - 0.4, align="right")
        brand.label(cv, t, "PRESSURE REGULATOR", tuple(pj(PUMP_X + 52, PUMP_Y0 + 4, Z0)), (930, 1000), YEL,
                    T_REG - 0.05, T_KEY - 0.4, align="right")
        brand.label(cv, t, "CHARCOAL CANISTER", tuple(pj(CAN_X + CAN_R, 0, Z0)), (930, 920), YEL,
                    T_CHARCOAL - 0.05, T_END + 0.2, align="right")
        k = win(t, T_FUMES - 0.1, T_CHARCOAL, 0.2, 0.3)
        if k > 0:
            pill(cv, 930, 1060, "FUEL VAPOR", font("inter_xb", 28), INK, border=hx("#9fb3a0"), a=k, align="right",
                 tracking=2)
        k = win(t, T_BURNS - 0.1, T_END + 0.1, 0.25, 0.3)
        if k > 0:
            pill(cv, 930, 1060, "BURNED LATER", font("inter_xb", 28), INK, border=hx("#9fb3a0"), a=k, align="right",
                 tracking=2)
        cv.restore()
    # close-up labels (screen coords, view scale ~1)
    kc = cu_k(t)
    if kc > 0:
        cv.saveLayerAlpha(None, int(255 * kc))
        brand.label(cv, t, "ENGINE COMPUTER", (428, 416), (80, 300), AMBER, T_COMPUTER - 0.05, T_MAGNET)
        brand.label(cv, t, "ELECTROMAGNET", (330, 600), (80, 420), AMBER, T_MAGNET - 0.05, T_BURSTS)
        brand.label(cv, t, "NEEDLE PULLED OPEN", (378, 712), (80, 540), RED, T_PULLS - 0.05, T_MIST)
        brand.label(cv, t, "FINE MIST", (440, 790), (80, 560), AMBER, T_MIST - 0.25, T_AIR + 0.2)
        brand.label(cv, t, "AIR", (150, 712), (80, 860), CYAN, T_AIR - 0.05, T_RESULT)
        brand.label(cv, t, "INTAKE VALVE", (IV_X + 10, 600), (930, 470), hx("#c3cbd8"), T_VALVE - 0.3,
                    T_RESULT + 0.4, align="right")
        brand.label(cv, t, "EXHAUST", (930, 760), (930, 600), C_BURNT, T_OXY - 0.05, T_RICH, align="right")
        brand.label(cv, t, "2ND PUMP, ON THE ENGINE", (110, 1010), (80, 1290), RED, T_PUMP2 - 0.05, T_STRAIGHT - 0.1)
        k = win(t, T_STRAIGHT - 0.1, T_OUTRO - 0.2, 0.25, 0.3)
        if k > 0:
            pill(cv, 930, 1290, "INJECTOR IN THE CYLINDER", font("inter_xb", 27), INK, border=RED, a=k, align="right",
                 tracking=1.5)
        k = win(t, T_HIGHER - 0.1, T_OUTRO - 0.1, 0.25, 0.3)
        if k > 0:
            pill(cv, 540, 1365, "FAR HIGHER PRESSURE", font("inter_xb", 30), INK, border=RED, a=k, align="center",
                 tracking=2)
        cv.restore()


def phase(t):
    if t < T_PROB:
        return "FILL-UP", AMBER
    if t < T_PARTS:
        return "TANK TO ENGINE", YEL
    if t < T_HOW:
        return "THE PARTS", MUTED
    if t < T_KEY:
        return "PRESSURIZED", AMBER
    if t < T_RESULT:
        return "INJECTION", RED
    if t < T_DIRECT:
        return "CLOSED LOOP", GREEN
    if t < T_OUTRO:
        return "DIRECT INJECTION", RED
    return "VAPOR RECOVERY", hx("#9fb3a0")


def draw_header(cv, t):
    k = win(t, T_WHAT + 0.3, T_END, 0.3, 0.3)
    if k <= 0:
        return
    nm, c = phase(t)
    brand.status_pill(cv, k, nm, c)
    kr = k * win(t, T_FORTY - 0.1, T_KEY - 0.2, 0.3, 0.3)
    if kr > 0:
        brand.readout(cv, kr, "40-60", "PSI IN THE RAIL", frac=0.55 + 0.03 * math.sin(t * 9) *
                      (1 - ease(lin(t, T_REG, T_STEADY))), bar_color=AMBER)
    kn = k * cu_k(t) * 0.9
    if kn > 0:
        brand.note(cv, "ANIMATION SLOWED", kn, dy=-36)


def draw_stamps(cv, t):
    brand.stamp(cv, t, "SPRAY!", T_BURSTS, center=(700, 1310))


def draw(cv, t):
    draw_overview(cv, t)
    draw_closeup(cv, t)
    draw_problem(cv, t)
    draw_labels(cv, t)
    draw_header(cv, t)
    draw_stamps(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_BURSTS
MUSIC_START = T_WHAT


def sound():
    sfx = [(0.05, "hiss", 0.35), (T_HOOK_OUT - 0.1, "whoosh_big", 0.5),
           (T_PUMP, "tick", 0.2), (T_FILTER, "tick", 0.2), (T_RAIL, "tick", 0.2), (T_INJ, "tick", 0.2),
           (T_PUSHES, "spool", 0.3), (T_REG, "tick", 0.2),
           (T_CU_IN, "whoosh_up", 0.4), (T_PULSE, "tick", 0.35), (T_PULLS, "clunk", 0.45), (T_BURSTS, "hiss", 0.6),
           (T_OXY, "tick", 0.2), (T_SECOND, "whoosh_up", 0.35), (T_SPRAY, "hiss", 0.4),
           (T_CU_OUT, "whoosh_down", 0.4), (T_FUMES, "hiss", 0.25)]
    return {"build": (T_HOW, T_BURSTS), "drop": (T_BURSTS, T_OUTRO - 0.05), "sfx": sfx}
