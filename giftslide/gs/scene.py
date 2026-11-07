"""
GS-05 GIFT SLIDE: the Blender project and the product renders (bpy).

Builds an organised .blend (closed, mid-slide and open states, exploded view, cutaways,
print plate, colourways, the underside) with the generator scripts embedded as text blocks,
then renders the product images with Cycles.
"""

import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import geom as G
from .params import COLOURS, P

COLL = {}
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CX = P.L / 2   # everything is shown centred on the box


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


def mesh_object(name, m, coll, mat=None, smooth_deg=25, centre=True):
    if centre:
        m = m.translate((-CX, 0, 0))
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


def material(name, hexcol, rough=0.5, layer_axis="Z", layer_bump=0.08, bed_axis="Z", spec=0.4, sheen=0.0):
    """Matte PLA with 0.2 mm layer lines (object Z) and a textured-PEI finish on faces that
    were on the bed (normal along -Z)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if sheen:
        bsdf.inputs["Sheen Weight"].default_value = sheen
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
        noise.inputs["Scale"].default_value = 2.6
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


def image_material(name, path, rough=0.35, edge_hex="1C2A3A"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Coat Weight"].default_value = 0.6
    tc = nodes.new("ShaderNodeTexCoord")
    img = nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(path)
    img.image.pack()
    img.extension = "CLIP"
    links.new(tc.outputs["Generated"], img.inputs["Vector"])
    # faces not facing up get the plain edge colour
    geo = nodes.new("ShaderNodeNewGeometry")
    sepn = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Normal"], sepn.inputs[0])
    gt = nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.9
    links.new(sepn.outputs["Z"], gt.inputs[0])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = hex_lin(edge_hex)
    links.new(gt.outputs[0], mix.inputs["Factor"])
    links.new(img.outputs["Color"], mix.inputs["B"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def card_texture(path):
    """A generic gift card face (no brand): night-blue gradient, a gold band, plain lettering."""
    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1712, 1080
    y, x = np.mgrid[0:H, 0:W]
    t = (x / W * 0.65 + y / H * 0.35)
    c0, c1 = np.array([24, 52, 78]), np.array([12, 24, 40])
    arr = (c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    dr = ImageDraw.Draw(im)
    gold = (226, 189, 112)
    dr.rectangle([0, int(H * 0.62), W, int(H * 0.66)], fill=gold)
    bold = ImageFont.truetype(font_manager.findfont("DejaVu Sans:bold"), 120)
    reg = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 64)
    dr.text((110, 150), "GIFT CARD", fill=(246, 241, 230), font=bold)
    dr.text((110, 310), "for something you love", fill=(170, 186, 204), font=reg)
    dr.text((W - 420, H - 250), "$ 50", fill=gold, font=bold)
    im.save(path)
    return path


def look_at(ob, target, up="Y"):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", up).to_euler()


def camera(name, loc, target, lens=70, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 8000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["GS05_Cameras"].objects.link(ob)
    ob.location = loc
    look_at(ob, target, "Y")
    return ob


def area_light(name, loc, target, size, power, coll, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    COLL[coll].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def plane(name, size, loc, mat, coll):
    me = bpy.data.meshes.new(name)
    h = size / 2
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = loc
    me.materials.append(mat)
    return ob


def arrow(name, pts, coll, mat, r=0.5, head=2.2):
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
    a, b = Vector(pts[-2]), Vector(pts[-1])
    d = (b - a).normalized()
    bpy.ops.mesh.primitive_cone_add(radius1=head, depth=head * 2.4, location=b + d * head * 1.2)
    cone = bpy.context.active_object
    cone.name = name + "_tip"
    cone.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    for c in cone.users_collection:
        c.objects.unlink(cone)
    coll.objects.link(cone)
    cone.data.materials.append(mat)
    return ob


def assign_cut_faces(ob, normal, offset, mat_cut):
    ob.data.materials.append(mat_cut)
    n = Vector(normal).normalized()
    for poly in ob.data.polygons:
        if poly.normal.dot(n) > 0.999 and abs(n.dot(poly.center) - offset) < 0.05:
            poly.material_index = len(ob.data.materials) - 1
            poly.use_smooth = False


# =====================================================================================
# scene
# =====================================================================================


def build(C, blend=True, render=False, samples=160):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    for name in ("GS05_Closed", "GS05_Mid", "GS05_Open", "GS05_Message", "GS05_Exploded", "GS05_Section",
                 "GS05_Detent", "GS05_Print_Plate", "GS05_Colourways", "GS05_Underside", "GS05_Studio",
                 "GS05_Table", "GS05_Cameras"):
        collection(name)

    parts = C.data["parts"]
    tray, lid, lid_star, inlay = parts["tray"], parts["lid"], parts["lid_star"], parts["star_inlay"]
    card = G.card(P)
    tex = card_texture(os.path.join(HERE, "renders", "_card_texture.png"))
    mats = dict(
        tray=material("GS_Tray_PLA", COLOURS["tray"][2], 0.62),
        lid=material("GS_Lid_PLA", COLOURS["lid"][2], 0.55),
        green=material("GS_Pine_PLA", "1F4D3A", 0.58),
        graphite=material("GS_Graphite_PLA", "2B2D31", 0.6),
        sand=material("GS_Sand_PLA", "D8C7A6", 0.62),
        gold=material("GS_Gold_PLA", COLOURS["inlay"][2], 0.32, spec=0.7),
        card=image_material("GS_Card", tex),
        surface=material("GS_Table_Linen", "E9E4DA", 0.9, None),
        pei=material("GS_PEI", "1D1D20", 0.6, None),
        guide=material("GS_Guide", "8A8D93", 0.5, None),
        cut_t=material("GS_Section_Tray", "8F8778", 0.7, None),
        cut_l=material("GS_Section_Lid", "F0A0A0", 0.7, None),
        note=material("GS_Banknote", "9DB59A", 0.8, None),
    )

    def lid_at(s, m=None, mat=None, coll=None, name="Lid"):
        return mesh_object(name, G.lid_placed(P, s, lid_m=m or lid), coll, mat or mats["lid"])

    # ---- states ------------------------------------------------------------------------
    for coll, s, with_card in (("GS05_Closed", 0.0, True), ("GS05_Mid", P.travel * 0.45, True),
                               ("GS05_Open", P.travel, True), ("GS05_Message", P.travel, False)):
        K = COLL[coll]
        tag = coll.split("_")[1]
        mesh_object(f"{tag}_Tray", tray, K, mats["tray"])
        lid_at(s, coll=K, name=f"{tag}_Lid")
        if with_card:
            mesh_object(f"{tag}_Card", card, K, mats["card"])
    # a folded note under the card in the open view (cash option)
    note = G.prism_z(G.rrect(P.end_wall + 6, P.end_wall + 6 + 78, -16.5, 16.5, 0.5), P.floor_t + P.card_t,
                     P.floor_t + P.card_t + 0.45).translate((0, 0, -P.card_t))
    # (notes go under the card: lift the card in this state)
    for ob in COLL["GS05_Open"].objects:
        if ob.name.endswith("_Card"):
            ob.location.z += 0.45
    mesh_object("Open_Folded_Note", note, COLL["GS05_Open"], mats["note"])

    # ---- exploded: lid lifted and pulled back, path into the open end --------------------
    E = COLL["GS05_Exploded"]
    mesh_object("Exploded_Tray", tray, E, mats["tray"])
    mesh_object("Exploded_Card", card, E, mats["card"])
    lift = 14.0
    s_out = P.lid_l + 14.0
    mesh_object("Exploded_Lid", G.lid_placed(P, s_out, lid_m=lid).translate((0, 0, lift)), E, mats["lid"])
    x_end = P.L - CX
    # the lid's rear end goes into the open end first, then slides home
    arrow("Path_Lid_In", [(x_end + 12, 0, P.H + lift - 2), (x_end + 12, 0, P.H + 4), (x_end - 28, 0, P.H + 4)],
          E, mats["guide"], r=0.55, head=2.2)

    # ---- section across the lid at the parked bump --------------------------------------
    X = COLL["GS05_Section"]
    xc = P.bump_closed_x
    nrm = (-1.0, 0.0, 0.0)
    tcut = tray.trim_by_plane([1, 0, 0], xc)
    lcut = G.lid_placed(P, 0.0, lid_m=lid).trim_by_plane([1, 0, 0], xc)
    ccut = card.trim_by_plane([1, 0, 0], xc)
    ob = mesh_object("Section_Tray", tcut, X, mats["tray"])
    assign_cut_faces(ob, nrm, -(xc - CX), mats["cut_t"])
    ob = mesh_object("Section_Lid", lcut, X, mats["lid"])
    assign_cut_faces(ob, nrm, -(xc - CX), mats["cut_l"])
    mesh_object("Section_Card", ccut, X, mats["card"])

    # ---- detent: horizontal cut through the bump band, from above -----------------------
    Dd = COLL["GS05_Detent"]
    zc = P.z_ledge + 0.7
    tcut = tray.trim_by_plane([0, 0, -1], -zc)
    lcut = G.lid_placed(P, 0.0, lid_m=lid).trim_by_plane([0, 0, -1], -zc)
    ob = mesh_object("Detent_Tray", tcut, Dd, mats["tray"])
    assign_cut_faces(ob, (0, 0, 1), zc, mats["cut_t"])
    ob = mesh_object("Detent_Lid", lcut, Dd, mats["lid"])
    assign_cut_faces(ob, (0, 0, 1), zc, mats["cut_l"])

    # ---- print plate ---------------------------------------------------------------------
    PP = COLL["GS05_Print_Plate"]

    def onplate(m, cx, cy):
        bb = m.bounding_box()
        return m.translate((cx - (bb[0] + bb[3]) / 2, cy - (bb[1] + bb[4]) / 2, -bb[2]))

    mesh_object("Plate_Tray", onplate(tray, 0, 35.5), PP, mats["tray"], centre=False)
    mesh_object("Plate_Lid", onplate(lid, 0, -33.5), PP, mats["lid"], centre=False)
    plane("Plate_PEI", 184, (0, 0, -0.01), mats["pei"], PP)

    # ---- colourways ----------------------------------------------------------------------
    CW = COLL["GS05_Colourways"]
    ways = [(-80, "tray", "lid", False), (0, "sand", "green", True), (80, "graphite", "graphite", True)]
    for i, (dy, tm, lm, star) in enumerate(ways):
        rot = Matrix.Rotation(math.radians(-8 + 8 * i), 4, "Z")
        objs = [mesh_object(f"CW{i}_Tray", tray, CW, mats[tm])]
        objs.append(mesh_object(f"CW{i}_Lid", G.lid_placed(P, 0.0, lid_m=lid_star if star else lid), CW, mats[lm]))
        if star:
            objs.append(mesh_object(f"CW{i}_Inlay", G.lid_placed(P, 0.0, lid_m=inlay), CW, mats["gold"]))
        for ob in objs:
            ob.matrix_world = Matrix.Translation((0, dy, 0)) @ rot @ ob.matrix_world

    # ---- underside -----------------------------------------------------------------------
    U = COLL["GS05_Underside"]
    flip = Matrix.Rotation(math.radians(180), 4, "X")
    for nm, m, mt in (("Under_Tray", tray, mats["tray"]), ("Under_Lid", G.lid_placed(P, 0.0, lid_m=lid), mats["lid"])):
        ob = mesh_object(nm, m, U, mt)
        ob.matrix_world = Matrix.Translation((0, 0, P.H)) @ flip

    # ---- studio --------------------------------------------------------------------------
    ST = COLL["GS05_Studio"]
    plane("Surface", 3000, (0, 0, -0.02), mats["surface"], ST)
    world = bpy.data.worlds.new("GS_World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_lin("E7E2D9")
    bg.inputs["Strength"].default_value = 0.45
    area_light("Key", (-170, -150, 260), (0, 0, 0), 240, 5.0e5, "GS05_Studio", (1.0, 0.97, 0.92))
    area_light("Fill", (230, -60, 120), (0, 0, 0), 280, 1.6e5, "GS05_Studio", (0.92, 0.96, 1.0))
    area_light("Rim", (40, 260, 160), (0, 0, 0), 220, 2.4e5, "GS05_Studio")
    area_light("Table_Key", (-140, -160, 300), (0, 0, 0), 300, 7.0e5, "GS05_Table")
    area_light("Table_Fill", (200, 80, 200), (0, 0, 0), 300, 2.5e5, "GS05_Table")
    plane("Table_Back", 3000, (0, 0, -0.5), mats["surface"], COLL["GS05_Table"])

    # ---- embedded sources ----------------------------------------------------------------
    for rel in ("giftslide.py", "gs/params.py", "gs/geom.py", "gs/detent.py", "gs/validate.py", "gs/estimate.py",
                "gs/export.py", "gs/report.py", "gs/scene.py"):
        txt = bpy.data.texts.new(rel)
        with open(os.path.join(HERE, rel)) as fh:
            txt.write(fh.read())
    readme = bpy.data.texts.new("README_GS05")
    readme.write(
        "ODD LAYER GS-05 GIFT SLIDE\n\nCollections:\n"
        "  GS05_Closed / _Mid / _Open   the three states with a card (Open also holds a folded note)\n"
        "  GS05_Message                 open, card removed: the message in the pocket floor\n"
        "  GS05_Exploded                lid lifted out of the open end, with its path back in\n"
        "  GS05_Section                 cut across the box at the parked detent bump\n"
        "  GS05_Detent                  cut through the bump band, seen from above\n"
        "  GS05_Print_Plate             tray + lid on a 180 mm A1 mini plate\n"
        "  GS05_Colourways              Ivory/Scarlet, Sand/Pine + gold star, Graphite + gold star\n"
        "  GS05_Underside               push hole and logo\n\n"
        "Geometry comes from giftslide.py (embedded here as text blocks; it needs manifold3d,\n"
        "shapely, numpy and matplotlib: run `python giftslide.py --blend` outside Blender).\n"
        "Units: millimetres (scene unit scale 0.001). X: slide direction, the lid opens toward +X.\n"
        "CAD-validated only: nothing has been printed or physically tested.\n"
    )

    cams = make_cameras()
    setup_render(sc, samples)
    path = os.path.join(HERE, "models", "GS05_GiftSlide.blend")
    set_visible(["GS05_Closed", "GS05_Studio"])
    sc.camera = cams["hero"]
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
        print("saved", path)
    if render:
        render_all(sc, cams)
        if blend:
            set_visible(["GS05_Closed", "GS05_Studio"])
            sc.camera = cams["hero"]
            bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    tmp = os.path.join(HERE, "renders", "_card_texture.png")
    if os.path.exists(tmp):
        os.remove(tmp)


def make_cameras():
    zc = P.z_ledge + 0.9
    xs = P.bump_closed_x - CX
    return dict(
        hero=camera("CAM_Hero", (-150, -165, 120), (4, 0, 0), 72),
        open=camera("CAM_Open", (-165, -150, 150), (8, 0, 0), 66),
        mid=camera("CAM_Mid", (-160, -150, 140), (10, 0, 0), 66),
        top=camera("CAM_Top", (31, 0, 400), (31, 0, 0), ortho=164),
        exploded=camera("CAM_Exploded", (-120, -230, 150), (40, 0, 4), 58),
        section=camera("CAM_Section", (xs - 120, 52, 30), (xs, 27.5, P.z_ledge + 1.2), 110),
        detent=camera("CAM_Detent", (xs + 2.5, 29.4, 250), (xs + 2.5, 29.4, 0), ortho=15),
        plate=camera("CAM_Print_Plate", (0, -200, 230), (0, -4, 0), 62),
        colourways=camera("CAM_Colourways", (-235, -150, 260), (0, 0, 0), 55),
        underside=camera("CAM_Underside", (-150, -160, 140), (0, 0, 2), 70),
        message=camera("CAM_Message", (-120, -40, 180), (-15, 0, 0), 70),
    )


def set_visible(names):
    for name, c in COLL.items():
        if name == "GS05_Cameras":
            continue
        c.hide_render = name not in names
        c.hide_viewport = name not in names


def setup_render(sc, samples, res=(1600, 1200)):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"


def shot(sc, cam, name, colls, res=(1600, 1200)):
    only = os.environ.get("GS_SHOTS")   # e.g. GS_SHOTS=01,05 renders only those (drafting)
    if only and not any(name.startswith(k) for k in only.split(",")):
        return None
    path = os.path.join(HERE, "renders", name)
    set_visible(colls)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)
    return path


def render_all(sc, cams):
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    shot(sc, cams["hero"], "01_hero.png", ["GS05_Closed", "GS05_Studio"])
    shot(sc, cams["open"], "02_reveal.png", ["GS05_Open", "GS05_Studio"])
    seq = []
    for key, coll in (("closed", "GS05_Closed"), ("mid", "GS05_Mid"), ("open", "GS05_Open")):
        seq.append(shot(sc, cams["top"], f"_seq_{key}.png", [coll, "GS05_Studio"], res=(900, 760)))
    if all(seq):
        composite(seq, ["CLOSED", "SLIDE", "OPEN"],
                  ["held by the detent", f"{P.travel:.0f} mm of glide", "firm stop, card 72 % uncovered"],
                  os.path.join(HERE, "renders", "03_sequence.png"))
        for p_ in seq:
            os.remove(p_)
    shot(sc, cams["exploded"], "04_exploded.png", ["GS05_Exploded", "GS05_Studio"])
    shot(sc, cams["section"], "05_section.png", ["GS05_Section", "GS05_Studio"])
    shot(sc, cams["detent"], "06_detent_cutaway.png", ["GS05_Detent", "GS05_Table"], res=(1600, 1000))
    shot(sc, cams["message"], "07_message.png", ["GS05_Message", "GS05_Studio"])
    shot(sc, cams["plate"], "08_print_plate.png", ["GS05_Print_Plate", "GS05_Table"])
    shot(sc, cams["colourways"], "09_colourways.png", ["GS05_Colourways", "GS05_Studio"])
    shot(sc, cams["underside"], "10_underside.png", ["GS05_Underside", "GS05_Studio"])


def composite(paths, titles, subs, out):
    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    pad = 90
    img = Image.new("RGB", (w * len(ims), h + pad), (236, 233, 227))
    font = ImageFont.truetype(font_manager.findfont("DejaVu Sans:bold"), 36)
    small = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), 26)
    dr = ImageDraw.Draw(img)
    for i, (im, t, s) in enumerate(zip(ims, titles, subs)):
        img.paste(im, (i * w, 0))
        tw = dr.textlength(t, font=font)
        dr.text((i * w + (w - tw) / 2, h + 8), t, fill=(43, 45, 49), font=font)
        sw = dr.textlength(s, font=small)
        dr.text((i * w + (w - sw) / 2, h + 52), s, fill=(110, 112, 118), font=small)
    img.save(out)
