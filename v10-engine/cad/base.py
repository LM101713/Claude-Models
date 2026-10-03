"""Phase 2 display base.

The base is 400 x 250 x 72 mm, too long for one print, so it is two halves
joined at X=0 with 2 locating pegs and 6 M3x8 screws (all inside). Each half has a
removable bottom panel (both panels are the SAME part).

  09 base_front : motor bulkhead (slotted for belt tension), belt slot, hall wire hole
  10 base_rear  : control panel (12 V jack, power rocker, speed knob, start button),
                  carrier-PCB standoffs, LED-harness hole
  11 base_panel : x2, vents over the motor and the electronics, 4 screws each

Printing: halves print TOP SKIN DOWN on a textured plate (the visible top gets
the bed texture, and the inside needs no supports). The top edge chamfer is a
45 deg overhang, which prints cleanly.
"""

import math

import cadquery as cq

from common import C, box, cyl_x, cyl_z, move, rot_z, safe_clean

X0, X1 = C.BASE_X
Y0, Y1 = C.BASE_Y
ZT = C.BASE_TOP_Z
ZB = C.BASE_BOTTOM_Z
W = C.BASE_WALL
ZS = ZT - C.BASE_SKIN                       # underside of the top skin
ZP = ZB + C.PANEL_T                         # top of the bottom panel
INS = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
S45 = math.sqrt(0.5)


def _panel_screws(front=True):
    xi = X1 - W - C.PANEL_SCREW_INSET
    xs = (C.PANEL_SCREW_INSET, xi)
    ys = (Y0 + W + C.PANEL_SCREW_INSET, Y1 - W - C.PANEL_SCREW_INSET)
    pts = [(x, y) for x in xs for y in ys]
    return pts if front else [(-x, -y) for x, y in pts]


CASE_SCREWS = [(sx * 112.0, sy * 40.0) for sx in (-1, 1) for sy in (-1, 1)]   # = block.BASE_INSERTS


def _shell():
    s = box(X0, X1, Y0, Y1, ZB, ZT)
    s = cq.Workplane().add(s).faces(">Z").edges().chamfer(C.BASE_TOP_CHAMFER).val()
    s = s.cut(box(X0 + W, X1 - W, Y0 + W, Y1 - W, ZB - 1, ZS))
    # shadow-line groove round the engine footprint (crankcase + end plates)
    g = C.SHADOW_GROOVE
    hx = C.END_PLATE_OUTER_X + g["offset"]
    cy, _ = (52.35 + g["offset"], 0)
    ring = box(-hx - g["w"], hx + g["w"], -cy - g["w"], cy + g["w"], ZT - g["d"], ZT + 1).cut(
        box(-hx, hx, -cy, cy, ZT - g["d"] - 1, ZT + 2))
    s = s.cut(ring)
    # crankcase screws: bosses under the skin, counterbored from below, M3x8
    for x, y in CASE_SCREWS:
        s = s.fuse(cyl_z(7.0, ZS - 8.0, ZS + 0.1, x, y))
        s = s.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, ZS - 9, ZT + 1, x, y))
        s = s.cut(cyl_z(C.hole(C.M3_CBORE) / 2, ZS - 9, ZT - C.SCREW_FLOOR, x, y))
    # panel pillars (both halves), insert from below
    for x, y in _panel_screws(True) + _panel_screws(False):
        s = s.fuse(cyl_z(5.5, ZP, ZS + 0.1, x, y))
        s = s.cut(cyl_z(INS / 2, ZP - 1, ZP + C.INSERT_DEPTH, x, y))
    # cable-tie anchors under the skin (tie passes through a tunnel along Y)
    for x in C.TIE_ANCHOR_X:
        a = box(x - 4, x + 4, C.TIE_ANCHOR_Y - 3, C.TIE_ANCHOR_Y + 3, ZS - 6, ZS + 0.1)
        a = a.cut(box(x - 2.5, x + 2.5, C.TIE_ANCHOR_Y - 4, C.TIE_ANCHOR_Y + 4, ZS - 3.5, ZS - 1.2))
        s = s.fuse(a)
    # side-wall vents (high on the long sides, over the motor and the electronics)
    for xc in (110.0, -150.0):
        for i in range(-4, 5):
            for yside in (Y0, Y1 - W):
                s = s.cut(box(xc + i * 7 - 1.5, xc + i * 7 + 1.5, yside - 1, yside + W + 1, ZT - 26, ZT - 12))
    return s


def _joint_features(s):
    """Screw bosses + pegs across the X=0 joint. Rear side: counterbore; front: insert."""
    for y, z in C.BASE_JOINT_PEGS:
        s = s.fuse(box(-8, 8, y - 6, y + 6, z - 6, ZS + 0.1))
    for y, z in C.BASE_JOINT_SCREWS:
        top = min(z + 6, ZS + 0.1)
        s = s.fuse(box(-8, 8, y - 6, y + 6, z - 6, top))
        if top < ZS:
            # 45 deg gusset from the boss up to the wall/skin: the base prints
            # skin-down, so the boss's engine-top face would otherwise be a
            # 12 mm overhang hanging off the wall
            side = 1 if y > 0 else -1
            wall = C.BASE_Y[1] - W if side > 0 else C.BASE_Y[0] + W
            g = (cq.Workplane("YZ").workplane(offset=-8)
                 .polyline([(y - side * 6, top), (wall, top + abs(wall - (y - side * 6))), (wall, top)]).close()
                 .extrude(16).val())
            s = s.fuse(g.intersect(box(-9, 9, C.BASE_Y[0], C.BASE_Y[1], ZB, ZS + 0.1)))
        s = s.cut(cyl_x(C.hole(C.M3_CLEAR) / 2, -4.1, 0.1, y, z))
        s = s.cut(cyl_x(C.hole(C.M3_CBORE) / 2, -9, -C.SCREW_FLOOR, y, z))
        s = s.cut(cyl_x(INS / 2, -0.1, C.INSERT_DEPTH, y, z))
    return s


def _pegs(front):
    out = []
    for y, z in C.BASE_JOINT_PEGS:
        if front:
            out.append(cyl_x(2.5, -4, 0.1, y, z))                       # peg on the front half
        else:
            out.append(cyl_x(C.hole(5.0, "spigot") / 2, -4.5, 0.1, y, z))  # hole in the rear half
    return out, list(C.BASE_JOINT_PEGS)


def _front_features(s):
    # motor bulkhead with vertical slots: belt tension for the nominal 210 mm
    # loop and the 220 mm second-source loop (motor axis MOTOR_SLOT_TOP..BOTTOM)
    za, zb = C.MOTOR_SLOT_BOTTOM, C.MOTOR_SLOT_TOP
    x0, x1 = C.MOTOR_FACE_X, C.MOTOR_PLATE_X1
    bh = box(x0, x1, Y0 + W - 0.1, Y1 - W + 0.1, ZP + 6, ZS + 0.1)
    s = s.fuse(bh)

    def slot(r, y, dz):
        return cyl_x(r, x0 - 1, x1 + 1, y, za + dz).fuse(cyl_x(r, x0 - 1, x1 + 1, y, zb + dz)).fuse(
            box(x0 - 1, x1 + 1, y - r, y + r, za + dz, zb + dz))
    rb = C.MOTOR["boss_d"] / 2 + 0.5
    s = s.cut(slot(rb, 0, 0.0))
    # the lower end of the boss slot is the top of the arch on the printer (base
    # prints skin-down): pointed 45 deg end instead of a 23 mm round bridge
    s = s.cut(cq.Workplane("YZ").workplane(offset=x0 - 1)
              .polyline([(-rb * S45, za - rb * S45), (0.0, za - rb / S45), (rb * S45, za - rb * S45)])
              .close().extrude(x1 - x0 + 2).val())
    hp = C.MOTOR["hole_pitch"] / 2
    for dy in (-hp, hp):
        for dz in (-hp, hp):
            s = s.cut(slot(C.hole(C.M3_CLEAR) / 2, dy, dz))
    for y in (-80.0, 80.0):      # cable pass-throughs (teardrop: no flat bridge when printed skin-down)
        r = 7.0
        zc = ZP + 16
        s = s.cut(cyl_x(r, x0 - 1, x1 + 1, y, zc))
        tri = (cq.Workplane("YZ").workplane(offset=x0 - 1)
               .polyline([(y - r * 0.7071, zc - r * 0.7071), (y, zc - r * 1.4142), (y + r * 0.7071, zc - r * 0.7071)])
               .close().extrude(x1 - x0 + 2).val())
        s = s.cut(tri)
    # belt slot through the top skin (hidden by the drive cover)
    s = s.cut(box(C.BELT_X - 7, C.BELT_X + 7, -20, 20, ZS - 1, ZT + 1))
    # hall sensor wires straight down from the crankcase floor pocket
    s = s.cut(cyl_z(4.0, ZS - 1, ZT + 1, C.WEB_FACE_X + C.END_WEB_T / 2, 0))
    return s


def _rear_features(s):
    # control panel: rear wall thinned from inside to CONTROL_PANEL_T so the
    # jack / rocker / button nuts and clips can grip
    ys = [c[1] for c in C.CONTROLS]
    s = s.cut(box(X0 + C.CONTROL_PANEL_T, X0 + W + 1, min(ys) - 18, max(ys) + 18,
                  C.CONTROLS_Z - 15, C.CONTROLS_Z + 15))
    # control cut-outs in the rear wall
    for name, y, shape, d in C.CONTROLS:
        s = s.cut(cyl_x(d / 2 + C.HOLE_COMP / 2, X0 - 1, X0 + W + 1, y, C.CONTROLS_Z))
        if name == "speed":
            s = s.cut(cyl_x(C.POT_TAB["d"] / 2, X0 + 1.5, X0 + W + 1, y + C.POT_TAB["dy"], C.CONTROLS_Z))
        # engraved label under each control, reading correctly from behind
        label = {"dc_jack": "12V DC", "power": "POWER", "speed": "SPEED", "start": "START"}[name]
        pl = cq.Plane(origin=(X0 + 0.6, y, C.CONTROLS_Z - 19), xDir=(0, -1, 0), normal=(-1, 0, 0))
        txt = cq.Workplane(pl).text(label, 5.0, 0.8, halign="center", valign="center", kind="bold")
        s = s.cut(txt.val())
    # carrier PCB standoffs
    p = C.PCB
    for dx in (-1, 1):
        for dy in (-1, 1):
            x = p["x_center"] + dx * (p["w"] / 2 - p["inset"])
            y = p["y_center"] + dy * (p["h"] / 2 - p["inset"])
            s = s.fuse(cyl_z(4.0, ZS - p["standoff"], ZS + 0.1, x, y))
            s = s.cut(cyl_z(INS / 2, ZS - p["standoff"] - 1, ZS - p["standoff"] + C.INSERT_DEPTH, x, y))
    # LED harness hole (under the rear cover)
    h = C.HARNESS_HOLE
    s = s.cut(cyl_z(h["d"] / 2, ZS - 1, ZT + 1, h["x"], h["y"]))
    return s


def base_halves():
    whole = _joint_features(_shell())
    front = whole.intersect(box(0, X1 + 1, Y0 - 1, Y1 + 1, ZB - 1, ZT + 1))
    rear = whole.intersect(box(X0 - 1, 0, Y0 - 1, Y1 + 1, ZB - 1, ZT + 1))
    pegs, _ = _pegs(True)
    holes, _ = _pegs(False)
    for pg in pegs:
        front = front.fuse(pg)
    for hl in holes:
        rear = rear.cut(hl)
    front = _front_features(front)
    rear = _rear_features(rear)
    return safe_clean(front), safe_clean(rear)


def bottom_panel():
    """One panel, engine frame, for the FRONT half (rear = same part turned 180 deg)."""
    c = 0.4
    p = box(c, X1 - W - c, Y0 + W + c, Y1 - W - c, ZB, ZP)
    p = cq.Workplane().add(p).edges("|Z").fillet(3.0).val()
    for x, y in _panel_screws(True):
        p = p.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, ZB - 1, ZP + 1, x, y))
    # vents: under the motor and (on the rear copy, rotated) under the electronics
    for i in range(10):
        x = 98 + i * 6.0
        for yc in (-45.0, 0.0, 45.0):
            p = p.cut(box(x - 1.5, x + 1.5, yc - 18, yc + 18, ZB - 1, ZP + 1))
    # foot locating rings (for 20 mm adhesive rubber feet)
    for x in (30.0, 170.0):
        for y in (-95.0, 95.0):
            p = p.cut(cyl_z(10.5, ZB - 1, ZB + 0.4, x, y).cut(cyl_z(9.7, ZB - 2, ZB + 1, x, y)))
    return safe_clean(p)


def print_half(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)       # top skin on the bed


def print_panel(s):
    return s


def placed(lib):
    return [("base_front", lib["base_front"], "carbon"), ("base_rear", lib["base_rear"], "carbon"),
            ("panel_front", lib["panel"], "case"), ("panel_rear", rot_z(lib["panel"], 180), "case")]


def build_all():
    f, r = base_halves()
    return {"base_front": f, "base_rear": r, "panel": bottom_panel()}
