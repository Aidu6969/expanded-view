"""RB26 visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  ROAD    (hook, what)       night highway, three generic 90s coupes driving nose to tail, all tagged "276 HP";
                             the middle one (the GT-R) is singled out, camera pushes in, the hood x-rays to a straight six
  RULE    (rule)             two cards: STREET (gentlemen's agreement, 280 PS cap) vs RACING (Group A rulebook)
  SIZE    (size)             displacement bars: 2,568 cc x 1.7 = 4,366 cc, just under the 4,500 cc class line
  ENGINE  (throttle, turbos, pulses)
                             3/4 view of the inline six: plenum + six throttles on the far side, two exhaust manifolds
                             (cyl 1-2-3 / 4-5-6) and two parallel turbos on the near side; exhaust pulses timed from
                             a real 720-degree cycle in firing order 1-5-3-6-2-4; pulse timeline per turbo (240 deg)
  RACE    (key)              road 276 HP vs race ~550 PS bars
  RECORD  (result)           29 race tiles ticking to 29 / 29

Mechanism model:
  cycle angle c (deg, 720 per cycle). Cylinder n fires at FIRE[n] = 0,480,240,600,120,360 (n = 1..6, order
  1-5-3-6-2-4, 120 deg apart). Its exhaust valve opens ~180 deg later, so its pulse leaves at FIRE[n] + 180.
  Front turbo gets cylinders 1,2,3 (pulses at 180, 660, 420 -> every 240), rear turbo 4,5,6 (780=60, 300, 540 ->
  every 240). check_physics() asserts the spacing.
"""
import math

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, flow, path_len, pipe, point_at, rev, spline, wheel

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_CLAIMED = F("hook", "claimed")
T_SAME = F("hook", "same")
T_276 = F("hook", "two")
T_HP = F("hook", "horsepower.")
T_HIDING = F("hook", "hiding?")
T_GTR = F("hook", "gt-r")
T_WHAT = L("what")["start"]
T_HOOD = F("what", "hood.")
T_HOW = F("what", "here's")
T_RULE = L("rule")["start"]
T_NUMBER = F("rule", "number")
T_AGREE = F("rule", "agreement")
T_CARMAKERS = F("rule", "carmakers.")
T_BUT = F("rule", "but")
T_RULEBOOK = F("rule", "rulebook.")
T_RACING = F("rule", "racing.")
T_SIZE = L("size")["start"]
T_26 = F("size", "two")
T_MULT = F("size", "multiplied")
T_17 = F("size", "one")
T_UNDER = F("size", "under")
T_CLASS = F("size", "class.")
T_THR = L("throttle")["start"]
T_THROTTLES = F("throttle", "throttles,")
T_EVERY = F("throttle", "every")
T_TURBOS = L("turbos")["start"]
T_TWO_T = F("turbos", "two")
T_SIDE = F("turbos", "side")
T_FRONT = F("turbos", "front")
T_SPIN1 = F("turbos", "spin")
T_BACK = F("turbos", "back")
T_OTHER = F("turbos", "other.")
T_PULSES = L("pulses")["start"]
T_WHY3 = F("pulses", "why")
T_EVENLY = F("pulses", "evenly,")
T_240 = F("pulses", "two")
T_STEADY = F("pulses", "steady")
T_BEAT = F("pulses", "beat")
T_KEY = L("key")["start"]
T_SECRET = F("key", "secret.")
T_RACE = F("key", "race")
T_550 = F("key", "five")
T_TWICE = F("key", "twice")
T_RESULT = L("result")["start"]
T_WON = F("result", "won")
T_29 = F("result", "twenty")
T_GROUPA = F("result", "group")
T_JAPAN = F("result", "japan.")
T_OUTRO = L("outro")["start"]

S_ROAD = (0.0, T_RULE + 0.3)
S_RULE = (T_RULE - 0.1, T_SIZE + 0.3)
S_SIZE = (T_SIZE - 0.1, T_THR + 0.3)
S_ENGINE = (T_THR - 0.1, T_KEY + 0.4)
S_RACE = (T_KEY - 0.1, T_RESULT + 0.3)
S_RECORD = (T_RESULT - 0.1, T_TOTAL + 1.0)


def scene_k(t, s, fin=0.35, fout=0.35):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== engine model
CYL_X = [-275.0 + 110.0 * i for i in range(6)]        # cylinder 1 at the front (left on screen)
FIRE = {1: 0.0, 5: 120.0, 3: 240.0, 6: 360.0, 2: 480.0, 4: 600.0}
EVO = 180.0                                             # exhaust pulse leaves ~180 deg after firing
GROUP = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1}           # 0 = front turbo, 1 = rear turbo
TURBO_X = [-165.0, 165.0]


def pulse_angle(n):
    return (FIRE[n] + EVO) % 720.0


def check_physics():
    bad = []
    for g in (0, 1):
        angs = sorted(pulse_angle(n) for n in GROUP if GROUP[n] == g)
        gaps = [(angs[(i + 1) % 3] - angs[i]) % 720 for i in range(3)]
        if any(abs(x - 240.0) > 1e-6 for x in gaps):
            bad.append(f"group {g} not evenly spaced: {gaps}")
    if sorted(FIRE.values()) != [0.0, 120.0, 240.0, 360.0, 480.0, 600.0]:
        bad.append("firing not 120 deg apart")
    if abs(2568 * 1.7 - 4365.6) > 0.01 or 2568 * 1.7 >= 4500:
        bad.append("class arithmetic")
    return bad


assert not check_physics(), check_physics()

# crank speed (deg of cycle per second of video), slowed for the engine scene; integrated so angle is continuous
SPEED_KEYS = [(0.0, 900.0), (T_THR - 0.2, 900.0), (T_THR + 0.6, 200.0), (T_PULSES + 0.3, 200.0),
              (T_PULSES + 1.0, 150.0), (T_KEY - 0.3, 150.0), (T_KEY + 0.8, 1400.0), (T_TOTAL + 1, 1400.0)]


def _cyc_series():
    dt = 1.0 / 600
    ts = np.arange(0, T_TOTAL + 1.0, dt)
    sp = np.array([smooth(x, SPEED_KEYS) for x in ts])
    c = np.concatenate([[0.0], np.cumsum(sp[:-1]) * dt]) + 100.0
    return ts, c


_TS, _CS = _cyc_series()


def cyc(t):
    return float(np.interp(t, _TS, _CS))


def t_of_cyc(c):
    return float(np.interp(c, _CS, _TS))


def pulse_events(t0, t1):
    """(time, cylinder) of every exhaust pulse with t0 <= time <= t1."""
    c0, c1 = cyc(t0), cyc(t1)
    out = []
    for n in range(1, 7):
        a = pulse_angle(n)
        k = math.ceil((c0 - a) / 720.0)
        while a + 720 * k <= c1:
            out.append((t_of_cyc(a + 720 * k), n))
            k += 1
    return sorted(out)


def turbo_theta(t):
    # spin follows engine speed (parallel turbos both get the same flow); slowed with the animation
    return -cyc(t) * 0.035


# ================================================================== ROAD scene (hook)
HORIZON = 900
C_TIRE = hx("#15171b")
CAR_COLS = [hx("#c9ced6"), hx("#4a5363"), hx("#b23a35")]   # generic: white, gunmetal (the GT-R), red
CAR_PROF = np.array([[5, -30], [0, -62], [8, -92], [100, -98], [150, -132], [265, -134], [330, -98],
                     [440, -86], [462, -66], [458, -30]], float)
WHEEL_X = (85.0, 375.0)
WHEEL_R = 33.0


def car_proj(cx, cy, s):
    return Proj(cx, cy, s, yaw=76, pitch=9)


def draw_car(cv, pj, t, base, a=1.0, xray=0.0, glow=0.0):
    """Generic 90s two-door coupe facing +X (units cm, wheels on Y = 0). No badges, no logos."""
    zf, zb = -86.0, 86.0
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(a)))
    # far wheels
    for x in WHEEL_X:
        cyl3(cv, pj, (x, -WHEEL_R, zb - 30), (x, -WHEEL_R, zb), WHEEL_R, C_TIRE, n=32, edge=hx("#000000"))
    ca = 1 - 0.55 * xray
    extrude(cv, pj, CAR_PROF, zf, zb, base, alpha=ca, rim=RED if glow > 0 else None, rim_w=2.0, rim_glow=glow)
    # wing on the boot lid
    extrude(cv, pj, np.array([[8, -96], [48, -96], [48, -112], [8, -112]], float), zf + 8, zb - 8,
            shade(base, 0.8), alpha=ca)
    # side glass
    sw = pj(np.array([160, 262, 318, 152]), np.array([-126, -128, -101, -101]), np.full(4, zf - 1))
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad(tuple(sw[0]), tuple(sw[2]), [hx("#8fb3df"), hx("#0f1a2b")]))
    g.setAlphaf(0.9 * ca)
    cv.drawPath(poly_path(sw), g)
    # door line
    dl = pj(np.array([300, 300]), np.array([-96, -36]), np.full(2, zf - 1))
    cv.drawLine(*dl[0], *dl[1], paint(shade(base, 0.45), a=ca, stroke=2))
    # x-ray: inline six under the hood (longitudinal, cylinder 1 at the front)
    if xray > 0:
        hood = pj(np.array([335, 452, 452, 335]), np.array([-90, -78, -40, -40]), np.zeros(4))
        cv.drawPath(poly_path(hood), paint(hx("#06202c"), a=0.85 * xray))
        cv.drawPath(poly_path(hood), paint(CYAN, a=0.8 * xray, stroke=2))
        for i in range(6):
            x = 437 - 18 * i
            p0, p1 = pj(x, -80, 0), pj(x, -50, 0)
            ph = (t * 3.2 + [0, 4, 2, 5, 1, 3][i] / 6.0) % 1.0
            col_ = mix(CYAN, AMBER, max(0.0, 1 - ph * 3))
            cv.drawLine(*p0, *p1, paint(col_, a=xray, stroke=11 * pj.s, cap=skia.Paint.kRound_Cap))
            cv.drawLine(*p0, *p1, paint(col_, a=0.35 * xray, stroke=20 * pj.s, blur=4))
    # near wheels (spinning spokes)
    rot = -t * 9.0
    for x in WHEEL_X:
        cyl3(cv, pj, (x, -WHEEL_R, zf - 4), (x, -WHEEL_R, zf + 26), WHEEL_R, C_TIRE, n=40, edge=hx("#000000"))
        hub = pj(x, -WHEEL_R, zf - 5)
        r = 22 * pj.s
        cv.drawCircle(*hub, r, paint(hx("#aeb7c4")))
        for k in range(5):
            an = rot + k * 2 * math.pi / 5
            cv.drawLine(hub[0], hub[1], hub[0] + r * math.cos(an), hub[1] + r * math.sin(an),
                        paint(hx("#3b4352"), stroke=3.2 * pj.s / 0.55))
        cv.drawCircle(*hub, 5 * pj.s / 0.55, paint(hx("#3b4352")))
    # lights
    hl = pj(458, -60, zf + 20)
    look.bloom(cv, hl[0], hl[1], 8 * pj.s / 0.55, hx("#fff4d6"), a=0.95)
    tlp = pj(2, -70, zf + 18)
    look.bloom(cv, tlp[0], tlp[1], 6 * pj.s / 0.55, RED, a=0.85)
    if a < 1:
        cv.restore()
    return hl


CAR_LEN_PX = 462 * 0.56
ROAD_Y = 1080.0


def road_cam(t):
    """(scale, focus x on screen, y of the road) - pushes in on the middle car during 'what'."""
    k = ease(lin(t, T_WHAT - 0.2, T_HOW + 0.2))
    s = 0.66 + (1.2 - 0.66) * k
    return s, k


def draw_road(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, HORIZON, t=t)
    look.mountains(cv, HORIZON, offset=t * 60)
    look.haze(cv, HORIZON - 240, HORIZON + 60, a=0.10)
    s, kz = road_cam(t)
    # road slab + moving dashes
    road_top = ROAD_Y - 60
    rp = skia.Paint()
    rp.setShader(lin_grad((0, road_top), (0, H), [hx("#1b1f27"), hx("#0b0d11")]))
    cv.drawRect(skia.Rect.MakeLTRB(0, road_top, W, H), rp)
    cv.drawRect(skia.Rect.MakeLTRB(0, road_top, W, road_top + 8), paint(hx("#3a4250")))
    spd = 700.0 * s / 0.66
    off = (t * spd) % 300
    for i in range(-1, 6):
        x = i * 300 - off
        cv.drawRect(skia.Rect.MakeXYWH(x, ROAD_Y + 150, 150, 12), paint(hx("#d8d2a8"), a=0.5))
    # street lights passing (parallax)
    off2 = (t * spd * 0.55) % 520
    for i in range(-1, 4):
        x = i * 520 - off2 + 260
        cv.drawLine(x, road_top, x, road_top - 330, paint(hx("#2e3542"), stroke=8))
        look.bloom(cv, x + 40, road_top - 330, 12, hx("#ffd9a0"), a=0.9)
        look.beam(cv, (x + 40, road_top - 325), (x + 40, road_top + 10), 6, 150, c=hx("#ffd9a0"), a=0.10)
    # three cars, nose to tail; the camera centres on the middle one (index 1)
    gap = 30.0
    xray = eout(lin(t, T_HOOD - 0.3, T_HOOD + 0.5))
    single = eout(lin(t, T_HIDING - 0.5, T_HIDING + 0.1))
    mid_x0 = 540 - (231 + (395 - 231) * kz) * s * 0.97
    for i in (0, 1, 2):
        x0 = mid_x0 + (i - 1) * (462 * s * 0.97 + gap * s / 0.66)
        bob = 1.5 * math.sin(t * 7 + i)
        pj = car_proj(x0, ROAD_Y + bob, s)
        look.soft_shadow(cv, x0 + 230 * s, ROAD_Y + 4, 520 * s, 40 * s / 0.66, a=0.6)
        a_ = 1.0 if i == 1 else 1 - 0.65 * single
        hl = draw_car(cv, pj, t, CAR_COLS[i], a=a_, xray=xray if i == 1 else 0.0,
                      glow=0.6 * single * (1 - kz) if i == 1 else 0.0)
        look.beam(cv, hl, (hl[0] + 420 * s / 0.66, hl[1] + 40), 8, 90, a=0.22 * a_)
        look.wet_reflection(cv, hl[0], ROAD_Y + 10, ROAD_Y + 180, 18, hx("#fff1c9"), a=0.25 * a_)
        # "276 HP" tags pop in one by one
        kt = eback(lin(t, T_SAME + 0.25 * i - 0.1, T_SAME + 0.25 * i + 0.25)) * (1 - kz)
        if kt > 0:
            top = pj(230, -150, 0)
            hot = i == 1 and t > T_HIDING - 0.3
            pill(cv, top[0], top[1] - 30, "276 HP?" if hot else "276 HP", font("inter_blk", 30), INK,
                 border=RED if hot else MUTED, a=clamp(kt) * a_, align="center", tracking=2)
    look.vignette(cv, 0.5)
    cv.restore()


def draw_road_overlays(cv, t):
    k = win(t, T_HIDING - 0.2, T_WHAT + 0.4, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1240, "GT-R", font("inter_blk", 40), INK, border=RED, a=k, align="center", tracking=6,
             dot=RED)
    k = win(t, T_HOOD - 0.1, T_RULE + 0.2, 0.25, 0.3)
    if k > 0:
        brand.chips(cv, k, 1320, [("STRAIGHT SIX", eout(lin(t, T_HOOD, T_HOOD + 0.3))),
                                  ("TWIN TURBO", eout(lin(t, T_HOOD + 0.3, T_HOOD + 0.6))),
                                  ("2.6 L", eout(lin(t, T_HOW, T_HOW + 0.3)))], center=True)


# ================================================================== RULE scene
def draw_rule(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    # card 1: the street number
    k1 = eout(lin(t, T_RULE - 0.1, T_RULE + 0.4))
    dim1 = 0.45 * eout(lin(t, T_BUT, T_BUT + 0.5))
    y1 = 470 + 40 * (1 - k1)
    brand.panel(cv, 110, y1, 860, 330, "STREET", CYAN, a=k1 * (1 - dim1))
    draw_text(cv, "GENTLEMEN'S AGREEMENT · 1989", 146, y1 + 120, font("inter_xb", 28), MUTED, a=k1 * (1 - dim1),
              tracking=2)
    draw_text(cv, "MAX 280 PS", 146, y1 + 225, font("pop_b", 92), INK, a=k1 * (1 - dim1))
    draw_text(cv, "= 276 HP", 146, y1 + 290, font("inter_xb", 36), CYAN, a=k1 * (1 - dim1), tracking=2)
    # handshake-free "seal": a ring of dots that closes as the carmakers are named
    kc = eout(lin(t, T_AGREE - 0.1, T_CARMAKERS + 0.3))
    cx, cy = 820, y1 + 210
    for j in range(7):
        a_ = kc * clamp(kc * 7 - j)
        an = -math.pi / 2 + j * 2 * math.pi / 7
        cv.drawCircle(cx + 70 * math.cos(an), cy + 70 * math.sin(an), 13, paint(CYAN, a=a_ * (1 - dim1)))
    # card 2: the racing rulebook
    k2 = eback(lin(t, T_BUT + 0.1, T_BUT + 0.55))
    if k2 > 0:
        y2 = 860 + 60 * (1 - clamp(k2))
        brand.panel(cv, 110, y2, 860, 380, "RACING", RED, a=clamp(k2))
        draw_text(cv, "GROUP A RULEBOOK", 146, y2 + 130, font("inter_xb", 30), MUTED, a=clamp(k2), tracking=3)
        # chequered flag
        fx, fy, sz = 640, y2 + 160, 34
        for r in range(5):
            for c_ in range(8):
                wave = 8 * math.sin(t * 5 + c_ * 0.7)
                colr = INK if (r + c_) % 2 == 0 else hx("#151a24")
                cv.drawRect(skia.Rect.MakeXYWH(fx + c_ * sz, fy + r * sz + wave, sz, sz), paint(colr, a=clamp(k2)))
        kr = eout(lin(t, T_RACING - 0.1, T_RACING + 0.3))
        draw_text(cv, "BUILT TO WIN", 146, y2 + 250, font("pop_b", 64), INK, a=kr)
        draw_text(cv, "NOT TO MATCH 276", 146, y2 + 315, font("inter_xb", 32), RED, a=kr, tracking=2)
    cv.restore()


# ================================================================== SIZE scene
SX0, SX1 = 150.0, 930.0          # 0 .. 5,000 cc


def cc_x(cc):
    return SX0 + (SX1 - SX0) * cc / 5000.0


def draw_size(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    k_eq = eout(lin(t, T_26 - 0.2, T_26 + 0.3))
    draw_text(cv, "2,568 cc", 540, 560, font("pop_b", 120), INK, a=k_eq, align="center")
    draw_text(cv, "TWIN TURBO STRAIGHT SIX", 540, 620, font("inter_xb", 28), MUTED, a=k_eq, align="center", tracking=3)
    km = eout(lin(t, T_17 - 0.2, T_17 + 0.3))
    if km > 0:
        draw_text(cv, "× 1.7 FOR TURBO", 540, 700, font("inter_xb", 40), AMBER, a=km, align="center", tracking=3)
    # bars
    y_a, y_b, bh = 900.0, 1040.0, 70.0
    grow_a = eout(lin(t, T_26, T_26 + 0.7))
    grow_b = ease(lin(t, T_17 + 0.1, T_UNDER + 0.2))
    cc_b = 2568 + (4366 - 2568) * grow_b
    # class lines
    kl = eout(lin(t, T_MULT - 0.2, T_MULT + 0.4))
    for cc_, lab, c_ in ((4000, "4.0 L CLASS", MUTED), (4500, "4.5 L CLASS LIMIT", RED)):
        x = cc_x(cc_)
        p = paint(c_, a=kl, stroke=3)
        p.setPathEffect(skia.DashPathEffect.Make([12, 8], 0))
        cv.drawLine(x, y_a - 20, x, y_b + bh + 40, p)
        draw_text(cv, lab, x + (0 if cc_ == 4000 else 10), y_a - (75 if cc_ == 4000 else 35), font("inter_xb", 24),
                  c_, a=kl, align="center" if cc_ == 4000 else "right", tracking=2)
    for (y, cc_, c_, lab, kk) in ((y_a, 2568 * grow_a, CYAN, "REAL", grow_a), (y_b, cc_b, RED, "COUNTS AS", km)):
        if kk <= 0:
            continue
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(SX0, y, max(1.0, cc_x(cc_) - SX0), bh), 14, 14)
        cv.drawRRect(r, paint(c_, a=0.35 * kk, blur=14))
        cv.drawRRect(r, paint(shade(c_, 0.55), a=kk))
        cv.drawRRect(r, paint(c_, a=kk, stroke=3))
        draw_text(cv, lab, SX0 + 20, y + 46, font("inter_xb", 28), INK, a=kk, tracking=2)
        draw_text(cv, f"{int(round(cc_)):,} cc", cc_x(cc_) - 18, y + 46, font("inter_blk", 30), INK, a=kk,
                  align="right")
    # axis
    cv.drawLine(SX0, y_b + bh + 40, SX1, y_b + bh + 40, paint(hx("#3a4559"), a=k, stroke=2))
    for cc_ in range(0, 5001, 1000):
        draw_text(cv, f"{cc_ // 1000} L", cc_x(cc_), y_b + bh + 80, font("inter_sb", 22), MUTED, align="center")
    ku = eout(lin(t, T_UNDER - 0.1, T_UNDER + 0.3))
    if ku > 0:
        x = cc_x(4366)
        cv.drawLine(x + 8, y_b + bh / 2, cc_x(4500) - 6, y_b + bh / 2, paint(GREEN, a=ku, stroke=4))
        check_icon(cv, (x + cc_x(4500)) / 2, y_b - 26, 30, GREEN, a=ku)
    cv.restore()
    brand.stamp(cv, t, "JUST UNDER", T_UNDER, dur=1.4, center=(540, 1290), color=GREEN, bg=hx("#06281a"))


# ================================================================== ENGINE scene
def eng_proj(t):
    k = ease(lin(t, T_THR - 0.3, T_THR + 1.0))
    s = 0.84 + 0.06 * k
    return Proj(525, 900, s, yaw=70 + 4 * math.sin(t * 0.2), pitch=34)


BLK_PROF = np.array([[-330, 0], [330, 0], [330, -160], [-330, -160]], float)
HEAD_PROF = np.array([[-325, -160], [325, -160], [325, -230], [-325, -230]], float)


def turbo_path(n):
    """Exhaust path (model coords) from cylinder n's port to its turbo's turbine."""
    x = CYL_X[n - 1]
    xt = TURBO_X[GROUP[n]]
    return np.array([[x, -195, -82], [x, -175, -125], [x * 0.55 + xt * 0.45, -140, -160],
                     [xt, -112, -185], [xt, -80, -215]], float)


def draw_engine(cv, t, k):
    if k <= 0:
        return
    pj = eng_proj(t)
    c = cyc(t)
    cv.saveLayerAlpha(None, int(255 * k))
    k_thr = eout(lin(t, T_THROTTLES - 0.3, T_THROTTLES + 0.4))
    k_tur = eout(lin(t, T_TWO_T - 0.2, T_TWO_T + 0.5))
    hi_f = win(t, T_FRONT - 0.1, T_BACK + 0.1, 0.2, 0.25)
    hi_b = win(t, T_BACK - 0.1, T_OTHER + 0.6, 0.2, 0.3)
    # ---- far side: plenum + throttles + runners (z > 0)
    plen = np.array([[-300, -300], [300, -300], [300, -250], [-300, -250]], float)
    extrude(cv, pj, plen, 230, 290, hx("#5b6678"), alpha=0.35 + 0.55 * k_thr)
    air_on = clamp(k_thr)
    for i, x in enumerate(CYL_X):
        # runner from throttle to the head (far side)
        run = spline(pj(np.array([x, x, x]), np.array([-262, -235, -205]), np.array([215, 150, 82])), 20)
        pipe(cv, run, 30 * pj.s, hx("#7a8496"), glass=True)
        if air_on > 0.05:
            flow(cv, run, t, 160, 16, CYAN, r=4.5, a=air_on, offset=i * 7)
        # throttle body + butterfly plate
        tb_c = mix(hx("#9aa6b8"), CYAN, 0.6 * win(t, T_THROTTLES - 0.2, T_TURBOS, 0.2, 0.4))
        cyl3(cv, pj, (x, -265, 245), (x, -265, 205), 24, tb_c, n=28)
        open_ = 0.25 + 0.6 * k_thr
        q0 = pj(x - 20 * math.cos(open_ * 1.2), -265 - 20 * math.sin(open_ * 1.2) * 0.2, 205)
        q1 = pj(x + 20 * math.cos(open_ * 1.2), -265 + 20 * math.sin(open_ * 1.2) * 0.2, 205)
        cv.drawLine(*q0, *q1, paint(INK, a=0.9 * k_thr, stroke=3))
    # ---- block + head (glass), cylinders
    extrude(cv, pj, BLK_PROF, -80, 80, hx("#5b6474"), alpha=0.55)
    extrude(cv, pj, HEAD_PROF, -78, 78, hx("#6f7a8c"), alpha=0.55)
    events = pulse_events(t - 0.6, t)
    for i, x in enumerate(CYL_X):
        n = i + 1
        on = 0.0
        for te, ne in events:
            if ne == n:
                on = max(on, 1 - (t - te) / 0.45)
        on = clamp(on) * k_tur
        grp_hi = hi_f if GROUP[n] == 0 else hi_b
        rim_c = mix(mix(hx("#9fb0c8"), YEL, grp_hi), AMBER, on)
        top = hcircle(pj, x, -231, 0, 40)
        cv.drawPath(poly_path(top), paint(mix(hx("#26303f"), AMBER, 0.7 * on)))
        cv.drawPath(poly_path(top), paint(rim_c, stroke=3 + 2 * grp_hi))
        if on > 0:
            q = pj(x, -231, 0)
            cv.drawCircle(q[0], q[1], 60 * pj.s, paint(AMBER, a=0.45 * on, blur=18))
        q = pj(x, -231, 0)
        draw_text(cv, str(n), q[0], q[1] + 13, font("inter_blk", 34), INK, align="center")
    # ---- near side: exhaust manifolds + turbos
    for n in range(1, 7):
        path = spline(pj(*turbo_path(n).T), 30)
        grp_hi = hi_f if GROUP[n] == 0 else hi_b
        pipe(cv, path, 24 * pj.s, mix(hx("#8a7a6e"), YEL, 0.5 * grp_hi), a=max(0.25, k_tur), glass=True)
        for te, ne in events:
            if ne != n:
                continue
            age = (t - te) / 0.55
            if 0 <= age <= 1:
                p, _ = point_at(path, path_len(path) * age)
                cv.drawCircle(p[0], p[1], 15 * pj.s, paint(AMBER, a=0.9 * k_tur * (1 - 0.4 * age)))
                cv.drawCircle(p[0], p[1], 34 * pj.s, paint(AMBER, a=0.5 * k_tur * (1 - age), blur=12))
    th = turbo_theta(t)
    for g, xt in enumerate(TURBO_X):
        if k_tur <= 0:
            break
        grp_hi = hi_f if g == 0 else hi_b
        cv.saveLayerAlpha(None, int(255 * k_tur))
        cxy = (xt, -60.0)
        rev(cv, pj, "z", cxy, [-205, -215, -240, -262, -270], [52, 78, 92, 80, 48], hx("#5a4a3e"), fill_a=0.45,
            edge=mix(hx("#8a7262"), YEL, grp_hi), edge_w=1.5 + 2 * grp_hi, glow=grp_hi)
        wheel(cv, pj, "z", cxy, -272.0, -228.0, lambda s_: 10 + 30 * s_ ** 2, lambda s_: 46 + 12 * s_, 11, th,
              mix(hx("#6c6866"), hx("#c0552a"), 0.3), blade=hx("#9a8f88"), twist=-0.5, bp_r=50,
              rim=AMBER, rim_a=0.5, blur=2 if t > T_KEY else 0)
        cv.restore()
    # labels
    brand.label(cv, t, "6 THROTTLES", tuple(pj(CYL_X[5], -265, 245)), (930, 420), CYAN, T_THROTTLES - 0.1,
                T_TURBOS + 0.2, align="right")
    brand.label(cv, t, "TURBO 1", tuple(pj(TURBO_X[0], -60, -272)), (90, 1080), YEL, T_FRONT - 0.1, T_PULSES)
    brand.label(cv, t, "TURBO 2", tuple(pj(TURBO_X[1], -60, -272)), (930, 1080), YEL, T_BACK - 0.1, T_PULSES,
                align="right")
    cv.restore()


TL_X0, TL_X1 = 230.0, 920.0


def draw_timeline(cv, t, k):
    kk = k * win(t, T_WHY3 - 0.2, T_KEY + 0.2, 0.3, 0.3)
    if kk <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * kk))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(80, 1100, 920, 285), 22, 22)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.88))
    cv.drawRRect(rr, paint(hx("#2a3446"), stroke=2))
    draw_text(cv, "EXHAUST PULSES · ONE 720° CYCLE", 110, 1136, font("inter_xb", 22), MUTED, tracking=3)
    c = cyc(t)
    ph = c % 720.0
    rows = [(0, 1210.0, "TURBO 1"), (1, 1320.0, "TURBO 2")]
    for g, y, lab in rows:
        draw_text(cv, lab, 110, y + 9, font("inter_xb", 24), YEL)
        cv.drawLine(TL_X0, y, TL_X1, y, paint(hx("#3a4559"), stroke=2))
        for n in range(1, 7):
            if GROUP[n] != g:
                continue
            a = pulse_angle(n)
            x = TL_X0 + (TL_X1 - TL_X0) * a / 720.0
            lit = 1.0 if (t > T_EVENLY or (ph - a) % 720 < 360) else 0.35
            cv.drawLine(x, y - 30, x, y + 30, paint(AMBER, a=lit, stroke=6))
            cv.drawLine(x, y - 30, x, y + 30, paint(AMBER, a=0.4 * lit, stroke=16, blur=6))
            draw_text(cv, str(n), x, y - 38, font("inter_blk", 24), INK, a=lit, align="center")
    # playhead
    x = TL_X0 + (TL_X1 - TL_X0) * ph / 720.0
    cv.drawLine(x, 1165, x, 1350, paint(INK, a=0.7, stroke=2))
    # 240 deg brackets
    kb = eout(lin(t, T_240 - 0.2, T_240 + 0.4))
    if kb > 0:
        for g, y, _ in rows:
            angs = sorted(pulse_angle(n) for n in GROUP if GROUP[n] == g)
            for a0, a1 in zip(angs, angs[1:]):
                x0 = TL_X0 + (TL_X1 - TL_X0) * a0 / 720.0 + 8
                x1 = TL_X0 + (TL_X1 - TL_X0) * a1 / 720.0 - 8
                cv.drawLine(x0, y + 20, x1, y + 20, paint(GREEN, a=kb, stroke=3))
                draw_text(cv, "240°", (x0 + x1) / 2, y + 45, font("inter_xb", 22), GREEN, a=kb, align="center")
    cv.restore()


def draw_engine_overlays(cv, t):
    k = win(t, T_EVERY - 0.2, T_TURBOS + 0.2, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1220, "ONE THROTTLE PER CYLINDER", font("inter_xb", 30), INK, border=CYAN, a=k,
             align="center", tracking=2, dot=CYAN)
    k = win(t, T_SIDE - 0.2, T_FRONT, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1220, "PARALLEL TWIN TURBO", font("inter_xb", 30), INK, border=AMBER, a=k, align="center",
             tracking=2, dot=AMBER)
    k = win(t, T_FRONT - 0.1, T_PULSES, 0.2, 0.3)
    if k > 0:
        kb = eout(lin(t, T_BACK - 0.1, T_BACK + 0.3))
        brand.chips(cv, k, 1220, [("CYL 1 · 2 · 3 → TURBO 1", eout(lin(t, T_SPIN1 - 0.1, T_SPIN1 + 0.3))),
                                  ], center=True)
        if kb > 0:
            brand.chips(cv, kb * k, 1300, [("CYL 4 · 5 · 6 → TURBO 2", eout(lin(t, T_OTHER - 0.2, T_OTHER + 0.2)))],
                        center=True)
    brand.stamp(cv, t, "EVERY 240°", T_240, dur=1.6, center=(540, 420), color=GREEN, bg=hx("#06281a"))


# ================================================================== RACE scene (key)
def draw_race(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    base_y, top_y = 1250.0, 520.0
    hmax = base_y - top_y
    k_road = eout(lin(t, T_KEY - 0.1, T_KEY + 0.4))
    grow = ease(lin(t, T_RACE - 0.1, T_550 + 0.5))
    val = 550 * grow
    for x, v, c_, lab, kk in ((300, 276, CYAN, "ROAD CAR", k_road), (660, val, RED, "RACE TRIM", eout(lin(t, T_RACE - 0.2, T_RACE + 0.2)))):
        if kk <= 0:
            continue
        h = hmax * v / 600.0
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 110, base_y - h, 220, h), 18, 18)
        cv.drawRRect(r, paint(c_, a=0.35 * kk, blur=18))
        g = skia.Paint(AntiAlias=True)
        g.setShader(lin_grad((0, base_y - h), (0, base_y), [shade(c_, 0.9), shade(c_, 0.35)]))
        g.setAlphaf(kk)
        cv.drawRRect(r, g)
        cv.drawRRect(r, paint(c_, a=kk, stroke=3))
        num = "276 HP" if c_ == CYAN else "≈550 PS"
        ka = kk if c_ == CYAN else eout(lin(t, T_550 - 0.1, T_550 + 0.3))
        draw_text(cv, num, x, base_y - h - 26, font("pop_b", 64), INK, a=ka, align="center")
        draw_text(cv, lab, x, base_y + 50, font("inter_xb", 30), c_, a=kk, align="center", tracking=3)
    cv.drawLine(150, base_y, 930, base_y, paint(hx("#3a4559"), a=k, stroke=3))
    # the official line
    kd = eout(lin(t, T_TWICE - 0.4, T_TWICE))
    y276 = base_y - hmax * 276 / 600.0
    p = paint(CYAN, a=0.7 * k_road, stroke=3)
    p.setPathEffect(skia.DashPathEffect.Make([12, 8], 0))
    cv.drawLine(150, y276, 930, y276, p)
    draw_text(cv, "OFFICIAL", 930, y276 - 12, font("inter_xb", 22), CYAN, a=k_road, align="right", tracking=3)
    cv.restore()
    brand.stamp(cv, t, "× 2", T_TWICE, dur=1.6, center=(540, 420))


# ================================================================== RECORD scene (result)
def draw_record(cv, t, k):
    k *= 1 - current.ending_k(t)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    draw_text(cv, "GROUP A · JAPAN", 540, 500, font("inter_xb", 34), MUTED, align="center", tracking=5,
              a=eout(lin(t, T_RESULT - 0.1, T_RESULT + 0.4)))
    t0, t1 = T_WON, T_JAPAN
    n_on = 29 * ease(lin(t, t0, t1))
    cols, sz, gp = 6, 104, 20
    x0 = 540 - (cols * sz + (cols - 1) * gp) / 2
    for i in range(29):
        r, c_ = divmod(i, cols)
        if r == 4:
            x = 540 - (5 * sz + 4 * gp) / 2 + c_ * (sz + gp)
        else:
            x = x0 + c_ * (sz + gp)
        y = 560 + r * (sz + gp)
        on = clamp(n_on - i)
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, sz, sz), 18, 18)
        if on > 0:
            cv.drawRRect(rr, paint(GREEN, a=0.35 * on, blur=12))
        cv.drawRRect(rr, paint(mix(hx("#141b28"), hx("#0b3a24"), on)))
        cv.drawRRect(rr, paint(mix(hx("#2a3446"), GREEN, on), stroke=3))
        if on > 0:
            check_icon(cv, x + sz / 2, y + sz / 2, 44, GREEN, a=on, prog=on)
    num = int(math.floor(n_on + 1e-6))
    draw_text(cv, f"{num} / 29 WINS", 540, 1270, font("pop_b", 84), INK, align="center",
              a=eout(lin(t, T_WON - 0.2, T_WON + 0.2)))
    cv.restore()


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_RULE + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(T_RULE, "THE NUMBER", CYAN), (T_SIZE, "THE RULEBOOK", RED), (T_THR, "INTAKE", CYAN),
           (T_TURBOS, "TWIN TURBOS", AMBER), (T_PULSES, "EXHAUST PULSES", AMBER), (T_KEY, "THE SECRET", RED),
           (T_RESULT, "THE RECORD", GREEN)]
    txt, c = "RB26", RED
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    eng = T_THR < t < T_KEY
    brand.note(cv, "ILLUSTRATION · ANIMATION SLOWED" if eng else "ILLUSTRATION", 0.9 * k, dy=-40)


# ================================================================== draw
def draw(cv, t):
    draw_road(cv, t, scene_k(t, S_ROAD, 0.0, 0.4))
    draw_road_overlays(cv, t)
    draw_rule(cv, t, scene_k(t, S_RULE))
    draw_size(cv, t, scene_k(t, S_SIZE))
    ke = scene_k(t, S_ENGINE)
    if ke > 0:
        draw_engine(cv, t, ke)
        draw_timeline(cv, t, ke)
        draw_engine_overlays(cv, t)
    draw_race(cv, t, scene_k(t, S_RACE))
    draw_record(cv, t, scene_k(t, S_RECORD))
    draw_header(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_550
MUSIC_START = T_WHAT


def sound():
    sfx = [(0.0, "whoosh_big", 0.45), (T_SAME, "tick", 0.3), (T_SAME + 0.25, "tick", 0.3), (T_SAME + 0.5, "tick", 0.3),
           (T_HIDING, "impact", 0.45), (T_HOOK_OUT - 0.1, "whoosh_big", 0.5), (T_HOOD, "whoosh_up", 0.35),
           (T_RULE - 0.2, "whoosh_down", 0.35), (T_BUT + 0.1, "clunk", 0.4), (T_RACING, "impact", 0.4),
           (T_SIZE - 0.2, "whoosh_up", 0.3), (T_17, "tick", 0.4), (T_UNDER, "clunk", 0.45),
           (T_THR - 0.2, "whoosh_down", 0.35), (T_THROTTLES, "hiss", 0.3), (T_TWO_T, "spool", 0.45),
           (T_FRONT, "tick", 0.35), (T_BACK, "tick", 0.35), (T_240, "clunk", 0.4),
           (T_KEY - 0.2, "whoosh_up", 0.35), (T_550, "spool", 0.5), (T_TWICE, "impact", 0.55),
           (T_RESULT - 0.2, "whoosh_down", 0.3)]
    sfx += [(te, "tick", 0.1) for te, _ in pulse_events(T_PULSES, T_KEY - 0.3)]
    sfx += [(T_WON + (T_JAPAN - T_WON) * i / 29, "tick", 0.08) for i in range(0, 29, 2)]
    return {"build": (T_PULSES, T_550), "drop": (T_550, T_OUTRO - 0.05), "sfx": sfx}
