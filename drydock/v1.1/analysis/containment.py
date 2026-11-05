#!/usr/bin/env python3
"""Bead-escape test: the smallest sphere that can get from inside the cartridge to the outside.

The assembled cartridge (both caps locked AND lifted outward by the full bearing-flank play,
windows in place, adapters left out because they sit outside the containment) is voxelised by
rasterising horizontal sections. A bead of radius r can occupy any free voxel whose distance
to the nearest solid voxel exceeds r. If the free region reachable from the chamber centre at
that r touches the outside of the box, a bead of diameter 2r can escape.

    python containment.py p001            # the Prototype 001 geometry
    python containment.py v11             # the V1.1 geometry
Resolution = voxel pitch (default 0.1 mm): results are good to about +/-0.1 mm in diameter.
"""
import importlib.util, json, math, sys
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
SRC = {"p001": HERE.parents[1] / "drydock.py", "v11": HERE.parent / "drydock_v11.py"}


def load(which):
    spec = importlib.util.spec_from_file_location("dd_" + which, SRC[which])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def mesh(shape, tol=0.01):
    v, t = shape.tessellate(tol, 0.1)
    return trimesh.Trimesh(np.array([(p.X, p.Y, p.Z) for p in v]), np.array(t))


def run(which, pitch=0.1, half=24.5, sealed=False):
    dd = load(which)
    P = dd.Params()
    if sealed:   # close the vents (sub-voxel slots) to measure the joint gaps on their own
        P.vent_width = 0.01
        P.face_slot_width = 0.01
    D = P.d()
    parts = dd.build_parts(P, log=lambda *a: None, sizes=[P.spool_bore])
    L = D["L_body"]
    lift = P.bearing_play
    from build123d import Pos
    asm = [(s, c, l) for s, c, l in dd.assembly(P, parts, explode=0.0) if l != "adapter"]
    shapes = []
    for s, c, l in asm:
        bb = s.bounding_box()
        if l in ("cap", "window"):            # lift each cap (and its window) outward by the play
            s = Pos(0, 0, -lift if bb.max.Z < L / 2 else lift) * s
        shapes.append(s)
    meshes = [mesh(s) for s in shapes]
    zmin = -D["cap_out"] - lift - 1.0
    zmax = L + D["cap_out"] + lift + 1.0
    zs = np.arange(zmin, zmax, pitch) + pitch / 2
    n = int(round(2 * half / pitch))
    solid = np.zeros((len(zs), n, n), dtype=bool)
    def to_px(xy):
        return [((x + half) / pitch, (y + half) / pitch) for x, y in xy]
    for m in meshes:
        secs = m.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=zs)
        for k, sec in enumerate(secs):
            if sec is None:
                continue
            # section_multiplane returns planar paths; map back to world x,y via its transform
            T = sec.metadata.get("to_3D", np.eye(4)) if hasattr(sec, "metadata") else np.eye(4)
            img = Image.new("1", (n, n), 0)
            dr = ImageDraw.Draw(img)
            for poly in sec.polygons_full:
                ext = np.array(poly.exterior.coords)
                ext3 = (T @ np.c_[ext, np.zeros(len(ext)), np.ones(len(ext))].T).T[:, :2]
                dr.polygon(to_px(ext3), fill=1)
                for hole in poly.interiors:
                    h = np.array(hole.coords)
                    h3 = (T @ np.c_[h, np.zeros(len(h)), np.ones(len(h))].T).T[:, :2]
                    dr.polygon(to_px(h3), fill=0)
            solid[k] |= np.array(img, dtype=bool).T.T
    free = ~solid
    edt = ndimage.distance_transform_edt(free) * pitch     # mm to nearest solid voxel centre
    # bead centre starts inside the chamber on the axis at mid-body
    seed = (int(np.argmin(np.abs(zs - L / 2))), n // 2, n // 2)
    def escapes(r):
        allowed = edt > r
        if not allowed[seed]:
            return None
        lab, _ = ndimage.label(allowed)
        comp = lab == lab[seed]
        return bool(comp[0].any() or comp[-1].any() or comp[:, 0].any() or comp[:, -1].any()
                    or comp[:, :, 0].any() or comp[:, :, -1].any())
    lo, hi = 0.1, 3.0           # radii (mm): lo escapes, hi does not
    assert not escapes(hi)
    if not escapes(lo):
        return {"geometry": which, "vents": "closed (joint gaps only)" if sealed else "open",
                "pitch_mm": pitch, "cap_lift_mm": lift,
                "largest_escaping_bead_mm": f"< {2 * lo:.1f} (nothing of 0.2 mm or more gets out)",
                "smallest_trapped_bead_mm": 2 * lo}
    while hi - lo > pitch / 4:
        mid = (lo + hi) / 2
        if escapes(mid):
            lo = mid
        else:
            hi = mid
    # where does the largest escaping sphere get out? (first exit voxel nearest the chamber)
    allowed = edt > lo
    lab, _ = ndimage.label(allowed)
    comp = lab == lab[seed]
    # narrowest point along the escape path ~ voxels in comp with edt close to lo
    path = np.argwhere(comp & (edt < lo + 2 * pitch))
    pts = np.c_[path[:, 1] * pitch - half + pitch / 2, path[:, 2] * pitch - half + pitch / 2, zs[path[:, 0]]]
    r = np.hypot(pts[:, 0], pts[:, 1])
    where = {"r_median": float(np.median(r)) if len(r) else None,
             "z_range": [float(pts[:, 2].min()), float(pts[:, 2].max())] if len(r) else None}
    return {"geometry": which, "vents": "closed (joint gaps only)" if sealed else "open", "pitch_mm": pitch, "cap_lift_mm": lift,
            "largest_escaping_bead_mm": round(2 * lo, 2), "smallest_trapped_bead_mm": round(2 * hi, 2),
            "solid_voxels": int(solid.sum())}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "p001"
    pitch = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    sealed = "sealed" in sys.argv
    res = run(which, pitch, sealed=sealed)
    print(json.dumps(res, indent=1))
    (HERE / f"containment_{which}{'_sealed' if sealed else ''}.json").write_text(json.dumps(res, indent=1))
