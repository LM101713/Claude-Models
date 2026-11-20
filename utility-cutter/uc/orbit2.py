"""
ORBIT v2 - the all-printed revision.  No screws, springs, pins or any other hardware:
five printed parts and the blade.

    body      one-piece monocoque (prints on its back face, no supports)
    wheel     thumb wheel + pinion + retaining flange, one piece
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
TIP = -7.5                      # blade tip, first segment out (retracted = +2.5)
WX, WZ, WR = 88.0, 21.6, 19.5   # wheel axis, radius
M, Z = 1.6, 12                  # pinion module / teeth (pitch radius 9.6)
RACK_Z = WZ - M * Z / 2         # rack pitch line
Y_WALL = -9.0                   # inner face of the back wall
Y_CARR = -5.7                   # carriage layer:  Y_WALL .. Y_CARR
Y_FL = (-5.4, -4.3)             # wheel flange
Y_GEAR = (-4.3, 2.7)            # rack + pinion layer
Y_DISC = (3.0, T / 2 + 0.3)     # thumb wheel disc
PAWL_X = 106.5                  # pawl tooth at the position shown; windows every 10 mm
WIN_Z = (4.4, 8.6)


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
    half_p = p / 4
    teeth = []
    k0 = int(math.floor((x0 - x_tooth) / p)) + 1
    k1 = int(math.floor((x1 - x_tooth) / p)) - 1
    for k in range(k0, k1 + 1):
        c = x_tooth + k * p
        a, b = half_p + (zp - zr) * math.tan(pa), half_p - (zt - zp) * math.tan(pa)
        teeth.append(Polygon([(c - a, zr - 0.01), (c - b, zt), (c + b, zt), (c + a, zr - 0.01)]))
    return unary_union([box(x0, z_bot, x1, zr)] + teeth)


def outline():
    H0n, H1n = -7.5, 23.5
    dx = G.raked_dx(H1n - H0n)
    top = G.spline([(dx, H1n), (42, 25.0), (66, 26.2), (WX, 26.6), (112, 26.0), (140, 23.6), (164, 20.4), (179.5, 19.0)])
    xb = 179.5 - G.raked_dx(19.0 + 11.0)
    bot = G.spline([(xb, -11.0), (140, -11.9), (112, -11.5), (84, -9.6), (56, -7.7), (30, -7.0), (0, H0n)])
    base = Polygon(top + bot)
    fender = G.circle(WX, WZ, 15.6)                         # covers the pinion on the back half
    return G.round_corners(unary_union([base, fender]), 6.4, 7.0), xb


def build(explode=False, cut_y=None):
    """Parts in assembled position; explode=True spreads them for the exploded view.
    cut_y removes everything above that y (cutaway through the gear layer)."""
    out, xb = outline()
    # back edge modest (the blade runs 2.9 mm inside that wall); palm side fuller
    solid = G.xz_solid(out, -T / 2, T / 2, (4.2, 3.6), (5.2, 5.2))

    # ---- body ---------------------------------------------------------------------
    split = xb + 11.0 / math.tan(G.RAKE) - 12.0             # raked tail-cap line (x at z = 0)
    body = solid - G.xz_prism(G.half_plane_raked(split - 0.18, +1), -30, 30)
    body = body - G.cube(-5, 27, BY - 0.35, BY + 0.35, -0.35, 18.35)                 # blade mouth
    body = body - G.cube(25, 220, Y_WALL, Y_GEAR[1] + 0.2, -0.6, 18.6)               # carriage + rack channel
    body = body - G.cyl_y(WX, WZ, M * Z / 2 + M + 0.6, Y_FL[0] - 0.2, Y_DISC[0], 96)  # pinion bay
    body = body - G.cyl_y(WX, WZ, WR + 0.5, Y_DISC[0] - 0.1, T, 160)                  # wheel bay = journal
    for k in range(9):                                                   # lock witness windows
        x = PAWL_X + 10 - 10 * k
        w = G.round_corners(box(x - 1.7, WIN_Z[0] - 0.2, x + 1.7, WIN_Z[1] + 0.2), 0.5)
        body = body - G.xz_solid(w, -T / 2, Y_WALL, 0.5, 0, flare=True, step=0.15)

    # ---- tail cap -------------------------------------------------------------------
    cap = solid ^ G.xz_prism(G.half_plane_raked(split + 0.18, +1), -30, 30)
    cap = G.union([cap, G.cube(split - 7, split + 3, Y_WALL + 0.3, Y_GEAR[1] - 0.1, -0.3, 18.3)])
    cap = cap - G.cube(split - 8, 173.5, Y_GEAR[0] - 0.4, Y_GEAR[1] + 0.3, RACK_Z - 6.4, RACK_Z + M + 0.8)

    # ---- wheel: disc + pinion + flange ----------------------------------------------
    y0, y1 = Y_DISC
    disc = G.fluted_wheel_xz(WX, WZ, WR, y0 + 2.4, y1, 40, flute_r=0.85, edge=1.0)
    disc = G.union([disc, G.cyl_y(WX, WZ, WR, y0, y0 + 2.5, 160)])                   # smooth journal band
    disc = disc - (G.cyl_y(WX, WZ, WR - 3.2, y1 - 0.7, y1 + 2, 128) - G.cyl_y(WX, WZ, 7.0, y1 - 2, y1 + 3, 96))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        disc = disc - G.cyl_y(WX + 12.0 * math.cos(a), WZ + 12.0 * math.sin(a), 0.9, y1 - 1.3, y1 + 2, 32)
    disc = disc - G.cyl_y(WX, WZ, 2.4, y1 - 1.0, y1 + 2, 48)
    pin = G.xz_prism(pinion_poly(WX, WZ, phase=-math.pi / 2 + math.pi / Z), Y_GEAR[0], y0 + 0.05)
    flange = G.cyl_y(WX, WZ, M * Z / 2 - 0.2, Y_FL[0], Y_FL[1] + 0.05, 96)
    wheel = G.union([disc, pin, flange])

    # ---- shuttle (rack) ----------------------------------------------------------------
    rack = G.xz_prism(rack_poly(74.0, 162.0, RACK_Z - 6.0), Y_GEAR[0] + 0.1, Y_GEAR[1] - 0.1)
    paddle = G.cube(100.0, 106.0, -7.6, Y_GEAR[0] + 1.0, 1.2, RACK_Z - 5.9)
    shuttle = G.union([rack, paddle])

    # ---- carriage with pawl ---------------------------------------------------------------
    tail = TIP + G.BLADE_L
    block = G.cube(tail, tail + 24.5, Y_WALL + 0.1, Y_CARR, 0.0, 18.0)
    plate = G.cube(tail - 12.5, tail + 0.1, BY + 0.3, Y_CARR, 0.2, 17.8)
    lug = G.cyl_y(tail - 7.0, 9.0, 1.95, BY - 0.3, BY + 0.4, 32)
    carriage = G.union([block, plate, lug])
    carriage = carriage - G.cube(97.0, 109.0, -8.0, Y_CARR + 1, 0.8, RACK_Z - 5.6)            # lost-motion pocket
    for z in (WIN_Z[0] - 0.6, WIN_Z[1] + 0.1):                                             # U-slit round the pawl arm
        carriage = carriage - G.cube(tail + 2.5, PAWL_X + 2.3, Y_WALL - 1, -7.5, z, z + 0.5)
    carriage = carriage - G.cube(PAWL_X + 1.8, PAWL_X + 2.3, Y_WALL - 1, -7.5, WIN_Z[0] - 0.6, WIN_Z[1] + 0.6)
    tooth = G.cube(PAWL_X - 1.45, PAWL_X + 1.45, -T / 2 + 0.5, Y_WALL + 0.2, WIN_Z[0], WIN_Z[1])
    carriage = G.union([carriage, tooth])

    blade = G.blade(TIP, BY)

    parts = dict(body=(body, "graphite"), tail_cap=(cap, "graphite"), wheel=(wheel, "orange"),
                 shuttle=(shuttle, "graphite2"), carriage=(carriage, "orange"), blade=(blade, "blade"))
    off = dict(body=(0, 0, 0), tail_cap=(0, 0, 0), wheel=(0, 0, 0), shuttle=(0, 0, 0), carriage=(0, 0, 0), blade=(0, 0, 0))
    if explode:
        off = dict(body=(0, 0, 0), tail_cap=(30, 0, 0), wheel=(0, 34, 46), shuttle=(34, 0, -40),
                   carriage=(34, 0, -68), blade=(14, 0, -68))
    res = []
    for k, (m, mat) in parts.items():
        if cut_y is not None and k in ("body", "tail_cap", "wheel"):
            m = m ^ G.cube(-50, 300, -50, cut_y, -80, 120)
        res.append((k, m.translate(list(off[k])), mat))
    anchors = dict(body=(50, -T / 2, 12), tail_cap=(170, -T / 2, 6), wheel=(WX, Y_FL[0], WZ),
                   shuttle=(130, Y_GEAR[0], RACK_Z - 3), carriage=(PAWL_X, -T / 2, 6.5), blade=(40, BY, 9))
    anchors = {k: tuple(np.add(v, off[k])) for k, v in anchors.items()}
    return dict(key="orbit2", code="02", name="ORBIT", parts=res, thick=T, anchors=anchors,
                detail=(WX - 6, 6, WZ + 2))
