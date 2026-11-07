"""Rotary (Mazda 13B) visuals + sound plan. Every cue is tied to a narration word via F(line, word).

Scenes
  ROAD     (hook)      night road, a generic 90s coupe (no badges) driving; the hood x-rays to two spinning rotors;
                       "3 MOVING PARTS" tag, then "WHERE ARE THE VALVES?"
  WHAT     (what)      push into one rotor housing, spinning fast, spec pill 13B / 2 ROTORS / 1.3 L
  PROBLEM  (problem)   two cards: piston engine (piston + crank + two cam-driven valves) vs the rotor that just spins
  PARTS    (parts)     housing appears, rotor drops in, camera swings to a 3/4 view: two rotors on one eccentric
                       shaft (lobes 180 deg apart); 1-2-3 count
  GEARS    (gears)     face-on x-ray: 36-tooth ring gear in the rotor rolls round the 24-tooth fixed gear; live
                       counters SHAFT 0..3 vs ROTOR 0..1
  GAPS     (rehook)    the three gaps light up 1, 2, 3
  CYCLE    (chambers)  one chamber tracked through intake / compression / power / exhaust with a live volume graph,
                       spark at the plugs at minimum volume, power-stroke counter
  PORTS    (key)       close on the side ports: the rotor body really covers / uncovers them; flow when open
  SEAL     (catch)     camera rides one apex; the apex seal wears and gas leaks past the tip
  OUTRO    (outro)     NO CAMS / NO SPRINGS / NO VALVES chips over the spinning rotor, fades into the end card

Mechanism model (profile units, y down; see research.md):
  housing = epitrochoid x = e cos3a + R cos a, y = e sin3a + R sin a, R = 210, e = 30 (R/e = 7)
  shaft angle th; rotor centre = e (cos th, sin th); rotor angle phi = th / 3; apex k at centre + R dir(phi + 2pi k/3)
  (the apexes lie exactly on the housing). Ring gear (pitch r 3e, 36 teeth) on the rotor rolls on the fixed gear
  (pitch r 2e, 24 teeth): rolling contact gives phi' = th'/3. Chamber k (apex k -> k+1) is at bottom dead centre
  (face at the port side) when th = pi/2 - 2 pi k (mod 6 pi). check_physics() asserts flank clearance, the
  rolling ratio and that the intake/exhaust ports open only to expanding/shrinking chambers (outside the overlap).
"""
import math
import os

import numpy as np
import skia
from matplotlib.path import Path as MPath
from scipy.interpolate import PchipInterpolator

from ev import brand, current, look
from ev.current import tl
from ev.gfx import *
from ev.parts import cyl3

F, L = tl.find, tl.line
T_TOTAL = tl.total
T_END, T_TOPIC = current.t_end, current.t_topic
T_HOOK_OUT = current.hook_out

# ================================================================== cue times
T_FANS = F("hook", "fans")
T_THREE_H = F("hook", "three")
T_PARTS_H = F("hook", "parts.")
T_WHERE = F("hook", "where")
T_VALVES_H = F("hook", "valves?")
T_WHAT = L("what")["start"]
T_ROTARY_W = F("what", "rotary")
T_INSIDE = F("what", "inside")
T_13B = F("what", "13b.")
T_PROB = L("problem")["start"]
T_PISTONS = F("problem", "pistons")
T_UPDOWN = F("problem", "up")
T_CAMS = F("problem", "camshafts")
T_VALVES_P = F("problem", "valves")
T_INOUT = F("problem", "out.")
T_SPINS = F("problem", "spins.")
T_PARTS = L("parts")["start"]
T_HOUSING = F("parts", "housing.")
T_ROTOR_P = F("parts", "rotor.")
T_TWO = F("parts", "two")
T_ECC = F("parts", "eccentric")
T_ALL = F("parts", "all")
T_THREE_P = F("parts", "three")
T_MOVING = F("parts", "moving")
T_GEARS = L("gears")["start"]
T_GEAR_IN = F("gears", "gear")
T_FIXED = F("gears", "fixed")
T_SPINS_G = F("gears", "spins")
T_THREE_G = F("gears", "three")
T_ROTOR_G = F("gears", "rotor.")
T_REHOOK = L("rehook")["start"]
T_GAPS = F("rehook", "gaps.")
T_FOR = F("rehook", "for?")
T_CH = L("chambers")["start"]
T_CHAMBER = F("chambers", "chamber.")
T_GROWS1 = F("chambers", "grows,")
T_SHRINKS1 = F("chambers", "shrinks,")
T_GROWS2 = F("chambers", "grows", 1)
T_SHRINKS2 = F("chambers", "shrinks", 1)
T_INTAKE = F("chambers", "intake,")
T_COMP = F("chambers", "compression,")
T_POWER = F("chambers", "power,")
T_EXH = F("chambers", "exhaust.")
T_THREE_C = F("chambers", "three")
T_EVERY_C = F("chambers", "turn.")
T_KEY = L("key")["start"]
T_VALVES_K = F("key", "valves?")
T_ITSELF = F("key", "itself.")
T_PORTS = F("key", "ports")
T_UNCOV = F("key", "uncovering")
T_COVER = F("key", "covering")
T_CATCH = L("catch")["start"]
T_TIPS = F("catch", "tips.")
T_APEX = F("catch", "apex")
T_SHUT = F("catch", "shut,")
T_WEAR = F("catch", "wear,")
T_LEAKS = F("catch", "leaks")
T_OUTRO = L("outro")["start"]
T_NOCAMS = F("outro", "cams.")
T_NOSPR = F("outro", "springs.")
T_NOVAL = F("outro", "valves.")

S_ROAD = (0.0, T_WHAT + 0.35)
S_UNIT = (T_WHAT - 0.15, T_PROB + 0.3)
S_PROB = (T_PROB - 0.1, T_PARTS + 0.3)
S_PARTS = (T_PARTS - 0.1, T_GEARS + 0.35)
S_FACE = (T_GEARS - 0.1, T_CATCH + 0.35)       # face-on single rotor: gears, gaps, cycle, ports
S_SEAL = (T_CATCH - 0.1, T_OUTRO + 0.35)
S_OUT = (T_OUTRO - 0.1, T_TOTAL + 1.0)


def scene_k(t, s, fin=0.3, fout=0.3):
    return win(t, s[0], s[1], fin, fout)


# ================================================================== mechanism model
R_, E_ = 210.0, 30.0
SAG = 38.0           # flank bulge (checked: clears the housing at every angle, chamber volume ratio ~8.6)
DEPTH = 80.0
N_RING, N_FIX = 36, 24
TAU = 2 * math.pi


def troch(a):
    a = np.asarray(a, float)
    return np.stack([E_ * np.cos(3 * a) + R_ * np.cos(a), E_ * np.sin(3 * a) + R_ * np.sin(a)], -1)


def housing_prof(off=0.0, n=360):
    a = np.linspace(0, TAU, n, endpoint=False)
    p = troch(a)
    if off:
        d = np.stack([-3 * E_ * np.sin(3 * a) - R_ * np.sin(a), 3 * E_ * np.cos(3 * a) + R_ * np.cos(a)], -1)
        nrm = np.stack([d[:, 1], -d[:, 0]], -1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        p = p + off * nrm
    return p


def rcenter(th):
    return np.array([E_ * math.cos(th), E_ * math.sin(th)])


def apexes(th):
    c, ph = rcenter(th), th / 3
    return [c + R_ * np.array([math.cos(ph + TAU * k / 3), math.sin(ph + TAU * k / 3)]) for k in range(3)]


def flank(th, k, n=24, sag=SAG, endpoint=False):
    ph = th / 3
    a0, a1 = ph + TAU * k / 3, ph + TAU * (k + 1) / 3
    c = rcenter(th)
    p0 = c + R_ * np.array([math.cos(a0), math.sin(a0)])
    p1 = c + R_ * np.array([math.cos(a1), math.sin(a1)])
    m = (a0 + a1) / 2
    out = np.array([math.cos(m), math.sin(m)])
    u = np.linspace(0, 1, n + 1 if endpoint else n, endpoint=endpoint)[:, None]
    return p0 + (p1 - p0) * u + out * sag * 4 * u * (1 - u)


def rotor_prof(th, n=24, sag=SAG):
    return np.vstack([flank(th, k, n, sag) for k in range(3)])


def chamber_prof(th, k, n=60):
    ph = th / 3
    a0 = ph + TAU * k / 3
    al = np.linspace(a0, a0 + TAU / 3, n)
    return np.vstack([troch(al), flank(th, k, 30, endpoint=True)[::-1]])


def _area(p):
    return 0.5 * abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


_VG = np.linspace(0, 6 * math.pi, 721)
_V0 = np.array([_area(chamber_prof(th, 0)) for th in _VG])
V_MIN, V_MAX = _V0.min(), _V0.max()


def vol(th, k):
    """Chamber k area at shaft angle th (V_k(th) = V_0(th + 2 pi k))."""
    return float(np.interp((th + TAU * k) % (6 * math.pi), _VG, _V0))


def psi(th, k):
    """Cycle phase of chamber k: 0 at bottom dead centre (start of intake), 6 pi per cycle."""
    return (th - math.pi / 2 + TAU * k) % (6 * math.pi)


STAGES = [("INTAKE", AMBER), ("COMPRESSION", AMBER), ("POWER", RED), ("EXHAUST", MUTED)]


def stage(th, k):
    return int(psi(th, k) // (1.5 * math.pi)) % 4


# ports (side ports in the side housing, opposite the plugs) and plugs
def _port_poly(ang_deg, r=155.0, w=50.0, h=30.0):
    a = math.radians(ang_deg)
    c = np.array([r * math.cos(a), r * math.sin(a)])
    tng, rad = np.array([-math.sin(a), math.cos(a)]), np.array([math.cos(a), math.sin(a)])
    q = np.linspace(0, TAU, 28, endpoint=False)
    # rounded rectangle-ish (superellipse)
    pts = [c + tng * (w / 2) * np.sign(math.cos(x)) * abs(math.cos(x)) ** 0.5
           + rad * (h / 2) * np.sign(math.sin(x)) * abs(math.sin(x)) ** 0.5 for x in q]
    return np.array(pts), c


PORT_IN, PORT_IN_C = _port_poly(117.0)
PORT_EX, PORT_EX_C = _port_poly(63.0)
_PORT_SAMPLES = {}
for _nm, _poly, _c in (("in", PORT_IN, PORT_IN_C), ("ex", PORT_EX, PORT_EX_C)):
    _PORT_SAMPLES[_nm] = np.vstack([_c] + [_c + 0.6 * (p - _c) for p in _poly[::3]])
PLUGS = [np.array([-26.0, -(R_ - E_) - 2]), np.array([26.0, -(R_ - E_) - 2])]


def port_open(th, which):
    """Uncovered fraction of a port (0 = rotor body over it) and the chamber it opens into."""
    pts = _PORT_SAMPLES[which]
    rp = MPath(rotor_prof(th, 16))
    inside = rp.contains_points(pts)
    frac = 1.0 - inside.mean()
    kk = None
    for k in range(3):
        if MPath(chamber_prof(th, k, 30)).contains_point(tuple(pts[0])):
            kk = k
    return frac, kk


def check_physics():
    bad = []
    from scipy.spatial import cKDTree
    hp = housing_prof(0, 2000)
    tree, hpath = cKDTree(hp), MPath(hp)
    worst = 1e9
    for th in np.linspace(0, 6 * math.pi, 240):
        r = rotor_prof(th, 20)
        msk = np.ones(len(r), bool)
        msk[::20] = False
        d, _ = tree.query(r[msk])
        d = np.where(hpath.contains_points(r[msk]), d, -d)
        worst = min(worst, d.min())
        for p in apexes(th):     # apexes on the housing
            if tree.query(p)[0] > 2.0:
                bad.append(f"apex off housing at th={th:.2f}")
                break
    if worst <= 0.5:
        bad.append(f"rotor flank hits the housing (clearance {worst:.2f})")
    # rolling contact: ring pitch 3e, fixed pitch 2e; contact point velocity = e th' - 3e phi' = 0 for phi' = th'/3
    if abs(E_ * 1.0 - 3 * E_ * (1.0 / 3)) > 1e-9 or N_RING * 2 != N_FIX * 3:
        bad.append("gear ratio inconsistent")
    # ports: intake only to an expanding chamber, exhaust only to a shrinking one (allow overlap near TDC)
    for th in np.linspace(0, 6 * math.pi, 360):
        for which, want in (("in", +1), ("ex", -1)):
            frac, kk = port_open(th, which)
            if frac > 0.3 and kk is not None:
                ps = psi(th, kk)
                near_tdc = ps < 0.9 or ps > 6 * math.pi - 0.9
                dv = vol(th + 0.01, kk) - vol(th - 0.01, kk)
                if not near_tdc and np.sign(dv) != want:
                    bad.append(f"{which} port open to wrong stroke at th={th:.2f} (psi={ps:.2f})")
                    break
    if V_MAX / V_MIN < 6:
        bad.append("volume ratio too low")
    if bad:
        raise AssertionError("; ".join(sorted(set(bad))[:5]))


check_physics()


# ================================================================== shaft angle over time (animation slowed)
def _build_theta():
    rev = TAU
    keys = [(0.0, 0.0)]

    def run(t1, rps):
        t0, th0 = keys[-1]
        keys.append((t1, th0 + rps * rev * (t1 - t0)))

    run(T_WHAT + 0.4, 2.2)                 # running engine in the car / first look
    run(T_13B, 1.0)
    run(T_PROB, 0.6)
    run(T_PARTS, 0.5)
    run(T_SPINS_G - 0.05, 0.35)
    keys.append((T_ROTOR_G + 0.15, keys[-1][1] + 3 * rev))   # exactly 3 shaft turns = 1 rotor turn
    run(T_GROWS1 - 0.6, 0.3)
    # tracked chamber at bottom dead centre on "grows": th = pi/2 (mod 2 pi) for one of the chambers
    th_a = keys[-1][1] + 0.3 * rev * 0.6
    base = math.pi / 2 + rev * math.ceil((th_a - math.pi / 2) / rev)
    keys.append((T_GROWS1, base))
    keys.append((T_SHRINKS1, base + 1.5 * math.pi))
    keys.append((T_GROWS2, base + 3.0 * math.pi))
    keys.append((T_SHRINKS2, base + 4.5 * math.pi))
    keys.append((T_INTAKE, base + 6.0 * math.pi))
    keys.append((T_COMP, base + 7.5 * math.pi))
    keys.append((T_POWER, base + 9.0 * math.pi))
    keys.append((T_EXH, base + 10.5 * math.pi))
    run(T_KEY, 0.45)
    run(T_CATCH, 0.5)
    run(T_OUTRO, 0.22)
    run(T_TOTAL + 1.0, 1.2)
    ts = np.array([k[0] for k in keys])
    ths = np.array([k[1] for k in keys])
    keep = np.concatenate([[True], np.diff(ts) > 1e-3])
    return PchipInterpolator(ts[keep], ths[keep]), base


_THF, TH_BASE = _build_theta()
TRACK = int(round(((math.pi / 2 - TH_BASE) / TAU))) % 3     # chamber with psi = 0 at TH_BASE
assert abs(psi(TH_BASE, TRACK)) < 1e-6 or abs(psi(TH_BASE, TRACK) - 6 * math.pi) < 1e-6


def theta(t):
    return float(_THF(t))


# ================================================================== drawing the rotor unit
def ojp(cx, cy, s, dx=0.26, dy=-0.2):
    return Proj(cx, cy, s, dx=dx, dy=dy)


def gear_ext(cx, cy, r, n, rot, h=6.0):
    pts = []
    for j in range(n):
        a = rot + TAU * j / n
        da = TAU / n
        pts += [(cx + (r - h) * math.cos(a - 0.5 * da), cy + (r - h) * math.sin(a - 0.5 * da)),
                (cx + (r - h) * math.cos(a - 0.3 * da), cy + (r - h) * math.sin(a - 0.3 * da)),
                (cx + (r + h) * math.cos(a - 0.15 * da), cy + (r + h) * math.sin(a - 0.15 * da)),
                (cx + (r + h) * math.cos(a + 0.15 * da), cy + (r + h) * math.sin(a + 0.15 * da)),
                (cx + (r - h) * math.cos(a + 0.3 * da), cy + (r - h) * math.sin(a + 0.3 * da))]
    return np.array(pts)


def gear_int(cx, cy, r, n, rot, h=6.0):
    """Internal teeth (pointing inward), tooth centres at rot + 2 pi j / n."""
    pts = []
    da = TAU / n
    for j in range(n):
        a = rot + TAU * j / n
        pts += [(cx + (r + h) * math.cos(a - 0.5 * da), cy + (r + h) * math.sin(a - 0.5 * da)),
                (cx + (r + h) * math.cos(a - 0.3 * da), cy + (r + h) * math.sin(a - 0.3 * da)),
                (cx + (r - h) * math.cos(a - 0.15 * da), cy + (r - h) * math.sin(a - 0.15 * da)),
                (cx + (r - h) * math.cos(a + 0.15 * da), cy + (r - h) * math.sin(a + 0.15 * da)),
                (cx + (r + h) * math.cos(a + 0.3 * da), cy + (r + h) * math.sin(a + 0.3 * da))]
    return np.array(pts)


def P2(pj, pts, z):
    pts = np.asarray(pts, float)
    return pj(pts[:, 0], pts[:, 1], np.full(len(pts), z))


def chamber_color(th, k, mode):
    if mode == "stage":
        st = stage(th, k)
        c = STAGES[st][1]
        if st == 1:
            c = mix(AMBER, hx("#ff8a20"), clamp(psi(th, k) / (1.5 * math.pi) - 1))
        return c
    return [CYAN, YEL, GREEN][k]


def draw_unit(cv, pj, th, a=1.0, rotor_a=1.0, rotor_dy=0.0, gears=0.0, ch_mode=None, ch_a=0.0, ch_only=None,
              ports=0.0, plugs=0.0, seals=0.0, spark=0.0, housing_a=1.0, seal_wear=0.0, glow_rotor=0.0,
              ring_hl=0.0, fix_hl=0.0, shaft_hl=0.0, z0=0.0):
    """One rotor + its housing in an oblique x-ray view. z0 shifts the whole unit along the shaft."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    zf, zb = z0, z0 + DEPTH
    # outer housing block (x-ray steel)
    outer = housing_prof(46.0, 200)
    if housing_a > 0:
        extrude(cv, pj, outer, zf, zb, hx("#2a3446"), alpha=0.55 * housing_a, outline=True)
        # back side-housing face inside the trochoid
        cv.drawPath(poly_path(P2(pj, housing_prof(0, 240), zb)), paint(hx("#0a111d"), a=0.92 * housing_a))
        cv.drawPath(poly_path(P2(pj, housing_prof(0, 240), zb)), paint(STEEL_D, a=0.8 * housing_a, stroke=2))
    # ports in the side housing
    if ports > 0:
        for nm, poly in (("in", PORT_IN), ("ex", PORT_EX)):
            frac, kk = port_open(th, nm)
            c = AMBER if nm == "in" else MUTED
            pth = poly_path(P2(pj, poly, zb))
            cv.drawPath(pth, paint(hx("#020407"), a=ports))
            cv.drawPath(pth, paint(c, a=ports * (0.35 + 0.65 * frac), stroke=3.5))
            if frac > 0.2:
                cv.drawPath(pth, paint(c, a=0.45 * ports * frac, blur=9))
    # rotor
    if rotor_a > 0:
        cv.save()
        cv.translate(0, rotor_dy)
        rp = rotor_prof(th, 28)
        extrude(cv, pj, rp, zf + 8, zb - 8, STEEL, alpha=rotor_a, rim=RED if glow_rotor > 0 else None,
                rim_w=3.0, rim_glow=glow_rotor)
        c = rcenter(th)
        ph = th / 3
        # eccentric journal on the shaft (lobe), turning with the shaft
        lobe = circle_prof(c[0], c[1], 64.0, 48)
        cv.drawPath(poly_path(P2(pj, lobe, zf + 7)), paint(hx("#3a4456"), a=rotor_a))
        cv.drawPath(poly_path(P2(pj, lobe, zf + 7)), paint(hx("#5a6577"), a=rotor_a, stroke=2))
        if gears > 0:
            ring = gear_int(c[0], c[1], 3 * E_, N_RING, ph + math.pi / N_RING, 6.0)
            path = poly_path(P2(pj, ring, zf + 7))
            cv.drawPath(path, paint(mix(STEEL_D, AMBER, ring_hl), a=gears * rotor_a, stroke=3.0))
            fx = gear_ext(0.0, 0.0, 2 * E_, N_FIX, 0.0, 6.0)
            fpath = poly_path(P2(pj, fx, zf + 5))
            cv.drawPath(fpath, paint(mix(hx("#1c2636"), hx("#0b3442"), fix_hl), a=gears * 0.95))
            cv.drawPath(fpath, paint(mix(STEEL, CYAN, fix_hl), a=gears, stroke=2.6))
            if fix_hl > 0:
                cv.drawPath(fpath, paint(CYAN, a=0.4 * fix_hl * gears, stroke=7, blur=6))
            if ring_hl > 0:
                cv.drawPath(path, paint(AMBER, a=0.4 * ring_hl * gears, stroke=7, blur=6))
        # shaft + eccentric throw marker
        sc_ = pj(0.0, 0.0, zf + 3)
        cc_ = pj(c[0], c[1], zf + 3)
        rs = 24 * pj.s
        cv.drawCircle(*sc_, rs, paint(mix(hx("#6b7688"), RED, shaft_hl), a=rotor_a))
        cv.drawCircle(*sc_, rs, paint(hx("#20262f"), a=rotor_a, stroke=2))
        tip = np.array(sc_) + (np.array(cc_) - np.array(sc_)) * 1.9
        cv.drawLine(*sc_, *tip, paint(RED, a=rotor_a * (0.5 + 0.5 * shaft_hl), stroke=5 * pj.s / 1.0 + 1,
                                      cap=skia.Paint.kRound_Cap))
        cv.drawCircle(*tip, 6 * pj.s + 1, paint(RED, a=rotor_a))
        # rotor marker (shows the rotor's slow turn)
        mk = c + 150 * np.array([math.cos(ph + math.pi / 3), math.sin(ph + math.pi / 3)])
        mp = pj(mk[0], mk[1], zf + 7)
        cv.drawCircle(*mp, 9 * pj.s + 2, paint(YEL, a=rotor_a * 0.9))
        # apex seals
        if seals > 0:
            for k, ap in enumerate(apexes(th)):
                d = ap - c
                d /= np.linalg.norm(d)
                wear = seal_wear if k == 0 else 0.0
                p0 = ap - d * 16
                p1 = ap - d * (1.0 + 7.0 * wear)
                for z in (zf + 8,):
                    q0, q1 = pj(p0[0], p0[1], z), pj(p1[0], p1[1], z)
                    cv.drawLine(*q0, *q1, paint(RED, a=seals * rotor_a, stroke=6 * pj.s,
                                                cap=skia.Paint.kButt_Cap))
                b0, b1 = pj(p1[0], p1[1], zf + 8), pj(p1[0], p1[1], zb - 8)
                cv.drawLine(*b0, *b1, paint(RED, a=0.8 * seals * rotor_a, stroke=3 * pj.s))
        cv.restore()
    # chambers (gas), drawn over the rotor's far side faces
    if ch_a > 0 and ch_mode:
        for k in range(3):
            if ch_only is not None and k != ch_only:
                kk = 0.18
            else:
                kk = 1.0
            c = chamber_color(th, k, ch_mode)
            pth = poly_path(P2(pj, chamber_prof(th, k, 50), zf + 8))
            if ch_mode == "stage" and stage(th, k) == 2:
                c = mix(RED, AMBER, clamp(1 - (psi(th, k) - 3 * math.pi) / 1.2))
            cv.drawPath(pth, paint(c, a=0.42 * ch_a * kk))
            cv.drawPath(pth, paint(c, a=0.75 * ch_a * kk, stroke=2.5))
    # front housing wall (x-ray outline)
    if housing_a > 0:
        hp = poly_path(P2(pj, housing_prof(0, 240), zf))
        cv.drawPath(hp, paint(CYAN, a=0.35 * housing_a, stroke=7, blur=6))
        cv.drawPath(hp, paint(CYAN, a=0.9 * housing_a, stroke=2.5))
        bp = poly_path(P2(pj, housing_prof(0, 240), zb))
        cv.drawPath(bp, paint(CYAN, a=0.25 * housing_a, stroke=1.5))
    # spark plugs at the minor axis
    if plugs > 0:
        for p in PLUGS:
            q0 = pj(p[0], p[1] - 60, zf + 40)
            q1 = pj(p[0], p[1], zf + 40)
            cv.drawLine(*q0, *q1, paint(hx("#d9dee8"), a=plugs, stroke=12 * pj.s))
            cv.drawLine(q0[0], q0[1] - 30 * pj.s, *q0, paint(hx("#f2f2f2"), a=plugs, stroke=16 * pj.s))
            if spark > 0:
                look.bloom(cv, q1[0], q1[1] + 6 * pj.s, 26 * pj.s, hx("#bfe8ff"), a=spark)
                look.bloom(cv, q1[0], q1[1] + 6 * pj.s, 60 * pj.s, AMBER, a=0.5 * spark)
    cv.restore()


def spark_k(th):
    """Spark flash for whichever chamber is at top dead centre (psi = 3 pi)."""
    best = 0.0
    for k in range(3):
        d = psi(th, k) - 3 * math.pi
        if -0.15 < d < 0.9:
            best = max(best, 1 - (d + 0.15) / 1.05)
    return best


# ================================================================== ROAD (hook)
HORIZON = 940
ROAD_Y = 1170.0
C_TIRE = hx("#15171b")
CAR_COL = hx("#b8322e")
CAR_PROF = np.array([[5, -30], [0, -60], [10, -86], [110, -96], [165, -128], [262, -130], [322, -96],
                     [438, -80], [462, -60], [458, -30]], float)
WHEEL_X = (88.0, 372.0)
WHEEL_R = 32.0


def car_proj(cx, cy, s):
    return Proj(cx, cy, s, yaw=76, pitch=9)


def draw_car(cv, pj, t, base, xray=0.0):
    """Generic 90s two-door coupe facing +X (units cm, wheels on Y = 0). No badges, no logos."""
    zf, zb = -86.0, 86.0
    for x in WHEEL_X:
        cyl3(cv, pj, (x, -WHEEL_R, zb - 30), (x, -WHEEL_R, zb), WHEEL_R, C_TIRE, n=32, edge=hx("#000000"))
    ca = 1 - 0.5 * xray
    extrude(cv, pj, CAR_PROF, zf, zb, base, alpha=ca)
    sw = pj(np.array([172, 258, 312, 160]), np.array([-123, -125, -98, -98]), np.full(4, zf - 1))
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad(tuple(sw[0]), tuple(sw[2]), [hx("#8fb3df"), hx("#0f1a2b")]))
    g.setAlphaf(0.9 * ca)
    cv.drawPath(poly_path(sw), g)
    dl = pj(np.array([300, 300]), np.array([-94, -36]), np.full(2, zf - 1))
    cv.drawLine(*dl[0], *dl[1], paint(shade(base, 0.45), a=ca, stroke=2))
    hood_c = pj(392, -60, 0)
    if xray > 0:
        hood = pj(np.array([330, 452, 452, 330]), np.array([-90, -76, -36, -36]), np.zeros(4))
        cv.drawPath(poly_path(hood), paint(hx("#06202c"), a=0.85 * xray))
        cv.drawPath(poly_path(hood), paint(CYAN, a=0.8 * xray, stroke=2))
        th = theta(t)
        for i, dxp in enumerate((-26, 26)):
            q = (hood_c[0] + dxp * pj.s / 0.6, hood_c[1])
            mp = ojp(q[0], q[1], 0.085 * pj.s / 0.6, 0.0, 0.0)
            draw_unit(cv, mp, th + math.pi * i, a=xray, ch_mode="stage", ch_a=0.9, housing_a=1.0)
    rot = -t * 9.0
    for x in WHEEL_X:
        cyl3(cv, pj, (x, -WHEEL_R, zf - 4), (x, -WHEEL_R, zf + 26), WHEEL_R, C_TIRE, n=40, edge=hx("#000000"))
        hub = pj(x, -WHEEL_R, zf - 5)
        r = 21 * pj.s
        cv.drawCircle(*hub, r, paint(hx("#aeb7c4")))
        for k in range(5):
            an = rot + k * TAU / 5
            cv.drawLine(hub[0], hub[1], hub[0] + r * math.cos(an), hub[1] + r * math.sin(an),
                        paint(hx("#3b4352"), stroke=3.2 * pj.s / 0.55))
        cv.drawCircle(*hub, 5 * pj.s / 0.55, paint(hx("#3b4352")))
    hl = pj(458, -58, zf + 20)
    look.bloom(cv, hl[0], hl[1], 8 * pj.s / 0.55, hx("#fff4d6"), a=0.95)
    tlp = pj(2, -68, zf + 18)
    look.bloom(cv, tlp[0], tlp[1], 6 * pj.s / 0.55, RED, a=0.85)
    return hl, hood_c


def road_cam(t):
    k = ease(lin(t, T_WHERE - 0.3, T_WHAT + 0.3))
    s = 1.0 + 1.3 * k
    return s, k


def draw_road(cv, t, k):
    if k <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * k))
    look.night_sky(cv, HORIZON, t=t)
    look.mountains(cv, HORIZON, offset=t * 60)
    look.haze(cv, HORIZON - 240, HORIZON + 60, a=0.10)
    s, kz = road_cam(t)
    road_top = ROAD_Y - 70
    rp = skia.Paint()
    rp.setShader(lin_grad((0, road_top), (0, H), [hx("#1b1f27"), hx("#0b0d11")]))
    cv.drawRect(skia.Rect.MakeLTRB(0, road_top, W, H), rp)
    cv.drawRect(skia.Rect.MakeLTRB(0, road_top, W, road_top + 8), paint(hx("#3a4250")))
    spd = 900.0
    off = (t * spd) % 300
    for i in range(-1, 6):
        x = i * 300 - off
        cv.drawRect(skia.Rect.MakeXYWH(x, ROAD_Y + 140, 150, 12), paint(hx("#d8d2a8"), a=0.5))
    off2 = (t * spd * 0.55) % 520
    for i in range(-1, 4):
        x = i * 520 - off2 + 260
        cv.drawLine(x, road_top, x, road_top - 330, paint(hx("#2e3542"), stroke=8))
        look.bloom(cv, x + 40, road_top - 330, 12, hx("#ffd9a0"), a=0.9)
        look.beam(cv, (x + 40, road_top - 325), (x + 40, road_top + 10), 6, 150, c=hx("#ffd9a0"), a=0.10)
    # car: centred, then the camera pushes in on the hood
    base_s = 0.9
    ss = base_s * s
    focus_x = 231 + (392 - 231) * kz
    x0 = 540 - focus_x * ss * 0.97
    y0 = ROAD_Y + kz * 260
    bob = 1.5 * math.sin(t * 7)
    pj = car_proj(x0, y0 + bob, ss)
    look.soft_shadow(cv, x0 + 230 * ss, y0 + 4, 520 * ss, 40 * ss / 0.66, a=0.6)
    xray = eout(lin(t, T_THREE_H - 0.2, T_THREE_H + 0.4))
    hl, hood = draw_car(cv, pj, t, CAR_COL, xray=xray)
    look.beam(cv, hl, (hl[0] + 420 * ss / 0.66, hl[1] + 40), 8, 90, a=0.22)
    look.wet_reflection(cv, hl[0], y0 + 10, y0 + 180, 18, hx("#fff1c9"), a=0.25)
    look.vignette(cv, 0.5)
    cv.restore()
    # tags
    kt = win(t, T_THREE_H - 0.1, T_WHERE - 0.05, 0.2, 0.2) * k
    if kt > 0:
        pill(cv, 540, 620, "3 MOVING PARTS?", font("inter_xb", 34), INK, border=YEL, a=kt, align="center",
             tracking=2, dot=YEL)
    brand.stamp(cv, t, "WHERE ARE THE VALVES?", T_WHERE - 0.05, dur=T_WHAT - T_WHERE + 0.3, center=(540, 620),
                color=YEL, bg=hx("#2a2405"))


# ================================================================== WHAT (first look inside)
def draw_what(cv, t, k):
    if k <= 0:
        return
    s = 1.05 + 0.25 * eout(lin(t, T_WHAT - 0.2, T_WHAT + 1.5))
    pj = ojp(540, 860, s)
    draw_unit(cv, pj, theta(t), a=k, ch_mode="stage", ch_a=0.8, plugs=1.0, spark=spark_k(theta(t)), ports=0.8,
              seals=1.0)
    sk = win(t, T_13B - 0.35, T_PROB + 0.3, 0.3, 0.3) * k
    if sk > 0:
        pill(cv, 540, 1290, "MAZDA 13B · 2 ROTORS · 1.3 L", font("inter_xb", 32), INK, border=RED, a=sk,
             align="center", tracking=2, dot=RED)
    ck = win(t, T_ROTARY_W - 0.2, T_PROB + 0.3, 0.3, 0.3) * k
    if ck > 0:
        draw_text(cv, "ONE ROTOR · X-RAY", 540, 1228, font("inter_xb", 28), MUTED, a=ck, align="center", tracking=4)


# ================================================================== PROBLEM (piston engine vs rotary)
def draw_piston_card(cv, t, x0, y0, w, h, a):
    brand.panel(cv, x0, y0, w, h, "PISTON ENGINE", CYAN, a=a)
    cx = x0 + w / 2
    cang = t * TAU * 1.2
    crank_y = y0 + 570
    rr = 46
    pin = (cx + rr * math.sin(cang), crank_y - rr * math.cos(cang))
    rod = 150
    py = pin[1] - math.sqrt(max(1.0, rod ** 2 - (pin[0] - cx) ** 2))
    # cylinder walls
    top = y0 + 250
    cv.drawRect(skia.Rect.MakeLTRB(cx - 78, top, cx - 66, crank_y - 90), paint(STEEL_D, a=a))
    cv.drawRect(skia.Rect.MakeLTRB(cx + 66, top, cx + 78, crank_y - 90), paint(STEEL_D, a=a))
    cv.drawRect(skia.Rect.MakeLTRB(cx - 78, top - 12, cx + 78, top), paint(STEEL_D, a=a))
    # valves (4-stroke: each opens once per two crank turns), cam-driven
    cyc = (cang / TAU) % 2.0
    v_in = max(0.0, math.sin(math.pi * clamp((cyc - 0.0) / 0.5))) if cyc < 0.5 else 0.0
    v_ex = max(0.0, math.sin(math.pi * clamp((cyc - 1.5) / 0.5))) if cyc >= 1.5 else 0.0
    for vx, lift, c in ((cx - 32, v_in, AMBER), (cx + 32, v_ex, MUTED)):
        vy = top + 4 + 22 * lift
        cv.drawLine(vx, top - 90, vx, vy, paint(STEEL, a=a, stroke=6))
        cv.drawLine(vx - 20, vy, vx + 20, vy, paint(c, a=a, stroke=8, cap=skia.Paint.kRound_Cap))
        # cam lobe
        ca = cang / 2 + (0 if c is AMBER else math.pi)
        cv.drawCircle(vx, top - 112, 18, paint(STEEL_D, a=a))
        cv.drawCircle(vx + 14 * math.cos(ca), top - 112 + 14 * math.sin(ca), 9, paint(CYAN, a=a))
    # piston
    cv.drawRoundRect(skia.Rect.MakeLTRB(cx - 62, py - 34, cx + 62, py + 34), 6, 6, paint(STEEL, a=a))
    cv.drawLine(cx, py, *pin, paint(hx("#aeb7c4"), a=a, stroke=12, cap=skia.Paint.kRound_Cap))
    cv.drawCircle(cx, crank_y, rr + 18, paint(hx("#3a4456"), a=a))
    cv.drawCircle(*pin, 12, paint(CYAN, a=a))
    # arrows: up & down
    ak = win(t, T_UPDOWN - 0.1, T_PARTS, 0.2, 0.3) * a
    if ak > 0:
        for d in (-1, 1):
            yy = (top + crank_y) / 2 - 30 + d * 60
            cv.drawLine(cx + 120, yy, cx + 120, yy + d * 40, paint(YEL, a=ak, stroke=5))
            cv.drawLine(cx + 108, yy + d * 28, cx + 120, yy + d * 42, paint(YEL, a=ak, stroke=5))
            cv.drawLine(cx + 132, yy + d * 28, cx + 120, yy + d * 42, paint(YEL, a=ak, stroke=5))
    bl = [("PISTONS", T_PISTONS), ("CAMSHAFTS", T_CAMS), ("VALVES", T_VALVES_P)]
    for i, (s_, tt) in enumerate(bl):
        ba = eout(lin(t, tt - 0.1, tt + 0.25)) * a
        brand.bullet(cv, x0 + 40, y0 + h - 170 + 52 * i, s_, False, a=ba, size=30)


def draw_problem(cv, t, k):
    if k <= 0:
        return
    w, h = 420, 820
    xa, xb, y0 = 70, 590, 470
    ka = k * eout(lin(t, T_PROB - 0.1, T_PROB + 0.4))
    draw_piston_card(cv, t, xa, y0 + (1 - ka) * 60, w, h, ka)
    kb = k * eout(lin(t, T_SPINS - 0.6, T_SPINS - 0.1))
    if kb > 0:
        brand.panel(cv, xb, y0 + (1 - kb) * 60, w, h, "ROTARY", RED, a=kb)
        pj = ojp(xb + w / 2, y0 + 360, 0.78)
        draw_unit(cv, pj, theta(t), a=kb, ch_mode="stage", ch_a=0.7)
        brand.bullet(cv, xb + 40, y0 + h - 170, "JUST SPINS", True, a=kb * eout(lin(t, T_SPINS - 0.1, T_SPINS + 0.3)),
                     size=30)
        brand.bullet(cv, xb + 40, y0 + h - 118, "NO VALVETRAIN", True,
                     a=kb * eout(lin(t, T_SPINS + 0.2, T_SPINS + 0.6)), size=30)


# ================================================================== PARTS (housing, rotor, two rotors on one shaft)
def parts_view(t):
    """Interpolate from a near face-on single unit to a 3/4 view of two units on one shaft."""
    k = ease(lin(t, T_TWO - 0.3, T_TWO + 0.7))
    cx = 540 + (-110) * k
    cy = 840 + 80 * k
    s = 1.15 + (0.82 - 1.15) * k
    dx = 0.26 + (0.95 - 0.26) * k
    dy = -0.2 + (-0.62 + 0.2) * k
    return ojp(cx, cy, s, dx, dy), k


def draw_parts(cv, t, k):
    if k <= 0:
        return
    pj, kv = parts_view(t)
    th = theta(t)
    ha = eout(lin(t, T_PARTS - 0.1, T_HOUSING - 0.1))
    ra = eout(lin(t, T_ROTOR_P - 0.55, T_ROTOR_P - 0.1))
    drop = -260 * (1 - eback(lin(t, T_ROTOR_P - 0.55, T_ROTOR_P + 0.05)))
    hl1 = win(t, T_ALL - 0.1, T_GEARS, 0.15, 0.3)
    hl2 = win(t, T_THREE_P - 0.1, T_GEARS, 0.15, 0.3)
    hl3 = win(t, T_MOVING - 0.1, T_GEARS, 0.15, 0.3)
    # far unit (rotor 2, eccentric lobe 180 deg away)
    z2 = 230.0
    a2 = eout(lin(t, T_TWO - 0.1, T_TWO + 0.5))
    if a2 > 0:
        draw_unit(cv, pj, th + math.pi, a=k * a2, z0=z2, housing_a=0.55, glow_rotor=hl2, seals=0.6)
    # shaft through both
    sa = eout(lin(t, T_ECC - 0.3, T_ECC + 0.2))
    if sa > 0:
        cyl3(cv, pj, (0, 0, -140), (0, 0, z2 + DEPTH + 120), 24, mix(hx("#6b7688"), RED, hl3), alpha=k * sa,
             edge=hx("#20262f"))
        for zc, ang in ((DEPTH / 2, th), (z2 + DEPTH / 2, th + math.pi)):
            c = (E_ * math.cos(ang), E_ * math.sin(ang))
            cyl3(cv, pj, (c[0], c[1], zc - 30), (c[0], c[1], zc + 30), 64, mix(hx("#3a4456"), RED, hl3),
                 alpha=k * sa * 0.85, edge=hx("#20262f"))
    draw_unit(cv, pj, th, a=k, rotor_a=ra, rotor_dy=drop, housing_a=ha, glow_rotor=hl1, seals=0.6 * ra)
    if sa > 0:
        cyl3(cv, pj, (0, 0, -140), (0, 0, -2), 24, mix(hx("#6b7688"), RED, hl3), alpha=k * sa, edge=hx("#20262f"))
    # labels
    if kv < 0.05:
        hp = pj(-R_ - E_, 0, 0)
        brand.label(cv, t, "HOUSING", tuple(hp), (90, 520), CYAN, T_HOUSING - 0.4, T_TWO - 0.3)
        rp = pj(0, -60, 8)
        brand.label(cv, t, "ROTOR", (rp[0], rp[1] + drop), (720, 520), RED, T_ROTOR_P - 0.1, T_TWO - 0.3)
    if t > T_TWO:
        ra1 = pj(-120, 90, 8)
        rb1 = pj(-120 + 0, 90, z2 + 8)
        brand.label(cv, t, "ROTOR 1", tuple(ra1), (80, 1290), RED, T_TWO + 0.2, T_GEARS + 0.2)
        brand.label(cv, t, "ROTOR 2", tuple(rb1), (690, 470), RED, T_TWO + 0.4, T_GEARS + 0.2)
        sp = pj(0, 0, -120)
        brand.label(cv, t, "ECCENTRIC SHAFT", tuple(sp), (100, 1180), AMBER, T_ECC - 0.1, T_GEARS + 0.2)
    # 1-2-3 count
    for i, (tt, nm) in enumerate(((T_ALL, "ROTOR"), (T_THREE_P, "ROTOR"), (T_MOVING, "SHAFT"))):
        kk = eback(lin(t, tt - 0.1, tt + 0.25)) * win(t, tt - 0.1, T_GEARS + 0.1, 0.1, 0.3)
        if kk > 0:
            x = 330 + i * 210
            pill(cv, x, 1370, f"{i + 1} · {nm}", font("inter_blk", 30), INK, border=RED if i < 2 else AMBER,
                 a=clamp(kk), align="center", tracking=2)


# ================================================================== FACE-ON (gears, gaps, cycle, ports)
def face_cam(t):
    """Camera for the face-on x-ray. Pulls down/in for the ports in the key beat."""
    kp = ease(lin(t, T_KEY - 0.2, T_KEY + 0.6))
    ko = ease(lin(t, T_CH - 0.2, T_CH + 0.4)) * (1 - kp)
    cx = 540
    cy = 760 + (700 - 760) * kp
    s = 1.2 + (1.45 - 1.2) * kp - 0.15 * ko
    return ojp(cx, cy, s, 0.2, -0.15)


def graph_xy(ps, v):
    gx, gy, gw, gh = 170, 1150, 740, 170
    return gx + gw * ps / (6 * math.pi), gy + gh - gh * (v - V_MIN) / (V_MAX - V_MIN)


def draw_volume_graph(cv, t, a):
    if a <= 0:
        return
    gx, gy, gw, gh = 170, 1150, 740, 170
    cv.saveLayerAlpha(None, int(255 * a))
    brand.graph_box(cv, (gx, gy, gw, gh), "CHAMBER VOLUME · ONE ROTOR TURN")
    for i, (nm, c) in enumerate(STAGES):
        x0 = gx + gw * i / 4
        cv.drawRect(skia.Rect.MakeXYWH(x0 + 2, gy, gw / 4 - 4, gh), paint(c, a=0.06))
        draw_text(cv, nm, x0 + gw / 8, gy + gh + 30, font("inter_xb", 17), c, align="center", tracking=1.5)
    ps_line = np.linspace(0, 6 * math.pi, 200)
    pts = np.array([graph_xy(p, vol(math.pi / 2 + p, 0)) for p in ps_line])
    brand.curve(cv, pts, CYAN, a=0.9)
    th = theta(t)
    ps = psi(th, TRACK)
    x, y = graph_xy(ps, vol(th, TRACK))
    brand.dot(cv, x, y, chamber_color(th, TRACK, "stage"))
    cv.restore()


def draw_face(cv, t, k):
    if k <= 0:
        return
    pj = face_cam(t)
    th = theta(t)
    kg = win(t, T_GEARS - 0.2, T_REHOOK + 0.2, 0.3, 0.4)
    gears = 0.35 + 0.65 * kg
    ring_hl = win(t, T_GEAR_IN - 0.1, T_REHOOK, 0.2, 0.4)
    fix_hl = win(t, T_FIXED - 0.1, T_REHOOK, 0.2, 0.4)
    shaft_hl = win(t, T_SPINS_G - 0.1, T_REHOOK, 0.2, 0.4)
    kgap = win(t, T_REHOOK + 0.3, T_CH + 0.2, 0.3, 0.3)
    kcyc = win(t, T_CH - 0.1, T_CATCH + 0.4, 0.3, 0.3)
    ch_mode = "gaps" if kgap > 0.5 else "stage"
    ch_a = max(kgap, kcyc)
    ch_only = TRACK if (T_CHAMBER - 0.2 < t < T_EVERY_C - 0.3) else None
    ports = win(t, T_KEY - 0.3, T_CATCH + 0.4, 0.3, 0.3)
    plugs = win(t, T_CH - 0.1, T_KEY + 0.1, 0.3, 0.3)
    draw_unit(cv, pj, th, a=k, gears=gears, ring_hl=ring_hl, fix_hl=fix_hl, shaft_hl=shaft_hl, ch_mode=ch_mode,
              ch_a=ch_a, ch_only=ch_only, ports=0.25 + 0.75 * ports, plugs=plugs, spark=spark_k(th) * plugs,
              seals=1.0)
    # --- gears beat
    if kg > 0:
        c = rcenter(th)
        ga = pj(c[0] + 3 * E_ * math.cos(-2.2), c[1] + 3 * E_ * math.sin(-2.2), 7)
        brand.label(cv, t, "GEAR IN THE ROTOR", tuple(ga), (80, 470), AMBER, T_GEAR_IN - 0.1, T_REHOOK)
        fa = pj(2 * E_ * math.cos(0.6), 2 * E_ * math.sin(0.6), 5)
        brand.label(cv, t, "FIXED GEAR", tuple(fa), (690, 1170), CYAN, T_FIXED - 0.1, T_REHOOK)
        cnt_k = win(t, T_SPINS_G - 0.3, T_REHOOK + 0.1, 0.25, 0.3)
        if cnt_k > 0:
            th0 = theta(T_SPINS_G - 0.05)
            turns = clamp((th - th0) / TAU, 0, 3)
            rturn = turns / 3
            for i, (nm, v, c_, x) in enumerate((("SHAFT", turns, RED, 300), ("ROTOR", rturn, YEL, 780))):
                draw_text(cv, f"{v:.1f}" if nm == "ROTOR" else f"{v:.1f}", x, 1330, font("inter_blk", 76), INK,
                          a=cnt_k, align="center")
                draw_text(cv, nm + " TURNS", x, 1370, font("inter_sb", 24), c_, a=cnt_k, align="center",
                          tracking=3)
            k31 = cnt_k * eout(lin(t, T_ROTOR_G - 0.2, T_ROTOR_G + 0.2))
            if k31 > 0.01:
                draw_text(cv, "3 : 1", 540, 1325, font("inter_blk", 56), RED, a=k31, align="center")
    # --- gaps
    if kgap > 0:
        for kk in range(3):
            cp = chamber_prof(th, kk, 30)
            cen = cp[:30].mean(0) * 0.55 + cp[30:].mean(0) * 0.45
            q = pj(cen[0], cen[1], 8)
            kk_ = eback(lin(t, T_GAPS - 0.3 + 0.15 * kk, T_GAPS + 0.05 + 0.15 * kk)) * kgap
            if kk_ > 0:
                draw_text(cv, str(kk + 1), q[0], q[1] + 22, font("inter_blk", 64), chamber_color(th, kk, "gaps"),
                          a=clamp(kk_), align="center", glow=10)
        brand.stamp(cv, t, "3 GAPS?", T_FOR - 0.1, dur=1.3, center=(540, 1290), color=YEL, bg=hx("#2a2405"))
    # --- cycle
    if kcyc > 0 and t < T_KEY + 0.2:
        st = stage(th, TRACK)
        nm, c = STAGES[st]
        ka = win(t, T_CHAMBER - 0.1, T_KEY + 0.2, 0.25, 0.3)
        if ka > 0:
            ka2 = ka * (1 - eout(lin(t, T_THREE_C - 0.3, T_THREE_C - 0.05)))
            if ka2 > 0:
                pill(cv, 540, 1050, f"CHAMBER: {nm}", font("inter_xb", 34), INK, border=c, a=ka2, align="center",
                     tracking=2, dot=c)
        draw_volume_graph(cv, t, win(t, T_CHAMBER - 0.2, T_KEY + 0.1, 0.3, 0.3))
        pk = win(t, T_THREE_C - 0.15, T_KEY + 0.1, 0.2, 0.3)
        if pk > 0:
            pill(cv, 540, 1050, "3 POWER STROKES PER ROTOR TURN", font("inter_xb", 28), INK, border=RED, a=pk,
                 align="center", tracking=2, dot=RED)
    # --- ports
    if ports > 0.05:
        for nm, poly_c, lpos, c, al in (("in", PORT_IN_C, (80, 1150), AMBER, "left"),
                                        ("ex", PORT_EX_C, (1000 - 80, 1150), MUTED, "right")):
            q = pj(poly_c[0], poly_c[1], DEPTH)
            title = "INTAKE PORT" if nm == "in" else "EXHAUST PORT"
            brand.label(cv, t, title, tuple(q), (lpos[0] if al == "left" else 600, lpos[1]), c,
                        T_PORTS - 0.1, T_CATCH + 0.2)
            frac, kk = port_open(th, nm)
            ka = win(t, T_UNCOV - 0.2, T_CATCH + 0.2, 0.2, 0.3)
            if ka > 0:
                txt = "OPEN" if frac > 0.35 else "COVERED"
                cc = GREEN if frac > 0.35 else RED
                x = 250 if nm == "in" else 830
                pill(cv, x, 1290, f"{'IN' if nm == 'in' else 'EX'}: {txt}", font("inter_xb", 28), INK, border=cc,
                     a=ka, align="center", tracking=2, dot=cc)
            # flow puffs while open
            if frac > 0.35 and kk is not None:
                for j in range(5):
                    ph_ = (t * 1.6 + j / 5) % 1.0
                    rr_ = 10 + 40 * ph_
                    cc_ = poly_c * (1 - 0.25 * ph_ if nm == "in" else 1)
                    q2 = pj(cc_[0], cc_[1], DEPTH * (1 - ph_) if nm == "in" else DEPTH * ph_)
                    cv.drawCircle(*q2, rr_ * pj.s * 0.4, paint(c, a=0.5 * (1 - ph_) * ports * frac))
        brand.stamp(cv, t, "NO VALVES", T_VALVES_K - 0.05, dur=T_ITSELF - T_VALVES_K + 0.1, center=(540, 1040),
                    color=YEL, bg=hx("#2a2405"))
        brand.stamp(cv, t, "IT'S THE ROTOR", T_ITSELF - 0.35, dur=1.6, center=(540, 1040))


# ================================================================== SEAL (apex seal close-up)
def seal_cam(t, th):
    ap = apexes(th)[0]
    s = 3.1
    return ojp(540 - s * ap[0], 840 - s * ap[1], s, 0.12, -0.09)


def draw_seal(cv, t, k):
    if k <= 0:
        return
    th = theta(t)
    pj = seal_cam(t, th)
    wear = eout(lin(t, T_WEAR - 0.2, T_WEAR + 0.6))
    LC, LR = (540, 840), 380
    cv.drawCircle(*LC, LR, paint(hx("#070b13"), a=0.95 * k))
    cv.save()
    clip = skia.Path()
    clip.addCircle(*LC, LR)
    cv.clipPath(clip, skia.ClipOp.kIntersect, True)
    draw_unit(cv, pj, th, a=k, ch_mode="stage", ch_a=0.75, seals=1.0, seal_wear=wear, ports=0.3)
    # leak: gas squeezing past the worn tip, from the chamber ahead into the one behind
    if wear > 0.05:
        ap = apexes(th)[0]
        c = rcenter(th)
        d = (ap - c) / np.linalg.norm(ap - c)
        tg = np.array([-d[1], d[0]])
        for j in range(14):
            ph_ = (t * 1.9 + j / 14) % 1.0
            off = (j % 3 - 1) * 2.0
            p = ap - d * (3 + off) + tg * (40 - 80 * ph_)
            q = pj(p[0], p[1], 8 + (j * 37 % 64))
            cv.drawCircle(*q, 8 + 5 * (1 - ph_), paint(AMBER, a=0.85 * wear * k * math.sin(math.pi * ph_)))
    cv.restore()
    cv.drawCircle(*LC, LR, paint(CYAN, a=0.35 * k, stroke=8, blur=6))
    cv.drawCircle(*LC, LR, paint(CYAN, a=0.9 * k, stroke=3))
    ap = apexes(th)[0]
    q = pj(ap[0], ap[1], 8)
    brand.label(cv, t, "APEX SEAL", tuple(q), (90, 520), RED, T_APEX - 0.1, T_OUTRO)
    sk = win(t, T_APEX - 0.2, T_WEAR - 0.1, 0.2, 0.2)
    if sk > 0:
        pill(cv, 540, 1290, "SEALED", font("inter_xb", 32), INK, border=GREEN, a=sk * k, align="center", tracking=3,
             dot=GREEN)
    lk = win(t, T_WEAR - 0.1, T_OUTRO + 0.2, 0.2, 0.3)
    if lk > 0:
        pill(cv, 540, 1290, "WORN · COMPRESSION LEAKING", font("inter_xb", 32), INK, border=RED, a=lk * k,
             align="center", tracking=2, dot=RED)
    brand.stamp(cv, t, "THE CATCH", T_CATCH - 0.05, dur=1.2, center=(540, 1290))


# ================================================================== OUTRO
def draw_outro(cv, t, k):
    if k <= 0:
        return
    ke = 1 - current.ending_k(t)
    pj = ojp(540, 820, 1.1)
    th = theta(t)
    draw_unit(cv, pj, th, a=k * ke, ch_mode="stage", ch_a=0.8, ports=1.0, plugs=1.0, spark=spark_k(th), seals=1.0,
              glow_rotor=win(t, F("outro", "the") - 0.1, T_END + 0.4, 0.2, 0.2))
    for i, (txt, tt) in enumerate((("NO CAMS", T_NOCAMS), ("NO SPRINGS", T_NOSPR), ("NO VALVES", T_NOVAL))):
        kk = eback(lin(t, tt - 0.25, tt + 0.1)) * ke * k
        if kk > 0:
            x = 200 + 340 * i
            pill(cv, x, 1300, txt, font("inter_xb", 30), INK, border=RED, a=clamp(kk), align="center", tracking=2)
            cross_icon(cv, x, 1240, 34, RED, a=clamp(kk))


# ================================================================== header
def draw_header(cv, t):
    k = win(t, T_WHAT + 0.2, T_END, 0.3, 0.3)
    if k <= 0:
        return
    sec = [(T_WHAT, "MAZDA 13B", RED), (T_PROB, "PISTONS VS ROTOR", CYAN), (T_PARTS, "THE PARTS", CYAN),
           (T_GEARS, "THE GEARS", AMBER), (T_REHOOK, "THREE GAPS", YEL), (T_CH, "THE CYCLE", AMBER),
           (T_KEY, "THE VALVES", RED), (T_CATCH, "APEX SEALS", RED), (T_OUTRO, "THE ROTARY", RED)]
    txt, c = "ROTARY", RED
    for ts, s, cc in sec:
        if t >= ts - 0.1:
            txt, c = s, cc
    brand.status_pill(cv, k, txt, c)
    brand.note(cv, "ILLUSTRATION · ANIMATION SLOWED", 0.9 * k, dy=-40)


# ================================================================== draw
def draw(cv, t):
    draw_road(cv, t, scene_k(t, S_ROAD, 0.0, 0.35))
    draw_what(cv, t, scene_k(t, S_UNIT))
    draw_problem(cv, t, scene_k(t, S_PROB))
    draw_parts(cv, t, scene_k(t, S_PARTS))
    draw_face(cv, t, scene_k(t, S_FACE))
    draw_seal(cv, t, scene_k(t, S_SEAL))
    draw_outro(cv, t, scene_k(t, S_OUT))
    draw_header(cv, t)


# ================================================================== sound (synthesized here; ElevenLabs paused)
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


def _rotary(dur, rpm0, rpm1):
    """Twin-rotor exhaust note: 2 sharp pulses per shaft turn (one per rotor), slightly uneven."""
    rng = np.random.default_rng(13)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    rpm = rpm0 + (rpm1 - rpm0) * (tt / dur) ** 1.5
    f = 2 * rpm / 60.0
    ph = np.cumsum(f) / SR
    frac = ph % 1.0
    idx = np.floor(ph).astype(int)
    amp = 0.8 + 0.2 * (idx % 2) + 0.15 * rng.standard_normal(idx.max() + 2)[idx]
    pulse = np.exp(-frac / 0.18) * amp
    noise = rng.standard_normal(n)
    body = _lp(noise * pulse, 900) * 1.6 + _lp(noise * pulse ** 2, 3200) * 0.6
    body += 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * pulse
    env = np.minimum(1, tt / 0.15) * np.minimum(1, (dur - tt) / 0.4)
    return _norm(np.tanh(1.5 * body) * env, 0.8)


def _spark(dur=0.18):
    rng = np.random.default_rng(9)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-tt / 0.012)
    x = x - _lp(x, 2500)
    return _norm(x, 0.8)


def _make_sfx():
    import soundfile as sf
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, x in {"rotary_idle": _rotary(4.6, 1500, 2600), "rotary_rev": _rotary(2.2, 2500, 8000),
                    "spark_snap": _spark()}.items():
        sf.write(os.path.join(SFX_DIR, f"{name}.wav"), x, SR)


BEAT_ANCHOR = T_ITSELF
MUSIC_START = T_WHAT


def sound():
    _make_sfx()
    sfx = [(0.0, "rotary_idle", 0.4), (T_THREE_H - 0.1, "tick", 0.3), (T_WHERE - 0.05, "impact", 0.4),
           (T_HOOK_OUT - 0.1, "whoosh_big", 0.45), (T_13B - 0.4, "rotary_rev", 0.3),
           (T_PROB - 0.2, "whoosh_down", 0.3), (T_PISTONS, "clunk", 0.3), (T_SPINS - 0.1, "whoosh_up", 0.3),
           (T_HOUSING - 0.2, "clunk", 0.35), (T_ROTOR_P - 0.1, "clunk", 0.45), (T_TWO - 0.2, "whoosh_big", 0.3),
           (T_ALL, "tick", 0.35), (T_THREE_P, "tick", 0.35), (T_MOVING, "tick", 0.35),
           (T_GEARS - 0.2, "whoosh_down", 0.3), (T_ROTOR_G, "clunk", 0.35), (T_FOR - 0.1, "impact", 0.35),
           (T_CHAMBER, "whoosh_up", 0.25), (T_VALVES_K - 0.05, "impact", 0.35), (T_ITSELF - 0.35, "impact", 0.5),
           (T_UNCOV, "hiss", 0.25), (T_COVER, "clunk", 0.3), (T_CATCH - 0.05, "whoosh_big", 0.3),
           (T_WEAR, "hiss", 0.35), (T_NOCAMS, "tick", 0.35), (T_NOSPR, "tick", 0.35), (T_NOVAL, "tick", 0.35)]
    # spark snaps at each top-dead-centre firing during the cycle beat
    ts = np.arange(T_CH, T_KEY, 1 / 60)
    prev = 0.0
    for tt in ts:
        sk = spark_k(theta(tt))
        if sk > 0.9 and prev <= 0.9:
            sfx.append((float(tt), "spark_snap", 0.35))
        prev = sk
    return {"build": (T_CH, T_ITSELF), "drop": (T_ITSELF, T_OUTRO - 0.05), "sfx": sfx, "music_gain": 0.8}
