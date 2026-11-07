"""
Print-time and filament estimate from the geometry itself.

No slicer could be run in the build environment, so this module does a slicer's arithmetic:
it slices each part at every layer, lays out walls, top/bottom skins and sparse infill the way
Bambu Studio's '0.20mm Standard @BBL A1M' process does, and times every move with a
trapezoidal acceleration model. Expect it to land within roughly +/-20 % of the slicer's
figure; the slicer's number is the one to trust. Assumptions are listed in PROCESS.
"""

import math

import numpy as np
import shapely
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

PROCESS = dict(
    printer="Bambu Lab A1 mini, 0.4 mm nozzle",
    process="0.20mm Standard @BBL A1M (values below)",
    filament="Bambu PLA Basic / Matte, 1.75 mm, 1.24 g/cm3",
    layer=0.20, first_layer=0.20, line_w=0.42, first_line_w=0.50,
    wall_loops=2, top_layers=5, bottom_layers=3, infill=0.15, infill_pattern="grid",
    v_outer=200.0, v_inner=300.0, v_sparse=270.0, v_solid=250.0, v_top=200.0,
    v_first=50.0, v_first_infill=105.0, v_travel=700.0,
    max_flow=21.0,            # mm3/s, Bambu PLA Basic profile
    acc=6000.0, acc_outer=5000.0, acc_top=2000.0, acc_travel=10000.0,
    corner_deg=25.0,          # direction change treated as a stop (pessimistic)
    layer_overhead_s=0.6,     # z move, wipe, retract/unretract at each layer change
    island_overhead_s=0.35,   # travel + retract per separate island / skin region
    start_overhead_min=4.0,   # A1 mini start: heat, wipe, prime line (no bed levelling)
    min_layer_time=4.0,
)


def to_shapely(sec):
    polys = [np.asarray(p) for p in sec.to_polygons() if len(p) >= 3]
    if not polys:
        return Polygon()
    # even-odd assembly: rings inside an odd number of rings are holes
    shells = [Polygon(p).buffer(0) for p in polys]
    out = Polygon()
    for s in shells:
        out = out.symmetric_difference(s)
    return out.buffer(0)


def _segments_time(lengths, v, a):
    L = np.asarray(lengths, float)
    if L.size == 0:
        return 0.0
    full = L >= v * v / a
    t = np.where(full, L / v + v / a, 2 * np.sqrt(np.maximum(L, 0) / a))
    return float(t.sum())


def _ring_runs(geom, corner_deg):
    """Split all rings of a (multi)polygon into straight-ish runs between sharp corners."""
    runs = []
    polys = getattr(geom, "geoms", [geom])
    for pg in polys:
        if pg.is_empty:
            continue
        for ring in [pg.exterior, *pg.interiors]:
            c = np.asarray(ring.coords)[:-1]
            if len(c) < 3:
                continue
            seg = np.roll(c, -1, axis=0) - c
            ln = np.linalg.norm(seg, axis=1)
            ang = np.arctan2(seg[:, 1], seg[:, 0])
            turn = np.abs((np.diff(np.r_[ang, ang[0]]) + np.pi) % (2 * np.pi) - np.pi)
            breaks = np.where(np.degrees(turn) > corner_deg)[0]
            if len(breaks) == 0:
                runs.append(ln.sum())
                continue
            acc = 0.0
            for i in range(len(ln)):
                acc += ln[i]
                if i in set(breaks):
                    runs.append(acc)
                    acc = 0.0
            if acc > 0:
                runs.append(acc)
    return runs


def _ring_length(geom):
    polys = getattr(geom, "geoms", [geom])
    return sum(pg.exterior.length + sum(i.length for i in pg.interiors) for pg in polys if not pg.is_empty)


def _hatch(region, spacing, angle_deg):
    if region.is_empty:
        return []
    minx, miny, maxx, maxy = region.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    R = math.hypot(maxx - minx, maxy - miny) / 2 + 1
    a = math.radians(angle_deg)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    lines = []
    for k in np.arange(-R, R, spacing):
        p0 = np.array([cx, cy]) + n * k - d * R
        p1 = np.array([cx, cy]) + n * k + d * R
        lines.append(LineString([p0, p1]))
    inter = shapely.intersection(np.array(lines, dtype=object), region)
    out = []
    for g in inter:
        if g.is_empty:
            continue
        for s in getattr(g, "geoms", [g]):
            if s.length > 1e-3:
                out.append(s.length)
    return out


def estimate(part, name="part", pr=PROCESS):
    """part: a manifold3d Manifold in print orientation (z = 0 on the bed)."""
    zmax = part.bounding_box()[5]
    h, w = pr["layer"], pr["line_w"]
    zs = [pr["first_layer"] / 2]
    while zs[-1] + h <= zmax - 1e-6 + h / 2:
        zs.append(zs[-1] + h)
    zs = [z for z in zs if z < zmax]
    regions = [to_shapely(part.slice(z)) for z in zs]
    v_cap = pr["max_flow"] / (w * h)
    t_total, vol, report = 0.0, 0.0, []
    for i, (z, R) in enumerate(zip(zs, regions)):
        if R.is_empty:
            continue
        first = i == 0
        lh = pr["first_layer"] if first else h
        lw = pr["first_line_w"] if first else w
        outer = R.buffer(-lw / 2, join_style=2)
        inner = R.buffer(-1.5 * lw, join_style=2)
        core = R.buffer(-(2 * lw - 0.15 * lw), join_style=2)
        Lo, Li = _ring_length(outer), _ring_length(inner)
        # skins
        above = regions[i + 1:i + 1 + pr["top_layers"]]
        below = regions[max(0, i - pr["bottom_layers"]):i]
        if len(above) < pr["top_layers"]:
            sup_above = Polygon()
        else:
            sup_above = above[0]
            for r in above[1:]:
                sup_above = sup_above.intersection(r)
        if len(below) < pr["bottom_layers"]:
            sup_below = Polygon()
        else:
            sup_below = below[0]
            for r in below[1:]:
                sup_below = sup_below.intersection(r)
        top_skin = core.difference(sup_above.buffer(-0.01))
        bot_skin = core.difference(sup_below.buffer(-0.01))
        # top surface proper = exposed to air directly above
        nxt = regions[i + 1] if i + 1 < len(regions) else Polygon()
        top_surf = core.difference(nxt.buffer(-0.01))
        solid = unary_union([top_skin, bot_skin]).buffer(0)
        sparse = core.difference(solid).buffer(0)
        ang = 45 if i % 2 == 0 else -45
        Ls_top = _hatch(top_surf, lw, ang)
        Ls_solid = _hatch(solid.difference(top_surf).buffer(0), lw, ang)
        Ls_sparse = _hatch(sparse, 2 * w / pr["infill"], 45) + _hatch(sparse, 2 * w / pr["infill"], -45)
        if first:
            vo = vi = pr["v_first"]
            vs = vt = vsp = pr["v_first_infill"]
        else:
            vo, vi = min(pr["v_outer"], v_cap), min(pr["v_inner"], v_cap)
            vs, vt, vsp = min(pr["v_solid"], v_cap), min(pr["v_top"], v_cap), min(pr["v_sparse"], v_cap)
        t = 0.0
        t += _segments_time(_ring_runs(outer, pr["corner_deg"]), vo, pr["acc_outer"])
        t += _segments_time(_ring_runs(inner, pr["corner_deg"]), vi, pr["acc"])
        t += _segments_time(Ls_top, vt, pr["acc_top"])
        t += _segments_time(Ls_solid, vs, pr["acc"])
        t += _segments_time(Ls_sparse, vsp, pr["acc"])
        n_isl = len(getattr(R, "geoms", [R]))
        n_skin = len(getattr(solid, "geoms", [solid])) if not solid.is_empty else 0
        t += pr["layer_overhead_s"] + pr["island_overhead_s"] * (2 * n_isl + n_skin)
        t = max(t, pr["min_layer_time"])
        L_ext = Lo + Li + sum(Ls_top) + sum(Ls_solid) + sum(Ls_sparse)
        vol += L_ext * lw * lh
        t_total += t
        report.append((z, t, L_ext))
    grams = vol / 1000 * 1.24
    metres = vol / (math.pi * 0.875 ** 2) / 1000
    return dict(name=name, layers=len(report), print_min=t_total / 60, grams=grams, metres=metres,
                solid_cm3=part.volume() / 1000)
