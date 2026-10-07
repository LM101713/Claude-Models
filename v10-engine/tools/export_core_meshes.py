"""Export the CAD moving core and the other parts that stay in CAD as engine-frame
STL meshes -> skin/core/ (for the Blender full-engine renders and tools/skin_check.py).

    python tools/export_core_meshes.py [--phi 0]
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))

import cadquery as cq  # noqa: E402

import assembly_v8 as A  # noqa: E402

OUT = os.path.join(ROOT, "skin", "core")
# everything the Blender skin does NOT rebuild: moving core, rails, bearings, end plates, valley beam, drive, electronics
CORE_PREFIXES = ("crankpin", "segment", "end_web", "main_shaft", "rod_", "piston_", "bearing", "bush", "pin_", "rail_",
                 "end_plate", "valley_beam", "pulley", "belt", "motor", "spacer", "elec_")


def core_parts(phi=0.0):
    parts = A.engine(phi) + A.drive_and_base(with_base=False, with_covers=False)
    return [(n, s) for n, s, _ in parts if n.startswith(CORE_PREFIXES)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phi", type=float, default=0.0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".stl"):
            os.remove(os.path.join(OUT, f))
    parts = core_parts(a.phi)
    for n, s in parts:
        cq.exporters.export(cq.Workplane().add(s), os.path.join(OUT, n + ".stl"), tolerance=0.02, angularTolerance=0.1)
    print(f"wrote {len(parts)} core meshes -> skin/core/ (crank angle {a.phi} deg)")


if __name__ == "__main__":
    main()
