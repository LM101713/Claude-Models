"""
ODD LAYER  HF-04  HOLDFAST
==========================

A gravity-locking wall grip for brooms, mops and garden tools (19-32 mm handles).
Push the handle in and up; let go and it locks. Lift it and it lets go.

    BASE     wall plate, two housings with 16-degree ramps, keyhole T-slots, 2 screw holes
    ROLLER   x2, a 24 mm puck that rolls on the ramp; its stub runs in the T-slot
             (variants: Grip = 36 shallow ridges, Loose = smaller stub for tight printers)
    COUPON   10-minute fit test: the top of the slot and the keyhole

This script builds every part as an exact manifold solid, validates the mechanism (travel
sweep, assembly path, retention, handle range, printer-variation corners, overhangs, wall
thickness, hand-calculated loads), exports STL / 3MF and writes the validation report.
With --blend it also builds the Blender project; with --render it renders the images.

    pip install manifold3d shapely numpy matplotlib     (and `pip install bpy` for --blend)
    python holdfast.py                       # build, validate, export
    python holdfast.py --blend --render      # ...plus the .blend and the renders

Status: CAD-validated only. Nothing has been printed or physically tested.
"""

import argparse
import json
import math
import os
import sys
import time


HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from hf import geom as G  # noqa: E402
from hf import validate as V  # noqa: E402
from hf.export import write_3mf, write_stl  # noqa: E402
from hf.params import D, P, kinematics_table, summary  # noqa: E402
from hf.report import write_report  # noqa: E402


def build_parts():
    base = G.build_base()
    roller = G.build_roller()
    grip = G.build_roller(grip=True)
    loose = G.build_roller(loose=True)
    coupon, _ = G.build_coupon()
    return dict(base=base, roller=roller, grip=grip, loose=loose, coupon=coupon)


def print_frames(parts):
    return dict(
        base=G.to_bed(G.base_to_print(parts["base"])),
        roller=G.to_bed(parts["roller"]),
        grip=G.to_bed(parts["grip"]),
        loose=G.to_bed(parts["loose"]),
        coupon=G.to_bed(G.base_to_print(parts["coupon"])),
    )


def export_all(parts, pf, out):
    stl = os.path.join(out, "models", "stl")
    tmf = os.path.join(out, "models", "3mf")
    os.makedirs(stl, exist_ok=True)
    os.makedirs(tmf, exist_ok=True)
    files = {
        "HF04_A_Base.stl": pf["base"],
        "HF04_B_Roller_x2.stl": pf["roller"],
        "HF04_B_Roller_Grip_x2_alt.stl": pf["grip"],
        "HF04_B_Roller_Loose_x2_alt.stl": pf["loose"],
        "HF04_T_Fit_Coupon.stl": pf["coupon"],
    }
    for fn, m in files.items():
        write_stl(os.path.join(stl, fn), m, "HF-04 " + fn[5:-4])
    # assembly (use frame, as it hangs on the wall, rollers resting on their bottom stops)
    # three separate shells (no boolean union, so the rollers stay separate bodies)
    from manifold3d import Manifold

    asm = Manifold.compose([parts["base"], V.place(parts["roller"], 0.0, -1), V.place(parts["roller"], 0.0, +1)])
    write_stl(os.path.join(out, "models", "HF04_Assembly.stl"), asm, "HF-04 assembly")
    # print plates (fit any bed >= 180 x 180)
    r = pf["roller"]
    full = [
        ("HF04_A_Base", pf["base"].translate([0, 22, 0])),
        ("HF04_B_Roller_1", r.translate([-22, -42, 0])),
        ("HF04_B_Roller_2", r.translate([22, -42, 0])),
    ]
    write_3mf(os.path.join(tmf, "HF04_full_set.3mf"), full)
    fit = [("HF04_T_Fit_Coupon", pf["coupon"].translate([-16, 0, 0])), ("HF04_B_Roller", r.translate([18, 0, 0]))]
    write_3mf(os.path.join(tmf, "HF04_fit_test_first.3mf"), fit)
    return list(files) + ["HF04_Assembly.stl", "HF04_full_set.3mf", "HF04_fit_test_first.3mf"]


def run_validation(parts, pf, out, quick=False):
    t0 = time.time()
    res = dict(summary=summary(), params={k: getattr(P, k) for k in dir(P) if k.isupper()})
    res["kinematics"] = kinematics_table()
    res["parts"] = {
        "base": V.part_report("Base", parts["base"], pf["base"]),
        "roller": V.part_report("Roller", parts["roller"], pf["roller"]),
        "roller_grip": V.part_report("Roller (Grip)", parts["grip"], pf["grip"]),
        "roller_loose": V.part_report("Roller (Loose)", parts["loose"], pf["loose"]),
        "coupon": V.part_report("Fit coupon", parts["coupon"], pf["coupon"]),
    }
    print(f"  parts checked ({time.time() - t0:.0f}s)")
    res["sweep"] = V.travel_sweep(parts["base"], parts["roller"], step=2.0 if quick else 0.5)
    res["sweep_grip"] = V.travel_sweep(parts["base"], parts["grip"], step=4.0 if quick else 1.0)
    print(f"  travel sweep ({time.time() - t0:.0f}s)")
    res["retention"] = V.retention_table(parts["base"], parts["roller"])
    res["assembly"] = V.assembly_path(parts["base"], parts["roller"], step=0.5 if quick else 0.25)
    res["assembly_right"] = V.assembly_path(parts["base"], parts["roller"], side=+1, step=0.5)
    print(f"  assembly path ({time.time() - t0:.0f}s)")
    res["handles"] = V.handle_checks(parts["base"], parts["roller"])
    res["insertion"] = V.insertion_path(parts["base"])
    print(f"  handle range ({time.time() - t0:.0f}s)")
    res["corners"] = V.corner_checks(False) + V.corner_checks(True)
    print(f"  printer-variation corners ({time.time() - t0:.0f}s)")
    res["models"] = V.mech_models(parts["roller"].volume(), parts["base"].volume())
    stl_dir = os.path.join(out, "models", "stl")
    res["files"] = [V.stl_file_check(os.path.join(stl_dir, fn)) for fn in sorted(os.listdir(stl_dir)) if fn.endswith(".stl")]
    res["files"].append(V.stl_file_check(os.path.join(out, "models", "HF04_Assembly.stl")))
    res["checks"] = verdicts(res)
    return res


def verdicts(r):
    out = []

    def chk(name, ok, detail):
        out.append(dict(check=name, ok=bool(ok), detail=detail))

    ps = r["parts"]
    chk("every part is one closed manifold shell", all(p["status"] == "NoError" and p["shells"] == 1 for p in ps.values()),
        ", ".join(f"{k}: {p['shells']} shell" for k, p in ps.items()))
    for key, label in (("sweep", "Standard"), ("sweep_grip", "Grip")):
        sw = r[key]
        ov = max(max(x["L_overlap"], x["R_overlap"]) for x in sw)
        chk(f"{label} roller: no collision over the full travel (both sides)", ov <= V.EPS_VOL,
            f"{len(sw)} positions x 2 sides, max overlap {ov:.4f} mm3")
    sw = r["sweep"]
    wall = min(min(x["L_gap_walls"], x["R_gap_walls"]) for x in sw)
    back = min(min(x["L_gap_back"], x["R_gap_back"]) for x in sw)
    mid = [x for x in sw if 0.5 < x["s"] < D.s_key - 0.5]
    stub = min(min(x["L_gap_stub"], x["R_gap_stub"]) for x in mid)
    chk("roller to pocket walls (not the ramp) >= 0.9 mm", wall >= 0.9, f"min {wall:.3f} mm (design 1.0)")
    chk("roller back face to back plate >= 0.25 mm", back >= 0.25, f"min {back:.3f} mm (design 0.30)")
    chk("stub floats in its T-slot between the stops", stub >= 0.2, f"min {stub:.3f} mm")
    ret = r["retention"]
    held = all(math.isfinite(x["forward_play"]) and x["forward_play"] < 1.5 for x in ret if x["s"] <= D.s_key - 1.5)
    free = not math.isfinite(ret[-1]["forward_play"])
    chk("roller cannot be pulled out anywhere except at the keyhole", held and free,
        f"forward play {min(x['forward_play'] for x in ret):.2f}-{max(x['forward_play'] for x in ret if math.isfinite(x['forward_play'])):.2f} mm; free at the keyhole: {free}")
    for k in ("assembly", "assembly_right"):
        a = r[k]
        chk(f"assembly path clear ({'left' if k == 'assembly' else 'right'} roller): in through the keyhole, roll down",
            not a["hits"], f"{a['steps_insert']} + {a['steps_roll']} poses, {len(a['hits'])} collisions")
    hs = r["handles"]
    ok = all(h["handle_base_overlap"] <= V.EPS_VOL and h["handle_roller_overlap"] <= V.EPS_VOL and h["roller_base_overlap"] <= V.EPS_VOL for h in hs)
    chk("handles 19-35 mm seat with no collision", ok, ", ".join(f"{h['handle_d']:.0f}" for h in hs))
    ok = all(h["contact_inside_flat"] for h in hs if h["rated"])
    chk("grip contact lands on the flat of the roller rim (rated sizes)", ok,
        f"min front margin {min(h['contact_margin_front'] for h in hs if h['rated']):.2f} mm")
    ins = r["insertion"]
    chk("channel lets every rated handle in from the front", not any(i["collides"] for i in ins),
        ", ".join(f"{i['handle_d']:.0f} mm: {i['min_gap_to_housings']:.1f} mm" for i in ins))
    for c in r["corners"]:
        good = c["assembly_hits"] == 0 and c["sweep_hits"] == 0 and all(
            x is not None and x > 0 for x in c["forward_play"])
        expect_fail = c["roller"] == "Standard" and c["corner"].startswith("very tight")
        marginal = good and c["min_stub_gap_in_travel"] < 0.1
        chk(f"printer corner [{c['corner']}] with {c['roller']} roller", good or expect_fail,
            ("MARGINAL (assembles in CAD with almost no gap): use the Loose roller" if marginal else
             "assembles, runs and is retained" if good else "BINDS: use the Loose roller (expected, documented)")
            + f"; min stub gap {c['min_stub_gap_in_travel']:.2f} mm")
    for fl in r["files"]:
        want = 3 if "Assembly" in fl["file"] else 1
        chk(f"exported file {fl['file']} re-read from disk: closed, {want} bod{'ies' if want > 1 else 'y'}",
            fl["non_manifold_edges"] == 0 and fl["misoriented_edges"] == 0 and fl["bodies"] == want and fl["zero_volume_bodies"] == 0,
            f"{fl['triangles']} triangles, {fl['non_manifold_edges']} open/non-manifold edges, {fl['bodies']} bodies, "
            f"{fl['zero_volume_bodies']} zero-volume")
    m = r["models"]
    chk("wedge friction needed <= 0.15 (PLA/PETG on handles ~0.2-0.4)", m["mu_required"] <= 0.15, f"tan(8 deg) = {m['mu_required']:.3f}")
    for k, p in ps.items():
        oh = p["overhang"]
        chk(f"{p['name']}: no overhang steeper than 45 deg; bridges small", oh["steep_area"] < 1.0 and oh["flat_area"] < 1.0,
            f"steep {oh['steep_area']:.2f} mm2, bridges {oh['flat_area']:.2f} mm2, engraving ceilings {oh['engraving_ceiling_area']:.0f} mm2, exactly 45 deg {oh['at_45_area']:.0f} mm2")
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--blend", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--samples", type=int, default=128)
    a = ap.parse_args(argv)
    t0 = time.time()
    parts = build_parts()
    pf = print_frames(parts)
    print(f"built parts ({time.time() - t0:.1f}s)")
    files = export_all(parts, pf, a.out)
    print("exported:", ", ".join(files))
    if not a.no_validate:
        res = run_validation(parts, pf, a.out, a.quick)
        with open(os.path.join(a.out, "models", "HF04_validation.json"), "w") as f:
            json.dump(res, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        write_report(res, os.path.join(a.out, "models", "HF04_validation_report.md"))
        bad = [c for c in res["checks"] if not c["ok"]]
        for c in res["checks"]:
            print(("PASS " if c["ok"] else "FAIL ") + c["check"] + " | " + c["detail"])
        print(f"{len(res['checks']) - len(bad)}/{len(res['checks'])} checks pass ({time.time() - t0:.0f}s)")
    if a.blend or a.render:
        from hf import scene

        scene.build(parts, pf, a.out, render=a.render, samples=a.samples)
    print(f"done ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main(sys.argv[1:])
