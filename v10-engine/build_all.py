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
import tolerance_test  # noqa: E402
from common import check_printable_size, export, rot_z  # noqa: E402

import drawings  # noqa: E402
import render  # noqa: E402

R = os.path.join(ROOT, "renders")


def parts():
    L = assembly.libs()
    cr, mp, bl, st, bs = L["crank"], L["rp"], L["block"], L["style"], L["base"]
    # (file name, shape in print orientation, qty per engine, preview colour)
    return [
        ("00_fit_check_optional", tolerance_test.build(), 1, "white"),
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
        ("10_cylinder_head", block.print_bank(st["head"]), 2, "block"),
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
        # printable stand-ins so the mechanism can be tested before the CNC parts arrive
        ("P1_proto_split_crankpin", crank.print_pin(cr["pin"]), 5, "orange"),
        ("P2_proto_main_shaft", crank.print_shaft(cr["shaft"]), 2, "orange"),
        # machined / cut steel and aluminium parts (STEP for the machine shop)
        ("M01_split_crankpin", cr["pin"], 5, "steel"),
        ("M02_main_shaft", cr["shaft"], 2, "steel"),
        ("M03_guide_rail", mp["rail"], 10, "steel"),
        ("M04_pulley_spacer", drive.spacer(), 1, "steel"),
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
        export(shape, name)
        ok, line = check_printable_size(shape, name)
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

    # assembly previews
    eng = assembly.engine(0.0)
    render.render([(s, c) for _, s, c in eng], os.path.join(R, "20_engine_phase1_iso.png"),
                  view="iso", title="Phase 1 core engine - crank angle 0 (cyl 1 firing)")
    render.render([(s, c) for _, s, c in eng], os.path.join(R, "21_engine_phase1_front.png"),
                  view="front", title="Phase 1 - front view (90 deg V)")
    render.render([(s, c) for _, s, c in eng], os.path.join(R, "22_engine_phase1_cutaway_side.png"),
                  view=((0.25, -1.0, 0.35), (0, 0, 1)), title="Phase 1 - cut-away windows (bank A side)")
    full = [(s, c) for _, s, c in eng + assembly.drive_and_base()]
    render.render(full, os.path.join(R, "40_engine_on_base_iso.png"), view="iso",
                  title="Phase 2 - engine on display base")
    render.render(full, os.path.join(R, "41_engine_on_base_rear.png"), view=((-1.0, 0.7, 0.35), (0, 0, 1)),
                  title="Phase 2 - rear control panel")
    drv = [(s, c) for n, s, c in eng + assembly.drive_and_base()
           if not n.startswith(("base_", "panel_", "front_cover", "bank_"))]
    render.render(drv, os.path.join(R, "42_drive_train.png"), view=((1.0, -0.8, 0.2), (0, 0, 1)), zoom=1.2,
                  title="Phase 2 - belt drive (3:1, GT2 210 mm), base and cover hidden")
    under = [(s, c) for n, s, c in assembly.drive_and_base() if not n.startswith("panel_")]
    render.render(under, os.path.join(R, "43_base_inside.png"), view=((0.6, -0.8, -1.0), (0, 0, 1)),
                  title="Phase 2 - base from below, panels removed")
    inner = assembly.engine(0.0, with_blocks=False)
    inner = [(s, c) for n, s, c in inner if not n.startswith(("crankcase", "end_plate"))]
    render.render(inner, os.path.join(R, "23_mechanism_iso.png"), view="iso",
                  title="Mechanism only - crank, rods, pistons, rails")
    render.render(inner, os.path.join(R, "24_mechanism_front.png"), view="front",
                  title="Mechanism - front view")
    crank_only = [(s, c) for n, s, c in assembly.engine(0.0, with_blocks=False, with_rails=False)
                  if n.startswith(("crankpin", "segment", "end_web", "main_shaft"))]
    render.render(crank_only, os.path.join(R, "10_crank_assembly.png"), view="iso", zoom=1.6,
                  title="Built-up crankshaft (5 split pins, 72 deg even firing)")
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
