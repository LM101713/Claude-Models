"""
SD-01 SINKDOCK: the Blender project and product renders (bpy, Cycles CPU).

The sponges and brush are generic stand-ins built to the researched dimensions (no logos,
faces or trade dress). The dock is the exact exported geometry.
"""

import math
import os

import bpy
import numpy as np
from mathutils import Vector

from . import geom as G
from .params import BAYS, P, W, cup_y

COL = {
    "dock": "ECE7DD",      # warm white PETG
    "dock_alt": "8FA89A",  # sage
    "graphite": "2B2D31",
    "orange": "FF6A13",
    "counter": "D9D4CB",
    "tile": "F2F0EB",
    "steel": "B9BDC2",
    "yellow": "F5C518",
    "pink": "EE7FA0",
    "teal": "2BB3B1",
    "green": "2E8B57",
    "sponge_y": "F2D24B",
    "handle": "F4F4F2",
    "bristle": "E9E6DF",
}
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


def mesh_object(name, m, coll, mat=None, smooth_deg=35):
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


def principled(name, hexcol, rough=0.5, spec=0.5, coat=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
        b.inputs["IOR"].default_value = ior
    return m, b


def printed(name, hexcol, rough=0.42):
    """PETG-like with 0.2 mm layer lines (object-space z)."""
    m, bsdf = principled(name, hexcol, rough=rough, spec=0.5)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / 0.2
    nt.links.new(sep.outputs["Z"], mul.inputs[0])
    sin = nt.nodes.new("ShaderNodeMath")
    sin.operation = "SINE"
    nt.links.new(mul.outputs[0], sin.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(sin.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def foam(name, hexcol, scale=1.4, strength=0.6, rough=0.9):
    m, bsdf = principled(name, hexcol, rough=rough, spec=0.2)
    nt = m.node_tree
    n = nt.nodes.new("ShaderNodeTexVoronoi")
    n.inputs["Scale"].default_value = scale
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.4
    nt.links.new(n.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.4)
    return m


def brushed(name, hexcol):
    m, bsdf = principled(name, hexcol, rough=0.32, spec=0.6)
    bsdf.inputs["Metallic"].default_value = 1.0
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.02, 3.0, 0.02)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 40.0
    nt.links.new(mp.outputs[0], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def stone(name, hexcol):
    m, bsdf = principled(name, hexcol, rough=0.35, spec=0.5)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.08
    n.inputs["Detail"].default_value = 12
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = hex_lin("CFC9BF")
    ramp.color_ramp.elements[1].color = hex_lin("E6E2DA")
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def bevel(ob, w, seg=4):
    mod = ob.modifiers.new("bevel", "BEVEL")
    mod.width = w
    mod.segments = seg
    mod.limit_method = "ANGLE"
    return mod


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(name, loc, target, lens=60, ortho=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 8000.0
    cam.dof.use_dof = False
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    COLL["SD01_Cameras"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def area_light(name, loc, target, size, power, color=(1, 1, 1)):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    COLL["SD01_Studio"].objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def box_obj(name, x0, y0, z0, x1, y1, z1, mat, coll):
    from manifold3d import Manifold
    m = Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
    return mesh_object(name, m, coll, mat, smooth_deg=10)


# -------------------------------------------------------------------------------------
def build_items(coll, mats):
    """Generic stand-ins at their computed rest positions."""
    from manifold3d import Manifold
    obs = []
    for b in BAYS:
        if b["kind"] == "disc":
            d, t = 104.0, 39.0
            x, y, z = G.rest_disc(b, d, t)
            if b["name"] == "Scrub Daddy":
                ob = mesh_object("Item_round_sponge_A", G.disc_sponge(d, t, 128), coll, mats["yellow"], 50)
                bevel(ob, 4.0, 6)
                ob.location = (x, y, z)
                obs.append(ob)
            else:
                # two-layer round sponge: a scrub layer and a foam layer
                a = G.disc_sponge(d, t * 0.5, 128).translate([-t * 0.25, 0, 0])
                c = G.disc_sponge(d, t * 0.5, 128).translate([t * 0.25, 0, 0])
                for nm, mm, mt in (("Item_round_sponge_B_scrub", a, mats["teal"]), ("Item_round_sponge_B_foam", c, mats["pink"])):
                    ob = mesh_object(nm, mm, coll, mt, 50)
                    bevel(ob, 3.0, 5)
                    ob.location = (x, y, z)
                    obs.append(ob)
        elif b["kind"] == "rect":
            L, T, H = 66.0, 17.0, 111.0
            x, y, z = G.rest_rect(b, L, T, H)
            body = Manifold.cube([T * 0.68, L, H]).translate([-T / 2, 0, 0])
            pad = Manifold.cube([T * 0.32, L, H]).translate([-T / 2 + T * 0.68, 0, 0])
            for nm, mm, mt in (("Item_flat_sponge", body, mats["sponge_y"]), ("Item_flat_sponge_pad", pad, mats["green"])):
                mm = mm.rotate([P.slope_y, 0, 0])
                ob = mesh_object(nm, mm, coll, mt, 50)
                bevel(ob, 1.5, 3)
                ob.location = (x, y + 0.2, z + 0.2)
                obs.append(ob)
        else:
            y0, y1 = cup_y()
            yc = (y0 + y1) / 2
            obs += build_brush(coll, mats, b["xc"], yc - 2.5, P.z0 + yc * P.tan_y + 1.2, lean_deg=5.0)
    return obs


def build_brush(coll, mats, x, y, z, lean_deg=5.0):
    """A generic dish brush, handle down: oval handle, round head, bristle tuft."""
    from manifold3d import CrossSection, JoinType, Manifold
    hcs = CrossSection.square([22.0, 16.0], center=True).offset(4.0, JoinType.Round).offset(-1.0, JoinType.Round)
    handle = Manifold.extrude(hcs, 190.0, n_divisions=8, scale_top=[1.25, 1.1])
    neck = Manifold.cylinder(18.0, 14.0, 18.0, 64).translate([0, 0, 188.0])
    head = Manifold.cylinder(12.0, 27.0, 29.0, 96).translate([0, 0, 204.0])
    tuft = Manifold.cylinder(24.0, 24.0, 26.0, 128).translate([0, 0, 215.0])
    out = []
    for nm, mm, mt in (("Item_brush_handle", handle + neck, mats["graphite"]), ("Item_brush_head", head, mats["orange"]),
                       ("Item_brush_bristles", tuft, mats["bristle"])):
        ob = mesh_object(nm, mm, coll, mt, 40)
        if nm.endswith("handle"):
            bevel(ob, 1.0, 3)
        ob.location = (x, y, z)
        ob.rotation_euler = (math.radians(-lean_deg), 0, 0)
        out.append(ob)
    return out


def build_kitchen(coll, mats):
    """Countertop with an undermount sink in front of the dock (y < -4) and a tiled wall behind."""
    from manifold3d import Manifold
    edge = -4.0
    top = Manifold.cube([900, 600, 30]).translate([-370, edge, -30])
    lip = Manifold.cube([900, 30, 30]).translate([-370, edge - 30, -30])  # nothing: the sink cut-out is in front
    ob = mesh_object("Counter", top, coll, mats["counter"], 10)
    bevel(ob, 3.0, 4)
    # sink: a brushed-steel basin below the counter edge
    basin = Manifold.cube([900, 420, 220]).translate([-370, edge - 420 - 6, -250])
    inner = Manifold.cube([880, 400, 220]).translate([-360, edge - 410 - 6, -232])
    sk = mesh_object("Sink", basin - inner, coll, mats["steel"], 10)
    bevel(sk, 6.0, 6)
    wall = Manifold.cube([900, 20, 600]).translate([-370, P.D + 22, -30])
    mesh_object("Backsplash", wall, coll, mats["tile"], 10)
    del lip
    return ob


def setup_world(strength=0.9):
    w = bpy.data.worlds.new("SD01_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
    bg.inputs["Strength"].default_value = strength


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
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = 0.6
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def hide(obs, state):
    for ob in obs:
        ob.hide_render = state
        ob.hide_viewport = state


def render_all(m, outdir, blend_path):
    os.makedirs(outdir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for n in ("SD01_Dock", "SD01_Items", "SD01_Kitchen", "SD01_Plate", "SD01_Studio", "SD01_Cameras"):
        collection(n)
    mats = dict(
        dock=printed("SD01_PETG_WarmWhite", COL["dock"]),
        dock_alt=printed("SD01_PETG_Sage", COL["dock_alt"]),
        yellow=foam("Sponge_Yellow", COL["yellow"], 1.6, 0.7),
        pink=foam("Sponge_Pink", COL["pink"], 1.6, 0.7),
        teal=foam("Scrub_Teal", COL["teal"], 3.0, 0.9),
        sponge_y=foam("Sponge_FlatYellow", COL["sponge_y"], 2.0, 0.6),
        green=foam("Scour_Green", COL["green"], 6.0, 1.0),
        handle=principled("Brush_Handle", COL["handle"], 0.35)[0],
        graphite=principled("Brush_Handle_Graphite", COL["graphite"], 0.45)[0],
        orange=principled("Brush_Collar_Orange", COL["orange"], 0.4)[0],
        bristle=foam("Brush_Bristle", COL["bristle"], 18.0, 1.2, 0.7),
        counter=stone("Counter_Stone", COL["counter"]),
        steel=brushed("Sink_Steel", COL["steel"]),
        tile=principled("Wall_Tile", COL["tile"], 0.25)[0],
        pei=principled("Plate_PEI", "1D1D20", 0.6)[0],
        cut=principled("SD01_Section_Orange", COL["orange"], 0.5)[0],
        water=principled("Water", "FFFFFF", 0.02, 0.5, trans=1.0, ior=1.33)[0],
    )
    dock = mesh_object("SD01_SinkDock", m, COLL["SD01_Dock"], mats["dock"], 35)
    items = build_items(COLL["SD01_Items"], mats)
    kitchen = list(COLL["SD01_Kitchen"].objects)
    build_kitchen(COLL["SD01_Kitchen"], mats)
    kitchen = list(COLL["SD01_Kitchen"].objects)
    # water: a drop hanging from the Scrub Daddy spout tip
    from manifold3d import Manifold
    b = BAYS[1]
    drop = Manifold.sphere(2.2, 48).scale([1, 1, 1.35]).translate([b["xc"], -P.lip + 1.8, -2.6])
    wob = mesh_object("Water_drop", drop, COLL["SD01_Items"], mats["water"], 80)
    items.append(wob)
    # print plate (hidden except for the plate render)
    plate = box_obj("A1mini_plate_180", W / 2 - 90, (P.D - P.lip) / 2 - 90, -1.0, W / 2 + 90, (P.D - P.lip) / 2 + 90, 0.0,
                    mats["pei"], COLL["SD01_Plate"])
    setup_world()
    cx, cy = W / 2, (P.D - P.lip) / 2
    key = area_light("Key", (cx - 300, cy - 480, 520), (cx, cy, 40), 320, 620000)
    fill = area_light("Fill", (cx + 480, cy - 200, 260), (cx, cy, 40), 380, 210000, (0.95, 0.97, 1.0))
    rim = area_light("Rim", (cx + 150, cy - 40, 520), (cx, cy, 40), 260, 160000, (1.0, 0.97, 0.92))
    del key, fill, rim

    cams = dict(
        hero=camera("CAM_01_hero", (cx - 290, cy - 560, 300), (cx + 6, cy + 10, 92), 50),
        empty=camera("CAM_02_empty", (cx + 170, cy - 300, 210), (cx - 2, cy + 3, 8), 50),
        section=camera("CAM_03_section", (BAYS[1]["xc"] + 4, -300, 21), (BAYS[1]["xc"] + 4, 35, 21), ortho=96),
        drip=camera("CAM_04_spout", (b["xc"] - 95, -175, 80), (b["xc"] + 6, 2, 6), 70),
        plate=camera("CAM_05_plate", (cx + 210, cy - 250, 300), (cx, cy, 10), 45),
        sage=camera("CAM_06_sage", (cx + 380, cy - 600, 320), (cx - 8, cy + 10, 112), 50),
    )

    only = os.environ.get("SD_ONLY", "01,02,03,04,05,06").split(",")
    hide([plate], True)
    if "01" in only:
        render(os.path.join(outdir, "01_hero.png"), cams["hero"])
    hide(items, True)
    if "02" in only:
        render(os.path.join(outdir, "02_empty.png"), cams["empty"])
    hide(items, False)
    if "03" in only:
        # cutaway: everything in front of y = 35 removed, showing sponges riding on the V gutters
        from manifold3d import Manifold as Mf
        keep = Mf.cube([600, 400, 600]).translate([-200, 35.0, -100])
        cut_objs = []
        hide(items + [dock], True)
        cut_objs.append(mesh_object("CUT_dock", m ^ keep, COLL["SD01_Dock"], mats["cut"], 35))
        for b_ in BAYS:
            if b_["kind"] == "disc":
                x, y, z = G.rest_disc(b_, 104.0, 39.0)
                mt = mats["yellow"] if b_["name"] == "Scrub Daddy" else mats["pink"]
                cut_objs.append(mesh_object("CUT_" + b_["name"], G.disc_sponge(104.0, 39.0, 128).translate([x, y, z]) ^ keep,
                                            COLL["SD01_Items"], mt, 50))
            elif b_["kind"] == "rect":
                x, y, z = G.rest_rect(b_, 66.0, 17.0, 111.0)
                cut_objs.append(mesh_object("CUT_flat", G.rect_sponge(66.0, 17.0, 111.0).translate([x, y + 0.2, z + 0.2]) ^ keep,
                                            COLL["SD01_Items"], mats["sponge_y"], 50))
        render(os.path.join(outdir, "03_section.png"), cams["section"], res=(1800, 1000))
        for ob in cut_objs:
            bpy.data.objects.remove(ob)
        hide(items + [dock], False)
        wob.hide_render = False
    if "04" in only:
        render(os.path.join(outdir, "04_spout_drip.png"), cams["drip"], res=(1600, 1100))
    hide(items + kitchen, True)
    hide([plate], False)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.86, 0.87, 0.89, 1)
    if "05" in only:
        render(os.path.join(outdir, "05_print_plate.png"), cams["plate"], res=(1600, 1100))
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
    hide([plate], True)
    hide(items + kitchen, False)
    dock.data.materials[0] = mats["dock_alt"]
    if "06" in only:
        render(os.path.join(outdir, "06_sage.png"), cams["sage"])
    dock.data.materials[0] = mats["dock"]
    # embed the generator so the .blend documents itself
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in ("params.py", "geom.py", "validate.py", "scene.py"):
        t = bpy.data.texts.new("sd_" + fn)
        with open(os.path.join(here, fn)) as f:
            t.write(f.read())
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
