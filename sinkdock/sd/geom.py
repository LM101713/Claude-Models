"""SD-01 SINKDOCK geometry (manifold3d). One printed part, plus proxies of what it holds."""

import math

import numpy as np
from manifold3d import CrossSection, Manifold
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

from .params import BAYS, CUP_WALLS, WALLS, W, P, cup_y

BIG = 400.0


# -------------------------------------------------------------------------------------
# helpers
# -------------------------------------------------------------------------------------
def cs(poly):
    """shapely polygon (with holes) -> CrossSection."""
    poly = orient(poly, 1.0)  # CCW exterior, CW holes (manifold's positive fill rule)
    rings = [np.asarray(poly.exterior.coords)[:-1]]
    rings += [np.asarray(r.coords)[:-1] for r in poly.interiors]
    return CrossSection([r.tolist() for r in rings])


def prism(poly, z0, z1):
    return Manifold.extrude(cs(poly), z1 - z0).translate([0, 0, z0])


def yz_prism(poly_yz, x0, x1):
    """Extrude a polygon drawn in the (y, z) plane along x from x0 to x1."""
    m = Manifold.extrude(cs(poly_yz), x1 - x0)  # (u, v, w) = (y, z, x - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def xz_prism(poly_xz, y0, y1):
    """Extrude a polygon drawn in the (x, z) plane along y from y0 to y1."""
    m = Manifold.extrude(cs(poly_xz), y1 - y0)  # (u, v, w) = (x, z, y - y0)
    return m.transform([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]])


def below_plane(m, a, bx, by, xc=0.0):
    """Keep the part of m with z <= a + bx*(x - xc) + by*y."""
    n = np.array([bx, by, -1.0])
    off = bx * xc - a
    k = np.linalg.norm(n)
    return m.trim_by_plane((n / k).tolist(), off / k)


def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16) if r > 0 else box(x0, y0, x1, y1)


# -------------------------------------------------------------------------------------
# parts of the dock
# -------------------------------------------------------------------------------------
def floor(p=P):
    """V-gutter floor in every bay, falling toward y = 0, plus the lip."""
    parts = []
    zmax = p.z0 + p.D * p.tan_y + 30 * p.tan_x + 1
    for b in BAYS:
        blk = Manifold.cube([b["w"] + 0.02, p.D, zmax]).translate([b["x0"] - 0.01, 0, 0])
        left = below_plane(blk, p.z0, -p.tan_x, p.tan_y, b["xc"])   # rises toward x0
        right = below_plane(blk, p.z0, p.tan_x, p.tan_y, b["xc"])   # rises toward x1
        parts += [left, right]
    # under the walls: solid to the height of the neighbouring bay edge (walls cover it anyway)
    for (x0, x1) in WALLS:
        blk = Manifold.cube([x1 - x0, p.D, p.z0 + 2]).translate([x0, 0, 0])
        parts.append(blk)
    # spouts: one tapered spout in front of each bay opening; V top continues the gutter
    for b in BAYS:
        parts.append(spout(b, p))
    return Manifold.batch_boolean(parts, _union())


def bay_opening(b, p=P):
    """Clear width between the front returns of a bay."""
    r = {"disc": p.ret_disc, "rect": p.ret_rect, "brush": 0.0}[b["kind"]]
    return b["w"] - 2 * r


def spout_plan(b, p=P):
    w0 = min(bay_opening(b, p) + p.spout_root, b["w"])
    w1 = p.spout_tip
    xc = b["xc"]
    pts = [(xc - w0 / 2, 0.01), (xc + w0 / 2, 0.01), (xc + w1 / 2, -p.lip), (xc - w1 / 2, -p.lip)]
    poly = Polygon(pts)
    r = 3.0
    return poly.buffer(-r, quad_segs=12).buffer(r, quad_segs=12).union(
        box(xc - w0 / 2 + 0.5, -2.0, xc + w0 / 2 - 0.5, 0.01))


def spout(b, p=P):
    plan = spout_plan(b, p)
    blk = prism(plan, 0.0, p.z0 + 4)
    left = below_plane(blk, p.z0, -p.tan_x, p.tan_lip, b["xc"])
    right = below_plane(blk, p.z0, p.tan_x, p.tan_lip, b["xc"])
    s = left + right
    groove = Manifold.cube([b["w"] + 2, p.groove_w, p.groove_d]).translate(
        [b["x0"] - 1, -p.groove_y - p.groove_w / 2, -0.01])
    return s - groove


def _union():
    from manifold3d import OpType
    return OpType.Add


def diamond(yc, zc, w, h):
    return Polygon([(yc, zc - h / 2), (yc + w / 2, zc), (yc, zc + h / 2), (yc - w / 2, zc)])


def vent_overhang_deg(w, h):
    """Overhang of a diamond's upper sides, measured from vertical."""
    return math.degrees(math.atan2(w / 2, h / 2))


def divider_profile(p=P, vents=True, avoid=None):
    """Side profile (y, z) of every divider: rounded top corners, flat bottom."""
    r = p.top_r
    prof = box(0 + r, -20 + r, p.D - r, p.H - r).buffer(r, quad_segs=24)
    prof = prof.intersection(box(-1, 0, p.D + 1, p.H + 1))
    prof = prof.union(box(0, 0, p.D, p.H - r))
    if vents:
        for yc in p.vent_yc:
            if avoid and yc + p.vent_w / 2 > avoid[0] and yc - p.vent_w / 2 < avoid[1]:
                continue
            prof = prof.difference(diamond(yc, p.vent_zc, p.vent_w, p.vent_h))
    return prof


def dividers(p=P):
    y0, y1 = cup_y(p)
    vented = divider_profile(p)
    # the two walls the brush cup shares keep only the vents clear of the cup (it has its own)
    cupside = divider_profile(p, avoid=(y0 - p.cup_t - 1.0, y1 + p.cup_t + 1.0))
    parts = [yz_prism(cupside if (x0, x1) in CUP_WALLS else vented, x0, x1) for (x0, x1) in WALLS]
    walls = Manifold.batch_boolean(parts, _union())
    # those two walls stop 1.2 mm inside the cup's front and back walls; the cup replaces them
    a, b = y0 - p.cup_t + 1.2, y1 + p.cup_t - 1.2
    gap = Manifold.cube([CUP_WALLS[1][1] - CUP_WALLS[0][0] + 2, b - a, p.H + 10]).translate([CUP_WALLS[0][0] - 1, a, -1])
    return walls - gap


def returns(p=P):
    """Front sponge stops: short fins at y = 0 .. ret_t reaching into each sponge bay."""
    parts = []
    # side profile (x, z) of a fin: chamfered at the inner top corner
    for b in BAYS:
        if b["kind"] == "brush":
            continue
        r = p.ret_disc if b["kind"] == "disc" else p.ret_rect
        c = min(r - 1.0, 6.0)
        for side in (0, 1):
            if side == 0:
                xa, xb = b["x0"] - 0.5, b["x0"] + r
                poly = Polygon([(xa, 0), (xb, 0), (xb, p.ret_h - c), (xb - c, p.ret_h), (xa, p.ret_h)])
            else:
                xa, xb = b["x1"] - r, b["x1"] + 0.5
                poly = Polygon([(xa, 0), (xb, 0), (xb, p.ret_h), (xa + c, p.ret_h), (xa, p.ret_h - c)])
            parts.append(xz_prism(poly, 0.0, p.ret_t))
    return Manifold.batch_boolean(parts, _union())


def cup(p=P):
    """Brush cup: a rounded tube over the brush bay, open-slotted front and back."""
    b = [b for b in BAYS if b["kind"] == "brush"][0]
    wl, wr = CUP_WALLS
    y0, y1 = cup_y(p)
    t = p.cup_t
    rv = p.cup_reveal  # the cup stands proud of the walls it meets: no coplanar faces
    outer = rounded_rect(wl[0] - rv, y0 - t, wr[1] + rv, y1 + t, p.cup_r_out)
    inner = rounded_rect(b["x0"], y0, b["x1"], y1, p.cup_r_in)
    tube = prism(outer.difference(inner), 0.0, p.cup_h)
    # round the top outside edge a little by chamfering 0.8 mm (cheap, printable)
    slot = Manifold.cube([p.cup_slot, p.D + 10, p.cup_h + 2]).translate([b["xc"] - p.cup_slot / 2, -5, -1])
    tube = tube - slot
    return tube, inner


def cup_vent(p=P):
    """One tall diamond vent through each side wall of the cup."""
    wl, wr = CUP_WALLS
    y0, y1 = cup_y(p)
    yc = (y0 + y1) / 2
    return yz_prism(diamond(yc, p.cup_vent_zc, p.cup_vent_w, p.cup_vent_h), wl[0] - 1, wr[1] + 1)


def footprint(p=P):
    """Plan outline of the body behind y = 0, plus the spouts."""
    plan = rounded_rect(0, -20, W, p.D, p.corner_r).intersection(box(-1, 0, W + 1, p.D + 1))
    for b in BAYS:
        plan = plan.union(spout_plan(b, p))
    return plan


def build(p=P):
    body = dividers(p) + returns(p) + floor(p)
    body = body ^ prism(footprint(p), -0.5, 200)   # corner rounding and spout outlines
    tube, _ = cup(p)                               # a hollow outline: nothing intrudes into the bore
    return body + (tube - cup_vent(p))             # the cup stands proud of the walls, never clipped


# -------------------------------------------------------------------------------------
# proxies of what it holds (for fit checks and renders)
# -------------------------------------------------------------------------------------
def disc_sponge(dia, thick, segments=96):
    """A disc sponge standing on edge, axis along x, centred on the origin."""
    c = Manifold.cylinder(thick, dia / 2, dia / 2, segments).translate([0, 0, -thick / 2])
    return c.rotate([0, 90, 0])


def rest_disc(bay, dia, thick, p=P):
    """Where a disc sponge settles: rim on the V floor, rolled forward against the returns."""
    # The rim touches the V floor at x = xc +- thick/2. Lowest rim point sits at height zr(y).
    h = (thick / 2) * p.tan_x
    # it rolls forward until the circle touches the return top edge (y = ret_t, z = ret_h)
    # centre (yc, zc): zc = r + zfloor(yc) approx; contact: (yc - ret_t)^2 + (zc - ret_h)^2 = r^2
    r = dia / 2
    yc = r  # start
    k = math.sqrt(1 + p.tan_y ** 2)  # circle resting on a plane rising at slope_y
    for _ in range(60):
        zc = r * k + p.z0 + h + yc * p.tan_y
        dz = zc - p.ret_h
        yc_new = p.ret_t + math.sqrt(max(r * r - dz * dz, 0.0))
        if abs(yc_new - yc) < 1e-6:
            break
        yc = yc_new
    zc = r * k + p.z0 + h + yc * p.tan_y
    return bay["xc"], yc, zc


def rect_sponge(L, T, Hh, p=P):
    """Standing on its short end, tilted back with the floor; origin at the front-bottom centre."""
    return Manifold.cube([T, L, Hh]).translate([-T / 2, 0, 0]).rotate([p.slope_y, 0, 0])


def rest_rect(bay, L, T, Hh, p=P):
    """A flat sponge on its long edge, slid forward against the returns, tilted with the floor."""
    h = (T / 2) * p.tan_x
    yb = p.ret_t + p.ret_h * p.tan_y  # leans forward with the floor onto the top of the returns
    return bay["xc"], yb, p.z0 + h + yb * p.tan_y


def brush_proxy(handle_w=26.0, handle_t=20.0, handle_len=200.0, head_d=62.0, head_h=40.0, lean_deg=0.0):
    """A generic dish brush, handle down. Origin at the handle tip centre."""
    hcs = CrossSection.square([handle_w, handle_t], center=True).offset(3.0, join_type=_round())
    handle = Manifold.extrude(hcs.offset(-3.0, join_type=_round()), handle_len)
    head = Manifold.cylinder(head_h, head_d / 2 * 0.85, head_d / 2, 64).translate([0, 0, handle_len - 6])
    m = handle + head
    return m.rotate([lean_deg, 0, 0])


def _round():
    from manifold3d import JoinType
    return JoinType.Round
