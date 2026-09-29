#!/usr/bin/env python3
"""
Gemscale Flexi Octopus: generator for a print-in-place articulated octopus.

A faceted "gem" mantle with big eyes sits on a round body. Eight ridged tentacles
curl around it in a pinwheel. Every tentacle joint is a captured knob-in-socket
swivel (the same joint as the Gemscale Flexi Dragon), so the whole octopus prints
fully assembled, flat on the bed, with no supports.

Pure Python: needs only `manifold3d`, `numpy` and `trimesh` (pip install -r requirements.txt).

    python gemscale_octopus.py --preset standard --out models
    python gemscale_octopus.py --preset mini --seed 42 --keyring

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

# Clearances (mm). Same values as the Gemscale Flexi Dragon, which prints reliably
# on Bambu / Prusa class printers at 0.2 mm layers.
GAP = 0.50      # between a segment's round housing and the next segment's cup
VGAP = 0.40     # air under each tongue bridge (= two 0.2 mm layers)
SIDE = 0.40     # tongue side clearance inside its notch
LAYER = 0.20    # heights are snapped to this layer grid (print at 0.2 mm layers)
WALL = 1.00     # minimum socket wall
THETA = 35.0    # each joint swings +-THETA degrees either side of straight
MARGIN = 5.0    # extra angular margin kept free around the swing cone

PRESETS = {
    # hw: housing radius of each joint along a tentacle (joint 0 sits on the body)
    # L: joint-to-joint length of each full segment; tip: length of the curly tip
    # T: ridge height of each moving part (segments, then the tip)
    # curl: printed bend of each joint (deg, all the same way -> pinwheel)
    "standard": dict(
        Rj=18.0, hw=[5.4, 4.9, 4.4, 4.0, 3.8], L=[10.5, 9.5, 8.6, 7.8], tip=21.0,
        T=[6.0, 5.6, 5.2, 4.9, 4.6], curl=[8, 14, 20, 25, 28], tip_curl=230.0,
        r_n=1.5, r_e=2.35, band=0.7, Tb=6.4, mantle=(15.0, 15.8, 22.0),
        eye_r=4.3, bed=(180, 180)),
    "mini": dict(
        Rj=12.5, hw=[4.1, 3.8, 3.6], L=[8.0, 7.2], tip=15.0,
        T=[4.9, 4.6, 4.4], curl=[10, 20, 27], tip_curl=220.0,
        r_n=1.3, r_e=2.05, band=0.6, Tb=5.0, mantle=(10.3, 10.9, 15.5),
        eye_r=3.1, bed=(180, 180)),
}

TAU = 2.0 * math.pi


# =============================================================================
# 2. SMALL GEOMETRY HELPERS
# =============================================================================

def rup(z):
    """Round a height up to the layer grid."""
    return math.ceil(z / LAYER - 1e-6) * LAYER


def rot2(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def ngon(cx, cy, r, n, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / n), cy + r * math.sin(phase + TAU * i / n))
            for i in range(n)]


def prism(poly, z0, z1):
    """Extrude a CCW polygon from z0 to z1."""
    return CrossSection([poly]).extrude(z1 - z0).translate((0, 0, z0))


def hull(points):
    return Manifold.hull_points([tuple(map(float, p)) for p in points])


def lathe(profile, segs=48):
    """Revolve an (r, z) profile around the z axis. Profile runs from the axis back to it."""
    return CrossSection([profile]).revolve(segs)


def place(m, heading, pos):
    return m.rotate((0, 0, math.degrees(heading))).translate((pos[0], pos[1], 0))


def union(parts):
    parts = [p for p in parts if p is not None]
    return Manifold.batch_boolean(parts, 0) if len(parts) > 1 else parts[0]


def ridge_heights(T, z_n):
    """Side height and ridge height of a part whose tongue starts at z_n."""
    rh = max(0.4, min(0.25 * T, T - z_n - 1.0))
    return T - rh, T


# =============================================================================
# 3. THE JOINT
# =============================================================================

class Joint:
    """Knob-in-socket swivel between a front part F and the next part R.

    F (body or inner segment) owns the round housing, the socket and the notch.
    R (outer segment or tip) owns the cup, the tongue and the knob.

    side view of the knob inside F's socket:   top view:
             ____                                F | housing ( knob ) <- tongue - R
         ___/    \\___  <- 45 deg, no support      | the notch lets the tongue swing +-THETA
        |   knob     |  <- vertical band
         \\___    ___/  <- 45 deg
             \\__/        sits on the bed
    """

    def __init__(self, hw, cfg):
        c = cfg["clearance"]
        self.hw, self.c = hw, c
        self.r_n, self.r_e, self.band = cfg["r_n"], cfg["r_e"], cfg["band"]
        self.z1 = self.r_e - self.r_n
        self.z2 = self.z1 + self.band
        self.z3 = self.z2 + (self.r_e - self.r_n)
        self.z_nf = rup(self.z3 + 0.414 * c + 0.05)   # notch floor (top of F under the tongue)
        self.z_n = self.z_nf + VGAP                    # tongue underside
        self.w_t = 2 * self.r_n - 0.3                  # tongue width
        self.theta = math.radians(THETA)
        self.alpha = math.radians(90.0 - THETA - MARGIN)   # R's half-cone at its cup

    def wall_ok(self):
        return self.hw >= self.r_e + self.c + WALL

    def knob(self, H):
        return lathe([(0, 0), (self.r_n, 0), (self.r_e, self.z1), (self.r_e, self.z2),
                      (self.r_n, self.z3), (self.r_n, H), (0, H)])

    def socket(self):
        c = self.c
        k = (math.sqrt(2) - 1) * c
        s2 = math.sqrt(2) * c
        return lathe([(0, -1), (self.r_n + s2, -1), (self.r_n + s2, 0),
                      (self.r_e + c, self.z1 - k), (self.r_e + c, self.z2 + k),
                      (self.r_n + c, self.z3 + k), (self.r_n + c, 80), (0, 80)])

    def notch(self):
        """Region swept by the tongue (+ SIDE) in F's frame, R toward +x."""
        a = self.w_t / 2 + SIDE
        far = self.hw + 4.0
        th = self.theta
        lo = (-a * math.sin(th), -a * math.cos(th))
        hi = (-a * math.sin(th), a * math.cos(th))
        lo_f = (lo[0] + far * math.cos(-th), lo[1] + far * math.sin(-th))
        hi_f = (hi[0] + far * math.cos(th), hi[1] + far * math.sin(th))
        rr = math.hypot(*lo_f)
        a0, a1 = math.atan2(lo_f[1], lo_f[0]), math.atan2(hi_f[1], hi_f[0])
        arc = [(rr * math.cos(a0 + (a1 - a0) * i / 12), rr * math.sin(a0 + (a1 - a0) * i / 12))
               for i in range(1, 12)]
        return prism([lo, lo_f] + arc + [hi_f, hi], self.z_nf, 80)

    def f_cutters(self):
        return self.socket() + self.notch()


# =============================================================================
# 4. OCTOPUS PARTS
# =============================================================================

def moving_part(jin, T, hw_out=None, L=None, tip_len=None, tip_curl=0.0):
    """One outer part in its local frame: the proximal joint at the origin, +x outward.

    A segment (hw_out, L given) ends in a round housing for the next joint.
    A tip (tip_len given) tapers and curls to a blunt point.
    Returns (solid without the distal joint cuts, side height, ridge height).
    """
    rho = jin.hw + GAP
    x0, y0 = rho * math.cos(jin.alpha), rho * math.sin(jin.alpha)
    t_side, t_top = ridge_heights(T, jin.z_n)

    if tip_len is None:
        pts = [(x0, s * y0, z) for s in (-1, 1) for z in (0.0, t_side)]
        pts += [(x0, 0.0, t_top)]
        for (x, y) in ngon(L, 0.0, hw_out, 12, math.pi / 12):
            pts += [(x, y, 0.0), (x, y, t_side)]
        pts += [(L + 0.45 * hw_out, 0.0, t_top)]
        body = hull(pts)
    else:
        # curly tip: hulls between consecutive cross-sections along a centre line whose
        # curvature grows toward the end, so the tip rolls into a little spiral
        n = 20
        total = math.radians(tip_curl)
        slices = []
        cx, cy, steps = x0, 0.0, 12
        for i in range(n + 1):
            u = i / n
            if i:
                for q in range(steps):
                    uu = (i - 1 + (q + 0.5) / steps) / n
                    a = total * uu ** 1.7
                    cx += math.cos(a) * tip_len / (n * steps)
                    cy += math.sin(a) * tip_len / (n * steps)
            ang = total * u ** 1.7
            nx, ny = -math.sin(ang), math.cos(ang)
            w = 0.55 + (y0 - 0.55) * (1 - u) ** 1.1
            ts = 1.0 + (t_side - 1.0) * (1 - u) ** 0.9
            tt = 1.5 + (t_top - 1.5) * (1 - u) ** 0.9
            slices.append([(cx + sgn * w * nx, cy + sgn * w * ny, z)
                           for sgn in (-1, 1) for z in (0.0, ts)] + [(cx, cy, tt)])
        # hull three sections at a time so neighbouring pieces overlap (not just touch)
        body = union([hull(slices[i] + slices[i + 1] + slices[min(i + 2, n)]) for i in range(n)])

    body = body - Manifold.cylinder(40, rho, rho, 96).translate((0, 0, -10))

    # tongue: rounded end around the knob, bridges over F's notch floor
    r_t = jin.w_t / 2
    x_end = rho + 1.2
    foot = [(r_t * math.cos(a), r_t * math.sin(a))
            for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 9)]
    foot += [(x_end, -r_t), (x_end, r_t)]
    tpts = [(x, y, z) for (x, y) in foot for z in (jin.z_n, t_side)]
    tpts += [(0.0, 0.0, t_top), (x_end, 0.0, t_top)]
    tongue = hull(tpts)

    knob = jin.knob(t_side - 0.2)
    return union([body, tongue, knob]), t_side, t_top


def build_body(cfg, joints0, headings, rng):
    """Round body, faceted mantle and eyes. F side of the eight root joints."""
    Rj, Tb = cfg["Rj"], cfg["Tb"]
    ch = 0.8
    disk = hull([(x, y, z) for (x, y) in ngon(0, 0, Rj, 24) for z in (0, Tb - ch)] +
                [(x, y, Tb) for (x, y) in ngon(0, 0, Rj - ch, 24)])
    parts = [disk]
    for j, h in zip(joints0, headings):
        cx, cy = Rj * math.cos(h), Rj * math.sin(h)
        parts.append(hull([(x, y, z) for (x, y) in ngon(cx, cy, j.hw, 12, h + math.pi / 12)
                           for z in (0, Tb - ch)] +
                          [(x, y, Tb) for (x, y) in ngon(cx, cy, j.hw - ch, 12, h + math.pi / 12)]))

    # mantle: convex hull of jittered points on a leaning half-ellipsoid
    ax, ay, az = cfg["mantle"]
    my = 0.08 * ay                 # mantle centre sits a little toward the back
    lean = 0.16 * ay               # the top leans back (no overhang: see README)
    z0 = Tb - 0.4
    pts = []
    rings = [(0, 12), (24, 11), (46, 10), (66, 8), (82, 5)]
    for ri, (el, n) in enumerate(rings):
        e = math.radians(el)
        ph = rng.uniform(0, TAU)
        for i in range(n):
            a = ph + TAU * (i + rng.uniform(-0.18, 0.18)) / n
            j = 1.0 + (rng.uniform(-0.035, 0.035) if ri else 0.0)
            x = ax * math.cos(e) * math.cos(a) * j
            y = -my + ay * math.cos(e) * math.sin(a) * j - lean * math.sin(e)
            pts.append((x, y, z0 + az * math.sin(e)))
    pts.append((0.0, -my - lean, z0 + az))
    mantle = hull(pts)
    parts.append(mantle)

    # eyes: spheres on the lower front of the mantle, with a 45 deg chin below each
    er = cfg["eye_r"]
    el = math.radians(16)
    eyes, pupils = [], []
    for sgn in (-1, 1):
        a = math.radians(90 - sgn * 27)
        nrm = np.array([math.cos(el) * math.cos(a) / ax, math.cos(el) * math.sin(a) / ay,
                        math.sin(el) / az])
        nrm /= np.linalg.norm(nrm)
        surf = np.array([ax * math.cos(el) * math.cos(a), -my + ay * math.cos(el) * math.sin(a)
                         - lean * math.sin(el), z0 + az * math.sin(el)])
        c = surf + nrm * 0.38 * er
        ball = Manifold.sphere(er, 40).translate(tuple(c))
        chin = Manifold.sphere(er, 40).translate(tuple(c + np.array([-nrm[0], -nrm[1], -1.0])
                                                        * er * 0.9))
        eyes.append(Manifold.batch_hull([ball, chin]))
        # pupil: a round dimple looking forward and a little up
        d = np.array([nrm[0], nrm[1], 0.0])
        d = d / np.linalg.norm(d) * math.cos(math.radians(12)) + np.array([0, 0, math.sin(math.radians(12))])
        d /= np.linalg.norm(d)
        pr = 0.5 * er
        cyl = Manifold.cylinder(6.0, pr, pr, 32)
        yaw = math.degrees(math.atan2(d[1], d[0]))
        pitch = math.degrees(math.acos(max(-1, min(1, d[2]))))
        cyl = cyl.rotate((0, pitch, 0)).rotate((0, 0, yaw))
        pupils.append(cyl.translate(tuple(c + d * (er - 1.1))))
    parts += eyes

    body = union(parts)
    cutters = [place(j.f_cutters(), h, (Rj * math.cos(h), Rj * math.sin(h)))
               for j, h in zip(joints0, headings)]
    body = body - union(cutters + pupils)
    info = dict(mantle_top=z0 + az, mantle_pts=pts, eye_pupils=len(pupils))
    return body, info


def add_keyring(body, info, cfg):
    """Horizontal loop hole through the top of the mantle (for a keychain)."""
    ay = cfg["mantle"][1]
    z = info["mantle_top"] - 4.4
    yc = -0.08 * ay - 0.16 * ay * 0.95        # mantle centre line near the top
    r = 1.7
    # teardrop section: the 45 deg point on top prints without a bridge
    sec = [(yc + r * math.cos(a), z + r * math.sin(a))
           for a in np.linspace(math.pi * 0.75, math.pi * 2.25, 28)] + [(yc, z + r * 1.414)]
    return body - hull([(x, y, zz) for x in (-40, 40) for (y, zz) in sec])


# =============================================================================
# 5. ASSEMBLY
# =============================================================================

class Part:
    def __init__(self, name, solid, kind, tentacle=-1, index=0, t=0.0):
        self.name, self.solid, self.kind = name, solid, kind
        self.tentacle, self.index, self.t = tentacle, index, t


def generate(cfg, verbose=True):
    rng = random.Random(cfg["seed"])
    n_arms = 8
    hws = cfg["hw"]
    joints = [Joint(hw, cfg) for hw in hws]
    for i, j in enumerate(joints):
        if not j.wall_ok():
            raise ValueError(f"joint {i}: housing radius {j.hw} too small for the knob "
                             f"(need >= {j.r_e + j.c + WALL:.2f})")

    headings = [math.radians(90 + 45 * i) for i in range(n_arms)]   # arm 0 points forward (+y)
    body, info = build_body(cfg, joints[:1] * n_arms, headings, rng)
    parts = [Part("body", body, "body")]
    links = []       # (F index, R index, joint, pivot, F heading, R heading)

    n_seg = len(cfg["L"])
    local = []       # moving parts in local frames (shared by all arms)
    for k in range(n_seg + 1):
        jin = joints[k]
        if k < n_seg:
            m, _, _ = moving_part(jin, cfg["T"][k], hw_out=hws[k + 1], L=cfg["L"][k])
            m = m - joints[k + 1].f_cutters().translate((cfg["L"][k], 0, 0))
        else:
            m, _, _ = moving_part(jin, cfg["T"][k], tip_len=cfg["tip"], tip_curl=cfg["tip_curl"])
        local.append(m)

    for a, h0 in enumerate(headings):
        pos = (cfg["Rj"] * math.cos(h0), cfg["Rj"] * math.sin(h0))
        f_idx, f_head = 0, h0
        h = h0
        for k in range(n_seg + 1):
            h = h + math.radians(cfg["curl"][k])
            solid = place(local[k], h, pos)
            kind = "tip" if k == n_seg else "segment"
            parts.append(Part(f"arm{a}_{kind}{k + 1}", solid, kind, a, k + 1,
                              (k + 1) / (n_seg + 1)))
            r_idx = len(parts) - 1
            links.append((f_idx, r_idx, joints[k], pos, f_head, h))
            if k < n_seg:
                pos = (pos[0] + cfg["L"][k] * math.cos(h), pos[1] + cfg["L"][k] * math.sin(h))
                f_idx, f_head = r_idx, h

    if cfg.get("keyring"):
        parts[0].solid = add_keyring(parts[0].solid, info, cfg)

    # centre on the bed
    lo, hi = bbox(parts)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for p in parts:
        p.solid = p.solid.translate((-cx, -cy, 0))
    links = [(f, r, j, (pv[0] - cx, pv[1] - cy), fh, rh) for (f, r, j, pv, fh, rh) in links]

    plan = dict(parts=parts, links=links, joints=joints, info=info, center=(cx, cy))
    if verbose:
        lo, hi = bbox(parts)
        print(f"built {len(parts)} parts, {len(links)} joints, "
              f"{hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2]:.1f} mm")
    return plan


def bbox(parts):
    lo = np.array([1e9] * 3)
    hi = -lo
    for p in parts:
        b = p.solid.bounding_box()
        lo = np.minimum(lo, b[:3])
        hi = np.maximum(hi, b[3:])
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

    # 1. every part is a clean closed solid
    bad = [p.name for p in parts if p.solid.status().name != "NoError" or p.solid.volume() <= 0
           or p.solid.genus() < 0]
    rep("solids", not bad, "all parts are closed manifolds" if not bad else f"bad: {bad}")

    # 2. no part touches another: union keeps every part separate
    whole = union([p.solid for p in parts])
    n_comp = len(whole.decompose())
    rep("separate parts", n_comp == len(parts), f"{n_comp} shells for {len(parts)} parts")

    # 3. gaps in the printed pose
    linked = {(f, r) for (f, r, *_rest) in links} | {(r, f) for (f, r, *_rest) in links}
    boxes = [p.solid.bounding_box() for p in parts]
    worst_j, worst_o, worst_o_pair = 9.0, 9.0, None
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            bi, bj = boxes[i], boxes[j]
            if any(bi[k] > bj[k + 3] + 1.5 or bj[k] > bi[k + 3] + 1.5 for k in range(3)):
                continue
            g = parts[i].solid.min_gap(parts[j].solid, 1.5)
            if (i, j) in linked:
                worst_j = min(worst_j, g)
            elif g < worst_o:
                worst_o, worst_o_pair = g, (parts[i].name, parts[j].name)
    c = cfg["clearance"]
    rep("joint gaps", worst_j >= c - 0.03, f"smallest gap inside a joint {worst_j:.2f} mm "
        f"(design {c:.2f})")
    rep("part gaps", worst_o >= 0.45,
        f"smallest gap between unlinked parts {min(worst_o, 1.5):.2f} mm"
        + (f" ({worst_o_pair[0]} / {worst_o_pair[1]})" if worst_o < 1.5 else " (>= 1.5)"))

    # 4. every joint swings +-THETA about straight without hitting its neighbour
    worst_s, worst_s_at = 9.0, None
    for (f, r, jt, pv, fh, rh) in links:
        fsol, rsol = parts[f].solid, parts[r].solid
        for deg in (-THETA, -THETA / 2, THETA / 2, THETA):
            turn = math.degrees(fh + math.radians(deg) - rh)
            moved = (rsol.translate((-pv[0], -pv[1], 0)).rotate((0, 0, turn))
                     .translate((pv[0], pv[1], 0)))
            g = fsol.min_gap(moved, 1.0)
            if g < worst_s:
                worst_s, worst_s_at = g, (parts[r].name, deg)
    rep("joint swing", worst_s >= 0.30, f"every joint swings +-{THETA:.0f} deg; smallest gap "
        f"while swinging {worst_s:.2f} mm ({worst_s_at[0]} at {worst_s_at[1]:+.0f} deg)")

    # 5. overhangs: downward faces steeper than 45 deg that are not on the bed.
    # Tongue undersides are short bridges (both ends supported) and are listed apart.
    tm = to_trimesh(whole)
    n = tm.face_normals
    zc = tm.triangles_center[:, 2]
    down = (n[:, 2] < -0.72) & (zc > 0.05)        # 45 deg itself prints fine
    area = tm.area_faces
    bridge_z = sorted({round(j.z_n, 2) for j in plan["joints"]})
    is_bridge = down & np.any(np.abs(zc[:, None] - np.array(bridge_z)[None, :]) < 0.02, axis=1) \
        & (n[:, 2] < -0.999)
    steep = down & ~is_bridge
    rep("overhangs", area[steep].sum() < 6.0,
        f"{area[steep].sum():.1f} mm^2 of unsupported overhang (pupil tops); "
        f"{area[is_bridge].sum():.0f} mm^2 of short tongue bridges")

    # 6. fits the bed
    lo, hi = bbox(parts)
    bx, by = cfg["bed"]
    size = (hi[0] - lo[0], hi[1] - lo[1])
    rep("bed", size[0] <= bx - 10 and size[1] <= by - 10,
        f"{size[0]:.1f} x {size[1]:.1f} mm on a {bx} x {by} bed")

    # 7. walls around every socket
    rep("socket walls", all(j.wall_ok() for j in plan["joints"]),
        f"housing radius >= knob + clearance + {WALL} mm wall")

    if verbose:
        print("\n".join(res))
    return ok, res, whole


def estimate(whole, tm=None):
    """Rough filament estimate (2 walls, 4 top/bottom layers, 15 % infill, PLA)."""
    import trimesh  # noqa: F401
    tm = tm or to_trimesh(whole)
    vol = whole.volume()
    shell = min(vol, tm.area * 0.84)
    grams = (shell + 0.15 * (vol - shell)) * 1.24e-3
    return vol, grams


# =============================================================================
# 7. EXPORT
# =============================================================================

def write_3mf(path, tm, name):
    """Minimal 3MF (one object, millimetres). Opens in Bambu Studio, Orca and PrusaSlicer."""
    import zipfile
    v = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
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
    stem = f"GemscaleOctopus_{cfg['preset']}_seed{cfg['seed']}"
    if cfg.get("keyring"):
        stem += "_keyring"
    if abs(cfg["clearance"] - 0.35) > 1e-6:
        stem += f"_clearance{cfg['clearance']:.2f}".replace(".", "p")
    tm = to_trimesh(whole)
    stl = os.path.join(out_dir, stem + ".stl")
    tm.export(stl)
    mf = os.path.join(out_dir, stem + ".3mf")
    write_3mf(mf, tm, "Gemscale Flexi Octopus")

    # per-part GLB for the renderer (vertex colours stay flat; the renderer colours by part)
    scene = trimesh.Scene()
    meta = []
    for i, p in enumerate(plan["parts"]):
        scene.add_geometry(to_trimesh(p.solid), node_name=f"p{i}", geom_name=f"p{i}")
        meta.append(dict(name=p.name, kind=p.kind, tentacle=p.tentacle, t=p.t))
    glb = os.path.join(out_dir, stem + ".glb")
    scene.export(glb)
    with open(os.path.join(out_dir, stem + "_parts.json"), "w") as fh:
        json.dump(meta, fh)

    vol, grams = estimate(whole, tm)
    lo, hi = bbox(plan["parts"])
    report = [f"Gemscale Flexi Octopus  preset={cfg['preset']}  seed={cfg['seed']}  "
              f"clearance={cfg['clearance']:.2f}",
              f"size {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2]:.1f} mm, "
              f"{len(plan['parts'])} parts, {len(plan['links'])} joints",
              f"solid volume {vol / 1000:.1f} cm^3, estimated {grams:.0f} g PLA "
              f"(2 walls, 15 % infill)", ""] + results
    with open(os.path.join(out_dir, stem + "_report.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print(f"wrote {stl}, {mf}, {glb}")
    return stem


# =============================================================================
# 8. COMMAND LINE
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
    ap.add_argument("--seed", type=int, default=7, help="varies the mantle facets")
    ap.add_argument("--clearance", type=float, default=0.35,
                    help="knob-in-socket clearance in mm (0.35 default, 0.4 for looser joints)")
    ap.add_argument("--keyring", action="store_true", help="add a keychain hole through the mantle")
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
