"""30 cylinder head, 31 valve cover, 31B oil cap, 32 plug boot, 34 header
flange plate - bank-local frame (as cad/exterior_v8.py), functional
features at the JSON positions, cast / crisp detail on the visible faces."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P


def _dims():
    DECK = P.DECK_DIST
    return dict(DECK=DECK, TOP=DECK + P.HEAD_H, X0=P.BLOCK_X_MIN, X1=P.BLOCK_X_MAX, YO=P.BLOCK_Y_OUT, YV=P.BLOCK_Y_VALLEY,
                PORT_Z=DECK + P.EXH_PORT_Z, BOOT_Z=DECK + P.PLUG_BOOT["z"], BOOT_X=[x + P.PLUG_BOOT["dx"] for x in P.BANK_A_CYL_X],
                FP=P.EXH_FLANGE_PLATE)


def plate_screw_xz():
    d = _dims()
    fp = d["FP"]
    xs = (d["X0"] + fp["end_inset"] + P.HEADER_SCREW_X_INSET, d["X1"] - fp["end_inset"] - P.HEADER_SCREW_X_INSET)
    return [(x, d["DECK"] + fp["z1"] - 5.0) for x in xs]


def cylinder_head():
    d = _dims()
    DECK, TOP, X0, X1, YO, YV = d["DECK"], d["TOP"], d["X0"], d["X1"], d["YO"], d["YV"]
    head = U.box("30_cylinder_head", X0, X1, YO, YV, DECK, TOP)
    U.bevel_edges(head, 3.0, 4, lambda c, dd: abs(dd.z) > 0.9)                       # cast vertical corners
    U.bevel_edges(head, 2.0, 3, lambda c, dd: abs(dd.x) > 0.9 and abs(c.z - TOP) < 0.3)   # top long edges
    U.bevel_edges(head, 1.2, 2, lambda c, dd: abs(dd.x) > 0.9 and abs(c.z - DECK) < 0.3)  # parting line at the deck
    # end faces (what you see of the head behind the damper and the bellhousing): a raised, chamfered cast
    # pad with a bolted cover plate look (round-1 critique: the ends were blank slabs), plus the 2 bosses.
    # The head prints deck down, so the end faces are vertical in print and raised detail is fine.
    for xe, sgn in ((X0, 1), (X1, -1)):
        pad = U.box("end_pad", min(xe - sgn * 0.3, xe - sgn * 1.5), max(xe - sgn * 0.3, xe - sgn * 1.5), YO + 7.0, YV - 7.0, DECK + 5.0, TOP - 7.0)
        U.bevel_edges(pad, 1.0, 2, lambda c, dd: abs(c.x - (xe - sgn * 1.5)) < 0.2)
        U.boolean(head, pad, "UNION")
        for yb in (YO + 11.0, YV - 11.0):
            for zb in (DECK + 9.0, TOP - 11.0):
                b = U.cylinder("end_bolt", 2.0, min(xe - sgn * 1.4, xe - sgn * 2.8), max(xe - sgn * 1.4, xe - sgn * 2.8), yb, zb, "X", segs=6)
                U.boolean(head, b, "UNION")
        for yb in (-18.0, 24.0):
            boss = U.cylinder("end_boss", 6.0, min(xe - sgn * 0.3, xe + sgn * 1.6), max(xe - sgn * 0.3, xe + sgn * 1.6), yb, DECK + 14.0, "X")
            U.boolean(head, boss, "UNION")
            U.boolean(head, U.cylinder("end_boss_hex", 2.4, min(xe - sgn * 1.0, xe + sgn * 1.8), max(xe - sgn * 1.0, xe + sgn * 1.8), yb, DECK + 14.0, "X", segs=6))
    # valve-cover seat (1 mm recess) + 4 magnets
    vc = P.VC
    seat = U.rrect_prism("vc_seat", (X0 + X1) / 2, (vc["y0"] + vc["y1"]) / 2, (X1 - X0) - 2 * vc["x_inset"] + 2 * P.CLEARANCE,
                         vc["y1"] - vc["y0"] + 2 * P.CLEARANCE, vc["r"] + P.CLEARANCE, TOP - 1.0, TOP + 1)
    U.boolean(head, seat)
    bx = P.bank_between_x
    for xc in (P.BANK_A_CYL_X[0], P.BANK_A_CYL_X[-1], bx[0], bx[-1]):
        F.cut_magnet(head, TOP - 1.0, -1, xc, P.VC_MAGNET_Y)
    for xc in bx:
        for yc in P.HEAD_SCREW_Y:
            U.boolean(head, F.screw_cbore("head_screw", DECK, TOP, P.SCREW_FLOOR, xc, yc))
    gw, gd, ew = P.LED_GROOVE["w"], P.LED_GROOVE["d"], P.LED_GROOVE["end_wall"]
    U.boolean(head, U.box("led_groove", X0 + ew, X1 - ew, -gw / 2, gw / 2, DECK - 1, DECK + gd))
    ww, wd = P.LED_WIRE_GROOVE["w"], P.LED_WIRE_GROOVE["d"]
    for xa in (X0 + ew, X1 - ew - ww):
        U.boolean(head, U.box("led_lead", xa, xa + ww, -gw / 2, YV + 1, DECK - 1, DECK + wd))
    it = P.INTAKE
    for xc in P.BANK_A_CYL_X:
        for yv in P.HEAD_VALVE_Y:
            U.boolean(head, U.cylinder("valve", P.HEAD_VALVE_R, DECK - 1, DECK + 0.4, xc, yv))
        rz1 = DECK + P.RAIL_HEAD_ENGAGE + P.RAIL_POCKET_EXTRA
        F.cut_crush(head, "rail_3", DECK - 0.01, rz1, xc, P.RAIL_OFFSET, entry="lo")
        # exhaust port: counterbore + 14 mm crush socket (no raised ring: the flange plate covers the port face)
        # +CLEARANCE on the counterbore: the pipe is EXH_PORT_D too (the CAD head is line-to-line here)
        U.boolean(head, U.cylinder("port_cbore", P.EXH_PORT_D / 2 + P.CLEARANCE, YO - 2.0, YO + P.EXH_PORT_DEPTH, xc, d["PORT_Z"], "Y"))
        F.cut_crush(head, "trumpet_14", YO - 0.01, YO + P.EXH_SPIGOT_L + P.EXH_PORT_DEPTH + 0.5, xc, d["PORT_Z"], "Y", entry="lo")
        pocket = U.rrect_prism("runner_pocket", 0, 0, it["runner_w"] + 2 * P.RUNNER_POCKET_CLEAR, it["runner_h"] + 2 * P.RUNNER_POCKET_CLEAR,
                               it["runner_r"], -it["port_depth"], 1.0)
        U.rot(pocket, 'X', -90)
        U.move(pocket, xc, YV - 0.01, DECK + it["port_z"])
        U.boolean(head, pocket)
    bs, pb = P.BOOT_STRIP, P.PLUG_BOOT
    U.boolean(head, U.box("boot_strip", X0 + 6, X1 - 6, YO - 1, YO + bs["d"], d["BOOT_Z"] - bs["w"] / 2, d["BOOT_Z"] + bs["w"] / 2))
    for xb in d["BOOT_X"]:
        F.cut_crush(head, "boot_9", YO - 0.01, YO + pb["shaft_l"] + bs["d"] + 0.5, xb, d["BOOT_Z"], "Y", entry="lo")
    for xs, zs in plate_screw_xz():
        U.boolean(head, U.cylinder("plate_ins", P.insert_hole / 2, YO - 1.0, YO + P.INSERT_DEPTH, xs, zs, "Y"))
    U.cleanup(head)
    U.shade(head)
    return head


def valve_cover():
    d = _dims()
    X0, X1, TOP = d["X0"], d["X1"], d["TOP"]
    vc = P.VC
    x0, x1 = X0 + vc["x_inset"], X1 - vc["x_inset"]
    y0, y1, h, w = vc["y0"], vc["y1"], vc["h"], vc["wall"]
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    z0, z1 = TOP - 1.0, TOP - 1.0 + h
    cover = U.rrect_prism("31_valve_cover", xm, ym, x1 - x0, y1 - y0, vc["r"], z0, z1)
    U.bevel_edges(cover, vc["chamfer"], 3, lambda c, dd: abs(c.z - z1) < 0.3)          # crisp top edge
    # shell
    U.boolean(cover, U.rrect_prism("vc_inner", xm, ym, x1 - x0 - 2 * w, y1 - y0 - 2 * w, max(0.5, vc["r"] - w), z0 - 1, z1 - w))
    # recessed top panel with two shallow cast ribs along it
    pi, pd = vc["panel_inset"], vc["panel_depth"]
    U.boolean(cover, U.rrect_prism("vc_panel", xm, ym, x1 - x0 - 2 * pi, y1 - y0 - 2 * pi, 2.0, z1 - pd, z1 + 1))
    for yr in (ym - 9.0, ym + 9.0):
        rib = U.box("vc_top_rib", x0 + pi + 10, x1 - pi - 10, yr - 1.5, yr + 1.5, z1 - pd - 0.1, z1 - 0.1)
        U.bevel_edges(rib, 0.6, 2, lambda c, dd: abs(dd.x) > 0.9 and c.z > z1 - 0.5)
        U.boolean(cover, rib, "UNION")
    # bolt rim band with recessed hex sockets
    rt, rh = vc["rim_t"], vc["rim_h"]
    rim = U.rrect_prism("vc_rim", xm, ym, x1 - x0 + 2 * rt, y1 - y0 + 2 * rt, vc["r"] + rt, z0 + 1.0, z0 + 1.0 + rh)
    U.boolean(rim, U.rrect_prism("vc_rim_in", xm, ym, x1 - x0 - 2 * w, y1 - y0 - 2 * w, max(0.5, vc["r"] - w), z0, z1))
    U.bevel_edges(rim, 0.8, 2, lambda c, dd: abs(c.z - (z0 + 1.0 + rh)) < 0.3)
    U.boolean(cover, rim, "UNION")
    n = int((x1 - x0 - 16.0) // vc["bolt_pitch"])
    xb = [x0 + 8.0 + i * (x1 - x0 - 16.0) / n for i in range(n + 1)]
    heads = [(x, yb) for x in xb for yb in (y0 - rt / 2 + 0.3, y1 + rt / 2 - 0.3)]
    heads += [(xe, yb) for yb in (ym - 10.0, ym + 10.0) for xe in (x0 - rt / 2 + 0.3, x1 + rt / 2 - 0.3)]
    zb = z0 + 1.0 + rh
    for x, yb in heads:
        U.boolean(cover, U.cylinder("vc_hex", vc["bolt_d"] / 2, zb - 1.2, zb + 1, x, yb, segs=6))
    # oil cap socket (31B is a separate part); the panel ribs are cleared under the cap's footprint
    cx, cy = (X1 - 40.0 if vc["cap_x"] < 0 else X0 + 40.0), vc["cap_y"]
    U.boolean(cover, U.cylinder("cap_seat", vc["cap_d"] / 2 + 0.5, z1 - pd + 0.01, z1 + 1.0, cx, cy))
    F.cut_crush(cover, "boot_9", z1 - w - 1.0, z1 + 1.0, cx, cy, entry="hi")
    # magnet pillars down to the head
    outer = U.rrect_prism("vc_outer", xm, ym, x1 - x0, y1 - y0, vc["r"], z0, z1)
    bx = P.bank_between_x
    for xc in (P.BANK_A_CYL_X[0], P.BANK_A_CYL_X[-1], bx[0], bx[-1]):
        U.boolean(cover, U.cylinder("vc_pillar", 4.5, z0, z1 - w + 0.1, xc, P.VC_MAGNET_Y), "UNION")
        F.cut_magnet(cover, z0, 1, xc, P.VC_MAGNET_Y)
    U.delete(outer)
    U.cleanup(cover)
    U.shade(cover)
    return cover


def oil_cap():
    d = _dims()
    X0, X1, TOP = d["X0"], d["X1"], d["TOP"]
    vc = P.VC
    z1 = TOP - 1.0 + vc["h"] - vc["panel_depth"]
    cx, cy = (X1 - 40.0 if vc["cap_x"] < 0 else X0 + 40.0), vc["cap_y"]
    cap = U.cylinder("31B_oil_cap", vc["cap_d"] / 2, z1, z1 + vc["cap_h"], cx, cy)
    U.bevel_edges(cap, 1.5, 3, lambda c, dd: abs(c.z - (z1 + vc["cap_h"])) < 0.3)
    nk = 24
    for i in range(nk):
        a = i * 360.0 / nk
        g = U.box("knurl", -0.6, 0.6, vc["cap_d"] / 2 - 0.7, vc["cap_d"] / 2 + 1, z1 + 1.0, z1 + vc["cap_h"] - 1.6)
        U.rot(g, 'Z', a)
        U.move(g, cx, cy, 0)
        U.boolean(cap, g)
    spig = U.cylinder("cap_spigot", vc["cap_spigot_d"] / 2, z1 - vc["wall"] - 0.5 + vc["panel_depth"], z1 + 0.1, cx, cy)
    U.boolean(cap, spig, "UNION")
    U.shade(cap)
    return cap


def plug_boot():
    """Local frame: +Z = outboard, z = 0 at the head's outboard face."""
    pb, fp_t = P.PLUG_BOOT, P.EXH_FLANGE_PLATE["t"]
    shaft = U.cylinder("32_plug_boot", pb["shaft_d"] / 2, -pb["shaft_l"], fp_t + 0.01)
    body = U.cylinder("boot_body", pb["d"] / 2, fp_t, fp_t + pb["l"])
    U.bevel_edges(body, 3.5, 6, lambda c, dd: abs(c.z - (fp_t + pb["l"])) < 0.3)
    U.boolean(shaft, body, "UNION")
    U.shade(shaft)
    return shaft


def flange_plate():
    d = _dims()
    X0, X1, YO, DECK = d["X0"], d["X1"], d["YO"], d["DECK"]
    fp = d["FP"]
    plate = U.box("34_header_plate", X0 + fp["end_inset"], X1 - fp["end_inset"], YO - fp["t"], YO, DECK + fp["z0"], DECK + fp["z1"])
    U.bevel_edges(plate, 2.0, 3, lambda c, dd: abs(dd.y) > 0.9)
    # round-1 critique: the plate read as one blank strip. Each primary gets its own square flange pad
    # (2.5 mm proud of the outboard face, chamfered) with two hex bolt heads on the diagonal, like the
    # references' individual port flanges. The plate prints outboard face up, so the pads are on the top.
    pad_hw, pad_hh, pad_t = 11.5, 14.5, 2.5                     # 2 mm clear of the boot bodies at xc + 15
    for xc in P.BANK_A_CYL_X:
        pad = U.box("fl_pad", xc - pad_hw, xc + pad_hw, YO - fp["t"] - pad_t, YO - fp["t"] + 0.3, d["PORT_Z"] - pad_hh, d["PORT_Z"] + pad_hh)
        U.bevel_edges(pad, 1.2, 2, lambda c, dd: abs(c.y - (YO - fp["t"] - pad_t)) < 0.2)
        U.boolean(plate, pad, "UNION")
        for sx, sz in ((-1, 1), (1, -1)):
            hx, hz = xc + sx * (pad_hw - 3.5), d["PORT_Z"] + sz * (pad_hh - 3.5)
            bolt = U.cylinder("fl_bolt", 2.2, YO - fp["t"] - pad_t - 1.6, YO - fp["t"] - pad_t + 0.2, hx, hz, "Y", segs=6)
            U.boolean(plate, bolt, "UNION")
    for xc in P.BANK_A_CYL_X:
        U.boolean(plate, U.cylinder("fp_pipe", P.EXH_PRIMARY_D / 2 + P.CLEARANCE, YO - fp["t"] - 1, YO + 1, xc, d["PORT_Z"], "Y"))
    for xb in d["BOOT_X"]:
        U.boolean(plate, U.cylinder("fp_boot", P.PLUG_BOOT["shaft_d"] / 2 + P.CLEARANCE, YO - fp["t"] - 1, YO + 1, xb, d["BOOT_Z"], "Y"))
    for xs, zs in plate_screw_xz():
        U.boolean(plate, U.cylinder("fp_clear", P.hole["M3_CLEAR"] / 2, YO - fp["t"] - 1, YO + 1, xs, zs, "Y"))
        U.boolean(plate, U.cylinder("fp_cbore", P.hole["M3_CBORE"] / 2, YO - fp["t"] - 1, YO - fp["t"] + (fp["t"] - P.SCREW_FLOOR + 2.0), xs, zs, "Y"))
    U.shade(plate)
    return plate


def placed(lib, banks=("A", "B")):
    """Engine frame: bank A = to_bank(A); bank B = mirror of bank A's placed part, shifted by the bank
    offset (head, plate, boots), covers rotated (one part). Same logic as cad/exterior_v8.placed."""
    out = []
    d = _dims()
    for bank in banks:
        def tA(name, obj):
            o = U.copy(obj, name)
            return U.to_bank(o, "A", P.bank_angle_A, P.bank_angle_B)

        def mir(name, o):
            if bank == "A":
                return o
            m = U.mirror_y(o, name)
            U.delete(o)
            return U.move(m, P.BANK_OFFSET, 0, 0)
        out.append((f"head_{bank}", mir(f"head_{bank}", tA(f"head_{bank}", lib["head"]))))
        out.append((f"valve_cover_{bank}", U.to_bank(U.copy(lib["valve_cover"], f"valve_cover_{bank}"), bank, P.bank_angle_A, P.bank_angle_B)))
        out.append((f"oil_cap_{bank}", U.to_bank(U.copy(lib["oil_cap"], f"oil_cap_{bank}"), bank, P.bank_angle_A, P.bank_angle_B)))
        out.append((f"header_plate_{bank}", mir(f"header_plate_{bank}", tA(f"header_plate_{bank}", lib["plate"]))))
        for i, xl in enumerate(P.BANK_A_CYL_X):
            b = U.copy(lib["boot"], f"boot_{bank}{i+1}")
            U.rot(b, 'X', 90)                                              # local +Z -> -y' (outboard)
            U.move(b, xl + P.PLUG_BOOT["dx"], d["YO"], d["BOOT_Z"])
            U.to_bank(b, "A", P.bank_angle_A, P.bank_angle_B)
            out.append((f"boot_{bank}{i+1}", mir(f"boot_{bank}{i+1}", b)))
    return out


def build_all():
    return {"head": cylinder_head(), "valve_cover": valve_cover(), "oil_cap": oil_cap(), "boot": plug_boot(), "plate": flange_plate()}
