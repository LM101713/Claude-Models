#!/usr/bin/env python3
"""
Gemscale Flexi Bat: generator for a print-in-place articulated bat.

A gem-faceted head with tall cupped ears, big eyes and tiny fangs sits on a chest
that carries two jointed wings. Each wing is a chain of thin membrane panels with
raised finger bones, a bony leading edge and scalloped trailing edges; the panels
fold back and forth in the plane of the wing. A jointed abdomen carries clawed feet
and a tail membrane. Every joint is the captured knob-in-socket swivel used by the
Gemscale Flexi Dragon and Octopus, so the bat prints fully assembled, flat on the
bed, with no supports.

Pure Python: needs only `manifold3d`, `numpy` and `trimesh` (pip install -r requirements.txt).

    python gemscale_bat.py --preset standard --out models
    python gemscale_bat.py --preset mini --keyring --out models

The script builds every part with exact CSG, runs printability checks (part gaps,
joint swing, overhangs, bed fit), then writes STL + 3MF files, a GLB for the
renderer, and a text report.
"""

import argparse
import json
import math
import os
import random
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

# =============================================================================
# 1. SETTINGS
# =============================================================================

# Clearances (mm), shared with the Gemscale Dragon and Octopus.
GAP = 0.50      # between a joint housing and the next part's cup
VGAP = 0.40     # air under each tongue bridge (= two 0.2 mm layers)
SIDE = 0.40     # tongue side clearance inside its notch
LAYER = 0.20    # heights are snapped to this layer grid (print at 0.2 mm layers)
WALL = 1.00     # minimum socket wall
MARGIN = 5.0    # extra angle (deg) kept free beyond each joint's swing

# Wing joints fold the wing back (toward the tail) and forward, in the wing plane.
WING_BACK = 15.0     # deg
WING_FWD = 30.0      # deg
BODY_SWING = 25.0    # abdomen joint, either way

# A wing is a chain of panels hinged along the leading edge.
#   pivots: joint centres; pivot 0 is the shoulder on the chest
#   tip:    the wing tip; beta: direction of each panel's finger bone (deg)
#   finger: finger length; ell: depth of the membrane at the next joint's gap
#   scallop: trailing-edge sag as a fraction of the edge length
PRESETS = {
    "standard": dict(
        r_n=1.5, r_e=2.35, band=0.7, hw_wing=4.4, hw_body=4.8,
        tm=1.6, Hb=4.4, Hpk=5.0, Hf=2.4, Hfp=3.0, wb=3.6, wf=2.6,
        pivots=[(11.0, 2.0), (25.0, 10.0), (39.0, 15.0), (53.0, 11.0)], tip=(82.0, 3.0),
        beta=[-74.0, -63.0, -50.0, -37.0], finger=[30.0, 37.0, 37.0, 31.0],
        ell=[29.0, 29.0, 18.0], scallop=0.14, thumb=80.0,
        body=dict(chest=(0.0, 2.0, 9.4, 9.0, 9.0), head=(0.0, 13.2, 9.0, 7.8, 13.0),
                  pivot=(0.0, -7.0), abdomen=(0.0, -15.5, 6.0, 7.5, 6.8),
                  foot=(5.5, -24.0), tail=(0.0, -31.0), eye_r=3.3,
                  ear=dict(c=(5.6, 11.4), rx=4.3, ry=2.3, zb=5.5, zt=20.0)),
        bed=(180, 180)),
    "mini": dict(
        r_n=1.3, r_e=2.05, band=0.6, hw_wing=3.6, hw_body=3.9,
        tm=1.4, Hb=4.0, Hpk=4.5, Hf=2.0, Hfp=2.5, wb=3.0, wf=2.1,
        pivots=[(8.0, 1.5), (19.5, 7.5), (31.0, 8.0)], tip=(55.0, 1.0),
        beta=[-72.0, -58.0, -42.0], finger=[21.0, 26.0, 23.0],
        ell=[20.0, 16.0], scallop=0.14, thumb=80.0,
        body=dict(chest=(0.0, 1.5, 6.9, 6.6, 6.8), head=(0.0, 9.8, 6.8, 5.8, 9.8),
                  pivot=(0.0, -5.2), abdomen=(0.0, -11.6, 4.4, 5.4, 5.2),
                  foot=(4.2, -17.6), tail=(0.0, -22.5), eye_r=2.5,
                  ear=dict(c=(4.1, 8.4), rx=3.2, ry=1.7, zb=4.2, zt=15.0)),
        bed=(180, 180)),
}

TAU = 2.0 * math.pi


# =============================================================================
# 2. SMALL GEOMETRY HELPERS
# =============================================================================

def rup(z):
    return math.ceil(z / LAYER - 1e-6) * LAYER


def d2r(a):
    return math.radians(a)


def dirv(a_deg):
    return (math.cos(d2r(a_deg)), math.sin(d2r(a_deg)))


def add(p, q, s=1.0):
    return (p[0] + s * q[0], p[1] + s * q[1])


def heading(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def ngon(cx, cy, r, n, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n))
            for i in range(n)]


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                     poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def prism(poly, z0, z1):
    return CrossSection([ccw(list(poly))]).extrude(z1 - z0).translate((0, 0, z0))


def hull(points):
    return Manifold.hull_points([tuple(map(float, p)) for p in points])


def lathe(profile, segs=48):
    return CrossSection([profile]).revolve(segs)


def union(parts):
    parts = [p for p in parts if p is not None]
    return Manifold.batch_boolean(parts, 0) if len(parts) > 1 else parts[0]


def cyl(c, r, z0=-5.0, z1=80.0, n=64):
    return Manifold.cylinder(z1 - z0, r, r, n).translate((c[0], c[1], z0))


def wedge(c, a0, a1, R=400.0):
    """Tall solid covering directions a0 -> a1 (deg, CCW) seen from point c."""
    n = max(3, int(abs(a1 - a0) / 6) + 2)
    pts = [c] + [add(c, dirv(a0 + (a1 - a0) * i / (n - 1)), R) for i in range(n)]
    return prism(pts, -5.0, 80.0)


def bezier(p0, c, p1, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])
            for t in np.linspace(0, 1, n)]


def scallop(a, b, toward, sag):
    """Concave curve from a to b, sagging toward the point `toward`."""
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    nx, ny = -(b[1] - a[1]) / ln, (b[0] - a[0]) / ln
    if (toward[0] - m[0]) * nx + (toward[1] - m[1]) * ny < 0:
        nx, ny = -nx, -ny
    return bezier(a, (m[0] + 2 * sag * ln * nx, m[1] + 2 * sag * ln * ny), b)


def ridge_bar(p, q, w0, w1, h0, h1, pk0, pk1, side=0):
    """Bone from p to q, width w0 -> w1, side height h0 -> h1, ridge peak pk0 -> pk1.
    side=0: centred on the line; side=+1: lies entirely on the left (CCW) of p->q."""
    ux, uy = q[0] - p[0], q[1] - p[1]
    ln = math.hypot(ux, uy)
    nx, ny = -uy / ln, ux / ln
    pts = []
    for (c, w, h, pk) in ((p, w0, h0, pk0), (q, w1, h1, pk1)):
        lo, hi = (-w / 2, w / 2) if side == 0 else (0.0, w)
        for o in (lo, hi):
            pts += [(c[0] + o * nx, c[1] + o * ny, 0.0), (c[0] + o * nx, c[1] + o * ny, h)]
        mid = (lo + hi) / 2
        pts.append((c[0] + mid * nx, c[1] + mid * ny, pk))
    return hull(pts)


def gem_dome(cx, cy, ax, ay, az, rng, z0=0.0, lean=0.0, rings=None, jit=0.035):
    """Faceted half-ellipsoid: convex hull of jittered points on rings of latitude."""
    rings = rings or [(0, 14), (22, 13), (42, 11), (60, 9), (76, 6)]
    pts = []
    for ri, (el, n) in enumerate(rings):
        e = d2r(el)
        ph = rng.uniform(0, TAU)
        for i in range(n):
            a = ph + TAU * (i + rng.uniform(-0.18, 0.18)) / n
            j = 1.0 + (rng.uniform(-jit, jit) if ri else 0.0)
            pts.append((cx + ax * math.cos(e) * math.cos(a) * j,
                        cy + ay * math.cos(e) * math.sin(a) * j - lean * math.sin(e),
                        z0 + az * math.sin(e)))
    pts.append((cx, cy - lean, z0 + az))
    return hull(pts)


def ellipsoid_point(c, ax, ay, az, z0, lean, el_deg, az_deg):
    """Surface point and normal of a leaning half-ellipsoid."""
    e, a = d2r(el_deg), d2r(az_deg)
    nrm = np.array([math.cos(e) * math.cos(a) / ax, math.cos(e) * math.sin(a) / ay,
                    math.sin(e) / az])
    nrm /= np.linalg.norm(nrm)
    surf = np.array([c[0] + ax * math.cos(e) * math.cos(a),
                     c[1] + ay * math.cos(e) * math.sin(a) - lean * math.sin(e),
                     z0 + az * math.sin(e)])
    return surf, nrm


# =============================================================================
# 3. THE JOINT
# =============================================================================

class Joint:
    """Knob-in-socket swivel between a front part F and the next part R.

    F owns the round housing, the socket and the notch. R owns the cup, the tongue
    and the knob. The notch lets the tongue swing from `lo` to `hi` degrees (R turning
    clockwise is negative), which is also the joint's hard stop.

    side view of the knob inside F's socket:
             ____
         ___/    \\___  <- 45 deg, no support
        |   knob     |  <- vertical band
         \\___    ___/  <- 45 deg
             \\__/        sits on the bed
    """

    def __init__(self, cfg, hw, pivot, head, lo, hi, t_side, t_top):
        c = cfg["clearance"]
        self.hw, self.c, self.pivot, self.head = hw, c, pivot, head
        self.lo, self.hi = lo, hi
        self.r_n, self.r_e, self.band = cfg["r_n"], cfg["r_e"], cfg["band"]
        self.z1 = self.r_e - self.r_n
        self.z2 = self.z1 + self.band
        self.z3 = self.z2 + (self.r_e - self.r_n)
        self.z_nf = rup(self.z3 + 0.414 * c + 0.05)   # notch floor (top of F under the tongue)
        self.z_n = self.z_nf + VGAP                    # tongue underside
        self.w_t = 2 * self.r_n - 0.3                  # tongue width
        self.rho = hw + GAP                            # R's cup radius
        self.t_side, self.t_top = t_side, t_top
        assert t_side - self.z_n >= 0.95, "tongue too thin"

    def wall_ok(self):
        return self.hw >= self.r_e + self.c + WALL

    def to_world(self, m):
        return m.rotate((0, 0, self.head)).translate((self.pivot[0], self.pivot[1], 0))

    def socket(self):
        c = self.c
        k = (math.sqrt(2) - 1) * c
        s2 = math.sqrt(2) * c
        return self.to_world(lathe([(0, -1), (self.r_n + s2, -1), (self.r_n + s2, 0),
                                    (self.r_e + c, self.z1 - k), (self.r_e + c, self.z2 + k),
                                    (self.r_n + c, self.z3 + k), (self.r_n + c, 80), (0, 80)]))

    def notch(self):
        a = self.w_t / 2 + SIDE
        far = self.hw + 4.0
        pl, ph = d2r(self.lo), d2r(self.hi)
        lo = (a * math.sin(pl), -a * math.cos(pl))
        hi = (-a * math.sin(ph), a * math.cos(ph))
        lo_f = (lo[0] + far * math.cos(pl), lo[1] + far * math.sin(pl))
        hi_f = (hi[0] + far * math.cos(ph), hi[1] + far * math.sin(ph))
        rr = math.hypot(*lo_f)
        a0, a1 = math.atan2(lo_f[1], lo_f[0]), math.atan2(hi_f[1], hi_f[0])
        arc = [(rr * math.cos(a0 + (a1 - a0) * i / 12), rr * math.sin(a0 + (a1 - a0) * i / 12))
               for i in range(1, 12)]
        return self.to_world(prism([lo, lo_f] + arc + [hi_f, hi], self.z_nf, 80))

    def f_cutters(self):
        return self.socket() + self.notch()

    def r_addons(self):
        """Knob and tongue (the tongue bridges over F's notch floor)."""
        r_t = self.w_t / 2
        x_end = self.rho + 1.2
        foot = [(r_t * math.cos(a), r_t * math.sin(a))
                for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 9)]
        foot += [(x_end, -r_t), (x_end, r_t)]
        pts = [(x, y, z) for (x, y) in foot for z in (self.z_n, self.t_side)]
        pts += [(0.0, 0.0, self.t_top), (x_end, 0.0, self.t_top)]
        knob = lathe([(0, 0), (self.r_n, 0), (self.r_e, self.z1), (self.r_e, self.z2),
                      (self.r_n, self.z3), (self.r_n, self.t_side - 0.2), (0, self.t_side - 0.2)])
        return self.to_world(hull(pts) + knob)

    def cup(self):
        return cyl(self.pivot, self.rho, n=96)


# =============================================================================
# 4. WINGS
# =============================================================================

def build_right_wing(cfg):
    """Returns (panels, joints). Panel k is R of joint k; joint 0 is the shoulder."""
    P, T = cfg["pivots"], cfg["tip"]
    n = len(P)
    beta, L, ell = cfg["beta"], cfg["finger"], cfg["ell"]
    hw, tm, Hb, Hpk = cfg["hw_wing"], cfg["tm"], cfg["Hb"], cfg["Hpk"]
    ends = P[1:] + [T]
    d = [heading(P[k], ends[k]) for k in range(n)]
    joints = [Joint(cfg, hw if k else cfg["hw_wing"], P[k], d[k], -WING_BACK, WING_FWD,
                    Hb, Hpk) for k in range(n)]

    panels = []
    for k in range(n):
        Fk = add(P[k], dirv(beta[k]), L[k])
        if k < n - 1:
            Q = add(P[k + 1], dirv(beta[k + 1] - WING_BACK - MARGIN), ell[k])
            edge = scallop(Q, Fk, P[k], cfg["scallop"])
            poly = [P[k], P[k + 1]] + edge
        else:
            edge = scallop(T, Fk, P[k], cfg["scallop"])
            poly = [P[k]] + edge
        parts = [prism(poly, 0.0, tm)]
        # two thin veins fanning across the membrane toward the trailing edge
        mid = edge[len(edge) // 2]
        for f in (0.35, 0.7):
            a = add(add(P[k], dirv(beta[k]), f * L[k] * 0.55), dirv(beta[k] + 90), cfg["wf"] + 0.3)
            b_ = (a[0] + 0.82 * (mid[0] - a[0]) + 0.12 * (f - 0.5) * (ends[k][0] - P[k][0]),
                  a[1] + 0.82 * (mid[1] - a[1]))
            parts.append(ridge_bar(a, b_, 1.0, 0.5, tm + 0.4, tm + 0.2, tm + 0.6, tm + 0.3))

        # finger bone on the panel side of its ray, a pointed tip a little past the membrane
        ftip = add(P[k], dirv(beta[k]), L[k] + 2.0)
        parts.append(ridge_bar(P[k], ftip, cfg["wf"], 0.25, cfg["Hf"], 1.2, cfg["Hfp"], 1.4,
                               side=+1))
        # leading-edge bone
        if k < n - 1:
            parts.append(ridge_bar(P[k], P[k + 1], cfg["wb"], cfg["wb"], Hb, Hb, Hpk, Hpk))
            # housing (knuckle) for the next joint, chamfered top
            c = P[k + 1]
            parts.append(hull([(x, y, z) for (x, y) in ngon(c[0], c[1], hw, 20) for z in (0, Hb - 0.6)]
                              + [(x, y, Hb) for (x, y) in ngon(c[0], c[1], hw - 0.6, 20)]))
        else:
            parts.append(ridge_bar(P[k], T, cfg["wb"], 0.3, Hb, 1.6, Hpk, 1.8))
        # thumb claw at the wrist (the second wing joint)
        if k == 1:
            c = P[2]
            a = cfg["thumb"]
            base = add(c, dirv(a), hw - 0.8)
            tipp = add(add(c, dirv(a), hw + 5.0), dirv(a - 90), 1.2)
            parts.append(hull([(x, y, z) for (x, y) in ngon(base[0], base[1], 1.5, 10)
                               for z in (0, 3.0)] + [(tipp[0], tipp[1], 0), (tipp[0], tipp[1], 0.9)]))
        solid = union(parts)

        # R side of joint k: stay inside its own sector (finger ray to just past the
        # leading bone) and clear the cup around F's housing
        solid = (solid ^ wedge(P[k], beta[k], d[k] + 60.0)) - joints[k].cup()
        # F side of joint k+1: stay out of the next panel's swing, cut socket + notch
        if k < n - 1:
            jn = joints[k + 1]
            keep_out = wedge(jn.pivot, beta[k + 1] - WING_BACK - MARGIN,
                             d[k + 1] + 25.0 + WING_FWD + MARGIN) - cyl(jn.pivot, jn.hw)
            solid = solid - keep_out - jn.f_cutters()
        solid = solid + joints[k].r_addons()
        panels.append(solid)
    return panels, joints, d


def shoulder_keep_out(cfg, d0, mirror=False):
    j0 = cfg["pivots"][0]
    w = wedge(j0, cfg["beta"][0] - WING_BACK - MARGIN, d0 + 25.0 + WING_FWD + MARGIN) \
        - cyl(j0, cfg["hw_wing"])
    return w.mirror((1, 0, 0)) if mirror else w


# =============================================================================
# 5. BODY
# =============================================================================

def build_head_and_chest(cfg, rng):
    b = cfg["body"]
    Hb, hw = cfg["Hb"], cfg["hw_wing"]
    cx, cy, cax, cay, caz = b["chest"]
    parts = [gem_dome(cx, cy, cax, cay, caz, rng)]
    hx, hy, hax, hay, haz = b["head"]
    lean = 0.12 * hay
    parts.append(gem_dome(hx, hy, hax, hay, haz, rng, lean=lean,
                          rings=[(0, 16), (20, 15), (38, 13), (55, 11), (70, 8), (82, 5)]))

    # shoulders: housing + a blob joining it to the chest (both sides)
    S = cfg["pivots"][0]
    for sgn in (1, -1):
        c = (sgn * S[0], S[1])
        parts.append(hull([(x, y, z) for (x, y) in ngon(c[0], c[1], hw, 20) for z in (0, Hb - 0.6)]
                          + [(x, y, Hb) for (x, y) in ngon(c[0], c[1], hw - 0.6, 20)]))
        inner = (sgn * (S[0] - 0.55 * hw - 2.5), S[1])
        parts.append(hull([(x, y, z) for (x, y) in ngon(c[0], c[1], hw - 0.4, 16) for z in (0, Hb - 0.8)]
                          + [(x, y, z) for (x, y) in ngon(inner[0], inner[1], 0.55 * hw + 0.8, 16)
                             for z in (0, Hb + 0.8)]))

    # abdomen joint housing at the back of the chest
    B = b["pivot"]
    hb = cfg["hw_body"]
    Ht = rup(cfg["Hb"] + 0.8)
    parts.append(hull([(x, y, z) for (x, y) in ngon(B[0], B[1], hb, 24) for z in (0, Ht - 0.6)]
                      + [(x, y, Ht) for (x, y) in ngon(B[0], B[1], hb - 0.6, 24)]))

    # ears: broad faceted leaves, tips leaning out a little, cupped on the front
    ear = b["ear"]
    ears, ear_cuts = [], []
    (ex, ey), rx, ry, zb, zt = ear["c"], ear["rx"], ear["ry"], ear["zb"], ear["zt"]
    zm = zb + 0.55 * (zt - zb)

    def ring(cx_, cy_, ax_, ay_, z, n=12):
        return [(cx_ + ax_ * math.cos(TAU * i / n), cy_ + ay_ * math.sin(TAU * i / n), z)
                for i in range(n)]

    for sgn in (1, -1):
        # rounded tip: a small ring just under the top instead of a single point
        e = hull(ring(sgn * ex, ey, rx, ry, 0.0) + ring(sgn * ex, ey, rx, ry, zb)
                 + ring(sgn * (ex + 0.2 * rx), ey - 0.2 * ry, 0.78 * rx, 0.66 * ry, zm)
                 + ring(sgn * (ex + 0.38 * rx), ey - 0.3 * ry, 0.24 * rx, 0.3 * ry, zt - 1.0, 8)
                 + [(sgn * (ex + 0.4 * rx), ey - 0.3 * ry, zt)])
        ears.append(e)
        ear_cuts.append(hull(ring(sgn * (ex + 0.05 * rx), ey + 0.6 * ry, 0.6 * rx, 0.5 * ry, zb + 1.0)
                             + ring(sgn * (ex + 0.22 * rx), ey + 0.3 * ry, 0.46 * rx, 0.34 * ry, zm)
                             + [(sgn * (ex + 0.36 * rx), ey + 0.05 * ry, zt - 2.4)]))
    parts += ears

    # eyes: spheres on the face with a 45 deg chin under each, round pupil dimples
    er = b["eye_r"]
    eyes, pupils = [], []
    for sgn in (1, -1):
        surf, nrm = ellipsoid_point((hx, hy), hax, hay, haz, 0.0, lean, 30, 90 - sgn * 30)
        c = surf + nrm * 0.36 * er
        ball = Manifold.sphere(er, 48).translate(tuple(c))
        chin = Manifold.sphere(er, 48).translate(tuple(c + np.array([-nrm[0], -nrm[1], -1.0]) * er * 0.9))
        eyes.append(Manifold.batch_hull([ball, chin]))
        dvec = np.array([nrm[0], nrm[1], 0.0])
        dvec = dvec / np.linalg.norm(dvec) * math.cos(d2r(10)) + np.array([0, 0, math.sin(d2r(10))])
        dvec /= np.linalg.norm(dvec)
        pr = 0.5 * er
        cut = Manifold.cylinder(6.0, pr, pr, 36)
        yaw = math.degrees(math.atan2(dvec[1], dvec[0]))
        pitch = math.degrees(math.acos(max(-1, min(1, dvec[2]))))
        pupils.append(cut.rotate((0, pitch, 0)).rotate((0, 0, yaw)).translate(tuple(c + dvec * (er - 1.1))))
    parts += eyes

    # nose: a small faceted snout bump between the eyes (underside is a 45 deg slope)
    surf, nrm = ellipsoid_point((hx, hy), hax, hay, haz, 0.0, lean, 22, 90)
    ns = 0.11 * haz
    yb, zn = surf[1] - 0.8, surf[2]
    parts.append(hull([(-1.6 * ns, yb, zn - ns), (1.6 * ns, yb, zn - ns), (-1.4 * ns, yb, zn + 1.2 * ns),
                       (1.4 * ns, yb, zn + 1.2 * ns), (-0.7 * ns, yb + 1.8 * ns, zn + 0.6 * ns),
                       (0.7 * ns, yb + 1.8 * ns, zn + 0.6 * ns), (0.0, yb + 1.6 * ns, zn - 0.1 * ns)]))

    # fangs: two pointed teeth under the snout
    for sgn in (1, -1):
        fx = sgn * 0.15 * hax
        surf, nrm = ellipsoid_point((hx, hy), hax, hay, haz, 0.0, lean, 8, 90 - sgn * 7)
        yf = surf[1] - 0.8
        zt = 0.33 * haz
        fl = 0.24 * haz
        fw = 0.09 * hax
        parts.append(hull([(fx - fw, yf, zt), (fx + fw, yf, zt), (fx, yf + 1.9, zt - 0.3),
                           (fx, yf + 0.9, zt - fl)]))

    solid = union(parts)
    return solid, ear_cuts, pupils


def build_abdomen(cfg, rng):
    b = cfg["body"]
    cx, cy, ax, ay, az = b["abdomen"]
    tm = cfg["tm"]
    parts = [gem_dome(cx, cy, ax, ay, az, rng, rings=[(0, 12), (25, 11), (48, 9), (68, 6)])]
    fx, fy = b["foot"]
    tail = b["tail"]
    for sgn in (1, -1):
        hip = (sgn * 0.55 * ax, cy - 0.35 * ay)
        foot = (sgn * fx, fy)
        parts.append(ridge_bar(hip, foot, 2.2, 1.6, 2.8, 2.2, 3.4, 2.6))
        # three toe claws fanning back from the foot
        for a in (-60, -90, -120):
            a2 = a if sgn > 0 else 180 - a
            toe = add(foot, dirv(a2), 3.0)
            parts.append(ridge_bar(foot, toe, 1.4, 0.2, 2.0, 0.9, 2.4, 1.0))
    # tail membrane between the legs, scalloped, with a tail bone down the middle
    lft, rgt = (-fx - 0.4, fy + 0.8), (fx + 0.4, fy + 0.8)
    top = (0.0, cy - 0.2 * ay)
    poly = [rgt, top, lft] + scallop(lft, tail, top, 0.12)[1:-1] + [tail] + scallop(tail, rgt, top, 0.12)[1:-1]
    parts.append(prism(poly, 0.0, tm))
    parts.append(ridge_bar((0.0, cy - 0.5 * ay), tail, 2.0, 0.3, 2.4, 1.2, 3.0, 1.4))
    return union(parts)


def add_keyring(abd, cfg):
    """Round tab with a vertical hole on the tail tip, so the bat hangs upside down."""
    tail = cfg["body"]["tail"]
    s = cfg["hw_body"] / 4.8
    r_out, r_in, h = 3.8 * s + 0.4, 1.8, rup(2.4 * s + 0.2)
    c = (tail[0], tail[1] - r_out + 1.2)
    tab = Manifold.cylinder(h - 0.4, r_out, r_out, 40) + \
        Manifold.cylinder(0.4, r_out, r_out - 0.4, 40).translate((0, 0, h - 0.4))
    neck = ridge_bar((tail[0], tail[1] + 4.0 * s), c, 2.6 * s, 2.6 * s, h, h, h, h)
    return (abd + tab.translate((c[0], c[1], 0)) + neck) - cyl(c, r_in, n=32)


# =============================================================================
# 6. ASSEMBLY
# =============================================================================

class Part:
    def __init__(self, name, solid, kind, t=0.0):
        self.name, self.solid, self.kind, self.t = name, solid, kind, t


def generate(cfg, verbose=True):
    rng = random.Random(cfg["seed"])
    b = cfg["body"]

    panels, wjoints, d = build_right_wing(cfg)
    for j in wjoints:
        if not j.wall_ok():
            raise ValueError(f"wing joint housing {j.hw} too small for the knob")

    # chest + head (F of both shoulders and of the abdomen joint)
    body, ear_cuts, pupils = build_head_and_chest(cfg, rng)
    bj = Joint(cfg, cfg["hw_body"], b["pivot"], -90.0, -BODY_SWING, BODY_SWING,
               rup(cfg["Hb"] + 0.8), rup(cfg["Hb"] + 0.8) + 0.6)
    if not bj.wall_ok():
        raise ValueError("body joint housing too small")
    sko = [shoulder_keep_out(cfg, d[0]), shoulder_keep_out(cfg, d[0], mirror=True)]
    alpha = 90.0 - BODY_SWING - MARGIN
    abd_ko = wedge(bj.pivot, -90.0 - alpha - BODY_SWING - MARGIN,
                   -90.0 + alpha + BODY_SWING + MARGIN) - cyl(bj.pivot, bj.hw)
    cuts = sko + [abd_ko, bj.f_cutters()]
    for sgn in (1, -1):
        jm = wjoints[0]
        cuts.append(jm.f_cutters() if sgn > 0 else jm.f_cutters().mirror((1, 0, 0)))
    body = body - union(cuts) - union(ear_cuts + pupils)

    # abdomen (R of the body joint)
    abd = build_abdomen(cfg, rng)
    if cfg.get("keyring"):
        abd = add_keyring(abd, cfg)
    abd = (abd ^ wedge(bj.pivot, -90.0 - alpha, -90.0 + alpha)) - bj.cup() - union(sko)
    abd = abd + bj.r_addons()

    parts = [Part("body", body, "body", 0.0), Part("abdomen", abd, "abdomen", 0.1)]
    links = [(0, 1, bj, 1)]
    n = len(panels)
    for side, sgn in (("R", 1), ("L", -1)):
        prev = 0
        for k, p in enumerate(panels):
            solid = p if sgn > 0 else p.mirror((1, 0, 0))
            parts.append(Part(f"wing{side}_{k + 1}", solid, "wing", 0.3 + 0.7 * k / max(1, n - 1)))
            idx = len(parts) - 1
            links.append((prev, idx, wjoints[k], sgn))
            prev = idx

    lo, hi = bbox(parts)
    cy = (lo[1] + hi[1]) / 2
    for p in parts:
        p.solid = p.solid.translate((0, -cy, 0))
    plan = dict(parts=parts, links=links, shift=(0.0, -cy), joints=wjoints + [bj])
    if verbose:
        lo, hi = bbox(parts)
        print(f"built {len(parts)} parts, {len(links)} joints, "
              f"{hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2]:.1f} mm")
    return plan


def bbox(parts):
    lo = np.array([1e9] * 3)
    hi = -lo
    for p in parts:
        bb = p.solid.bounding_box()
        lo = np.minimum(lo, bb[:3])
        hi = np.maximum(hi, bb[3:])
    return lo, hi


# =============================================================================
# 7. PRINTABILITY CHECKS
# =============================================================================

def to_trimesh(m):
    import trimesh
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts),
                           process=False)


def check(plan, cfg, verbose=True):
    parts, links = plan["parts"], plan["links"]
    sx, sy = plan["shift"]
    res, ok = [], True

    def rep(name, passed, msg):
        nonlocal ok
        ok &= passed
        res.append(f"[{'PASS' if passed else 'FAIL'}] {name}: {msg}")

    bad = [p.name for p in parts if p.solid.status().name != "NoError" or p.solid.volume() <= 0]
    rep("solids", not bad, "all parts are closed manifolds" if not bad else f"bad: {bad}")

    whole = union([p.solid for p in parts])
    n_comp = len(whole.decompose())
    rep("separate parts", n_comp == len(parts), f"{n_comp} shells for {len(parts)} parts")
    multi = [p.name for p in parts if len(p.solid.decompose()) != 1]
    rep("one piece each", not multi, "every part is a single connected piece"
        if not multi else f"split: {multi}")

    linked = {(f, r) for (f, r, *_x) in links} | {(r, f) for (f, r, *_x) in links}
    boxes = [p.solid.bounding_box() for p in parts]
    worst_j, worst_o, worst_pair = 9.0, 9.0, None
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            bi, bj = boxes[i], boxes[j]
            if any(bi[k] > bj[k + 3] + 1.5 or bj[k] > bi[k + 3] + 1.5 for k in range(3)):
                continue
            g = parts[i].solid.min_gap(parts[j].solid, 1.5)
            if (i, j) in linked:
                worst_j = min(worst_j, g)
            elif g < worst_o:
                worst_o, worst_pair = g, (parts[i].name, parts[j].name)
    c = cfg["clearance"]
    rep("joint gaps", worst_j >= c - 0.03, f"smallest gap inside a joint {worst_j:.2f} mm "
        f"(design {c:.2f})")
    rep("part gaps", worst_o >= 0.45, f"smallest gap between unlinked parts {min(worst_o, 1.5):.2f} mm"
        + (f" ({worst_pair[0]} / {worst_pair[1]})" if worst_o < 1.5 else " (>= 1.5)"))

    # every joint swings through its full range without its two parts touching
    worst_s, at = 9.0, None
    for (f, r, jt, sgn) in links:
        px, py = sgn * jt.pivot[0] + sx, jt.pivot[1] + sy
        for deg in (jt.lo, jt.lo / 2, jt.hi / 2, jt.hi):
            moved = (parts[r].solid.translate((-px, -py, 0)).rotate((0, 0, sgn * deg))
                     .translate((px, py, 0)))
            g = parts[f].solid.min_gap(moved, 1.0)
            if g < worst_s:
                worst_s, at = g, (parts[r].name, deg)
    rep("joint swing", worst_s >= 0.30, f"wings fold {WING_BACK:.0f} deg back / {WING_FWD:.0f} deg "
        f"forward, abdomen +-{BODY_SWING:.0f} deg; smallest gap while swinging {worst_s:.2f} mm "
        f"({at[0]} at {at[1]:+.0f} deg)")

    tm_ = to_trimesh(whole)
    nrm = tm_.face_normals
    zc = tm_.triangles_center[:, 2]
    down = (nrm[:, 2] < -0.72) & (zc > 0.05)
    ar = tm_.area_faces
    bridge_z = sorted({round(j.z_n, 2) for j in plan["joints"]})
    is_bridge = down & np.any(np.abs(zc[:, None] - np.array(bridge_z)[None, :]) < 0.02, axis=1) \
        & (nrm[:, 2] < -0.999)
    steep = down & ~is_bridge
    rep("overhangs", ar[steep].sum() < 8.0,
        f"{ar[steep].sum():.1f} mm^2 of unsupported overhang (pupil and inner-ear tops); "
        f"{ar[is_bridge].sum():.0f} mm^2 of short tongue bridges")

    lo, hi = bbox(parts)
    bx, by = cfg["bed"]
    size = (hi[0] - lo[0], hi[1] - lo[1])
    rep("bed", size[0] <= bx - 10 and size[1] <= by - 10,
        f"{size[0]:.1f} x {size[1]:.1f} mm on a {bx} x {by} bed")
    rep("socket walls", all(j.wall_ok() for j in plan["joints"]),
        f"housing radius >= knob + clearance + {WALL} mm wall")
    rep("membranes", cfg["tm"] >= 1.2, f"wing membranes {cfg['tm']:.1f} mm thick "
        f"({int(round(cfg['tm'] / LAYER))} layers)")

    if verbose:
        print("\n".join(res))
    return ok, res, whole


def estimate(whole, tm_=None):
    tm_ = tm_ or to_trimesh(whole)
    vol = whole.volume()
    shell = min(vol, tm_.area * 0.84)
    grams = (shell + 0.15 * (vol - shell)) * 1.24e-3
    return vol, grams


# =============================================================================
# 8. EXPORT
# =============================================================================

def write_3mf(path, tm_, name):
    """Minimal 3MF (one object, millimetres). Opens in Bambu Studio, Orca and PrusaSlicer."""
    import zipfile
    v = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm_.vertices)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm_.faces)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
             f'<metadata name="Title">{name}</metadata>\n<resources>\n'
             f'<object id="1" name="{name}" type="model"><mesh>\n<vertices>\n{v}\n</vertices>\n'
             f'<triangles>\n{t}\n</triangles>\n</mesh></object>\n</resources>\n'
             '<build><item objectid="1"/></build>\n</model>\n')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def export(plan, cfg, whole, results, out_dir):
    import trimesh
    os.makedirs(out_dir, exist_ok=True)
    stem = f"GemscaleBat_{cfg['preset']}_seed{cfg['seed']}"
    if cfg.get("keyring"):
        stem += "_keyring"
    if abs(cfg["clearance"] - 0.35) > 1e-6:
        stem += f"_clearance{cfg['clearance']:.2f}".replace(".", "p")
    tm_ = to_trimesh(whole)
    stl = os.path.join(out_dir, stem + ".stl")
    tm_.export(stl)
    mf = os.path.join(out_dir, stem + ".3mf")
    write_3mf(mf, tm_, "Gemscale Flexi Bat")

    scene = trimesh.Scene()
    meta = []
    for i, p in enumerate(plan["parts"]):
        scene.add_geometry(to_trimesh(p.solid), node_name=f"p{i}", geom_name=f"p{i}")
        meta.append(dict(name=p.name, kind=p.kind, t=p.t))
    glb = os.path.join(out_dir, stem + ".glb")
    scene.export(glb)
    with open(os.path.join(out_dir, stem + "_parts.json"), "w") as fh:
        json.dump(meta, fh)

    vol, grams = estimate(whole, tm_)
    lo, hi = bbox(plan["parts"])
    report = [f"Gemscale Flexi Bat  preset={cfg['preset']}  seed={cfg['seed']}  "
              f"clearance={cfg['clearance']:.2f}",
              f"size {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2]:.1f} mm, "
              f"{len(plan['parts'])} parts, {len(plan['links'])} joints",
              f"solid volume {vol / 1000:.1f} cm^3, estimated {grams:.0f} g PLA "
              f"(2 walls, 15 % infill)",
              f"two-tone: filament change at {cfg['Hpk'] + 0.2:.1f} mm colours the body (head, ears, "
              f"eyes, chest and belly tops); the wings stay the first colour", ""] + results
    with open(os.path.join(out_dir, stem + "_report.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print(f"wrote {stl}, {mf}, {glb}")
    return stem


# =============================================================================
# 9. COMMAND LINE
# =============================================================================

def resolve(args):
    cfg = dict(PRESETS[args.preset])
    cfg.update(preset=args.preset, seed=args.seed, clearance=args.clearance,
               keyring=args.keyring)
    if args.bed:
        bx, by = args.bed.lower().split("x")
        cfg["bed"] = (int(bx), int(by))
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--preset", choices=sorted(PRESETS), default="standard")
    ap.add_argument("--seed", type=int, default=7, help="varies the head and body facets")
    ap.add_argument("--clearance", type=float, default=0.35,
                    help="knob-in-socket clearance in mm (0.35 default, 0.4 for looser joints)")
    ap.add_argument("--keyring", action="store_true", help="add a keychain loop on the tail tip")
    ap.add_argument("--bed", help="bed size, e.g. 256x256")
    ap.add_argument("--out", default="gemscale_export")
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args(argv)
    cfg = resolve(args)
    plan = generate(cfg)
    if args.no_check:
        whole = union([p.solid for p in plan["parts"]])
        ok, results = True, []
    else:
        ok, results, whole = check(plan, cfg)
    export(plan, cfg, whole, results, args.out)
    if not ok:
        print("WARNING: some printability checks failed (see above)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
