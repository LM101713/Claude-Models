"""Premium presentation concept renders (look only - sizes are placeholders until the
real engine and the laser are known): walnut base, clear acrylic cover, engraved plate,
and the shipping box with foam.

    python tools/presentation/concept.py
-> renders/presentation/*.png
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bpy  # noqa: E402

import skin_blender as SB  # noqa: E402
from skin import bpyutil as U, materials as M, studio as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "renders", "presentation")

# concept sizes (mm), engine frame: the stand plate is x -141..159, y -120..120, top z -132
GAP = 18.0
ENG = dict(x0=-141.0, x1=159.0, y0=-120.0, y1=120.0, z_stand_bot=-144.0, z_top=162.0)


def walnut():
    return M._principled("walnut", (0.16, 0.075, 0.035), roughness=0.38, coat=0.6)


def acrylic():
    m = bpy.data.materials.new("MAT_acrylic")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1.0)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    return m


def brass():
    return M._principled("brass", (0.78, 0.58, 0.25), metallic=1.0, roughness=0.25)


def box_black():
    return M._principled("box_black", (0.02, 0.02, 0.022), roughness=0.55)


def foam():
    return M._principled("foam", (0.05, 0.05, 0.055), roughness=0.95)


def display_case():
    x0, x1 = ENG["x0"] - GAP, ENG["x1"] + GAP
    y0, y1 = ENG["y0"] - GAP, ENG["y1"] + GAP
    zb = ENG["z_stand_bot"]
    objs = []
    base = U.rrect_prism("case_base", (x0 + x1) / 2, 0, x1 - x0 + 30, y1 - y0 + 30, 10.0, zb - 32, zb)
    U.bevel_edges(base, 4.0, 4, lambda c, d: abs(c.z - zb) < 0.3 and abs(d.z) < 0.1)
    U.set_material(base, walnut())
    objs.append(base)
    t = 4.0
    cover = U.box("case_cover", x0, x1, y0, y1, zb, ENG["z_top"] + GAP)
    U.boolean(cover, U.box("cover_in", x0 + t, x1 - t, y0 + t, y1 - t, zb - 1, ENG["z_top"] + GAP - t))
    U.bevel_edges(cover, 1.5, 3, lambda c, d: True)
    U.set_material(cover, acrylic())
    objs.append(cover)
    plate = U.box("case_plate", x1 + 15 - 1.2, x1 + 15, -60, 60, zb - 24, zb - 8)
    U.set_material(plate, brass())
    objs.append(plate)
    return objs, (x0 - 15, x1 + 15, y0 - 15, y1 + 15, zb - 32, ENG["z_top"] + GAP)


def shipping_box(case_bb, offset_x):
    x0, x1, y0, y1, z0, z1 = case_bb
    f = 50.0                                      # foam all round
    W, D, H = x1 - x0 + 2 * f, y1 - y0 + 2 * f, z1 - z0 + 2 * f
    cx = (x0 + x1) / 2 + offset_x
    cy = (y0 + y1) / 2
    zb = z0 - f
    objs = []
    outer = U.box("ship_box", cx - W / 2, cx + W / 2, cy - D / 2, cy + D / 2, zb, zb + H * 0.62)
    U.boolean(outer, U.box("ship_in", cx - W / 2 + 6, cx + W / 2 - 6, cy - D / 2 + 6, cy + D / 2 - 6, zb + 6, zb + H))
    U.set_material(outer, box_black())
    objs.append(outer)
    insert = U.box("foam", cx - W / 2 + 6, cx + W / 2 - 6, cy - D / 2 + 6, cy + D / 2 - 6, zb + 6, zb + f + 60)
    U.boolean(insert, U.box("foam_pocket", cx - (x1 - x0) / 2, cx + (x1 - x0) / 2, cy - (y1 - y0) / 2, cy + (y1 - y0) / 2, zb + f, zb + f + 100))
    U.set_material(insert, foam())
    objs.append(insert)
    lid = U.box("ship_lid", cx - W / 2 - 3, cx + W / 2 + 3, cy - D / 2 - 3, cy + D / 2 + 3, zb + H * 0.62 + 140, zb + H * 0.62 + 140 + 0.38 * H)
    U.boolean(lid, U.box("lid_in", cx - W / 2 + 3, cx + W / 2 - 3, cy - D / 2 + 3, cy + D / 2 - 3, zb + H * 0.62 + 134, zb + H * 0.62 + 134 + 0.38 * H - 6))
    U.set_material(lid, box_black())
    U.rot(lid, 'Y', -12, pivot=(cx + W / 2, cy, zb + H * 0.62 + 140))
    objs.append(lid)
    logo = U.box("lid_plate", cx - 70, cx + 70, cy - 20, cy + 20, 0, 1.0)
    U.set_material(logo, brass())
    U.move(logo, 0, 0, zb + H * 0.62 + 140 + 0.38 * H)
    U.rot(logo, 'Y', -12, pivot=(cx + W / 2, cy, zb + H * 0.62 + 140))
    objs.append(logo)
    return objs, (W, D, H)


def main():
    os.makedirs(OUT, exist_ok=True)
    U.reset_scene()
    SB.build_library()
    placed = SB.place_all(0.0, with_core=True)
    case_objs, case_bb = display_case()
    bb = case_bb
    S.build(bb, bb[4])
    S.camera((1.0, 0.85, 0.5), bb, 1.0)
    S.render(os.path.join(OUT, "display_case.png"), size=(1600, 1200), samples=64)
    # packaging: the cased engine moved aside, box beside it
    box_objs, dims = shipping_box(case_bb, offset_x=0.0)
    for o in [o for _, o, _ in placed] + case_objs:
        U.move(o, 0, 0, 0)
    allbb = (bb[0] - 80, bb[1] + 80, bb[2] - 80, bb[3] + 80, bb[4] - 60, bb[5] + 300)
    S.camera((0.9, 1.0, 0.8), allbb, 0.95)
    S.render(os.path.join(OUT, "shipping_box.png"), size=(1600, 1200), samples=64)
    print(f"case footprint {case_bb[1]-case_bb[0]:.0f} x {case_bb[3]-case_bb[2]:.0f} x {case_bb[5]-case_bb[4]:.0f} mm; "
          f"shipping box {dims[0]:.0f} x {dims[1]:.0f} x {dims[2]:.0f} mm", flush=True)


if __name__ == "__main__":
    main()
