"""Stock-car V8: full engine assembly at any crank angle + collision checks.
Same API as assembly_v10.py so tools/verify_all.py and build_all.py work on
either engine (selected by config.py).

    python assembly_v8.py          # interference sweep over one revolution
"""

import sys
import time

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
        try:
            import exterior_v8
            _LIBS["style"] = exterior_v8.build_all()
        except ImportError:
            _LIBS["style"] = {}
        try:
            import pan_v8
            _LIBS["base"] = pan_v8.build_all()
        except ImportError:
            _LIBS["base"] = {}
        b = C.BEARING_608
        _LIBS["b608"] = cyl_x(b["od"] / 2, 0, b["w"]).cut(cyl_x(b["id"] / 2, -1, b["w"] + 1))
    return _LIBS


def main_bearings():
    b = libs()["b608"]
    front = move(b, C.BEARING_INNER_X)
    return [("bearing608_front", front, "steel"), ("bearing608_rear", rot_z(front, 180), "steel")]


def drive_and_base(with_base=True, with_covers=True):
    """Hidden drive (motor, belt, pulleys at the REAR inside the bellhousing),
    oil pan = motor + electronics bay, stand. Built by pan_v8 when it exists."""
    L = libs()
    if not L["base"]:
        return []
    import pan_v8
    return pan_v8.placed(L["base"], with_base=with_base, with_covers=with_covers)


def styling_parts(covers=True):
    """Heads, valve covers, plug boots, headers, intake."""
    if not libs()["style"]:
        return []
    import exterior_v8
    out = exterior_v8.placed(libs()["style"])
    if not covers:
        out = [p for p in out if not p[0].startswith("valve_cover")]
    return out


def full(phi=0.0, covers=True):
    return engine(phi) + styling_parts(covers) + drive_and_base()


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


MOVING = ("crankpin", "segment", "end_web", "main_shaft", "rod_", "piston_")
STATIC = ("crankcase", "valley_beam", "bank_", "end_plate", "rail_", "head_", "valve_cover", "boot_",
          "header", "collector", "intake", "throttle", "fuel_rail", "pan", "stand", "bracket", "front_cover",
          "damper", "pulley", "belt", "motor", "bellhousing", "alternator")
STATIC_ALL = STATIC + ("elec_", "spacer")


def _bb_overlap(a, b, tol=0.0):
    A, B = a.BoundingBox(), b.BoundingBox()
    return not (A.xmax < B.xmin - tol or B.xmax < A.xmin - tol or A.ymax < B.ymin - tol or
                B.ymax < A.ymin - tol or A.zmax < B.zmin - tol or B.zmax < A.zmin - tol)


def _same_joint(n1, n2):
    """Pairs that share a designed joint and are allowed to touch."""
    def cyl(n):
        return n.split("_")[-1]
    pair = sorted((n1, n2))
    if pair[0].startswith("piston_") and pair[1].startswith("rod_") and cyl(n1) == cyl(n2):
        return True
    # the two rods of one throw ride the same crankpin, 2 x PIN_SHOULDER_L apart
    return False


# press fits: the crush ribs are meant to overlap the part slightly
PRESS_FIT_PAIRS = {("head", "rail"): 1.0, ("rail", "valley"): 1.0, ("boot", "head"): 6.0,
                   ("head", "header"): 4.0, ("collector", "header"): 4.0,
                   ("bearing608", "end"): 5.0}


def static_check():
    parts = [(n, s) for n, s, _ in full(0.0) if n.startswith(STATIC_ALL)]
    bad = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            (n1, s1), (n2, s2) = parts[i], parts[j]
            if {n1.split("_")[0], n2.split("_")[0]} == {"belt", "pulley"}:
                continue
            if not _bb_overlap(s1, s2):
                continue
            v = s1.intersect(s2).Volume()
            key = tuple(sorted((n1.split("_")[0], n2.split("_")[0])))
            if v > PRESS_FIT_PAIRS.get(key, 0.01):
                bad.append((n1, n2, round(v, 2)))
    return bad


def drive_check():
    """Drive-train interference (motor, belt, pulleys, pan, bellhousing). Empty
    list = clear or not built yet (printed)."""
    L = libs()
    if not L["base"]:
        print("  drive: pan / motor / belt not built yet - nothing to check", flush=True)
        return []
    import pan_v8
    return pan_v8.drive_check()


def _kind(n):
    for k in ("crankpin", "segment", "end_web", "main_shaft", "rod", "piston",
              "crankcase", "bank", "end_plate", "rail", "head", "valve_cover", "header", "boot"):
        if n.startswith(k):
            return k
    return n


def sweep(step=15.0, verbose=True):
    hits = []
    t0 = time.time()
    angle = 0.0
    statics = [(n, s) for n, s, _ in styling_parts() + drive_and_base()]
    while angle < 360.0 - 1e-6:
        parts = [(n, s) for n, s, _ in engine(angle)] + statics
        mov = [(n, s) for n, s in parts if n.startswith(MOVING)]
        sta = [(n, s) for n, s in parts if n.startswith(STATIC)]
        pairs = [(a, b) for a in mov for b in sta]
        pairs += [(mov[i], mov[j]) for i in range(len(mov)) for j in range(i + 1, len(mov))]
        for (n1, s1), (n2, s2) in pairs:
            if n1.startswith("main_shaft") and n2.startswith(("pulley", "belt")):
                continue
            crank_parts = ("crankpin", "segment", "end_web", "main_shaft")
            if n1.startswith(crank_parts) and n2.startswith(crank_parts):
                continue
            if _same_joint(n1, n2) or not _bb_overlap(s1, s2):
                continue
            v = s1.intersect(s2).Volume()
            if v > 0.01:
                hits.append((angle, n1, n2, round(v, 3)))
        if verbose:
            print(f"  crank {angle:5.1f} deg: {len(hits)} collisions so far ({time.time()-t0:.0f}s)", flush=True)
        angle += step
    return hits


def clearances(step=30.0, near=4.0):
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
                continue
            if k1 == "main_shaft" and k2 == "end_plate":
                continue
            d = s1.distance(s2)
            key = tuple(sorted((k1, k2)))
            if key not in best or d < best[key][0]:
                best[key] = (d, angle, n1, n2)
        print(f"  clearance scan {angle:5.1f} deg", flush=True)
        angle += step
    return best


if __name__ == "__main__":
    step = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    h = sweep(step)
    print("COLLISIONS:" if h else "NO COLLISIONS over a full revolution")
    seen = set()
    for a, n1, n2, v in h:
        if (n1, n2) not in seen:
            print(f"  {a:6.1f} deg  {n1:>18} x {n2:<18} {v} mm3")
            seen.add((n1, n2))
