"""
ODD LAYER  ML-02  MOTIONLOOP
============================

A hand-cranked desk mechanism: one crank drives two opposed sliders through two connecting
rods. The crank is a built-up two-throw crankshaft (cheek | wheel | cheek) whose pins sit
180 degrees apart, so the sliders breathe in and out together (MIRROR). Swapping one part, the
centre wheel, puts the pins in line (SHUTTLE): then the left slider moves out while the right
one moves in.

This script builds every part with bmesh and exact booleans, validates the geometry and the
mechanism (intersections over a full turn, clearances, wall thickness, overhangs, weak links),
exports STL and 3MF, saves an organised .blend and, with --render, renders the product shots.

Run (Blender 4.2+, or the `bpy` 4.2 module on Python 3.11):

    blender -b -P motionloop.py -- --out .                 # build, validate, export, .blend
    blender -b -P motionloop.py -- --out . --render        # ...and the renders
    python motionloop.py --out . [--render]                # with `pip install bpy==4.2.*`
    python tools/make_docs.py                              # drawings, charts, report (no bpy)

Status: designed and checked in CAD only. Nothing has been printed or physically tested.
"""

import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from ml import geom as G  # noqa: E402
from ml import parts as PT  # noqa: E402
from ml import validate as VA  # noqa: E402
from ml import export as EX  # noqa: E402
from ml import scene as SC  # noqa: E402
from ml.params import P, D  # noqa: E402


def log(*a):
    print("[ML-02]", *a, flush=True)


def reset():
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    else:  # running inside an open Blender file: remove a previous build only
        for c in list(bpy.data.collections):
            if c.name.startswith("ML02_") or c.name == "_work":
                for ob in list(c.objects):
                    bpy.data.objects.remove(ob)
                bpy.data.collections.remove(c)
    G.COLL.clear()
    w = G.collection("_work")
    return w


def build():
    t = time.time()
    parts = {
        "frame": PT.build_plinth(),
        "wheel_mirror": PT.build_wheel(False),
        "wheel_shuttle": PT.build_wheel(True),
        "cheek": PT.build_cheek(),
        "rod": PT.build_rod(),
        "slider": PT.build_slider(),
        "pin": PT.build_pin(),
        "cap": PT.build_cap(),
        "handle": PT.build_handle(),
        "knob": PT.build_knob(),
    }
    log(f"built {len(parts)} parts in {time.time() - t:.1f} s")
    return parts


def overall_dims(parts):
    """Envelope of the assembly over a full turn (handle sweep included)."""
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for k in range(0, 360, 10):
        B = VA.bodies(parts, math.radians(k), "mirror")
        for lst in B.values():
            for ob, M in lst:
                for v in ob.data.vertices:
                    q = M @ v.co
                    lo = Vector((min(lo.x, q.x), min(lo.y, q.y), min(lo.z, q.z)))
                    hi = Vector((max(hi.x, q.x), max(hi.y, q.y), max(hi.z, q.z)))
    return dict(lo=[round(x, 2) for x in lo], hi=[round(x, 2) for x in hi],
                size=[round(h - l, 2) for h, l in zip(hi, lo)])


def sections(parts):
    """Section polylines for the drawings (crank angle 0, MIRROR)."""
    B = VA.bodies(parts, 0.0, "mirror")
    named = []
    for body, lst in B.items():
        for ob, M in lst:
            named.append((body, ob.name, ob, M))
    out = {}
    cuts = {
        "front_y0": (Vector((0, 1.0, 0)), Vector((0, 1, 0))),  # y = 1: clear of the key edges
        "rodplane_yA": (Vector((0, (D["Y_ROD0"] + D["Y_ROD1"]) / 2, 0)), Vector((0, 1, 0))),
        "stack_x0": (Vector((0.0, 0, 0)), Vector((1, 0, 0))),
        "plan_z1": (Vector((0, 0, 1.0)), Vector((0, 0, 1))),
        "plan_ztop": (Vector((0, 0, D["PLINTH_TOP"] - 0.3)), Vector((0, 0, 1))),
        "plan_zaxle": (Vector((0, 0, P.AXLE_Z)), Vector((0, 0, 1))),
    }
    for cname, (co, no) in cuts.items():
        out[cname] = []
        for body, nm, ob, M in named:
            for line in G.section_polylines(ob, co, no, M):
                if len(line) > 1:
                    out[cname].append(dict(body=body, part=nm, pts=line))
    return out


def embed_sources():
    for root, _, files in os.walk(HERE):
        if any(s in root for s in ("__pycache__", "models", "renders", "docs")):
            continue
        for f in sorted(files):
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, f), HERE)
                txt = bpy.data.texts.get(rel) or bpy.data.texts.new(rel)
                txt.clear()
                with open(os.path.join(root, f)) as fh:
                    txt.write(fh.read())


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated shot names to render")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--res", default="1600x1200")
    ap.add_argument("--quick", action="store_true", help="skip the full-rotation sweeps")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out)
    models = os.path.join(out, "models")
    os.makedirs(models, exist_ok=True)
    t0 = time.time()
    reset()
    parts = build()

    # ---------------- validation ----------------
    rep = {"status": "CAD only - not printed or physically tested", "params": {
        k: v for k, v in vars(P).items() if not k.startswith("_") and not callable(v)},
        "derived": D}
    rep["parts"] = {k: G.mesh_stats(ob) for k, ob in parts.items()}
    rep["kinematics"] = {}
    for cfg, p in (("mirror", VA.PMirror), ("shuttle", VA.PShuttle)):
        kin = VA.kinematics(p)
        rows = kin.pop("rows")
        kin["rows_5deg"] = [[round(r[0], 1), round(r[1], 4), round(r[2], 4)] for r in rows[::10]]
        kin["rod_pose_error_mm"] = VA.rod_length_check(parts, cfg)
        rep["kinematics"][cfg] = kin
    log("kinematics done")
    rep["designed_contacts"] = VA.designed_contacts(parts)
    log("designed contacts:", {k: (round(v, 3) if isinstance(v, float) else v)
                               for k, v in rep["designed_contacts"].items()})
    rep["sweep"] = {}
    if not a.quick:
        pts_cache = VA._local_points(parts, 0.8)
        for cfg in ("mirror", "shuttle"):
            res, lowest = VA.sweep(parts, cfg, 2.0, 5, pts_cache, log)
            rep["sweep"][cfg] = {
                f"{x}|{y}": dict(hits=r["hits"], hit_angles=r["hit_angles"][:10],
                                 min_gap=round(r["min_gap"], 3), at_deg=r["at"], where=r["where"])
                for (x, y), r in res.items()}
            rep["sweep"][cfg]["handle_lowest_z"] = round(lowest, 3)
            bad = {k: v for k, v in res.items() if v["hits"]}
            log(f"  {cfg}: intersecting pairs: {len(bad)}; handle lowest z {lowest:.2f}")
    rep["expected_gaps"] = {f"{x}|{y}": dict(gap=g, what=w) for (x, y), (g, w) in VA.EXPECTED.items()}
    rep["print"] = VA.print_checks(parts)
    rep["strength"] = VA.strength()
    rep["overall"] = overall_dims(parts)
    log("overall envelope", rep["overall"]["size"])

    # ---------------- export ----------------
    pm = VA.print_matrices()
    files, plate, _ = EX.export_all(parts, pm, os.path.join(models, "stl"), os.path.join(models, "3mf"), log)
    rep["files"] = files
    rep["plate"] = [dict(name=n, part=k, centre=[round(c, 1) for c in xy]) for n, k, xy in plate]
    rep["mass_g_petg_solid_upper_bound"] = round(sum(
        rep["parts"][k]["volume_mm3"] * q for k, _, _, q in EX.BOM) * 1.27e-3, 1)
    with open(os.path.join(models, "ML02_validation.json"), "w") as f:
        json.dump(rep, f, indent=1, default=lambda o: list(o) if hasattr(o, "__iter__") else str(o))
    with open(os.path.join(models, "ML02_geometry.json"), "w") as f:
        json.dump(sections(parts), f)
    log("validation + geometry json written")

    # ---------------- scene, .blend ----------------
    scene = bpy.context.scene
    scene.name = "ML-02 MotionLoop"
    colls = SC.organise(parts, plate, pm)
    SC.build_studio()
    w, h = (int(x) for x in a.res.split("x"))
    SC.setup_render(scene, a.samples, (w, h))
    shots = SC.shots(scene, colls, parts)
    work = G.COLL.get("_work")
    if work is not None:
        for ob in list(work.objects):
            bpy.data.objects.remove(ob)
        bpy.data.collections.remove(work)
    colls["asm"].hide_render = False
    embed_sources()
    blend = os.path.join(models, "ML02_MotionLoop.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    log("saved", blend)

    if a.render:
        rdir = os.path.join(out, "renders")
        os.makedirs(rdir, exist_ok=True)
        only = set(s for s in a.only.split(",") if s)
        for name, fn in shots:
            if only and name not in only:
                continue
            fn()
            if name.startswith("08_motion"):
                scene.render.resolution_x, scene.render.resolution_y = 1200, 640
            else:
                scene.render.resolution_x, scene.render.resolution_y = w, h
            scene.render.filepath = os.path.join(rdir, name + ".png")
            t = time.time()
            bpy.ops.render.render(write_still=True)
            log(f"rendered {name} in {time.time() - t:.0f} s")
    log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
