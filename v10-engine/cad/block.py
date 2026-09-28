"""Crankcase, cylinder banks and end plates.

Build order the geometry is designed for:
 1. Crank module (crank + rods + pistons) slides into the crankcase from one
    end - the con-rods run along the two long slots in the bank faces.
 2. End plates (with the 608 main bearings) slide onto the main shafts and
    bolt to the crankcase ends. Their spigots locate them.
 3. Each cylinder bank lowers straight down its bore axis over its five
    pistons. Two printed pegs make it fit only one way round.
 4. Guide rails drop in through the deck holes, through the piston lug
    bushings, into the crankcase.

Bank-local frame (used for the bank blocks and bank features): x along the
crank, z' along the bore axis from the crank axis, y' towards the valley.
Both banks use the SAME block part (rotated 180 deg for bank B).
"""

import math

import cadquery as cq

from common import C, box, cyl_x, cyl_z, move, polar, rot_x, rot_z

S45 = math.sqrt(0.5)


def _face_corner(y_local):
    """Global (y, z) of a point on bank A's mounting face at bank-local y'."""
    a = polar(1.0, C.BANK_A_ANGLE)
    v = polar(1.0, C.BANK_A_ANGLE + 90.0)
    return (C.FACE_DIST * a[0] + y_local * v[0], C.FACE_DIST * a[1] + y_local * v[1])


def outer_profile():
    cy, cz = _face_corner(C.BLOCK_Y_OUT)
    ridge = C.FACE_DIST / math.cos(math.radians(C.BANK_ANGLE / 2))
    return [(cy, C.CASE_FLOOR_Z), (-cy, C.CASE_FLOOR_Z), (-cy, cz), (0.0, ridge), (cy, cz)]


def _prism(poly, x0, x1):
    return cq.Workplane("YZ").workplane(offset=x0).polyline(poly).close().extrude(x1 - x0).val()


def teardrop(r, x0, x1):
    """Round cavity with a 45 deg roof so it prints without supports."""
    t = r * S45
    tri = [(-t, t), (0.0, r / S45), (t, t)]
    return cyl_x(r, x0, x1).fuse(_prism(tri, x0, x1))


def to_bank(shape, bank):
    """Bank-local (bank A convention) -> engine frame for either bank."""
    if bank == "B":
        shape = rot_z(shape, 180)
    return rot_x(shape, C.bank_angle(bank))


# ---------------------------------------------------------------------------
# 01 Crankcase
# ---------------------------------------------------------------------------
END_PLATE_SCREWS = [(-40.0, -22.0), (40.0, -22.0), (-42.0, -3.0), (42.0, -3.0), (0.0, 47.0)]
BASE_INSERTS = [(sx * 112.0, sy * 40.0) for sx in (-1, 1) for sy in (-1, 1)]


def bank_between_x():
    """X positions between neighbouring cylinders of bank A (bank-local)."""
    xs = C.BANK_A_CYL_X
    return [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]


def locator_xy():
    return [(C.BANK_A_CYL_X[0] + 18.0, C.LOCATOR_Y), (C.BANK_A_CYL_X[-1] - 18.0, C.LOCATOR_Y)]


def crankcase():
    h = C.CASE_HALF_LEN
    body = _prism(outer_profile(), -h, h)
    body = body.cut(teardrop(C.CASE_INTERIOR_R, -h - 1, h + 1))
    ins_d = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
    for bank in ("A", "B"):
        feats = box(-h - 1, h + 1, -C.CASE_SLOT_HALF, C.CASE_SLOT_HALF, 0.0, C.FACE_DIST + 1)
        for x in bank_between_x():
            for y in C.BLOCK_SCREW_Y:
                feats = feats.fuse(cyl_z(ins_d / 2, C.FACE_DIST - C.INSERT_DEPTH, C.FACE_DIST + 1, x, y))
        for x, y in locator_xy():
            feats = feats.fuse(cyl_z(C.hole(C.LOCATOR_D, "spigot") / 2, C.FACE_DIST - C.LOCATOR_H - 0.5, C.FACE_DIST + 1, x, y))
        for x in C.BANK_A_CYL_X:
            feats = feats.fuse(cyl_z(C.hole(C.RAIL_DIA, "rail_3_slip") / 2, C.RAIL_BOTTOM, C.FACE_DIST + 1, x, C.RAIL_OFFSET))
        body = body.cut(to_bank(feats, bank))
    # end-plate inserts (both ends)
    for sx in (-1, 1):
        for y, z in END_PLATE_SCREWS:
            x0 = sx * h
            lo, hi = sorted((x0 - sx * C.INSERT_DEPTH, x0 + sx * 1))
            body = body.cut(cyl_x(ins_d / 2, lo, hi, y, z))
    # base inserts in the underside
    for x, y in BASE_INSERTS:
        body = body.cut(cyl_z(ins_d / 2, C.CASE_FLOOR_Z - 1, C.CASE_FLOOR_Z + C.INSERT_DEPTH, x, y))
    # hall-effect sensor pocket (from below) under the front end-web magnet,
    # plus a wire slot running to the nearest base opening
    hx = C.WEB_FACE_X + C.END_WEB_T / 2
    hp = C.HALL_POCKET
    body = body.cut(box(hx - hp["l"] / 2, hx + hp["l"] / 2, -hp["w"] / 2, hp["w"] / 2,
                        C.CASE_FLOOR_Z - 1, C.CASE_FLOOR_Z + hp["d"]))
    body = body.cut(box(hx - 1.5, h + 1, -1.5, 1.5, C.CASE_FLOOR_Z - 1, C.CASE_FLOOR_Z + 2.0))
    return body.clean()


# ---------------------------------------------------------------------------
# 02 Cylinder bank (x2, identical)
# ---------------------------------------------------------------------------
def cylinder_bank():
    z0, z1 = C.FACE_DIST, C.DECK_DIST
    blk = box(C.BLOCK_X_MIN, C.BLOCK_X_MAX, C.BLOCK_Y_OUT, C.BLOCK_Y_VALLEY, z0, z1)
    # soften the long vertical edges (premium look, no sharp corners)
    blk = cq.Workplane().add(blk).edges("|Z").chamfer(3.0).val()
    pocket_r = C.LUG_OD / 2 + C.LUG_POCKET_CLEAR
    for x in C.BANK_A_CYL_X:
        blk = blk.cut(cyl_z(C.BORE_DIA / 2, z0 - 1, z1 + 1, x, 0))
        # guide-lug pocket, open at the bottom, closed by the deck ring
        top = z1 - C.DECK_RING_T
        pocket = cyl_z(pocket_r, z0 - 1, top, x, C.RAIL_OFFSET)
        pocket = pocket.fuse(box(x - pocket_r, x + pocket_r, 0, C.RAIL_OFFSET, z0 - 1, top))
        blk = blk.cut(pocket)
        blk = blk.cut(cyl_z(C.hole(C.RAIL_DIA, "rail_3_slip") / 2, top - 1, z1 + 1, x, C.RAIL_OFFSET))
        # cut-away window in the outboard wall
        win = box(x - C.WINDOW_HALF_W, x + C.WINDOW_HALF_W, C.BLOCK_Y_OUT - 1, 0,
                  C.WINDOW_BOTTOM, C.WINDOW_TOP)
        win = cq.Workplane().add(win).edges("|Y").fillet(4.0).val()
        blk = blk.cut(win)
    # screws: counterbored from the deck, M3x8 into crankcase inserts
    for x in bank_between_x():
        for y in C.BLOCK_SCREW_Y:
            blk = blk.cut(cyl_z(C.hole(C.M3_CBORE) / 2, z0 + C.SCREW_FLOOR, z1 + 1, x, y))
            blk = blk.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, z0 - 1, z0 + C.SCREW_FLOOR + 0.1, x, y))
    # locating pegs (make the block fit one way only)
    for x, y in locator_xy():
        blk = blk.fuse(cyl_z(C.LOCATOR_D / 2, z0 - C.LOCATOR_H, z0 + 0.1, x, y))
    return blk.clean()


# ---------------------------------------------------------------------------
# 03 End plate (x2, identical) - carries one 608 main bearing
# ---------------------------------------------------------------------------
def end_plate():
    """Local frame = engine frame of the FRONT plate (rear = rotate 180 about Z)."""
    h = C.CASE_HALF_LEN
    x_out = C.END_PLATE_OUTER_X
    plate = _prism(outer_profile(), h, x_out)
    # spigot into the crankcase cavity (self-locating)
    sp = teardrop(C.CASE_INTERIOR_R - C.CLEARANCE, C.END_PLATE_INNER_X, h + 0.01)
    plate = plate.fuse(sp)
    # hollow the spigot so it clears the crank flange and saves plastic
    plate = plate.cut(cyl_x(C.CASE_INTERIOR_R - 4.0, C.END_PLATE_INNER_X - 1, h - 3.0))
    # bearing seat (from outside) and lip that only touches the outer ring
    plate = plate.cut(cyl_x(C.hole(C.BEARING_608["od"], "bearing_608") / 2, C.BEARING_INNER_X, x_out + 1))
    plate = plate.cut(cyl_x(C.BEARING_608_OUTER_LIP_ID / 2, C.END_PLATE_INNER_X - 1, x_out))
    for y, z in END_PLATE_SCREWS:
        plate = plate.cut(cyl_x(C.hole(C.M3_CLEAR) / 2, h - 1, x_out + 1, y, z))
        plate = plate.cut(cyl_x(C.hole(C.M3_CBORE) / 2, h + C.SCREW_FLOOR, x_out + 1, y, z))
    return plate.clean()


def placed_static(lib):
    out = [("crankcase", lib["case"], "case")]
    out.append(("bank_A", to_bank(lib["bank"], "A"), "block"))
    out.append(("bank_B", to_bank(lib["bank"], "B"), "block"))
    out.append(("end_plate_front", lib["plate"], "case"))
    out.append(("end_plate_rear", rot_z(lib["plate"], 180), "case"))
    return out


def build_all():
    return {"case": crankcase(), "bank": cylinder_bank(), "plate": end_plate()}


def print_bank(s):
    # deck face down on the bed (flat head joint), bores vertical, pegs on top
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


def print_plate(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)   # outer face down
