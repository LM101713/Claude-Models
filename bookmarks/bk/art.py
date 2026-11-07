"""BK-01 BOOKMARKS: the front-cover artwork as 2D shapes (shapely), in front-plane
coordinates (x across the cover, z up the cover, millimetres).

    lettering()  -> 'Bookmarks' in Bubblegum Sans (SIL OFL), thickened and hand-tilted
    nameplate()  -> the raised label the lettering sits on
    meadow()     -> dict of relief layers: ground, foliage, veins, petals, centres

The meadow follows the reference: a low rounded mound, a few tall stems with open
flower heads, a cup flower, buds and two flower spikes, long lance leaves and grass.
Every feature is sized for a 0.4 mm nozzle: strokes >= 1.0 mm, gaps >= 0.7 mm,
coloured islands >= 2.6 mm across.
"""

import math
import os

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from . import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "fonts", "BubblegumSans-Regular.ttf")
RES = 24  # arc resolution for buffers


# =====================================================================================
# lettering
# =====================================================================================


def _flatten_glyph(glyph_set, name, steps=10):
    """Glyph outline -> list of closed point lists (quadratic/cubic curves flattened)."""
    from fontTools.pens.recordingPen import RecordingPen

    pen = RecordingPen()
    glyph_set[name].draw(pen)
    contours, cur, start = [], [], None

    def q(p0, p1, p2):
        t = np.linspace(0, 1, steps + 1)[1:, None]
        return list(map(tuple, (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2))

    def c(p0, p1, p2, p3):
        t = np.linspace(0, 1, steps + 1)[1:, None]
        return list(map(tuple, (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3))

    for op, args in pen.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op == "qCurveTo":
            pts = [np.array(cur[-1], float)] + [np.array(a, float) for a in args]
            # implied on-curve points between consecutive off-curve points (TrueType)
            offs, on_end = pts[1:-1], pts[-1]
            p0 = pts[0]
            for i, off in enumerate(offs):
                nxt = on_end if i == len(offs) - 1 else 0.5 * (off + offs[i + 1])
                cur += q(p0, off, nxt)
                p0 = nxt
        elif op == "curveTo":
            p0 = np.array(cur[-1], float)
            a, b, e = (np.array(x, float) for x in args)
            cur += c(p0, a, b, e)
        elif op in ("closePath", "endPath"):
            if len(cur) >= 3:
                contours.append(cur)
            cur = []
    return contours


def _glyph_polygon(contours):
    """Even-odd assembly of contours into polygons-with-holes."""
    polys = [Polygon(c).buffer(0) for c in contours]
    polys = [p for p in polys if p.area > 1e-6]
    polys.sort(key=lambda p: -p.area)
    shape = Polygon()
    for p in polys:
        # a contour inside an odd number of others is a hole
        depth = sum(1 for o in polys if o is not p and o.area > p.area and o.contains(p.representative_point()))
        shape = shape.difference(p) if depth % 2 else shape.union(p)
    return shape


def lettering():
    """'Bookmarks', centred on the nameplate, returned with per-letter list."""
    from fontTools.ttLib import TTFont

    font = TTFont(FONT)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    kern = {}
    letters, pen_x = [], 0.0
    for i, ch in enumerate(P.TEXT):
        gname = cmap[ord(ch)]
        shape = _glyph_polygon(_flatten_glyph(gs, gname))
        adv = hmtx[gname][0]
        if not shape.is_empty:
            cx = shape.centroid.x
            shape = affinity.rotate(shape, P.TEXT_TILT[i], origin=(cx, 0))
            shape = affinity.translate(shape, pen_x, P.TEXT_BOUNCE[i] * 1000 / 13.6)
            letters.append(shape)
        pen_x += adv + kern.get(ch, 0)
    allg = unary_union(letters)
    x0, z0, x1, z1 = allg.bounds
    s = min(P.TEXT_MAX_W / (x1 - x0), P.TEXT_MAX_H / (z1 - z0))
    pz0, pz1 = P.PLATE_Z0, P.PLATE_Z1
    out = []
    for g in letters:
        g = affinity.translate(g, -(x0 + x1) / 2, -(z0 + z1) / 2)
        g = affinity.scale(g, s, s, origin=(0, 0))
        g = affinity.translate(g, P.ART_CX, 0.5 * (pz0 + pz1))
        g = _simp(g.buffer(P.TEXT_GROW, RES))
        out.append(g)
    return unary_union(out), out


def nameplate():
    r = P.PLATE_R
    x0, x1 = P.ART_CX - P.PLATE_W / 2, P.ART_CX + P.PLATE_W / 2
    return _simp(box(x0 + r, P.PLATE_Z0 + r, x1 - r, P.PLATE_Z1 - r).buffer(r, RES))


# =====================================================================================
# meadow primitives
# =====================================================================================


def bezier(p0, p1, p2, p3=None, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.array(p, float) for p in (p0, p1, p2))
    if p3 is None:
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    p3 = np.array(p3, float)
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def stroke(pts, w0, w1=None):
    """Tapered stroke along a polyline: width w0 at the start, w1 at the end."""
    w1 = w0 if w1 is None else w1
    pts = np.asarray(pts)
    parts = []
    for i in range(len(pts) - 1):
        f = i / max(1, len(pts) - 2)
        w = w0 + (w1 - w0) * f
        parts.append(LineString([pts[i], pts[i + 1]]).buffer(w / 2, RES // 2))
    return unary_union(parts)


def leaf(base, tip, width, bend=0.0, n=30):
    """Lance leaf from base to tip, max width at ~35 % of the length; bend curves it."""
    base, tip = np.array(base, float), np.array(tip, float)
    d = tip - base
    L = np.linalg.norm(d)
    u = d / L
    nrm = np.array([-u[1], u[0]])
    t = np.linspace(0, 1, n)
    half = width / 2 * np.sin(np.pi * t ** 0.75) ** 1.1
    spine = base[None] + t[:, None] * d[None] + (bend * L * np.sin(np.pi * t))[:, None] * nrm[None]
    left = spine + half[:, None] * nrm[None]
    right = spine - half[:, None] * nrm[None]
    poly = Polygon(np.vstack([left, right[::-1]])).buffer(0)
    vein = LineString(spine[2:-4])
    return poly, vein


def petal(cx, cz, ang, r0, r1, w, notch=False):
    """One petal from radius r0 to r1 at angle ang (deg), max width w."""
    L = r1 - r0
    t = np.linspace(0, 1, 28)
    half = w / 2 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.85) ** 0.8
    half[-1] = 0
    xs = r0 + t * L
    pts = np.vstack([np.c_[xs, half], np.c_[xs[::-1], -half[::-1]]])
    p = Polygon(pts).buffer(0)
    if notch:
        p = p.difference(Polygon([(r1 + 0.2, 0), (r1 - 0.9, 0.45), (r1 - 0.9, -0.45)]).buffer(0.08))
        p = p.buffer(0.1, RES).buffer(-0.1, RES)
    p = affinity.rotate(p, ang, origin=(0, 0))
    return affinity.translate(p, cx, cz)


def flower(cx, cz, n, r_out, w, rc, rot=0.0, notch=False, gap_r=None):
    """Radial flower: n petals around a centre disc of radius rc."""
    r0 = rc * 0.55
    petals = [petal(cx, cz, rot + k * 360 / n, r0, r_out, w, notch) for k in range(n)]
    pet = unary_union(petals)
    centre = Point(cx, cz).buffer(rc, RES)
    return pet.difference(centre), centre


def blossom(cx, cz, r, rc, rot=0.0):
    """Five round petals (forget-me-not / primrose), small centre."""
    petals = [Point(cx + 0.58 * r * math.cos(math.radians(rot + 72 * k)),
                    cz + 0.58 * r * math.sin(math.radians(rot + 72 * k))).buffer(0.46 * r, RES)
              for k in range(5)]
    # separate the petals with radial cuts so they read individually
    cuts = [LineString([(cx, cz), (cx + 1.4 * r * math.cos(math.radians(rot + 36 + 72 * k)),
                                   cz + 1.4 * r * math.sin(math.radians(rot + 36 + 72 * k)))]).buffer(0.36)
            for k in range(5)]
    pet = unary_union(petals).difference(unary_union(cuts))
    centre = Point(cx, cz).buffer(rc, RES)
    return pet.difference(centre), centre


def cup(cx, cz, w, h, tilt=0.0):
    """Tulip: a rounded cup with three pointed petal tips, base at (cx, cz).
    Returns (silhouette, petal division lines). The lines are cut back in relief."""
    xl, xr = -w / 2, w / 2
    right = bezier((0, 0), (xr * 1.05, 0.05 * h), (xr * 1.02, 0.62 * h), (xr * 0.80, h * 0.96), n=30)
    notch_r = bezier((xr * 0.80, h * 0.96), (xr * 0.55, 0.72 * h), (xr * 0.30, 0.72 * h), (xr * 0.08, h), n=16)
    notch_l = bezier((-xr * 0.08, h), (xl * 0.30, 0.72 * h), (xl * 0.55, 0.72 * h), (xl * 0.80, h * 0.96), n=16)
    left = bezier((xl * 0.80, h * 0.96), (xl * 1.02, 0.62 * h), (xl * 1.05, 0.05 * h), (0, 0), n=30)
    tipc = np.array([[0, h * 1.06]])
    shape = Polygon(np.vstack([right, notch_r, tipc, notch_l, left])).buffer(0).buffer(0.15, RES).buffer(-0.15, RES)
    lines = unary_union([LineString(bezier((xl * 0.42, 0.72 * h), (xl * 0.30, 0.35 * h), (0, 0.12 * h))),
                         LineString(bezier((xr * 0.42, 0.72 * h), (xr * 0.30, 0.35 * h), (0, 0.12 * h)))]).buffer(0.3, RES // 2)
    shape = affinity.translate(affinity.rotate(shape, tilt, origin=(0, 0)), cx, cz)
    lines = affinity.translate(affinity.rotate(lines, tilt, origin=(0, 0)), cx, cz)
    return shape, lines.intersection(shape.buffer(-0.5, RES))


def bud(cx, cz, r, ang=90.0):
    """Teardrop bud pointing along ang."""
    a = math.radians(ang)
    tip = (cx + 2.1 * r * math.cos(a), cz + 2.1 * r * math.sin(a))
    body = Point(cx, cz).buffer(r, RES)
    return unary_union([body, Polygon([(cx + r * math.cos(a + 1.35), cz + r * math.sin(a + 1.35)), tip,
                                       (cx + r * math.cos(a - 1.35), cz + r * math.sin(a - 1.35))])]).buffer(0)


def spike(base, top, n, fw, fh, lean=0.0):
    """Lavender spike: paired oval florets climbing a central rachis, one connected
    island so it prints as one colour region rather than n specks."""
    base, top = np.array(base, float), np.array(top, float)
    parts = [LineString([base, top]).buffer(0.6, RES // 2)]
    for k in range(n):
        f = k / max(1, n - 1)
        p = base + (top - base) * f
        s = 1.0 - 0.35 * f
        for side in (-1, 1):
            e = affinity.scale(Point(0, 0).buffer(1.0, RES), fw * s / 2, fh * s / 2)
            e = affinity.rotate(e, side * 42 + lean, origin=(0, 0))
            parts.append(affinity.translate(e, p[0] + side * 0.95 * s, p[1] + 0.35 * s))
    parts.append(affinity.scale(Point(*top).buffer(1.0, RES), 0.75, 1.15, origin=tuple(top)))
    return unary_union(parts)


def separate(shapes, gap):
    """Later shapes sit in front: clip earlier ones back by `gap` around later ones."""
    out = []
    for i, s in enumerate(shapes):
        later = unary_union(shapes[i + 1:]) if i + 1 < len(shapes) else Polygon()
        out.append(s.difference(later.buffer(gap, RES)) if not later.is_empty else s)
    return out


# =====================================================================================
# the meadow
# =====================================================================================


def meadow():
    cx = P.ART_CX
    z0 = P.ART_Z0

    # ---- ground: a long low mound with a softly scalloped top
    half_w = 27.0
    xs = np.linspace(cx - half_w, cx + half_w, 160)
    u = (xs - cx) / half_w
    top = z0 + 1.4 + 4.4 * np.clip(1 - u ** 2, 0, 1) ** 0.8 + 0.45 * np.sin((xs - cx) * 1.15)
    ground = Polygon(np.vstack([np.c_[xs, top], [[cx + half_w, z0], [cx - half_w, z0]]])).buffer(0)
    ground = ground.buffer(-1.0, RES).buffer(1.0, RES)

    def zb(x):                      # a stem's root: a little inside the mound's top edge
        return float(np.interp(x, xs, top)) - 1.4

    heads, centres, petal_lines = [], [], []

    def add(pc):
        heads.append(pc[0])
        centres.append(pc[1])

    A = (cx - 7.0, 41.6)     # big daisy
    B = (cx + 9.6, 43.4)     # cosmos
    C = (cx - 18.6, 35.2)    # left blossom
    Dd = (cx + 20.0, 35.6)   # right blossom
    F = (cx - 15.0, 45.2)    # small daisy, top left
    G = (cx + 19.4, 45.6)    # small daisy, top right
    E = (cx + 1.2, 26.8)     # tulip base
    add(flower(*A, n=9, r_out=5.6, w=2.1, rc=1.7, rot=8))
    add(flower(*B, n=7, r_out=5.0, w=2.7, rc=1.6, rot=-12))
    add(blossom(*C, r=4.1, rc=1.3, rot=14))
    add(blossom(*Dd, r=3.8, rc=1.3, rot=-6))
    add(flower(*F, n=8, r_out=3.4, w=1.5, rc=1.2, rot=0))
    add(flower(*G, n=8, r_out=3.3, w=1.5, rc=1.2, rot=12))
    tulip, tulip_lines = cup(*E, w=6.2, h=6.6, tilt=-3)
    petal_lines.append(tulip_lines)
    buds = [bud(cx - 1.4, 44.6, 1.05, 96), bud(cx + 26.0, 44.4, 1.0, 75)]
    spikes = [spike((cx - 24.9, 28.0), (cx - 24.3, 41.6), 6, 2.6, 1.5, lean=3)]

    # ---- stems (root -> head)
    S = []

    def stem(p0, c1, c2, p3, w0=1.25, w1=1.05):
        S.append(stroke(bezier(p0, c1, c2, p3), w0, w1))

    x = cx - 5.4; stem((x, zb(x)), (x - 0.6, 27), (cx - 8.6, 33), A)
    x = cx + 5.8; stem((x, zb(x)), (x + 0.6, 28), (cx + 9.6, 34), B)
    x = cx - 12.4; stem((x, zb(x)), (x - 1.4, 25), (cx - 17.6, 28), C, 1.2, 1.0)
    x = cx + 13.4; stem((x, zb(x)), (x + 1.8, 25), (cx + 19.2, 29), Dd, 1.2, 1.0)
    x = cx + 0.3; stem((x, zb(x)), (x + 0.3, 20), (cx + 1.1, 23), (E[0], E[1] + 0.8), 1.25, 1.1)
    x = cx - 22.6; stem((x, zb(x)), (x - 1.0, 19), (cx - 25.0, 23), (cx - 25.0, 27.5), 1.15, 1.0)
    # branches: bud and small-daisy stems leave the main stems
    stem((cx - 7.4, 31.0), (cx - 10.0, 35), (cx - 13.0, 38.5), F, 1.05, 1.0)
    stem((cx + 8.4, 32.0), (cx + 13.0, 35.5), (cx + 17.0, 39.5), G, 1.05, 1.0)
    stem((cx + 0.9, 33.0), (cx + 0.2, 37.5), (cx - 0.4, 40.0), (cx - 1.3, 43.0), 1.05, 1.0)
    stem((cx + 21.0, 30.0), (cx + 23.5, 34), (cx + 25.2, 38.5), (cx + 25.8, 42.6), 1.05, 1.0)
    stems = unary_union(S)

    # ---- leaves (base, tip, width, bend)
    L = [((cx - 9.5, zb(cx - 9.5) + 0.4), (cx - 16.6, 26.2), 3.3, -0.12),
         ((cx - 3.6, zb(cx - 3.6) + 0.4), (cx - 2.0, 25.6), 2.6, 0.10),
         ((cx + 4.0, zb(cx + 4.0) + 0.4), (cx + 10.8, 24.4), 3.0, 0.12),
         ((cx + 10.5, zb(cx + 10.5) + 0.4), (cx + 18.0, 25.6), 3.0, 0.14),
         ((cx - 18.0, zb(cx - 18.0) + 0.4), (cx - 21.0, 26.2), 2.4, -0.10),
         ((cx + 18.6, zb(cx + 18.6) + 0.4), (cx + 23.6, 24.4), 2.4, 0.12),
         ((cx - 6.4, 28.8), (cx - 2.4, 33.4), 2.2, 0.15),
         ((cx + 6.6, 28.6), (cx + 3.2, 32.6), 2.0, -0.15),
         ((cx - 14.2, 25.4), (cx - 10.6, 30.0), 1.9, 0.12)]
    leaves, veins = [], []
    for b, t, w, bend in L:
        lf, vn = leaf(b, t, w, bend)
        leaves.append(lf)
        veins.append(vn)

    # ---- grass tufts along the mound
    grass = []
    for gx, h, lean in [(-21.0, 3.6, -0.8), (-15.6, 4.6, -0.9), (-14.8, 3.6, 0.6), (-1.0, 4.2, -0.6),
                        (2.4, 4.6, 0.7), (8.4, 4.0, 0.5), (15.8, 4.6, -0.5), (16.8, 3.4, 0.8), (23.6, 3.6, 0.7)]:
        x0 = cx + gx
        grass.append(stroke(bezier((x0, zb(x0)), (x0 + lean * 0.4, zb(x0) + h * 0.6), (x0 + lean, zb(x0) + h)), 1.15, 0.95))

    # ---- assemble, in front-to-back order: centres > petals > foliage > ground
    # simplify each group once (12 micron tolerance, far below a 0.4 mm nozzle) BEFORE the
    # region differences, so neighbouring regions keep identical shared boundaries
    petals_all = _simp(unary_union(heads + [tulip] + buds + spikes))
    centres_all = _simp(unary_union(centres))
    ground = _simp(ground)
    # stems stop at the flower's silhouette (closed, so nothing peeks through petal gaps)
    heads_closed = petals_all.union(centres_all).buffer(0.8, RES).buffer(-0.8, RES)
    foliage = _simp(unary_union([stems] + leaves + grass)).difference(heads_closed)
    vein_lines = _simp(unary_union([v.buffer(0.32, RES // 2) for v in veins]))
    veins = vein_lines.intersection(unary_union(leaves).buffer(-0.45, RES)).difference(stems.buffer(0.2))
    ground = ground.difference(foliage).difference(petals_all).difference(centres_all)
    petals = petals_all.difference(centres_all)
    plines = _simp(unary_union(petal_lines)).intersection(petals)

    return dict(ground=_clean(ground), foliage=_clean(foliage, 1.5), veins=_clean(veins),
                petals=_clean(petals), petal_lines=_clean(plines), centres=_clean(centres_all))


def _simp(g, tol=0.012):
    return g.simplify(tol, preserve_topology=True).buffer(0)


def _clean(g, min_area=0.15):
    g = g.buffer(0)
    if isinstance(g, Polygon):
        g = MultiPolygon([g]) if not g.is_empty else MultiPolygon()
    keep = [p for p in getattr(g, "geoms", []) if p.area >= min_area]
    return unary_union(keep) if keep else Polygon()
