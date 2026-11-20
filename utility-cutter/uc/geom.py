"""
Odd Layer utility-cutter concept study: geometry helpers (manifold3d + shapely).

Design frame (mm): X along the tool, nose at x = 0, tail at +X.  Z up, with the blade's
cutting edge on z = 0 and its back on z = 18.  Y across the thickness.
Side profiles are drawn in XZ and given thickness along Y with rounded ("pillowed") edges.
"""

import math

import numpy as np
import shapely
from manifold3d import CrossSection, FillRule, Manifold, Mesh, triangulate
from shapely.geometry import LinearRing, Point, Polygon, box
from shapely.ops import unary_union

RAKE = math.radians(59.0)          # snap-line angle of an 18 mm blade, reused as a design angle
SEG = 10.0                         # nominal segment pitch along the blade (verify per brand)
BLADE_L, BLADE_H, BLADE_T = 100.0, 18.0, 0.5

# (a, b, c) -> (x, y, z) = (b, c, a): a proper rotation, profiles are passed in as (z, x)
_M_XZ = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float)
# (a, b, c) -> (x, y, z) = (c, a, b): extrude a YZ profile along X
_M_YZ = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)


# ----------------------------------------------------------------------------- 2D
def circle(x, z, r, n=96):
    return Point(x, z).buffer(r, quad_segs=n // 4)


def stadium(x0, x1, z, r):
    return unary_union([circle(x0, z, r), circle(x1, z, r), box(x0, z - r, x1, z + r)])


def round_corners(poly, r_convex=0.0, r_concave=0.0):
    if r_convex > 0:
        poly = poly.buffer(-r_convex, quad_segs=12).buffer(r_convex, quad_segs=12)
    if r_concave > 0:
        poly = poly.buffer(r_concave, quad_segs=12).buffer(-r_concave, quad_segs=12)
    return poly


def spline(points, per=14):
    """Open Catmull-Rom curve through the given points (end tangents from the end chords)."""
    p = np.asarray(points, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2])
    return [tuple(q) for q in out]


def raked_dx(h):
    return h / math.tan(RAKE)


# ----------------------------------------------------------------------------- lofting
def _ring(poly, n):
    ext = poly.exterior
    if not ext.is_ccw:
        ext = LinearRing(list(ext.coords)[::-1])
    L = ext.length
    c = poly.centroid
    s0 = ext.project(Point(c.x + 1e4, c.y + 3e3))
    t = (s0 + np.linspace(0, L, n, endpoint=False)) % L
    return shapely.get_coordinates(shapely.line_interpolate_point(ext, t))


def _loft(rings, heights):
    n = len(rings[0])
    verts = np.vstack([np.column_stack([r, np.full(n, h)]) for r, h in zip(rings, heights)])
    tris = []
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        i = np.arange(n)
        j = (i + 1) % n
        tris.append(np.column_stack([a + i, a + j, b + j]))
        tris.append(np.column_stack([a + i, b + j, b + i]))
    cap = np.asarray(triangulate([rings[0]]), int)
    tris.append(cap[:, ::-1])
    cap = np.asarray(triangulate([rings[-1]]), int)
    tris.append(cap + (len(rings) - 1) * n)
    m = Manifold(Mesh(vert_properties=np.asarray(verts, np.float32),
                      tri_verts=np.asarray(np.vstack(tris), np.uint32)))
    if m.status().name != "NoError":
        raise RuntimeError(f"loft failed: {m.status()}")
    return m


def _levels(h0, h1, e0, e1, steps, sign):
    """Edge-rounding schedule. e = (in-plane radius, depth) or a single radius; sign -1 rounds
    a solid's edges, +1 flares a cutter so the hole it cuts gets rounded rims."""
    def pair(e):
        return (e, e) if np.isscalar(e) else e
    (r0, d0), (r1, d1) = pair(e0), pair(e1)
    lv = []
    if d0 > 0:
        for a in np.linspace(0, math.pi / 2, steps + 1):
            lv.append((h0 + d0 * (1 - math.cos(a)), sign * r0 * (1 - math.sin(a))))
    else:
        lv.append((h0, 0.0))
    if d1 > 0:
        for a in np.linspace(math.pi / 2, 0, steps + 1):
            lv.append((h1 - d1 * (1 - math.cos(a)), sign * r1 * (1 - math.sin(a))))
    else:
        lv.append((h1, 0.0))
    out = [lv[0]]
    for h, o in lv[1:]:
        if h > out[-1][0] + 1e-6:
            out.append((h, o))
    return out


def _stack(poly, levels, step):
    n = max(48, int(poly.exterior.length / step))
    rings, hs = [], []
    for h, off in levels:
        p = poly if abs(off) < 1e-9 else poly.buffer(off, quad_segs=10)
        if p.geom_type == "MultiPolygon":
            p = max(p.geoms, key=lambda g: g.area)
        rings.append(_ring(Polygon(p.exterior), n))
        hs.append(h)
    return _loft(rings, hs)


def z_solid(poly_xy, z0, z1, e0=0.0, e1=0.0, steps=7, step=0.3, flare=False):
    lv = _levels(z0, z1, e0, e1, steps, +1 if flare else -1)
    if flare:
        lv = [(z0 - 2, lv[0][1])] + lv + [(z1 + 2, lv[-1][1])]
    return _stack(Polygon(poly_xy.exterior), lv, step)


def xz_solid(poly_xz, y0, y1, e0=0.0, e1=0.0, steps=7, step=0.3, flare=False):
    """Give an XZ profile thickness from y0 to y1; e0 / e1 round the y0 / y1 edge loops."""
    sw = Polygon([(z, x) for x, z in poly_xz.exterior.coords])
    lv = _levels(y0, y1, e0, e1, steps, +1 if flare else -1)
    if flare:
        lv = [(y0 - 2, lv[0][1])] + lv + [(y1 + 2, lv[-1][1])]
    return _stack(sw, lv, step).transform(_M_XZ)


def xz_prism(poly_xz, y0, y1):
    """Plain prism of an XZ polygon that may have holes."""
    polys = poly_xz.geoms if poly_xz.geom_type == "MultiPolygon" else [poly_xz]
    rings = []
    for p in polys:
        rings.append([(z, x) for x, z in p.exterior.coords[:-1]])
        for h in p.interiors:
            rings.append([(z, x) for x, z in h.coords[:-1]])
    cs = CrossSection(rings, FillRule.EvenOdd)
    return cs.extrude(y1 - y0).translate([0, 0, y0]).transform(_M_XZ)


def yz_prism(pts_yz, x0, x1):
    return CrossSection([pts_yz], FillRule.Positive).extrude(x1 - x0).translate([0, 0, x0]).transform(_M_YZ)


def cyl_y(x, z, r, y0, y1, n=96):
    return Manifold.cylinder(y1 - y0, r, r, n).translate([0, 0, y0]).transform(_M_XZ).translate([x, 0, z])


def cyl_z(x, y, r, z0, z1, n=64):
    return Manifold.cylinder(z1 - z0, r, r, n).translate([x, y, z0])


def cube(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(ms):
    return Manifold.batch_boolean(list(ms), __import__("manifold3d").OpType.Add)


def half_plane_raked(x_at_z0, side=+1, big=400.0):
    """XZ polygon on the +X (side=+1) or -X side of a 59-degree raked line through (x_at_z0, 0)."""
    dx = raked_dx(big)
    a, b = (x_at_z0 - dx, -big), (x_at_z0 + dx, big)
    far = side * 3 * big
    return Polygon([a, b, (b[0] + far, b[1]), (a[0] + far, a[1])])


# ----------------------------------------------------------------------------- shared parts
def blade(tip_x, y=0.0):
    """18 mm snap-off blade: 100 x 18 x 0.5, 59-degree segments, ground edge, tail hole."""
    dx = raked_dx(BLADE_H)
    out = Polygon([(tip_x, 0), (tip_x + BLADE_L, 0), (tip_x + BLADE_L, BLADE_H), (tip_x + dx, BLADE_H)])
    m = xz_prism(out, -BLADE_T / 2, BLADE_T / 2)
    t = BLADE_T / 2
    wedge = yz_prism([(0, 0), (t, 1.4), (t, BLADE_H + 1), (-t, BLADE_H + 1), (-t, 1.4)], tip_x - 1, tip_x + BLADE_L + 1)
    m = m ^ wedge
    for k in range(1, 8):                                   # score lines, one face only
        x = tip_x + k * SEG
        g = Polygon([(x - 0.17, 0), (x + 0.17, 0), (x + 0.17 + dx, BLADE_H), (x - 0.17 + dx, BLADE_H)])
        m = m - xz_prism(g, t - 0.1, t + 1)
    m = m - cyl_y(tip_x + BLADE_L - 7, BLADE_H / 2, 2.1, -1, 1, 32)
    return m.translate([0, y, 0])


def screw_head(x, z, y_face, sign=+1, r=2.6, depth=2.4):
    """Socket-head screw sunk into the face at y = y_face (sign = outward direction).
    Returns (counterbore cutter, head solid)."""
    ya, yb = sorted([y_face + sign * 1.0, y_face - sign * depth])
    bore = cyl_y(x, z, r + 0.3, ya, yb, 48)
    ya, yb = sorted([y_face - sign * 0.35, y_face - sign * (depth + 0.5)])
    head = cyl_y(x, z, r, ya, yb, 48)
    ya, yb = sorted([y_face + sign * 0.5, y_face - sign * 1.9])
    head = head - cyl_y(x, z, 1.45, ya, yb, 6)
    return bore, head


def fluted_wheel_xz(x, z, r, y0, y1, n_flutes, flute_r=0.9, edge=0.8):
    w = xz_solid(circle(x, z, r), y0, y1, edge, edge)
    cut = [cyl_y(x + (r + 0.25) * math.cos(a), z + (r + 0.25) * math.sin(a), flute_r, y0 - 1, y1 + 1, 16)
           for a in np.linspace(0, 2 * math.pi, n_flutes, endpoint=False)]
    return w - union(cut)


def perimeter_groove(poly_xz, y, w=0.3, d=0.4):
    """Parting-line groove around an XZ outline at the given y."""
    ring = poly_xz.difference(poly_xz.buffer(-d))
    return xz_prism(ring, y - w / 2, y + w / 2)


def bbox(m):
    b = m.bounding_box()
    return np.array(b[:3]), np.array(b[3:])
