"""Build the base (no export) and render verification views.
Run:  blender --background --python render_base.py [-- view1 view2 ...]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["NO_EXPORT"] = "1"
ns = {"__file__": os.path.join(HERE, "military_base.py"), "__name__": "military_base"}
exec(compile(open(ns["__file__"]).read(), ns["__file__"], "exec"), ns)
B, RESERVED, FIT_TESTS = ns["B"], ns["RESERVED"], ns["FIT_TESTS"]
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
col = sc.collection


def b(p):
    return Vector((p[0], -p[2], p[1]))


def emis(name, rgb, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Emission Color"].default_value = (*rgb, 1)
    bs.inputs["Emission Strength"].default_value = 1.5
    bs.inputs["Alpha"].default_value = alpha
    return m


def rbox(name, x0, x1, y0, y1, z0, z1, mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.location = b(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o.scale = (x1 - x0, z1 - z0, y1 - y0)
    o.data.materials.append(mat)
    return o


# gameplay footprints (render only)
COLS = {"PlotSpawn": (0.1, 0.5, 1.0), "Collector": (1.0, 0.85, 0.1), "UpgradePad": (0.7, 0.2, 1.0),
        "VehiclePad": (0.1, 0.9, 0.9), "Gate": (1.0, 0.2, 0.2), "DrivePath": (1.0, 0.5, 0.1),
        "MakerSlot": (0.2, 0.9, 0.2)}
overlays = []
for (nm, x0, x1, z0, z1, y0, y1, _) in RESERVED:
    key = next(k for k in COLS if nm.startswith(k))
    if nm.endswith("_front"):
        continue
    h = 0.35 if not key == "DrivePath" else 0.2
    overlays.append(rbox("OV_" + nm, x0, x1, 0, h, z0, z1, emis("ov_" + nm, COLS[key], 0.55 if key == "DrivePath" else 0.9)))
# dummies: player 2x5x2 / Humvee 8x6x16 at the fit-test spots
red = emis("dummy", (0.9, 0.08, 0.08))
dummies = []
for name, (x0, x1, y0, y1, z0, z1) in FIT_TESTS:
    if name.startswith("Humvee"):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        w, l = (8, 16) if (z1 - z0) > (x1 - x0) else (16, 8)
        dummies.append(rbox("DUMMY_" + name, cx - w / 2, cx + w / 2, y0, y0 + 6, cz - l / 2, cz + l / 2, red))
    else:
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        dummies.append(rbox("DUMMY_" + name, cx - 1, cx + 1, y0, y0 + 5, cz - 1, cz + 1, red))

# lights
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
col.objects.link(sun)
sun.data.energy = 3.2
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
for (name, (x, y, z)) in B.lamps:
    L = bpy.data.lights.new(name, "POINT")
    L.energy = 2600 if "Beacon" not in name else 2000
    L.color = (1, 0.9, 0.75) if "Beacon" not in name else (1, 0.15, 0.1)
    L.shadow_soft_size = 1.0
    o = bpy.data.objects.new("PL_" + name, L)
    o.location = b((x, y - 1.2, z))
    col.objects.link(o)
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.7, 0.82, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
bpy.ops.mesh.primitive_plane_add(size=900)
gp = bpy.context.object
gm = bpy.data.materials.new("GroundM")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.33, 0.25, 1)
gp.data.materials.append(gm)
gp.location.z = -0.01

sc.render.engine = "CYCLES"
sc.cycles.samples = 28
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
col.objects.link(cam)
sc.camera = cam

VIEWS = {
    "map": dict(ortho=430, pos=(0, 400, 0), target=(0, 0, 0), res=(1400, 1400)),
    "ext_front_right": dict(pos=(290, 130, 290), target=(0, 0, 0), lens=30),
    "ext_front_left": dict(pos=(-290, 130, 290), target=(0, 0, 0), lens=30),
    "ext_back_left": dict(pos=(-290, 130, -290), target=(0, 0, 0), lens=30),
    "ext_back_right": dict(pos=(290, 130, -290), target=(0, 0, 0), lens=30),
    "core": dict(pos=(62, 34, 66), target=(0, 32, 0), lens=26),
    "core_ground": dict(pos=(16, 4, 30), target=(0, 18, 0), lens=18),
    "int_hq_ground": dict(pos=(-11, 6, -125), target=(22, 5, -162), lens=16),
    "int_hq_upper": dict(pos=(-11, 19, -125), target=(22, 18, -162), lens=16),
    "int_hq_roof": dict(pos=(-36, 34, -124), target=(10, 26, -160), lens=20),
    "int_barracks": dict(pos=(-135.5, 6.5, 25), target=(-178, 4, 25), lens=16),
    "int_hangar": dict(pos=(102, 9, -123), target=(172, 10, -178), lens=16),
    "int_tower": dict(pos=(193.5, 29, 193.5), target=(176, 22, 180), lens=16),
    "int_garage": dict(pos=(189, 9, 130), target=(142, 5, 80), lens=16),
    "fit_gate": dict(pos=(44, 22, 150), target=(0, 6, 196), lens=24),
    "fit_garage": dict(pos=(112, 16, 64), target=(140, 5, 83), lens=24),
    "fit_doorway": dict(pos=(-30, 7, -129), target=(-14, 3, -146), lens=18),
}
want = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(VIEWS)
for k in want:
    v = VIEWS[k]
    show_ov = k == "map"
    for o in overlays:
        o.hide_render = not show_ov
    for o in dummies:
        o.hide_render = not (k.startswith("fit") or k == "map")
    rx, ry = v.get("res", (1280, 800))
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cam.location = b(v["pos"])
    if "ortho" in v:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = v["ortho"]
        cam.rotation_euler = (0, 0, 0)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = v["lens"]
        d = b(v["target"]) - b(v["pos"])
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.3
    cam.data.clip_end = 2000
    sc.render.filepath = os.path.join(OUT, k + ".png")
    bpy.ops.render.render(write_still=True)
    print("[RENDER]", k)
