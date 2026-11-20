"""Studio scene and renders (bpy / Cycles). Parts are built in mm and placed at real scale."""

import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import geom as G

MM = 0.001


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h):
    return tuple(_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def plastic(name, col, rough, grain=0.035):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexc(col)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.5
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0          # object space is mm: fine moulded texture
    nz.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bev = nt.nodes.new("ShaderNodeBevel")
    bev.samples = 6
    bev.inputs["Radius"].default_value = 0.00028
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = grain
    bump.inputs["Distance"].default_value = 0.00004
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bev.outputs["Normal"], bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def metal(name, col, rough, aniso=0.0, bevel=0.00008):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexc(col)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Anisotropic"].default_value = aniso
    bev = nt.nodes.new("ShaderNodeBevel")
    bev.samples = 4
    bev.inputs["Radius"].default_value = bevel
    nt.links.new(bev.outputs["Normal"], b.inputs["Normal"])
    return m


def materials():
    return dict(
        graphite=plastic("UC_Graphite", "2A2C30", 0.46),
        graphite2=plastic("UC_Graphite_Dark", "1C1D20", 0.38, 0.02),
        orange=plastic("UC_Orange", "FF5F0F", 0.40, 0.025),
        blade=metal("UC_Blade_Steel", "C9CCD0", 0.24, 0.5, 0.00002),
        steel=metal("UC_Steel", "D4D6D8", 0.22),
        oxide=metal("UC_Black_Oxide", "2B2B2D", 0.36),
    )


def mesh_object(name, man, mat, coll, sharp_deg=32):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts).astype(int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], t.tolist())
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    except AttributeError:
        pass
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")   # keeps the large flats flat
    wn.keep_sharp = True
    wn.weight = 100
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, target, size, power, coll, color=(1, 1, 1), size_y=None):
    lt = bpy.data.lights.new(name, "AREA")
    lt.energy = power
    lt.color = color
    lt.size = size
    if size_y:
        lt.shape = "RECTANGLE"
        lt.size_y = size_y
    ob = bpy.data.objects.new(name, lt)
    coll.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    return sc


def setup_render(sc, samples, res):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.threads_mode = "AUTO"


def build(concept):
    """Fresh scene with the concept's parts under one root empty."""
    sc = reset()
    mats = materials()
    coll = bpy.data.collections.new(f"UC_{concept['name']}")
    sc.collection.children.link(coll)
    studio = bpy.data.collections.new("UC_Studio")
    sc.collection.children.link(studio)
    root = bpy.data.objects.new(f"{concept['name']}_root", None)
    coll.objects.link(root)
    lo = np.full(3, 1e9)
    hi = np.full(3, -1e9)
    for i, (name, man, mat) in enumerate(concept["parts"]):
        ob = mesh_object(f"{concept['name']}_{name}_{i:02d}", man, mats[mat], coll)
        ob.parent = root
        if name != "blade":
            a, b = G.bbox(man)
            lo, hi = np.minimum(lo, a), np.maximum(hi, b)
    # floor + world
    fm = bpy.data.materials.new("UC_Floor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = hexc("A9A8A4")
    fb.inputs["Roughness"].default_value = 0.62
    me = bpy.data.meshes.new("UC_Floor")
    s = 6.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(fm)
    floor = bpy.data.objects.new("UC_Floor", me)
    studio.objects.link(floor)
    w = bpy.data.worlds.new("UC_World")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.56, 0.58, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    return sc, root, studio, floor, (lo, hi)


def pose(root, floor, bounds, mode, yaw_deg):
    """mode 'flat': lying on its -Y face.  mode 'up': standing on its lower edge."""
    lo, hi = bounds
    c = (lo + hi) / 2
    Tm = Matrix.Translation(Vector(-c))
    Rz = Matrix.Rotation(math.radians(yaw_deg), 4, "Z")
    S = Matrix.Scale(MM, 4)
    if mode == "flat":
        Rx = Matrix.Rotation(math.radians(90), 4, "X")
        root.matrix_world = S @ Rz @ Rx @ Tm
        floor.location = (0, 0, (lo[1] - c[1]) * MM)
    else:
        root.matrix_world = S @ Rz @ Tm
        floor.location = (0, 0, (lo[2] - c[2]) * MM)
    return c

def to_world(root, p):
    return root.matrix_world @ Vector(p)


def lights(studio, kind, k=1.0):
    for ob in [o for o in studio.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(ob, do_unlink=True)
    t = (0, 0, 0)
    if kind == "hero":
        area("Key", (-0.45, 0.55, 0.75), t, 0.9, 30 * k, studio)
        area("Strip", (0.75, -0.25, 0.30), t, 0.22, 14 * k, studio, size_y=1.2)
        area("Front", (-0.1, -0.9, 0.45), t, 0.8, 5 * k, studio, (1.0, 0.97, 0.94))
        area("Top", (0.15, 0.0, 1.1), t, 1.2, 7 * k, studio)
    else:  # flat-lay / plan views: soft, slightly raking so the surfaces still model
        area("Key", (-0.5, 0.45, 0.9), t, 1.1, 34 * k, studio)
        area("Fill", (0.6, -0.5, 0.8), t, 1.2, 9 * k, studio, (1.0, 0.97, 0.94))
        area("Rake", (0.2, 0.9, 0.22), t, 0.3, 8 * k, studio, size_y=1.4)


def camera(sc, loc, target, lens, fstop=None, ortho=None):
    for ob in [o for o in sc.collection.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(ob, do_unlink=True)
    cam = bpy.data.cameras.new("UC_Cam")
    cam.lens = lens
    cam.clip_start, cam.clip_end = 0.01, 50
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new("UC_Cam", cam)
    sc.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    if fstop:
        cam.dof.use_dof = True
        cam.dof.focus_distance = (Vector(target) - Vector(loc)).length
        cam.dof.aperture_fstop = fstop
    sc.camera = ob
    return ob


def sph(dist, az_deg, el_deg, target=(0, 0, 0)):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return (target[0] + dist * math.cos(e) * math.sin(a), target[1] - dist * math.cos(e) * math.cos(a),
            target[2] + dist * math.sin(e))


def render_concept(concept, out, samples=96, scale=1.0, shots=None):
    sc, root, studio, floor, bounds = build(concept)
    key = concept["key"]
    lo, hi = bounds
    span = hi[0] - lo[0]
    tall = hi[2] - lo[2]
    paths = {}

    def go(tag, res):
        res = (int(res[0] * scale), int(res[1] * scale))
        setup_render(sc, samples, res)
        p = os.path.join(out, f"{concept['code']}_{key}_{tag}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths[tag] = p

    want = shots or ["hero", "side", "top", "detail"]
    if "hero" in want:
        pose(root, floor, bounds, "flat", 20)
        lights(studio, "hero", 1.15)
        d = 0.62 if tall < 60 else 0.74
        camera(sc, sph(d, -12, 31), (0, 0.006, -0.004), 105, fstop=16)
        go("hero", (1800, 1100))
    if "side" in want:
        pose(root, floor, bounds, "flat", 180)
        lights(studio, "flat", 0.85)
        camera(sc, (0, 0, 1.5), (0, 0, 0), 100, ortho=(span + 46) * MM)
        go("side", (1800, 620 if tall < 50 else 1000))
    if "top" in want:
        pose(root, floor, bounds, "up", 180)
        lights(studio, "flat", 0.85)
        camera(sc, (0, 0, 1.5), (0, 0, 0), 100, ortho=(span + 46) * MM)
        go("top", (1800, 420))
    if "detail" in want:
        pose(root, floor, bounds, "flat", 24)
        lights(studio, "hero")
        t = to_world(root, concept["detail"])
        camera(sc, sph(0.34, -14, 30, t), t, 100, fstop=20)
        go("detail", (1800, 1100))
    return paths
