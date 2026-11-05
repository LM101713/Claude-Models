"""Scene organisation, materials, studio, cameras and render shots."""

import math

import bpy
import bmesh
from mathutils import Matrix, Vector

from . import geom as G
from . import parts as PT
from .params import P, D

HEX = {"graphite": "2B2D31", "orange": "FF6A13", "sand": "D9D3C7", "backdrop": "C9C6C0"}


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def make_material(name, hexcol, rough=0.5, layer_axis="Z", bump=0.10, ghost=0.0):
    """Matte PETG with FDM layer lines (0.2 mm period along the part's print axis)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.45
    if ghost:
        bsdf.inputs["Alpha"].default_value = ghost
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / 0.2
    links.new(sep.outputs[layer_axis], mul.inputs[0])
    sin = nodes.new("ShaderNodeMath")
    sin.operation = "SINE"
    links.new(mul.outputs[0], sin.inputs[0])
    bp = nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.03
    links.new(sin.outputs[0], bp.inputs["Height"])
    links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def set_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def smooth_by_angle(ob, deg=32):
    me = ob.data
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(deg))
    except AttributeError:
        me.use_auto_smooth = True
        me.auto_smooth_angle = math.radians(deg)


def inst(src, name, coll, mat=Matrix()):
    c = bpy.data.objects.new(name, src.data)
    c.matrix_world = mat
    coll.objects.link(c)
    for k in src.keys():
        c[k] = src[k]
    return c


def add_camera(name, loc, target, lens=85, ortho=None, coll=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 5000.0
    cam.sensor_width = 36
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    (coll or G.COLL["ML02_Cameras"]).objects.link(ob)
    ob.location = loc
    d_ = Vector(target) - Vector(loc)
    if abs(d_.x) < 1e-6 and abs(d_.y) < 1e-6:  # straight down: +X right, +Y up in the image
        ob.rotation_euler = (0.0, 0.0, 0.0)
    else:
        ob.rotation_euler = d_.to_track_quat("-Z", "Y").to_euler()
    return ob


def add_area(name, loc, target, size, power, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    G.COLL["ML02_Lights"].objects.link(ob)
    ob.location = loc
    d_ = Vector(target) - Vector(loc)
    ob.rotation_euler = d_.to_track_quat("-Z", "Y").to_euler()
    return ob


def build_studio():
    coll = G.collection("ML02_Studio")
    bm = bmesh.new()
    Rb = 260.0
    prof = [(-1000.0, 0.0)] + [(320.0 + Rb * math.sin(math.radians(90 * i / 24)),
                                Rb - Rb * math.cos(math.radians(90 * i / 24))) for i in range(25)]
    prof.append((320.0 + Rb, 1300.0))
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-1400.0, 1400.0)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    ob = G.obj_from_bm("ML02_Backdrop", bm, coll)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    m = bpy.data.materials.new("Backdrop")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(HEX["backdrop"])
    b.inputs["Roughness"].default_value = 0.75
    ob.data.materials.append(m)
    ob.location.z = -0.01
    return ob


def setup_render(scene, samples, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
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


# =====================================================================================
# Scene layout
# =====================================================================================

HERO_DEG = 38.0


def pose_set(parts, theta, coll, prefix, shuttle=False, offset=Matrix(), explode=None):
    """Instance every part at crank angle theta. explode: {key: Vector} offsets."""
    from .validate import PMirror, PShuttle
    p = PShuttle if shuttle else PMirror
    ex = explode or {}

    def o(k):
        return Matrix.Translation(ex.get(k, Vector()))

    C = PT.crank_matrix(theta)
    wheel = parts["wheel_shuttle"] if shuttle else parts["wheel_mirror"]
    SA, SB = PT.slider_matrix(theta, -1, p), PT.slider_matrix(theta, 1, p)
    obs = [
        (parts["frame"], "Frame", o("frame")),
        (wheel, "Wheel", o("wheel") @ C),
        (parts["cheek"], "Cheek_A", o("cheek_a") @ C),
        (parts["cheek"], "Cheek_B", o("cheek_b") @ C @ PT.cheek_b_basis(shuttle)),
        (parts["cap"], "Cap", o("cap") @ C),
        (parts["handle"], "Handle", o("handle") @ C),
        (parts["knob"], "Knob", o("knob") @ C),
        (parts["pin"], "Pin_Knob", o("knob_pin") @ C @ PT.knob_pin_basis()),
        (parts["rod"], "Rod_A", o("rod_a") @ PT.rod_matrix(theta, -1, p)),
        (parts["rod"], "Rod_B", o("rod_b") @ PT.rod_matrix(theta, 1, p)),
        (parts["slider"], "Slider_A", o("slider_a") @ SA),
        (parts["slider"], "Slider_B", o("slider_b") @ SB),
        (parts["pin"], "Pin_Wrist_A", o("pin_a") @ SA),
        (parts["pin"], "Pin_Wrist_B", o("pin_b") @ SB),
    ]
    return [inst(src, f"{prefix}_{nm}", coll, offset @ M) for src, nm, M in obs]


def organise(parts, plate, print_mats):
    G.collection("ML02_Cameras")
    G.collection("ML02_Lights")
    mats = {
        "graphite": make_material("ML_Graphite", HEX["graphite"], 0.55, "Z"),
        "orange": make_material("ML_Orange", HEX["orange"], 0.42, "Y"),
        "orange_z": make_material("ML_Orange_Z", HEX["orange"], 0.42, "Z"),
        "sand": make_material("ML_Sand", HEX["sand"], 0.48, "Y"),
        "graphite_y": make_material("ML_Graphite_Y", HEX["graphite"], 0.5, "Y"),
    }
    look = {"frame": "graphite", "wheel_mirror": "orange", "wheel_shuttle": "sand", "cheek": "sand",
            "rod": "sand", "slider": "orange", "pin": "sand", "cap": "graphite_y",
            "handle": "graphite_y", "knob": "orange"}
    src = G.collection("ML02_Parts")
    notes = {
        "frame": "plinth bottom on the bed",
        "wheel_mirror": "either face on the bed",
        "wheel_shuttle": "either face on the bed",
        "cheek": "outer (socket) face on the bed, crank pin up",
        "rod": "flat",
        "slider": "on its outer side face (wrist-pin bore vertical)",
        "pin": "head on the bed",
        "cap": "outer face on the bed",
        "handle": "outer face on the bed, shaft up",
        "knob": "inner end on the bed",
    }
    for k, ob in parts.items():
        set_material(ob, mats[look[k]])
        smooth_by_angle(ob)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        src.objects.link(ob)
        ob["odd_layer_part"] = ob.name
        ob["print_orientation"] = notes[k]
        ob["status"] = "CAD only - not yet printed"
    src.hide_render = True
    src.hide_viewport = True
    th = math.radians(HERO_DEG)
    asm = G.collection("ML02_Assembly")
    pose_set(parts, th, asm, "ASM")
    # exploded: along Y for the crank stack, X for sliders/rods, Z for pins
    y = Vector((0, 1, 0))
    up = Vector((0, 0, 30))
    ex = {"cheek_a": up + 18 * y, "cheek_b": up - 18 * y, "cap": up + 44 * y,
          "handle": up - 46 * y, "knob": up - 62 * y, "knob_pin": up - 78 * y,
          "rod_a": up + 8 * y + Vector((0, 0, 4)), "rod_b": up - 8 * y + Vector((0, 0, 4)),
          "slider_a": Vector((-22, 0, 9)), "slider_b": Vector((30, 0, 9)),
          "pin_a": Vector((-22, 26, 9)), "pin_b": Vector((30, -26, 9)), "wheel": up}
    exp = G.collection("ML02_Exploded")
    pose_set(parts, th, exp, "EXP", explode=ex)
    # motion study: one copy, re-posed for each frame of the motion strip
    mot = G.collection("ML02_Motion")
    pose_set(parts, 0.0, mot, "MOT")
    # shuttle configuration
    shu = G.collection("ML02_Shuttle")
    pose_set(parts, th, shu, "SHU", shuttle=True)
    # print plate
    pc = G.collection("ML02_PrintPlate")
    for name, key, (cx, cy) in plate:
        inst(parts[key], "PLATE_" + name, pc, Matrix.Translation((cx - 128, cy - 128, 0)) @ _centre(parts[key], print_mats[key]) @ print_mats[key])
    plate_mat = bpy.data.materials.new("Plate")
    plate_mat.use_nodes = True
    pb = plate_mat.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = hex_lin("55565A")
    pb.inputs["Roughness"].default_value = 0.8
    plate_ob = G.prism("PLATE_BuildPlate", G.rrect(-128, 128, -128, 128, 6), -1.2, -0.002, pc)
    plate_ob.data.materials.append(plate_mat)
    for c in (asm, exp, mot, shu, pc):
        c.hide_render = True
    return dict(asm=asm, exp=exp, mot=mot, shu=shu, plate=pc)


def _centre(ob, M):
    v, _ = G.world_tris(ob, M)
    lo = Vector((min(q.x for q in v), min(q.y for q in v), min(q.z for q in v)))
    hi = Vector((max(q.x for q in v), max(q.y for q in v), max(q.z for q in v)))
    return Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))


def repose(parts, coll, theta):
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob)
    pose_set(parts, theta, coll, "MOT")


def shots(scene, colls, parts):
    add_area("Key", (-180, -240, 260), (0, 0, 15), 240, 7.0e5, (1.0, 0.97, 0.93))
    add_area("Fill", (280, -80, 140), (0, 0, 15), 260, 1.8e5, (0.92, 0.95, 1.0))
    add_area("Rim", (60, 280, 200), (0, 0, 15), 170, 3.6e5)
    add_area("Top", (0, 0, 440), (0, 0, 0), 320, 2.2e5)
    cams = {}

    def cam(name, loc, tgt, lens=85, ortho=None):
        cams[name] = add_camera("CAM_" + name, loc, tgt, lens, ortho)

    cam("01_hero", (-150, -205, 140), (2, -4, 15), 82)
    cam("02_exploded", (-255, -165, 205), (2, -10, 24), 50)
    cam("03_side_mechanism", (0, 150, 21), (0, 0, 21), 85, ortho=132)
    cam("04_top", (0, -6, 420), (0, -6, 0), 85, ortho=128)
    cam("05_crank_detail", (-62, 118, 70), (0, 4, 22), 100)
    cam("06_shuttle", (150, -205, 140), (-2, -4, 15), 82)
    cam("07_print_plate", (0, -250, 340), (0, 6, 0), 50)
    cam("08_motion", (0, 150, 21), (0, 0, 21), 85, ortho=128)

    def show(on):
        for c in colls.values():
            c.hide_render = True
        for c in on:
            colls[c].hide_render = False

    def shot(name, on):
        def f():
            show(on)
            scene.camera = cams[name]
        return f

    lst = [("01_hero", shot("01_hero", ["asm"])),
           ("02_exploded", shot("02_exploded", ["exp"])),
           ("03_side_mechanism", shot("03_side_mechanism", ["asm"])),
           ("04_top", shot("04_top", ["asm"])),
           ("05_crank_detail", shot("05_crank_detail", ["asm"])),
           ("06_shuttle", shot("06_shuttle", ["shu"])),
           ("07_print_plate", shot("07_print_plate", ["plate"]))]
    for deg in (0, 90, 180, 270):
        def f(deg=deg):
            repose(parts, colls["mot"], math.radians(deg))
            show(["mot"])
            scene.camera = cams["08_motion"]
        lst.append((f"08_motion_{deg:03d}", f))
    lst[0][1]()
    return lst
