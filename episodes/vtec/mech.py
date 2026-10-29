"""VTEC valvetrain geometry and kinematics (profile-plane coords, px, Y down).

Cam centre at (0,0). Rocker pivots on a shaft at P; a flat pad under the cam;
the tip pushes the valve stem. The cam rotates clockwise on screen.
"""
import numpy as np

R0 = 70.0                     # base-circle radius
MILD = dict(A=27.0, w=np.radians(64))
TALL = dict(A=41.0, w=np.radians(78))

P = np.array([-250.0, 96.0])  # rocker pivot
PAD = np.array([0.0, R0])     # pad contact point at rest
TIP = np.array([225.0, 136.0])  # adjuster-screw tip (valve stem top at rest)
PIN_BORE = np.array([-128.0, 98.0])
PIN_R = 13.0

# depth layout (along the camshaft)
ZC = [0.0, 140.0, 280.0]      # front outer, middle, back outer
LOBE_W = 96.0
ROCK_W = 120.0
# synchronising pins (rest positions along z) and travel
PIN_TRAVEL = 60.0
PINS_REST = [(-32.5, 62.5), (77.5, 202.5), (217.5, 250.0)]
PIN_WALL_BACK = ZC[2] + ROCK_W / 2 - 7.0   # spring seat inside back rocker
PIN_WALL_FRONT = ZC[0] - ROCK_W / 2 + 6.0  # oil chamber front wall


def _hull(pts):
    pts = sorted(map(tuple, pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


def lobe_profile(A, w, n=900):
    phi = np.linspace(-np.pi, np.pi, n, endpoint=False)
    x = np.clip(phi / w, -1, 1)
    f = np.where(np.abs(phi) < w, 0.5 * (1 + np.cos(np.pi * x)), 0.0)
    r = R0 + A * f
    pts = np.stack([r * np.cos(phi), r * np.sin(phi)], 1)
    h = _hull(pts)
    # resample hull evenly by arc length for smooth shading
    seg = np.linalg.norm(np.roll(h, -1, 0) - h, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    hh = np.vstack([h, h[:1]])
    ts = np.linspace(0, s[-1], 220, endpoint=False)
    xs = np.interp(ts, s, hh[:, 0])
    ys = np.interp(ts, s, hh[:, 1])
    return np.stack([xs, ys], 1)


PROF_MILD = lobe_profile(**MILD)
PROF_TALL = lobe_profile(**TALL)
DENSE_MILD = _hull(np.stack([(R0 + MILD['A'] * np.where(np.abs(p) < MILD['w'], 0.5 * (1 + np.cos(np.pi * np.clip(p / MILD['w'], -1, 1))), 0)) * np.array([np.cos(p), np.sin(p)]) for p in np.linspace(-np.pi, np.pi, 2000, endpoint=False)]))
DENSE_TALL = _hull(np.stack([(R0 + TALL['A'] * np.where(np.abs(p) < TALL['w'], 0.5 * (1 + np.cos(np.pi * np.clip(p / TALL['w'], -1, 1))), 0)) * np.array([np.cos(p), np.sin(p)]) for p in np.linspace(-np.pi, np.pi, 2000, endpoint=False)]))


def rot(pts, a, c=(0.0, 0.0)):
    c = np.asarray(c)
    ca, sa = np.cos(a), np.sin(a)
    d = np.asarray(pts) - c
    return np.stack([d[..., 0] * ca - d[..., 1] * sa, d[..., 0] * sa + d[..., 1] * ca], -1) + c


def _alpha_for(cam_pts):
    """Rocker angle so the flat pad is tangent to (below) the cam points."""
    def g(a):
        n = rot(np.array([0.0, -1.0]), a)
        q = rot(PAD, a, P)
        return np.min((cam_pts - q) @ n)
    if g(0.0) >= 0:
        return 0.0
    lo, hi = 0.0, 0.6
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if g(m) < 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


_TH = np.linspace(0, 2 * np.pi, 1441)
_AM = np.array([_alpha_for(rot(DENSE_MILD, t)) for t in _TH])
_AT = np.array([_alpha_for(rot(DENSE_TALL, t)) for t in _TH])


def alpha_mild(theta):
    return np.interp(np.mod(theta, 2 * np.pi), _TH, _AM)


def alpha_tall(theta):
    return np.interp(np.mod(theta, 2 * np.pi), _TH, _AT)


def tip_drop(alpha):
    d = TIP - P
    alpha = np.asarray(alpha)
    return P[1] + d[0] * np.sin(alpha) + d[1] * np.cos(alpha) - TIP[1]


def valve_lift_curve(which, n=361):
    th = np.linspace(0, 2 * np.pi, n)
    a = alpha_mild(th) if which == "mild" else alpha_tall(th)
    return th, tip_drop(a)


# angle at which the nose points straight down (max lift)
THETA_PEAK = np.pi / 2
MAX_LIFT_MILD = tip_drop(alpha_mild(THETA_PEAK))
MAX_LIFT_TALL = tip_drop(alpha_tall(THETA_PEAK))

if __name__ == "__main__":
    print("max valve lift mild/tall px:", round(MAX_LIFT_MILD, 1), round(MAX_LIFT_TALL, 1))
    th, lm = valve_lift_curve("mild", 3601)
    _, lt = valve_lift_curve("tall", 3601)
    print("tall >= mild everywhere:", bool(np.all(lt >= lm - 1e-6)))
    dm = np.degrees(th[lm > 0.5]); dt = np.degrees(th[lt > 0.5])
    print("cam deg open mild:", round(dm.min()), round(dm.max()), " tall:", round(dt.min()), round(dt.max()))
    print("pad alpha max (deg):", round(np.degrees(_AM.max()), 2), round(np.degrees(_AT.max()), 2))
