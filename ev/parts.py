"""Reusable mechanical parts and flows for Expanded View scenes (same look as ev.gfx).

  rev(...)          surface of revolution about an axis parallel to X, Y or z (shafts, hubs, housings, pulleys)
  ring_front(...)   the visible half of a circle on such a surface (edge highlight)
  wheel(...)        bladed wheel (compressor / turbine / fan / impeller) with correct blade occlusion
  spline(...)       Catmull-Rom resample of a polyline (smooth pipe and flow paths)
  pipe(...)         a tube drawn along a screen-space path
  flow(...)         particles streaming along a path (air, exhaust, oil, coolant, current...)
  arrow_head(...)   small arrowhead at the end of a path

Axis convention for rev/wheel: axis "x" | "y" | "z"; `c` = the two other coordinates of the axis line,
in (X, Y, z) order with the axial one removed, e.g. axis "x" -> c = (Y, z).
"""
import math

import numpy as np
import skia

from .gfx import (LIGHT3, _hull, clamp, col, hx, lin_grad, mix, paint, poly_path, shade)


# ----------------------------------------------------------------- geometry helpers
def _axmap(axis, a, r, th, c):
    a, r, th = np.broadcast_arrays(np.asarray(a, float), np.asarray(r, float), np.asarray(th, float))
    u, v = r * np.cos(th), r * np.sin(th)
    if axis == "x":
        return a, c[0] + u, c[1] + v
    if axis == "y":
        return c[0] + u, a, c[1] + v
    return c[0] + u, c[1] + v, a


def axis_dir_screen(pj, axis):
    e = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    p0, p1 = pj(0, 0, 0), pj(*e)
    d = p1 - p0
    return d / (np.linalg.norm(d) + 1e-9)


def axis_depth_sign(pj, axis):
    e = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    return float(np.sign(pj.depth(*e) - pj.depth(0, 0, 0)) or 1.0)


def ring(pj, axis, c, a, r, n=64, th0=0.0):
    th = th0 + np.linspace(0, 2 * np.pi, n, endpoint=False)
    return pj(*_axmap(axis, a, r, th, c))


def _radial_depth(pj, axis, th):
    """Depth of the unit radial direction at angle th (negative = toward the viewer)."""
    X, Y, z = _axmap(axis, 0.0, 1.0, th, (0.0, 0.0))
    return pj.depth(X, Y, z) - pj.depth(0.0, 0.0, 0.0)


# ----------------------------------------------------------------- surfaces of revolution
def rev(cv, pj, axis, c, as_, rs, base, alpha=1.0, n=64, outline=True, caps=True, edge=None, edge_w=2.0,
        glow=0.0, ks=(0.55, 1.25, 0.95, 0.42), fill_a=1.0):
    """Surface of revolution: profile (as_[i], rs[i]) along the axis. Shaded like ev.gfx.vcyl.
    fill_a < 1 makes the body see-through (x-ray housings) while the edge stays solid."""
    as_, rs = np.asarray(as_, float), np.asarray(rs, float)
    rings = [ring(pj, axis, c, a, max(r, 1e-3), n) for a, r in zip(as_, rs)]
    ud = axis_dir_screen(pj, axis)
    perp = np.array([-ud[1], ud[0]])
    if perp[1] > 0:
        perp = -perp                      # point "up" on screen: lit side
    mid = pj(*_axmap(axis, as_.mean(), 0, 0, c))
    R = max(rs.max(), 1e-3) * pj.s * 1.02
    p0, p1 = mid + perp * R, mid - perp * R
    shader = lin_grad(tuple(p0), tuple(p1), [shade(base, ks[0] * 0 + 1.05), shade(base, ks[1]), shade(base, ks[2]),
                                             shade(base, ks[3])], [0, 0.3, 0.55, 1])
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(alpha)))
    fill = skia.Paint(AntiAlias=True)
    fill.setShader(shader)
    builder = skia.OpBuilder() if outline or glow else None
    if fill_a < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(fill_a)))
    for i in range(len(rings) - 1):
        h = _hull(np.vstack([rings[i], rings[i + 1]]))
        pth = poly_path(h)
        cv.drawPath(pth, fill)
        if builder is not None:
            builder.add(pth, skia.PathOp.kUnion_PathOp)
    sil = builder.resolve() if builder is not None else None
    if caps:
        sgn = axis_depth_sign(pj, axis)
        i_cap = int(np.argmin(as_)) if sgn > 0 else int(np.argmax(as_))
        if rs[i_cap] > 1e-3:
            cv.drawPath(poly_path(rings[i_cap]), paint(shade(base, 1.08)))
            cv.drawPath(poly_path(rings[i_cap]), paint(shade(base, 0.38), stroke=1.3 * pj.s))
    if fill_a < 1:
        cv.restore()
    if sil is not None:
        if glow > 0 and edge is not None:
            cv.drawPath(sil, paint(edge, a=0.5 * glow, stroke=edge_w * 3 * pj.s, blur=7 * pj.s))
        cv.drawPath(sil, paint(edge if edge is not None else shade(base, 0.3), stroke=(edge_w if edge else 1.5) * pj.s))
    if alpha < 1:
        cv.restore()


def ring_front(cv, pj, axis, c, a, r, color, width=2.0, alpha=1.0, n=72, back=False):
    """Stroke the visible (front) half of a circle; back=True strokes the hidden half (dashed look use)."""
    th = np.linspace(0, 2 * np.pi, n + 1)
    pts = pj(*_axmap(axis, a, r, th, c))
    front = _radial_depth(pj, axis, th) < 0
    sel = ~front if back else front
    path = skia.Path()
    on = False
    for i in range(len(pts)):
        if sel[i]:
            (path.lineTo if on else path.moveTo)(*pts[i])
            on = True
        else:
            on = False
    cv.drawPath(path, paint(color, a=alpha, stroke=width * pj.s))


# ----------------------------------------------------------------- bladed wheels
def wheel(cv, pj, axis, c, nose_a, back_a, hub, tip, nb, theta, base, blade=None, twist=0.6, splitters=False,
          bp_r=None, bp_t=4.0, alpha=1.0, blur=0, blur_step=0.07, rim=None, rim_a=0.0, n_s=14):
    """Bladed wheel turning about `axis`.

    nose_a/back_a: axial positions of the nose (inducer/exducer end) and the back plate.
    hub(s), tip(s): radius of hub and blade tip, s = 0 at the nose .. 1 at the back.
    theta: rotation angle (radians); twist: blade wrap at the nose (sign sets the curvature direction).
    blur: number of extra trailing copies of the blades (motion blur for fast spins).
    """
    blade = blade if blade is not None else shade(base, 1.05)
    s = np.linspace(0, 1, n_s)
    a_s = nose_a + (back_a - nose_a) * s
    h_s = np.array([hub(x) for x in s])
    t_s = np.array([tip(x) for x in s])
    nose_near = pj.depth(*_axmap(axis, nose_a, 0, 0, c)) < pj.depth(*_axmap(axis, back_a, 0, 0, c))
    bp_r = bp_r if bp_r is not None else h_s[-1]
    back_dir = np.sign(back_a - nose_a) or 1.0
    if alpha < 1:
        cv.saveLayerAlpha(None, int(255 * clamp(alpha)))

    def backplate():
        rev(cv, pj, axis, c, [back_a, back_a + back_dir * bp_t], [bp_r, bp_r], base, n=72)

    def blades(sel_far, th0, a_mult=1.0):
        items = []
        kinds = [(0.0, 0.0)] + ([(math.pi / nb, 0.45)] if splitters else [])
        for off, s_start in kinds:
            for k in range(nb):
                ph = th0 + 2 * math.pi * k / nb + off
                m = s >= s_start
                phi = ph + twist * (1 - s[m]) ** 2
                Xh = _axmap(axis, a_s[m], h_s[m], phi, c)
                Xt = _axmap(axis, a_s[m], t_s[m], phi, c)
                mid_phi = ph + twist * 0.15
                dep = float(_radial_depth(pj, axis, mid_phi))
                if (dep > 0) != sel_far:
                    continue
                P = np.vstack([pj(*Xh), pj(*Xt)[::-1]])
                # Lambert-ish shade from the blade's tangential normal
                nX, nY, nz = _axmap(axis, 0.0, 1.0, mid_phi + math.pi / 2, (0.0, 0.0))
                lam = abs(nX * LIGHT3[0] + nY * LIGHT3[1] + nz * LIGHT3[2])
                face = abs(float(_radial_depth(pj, axis, mid_phi + math.pi / 2)))
                items.append((pj.depth(*_axmap(axis, a_s.mean(), t_s.mean() * 0.7, mid_phi, c)), P, lam, face))
        items.sort(key=lambda x: -x[0])
        for _, P, lam, face in items:
            cfill = shade(blade, 0.55 + 0.6 * lam + 0.15 * face)
            path = poly_path(P)
            cv.drawPath(path, paint(cfill, a=a_mult))
            cv.drawPath(path, paint(shade(blade, 0.32), a=a_mult, stroke=1.3 * pj.s))
            if rim is not None and rim_a > 0:
                cv.drawPath(poly_path(P[len(P) // 2:], close=False), paint(rim, a=a_mult * rim_a, stroke=2.2 * pj.s))

    def hub_body():
        rev(cv, pj, axis, c, a_s, h_s, base, n=56)

    def all_blades(sel_far):
        for j in range(blur, 0, -1):
            blades(sel_far, theta - j * blur_step, a_mult=0.28 * (1 - j / (blur + 1)))
        blades(sel_far, theta)

    if nose_near:
        backplate()
        all_blades(True)
        hub_body()
        all_blades(False)
    else:
        all_blades(True)
        hub_body()
        all_blades(False)
        backplate()
    if alpha < 1:
        cv.restore()


# ----------------------------------------------------------------- paths, pipes, flows
def spline(pts, n=120):
    """Catmull-Rom through pts (N,2 or N,3), resampled to ~n points evenly by arc length."""
    P = np.asarray(pts, float)
    if len(P) < 3:
        u = np.linspace(0, 1, n)[:, None]
        return P[0] * (1 - u) + P[-1] * u
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for u in np.linspace(0, 1, 16, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-1])
    out = np.array(out)
    return resample(out, n)


def resample(pts, n):
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(pts.shape[1])], 1)


def path_len(pts):
    return float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))


def point_at(pts, d):
    """Point and unit tangent at arc length d along pts."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    d = float(np.clip(d, 0, s[-1]))
    i = int(np.clip(np.searchsorted(s, d) - 1, 0, len(seg) - 1))
    u = (d - s[i]) / max(seg[i], 1e-9)
    p = pts[i] * (1 - u) + pts[i + 1] * u
    tvec = (pts[i + 1] - pts[i]) / max(seg[i], 1e-9)
    return p, tvec


def pipe(cv, pts, width, base, a=1.0, prog=1.0, glass=False):
    """Tube along a screen-space polyline. glass=True draws a see-through tube (for flows inside)."""
    if a <= 0 or prog <= 0:
        return
    pts = np.asarray(pts)
    m = max(2, int(len(pts) * clamp(prog)))
    path = poly_path(pts[:m], close=False)

    def p_(c, w, aa, blur=None):
        p = paint(c, a=aa * a, stroke=w, blur=blur)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        return p
    if glass:
        cv.drawPath(path, p_(hx("#5d7499"), width + 6, 0.55))
        cv.drawPath(path, p_(hx("#0a1220"), width, 0.88))
        cv.drawPath(path, p_(base, width, 0.18))
        hi = poly_path(pts[:m] + np.array([0, -width * 0.28]), close=False)
        cv.drawPath(hi, p_(hx("#9fb6d8"), max(2, width * 0.1), 0.35))
        return
    cv.drawPath(path, p_(shade(base, 0.3), width + 5, 1.0))
    cv.drawPath(path, p_(shade(base, 0.75), width, 1.0))
    cv.drawPath(path, p_(shade(base, 0.95), width * 0.62, 1.0))
    hi = poly_path(pts[:m] + np.array([0, -width * 0.22]), close=False)
    cv.drawPath(hi, p_(shade(base, 1.35), max(2, width * 0.16), 0.8))


def flow(cv, pts, t, speed, spacing, color, r=6.0, a=1.0, t_start=None, t_stop=None, color_at=None, r_at=None,
         glow=True, seed=0, jitter=0.0, offset=0.0):
    """Particles streaming along pts (screen polyline) at `speed` px/s.

    t_start: the flow front enters at t_start and advances along the path; t_stop: the tail leaves after t_stop.
    color_at(u)/r_at(u): colour / radius as a function of position u in 0..1 along the path.
    """
    if a <= 0:
        return
    pts = np.asarray(pts, float)
    L = path_len(pts)
    if L <= 1:
        return
    front = L if t_start is None else speed * (t - t_start)
    tail = -1e9 if t_stop is None else speed * (t - t_stop)
    if front <= 0:
        return
    n = int(L / spacing) + 2
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-1, 1, size=(n, 2)) * jitter
    shift = (speed * t + offset) % spacing
    for k in range(n):
        d = k * spacing + shift
        if d > L or d > front or d < tail:
            continue
        p, tv = point_at(pts, d)
        nrm = np.array([-tv[1], tv[0]])
        q = p + nrm * jit[k, 0]
        u = d / L
        c = color_at(u) if color_at else color
        rr = r_at(u) if r_at else r
        edge = clamp(min(d, L - d) / (spacing * 1.5))
        aa = a * edge
        if glow:
            cv.drawCircle(q[0], q[1], rr * 2.2, paint(c, a=0.35 * aa, blur=rr * 0.9))
        cv.drawCircle(q[0], q[1], rr, paint(c, a=aa))


def arrow_head(cv, pts, color, size=18.0, a=1.0):
    pts = np.asarray(pts, float)
    p, tv = point_at(pts, path_len(pts))
    nrm = np.array([-tv[1], tv[0]])
    tri = np.array([p + tv * size * 0.6, p - tv * size * 0.6 + nrm * size * 0.6, p - tv * size * 0.6 - nrm * size * 0.6])
    cv.drawPath(poly_path(tri), paint(color, a=a))
