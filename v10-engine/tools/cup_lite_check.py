"""Cup Lite interference check: every exported STL in its assembled position against every other
(bank-B valve cover = mirrored t01 moved back by 2 x bank offset). Prints pairs that overlap by more
than 0.5 mm3 and whether each STL is one closed body.

    python tools/cup_lite_check.py        (bpyenv: trimesh, manifold3d)
"""
import glob
import itertools
import os

import manifold3d as M
import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_OFF = 4.75


def man(m):
    return M.Manifold(M.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                             tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def main():
    ms, bad = {}, 0
    for p in sorted(glob.glob(os.path.join(ROOT, "cup_lite", "stl", "*.stl"))):
        n = os.path.basename(p)[:-4]
        m = trimesh.load(p)
        if m.body_count != 1 or not m.is_watertight:
            print(f"NOT ONE CLOSED BODY: {n} ({m.body_count} bodies)")
            bad += 1
        if n == "k07_plug_boot":
            continue
        ms[n] = man(m)
        if n == "t01_valve_cover":
            m.apply_transform(trimesh.transformations.reflection_matrix((0, 0, 0), (0, 1, 0)))
            m.apply_translation((-2 * BANK_OFF, 0, 0))
            ms[n + "_B"] = man(m)
    for a, b in itertools.combinations(ms, 2):
        v = (ms[a] ^ ms[b]).volume()
        if v > 0.5:
            print(f"OVERLAP {a:22s} {b:22s} {v:8.1f} mm3")
            bad += 1
    print("clean" if not bad else f"{bad} problems")


if __name__ == "__main__":
    main()
