"""
Gemscale Flexi T-Rex: Blender generator for a quick, print-in-place T. rex that chomps.

The T. rex is sculpted from metaball "muscle masses" (skull, cheeks, brow, neck, chest,
belly, thighs, a striding pair of legs, tiny arms and a long tapering tail) that blend into
one smooth organic body, plus a separate lower jaw. Teeth and claws are half-cones, the eye
is a dome with a slit pupil.

Every metaball centre lies on the T. rex's mid-plane, and the model is that body cut in half
along the mid-plane and laid flat on the bed. A sum of blobs centred on z = 0 falls off with
|z|, so the top surface is a pure height field: the model CAN'T have an overhang, prints
with no supports, and is low (12 mm), so it prints fast.

It is jointed with the same captured knob-in-socket swivel as the other Gemscale models:
the jaw opens (it chomps), the head nods and the four-part tail wiggles. Each part's
clearance cut is the exact swept volume of everything beyond its joint, so cuts follow the
shapes instead of being blunt wedges.

Run it
    blender -b -P gemscale_trex.py -- --preset standard --out models
    python gemscale_trex.py --preset mini --keyring --out models     (pip install bpy)
or open it in Blender's Scripting tab and press Run Script: a "Gemscale" tab appears in the
3D-viewport sidebar (N) with Generate / Export buttons.
"""

bl_info = {
    "name": "Gemscale Flexi T-Rex",
    "author": "Gemscale",
    "version": (2, 0, 0),
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
from mathutils import Matrix, Quaternion, Vector
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
MB0 = 0.5747    # an isolated metaball's semi-axis is MB0 * radius * size (threshold 0.6)

NECK = (-15.0, 15.0)    # the head (with the neck) nods
JAW = (0.0, 30.0)       # the jaw opens from its printed (slightly open) pose
TAIL = (-28.0, 28.0)    # each tail joint wiggles

PRESETS = {
    # s: design units -> mm; hz: extra height scale; res: metaball resolution (mm)
    "standard": dict(s=0.80, hz=0.90, res=0.45, r_n=1.5, r_e=2.35, band=0.7,
                     hw=dict(neck=4.6, jaw=4.4, hip=4.6, t1=4.3, t2=4.0), hw_max=8.0, bed=(180, 180)),
    "mini": dict(s=0.60, hz=1.10, res=0.36, r_n=1.3, r_e=2.05, band=0.6,
                 hw=dict(neck=3.9, jaw=3.8, hip=3.9, t1=3.7, t2=3.6), hw_max=6.0, bed=(180, 180)),
}

SETTINGS = dict(preset="standard", clearance=0.35, keyring=False, out="//gemscale_export")


# =============================================================================
# 2. ANATOMY (design units: facing LEFT, ground at y = 0, z = half body thickness)
# =============================================================================

def _ang(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def anatomy():
    """Metaball ellipsoids (x, y, ax, ay, az, angle) for the body and the jaw, the details,
    and the joint pivots."""
    body, jaw = [], []

    def el(lst, x, y, ax, ay, az, ang=0.0):
        lst.append((x, y, ax, ay, az, ang))

    def limb(lst, p, q, r0, r1, z0, z1, n):
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        a = _ang(p, q)
        for i in range(n):
            t = i / (n - 1)
            r = r0 + (r1 - r0) * t
            el(lst, p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t,
               max(r, 0.9 * ln / (n - 1)), r, z0 + (z1 - z0) * t, a)

    # --- head: deep cranium, back of the skull, snout, cheek (jaw muscle), brow horn, nasal ridge
    el(body, -40.0, 64.5, 13.5, 11.5, 12.0, -6)
    el(body, -31.0, 62.5, 7.0, 9.5, 11.5, 0)
    el(body, -55.0, 60.0, 12.0, 7.8, 9.8, -8)
    el(body, -67.0, 57.8, 7.0, 5.8, 7.2, -10)
    el(body, -34.0, 55.5, 8.0, 8.0, 10.5, 0)
    el(body, -46.0, 70.6, 5.0, 2.5, 13.2, -25)
    el(body, -42.5, 72.2, 2.2, 1.7, 12.8, 0)
    el(body, -61.0, 62.8, 5.0, 2.0, 9.8, -10)
    # --- neck: a dip behind the skull, then thick down to the chest
    el(body, -25.0, 57.0, 7.0, 8.5, 9.8, 40)
    el(body, -18.0, 51.0, 8.5, 9.5, 11.0, 45)
    # --- body: chest, belly, hips
    el(body, -11.0, 43.0, 13.0, 12.5, 12.5, 15)
    el(body, 4.0, 40.5, 16.0, 13.0, 13.5, 5)
    el(body, 19.0, 44.0, 12.0, 11.5, 12.5, 0)
    # --- near leg: big drumstick thigh, shin, long foot
    el(body, 13.0, 31.0, 14.0, 9.5, 13.5, -75)
    limb(body, (7.0, 21.0), (12.0, 7.5), 5.0, 3.6, 8.5, 6.5, 6)
    limb(body, (12.0, 5.2), (-6.0, 3.4), 3.6, 2.7, 6.0, 4.6, 8)
    # --- far leg striding forward, in lower relief behind
    el(body, -3.0, 31.0, 12.0, 8.0, 7.5, -110)
    limb(body, (-9.0, 20.0), (-14.0, 7.5), 4.0, 3.0, 6.0, 4.6, 5)
    limb(body, (-14.0, 5.0), (-30.0, 3.2), 3.0, 2.4, 4.6, 3.6, 7)
    # --- tiny arms (of course)
    limb(body, (-21.0, 34.0), (-27.0, 27.5), 2.7, 2.2, 5.2, 4.6, 4)
    limb(body, (-27.0, 27.5), (-33.0, 30.0), 2.2, 1.9, 4.6, 4.0, 4)
    # --- tail: thick at the hips, tapering to a point, held up
    tp = [(28.0, 46.0), (43.0, 48.8), (57.0, 51.8), (71.0, 54.3), (85.0, 56.3), (98.0, 58.0)]
    tr = [10.5, 8.6, 7.4, 6.4, 4.5, 2.0]
    tz = [12.5, 10.5, 9.2, 8.0, 6.0, 3.6]
    for k in range(len(tp) - 1):
        limb(body, tp[k], tp[k + 1], tr[k], tr[k + 1], tz[k], tz[k + 1], 6)

    # --- lower jaw (a separate part), printed slightly open so the teeth show
    el(jaw, -37.5, 49.5, 6.0, 5.0, 8.0, 18)
    el(jaw, -48.0, 44.6, 10.0, 3.6, 6.4, 20)
    el(jaw, -60.0, 40.8, 5.8, 3.3, 5.6, 18)

    det = dict(
        # upper teeth hang from the skull, lower teeth stand on the jaw: (x, length, radius)
        upper=[(-65.0, 3.0, 1.3), (-59.5, 3.6, 1.45), (-54.0, 3.3, 1.35), (-48.5, 3.0, 1.25), (-43.0, 2.5, 1.1)],
        lower=[(-57.0, 2.5, 1.15), (-51.5, 2.8, 1.25), (-46.0, 2.5, 1.15)],
        eye=(-47.5, 65.2, 3.7), nostril=(-68.0, 59.8, 1.0),
        # claws: (x, y, direction deg, length, radius)
        claws=[(-6.0, 3.6, 188, 4.2, 1.5), (-5.0, 5.3, 168, 3.4, 1.2),
               (-30.0, 3.4, 190, 3.6, 1.3), (-29.0, 4.8, 170, 2.8, 1.0),
               (-33.0, 30.6, 175, 2.8, 0.9), (-32.6, 28.6, 205, 2.6, 0.85)],
        tail_tip=(98.0, 58.0),
    )
    pv = dict(neck=(-16.5, 51.0), jaw=(-35.0, 50.5), hip=(30.0, 46.4),
              t1=(50.0, 50.2), t2=(68.0, 53.6))
    return body, jaw, det, pv


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


def cut_below_zero(bm):
    """Keep z >= 0 and close the cut with flat faces (the bed side)."""
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
                           plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
    bnd = [e for e in bm.edges if e.is_boundary]
    if bnd:
        bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    for v in bm.verts:
        if abs(v.co.z) < 1e-4:
            v.co.z = 0.0
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def half_cone(base, ang, length, rb, zs=2.2, embed=1.2, segs=24):
    """Tooth / claw: the top half of a cone lying on the bed (a height field), pointing
    along `ang` from `base`, sunk `embed` mm into whatever it grows from."""
    bm = bm_lathe([(rb, 0.0), (0.62 * rb, 0.55 * (length + embed)), (0.08, length + embed)], segs)
    bm.transform(Matrix.Diagonal((1.0, zs, 1.0, 1.0)))         # deeper than wide (taller on the bed)
    bm.transform(Matrix.Rotation(math.radians(90.0), 4, "Y"))  # axis z -> x, local y -> world z
    bm.transform(Matrix.Rotation(math.radians(-90.0), 4, "X"))
    bm.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))
    bx, by = base[0] - embed * math.cos(math.radians(ang)), base[1] - embed * math.sin(math.radians(ang))
    bm.transform(Matrix.Translation((bx, by, 0.0)))
    return cut_below_zero(bm)


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


def metaball_mesh(name, elems, res, coll, s, hz):
    """Blend ellipsoids (design units) into one smooth mesh in mm, cut to z >= 0."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = mb.render_resolution = res
    mb.threshold = 0.6
    ob = bpy.data.objects.new(name, mb)       # unique name: metaballs merge by base name
    coll.objects.link(ob)
    for (x, y, ax, ay, az, ang) in elems:
        ax, ay, az = ax * s, ay * s, az * s * hz
        R = max(ax, ay, az) / MB0
        e = mb.elements.new(type="ELLIPSOID")
        e.co = (x * s, y * s, 0.0)
        e.radius = R
        e.size_x, e.size_y, e.size_z = ax / (MB0 * R), ay / (MB0 * R), az / (MB0 * R)
        e.rotation = Quaternion((0.0, 0.0, 1.0), math.radians(ang))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    return link_obj(cut_below_zero(bm), name, coll)


def ray_y(ob, x, y0, dy, z=0.6):
    """First hit of a ray in the print plane, from (x, y0) along +/-y."""
    tree, _ = bvh_of(ob)
    hit = tree.ray_cast(Vector((x, y0, z)), Vector((0.0, 1.0 if dy > 0 else -1.0, 0.0)))
    return hit[0].y if hit[0] is not None else None


def height_at(ob, x, y):
    tree, _ = bvh_of(ob)
    hit = tree.ray_cast(Vector((x, y, 200.0)), Vector((0.0, 0.0, -1.0)))
    return hit[0].z if hit[0] is not None else 0.0


class Plan:
    pass


def generate(user=None, verbose=True):
    cfg = dict(SETTINGS)
    cfg.update(PRESETS[(user or {}).get("preset", SETTINGS["preset"])])
    cfg.update({k: v for k, v in (user or {}).items() if v is not None})
    s, hz = cfg["s"], cfg["hz"]
    coll = get_collection()
    body_e, jaw_e, det, pv = anatomy()

    def P(p):
        return (p[0] * s, p[1] * s)

    if verbose:
        print("[gemscale] sculpting the body ...")
    M = metaball_mesh("trexBody", body_e, cfg["res"], coll, s, hz)
    Jb = metaball_mesh("trexJaw", jaw_e, cfg["res"], coll, s, hz)

    # ---- details: teeth, claws, eye, nostril, keyring
    adds_m, adds_j, cuts_m = [], [], []
    for (x, ln, rb) in det["upper"]:
        y = ray_y(M, x * s, 46.5 * s, +1)            # underside of the skull at x
        if y is not None:
            adds_m.append(link_obj(half_cone((x * s, y), 268.0, ln * s, rb * s), "tooth", coll))
    for (x, ln, rb) in det["lower"]:
        y = ray_y(Jb, x * s, 52.0 * s, -1)           # top edge of the jaw at x
        if y is not None:
            adds_j.append(link_obj(half_cone((x * s, y), 92.0, ln * s, rb * s), "tooth", coll))
    for (x, y, a, ln, rb) in det["claws"]:
        adds_m.append(link_obj(half_cone((x * s, y * s), a, ln * s, rb * s, zs=1.8), "claw", coll))
    ex, ey, er = det["eye"]
    ex, ey, er = ex * s, ey * s, er * s
    zc = height_at(M, ex, ey) - 0.45 * er
    prof = [(er, 0.0), (er, zc)] + [(er * math.cos(math.radians(a)), zc + er * math.sin(math.radians(a)))
                                    for a in range(15, 90, 15)] + [(0.25, zc + er - 0.02)]
    adds_m.append(link_obj(bm_lathe(prof, 48, ex, ey), "eye", coll))
    # slit pupil: a vertical diamond, slanted, cut 0.9 mm into the eye dome
    w2, h2, a = 0.3 * er, 0.62 * er, math.radians(-20.0)
    dia = [(ex + px * math.cos(a) - py * math.sin(a), ey + px * math.sin(a) + py * math.cos(a))
           for (px, py) in ((w2, 0.0), (0.0, h2), (-w2, 0.0), (0.0, -h2))]
    cuts_m.append(link_obj(bm_prism(dia, zc + er - 0.9, 80.0), "pupil", coll))
    nx, ny, nr = det["nostril"]
    zn = height_at(M, nx * s, ny * s)
    cuts_m.append(link_obj(bm_lathe([(nr * s, zn - 1.0), (nr * s, 80.0)], 24, nx * s, ny * s), "nostril", coll))
    if cfg["keyring"]:
        tx, ty = P(det["tail_tip"])
        h = rup(3.0)
        r_out = 4.0 * max(s / 0.8, 0.8)
        c = (tx + r_out - 2.0, ty + 0.5)
        tab = bm_lathe([(r_out, 0.0), (r_out, h - 0.4), (r_out - 0.4, h)], 48, c[0], c[1])
        adds_m.append(link_obj(tab, "tab", coll))
        cuts_m.append(link_obj(bm_lathe([(1.8, -1.0), (1.8, 80.0)], 32, c[0], c[1]), "hole", coll))
    boolean(M, adds_m, "UNION")
    boolean(M, cuts_m, "DIFFERENCE")
    boolean(Jb, adds_j, "UNION")

    if cfg.get("preview"):
        # shape only (no joints), for working on the sculpt
        plan = Plan()
        plan.cfg, plan.joints, plan.coll = cfg, [], coll
        plan.parts, plan.names, plan.tints = [M, Jb], ["body", "jaw"], [0.3, 0.0]
        return plan

    # ---- joints
    hw = cfg["hw"]

    def hd(a, b):
        return _ang(P(pv[a]), P(pv[b]) if isinstance(b, str) else P(b))

    jaw_head = _ang(P(pv["jaw"]), P((-60.0, 40.6)))
    J = [Joint("neck", "body", "head", P(pv["neck"]), _ang(P(pv["neck"]), P((-42.0, 63.0))), NECK, hw["neck"], cfg,
               split=(-90.0, 55.0)),
         Joint("jaw", "head", "jaw", P(pv["jaw"]), jaw_head, JAW, hw["jaw"], cfg, source="jaw", split=(-90.0, 90.0)),
         Joint("hip", "body", "tail1", P(pv["hip"]), hd("hip", "t1"), TAIL, hw["hip"], cfg),
         Joint("t1", "tail1", "tail2", P(pv["t1"]), hd("t1", "t2"), TAIL, hw["t1"], cfg),
         Joint("t2", "tail2", "tip", P(pv["t2"]), hd("t2", det["tail_tip"]), TAIL, hw["t2"], cfg)]

    # big round knuckles: each housing fills the body's width at its pivot, so the next part
    # wraps round it in a matching cup and the joint sweeps almost nothing away
    tree, _ = bvh_of(M)
    for j in J:
        ds = []
        for side in (90.0, -90.0):
            d = dirv(j.heading + side)
            hit = tree.ray_cast(Vector((j.pivot[0], j.pivot[1], 0.3)), Vector((d[0], d[1], 0.0)))
            ds.append((hit[0].xy - Vector(j.pivot)).length if hit[0] is not None else j.hw)
        j.hw = max(j.hw, min(min(ds) - 0.6, cfg["hw_max"]))
    jn, jj = J[0], J[1]
    room = (Vector(jn.pivot) - Vector(jj.pivot)).length - 1.6
    if jn.hw + GAP + jj.hw > room:            # neck cup and jaw housing must not meet
        jn.hw = max(cfg["hw"]["neck"], room - GAP - jj.hw)
    chain = [j for j in J if j.name in ("hip", "t1", "t2")]
    for a, b in zip(chain[:-1], chain[1:]):     # a's cup and b's housing must fit between them
        room = (Vector(a.pivot) - Vector(b.pivot)).length - GAP - 1.8
        over = a.hw + b.hw - room
        if over > 0:
            a.hw -= over * a.hw / (a.hw + b.hw)
            b.hw -= over * b.hw / (a.hw + b.hw + over * b.hw / (a.hw + b.hw))
            b.hw = min(b.hw, room - a.hw)
    for j in J:
        j.rho = j.hw + GAP
    if verbose:
        print("[gemscale] housings:", ", ".join(f"{j.name} {j.hw:.1f}" for j in J))

    # ---- 1. split the body into parts along each joint's sector
    if verbose:
        print("[gemscale] splitting into parts ...")
    regions = {"body": M}
    for j in J:
        s0, s1 = j.sector()
        if j.source == "jaw":
            Rr = Jb
        else:
            Rr = copy_obj(regions[j.F], j.R)
            boolean(Rr, [j.wedge(coll, s0, s1)], "INTERSECT")
            w = j.wedge(coll, s0, s1)
            boolean(w, [j.disc(coll, j.hw)], "DIFFERENCE")
            boolean(regions[j.F], [w], "DIFFERENCE")
        boolean(Rr, [j.disc(coll, j.rho)], "DIFFERENCE")
        Rr.name = j.R
        regions[j.R] = Rr
    for ob in regions.values():
        keep_main_islands(ob)

    # every F gets a round boss at its joint, so the socket always has a full wall
    for j in J:
        hb = j.z_nf + 1.6
        boss = bm_lathe([(j.hw, 0.0), (j.hw, hb - 0.5), (j.hw - 0.5, hb)], 64, j.pivot[0], j.pivot[1])
        boolean(regions[j.F], [link_obj(boss, "boss", coll)], "UNION")

    # ---- 2. clear each joint's sweep: F loses the swept volume of everything beyond it
    if verbose:
        print("[gemscale] clearing joint sweeps ...")
    children = {}
    for j in J:
        children.setdefault(j.F, []).append(j.R)

    def subtree(name):
        out = [name]
        for c in children.get(name, []):
            out += subtree(c)
        return out

    for j in J:
        if os.environ.get("GEMSCALE_DEBUG"):
            for n in subtree(j.R):
                bm = bmesh.new()
                bm.from_mesh(regions[n].data)
                print("  ", j.name, n, len(bm.verts), "closed" if _is_closed(bm) else "OPEN", flush=True)
                bm.free()
        tool = sweep_tool(j, [regions[n] for n in subtree(j.R)], coll)
        disc = j.disc(coll, j.hw)
        boolean(tool, [disc], "DIFFERENCE", tidy=False)
        boolean(regions[j.F], [tool], "DIFFERENCE")
    for ob in regions.values():
        keep_main_islands(ob)

    # ---- 3. the joint hardware
    for j in J:
        boolean(regions[j.F], j.f_cutters(coll), "DIFFERENCE")
    for j in J:
        boolean(regions[j.R], j.r_addons(coll), "UNION")

    order = ["head", "jaw", "body", "tail1", "tail2", "tip"]
    tints = dict(head=0.0, jaw=0.08, body=0.25, tail1=0.5, tail2=0.75, tip=1.0)
    plan = Plan()
    plan.cfg, plan.joints, plan.coll = cfg, J, coll
    plan.parts = [regions[n] for n in order]
    plan.names = list(order)
    for n in order:
        regions[n].name = "trex_" + n
    plan.tints = [tints[n] for n in order]
    for ob in plan.parts:
        keep_main_islands(ob)
        weld(ob)
        triangulate(ob)
    # centre on the bed
    xs = [(ob.matrix_world @ v.co) for ob in plan.parts for v in ob.data.vertices]
    cx = (min(v.x for v in xs) + max(v.x for v in xs)) / 2
    cy = (min(v.y for v in xs) + max(v.y for v in xs)) / 2
    T = Matrix.Translation((-cx, -cy, 0.0))
    for ob in plan.parts:
        transform_obj(ob, T)
    for j in J:
        j.pivot = (j.pivot[0] - cx, j.pivot[1] - cy)
    plan.subtree = {j.name: subtree(j.R) for j in J}
    if verbose:
        lo, hi = bounds(plan.parts)
        print(f"[gemscale] built {len(plan.parts)} parts, {len(J)} joints, "
              f"{hi.x - lo.x:.1f} x {hi.y - lo.y:.1f} x {hi.z:.1f} mm")
    return plan


def sweep_tool(j, objs, coll, reach=22.0):
    """Union of copies of `objs` (each grown by GAP) rotated about the joint over its swing.
    Only what lies within `reach` of the pivot is swept (that is where F can be; the swing
    check covers the rest). Every part stays its own boolean operand: joining them would make
    one mesh with intersecting shells, which the Manifold solver can't take."""
    piv = Vector((j.pivot[0], j.pivot[1], 0.0))
    grow = GAP * 1.35
    bases = []
    for ob in objs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        if min((v.co - piv).xy.length for v in bm.verts) > reach:
            bm.free()
            continue
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * grow
            # stretch it up: the part is a height field, so this keeps its footprint and
            # makes the cut a vertical wall (nothing of F may hang over the swept zone)
            v.co.z = v.co.z * 40.0 if v.co.z > 0.0 else v.co.z
        base = link_obj(bm, "sweep_src", coll)
        clip = link_obj(bm_lathe([(reach, -5.0), (reach, 500.0)], 96, piv.x, piv.y), "clip", coll)
        boolean(base, [clip], "INTERSECT", tidy=False)
        if len(base.data.vertices) < 4:
            delete_obj(base)
            continue
        bases.append(base)
    step = min(2.0, math.degrees(0.45 / reach))
    n = max(2, int(math.ceil((j.hi - j.lo) / step)))
    if os.environ.get("GEMSCALE_DEBUG"):
        print(f"   sweep {j.name}: {len(bases)} parts x {n + 1} copies", flush=True)
    copies = []
    for base in bases:
        for i in range(n + 1):
            a = j.lo + (j.hi - j.lo) * i / n
            c = copy_obj(base, "sweep")
            Mr = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(a), 4, "Z") @ Matrix.Translation(-piv)
            transform_obj(c, Mr)
            copies.append(c)
        delete_obj(base)
    tool = copies.pop(0)
    boolean(tool, copies, "UNION", tidy=False)
    return tool


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
        f"jaw opens {JAW[1]:.0f} deg, head nods +-{NECK[1]:.0f}, tail joints +-{TAIL[1]:.0f}; smallest gap while "
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
    preset: bpy.props.EnumProperty(items=[("standard", "Standard", "14 cm long"),
                                          ("mini", "Mini", "10.5 cm long")], default="standard")
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
    ap.add_argument("--preview", action="store_true", help="sculpt only (no joints), fast")
    a = ap.parse_args(argv)
    if bpy.data.objects.get("Cube"):
        delete_obj(bpy.data.objects["Cube"])
    plan = generate(dict(preset=a.preset, clearance=a.clearance, keyring=a.keyring, out=a.out,
                         preview=a.preview))
    ok, res = (True, []) if (a.no_check or a.preview) else check(plan)
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
