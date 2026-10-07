"""Measure fit features on an exported STL (numpy + trimesh only, no Blender).
A feature is a cylinder axis (point p, unit direction d) with an along-axis
window [t0, t1] and a target radius r. The mesh vertices in the window whose
radial distance is within `window` of the target are the bore (or rib tip)
surface; we report their mean / min / max radius."""
import numpy as np


def measure(mesh, feats, M=None, window=0.05):
    """mesh: trimesh.Trimesh; feats: list of fitcut.FITS entries (library frame);
    M: 4x4 matrix taking the library frame to the mesh's frame (print orientation)."""
    V = np.asarray(mesh.vertices, dtype=np.float64)
    M = np.eye(4) if M is None else np.asarray(M, dtype=np.float64)
    R = M[:3, :3]
    out = []
    for f in feats:
        p = R @ np.asarray(f["p"]) + M[:3, 3]
        d = R @ np.asarray(f["d"])
        d = d / np.linalg.norm(d)
        rel = V - p
        t = rel @ d
        radial = np.linalg.norm(rel - np.outer(t, d), axis=1)
        sel = (t >= f["t0"]) & (t <= f["t1"]) & (np.abs(radial - f["r"]) <= window)
        if f.get("sectors"):
            e1 = R @ np.asarray(f["e1"])
            e1 = e1 - (e1 @ d) * d
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(d, e1)
            perp = rel - np.outer(t, d)
            ang = np.degrees(np.arctan2(perp @ e2, perp @ e1))
            in_sector = np.zeros(len(V), dtype=bool)
            for a, hw in f["sectors"]:
                da = (ang - a + 180.0) % 360.0 - 180.0
                in_sector |= np.abs(da) <= hw
            sel &= in_sector if f["kind"] == "tip" else ~in_sector
        n = int(sel.sum())
        rec = dict(label=f["label"], kind=f["kind"], target=f["r"], n=n)
        if n:
            rr = radial[sel]
            rec.update(mean=float(rr.mean()), min=float(rr.min()), max=float(rr.max()),
                       dev=float(np.abs(rr - f["r"]).max()))
        out.append(rec)
    return out
