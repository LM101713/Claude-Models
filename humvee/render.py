import bpy, math, sys, os
from mathutils import Vector
here = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(here, "humvee.py")).read())
out = os.path.join(here, "renders"); os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if not o.name.startswith("Humvee_"): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.68, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.7
bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.object
gm = bpy.data.materials.new("G"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.32, 0.27, 1)
g.data.materials.append(gm)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(-30))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
views = {"front34": ((6.5, 7.5, 3.4), (0, 0.2, 1.0), 40), "side": ((10, 0, 1.3), (0, 0, 1.0), 40),
         "top": ((0, 0, 11), (0, 0, 0), 40), "wheel": ((2.6, 2.4, 0.8), (0.95, 1.58, 0.45), 40),
         "rear34": ((-6, -7, 3.6), (0, -0.2, 1.1), 40), "turret": ((3.2, 2.6, 3.4), (0, -0.2, 2.2), 40)}
only = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else list(views)
for k in only:
    p, t, lens = views[k]
    cam.location = p; cam.data.lens = lens
    d = Vector(t) - Vector(p)
    cam.rotation_euler = d.to_track_quat("-Z", "Y" if k != "top" else "Y").to_euler()
    if k == "top": cam.rotation_euler = (0, 0, 0)
    sc.render.filepath = os.path.join(out, k + ".png")
    bpy.ops.render.render(write_still=True)
