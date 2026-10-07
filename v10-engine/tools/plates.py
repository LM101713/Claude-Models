"""Fixed, named build plates for ONE engine on the Bambu Lab H2C.

    python tools/plates.py

Writes stl/plates/<Plate>.3mf (one multi-object 3MF per plate, parts already
placed on the bed, ready to open in Bambu Studio with YOUR printer / filament /
process profiles - no machine profile is invented here), renders/plates/*.png
(layout drawings) and docs/PLATES.md (the plate table with hours and grams).

Plate groups:  C = coupons (print first)    M = motion test    F = the rest.
Every plate holds parts of one layer height. Bed = config.PRINTER["bed"]
(single-nozzle mode); plates that would not fit the dual-nozzle bed are flagged.
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "cad"))
import config as C  # noqa: E402
import printcheck  # noqa: E402

BED = C.PRINTER["bed"]
DUAL = C.PRINTER["dual_bed"]
MARGIN = 6.0          # bed edge to first part (brim / skirt room)
GAP = 8.0             # between parts
from common import STL_DIR  # noqa: E402
OUT_3MF = os.path.join(STL_DIR, "plates")
OUT_PNG = os.path.join(ROOT, "renders", "plates")
EXPORT_GROUPS = ("C", "M")     # only coupons + motion test until a real engine has been built

# (plate name, description, [(part file name, qty), ...])
PLATES = [
    ("C1_coupons", "fit coupons T1-T10 - PRINT FIRST (PLA; T9b boots in the translucent filament)", [
        ("T1_hole_ladder", 1), ("T1b_test_peg", 2), ("T1c_peg_captive", 1), ("T2_insert_ladder", 1),
        ("T3_608_seats", 1), ("T3b_686_seats", 1), ("T4_piston_guide", 1), ("T4b_test_lug", 1),
        ("T4c_lug_slots", 1), ("T4d_wrist_pins", 1),
        ("T5_dpin_sockets", 1), ("T5b_magnets", 1), ("T6_end_plate_seat", 1),
        ("T7_crank_vblock", 2), ("T8_belt_feeler", 1), ("T9_boot_glow", 1), ("T9b_boot", 2), ("T10_header_flex", 1)]),
    ("M1_crank", "motion test: crank webs + segments, printed shafts", [
        ("05_crank_end_web", 2), ("06_crank_segment_54", 2), ("07_crank_segment_198", 2), ("P2_proto_main_shaft", 2)]),
    ("M2_rods_pins", "motion test: 10 con-rods, 5 printed crankpins", [("08_conrod", 10), ("P1_proto_split_crankpin", 5)]),
    ("M3_pistons", "motion test: 10 pistons", [("09_piston", 10)]),
    ("M4_bank_head", "motion test: one bank + one head", [("03_cylinder_bank", 1), ("10_cylinder_head", 1)]),
    ("M5_crankcase", "motion test: crankcase", [("01_crankcase", 1)]),
    ("M6_beam_plates", "motion test: valley beam + 2 end plates", [("02_valley_beam", 1), ("04_end_plate", 2)]),
    ("F1_bank_head_2", "second bank + head", [("03_cylinder_bank", 1), ("10_cylinder_head", 1)]),
    ("F2_base_front", "base front half (motor)", [("19_base_front", 1)]),
    ("F3_base_rear", "base rear half (controls, board)", [("20_base_rear", 1)]),
    ("F4_base_panel_1", "bottom panel 1", [("21_base_panel", 1)]),
    ("F5_base_panel_2", "bottom panel 2", [("21_base_panel", 1)]),
    ("F6_covers", "cam covers + side panels", [("11_cam_cover", 2), ("12_side_panel", 2)]),
    ("F7_frame_end_covers", "throttle frame + end covers", [("17_throttle_frame", 1), ("18_end_cover", 2)]),
    ("F8_exhausts_coils", "exhaust headers A + B, 10 coil packs", [("14_exhaust_bank_A", 1), ("15_exhaust_bank_B", 1), ("16_coil_pack", 10)]),
    ("F9_trumpets", "10 intake trumpets", [("13_intake_trumpet", 10)]),
]

if C.VARIANT == "v8":
    PLATES = [
        ("C1_coupons", "fit coupons T1-T10 - PRINT FIRST (PLA; T9b boots in the translucent filament)", [
            ("T1_hole_ladder", 1), ("T1b_test_peg", 2), ("T1c_peg_captive", 1), ("T2_insert_ladder", 1),
            ("T3_608_seats", 1), ("T3b_686_seats", 1), ("T4_piston_guide", 1), ("T4b_test_lug", 1),
            ("T4c_lug_slots", 1), ("T4d_wrist_pins", 1), ("T5_dpin_sockets", 1), ("T5b_magnets", 1),
            ("T6_end_plate_seat", 1), ("T7_crank_vblock", 2), ("T8_belt_feeler", 1), ("T9_boot_glow", 1),
            ("T9b_boot", 2), ("T10_header_flex", 1)]),
        ("M1_crank", "motion test: crank webs + 3 segments, printed shafts", [
            ("05_crank_end_web", 2), ("06_crank_segment_90", 1), ("07_crank_segment_180", 1), ("08_crank_segment_270", 1),
            ("P2_proto_main_shaft", 1), ("P2F_proto_main_shaft_front", 1)]),
        ("M2_rods_pins", "motion test: 8 con-rods, 4 printed crankpins", [("09_conrod", 8), ("P1_proto_crankpin", 4)]),
        ("M3_pistons", "motion test: 8 pistons", [("10_piston", 8)]),
        ("M4_bank_head", "motion test: one bank + head A", [("03_cylinder_bank", 1), ("30_cylinder_head_A", 1)]),
        ("M5_crankcase", "motion test: crankcase", [("01_crankcase", 1)]),
        ("M6_beam_plates", "motion test: valley beam + 2 end plates", [("02_valley_beam", 1), ("04_end_plate", 2)]),
        ("F1_bank_head_B", "second bank + head B (mirror)", [("03_cylinder_bank", 1), ("30B_cylinder_head_B", 1)]),
        ("F2_covers_boots_tb", "2 valve covers, 2 oil caps, throttle body", [("31_valve_cover", 2), ("31B_oil_cap", 2), ("36C_throttle_body", 1)]),
        ("F2b_boots", "8 translucent boots (5th filament)", [("32_plug_boot", 8)]),
        ("F3_primaries_plates", "8 header primaries (4 + 4 mirror), 2 flange plates", [
            ("33_header_primary_A", 4), ("33B_header_primary_B", 4), ("34_header_plate_A", 1), ("34B_header_plate_B", 1)]),
        ("F4_collectors", "2 collectors (mirror pair)", [("35_collector_A", 1), ("35B_collector_B", 1)]),
        ("F5_intake_lid", "intake lid", [("36_intake_lid", 1)]),
        ("F6_intake_base", "intake base", [("36B_intake_base", 1)]),
        ("F7_pan", "oil pan", [("40_oil_pan", 1)]),
        ("F8_panel_bell_damper", "pan floor panel, bellhousing, damper", [("41_pan_floor_panel", 1), ("42_bellhousing", 1), ("44_damper", 1)]),
        ("F9_front", "front cover + accessory module", [("43_front_cover", 1), ("45_accessory_module", 1)]),
        ("F10_stand_plate", "stand plate (single-nozzle mode)", [("46_stand_plate", 1)]),
        ("F11_brackets_plinth", "4 brackets + controls plinth", [("47_bracket", 2), ("47B_bracket_mirror", 2), ("48_controls_plinth", 1)]),
    ]


def load(name):
    m = trimesh.load(os.path.join(STL_DIR, name + ".stl"), force="mesh")
    m.apply_translation(-m.bounds[0])          # min corner at the origin, sitting on z = 0
    return m


def pack(items):
    """Shelf packing with 90 deg rotation. items: (name, w, d). Returns
    [(name, x, y, w, d, rotated)] or raises if the plate does not fit."""
    items = sorted(items, key=lambda it: -max(it[1], it[2]))
    shelves = []                                 # dict(y, h, x)
    placed = []
    for name, w, d in items:
        best = None
        for rot in (False, True):
            ww, dd = (d, w) if rot else (w, d)
            if ww > BED[0] - 2 * MARGIN or dd > BED[1] - 2 * MARGIN:
                continue
            for sh in shelves:
                if dd <= sh["h"] and sh["x"] + ww <= BED[0] - MARGIN:
                    cand = (sh["h"] - dd, sh, ww, dd, rot)       # least wasted height
                    if best is None or cand[0] < best[0]:
                        best = cand
        if best is None:
            for rot in (False, True):
                ww, dd = (d, w) if rot else (w, d)
                if ww > BED[0] - 2 * MARGIN or dd > BED[1] - 2 * MARGIN:
                    continue
                y = MARGIN + sum(sh["h"] + GAP for sh in shelves)
                if y + dd <= BED[1] - MARGIN:
                    sh = dict(y=y, h=dd, x=MARGIN)
                    shelves.append(sh)
                    best = (0, sh, ww, dd, rot)
                    break
        if best is None:
            raise SystemExit(f"plate does not fit the {BED[0]:.0f} x {BED[1]:.0f} bed: {name}")
        _, sh, ww, dd, rot = best
        placed.append((name, sh["x"], sh["y"], ww, dd, rot))
        sh["x"] += ww + GAP
    return placed


def main():
    os.makedirs(OUT_3MF, exist_ok=True)
    os.makedirs(OUT_PNG, exist_ok=True)
    res = json.load(open(os.path.join(ROOT, "docs", "print_results.json")))
    rows = []
    for pname, desc, parts in PLATES:
        if not pname.startswith(EXPORT_GROUPS):
            rows.append((pname, desc + " (planned, NOT exported: design unproven)", "ASA", "-",
                         ", ".join(f"{q} x {n}" for n, q in parts), 0.0, 0.0, True))
            continue
        meshes = {n: load(n) for n, _ in parts}
        layers = {printcheck.settings_for(n)[1] for n, _ in parts}
        mats = {printcheck.settings_for(n)[0] for n, _ in parts}
        assert len(layers) == 1, f"{pname}: mixed layer heights {layers}"
        items = []
        for n, q in parts:
            e = meshes[n].bounds[1] - meshes[n].bounds[0]
            for k in range(q):
                items.append((f"{n}#{k + 1}", float(e[0]), float(e[1])))
        placed = pack(items)
        scene = trimesh.Scene()
        hours = grams = 0.0
        max_x = 0.0
        fig, ax = plt.subplots(figsize=(6.5, 6.5 * BED[1] / BED[0]))
        ax.add_patch(Rectangle((0, 0), BED[0], BED[1], fill=False, lw=1.5, ec="#333"))
        ax.add_patch(Rectangle((0, 0), DUAL[0], DUAL[1], fill=False, lw=0.8, ec="#999", ls="--"))
        for label, x, y, w, d, rot in placed:
            n = label.split("#")[0]
            m = meshes[n].copy()
            if rot:
                m.apply_transform(trimesh.transformations.rotation_matrix(1.5707963, (0, 0, 1)))
                m.apply_translation(-m.bounds[0])
            m.apply_translation((x, y, 0))
            scene.add_geometry(m, node_name=label, geom_name=label)
            r = res.get(n, {})
            hours += r.get("hours", 0.0)
            grams += r.get("grams", 0.0)
            max_x = max(max_x, x + w)
            ax.add_patch(Rectangle((x, y), w, d, fc="#cfd8e3", ec="#1b1d22", lw=0.8))
            ax.text(x + w / 2, y + d / 2, n.replace("_", "\n", 1), ha="center", va="center", fontsize=6)
        ax.set_xlim(-5, BED[0] + 5); ax.set_ylim(-5, BED[1] + 5); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{pname}  ({C.PRINTER['name']} {BED[0]:.0f} x {BED[1]:.0f}, dashed = dual-nozzle bed)", fontsize=9)
        fig.savefig(os.path.join(OUT_PNG, pname + ".png"), dpi=130, bbox_inches="tight")
        plt.close(fig)
        # verify: on bed, no overlap (shelf packing guarantees it; check anyway)
        for i, a in enumerate(placed):
            assert a[1] + a[3] <= BED[0] - MARGIN + 1e-6 and a[2] + a[4] <= BED[1] - MARGIN + 1e-6, (pname, a)
            for b in placed[i + 1:]:
                sep = a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1] or a[2] + a[4] <= b[2] or b[2] + b[4] <= a[2]
                assert sep, (pname, a[0], b[0])
        with open(os.path.join(OUT_3MF, pname + ".3mf"), "wb") as f:
            f.write(scene.export(file_type="3mf"))
        dual_ok = all(a[1] + a[3] <= DUAL[0] - MARGIN and a[2] + a[4] <= DUAL[1] - MARGIN for a in placed)
        rows.append((pname, desc, mats.pop(), layers.pop(), ", ".join(f"{q} x {n}" for n, q in parts), hours, grams, dual_ok))
        print(f"{pname:22s} {len(placed):3d} parts  {hours:5.1f} h  {grams:6.0f} g  {'' if dual_ok else 'single-nozzle mode only'}")

    L = ["# Build plates (one engine)", "",
         f"Generated by `tools/plates.py` for the **{C.PRINTER['name']}**, bed {BED[0]:.0f} x {BED[1]:.0f} mm in "
         f"single-nozzle mode (dual-nozzle mode is {DUAL[0]:.0f} x {DUAL[1]:.0f}; plates marked * do not fit it). "
         "One 3MF per plate in `stl/plates/`, parts placed and ready to slice with your own printer, filament and "
         "process profiles; layout drawings in `renders/plates/`. Times/grams are PrusaSlicer estimates with the "
         "production settings (`docs/PRINT_REPORT.md`).", "",
         "**Print order:** C1 first (fits), then M1-M6 (motion test), then F1-F9. Material: coupons and motion test "
         "in PLA (or PETG for the printed pins/shafts); production parts in ASA. "
         "The A1 Mini (180 mm) can print C1's parts individually and plates M1-M3 and F9; everything else needs the H2C/H2S.", "",
         "| Plate | Contents | Material (production) | Layer | Parts | Hours | Grams |", "|---|---|---|---|---|---|---|"]
    for pname, desc, mat, layer, parts, h, g, dual_ok in rows:
        L.append(f"| **{pname}**{'' if dual_ok else ' *'} | {desc} | {mat} | {layer} | {parts} | {h:.1f} | {g:.0f} |" if layer != "-"
                 else f"| {pname} | {desc} | | | {parts} | | |")
    L += [f"| | **total** | | | | **{sum(r[5] for r in rows):.0f}** | **{sum(r[6] for r in rows):.0f}** |", ""]
    with open(os.path.join(ROOT, "docs", "PLATES.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("wrote docs/PLATES.md,", len(rows), "plates")


if __name__ == "__main__":
    main()
