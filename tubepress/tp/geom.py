"""TP-01 TUBEPRESS geometry (manifold3d): the frame and the key, in assembled coordinates."""

import math

import numpy as np
from manifold3d import CrossSection, Manifold, OpType
from shapely.affinity import rotate as srotate
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient

from .params import P, knob_x


# -------------------------------------------------------------------------------------
def cs(poly):
    poly = orient(poly, 1.0)
    rings = [np.asarray(poly.exterior.coords)[:-1]]
    rings += [np.asarray(r.coords)[:-1] for r in poly.interiors]
    return CrossSection([r.tolist() for r in rings])


def prism(poly, z0, z1):
    return Manifold.extrude(cs(poly), z1 - z0).translate([0, 0, z0])


def yz_prism(poly_yz, x0, x1):
    """Extrude a polygon drawn in the (y, z) plane along x from x0 to x1."""
    m = Manifold.extrude(cs(poly_yz), x1 - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def union(parts):
    return Manifold.batch_boolean(parts, OpType.Add)


def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16)


def teardrop(cy, cz, r, segs=64):
    """Circle with a 45 deg pointed top: prints without support in a vertical wall."""
    c = Point(cy, cz).buffer(r, quad_segs=segs // 4)
    k = r / math.sqrt(2)
    tri = Polygon([(cy - k, cz + k), (cy + k, cz + k), (cy, cz + r * math.sqrt(2))])
    return c.union(tri)


# -------------------------------------------------------------------------------------
# key
# -------------------------------------------------------------------------------------
def knob_profile(p=P, phase_deg=0.0):
    """Sawtooth outline in the (y, z) plane, centred on the axis. Going round in +angle, each tooth
    ramps out from the root to the tip, then drops back on a steep, slightly undercut face."""
    pitch = 2 * math.pi / p.teeth
    s = p.steep_frac
    d_under = math.tan(math.radians(p.undercut_deg)) * p.tooth_depth / p.r_root
    pts = []
    ph = math.radians(phase_deg)
    for i in range(p.teeth):
        a0 = ph + i * pitch
        at = a0 + (1 - s) * pitch
        n = 8
        for k in range(n + 1):  # the ramp: r rises linearly with angle
            f = k / n
            a = a0 + f * (at - a0)
            r = p.r_root + f * p.tooth_depth
            pts.append((r * math.cos(a), p.axis_z + r * math.sin(a)))
        ar = at - d_under
        pts.append((p.r_root * math.cos(ar), p.axis_z + p.r_root * math.sin(ar)))
        for k in range(1, 3):  # short root land up to the next ramp
            a = ar + (a0 + pitch - ar) * k / 3
            pts.append((p.r_root * math.cos(a), p.axis_z + p.r_root * math.sin(a)))
    return Polygon(pts).buffer(0)


def rest_phase(p=P):
    """Knob phase that puts a tooth gap centred over the pawl (at the bottom, angle -90 deg)."""
    pitch = 360.0 / p.teeth
    s = p.steep_frac
    # steep face at a0 + (1 - s) pitch; the pawl sits just after it
    face = -90.0 - 0.5 * s * pitch - 0.15 * pitch
    return face - (1 - s) * pitch


def key(p=P, phase_deg=None):
    """Knob + journal + open fork. Fork gap normal is y (the tube's plane is x-z)."""
    if phase_deg is None:
        phase_deg = rest_phase(p)
    k0, k1 = knob_x(p)
    knob = yz_prism(knob_profile(p, phase_deg), k0, k1)
    # index mark on the knob's outer face, in the plane of the fork gap
    mark = Manifold.cube([p.mark_d * 2, p.mark_w, p.r_root * 1.6]).translate(
        [k0 - p.mark_d, -p.mark_w / 2, p.axis_z - p.r_root * 0.8])
    knob = knob - mark
    # winding arrow on the knob face: a small arrowhead pointing counter-clockwise (seen from the face)
    knob = knob - arrow(p)
    r = p.shaft_d / 2
    x_end = p.slot_l + p.lug_t_far
    # journal + fork as one revolved profile (tip chamfer included): consistent facets, no slivers
    c = p.tip_chamfer
    prof = CrossSection([[(0.0, k1 - 1.0), (r, k1 - 1.0), (r, x_end - c), (r - c, x_end), (0.0, x_end)]])
    shaft = Manifold.revolve(prof, 128).transform([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, p.axis_z]])
    gap = Manifold.cube([x_end + 1, p.fork_gap, p.shaft_d + 2]).translate([0.0, -p.fork_gap / 2, p.axis_z - r - 1])
    fork = shaft - gap
    return knob + fork


def arrow(p=P):
    """Debossed arrowhead on the knob's outer face at 12 o'clock + 50 deg, pointing in the winding
    direction. Seen from the face (looking along +x), +y is to the LEFT, so counter-clockwise as seen
    is a negative rotation about +x."""
    k0, _ = knob_x(p)
    r = p.r_root - 4.5
    a = math.radians(90 - 50)  # angle in the y-z plane (from +y)
    cy, cz = r * math.cos(a), p.axis_z + r * math.sin(a)
    t = (math.sin(a), -math.cos(a))  # tangent for a negative rotation about +x
    n = (math.cos(a), math.sin(a))
    L, Wd = 4.0, 3.2
    tip = (cy + t[0] * L / 2, cz + t[1] * L / 2)
    b1 = (cy - t[0] * L / 2 + n[0] * Wd / 2, cz - t[1] * L / 2 + n[1] * Wd / 2)
    b2 = (cy - t[0] * L / 2 - n[0] * Wd / 2, cz - t[1] * L / 2 - n[1] * Wd / 2)
    tri = Polygon([tip, b1, b2])
    return yz_prism(tri, k0 - 1.0, k0 + p.mark_d)


# -------------------------------------------------------------------------------------
# frame
# -------------------------------------------------------------------------------------
def leaf_box(p=P):
    k0, k1 = knob_x(p)
    y_tip = pawl_y(p) - p.pawl_base_y / 2 - 0.5
    return k0, k0 + p.leaf_w, y_tip, y_tip + p.leaf_l  # flush with the knob's outer face


def pawl_y(p=P):
    """y of the pawl post centre: just past the steep face at the bottom of the knob."""
    return 0.9


def pawl_profile(p=P, clearance=0.15):
    """Pawl post in (y, z): fills the tooth gap at the bottom of the knob (at rest phase) from the
    leaf up to pawl_engage inside the tip circle, less a running clearance."""
    gap_region = box(-6, 0, 8, p.axis_z - p.r_root + 0.01)
    knob = knob_profile(p, rest_phase(p)).buffer(clearance)
    tip_circle_z = p.axis_z - p.r_tip
    reach = Point(0, p.axis_z).buffer(p.r_tip - p.pawl_engage, quad_segs=64)
    pc = pawl_y(p)
    col = box(pc - p.pawl_base_y / 2, p.leaf_t - 0.01, pc + p.pawl_base_y / 2, p.axis_z)
    shape = col.intersection(gap_region).difference(knob).difference(reach)
    # keep the piece attached to the leaf
    if shape.geom_type != "Polygon":
        shape = max(shape.geoms, key=lambda g: g.area)
    del tip_circle_z
    return shape


def frame(p=P, nip=None):
    nip = p.nip if nip is None else nip
    k0, k1 = knob_x(p)
    x_far = p.slot_l + p.lug_t_far
    # plate: main body plus a wider pad under the knob for the leaf
    x_left = k0 - p.knob_plate_ext
    lx0, lx1, ly0, ly1 = leaf_box(p)
    main = rounded_rect(-p.lug_t_near, -p.plate_w / 2, x_far, p.plate_w / 2, p.corner_r)
    pad = rounded_rect(x_left, ly0 - 3.0, -p.lug_t_near + p.corner_r + 1, ly1 + 2.5, p.corner_r)
    plan = main.union(pad)
    plate = prism(plan, 0.0, p.plate_t)
    # U-cut around the leaf, then the leaf itself (thinner than the plate, printed on the bed)
    g = p.leaf_gap
    cut = prism(box(lx0 - g, ly0 - g, lx1 + g, ly1), -1, p.plate_t + 1)
    leaf = prism(box(lx0, ly0, lx1, ly1 + 0.6), 0.0, p.leaf_t)
    pawl = yz_prism(pawl_profile(p), lx0, lx1)
    # 45 deg lead-in on the pawl's knob-side (-x) top edge: a key pushed in at the wrong angle
    # presses the pawl down instead of jamming on it
    lead = 1.6
    pawl = pawl - _chamfer_block(lx0, p.axis_z - p.r_tip + p.pawl_engage - lead, lead)
    plate = plate - cut + leaf + pawl
    # nip slot with 45 deg lead-ins, top and bottom
    c, h, t = p.nip_chamfer, nip / 2, p.plate_t
    slot = Polygon([(-h - c, -0.01), (h + c, -0.01), (h, c), (h, t - c), (h + c, t + 0.01), (-h - c, t + 0.01),
                    (-h, t - c), (-h, c)])
    plate = plate - yz_prism(slot, 0.0, p.slot_l)
    # lugs: gothic outline round a teardrop bore
    rb = p.shaft_d / 2 + p.bore_clear
    outer = teardrop(0, p.axis_z, rb + p.lug_wall).union(box(-p.lug_w / 2, 0, p.lug_w / 2, p.axis_z))
    apex = p.axis_z + (rb + p.lug_wall) * math.sqrt(2)
    outer = outer.intersection(box(-p.lug_w / 2, 0, p.lug_w / 2, apex - 1.4))  # 2.8 mm flat on the point
    lug_prof = outer.difference(teardrop(0, p.axis_z, rb))
    near = yz_prism(lug_prof, -p.lug_t_near, 0.0)
    far = yz_prism(lug_prof, p.slot_l, x_far)
    return plate + near + far


def _chamfer_block(x0, z0, c):
    """A 45 deg wedge removing the top -x edge of the pawl: points with z > z0 + (x - x0)."""
    poly = Polygon([(x0 - 5, z0 - 5), (x0 + c + 5, z0 + c + 5), (x0 - 5, z0 + c + 5)])
    m = Manifold.extrude(cs(poly), 40)  # (u, v, w) = (x, z, y)
    return m.transform([[1, 0, 0, 0], [0, 0, 1, -20], [0, 1, 0, 0]])


# -------------------------------------------------------------------------------------
# tube proxy (renders and checks)
# -------------------------------------------------------------------------------------
def tube_flat(width, thick, z0, z1, x0=None):
    x0 = (P.slot_l - width) / 2 if x0 is None else x0
    return Manifold.cube([width, thick, z1 - z0]).translate([x0, -thick / 2, z0])
