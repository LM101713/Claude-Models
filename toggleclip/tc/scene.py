"""
Blender project and renders for TC-03 (bpy 4.2, run after toggleclip.py):

    python tc/scene.py            # build the .blend
    python tc/scene.py --render   # ...and render the product shots

Collections: TC03_Parts (one source mesh per printed part, print notes as custom properties),
TC03_Assembly (locked, blade bar pressed flush), TC03_Open (lever lifted 150 deg), TC03_Exploded,
TC03_PrintPlate (220 x 220 plate, print orientations), TC03_Cameras, TC03_Lights, TC03_Studio.
Every posed object is a linked instance of its part mesh (except the deformed locked blade).
"""

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from tc import mech as M  # noqa: E402
from tc import export as EX  # noqa: E402
from tc.params import P, D  # noqa: E402

HEX = {"graphite": "2B2D31", "orange": "FF6A13", "sand": "D9D3C7", "backdrop": "D2CFC9"}
LOOK = {"upper": ("graphite", "Z"), "blade": ("sand", "Y"), "blade_firm": ("sand", "Y"),
        "lever": ("orange", "Z"), "bail_a": ("graphite", "Y"), "bail_b": ("graphite", "Y"),
        "pin_p": ("sand", "Y"), "pin_h": ("sand", "Y")}
NAMES = {"upper": "Upper jaw", "blade": "Blade (Standard)", "blade_firm": "Blade (Firm)", "lever": "Lever",
         "bail_a": "Bail A (pegs)", "bail_b": "Bail B", "pin_p": "Lever pin 12", "pin_h": "Hinge pin 18"}
COLL = {}


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(c)
    COLL[name] = c
    return c


def material(name, hexcol, rough, axis, bump=0.12):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / 0.2       # 0.2 mm layers
    nt.links.new(sep.outputs[axis], mul.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    nt.links.new(mul.outputs[0], sn.inputs[0])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.03
    nt.links.new(sn.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mesh_object(name, v, t, coll, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, p)) for p in v], [], [tuple(map(int, f)) for f in t])
    me.validate()
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(30))
    except AttributeError:
        pass
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def inst(src, name, coll, mat4):
    ob = bpy.data.objects.new(name, src.data)
    ob.matrix_world = Matrix([list(r) for r in mat4])
    coll.objects.link(ob)
    for k in src.keys():
        ob[k] = src[k]
    return ob


def add_camera(name, loc, target, lens=85, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start, cam.clip_end = 1.0, 5000.0
    cam.sensor_width = 36
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["TC03_Cameras"].objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def add_area(name, loc, target, size, power, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size, lt.energy, lt.color = size, power, color
    ob = bpy.data.objects.new(name, lt)
    COLL["TC03_Lights"].objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def studio(z_floor):
    coll = collection("TC03_Studio")
    bm = bmesh.new()
    Rb = 260.0
    prof = [(-1000.0, 0.0)] + [(320.0 + Rb * math.sin(math.radians(90 * i / 24)),
                                Rb - Rb * math.cos(math.radians(90 * i / 24))) for i in range(25)]
    prof.append((320.0 + Rb, 1300.0))
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-1400.0, 1400.0)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new("Backdrop")
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("TC03_Backdrop", me)
    coll.objects.link(ob)
    m = bpy.data.materials.new("Backdrop")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(HEX["backdrop"])
    b.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    ob.location.z = z_floor


def setup_render(scene, samples, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.render.image_settings.file_format = "PNG"
    w = scene.world or bpy.data.worlds.new("World")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_lin("D6D3CE")
    bg.inputs["Strength"].default_value = 0.35
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--only", default="")
    a = ap.parse_args([x for x in sys.argv[1:] if x != "--"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    data = np.load(os.path.join(ROOT, "build", "meshes.npz"))
    for c in ("TC03_Parts", "TC03_Assembly", "TC03_Open", "TC03_Exploded", "TC03_PrintPlate",
              "TC03_Cameras", "TC03_Lights"):
        collection(c)
    mats = {}
    src = {}
    notes = {k: n for k, _, _, _, n in EX.BOM + EX.OPTIONAL}
    for k, (col, axis) in LOOK.items():
        key = f"{col}_{axis}"
        if key not in mats:
            mats[key] = material(f"TC_{col}_{axis}", HEX[col], {"graphite": 0.55, "orange": 0.42, "sand": 0.5}[col], axis)
        ob = mesh_object(f"TC03_{k}", data[f"{k}_v"], data[f"{k}_t"], COLL["TC03_Parts"], mats[key])
        ob["odd_layer_part"] = NAMES[k]
        ob["print_orientation"] = notes.get(k, "")
        ob["status"] = "CAD only - not yet printed"
        src[k] = ob
    COLL["TC03_Parts"].hide_render = True
    COLL["TC03_Parts"].hide_viewport = True
    main_parts = ("upper", "blade", "lever", "bail_a", "bail_b", "pin_p", "pin_h")

    # locked assembly: the blade's bar pressed flush (deformed copy of the mesh)
    st0 = M.pose(0.0)
    for k in main_parts:
        if k == "blade":
            v = EX.deform_blade(data["blade_v"])
            ob = mesh_object("ASM_blade_locked", v, data["blade_t"], COLL["TC03_Assembly"], src["blade"].data.materials[0])
            ob["note"] = "blade shown with its bar pressed flush against the jaw (bag 0 mm)"
        else:
            inst(src[k], f"ASM_{k}", COLL["TC03_Assembly"], EX.pose_matrix(k, st0))
    # open: lever lifted 150 deg, jaws open, blade unloaded
    st1 = M.pose(math.radians(150.0))
    for k in main_parts:
        Mx = EX.pose_matrix(k, st1).copy()
        Mx[2, 3] += 12.0          # lifted so the open blade's nose clears the studio floor
        inst(src[k], f"OPEN_{k}", COLL["TC03_Open"], Mx)
    # exploded (from the locked pose)
    # everything lifted 30 mm so the blade stays above the studio floor
    off = {"upper": (0, 0, 30), "lever": (0, 0, 56), "blade": (0, 0, 8), "bail_a": (14, -30, 30),
           "bail_b": (14, 30, 30), "pin_p": (0, -48, 30), "pin_h": (0, 40, 8)}
    for k in main_parts:
        Mx = EX.pose_matrix(k, st0).copy()
        Mx[:3, 3] += np.array(off[k], float)
        inst(src[k], f"EXP_{k}", COLL["TC03_Exploded"], Mx)
    # print plate (220 x 220), parts in print orientation
    rep = json.load(open(os.path.join(ROOT, "models", "TC03_validation.json")))
    pos = rep["plate"]["positions"]
    for k, stem, _, _, _ in EX.BOM:
        v = data[f"{k}_v"]
        w, _ = EX.to_print(k, v)
        R = EX.ORIENT[k]
        lo = (v @ R.T).min(0)
        hi = (v @ R.T).max(0)
        c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
        Mx = np.eye(4)
        Mx[:3, :3] = R
        Mx[:3, 3] = np.array([pos[stem][0] - 110.0, pos[stem][1] - 110.0, 0.0]) - c
        inst(src[k], f"PLATE_{k}", COLL["TC03_PrintPlate"], Mx)
    pm = bpy.data.materials.new("Plate")
    pm.use_nodes = True
    pb = pm.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = hex_lin("4A4B4F")
    pb.inputs["Roughness"].default_value = 0.85
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new("BuildPlate")
    bm.to_mesh(me)
    bm.free()
    plate = bpy.data.objects.new("PLATE_BuildPlate_220", me)
    plate.scale = (220, 220, 1.2)
    plate.location = (0, 0, -0.61)
    me.materials.append(pm)
    COLL["TC03_PrintPlate"].objects.link(plate)

    for c in ("TC03_Assembly", "TC03_Open", "TC03_Exploded", "TC03_PrintPlate"):
        COLL[c].hide_render = True
    studio(z_floor=-15.6)
    setup_render(scene, a.samples, (1800, 1100))
    add_area("Key", (-160, -230, 240), (60, 0, 0), 220, 6.0e5, (1.0, 0.97, 0.93))
    add_area("Fill", (300, -120, 120), (60, 0, 0), 260, 1.6e5, (0.92, 0.95, 1.0))
    add_area("Rim", (120, 260, 180), (60, 0, 0), 170, 3.2e5)
    add_area("Top", (60, 0, 420), (60, 0, 0), 320, 2.0e5)
    cams = {
        "01_hero": add_camera("CAM_01_hero", (-60, -190, 120), (62, 0, -2), 70),
        "02_exploded": add_camera("CAM_02_exploded", (-70, -215, 150), (64, 0, 26), 50),
        "03_side_locked": add_camera("CAM_03_side_locked", (62, -300, 0), (62, 0, -1), 85, ortho=150),
        "04_open": add_camera("CAM_04_open", (-40, -200, 122), (70, 0, 12), 58),
        "05_nose_detail": add_camera("CAM_05_nose_detail", (175, -95, 55), (112, 0, -1), 100),
        "06_side_open": add_camera("CAM_06_side_open", (74, -300, 12), (74, 0, 12), 85, ortho=182),
        "07_print_plate": add_camera("CAM_07_print_plate", (0, -230, 300), (0, 8, 0), 50),
    }
    show = {"01_hero": ["TC03_Assembly"], "02_exploded": ["TC03_Exploded"], "03_side_locked": ["TC03_Assembly"],
            "04_open": ["TC03_Open"], "05_nose_detail": ["TC03_Assembly"], "06_side_open": ["TC03_Open"],
            "07_print_plate": ["TC03_PrintPlate"]}
    scene.camera = cams["01_hero"]
    COLL["TC03_Assembly"].hide_render = False
    # embed the sources
    for fn in ["toggleclip.py"] + [os.path.join("tc", f) for f in sorted(os.listdir(HERE)) if f.endswith(".py")]:
        tb = bpy.data.texts.new(os.path.basename(fn))
        tb.write(open(os.path.join(ROOT, fn)).read())
    blend = os.path.join(ROOT, "models", "TC03_ToggleClip.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("[TC-03] saved", blend, flush=True)
    if a.render:
        os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
        for name, cam in cams.items():
            if a.only and name not in a.only.split(","):
                continue
            for c in ("TC03_Assembly", "TC03_Open", "TC03_Exploded", "TC03_PrintPlate"):
                COLL[c].hide_render = c not in show[name]
            COLL["TC03_Studio"].hide_render = name == "07_print_plate" and False
            scene.camera = cam
            scene.render.filepath = os.path.join(ROOT, "renders", name + ".png")
            bpy.ops.render.render(write_still=True)
            print("[TC-03] rendered", name, flush=True)


if __name__ == "__main__":
    main()
