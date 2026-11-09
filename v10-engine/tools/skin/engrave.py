"""Part numbers cut 0.5 mm into a hidden face of each exported skin part, in the
part's PRINT orientation (same rule as cad/partnum.py: recessed, never raised,
never on the bed face). The spot is found by probing the exported mesh for a
flat, feature-free patch big enough for the text."""
import numpy as np

from . import bpyutil as U

DEPTH = 0.5
# print-frame face: (outward normal, text x direction)
FACES = {
    "+z": ((0, 0, 1), (1, 0, 0)),
    "+x": ((1, 0, 0), (0, 1, 0)), "-x": ((-1, 0, 0), (0, -1, 0)),
    "+y": ((0, 1, 0), (-1, 0, 0)), "-y": ((0, -1, 0), (1, 0, 0)),
}
# part file prefix: (label, faces to try in order, text sizes to try, max scan depth from the bbox face)
# -z is never used: it is the bed face. Parts without a hidden flat face are left unlabelled on purpose.
SPEC = {
    "01_": ("01", ("+x", "-x"), (5.0, 3.5), 1.0),        # crankcase: end face, under an end plate
    "03_": ("03", ("+z",), (5.0, 3.5, 2.5), 8.0),         # bank: mounting face (deck-down print)
    "30_": ("30A", ("+z",), (4.0, 3.0, 2.5), 40.0),       # head A: top, under the valve cover
    "30B": ("30B", ("+z",), (4.0, 3.0, 2.5), 40.0),
    "31_": ("31", ("+z",), (4.0, 3.0, 2.2), 30.0),        # valve cover: inside of the top (printed top-down)
    "31B": ("31B", ("+z",), (2.2, 1.8), 12.0),            # oil cap: inside the spigot end? (cap top is the bed) -> skirt rim
    "33_": ("33A", ("*top",), (2.2, 1.8), 3.0),           # primary: head-spigot end face (inside its socket) = the leaning top of the standing print
    "33B": ("33B", ("*top",), (2.2, 1.8), 3.0),
    "34_": ("34A", ("+y", "-y"), (2.2, 1.8), 1.0),        # flange plate: 4 mm long edge face (the end faces are all bevel)
    "34B": ("34B", ("+y", "-y"), (2.2, 1.8), 1.0),
    "35_": ("35A", ("+z",), (2.5, 2.0), 1.0),             # collector: nose end face (top of the standing print)
    "35B": ("35B", ("+z",), (2.5, 2.0), 1.0),
    "36_": ("36A", ("+z",), (4.0, 3.0, 2.2), 45.0),       # intake lid: inside the roof (printed upside down)
    "36B": ("36B", ("+z",), (4.0, 3.0, 2.2), 30.0),       # intake base: floor inside
    "40_": ("40", ("+z",), (5.0, 3.5), 70.0),             # pan: inside of the skin (printed skin-down)
    "41_": ("41", ("+z",), (5.0, 3.5), 12.0),             # floor panel: inside face, between the standoffs
    "42_": ("42", ("+z",), (4.0, 3.0, 2.2), 25.0),        # bellhousing: inside the rear face
    "43_": ("43", ("+z",), (4.0, 3.0, 2.2), 25.0),        # front cover: inside the front wall
    "46_": ("46", ("+y", "-y"), (5.0, 3.5), 1.0),         # stand plate: long edge face
    "47_": ("47", ("+y", "-y"), (3.0, 2.2), 1.0),         # bracket: tab side face (against the pan)
    "47B": ("47m", ("+y", "-y"), (3.0, 2.2), 1.0),
    "48_": ("48", ("+z",), (4.0, 3.0), 32.0),             # plinth: inside the roof (printed upside down)
}
UNLABELLED = ("32_", "36C", "44_", "45_", "45B", "49_", "T11")   # no hidden flat face / purchased / coupons


def _patch_offsets(w, h):
    return [(u * w, v * h) for u in (-0.5, -0.25, 0.0, 0.25, 0.5) for v in (-0.5, 0.0, 0.5)]


def find_spot(mesh, faces, sizes, scan, label):
    """Find a flat, feature-free patch for the label: returns (origin, normal, xdir, size) or None.
    Candidate planes are the mesh's own faces that look along the wanted normal (grouped by plane,
    nearest the bbox face first, within `scan` mm of it; "*top" = the leaning end face at the top of a
    standing print). Every candidate centre of a plane is probed in ONE containment query: solid 0.3 mm
    below all 15 samples, air 0.3 mm above them."""
    lo, hi = mesh.bounds
    normals = mesh.face_normals
    centers = mesh.triangles_center
    areas = mesh.area_faces
    V = mesh.vertices
    Fc = mesh.faces
    for face in faces:
        if face == "*top":
            i_top = int(np.argmax(centers[:, 2]))
            n_ = normals[i_top].copy()
            xd_ = np.cross(n_, [0.0, 0.0, 1.0])
            if np.linalg.norm(xd_) < 1e-3:
                xd_ = np.array([1.0, 0.0, 0.0])
            xd_ /= np.linalg.norm(xd_)
            sel_all = (normals @ n_ > 0.98) & (centers[:, 2] > hi[2] - 3.0)
            groups = [np.nonzero(sel_all)[0]]
        else:
            n, xd = FACES[face]
            n_, xd_ = np.asarray(n, float), np.asarray(xd, float)
            axis = int(np.argmax(np.abs(n_)))
            face_coord = hi[axis] if n_[axis] > 0 else lo[axis]
            aligned = normals @ n_ > 0.98
            if not aligned.any():
                continue
            depth = (face_coord - centers[aligned, axis]) * n_[axis]      # distance inward from the bbox face
            keep = depth <= scan + 0.5
            idx = np.nonzero(aligned)[0][keep]
            bins = np.round(depth[keep] / 0.2).astype(int)
            groups = [idx[bins == b] for b in sorted(set(bins.tolist()))]
        yd = np.cross(n_, xd_)
        for sel in groups:
            if len(sel) == 0:
                continue
            c = centers[sel]
            verts = V[Fc[sel]].reshape(-1, 3)
            for size in sizes:
                w, h = 0.75 * size * len(label) + 1.0, size * 1.3
                if areas[sel].sum() < 1.2 * w * h:
                    continue
                if face == "*top":
                    cand = c.copy()
                else:
                    # grid over the plane's vertex extent, on the plane's own coordinate
                    axis = int(np.argmax(np.abs(n_)))
                    plane = float(np.median(c[:, axis]))
                    a1, a2 = [i for i in range(3) if i != axis]
                    us = np.arange(verts[:, a1].min() + w / 2, verts[:, a1].max() - w / 2 + 1e-6, max(1.0, w / 3))
                    vs = np.arange(verts[:, a2].min() + h / 2, verts[:, a2].max() - h / 2 + 1e-6, max(1.0, h / 2))
                    if len(us) == 0 or len(vs) == 0:
                        continue
                    cand = np.array([[plane if k == axis else (u if k == a1 else v) for k in range(3)] for u in us for v in vs])
                # keep candidates on this plane's own triangles (not over a hole), the most interior first; at most 48
                if len(c) * len(cand) < 4e6:
                    d2 = ((cand[:, None, :] - c[None, :, :]) ** 2).sum(axis=2).min(axis=1)
                else:
                    d2 = np.zeros(len(cand))
                near = d2 <= max(w, h) ** 2
                if not near.any():
                    continue
                cand = cand[near][np.argsort(d2[near])][:48]
                offs = _patch_offsets(w, h)
                pts = np.empty((len(cand), len(offs), 2, 3))
                for i, o in enumerate(cand):
                    for j, (du, dv) in enumerate(offs):
                        q = o + xd_ * du + yd * dv
                        pts[i, j, 0] = q - n_ * (DEPTH * 0.6)
                        pts[i, j, 1] = q + n_ * 0.3
                inside = mesh.contains(pts.reshape(-1, 3)).reshape(len(cand), len(offs), 2)
                ok = inside[:, :, 0].all(axis=1) & ~inside[:, :, 1].any(axis=1)
                if ok.any():
                    return cand[np.argmax(ok)], n_, xd_, size
    return None


def engrave(obj, label, spot):
    """Cut `label` into obj at the spot found by find_spot (print frame)."""
    from mathutils import Matrix, Vector
    p, n, xd, size = spot
    tm = U.text_mesh("partnum", label, size, DEPTH * 2)
    # text lies in XY with +X right, +Z up its extrusion; map +X -> xd, +Z -> n
    zb = Vector(n).normalized()
    xb = Vector(xd).normalized()
    yb = zb.cross(xb)
    R = Matrix((xb, yb, zb)).transposed().to_4x4()
    U.transform(tm, Matrix.Translation(Vector(p)) @ R)
    U.boolean(obj, tm)
    return obj


def label_for(name):
    if name.startswith(UNLABELLED):
        return None
    for prefix, spec in sorted(SPEC.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(prefix):
            return spec
    return None


def label_part(obj, name, mesh):
    """Engrave the part number if the spec has a spot. mesh = trimesh of obj in the same frame.
    Returns a note for the report."""
    spec = label_for(name)
    if spec is None:
        return "not labelled (no hidden flat face)" if name.startswith(UNLABELLED) else "no spec"
    label, faces, sizes, scan = spec
    spot = find_spot(mesh, faces, sizes, scan, label)
    if spot is None:
        return f"{label}: NO SPOT FOUND"
    engrave(obj, label, spot)
    p, n, _, size = spot
    names = [k for k, (nn, _) in FACES.items() if np.allclose(nn, n)]
    face = names[0] if names else "top end face"
    return f"{label} on {face} at ({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f}), {size:.1f} mm"
