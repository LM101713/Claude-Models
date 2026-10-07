"""Photo-real product renders of the Blender skin (Liam, 2026-10-07: "make me renders real").

Same geometry as tools/skin_blender.py; only the look changes: per-part materials (sand-cast
aluminium with a cast grain, painted graphite block, black wrinkle valve covers, stainless headers
with a heat tint toward the ports, machined throttle body, black anodised front drive, powder-coated
stand), soft rounded edge highlights (Cycles bevel shader), a dark seamless studio with softboxes and
strip rims, and a short depth of field.

    python tools/skin_photo.py [--views ref3_front_right_34,ref2_rear_left_34] [--samples 192] [--size 1920x1440]

Renders go to renders/photo/. Colours are a render proposal only; the filament colours are still
Liam's sign-off.
"""
import argparse
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import skin_blender as SB  # noqa: E402
from skin import bpyutil as U  # noqa: E402
from skin import studio as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "photo")
_MATS = {}


def _mat(name, base, metallic, rough, grain=None, coat=0.0, aniso=0.0, bevel=0.35, tint=None):
    """Principled material with optional cast/wrinkle grain (noise bump), bevel-rounded edges and a
    heat tint ramp along world Z (headers)."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new("PHOTO_" + name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.2
    if aniso:
        b.inputs["Anisotropic"].default_value = aniso
    normal_src = None
    if bevel:
        bv = nt.nodes.new("ShaderNodeBevel")
        bv.inputs["Radius"].default_value = bevel
        bv.samples = 6
        normal_src = bv.outputs["Normal"]
    if grain:
        scale, strength, dist = grain
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = 8.0
        nz.inputs["Roughness"].default_value = 0.65
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = strength
        bp.inputs["Distance"].default_value = dist
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        if normal_src is not None:
            nt.links.new(normal_src, bp.inputs["Normal"])
        normal_src = bp.outputs["Normal"]
        # the grain also breaks up the roughness a little, like a real casting
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = rough - 0.06
        rr.inputs["To Max"].default_value = rough + 0.06
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
        nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    if normal_src is not None:
        nt.links.new(normal_src, b.inputs["Normal"])
    if tint:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = tint[0]
        mr.inputs["From Max"].default_value = tint[1]
        nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].position, cr.elements[0].color = 0.0, (*base, 1.0)            # far from the port: clean stainless
        cr.elements[1].position, cr.elements[1].color = 0.80, (0.46, 0.47, 0.60, 1)  # faint blue-violet band
        e = cr.elements.new(0.93)
        e.color = (0.66, 0.52, 0.34, 1)                                               # straw/gold at the port
        e2 = cr.elements.new(1.0)
        e2.color = (0.55, 0.42, 0.30, 1)
        nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    _MATS[name] = m
    return m


def cast_alu():
    return _mat("cast_alu", (0.60, 0.60, 0.61), 1.0, 0.40, grain=(1.6, 0.22, 0.25))


def machined_alu():
    return _mat("machined_alu", (0.80, 0.80, 0.82), 1.0, 0.18, aniso=0.5, bevel=0.25)


def graphite_paint():
    return _mat("graphite_paint", (0.075, 0.08, 0.088), 0.0, 0.42, grain=(1.2, 0.30, 0.3), coat=0.35)


def wrinkle_black():
    return _mat("wrinkle_black", (0.012, 0.012, 0.013), 0.0, 0.58, grain=(0.9, 0.7, 0.3), bevel=0.5)


def stainless_heat():
    return _mat("stainless_heat", (0.76, 0.76, 0.74), 1.0, 0.24, bevel=0.0, tint=(-40.0, 110.0))


def flange_steel():
    return _mat("flange_steel", (0.42, 0.42, 0.44), 1.0, 0.32)


def anodised_black():
    return _mat("anodised_black", (0.03, 0.03, 0.034), 1.0, 0.34)


def powder_black():
    return _mat("powder_black", (0.02, 0.02, 0.022), 0.0, 0.62, grain=(2.0, 0.15, 0.2))


def brushed():
    return _mat("brushed", (0.62, 0.62, 0.64), 1.0, 0.28, aniso=0.7)


def boot_glow():
    if "boot" in _MATS:
        return _MATS["boot"]
    m = _mat("boot", (0.85, 0.30, 0.08), 0.0, 0.35, bevel=0.3)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (1.0, 0.45, 0.12, 1.0)
    b.inputs["Emission Strength"].default_value = 0.8
    b.inputs["Subsurface Weight"].default_value = 0.4
    return m


def dark_steel():
    return _mat("dark_steel", (0.16, 0.16, 0.17), 1.0, 0.45, bevel=0.0)


# placed-name prefix -> material (first match wins; order matters for overlapping prefixes)
TABLE = [
    ("core_", dark_steel), ("crankcase", graphite_paint), ("bank", graphite_paint), ("head_", cast_alu),
    ("valve_cover", wrinkle_black), ("oil_cap", wrinkle_black), ("header_plate", flange_steel), ("boot", boot_glow),
    ("header_", stainless_heat), ("collector", stainless_heat), ("intake_lid", cast_alu), ("intake_base", cast_alu),
    ("throttle", machined_alu), ("pan_panel", powder_black), ("pan", machined_alu), ("bellhousing", cast_alu),
    ("front_cover", cast_alu), ("damper", anodised_black), ("accessory", anodised_black), ("alternator", anodised_black),
    ("stand_plate", powder_black), ("plinth", powder_black), ("edition", brushed),
]


def material_for(name):
    for pre, fn in TABLE:
        if name.startswith(pre):
            return fn()
    return cast_alu()


def studio(bb, floor_z):
    sc = bpy.context.scene
    x0, x1, y0, y1, z0, z1 = bb
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span = max(x1 - x0, y1 - y0, z1 - z0)
    # seamless sweep: floor + curved back so the horizon disappears
    size = span * 8
    floor = U.box("STUDIO_floor", cx - size, cx + size, cy - size, cy + size, floor_z - 2.0, floor_z, "COL_studio")
    fm = _mat("floor", (0.055, 0.058, 0.062), 0.0, 0.32, bevel=0.0)
    U.set_material(floor, fm)

    def area(name, loc, energy, size_, ratio=0.6, target=None):
        bpy.ops.object.light_add(type='AREA', location=loc)
        lt = bpy.context.object
        lt.name = name
        lt.data.energy = energy
        lt.data.shape = 'RECTANGLE'
        lt.data.size = size_
        lt.data.size_y = size_ * ratio
        d = Vector(target or (cx, cy, (z0 + z1) / 2)) - Vector(loc)
        lt.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        for c in lt.users_collection:
            c.objects.unlink(lt)
        U.collection("COL_studio").objects.link(lt)
        return lt
    zc = (z0 + z1) / 2
    area("PH_key", (cx + 1.0 * span, cy + 1.4 * span, z1 + 1.6 * span), 7.0e6, 1.6 * span)              # big overhead softbox, front right
    area("PH_fill", (cx - 1.6 * span, cy + 1.0 * span, zc + 0.4 * span), 1.4e6, 2.4 * span)             # broad, dim fill
    area("PH_rim_l", (cx - 1.4 * span, cy - 1.5 * span, z1 + 0.5 * span), 3.2e6, 1.8 * span, ratio=0.12)  # strip rims for edge lines
    area("PH_rim_r", (cx + 1.6 * span, cy - 1.2 * span, z1 + 0.3 * span), 2.6e6, 1.8 * span, ratio=0.12)
    area("PH_top", (cx, cy, z1 + 2.4 * span), 2.2e6, 2.0 * span)
    w = bpy.data.worlds.new("photo_world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.20, 0.21, 0.23, 1.0)
    bg.inputs["Strength"].default_value = 0.6
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 10
    sc.cycles.glossy_bounces = 6
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default="ref3_front_right_34,ref2_rear_left_34,ref1_closeup_34_above")
    ap.add_argument("--samples", type=int, default=192)
    ap.add_argument("--size", default="1920x1440")
    ap.add_argument("--exposure", type=float, default=0.0)
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    t = time.time()
    U.reset_scene()
    SB.build_library()
    placed = SB.place_all(0.0, with_core=True)
    for name, obj, _ in placed:
        U.set_material(obj, material_for(name))
    shown = {o.name for _, o, _ in placed}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in shown and not o.name.startswith("STUDIO"):
            o.hide_render = True
    bbs = [U.bbox(o) for n, o, _ in placed if not n.startswith(("stand", "plinth", "edition"))]
    bb = (min(b[0] for b in bbs), max(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs),
          min(b[4] for b in bbs), max(b[5] for b in bbs))
    floor_z = min(U.bbox(o)[4] for _, o, _ in placed)
    studio(bb, floor_z)
    bpy.context.scene.view_settings.exposure = a.exposure
    targets = SB._view_targets(placed)
    w, h = (int(v) for v in a.size.lower().split("x"))
    os.makedirs(OUT, exist_ok=True)
    for v in a.views.split(","):
        direction, zoom, _, tgt = S.VIEWS[v]
        cam = S.camera(direction, bb, zoom * 1.08, lens=70.0, target=targets.get(tgt))
        cam.data.dof.use_dof = True
        tgt_pt = Vector(targets.get(tgt) or ((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
        cam.data.dof.focus_distance = (cam.location - tgt_pt).length
        cam.data.dof.aperture_fstop = 5.6 if zoom < 1.3 else 4.0
        path = os.path.join(OUT, f"{v}{a.tag}.png")
        t0 = time.time()
        S.render(path, size=(w, h), samples=a.samples)
        print(f"  rendered {v} ({time.time()-t0:.0f}s)", flush=True)
    print(f"done in {time.time()-t:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
