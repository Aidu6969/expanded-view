"""Expanded View drawing toolkit: colours, easing, 3D projection, extrusions, springs, text, labels."""
import math
import numpy as np
import skia

W, H = 1080, 1920
# Brand fonts ship with the repo (ev/fonts, SIL OFL) so every run renders identically.
FONT_DIR = __import__("os").path.join(__import__("os").path.dirname(__file__), "fonts")
_FONT_FILES = {
    "pop_b": "Poppins-Bold.ttf",
    "inter_b": "Inter-Bold.otf",
    "inter_sb": "Inter-SemiBold.otf",
    "inter_xb": "Inter-ExtraBold.otf",
    "inter_blk": "InterDisplay-Black.otf",
    "inter_m": "Inter-Medium.otf",
}
TF = {}
for _k, _f in _FONT_FILES.items():
    TF[_k] = skia.Typeface.MakeFromFile(f"{FONT_DIR}/{_f}")
    if TF[_k] is None:
        raise FileNotFoundError(f"brand font missing: {FONT_DIR}/{_f}")
_fcache = {}


def font(name, size):
    k = (name, round(size, 2))
    if k not in _fcache:
        f = skia.Font(TF[name], size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _fcache[k] = f
    return _fcache[k]


# ---------------------------------------------------------------- colours
def hx(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def col(c, a=None):
    r, g, b, aa = c if len(c) == 4 else (*c, 1.0)
    if a is not None:
        aa = aa * a
    return skia.Color(int(round(r)), int(round(g)), int(round(b)), int(round(255 * max(0, min(1, aa)))))


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    a = c1 if len(c1) == 4 else (*c1, 1.0)
    b = c2 if len(c2) == 4 else (*c2, 1.0)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def shade(c, k):
    return (min(255, c[0] * k), min(255, c[1] * k), min(255, c[2] * k), c[3] if len(c) == 4 else 1.0)


BG0 = hx("#06080d")
BG1 = hx("#0d1422")
INK = hx("#f4f6fb")
MUTED = hx("#8d97ab")
CYAN = hx("#38d3ff")
RED = hx("#ff3b3b")
AMBER = hx("#ffb020")
YEL = hx("#ffd43b")
STEEL = hx("#8f9aab")
STEEL_D = hx("#4b5566")
GREEN = hx("#3ee08f")


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lin(t, t0, t1):
    if t1 == t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease(x):  # cubic in-out
    x = clamp(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eback(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def win(t, t0, t1, fin=0.25, fout=0.25):
    """1 inside [t0,t1] with eased fades."""
    return eout(lin(t, t0, t0 + fin)) * (1 - ease(lin(t, t1 - fout, t1)))


def smooth(t, keys):
    """Piecewise eased interpolation through (time, value) keys."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease(lin(t, t0, t1))
    return keys[-1][1]


def _hull(pts):
    """Convex hull (monotone chain) of 2D points -> (N,2) array."""
    pts = sorted(map(tuple, np.asarray(pts, float)))
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


hull = _hull


def zhelix(pj, x, y, r, z0, z1, turns, n=160):
    """Helix along the depth (z) axis, e.g. a spring inside a bore. Returns projected points."""
    u = np.linspace(0, 2 * np.pi * turns, n)
    z = z0 + (z1 - z0) * u / u[-1]
    return pj(x + r * np.cos(u), y + r * np.sin(u), z)


# ---------------------------------------------------------------- paints
def paint(c, a=None, stroke=None, cap=None, join=None, blur=None):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(join or skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def poly_path(pts, close=True):
    path = skia.Path()
    pts = np.asarray(pts)
    path.moveTo(float(pts[0][0]), float(pts[0][1]))
    for x, y in pts[1:]:
        path.lineTo(float(x), float(y))
    if close:
        path.close()
    return path


def lin_grad(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear(
        [skia.Point(*p0), skia.Point(*p1)], [col(c) for c in colors], pos)


# ---------------------------------------------------------------- projection
class Proj:
    """Parallel projection of (X, Y, z): X along the rocker, Y down, z along the camshaft.

    mode "ortho": true 3/4 orthographic view from yaw/pitch (valves toward the viewer).
    mode "oblique": profile plane true shape, depth receding up-right (used for small inset cams).
    """
    YAW, PITCH = 35.0, 28.0

    def __init__(self, ox, oy, s, dx=None, dy=None, yaw=None, pitch=None):
        self.ox, self.oy, self.s = ox, oy, s
        if dx is not None:
            self.mode = "oblique"
            self.eX, self.eY, self.eZ = np.array([1.0, 0.0]), np.array([0.0, 1.0]), np.array([dx, dy])
            self.D = np.array([dx, dy])
        else:
            self.mode = "ortho"
            ps, ph = math.radians(yaw or self.YAW), math.radians(pitch or self.PITCH)
            self.yaw, self.pitch = yaw or self.YAW, pitch or self.PITCH
            self.eX = np.array([math.sin(ps), math.cos(ps) * math.sin(ph)])
            self.eY = np.array([0.0, math.cos(ph)])
            self.eZ = np.array([math.cos(ps), -math.sin(ps) * math.sin(ph)])
            # depth gradient (farther = larger)
            self.dX, self.dY, self.dZ = -math.cos(ps) * math.cos(ph), math.sin(ph), math.sin(ps) * math.cos(ph)
            self.D = self.eZ

    def shifted(self, dy=0.0, dx=0.0):
        p = Proj.__new__(Proj)
        p.__dict__.update(self.__dict__)
        p.ox, p.oy = self.ox + dx, self.oy + dy
        return p

    def __call__(self, X, Y, z=0.0):
        X = np.asarray(X, float)
        Y = np.asarray(Y, float)
        z = np.asarray(z, float)
        sx = self.ox + self.s * (X * self.eX[0] + Y * self.eY[0] + z * self.eZ[0])
        sy = self.oy + self.s * (X * self.eX[1] + Y * self.eY[1] + z * self.eZ[1])
        return np.stack(np.broadcast_arrays(sx, sy), -1)

    def pts(self, prof, z):
        prof = np.asarray(prof)
        return self(prof[:, 0], prof[:, 1], z)

    def depth(self, X, Y, z):
        if self.mode == "oblique":
            return np.asarray(z, float) + 0 * np.asarray(X, float)  # nearer = smaller z
        return np.asarray(X) * self.dX + np.asarray(Y) * self.dY + np.asarray(z) * self.dZ

    def side_vis(self, n):
        """Visibility score of side faces with profile-plane outward normals n (N,2)."""
        if self.mode == "oblique":
            Dn = self.D / np.linalg.norm(self.D)
            return n @ Dn
        return -(n[:, 0] * self.dX + n[:, 1] * self.dY)


LIGHT = np.array([-0.38, -1.0]) / np.linalg.norm([-0.38, -1.0])
LIGHT3 = np.array([-0.6, -1.0, -0.2]) / np.linalg.norm([-0.6, -1.0, -0.2])  # toward the light (X, Y, z)


def _orient_outward(pts):
    d = np.roll(pts, -1, 0) - pts
    area = np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    n = np.stack([d[:, 1], -d[:, 0]], 1) if area > 0 else np.stack([-d[:, 1], d[:, 0]], 1)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-9)


def extrude(cv, pj, prof, z0, z1, base, alpha=1.0, rim=None, rim_w=3.0, rim_glow=0.0,
            face_hi=1.18, face_lo=0.62, outline=True, side_k=(0.42, 0.75)):
    """Draw a prism: profile (N,2 profile coords) extruded from depth z0 (front) to z1 (back)."""
    prof = np.asarray(prof, float)
    F = pj.pts(prof, z0)
    B = pj.pts(prof, z1)
    n = _orient_outward(prof)
    vis = pj.side_vis(n) > 1e-4
    if pj.mode == "ortho":
        lam = np.clip(n[:, 0] * LIGHT3[0] + n[:, 1] * LIGHT3[1], 0, 1)
    else:
        lam = np.clip(n @ LIGHT, 0, 1)
    k = side_k[0] + side_k[1] * lam
    N = len(prof)
    if alpha < 1.0:
        cv.saveLayerAlpha(None, int(255 * clamp(alpha)))
    idx = np.nonzero(vis)[0]
    if len(idx):
        pos, cols = [], []
        for i in idx:
            j = (i + 1) % N
            c = col(shade(base, k[i]))
            a, b, cc, d = F[i], F[j], B[j], B[i]
            pos += [skia.Point(*a), skia.Point(*b), skia.Point(*cc), skia.Point(*a), skia.Point(*cc), skia.Point(*d)]
            cols += [c] * 6
        v = skia.Vertices(skia.Vertices.kTriangles_VertexMode, pos, None, cols)
        cv.drawVertices(v, skia.Paint(AntiAlias=True), skia.BlendMode.kDst)
        if outline:
            # back silhouette edges, antialiased
            pth = skia.Path()
            for i in idx:
                j = (i + 1) % N
                pth.moveTo(*B[i]); pth.lineTo(*B[j])
            cv.drawPath(pth, paint(shade(base, 0.35), stroke=1.6 * pj.s))
            # connecting edges where visibility flips
            pth2 = skia.Path()
            for i in range(N):
                if vis[i] != vis[i - 1]:
                    pth2.moveTo(*F[i]); pth2.lineTo(*B[i])
            cv.drawPath(pth2, paint(shade(base, 0.35), stroke=1.4 * pj.s))
    # front face
    path = poly_path(F)
    ymin, ymax = F[:, 1].min(), F[:, 1].max()
    xmin, xmax = F[:, 0].min(), F[:, 0].max()
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((xmin, ymin), (xmin + (xmax - xmin) * 0.35, ymax),
                         [shade(base, face_hi), shade(base, 0.92), shade(base, face_lo)], [0, 0.45, 1]))
    cv.drawPath(path, p)
    if outline:
        cv.drawPath(path, paint(shade(base, 0.3), stroke=1.8 * pj.s))
    if rim is not None:
        if rim_glow > 0:
            cv.drawPath(path, paint(rim, a=0.55 * rim_glow, stroke=rim_w * 3.2 * pj.s, blur=7 * pj.s))
        cv.drawPath(path, paint(rim, stroke=rim_w * pj.s))
    if alpha < 1.0:
        cv.restore()
    return F, B


def circle_prof(cx, cy, r, n=40):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1)


def hcircle(pj, x, y, z, r, n=48):
    """Horizontal circle (in X-Z plane) projected."""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return pj(x + r * np.cos(a), np.full(n, y), z + r * np.sin(a))


def vcyl(cv, pj, x, z, r, y0, y1, base, alpha=1.0, top_cap=True):
    """Vertical cylinder (axis along Y) from y0 (top) to y1 (bottom)."""
    top = hcircle(pj, x, y0, z, r)
    bot = hcircle(pj, x, y1, z, r)
    xs = np.concatenate([top[:, 0], bot[:, 0]])
    hw_l, hw_r = xs.min(), xs.max()
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * alpha))
    # body: hull of the two ellipses
    pts = np.vstack([top, bot])
    hull = _hull(pts)
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((hw_l, 0), (hw_r, 0),
                         [shade(base, 0.55), shade(base, 1.25), shade(base, 0.95), shade(base, 0.45)], [0, 0.32, 0.55, 1]))
    cv.drawPath(poly_path(hull), p)
    cv.drawPath(poly_path(hull), paint(shade(base, 0.3), stroke=1.4 * pj.s))
    if top_cap:
        cv.drawPath(poly_path(top), paint(shade(base, 1.15)))
        cv.drawPath(poly_path(top), paint(shade(base, 0.35), stroke=1.2 * pj.s))
    if alpha < 1:
        cv.restore()


def frustum(cv, pj, x, z, r0, y0, r1, y1, base, alpha=1.0, cap=True):
    top = hcircle(pj, x, y0, z, r0)
    bot = hcircle(pj, x, y1, z, r1)
    hull = _hull(np.vstack([top, bot]))
    xs = hull[:, 0]
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * alpha))
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((xs.min(), 0), (xs.max(), 0),
                         [shade(base, 0.55), shade(base, 1.25), shade(base, 0.95), shade(base, 0.45)], [0, 0.32, 0.55, 1]))
    cv.drawPath(poly_path(hull), p)
    cv.drawPath(poly_path(hull), paint(shade(base, 0.3), stroke=1.3 * pj.s))
    if cap:
        cv.drawPath(poly_path(top), paint(shade(base, 1.1)))
        cv.drawPath(poly_path(top), paint(shade(base, 0.35), stroke=1.1 * pj.s))
    if alpha < 1:
        cv.restore()


def helix(pj, x, z, r, y_top, y_bot, turns, n=200):
    u = np.linspace(0, 2 * np.pi * turns, n)
    y = y_top + (y_bot - y_top) * u / u[-1]
    X, Z = x + r * np.cos(u), z - r * np.sin(u)
    pts = pj(X, y, Z)
    dd = pj.depth(X, y, Z) - pj.depth(np.full_like(X, x), y, np.full_like(Z, z))
    front = dd < 0
    return pts, front


def draw_spring(cv, pj, x, z, r, y_top, y_bot, turns, base, width=6.0, alpha=1.0, which="both"):
    pts, front = helix(pj, x, z, r, y_top, y_bot, turns)
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * alpha))
    for want, k in (("back", 0.55), ("front", 1.15)):
        if which not in ("both", want):
            continue
        sel = front if want == "front" else ~front
        path = skia.Path()
        on = False
        for i in range(len(pts)):
            if sel[i]:
                if not on:
                    path.moveTo(*pts[i]); on = True
                else:
                    path.lineTo(*pts[i])
            else:
                on = False
        cv.drawPath(path, paint(shade(base, 0.3), stroke=(width + 2.5) * pj.s))
        cv.drawPath(path, paint(shade(base, k), stroke=width * pj.s))
    if alpha < 1:
        cv.restore()


# ---------------------------------------------------------------- text
def text_w(s, f, tracking=0.0):
    if tracking == 0:
        return f.measureText(s)
    return sum(f.measureText(ch) for ch in s) + tracking * (len(s) - 1)


def draw_text(cv, s, x, y, f, c, a=1.0, align="left", tracking=0.0, stroke=None, stroke_c=hx("#000000"),
              glow=None, glow_c=None):
    w = text_w(s, f, tracking)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    def _draw(p):
        if tracking == 0:
            cv.drawString(s, x, y, f, p)
        else:
            xx = x
            for ch in s:
                cv.drawString(ch, xx, y, f, p)
                xx += f.measureText(ch) + tracking
    if glow:
        _draw(paint(glow_c or c, a=0.8 * a, blur=glow))
    if stroke:
        _draw(paint(stroke_c, a=a, stroke=stroke))
    _draw(paint(c, a=a))
    return w


def pill(cv, x, y, s, f, fg, bg=hx("#0b111c"), border=None, a=1.0, pad=(18, 11), align="left", tracking=0.0,
         dot=None):
    """Rounded label. (x,y) = left/centre x and vertical centre."""
    w = text_w(s, f, tracking)
    dotw = 26 if dot else 0
    bw = w + 2 * pad[0] + dotw
    m = f.getMetrics()
    th = -m.fAscent * 0.74
    bh = th + 2 * pad[1]
    if align == "center":
        x0 = x - bw / 2
    elif align == "right":
        x0 = x - bw
    else:
        x0 = x
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y - bh / 2, bw, bh), bh / 2, bh / 2)
    cv.drawRRect(r, paint(bg, a=0.88 * a))
    if border:
        cv.drawRRect(r, paint(border, a=a, stroke=2.4))
    if dot:
        cv.drawCircle(x0 + pad[0] + 8, y, 8, paint(dot, a=a))
        cv.drawCircle(x0 + pad[0] + 8, y, 14, paint(dot, a=0.5 * a, blur=6))
    draw_text(cv, s, x0 + pad[0] + dotw, y + th / 2, f, fg, a=a, tracking=tracking)
    return x0, bw, bh


def leader(cv, x0, y0, x1, y1, c, a=1.0, prog=1.0):
    """Line from anchor (x0,y0) to label point (x1,y1) with a dot at the anchor."""
    prog = clamp(prog)
    if prog <= 0:
        return
    xe, ye = x0 + (x1 - x0) * prog, y0 + (y1 - y0) * prog
    cv.drawLine(x0, y0, xe, ye, paint(c, a=a, stroke=3))
    cv.drawCircle(x0, y0, 7, paint(c, a=a))
    cv.drawCircle(x0, y0, 14, paint(c, a=0.35 * a, blur=5))


def check_icon(cv, x, y, s, c, a=1.0, prog=1.0):
    path = skia.Path()
    pts = [(x - 0.45 * s, y + 0.0 * s), (x - 0.12 * s, y + 0.32 * s), (x + 0.5 * s, y - 0.36 * s)]
    path.moveTo(*pts[0]); path.lineTo(*pts[1]); path.lineTo(*pts[2])
    cv.drawPath(path, paint(c, a=a, stroke=0.2 * s))


def cross_icon(cv, x, y, s, c, a=1.0):
    p = paint(c, a=a, stroke=0.2 * s)
    cv.drawLine(x - 0.35 * s, y - 0.35 * s, x + 0.35 * s, y + 0.35 * s, p)
    cv.drawLine(x - 0.35 * s, y + 0.35 * s, x + 0.35 * s, y - 0.35 * s, p)
