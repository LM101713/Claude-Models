"""Fail if a clearance / tolerance number is written inside a part file.

Every fit must live in fits.py. This scans cad/*.py for fractional offsets
(`+ 0.3`, `- 0.25`, `/ 2 + 0.5` ...) and compares each offending line with
tools/fit_literals_allow.txt: the reviewed list of lines that are pure
geometry (chamfer sizes, cosmetic positions, boolean overshoots), not fits.

    python tools/check_fits.py            # check (exit 1 on a new literal)
    python tools/check_fits.py --accept   # after review: add new lines to the allow list
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(ROOT, "cad")
ALLOW = os.path.join(ROOT, "tools", "fit_literals_allow.txt")

PATTERN = re.compile(r"[+-]\s*\d*\.\d+\b")
# tiny boolean overshoots and obvious non-fits are never clearances
IGNORE = re.compile(r"\b0\.0+1\b|\b0\.1\b|chamfer\(|fillet\(|\.text\(|rotate\(|print_|^\s*#|\"\"\"|dpi")


def offending():
    out = []
    for fn in sorted(os.listdir(CAD)):
        if not fn.endswith(".py") or fn == "coupons.py":      # the coupons ARE the fit ladders
            continue
        for i, line in enumerate(open(os.path.join(CAD, fn)), 1):
            code = line.split("#")[0]
            if not PATTERN.search(code) or IGNORE.search(line):
                continue
            # a literal next to a fits.py name is fine (e.g. "+ C.MAGNET_DEPTH_CLEAR")
            out.append((fn, i, code.strip()))
    return out


def main():
    allow = set()
    if os.path.exists(ALLOW):
        allow = {l.rstrip("\n") for l in open(ALLOW) if l.strip()}
    hits = offending()
    keys = [f"{fn}: {code}" for fn, _, code in hits]
    new = [(h, k) for h, k in zip(hits, keys) if k not in allow]
    if "--accept" in sys.argv:
        with open(ALLOW, "w") as f:
            f.write("\n".join(sorted(set(keys))) + "\n")
        print(f"allow list rewritten: {len(set(keys))} reviewed geometry lines")
        return 0
    if new:
        print("NEW numeric offsets in part code - move them to fits.py, or review and run --accept:")
        for (fn, i, code), _ in new:
            print(f"  {fn}:{i}: {code}")
        return 1
    print(f"check_fits: OK ({len(hits)} reviewed geometry literals, 0 new)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
