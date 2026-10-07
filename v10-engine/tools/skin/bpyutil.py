"""bpy helpers: solid primitives (bmesh), bevels, booleans, mirror, transforms,
smoothing, STL export. All lengths in millimetres; the scene unit is mm."""
import json
import math
import os

import bpy  # noqa: F401  (must come first: bmesh / mathutils are registered by bpy)
import bmesh
from mathutils import Matrix, Vector

SEGS = 128          # every hole / bore / round boss: at least 128 segments
COL = {}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = 'MILLIMETERS'
    COL.clear()
    from . import materials as _mat
    _mat._M.clear()                      # cached materials die with the old scene


def collection(name):
    if name in COL:
        return COL[name]
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    COL[name] = c
    return c


def _link(obj, col="COL_skin"):
    collection(col).objects.link(obj)
    return obj


def _activate(obj):
    for o in bpy.data.objects:
        try:
            o.select_set(False)
        except RuntimeError:
            pass
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def from_bmesh(name, bm, col="COL_skin"):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    return _link(obj, col)


def box(name, x0, x1, y0, y1, z0, z1, col="COL_skin"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return from_bmesh(name, bm, col)


def cylinder(name, r, z0, z1, x=0.0, y=0.0, axis="Z", segs=SEGS, r2=None, col="COL_skin"):
    """Cylinder (or cone when r2 is given) from z0 to z1 along `axis` through (x, y)
    of the two other coordinates, in the order of the remaining axes."""
    bm = bmesh.new()
    h = z1 - z0
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, (z0 + z1) / 2), verts=bm.verts)
    if axis == "X":      # local Z -> X; (x, y) given are (y, z)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, x, y), verts=bm.verts)
    elif axis == "Y":    # local Z -> Y; (x, y) given are (x, z)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, 'X'), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x, 0, y), verts=bm.verts)
    else:
        bmesh.ops.translate(bm, vec=(x, y, 0), verts=bm.verts)
    obj = from_bmesh(name, bm, col)
    if r2 is None:
        # remembered so boolean() can log the feature for the STL fit measurement (see fitcut.FITS)
        obj["fit_meta"] = json.dumps(dict(name=name, r=r, z0=z0, z1=z1, x=x, y=y, axis=axis))
    return obj


def prism(name, pts_yz, x0, x1, col="COL_skin"):
    """Polygon in the YZ plane extruded along X (closed, counter-clockwise or not)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x0, y, z)) for y, z in pts_yz]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    verts = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(x1 - x0, 0, 0), verts=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, col)


def prism_z(name, pts_xy, z0, z1, col="COL_skin"):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in pts_xy]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    verts = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, col)


def loft(name, rings, col="COL_skin"):
    """Closed solid through a stack of rings (lists of (x, y, z) with equal length), capped."""
    bm = bmesh.new()
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vrings, vrings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(list(reversed(vrings[0])))
    bm.faces.new(vrings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm, col)


def rrect_ring(cx, cy, w, h, r, z, segs_per_corner=16):
    """Rounded-rectangle ring (list of (x, y, z)), counter-clockwise."""
    pts = []
    r = max(0.01, min(r, w / 2 - 0.01, h / 2 - 0.01))
    corners = [(cx + w / 2 - r, cy + h / 2 - r, 0), (cx - w / 2 + r, cy + h / 2 - r, 90),
               (cx - w / 2 + r, cy - h / 2 + r, 180), (cx + w / 2 - r, cy - h / 2 + r, 270)]
    for ccx, ccy, a0 in corners:
        for i in range(segs_per_corner):
            a = math.radians(a0 + 90.0 * i / segs_per_corner)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a), z))
    return pts


def circle_ring(cx, cy, r, z, segs=SEGS):
    return [(cx + r * math.cos(2 * math.pi * i / segs), cy + r * math.sin(2 * math.pi * i / segs), z) for i in range(segs)]


def rrect_prism(name, cx, cy, w, h, r, z0, z1, col="COL_skin"):
    return loft(name, [rrect_ring(cx, cy, w, h, r, z0), rrect_ring(cx, cy, w, h, r, z1)], col)


def apply_modifier(obj, mod):
    _activate(obj)
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def bevel(obj, width, segments=4, angle_deg=30.0, profile=0.5, clamp=True):
    m = obj.modifiers.new("bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)
    m.profile = profile
    m.use_clamp_overlap = clamp
    m.miter_outer = 'MITER_ARC'
    apply_modifier(obj, m)
    return obj


def bevel_edges(obj, width, segments, pick, profile=0.5):
    """Bevel only the edges for which pick(edge_center_vector, edge_dir_vector) is True."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edges = [e for e in bm.edges if pick((e.verts[0].co + e.verts[1].co) / 2, (e.verts[1].co - e.verts[0].co).normalized())]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=segments, profile=profile, affect='EDGES', clamp_overlap=True)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def subsurf(obj, levels=2):
    m = obj.modifiers.new("subd", 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    apply_modifier(obj, m)
    return obj


DEBUG_MANIFOLD = False
SOLVER = "MANIFOLD"


def non_manifold_edges(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    n = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.free()
    return n


def cleanup(obj, dist=1e-5):
    """Merge exactly coincident vertices and fix normals. Degenerate-edge dissolving is
    deliberately NOT done: it opened holes on the collector's socket rims."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def boolean(obj, cutter, op="DIFFERENCE", keep_cutter=False):
    before = non_manifold_edges(obj) if DEBUG_MANIFOLD else 0
    m = obj.modifiers.new("bool", 'BOOLEAN')
    m.operation = op
    try:
        m.solver = SOLVER                    # 'MANIFOLD' (Blender 4.5+): manifold in -> manifold out
    except TypeError:
        m.solver = 'EXACT'
    m.object = cutter
    m.use_self = False
    meta = cutter.get("fit_meta") if op == "DIFFERENCE" else None
    meta = meta or None
    apply_modifier(obj, m)
    if meta:
        _log_fit(obj, json.loads(meta))
    if DEBUG_MANIFOLD:
        after = non_manifold_edges(obj)
        if after != before:
            print(f"    [manifold] {obj.name}: {op} {cutter.name}: non-manifold edges {before} -> {after}", flush=True)
    if not keep_cutter:
        delete(cutter)
    return obj


MEASURED_CUTTERS = ("bore", "pan_screw", "pan_cbore", "shaft_hole", "ctl_hole", "port_cbore")


def _log_fit(obj, meta):
    """Straight cylindrical cutters that are fits (inserts, screw holes, bores) -> fitcut.FITS.
    Along-axis window trimmed 0.02 mm at both ends (cutters always run past the faces they cut)."""
    n = meta["name"]
    if not (n in MEASURED_CUTTERS or n.endswith(("_ins", "_clear", "_cbore"))):
        return
    from . import fitcut as F
    ax = meta["axis"]
    if ax == "X":
        p, d = (0.0, meta["x"], meta["y"]), (1.0, 0.0, 0.0)
    elif ax == "Y":
        p, d = (meta["x"], 0.0, meta["y"]), (0.0, 1.0, 0.0)
    else:
        p, d = (meta["x"], meta["y"], 0.0), (0.0, 0.0, 1.0)
    F.note(obj, n, "bore", meta["r"], p, d, meta["z0"] + 0.02, meta["z1"] - 0.02)


def union(objs, name=None):
    """Boolean union of a list into the first object (robust for overlapping solids)."""
    base = objs[0]
    for o in objs[1:]:
        boolean(base, o, "UNION")
    if name:
        base.name = name
    return base


def delete(obj):
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and data.users == 0:
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)


def copy(obj, name=None):
    new = obj.copy()
    new.data = obj.data.copy()
    if name:
        new.name = name
    for c in obj.users_collection:
        c.objects.link(new)
    return new


def transform(obj, mat):
    """Bake a world-space matrix into the mesh (object transform stays identity)."""
    obj.data.transform(mat)
    obj.data.update()
    return obj


def move(obj, dx=0.0, dy=0.0, dz=0.0):
    return transform(obj, Matrix.Translation((dx, dy, dz)))


def rot(obj, axis, deg, pivot=(0, 0, 0)):
    p = Vector(pivot)
    return transform(obj, Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p))


def mirror_y(obj, name=None):
    """Mirror image about the XZ plane (y -> -y), normals fixed."""
    new = copy(obj, name)
    new.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
    bm = bmesh.new()
    bm.from_mesh(new.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(new.data)
    bm.free()
    return new


def to_bank(obj, bank, angle_A, angle_B):
    """Bank-local (bank A convention) -> engine frame, as cad/block.to_bank:
    bank B first turns 180 deg about Z, then both rotate about X by -bank_angle."""
    if bank == "B":
        rot(obj, 'Z', 180)
    return rot(obj, 'X', -(angle_A if bank == "A" else angle_B))


def shade(obj, angle_deg=35.0):
    """Smooth shading with sharp edges above angle (render only; no geometry change)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    thr = math.radians(angle_deg)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a = e.calc_face_angle(0.0)
            e.smooth = a < thr
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def bbox(obj):
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def finalize(obj, tol=1e-4):
    """Triangulate, merge, and pass the mesh through manifold3d: it collapses the sub-micron
    slivers the boolean solver leaves (which turn into non-manifold edges once STL rounds
    them to float32) while moving no surface by more than `tol` mm. Writes the result back
    into the object so renders and STLs are the same geometry.
    Returns (ok, message)."""
    import numpy as np
    import manifold3d as M3
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.verts.ensure_lookup_table()
    # round to float32 first: STL stores float32, so slivers that only exist in float64 must collapse here
    verts = np.array([v.co[:] for v in bm.verts], dtype=np.float32).astype(np.float64)
    tris = np.array([[v.index for v in f.verts] for f in bm.faces], dtype=np.uint32)
    bm.free()
    mesh = M3.Mesh64(vert_properties=verts, tri_verts=tris)
    mesh.merge()
    man = M3.Manifold(mesh)
    if man.status() != M3.Error.NoError:
        return False, f"{obj.name}: manifold3d {man.status()}"
    man = man.simplify(tol)
    # second pass after simplify in case collapsing created new float32 coincidences
    out = man.to_mesh64()
    v32 = np.asarray(out.vert_properties)[:, :3].astype(np.float32).astype(np.float64)
    mesh = M3.Mesh64(vert_properties=np.ascontiguousarray(v32), tri_verts=np.ascontiguousarray(np.asarray(out.tri_verts, dtype=np.uint32)))
    mesh.merge()
    man2 = M3.Manifold(mesh)
    if man2.status() == M3.Error.NoError:
        man = man2
    out = man.to_mesh64()
    v = np.asarray(out.vert_properties)[:, :3]
    f = np.asarray(out.tri_verts)
    me = obj.data
    me.clear_geometry()
    me.from_pydata(v.tolist(), [], f.tolist())
    me.update()
    shade(obj)
    dup = len(v) - len(np.unique(v.astype(np.float32), axis=0))
    msg = f"{obj.name}: genus {man.genus()} tris {man.num_tri()} vol {man.volume():.0f}"
    if dup:
        return False, msg + f" PINCHED ({dup} coincident vertex pairs: slicers will see open edges)"
    return True, msg


def export_stl(obj, path, do_finalize=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if do_finalize:
        ok, msg = finalize(obj)
        if not ok:
            print("WARNING", msg)
    _activate(obj)
    with bpy.context.temp_override(selected_objects=[obj], active_object=obj):
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, apply_modifiers=True, global_scale=1.0, ascii_format=False)
    return path


def stats(obj):
    return len(obj.data.vertices), len(obj.data.polygons)


def tube_along(name, points, radius, profile=None, segs=SEGS, smooth=True, col="COL_skin"):
    """Capped tube swept along a polyline / smooth path of 3D points.
    profile=None -> round (radius); profile=(w, h, r) -> rounded rectangle (w across the
    path's local x, h across its local y) swept with a rounded-rect bevel object."""
    cu = bpy.data.curves.new(name + "_path", 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY' if not smooth else 'NURBS')
    sp.points.add(len(points) - 1)
    for p, pt in zip(sp.points, points):
        p.co = (pt[0], pt[1], pt[2], 1.0)
    if smooth:
        sp.order_u = min(4, len(points))
        sp.use_endpoint_u = True
    sp.resolution_u = 24
    cu.use_fill_caps = True
    cu.twist_mode = 'MINIMUM'
    if profile is None:
        cu.bevel_depth = radius
        cu.bevel_resolution = max(1, segs // 4 - 1)
    else:
        w, h, r = profile
        prof = bpy.data.curves.new(name + "_prof", 'CURVE')
        prof.dimensions = '2D'
        ring = rrect_ring(0, 0, w, h, r, 0, segs_per_corner=max(4, segs // 4))
        ps = prof.splines.new('POLY')
        ps.points.add(len(ring) - 1)
        for p, pt in zip(ps.points, ring):
            p.co = (pt[0], pt[1], 0.0, 1.0)
        ps.use_cyclic_u = True
        pobj = bpy.data.objects.new(name + "_prof", prof)
        collection(col).objects.link(pobj)
        cu.bevel_mode = 'OBJECT'
        cu.bevel_object = pobj
    obj = bpy.data.objects.new(name, cu)
    collection(col).objects.link(obj)
    _activate(obj)
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.convert(target='MESH')
    obj = bpy.data.objects[name]
    if profile is not None:
        delete(bpy.data.objects[name + "_prof"])
    cleanup(obj)
    return obj


def fillet_polygon(pts, r, n=10):
    """2D polygon (list of (u, v)) with every convex/concave corner replaced by an arc of radius r
    (clamped to the shorter adjacent half-edge). Returns the sampled outline."""
    out = []
    m = len(pts)
    for i in range(m):
        Pp, Q, R = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % m])
        t1, t2 = (Q - Pp), (R - Q)
        l1, l2 = t1.length, t2.length
        t1.normalize(); t2.normalize()
        cross = t1.x * t2.y - t1.y * t2.x
        dot = max(-1.0, min(1.0, t1.dot(t2)))
        beta = math.acos(dot)
        if beta < 1e-6:
            out.append(tuple(Q))
            continue
        rr = min(r, 0.49 * l1 / math.tan(beta / 2), 0.49 * l2 / math.tan(beta / 2))
        tl = rr * math.tan(beta / 2)
        A, B = Q - t1 * tl, Q + t2 * tl
        nrm = Vector((-t1.y, t1.x)) * (1 if cross > 0 else -1)
        centre = A + nrm * rr
        a0 = math.atan2(A.y - centre.y, A.x - centre.x)
        sweep = beta * (1 if cross > 0 else -1)
        for k in range(n + 1):
            a = a0 + sweep * k / n
            out.append((centre.x + rr * math.cos(a), centre.y + rr * math.sin(a)))
    return out


def convex_hull_2d(pts):
    pts = sorted(set((float(a), float(b)) for a, b in pts))
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


def text_mesh(name, text, size, depth, col="COL_skin"):
    """Extruded bold text as a mesh, centred on the origin in the XY plane, from z=-depth/2 to +depth/2."""
    cu = bpy.data.curves.new(name + "_font", 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.resolution_u = 6
    obj = bpy.data.objects.new(name, cu)
    collection(col).objects.link(obj)
    _activate(obj)
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
        bpy.ops.object.convert(target='MESH')
    obj = bpy.data.objects[name]
    cleanup(obj)
    return obj
