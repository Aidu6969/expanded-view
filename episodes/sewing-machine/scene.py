"""LOCKSTITCH visuals + sound plan. Every cue is tied to a narration word via F(line, word).

View: end-on cutaway of a lockstitch machine with a full rotary hook (hook axis toward the viewer, oblique
projection: the hook's plane is shown true-shape, depth recedes up-right). The fabric and throat plate are cut
along the seam line (z = 0) so the threads can be seen inside the cloth.

Mechanism model (one stitch = one unit of phase PHI):
  needle      tip_y = NEEDLE_C - NEEDLE_A * cos(2 pi phi)          (top at frac 0, bottom at frac 0.5)
  hook        theta = -90 deg + 720 deg * (phi - 0.6)              (2 turns per stitch; point at the needle at 0.6)
  loop        forms frac 0.50-0.60, caught at 0.60, carried around the bobbin case until it slips off at 1.00
  take-up     pays out thread 0.12-0.45, pulls the loop shut frac 0.00-0.09 of the next stitch
  feed dogs   rise 0.03-0.08, move the cloth one stitch 0.08-0.17 (needle is above the cloth then), drop, return
"""
import math

import numpy as np
import skia
from scipy.interpolate import PchipInterpolator

from ev import brand, current
from ev.current import tl
from ev.gfx import *

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
HOOK_OUT = current.hook_out

# ================================================================== geometry (profile coords: X right, Y down)
PJ = Proj(540, 0, 1.0, dx=0.5, dy=-0.35)   # oblique: X/Y true shape, z recedes up-right (nearer = smaller z)
FAB_Y, FAB_B = 700.0, 722.0                 # fabric top / bottom
FAB_MID = 711.0
PLATE_B = 738.0
STEP = 72.0                                 # stitch length on screen
NEEDLE_C, NEEDLE_A = 770.0, 170.0           # tip from 600 (top) to 940 (bottom)
NEEDLE_LEN = 280.0
EYE_UP = 16.0                               # eye centre above the tip
C = np.array([0.0, 1062.0])                 # hook / bobbin centre
R_CUP, R_CASE, R_BOB, R_PT = 150.0, 100.0, 62.0, 157.0
SLOT_ANG = math.radians(-58)
SLOT = C + R_CASE * np.array([math.cos(SLOT_ANG), math.sin(SLOT_ANG)])
TU_PIV = np.array([160.0, 455.0])           # take-up lever pivot (inside the head)
TU_LEN = 150.0
HEAD = (-300.0, 440.0, 250.0, 482.0)        # machine head block X0, Y0, X1, Y1
TOP_TH, BOT_TH = CYAN, RED

# ================================================================== cue times
T_PANEL = (L("problem")["start"] - 0.25, L("parts")["start"] + 0.05)
T_MECH_OUT = (L("problem")["start"] - 0.3, L("problem")["start"] + 0.25)
T_MECH_BACK = (L("parts")["start"] - 0.25, L("parts")["start"] + 0.35)
T_HEAD = F("parts", "up") - 0.3
T_SNAG = F("key", "snags")
T_LOCK = F("tight", "lock")
T_TWICE = F("feed", "twice")

R_FRAC = 0.18      # resting phase: cloth fed, needle tip just above the cloth


def _phase_keys():
    keys = []
    rate_fast = 1.6
    t_slow = L("what")["start"] + 0.6
    p = 0.0
    t = 0.0
    while t < t_slow:                          # full speed under the hook
        keys.append((t, p))
        t += 0.25
        p += 0.25 * rate_fast
    # decelerate to rest (needle up) during "what"
    N0 = math.floor(p) + 2
    t_rest = F("what", "underneath") - 0.4
    keys.append((t_slow + 0.9, p + 1.1))
    keys.append((t_rest, N0 + R_FRAC))
    N = N0
    keys.append((F("down", "pushes") - 0.1, N + R_FRAC))
    keys.append((F("down", "fabric.", which="end"), N + 0.5))
    keys.append((F("down", "rise,", which="end") - 0.05, N + 0.52))
    keys.append((F("down", "loop.", which="end"), N + 0.585))
    keys.append((T_SNAG - 0.15, N + 0.586))
    keys.append((T_SNAG + 0.25, N + 0.615))
    keys.append((F("key", "case.", which="end"), N + 0.965))
    keys.append((F("key", "wrapped"), N + 0.975))
    keys.append((F("tight", "yanks") - 0.15, N + 0.99))
    keys.append((F("tight", "shut,", which="end"), N + 1.09))
    keys.append((F("feed", "feed") - 0.1, N + 1.095))
    keys.append((F("feed", "stitch,", which="end"), N + 1.0 + R_FRAC))
    t_again = F("feed", "again.", which="end")
    keys.append((t_again, N + 2.0 + R_FRAC))
    t_m = F("feed", "hook") - 0.1
    keys.append((t_m, N + 2.0 + R_FRAC + (t_m - t_again) * 0.9))
    p = keys[-1][1]
    t = t_m
    while t < T_TOTAL + 0.5:                   # ~0.55 stitch/s: you can count two hook turns per stitch
        rate = 0.55 if t < L("outro")["start"] else 0.55 + 1.2 * min(1.0, (t - L("outro")["start"]) / 1.5)
        t += 0.25
        p += 0.25 * rate
        keys.append((t, p))
    ts = np.array([k[0] for k in keys])
    ps = np.array([k[1] for k in keys])
    o = np.argsort(ts)
    return PchipInterpolator(ts[o], ps[o]), N


_PHI, N_EXPL = _phase_keys()


def phi_at(t):
    return float(_PHI(max(0.0, t)))


def rate_at(t):
    return (phi_at(t + 1 / 60) - phi_at(t - 1 / 60)) * 30


# ------------------------------------------------------------------ mechanism functions of phase
def needle_tip(phi):
    return NEEDLE_C - NEEDLE_A * math.cos(2 * math.pi * phi)


def hook_theta(phi):
    return math.radians(-90 + 720 * (phi - 0.6))


def feed_offset(phi):
    n = math.floor(phi)
    f = phi - n
    return STEP * (n + ease(clamp((f - 0.08) / 0.09)))


def hole_x(k, phi):
    """screen-relative X of hole k (needle at X = 0)."""
    return STEP * (k + 1) - feed_offset(phi) - STEP


def takeup_k(phi):
    f = phi % 1.0
    if f < 0.09:
        return ease(f / 0.09)
    if f < 0.12:
        return 1.0
    if f < 0.45:
        return 1 - ease((f - 0.12) / 0.33)
    return 0.0


def feed_dog(phi):
    """(dx, rise) of the feed dog: rise 1 = teeth above the plate."""
    f = phi % 1.0
    rise = ease(clamp((f - 0.03) / 0.05)) * (1 - ease(clamp((f - 0.17) / 0.06)))
    if f < 0.08:
        dx = 0.0
    elif f < 0.17:
        dx = -STEP * ease((f - 0.08) / 0.09)
    elif f < 0.25:
        dx = -STEP
    else:
        dx = -STEP * (1 - ease(clamp((f - 0.25) / 0.6)))
    return dx, rise


def stitch_stage(phi):
    """For the stitch in progress: (k, stage, u). stage: none | loop | caught | tight."""
    n = math.floor(phi)
    f = phi - n
    if f < 0.09:            # previous stitch is being pulled shut
        return n - 1, "tight", f / 0.09
    if 0.5 <= f < 0.6:
        return n, "loop", (f - 0.5) / 0.1
    if f >= 0.6:
        return n, "caught", (f - 0.6) / 0.4
    return n, "none", 0.0


def locked(k, phi):
    return phi >= k + 1.09


def check_physics():
    """Feed only while the needle is clear of the cloth; hook point passes the needle exactly at the catch."""
    bad = 0
    for i in range(4000):
        phi = i / 1000
        f = phi % 1
        moving = 0.08 < f < 0.17
        if moving and needle_tip(phi) > FAB_Y:
            bad += 1
    return bad


# ================================================================== camera
def zoom_k(t):
    return ease(lin(t, F("tight", "two") - 0.2, T_LOCK + 0.2)) * (1 - ease(lin(t, F("feed", "feed") - 0.6,
                                                                            F("feed", "feed") + 0.3)))


def cam(t):
    """(scale, cx, cy): zoom around a point. Hook: slightly closer; lock: into the cloth."""
    z_hook = BASE * (1.0 + 0.08 * (1 - ease(lin(t, HOOK_OUT - 0.2, L("what")["start"] + 1.0))))
    zl = zoom_k(t)
    s = z_hook * (1 + 0.6 * zl)
    cx = 540.0
    cy = mix_f(CAM_Y, FAB_MID, zl)
    sh = 130.0 * zl                                    # cloth moves to mid-screen while zoomed
    end = current.ending_k(t)
    s *= 1 - 0.15 * end
    return s, cx, cy, sh - 100 * end


BASE, CAM_Y = 1.25, 760.0


def mix_f(a, b, k):
    return a + (b - a) * k


def to_screen(X, Y, z, t):
    p = PJ(X, Y, z)
    s, cx, cy, sh = cam(t)
    return np.array([cx + (p[0] - cx) * s, cy + (p[1] - cy) * s + sh])


# ================================================================== drawing helpers
def rod(cv, x, y0, y1, r, base, a=1.0):
    """Vertical round rod with cylinder shading (screen coords)."""
    if y1 <= y0:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((x - r, 0), (x + r, 0), [shade(base, 0.55), shade(base, 1.3), shade(base, 0.95),
                                                  shade(base, 0.45)], [0, 0.35, 0.6, 1]))
    if a < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cv.drawRect(skia.Rect.MakeLTRB(x - r, y0, x + r, y1), p)
    cv.drawRect(skia.Rect.MakeLTRB(x - r, y0, x + r, y1), paint(shade(base, 0.3), stroke=1.5))
    if a < 1:
        cv.restore()


def thread(cv, pts, c, a=1.0, w=4.0, glow=0.0):
    pts = np.asarray(pts, float)
    if len(pts) < 2 or a <= 0:
        return
    path = poly_path(pts, close=False)
    cv.drawPath(path, paint(hx("#05070b"), a=0.7 * a, stroke=w + 3, cap=skia.Paint.kRound_Cap,
                            join=skia.Paint.kRound_Join))
    if glow > 0:
        cv.drawPath(path, paint(c, a=0.5 * a * glow, stroke=w * 3, blur=6))
    cv.drawPath(path, paint(c, a=a, stroke=w, cap=skia.Paint.kRound_Cap, join=skia.Paint.kRound_Join))


def P(X, Y, z=0.0):
    return PJ(X, Y, z)


def arc_pts(c, r, a0, a1, z, n=40):
    a = np.linspace(a0, a1, n)
    return PJ(c[0] + r * np.cos(a), c[1] + r * np.sin(a), np.full(n, z))


def beak_prof(theta):
    """Hook beak: a tapering horn on the cup rim, sharp point leading at angle theta (clockwise rotation)."""
    a = np.linspace(theta - math.radians(70), theta, 18)
    outer = np.stack([C[0] + (R_CUP + 4 + 3 * np.linspace(0, 1, 18)) * np.cos(a),
                      C[1] + (R_CUP + 4 + 3 * np.linspace(0, 1, 18)) * np.sin(a)], 1)
    inner_r = R_CUP - 22 + 22 * np.linspace(0, 1, 18) ** 1.4
    inner = np.stack([C[0] + inner_r * np.cos(a), C[1] + inner_r * np.sin(a)], 1)[::-1]
    tip = C + R_PT * np.array([math.cos(theta + 0.05), math.sin(theta + 0.05)])
    return np.vstack([outer, [tip], inner])


# ================================================================== threads (all in profile coords, then PJ)
def loop_paths(phi):
    """Return (back_leg, front_leg) screen polylines of the needle-thread loop below the plate, or None."""
    k, stage, u = stitch_stage(phi)
    tip = needle_tip(phi)
    eye_y = tip - EYE_UP
    H = np.array([0.0, PLATE_B])
    if stage == "loop":
        s = ease(u)
        top = np.array([3.0, max(eye_y, PLATE_B)])
        w, h = 6 + 18 * s, 10 + 26 * s
        # teardrop hanging from the eye, bulging toward the hook side (right)
        tt = np.linspace(0, np.pi, 24)
        right = np.stack([4 + w * np.sin(tt), top[1] + h * (1 - np.cos(tt)) / 2], 1)
        return None, PJ(right[:, 0], right[:, 1], -2.0)
    if stage == "caught":
        th = -math.pi / 2 + 4 * math.pi * 0.4 * u          # unwrapped angle since the catch
        pt = C + R_PT * np.array([math.cos(th), math.sin(th)]) * 0.985
        A = np.array([2.0, eye_y]) if eye_y > PLATE_B else H
        # back leg: down to the case top, around the case rim (behind it), to the point
        a0 = -math.pi / 2
        arc = np.stack([C[0] + (R_CASE + 26) * np.cos(np.linspace(a0, th, 48)),
                        C[1] + (R_CASE + 26) * np.sin(np.linspace(a0, th, 48))], 1)
        back = np.vstack([H, arc, pt])
        front = np.vstack([A, pt])
        return PJ(back[:, 0], back[:, 1], 8.0), PJ(front[:, 0], front[:, 1], -30.0)
    if stage == "tight":
        th = -math.pi / 2 + 4 * math.pi * 0.4
        pt = C + R_PT * np.array([math.cos(th), math.sin(th)]) * 0.985
        arc = np.stack([C[0] + (R_CASE + 26) * np.cos(np.linspace(-math.pi / 2, th, 48)),
                        C[1] + (R_CASE + 26) * np.sin(np.linspace(-math.pi / 2, th, 48))], 1)
        back0 = resample_poly(np.vstack([H, arc, pt]), 60)
        front0 = resample_poly(np.vstack([H, pt]), 60)
        I = interlock_point(phi)
        e = ease(clamp(u * 1.25))
        tgt_b = resample_poly(np.vstack([H, I + [4, 6], I]), 60)
        tgt_f = resample_poly(np.vstack([H, I + [-4, 6], I]), 60)
        back = back0 + (tgt_b - back0) * e
        front = front0 + (tgt_f - front0) * e
        return PJ(back[:, 0], back[:, 1], 8.0 * (1 - e)), PJ(front[:, 0], front[:, 1], -30.0 * (1 - e))
    return None, None


def resample_poly(pts, n):
    pts = np.asarray(pts, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1)


def interlock_point(phi):
    """Where the top thread grips the bobbin thread while the stitch is pulled shut (profile coords)."""
    k, stage, u = stitch_stage(phi)
    I0 = SLOT + (np.array([-STEP, FAB_B + 2]) - SLOT) * 0.45
    hole = np.array([hole_x(k, phi), FAB_MID])
    return I0 + (hole - I0) * ease(clamp((u - 0.35) / 0.65))


# ================================================================== scene blocks
def mech_alpha(t):
    a_in = ease(lin(t, -0.05, 0.25))
    out = ease(lin(t, *T_MECH_OUT)) * (1 - ease(lin(t, *T_MECH_BACK)))
    return a_in * (1 - out) * (1 - 0.85 * current.ending_k(t))


def draw_hook_assembly(cv, t, phi, v):
    th = hook_theta(phi)
    rate = abs(rate_at(t))
    cup_c = hx("#5d6879")
    # cup (rotating basket) behind the bobbin case
    extrude(cv, PJ, circle_prof(*C, R_CUP, 72), 10, 70, cup_c, rim=RED if v["hl_hook"] > 0.01 else None,
            rim_w=3 * v["hl_hook"], rim_glow=v["hl_hook"])
    fc = PJ(*C, 10)
    for i in range(3):                     # rotating windows show the turning
        a = th + i * 2 * math.pi / 3 + 0.6
        a_arc = np.linspace(a - 0.42, a + 0.42, 16)
        pts = np.vstack([np.stack([fc[0] + 140 * np.cos(a_arc), fc[1] + 140 * np.sin(a_arc)], 1),
                         np.stack([fc[0] + 112 * np.cos(a_arc[::-1]), fc[1] + 112 * np.sin(a_arc[::-1])], 1)])
        cv.drawPath(poly_path(pts), paint(hx("#262e3b")))
        cv.drawPath(poly_path(pts), paint(hx("#7d899b"), a=0.6, stroke=1.5))
    # turning motion blur ring at speed
    if rate > 0.8:
        cv.drawPath(poly_path(arc_pts(C, R_PT - 6, 0, 2 * math.pi, 0, 72)),
                    paint(hx("#c9d0db"), a=clamp((rate - 0.8) / 1.5) * 0.35, stroke=8))
    if v["back"] is not None:
        thread(cv, v["back"], TOP_TH, a=v["thread_a"] * 0.85, w=4.6, glow=v["loop_glow"])
    # bobbin case (held still) + bobbin
    case_c = hx("#aab3c2")
    extrude(cv, PJ, circle_prof(*C, R_CASE, 72), -25, 5, case_c,
            rim=YEL if v["hl_case"] > 0.01 else None, rim_w=3 * v["hl_case"], rim_glow=v["hl_case"])
    cf = PJ(*C, -25)
    tab = np.array([[-14, -R_CASE - 14], [14, -R_CASE - 14], [10, -R_CASE + 4], [-10, -R_CASE + 4]]) + C
    extrude(cv, PJ, tab, -25, 5, hx("#8c97a8"))          # tab that stops the case from turning
    cv.drawCircle(cf[0], cf[1], R_BOB + 6, paint(hx("#1a2130")))
    used = phi * 0.05
    for r in np.arange(26, R_BOB, 3.0):                 # thread wound on the bobbin
        cv.drawCircle(cf[0], cf[1], r, paint(shade(BOT_TH, 0.55 + 0.25 * ((r // 3) % 2)), stroke=3.2))
    for i in range(6):
        a = i * math.pi / 3 + used
        cv.drawLine(cf[0] + 18 * math.cos(a), cf[1] + 18 * math.sin(a), cf[0] + (R_BOB - 2) * math.cos(a),
                    cf[1] + (R_BOB - 2) * math.sin(a), paint(hx("#ffd0d0"), a=0.18, stroke=2))
    cv.drawCircle(cf[0], cf[1], 22, paint(hx("#c9d0db")))
    cv.drawCircle(cf[0], cf[1], 9, paint(hx("#3a4456")))
    # bobbin thread: bobbin -> tension slot
    sp = PJ(*SLOT, -25)
    bo = cf + (R_BOB - 4) * np.array([math.cos(SLOT_ANG - 0.5), math.sin(SLOT_ANG - 0.5)])
    thread(cv, [bo, sp], BOT_TH, a=v["thread_a"], w=4.6, glow=v["bob_glow"])
    cv.drawCircle(sp[0], sp[1], 6, paint(hx("#2a3140")))
    # beak (hook point), with ghost copies at speed
    nghost = 3 if rate > 0.8 else 0
    dth = rate * 4 * math.pi / 30
    for g in range(nghost, 0, -1):
        extrude(cv, PJ, beak_prof(th - dth * g / (nghost + 1)), -10, 30, hx("#c9d0db"),
                alpha=0.22 * (1 - g / (nghost + 1)), outline=False)
    extrude(cv, PJ, beak_prof(th), -10, 30, hx("#c9d0db"),
            rim=RED if v["hl_point"] > 0.01 else None, rim_w=4.2 * v["hl_point"], rim_glow=v["hl_point"])


def draw_plate_and_feed(cv, t, phi, v):
    dx, rise = feed_dog(phi)
    # feed dog: toothed block under the plate
    y_top = PLATE_B + 10 - (PLATE_B + 10 - FAB_B + 5) * rise
    x0, x1 = -150 + dx, -36 + dx
    teeth = [(x0, y_top + 40), (x0, y_top + 8)]
    n = 6
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        teeth += [(xa, y_top + 8), (xb - 4, y_top), (xb, y_top + 8)]
    teeth += [(x1, y_top + 40)]
    fd_c = mix(hx("#7f8a9c"), hx("#ffffff"), 0.3 * v["hl_feed"])
    extrude(cv, PJ, np.array(teeth), 0, 60, fd_c, rim=YEL if v["hl_feed"] > 0.01 else None,
            rim_w=2.6 * v["hl_feed"], rim_glow=v["hl_feed"])
    # throat plate (cut at z = 0): slot for the feed dog, hole for the needle
    for xa, xb in ((-420, -236), (-26, -7), (7, 420)):
        extrude(cv, PJ, np.array([[xa, FAB_B], [xb, FAB_B], [xb, PLATE_B], [xa, PLATE_B]]), 0, 95, hx("#9aa4b4"))


def draw_fabric(cv, t, phi, v):
    off = feed_offset(phi)
    fab = hx("#41557e")
    extrude(cv, PJ, np.array([[-560, FAB_Y], [560, FAB_Y], [560, FAB_B], [-560, FAB_B]]), 0, 75, fab,
            face_hi=1.05, face_lo=0.8)
    # weave lines on the top face (they travel with the cloth)
    for i in range(-30, 31):
        u = i * 24 - (off % 24)
        if -540 < u < 540:
            a = PJ(u, FAB_Y, 2)
            b = PJ(u, FAB_Y, 74)
            cv.drawLine(a[0], a[1], b[0], b[1], paint(hx("#7f95c4"), a=0.16, stroke=2))
    # cut face hatch
    for i in range(-30, 31):
        u = i * 24 - (off % 24)
        if -548 < u < 548:
            a = PJ(u, FAB_Y + 3, 0)
            cv.drawLine(a[0], a[1], a[0] + 8, a[1] + 16, paint(hx("#9fb3dc"), a=0.10, stroke=2))


def draw_presser_foot(cv, t, v):
    foot = np.array([[-95, FAB_Y - 2], [70, FAB_Y - 2], [90, FAB_Y - 14], [70, FAB_Y - 20], [-95, FAB_Y - 20]])
    extrude(cv, PJ, foot, 8, 60, hx("#8f9aab"), alpha=0.9)
    extrude(cv, PJ, np.array([[-70, HEAD[3]], [-50, HEAD[3]], [-50, FAB_Y - 20], [-70, FAB_Y - 20]]), 25, 45,
            hx("#6b7688"), alpha=v["head"])


def draw_stitches(cv, t, phi, v):
    """Finished stitches in the cut face: top thread on top, bobbin thread underneath, locked mid-cloth."""
    a = v["thread_a"]
    n = math.floor(phi)
    k_cur, stage, u = stitch_stage(phi)
    yt, yb = FAB_Y - 3, FAB_B + 3
    # top thread along the top of the cloth, through each hole (vertical joins)
    for k in range(n - 12, n + 1):
        x = hole_x(k, phi)
        if x < -560 or not locked(k, phi):
            continue
        xp = hole_x(k - 1, phi)
        seg_t = [P(xp, yt), P(x, yt)]
        thread(cv, seg_t, TOP_TH, a=a, w=4.6)
        thread(cv, [P(xp, yb), P(x, yb)], BOT_TH, a=a, w=4.6, glow=0)
        # interlock inside the cloth
        thread(cv, [P(x, yt), P(x - 1, FAB_MID - 1)], TOP_TH, a=a, w=4.0)
        thread(cv, [P(x, yb), P(x + 1, FAB_MID + 1)], BOT_TH, a=a, w=4.0)
        g = lin(phi, k + 1.09, k + 1.6)
        fresh = 1 - g
        q = P(x, FAB_MID)
        cv.drawCircle(q[0], q[1], 5, paint(YEL, a=a * (0.35 + 0.65 * fresh)))
        if fresh > 0:
            cv.drawCircle(q[0], q[1], 14, paint(YEL, a=0.5 * a * fresh, blur=6))


def draw_live_threads(cv, t, phi, v):
    """Needle thread from the newest hole up to the needle eye, the loop, and the bobbin thread to the cloth."""
    a = v["thread_a"]
    n = math.floor(phi)
    tip = needle_tip(phi)
    eye = np.array([0.0, tip - EYE_UP])
    k_cur, stage, u = stitch_stage(phi)
    # newest hole the needle has gone through
    kh = n if phi >= n + 0.21 else n - 1
    xh = hole_x(kh, phi)
    xprev = hole_x(kh - 1, phi)
    yt = FAB_Y - 3
    # the top thread laid on the cloth from the last locked hole to the newest hole
    if not locked(kh, phi):
        thread(cv, [P(xprev, yt), P(xh, yt)], TOP_TH, a=a, w=4.6, glow=v["top_glow"])
    # stitch-side leg: from the newest hole down to the eye (needle in the cloth) or up to it
    if eye[1] > FAB_Y:
        if stage in ("none", "loop"):
            thread(cv, [P(xh - 3, yt), P(-3, max(eye[1], FAB_Y))], TOP_TH, a=a, w=4.6, glow=v["top_glow"])
    else:
        thread(cv, [P(xh, yt), P(-3, eye[1] + 2)], TOP_TH, a=a, w=4.6, glow=v["top_glow"])
    if stage in ("caught", "tight"):
        thread(cv, [P(xh, yt), P(0, PLATE_B)], TOP_TH, a=a, w=4.6, glow=v["loop_glow"])
    # bobbin thread: tension slot -> (interlock) -> underside of the last locked hole
    sp = P(*SLOT, -25)
    kl = kh if locked(kh, phi) else kh - 1
    xl = hole_x(kl, phi)
    if stage == "tight":
        I = interlock_point(phi)
        pI = P(*I)
        thread(cv, [sp, pI, P(xl, FAB_B + 3)], BOT_TH, a=a, w=4.6, glow=v["bob_glow"])
    else:
        thread(cv, [sp, P(xl + 1, FAB_B + 3)], BOT_TH, a=a, w=4.6, glow=v["bob_glow"])


def draw_front_loop(cv, v):
    if v["front"] is not None:
        thread(cv, v["front"], TOP_TH, a=v["thread_a"], w=4.8, glow=v["loop_glow"])


def draw_needle(cv, t, phi, v):
    tip = needle_tip(phi)
    x0 = 540.0
    top_bar = 520.0 - 42.0 * v["head"]
    clamp_y = tip - NEEDLE_LEN
    # needle bar from the head down to the clamp
    if clamp_y > top_bar:
        rod(cv, x0, top_bar, clamp_y, 13, hx("#9aa6b8"))
    rr = skia.Rect.MakeLTRB(x0 - 19, clamp_y - 6, x0 + 19, clamp_y + 26)
    if clamp_y + 26 > top_bar:
        cv.save()
        cv.clipRect(skia.Rect.MakeLTRB(0, top_bar, 1080, 1920))
        cv.drawRect(rr, paint(hx("#6b7688")))
        cv.drawRect(rr, paint(hx("#2a313e"), stroke=2))
        cv.restore()
    # shank + blade + tip
    y_sh = max(clamp_y + 26, top_bar)
    if clamp_y + 70 > y_sh:
        rod(cv, x0, y_sh, clamp_y + 70, 8, hx("#c2cad6"))
    rod(cv, x0, max(clamp_y + 70, top_bar), tip - 24, 5, hx("#dfe5ee"))
    path = skia.Path()
    path.moveTo(x0 - 5, tip - 24); path.lineTo(x0 + 5, tip - 24); path.lineTo(x0 + 1, tip); path.lineTo(x0 - 1, tip)
    path.close()
    cv.drawPath(path, paint(hx("#dfe5ee")))
    # eye (right at the point) with the thread through it
    ey = tip - EYE_UP
    hl = v["hl_eye"]
    if hl > 0:
        cv.drawCircle(x0, ey, 22, paint(YEL, a=0.55 * hl, blur=8))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x0 - 2.4, ey - 7, x0 + 2.4, ey + 7), 2.4, 2.4, paint(hx("#0b0f16")))
    cv.drawCircle(x0, ey, 3.2, paint(TOP_TH, a=v["thread_a"]))
    # needle-side thread running up the front groove to the bar guide
    gy = max(clamp_y + 12, top_bar)
    thread(cv, [(548.0, gy), (546.0, ey)], TOP_TH, a=v["thread_a"], w=4.0, glow=v["tu_glow"])
    return ey


def draw_head(cv, t, phi, v):
    k = v["head"]
    if k <= 0:
        return
    tk = takeup_k(phi)
    # take-up lever eye height: low = paying out thread, high = pulled tight
    y_eye = 482 - 78 * tk
    s = clamp((y_eye - TU_PIV[1]) / TU_LEN, -1, 1)
    ang = math.asin(s)
    eye = TU_PIV + TU_LEN * np.array([-math.cos(ang), s])
    tip = needle_tip(phi)
    clamp_y = tip - NEEDLE_LEN
    cv.saveLayerAlpha(None, int(255 * k))
    x0, y0, x1, y1 = HEAD
    head = np.array([[x0, y0 + 30], [x0 + 30, y0], [x1, y0], [x1, y1], [x0, y1]])
    extrude(cv, PJ, head, -45, 70, hx("#3d4a60"), face_hi=1.12, face_lo=0.7)
    # needle-bar bushing
    b = P(0, y1 - 2, -45)
    cv.drawRect(skia.Rect.MakeLTRB(b[0] - 22, b[1] - 10, b[0] + 22, b[1] + 4), paint(hx("#2a3240")))
    # thread: spool (off right) -> tension discs -> take-up eye -> guide -> needle bar guide -> eye
    ten = P(225, 462, -46)
    eye_s = P(eye[0], eye[1], -60)
    guide = P(30, y1 - 8, -46)
    bar_g = np.array([548.0, max(clamp_y + 12, y1 + 6)])
    path_pts = [np.array([900.0, 470.0]), ten, eye_s, guide, bar_g]
    thread(cv, path_pts, TOP_TH, a=v["thread_a"], w=4.2, glow=v["tu_glow"])
    # tension discs
    for dz in (0, 1):
        cv.drawCircle(ten[0] + 6 * dz, ten[1] - 4 * dz, 22, paint(hx("#9aa6b8") if dz else hx("#c2cad6")))
        cv.drawCircle(ten[0] + 6 * dz, ten[1] - 4 * dz, 22, paint(hx("#2a313e"), stroke=2))
    # take-up lever (pivot inside the head, sticking out of a slot)
    piv = P(*TU_PIV, -46)
    arm = np.array([TU_PIV + 14 * np.array([math.sin(ang), -math.cos(ang)]),
                    eye + 9 * np.array([math.sin(ang), -math.cos(ang)]),
                    eye - 9 * np.array([math.sin(ang), -math.cos(ang)]),
                    TU_PIV - 14 * np.array([math.sin(ang), -math.cos(ang)])])
    lev_c = mix(hx("#b7c0cd"), hx("#ffffff"), 0.25 * v["hl_tu"])
    extrude(cv, PJ, arm, -62, -48, lev_c, rim=RED if v["hl_tu"] > 0.01 else None, rim_w=3 * v["hl_tu"],
            rim_glow=v["hl_tu"])
    cv.drawCircle(piv[0], piv[1], 13, paint(hx("#5d6879")))
    cv.drawCircle(piv[0], piv[1], 5, paint(hx("#1a2130")))
    cv.drawCircle(eye_s[0], eye_s[1], 11, paint(lev_c))
    cv.drawCircle(eye_s[0], eye_s[1], 11, paint(hx("#2a313e"), stroke=2))
    cv.drawCircle(eye_s[0], eye_s[1], 4.5, paint(hx("#0b0f16")))
    cv.restore()


# ------------------------------------------------------------------ visibility / highlight schedule
def vis(t, phi):
    v = {}
    v["head"] = eout(lin(t, T_HEAD, T_HEAD + 0.5))
    v["thread_a"] = 1.0
    v["top_glow"] = win(t, F("what", "top") - 0.2, F("what", "bobbin") - 0.2, 0.2, 0.3)
    v["bob_glow"] = max(win(t, F("what", "bobbin") - 0.2, L("what")["end"] + 0.3, 0.2, 0.3),
                        win(t, F("key", "bottom") - 0.2, L("tight")["start"], 0.2, 0.3))
    v["hl_hook"] = win(t, F("parts", "spinning") - 0.1, F("parts", "case.") + 0.3, 0.2, 0.3)
    v["hl_case"] = max(win(t, F("parts", "bobbin") - 0.1, F("parts", "up") + 0.1, 0.2, 0.3),
                       win(t, F("key", "around") - 0.1, F("key", "case.", which="end") + 0.3, 0.2, 0.3))
    v["hl_point"] = win(t, F("key", "point") - 0.15, F("key", "drags") + 0.3, 0.15, 0.3)
    v["hl_tu"] = max(win(t, F("parts", "take") - 0.1, L("parts")["end"] + 0.2, 0.2, 0.3),
                     win(t, F("tight", "take") - 0.1, F("tight", "shut,") + 0.3, 0.2, 0.3))
    v["tu_glow"] = v["hl_tu"] * 0.6
    v["hl_feed"] = win(t, F("feed", "feed") - 0.1, F("feed", "stitch,") + 0.4, 0.2, 0.3)
    v["hl_eye"] = win(t, F("down", "needle") - 0.1, F("down", "fabric.") + 0.2, 0.2, 0.3)
    v["loop_glow"] = max(win(t, F("down", "loop.") - 0.25, F("key", "snags") + 0.6, 0.2, 0.3),
                         win(t, F("key", "wrapped") - 0.15, L("key")["end"] + 0.2, 0.2, 0.3))
    v["back"], v["front"] = loop_paths(phi)
    return v


def draw_mechanism(cv, t):
    a = mech_alpha(t)
    if a <= 0.004:
        return
    phi = phi_at(t)
    v = vis(t, phi)
    s, cx, cy, sh = cam(t)
    cv.save()
    cv.translate(cx, cy + sh)
    cv.scale(s, s)
    cv.translate(-cx, -cy)
    cv.saveLayerAlpha(None, int(255 * a))
    zl = zoom_k(t)
    if zl > 0:
        cv.saveLayerAlpha(None, int(255 * (1 - 0.75 * zl)))
    draw_hook_assembly(cv, t, phi, v)
    if zl > 0:
        cv.restore()
    draw_plate_and_feed(cv, t, phi, v)
    draw_fabric(cv, t, phi, v)
    draw_presser_foot(cv, t, v)
    draw_stitches(cv, t, phi, v)
    draw_live_threads(cv, t, phi, v)
    draw_front_loop(cv, v)
    draw_needle(cv, t, phi, v)
    if zl > 0:
        cv.saveLayerAlpha(None, int(255 * (1 - 0.7 * zl)))
    draw_head(cv, t, phi, v)
    if zl > 0:
        cv.restore()
    cv.restore()
    cv.restore()


# ================================================================== PROBLEM: hand needle vs machine needle
def draw_panels(cv, t):
    if not (T_PANEL[0] <= t <= T_PANEL[1] + 0.1):
        return
    out = ease(lin(t, T_PANEL[1] - 0.5, T_PANEL[1]))
    t_m = F("problem", "machine") - 0.2
    specs = [dict(y=540, c=CYAN, title="BY HAND", tin=T_PANEL[0] + 0.1),
             dict(y=960, c=RED, title="SEWING MACHINE", tin=t_m)]
    for i, sp in enumerate(specs):
        k = eout(lin(t, sp["tin"], sp["tin"] + 0.45))
        if k <= 0:
            continue
        a = k * (1 - out)
        dx = (1 - k) * 240 + out * (-120 if i == 0 else 120)
        x0, y0 = 60 + dx, sp["y"]
        cv.saveLayerAlpha(None, int(255 * a))
        brand.panel(cv, x0, y0, 880, 380, sp["title"], sp["c"])
        yf = y0 + 230
        # cloth strip (side view)
        cloth = skia.Rect.MakeLTRB(x0 + 50, yf - 9, x0 + 450, yf + 9)
        cv.drawRect(cloth, paint(hx("#41557e")))
        cv.drawRect(cloth, paint(hx("#7f95c4"), a=0.6, stroke=2))
        if i == 0:
            draw_hand_needle(cv, t - sp["tin"], x0, yf)
            kb = eout(lin(t, F("problem", "whole") - 0.1, F("problem", "whole") + 0.25))
            brand.bullet(cv, x0 + 490 + (1 - kb) * 30, y0 + 160, "Whole needle", True, a=kb, size=30)
            draw_text(cv, "goes through", x0 + 528 + (1 - kb) * 30, y0 + 204, font("inter_b", 30), INK, a=kb)
            kc = eout(lin(t, F("problem", "side.") - 0.1, F("problem", "side.") + 0.25))
            brand.bullet(cv, x0 + 490 + (1 - kc) * 30, y0 + 270, "Eye at the back", True, a=kc, size=30)
        else:
            ey = draw_machine_needle(cv, t - sp["tin"], x0, yf, eout(lin(t, F("problem", "eye") - 0.1,
                                                                       F("problem", "eye") + 0.3)))
            kb = eout(lin(t, F("problem", "never") - 0.1, F("problem", "never") + 0.25))
            brand.bullet(cv, x0 + 490 + (1 - kb) * 30, y0 + 160, "Can't let go", False, a=kb, size=30)
            draw_text(cv, "of the needle", x0 + 528 + (1 - kb) * 30, y0 + 204, font("inter_b", 30), INK, a=kb)
            kc = eout(lin(t, F("problem", "point.") - 0.1, F("problem", "point.") + 0.25))
            brand.bullet(cv, x0 + 490 + (1 - kc) * 30, y0 + 270, "Eye at the point", True, a=kc, size=30)
        cv.restore()


def draw_hand_needle(cv, tt, x0, yf):
    """Needle with the eye at the back passes all the way through, moves along underneath, comes back up."""
    per = 3.4
    p = (tt % per) / per
    L_ = 90.0
    xa, xb = x0 + 170, x0 + 320
    if p < 0.4:
        k = ease(p / 0.4)
        x, tip = xa, yf - 100 + 215 * k               # the whole needle goes through, eye last
        ang = 1
    elif p < 0.55:
        k = ease((p - 0.4) / 0.15)
        x, tip = xa + (xb - xa) * k, yf + 115
        ang = 1
    else:
        k = ease((p - 0.55) / 0.4)
        x, tip = xb, yf + 115 - 235 * k
        ang = -1
    # needle body: tip end and eye end
    eye_y = tip - ang * L_
    y0, y1 = min(tip, eye_y), max(tip, eye_y)
    fade = 1 - lin(p, 0.93, 1.0)
    thread(cv, [(x0 + 90, yf - 10), (xa, yf), (x, eye_y)] if p >= 0.4 else [(x0 + 90, yf - 10), (x, eye_y)],
           CYAN, a=fade, w=3)
    rod(cv, x, y0, y1, 4.5, hx("#dfe5ee"), a=fade)
    e = eye_y + 12 * ang
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 2, e - 6, x + 2, e + 6), 2, 2, paint(hx("#0b0f16"), a=fade))
    # redraw cloth front edge over the part of the needle that is inside it
    cv.drawRect(skia.Rect.MakeLTRB(x - 6, yf - 9, x + 6, yf + 9), paint(hx("#41557e"), a=0.85))


def draw_machine_needle(cv, tt, x0, yf, hl):
    x = x0 + 250
    tip = yf - 20 + 75 * (0.5 - 0.5 * math.cos(tt * 2 * math.pi / 1.6))
    top = tip - 110
    rod(cv, x, top + 20, tip - 18, 5, hx("#dfe5ee"))
    cv.drawRect(skia.Rect.MakeLTRB(x - 16, top - 10, x + 16, top + 20), paint(hx("#6b7688")))
    path = skia.Path()
    path.moveTo(x - 5, tip - 18); path.lineTo(x + 5, tip - 18); path.lineTo(x + 1, tip); path.lineTo(x - 1, tip)
    path.close()
    cv.drawPath(path, paint(hx("#dfe5ee")))
    ey = tip - 12
    thread(cv, [(x + 9, top + 20), (x + 7, ey)], CYAN, w=3)
    if hl > 0:
        cv.drawCircle(x, ey, 24, paint(YEL, a=0.6 * hl, blur=8))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 2, ey - 6, x + 2, ey + 6), 2, 2, paint(hx("#0b0f16")))
    cv.drawCircle(x, ey, 3, paint(CYAN))
    if hl > 0:
        leader(cv, x - 10, ey, x - 110, ey + 55, YEL, a=hl, prog=hl)
        pill(cv, x - 118, ey + 55, "EYE", font("inter_xb", 26), INK, border=YEL, a=hl, align="right", tracking=1.5)
    # cloth front edge over the needle part inside the cloth
    if tip > yf - 9:
        cv.drawRect(skia.Rect.MakeLTRB(x - 6, yf - 9, x + 6, min(tip, yf + 9)), paint(hx("#41557e"), a=0.85))
    return ey


# ================================================================== labels + HUD
def draw_labels(cv, t):
    if mech_alpha(t) <= 0.01:
        return
    phi = phi_at(t)
    lab = brand.label
    end = T_END
    ts = lambda X, Y, z=0.0: to_screen(X, Y, z, t)
    # threads ("what")
    a = ts(-110, FAB_Y - 3)
    lab(cv, t, "TOP THREAD", a, (a[0] - 60, a[1] - 210), CYAN, F("what", "top") - 0.15, F("what", "bobbin") + 1.4,
        align="right")
    sl = ts(SLOT[0] + 30, SLOT[1] - 40, -25)
    lab(cv, t, "BOBBIN THREAD", sl, (sl[0] - 10, sl[1] - 150), RED, F("what", "bobbin") - 0.1,
        L("what")["end"] + 0.4, align="left")
    # parts
    a = ts(-150, 1062, 10)
    lab(cv, t, "ROTARY HOOK", a, (a[0] - 20, a[1] + 120), RED, F("parts", "spinning") - 0.05, F("parts", "up"),
        align="right")
    a = ts(70, 1100, -25)
    lab(cv, t, "BOBBIN CASE", a, (a[0] + 50, a[1] + 90), YEL, F("parts", "bobbin") - 0.05, F("parts", "up") + 0.2)
    a = ts(200, 730, 0)
    lab(cv, t, "PLATE", a, (a[0] + 20, a[1] + 110), INK, F("parts", "plate,") - 0.15, F("parts", "spinning") + 0.4)
    k_tu = takeup_k(phi)
    y_eye = 482 - 78 * k_tu
    s = clamp((y_eye - TU_PIV[1]) / TU_LEN, -1, 1)
    ang = math.asin(s)
    eye = TU_PIV + TU_LEN * np.array([-math.cos(ang), s])
    a = ts(eye[0], eye[1], -60)
    lab(cv, t, "TAKE-UP LEVER", a, (a[0] - 140, a[1] + 210), RED, F("parts", "take") - 0.05, L("parts")["end"] + 0.3,
        align="right")
    lab(cv, t, "TAKE-UP LEVER", a, (a[0] - 140, a[1] + 210), RED, F("tight", "take") - 0.05, F("tight", "shut,") + 0.2,
        align="right")
    # how it works
    tip = needle_tip(phi)
    a = ts(-6, tip - EYE_UP)
    lab(cv, t, "EYE", a, (a[0] - 170, a[1] + 60), YEL, F("down", "needle") - 0.05, F("down", "fabric.") + 0.3,
        align="right")
    a = ts(22, tip + 14, -2)
    lab(cv, t, "LOOP", a, (a[0] + 190, a[1] + 40), YEL, F("down", "loop.") - 0.15, T_SNAG + 0.5)
    th = hook_theta(phi)
    pt = ts(*(C + R_PT * np.array([math.cos(th), math.sin(th)])), -10)
    lab(cv, t, "HOOK POINT", pt, (700, 820), RED, F("key", "point") - 0.1, F("key", "drags") + 0.6)
    a = ts(-60, FAB_B + 30, 0)
    lab(cv, t, "FEED DOGS", a, (a[0] - 90, a[1] + 120), YEL, F("feed", "feed") - 0.05, F("feed", "again.") + 0.2,
        align="right")
    brand.stamp(cv, t, "LOCKED", T_LOCK, dur=1.6, center=(540, 1120))
    brand.stamp(cv, t, "2 TURNS = 1 STITCH", T_TWICE - 0.1, dur=2.1, center=(540, 1330), color=YEL,
                bg=hx("#2a2205"))


STAGES = [("down", "pushes", "1  NEEDLE DOWN", CYAN), ("down", "rise,", "2  LOOP", YEL),
          ("key", "snags", "3  HOOK", RED), ("tight", "yanks", "4  PULL TIGHT", RED),
          ("feed", "feed", "5  FEED", CYAN)]


def draw_hud(cv, t):
    k = win(t, L("down")["start"] - 0.2, T_END, 0.3, 0.4)
    if k <= 0:
        return
    cur = None
    for i, (ln, w, txt, c) in enumerate(STAGES):
        if t >= F(ln, w) - 0.1:
            cur = (i, txt, c)
    if cur is not None:
        i, txt, c = cur
        t0 = F(STAGES[i][0], STAGES[i][1]) - 0.1
        kk = eout(lin(t, t0, t0 + 0.3))
        brand.status_pill(cv, k * kk, txt, c)
    phi = phi_at(t)
    t_f = L("feed")["start"]
    if t >= t_f - 0.2:
        p0 = phi_at(t_f)
        turns = max(0.0, (phi - p0) * 2)
        stitches = int(max(0.0, phi - p0 + 0.04))
        kr = eout(lin(t, t_f - 0.2, t_f + 0.3)) * k
        brand.readout(cv, kr, f"{turns:.1f}", "HOOK TURNS")
        draw_text(cv, f"STITCHES  {stitches}", 70, 318, font("inter_xb", 28), INK, a=kr, tracking=2)
    else:
        brand.note(cv, "ANIMATION SLOWED  ·  CUTAWAY", k * 0.9, dy=-80)


def draw_hook_extra(cv, t):
    """Hook: speed note so the first frames read as the real machine running."""
    a = win(t, 0.0, HOOK_OUT + 0.2, 0.15, 0.4)
    if a <= 0:
        return
    draw_text(cv, "CUTAWAY", 540, 1395, font("inter_sb", 22), MUTED, a=0.8 * a, align="center", tracking=4)


# ================================================================== frame + sound
def draw(cv, t):
    draw_mechanism(cv, t)
    draw_panels(cv, t)
    draw_labels(cv, t)
    draw_hud(cv, t)
    draw_hook_extra(cv, t)


BEAT_ANCHOR = T_LOCK
MUSIC_START = L("what")["start"]


def _needle_downs(t0, t1):
    out = []
    ts = np.arange(t0, t1, 1 / 120)
    ph = np.array([phi_at(x) for x in ts])
    for i in range(1, len(ts)):
        if math.floor(ph[i] - 0.5) > math.floor(ph[i - 1] - 0.5):
            out.append(ts[i])
    return out


def sound():
    sfx = [(HOOK_OUT - 0.1, "whoosh_big", 0.6), (T_PANEL[0] - 0.15, "whoosh_down", 0.45),
           (T_MECH_BACK[0] - 0.1, "whoosh_up", 0.45), (T_SNAG + 0.1, "clunk", 0.45),
           (T_LOCK, "impact", 0.5), (T_TWICE - 0.1, "clunk", 0.4)]
    sfx += [(x, "tick", 0.22) for x in _needle_downs(0.0, L("what")["start"] + 3.0)]
    sfx += [(x, "tick", 0.18) for x in _needle_downs(F("feed", "again."), T_END)]
    return {"build": (L("key")["start"], T_LOCK), "drop": (T_LOCK, L("outro")["start"]), "sfx": sfx}
