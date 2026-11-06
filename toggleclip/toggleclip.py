"""
ODD LAYER  TC-03  TOGGLECLIP
============================

A fully printed bag clip with an over-centre toggle lock. Pressing the lever down pulls the
nose of the lower jaw ("blade") up through a bail link; the link passes 10 deg over centre and
the lever lands on its stop with a click. The blade is a floating pressure bar on an arched bow
spring, so the clamp force stays moderate and even for any bag from 0 to 2 mm thick.

Pipeline (plain Python 3.11 + manifold3d + shapely; Blender's bpy only for the scene):

    python toggleclip.py              # build, validate, export STL/3MF, meshes for Blender
    python toggleclip.py --quick      # skip the full motion sweep
    python tc/scene.py [--render]     # Blender project (.blend) and renders (needs bpy 4.2)
    python tools/make_docs.py         # charts, drawing, validation report

Status: designed and checked in CAD only. Nothing has been printed or physically tested.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import manifold3d as mf  # noqa: E402
from shapely.geometry import box  # noqa: E402

from tc import geo as G  # noqa: E402
from tc import mech as M  # noqa: E402
from tc import parts as PT  # noqa: E402
from tc import validate as VA  # noqa: E402
from tc import export as EX  # noqa: E402
from tc.params import P, D  # noqa: E402

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def log(*a):
    print("[TC-03]", *a, flush=True)


def build_solids(B):
    S = {}
    for k in ("upper", "blade", "lever", "bail_a", "bail_b", "pin_p", "pin_h", "blade_firm"):
        S[k] = G.solid(B[k], chamfer=0.6 if not k.startswith("pin") else 0.4)
    # wordmark debossed 0.5 mm into the upper jaw's top deck (behind the lever)
    if os.path.exists(FONT):
        txt = G.text_polys("ODD LAYER", 3.6, FONT, center=(21.0, 0.0))
        cs = G._cs(txt)
        if cs is not None:
            t3 = mf.Manifold.extrude(cs, 1.0).translate([0, 0, P.UJ_H - 0.5])
            S["upper"] = S["upper"] - t3
    return S


def mesh_check(S):
    out = {}
    for k, m in S.items():
        comps = len(m.decompose())
        v, t = G.mesh_arrays(m)
        out[k] = dict(volume_mm3=round(m.volume(), 1), components=comps, genus=m.genus(),
                      triangles=int(len(t)), status=str(m.status()))
    return out


def _cs_to_shapely(cs):
    from shapely.geometry import Polygon as Pg
    from shapely.ops import unary_union
    pos, neg = [], []
    for ring in cs.to_polygons():
        if len(ring) < 3:
            continue
        p = Pg(ring)
        if not p.is_valid:
            p = p.buffer(0)
        (pos if G.area_signed(ring) > 0 else neg).append(p)
    shape = unary_union(pos) if pos else Pg()
    if neg:
        shape = shape.difference(unary_union(neg))
    return shape


def overhangs(key, m, layer=0.2, allow=0.25, min_area=0.4):
    """Slice the part in print orientation every layer and find material that is not supported
    by the layer below grown by `allow` (0.2 mm per 0.2 mm layer = 45 deg, plus 0.05).
    Returns unsupported regions merged through height: these print as bridges or need help."""
    R = EX.ORIENT[key]
    mt = m.transform([[R[0, 0], R[0, 1], R[0, 2], 0], [R[1, 0], R[1, 1], R[1, 2], 0], [R[2, 0], R[2, 1], R[2, 2], 0]])
    bb = mt.bounding_box()
    mt = mt.translate([0, 0, -bb[2]])
    top = bb[5] - bb[2]
    prev = None
    regions = []
    z = layer / 2
    while z < top:
        cur = _cs_to_shapely(mt.slice(z))
        if prev is not None and not cur.is_empty:
            un = cur.difference(prev.buffer(allow, quad_segs=6))
            for g in G.as_polys(un):
                if g.area < min_area:
                    continue
                mrr = g.minimum_rotated_rectangle
                xs, ys = mrr.exterior.xy
                sides = sorted({round(((xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2) ** 0.5, 2) for i in range(4)})
                c = g.centroid
                regions.append(dict(z=round(z, 2), area_mm2=round(g.area, 2), span=sides[0],
                                    length=sides[-1], at=[round(c.x, 1), round(c.y, 1)]))
        prev = cur
        z += layer
    regions.sort(key=lambda r: -r["area_mm2"])
    return regions


def thin_features(bands, w=1.2, min_area=0.15):
    """Regions of the XZ profiles narrower than w (opening test); returns the largest."""
    found = []
    for y0, y1, p in bands:
        if y1 - y0 < 0.05:
            continue
        opened = p.buffer(-w / 2, quad_segs=8).buffer(w / 2, quad_segs=8)
        thin = p.difference(opened.buffer(0.02))
        for g in G.as_polys(thin):
            if g.area >= min_area:
                c = g.centroid
                found.append(dict(y=(round(y0, 2), round(y1, 2)), area=round(g.area, 2),
                                  at=(round(c.x, 1), round(c.y, 1))))
    found.sort(key=lambda f: -f["area"])
    return found[:12]


def mechanics():
    out = {"geometry": {k: (list(v) if isinstance(v, tuple) else v) for k, v in D.items()}}
    rows = []
    for name, E, bow in (("PLA, Standard blade", P.E_PLA, P.BOW_T), ("PETG, Standard blade", P.E_PETG, P.BOW_T),
                         ("PETG, Firm blade", P.E_PETG, P.BOW_T_FIRM), ("PLA, Firm blade", P.E_PLA, P.BOW_T_FIRM)):
        keep = P.BOW_T
        P.BOW_T = bow
        for sl in (0.4, 1.0, 1.4):
            for t in (0.0, 0.3, 0.6, 1.0, 1.5, 2.0):
                r = M.locked(t, E, sl)
                q = r["q"]
                n = len(q)
                rows.append(dict(case=name, slop=sl, bag=t, clamp_N=round(r["total"], 2), link_N=round(r["F_K"], 2),
                                 q_end=round(float(q[0]), 3), q_quarter=round(float(q[n // 4]), 3),
                                 q_mid=round(float(q[n // 2]), 3), bow_MPa=round(r["stress"]["bow"], 1),
                                 bar_MPa=round(r["stress"]["bar"], 1), upper_MPa=round(r["stress"]["upper"], 1),
                                 bar_drop=round(r["bar_drop"], 2)))
        P.BOW_T = keep
    out["clamp"] = rows
    strokes = {}
    for name, E, t in (("PLA_bag0.5", P.E_PLA, 0.5), ("PLA_bag2.0", P.E_PLA, 2.0), ("PETG_bag0.5", P.E_PETG, 0.5)):
        st = M.stroke(t, E, 1.0, degs=np.arange(0.0, 90.1, 1.0))
        strokes[name] = st.tolist()
    out["stroke"] = strokes
    out["opening"] = [(d, round(M.opening(math.radians(d), P.BAR_X[1]), 2), round(M.opening(math.radians(d), 30.0), 2))
                      for d in range(0, 191, 10)]
    out["dead_centre_deg"] = float(max(np.arange(0, 30, 0.05), key=lambda d: M.k_lift(math.radians(d))))
    return out


def detent_numbers():
    """Click force from the finger flexure (hand calc)."""
    out = {}
    for name, E in (("PLA", P.E_PLA), ("PETG", P.E_PETG)):
        Iy = 3.0 * P.FINGER_W ** 3 / 12          # finger 3 mm tall, FINGER_W wide, bending in y
        k = 3 * E * Iy / P.FINGER_L ** 3
        f = k * P.BUMP                           # each finger
        mu = 0.3
        fv = 2 * f * (1 + mu) / (1 - mu)         # vertical push through two 45 deg ramps
        r_peg = D["P"][0] - P.PEG_X
        thumb = fv * r_peg / M.r_thumb()
        sig = f * P.FINGER_L / (3.0 * P.FINGER_W ** 2 / 6)
        out[name] = dict(finger_k_N_per_mm=round(k, 2), finger_force_N=round(f, 2), push_N=round(fv, 2),
                         thumb_N=round(thumb, 2), finger_stress_MPa=round(sig, 1))
    return out


def strength():
    """Hand checks of the joints at an abuse load: 60 N in the link (about 4x the clamp at a
    2 mm bag) and 25 N on the lever tip sideways/upwards."""
    F = 60.0
    A = math.pi * 2.5 ** 2
    tau = F / (2 * A)
    rows = [("pins and pegs, double shear at 60 N link force", tau, 15.0)]
    # cheek (upper jaw nose) in bending: 30 N each at ~6 mm arm, section 2.65 x 8
    m = 30.0 * 6.0
    z = 2.65 * 8.0 ** 2 / 6
    rows.append(("nose cheek bending (each), 30 N", m / z, 20.0))
    # bail plate in tension, net section through a hole: (2*3.3 - 5.3) x 2.65 at 30 N per plate
    rows.append(("bail plate net section, 30 N", 30.0 / ((2 * 4.5 - 5.3) * 2.65), 20.0))
    # integral peg root bending (printed across layers): 30 N per joint shared by 2 supports
    rows.append(("integral peg bending across layers", 15.0 * 1.5 / (math.pi * 5 ** 3 / 32), 15.0))
    # lever arm bending with 25 N on the thumb pad (abuse) at 62 mm
    rows.append(("lever arm root, 25 N at the thumb pad", 25.0 * 55.0 / (18.0 * P.LEVER_T ** 2 / 6), 25.0))
    # bearing in the teardrop Q hole, web 6 mm long
    rows.append(("bearing, Q peg in the lever web, 60 N", F / (5.0 * 6.0), 10.0))
    return [dict(item=a, stress_MPa=round(s, 2), allow_MPa=al, SF=round(al / s, 1)) for a, s, al in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    t0 = time.time()
    out = a.out
    for d in ("models/stl", "models/3mf", "build"):
        os.makedirs(os.path.join(out, d), exist_ok=True)

    log("building bands")
    B = VA.all_bands()
    keep = P.BOW_T
    B["blade_firm"] = PT.blade_bands(bow_t=P.BOW_T_FIRM)
    log("building solids")
    S = build_solids(B)
    rep = {"status": "CAD only - not printed or physically tested"}
    rep["mesh"] = mesh_check(S)
    log("mesh:", {k: (v["components"], v["genus"]) for k, v in rep["mesh"].items()})

    # ------------------------------------------------------------------ motion sweep
    degs = list(np.arange(0, 191, 10 if a.quick else 2))
    log(f"clearance sweep over {len(degs)} lever angles")
    sw = VA.sweep(B, degs)
    rep["sweep"] = {"|".join(k): dict(min_gap=round(d, 3), at_deg=dg, where=info) for k, (d, dg, info) in sw.items()}
    rep["sweep_degs"] = [float(degs[0]), float(degs[-1]), len(degs)]
    # the FIRM blade in place of the standard one
    B2 = dict(B)
    B2["blade"] = B["blade_firm"]
    B2["blade_nobar"] = PT.blade_bands(bow_t=P.BOW_T_FIRM, nobar=True)
    sw2 = VA.sweep(B2, degs)
    rep["sweep_firm_blade"] = {"|".join(k): dict(min_gap=round(d, 3), at_deg=dg, where=info)
                               for k, (d, dg, info) in sw2.items() if "blade" in k}
    rep["lock_fit"] = {k: dict(min_gap=round(d, 3), where=i) for k, (d, i) in VA.lock_fit(B).items()}
    rep["detent_sweep"] = VA.detent_check(B)
    rep["detent"] = detent_numbers()

    # ------------------------------------------------------------------ 3D cross-check at lock
    st0 = M.pose(0.0)
    asm = {}
    for k in ("upper", "blade", "lever", "bail_a", "bail_b", "pin_p", "pin_h"):
        v, t = G.mesh_arrays(S[k])
        if k == "blade":
            v = EX.deform_blade(v)
        Mx = EX.pose_matrix(k, st0)
        v = v @ Mx[:3, :3].T + Mx[:3, 3]
        asm[k] = (v, t)
    inter, contacts = {}, {}
    names = list(asm)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            mx = mf.Manifold(mf.Mesh(asm[x][0].astype(np.float32), asm[x][1].astype(np.uint32)))
            my = mf.Manifold(mf.Mesh(asm[y][0].astype(np.float32), asm[y][1].astype(np.uint32)))
            vol, touch = 0.0, 0.0
            for comp in (mx ^ my).decompose():
                bb = comp.bounding_box()
                thick = min(bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
                if thick < 0.01:          # face-to-face contact (polygon chord error < 10 um)
                    touch = max(touch, thick)
                else:
                    vol += comp.volume()
            if vol > 1e-3:
                inter[f"{x}|{y}"] = round(vol, 3)
            if touch > 0:
                contacts[f"{x}|{y}"] = round(touch, 4)
    rep["lock_3d_overlaps_mm3"] = inter
    rep["lock_3d_contacts_mm"] = contacts
    log("3D overlaps at lock (mm3):", inter)

    # ------------------------------------------------------------------ printability
    rep["print"] = {}
    for key, stem, col, qty, note in EX.BOM + EX.OPTIONAL:
        v, t = G.mesh_arrays(S[key])
        w, size = EX.to_print(key, v)
        rep["print"][key] = dict(file=stem + ".stl", size_mm=[round(s, 1) for s in size],
                                 fits_220=bool(size[0] <= 220 and size[1] <= 220 and size[2] <= 220),
                                 orientation=note, overhangs=overhangs(key, S[key])[:10],
                                 thin_lt_1p2=thin_features(B[key]))
        EX.write_stl(os.path.join(out, "models/stl", stem + ".stl"), w, t, stem)
    # 3MF: the full set on one 220 x 220 plate, plus the firm blade on its own
    objs, sizes = [], []
    for key, stem, col, qty, note in EX.BOM:
        v, t = G.mesh_arrays(S[key])
        w, size = EX.to_print(key, v)
        objs.append((stem, w, t, EX.COLORS[col]))
        sizes.append((size[0], size[1]))
    pos, extent = EX.pack(sizes)
    EX.write_3mf(os.path.join(out, "models/3mf/TC03_ToggleClip_full_set.3mf"),
                 [(n, w, t, pos[i], c) for i, (n, w, t, c) in enumerate(objs)], "Odd Layer TC-03 ToggleClip")
    v, t = G.mesh_arrays(S["blade_firm"])
    w, _ = EX.to_print("blade_firm", v)
    EX.write_3mf(os.path.join(out, "models/3mf/TC03_Blade_Firm.3mf"), [("TC03_Blade_Firm", w, t, (110, 110), EX.COLORS["sand"])],
                 "Odd Layer TC-03 Firm blade (PETG)")
    rep["plate"] = dict(extent_mm=[round(e, 1) for e in extent], positions={objs[i][0]: [round(c, 1) for c in pos[i]] for i in pos})
    # assembly (locked, use frame, blade bar pressed flush)
    av = np.concatenate([asm[k][0] for k in asm])
    offs = np.cumsum([0] + [len(asm[k][0]) for k in asm])[:-1]
    at = np.concatenate([asm[k][1] + o for k, o in zip(asm, offs)])
    EX.write_stl(os.path.join(out, "models/stl", "TC03_Assembly_locked.stl"), av, at, "TC03 assembly")
    # meshes for the Blender scene (use frame, unposed) + poses
    np.savez_compressed(os.path.join(out, "build", "meshes.npz"),
                        **{f"{k}_v": G.mesh_arrays(S[k])[0] for k in S}, **{f"{k}_t": G.mesh_arrays(S[k])[1] for k in S})

    # ------------------------------------------------------------------ mechanics
    log("mechanics")
    rep["mechanics"] = mechanics()
    rep["strength"] = strength()
    rep["elapsed_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out, "models", "TC03_validation.json"), "w") as f:
        json.dump(rep, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    log(f"done in {rep['elapsed_s']} s")


if __name__ == "__main__":
    main()
