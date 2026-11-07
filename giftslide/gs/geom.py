"""
GS-05 GIFT SLIDE geometry (manifold3d).

Two printed parts:
  Tray  printed floor-down. Pocket for the card, a 45-degree dovetail lip along both long
        walls, and a relief track cut into each groove face for the detent bump.
  Lid   printed underside-down. Dovetail edges, a shadow-gap rebate, two in-plane flexure
        beams (one per edge) each carrying a small bump that runs in the tray's relief track.

All geometry is built from 2-D sections that are extruded, so every surface is either
vertical, horizontal-up, a <=45 degree overhang, or a short (<0.5 mm) step.

`dy` arguments grow a part's lateral surfaces outward per side (printer-variation corners):
tray dy > 0 means the tray prints its slots wide, lid dy > 0 means the lid prints wide.
"""

import math

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold

from .params import P

import manifold3d as _m

_m.set_circular_segments(96)

# =====================================================================================
# primitives
# =====================================================================================


def cs(pts):
    return CrossSection([np.asarray(pts, dtype=float)], FillRule.EvenOdd)


def rrect(x0, x1, y0, y1, r):
    """Rounded rectangle cross-section in XY."""
    r = min(r, 0.5 * (x1 - x0) - 1e-6, 0.5 * (y1 - y0) - 1e-6)
    sq = CrossSection.square((x1 - x0 - 2 * r, y1 - y0 - 2 * r)).translate((x0 + r, y0 + r))
    return sq.offset(r, JoinType.Round, circular_segments=96) if r > 0 else sq


def prism_z(sec, z0, z1):
    return Manifold.extrude(sec, z1 - z0).translate((0, 0, z0))


def prism_x(sec_yz, x0, x1):
    """Extrude a section drawn in (y, z) along X from x0 to x1."""
    m = Manifold.extrude(sec_yz, x1 - x0)
    # (u, v, w) -> (x = w + x0, y = u, z = v)
    return m.transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], dtype=float))


def prism_y(sec_xz, y0, y1):
    """Extrude a section drawn in (x, z) along Y from y0 to y1."""
    m = Manifold.extrude(sec_xz, y1 - y0)
    # (u, v, w) -> (x = u, y = w + y0, z = v)  (det = -1, so mirror back with a flip)
    m = m.transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]], dtype=float))
    return m


def chamfered_rrect_box(x0, x1, y0, y1, r, z0, z1, cb, ct):
    """Rounded-rect block with a 45-degree chamfer cb on the bottom edge and ct on the top."""
    parts = [prism_z(rrect(x0, x1, y0, y1, r), z0 + cb, z1 - ct)]
    if cb > 0:
        parts.append(prism_z(rrect(x0 + cb, x1 - cb, y0 + cb, y1 - cb, r - cb), z0, z0 + 1e-3))
    if ct > 0:
        parts.append(prism_z(rrect(x0 + ct, x1 - ct, y0 + ct, y1 - ct, r - ct), z1 - 1e-3, z1))
    return Manifold.batch_hull(parts)


def mirror_y_pts(right):
    """right: list of (y, z) for y >= 0 going up the right side. Returns a closed symmetric loop."""
    left = [(-y, z) for (y, z) in reversed(right)]
    return right + left


def text_section(s, height, font_weight="bold", family="DejaVu Sans"):
    """Text as a CrossSection in local (u, v): u along the baseline, v up, centred on the origin.
    `height` is the cap height in mm."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    fp = FontProperties(family=family, weight=font_weight)
    cap = TextPath((0, 0), "H", size=10, prop=fp).get_extents().height
    tp = TextPath((0, 0), s, size=10 * height / cap, prop=fp)
    polys = [np.asarray(p) for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    sec = CrossSection([p[:-1] if np.allclose(p[0], p[-1]) else p for p in polys], FillRule.EvenOdd)
    (u0, v0), (u1, v1) = sec.bounds()[:2], sec.bounds()[2:]
    return sec.translate((-(u0 + u1) / 2, -(v0 + v1) / 2))


def place_uv(sec, x, y, up=(1, 0), right=(0, -1)):
    """Map a (u, v) section to XY with the text 'right' and 'up' directions given."""
    rx, ry = right
    ux, uy = up
    return sec.transform(np.array([[rx, ux, x], [ry, uy, y]], dtype=float))


def star_section(r_out, r_in, n=5, rot=0.0, round_r=0.35):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi / 2 + i * math.pi / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    s = cs(pts)
    return s.offset(-round_r, JoinType.Round).offset(round_r, JoinType.Round)


# =====================================================================================
# sections
# =====================================================================================


def lid_section(p=P, dy=0.0):
    """Lid cross-section in (y, z lid-local)."""
    yf, py = p.land_y + dy, p.panel_y + dy
    lc, pc = p.land_chamfer, p.panel_chamfer
    right = [
        (0.0, 0.0),
        (yf - lc, 0.0),
        (yf, lc),
        (yf, p.land_h),
        (yf - p.bevel_run, p.bevel_top_z),
        (py, p.bevel_top_z),
        (py, p.lid_t - pc),
        (py - pc, p.lid_t),
        (0.0, p.lid_t),
    ]
    return cs(mirror_y_pts(right[1:-1]))


def groove_void_section(p=P, dy=0.0):
    """The space the lid lives in, in (y, z absolute). dy grows it outward (tray prints wide)."""
    zs, H = p.z_ledge, p.H
    yg, yl = p.y_g + dy, p.y_lip + dy
    lb = zs + p.lid_t - p.lip_tip_h
    c = p.lip_chamfer
    right = [
        (yg, zs),
        (yg, zs + p.z_junction),
        (yl, lb),
        (yl, H - c),
        (yl + c, H),
        (yl + c, H + 1.0),
    ]
    return cs(mirror_y_pts(right))


def relief_plan(p=P, dy=0.0, side=+1):
    """Relief-track outline in XY for one side (side = +1 or -1)."""
    prof = p.relief_profile()
    yg = p.y_g + dy
    outer = [(x, side * (yg + d)) for x, d in prof]
    inner = [(prof[-1][0], side * (yg - 0.05)), (prof[0][0], side * (yg - 0.05))]
    pts = outer + inner
    if side < 0:
        pts = pts[::-1]
    return cs(pts)


# =====================================================================================
# parts
# =====================================================================================


def tray(p=P, dy=0.0, message=None, logo=True, push_hole=True, window=False):
    L, W, H = p.L, p.W, p.H
    zs = p.z_ledge
    body = chamfered_rrect_box(0, L, -W / 2, W / 2, p.corner_r, 0, H, p.bottom_chamfer, p.top_chamfer)
    cuts = []
    # pocket (dy shrinks/grows it like any internal feature)
    x0 = p.end_wall - dy
    cuts.append(prism_z(rrect(x0, x0 + p.pocket_l + 2 * dy, -p.pocket_w / 2 - dy, p.pocket_w / 2 + dy,
                              p.pocket_r), p.floor_t, zs + 0.01))
    # lid groove, open at x = L, closed by the end wall at x = end_wall
    cuts.append(prism_x(groove_void_section(p, dy), p.end_wall - dy, L + 1.0))
    # relief tracks
    for side in (+1, -1):
        cuts.append(prism_z(relief_plan(p, dy, side), zs - p.relief_floor, zs + p.z_junction))
    # chamfer on the end wall's inner top edge (the rear seam reads as a V like the sides)
    c = p.panel_chamfer
    xe = p.end_wall - dy
    cuts.append(prism_y(cs([(xe - c, H + 0.01), (xe + 0.01, H - c - 0.01), (xe + 0.01, H + 0.01)]),
                        -(p.y_lip + dy + p.lip_chamfer), p.y_lip + dy + p.lip_chamfer))
    if push_hole:
        cuts.append(prism_z(CrossSection.circle(p.push_hole_d / 2, 96).translate((p.push_hole_x, 0)),
                            -1, p.floor_t + 0.5))
    msg = p.message if message is None else message
    if msg:
        t = text_section(msg, p.message_h)
        cuts.append(prism_z(place_uv(t, p.message_x, 0.0, up=(1, 0), right=(0, -1)),
                            p.floor_t - p.message_depth, p.floor_t + 0.5))
    if logo:
        t1 = text_section("ODD LAYER", 4.0)
        t2 = text_section("GIFT SLIDE  GS-05", 2.6, font_weight="bold")
        # read from underneath with the open end pointing away: right = +Y, up = +X
        xs = L * 0.62
        cuts.append(prism_z(place_uv(t1, xs + 3.2, 0.0, up=(1, 0), right=(0, 1)), -1, p.logo_depth))
        cuts.append(prism_z(place_uv(t2, xs - 3.4, 0.0, up=(1, 0), right=(0, 1)), -1, p.logo_depth))
    if window:   # fit coupon: open floor to save time
        cuts.append(prism_z(rrect(p.end_wall + 6, L - p.open_wall - 6, -p.pocket_w / 2 + 6,
                                  p.pocket_w / 2 - 6, 3), -1, p.floor_t + 1))
    return body - Manifold.batch_boolean(cuts, _m.OpType.Add)


def bump(p=P, dy=0.0, side=+1):
    """Detent bump on the land of the flexure beam (lid-local)."""
    yf = p.land_y + dy
    hf = 0.5 * p.bump_flat
    xb = p.bump_x
    xf, xr = xb + p.bump_front, xb - p.bump_rear

    def trap(inset):
        pts = [(xr + inset, yf - 0.3), (xf - inset, yf - 0.3), (xf - inset, yf),
               (xb + hf - inset * 0.3, yf + p.bump_p - inset), (xb - hf + inset * 0.3, yf + p.bump_p - inset),
               (xr + inset, yf)]
        return cs(pts)

    lc = p.land_chamfer
    m = Manifold.batch_hull([prism_z(trap(lc), 0, 1e-3), prism_z(trap(0), lc, p.bump_h)])
    if side < 0:
        m = m.mirror((0, 1, 0))
    return m


def lid(p=P, dy=0.0, star=False, window=False, bumps=True, tag=""):
    """Lid, lid-local coordinates (x from the rear end, z from the underside)."""
    T, Ll = p.lid_t, p.lid_l
    body = prism_x(lid_section(p, dy), 0.0, Ll)
    if bumps:
        body = body + bump(p, dy, +1) + bump(p, dy, -1)
    cuts = []
    # flexure slots (stadium) between the main panel and each beam
    r = 0.5 * p.slot_w
    for side in (+1, -1):
        yc = side * (p.panel_y + dy + r)
        slot = rrect(p.beam_x0, p.beam_x1, yc - r, yc + r, r - 1e-3)
        cuts.append(prism_z(slot, -1, T + 1))
    # plan shape: front corners follow the tray's rounded corners, rear corners get a lead-in
    fp = rrect(-p.end_wall, p.L - p.end_wall, -p.W / 2, p.W / 2, p.corner_r)
    keep = prism_z(fp, -1, T + 1)
    yf = p.land_y + dy
    for side in (+1, -1):
        tri = cs([(-0.01, side * (yf - 0.6)), (0.6, side * (yf + 0.01)), (-0.01, side * (yf + 0.01))][::side])
        cuts.append(prism_z(tri, -1, T + 1))
    # edge chamfers: front top 0.6 (matches the tray), rear top 0.3, rear bottom 0.4
    ct, cr, cb = p.top_chamfer, p.panel_chamfer, 0.4
    span = (-p.W, p.W)
    cuts.append(prism_y(cs([(Ll - ct, T + 0.01), (Ll + 0.01, T - ct - 0.01), (Ll + 0.01, T + 0.01)]), *span))
    cuts.append(prism_y(cs([(-0.01, T - cr - 0.01), (cr, T + 0.01), (-0.01, T + 0.01)]), *span))
    cuts.append(prism_y(cs([(-0.01, -0.01), (cb, -0.01), (-0.01, cb)]), *span))
    # thumb dish
    if p.dish_depth > 0:
        a, h = p.dish_d / 2, p.dish_depth
        R = (a * a + h * h) / (2 * h)
        cuts.append(Manifold.sphere(R, 256).translate((p.dish_x, 0, T + R - h)))
    if star:
        st = star_section(p.star_r, p.star_r * 0.42)
        cuts.append(prism_z(st.translate((p.star_x, 0)), T - p.star_depth, T + 1))
    if window:
        cuts.append(prism_z(rrect(6.0, Ll - 6.0, -p.panel_y + 7, p.panel_y - 7, 3), -1, T + 1))
    if tag:   # coupon lids: which fit this is, debossed in the front strip, readable from the open end
        t = text_section(tag, 3.2)
        cuts.append(prism_z(place_uv(t, Ll - 3.0, 0.0, up=(1, 0), right=(0, -1)), T - 0.6, T + 1))
    return (body ^ keep) - Manifold.batch_boolean(cuts, _m.OpType.Add)


def star_inlay(p=P):
    """Inlay that fills the Star lid's deboss, for a second colour (lid-local)."""
    st = star_section(p.star_r, p.star_r * 0.42)
    return prism_z(st.translate((p.star_x, 0)), p.lid_t - p.star_depth, p.lid_t)


def card(p=P):
    x0 = p.end_wall + p.pocket_clear
    return prism_z(rrect(x0, x0 + p.card_l, -p.card_w / 2, p.card_w / 2, p.card_r),
                   p.floor_t, p.floor_t + p.card_t)


def lid_placed(p=P, s=0.0, dy=0.0, star=False, lid_m=None):
    """Lid in assembly coordinates at opening travel s (s = 0 closed)."""
    m = lid_m if lid_m is not None else lid(p, dy, star)
    return m.translate((p.end_wall + s, 0, p.z_ledge))


# =====================================================================================
# fit coupon
# =====================================================================================


def coupon_params(p=P):
    """A 46 mm long tray + lid that carries the full cross-section and every detent feature
    (parking pocket, R1, travel track, open stop, entry zone) with 12 mm of travel."""
    from dataclasses import replace

    return replace(p, card_l=40.0, travel=12.0, message="", push_hole_d=0.0)
