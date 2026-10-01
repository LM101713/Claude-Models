"""Render the six money makers (no export).  Run: blender --background --python render_makers.py"""
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["NO_EXPORT"] = "1"
ns = {"__file__": os.path.join(HERE, "makers.py"), "__name__": "makers"}
exec(compile(open(ns["__file__"]).read(), ns["__file__"], "exec"), ns)
B, ORIGINS, ORDER = ns["B"], ns["ORIGINS"], ns["ORDER"]
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene


def b(p):
    return Vector((p[0], -p[2], p[1]))


sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sc.collection.objects.link(sun)
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
for (name, (x, y, z)) in B.lamps:
    L = bpy.data.lights.new(name, "POINT")
    L.energy = 600
    o = bpy.data.objects.new("PL_" + name, L)
    o.location = b((x, y - 0.8, z))
    sc.collection.objects.link(o)
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.7, 0.82, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=600)
gm = bpy.data.materials.new("GroundM")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.33, 0.25, 1)
bpy.context.object.data.materials.append(gm)
bpy.context.object.location.z = -0.01
sc.render.engine = "CYCLES"
sc.cycles.samples = 28
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam


def shot(name, pos, target, lens, res):
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.location = b(pos)
    cam.data.lens = lens
    cam.rotation_euler = (b(target) - b(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("[RENDER]", name)


import sys
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
if not only or "makers_lineup" in only:
    shot("makers_lineup", (0, 75, 175), (0, 8, 0), 24, (1600, 700))
for nm in ORDER:
    if only and "maker_" + nm not in only:
        continue
    ox, _, oz = ORIGINS[nm]
    far = 1.45 if nm == "MissileSilo" else 1.0
    shot("maker_" + nm, (ox + 26 * far, 22 * far, oz + 34 * far), (ox, 8 if far == 1 else 13, oz), 30, (800, 600))
