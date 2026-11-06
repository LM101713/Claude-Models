"""
HF-04 HOLDFAST geometry: builds every part as an exact manifold solid (manifold3d).

Construction convention for the base: profiles are drawn in the use-frame XZ plane and
extruded along +Y (out of the wall). `xz_to_use` turns an extrusion made in a scratch frame
into the use frame with a proper rotation (no mirroring), so the STL in print orientation is
the same handed part as the one in the assembly.
"""

import math

import numpy as np
import shapely
from manifold3d import CrossSection, FillRule, Manifold, Mesh, triangulate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from .params import D, P, centre

# =====================================================================================
# low-level helpers
# =====================================================================================


def signed_area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def ccw(r):
    r = np.asarray(r, float)
    if np.allclose(r[0], r[-1]):
        r = r[:-1]
    return r if signed_area(r) > 0 else r[::-1]


def resample(ring, step=0.35):
    """Uniform arc-length resampling of a closed ring (keeps sharp features to ~step)."""
    r = np.vstack([ring, ring[:1]])
    seg = np.linalg.norm(np.diff(r, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    n = max(16, int(math.ceil(L[-1] / step)))
    t = np.linspace(0, L[-1], n, endpoint=False)
    x = np.interp(t, L, r[:, 0])
    y = np.interp(t, L, r[:, 1])
    return np.column_stack([x, y])


def vertex_normals(r):
    """Outward unit normals of a CCW ring (averaged edge normals)."""
    e = np.roll(r, -1, axis=0) - r
    en = np.column_stack([e[:, 1], -e[:, 0]])
    en /= np.linalg.norm(en, axis=1)[:, None] + 1e-12
    vn = en + np.roll(en, 1, axis=0)
    vn /= np.linalg.norm(vn, axis=1)[:, None] + 1e-12
    # scale so that the offset of a straight edge stays exact at corners
    cos_half = np.clip(np.sum(vn * en, axis=1), 0.3, 1.0)
    return vn / cos_half[:, None]


def loft(rings, heights):
    """Closed solid through rings (all CCW, same vertex count) stacked at the given z."""
    n = len(rings[0])
    verts = np.vstack([np.column_stack([r, np.full(n, h)]) for r, h in zip(rings, heights)])
    tris = []
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            tris.append((a + i, a + j, b + j))
            tris.append((a + i, b + j, b + i))
    cap = triangulate([rings[0]])
    for t in cap:
        tris.append((int(t[0]), int(t[2]), int(t[1])))  # bottom faces down
    top = (len(rings) - 1) * n
    cap = triangulate([rings[-1]])
    for t in cap:
        tris.append((top + int(t[0]), top + int(t[1]), top + int(t[2])))
    m = Manifold(Mesh(vert_properties=np.asarray(verts, np.float32), tri_verts=np.asarray(tris, np.uint32)))
    if m.status().name != "NoError":
        raise RuntimeError(f"loft failed: {m.status()}")
    return m


def chamfered_prism(poly, z0, z1, c_bot=0.0, c_top=0.0, step=0.35):
    """Prism of a shapely polygon (no holes) with 45-degree chamfers on its two end loops."""
    ring = ccw(resample(ccw(np.array(poly.exterior.coords)), step))
    nrm = vertex_normals(ring)
    rings, hs = [], []
    if c_bot > 0:
        rings += [ring - c_bot * nrm, ring]
        hs += [z0, z0 + c_bot]
    else:
        rings += [ring]
        hs += [z0]
    if c_top > 0:
        rings += [ring, ring - c_top * nrm]
        hs += [z1 - c_top, z1]
    else:
        rings += [ring]
        hs += [z1]
    return loft(rings, hs)


def xz_to_use(m):
    """Scratch frame (u, v, w) with v = -Z, w = Y  ->  use frame.  Rx(-90): (x,y,z)->(x,z,-y)."""
    return m.rotate([-90.0, 0.0, 0.0])


def XZ(poly):
    """Map a shapely polygon drawn in use-frame (X, Z) to scratch-frame (X, -Z) for extrusion."""
    return shapely.affinity.scale(poly, xfact=1.0, yfact=-1.0, origin=(0, 0))


def stadium_ring(a, b, r, n_cap=48):
    """CCW ring of a stadium (capsule) around segment a-b, radius r, in a 2D plane."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    ang = math.atan2(d[1], d[0])
    pts = []
    for k in range(n_cap + 1):  # cap around b
        t = ang - math.pi / 2 + math.pi * k / n_cap
        pts.append(b + r * np.array([math.cos(t), math.sin(t)]))
    for k in range(n_cap + 1):  # cap around a
        t = ang + math.pi / 2 + math.pi * k / n_cap
        pts.append(a + r * np.array([math.cos(t), math.sin(t)]))
    return np.array(pts)


def circle_ring(c, r, n=P.SEG):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.column_stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)])


def text_polys(s, size, family="DejaVu Sans", weight="bold"):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    tp = TextPath((0, 0), s, size=size, prop=FontProperties(family=family, weight=weight))
    polys = [np.array(p) for p in tp.to_polygons() if len(p) > 2]
    allp = np.vstack(polys)
    cx = (allp[:, 0].min() + allp[:, 0].max()) / 2
    cy = (allp[:, 1].min() + allp[:, 1].max()) / 2
    return [p - [cx, cy] for p in polys]


def text_solid(s, size, z0, z1):
    cs = CrossSection([p.tolist() for p in text_polys(s, size)], fillrule=FillRule.EvenOdd)
    return cs.extrude(z1 - z0).translate([0, 0, z0])


# =====================================================================================
# 2D layout of the base (use-frame X, Z)
# =====================================================================================


def ramp_halfplane_left(big=400.0):
    """Points on the pocket side of the left ramp line (contains the roller)."""
    p0, u, n = D.P0, D.u, D.n
    a = p0 - big * u
    b = p0 + big * u
    return Polygon([a, b, b + big * n, a + big * n])


def outer_edge_left():
    """Outer edge of the left housing: ramp line moved W_OUTER away from the pocket."""
    return D.P0 - P.W_OUTER * D.n, D.u


def base_outline():
    """Outline of the whole base: a V-shaped trapezoid (outer edges parallel to the ramps)."""
    p, u = outer_edge_left()
    big = 400.0
    nl = -D.n  # outward of the left outer edge
    left_cut = Polygon([p - big * u, p + big * u, p + big * u + big * nl, p - big * u + big * nl])
    right_cut = shapely.affinity.scale(left_cut, xfact=-1, yfact=1, origin=(0, 0))
    slab = box(-200, D.z_bot, 200, D.z_top)
    o = slab.difference(left_cut).difference(right_cut)
    return o.buffer(-P.R_OUTLINE, join_style="round", quad_segs=24).buffer(
        P.R_OUTLINE, join_style="round", quad_segs=24
    )


def pocket_left(extra=0.0):
    """Region swept by the left roller (plus clearance), cut off at the ramp line."""
    a = centre(0.0)
    b = centre(D.s_key)
    st = Polygon(stadium_ring(a, b, P.R_ROLL + P.C_POCKET + extra, 64))
    return st.intersection(ramp_halfplane_left())


def round_poly(poly, r_cvx, r_ccv):
    poly = poly.buffer(r_ccv, join_style="round", quad_segs=16).buffer(-r_ccv, join_style="round", quad_segs=16)
    poly = poly.buffer(-r_cvx, join_style="round", quad_segs=16).buffer(r_cvx, join_style="round", quad_segs=16)
    return poly


def mirror_x(poly):
    return shapely.affinity.scale(poly, xfact=-1, yfact=1, origin=(0, 0))


# =====================================================================================
# parts
# =====================================================================================


def slot_cutter(s_lo, s_hi, keyhole_s, frame_offset=(0.0, 0.0)):
    """Keyhole T-slot for the roller stub along the roller-centre path (scratch frame).

    The stub stops at s_lo and s_hi (neck against the slot ends); keyhole at keyhole_s.
    """
    ox, oz = frame_offset
    e = P.LIP_SLOT_HALF - P.NECK_R  # stop offset so the neck touches the end exactly at s_lo/s_hi

    def pt(s):
        c = centre(s)
        return np.array([c[0] - ox, -(c[1] - oz)])  # scratch frame (X, -Z)

    a, b = pt(s_lo - e), pt(s_hi + e)
    halfs = [P.CAV_HALF, P.CAV_HALF, P.LIP_SLOT_HALF, P.LIP_SLOT_HALF, P.LIP_SLOT_HALF + P.SLOT_LEAD + 0.05]
    ys = [P.Y_CAV_FLOOR, P.Y_LIP_UNDER - (P.CAV_HALF - P.LIP_SLOT_HALF), P.Y_LIP_UNDER,
          P.BACK_T - P.SLOT_LEAD, P.BACK_T + 0.05]
    rings = [stadium_ring(a, b, h, 40) for h in halfs]
    slot = loft(rings, ys)
    k = pt(keyhole_s)
    kr = [circle_ring(k, P.KEY_R), circle_ring(k, P.KEY_R), circle_ring(k, P.KEY_R + P.SLOT_LEAD + 0.05)]
    key = loft(kr, [P.Y_CAV_FLOOR, P.BACK_T - P.SLOT_LEAD, P.BACK_T + 0.05])
    return slot + key


def screw_cutter(x, z):
    """Through hole and 90-degree countersink opening toward the front (scratch frame)."""
    c = (x, -z)
    r_h, r_c = P.SCREW_HOLE_D / 2, P.SCREW_CSK_D / 2
    y_cone = P.BACK_T - (r_c - r_h)
    rings = [circle_ring(c, r_h, 64), circle_ring(c, r_h, 64), circle_ring(c, r_c, 64), circle_ring(c, r_c, 64)]
    return loft(rings, [-1.0, y_cone, P.BACK_T, P.BACK_T + 3.0])


def screw_positions():
    return [(0.0, D.z_top - P.SCREW_INSET), (0.0, D.z_bot + P.SCREW_INSET)]


def cavity_outline():
    """Everything removed in front of the back plate: both pockets and the handle channel,
    as one polygon (so the base is one prism minus one cutter: no coincident faces)."""
    ch = box(-P.X_CH, D.z_bot - 30, P.X_CH, D.z_top + 30)
    pl = pocket_left()
    cut = unary_union([pl, mirror_x(pl), ch])
    # cutter convex corners = housing concave corners; cutter concave corners = housing tips
    return round_poly(cut, P.R_CONCAVE, P.R_CONVEX * 0.5)


def housing_left():
    """Left housing (for drawings): base outline minus the cavity, left of the channel."""
    h = base_outline().difference(cavity_outline()).intersection(box(-200, -200, 0, 200))
    if h.geom_type != "Polygon":
        h = max(h.geoms, key=lambda g: g.area)
    return h


def build_base(engrave=True):
    """The wall plate with the two housings, ramps and keyhole slots (use frame)."""
    body = chamfered_prism(XZ(base_outline()), 0.0, P.Y_FRONT, P.CH_BACK, P.CH_FRONT)
    ring = ccw(resample(ccw(np.array(XZ(cavity_outline()).exterior.coords)), 0.35))
    nrm = vertex_normals(ring)
    c = P.CH_FRONT
    cav = loft([ring, ring, ring + (c + 0.02) * nrm, ring + (c + 0.02) * nrm],
               [P.BACK_T, P.Y_FRONT - c, P.Y_FRONT + 0.02, P.Y_FRONT + 3.0])
    cutters = [cav]
    sl = slot_cutter(0.0, D.s_key, D.s_key)
    cutters += [sl, sl.mirror([1, 0, 0])]
    cutters += [screw_cutter(x, z) for x, z in screw_positions()]
    if engrave:
        # wall-side marking, reads correctly from behind the part (0.4 deep)
        for txt, size, z in (("ODD LAYER", 4.2, 4.0), ("HF-04  HOLDFAST", 3.2, -1.6), ("19-32 mm", 3.2, -6.4)):
            t = text_solid(txt, size, -0.1, 0.4)  # glyphs in (X, Y) of the scratch frame
            # scratch frame is (X, -Z); viewed from behind (from -Y) +X is to the viewer's right,
            # so the glyphs keep X and flip their vertical axis
            t = t.mirror([0, 1, 0]).translate([0, -z, 0])
            cutters.append(t)
    body = body - Manifold.batch_boolean(cutters, _op("Add"))
    return xz_to_use(body)


def _op(name):
    from manifold3d import OpType

    return getattr(OpType, name)


# ---- roller -------------------------------------------------------------------------------------


def roller_profile_rings(grip=False):
    n = P.GRIP_N * 12 if grip else P.SEG
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    R = P.R_ROLL
    if grip:
        rr = R - P.GRIP_DEPTH * 0.5 * (1 - np.cos(P.GRIP_N * t))
    else:
        rr = np.full(n, R)

    def ring(r):
        return np.column_stack([r * np.cos(t), r * np.sin(t)])

    cf, cb, T = P.ROLL_CH_FRONT, P.ROLL_CH_BACK, P.T_ROLL
    rings = [ring(np.full(n, R - cf)), ring(rr), ring(rr), ring(np.full(n, R - cb))]
    hs = [0.0, cf, T - cb, T]
    return rings, hs


def stub_profile(loose=False):
    """(r, z) outline of the stub in the roller print frame (z up from the front face)."""
    T = P.T_ROLL
    y_rb = P.BACK_T + P.G_BACK

    def z_of(y):
        return y_rb + T - y

    dr = P.LOOSE_NECK_DR if loose else 0.0
    dy = -P.LOOSE_AXIAL if loose else 0.0
    rn, rh = P.NECK_R + dr, P.HEAD_R + dr
    zc0 = z_of(P.Y_CONE0 + dy)
    zc1 = zc0 + (rh - rn)  # 45-degree cone
    ze = z_of(P.Y_HEAD_END + dy)
    return [(0, T - 0.6), (rn, T - 0.6), (rn, zc0), (rh, zc1), (rh, ze - P.HEAD_CH), (rh - P.HEAD_CH, ze), (0, ze)]


def build_roller(grip=False, loose=False):
    """Roller in PRINT orientation: front face on the bed (z = 0), stub on top."""
    rings, hs = roller_profile_rings(grip)
    body = loft(rings, hs)
    prof = stub_profile(loose)
    stub = CrossSection([[list(p) for p in prof]]).revolve(P.SEG)
    m = body + stub
    # index line on the front face: shows the roller turning as it rolls
    r0, r1 = P.INDEX_R
    w = P.INDEX_W
    groove = loft(
        [stadium_ring((0, r0), (0, r1), w / 2, 12)] * 2, [-0.1, P.INDEX_D]
    )
    return m - groove


def roller_to_use(m, s, side=-1):
    """Place a print-frame roller in the use frame at travel s on the left (-1) / right (+1)."""
    T = P.T_ROLL
    y_rb = P.BACK_T + P.G_BACK
    u = m.rotate([90.0, 0.0, 0.0]).translate([0, y_rb + T, 0])  # (x,y,z)->(x,-z,y); front face at Y=27.3
    ang = math.degrees(s / P.R_ROLL) * (-1.0 if side < 0 else 1.0)  # rolling without slip
    u = u.rotate([0.0, ang, 0.0])
    c = centre(s)
    return u.translate([c[0] if side < 0 else -c[0], 0, c[1]])


# ---- fit-test coupon ------------------------------------------------------------------------


def build_coupon(length=16.0):
    """A 7 mm slice of back plate holding the top 16 mm of the slot and the keyhole.

    Print it with one roller before the base: it tells you, in ten minutes, whether the stub
    drops in, slides and is held on your printer.
    """
    s_lo, s_hi = D.s_key - length, D.s_key
    mid = centre((s_lo + s_hi) / 2)
    a = centre(s_lo) - mid
    b = centre(s_hi) - mid
    outline = Polygon(stadium_ring(a, b, 10.0, 48))
    plate = chamfered_prism(XZ(outline), 0.0, P.BACK_T, P.CH_BACK, 0.6)
    cut = slot_cutter(s_lo, s_hi, s_hi, frame_offset=(mid[0], mid[1]))
    t = text_solid("FIT", 3.6, -0.1, 0.4).mirror([0, 1, 0])
    return xz_to_use(plate - cut - t), mid


# ---- dummy handle -------------------------------------------------------------------------------


def handle(dia, z0=-150.0, z1=150.0, gap=0.0):
    """A broom handle resting on the back plate, in the use frame."""
    r = dia / 2
    m = Manifold.cylinder(z1 - z0, r, r, 160).translate([0, P.BACK_T + r + gap, z0])
    return m


def rollers_on_handle(roller_print, dia, gap=0.0):
    """Both rollers at the travel that grips a handle of diameter dia (with optional gap)."""
    from .params import s_of_diameter

    s = s_of_diameter(dia + 2 * gap)
    return roller_to_use(roller_print, s, -1), roller_to_use(roller_print, s, +1), s


# =====================================================================================
# print-frame transforms
# =====================================================================================


def base_to_print(m):
    """Use frame -> print frame (wall side on the bed). Rx(+90): (x,y,z)->(x,-z,y)."""
    return m.rotate([90.0, 0.0, 0.0])


def to_bed(m):
    lo, hi = np.array(m.bounding_box()[:3]), np.array(m.bounding_box()[3:])
    return m.translate([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
