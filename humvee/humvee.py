"""Game-ready HMMWV (Humvee) for Roblox.  Run: blender --background --python humvee.py

Front = +Y, up = +Z, length ~4.6.  Hierarchy:
  Humvee_Root
    Humvee_Body_* (joined by material)
    Humvee_Wheel_FL/FR/RL/RR  -> _Rim, _Hub, _Lugs
    Humvee_Turret_Yaw         -> Humvee_Gun_Pitch
"""
import math
import bmesh
import bpy
from mathutils import Matrix, Vector

JOIN_BY_MATERIAL = True
P = "Humvee_"

# ---------------------------------------------------------------- cleanup
for ob in [o for o in bpy.data.objects if o.name.startswith(P)]:
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials):
    for d in list(coll):
        if d.name.startswith(P) and d.users == 0:
            coll.remove(d)

# ---------------------------------------------------------------- materials
def mat(name, color, rough=0.6, metal=0.0, emit=None, alpha=1.0):
    m = bpy.data.materials.new(P + name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 6.0
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
    m.diffuse_color = (*color, alpha)
    return m

M = {
    "Olive": mat("Olive", (0.16, 0.19, 0.09), 0.75),
    "Black": mat("Black", (0.02, 0.02, 0.02), 0.55),
    "Tire": mat("Tire", (0.012, 0.012, 0.012), 0.9),
    "Rim": mat("Rim", (0.28, 0.29, 0.27), 0.45, 0.6),
    "Glass": mat("Glass", (0.05, 0.08, 0.1), 0.05, alpha=0.35),
    "Headlight": mat("Headlight", (1, 0.95, 0.8), 0.2, emit=(1, 0.93, 0.75)),
    "Taillight": mat("Taillight", (0.8, 0.02, 0.01), 0.3, emit=(1, 0.05, 0.02)),
    "Gun": mat("Gun", (0.05, 0.05, 0.05), 0.35, 0.8),
}

col = bpy.context.scene.collection

def new_obj(name, bm, m, loc, bevel=0.0, segs=2, angle=40):
    me = bpy.data.meshes.new(P + name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M[m])
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(P + name, me)
    ob.location = loc
    col.objects.link(ob)
    if bevel > 0:
        bv = ob.modifiers.new("Bevel", "BEVEL")
        bv.width = bevel
        bv.segments = segs
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(angle)
        bv.harden_normals = True
    return ob

def box(name, loc, size, m="Olive", bevel=0.02, rot=None, taper=None):
    """Box centred on loc.  taper: dict of {vertex selector: offset} tweaks."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if taper:
        for sel, off in taper:
            for v in bm.verts:
                if sel(v.co):
                    v.co += Vector(off)
    ob = new_obj(name, bm, m, loc, bevel)
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    return ob

def cyl(name, loc, r, depth, m="Black", axis="X", segs=24, bevel=0.0, off=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    rot = {"X": Matrix.Rotation(math.pi / 2, 4, "Y"),
           "Y": Matrix.Rotation(math.pi / 2, 4, "X"), "Z": Matrix()}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(off) @ rot, verts=bm.verts)
    return new_obj(name, bm, m, loc, bevel, angle=30)

def quad(name, pts, m="Glass"):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    return new_obj(name, bm, m, (0, 0, 0))

def arch(name, cy, cx, r_in, r_out, x_in, x_out, m="Olive", segs=16, a0=12, a1=168, cz=0.45):
    """Fender flare: rectangular section swept over the top of a wheel."""
    bm = bmesh.new()
    rings = []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        ring = []
        for (x, r) in ((x_in, r_in), (x_out, r_in), (x_out, r_out), (x_in, r_out)):
            ring.append(bm.verts.new((x, cy + math.cos(a) * r, cz + math.sin(a) * r)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, m, (0, 0, 0), 0.015, angle=50)

def parent(child, par):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = par
    child.matrix_world = mw

# ---------------------------------------------------------------- key dims
WZ, WR = 0.45, 0.45            # wheel centre height / radius
WX, WY = 0.93, 1.58            # half track / half wheelbase
BELT = 1.40                    # beltline
ROOF = 1.92
GH_X = 1.00                    # greenhouse half width
GH_F, GH_R = 0.52, -2.08       # greenhouse front (bottom) / rear
DOOR_R = -1.0                  # rear edge of rear door
HATCH = 0.38                   # rear hatch slope (top edge pulled forward)
RAKE = 0.22                    # windshield lean back at top
TY = -0.35                     # turret ring Y

root = bpy.data.objects.new(P + "Root", None)
col.objects.link(root)

body = []   # static parts, joined later
def B(o):
    body.append(o)
    return o

# ---------------------------------------------------------------- body shell
tub = B(box("Tub", (0, -0.83, 0.975), (2.04, 2.84, 0.85), bevel=0.04))
hood = B(box("Hood", (0, 1.43, 0.985), (2.22, 1.76, 0.77), bevel=0.05,
             taper=[(lambda c: c.y > 0 and c.z > 0, (0, 0, -0.12)),     # hood drops to the nose
                    (lambda c: c.y > 0 and c.z < 0, (0, -0.12, 0))]))    # undercut nose
# wheel wells
for y in (WY, -WY):
    for o in (tub, hood):
        cut = cyl("Cut", (0, y, WZ), 0.58, 3.0, segs=32)
        bo = o.modifiers.new("Well", "BOOLEAN")
        bo.object = cut
        bo.operation = "DIFFERENCE"
        cut.hide_render = cut.hide_viewport = True
        body.append(cut)  # removed after apply
# move bevel after booleans
for o in (tub, hood):
    o.modifiers.move(0, len(o.modifiers) - 1)

# fender flares (black rubber-ish, wider than body)
for sx in (1, -1):
    for y, xb in ((WY, 1.11), (-WY, 1.02)):
        B(arch(f"Flare_{'L' if sx < 0 else 'R'}{'F' if y > 0 else 'R'}", y, 0,
               0.57, 0.66, *(sorted((sx * (xb - 0.06), sx * (xb + 0.07)))), m="Black"))

# greenhouse (cab) with raked windshield
gh = B(box("Cab", (0, (GH_F + GH_R) / 2, (BELT - 0.04 + ROOF) / 2),
           (GH_X * 2, GH_F - GH_R, ROOF - BELT + 0.04), bevel=0.035,
           taper=[(lambda c: c.y > 0 and c.z > 0, (0, -RAKE, 0)),
                  (lambda c: c.y < 0 and c.z > 0, (0, HATCH, 0))]))
# roof cap slightly overhanging (drip rail)
B(box("RoofCap", (0, (GH_F - RAKE + GH_R + HATCH) / 2 - 0.01, ROOF + 0.015),
      (GH_X * 2 + 0.03, GH_F - RAKE - GH_R - HATCH + 0.03, 0.05), bevel=0.02))

# ---------------------------------------------------------------- glass
gz0, gz1 = BELT + 0.05, ROOF - 0.07
def rake_y(z):  # windshield plane Y at height z
    return GH_F - RAKE * (z - (BELT - 0.04)) / (ROOF - BELT + 0.04)
e = 0.006
n = Vector((0, ROOF - BELT + 0.04, RAKE)).normalized() * e
for x0, x1 in ((-GH_X + 0.08, -0.04), (0.04, GH_X - 0.08)):
    pts = [(x0, rake_y(gz0), gz0), (x1, rake_y(gz0), gz0),
           (x1, rake_y(gz1), gz1), (x0, rake_y(gz1), gz1)]
    B(quad(f"Windshield_{'L' if x0 < 0 else 'R'}", [Vector(p) + n for p in pts]))
for sx in (1, -1):
    x = sx * (GH_X + e)
    # front door glass follows the A-pillar rake
    for nm, pts in (("F", [(x, -0.06, gz0), (x, rake_y(gz0) - 0.09, gz0),
                           (x, rake_y(gz1) - 0.09, gz1), (x, -0.06, gz1)]),
                    ("R", [(x, DOOR_R + 0.08, gz0), (x, -0.16, gz0),
                           (x, -0.16, gz1), (x, DOOR_R + 0.08, gz1)])):
        if sx < 0:
            pts = pts[::-1]
        B(quad(f"Glass_{'L' if sx < 0 else 'R'}{nm}", pts))


# ---------------------------------------------------------------- doors, handles, mirrors
for sx in (1, -1):
    xs = sx * 1.025
    for y in (GH_F - 0.02, -0.11, DOOR_R):   # door seams on the tub
        B(box("Seam", (xs, y, 1.03), (0.012, 0.018, 0.66), "Black", 0))
    for y in (-0.11, DOOR_R):                         # door seams on the cab
        B(box("Seam", (sx * (GH_X + 0.004), y, (BELT + ROOF) / 2), (0.012, 0.018, ROOF - BELT - 0.04), "Black", 0))
    B(box("Seam", (xs, (GH_F + DOOR_R) / 2, 0.72), (0.012, GH_F - DOOR_R + 0.02, 0.018), "Black", 0))
    for y in (0.08, -0.84):
        B(box("Handle", (sx * 1.035, y, 1.28), (0.03, 0.14, 0.035), "Black", 0.008))
    # mirror: arm bolted to A-pillar base, head outboard
    ay = GH_F - 0.04
    B(box("MirrorArm", (sx * (GH_X + 0.13), ay, BELT + 0.1), (0.28, 0.03, 0.03), "Black", 0.008))
    B(box("MirrorArmLo", (sx * (GH_X + 0.03), ay, BELT + 0.04), (0.08, 0.04, 0.14), "Black", 0.008))
    B(box("Mirror", (sx * (GH_X + 0.29), ay, BELT + 0.14), (0.06, 0.05, 0.30), "Black", 0.012))

# ---------------------------------------------------------------- nose
HF = 2.31  # hood front face Y
B(box("Grille", (0, HF + 0.005, 0.95), (1.1, 0.03, 0.42), "Black", 0.01))
for i in range(-5, 6):
    B(box("Slat", (i * 0.095, HF + 0.02, 0.95), (0.035, 0.02, 0.40), "Olive", 0.006))
for sx in (1, -1):
    B(box("LampBezel", (sx * 0.84, HF + 0.01, 1.00), (0.30, 0.04, 0.26), "Black", 0.012))
    B(box("Headlight", (sx * 0.84, HF + 0.035, 1.00), (0.22, 0.02, 0.19), "Headlight", 0.01))
    B(box("Taillight", (sx * 0.86, -2.25 - 0.012, 1.10), (0.16, 0.03, 0.22), "Taillight", 0.008))
    B(box("TowEye", (sx * 0.6, HF + 0.12, 0.52), (0.06, 0.12, 0.08), "Black", 0.01))
B(box("BumperF", (0, HF + 0.08, 0.56), (2.18, 0.14, 0.18), "Black", 0.02))
B(box("BumperR", (0, -2.33, 0.62), (2.0, 0.14, 0.18), "Black", 0.02))
B(box("Chassis", (0, 0, 0.47), (1.3, 4.3, 0.2), "Black", 0.02))
for y in (WY, -WY):
    B(cyl("Axle", (0, y, WZ), 0.07, WX * 2 - 0.2, "Black", segs=10))
# rear cargo hatch outline and cowl vent
B(box("HatchSeam", (0, -2.255, 1.30), (1.4, 0.012, 0.018), "Black", 0))
B(box("Cowl", (0, GH_F + 0.08, BELT - 0.08), (1.7, 0.10, 0.06), "Black", 0.01))

# ---------------------------------------------------------------- wheels
wheels = []
for tag, sx, y in (("FL", -1, WY), ("FR", 1, WY), ("RL", -1, -WY), ("RR", 1, -WY)):
    c = (sx * WX, y, WZ)
    tire = cyl(f"Wheel_{tag}", c, WR, 0.37, "Tire", segs=32, bevel=0.07)
    tire.modifiers["Bevel"].segments = 3
    # tread lugs: raised blocks around the circumference
    bm = bmesh.new()
    for i in range(24):
        a = 2 * math.pi * i / 24
        for side in (-1, 1):
            t = bmesh.ops.create_cube(bm, size=1.0)["verts"]
            for v in t:
                v.co = Vector((v.co.x * 0.13, v.co.y * 0.09, v.co.z * 0.035))
                v.co.x += side * 0.075
                v.co.x += 0.02 * side if i % 2 else 0
                v.co.z += WR - 0.012
                v.co = Matrix.Rotation(a, 3, "X") @ v.co
    tread = new_obj(f"Wheel_{tag}_Tread", bm, "Tire", c)
    rim = cyl(f"Wheel_{tag}_Rim", c, 0.28, 0.26, "Rim", segs=24, bevel=0.02, off=(sx * 0.07, 0, 0))
    hub = cyl(f"Wheel_{tag}_Hub", c, 0.10, 0.12, "Rim", segs=16, bevel=0.01, off=(sx * 0.22, 0, 0), r2=0.08)
    bm = bmesh.new()
    for i in range(8):
        a = 2 * math.pi * i / 8
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.022, radius2=0.022, depth=0.06)
        bmesh.ops.transform(bm, verts=r["verts"],
                            matrix=Matrix.Translation((sx * 0.205, 0.18 * math.cos(a), 0.18 * math.sin(a)))
                            @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    lugs = new_obj(f"Wheel_{tag}_Lugs", bm, "Gun", c)
    for ch in (tread, rim, hub, lugs):
        parent(ch, tire)
    wheels.append(tire)

# ---------------------------------------------------------------- turret
TZ = ROOF + 0.04
tur = []
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.62, radius2=0.60, depth=0.10)
yaw = new_obj("Turret_Yaw", bm, "Black", (0, TY, TZ + 0.05), 0.02)
# pedestal
tur.append(cyl("Pedestal", (0, TY + 0.05, TZ + 0.25), 0.06, 0.32, "Black", axis="Z", segs=12))
# angled shield: two halves + top/bottom bridging a gun slot, wings swept back
SY, SZ = TY + 0.48, TZ + 0.42
for sx in (1, -1):
    tur.append(box("ShieldHalf", (sx * 0.30, SY, SZ), (0.44, 0.04, 0.62), "Olive", 0.012, rot=(12, 0, 0)))
    w = box("ShieldWing", (sx * 0.66, SY - 0.13, SZ), (0.36, 0.04, 0.55), "Olive", 0.012,
            rot=(10, 0, sx * -35))
    tur.append(w)
for z in (-0.20, 0.22):
    s12, c12 = math.sin(math.radians(12)), math.cos(math.radians(12))
    tur.append(box("ShieldBridge", (0, SY - s12 * z, SZ + c12 * z),
                   (0.18, 0.04, 0.22 if z < 0 else 0.18), "Olive", 0.01, rot=(12, 0, 0)))
# skirt plates between ring and shield (so shield isn't floating)
for sx in (1, -1):
    tur.append(box("ShieldStrut", (sx * 0.3, SY - 0.12, TZ + 0.12), (0.05, 0.3, 0.05), "Black", 0.01, rot=(35, 0, 0)))

# ---------------------------------------------------------------- gun
GY, GZ = TY + 0.12, TZ + 0.45
gun = cyl("Gun_Pitch", (0, GY, GZ), 0.05, 0.22, "Gun", segs=12)        # trunnion at pivot
g = [box("Receiver", (0, GY + 0.02, GZ + 0.03), (0.13, 0.55, 0.14), "Gun", 0.012),
     cyl("Barrel", (0, GY + 0.72, GZ + 0.03), 0.028, 0.95, "Gun", "Y", 12),
     cyl("Jacket", (0, GY + 0.42, GZ + 0.03), 0.045, 0.28, "Gun", "Y", 12),
     cyl("Muzzle", (0, GY + 1.20, GZ + 0.03), 0.04, 0.08, "Gun", "Y", 12),
     box("Grips", (0, GY - 0.30, GZ), (0.2, 0.06, 0.03), "Gun", 0.01),
     box("Handle", (0, GY - 0.33, GZ - 0.05), (0.03, 0.03, 0.10), "Gun", 0.005),
     box("Ammo", (0.14, GY + 0.02, GZ - 0.02), (0.14, 0.30, 0.18), "Olive", 0.012),
     box("Cradle", (0, GY, GZ - 0.08), (0.09, 0.12, 0.14), "Black", 0.01)]

# ---------------------------------------------------------------- finalize
def apply_all(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.modifiers:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            old = o.data
            o.modifiers.clear()
            o.data = me
            me.name = old.name
            bpy.data.meshes.remove(old)

meshes = [o for o in bpy.data.objects if o.name.startswith(P) and o.type == "MESH"]
apply_all(meshes)
for o in [b for b in body if b.name.startswith(P + "Cut")]:
    body.remove(o)
    bpy.data.objects.remove(o, do_unlink=True)

def join(objs, active, name=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs + [active]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.ops.object.join()
    if name:
        active.name = active.data.name = name
    return active

join(tur, yaw)
join(g, gun)
if JOIN_BY_MATERIAL:
    groups = {}
    for o in body:
        groups.setdefault(o.data.materials[0].name, []).append(o)
    body = []
    for mname, objs in groups.items():
        body.append(join(objs[1:], objs[0], P + "Body_" + mname[len(P):]))

bpy.context.view_layer.update()
for o in body + wheels + [yaw]:
    parent(o, root)
parent(gun, yaw)

# clean data names / report
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
mesh_objs = [o for o in bpy.data.objects if o.name.startswith(P) and o.type == "MESH"]
for o in mesh_objs:
    o.data.name = o.name
    tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
bpy.ops.object.select_all(action="DESELECT")
print(f"HUMVEE_STATS meshes={len(mesh_objs)} tris={tris}")
