"""Jake brake visuals + sound plan (first episode in the upgraded look). Cues tied to words via F(line, word).

Scenes
  ROAD   (hook, result, sign)  night mountain grade, semi descending, lit with ev.look (sky, ridges, haze, beams,
                               wet reflections); exhaust pulses + pressure rings on every release
  XRAY   (what)                camera pushes in, the hood turns to glass and shows the inline six
  BRAKE  (problem)             drive wheel close-up: drum brake heating towards fade
  CYL    (normal, jake, key)   one-cylinder cutaway with the engine-brake housing; exact slider-crank, 720-deg
                               cycle, valve events, adiabatic cylinder pressure, pressure-vs-crank graph
  SIX    (sound)               top view of the six cylinders releasing in firing order 1-5-3-6-2-4 into the stack

Mechanism model (engine braking = no fuel, so no combustion):
  cycle angle c: 0 TDC (intake starts), 180 BDC, 360 TDC (end of compression), 540 BDC, 720 TDC (end of exhaust)
  normal valves: intake 0..180, exhaust 540..720.  Engine brake: exhaust valve also opened 338..378 (small lift),
  driven hydraulically (engine oil) from the injector rocker, which moves near TDC of compression.
  pressure: adiabatic p = (V0/V)^1.35 while valves are shut; with the brake, p falls to ~1 bar as the valve
  opens, then the expansion stroke starts from ~1 bar (so almost no work comes back).
"""
import math

import numpy as np
import skia
from scipy.interpolate import PchipInterpolator

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, flow, pipe, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_MG = F("hook", "machine")
T_FIGHT = F("hook", "fighting")
T_WHAT = L("what")["start"]
T_JAKE1 = F("what", "jake")
T_HOW = F("what", "here's")
T_PROB = L("problem")["start"]
T_WHEEL = F("problem", "wheel")
T_HOT = F("problem", "overheat.")
T_NORMAL = L("normal")["start"]
T_FUEL = F("normal", "fuel,")
T_SQZ = F("normal", "squeezes")
T_UP = F("normal", "up.")
T_PUSH = F("normal", "pushes")
T_SPRING = F("normal", "spring.")
T_COMES = F("normal", "comes")
T_JAKE = L("jake")["start"]
T_BREAKS = F("jake", "breaks")
T_OIL = F("jake", "oil")
T_POPS = F("jake", "pops")
T_EXV = F("jake", "exhaust")
T_TOP = F("jake", "top")
T_KEY = L("key")["start"]
T_BANG = F("key", "bang.")
T_BLAST = F("key", "blasts")
T_NOTHING = F("key", "nothing")
T_GONE = F("key", "gone.")
T_RESULT = L("result")["start"]
T_COMP = F("result", "compressor")
T_HOLDS = F("result", "holds")
T_COOL = F("result", "cool.")
T_SOUND = L("sound")["start"]
T_PULSE = F("sound", "pulse")
T_SIX = F("sound", "six")
T_MG2 = F("sound", "machine")
T_TOWNS = F("sound", "towns")
T_SIGN = F("sound", "no")
T_OUTRO = L("outro")["start"]

# scene windows
S_ROAD1 = (0.0, T_PROB + 0.3)
S_XRAY = (T_WHAT - 0.2, T_PROB + 0.3)
S_BRAKE = (T_PROB - 0.1, T_NORMAL + 0.3)
S_CYL = (T_NORMAL - 0.1, T_RESULT + 0.3)
S_ROAD2 = (T_RESULT - 0.1, T_SOUND + 0.3)
S_SIX = (T_SOUND - 0.1, T_TOWNS + 0.2)
S_ROAD3 = (T_TOWNS - 0.1, T_TOTAL + 1)


def scene_k(t, s, fin=0.35, fout=0.35):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== engine-brake release clock (road + six scenes)
FIRING = [1, 5, 3, 6, 2, 4]


def release_times(t0, t1, rate):
    """Release events (one cylinder each) at `rate` per second between t0 and t1."""
    n = int(max(0, (t1 - t0) * rate))
    return [t0 + i / rate for i in range(n)]


REL_HOOK = release_times(0.05, T_WHAT + 0.4, 11.0)          # the machine gun, real-time-ish
REL_ROAD2 = release_times(T_RESULT, T_SOUND + 0.3, 9.0)
REL_SIX = release_times(T_PULSE - 0.1, T_TOWNS + 0.2, 3.2)       # slowed for the top view
REL_ROAD3 = release_times(T_TOWNS, T_END, 9.0)
ALL_REL = REL_HOOK + REL_ROAD2 + REL_ROAD3


def last_release(t, events):
    past = [e for e in events if e <= t]
    return (t - past[-1], len(past) - 1) if past else (1e9, -1)


# ================================================================== cylinder model
R_CR, ROD, PIN_H, PIST_H, BORE = 52.0, 190.0, 36.0, 70.0, 64.0
DECK = R_CR + ROD + PIN_H + 10.0          # crank centre -> deck (upwards)
HEAD_H = 120.0
CR = 16.0                                  # illustrative compression ratio (not stated in the video)
EXH_X, INT_X = 30.0, -30.0
LIFT_N, LIFT_J = 16.0, 6.0
JB_OPEN = (338.0, 378.0)


def pin_s(c):
    a = math.radians(c)
    return R_CR * math.cos(a) + math.sqrt(ROD ** 2 - (R_CR * math.sin(a)) ** 2)


S_TDC, S_BDC = R_CR + ROD, ROD - R_CR


def vol(c):
    """Cylinder volume, 1 at BDC."""
    vc = 1.0 / (CR - 1)
    return ((S_TDC - pin_s(c)) / (S_TDC - S_BDC)) + vc


V_BDC = vol(180.0)


def lift_curve(c, a, b, peak):
    if a < c < b:
        return peak * math.sin(math.pi * (c - a) / (b - a)) ** 0.8
    return 0.0


def valves(c, jake_on):
    c = c % 720
    li = lift_curve(c, 0, 190, LIFT_N)
    le = lift_curve(c, 530, 720, LIFT_N)
    lj = lift_curve(c, *JB_OPEN, LIFT_J) if jake_on else 0.0
    return li, max(le, lj), lj


def pressure(c, jake_on):
    """Cylinder pressure (bar, illustrative) through compression and expansion; ~1 elsewhere."""
    c = c % 720
    if c < 180 or c > 540:
        return 1.0
    if not jake_on:
        return (V_BDC / vol(c)) ** 1.35
    a0 = JB_OPEN[0]
    if c <= a0:
        return (V_BDC / vol(c)) ** 1.35
    p_open = (V_BDC / vol(a0)) ** 1.35
    if c <= JB_OPEN[1]:
        k = (c - a0) / (JB_OPEN[1] - a0)
        return 1.0 + (p_open - 1.0) * math.exp(-6.0 * k)
    p_end = 1.0 + (p_open - 1.0) * math.exp(-6.0)
    return p_end * (vol(JB_OPEN[1]) / vol(c)) ** 1.35


P_MAX = (V_BDC / vol(360.0)) ** 1.35


def check_physics():
    bad = []
    if abs(vol(180.0) - vol(540.0)) > 1e-9 or vol(360.0) >= vol(300.0):
        bad.append("volume not symmetric / TDC not minimum")
    if pressure(360, True) > 0.2 * P_MAX:
        bad.append("brake does not release the pressure by TDC")
    if pressure(450, True) > 1.2:
        bad.append("expansion stroke still pushes with the brake on")
    if abs(pressure(300, False) - pressure(420, False)) > 1e-6:
        bad.append("normal air spring not symmetric")
    if DECK - (R_CR + ROD + PIN_H) < 5:
        bad.append("piston hits head")
    return bad


assert not check_physics(), check_physics()


# cycle angle vs time (slowed, keyed to the narration)
_KEYS = [(T_NORMAL - 0.4, 150.0), (T_SQZ, 200.0), (T_SPRING, 360.0), (T_COMES + 0.3, 545.0),
         (T_BREAKS, 640.0), (T_OIL, 720.0 + 200.0), (T_POPS, 720.0 + 338.0), (T_TOP + 0.4, 720.0 + 350.0),
         (T_BANG - 0.05, 720.0 + 354.0), (T_BANG + 0.55, 720.0 + 380.0), (T_GONE, 720.0 + 540.0),
         (T_RESULT + 0.4, 720.0 + 600.0)]
_CI = PchipInterpolator([k[0] for k in _KEYS], [k[1] for k in _KEYS])


def cyc(t):
    t = clamp(t, _KEYS[0][0], _KEYS[-1][0])
    return float(_CI(t))


def jake_on(t):
    return t >= T_BREAKS - 0.2


# ================================================================== ROAD scene
GRADE = math.radians(6.0)
HORIZON = 980
TR_S = 0.50
SPEED = 520.0          # px/s scroll of road features (illustrative)


def truck_proj(cx, cy, s):
    return Proj(cx, cy, s, yaw=74, pitch=10)


C_CAB = hx("#b8322f")
C_TRAILER = hx("#c9d0da")
C_CHROME = hx("#d9e2ee")
C_TIRE = hx("#17191d")


def draw_truck(cv, pj, t, rel_events, xray=0.0):
    """Semi truck, facing +X. Units: cm. Wheels sit on Y = 0."""
    zf, zb = -125.0, 125.0
    # trailer
    extrude(cv, pj, np.array([[0, -400], [1300, -400], [1300, -125], [0, -125]], float), zf, zb, C_TRAILER)
    cv_line = pj(np.array([0, 1300]), np.array([-262, -262]), np.array([zf, zf]))
    cv.drawLine(*cv_line[0], *cv_line[1], paint(hx("#9aa4b2"), stroke=2 * pj.s))
    # chassis rail
    extrude(cv, pj, np.array([[1250, -125], [1960, -125], [1960, -95], [1250, -95]], float), zf + 20, zb - 20,
            hx("#2a2f38"))
    # cab + hood (glass when x-rayed)
    ca = 1 - 0.78 * xray
    cab = np.array([[1340, -350], [1640, -350], [1660, -230], [1950, -215], [1965, -110], [1340, -110]], float)
    extrude(cv, pj, cab, zf, zb, C_CAB, alpha=ca)
    # windshield + side window
    ws = pj(np.array([1645, 1660, 1660, 1645]), np.array([-340, -240, -240, -340]), np.array([zf - 1, zf - 1, zb, zb]))
    sw = pj(np.array([1420, 1610, 1610, 1420]), np.array([-330, -330, -250, -250]), np.full(4, zf - 1))
    for poly, a in ((sw, 0.95), (ws, 0.9)):
        g = skia.Paint(AntiAlias=True)
        g.setShader(lin_grad(tuple(poly[0]), tuple(poly[2]), [hx("#7fa6d6"), hx("#0f1a2b")]))
        g.setAlphaf(a * ca)
        cv.drawPath(poly_path(poly), g)
    # inline six inside the hood (x-ray)
    if xray > 0:
        for i in range(6):
            x = 1690 + 42 * i
            pk = 0.0
            for e in rel_events:
                if 0 <= t - e < 0.25 and FIRING[(rel_events.index(e)) % 6] == i + 1:
                    pk = 1 - (t - e) / 0.25
            col = mix(CYAN, AMBER, pk)
            p0, p1 = pj(x, -205, 0), pj(x, -140, 0)
            cv.drawLine(*p0, *p1, paint(col, a=xray, stroke=22 * pj.s, cap=skia.Paint.kRound_Cap))
            cv.drawLine(*p0, *p1, paint(col, a=0.5 * xray, stroke=40 * pj.s, blur=8 * pj.s))
        blk = pj(np.array([1670, 1940, 1940, 1670]), np.array([-225, -225, -120, -120]), np.zeros(4))
        cv.drawPath(poly_path(blk), paint(CYAN, a=0.8 * xray, stroke=3))
    # exhaust stack (near side, behind the cab)
    stack_top = (1330.0, -470.0, zf + 10)
    cyl3(cv, pj, (1330, -150, zf + 10), stack_top, 13, C_CHROME, n=24)
    # wheels
    for x in (180, 320, 1460, 1590, 1840):
        for z in (zf + 5, ):
            cyl3(cv, pj, (x, -52, z - 2), (x, -52, z + 40), 52, C_TIRE, n=40, edge=hx("#000000"))
            hub = pj(x, -52, z - 3)
            cv.drawCircle(*hub, 22 * pj.s, paint(C_CHROME))
            cv.drawCircle(*hub, 22 * pj.s, paint(hx("#5a6575"), stroke=2))
    # lights: headlight, marker lights
    hl = pj(1966, -150, zf + 30)
    look.bloom(cv, hl[0], hl[1], 9 * pj.s / 0.42, hx("#fff4d6"), a=0.95)
    for x in (60, 400, 750, 1100, 1290):
        m = pj(x, -395, zf - 1)
        look.bloom(cv, m[0], m[1], 4, AMBER, a=0.9)
    tl_ = pj(5, -150, zf - 1)
    look.bloom(cv, tl_[0], tl_[1], 6, RED, a=0.8)
    return pj(*stack_top), hl


def draw_road(cv, t, k, rel_events, cam=(560.0, 1130.0, TR_S), xray=0.0, sign_k=0.0, sign_x=None):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, HORIZON, t=t)
    look.mountains(cv, HORIZON, offset=t * 90)
    look.haze(cv, HORIZON - 260, HORIZON + 60, a=0.10)
    cx, cy, s = cam
    cv.save()
    cv.rotate(math.degrees(GRADE), cx, cy)
    # road slab
    road_top = cy + 4
    rp = skia.Paint()
    rp.setShader(lin_grad((0, road_top), (0, road_top + 900), [hx("#1b1f27"), hx("#0b0d11")]))
    cv.drawRect(skia.Rect.MakeLTRB(-800, road_top, W + 800, road_top + 900), rp)
    cv.drawRect(skia.Rect.MakeLTRB(-800, road_top, W + 800, road_top + 10), paint(hx("#3a4250")))
    # moving lane dashes + guard-rail posts (parallax: we follow the truck)
    off = (t * SPEED) % 260
    for i in range(-4, 12):
        x = i * 260 - off
        cv.drawRect(skia.Rect.MakeXYWH(x, road_top + 70, 130, 10), paint(hx("#d8d2a8"), a=0.55))
        x2 = i * 260 - (t * SPEED * 1.6) % 260
        cv.drawRect(skia.Rect.MakeXYWH(x2, road_top + 250, 170, 14), paint(hx("#d8d2a8"), a=0.45))
    cv.drawRect(skia.Rect.MakeLTRB(-800, road_top + 470, W + 800, road_top + 482), paint(hx("#e8e4d0"), a=0.5))
    off2 = (t * SPEED * 1.25) % 180
    for i in range(-4, 14):
        x = i * 180 - off2
        cv.drawRect(skia.Rect.MakeXYWH(x, road_top - 60, 8, 60), paint(hx("#4b5566")))
    cv.drawRect(skia.Rect.MakeLTRB(-800, road_top - 58, W + 800, road_top - 44), paint(hx("#7d889b")))
    # sign (passes by)
    pj = truck_proj(cx - 980 * s * 0.98, cy, s)
    look.soft_shadow(cv, cx, cy + 6, 1100 * s * 1.9, 60, a=0.6)
    stack, hl = draw_truck(cv, pj, t, rel_events, xray)
    # headlight beam + wet reflections
    look.beam(cv, hl, (hl[0] + 700, hl[1] + 60), 10, 160, a=0.30)
    look.wet_reflection(cv, hl[0], road_top + 12, road_top + 300, 26, hx("#fff1c9"), a=0.35)
    for e in (0.08, 0.3, 0.52, 0.7):
        m = pj(1300 * e, -395, -126)
        look.wet_reflection(cv, m[0], road_top + 14, road_top + 160, 10, AMBER, a=0.18)
    if sign_k > 0 and sign_x is not None:
        # kept above y~1380 so the captions (y~1440) never cover it
        look.road_sign(cv, sign_x, road_top + 235, ["NO", "ENGINE", "BRAKE"], w=240, h=195, a=sign_k, post=70)
        look.beam(cv, (sign_x + 320, road_top + 120), (sign_x, road_top + 150), 4, 120, a=0.12 * sign_k)
    cv.restore()
    # exhaust pulses: puff + pressure ring at every release
    sp = np.array(stack)
    for e in rel_events:
        age = t - e
        if 0 <= age < 0.9:
            look.puff(cv, sp[0], sp[1] - 6, age, life=0.9, size=26, a=0.35)
        if 0 <= age < 0.35:
            r = 20 + 240 * age
            cv.drawCircle(sp[0], sp[1], r, paint(INK, a=0.55 * (1 - age / 0.35), stroke=3))
    look.vignette(cv, 0.55)
    cv.restore()


def draw_road_overlays(cv, t):
    # hook chips under the scene
    k = win(t, T_MG - 0.1, T_HOOK_OUT + 0.3, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1330, "ENGINE BRAKE ON · NO FUEL", font("inter_xb", 30), INK, border=AMBER, a=k, align="center",
             tracking=2, dot=AMBER)
    k = win(t, T_JAKE1 - 0.1, T_PROB + 0.1, 0.25, 0.3)
    if k > 0:
        brand.chips(cv, k, 1330, [("JAKE BRAKE", eout(lin(t, T_JAKE1, T_JAKE1 + 0.3))),
                                  ("ENGINE BRAKE", eout(lin(t, T_JAKE1 + 0.3, T_JAKE1 + 0.6))),
                                  ("COMPRESSION RELEASE", eout(lin(t, T_HOW, T_HOW + 0.3)))], center=True)
    # result
    k = win(t, T_COMP - 0.2, T_SOUND, 0.25, 0.3)
    if k > 0:
        brand.stamp(cv, t, "AIR COMPRESSOR", T_COMP, dur=1.5, center=(540, 600), color=CYAN, bg=hx("#05202a"))
        kb = win(t, T_HOLDS - 0.1, T_SOUND, 0.25, 0.3)
        if kb > 0:
            brand.bullet(cv, 300, 1300, "SPEED HELD ON THE GRADE", True, a=kb)
        kc = win(t, T_COOL - 0.3, T_SOUND, 0.25, 0.3)
        if kc > 0:
            brand.bullet(cv, 300, 1365, "WHEEL BRAKES STAY COOL", True, a=kc)


# ================================================================== BRAKE close-up
def draw_brake(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    brand_bg = brand.background()
    cv.drawImage(brand_bg, 0, 0)
    heat = eout(lin(t, T_WHEEL - 0.3, T_HOT + 0.6))
    cx, cy = 540.0, 820.0
    pj = Proj(cx, cy, 1.0, yaw=80, pitch=8)
    rot = t * 2.6
    # tyre
    cyl3(cv, pj, (0, 0, -140), (0, 0, 140), 330, C_TIRE, n=72, edge=hx("#000000"))
    # brake drum (inside the wheel), glowing with heat
    drum_c = mix(hx("#5a6170"), hx("#ff5a1f"), 0.85 * heat)
    face = pj(0, 0, -142)
    cv.drawCircle(face[0], face[1], 250, paint(hx("#2a2f38")))
    cv.drawCircle(face[0], face[1], 190, paint(drum_c))
    if heat > 0:
        cv.drawCircle(face[0], face[1], 230, paint(hx("#ff6a2a"), a=0.55 * heat, blur=40))
        cv.drawCircle(face[0], face[1], 150, paint(hx("#ffd08a"), a=0.35 * heat, blur=30))
        # heat shimmer lines
        for i in range(7):
            x = face[0] - 150 + 50 * i
            y0 = face[1] - 260 - 40 * math.sin(t * 4 + i)
            pth = skia.Path()
            pth.moveTo(x, y0)
            for j in range(1, 8):
                pth.lineTo(x + 10 * math.sin(t * 6 + i + j), y0 - 22 * j)
            cv.drawPath(pth, paint(hx("#ffb27a"), a=0.25 * heat, stroke=3))
    for i in range(10):
        a = rot + i * 2 * math.pi / 10
        x, y = face[0] + 120 * math.cos(a), face[1] + 120 * math.sin(a) * 0.95
        cv.drawCircle(x, y, 14, paint(hx("#c7ced9")))
    cv.drawCircle(face[0], face[1], 60, paint(hx("#c7ced9")))
    cv.drawCircle(face[0], face[1], 60, paint(hx("#5a6575"), stroke=3))
    brand.label(cv, t, "WHEEL BRAKES", (face[0] - 150, face[1] - 60), (90, 470), YEL, T_WHEEL - 0.1, T_NORMAL)
    # temperature bar
    x0, x1, y = 140.0, 900.0, 1330.0
    cv.drawLine(x0, y, x1, y, paint(hx("#263043"), stroke=16, cap=skia.Paint.kRound_Cap))
    cv.drawLine(x0, y, x0 + (x1 - x0) * (0.2 + 0.78 * heat), y,
                paint(mix(CYAN, RED, heat), stroke=16, cap=skia.Paint.kRound_Cap))
    draw_text(cv, "BRAKE TEMPERATURE", x0, y - 30, font("inter_xb", 24), MUTED, tracking=3)
    cv.restore()
    brand.stamp(cv, t, "OVERHEATING", T_HOT, dur=1.5, center=(540, 1220))


# ================================================================== CYLINDER cutaway
def cyl_proj(t):
    k = ease(lin(t, T_NORMAL - 0.2, T_NORMAL + 1.4))
    s = 1.45 - 0.15 * ease(lin(t, T_JAKE - 0.2, T_JAKE + 1.2))
    yaw = 28 + 14 * (1 - k) + 8 * math.sin(t * 0.25)
    oy = 1060 + 40 * ease(lin(t, T_JAKE - 0.2, T_JAKE + 1.2))
    return Proj(520, oy, s, yaw=yaw, pitch=16)


def draw_cyl(cv, t, k):
    if k <= 0:
        return
    pj = cyl_proj(t)
    c = cyc(t)
    jon = jake_on(t)
    li, le, lj = valves(c, jon)
    s_pin = pin_s(c)
    p = pressure(c, jon)
    a = math.radians(c)
    cv.saveLayerAlpha(None, int(255 * k))
    # block (glass) + liner
    blk = np.array([[-110, 0 - 40], [110, -40], [110, -DECK], [-110, -DECK]], float)
    extrude(cv, pj, blk, -90, 90, hx("#4d5767"), alpha=0.22)
    cyl3(cv, pj, (0, -S_BDC - PIN_H - PIST_H + 10, 0), (0, -DECK, 0), BORE + 4, hx("#6b7c96"), fill_a=0.12,
         edge=hx("#7d8fae"), edge_w=1.2, cap=False, n=48)
    # crank
    cpin = (R_CR * math.sin(a), -R_CR * math.cos(a))
    for z0, z1 in ((28, 42), (-42, -28)):
        prof = []
        ang = math.atan2(cpin[1], cpin[0])
        for th in np.linspace(0, 2 * np.pi, 48, endpoint=False):
            d = (th - ang) % (2 * np.pi)
            r = 30 + (R_CR + 6) * max(0, math.cos(d)) ** 6 + 46 * max(0, -math.cos(d)) ** 0.7
            prof.append((r * math.cos(th), r * math.sin(th)))
        extrude(cv, pj, np.array(prof), z0, z1, STEEL_D)
    cyl3(cv, pj, (cpin[0], cpin[1], 30), (cpin[0], cpin[1], -30), 16, STEEL, n=24)
    # rod
    ppin = np.array([0.0, -s_pin])
    v = ppin - np.array(cpin)
    v /= np.linalg.norm(v)
    n = np.array([-v[1], v[0]])
    rod = [np.array(cpin) + n * 16, ppin + n * 10, ppin - n * 10, np.array(cpin) - n * 16]
    extrude(cv, pj, np.array(rod), -9, 9, hx("#7d889b"))
    # compressed air in the cylinder (density ~ pressure)
    crown = -s_pin - PIN_H
    hot = clamp((p - 1) / (P_MAX - 1))
    rng = np.random.default_rng(int(t * 24))
    npart = int(30 + 90 * hot)
    for _ in range(npart):
        x = rng.uniform(-BORE + 8, BORE - 8)
        y = rng.uniform(-DECK + 4, crown - 4) if crown - 4 > -DECK + 4 else -DECK + 4
        z = rng.uniform(-BORE + 8, BORE - 8)
        if x * x + z * z > (BORE - 8) ** 2:
            continue
        q = pj(x, y, z)
        cv.drawCircle(q[0], q[1], 3.2, paint(mix(CYAN, AMBER, hot), a=0.75))
    if hot > 0.05:
        q = pj(0, (crown - DECK) / 2, 0)
        cv.drawCircle(q[0], q[1], 70 * pj.s * 1.6, paint(AMBER, a=0.25 * hot, blur=30))
    # piston
    pc = mix(STEEL, YEL, 0.3 * win(t, T_SQZ - 0.1, T_COMES, 0.2, 0.4))
    cyl3(cv, pj, (0, crown + PIST_H, 0), (0, crown, 0), BORE - 3, pc, n=48)
    for yy in (crown + 10, crown + 18):
        ring_pts = pj(np.cos(np.linspace(0, np.pi, 30)) * (BORE - 2), np.full(30, yy),
                      -np.sin(np.linspace(0, np.pi, 30)) * (BORE - 2))
        cv.drawPath(poly_path(ring_pts, close=False), paint(shade(STEEL, 0.5), stroke=1.6))
    # head (glass) with ports
    head = np.array([[-110, -DECK], [110, -DECK], [110, -DECK - HEAD_H], [-110, -DECK - HEAD_H]], float)
    extrude(cv, pj, head, -90, 90, hx("#55606f"), alpha=0.28)
    # exhaust port + gas jet when the valve is open
    port = spline(pj(np.array([EXH_X, EXH_X + 10, 150, 260]), np.array([-DECK - 10, -DECK - 60, -DECK - 80, -DECK - 80]),
                     np.zeros(4)), 30)
    pipe(cv, port, 46 * pj.s, hx("#7a8496"), glass=True)
    blast = 0.0
    if le > 0.5:
        blast = clamp(le / LIFT_J) * clamp((p - 1) / 6 + (0.35 if c % 720 > 530 else 0))
    if jon and JB_OPEN[0] < c % 720 < JB_OPEN[1] + 12:
        blast = max(blast, clamp((pressure(c, True) - 1) / 8 + 0.3))
    if blast > 0.02:
        flow(cv, port, t, 1100, 12, AMBER, r=7, a=blast)
        end = port[-1]
        look.bloom(cv, end[0], end[1], 26 * blast + 4, AMBER, a=blast)
        for j in range(3):
            ph = ((t * 3.0) + j / 3) % 1.0
            cv.drawCircle(end[0], end[1], 30 + 220 * ph, paint(AMBER, a=0.6 * blast * (1 - ph), stroke=4))
        vlv = pj(EXH_X, -DECK + 8, 0)
        cv.drawCircle(vlv[0], vlv[1], 50 * blast, paint(AMBER, a=0.5 * blast, blur=16))
    # valves (intake left, exhaust right)
    for x, lift, isx in ((INT_X, li, False), (EXH_X, le, True)):
        face_y = -DECK + lift
        vcol = mix(STEEL, AMBER, 0.6 * clamp(lj / LIFT_J)) if isx else mix(STEEL, CYAN, 0.5 * clamp(lift / LIFT_N))
        q0, q1 = pj(x, face_y - 4, 0), pj(x, -DECK - HEAD_H - 40 + lift, 0)
        cv.drawLine(*q0, *q1, paint(vcol, stroke=6))
        cyl3(cv, pj, (x, face_y, 0), (x, face_y - 6, 0), 26, vcol, n=32)
        draw_spring(cv, pj, x, 0, 16, -DECK - HEAD_H + 8 + lift, -DECK - HEAD_H - 34 + lift * 0.4, 5, hx("#9aa6b8"),
                    width=3.5)
    # rocker arms + engine-brake housing
    top = -DECK - HEAD_H - 40
    jk = eout(lin(t, T_BREAKS - 0.2, T_BREAKS + 0.6))
    # exhaust rocker (pivot at x=110): tip pushes valve down by le
    piv = np.array([110.0, top - 30])
    tip = np.array([EXH_X, top + le])
    rk = [tip + np.array([0, -10]), piv + np.array([0, -12]), piv + np.array([0, 12]), tip + np.array([0, 10])]
    extrude(cv, pj, np.array(rk), -10, 10, hx("#8c96a8"))
    if jk > 0:
        # housing
        hy0, hy1 = top - 150, top - 70
        house = np.array([[-90, hy0], [140, hy0], [140, hy1], [-90, hy1]], float)
        extrude(cv, pj, house, -40, 40, mix(hx("#3a4352"), AMBER, 0.15), alpha=0.85 * jk, rim=AMBER, rim_w=1.4,
                rim_glow=0.4 * jk)
        # master piston over the injector rocker (x=-50), slave piston over the exhaust valve (x=EXH_X)
        inj = lift_curve(c % 720, 320, 380, 9.0) if jon else 0.0
        oil_on = clamp(inj / 4) * jk
        cyl3(cv, pj, (-50, hy1 + 2, 0), (-50, hy1 + 34 - inj, 0), 16, hx("#c8d2e2"), n=24)
        cyl3(cv, pj, (EXH_X, hy1 + 2, 0), (EXH_X, top - 4 + lj, 0), 14, mix(hx("#c8d2e2"), AMBER, 0.6 * oil_on), n=24)
        oil = pj(np.array([-50, -50, EXH_X, EXH_X]), np.array([hy1 - 20, hy0 + 20, hy0 + 20, hy1 - 20]), np.zeros(4))
        pipe(cv, oil, 12, AMBER, a=jk, glass=True)
        if oil_on > 0.05:
            flow(cv, oil, t, 260, 14, AMBER, r=4, a=oil_on)
        # injector rocker (pushes master piston up near TDC of compression)
        ir = np.array([[-110, hy1 + 40 - inj], [10, hy1 + 40 - inj], [10, hy1 + 52 - inj], [-110, hy1 + 52 - inj]], float)
        extrude(cv, pj, ir, -10, 10, hx("#8c96a8"), alpha=jk)
        brand.label(cv, t, "ENGINE OIL", tuple(pj(-50, hy0 + 20, 0)), (90, 560), AMBER, T_OIL - 0.1, T_KEY)
        brand.label(cv, t, "EXHAUST VALVE", tuple(pj(EXH_X + 26, -DECK + 6, 0)), (940, 470), AMBER, T_EXV - 0.1,
                    T_KEY + 0.2, align="right")
    brand.label(cv, t, "PISTON", tuple(pj(-BORE, crown + 20, 0)), (90, 560), YEL, T_SQZ - 0.1, T_PUSH)
    cv.restore()
    draw_graph(cv, t, k, c, jon)


GX, GY, GW, GH = 150.0, 1228.0, 700.0, 115.0


def draw_graph(cv, t, k, c, jon):
    kg = k * win(t, T_SQZ - 0.3, T_RESULT + 0.2, 0.3, 0.3)
    if kg <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * kg))
    brand.graph_box(cv, (GX, GY, GW, GH), "CYLINDER PRESSURE", xlabel="UP STROKE · TOP · DOWN STROKE")
    cs = np.linspace(180, 540, 200)
    def pts(j):
        ys = np.array([pressure(x, j) for x in cs])
        return np.stack([GX + GW * (cs - 180) / 360, GY + GH - GH * 0.92 * (ys - 1) / (P_MAX - 1)], 1)
    pn, pjk = pts(False), pts(True)
    cv.drawLine(GX + GW / 2, GY, GX + GW / 2, GY + GH, paint(hx("#3a4559"), stroke=1.5))
    # normal curve: traced during the normal line, then kept dashed for reference
    cc = c % 720 if not jon else 540
    prog_n = clamp((cc - 180) / 360) if t < T_BREAKS else 1.0
    brand.curve(cv, pn, GREEN, prog=prog_n, dashed=t > T_BREAKS + 0.3, width=4)
    if t < T_BREAKS + 0.3:
        draw_text(cv, "AIR SPRINGS BACK", GX + GW, GY - 12, font("inter_xb", 22), GREEN, a=eout(lin(t, T_PUSH, T_PUSH + 0.4)),
                  align="right", tracking=2)
    if jon:
        cj = (c % 720) if t < T_RESULT else 540
        prog_j = clamp((cj - 180) / 360) if cj >= 180 else 0.0
        brand.curve(cv, pjk, RED, prog=prog_j, width=5)
        ka = eout(lin(t, T_NOTHING - 0.2, T_NOTHING + 0.5))
        if ka > 0:
            # shaded area: the energy that no longer comes back
            half = pn[100:]
            poly = np.vstack([half, pjk[100:][::-1]])
            cv.drawPath(poly_path(poly), paint(RED, a=0.25 * ka))
            draw_text(cv, "ENERGY THROWN AWAY", GX + GW, GY - 12, font("inter_xb", 22), RED, a=ka, align="right",
                      tracking=2)
    if 180 <= c % 720 <= 540 and t < T_RESULT:
        x = c % 720
        brand.dot(cv, GX + GW * (x - 180) / 360, GY + GH - GH * 0.92 * (pressure(x, jon) - 1) / (P_MAX - 1),
                  RED if jon else GREEN)
    cv.restore()


def draw_cyl_overlays(cv, t):
    brand.stamp(cv, t, "AIR SPRING", T_SPRING, dur=1.3, center=(770, 760), color=GREEN, bg=hx("#06281a"))
    brand.stamp(cv, t, "BANG", T_BANG, dur=1.1, center=(770, 760))
    brand.stamp(cv, t, "ENERGY GONE", T_GONE - 0.1, dur=1.3, center=(740, 760))
    k = win(t, T_FUEL - 0.2, T_SQZ + 0.4, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1080, "OFF THE FUEL: NO COMBUSTION", font("inter_xb", 28), INK, border=MUTED, a=k, align="center",
             tracking=2)


# ================================================================== SIX cylinders (top view)
def draw_six(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    pj = Proj(520, 820, 1.0, yaw=84, pitch=58)
    pitch = 120.0
    xs = [(i - 2.5) * pitch for i in range(6)]
    extrude(cv, pj, np.array([[-380, -40], [380, -40], [380, 40], [-380, 40]], float), -90, 90, hx("#4d5767"),
            alpha=0.5)
    age, idx = last_release(t, REL_SIX)
    # manifold to the stack
    man = pj(np.array(xs + [470.0]), np.full(7, -60.0), np.full(7, -150.0))
    pipe(cv, spline(man, 60), 36, hx("#7a8496"), glass=True)
    for i, x in enumerate(xs):
        on = 0.0
        for e_i, e in enumerate(REL_SIX):
            if FIRING[e_i % 6] == i + 1 and 0 <= t - e < 0.45:
                on = 1 - (t - e) / 0.45
        top = pj(x, -60, 0)
        cv.drawCircle(top[0], top[1], 46, paint(mix(hx("#2a3446"), AMBER, on)))
        cv.drawCircle(top[0], top[1], 46, paint(mix(hx("#6b7c96"), AMBER, on), stroke=3))
        if on > 0:
            cv.drawCircle(top[0], top[1], 70, paint(AMBER, a=0.5 * on, blur=16))
            runner = spline(pj(np.array([x, x]), np.array([-60, -60]), np.array([0.0, -150.0])), 10)
            flow(cv, runner, t, 500, 14, AMBER, r=5, a=on)
        draw_text(cv, str(i + 1), top[0], top[1] + 14, font("inter_blk", 40), INK, align="center")
    # stack + rings
    st = pj(470.0, -60.0, -150.0)
    cv.drawCircle(st[0], st[1], 34, paint(C_CHROME))
    if age < 0.45:
        for j in range(2):
            r = 40 + 380 * (age + 0.12 * j)
            cv.drawCircle(st[0], st[1], r, paint(INK, a=0.6 * (1 - age / 0.45), stroke=4))
    draw_text(cv, "FIRING ORDER 1 · 5 · 3 · 6 · 2 · 4", 540, 600, font("inter_xb", 28), MUTED, align="center",
              tracking=3, a=eout(lin(t, T_SIX, T_SIX + 0.4)))
    # pulse train (sound)
    x0, x1, y = 120.0, 960.0, 1250.0
    cv.drawLine(x0, y, x1, y, paint(hx("#3a4559"), stroke=2))
    for e in REL_SIX:
        dx = (t - e) * 260
        if 0 <= dx <= x1 - x0:
            xx = x1 - dx
            cv.drawLine(xx, y - 60, xx, y + 60, paint(AMBER, stroke=5))
            cv.drawLine(xx, y - 60, xx, y + 60, paint(AMBER, a=0.4, stroke=14, blur=6))
    draw_text(cv, "SOUND", x0, y - 90, font("inter_xb", 22), MUTED, tracking=3)
    cv.restore()
    brand.stamp(cv, t, "MACHINE GUN", T_MG2, dur=1.4, center=(540, 470))


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_WHAT + 0.6, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(T_PROB, "THE PROBLEM", RED), (T_NORMAL, "NORMAL: AIR SPRING", GREEN), (T_JAKE, "ENGINE BRAKE ON", AMBER),
           (T_RESULT, "THE RESULT", CYAN), (T_SOUND, "THE SOUND", AMBER)]
    txt, c = "JAKE BRAKE", AMBER
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    brand.note(cv, "ILLUSTRATION · ANIMATION SLOWED" if T_NORMAL < t < T_RESULT else "ILLUSTRATION", 0.9 * k, dy=-40)


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    # road (hook / x-ray push-in)
    k1 = scene_k(t, S_ROAD1, 0.0, 0.4)
    if k1 > 0:
        push = ease(lin(t, T_WHAT - 0.3, T_PROB))
        s_ = TR_S * (1 + 1.3 * push)
        cam = (560 + (540 - 768 * TR_S * 2.3 - 560) * push, 1130 + (950 + 81 * TR_S * 2.3 - 1130) * push, s_)
        draw_road(cv, t, k1, REL_HOOK, cam=cam, xray=eout(lin(t, T_JAKE1 - 0.3, T_JAKE1 + 0.5)))
    draw_brake(cv, t, scene_k(t, S_BRAKE))
    if scene_k(t, S_CYL) > 0:
        draw_cyl(cv, t, scene_k(t, S_CYL))
        draw_cyl_overlays(cv, t)
    k2 = scene_k(t, S_ROAD2)
    if k2 > 0:
        draw_road(cv, t, k2, REL_ROAD2)
    draw_six(cv, t, scene_k(t, S_SIX))
    k3 = scene_k(t, S_ROAD3) * kE
    if k3 > 0:
        sx = 480 - (t - T_SIGN) * 55
        draw_road(cv, t, k3, REL_ROAD3, sign_k=eout(lin(t, T_SIGN - 0.3, T_SIGN + 0.1)), sign_x=sx)
    draw_road_overlays(cv, t)
    draw_header(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_BANG
MUSIC_START = T_WHAT

SFX_PROMPTS = {
    "jake_barks": ("semi truck engine brake (jake brake) staccato exhaust bark, loud machine gun like rattle, "
                   "big diesel going downhill, exterior recording, no music, no voice", 3.0),
    "truck_pass": ("heavy semi truck rolling past at highway speed at night, tyre roar and wind, no horn, no music", 4.0),
    "air_blast": ("single sharp burst of compressed air escaping from a valve, short pneumatic blast, close", 0.8),
    "brake_hiss": ("hot truck drum brakes squealing and hissing under heavy load, no music", 2.0),
}


def sound():
    sfx = [(0.0, "jake_barks", 0.7), (2.8, "jake_barks", 0.6), (T_HOOK_OUT - 0.1, "whoosh_big", 0.5),
           (T_JAKE1, "impact", 0.35), (T_WHEEL, "brake_hiss", 0.45), (T_HOT, "impact", 0.45),
           (T_SPRING, "whoosh_down", 0.3), (T_OIL, "hiss", 0.25), (T_POPS, "clunk", 0.4),
           (T_BANG, "air_blast", 0.8), (T_BANG + 0.05, "impact", 0.5), (T_GONE, "whoosh_down", 0.3),
           (T_RESULT, "truck_pass", 0.45), (T_RESULT + 0.6, "jake_barks", 0.5),
           (T_MG2 - 0.4, "jake_barks", 0.7), (T_TOWNS + 0.3, "truck_pass", 0.35)]
    sfx += [(e, "tick", 0.12) for e in REL_SIX if e < T_MG2 - 0.4]
    return {"build": (T_JAKE, T_BANG), "drop": (T_BANG, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
