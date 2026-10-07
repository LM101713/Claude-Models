"""40 oil pan (motor + electronics bay), 41 floor panel, 42 bellhousing -
functional geometry as cad/pan_v8.py, from params.json, with the cast look:
rounded corners, chamfered sump, horizontal ribs, gasket flange."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P

S45 = math.sqrt(0.5)


def _d():
    PAN = P.PAN
    X0, X1 = -P.END_PLATE_OUTER_X, P.END_PLATE_OUTER_X
    d = dict(PAN=PAN, X0=X0, X1=X1, Y0=-PAN["w"] / 2, Y1=PAN["w"] / 2, SY0=-PAN["w_sump"] / 2, SY1=PAN["w_sump"] / 2,
             ZT=P.CASE_FLOOR_Z, ZB=PAN["z_bot"], ZSTEP=PAN["z_step"], W=PAN["wall"], RW=P.MOTOR_PLATE_T)
    d["ZS"] = d["ZT"] - PAN["skin"]
    d["ZF"] = d["ZB"] + PAN["floor"]
    d["IX0"], d["IX1"], d["IY0"], d["IY1"] = P.pan_interior
    d["PX0"], d["PX1"], d["PY0"], d["PY1"] = P.pan_opening
    d["RX0"], d["RX1"], d["RY0"], d["RY1"] = P.pan_rabbet
    return d


def _rbox(name, x0, x1, y0, y1, z0, z1, r):
    return U.rrect_prism(name, (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, r, z0, z1)


def oil_pan():
    d = _d()
    PAN, X0, X1, Y0, Y1, SY0, SY1 = d["PAN"], d["X0"], d["X1"], d["Y0"], d["Y1"], d["SY0"], d["SY1"]
    ZT, ZB, ZSTEP, W, RW, ZS, ZF = d["ZT"], d["ZB"], d["ZSTEP"], d["W"], d["RW"], d["ZS"], d["ZF"]
    IX0, IX1, IY0, IY1 = d["IX0"], d["IX1"], d["IY0"], d["IY1"]
    pan = _rbox("40_oil_pan", X0, X1, Y0, Y1, ZSTEP - 0.1, ZT, PAN["r"])
    sump = _rbox("sump", X0, X1, SY0, SY1, ZB, ZSTEP + 6.0, PAN["r"])
    U.bevel_edges(sump, PAN["bottom_chamfer"], 1, lambda c, dd: abs(c.z - ZB) < 0.3 and abs(dd.z) < 0.1)
    U.boolean(pan, sump, "UNION")
    for sgn in (-1, 1):                         # 45 deg under-cut rail -> sump
        yw, ys = (Y1, SY1) if sgn > 0 else (Y0, SY0)
        dd = abs(yw - ys)
        # ends 1 mm short of the corner arcs and the inner vertex 0.2 mm inside the sump wall: no surfaces coincide
        U.boolean(pan, U.prism("wedge", [(ys - sgn * 0.2, ZSTEP + 0.1), (yw, ZSTEP + 0.1), (ys - sgn * 0.2, ZSTEP - dd)], X0 + PAN["r"] + 1.0, X1 - PAN["r"] - 1.0), "UNION")
    fo, fh = PAN["flange_out"], PAN["flange_h"]
    for sgn in (-1, 1):
        yw = Y1 if sgn > 0 else Y0
        fl = U.box("flange", X0 + 8, X1 - 8, min(yw - sgn * 0.2, yw + sgn * fo), max(yw - sgn * 0.2, yw + sgn * fo), ZT - fh, ZT)
        U.bevel_edges(fl, 2.0, 1, lambda c, dd: abs(dd.y) > 0.9)
        U.boolean(pan, fl, "UNION")
        ys = SY1 if sgn > 0 else SY0
        for z in PAN["rib_z"]:
            rib = U.box("rib", X0 + 14, X1 - 14, min(ys - sgn * 0.3, ys + sgn * PAN["rib_out"]), max(ys - sgn * 0.3, ys + sgn * PAN["rib_out"]),
                        z - PAN["rib_h"] / 2, z + PAN["rib_h"] / 2)
            yo = ys + sgn * PAN["rib_out"]
            U.bevel_edges(rib, PAN["rib_out"] * 0.7, 1, lambda c, dd: abs(dd.x) > 0.9 and abs(c.z - (z + PAN["rib_h"] / 2)) < 0.2 and abs(c.y - yo) < 0.2)
            for xb in P.STAND["bracket_x"]:
                U.boolean(rib, U.box("rib_gap", xb - P.STAND["bracket_w"] / 2 - 3.0, xb + P.STAND["bracket_w"] / 2 + 3.0, Y0 - 10, Y1 + 10, ZB - 1, ZT + 1))
            U.boolean(pan, rib, "UNION")
    # interior
    U.boolean(pan, _rbox("int_rail", IX0, IX1, Y0 + W, Y1 - W, ZSTEP + W, ZS, max(1.0, PAN["r"] - W)))
    ri = max(1.0, PAN["r"] - W)
    PX0, PX1, PY0, PY1 = d["PX0"], d["PX1"], d["PY0"], d["PY1"]
    led = PAN["ledge"]
    U.boolean(pan, _rbox("int_sump", IX0, IX1, IY0, IY1, ZF, ZS, ri))
    for sgn in (-1, 1):
        yw, ys = (Y1 - W, SY1 - W) if sgn > 0 else (Y0 + W, SY0 + W)
        dd = abs(yw - ys)
        ri = max(1.0, PAN["r"] - W)
        U.boolean(pan, U.prism("int_wedge", [(ys - sgn * 0.2, ZSTEP + W + 0.1), (yw, ZSTEP + W + 0.1), (ys - sgn * 0.2, ZSTEP + W - dd)], IX0 + ri + 1.0, IX1 - ri - 1.0))
    RX0, RX1, RY0, RY1 = d["RX0"], d["RX1"], d["RY0"], d["RY1"]
    c = P.CLEARANCE
    U.boolean(pan, _rbox("floor_open", PX0, PX1, PY0, PY1, ZB - 1, ZF + 1, 3.0))
    U.boolean(pan, _rbox("rabbet", RX0 - c, RX1 + c, RY0 - c, RY1 + c, ZB - 1, ZB + PAN["panel_t"], 3.0 + c))
    # 45 deg fillets along the long sides of the floor ledge: skin-down the ledge top is otherwise an 11 mm ceiling.
    # Long sides only - the motor's tension travel runs down to z -93 at the front wall (differs from the frozen CAD pan)
    for sgn in (-1, 1):
        yl, yw_ = sgn * d["PY1"], sgn * (IY1 + 0.01)
        U.boolean(pan, U.prism("ledge_fillet", [(yl, ZF - 0.01), (yw_, ZF - 0.01), (yw_, ZF + led)], d["PX0"] + 3.0, d["PX1"] - 3.0), "UNION")
    for x, y in P.pan_panel_screws:                                   # panel screw pillars + inserts
        U.boolean(pan, U.cylinder("pillar", 4.5, ZF - 0.3, ZS + 0.1, x, y), "UNION")
        U.boolean(pan, U.cylinder("pillar_ins", P.insert_hole / 2, ZB + PAN["panel_t"] - 0.5, ZF + 8.0 - 2.0, x, y))
    for x, y in P.PAN_SCREWS:                                         # up into the crankcase, heads inside
        U.boolean(pan, U.cylinder("pan_screw", P.hole["M3_CLEAR"] / 2, ZS - 1, ZT + 1, x, y))
        U.boolean(pan, U.cylinder("pan_cbore", P.hole["M3_CBORE"] / 2, ZS - 1, ZT - 2.5, x, y))
    hs = P.HALL_LEAD_SLOT
    hx = P.HALL_X + hs["dx"]
    U.boolean(pan, U.box("hall_slot", hx - hs["l"] / 2, hx + hs["l"] / 2, -hs["w"] / 2, hs["w"] / 2, ZS - 1, ZT + 1))
    # stand bracket bosses with horizontal inserts inside the sump walls
    ST = P.STAND
    for xb in ST["bracket_x"]:
        for sgn in (-1, 1):
            yw = sgn * SY1
            for dx in (-8.0, 8.0):
                ya, yb = sorted((yw - sgn * (W - 0.1), yw - sgn * 9.0))
                U.boolean(pan, U.cylinder("br_boss", 4.5, ya, yb, xb + dx, ST["bracket_tab_z"], "Y"), "UNION")
                ya, yb = sorted((yw + sgn * 1, yw - sgn * (P.INSERT_DEPTH + 0.5)))
                U.boolean(pan, U.cylinder("br_ins", P.insert_hole / 2, ya, yb, xb + dx, ST["bracket_tab_z"], "Y"))
    h = P.HARNESS_HOLE
    U.boolean(pan, U.cylinder("harness", h["d"] / 2, X0 - 1, IX0 + 1, h["y"], h["z"], "X"))
    # front wall = motor bulkhead: boss slot (pointed bottom) + 4 bolt slots
    za, zb = P.MOTOR_SLOT_BOTTOM, P.MOTOR_SLOT_TOP
    xa, xb = P.MOTOR_FACE_X - 1, X1 + 1

    def slot(name, r, y, dz=0.0):
        s = U.cylinder(name, r, xa, xb, y, za + dz, "X")
        U.boolean(s, U.cylinder(name + "_b", r, xa, xb, y, zb + dz, "X"), "UNION")
        U.boolean(s, U.box(name + "_c", xa, xb, y - r, y + r, za + dz, zb + dz), "UNION")
        return s
    rb = P.MOTOR["boss_d"] / 2 + P.MOTOR_BOSS_SLOT_CLEAR
    U.boolean(pan, slot("boss_slot", rb, 0.0))
    U.boolean(pan, U.prism("boss_arch", [(-rb * S45, za - rb * S45), (0.0, za - rb / S45), (rb * S45, za - rb * S45)], xa, xb))
    hp = P.MOTOR["hole_pitch"] / 2
    for dy in (-hp, hp):
        for dz in (-hp, hp):
            U.boolean(pan, slot("bolt_slot", P.hole["M3_CLEAR"] / 2, dy, dz))
    U.shade(pan)
    return pan


def floor_panel():
    d = _d()
    PAN, ZB = d["PAN"], d["ZB"]
    RX0, RX1, RY0, RY1 = d["RX0"], d["RX1"], d["RY0"], d["RY1"]
    p = _rbox("41_pan_floor_panel", RX0, RX1, RY0, RY1, ZB, ZB + PAN["panel_t"], 3.0)
    for x, y in P.pan_panel_screws:
        U.boolean(p, U.cylinder("cap_clear", P.hole["M3_CLEAR"] / 2, ZB - 1, ZB + PAN["panel_t"] - P.CAPTIVE_LIP_T, x, y))
        U.boolean(p, U.cylinder("cap_lip", P.CAPTIVE_LIP_D / 2, ZB - 1, ZB + PAN["panel_t"] + 1, x, y))
    b = P.PCB
    for x, y in P.pan_board_holes:
        U.boolean(p, U.cylinder("standoff", 4.0, ZB + PAN["panel_t"] - 0.1, ZB + PAN["panel_t"] + b["standoff"], x, y), "UNION")
        U.boolean(p, U.cylinder("standoff_ins", P.insert_hole / 2, ZB + 1.0, ZB + PAN["panel_t"] + b["standoff"] + 0.1, x, y))
    for i in range(8):
        x = P.MOTOR_FACE_X - 36 + i * 4.5
        for yc in (-20.0, 20.0):
            U.boolean(p, U.box("vent", x - 1.2, x + 1.2, yc - 12, yc + 12, ZB - 1, ZB + PAN["panel_t"] + 1))
    U.shade(p)
    return p


def electronics_envelope():
    """Board + component stack (for the STL interference check), as cad/pan_v8.electronics_envelopes."""
    d = _d()
    b = P.PCB
    cx, cy = P.pan_board_centre
    z0 = d["ZB"] + d["PAN"]["panel_t"] + b["standoff"]
    env = U.box("elec_board", cx - b["w"] / 2, cx + b["w"] / 2, cy - b["h"] / 2, cy + b["h"] / 2, z0, z0 + 1.6)
    U.boolean(env, U.box("elec_parts", cx - b["w"] / 2 + 6, cx + b["w"] / 2 - 6, cy - b["h"] / 2 + 4, cy + b["h"] / 2 - 4, z0 + 1.6, z0 + 1.6 + P.board_stack), "UNION")
    return env


def _bell_outline(name, off, x0, x1):
    b = P.BELL
    r, hw, zb = b["r_top"] - off, b["half_w_bot"] - off, b["z_bot"] + off
    dist = math.hypot(hw, zb)
    ang_c, ang_t = math.atan2(zb, hw), math.acos(r / dist)
    t_right = ang_c + ang_t
    pts = [(hw, zb)]
    n = 64
    a0, a1 = t_right, math.pi - t_right
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    pts.append((-hw, zb))
    return U.prism(name, pts, x0, x1)


def bellhousing():
    b = P.BELL
    x1 = -P.END_PLATE_OUTER_X
    x0 = x1 - b["depth"]
    bell = _bell_outline("42_bellhousing", 0.0, x0, x1)
    U.bevel_edges(bell, 2.5, 3, lambda c, dd: abs(c.x - x0) < 0.3 and abs(dd.x) < 0.1)
    U.boolean(bell, _bell_outline("bell_in", b["wall"], x0 + b["wall"], x1 + 1))
    ring = U.cylinder("hub_ring", b["hub_r"], x0 - 1, x0 + 1.5, 0, 0, "X")
    U.boolean(ring, U.cylinder("hub_ring_in", b["hub_r"] - 2.5, x0 - 2, x0 + 2, 0, 0, "X"))
    U.boolean(bell, ring)
    for i in range(b["n_bolts"]):
        a = math.radians(i * 360.0 / b["n_bolts"] + 22.5)
        y, z = b["bolt_r"] * math.cos(a), b["bolt_r"] * math.sin(a)
        if z > b["z_bot"] + 6:
            U.boolean(bell, U.cylinder("bell_bolt", 2.2, x0 - 1, x0 + 1.5, y, z, "X"))
    # cast detail on the outer skin (faces outward / up when the bell prints rear face down):
    # a rib band at mid depth and six bosses with recessed hex pockets in the rear face
    band = _bell_outline("bell_band", -1.5, x0 + 9.0, x0 + 12.5)
    U.boolean(band, _bell_outline("bell_band_in", 0.01, x0 + 8.0, x0 + 14.0))
    U.bevel_edges(band, 0.8, 2, lambda c, dd: abs(dd.x) < 0.1)
    U.boolean(bell, band, "UNION")
    for i in range(6):
        a = math.radians(30.0 + 24.0 * i)
        y, z = (b["r_top"] - 1.0) * math.cos(a), (b["r_top"] - 1.0) * math.sin(a)
        boss = U.cylinder("bell_boss", 4.0, x0 + 0.5, x1 - 3.0, y, z, "X")
        U.boolean(bell, boss, "UNION")
        U.boolean(bell, U.cylinder("bell_boss_hex", 2.2, x0 - 1, x0 + 2.0, y, z, "X", segs=6))
    outer = _bell_outline("bell_outer", 0.0, x0, x1)
    for y, z in P.COVER_MAGNETS:
        y = -y
        pil = U.cylinder("pillar", P.COVER_PILLAR_R, x0 + b["wall"] - 0.1, x1, y, z, "X")
        web = U.box("web", x0 + b["wall"] - 0.1, x1, -P.COVER_PILLAR_R, P.COVER_PILLAR_R, 0, 8)
        U.rot(web, 'X', -math.degrees(math.atan2(y, z)))
        U.move(web, 0, y, z)
        U.boolean(pil, web, "UNION")
        U.boolean(pil, U.copy(outer, "outer_copy"), "INTERSECT")
        U.boolean(bell, pil, "UNION")
        F.cut_magnet(bell, x1, -1, y, z, axis="X")
    U.delete(outer)
    U.shade(bell)
    return bell


def build_all():
    return {"pan": oil_pan(), "panel": floor_panel(), "bellhousing": bellhousing()}


def placed(lib):
    return [("pan", U.copy(lib["pan"], "pan")), ("pan_panel", U.copy(lib["panel"], "pan_panel")),
            ("bellhousing", U.copy(lib["bellhousing"], "bellhousing"))]
