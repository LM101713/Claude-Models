"""BK-01 BOOKMARKS: solid geometry (manifold3d), built in the print frame.

    build() -> dict of colour-region solids that tile the part exactly:
               body, pages, lettering, petals, centres, foliage
               plus 'full' (their union) and the 2D layers used to make them.

Every region is an exact manifold. Regions touch but never overlap, so they can be
assigned to filaments independently in Bambu Studio and their union is the single-colour
part.
"""

import math

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold, OpType, set_circular_segments
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from . import art
from . import params as P

set_circular_segments(96)
RES = 24


# =====================================================================================
# shapely <-> manifold
# =====================================================================================


def _polys(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon) and not p.is_empty]


def cross(g):
    """shapely (Multi)Polygon -> CrossSection (rings oriented, holes respected)."""
    rings = []
    for p in _polys(g):
        ext = np.asarray(p.exterior.coords)[:-1]
        if Polygon(ext).exterior.is_ccw is False:
            ext = ext[::-1]
        rings.append(ext)
        for h in p.interiors:
            hc = np.asarray(h.coords)[:-1]
            if Polygon(hc).exterior.is_ccw:
                hc = hc[::-1]
            rings.append(hc)
    if not rings:
        return CrossSection()
    return CrossSection(rings, FillRule.Positive)


def prism_z(g, z0, z1):
    """Plan shape (x, y) extruded from z0 to z1."""
    cs = cross(g)
    if cs.is_empty() or z1 <= z0:
        return Manifold()
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def prism_y(g, y0, y1):
    """Front-plane shape (x, z) extruded along +Y from y0 to y1."""
    cs = cross(g)
    if cs.is_empty() or y1 <= y0:
        return Manifold()
    # rotate +90 about X: (x, y, z) -> (x, -z, y), so local y -> world z, depth -> -y
    return Manifold.extrude(cs, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def union(ms):
    ms = [m for m in ms if not m.is_empty()]
    if not ms:
        return Manifold()
    return Manifold.batch_boolean(ms, OpType.Add)


def clean(m, min_vol=1e-3):
    """Drop zero-volume debris (flat 4-8 triangle shells the booleans leave where slice
    faces coincide). Real geometry is untouched: every kept body has positive volume."""
    bodies = [b for b in m.decompose() if b.volume() > min_vol]
    return Manifold.compose(bodies) if bodies else Manifold()


# =====================================================================================
# the book shell
# =====================================================================================


def plan_outline():
    """Plan view (x, y) of the book: rounded spine, two cover boards, recessed page block."""
    sb, yf = P.SPINE_BULGE, P.YF
    R = ((yf / 2) ** 2 + sb ** 2) / (2 * sb)
    spine = Point(R, yf / 2).buffer(R, 720).intersection(box(0, 0, sb + 1.0, yf))
    boards = unary_union([box(sb, 0, P.W, P.BOARD), box(sb, yf - P.BOARD, P.W, yf)])
    block = box(sb, 0, P.W - P.SQUARE, yf)
    outline = unary_union([spine, boards, block])
    # round convex outer corners, ease the concave corners where boards meet the block
    outline = outline.buffer(-P.EDGE_R, RES).buffer(P.EDGE_R, RES)
    outline = outline.buffer(0.3, RES).buffer(-0.3, RES)
    # hinge grooves ("joints") on both boards: shallow round-bottomed channels
    rg = ((P.HINGE_W / 2) ** 2 + P.HINGE_DEPTH ** 2) / (2 * P.HINGE_DEPTH)
    grooves = [Point(P.HINGE_X, yf + rg - P.HINGE_DEPTH).buffer(rg, RES * 2),
               Point(P.HINGE_X, -rg + P.HINGE_DEPTH).buffer(rg, RES * 2)]
    # page lines on the fore-edge
    xe = P.W - P.SQUARE
    rp = P.PAGE_GROOVE_W / 2
    ys = np.arange(P.BOARD + 0.9, yf - P.BOARD - 0.6, P.PAGE_PITCH)
    ys += 0.5 * ((yf - P.BOARD - 0.6) - ys[-1] - (P.BOARD + 0.9 - P.BOARD))  # centre the set
    pages = [Point(xe - P.PAGE_GROOVE_DEPTH + rp, y).buffer(rp, RES) for y in ys]
    return outline.difference(unary_union(grooves + pages)), len(ys)


def stepped_prism(outline, z0, z1, foot, top, step):
    """Extrude with 45-degree chamfers at the bottom (foot) and top, built in `step` layers."""
    parts = []
    nb, nt = int(round(foot / step)), int(round(top / step))
    for k in range(nb):
        inset = foot - k * step
        parts.append(prism_z(outline.buffer(-inset, RES, join_style=2), z0 + k * step, z0 + (k + 1) * step))
    parts.append(prism_z(outline, z0 + foot, z1 - top))
    for k in range(nt):
        inset = (k + 1) * step
        parts.append(prism_z(outline.buffer(-inset, RES, join_style=2), z1 - top + k * step, z1 - top + (k + 1) * step))
    return union(parts)


def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, RES * 2)


def cavity():
    """Storage cavity: rounded vertical corners (R2.5), an R2.5 floor fillet and a 0.5 mm 45°
    lead-in at the opening. Built from exact rounded-rectangle extrusions stacked in 0.1 mm
    steps (well under one layer), not from a convex hull: a hull of spheres leaves sliver
    facets lying almost in the wall planes, which do not survive export cleanly."""
    r, rf, st = P.CAV_R, P.CAV_FLOOR_R, P.CHAMFER_STEP
    x0, x1, y0, y1 = P.CAV_X0, P.CAV_X1, P.CAV_Y0, P.CAV_Y1

    def rr(off):  # the cavity outline offset outward by `off` (negative = inward)
        return rounded_rect(x0 - off, y0 - off, x1 + off, y1 + off, max(0.05, r + off))

    parts = []
    n = int(round(rf / st))
    for k in range(n):                         # floor fillet: quarter circle, sampled mid-step
        h = (k + 0.5) * st
        inset = rf - math.sqrt(max(0.0, rf * rf - (rf - h) ** 2))
        parts.append(prism_z(rr(-inset), P.FLOOR + k * st, P.FLOOR + (k + 1) * st))
    zl = P.H - P.HEAD_SQUARE                   # the lead-in ends at the page-head level
    z_lip = zl - P.CAV_LIP
    parts.append(prism_z(rr(0.0), P.FLOOR + rf, z_lip))
    m = int(round(P.CAV_LIP / st))
    for k in range(m):                         # 45 deg lead-in
        parts.append(prism_z(rr((k + 1) * st), z_lip + k * st, z_lip + (k + 1) * st))
    parts.append(prism_z(rr(P.CAV_LIP), zl, P.H + 2.0))
    return union(parts)


def head_recess():
    """The page block sits HEAD_SQUARE below the boards and the spine's headcap."""
    g = box(P.SPINE_BULGE + 0.8, P.BOARD, P.W + 1, P.YF - P.BOARD)
    return prism_z(g, P.H - P.HEAD_SQUARE, P.H + 1)


def page_zone():
    """Where the page colour goes: a skin on the fore-edge and a cap on the head of the block."""
    # kept 0.25 mm clear of the board planes, which are also the cavity-wall planes, so no
    # face of the page region ever lies on a face of the cavity
    y0, y1 = P.BOARD + 0.25, P.YF - P.BOARD - 0.25
    skin = box(P.W - P.SQUARE - P.PAGE_SKIN, y0, P.W + 1, y1)
    head = box(P.SPINE_BULGE + 0.8, y0, P.W + 1, y1)
    return union([prism_z(skin, -1, P.H + 1),
                  prism_z(head, P.H - P.HEAD_SQUARE - P.PAGE_HEAD_CAP, P.H + 1)])


def shell():
    outline, n_pages = plan_outline()
    s = stepped_prism(outline, 0.0, P.H, P.FOOT_CHAMFER, P.TOP_CHAMFER, P.CHAMFER_STEP)
    s = s - head_recess()
    s = s - cavity()
    return s, outline, n_pages


# =====================================================================================
# the front relief: one height-field, sliced so every underside is 45 degrees
# =====================================================================================


def relief_layers():
    """The art as disjoint 2D regions, each with a rise, a softening rule and a colour rule."""
    text, letters = art.lettering()
    plate = art.nameplate()
    m = art.meadow()
    lt0 = P.PLATE_RISE - P.LETTER_INLAY

    def plate_soft(t):          # bevel on the nameplate's top and sides
        return P.PLATE_SIDE_BEVEL * min(1.0, t / P.PLATE_RISE)

    def top_soft(rise):
        def f(t):
            return P.TOP_SOFTEN * min(1.0, max(0.0, (t - (rise - 0.45)) / 0.45))
        return f

    L = [
        dict(name="plate", g=plate.difference(text), rise=P.PLATE_RISE, soft=plate_soft, col=lambda t: "body"),
        dict(name="letters", g=text, rise=P.RELIEF_MAX, soft=top_soft(P.RELIEF_MAX),
             col=lambda t: "lettering" if t >= lt0 - 1e-9 else "body"),
        dict(name="ground", g=m["ground"], rise=P.GROUND_RISE, soft=top_soft(P.GROUND_RISE), col=lambda t: "foliage"),
        dict(name="foliage", g=m["foliage"].difference(m["veins"]), rise=P.FOLIAGE_RISE,
             soft=top_soft(P.FOLIAGE_RISE), col=lambda t: "foliage"),
        dict(name="veins", g=m["veins"], rise=P.VEIN_RISE, soft=lambda t: 0.0, col=lambda t: "foliage"),
        dict(name="petals", g=m["petals"].difference(m["petal_lines"]), rise=P.PETAL_RISE,
             soft=top_soft(P.PETAL_RISE), col=lambda t: "petals"),
        dict(name="petal_lines", g=m["petal_lines"], rise=P.PETAL_RISE - 0.4, soft=lambda t: 0.0,
             col=lambda t: "petals"),
        dict(name="centres", g=m["centres"], rise=P.CENTRE_RISE, soft=top_soft(P.CENTRE_RISE),
             col=lambda t: "centres"),
    ]
    # the plate also gets a 45-degree underside through the recursion; that keeps the
    # bottom edge printable without a ledge
    return L, dict(text=text, letters=letters, plate=plate, meadow=m)


def tidy(g, min_area=0.03, min_width=0.06):
    """Drop boolean slivers: micro-polygons left along shared boundaries."""
    keep = [p for p in _polys(g.buffer(0)) if p.area >= min_area and not p.buffer(-min_width / 2).is_empty]
    return unary_union(keep) if keep else Polygon()


def relief(layers, step=P.RELIEF_STEP):
    """Slice k spans depth [t, t+step] in front of the cover plane, t = k*step.

    support  S_0 = union of every region;  S_k = {regions with rise > t}  n  (S_{k-1} moved up one step)
             so a slice can only reach one step (0.2 mm) lower than the slice behind it:
             every underside is 45 degrees, whatever the shape or its neighbours.
    easing   each region is eased near its own top, but only along edges that face lower
             relief or the cover (region i is eroded as part of U_i = all regions at least as
             high as i), so no seam ever opens between a region and a taller neighbour.
    slice_k  = S_k  n  eased_k, split back into the disjoint colour regions.

    Returns {colour: [(t0, t1, shapely region)]} and the slice outlines.
    """
    n = int(math.ceil(P.RELIEF_MAX / step - 1e-9))
    out, R = {}, []
    prev = None
    for k in range(n):
        t = k * step
        top = min(P.RELIEF_MAX, t + step)
        live = [L for L in layers if L["rise"] > t + 1e-9]
        raw = unary_union([L["g"] for L in live])
        S = raw if prev is None else raw.intersection(affinity.translate(prev, 0, step))
        S = S.buffer(0)
        eased = []
        for L in live:
            U = unary_union([M["g"] for M in live if M["rise"] >= L["rise"] - 1e-9])
            sft = L["soft"](top)
            eased.append(U.buffer(-sft, RES) if sft > 0 else U)
        sl = tidy(S.intersection(unary_union(eased)))
        R.append(sl)
        for L in live:
            piece = tidy(sl.intersection(L["g"]))
            if piece.is_empty:
                continue
            out.setdefault(L["col"](t), []).append((t, min(top, L["rise"]), piece))
        prev = S
    return out, R


GROW = 0.002   # 2 microns: same-colour columns are grown this much inside their own colour


def relief_solids(layers):
    """Each slice becomes a COLUMN from the cover plane (or, for the lettering, from the
    top of its inlay) up to the slice's top, so successive slices overlap by volume and the
    union is a clean height field.

    Within one colour, pieces that share a top height are merged, then grown by GROW and
    clipped back to that colour's own region. Two columns of the same colour therefore
    overlap rather than touch along a single line (a line contact is a non-manifold edge
    once a slicer welds the STL), while the boundary between two different colours stays
    exactly where it was, so colour regions still never overlap.
    Returns per-colour solids, the slice outlines, and the merged pieces."""
    pieces, R = relief(layers)
    lt0 = P.PLATE_RISE - P.LETTER_INLAY
    def region(c, t):
        """Plan area that is colour c at depth t (e.g. a letter footprint is body below the
        inlay floor and lettering above it)."""
        return unary_union([L["g"] for L in layers if L["rise"] > t + 1e-9 and L["col"](t) == c]).buffer(0)

    solids, merged = {}, {}
    for c, lst in pieces.items():
        base = lt0 if c == "lettering" else 0.0
        # nested slabs: the footprint at each level is every piece at least that high, so
        # each slab sits inside the one below and no two columns can meet at a point or line
        levels = sorted({round(t1, 6) for _, t1, _ in lst})
        slabs, lo = [], base
        for lev in levels:
            foot = unary_union([g for _, t1, g in lst if t1 >= lev - 1e-9])
            foot = tidy(foot.buffer(GROW, 4).intersection(region(c, lo)))
            if not foot.is_empty:
                merged.setdefault(c, []).append((lo, lev, foot))
                slabs.append(prism_y(foot, P.YF + lo, P.YF + lev))
            lo = lev
        solids[c] = union(slabs)
    return solids, R, merged


def to_world(m):
    """Design frame -> delivered frame. The geometry is designed with the back cover on
    y = 0 and the art drawn as seen from the front; turning the book to face -Y makes the
    art read correctly from the front, with the spine on the viewer's left (as on a real
    book and in the reference photo). Bambu Studio's default view also looks along +Y,
    so the front cover faces the user when the file opens."""
    return m.mirror([0, 1, 0]).translate([0, P.D, 0])


# =====================================================================================
# assemble the colour regions
# =====================================================================================


def build():
    body, outline, n_pages = shell()
    shell_solid = body
    layers, art2d = relief_layers()
    rel, R, rel_pieces = relief_solids(layers)
    zone = page_zone()
    pages = body ^ zone          # intersection
    front = {c: rel.get(c, Manifold()) for c in ("lettering", "petals", "centres", "foliage")}
    # The front regions are disjoint in plan, stand ON the cover plane and (for the
    # lettering) on the plate's inlay floor, so nothing needs subtracting: every pair of
    # regions meets face-to-face and never overlaps.
    body = union([body - zone, rel.get("body", Manifold())])
    parts = {k: to_world(clean(v)) for k, v in dict(body=body, pages=pages, **front).items()}
    # The single-colour solid: the shell plus the relief as NESTED slabs. Level k's footprint
    # is everything at least that high (all colours together), so each slab sits inside the
    # one below it and no two pieces can meet along a line. Same surface as the six regions.
    allreg = unary_union([L["g"] for L in layers]).buffer(0)
    levels = sorted({t1 for lst in rel_pieces.values() for _, t1, _ in lst})
    slabs, lo = [], 0.0
    for lev in levels:
        foot = unary_union([g for lst in rel_pieces.values() for _, t1, g in lst if t1 >= lev - 1e-9])
        foot = tidy(foot.buffer(GROW, 4).intersection(allreg))
        if not foot.is_empty:
            slabs.append(prism_y(foot, P.YF + lo, P.YF + lev))
        lo = lev
    full_relief = union(slabs)
    full = to_world(clean(union([shell_solid, full_relief])))
    return dict(parts=parts, full=full, outline=outline, n_pages=n_pages, layers=layers, art=art2d, R=R)
