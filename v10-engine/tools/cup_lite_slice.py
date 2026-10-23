"""Real slice of the Cup Lite parts with the PrusaSlicer CLI (apt package prusa-slicer 2.7.2), to replace
the fitted estimate in tools/cup_lite_estimate.py.

Each STL is turned to its print orientation (the exported STLs sit in their assembled positions),
sliced with tools/slicer_cup_lite/asa_08.ini, and the slicer's own time and filament are read from the
G-code. Runs at two hotend melt rates: 18 mm3/s (a standard Bambu-class hotend on ASA, the same cap
as tools/slicer/h2s_like.ini) and 28 mm3/s (a high-flow hotend, untested).

    python tools/cup_lite_slice.py [--flow 18,28] [--json]      (bpyenv: trimesh)

Oriented STLs and G-code go to cup_lite/slice/ (G-code is not committed). PrusaSlicer's time model
is not Bambu Studio's; treat the result as +-10 % rather than +-20 %.
"""
import argparse
import json
import math
import os
import re
import subprocess

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "cup_lite", "stl")
OUT = os.path.join(ROOT, "cup_lite", "slice")
INI = os.path.join(ROOT, "tools", "slicer_cup_lite", "asa_08.ini")
S45 = math.sqrt(0.5)


def rx(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (1, 0, 0))


def ry(deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), (0, 1, 0))


# file -> (rotation to print orientation, qty per engine, extra slicer options)
SUP = ["--support-material", "--support-material-auto"]
PARTS = {
    "l1_block_pan": (None, 1, []),
    "l2_top_end": (None, 1, SUP + ["--brim-width", "6"]),
    "l3_air_cleaner": (None, 1, []),
    "l4_header_right": (rx(135), 1, SUP),          # port flanges on the bed
    "l5_header_left": (rx(-135), 1, SUP),
    "l6_front_drive": (ry(90), 1, SUP),            # pulley noses down
    "t01_valve_cover": (rx(45), 2, []),            # flange down (bank A frame)
    "t02_air_cleaner_lid": (None, 1, []),
    "k01_crank_pulley": (ry(-90), 1, []),          # damper face down
    "k02_pulley_water": (ry(90), 1, []),
    "k03_pulley_pump": (ry(90), 1, []),
    "k04_pulley_alt": (ry(90), 1, []),
    "k05_flywheel": (ry(90), 1, []),
    "k06_distributor": (None, 1, []),
    "k07_plug_boot": (None, 8, []),
    "k08_control_pod": (None, 1, []),
}


def orient(name, rot):
    m = trimesh.load(os.path.join(STL, name + ".stl"))
    if rot is not None:
        m.apply_transform(rot)
    m.apply_translation(-m.bounds[0])
    path = os.path.join(OUT, name + ".stl")
    m.export(path)
    return path, m.extents


def parse_time(s):
    t = 0.0
    for v, u in re.findall(r"(\d+)([dhms])", s):
        t += int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
    return t / 3600.0


def slice_one(name, stl, opts, flow):
    gc = os.path.join(OUT, f"{name}_f{flow}.gcode")
    cmd = ["prusa-slicer", "--export-gcode", "--load", INI, "--max-volumetric-speed", str(flow),
           "--center", "128,128", *opts, "--output", gc, stl]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(gc):
        raise RuntimeError(f"{name}: slicer failed\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    txt = open(gc, errors="ignore").read()[-20000:]
    hours = parse_time(re.search(r"estimated printing time \(normal mode\) = (.+)", txt).group(1))
    grams = float(re.search(r"filament used \[g\] = ([\d.]+)", txt).group(1))
    return hours, grams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", default="18,28")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    flows = [int(f) for f in a.flow.split(",")]
    os.makedirs(OUT, exist_ok=True)
    rows, tot = [], {f: [0.0, 0.0] for f in flows}
    for name, (rot, qty, opts) in PARTS.items():
        stl, ext = orient(name, rot)
        if max(ext[0], ext[1]) > 256 or ext[2] > 256:
            print(f"WARNING {name} does not fit a 256 mm bed as oriented: {np.round(ext, 1)}")
        row = dict(file=name, qty=qty, size_as_printed=[round(float(v), 1) for v in ext],
                   supports=("--support-material" in opts))
        for f in flows:
            h, g = slice_one(name, stl, opts, f)
            row[f"h{f}"], row[f"g{f}"] = round(h, 2), round(g, 1)
            tot[f][0] += h * qty
            tot[f][1] += g * qty
        rows.append(row)
        print(f"  {name:22s} x{qty}  " + "  ".join(f"{f} mm3/s: {row[f'h{f}']:5.2f} h {row[f'g{f}']:6.1f} g" for f in flows)
              + ("  (supports)" if row["supports"] else ""), flush=True)
    for f in flows:
        print(f"Cup Lite per engine at {f} mm3/s: {tot[f][0]:.1f} printer-h, {tot[f][1]:.0f} g")
    if a.json:
        json.dump(dict(parts=rows, total={str(f): dict(hours=tot[f][0], grams=tot[f][1]) for f in flows},
                       profile=os.path.relpath(INI, ROOT), slicer="PrusaSlicer 2.7.2 CLI"),
                  open(os.path.join(ROOT, "cup_lite", "slice.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
