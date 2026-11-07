"""
BK-01 BOOKMARKS: a book-shaped bookmark holder
==============================================

A miniature hardcover standing upright with an open top: rounded spine, cover boards with
hinge grooves, a page block with page lines on the fore-edge and at the head, a raised
nameplate reading "Bookmarks", and a meadow of flowers in relief below it.

    envelope   79.0 x 44.5 x 84.3 mm  (3.11 x 1.75 x 3.32 in), decoration included
    storage    69.45 x 38.7 mm opening, 81.9 mm deep, 2.0 mm walls, 2.4 mm floor
    printing   upright, open top up, no supports, 6 independently colourable regions

This script builds the part as exact manifold solids (manifold3d + shapely), validates it,
exports STL / 3MF and the reports. With --blend it also builds the Blender project, with
--render it renders the product images, with --docs it draws the engineering drawing.

    pip install manifold3d shapely numpy matplotlib fonttools trimesh   (and `pip install bpy`)
    python bookmarks.py                          # build, validate, export
    python bookmarks.py --blend --render --docs  # ...plus .blend, renders, drawing

Every dimension lives in bk/params.py.
"""

import argparse
import json
import os
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bk import geom as G  # noqa: E402
from bk import params as P  # noqa: E402
from bk import props  # noqa: E402
from bk import validate as V  # noqa: E402
from bk.export import write_3mf, write_stl  # noqa: E402
from bk.report import write_report  # noqa: E402

ORDER = ["body", "pages", "lettering", "petals", "centres", "foliage"]
PLAN_FILES = {"FULL": "BK01_Bookmarks_4colour.3mf", "TRIO": "BK01_Bookmarks_3colour.3mf",
              "DUO": "BK01_Bookmarks_2colour.3mf"}


def export_all(result, out, thumb=None):
    M = os.path.join(out, "models")
    S, T = os.path.join(M, "stl"), os.path.join(M, "3mf")
    os.makedirs(S, exist_ok=True)
    os.makedirs(T, exist_ok=True)
    files = {}
    p = os.path.join(S, "BK01_Bookmarks_single_colour.stl")
    write_stl(p, result["full"], "BK-01 Bookmarks single colour")
    files["single"] = p
    for i, k in enumerate(ORDER, start=1):
        p = os.path.join(S, f"BK01_region{i}_{k}.stl")
        write_stl(p, result["parts"][k], f"BK-01 region {k}")
        files[k] = p
    for plan, fname in PLAN_FILES.items():
        spec = P.PLANS[plan]
        note = "; ".join(f"Filament {s} = {n}" for s, (n, h) in spec["filaments"].items())
        parts = [(f"{i} {k.capitalize()} - F{spec['slots'][k]} {spec['filaments'][spec['slots'][k]][0]}",
                  result["parts"][k]) for i, k in enumerate(ORDER, start=1)]
        p = os.path.join(T, fname)
        write_3mf(p, parts, f"BK-01 Bookmarks ({plan})", [spec["slots"][k] for k in ORDER], thumbnail=thumb,
                  title=f"BK-01 Bookmarks - {len(spec['filaments'])}-colour", filament_note=note)
        files[plan] = p
    return files


def read_3mf_parts(path):
    """Independent 3MF reader: follow the build item's components to their mesh files and
    read exactly the referenced object from each. Returns [(name, (v, t))], the filament
    slot of each part from model_settings.config, and the zip entry names."""
    import re
    import xml.etree.ElementTree as ET

    import numpy as np

    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    pns = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path"
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("3D/3dmodel.model"))
    item = root.find("m:build/m:item", ns)
    top = [o for o in root.iter("{%s}object" % ns["m"]) if o.get("id") == item.get("objectid")][0]
    parts = []
    for comp in top.iter("{%s}component" % ns["m"]):
        sub = ET.fromstring(z.read(comp.get(pns).lstrip("/")))
        obj = [o for o in sub.iter("{%s}object" % ns["m"]) if o.get("id") == comp.get("objectid")]
        assert len(obj) == 1, "component must resolve to exactly one object"
        mesh = obj[0].find("m:mesh", ns)
        v = np.array([[float(e.get(a)) for a in "xyz"] for e in mesh.iter("{%s}vertex" % ns["m"])])
        t = np.array([[int(e.get(a)) for a in ("v1", "v2", "v3")] for e in mesh.iter("{%s}triangle" % ns["m"])])
        parts.append((obj[0].get("name"), (v, t)))
    cfg = z.read("Metadata/model_settings.config").decode()
    ext = [int(x) for x in re.findall(r'<part id="\d+" subtype="normal_part">\s*<metadata key="name" value="[^"]*"/>\s*'
                                      r'<metadata key="matrix" value="[^"]*"/>\s*<metadata key="extruder" value="(\d+)"/>', cfg)]
    return parts, ext, z.namelist()


def reread(files, result):
    """Read every exported file back from disk and check it, independently of manifold3d."""
    import numpy as np
    import trimesh

    rows, ok = [], True
    for k, p in files.items():
        if p.endswith(".stl"):
            m = trimesh.load(p, force="mesh")
            src = result["full"] if k == "single" else result["parts"][k]
            dv = abs(m.volume - src.volume()) / src.volume()
            good = bool(m.is_watertight and m.is_winding_consistent and m.volume > 0 and dv < 1e-4)
            rows.append(dict(file=os.path.relpath(p, HERE), triangles=len(m.faces), watertight=bool(m.is_watertight),
                             winding=bool(m.is_winding_consistent), volume=round(float(m.volume), 2),
                             extents=[round(float(e), 3) for e in m.extents], ok=good))
            ok &= good
        else:
            parts, ext, names = read_3mf_parts(p)
            vols, wt, allv = [], True, []
            for name, (vv, tt) in parts:
                m = trimesh.Trimesh(vv, tt, process=True)      # weld by position, as a slicer does
                wt &= bool(m.is_watertight and m.is_winding_consistent)
                vols.append(round(float(m.volume), 2))
                allv.append(m.vertices)
            want = [round(result["parts"][k].volume(), 2) for k in ORDER]
            allv = np.vstack(allv)
            ext_mm = (allv.max(0) - allv.min(0)).round(3).tolist()
            plan = [k for k, f in PLAN_FILES.items() if p.endswith(f)][0]
            exp_slots = [P.PLANS[plan]["slots"][k] for k in ORDER]
            good = (len(parts) == 6 and wt and max(abs(a - b) for a, b in zip(vols, want)) < 0.05
                    and ext == exp_slots)
            rows.append(dict(file=os.path.relpath(p, HERE), triangles=sum(len(t) for _, (v, t) in parts),
                             watertight=wt, winding=wt, volume=round(sum(vols), 2), extents=ext_mm,
                             part_extruders=ext, ok=good))
            ok &= good
    return V.check("Exported files re-read from disk: watertight, correct volumes, correct filament slots", ok, rows=rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--blend", action="store_true", help="build the Blender project (needs bpy)")
    ap.add_argument("--render", action="store_true", help="render the product images (implies --blend)")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--shots", default="", help="comma list of shot prefixes to render, e.g. 01,02")
    ap.add_argument("--docs", action="store_true", help="draw the dimensioned engineering drawing")
    a = ap.parse_args()

    t0 = time.time()
    print("building geometry ...")
    result = G.build()
    print(f"  {time.time() - t0:.1f}s")

    print("validating ...")
    checks = V.run_all(result)
    thumb = os.path.join(a.out, "renders", "01_hero.png")
    files = export_all(result, a.out, thumb if os.path.exists(thumb) else None)
    checks.append(reread(files, result))
    for c in checks:
        print(("  PASS  " if c["ok"] else "  FAIL  ") + c["name"])

    M = os.path.join(a.out, "models")
    with open(os.path.join(M, "BK01_validation.json"), "w") as f:
        json.dump(dict(params=P.summary(), checks=checks), f, indent=1, default=str)
    write_report(os.path.join(M, "BK01_validation_report.md"), checks, result)

    if a.docs:
        from bk import drawing
        drawing.draw_all(result, os.path.join(a.out, "docs"))
    if a.blend or a.render:
        from bk import scene
        scene.build(result, a.out, props.bookmark_set(), render=a.render, samples=a.samples,
                    shots=[s for s in a.shots.split(",") if s] or None)
        if a.render and os.path.exists(thumb):
            export_all(result, a.out, thumb)   # re-pack the 3MFs with the fresh plate thumbnail
    bad = [c["name"] for c in checks if not c["ok"]]
    print(f"done in {time.time() - t0:.0f}s; {len(checks) - len(bad)}/{len(checks)} checks pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
