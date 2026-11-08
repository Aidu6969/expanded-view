"""Boxer rumble visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  HOOK    (hook)     a generic sedan idling at the kerb at night, rumble rings out of the tailpipe; BOXER ENGINE crossed out.
  ENGINE  (what, how) x-ray flat-four: crank + four pistons on real crank kinematics, bank-then-bank firing, every 180 deg.
  PIPES   (parts, key) pipes drawn from the heads to one turbo; each bang launches a pulse that travels its own pipe.
  TIMELINE            LEAVE row (even) and ARRIVE row (computed from the pipe lengths): short gap / long gap.
  EQUAL   (result)   right-bank pipes morph to the same length as the left; arrivals go even, rumble fades.
  KEEP    (keep)     pipes morph back, rumble returns.
Audio: the rumble clips are synthesized from the same pulse model (uneven vs even gaps) in _rumble().
"""
import math
import os

import numpy as np
import skia

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import arrow_head, path_len, pipe, point_at, resample, rev, spline

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_SAYS = F("hook", "Everyone")
T_BOXER0 = F("hook", "boxer")
T_ISNT = F("hook", "isn't.")
T_MAKING = F("hook", "making")
T_WHAT = L("what")["start"]
T_HOW = L("how")["start"]
T_PISTONS = F("how", "pistons")
T_PAIRS = F("how", "pairs,")
T_EVENLY = F("how", "evenly,")
T_BANG = F("how", "bang")
T_CRANK = F("how", "crank.")
T_PAPER = F("how", "paper,")
T_SMOOTH = F("how", "smooth")
T_RE = L("rehook")["start"]
T_WHERE = F("rehook", "where's")
T_PARTS = L("parts")["start"]
T_EXH = F("parts", "exhaust.")
T_PIPE = F("parts", "pipe,")
T_TURBO = F("parts", "turbo,")
T_SIDE = F("parts", "side")
T_KEY = L("key")["start"]
T_UNDER = F("key", "under")
T_LONG = F("key", "long")
T_OTHER = F("key", "other")
T_INCHES = F("key", "inches")
T_LEAVE = F("key", "leave")
T_ARRIVE = F("key", "arrive")
T_UNEV = F("key", "unevenly.")
T_SHORT = F("key", "short")
T_LGAP = F("key", "long", nth=1)
T_LUMPY = F("key", "lumpy")
T_RUMB = F("key", "rumble.")
T_RES = L("result")["start"]
T_FIF = F("result", "fifteen")
T_EQ = F("result", "equal")
T_TWIN = F("result", "twin")
T_LINED = F("result", "lined")
T_MOST = F("result", "most")
T_AWAY = F("result", "away.")
T_KEEP = L("keep")["start"]
T_STI = F("keep", "STI")
T_OLD = F("keep", "old")
T_YEAR = F("keep", "one.")
T_BUY = F("keep", "buy")
T_UNEQ = F("keep", "unequal")
T_BRING = F("keep", "bring")
T_OUTRO = L("outro")["start"]

# ================================================================== engine model
CYC = 2.0                 # seconds per 720 deg (slowed a lot; noted on screen)
STEP = CYC / 4            # one bang every 180 crank degrees
T0 = T_HOW - 2 * CYC      # phase origin (the crank is already turning)
STROKE_R, ROD = 38.0, 112.0

PJ = Proj(540, 640, 1.05, dx=0.42, dy=-0.42)
# cylinders: bank +1 is the car's right (near the turbo), -1 the left. z = front/rear stagger.
CYLS = [(+1, -120.0), (-1, -75.0), (+1, 75.0), (-1, 120.0)]
TDC_PHASE = [0.0, 0.0, 180.0, 180.0]
ORDER = [0, 2, 1, 3]      # bank then bank: right, right, left, left


def crank_deg(t):
    return 360.0 * (t - T0) / (CYC / 2.0)


def piston_x(c, t):
    """Distance of the crown from the crank axis, real slider-crank kinematics."""
    a = math.radians(crank_deg(t) - TDC_PHASE[c])
    return STROKE_R * math.cos(a) + math.sqrt(ROD ** 2 - (STROKE_R * math.sin(a)) ** 2) + 62.0


def pin(c, t):
    bank = CYLS[c][0]
    a = math.radians(crank_deg(t) - TDC_PHASE[c])
    return bank * STROKE_R * math.cos(a), STROKE_R * math.sin(a)


HEAD_X = 268.0
C_POINT = np.array([690.0, 955.0])
TURBO_C = np.array([806.0, 1002.0])


def port(c):
    s, z = CYLS[c]
    return np.array(PJ(s * HEAD_X, 48.0, z), float)


def left_path(c, row):
    p = port(c)
    return spline([p, p + (0, 160), (p[0] + 150, 905 + row * 22), (590, 925 + row * 22), C_POINT - (34, 0), C_POINT], 150)


def right_short(c):
    p = port(c)
    q = p + (0, 95)
    return spline([p, q, (p[0] * 0.5 + 345, 880), C_POINT], 150)


def right_equal(c, w):
    p = port(c)
    q = p + (0, 80)
    return spline([p, q, (p[0] - 110, 850), (p[0] - w, 870), (430, 880), (540, 890), C_POINT - (46, 0), C_POINT], 150)


LEFT = {1: left_path(1, 0), 3: left_path(3, 1)}
RIGHT_S = {0: right_short(0), 2: right_short(2)}
TARGET = (path_len(LEFT[1]) + path_len(LEFT[3])) / 2


def _solve_equal(c):
    lo, hi = 110.0, 620.0
    for _ in range(40):
        m = (lo + hi) / 2
        if path_len(right_equal(c, m)) < TARGET:
            lo = m
        else:
            hi = m
    return right_equal(c, (lo + hi) / 2)


RIGHT_E = {0: _solve_equal(0), 2: _solve_equal(2)}
N_R = 180
PATHS_UNEQ = {0: resample(RIGHT_S[0], N_R), 2: resample(RIGHT_S[2], N_R), 1: resample(LEFT[1], N_R), 3: resample(LEFT[3], N_R)}
PATHS_EQ = {0: resample(RIGHT_E[0], N_R), 2: resample(RIGHT_E[2], N_R), 1: PATHS_UNEQ[1], 3: PATHS_UNEQ[3]}
SHIFT = 0.21              # seconds of extra travel on the long side (exaggerated, noted)
_dL = TARGET - (path_len(RIGHT_S[0]) + path_len(RIGHT_S[2])) / 2
VEL = _dL / SHIFT


def eq_k(t):
    return ease(lin(t, T_EQ, T_EQ + 0.55)) * (1 - ease(lin(t, T_UNEQ - 0.1, T_UNEQ + 0.5)))


def mode_eq(tf):
    return T_EQ + 0.25 <= tf < T_UNEQ + 0.2


def fires(t0, t1):
    n0 = math.ceil((t0 - T0) / STEP)
    out = []
    n = n0
    while T0 + n * STEP <= t1:
        out.append((T0 + n * STEP, ORDER[n % 4]))
        n += 1
    return out


D_LONG = TARGET / VEL
D_SHORT = D_LONG - SHIFT


def delay(c, tf):
    """Same travel time for both pipes of a bank; equal-length mode: all four the same."""
    return D_LONG if (c in (1, 3) or mode_eq(tf)) else D_SHORT


# ================================================================== drawing: engine
STEEL = hx("#8d9bb0")


def fire_k(c, t):
    k = 0.0
    for tf, cc in fires(t - 0.5, t):
        if cc == c:
            k = max(k, math.exp(-(t - tf) / 0.11))
    return k


def draw_cylinder(cv, t, c, a):
    s, z = CYLS[c]
    ax0, ax1 = (60, HEAD_X - 12) if s > 0 else (-(HEAD_X - 12), -60)
    fk = fire_k(c, t)
    xc = s * piston_x(c, t)
    # conrod, then piston
    px, py = pin(c, t)
    p0 = PJ(px, py, z)
    p1 = PJ(xc - s * 30, 0.0, z)
    cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(hx("#c7d2e0"), a=a, stroke=12, cap=skia.Paint.kRound_Cap))
    # combustion glow between crown and head
    if fk > 0.02:
        x0, x1 = (xc, HEAD_X - 12) if s > 0 else (-(HEAD_X - 12), xc)
        if x1 > x0:
            rev(cv, PJ, "x", (0.0, z), [x0, x1], [44, 44], AMBER, alpha=a * clamp(fk), edge=RED, glow=fk, edge_w=1.4)
    rev(cv, PJ, "x", (0.0, z), sorted([xc, xc - s * 48]), [46, 46], hx("#d6dee9"), alpha=a, edge=mix(hx("#7f8ea6"), RED, fk), edge_w=1.4)
    # glass barrel + head
    rev(cv, PJ, "x", (0.0, z), [ax0, ax1], [56, 56], STEEL, alpha=a, fill_a=0.14, edge=hx("#9fb6d8"), edge_w=1.3)
    h0, h1 = (HEAD_X - 12, HEAD_X + 22) if s > 0 else (-HEAD_X - 22, -HEAD_X + 12)
    rev(cv, PJ, "x", (0.0, z), [h0, h1], [68, 68], hx("#5d6b82"), alpha=a, edge=hx("#9fb6d8"), edge_w=1.3)


def draw_crank(cv, t, a):
    rev(cv, PJ, "z", (0.0, 0.0), [-205, 205], [13, 13], hx("#c7d2e0"), alpha=a)
    for c in (3, 2, 1, 0):
        s, z = CYLS[c]
        px, py = pin(c, t)
        p0 = PJ(0, 0, z)
        p1 = PJ(px, py, z)
        cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(hx("#aab6c8"), a=a, stroke=22, cap=skia.Paint.kRound_Cap))
        cv.drawCircle(p1[0], p1[1], 10, paint(hx("#dfe6f0"), a=a))
    q = (crank_deg(t) * math.pi / 180) * 1.0
    rev(cv, PJ, "z", (0.0, 0.0), [-175, 175], [74, 74], STEEL, alpha=a, fill_a=0.10, edge=hx("#6a7c97"), edge_w=1.2)


def view_k(t):
    return 1 - ease(lin(t, T_PARTS - 0.35, T_EXH - 0.02))


def apply_view(cv, t):
    k = view_k(t)
    s = 1 + 0.25 * k
    cv.translate(540 - 20 * k, 640 + 170 * k)
    cv.scale(s, s)
    cv.translate(-540, -640)


def view_pt(p, t):
    k = view_k(t)
    s = 1 + 0.25 * k
    return (540 - 20 * k + (p[0] - 540) * s, 640 + 170 * k + (p[1] - 640) * s)


def draw_engine(cv, t, a):
    if a <= 0:
        return
    for c in (3, 2):
        draw_cylinder(cv, t, c, a)
    draw_crank(cv, t, a)
    for c in (1, 0):
        draw_cylinder(cv, t, c, a)


# ================================================================== drawing: pipes and pulses
def pipe_path(c, t):
    k = eq_k(t)
    return (1 - k) * PATHS_UNEQ[c] + k * PATHS_EQ[c]


def draw_turbo(cv, t, a):
    cx, cy = TURBO_C
    cv.drawCircle(cx, cy, 72, paint(hx("#0a1220"), a=0.85 * a))
    cv.drawCircle(cx, cy, 72, paint(hx("#9fb6d8"), a=a, stroke=3))
    th = 6.0 * t
    for i in range(9):
        ang = th + i * 2 * math.pi / 9
        x0, y0 = cx + 16 * math.cos(ang), cy + 16 * math.sin(ang)
        x1, y1 = cx + 58 * math.cos(ang + 0.5), cy + 58 * math.sin(ang + 0.5)
        cv.drawLine(x0, y0, x1, y1, paint(hx("#a98360"), a=a, stroke=8, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(cx, cy, 14, paint(hx("#c7d2e0"), a=a))


def arrivals(t0, t1):
    out = []
    for tf, c in fires(t0 - 1.2, t1):
        ta = tf + delay(c, tf)
        if t0 <= ta <= t1:
            out.append((ta, c, tf))
    return sorted(out)


def pulse_col(c):
    return RED if c in (1, 3) else CYAN


def draw_pipes(cv, t, a):
    if a <= 0:
        return
    prog = lin(t, T_EXH - 0.05, T_PIPE + 0.5)
    hi_l = win(t, T_UNDER - 0.15, T_OTHER - 0.05, 0.2, 0.3)
    hi_r = win(t, T_OTHER - 0.1, T_LEAVE + 0.1, 0.2, 0.3)
    for c in (1, 3, 2, 0):
        p = pipe_path(c, t)
        base = hx("#5d7499")
        if c in (1, 3) and hi_l > 0:
            base = mix(base, RED, hi_l)
        if c in (0, 2) and hi_r > 0:
            base = mix(base, CYAN, hi_r)
        pipe(cv, p, 28, base, a=a, prog=prog, glass=True)
    tp = spline([C_POINT, (746, 972), TURBO_C], 30)
    pipe(cv, tp, 40, hx("#5d7499"), a=a * eout(lin(t, T_PIPE, T_TURBO)), glass=True)
    # pulses
    if prog >= 1:
        for tf, c in fires(t - 1.3, t):
            path = (PATHS_EQ if mode_eq(tf) else PATHS_UNEQ)[c]
            Ln = path_len(path)
            dly = delay(c, tf)
            if t - tf > dly:
                continue
            d = (t - tf) / dly * Ln
            col = pulse_col(c)
            for j in range(9):
                dj = d - j * 16
                if dj < 0:
                    continue
                q, _ = point_at(path, dj)
                r = 11 - j
                aa = a * (1 - j / 9)
                cv.drawCircle(q[0], q[1], r * 2, paint(col, a=0.3 * aa, blur=r))
                cv.drawCircle(q[0], q[1], r, paint(col, a=aa))
    ka = eout(lin(t, T_TURBO - 0.1, T_TURBO + 0.25))
    if ka > 0:
        draw_turbo(cv, t, a * ka)
        for ta, c, tf in arrivals(t - 0.25, t):
            ks = 1 - (t - ta) / 0.25
            cv.drawCircle(C_POINT[0], C_POINT[1], 22 + 70 * (1 - ks), paint(YEL, a=a * 0.8 * ks, stroke=4))


def draw_bangs(cv, t, a):
    for tf, c in fires(t - 0.45, t):
        k = 1 - (t - tf) / 0.45
        s, z = CYLS[c]
        p = PJ(s * (HEAD_X + 28), -62, z)
        sz = eback(clamp((t - tf) / 0.12))
        draw_text(cv, "BANG", p[0], p[1] - 16, font("pop_b", 34 + 16 * sz), YEL, a=a * clamp(k), align="center", glow=8, glow_c=AMBER)


# ================================================================== timeline
PANEL = (150, 1228, 780, 112)


def draw_timeline(cv, t):
    k = win(t, T_BANG - 0.3, T_OUTRO - 0.1, 0.35, 0.3)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    gx, gy, gw, gh = PANEL
    brand.graph_box(cv, PANEL, "EXHAUST PULSES")
    span = 2.3
    x0 = gx + 118
    tw = gw - 126
    r1, r2 = gy + 30, gy + 90
    k2 = eout(lin(t, T_ARRIVE - 0.2, T_ARRIVE + 0.25))
    draw_text(cv, "LEAVE", gx - 6, r1 + 9, font("inter_xb", 24), CYAN, tracking=2)
    if k2 > 0:
        draw_text(cv, "ARRIVE", gx - 6, r2 + 9, font("inter_xb", 24), RED, a=k2, tracking=2)
        cv.drawLine(x0, r2, x0 + tw, r2, paint(hx("#3a4559"), a=k2, stroke=2))
    cv.drawLine(x0, r1, x0 + tw, r1, paint(hx("#3a4559"), stroke=2))
    X = lambda tt: x0 + tw * (1 - (t - tt) / span)
    for tf, c in fires(t - span, t):
        x = X(tf)
        cv.drawLine(x, r1 - 18, x, r1 + 18, paint(CYAN, stroke=6))
        cv.drawCircle(x, r1, 8, paint(INK))
    if k2 > 0:
        arr = [a_ for a_ in arrivals(t - span - 0.4, t)]
        for i, (ta, c, tf) in enumerate(arr):
            if ta >= t - span:
                x = X(ta)
                cc = pulse_col(c)
                cv.drawLine(x, r2 - 18, x, r2 + 18, paint(cc, a=k2, stroke=6))
                cv.drawCircle(x, r2, 8, paint(INK, a=k2))
        k3 = eout(lin(t, T_SHORT - 0.1, T_SHORT + 0.2))
        if k3 > 0 and t < T_RES + 0.6:
            for i in range(len(arr) - 1):
                a0, a1 = arr[i][0], arr[i + 1][0]
                if a0 < t - span:
                    continue
                g = a1 - a0
                cx = X((a0 + a1) / 2)
                if g < 0.78 * STEP:
                    draw_text(cv, "SHORT", cx, r2 + 42, font("inter_xb", 22), AMBER, a=k2 * k3, align="center", tracking=1.5)
                elif g > 1.22 * STEP:
                    draw_text(cv, "LONG", cx, r2 + 42, font("inter_xb", 22), RED, a=k2 * k3, align="center", tracking=1.5)
    cv.restore()


# ================================================================== top-of-screen status
def draw_top(cv, t):
    k = win(t, T_HOW + 0.1, T_OUTRO - 0.05, 0.3, 0.3)
    if k <= 0:
        return
    if t < T_RE:
        txt, c = "EVEN FIRING", CYAN
    elif t < T_ARRIVE:
        txt, c = "WHERE'S THE RUMBLE?", YEL
    elif t < T_EQ + 0.2:
        txt, c = "UNEVEN ARRIVAL", RED
    elif t < T_UNEQ:
        txt, c = "EQUAL LENGTH", GREEN
    else:
        txt, c = "UNEQUAL = RUMBLE", RED
    brand.status_pill(cv, k, txt, c)
    ka = eout(lin(t, T_BANG - 0.15, T_BANG + 0.2)) * win(t, T_HOW, T_RE, 0.3, 0.3)
    if ka > 0:
        brand.readout(cv, ka, "180°", "CRANK TURN PER BANG")
    brand.note(cv, "SLOWED · TIMING EXAGGERATED", k * eout(lin(t, T_PARTS, T_PARTS + 0.4)))


def draw_labels(cv, t):
    brand.label(cv, t, "OPPOSED PISTONS", view_pt(PJ(142, -38, -120), t), (620, 560), CYAN, T_PISTONS - 0.1, T_BANG - 0.1)
    brand.label(cv, t, "CRANK", view_pt(PJ(0, 0, -205), t), (300, 1030), YEL, T_CRANK - 0.2, T_PAPER + 0.1)
    if T_PARTS < t < T_KEY + 0.3:
        brand.label(cv, t, "TURBO", tuple(TURBO_C + (-32, 60)), (640, 1125), AMBER, T_TURBO - 0.1, T_UNDER - 0.2)
    brand.label(cv, t, "THE LONG WAY", (430, 925), (120, 1040), RED, T_UNDER - 0.1, T_ARRIVE - 0.2)
    brand.label(cv, t, "INCHES AWAY", (778, 860), (918, 760), CYAN, T_INCHES - 0.15, T_ARRIVE - 0.2, align="right")


def draw_keep_pills(cv, t):
    a = win(t, T_STI - 0.1, T_YEAR + 0.5, 0.25, 0.3)
    if a > 0:
        pill(cv, 540, 1130, "WRX STI: UNEQUAL THROUGH 2021", font("inter_xb", 29), INK, border=RED, a=a, align="center", tracking=1.5, dot=RED)
    b = win(t, T_BUY - 0.1, T_BRING + 0.7, 0.25, 0.3)
    if b > 0:
        pill(cv, 540, 1130, "UNEQUAL HEADERS, STILL ON SALE", font("inter_xb", 29), INK, border=YEL, a=b, align="center", tracking=1.5, dot=YEL)
    c = win(t, T_FIF - 0.15, T_LINED + 0.2, 0.25, 0.3)
    if c > 0:
        pill(cv, 540, 1130, "2015 WRX · TWIN SCROLL TURBO", font("inter_xb", 29), INK, border=GREEN, a=c, align="center", tracking=1.5, dot=GREEN)


# ================================================================== hook (world)
def draw_sedan(cv, x, y, s, t, a):
    """Generic four-door saloon, side view (no badges). Nose right, tailpipe left."""
    W_, H_ = 690 * s, 175 * s
    prof = np.array([[-1.0, 0.1], [-0.99, -0.26], [-0.87, -0.42], [-0.58, -0.47], [-0.46, -0.9], [0.2, -0.96], [0.42, -0.5],
                     [0.86, -0.42], [1.0, -0.22], [1.02, 0.12], [0.94, 0.24], [-0.95, 0.24]])
    body = np.stack([x + prof[:, 0] * W_ / 2, y - 62 * s + prof[:, 1] * H_], 1)
    pth = poly_path(spline(np.vstack([body, body[:1]]), 110))
    cv.drawPath(pth, paint(hx("#3b6fb5"), a=a * 0.42, stroke=14 * s, blur=14 * s))
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((x, y - H_ - 62 * s), (x, y + 30), [hx("#3a4a66"), hx("#1a2436"), hx("#0d1320")]))
    p.setAlphaf(a)
    cv.drawPath(pth, p)
    cv.drawPath(pth, paint(hx("#7f9ac2"), a=a * 0.8, stroke=2.5 * s))
    wp = np.array([[-0.52, -0.5], [-0.42, -0.84], [0.17, -0.88], [0.36, -0.52]])
    w = np.stack([x + wp[:, 0] * W_ / 2, y - 62 * s + wp[:, 1] * H_], 1)
    cv.drawPath(poly_path(spline(np.vstack([w, w[:1]]), 60)), paint(hx("#0a1220"), a=a))
    for wx in (-0.60, 0.62):
        cx, cy, r = x + wx * W_ / 2, y - 26 * s, 62 * s
        cv.drawCircle(cx, cy, r, paint(hx("#0a0f18"), a=a))
        cv.drawCircle(cx, cy, r, paint(hx("#3a4456"), a=a, stroke=5 * s))
        cv.drawCircle(cx, cy, r * 0.56, paint(hx("#5a6577"), a=a))
    wing = np.array([[x - 0.97 * W_ / 2, y - 62 * s - 0.56 * H_], [x - 0.72 * W_ / 2, y - 62 * s - 0.56 * H_]])
    cv.drawLine(*wing[0], *wing[1], paint(hx("#7f9ac2"), a=a, stroke=6 * s, cap=skia.Paint.kRound_Cap))
    for wx in (-0.93, -0.76):
        cv.drawLine(x + wx * W_ / 2, y - 62 * s - 0.56 * H_, x + wx * W_ / 2, y - 62 * s - 0.42 * H_, paint(hx("#5d7499"), a=a, stroke=4 * s))
    head = np.array([x + 0.95 * W_ / 2, y - 62 * s - 0.2 * H_])
    cv.drawCircle(head[0], head[1], 28 * s, paint(hx("#ffe9a8"), a=a * 0.55, blur=14 * s))
    tail = np.array([x - 0.97 * W_ / 2, y - 62 * s - 0.18 * H_])
    cv.drawCircle(tail[0], tail[1], 18 * s, paint(RED, a=a * 0.8, blur=10 * s))
    return np.array([x - 1.0 * W_ / 2, y - 56 * s + 0.2 * H_ * 0.0 + 8 * s])


def draw_hook(cv, t):
    if t > T_WHAT + 0.8:
        return
    a = clamp(1 - lin(t, T_WHAT + 0.15, T_WHAT + 0.55))
    zoom = 1 + 2.4 * ease(lin(t, T_WHAT - 0.1, T_WHAT + 0.55))
    cv.saveLayerAlpha(None, int(255 * a))
    look.night_sky(cv, horizon=1030, t=t)
    cv.drawRect(skia.Rect.MakeLTRB(0, 1030, 1080, 1920), paint(hx("#0b101a")))
    cv.drawRect(skia.Rect.MakeLTRB(0, 1030, 1080, 1034), paint(hx("#3b6fb5"), a=0.45))
    look.beam(cv, (880, 560), (760, 1120), 40, 420, a=0.22)
    cv.drawRect(skia.Rect.MakeXYWH(872, 560, 12, 560), paint(hx("#2b3548")))
    cv.drawCircle(878, 556, 22, paint(hx("#fff1c9"), a=0.9))
    look.bloom(cv, 878, 556, 110, hx("#ffd98a"), a=0.5)
    cv.save()
    cv.translate(620, 960)
    cv.scale(zoom, zoom)
    cv.translate(-620, -960)
    sh = 2.2 * math.sin(t * 73) * math.sin(t * 19)
    tp = draw_sedan(cv, 540, 1095 + sh, 1.05, t, 1.0)
    # exhaust rumble rings, uneven spacing (from the same pulse pattern)
    gaps = [0.0, STEP * 0.55, STEP * 1.45, STEP * 2.0]
    for cyc in range(8):
        for g in gaps:
            t_r = cyc * CYC * 0.32 + g * 0.32
            age = t - t_r
            if 0 < age < 1.1:
                r = 26 + 330 * age
                cv.drawArc(skia.Rect.MakeLTRB(tp[0] - r, tp[1] - r * 0.8, tp[0] + r, tp[1] + r * 0.8), 118, 124, False,
                           paint(AMBER, a=0.62 * (1 - age / 1.1), stroke=5.5))
    cv.drawCircle(tp[0] + 5, tp[1], 11, paint(hx("#0b101a")))
    cv.drawCircle(tp[0] + 5, tp[1], 11, paint(hx("#7f9ac2"), stroke=2.5))
    cv.restore()
    # BOXER ENGINE tag, crossed out on "It isn't."
    kb = win(t, T_BOXER0 - 0.1, T_MAKING - 0.1, 0.2, 0.3)
    if kb > 0:
        pill(cv, 590, 905, "BOXER ENGINE", font("inter_xb", 40), INK, border=CYAN, a=kb, align="center", tracking=3, dot=CYAN)
        kx = eout(lin(t, T_ISNT - 0.05, T_ISNT + 0.2))
        if kx > 0:
            w_ = 370 * kx
            cv.drawLine(590 - w_ / 2, 930, 590 + w_ / 2, 884, paint(RED, a=kb, stroke=11))
    cv.restore()
    brand.stamp(cv, t, "WHAT'S MAKING IT?", T_MAKING - 0.1, dur=1.4, center=(540, 1290), color=YEL, bg=hx("#2a2405"))


def draw(cv, t):
    kE = 1 - current.ending_k(t)
    cv.saveLayerAlpha(None, int(255 * clamp(kE)))
    draw_hook(cv, t)
    k_e = win(t, T_WHAT + 0.1, T_END + 0.2, 0.4, 0.3)
    draw_pipes(cv, t, k_e)
    cv.save()
    apply_view(cv, t)
    draw_engine(cv, t, k_e)
    draw_bangs(cv, t, k_e * win(t, T_HOW, T_RE, 0.2, 0.3))
    cv.restore()
    draw_labels(cv, t)
    draw_top(cv, t)
    draw_timeline(cv, t)
    draw_keep_pills(cv, t)
    if T_WHAT < t < T_HOW + 0.2:
        pill(cv, 540, 1240, "BOXER RUMBLE", font("inter_xb", 34), INK, border=RED, a=win(t, T_WHAT + 0.1, T_HOW + 0.2, 0.2, 0.3),
             align="center", tracking=3, dot=RED)
    sc = (540, 1130)
    brand.stamp(cv, t, "PERFECTLY EVEN", T_EVENLY - 0.05, dur=1.5, center=(540, 1130), color=GREEN, bg=hx("#07261a"))
    brand.stamp(cv, t, "SHOULD BE SMOOTH", T_PAPER, dur=1.7, center=(540, 1130), color=CYAN, bg=hx("#07202a"))
    brand.stamp(cv, t, "WHERE'S THE RUMBLE?", T_WHERE - 0.05, dur=1.5, center=(540, 1130), color=YEL, bg=hx("#2a2405"))
    brand.stamp(cv, t, "THAT'S THE RUMBLE", T_LUMPY - 0.05, dur=1.6, center=(540, 1130), color=RED)
    brand.stamp(cv, t, "PULSES LINED UP", T_LINED - 0.05, dur=1.5, center=(540, 1130), color=GREEN, bg=hx("#07261a"))
    brand.stamp(cv, t, "RUMBLE'S BACK", T_BRING - 0.05, dur=1.3, center=(540, 1130), color=RED)
    cv.restore()


# ================================================================== sound
SR = 48000
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")


def _rumble(dur, uneven, rpm=1050.0, seed=4):
    """Boxer exhaust from the pulse model: one decaying low thump per bang, at even or uneven arrival gaps."""
    from scipy import signal
    N = int(dur * SR)
    tt = np.arange(N) / SR
    x = np.zeros(N)
    rng = np.random.default_rng(seed)
    step = 60.0 / rpm / 2
    sh = step * (0.40 if uneven else 0.0)
    offs = [0.0, step, 2 * step + sh, 3 * step + sh]
    cyc = 4 * step
    b, a = signal.butter(2, [38 / (SR / 2), 460 / (SR / 2)], "band")
    t0 = -cyc
    while t0 < dur:
        for off in offs:
            tb = t0 + off
            j = int(max(tb, 0) * SR)
            if j >= N:
                continue
            n = min(N - j, int(0.09 * SR))
            e = np.exp(-np.arange(n) / (0.024 * SR))
            amp = rng.uniform(0.85, 1.1)
            x[j:j + n] += amp * e * (0.65 + 0.35 * rng.standard_normal(n) * 0.5)
        t0 += cyc
    x = signal.lfilter(b, a, x)
    n = int(0.08 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return (x / (np.abs(x).max() + 1e-9) * 0.85).astype(np.float32)


CUES = {
    "rumble_hook": (0.0, T_WHAT + 0.3, True),
    "rumble_even": (T_HOW, T_RE, False),
    "rumble_key": (T_LEAVE - 0.3, T_RES + 0.4, True),
    "rumble_smooth": (T_RES + 0.4, T_KEEP - 0.1, False),
    "rumble_back": (T_UNEQ, T_OUTRO + 0.3, True),
}


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, (t0, t1, un) in CUES.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), _rumble(max(t1 - t0, 0.5), un, seed=hash(name) & 1023), SR)


BEAT_ANCHOR = T_LUMPY
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    gains = {"rumble_hook": 0.75, "rumble_even": 0.45, "rumble_key": 0.75, "rumble_smooth": 0.42, "rumble_back": 0.6}
    sfx = [(CUES[n][0], n, gains[n]) for n in CUES]
    sfx += [(T_ISNT, "impact", 0.4), (T_MAKING - 0.1, "impact", 0.3), (T_WHAT + 0.05, "whoosh_big", 0.35), (T_EVENLY, "tick", 0.3),
            (T_PAPER, "whoosh_down", 0.2), (T_WHERE, "impact", 0.3), (T_EXH, "whoosh_up", 0.3), (T_TURBO, "clunk", 0.25),
            (T_UNDER, "whoosh_down", 0.25), (T_INCHES, "tick", 0.3), (T_ARRIVE, "impact_long", 0.38), (T_LUMPY, "impact", 0.35),
            (T_EQ, "whoosh_big", 0.3), (T_LINED, "tick", 0.3), (T_UNEQ, "whoosh_up", 0.3), (T_BRING, "impact", 0.3)]
    return {"build": (T_RE, T_KEY), "drop": (T_KEY, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.6}
