#!/usr/bin/env python3
"""
Odd Layer GS-05 GIFT SLIDE: generator.

    python giftslide.py                  build every part, run all checks, export STL / 3MF, write the report
    python giftslide.py --quick          coarser travel sweep (faster)
    python giftslide.py --blend --render Blender project and product renders (needs `pip install bpy`)

All dimensions live in gs/params.py. Change a value there and rerun.
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gs import export as X  # noqa: E402
from gs import geom as G  # noqa: E402
from gs import report as R  # noqa: E402
from gs import validate as V  # noqa: E402
from gs.params import LOOSE, P, SNUG  # noqa: E402

MODELS = os.path.join(HERE, "models")
STL = os.path.join(MODELS, "stl")
TMF = os.path.join(MODELS, "3mf")


def arrange(m, cx, cy):
    """Centre a part's footprint on (cx, cy), base on z = 0."""
    bb = m.bounding_box()
    return m.translate((cx - (bb[0] + bb[3]) / 2, cy - (bb[1] + bb[4]) / 2, -bb[2]))


def export_all(C):
    os.makedirs(STL, exist_ok=True)
    os.makedirs(TMF, exist_ok=True)
    parts = C.data["parts"]
    tray, lid = parts["tray"], parts["lid"]
    tray_plain = G.tray(P, message="")
    lid_star, inlay = parts["lid_star"], parts["star_inlay"]
    stls = {
        "GS05_A_Tray.stl": tray,
        "GS05_A_Tray_Plain_alt.stl": tray_plain,
        "GS05_B_Lid.stl": lid,
        "GS05_B_Lid_Star_alt.stl": lid_star,
        "GS05_B_Lid_Loose_alt.stl": parts["lid_loose"],
        "GS05_B_Lid_Snug_alt.stl": parts["lid_snug"],
        "GS05_C_Star_Inlay_multicolour.stl": inlay,
        "GS05_T_Coupon_Tray.stl": parts["coupon_tray"],
        "GS05_T_Coupon_Lid_STD.stl": parts["coupon_lid"],
        "GS05_T_Coupon_Lid_LOOSE.stl": parts["coupon_lid_loose"],
        "GS05_T_Coupon_Lid_SNUG.stl": parts["coupon_lid_snug"],
    }
    written = []
    for name, m in stls.items():
        path = os.path.join(STL, name)
        X.write_stl(path, m, name[:-4])
        written.append((os.path.relpath(path, HERE), m))
    # reference assembly (closed, with a card): not for printing
    asm = tray + G.lid_placed(P, 0.0, lid_m=lid)
    X.write_stl(os.path.join(MODELS, "GS05_Assembly_closed.stl"), asm, "GS05 assembly (reference)")
    # plates (A1 mini, 180 x 180)
    plate = [("GS05_A_Tray", arrange(tray, 0, 35.5)), ("GS05_B_Lid", arrange(lid, 0, -33.5))]
    X.write_3mf(os.path.join(TMF, "GS05_gift_slide_plate.3mf"), plate)
    coupon = [("GS05_T_Coupon_Tray", arrange(parts["coupon_tray"], -34.5, 35.5)),
              ("GS05_T_Coupon_Lid_STD", arrange(parts["coupon_lid"], 34.5, 35.5)),
              ("GS05_T_Coupon_Lid_LOOSE", arrange(parts["coupon_lid_loose"], -34.5, -33.5)),
              ("GS05_T_Coupon_Lid_SNUG", arrange(parts["coupon_lid_snug"], 34.5, -33.5))]
    X.write_3mf(os.path.join(TMF, "GS05_fit_coupon_first.3mf"), coupon)
    off = arrange(lid_star, 0, -33.5)
    bb = lid_star.bounding_box()
    shift = (off.bounding_box()[0] - bb[0], off.bounding_box()[1] - bb[1], 0)
    star_obj = [("GS05_B_Lid_Star", off), ("GS05_C_Star_Inlay", inlay.translate(shift))]
    X.write_3mf(os.path.join(TMF, "GS05_star_lid_two_colour.3mf"),
                [("GS05_A_Tray", arrange(tray, 0, 35.5)), ("GS05_B_Lid_Star (2 parts)", star_obj)])
    X.write_3mf(os.path.join(TMF, "GS05_lid_fit_variants.3mf"),
                [("GS05_B_Lid_Loose", arrange(parts["lid_loose"], 0, 34.0)),
                 ("GS05_B_Lid_Snug", arrange(parts["lid_snug"], 0, -34.0))])
    # round-trip every file
    files = []
    for rel, m in written:
        v, t = X.read_stl(os.path.join(HERE, rel))
        back = X.manifold_from_arrays(v, t)
        ok = back.status().name == "NoError" and abs(back.volume() - m.volume()) < 0.01 * m.volume() + 0.5
        files.append(dict(file=rel, tris=len(t), vol=back.volume(), ok=ok, limit="closed solid, volume matches the model"))
    for f in sorted(os.listdir(TMF)):
        objs = X.read_3mf(os.path.join(TMF, f))
        for name, back in objs.items():
            bb = back.bounding_box()
            on_plate = bb[0] >= 0 and bb[1] >= 0 and bb[3] <= 180 and bb[4] <= 180 and abs(bb[2]) < 1e-3 + (0.0 if "Inlay" not in name else 3)
            ok = back.status().name == "NoError" and back.volume() > 0 and on_plate
            files.append(dict(file=f"models/3mf/{f} : {name}", tris=back.num_tri(), vol=back.volume(), ok=ok,
                              limit="closed solid, on the 180 mm plate"))
    for f in files:
        C.add("H files", f"re-read {f['file']}", f"{f['vol'] / 1000:.2f} cm3", f["limit"], f["ok"])
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--blend", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--samples", type=int, default=160)
    a = ap.parse_args()
    t0 = time.time()
    print("GS-05 GIFT SLIDE: building and checking ...")
    C = V.run(P, quick=a.quick)
    files = export_all(C)
    R.write(C, os.path.join(MODELS, "GS05_validation_report.md"), os.path.join(MODELS, "GS05_validation.json"), P, files)
    n_ok = sum(r["ok"] for r in C.rows)
    for r in C.rows:
        if not r["ok"]:
            print(f"  FAIL  {r['group']}: {r['name']}  ({r['value']} vs {r['limit']})")
    print(f"  {n_ok}/{len(C.rows)} checks pass  ({time.time() - t0:.0f} s)")
    if a.blend or a.render:
        from gs import scene

        scene.build(C, blend=a.blend, render=a.render, samples=a.samples)
    return 0 if C.passed else 1


if __name__ == "__main__":
    sys.exit(main())
