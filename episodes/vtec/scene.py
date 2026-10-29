"""VTEC episode visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Structure (reuse for new episodes):
  1. cue times from the timeline (F/L)
  2. deterministic per-frame state (mechanism physics) -> frame_state(t)
  3. scene blocks, each visible in its own time window: hook, acronym, comparison, mechanism, labels, HUD
  4. draw(cv, t) calls the blocks;  sound() returns the audio plan
The brand layer (background, hook title, captions, end card) is drawn by ev.build — don't draw it here.
"""
import math

import numpy as np
import skia

import mech
from ev import brand, current
from ev.current import tl
from ev.gfx import *

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic

# ================================================================== cue times
T_HOOK_OUT = (current.hook_out, L("name")["start"])
T_NAME = (L("name")["start"] - 0.3, L("trade")["start"] - 0.01)
T_TRADE = (L("trade")["start"] - 0.21, L("lobes")["start"] + 0.19)
T_MECH_IN = L("lobes")["start"] - 0.21
T_LAMP = F("hook", "kicked") - 0.03

T_ENGAGE = (F("switch", "pushes") + 0.12, F("switch", "rockers") - 0.17)   # pins slide in
T_DISENGAGE = (F("outro", "pushes") - 0.1, F("outro", "pushes") + 0.7)     # pins slide back
T_SOL_OPEN = F("switch", "opens") + 0.05
T_SOL_CLOSE = F("outro", "revs") - 0.1
T_LOCK_FX = F("switch", "locking")

# ================================================================== mechanism state (deterministic)
_Ls, _Lf, _Ll, _Lsw, _Lo = (L(k)["start"] for k in ("lobes", "free", "low", "switch", "outro"))
# visual cam speed in revolutions/second of the drawing (slow motion)
OMEGA_KEYS = [(0.0, 0.30), (_Ls - 0.15, 0.30), (_Lf + 0.04, 0.30), (_Lf + 0.44, 0.45), (_Ll - 0.02, 0.45),
              (_Ll + 0.48, 0.60), (_Lsw + 0.1, 0.60), (_Lsw + 2.0, 0.95), (T_SOL_OPEN + 0.12, 0.95),
              (T_SOL_OPEN + 1.32, 0.27), (T_LOCK_FX, 0.27), (T_LOCK_FX + 1.9, 1.05), (_Lo + 0.01, 1.05),
              (_Lo + 0.61, 0.30), (T_DISENGAGE[1] + 0.3, 0.30), (T_DISENGAGE[1] + 1.15, 0.60), (T_TOTAL, 0.60)]
# the cam must sit on its base circle (nose up) while the pins move — physically they can only slide then
SYNC = [((T_ENGAGE[0] + T_ENGAGE[1]) / 2, 1.5 * np.pi, (T_SOL_OPEN - 0.28, T_ENGAGE[0] - 0.6)),
        ((T_DISENGAGE[0] + T_DISENGAGE[1]) / 2, 1.5 * np.pi, (_Lo - 1.54, T_DISENGAGE[0] - 0.65))]
RPM_KEYS = [(0, 900), (_Ll - 0.12, 2500), (_Lsw + 0.15, 2500), (_Lsw + 2.2, 5800), (T_LOCK_FX, 5800),
            (T_LOCK_FX + 1.9, 7300), (_Lo + 0.01, 7300), (_Lo + 0.86, 3200), (T_TOTAL, 3000)]


def _theta_series():
    dt = 1.0 / 600
    ts = np.arange(0, T_TOTAL + 1.0, dt)
    om = np.array([smooth(t, OMEGA_KEYS) for t in ts]) * 2 * np.pi
    th = np.concatenate([[0.0], np.cumsum(om[:-1]) * dt]) + 0.3
    for (tk, target, (r0, r1)) in SYNC:
        ph = np.interp(tk, ts, th)
        d = (target - ph + np.pi) % (2 * np.pi) - np.pi
        ramp = np.array([ease(lin(t, r0, r1)) for t in ts])
        th = th + d * ramp
    return ts, th


_TS, _TH = _theta_series()


def pin_travel(t):
    if t < T_ENGAGE[0]:
        return 0.0
    if t < T_ENGAGE[1]:
        return ease(lin(t, *T_ENGAGE))
    if t < T_DISENGAGE[0]:
        return 1.0
    return 1.0 - ease(lin(t, *T_DISENGAGE))


def frame_state(t):
    th = float(np.interp(t, _TS, _TH))
    a_mild = float(mech.alpha_mild(th))
    a_tall = float(mech.alpha_tall(th))
    p = pin_travel(t)
    locked = p > 0.0
    a_out = a_tall if locked else a_mild
    oil_path = lin(t, T_SOL_OPEN + 0.35, T_ENGAGE[0] - 0.1)
    drain = lin(t, T_SOL_CLOSE + 0.1, T_DISENGAGE[0])
    oil_p = (1.0 if t >= T_SOL_OPEN + 0.35 else 0.0) * (1 - drain)
    sol = ease(lin(t, T_SOL_OPEN, T_SOL_OPEN + 0.3)) * (1 - ease(lin(t, T_SOL_CLOSE, T_SOL_CLOSE + 0.3)))
    return dict(t=t, theta=th, a_mild=a_mild, a_tall=a_tall, a_out=a_out, a_mid=a_tall, pin=p, locked=locked,
                oil_path=oil_path, oil_p=oil_p, drain=drain, sol=sol, rpm=smooth(t, RPM_KEYS),
                lift_out=float(mech.tip_drop(a_out)), lift_mid=float(mech.tip_drop(a_tall)))


def check_physics():
    """Pins may only move while all three rockers sit on the base circle."""
    bad = 0
    for f in range(int(T_TOTAL * 30)):
        s = frame_state(f / 30)
        if 0 < s["pin"] < 1 and (s["a_tall"] > 1e-4 or s["a_mild"] > 1e-4):
            bad += 1
    return bad


# ================================================================== HOOK (tach sweeps, VTEC lamp lights)
_HK = T_LAMP / 1.22


def hook_rpm(t):
    base = smooth(t, [(0, 900), (0.18 * _HK, 900), (1.55 * _HK, 7050), (1.9 * _HK, 6800), (T_HOOK_OUT[1], 6900)])
    if t > 1.5 * _HK:
        base += 90 * math.sin(t * 38) * lin(t, 1.5 * _HK, 1.8 * _HK)
    return base


def draw_hook(cv, t):
    if t > T_HOOK_OUT[1]:
        return
    zp = ease(lin(t, *T_HOOK_OUT))
    a_scene = 1 - lin(t, T_HOOK_OUT[0] + 0.25, T_HOOK_OUT[1])
    cx, cy, R = 540, 900, 300
    lamp_y = cy + 175
    shake = 0.0
    if T_LAMP < t < T_LAMP + 0.35:
        shake = 7 * (1 - lin(t, T_LAMP, T_LAMP + 0.35)) * math.sin(t * 90)
    cv.save()
    sc = 1 + 7 * zp ** 2.2                      # zoom "into" the lamp as the hook ends
    cv.translate(540 + shake, lamp_y)
    cv.scale(sc, sc)
    cv.translate(-540, -lamp_y)
    cv.saveLayerAlpha(None, int(255 * a_scene * (0.55 + 0.45 * eout(lin(t, 0.0, 0.3)))))
    brand.gauge(cv, cx, cy, R, hook_rpm(t), vmax=9000, redline=7500, marker=5500)
    on = eout(lin(t, T_LAMP, T_LAMP + 0.08))
    brand.lamp(cv, cx, lamp_y, "VTEC", on)
    if T_LAMP < t < T_LAMP + 0.6:
        k = lin(t, T_LAMP, T_LAMP + 0.6)
        cv.drawCircle(cx, lamp_y, 70 + 230 * eout(k), paint(RED, a=0.55 * (1 - k) ** 1.5, stroke=7 * (1 - k) + 1))
    cv.restore()
    cv.restore()


# ================================================================== ACRONYM
def draw_name(cv, t):
    if not (T_NAME[0] <= t <= T_NAME[1]):
        return
    t_out = F("name", "tradeoff") - 0.35
    rows = [("V", "Variable Valve", F("name", "variable")), ("T", "Timing & Lift", F("name", "timing")),
            ("E", "Electronic", F("name", "electronic")), ("C", "Control", F("name", "control"))]
    brand.acronym_rows(cv, t, "VTEC STANDS FOR", rows, T_NAME[0], t_out, highlight=1)
    tu = F("name", "lift")
    u = ease(lin(t, tu, tu + 0.35)) * (1 - ease(lin(t, t_out, t_out + 0.4)))
    if u > 0:
        x0, y0 = 360, 560 + 165 + 44
        cv.drawLine(x0, y0, x0 + text_w("Timing & Lift", font("pop_b", 66)) * u, y0, paint(YEL, stroke=6))


# ================================================================== TRADEOFF (mild vs aggressive cam)
def lift_curve_pts(which, x0, y0, w, h, n=181):
    th, lift = mech.valve_lift_curve(which, n)
    crank = (2 * (th - mech.THETA_PEAK) + 2 * np.pi) % (4 * np.pi)   # peak in the middle of a 720° window
    order = np.argsort(crank)
    crank, lift = crank[order], lift[order]
    return np.stack([x0 + w * crank / (4 * np.pi), y0 + h - h * lift / mech.MAX_LIFT_TALL], 1)


def crank_x(theta, x0, w):
    crank = (2 * (theta - mech.THETA_PEAK) + 2 * np.pi) % (4 * np.pi)
    return x0 + w * crank / (4 * np.pi), crank


def draw_mini_cam(cv, cx, cy, s, which, theta, base_rim):
    pj = Proj(cx, cy, s, 0.62, -0.42)
    prof = mech.PROF_MILD if which == "mild" else mech.PROF_TALL
    dense = mech.DENSE_MILD if which == "mild" else mech.DENSE_TALL
    L_ = float(mech.rot(dense, theta)[:, 1].max() - mech.R0)
    zc, wz = 0.0, 70.0
    vcyl(cv, pj, 0, zc, 7, mech.R0 + L_ + 40, mech.R0 + L_ + 140, STEEL)
    draw_spring(cv, pj, 0, zc, 30, mech.R0 + L_ + 46, 250, 4.5, STEEL, width=5)
    vcyl(cv, pj, 0, zc, 46, mech.R0 + L_, mech.R0 + L_ + 40, hx("#9aa6b8"))
    extrude(cv, pj, circle_prof(0, 0, 26), wz / 2 + 40, wz / 2, STEEL_D)
    extrude(cv, pj, mech.rot(prof, theta), -wz / 2, wz / 2, STEEL, rim=base_rim, rim_w=3.2, rim_glow=0.6)
    extrude(cv, pj, circle_prof(0, 0, 26), -wz / 2 - 1, -wz / 2 - 40, STEEL_D)
    return L_


def draw_trade(cv, t):
    if not (T_TRADE[0] <= t <= T_TRADE[1]):
        return
    t_b = F("trade", "an") - 0.15
    t_both = F("trade", "both") - 0.5
    out = ease(lin(t, T_TRADE[1] - 0.55, T_TRADE[1]))
    theta = t * 0.55 * 2 * np.pi
    panels = [
        dict(which="mild", y=330, c=CYAN, title="MILD CAM", tin=T_TRADE[0],
             bullets=[(True, "Smooth idle", F("trade", "idles")), (True, "Saves fuel", F("trade", "saves"))]),
        dict(which="tall", y=760, c=RED, title="AGGRESSIVE CAM", tin=t_b,
             bullets=[(True, "Big top-end power", F("trade", "power")), (False, "Rough at low RPM", F("trade", "rough"))]),
    ]
    for i, pnl in enumerate(panels):
        k = eout(lin(t, pnl["tin"], pnl["tin"] + 0.45))
        if k <= 0:
            continue
        a = k * (1 - out)
        dx = (1 - k) * 260 + out * (-120 if i == 0 else 120)
        x0, y0 = 60 + dx, pnl["y"]
        cv.saveLayerAlpha(None, int(255 * a))
        brand.panel(cv, x0, y0, 880, 380, pnl["title"], pnl["c"])
        lift = draw_mini_cam(cv, x0 + 180, y0 + 175, 0.82, pnl["which"], theta, pnl["c"])
        gx, gy, gw, gh = x0 + 390, y0 + 84, 450, 128
        cv.drawLine(gx, gy + gh, gx + gw, gy + gh, paint(MUTED, a=0.6, stroke=2))
        cv.drawLine(gx, gy, gx, gy + gh, paint(MUTED, a=0.6, stroke=2))
        draw_text(cv, "VALVE LIFT", gx + 10, gy + 6, font("inter_sb", 20), MUTED, tracking=2)
        pts = lift_curve_pts(pnl["which"], gx, gy, gw, gh)
        prog = ease(lin(t, pnl["tin"] + 0.2, pnl["tin"] + 1.1))
        if pnl["which"] == "tall":
            brand.curve(cv, lift_curve_pts("mild", gx, gy, gw, gh), CYAN, a=0.7 * eout(lin(t, t_b + 0.6, t_b + 1.2)),
                        dashed=True)
        brand.curve(cv, pts, pnl["c"], prog=prog)
        xd, _ = crank_x(theta, gx, gw)
        if prog >= 1:
            yd = gy + gh - gh * lift / mech.MAX_LIFT_TALL
            cv.drawCircle(xd, yd, 9, paint(INK))
            cv.drawCircle(xd, yd, 16, paint(pnl["c"], a=0.5, blur=6))
        if pnl["which"] == "tall":
            tw = F("trade", "wider") - 0.1
            ka = eout(lin(t, tw, tw + 0.35))
            if ka > 0:
                top_m = gy + gh - gh * mech.MAX_LIFT_MILD / mech.MAX_LIFT_TALL
                xa = gx + gw / 2
                ap = paint(YEL, a=ka, stroke=4)
                cv.drawLine(xa, top_m - 2, xa, gy + 10, ap)
                cv.drawLine(xa - 9, gy + 21, xa, gy + 10, ap)
                cv.drawLine(xa + 9, gy + 21, xa, gy + 10, ap)
                draw_text(cv, "MORE LIFT", xa + 72, gy + 30, font("inter_xb", 22), YEL, a=ka, tracking=2)
            tl2 = F("trade", "longer") - 0.1
            kb = eout(lin(t, tl2, tl2 + 0.35))
            if kb > 0:
                yb = gy + gh + 22
                open_ = pts[pts[:, 1] < gy + gh - 1.5]
                xa0, xa1 = open_[:, 0].min(), open_[:, 0].max()
                ap = paint(YEL, a=kb, stroke=4)
                cv.drawLine(xa0, yb, xa1, yb, ap)
                for xe, d in ((xa0, 1), (xa1, -1)):
                    cv.drawLine(xe, yb, xe + 12 * d, yb - 9, ap)
                    cv.drawLine(xe, yb, xe + 12 * d, yb + 9, ap)
                draw_text(cv, "OPEN LONGER", (xa0 + xa1) / 2, yb + 32, font("inter_xb", 22), YEL, a=kb,
                          align="center", tracking=2)
        for j, (good, txt, tb) in enumerate(pnl["bullets"]):
            kb = eout(lin(t, tb - 0.1, tb + 0.25))
            brand.bullet(cv, gx + (1 - kb) * 30, y0 + 318 + j * 46, txt, good, a=kb)
        cv.restore()
    kb = eout(lin(t, t_b + 0.3, t_b + 0.6)) * (1 - out)
    if kb > 0:
        pulse = ease(lin(t, t_both, t_both + 0.25)) * (1 - ease(lin(t, t_both + 0.9, t_both + 1.4)))
        r = 42 + 10 * pulse
        cv.drawCircle(500, 735, r + 6, paint(hx("#06080d"), a=kb))
        cv.drawCircle(500, 735, r, paint(mix(hx("#1a2232"), RED, pulse), a=kb))
        cv.drawCircle(500, 735, r, paint(mix(MUTED, hx("#ffb0b0"), pulse), a=kb, stroke=3))
        if pulse > 0:
            cv.drawCircle(500, 735, r + 10, paint(RED, a=0.5 * pulse * kb, blur=14))
        draw_text(cv, "OR", 500, 747, font("inter_blk", 34), INK, a=kb, align="center")


# ================================================================== MECHANISM (3/4 orthographic view)
MP = dict(ox=405, oy=640, s=1.08)
VALVE_X = 225.0
DECK_Y = 352.0
SPRING_SEAT_Y = 292.0
ZOOM_C = (430, 650)


def rocker_profile():
    Px, Py = mech.P
    pts = []
    for a in np.radians(np.linspace(-70, -290, 34)):
        pts.append((Px + 34 * math.cos(a), Py + 34 * math.sin(a)))
    pts += [(-160, 124), (-60, 118), (40, 112), (150, 118), (206, 126)]
    for a in np.radians(np.linspace(100, -90, 16)):
        pts.append((226 + 17 * math.cos(a), 112 + 17 * math.sin(a)))
    pts += [(190, 95), (120, 82), (55, 70), (0, 70), (-55, 70), (-120, 72), (-190, 70)]
    return np.array(pts, float)


ROCKER = rocker_profile()
MID_TIP = np.array([214.0, 124.0])


def draw_valve_head(cv, pj, z, lift, a=1.0):
    vcyl(cv, pj, VALVE_X, z, 44, 356 + lift, 363 + lift, hx("#a3adbd"), alpha=a, top_cap=False)
    frustum(cv, pj, VALVE_X, z, 11, 334 + lift, 44, 356 + lift, hx("#b0b9c8"), alpha=a)


def draw_air(cv, pj, z, lift, t, strength):
    k = clamp(lift / 45.0) * strength
    if k <= 0.02:
        return
    for i in range(22):
        u = 2 * np.pi * i / 22 + 0.37 * math.sin(i * 12.9)
        ph = (t * 1.35 + i * 0.618) % 1.0
        r0, r1 = 46 + 34 * ph, 46 + 34 * max(0, ph - 0.12)
        y0 = DECK_Y + 6 + lift * 0.5 + 95 * ph
        y1 = DECK_Y + 6 + lift * 0.5 + 95 * max(0, ph - 0.12)
        p0 = pj(VALVE_X + r0 * math.cos(u), y0, z + r0 * math.sin(u))
        p1 = pj(VALVE_X + r1 * math.cos(u), y1, z + r1 * math.sin(u))
        aa = (1 - ph) * k * 0.85 * (0.6 if math.sin(u) > 0.2 else 1.0)
        cv.drawLine(p1[0], p1[1], p0[0], p0[1], paint(hx("#bfefff"), a=aa, stroke=4))


def draw_deck(cv, pj, a):
    z0, z1, x0, x1 = -75.0, 355.0, 120.0, 330.0
    quad = np.array([pj(x0, DECK_Y, z0), pj(x1, DECK_Y, z0), pj(x1, DECK_Y, z1), pj(x0, DECK_Y, z1)])
    path = poly_path(quad)
    for zc in (mech.ZC[0], mech.ZC[2]):
        path.addPath(poly_path(hcircle(pj, VALVE_X, DECK_Y, zc, 40)))
    path.setFillType(skia.PathFillType.kEvenOdd)
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad(tuple(quad[0]), tuple(quad[2]), [hx("#3a4558", 0.82 * a), hx("#232b39", 0.82 * a)]))
    cv.drawPath(path, p)
    cv.drawPath(poly_path(quad), paint(hx("#6b7a92"), a=0.7 * a, stroke=2))
    for zc in (mech.ZC[0], mech.ZC[2]):
        cv.drawPath(poly_path(hcircle(pj, VALVE_X, DECK_Y, zc, 52)), paint(hx("#8d9bb2"), a=0.8 * a, stroke=3))
        cv.drawPath(poly_path(hcircle(pj, VALVE_X, DECK_Y, zc, 40)), paint(hx("#0b0f16"), a=0.9 * a, stroke=3))


def draw_valve_upper(cv, pj, z, lift, a=1.0, hl=0.0):
    y = lift
    frustum(cv, pj, VALVE_X, z, 33, SPRING_SEAT_Y, 33, SPRING_SEAT_Y + 7, STEEL_D, alpha=a)
    draw_spring(cv, pj, VALVE_X, z, 26, 166 + y, SPRING_SEAT_Y, 6.0, hx("#7d8899"), width=5.5, alpha=a, which="back")
    vcyl(cv, pj, VALVE_X, z, 7, 136 + y, 336 + y, hx("#c2cad6"), alpha=a, top_cap=False)
    draw_spring(cv, pj, VALVE_X, z, 26, 166 + y, SPRING_SEAT_Y, 6.0, hx("#7d8899"), width=5.5, alpha=a, which="front")
    frustum(cv, pj, VALVE_X, z, 28, 152 + y, 18, 168 + y, hx("#a9b3c2"), alpha=a)
    if hl > 0:
        top, bot = pj(VALVE_X, 140 + y, z), pj(VALVE_X, 330 + y, z)
        cv.drawLine(top[0], top[1], bot[0], bot[1], paint(CYAN, a=0.5 * hl, stroke=16, blur=8))


def draw_lost_motion(cv, pj, a_mid, a=1.0):
    z = mech.ZC[1]
    tip = mech.rot(MID_TIP, a_mid, mech.P)
    x, top = tip[0], tip[1] + 4
    draw_spring(cv, pj, x, z, 18, top + 26, SPRING_SEAT_Y + 10, 5.0, hx("#7d8899"), width=4.5, alpha=a, which="back")
    vcyl(cv, pj, x, z, 13, top, top + 28, hx("#9aa6b8"), alpha=a)
    draw_spring(cv, pj, x, z, 18, top + 26, SPRING_SEAT_Y + 10, 5.0, hx("#7d8899"), width=4.5, alpha=a, which="front")
    frustum(cv, pj, x, z, 24, SPRING_SEAT_Y + 10, 24, SPRING_SEAT_Y + 16, STEEL_D, alpha=a)


def mech_vis(t):
    v = {}
    v["mech"] = eout(lin(t, T_MECH_IN, T_MECH_IN + 0.5))
    tv = L("lobes")["start"] - 0.25
    v["valves"] = eout(lin(t, tv, tv + 0.45))
    tl_ = F("lobes", "three") - 0.1
    v["lobe"] = [eback(lin(t, tl_ + d, tl_ + d + 0.4)) for d in (0.0, 0.3, 0.15)]
    v["cam"] = eout(lin(t, tl_ - 0.1, tl_ + 0.3))
    tr = F("lobes", "rocker") - 0.35
    v["rockers"] = eout(lin(t, tr, tr + 0.5))
    t_only, t_mid = F("free", "only"), F("free", "middle")
    v["rim_mild"] = eout(lin(t, F("lobes", "two") - 0.1, F("lobes", "two") + 0.2))
    v["rim_tall"] = eout(lin(t, F("lobes", "tall") - 0.1, F("lobes", "tall") + 0.2))
    v["hl_outer"] = win(t, t_only - 0.05, t_mid - 0.05, 0.25, 0.3)
    v["hl_mid"] = win(t, t_mid - 0.05, L("low")["start"] + 0.4, 0.25, 0.4)
    xr_on1, xr_off1 = (T_SOL_OPEN + 0.9, T_SOL_OPEN + 1.5), (T_LOCK_FX + 0.35, T_LOCK_FX + 1.0)
    xr_on2 = (L("outro")["start"], L("outro")["start"] + 0.6)
    xr_off2 = (T_DISENGAGE[1] + 0.15, T_DISENGAGE[1] + 0.8)
    v["xray"] = max(ease(lin(t, *xr_on1)) * (1 - ease(lin(t, *xr_off1))),
                    ease(lin(t, *xr_on2)) * (1 - ease(lin(t, *xr_off2))))
    z1 = ease(lin(t, T_SOL_OPEN + 0.9, T_SOL_OPEN + 2.0)) * (1 - ease(lin(t, T_LOCK_FX + 0.3, T_LOCK_FX + 1.2)))
    z2 = ease(lin(t, L("outro")["start"], L("outro")["start"] + 0.8)) * \
        (1 - ease(lin(t, T_DISENGAGE[1] + 0.1, T_DISENGAGE[1] + 0.9)))
    v["zoom"] = max(z1, z2)
    v["end"] = current.ending_k(t)
    v["solenoid"] = eout(lin(t, F("switch", "computer") - 0.2, F("switch", "computer") + 0.3)) * \
        (1 - ease(lin(t, T_END - 0.6, T_END)))
    return v


def to_screen(X, Y, z, v):
    """Profile coords -> screen, including the camera zoom used in draw_mechanism (for labels)."""
    p = Proj(MP["ox"], MP["oy"], MP["s"])(X, Y, z)
    zz = (1 + 0.30 * v["zoom"]) * (1 - 0.18 * v["end"])
    return np.array([ZOOM_C[0] + (p[0] - ZOOM_C[0]) * zz, ZOOM_C[1] - 120 * v["end"] + (p[1] - ZOOM_C[1]) * zz])


def draw_mechanism(cv, t, st, v):
    if t < T_MECH_IN or v["mech"] <= 0:
        return
    cv.save()
    endk = v["end"]
    z = (1 + 0.30 * v["zoom"]) * (1 - 0.18 * endk)
    cv.translate(ZOOM_C[0], ZOOM_C[1] - 120 * endk)
    cv.scale(z, z)
    cv.translate(-ZOOM_C[0], -ZOOM_C[1])
    cv.saveLayerAlpha(None, int(255 * v["mech"] * (1 - 0.8 * endk)))
    pj = Proj(MP["ox"], MP["oy"], MP["s"])
    theta = st["theta"]
    rk = v["rockers"]
    a_out, a_mid = st["a_out"] * rk, st["a_mid"] * rk
    lift_v = float(mech.tip_drop(a_out))
    lockfx = win(t, T_LOCK_FX - 0.05, T_LOCK_FX + 0.9, 0.12, 0.6)
    red_rocks = clamp(ease(lin(t, T_LOCK_FX - 0.1, T_LOCK_FX + 0.25))) * (1 - ease(lin(t, *T_DISENGAGE)))
    xr = v["xray"]
    vy_off, va = (1 - v["valves"]) * 60, v["valves"]
    pjv = pj.shifted(vy_off * pj.s)
    if va > 0:
        for zc in (mech.ZC[2], mech.ZC[0]):
            draw_valve_head(cv, pjv, zc, lift_v, a=va)
            draw_air(cv, pjv, zc, lift_v, t, va)
        draw_deck(cv, pjv, va)
    rock_ang = [a_out, a_mid, a_out]
    ry_off = (1 - rk) * 90
    pjr = pj.shifted(ry_off * pj.s)
    seg_cam = [(400, mech.ZC[2] + 48), (mech.ZC[2] - 48, mech.ZC[1] + 48), (mech.ZC[1] - 48, mech.ZC[0] + 48),
               (mech.ZC[0] - 48, -110)]
    seg_rs = [(392, mech.ZC[2] + 60), (mech.ZC[2] - 60, mech.ZC[1] + 60), (mech.ZC[1] - 60, mech.ZC[0] + 60),
              (mech.ZC[0] - 60, -100)]
    for k_i, slab in enumerate((2, 1, 0)):          # painter's order: back slab first
        zc = mech.ZC[slab]
        if rk > 0:
            extrude(cv, pjr, circle_prof(*mech.P, 24), seg_rs[k_i][1], seg_rs[k_i][0], hx("#5d6879"),
                    alpha=rk * (1 - 0.55 * xr))
        if v["cam"] > 0:
            extrude(cv, pj, circle_prof(0, 0, 30), seg_cam[k_i][1], seg_cam[k_i][0], STEEL_D,
                    alpha=v["cam"] * (1 - 0.72 * xr))
        if slab != 1 and va > 0:
            draw_valve_upper(cv, pjv, zc, lift_v, a=va, hl=v["hl_outer"])
        if slab == 1 and rk > 0:
            draw_lost_motion(cv, pjr, a_mid, a=rk)
        if rk > 0:
            ang = rock_ang[slab]
            if slab != 1:
                tipp = mech.rot(np.array([226.0, 124.0]), ang, mech.P)
                vcyl(cv, pjr, tipp[0], zc, 8, tipp[1] - 6, 136 + lift_v - ry_off + 2, hx("#c9d0db"), alpha=rk,
                     top_cap=False)
            if slab == 1:
                rim_c, rim_a = RED, max(v["hl_mid"], red_rocks)
            else:
                rim_c, rim_a = mix(CYAN, RED, red_rocks), max(v["hl_outer"], red_rocks)
            base = mix(mix(hx("#7f8a9c"), hx("#b07a7a"), 0.35 * red_rocks), hx("#ffffff"), 0.35 * lockfx)
            extrude(cv, pjr, mech.rot(ROCKER, ang, mech.P), zc - 60, zc + 60, base, alpha=rk * (1 - 0.68 * xr),
                    rim=rim_c if rim_a > 0.01 else None, rim_w=3.2 * max(rim_a, 0.01), rim_glow=rim_a)
        lk = v["lobe"][slab]
        if lk > 0:
            sc = 0.6 + 0.4 * lk
            pr = mech.rot(mech.PROF_TALL if slab == 1 else mech.PROF_MILD, theta) * sc
            rim_k = v["rim_tall"] if slab == 1 else v["rim_mild"]
            extrude(cv, pj, pr, zc - 48 * sc, zc + 48 * sc, hx("#8c97a8"), alpha=clamp(lk) * (1 - 0.7 * xr),
                    rim=(RED if slab == 1 else CYAN) if rim_k > 0.01 else None, rim_w=3.4 * rim_k, rim_glow=0.8 * rim_k)
    if rk > 0:
        extrude(cv, pjr, circle_prof(*mech.P, 24), seg_rs[3][1], seg_rs[3][0], hx("#5d6879"), alpha=rk * (1 - 0.55 * xr))
    if v["cam"] > 0:
        extrude(cv, pj, circle_prof(0, 0, 30), seg_cam[3][1], seg_cam[3][0], STEEL_D, alpha=v["cam"] * (1 - 0.72 * xr))
    if xr > 0.01 or v["solenoid"] > 0.01:
        draw_internals(cv, pj, t, st, xr, v, rock_ang)
    cv.restore()
    cv.restore()


def draw_internals(cv, pj, t, st, xr, v, rock_ang):
    sol_a = v["solenoid"]
    Px, Py = mech.P
    zs = -100.0
    if sol_a > 0:
        body = np.array([[Px - 34, 182], [Px + 34, 182], [Px + 34, 246], [Px - 34, 246]], float)
        extrude(cv, pj, body, zs - 40, zs + 40, hx("#2f3a4c"), alpha=sol_a, rim=AMBER, rim_w=2.0 * st["sol"] + 0.01,
                rim_glow=st["sol"])
        p0, p1 = pj(Px, 182, zs), pj(Px, Py + 6, zs)
        cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(hx("#55617a"), a=sol_a, stroke=16))
        cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(hx("#0b0f16"), a=sol_a, stroke=9))
        for i in range(3):
            q0, q1 = pj(Px - 34, 196 + i * 16, zs - 40), pj(Px + 34, 196 + i * 16, zs - 40)
            cv.drawLine(q0[0], q0[1], q1[0], q1[1], paint(hx("#b06a2a"), a=0.75 * sol_a, stroke=4))
    op, oa = st["oil_path"], 1 - st["drain"]
    if op > 0 and oa > 0:
        k1 = clamp(op / 0.25)
        p0, p1 = pj(Px, 182, zs), pj(Px, Py + 6, zs)
        pe = p0 + (p1 - p0) * k1
        cv.drawLine(p0[0], p0[1], pe[0], pe[1], paint(AMBER, a=oa, stroke=7))
        cv.drawLine(p0[0], p0[1], pe[0], pe[1], paint(AMBER, a=0.5 * oa, stroke=14, blur=6))
        k2 = clamp((op - 0.25) / 0.55)
        if k2 > 0:
            extrude(cv, pj, circle_prof(Px, Py, 11), -100, -100 + 490 * k2, AMBER, alpha=oa * max(xr, 0.25),
                    outline=False, side_k=(0.7, 0.4))
        k3 = clamp((op - 0.8) / 0.2)
        if k3 > 0:
            s0 = mech.rot(np.array([Px, Py]), rock_ang[0], mech.P)
            b0 = mech.rot(mech.PIN_BORE, rock_ang[0], mech.P)
            zf = mech.PIN_WALL_FRONT + 8
            q0, q1 = pj(s0[0], s0[1], zf), pj(b0[0], b0[1], zf)
            qe = q0 + (q1 - q0) * k3
            cv.drawLine(q0[0], q0[1], qe[0], qe[1], paint(AMBER, a=oa * xr, stroke=8))
    if xr <= 0.01:
        return
    cv.saveLayerAlpha(None, int(255 * xr))
    for slab in (2, 1, 0):
        zc = mech.ZC[slab]
        b = mech.rot(mech.PIN_BORE, rock_ang[slab], mech.P)
        prof = circle_prof(b[0], b[1], mech.PIN_R + 2.5, 36)
        extrude(cv, pj, prof, zc - 60, zc + 60, hx("#0d131d"), outline=False, side_k=(0.6, 0.3))
        cv.drawPath(poly_path(pj.pts(prof, zc - 60)), paint(hx("#6f7d94"), stroke=2))
    trav = mech.PIN_TRAVEL * st["pin"]
    b2 = mech.rot(mech.PIN_BORE, rock_ang[2], mech.P)
    sp = zhelix(pj, b2[0], b2[1], 10, mech.PINS_REST[2][1] + trav, mech.PIN_WALL_BACK, 6)
    sc = mix(hx("#9fb0c8"), YEL, win(t, F("outro", "spring") - 0.1, T_DISENGAGE[1] + 0.3, 0.2, 0.4))
    cv.drawPath(poly_path(sp, close=False), paint(hx("#0a0d12"), stroke=6))
    cv.drawPath(poly_path(sp, close=False), paint(sc, stroke=3.5))
    b0 = mech.rot(mech.PIN_BORE, rock_ang[0], mech.P)
    if st["oil_path"] >= 0.99 and st["oil_p"] > 0.01:
        extrude(cv, pj, circle_prof(b0[0], b0[1], mech.PIN_R, 36), mech.PIN_WALL_FRONT, mech.PINS_REST[0][0] + trav,
                AMBER, alpha=st["oil_p"], outline=False, side_k=(0.75, 0.35))
    pin_glow = win(t, T_ENGAGE[0] - 0.1, T_LOCK_FX + 0.8, 0.2, 0.5)
    for i in (2, 1, 0):
        z0, z1 = mech.PINS_REST[i]
        bb = mech.rot(mech.PIN_BORE, rock_ang[i], mech.P)
        extrude(cv, pj, circle_prof(bb[0], bb[1], mech.PIN_R, 36), z0 + trav, z1 + trav, hx("#e9eef6"),
                rim=YEL, rim_w=2.2, rim_glow=pin_glow, side_k=(0.5, 0.6))
    cv.restore()


def draw_labels(cv, t, v):
    if t < T_MECH_IN or v["mech"] <= 0:
        return
    lab = brand.label
    a = to_screen(VALVE_X + 40, 300, mech.ZC[0], v)
    lab(cv, t, "2 VALVES", a, (a[0] + 90, a[1] + 120), INK, L("lobes")["start"] - 0.1, F("lobes", "two") + 0.1)
    tm, t_end = F("lobes", "two") - 0.05, F("free", "only") - 0.1
    a = to_screen(-60, -90, mech.ZC[0] - 30, v)
    lab(cv, t, "MILD", a, (a[0] - 70, a[1] - 150), CYAN, tm, t_end, align="right")
    a = to_screen(60, -95, mech.ZC[2] + 30, v)
    lab(cv, t, "MILD", a, (a[0] + 60, a[1] - 60), CYAN, tm + 0.1, t_end)
    a = to_screen(0, -112, mech.ZC[1], v)
    lab(cv, t, "TALL", a, (a[0] - 40, a[1] - 140), RED, F("lobes", "tall") - 0.05, t_end, align="right")
    a = to_screen(-200, 120, mech.ZC[0], v)
    lab(cv, t, "ROCKER ARMS", a, (a[0] + 20, a[1] + 150), INK, F("lobes", "rocker") + 0.1, t_end + 0.6)
    t_mid = F("free", "middle") - 0.05
    a = to_screen(214, 160, mech.ZC[1], v)
    lab(cv, t, "NO VALVE", a, (a[0] + 50, a[1] - 205), RED, t_mid + 0.1, L("low")["start"] + 0.3)
    a = to_screen(VALVE_X - 20, 250, mech.ZC[0], v)
    lab(cv, t, "PUSH VALVES", a, (a[0] + 150, a[1] + 175), CYAN, F("free", "only") + 0.3, t_mid - 0.1)
    a = to_screen(mech.P[0], 215, -100, v)
    lab(cv, t, "SOLENOID", a, (a[0] + 10, a[1] + 150), AMBER, F("switch", "solenoid") - 0.45, F("switch", "oil") + 0.6)
    a = to_screen(mech.P[0], mech.P[1], 120, v)
    lab(cv, t, "OIL PRESSURE", a, (a[0] - 40, a[1] - 230), AMBER, F("switch", "oil") - 0.05, F("switch", "rockers"))
    a = to_screen(mech.PIN_BORE[0], mech.PIN_BORE[1] + 14, 70, v)
    lab(cv, t, "LOCKING PINS", a, (a[0] + 10, a[1] + 205), YEL, F("switch", "pins") - 0.1, T_LOCK_FX + 0.4)
    a = to_screen(mech.PIN_BORE[0], mech.PIN_BORE[1] + 12, 300, v)
    lab(cv, t, "RETURN SPRING", a, (a[0] + 20, a[1] + 175), YEL, F("outro", "spring") - 0.1, T_DISENGAGE[1] + 0.5)
    brand.stamp(cv, t, "LOCKED", T_LOCK_FX)


# ================================================================== HUD: mode pill, RPM, ECU chips, lift graph
T_HDR = (L("low")["start"] - 0.1, T_END)


def draw_header(cv, t, st, v):
    k = win(t, T_HDR[0], T_HDR[1], 0.35, 0.4)
    if k <= 0:
        return
    engaged = clamp(ease(lin(t, T_LOCK_FX - 0.05, T_LOCK_FX + 0.2))) * \
        (1 - ease(lin(t, T_DISENGAGE[1] - 0.1, T_DISENGAGE[1] + 0.2)))
    dy = (1 - k) * -30
    if engaged < 0.5:
        brand.status_pill(cv, k * (1 - engaged * 2), "LOW-RPM CAM", CYAN, dy)
    else:
        brand.status_pill(cv, k * (engaged * 2 - 1), "VTEC ENGAGED", RED, dy, bg=hx("#2a0707"))
    rpm = st["rpm"]
    brand.readout(cv, k, f"{int(round(rpm / 50) * 50):,}", "RPM", frac=rpm / 8000,
                  bar_color=mix(CYAN, RED, clamp((rpm - 5000) / 900)), marker_frac=5500 / 8000, dy=dy)
    brand.note(cv, "ANIMATION SLOWED", k * (0.55 + 0.45 * v["zoom"]), dy)


def draw_ecu(cv, t, v):
    k = win(t, F("switch", "high") - 0.2, F("switch", "oil") + 0.15, 0.35, 0.45)
    if k <= 0:
        return
    y = 410
    items = []
    for i, (name, word) in enumerate([("RPM", "rev"), ("TEMP", "warm"), ("LOAD", "load"), ("SPEED", "load")]):
        tw = F("switch", word) + 0.05 * i
        items.append((name, eout(lin(t, tw, tw + 0.25))))
    tc = F("switch", "computer") - 0.1
    brand.chips(cv, k, y, items, lead=("ECU", eout(lin(t, tc, tc + 0.3))))
    ts = F("switch", "opens") - 0.15
    sk = lin(t, ts, ts + 0.5)
    if sk > 0:                          # signal wire ECU -> solenoid with a travelling pulse
        sol = to_screen(mech.P[0] - 34, 214, -140, v)
        wx = 92
        cv.drawPath(poly_path([(wx, y + 25), (wx, sol[1]), (sol[0], sol[1])], close=False),
                    paint(AMBER, a=0.35 * k, stroke=3))
        if sk < 1:
            seg1 = sol[1] - (y + 25)
            d = (seg1 + abs(sol[0] - wx)) * ease(sk)
            px, py = (wx, y + 25 + d) if d < seg1 else (wx + (d - seg1) * (1 if sol[0] > wx else -1), sol[1])
            cv.drawCircle(px, py, 9, paint(YEL, a=k))
            cv.drawCircle(px, py, 20, paint(AMBER, a=0.6 * k, blur=8))


GRAPH = (110, 1232, 760, 104)


def draw_graph(cv, t, st, v):
    k = win(t, L("low")["start"], T_END, 0.4, 0.4) * (1 - 0.9 * v["zoom"])
    if k <= 0.01:
        return
    gx, gy, gw, gh = GRAPH
    gy += (1 - k) * 40
    cv.saveLayerAlpha(None, int(255 * k))
    brand.graph_box(cv, (gx, gy, gw, gh), "VALVE LIFT", "CRANK ANGLE →")
    eng = clamp(ease(lin(t, T_LOCK_FX - 0.6, T_LOCK_FX + 0.2))) * (1 - ease(lin(t, T_DISENGAGE[0], T_DISENGAGE[1] + 0.3)))
    pm, pt = lift_curve_pts("mild", gx, gy, gw, gh), lift_curve_pts("tall", gx, gy, gw, gh)
    if eng < 1:
        brand.curve(cv, pm, CYAN, a=1 - eng)
    if eng > 0:
        brand.curve(cv, pm, CYAN, a=eng, dashed=True)
        brand.curve(cv, pt, RED, a=eng, prog=eout(eng))
    xd, _ = crank_x(st["theta"], gx, gw)
    brand.dot(cv, xd, gy + gh - gh * st["lift_out"] / mech.MAX_LIFT_TALL, mix(CYAN, RED, eng))
    ka = win(t, F("high", "lift") - 0.1, T_DISENGAGE[0] + 0.2, 0.3, 0.4)
    if ka > 0:
        top_m = gy + gh - gh * mech.MAX_LIFT_MILD / mech.MAX_LIFT_TALL
        xa = gx + gw / 2
        ap = paint(YEL, a=ka, stroke=4)
        cv.drawLine(xa, top_m - 4, xa, gy + 8, ap)
        cv.drawLine(xa - 10, gy + 20, xa, gy + 8, ap)
        cv.drawLine(xa + 10, gy + 20, xa, gy + 8, ap)
        draw_text(cv, "MORE LIFT", xa + 16, gy - 10, font("inter_xb", 22), YEL, a=ka, tracking=2)
    kb = win(t, F("high", "duration") - 0.35, T_DISENGAGE[0] + 0.2, 0.3, 0.4)
    if kb > 0:
        open_t, open_m = pt[pt[:, 1] < gy + gh - 1.5], pm[pm[:, 1] < gy + gh - 1.5]
        yb = gy + gh - 18
        ap = paint(YEL, a=kb, stroke=4)
        for x_m, x_t, d in ((open_m[:, 0].min(), open_t[:, 0].min(), -1), (open_m[:, 0].max(), open_t[:, 0].max(), 1)):
            cv.drawLine(x_m, yb, x_t, yb, ap)
            cv.drawLine(x_t, yb, x_t - 10 * d, yb - 8, ap)
            cv.drawLine(x_t, yb, x_t - 10 * d, yb + 8, ap)
        draw_text(cv, "LONGER DURATION", gx + 8, gy + gh - 30, font("inter_xb", 20), YEL, a=kb, tracking=1.5)
    cv.restore()


# ================================================================== frame + sound
def draw(cv, t):
    st = frame_state(t)
    v = mech_vis(t)
    draw_hook(cv, t)
    draw_name(cv, t)
    draw_trade(cv, t)
    draw_mechanism(cv, t, st, v)
    draw_labels(cv, t, v)
    draw_header(cv, t, st, v)
    draw_ecu(cv, t, v)
    draw_graph(cv, t, st, v)


BEAT_ANCHOR = T_LOCK_FX            # a beat lands exactly on the lock moment
MUSIC_START = L("name")["start"]


def sound():
    hook_end = T_HOOK_OUT[1] + 0.05
    sfx = [(T_LAMP, "impact", 0.45), (T_HOOK_OUT[0] - 0.1, "whoosh_big", 0.6),
           (L("trade")["start"] - 0.41, "whoosh_down", 0.45), (L("lobes")["start"] - 0.41, "whoosh_up", 0.45),
           (T_ENGAGE[1] - 0.05, "clunk", 0.6), (T_LOCK_FX, "impact", 0.5), (T_DISENGAGE[1] - 0.05, "clunk", 0.55)]
    sfx += [(F("switch", w) + 0.05, "tick", 0.22) for w in ("rev", "warm", "load", "computer")]

    def rpm(x):
        return hook_rpm(x) if x < hook_end else smooth(x, RPM_KEYS)

    def bright(x):
        b = ease(lin(x, T_LOCK_FX - 0.05, T_LOCK_FX + 0.15)) * (1 - ease(lin(x, *T_DISENGAGE)))
        if x < hook_end:
            b = max(b, smooth(x, [(0, 0), (T_LAMP - 0.05, 0), (T_LAMP + 0.1, 1)]))
        return b

    env = [(0, 0.25), (0.05, 0.4), (T_HOOK_OUT[0] - 0.25, 0.4), (T_HOOK_OUT[1] - 0.05, 0.0), (_Ll - 0.22, 0.0),
           (_Ll + 0.48, 0.35), (_Lsw - 0.1, 0.45), (_Lo - 0.04, 0.35), (_Lo + 1.26, 0.3), (T_END + 0.04, 0.25),
           (T_END + 0.64, 0.0)]
    return {"build": (_Lsw, T_LOCK_FX), "drop": (T_LOCK_FX, _Lo - 0.04), "sfx": sfx,
            "engine": {"rpm": rpm, "bright": bright, "env": env}}
