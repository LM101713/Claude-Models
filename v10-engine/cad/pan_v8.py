"""Stock-car V8 oil pan = motor + electronics bay, rear bellhousing, and the
placement of the purchased drive parts (motor, pulleys, belt, spacer - from
drive.py, unchanged from the V10: the drive stays at the FRONT, hidden inside
the front cover / harmonic damper that come after the pan is approved).

  40 oil pan (x1)            41 pan floor panel (x1, 6 captive M3 screws)
  42 bellhousing (x1, 3 magnets on the rear end plate, cosmetic)

Engine frame. The pan's front wall is the motor bulkhead (vertical slots for
belt tension, both belt lengths); its top skin screws up into the crankcase
floor inserts from inside (hidden fasteners); the controller board sits on
the floor panel; the stand brackets bolt to the pan sides (later).
Printing: pan skin-down (open floor up), panel flat, bell rear face down.
"""

import math

import cadquery as cq

import drive
from common import C, box, crush_x, cyl_x, cyl_z, rot_z, safe_clean

P = C.PAN
X0, X1 = -C.END_PLATE_OUTER_X, C.END_PLATE_OUTER_X        # pan outer faces = end plates' outer faces
Y0, Y1 = -P["w"] / 2, P["w"] / 2                          # rail section (upper)
SY0, SY1 = -P["w_sump"] / 2, P["w_sump"] / 2              # sump (lower)
ZT, ZB, ZSTEP = C.CASE_FLOOR_Z, P["z_bot"], P["z_step"]
W, RW = P["wall"], C.MOTOR_PLATE_T                        # side / rear wall, front (motor) wall
ZS = ZT - P["skin"]                                       # underside of the top skin
ZF = ZB + P["floor"]                                      # top of the floor ring
INS = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
S45 = math.sqrt(0.5)
IX0, IX1, IY0, IY1 = X0 + W, X1 - RW, SY0 + W, SY1 - W     # sump interior (floor ring / panel follow it)
PX0, PX1, PY0, PY1 = IX0 + P["ledge"], IX1 - P["ledge"], IY0 + P["ledge"], IY1 - P["ledge"]   # floor opening
RO = P["rabbet_overlap"]                                  # panel overlaps the floor ring by this much
RX0, RX1, RY0, RY1 = PX0 - RO, PX1 + RO, PY0 - RO, PY1 + RO   # panel rabbet (= panel outline)
BOARD_STACK = 22.0          # tallest part on the board (ESP32 on headers, driver heatsink)


def _rbox(x0, x1, y0, y1, z0, z1, r):
    return cq.Workplane().add(box(x0, x1, y0, y1, z0, z1)).edges("|Z").fillet(r).val()


def panel_screws():
    """6 captive screws in the panel's overlap band (into bosses on the floor ring)."""
    i = P["panel_screw_inset"]
    xs = (PX0 - i, (PX0 + PX1) / 2, PX1 + i)
    return [(x, y) for x in xs for y in (PY0 - i, PY1 + i)]


# ---------------------------------------------------------------------------
# 40 Oil pan
# ---------------------------------------------------------------------------
def pan():
    upper = _rbox(X0, X1, Y0, Y1, ZSTEP - 0.1, ZT, P["r"])
    sump = _rbox(X0, X1, SY0, SY1, ZB, ZSTEP + 6.0, P["r"])
    sump = cq.Workplane().add(sump).faces("<Z").edges().chamfer(P["bottom_chamfer"]).val()
    body = upper.fuse(sump)
    # 45 deg under-cut from the rail section down to the sump (prints as a 45 deg overhang skin-down)
    for sgn in (-1, 1):
        yw, ys = (Y1, SY1) if sgn > 0 else (Y0, SY0)
        d = abs(yw - ys)
        wedge = (cq.Workplane("YZ").workplane(offset=X0 + P["r"])
                 .polyline([(ys, ZSTEP + 0.1), (yw, ZSTEP + 0.1), (ys, ZSTEP - d)]).close()
                 .extrude(X1 - X0 - 2 * P["r"]).val())
        body = body.fuse(wedge)
    # side rail flanges (the pan-to-block gasket rail) and horizontal ribs on the sump
    fo, fh = P["flange_out"], P["flange_h"]
    for sgn in (-1, 1):
        yw = Y1 if sgn > 0 else Y0
        fl = box(X0 + 8, X1 - 8, min(yw - sgn * 0.2, yw + sgn * fo), max(yw - sgn * 0.2, yw + sgn * fo), ZT - fh, ZT)
        fl = cq.Workplane().add(fl).edges("|Y").chamfer(2.0).val()
        body = body.fuse(fl)
        ys = SY1 if sgn > 0 else SY0
        for z in P["rib_z"]:
            rib = box(X0 + 14, X1 - 14, min(ys - sgn * 0.3, ys + sgn * P["rib_out"]), max(ys - sgn * 0.3, ys + sgn * P["rib_out"]),
                      z - P["rib_h"] / 2, z + P["rib_h"] / 2)
            # 45 deg on the rib's top outer edge: no overhang when the pan prints skin-down
            rib = cq.Workplane().add(rib).edges(">Z").edges(">Y" if sgn > 0 else "<Y").chamfer(P["rib_out"] * 0.7).val()
            for xb in C.STAND["bracket_x"]:                      # ribs stop either side of the stand brackets
                rib = rib.cut(box(xb - C.STAND["bracket_w"] / 2 - 3.0, xb + C.STAND["bracket_w"] / 2 + 3.0, Y0 - 10, Y1 + 10, ZB - 1, ZT + 1))
            body = body.fuse(rib)
    # interior: rail section + sump, open floor (panel), top skin stays
    body = body.cut(_rbox(IX0, IX1, Y0 + W, Y1 - W, ZSTEP + W, ZS, max(1.0, P["r"] - W)))
    body = body.cut(_rbox(IX0, IX1, IY0, IY1, ZF, ZS, max(1.0, P["r"] - W)))
    for sgn in (-1, 1):                                   # inside of the 45 deg under-cut
        yw, ys = (Y1 - W, SY1 - W) if sgn > 0 else (Y0 + W, SY0 + W)
        d = abs(yw - ys)
        wedge = (cq.Workplane("YZ").workplane(offset=IX0)
                 .polyline([(ys, ZSTEP + W + 0.1), (yw, ZSTEP + W + 0.1), (ys, ZSTEP + W - d)]).close()
                 .extrude(IX1 - IX0).val())
        body = body.cut(wedge)
    body = body.cut(_rbox(PX0, PX1, PY0, PY1, ZB - 1, ZF + 1, 3.0))                      # floor opening
    body = body.cut(_rbox(RX0 - C.CLEARANCE, RX1 + C.CLEARANCE, RY0 - C.CLEARANCE, RY1 + C.CLEARANCE,
                          ZB - 1, ZB + P["panel_t"], 3.0 + C.CLEARANCE))                 # panel rabbet
    # panel screw bosses with inserts (on the ledge, inside)
    for x, y in panel_screws():
        body = body.fuse(cyl_z(4.5, ZF - 0.3, ZS + 0.1, x, y).intersect(box(IX0, IX1, IY0, IY1, ZB, ZS + 0.2)))   # pillar up to the skin
        body = body.cut(cyl_z(INS / 2, ZB + P["panel_t"] - 0.5, ZF + 8.0 - 2.0, x, y))
    # pan-to-crankcase screws: M3x8 up through the skin, heads inside the pan
    for x, y in C.PAN_SCREWS:
        body = body.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, ZS - 1, ZT + 1, x, y))
        body = body.cut(cyl_z(C.hole(C.M3_CBORE) / 2, ZS - 1, ZT - 2.5, x, y))
    # hall-sensor lead slot through the skin (sensor body in the crankcase floor pocket)
    hs = C.HALL_LEAD_SLOT
    hx = C.HALL_X + hs["dx"]
    body = body.cut(box(hx - hs["l"] / 2, hx + hs["l"] / 2, -hs["w"] / 2, hs["w"] / 2, ZS - 1, ZT + 1))
    # stand bracket bosses with horizontal inserts inside the sump walls
    try:
        import stand_v8
        for boss, hole in stand_v8.pan_bracket_bosses():
            body = body.fuse(boss.intersect(box(IX0, IX1, IY0 - 1, IY1 + 1, ZF, ZSTEP)))
            body = body.cut(hole)
    except ImportError:
        pass
    # harness hole in the rear wall (inside the bellhousing)
    h = C.HARNESS_HOLE
    body = body.cut(cyl_x(h["d"] / 2, X0 - 1, IX0 + 1, h["y"], h["z"]))
    # front wall = motor bulkhead: boss slot + 4 bolt slots, nominal 210 and 220 mm belts, tension travel
    za, zb = C.MOTOR_SLOT_BOTTOM, C.MOTOR_SLOT_TOP
    xa, xb = C.MOTOR_FACE_X - 1, X1 + 1

    def slot(r, y):
        return cyl_x(r, xa, xb, y, za).fuse(cyl_x(r, xa, xb, y, zb)).fuse(box(xa, xb, y - r, y + r, za, zb))
    rb = C.MOTOR["boss_d"] / 2 + C.MOTOR_BOSS_SLOT_CLEAR
    body = body.cut(slot(rb, 0.0))
    # pointed lower end of the boss slot: it is the top of an arch when the pan prints skin-down
    body = body.cut(cq.Workplane("YZ").workplane(offset=xa)
                    .polyline([(-rb * S45, za - rb * S45), (0.0, za - rb / S45), (rb * S45, za - rb * S45)])
                    .close().extrude(xb - xa).val())
    hp = C.MOTOR["hole_pitch"] / 2
    for dy in (-hp, hp):
        for dz in (-hp, hp):
            body = body.cut(slot(C.hole(C.M3_CLEAR) / 2, dy).translate(cq.Vector(0, 0, dz)))
    return safe_clean(body)


def print_pan(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)          # skin on the bed, open floor up


# ---------------------------------------------------------------------------
# 41 Floor panel (captive screws) with the board standoffs
# ---------------------------------------------------------------------------
def floor_panel():
    c = C.CLEARANCE
    p = _rbox(RX0, RX1, RY0, RY1, ZB, ZB + P["panel_t"], 3.0)
    for x, y in panel_screws():
        p = p.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, ZB - 1, ZB + P["panel_t"] - C.CAPTIVE_LIP_T, x, y))
        p = p.cut(cyl_z(C.CAPTIVE_LIP_D / 2, ZB - 1, ZB + P["panel_t"] + 1, x, y))
    # controller board standoffs (board components-up, in the rear half of the pan)
    b = C.PCB
    for x, y in _board_holes():
        p = p.fuse(cyl_z(4.0, ZB + P["panel_t"] - 0.1, ZB + P["panel_t"] + b["standoff"], x, y))
        p = p.cut(cyl_z(INS / 2, ZB + 1.0, ZB + P["panel_t"] + b["standoff"] + 0.1, x, y))
    # vents under the motor and the driver
    for i in range(8):
        x = C.MOTOR_FACE_X - 36 + i * 4.5
        for yc in (-20.0, 20.0):
            p = p.cut(box(x - 1.2, x + 1.2, yc - 12, yc + 12, ZB - 1, ZB + P["panel_t"] + 1))
    return safe_clean(p)


def print_panel(s):
    return s


def _board_centre():
    b = C.PCB
    return (IX0 + P["ledge"] + 8.0 + b["w"] / 2, 0.0)


def _board_holes():
    b = C.PCB
    cx, cy = _board_centre()
    return [(cx + dx * (b["w"] / 2 - b["inset"]), cy + dy * (b["h"] / 2 - b["inset"])) for dx in (-1, 1) for dy in (-1, 1)]


def electronics_envelopes():
    """Board + component stack as a simple envelope so the interference check proves it fits."""
    b = C.PCB
    cx, cy = _board_centre()
    z0 = ZB + P["panel_t"] + b["standoff"]
    board = box(cx - b["w"] / 2, cx + b["w"] / 2, cy - b["h"] / 2, cy + b["h"] / 2, z0, z0 + 1.6)
    parts = box(cx - b["w"] / 2 + 6, cx + b["w"] / 2 - 6, cy - b["h"] / 2 + 4, cy + b["h"] / 2 - 4, z0 + 1.6, z0 + 1.6 + BOARD_STACK)
    return [("elec_board", board.fuse(parts), "green")]


# ---------------------------------------------------------------------------
# 42 Bellhousing (cosmetic shell on the rear end plate)
# ---------------------------------------------------------------------------
def _bell_outline(off, x0, x1):
    """Bell shape: a circle round the crank axis with straight tangent sides
    down to a flat bottom (convex polygon + arc), extruded along X."""
    b = C.BELL
    r = b["r_top"] - off
    hw = b["half_w_bot"] - off
    zb = b["z_bot"] + off
    # tangent point from the bottom corner (hw, zb) to the circle (0,0) r
    d = math.hypot(hw, zb)
    ang_c = math.atan2(zb, hw)                      # direction centre -> corner
    ang_t = math.acos(r / d)                        # half-angle between corner direction and tangent point
    t_right = ang_c + ang_t                         # tangent point angle on the right side (y > 0)
    pts = [(hw, zb)]
    n = 24
    a0, a1 = t_right, math.pi - t_right             # sweep over the top from right to left
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    pts.append((-hw, zb))
    return cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close().extrude(x1 - x0).val()


def bellhousing():
    b = C.BELL
    x1 = -C.END_PLATE_OUTER_X                 # open rim on the end plate face
    x0 = x1 - b["depth"]
    outer = _bell_outline(0.0, x0, x1)
    outer = cq.Workplane().add(outer).faces("<X").edges().chamfer(2.5).val()
    bell = outer.cut(_bell_outline(b["wall"], x0 + b["wall"], x1 + 1))
    # flywheel hub ring and bolt holes RECESSED into the rear face (the face prints flat on the bed)
    ring = cyl_x(b["hub_r"], x0 - 1, x0 + 1.5).cut(cyl_x(b["hub_r"] - 2.5, x0 - 2, x0 + 2))
    bell = bell.cut(ring)
    for i in range(b["n_bolts"]):
        a = math.radians(i * 360.0 / b["n_bolts"] + 22.5)
        y, z = b["bolt_r"] * math.cos(a), b["bolt_r"] * math.sin(a)
        if z > b["z_bot"] + 6:
            bell = bell.cut(cyl_x(2.2, x0 - 1, x0 + 1.5, y, z))
    # magnet pillars on the end plate pattern (mirrored for the rear plate)
    for y, z in C.COVER_MAGNETS:
        y = -y
        pil = cyl_x(C.COVER_PILLAR_R, x0 + b["wall"] - 0.1, x1, y, z)
        ang = math.degrees(math.atan2(y, z))
        pil = pil.fuse(cq.Workplane().add(box(x0 + b["wall"] - 0.1, x1, -C.COVER_PILLAR_R, C.COVER_PILLAR_R, 0, 8)).val()
                       .rotate((0, 0, 0), (1, 0, 0), -ang).translate(cq.Vector(0, y, z)))
        bell = bell.fuse(pil.intersect(_bell_outline(0.0, x0, x1)))
        bell = bell.cut(crush_x(C.MAGNET["d"], x1 - C.MAGNET["h"] - C.MAGNET_DEPTH_CLEAR, x1 + 0.5, y, z, "magnet_6", entry="hi"))
    return safe_clean(bell)


def print_bell(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90)          # rear face on the bed


# ---------------------------------------------------------------------------
def build_all():
    return {"pan": pan(), "panel": floor_panel(), "bellhousing": bellhousing()}


def placed(lib, with_base=True, with_covers=True):
    out = [("pan", lib["pan"], "carbon"), ("pan_panel", lib["panel"], "case")]
    if with_covers:
        out.append(("bellhousing", lib["bellhousing"], "block"))
    out += drive.purchased_parts()
    out += electronics_envelopes()
    return out


def drive_check():
    """Motor / belt / pulleys against pan, panel, crankcase, board; motor at
    both slot ends and with the 220 mm belt."""
    import assembly_v8 as A
    parts = dict((n, s) for n, s, _ in A.engine(0.0) + A.drive_and_base() + A.styling_parts())
    pairs = [("pan", "motor"), ("pan", "belt"), ("pan", "pulley_20T"), ("pan", "pulley_60T"), ("pan", "crankcase"),
             ("pan", "end_plate_front"), ("pan", "end_plate_rear"), ("pan_panel", "motor"), ("pan_panel", "elec_board"),
             ("pan", "elec_board"), ("motor", "elec_board"), ("crankcase", "motor"), ("belt", "pulley_60T"),
             ("belt", "pulley_20T"), ("bellhousing", "end_plate_rear"), ("bellhousing", "pan"),
             ("bellhousing", "main_shaft_rear"), ("bellhousing", "crankcase"),
             ("front_cover", "pulley_60T"), ("front_cover", "belt"), ("front_cover", "pulley_20T"),
             ("front_cover", "end_plate_front"), ("front_cover", "pan"), ("front_cover", "main_shaft_front"),
             ("front_cover", "damper"), ("front_cover", "accessory"), ("accessory", "damper"),
             ("damper", "pulley_60T"), ("accessory", "head_A"), ("accessory", "valve_cover_A"), ("accessory", "intake_base"),
             ("accessory", "intake_lid")]
    bad = []
    for a, b in pairs:
        v = parts[a].intersect(parts[b]).Volume()
        if v > 0.01:
            bad.append((a, b, round(v, 2)))
        print(f"  {a:>16} x {b:<16} {v:8.3f} mm3", flush=True)
    nominal = C.MOTOR_Z
    try:
        for z, tag in ((C.MOTOR_Z_ALT, f"{C.BELT_ALT_LEN:.0f}mm belt"), (C.MOTOR_SLOT_TOP, "slot top"),
                       (C.MOTOR_SLOT_BOTTOM, "slot bottom")):
            C.MOTOR_Z = z
            moved = dict((n, s) for n, s, _ in drive.purchased_parts())
            for a, b in pairs:
                if a in moved or b in moved:
                    sa, sb = moved.get(a, parts[a]), moved.get(b, parts[b])
                    v = sa.intersect(sb).Volume()
                    if v > 0.01 and not ({a, b} <= {"belt", "pulley_60T", "pulley_20T"} and tag != f"{C.BELT_ALT_LEN:.0f}mm belt"):
                        bad.append((tag, a, b, round(v, 2)))
            print(f"  motor at z={z:.1f} ({tag}) checked", flush=True)
    finally:
        C.MOTOR_Z = nominal
    return bad
