"""
The three concepts as solids.  Each builder returns
    dict(name, parts=[(part_name, Manifold, material_key)], notes about pose / camera targets)
Internals are modelled only as far as they are visible; this is a form + architecture study,
not print-ready CAD.
"""

import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from . import geom as G

TIP = -9.5        # blade tip x with one segment deployed


# =====================================================================================
# 01  KEEL - raked monocoque slab, press-to-slide sled, steel pin in a notch ladder
# =====================================================================================
def keel():
    H0, H1, L, T = -7.5, 27.0, 158.0, 12.0
    dx = G.raked_dx(H1 - H0)
    x_at = lambda z: (z - H0) / math.tan(G.RAKE)            # nose face x at height z
    outline = G.round_corners(Polygon([(0, H0), (L, H0), (L + dx, H1), (dx, H1)]), 2.2)
    solid = G.xz_solid(outline, -T / 2, T / 2, 1.5, 1.5)

    # tail cap: an 8 mm raked slice that slides out sideways
    split = L - 8.0 + (0 - H0) / math.tan(G.RAKE)           # raked line through z = 0
    body = solid - G.xz_prism(G.half_plane_raked(split - 0.18, +1), -20, 20)
    cap = solid ^ G.xz_prism(G.half_plane_raked(split + 0.18, +1), -20, 20)
    cap = cap - G.cube(L - 3, L + 40, -0.45, 0.45, 3.5, 15.5)       # blade-snapper slit

    # blade channel and nose mouth
    body = body - G.cube(-5, L - 12, -0.5, 0.5, -0.35, 18.35)

    # notch ladder: free channel + nine notches at one-segment pitch, through both walls
    N0, SLED = 34.0, 104.0                                   # first notch, sled position shown
    comb = unary_union([box(N0 - 3.6, 19.4, N0 + 8 * G.SEG + 3.6, 21.9)] +
                       [box(N0 + k * G.SEG - 1.7, 21.5, N0 + k * G.SEG + 1.7, 24.5) for k in range(9)])
    comb = G.round_corners(comb, 0.6, 0.35)
    body = body - G.xz_solid(comb, -T / 2, T / 2, 0.5, 0.5, flare=True, step=0.15)
    # sled slot in the spine
    body = body - G.z_solid(G.stadium(N0 - 2, N0 + 8 * G.SEG + 6, 0, 1.7), 19.0, 40.0)

    parts = []
    # nose bolts (steel, clamp the mouth above and below the blade)
    for (x, z) in [(x_at(23.0) + 6.3, 23.0), (x_at(-3.9) + 5.2, -3.9)]:
        bore, head = G.screw_head(x, z, T / 2, +1, r=2.45)
        body = body - bore
        parts.append(("bolt", head, "oxide"))

    # sled: graphite saddle with an orange press button; steel cross-pin in the ladder
    sz0, sz1 = H1 + 0.3, H1 + 4.3
    sdx = G.raked_dx(sz1 - sz0)
    saddle = G.xz_solid(G.round_corners(Polygon([(SLED - 14, sz0), (SLED + 12, sz0),
                                                 (SLED + 12 + sdx, sz1), (SLED - 14 + sdx, sz1)]), 1.0),
                        -T / 2, T / 2, 1.2, 1.2)
    saddle = G.union([saddle, G.cube(SLED - 6, SLED + 6, -1.4, 1.4, 19.5, sz0 + 1)])
    bx = SLED + sdx * 0.5 - 1.0
    saddle = saddle - G.z_solid(G.stadium(bx - 4.2, bx + 4.2, 0, 3.55), sz1 - 3.0, sz1 + 2)
    button = G.z_solid(G.stadium(bx - 4.2, bx + 4.2, 0, 3.3), sz1 - 3.0, sz1 + 1.9, 0, (1.6, 0.9))
    pin = G.cyl_y(SLED, 23.0, 1.5, -T / 2 + 0.4, T / 2 - 0.4, 48)

    parts += [("body", body, "graphite"), ("tail_cap", cap, "orange"), ("saddle", saddle, "graphite2"),
              ("button", button, "orange"), ("lock_pin", pin, "steel"), ("blade", G.blade(TIP), "blade")]
    return dict(key="keel", code="01", name="KEEL", parts=parts, thick=T,
                detail=(SLED - 14, 0, 25), detail2=(8, 0, 9))


# =====================================================================================
# 02  ORBIT - stationary geared thumb wheel, rack-driven blade, hex index lock
# =====================================================================================
def orbit():
    T = 20.0
    H0n, H1n = -7.5, 23.0
    dx = G.raked_dx(H1n - H0n)
    # Rack layout fixes the wheel position: the pinion must stay on the rack from "retracted"
    # to "last segment" (82 mm) without the rack ever leaving the nose -> axis ~88 mm back.
    WX, WZ, WR = 88.0, 21.6, 19.5
    top = G.spline([(dx, H1n), (45, 24.6), (70, 25.4), (WX, 25.8), (112, 25.0), (140, 20.5), (162, 12.5),
                    (171.5, 3.0), (168, -6.5), (152, -11.5), (124, -12.6), (92, -10.6), (60, -7.6), (34, -6.6),
                    (14, -7.3), (0, H0n)])
    outline = G.round_corners(Polygon(top), 2.4)
    edge = (6.5, 3.4)
    solid = G.xz_solid(outline, -T / 2, T / 2, edge, edge)

    BY = -6.3                                               # blade plane: the gear train sits beside it
    WY0, WY1 = 2.2, T / 2 + 0.4                             # wheel: thumb-side, face just proud of the shell

    body = solid - G.cube(-5, 122, BY - 0.5, BY + 0.5, -0.35, 18.35)
    body = body - G.cyl_y(WX, WZ, WR + 0.9, WY0 - 0.7, T, 160)       # wheel bay, open on the +Y face
    body = body - G.perimeter_groove(outline, 0.0)
    cx = 150.0                                              # tail-cap line
    sl = solid ^ G.cube(cx - 0.17, cx + 0.17, -30, 30, -40, 60)
    lo, hi = G.bbox(sl)
    c = (lo + hi) / 2
    inner = sl.translate(list(-c)).scale([1.0, (T - 0.8) / T, (hi[2] - lo[2] - 0.8) / (hi[2] - lo[2])]).translate(list(c))
    body = body - (sl - inner)

    parts = []
    wheel = G.fluted_wheel_xz(WX, WZ, WR, WY0, WY1, 40, flute_r=0.85, edge=1.0)
    wheel = wheel  # 40 flutes: grip only
    # face: shallow dish between rim and hub, hex socket for the index lock
    dish = G.xz_solid(G.circle(WX, WZ, WR - 3.2).difference(G.circle(WX, WZ, 9.0)).buffer(-0.01), 0, 1)\
        if False else None
    ring = G.cyl_y(WX, WZ, WR - 3.2, WY1 - 0.7, WY1 + 2, 128) - G.cyl_y(WX, WZ, 9.2, WY1 - 2, WY1 + 3, 96)
    wheel = wheel - ring
    wheel = wheel - G.cyl_y(WX, WZ, 5.75, WY0 - 1, WY1 + 2, 6)
    # six index marks on the dish, one per lock position
    for k in range(6):
        a = math.radians(30 + 60 * k)
        wheel = wheel - G.cyl_y(WX + 12.7 * math.cos(a), WZ + 12.7 * math.sin(a), 0.9, WY1 - 1.3, WY1 + 2, 32)
    hexb = G.xz_solid(Polygon([(WX + 5.5 * math.cos(a), WZ + 5.5 * math.sin(a))
                               for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]).buffer(-0.6).buffer(0.6),
                      WY0, WY1 + 1.1, 0, 0.7)
    bore, axle = G.screw_head(WX, WZ, -T / 2, -1, r=3.4, depth=2.6)
    body = body - bore
    parts.append(("axle", axle, "oxide"))

    for (x, z) in [(9.3, -4.3), (27.5, 20.6), (124.0, -8.6), (160.0, 3.5)]:
        bore, head = G.screw_head(x, z, T / 2, +1, r=2.45, depth=3.0)
        body = body - bore
        parts.append(("bolt", head, "oxide"))

    parts += [("body", body, "graphite"), ("wheel", wheel, "orange"), ("hex_button", hexb, "graphite2"),
              ("blade", G.blade(TIP, BY), "blade")]
    return dict(key="orbit", code="02", name="ORBIT", parts=parts, thick=T,
                detail=(WX - 6, 6, WZ + 2), detail2=(8, 0, 9))


# =====================================================================================
# 03  LOOP - guard frame with a 40-degree skid, toothed carriage clamped by a wheel
# =====================================================================================
def loop():
    TS, TF = 14.0, 10.0                                     # spine and frame thickness
    H0, H1, L = -6.5, 27.0, 158.0
    dx = G.raked_dx(H1 - H0)
    sk = math.tan(math.radians(40.0))
    ZB = -46.0
    xb = (H0 - ZB) / sk                                     # where the skid meets the lower bar
    heel = [(L - 16 + 16 * math.cos(a), ZB + 16 + 16 * math.sin(a)) for a in np.linspace(-math.pi / 2, 0, 16)]
    outer = G.round_corners(Polygon([(dx, H1), (L, H1)] + heel[::-1] + [(xb, ZB), (0, H0)]), 3.0)
    off = 9.5 / math.cos(math.radians(40.0))
    zi = ZB + 9.0
    opening = Polygon([((H0 + off - H0) / sk, H0), (L - 10.5, H0), (L - 10.5, zi), ((H0 + off - zi) / sk, zi)])
    opening = G.round_corners(opening, 7.5)
    spine2d = G.round_corners(Polygon([(0, H0), (L, H0), (L, H1), (dx, H1)]), 3.0)

    frame = G.xz_solid(outer, -TF / 2, TF / 2, 2.6, 2.6) - \
        G.xz_solid(opening, -TF / 2, TF / 2, 2.6, 2.6, flare=True)
    spine = G.xz_solid(spine2d, -TS / 2, TS / 2, (4.5, 3.0), (4.5, 3.0))
    solid = G.union([frame, spine])

    body = solid - G.cube(-5, 126, -0.5, 0.5, -0.35, 18.35)
    body = body - G.perimeter_groove(outer.difference(opening), 0.0)

    # clamp wheel: rail land + slot on the +Y face; wheel rides with the carriage
    CZ, WXP = 9.0, 92.0
    X0, X1 = 22.0, 102.0
    body = body - G.xz_solid(G.stadium(X0, X1, CZ, 7.2), TS / 2 - 1.0, TS / 2 + 3, 0, 0)
    body = body - G.xz_solid(G.stadium(X0, X1, CZ, 2.2), 1.5, TS / 2 + 3, 0, 0)
    wheel = G.fluted_wheel_xz(WXP, CZ, 11.0, TS / 2 - 0.7, TS / 2 + 5.6, 24, flute_r=0.9, edge=0)
    wheel = wheel ^ G.xz_solid(G.circle(WXP, CZ, 11.6), TS / 2 - 0.7, TS / 2 + 5.6, 0, (1.6, 1.2))
    wheel = wheel - G.cyl_y(WXP, CZ, 4.0, TS / 2 + 4.6, TS / 2 + 8, 64)
    nut = G.cyl_y(WXP, CZ, 3.5, TS / 2 + 3.0, TS / 2 + 5.2, 6) - G.cyl_y(WXP, CZ, 1.55, TS / 2 + 4.4, TS / 2 + 8, 32)
    stud = G.cyl_y(WXP, CZ, 1.5, TS / 2 + 3.0, TS / 2 + 5.0, 32)
    stem = G.cyl_y(WXP, CZ, 2.0, 2.0, TS / 2, 32)

    parts = [("nut", nut, "steel"), ("stud", stud, "steel"), ("stem", stem, "oxide")]
    xn = lambda z: (z - H0) / math.tan(G.RAKE)
    for (x, z, yf) in [(xn(-3.0) + 6.0, -3.0, TS / 2), (xn(23.0) + 6.5, 23.0, TS / 2), (150.5, 20.5, TS / 2)]:
        bore, head = G.screw_head(x, z, yf, +1, r=2.45, depth=2.8)
        body = body - bore
        parts.append(("bolt", head, "oxide"))
    for (x, z) in [(26.0, -22.5), (L - 7.0, ZB + 9.5)]:
        bore, head = G.screw_head(x, z, TF / 2, +1, r=2.45, depth=2.6)
        body = body - bore
        parts.append(("bolt", head, "oxide"))

    parts += [("body", body, "graphite"), ("clamp_wheel", wheel, "orange"), ("blade", G.blade(TIP), "blade")]
    return dict(key="loop", code="03", name="LOOP", parts=parts, thick=TS,
                detail=(WXP - 18, 4, CZ), detail2=(10, 0, -6))


ALL = [keel, orbit, loop]
