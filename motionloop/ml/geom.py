"""
Geometry helpers: 2D outlines, bmesh solids, exact booleans, mesh statistics.

All solids are built as closed bmesh lofts of polygon rings and combined with Blender's EXACT
boolean solver, so every part comes out as one closed manifold shell.
"""

import math

import bpy  # noqa: F401  (bpy must be imported before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

COLL = {}


# =====================================================================================
# 2D outlines (lists of (a, b) tuples, counter-clockwise)
# =====================================================================================


def area2d(pts):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2


def ccw(pts):
    return pts if area2d(pts) > 0 else list(reversed(pts))


def circle(cx, cy, r, seg=64, start=0.0):
    return [(cx + r * math.cos(start + 2 * math.pi * i / seg),
             cy + r * math.sin(start + 2 * math.pi * i / seg)) for i in range(seg)]


def arc(cx, cy, r, a0, a1, n):
    """n+1 points from angle a0 to a1 (radians, any direction)."""
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def superellipse_rect(hx, hy, R, n_exp=4.0, inset=0.0, seg=12):
    """Rectangle +-hx, +-hy whose corners are superellipse quarters of size R; offset
    inward by `inset` (shrinks the half-sizes and the corner size together)."""
    hx, hy, R = hx - inset, hy - inset, max(R - inset, 0.05)
    pts = []
    for cx, cy, a0 in ((hx - R, hy - R, 0), (-hx + R, hy - R, 90), (-hx + R, -hy + R, 180),
                       (hx - R, -hy + R, 270)):
        for i in range(seg + 1):
            t = math.radians(a0 + 90.0 * i / seg)
            c, s = math.cos(t), math.sin(t)
            pts.append((cx + R * math.copysign(abs(c) ** (2 / n_exp), c),
                        cy + R * math.copysign(abs(s) ** (2 / n_exp), s)))
    return pts


def offset_convex(pts, d):
    """Inward offset of a convex CCW polygon by d (miter join; exact for edge lines)."""
    pts = ccw(list(pts))
    n = len(pts)
    nrm = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        nrm.append((-(y1 - y0) / L, (x1 - x0) / L))
    out = []
    for i in range(n):
        a, b = nrm[i - 1], nrm[i]
        k = 1.0 + a[0] * b[0] + a[1] * b[1]
        out.append((pts[i][0] + d * (a[0] + b[0]) / k, pts[i][1] + d * (a[1] + b[1]) / k))
    return out


def rrect(x0, x1, y0, y1, r, seg=8):
    r = min(r, (x1 - x0) / 2 - 1e-4, (y1 - y0) / 2 - 1e-4)
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180),
                       (x1 - r, y0 + r, 270)):
        pts += arc(cx, cy, r, math.radians(a0), math.radians(a0 + 90), seg)
    return pts


def rrect2(x0, x1, y0, y1, r_top, r_bot, seg=8):
    """Rounded rectangle with different top and bottom corner radii."""
    pts = []
    for cx, cy, a0, r in ((x1 - r_top, y1 - r_top, 0, r_top), (x0 + r_top, y1 - r_top, 90, r_top),
                          (x0 + r_bot, y0 + r_bot, 180, r_bot), (x1 - r_bot, y0 + r_bot, 270, r_bot)):
        pts += arc(cx, cy, r, math.radians(a0), math.radians(a0 + 90), seg)
    return pts


def teardrop(cx, cy, r, seg=48, cap=1.15):
    """Circle with a 45-degree roof (+y) truncated at cy + cap*r: prints without support when
    the axis is horizontal."""
    k = r * math.sqrt(2) - cap * r  # half-width of the flat cap
    pts = [(cx + r * math.cos(math.pi / 4), cy + r * math.sin(math.pi / 4)),
           (cx + k, cy + cap * r), (cx - k, cy + cap * r)]
    n = int(seg * 0.75)
    for i in range(n):
        a = 3 * math.pi / 4 + (3 * math.pi / 2) * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def d_shape(cx, cy, r, flat, flat_angle, seg=48):
    """Circle of radius r with a flat chord at distance `flat` from the centre, whose outward
    normal points at flat_angle (radians)."""
    half = math.acos(flat / r)
    a0 = flat_angle + half
    a1 = flat_angle + 2 * math.pi - half
    return arc(cx, cy, r, a0, a1, seg)


def hexagon(cx, cy, af, rot=0.0):
    rc = af / math.sqrt(3)
    return [(cx + rc * math.cos(rot + math.pi / 6 + i * math.pi / 3),
             cy + rc * math.sin(rot + math.pi / 6 + i * math.pi / 3)) for i in range(6)]


def link_outline(L, R1, R2, h1, h2, f, n_boss=28, n_fil=8):
    """Outline of a tapered link: boss R1 at (0, 0), boss R2 at (L, 0), straight shank of
    half-width h1 -> h2 joined to the bosses by concave fillets of radius f. Offsetting the
    outline inward by d is exact with (R1-d, R2-d, h1-d, h2-d, f+d). Same point count for any
    parameters, so offsets can be lofted."""
    ln = math.hypot(L, h2 - h1)
    d = (L / ln, (h2 - h1) / ln)
    nrm = (-d[1], d[0])  # outward normal of the upper shank line
    p0 = (0.0, h1)

    def fillet(O, R, pick_max):
        # centre C = p0 + t d + f nrm with |C - O| = R + f
        bx = p0[0] + f * nrm[0] - O[0]
        by = p0[1] + f * nrm[1] - O[1]
        bb = bx * d[0] + by * d[1]
        cc = bx * bx + by * by - (R + f) ** 2
        disc = math.sqrt(max(bb * bb - cc, 0.0))
        t = -bb + disc if pick_max else -bb - disc
        C = (p0[0] + t * d[0] + f * nrm[0], p0[1] + t * d[1] + f * nrm[1])
        Tb = (O[0] + (C[0] - O[0]) * R / (R + f), O[1] + (C[1] - O[1]) * R / (R + f))
        Tl = (C[0] - f * nrm[0], C[1] - f * nrm[1])
        return C, Tb, Tl

    C1, Tb1, Tl1 = fillet((0.0, 0.0), R1, True)
    C2, Tb2, Tl2 = fillet((L, 0.0), R2, False)
    upper = []
    # small boss, from its rightmost point up to the fillet tangent
    a_s = math.atan2(Tb2[1], Tb2[0] - L)
    upper += arc(L, 0.0, R2, 0.0, a_s, n_boss)[:-1]
    # small fillet (concave): around C2 from Tb2 to Tl2
    a0 = math.atan2(Tb2[1] - C2[1], Tb2[0] - C2[0])
    a1 = math.atan2(Tl2[1] - C2[1], Tl2[0] - C2[0])
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    if a0 - a1 > math.pi:
        a1 += 2 * math.pi
    upper += arc(C2[0], C2[1], f, a0, a1, n_fil)[:-1]
    # shank line Tl2 -> Tl1 (two points: the fillet arcs supply the ends)
    upper.append(Tl2)
    # big fillet: around C1 from Tl1 to Tb1
    a0 = math.atan2(Tl1[1] - C1[1], Tl1[0] - C1[0])
    a1 = math.atan2(Tb1[1] - C1[1], Tb1[0] - C1[0])
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    if a0 - a1 > math.pi:
        a1 += 2 * math.pi
    upper += arc(C1[0], C1[1], f, a0, a1, n_fil)[:-1]
    # big boss from the tangent over the top to the leftmost point
    a_b = math.atan2(Tb1[1], Tb1[0])
    upper += arc(0.0, 0.0, R1, a_b, math.pi, n_boss)[:-1]
    lower = [(x, -y) for (x, y) in reversed(upper)]
    # upper runs from angle 0 of the small boss to angle pi of the big boss; lower mirrors it
    return upper + [(-R1, 0.0)] + lower[:-1]


# =====================================================================================
# Solids
# =====================================================================================


def collection(name, parent=None):
    if name in bpy.data.collections:
        c = bpy.data.collections[name]
    else:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    COLL[name] = c
    return c


def obj_from_bm(name, bm, coll=None):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or COLL["_work"]).objects.link(ob)
    return ob


def loft(name, rings, coll=None):
    """Solid from stacked rings [(z, [(x, y), ...]), ...]; all rings the same count."""
    rings = [(z, ccw(list(poly))) for z, poly in rings]
    bm = bmesh.new()
    vr = [[bm.verts.new((x, y, z)) for (x, y) in poly] for z, poly in rings]
    n = len(vr[0])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(vr[0])))
    bm.faces.new(vr[-1])
    return obj_from_bm(name, bm, coll)


def prism(name, poly, z0, z1, coll=None):
    return loft(name, [(z0, poly), (z1, poly)], coll)


SWAP_YZ = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def loft_y(name, rings, coll=None):
    """Solid from rings in the XZ plane stacked along Y: [(y, [(x, z), ...]), ...]."""
    ob = loft(name, rings, coll)
    ob.data.transform(SWAP_YZ)
    ob.data.flip_normals()
    ob.data.update()
    return ob


def prism_y(name, poly_xz, y0, y1, coll=None):
    return loft_y(name, [(min(y0, y1), poly_xz), (max(y0, y1), poly_xz)], coll)


SWAP_XZ = Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1)))


def prism_x(name, poly_zy, x0, x1, coll=None):
    """Prism along X of a profile given as (z, y) points."""
    ob = prism(name, poly_zy, min(x0, x1), max(x0, x1), coll)
    # built as (x=z_prof, y=y, z=x_extrude); swap X and Z
    ob.data.transform(SWAP_XZ)
    ob.data.flip_normals()
    ob.data.update()
    return ob


def chamfer_rings(poly_fn, a0, a1, c0, c1):
    """Rings for an extrusion from a0 to a1 with 45-degree chamfers c0 / c1 at the ends.
    poly_fn(inset) returns the outline inset by `inset`."""
    rings = []
    if c0 > 0:
        rings.append((a0, poly_fn(c0)))
    rings.append((a0 + c0, poly_fn(0.0)))
    rings.append((a1 - c1, poly_fn(0.0)))
    if c1 > 0:
        rings.append((a1, poly_fn(c1)))
    return rings


def apply_bool(target, cutter, op, delete_cutter=True):
    m = target.modifiers.new("b", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.object = cutter
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear()
    old = target.data
    target.data = me
    me.name = target.name
    bpy.data.meshes.remove(old)
    if delete_cutter:
        cm = cutter.data
        bpy.data.objects.remove(cutter)
        if cm.users == 0:
            bpy.data.meshes.remove(cm)
    return target


def union(target, *others):
    for o in others:
        apply_bool(target, o, "UNION")
    return target


def cut(target, *others):
    for o in others:
        apply_bool(target, o, "DIFFERENCE")
    return target


def join_cutters(name, objs):
    """Merge several (disjoint) cutter solids into one object: one boolean instead of many."""
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bpy.data.objects.remove(o)
    return obj_from_bm(name, bm)


def text_solid(name, body, size, z0, z1, cx=0.0, cy=0.0, mirror_x=False, spacing=1.0, rot=0.0):
    cu = bpy.data.curves.new(name + "_curve", "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_character = spacing
    cu.extrude = (z1 - z0) / 2
    cu.resolution_u = 4
    try:
        cu.font = bpy.data.fonts.load("<builtin>") if "Bfont" not in bpy.data.fonts else \
            bpy.data.fonts["Bfont"]
    except RuntimeError:
        pass
    ob = bpy.data.objects.new(name + "_txt", cu)
    COLL["_work"].objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    sx = -1 if mirror_x else 1
    me.transform(Matrix.Translation((cx, cy, (z0 + z1) / 2)) @ Matrix.Rotation(rot, 4, "Z")
                 @ Matrix.Diagonal((sx, 1, 1, 1)))
    if mirror_x:
        me.flip_normals()
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return obj_from_bm(name, bm)


# =====================================================================================
# Measurement
# =====================================================================================


def mesh_stats(ob, mat=None):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform((mat or Matrix()) @ ob.matrix_world)
    vol = bm.calc_volume(signed=True)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    seen, shells = set(), 0
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
    co = [v.co for v in bm.verts]
    bb = [min(c.x for c in co), min(c.y for c in co), min(c.z for c in co),
          max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)]
    area = sum(f.calc_area() for f in bm.faces)
    nf = len(bm.faces)
    bm.free()
    return dict(volume_mm3=vol, nonmanifold_edges=nonman, shells=shells, bbox=bb,
                area_mm2=area, faces=nf)


def world_tris(ob, mat=None):
    me = ob.data
    me.calc_loop_triangles()
    M = (mat or Matrix()) @ ob.matrix_world
    verts = [M @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return verts, tris


def bvh_of(obs_mats):
    """One BVH tree for several (object, matrix) pairs."""
    verts, tris = [], []
    for ob, mat in obs_mats:
        v, t = world_tris(ob, mat)
        off = len(verts)
        verts += v
        tris += [(a + off, b + off, c + off) for a, b, c in t]
    return BVHTree.FromPolygons(verts, tris, epsilon=0.0), verts, tris


def surface_points(ob, step=0.6, mat=None):
    """Points on every triangle (vertices, edge midpoints and an interior grid)."""
    v, t = world_tris(ob, mat)
    pts = list(v)
    for a, b, c in t:
        A, B, C = v[a], v[b], v[c]
        la, lb = (B - A).length, (C - A).length
        n = max(1, int(max(la, lb, (C - B).length) / step))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                if (i, j) in ((0, 0), (n, 0), (0, n)):
                    continue
                u, w = i / n, j / n
                pts.append(A + (B - A) * u + (C - A) * w)
    return pts


def min_dist(points, tree, limit=4.0):
    best = (limit, None)
    for q in points:
        hit = tree.find_nearest(q, limit)
        if hit[0] is not None and hit[3] < best[0]:
            best = (hit[3], (tuple(round(c, 2) for c in q), tuple(round(c, 2) for c in hit[0])))
    return best


def thickness_scan(ob, mat=None, min_area=0.03):
    """Ray-cast inward from every face; return (thickness, face centre) for opposing exits."""
    verts, tris = world_tris(ob, mat)
    tree = BVHTree.FromPolygons(verts, tris)
    res = []
    for k, (a, b, c) in enumerate(tris):
        A, B, C = verts[a], verts[b], verts[c]
        n = (B - A).cross(C - A)
        if n.length / 2 < min_area:
            continue
        n.normalize()
        cen = (A + B + C) / 3
        hit = tree.ray_cast(cen - n * 1e-3, -n, 60.0)
        if hit[0] is None or hit[1].dot(n) > -0.85:
            continue
        if set(tris[hit[2]]) & {a, b, c}:
            continue
        res.append((hit[3], tuple(round(x, 2) for x in cen)))
    return res


def overhang_scan(verts, tris, limit_deg=45.0, z_bed=0.0):
    """Down-facing area steeper than the limit, in print orientation, bed face excluded.
    Returns (flat, steep) lists of (area, centre)."""
    lim = -math.cos(math.radians(90 - limit_deg)) - 0.01
    flat, steep = [], []
    for t in tris:
        a, b, c = (verts[i] for i in t)
        n = (b - a).cross(c - a)
        area = n.length / 2
        if area < 1e-9:
            continue
        n.normalize()
        zc = (a.z + b.z + c.z) / 3
        if zc < z_bed + 0.05:
            continue
        if n.z < -0.999:
            flat.append((area, (a + b + c) / 3))
        elif n.z < lim:
            steep.append((area, (a + b + c) / 3))
    return flat, steep


def cluster(items, cell=2.5):
    groups = []
    for area, c in items:
        for g in groups:
            if abs(g["z"] - c.z) < 0.3 and g["lo"][0] - cell <= c.x <= g["hi"][0] + cell and \
                    g["lo"][1] - cell <= c.y <= g["hi"][1] + cell:
                g["area"] += area
                g["lo"] = [min(g["lo"][i], c[i]) for i in range(3)]
                g["hi"] = [max(g["hi"][i], c[i]) for i in range(3)]
                break
        else:
            groups.append(dict(area=area, z=c.z, lo=list(c), hi=list(c)))
    return sorted(groups, key=lambda g: -g["area"])


def section_polylines(ob, co, no, mat=None):
    """Cut a mesh with a plane; return the cut as a list of 3D polylines."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform((mat or Matrix()) @ ob.matrix_world)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
    cut_edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in cut_edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    used, lines = set(), []
    for start in list(adj):
        if start in used:
            continue
        line = [start]
        used.add(start)
        cur = start
        while True:
            nxt = [w for w in adj[cur] if w not in used]
            if not nxt:
                break
            cur = nxt[0]
            used.add(cur)
            line.append(cur)
        if len(adj[start]) == 2 and line[-1] in adj[start] and len(line) > 2:
            line.append(start)
        lines.append([tuple(round(c, 4) for c in v.co) for v in line])
    bm.free()
    return lines


def V(*a):
    return Vector(a)
