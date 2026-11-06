"""
HF-04 HOLDFAST: the Blender project and the renders (bpy).

Builds an organised .blend (assembly, exploded view, print plate, variants, handles, studio,
cameras, and the generator scripts embedded as text blocks), then renders the product images.
"""

import math
import os

import bpy
import numpy as np
from mathutils import Vector

from . import geom as G
from . import validate as V
from .params import D, P, centre, s_of_diameter

COLORS = {"graphite": "2B2D31", "orange": "FF6A13", "wall": "E4E1DB", "wood": "C99A68", "pei": "1D1D20"}
COLL = {}


# =====================================================================================
# helpers
# =====================================================================================


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


def mesh_object(name, m, coll, mat=None, smooth_deg=30):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts).astype(int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], t.tolist())
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


def material(name, hexcol, rough=0.5, layer_axis="Z", layer_bump=0.10, bed_axis=None, spec=0.45):
    """PLA-like material with 0.2 mm layer lines along layer_axis (object space) and a
    textured-PEI finish on faces whose normal is along bed_axis."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if layer_axis is None:
        return m
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
    height = sin.outputs[0]
    if bed_axis:
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.2
        noise.inputs["Detail"].default_value = 6.0
        links.new(tc.outputs["Object"], noise.inputs["Vector"])
        geo = nodes.new("ShaderNodeNewGeometry")
        sepn = nodes.new("ShaderNodeSeparateXYZ")
        links.new(geo.outputs["Normal"], sepn.inputs[0])
        absn = nodes.new("ShaderNodeMath")
        absn.operation = "ABSOLUTE"
        links.new(sepn.outputs[bed_axis], absn.inputs[0])
        gt = nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.98
        links.new(absn.outputs[0], gt.inputs[0])
        mixh = nodes.new("ShaderNodeMix")
        mixh.data_type = "FLOAT"
        links.new(gt.outputs[0], mixh.inputs["Factor"])
        links.new(sin.outputs[0], mixh.inputs["A"])
        links.new(noise.outputs["Fac"], mixh.inputs["B"])
        height = mixh.outputs["Result"]
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = layer_bump
    bump.inputs["Distance"].default_value = 0.03
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def wood_material():
    m = bpy.data.materials.new("HF_Wood_Handle")
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.42
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (6.0, 6.0, 0.25)  # grain stretched along the handle (Z)
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Distortion"].default_value = 0.6
    links.new(mp.outputs[0], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_lin("B4834F")
    ramp.color_ramp.elements[1].color = hex_lin("D8AF7E")
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def look_at(ob, target, up="Y"):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", up).to_euler()


def camera(name, loc, target, lens=70, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 6000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["HF04_Cameras"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def area_light(name, loc, target, size, power, color=(1, 1, 1), coll="HF04_Studio"):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    COLL[coll].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def plane(name, size, loc, rot, mat, coll):
    me = bpy.data.meshes.new(name)
    h = size / 2
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    me.materials.append(mat)
    return ob


def guide(name, pts, coll, mat, r=0.35, arrow=True):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p_, q in zip(sp.points, pts):
        p_.co = (q[0], q[1], q[2], 1.0)
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    cu.materials.append(mat)
    if arrow:
        a, b = Vector(pts[-2]), Vector(pts[-1])
        d = (b - a).normalized()
        bpy.ops.mesh.primitive_cone_add(radius1=1.6, depth=4.0, location=b - d * 2.0)
        cone = bpy.context.active_object
        cone.name = name + "_tip"
        cone.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        for c in cone.users_collection:
            c.objects.unlink(cone)
        coll.objects.link(cone)
        cone.data.materials.append(mat)
    return ob


def assign_cut_faces(ob, normal, offset, mat_cut):
    """Give faces lying in a section plane a second material."""
    ob.data.materials.append(mat_cut)
    n = Vector(normal).normalized()
    for poly in ob.data.polygons:
        if poly.normal.dot(n) > 0.999 and abs(n.dot(poly.center) - offset) < 0.05:
            poly.material_index = 1
            poly.use_smooth = False


# =====================================================================================
# scene
# =====================================================================================


def build(parts, pf, out, render=False, samples=128):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"

    for name in ("HF04_Assembly", "HF04_Exploded", "HF04_Print_Plate", "HF04_Variants", "HF04_States",
                 "HF04_Section", "HF04_Row", "HF04_Studio", "HF04_Table", "HF04_Cameras"):
        collection(name)

    mats = dict(
        g=material("HF_Graphite_PLA", COLORS["graphite"], 0.55, "Y", 0.10, bed_axis="Y"),
        o=material("HF_Orange_PLA", COLORS["orange"], 0.42, "Y", 0.10, bed_axis="Y"),
        g_p=material("HF_Graphite_PLA_printframe", COLORS["graphite"], 0.55, "Z", 0.10, bed_axis="Z"),
        o_p=material("HF_Orange_PLA_printframe", COLORS["orange"], 0.42, "Z", 0.10, bed_axis="Z"),
        wood=wood_material(),
        wall=material("HF_Wall", COLORS["wall"], 0.85, None),
        pei=material("HF_PEI", COLORS["pei"], 0.6, None),
        guide=material("HF_Guide", "8A8D93", 0.5, None),
        cut_g=material("HF_Section_Graphite", "6E7179", 0.7, None),
        cut_o=material("HF_Section_Orange", "FFB27F", 0.7, None),
        steel=material("HF_Steel_Handle", "3E5C6E", 0.35, None, spec=0.6),
    )

    base, roller = parts["base"], parts["roller"]
    # ---- assembly: 25 mm wooden broom handle ------------------------------------------
    A = COLL["HF04_Assembly"]
    mesh_object("Base", base, A, mats["g"])
    s25 = s_of_diameter(25.0)
    mesh_object("Roller_L", V.place(roller, s25, -1, dn=0.0), A, mats["o"])
    mesh_object("Roller_R", V.place(roller, s25, +1, dn=0.0), A, mats["o"])
    mesh_object("Handle_25mm", G.handle(25.0, -330, 420), A, mats["wood"], 20)

    # ---- states (front view panel) -------------------------------------------------------
    S = COLL["HF04_States"]
    states = {}
    for d in (None, 19.0, 25.0, 32.0):
        key = "empty" if d is None else f"{d:.0f}"
        sub = collection(f"HF04_State_{key}", S)
        s = 0.0 if d is None else s_of_diameter(d)
        mesh_object(f"State_{key}_Base", base, sub, mats["g"])
        mesh_object(f"State_{key}_Roller_L", V.place(roller, s, -1, dn=0.0), sub, mats["o"])
        mesh_object(f"State_{key}_Roller_R", V.place(roller, s, +1, dn=0.0), sub, mats["o"])
        if d is not None:
            mesh_object(f"State_{key}_Handle", G.handle(d, -330, 420), sub, mats["wood"], 20)
        states[key] = sub

    # ---- exploded --------------------------------------------------------------------------
    E = COLL["HF04_Exploded"]
    mesh_object("Exploded_Base", base, E, mats["g"])
    lift = 48.0
    for side, nm in ((-1, "L"), (+1, "R")):
        mesh_object(f"Exploded_Roller_{nm}", V.place(roller, D.s_key, side, dn=0.0, dy=lift), E, mats["o"])
        k = centre(D.s_key)
        b0 = centre(0.0)
        x = k[0] if side < 0 else -k[0]
        x0 = b0[0] if side < 0 else -b0[0]
        guide(f"Path_in_{nm}", [(x, P.Y_HEAD_END + lift - 6, k[1]), (x, P.BACK_T + 1.5, k[1])], E, mats["guide"])
        guide(f"Path_down_{nm}", [(x, P.BACK_T + 1.5, k[1]), (x0, P.BACK_T + 1.5, b0[1])], E, mats["guide"], 0.3)

    # ---- section through the left roller axis, along its slot ----------------------------
    X = COLL["HF04_Section"]
    nrm = (D.u[0], 0.0, D.u[1])  # cut across the slot, through the roller axis
    s_cut = 14.0
    c = centre(s_cut)
    off = nrm[0] * c[0] + nrm[2] * c[1]
    bcut = base.trim_by_plane([-nrm[0], 0, -nrm[2]], -off)
    rcut = V.place(roller, s_cut, -1, dn=0.0).trim_by_plane([-nrm[0], 0, -nrm[2]], -off)
    ob = mesh_object("Section_Base", bcut, X, mats["g"])
    assign_cut_faces(ob, nrm, off, mats["cut_g"])
    ob = mesh_object("Section_Roller", rcut, X, mats["o"])
    assign_cut_faces(ob, nrm, off, mats["cut_o"])

    # ---- print plate (print orientation) -------------------------------------------------
    PP = COLL["HF04_Print_Plate"]
    plate_off = Vector((0, 0, 0))
    mesh_object("Plate_Base", pf["base"].translate([0, 22, 0]), PP, mats["g_p"])
    mesh_object("Plate_Roller_1", pf["roller"].translate([-22, -42, 0]), PP, mats["o_p"])
    mesh_object("Plate_Roller_2", pf["roller"].translate([22, -42, 0]), PP, mats["o_p"])
    mesh_object("Plate_Fit_Coupon", pf["coupon"].translate([66, -40, 0]), PP, mats["g_p"])
    plane("Plate_PEI", 230, (0, -5, -0.01), (0, 0, 0), mats["pei"], PP)
    for ob in PP.objects:
        ob.location += plate_off

    # ---- variants -------------------------------------------------------------------------
    VA = COLL["HF04_Variants"]
    mesh_object("Variant_Roller_Standard", pf["roller"].translate([-45, 0, 0]), VA, mats["o_p"])
    mesh_object("Variant_Roller_Grip", pf["grip"].translate([-15, 0, 0]), VA, mats["o_p"])
    mesh_object("Variant_Roller_Loose", pf["loose"].translate([15, 0, 0]), VA, mats["o_p"])
    mesh_object("Variant_Fit_Coupon", pf["coupon"].translate([50, 0, 0]), VA, mats["g_p"])
    plane("Variant_Surface", 600, (0, 0, -0.01), (0, 0, 0), mats["wall"], VA)

    # ---- a row of three on the wall (broom, mop, rake) -------------------------------------
    RW = COLL["HF04_Row"]
    for i, (d, mat) in enumerate(((22.0, mats["steel"]), (25.0, mats["wood"]), (30.0, mats["wood"]))):
        dx = (i - 1) * 140.0
        s = s_of_diameter(d)
        mesh_object(f"Row{i}_Base", base.translate([dx, 0, 0]), RW, mats["g"])
        mesh_object(f"Row{i}_Roller_L", V.place(roller, s, -1, dn=0.0).translate([dx, 0, 0]), RW, mats["o"])
        mesh_object(f"Row{i}_Roller_R", V.place(roller, s, +1, dn=0.0).translate([dx, 0, 0]), RW, mats["o"])
        mesh_object(f"Row{i}_Handle_{d:.0f}mm", G.handle(d, -600, 500 - 40 * i).translate([dx, 0, 0]), RW, mat, 20)

    # ---- studio ---------------------------------------------------------------------------
    ST = COLL["HF04_Studio"]
    plane("Wall", 2400, (0, -0.05, 0), (math.radians(90), 0, 0), mats["wall"], ST)
    world = bpy.data.worlds.new("HF_World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_lin("D9D6D0")
    bg.inputs["Strength"].default_value = 0.35
    area_light("Key", (-260, 330, 260), (0, 0, 0), 260, 9.0e5)
    area_light("Fill", (320, 260, -60), (0, 0, 0), 300, 3.2e5)
    area_light("Top", (40, 120, 420), (0, 10, 0), 200, 2.5e5)
    area_light("Table_Key", (-180, -200, 320), (0, 0, 0), 300, 1.1e6, coll="HF04_Table")
    area_light("Table_Fill", (240, -60, 200), (0, 0, 0), 300, 4.0e5, coll="HF04_Table")
    area_light("Table_Back", (0, 260, 220), (0, 0, 0), 250, 3.0e5, coll="HF04_Table")

    # ---- generator scripts embedded --------------------------------------------------------
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("holdfast.py", "hf/params.py", "hf/geom.py", "hf/validate.py", "hf/export.py", "hf/report.py", "hf/scene.py"):
        txt = bpy.data.texts.new(rel)
        with open(os.path.join(here, rel)) as fh:
            txt.write(fh.read())
    readme = bpy.data.texts.new("README_HF04")
    readme.write(
        "ODD LAYER HF-04 HOLDFAST\n\nCollections:\n"
        "  HF04_Assembly     on the wall, 25 mm handle, use frame (X along wall, Y out of wall, Z up)\n"
        "  HF04_States       empty / 19 / 25 / 32 mm handles (front-view panel)\n"
        "  HF04_Exploded     rollers lifted out at the keyhole with the assembly path\n"
        "  HF04_Section      cut along the left slot through the roller axis\n"
        "  HF04_Print_Plate  parts in print orientation\n"
        "  HF04_Variants     Standard / Grip / Loose rollers and the fit coupon\n\n"
        "Geometry is generated by holdfast.py (embedded here as text blocks; it needs manifold3d,\n"
        "shapely and numpy: run it with `python holdfast.py --blend` outside Blender).\n"
        "Units: millimetres (scene unit scale 0.001).\n"
        "CAD-validated only: nothing has been printed or physically tested.\n"
    )

    cams = make_cameras()
    blend = os.path.join(out, "models", "HF04_Holdfast.blend")
    set_visible(["HF04_Assembly", "HF04_Studio"])
    sc.camera = cams["hero"]
    setup_render(sc, samples)
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("saved", blend)
    if render:
        render_all(sc, cams, out, states)
        set_visible(["HF04_Assembly", "HF04_Studio"])
        sc.camera = cams["hero"]
        bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)


def make_cameras():
    return dict(
        hero=camera("CAM_Hero", (150, 215, 70), (-3, 12, -4), 70),
        row=camera("CAM_Row", (110, 640, 120), (0, 10, -40), 55),
        empty=camera("CAM_Empty", (-150, 250, 120), (0, 10, -2), 70),
        front=camera("CAM_Front_Ortho", (0, 600, 0), (0, 0, 0), ortho=150),
        exploded=camera("CAM_Exploded", (-215, 255, 150), (0, 26, 2), 60),
        section=camera("CAM_Section", tuple(np.array([0, 0, 0]) + 0), (0, 0, 0), 80),
        plate=camera("CAM_Print_Plate", (0, -250, 270), (0, -8, 6), 62),
        variants=camera("CAM_Variants", (0, -170, 160), (2, 0, 8), 62),
    )


def set_visible(names):
    for name, c in COLL.items():
        if name == "HF04_Cameras":
            continue
        c.hide_render = not (name in names)
        c.hide_viewport = not (name in names)
    # child collections follow their parent unless named explicitly
    for name, c in COLL.items():
        if name.startswith("HF04_State_") and "HF04_States" in names and name not in names:
            c.hide_render = True
            c.hide_viewport = True


def setup_render(sc, samples, res=(1600, 1200)):
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


def shot(sc, cam, path, colls, res=(1600, 1200)):
    only = os.environ.get("HF_SHOTS")  # e.g. HF_SHOTS=01,05 renders only those (drafting)
    if only and not any(os.path.basename(path).startswith(k) or k in path for k in only.split(",")):
        return
    set_visible(colls)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def render_all(sc, cams, out, states):
    R = os.path.join(out, "renders")
    os.makedirs(R, exist_ok=True)
    shot(sc, cams["hero"], os.path.join(R, "01_hero.png"), ["HF04_Assembly", "HF04_Studio"])
    shot(sc, cams["exploded"], os.path.join(R, "02_exploded.png"), ["HF04_Exploded", "HF04_Studio"])
    # front panel: four states, composited
    panels = []
    for key in ("empty", "19", "25", "32"):
        p = os.path.join(R, f"_front_{key}.png")
        shot(sc, cams["front"], p, ["HF04_States", f"HF04_State_{key}", "HF04_Studio"], res=(800, 900))
        panels.append((key, p))
    if all(os.path.exists(p) for _, p in panels):
        composite_states(panels, os.path.join(R, "03_range.png"))
        for _, p in panels:
            os.remove(p)
    shot(sc, cams["empty"], os.path.join(R, "04_empty.png"), ["HF04_States", "HF04_State_empty", "HF04_Studio"])
    # section camera: look down the ramp at the cut face (normal +u), wall at the bottom of the frame
    u3 = Vector((D.u[0], 0.0, D.u[1]))
    c = centre(14.0)
    tgt = Vector((c[0] + 1.5, 13.5, c[1]))
    cam = cams["section"]
    cam.location = tgt + u3 * 150 + Vector((0, 18, 0)) + Vector((D.n[0], 0, D.n[1])) * 12
    f = (tgt - cam.location).normalized()
    right = f.cross(Vector((0, 1, 0))).normalized()
    up = right.cross(f).normalized()
    from mathutils import Matrix

    cam.matrix_world = Matrix((
        (right.x, up.x, -f.x, cam.location.x),
        (right.y, up.y, -f.y, cam.location.y),
        (right.z, up.z, -f.z, cam.location.z),
        (0, 0, 0, 1),
    ))
    cam.data.lens = 70
    sec_light = COLL["HF04_Section"].objects.get("Section_Light")
    if sec_light is None:
        sec_light = area_light("Section_Light", tuple(cam.location + Vector((0, 40, 0)) + right * 40), tuple(tgt), 150,
                               2.2e5, coll="HF04_Section")
    shot(sc, cam, os.path.join(R, "05_section.png"), ["HF04_Section", "HF04_Studio"])
    shot(sc, cams["plate"], os.path.join(R, "06_print_plate.png"), ["HF04_Print_Plate", "HF04_Table"])
    shot(sc, cams["variants"], os.path.join(R, "07_variants.png"), ["HF04_Variants", "HF04_Table"])
    shot(sc, cams["row"], os.path.join(R, "08_row_of_three.png"), ["HF04_Row", "HF04_Studio"])


def composite_states(panels, path):
    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    ims = [Image.open(p).convert("RGB") for _, p in panels]
    w, h = ims[0].size
    pad = 70
    out = Image.new("RGB", (w * len(ims), h + pad), (236, 234, 230))
    font = ImageFont.truetype(font_manager.findfont("DejaVu Sans:bold"), 34)
    small = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 24)
    labels = {"empty": ("EMPTY", "rollers on their stops"), "19": ("Ø19 mm", "rollers low"),
              "25": ("Ø25 mm", "mid travel"), "32": ("Ø32 mm", "rollers high")}
    dr = ImageDraw.Draw(out)
    for i, ((key, _), im) in enumerate(zip(panels, ims)):
        out.paste(im, (i * w, 0))
        t, sub = labels[key]
        tw = dr.textlength(t, font=font)
        dr.text((i * w + (w - tw) / 2, h + 6), t, fill=(43, 45, 49), font=font)
        sw = dr.textlength(sub, font=small)
        dr.text((i * w + (w - sw) / 2, h + 42), sub, fill=(110, 112, 118), font=small)
    out.save(path)
