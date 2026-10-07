"""36 intake lid, 36B intake base, 36C throttle body - sculpted single-plane
plenum with bulging flanks and eight runner ridges (approved D42/D48 layout),
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


def intake_lid():
    it = P.INTAKE
    Z0, ZTOP, SPLIT, W = it["sections"][0][0], it["sections"][-1][0], it["split_z"], it["wall"]
    lid = envelope("36_intake_lid", SPLIT, ZTOP)
    U.bevel_edges(lid, it["top_fillet"], 6, lambda c, d: abs(c.z - ZTOP) < 0.3)
    # runner ridges: rounded-rect tube along the flank, over the top edge, onto the roof
    for bank in ("A", "B"):
        sgn = -1 if bank == "A" else 1
        xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
        for xc in xs:
            pts = [(xc, sgn * y, z) for y, z in it["ridge"]]
            # smooth path: pre-point inside the flank so the ridge grows out of the wall; the section swells
            # from 0.8x at the flank to 1.15x where the runner enters the plenum roof (cast-runner look)
            pts = [(xc, sgn * (it["ridge"][0][0] - 6.0), it["ridge"][0][1] - 4.0)] + pts
            path, _ = U.rounded_path(pts, [10.0, 10.0], n=10)
            ridge = U.loft_along("ridge", path, lambda f: (it["runner_w"] * (0.8 + 0.35 * f), it["runner_h"] * (0.8 + 0.35 * f), it["runner_r"]), up=(1, 0, 0))
            U.boolean(ridge, U.box("ridge_clip", -300, 300, -300, 300, SPLIT + 0.05, ZTOP + 50), "INTERSECT")   # nothing below the split (the base is there)
            U.boolean(lid, ridge, "UNION")
        # molded fuel rail with injector bosses
        yr = sgn * (_dim(it["rail_z"])[0] / 2 + it["rail_out"])
        rail = U.cylinder("rail", it["rail_r"], min(xs) - 12.0, max(xs) + 12.0, yr, it["rail_z"], "X")
        U.bevel_edges(rail, 1.5, 3, lambda c, d: abs(d.x) < 0.1 and abs(abs(c.x) - (max(xs) + 12.0 if c.x > 0 else -(min(xs) - 12.0))) < 2.0)
        U.boolean(lid, rail, "UNION")
        for xc in xs:
            boss = U.cylinder("inj", it["inj_r"], 0, it["inj_l"], 0, 0)
            U.rot(boss, 'X', -sgn * 150.0)                               # pointing down-inward into the flank
            U.move(boss, xc, yr, it["rail_z"])
            U.boolean(lid, boss, "UNION")
    # hollow (after the ridges so nothing intrudes where the base's tongue sits)
    U.boolean(lid, envelope("lid_inner", SPLIT - 1.0, ZTOP - W, W))
    # roof ribs
    l_in = _dim(ZTOP - W)[1] - 2 * W
    n = int(l_in // it["rib_pitch"])
    for i in range(1, n + 1):
        x = -l_in / 2 + i * l_in / (n + 1)
        rib = U.box("roof_rib", x - it["rib_t"] / 2, x + it["rib_t"] / 2, -100, 100, ZTOP - W - 8.0, ZTOP - W + 0.1)
        U.boolean(rib, envelope("rib_clip", SPLIT, ZTOP, W - 0.1), "INTERSECT")
        U.boolean(lid, rib, "UNION")
    # plenum crown along the roof centre, between the ridge ends
    cw = _dim(ZTOP)[0] - 2 * (it["ridge"][-1][0] + it["runner_h"] / 2 + 2.0)
    cl = (max(P.BANK_B_CYL_X) - min(P.BANK_A_CYL_X)) + it["runner_w"] + 12.0
    crown = U.loft("crown", [U.rrect_ring((max(P.BANK_B_CYL_X) + min(P.BANK_A_CYL_X)) / 2, 0, cl, cw, 10.0, ZTOP - 0.5),
                             U.rrect_ring((max(P.BANK_B_CYL_X) + min(P.BANK_A_CYL_X)) / 2, 0, cl - 10.0, cw - 8.0, 7.0, ZTOP + 4.0)])
    U.boolean(lid, crown, "UNION")
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
    it = P.INTAKE
    axis, base = tb_axis()
    tb = U.cylinder("36C_throttle_body", it["tb_d"] / 2, -2.0, it["tb_l"], 0, 0)
    U.bevel_edges(tb, 2.0, 3, lambda c, d: abs(c.z - it["tb_l"]) < 0.3)
    # cast ring and a throttle-shaft boss on the side
    U.boolean(tb, U.cylinder("tb_ring", it["tb_d"] / 2 + 1.5, it["tb_l"] - 9.0, it["tb_l"] - 6.0, 0, 0), "UNION")
    # square mounting flange at the lid face with four recessed bolts (pockets open towards the bore face)
    fl = U.rrect_prism("tb_flange", 0, 0, it["tb_d"] + 10.0, it["tb_d"] + 10.0, 5.0, 0.5, 4.0)
    U.bevel_edges(fl, 1.0, 2, lambda c, d: abs(c.z - 4.0) < 0.2 and abs(d.z) < 0.1)
    U.boolean(tb, fl, "UNION")
    hp = (it["tb_d"] + 10.0) / 2 - 4.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            U.boolean(tb, U.cylinder("tb_bolt", 2.0, 2.6, 5.0, sx * hp, sy * hp, segs=6))
    U.boolean(tb, U.cylinder("tb_bore", it["tb_bore"] / 2, it["tb_l"] - it["tb_bore_depth"], it["tb_l"] + 1, 0, 0))
    U.boolean(tb, U.cylinder("tb_bore_chamfer", it["tb_bore"] / 2 + 0.01, it["tb_l"] - 1.5, it["tb_l"] + 0.05, 0, 0, r2=it["tb_bore"] / 2 + 1.6))
    blade = U.box("blade", -it["tb_bore"] / 2 + 0.3, it["tb_bore"] / 2 - 0.3, -1.2, 1.2, -it["tb_bore"] / 2 + 0.3, it["tb_bore"] / 2 - 0.3)
    U.rot(blade, 'X', 90 - it["tb_blade_deg"])
    U.move(blade, 0, 0, it["tb_l"] - it["tb_bore_depth"] / 2)
    U.boolean(blade, U.cylinder("blade_clip", it["tb_bore"] / 2 + 0.5, it["tb_l"] - it["tb_bore_depth"] - 0.5, it["tb_l"] + 1, 0, 0), "INTERSECT")
    U.boolean(tb, blade, "UNION")
    zs = it["tb_l"] - it["tb_bore_depth"] / 2
    U.boolean(tb, U.cylinder("tb_shaft", 1.6, -it["tb_d"] / 2 - 1, it["tb_d"] / 2 + 3.0, 0, zs, "X"), "UNION")
    # throttle shaft boss and lever on the +x side
    U.boolean(tb, U.cylinder("tb_shaft_boss", 4.0, it["tb_d"] / 2 - 2.0, it["tb_d"] / 2 + 2.5, 0, zs, "X"), "UNION")
    lever = U.box("tb_lever", it["tb_d"] / 2 + 2.5, it["tb_d"] / 2 + 4.0, -2.0, 2.0, zs - 12.0, zs + 2.0)
    U.boolean(tb, lever, "UNION")
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
