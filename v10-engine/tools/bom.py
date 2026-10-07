"""Bill of materials for one engine and for the 50-unit order.

Printed-part times and grams come from tools/printcheck.py (docs/print_results.json,
sliced with the production settings). Screw, insert and magnet counts are
derived from the same CAD lists that cut the holes, so they cannot drift from
the model. Writes docs/BOM.md, docs/BOM.csv and docs/SHOPPING_LIST.txt.

    python tools/bom.py
"""

import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import config as C  # noqa: E402

ASA_PER_KG = 25.0          # USD, 1 kg spools (Bambu / Polymaker / eSun ASA)
PRINTER_COST_PER_H = 0.30  # USD: electricity + wear parts per printer hour
UNITS = 50


def hardware_counts_v8():
    """M3x8 screws, M3 inserts and 6x3 magnets per V8 engine, by location."""
    import block
    import pan_v8
    import stand_v8
    nb = len(block.bank_between_x())
    n_panel = len(pan_v8.panel_screws())
    n_br = len(stand_v8.bracket_positions())
    screws = {
        "banks -> crankcase / beam (block end screws)": 2 * (2 * len(block.block_end_screws_x())),
        "end plates": 2 * len(block.END_PLATE_SCREWS),
        "heads -> banks (head screws)": 2 * nb * len(C.HEAD_SCREW_Y),
        "header flange plates -> heads": 2 * 2,
        "crankpin ends (into the steel pins)": 2 * C.N_THROWS,
        "main shaft flanges -> end webs": 2 * len(C.SHAFT_FLANGE_BOLT_ANGLES),
        "pan skin -> crankcase": len(C.PAN_SCREWS),
        "pan floor panel (captive)": n_panel,
        "controller board standoffs": 4,
        "brackets -> pan": 2 * n_br,
        "brackets -> stand plate": 2 * n_br,
        "motor -> bulkhead": 4,
    }
    inserts = {
        "crankcase (bank ends, end plates, pan)": 2 * len(block.block_end_screws_x()) + 2 * len(block.CASE_END_SCREWS) + len(C.PAN_SCREWS),
        "valley beam (banks, end plates)": 2 * nb + 2 * len(block.BEAM_END_SCREWS),
        "cylinder banks (head screws)": 2 * nb * len(C.HEAD_SCREW_Y),
        "crank end webs (main shafts)": 2 * len(C.SHAFT_FLANGE_BOLT_ANGLES),
        "cylinder heads (flange plates)": 2 * 2,
        "pan (panel bosses, bracket bosses)": n_panel + 2 * n_br,
        "floor panel (board standoffs)": 4,
        "bracket feet": 2 * n_br,
    }
    magnets = {
        "valve covers (head + cover)": 2 * 2 * 4,
        "intake lid (lid + base)": 2 * len(C.INTAKE["magnet_xy"]),
        "front cover (end plate + cover)": 2 * len(C.COVER_MAGNETS),
        "bellhousing (end plate + bell)": 2 * len(C.COVER_MAGNETS),
        "accessory module (cover + module)": 2 * len(C.FRONT_COVER["module_magnets"]),
        "hall magnet (one in each end web)": 2,
    }
    return screws, inserts, magnets


def hardware_counts():
    if C.VARIANT == "v8":
        return hardware_counts_v8()
    """Fasteners and magnets, counted from the CAD feature lists."""
    import block
    import base
    import styling
    nb = len(block.bank_between_x())
    screws = {
        "cylinder bank -> crankcase / valley beam": 2 * (nb + len(block.block_end_screws_x())),
        "cylinder head -> bank deck": 2 * len(styling.BETWEEN_X) * len(C.HEAD_SCREW_Y),
        "end plate -> crankcase / valley beam": 2 * len(block.END_PLATE_SCREWS),
        "crankcase -> base": len(base.CASE_SCREWS),
        "base halves joint": len(C.BASE_JOINT_SCREWS),
        "bottom panels": 2 * len(base._panel_screws(True)),
        "controller board standoffs": 4,
        "crankpin ends (into the steel pins)": 2 * C.N_THROWS,
        "main shaft flanges -> end webs": 2 * len(C.SHAFT_FLANGE_BOLT_ANGLES),
        "exhaust port flanges -> heads": 2 * C.N_THROWS,
        "motor -> bulkhead": 4,
    }
    inserts = {
        "crankcase (bank ends, end plates, base)": 2 * len(block.block_end_screws_x()) + 2 * len(block.CASE_END_SCREWS)
        + len(block.BASE_INSERTS),
        "valley beam (banks, end plates)": 2 * nb + 2 * len(block.BEAM_END_SCREWS),
        "cylinder banks (head screws)": 2 * nb * len(C.HEAD_SCREW_Y),
        "crank end webs (main shafts)": 2 * len(C.SHAFT_FLANGE_BOLT_ANGLES),
        "cylinder heads (exhaust)": 2 * C.N_THROWS,
        "base (joint, panel pillars, board standoffs)": len(C.BASE_JOINT_SCREWS) + 2 * len(base._panel_screws(True)) + 4,
    }
    cam = len((C.BANK_A_CYL_X[0], C.BANK_A_CYL_X[1], C.BANK_A_CYL_X[3], C.BANK_A_CYL_X[4]))
    magnets = {
        "cam covers (head + cover)": 2 * 2 * cam,
        "side panels (bank + panel)": 2 * 2 * nb,
        "end covers (end plate + cover)": 2 * 2 * len(C.COVER_MAGNETS),
        "hall magnet (one in each end web)": 2,
    }
    return screws, inserts, magnets


def printed_parts():
    import build_all
    names = [(n, q) for n, _, q, _ in build_all.parts() if not n.startswith(("M0", "P1", "P2", "00_"))]
    res = {}
    path = os.path.join(ROOT, "docs", "print_results.json")
    if os.path.exists(path):
        res = json.load(open(path))
    rows = []
    for n, q in names:
        r = res.get(n, {})
        rows.append(dict(name=n, qty=q, material=r.get("material", "ASA"), layer=r.get("layer"), walls=r.get("walls"),
                         infill=r.get("infill"), hours=r.get("hours", 0.0), grams=r.get("grams", 0.0)))
    return rows


# Machined parts: (part, qty per engine, material / process, each x1, each in a 50-unit batch)
MACHINED = [
    ("M01 split crankpin (drawing M01)", 5, "416 / 303 stainless, turned + offset journal, ground journals, tapped M3",
     45.0, 9.0),
    ("M02 main shaft (drawing M02)", 2, "303 stainless, turned, 3-hole flange, flat", 35.0, 8.0),
    ("M03 guide rail 3 x 57 mm (drawing M03)", C.N_CYL, "cut from 3 mm h6 ground stainless rod, ends chamfered", 0.8, 0.5),
    ("M04 pulley spacer (drawing M04)", 1, "303 stainless, parted off", 8.0, 1.5),
    ("M06 bearing spacer ring 6 x 7.5 x 0.75 (drawing M06)", 2 * C.N_THROWS, "303 stainless, parted off, deburred", 3.0, 0.4),
]
OPTIONAL = [
    *([("M05 intake trumpet, machined aluminium (drawing M05) - optional upgrade for the printed 13", 10,
     "6061-T6, turned, clear anodised", 25.0, 5.0)] if C.VARIANT == "v10" else []),
]

# Purchased parts: (id, item, exact spec / search term, qty per engine, each x1, each x50, buy-ahead spares %)
def purchased(screws, inserts, magnets):
    s = sum(screws.values())
    i = sum(inserts.values())
    m = sum(magnets.values())
    return [
        # mechanical
        ("H1", "Ball bearing 608ZZ", "8x22x7 mm, metal shields (ZZ, not 2RS - low drag)", 2, 0.80, 0.35, 5),
        ("H2", "Ball bearing 686ZZ", "6x13x5 mm, metal shields", 2 * C.N_THROWS, 0.90, 0.40, 5),
        ("H3", "Sintered bronze bushing", "3x5x4 mm (ID 3, OD 5, length 4), oil-impregnated", 3 * C.N_CYL, 0.20, 0.08, 10),
        ("H4", "Wrist pin", "3x20 mm dowel pin, stainless, ISO 8734 m6", C.N_CYL, 0.15, 0.06, 10),
        ("H5", "Heat-set insert", "M3 x 5.7 mm brass, 4.6 mm OD (for a 4.0 mm hole)", i, 0.08, 0.03, 10),
        ("H6", "Socket head cap screw", "M3 x 8 mm, ISO 4762, A2 stainless - the ONLY screw size in the engine", s,
         0.06, 0.025, 10),
        ("H7", "Neodymium disc magnet", "6 x 3 mm N52, nickel plated", m, 0.10, 0.05, 10),
        ("H8", "GT2 pulley 60T", "60 teeth, 8 mm bore, 6 mm belt, 2 grub screws, ~16 mm wide", 1, 6.00, 4.00, 2),
        ("H9", "GT2 pulley 20T", "20 teeth, 5 mm bore, 6 mm belt, 2 grub screws", 1, 2.00, 1.20, 2),
        ("H10", "GT2 closed belt", "GT2-6 mm, 210 mm (105 teeth); 220 mm also fits the motor slots", 1, 2.50, 1.20, 10),
        ("H11", "Rubber feet", "20 mm round self-adhesive, 3-5 mm thick", 8, 0.15, 0.08, 10),
        ("H12", "Threadlocker", "Vibra-TITE VC-3 (plastic-safe, removable), 1 drop per screw", 0.02, 12.00, 12.00, 0),
        ("H13", "Light oil", "clock / sewing-machine oil, 1 drop per rail", 0.01, 6.00, 6.00, 0),
        ("H14", "Edition plate", "custom engraved metal nameplate 120 x 30 mm, 0.8 mm brushed aluminium (black "
         "anodised, laser-engraved) or brass, R3 corners, self-adhesive (3M 467MP), numbered 01-50 - "
         "drawings/H14_edition_plate.png", 1, 12.00, 5.00, 4),
        # electronics (see docs/ELECTRONICS.md)
        ("E1", "ESP32 board", "Espressif ESP32-DevKitC-32E (ESP32-WROOM-32E, 38 pin)", 1, 10.00, 9.00, 4),
        ("E2", "Stepper driver", "BIGTREETECH TMC2209 V1.3", 1, 6.00, 4.50, 4),
        ("E3", "5 V regulator", "Pololu D24V22F5 (5 V 2.5 A)", 1, 11.00, 9.50, 4),
        ("E4", "Level shifter", "TI SN74AHCT125N DIP-14 + DIP-14 socket", 1, 0.90, 0.60, 4),
        ("E5", "Hall switch", "TI DRV5033AJQLPG (TO-92, omnipolar)", 1, 0.80, 0.60, 10),
        ("E6", "Power supply", "Mean Well GST25A12-P1J 12 V 2.08 A + IEC C7 cord (customer's country)", 1, 17.00, 14.00, 2),
        ("E7", "DC panel jack", "5.5 x 2.1 mm, 11 mm thread, with nut", 1, 1.50, 0.80, 4),
        ("E8", "Power rocker", "round 20 mm illuminated (KCD1 round, 3 pin, 12 V lamp)", 1, 1.50, 0.90, 4),
        ("E9", "START button", "16 mm stainless momentary 1NO, 12 V ring LED", 1, 3.50, 2.50, 4),
        ("E10", "Speed pot + knob", "10 k linear, 16 mm, M7 bushing, 6 mm shaft + 20 mm aluminium knob", 1, 3.50, 2.50, 4),
        ("E11", "Stepper motor", "StepperOnline 17HS4401S (1.7 A, 40 Ncm, 40 mm)", 1, 12.00, 10.00, 2),
        ("E12", "LED strip", "BTF-LIGHTING WS2812B 60 LED/m, black PCB, IP30, 5 V (m)", round(2 * (C.LED_STRIP["n"] + getattr(C, "BOOT_STRIP", {"n": 0})["n"]) / 60.0 + 0.05, 2), 4.00, 3.20, 10),
        ("E13", "Prototype board", "70 x 90 mm double-sided FR4", 1, 0.80, 0.40, 4),
        ("E14", "JST XH set", "headers 2/3/3/3/3/4/4 pin + housings + pre-crimped leads", 1, 3.00, 2.00, 4),
        ("E15", "Small parts set", "RXEF200, 1N5822, P6KE18A, 1N5817, 220uF 35V, 470uF 16V, 3x100nF/10nF, "
         "1k x2, 10k x2, 330R x2, 100k, 2N3904, female headers", 1, 3.50, 2.00, 4),
        ("E16", "Wire + sleeving set", "silicone 20/22/24/26 AWG, 6 mm braided sleeve, heat-shrink, 4.8 mm spades", 1,
         3.00, 2.00, 4),
        ("E17", "Cable ties", "100 mm, small", 12, 0.02, 0.01, 10),
    ]


def main():
    screws, inserts, magnets = hardware_counts()
    pp = printed_parts()
    buy = purchased(screws, inserts, magnets)

    L = ["# Bill of materials", "",
         f"One engine and the {UNITS}-unit order. Generated by `tools/bom.py` (re-run after any change). "
         "Printed-part times and grams are PrusaSlicer estimates with the production settings "
         "(`tools/printcheck.py`); Bambu Studio is typically within +/-20 %. Prices are typical 2026 USD "
         "(x1 = single prototype, x50 = per piece when buying for 50 engines).", ""]

    # printed
    L += ["## 1. Printed parts (all ASA)", "",
          "| Part | Qty | Layer | Walls | Infill | h each | g each | h / engine | g / engine |",
          "|---|---|---|---|---|---|---|---|---|"]
    th = tg = 0.0
    for r in pp:
        th += r["hours"] * r["qty"]
        tg += r["grams"] * r["qty"]
        L.append(f"| {r['name']} | {r['qty']} | {r['layer']} | {r['walls']} | {r['infill']}% | {r['hours']:.2f} | "
                 f"{r['grams']:.0f} | {r['hours'] * r['qty']:.1f} | {r['grams'] * r['qty']:.0f} |")
    filament_cost = tg / 1000 * ASA_PER_KG
    print_cost = filament_cost + th * PRINTER_COST_PER_H
    L += [f"| **Total** | {sum(r['qty'] for r in pp)} parts | | | | | | **{th:.0f} h** | **{tg / 1000:.2f} kg** |", "",
          f"Filament: {tg / 1000:.2f} kg ASA = ${filament_cost:.0f} per engine at ${ASA_PER_KG:.0f}/kg "
          f"({tg * UNITS / 1000:.0f} kg for {UNITS} engines; buy {math.ceil(tg * UNITS * 1.08 / 1000)} x 1 kg spools "
          f"incl. 8 % for purge, brims and reprints). Printer time {th:.0f} h per engine "
          f"({th * UNITS:,.0f} printer-hours for {UNITS}; see PRODUCTION_PLAN.md).", ""]

    # machined
    L += ["## 2. Machined parts (order from the drawings in `drawings/`, STEP files in `stl/`)", "",
          "| Part | Qty | Material / process | Each x1 | Each x50 | Per engine x1 | Per engine x50 |",
          "|---|---|---|---|---|---|---|"]
    m1 = m50 = 0.0
    for name, q, mat, c1, c50 in MACHINED:
        m1 += q * c1
        m50 += q * c50
        L.append(f"| {name} | {q} | {mat} | ${c1:.2f} | ${c50:.2f} | ${q * c1:.2f} | ${q * c50:.2f} |")
    L.append(f"| **Total** | | | | | **${m1:.2f}** | **${m50:.2f}** |")
    for name, q, mat, c1, c50 in OPTIONAL:
        L.append(f"| *(optional)* {name} | {q} | {mat} | ${c1:.2f} | ${c50:.2f} | ${q * c1:.2f} | ${q * c50:.2f} |")
    L.append("")

    # purchased
    L += ["## 3. Purchased parts", "",
          "| ID | Item | Exact spec | Qty / engine | Each x1 | Each x50 | Per engine x1 | Per engine x50 | Order for 50 (incl. spares) |",
          "|---|---|---|---|---|---|---|---|---|"]
    b1 = b50 = 0.0
    for pid, item, spec, q, c1, c50, spare in buy:
        b1 += q * c1
        b50 += q * c50
        order = q * UNITS * (1 + spare / 100.0)
        order_s = f"{order:.0f}" if q >= 1 else ("1" if pid in ("H12", "H13") else f"{order:.0f} m")
        if pid == "H12":
            order_s = "4 bottles"
        if pid == "H13":
            order_s = "1 bottle"
        if pid == "E12":
            order_s = f"{order:.1f} m (= {int(order / 5) + 1} x 5 m reels)"
        L.append(f"| {pid} | {item} | {spec} | {q:g} | ${c1:.2f} | ${c50:.2f} | ${q * c1:.2f} | ${q * c50:.2f} | {order_s} |")
    L.append(f"| | **Total purchased** | | | | | **${b1:.2f}** | **${b50:.2f}** | |")
    L += ["", "### Where the screws, inserts and magnets go (counted from the CAD)", "",
          "| M3 x 8 screws | Qty |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in screws.items()] + [f"| **total** | **{sum(screws.values())}** |", ""]
    L += ["| Heat-set inserts | Qty |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in inserts.items()] + [f"| **total** | **{sum(inserts.values())}** |", ""]
    L += ["| 6 x 3 mm magnets | Qty |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in magnets.items()] + [f"| **total** | **{sum(magnets.values())}** |", ""]

    # totals
    t1 = print_cost + m1 + b1
    t50 = print_cost + m50 + b50
    L += ["## 4. Cost per engine", "",
          "| | x1 (prototype) | x50 (per engine) |", "|---|---|---|",
          f"| Printed parts (filament ${filament_cost:.0f} + printer time ${th * PRINTER_COST_PER_H:.0f}) | "
          f"${print_cost:.0f} | ${print_cost:.0f} |",
          f"| Machined parts | ${m1:.0f} | ${m50:.0f} |",
          f"| Purchased parts | ${b1:.0f} | ${b50:.0f} |",
          f"| **Materials total** | **${t1:.0f}** | **${t50:.0f}** |",
          f"| Optional machined aluminium trumpets | +${sum(q * c for _, q, _, c, _ in OPTIONAL):.0f} | "
          f"+${sum(q * c for _, q, _, _, c in OPTIONAL):.0f} |",
          "", f"Materials for the whole order: about **${t50 * UNITS:,.0f}** "
          f"(+${sum(q * c for _, q, _, _, c in OPTIONAL) * UNITS:,.0f} with machined trumpets). Not included: "
          "labour (see PRODUCTION_PLAN.md), packaging, shipping, the printers themselves.", ""]
    with open(os.path.join(ROOT, "docs", "BOM.md"), "w") as f:
        f.write("\n".join(L) + "\n")

    with open(os.path.join(ROOT, "docs", "BOM.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "id / part", "item", "spec", "qty per engine", "each x1 USD", "each x50 USD",
                    "order for 50 incl. spares"])
        for r in pp:
            w.writerow(["printed", r["name"], "ASA print", f"{r['layer']} mm, {r['walls']} walls, {r['infill']}%",
                        r["qty"], f"{r['grams'] / 1000 * ASA_PER_KG:.2f}", f"{r['grams'] / 1000 * ASA_PER_KG:.2f}",
                        r["qty"] * UNITS])
        for name, q, mat, c1, c50 in MACHINED + OPTIONAL:
            w.writerow(["machined", name.split(" ")[0], name, mat, q, c1, c50, q * UNITS])
        for pid, item, spec, q, c1, c50, spare in buy:
            w.writerow(["purchased", pid, item, spec, q, c1, c50, round(q * UNITS * (1 + spare / 100.0), 1)])

    # shopping list with search links
    S = [f"{C.VARIANT.upper()} ENGINE - SHOPPING LIST (generated by tools/bom.py from the BOM)",
         "Search links: pick a listing that matches the exact spec. Quantities: ONE engine / 50 engines (with spares).",
         ""]
    for pid, item, spec, q, c1, c50, spare in buy:
        term = spec.split(",")[0].replace(" ", "+")
        n50 = q * UNITS * (1 + spare / 100.0)
        S.append(f"{pid}. {item} - {spec}")
        S.append(f"    qty: {q:g} per engine / {n50:.0f} for 50")
        S.append(f"    https://www.amazon.com/s?k={term}")
        S.append("")
    qty = ", ".join(f"{n.split()[0]} x{q * UNITS}" for n, q, *_ in MACHINED)
    S += ["MACHINED PARTS: send drawings/machined_parts.pdf (M01-M06) + stl/M0x_*.step to a CNC service (Xometry, PCBWay,",
          f"JLCCNC, a local shop). Quantities for 50 engines: {qty} (+5 % spares).",
          "Optional: M05 machined aluminium trumpets x500."]
    with open(os.path.join(ROOT, "docs", "SHOPPING_LIST.txt"), "w") as f:
        f.write("\n".join(S) + "\n")
    print("\n".join(L[-14:]))
    print("wrote docs/BOM.md, docs/BOM.csv, docs/SHOPPING_LIST.txt")


if __name__ == "__main__":
    main()
