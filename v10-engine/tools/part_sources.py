"""Where each V8 part file comes from - the ONE place the plate, print-check
and BOM tools look up a part's STL.

Two sources feed the kit:
  * the Blender skin (`skin/<name>.stl`, written by tools/skin_blender.py --export):
    every visible part, 01 / 03 included (decision D55)
  * the CAD core (`stl/<name>.stl`, written by build_all.py): crank, rods,
    pistons, rails, end plates, valley beam, coupons, proto shafts, machined

`resolve(name)` returns the path to use; the skin wins when both exist. Set
SKIN_FIRST = False to build the kit from the frozen CAD skin instead
(docs/DECISIONS.md D54: the CAD skin is frozen at cad-skin-v1).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIN_DIR = os.path.join(ROOT, "skin")
STL_DIR = os.path.join(ROOT, "stl")
SKIN_FIRST = True

# part-number prefixes the Blender skin owns (anything else is CAD)
SKIN_PREFIXES = ("01_", "03_", "30", "31", "32_", "33", "34", "35", "36", "40_", "41_", "42_", "43_", "44_", "45", "46_", "47", "48_", "49_", "T11")


def is_skin_part(name):
    return name.startswith(SKIN_PREFIXES)


def resolve(name):
    """Absolute STL path for a V8 part file name (without .stl), or None if neither source has it."""
    skin = os.path.join(SKIN_DIR, name + ".stl")
    cad = os.path.join(STL_DIR, name + ".stl")
    if SKIN_FIRST and is_skin_part(name) and os.path.exists(skin):
        return skin
    if os.path.exists(cad):
        return cad
    if os.path.exists(skin):
        return skin
    return None


def source_of(name):
    p = resolve(name)
    if p is None:
        return "missing"
    return "blender" if p.startswith(SKIN_DIR) else "cad"


def skin_parts():
    """(file name, qty, slot, note) for every exported skin part, from skin/parts.json."""
    path = os.path.join(SKIN_DIR, "parts.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [(r["file"], r["qty"], r["slot"], r["note"]) for r in json.load(f)["parts"]]


def kit_parts():
    """Every printed part of one V8 engine with its source: (name, qty, source).
    Skin parts from skin/parts.json (49 is a purchased plate, not printed); core parts from build_all.parts()."""
    out = []
    for name, qty, slot, _ in skin_parts():
        if slot in ("purchased", "coupon"):
            continue
        out.append((name, qty, source_of(name)))
    try:
        import sys
        sys.path.insert(0, ROOT)
        sys.path.insert(0, os.path.join(ROOT, "cad"))
        import build_all
        for name, _, qty, _ in build_all.parts():
            if is_skin_part(name) or name.startswith(("M0", "P1", "P2", "T")):
                continue
            out.append((name, qty, source_of(name)))
    except Exception as e:                       # noqa: BLE001  (CAD env not available: skin only)
        print("  part_sources: CAD part table not available:", e)
    return out
