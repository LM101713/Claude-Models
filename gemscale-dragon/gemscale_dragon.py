"""
GEMSCALE FLEXI DRAGON  -  procedural print-in-place articulated dragon for Blender
=====================================================================================

What it makes
    A low-poly "gem" dragon - horned head, crystal dorsal fins, faceted armour
    plates, four legs, spade tail and snap-in wings - built from interlocking
    segments that print IN ONE PIECE, already assembled, with NO SUPPORTS, and
    wiggle straight off the build plate.  Every random seed gives a unique dragon.

How to use (Blender 4.5 LTS or newer recommended - tested on 4.5 and 5.0;
             4.2 LTS also works, just slower)
    1. Open Blender -> "Scripting" workspace -> Text Editor -> Open this file.
    2. Press "Run Script".  A dragon appears and a "Gemscale" tab shows up in the
       3D-View sidebar (press N).  Pick a preset / seed / features -> Generate.
    3. Press "Export STL + 3MF" (and optionally "Render Covers").

    Command line (batch / headless):
        blender -b -P gemscale_dragon.py -- --preset standard --out ./export
        blender -b -P gemscale_dragon.py -- --preset mini --seed 3 --render
        options: --preset mini|standard|long  --seed N  --scale F  --bed 256x256
                 --layout auto|coil|wave|straight  --clearance 0.35  --wing-fit 0.3
                 --neck N --torso N --tail N  --no-wings --no-legs --no-horns
                 --no-spikes --no-plates --keyring  --render --samples N
                 --color-scheme emerald|obsidian|ruby|sunset|frost|rainbow

The joint (why it prints without supports)
    Every joint is a vertical "diamond" knob sitting in a matching socket.  All
    sliding surfaces are vertical or 45 degrees, so nothing droops into the
    clearance gap.  The only horizontal overhang is a short (4-9 mm) bridge - the
    tongue that links each knob to the next segment - printed two 0.2 mm layers
    above the floor under it.  The lower socket ring surrounds the knob a full
    360 degrees, so joints cannot pop apart.

Built-in checks (run on every Generate)
    watertight parts, no touching neighbours, every joint swept through its full
    range without collisions, no unsupported overhangs, everything on the bed.

Notes
    Created with the help of an AI assistant (Claude Code).  If you publish
    models made with this script, follow the site's rules on AI disclosure.
"""

import bpy
import bmesh
import math
import os
import random
import sys
import time
import zipfile
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

# =============================================================================
# 1. SETTINGS  (edit these, or use the sidebar panel / command line)
# =============================================================================

SETTINGS = {
    "preset": "standard",   # "mini", "standard", "long"  (fills the values below)
    "scale": None,          # overall size multiplier (None = preset value)
    "neck": None,           # number of neck segments
    "torso": None,          # segments between front and rear legs
    "tail": None,           # tail segments (before the spade tip)
    "layout": "auto",       # "auto", "coil", "wave", "straight"
    "bed": None,            # printable area in mm, e.g. (180, 180) for A1 mini
    "clearance": 0.35,      # knob <-> socket gap (mm).  Loose joints? lower it
                            # to 0.30.  Fused joints? raise it to 0.40-0.45.
    "seed": 7,              # facet variation - every seed is a unique dragon
    "legs": True,
    "horns": True,
    "spikes": True,
    "plates": True,
    "wings": True,          # snap-in wings (printed flat, press into the shoulder slots)
    "wing_fit": 0.30,       # extra slot width for the wing tabs (mm): tight? 0.4, loose? 0.2
    "keyring": None,        # keyring loop on the tail tip (None = preset: on for mini)
    "out": "//gemscale_export",  # export folder ("//" = next to the .blend)
    "render": False,        # render MakerWorld cover images after export
    "render_samples": 96,
    "color_scheme": "emerald",   # emerald, obsidian, ruby (two-tone) / sunset, frost, rainbow (gradient)
}

PRESETS = {
    # tiny: fits any bed, ~35-45 min print, great keychain / desk fidget
    "mini":     dict(scale=0.62, neck=2, torso=3, tail=5, bed=(180, 180), keyring=True),
    # the hero model: ~30 cm dragon curled to fit an A1 mini (180 mm) bed
    "standard": dict(scale=1.00, neck=2, torso=4, tail=6, bed=(180, 180), keyring=False),
    # show-off version for 256 mm beds (X1/P1/A1/P2S)
    "long":     dict(scale=1.00, neck=3, torso=8, tail=10, bed=(256, 256), keyring=False),
}

# Printer-dependent clearances (mm) - these do NOT scale with the model.
GAP = 0.50      # between a segment's round rear housing and the next segment's cup
VGAP = 0.40     # air under each tongue bridge (= two 0.2 mm layers)
SIDE = 0.40     # tongue side clearance inside its notch
LAYER = 0.20    # heights are snapped to this layer grid (print at 0.2 mm layers)
WALL = 1.20     # minimum socket wall (scaled down a little for minis)

TAU = 2.0 * math.pi


# =============================================================================
# 2. 2D GEOMETRY HELPERS
# =============================================================================

def arc(cx, cy, r, a0, a1, step_deg=5.0):
    n = max(2, int(math.ceil(abs(a1 - a0) / math.radians(step_deg))))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def poly_area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return 0.5 * s


def ccw(poly):
    return list(poly) if poly_area(poly) > 0 else list(poly)[::-1]


def dedupe(poly, eps=1e-4):
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 2 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def clip_halfplane(poly, px, py, nx, ny):
    """Sutherland-Hodgman: keep the part of poly where (p - P) . n >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        da = (a[0] - px) * nx + (a[1] - py) * ny
        db = (b[0] - px) * nx + (b[1] - py) * ny
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return dedupe(out)


def clip_line_side(poly, p, q, keep_left=True):
    """Keep the part of poly left (or right) of the directed line p->q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    nx, ny = (-dy, dx) if keep_left else (dy, -dx)
    return clip_halfplane(poly, p[0], p[1], nx, ny)


def subtract_disk_star(poly, r, step_deg=4.0):
    """poly: CCW, star-shaped around the origin, origin inside disk(0, r).
    Returns poly with the disk removed (the boundary becomes a concave arc)."""
    n = len(poly)
    inside = [math.hypot(*p) < r for p in poly]
    if not any(inside):
        return poly
    exits = [i for i in range(n) if inside[i] and not inside[(i + 1) % n]]
    enters = [i for i in range(n) if not inside[i] and inside[(i + 1) % n]]
    if len(exits) != 1 or len(enters) != 1:
        raise ValueError("cup subtraction: polygon not star shaped")

    def cross_pt(i):
        a = poly[i]
        b = poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        A = dx * dx + dy * dy
        B = 2 * (a[0] * dx + a[1] * dy)
        C = a[0] ** 2 + a[1] ** 2 - r * r
        disc = math.sqrt(max(0.0, B * B - 4 * A * C))
        ts = [t for t in ((-B - disc) / (2 * A), (-B + disc) / (2 * A)) if -1e-9 <= t <= 1 + 1e-9]
        t = ts[0] if ts else 0.5
        return (a[0] + dx * t, a[1] + dy * t)

    q_out = cross_pt(exits[0])
    q_in = cross_pt(enters[0])
    chain = [q_out]
    i = (exits[0] + 1) % n
    while True:
        chain.append(poly[i])
        if i == enters[0]:
            break
        i = (i + 1) % n
    chain.append(q_in)
    a_in = math.atan2(q_in[1], q_in[0])
    a_out = math.atan2(q_out[1], q_out[0])
    while a_out > a_in:
        a_out -= TAU
    return dedupe(chain + arc(0, 0, r, a_in, a_out, step_deg)[1:-1])


def inset_convex(poly, d):
    """Shrink a convex CCW polygon by distance d."""
    poly = ccw(poly)
    out = poly
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        el = math.hypot(ex, ey)
        if el < 1e-9:
            continue
        nx, ny = -ey / el, ex / el          # inward normal for CCW
        out = clip_halfplane(out, a[0] + nx * d, a[1] + ny * d, nx, ny)
        if len(out) < 3:
            return []
    return out


def rot2(p, a):
    c, s = math.cos(a), math.sin(a)
    return (c * p[0] - s * p[1], s * p[0] + c * p[1])


def lerp(a, b, t):
    return a + (b - a) * t


def smooth_profile(points, u):
    """piecewise-linear lookup in [(u, value), ...]"""
    if u <= points[0][0]:
        return points[0][1]
    for (u0, v0), (u1, v1) in zip(points[:-1], points[1:]):
        if u <= u1:
            t = (u - u0) / (u1 - u0)
            t = t * t * (3 - 2 * t)
            return lerp(v0, v1, t)
    return points[-1][1]


def rup(z):
    """round a height up to the layer grid"""
    return math.ceil(z / LAYER - 1e-6) * LAYER


# =============================================================================
# 3. MESH CONSTRUCTION (bmesh)
# =============================================================================

def bm_prism(poly, z0, z1):
    poly = ccw(dedupe(poly))
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in poly]
    top = [bm.verts.new((x, y, z1)) for x, y in poly]
    bm.faces.new(bot[::-1])
    bm.faces.new(top)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    return bm


def bm_lathe(profile, segs=64, cx=0.0, cy=0.0):
    """Solid of revolution around a vertical axis.  profile: [(r, z), ...] bottom->top."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((cx + r * math.cos(TAU * i / segs),
                                    cy + r * math.sin(TAU * i / segs), z)) for i in range(segs)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    return bm


def bm_hull(points, merge=0.02):
    # drop near-duplicate points first: they create sliver faces that can
    # break booleans once coordinates are rounded to floats
    pts = []
    for p in points:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 > merge * merge for q in pts):
            pts.append(p)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
    kill = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def hull_clip(points, planes):
    """Convex hull of points intersected with half-spaces [(point, normal), ...]
    (keeps the side the normal points to).  Returns the clipped vertex list."""
    pts = [Vector(p) for p in points]
    for (pp, nn) in planes:
        pp, nn = Vector(pp), Vector(nn)
        bm = bm_hull([tuple(p) for p in pts])
        keep = [v.co.copy() for v in bm.verts if (v.co - pp).dot(nn) >= 0]
        for e in bm.edges:
            a, b = e.verts[0].co, e.verts[1].co
            da, db = (a - pp).dot(nn), (b - pp).dot(nn)
            if (da >= 0) != (db >= 0):
                t = da / (da - db)
                keep.append(a.lerp(b, t))
        bm.free()
        pts = keep
        if len(pts) < 4:
            return []
    return [tuple(p) for p in pts]


def link_obj(bm, name, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def boolean_solver():
    items = bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items.keys()
    return "MANIFOLD" if "MANIFOLD" in items else "EXACT"


def csg(target, cutters=(), adders=()):
    """Apply DIFFERENCE(cutters) then UNION(adders) to target, delete the tools."""
    solver = boolean_solver()
    tmp = []
    scene_coll = bpy.context.scene.collection

    def add_mod(objs, op):
        c = bpy.data.collections.new("_gs_tmp_" + op.lower())
        scene_coll.children.link(c)
        for o in objs:
            for uc in list(o.users_collection):
                uc.objects.unlink(o)
            c.objects.link(o)
        m = target.modifiers.new(op, "BOOLEAN")
        m.operation = op
        m.operand_type = "COLLECTION"
        m.collection = c
        m.solver = solver
        if solver == "EXACT":
            # the tool objects overlap each other; EXACT needs this to union them correctly
            m.use_self = True
            m.use_hole_tolerant = True
        tmp.append(c)

    if cutters:
        add_mod(cutters, "DIFFERENCE")
    if adders:
        add_mod(adders, "UNION")
    if tmp:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
        old = target.data
        target.modifiers.clear()
        target.data = me
        bpy.data.meshes.remove(old)
        clean_mesh(target)      # merge coincident verts before the next boolean pass
    for c in tmp:
        for o in list(c.objects):
            m = o.data
            bpy.data.objects.remove(o)
            if m.users == 0:
                bpy.data.meshes.remove(m)
        bpy.data.collections.remove(c)
    return target


def _is_closed(bm):
    return all(e.is_manifold and not e.is_boundary for e in bm.edges)


def _obj_closed(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    ok = _is_closed(bm)
    bm.free()
    return ok


def clean_mesh(ob):
    """Merge coincident vertices and dissolve zero-area slivers left by the
    booleans - but only keep the result if the part is still a closed,
    manifold shell (otherwise try a gentler pass, else keep the original)."""
    for dist, dissolve in ((1e-4, True), (1e-6, True), (1e-6, False)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
        if dissolve:
            bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        if _is_closed(bm):
            bm.to_mesh(ob.data)
            bm.free()
            ob.data.update()
            return ob
        bm.free()
    return ob


# =============================================================================
# 4. THE PRINT-IN-PLACE JOINT
# =============================================================================

class Joint:
    """Joint between a front segment F (owns the round housing + socket + notch)
    and a rear segment R (owns the cup, tongue, knob and dorsal spike).

    side view of knob (R) inside socket (F):     top view:
             ____                                 F body |housing(  knob )<- tongue - R
         ___/    \\___  <- 45 deg: no support            | notch lets tongue swing +-theta
        |  knob       |  <- vertical band
         \\___    ___/  <- 45 deg
             \\__/        sits on the bed
    """

    def __init__(self, idx, hw, s, clearance, theta_deg=35.0, alpha_deg=None, margin_deg=5.0):
        self.idx = idx
        self.hw = hw                         # housing radius == local half width
        sj = max(0.70, min(1.0, hw / (9.0 * s))) * s
        self.sj = sj
        self.c = clearance
        self.r_n = max(1.30, 2.2 * sj)       # knob top / bottom radius
        self.r_e = max(self.r_n + 0.75, 3.4 * sj)   # knob equator radius
        self.band = max(0.6, 1.0 * sj)
        self.z1 = self.r_e - self.r_n
        self.z2 = self.z1 + self.band
        self.z3 = self.z2 + (self.r_e - self.r_n)
        self.z_nf = rup(self.z3 + 0.414 * clearance + 0.05)   # notch floor
        self.z_n = self.z_nf + VGAP                           # tongue underside
        self.tongue_min = max(1.2, 2.0 * s)
        self.H = None                        # set when all joints are known
        self.theta = math.radians(theta_deg)
        a = 90.0 - theta_deg - margin_deg if alpha_deg is None else alpha_deg
        self.alpha = math.radians(a)
        self.margin = math.radians(margin_deg)
        self.w_t = max(2.2, 2 * self.r_n - 0.4 * sj)
        self.segs = 64
        self.spike_h = 0.0
        self.pos = None                      # world position (layout)
        self.bend = 0.0                      # printed bend angle (layout)

    def wall_ok(self):
        return self.hw >= self.r_e + self.c + WALL * min(1.0, self.sj + 0.2)

    def knob_profile(self):
        return [(self.r_n, 0.0), (self.r_e, self.z1), (self.r_e, self.z2),
                (self.r_n, self.z3), (self.r_n, self.H)]

    def socket_profile(self):
        c = self.c
        k = (math.sqrt(2) - 1) * c
        s2 = math.sqrt(2) * c
        return [(self.r_n + s2, -1.0), (self.r_n + s2, 0.0),
                (self.r_e + c, self.z1 - k), (self.r_e + c, self.z2 + k),
                (self.r_n + c, self.z3 + k), (self.r_n + c, self.H + 40.0)]

    def notch_poly(self):
        """Top view of the notch in F's frame (joint at origin, R toward -x)."""
        a = self.w_t / 2 + SIDE
        far = self.hw + 3.0
        th = self.theta
        p0 = rot2((0.0, -a), th)
        p1 = rot2((-far, -a), th)
        q0 = rot2((0.0, a), -th)
        q1 = rot2((-far, a), -th)
        a1 = math.atan2(p1[1], p1[0])
        a2 = math.atan2(q1[1], q1[0])
        if a1 < 0:
            a1 += TAU
        rr = math.hypot(*p1)
        return ccw(dedupe([p0, p1] + arc(0, 0, rr, a1, a2, 4.0)[1:-1] + [q1, q0]))

    def r_sweep_cone(self):
        """R's material (in F frame) stays within this angle from -x."""
        return self.alpha + self.theta + self.margin


# =============================================================================
# 5. DRAGON ANATOMY
# =============================================================================

class Seg:
    def __init__(self, idx, kind):
        self.idx = idx
        self.kind = kind            # head, neck, shoulder, torso, hip, tail, tip
        self.front = None           # Joint (R side)
        self.rear = None            # Joint (F side)
        self.L = 0.0
        self.obj = None
        self.footprint = None
        self.origin = (0.0, 0.0)    # world position of the local origin
        self.heading = 0.0          # world angle of local +x
        self.color_t = 0.0          # 0 head .. 1 tail (for gradients)


class Plan:
    pass


def resolve_settings(user=None):
    cfg = dict(SETTINGS)
    if user:
        cfg.update({k: v for k, v in user.items() if v is not None})
    pre = PRESETS.get(cfg["preset"], PRESETS["standard"])
    for k, v in pre.items():
        if cfg.get(k) is None:
            cfg[k] = v
    return cfg


def plan_dragon(cfg):
    s = cfg["scale"]
    c = cfg["clearance"]
    kinds = (["neck"] * cfg["neck"] + ["shoulder"] + ["torso"] * cfg["torso"] +
             ["hip"] + ["tail"] * cfg["tail"])
    if not cfg["legs"]:
        kinds = [("torso" if k in ("shoulder", "hip") else k) for k in kinds]
    segs = [Seg(0, "head")] + [Seg(i + 1, k) for i, k in enumerate(kinds)] + [Seg(len(kinds) + 1, "tip")]
    n_j = len(segs) - 1
    # half-width (== housing radius) at every joint, head -> tail
    wprof = [(0.00, 7.4), (0.14, 8.8), (0.34, 9.8), (0.55, 9.6), (0.70, 8.6), (1.00, 5.4)]
    joints = []
    for j in range(n_j):
        u = j / max(1, n_j - 1)
        hw = smooth_profile(wprof, u) * s
        joints.append(Joint(j + 1, hw, s, c))
    # stiffer / narrower joint behind the hips so the hind feet can tuck back
    for i, sg in enumerate(segs):
        if sg.kind == "hip" and i < n_j:
            jb = joints[i]          # joint i+1 sits at the rear of segs[i]
            jb.theta = math.radians(28.0)
            jb.alpha = math.radians(44.0)
    H = max(rup(j.z_n + j.tongue_min) for j in joints)
    z_edge = max(rup(H - 2.0 * s), 2.4)
    for j in joints:
        j.H = H
    for i, sg in enumerate(segs):
        sg.front = joints[i - 1] if i > 0 else None
        sg.rear = joints[i] if i < n_j else None
        sg.color_t = i / (len(segs) - 1)
        sg.s = s
        sg.z_edge = z_edge
    # segment lengths (front joint -> rear joint)
    for sg in segs[1:-1]:
        jf, jr = sg.front, sg.rear
        wall = WALL * min(1.0, jr.sj + 0.2)
        lmin = jf.hw + GAP + wall + jr.r_e + jr.c
        extra = {"neck": 1.2, "shoulder": 10.0, "torso": 1.8, "hip": 9.0, "tail": 1.2}[sg.kind] * s
        sg.L = lmin + extra
    # dorsal spike heights (on each knob)
    for j in joints:
        u = (j.idx - 1) / max(1, n_j - 1)
        j.spike_h = smooth_profile([(0, 5.2), (0.3, 7.6), (0.6, 7.0), (1.0, 3.8)], u) * s if cfg["spikes"] else 0.0
    plan = Plan()
    plan.cfg = cfg
    plan.s = s
    plan.segs = segs
    plan.joints = joints
    plan.H = H
    plan.head_len = 44.2 * s
    plan.tip_len = 34.0 * s
    return plan


# =============================================================================
# 6. PART BUILDERS
# =============================================================================

def seg_front_constraints(poly, jf):
    """Clip to R's V (angle <= alpha from -x) and remove the cup disk."""
    al = jf.alpha
    poly = clip_halfplane(poly, 0, 0, -math.sin(al), -math.cos(al))
    poly = clip_halfplane(poly, 0, 0, -math.sin(al), math.cos(al))
    return ccw(subtract_disk_star(ccw(poly), jf.hw + GAP))


def body_footprint(sg):
    L = sg.L
    hf = sg.front.hw
    hr = sg.rear.hw
    pts = [(0.5, -hf), (-L, -hr)]
    pts += arc(-L, 0, hr, -math.pi / 2, -3 * math.pi / 2, 5.0)[1:-1]
    pts += [(-L, hr), (0.5, hf)]
    return seg_front_constraints(ccw(dedupe(pts)), sg.front)


def rear_joint_cutters(sg, coll, x0):
    """socket + notch for the joint at (x0, 0) in the segment's local frame"""
    jr = sg.rear
    out = [link_obj(bm_lathe(jr.socket_profile(), jr.segs, x0, 0.0), sg.kind + "_sock", coll)]
    npoly = [(x + x0, y) for x, y in jr.notch_poly()]
    out.append(link_obj(bm_prism(npoly, jr.z_nf, jr.H + 40.0), sg.kind + "_notch", coll))
    return out


def front_joint_adders(sg, coll, rng):
    """knob + tongue (+ crystal spike) at the local origin"""
    jf = sg.front
    out = [link_obj(bm_lathe(jf.knob_profile(), jf.segs, 0.0, 0.0), sg.kind + "_knob", coll)]
    tl = jf.hw + GAP + 1.6 * jf.sj
    a = jf.w_t / 2
    out.append(link_obj(bm_prism([(0.0, -a), (0.0, a), (-tl, a), (-tl, -a)], jf.z_n, jf.H),
                        sg.kind + "_tongue", coll))
    if jf.spike_h > 0:
        out.append(link_obj(bm_hull(spike_points(jf, rng)), sg.kind + "_spike", coll))
    return out


def spike_points(jf, rng):
    """Crystal dorsal fin standing on the knob + tongue.  It only ever moves
    inside the notch of the segment in front, so it can never hit it."""
    H = jf.H - 0.4          # base sunk well into knob/tongue (no hair-thin slivers)
    r = jf.r_n * 0.9
    w = jf.w_t / 2 - 0.2
    tl = jf.hw + GAP + 1.2 * jf.sj
    pts = []
    for i in range(7):
        a = math.pi / 2 - math.pi * i / 6
        pts.append((r * math.cos(a), r * math.sin(a), H))
    pts += [(-tl, w, H), (-tl, -w, H)]
    h = jf.spike_h * (0.9 + 0.2 * rng.random())
    xa = -0.30 * tl
    pts.append((xa, 0.0, H + h))
    pts.append((xa - 0.33 * tl, 0.0, H + 0.60 * h))
    pts.append((0.35 * r, 0.0, H + 0.42 * h))
    return pts


def plate_points(sg, side, rng):
    """Faceted armour plate on one flank (side=+1 left, -1 right) of a body
    segment.  The region is convex and provably stays on this segment:
    V of the front joint, outside the cup circle (tangent), outside the notch
    and socket of the rear joint.  Highest along the spine, sloping to the flank."""
    jf, jr = sg.front, sg.rear
    L = sg.L
    H = jf.H
    s = sg.s
    hf, hr = jf.hw, jr.hw
    poly = [(0.5, -hf), (-L, -hr)] + arc(-L, 0, hr, -math.pi / 2, -3 * math.pi / 2, 6.0)[1:-1] + [(-L, hr), (0.5, hf)]
    poly = ccw(dedupe(poly))
    al = jf.alpha
    poly = clip_halfplane(poly, 0, 0, -math.sin(al), -math.cos(al))
    poly = clip_halfplane(poly, 0, 0, -math.sin(al), math.cos(al))
    y_in = 0.45 * s
    poly = clip_halfplane(poly, 0, side * y_in, 0, side)
    rc = hf + GAP + 0.5
    psi = math.radians(38.0)
    tx, ty = -rc * math.cos(psi), side * rc * math.sin(psi)
    poly = clip_halfplane(poly, tx, ty, tx, ty)
    poly = notch_keepout(poly, jr, -L, side)
    poly = inset_convex(ccw(poly), 0.45 * s)
    if len(poly) < 3 or abs(poly_area(poly)) < 6.0 * s * s:
        return []
    xs = [p[0] for p in poly]
    ys = [p[1] * side for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    # a swept-back scale: the ridge climbs toward the rear, like overlapping armour
    hp = (1.0 * s + 0.30 * min(hf, hr)) * (0.92 + 0.16 * rng.random())
    yr = y0 + 0.30 * (y1 - y0)
    j = lambda a: (rng.random() - 0.5) * a * s
    ridge = [(lerp(x1, x0, 0.16) + j(0.5), side * (yr + j(0.4)), H + hp * 0.50),
             (lerp(x1, x0, 0.70) + j(0.5), side * (yr + 0.08 * (y1 - y0) + j(0.4)), H + hp)]
    shoulder = (lerp(x1, x0, 0.62), side * (y0 + 0.74 * (y1 - y0)), H + hp * 0.38)
    base = [(x, y, sg.z_edge - 0.3) for x, y in poly]
    return base + ridge + [shoulder]


def leg_points(sg, side, which, rng):
    """Chunky faceted leg (list of hulls) on a shoulder/hip segment.  The leg's
    reach is shortened until it fits inside the space the neighbouring segments
    never sweep through, so it never collides and never needs clipping (clipped
    pieces meeting on one plane upset some boolean solvers)."""
    s = sg.s
    L = sg.L
    jf, jr = sg.front, sg.rear
    hw = min(jf.hw, jr.hw)
    H = jf.H
    sd = side
    al = jf.alpha - math.radians(1.5)
    cone = jr.r_sweep_cone() + math.radians(2.0)
    n_v = (-math.sin(al), -sd * math.cos(al))           # inside the front joint's V
    n_c = (math.sin(cone), sd * math.cos(cone))          # outside the rear joint's sweep
    rc = jf.hw + GAP + 0.35
    jitter_seed = rng.random()

    def make(reach):
        jr_ = random.Random(jitter_seed)
        if which == "front":
            root = (-0.56 * L, hw - 2.2 * s)
            elbow = (-0.64 * L, hw + 5.6 * s * reach)
            paw = (-0.56 * L - 0.24 * L * reach, hw + 10.4 * s * reach)
            claws = [(-0.15, 1.0), (-0.70, 0.85), (-1.0, 0.30)]
        else:
            root = (-0.50 * L, hw - 2.2 * s)
            elbow = (-0.64 * L, hw + 5.0 * s * reach)
            paw = (-0.50 * L - 0.42 * L * reach, hw + 8.6 * s * reach)
            claws = [(-0.35, 1.0), (-0.85, 0.65), (-1.0, 0.05)]

        def B(p, r, z1, rx=None, top=0.62, n=7):
            return blob(p[0], sd * p[1], rx or r, r, 0.0, z1, n, top, jitter=jr_)

        # overlapping pieces nest strictly inside their neighbour (no
        # near-coincident surfaces - those break booleans after float rounding)
        pieces = [
            B(root, 5.2 * s, H + 1.4 * s, rx=6.0 * s, top=0.55),
            B(root, 3.4 * s, H + 0.7 * s) + B(elbow, 3.0 * s, H * 0.86),
            B(elbow, 2.3 * s, H * 0.78) + B(paw, 2.4 * s, H * 0.56),
            B(paw, 3.5 * s, H * 0.62, rx=3.9 * s),
        ]
        for dx, dy in claws:
            dl = math.hypot(dx, dy)
            dx, dy = dx / dl, dy / dl
            cl = 4.4 * s * (0.9 + 0.2 * jr_.random()) * (0.6 + 0.4 * reach)
            base = (paw[0] + dx * 1.9 * s, paw[1] + dy * 1.9 * s)
            tip = (base[0] + dx * cl, base[1] + dy * cl)
            px, py = -dy * 1.45 * s, dx * 1.45 * s
            pieces.append([(base[0] + px, sd * (base[1] + py), 0.0), (base[0] - px, sd * (base[1] - py), 0.0),
                           (tip[0], sd * tip[1], 0.0), (base[0], sd * base[1], H * 0.5),
                           (tip[0] - dx * 1.2 * s, sd * (tip[1] - dy * 1.2 * s), H * 0.2)])
        return pieces

    def fits(pieces, margin=0.3):
        for pc in pieces[1:]:          # the root blob is trimmed by the cup tangent below
            for x, y, z in pc:
                if x * n_v[0] + y * n_v[1] < margin:
                    return False
                if (x + L) * n_c[0] + y * n_c[1] < margin:
                    return False
        return True

    reach = 1.0
    pieces = make(reach)
    while not fits(pieces) and reach > 0.45:
        reach -= 0.05
        pieces = make(reach)
    out = []
    for pc in pieces:
        cxp = sum(p[0] for p in pc) / len(pc)
        cyp = sum(p[1] for p in pc) / len(pc)
        ang = math.atan2(cyp, cxp)
        tpt = (rc * math.cos(ang), rc * math.sin(ang), 0.0)
        # safety net only - after the reach search these planes normally cut nothing
        planes = [((0, 0, 0), (n_v[0], n_v[1], 0)),
                  ((-L, 0, 0), (n_c[0], n_c[1], 0)),
                  (tpt, (tpt[0], tpt[1], 0.0))]
        cp = hull_clip(pc, planes)
        if len(cp) >= 4:
            out.append(cp)
    return out


def build_body(sg, coll, rng, cfg):
    fp = body_footprint(sg)
    sg.footprint = fp
    ob = link_obj(bm_prism(fp, 0.0, sg.z_edge), f"{sg.idx:02d}_{sg.kind}", coll)
    adders = core_prisms(sg, fp, coll, x_rear=-sg.L)
    if cfg["plates"]:
        for side in (1, -1):
            pts = plate_points(sg, side, rng)
            if pts:
                adders.append(link_obj(bm_hull(pts), "plate", coll))
    if cfg["legs"] and sg.kind in ("shoulder", "hip"):
        which = "front" if sg.kind == "shoulder" else "rear"
        for side in (1, -1):
            for pts in leg_points(sg, side, which, rng):
                adders.append(link_obj(bm_hull(pts), "leg", coll))
    csg(ob, [], adders)
    cutters = rear_joint_cutters(sg, coll, -sg.L)
    sg.wing_info = None
    if getattr(sg, "want_wings", False):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        tree = BVHTree.FromBMesh(bm)
        bm.free()
        info = []
        for side in (1, -1):
            r = slot_and_mount(sg, side, tree, cfg.get("wing_fit", 0.30))
            if r is None:
                info = None
                break
            pts, mount, tab_depth = r
            cutters.append(link_obj(bm_hull(pts), "slot", coll))
            info.append((mount, tab_depth))
        sg.wing_info = info
    csg(ob, cutters, front_joint_adders(sg, coll, rng))
    sg.obj = clean_mesh(ob)
    return ob


def build_tip(sg, coll, rng, cfg, plan):
    """last segment: cup + knob at the front, tapering tail with a spade"""
    s = plan.s
    jf = sg.front
    H = jf.H
    hf = jf.hw
    Lt = plan.tip_len
    sp_len = 13.0 * s
    sp_w = 7.0 * s
    neck_w = 2.3 * s
    x_sp = -(Lt - sp_len)
    x_mid = -(hf + GAP + 3.0 * s)
    pts = [(0.5, -hf), (x_mid, -hf * 0.92), (x_sp, -neck_w),
           (x_sp - 0.35 * sp_len, -sp_w), (-Lt, 0.0), (x_sp - 0.35 * sp_len, sp_w), (x_sp, neck_w),
           (x_mid, hf * 0.92), (0.5, hf)]
    fp = seg_front_constraints(ccw(dedupe(pts)), jf)
    sg.footprint = fp
    ze = sg.z_edge
    ob = link_obj(bm_prism(fp, 0.0, ze), f"{sg.idx:02d}_tip", coll)
    adders = core_prisms(sg, fp, coll)
    z_end = max(1.8, 2.4 * s)
    # central crest from the knob core down to the spade
    x_c0 = -(hf + GAP + 2.6 * s)
    crest = [(x_c0 + 1.0, hf * 0.55, ze - 0.3), (x_c0 + 1.0, -hf * 0.55, ze - 0.3),
             (x_sp + 1.0, neck_w * 0.8, z_end - 0.3), (x_sp + 1.0, -neck_w * 0.8, z_end - 0.3),
             (x_c0, 0.0, H + 1.8 * s), (lerp(x_c0, x_sp, 0.5), 0.0, lerp(H, z_end, 0.5) + 1.4 * s),
             (x_sp + 1.5, 0.0, z_end + 1.0 * s)]
    crest = hull_clip(crest, [((x_c0 + 1.0, 0, 0), (-1, 0, 0))])
    adders.append(link_obj(bm_hull(crest), "crest", coll))
    cut = [(x_c0, -40, ze + 0.3), (x_c0, 40, ze + 0.3), (-Lt - 5, -40, z_end), (-Lt - 5, 40, z_end),
           (x_c0, -40, H + 30), (x_c0, 40, H + 30), (-Lt - 5, -40, H + 30), (-Lt - 5, 40, H + 30)]
    if cfg["spikes"]:
        for i, t in enumerate((0.3, 0.62)):
            x = lerp(x_c0, x_sp, t)
            zt = lerp(H + 1.8 * s, z_end + 1.0 * s, t) - 0.4
            h = (4.2 - 1.3 * i) * s
            w = (1.4 - 0.25 * i) * s
            # base sunk into the sloped flank so nothing overhangs
            zb = lerp(ze, z_end, (x_c0 - (x + 2.6 * s)) / (x_c0 + Lt + 5)) - 0.3
            adders.append(link_obj(bm_hull([(x + 2.6 * s, 0, zb), (x - 2.6 * s, w, zb),
                                             (x - 2.6 * s, -w, zb), (x - 1.2 * s, 0, zt + h)]), "tspk", coll))
    zs = z_end
    spade = [(x_sp + 0.5, 0, 0.0), (x_sp - 0.35 * sp_len, sp_w - 0.6, 0.0), (x_sp - 0.35 * sp_len, -sp_w + 0.6, 0.0),
             (-Lt + 0.8, 0, 0.0), (x_sp - 0.35 * sp_len, 0, zs + 2.0 * s), (x_sp - 0.05 * sp_len, 0, zs + 1.0 * s),
             (x_sp - 0.35 * sp_len, sp_w * 0.45, zs + 0.5 * s), (x_sp - 0.35 * sp_len, -sp_w * 0.45, zs + 0.5 * s),
             (-Lt + 3.0 * s, 0, zs + 0.8 * s)]
    ring_c = (-Lt - 4.5 + 1.5, 0.0)
    csg(ob, [link_obj(bm_hull(cut), "tipcut", coll)], [])
    csg(ob, [], adders + [link_obj(bm_hull(spade), "spade", coll)])
    extra = front_joint_adders(sg, coll, rng)
    if cfg["keyring"]:
        extra.append(link_obj(bm_lathe([(4.5, 0.0), (4.5, 3.0)], 48, ring_c[0], ring_c[1]), "ring", coll))
    csg(ob, [], extra)
    if cfg["keyring"]:
        csg(ob, [link_obj(bm_lathe([(2.4, -1.0), (2.4, 10.0)], 48, ring_c[0], ring_c[1]), "ringhole", coll)], [])
    sg.obj = clean_mesh(ob)
    return ob


def groove_sweep(apex, sd, depth):
    """Closed solid used to cut a V groove: a triangular section (apex inside
    the surface, 50-deg roof, sloped floor) swept along a polyline with mitred
    joints.  apex: [(x, y, z), ...] on one side (sd = +1 / -1)."""
    n = len(apex)
    bm = bmesh.new()
    rings = []
    for i, (x, y, z) in enumerate(apex):
        a = apex[max(0, i - 1)]
        b = apex[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = ty / tl, -tx / tl                 # horizontal normal
        if ny * sd < 0:
            nx, ny = -nx, -ny                      # point outward
        ext = 0.5 if i in (0, n - 1) else 0.0
        ex, ey = (tx / tl) * ext * (1 if i else -1), (ty / tl) * ext * (1 if i else -1)
        o = depth
        rings.append([bm.verts.new((x + ex, y + ey, z)),
                      bm.verts.new((x + ex + nx * o, y + ey + ny * o, z + o * 1.2)),
                      bm.verts.new((x + ex + nx * o, y + ey + ny * o, z - o * 0.55))])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(3):
            bm.faces.new((r0[k], r0[(k + 1) % 3], r1[(k + 1) % 3], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def build_head(sg, coll, rng, cfg, plan):
    """Low-poly dragon head.  Local origin = neck joint (round back of the skull
    that holds the first neck knob), +x = snout direction.  Everything is a union
    of convex hulls; every downward face is >= 45 deg or sits on the bed."""
    s = plan.s
    jr = sg.rear
    H = jr.H
    hw = jr.hw
    k = s

    def P(pts, sd=1):
        return [(x * k, sd * y * k, z * k) for x, y, z in pts]

    def both(pts):
        out = []
        for x, y, z in pts:
            out.append((x * k, y * k, z * k))
            if abs(y) > 1e-6:
                out.append((x * k, -y * k, z * k))
        return out

    house = [(0.4, -hw)] + arc(0, 0, hw, -math.pi / 2, -3 * math.pi / 2, 5.0)[1:-1] + [(0.4, hw)]
    house = ccw(dedupe(house))
    base = link_obj(bm_prism(house, 0.0, sg.z_edge), f"{sg.idx:02d}_head", coll)
    objs = core_prisms(sg, house, coll, x_rear=0.0)
    hwk = hw / k
    ze = sg.z_edge / k
    parts = []
    # jaw slab: whole skull footprint, low and wide
    parts.append(both([(0.3, hwk, 0), (4, 10.4, 0), (10, 13.0, 0), (16, 13.4, 0), (22, 12.0, 0), (27, 9.8, 0),
                       (0.3, hwk - 0.5, ze), (4, 9.8, 5.2), (10, 12.2, 6.0), (16, 12.6, 6.0),
                       (22, 11.2, 5.6), (27, 9.0, 5.0)]))
    # muzzle slab
    parts.append(both([(22, 10.2, 0), (29, 8.8, 0), (35, 7.6, 0), (40, 6.2, 0), (43, 3.8, 0), (44.2, 0, 0),
                       (22, 9.5, 4.8), (29, 8.1, 4.6), (35, 7.0, 4.3), (40, 5.6, 4.0), (42.8, 3.3, 3.8),
                       (43.8, 0, 3.8)]))
    # cranium (stays clear of the neck knob + its fin)
    x0 = max(3.8, (jr.r_n + jr.c + 1.3) / k)
    parts.append(both([(x0, 6.2, 3.0), (8, 11.2, 4.0), (15, 12.2, 4.5), (22, 10.0, 4.0),
                       (x0 + 1.4, 4.4, 10.6), (9, 7.4, 13.0), (15, 8.0, 14.2), (21, 6.0, 12.8),
                       (11, 0, 15.8), (19, 0, 14.8)]))
    # snout ridge
    parts.append(both([(20, 8.2, 4.0), (42, 4.2, 3.0), (21, 4.8, 11.8), (28, 4.2, 10.6), (36, 3.4, 9.0),
                       (41.5, 2.4, 7.0), (43.9, 0, 5.2), (27, 0, 11.6)]))
    # brow ridges: angular, sitting on the skull (no overhang)
    for sd in (1, -1):
        parts.append(P([(15.5, 6.2, 5.0), (27.0, 5.2, 5.0), (16.5, 11.0, 5.2), (25.0, 9.6, 5.0),
                        (17.0, 6.8, 15.4), (25.8, 5.4, 13.2), (18.6, 10.2, 13.8), (22.0, 8.6, 15.0)], sd))
    # eyes: faceted domes under the brows, looking up and out
    for sd in (1, -1):
        cx, cy = 21.8, 8.5
        pts = []
        for i in range(8):
            a = TAU * i / 8
            pts.append((cx + 3.1 * math.cos(a), cy + 2.4 * math.sin(a), 4.6))
        for i in range(8):
            a = TAU * (i + 0.5) / 8
            pts.append((cx + 2.3 * math.cos(a), cy + 1.7 * math.sin(a) + 0.7, 9.9))
        pts.append((cx + 0.6, cy + 1.3, 11.8))
        parts.append(P(pts, sd))
    # nose bumps
    for sd in (1, -1):
        parts.append(P([(38.5, 1.0, 5.5), (43.0, 1.0, 4.0), (39.0, 3.8, 5.0), (42.5, 3.5, 3.8),
                        (40.5, 2.3, 8.0)], sd))
    high_parts = []
    if cfg["horns"]:
        for sd in (1, -1):
            # main horns: straight faceted cones rising ~58 deg, sweeping back
            hx, hy, hz = 8.4, 6.8, 5.0
            pts = [(hx + 2.8 * math.cos(TAU * i / 6), hy + 2.4 * math.sin(TAU * i / 6), hz) for i in range(6)]
            pts += [(hx - 2.2 + 2.1 * math.cos(TAU * (i + 0.5) / 6), hy + 0.9 + 1.8 * math.sin(TAU * (i + 0.5) / 6),
                     hz + 7.0) for i in range(6)]
            pts += [(-2.6, 11.0, 28.5)]
            high_parts.append(P(pts, sd))       # passes over the neck, never clipped
            # side horns
            parts.append(P([(12.0, 10.2, 5.0), (16.5, 11.0, 5.0), (13.5, 12.6, 4.2), (14.0, 10.6, 9.6),
                            (9.4, 14.0, 13.0), (8.4, 14.8, 16.6)], sd))
            # jaw spikes on the bed, pointing back and out (kept forward of the joint)
            parts.append(P([(9.0, 12.2, 0.0), (15.0, 12.8, 0.0), (12.5, 12.0, 5.2), (4.6, 17.2, 0.0),
                            (5.4, 16.4, 1.4)], sd))
    for pts in parts:
        # low parts may not reach behind the neck joint (the neck swings there)
        if min(p[0] for p in pts) < 0.3:
            pts = hull_clip(pts, [((0.3, 0, 0), (1, 0, 0))])
        if len(pts) >= 4:
            objs.append(link_obj(bm_hull(pts), "head_part", coll))
    for pts in high_parts:
        objs.append(link_obj(bm_hull(pts), "horn", coll))
    cutters = rear_joint_cutters(sg, coll, 0.0)
    for sd in (1, -1):
        cutters.append(link_obj(bm_lathe([(0.25 * k, 4.4 * k), (1.1 * k, 7.4 * k), (1.1 * k, 14 * k)], 12,
                                         40.8 * k, sd * 2.3 * k), "nostril", coll))
        # mouth line: one continuous V groove swept along the jaw (roof >= 50 deg)
        apex = [(22.0, 10.1, 2.75), (25.5, 8.9, 2.7), (29.0, 7.45, 2.62), (32.5, 6.65, 2.55), (35.5, 5.95, 2.45),
                (38.5, 5.0, 2.35), (41.0, 3.95, 2.28), (43.0, 2.6, 2.22), (43.9, 1.2, 2.2)]
        cutters.append(link_obj(groove_sweep(P(apex, sd), sd, 4.0 * k), "mouth", coll))
    csg(base, [], objs)
    csg(base, cutters, [])
    # lower fangs poking up past the lip (added after the mouth groove)
    fangs = []
    for sd in (1, -1):
        for fx, fy, fh in ((37.2, 6.6, 5.8), (31.5, 7.95, 5.2)):
            fangs.append(link_obj(bm_hull(P([(fx - 0.9, fy - 0.6, 0.0), (fx + 0.9, fy - 0.6, 0.0),
                                              (fx, fy + 0.55, 0.0), (fx, fy - 0.1, fh)], sd)), "fang", coll))
    csg(base, [], fangs)
    sg.footprint = None
    sg.obj = clean_mesh(base)
    return base


def blob(cx, cy, rx, ry, z0, z1, n=7, top=0.62, rot=0.0, jitter=None):
    """faceted lump: n-gon ring on z0 and a smaller ring at z1"""
    pts = []
    for i in range(n):
        a = TAU * i / n + rot
        j = 1.0 if jitter is None else (0.92 + 0.16 * jitter.random())
        pts.append((cx + rx * math.cos(a) * j, cy + ry * math.sin(a) * j, z0))
    for i in range(n):
        a = TAU * (i + 0.5) / n + rot
        pts.append((cx + rx * top * math.cos(a), cy + ry * top * math.sin(a), z1))
    return pts


def notch_keepout(poly, jr, x0, side, extra=0.6):
    """clip a flank polygon (on `side`) so it stays outside the notch walls of
    the joint at (x0, 0) and clear of the socket top"""
    a = jr.w_t / 2 + SIDE + extra
    th = jr.theta
    w0 = rot2((0.0, side * a), -side * th)
    d = rot2((-1.0, 0.0), -side * th)
    n = (-d[1], d[0])
    probe = (-5.0 - w0[0], 0.0 - w0[1])
    if n[0] * probe[0] + n[1] * probe[1] > 0:
        n = (-n[0], -n[1])
    poly = clip_halfplane(poly, w0[0] + x0, w0[1], n[0], n[1])
    # tangent to the socket hole at 55 deg on this side (keeps the knob top free)
    rho = jr.r_n + jr.c + extra
    phi = math.radians(55.0)
    tx, ty = rho * math.cos(phi), side * rho * math.sin(phi)
    return clip_halfplane(poly, x0 + tx, ty, tx, ty)


def clip_convex(poly, clip):
    """poly (any simple polygon) intersected with a convex CCW polygon"""
    out = list(poly)
    clip = ccw(clip)
    n = len(clip)
    for i in range(n):
        out = clip_line_side(out, clip[i], clip[(i + 1) % n], keep_left=True)
        if len(out) < 3:
            return []
    return out


def ngon(cx, cy, r, n=40):
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n)) for i in range(n)]


def core_prisms(sg, fp, coll, x_rear=None):
    """Full-height cores that the joint needs: around the socket of the rear
    joint, and where the tongue of the front joint roots into the body.  The
    rest of the segment is a lower flank slab covered by sloped armour plates."""
    out = []
    H = (sg.front or sg.rear).H
    if sg.rear is not None and x_rear is not None:
        jr = sg.rear
        r_core = jr.r_e + jr.c + 1.7 * max(0.75, jr.sj)
        poly = clip_convex(fp, ngon(x_rear, 0.0, min(r_core, jr.hw - 0.01), 40))
        if len(poly) >= 3:
            out.append(link_obj(bm_prism(poly, 0.0, H), "core_r", coll))
    if sg.front is not None:
        jf = sg.front
        x0 = -(jf.hw + GAP)
        a = jf.w_t / 2 + 1.5 * sg.s
        rect = [(x0 + 1.5, -a), (x0 + 1.5, a), (x0 - 3.0 * sg.s, a), (x0 - 3.0 * sg.s, -a)]
        poly = clip_convex(fp, rect)
        if len(poly) >= 3:
            out.append(link_obj(bm_prism(poly, 0.0, H), "core_f", coll))
    return out


def scallop(a, b, toward, sag, n=6):
    """points strictly between a and b, bowed toward `toward` by sag*|ab|"""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = toward[0] - mx, toward[1] - my
    dl = math.hypot(dx, dy) or 1.0
    dx, dy = dx / dl, dy / dl
    out = []
    for i in range(1, n):
        t = i / n
        k = math.sin(math.pi * t) * sag * L
        out.append((lerp(a[0], b[0], t) + dx * k, lerp(a[1], b[1], t) + dy * k))
    return out


def wing_design(s):
    """2D layout of the (left) wing, printed flat.  x = along the body (leading
    edge toward +x), y = span, root chord on y = 0, tab at y < 0."""
    d = {}
    d["root"] = 7.0 * s
    d["W"] = (9.0 * s, 33.0 * s)                   # wrist
    d["tips"] = [(-3.0 * s, 70.0 * s), (-24.0 * s, 62.0 * s), (-40.0 * s, 46.0 * s), (-44.0 * s, 25.0 * s)]
    d["t_m"] = max(1.2, 1.3 * s)                   # membrane thickness
    d["t_b"] = max(2.2, 3.0 * s)                   # bone height
    d["t_tab"] = max(2.0, 2.2 * s)                 # tab thickness (slot = +0.3)
    d["tab_len"] = max(7.0, 9.0 * s)
    d["tab_x"] = 0.0
    return d


def wing_outline(d, s):
    r = d["root"]
    W = d["W"]
    t1, t2, t3, t4 = d["tips"]
    pts = [(-r, 0.0), (r, 0.0), (r + 2.5 * s, 10.0 * s), (W[0] + 1.6 * s, W[1] - 3.0 * s), (W[0] + 1.0 * s, W[1] + 3.0 * s),
           (W[0] - 2.0 * s, W[1] + 20.0 * s), t1]
    pts += scallop(t1, t2, W, 0.16)
    pts += [t2] + scallop(t2, t3, W, 0.18) + [t3] + scallop(t3, t4, W, 0.18) + [t4]
    pts += scallop(t4, (-r, 0.0), (0.0, 18.0 * s), 0.14)
    return ccw(dedupe(pts))


def bone_hull(a, b, wa, wb, za, zb, z0):
    """faceted bone ridge from a to b (2D), widths wa->wb, heights za->zb"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L, dx / L
    return [(a[0] + px * wa, a[1] + py * wa, z0), (a[0] - px * wa, a[1] - py * wa, z0),
            (b[0] + px * wb, b[1] + py * wb, z0), (b[0] - px * wb, b[1] - py * wb, z0),
            (a[0], a[1], za), (b[0], b[1], zb),
            (a[0] + px * wa * 0.35, a[1] + py * wa * 0.35, za * 0.9),
            (b[0] - px * wb * 0.35, b[1] - py * wb * 0.35, zb * 0.9)]


def build_wing(plan, side, coll, tab_depth):
    """flat printable wing (side=+1 left, -1 right = mirror image)"""
    s = plan.s
    d = wing_design(s)
    mirror = 1.0 if side > 0 else -1.0

    def mx(pts2):
        return [(mirror * x, y) for x, y in pts2]

    def mx3(pts3):
        return [(mirror * x, y, z) for x, y, z in pts3]

    outline = ccw(mx(wing_outline(d, s)))
    ob = link_obj(bm_prism(outline, 0.0, d["t_m"]), "wing_L" if side > 0 else "wing_R", coll)
    W = d["W"]
    root_c = (0.0, 1.0 * s)
    tb, tm = d["t_b"], d["t_m"]
    # bones start on the bed so nothing hangs past the membrane edge
    bones = [bone_hull(root_c, W, 2.6 * s, 2.0 * s, tb, tb * 0.95, 0.0)]
    for i, tp in enumerate(d["tips"]):
        w0 = (1.7 - 0.15 * i) * s
        bones.append(bone_hull(W, tp, w0, 0.7 * s, tb * 0.92, tb * 0.55, 0.0))
    # leading edge spar from root to wrist
    bones.append(bone_hull((d["root"] * 0.8, 1.0 * s), (W[0] + 0.6 * s, W[1] - 2.0 * s), 1.5 * s, 1.6 * s,
                           tb * 0.8, tb * 0.9, 0.0))
    # wrist claw (flat on the bed, pointing forward)
    claw = [(W[0] - 1.5 * s, W[1] - 1.2 * s, 0.0), (W[0] - 1.5 * s, W[1] + 1.8 * s, 0.0),
            (W[0] + 7.0 * s, W[1] + 3.2 * s, 0.0), (W[0], W[1], tb * 1.05), (W[0] + 4.5 * s, W[1] + 2.2 * s, tb * 0.5)]
    adders = [link_obj(bm_hull(mx3(b)), "bone", coll) for b in bones]
    adders.append(link_obj(bm_hull(mx3(claw)), "claw", coll))
    tl = d["tab_len"]
    tx = mirror * d["tab_x"]
    tab = [(tx - tl / 2, -tab_depth), (tx + tl / 2, -tab_depth), (tx + tl / 2, 1.0), (tx - tl / 2, 1.0)]
    adders.append(link_obj(bm_prism(tab, 0.0, d["t_tab"]), "tab", coll))
    csg(ob, [], adders)
    return clean_mesh(ob), d


def wing_frame(side, tilt_deg=45.0, sweep_deg=0.0):
    """rotation taking wing-local axes to the mounted pose (shoulder frame)"""
    t = math.radians(tilt_deg)
    ydir = Vector((0.0, side * math.sin(t), math.cos(t)))
    xdir = Vector((1.0, 0.0, 0.0)) if side > 0 else Vector((-1.0, 0.0, 0.0))
    # sweep the wing back a little around its root-normal
    zdir = xdir.cross(ydir).normalized()
    R = Matrix((xdir, ydir, zdir)).transposed()
    sw = Matrix.Rotation(math.radians(sweep_deg) * (1 if side > 0 else -1), 3, zdir) if sweep_deg else Matrix.Identity(3)
    return (sw @ R).to_4x4(), xdir, ydir, zdir


def slot_and_mount(sg, side, bvh_before, fit=0.30):
    """Find where a wing plugs into the shoulder: returns (cutter points, mount
    matrix in shoulder frame, tab depth)."""
    s = sg.s
    d = wing_design(s)
    R4, xdir, ydir, zdir = wing_frame(side, sweep_deg=0.0)
    x_m = -0.65 * sg.L
    y_b = side * 3.2 * s
    # top surface along the slot axis (max over the slot length)
    best = None
    for dx in (-d["tab_len"] / 2, 0.0, d["tab_len"] / 2):
        o = Vector((x_m + dx, y_b, 0.0)) + ydir * 40.0
        hit = bvh_before.ray_cast(o, -ydir)
        if hit[0] is not None:
            dist = 40.0 - hit[3]
            best = dist if best is None else max(best, dist)
    if best is None:
        return None
    base = Vector((x_m, y_b, 0.0))
    M = base + ydir * best                     # root line at the surface
    depth = min(max(3.0, 4.0 * s), best - (sg.z_edge * 0.35))
    ls = d["tab_len"] + fit
    ws = d["t_tab"] + fit
    pts = []
    for ex in (-ls / 2, ls / 2):
        for en in (-ws / 2, ws / 2):
            for ey in (-depth, 15.0):
                p = M + Vector((ex, 0, 0)) + zdir * en + ydir * ey
                pts.append(tuple(p))
    mount = Matrix.Translation(M - zdir * (d["t_tab"] / 2)) @ R4
    return pts, mount, depth - 0.4


# =============================================================================
# 7. LAYOUT ON THE BED
# =============================================================================

def chain_lengths(plan):
    return [sg.L for sg in plan.segs[1:-1]]


def path_points(kind, total, params):
    """Return a dense polyline (list of (x,y)) of arc length >= total."""
    pts = []
    ds = 0.5
    n = int(total / ds) + 200
    if kind == "straight":
        return [(-i * ds, 0.0) for i in range(n)]
    if kind == "wave":
        A, lam = params
        x = 0.0
        y = 0.0
        pts = [(0.0, 0.0)]
        s = 0.0
        while len(pts) < n:
            dy = A * TAU / lam * math.cos(TAU * s / lam)
            dx = -1.0
            l = math.hypot(dx, dy)
            x += dx / l * ds
            y += dy / l * ds
            s += ds / l
            pts.append((x, y))
        return pts
    if kind == "coil":
        r0, pitch = params
        b = pitch / TAU
        phi = 0.0
        pts = []
        for _ in range(n):
            r = r0 - b * phi
            if r < 5:
                break
            pts.append((r * math.cos(-phi), r * math.sin(-phi)))
            phi += ds / max(r, 1.0)
        return pts
    raise ValueError(kind)


def place_on_path(plan, poly):
    """Put joints on the polyline at the right chord distances."""
    Ls = chain_lengths(plan)
    joints = plan.joints
    idx = 0
    P = poly[0]
    joints[0].pos = P
    for k, L in enumerate(Ls):
        # walk until chord distance >= L
        j = idx
        while j < len(poly) - 1 and math.dist(poly[j + 1], P) < L:
            j += 1
        if j >= len(poly) - 1:
            return False
        a, b = poly[j], poly[j + 1]
        # solve |a + t(b-a) - P| = L
        dx, dy = b[0] - a[0], b[1] - a[1]
        fx, fy = a[0] - P[0], a[1] - P[1]
        A = dx * dx + dy * dy
        B = 2 * (fx * dx + fy * dy)
        C = fx * fx + fy * fy - L * L
        t = (-B + math.sqrt(max(0.0, B * B - 4 * A * C))) / (2 * A)
        P = (a[0] + dx * t, a[1] + dy * t)
        joints[k + 1].pos = P
        idx = j
    # tail tip direction from the path after the last joint
    j = idx
    while j < len(poly) - 1 and math.dist(poly[j + 1], P) < plan.tip_len * 0.6:
        j += 1
    plan.tip_dir_pt = poly[min(j + 1, len(poly) - 1)]
    plan.head_dir_pt = (2 * poly[0][0] - poly[4][0], 2 * poly[0][1] - poly[4][1])
    return True


def assign_frames(plan):
    segs = plan.segs
    J = plan.joints
    # head: origin at joint 1, +x away from the body
    h = segs[0]
    p1 = J[0].pos
    hd = plan.head_dir_pt
    h.origin = p1
    h.heading = math.atan2(hd[1] - p1[1], hd[0] - p1[0])
    for sg in segs[1:-1]:
        a, b = sg.front.pos, sg.rear.pos
        sg.origin = a
        sg.heading = math.atan2(a[1] - b[1], a[0] - b[0])
    t = segs[-1]
    t.origin = t.front.pos
    tp = plan.tip_dir_pt
    t.heading = math.atan2(t.origin[1] - tp[1], t.origin[0] - tp[0])
    # bend at each joint = heading(front seg) - heading(rear seg)
    for i, j in enumerate(J):
        f, r = segs[i], segs[i + 1]
        d = f.heading - r.heading
        j.bend = (d + math.pi) % TAU - math.pi


def layout_extent(plan):
    """rough 2D extent of each part: circles (center, radius) per segment"""
    circles = []
    s = plan.s
    for sg in plan.segs:
        c, hdg = sg.origin, sg.heading
        u = (math.cos(hdg), math.sin(hdg))
        if sg.kind == "head":
            for t, r in ((0.0, sg.rear.hw), (10 * s, 18.5 * s), (26 * s, 11 * s), (38 * s, 7 * s)):
                circles.append((sg.idx, (c[0] + u[0] * t, c[1] + u[1] * t), r))
        elif sg.kind == "tip":
            for t, r in ((-4 * s, sg.front.hw), (-plan.tip_len * 0.5, 5 * s), (-plan.tip_len + 6 * s, 8 * s)):
                circles.append((sg.idx, (c[0] + u[0] * t, c[1] + u[1] * t), r))
        else:
            r = max(sg.front.hw, sg.rear.hw)
            if sg.kind in ("shoulder", "hip") and plan.cfg["legs"]:
                circles.append((sg.idx, (c[0] - u[0] * sg.L * 0.72, c[1] - u[1] * sg.L * 0.72), r + 15 * s))
            circles.append((sg.idx, (c[0] - u[0] * sg.L * 0.5, c[1] - u[1] * sg.L * 0.5), max(r, sg.L * 0.55)))
    return circles


def layout_score(plan, bed):
    circles = layout_extent(plan)
    xs0 = min(c[1][0] - c[2] for c in circles)
    xs1 = max(c[1][0] + c[2] for c in circles)
    ys0 = min(c[1][1] - c[2] for c in circles)
    ys1 = max(c[1][1] + c[2] for c in circles)
    # non adjacent overlap
    worst = 0.0
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            a, b = circles[i], circles[j]
            if abs(a[0] - b[0]) < 3:
                continue
            d = math.dist(a[1], b[1]) - a[2] - b[2]
            worst = min(worst, d)
    return (xs0, xs1, ys0, ys1), worst


def auto_layout(plan):
    cfg = plan.cfg
    bed = cfg["bed"]
    margin = 6.0
    total = sum(chain_lengths(plan)) + plan.tip_len + 60
    candidates = []
    kinds = [cfg["layout"]] if cfg["layout"] != "auto" else ["coil", "wave", "straight"]
    for kind in kinds:
        if kind == "straight":
            params_list = [None]
        elif kind == "wave":
            params_list = [(A, lam) for A in (10, 16, 22, 30) for lam in (140, 180, 230)]
        else:
            params_list = [(r0, p) for r0 in (48, 55, 62, 68, 74, 80, 86, 92, 100, 110, 120)
                           for p in (40, 48, 56, 64)]
        for params in params_list:
            poly = path_points(kind, total, params)
            if not place_on_path(plan, poly):
                continue
            assign_frames(plan)
            bends_ok = all(abs(j.bend) <= j.theta - math.radians(6) for j in plan.joints)
            if not bends_ok:
                continue
            best_rot = None
            for ang in range(0, 180, 5):
                a = math.radians(ang)
                rot_c = [(sid, rot2(c, a), r) for sid, c, r in layout_extent(plan)]
                w = max(c[0] + r for _, c, r in rot_c) - min(c[0] - r for _, c, r in rot_c)
                h = max(c[1] + r for _, c, r in rot_c) - min(c[1] - r for _, c, r in rot_c)
                fit = max(w / (bed[0] - 2 * margin), h / (bed[1] - 2 * margin))
                if best_rot is None or fit < best_rot[0]:
                    best_rot = (fit, a)
            ext, worst = layout_score(plan, bed)
            if worst < -1e-6:
                continue
            maxbend = max(abs(j.bend) for j in plan.joints)
            pref = {"coil": 0.0, "wave": 0.02, "straight": 0.04}[kind]
            candidates.append((best_rot[0] > 1.0, maxbend + 0.3 * best_rot[0] + pref, kind, params, best_rot[1]))
    if not candidates:
        raise RuntimeError("No layout found - try a bigger bed or fewer segments")
    candidates.sort()
    _, _, kind, params, ang = candidates[0]
    poly = path_points(kind, total, params)
    place_on_path(plan, poly)
    # rotate + center on bed
    for j in plan.joints:
        j.pos = rot2(j.pos, ang)
    plan.tip_dir_pt = rot2(plan.tip_dir_pt, ang)
    plan.head_dir_pt = rot2(plan.head_dir_pt, ang)
    assign_frames(plan)
    plan.layout = (kind, params, math.degrees(ang), candidates[0][0])
    return plan


def recenter(plan, objs, bed):
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    off = Vector((bed[0] / 2 - (mn.x + mx.x) / 2, bed[1] / 2 - (mn.y + mx.y) / 2, -mn.z))
    for o in objs:
        o.matrix_world = Matrix.Translation(off) @ o.matrix_world
    for j in plan.joints:
        j.pos = (j.pos[0] + off.x, j.pos[1] + off.y)
    for sg in plan.segs:
        sg.origin = (sg.origin[0] + off.x, sg.origin[1] + off.y)
    return (mn + off, mx + off)


# =============================================================================
# 8. BUILD EVERYTHING
# =============================================================================

def get_collection(name="Gemscale Dragon"):
    old = bpy.data.collections.get(name)
    if old:
        for o in list(old.objects):
            me = o.data
            bpy.data.objects.remove(o)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(old)
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def hull2d(points):
    pts = sorted(set((round(p[0], 4), round(p[1], 4)) for p in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _axes(poly):
    import numpy as np
    P = np.asarray(poly, dtype=float)
    E = np.roll(P, -1, axis=0) - P
    N = np.stack([E[:, 1], -E[:, 0]], axis=1)
    L = np.linalg.norm(N, axis=1)
    return N[L > 1e-9] / L[L > 1e-9][:, None]


def sat_separated(A, B, margin, axA=None, axB=None):
    """True if convex polygons A and B are at least `margin` apart (numpy SAT)."""
    import numpy as np
    Pa = np.asarray(A, dtype=float)
    Pb = np.asarray(B, dtype=float)
    ax = np.vstack([axA if axA is not None else _axes(A), axB if axB is not None else _axes(B)])
    pa = Pa @ ax.T
    pb = Pb @ ax.T
    return bool(np.any((pa.max(0) + margin <= pb.min(0)) | (pb.max(0) + margin <= pa.min(0))))


def obj_hull2d(ob, mat=None):
    m = (mat or ob.matrix_world)
    return hull2d([(m @ v.co)[:2] for v in ob.data.vertices])


def place_wings(plan, wings, bed, margin=2.5):
    """Find free spots for the flat wings on the build plate (inside the curl)."""
    obst = [obj_hull2d(sg.obj) for sg in plan.segs]
    placed = []
    cx, cy = bed[0] / 2, bed[1] / 2
    for w in wings:
        local = hull2d([v.co[:2] for v in w.data.vertices])
        lc = (sum(p[0] for p in local) / len(local), sum(p[1] for p in local) / len(local))
        oax = [_axes(o) for o in obst]
        obox = [(min(p[0] for p in o), max(p[0] for p in o), min(p[1] for p in o), max(p[1] for p in o)) for o in obst]
        cands = []
        for ang in range(0, 360, 15):
            a = math.radians(ang)
            rl = [rot2(p, a) for p in local]
            rc = rot2(lc, a)
            x0 = min(p[0] for p in rl)
            x1 = max(p[0] for p in rl)
            y0 = min(p[1] for p in rl)
            y1 = max(p[1] for p in rl)
            step = 3.0
            tx = margin - x0
            while tx + x1 <= bed[0] - margin:
                ty = margin - y0
                while ty + y1 <= bed[1] - margin:
                    cands.append((math.hypot(rc[0] + tx - cx, rc[1] + ty - cy), ang, tx, ty))
                    ty += step
                tx += step
        cands.sort()
        rot_cache = {}
        best = None
        last_hit = 0
        for score, ang, tx, ty in cands:
            if ang not in rot_cache:
                rl = [rot2(q, math.radians(ang)) for q in local]
                rot_cache[ang] = (rl, _axes(rl), (min(p[0] for p in rl), max(p[0] for p in rl),
                                                  min(p[1] for p in rl), max(p[1] for p in rl)))
            rl, rax, (bx0, bx1, by0, by1) = rot_cache[ang]
            cand = [(p[0] + tx, p[1] + ty) for p in rl]
            ok = True
            order = [last_hit] + [i for i in range(len(obst)) if i != last_hit]
            for i in order:
                ox0, ox1, oy0, oy1 = obox[i]
                if bx1 + tx + margin <= ox0 or ox1 + margin <= bx0 + tx or \
                   by1 + ty + margin <= oy0 or oy1 + margin <= by0 + ty:
                    continue
                if not sat_separated(cand, obst[i], margin, rax, oax[i]):
                    ok = False
                    last_hit = i
                    break
            if ok:
                best = (score, math.radians(ang), tx, ty, cand)
                break
        if best is None:
            return False
        _, a, tx, ty, cand = best
        w.matrix_world = Matrix.Translation((tx, ty, 0.0)) @ Matrix.Rotation(a, 4, "Z")
        obst.append(cand)
        placed.append(w)
    return True


def wing_segment_index(plan):
    for i, sg in enumerate(plan.segs):
        if sg.kind == "shoulder":
            return i
    return min(len(plan.segs) - 2, plan.cfg["neck"] + 1)


def generate(user_settings=None, verbose=True):
    t0 = time.time()
    cfg = resolve_settings(user_settings)
    plan = plan_dragon(cfg)
    for j in plan.joints:
        if not j.wall_ok():
            raise RuntimeError(f"joint {j.idx}: body too thin for the knob - increase scale")
    auto_layout(plan)
    rng = random.Random(cfg["seed"])
    coll = get_collection()
    plan.wings, plan.wing_mounts, plan.wing_print_mats = [], [], []
    plan.wing_seg = wing_segment_index(plan) if cfg["wings"] else None
    plan.wings_separate = False
    legacy = boolean_solver() != "MANIFOLD"
    if legacy:
        print("[gemscale] note: this Blender has no Manifold boolean solver (needs 4.5+); "
              "using EXACT - slower, and parts are re-built if a boolean glitches")
    for i, sg in enumerate(plan.segs):
        sg.want_wings = (i == plan.wing_seg)
        for attempt in range(4 if legacy else 1):
            r = rng if attempt == 0 else random.Random(cfg["seed"] * 7919 + i * 31 + attempt)
            if sg.kind == "head":
                build_head(sg, coll, r, cfg, plan)
            elif sg.kind == "tip":
                build_tip(sg, coll, r, cfg, plan)
            else:
                build_body(sg, coll, r, cfg)
            if not legacy or attempt == 3 or _obj_closed(sg.obj):
                break
            me = sg.obj.data
            bpy.data.objects.remove(sg.obj)
            bpy.data.meshes.remove(me)
        sg.obj.matrix_world = Matrix.Translation((sg.origin[0], sg.origin[1], 0)) @ Matrix.Rotation(sg.heading, 4, "Z")
    objs = [sg.obj for sg in plan.segs]
    plan.bbox = recenter(plan, objs, cfg["bed"])
    for sg in plan.segs:
        sg.print_matrix = sg.obj.matrix_world.copy()
    # snap-in wings
    if plan.wing_seg is not None and getattr(plan.segs[plan.wing_seg], "wing_info", None):
        sg = plan.segs[plan.wing_seg]
        for side, (mount, tab_depth) in zip((1, -1), sg.wing_info):
            w, _ = build_wing(plan, side, coll, tab_depth)
            plan.wings.append(w)
            plan.wing_mounts.append(mount)
        if not place_wings(plan, plan.wings, cfg["bed"]):
            # no room next to the dragon: lay them side by side for a second plate
            plan.wings_separate = True
            x = 10.0
            for w in plan.wings:
                w.matrix_world = Matrix.Identity(4)
                mn = min(v.co.x for v in w.data.vertices)
                mxx = max(v.co.x for v in w.data.vertices)
                mny = min(v.co.y for v in w.data.vertices)
                w.matrix_world = Matrix.Translation((x - mn, 10.0 - mny, 0.0))
                x += (mxx - mn) + 8.0
        plan.wing_print_mats = [w.matrix_world.copy() for w in plan.wings]
    plan.z_split = sg_z_split(plan)
    plan.collection = coll
    plan.build_time = time.time() - t0
    if verbose:
        k, p, a, _ = plan.layout
        print(f"[gemscale] built {len(objs)} parts + {len(plan.wings)} wings in {plan.build_time:.1f}s  "
              f"layout={k} {p} rot={a:.0f}")
    return plan


def sg_z_split(plan):
    """height of the suggested filament change (plates, fins, horns get colour 2)"""
    return rup(plan.segs[1].z_edge + 1.2 * plan.s)


def export_dir(plan):
    """'//' means next to the saved .blend; for an unsaved file use the home folder
    (Blender's working directory is often read-only, e.g. Program Files)."""
    out = plan.cfg["out"]
    if out.startswith("//"):
        if bpy.data.filepath:
            base = os.path.dirname(bpy.data.filepath)
        elif bpy.app.background:
            base = os.getcwd()
        else:
            base = os.path.expanduser("~")
        out = os.path.join(base, out[2:])
    out = os.path.abspath(bpy.path.abspath(out))
    os.makedirs(out, exist_ok=True)
    return out


# =============================================================================
# 9. CHECKS
# =============================================================================

def _tri_bvh(ob, extra=None):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform((extra or Matrix()) @ ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tree = BVHTree.FromBMesh(bm)
    samples = [v.co.copy() for v in bm.verts] + [f.calc_center_median() for f in bm.faces]
    bm.free()
    return tree, samples


def _min_dist(ta, sa, tb, sb, cap=5.0):
    best = cap
    for p in sa:
        r = tb.find_nearest(p, best)
        if r[0] is not None and r[3] < best:
            best = r[3]
    for p in sb:
        r = ta.find_nearest(p, best)
        if r[0] is not None and r[3] < best:
            best = r[3]
    return best


def check_dragon(plan, sweep_step_deg=4.0, verbose=True):
    segs = plan.segs
    rep = {"parts": len(segs), "nonmanifold": [], "overlaps": [], "min_gap": 99.0,
           "sweep_fail": [], "far_overlaps": [], "volume_cm3": 0.0}
    for sg in list(segs) + [type("W", (), {"obj": w})() for w in plan.wings]:
        bm = bmesh.new()
        bm.from_mesh(sg.obj.data)
        bad = sum(1 for e in bm.edges if not e.is_manifold) + sum(1 for e in bm.edges if e.is_boundary)
        rep["volume_cm3"] += abs(bm.calc_volume()) / 1000.0
        bm.free()
        if bad:
            rep["nonmanifold"].append((sg.obj.name, bad))
    trees = [_tri_bvh(sg.obj) for sg in segs]
    for i in range(1, len(segs)):
        (ta, sa), (tb, sb) = trees[i - 1], trees[i]
        if ta.overlap(tb):
            rep["overlaps"].append((segs[i - 1].obj.name, segs[i].obj.name))
        rep["min_gap"] = min(rep["min_gap"], _min_dist(ta, sa, tb, sb))
    # non-adjacent: must not touch at all (gap >= 0.8 mm)
    for i in range(len(segs)):
        for k in range(i + 2, len(segs)):
            (ta, sa), (tb, sb) = trees[i], trees[k]
            if ta.overlap(tb) or _min_dist(ta, sa, tb, sb, 0.8) < 0.8:
                rep["far_overlaps"].append((segs[i].obj.name, segs[k].obj.name))
    # wings lying on the plate must not touch anything
    if plan.wings and not plan.wings_separate:
        wt = [_tri_bvh(w) for w in plan.wings]
        others = trees + wt
        for a, (ta, sa) in enumerate(wt):
            for b, (tb, sb) in enumerate(others):
                if b == len(trees) + a:
                    continue
                if ta.overlap(tb) or _min_dist(ta, sa, tb, sb, 1.0) < 1.0:
                    rep["far_overlaps"].append((plan.wings[a].name, "part %d" % b))
    # joint sweep: rotate the rear part about the joint axis through its range
    for i, j in enumerate(plan.joints):
        F, R = segs[i], segs[i + 1]
        tf, _ = trees[i]
        P = Vector((j.pos[0], j.pos[1], 0.0))
        lo = -j.theta + math.radians(1.0)
        hi = j.theta - math.radians(1.0)
        n = max(2, int(math.degrees(hi - lo) / sweep_step_deg))
        for m in range(n + 1):
            rel = lo + (hi - lo) * m / n            # target bend, relative to straight
            rho = j.bend - rel                      # rotation of R from its printed pose
            M = Matrix.Translation(P) @ Matrix.Rotation(rho, 4, "Z") @ Matrix.Translation(-P)
            tr, _ = _tri_bvh(R.obj, M)
            if tf.overlap(tr):
                rep["sweep_fail"].append((j.idx, round(math.degrees(rel), 1)))
                break
    # printability: anything facing down steeper than 45 deg that is not on the
    # bed and not one of the designed tongue bridges is reported as an overhang
    rep["overhang_mm2"] = 0.0
    rep["overhangs"] = []
    rep["bridge_mm2"] = 0.0
    rep["shells"] = []
    zb = {round(j.z_n, 3) for j in plan.joints}
    for sg in list(segs) + [type("W", (), {"obj": w})() for w in plan.wings]:
        bm = bmesh.new()
        bm.from_mesh(sg.obj.data)
        bm.transform(sg.obj.matrix_world)
        bm.normal_update()
        for f in bm.faces:
            nz = f.normal.z
            if nz > -0.7072:
                continue
            zc = f.calc_center_median().z
            if zc < 0.02:
                continue
            a = f.calc_area()
            if nz < -0.999 and any(abs(zc - z) < 0.01 for z in zb):
                rep["bridge_mm2"] += a
                continue
            rep["overhang_mm2"] += a
            if a > 0.05:
                c = f.calc_center_median()
                rep["overhangs"].append((sg.obj.name, round(a, 2), round(math.degrees(math.acos(max(-1, min(1, -nz)))), 1),
                                         tuple(round(v, 1) for v in (sg.obj.matrix_world.inverted() @ c))))
        # connected shells per part (must be exactly 1)
        seen = set()
        shells = 0
        for v in bm.verts:
            if v.index in seen:
                continue
            shells += 1
            stack = [v]
            seen.add(v.index)
            while stack:
                w = stack.pop()
                for e in w.link_edges:
                    o = e.other_vert(w)
                    if o.index not in seen:
                        seen.add(o.index)
                        stack.append(o)
        if shells != 1:
            rep["shells"].append((sg.obj.name, shells))
        bm.free()
    rep["overhangs"].sort(key=lambda t: -t[1])
    rep["ok"] = not (rep["nonmanifold"] or rep["overlaps"] or rep["far_overlaps"] or rep["sweep_fail"]
                     or rep["shells"] or rep["overhang_mm2"] > 2.0)
    if verbose:
        short = {k: (v[:8] if isinstance(v, list) else v) for k, v in rep.items()}
        print("[gemscale] check:", short)
    return rep


# =============================================================================
# 10. EXPORT (version independent STL + 3MF writers)
# =============================================================================

def _triangles(objs):
    tris = []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        mw = ob.matrix_world
        co = [mw @ v.co for v in me.vertices]
        for lt in me.loop_triangles:
            a, b, c = lt.vertices
            tris.append((co[a], co[b], co[c]))
    return tris


def write_stl(objs, path, name="gemscale_dragon"):
    import struct
    tris = _triangles(objs)
    with open(path, "wb") as f:
        hdr = f"{name} - Gemscale Flexi Dragon (mm)".encode()[:80]
        f.write(hdr + b" " * (80 - len(hdr)))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z, 0))
    return len(tris)


def write_3mf(objs, path, title="Gemscale Flexi Dragon"):
    # one object containing all (separate) shells, so slicers keep the assembly intact
    verts, index, tris = [], {}, []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        mw = ob.matrix_world
        base = len(verts)
        for v in me.vertices:
            w = mw @ v.co
            verts.append((w.x, w.y, w.z))
        for lt in me.loop_triangles:
            tris.append(tuple(base + i for i in lt.vertices))
    vx = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    tx = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    model = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<metadata name="Title">{title}</metadata>
<metadata name="Designer">Gemscale generator</metadata>
<metadata name="Application">Blender {bpy.app.version_string} + gemscale_dragon.py</metadata>
<resources>
<object id="1" type="model" name="{title}">
<mesh>
<vertices>
{vx}
</vertices>
<triangles>
{tx}
</triangles>
</mesh>
</object>
</resources>
<build>
<item objectid="1"/>
</build>
</model>
"""
    ct = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
    return len(tris)


def export_all(plan, out_dir=None, report=None):
    cfg = plan.cfg
    out = out_dir or export_dir(plan)
    os.makedirs(out, exist_ok=True)
    stem = f"GemscaleDragon_{cfg['preset']}_seed{cfg['seed']}"
    if abs(cfg["clearance"] - 0.35) > 1e-4:
        stem += f"_clearance{cfg['clearance']:.2f}".replace(".", "p")
    objs = [sg.obj for sg in plan.segs]
    if plan.wings and not plan.wings_separate:
        objs += plan.wings
    n = write_stl(objs, os.path.join(out, stem + ".stl"), stem)
    write_3mf(objs, os.path.join(out, stem + ".3mf"), f"Gemscale Flexi Dragon ({cfg['preset']})")
    if plan.wings:
        # extra files: dragon only, and wings only (e.g. to print the wings in another colour)
        write_stl([sg.obj for sg in plan.segs], os.path.join(out, stem + "_body_only.stl"), stem + "_body")
        mats = [w.matrix_world.copy() for w in plan.wings]
        x = 5.0
        for w in plan.wings:
            w.matrix_world = Matrix.Identity(4)
            xs = [v.co.x for v in w.data.vertices]
            ys = [v.co.y for v in w.data.vertices]
            w.matrix_world = Matrix.Translation((x - min(xs), 5.0 - min(ys), 0.0))
            x += (max(xs) - min(xs)) + 6.0
        write_stl(plan.wings, os.path.join(out, stem + "_wings_only.stl"), stem + "_wings")
        write_3mf(plan.wings, os.path.join(out, stem + "_wings_only.3mf"), "Gemscale Flexi Dragon wings")
        for w, m in zip(plan.wings, mats):
            w.matrix_world = m
    txt = summary_text(plan, report)
    with open(os.path.join(out, stem + "_report.txt"), "w") as f:
        f.write(txt)
    print(f"[gemscale] exported {n} triangles -> {out}/{stem}.stl/.3mf")
    return out, stem


def summary_text(plan, report=None):
    cfg = plan.cfg
    on_plate = [sg.obj for sg in plan.segs] + ([] if plan.wings_separate else list(plan.wings))
    mn, mx = _bbox_world(on_plate)
    H = plan.H
    lines = [
        "GEMSCALE FLEXI DRAGON - build report",
        f"preset={cfg['preset']} scale={cfg['scale']} seed={cfg['seed']} clearance={cfg['clearance']} mm",
        f"parts (segments incl. head & tail): {len(plan.segs)}   joints: {len(plan.joints)}",
        f"footprint on bed: {mx.x - mn.x:.1f} x {mx.y - mn.y:.1f} mm, height {mx.z:.1f} mm (bed {cfg['bed'][0]}x{cfg['bed'][1]})",
        f"length when stretched out: ~{sum(chain_lengths(plan)) + plan.head_len + plan.joints[0].hw + plan.tip_len:.0f} mm",
        f"layout: {plan.layout[0]}",
        "",
        "PRINT SETTINGS (Bambu Studio / Orca)",
        "  layer height 0.20 mm (first layer 0.20)   <- joint gaps are sized for this",
        "  supports OFF, brim OFF (or 3 mm outer brim only), 2 walls, 15% gyroid/grid infill",
        "  PLA or PLA silk; keep the default 'elephant foot compensation' (0.15)",
        f"  two-tone trick: filament change at Z = {plan.z_split:.1f} mm -> plates, fins & horns get the 2nd colour",
        ("  wings: printed on the same plate - press the tabs into the two shoulder slots (drop of glue if loose)"
         if plan.wings and not plan.wings_separate else
         "  wings: did not fit next to the dragon - print *_wings_only, then press the tabs into the shoulder slots"
         if plan.wings else "  wings: off"),
        "  after printing: flex every joint gently side to side to break it free",
    ]
    if report:
        lines += ["", "AUTOMATED CHECKS",
                  f"  manifold/watertight parts: {len(all_objects(plan)) - len(report['nonmanifold'])}/{len(all_objects(plan))}",
                  f"  intersecting neighbours: {len(report['overlaps'])}",
                  f"  smallest gap between neighbours: {report['min_gap']:.2f} mm",
                  f"  non-neighbour contacts: {len(report['far_overlaps'])}",
                  f"  joint sweep collisions (+-{math.degrees(plan.joints[1].theta):.0f} deg): {len(report['sweep_fail'])}",
                  f"  solid volume: {report['volume_cm3']:.1f} cm3 (~{report['volume_cm3'] * 1.24 * 0.75:.0f} g PLA at 2 walls/15%)",
                  f"  RESULT: {'PASS' if report['ok'] else 'CHECK FAILED - see above'}"]
    return "\n".join(lines) + "\n"


# =============================================================================
# 11. POSING + STUDIO RENDERS (MakerWorld cover images, 4:3)
# =============================================================================

COLOR_SCHEMES = {
    # two-tone schemes = what you get with ONE filament change at the reported Z
    # backdrop = (colour under the dragon, colour far away) for the render studio
    "obsidian": dict(base=(0.018, 0.018, 0.022), accent=(0.95, 0.70, 0.28), silk=0.35,
                     backdrop=((0.36, 0.43, 0.55), (0.010, 0.014, 0.024))),
    "emerald":  dict(base=(0.015, 0.28, 0.17), accent=(0.93, 0.66, 0.22), silk=0.30,
                     backdrop=((0.30, 0.24, 0.20), (0.020, 0.014, 0.012))),
    "ruby":     dict(base=(0.30, 0.012, 0.03), accent=(0.95, 0.80, 0.55), silk=0.30,
                     backdrop=((0.22, 0.30, 0.36), (0.008, 0.014, 0.020))),
    # gradient schemes = what "silk dual / rainbow" filaments look like
    "sunset":   dict(grad=[(0.0, (1.0, 0.50, 0.06)), (0.5, (0.92, 0.12, 0.20)), (1.0, (0.45, 0.06, 0.55))], silk=0.45,
                     backdrop=((0.20, 0.22, 0.40), (0.010, 0.010, 0.028))),
    "frost":    dict(grad=[(0.0, (0.80, 0.92, 1.0)), (0.6, (0.35, 0.62, 0.98)), (1.0, (0.20, 0.30, 0.85))], silk=0.45,
                     backdrop=((0.12, 0.16, 0.30), (0.006, 0.008, 0.020))),
    "rainbow":  dict(grad=[(0.0, (0.95, 0.10, 0.12)), (0.2, (1.0, 0.45, 0.02)), (0.4, (0.98, 0.85, 0.05)),
                           (0.6, (0.10, 0.75, 0.25)), (0.8, (0.10, 0.35, 0.95)), (1.0, (0.50, 0.12, 0.85))], silk=0.5,
                     backdrop=((0.24, 0.24, 0.27), (0.010, 0.010, 0.012))),
}


def _grad(stops, t):
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            return tuple(lerp(a, b, u) for a, b in zip(c0, c1))
    return stops[-1][1]


def make_material(scheme_name, z_split, z_max):
    sch = COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["emerald"])
    name = f"Gemscale_{scheme_name}"
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    silk = sch.get("silk", 0.3)
    bsdf.inputs["Metallic"].default_value = silk * 0.7
    bsdf.inputs["Roughness"].default_value = 0.46 - silk * 0.35
    for nm_, val in (("Coat Weight", 0.30), ("Coat Roughness", 0.12), ("Clearcoat", 0.30), ("Clearcoat Roughness", 0.12)):
        if nm_ in bsdf.inputs:          # glossy sheen (names differ between Blender versions)
            bsdf.inputs[nm_].default_value = val
    if "grad" in sch:
        oi = nodes.new("ShaderNodeObjectInfo")
        links.new(oi.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        geo = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        div = nodes.new("ShaderNodeMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = max(1.0, z_max)
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        e = ramp.color_ramp.elements
        e[0].position = 0.0
        e[0].color = sch["base"] + (1.0,)
        e[1].position = min(0.999, z_split / max(1.0, z_max))
        e[1].color = sch["accent"] + (1.0,)
        links.new(geo.outputs["Object"], sep.inputs[0])       # printed height, not world height
        links.new(sep.outputs["Z"], div.inputs[0])
        links.new(div.outputs[0], ramp.inputs[0])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    # 0.2 mm layer lines, so renders read like real prints
    try:
        wave = nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "Z"
        wave.inputs["Scale"].default_value = math.pi / 2.0
        wave.inputs["Distortion"].default_value = 0.0
        tc = nodes.new("ShaderNodeTexCoord")
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.05
        bump.inputs["Distance"].default_value = 0.02
        links.new(tc.outputs["Object"], wave.inputs["Vector"])
        links.new(wave.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    except Exception:
        pass
    return m, sch


def apply_colors(plan, scheme_name):
    z_split = plan.z_split
    z_max = max(o.dimensions.z for o in all_objects(plan)) + 1.0
    mat, sch = make_material(scheme_name, z_split, z_max)
    for o in all_objects(plan):
        o.data.materials.clear()
        o.data.materials.append(mat)
        for p in o.data.polygons:
            p.use_smooth = False
    if "grad" in sch:
        for sg in plan.segs:
            c = _grad(sch["grad"], sg.color_t)
            sg.obj.color = c + (1.0,)
        for w in plan.wings:
            c = _grad(sch["grad"], plan.segs[plan.wing_seg].color_t)
            w.color = c + (1.0,)
    return mat


def all_objects(plan):
    return [sg.obj for sg in plan.segs] + list(plan.wings)


def pose_chain(plan, bends=None, head_pos=(0.0, 0.0), head_heading=0.0, wings_mounted=True):
    """Forward kinematics: put every segment at the given joint bends (radians,
    None = printed pose).  Used for the display renders."""
    if bends is None:
        for sg in plan.segs:
            sg.obj.matrix_world = sg.print_matrix
        for w, m in zip(plan.wings, plan.wing_print_mats):
            w.matrix_world = m
        return
    segs = plan.segs
    P = Vector((head_pos[0], head_pos[1], 0.0))
    h = head_heading
    segs[0].obj.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(h, 4, "Z")
    for i, sg in enumerate(segs[1:], start=1):
        h = h - bends[i - 1]
        sg.obj.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(h, 4, "Z")
        if sg.kind != "tip":
            P = P + Matrix.Rotation(h, 3, "Z") @ Vector((-sg.L, 0.0, 0.0))
    if wings_mounted and plan.wings:
        sh = segs[plan.wing_seg].obj.matrix_world
        for w, mnt in zip(plan.wings, plan.wing_mounts):
            w.matrix_world = sh @ mnt


def display_bends(plan, amp_deg=24.0, waves=1.05, phase=0.9):
    out = []
    n = len(plan.joints)
    for i, j in enumerate(plan.joints):
        u = i / max(1, n - 1)
        a = math.radians(amp_deg) * math.sin(phase + TAU * waves * u) * (0.55 + 0.6 * u)
        lim = j.theta - math.radians(4)
        out.append(max(-lim, min(lim, a)))
    return out


def _bbox_world(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def _studio_floor_material():
    """dark glossy floor with a soft pool of colour under the model"""
    m = bpy.data.materials.get("GS_floor_studio") or bpy.data.materials.new("GS_floor_studio")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.42
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.name = "GS_pool"
    mr.interpolation_type = "SMOOTHSTEP"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.name = "GS_ramp"
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs[0], ln.inputs[0])
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def _pei_material():
    """dark textured build plate, like a real PEI sheet"""
    m = bpy.data.materials.get("GS_floor_plate") or bpy.data.materials.new("GS_floor_plate")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.27, 0.245, 0.22, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Metallic"].default_value = 0.35
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.65
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def _backdrop(scheme, mode, ctr, R):
    """mode 'studio': coloured pool of light on a dark floor; 'plate': PEI sheet"""
    sc = bpy.context.scene
    sch = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES["emerald"])
    near, far = sch.get("backdrop", ((0.13, 0.12, 0.12), (0.012, 0.012, 0.014)))
    floor = bpy.data.objects["GS_studio_floor"]
    floor.location = (ctr.x, ctr.y, -0.01)
    wn = sc.world.node_tree.nodes
    amb, cam = wn["GS_amb"], wn["GS_camrays"]
    if mode == "plate":
        floor.material_slots[0].material = _pei_material()
        for n_ in (amb, cam):
            n_.inputs["Color"].default_value = (0.06, 0.06, 0.065, 1.0)
            n_.inputs["Strength"].default_value = 0.5
        return
    mat = _studio_floor_material()
    floor.material_slots[0].material = mat
    nt = mat.node_tree
    mr = nt.nodes["GS_pool"]
    mr.inputs["From Min"].default_value = 0.30 * R
    mr.inputs["From Max"].default_value = 2.4 * R
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    el = nt.nodes["GS_ramp"].color_ramp.elements
    el[0].position = 0.0
    el[0].color = tuple(near) + (1.0,)
    el[1].position = 1.0
    el[1].color = tuple(far) + (1.0,)
    amb.inputs["Color"].default_value = (0.10, 0.11, 0.14, 1.0)      # dim ambient fill
    amb.inputs["Strength"].default_value = 1.0
    cam.inputs["Color"].default_value = tuple(far) + (1.0,)          # seamless dark horizon
    cam.inputs["Strength"].default_value = 1.0


def setup_studio(plan, samples=96, scheme=None):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.name.startswith("GS_studio"):
            bpy.data.objects.remove(o)
    coll = bpy.data.collections.get("Gemscale Studio")
    if coll is None:
        coll = bpy.data.collections.new("Gemscale Studio")
        sc.collection.children.link(coll)
    bm = bmesh.new()
    size = 4000.0
    vs = [bm.verts.new(v) for v in ((-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0))]
    bm.faces.new(vs)
    floor = link_obj(bm, "GS_studio_floor", coll)
    floor.data.materials.append(_studio_floor_material())
    world = bpy.data.worlds.get("GS_world") or bpy.data.worlds.new("GS_world")
    sc.world = world
    world.use_nodes = True
    wt = world.node_tree
    wt.nodes.clear()
    w_out = wt.nodes.new("ShaderNodeOutputWorld")
    w_amb = wt.nodes.new("ShaderNodeBackground")
    w_amb.name = "GS_amb"                       # what lights the scene
    w_cam = wt.nodes.new("ShaderNodeBackground")
    w_cam.name = "GS_camrays"                   # what the camera sees
    w_lp = wt.nodes.new("ShaderNodeLightPath")
    w_mix = wt.nodes.new("ShaderNodeMixShader")
    wt.links.new(w_lp.outputs["Is Camera Ray"], w_mix.inputs["Fac"])
    wt.links.new(w_amb.outputs["Background"], w_mix.inputs[1])
    wt.links.new(w_cam.outputs["Background"], w_mix.inputs[2])
    wt.links.new(w_mix.outputs["Shader"], w_out.inputs["Surface"])
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    for attr, val in (("use_adaptive_sampling", True), ("use_denoising", True), ("sample_clamp_indirect", 6.0),
                      ("caustics_reflective", False), ("caustics_refractive", False)):
        try:
            setattr(sc.cycles, attr, val)
        except Exception:
            pass
    try:
        sc.view_settings.view_transform = "AgX"
        looks = [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items]
        for want in ("Punchy", "Medium High Contrast", "High Contrast"):
            hit = [i for i in looks if want in i]
            if hit:
                sc.view_settings.look = hit[0]
                break
    except Exception:
        pass
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1200
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    return coll


def _light(coll, name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    coll.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return lo


def _camera(coll, loc, target, lens=55.0, dof_target=None, fstop=5.6, ortho_scale=None):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("GS_studio_cam")
    cam = bpy.data.objects.new("GS_studio_cam", cd)
    coll.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.clip_end = 20000
    if ortho_scale:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho_scale
    if dof_target is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(loc) - dof_target).length
        cd.dof.aperture_fstop = fstop
    sc.camera = cam
    return cam


def _fit_camera(cam, objs, fill=0.86, iters=4):
    """Dolly the camera along its view axis and shift the lens so the objects
    fill `fill` of the 4:3 frame, centred."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    pts = []
    for o in objs:      # every vertex, so thin tips (snout, horns) are never cropped
        mw = o.matrix_world
        pts += [mw @ v.co for v in o.data.vertices]
    cd = cam.data
    cd.shift_x = cd.shift_y = 0.0
    for _ in range(iters):
        bpy.context.view_layer.update()     # a new camera's matrix is stale until updated
        fwd = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
        ndc = [world_to_camera_view(sc, cam, p) for p in pts]
        x0, x1 = min(v.x for v in ndc), max(v.x for v in ndc)
        y0, y1 = min(v.y for v in ndc), max(v.y for v in ndc)
        k = max((x1 - x0) / fill, (y1 - y0) / fill)
        if cd.type == "ORTHO":
            cd.ortho_scale *= k
        else:
            # distance to the point cloud centre along the view axis
            c = sum(pts, Vector()) / len(pts)
            dist = (c - cam.location).dot(fwd)
            cam.location = cam.location + fwd * (dist - dist * k)
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(sc, cam, p) for p in pts]
        x0, x1 = min(v.x for v in ndc), max(v.x for v in ndc)
        y0, y1 = min(v.y for v in ndc), max(v.y for v in ndc)
        rx, ry = sc.render.resolution_x, sc.render.resolution_y
        m = max(rx, ry)
        cd.shift_x += ((x0 + x1) / 2 - 0.5) * rx / m
        cd.shift_y += ((y0 + y1) / 2 - 0.5) * ry / m


def _clear_studio_rigs():
    for o in list(bpy.data.objects):
        if o.name.startswith("GS_studio") and o.type in ("LIGHT", "CAMERA"):
            data = o.data
            bpy.data.objects.remove(o)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                else:
                    bpy.data.cameras.remove(data)


def _lights_for(coll, ctr, R, key_from=(-1.0, -1.3), mood="studio"):
    """warm key, cool rim, orange kicker and a dim fill (studio); soft key + fill (plate)"""
    k = (R / 80.0) ** 2 * (2.6 if mood == "plate" else 1.0)
    kx, ky = key_from
    warm, cool, orange = (1.0, 0.93, 0.82), (0.62, 0.78, 1.0), (1.0, 0.62, 0.32)
    _light(coll, "GS_studio_key", ctr + Vector((kx * R * 1.4, ky * R * 1.4, R * 2.0)), ctr, 52000 * k, R * 1.5, warm)
    _light(coll, "GS_studio_fill", ctr + Vector((-ky * R * 1.6, kx * R * 1.6, R * 1.0)), ctr, 9000 * k, R * 2.0, (1, 1, 1))
    if mood == "plate":
        return
    _light(coll, "GS_studio_rim", ctr + Vector((-kx * R * 1.5, -ky * R * 1.7, R * 1.1)), ctr, 72000 * k, R * 0.6, cool)
    _light(coll, "GS_studio_kick", ctr + Vector((ky * R * 1.6, -kx * R * 1.6, R * 0.5)), ctr, 30000 * k, R * 0.5, orange)


def render_covers(plan, out_dir, scheme=None, samples=None, views=("hero", "head", "plate"), prefix=""):
    """Render MakerWorld-ready 1600x1200 (4:3) images.  NOTE: MakerWorld needs at
    least one REAL photo of a printed model too - use these as extra images."""
    cfg = plan.cfg
    scheme = scheme or cfg["color_scheme"]
    samples = samples or cfg["render_samples"]
    sc = bpy.context.scene
    coll = setup_studio(plan, samples, scheme)
    apply_colors(plan, scheme)
    files = []
    objs = all_objects(plan)
    for view in views:
        _clear_studio_rigs()
        if view == "plate":
            pose_chain(plan, None)
            mn, mx = _bbox_world(objs)
            ctr = (mn + mx) / 2
            R = max(mx.x - mn.x, mx.y - mn.y) / 2
            _backdrop(scheme, "plate", ctr, R)
            _lights_for(coll, ctr, R, mood="plate")
            cam = _camera(coll, ctr + Vector((0, 0, 800)), ctr, ortho_scale=200.0)
            _fit_camera(cam, objs, fill=0.9)
        else:
            bends = display_bends(plan)
            pose_chain(plan, bends, (0.0, 0.0), 0.0)
            mn, mx = _bbox_world(objs)
            ctr = (mn + mx) / 2
            R = (mx - mn).length / 2
            hm = plan.segs[0].obj.matrix_world
            head_c = hm @ Vector((plan.head_len * 0.45, 0, 10 * plan.s))
            tail_c = plan.segs[-1].obj.matrix_world @ Vector((-plan.tip_len * 0.5, 0, 0))
            u = (head_c - tail_c)
            u.z = 0
            u.normalize()
            v = Vector((-u.y, u.x, 0.0))
            if view == "hero":
                _backdrop(scheme, "studio", ctr, R)
                _lights_for(coll, ctr, R)
                loc = ctr + (u * 0.9 - v * 0.75).normalized() * R * 2.0 + Vector((0, 0, R * 1.35))
                cam = _camera(coll, loc, ctr.lerp(head_c, 0.2), lens=50, dof_target=head_c, fstop=11.0)
                _fit_camera(cam, objs, fill=0.9)
                cam.data.dof.focus_distance = (cam.location - head_c).length
            elif view == "head":
                _backdrop(scheme, "studio", head_c, 90 * plan.s)
                _lights_for(coll, head_c, 60 * plan.s)
                hdir = (hm.to_3x3() @ Vector((1, 0, 0))).normalized()
                az = math.atan2(hdir.y, hdir.x) - math.radians(32)
                d = 130.0 * plan.s
                loc = head_c + Vector((math.cos(az) * d, math.sin(az) * d, d * 0.55))
                _camera(coll, loc, head_c + Vector((-6 * plan.s * hdir.x, -6 * plan.s * hdir.y, -3 * plan.s)),
                        lens=70, dof_target=head_c, fstop=4.5)
            elif view == "side":
                _backdrop(scheme, "studio", ctr, R)
                _lights_for(coll, ctr, R, key_from=(0.4, -1.4))
                loc = ctr - v * R * 2.4 + u * R * 0.35 + Vector((0, 0, R * 0.55))
                cam = _camera(coll, loc, ctr, lens=60, dof_target=ctr, fstop=11.0)
                _fit_camera(cam, objs, fill=0.92)
                cam.data.dof.focus_distance = (cam.location - ctr).length
        path = os.path.join(out_dir, f"{prefix}cover_{view}.png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        files.append(path)
        print("[gemscale] rendered", path)
    pose_chain(plan, None)
    return files


# =============================================================================
# 12. BLENDER UI (sidebar "Gemscale" tab)
# =============================================================================

_LAST = {"plan": None, "report": None}


def _props_to_settings(p):
    return dict(preset=p.preset, scale=p.scale, neck=p.neck, torso=p.torso, tail=p.tail, layout=p.layout,
                bed=(p.bed_x, p.bed_y), clearance=p.clearance, seed=p.seed, legs=p.legs, horns=p.horns,
                spikes=p.spikes, plates=p.plates, wings=p.wings, wing_fit=p.wing_fit, keyring=p.keyring, out=p.out,
                color_scheme=p.color_scheme, render_samples=p.render_samples)


def _apply_preset(self, context):
    pre = PRESETS.get(self.preset)
    if pre:
        self.scale = pre["scale"]
        self.neck, self.torso, self.tail = pre["neck"], pre["torso"], pre["tail"]
        self.bed_x, self.bed_y = pre["bed"]
        self.keyring = pre.get("keyring", False)


def _ui_classes():
    from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

    class GemscaleProps(bpy.types.PropertyGroup):
        preset: EnumProperty(name="Preset", items=[("mini", "Mini (keychain)", ""), ("standard", "Standard (A1 mini)", ""),
                                                   ("long", "Long (256 mm bed)", "")], default="standard",
                             update=_apply_preset)
        scale: FloatProperty(name="Scale", default=1.0, min=0.5, max=2.0)
        neck: IntProperty(name="Neck", default=2, min=1, max=6)
        torso: IntProperty(name="Torso", default=4, min=1, max=16)
        tail: IntProperty(name="Tail", default=6, min=2, max=20)
        layout: EnumProperty(name="Bed layout", items=[("auto", "Auto", ""), ("coil", "Coil", ""), ("wave", "Wave", ""),
                                                       ("straight", "Straight", "")], default="auto")
        bed_x: FloatProperty(name="Bed X", default=180.0, min=80.0, max=500.0)
        bed_y: FloatProperty(name="Bed Y", default=180.0, min=80.0, max=500.0)
        clearance: FloatProperty(name="Joint clearance", default=0.35, min=0.2, max=0.6, precision=2)
        seed: IntProperty(name="Seed", default=7, min=0)
        legs: BoolProperty(name="Legs", default=True)
        horns: BoolProperty(name="Horns", default=True)
        spikes: BoolProperty(name="Crystal fins", default=True)
        plates: BoolProperty(name="Armour plates", default=True)
        wings: BoolProperty(name="Snap-in wings", default=True)
        wing_fit: FloatProperty(name="Wing slot fit", default=0.30, min=0.1, max=0.8, precision=2)
        keyring: BoolProperty(name="Keyring loop", default=False)
        color_scheme: EnumProperty(name="Render colours", items=[(k, k.title(), "") for k in COLOR_SCHEMES],
                                   default="emerald")
        render_samples: IntProperty(name="Render samples", default=96, min=8, max=4096)
        out: StringProperty(name="Export folder", default="//gemscale_export", subtype="DIR_PATH")

    class GEMSCALE_OT_generate(bpy.types.Operator):
        bl_idname = "gemscale.generate"
        bl_label = "Generate Dragon"
        bl_description = "Build the print-in-place dragon and run the printability checks"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            try:
                plan = generate(_props_to_settings(context.scene.gemscale))
                rep = check_dragon(plan, verbose=False)
            except Exception as e:
                self.report({"ERROR"}, str(e))
                return {"CANCELLED"}
            _LAST["plan"], _LAST["report"] = plan, rep
            self.report({"INFO"} if rep["ok"] else {"WARNING"},
                        f"Dragon ready: {len(plan.segs)} parts - checks {'PASSED' if rep['ok'] else 'need attention'}")
            return {"FINISHED"}

    class GEMSCALE_OT_export(bpy.types.Operator):
        bl_idname = "gemscale.export"
        bl_label = "Export STL + 3MF"
        bl_description = "Write STL, 3MF and a print report to the export folder"

        def execute(self, context):
            plan = _LAST["plan"]
            if plan is None or any(sg.obj.name not in bpy.data.objects for sg in plan.segs):
                bpy.ops.gemscale.generate()
                plan = _LAST["plan"]
            out, stem = export_all(plan, report=_LAST["report"])
            self.report({"INFO"}, f"Exported {stem} to {out}")
            return {"FINISHED"}

    class GEMSCALE_OT_render(bpy.types.Operator):
        bl_idname = "gemscale.render"
        bl_label = "Render Covers (slow)"
        bl_description = "Render 1600x1200 MakerWorld cover images with Cycles (takes a few minutes)"

        def execute(self, context):
            plan = _LAST["plan"]
            if plan is None or any(sg.obj.name not in bpy.data.objects for sg in plan.segs):
                bpy.ops.gemscale.generate()
                plan = _LAST["plan"]
            out = export_dir(plan)
            files = render_covers(plan, out)
            self.report({"INFO"}, f"Rendered {len(files)} images to {out}")
            return {"FINISHED"}

    class GEMSCALE_PT_panel(bpy.types.Panel):
        bl_label = "Gemscale Flexi Dragon"
        bl_idname = "GEMSCALE_PT_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Gemscale"

        def draw(self, context):
            p = context.scene.gemscale
            L = self.layout
            L.prop(p, "preset")
            col = L.column(align=True)
            col.prop(p, "scale")
            row = col.row(align=True)
            row.prop(p, "neck")
            row.prop(p, "torso")
            row.prop(p, "tail")
            col.prop(p, "seed")
            box = L.box()
            box.label(text="Printer")
            box.prop(p, "layout")
            row = box.row(align=True)
            row.prop(p, "bed_x")
            row.prop(p, "bed_y")
            box.prop(p, "clearance")
            box.prop(p, "wing_fit")
            box = L.box()
            box.label(text="Features")
            grid = box.grid_flow(columns=2, align=True)
            for k in ("legs", "horns", "spikes", "plates", "wings", "keyring"):
                grid.prop(p, k)
            L.operator("gemscale.generate", icon="PLAY")
            rep = _LAST["report"]
            if rep:
                b = L.box()
                b.label(text=("Checks PASSED" if rep["ok"] else "Checks need attention"),
                        icon=("CHECKMARK" if rep["ok"] else "ERROR"))
                b.label(text=f"Smallest joint gap {rep['min_gap']:.2f} mm")
                b.label(text=f"~{rep['volume_cm3'] * 1.24 * 0.75:.0f} g of PLA")
            L.prop(p, "out")
            L.operator("gemscale.export", icon="EXPORT")
            L.prop(p, "color_scheme")
            L.prop(p, "render_samples")
            L.operator("gemscale.render", icon="RENDER_STILL")

    return [GemscaleProps, GEMSCALE_OT_generate, GEMSCALE_OT_export, GEMSCALE_OT_render, GEMSCALE_PT_panel]


def register_ui():
    """(Re-)register the sidebar UI.  Classes from a previous run of this script
    in the same Blender session are unregistered first."""
    ns = bpy.app.driver_namespace
    for cls in reversed(ns.get("gemscale_classes", [])):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    classes = _ui_classes()
    for cls in classes:
        bpy.utils.register_class(cls)
    ns["gemscale_classes"] = classes
    bpy.types.Scene.gemscale = bpy.props.PointerProperty(type=classes[0])


def setup_scene_units():
    us = bpy.context.scene.unit_settings
    us.system = "METRIC"
    us.scale_length = 0.001
    us.length_unit = "MILLIMETERS"


# =============================================================================
# 13. ENTRY POINT
# =============================================================================

def parse_cli(argv):
    user = {}
    if "--" not in argv:
        return user
    args = argv[argv.index("--") + 1:]
    flags = {"render": ("render", True), "keyring": ("keyring", True), "no-legs": ("legs", False),
             "no-horns": ("horns", False), "no-spikes": ("spikes", False), "no-plates": ("plates", False),
             "no-wings": ("wings", False)}
    i = 0
    while i < len(args):
        a = args[i]
        if not a.startswith("--"):
            i += 1
            continue
        key = a[2:]
        if key in flags:
            k, v = flags[key]
            user[k] = v
            i += 1
            continue
        val = args[i + 1] if i + 1 < len(args) else None
        key = key.replace("-", "_")
        if key == "bed" and val:
            w, _, h = val.lower().partition("x")
            user["bed"] = (float(w), float(h or w))
        elif key in ("scale", "clearance", "wing_fit"):
            user[key] = float(val)
        elif key in ("neck", "torso", "tail", "seed", "render_samples", "samples"):
            user["render_samples" if key == "samples" else key] = int(val)
        else:
            user[key] = val
        i += 2
    return user


def main():
    user = parse_cli(sys.argv)
    if bpy.app.background:
        plan = generate(user)
        rep = check_dragon(plan)
        print(summary_text(plan, rep))
        out, stem = export_all(plan, report=rep)
        if plan.cfg["render"]:
            render_covers(plan, out)
        if user.get("save"):
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(user["save"]))
    else:
        setup_scene_units()
        register_ui()
        plan = generate(user)
        rep = check_dragon(plan, verbose=True)
        _LAST["plan"], _LAST["report"] = plan, rep
        mat = apply_colors(plan, plan.cfg["color_scheme"])
        sch = COLOR_SCHEMES.get(plan.cfg["color_scheme"], {})
        if "base" in sch:
            mat.diffuse_color = sch["base"] + (1.0,)
        print(summary_text(plan, rep))


if __name__ == "__main__":
    main()
