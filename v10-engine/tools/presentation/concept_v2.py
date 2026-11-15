"""Packaging renders for the current plan (D65-D67): engine on one solid walnut base with a
brass plate, and the wooden shipping crate with foam. Sizes match tools/presentation/cutfiles.py.

    python3.13 tools/presentation/concept_v2.py
-> renders/presentation/base_v2.png, crate_v2.png
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,F401

import skin_blender as SB  # noqa: E402
from skin import bpyutil as U, materials as M, studio as S  # noqa: E402
import cutfiles as CF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "renders", "presentation")

CX, CY = 9.0, 0.0            # engine footprint centre (stand plate x -141..159, y -120..120)
Z_TOP = -144.0               # underside of the engine stand = top of the base
ENG_TOP = 162.0
PLY = 18.0                   # crate plywood
FOAM = 50.0


def walnut():
    return M._principled("walnut", (0.16, 0.075, 0.035), roughness=0.38, coat=0.6)


def brass():
    return M._principled("brass", (0.78, 0.58, 0.25), metallic=1.0, roughness=0.25)


def plywood():
    return M._principled("plywood", (0.62, 0.46, 0.28), roughness=0.7)


def batten():
    return M._principled("batten", (0.50, 0.36, 0.20), roughness=0.75)


def foam():
    return M._principled("foam", (0.22, 0.22, 0.24), roughness=0.95)


def base():
    z0 = Z_TOP - CF.T_SLAB
    b = U.rrect_prism("base_slab", CX, CY, CF.B_W, CF.B_D, CF.R_CORNER, z0, Z_TOP)
    U.bevel_edges(b, 5.0, 4, lambda c, d: abs(c.z - Z_TOP) < 0.3 and abs(d.z) < 0.1)
    U.set_material(b, walnut())
    xf = CX + CF.B_W / 2
    zc = (z0 + Z_TOP) / 2
    p = U.box("name_plate", xf - 0.2, xf + CF.T_BRASS, -CF.PL_W / 2, CF.PL_W / 2, zc - CF.PL_H / 2, zc + CF.PL_H / 2)
    U.set_material(p, brass())
    return [b, p], (CX - CF.B_W / 2, CX + CF.B_W / 2, -CF.B_D / 2, CF.B_D / 2, z0, ENG_TOP)


def crate(bb):
    x0, x1, y0, y1, z0, z1 = bb
    ix0, ix1, iy0, iy1 = x0 - FOAM, x1 + FOAM, y0 - FOAM, y1 + FOAM
    iz0, iz1 = z0 - FOAM, z1 + FOAM
    ox0, ox1, oy0, oy1, oz0 = ix0 - PLY, ix1 + PLY, iy0 - PLY, iy1 + PLY, iz0 - PLY
    objs = []
    shell = U.box("crate", ox0, ox1, oy0, oy1, oz0, iz1)
    U.boolean(shell, U.box("crate_in", ix0, ix1, iy0, iy1, iz0, iz1 + 10))
    U.set_material(shell, plywood())
    objs.append(shell)
    # battens round the top and bottom edges of the four walls
    for zb in (oz0, iz1 - 60):
        for (a0, a1, b0, b1) in ((ox0 - 12, ox1 + 12, oy0 - 12, oy0), (ox0 - 12, ox1 + 12, oy1, oy1 + 12),
                                 (ox0 - 12, ox0, oy0, oy1), (ox1, ox1 + 12, oy0, oy1)):
            o = U.box("batten", a0, a1, b0, b1, zb, zb + 60)
            U.set_material(o, batten())
            objs.append(o)
    # foam: floor pad and four corner blocks
    pad = U.box("foam_pad", ix0, ix1, iy0, iy1, iz0, z0)
    U.set_material(pad, foam())
    objs.append(pad)
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        fx0 = ix0 if sx == 0 else x1 - 60
        fx1 = x0 + 60 if sx == 0 else ix1
        fy0 = iy0 if sy == 0 else y1 - 60
        fy1 = y0 + 60 if sy == 0 else iy1
        blk = U.box("foam_corner", fx0, fx1, fy0, fy1, z0, z0 + 260)
        U.boolean(blk, U.box("cut", x0, x1, y0, y1, z0 - 1, z0 + 300))
        U.set_material(blk, foam())
        objs.append(blk)
    # lid leaning open on the back edge
    lid = U.box("crate_lid", ox0, ox1, oy0, oy1, iz1, iz1 + PLY)
    U.set_material(lid, plywood())
    lb = [U.box("lid_batten", ox0 + 40, ox1 - 40, yy, yy + 60, iz1 + PLY, iz1 + PLY + 18) for yy in (oy0 + 30, oy1 - 90)]
    for o in lb:
        U.set_material(o, batten())
    for o in [lid] + lb:
        U.rot(o, 'Y', -70, pivot=(ox0, 0, iz1))
        objs.append(o)
    return objs, (ox1 - ox0, oy1 - oy0, iz1 + PLY - oz0)


def main():
    os.makedirs(OUT, exist_ok=True)
    U.reset_scene()
    SB.build_library()
    SB.place_all(0.0, with_core=True)
    _, bb = base()
    S.build(bb, bb[4])
    S.camera((1.0, 0.85, 0.45), bb, 1.0)
    S.render(os.path.join(OUT, "base_v2.png"), size=(1600, 1200), samples=64)
    _, dims = crate(bb)
    drop = CF.T_SLAB * 0 + FOAM + PLY                      # crate sits below the base: lower the floor
    U.move(bpy.data.objects["STUDIO_floor"], 0, 0, -drop)
    big = (bb[0] - 140, bb[1] + 140, bb[2] - 140, bb[3] + 140, bb[4] - 70, bb[5] + 200)
    S.camera((1.0, 0.7, 1.1), big, 0.95)
    S.render(os.path.join(OUT, "crate_v2.png"), size=(1600, 1200), samples=64)
    print("crate outside %.0f x %.0f x %.0f mm" % dims, flush=True)


if __name__ == "__main__":
    main()
