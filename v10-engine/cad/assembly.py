"""Full engine assembly at any crank angle + collision sweep.

    python assembly.py            # interference sweep over one revolution
"""

import sys
import time

import cadquery as cq

import block
import crank
import rods_pistons as rp
from common import C, cyl_x, move, rot_z

_LIBS = {}


def libs():
    if not _LIBS:
        _LIBS["crank"] = crank.build_all()
        _LIBS["rp"] = rp.build_all()
        _LIBS["block"] = block.build_all()
        b = C.BEARING_608
        _LIBS["b608"] = cyl_x(b["od"] / 2, 0, b["w"]).cut(cyl_x(b["id"] / 2, -1, b["w"] + 1))
    return _LIBS


def main_bearings():
    b = libs()["b608"]
    front = move(b, C.BEARING_INNER_X)
    return [("bearing608_front", front, "steel"), ("bearing608_rear", rot_z(front, 180), "steel")]


def engine(phi=0.0, with_blocks=True, with_rails=True):
    L = libs()
    cols = {"crankpin": "steel", "segment": "crank", "end_web": "crank", "main_shaft": "steel"}
    out = []
    for name, s in crank.placed_parts(L["crank"], phi):
        out.append((name, s, [c for k, c in cols.items() if name.startswith(k)][0]))
    out += rp.moving_parts(L["rp"], phi)
    if with_rails:
        out += rp.static_rails(L["rp"])
    out += main_bearings()
    static = block.placed_static(L["block"])
    if not with_blocks:
        static = [s for s in static if not s[0].startswith("bank")]
    return out + static


# groups for the collision sweep (small purchased parts are checked implicitly
# through the holes that hold them)
MOVING = ("crankpin", "segment", "end_web", "main_shaft", "rod_", "piston_")
STATIC = ("crankcase", "bank_", "end_plate", "rail_")


def _bb_overlap(a, b, tol=0.0):
    A, B = a.BoundingBox(), b.BoundingBox()
    return not (A.xmax < B.xmin - tol or B.xmax < A.xmin - tol or A.ymax < B.ymin - tol or
                B.ymax < A.ymin - tol or A.zmax < B.zmin - tol or B.zmax < A.zmin - tol)


def _same_joint(n1, n2):
    """Pairs that share a designed joint and are allowed to touch."""
    def cyl(n):
        return n.split("_")[-1]
    pair = sorted((n1, n2))
    # rod small end sits between its own piston's bosses
    if pair[0].startswith("piston_") and pair[1].startswith("rod_") and cyl(n1) == cyl(n2):
        return True
    return False


def sweep(step=15.0, verbose=True):
    hits = []
    t0 = time.time()
    angle = 0.0
    while angle < 360.0 - 1e-6:
        parts = [(n, s) for n, s, _ in engine(angle)]
        mov = [(n, s) for n, s in parts if n.startswith(MOVING)]
        sta = [(n, s) for n, s in parts if n.startswith(STATIC)]
        pairs = [(a, b) for a in mov for b in sta]
        pairs += [(mov[i], mov[j]) for i in range(len(mov)) for j in range(i + 1, len(mov))]
        for (n1, s1), (n2, s2) in pairs:
            if n1.startswith(("crankpin", "segment", "end_web", "main_shaft")) and \
               n2.startswith(("crankpin", "segment", "end_web", "main_shaft")):
                continue                      # crank is one rigid body
            if _same_joint(n1, n2) or not _bb_overlap(s1, s2):
                continue
            v = s1.intersect(s2).Volume()
            if v > 0.01:
                hits.append((angle, n1, n2, round(v, 3)))
        if verbose:
            print(f"  crank {angle:5.1f} deg: {len(hits)} collisions so far ({time.time()-t0:.0f}s)", flush=True)
        angle += step
    return hits


if __name__ == "__main__":
    step = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    h = sweep(step)
    print("COLLISIONS:" if h else "NO COLLISIONS over a full revolution")
    seen = set()
    for a, n1, n2, v in h:
        key = (n1, n2)
        if key not in seen:
            print(f"  {a:6.1f} deg  {n1:>18} x {n2:<18} {v} mm3")
            seen.add(key)


def _kind(n):
    for k in ("crankpin", "segment", "end_web", "main_shaft", "rod", "piston",
              "crankcase", "bank", "end_plate", "rail"):
        if n.startswith(k):
            return k
    return n


def clearances(step=30.0, near=4.0):
    """Minimum gap between every moving/static pair that comes within `near` mm.
    Returns {(kind1, kind2): (gap, angle, name1, name2)}."""
    best = {}
    angle = 0.0
    while angle < 360.0 - 1e-6:
        parts = [(n, s) for n, s, _ in engine(angle)]
        mov = [(n, s) for n, s in parts if n.startswith(MOVING)]
        sta = [(n, s) for n, s in parts if n.startswith(STATIC)]
        pairs = [(a, b) for a in mov for b in sta]
        pairs += [(mov[i], mov[j]) for i in range(len(mov)) for j in range(i + 1, len(mov))]
        for (n1, s1), (n2, s2) in pairs:
            k1, k2 = _kind(n1), _kind(n2)
            crank_parts = ("crankpin", "segment", "end_web", "main_shaft")
            if k1 in crank_parts and k2 in crank_parts:
                continue
            if _same_joint(n1, n2) or not _bb_overlap(s1, s2, near):
                continue
            if k1 == "rod" and k2 == "crankpin":
                continue          # joined through the 686 bearing
            if k1 == "main_shaft" and k2 == "end_plate":
                continue          # joined through the 608 bearing
            d = s1.distance(s2)
            key = tuple(sorted((k1, k2)))
            if key not in best or d < best[key][0]:
                best[key] = (d, angle, n1, n2)
        print(f"  clearance scan {angle:5.1f} deg", flush=True)
        angle += step
    return best
