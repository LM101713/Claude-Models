"""BK-01 BOOKMARKS: the Blender project and the product renders (bpy).

Collections in the .blend:
    BK01_Part        the six colour regions exactly as exported (print frame, mm)
    BK01_Bookmarks   prop bookmarks standing in the compartment (the fit-test set)
    BK01_Studio      sweep, lights
    BK01_Cameras     front / back / left / right / top / three-quarter / hero / plate
The generator scripts are embedded as text blocks so the .blend is self-documenting.
"""

import glob
import math
import os

import bpy
import numpy as np
from mathutils import Vector

from . import params as P
from .export import mesh_arrays

COLL = {}


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    COLL[name] = c
    return c


def mesh_object(name, m, coll, mat=None, smooth_deg=35, verts=None, tris=None):
    if m is not None:
        v, t = mesh_arrays(m)
    else:
        v, t = verts, tris
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(v).tolist(), [], np.asarray(t).tolist())
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(smooth_deg))
    except AttributeError:
        pass
    return ob


def petg(name, hexcol, rough=0.32, layer=True, sss=0.0, bump=0.06):
    """Satin PETG with 0.2 mm layer lines running horizontally (the part prints upright)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    if sss:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.5)
        bsdf.inputs["Subsurface Scale"].default_value = 0.6
    if not layer:
        return m
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / 0.2
    links.new(sep.outputs["Z"], mul.inputs[0])
    sin = nodes.new("ShaderNodeMath")
    sin.operation = "SINE"
    links.new(mul.outputs[0], sin.inputs[0])
    bp = nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.02
    links.new(sin.outputs[0], bp.inputs["Height"])
    links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def simple(name, hexcol, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def wood(name="BK_Wood"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.5
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.5, 2.5, 0.12)
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.6
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Distortion"].default_value = 0.8
    links.new(mp.outputs[0], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_lin("A9784A")
    ramp.color_ramp.elements[1].color = hex_lin("D6A877")
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def look_at(ob, target, up="Y"):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", up).to_euler()


def camera(name, loc, target, lens=85, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 8000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["BK01_Cameras"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def area_light(name, loc, target, size, power, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    COLL["BK01_Studio"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def sweep(mat, name, coll, side=1):
    """A curved studio backdrop: floor curving up behind the subject (behind = side * +Y)."""
    verts, faces = [], []
    n, w = 40, 900.0
    pts = [(y, 0.0) for y in np.linspace(450, -150, 12)]
    for i in range(1, n + 1):
        a = i / n * (math.pi / 2)
        pts.append((-150 - 160 * math.sin(a), 160 - 160 * math.cos(a)))
    pts.append((-310, 700))
    for j, (y, z) in enumerate(pts):
        verts += [(P.W / 2 - w / 2, -side * y, z), (P.W / 2 + w / 2, -side * y, z)]
        if j:
            k = 2 * j
            faces.append((k - 2, k - 1, k + 1, k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me)
    COLL[coll].objects.link(ob)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return ob


# =====================================================================================
# props: the bookmark set used for the fit test
# =====================================================================================


def tassel(coll, mat, top, length=38, r=2.2, strands=26):
    """Silk tassel hanging from `top` (x, y, z)."""
    rng = np.random.default_rng(3)
    obs = []
    for i in range(strands):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.2, r)
        dx, dy = rr * math.cos(a), rr * math.sin(a)
        cu = bpy.data.curves.new(f"strand{i}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.32
        sp = cu.splines.new("POLY")
        sp.points.add(2)
        L = length * rng.uniform(0.92, 1.0)
        pts = [(top[0], top[1], top[2]), (top[0] + dx * 0.6, top[1] + dy * 0.6, top[2] - 8),
               (top[0] + dx * 1.4, top[1] + dy * 1.4, top[2] - L)]
        for p_, q in zip(sp.points, pts):
            p_.co = (*q, 1.0)
        ob = bpy.data.objects.new(f"Tassel_strand_{i}", cu)
        coll.objects.link(ob)
        cu.materials.append(mat)
        obs.append(ob)
    # the binding knot
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.6, location=(top[0], top[1], top[2] - 4))
    knot = bpy.context.active_object
    for c in knot.users_collection:
        c.objects.unlink(knot)
    coll.objects.link(knot)
    knot.scale = (1, 1, 1.5)
    knot.data.materials.append(mat)
    return obs


def build(result, out, props, render=False, samples=96, shots=None, plan_name="FULL"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    for name in ("BK01_Part", "BK01_Bookmarks", "BK01_Studio", "BK01_Sweep", "BK01_Sweep_Back", "BK01_Cameras"):
        collection(name)

    plan = P.PLANS[plan_name]
    fil = {s: petg(f"BK_Filament{s}_{n}", h, sss=0.05 if s == 1 else 0.0) for s, (n, h) in plan["filaments"].items()}
    mats = {k: fil[plan["slots"][k]] for k in P.PARTS}
    for k, m in result["parts"].items():
        mesh_object(f"BK01_{k}", m, COLL["BK01_Part"], mats[k])

    # ---------------- bookmark props (same boxes the fit test uses)
    pm = {"fabric": simple("BK_Fabric", "F2D7DC", 0.8), "wood": wood(), "leather": simple("BK_Leather", "A8653A", 0.55),
          "card": simple("BK_Card", "F7F1E6", 0.7), "silk": simple("BK_Silk", "E89AB5", 0.45)}
    for b in props:
        v, t = mesh_arrays(b["solid"])
        ob = mesh_object("Bookmark_" + b["name"], None, COLL["BK01_Bookmarks"], pm[b["mat"]], verts=v, tris=t, smooth_deg=20)
        if b.get("tassel"):
            tassel(COLL["BK01_Bookmarks"], pm["silk"], b["tassel"])

    # ---------------- studio
    sm = simple("BK_Sweep", "F6EEF1", 0.85)
    sweep(sm, "Sweep", "BK01_Sweep", side=1)          # backdrop behind the book for front views
    sweep(sm, "Sweep_Back", "BK01_Sweep_Back", side=-1)  # turned round for the back view
    world = bpy.data.worlds.new("BK_World")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = hex_lin("FBF5F7")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    c = Vector((P.W / 2, P.D / 2, P.H / 2))
    area_light("Key", (c.x - 220, c.y - 260, c.z + 230), tuple(c), 220, 6.5e5)
    area_light("Fill", (c.x + 300, c.y - 200, c.z + 40), tuple(c), 300, 2.4e5)
    area_light("Rim", (c.x + 60, c.y + 300, c.z + 260), tuple(c), 200, 3.0e5)
    area_light("Top", (c.x, c.y, c.z + 380), tuple(c), 220, 1.6e5)

    # ---------------- cameras (the front cover faces -Y)
    dist = 520
    cams = {
        "front": camera("Cam_Front", (c.x, c.y - dist, c.z), c, 135),
        "back": camera("Cam_Back", (c.x, c.y + dist, c.z), c, 135),
        "left": camera("Cam_Left_Spine", (c.x - dist, c.y, c.z), c, 165),
        "right": camera("Cam_Right_Pages", (c.x + dist, c.y, c.z), c, 165),
        "top": camera("Cam_Top", (c.x, c.y, c.z + dist), c, 165),
        "three_q": camera("Cam_ThreeQuarter", (c.x + 250, c.y - 330, c.z + 190), c + Vector((0, 0, -4)), 85),
        "hero": camera("Cam_Hero", (c.x - 165, c.y - 345, c.z + 80), c + Vector((6, 0, 36)), 70),
        "detail": camera("Cam_Detail", (c.x - 60, c.y - 210, c.z + 40), Vector((P.ART_CX, P.D - P.YF, 46)), 100),
    }
    cams["top"].rotation_euler = (0, 0, 0)   # looking down, front cover (-Y) at the bottom of the frame

    # ---------------- embed the generator scripts
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in [p for p in sorted(glob.glob(os.path.join(here, "bk", "*.py"))) + [os.path.join(here, "bookmarks.py")] if os.path.exists(p)]:
        tb = bpy.data.texts.new(os.path.relpath(f, here))
        tb.write(open(f).read())

    setup_render(sc, samples)
    os.makedirs(os.path.join(out, "models"), exist_ok=True)
    blend = os.path.join(out, "models", "BK01_Bookmarks.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("saved", blend)
    if render:
        render_all(sc, cams, out, shots)
    return blend


def setup_render(sc, samples, res=(1400, 1400)):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.45


def set_visible(names):
    for name, c in COLL.items():
        if name == "BK01_Cameras":
            continue
        vis = name in names
        c.hide_render = not vis
        c.hide_viewport = not vis


SHOTS = [
    # file, camera, collections, resolution
    ("01_hero.png", "hero", ["BK01_Part", "BK01_Bookmarks", "BK01_Studio", "BK01_Sweep"], (1400, 1400)),
    ("02_front.png", "front", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (1200, 1300)),
    ("03_three_quarter.png", "three_q", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (1400, 1400)),
    ("04_back.png", "back", ["BK01_Part", "BK01_Studio", "BK01_Sweep_Back"], (1200, 1300)),
    ("05_left_spine.png", "left", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (900, 1300)),
    ("06_right_pages.png", "right", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (900, 1300)),
    ("07_top.png", "top", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (1300, 900)),
    ("08_front_detail.png", "detail", ["BK01_Part", "BK01_Studio", "BK01_Sweep"], (1400, 1100)),
]


def render_all(sc, cams, out, only=None):
    R = os.path.join(out, "renders")
    os.makedirs(R, exist_ok=True)
    for fname, cam, colls, res in SHOTS:
        if only and not any(fname.startswith(k) for k in only):
            continue
        set_visible(colls)
        sc.camera = cams[cam]
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = os.path.join(R, fname)
        bpy.ops.render.render(write_still=True)
        print("rendered", fname)
    set_visible(list(COLL))
