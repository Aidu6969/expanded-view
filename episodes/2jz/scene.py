"""2JZ visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Model (ortho 3/4 view; X across the engine, Y down, z along the crankshaft; units mm, 2JZ dimensions):
  six cylinders on z_i = (i - 2.5) * PITCH, cylinder 1 at the front (nearest the viewer)
  bore 86, stroke 86 (throw 43), rod 142; exact slider-crank kinematics for every piston
  crank throws: 1&6 at 0 deg, 2&5 at 120 deg, 3&4 at 240 deg (mirror-symmetric, firing 1-5-3-6-2-4)
  seven main journals at z = (j - 3) * PITCH: one each side of every cylinder
  balance graph: inertia force of one piston  ~ cos(a) + (r/L) cos(2a)  vs the sum over six (= 0)
"""
import math

import numpy as np
import skia

from ev import brand, current
from ev.current import tl
from ev.gfx import *
from ev.parts import rev, ring_front, wheel, spline, pipe, flow, resample

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_DOUBLE = F("hook", "double")
T_FACTORY = F("hook", "factory")
T_WHAT = L("what")["start"]
T_TRUE = F("what", "true?")
T_LITRE = F("what", "three")
T_SIX = F("what", "six")
T_SUPRA = F("what", "supra.")
T_WHY = F("what", "why")
T_STRONG = F("what", "strong.")
T_BLOCK = L("block")["start"]
T_BLOCK_W = F("block", "block.")
T_IRON = F("block", "iron,")
T_ALU = F("block", "aluminium,")
T_CLOSED = F("block", "closed")
T_SOLID = F("block", "solid")
T_EVERY = F("block", "every")
T_BRACED = F("block", "braced")
T_BOOST = F("block", "boost.")
T_CRANK = L("crank")["start"]
T_FORGED = F("crank", "forged")
T_CRANKSHAFT = F("crank", "crankshaft")
T_SEVEN = F("crank", "seven")
T_MAINS_E = F("crank", "bearings,", which="end")
T_EACH = F("crank", "each")
T_FLEX = F("crank", "flex.")
T_BAL = L("balance")["start"]
T_BALANCES = F("balance", "balances")
T_FRONT = F("balance", "front")
T_BACK = F("balance", "back")
T_SHAKING = F("balance", "shaking")
T_CANCEL = F("balance", "cancel")
T_HAMMER = F("balance", "hammering")
T_TURBOS = L("turbos")["start"]
T_TWO = F("turbos", "two")
T_IDENT = F("turbos", "identical")
T_SEQ = F("turbos", "sequence.")
T_FIRST = F("turbos", "first")
T_LOW = F("turbos", "low.")
T_4000 = F("turbos", "four")
T_SECOND = F("turbos", "second")
T_JOINS = F("turbos", "joins")
T_KEY = L("key")["start"]
T_EXPORT = F("key", "export")
T_320 = F("key", "three")
T_HP1_E = F("key", "horsepower.", which="end")
T_TUNERS = F("key", "tuners")
T_600 = F("key", "six")
T_STOCK = F("key", "stock")
T_DOUBLE2 = F("key", "double.")
T_LIMIT = L("limit")["start"]
T_KILLS = F("limit", "kills")
T_IRON2 = F("limit", "iron.")
T_TUNE = F("limit", "tune,")
T_DET = F("limit", "detonation")
T_PISTONS = F("limit", "pistons")
T_RODS = F("limit", "rods.")
T_OUTRO = L("outro")["start"]

# ================================================================== geometry (mm)
PITCH = 100.0
NCYL = 6
ZC = [(i - 2.5) * PITCH for i in range(NCYL)]          # cylinder 1 = index 0 = front
ZM = [(j - 3) * PITCH for j in range(7)]                # main journals
R_B = 43.0                                              # bore radius
CR_R, ROD = 43.0, 142.0
PIN_H = 30.0
PISTON_H = 50.0
CR_Y = 6.0 + PIN_H + CR_R + ROD                         # crown 6 mm below the deck at TDC
OFF = [0.0, 2 * math.pi / 3, 4 * math.pi / 3, 4 * math.pi / 3, 2 * math.pi / 3, 0.0]
FIRING = [1, 5, 3, 6, 2, 4]
BX = 72.0                                               # block half-width
BLOCK_Y1 = CR_Y + 6.0
C_IRON = hx("#55606f")
C_ROD = hx("#7d889b")
C_CAP = hx("#6a7486")


def pin_y(a):
    return CR_Y - (CR_R * math.cos(a) + math.sqrt(ROD ** 2 - (CR_R * math.sin(a)) ** 2))


def crown_y(a):
    return pin_y(a) - PIN_H


def accel_force(a):
    """Inertia force of one piston, normalised (primary + secondary terms)."""
    lam = CR_R / ROD
    return np.cos(a) + lam * np.cos(2 * a)


def check_physics():
    bad = []
    aa = np.linspace(0, 2 * math.pi, 721)
    tot1 = sum(np.cos(aa - o) for o in OFF)
    tot2 = sum(np.cos(2 * (aa - o)) for o in OFF)
    if np.max(np.abs(tot1)) > 1e-9 or np.max(np.abs(tot2)) > 1e-9:
        bad.append("six-cylinder forces do not cancel")
    # firing order: TDC-compression every 120 deg in order 1-5-3-6-2-4 over 720 deg
    tdc = {}
    for i in range(NCYL):
        tdc[i + 1] = OFF[i]
    seq = [tdc[c] % (2 * math.pi) for c in FIRING]
    for k in range(len(seq) - 1):
        d = (seq[k + 1] - seq[k]) % (2 * math.pi)
        if abs(d - 2 * math.pi / 3) > 1e-6:
            bad.append("firing interval not 120 deg")
            break
    if crown_y(0) < 1:
        bad.append("piston hits deck")
    return bad


assert not check_physics(), check_physics()

# ================================================================== crank angle vs time (visual, slowed)
REV = 2 * math.pi


def _w(t):
    return smooth(t, [(0.0, REV * 2.2), (T_WHAT, REV * 2.2), (T_BLOCK, REV * 0.55), (T_BAL, REV * 0.55),
                      (T_BAL + 0.8, REV * 0.35), (T_TURBOS, REV * 0.35), (T_TURBOS + 1.0, REV * 0.8),
                      (T_4000, REV * 1.1), (T_KEY, REV * 1.6), (T_LIMIT, REV * 1.6), (T_LIMIT + 1.0, REV * 0.6),
                      (T_TOTAL, REV * 0.6)])


def _build():
    dt = 1 / 600
    ts = np.arange(0, T_TOTAL + 1, dt)
    w = np.array([_w(x) for x in ts])
    ph = np.concatenate([[0.0], np.cumsum(w[:-1]) * dt]) + 0.35
    return ts, ph


_TS, _PH = _build()


def phi_at(t):
    return float(np.interp(t, _TS, _PH))


def rpm_display(t):
    """Engine speed the scene represents (the animation itself is slowed)."""
    return smooth(t, [(0, 6800), (T_WHAT, 6800), (T_BLOCK, 900), (T_FIRST - 0.3, 900), (T_LOW, 2000),
                      (T_4000, 3500), (T_JOINS, 4000), (T_JOINS + 0.8, 4600), (T_KEY, 5400), (T_DOUBLE2, 6600), (T_LIMIT + 0.8, 3000),
                      (T_TOTAL, 3000)])


# ================================================================== camera
CAM_HOOK = (530.0, 850.0, 1.30)
CAM_MAIN = (490.0, 790.0, 1.45)
CAM_BAL = (490.0, 620.0, 1.30)
CAM_TOP = (490.0, 590.0, 1.10)


def cam_xy(t):
    keys = [(0.0, CAM_HOOK), (T_WHAT + 0.3, CAM_HOOK), (T_WHAT + 1.6, CAM_MAIN), (T_BALANCES - 0.2, CAM_MAIN),
            (T_BALANCES + 0.8, CAM_BAL), (T_TURBOS - 0.2, CAM_BAL), (T_TURBOS + 0.9, CAM_TOP),
            (T_LIMIT - 0.3, CAM_TOP), (T_LIMIT + 0.7, CAM_MAIN), (T_TOTAL, CAM_MAIN)]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease(lin(t, t0, t1))
            return np.array(a) * (1 - k) + np.array(b) * k
    return np.array(keys[-1][1])


def cam(t):
    ox, oy, s = cam_xy(t)
    return Proj(ox, oy, s, yaw=42, pitch=24)


# ================================================================== highlight timing helpers
def hl(t, t0, t1):
    return win(t, t0 - 0.1, t1, 0.2, 0.4)


def pair_k(t, i):
    """Pair highlight for the balance beat: pairs (1,6), (2,5), (3,4) light up in turn."""
    p = min(i, NCYL - 1 - i)
    t0 = T_FRONT + (T_BACK - T_FRONT) * p / 3.0
    return win(t, t0, T_HAMMER + 0.3, 0.25, 0.4)


def knock_k(t):
    """Detonation flashes in cylinder 3 during the limit beat."""
    if not (T_DET - 0.2 < t < T_OUTRO + 0.2):
        return 0.0
    k = 0.0
    for tt in (T_DET, T_DET + 0.45, T_PISTONS, T_RODS):
        k = max(k, win(t, tt - 0.02, tt + 0.35, 0.03, 0.3))
    return k


# ================================================================== engine
def web_prof(cx, cy, ang, n=56):
    """Crank web: round boss on the journal + lobe to the pin + counterweight opposite. ang = pin direction."""
    prof = []
    for th in np.linspace(0, 2 * np.pi, n, endpoint=False):
        d = (th - ang) % (2 * np.pi)
        r = 24 + (CR_R + 4) * max(0.0, math.cos(d)) ** 6 + 44 * max(0.0, -math.cos(d)) ** 0.7
        prof.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return np.array(prof)


def draw_engine(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return pj
    ph = phi_at(t)
    h_block = hl(t, T_BLOCK_W, T_CRANK + 0.2)
    h_deck = hl(t, T_CLOSED, T_CRANK + 0.2)
    h_crank = hl(t, T_FORGED, T_BAL + 0.2) + hl(t, T_HAMMER, T_TURBOS)
    h_rods = 0.0
    kk = knock_k(t)
    fade_block = 1 - 0.55 * win(t, T_CRANK + 0.2, T_LIMIT, 0.6, 0.6)   # see-through while we look inside
    cv.saveLayerAlpha(None, int(255 * kE))

    # ---- block back half (glass): drawn first so everything inside shows through
    blk = np.array([[-BX, 0], [BX, 0], [BX, BLOCK_Y1], [-BX, BLOCK_Y1]], float)
    z0, z1 = ZC[0] - 62, ZC[-1] + 62
    blk_c = mix(C_IRON, YEL, 0.25 * h_block)
    extrude(cv, pj, blk, z0, z1, blk_c, alpha=0.30 * fade_block, rim=YEL if h_block > 0.02 else None,
            rim_w=1.6, rim_glow=h_block)

    # ---- collect parts by depth (far first). Depth along the crank: larger z = farther.
    items = []
    for j, zm in enumerate(ZM):
        items.append((zm + 0.5, "main", j))
    for i, zc in enumerate(ZC):
        items.append((zc, "cyl", i))
    items.sort(key=lambda x: -x[0])

    main_on = [eout(lin(t, T_SEVEN + 0.11 * j, T_SEVEN + 0.11 * j + 0.2)) * win(t, T_SEVEN - 0.1, T_BAL + 0.1, 0.1, 0.4)
               for j in range(7)]
    bal_ok = win(t, T_HAMMER, T_TURBOS + 0.2, 0.25, 0.4)
    for _, kind, idx in items:
        if kind == "main":
            zm = ZM[idx]
            mk = max(main_on[idx], 0.0)
            cap_c = mix(C_CAP, YEL, 0.6 * mk)
            cap_c = mix(cap_c, GREEN, 0.5 * bal_ok)
            rev(cv, pj, "z", (0.0, CR_Y), [zm - 13, zm + 13], [16, 16], STEEL, n=36)
            cap = np.array([[-44, CR_Y + 4], [44, CR_Y + 4], [40, CR_Y + 34], [-40, CR_Y + 34]], float)
            extrude(cv, pj, cap, zm - 12, zm + 12, cap_c, rim=YEL if mk > 0.02 else (GREEN if bal_ok > 0.02 else None),
                    rim_w=1.8, rim_glow=max(mk, bal_ok))
            continue
        i = idx
        zc = ZC[i]
        a = ph - OFF[i]
        cpin = (CR_R * math.sin(a), CR_Y - CR_R * math.cos(a))
        top = crown_y(a)
        pin = pin_y(a)
        pk = pair_k(t, i)
        knock = kk if i == 2 else 0.0
        hr = max(h_crank, 0.0)
        web_c = mix(STEEL_D, YEL, 0.3 * hr)
        # back web, pin, rod, front web
        ang = math.atan2(cpin[1] - CR_Y, cpin[0])
        extrude(cv, pj, web_prof(0.0, CR_Y, ang), zc + 22, zc + 34, web_c, rim=YEL if hr > 0.02 else None,
                rim_w=1.6, rim_glow=hr)
        rev(cv, pj, "z", cpin, [zc - 22, zc + 22], [12, 12], STEEL, n=24)
        v = np.array([-cpin[0], pin - cpin[1]])
        v /= np.linalg.norm(v)
        nrm = np.array([-v[1], v[0]])
        big, small = np.array(cpin), np.array([0.0, pin])
        rod_c = mix(C_ROD, RED, 0.8 * knock)
        rod = [big + nrm * 13, small + nrm * 8, small - nrm * 8, big - nrm * 13]
        extrude(cv, pj, np.array(rod), zc - 7, zc + 7, rod_c, rim=RED if knock > 0.02 else None, rim_w=1.8,
                rim_glow=knock)
        extrude(cv, pj, circle_prof(big[0], big[1], 18, 28), zc - 7, zc + 7, rod_c)
        extrude(cv, pj, web_prof(0.0, CR_Y, ang), zc - 34, zc - 22, web_c, rim=YEL if hr > 0.02 else None,
                rim_w=1.6, rim_glow=hr)
        # piston
        pc = mix(STEEL, YEL, 0.3 * pk)
        pc = mix(pc, RED, 0.6 * knock)
        edge = RED if knock > 0.02 else (YEL if pk > 0.02 else None)
        rev(cv, pj, "y", (0.0, zc), [top, top + PISTON_H], [R_B - 2, R_B - 2], pc, n=48,
            edge=edge, edge_w=2 + 1.5 * max(pk, knock), glow=max(pk, knock))
        for yy in (top + 8, top + 15):
            ring_front(cv, pj, "y", (0.0, zc), yy, R_B - 1, shade(STEEL, 0.45), width=1.6)
        if knock > 0:
            q = pj(0, top * 0.5, zc)
            cv.drawCircle(q[0], q[1], 46 * pj.s, paint(hx("#ff5a2a"), a=0.55 * knock, blur=18 * pj.s))
            rng = np.random.default_rng(int(t * 30))
            for _ in range(7):
                an = rng.uniform(0, 2 * math.pi)
                r = rng.uniform(20, 46)
                cv.drawLine(q[0], q[1], q[0] + r * math.cos(an) * pj.s, q[1] + r * math.sin(an) * pj.s,
                            paint(hx("#ffd9a0"), a=knock, stroke=2.2 * pj.s))
        # bore (liner) front edge
        ring_front(cv, pj, "y", (0.0, zc), 120, R_B + 3, hx("#6b7c96"), width=1.4, alpha=0.7)

    # ---- the deck (top face of the block) with six bores; solid around every bore = closed deck
    deck_k = h_deck
    corners = pj(np.array([-BX, BX, BX, -BX]), np.zeros(4), np.array([z0, z0, z1, z1]))
    deck_path = poly_path(corners)
    for i, zc in enumerate(ZC):
        deck_path.addPath(poly_path(pj(*_hc(zc, R_B + 1))))
    deck_path.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(deck_path, paint(mix(hx("#46505e"), hx("#6b5d2a"), 0.5 * deck_k), a=clamp(0.38 + 0.52 * (fade_block - 0.45) / 0.55 + 0.08 * deck_k)))
    if deck_k > 0:
        cv.drawPath(deck_path, paint(YEL, a=0.45 * deck_k, stroke=6 * pj.s, blur=5 * pj.s))
    cv.drawPath(deck_path, paint(mix(hx("#7d8aa0"), YEL, deck_k), a=0.9 * fade_block, stroke=1.6 * pj.s))
    # small coolant holes in the deck (closed deck still passes coolant to the head)
    for i in range(NCYL - 1):
        zm = (ZC[i] + ZC[i + 1]) / 2
        for sx in (-1, 1):
            q = pj(sx * 56, 0, zm)
            cv.drawCircle(q[0], q[1], 4 * pj.s, paint(hx("#0a1220"), a=0.9 * fade_block))
    # braced bores: rings light one by one on "every cylinder"
    for i, zc in enumerate(ZC):
        kr = eout(lin(t, T_EVERY + 0.09 * i, T_EVERY + 0.09 * i + 0.25)) * win(t, T_EVERY, T_CRANK + 0.1, 0.1, 0.4)
        if kr > 0:
            P = pj(*_hc(zc, R_B + 6))
            cv.drawPath(poly_path(P), paint(YEL, a=0.5 * kr, stroke=7 * pj.s, blur=5 * pj.s))
            cv.drawPath(poly_path(P), paint(YEL, a=kr, stroke=2.2 * pj.s))
    # near glass walls (side X = +BX and front end z = z0): faint fill so the x-ray reads as a solid block
    for X_, Z_ in (((BX, BX, BX, BX), (z0, z1, z1, z0)), ((-BX, BX, BX, -BX), (z0, z0, z0, z0))):
        P = pj(np.array(X_), np.array([0, 0, BLOCK_Y1, BLOCK_Y1]), np.array(Z_))
        cv.drawPath(poly_path(P), paint(hx("#6f86a8"), a=0.10 * fade_block))
        cv.drawPath(poly_path(P), paint(hx("#7d8aa0"), a=0.45 * fade_block, stroke=1.3 * pj.s))
    # block front face outline
    ext = 0.75 * fade_block
    fr = pj(np.array([-BX, BX, BX, -BX, -BX]), np.array([0, 0, BLOCK_Y1, BLOCK_Y1, 0]), np.full(5, z0))
    cv.drawPath(poly_path(fr, close=False), paint(mix(hx("#7d8aa0"), YEL, h_block), a=ext, stroke=1.6 * pj.s))
    cv.restore()
    return pj


def _hc(zc, r, n=48):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return r * np.cos(th), np.zeros(n), zc + r * np.sin(th)


# ================================================================== overlays
def draw_hook(cv, t):
    k = 1 - ease(lin(t, T_HOOK_OUT + 0.2, T_WHAT + 0.5))
    if k <= 0:
        return
    a1 = k * eout(lin(t, 0.15, 0.5))
    pill(cv, 540, 1270, "FACTORY: 320 HP", font("inter_xb", 34), INK, border=CYAN, a=a1, align="center", tracking=2)
    a2 = k * eback(lin(t, T_DOUBLE - 0.1, T_DOUBLE + 0.3))
    if a2 > 0:
        pill(cv, 540, 1360, "STOCK ENGINE: 640 HP?", font("inter_xb", 40), INK, border=RED, a=clamp(a2),
             align="center", tracking=2)


def draw_what(cv, t):
    brand.stamp(cv, t, "TRUE?", T_TRUE, dur=1.1, center=(540, 1300), color=YEL, bg=hx("#2a2205"))
    k = win(t, T_LITRE - 0.2, T_BLOCK + 0.2, 0.3, 0.3)
    if k > 0:
        items = [("3.0 LITRE", eout(lin(t, T_LITRE, T_LITRE + 0.25))),
                 ("STRAIGHT SIX", eout(lin(t, T_SIX, T_SIX + 0.25))),
                 ("TOYOTA SUPRA", eout(lin(t, T_SUPRA - 0.2, T_SUPRA + 0.1)))]
        brand.chips(cv, k, 1300, items, center=True)
    # cylinder numbers 1..6 on "six"
    pj = cam(t)
    for i, zc in enumerate(ZC):
        kn = eout(lin(t, T_SIX + 0.08 * i, T_SIX + 0.08 * i + 0.25)) * win(t, T_SIX, T_BLOCK_W, 0.1, 0.4)
        if kn > 0:
            q = pj(-BX - 26, -14, zc)
            pill(cv, q[0], q[1], str(i + 1), font("inter_blk", 30), INK, border=YEL, a=kn, align="center")
    k = win(t, T_WHY - 0.1, T_BLOCK + 0.1, 0.25, 0.3)
    if k > 0:
        pill(cv, 540, 1372, "WHY IT DOESN'T BREAK", font("inter_xb", 30), INK, border=RED, a=k, align="center",
             tracking=3)


def draw_block(cv, t):
    k = win(t, T_IRON - 0.2, T_CRANK + 0.2, 0.25, 0.35)
    if k > 0:
        brand.chips(cv, k, 1300, [("CAST IRON", eout(lin(t, T_IRON, T_IRON + 0.25))),
                                  ("CLOSED DECK", eout(lin(t, T_CLOSED, T_CLOSED + 0.25)))], center=True)
    ka = win(t, T_ALU - 0.1, T_CLOSED, 0.15, 0.25)
    if ka > 0:
        pill(cv, 540, 1376, "NOT ALUMINIUM", font("inter_xb", 28), INK, border=RED, a=ka, align="center", tracking=3)
        cross_icon(cv, 390, 1372, 26, RED, a=ka)
    kb = win(t, T_SOLID - 0.1, T_CRANK + 0.1, 0.25, 0.3)
    if kb > 0:
        pill(cv, 540, 1376, "DECK SOLID AROUND EVERY BORE", font("inter_xb", 28), INK, border=YEL, a=kb,
             align="center", tracking=2)
    brand.stamp(cv, t, "BRACED", T_BRACED, dur=1.4, center=(540, 1170), color=YEL, bg=hx("#2a2205"))


def draw_crank(cv, t):
    k = win(t, T_FORGED - 0.15, T_SEVEN, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1300, "FORGED STEEL CRANKSHAFT", font("inter_xb", 32), INK, border=YEL, a=k, align="center",
             tracking=2)
    k = win(t, T_SEVEN - 0.1, T_BAL + 0.1, 0.2, 0.35)
    if k > 0:
        n = sum(1 for j in range(7) if t >= T_SEVEN + 0.11 * j)
        pill(cv, 540, 1300, f"MAIN BEARINGS: {n} / 7", font("inter_xb", 34), INK, border=YEL, a=k, align="center",
             tracking=2)
    k = win(t, T_EACH - 0.1, T_BAL + 0.1, 0.2, 0.3)
    if k > 0:
        pill(cv, 540, 1376, "ONE EACH SIDE OF EVERY CYLINDER", font("inter_xb", 26), INK, border=MUTED, a=k,
             align="center", tracking=2)
    brand.stamp(cv, t, "NO FLEX", T_FLEX, dur=1.3, center=(540, 1170), color=YEL, bg=hx("#2a2205"))


GX, GY, GW, GH = 140.0, 1150.0, 720.0, 180.0


def draw_balance(cv, t):
    k = win(t, T_BALANCES - 0.2, T_TURBOS + 0.1, 0.35, 0.4)
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    brand.graph_box(cv, (GX, GY, GW, GH), "SHAKING FORCE", xlabel="ONE CRANK TURN")
    mid = GY + GH / 2
    cv.drawLine(GX, mid, GX + GW, mid, paint(hx("#3a4559"), stroke=1.5))
    aa = np.linspace(0, 2 * math.pi, 200)
    one = accel_force(aa)
    p1 = np.stack([GX + GW * aa / (2 * math.pi), mid - one * GH * 0.36], 1)
    brand.curve(cv, p1, AMBER, prog=eout(lin(t, T_BALANCES, T_BALANCES + 1.0)), width=4)
    draw_text(cv, "ONE PISTON", GX + GW - 190, GY - 12, font("inter_xb", 22), AMBER, align="right", tracking=2)
    tot = sum(accel_force(aa - o) for o in OFF)
    ks = eout(lin(t, T_CANCEL - 0.3, T_CANCEL + 0.7))
    if ks > 0:
        p2 = np.stack([GX + GW * aa / (2 * math.pi), mid - tot * GH * 0.36], 1)
        brand.curve(cv, p2, GREEN, prog=ks, width=5)
        draw_text(cv, "ALL SIX = 0", GX + GW, GY - 12, font("inter_xb", 22), GREEN, align="right", tracking=2,
                  a=ks)
    # moving dot: current crank angle
    a = phi_at(t) % (2 * math.pi)
    brand.dot(cv, GX + GW * a / (2 * math.pi), mid - float(accel_force(a)) * GH * 0.36, AMBER)
    cv.restore()
    # mirror pairs label
    kp = win(t, T_FRONT - 0.1, T_SHAKING, 0.25, 0.3)
    if kp > 0:
        pill(cv, 540, 1045, "PAIRS: 1+6 · 2+5 · 3+4", font("inter_xb", 30), INK, border=YEL, a=kp * k,
             align="center", tracking=2)
    brand.stamp(cv, t, "CANCELLED", T_CANCEL + 0.1, dur=1.4, center=(540, 1045), color=GREEN, bg=hx("#06281a"))


# ---- turbos panel
TB1 = (370.0, 1110.0)
TB2 = (710.0, 1110.0)
GAUGE = (270.0, 1190.0, 130.0)


def turbo_speed(t, which):
    """Visual wheel speed 0..1."""
    if which == 0:
        return smooth(t, [(0, 0), (T_FIRST, 0.05), (T_LOW + 0.3, 0.75), (T_4000, 0.85), (T_KEY, 1.0), (T_TOTAL, 1.0)])
    return smooth(t, [(0, 0), (T_JOINS - 0.4, 0.0), (T_JOINS + 0.5, 0.9), (T_KEY, 1.0), (T_TOTAL, 1.0)])


_TT = np.arange(0.0, T_TOTAL + 1.0, 1 / 300)
_TTH = [np.concatenate([[0.0], np.cumsum([turbo_speed(x, w) * 2 * math.pi * 3.5 / 300 for x in _TT[:-1]])])
        for w in (0, 1)]


def _turbo_theta(t, which):
    return float(np.interp(t, _TT, _TTH[which]))


def draw_turbo(cv, t, c, which, a):
    sp = turbo_speed(t, which)
    pj = Proj(c[0], c[1], 0.95, yaw=12, pitch=10)
    on = clamp(sp / 0.6)
    ring = mix(hx("#3a4252"), AMBER, on)
    cv.saveLayerAlpha(None, int(255 * a))
    cv.drawCircle(c[0], c[1], 78, paint(hx("#0b111c"), a=0.9))
    if on > 0.02:
        cv.drawCircle(c[0], c[1], 78, paint(AMBER, a=0.4 * on, stroke=10, blur=8))
    cv.drawCircle(c[0], c[1], 78, paint(ring, stroke=3))
    wheel(cv, pj, "z", (0.0, 0.0), -30.0, 18.0, lambda s: 9 + 30 * s ** 2, lambda s: 40 + 20 * s, 7,
          _turbo_theta(t, which), hx("#a9b6c8"), blade=hx("#d3dcea"), twist=0.9, splitters=True, bp_r=60,
          blur=int(3 * clamp(sp)), blur_step=0.12)
    draw_text(cv, f"TURBO {which + 1}", c[0], c[1] + 122, font("inter_xb", 26), INK, align="center", tracking=2)
    st = "SPOOLING" if (sp > 0.05 and sp < 0.6) else ("BOOST" if sp >= 0.6 else "WAITING")
    draw_text(cv, st, c[0], c[1] + 156, font("inter_sb", 22), mix(MUTED, AMBER, on), align="center", tracking=3)
    cv.restore()


def draw_turbos(cv, t):
    k = win(t, T_TWO - 0.2, T_KEY + 0.2, 0.35, 0.35) * (1 - current.ending_k(t))
    if k <= 0:
        return
    kk = [eback(lin(t, T_TWO, T_TWO + 0.4)), eback(lin(t, T_TWO + 0.2, T_TWO + 0.6))]
    for w, c in enumerate((TB1, TB2)):
        draw_turbo(cv, t, c, w, k * clamp(kk[w]))
    if t > T_IDENT - 0.1:
        ki = k * win(t, T_IDENT - 0.1, T_FIRST, 0.2, 0.3)
        pill(cv, 540, 985, "IDENTICAL", font("inter_xb", 26), INK, border=YEL, a=ki, align="center", tracking=3)
        ks = k * win(t, T_SEQ - 0.1, T_JOINS - 0.1, 0.2, 0.3)
        pill(cv, 540, 985, "1 THEN 2", font("inter_xb", 26), INK, border=AMBER, a=ks, align="center", tracking=3)
    kg = k * eout(lin(t, T_TWO - 0.1, T_TWO + 0.4))
    if kg > 0:
        x0, x1, y = 140.0, 900.0, 1350.0
        r = rpm_display(t)
        cv.drawLine(x0, y, x1, y, paint(hx("#263043"), a=kg, stroke=14, cap=skia.Paint.kRound_Cap))
        xr = x0 + (x1 - x0) * clamp(r / 7000)
        c = mix(CYAN, AMBER, clamp((r - 3600) / 600))
        cv.drawLine(x0, y, xr, y, paint(c, a=kg, stroke=14, cap=skia.Paint.kRound_Cap))
        xm = x0 + (x1 - x0) * 4000 / 7000
        cv.drawLine(xm, y - 22, xm, y + 22, paint(YEL, a=kg, stroke=4))
        draw_text(cv, "4,000 RPM: TURBO 2 JOINS", xm, y - 32, font("inter_xb", 22), YEL, a=kg, align="center",
                  tracking=2)
        draw_text(cv, "RPM", x0, y - 32, font("inter_xb", 22), MUTED, a=kg, tracking=3)
    brand.stamp(cv, t, "TURBO 2 ONLINE", T_JOINS, dur=1.4, center=(540, 960), color=AMBER, bg=hx("#2a1c05"))


def draw_key(cv, t):
    k = win(t, T_EXPORT - 0.2, T_LIMIT + 0.1, 0.3, 0.35)
    if k <= 0:
        return
    x0, x1 = 120.0, 900.0
    hp_max = 700.0
    rows = [(1080.0, "FACTORY (EXPORT)", 320.0, CYAN, T_320, T_HP1_E),
            (1250.0, "STOCK INTERNALS, TUNED", 600.0, RED, T_600, T_STOCK + 0.3)]
    for y, name, hpv, c, ta, tb in rows:
        kr = k * eout(lin(t, ta - 0.4, ta))
        if kr <= 0:
            continue
        g = ease(lin(t, ta, tb))
        draw_text(cv, name, x0, y - 22, font("inter_xb", 26), MUTED, a=kr, tracking=3)
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y, x1 - x0, 56), 14, 14)
        cv.drawRRect(rr, paint(hx("#0b111c"), a=0.9 * kr))
        cv.drawRRect(rr, paint(hx("#2a3446"), a=kr, stroke=2))
        w = (x1 - x0) * hpv / hp_max * g
        if w > 4:
            br = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y, w, 56), 14, 14)
            cv.drawRRect(br, paint(c, a=0.45 * kr, blur=10))
            cv.drawRRect(br, paint(mix(c, hx("#000000"), 0.15), a=kr))
        if g < 0.08:
            continue
        val = ("~" if hpv == 600 else "") + f"{int(round(hpv * g / 10) * 10)} HP"
        draw_text(cv, val, x0 + max(w, 0) + 14 if w < (x1 - x0) - 190 else x0 + w - 14, y + 41,
                  font("inter_blk", 36), INK, a=kr, align="left" if w < (x1 - x0) - 190 else "right")
    brand.stamp(cv, t, "2× FACTORY", T_DOUBLE2, dur=1.6, center=(540, 960))


def draw_limit(cv, t):
    k = win(t, T_KILLS - 0.1, T_END + 0.05, 0.3, 0.3) * (1 - current.ending_k(t))
    if k <= 0:
        return
    k1 = eout(lin(t, T_IRON2 - 0.2, T_IRON2 + 0.1))
    k2 = eout(lin(t, T_TUNE - 0.2, T_TUNE + 0.1))
    x = 300
    brand.bullet(cv, x, 1290, "THE IRON BLOCK", True, a=k * k1)
    brand.bullet(cv, x, 1360, "BAD TUNE · DETONATION", False, a=k * k2)
    pj = cam(t)
    top = crown_y(phi_at(t) - OFF[2])
    brand.label(cv, t, "DETONATION", tuple(pj(-R_B, top * 0.5, ZC[2])), (90, 520), RED, T_DET - 0.05, T_OUTRO + 0.2)
    brand.stamp(cv, t, "KNOCK", T_DET + 0.05, dur=1.2, center=(780, 520))


def draw_labels(cv, t):
    pj = cam(t)
    kE = 1 - current.ending_k(t)
    if kE <= 0:
        return
    brand.label(cv, t, "IRON BLOCK", tuple(pj(-BX, 120, ZC[0] - 62)), (90, 560), STEEL, T_BLOCK_W - 0.05,
                T_CLOSED - 0.1)
    brand.label(cv, t, "CLOSED DECK", tuple(pj(-BX + 10, 0, ZC[1])), (90, 560), YEL, T_CLOSED - 0.05,
                T_CRANK + 0.1)
    brand.label(cv, t, "CRANKSHAFT", tuple(pj(0, CR_Y + 30, ZC[0] - 30)), (90, 560), YEL, T_CRANKSHAFT - 0.1,
                T_SEVEN)
    brand.label(cv, t, "MAIN BEARINGS", tuple(pj(-40, CR_Y + 30, ZM[0])), (90, 560), YEL, T_SEVEN - 0.05,
                T_BAL + 0.1)
    # pair arcs (balance beat): connect mirrored cylinders over the deck
    for p in range(3):
        kp = pair_k(t, p)
        if kp <= 0:
            continue
        za, zb = ZC[p], ZC[NCYL - 1 - p]
        hgt = 30 + 28 * (2 - p)
        zz = np.linspace(za, zb, 40)
        yy = -hgt * np.sin(np.linspace(0, math.pi, 40))
        P = pj(np.zeros(40), yy - 8, zz)
        cv.drawPath(poly_path(P, close=False), paint(YEL, a=0.9 * kp * kE, stroke=3))


def draw_header(cv, t):
    k = win(t, T_WHAT + 0.4, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(T_BLOCK, "THE BLOCK", YEL), (T_CRANK, "THE BOTTOM END", YEL), (T_BAL, "BALANCE", GREEN),
           (T_TURBOS, "SEQUENTIAL TWIN TURBOS", AMBER), (T_KEY, "THE POWER", RED), (T_LIMIT, "WHAT BREAKS IT", RED)]
    txt, c = "2JZ-GTE · STRAIGHT SIX", CYAN
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    r = rpm_display(t)
    brand.readout(cv, k, f"{int(round(r / 100) * 100):,}", "ENGINE RPM", frac=r / 8000, bar_color=c,
                  marker_frac=4000 / 8000 if T_TURBOS - 0.2 < t < T_LIMIT else None)
    brand.note(cv, "ANIMATION SLOWED", k * 0.9)


def draw(cv, t):
    draw_engine(cv, t)
    draw_labels(cv, t)
    draw_hook(cv, t)
    draw_what(cv, t)
    draw_block(cv, t)
    draw_crank(cv, t)
    draw_balance(cv, t)
    draw_turbos(cv, t)
    draw_key(cv, t)
    draw_limit(cv, t)
    draw_header(cv, t)


# ================================================================== sound
BEAT_ANCHOR = T_JOINS
MUSIC_START = T_WHAT


def sound():
    sfx = [(T_HOOK_OUT - 0.1, "whoosh_big", 0.6), (T_TRUE, "impact", 0.45), (T_BLOCK_W, "clunk", 0.35),
           (T_CLOSED, "tick", 0.25), (T_BRACED, "impact", 0.45), (T_FORGED, "clunk", 0.35)]
    sfx += [(T_SEVEN + 0.11 * j, "tick", 0.18) for j in range(7)]
    sfx += [(T_FLEX, "impact", 0.4), (T_CANCEL, "whoosh_down", 0.4), (T_FIRST, "spool", 0.4),
            (T_JOINS, "spool", 0.55), (T_JOINS + 0.1, "impact", 0.4), (T_320, "tick", 0.25), (T_600, "whoosh_up", 0.4),
            (T_DOUBLE2, "impact", 0.65), (T_DET, "clunk", 0.45), (T_PISTONS, "clunk", 0.35), (T_RODS, "clunk", 0.35)]
    eng = {"rpm": rpm_display, "bright": lambda t: 0.5 if T_4000 < t < T_LIMIT else 0.25,
           "env": [(0, 0.8), (T_WHAT, 0.8), (T_BLOCK, 0.15), (T_TURBOS, 0.15), (T_FIRST, 0.45), (T_LIMIT, 0.55),
                   (T_LIMIT + 1.0, 0.2), (T_END, 0.2), (T_END + 0.6, 0.0), (T_TOTAL, 0.0)]}
    return {"build": (T_TURBOS, T_JOINS), "drop": (T_JOINS, T_OUTRO - 0.05), "sfx": sfx, "engine": eng}
