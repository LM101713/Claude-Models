#!/usr/bin/env python3
"""
Gemscale Flexi T-Rex: generator for a small, fast, print-in-place T. rex that CHOMPS.

The T. rex prints lying on its side, so seen from above you see its classic profile: a huge
toothy head, a tiny arm, a thick leg and a long tail. Every part is a faceted "gem" dome.
The jaw is its own hinged part, so it opens and chomps; the head nods; the four-part tail
wiggles. Every joint is a captured knob-in-socket swivel (the same joint as the Gemscale
Flexi Dragon, Octopus and Bat) and swings in the plane of the profile, so the whole thing
prints fully assembled, flat on the bed, with no supports.

Pure Python: needs only `manifold3d`, `numpy` and `trimesh` (pip install -r requirements.txt).

    python gemscale_trex.py --preset standard --out models
    python gemscale_trex.py --preset mini --keyring --out models

The script builds every part with exact CSG, runs printability checks (part gaps, joint
swing, overhangs, bed fit), then writes STL + 3MF files, a GLB for the renderer, and a
text report.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

# =============================================================================
# 1. SETTINGS
# =============================================================================

# Clearances (mm), shared with the other Gemscale models.
GAP = 0.50      # between a joint housing and the next part's cup
VGAP = 0.40     # air under each tongue bridge (= two 0.2 mm layers)
SIDE = 0.40     # tongue side clearance inside its notch
LAYER = 0.20    # heights are snapped to this layer grid (print at 0.2 mm layers)
WALL = 1.00     # minimum socket wall
MARGIN = 5.0    # extra angle (deg) kept free beyond each joint's swing

# Swing of each joint around its printed pose (deg, counter-clockwise positive).
NECK = (-25.0, 25.0)       # the head nods
JAW = (0.0, 36.0)          # the jaw opens downward from its printed (closed) pose
TAIL = (-30.0, 30.0)       # every tail joint wiggles

TILT = 8.0                 # the head is printed tipped down by this much

# Everything below is in millimetres for the standard T. rex, in the print plane with the
# T. rex facing LEFT (-x), tail to the right, up = +y. (x, y) polygons are the profile
# outlines of convex "gem dome" pieces; T is how thick the piece is on the bed.
BODY = dict(
    pieces=[   # (polygon, thickness)
        ([(-17, 31), (-15, 41), (-6, 47.5), (6, 46.5), (16.5, 40), (22, 31), (17, 22), (4, 19), (-8, 21.5)], 11.0),
        ([(-16, 37), (-9, 47), (-22, 56.5), (-26.5, 56), (-26.5, 47), (-23, 41)], 8.5),
        ([(0, 30), (14, 32), (21, 22), (17, 10), (6, 7), (-3, 17)], 8.5),            # thigh
        ([(6, 13), (17, 13), (14, 0.5), (3, 0.5)], 6.5),                              # shin
        ([(-9, 0.5), (15, 0.5), (15, 5), (-9, 3.5)], 5.0),                            # foot
        ([(-14, 36), (-21.5, 33.5), (-23, 29), (-14, 31.5)], 5.2),                    # tiny arm
        ([(-21.5, 33.5), (-27.5, 33.2), (-29, 29.0), (-22.5, 28.8)], 4.6),             # tiny forearm
    ],
    small=[    # (polygon, thickness): toes, claws, back spikes
        ([(-9, 0.5), (-9, 2.3), (-14, 0.5)], 3.6),
        ([(-9, 1.6), (-9, 3.5), (-14.5, 2.2)], 3.6),
        ([(-9, 2.6), (-9, 4.4), (-13, 4.8)], 3.6),
        ([(-27, 33.2), (-28.5, 30.0), (-33.5, 31.8)], 3.6),
        ([(-27.5, 30.6), (-29, 28.6), (-33.0, 27.8)], 3.6),
        ([(-6.0, 45.6), (-1.5, 46.4), (-3.6, 52.6)], 4.4),
        ([(0.5, 45.4), (4.5, 44.8), (2.8, 52.0)], 4.4),
        ([(7.0, 43.4), (11.0, 41.4), (10.0, 48.6)], 4.0),
        ([(12.5, 40.4), (16.0, 37.0), (16.8, 44.4)], 3.6),
        ([(-15, 43.0), (-11.0, 46.5), (-17.5, 51.0)], 3.6),
    ],
    neck_pivot=(-27.0, 52.0), hip_pivot=(22.0, 32.0),
)
HEAD = dict(   # drawn untilted (facing exactly left); rotated by TILT about the neck pivot
    pieces=[
        ([(-32.5, 58), (-37, 61.5), (-45, 60.5), (-52, 57), (-57, 53), (-57, 49), (-48, 47.6),
          (-40, 47.4), (-34, 48.2), (-31, 52)], 9.5),
        ([(-40, 60), (-46, 61.8), (-47.5, 58.2), (-41.5, 56.8)], 11.5),                # brow
    ],
    small=[
        ([(-35.5, 58.4), (-39.0, 59.6), (-37.6, 65.4)], 4.6),
        ([(-40.5, 59.0), (-44.0, 59.4), (-43.0, 65.8)], 4.4),
    ],
    upper_teeth=[-55.0, -50.0, -45.0, -40.0],   # x of each tooth, hanging from the jaw line
    eye=(-44.0, 54.6, 4.4, 2.8, 3.0, 18.0),     # x, y, semi-axes, slant (deg)
    nostril=(-55.0, 53.6),
    jaw_pivot=(-38.5, 44.4),
    jaw=([(-43.5, 43.9), (-56, 43.7), (-57.5, 41.5), (-55, 38.5), (-47, 37.6), (-43.5, 40.4)], 6.5),
    lower_teeth=[-52.5, -47.5, -42.8],
)
# tail: four parts in their own frames (pivot at the origin, +x toward the tip); stations
# are (x, half height in the profile, side thickness, top thickness)
TAIL_SEGS = [
    dict(name="tail1", L=13.0, prox=(4.4, 5.8), mid=[(7.0, 5.4, 5.2, 6.2)], H=5.6, spikes=[(8.5, 2.4)]),
    dict(name="tail2", L=12.0, prox=(4.0, 5.2), mid=[(6.5, 4.6, 4.4, 5.4)], H=5.0, spikes=[(7.2, 2.1)]),
    dict(name="tail3", L=11.0, prox=(3.9, 4.8), mid=[(6.0, 4.2, 4.1, 5.0)], H=4.6, spikes=[(6.5, 1.8)]),
    dict(name="tip", L=15.0, prox=(3.9, 4.5),
         mid=[(7.0, 3.4, 3.5, 4.4), (11.0, 2.2, 2.4, 3.4), (15.0, 0.7, 1.2, 1.8)], H=None, spikes=[]),
]
TAIL_HEADS = [-4.0, 2.0, 10.0, 20.0]   # printed heading of each tail part (deg)

PRESETS = {
    "standard": dict(
        r_n=1.5, r_e=2.35, band=0.7, s=1.0, th=1.0,
        hws=dict(neck=4.6, jaw=4.4, hip=4.8, t1=4.3, t2=4.0, t3=3.9),
        two_tone=4.4, bed=(180, 180)),
    "mini": dict(
        r_n=1.3, r_e=2.05, band=0.6, s=0.74, th=0.82,
        hws=dict(neck=3.9, jaw=3.8, hip=4.0, t1=3.7, t2=3.6, t3=3.6),
        two_tone=3.8, bed=(180, 180)),
}

TAU = 2.0 * math.pi


# =============================================================================
# 2. SMALL GEOMETRY HELPERS
# =============================================================================

def rup(z):
    return math.ceil(z / LAYER - 1e-6) * LAYER


def d2r(a):
    return math.radians(a)


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


def cyl(c, r, z0=-5.0, z1=80.0, n=96):
    return Manifold.cylinder(z1 - z0, r, r, n).translate((c[0], c[1], z0))


def clean(m, eps=1e-3):
    """Drop zero-volume fragments that exact booleans can leave at coplanar seams."""
    comps = [c for c in m.decompose() if abs(c.volume()) > eps]
    return union(comps) if comps else m


def rotate_about(m, c, deg):
    return m.translate((-c[0], -c[1], 0)).rotate((0, 0, deg)).translate((c[0], c[1], 0))


def rot_pt(p, c, deg):
    a = d2r(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def wedge(c, a0, a1, R=400.0):
    """Tall solid covering the directions a0 -> a1 (deg, CCW) seen from point c."""
    n = max(4, int(abs(a1 - a0) / 6) + 2)
    pts = [c] + [(c[0] + R * math.cos(d2r(a0 + (a1 - a0) * i / (n - 1))),
                  c[1] + R * math.sin(d2r(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    return prism(pts, -5.0, 80.0)


def ridge_heights(T, z_n):
    """Side height and ridge height of a part whose tongue starts at z_n."""
    rh = max(0.4, min(0.25 * T, T - z_n - 1.0))
    return T - rh, T


def piece(poly, T, top=0.4, hs=None, shift=(0.0, 0.0)):
    """Faceted gem dome: vertical walls up to hs, then facets leaning in to a smaller flat
    top at height T. The top can be shifted off-centre (toward the back, say) so the facets
    are not all the same. (A convex polygon; the hull makes it convex anyway.)"""
    poly = ccw(list(poly))
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    hs = 0.5 * T if hs is None else hs
    pts = [(x, y, 0.0) for (x, y) in poly] + [(x, y, hs) for (x, y) in poly]
    pts += [(cx + shift[0] + top * (x - cx), cy + shift[1] + top * (y - cy), T) for (x, y) in poly]
    return hull(pts)


def housing(c, hw, H, n=12, ch=0.6):
    """Faceted joint housing: an n-sided prism with a chamfered top."""
    return hull([(x, y, z) for (x, y) in ngon(c[0], c[1], hw, n, math.pi / n) for z in (0.0, H - ch)]
                + [(x, y, H) for (x, y) in ngon(c[0], c[1], hw - ch, n, math.pi / n)])


def loft(stations):
    """Faceted body through (x, half width, side height, ridge height) stations: flat-
    bottomed pentagon sections, three stations hulled at a time so pieces overlap."""
    secs = []
    for (x, w, hs, ht) in stations:
        secs.append([(x, -w, 0.0), (x, w, 0.0), (x, -w, hs), (x, w, hs),
                     (x, -0.6 * w, hs + 0.75 * (ht - hs)), (x, 0.6 * w, hs + 0.75 * (ht - hs)),
                     (x, 0.0, ht)])
    n = len(secs)
    return union([hull(secs[i] + secs[i + 1] + secs[min(i + 2, n - 1)]) for i in range(n - 1)])


# =============================================================================
# 3. THE JOINT
# =============================================================================

class Joint:
    """Knob-in-socket swivel between a front part F and the next part R.

    F owns the round housing, the socket and the notch. R owns the cup, the tongue and
    the knob. R's printed pose is the middle reference: it can swing from `lo` to `hi`
    degrees (counter-clockwise positive), and the notch is the hard stop.

    side view of the knob inside F's socket:   top view:
             ____                                F | housing ( knob ) <- tongue - R
         ___/    \\___  <- 45 deg, no support      | the notch lets the tongue swing
        |   knob     |  <- vertical band
         \\___    ___/  <- 45 deg
             \\__/        sits on the bed
    """

    def __init__(self, cfg, hw, rng_deg):
        c = cfg["clearance"]
        self.hw, self.c = hw, c
        self.lo, self.hi = rng_deg
        self.r_n, self.r_e, self.band = cfg["r_n"], cfg["r_e"], cfg["band"]
        self.z1 = self.r_e - self.r_n
        self.z2 = self.z1 + self.band
        self.z3 = self.z2 + (self.r_e - self.r_n)
        self.z_nf = rup(self.z3 + 0.414 * c + 0.05)   # notch floor (top of F under the tongue)
        self.z_n = self.z_nf + VGAP                    # tongue underside
        self.w_t = 2 * self.r_n - 0.3                  # tongue width
        self.rho = hw + GAP                            # R's cup radius

    def wall_ok(self, sides=12):
        return self.hw * math.cos(math.pi / sides) >= self.r_e + self.c + WALL

    def sector(self):
        """Angles (relative to R's axis) R's material may occupy: after the full swing it
        stays on R's side of the pivot, with a margin."""
        return -90.0 + MARGIN - self.lo, 90.0 - MARGIN - self.hi

    def socket(self):
        c = self.c
        k = (math.sqrt(2) - 1) * c
        s2 = math.sqrt(2) * c
        return lathe([(0, -1), (self.r_n + s2, -1), (self.r_n + s2, 0),
                      (self.r_e + c, self.z1 - k), (self.r_e + c, self.z2 + k),
                      (self.r_n + c, self.z3 + k), (self.r_n + c, 80), (0, 80)])

    def notch(self):
        """Region swept by the tongue (+ SIDE) in the joint frame (R toward +x)."""
        a = self.w_t / 2 + SIDE
        far = self.hw + 4.0
        pl, ph = d2r(self.lo), d2r(self.hi)
        lo = (a * math.sin(pl), -a * math.cos(pl))
        hi = (-a * math.sin(ph), a * math.cos(ph))
        lo_f = (lo[0] + far * math.cos(pl), lo[1] + far * math.sin(pl))
        hi_f = (hi[0] + far * math.cos(ph), hi[1] + far * math.sin(ph))
        r0, r1 = math.hypot(*lo_f), math.hypot(*hi_f)
        a0, a1 = math.atan2(lo_f[1], lo_f[0]), math.atan2(hi_f[1], hi_f[0])
        arc = [((r0 + (r1 - r0) * t) * math.cos(a0 + (a1 - a0) * t),
                (r0 + (r1 - r0) * t) * math.sin(a0 + (a1 - a0) * t))
               for t in np.linspace(0, 1, 14)[1:-1]]
        return prism([lo, lo_f] + arc + [hi_f, hi], self.z_nf, 80)

    def f_cutters(self, pivot, head_deg):
        """Socket + notch in F, placed at the pivot with R heading toward head_deg."""
        m = self.socket() + self.notch()
        return m.rotate((0, 0, head_deg)).translate((pivot[0], pivot[1], 0))

    def r_addons(self, t_side, t_top, pivot, head_deg):
        """Knob and tongue (the tongue bridges over F's notch floor), placed at the pivot."""
        r_t = self.w_t / 2
        x_end = self.rho + 1.2
        foot = [(r_t * math.cos(a), r_t * math.sin(a))
                for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 9)]
        foot += [(x_end, -r_t), (x_end, r_t)]
        pts = [(x, y, z) for (x, y) in foot for z in (self.z_n, t_side)]
        pts += [(0.0, 0.0, t_top), (x_end, 0.0, t_top)]
        knob = lathe([(0, 0), (self.r_n, 0), (self.r_e, self.z1), (self.r_e, self.z2),
                      (self.r_n, self.z3), (self.r_n, t_side - 0.2), (0, t_side - 0.2)])
        return (hull(pts) + knob).rotate((0, 0, head_deg)).translate((pivot[0], pivot[1], 0))


def make_r(joint, solid, pivot, head_deg, t_root, root=(-35.0, 35.0)):
    """Turn raw R geometry into R: keep it on R's side, clear F's housing with the cup,
    give the tongue a solid flat-topped hub (a fan from the cup out to rho + 3.5 over the
    `root` angles) and add the tongue + knob."""
    t_side, t_top = ridge_heights(t_root, joint.z_n)
    assert t_side - joint.z_n >= 0.95, "tongue too thin"
    s0, s1 = joint.sector()
    r1 = joint.rho + 3.5
    a0, a1 = head_deg + max(root[0], s0), head_deg + min(root[1], s1)
    n = max(4, int((a1 - a0) / 5) + 2)
    arc = [(pivot[0] + r1 * math.cos(d2r(a0 + (a1 - a0) * i / (n - 1))),
            pivot[1] + r1 * math.sin(d2r(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    hub = prism([pivot] + arc, 0.0, t_root)
    sector = wedge(pivot, head_deg + s0, head_deg + s1)
    body = ((solid ^ sector) + hub) - cyl(pivot, joint.rho)
    return body + joint.r_addons(t_side, t_top, pivot, head_deg)


# =============================================================================
# 4. BUILDING THE PARTS
# =============================================================================

def sc(pts, s):
    return [(x * s, y * s) for (x, y) in pts]


def build_body(cfg, J):
    s, th = cfg["s"], cfg["th"]
    pn = tuple(v * s for v in BODY["neck_pivot"])
    ph = tuple(v * s for v in BODY["hip_pivot"])
    parts = [piece(sc(p, s), T * th, top=0.3, shift=(2.2 * s, 2.6 * s) if T > 10 else (0.0, 1.0 * s))
             for (p, T) in BODY["pieces"]]
    parts += [piece(sc(p, s), T * th, top=0.3, hs=0.45 * T * th) for (p, T) in BODY["small"]]
    parts.append(housing(pn, J["neck"].hw, 7.2 * th))
    parts.append(housing(ph, J["hip"].hw, 7.4 * th))
    body = union(parts)
    body = body - J["neck"].f_cutters(pn, 180.0 + TILT) - J["hip"].f_cutters(ph, TAIL_HEADS[0])
    return clean(body), pn, ph


def build_head(cfg, J, pn):
    """Head and jaw, drawn untilted and then tipped down by TILT about the neck pivot."""
    s, th = cfg["s"], cfg["th"]
    pj = tuple(v * s for v in HEAD["jaw_pivot"])
    parts = [piece(sc(p, s), T * th) for (p, T) in HEAD["pieces"]]
    parts += [piece(sc(p, s), T * th, top=0.3, hs=0.4 * T * th) for (p, T) in HEAD["small"]]

    # upper teeth hang from the jaw line (vertical walls: they print without support)
    jl_x = [-57.0, -48.0, -40.0, -34.0]
    jl_y = [49.0, 47.6, 47.4, 48.2]
    tl, tw = 2.6 * s, 1.25 * s
    for x in HEAD["upper_teeth"]:
        ye = float(np.interp(x, jl_x, jl_y)) * s
        x *= s
        parts.append(prism([(x + tw, ye + 1.6), (x - tw, ye + 1.6), (x - 0.15 * s, ye - tl)], 0.0, 3.4 * th))

    # big slanted almond eye gem with a slit pupil
    ex, ey, ax, ay, az, slant = HEAD["eye"]
    ex, ey = ex * s, ey * s
    almond = Manifold.sphere(1.0, 40).scale((ax * s, ay * s, az * th)) \
        .rotate((0, 0, slant)).translate((ex, ey, 8.8 * th))
    parts.append(Manifold.batch_hull([almond, almond.translate((0.0, 0.0, -5.0 * th))]))
    cuts = []
    w2, h2 = 0.55 * s, 1.5 * s
    slit = CrossSection([[(w2, 0.0), (0.0, h2), (-w2, 0.0), (0.0, -h2)]]).extrude(12.0)
    cuts.append(slit.rotate((0, 0, slant + 90.0)).translate((ex, ey, 8.8 * th + 1.5)))
    nx, ny = HEAD["nostril"]
    cuts.append(cyl((nx * s, ny * s), 0.9 * max(s, 0.8), 6.0 * th, 20.0, 16))

    # raw head: keep inside the sector, with the jaw hinge housing added afterwards
    raw = union(parts)
    sector = J["neck"].sector()
    head_raw = raw ^ wedge(pn, 180.0 + sector[0], 180.0 + sector[1])
    head_raw = head_raw + housing(pj, J["jaw"].hw, 6.8 * th)
    head_raw = head_raw - union(cuts) - J["jaw"].f_cutters(pj, 180.0)
    head = make_r(J["neck"], head_raw, pn, 180.0, 7.0 * th)
    # (the neck hub is added last, and on the small T. rex it reaches the jaw hinge: cut again)
    head = head - J["jaw"].f_cutters(pj, 180.0)

    # the jaw: its own hinged part
    jp, jT = HEAD["jaw"]
    jparts = [piece(sc(jp, s), jT * th)]
    ly, lh, lw = 43.8 * s, 2.6 * s, 1.1 * s
    for x in HEAD["lower_teeth"]:
        x *= s
        jparts.append(prism([(x + lw, ly - 1.2), (x - lw, ly - 1.2), (x + 0.1 * s, ly + lh)], 0.0, 3.2 * th))
    jaw = make_r(J["jaw"], union(jparts), pj, 180.0, 5.8 * th, root=(8.0, 42.5))

    # tip everything down by TILT about the neck pivot
    head = rotate_about(clean(head), pn, TILT)
    jaw = rotate_about(clean(jaw), pn, TILT)
    return head, jaw, rot_pt(pj, pn, TILT)


def build_tail(cfg, J, hw_out, k, sg):
    """Tail part k in its own frame: its proximal pivot (the joint with index k) at the
    origin, +x toward the tip. It owns the cup/tongue/knob of that joint and, unless it is
    the tip, the housing of the next one (the socket and notch are cut by the caller)."""
    s, th = cfg["s"], cfg["th"]
    jin = J["tail"][k]
    rho = jin.rho
    s0, s1 = jin.sector()
    al = d2r(min(abs(s0), abs(s1)))
    x0, y0 = rho * math.cos(al), rho * math.sin(al)
    z_floor = jin.z_n + 1.4
    hs0, ht0 = sg["prox"]
    ht0, hs0 = max(ht0 * th, z_floor), max(hs0 * th, z_floor - 0.4)
    st = [(x0, y0, hs0, ht0)]
    L = max(sg["L"] * s, rho + (hw_out or 3.0) + 2.0)
    for (x, w, hs, ht) in sg["mid"]:
        near = x * s < x0 + rho + 1.5
        st.append((x * s, w * s, max(hs * th, z_floor - 0.4) if near else hs * th,
                   max(ht * th, z_floor) if near else ht * th))
    if hw_out:
        H = sg["H"] * th
        st.append((L, hw_out, H, H))
    parts = [loft(st)]
    if hw_out:
        parts.append(housing((L, 0.0), hw_out, sg["H"] * th))
    for (x, size) in sg["spikes"]:
        x, size = x * s, size * max(s, 0.8)
        w = float(np.interp(x, [t[0] for t in st], [t[1] for t in st]))
        parts.append(piece([(x - 1.5 * size, w - 0.8), (x + 1.5 * size, w - 0.8), (x + 0.2 * size, w + 1.7 * size)],
                           2.6 * th, top=0.3, hs=1.0 * th))
    body = make_r(jin, union(parts), (0.0, 0.0), 0.0, ht0)
    return body, L


def add_keyring(tip, cfg, L):
    """Round tab with a hole off the tail tip, so the T. rex hangs from your keys."""
    s = max(cfg["s"], 0.8)
    r_out, r_in, h = 3.6 * s + 0.5, 1.8, rup(2.4 * s + 0.2)
    c = (L + r_out - 1.2, 0.0)
    tab = Manifold.cylinder(h - 0.4, r_out, r_out, 40) + \
        Manifold.cylinder(0.4, r_out, r_out - 0.4, 40).translate((0, 0, h - 0.4))
    x0 = L - 4.5 * s
    neck = hull([(x0, -1.3 * s, 0.0), (x0, 1.3 * s, 0.0), (c[0], -1.3 * s, 0.0), (c[0], 1.3 * s, 0.0),
                 (x0, -1.3 * s, h), (x0, 1.3 * s, h), (c[0], -1.3 * s, h), (c[0], 1.3 * s, h)])
    return (tip + tab.translate((c[0], c[1], 0)) + neck) - cyl(c, r_in, n=32)


# =============================================================================
# 5. ASSEMBLY
# =============================================================================

class Part:
    def __init__(self, name, solid, kind, t=0.0):
        self.name, self.solid, self.kind, self.t = name, solid, kind, t


def generate(cfg, verbose=True):
    hws = cfg["hws"]
    J = dict(neck=Joint(cfg, hws["neck"], NECK), jaw=Joint(cfg, hws["jaw"], JAW),
             hip=Joint(cfg, hws["hip"], TAIL))
    J["tail"] = [J["hip"], Joint(cfg, hws["t1"], TAIL), Joint(cfg, hws["t2"], TAIL),
                 Joint(cfg, hws["t3"], TAIL)]
    all_j = [J["neck"], J["jaw"], J["hip"]] + J["tail"][1:]
    for j in all_j:
        if not j.wall_ok():
            raise ValueError(f"joint housing {j.hw} too small for the knob")

    body, pn, ph = build_body(cfg, J)
    head, jaw, pj = build_head(cfg, J, pn)
    parts = [Part("body", body, "body", 0.1), Part("head", head, "head", 0.0), Part("jaw", jaw, "jaw", 0.0)]
    links = [(0, 1, J["neck"], pn, 180.0 + TILT),
             (1, 2, J["jaw"], pj, 180.0 + TILT)]

    # tail: each part in its own frame, then placed one after another
    hw_out = [hws["t1"], hws["t2"], hws["t3"], None]
    pos, f_idx = ph, 0
    n = len(TAIL_SEGS)
    for k, sg in enumerate(TAIL_SEGS):
        h = TAIL_HEADS[k]
        m, L = build_tail(cfg, J, hw_out[k], k, sg)
        if k + 1 < n:
            rel = TAIL_HEADS[k + 1] - h
            m = m - J["tail"][k + 1].f_cutters((L, 0.0), rel)
        if k == n - 1 and cfg.get("keyring"):
            m = add_keyring(m, cfg, L)
        solid = clean(m).rotate((0, 0, h)).translate((pos[0], pos[1], 0))
        parts.append(Part(sg["name"], solid, "tail", 0.35 + 0.65 * (k + 1) / n))
        r_idx = len(parts) - 1
        links.append((f_idx, r_idx, J["tail"][k], pos, h))
        pos = (pos[0] + L * math.cos(d2r(h)), pos[1] + L * math.sin(d2r(h)))
        f_idx = r_idx

    lo, hi = bbox(parts)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for p in parts:
        p.solid = p.solid.translate((-cx, -cy, 0))
    links = [(f, r, j, (pv[0] - cx, pv[1] - cy), h) for (f, r, j, pv, h) in links]
    plan = dict(parts=parts, links=links, joints=all_j)
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
# 6. PRINTABILITY CHECKS
# =============================================================================

def to_trimesh(m):
    import trimesh
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts),
                           process=False)


def check(plan, cfg, verbose=True):
    parts, links = plan["parts"], plan["links"]
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

    # every joint swings through its whole range without its two parts touching
    worst_s, at = 9.0, None
    for (f, r, jt, pv, h) in links:
        for deg in sorted({jt.lo, 0.5 * jt.lo, 0.5 * jt.hi, jt.hi} - {0.0}):
            moved = rotate_about(parts[r].solid, pv, deg)
            g = parts[f].solid.min_gap(moved, 1.0)
            if g < worst_s:
                worst_s, at = g, (parts[r].name, deg)
    rep("joint swing", worst_s >= 0.30,
        f"jaw opens {JAW[1]:.0f} deg, head nods +-{NECK[1]:.0f}, tail joints +-{TAIL[1]:.0f}; smallest gap "
        f"while swinging {worst_s:.2f} mm ({at[0]} at {at[1]:+.0f} deg)")

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
        f"{ar[steep].sum():.1f} mm^2 of unsupported overhang (eye and nostril tops); "
        f"{ar[is_bridge].sum():.0f} mm^2 of short tongue bridges")

    lo, hi = bbox(parts)
    bx, by = cfg["bed"]
    size = (hi[0] - lo[0], hi[1] - lo[1])
    rep("bed", size[0] <= bx - 10 and size[1] <= by - 10,
        f"{size[0]:.1f} x {size[1]:.1f} mm on a {bx} x {by} bed")
    rep("socket walls", all(j.wall_ok() for j in plan["joints"]),
        f"housing radius >= knob + clearance + {WALL} mm wall (to the flats of the 12-sided housings)")

    merged = []
    for p in parts:
        v = to_trimesh(p.solid).vertices.astype(np.float32)
        if len(np.unique(v, axis=0)) != len(v):
            merged.append(p.name)
    rep("stl precision", not merged, "no vertices merge when saved as float32 STL"
        if not merged else f"near-duplicate vertices in {merged}")

    if verbose:
        print("\n".join(res))
    return ok, res, whole


def estimate(whole, tm_=None):
    """Rough filament estimate (2 walls, 4 top/bottom layers, 15 % infill, PLA)."""
    tm_ = tm_ or to_trimesh(whole)
    vol = whole.volume()
    shell = min(vol, tm_.area * 0.84)
    grams = (shell + 0.15 * (vol - shell)) * 1.24e-3
    return vol, grams


# =============================================================================
# 7. EXPORT
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
    stem = f"GemscaleTRex_{cfg['preset']}"
    if cfg.get("keyring"):
        stem += "_keyring"
    if abs(cfg["clearance"] - 0.35) > 1e-6:
        stem += f"_clearance{cfg['clearance']:.2f}".replace(".", "p")
    tm_ = to_trimesh(whole)
    stl = os.path.join(out_dir, stem + ".stl")
    tm_.export(stl)
    mf = os.path.join(out_dir, stem + ".3mf")
    write_3mf(mf, tm_, "Gemscale Flexi T-Rex")

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
    report = [f"Gemscale Flexi T-Rex  preset={cfg['preset']}  clearance={cfg['clearance']:.2f}",
              f"size {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2]:.1f} mm, "
              f"{len(plan['parts'])} parts, {len(plan['links'])} joints",
              f"solid volume {vol / 1000:.1f} cm^3, estimated {grams:.0f} g PLA "
              f"(2 walls, 15 % infill), about {3.0 * grams:.0f} min",
              f"two-tone: filament change at {cfg['two_tone']:.1f} mm gives the tops of the domes, "
              f"spikes and eye a second colour", ""] + results
    with open(os.path.join(out_dir, stem + "_report.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print(f"wrote {stl}, {mf}, {glb}")
    return stem


# =============================================================================
# 8. COMMAND LINE
# =============================================================================

def resolve(args):
    cfg = json.loads(json.dumps(PRESETS[args.preset]))
    cfg.update(preset=args.preset, clearance=args.clearance, keyring=args.keyring)
    if args.bed:
        bx, by = args.bed.lower().split("x")
        cfg["bed"] = (int(bx), int(by))
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--preset", choices=sorted(PRESETS), default="standard")
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
