"""
Checks for TC-03, run on every build.

Because every part is a stack of flat bands along y and the motion is planar, two parts can
only touch where their y-bands overlap, and there the question is purely 2D. So the clearance
sweep is exact: for every pair of parts, every pair of overlapping bands and every sampled lever
angle, it measures the distance (or overlap area) between the posed XZ profiles.
"""

import math

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from . import geo as G
from . import mech as M
from . import parts as PT
from .params import P, D

# pairs that are meant to touch: (a, b) -> reason
PRESS = {("blade", "pin_h"): "hinge pin pressed into the blade (crush ribs)",
         ("lever", "pin_p"): "lever pin pressed into the lever (crush ribs)",
         ("bail_a", "bail_b"): "bail pegs pressed into bail B (crush ribs)"}
RUNNING = {("pin_h", "upper"): "hinge pin in the ears",
           ("pin_p", "upper"): "lever pin in the nose cheeks",
           ("bail_a", "lever"): "Q peg in the lever",
           ("bail_a", "blade"): "K peg in the blade"}


def _key(a, b):
    return tuple(sorted((a, b)))


def band_pairs(Ba, Bb, min_overlap=-(P.AX - 0.05)):
    """Band pairs that overlap in y, or whose faces are closer than the axial gap: any 2D
    overlap of those is a collision or an axial-clearance violation."""
    for a0, a1, pa in Ba:
        for b0, b1, pb in Bb:
            ov = min(a1, b1) - max(a0, b0)
            if ov > min_overlap:
                yield (max(a0, b0), min(a1, b1)), pa, pb


def pair_distance(ka, Ba, kb, Bb, st, region=None, strict=False):
    """Smallest gap (negative = overlap depth estimate) between two posed parts. strict: only
    bands that really overlap in y (for the stepped ridge/groove and the detent, whose 0.2 mm
    steps would otherwise be compared with their neighbours)."""
    best = (1e9, None)
    for (y0, y1), pa, pb in band_pairs(Ba, Bb, 0.02 if strict else -(P.AX - 0.05)):
        ga, gb = PT.pose2(ka, pa, st), PT.pose2(kb, pb, st)
        if region is not None:
            ga, gb = ga.intersection(region), gb.intersection(region)
        if ga.is_empty or gb.is_empty:
            continue
        inter = ga.intersection(gb)
        if inter.area > 1e-5:
            # overlap depth: how far one has to shrink before they separate
            d = -_depth(ga, gb)
        else:
            d = ga.distance(gb)
        if d < best[0]:
            c = inter.centroid if inter.area > 1e-5 else None
            best = (d, dict(y=(round(y0, 2), round(y1, 2)),
                            at=(round(c.x, 1), round(c.y, 1)) if c is not None else None))
    return best


def _depth(ga, gb):
    lo, hi = 0.0, 3.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if ga.buffer(-mid / 2).intersection(gb.buffer(-mid / 2)).area > 1e-6:
            lo = mid
        else:
            hi = mid
    return hi


def all_bands():
    return {"upper": PT.upper_bands(), "blade": PT.blade_bands(),
            "blade_loaded": PT.blade_bands(loaded=True), "blade_nobar": PT.blade_bands(nobar=True),
            "lever": PT.lever_bands(),
            "bail_a": PT.bail_a_bands(), "bail_b": PT.bail_b_bands(),
            "pin_p": PT.pin_p_bands(), "pin_h": PT.pin_h_bands()}


def sweep(B, degs, log=print):
    """Minimum gap of every non-press pair over the stroke. The clamp contact (bar vs upper
    jaw) and the detent are handled separately (they are meant to interfere)."""
    names = [n for n in B if n not in ("blade_loaded", "blade_nobar", "blade_firm", "blade_firm_nobar")]
    res = {}
    clamp_region = box(-20, -30, 200, 30)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            k = _key(a, b)
            if k in PRESS:
                continue
            worst = (1e9, None, None)
            for dg in degs:
                st = M.pose(math.radians(dg))
                Ba, Bb = B[a], B[b]
                if k == ("blade", "upper"):
                    # the bar is the clamp spring's contact face: it is pressed against the jaw
                    # whenever the jaws are near closed. Check everything else on the blade here,
                    # and the bar's ridge-in-groove fit in the loaded lock pose (lock_fit()).
                    Ba = B["blade_nobar"] if a == "blade" else Ba
                    Bb = B["blade_nobar"] if b == "blade" else Bb
                region = None
                if k == ("lever", "upper"):
                    region = NOT_DETENT        # the detent is checked by detent_check()
                d, info = pair_distance(a, Ba, b, Bb, st, region=region)
                if k in RUNNING:
                    d2, info2 = pair_distance(a, Ba, b, Bb, st, region=_away_from_joints(st))
                    body = res.get(k + ("body",), (1e9, None, None))
                    if d2 < body[0]:
                        res[k + ("body",)] = (d2, dg, info2)
                if d < worst[0]:
                    worst = (d, dg, info)
            res[k] = worst
    return res


LOCKED_UNTIL = 30.0     # deg: until here the bar can still touch the jaw (bag thickness)
DETENT_BOX = box(P.PEG_X - 6, 3, P.PEG_X + 6, 10)
NOT_DETENT = box(-50, -60, 250, 60).difference(DETENT_BOX)


def _away_from_joints(st, r=3.4):
    """Everything except small discs round the four joints (their own fits are checked
    separately), so a running pair's other features are checked too."""
    pts = [D["P"], M.q_of(st["theta"]), st["K"], D["H"]]
    holes = unary_union([G.circ(p, r) for p in pts])
    return box(-50, -60, 250, 60).difference(holes)


def detent_check(B, log=print):
    """Peg/finger interference during the last degrees of the stroke, and its clearance when
    locked."""
    out = []
    region = box(P.PEG_X - 6, 3, P.PEG_X + 6, 10)
    for dg in np.arange(0.0, 8.01, 0.25):
        st = M.pose(math.radians(dg))
        near = lambda bands: [(a, b, p) for a, b, p in bands if abs((a + b) / 2) < 2.3]
        d, info = pair_distance("lever", near(B["lever"]), "upper", near(B["upper"]), st, region, strict=True)
        out.append((float(dg), d))
    return out


def peg_rise(theta):
    """How far the detent peg lifts from its locked position at lever angle theta."""
    px, pz = D["P"]
    r = (P.PEG_X - px, 6.2 - pz)
    v = M.rot(r, -theta)
    return (pz + v[1]) - 6.2


def lock_fit(B):
    """Locked pose with the bar pressed flush (bag thickness 0): the ridge must sit in the
    groove with its designed clearance and the bar face must meet the jaw face."""
    st = M.pose(0.0)
    out = {}
    for name, band_filter in (("ridge_flank_and_top", lambda y: abs(y) < P.RIDGE_BASE / 2),
                              ("bar_face_lands", lambda y: abs(y) >= P.RIDGE_BASE / 2)):
        Bb = [(a, b, p) for a, b, p in B["blade_loaded"] if band_filter((a + b) / 2)]
        Bu = [(a, b, p.intersection(box(P.BAR_X[0] + 4, -20, P.BAR_X[1] - 4, 20))) for a, b, p in B["upper"]]
        out[name] = pair_distance("blade", Bb, "upper", Bu, st, strict=True)
    return out
