"""43 front cover, 44 harmonic damper, 45 accessory module - as cad/front_v8.py
from params.json. Engine frame, +X = front."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P


def _polar(r, deg):
    a = math.radians(deg)
    return r * math.sin(a), r * math.cos(a)


def _outline(off):
    FC = P.FRONT_COVER
    pts = []
    for i, (z, hw) in enumerate(FC["outline"]):
        pts.append((hw - off, z + (off if i == 0 else 0)))
    pts[-1] = (FC["outline"][-1][1] - off, FC["outline"][-1][0] - off)
    right = pts
    left = [(-y, z) for y, z in reversed(right)]
    return U.fillet_polygon(right + left, max(1.0, FC["r"] - off), n=12)


def _outline_solid(name, off, x0, x1):
    return U.prism(name, _outline(off), x0, x1)


def _outline_perimeter_points(off, n, phase=0.03):
    """n points evenly spaced along the outline's perimeter (for the bolt dimples)."""
    poly = _outline(off)
    segs = [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)
    out = []
    for k in range(n):
        s = ((k / n) + phase) % 1.0 * total
        acc = 0.0
        for (a, b), L in zip(segs, lens):
            if acc + L >= s:
                f = (s - acc) / L if L else 0
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
            acc += L
    return out


def front_cover():
    FC = P.FRONT_COVER
    X0, X1, w = P.COVER_X0, P.COVER_X1, FC["wall"]
    cover = _outline_solid("43_front_cover", 0.0, X0, X1)
    U.bevel_edges(cover, 2.0, 3, lambda c, d: abs(c.x - X1) < 0.3 and abs(d.x) < 0.1)
    U.boolean(cover, _outline_solid("cover_in", w, X0 - 1, X1 - w))
    groove = _outline_solid("groove", 4.0, X1 - 1.0, X1 + 1)
    U.boolean(groove, _outline_solid("groove_in", 5.2, X1 - 2, X1 + 2))
    U.boolean(cover, groove)
    for y, z in _outline_perimeter_points(2.0, FC["n_bolts"]):
        U.boolean(cover, U.cylinder("dimple", FC["bolt_r"], X1 - 1.0, X1 + 1, y, z, "X"))
    U.boolean(cover, U.cylinder("shaft_hole", P.SHAFT_D / 2 + FC["shaft_clear"], X1 - w - 1, X1 + 2, 0, 0, "X"))
    outer = _outline_solid("outer_ref", 0.0, X0, X1)
    for y, z in P.COVER_MAGNETS:
        pil = U.cylinder("pillar", P.COVER_PILLAR_R, X0, X1 - w + 0.1, y, z, "X")
        web = U.box("web", X0, X1 - w + 0.1, -P.COVER_PILLAR_R, P.COVER_PILLAR_R, 0, 8)
        U.rot(web, 'X', -math.degrees(math.atan2(y, z)))
        U.move(web, 0, y, z)
        U.boolean(pil, web, "UNION")
        U.boolean(pil, U.copy(outer, "outer_copy"), "INTERSECT")
        U.boolean(cover, pil, "UNION")
        F.cut_magnet(cover, X0, 1, y, z, axis="X")
    U.delete(outer)
    for y, z in FC["module_magnets"]:
        U.boolean(cover, U.cylinder("mod_boss", P.COVER_PILLAR_R + 0.5, X1 - w - 5.0, X1 - w + 0.1, y, z, "X"), "UNION")
        F.cut_magnet(cover, X1, -1, y, z, axis="X")
    U.shade(cover)
    return cover


def damper():
    DM = P.DAMPER
    x0, x1 = P.DAMPER_X0, P.DAMPER_X0 + DM["t"]
    d = U.cylinder("44_damper", DM["d"] / 2, x0, x1, 0, 0, "X")
    U.bevel_edges(d, 1.5, 3, lambda c, dd: abs(c.x - x1) < 0.3 and abs(dd.x) < 0.1)
    U.bevel_edges(d, 1.0, 2, lambda c, dd: abs(c.x - x0) < 0.3 and abs(dd.x) < 0.1)
    gr = U.cylinder("groove", DM["groove_r"] + DM["groove_w"] / 2, x1 - DM["groove_d"], x1 + 1, 0, 0, "X")
    U.boolean(gr, U.cylinder("groove_in", DM["groove_r"] - DM["groove_w"] / 2, x1 - DM["groove_d"] - 1, x1 + 2, 0, 0, "X"))
    U.boolean(d, gr)
    # skin round 2: the face read as a flat disc - two more shallow rings inside the main groove (serpentine look)
    for rr in (24.0, 19.0):
        ring = U.cylinder("face_ring", rr + 0.6, x1 - 0.8, x1 + 1, 0, 0, "X")
        U.boolean(ring, U.cylinder("face_ring_in", rr - 0.6, x1 - 2, x1 + 2, 0, 0, "X"))
        U.boolean(d, ring)
    hub = U.cylinder("hub", DM["hub_d"] / 2, x1 - 0.1, x1 + DM["hub_h"], 0, 0, "X")
    U.bevel_edges(hub, 0.8, 2, lambda c, dd: abs(c.x - (x1 + DM["hub_h"])) < 0.2 and abs(dd.x) < 0.1)
    U.boolean(d, hub, "UNION")
    for i in range(DM["n_holes"]):
        a = math.radians(i * 360.0 / DM["n_holes"] + 30.0)
        U.boolean(d, U.cylinder("hole", DM["hole_r"], x1 - 2.0, x1 + 3, 0.6 * DM["d"] / 2 * math.cos(a), 0.6 * DM["d"] / 2 * math.sin(a), "X"))
    U.boolean(d, U.box("timing_notch", x1 - 3.0, x1 + 3, -0.8, 0.8, DM["d"] / 2 - 1.5, DM["d"] / 2 + 1))
    # D-bore with two crush ribs opposite the flat (flat faces +Z at crank angle 0), as cad/common.crush_d_x
    c = P.crush["dpin_shaft"]
    flat = P.SHAFT_D / 2 - P.SHAFT_FLAT_DEPTH + 0.05 + P.HOLE_COMP / 2
    bore = U.cylinder("dbore_cut", c["bore"] / 2, x0 - 1, x1 + 3, 0, 0, "X")
    U.boolean(bore, U.box("dflat", x0 - 2, x1 + 4, -c["bore"], c["bore"], flat, flat + c["bore"]))
    U.boolean(d, bore)
    lead = P.CRUSH_LEAD
    U.boolean(d, U.cylinder("lead_lo", c["bore"] / 2 + lead + 0.005, x0 - 0.05, x0 + lead + 0.01, 0, 0, "X", r2=c["bore"] / 2 + 0.005))
    U.boolean(d, U.cylinder("lead_hi", c["bore"] / 2 + 0.005, x1 + DM["hub_h"] - lead - 0.01, x1 + DM["hub_h"] + 0.05, 0, 0, "X", r2=c["bore"] / 2 + lead + 0.005))
    offsets = []
    for a in (180.0 - 55.0, 180.0 + 55.0):
        ry, rz = _polar(c["rib_centre_r"], a)
        U.boolean(d, U.cylinder("drib", c["rib_r"], x0 + lead + 0.05, x1 + DM["hub_h"] - lead - 0.05, ry, rz, "X", segs=24), "UNION")
        offsets.append((0.0, ry, rz))
    # measurement records: the round part of the D (the flat sector, +Z side, is skipped as a wide extra "rib" sector)
    p_ax, d_ax, e1 = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    hw = math.degrees(math.asin(c["rib_r"] / c["rib_centre_r"])) + 2.0
    sectors = [(F.sector_angle(d_ax, e1, o), hw) for o in offsets]
    flat_hw = math.degrees(math.acos(flat / (c["bore"] / 2))) + 1.0
    F.note(d, "dpin_shaft bore", "bore", c["bore"] / 2, p_ax, d_ax, x0 + lead + 0.01 - 0.05, x1 + DM["hub_h"] - lead - 0.01 + 0.05, e1,
           sectors + [(F.sector_angle(d_ax, e1, (0.0, 0.0, 1.0)), flat_hw)])
    F.note(d, "dpin_shaft rib tip", "tip", c["rib_centre_r"] - c["rib_r"], p_ax, d_ax, x0 + lead + 0.05 - 0.05, x1 + DM["hub_h"] - lead - 0.05 + 0.05, e1,
           [(a_, 1.0) for a_, _ in sectors])
    U.shade(d)
    return d


def _band_polygon(off):
    DM, AC = P.DAMPER, P.ACCESSORY
    circles = [(0.0, 0.0, DM["d"] / 2 + AC["band_gap"])] + [(y, z, r) for _, y, z, r in AC["pulleys"]]
    pts = []
    for y, z, r in circles:
        rr = r + off
        pts += [(y + rr * math.cos(a), z + rr * math.sin(a)) for a in [2 * math.pi * k / 180 for k in range(180)]]
    return U.convex_hull_2d(pts)


def _arm(name, p, q, w, x0, x1):
    dy, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dy, dz)
    ny, nz = -dz / L * w / 2, dy / L * w / 2
    return U.prism(name, [(p[0] + ny, p[1] + nz), (q[0] + ny, q[1] + nz), (q[0] - ny, q[1] - nz), (p[0] - ny, p[1] - nz)], x0, x1)


ALT_SPIGOT_L = 6.0        # mm, the 45B spigot engagement in the module (plate + alternator front body)


def alternator_body():
    """45B: the alternator's rear body (behind the module's back plate) with the cooling slots, printed slotted
    face down; a 9 mm crush-fit spigot locates it in the module."""
    AC, X1 = P.ACCESSORY, P.COVER_X1
    ab = AC["alt_body"]
    y, z = [(yy, zz) for name, yy, zz, _ in AC["pulleys"] if name == "alt"][0]
    px0 = X1 + 0.3
    body = U.cylinder("45B_alternator_body", ab["r"], ab["x0"], px0 - P.CLEARANCE, y, z, "X")
    U.bevel_edges(body, 2.0, 2, lambda c, dd: abs(c.x - ab["x0"]) < 0.3 and abs(dd.x) < 0.1)
    for i in range(12):
        sl = U.box("alt_slot", ab["x0"] - 1, ab["x0"] + 2.0, -1.2, 1.2, ab["r"] * 0.45, ab["r"] * 0.8)
        U.rot(sl, 'X', i * 30.0)
        U.move(sl, 0, y, z)
        U.boolean(body, sl)
    sp = U.cylinder("alt_spigot", P.PLUG_BOOT["shaft_d"] / 2, px0 - P.CLEARANCE - 0.1, px0 + ALT_SPIGOT_L - 0.3, y, z, "X")
    U.bevel_edges(sp, 0.6, 1, lambda c, dd: abs(c.x - (px0 + ALT_SPIGOT_L - 0.3)) < 0.2 and abs(dd.x) < 0.1)
    U.boolean(body, sp, "UNION")
    U.shade(body)
    return body


def accessory_module():
    AC, DM, FC, X1 = P.ACCESSORY, P.DAMPER, P.FRONT_COVER, P.COVER_X1
    t = AC["plate_t"]
    px0, px1 = X1 + 0.3, X1 + 0.3 + t
    pul = {name: (y, z, r) for name, y, z, r in AC["pulleys"]}
    mod = None
    for name, (y, z, r) in pul.items():
        disc = U.cylinder("45_accessory_module" if mod is None else "disc", r + AC["plate_margin"], px0, px1, y, z, "X")
        mod = disc if mod is None else U.boolean(mod, disc, "UNION")
    for a, b in AC["arms"]:
        (ya, za, _), (yb, zb, _) = pul[a], pul[b]
        U.boolean(mod, _arm("arm", (ya, za), (yb, zb), AC["arm_w"], px0, px1), "UNION")
    U.boolean(mod, U.cylinder("damper_gap", DM["d"] / 2 + 3.0, px0 - 1, px1 + 1, 0, 0, "X"))
    bx0 = X1 + AC["band_x0"]
    band = U.prism("band", _band_polygon(AC["band_t"]), bx0, bx0 + AC["band_w"])
    # inner face 0.5 mm inside the pulley grooves (not tangent to the pulley rims): the band fuses into the grooves
    U.boolean(band, U.prism("band_in", _band_polygon(-0.5), bx0 - 1, bx0 + AC["band_w"] + 1))
    U.boolean(mod, band, "UNION")
    py0, py1 = X1 + AC["pulley_x0"], X1 + AC["pulley_x0"] + AC["pulley_t"]
    for name, (y, z, r) in pul.items():
        p = U.cylinder("pulley", r, py0, py1, y, z, "X")
        U.bevel_edges(p, 1.0, 2, lambda c, dd: abs(c.x - py1) < 0.2 and abs(dd.x) < 0.1)
        groove = U.cylinder("pgroove", r + 1, bx0, bx0 + AC["band_w"], y, z, "X")
        U.boolean(groove, U.cylinder("pgroove_in", r - 1.0, bx0 - 1, bx0 + AC["band_w"] + 1, y, z, "X"))
        U.boolean(p, groove)
        # skin round 2: flat discs - two shallow concentric grooves in each pulley face (faces up in the print)
        for f in (0.58, 0.82):
            fr = U.cylinder("face_groove", r * f + 0.5, py1 - 0.8, py1 + 1, y, z, "X")
            U.boolean(fr, U.cylinder("face_groove_in", r * f - 0.5, py1 - 2, py1 + 2, y, z, "X"))
            U.boolean(p, fr)
        U.boolean(p, U.cylinder("nut", r * 0.35, py1 - 0.1, py1 + 1.5, y, z, "X", segs=6), "UNION")
        if name == "alt":
            # the alternator body in front of the plate stays on the module; the part behind the plate is 45B
            # (it would hang 35 mm below the back plate when the module prints plate-down) and plugs into a socket here
            ab = AC["alt_body"]
            front_body = U.cylinder("alt_front", ab["r"], px1 - 0.1, ab["x1"], y, z, "X")
            U.bevel_edges(front_body, 2.0, 2, lambda c, dd: abs(c.x - ab["x1"]) < 0.3 and abs(dd.x) < 0.1)
            U.boolean(mod, front_body, "UNION")
            F.cut_crush(mod, "boot_9", px0 - 0.5, px0 + ALT_SPIGOT_L + 0.3, y, z, "X", entry="lo")
        elif name == "pump":
            U.boolean(mod, U.cylinder("snout", AC["pump_snout_r"], px1 - 0.1, py0 + 0.1, y, z, "X"), "UNION")
        else:
            U.boolean(mod, U.cylinder("idler_boss", AC["idler_boss_r"], px1 - 0.1, py0 + 0.1, y, z, "X"), "UNION")
        U.boolean(mod, p, "UNION")
    for y, z in FC["module_magnets"]:
        U.boolean(mod, U.cylinder("mag_boss", P.COVER_PILLAR_R + 0.5, px0, px1 + 2.0, y, z, "X"), "UNION")
        F.cut_magnet(mod, px0, 1, y, z, axis="X")
    U.shade(mod)
    return mod


def build_all():
    return {"front_cover": front_cover(), "damper": damper(), "accessory": accessory_module(), "alt_body": alternator_body()}


def placed(lib, phi=0.0):
    d = U.copy(lib["damper"], "damper")
    U.rot(d, 'X', -(P.THROW_PIN_A[0] + phi))
    return [("front_cover", U.copy(lib["front_cover"], "front_cover")), ("damper", d), ("accessory", U.copy(lib["accessory"], "accessory")),
            ("alternator", U.copy(lib["alt_body"], "alternator"))]
