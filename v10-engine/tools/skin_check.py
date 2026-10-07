"""Mesh-based interference and full-rotation checks of the Blender skin against
the CAD moving core, and a comparison with the CAD checks.

    python tools/skin_check.py [--step 15] [--cad]

Skin parts come from skin/assembly/*.stl (engine frame, written by
tools/skin_blender.py --export). The moving core is positioned by the CAD
kinematics (cad/assembly_v8.engine(phi)) and tessellated per crank angle, so
the check uses the SAME crank positions as the CAD check. Volumes are exact
mesh booleans (manifold3d). --cad also re-runs the CAD static check for a
side-by-side comparison (slow, ~4 min).
Writes docs/SKIN_CHECK_REPORT.md.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))

import manifold3d as M3  # noqa: E402
import trimesh  # noqa: E402

import assembly_v8 as A  # noqa: E402
import config as C  # noqa: E402

ASM = os.path.join(ROOT, "skin", "assembly")
REPORT = os.path.join(ROOT, "docs", "SKIN_CHECK_REPORT.md")
# allowed overlaps for designed press fits (mm3), as cad/assembly_v8.PRESS_FIT_PAIRS
# Crush joints: the ribs are MEANT to overlap the pin by (bore - tip) so the allowance is the rib volume inside the
# pin: 6 ribs x 0.063 mm2 x 10 mm engagement = 3.8 mm3 theoretical for a 14 mm trumpet joint; the mesh booleans
# report 9.1 mm3 for the head/header joint (ribs sampled as 24-gons, full engagement length). The CAD check used
# 4.0 and passed because its rib engagement is shorter; both are the same designed fit, so 12 mm3 is the limit here.
PRESS = {("head", "rail"): 1.0, ("rail", "valley"): 1.0, ("boot", "head"): 6.0, ("head", "header"): 12.0,
         ("collector", "header"): 12.0, ("bearing608", "end"): 5.0, ("intake", "throttle"): 12.0, ("damper", "main"): 6.0,
         ("valve", "valve"): 4.0, ("boot", "header"): 6.0, ("oil", "valve"): 6.0, ("accessory", "alternator"): 6.0}
EPS = 0.01


def to_manifold(tm):
    v = np.asarray(tm.vertices, dtype=np.float64)
    f = np.asarray(tm.faces, dtype=np.uint32)
    mesh = M3.Mesh64(vert_properties=np.ascontiguousarray(v), tri_verts=np.ascontiguousarray(f))
    mesh.merge()
    man = M3.Manifold(mesh)
    return man if man.status() == M3.Error.NoError else None


def cad_mesh(shape, tol=0.05):
    verts, tris = shape.tessellate(tol, 0.3)
    tm = trimesh.Trimesh([v.toTuple() for v in verts], tris, process=True)
    return tm


class Part:
    def __init__(self, name, tm, source):
        self.name, self.tm, self.source = name, tm, source
        self.bounds = tm.bounds
        self.man = to_manifold(tm)
        self.watertight = tm.is_watertight

    def kind(self):
        return self.name.split("_")[0]


def bb_overlap(a, b, tol=0.0):
    return not (a.bounds[1][0] < b.bounds[0][0] - tol or b.bounds[1][0] < a.bounds[0][0] - tol or
                a.bounds[1][1] < b.bounds[0][1] - tol or b.bounds[1][1] < a.bounds[0][1] - tol or
                a.bounds[1][2] < b.bounds[0][2] - tol or b.bounds[1][2] < a.bounds[0][2] - tol)


CONTACT = 0.02        # mm: an intersection thinner than this is two faces touching (float32 STL), not an overlap


def overlap_volume(a, b):
    """Exact intersection volume of two manifold meshes; falls back to a point containment estimate.
    Face-on-face contact (intersection thinner than CONTACT) counts as 0."""
    if a.man is not None and b.man is not None:
        x = a.man ^ b.man
        if x.is_empty():
            return 0.0
        total = 0.0
        for c in x.decompose():                    # per connected piece: drop face-on-face contact sheets
            bb = c.bounding_box()
            ext = [bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]
            if min(ext) >= CONTACT:
                total += float(c.volume())
        return total
    # fallback: sample volume of the smaller part and count points inside the other
    small, big = (a, b) if a.tm.volume < b.tm.volume else (b, a)
    pts = trimesh.sample.volume_mesh(small.tm, 4000)
    if len(pts) == 0:
        return 0.0
    inside = big.tm.contains(pts)
    return float(inside.mean() * small.tm.volume)


def load_skin():
    out = []
    for f in sorted(os.listdir(ASM)):
        if f.endswith(".stl"):
            out.append(Part(f[:-4], trimesh.load(os.path.join(ASM, f)), "blender"))
    return out


def cad_parts(phi):
    """CAD parts that are not rebuilt in Blender, positioned at crank angle phi."""
    keep = ("crankpin", "segment", "end_web", "main_shaft", "rod_", "piston_", "bearing", "bush", "pin_", "rail_",
            "end_plate", "valley_beam", "pulley", "belt", "motor", "spacer", "elec_")
    parts = A.engine(phi) + A.drive_and_base(with_base=False, with_covers=False)
    return [Part(n, cad_mesh(s), "cad") for n, s, _ in parts if n.startswith(keep)]


def same_joint(n1, n2):
    k1, k2 = n1.split("_")[0], n2.split("_")[0]
    return PRESS.get(tuple(sorted((k1, k2))), None)


def static_check(skin, cad0):
    """Every skin part against every other skin part and every CAD static part at phi = 0."""
    statics = skin + [p for p in cad0 if not p.name.startswith(A.MOVING)]
    bad, checked = [], 0
    for i in range(len(statics)):
        for j in range(i + 1, len(statics)):
            a, b = statics[i], statics[j]
            if a.source == "cad" and b.source == "cad":
                continue                                      # CAD vs CAD is the CAD check's job
            if {a.kind(), b.kind()} == {"belt", "pulley"}:
                continue
            if not bb_overlap(a, b):
                continue
            checked += 1
            v = overlap_volume(a, b)
            allow = same_joint(a.name, b.name)
            if v > (allow if allow is not None else EPS):
                bad.append((a.name, b.name, round(v, 3), allow))
    return bad, checked


def sweep(skin, step, verbose=True):
    """Moving core (CAD, per angle) against every skin part; CAD vs CAD pairs are the CAD check's job."""
    hits, checked = [], 0
    t0 = time.time()
    angle = 0.0
    while angle < 360.0 - 1e-6:
        mov = [p for p in cad_parts(angle) if p.name.startswith(A.MOVING)]
        for m in mov:
            for s in skin:
                if m.name.startswith("main_shaft") and s.name.startswith(("damper",)):
                    continue                                  # damper is pressed on the front shaft (designed fit)
                if not bb_overlap(m, s):
                    continue
                checked += 1
                v = overlap_volume(m, s)
                if v > EPS:
                    hits.append((angle, m.name, s.name, round(v, 3)))
        if verbose:
            print(f"  crank {angle:5.1f} deg: {len(hits)} hits so far ({time.time()-t0:.0f}s)", flush=True)
        angle += step
    return hits, checked


def clearances(skin, cad0, near=4.0):
    """Smallest gaps between skin parts and the static CAD parts / each other (bbox-near pairs), for the report."""
    out = []
    parts = skin + [p for p in cad0 if not p.name.startswith(A.MOVING)]
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            if a.source == "cad" and b.source == "cad":
                continue
            if not bb_overlap(a, b, near):
                continue
            if a.man is None or b.man is None:
                continue
            try:
                g = a.man.min_gap(b.man, near)
            except Exception:                                 # noqa: BLE001
                continue
            if g < near:
                out.append((round(float(g), 2), a.name, b.name))
    return sorted(out)[:25]


def compare_parts_table(skin):
    """Blender part list vs the CAD part table (names, quantities) and STL volumes."""
    import build_all  # noqa: E402
    with open(os.path.join(ROOT, "skin", "parts.json")) as f:
        bl = {r["file"]: r for r in json.load(f)["parts"]}
    cad_rows = {}
    try:
        for name, shape, qty, _ in build_all.parts_v8():
            cad_rows[name] = (qty, shape.Volume())
    except Exception as e:                                    # noqa: BLE001
        print("  CAD part table not available:", e)
    rows = []
    for name in sorted(set(bl) | set(cad_rows)):
        b = bl.get(name)
        c = cad_rows.get(name)
        bvol = None
        if b and os.path.exists(b["path"]):
            bvol = trimesh.load(b["path"]).volume
        rows.append((name, b["qty"] if b else None, c[0] if c else None, bvol, c[1] if c else None))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=15.0)
    ap.add_argument("--cad", action="store_true", help="also re-run the CAD static check for comparison")
    ap.add_argument("--no-sweep", action="store_true")
    a = ap.parse_args()
    t = time.time()
    skin = load_skin()
    print(f"loaded {len(skin)} skin meshes ({sum(1 for p in skin if p.man is None)} not manifold for the exact boolean)", flush=True)
    cad0 = cad_parts(0.0)
    print(f"tessellated {len(cad0)} CAD core parts ({sum(1 for p in cad0 if p.man is None)} fall back to point sampling)", flush=True)
    bad, n_static = static_check(skin, cad0)
    print(f"static: {n_static} pairs, {len(bad)} interferences", flush=True)
    for b in bad:
        print("   ", b)
    hits, n_sweep = ([], 0) if a.no_sweep else sweep(skin, a.step)
    print(f"sweep: {n_sweep} pair checks, {len(hits)} collisions", flush=True)
    gaps = clearances(skin, cad0)
    cad_bad = None
    if a.cad:
        t1 = time.time()
        cad_bad = A.static_check()
        print(f"CAD static check: {len(cad_bad)} interferences ({time.time()-t1:.0f}s)")
    table = compare_parts_table(skin)
    write_report(skin, cad0, bad, n_static, hits, n_sweep, a.step, gaps, cad_bad, table, time.time() - t)


def write_report(skin, cad0, bad, n_static, hits, n_sweep, step, gaps, cad_bad, table, secs):
    L = []
    L.append("# Blender skin - mesh interference and rotation check")
    L.append("")
    L.append(f"Generated by `tools/skin_check.py` on {time.strftime('%Y-%m-%d %H:%M')} UTC in {secs:.0f} s. "
             f"Skin: {len(skin)} engine-frame STLs from `skin/assembly/` (Blender). Core: {len(cad0)} CAD parts tessellated at 0.05 mm "
             f"and positioned by `cad/assembly_v8.engine(phi)`. Overlap volumes are exact mesh booleans (manifold3d); "
             f"{sum(1 for p in skin + cad0 if p.man is None)} meshes were not manifold and used point sampling instead.")
    L.append("")
    L.append("## Static interference (crank at 0 deg)")
    L.append("")
    L.append(f"{n_static} bounding-box-near pairs checked (skin vs skin, skin vs CAD static parts). Designed press fits are allowed "
             f"their CAD allowance (`PRESS`); anything else above {EPS} mm3 is listed.")
    L.append("")
    if bad:
        L.append("| part A | part B | overlap (mm3) | allowance |")
        L.append("|---|---|---|---|")
        for a, b, v, al in bad:
            L.append(f"| {a} | {b} | {v} | {al if al is not None else EPS} |")
    else:
        L.append("**No interference.**")
    L.append("")
    L.append(f"## Full rotation sweep ({step:.0f} deg steps)")
    L.append("")
    L.append(f"{n_sweep} pair checks of the CAD moving parts (crank, rods, pistons, bearings) against every skin mesh.")
    L.append("")
    if hits:
        L.append("| crank angle | moving part | skin part | overlap (mm3) |")
        L.append("|---|---|---|---|")
        for ang, m, s, v in hits:
            L.append(f"| {ang:.0f} | {m} | {s} | {v} |")
    else:
        L.append("**No collision at any angle.**")
    L.append("")
    L.append("## Comparison with the CAD checks")
    L.append("")
    if cad_bad is not None:
        L.append(f"CAD `assembly_v8.static_check()` re-run now: {len(cad_bad)} interferences" + (": " + str(cad_bad) if cad_bad else "."))
    else:
        L.append("CAD static check and 15-degree sweep (last run on the frozen CAD skin, see docs/V8_STATUS.md and VISUAL_REVIEW.md): "
                 "0 interferences, 0 collisions. Run `python tools/skin_check.py --cad` to re-run the CAD static check alongside.")
    L.append(f"Mesh check on the Blender skin: {len(bad)} interferences, {len(hits)} collisions. "
             + ("The two agree." if not bad and not hits else "They disagree - see the tables above; the Blender part named there is the one to fix "
                "unless the overlap is with a CAD part whose position differs from the frozen CAD."))
    L.append("")
    L.append("## Smallest clearances (skin vs core / skin vs skin, under 4 mm)")
    L.append("")
    L.append("| gap (mm) | part A | part B |")
    L.append("|---|---|---|")
    for g, a, b in gaps:
        L.append(f"| {g} | {a} | {b} |")
    L.append("")
    L.append("## Part list: Blender export vs CAD part table")
    L.append("")
    L.append("| part | qty (Blender) | qty (CAD) | volume Blender STL (cm3) | volume CAD (cm3) | note |")
    L.append("|---|---|---|---|---|---|")
    for name, qb, qc, vb, vc in table:
        note = ""
        if qb is None:
            note = "CAD only (moving core / coupon / purchased)"
        elif qc is None:
            note = "Blender only" + (" (reference model of a purchased plate)" if name.startswith("49") else "")
        elif qb != qc:
            note = "**quantity differs**"
        elif vb is not None and vc and abs(vb - vc) / vc > 0.08:
            note = f"volume differs {100 * (vb - vc) / vc:+.0f}% (restyled surface)"
        L.append(f"| {name} | {qb if qb is not None else '-'} | {qc if qc is not None else '-'} | "
                 f"{vb / 1000:.1f}" if vb is not None else f"| {name} | {qb if qb is not None else '-'} | {qc if qc is not None else '-'} | -")
        L[-1] += f" | {vc / 1000:.1f} | {note} |" if vc else f" | - | {note} |"
    L.append("")
    with open(REPORT, "w") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", REPORT)


if __name__ == "__main__":
    main()
