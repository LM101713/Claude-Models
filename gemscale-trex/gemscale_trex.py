"""
Gemscale Flexi T-Rex: Blender generator for a classic print-in-place flexi T. rex.

Seen from above it's a big toothy head followed by a chain of ridged segments: neck, chest
(with tiny arms), belly, hips (with big legs), five tail segments and a pointed tip. The
gaps between segments are V-shaped, the classic flexi look, and every joint is the captured
knob-in-socket swivel used by the other Gemscale models, so it prints fully assembled, flat
on its belly, with no supports, and wiggles side to side.

Every part is lofted through flat-bottomed, pitched-roof sections, so nothing overhangs.

Run it
    blender -b -P gemscale_trex.py -- --preset standard --out models
    python gemscale_trex.py --preset mini --keyring --out models     (pip install bpy)
or open it in Blender's Scripting tab and press Run Script: a "Gemscale" tab appears in the
3D-viewport sidebar (N) with Generate / Export buttons.
"""

bl_info = {
    "name": "Gemscale Flexi T-Rex",
    "author": "Gemscale",
    "version": (3, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Gemscale",
    "description": "Print-in-place articulated T. rex generator",
    "category": "Add Mesh",
}

import json
import math
import os
import struct
import sys
import zipfile

import bpy  # noqa: I001  (bpy must come first when it is used as a Python module)
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# =============================================================================
# 1. SETTINGS
# =============================================================================

GAP = 0.50      # clearance between a joint housing and the next part (and every swept cut)
VGAP = 0.40     # air under each tongue bridge (= two 0.2 mm layers)
SIDE = 0.40     # tongue side clearance inside its notch
LAYER = 0.20    # joint heights are snapped to this layer grid (print at 0.2 mm layers)
WALL = 1.00     # minimum socket wall
MARGIN = 5.0    # extra angle (deg) kept free beyond each joint's swing
TAU = 2.0 * math.pi

THETA = 25.0    # every joint wiggles +-THETA degrees either side of its printed pose

PRESETS = {
    # s: scale of the whole design; hw_min: smallest joint housing the knob allows
    "standard": dict(s=1.0, r_n=1.5, r_e=2.35, band=0.7, hw_min=3.9, bed=(180, 180)),
    "mini": dict(s=0.72, r_n=1.3, r_e=2.05, band=0.6, hw_min=3.6, bed=(180, 180)),
}

SETTINGS = dict(preset="standard", clearance=0.35, keyring=False, out="//gemscale_export")


# =============================================================================
# 2. THE DESIGN (mm, standard size; the mini scales it)
# =============================================================================
#
# Seen from above, the T. rex is a big head followed by a chain of ridged segments: neck,
# chest (tiny arms), belly, hips (big legs), five tail segments and a pointed tip. It lies
# on its belly and wiggles side to side, the classic flexi-toy way.
#
# Every part is lofted through "stations" (x, half width, side height, ridge height):
# flat-bottomed sections with vertical sides and a pitched roof, so it can't overhang. Each
# part runs along its own +x axis from its front joint (x = 0) to its back joint (x = L).

HEAD = dict(
    # head runs along -x from the neck joint at x = 0: blunt snout, deep skull, wide cheeks
    st=[(-34.5, 4.0, 5.6, 7.0), (-33.0, 6.4, 6.4, 8.4), (-28.5, 8.4, 7.6, 10.6), (-19.5, 10.6, 9.2, 13.2),
        (-11.0, 13.8, 10.4, 15.4), (-4.5, 13.4, 10.2, 14.8), (-1.0, 9.6, 9.0, 11.6)],
    eye=(-12.5, 9.9, 3.5),             # x, y, radius
    nostril=(-30.0, 3.0, 1.1),
    teeth=[-31.0, -27.2, -23.4, -19.6, -15.8],
    crown=[(-6.5, 2.2), (-2.8, 1.7)],  # (x, height) of the little spikes on the skull
)

# name, length, stations (x, half width, side height, ridge height), spike height
SEGS = [
    ("neck", 9.5, [(0, 7.0, 7.0, 9.4), (4.75, 7.6, 7.4, 9.8), (9.5, 7.2, 7.2, 9.4)], 1.8),
    ("chest", 13.0, [(0, 9.0, 7.6, 10.8), (6.5, 10.8, 8.4, 12.0), (13, 10.2, 8.0, 11.6)], 2.2),
    ("hips", 14.0, [(0, 10.6, 8.2, 11.6), (7, 11.4, 8.6, 12.0), (14, 8.6, 7.2, 10.0)], 2.2),
    ("tail1", 12.0, [(0, 8.0, 7.0, 9.6), (12, 7.0, 6.6, 8.6)], 2.0),
    ("tail2", 12.0, [(0, 7.0, 6.6, 8.6), (12, 6.0, 6.0, 7.6)], 1.8),
    ("tail3", 11.0, [(0, 6.0, 6.0, 7.6), (11, 5.2, 5.6, 6.8)], 1.6),
    ("tail4", 11.0, [(0, 5.2, 5.6, 6.8), (11, 4.6, 5.3, 6.2)], 1.4),
    ("tail5", 10.0, [(0, 4.6, 5.3, 6.2), (10, 4.2, 5.1, 5.7)], 1.2),
    ("tip", 16.0, [(0, 4.2, 5.1, 5.7), (8, 2.8, 4.2, 4.8), (16, 0.6, 1.6, 2.0)], 0.0),
]
# housing radius of the joint at the back of each part (head first)
HOUSING = [5.6, 5.8, 6.2, 6.0, 5.6, 5.0, 4.6, 4.2, 3.9]
# printed bend at each joint (deg): an S-curve with the tail swinging round
CURL = [8.0, -8.0, -6.0, 6.0, 9.0, 10.0, 10.0, 9.0, 8.0]
HEAD_HEADING = 182.0    # the head points this way (deg); the chain runs off behind it

# limbs, in the frame of their segment (+y side; mirrored for the other side)
LEG = dict(thigh=(10.0, 15.6, 6.4, 4.6, 10.5, 50.0),      # x, y, rx, ry, height, angle
           shin=((11.5, 18.5), (12.5, 23.5), 5.2, 4.6, 6.6, 5.8),
           foot=((12.5, 23.5), (3.4, 24.4), 5.2, 4.2, 5.0, 4.2),
           toes=(4.2, 2.0, 2.8))                           # length, base width, height
ARM = dict(upper=((6.5, 9.6), (4.0, 12.6), 2.6, 2.3, 4.6, 4.2),
           fore=((4.0, 12.6), (1.2, 13.4), 2.3, 2.0, 4.2, 3.8),
           claws=(2.0, 1.2, 2.0))

_HEAD0, _SEGS0, _LEG0, _ARM0 = HEAD, SEGS, LEG, ARM


# =============================================================================
# 3. SMALL HELPERS
# =============================================================================

def rup(z):
    return math.ceil(z / LAYER - 1e-6) * LAYER


def dirv(a_deg):
    return (math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg)))


def ccw(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
            for i in range(len(poly)))
    return poly if a > 0 else poly[::-1]


def bm_prism(poly, z0, z1):
    poly = ccw(list(poly))
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
    """Solid of revolution about a vertical axis; profile [(r, z)] bottom -> top, r > 0."""
    bm = bmesh.new()
    rings = [[bm.verts.new((cx + r * math.cos(TAU * i / segs), cy + r * math.sin(TAU * i / segs), z))
              for i in range(segs)] for r, z in profile]
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    return bm


def bm_hull(points):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in points]
    res = bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
    kill = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def link_obj(bm, name, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def copy_obj(ob, name=None):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = name or ob.name + "_copy"
    for coll in ob.users_collection:
        coll.objects.link(c)
    return c


def delete_obj(ob):
    me = ob.data
    bpy.data.objects.remove(ob)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)


def transform_obj(ob, M):
    ob.data.transform(M)
    ob.data.update()


def boolean_solver():
    items = bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items.keys()
    return "MANIFOLD" if "MANIFOLD" in items else "EXACT"


def _is_closed(bm):
    return all(e.is_manifold and not e.is_boundary for e in bm.edges)


def clean_mesh(ob):
    """Merge coincident verts, drop slivers and keep the mesh all triangles (big n-gons
    left by the booleans can be non-simple and then can't be triangulated cleanly later).
    A variant is kept only if the shell stays closed."""
    for dist, dissolve in ((1e-4, True), (1e-6, True), (1e-6, False), (0.0, False)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
        if dist:
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
        if dissolve:
            bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
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


def boolean(target, tools, op, tidy=True):
    """target = target OP tools (tools are consumed). INTERSECT takes exactly one tool.
    tidy=False skips the vertex clean-up (for throw-away tool meshes)."""
    tools = [t for t in tools if t is not None]
    if not tools:
        return target
    if op == "INTERSECT":
        assert len(tools) == 1
    solver = boolean_solver()
    coll = bpy.data.collections.new("_gs_tool")
    bpy.context.scene.collection.children.link(coll)
    for t in tools:
        for uc in list(t.users_collection):
            uc.objects.unlink(t)
        coll.objects.link(t)
    m = target.modifiers.new(op, "BOOLEAN")
    m.operation = op
    if len(tools) == 1:
        m.operand_type = "OBJECT"
        m.object = tools[0]
    else:
        m.operand_type = "COLLECTION"
        m.collection = coll
    m.solver = solver
    if solver == "EXACT":
        m.use_self = True
        m.use_hole_tolerant = True
    for t in tools:
        t.hide_render = True
        t.display_type = "WIRE"
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    old = target.data
    target.modifiers.clear()
    target.data = me
    bpy.data.meshes.remove(old)
    if tidy:
        clean_mesh(target)
    for t in list(coll.objects):
        delete_obj(t)
    bpy.data.collections.remove(coll)
    return target


def weld(ob, dist=1e-4):
    """Merge vertices closer than float32 STL precision (only if the shell stays closed)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    if _is_closed(bm) and all(len(f.verts) == 3 for f in bm.faces):
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()


def triangulate(ob):
    """Final triangle mesh (what the STL/3MF get), checked: n-gons left by the booleans are
    triangulated here rather than by the exporter. A result is kept only if it is still a
    closed manifold with no zero-area triangles; the plainest variant is the last resort."""
    tries = [(m, d, strict) for strict in (True, False) for m, d in
             (("BEAUTY", True), ("EAR_CLIP", True), ("BEAUTY", False), ("EAR_CLIP", False))]
    for method, dissolve, strict in tries:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method=method)
        if dissolve:
            bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        tris = all(len(f.verts) == 3 for f in bm.faces)
        if _is_closed(bm) and tris and (not strict or all(f.calc_area() > 1e-10 for f in bm.faces)):
            bm.to_mesh(ob.data)
            ob.data.update()
            bm.free()
            return True
        bm.free()
    return False


def mesh_islands(bm):
    seen, islands = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            w = stack.pop()
            isl.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        islands.append(isl)
    return islands


def keep_main_islands(ob, min_vol=2.0):
    """Drop crumbs (tiny islands) that a cut can leave behind."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.index_update()
    isl = mesh_islands(bm)
    if len(isl) > 1:
        vols = []
        for vs in isl:
            faces = {f for v in vs for f in v.link_faces}
            vol = 0.0
            for f in faces:
                tri = [l.vert.co for l in f.loops]
                for i in range(1, len(tri) - 1):
                    vol += tri[0].dot(tri[i].cross(tri[i + 1])) / 6.0
            vols.append(abs(vol))
        biggest = max(vols)
        kill = [v for vs, vol in zip(isl, vols) if vol < max(min_vol, 0.02 * biggest) for v in vs]
        if kill:
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def bvh_of(ob, M=None):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    if M is not None:
        bm.transform(M)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tree = BVHTree.FromBMesh(bm)
    pts = [v.co.copy() for v in bm.verts]
    bm.free()
    return tree, pts


# =============================================================================
# 4. THE JOINT
# =============================================================================

class Joint:
    """Knob-in-socket swivel between a front part F and the next part R.

    F owns the round housing, the socket and the notch. R owns the cup, the tongue and the
    knob. R's printed pose is the reference: it swings from `lo` to `hi` degrees (counter-
    clockwise positive) and the notch is the hard stop.

      side view of the knob in F's socket:     top view:
               ____                              F | housing ( knob ) <- tongue - R
           ___/    \\___  <- 45 deg, no support    | the notch lets the tongue swing
          |   knob     |  <- vertical band
           \\___    ___/  <- 45 deg
               \\__/        sits on the bed
    """

    def __init__(self, name, F, R, pivot, heading, rng, hw, cfg, source=None, split=(-88.0, 88.0)):
        c = cfg["clearance"]
        self.split = split                             # where R's share of the body starts (deg)
        self.name, self.F, self.R, self.source = name, F, R, source
        self.pivot, self.heading = pivot, heading
        self.lo, self.hi = rng
        self.hw, self.c = hw, c
        self.r_n, self.r_e, self.band = cfg["r_n"], cfg["r_e"], cfg["band"]
        self.z1 = self.r_e - self.r_n
        self.z2 = self.z1 + self.band
        self.z3 = self.z2 + (self.r_e - self.r_n)
        self.z_nf = rup(self.z3 + 0.414 * c + 0.05)   # notch floor (top of F under the tongue)
        self.z_n = self.z_nf + VGAP                    # tongue underside
        self.t_side = self.z_n + 1.4                   # tongue top
        self.t_top = self.t_side + 0.4
        self.w_t = 2 * self.r_n - 0.3
        self.rho = hw + GAP

    def M(self):
        return Matrix.Translation((self.pivot[0], self.pivot[1], 0.0)) @ Matrix.Rotation(
            math.radians(self.heading), 4, "Z")

    def sector(self):
        """Angles (relative to the heading) of R's share of the body. R is cut off by a disc
        round F's knuckle, so it can never swing into the housing; anything else it would hit
        is trimmed from F by the swept clearance cut."""
        return self.split

    def wedge(self, coll, a0, a1, R=400.0):
        n = max(4, int(abs(a1 - a0) / 5) + 2)
        pts = [(0.0, 0.0)] + [(R * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
                               R * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
        bm = bm_prism(pts, -5.0, 80.0)
        bm.transform(self.M())
        return link_obj(bm, "wedge", coll)

    def disc(self, coll, r):
        bm = bm_lathe([(r, -5.0), (r, 80.0)], 96, self.pivot[0], self.pivot[1])
        return link_obj(bm, "disc", coll)

    def f_cutters(self, coll):
        c = self.c
        k = (math.sqrt(2) - 1) * c
        s2 = math.sqrt(2) * c
        sock = bm_lathe([(self.r_n + s2, -1.0), (self.r_n + s2, 0.0), (self.r_e + c, self.z1 - k),
                         (self.r_e + c, self.z2 + k), (self.r_n + c, self.z3 + k), (self.r_n + c, 80.0)], 64)
        sock.transform(self.M())
        a = self.w_t / 2 + SIDE
        far = self.hw + 4.0
        pl, ph = math.radians(self.lo), math.radians(self.hi)
        lo = (a * math.sin(pl), -a * math.cos(pl))
        hi = (-a * math.sin(ph), a * math.cos(ph))
        lo_f = (lo[0] + far * math.cos(pl), lo[1] + far * math.sin(pl))
        hi_f = (hi[0] + far * math.cos(ph), hi[1] + far * math.sin(ph))
        r0, r1 = math.hypot(*lo_f), math.hypot(*hi_f)
        a0, a1 = math.atan2(lo_f[1], lo_f[0]), math.atan2(hi_f[1], hi_f[0])
        arc = [((r0 + (r1 - r0) * t) * math.cos(a0 + (a1 - a0) * t), (r0 + (r1 - r0) * t) * math.sin(a0 + (a1 - a0) * t))
               for t in [i / 13 for i in range(1, 13)]]
        notch = bm_prism([lo, lo_f] + arc + [hi_f, hi], self.z_nf, 80.0)
        notch.transform(self.M())
        return [link_obj(sock, "socket", coll), link_obj(notch, "notch", coll)]

    def r_addons(self, coll):
        r_t = self.w_t / 2
        x_end = self.rho + 1.2
        foot = [(r_t * math.cos(math.pi / 2 + math.pi * i / 8), r_t * math.sin(math.pi / 2 + math.pi * i / 8))
                for i in range(9)] + [(x_end, -r_t), (x_end, r_t)]
        pts = [(x, y, z) for (x, y) in foot for z in (self.z_n, self.t_side)]
        pts += [(0.0, 0.0, self.t_top), (x_end, 0.0, self.t_top)]
        tongue = bm_hull(pts)
        tongue.transform(self.M())
        knob = bm_lathe([(self.r_n, 0.0), (self.r_e, self.z1), (self.r_e, self.z2), (self.r_n, self.z3),
                         (self.r_n, self.t_side - 0.2)], 64)
        knob.transform(self.M())
        return [link_obj(tongue, "tongue", coll), link_obj(knob, "knob", coll)]


# =============================================================================
# 5. BUILDING
# =============================================================================

def get_collection(name="Gemscale T-Rex"):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        delete_obj(ob)
    return coll


def section(x, w, hs, ht):
    """Flat bottom, vertical sides, pitched roof with a ridge (a pentagon)."""
    hm = hs + 0.75 * (ht - hs)
    return [(x, -w, 0.0), (x, w, 0.0), (x, -w, hs), (x, w, hs), (x, -0.6 * w, hm), (x, 0.6 * w, hm), (x, 0.0, ht)]


def loft(stations, coll, name="loft"):
    """Hull consecutive sections (three at a time, so the pieces overlap) into one body."""
    secs = [section(*s) for s in stations]
    n = len(secs)
    pieces = [link_obj(bm_hull(secs[i] + secs[i + 1] + secs[min(i + 2, n - 1)]), name, coll) for i in range(n - 1)]
    body = pieces.pop(0)
    return boolean(body, pieces, "UNION")


def prof(stations, x, k):
    """Station value k (1 half width, 2 side height, 3 ridge height) at x (linear)."""
    xs = [s[0] for s in stations]
    if x <= xs[0]:
        return stations[0][k]
    for a, b in zip(stations[:-1], stations[1:]):
        if x <= b[0]:
            t = (x - a[0]) / (b[0] - a[0])
            return a[k] + (b[k] - a[k]) * t
    return stations[-1][k]


def roof_z(stations, x, y):
    """Height of a loft's top surface at (x, y)."""
    w, hs, ht = prof(stations, x, 1), prof(stations, x, 2), prof(stations, x, 3)
    hm = hs + 0.75 * (ht - hs)
    u = min(abs(y) / w, 1.0)
    return ht - (ht - hm) * u / 0.6 if u <= 0.6 else hm - (hm - hs) * (u - 0.6) / 0.4


def bar(p, q, w0, w1, h0, h1, coll, n=8, ch=0.5):
    """A rounded bone from p to q: octagons at each end, chamfered on top."""
    pts = []
    for (c, w, h) in ((p, w0, h0), (q, w1, h1)):
        r = w / 2
        for i in range(n):
            a = TAU * (i + 0.5) / n
            pts += [(c[0] + r * math.cos(a), c[1] + r * math.sin(a), 0.0),
                    (c[0] + r * math.cos(a), c[1] + r * math.sin(a), h - ch),
                    (c[0] + (r - ch) * math.cos(a), c[1] + (r - ch) * math.sin(a), h)]
    return link_obj(bm_hull(pts), "bar", coll)


def claw(base, ang, length, wb, h, coll):
    """A claw / tooth lying on the bed, pointing along `ang`."""
    d, n = dirv(ang), dirv(ang + 90.0)
    b = (base[0] - 0.8 * d[0], base[1] - 0.8 * d[1])
    t = (base[0] + length * d[0], base[1] + length * d[1])
    pts = [(b[0] + s * wb / 2 * n[0], b[1] + s * wb / 2 * n[1], z) for s in (-1, 1) for z in (0.0, h)]
    pts += [(t[0], t[1], 0.0), (t[0], t[1], 0.35 * h)]
    return link_obj(bm_hull(pts), "claw", coll)


def spike(stations, x, size, coll):
    """A little dorsal spike growing out of the ridge (its tip stays over its base)."""
    zr = prof(stations, x, 3)
    pts = [(x + dx, dy, zr - 1.2) for dx in (-1.4 * size, 1.0 * size) for dy in (-0.55, 0.55)]
    pts += [(x + 0.4 * size, 0.0, zr + size)]
    return link_obj(bm_hull(pts), "spike", coll)


def housing(c, hw, H, coll, n=12, ch=0.6):
    pts = [(x, y, z) for (x, y) in [(c[0] + hw * math.cos(math.pi / n + TAU * i / n),
                                     c[1] + hw * math.sin(math.pi / n + TAU * i / n)) for i in range(n)]
           for z in (0.0, H - ch)]
    pts += [(c[0] + (hw - ch) * math.cos(math.pi / n + TAU * i / n),
             c[1] + (hw - ch) * math.sin(math.pi / n + TAU * i / n), H) for i in range(n)]
    return link_obj(bm_hull(pts), "housing", coll)


def mirror_y(ob):
    transform_obj(ob, Matrix.Diagonal((1.0, -1.0, 1.0, 1.0)))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def both_sides(make):
    a = make()
    b = mirror_y(make())
    return [a, b]


def leg(coll):
    x, y, rx, ry, h, ang = LEG["thigh"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def ring(sx, sy, z):
        pts = [(sx * math.cos(TAU * i / 16), sy * math.sin(TAU * i / 16)) for i in range(16)]
        return [(x + px * ca - py * sa, y + px * sa + py * ca, z) for (px, py) in pts]
    parts = [link_obj(bm_hull(ring(rx, ry, 0.0) + ring(rx, ry, 0.45 * h) + ring(0.85 * rx, 0.85 * ry, 0.75 * h)
                              + ring(0.45 * rx, 0.45 * ry, h)), "thigh", coll)]
    for k in ("shin", "foot"):
        p, q, w0, w1, h0, h1 = LEG[k]
        parts.append(bar(p, q, w0, w1, h0, h1, coll))
    ln, wb, th = LEG["toes"]
    toe = LEG["foot"][1]
    for a in (155.0, 180.0, 205.0):
        parts.append(claw(toe, a, ln, wb, th, coll))
    first = parts.pop(0)
    return boolean(first, parts, "UNION")


def arm(coll):
    parts = []
    for k in ("upper", "fore"):
        p, q, w0, w1, h0, h1 = ARM[k]
        parts.append(bar(p, q, w0, w1, h0, h1, coll))
    ln, wb, th = ARM["claws"]
    hand = ARM["fore"][1]
    for a in (165.0, 205.0):
        parts.append(claw(hand, a, ln, wb, th, coll))
    first = parts.pop(0)
    return boolean(first, parts, "UNION")


def build_head(cfg, coll):
    st = HEAD["st"] + [(0.0, cfg["hw"][0], HEAD["st"][-1][2], HEAD["st"][-1][3])]
    head = loft(st, coll, "head")
    adds, cuts = [housing((0.0, 0.0), cfg["hw"][0], st[-1][2], coll)], []
    for (x, h) in HEAD["crown"]:
        adds.append(spike(st, x, h, coll))
    # teeth: a zig-zag along both lips
    for x in HEAD["teeth"]:
        w = prof(st, x, 1)
        for s in (1, -1):
            adds.append(link_obj(bm_prism([(x + 1.3, s * (w - 0.6)), (x - 1.3, s * (w - 0.6)), (x - 0.4, s * (w + 1.5))],
                                          0.0, 2.6), "tooth", coll))
    # eyes: domes set into the top of the head, under an angled brow; slit pupils
    ex, ey, er = HEAD["eye"]
    for s in (1, -1):
        zc = roof_z(st, ex, ey) - 0.5 * er
        prof_ = [(er, 0.0), (er, zc)] + [(er * math.cos(math.radians(a)), zc + er * math.sin(math.radians(a)))
                                         for a in range(15, 90, 15)] + [(0.25, zc + er - 0.02)]
        adds.append(link_obj(bm_lathe(prof_, 40, ex, s * ey), "eye", coll))
        # brow boss: a raised bump over the inner-back of the eye (the T. rex "eyebrow")
        bx, by = ex + 1.4, s * (ey - 1.9)
        zb = roof_z(st, bx, by)
        ring = lambda rx, ry, z: [(bx + rx * math.cos(TAU * i / 14 + 0.2), by + ry * math.sin(TAU * i / 14 + 0.2), z)
                                  for i in range(14)]
        adds.append(link_obj(bm_hull(ring(4.2, 2.9, 0.0) + ring(4.2, 2.9, zb - 0.6) + ring(2.6, 1.7, zb + 1.9)),
                             "brow", coll))
        w2, h2 = 0.28 * er, 0.62 * er
        a = math.radians(-s * 15.0)
        dia = [(ex + px * math.cos(a) - py * math.sin(a), s * ey + px * math.sin(a) + py * math.cos(a))
               for (px, py) in ((h2, 0.0), (0.0, w2), (-h2, 0.0), (0.0, -w2))]
        cuts.append(link_obj(bm_prism(dia, zc + er - 0.9, 80.0), "pupil", coll))
    nx, ny, nr = HEAD["nostril"]
    for s in (1, -1):
        cuts.append(link_obj(bm_lathe([(nr, roof_z(st, nx, ny) - 1.0), (nr, 80.0)], 20, nx, s * ny), "nostril", coll))
    boolean(head, adds, "UNION")
    boolean(head, cuts, "DIFFERENCE")
    return head


def build_seg(k, cfg, coll):
    """Segment k in its own frame (front joint at the origin, +x toward the tail), before
    any joint cuts. Returns (body, limbs)."""
    name, L, st, sp = SEGS[k]
    hw_out = cfg["hw"][k + 1] if k + 1 < len(cfg["hw"]) else None
    st = list(st)
    if hw_out:
        st[-1] = (L, max(st[-1][1], hw_out), st[-1][2], st[-1][3])
    body = loft(st, coll, name)
    adds = []
    if hw_out:
        adds.append(housing((L, 0.0), hw_out, st[-1][2], coll))
    if sp:
        adds.append(spike(st, 0.5 * L, sp, coll))
    boolean(body, adds, "UNION")
    limbs = []
    if name == "hips":
        limbs = both_sides(lambda: leg(coll))
    elif name == "chest":
        limbs = both_sides(lambda: arm(coll))
    return body, limbs


class Plan:
    pass


def scale_design(s):
    """Scale the design dictionaries by s (in place on copies)."""
    def st(lst):
        return [(a * s, b * s, c * s, d * s) for (a, b, c, d) in lst]
    g = globals()
    g["HEAD"] = dict(_HEAD0, st=st(_HEAD0["st"]), eye=tuple(v * s for v in _HEAD0["eye"]),
                     nostril=tuple(v * s for v in _HEAD0["nostril"]), teeth=[x * s for x in _HEAD0["teeth"]],
                     crown=[(x * s, h * s) for (x, h) in _HEAD0["crown"]])
    g["SEGS"] = [(n, L * s, st(stt), sp * s) for (n, L, stt, sp) in _SEGS0]

    def sc(v):
        if isinstance(v, (int, float)):
            return v * s
        return type(v)(sc(x) for x in v)
    g["LEG"] = {k: sc(v) for k, v in _LEG0.items()}
    g["LEG"]["thigh"] = g["LEG"]["thigh"][:5] + (_LEG0["thigh"][5],)      # (the angle stays)
    g["ARM"] = {k: sc(v) for k, v in _ARM0.items()}


def generate(user=None, verbose=True):
    cfg = dict(SETTINGS)
    cfg.update(PRESETS[(user or {}).get("preset", SETTINGS["preset"])])
    cfg.update({k: v for k, v in (user or {}).items() if v is not None})
    scale_design(cfg["s"])
    # housings scale too, but never below what the knob needs
    cfg["hw"] = [max(h * cfg["s"], cfg["hw_min"]) for h in HOUSING]
    # every segment must be long enough for the cup at its front and the housing at its back
    segs = []
    for k, (nm, L, st, sp) in enumerate(SEGS):
        if k + 1 < len(SEGS):
            need = cfg["hw"][k] + GAP + cfg["hw"][k + 1] + 1.6
            if L < need:
                f = need / L
                L, st = need, [(x * f, w, hs, ht) for (x, w, hs, ht) in st]
        segs.append((nm, L, st, sp))
    globals()["SEGS"] = segs
    coll = get_collection()
    n = len(SEGS)

    # ---- layout: pivots and headings along the chain
    heads, pivots = [HEAD_HEADING + 180.0], [(0.0, 0.0)]   # heads[i]: axis of part i (+x toward the tail)
    for k in range(n):
        heads.append(heads[-1] + CURL[k])
        if k + 1 < n:
            d = dirv(heads[-1])
            pivots.append((pivots[-1][0] + SEGS[k][1] * d[0], pivots[-1][1] + SEGS[k][1] * d[1]))
    names = ["head"] + [s[0] for s in SEGS]
    J = []
    for k in range(n):
        J.append(Joint(SEGS[k][0], names[k], names[k + 1], pivots[k], heads[k + 1], (-THETA, THETA),
                       cfg["hw"][k], cfg))
    alpha = 90.0 - THETA - MARGIN

    def place(ob, pivot, heading):
        transform_obj(ob, Matrix.Translation((pivot[0], pivot[1], 0.0)) @ Matrix.Rotation(math.radians(heading), 4, "Z"))
        return ob

    if verbose:
        print("[gemscale] building parts ...")
    # ---- head (F of the first joint): stays behind the neck joint
    head = place(build_head(cfg, coll), pivots[0], heads[0])
    parts = [head]
    # ---- segments
    for k in range(n):
        body, limbs = build_seg(k, cfg, coll)
        for ob in [body] + limbs:
            place(ob, pivots[k], heads[k + 1])
        jin = J[k]
        boolean(body, [jin.wedge(coll, -alpha, alpha)], "INTERSECT")    # the chevron front
        if limbs:
            boolean(body, limbs, "UNION")
        boolean(body, [jin.disc(coll, jin.rho)], "DIFFERENCE")            # the cup
        parts.append(body)

    # ---- joint cuts: F keeps out of R's swing, then socket + notch in F, knob + tongue on R
    for k, j in enumerate(J):
        F = parts[k]
        keep = j.wedge(coll, -90.0, 90.0)
        boolean(keep, [j.disc(coll, j.hw)], "DIFFERENCE", tidy=False)
        boolean(F, [keep], "DIFFERENCE")
        boolean(F, j.f_cutters(coll), "DIFFERENCE")
    for k, j in enumerate(J):
        boolean(parts[k + 1], j.r_addons(coll), "UNION")
    if cfg["keyring"]:
        tip = parts[-1]
        L = SEGS[-1][1]
        d = dirv(heads[-1])
        r_out = 3.6 * max(cfg["s"], 0.8)
        c = (pivots[-1][0] + (L + r_out - 1.6) * d[0], pivots[-1][1] + (L + r_out - 1.6) * d[1])
        h = rup(2.8)
        boolean(tip, [link_obj(bm_lathe([(r_out, 0.0), (r_out, h - 0.4), (r_out - 0.4, h)], 40, c[0], c[1]), "tab", coll),
                      bar((pivots[-1][0] + (L - 4.0) * d[0], pivots[-1][1] + (L - 4.0) * d[1]), c, 2.4, 2.4, h, h, coll)],
                "UNION")
        boolean(tip, [link_obj(bm_lathe([(1.8, -1.0), (1.8, 80.0)], 32, c[0], c[1]), "hole", coll)], "DIFFERENCE")

    plan = Plan()
    plan.cfg, plan.joints, plan.coll = cfg, J, coll
    plan.parts, plan.names = parts, names
    plan.tints = [k / n for k in range(n + 1)]
    for nm, ob in zip(names, parts):
        ob.name = "trex_" + nm
        keep_main_islands(ob)
        weld(ob)
        triangulate(ob)
    # centre on the bed
    lo, hi = bounds(parts)
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    T = Matrix.Translation((-cx, -cy, 0.0))
    for ob in parts:
        transform_obj(ob, T)
    for j in J:
        j.pivot = (j.pivot[0] - cx, j.pivot[1] - cy)
    plan.subtree = {j.name: names[k + 1:] for k, j in enumerate(J)}
    if verbose:
        lo, hi = bounds(parts)
        print(f"[gemscale] built {len(parts)} parts, {len(J)} joints, "
              f"{hi.x - lo.x:.1f} x {hi.y - lo.y:.1f} x {hi.z:.1f} mm")
    return plan


def bounds(objs):
    vs = [ob.matrix_world @ v.co for ob in objs for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi


# =============================================================================
# 6. CHECKS
# =============================================================================

def check(plan, verbose=True):
    cfg, parts, J = plan.cfg, plan.parts, plan.joints
    names = plan.names
    idx = {n: i for i, n in enumerate(names)}
    res, ok = [], True

    def rep(name, passed, msg):
        nonlocal ok
        ok &= bool(passed)
        res.append(f"[{'PASS' if passed else 'FAIL'}] {name}: {msg}")

    bad, shells = [], []
    for ob in parts:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        if not _is_closed(bm):
            bad.append(names[parts.index(ob)])
        bm.verts.index_update()
        if len(mesh_islands(bm)) != 1:
            shells.append(names[parts.index(ob)])
        bm.free()
    rep("solids", not bad, "all parts are closed manifolds" if not bad else f"open: {bad}")
    rep("one piece each", not shells, "every part is a single connected piece" if not shells else f"split: {shells}")

    trees = [bvh_of(ob) for ob in parts]
    linked = {(idx[j.F], idx[j.R]) for j in J}
    worst_j, worst_o, pair, jpair = 9.0, 9.0, None, None
    for a in range(len(parts)):
        for b in range(a + 1, len(parts)):
            (ta, pa), (tb, pb) = trees[a], trees[b]
            if ta.overlap(tb):
                g = 0.0
            else:
                g = min(_nearest(tb, pa, 1.5), _nearest(ta, pb, 1.5))
            if (a, b) in linked or (b, a) in linked:
                if g < worst_j:
                    worst_j, jpair = g, (names[a], names[b])
            elif g < worst_o:
                worst_o, pair = g, (names[a], names[b])
    c = cfg["clearance"]
    rep("joint gaps", worst_j >= c - 0.05, f"smallest gap inside a joint {worst_j:.2f} mm (design {c:.2f})"
        + (f" ({jpair[0]} / {jpair[1]})" if jpair else ""))
    rep("part gaps", worst_o >= 0.4, f"smallest gap between unlinked parts {min(worst_o, 1.5):.2f} mm"
        + (f" ({pair[0]} / {pair[1]})" if worst_o < 1.5 else " (>= 1.5)"))

    # every joint swings through its whole range: everything beyond it, against everything else
    worst_s, at = 9.0, None
    for j in J:
        moving = [idx[n] for n in plan.subtree[j.name]]
        still = [i for i in range(len(parts)) if i not in moving]
        piv = Vector((j.pivot[0], j.pivot[1], 0.0))
        n = max(4, int((j.hi - j.lo) / 3.0))
        for k in range(n + 1):
            a = j.lo + (j.hi - j.lo) * k / n
            if abs(a) < 1e-6:
                continue
            Mr = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(a), 4, "Z") @ Matrix.Translation(-piv)
            for m in moving:
                tm, pm = bvh_of(parts[m], Mr)
                for st in still:
                    ts, ps = trees[st]
                    g = 0.0 if tm.overlap(ts) else min(_nearest(ts, pm, 0.6), _nearest(tm, ps, 0.6))
                    if g < worst_s:
                        worst_s, at = g, (j.name, names[m], names[st], a)
    rep("joint swing", worst_s >= 0.25,
        f"every joint wiggles +-{THETA:.0f} deg; smallest gap while "
        f"swinging {min(worst_s, 0.6):.2f} mm" + (f" ({at[1]} vs {at[2]} at {at[3]:+.0f} deg)" if at else ""))

    # overhangs: faces pointing down steeper than 45 deg, not on the bed, not tongue bridges
    zb = {round(j.z_n, 3) for j in J}
    over = bridge = 0.0
    for ob in parts:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.normal_update()
        for f in bm.faces:
            if f.normal.z > -0.72:
                continue
            zc = f.calc_center_median().z
            if zc < 0.02:
                continue
            if f.normal.z < -0.999 and any(abs(zc - z) < 0.01 for z in zb):
                bridge += f.calc_area()
            else:
                over += f.calc_area()
        bm.free()
    rep("overhangs", over < 4.0, f"{over:.1f} mm^2 of unsupported overhang; {bridge:.0f} mm^2 of short tongue bridges")

    lo, hi = bounds(parts)
    bx, by = cfg["bed"]
    rep("bed", hi.x - lo.x <= bx - 10 and hi.y - lo.y <= by - 10,
        f"{hi.x - lo.x:.1f} x {hi.y - lo.y:.1f} mm on a {bx} x {by} bed")

    # socket walls: the housing must stand at least up to the notch floor all round the socket
    thin = []
    for j in J:
        F = parts[idx[j.F]]
        tree, _ = trees[idx[j.F]]
        r = j.r_e + j.c + WALL * 0.6
        for i in range(24):
            a = TAU * i / 24
            p = Vector((j.pivot[0] + r * math.cos(a), j.pivot[1] + r * math.sin(a), 50.0))
            hit = tree.ray_cast(p, Vector((0, 0, -1)))
            rel = math.degrees(a) - j.heading
            rel = (rel + 180.0) % 360.0 - 180.0
            in_notch = j.lo - 15.0 <= rel <= j.hi + 15.0
            if not in_notch and (hit[0] is None or hit[0].z < j.z_nf - 0.05):
                thin.append(j.name)
                break
        del F
    rep("socket walls", not thin, "every housing surrounds its socket" if not thin else f"thin housing: {thin}")

    merged = []
    for ob in parts:
        vs = {(round(float(v.co.x), 5), round(float(v.co.y), 5), round(float(v.co.z), 5)) for v in ob.data.vertices}
        import array
        f32 = {tuple(array.array("f", k)) for k in vs}
        if len(f32) != len(ob.data.vertices):
            merged.append(names[parts.index(ob)])
    rep("stl precision", not merged, "no vertices merge when saved as float32 STL"
        if not merged else f"near-duplicate vertices in {merged}")

    # watertight as exported: every edge of the float32 triangle soup is shared by exactly 2
    leaky = {}
    for name, ob in zip(names, parts):
        n = len(export_edge_faults(ob))
        if n:
            leaky[name] = n
    rep("watertight", not leaky, "every part is watertight as written to the STL/3MF"
        if not leaky else f"open edges: {leaky}")

    if verbose:
        print("\n".join(res))
    return ok, res


def export_edge_faults(ob):
    import array
    me = ob.data
    me.calc_loop_triangles()
    key = [tuple(array.array("f", ob.matrix_world @ v.co)) for v in me.vertices]
    count = {}
    for lt in me.loop_triangles:
        a, b, c = (key[i] for i in lt.vertices)
        for e in ((a, b), (b, c), (c, a)):
            if e[0] != e[1]:
                k = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
                count[k] = count.get(k, 0) + 1
    return [k for k, v in count.items() if v != 2]


def _nearest(tree, pts, cap):
    best = cap
    for p in pts:
        r = tree.find_nearest(p, best)
        if r[0] is not None and r[3] < best:
            best = r[3]
    return best


# =============================================================================
# 7. EXPORT
# =============================================================================

def _tris(objs):
    out = []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        co = [ob.matrix_world @ v.co for v in me.vertices]
        out += [(co[a], co[b], co[c]) for (a, b, c) in (lt.vertices for lt in me.loop_triangles)]
    return out


def write_stl(objs, path):
    tris = _tris(objs)
    with open(path, "wb") as f:
        f.write(b"Gemscale Flexi T-Rex (mm)".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z, 0))


def write_3mf(objs, path, title):
    verts, tris = [], []
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        base = len(verts)
        verts += [tuple(ob.matrix_world @ v.co) for v in me.vertices]
        tris += [tuple(base + i for i in lt.vertices) for lt in me.loop_triangles]
    vx = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
    tx = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
             f'<metadata name="Title">{title}</metadata>\n<resources>\n<object id="1" type="model" name="{title}">'
             f'<mesh>\n<vertices>\n{vx}\n</vertices>\n<triangles>\n{tx}\n</triangles>\n</mesh></object>\n'
             '</resources>\n<build><item objectid="1"/></build>\n</model>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
          'relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-'
          '3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.'
            'microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def volume(objs):
    v = 0.0
    for ob in objs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        v += abs(bm.calc_volume())
        bm.free()
    return v


def export(plan, results, out_dir=None, glb=True):
    cfg = plan.cfg
    out = out_dir or cfg["out"]
    if out.startswith("//"):
        base = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
        out = os.path.join(base, out[2:])
    os.makedirs(out, exist_ok=True)
    stem = f"GemscaleTRex_{cfg['preset']}"
    if cfg["keyring"]:
        stem += "_keyring"
    if abs(cfg["clearance"] - 0.35) > 1e-6:
        stem += f"_clearance{cfg['clearance']:.2f}".replace(".", "p")
    write_stl(plan.parts, os.path.join(out, stem + ".stl"))
    write_3mf(plan.parts, os.path.join(out, stem + ".3mf"), f"Gemscale Flexi T-Rex ({cfg['preset']})")
    if glb:
        # per-part GLB + part list for the three.js render studio in render/
        old = [ob.name for ob in plan.parts]
        tags = plan.names
        bpy.ops.object.select_all(action="DESELECT")
        for i, ob in enumerate(plan.parts):
            ob.name = f"p{i}"
            ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(out, stem + ".glb"), export_format="GLB",
                                  use_selection=True, export_yup=False, export_apply=True,
                                  export_normals=True, export_materials="NONE")
        for ob, n in zip(plan.parts, old):
            ob.name = n
        with open(os.path.join(out, stem + "_parts.json"), "w") as fh:
            json.dump([dict(name=n, t=t, smooth=True) for n, t in zip(tags, plan.tints)], fh)
    vol = volume(plan.parts)
    area = sum(sum(f.area for f in ob.data.polygons) for ob in plan.parts)
    shell = min(vol, area * 0.84)
    grams = (shell + 0.15 * (vol - shell)) * 1.24e-3
    lo, hi = bounds(plan.parts)
    report = [f"Gemscale Flexi T-Rex  preset={cfg['preset']}  clearance={cfg['clearance']:.2f}  "
              f"(Blender {bpy.app.version_string})",
              f"size {hi.x - lo.x:.1f} x {hi.y - lo.y:.1f} x {hi.z:.1f} mm, {len(plan.parts)} parts, "
              f"{len(plan.joints)} joints",
              f"solid volume {vol / 1000:.1f} cm^3, estimated {grams:.0f} g PLA (2 walls, 15 % infill)", ""] + results
    with open(os.path.join(out, stem + "_report.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print(f"[gemscale] wrote {os.path.join(out, stem)}.stl / .3mf")
    return stem


# =============================================================================
# 8. UI PANEL (when run inside Blender)
# =============================================================================

class GEMSCALE_PG_trex(bpy.types.PropertyGroup):
    preset: bpy.props.EnumProperty(items=[("standard", "Standard", "full size"),
                                          ("mini", "Mini", "smaller and quicker")], default="standard")
    clearance: bpy.props.FloatProperty(name="Clearance", default=0.35, min=0.25, max=0.6, step=1)
    keyring: bpy.props.BoolProperty(name="Keyring loop", default=False)
    out: bpy.props.StringProperty(name="Export to", default="//gemscale_export", subtype="DIR_PATH")
    status: bpy.props.StringProperty(default="")


_LAST = {}


class GEMSCALE_OT_trex_generate(bpy.types.Operator):
    bl_idname = "gemscale.trex_generate"
    bl_label = "Generate T-Rex"

    def execute(self, context):
        p = context.scene.gemscale_trex
        plan = generate(dict(preset=p.preset, clearance=p.clearance, keyring=p.keyring, out=p.out))
        ok, res = check(plan)
        _LAST.update(plan=plan, res=res)
        p.status = "All checks passed" if ok else "Some checks FAILED (see console)"
        return {"FINISHED"}


class GEMSCALE_OT_trex_export(bpy.types.Operator):
    bl_idname = "gemscale.trex_export"
    bl_label = "Export STL + 3MF"

    def execute(self, context):
        if "plan" not in _LAST:
            self.report({"ERROR"}, "Generate first")
            return {"CANCELLED"}
        export(_LAST["plan"], _LAST["res"], glb=False)
        return {"FINISHED"}


class GEMSCALE_PT_trex(bpy.types.Panel):
    bl_label = "Gemscale T-Rex"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gemscale"

    def draw(self, context):
        p = context.scene.gemscale_trex
        col = self.layout.column()
        for k in ("preset", "clearance", "keyring", "out"):
            col.prop(p, k)
        col.operator("gemscale.trex_generate")
        col.operator("gemscale.trex_export")
        if p.status:
            col.label(text=p.status)


CLASSES = (GEMSCALE_PG_trex, GEMSCALE_OT_trex_generate, GEMSCALE_OT_trex_export, GEMSCALE_PT_trex)


def register():
    if hasattr(bpy.types.Scene, "gemscale_trex"):     # running the script again: re-register
        unregister()
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.gemscale_trex = bpy.props.PointerProperty(type=GEMSCALE_PG_trex)


def unregister():
    del bpy.types.Scene.gemscale_trex
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)


# =============================================================================
# 9. COMMAND LINE
# =============================================================================

def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Gemscale Flexi T-Rex generator")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="standard")
    ap.add_argument("--clearance", type=float, default=0.35)
    ap.add_argument("--keyring", action="store_true")
    ap.add_argument("--out", default="gemscale_export")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--save", help="also save a .blend file")
    a = ap.parse_args(argv)
    if bpy.data.objects.get("Cube"):
        delete_obj(bpy.data.objects["Cube"])
    plan = generate(dict(preset=a.preset, clearance=a.clearance, keyring=a.keyring, out=a.out))
    ok, res = (True, []) if a.no_check else check(plan)
    export(plan, res, a.out)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    return 0 if ok else 1


if __name__ == "__main__":
    if bpy.app.background or "--" in sys.argv or not hasattr(bpy.types, "VIEW3D_PT_tools_active"):
        args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
        sys.exit(main(args))
    else:
        register()
