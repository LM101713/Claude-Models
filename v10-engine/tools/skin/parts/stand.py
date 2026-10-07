"""46 stand plate, 48 controls plinth, 49 edition plate (the 47 brackets became cast legs on the pan, D60) -
as cad/stand_v8.py from params.json. Engine frame, +X = front."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P


def _d():
    ST, PL = P.STAND, P.PLINTH
    XC = ST["x_offset"]
    d = dict(ST=ST, PL=PL, XC=XC, X0=XC - ST["l"] / 2, X1=XC + ST["l"] / 2, Y0=-ST["w"] / 2, Y1=ST["w"] / 2, ZT=ST["z_top"])
    d["ZB"] = d["ZT"] - ST["t"]
    d["SY1"] = P.PAN["w_sump"] / 2
    return d


def _rbox(name, x0, x1, y0, y1, z0, z1, r):
    return U.rrect_prism(name, (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, r, z0, z1)


def leg_positions():
    """Where the pan's cast saddle legs meet the plate (D60): one screw per leg, from below."""
    return [(x, sgn) for x in P.STAND["bracket_x"] for sgn in (-1, 1)]


def stand_plate():
    d = _d()
    ST, PL, XC, X0, X1, Y0, Y1, ZT, ZB = d["ST"], d["PL"], d["XC"], d["X0"], d["X1"], d["Y0"], d["Y1"], d["ZT"], d["ZB"]
    pl = _rbox("46_stand_plate", X0, X1, Y0, Y1, ZB, ZT, 8.0)
    U.bevel_edges(pl, ST["chamfer"], 1, lambda c, dd: abs(c.z - ZT) < 0.2 and abs(dd.z) < 0.1)
    cw, cd = ST["cutout"]
    U.boolean(pl, _rbox("cutout", -cw / 2, cw / 2, -cd / 2, cd / 2, ZB - 1, ZT + 1, 6.0))
    for x, sgn in leg_positions():
        U.boolean(pl, U.cylinder("leg_clear", P.hole["M3_CLEAR"] / 2, ZB - 1, ZT + 1, x, sgn * ST["foot_y"]))
        U.boolean(pl, U.cylinder("leg_cbore", P.hole["M3_CBORE"] / 2, ZB - 1, ZB + ST["t"] - P.SCREW_FLOOR, x, sgn * ST["foot_y"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = XC + sx * (ST["l"] / 2 - ST["feet_inset"])
            y = sy * (ST["w"] / 2 - ST["feet_inset"])
            ring = U.cylinder("foot_ring", ST["feet_d"] / 2 + 0.5, ZB - 1, ZB + 0.4, x, y)
            U.boolean(ring, U.cylinder("foot_ring_in", ST["feet_d"] / 2 - 0.3, ZB - 2, ZB + 1, x, y))
            U.boolean(pl, ring)
    ch_w, ch_d = ST["channel_w"], ST["channel_d"]
    yc = (PL["y"][0] + PL["y"][1]) / 2
    xm = PL["x0"] + PL["depth"] / 2
    U.boolean(pl, U.box("channel", -cw / 2 - 1, xm, yc - ch_w / 2, yc + ch_w / 2, ZB - 1, ZB + ch_d))
    U.boolean(pl, U.box("channel_up", xm - ch_w / 2, xm + ch_w / 2, yc - ch_w / 2, yc + ch_w / 2, ZB - 1, ZT + 1))
    for dx in (-30.0, 30.0):
        for sy in (-1, 1):
            ya, yb = sorted((yc + sy * (ch_w / 2 + 2), yc + sy * (ch_w / 2 + 6)))
            U.boolean(pl, U.box("tie_slot", dx - 1.5, dx + 1.5, ya, yb, ZB - 1, ZB + ch_d + 2))
    # edition plate recess on the front edge: floor at X1 - depth, 45 deg flare outwards
    e = P.EDITION_PLATE
    zc = (ZT + ZB) / 2
    w0, h0, r0 = e["w"] + 2 * e["clear"], e["h"] + 2 * e["clear"], e["r"] + e["clear"]
    x_floor, x_out = X1 - e["depth"], X1 + 0.5
    grow = (x_out - x_floor)
    ring0 = [(x_floor, P.edition_y + u, zc + v) for u, v, _ in U.rrect_ring(0, 0, w0, h0, r0, 0)]
    ring1 = [(x_out, P.edition_y + u, zc + v) for u, v, _ in U.rrect_ring(0, 0, w0 + 2 * grow, h0 + 2 * grow, r0 + grow, 0)]
    U.boolean(pl, U.loft("edition_recess", [ring0, ring1]))
    U.shade(pl)
    return pl


def edition_plate(number=1):
    d = _d()
    X1, ZT, ZB = d["X1"], d["ZT"], d["ZB"]
    e = P.EDITION_PLATE
    zc = (ZT + ZB) / 2
    x0 = X1 - e["depth"] + e["tape"]
    ring_a = [(x0, P.edition_y + u, zc + v) for u, v, _ in U.rrect_ring(0, 0, e["w"], e["h"], e["r"], 0)]
    ring_b = [(x0 + e["t"], P.edition_y + u, zc + v) for u, v, _ in U.rrect_ring(0, 0, e["w"], e["h"], e["r"], 0)]
    plate = U.loft("49_edition_plate", [ring_a, ring_b])
    face = x0 + e["t"]
    for text, size, dz in P.edition_texts:
        tm = U.text_mesh("edition_text", text.format(number=number), size, 0.5 * 2)
        # text drawn in XY (+X right, +Y up) -> plate face: right = +Y, up = +Z, normal +X
        U.rot(tm, 'Z', 90)          # +X -> +Y
        U.rot(tm, 'X', 90)          # +Y(up) -> +Z
        U.move(tm, face - 0.12 + 0.5, P.edition_y, zc + dz)
        U.boolean(plate, tm)
    U.shade(plate)
    return plate


def plinth():
    d = _d()
    ST, PL, ZT = d["ST"], d["PL"], d["ZT"]
    x0, x1 = PL["x0"], PL["x0"] + PL["depth"]
    y0, y1 = PL["y"]
    z0, z1 = ZT, ZT + PL["h"]
    bx = _rbox("48_controls_plinth", x0, x1, y0, y1, z0, z1, 8.0)
    U.bevel_edges(bx, ST["chamfer"], 2, lambda c, dd: abs(c.z - z1) < 0.2 and abs(dd.z) < 0.1)   # round 5: same chamfer as the stand
    # round 5: panel line (1 mm groove, 0.8 deep) framing the control face, 2.5 mm in from the edges
    # (4 mm clipped the rim of the 20 mm power-switch hole: fit deviation 0.04 mm)
    frame = _rbox("panel_line", x1 - 0.8, x1 + 1, y0 + 2.5, y1 - 2.5, z0 + 2.5, z1 - 2.5, 2.5)
    U.boolean(frame, _rbox("panel_line_in", x1 - 2, x1 + 2, y0 + 3.5, y1 - 3.5, z0 + 3.5, z1 - 3.5, 1.5))
    U.boolean(bx, frame)
    w = PL["wall"]
    U.boolean(bx, _rbox("plinth_in", x0 + w, x1 - PL["face_t"], y0 + w, y1 - w, z0 - 1, z1 - w, 2.0))
    zc = ZT + PL["controls_z"]
    sizes = {c[0]: c[3] for c in P.CONTROLS}
    for name, y in PL["controls"]:
        dia = sizes[name]
        U.boolean(bx, U.cylinder("ctl_hole", dia / 2 + P.HOLE_COMP / 2, x1 - PL["face_t"] - 1, x1 + 1, y, zc, "X"))
        if name == "speed":
            U.boolean(bx, U.cylinder("pot_tab", P.POT_TAB["d"] / 2, x1 - PL["face_t"] - 1, x1 + 1, y + P.POT_TAB["dy"], zc, "X"))
        tm = U.text_mesh("label", P.plinth_labels[name], 3.6, 0.8 * 2)
        U.rot(tm, 'Z', -90)         # +X -> -Y (viewer at +X reads left-to-right towards -Y)
        U.rot(tm, 'X', 90)
        U.move(tm, x1 - 0.5 + 0.8, y, zc - 13.0)
        U.boolean(bx, tm)
    yc = (y0 + y1) / 2
    xm = (x0 + x1) / 2
    U.boolean(bx, U.box("wire_exit", xm - ST["channel_w"] / 2, xm + ST["channel_w"] / 2, yc - ST["channel_w"] / 2, yc + ST["channel_w"] / 2, z0 - 1, z0 + w + 1))
    U.shade(bx)
    return bx


def build_all():
    return {"stand_plate": stand_plate(), "plinth": plinth(), "edition_plate": edition_plate()}


def placed(lib):
    return [("stand_plate", U.copy(lib["stand_plate"], "stand_plate")), ("plinth", U.copy(lib["plinth"], "plinth")),
            ("edition_plate", U.copy(lib["edition_plate"], "edition_plate"))]
