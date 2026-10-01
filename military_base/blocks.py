"""Shared geometry builder for the military tycoon generators.

All coordinates passed to the builder are ROBLOX coordinates: x right, y up, z toward the
front gate.  The builder converts to Blender (x, -z, y) when it creates meshes.

Visual geometry is merged into one mesh per Group_Material (split into chunks so no mesh
exceeds MAX_TRIS).  Collision is recorded separately as axis-aligned boxes that
fit_base.lua turns into invisible Parts; the meshes themselves never collide.
"""
import math

import bmesh
import bpy
from mathutils import Vector

MAX_TRIS = 8500

# Palette: suffix -> (RGB 0-255, Roblox material).  Keep in sync with fit_base.lua.
PALETTE = {
    "Olive":        ((92, 104, 62),   "SmoothPlastic"),
    "DarkOlive":    ((60, 68, 44),    "SmoothPlastic"),
    "Concrete":     ((170, 166, 152), "Concrete"),
    "DarkConcrete": ((112, 110, 102), "Concrete"),
    "Asphalt":      ((50, 52, 55),    "Asphalt"),
    "Metal":        ((92, 96, 100),   "Metal"),
    "Steel":        ((150, 154, 158), "DiamondPlate"),
    "Hazard":       ((224, 178, 40),  "SmoothPlastic"),
    "Marking":      ((228, 224, 208), "SmoothPlastic"),
    "Sand":         ((178, 158, 114), "Sand"),
    "Wood":         ((122, 92, 60),   "WoodPlanks"),
    "Canvas":       ((130, 122, 90),  "Fabric"),
    "Rust":         ((128, 70, 44),   "CorrodedMetal"),
    "Black":        ((24, 24, 26),    "SmoothPlastic"),
    "Glass":        ((150, 190, 210), "Glass"),
    "Lamp":         ((255, 236, 180), "Neon"),
    "Beacon":       ((255, 44, 32),   "Neon"),
    "Shady":        ((150, 60, 255),  "Neon"),
}
NON_COLLIDE_MATS = {"Glass", "Lamp", "Beacon", "Shady"}
LIGHT_MATS = {"Lamp", "Beacon", "Shady"}


def b(p):
    """Roblox (x, y, z) -> Blender (x, -z, y)."""
    return (p[0], -p[2], p[1])


class Builder:
    def __init__(self):
        self.chunks = {}      # (group, mat) -> [ {v, f, tris} ]
        self.collide = []     # (cx, cy, cz, sx, sy, sz)
        self.prims = []       # (label, kind, (x0, x1, y0, y1, z0, z1))
        self.trusses = []     # (x, y0, z, height)
        self.lamps = []       # (object name, (x, y, z))
        self.nlamp = 0
        self.boxes = []       # visual axis-aligned boxes, for the coplanar check
        self.posts = set()    # rail post positions already placed (corners are shared)

    # ------------------------------------------------------------ low level
    def _add(self, g, m, verts_b, faces, tris, kind, aabb):
        lst = self.chunks.setdefault((g, m), [])
        if not lst or lst[-1]["tris"] + tris > MAX_TRIS:
            lst.append({"v": [], "f": [], "tris": 0})
        c = lst[-1]
        o = len(c["v"])
        c["v"].extend(verts_b)
        c["f"].extend([tuple(i + o for i in f) for f in faces])
        c["tris"] += tris
        self.prims.append((f"{g}_{m}", kind, aabb))

    def coll(self, x0, x1, y0, y1, z0, z1, label="Coll"):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        self.collide.append(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0))
        self.prims.append((label, "collision", (x0, x1, y0, y1, z0, z1)))

    # ------------------------------------------------------------ primitives
    def box(self, g, m, x0, x1, y0, y1, z0, z1, col=True, kind="solid"):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        if min(x1 - x0, y1 - y0, z1 - z0) <= 1e-6:
            return
        bx0, bx1, by0, by1, bz0, bz1 = x0, x1, -z1, -z0, y0, y1
        v = [(bx0, by0, bz0), (bx1, by0, bz0), (bx1, by1, bz0), (bx0, by1, bz0),
             (bx0, by0, bz1), (bx1, by0, bz1), (bx1, by1, bz1), (bx0, by1, bz1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(g, m, v, f, 12, kind, (x0, x1, y0, y1, z0, z1))
        self.boxes.append((f"{g}_{m}", (x0, x1, y0, y1, z0, z1)))
        if col and m not in NON_COLLIDE_MATS:
            self.coll(x0, x1, y0, y1, z0, z1, f"{g}_{m}")

    def decal(self, g, m, x0, x1, z0, z1, y=0.02, t=0.08):
        """Flat ground marking; never collides."""
        self.box(g, m, x0, x1, y, y + t, z0, z1, col=False, kind="decal")

    def hull(self, g, m, pts, kind="solid"):
        """Convex hull of Roblox-space points (visual only)."""
        bm = bmesh.new()
        vs = [bm.verts.new(b(p)) for p in pts]
        res = bmesh.ops.convex_hull(bm, input=vs)
        kill = [e for e in res["geom_interior"] + res["geom_unused"] if isinstance(e, bmesh.types.BMVert)]
        if kill:
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.verts.index_update()
        verts = [tuple(v.co) for v in bm.verts]
        faces = [tuple(v.index for v in f.verts) for f in bm.faces]
        tris = sum(len(f) - 2 for f in faces)
        bm.free()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        self._add(g, m, verts, faces, tris, kind, (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

    def cyl(self, g, m, cx, cz, y0, y1, r0, r1=None, segs=16, col=False, kind="solid"):
        """Vertical cylinder / frustum.  col=True adds an inscribed collision box."""
        r1 = r0 if r1 is None else r1
        pts = []
        for i in range(segs):
            a = 2 * math.pi * (i + 0.5) / segs
            pts.append((cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)))
            pts.append((cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)))
        self.hull(g, m, pts, kind)
        if col:
            h = min(r0, r1) * 0.72
            self.coll(cx - h, cx + h, y0, y1, cz - h, cz + h, f"{g}_{m}")

    def hcyl(self, g, m, axis, a0, a1, c1, cy, r, segs=12):
        """Horizontal cylinder along 'x' or 'z' (visual only).  c1 = the other horizontal coord."""
        pts = []
        for i in range(segs):
            t = 2 * math.pi * i / segs
            u, w = r * math.cos(t), r * math.sin(t)
            for a in (a0, a1):
                pts.append((a, cy + w, c1 + u) if axis == "x" else (c1 + u, cy + w, a))
        self.hull(g, m, pts)

    def beam(self, g, m, p0, p1, w, h=None):
        """Square/rect beam between two points (visual only)."""
        h = w if h is None else h
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized()
        a = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
        u = d.cross(a).normalized()
        v = d.cross(u).normalized()
        pts = [tuple(p + u * su * w / 2 + v * sv * h / 2) for p in (p0, p1) for su in (-1, 1) for sv in (-1, 1)]
        self.hull(g, m, pts)

    def lamp(self, x, y, z, s=1.6, t=0.4, mat="Lamp"):
        """Light fixture: its own object so fit_base.lua can put one PointLight on it."""
        self.nlamp += 1
        g = f"L{self.nlamp:02d}"
        self.box(g, mat, x - s / 2, x + s / 2, y - t, y, z - s / 2, z + s / 2, col=False, kind="lamp")
        self.lamps.append((f"{g}_{mat}", (x, y, z)))

    def truss(self, x, y0, z, h):
        self.trusses.append((x, y0, z, h))
        self.prims.append(("Truss", "collision", (x - 1, x + 1, y0, y0 + h, z - 1, z + 1)))

    # ------------------------------------------------------------ composites
    @staticmethod
    def rect_subtract(r, holes, merge_axis=1):
        """r = (a0, a1, b0, b1); holes = list of rects.  Returns rects covering r minus holes,
        merged along axis 1 (b) or 0 (a)."""
        a0, a1, b0, b1 = r
        hs = [(max(a0, h[0]), min(a1, h[1]), max(b0, h[2]), min(b1, h[3])) for h in holes]
        hs = [h for h in hs if h[0] < h[1] and h[2] < h[3]]
        A = sorted({a0, a1, *[h[0] for h in hs], *[h[1] for h in hs]})
        B = sorted({b0, b1, *[h[2] for h in hs], *[h[3] for h in hs]})

        def filled(i, j):
            ca, cb = (A[i] + A[i + 1]) / 2, (B[j] + B[j + 1]) / 2
            return not any(h[0] < ca < h[1] and h[2] < cb < h[3] for h in hs)

        out = []
        if merge_axis == 1:
            for i in range(len(A) - 1):
                j = 0
                while j < len(B) - 1:
                    if filled(i, j):
                        k = j
                        while k + 1 < len(B) - 1 and filled(i, k + 1):
                            k += 1
                        out.append((A[i], A[i + 1], B[j], B[k + 1]))
                        j = k + 1
                    else:
                        j += 1
        else:
            for j in range(len(B) - 1):
                i = 0
                while i < len(A) - 1:
                    if filled(i, j):
                        k = i
                        while k + 1 < len(A) - 1 and filled(k + 1, j):
                            k += 1
                        out.append((A[i], A[k + 1], B[j], B[j + 1]))
                        i = k + 1
                    else:
                        i += 1
        return out

    def wall(self, g, m, axis, a0, a1, c0, c1, y0, y1, openings=(), glass=True):
        """Wall running along `axis` ('x' or 'z') from a0..a1, thickness c0..c1, height y0..y1.
        openings: (u0, u1, v0, v1) along the wall; windows (v0 > y0) get a glass pane."""
        holes = [(o[0], o[1], o[2], o[3]) for o in openings]
        for (u0, u1, v0, v1) in self.rect_subtract((a0, a1, y0, y1), holes, merge_axis=1):
            if axis == "x":
                self.box(g, m, u0, u1, v0, v1, c0, c1)
            else:
                self.box(g, m, c0, c1, v0, v1, u0, u1)
        if glass:
            cm = (c0 + c1) / 2
            for (u0, u1, v0, v1) in holes:
                if v0 > y0 + 0.5:
                    if axis == "x":
                        self.box(g, "Glass", u0, u1, v0, v1, cm - 0.1, cm + 0.1, col=False, kind="glass")
                    else:
                        self.box(g, "Glass", cm - 0.1, cm + 0.1, v0, v1, u0, u1, col=False, kind="glass")

    def slab(self, g, m, x0, x1, z0, z1, y0, y1, holes=()):
        for (a0, a1, c0, c1) in self.rect_subtract((x0, x1, z0, z1), holes, merge_axis=0):
            self.box(g, m, a0, a1, y0, y1, c0, c1)

    def stairs(self, g, m, x0, x1, z0, z1, axis, sign, ya, yb, solid=False, thick=1.0, stringer=True):
        """Straight flight inside rect, climbing along axis in direction sign from ya to yb.
        Enforces rise <= 1 and tread >= 2."""
        a0, a1 = (x0, x1) if axis == "x" else (z0, z1)
        L = a1 - a0
        n = max(1, math.ceil((yb - ya) - 1e-6))
        rise, tread = (yb - ya) / n, L / n
        assert rise <= 1.0 + 1e-6 and tread >= 2.0 - 1e-6, f"{g}: rise {rise:.2f} tread {tread:.2f}"
        for i in range(n):
            top = ya + rise * (i + 1)
            if sign > 0:
                s0, s1 = a0 + i * tread, a0 + (i + 1) * tread
            else:
                s0, s1 = a1 - (i + 1) * tread, a1 - i * tread
            bot = ya if solid else max(ya, top - thick)
            if axis == "x":
                self.box(g, m, s0, s1, bot, top, z0, z1)
            else:
                self.box(g, m, x0, x1, bot, top, s0, s1)
        if stringer and not solid:
            lo, hi = (a0, a1) if sign > 0 else (a1, a0)
            for cm in ((z0 + 0.15, z1 - 0.15) if axis == "x" else (x0 + 0.15, x1 - 0.15)):
                p0 = (lo, ya + 0.6, cm) if axis == "x" else (cm, ya + 0.6, lo)
                p1 = (hi, yb - 0.6, cm) if axis == "x" else (cm, yb - 0.6, hi)
                self.beam(g, "Metal", p0, p1, 0.4, 0.9)
        return n, rise, tread

    def rail(self, g, axis, a0, a1, c, y, h=3.5, m="Metal", post=4.0, yb=None):
        """Railing along axis at cross-coordinate c, standing on y (or sloping y -> yb).
        Collision: one thin invisible wall.  Visual: posts + top and mid rails."""
        yb = y if yb is None else yb
        if axis == "x":
            self.coll(a0, a1, min(y, yb), max(y, yb) + h, c - 0.2, c + 0.2, f"{g}_Rail")
        else:
            self.coll(c - 0.2, c + 0.2, min(y, yb), max(y, yb) + h, a0, a1, f"{g}_Rail")
        n = max(1, round((a1 - a0) / post))

        def P(a, yy):
            return (a, yy, c) if axis == "x" else (c, yy, a)

        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            yy = y + (yb - y) * i / n
            key = tuple(round(v, 2) for v in P(a, yy))
            if key in self.posts:
                continue                      # shared corner post: don't stack two identical beams
            self.posts.add(key)
            self.beam(g, m, P(a, yy), P(a, yy + h), 0.3)
        bar = 0.25 if axis == "x" else 0.28   # different bar sizes so crossing bars never share a face
        for hh in (h, h * 0.5):
            self.beam(g, m, P(a0, y + hh), P(a1, yb + hh), bar)

    # ------------------------------------------------------------ objects
    def build(self, prefix=""):
        mats = {}
        for name, (rgb, _) in PALETTE.items():
            mt = bpy.data.materials.new(name)
            mt.use_nodes = True
            bsdf = mt.node_tree.nodes["Principled BSDF"]
            col = tuple(c / 255 for c in rgb) + (1,)
            bsdf.inputs["Base Color"].default_value = col
            bsdf.inputs["Roughness"].default_value = 0.8
            if name in LIGHT_MATS:
                bsdf.inputs["Emission Color"].default_value = col
                bsdf.inputs["Emission Strength"].default_value = 8
            if name == "Glass":
                bsdf.inputs["Alpha"].default_value = 0.35
            mt.diffuse_color = col
            mats[name] = mt
        objs = []
        col = bpy.context.scene.collection
        for (g, m), lst in sorted(self.chunks.items()):
            for k, c in enumerate(lst):
                name = f"{prefix}{g}{k + 1 if k else ''}_{m}"
                me = bpy.data.meshes.new(name)
                me.from_pydata(c["v"], [], c["f"])
                bm = bmesh.new()
                bm.from_mesh(me)
                bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="EAR_CLIP")
                bm.to_mesh(me)
                bm.free()
                me.materials.append(mats[m])
                ob = bpy.data.objects.new(name, me)
                col.objects.link(ob)
                objs.append(ob)
        return objs


# ------------------------------------------------------------------ reporting / checks
def report(objs, title):
    total = 0
    print(f"\n==== {title}: per-object triangles ====")
    for o in sorted(objs, key=lambda o: -len(o.data.polygons)):
        n = len(o.data.polygons)
        total += n
        flag = "  <-- OVER 9000" if n > 9000 else ""
        print(f"  {o.name:28s} {n:6d}{flag}")
    print(f"  TOTAL meshes={len(objs)} tris={total}")
    return total


def check_normals(objs):
    """Each primitive is a closed island, so recalculating normals must flip nothing."""
    bad = 0
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        before = [f.normal.copy() for f in bm.faces]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        flips = sum(1 for f, n0 in zip(bm.faces, before) if f.normal.dot(n0) < 0)
        if flips:
            bad += 1
            print(f"  NORMALS: {o.name} {flips} inward faces")
        bm.free()
    print(f"[CHECK] outward normals: {'OK' if bad == 0 else str(bad) + ' objects with flipped faces'}")
    return bad == 0


def write_lua(path, header, body):
    with open(path, "w") as f:
        f.write(header)
        f.write(body)


def n(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             apply_unit_scale=True, bake_space_transform=False, use_mesh_modifiers=True)
    print("[EXPORT]", path)


def check_coplanar(builder, verbose=12):
    """Two boxes whose faces lie in the same plane, face the same way and overlap in area
    will z-fight (flicker) in Roblox.  Report every such pair."""
    planes = {}
    for idx, (name, bb) in enumerate(builder.boxes):
        for ax in range(3):
            for side in (0, 1):
                v = round(bb[ax * 2 + side], 3)
                if ax == 1 and side == 0 and abs(v) < 1e-6:
                    continue          # bottoms resting on the Studio floor are never seen
                planes.setdefault((ax, side, v), []).append(idx)
    bad = []
    for (ax, side, v), ids in planes.items():
        if len(ids) < 2:
            continue
        o = [a for a in range(3) if a != ax]
        for i in range(len(ids)):
            A = builder.boxes[ids[i]][1]
            for j in range(i + 1, len(ids)):
                Bb = builder.boxes[ids[j]][1]
                ov = [(max(A[a * 2], Bb[a * 2]), min(A[a * 2 + 1], Bb[a * 2 + 1])) for a in o]
                if all(hi - lo > 1e-3 for lo, hi in ov):
                    # hidden if an opposite-facing face in the same plane covers the overlap (e.g. a wall)
                    covers = [builder.boxes[k][1] for k in planes.get((ax, 1 - side, v), [])]
                    rest = Builder.rect_subtract((ov[0][0], ov[0][1], ov[1][0], ov[1][1]),
                                                 [(C[o[0] * 2], C[o[0] * 2 + 1], C[o[1] * 2], C[o[1] * 2 + 1]) for C in covers])
                    hidden = sum((r[1] - r[0]) * (r[3] - r[2]) for r in rest) < 1e-4
                    if not hidden:
                        bad.append((builder.boxes[ids[i]][0], builder.boxes[ids[j]][0], "xyz"[ax], v))
    for b_ in bad[:verbose]:
        print(f"  COPLANAR {b_[0]} / {b_[1]} on {b_[2]}={b_[3]}")
    print(f"[CHECK] coplanar same-facing faces: {'OK' if not bad else str(len(bad)) + ' pairs'}")
    return bad
