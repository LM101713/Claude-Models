"""36 intake lid, 36B intake base, 36C throttle body - sculpted single-plane
plenum with bulging flanks and eight continuous runner tubes (D42/D48 layout, D61 tubes),
every dimension from params.json INTAKE."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P


def _dim(z):
    secs = P.INTAKE.get("skin_sections", P.INTAKE["sections"])
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
    # NASCAR restyle (D64): a stock-car single-plane manifold is a smooth cast box with no visible runners;
    # the eight runner tubes and the raised spine are gone, so the top is flat (no raised detail on the
    # lid's top-down print face any more). The fuel rail sits on each top flank with short injector bosses.
    for bank in ("A", "B"):
        sgn = -1 if bank == "A" else 1
        xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
        yr, zr = sgn * it["skin_rail_y"], it["skin_rail_z"]
        re_ = it["skin_rail_end"]                                 # round 7: 12 -> 6 mm, the fittings pinched the shoulder corners
        rail = U.cylinder("rail", it["rail_r"], min(xs) - re_, max(xs) + re_, yr, zr, "X")
        for xe in (min(xs) - re_, max(xs) + re_):                # end fittings
            cap = U.cylinder("rail_cap", it["rail_r"] + 1.5, xe - 2.5, xe + 2.5, yr, zr, "X", segs=6)
            U.boolean(rail, cap, "UNION")
        for xc in xs:
            boss = U.cylinder("inj", it["inj_r"], 0, it["skin_inj_l"], 0, 0)
            U.rot(boss, 'X', sgn * it["inj_deg"])
            U.move(boss, xc, yr, zr)
            U.boolean(rail, boss, "UNION")
        U.boolean(rail, U.box("rail_clip", -300, 300, -300, 300, SPLIT + 0.05, ZTOP - 2.0), "INTERSECT")
        U.boolean(lid, rail, "UNION")
    # manifold-to-head bolt row along each flank, just above the gasket line (vertical-axis hex heads on a
    # 45 deg ledge, so they print without support in the top-down orientation)
    zl = SPLIT + it["bolt_ledge_z"]
    wl = _dim(zl)[0] / 2
    for sgn in (-1, 1):
        for i in range(it["n_flank_bolts"]):
            xb = -it["flank_bolt_span"] / 2 + i * it["flank_bolt_span"] / (it["n_flank_bolts"] - 1)
            boss = U.cylinder("flank_boss", 3.4, SPLIT + 0.05, zl, xb, sgn * (wl - 0.6))
            U.boolean(boss, U.cylinder("flank_boss_cone", 3.4, zl - 0.01, zl + 3.4, xb, sgn * (wl - 0.6), r2=0.2), "UNION")
            U.boolean(lid, boss, "UNION")
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
    # NASCAR restyle (D64): the throttle body stands on the top centre (4-barrel style). Solid boss under the
    # roof for the 14 mm crush socket (grows up from the roof in the top-down print: no overhang).
    sock_len = it["tb_spigot_l"] + 0.5
    U.boolean(lid, U.cylinder("tb_boss", 12.0, ZTOP - sock_len - 3.0, ZTOP - W + 0.1, 0, 0), "UNION")
    from mathutils import Matrix
    F.cut_crush_M(lid, "trumpet_14", -sock_len, 0.5, Matrix.Translation((0.0, 0.0, ZTOP)), entry="hi")
    U.cleanup(lid)
    U.shade(lid)
    return lid


def tb_axis():
    """NASCAR restyle (D64): vertical axis, seated on the centre of the lid top."""
    return (0.0, 0.0, 1.0), (0.0, 0.0, P.INTAKE["sections"][-1][0])


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
    for x, y in it["magnet_xy"]:
        pil = U.cylinder("base_pillar", it["pillar_r"], Z0 + W - 0.1, SPLIT, x, y)
        U.boolean(base, pil, "UNION")
        F.cut_magnet(base, SPLIT, -1, x, y)
    U.boolean(base, U.cylinder("harness", 6.0, Z0 - 1, Z0 + W + 1, -40.0, 0.0))
    U.cleanup(base)
    U.shade(base)
    return base


def throttle_body():
    """NASCAR restyle (D64): square 4-barrel throttle body on a tapered-spacer plate, four open bores with
    their blades, linkage shaft and cam on one side. Prints top (bore) face down, spigot up."""
    it = P.INTAKE
    axis, base = tb_axis()
    L, W_, H = it["tb4_l"], it["tb4_w"], it["tb4_h"]
    st, sp = it["spacer_t"], it["spacer_out"]
    tb = U.rrect_prism("36C_throttle_body", 0, 0, L, W_, 4.0, st - 0.01, st + H)
    U.bevel_edges(tb, 1.2, 2, lambda c, d: abs(c.z - (st + H)) < 0.3)
    spacer = U.rrect_prism("tb_spacer", 0, 0, L + 2 * sp, W_ + 2 * sp, 6.0, 0.0, st)
    U.boolean(tb, spacer, "UNION")
    for sx in (-1, 1):                                            # spacer corner bolts (vertical hex heads)
        for sy in (-1, 1):
            U.boolean(tb, U.cylinder("tb_bolt", 2.3, st - 0.1, st + 1.6, sx * (L / 2 + sp / 2), sy * (W_ / 2 + sp / 2), segs=6), "UNION")
    zt = st + H
    r = it["tb4_bore"] / 2
    for bx in (-it["tb4_pitch_x"] / 2, it["tb4_pitch_x"] / 2):
        for by in (-it["tb4_pitch_y"] / 2, it["tb4_pitch_y"] / 2):
            U.boolean(tb, U.cylinder("tb_bore", r, zt - it["tb_bore_depth"], zt + 1, bx, by))
            U.boolean(tb, U.cylinder("tb_bore_lead", r, zt - 1.2, zt + 0.05, bx, by, r2=r + 1.2))
            blade = U.box("blade", -r, r, -0.9, 0.9, -r, r)
            U.rot(blade, 'X', 90 - it["tb_blade_deg"])
            U.move(blade, bx, by, zt - it["tb_bore_depth"] / 2)
            U.boolean(blade, U.cylinder("blade_clip", r + 0.3, zt - it["tb_bore_depth"] - 0.5, zt + 1, bx, by), "INTERSECT")
            U.boolean(tb, blade, "UNION")
    # throttle shaft along Y through both bore pairs, cam disc on the +Y side (45 deg cone under it)
    zs = zt - it["tb_bore_depth"] / 2
    for bx in (-it["tb4_pitch_x"] / 2, it["tb4_pitch_x"] / 2):
        U.boolean(tb, U.cylinder("tb_shaft", 1.4, -W_ / 2 + 1.0, W_ / 2 + 4.0, bx, zs, "Y"), "UNION")
    xc = it["tb4_pitch_x"] / 2
    U.boolean(tb, U.cylinder("tb_cam_cone", 2.0, W_ / 2 - 0.5, W_ / 2 + 5.0, xc, zs, "Y", r2=7.5), "UNION")
    U.boolean(tb, U.cylinder("tb_cam", 7.5, W_ / 2 + 4.9, W_ / 2 + 7.0, xc, zs, "Y"), "UNION")
    spig = U.cylinder("tb_spigot", it["tb_spigot_d"] / 2, -it["tb_spigot_l"], 0.1, 0, 0)
    U.boolean(tb, spig, "UNION")
    U.move(tb, *base)
    U.cleanup(tb)
    U.shade(tb)
    return tb


def build_all():
    return {"intake_lid": intake_lid(), "intake_base": intake_base(), "throttle": throttle_body()}


def placed(lib):
    return [("intake_lid", U.copy(lib["intake_lid"], "intake_lid")), ("intake_base", U.copy(lib["intake_base"], "intake_base")),
            ("throttle", U.copy(lib["throttle"], "throttle"))]
