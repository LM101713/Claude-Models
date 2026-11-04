#!/usr/bin/env python3
"""Build the render scenes for DRYDOCK P001 (GLB + JSON per scene) from the real CAD.

    python render/scenes.py            # writes render/out/<scene>.glb and <scene>.json
    cd render && node render.mjs       # renders every scene to ../renders/*.png

Nothing here is modelled separately: every mesh is tessellated from the same build123d parts
that are exported for printing. The spool is a generic stand-in built from the brief's
preliminary numbers (200 mm flanges, 67 mm wide, 55 mm bore), not a model of any real spool.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import drydock as dd  # noqa: E402
from build123d import Box, Cylinder, Pos, Rot  # noqa: E402

OUT = HERE / "out"
COL = {"charcoal": "#2b2d31", "orange": "#ff6a13", "clear": "#d8eef5", "spool": "#c9ccd2",
       "filament": "#3b6fd1", "bead": "#ff8c1a"}


def mesh_of(shape, tol=0.02):
    v, t = shape.tessellate(tol, 0.15)
    return trimesh.Trimesh(np.array([(p.X, p.Y, p.Z) for p in v]), np.array(t), process=True)


def write_scene(name, items, beads=None, extra=None):
    """items: list of (shape_or_trimesh, color_key, label, label_anchor_xyz or None)."""
    OUT.mkdir(exist_ok=True)
    sc = trimesh.Scene()
    meta = {"parts": [], "beads": beads or [], **(extra or {})}
    for i, (shape, col, label, anchor) in enumerate(items):
        m = shape if isinstance(shape, trimesh.Trimesh) else mesh_of(shape)
        sc.add_geometry(m, node_name=f"p{i}", geom_name=f"p{i}")
        meta["parts"].append({"name": f"p{i}", "color": COL[col], "kind": col, "label": label,
                              "anchor": anchor})
    sc.export(OUT / f"{name}.glb")
    (OUT / f"{name}.json").write_text(json.dumps(meta))
    print("scene", name, len(items), "meshes", len(meta["beads"]), "beads")


def bead_fill(P, D, rb=1.75, keep=lambda x, y, z: True, z_shift=0.0):
    """Hex-packed bead centres filling the cartridge up to the fill line (bottom cap installed)."""
    Ls = D["L_body"]
    zfi = -D["cap_out"] + P.face_thickness
    fill = Ls - D["collar_total"]

    def rmax(z):
        if z < zfi:
            return -1
        if z < -D["neck_len"]:
            return D["R_hi"] - (z - zfi)
        if z < D["plug_len"]:
            return D["R_pi"]
        if z < D["collar"]:
            return D["R_s"]
        if z < D["collar_total"]:
            return D["R_s"] + (z - D["collar"])
        return D["R_i"]
    pts = []
    dz = rb * math.sqrt(8 / 3)
    k = 0
    z = zfi + rb
    while z < fill - rb:
        r_lim = min(rmax(z - rb * 0.9), rmax(z), rmax(z + rb * 0.9)) - rb - 0.05
        off = (rb if k % 3 == 1 else 0, rb / math.sqrt(3) * (k % 3))
        for i in range(-14, 15):
            for j in range(-14, 15):
                x = 2 * rb * i + rb * (j % 2) + off[0]
                y = rb * math.sqrt(3) * j + off[1]
                if math.hypot(x, y) <= r_lim and keep(x, y, z):
                    pts.append([round(x, 3), round(y, 3), round(z + z_shift, 3)])
        z += dz
        k += 1
    return pts


def main():
    P = dd.Params()
    D = P.d()
    parts = dd.build_parts(P, sizes=P.adapter_sizes)
    L = D["L_body"]

    # 1) hero: assembled and locked, 55 mm adapters
    asm = dd.assembly(P, parts, explode=0.0)
    write_scene("hero", [(s, c, None, None) for s, c, _ in asm])

    # 2) exploded with labels
    e = 16.0
    ex = dd.assembly(P, parts, explode=e, angle=0.0)
    names = {"cap": "QuickLock end cap", "window": "Indicator window", "adapter": "Spool adapter (55 mm)",
             "body": "Vented body"}
    seen = {}
    items = []
    for s, c, lab in ex:
        bb = s.bounding_box()
        k = seen.get(lab, 0)
        seen[lab] = k + 1
        text = names[lab] if k == 0 or lab == "cap" else None
        if lab == "cap" and k == 1:
            text = "QuickLock end cap (same part)"
        if lab == "window" and k == 1:
            text = None
        items.append((s, c, text, None))
    write_scene("exploded", items)
    side = {"Indicator window": ("down", 120), "QuickLock end cap": ("up", 130),
            "Spool adapter (55 mm)": ("down", 170), "Vented body": ("up", 120),
            "QuickLock end cap (same part)": ("up", 130)}
    meta = json.loads((OUT / "exploded.json").read_text())
    for prt in meta["parts"]:
        if prt["label"] in side:
            prt["side"], prt["lift"] = side[prt["label"]]
    (OUT / "exploded.json").write_text(json.dumps(meta))

    # 3) section through the axis (keep y <= 0), with beads
    half = Pos(0, -60, 20) * Box(200, 120, 200)
    sec = []
    for s, c, lab in asm:
        cut = s & half
        if cut is not None and cut.solids():
            sec.append((cut, c, None, None))
    beads = bead_fill(P, D, keep=lambda x, y, z: y <= -1.75)
    write_scene("section", sec, beads=beads,
                extra={"callouts": [
                    {"text": "QuickLock lug in its groove", "at": [0, 0, D["z_c"]], "r": D["R_o"], "dx": 120, "dy": 40},
                    {"text": "Window, held by the face lip", "at": [0, 0, -D["cap_out"] + 1.6], "r": 7.5, "dx": 300, "dy": 70},
                    {"text": "Fill line (internal step)", "at": [0, 0, L - D["collar_total"]], "r": D["R_i"], "dx": 140, "dy": -20},
                    {"text": "Spool adapter", "at": [0, 0, L + 2.0], "r": 24.0, "dx": 120, "dy": -60}]})

    # 4) in a generic spool (half section of the spool, whole cartridge)
    W, Rf, Rb, Rcore = P.spool_width, 100.0, P.spool_bore / 2, 40.0
    zc = L / 2
    z0 = zc - W / 2
    flange_t, wall = 2.4, 2.4
    spool = (Pos(0, 0, z0 + flange_t / 2) * Cylinder(Rf, flange_t)
             + Pos(0, 0, z0 + W - flange_t / 2) * Cylinder(Rf, flange_t)
             + Pos(0, 0, zc) * Cylinder(Rb + wall, W)
             - Pos(0, 0, zc) * Cylinder(Rb, W + 2))
    # hub ribs between bore tube and filament core, just to read as a spool
    core = Pos(0, 0, zc) * Cylinder(Rcore, W - 2 * flange_t) - Pos(0, 0, zc) * Cylinder(Rcore - 2, W)
    ribs = None
    for k in range(6):
        rib = Rot(0, 0, 60 * k + 30) * (Pos((Rb + Rcore) / 2, 0, zc) * Box(Rcore - Rb, 2.0, W - 2 * flange_t))
        ribs = rib if ribs is None else ribs + rib
    spool = spool + core + ribs
    fil = Pos(0, 0, zc) * Cylinder(85, W - 2 * flange_t - 0.6) - Pos(0, 0, zc) * Cylinder(Rcore, W)
    cutq = Pos(0, -150, zc) * Box(400, 300, 200)   # keep y <= 0
    items = [((spool & cutq), "spool", None, None),
             ((fil & cutq), "filament", None, None)]
    for s, c, lab in asm:
        items.append((s, c, None, None))
    write_scene("spool", items)

    # 5) expansion: body + coupler + body, exploded a little
    exm = dd.assembly(P, parts, explode=0.0, extra_module=True)
    write_scene("expansion", [(s, c, None, None) for s, c, _ in exm])
    exm2 = dd.assembly(P, parts, explode=14.0, angle=0.0, extra_module=True)
    lbl = {"coupler": "Expansion coupler", "body2": "Second body (same part)"}
    write_scene("expansion_exploded", [(s, c, lbl.get(l), None) for s, c, l in exm2])

    # 6) adapter set, flat, plus the fit gauge
    items = []
    sizes = list(parts["adapters"].items())
    for i, (b, ad) in enumerate(sizes):
        x = (i % 3 - 1) * 66
        y = (0.5 - i // 3) * 66
        items.append((Pos(x, y, 0) * ad, "orange", f"{b:g} mm", [x, y - 33, 0]))
    write_scene("adapters", items)

    # 7) cap face close-up (window installed)
    lip_t = P.face_thickness - P.window_seat_depth
    cap_face = [(Rot(180, 0, 0) * parts["cap"], "charcoal", None, None),
                (Rot(180, 0, 0) * (Pos(0, 0, -D["cap_out"] + lip_t) * parts["window"]), "clear", None, None)]
    write_scene("capface", cap_face)

    # beads for the hero shot are not shown (closed cartridge)
    (OUT / "dims.json").write_text(json.dumps({k: v for k, v in D.items() if not callable(v)}))


if __name__ == "__main__":
    main()
