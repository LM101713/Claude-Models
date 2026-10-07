"""Regenerate everything from config.py.

    python build_all.py              # parts + previews + drawings
    python build_all.py --stl-only   # just regenerate STL/STEP (fast)
    python build_all.py --only 07_   # only parts whose file name starts with 07_
    python build_all.py --check      # also run the collision sweep + drive check

Outputs
  stl/       numbered STL + STEP for every part, already in print orientation
  renders/   preview images
  drawings/  dimensioned drawings of the machined parts
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import config as C  # noqa: E402
import assembly  # noqa: E402
import base  # noqa: E402
import block  # noqa: E402
import drive  # noqa: E402
import crank  # noqa: E402
import rods_pistons as rp  # noqa: E402
import styling  # noqa: E402
import coupons  # noqa: E402
import partnum  # noqa: E402
from common import check_printable_size, export, rot_z  # noqa: E402

import drawings  # noqa: E402
import render  # noqa: E402

R = os.path.join(ROOT, "renders")


def parts():
    if C.VARIANT == "v8":
        return parts_v8()
    return parts_v10()


def parts_v8():
    """Stock-car V8 part table: (file name, shape in print orientation, qty per engine, preview colour)."""
    import exterior_v8 as E
    import intake_v8 as I
    import pan_v8 as PV
    import front_v8 as F
    import stand_v8 as S
    L = assembly.libs()
    cr, mp, bl, st, bs, fr, sd = L["crank"], L["rp"], L["block"], L["style"], L["base"], L["front"], L["stand"]
    segs = [(f"{6 + i:02d}_crank_segment_{t:.0f}", crank.print_segment(cr["segA" if i == 0 else ("segB" if i == 1 else f"seg{i}")]),
             sum(1 for d in C.SEGMENT_DELTA if abs(d - t) < 1e-6), "crank") for i, t in enumerate(C.SEGMENT_TYPES)]
    return [
        ("01_crankcase", bl["case"], 1, "case"),
        ("02_valley_beam", block.print_beam(bl["beam"]), 1, "case"),
        ("03_cylinder_bank", block.print_bank(bl["bank"]), 2, "block"),
        ("04_end_plate", block.print_plate(bl["plate"]), 2, "case"),
        ("05_crank_end_web", crank.print_end_web(cr["end"]), 2, "crank"),
        *segs,
        ("09_conrod", rp.print_rod(mp["rod"]), C.N_CYL, "rod"),
        ("10_piston", rp.print_piston(mp["piston"]), C.N_CYL, "piston"),
        # exterior
        ("30_cylinder_head_A", E.print_head(st["head"]), 1, "block"),
        ("30B_cylinder_head_B", E.print_head(st["head"].mirror("XZ")), 1, "block"),
        ("31_valve_cover", E.print_valve_cover(st["valve_cover"]), 2, "carbon"),
        ("32_plug_boot", E.print_boot(st["boot"]), C.N_CYL, "white"),
        ("33_header_primary_A", E.print_primary(st["primary"]), 4, "steel"),
        ("33B_header_primary_B", E.print_primary(st["primary"].mirror("XZ")), 4, "steel"),
        ("34_header_plate_A", E.print_plate(st["plate"]), 1, "steel"),
        ("34B_header_plate_B", E.print_plate(st["plate"].mirror("XZ")), 1, "steel"),
        ("35_collector_A", E.print_collector(st["collector_A"]), 1, "steel"),
        ("35B_collector_B", E.print_collector(st["collector_B"]), 1, "steel"),
        ("36_intake_lid", I.print_lid(st["intake_lid"]), 1, "block"),
        ("36B_intake_base", I.print_base(st["intake_base"]), 1, "block"),
        ("36C_throttle_body", I.print_throttle(st["throttle"]), 1, "steel"),
        # pan, bell, front, stand
        ("40_oil_pan", PV.print_pan(bs["pan"]), 1, "carbon"),
        ("41_pan_floor_panel", PV.print_panel(bs["panel"]), 1, "case"),
        ("42_bellhousing", PV.print_bell(bs["bellhousing"]), 1, "block"),
        ("43_front_cover", F.print_cover(fr["front_cover"]), 1, "block"),
        ("44_damper", F.print_damper(fr["damper"]), 1, "carbon"),
        ("45_accessory_module", F.print_module(fr["accessory"]), 1, "carbon"),
        ("46_stand_plate", S.print_plate(sd["stand_plate"]), 1, "carbon"),
        ("47_bracket", S.print_bracket(sd["bracket"]), 2, "carbon"),
        ("47B_bracket_mirror", S.print_bracket(sd["bracket_m"]), 2, "carbon"),
        ("48_controls_plinth", S.print_plinth(sd["plinth"]), 1, "carbon"),
        # test coupons (print FIRST, in PLA; see docs/TEST_CHECKLIST.md)
        *[(n, shp, q, "white") for n, (shp, q) in coupons.build_all().items()],
        # printable stand-ins so the mechanism can be tested before the CNC parts arrive
        ("P1_proto_crankpin", crank.print_pin(cr["pin"]), C.N_THROWS, "orange"),
        ("P2_proto_main_shaft", crank.print_shaft(cr["shaft"]), 1, "orange"),
        ("P2F_proto_main_shaft_front", crank.print_shaft(cr["shaft_front"]), 1, "orange"),
        # machined / cut steel parts (STEP for the machine shop)
        ("M01_crankpin", cr["pin"], C.N_THROWS, "steel"),
        ("M02R_main_shaft_rear", cr["shaft"], 1, "steel"),
        ("M02F_main_shaft_front", cr["shaft_front"], 1, "steel"),
        ("M03_guide_rail", mp["rail"], C.N_CYL, "steel"),
        ("M04_pulley_spacer", drive.spacer(), 1, "steel"),
        ("M06_bearing_spacer_ring", cr["ring"], 2 * C.N_THROWS, "steel"),
    ]


def parts_v10():
    L = assembly.libs()
    cr, mp, bl, st, bs = L["crank"], L["rp"], L["block"], L["style"], L["base"]
    # (file name, shape in print orientation, qty per engine, preview colour)
    return [
        # Phase 1 - core engine
        ("01_crankcase", bl["case"], 1, "case"),
        ("02_valley_beam", block.print_beam(bl["beam"]), 1, "case"),
        ("03_cylinder_bank", block.print_bank(bl["bank"]), 2, "block"),
        ("04_end_plate", block.print_plate(bl["plate"]), 2, "case"),
        ("05_crank_end_web", crank.print_end_web(cr["end"]), 2, "crank"),
        (f"06_crank_segment_{C.SEGMENT_TYPES[0]:.0f}", crank.print_segment(cr["segA"]), 2, "crank"),
        (f"07_crank_segment_{C.SEGMENT_TYPES[1]:.0f}", crank.print_segment(cr["segB"]), 2, "crank"),
        ("08_conrod", rp.print_rod(mp["rod"]), 10, "rod"),
        ("09_piston", rp.print_piston(mp["piston"]), 10, "piston"),
        # Phase 3 - heads, covers, intake, exhaust
        ("10_cylinder_head", styling.print_head(st["head"]), 2, "block"),
        ("11_cam_cover", styling.print_cam_cover(st["cam_cover"]), 2, "carbon"),
        ("12_side_panel", styling.print_side_panel(st["side_panel"]), 2, "carbon"),
        ("13_intake_trumpet", styling.print_trumpet(st["trumpet"]), 10, "steel"),
        ("14_exhaust_bank_A", styling.print_header(st["header_A"]), 1, "gold"),
        ("15_exhaust_bank_B", styling.print_header(st["header_B"]), 1, "gold"),
        ("16_coil_pack", styling.print_coil(st["coil"]), 10, "red"),
        ("17_throttle_frame", styling.print_plenum(st["plenum"]), 1, "carbon"),
        ("18_end_cover", styling.print_end_cover(st["end_cover"]), 2, "carbon"),
        # Phase 2 - display base
        ("19_base_front", base.print_half(bs["base_front"]), 1, "carbon"),
        ("20_base_rear", base.print_half(bs["base_rear"]), 1, "carbon"),
        ("21_base_panel", base.print_panel(bs["panel"]), 2, "case"),
        # test coupons (print FIRST, in PLA; see docs/TEST_CHECKLIST.md)
        *[(n, shp, q, "white") for n, (shp, q) in coupons.build_all().items()],
        # printable stand-ins so the mechanism can be tested before the CNC parts arrive
        ("P1_proto_split_crankpin", crank.print_pin(cr["pin"]), 5, "orange"),
        ("P2_proto_main_shaft", crank.print_shaft(cr["shaft"]), 2, "orange"),
        # machined / cut steel and aluminium parts (STEP for the machine shop)
        ("M01_split_crankpin", cr["pin"], 5, "steel"),
        ("M02_main_shaft", cr["shaft"], 2, "steel"),
        ("M03_guide_rail", mp["rail"], 10, "steel"),
        ("M04_pulley_spacer", drive.spacer(), 1, "steel"),
        ("M06_bearing_spacer_ring", cr["ring"], 10, "steel"),
        ("M05_intake_trumpet_machined", st["trumpet"], 10, "steel"),
    ]


def main(check=False, stl_only=False, only=None):
    problems = C.self_check(verbose=False)
    print(problems or "config self-check OK")
    if problems:
        raise SystemExit("config self-check failed - fix config.py first")
    os.makedirs(R, exist_ok=True)
    report = []
    for name, shape, qty, col in parts():
        if only and not name.startswith(only):
            continue
        if not shape.isValid():
            raise SystemExit(f"{name}: invalid solid - not exported")
        n_solids = len(shape.Solids())
        if n_solids != 1:
            raise SystemExit(f"{name}: {n_solids} separate solids - a printed part must be one piece")
        shape, note = partnum.label_part(name, shape)
        if note is None:
            print(f"  WARNING {name}: no flat hidden spot found for its part number", flush=True)
        export(shape, name)
        # the stand plate is the one part that uses the single-nozzle bed (325 x 320), not the 300 mm cube
        ok, line = check_printable_size(shape, name, limit=max(C.PRINTER["bed"]) if name.startswith("46_") else 300.0)
        report.append(f"{line}   x{qty}")
        if not ok:
            raise SystemExit(line)
        if not stl_only:
            render.render([(shape, col)], os.path.join(R, f"part_{name}.png"), view="iso",
                          size=(900, 700), title=f"{name}  (x{qty})")
        print("  exported", name, flush=True)
    if stl_only or only:
        print("\n".join(report))
        return

    # assembly previews of the finished engine
    full = [(s, c) for _, s, c in assembly.full(0.0)]
    render.render(full, os.path.join(R, "01_engine_iso.png"), view="iso", size=(1600, 1100),
                  title=f"{C.VARIANT.upper()} display engine - covers on")
    render.render(full, os.path.join(R, "02_engine_front.png"), view="front", size=(1400, 1000),
                  title="front: 90 deg V, belt drive under the front cover")
    render.render(full, os.path.join(R, "03_engine_rear.png"), view=((-1.0, 0.75, 0.45), (0, 0, 1)),
                  size=(1400, 1000), title="rear: 12 V jack, power, speed knob, START")
    render.render(full, os.path.join(R, "04_engine_top.png"), view="top", size=(1400, 1000),
                  title="top: trumpets on the throttle frame, coil packs, exhausts")
    open_ = [(s, c) for n, s, c in assembly.full(0.0, covers=False) if not n.startswith("end_cover")]
    render.render(open_, os.path.join(R, "05_engine_covers_off.png"), view=((0.45, -1.0, 0.5), (0, 0, 1)),
                  size=(1600, 1100), title="side panels, cam covers and end covers off (all magnetic)")
    render.render(open_, os.path.join(R, "06_engine_windows.png"), view=((0.15, -1.0, 0.25), (0, 0, 1)),
                  size=(1600, 1000), zoom=1.3, title="bank A windows: pistons on their rails, rods, crank")
    inner = [(s, c) for n, s, c in assembly.engine(0.0, with_blocks=False)
             if not n.startswith(("crankcase", "end_plate", "valley_beam"))]
    render.render(inner, os.path.join(R, "07_mechanism_iso.png"), view="iso", size=(1400, 1000),
                  title="mechanism: crank, rods, pistons, guide rails")
    render.render(inner, os.path.join(R, "08_mechanism_front.png"), view="front", size=(1200, 1000),
                  title="mechanism - front view")
    crank_only = [(s, c) for n, s, c in assembly.engine(0.0, with_blocks=False, with_rails=False)
                  if n.startswith(("crankpin", "segment", "end_web", "main_shaft"))]
    render.render(crank_only, os.path.join(R, "09_crank_assembly.png"), view="iso", zoom=1.6, size=(1400, 900),
                  title="built-up crankshaft: 5 split pins (18 deg), 72 deg even firing")
    drv = [(s, c) for n, s, c in assembly.engine(0.0) + assembly.drive_and_base()
           if not n.startswith(("base_", "panel_", "end_cover", "bank_", "elec_"))]
    render.render(drv, os.path.join(R, "10_drive_train.png"), view=((1.0, -0.8, 0.2), (0, 0, 1)), zoom=1.2,
                  size=(1400, 1000), title="3:1 GT2 belt drive (base and covers hidden)")
    under = [(s, c) for n, s, c in assembly.drive_and_base() if not n.startswith(("panel_", "end_cover"))]
    render.render(under, os.path.join(R, "11_base_inside.png"), view=((0.6, -0.8, -1.0), (0, 0, 1)),
                  size=(1400, 1000), title="base from below, panels off: motor, controller board, panel parts")
    drawings.build()

    with open(os.path.join(ROOT, "stl", "SIZE_REPORT.txt"), "w") as f:
        f.write("Bounding boxes (print orientation). Limit 300 x 300 x 300 mm.\n")
        f.write("\n".join(report) + "\n")
    print("\n".join(report))

    if check:
        hits = assembly.sweep(10.0, verbose=False)
        print("collision sweep:", "CLEAR" if not hits else f"{len(hits)} COLLISIONS")
        bad = assembly.drive_check()
        print("drive check:", "CLEAR" if not bad else bad)
        for h in hits[:20]:
            print("  ", h)


if __name__ == "__main__":
    a = sys.argv
    main(check="--check" in a, stl_only="--stl-only" in a,
         only=a[a.index("--only") + 1] if "--only" in a else None)
