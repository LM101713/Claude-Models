"""TP-01 TUBEPRESS: Blender project and renders (bpy, Cycles CPU). The tube is a generic stand-in."""

import math
import os

import bpy
import numpy as np
from manifold3d import Manifold
from mathutils import Vector

from .params import P

COL = {"frame": "2B2D31", "key": "FF6A13", "tube": "F3F4F6", "band": "2BB3B1", "cap": "2BB3B1",
       "counter": "E2DED6", "tile": "EEF0F2", "pei": "1D1D20"}
COLL = {}


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    COLL[name] = c
    return c


def obj(name, m, coll, mat, smooth=35):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts).astype(int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], t.tolist())
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(smooth))
    except AttributeError:
        pass
    return ob


def mat(name, hexcol, rough=0.45, layers=True, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if layers:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 2 * math.pi / 0.2
        nt.links.new(sep.outputs[layers if isinstance(layers, str) else "Z"], mul.inputs[0])
        sn = nt.nodes.new("ShaderNodeMath")
        sn.operation = "SINE"
        nt.links.new(mul.outputs[0], sn.inputs[0])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.08
        bump.inputs["Distance"].default_value = 0.03
        nt.links.new(sn.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def look_at(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, loc, target, lens=60, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 8000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["TP01_Cameras"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def light(name, loc, target, size, power, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    COLL["TP01_Studio"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)


def render(path, cam, res=(1800, 1200), samples=64):
    sc = bpy.context.scene
    sc.camera = cam
    if os.environ.get("SD_PREVIEW"):
        samples, res = 10, (int(res[0] * 0.4), int(res[1] * 0.4))
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = 0.5
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def hide(obs, state):
    for o in obs:
        o.hide_render = state
        o.hide_viewport = state


# -------------------------------------------------------------------------------------
def tube(width=52.0, wound=60.0, loading=False):
    """A generic laminate tube in assembled coordinates: a roll on the fork, a flat strip down
    through the nip, then the body widening to round, shoulder and cap below the frame."""
    x0 = (P.slot_l - width) / 2
    t_layer = 0.9
    r_roll = math.sqrt((P.shaft_d / 2) ** 2 + wound * t_layer / math.pi)
    roll = Manifold.cylinder(width, r_roll, r_roll, 96).rotate([0, 90, 0]).translate([x0, 0, P.axis_z])
    strip = Manifold.cube([width, 0.7, P.axis_z + 2.0]).translate([x0, -0.35, -2.0])
    if loading:  # flat end pulled up through the nip, crimp above the axis, nothing wound yet
        roll = Manifold.cube([width, 1.0, 8.0]).translate([x0, -0.5, P.axis_z + 8.0])
        strip = Manifold.cube([width, 0.7, P.axis_z + 18.0]).translate([x0, -0.35, -2.0])
    # body: hull from a flat seam just under the plate to a round section 70 mm down
    flat = [(x0 + u, s * 0.35, -2.5) for u in np.linspace(0, width, 24) for s in (-1, 1)]
    R = width / math.pi
    ring = [(P.slot_l / 2 + R * math.cos(a), R * 0.92 * math.sin(a), -70.0) for a in np.linspace(0, 2 * math.pi, 96, endpoint=False)]
    body = Manifold.hull_points(flat + ring)
    cyl = Manifold.cylinder(30.0, R, R, 96).scale([1, 0.92, 1]).translate([P.slot_l / 2, 0, -100.0])
    shoulder = Manifold.cylinder(8.0, 7.0, R, 96).translate([P.slot_l / 2, 0, -108.0])
    cap = Manifold.cylinder(18.0, 13.0, 13.0, 96).translate([P.slot_l / 2, 0, -126.0])
    band = Manifold.cylinder(14.0, R + 0.25, R + 0.25, 96).scale([1, 0.92, 1]).translate([P.slot_l / 2, 0, -96.0])
    return dict(tube=roll + strip + body + cyl + shoulder, band=band, cap=cap), -126.0


def render_all(frame, key, keyp, outdir, blend_path):
    os.makedirs(outdir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for n in ("TP01_Assembly", "TP01_Tube", "TP01_Scene", "TP01_Plate", "TP01_Studio", "TP01_Cameras"):
        collection(n)
    M = dict(frame=mat("TP01_Frame_Graphite", COL["frame"], 0.5), key=mat("TP01_Key_Orange", COL["key"], 0.42, "X"),
             tube=mat("Tube_Laminate", COL["tube"], 0.25, False, 0.6), band=mat("Tube_Band", COL["band"], 0.3, False),
             cap=mat("Tube_Cap", COL["cap"], 0.35, False), counter=mat("Counter", COL["counter"], 0.3, False),
             tile=mat("Wall", COL["tile"], 0.3, False), pei=mat("PEI", COL["pei"], 0.6, False))
    parts, zcap = tube()
    lift = -zcap  # the tube stands on its cap: everything moves up by this much
    fo = obj("TP01_Frame", frame.translate([0, 0, lift]), COLL["TP01_Assembly"], M["frame"])
    ko = obj("TP01_Key", key.translate([0, 0, lift]), COLL["TP01_Assembly"], M["key"])
    tubes = [obj("Tube_" + n, m.translate([0, 0, lift]), COLL["TP01_Tube"], M[n], 50) for n, m in parts.items()]
    cx = P.slot_l / 2
    counter = obj("Counter", Manifold.cube([900, 600, 20]).translate([cx - 450, -250, -20]), COLL["TP01_Scene"], M["counter"], 10)
    wall = obj("Wall", Manifold.cube([900, 20, 700]).translate([cx - 450, 160, -20]), COLL["TP01_Scene"], M["tile"], 10)
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.93, 0.94, 0.96, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    zc = lift + 10
    light("Key", (cx - 300, -420, zc + 420), (cx, 0, zc), 300, 520000)
    light("Fill", (cx + 420, -180, zc + 150), (cx, 0, zc), 360, 180000, (0.95, 0.97, 1.0))
    light("Rim", (cx + 120, 120, zc + 420), (cx, 0, zc), 220, 120000, (1.0, 0.97, 0.92))
    cams = dict(
        hero=camera("CAM_01_hero", (cx - 210, -300, lift + 150), (cx - 6, 0, lift - 25), 50),
        parts=camera("CAM_02_parts", (cx - 115, -235, 170), (cx - 10, -24, 12), 50),
        load=camera("CAM_03_load", (cx - 150, -230, lift + 120), (cx - 25, 0, lift + 10), 55),
        plate=camera("CAM_04_plate", (90 + 160, -150 + 90, 260), (90, 90, 12), 45),
    )
    only = os.environ.get("TP_ONLY", "01,02,03,04").split(",")
    if "01" in only:
        render(os.path.join(outdir, "01_hero.png"), cams["hero"])
    # 02: the two parts apart, frame on the counter, key pulled out along its axis and lifted
    hide(tubes, True)
    fo.location = (0, 0, -lift)
    ko.location = (-18, -58, -lift - (P.axis_z - P.r_tip))
    if "02" in only:
        render(os.path.join(outdir, "02_parts.png"), cams["parts"])
    # 03: loading: tube through the nip, key half-way in (mark aligned)
    fo.location = (0, 0, 0)
    ko.location = (-46, 0, 0)
    load_parts, _ = tube(loading=True)
    load_objs = [obj("TubeLoad_" + n, m.translate([0, 0, lift]), COLL["TP01_Tube"], M[n], 50) for n, m in load_parts.items()]
    hide(tubes, True)
    if "03" in only:
        render(os.path.join(outdir, "03_loading.png"), cams["load"])
    ko.location = (0, 0, 0)
    for o in load_objs:
        bpy.data.objects.remove(o)
    # 04: print plate
    hide(tubes + [fo, ko, counter, wall], True)
    from .validate import plate_layout
    plate_objs = [obj("PLATE_" + n, m.translate([90, 90, 0]), COLL["TP01_Plate"], M["key"] if "Key" in n else M["frame"])
                  for n, m in plate_layout(frame, keyp)]
    plate_objs.append(obj("A1mini_plate", Manifold.cube([180, 180, 1]).translate([0, 0, -1]), COLL["TP01_Plate"], M["pei"], 10))
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.86, 0.87, 0.89, 1)
    if "04" in only:
        render(os.path.join(outdir, "04_print_plate.png"), cams["plate"], res=(1600, 1100))
    hide(plate_objs, True)
    hide(tubes + [fo, ko, counter, wall], False)
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in ("params.py", "geom.py", "validate.py", "scene.py"):
        t = bpy.data.texts.new("tp_" + fn)
        with open(os.path.join(here, fn)) as f:
            t.write(f.read())
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
