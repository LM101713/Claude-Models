#!/usr/bin/env python
"""V8 display engine - Blender skin build / export / check / render.

    python tools/skin_blender.py --all                 (bpy as a Python module)
    blender -b -P tools/skin_blender.py -- --all        (Blender binary, headless)

Every dimension comes from skin/params.json (written by tools/export_params.py
from config.py / fits.py). Steps:
  --build    build the part library in Blender (tools/skin/parts/*)
  --export   print-oriented STLs with part numbers -> skin/, engine-frame
             copies -> skin/assembly/ (for the mesh interference checks)
  --check    mesh checks + fit measurement on the exported STLs -> docs/SKIN_PRINT_REPORT.md
  --render   full engine studio renders from the reference angles -> renders/skin_round<N>/
"""
import argparse
import json
import math
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from skin import bpyutil as U, fitcut as F, materials as M, measure as MS, studio as S  # noqa: E402
from skin.params import P  # noqa: E402
from skin.parts import block, exhaust, front, heads, intake, pan, stand  # noqa: E402

SKIN_DIR = os.path.join(ROOT, "skin")
ASM_DIR = os.path.join(SKIN_DIR, "assembly")
CORE_DIR = os.path.join(SKIN_DIR, "core")
REPORT = os.path.join(ROOT, "docs", "SKIN_PRINT_REPORT.md")
FIT_TOL = 0.02                                   # mm, on bores / rib tips measured on the exported STL
# build volumes (W x D x H, mm) from the Bambu Lab specification pages; the design limit is the smallest
PLATES = {"H2S": (340, 320, 340), "H2C single nozzle": (325, 320, 325), "H2C dual nozzle (design limit)": (300, 320, 320)}
LIMIT = PLATES["H2C dual nozzle (design limit)"]
NOZZLE = 0.4
MIN_WALL = 2 * NOZZLE                            # a wall thinner than two perimeters is a slicing risk
OVERHANG_DEG = 47.0                              # faces steeper than this (from vertical) count as overhang; 45 deg designs pass
NEAR_BED = 3.0                                   # mm: bottom-edge bevels below this height are listed separately (they print)
SLIVER = 1e-6                                    # mm2: faces below this are slivers left by the mesh merge (harmless when watertight)


def rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def align(v_from, v_to):
    """Rotation matrix taking direction v_from onto v_to."""
    return Vector(v_from).rotation_difference(Vector(v_to)).to_matrix().to_4x4()


def _primary_print():
    g = exhaust.geometry()
    return align(g["t3"], (0, 0, -1))              # pipe end direction -> straight down (stands on the collector spigot)


def _throttle_print():
    axis, base = intake.tb_axis()
    return align(axis, (0, 0, -1)) @ Matrix.Translation(-Vector(base))   # bore face down, spigot up


# (file, library key, qty per engine, palette slot, mirror in Y, print orientation matrix factory, note)
PARTS = [
    ("01_crankcase", "case", 1, "slot1", False, lambda: Matrix.Identity(4), "pan rail down (as CAD)"),
    ("03_cylinder_bank", "bank", 2, "slot1", False, lambda: rx(180), "deck face down, bores vertical"),
    ("30_cylinder_head_A", "head", 1, "slot1", False, lambda: Matrix.Identity(4), "deck face down"),
    ("30B_cylinder_head_B", "head", 1, "slot1", True, lambda: Matrix.Identity(4), "deck face down (mirror of 30)"),
    ("31_valve_cover", "valve_cover", 2, "slot2", False, lambda: rx(180), "top face down on the textured plate"),
    ("31B_oil_cap", "oil_cap", 2, "slot2", False, lambda: rx(180), "cap top down, spigot up"),
    ("32_plug_boot", "boot", 8, "slot4", False, lambda: Matrix.Identity(4), "shaft end down, dome up"),
    ("33_header_primary_A", "primary", 4, "slot3", False, _primary_print, "standing on the collector spigot"),
    ("33B_header_primary_B", "primary", 4, "slot3", True, _primary_print, "standing on the collector spigot (mirror)"),
    ("34_header_plate_A", "plate", 1, "slot3", False, lambda: rx(-90), "outboard face up, flat"),
    ("34B_header_plate_B", "plate", 1, "slot3", True, lambda: rx(90), "outboard face up, flat (mirror; mirrored in Y, so the opposite turn)"),
    ("35_collector_A", "collector_A", 1, "slot3", False, lambda: ry(-90), "standing on the open tail"),
    ("35B_collector_B", "collector_B", 1, "slot3", False, lambda: ry(-90), "standing on the open tail"),
    ("36_intake_lid", "intake_lid", 1, "slot1", False, lambda: rx(180), "top face down"),
    ("36B_intake_base", "intake_base", 1, "slot1", False, lambda: Matrix.Identity(4), "flange down"),
    ("36C_throttle_body", "throttle", 1, "slot3", False, _throttle_print, "bore face down, spigot up"),
    ("40_oil_pan", "pan", 1, "slot2", False, lambda: rx(180), "top skin down, open floor up"),
    ("41_pan_floor_panel", "panel", 1, "slot2", False, lambda: Matrix.Identity(4), "flat"),
    ("42_bellhousing", "bellhousing", 1, "slot1", False, lambda: ry(-90), "rear face down"),
    ("43_front_cover", "front_cover", 1, "slot1", False, lambda: ry(90), "front face down"),
    ("44_damper", "damper", 1, "slot2", False, lambda: ry(-90), "back face down"),
    ("45_accessory_module", "accessory", 1, "slot2", False, lambda: ry(-90), "back plate down"),
    ("45B_alternator_body", "alt_body", 1, "slot2", False, lambda: ry(-90), "rear (slotted) face down, spigot up"),
    ("46_stand_plate", "stand_plate", 1, "slot2", False, lambda: rx(180), "chamfered top face down (as CAD)"),
    ("47_bracket", "bracket", 2, "slot2", False, lambda: ry(90), "lying on its side"),
    ("47B_bracket_mirror", "bracket_m", 2, "slot2", False, lambda: ry(90), "lying on its side"),
    ("48_controls_plinth", "plinth", 1, "slot2", False, lambda: rx(180), "top face down, open bottom up"),
    ("49_edition_plate", "edition_plate", 1, "purchased", False, lambda: ry(90), "reference model of the engraved plate (bought, not printed)"),
]

SLOT_MATERIAL = {"slot1": M.satin_alu, "slot2": M.matte_black, "slot3": M.painted_header, "slot4": M.amber_boot,
                 "purchased": M.brushed_plate, "core": M.dark_steel}

LIB = {}
PLACED = []
TIMES = {}
FINALIZE = {}


def build_library():
    t = time.time()
    steps = [("case", block.crankcase), ("bank", block.cylinder_bank)]
    LIB.update({})
    for k, fn in steps:
        t0 = time.time()
        LIB[k] = fn()
        TIMES[k] = time.time() - t0
    for mod in (heads, intake, exhaust, pan, front, stand):
        t0 = time.time()
        LIB.update(mod.build_all())
        TIMES[mod.__name__.split(".")[-1]] = time.time() - t0
    for k, o in LIB.items():
        ok, msg = U.finalize(o)
        FINALIZE[k] = (ok, msg)
        if not ok:
            print("  FINALIZE FAIL", msg, flush=True)
    print(f"library: {len(LIB)} parts in {time.time()-t:.0f}s", flush=True)
    return LIB


def place_all(phi=0.0, with_core=False):
    """Engine-frame copies of every skin part (+ the CAD core meshes from skin/core if asked)."""
    out = []
    out += block.placed(U.copy(LIB["case"], "crankcase"), LIB["bank"])
    out += heads.placed(LIB)
    out += intake.placed(LIB)
    out += exhaust.placed(LIB)
    out += pan.placed(LIB)
    out += front.placed(LIB, phi)
    out += stand.placed(LIB)
    slot_of = {}
    for file, key, *_ in PARTS:
        slot = [p[3] for p in PARTS if p[1] == key][0]
        slot_of[key] = slot
    named = []
    for name, obj in out:
        key = _lib_key_for_placed(name)
        slot = slot_of.get(key, "slot1")
        U.set_material(obj, SLOT_MATERIAL[slot]())
        named.append((name, obj, slot))
    if with_core and os.path.isdir(CORE_DIR):
        for f in sorted(os.listdir(CORE_DIR)):
            if not f.endswith(".stl"):
                continue
            bpy.ops.wm.stl_import(filepath=os.path.join(CORE_DIR, f), global_scale=1.0)
            o = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.data.objects[-1]
            o.name = "core_" + f[:-4]
            for c in o.users_collection:
                c.objects.unlink(o)
            U.collection("COL_core").objects.link(o)
            U.set_material(o, M.dark_steel())
            U.shade(o)
            named.append((o.name, o, "core"))
    PLACED[:] = named
    return named


def _lib_key_for_placed(name):
    table = {"crankcase": "case", "bank": "bank", "head_": "head", "valve_cover": "valve_cover", "oil_cap": "oil_cap",
             "header_plate": "plate", "boot": "boot", "header_": "primary", "collector": "collector_A", "intake_lid": "intake_lid",
             "intake_base": "intake_base", "throttle": "throttle", "pan_panel": "panel", "pan": "pan", "bellhousing": "bellhousing",
             "front_cover": "front_cover", "damper": "damper", "accessory": "accessory", "alternator": "alt_body", "stand_plate": "stand_plate",
             "bracket": "bracket", "plinth": "plinth", "edition": "edition_plate"}
    for k in ("pan_panel", "header_plate", "intake_lid", "intake_base", "stand_plate", "valve_cover", "front_cover"):
        if name.startswith(k):
            return table[k]
    for k, v in table.items():
        if name.startswith(k):
            return v
    return "case"


def settle(obj):
    """Print orientation finishing: part centred in XY, lowest point on z = 0. Returns the translation matrix."""
    bb = U.bbox(obj)
    T = Matrix.Translation((-(bb[0] + bb[1]) / 2, -(bb[2] + bb[3]) / 2, -bb[4]))
    U.transform(obj, T)
    return T


def export_parts():
    import trimesh
    os.makedirs(SKIN_DIR, exist_ok=True)
    rows = []
    for file, key, qty, slot, mirror, mfac, note in PARTS:
        src = LIB[key]
        obj = U.copy(src, file)
        Mm = Matrix.Identity(4)
        if mirror:
            m = U.mirror_y(obj, file)
            U.delete(obj)
            obj = m
            Mm = Matrix.Scale(-1, 4, (0, 1, 0))
        Mp = mfac()
        U.transform(obj, Mp)
        T = settle(obj)
        Mtot = T @ Mp @ Mm
        path = os.path.join(SKIN_DIR, file + ".stl")
        U.export_stl(obj, path, do_finalize=True)          # re-merge after the rotation (float32 rounding moved)
        rows.append(dict(file=file, key=key, qty=qty, slot=slot, note=note, lib_name=src.name, M=[list(r) for r in Mtot], path=path))
        U.delete(obj)
    with open(os.path.join(SKIN_DIR, "parts.json"), "w") as f:
        json.dump(dict(parts=rows, fits=F.FITS, finalize={k: v[1] for k, v in FINALIZE.items()}), f, indent=1)
    print(f"exported {len(rows)} STLs -> skin/", flush=True)
    return rows


def export_assembly(phi=0.0):
    os.makedirs(ASM_DIR, exist_ok=True)
    for f in os.listdir(ASM_DIR):
        if f.endswith(".stl"):
            os.remove(os.path.join(ASM_DIR, f))
    placed = place_all(phi, with_core=False)
    for name, obj, slot in placed:
        U.export_stl(obj, os.path.join(ASM_DIR, name + ".stl"), do_finalize=True)
    print(f"exported {len(placed)} engine-frame STLs -> skin/assembly/", flush=True)
    for _, obj, _ in placed:
        U.delete(obj)


def _plate_fit(dims):
    """dims = (dx, dy, dz) in print orientation; the part may be turned 90 deg about Z on the bed."""
    dx, dy, dz = dims
    out = {}
    for name, (W, D, H) in PLATES.items():
        out[name] = (dx <= W and dy <= D and dz <= H) or (dy <= W and dx <= D and dz <= H)
    return out


def check_parts(rows):
    import numpy as np
    import trimesh
    results = []
    for r in rows:
        m = trimesh.load(r["path"])
        raw = trimesh.load(r["path"], process=False)
        bb = m.bounds
        dims = tuple(float(v) for v in (bb[1] - bb[0]))
        areas = m.area_faces
        degenerate = int((areas < SLIVER).sum())
        # overhangs in print orientation: faces looking down more than 45 deg, not on the bed
        n = m.face_normals
        centers = m.triangles_center
        steep = n[:, 2] < -math.sin(math.radians(OVERHANG_DEG))          # normal pointing down more than OVERHANG_DEG from vertical
        down = steep & (centers[:, 2] > NEAR_BED)
        overhang_area = float(areas[down].sum())
        near_bed_area = float(areas[steep & (centers[:, 2] > 0.3) & (centers[:, 2] <= NEAR_BED)].sum())   # bottom-edge bevels
        # min wall: ray thickness from sampled surface points inward
        try:
            pts, fid = trimesh.sample.sample_surface(m, 2500, seed=1)
            th = trimesh.proximity.thickness(m, pts, exterior=False, normals=m.face_normals[fid], method='ray')
            th = th[np.isfinite(th) & (th > 1e-6)]
            min_wall = float(np.percentile(th, 1)) if len(th) else float("nan")      # 1st percentile: single grazing rays ignored
            thin = int((th < MIN_WALL).sum()) if r["slot"] != "purchased" else 0
        except Exception as e:                                    # noqa: BLE001
            min_wall, thin = float("nan"), -1
        fits = MS.measure(m, F.FITS.get(r["lib_name"], []), r["M"])
        bad_fits = [f for f in fits if f["n"] == 0 or f.get("dev", 9) > FIT_TOL]
        res = dict(r, faces=len(m.faces), watertight=bool(m.is_watertight), winding=bool(m.is_winding_consistent),
                   volume=float(m.volume), dims=dims, degenerate=degenerate, overhang_area=overhang_area, near_bed_area=near_bed_area, min_wall=min_wall,
                   thin_samples=thin, plate=_plate_fit(dims), fits=fits, bad_fits=bad_fits, raw_verts=len(raw.vertices))
        results.append(res)
        flag = "" if res["watertight"] and not bad_fits and res["plate"]["H2C dual nozzle (design limit)"] else "  <-- CHECK"
        print(f"  {r['file']:26s} wt={str(res['watertight']):5s} vol={res['volume']:9.0f} dims={dims[0]:6.1f}x{dims[1]:6.1f}x{dims[2]:6.1f} "
              f"fits {len(fits)-len(bad_fits)}/{len(fits)} minwall {min_wall:.2f} overhang {overhang_area:.0f}mm2{flag}", flush=True)
    return results


def write_report(results):
    import trimesh
    lines = []
    L = lines.append
    L("# Blender skin - print and fit report")
    L("")
    L(f"Generated by `tools/skin_blender.py --check` on {time.strftime('%Y-%m-%d %H:%M')} UTC. "
      f"Blender (bpy) {bpy.app.version_string}, Python {platform.python_version()}, trimesh {trimesh.__version__}.")
    L("Every dimension in these parts comes from `skin/params.json` (exported from `config.py` / `fits.py`); "
      "nothing in `tools/skin/` holds an engine dimension of its own.")
    L("")
    L("## What is cut where")
    L("")
    L("All mounting and fit features are cut in Blender at the parameter positions with 128-segment cylinders "
      "(crush ribs 24 segments at 0.6 mm radius; the collector saddle 136 segments - see the code comments for why). "
      "Nothing is cut after import in CAD. The moving core (crank, rods, pistons, rails, end plates, valley beam, "
      "bearings, drive) stays in CAD and is the reference the skin is checked against (`tools/skin_check.py`).")
    L("")
    L("## Parts")
    L("")
    L(f"Design limit {LIMIT[0]} x {LIMIT[1]} x {LIMIT[2]} mm (H2C dual nozzle). Plate columns: fits = the part's print-orientation "
      f"box fits that printer (turned 90 deg on the bed if needed). Min wall = 1st-percentile ray thickness of 2500 surface samples "
      f"(< {MIN_WALL:.1f} mm = fewer than two {NOZZLE} mm perimeters); thin samples = how many of the 2500 are below that. "
      f"Overhang = face area steeper than {OVERHANG_DEG:.0f} deg from vertical and facing down, higher than {NEAR_BED:.0f} mm above the bed "
      f"(45 deg chamfers and wedges pass); bottom bevel = the same kind of face within {NEAR_BED:.0f} mm of the bed (edge chamfers that print fine). "
      f"Sliver faces = triangles under {SLIVER:g} mm2 left by the mesh merge; harmless while the mesh is watertight.")
    L("")
    L("| file | qty | slot | print orientation | size (mm) | H2S | H2C single | H2C dual | watertight | faces | volume (cm3) | sliver faces | min wall (mm) | thin samples | overhang (mm2) | bottom bevel (mm2) |")
    L("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        d = r["dims"]
        pl = r["plate"]
        L(f"| {r['file']} | {r['qty']} | {r['slot']} | {r['note']} | {d[0]:.1f} x {d[1]:.1f} x {d[2]:.1f} | "
          f"{'yes' if pl['H2S'] else 'NO'} | {'yes' if pl['H2C single nozzle'] else 'NO'} | {'yes' if pl['H2C dual nozzle (design limit)'] else 'NO'} | "
          f"{'yes' if r['watertight'] else 'NO'} | {r['faces']} | {r['volume']/1000:.1f} | {r['degenerate']} | "
          f"{r['min_wall']:.2f} | {r['thin_samples']} | {r['overhang_area']:.0f} | {r['near_bed_area']:.0f} |")
    L("")
    L("## Fit features measured on the exported STLs")
    L("")
    L(f"Target = the radius the CAD cuts (bore of the crush pocket, rib tip, insert pilot, screw clearance / counterbore). "
      f"Measured = radial distance of the STL vertices on that surface. PASS = every vertex within {FIT_TOL} mm of the target. "
      f"A 128-segment circle's chord sag is below 0.01 mm at these radii, so the polygon itself is inside the tolerance.")
    L("")
    L("| part | feature | kind | target r | mean r | min r | max r | max dev | vertices | result |")
    L("|---|---|---|---|---|---|---|---|---|---|")
    n_pass = n_fail = 0
    for r in results:
        for f in r["fits"]:
            if f["n"] == 0:
                n_fail += 1
                L(f"| {r['file']} | {f['label']} | {f['kind']} | {f['target']:.3f} | - | - | - | - | 0 | **FAIL (no surface found)** |")
                continue
            ok = f["dev"] <= FIT_TOL
            n_pass += ok
            n_fail += (not ok)
            L(f"| {r['file']} | {f['label']} | {f['kind']} | {f['target']:.3f} | {f['mean']:.4f} | {f['min']:.4f} | {f['max']:.4f} | "
              f"{f['dev']:.4f} | {f['n']} | {'PASS' if ok else '**FAIL**'} |")
    L("")
    L(f"Fit features: {n_pass} pass, {n_fail} fail (tolerance {FIT_TOL} mm).")
    L("")
    L("## Failures and warnings")
    L("")
    fails = []
    for r in results:
        if not r["watertight"]:
            fails.append(f"- **{r['file']}**: not watertight after export")
        if r["degenerate"] and not r["watertight"]:
            fails.append(f"- **{r['file']}**: {r['degenerate']} sliver faces on a non-watertight mesh")
        if not r["plate"]["H2C dual nozzle (design limit)"]:
            fails.append(f"- **{r['file']}**: exceeds the design limit ({r['dims'][0]:.0f} x {r['dims'][1]:.0f} x {r['dims'][2]:.0f} mm)")
        if r["thin_samples"] > 0:
            fails.append(f"- {r['file']}: {r['thin_samples']} of 2500 thickness samples below {MIN_WALL:.1f} mm (1st percentile {r['min_wall']:.2f} mm) - "
                         "check the thin spots in the slicer (text engraving, crush-rib tips and LED strip channels are expected to sample thin)")
        if r["overhang_area"] > 400:
            fails.append(f"- {r['file']}: {r['overhang_area']:.0f} mm2 of faces steeper than {OVERHANG_DEG:.0f} deg in print orientation - "
                         f"see renders/skin_print_check/{r['file']}_a.png (red = overhang) and the notes below")
        for f in r["bad_fits"]:
            fails.append(f"- **{r['file']}**: fit `{f['label']}` " + ("not found on the mesh" if f["n"] == 0 else f"deviates {f['dev']:.3f} mm"))
    for k, (ok, msg) in FINALIZE.items():
        if not ok:
            fails.append(f"- **library part {k}**: {msg}")
    lines += fails or ["- none"]
    L("")
    L("## Coupons")
    L("")
    L("The coupon STLs (`stl/T*.stl`, batch C1) are unchanged. Every crush pocket, insert pilot and bearing seat in the skin "
      "uses the same `fits.py` numbers the coupons test, so no coupon result is invalidated by the Blender rebuild. "
      "Bearing seats (608 / 686) and bushing bores are in the CAD core parts, which were not rebuilt.")
    L("")
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", REPORT, flush=True)


def _view_targets(placed):
    """Named camera targets from the placed parts (bbox centres)."""
    def centre(names):
        bbs = [U.bbox(o) for n, o, _ in placed if n in names]
        if not bbs:
            return None
        return ((min(b[0] for b in bbs) + max(b[1] for b in bbs)) / 2, (min(b[2] for b in bbs) + max(b[3] for b in bbs)) / 2,
                (min(b[4] for b in bbs) + max(b[5] for b in bbs)) / 2)
    return {"bank_A_top": centre(("valve_cover_A", "intake_lid", "throttle")), "intake": centre(("intake_lid", "throttle")),
            "valve_cover_A": centre(("valve_cover_A", "oil_cap_A"))}


def render_set(round_no, views, samples, size, phi=0.0, with_core=True):
    out_dir = os.path.join(ROOT, "renders", f"skin_round{round_no}")
    os.makedirs(out_dir, exist_ok=True)
    placed = place_all(phi, with_core=with_core)
    # Only the placed copies render. The library originals sit in the scene too (bank-local parts such as
    # the valve cover float over the intake; engine-frame parts coincide with their copies): without this
    # the first round-1 renders showed a black slab with a socket hole on top of the intake - the unrotated
    # library valve cover.
    shown = {o.name for _, o, _ in placed}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in shown and not o.name.startswith("STUDIO"):
            o.hide_render = True
    bbs = [U.bbox(o) for _, o, _ in placed if not _.startswith(("stand", "plinth", "edition", "bracket"))]
    bb = (min(b[0] for b in bbs), max(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs), min(b[4] for b in bbs), max(b[5] for b in bbs))
    floor_z = min(U.bbox(o)[4] for _, o, _ in placed)
    S.build(bb, floor_z)
    ref_dir = os.path.join(ROOT, "references")
    outputs = []
    targets = _view_targets(placed)
    for v in views:
        direction, zoom, ref, tgt = S.VIEWS[v]
        S.camera(direction, bb, zoom, target=targets.get(tgt))
        path = os.path.join(out_dir, v + ".png")
        t0 = time.time()
        S.render(path, size=size, samples=samples)
        print(f"  rendered {v} ({time.time()-t0:.0f}s)", flush=True)
        if ref and os.path.exists(os.path.join(ref_dir, ref)):
            S.composite(path, os.path.join(ref_dir, ref), os.path.join(out_dir, v + "_vs_ref.png"), v)
        outputs.append(path)
    return outputs


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--round", type=int, default=1, help="render round number (renders/skin_round<N>/)")
    ap.add_argument("--views", default=",".join(S.VIEWS.keys()))
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--size", default="1456x1086")
    ap.add_argument("--phi", type=float, default=0.0, help="crank angle for the damper")
    ap.add_argument("--no-core", action="store_true", help="render without the CAD core meshes from skin/core/")
    a = ap.parse_args(argv)
    if a.all:
        a.build = a.export = a.check = a.render = True
    t = time.time()
    U.reset_scene()
    if a.build or a.export or a.render:
        build_library()
    rows = None
    if a.export:
        rows = export_parts()
        export_assembly(a.phi)
    if a.check:
        if rows is None:
            with open(os.path.join(SKIN_DIR, "parts.json")) as f:
                d = json.load(f)
            rows = d["parts"]
            F.FITS.update(d["fits"])
        results = check_parts(rows)
        write_report(results)
    if a.render:
        w, h = (int(v) for v in a.size.lower().split("x"))
        render_set(a.round, a.views.split(","), a.samples, (w, h), a.phi, with_core=not a.no_core)
    print(f"done in {time.time()-t:.0f}s", flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
