"""
2D profile helpers (shapely, in the XZ plane) and the band-stack -> solid builder (manifold3d).

A part is a list of BANDS: (y0, y1, polygon_xz). Every band is the polygon extruded from y0 to
y1. This matches the mechanism (planar, layered along y) and also how the on-side parts print.
"""

import math

import numpy as np
import manifold3d as mf
from shapely import affinity
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union

SEG = 10          # quarter-circle segments for buffers (shapely quad_segs)


def circ(c, r, n=64):
    return Point(c).buffer(r, quad_segs=max(8, n // 4))


def teardrop(c, r, up, cap=1.05):
    """Hole for an axis that prints horizontally: a circle with a 45 deg roof towards `up`
    (2D unit vector, the print-up direction seen in XZ), cut flat at cap*r."""
    ux, uy = up
    base = circ(c, r)
    k = r * math.sqrt(2)
    # square rotated 45 deg whose corner points up: the roof
    sq = Polygon([(0, k), (k / 2, k / 2), (0, 0), (-k / 2, k / 2)])
    roof = sq.intersection(box(-r, -r, r, cap * r))
    ang = math.degrees(math.atan2(uy, ux)) - 90.0
    roof = affinity.translate(affinity.rotate(roof, ang, origin=(0, 0)), c[0], c[1])
    return unary_union([base, roof])


def crush_hole(c, r_pin, clear, rib, up=None, n_ribs=3):
    """Press-fit hole: radius r_pin + clear with n_ribs half-round ribs that reach rib inside
    r_pin (radial interference). The ribs crush on assembly, which makes the fit tolerant."""
    r_h = r_pin + clear
    hole = teardrop(c, r_h, up) if up is not None else circ(c, r_h)
    rr = 0.45                               # rib radius
    depth = clear + rib                     # how far a rib stands proud of the hole wall
    a0 = math.atan2(up[1], up[0]) + math.pi if up is not None else math.pi / 2
    ribs = []
    for i in range(n_ribs):
        a = a0 + 2 * math.pi * i / n_ribs
        d = r_h - depth + rr
        ribs.append(circ((c[0] + d * math.cos(a), c[1] + d * math.sin(a)), rr, 32))
    return hole.difference(unary_union(ribs))


def rounded(poly, r_convex=0.0, r_concave=0.0):
    p = poly
    if r_concave > 0:
        p = p.buffer(r_concave, quad_segs=SEG).buffer(-r_concave, quad_segs=SEG)
    if r_convex > 0:
        p = p.buffer(-r_convex, quad_segs=SEG).buffer(r_convex, quad_segs=SEG)
    return p


def hull(*geoms):
    return unary_union(geoms).convex_hull


def polyline_band(xs, top, bot):
    """Polygon between two curves z = top(x) and z = bot(x) sampled at xs."""
    pts = [(x, top(x)) for x in xs] + [(x, bot(x)) for x in reversed(xs)]
    return Polygon(pts).buffer(0)


def rot2(g, deg, origin):
    return affinity.rotate(g, deg, origin=origin)


def place2(g, ang_rad, pivot, new_pivot=None):
    """Rotate g by ang (radians, CCW) about pivot, then move pivot to new_pivot."""
    out = affinity.rotate(g, math.degrees(ang_rad), origin=pivot)
    if new_pivot is not None:
        out = affinity.translate(out, new_pivot[0] - pivot[0], new_pivot[1] - pivot[1])
    return out


def as_polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


# =====================================================================================
# Bands -> solid
# =====================================================================================


def _cs(poly, tol=0.015):
    rings = []
    poly = poly.simplify(tol, preserve_topology=True) if tol else poly
    for p in as_polys(poly):
        if p.area < 1e-4:
            continue
        rings.append(np.array(p.exterior.coords)[:-1])
        for h in p.interiors:
            rings.append(np.array(h.coords)[:-1])
    if not rings:
        return None
    return mf.CrossSection(rings, mf.FillRule.EvenOdd)


def band_solid(y0, y1, poly):
    cs = _cs(poly)
    if cs is None or y1 - y0 < 1e-6:
        return None
    m = mf.Manifold.extrude(cs, y1 - y0)
    # local (X, Y, Z) -> world (x = X, y = y1 - Z, z = Y): a proper rotation
    return m.transform([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]])


def chamfer_bands(bands, c=0.6, steps=3):
    """Stepped chamfer (like printed layers) on the part's two outer y faces."""
    ymin = min(b[0] for b in bands)
    ymax = max(b[1] for b in bands)
    out = []
    d = c / steps
    for y0, y1, poly in bands:
        lo, hi = y0, y1
        pieces = []
        if abs(y1 - ymax) < 1e-6 and y1 - y0 > c + 0.2:
            for k in range(steps):
                a, b = y1 - c + k * d, y1 - c + (k + 1) * d
                pieces.append((a, b, poly.buffer(-(k + 1) * d, quad_segs=SEG)))
            hi = y1 - c
        if abs(y0 - ymin) < 1e-6 and y1 - y0 > c + 0.2:
            for k in range(steps):
                a, b = y0 + c - (k + 1) * d, y0 + c - k * d
                pieces.append((a, b, poly.buffer(-(k + 1) * d, quad_segs=SEG)))
            lo = y0 + c
        pieces.append((lo, hi, poly))
        out += pieces
    return out


def solid(bands, chamfer=0.6, eps=0.002):
    bs = chamfer_bands(bands, chamfer) if chamfer else bands
    ymin = min(b[0] for b in bs)
    ymax = max(b[1] for b in bs)
    # bands overlap their neighbours by eps so the union fuses them (faces that only touch
    # are left as separate shells); the part's two outer faces stay exact
    parts = [band_solid(y0 - (eps if y0 > ymin + 1e-9 else 0), y1 + (eps if y1 < ymax - 1e-9 else 0), p)
             for y0, y1, p in bs]
    parts = [p for p in parts if p is not None]
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)


def mirror_bands(half):
    """Bands given for y >= 0 -> the symmetric set (a centre band starting at 0 is joined)."""
    out = []
    for y0, y1, p in half:
        if y0 == 0:
            out.append((-y1, y1, p))
        else:
            out.append((y0, y1, p))
            out.append((-y1, -y0, p))
    return out


def mesh_arrays(m):
    me = m.to_mesh()
    v = np.array(me.vert_properties)[:, :3]
    t = np.array(me.tri_verts)
    return v, t


def text_polys(text, size, font_path, center=(0, 0), spacing=0.0):
    """Glyph outlines as shapely polygons (mm), centred on `center`, reading along +x."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    fp = FontProperties(fname=font_path)
    tp = TextPath((0, 0), text, size=size, prop=fp)
    polys = []
    for poly in tp.to_polygons(closed_only=True):
        if len(poly) >= 3:
            polys.append(Polygon(poly).buffer(0))
    # even-odd assembly: holes in letters
    polys.sort(key=lambda p: -p.area)
    shape = Polygon()
    for p in polys:
        if shape.contains(p.representative_point()) and shape.intersects(p):
            shape = shape.difference(p)
        else:
            shape = shape.union(p)
    b = shape.bounds
    return affinity.translate(shape, center[0] - (b[0] + b[2]) / 2, center[1] - (b[1] + b[3]) / 2)


def area_signed(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2
