"""
ORBIT, all-printed revision (exterior review B).  No screws, springs, pins or other
hardware: five printed parts and the blade.

    body      one-piece monocoque (prints on its back face, no supports)
    wheel     thumb wheel + pinion + retaining flange, one part (face cap is a colour inlay)
    shuttle   the rack; it also keys the wheel into the body
    carriage  blade seat with an integral in-plane lock pawl
    tail cap  closes the channel

Concept-stage geometry for the visual direction: form, layout and the visible mechanism.
Fits, tooth forms and flexure proportions are placeholders, not print-ready CAD.
"""

import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from . import geom as G

T = 23.0                        # body thickness
BY = -8.6                       # blade plane, against the back wall
H0N, H1N = -7.5, 23.5           # nose height
MOUTH = (0 - H0N) / math.tan(G.RAKE)      # x of the nose face at the cutting edge (z = 0)
TIP = MOUTH - G.SEG             # tip with one segment out: its score line sits at the mouth
PARK = 13.5                     # retract step: parks the tip 3.5 mm inside the mouth
TIPS = 7                        # working positions (the eighth, the tail stub, is not used)
M, Z = 1.6, 12                  # pinion module / teeth (pitch radius 9.6)
WR = 19.5
WZ = 21.6
RACK_Z = WZ - M * Z / 2
RK = lambda z: z / math.tan(G.RAKE)       # x offset of a 59-degree line at height z
# Rack ends are raked parallel to the nose and tail. Fully forward (last tip) its front end must
# stay 3 mm behind the nose face; that fixes how far forward the wheel can sit.
RACK_F0 = MOUTH + 3.0 + G.SEG * (TIPS - 1)                # rack front line, x at z = 0, position shown
WX = round(RACK_F0 + RK(RACK_Z) + 3.0 + PARK + 0.3, 1)   # wheel axis
Y_WALL, Y_CARR = -9.0, -5.7     # carriage layer
Y_FL = (-5.4, -4.3)             # wheel flange
Y_GEAR = (-4.3, 2.7)            # rack + pinion layer
Y_DISC = (3.0, T / 2 + 0.3)     # thumb wheel disc
TAIL = TIP + G.BLADE_L          # blade tail, position shown
PAWL_X = TAIL + 14.0
WIN_Z = (3.4, 9.6)
WIN_X = [PAWL_X + PARK] + [PAWL_X - G.SEG * k for k in range(TIPS)]     # parked, then 7 working
RACK_R0 = WX + 3.0 + G.SEG * (TIPS - 1) - RK(RACK_Z)        # rack rear line, x at z = 0
RACK_X = (RACK_F0, RACK_R0 + RK(RACK_Z + M))                # bounding extent, position shown
BACK_EDGE = (2.4, 2.4, "c")     # 45-degree chamfer: this face is on the bed
FRONT_EDGE = (3.6, 3.6, "c")


def pinion_poly(cx, cz, m=M, z=Z, pa=math.radians(20), phase=0.0):
    r, rb, ra, rf = m * z / 2, m * z / 2 * math.cos(pa), m * z / 2 + m, m * z / 2 - 1.2 * m
    inv = lambda a: math.tan(a) - a
    pts = []
    for i in range(z):
        c = phase + 2 * math.pi * i / z
        fl = []
        for rho in np.linspace(max(rb, rf), ra, 7):
            a = math.acos(min(1.0, rb / rho))
            fl.append((rho, math.pi / (2 * z) + inv(pa) - inv(a)))
        left = [(rf, fl[0][1])] + fl if rb > rf else fl
        for rho, th in left:
            pts.append((cx + rho * math.cos(c - th), cz + rho * math.sin(c - th)))
        for rho, th in left[::-1]:
            pts.append((cx + rho * math.cos(c + th), cz + rho * math.sin(c + th)))
    return Polygon(pts).buffer(0)


def rack_poly(x0, x1, z_bot, m=M, pa=math.radians(20), x_tooth=WX):
    p = math.pi * m
    zt, zr, zp = RACK_Z + m, RACK_Z - 1.2 * m, RACK_Z
    teeth = []
    k0 = int(math.floor((x0 - x_tooth) / p)) + 1
    k1 = int(math.floor((x1 - x_tooth) / p)) - 1
    for k in range(k0, k1 + 1):
        c = x_tooth + k * p
        a, b = p / 4 + (zp - zr) * math.tan(pa), p / 4 - (zt - zp) * math.tan(pa)
        teeth.append(Polygon([(c - a, zr - 0.01), (c - b, zt), (c + b, zt), (c + a, zr - 0.01)]))
    return unary_union([box(x0, z_bot, x1, zr)] + teeth)


def tail_geometry():
    """The tail face is parallel to the rack's rear end when the blade is parked, plus a wall."""
    x0 = RACK_R0 + PARK + 0.6 + 3.5                     # tail face, x at z = 0
    return x0 - RK(11.0), x0 + RK(19.0)


def outline():
    dx = G.raked_dx(H1N - H0N)
    xb, xt = tail_geometry()
    top = G.spline([(dx, H1N), (46, 25.0), (WX, 26.2), (WX + 34, 25.0), (xt - 22, 22.0), (xt, 19.0)])
    bot = G.spline([(xb, -11.0), (xb - 22, -12.0), (xb - 48, -11.3), (72, -9.3), (46, -7.7), (24, -7.0), (0, H0N)])
    base = Polygon(top + bot)
    crest = G.circle(WX, WZ, 15.6)          # covers the pinion; blended into the spine as one swell
    shape = unary_union([base, crest]).buffer(26, quad_segs=24).buffer(-26, quad_segs=24)
    return G.round_corners(shape, 6.4), xb


def build(explode=False, cut_y=None):
    """Parts in assembled position; explode=True spreads them for the exploded view.
    cut_y removes everything above that y (cutaway through the gear layer)."""
    out, xb = outline()
    solid = G.xz_solid(out, -T / 2, T / 2, BACK_EDGE, FRONT_EDGE)

    # ---- body ---------------------------------------------------------------------
    split = xb + 11.0 / math.tan(G.RAKE) - 12.0             # raked tail-cap line (x at z = 0)
    body = solid - G.xz_prism(G.half_plane_raked(split - 0.18, +1), -30, 30)
    body = body - G.cube(-5, 27, BY - 0.35, BY + 0.35, -0.35, 18.35)                  # blade mouth
    body = body - G.cube(25, 260, Y_WALL, Y_GEAR[1] + 0.2, -0.6, 18.6)                # carriage + rack channel
    tun = box(0, RACK_Z - 6.4, 26, RACK_Z + M + 0.6).intersection(G.half_plane_raked(MOUTH + 2.5, +1))
    body = body - G.xz_prism(tun, Y_GEAR[0] - 0.3, Y_GEAR[1] + 0.2)                   # rack tunnel in the nose
    body = body - G.cyl_y(WX, WZ, M * Z / 2 + M + 0.6, Y_FL[0] - 0.2, Y_DISC[0], 96)   # pinion bay
    body = body - G.cyl_y(WX, WZ, WR + 0.5, Y_DISC[0] - 0.1, T, 160)                   # wheel bay = journal
    # lock windows in a shallow raked track: one parked, seven working
    zc = (WIN_Z[0] + WIN_Z[1]) / 2
    x0, x1 = min(WIN_X) - 6.5, max(WIN_X) + 6.5
    h = 5.6
    sk = G.raked_dx(h)
    track = G.round_corners(Polygon([(x0 - sk, zc - h), (x1 - sk, zc - h), (x1 + sk, zc + h), (x0 + sk, zc + h)]), 1.6)
    body = body - G.xz_prism(track, -T / 2 - 1, -T / 2 + 0.6)
    for x in WIN_X:
        w = G.round_corners(box(x - 1.45, WIN_Z[0] - 0.2, x + 1.45, WIN_Z[1] + 0.2), 0.6)
        body = body - G.xz_prism(w, -T / 2 - 1, Y_WALL + 0.1)

    # ---- tail cap -------------------------------------------------------------------
    cap = solid ^ G.xz_prism(G.half_plane_raked(split + 0.18, +1), -30, 30)
    cap = G.union([cap, G.cube(split - 7, split + 3, Y_WALL + 0.3, Y_GEAR[1] - 0.1, -0.3, 18.3)])
    pocket = box(split - 8, RACK_Z - 6.4, 300, RACK_Z + M + 0.8).intersection(G.half_plane_raked(RACK_R0 + PARK + 0.6, -1))
    cap = cap - G.xz_prism(pocket, Y_GEAR[0] - 0.4, Y_GEAR[1] + 0.3)

    # ---- wheel: knurled ring + pinion + flange; dark face cap is a first-layer colour inlay ----
    y0, y1 = Y_DISC
    disc = G.fluted_wheel_xz(WX, WZ, WR, y0 + 2.4, y1, 64, flute_r=0.55, edge=(0.9, 0.9, "c"))
    disc = G.union([disc, G.cyl_y(WX, WZ, WR, y0, y0 + 2.5, 160)])                    # smooth journal band
    RC = WR - 2.9                                                                     # face-cap radius
    disc = disc - G.cyl_y(WX, WZ, RC + 0.02, y1 - 0.9, y1 + 2, 160)
    pip = (WX + (RC - 3.4) * math.cos(math.radians(90)), WZ + (RC - 3.4) * math.sin(math.radians(90)))
    disc = G.union([disc, G.cyl_y(pip[0], pip[1], 1.25, y1 - 1.0, y1 - 0.25, 48)])    # index pip, shows through the cap
    capface = G.xz_solid(G.circle(WX, WZ, RC), y1 - 0.9, y1 - 0.3, 0, (0.35, 0.35, "c")) - \
        G.cyl_y(pip[0], pip[1], 1.27, y1 - 2, y1 + 2, 48)
    pin = G.xz_prism(pinion_poly(WX, WZ, phase=-math.pi / 2 + math.pi / Z), Y_GEAR[0], y0 + 0.05)
    flange = G.cyl_y(WX, WZ, M * Z / 2 - 0.2, Y_FL[0], Y_FL[1] + 0.05, 96)
    wheel = G.union([disc, pin, flange])

    # ---- shuttle (rack) ----------------------------------------------------------------
    rp = rack_poly(RACK_F0 - 2, RACK_X[1] + 2, RACK_Z - 6.0).intersection(G.half_plane_raked(RACK_F0, +1))
    rp = rp.intersection(G.half_plane_raked(RACK_R0, -1))
    rp = max(rp.geoms, key=lambda g: g.area) if rp.geom_type == "MultiPolygon" else rp
    rack = G.xz_prism(rp, Y_GEAR[0] + 0.1, Y_GEAR[1] - 0.1)
    px = PAWL_X - 3.5
    paddle = G.cube(px - 3, px + 3, -7.6, Y_GEAR[0] + 1.0, 1.2, RACK_Z - 5.9)
    shuttle = G.union([rack, paddle])

    # ---- carriage with pawl ---------------------------------------------------------------
    block = G.cube(TAIL, TAIL + 24.5, Y_WALL + 0.1, Y_CARR, 0.0, 18.0)
    plate = G.cube(TAIL - 12.5, TAIL + 0.1, BY + 0.3, Y_CARR, 0.2, 17.8)
    lug = G.cyl_y(TAIL - 7.0, 9.0, 1.95, BY - 0.3, BY + 0.4, 32)
    carriage = G.union([block, plate, lug])
    carriage = carriage - G.cube(px - 6, px + 6, -8.0, Y_CARR + 1, 0.8, RACK_Z - 5.6)        # lost-motion pocket
    for z in (WIN_Z[0] - 0.6, WIN_Z[1] + 0.1):                                             # U-slit round the pawl arm
        carriage = carriage - G.cube(TAIL + 2.5, PAWL_X + 2.0, Y_WALL - 1, -7.5, z, z + 0.5)
    carriage = carriage - G.cube(PAWL_X + 1.5, PAWL_X + 2.0, Y_WALL - 1, -7.5, WIN_Z[0] - 0.6, WIN_Z[1] + 0.6)
    tooth = G.cube(PAWL_X - 1.2, PAWL_X + 1.2, -T / 2 + 0.9, Y_WALL + 0.2, WIN_Z[0], WIN_Z[1])
    carriage = G.union([carriage, tooth])

    blade = G.blade(TIP, BY)

    parts = dict(body=(body, "graphite"), tail_cap=(cap, "graphite"), wheel=(wheel, "orange"),
                 wheel_face=(capface, "graphite2"), shuttle=(shuttle, "graphite2"),
                 carriage=(carriage, "orange"), blade=(blade, "blade"))
    off = {k: (0, 0, 0) for k in parts}
    if explode:
        off.update(tail_cap=(30, 0, 0), wheel=(0, 34, 46), wheel_face=(0, 34, 46), shuttle=(34, 0, -40),
                   carriage=(34, 0, -68), blade=(14, 0, -68))
    res = []
    for k, (m, mat) in parts.items():
        if cut_y is not None and k in ("body", "tail_cap", "wheel", "wheel_face"):
            m = m ^ G.cube(-50, 300, -50, cut_y, -80, 120)
            if m.is_empty():
                continue
        res.append((k, m.translate(list(off[k])), mat))
    anchors = dict(body=(34, -T / 2, 16), tail_cap=(xb + 14, -T / 2, 6), wheel=(WX, Y_FL[0], WZ),
                   shuttle=(RACK_X[1] - 14, Y_GEAR[0], RACK_Z - 3), carriage=(PAWL_X - 6, -T / 2, 14), blade=(40, BY, 9))
    anchors = {k: tuple(np.add(v, off[k])) for k, v in anchors.items()}
    lo = np.full(3, 1e9)
    hi = -lo
    for k, (m, _) in parts.items():
        if k != "blade":
            a, b = G.bbox(m)
            lo, hi = np.minimum(lo, a), np.maximum(hi, b)
    return dict(key="orbit2", code="02", name="ORBIT", parts=res, thick=T, anchors=anchors,
                detail=(WX - 4, 8, WZ + 1), envelope=tuple(float(v) for v in (hi - lo)),
                labels=dict(pinion=(WX, WZ + 9), rack=(RACK_X[1] - 12, RACK_Z - 3), carriage=(TAIL + 19, 15.5),
                            blade=(40, 9.0)))
