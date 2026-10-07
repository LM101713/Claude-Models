"""01 crankcase and 03 cylinder bank - functional geometry ported from
cad/block.py (bores, rail pockets, slots, inserts, locators, windows) plus the
cast look: skirt ribs, chamfered window frames, deck and pan-rail lips."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P, bank_angle

S45 = math.sqrt(0.5)


def _to_bank(obj, bank):
    return U.to_bank(obj, bank, P.bank_angle_A, P.bank_angle_B)


def _teardrop(name, r, x0, x1):
    t = r * S45
    cyl = U.cylinder(name, r, x0, x1, 0, 0, "X")
    tri = U.prism(name + "_roof", [(-t, t), (0.0, r / S45), (t, t)], x0, x1)
    return U.boolean(cyl, tri, "UNION")


def _bank_face_features_case(bank):
    """Cutters on one bank's mounting face of the crankcase (bank-local), then to the engine frame."""
    h = P.CASE_HALF_LEN
    cut = U.box("case_slot", -h - 1, h + 1, -P.CASE_SLOT_HALF, P.CASE_SLOT_HALF, 0.0, P.FACE_DIST + 1)
    for x in P.block_end_screws_x:
        U.boolean(cut, U.cylinder("case_ins", P.insert_hole / 2, P.FACE_DIST - P.INSERT_DEPTH, P.FACE_DIST + 1, x, P.BLOCK_SCREW_END_Y), "UNION")
    return _to_bank(cut, bank)


def crankcase():
    h = P.CASE_HALF_LEN
    prof = [tuple(p) for p in P.crankcase_outer_profile_yz]
    case = U.prism("01_crankcase", prof, -h, h)
    # cast look before the cuts: chamfered bottom edge, vertical skirt ribs with draft on both side walls
    cy = max(abs(p[0]) for p in prof)
    z_floor, z_top = P.CASE_FLOOR_Z, max(p[1] for p in prof if abs(p[0]) > 1)
    U.bevel_edges(case, 2.5, 3, lambda c, d: abs(d.x) > 0.9 and abs(c.z - z_floor) < 0.5 and abs(abs(c.y) - cy) < 0.5)
    rib_x = list(P.bank_between_x) + [P.BANK_A_CYL_X[0] + 22.0, P.BANK_A_CYL_X[-1] - 22.0]
    for sgn in (-1, 1):
        for x in rib_x:
            yw = sgn * cy
            rib = U.loft("skirt_rib", [
                [(x - 3.0, yw - sgn * 0.3, z_floor + 6.0), (x + 3.0, yw - sgn * 0.3, z_floor + 6.0), (x + 3.0, yw + sgn * 2.2, z_floor + 6.0), (x - 3.0, yw + sgn * 2.2, z_floor + 6.0)],
                [(x - 2.2, yw - sgn * 0.3, z_top - 3.0), (x + 2.2, yw - sgn * 0.3, z_top - 3.0), (x + 2.2, yw + sgn * 1.4, z_top - 3.0), (x - 2.2, yw + sgn * 1.4, z_top - 3.0)]])
            U.boolean(case, rib, "UNION")
        # pan-rail lip along the bottom of each side wall
        lip = U.box("rail_lip", -h + 6, h - 6, min(yw - sgn * 0.3, yw + sgn * 2.0), max(yw - sgn * 0.3, yw + sgn * 2.0), z_floor, z_floor + 5.0)
        U.bevel_edges(lip, 1.5, 2, lambda c, d: abs(d.x) > 0.9 and abs(c.z - (z_floor + 5.0)) < 0.3)
        U.boolean(case, lip, "UNION")
        # round-1 critique: pan-rail bolt heads between the skirt ribs (side walls are vertical in the print)
        for x in P.BANK_A_CYL_X:
            lo, hi = sorted((yw - sgn * 0.3, yw + sgn * 3.0))
            U.boolean(case, U.cylinder("rail_bolt", 2.2, lo, hi, x, z_floor + 9.0, "Y", segs=6), "UNION")
    # functional cuts, as the CAD
    U.boolean(case, _teardrop("cavity", P.CASE_INTERIOR_R, -h - 1, h + 1))
    U.boolean(case, U.prism("beam_space", [tuple(p) for p in P.beam_profile_yz], -h - 1, h + 1))
    for bank in ("A", "B"):
        U.boolean(case, _bank_face_features_case(bank))
    for sx in (-1, 1):
        for y, z in P.case_end_screws:
            x0 = sx * h
            lo, hi = sorted((x0 - sx * P.INSERT_DEPTH, x0 + sx * 1))
            U.boolean(case, U.cylinder("end_ins", P.insert_hole / 2, lo, hi, y, z, "X"))
    for x, y in P.base_inserts:
        U.boolean(case, U.cylinder("pan_ins", P.insert_hole / 2, P.CASE_FLOOR_Z - 1, P.CASE_FLOOR_Z + P.INSERT_DEPTH, x, y))
    hp, hx = P.HALL_POCKET, P.HALL_X
    U.boolean(case, U.box("hall", hx - 2.2, hx - 2.2 + hp["l"], -hp["w"] / 2, hp["w"] / 2, P.CASE_FLOOR_Z - 1, P.CASE_FLOOR_Z + hp["d"]))
    U.shade(case)         # no remove_doubles: it opened a 4-edge hole; finalize() does the merge
    return case


def _window(name, x):
    hw, yo = P.WINDOW_HALF_W, P.BLOCK_Y_OUT - 1
    zb, zt = P.WINDOW_BOTTOM, P.WINDOW_TOP
    pts = [(x - hw, zt), (x - hw, zb + hw), (x, zb), (x + hw, zb + hw), (x + hw, zt)]
    w = U.prism_z(name, [(0, 0)] * 0 or [(px, 0.0) for px, pz in pts], 0, 1) if False else None
    # polygon in the XZ plane extruded along +Y (through the outboard wall into the bore)
    import bmesh
    bm = bmesh.new()
    vs = [bm.verts.new((px, yo, pz)) for px, pz in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    verts = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, -yo, 0), verts=verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return U.from_bmesh(name, bm)


def _window_frame(name, x, cham=1.5):
    """Shallow flared copy of the window: chamfers its edges on the outboard face without beveling cut edges."""
    hw, yo = P.WINDOW_HALF_W + cham, P.BLOCK_Y_OUT - 1
    zb, zt = P.WINDOW_BOTTOM - cham * 1.4142, P.WINDOW_TOP + cham
    import bmesh
    bm = bmesh.new()
    outer = [(x - hw, zt), (x - hw, zb + hw), (x, zb), (x + hw, zb + hw), (x + hw, zt)]
    hw0 = P.WINDOW_HALF_W
    inner = [(x - hw0, zt - cham), (x - hw0, P.WINDOW_BOTTOM + hw0), (x, P.WINDOW_BOTTOM), (x + hw0, P.WINDOW_BOTTOM + hw0), (x + hw0, zt - cham)]
    vo = [bm.verts.new((px, yo, pz)) for px, pz in outer]
    vi = [bm.verts.new((px, P.BLOCK_Y_OUT + cham, pz)) for px, pz in inner]
    n = len(outer)
    bm.faces.new(vo)
    bm.faces.new(list(reversed(vi)))
    for i in range(n - 1):
        bm.faces.new((vo[i], vi[i], vi[i + 1], vo[i + 1]))
    bm.faces.new((vo[n - 1], vi[n - 1], vi[0], vo[0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return U.from_bmesh(name, bm)


def cylinder_bank():
    """Bank-local frame (as the CAD): x along the crank, y' to the valley, z' along the bore."""
    z0, z1 = P.FACE_DIST, P.DECK_DIST
    X0, X1, YO, YV = P.BLOCK_X_MIN, P.BLOCK_X_MAX, P.BLOCK_Y_OUT, P.BLOCK_Y_VALLEY
    blk = U.box("03_cylinder_bank", X0, X1, YO, YV, z0, z1)
    U.bevel_edges(blk, 3.0, 4, lambda c, d: abs(d.z) > 0.9)                  # cast corners
    # cast look on the outboard wall: vertical ribs between the windows, deck lip and skirt lip
    for x in P.bank_between_x:
        rib = U.loft("bank_rib", [
            [(x - 3.2, YO + 0.3, z0 + 4.0), (x + 3.2, YO + 0.3, z0 + 4.0), (x + 3.2, YO - 1.8, z0 + 4.0), (x - 3.2, YO - 1.8, z0 + 4.0)],
            [(x - 2.4, YO + 0.3, z1 - 4.0), (x + 2.4, YO + 0.3, z1 - 4.0), (x + 2.4, YO - 1.2, z1 - 4.0), (x - 2.4, YO - 1.2, z1 - 4.0)]])
        U.boolean(blk, rib, "UNION")
    lip = U.box("deck_lip", X0 + 6, X1 - 6, YO - 1.5, YO + 0.3, z1 - 4.0, z1 - 0.05)
    U.bevel_edges(lip, 1.0, 2, lambda c, d: abs(d.x) > 0.9 and abs(c.z - (z1 - 4.0)) < 0.3)
    U.boolean(blk, lip, "UNION")
    # round-1 critique: the outboard wall between the windows was a blank slab. Two bolt rows like the
    # references' head-to-block and block-to-crankcase joints: hex heads on the ribs under the deck lip
    # and above the skirt foot (the wall is vertical in the deck-down print, so raised heads are fine).
    for x in list(P.bank_between_x) + [X0 + 9.0, X1 - 9.0]:
        for z in (z1 - 7.5, z0 + 6.5):
            U.boolean(blk, U.cylinder("wall_bolt", 2.2, YO - 3.2, YO + 0.3, x, z, "Y", segs=6), "UNION")
    pocket_r = P.LUG_OD / 2 + P.LUG_POCKET_CLEAR
    for x in P.BANK_A_CYL_X:
        U.boolean(blk, U.cylinder("bore", P.BORE_DIA / 2, z0 - 1, z1 + 1, x, 0))
        pocket = U.cylinder("lug_pocket", pocket_r, z0 - 1, z1 + 1, x, P.RAIL_OFFSET)
        U.boolean(pocket, U.box("lug_slot", x - pocket_r, x + pocket_r, 0, P.RAIL_OFFSET, z0 - 1, z1 + 1), "UNION")
        U.boolean(blk, pocket)
        U.boolean(blk, U.cylinder("bore_lead", P.BORE_DIA / 2 + 1.5, z0 - 0.001, z0 + 1.5, x, 0, r2=P.BORE_DIA / 2))
        U.boolean(blk, U.cylinder("lug_lead", pocket_r + 1.0, z0 - 0.001, z0 + 1.0, x, P.RAIL_OFFSET, r2=pocket_r))
        if P.WINDOWS:
            U.boolean(blk, _window("window", x))
            U.boolean(blk, _window_frame("window_frame", x))             # 45 deg chamfered frame on the outboard face
    screws = [(x, P.BLOCK_SCREW_VALLEY_Y) for x in P.bank_between_x] + [(x, P.BLOCK_SCREW_END_Y) for x in P.block_end_screws_x]
    for x, y in screws:
        U.boolean(blk, F.screw_cbore("blk_screw", z0, z1, P.SCREW_FLOOR, x, y))
    for x in P.bank_between_x:
        for y in P.HEAD_SCREW_Y:
            U.boolean(blk, U.cylinder("head_ins", P.insert_hole / 2, z1 - P.INSERT_DEPTH, z1 + 1, x, y))
    for x, y in P.locator_xy:
        U.boolean(blk, U.cylinder("locator", P.LOCATOR_D / 2, z0 - P.LOCATOR_H, z0 + 0.1, x, y), "UNION")
    U.cleanup(blk)
    U.shade(blk)
    return blk


def placed(case, bank, with_case=True):
    out = []
    if with_case:
        out.append(("crankcase", case))
    for b in ("A", "B"):
        out.append((f"bank_{b}", _to_bank(U.copy(bank, f"bank_{b}"), b)))
    return out
