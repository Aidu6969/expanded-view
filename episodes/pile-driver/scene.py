"""Diesel pile hammer visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (oblique section view: X right, Y down, z depth receding up-right; units ~mm-ish, not to scale):
  cylinder   open top at CYL_TOP, bottom at 0; bore radius BORE; glass so the ram is visible
  ram        free steel piston, height RAM_H; yb = Y of its bottom face (yb = BLOCK_TOP when resting on the block)
  block      impact block (anvil) BLOCK_TOP..BLOCK_BOT, sits on the helmet (drive cap) on top of the pile
  ports      exhaust ports through the wall, PORT_TOP..PORT_BOT: open whenever the ram's bottom is above PORT_TOP,
             fully covered once yb >= PORT_BOT (the ram is far taller than the port, so it covers it all)
  fuel pump  on the side; its lever pokes into the bore at LEV_Y and is pressed while the ram is beside it
             (yb > LEV_Y); the pump puts a shot of diesel onto the block through a nozzle low in the wall
  cycle      free running: ballistic hop, yb = BLOCK_TOP - HOP * 4u(1-u) for phase u in [0,1), blow at u = 0
             narrated blow: trip lifts the ram and lets go; slowed fall stepped with the narration; impact,
             ignition, pile driven down, ram thrown up past the ports, gravity brings it back -> free running
  pile       every blow drives the hammer + pile down by STEP (ground stays put)
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, pipe, flow, spline, resample, arrow_head

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_POUND = F("hook", "pound")
T_ENGINE_H = F("hook", "engine.")
T_WHAT = L("what")["start"]
T_TWO = F("what", "two")
T_DIESEL_W = F("what", "diesel", 1)
T_PISTON = F("what", "piston")
T_FREE = F("what", "free.")
T_PROB = L("problem")["start"]
T_CRANE_P = F("problem", "crane")
T_SLOW = F("problem", "slow.")
T_ITSELF = F("problem", "itself.")
T_PARTS = L("parts")["start"]
T_RAM = F("parts", "ram")
T_CYL = F("parts", "cylinder.")
T_IMPACT = F("parts", "impact")
T_PILE = F("parts", "pile.")
T_PUMP = F("parts", "fuel")
T_EXH_P = F("parts", "exhaust")
T_START = L("start")["start"]
T_LIFTS = F("start", "lifts")
T_TRIP = F("start", "trip")
T_GO = F("start", "go.")
T_FALL = L("fall")["start"]
T_PRESSES = F("fall", "presses")
T_LEVER = F("fall", "lever,")
T_SQUIRTS = F("fall", "squirts")
T_BLOCK_E = F("fall", "block.", which="end")
T_COVERS = F("fall", "covers")
T_TRAPPING = F("fall", "trapping")
T_BELOW_E = F("fall", "it.", which="end")
T_KEY = L("key")["start"]
T_SQUEEZED = F("key", "squeezed")
T_HOT_E = F("key", "hot.", which="end")
T_SLAMS = F("key", "slams")
T_SPLASH = F("key", "splashing")
T_IGNITES = F("key", "ignites.")
T_BANG = F("key", "bang.")
T_RESULT = L("result")["start"]
T_BOTH = F("result", "both")
T_DRIVES = F("result", "drives")
T_DOWN_R = F("result", "down,", which="end")
T_THROWS = F("result", "throws")
T_CYL_E = F("result", "cylinder.", which="end")
T_RISE = L("rise")["start"]
T_PASSES = F("rise", "passes")
T_EXH_R = F("rise", "exhaust")
T_FRESH = F("rise", "fresh")
T_GRAVITY = F("rise", "gravity")
T_DOWN2 = F("rise", "down.", which="end")
T_NOCRANK = F("rise", "crankshaft,")
T_NOSPARK = F("rise", "spark")
T_RUNS = F("rise", "runs")
T_FUEL_E = F("rise", "fuel.", which="end")
T_OUTRO = L("outro")["start"]

# ================================================================== geometry
CYL_TOP = -720.0
BORE = 92.0
WALL = 108.0
RAM_H = 230.0
BLOCK_TOP, BLOCK_BOT = -90.0, 20.0
HELM_TOP, HELM_BOT = 20.0, 78.0
PILE_R = 70.0
PILE_BOT = 1400.0
GROUND = 200.0
PORT_TOP, PORT_BOT = -250.0, -215.0
PORT_Y = 0.5 * (PORT_TOP + PORT_BOT)
LEV_Y = -305.0
NOZ_Y = -112.0
YB_TOP = CYL_TOP + RAM_H + 20.0          # highest ram-bottom position (ram top just below the open top)
HOP = BLOCK_TOP - YB_TOP                 # free-running hop height
STEP = 1.8                               # pile set per blow

C_RAM = hx("#9aa5b6")
C_CYL = hx("#2a3446")
C_PILE = hx("#6f7a8c")
C_BURNT = hx("#8a7a6a")
C_FLAME = hx("#ff6a2a")
C_SOIL = hx("#1c1712")


# ================================================================== ram motion
def _ease_mode(u, mode):
    u = clamp(u)
    if mode == "in":
        return u * u
    if mode == "out":
        return u * (2 - u)
    if mode == "io":
        return ease(u)
    return u


def _hop(u):
    return BLOCK_TOP - HOP * 4 * u * (1 - u)


# --- section A: free running from frame 1 (falling), slowing a little, stops on the block before the parts beat
_dt = 1.0 / 600
_TA = np.arange(0.0, T_PARTS + 0.01, _dt)
_PER_A = lambda t: smooth(t, [(0.0, 0.95), (T_HOOK_OUT, 0.95), (T_WHAT + 1.5, 1.45), (T_PARTS, 1.45)])
_PH = np.zeros_like(_TA)
_PH[0] = 0.72
for _i in range(1, len(_TA)):
    _PH[_i] = _PH[_i - 1] + _dt / _PER_A(_TA[_i - 1])
_crossings = [(_TA[i], math.floor(_PH[i])) for i in range(1, len(_TA)) if math.floor(_PH[i]) > math.floor(_PH[i - 1])]
_stop = next(c for c in _crossings if c[0] >= T_PARTS - 1.6)
T_STOP_A = _stop[0]
BANGS_A = [c[0] for c in _crossings if c[0] <= T_STOP_A]


def phase_a(t):
    if t >= T_STOP_A:
        return float(_stop[1])
    return float(np.interp(t, _TA, _PH))


# --- narrated blow (slowed): (t0, t1, y0, y1, mode)
T_LIFT0 = T_LIFTS - 0.1
T_LIFT1 = T_TRIP + 0.1
SEGS = [
    (T_LIFT0, T_LIFT1, BLOCK_TOP, YB_TOP, "io"),          # crane + trip lift the ram
    (T_GO, T_PRESSES, YB_TOP, LEV_Y + 6, "in"),            # released: falls
    (T_PRESSES, T_BLOCK_E, LEV_Y + 6, -268.0, "out"),      # slowed while the pump fires
    (T_BLOCK_E, T_TRAPPING, -268.0, PORT_BOT + 4, "io"),   # covers the ports
    (T_TRAPPING, T_HOT_E, PORT_BOT + 4, -128.0, "lin"),    # squeezing the trapped air
    (T_HOT_E, T_SLAMS, -128.0, BLOCK_TOP, "in"),           # slams the block
    (T_THROWS - 0.05, T_CYL_E, BLOCK_TOP, -200.0, "out"),  # thrown back up
    (T_CYL_E, T_PASSES, -200.0, PORT_TOP - 12, "lin"),     # passes the ports
    (T_PASSES, T_GRAVITY, PORT_TOP - 12, YB_TOP, "out"),   # coasts to the top
    (T_GRAVITY, T_DOWN2, YB_TOP, BLOCK_TOP, "in"),         # gravity brings it back
]
PER_B = 1.12
BANG_N = T_SLAMS                                           # narrated impact


def yb_at(t):
    if t < T_LIFT0:
        u = phase_a(t) % 1.0
        return _hop(u)
    if t >= T_DOWN2:
        return _hop(((t - T_DOWN2) / PER_B) % 1.0)
    y = SEGS[0][2]
    for t0, t1, y0, y1, mode in SEGS:
        if t >= t0:
            y = y0 + (y1 - y0) * _ease_mode(lin(t, t0, t1), mode)
    return y


BANGS_B = [T_DOWN2 + k * PER_B for k in range(0, 40) if T_DOWN2 + k * PER_B < T_TOTAL + 1]
BANGS_FREE = BANGS_A + BANGS_B


def blows(t):
    n = sum(1 for b in BANGS_A if b <= t)
    n += 1 if t >= T_IGNITES else 0
    n += sum(1 for b in BANGS_B if b <= t)
    return n


def pen(t):
    p = sum(ease(lin(t, b, b + 0.09)) for b in BANGS_FREE)
    p += 10.0 * ease(lin(t, T_DRIVES - 0.05, T_DOWN_R))     # the narrated blow, slowed (exaggerated so it reads)
    return STEP * p


def free_running(t):
    return t < T_LIFT0 or t >= T_DOWN2


def since_bang(t):
    best = 99.0
    for b in BANGS_FREE:
        if b <= t:
            best = min(best, t - b)
    return best


def check_physics():
    bad = []
    for t in np.arange(0, T_TOTAL, 0.01):
        y = yb_at(t)
        if y > BLOCK_TOP + 1e-6:
            bad.append(f"ram below block at {t:.2f}")
            break
        if y - RAM_H < CYL_TOP - 1e-6:
            bad.append(f"ram leaves cylinder at {t:.2f}")
            break
    # the ram must be falling past the lever before the ports close in the narrated blow
    if not (yb_at(T_PRESSES) > LEV_Y and yb_at(T_PRESSES) < PORT_TOP):
        bad.append("lever not pressed before the ports close")
    if yb_at(T_TRAPPING) < PORT_BOT:
        bad.append("ports not covered on 'trapping'")
    if abs(yb_at(T_SLAMS + 0.01) - BLOCK_TOP) > 1e-6:
        bad.append("ram not on the block at 'slams'")
    if yb_at(T_PASSES) > PORT_TOP:
        bad.append("ports not open on 'passes'")
    return bad


assert not check_physics(), check_physics()


def ports_open(yb):
    return clamp((PORT_BOT - yb) / (PORT_BOT - PORT_TOP))


def lever_k(yb):
    return clamp((yb - (LEV_Y - 4)) / 16.0)


# ================================================================== camera
DX, DY = 0.42, -0.30
CAM_HOOK = (548.0, 1118.0, 0.9)
CAM_MAIN = (540.0, 1020.0, 1.0)


def cam(t):
    k = ease(lin(t, T_HOOK_OUT - 0.2, T_WHAT + 0.6))
    p = np.array(CAM_HOOK) * (1 - k) + np.array(CAM_MAIN) * k
    return Proj(p[0], p[1], p[2], dx=DX, dy=DY)


# ================================================================== gas inside the chamber
_rng = np.random.default_rng(5)
NDOT = 40
DOTS = np.stack([np.sqrt(_rng.uniform(0.0, 0.85, NDOT)), _rng.uniform(0, 2 * np.pi, NDOT),
                 _rng.uniform(0.05, 0.95, NDOT)], 1)


def heat(k):
    k = clamp(k)
    return mix(CYAN, INK, 2 * k) if k < 0.5 else mix(INK, AMBER, 2 * k - 1)


def gas_color(t, yb):
    """Colour of the air/gas under the ram + flame strength."""
    comp = clamp((yb - PORT_BOT) / (BLOCK_TOP - PORT_BOT))         # 0 at port close .. 1 on the block
    if not free_running(t):
        if t < T_TRAPPING:
            return CYAN, 0.0
        if t < T_IGNITES:
            return heat(max(comp, lin(t, T_SQUEEZED, T_HOT_E))), 0.0
        fl = 1 - lin(t, T_IGNITES + 0.4, T_PASSES)
        if t < T_FRESH:
            return mix(C_BURNT, C_FLAME, fl), fl
        return mix(C_BURNT, CYAN, lin(t, T_FRESH, T_FRESH + 1.2)), 0.0
    sb = since_bang(t)
    fl = clamp(1 - sb / 0.35) if sb < 0.35 else 0.0
    u = (phase_a(t) % 1.0) if t < T_LIFT0 else (((t - T_DOWN2) / PER_B) % 1.0)
    if t >= T_STOP_A and t < T_LIFT0:
        return CYAN, 0.0
    if u < 0.5 and ports_open(yb) < 0.5:
        return mix(C_BURNT, C_FLAME, fl), fl
    if u >= 0.5 and ports_open(yb) < 0.5:
        return heat(comp), 0.0
    return CYAN, 0.0


# ================================================================== drawing helpers
def arrow(cv, x0, y0, x1, y1, c, a=1.0, w=14):
    if a <= 0:
        return
    cv.drawLine(x0, y0, x1, y1, paint(c, a=0.45 * a, stroke=w * 2, blur=8))
    v = np.array([x1 - x0, y1 - y0], float)
    n = np.linalg.norm(v)
    v /= n
    tip = np.array([x1, y1])
    base = tip - v * w * 2.2
    cv.drawLine(x0, y0, base[0], base[1], paint(c, a=a, stroke=w))
    nrm = np.array([-v[1], v[0]])
    tri = np.array([tip, base + nrm * w * 1.5, base - nrm * w * 1.5])
    cv.drawPath(poly_path(tri), paint(c, a=a))


def soil(cv, pj, t):
    gy = pj(0, GROUND, 0)[1]
    y1 = 1418
    if gy >= y1:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((0, gy), (0, y1), [hx("#2b241b", 0.86), hx("#1c1712", 0.55)]))
    cv.drawRect(skia.Rect.MakeLTRB(0, gy, W, y1), p)
    hp = paint(hx("#6b5a44"), a=0.35, stroke=2)
    for x in range(-200, W, 34):
        cv.drawLine(x, gy + 70, x + 40, gy + 6, hp)
    cv.drawLine(0, gy, W, gy, paint(hx("#a08a66"), a=0.9, stroke=3))


# ================================================================== the hammer
def draw_fuel(cv, t, pj, yb, dp, S, fl):
    # ---- fuel: squirt, puddle in the bowl, mist
    if not free_running(t):
        ks = win(t, T_SQUIRTS - 0.05, T_BLOCK_E + 0.2, 0.1, 0.3)
        noz = np.array(pj(-BORE + 4, NOZ_Y + dp, 0))
        tgt = np.array(pj(0, BLOCK_TOP + dp - 2, 0))
        if ks > 0:
            for j in range(14):
                u = ((t - T_SQUIRTS) * 1.6 + j / 14) % 1.0
                q = noz + (tgt - noz) * u + np.array([0, -38 * S * 4 * u * (1 - u)])
                cv.drawCircle(q[0], q[1], 4.5 * S, paint(AMBER, a=ks))
        kp = clamp(lin(t, T_SQUIRTS + 0.2, T_BLOCK_E)) * (1 - lin(t, T_SPLASH - 0.05, T_SPLASH + 0.25))
        if kp > 0:
            pud = np.array([pj(30 * math.cos(a), BLOCK_TOP + dp - 1, 30 * math.sin(a)) for a in
                            np.linspace(0, 2 * math.pi, 32)])
            cv.drawPath(poly_path(pud), paint(AMBER, a=0.85 * kp))
            cv.drawPath(poly_path(pud), paint(AMBER, a=0.4 * kp, blur=6))
        km = win(t, T_SPLASH - 0.05, T_IGNITES + 0.25, 0.2, 0.2)
        if km > 0:
            rng = np.random.default_rng(3)
            for j in range(60):
                rr = rng.uniform(0, BORE + 6) * min(1.0, 0.3 + 1.5 * lin(t, T_SPLASH, T_SPLASH + 0.5))
                an = rng.uniform(0, 2 * math.pi)
                hy = rng.uniform(-0.3, 1) * max(BLOCK_TOP - yb - 6, 26)
                q = pj(rr * math.cos(an), BLOCK_TOP - 3 - hy + dp, rr * math.sin(an))
                cv.drawCircle(q[0], q[1], 2.6 * S, paint(AMBER, a=0.9 * km))
    # ---- combustion
    if fl > 0:
        cy_ = BLOCK_TOP - 0.5 * (BLOCK_TOP - yb)
        q = pj(0, cy_ + dp, 0)
        cv.drawCircle(q[0], q[1], (70 + 0.4 * (BLOCK_TOP - yb)) * S, paint(C_FLAME, a=0.55 * fl, blur=26 * S))
        cv.drawCircle(q[0], q[1], 34 * S, paint(hx("#ffe2a0"), a=0.5 * fl, blur=12 * S))



def draw_hammer(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return pj
    yb = yb_at(t)
    dp = pen(t)
    S = pj.s
    hl = lambda t0, t1: win(t, t0 - 0.1, t1, 0.2, 0.4)
    h_ram = max(hl(T_RAM, T_IMPACT), hl(T_PISTON, T_FREE + 0.6))
    h_cyl = hl(T_CYL, T_PILE)
    h_blk = hl(T_IMPACT, T_PUMP) + hl(T_SLAMS, T_SPLASH)
    h_pile = hl(T_PILE, T_EXH_P) + hl(T_DRIVES, T_THROWS)
    h_pump = hl(T_PUMP, T_START) + hl(T_PRESSES, T_SQUIRTS + 0.5)
    h_port = hl(T_EXH_P, T_START + 0.3) + hl(T_COVERS, T_TRAPPING + 0.6) + hl(T_PASSES, T_EXH_R + 0.6)
    cv.saveLayerAlpha(None, int(255 * kE))
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(0, 0, W, 1418))

    # ---- leads (guide mast behind the hammer)
    for xx in (-150.0, 150.0):
        a0 = pj(xx, -1300, 190)
        a1 = pj(xx, GROUND, 190)
        cv.drawLine(*a0, *a1, paint(hx("#3a4559"), a=0.8, stroke=10 * S))
    for yy in np.arange(-1300, GROUND, 90):
        a0 = pj(-150, yy, 190)
        a1 = pj(150, yy + 90, 190)
        cv.drawLine(*a0, *a1, paint(hx("#2c3546"), a=0.8, stroke=4 * S))

    # ---- pile (steel pipe pile) + helmet (drive cap)
    rev(cv, pj, "y", (0.0, 0.0), [HELM_BOT - 4 + dp, PILE_BOT + dp], [PILE_R, PILE_R], mix(C_PILE, YEL, 0.25 * h_pile),
        edge=YEL if h_pile > 0.02 else None, edge_w=2 + 1.5 * h_pile, glow=h_pile)
    soil(cv, pj, t)
    rev(cv, pj, "y", (0.0, 0.0), [HELM_TOP + dp, HELM_BOT + dp], [WALL + 12, PILE_R + 16], STEEL_D)

    # ---- cylinder back (glass)
    rev(cv, pj, "y", (0.0, 0.0), [CYL_TOP + dp, 0 + dp], [WALL, WALL], C_CYL, fill_a=0.30,
        edge=mix(hx("#4b5a72"), YEL, clamp(h_cyl)), edge_w=1.6 + 1.4 * h_cyl, glow=h_cyl, caps=False)

    # ---- impact block (anvil) with its bowl
    rev(cv, pj, "y", (0.0, 0.0), [BLOCK_TOP + dp, BLOCK_BOT + dp], [BORE - 2, BORE - 2],
        mix(STEEL, YEL, 0.25 * clamp(h_blk)), edge=YEL if h_blk > 0.02 else None, edge_w=2 + 1.5 * clamp(h_blk),
        glow=clamp(h_blk))
    bowl = np.array([pj(44 * math.cos(a), BLOCK_TOP + dp, 44 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)])
    cv.drawPath(poly_path(bowl), paint(hx("#2c3442")))
    cv.drawPath(poly_path(bowl), paint(hx("#141922"), stroke=2 * S))

    # ---- gas under the ram
    gc, fl = gas_color(t, yb)
    for i in range(NDOT):
        r, an, h = DOTS[i]
        X, z = r * (BORE - 12) * math.cos(an), r * (BORE - 12) * math.sin(an)
        Y = BLOCK_TOP - 4 - h * (BLOCK_TOP - yb - 8)
        if BLOCK_TOP - yb < 12:
            continue
        q = pj(X, Y + dp, z)
        cv.drawCircle(q[0], q[1], 7 * S, paint(gc, a=0.28, blur=4 * S))
        cv.drawCircle(q[0], q[1], 3.6 * S, paint(gc))

    # ---- ram
    rev(cv, pj, "y", (0.0, 0.0), [yb - RAM_H + dp, yb + dp], [BORE - 3, BORE - 3], mix(C_RAM, YEL, 0.25 * h_ram),
        edge=YEL if h_ram > 0.02 else None, edge_w=2 + 1.5 * h_ram, glow=h_ram)
    for yy in (yb - 18, yb - 30):
        ring_front(cv, pj, "y", (0.0, 0.0), yy + dp, BORE - 2, shade(C_RAM, 0.5), width=2.0)
    # lifting lug on top of the ram
    rev(cv, pj, "y", (0.0, 0.0), [yb - RAM_H - 16 + dp, yb - RAM_H + dp], [22, 22], STEEL_D, n=24)

    draw_fuel(cv, t, pj, yb, dp, S, fl)

    # ---- trip (start only): cable + claw holding the lug
    ktr = win(t, T_START - 0.2, T_GO + 0.9, 0.4, 0.5)
    if ktr > 0:
        yl = yb - RAM_H - 16 + dp
        if t > T_GO:
            yl = YB_TOP - RAM_H - 16 + dp - 180 * ease(lin(t, T_GO + 0.15, T_GO + 0.9))
        if t < T_LIFT0:
            yl = yl - 260 * (1 - ease(lin(t, T_START - 0.2, T_LIFT0)))
        top = pj(0, -1500, 0)
        cl = pj(0, yl - 26, 0)
        cv.drawLine(*top, *cl, paint(STEEL, a=ktr, stroke=3 * S))
        opn = ease(lin(t, T_GO - 0.05, T_GO + 0.2))
        box = np.array([[-34, yl - 52], [34, yl - 52], [34, yl - 22], [-34, yl - 22]])
        extrude(cv, pj, box, -16, 16, YEL, alpha=ktr)
        for sgn in (-1, 1):
            ang = sgn * (0.15 + 0.6 * opn)
            p0 = pj(sgn * 26, yl - 24, 0)
            p1 = pj(sgn * 26 + sgn * 30 * math.sin(abs(ang)) - sgn * 10, yl - 24 + 28 * math.cos(abs(ang)), 0)
            cv.drawLine(*p0, *p1, paint(YEL, a=ktr, stroke=7 * S))

    # ---- fuel pump + lever + line to the nozzle (left side)
    lk = lever_k(yb)
    px0, px1 = -WALL - 86, -WALL - 4
    body = np.array([[px0, LEV_Y - 60], [px1, LEV_Y - 60], [px1, LEV_Y + 30], [px0, LEV_Y + 30]]) + [0, dp]
    extrude(cv, pj, body, -30, 30, mix(hx("#5c6678"), AMBER, 0.25 * clamp(h_pump)),
            rim=AMBER if h_pump > 0.02 else None, rim_w=2.0, rim_glow=clamp(h_pump))
    piv = (-WALL + 6, LEV_Y + dp)
    tipx = -BORE + 16 - 18 * lk
    tip = (tipx, LEV_Y + 14 + 6 * lk + dp)
    lp0, lp1 = pj(piv[0], piv[1], 0), pj(tip[0], tip[1], 0)
    cv.drawLine(*lp0, *lp1, paint(mix(AMBER, RED, lk), stroke=9 * S, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(*lp0, 6 * S, paint(STEEL_D))
    line = [pj(px0 + 30, LEV_Y + 30 + dp, 0), pj(px0 + 30, NOZ_Y + dp, 0), pj(-WALL, NOZ_Y + dp, 0)]
    line = resample(np.array(line), 60)
    kf = win(t, T_SQUIRTS - 0.25, T_BLOCK_E + 0.1, 0.1, 0.3) if not free_running(t) else 0.0
    pipe(cv, line, 12 * S, AMBER, glass=True)
    if kf > 0:
        flow(cv, line, t, 260 * S, 18 * S, AMBER, r=3.6 * S, a=kf)
    nz = pj(-WALL + 2, NOZ_Y + dp, 0)
    cv.drawCircle(*nz, 7 * S, paint(STEEL))

    # ---- exhaust ports (stubs both sides) + gas through them
    po = ports_open(yb)
    ex_pts = resample(np.array([pj(WALL - 2, PORT_Y + dp, 0), pj(WALL + 90, PORT_Y - 8 + dp, 0)]), 30)
    in_pts = resample(np.array([pj(-WALL - 110, PORT_Y + 30 + dp, 0), pj(-WALL + 2, PORT_Y + dp, 0)]), 30)
    pc = mix(hx("#4b5a72"), YEL, clamp(h_port))
    for pts in (ex_pts, in_pts):
        pipe(cv, pts, 30 * S, pc, glass=True)
    for sgn in (-1, 1):
        quad = []
        for th, yy in ((14, PORT_TOP), (40, PORT_TOP), (40, PORT_BOT), (14, PORT_BOT)):
            a = math.radians(th)
            quad.append(pj(sgn * WALL * math.cos(a), yy + dp, -WALL * math.sin(a)))
        qp = poly_path(np.array(quad))
        cv.drawPath(qp, paint(hx("#05070b") if po > 0.05 else STEEL_D, a=0.9))
        cv.drawPath(qp, paint(mix(hx("#6b7c96"), YEL, clamp(h_port)), stroke=2 * S))
    if free_running(t):
        u = (phase_a(t) % 1.0) if t < T_LIFT0 else (((t - T_DOWN2) / PER_B) % 1.0)
        active = not (T_STOP_A <= t < T_LIFT0)
        k_ex = (1.0 if (active and u < 0.5 and po > 0.3) else 0.0)
        k_in = (1.0 if (active and po > 0.3) else 0.0)
        sp = 420 * S
    else:
        k_ex = win(t, T_EXH_R - 0.15, T_GRAVITY + 0.2, 0.2, 0.4) * clamp(po * 3)
        k_in = win(t, T_FRESH - 0.15, T_DOWN2 - 0.4, 0.2, 0.4) * clamp(po * 3)
        sp = 180 * S
    if k_ex > 0:
        flow(cv, ex_pts, t, sp, 20 * S, C_BURNT, r=4.5 * S, a=k_ex)
    if k_in > 0:
        flow(cv, in_pts, t, sp, 20 * S, CYAN, r=4.0 * S, a=k_in)

    # ---- front edges
    ring_front(cv, pj, "y", (0.0, 0.0), CYL_TOP + dp, WALL, hx("#6b7c96"), width=2)
    ring_front(cv, pj, "y", (0.0, 0.0), 0 + dp, WALL, hx("#6b7c96"), width=2)
    cv.restore()
    cv.restore()
    return pj


# ================================================================== overlays
def draw_hook(cv, t):
    k = win(t, T_ENGINE_H - 0.4, T_WHAT + 0.5, 0.25, 0.4)
    if k > 0:
        pill(cv, 540, 1250, "THE HAMMER IS AN ENGINE", font("inter_xb", 34), INK, border=RED, a=k, align="center",
             tracking=3)


def draw_what(cv, t):
    k = win(t, T_TWO - 0.2, T_PROB + 0.2, 0.3, 0.3)
    if k > 0:
        items = [("TWO-STROKE", eout(lin(t, T_TWO, T_TWO + 0.25))),
                 ("DIESEL", eout(lin(t, T_DIESEL_W, T_DIESEL_W + 0.25))),
                 ("FREE PISTON", eout(lin(t, T_FREE - 0.2, T_FREE + 0.1)))]
        brand.chips(cv, k, 1250, items, center=True)


def draw_problem(cv, t):
    k = win(t, T_CRANE_P - 0.2, T_PARTS + 0.1, 0.3, 0.35)
    if k <= 0:
        return
    x0, y0, w, h = 585, 430, 355, 220
    brand.panel(cv, x0, y0, w, h, "EVERY BLOW", YEL, a=k)
    brand.bullet(cv, x0 + 30, y0 + 125, "CRANE: SLOW", False, a=k * eout(lin(t, T_CRANE_P, T_CRANE_P + 0.3)),
                 size=30)
    brand.bullet(cv, x0 + 30, y0 + 180, "SELF-LIFTING", True, a=k * eout(lin(t, T_ITSELF - 0.4, T_ITSELF)),
                 size=30)


def draw_labels(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return
    yb = yb_at(t)
    dp = pen(t)
    brand.label(cv, t, "PISTON = RAM", tuple(pj(-BORE + 8, yb - RAM_H / 2 + dp, -20)), (80, pj(0, yb - RAM_H / 2 + dp)[1]),
                C_RAM, T_PISTON - 0.05, T_PROB - 0.2)
    brand.label(cv, t, "RAM", tuple(pj(-BORE + 8, yb - RAM_H / 2 + dp, -20)), (80, 700), C_RAM, T_RAM - 0.05,
                T_START)
    brand.label(cv, t, "CYLINDER", tuple(pj(WALL, -560 + dp, -20)), (930, 430), hx("#6b7c96"), T_CYL - 0.05,
                T_START, align="right")
    brand.label(cv, t, "IMPACT BLOCK", tuple(pj(BORE - 6, -40 + dp, -20)), (930, 960), STEEL, T_IMPACT - 0.05,
                T_START, align="right")
    brand.label(cv, t, "PILE", tuple(pj(PILE_R, 140 + dp, -10)), (930, 1150), C_PILE, T_PILE - 0.05, T_START,
                align="right")
    brand.label(cv, t, "FUEL PUMP", tuple(pj(-WALL - 80, LEV_Y - 30 + dp, -30)), (80, 600), AMBER, T_PUMP - 0.05,
                T_START)
    brand.label(cv, t, "EXHAUST PORTS", tuple(pj(WALL + 70, PORT_Y - 6 + dp, 0)), (930, 740), YEL, T_EXH_P - 0.05,
                T_START, align="right")
    # start
    brand.label(cv, t, "TRIP", tuple(pj(34, YB_TOP - RAM_H - 50 + dp, 0)), (80, 380), YEL, T_TRIP - 0.05,
                T_GO + 0.6)
    k = win(t, T_LIFTS - 0.1, T_FALL + 0.1, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "CRANE LIFTS · TRIP RELEASES", font("inter_xb", 30), INK, border=YEL, a=k, align="center",
             tracking=2)
    # fall
    brand.label(cv, t, "PUMP LEVER", tuple(pj(-BORE + 6, LEV_Y + 14 + dp, 0)), (80, 560), RED, T_PRESSES - 0.05,
                T_SQUIRTS)
    brand.label(cv, t, "DIESEL ONTO THE BLOCK", tuple(pj(-30, BLOCK_TOP - 4 + dp, 0)), (80, 1010), AMBER,
                T_SQUIRTS - 0.05, T_COVERS)
    brand.label(cv, t, "PORTS CLOSED", tuple(pj(WALL + 4, PORT_Y + dp, 0)), (930, 740), RED, T_COVERS - 0.05,
                T_SQUEEZED, align="right")
    k = win(t, T_TRAPPING - 0.1, T_SQUEEZED - 0.05, 0.25, 0.25)
    if k > 0:
        pill(cv, 540, 1300, "AIR TRAPPED UNDER THE RAM", font("inter_xb", 30), INK, border=CYAN, a=k, align="center",
             tracking=2)
    k = win(t, T_SQUEEZED + 0.1, T_SLAMS + 0.1, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "SQUEEZED AIR GETS HOT", font("inter_xb", 30), INK, border=AMBER, a=k, align="center",
             tracking=2)
    brand.label(cv, t, "FUEL MIST", tuple(pj(-40, BLOCK_TOP - 20 + dp, 0)), (80, 1010), AMBER, T_SPLASH - 0.05,
                T_IGNITES + 0.1)
    k = win(t, T_IGNITES - 0.1, T_RESULT + 0.1, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "IGNITES FROM THE HEAT · NO SPARK", font("inter_xb", 28), INK, border=RED, a=k,
             align="center", tracking=2)
    # result: both ways
    k = win(t, T_BOTH - 0.1, T_RISE + 0.1, 0.25, 0.35) * kE
    if k > 0:
        kd = k * eout(lin(t, T_DRIVES - 0.1, T_DRIVES + 0.3))
        q = pj(PILE_R + 40, 120 + dp, 0)
        arrow(cv, q[0] + 30, q[1] - 90, q[0] + 30, q[1] + 60, RED, a=kd)
        pill(cv, q[0] + 70, q[1] - 10, "PILE DOWN", font("inter_xb", 28), INK, border=RED, a=kd, tracking=2)
        ku = k * eout(lin(t, T_THROWS - 0.1, T_THROWS + 0.3))
        q = pj(-WALL - 60, yb - 60 + dp, 0)
        arrow(cv, q[0] - 40, q[1] + 60, q[0] - 40, q[1] - 110, RED, a=ku)
        pill(cv, 80, q[1] - 160, "RAM UP", font("inter_xb", 28), INK, border=RED, a=ku, tracking=2)
    # rise
    brand.label(cv, t, "EXHAUST OUT", tuple(pj(WALL + 80, PORT_Y - 8 + dp, 0)), (930, 740), C_BURNT,
                T_EXH_R - 0.05, T_GRAVITY + 0.3, align="right")
    brand.label(cv, t, "FRESH AIR IN", tuple(pj(-WALL - 100, PORT_Y + 26 + dp, 0)), (80, 900), CYAN,
                T_FRESH - 0.05, T_GRAVITY + 0.5)
    k = win(t, T_GRAVITY - 0.1, T_NOCRANK, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "GRAVITY · NEXT BLOW", font("inter_xb", 30), INK, border=YEL, a=k, align="center",
             tracking=2)
    k = win(t, T_NOCRANK - 0.2, T_END + 0.05, 0.25, 0.3) * kE
    if k > 0:
        brand.bullet(cv, 90, 1250, "NO CRANKSHAFT", False, a=k, size=30)
        brand.bullet(cv, 90, 1305, "NO SPARK PLUG", False, a=k * eout(lin(t, T_NOSPARK - 0.1, T_NOSPARK + 0.2)),
                     size=30)
        brand.bullet(cv, 90, 1360, "RUNS ON FUEL ALONE", True, a=k * eout(lin(t, T_RUNS - 0.1, T_RUNS + 0.2)),
                     size=30)


def phase_name(t):
    if t < T_PARTS - 0.3:
        return "RUNNING", GREEN
    if t < T_START:
        return "AT REST", MUTED
    if t < T_GO:
        return "STARTING", YEL
    if t < T_TRAPPING:
        return "FALLING", CYAN
    if t < T_IGNITES:
        return "COMPRESSING", AMBER
    if t < T_RISE:
        return "POWER", RED
    if t < T_DOWN2:
        return "EXHAUST + FRESH AIR", C_BURNT
    return "RUNNING", GREEN


def draw_header(cv, t):
    k = win(t, T_WHAT + 0.3, T_END, 0.3, 0.3)
    if k <= 0:
        return
    nm, c = phase_name(t)
    brand.status_pill(cv, k, nm, c)
    brand.readout(cv, k, f"{blows(t)}", "BLOWS")
    brand.note(cv, "ANIMATION SLOWED", k * win(t, T_START, T_DOWN2 + 0.3, 0.3, 0.3) * 0.9, dy=-36)


def draw_stamps(cv, t):
    brand.stamp(cv, t, "BANG!", T_BANG, center=(780, 1000))


def draw(cv, t):
    draw_hammer(cv, t)
    draw_hook(cv, t)
    draw_what(cv, t)
    draw_problem(cv, t)
    draw_labels(cv, t)
    draw_header(cv, t)
    draw_stamps(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_IGNITES
MUSIC_START = T_WHAT


def sound():
    sfx = [(b, "impact", 0.42 if b < T_HOOK_OUT + 0.5 else 0.22) for b in BANGS_FREE if b < T_END + 0.5]
    sfx += [(T_HOOK_OUT - 0.1, "whoosh_big", 0.5),
            (T_RAM, "tick", 0.2), (T_CYL, "tick", 0.2), (T_IMPACT, "tick", 0.2), (T_PILE, "tick", 0.2),
            (T_PUMP, "tick", 0.2), (T_EXH_P, "tick", 0.2),
            (T_LIFTS, "whoosh_up", 0.3), (T_GO, "clunk", 0.45), (T_PRESSES, "clunk", 0.3), (T_SQUIRTS, "hiss", 0.35),
            (T_COVERS, "clunk", 0.3), (T_SLAMS, "clunk", 0.55), (T_IGNITES, "impact_long", 0.75),
            (T_THROWS, "whoosh_up", 0.4), (T_EXH_R, "hiss", 0.4), (T_GRAVITY, "whoosh_down", 0.35)]
    return {"build": (T_FALL, T_IGNITES), "drop": (T_IGNITES, T_OUTRO - 0.05), "sfx": sfx}
