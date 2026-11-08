"""
ODD LAYER SD-01 SINKDOCK: a one-piece, self-draining sink dock for a Scrub Daddy, a Scrub Mommy,
a flat sponge and a dish brush.

    python sinkdock.py            build, export STL + 3MF, run every check, write the reports
    python sinkdock.py --render   ...plus the product renders (Blender as a Python module, Cycles CPU)

Everything comes from sd/params.py.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sd import geom as G  # noqa: E402
from sd import export as X  # noqa: E402
from sd import report as R  # noqa: E402
from sd import validate as V  # noqa: E402

MODELS = os.path.join(HERE, "models")
STL = os.path.join(MODELS, "stl", "SD01_SinkDock.stl")
MF = os.path.join(MODELS, "3mf", "SD01_SinkDock_A1mini_plate.3mf")


def centred(m):
    bb = m.bounding_box()
    return m.translate([-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(STL), exist_ok=True)
    os.makedirs(os.path.dirname(MF), exist_ok=True)

    m = G.build()
    X.write_stl(STL, m)
    X.write_3mf(MF, [("SD-01 SinkDock", centred(m))], plate_center=(90.0, 90.0))

    checks, est_pla, est_petg = V.run_all(m, [STL, MF])
    maps = None
    for name, ok, d in checks:
        if "_maps" in d:
            maps = d.pop("_maps")
    n_ok = sum(1 for c in checks if c[1])
    print(f"\nSD-01 SINKDOCK: {n_ok}/{len(checks)} checks pass\n")
    for name, ok, d in checks:
        print(("PASS " if ok else "FAIL ") + name)

    with open(os.path.join(MODELS, "SD01_validation.json"), "w") as f:
        json.dump(dict(checks=[dict(name=n, passed=ok, detail=d) for n, ok, d in checks],
                       estimate_pla=est_pla, estimate_petg=est_petg), f, indent=1, default=str)
    R.write_report(os.path.join(MODELS, "SD01_validation_report.md"), m, checks, est_pla, est_petg)
    R.drainage_map(os.path.join(HERE, "docs", "SD01_drainage_map.png"), m, maps)
    R.drawing(os.path.join(HERE, "docs", "SD01_drawing.png"), m)

    if a.render:
        from sd import scene
        scene.render_all(m, os.path.join(HERE, "renders"), os.path.join(MODELS, "SD01_SinkDock.blend"))
    return 0 if n_ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
