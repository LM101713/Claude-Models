"""PROTOTYPE bill of materials: enough for 1-2 engines plus spares and a few
alternative sizes for fit testing. This is the ONLY order to place until the
first engine runs. (The 50-unit BOM is deliberately not built yet.)

    python tools/proto_bom.py   -> docs/PROTO_BOM.md, docs/PROTO_BOM.csv
"""

import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import config as C  # noqa: E402
import bom  # noqa: E402

ENGINES = 2            # the prototype order covers two engines
SPARE = 0.25           # +25 % on consumables (the fit coupons eat inserts, magnets, bearings)

# extra items only for the test phase: (part, spec, qty, supplier, link, unit price)
TEST_EXTRAS = [
    ("Heat-set insert, alternative", "M3 x 4 mm short, 4.6 OD (if 5.7 mm inserts prove too long for the covers)", 50,
     "Amazon / CNC Kitchen", "https://www.amazon.com/s?k=M3+heat+set+insert+4.6mm", 0.08),
    ("Heat-set insert, alternative", "M3 x 5 mm, 5.0 OD long series (if pull-out is weak)", 50,
     "Amazon", "https://www.amazon.com/s?k=M3+heat+set+insert+5mm", 0.08),
    ("Screws, alternative lengths", "M3 x 6 and M3 x 10 SHCS A2, 50 each (fit testing around the single 8 mm size)", 100,
     "Amazon / Bolt Depot", "https://www.amazon.com/s?k=M3+socket+head+cap+screw+assortment+A2", 0.06),
    ("GT2 belt, alternative length", "GT2-6 mm closed, 220 mm (110 T) - the slots accept it; also the SPARE belt", 2,
     "Amazon", "https://www.amazon.com/s?k=GT2+6mm+closed+belt+220mm", 2.50),
    ("Stainless rod 3 mm", "3 mm h6 ground stainless rod, 500 mm, for the 20 guide rails (M03) + coupons", 2,
     "McMaster / Amazon", "https://www.amazon.com/s?k=3mm+stainless+steel+rod+h6", 6.00),
    ("Pin gauges / drill shanks", "2.5-8.5 mm in 0.1 mm steps (or a cheap pin gauge set) to measure printed holes", 1,
     "Amazon", "https://www.amazon.com/s?k=pin+gauge+set+metric+minus", 35.00),
    ("Digital calipers", "150 mm, 0.01 mm", 1, "Amazon", "https://www.amazon.com/s?k=digital+caliper+150mm", 20.00),
    ("Dial indicator + magnetic base", "0.01 mm, for crank runout on the T7 V-blocks", 1,
     "Amazon", "https://www.amazon.com/s?k=dial+indicator+magnetic+base", 25.00),
    ("Soldering-iron insert tips", "M3 heat-set tip for the iron", 1, "Amazon", "https://www.amazon.com/s?k=heat+set+insert+soldering+tip+M3", 10.00),
    ("Arbor press or vise soft jaws", "1 t arbor press, or aluminium soft jaws for the bench vise", 1,
     "Amazon / Harbor Freight", "https://www.amazon.com/s?k=1+ton+arbor+press", 60.00),
]

FILAMENT_PLA_KG = 2.0      # coupons + motion-test prints
FILAMENT_PETG_KG = 1.0     # printed pins, shafts (and rods if you prefer) for the motion test


def filament_by_slot(engines):
    res = json.load(open(os.path.join(ROOT, "docs", "print_results.json")))
    import build_all
    grams = {}
    for n, _, q, _ in build_all.parts():
        if n[:2].isdigit() and n in res:
            slot = next((k for k, v in C.PALETTE.items() if n.startswith(v["parts"])), "hidden")
            grams[slot] = grams.get(slot, 0.0) + res[n]["grams"] * q
    return {k: v * engines for k, v in grams.items()}


def main():
    screws, inserts, magnets = bom.hardware_counts()
    buy = bom.purchased(screws, inserts, magnets)
    rows = []   # (section, part, part no, spec, qty/engine, qty order, supplier, link, unit, total)

    def supplier_for(pid):
        if pid in ("E1", "E2", "E3", "E4", "E5", "E6", "E13", "E14", "E15"):
            return "Digi-Key / Mouser (or Amazon)"
        if pid == "E11":
            return "StepperOnline"
        if pid == "H14":
            return "local engraver / online nameplate shop"
        return "Amazon"

    for pid, item, spec, q, c1, c50, spare in buy:
        if pid == "H14":
            qty = 2                                  # two plates (01 and 02) for the two prototypes
        elif q < 1:
            qty = 1 if pid in ("H12", "H13") else math.ceil(q * ENGINES * 2) # consumables / per-metre items
        else:
            qty = math.ceil(q * ENGINES * (1 + SPARE))
        term = spec.split(",")[0].replace(" ", "+")
        rows.append(("Purchased", item, pid, spec, q, qty, supplier_for(pid), f"https://www.amazon.com/s?k={term}",
                     c1, qty * c1))
    for item, spec, qty, sup, link, unit in TEST_EXTRAS:
        rows.append(("Test phase only", item, "-", spec, "-", qty, sup, link, unit, qty * unit))

    # steel parts: NOT ordered yet (printed PETG stand-ins first), except the rail rod above
    # filament
    slots = filament_by_slot(ENGINES)
    for k, g in slots.items():
        kg = math.ceil(g / 1000 * 1.15)              # +15 % purge, brims, failed prints
        rows.append(("Filament", f"ASA, {C.PALETTE[k]['name']}", "-", "1 kg spools, ONE colour lot per slot", f"{g / ENGINES / 1000:.2f} kg",
                     kg, "Bambu / Polymaker / eSun", "https://www.amazon.com/s?k=ASA+filament+1kg", 25.0, kg * 25.0))
    rows.append(("Filament", "PLA (coupons + motion test)", "-", "any PLA, 0.4 mm nozzle", "-", int(FILAMENT_PLA_KG),
                 "Bambu / any", "https://www.amazon.com/s?k=PLA+filament+1kg", 20.0, FILAMENT_PLA_KG * 20.0))
    rows.append(("Filament", "PETG (printed pins/shafts/rods for the motion test)", "-", "any PETG", "-", int(FILAMENT_PETG_KG),
                 "Bambu / any", "https://www.amazon.com/s?k=PETG+filament+1kg", 22.0, FILAMENT_PETG_KG * 22.0))

    total = sum(r[9] for r in rows)
    L = ["# PROTOTYPE bill of materials (1-2 engines + spares) - DRAFT", "",
         f"Generated by `tools/proto_bom.py`. Covers **{ENGINES} engines** plus **{SPARE:.0%} spares** on consumables, "
         "alternative insert / screw / belt sizes for fit testing, and the measuring tools the coupons need. "
         "Prices are typical 2026 USD estimates; links are search terms, not specific listings. "
         "**Not included on purpose:** the machined steel parts M01, M02, M04, M06 (printed PETG stand-ins are used "
         "until the coupons confirm the dimensions), and anything for the 50-unit run.", "",
         "| Section | Part | Part no | Spec | Qty / engine | Order qty | Supplier | Link | Unit $ | Line $ |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | [search]({r[7]}) | {r[8]:.2f} | {r[9]:.2f} |")
    L += [f"| | **Total** | | | | | | | | **{total:,.0f}** |", "",
          "## Filament per engine by palette slot (ASA)", "", "| Slot | Parts | g / engine |", "|---|---|---|"]
    for k, g in slots.items():
        L.append(f"| {C.PALETTE[k]['name']} | {', '.join(C.PALETTE[k]['parts'])} | {g / ENGINES:.0f} |")
    L += ["", "Hidden parts (crank, rods, pistons) can be any of the four colours - whichever spool is loaded.", "",
          "## Not yet - wait for the coupons", "",
          "* Steel M01 crankpins, M02 shafts, M04 spacer, M06 rings: order (or have made) only after T3/T5/T6 and the "
          "motion test confirm the printed sockets and seats. Drawings with tolerances: `drawings/machined_parts.pdf`.",
          "* Anything x50."]
    with open(os.path.join(ROOT, "docs", "PROTO_BOM.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(ROOT, "docs", "PROTO_BOM.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "part", "part_no", "spec", "qty_per_engine", "order_qty", "supplier", "link", "unit_usd", "line_usd"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], f"{r[8]:.2f}", f"{r[9]:.2f}"])
    print(f"wrote docs/PROTO_BOM.md / .csv: {len(rows)} lines, about ${total:,.0f}")


if __name__ == "__main__":
    main()
