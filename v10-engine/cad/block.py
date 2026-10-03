"""Crankcase, cylinder banks and end plates.

Build order the geometry is designed for:
 1. End plates (with the 608 main bearings) go onto the crank's main shafts.
 2. The crank module (crank + rods + pistons + end plates) is lowered into
    the open-top crankcase from above; the end-plate spigots drop into the
    crankcase ends.
 3. The valley beam drops in between the two rows of con-rods and bolts to
    both end plates.
 4. Each cylinder bank lowers straight down its bore axis over its five
    pistons onto the crankcase (outboard) and valley beam (valley side).
    Two printed pegs make it fit only one way round.
 5. Guide rails drop in through the lug slots, through the piston lug
    bushings, into the valley beam. The cylinder head caps them.

Bank-local frame (used for the bank blocks and bank features): x along the
crank, z' along the bore axis from the crank axis, y' towards the valley.
Both banks use the SAME block part (rotated 180 deg for bank B).
"""

import math

import cadquery as cq

from common import C, box, bridge_step, crush_x, crush_z, cyl_x, cyl_z, move, polar, rot_x, rot_z, safe_clean

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
# 01 Crankcase (open-top U) and 02 Valley beam
# ---------------------------------------------------------------------------
# The two con-rod slots run the full length, so the ridge between them is a
# separate part (the valley beam). That also lets the whole crank module
# (crank + rods + pistons) be lowered into the crankcase from above.
CASE_END_SCREWS = [(-40.0, -22.0), (40.0, -22.0), (-42.0, -3.0), (42.0, -3.0)]   # (y, z) U-body
BEAM_END_SCREWS = [(-9.0, 39.0), (9.0, 39.0)]                                      # (y, z) valley beam
END_PLATE_SCREWS = CASE_END_SCREWS + BEAM_END_SCREWS
BASE_INSERTS = [(sx * 112.0, sy * 40.0) for sx in (-1, 1) for sy in (-1, 1)]
SQ2 = math.sqrt(2.0)


def bank_between_x():
    """X positions between neighbouring cylinders of bank A (bank-local)."""
    xs = C.BANK_A_CYL_X
    return [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]


def block_end_screws_x():
    xs = C.BANK_A_CYL_X
    return [xs[0] + 18.0, xs[-1] - 19.0]


def locator_xy():
    return [(C.BANK_A_CYL_X[0] + 18.0, C.LOCATOR_Y), (C.BANK_A_CYL_X[-1] - 18.0, C.LOCATOR_Y)]


def beam_profile():
    """Cross-section (y, z) of the valley beam = the ridge between the slots."""
    p_slot = C.CASE_SLOT_HALF * SQ2          # slot valley edge, in y+z / z-y units
    p_cav = C.CASE_INTERIOR_R * SQ2          # teardrop roof of the crank cavity
    p_face = C.FACE_DIST * SQ2               # bank mounting faces
    pq = [(p_face, p_face), (p_face, p_slot), (p_cav, p_slot), (p_cav, p_cav),
          (p_slot, p_cav), (p_slot, p_face)]
    return [((p - q) / 2, (p + q) / 2) for p, q in pq]


def _bank_face_features(ins_d, which):
    """Cutters on one bank's mounting face, bank-local. which: 'case' or 'beam'."""
    h = C.CASE_HALF_LEN
    f = []
    if which == "case":
        f.append(box(-h - 1, h + 1, -C.CASE_SLOT_HALF, C.CASE_SLOT_HALF, 0.0, C.FACE_DIST + 1))
        for x in block_end_screws_x():
            f.append(cyl_z(ins_d / 2, C.FACE_DIST - C.INSERT_DEPTH, C.FACE_DIST + 1, x, C.BLOCK_SCREW_END_Y))
    else:
        for x in bank_between_x():
            f.append(cyl_z(ins_d / 2, C.FACE_DIST - C.INSERT_DEPTH, C.FACE_DIST + 1, x, C.BLOCK_SCREW_VALLEY_Y))
        for x, y in locator_xy():
            f.append(cyl_z(C.hole(C.LOCATOR_D, "spigot") / 2, C.FACE_DIST - C.LOCATOR_H - 0.5, C.FACE_DIST + 1, x, y))
        for x in C.BANK_A_CYL_X:
            # rail foot: crush ribs centre it, it still slides in by hand
            f.append(crush_z(C.RAIL_DIA, C.RAIL_BOTTOM, C.FACE_DIST + 0.01, x, C.RAIL_OFFSET, "rail_3", entry="hi"))
    out = f[0]
    for g in f[1:]:
        out = out.fuse(g)
    return out


def crankcase():
    h = C.CASE_HALF_LEN
    body = _prism(outer_profile(), -h, h)
    body = body.cut(teardrop(C.CASE_INTERIOR_R, -h - 1, h + 1))
    body = body.cut(_prism(beam_profile(), -h - 1, h + 1))      # the beam's space
    ins_d = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
    for bank in ("A", "B"):
        body = body.cut(to_bank(_bank_face_features(ins_d, "case"), bank))
    for sx in (-1, 1):
        for y, z in CASE_END_SCREWS:
            x0 = sx * h
            lo, hi = sorted((x0 - sx * C.INSERT_DEPTH, x0 + sx * 1))
            body = body.cut(cyl_x(ins_d / 2, lo, hi, y, z))
    for x, y in BASE_INSERTS:
        body = body.cut(cyl_z(ins_d / 2, C.CASE_FLOOR_Z - 1, C.CASE_FLOOR_Z + C.INSERT_DEPTH, x, y))
    # hall-effect sensor pocket (from below) under the front end-web magnet;
    # its leads go straight down through a hole in the base top
    hx = C.WEB_FACE_X + C.END_WEB_T / 2
    hp = C.HALL_POCKET
    body = body.cut(box(hx - hp["l"] / 2, hx + hp["l"] / 2, -hp["w"] / 2, hp["w"] / 2,
                        C.CASE_FLOOR_Z - 1, C.CASE_FLOOR_Z + hp["d"]))
    return safe_clean(body)


def valley_beam():
    h = C.CASE_HALF_LEN
    beam = _prism(beam_profile(), -h, h)
    ins_d = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
    for bank in ("A", "B"):
        beam = beam.cut(to_bank(_bank_face_features(ins_d, "beam"), bank))
    for sx in (-1, 1):
        for y, z in BEAM_END_SCREWS:
            x0 = sx * h
            lo, hi = sorted((x0 - sx * C.INSERT_DEPTH, x0 + sx * 1))
            beam = beam.cut(cyl_x(ins_d / 2, lo, hi, y, z))
    return safe_clean(beam)


def print_beam(s):
    """Lay the beam on bank A's land (that face becomes the flat bed face)."""
    s = rot_x(s, -C.BANK_A_ANGLE)                       # bank A axis -> +Z
    return s.rotate((0, 0, 0), (1, 0, 0), 180)           # land face down


# ---------------------------------------------------------------------------
# 03 Cylinder bank (x2, identical)
# ---------------------------------------------------------------------------
def _window(x):
    """Cut-away window through the outboard wall into the bore. Its bottom is a
    45 deg V, so when the block prints deck-down the window top is a gable of
    two 45 deg overhangs: no bridge and no shallow curve where it meets the
    bore. It reads as a machined lightening cut."""
    hw = C.WINDOW_HALF_W
    yo = C.BLOCK_Y_OUT - 1
    zb, zt = C.WINDOW_BOTTOM, C.WINDOW_TOP
    pts = [(x - hw, zt), (x - hw, zb + hw), (x, zb), (x + hw, zb + hw), (x + hw, zt)]     # (x, z')
    wire = cq.Wire.makePolygon([cq.Vector(px, yo, pz) for px, pz in pts], close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), cq.Vector(0, -yo, 0))


def cylinder_bank():
    z0, z1 = C.FACE_DIST, C.DECK_DIST
    blk = box(C.BLOCK_X_MIN, C.BLOCK_X_MAX, C.BLOCK_Y_OUT, C.BLOCK_Y_VALLEY, z0, z1)
    blk = cq.Workplane().add(blk).edges("|Z").chamfer(3.0).val()
    pocket_r = C.LUG_OD / 2 + C.LUG_POCKET_CLEAR
    ins_d = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
    for x in C.BANK_A_CYL_X:
        blk = blk.cut(cyl_z(C.BORE_DIA / 2, z0 - 1, z1 + 1, x, 0))
        # guide-lug pocket: a through slot (the cylinder head caps the rail top)
        pocket = cyl_z(pocket_r, z0 - 1, z1 + 1, x, C.RAIL_OFFSET)
        pocket = pocket.fuse(box(x - pocket_r, x + pocket_r, 0, C.RAIL_OFFSET, z0 - 1, z1 + 1))
        blk = blk.cut(pocket)
        blk = blk.cut(_window(x))
    # block-to-crankcase screws, counterbored from the deck (M3x8 into inserts)
    screws = [(x, C.BLOCK_SCREW_VALLEY_Y) for x in bank_between_x()]
    screws += [(x, C.BLOCK_SCREW_END_Y) for x in block_end_screws_x()]
    for x, y in screws:
        cb = cyl_z(C.hole(C.M3_CBORE) / 2, z0 + C.SCREW_FLOOR, z1 + 1, x, y)
        blk = blk.cut(cb)
        blk = blk.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, z0 - 1, z0 + C.SCREW_FLOOR + 0.1, x, y))
        # prints deck-down: the counterbore floor is a ceiling -> bridged step
        blk = blk.cut(bridge_step(cb, C.hole(C.M3_CLEAR) / 2, (x, y, z0 + C.SCREW_FLOOR), "z", -1, C.LAYER["bank"]))
    # cylinder-head screw inserts in the deck, on the two cam lines
    for x in bank_between_x():
        for y in C.HEAD_SCREW_Y:
            blk = blk.cut(cyl_z(ins_d / 2, z1 - C.INSERT_DEPTH, z1 + 1, x, y))
    # side-panel magnets in the outboard face, between the windows
    for x in bank_between_x():
        blk = blk.cut(crush_x(C.MAGNET["d"], 0, C.MAGNET["h"] + 0.3, 0, 0, "magnet_6", entry="lo")
                      .rotate((0, 0, 0), (0, 0, 1), 90)          # axis along +Y'
                      .translate(cq.Vector(x, C.BLOCK_Y_OUT - 0.01, C.SIDE_PANEL_MAGNET_Z)))
    for x, y in locator_xy():
        blk = blk.fuse(cyl_z(C.LOCATOR_D / 2, z0 - C.LOCATOR_H, z0 + 0.1, x, y))
    return safe_clean(blk)


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
    # 608 seat: pressed in from the INSIDE face until it stops on a lip on the
    # outside (the lip only touches the outer ring). Plain lead-in bore, then
    # a crush-rib seat exactly one bearing wide.
    lead_d = C.BEARING_608["od"] + C.HOLE_COMP + C.CRUSH_RELIEF
    plate = plate.cut(cyl_x(lead_d / 2, C.END_PLATE_INNER_X - 1, C.BEARING_INNER_X + 0.01))
    plate = plate.cut(crush_x(C.BEARING_608["od"], C.BEARING_INNER_X, C.BEARING_OUTER_X,
                              0, 0, "bearing_608", entry="lo"))
    plate = plate.cut(cyl_x(C.BEARING_608_OUTER_LIP_ID / 2, C.BEARING_OUTER_X - 0.01, x_out + 1))
    for y, z in END_PLATE_SCREWS:
        plate = plate.cut(cyl_x(C.hole(C.M3_CLEAR) / 2, h - 1, x_out + 1, y, z))
        cb = cyl_x(C.hole(C.M3_CBORE) / 2, h + C.SCREW_FLOOR, x_out + 1, y, z)
        plate = plate.cut(cb)
        # prints outer-face down: bridged counterbore ceiling
        plate = plate.cut(bridge_step(cb, C.hole(C.M3_CLEAR) / 2, (h + C.SCREW_FLOOR, y, z), "x", -1, C.LAYER["plate"]))
    # magnets for the drive cover (front) / rear cover (Phase 3) - same pattern both ends
    for y, z in C.COVER_MAGNETS:
        plate = plate.cut(crush_x(C.MAGNET["d"], x_out - C.MAGNET["h"] - 0.3, x_out + 0.5, y, z,
                                  "magnet_6", entry="hi"))
    return safe_clean(plate)


def placed_static(lib):
    out = [("crankcase", lib["case"], "case"), ("valley_beam", lib["beam"], "case")]
    out.append(("bank_A", to_bank(lib["bank"], "A"), "block"))
    out.append(("bank_B", to_bank(lib["bank"], "B"), "block"))
    out.append(("end_plate_front", lib["plate"], "case"))
    out.append(("end_plate_rear", rot_z(lib["plate"], 180), "case"))
    return out


def build_all():
    return {"case": crankcase(), "beam": valley_beam(), "bank": cylinder_bank(), "plate": end_plate()}


def print_bank(s):
    # deck face down on the bed (flat head joint), bores vertical, locator pegs on top
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


def print_plate(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)   # outer face down
