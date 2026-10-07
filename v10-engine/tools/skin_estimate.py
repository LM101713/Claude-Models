"""Print-time and filament estimate for the Blender skin, without a slicer.

PrusaSlicer is not available in the cloud container, so each skin part is
scaled from the CAD part of the same name in docs/print_results.json
(the production-profile slice): grams and hours per cm3 of solid volume of
that CAD part, times the skin part's solid volume. Parts without a CAD
twin use the median ratio of the matched parts. Core parts (not in the
skin) keep their slicer values. Treat the result as an estimate, +-15 %;
the first real slice replaces it.

    python tools/skin_estimate.py            (bpyenv: needs trimesh)
"""
import json
import os
import statistics
import sys

import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIN = os.path.join(ROOT, "skin")
RES = json.load(open(os.path.join(ROOT, "docs", "print_results.json")))
PARTS = json.load(open(os.path.join(SKIN, "parts.json")))["parts"]


def cad_ratio(name):
    r = RES.get(name)
    p = os.path.join(ROOT, "stl", name + ".stl")
    if not r or not os.path.exists(p):
        return None
    v = trimesh.load(p).volume / 1000.0
    return r["grams"] / v, r["hours"] / v


def main():
    ratios = {}
    for row in PARTS:
        ratios[row["file"]] = cad_ratio(row["file"])
    matched = [v for v in ratios.values() if v]
    med = (statistics.median(g for g, _ in matched), statistics.median(h for _, h in matched))
    skin_files = {row["file"] for row in PARTS}
    out, tot_g, tot_h, tot_n = [], 0.0, 0.0, 0
    for row in PARTS:
        v = trimesh.load(row["path"]).volume / 1000.0
        g_r, h_r = ratios[row["file"]] or med
        g, h = v * g_r * row["qty"], v * h_r * row["qty"]
        src = "cad twin" if ratios[row["file"]] else "median"
        out.append((row["file"], row["qty"], v, g, h, src))
        tot_g += g
        tot_h += h
        tot_n += row["qty"]
    # core parts: everything sliced that is not a skin file and not a CAD exterior part replaced by the skin
    # quantities from BOM.md section 1 (| name | qty | ... |); CAD exterior parts (3x, 4x) are replaced by the skin
    qty = {}
    for line in open(os.path.join(ROOT, "docs", "BOM.md")):
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1] in RES and cells[2].isdigit():
            qty[cells[1]] = int(cells[2])
    core = [(n, r) for n, r in RES.items() if n not in skin_files and not n.startswith(("3", "4"))]
    core_g = sum(r["grams"] * qty.get(n, 1) for n, r in core)
    core_h = sum(r["hours"] * qty.get(n, 1) for n, r in core)
    core_n = sum(qty.get(n, 1) for n, _ in core)
    print(f"Blender skin: {tot_n} pieces in {len(PARTS)} files, est. {tot_g:.0f} g, {tot_h:.1f} h "
          f"({len(matched)} of {len(PARTS)} files scaled from their CAD twin, the rest at the median {med[0]:.2f} g/cm3, {med[1]*60:.1f} min/cm3)")
    print(f"Core (CAD, slicer values, {core_n} pieces in {len(core)} files): {core_g:.0f} g, {core_h:.1f} h")
    print(f"Engine estimate: {tot_n + core_n} printed pieces, {tot_g + core_g:.0f} g, {tot_h + core_h:.0f} h  (CAD-only BOM.md: 88 pieces, 3050 g, 127 h)")
    print()
    for f, q, v, g, h, src in sorted(out, key=lambda t: -t[4]):
        print(f"  {f:26s} x{q}  {v:7.1f} cm3  {g:6.0f} g  {h:5.1f} h  ({src})")
    if "--json" in sys.argv:
        json.dump(dict(skin_g=tot_g, skin_h=tot_h, core_g=core_g, core_h=core_h, parts=out),
                  open(os.path.join(ROOT, "docs", "skin_estimate.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
