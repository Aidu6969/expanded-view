"""Why electric cars make fake sounds: visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  STREET  (hook, what)       night city crossing; a generic EV creeps up to a pedestrian on a phone; hum rings
                             leave the front bumper; camera pushes in and the bumper turns to glass (speaker)
  COMPARE (problem)          gas engine (pistons, exhaust pulses, big sound rings) vs electric motor (spinning
                             rotor, almost no rings) with sound-level meters
  DATA    (data)             NHTSA 2017: pedestrian-crash odds in low-speed moves, gas 1.0 vs hybrid/EV 1.52
  XRAY    (law)              glass car: speed -> control unit -> speaker in the front bumper; speaker cutaway
                             (magnet, coil, cone moving); ring size and level bar follow speed (louder with speed)
  GRAPH   (rehook, key)      sound heard by people vs speed: speaker (amber) keeps the car above the "audible"
                             line up to 30 km/h, then switches off; tyre + wind noise (cyan) rises and crosses
                             the line at 30 km/h (the legal crossover speed, US)
  STREET2 (key payoff)       car passes at speed, tyre noise rings, speaker OFF; the pedestrian looks up
  TWIST   (twist)            performance EV: speaker counts (8 inside, 2 outside), virtual tach with fake gear
                             shifts and the motor power briefly cut at each shift
  STREET3 (outro)            back on the street, hum rings at walking pace

Sound: the AVAS hum, the gas idle, motor whine, tyre roar and the fake engine are synthesized here (sound()) and
written to episodes/ev-fake-sound/sfx/; the fake engine clip follows the same RPM/shift model as the tach.
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3, flow, pipe, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_HUM = F("hook", "hum")
T_WHO = F("hook", "who")
T_NOT = L("what")["start"]
T_HERES = F("what", "here's")
T_PROB = L("problem")["start"]
T_GAS = F("problem", "gas")
T_ELEC = F("problem", "electric")
T_SILENT = F("problem", "silent,")
T_PEOPLE = F("problem", "people")
T_DATA = L("data")["start"]
T_RESEARCH = F("data", "researchers")
T_HYB = F("data", "hybrids")
T_FIFTY = F("data", "fifty")
T_BACK = F("data", "backing")
T_TURN = F("data", "turning.")
T_LAW = L("law")["start"]
T_LAWW = F("law", "law.")
T_READS = F("law", "reads")
T_PLAYS = F("law", "plays")
T_SPEAKER = F("law", "speaker")
T_BUMPER = F("law", "bumper.")
T_FASTER = F("law", "faster")
T_LOUDER = F("law", "louder")
T_RE = L("rehook")["start"]
T_NINETEEN = F("rehook", "nineteen")
T_QUIET = F("rehook", "quiet.")
T_WHY = F("rehook", "why?")
T_KEY = L("key")["start"]
T_TIRES = F("key", "tires")
T_WIND = F("key", "wind")
T_LOUD = F("key", "loud")
T_NEVER = F("key", "never")
T_PEOPLE2 = F("key", "people")
T_TW = L("twist")["start"]
T_DRIVER = F("twist", "driver")
T_IONIQ = F("twist", "ioniq")
T_TEN = F("twist", "ten")
T_CUTS = F("twist", "cuts")
T_SHIFT = F("twist", "shift.")
T_OUTRO = L("outro")["start"]

S_STREET1 = (0.0, T_PROB + 0.3)
S_COMPARE = (T_PROB - 0.1, T_DATA + 0.3)
S_DATA = (T_DATA - 0.1, T_LAW + 0.3)
S_XRAY = (T_LAW - 0.1, T_RE + 0.3)
S_GRAPH = (T_RE - 0.1, T_NEVER + 0.25)
S_STREET2 = (T_NEVER - 0.15, T_TW + 0.3)
S_TWIST = (T_TW - 0.1, T_OUTRO + 0.3)
S_STREET3 = (T_OUTRO - 0.1, T_TOTAL + 1)


def scene_k(t, s, fin=0.35, fout=0.35):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== the car (generic EV, no badges). Units: cm.
CAR_BODY = np.array([[0, -40], [2, -78], [22, -100], [125, -112], [178, -147], [300, -150], [362, -118],
                     [452, -102], [471, -84], [475, -44], [462, -28], [12, -28]], float)
CAR_WIN = np.array([[140, -111], [184, -142], [296, -144], [345, -116]], float)
WHEELS = (95.0, 380.0)
WR = 34.0
ZF, ZB = -88.0, 88.0
SPK = (458.0, -52.0, -20.0)          # speaker behind the front bumper
C_BODY = hx("#9aa8bd")
C_TIRE = hx("#15181d")
C_RIM = hx("#c9d2df")


def car_proj(x0, ground_y, s):
    """x0 = screen x of the car's rear, ground_y = screen y where the tyres touch."""
    return Proj(x0, ground_y, s, yaw=80, pitch=8)


def draw_car(cv, pj, t, roll=0.0, xray=0.0, a=1.0, glow_spk=0.0):
    """roll = distance travelled (cm) for wheel rotation. Returns screen point of the speaker."""
    cv.saveLayerAlpha(None, int(255 * a))
    # far wheels
    for x in WHEELS:
        cyl3(cv, pj, (x, -WR, ZB - 30), (x, -WR, ZB - 4), WR, C_TIRE, n=36, edge=hx("#000000"))
    ba = 1 - 0.62 * xray
    extrude(cv, pj, CAR_BODY, ZF, ZB, C_BODY, alpha=ba, rim=CYAN if xray > 0.05 else None, rim_w=1.6,
            rim_glow=0.3 * xray)
    # glass
    poly = pj.pts(CAR_WIN, ZF - 1)
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad(tuple(poly[1]), tuple(poly[3]), [hx("#86a9d8"), hx("#101b2e")]))
    g.setAlphaf(0.92 * ba)
    cv.drawPath(poly_path(poly), g)
    # door line + handle
    d0, d1 = pj(258, -112, ZF - 1), pj(258, -40, ZF - 1)
    cv.drawLine(*d0, *d1, paint(shade(C_BODY, 0.55), a=ba, stroke=2))
    h0, h1 = pj(215, -92, ZF - 1), pj(240, -92, ZF - 1)
    cv.drawLine(*h0, *h1, paint(shade(C_BODY, 0.45), a=ba, stroke=4, cap=skia.Paint.kRound_Cap))
    # light bar front + rear
    hl0, hl1 = pj(452, -92, ZF + 6), pj(474, -84, ZF + 30)
    cv.drawLine(*hl0, *hl1, paint(hx("#eaf6ff"), stroke=4, cap=skia.Paint.kRound_Cap))
    hl = pj(472, -86, ZF + 20)
    look.bloom(cv, hl[0], hl[1], 7 * pj.s, hx("#eaf6ff"), a=0.9)
    tlp = pj(2, -76, ZF + 20)
    look.bloom(cv, tlp[0], tlp[1], 5 * pj.s, RED, a=0.8)
    # speaker (x-ray): cone facing forward
    sp = pj(*SPK)
    if xray > 0.02:
        cyl3(cv, pj, (SPK[0] - 26, SPK[1], SPK[2]), (SPK[0] - 8, SPK[1], SPK[2]), 9, STEEL_D, alpha=xray, n=24)
        cyl3(cv, pj, (SPK[0] - 8, SPK[1], SPK[2]), (SPK[0] + 4, SPK[1], SPK[2]), 18, mix(STEEL, AMBER, glow_spk),
             alpha=xray, n=32)
        if glow_spk > 0:
            cv.drawCircle(sp[0], sp[1], 30 * pj.s, paint(AMBER, a=0.5 * glow_spk * xray, blur=12 * pj.s))
    # near wheels (rotating spokes)
    for x in WHEELS:
        cyl3(cv, pj, (x, -WR, ZF + 4), (x, -WR, ZF + 30), WR, C_TIRE, n=40, edge=hx("#000000"))
        c = pj(x, -WR, ZF + 3)
        cv.drawCircle(c[0], c[1], 21 * pj.s, paint(C_RIM))
        ang = -roll / WR
        for i in range(5):
            th = ang + i * 2 * math.pi / 5
            e = (c[0] + 19 * pj.s * math.cos(th) * 0.99, c[1] + 19 * pj.s * math.sin(th))
            cv.drawLine(*c, *e, paint(hx("#5a6575"), stroke=3.2 * pj.s / 1.2))
        cv.drawCircle(c[0], c[1], 6 * pj.s, paint(hx("#3a4250")))
    cv.restore()
    return sp, hl


def sound_rings(cv, p, t, level, color=CYAN, rate=2.2, rmax=320, sweep=110, direction=0.0, width=4):
    """Expanding arcs from p (a sound source). level 0..1 scales size and opacity."""
    if level <= 0.01:
        return
    for j in range(4):
        ph = (t * rate / 1.0 + j / 4) % 1.0
        r = 20 + rmax * ph * (0.4 + 0.6 * level)
        a = level * (1 - ph) ** 1.3
        rect = skia.Rect.MakeLTRB(p[0] - r, p[1] - r, p[0] + r, p[1] + r)
        cv.drawArc(rect, direction - sweep / 2, sweep, False, paint(color, a=0.85 * a, stroke=width))
        cv.drawArc(rect, direction - sweep / 2, sweep, False, paint(color, a=0.35 * a, stroke=width * 3, blur=6))


# ================================================================== pedestrian (generic silhouette)
def draw_person(cv, x, yf, h, walk=0.0, look_up=0.0, a=1.0, facing=0.0):
    """Front-facing walker. walk = gait phase (rad); look_up 0 = eyes on phone, 1 = head up toward the car."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * a))
    u = h / 180.0
    body = hx("#24304a")
    rim = hx("#7fa0d0")
    sw = math.sin(walk)
    # legs
    for side, ph in ((-1, sw), (1, -sw)):
        hip = (x + side * 11 * u, yf - 90 * u)
        foot = (x + side * 13 * u, yf - max(0, ph) * 8 * u)
        knee = (x + side * 13 * u + ph * 3 * u, yf - 45 * u - max(0, ph) * 6 * u)
        pth = skia.Path()
        pth.moveTo(*hip); pth.lineTo(*knee); pth.lineTo(*foot)
        cv.drawPath(pth, paint(body, stroke=17 * u, cap=skia.Paint.kRound_Cap, join=skia.Paint.kRound_Join))
        cv.drawPath(pth, paint(rim, a=0.35, stroke=2))
    # torso
    tr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 25 * u, yf - 150 * u, x + 25 * u, yf - 84 * u), 14 * u, 14 * u)
    cv.drawRRect(tr, paint(body))
    cv.drawRRect(tr, paint(rim, a=0.5, stroke=2))
    # arms: right hand holds the phone in front of the chest
    la = skia.Path()
    la.moveTo(x - 24 * u, yf - 142 * u); la.lineTo(x - 30 * u + sw * 4 * u, yf - 100 * u)
    cv.drawPath(la, paint(body, stroke=11 * u, cap=skia.Paint.kRound_Cap))
    hand = (x + 6 * u, yf - 118 * u + 10 * u * look_up)
    ra = skia.Path()
    ra.moveTo(x + 24 * u, yf - 142 * u); ra.lineTo(x + 22 * u, yf - 116 * u); ra.lineTo(*hand)
    cv.drawPath(ra, paint(body, stroke=11 * u, cap=skia.Paint.kRound_Cap, join=skia.Paint.kRound_Join))
    # phone glow
    pr = skia.Rect.MakeXYWH(hand[0] - 7 * u, hand[1] - 12 * u, 14 * u, 20 * u)
    cv.drawRect(pr, paint(hx("#bfe9ff"), a=0.95))
    cv.drawCircle(hand[0], hand[1] - 12 * u, 26 * u, paint(CYAN, a=0.35 * (1 - 0.6 * look_up), blur=10 * u))
    # head: tilted down at the phone, or turned toward the car (left)
    hx_ = x - 6 * u * look_up
    hy = yf - 166 * u + 6 * u * (1 - look_up)
    cv.drawCircle(hx_, hy, 15 * u, paint(body))
    cv.drawCircle(hx_, hy, 15 * u, paint(rim, a=0.55, stroke=2))
    # face glow from the phone
    cv.drawCircle(hx_, hy + 6 * u, 10 * u, paint(CYAN, a=0.25 * (1 - look_up), blur=6 * u))
    cv.restore()


# ================================================================== street
HORIZON = 900
GROUND = 1185          # where the car's tyres touch
CAR_S = 1.05
_rng = np.random.default_rng(11)
BUILDINGS = []
_x = -40
while _x < W + 400:
    w = float(_rng.uniform(90, 190))
    h = float(_rng.uniform(160, 430))
    BUILDINGS.append((_x, w, h, int(_rng.integers(0, 10 ** 6))))
    _x += w + float(_rng.uniform(4, 30))


def draw_city(cv, scroll=0.0):
    look.night_sky(cv, HORIZON, glow=hx("#5a7bd6"), glow_a=0.22, t=0.0)
    for (x0, w, h, seed) in BUILDINGS:
        x = x0 - (scroll * 0.25) % (W + 400)
        if x < -250:
            x += W + 450
        r = skia.Rect.MakeLTRB(x, HORIZON - h, x + w, HORIZON + 10)
        cv.drawRect(r, paint(hx("#0c1422")))
        cv.drawRect(r, paint(hx("#2a3c5e"), a=0.5, stroke=1.5))
        rg = np.random.default_rng(seed)
        for wy in np.arange(HORIZON - h + 18, HORIZON - 10, 30):
            for wx in np.arange(x + 12, x + w - 16, 24):
                if rg.uniform() < 0.33:
                    cv.drawRect(skia.Rect.MakeXYWH(wx, wy, 11, 14), paint(hx("#ffd890"), a=float(rg.uniform(0.25, 0.7))))
    look.haze(cv, HORIZON - 200, HORIZON + 40, a=0.10)


def draw_ground(cv, scroll=0.0, crosswalk_x=None):
    rp = skia.Paint()
    rp.setShader(lin_grad((0, HORIZON), (0, 1500), [hx("#1a1f29"), hx("#090b0f")]))
    cv.drawRect(skia.Rect.MakeLTRB(0, HORIZON, W, H), rp)
    # far sidewalk + curb
    cv.drawRect(skia.Rect.MakeLTRB(0, HORIZON, W, HORIZON + 70), paint(hx("#232a36")))
    cv.drawRect(skia.Rect.MakeLTRB(0, HORIZON + 66, W, HORIZON + 74), paint(hx("#4a5468")))
    # near sidewalk
    cv.drawRect(skia.Rect.MakeLTRB(0, 1300, W, H), paint(hx("#20262f")))
    cv.drawRect(skia.Rect.MakeLTRB(0, 1296, W, 1306), paint(hx("#4a5468")))
    # lane dashes
    off = scroll % 300
    for i in range(-2, 6):
        x = i * 300 - off
        cv.drawRect(skia.Rect.MakeXYWH(x, 1085, 150, 9), paint(hx("#d8d2a8"), a=0.45))
    # crosswalk stripes (on the road plane: stripes run across the lane, receding up-right)
    if crosswalk_x is not None:
        for i in range(7):
            y0 = HORIZON + 86 + i * 30
            y1 = y0 + 16
            sh0, sh1 = (1300 - y0) * 0.17, (1300 - y1) * 0.17
            quad = np.array([[crosswalk_x + sh0, y0], [crosswalk_x + 190 + sh0, y0],
                             [crosswalk_x + 190 + sh1, y1], [crosswalk_x + sh1, y1]])
            cv.drawPath(poly_path(quad), paint(hx("#e8e6da"), a=0.32 + 0.03 * i))
        for i in range(3):
            y0 = 1196 + i * 32
            sh = (1300 - y0) * 0.17
            quad = np.array([[crosswalk_x + sh, y0], [crosswalk_x + 190 + sh, y0], [crosswalk_x + 190 + sh, y0 + 18],
                             [crosswalk_x + sh, y0 + 18]])
            cv.drawPath(poly_path(quad), paint(hx("#e8e6da"), a=0.5))


def draw_streetlight(cv, x, scroll=0.0):
    x = x - scroll
    cv.drawRect(skia.Rect.MakeXYWH(x - 5, HORIZON - 330, 10, 400), paint(hx("#3a4456")))
    cv.drawLine(x, HORIZON - 330, x - 70, HORIZON - 340, paint(hx("#3a4456"), stroke=8))
    look.beam(cv, (x - 70, HORIZON - 335), (x - 70, HORIZON + 200), 8, 190, c=hx("#ffe2a8"), a=0.16)
    look.bloom(cv, x - 70, HORIZON - 332, 9, hx("#ffe2a8"), a=0.9)


def street_base(cv, t, scroll=0.0, crosswalk_x=None):
    draw_city(cv, scroll)
    draw_ground(cv, scroll, crosswalk_x)
    draw_streetlight(cv, 930, scroll * 0.0)


# hook: the car creeps toward the crossing; pedestrian walks across, eyes on the phone
def car_x_hook(t):
    return 30 + 16 * min(t, T_PROB)          # rear x (px); slow creep


def draw_street1(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    zoom = 1 + 1.0 * ease(lin(t, T_NOT - 0.2, T_HERES + 0.5))
    x0 = car_x_hook(t)
    pj = car_proj(x0, GROUND, CAR_S)
    spk = pj(*SPK)
    fx, fy = spk[0], spk[1]
    tx = (540 - fx) * ease(lin(t, T_NOT - 0.2, T_HERES + 0.5))
    ty = (900 - fy) * ease(lin(t, T_NOT - 0.2, T_HERES + 0.5))
    cv.save()
    cv.translate(fx + tx, fy + ty)
    cv.scale(zoom, zoom)
    cv.translate(-fx, -fy)
    street_base(cv, t, 0.0, crosswalk_x=690)
    look.soft_shadow(cv, x0 + 250, GROUND + 4, 560, 40, a=0.7)
    xr = eout(lin(t, T_NOT + 0.2, T_NOT + 0.9))
    sp, hl = draw_car(cv, pj, t, roll=16 * min(t, T_PROB) / CAR_S, xray=xr, glow_spk=0.6 + 0.4 * math.sin(t * 9))
    look.beam(cv, hl, (hl[0] + 520, hl[1] + 70), 8, 120, a=0.22)
    # hum rings
    sound_rings(cv, sp, t, 0.75, CYAN, rate=1.6, rmax=260, sweep=120, direction=0)
    # pedestrian walks across (toward the camera) on the crossing
    pk = lin(t, 0.0, T_NOT + 1.0)
    px, pyf = 860 - 60 * pk, 1090 + 170 * pk
    draw_person(cv, px, pyf, 165 + 30 * pk, walk=t * 6.5)
    cv.restore()
    look.vignette(cv, 0.5)
    cv.restore()
    # overlays (not zoomed)
    k_q = win(t, T_WHO - 0.1, T_HOOK_OUT + 0.3, 0.2, 0.3)
    if k_q > 0:
        s_ = 1 + 0.3 * (1 - eback(lin(t, T_WHO - 0.1, T_WHO + 0.25)))
        pk = lin(t, 0.0, T_NOT + 1.0)
        cv.save(); cv.translate(860 - 60 * pk + 70, 1090 + 170 * pk - (165 + 30 * pk) - 40); cv.scale(s_, s_)
        draw_text(cv, "?", 0, 0, font("pop_b", 120), YEL, a=k_q, align="center", glow=14, glow_c=YEL)
        cv.restore()
    k_p = win(t, 0.2, T_HOOK_OUT + 0.2, 0.3, 0.3)
    if k_p > 0:
        pill(cv, 540, 1360, "ELECTRIC CAR · 8 KM/H", font("inter_xb", 28), INK, border=CYAN, a=k_p, align="center",
             tracking=2, dot=CYAN)
    k_c = win(t, T_HERES - 0.1, T_PROB + 0.1, 0.25, 0.3)
    if k_c > 0:
        brand.label(cv, t, "SPEAKER", (540, 900), (640, 690), AMBER, T_NOT + 0.6, T_PROB + 0.1)
        brand.chips(cv, k_c, 1360, [("FAKE SOUND", eout(lin(t, T_HERES, T_HERES + 0.3))),
                                    ("ON PURPOSE", eout(lin(t, T_HERES + 0.4, T_HERES + 0.7)))], center=True)


# ================================================================== COMPARE: gas engine vs electric motor
def draw_engine_icon(cv, cx, cy, t, a):
    pj = Proj(cx, cy, 1.0, yaw=35, pitch=24)
    extrude(cv, pj, np.array([[-150, -115], [150, -115], [150, 70], [-150, 70]], float), -55, 55, hx("#4d5767"),
            alpha=0.3 * a)
    for i in range(4):
        x = -105 + 70 * i
        ph = t * 9.0 + [0, math.pi, math.pi, 0][i]
        y = -20 - 38 - 22 * math.cos(ph)
        cyl3(cv, pj, (x, y + 30, 0), (x, y, 0), 26, mix(STEEL, YEL, 0.2), alpha=a, n=28)
        cyl3(cv, pj, (x, -110, 0), (x, -20, 0), 30, hx("#6b7c96"), alpha=a, fill_a=0.1, edge=hx("#7d8fae"),
             edge_w=1.2, cap=False, n=28)
    # exhaust pipe out the back with pulses
    pts = spline(pj(np.array([150, 200, 240, 300]), np.array([10, 10, 60, 70]), np.array([0, 0, 0, 0])), 30)
    pipe(cv, pts, 22, hx("#7a8496"), a=a)
    end = pts[-1]
    for j in range(5):
        age = (t * 4.4 + j / 5) % 1.0
        look.puff(cv, end[0] + 10, end[1], age * 0.9, life=0.9, size=18, a=0.35 * a, drift=(80, -40))
    return pj(0, -130, 0)


def draw_motor_icon(cv, cx, cy, t, a):
    from ev.parts import rev
    pj = Proj(cx, cy, 1.0, yaw=35, pitch=24)
    rev(cv, pj, "x", (0, 0), [-120, 120], [80, 80], hx("#5b6a82"), alpha=a, fill_a=0.25, edge=hx("#7d8fae"))
    th = t * 14.0
    for i in range(6):
        ang = th + i * math.pi / 3
        y, z = 50 * math.sin(ang), 50 * math.cos(ang)
        if z < 0:
            continue
        p0, p1 = pj(-110, y, z), pj(110, y, z)
        cv.drawLine(*p0, *p1, paint(CYAN, a=0.5 * a, stroke=3))
    rev(cv, pj, "x", (0, 0), [-100, 100], [42, 42], hx("#b8892a"), alpha=a)
    rev(cv, pj, "x", (0, 0), [-170, 170], [12, 12], STEEL, alpha=a)
    for i in range(6):
        ang = th + i * math.pi / 3
        y, z = 50 * math.sin(ang), 50 * math.cos(ang)
        if z >= 0:
            continue
        p0, p1 = pj(-110, y, z), pj(110, y, z)
        cv.drawLine(*p0, *p1, paint(CYAN, a=0.9 * a, stroke=3))
    return pj(0, -100, 0)


def meter(cv, x, y, w, frac, color, label, a):
    draw_text(cv, label, x, y - 22, font("inter_xb", 22), MUTED, a=a, tracking=3)
    n = 14
    for i in range(n):
        on = (i + 0.5) / n < frac
        c = color if on else hx("#263043")
        cv.drawRect(skia.Rect.MakeXYWH(x + i * (w / n), y, w / n - 6, 26), paint(c, a=a))


def draw_compare(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    kg = eout(lin(t, T_GAS - 0.2, T_GAS + 0.3))
    ke = eout(lin(t, T_ELEC - 0.2, T_ELEC + 0.3))
    if kg > 0:
        brand.panel(cv, 70, 330, 940, 470, "GAS ENGINE", AMBER, a=kg)
        top = draw_engine_icon(cv, 400, 620, t, kg)
        sound_rings(cv, (650, 560), t, 1.0 * kg, AMBER, rate=2.6, rmax=230, sweep=150, direction=-20, width=5)
        meter(cv, 130, 740, 600, 0.85, AMBER, "SOUND", kg)
        draw_text(cv, "LOUD", 960, 763, font("inter_blk", 30), AMBER, a=kg, align="right", tracking=3)
    if ke > 0:
        brand.panel(cv, 70, 830, 940, 470, "ELECTRIC MOTOR", CYAN, a=ke)
        draw_motor_icon(cv, 420, 1110, t, ke)
        sound_rings(cv, (690, 1060), t, 0.18 * ke, CYAN, rate=2.0, rmax=120, sweep=150, direction=-20, width=3)
        meter(cv, 130, 1240, 600, 0.12, CYAN, "SOUND", ke)
        draw_text(cv, "ALMOST SILENT", 960, 1263, font("inter_blk", 26), CYAN, a=ke, align="right", tracking=2)
    cv.restore()
    brand.stamp(cv, t, "CAN'T HEAR IT COMING", T_PEOPLE, dur=1.8, center=(540, 1060))


# ================================================================== DATA: NHTSA 2017
GDX, GDY, GDW, GDH = 170.0, 560.0, 740.0, 520.0
ODDS = [("GAS CARS", 1.00, CYAN), ("HYBRIDS + EVs", 1.52, RED)]


def draw_data(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    brand.graph_box(cv, (GDX, GDY, GDW, GDH), "PEDESTRIAN CRASH ODDS · LOW-SPEED MOVES")
    vmax = 1.8
    bw = 210
    for i, (name, v, c) in enumerate(ODDS):
        t0 = T_RESEARCH if i == 0 else T_HYB
        g = eout(lin(t, t0 - 0.1, t0 + 0.7))
        if g <= 0:
            continue
        x = GDX + 110 + i * 340
        hgt = GDH * (v / vmax) * g
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x, GDY + GDH - hgt, x + bw, GDY + GDH), 12, 12)
        cv.drawRRect(r, paint(c, a=0.25, blur=14))
        cv.drawRRect(r, paint(mix(c, hx("#0b111c"), 0.35)))
        cv.drawRRect(r, paint(c, stroke=3))
        draw_text(cv, f"{v * g:.2f}x" if i else "1.00x", x + bw / 2, GDY + GDH - hgt - 22, font("inter_blk", 44), INK,
                  align="center")
        draw_text(cv, name, x + bw / 2, GDY + GDH + 40, font("inter_xb", 26), c, align="center", tracking=2)
    # +50% bracket
    kb = eout(lin(t, T_FIFTY - 0.1, T_FIFTY + 0.4))
    if kb > 0:
        y1 = GDY + GDH - GDH / vmax
        y2 = GDY + GDH - GDH * 1.52 / vmax
        x = GDX + 110 + 340 - 40
        cv.drawLine(GDX + 110 + bw, y1, x + 30, y1, paint(MUTED, a=kb, stroke=2))
        p = paint(RED, a=kb, stroke=4)
        cv.drawLine(x, y1, x, y2, p)
        cv.drawLine(x - 10, y1, x + 10, y1, p)
        cv.drawLine(x - 10, y2, x + 10, y2, p)
    draw_text(cv, "SOURCE: NHTSA STUDY, 2017", GDX + GDW / 2, GDY + GDH + 110, font("inter_sb", 20), MUTED, align="center", tracking=2)
    cv.restore()
    brand.stamp(cv, t, "+50%", T_FIFTY, dur=2.2, center=(540, 455))
    kc = win(t, T_BACK - 0.2, T_LAW + 0.2, 0.25, 0.3)
    if kc > 0:
        brand.chips(cv, kc, 1270, [("BACKING UP", eout(lin(t, T_BACK, T_BACK + 0.3))),
                                   ("TURNING", eout(lin(t, T_TURN, T_TURN + 0.3)))], center=True)


# ================================================================== XRAY: the law + how it works
XS = 1.62


def speed_law(t):
    """km/h during the law beat: 0 -> 28."""
    return 28.0 * ease(lin(t, T_READS - 0.2, T_LOUDER + 0.6))


def draw_xray(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    v = speed_law(t)
    lev = clamp(0.25 + 0.75 * v / 28.0) if t > T_PLAYS - 0.1 else 0.0
    lev *= eout(lin(t, T_PLAYS - 0.1, T_PLAYS + 0.4))
    x0 = 540 - 475 * XS * 0.985 / 2 - 40
    pj = car_proj(x0, 980, XS)
    look.soft_shadow(cv, 540, 984, 760, 40, a=0.6)
    roll = 0.0
    for tt in np.linspace(T_LAW, t, 12):
        pass
    roll = 400 * lin(t, T_READS, T_RE) ** 1.6
    sp, hl = draw_car(cv, pj, t, roll=roll, xray=1.0, glow_spk=lev)
    # speed sensor at the front wheel -> control unit -> speaker
    ws = pj(WHEELS[1], -WR, ZF + 12)
    cu = pj(430.0, -70.0, -20.0)
    wire1 = spline(np.array([ws, [ws[0] + 30, ws[1] - 60], [cu[0] - 30, cu[1] + 10], cu]), 40)
    wire2 = spline(np.array([cu, [cu[0] + 18, cu[1] + 14], sp]), 20)
    kw = eout(lin(t, T_READS - 0.2, T_READS + 0.4))
    if kw > 0:
        pipe(cv, wire1, 8, AMBER, a=kw, glass=True)
        flow(cv, wire1, t, 260, 22, AMBER, r=4, a=kw, t_start=T_READS)
        cv.drawCircle(ws[0], ws[1], 10, paint(AMBER, a=kw))
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cu[0] - 26, cu[1] - 18, 52, 36), 6, 6)
        cv.drawRRect(r, paint(hx("#1a2333"), a=kw))
        cv.drawRRect(r, paint(AMBER, a=kw, stroke=2.5))
    kp = eout(lin(t, T_PLAYS - 0.2, T_PLAYS + 0.3))
    if kp > 0:
        pipe(cv, wire2, 8, AMBER, a=kp, glass=True)
        flow(cv, wire2, t, 260, 22, AMBER, r=4, a=kp, t_start=T_PLAYS)
    sound_rings(cv, sp, t, lev, AMBER, rate=2.4, rmax=260, sweep=110, direction=0, width=5)
    brand.label(cv, t, "WHEEL SPEED", tuple(ws), (300, 1070), AMBER, T_READS - 0.1, T_RE + 0.2)
    brand.label(cv, t, "CONTROL UNIT", tuple(cu), (700, 560), AMBER, T_PLAYS - 0.1, T_RE + 0.2, align="right")
    brand.label(cv, t, "SPEAKER", tuple(sp), (960, 650), YEL, T_SPEAKER - 0.1, T_RE + 0.2, align="right")
    # speaker cutaway inset
    ki = win(t, T_SPEAKER - 0.1, T_RE + 0.2, 0.3, 0.3)
    if ki > 0:
        draw_speaker_cut(cv, t, ki, lev)
    cv.restore()
    kr = win(t, T_READS - 0.2, T_RE + 0.2, 0.3, 0.3)
    brand.readout(cv, kr, f"{v:.0f}", "KM/H", frac=v / 30.0, bar_color=AMBER)
    if kr > 0:
        brand.note(cv, f"{v * 0.621:.0f} MPH", 0.9 * kr, dy=0)
    brand.stamp(cv, t, "REQUIRED BY LAW", T_LAWW - 0.15, dur=1.6, center=(540, 520), color=AMBER, bg=hx("#2a1d05"))


def draw_speaker_cut(cv, t, k, lev):
    """Side cutaway of a speaker: magnet, voice coil, cone that pumps air; level = excursion."""
    cx, cy = 540.0, 1230.0
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 400, cy - 115, 800, 220), 24, 24)
    cv.drawRRect(rr, paint(hx("#0b111c"), a=0.9 * k))
    cv.drawRRect(rr, paint(hx("#2a3446"), a=k, stroke=2))
    draw_text(cv, "SPEAKER, CUT IN HALF", cx - 370, cy - 78, font("inter_xb", 20), MUTED, a=k, tracking=3)
    ex = 9 * lev * math.sin(t * 2 * math.pi * 7.0)
    mx = cx - 200
    # magnet
    cv.drawRect(skia.Rect.MakeXYWH(mx - 70, cy - 45, 60, 90), paint(hx("#5a6170"), a=k))
    cv.drawRect(skia.Rect.MakeXYWH(mx - 10, cy - 18, 50, 36), paint(hx("#8c96a8"), a=k))
    draw_text(cv, "MAGNET", mx - 40, cy + 78, font("inter_xb", 18), MUTED, a=k, align="center", tracking=2)
    # coil (amber when driven)
    cr = skia.Rect.MakeXYWH(mx + 30 + ex, cy - 26, 28, 52)
    cv.drawRect(cr, paint(mix(STEEL, AMBER, lev), a=k))
    draw_text(cv, "COIL", mx + 44, cy - 40, font("inter_xb", 18), AMBER, a=k, align="center", tracking=2)
    # cone
    pth = skia.Path()
    pth.moveTo(mx + 58 + ex, cy - 26)
    pth.lineTo(mx + 190 + ex, cy - 92)
    pth.moveTo(mx + 58 + ex, cy + 26)
    pth.lineTo(mx + 190 + ex, cy + 92)
    cv.drawPath(pth, paint(INK, a=k, stroke=5))
    cv.drawLine(mx + 190 + ex, cy - 92, mx + 190 + ex, cy + 92, paint(INK, a=0.3 * k, stroke=2))
    draw_text(cv, "CONE", mx + 120, cy + 102, font("inter_xb", 18), MUTED, a=k, align="center", tracking=2)
    # air waves leaving the cone (amplitude = level)
    for j in range(5):
        ph = (t * 1.6 + j / 5) % 1.0
        x = mx + 210 + 300 * ph
        h = 80 * (0.3 + 0.7 * lev)
        cv.drawLine(x, cy - h, x, cy + h, paint(AMBER, a=k * lev * (1 - ph), stroke=4))
    # level bar
    bx = cx + 330
    cv.drawLine(bx, cy + 80, bx, cy - 80, paint(hx("#263043"), a=k, stroke=16))
    cv.drawLine(bx, cy + 80, bx, cy + 80 - 160 * lev, paint(AMBER, a=k, stroke=16))
    draw_text(cv, "LEVEL", bx, cy + 104, font("inter_xb", 16), MUTED, a=k, align="center", tracking=2)


# ================================================================== GRAPH: why it switches off
GX, GY, GW, GH = 150.0, 600.0, 780.0, 520.0
VMAX = 50.0
THR = 0.42           # "audible to people nearby" line (illustrative)


def tyre_wind(v):
    return 0.06 + (THR - 0.06) * (v / 30.0) ** 1.4


def speaker_lvl(v):
    return 0.0 if v > 30.0 else 0.50 + 0.18 * v / 30.0


def heard(v):
    return max(tyre_wind(v), speaker_lvl(v))


def gpt(v, y):
    return GX + GW * v / VMAX, GY + GH - GH * y / 1.0


def speed_graph(t):
    """Car speed shown by the dot (km/h)."""
    return float(np.interp(t, [T_RE, T_NINETEEN + 0.3, T_QUIET + 0.2, T_TIRES, T_LOUD + 0.4],
                           [10.0, 28.0, 31.5, 31.5, 46.0]))


def draw_graph(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    brand.graph_box(cv, (GX, GY, GW, GH), "SOUND PEOPLE NEARBY HEAR")
    # x ticks
    for v in (0, 10, 20, 30, 40, 50):
        x, y = gpt(v, 0)
        draw_text(cv, str(v) + (" KM/H" if v == 50 else ""), x - (40 if v == 50 else 0), y + 34, font("inter_sb", 20),
                  MUTED, align="center")
    # audible threshold
    p = paint(GREEN, a=0.8, stroke=2.5)
    p.setPathEffect(skia.DashPathEffect.Make([12, 9], 0))
    ty = gpt(0, THR)[1]
    cv.drawLine(GX, ty, GX + GW, ty, p)
    draw_text(cv, "EASY TO HEAR", GX + 8, ty - 12, font("inter_xb", 20), GREEN, tracking=2)
    vs = np.linspace(0, VMAX, 240)
    vd = speed_graph(t)
    # speaker curve (amber): traced up to the dot
    sp_pts = []
    for v in vs:
        if v > vd:
            break
        sp_pts.append(gpt(v, speaker_lvl(v)))
    if len(sp_pts) > 2:
        pts = np.array(sp_pts)
        # draw the drop to zero at 30 as a vertical segment
        on = pts[np.array([v <= 30.0 for v in vs[:len(pts)]])]
        brand.curve(cv, on, AMBER, width=5)
        if vd > 30.0:
            a0, a1 = gpt(30.0, speaker_lvl(30.0)), gpt(30.0, 0.0)
            cv.drawLine(*a0, *a1, paint(AMBER, stroke=5))
            brand.curve(cv, np.array([gpt(30.0, 0.0), gpt(vd, 0.0)]), AMBER, width=5)
    kl = eout(lin(t, T_RE, T_RE + 0.4))
    draw_text(cv, "SPEAKER", gpt(4, 0)[0], gpt(0, 0.74)[1], font("inter_xb", 24), AMBER, a=kl, tracking=2)
    # 30 km/h line
    kn = eout(lin(t, T_NINETEEN - 0.2, T_NINETEEN + 0.3))
    if kn > 0:
        x30 = gpt(30, 0)[0]
        p2 = paint(INK, a=0.6 * kn, stroke=2)
        p2.setPathEffect(skia.DashPathEffect.Make([8, 8], 0))
        cv.drawLine(x30, GY, x30, GY + GH, p2)
        pill(cv, x30, GY + 34, "30 KM/H ≈ 19 MPH", font("inter_xb", 24), INK, border=INK, a=kn, align="center",
             tracking=1.5)
    # tyre + wind curve (cyan)
    kt = lin(t, T_TIRES - 0.1, T_LOUD + 0.3)
    if kt > 0:
        pts = np.array([gpt(v, tyre_wind(v)) for v in vs])
        brand.curve(cv, pts, CYAN, prog=ease(kt), width=5)
        draw_text(cv, "TIRES + WIND", gpt(30, 0)[0], gpt(0, tyre_wind(50) + 0.02)[1], font("inter_xb", 24), CYAN,
                  a=clamp(kt * 3), tracking=2)
    # crossover glow at 30
    kx = eout(lin(t, T_LOUD - 0.1, T_LOUD + 0.4))
    if kx > 0:
        x, y = gpt(30, tyre_wind(30))
        cv.drawCircle(x, y, 34, paint(GREEN, a=0.5 * kx, blur=12))
        cv.drawCircle(x, y, 12, paint(INK, a=kx))
    # dot = this car
    x, y = gpt(vd, speaker_lvl(vd) if vd <= 30 else (tyre_wind(vd) if t > T_TIRES else 0.0))
    brand.dot(cv, x, y, AMBER if vd <= 30 else CYAN)
    # status chip under the graph
    off = vd > 30.0
    pill(cv, 540, 1290, "SPEAKER: OFF" if off else "SPEAKER: ON", font("inter_blk", 32), INK,
         border=(MUTED if off else AMBER), dot=(MUTED if off else AMBER), align="center", tracking=3)
    draw_text(cv, "ILLUSTRATION · US RULE: UNDER 30 KM/H · EU: UNDER ~20 KM/H", 540, 1360, font("inter_sb", 19),
              MUTED, align="center", tracking=1.5)
    cv.restore()
    k = win(t, T_WHY - 0.1, T_KEY + 0.4, 0.15, 0.3)
    if k > 0:
        s_ = 1 + 0.3 * (1 - eback(lin(t, T_WHY - 0.1, T_WHY + 0.25)))
        cv.save(); cv.translate(800, 760); cv.scale(s_, s_)
        draw_text(cv, "?", 0, 40, font("pop_b", 150), YEL, a=k, align="center", glow=16, glow_c=YEL)
        cv.restore()
    brand.stamp(cv, t, "LOUD ENOUGH", T_LOUD, dur=1.5, center=(540, 470), color=GREEN, bg=hx("#06281a"))


# ================================================================== STREET2: payoff
def draw_street2(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    street_base(cv, t, 0.0, crosswalk_x=None)
    t0, t1 = S_STREET2[0], T_TW + 0.3
    x0 = -380 + 1300 * lin(t, t0, t1)
    pj = car_proj(x0, GROUND, CAR_S)
    # speed streaks
    for i in range(7):
        y = GROUND - 30 - 18 * i
        cv.drawLine(x0 - 220, y, x0 - 20, y, paint(INK, a=0.10, stroke=3))
    look.soft_shadow(cv, x0 + 250, GROUND + 4, 560, 40, a=0.7)
    sp, hl = draw_car(cv, pj, t, roll=1300 * lin(t, t0, t1) * 3)
    look.beam(cv, hl, (hl[0] + 520, hl[1] + 70), 8, 120, a=0.22)
    for x in WHEELS:
        c = pj(x, -6, ZF)
        sound_rings(cv, c, t, 0.85, CYAN, rate=3.0, rmax=220, sweep=160, direction=-90, width=4)
    # pedestrian on the near sidewalk looks up
    lu = eout(lin(t, T_NEVER, T_NEVER + 0.6))
    draw_person(cv, 820, 1375, 225, walk=0.0, look_up=lu)
    look.vignette(cv, 0.5)
    cv.restore()
    brand.stamp(cv, t, "NOT FOR YOU", T_NEVER + 0.1, dur=1.4, center=(540, 520))
    kp = win(t, T_PEOPLE2 - 0.1, T_TW + 0.2, 0.25, 0.3)
    if kp > 0:
        pill(cv, 540, 520, "FOR THE PEOPLE OUTSIDE", font("inter_blk", 40), INK, border=GREEN, dot=GREEN, a=kp * k,
             align="center", tracking=3)
    kq = win(t, T_NEVER - 0.1, T_TW + 0.2, 0.25, 0.3)
    if kq > 0:
        pill(cv, 540, 640, "SPEAKER: OFF · TIRES DO THE WORK", font("inter_xb", 24), INK, border=CYAN, a=kq * k,
             tracking=1.5, align="center")


# ================================================================== TWIST: performance EV
SHIFT_DT = 1.35


def shifts():
    s = [T_SHIFT - i * SHIFT_DT for i in range(8)]
    return sorted(x for x in s if x > T_IONIQ + 0.4)


SHIFTS = shifts()


def gear_rpm(t):
    """Virtual tach: climbs in each gear, drops at each fake shift (after the power cut)."""
    t0 = T_IONIQ
    if t < t0:
        return 1200.0, 1
    marks = [t0] + SHIFTS
    g = sum(1 for s in SHIFTS if t >= s + 0.12)
    start = marks[min(g, len(marks) - 1)] + (0.12 if g else 0.0)
    span = SHIFT_DT
    u = clamp((t - start) / span)
    lo, hi = (2500.0, 7600.0) if g == 0 else (5200.0, 7600.0)
    return lo + (hi - lo) * (1 - (1 - u) ** 1.6), 1 + g


def power_cut(t):
    """1 = full power, 0 = cut (the fake shift)."""
    for s in SHIFTS:
        if s - 0.02 <= t <= s + 0.12:
            return 0.15
    return 1.0


def draw_topview(cv, t, k):
    cx, cy = 540.0, 760.0
    cv.saveLayerAlpha(None, int(255 * k))
    body = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 150, cy - 300, 300, 600), 90, 90)
    cv.drawRRect(body, paint(hx("#1a2333")))
    cv.drawRRect(body, paint(CYAN, stroke=3))
    cab = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 115, cy - 150, 230, 310), 50, 50)
    cv.drawRRect(cab, paint(hx("#0f1a2b")))
    cv.drawRRect(cab, paint(hx("#5d7499"), stroke=2))
    for (dx, dy) in ((-62, -60), (62, -60), (-62, 70), (62, 70)):
        seat = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx + dx - 34, cy + dy - 40, 68, 80), 16, 16)
        cv.drawRRect(seat, paint(hx("#2b3650")))
    for (wx, wy) in ((-160, -190), (160, -190), (-160, 190), (160, 190)):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx + wx - 18, cy + wy - 45, 36, 90), 10, 10),
                     paint(C_TIRE))
    draw_text(cv, "FRONT", cx, cy - 318, font("inter_xb", 20), MUTED, align="center", tracking=3)
    # sound inside the cabin + outside
    cv.save()
    cv.clipRRect(cab, doAntiAlias=True)
    for j in range(4):
        ph = (t * 1.8 + j / 4) % 1.0
        cv.drawCircle(cx, cy, 20 + 220 * ph, paint(CYAN, a=0.7 * (1 - ph), stroke=4))
    cv.restore()
    ko = eout(lin(t, T_TEN, T_TEN + 0.4))
    for j in range(3):
        ph = (t * 1.4 + j / 3) % 1.0
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 150 - 120 * ph, cy - 300 - 120 * ph, 300 + 240 * ph,
                                                     600 + 240 * ph), 90 + 60 * ph, 90 + 60 * ph)
        cv.drawRRect(r, paint(AMBER, a=0.6 * ko * (1 - ph), stroke=4))
    cv.restore()


def speaker_icon(cv, x, y, c, a):
    cv.drawRect(skia.Rect.MakeXYWH(x - 14, y - 10, 12, 20), paint(c, a=a))
    pth = skia.Path()
    pth.moveTo(x - 2, y - 10); pth.lineTo(x + 14, y - 22); pth.lineTo(x + 14, y + 22); pth.lineTo(x - 2, y + 10)
    pth.close()
    cv.drawPath(pth, paint(c, a=a))


def draw_twist(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    cv.drawImage(brand.background(), 0, 0)
    k_top = win(t, T_TW - 0.1, T_CUTS - 0.2, 0.3, 0.4)
    if k_top > 0:
        draw_topview(cv, t, k_top)
        kt = eout(lin(t, T_TEN - 0.1, T_TEN + 0.5))
        if kt > 0:
            for i in range(8):
                speaker_icon(cv, 150 + i * 62, 1185, CYAN, kt * clamp((t - T_TEN) * 8 - i * 0.6))
            draw_text(cv, "8 INSIDE", 150 - 14, 1240, font("inter_xb", 24), CYAN, a=kt, tracking=2)
            for i in range(2):
                speaker_icon(cv, 760 + i * 62, 1185, AMBER, kt * clamp((t - T_TEN) * 8 - (8 + i) * 0.6))
            draw_text(cv, "2 OUTSIDE", 746, 1240, font("inter_xb", 24), AMBER, a=kt, tracking=2)
        k_l = win(t, T_IONIQ - 0.1, T_CUTS, 0.3, 0.3)
        if k_l > 0:
            pill(cv, 540, 1310, "SYNTHETIC ENGINE SOUND", font("inter_xb", 26), INK, border=RED, dot=RED,
                 a=k_l * k_top, align="center", tracking=2)
    k_g = win(t, T_CUTS - 0.4, T_END + 0.3, 0.35, 0.3)
    if k_g > 0:
        rpm, gear = gear_rpm(t)
        brand.gauge(cv, 540, 800, 250, rpm, vmax=9000, redline=7500, label="FAKE RPM", unit=f"GEAR {gear}",
                    alpha=k_g)
        # motor power trace
        bx, by, bw, bh = 150.0, 1185.0, 780.0, 110.0
        cv.saveLayerAlpha(None, int(255 * k_g))
        brand.graph_box(cv, (bx, by, bw, bh), "MOTOR POWER")
        ts = np.linspace(t - 3.0, t, 220)
        pts = np.array([[bx + bw * (tt - (t - 3.0)) / 3.0, by + bh - bh * 0.85 * (power_cut(tt) if tt >= T_IONIQ else 0.6)]
                        for tt in ts])
        brand.curve(cv, pts, RED, width=4)
        cv.restore()
    cv.restore()
    for s in SHIFTS:
        if T_CUTS - 0.3 <= s:
            brand.stamp(cv, t, "POWER CUT", s, dur=0.7, center=(540, 470), color=RED)
    brand.stamp(cv, t, "FAKE GEAR SHIFT", T_SHIFT + 0.13, dur=1.6, center=(540, 470))


# ================================================================== STREET3: outro
def draw_street3(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    street_base(cv, t, 0.0, crosswalk_x=690)
    x0 = 40 + 30 * (t - T_OUTRO)
    pj = car_proj(x0, GROUND, CAR_S)
    look.soft_shadow(cv, x0 + 250, GROUND + 4, 560, 40, a=0.7)
    sp, hl = draw_car(cv, pj, t, roll=30 * (t - T_OUTRO) / CAR_S)
    look.beam(cv, hl, (hl[0] + 520, hl[1] + 70), 8, 120, a=0.22)
    sound_rings(cv, sp, t, 0.75, CYAN, rate=1.6, rmax=260, sweep=120, direction=0)
    draw_person(cv, 880, 1375, 225, walk=0.0, look_up=1.0)
    look.vignette(cv, 0.5)
    cv.restore()


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_HOOK_OUT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(0, "EV ALERT SOUND", CYAN), (T_PROB, "THE PROBLEM", RED), (T_DATA, "THE DATA", RED),
           (T_LAW, "THE LAW", AMBER), (T_RE, "THE MYSTERY", YEL), (T_KEY, "THE ANSWER", GREEN),
           (T_TW, "THE TWIST", RED)]
    txt, c = sec[0][1], sec[0][2]
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    if not (T_READS - 0.2 < t < T_RE + 0.2):
        brand.note(cv, "ILLUSTRATION", 0.9 * k, dy=-40)


# ================================================================== draw
def draw(cv, t):
    kE = 1 - current.ending_k(t)
    draw_street1(cv, t, scene_k(t, S_STREET1, 0.0, 0.4))
    draw_compare(cv, t, scene_k(t, S_COMPARE))
    draw_data(cv, t, scene_k(t, S_DATA))
    draw_xray(cv, t, scene_k(t, S_XRAY))
    draw_graph(cv, t, scene_k(t, S_GRAPH))
    draw_street2(cv, t, scene_k(t, S_STREET2))
    draw_twist(cv, t, scene_k(t, S_TWIST))
    draw_street3(cv, t, scene_k(t, S_STREET3) * kE)
    draw_header(cv, t)


# ================================================================== sound (all synthesized here)
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


def _avas(dur, rise=False):
    tt = np.arange(int(dur * SR)) / SR
    g = (0.35 + 0.65 * tt / dur) if rise else np.ones_like(tt)
    f = 1.0 + (0.12 * tt / dur if rise else 0.0)
    x = np.zeros_like(tt)
    for fr, am in ((180, 0.5), (360, 0.35), (540, 0.25), (905, 0.18), (1210, 0.1)):
        x += am * np.sin(2 * np.pi * fr * f * tt + 0.3 * np.sin(2 * np.pi * 0.7 * tt))
    x *= (0.85 + 0.15 * np.sin(2 * np.pi * 5.5 * tt)) * g
    x *= np.minimum(1, tt / 0.4) * np.minimum(1, (dur - tt) / 0.5)
    return _norm(x, 0.8)


def _engine(rpm_fn, cut_fn, dur, cyl=4):
    tt = np.arange(int(dur * SR)) / SR
    rpm = np.array([rpm_fn(x) for x in tt[::48]])
    rpm = np.interp(tt, tt[::48], rpm)
    f0 = rpm / 60.0 * cyl / 2.0
    ph = np.cumsum(f0) / SR
    x = np.zeros_like(tt)
    for kk in range(1, 12):
        x += np.sin(2 * np.pi * kk * ph) / kk ** 0.9
    rng = np.random.default_rng(5)
    noise = _lp(rng.standard_normal(len(tt)), 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * ph) ** 8)
    x = x + 0.6 * noise
    cut = np.array([cut_fn(x_) for x_ in tt[::48]])
    cut = np.interp(tt, tt[::48], cut)
    x *= _lp(cut, 60)
    x = np.tanh(1.6 * x)
    return _norm(_lp(x, 5000), 0.85)


def _roar(dur):
    rng = np.random.default_rng(9)
    n = int(dur * SR)
    x = _lp(rng.standard_normal(n), 700) + 0.3 * _lp(rng.standard_normal(n), 2500)
    env = np.sin(np.pi * np.arange(n) / n) ** 1.5
    return _norm(x * env, 0.8)


def _whine(dur):
    tt = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * 2400 * tt) + 0.4 * np.sin(2 * np.pi * 4800 * tt)
    return _norm(x * np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.3), 0.5)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    clips = {
        "avas_hum": _avas(5.6),
        "avas_rise": _avas(max(2.0, T_RE - T_PLAYS), rise=True),
        "avas_out": _avas(max(2.0, T_END - T_OUTRO + 0.3)),
        "gas_idle": _engine(lambda x: 900.0, lambda x: 1.0, 2.6),
        "motor_whine": _whine(2.2),
        "tire_roar": _roar(4.0),
        "fake_engine": _engine(lambda x: gear_rpm(T_IONIQ + x)[0], lambda x: power_cut(T_IONIQ + x),
                               T_OUTRO - T_IONIQ),
    }
    for name, x in clips.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_TIRES
MUSIC_START = T_NOT


def sound():
    _make_sfx()
    sfx = [(0.0, "avas_hum", 0.55), (T_HOOK_OUT - 0.1, "whoosh_big", 0.5), (T_NOT + 0.2, "whoosh_up", 0.3),
           (T_GAS, "gas_idle", 0.45), (T_ELEC, "motor_whine", 0.12), (T_PEOPLE, "impact", 0.35),
           (T_RESEARCH, "whoosh_up", 0.25), (T_FIFTY, "impact", 0.5), (T_LAWW - 0.15, "clunk", 0.4),
           (T_PLAYS, "avas_rise", 0.5), (T_QUIET, "whoosh_down", 0.4), (T_WHY, "tick", 0.3),
           (T_TIRES, "tire_roar", 0.45), (T_LOUD, "impact", 0.4), (T_NEVER - 0.1, "tire_roar", 0.5),
           (T_TW, "whoosh_big", 0.35), (T_IONIQ, "fake_engine", 0.45), (T_OUTRO, "avas_out", 0.35)]
    return {"build": (T_RE, T_TIRES), "drop": (T_TIRES, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
