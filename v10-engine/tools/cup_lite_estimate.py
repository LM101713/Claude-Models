"""Print-time and filament estimate for Cup Lite (cup_lite/stl), without a slicer, on the same
fitted model as tools/cup_estimate.py (plastic = shell + infill, hours = plastic / Q + layers x t).

Profiles:
  0.6 mm nozzle, 3 walls x 0.65, 12 % gyroid, 0.30 mm layers (the Cup concept's numbers)
  0.8 mm nozzle, 2 walls x 0.85, 10 % gyroid, 0.40 mm layers (Cup Lite)
Flow: 0.8 mm runs at K08 x the fitted 0.4 mm flow, capped at QCAP. The cap is the melt limit of the
hotend, not the nozzle: above about 16 mm3/s average ASA stops gaining (ASSUMED from typical Bambu
ASA profiles, about 20 mm3/s peak). This is why 0.8 mm is not twice as fast as 0.6 mm.
Supported prints: +20-30 % time, +10-15 % plastic. Treat as +-20 % until a real slice.

    python tools/cup_lite_estimate.py [--json]    (bpyenv: trimesh, numpy)
"""
import json
import os
import sys

import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cup_estimate as CE  # noqa: E402

ROOT = CE.ROOT
PARTS = json.load(open(os.path.join(ROOT, "cup_lite", "parts.json")))["parts"]
K08 = 0.82 * (0.85 * 0.40) / (0.45 * 0.20)   # geometric flow ratio, derated like K06
QCAP = 16.0
P06 = dict(walls=3, line=0.65, infill=12, layer=0.30)
P08 = dict(walls=2, line=0.85, infill=10, layer=0.40)

# height as printed (mm), support factor (time, plastic), how it prints, filament colour
ORIENT = {
    "l1_block_pan": (149, None, "pan opening down, hollow", "orange ASA"),
    "l2_top_end": (128, (1.2, 1.1), "upright, tree supports under the deck edges and port bosses", "silver ASA"),
    "l3_air_cleaner": (29, None, "base down, open top", "black ASA"),
    "l4_header_right": (94, (1.3, 1.15), "on its port flanges, tree supports", "silver ASA"),
    "l5_header_left": (94, (1.3, 1.15), "on its port flanges, tree supports", "silver ASA"),
    "l6_front_drive": (90, (1.3, 1.15), "pulley noses down, tree supports under the cover plate", "silver ASA"),
    "t01_valve_cover": (41, None, "flange down, hollow, 45 deg roof inside", "black ASA"),
    "t02_air_cleaner_lid": (12, None, "upright, groove underneath", "silver ASA"),
    "k01_crank_pulley": (37, None, "damper face down", "black ASA"),
    "k02_pulley_water": (10, None, "flat", "black ASA"),
    "k03_pulley_pump": (10, None, "flat", "black ASA"),
    "k04_pulley_alt": (10, None, "flat", "black ASA"),
    "k05_flywheel": (12, None, "flat", "black ASA"),
    "k06_distributor": (100, None, "upright", "black ASA"),
    "k07_plug_boot": (13, None, "upright", "clear PETG"),
}


def hours(m, prof, q, t_l, hgt, sup):
    pl = CE.plastic(m, prof["walls"], prof["line"], prof["infill"])
    h = (pl / q + hgt / prof["layer"] * t_l) / 3600.0
    if sup:
        h, pl = h * sup[0], pl * sup[1]
    return h, pl


def main():
    q04, t_l, err, gm, n = CE.fit()
    q06 = q04 * CE.K06
    q08 = min(q04 * K08, QCAP)
    rows, tot = [], dict(n=0, h06=0.0, h08=0.0, g08=0.0)
    for r in PARTS:
        m = trimesh.load(os.path.join(ROOT, r["path"]))
        hgt, sup, note, col = ORIENT[r["file"]]
        h06, _ = hours(m, P06, q06, t_l, hgt, sup)
        h08, pl08 = hours(m, P08, q08, t_l, hgt, sup)
        g08 = pl08 / 1000.0 * gm
        q = r["qty"]
        rows.append(dict(file=r["file"], qty=q, size=r["size"], h06=round(h06, 2), h08=round(h08, 2), g08=round(g08, 1),
                         print=note, colour=col))
        tot["n"] += q
        tot["h06"] += h06 * q
        tot["h08"] += h08 * q
        tot["g08"] += g08 * q
    by_col = {}
    for r in rows:
        by_col[r["colour"]] = by_col.get(r["colour"], 0.0) + r["g08"] * r["qty"]
    # the Cup concept's parts on the 0.8 profile, to separate the nozzle gain from the merge gain
    cup08 = 0.0
    for r in CE.PARTS:
        hgt, note = CE.ORIENT[r["file"]]
        if r["file"] == "c18_plinth":
            continue
        sup = (1.3, 1.15) if r["file"] in CE.SUPPORTED else None
        cup08 += hours(trimesh.load(r["path"]), P08, q08, t_l, hgt, sup)[0] * r["qty"]
    print(f"Fit on {n} sliced parts: Q04 {q04:.1f} mm3/s, {t_l:.1f} s/layer, median error {err*100:.0f} %; "
          f"Q06 {q06:.1f}, Q08 {q08:.1f} mm3/s (cap {QCAP})")
    print(f"Cup Lite: {tot['n']} printed pieces, 0.6 mm {tot['h06']:.1f} h, 0.8 mm {tot['h08']:.1f} h, {tot['g08']:.0f} g")
    print(f"Cup concept without plinth on the 0.8 profile: {cup08:.1f} h")
    for r in sorted(rows, key=lambda r: -r["h08"] * r["qty"]):
        print(f"  {r['file']:22s} x{r['qty']}  0.6: {r['h06']:5.2f} h  0.8: {r['h08']:5.2f} h  {r['g08']:6.0f} g  "
              f"{r['colour']:11s} {r['print']}")
    print("  filament by colour (g):", {k: round(v) for k, v in by_col.items()})
    tot.update(cup_concept_h08=cup08, q08=q08, by_colour=by_col)
    if "--json" in sys.argv:
        json.dump(dict(total=tot, parts=rows, q04=q04, t_layer=t_l, fit_err=err),
                  open(os.path.join(ROOT, "cup_lite", "estimate.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
