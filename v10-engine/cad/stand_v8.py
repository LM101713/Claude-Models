"""Stock-car V8 display stand:

  46 stand plate    - 300 x 240 x 12, matte black, 4 rubber feet; cut-out
                      under the pan's floor panel (electronics access from
                      below without taking the engine off the brackets); a
                      wiring channel on its underside from the plinth to the
                      cut-out; edition-plate recess on the front edge face
  47 bracket (x4)   - angled strut from the plate up to the pan's sump wall
                      (2 x M3 into pan inserts, 2 x M3 from under the plate)
  48 controls plinth - front-right box with the DC jack, power rocker, speed
                      pot and start button on its FRONT face; wiring down
                      through the plate channel with cable-tie strain relief
  49 edition plate  - the purchased engraved plate (same spec as the V10 H14)

Engine frame, +X = front (damper end), viewer at +X.
"""

import math

import cadquery as cq

from common import C, box, cyl_x, cyl_y, cyl_z, safe_clean

ST, PL = C.STAND, C.PLINTH
XC = ST["x_offset"]
X0, X1 = XC - ST["l"] / 2, XC + ST["l"] / 2
Y0, Y1 = -ST["w"] / 2, ST["w"] / 2
ZT = ST["z_top"]
ZB = ZT - ST["t"]
INS = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
P = C.PAN
SY1 = P["w_sump"] / 2
EDITION_Y = 65.0                    # edition plate centred here on the front edge (left of the plinth)


def _rbox(x0, x1, y0, y1, z0, z1, r):
    return cq.Workplane().add(box(x0, x1, y0, y1, z0, z1)).edges("|Z").fillet(r).val()


def bracket_positions():
    return [(x, sgn) for x in ST["bracket_x"] for sgn in (-1, 1)]


def bracket(sgn=1):
    """Bent-plate bracket on side sgn: foot on the plate, angled strut, tab flat
    against the pan's sump wall. One part; the other side is its mirror (47 / 47m)."""
    t, w = ST["bracket_t"], ST["bracket_w"]
    yf, y_wall, z_tab = ST["foot_y"], SY1 + 0.2, ST["bracket_tab_z"]

    def prism(pts):
        return cq.Workplane("YZ").workplane(offset=-w / 2).polyline([(sgn * y, z) for y, z in pts]).close().extrude(w).val()
    foot = prism([(yf - 22, ZT), (yf + 20, ZT), (yf + 20, ZT + t), (yf - 22, ZT + t)])
    hh = ST["bracket_tab_h"] / 2
    tab = prism([(y_wall, z_tab - hh), (y_wall + t, z_tab - hh), (y_wall + t, z_tab + hh), (y_wall, z_tab + hh)])
    A, B = (yf - 14.0, ZT + t / 2), (y_wall + t / 2, z_tab - hh + 2.0)      # strut centreline
    dy, dz = B[0] - A[0], B[1] - A[1]
    L = math.hypot(dy, dz)
    ny, nz = -dz / L * t / 2, dy / L * t / 2
    strut = prism([(A[0] + ny, A[1] + nz), (B[0] + ny, B[1] + nz), (B[0] - ny, B[1] - nz), (A[0] - ny, A[1] - nz)])
    b = foot.fuse(strut).fuse(tab)
    # 2 screws into the pan wall through the tab, 2 inserts in the foot (screws come from under the plate)
    yw = sgn * y_wall
    for dx in (-8.0, 8.0):
        ya, yb = sorted((yw - sgn * 1, yw + sgn * (t + 1)))
        b = b.cut(cyl_y(C.hole(C.M3_CLEAR) / 2, ya, yb, dx, z_tab))
        ya, yb = sorted((yw + sgn * (t - C.SCREW_FLOOR + 1.5), yw + sgn * (t + 6)))
        b = b.cut(cyl_y(C.hole(C.M3_CBORE) / 2, ya, yb, dx, z_tab))
        b = b.cut(cyl_z(INS / 2, ZT - 1, ZT + C.INSERT_DEPTH, dx, sgn * yf))
    return safe_clean(b)


def print_bracket(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)       # lying on its side (the profile face)


def pan_bracket_bosses():
    """Bosses with horizontal inserts inside the pan's sump walls for the 4 brackets (fused into the pan)."""
    out = []
    for x, sgn in bracket_positions():
        yw = sgn * SY1
        for dx in (-8.0, 8.0):
            boss = cyl_y(4.5, min(yw - sgn * (P["wall"] - 0.1), yw - sgn * 9.0), max(yw - sgn * (P["wall"] - 0.1), yw - sgn * 9.0),
                         x + dx, ST["bracket_tab_z"])
            hole = cyl_y(INS / 2, min(yw + sgn * 1, yw - sgn * (C.INSERT_DEPTH + 0.5)), max(yw + sgn * 1, yw - sgn * (C.INSERT_DEPTH + 0.5)),
                         x + dx, ST["bracket_tab_z"])
            out.append((boss, hole))
    return out


def stand_plate():
    pl = _rbox(X0, X1, Y0, Y1, ZB, ZT, 8.0)
    pl = cq.Workplane().add(pl).faces(">Z").edges().chamfer(ST["chamfer"]).val()
    # cut-out under the pan floor panel
    cw, cd = ST["cutout"]
    pl = pl.cut(_rbox(-cw / 2, cw / 2, -cd / 2, cd / 2, ZB - 1, ZT + 1, 6.0))
    # bracket screws from below (counterbored)
    for x, sgn in bracket_positions():
        for dx in (-8.0, 8.0):
            pl = pl.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, ZB - 1, ZT + 1, x + dx, sgn * ST["foot_y"]))
            pl = pl.cut(cyl_z(C.hole(C.M3_CBORE) / 2, ZB - 1, ZB + ST["t"] - C.SCREW_FLOOR, x + dx, sgn * ST["foot_y"]))
    # rubber feet rings (20 mm adhesive feet), 4 corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = XC + sx * (ST["l"] / 2 - ST["feet_inset"])
            y = sy * (ST["w"] / 2 - ST["feet_inset"])
            pl = pl.cut(cyl_z(ST["feet_d"] / 2 + 0.5, ZB - 1, ZB + 0.4, x, y).cut(cyl_z(ST["feet_d"] / 2 - 0.3, ZB - 2, ZB + 1, x, y)))
    # wiring channel on the underside: from under the plinth to the cut-out, with cable-tie slots
    ch_w, ch_d = ST["channel_w"], ST["channel_d"]
    yc = (PL["y"][0] + PL["y"][1]) / 2
    pl = pl.cut(box(-cw / 2 - 1, PL["x0"] + PL["depth"] / 2, yc - ch_w / 2, yc + ch_w / 2, ZB - 1, ZB + ch_d))
    pl = pl.cut(box(PL["x0"] + PL["depth"] / 2 - ch_w / 2, PL["x0"] + PL["depth"] / 2 + ch_w / 2, yc - ch_w / 2, yc + ch_w / 2, ZB - 1, ZT + 1))   # up into the plinth
    for dx in (-30.0, 30.0):                                   # cable-tie slots either side of the channel
        for sy in (-1, 1):
            ya, yb = sorted((yc + sy * (ch_w / 2 + 2), yc + sy * (ch_w / 2 + 6)))
            pl = pl.cut(box(dx - 1.5, dx + 1.5, ya, yb, ZB - 1, ZB + ch_d + 2))
    # edition plate recess on the front edge face (floor = plate + clearance, 45 deg bevel out)
    e = C.EDITION_PLATE
    zc = (ZT + ZB) / 2
    sk = cq.Sketch().rect(e["w"] + 2 * e["clear"], e["h"] + 2 * e["clear"]).vertices().fillet(e["r"] + e["clear"])
    rec = (cq.Workplane("YZ", origin=(X1 - e["depth"], EDITION_Y, zc)).placeSketch(sk).extrude(e["depth"] + 0.5, taper=-45).val())
    pl = pl.cut(rec)
    return safe_clean(pl)


def print_plate(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)       # top face down? no: chamfered top up, flat bottom on the bed
    

def edition_plate(number=1):
    e = C.EDITION_PLATE
    zc = (ZT + ZB) / 2
    x0 = X1 - e["depth"] + e["tape"]
    sk = cq.Sketch().rect(e["w"], e["h"]).vertices().fillet(e["r"])
    plate = cq.Workplane("YZ", origin=(x0, EDITION_Y, zc)).placeSketch(sk).extrude(e["t"]).val()
    face = x0 + e["t"]
    order = "-".join(str(c) for c in C.FIRING_ORDER)
    for text, size, dz in (("358 ci  V8  -  90 DEG  CROSS-PLANE", 5.0, 5.5), (f"{order}      No. {number:02d} / 50", 3.6, -6.0)):
        pl = cq.Plane(origin=(face - 0.12, EDITION_Y, zc + dz), xDir=(0, 1, 0), normal=(1, 0, 0))
        plate = plate.cut(cq.Workplane(pl).text(text, size, 0.5, halign="center", valign="center", kind="bold").val())
    return plate


def plinth():
    x0, x1 = PL["x0"], PL["x0"] + PL["depth"]
    y0, y1 = PL["y"]
    z0, z1 = ZT, ZT + PL["h"]
    bx = _rbox(x0, x1, y0, y1, z0, z1, 4.0)
    bx = cq.Workplane().add(bx).faces(">Z").edges().chamfer(1.5).val()
    w = PL["wall"]
    bx = bx.cut(_rbox(x0 + w, x1 - PL["face_t"], y0 + w, y1 - w, z0 - 1, z1 - w, 2.0))      # hollow; thin front face for the controls
    zc = ZT + PL["controls_z"]
    sizes = dict(C.CONTROLS and [(c[0], (c[2], c[3])) for c in C.CONTROLS])
    for name, y in PL["controls"]:
        _, d = sizes[name]
        bx = bx.cut(cyl_x(d / 2 + C.HOLE_COMP / 2, x1 - PL["face_t"] - 1, x1 + 1, y, zc))
        if name == "speed":
            bx = bx.cut(cyl_x(C.POT_TAB["d"] / 2, x1 - PL["face_t"] - 1, x1 + 1, y + C.POT_TAB["dy"], zc))
        label = {"dc_jack": "12V DC", "power": "POWER", "speed": "SPEED", "start": "START"}[name]
        pl = cq.Plane(origin=(x1 - 0.5, y, zc - 13.0), xDir=(0, -1, 0), normal=(1, 0, 0))
        bx = bx.cut(cq.Workplane(pl).text(label, 3.6, 0.8, halign="center", valign="center", kind="bold").val())
    # wiring exit down through the floor into the plate channel (the plate has the matching hole)
    yc = (y0 + y1) / 2
    bx = bx.cut(box((x0 + x1) / 2 - ST["channel_w"] / 2, (x0 + x1) / 2 + ST["channel_w"] / 2, yc - ST["channel_w"] / 2, yc + ST["channel_w"] / 2, z0 - 1, z0 + w + 1))
    return safe_clean(bx)


def print_plinth(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)       # open bottom up: top face on the bed


def build_all():
    return {"stand_plate": stand_plate(), "bracket": bracket(1), "bracket_m": bracket(-1), "plinth": plinth(),
            "edition_plate": edition_plate()}


def placed(lib):
    out = [("stand_plate", lib["stand_plate"], "carbon"), ("plinth", lib["plinth"], "carbon"),
           ("edition_plate", lib["edition_plate"], "steel")]
    for x, sgn in bracket_positions():
        out.append((f"bracket_{'R' if sgn < 0 else 'L'}{x:+.0f}", (lib["bracket"] if sgn > 0 else lib["bracket_m"]).translate((x, 0, 0)), "carbon"))
    return out
