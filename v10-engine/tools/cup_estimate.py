"""Print-time and filament estimate for the Cup production concept (cup/stl), without a slicer.

Model per part: plastic = shell (surface area x wall thickness, capped at the solid volume)
+ the rest of the solid x infill; hours = plastic / Q + layers x t_layer.
Q and t_layer are fitted on the CAD parts that were really sliced (docs/print_results.json,
0.4 mm nozzle production profile, each with its own walls / infill / layer height), then the
0.6 mm nozzle profile (3 walls of 0.65 mm, 12 % gyroid, 0.30 mm layers) runs at K06 x that flow.
Headers print on tree supports: +30 % time, +15 % plastic. Treat as +-20 %; a real slice replaces it.

    python tools/cup_estimate.py [--json]        (bpyenv: trimesh, numpy)
"""
import json
import os
import sys

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = json.load(open(os.path.join(ROOT, "docs", "print_results.json")))
PARTS = json.load(open(os.path.join(ROOT, "cup", "parts.json")))["parts"]
RHO = 1.07          # ASA g/cm3
K06 = 1.8           # 0.6 mm / 0.30 mm flow vs 0.4 mm / 0.20 mm (geometric 2.2x, derated for outer-wall speed)
LINE04 = 0.45
P06 = dict(walls=3, line=0.65, infill=12, layer=0.30)

# height as printed (mm) and orientation note, per concept part
ORIENT = {
    "c01_block": (119, "pan rail down, open bottom"),
    "c02_pan": (29, "flange down, open top"),
    "c03_head": (45, "deck face down, open"),
    "c04_valve_cover": (41, "flange down, open, 45 deg roof inside"),
    "c05_intake": (112, "upright, open underneath"),
    "c06_air_cleaner_base": (27, "base down, open top"),
    "c07_air_cleaner_lid": (12, "upright"),
    "c08_distributor": (100, "upright"),
    "c09_header_right": (94, "on its port flanges, tree supports"),
    "c10_header_left": (94, "on its port flanges, tree supports"),
    "c11_front_cover": (90, "back face down"),
    "c12_alternator": (22, "back face down"),
    "c13_crank_pulley": (28, "back face down"),
    "c14_pulley_water": (10, "flat"),
    "c15_pulley_pump": (10, "flat"),
    "c16_pulley_alt": (10, "flat"),
    "c17_flywheel": (12, "flat"),
    "c18_plinth": (38, "flat"),
    "c19_plug_boot": (13, "upright, translucent"),
}
SUPPORTED = {"c09_header_right", "c10_header_left"}


def plastic(mesh, walls, line, infill):
    v = mesh.volume
    shell = min(v, mesh.area * walls * line)
    return shell + (v - shell) * infill / 100.0


def fit():
    rows = []
    for name, r in RES.items():
        p = os.path.join(ROOT, "stl", name + ".stl")
        if not os.path.exists(p):
            continue
        m = trimesh.load(p)
        pl = plastic(m, r["walls"], LINE04, r["infill"])
        layers = m.extents[2] / r["layer"]
        rows.append((pl, layers, r["hours"] * 3600.0, r["grams"], name))
    A = np.array([[pl, n] for pl, n, _, _, _ in rows])
    y = np.array([h for _, _, h, _, _ in rows])
    (inv_q, t_l), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ np.array([inv_q, t_l])
    err = np.median(np.abs(pred - y) / y)
    gm = np.median([g / (pl / 1000.0) for pl, _, _, g, _ in rows])
    return 1.0 / inv_q, t_l, err, gm, len(rows)


def main():
    q04, t_l, err, gm, n = fit()
    q06 = q04 * K06
    out, tot = [], dict(n=0, h04=0.0, h06=0.0, g06=0.0)
    for row in PARTS:
        m = trimesh.load(row["path"])
        hgt, note = ORIENT[row["file"]]
        pl04 = plastic(m, 4, LINE04, 25)
        pl06 = plastic(m, P06["walls"], P06["line"], P06["infill"])
        h04 = (pl04 / q04 + hgt / 0.2 * t_l) / 3600.0
        h06 = (pl06 / q06 + hgt / P06["layer"] * t_l) / 3600.0
        g06 = pl06 / 1000.0 * gm
        if row["file"] in SUPPORTED:
            h04 *= 1.3
            h06 *= 1.3
            g06 *= 1.15
        q = row["qty"]
        out.append(dict(file=row["file"], qty=q, solid_cm3=round(m.volume / 1000.0, 1), h04=round(h04, 2),
                        h06=round(h06, 2), g06=round(g06, 1), size=row["size"], print=note))
        tot["n"] += q
        tot["h04"] += h04 * q
        tot["h06"] += h06 * q
        tot["g06"] += g06 * q
    print(f"Fit on {n} sliced CAD parts: Q = {q04:.1f} mm3/s, {t_l:.1f} s per layer, median error {err*100:.0f} %, "
          f"{gm:.2f} g per cm3 of plastic")
    print(f"Cup concept: {tot['n']} printed pieces, 0.4 mm nozzle {tot['h04']:.0f} h, "
          f"0.6 mm nozzle {tot['h06']:.0f} h, {tot['g06']:.0f} g")
    for r in sorted(out, key=lambda r: -r["h06"] * r["qty"]):
        print(f"  {r['file']:24s} x{r['qty']}  {r['solid_cm3']:7.1f} cm3  0.4: {r['h04']:5.1f} h  0.6: {r['h06']:5.1f} h  "
              f"{r['g06']:6.0f} g   {r['print']}")
    # same model on the round-7 engine (Blender skin + moving CAD core), for a like-for-like comparison
    skin = json.load(open(os.path.join(ROOT, "skin", "parts.json")))["parts"]
    qty = {}
    for line in open(os.path.join(ROOT, "docs", "BOM.md")):
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1] in RES and cells[2].isdigit():
            qty[cells[1]] = int(cells[2])
    skin_files = {r["file"] for r in skin}
    r7 = [(trimesh.load(r["path"]), r["qty"]) for r in skin]
    core = [n for n in RES if n not in skin_files and not n.startswith(("3", "4"))
            and os.path.exists(os.path.join(ROOT, "stl", n + ".stl"))]
    r7 += [(trimesh.load(os.path.join(ROOT, "stl", n + ".stl")), qty.get(n, 1)) for n in core]
    h7_04 = sum((plastic(m, 4, LINE04, 25) / q04 + m.extents[2] / 0.2 * t_l) / 3600.0 * q for m, q in r7)
    h7_06 = sum((plastic(m, 3, 0.65, 12) / q06 + m.extents[2] / 0.3 * t_l) / 3600.0 * q for m, q in r7)
    n7 = sum(q for _, q in r7)
    print(f"Round 7, same model: {n7} pieces, 0.4 mm nozzle {h7_04:.0f} h, 0.6 mm nozzle {h7_06:.0f} h")
    tot.update(r7_n=n7, r7_h04=h7_04, r7_h06=h7_06)
    if "--json" in sys.argv:
        json.dump(dict(total=tot, parts=out, q04=q04, t_layer=t_l, fit_err=err),
                  open(os.path.join(ROOT, "cup", "estimate.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
