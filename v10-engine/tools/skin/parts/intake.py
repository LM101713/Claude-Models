"""36 intake lid, 36B intake base, 36C throttle body - sculpted single-plane
plenum with bulging flanks and eight continuous runner tubes (D42/D48 layout, D61 tubes),
every dimension from params.json INTAKE."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P


def _dim(z):
    secs = P.INTAKE["sections"]
    for (za, wa, la), (zb, wb, lb) in zip(secs, secs[1:]):
        if za - 1e-9 <= z <= zb + 1e-9:
            f = (z - za) / (zb - za)
            f = 0.5 - 0.5 * math.cos(math.pi * f)              # eased: the flank bulges instead of a straight taper
            return wa + f * (wb - wa), la + f * (lb - la)
    return (secs[0][1], secs[0][2]) if z < secs[0][0] else (secs[-1][1], secs[-1][2])


def envelope(name, z0, z1, inset=0.0, steps=10):
    rings = []
    for i in range(steps + 1):
        z = z0 + (z1 - z0) * i / steps
        w, l = _dim(z)
        rings.append(U.rrect_ring(0, 0, l - 2 * inset, w - 2 * inset, max(1.0, P.INTAKE["r"] - inset), z, 12))
    return U.loft(name, rings)


def _bank_vec(bank, yl, zl):
    a = math.radians(-P.bank_angle_A if bank == "A" else -P.bank_angle_B)   # to_bank: rotate by -bank_angle about X
    sgn = -1 if bank == "B" else 1                                             # bank B: 180 about Z first (y' -> -y')
    y, z = sgn * yl, zl
    return (y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))


def runner_path(bank, xc):
    """Guide points (engine frame) of one runner tube: INTAKE.runner_path (|y|, z) from just above the head's
    port face, up and outward along the flank, over the top edge and into the spine. Every point lies on the
    plenum side of the head's valley face. Lid and base sweep the same path and clip at split_z, so the tube
    section matches across the gasket line; the straight port stub on the base plugs the head pocket."""
    sgn = -1 if bank == "A" else 1
    return [(xc, sgn * y, z) for y, z in P.INTAKE["runner_path"]]


def _runner(bank, xc, z0, z1):
    it = P.INTAKE
    tube = U.tube_along("runner", runner_path(bank, xc), 0, profile=(it["runner_w"], it["runner_h"], it["runner_r"]), segs=32)
    U.boolean(tube, U.box("runner_clip", -300, 300, -300, 300, z0, z1), "INTERSECT")
    return tube


def intake_lid():
    it = P.INTAKE
    Z0, ZTOP, SPLIT, W = it["sections"][0][0], it["sections"][-1][0], it["split_z"], it["wall"]
    lid = envelope("36_intake_lid", SPLIT, ZTOP)
    U.bevel_edges(lid, it["top_fillet"], 6, lambda c, d: abs(c.z - ZTOP) < 0.3)
    # skin round 4 (D61): eight full runner tubes (the round-2/3 ridges read as bumps on a box). Nothing
    # below the split: the base carries the same tube from the head port up to the gasket line.
    for bank in ("A", "B"):
        sgn = -1 if bank == "A" else 1
        xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
        for xc in xs:
            U.boolean(lid, _runner(bank, xc, SPLIT + 0.05, ZTOP + 60.0), "UNION")
        # fuel rail outboard of the runners, injector bosses bridging the gap into each tube
        yr = sgn * it["rail_y"]
        rail = U.cylinder("rail", it["rail_r"], min(xs) - 12.0, max(xs) + 12.0, yr, it["rail_z"], "X")
        U.bevel_edges(rail, 1.5, 3, lambda c, d: abs(d.x) < 0.1 and abs(abs(c.x) - (max(xs) + 12.0 if c.x > 0 else -(min(xs) - 12.0))) < 2.0)
        for xe in (min(xs) - 12.0, max(xs) + 12.0):              # round 5: end caps (fittings) on the rail
            cap = U.cylinder("rail_cap", it["rail_r"] + 1.5, xe - 2.5, xe + 2.5, yr, it["rail_z"], "X", segs=6)
            U.boolean(rail, cap, "UNION")
        for xc in xs:
            boss = U.cylinder("inj", it["inj_r"], 0, it["inj_l"], 0, 0)
            U.rot(boss, 'X', sgn * it["inj_deg"])                        # Rx(+a) takes +z to (0, -sin a, cos a): down and inward for bank B (+y), mirrored for A
            U.move(boss, xc, yr, it["rail_z"])
            U.boolean(rail, boss, "UNION")
        U.boolean(rail, U.box("rail_clip", -300, 300, -300, 300, SPLIT + 0.05, ZTOP + 60.0), "INTERSECT")
        U.boolean(lid, rail, "UNION")
    # raised plenum spine the runners dive into (bolt row along both edges). Same print case as the runners
    # (raised detail on the lid's print face - the open D53 decision: soluble support upright, or a split roof).
    l_top = _dim(ZTOP)[1]
    spine = U.rrect_prism("spine", 0, 0, l_top - 36.0, it["spine_w"], 10.0, ZTOP - 0.5, ZTOP + it["spine_h"])
    U.bevel_edges(spine, 2.5, 3, lambda c, d: abs(c.z - (ZTOP + it["spine_h"])) < 0.2)
    U.boolean(lid, spine, "UNION")
    for xs in (-(l_top / 2 - 25.0), -(l_top / 6), l_top / 6, l_top / 2 - 25.0):
        for ys in (-(it["spine_w"] / 2 - 5.0), it["spine_w"] / 2 - 5.0):
            U.boolean(lid, U.cylinder("spine_bolt", 2.0, ZTOP + it["spine_h"] - 0.1, ZTOP + it["spine_h"] + 1.3, xs, ys, segs=6), "UNION")
    # hollow (after the runners so nothing intrudes where the base's tongue sits)
    U.boolean(lid, envelope("lid_inner", SPLIT - 1.0, ZTOP - W, W))
    # roof ribs
    l_in = _dim(ZTOP - W)[1] - 2 * W
    n = int(l_in // it["rib_pitch"])
    for i in range(1, n + 1):
        x = -l_in / 2 + i * l_in / (n + 1)
        rib = U.box("roof_rib", x - it["rib_t"] / 2, x + it["rib_t"] / 2, -100, 100, ZTOP - W - 8.0, ZTOP - W + 0.1)
        U.boolean(rib, envelope("rib_clip", SPLIT, ZTOP, W - 0.1), "INTERSECT")
        U.boolean(lid, rib, "UNION")
    for x, y in it["magnet_xy"]:
        U.boolean(lid, U.cylinder("lid_pillar", it["pillar_r"], SPLIT, ZTOP - W + 0.1, x, y), "UNION")
        F.cut_magnet(lid, SPLIT, 1, x, y)
    # throttle-body spigot socket in the front face, along the TB axis
    axis, base = tb_axis()
    sock_len = it["tb_spigot_l"] + 0.5
    from mathutils import Matrix
    M = Matrix.Translation(base) @ Matrix.Rotation(math.radians(90 - it["tb_tilt"]), 4, 'Y')
    F.cut_crush_M(lid, "trumpet_14", -sock_len, 0.5, M, entry="hi")          # 14 mm crush socket for the TB spigot
    U.cleanup(lid)
    U.shade(lid)
    return lid


def tb_axis():
    it = P.INTAKE
    t = math.radians(it["tb_tilt"])
    return (math.cos(t), 0.0, math.sin(t)), (_dim(it["tb_z"])[1] / 2, 0.0, it["tb_z"])


def intake_base():
    it = P.INTAKE
    Z0, SPLIT, W = it["sections"][0][0], it["split_z"], it["wall"]
    base = envelope("36B_intake_base", Z0, SPLIT)
    U.boolean(base, envelope("base_inner", Z0 + W, SPLIT + 1.0, W))
    tongue = envelope("tongue", SPLIT - 0.1, SPLIT + it["tongue_h"], W + P.CLEARANCE)
    U.boolean(tongue, envelope("tongue_in", SPLIT - 1.0, SPLIT + it["tongue_h"] + 1.0, W + P.CLEARANCE + it["tongue_w"]))
    U.boolean(base, tongue, "UNION")
    for bank in ("A", "B"):
        xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
        yl, zl = P.BLOCK_Y_VALLEY - it["port_depth"] + 0.5, P.DECK_DIST + it["port_z"]
        pe = _bank_vec(bank, yl, zl)
        up0 = _bank_vec(bank, 0.0, 0.0)
        up1 = _bank_vec(bank, 1.0, 0.0)
        up = (up1[0] - up0[0], up1[1] - up0[1])
        L = (SPLIT + 2.0 - pe[1]) / up[1]
        for xc in xs:
            # straight port stub along the bank normal into the head pocket (as before) ...
            stub = U.rrect_prism("stub", 0, 0, it["runner_w"], it["runner_h"], it["runner_r"], 0.0, L)
            ang = math.degrees(math.atan2(up[0], up[1]))                     # tilt of +y' from +z in the yz plane
            U.rot(stub, 'X', -ang)
            U.move(stub, xc, pe[0], pe[1])
            clip = U.box("stub_clip", -200, 200, -200, 200, Z0 - 20, SPLIT)
            U.boolean(stub, clip, "INTERSECT")
            U.boolean(base, stub, "UNION")
            # ... merged with the lower half of the runner tube that the lid continues above the gasket line (D61).
            # The tube is cut back to 0.3 mm outside the head's valley face (its section would otherwise cross
            # into the head: 8.9 cm3 overlap per head in the skin check).
            tube = _runner(bank, xc, Z0 - 20.0, SPLIT)
            head_side = U.box("head_side", -300, 300, -300, yl + 4.0, -300, 400)          # bank-local: 4 mm out from the port face (the straight stub covers that zone; 0.3 left a thin step)
            U.to_bank(head_side, bank, P.bank_angle_A, P.bank_angle_B)
            U.boolean(tube, head_side)
            U.boolean(base, tube, "UNION")
    for x, y in it["magnet_xy"]:
        pil = U.cylinder("base_pillar", it["pillar_r"], Z0 + W - 0.1, SPLIT, x, y)
        U.boolean(base, pil, "UNION")
        F.cut_magnet(base, SPLIT, -1, x, y)
    U.boolean(base, U.cylinder("harness", 6.0, Z0 - 1, Z0 + W + 1, -40.0, 0.0))
    U.cleanup(base)
    U.shade(base)
    return base


def throttle_body():
    it = P.INTAKE
    axis, base = tb_axis()
    tb = U.cylinder("36C_throttle_body", it["tb_d"] / 2, -2.0, it["tb_l"], 0, 0)
    U.bevel_edges(tb, 2.0, 3, lambda c, d: abs(c.z - it["tb_l"]) < 0.3)
    # cast ring and a throttle-shaft boss on the side
    U.boolean(tb, U.cylinder("tb_ring", it["tb_d"] / 2 + 1.5, it["tb_l"] - 9.0, it["tb_l"] - 6.0, 0, 0), "UNION")
    # skin round 2: the mouth read as a plain tube end. A wider bell rim at the mouth with a 45 deg lead
    # (the rim only widens the bed footprint of the bore-down print; 0.1 mm clear of tb_ring, never tangent)
    U.boolean(tb, U.cylinder("tb_mouth_cone", it["tb_d"] / 2 + 0.05, it["tb_l"] - 5.9, it["tb_l"] - 3.4, 0, 0, r2=it["tb_d"] / 2 + 2.5), "UNION")
    U.boolean(tb, U.cylinder("tb_mouth_rim", it["tb_d"] / 2 + 2.5, it["tb_l"] - 3.5, it["tb_l"], 0, 0), "UNION")
    U.boolean(tb, U.cylinder("tb_bore", it["tb_bore"] / 2, it["tb_l"] - it["tb_bore_depth"], it["tb_l"] + 1, 0, 0))
    blade = U.box("blade", -it["tb_bore"] / 2 + 0.3, it["tb_bore"] / 2 - 0.3, -1.2, 1.2, -it["tb_bore"] / 2 + 0.3, it["tb_bore"] / 2 - 0.3)
    U.rot(blade, 'X', 90 - it["tb_blade_deg"])
    U.move(blade, 0, 0, it["tb_l"] - it["tb_bore_depth"] / 2)
    U.boolean(blade, U.cylinder("blade_clip", it["tb_bore"] / 2 + 0.5, it["tb_l"] - it["tb_bore_depth"] - 0.5, it["tb_l"] + 1, 0, 0), "INTERSECT")
    U.boolean(tb, blade, "UNION")
    zs = it["tb_l"] - it["tb_bore_depth"] / 2
    U.boolean(tb, U.cylinder("tb_shaft", 1.6, -it["tb_d"] / 2 - 1, it["tb_d"] / 2 + 10.0, 0, zs, "X"), "UNION")
    # round 5: throttle cam on the shaft end (45 deg cone under the disc: the bore-down print has no flat ceiling)
    U.boolean(tb, U.cylinder("tb_cam_cone", 2.0, it["tb_d"] / 2 + 1.0, it["tb_d"] / 2 + 8.0, 0, zs, "X", r2=9.0), "UNION")
    U.boolean(tb, U.cylinder("tb_cam", 9.0, it["tb_d"] / 2 + 7.9, it["tb_d"] / 2 + 10.0, 0, zs, "X"), "UNION")
    U.boolean(tb, U.cylinder("tb_cam_hex", 2.2, it["tb_d"] / 2 + 9.9, it["tb_d"] / 2 + 11.4, 0, zs, "X", segs=6), "UNION")
    spig = U.cylinder("tb_spigot", it["tb_spigot_d"] / 2, -(it["tb_spigot_l"] + 2.0), 0.1, 0, 0)
    U.boolean(tb, spig, "UNION")
    # place: local +Z -> TB axis (x forward, tilted up), seat on the lid's front face, trim with the lid envelope
    U.rot(tb, 'Y', 90 - it["tb_tilt"])
    U.move(tb, *base)
    # trim with the lid's and the base's own envelopes (same ring sampling, so no slivers between them and the TB)
    U.boolean(tb, envelope("tb_trim_lid", it["split_z"], it["sections"][-1][0]))
    U.boolean(tb, envelope("tb_trim_base", it["sections"][0][0], it["split_z"] + 0.01))
    U.cleanup(tb)
    U.shade(tb)
    return tb


def build_all():
    return {"intake_lid": intake_lid(), "intake_base": intake_base(), "throttle": throttle_body()}


def placed(lib):
    return [("intake_lid", U.copy(lib["intake_lid"], "intake_lid")), ("intake_base", U.copy(lib["intake_base"], "intake_base")),
            ("throttle", U.copy(lib["throttle"], "throttle"))]
