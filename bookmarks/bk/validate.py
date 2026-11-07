"""BK-01 BOOKMARKS: engineering validation, measured on the delivered geometry.

Every number here is measured from the solids (manifold3d slices, booleans and mesh
properties), not copied from the parameters. Each check returns pass/fail plus the
measured values; the report writer prints them all.
"""

import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from . import art
from . import params as P
from . import props
from .export import mesh_arrays

LAYER = 0.2


# =====================================================================================
# helpers
# =====================================================================================


def section(m, z):
    """Horizontal slice of a manifold at height z -> shapely geometry (holes respected)."""
    polys = m.slice(z).to_polygons()
    outers, holes = [], []
    for r in polys:
        r = np.asarray(r)
        if len(r) < 3:
            continue
        pg = Polygon(r)
        if not pg.is_valid:
            pg = pg.buffer(0)
        a = 0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1])
        (outers if a > 0 else holes).append(pg)
    g = unary_union(outers) if outers else Polygon()
    if holes:
        g = g.difference(unary_union(holes))
    return g


def _polys(g):
    if g.is_empty:
        return []
    return [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.geom_type == "Polygon"]


def chord(g, a, b):
    """Lengths of the pieces of segment a-b that lie inside g."""
    seg = LineString([a, b]).intersection(g)
    parts = [seg] if seg.geom_type == "LineString" else list(getattr(seg, "geoms", []))
    return [p.length for p in parts if p.length > 1e-6]


def check(name, ok, **vals):
    return dict(name=name, ok=bool(ok), **vals)


# =====================================================================================
# checks
# =====================================================================================


def envelope(result):
    bb = result["full"].bounding_box()
    size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    target = (P.W, P.D, P.H)
    err = max(abs(a - b) for a, b in zip(size, target))
    parts_inside = all(
        m.bounding_box()[0] >= bb[0] - 1e-6 and m.bounding_box()[3] <= bb[3] + 1e-6 for m in result["parts"].values())
    return check("Overall envelope = customer dimensions (decoration included)", err < 0.02 and bb[2] > -1e-6 and parts_inside,
                 measured=tuple(round(v, 3) for v in size), target=target, max_error=round(err, 4),
                 min_corner=tuple(round(v, 3) for v in bb[:3]))


def manifold(result):
    rows, ok = [], True
    for k, m in list(result["parts"].items()) + [("FULL (single colour)", result["full"])]:
        bodies = m.decompose()
        st = str(m.status()).split(".")[-1]
        rows.append(dict(part=k, status=st, triangles=m.num_tri(), volume=round(m.volume(), 2),
                         genus=m.genus(), bodies=len(bodies), min_body=round(min(b.volume() for b in bodies), 2)))
        ok &= st == "NoError" and min(b.volume() for b in bodies) > 0.5
    ok &= len(result["full"].decompose()) == 1
    return check("Every region and the full part are closed 2-manifolds; the full part is ONE body", ok, rows=rows)


def separation(result):
    ps = result["parts"]
    ks = list(ps)
    worst, pairs = 0.0, []
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            v = (ps[ks[i]] ^ ps[ks[j]]).volume()
            worst = max(worst, v)
            if v > 1e-6:
                pairs.append((ks[i], ks[j], round(v, 5)))
    s = sum(m.volume() for m in ps.values())
    f = result["full"].volume()
    return check("Colour regions are disjoint and tile the part exactly", worst < 1e-3 and abs(s - f) / f < 1e-4,
                 max_overlap_mm3=round(worst, 6), overlapping_pairs=pairs, sum_of_regions=round(s, 2),
                 full_volume=round(f, 2), mismatch_pct=round(100 * abs(s - f) / f, 5))


def islands(result):
    rows, ok = [], True
    for k, m in result["parts"].items():
        bs = sorted(m.decompose(), key=lambda b: b.volume())
        dims = []
        for b in bs:
            bb = b.bounding_box()
            dims.append(sorted([bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]]))
        rows.append(dict(part=k, islands=len(bs), smallest_mm3=round(bs[0].volume(), 2),
                         smallest_dims=[round(d, 2) for d in dims[0]]))
        ok &= bs[0].volume() >= 2.0
    return check("No tiny colour islands (every island >= 2 mm3) and none floating (full part is one body)",
                 ok and len(result["full"].decompose()) == 1, rows=rows)


def compartment(result):
    full = result["full"]
    out = {}
    # floor: first height at which the section has a hole
    zf = None
    for z in np.arange(0.1, 6.0, 0.05):
        g = section(full, z)
        if any(len(p.interiors) for p in _polys(g)):
            zf = z
            break
    out["floor_thickness"] = round(zf - 0.05, 2) if zf else None
    stations = {}
    for z in (P.FLOOR + P.CAV_FLOOR_R + 0.5, 20.0, 42.0, 70.0, P.H - P.HEAD_SQUARE - P.CAV_LIP - 0.2):
        g = section(full, z)
        main = max(_polys(g), key=lambda p: p.area)
        hole = Polygon(max(main.interiors, key=lambda r: Polygon(r).area))
        x0, y0, x1, y1 = hole.bounds
        stations[round(z, 1)] = dict(width=round(x1 - x0, 2), depth=round(y1 - y0, 2), area=round(hole.area, 1))
    out["stations"] = stations
    zc = 42.0
    st = stations[zc]
    out["usable"] = dict(width=st["width"], depth=st["depth"], height=round(P.H - P.FLOOR, 2),
                         volume_ml=round(stations[zc]["area"] * (P.H - P.FLOOR) / 1000, 1))
    # a bookmark-sized gauge and the prop set must not touch the part
    gauge = props.standard_gauge()
    gi = (gauge ^ full).volume()
    pset = props.bookmark_set()
    pi = {b["name"]: round((b["solid"] ^ full).volume(), 4) for b in pset}
    ok = (out["floor_thickness"] is not None and abs(out["floor_thickness"] - P.FLOOR) < 0.1
          and st["width"] > 50.8 + 10 and st["depth"] > 30 and gi < 1e-6 and max(pi.values()) < 1e-6)
    return check("Compartment is genuinely hollow, open and takes real bookmarks", ok, floor=out["floor_thickness"],
                 stations=stations, usable=out["usable"], gauge_interference=round(gi, 6), prop_interference=pi,
                 props=[(b["name"], b["size"]) for b in pset])


def opening(result):
    """Straight-down access: every lower section of the cavity lies inside the opening."""
    full = result["full"]
    worst = 0.0
    g = section(full, P.H - P.HEAD_SQUARE - 0.05)
    mm = max(_polys(g), key=lambda p: p.area)
    tophole = Polygon(max(mm.interiors, key=lambda r: Polygon(r).area))
    for z in np.arange(P.FLOOR + 0.3, P.H - P.HEAD_SQUARE - 0.1, 0.5):
        g = section(full, z)
        m = max(_polys(g), key=lambda p: p.area)
        if not m.interiors:
            continue
        h = Polygon(max(m.interiors, key=lambda r: Polygon(r).area))
        worst = max(worst, h.difference(tophole).area)
    return check("Opening is unobstructed: no lip or ledge overhangs the cavity", worst < 0.01,
                 hidden_area_mm2=round(worst, 4), opening_w=round(tophole.bounds[2] - tophole.bounds[0], 2),
                 opening_d=round(tophole.bounds[3] - tophole.bounds[1], 2))


def walls(result):
    full = result["full"]
    yb, yfr = P.D - P.CAV_Y0, P.D - P.CAV_Y1     # world y of the back and front cavity faces
    rows, mins = [], []
    zs = np.arange(P.FLOOR + 0.5, P.H - 1.6, 1.0)
    for z in zs:
        g = section(full, z)
        m = max(_polys(g), key=lambda p: p.area)
        if not m.interiors:
            continue
        hole = max(m.interiors, key=lambda r: Polygon(r).area)
        d = hole.distance(m.exterior)
        mins.append((d, z))
    dmin, zmin = min(mins)
    # named walls at mid height: each face of the cavity to the nearest outside surface
    g = section(full, 40.0)
    m = max(_polys(g), key=lambda p: p.area)
    hole = max(m.interiors, key=lambda r: Polygon(r).area)
    from shapely.geometry import box as _box
    xc0, xc1 = P.CAV_X0, P.CAV_X1

    def face(bx):
        return LineString(hole.coords).intersection(_box(*bx)).distance(m.exterior)

    named = dict(
        front=face((xc0 + 3, yfr - 0.1, xc1 - 3, yfr + 0.1)),
        front_plain_strip=face((xc0 + 3, yfr - 0.1, 12.0, yfr + 0.1)),
        back=face((xc0 + 3, yb - 0.1, xc1 - 3, yb + 0.1)),
        spine_side=face((xc0 - 0.1, yfr + 3, xc0 + 0.1, yb - 3)),
        fore_edge_to_page_grooves=face((xc1 - 0.1, yfr + 3, xc1 + 0.1, yb - 3)),
    )
    ok = dmin >= P.WALL - 0.05
    return check(f"Wall thickness >= {P.WALL - 0.05:.2f} mm everywhere below the rim lead-in", ok,
                 min_wall=round(dmin, 3), at_z=round(zmin, 1), named={k: round(v, 3) for k, v in named.items()},
                 note="Above z = H-1.5 the opening has a 0.5 mm lead-in and the top edge a 0.5 mm chamfer, "
                      "so the cover rim narrows to ~1.0 mm in its last 0.5 mm by design.")


def overhangs(result):
    """Slicer's-eye check: each layer must lie within 45 deg (one layer height) of the one below."""
    full = result["full"]
    tol = LAYER * math.tan(math.radians(P.OVERHANG_MAX_DEG)) + 0.06
    prev = section(full, LAYER * 0.5)
    worst_area, worst_z, total = 0.0, None, 0.0
    for z in np.arange(LAYER * 1.5, P.H, LAYER):
        cur = section(full, z)
        un = cur.difference(prev.simplify(0.01).buffer(tol, 2))
        a = un.area
        total += a
        if a > worst_area:
            worst_area, worst_z = a, z
        prev = cur
    ok = worst_area < 0.5
    return check("No supports needed: every layer is carried by the one below at <= 45 deg", ok,
                 worst_unsupported_mm2=round(worst_area, 3), at_z=None if worst_z is None else round(worst_z, 2),
                 total_unsupported_mm2=round(total, 3), tolerance_mm=round(tol, 3))


def thin_features(result):
    """Detail width as the nozzle sees it: each coloured region drawn on the front plane.
    (Relief is fused to the cover, so depth is never the limit; across the cover the
    0.4 mm line width is.)"""
    groups = dict(lettering=["letters"], petals=["petals", "petal_lines"], centres=["centres"],
                  foliage=["ground", "foliage", "veins"])
    by = {L["name"]: L["g"] for L in result["layers"]}
    rows, ok = [], True
    for k, names in groups.items():
        g = unary_union([by[n] for n in names])
        a = g.area
        t08 = a - g.buffer(-P.MIN_FEATURE / 2, 16).buffer(P.MIN_FEATURE / 2, 16).area
        t05 = a - g.buffer(-0.25, 16).buffer(0.25, 16).area
        gap = g.buffer(P.MIN_GAP / 2, 16).buffer(-P.MIN_GAP / 2, 16).area - a
        rows.append(dict(part=k, area_mm2=round(a, 1), pct_under_0p8=round(100 * t08 / a, 2),
                         pct_under_0p5=round(100 * t05 / a, 2), gaps_under_0p6_mm2=round(gap, 2)))
        ok &= t05 / a < (0.01 if k in ("lettering", "centres") else 0.05)
    return check("Coloured detail is resolvable by a 0.4 mm nozzle", ok, rows=rows,
                 note="'Under 0.8/0.5' = share of the region's front-face area in features narrower than "
                      "2 / 1.25 line widths: the tapered tips of petals, leaves and grass. The slicer prints them "
                      "with Arachne's narrower lines or drops the last fraction of a millimetre of a tip. "
                      "Pages: a 0.8 mm (2-line) skin with 0.5 mm grooves, read from the side.")


def lettering_check(result):
    text, letters = result["art"]["text"], result["art"]["letters"]
    x0, z0, x1, z1 = text.bounds
    rows, ok = [], True
    for ch, g in zip([c for c in P.TEXT if c != " "], letters):
        # thickest erosion that still keeps the letter in one piece = stroke width
        w = 0.0
        for e in np.arange(0.2, 2.4, 0.05):
            er = g.buffer(-e / 2, 8)
            if er.is_empty or len(_polys(er)) > len(_polys(g)):
                break
            w = e
        rows.append((ch, round(w, 2)))
        ok &= w >= 1.0
    plate = result["art"]["plate"]
    return check("Lettering is bold enough to print and read", ok, text=P.TEXT, font="Bubblegum Sans (SIL OFL 1.1)",
                 text_w=round(x1 - x0, 2), text_h=round(z1 - z0, 2), min_stroke=min(r[1] for r in rows), strokes=rows,
                 inside_plate=plate.buffer(-1.5).contains(text), letter_relief=P.LETTER_RISE,
                 white_depth=P.LETTER_RISE + P.LETTER_INLAY)


def stability(result):
    full = result["full"]
    v, t = mesh_arrays(full)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    com = ((a + b + c) * vol6[:, None]).sum(0) / (4 * vol6.sum())
    foot = section(full, 0.05).convex_hull
    from shapely.geometry import Point
    edge = foot.exterior.distance(Point(com[0], com[1]))
    tip = math.degrees(math.atan2(edge, com[2]))
    fp = section(full, 0.05)
    grams = full.volume() / 1000 * P.PETG_DENSITY
    return check("Stable on the bed and on the desk", tip > 20, footprint_mm2=round(fp.area, 1),
                 centre_of_mass=tuple(round(x, 2) for x in com), tipping_angle_deg=round(tip, 1),
                 solid_volume_cm3=round(full.volume() / 1000, 2), solid_mass_g=round(grams, 1))


def colour_layers(result):
    """How many layers hold each colour, and the filament swaps each colour plan needs."""
    ps = result["parts"]
    nl = int(round(P.H / LAYER))
    present = {k: np.zeros(nl, bool) for k in ps}
    for k, m in ps.items():
        bb = m.bounding_box()
        for i in range(nl):
            z = (i + 0.5) * LAYER
            if bb[2] <= z <= bb[5] and not m.slice(z).is_empty():
                present[k][i] = True
    plans = {}
    for plan, spec in P.PLANS.items():
        slots = np.zeros((nl, 5), bool)
        for k in ps:
            slots[:, spec["slots"][k]] |= present[k]
        per_layer = slots.sum(1)
        single = int(np.maximum(per_layer - 1, 0).sum())
        # two-nozzle machine: a change between nozzles needs no flush; a change between two
        # filaments sharing a nozzle does (roughly one per layer that holds both)
        flushes = 0
        for side, ss in spec["nozzles"].items():
            n_side = slots[:, list(ss)].sum(1)
            flushes += int(np.maximum(n_side - 1, 0).sum())
        plans[plan] = dict(filaments=len(spec["filaments"]), layers_with_2plus=int((per_layer > 1).sum()),
                           max_in_one_layer=int(per_layer.max()), changes_one_nozzle=single,
                           flushes_two_nozzles=flushes, nozzle_map=spec["nozzles"],
                           slot_layers={s: int(slots[:, s].sum()) for s in range(1, 5) if slots[:, s].any()})
    rng = {k: (round(float(np.argmax(v)) * LAYER, 1), round((nl - float(np.argmax(v[::-1]))) * LAYER, 1)) if v.any() else None
           for k, v in present.items()}
    return check("Colour regions are independently assignable; colour-change load measured", True,
                 z_ranges=rng, layers=nl, plans=plans,
                 grams={k: round(m.volume() / 1000 * P.PETG_DENSITY, 2) for k, m in ps.items()})


def run_all(result):
    checks = [envelope(result), manifold(result), separation(result), islands(result), compartment(result),
              opening(result), walls(result), overhangs(result), thin_features(result), lettering_check(result),
              stability(result), colour_layers(result)]
    return checks
