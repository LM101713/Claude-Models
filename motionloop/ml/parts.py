"""
Part builders. Each returns one closed solid (bpy object) in its reference frame:

    plinth                         assembly frame
    wheel, cheek, cap, handle      assembly frame at crank angle 0 (pin A at +X)
    knob_sleeve                    assembly frame at crank angle 0
    rod                            local: big end at the origin, small end at (+ROD_L, 0, 0),
                                   centred on y = 0
    slider, pin                    the RIGHT slider's frame with the wrist pin axis at x = 0
"""

import math

from mathutils import Matrix

from . import geom as G
from .params import P, D


def _disc_y(name, cx, cz, r, y0, y1, c0, c1, seg=None):
    seg = seg or P.SEG
    return G.loft_y(name, G.chamfer_rings(lambda i: G.circle(cx, cz, r - i, seg), y0, y1, c0, c1))


def _hole_y(name, poly_fn, y0, y1, c0=0.0, c1=0.0, ext=1.0):
    """Cutter along Y from y0 to y1 (y0 < y1) with mouth chamfers c0 / c1 (negative inset =
    flare); extended `ext` beyond a chamfered (open) end."""
    rings = []
    if c0 > 0:
        rings += [(y0 - ext, poly_fn(-c0 - ext)), (y0 + c0, poly_fn(0.0))]
    else:
        rings.append((y0, poly_fn(0.0)))
    if c1 > 0:
        rings += [(y1 - c1, poly_fn(0.0)), (y1 + ext, poly_fn(-c1 - ext))]
    else:
        rings.append((y1, poly_fn(0.0)))
    return G.loft_y(name, rings)


# =====================================================================================
# Frame
# =====================================================================================


def plinth_outline(inset=0.0):
    base = G.superellipse_rect(P.L / 2, P.W / 2, P.CORNER_R, P.CORNER_N, 0.0, 16)
    return G.offset_convex(base, inset) if inset else G.ccw(base)


def plinth_rings(top):
    R = P.TOP_R
    c = P.FOOT_CHAMFER
    rings = [(0.0, plinth_outline(c)), (c, plinth_outline(0.0))]
    for i in range(7):
        a = math.radians(90 * i / 6)
        z = top - R + R * math.sin(a)
        rings.append((z, plinth_outline(R - R * math.cos(a))))
    return rings


def tower_profile(inset=0.0, zb=None):
    """XZ outline of a tower: straight sides, semicircular top about the axle."""
    hw = P.TOWER_HW - inset
    zb = D["PLINTH_TOP"] - 1.0 if zb is None else zb
    pts = [(hw, zb)] + G.arc(0.0, P.AXLE_Z, hw, 0.0, math.pi, 32) + [(-hw, zb)]
    return pts


def groove_profile(yc, top):
    """Dovetail groove cross-section as (z, y) points, centred on y = yc."""
    nk, fl = P.GROOVE_NECK_HW, P.GROOVE_FLARE_HW
    z_neck = top - P.GROOVE_NECK_H
    z_flare = z_neck - (fl - nk)
    z_floor = z_flare - 0.5
    half = [(top + 1.0, nk + 1.4), (top - 0.4, nk), (z_neck, nk), (z_flare, fl), (z_floor, fl)]
    pts = [(z, yc + y) for z, y in half] + [(z, yc - y) for z, y in reversed(half)]
    return pts


def build_plinth(variant_ticks=True):
    top = D["PLINTH_TOP"]
    pl = G.loft("ML02_Frame", plinth_rings(top))
    cutters = []
    # dovetail grooves: right slider centred at +SLIDER_YC, left at -SLIDER_YC.
    # (Overlapping cutters must be cut one at a time; only disjoint ones are merged.)
    yc = D["SLIDER_YC"]
    G.cut(pl, G.prism_x("groove_r", groove_profile(yc, top), P.PIT_X - 1.0, P.L / 2 + 2))
    G.cut(pl, G.prism_x("groove_l", groove_profile(-yc, top), -P.L / 2 - 2, -P.PIT_X + 1.0))
    # travel scale: one tick per 2 mm over the stroke, where the slider's outer end passes
    if variant_ticks:
        s0, s1 = D["PIN_STROKE"]
        n = int(round((s1 - s0) / P.TICK_PITCH)) + 1
        for side in (1, -1):
            for k in range(n):
                x = side * (s0 + P.SLIDER_U[1] + k * P.TICK_PITCH)
                long_ = k in (0, n - 1, (n - 1) // 2)
                y_in = 8.6
                y_out = y_in + (3.0 if long_ else 1.8)
                # the scale sits on the side of the slider away from its rod
                ys = (y_in, y_out) if side > 0 else (-y_out, -y_in)
                cutters.append(G.prism("tick", G.rrect(x - 0.25, x + 0.25, ys[0], ys[1], 0.2, 3),
                                       top - 0.4, top + 1))
    G.cut(pl, G.join_cutters("frame_cuts", cutters))
    # engraving on the underside (mirrored so it reads from below)
    txt = [G.text_solid("t1", "ODD LAYER", 5.0, -1, 0.6, cx=0, cy=4.0, mirror_x=True, spacing=1.15, rot=0.002),
           G.text_solid("t2", "ML-02  MOTIONLOOP", 3.2, -1, 0.6, cx=0, cy=-3.5, mirror_x=True,
                        spacing=1.1, rot=0.002)]
    # (the 0.1-degree twist avoids an axis-aligned degeneracy in the 'T' glyph that leaves the
    # exact boolean with open edges)
    G.cut(pl, G.join_cutters("engrave", txt))
    # towers, built 2.5 mm too long inward; the pit cut then trims them to their inner face
    towers, bosses = [], []
    for s in (1, -1):
        y_in, y_out = D["Y_TOWER0"] - 2.5, D["Y_TOWER1"]  # trimmed back to Y_TOWER0 by the pit
        if s > 0:
            rings = [(y_in, tower_profile()), (y_out - 0.6, tower_profile()), (y_out, tower_profile(0.6))]
        else:
            rings = [(-y_out, tower_profile(0.6)), (-y_out + 0.6, tower_profile()), (-y_in, tower_profile())]
        towers.append(G.loft_y("tower", rings))
        # thrust boss on the inner face
        yb = D["Y_BOSS"]
        if s > 0:
            b = _disc_y("boss", 0.0, P.AXLE_Z, P.THRUST_RING_R[1], yb, yb + 1.0, 0.15, 0.0)
        else:
            b = _disc_y("boss", 0.0, P.AXLE_Z, P.THRUST_RING_R[1], -yb - 1.0, -yb, 0.0, 0.15)
        bosses.append(b)
    G.union(pl, G.join_cutters("towers", towers))
    # crank pit: its Y walls are the towers' inner faces; its X ends get a 0.6 top chamfer
    hy = D["Y_TOWER0"]
    e = P.PIT_EDGE
    x0 = P.PIT_X
    pit = G.loft("pit", [(P.PIT_FLOOR, G.rrect(-x0, x0, -hy, hy, 3.0)),
                         (top - e, G.rrect(-x0, x0, -hy, hy, 3.0)),
                         (top + 1.0, G.rrect(-x0 - e - 1, x0 + e + 1, -hy, hy, 3.0)),
                         (D["TOWER_TOP"] + 2, G.rrect(-x0 - e - 1, x0 + e + 1, -hy, hy, 3.0))])
    G.cut(pl, pit)
    G.union(pl, G.join_cutters("bosses", bosses))
    # bearing bores (teardrop roof, chamfered mouths)
    rb = P.BORE_D / 2
    bores = []
    for s in (1, -1):
        y0, y1 = D["Y_BOSS"], D["Y_TOWER1"]
        lo, hi = (y0, y1) if s > 0 else (-y1, -y0)
        bores.append(_hole_y("bore", lambda i: G.teardrop(0.0, P.AXLE_Z, rb - i, 48), lo, hi, 0.4, 0.4))
    G.cut(pl, G.join_cutters("bores", bores))
    return pl


# =====================================================================================
# Crank: wheel, cheeks, cap, handle, knob
# =====================================================================================


def _d_hole(cx, depth_from, depth_to, flat_angle):
    r = P.SPIGOT_D / 2 + P.KEY
    fl = P.SPIGOT_FLAT + P.KEY
    lo, hi = min(depth_from, depth_to), max(depth_from, depth_to)
    return G.prism_y("dhole", G.d_shape(cx, P.AXLE_Z, r, fl, flat_angle, 48), lo, hi)


def build_wheel(shuttle=False):
    name = "ML02_Wheel_Shuttle" if shuttle else "ML02_Wheel_Mirror"
    hw = D["Y_WHEEL"]
    w = _disc_y(name, 0.0, P.AXLE_Z, P.WHEEL_R, -hw, hw, P.WHEEL_EDGE, P.WHEEL_EDGE, 96)
    dep = P.SPIGOT_HOLE_DEPTH
    cuts = [_d_hole(P.CRANK_R, hw - dep, hw + 1, math.pi)]  # pin A hole, +Y face
    if shuttle:
        cuts.append(_d_hole(P.CRANK_R, -hw - 1, -hw + dep + 0.05, math.pi))
    else:
        cuts.append(_d_hole(-P.CRANK_R, -hw - 1, -hw + dep, 0.0))
    r0, r1, wd, dp = P.WHEEL_INDEX
    angles = (math.pi / 2, -math.pi / 2) if shuttle else (math.pi / 2,)
    for a in angles:
        for s in (1, -1):
            slot = G.rrect(r0, r1, -wd / 2, wd / 2, wd / 2 - 0.01, 4)
            rot = [(x * math.cos(a) - y * math.sin(a), P.AXLE_Z + x * math.sin(a) + y * math.cos(a))
                   for x, y in slot]
            lo, hi = (hw - dp, hw + 1) if s > 0 else (-hw - 1, -hw + dp)
            cuts.append(G.prism_y("index", rot, lo, hi))
    for c in cuts:  # one at a time: the shuttle's two D-holes meet mid-wheel
        G.cut(w, c)
    return w


def build_cheek():
    """Cheek A (on +Y), with its crank pin at +X pointing toward the wheel."""
    y0, y1 = D["Y_CHEEK0"], D["Y_CHEEK1"]
    ch = _disc_y("ML02_Cheek", 0.0, P.AXLE_Z, P.CHEEK_R, y0, y1, P.CHEEK_EDGE, P.CHEEK_EDGE, 96)
    rp = P.PIN_D / 2
    f = P.PIN_ROOT_F
    yw = D["Y_WHEEL"]
    x = P.CRANK_R
    pin = G.loft_y("pin", [(yw, G.circle(x, P.AXLE_Z, rp - 0.3, 48)),
                           (yw + 0.3, G.circle(x, P.AXLE_Z, rp, 48)),
                           (y0 - f, G.circle(x, P.AXLE_Z, rp, 48)),
                           (y0, G.circle(x, P.AXLE_Z, rp + f, 48)),
                           (y0 + 0.5, G.circle(x, P.AXLE_Z, rp + f, 48))])
    r = P.SPIGOT_D / 2
    fl = P.SPIGOT_FLAT

    def dpoly(i):
        return G.d_shape(x, P.AXLE_Z, r - i, fl - i, math.pi, 40)

    sp = G.loft_y("spigot", [(yw - P.SPIGOT_L, dpoly(0.3)), (yw - P.SPIGOT_L + 0.3, dpoly(0.0)),
                             (yw + 0.2, dpoly(0.0))])
    G.union(ch, pin, sp)
    af = P.HEX_AF + P.HEX_PRESS

    def hexp(i):
        return G.hexagon(0.0, P.AXLE_Z, af - 2 * i)

    sock = G.loft_y("socket", [(D["Y_HEX_TIP"], hexp(0)), (y1 - 0.4, hexp(0)), (y1 + 1.0, hexp(-1.4))])
    G.cut(ch, sock)
    return ch


def _shaft(name, y_face, y_end, s):
    """Journal from y_face (shoulder side) to the cheek face, then the hex drive.
    s = +1 for the cap side, -1 for the handle side."""
    rj = P.JOURNAL_D / 2
    yc = s * D["Y_CHEEK1"]
    yt = s * D["Y_HEX_TIP"]
    j = G.prism_y(name, G.circle(0.0, P.AXLE_Z, rj, 48), min(y_face, yc), max(y_face, yc))

    def hexp(i):
        return G.hexagon(0.0, P.AXLE_Z, P.HEX_AF - 2 * i)

    if s > 0:
        rings = [(yt, hexp(0.3)), (yt + 0.3, hexp(0)), (yc + 0.2, hexp(0))]
    else:
        rings = [(yc - 0.2, hexp(0)), (yt - 0.3, hexp(0)), (yt, hexp(0.3))]
    G.union(j, G.loft_y("hex", rings))
    return j


def build_cap():
    y0 = D["Y_CAP0"]
    rh = P.CAP_D / 2
    cap = _disc_y("ML02_Cap", 0.0, P.AXLE_Z, rh, y0, y0 + P.CAP_T, 0.2, 0.5, 64)
    G.union(cap, _shaft("shaft", y0 + 0.2, 0, +1))
    # engraved ring on the outer face: an annular cutter (outer cylinder minus inner)
    ring = _disc_y("ring", 0.0, P.AXLE_Z, 3.9, y0 + P.CAP_T - 0.3, y0 + P.CAP_T + 1, 0, 0, 48)
    G.cut(ring, _disc_y("ring_in", 0.0, P.AXLE_Z, 3.4, y0 + P.CAP_T - 1, y0 + P.CAP_T + 2, 0, 0, 48))
    G.cut(cap, ring)
    return cap


def handle_outline(i=0.0):
    pts = G.link_outline(P.HANDLE_R, P.ARM_HUB_R - i, P.ARM_TIP_R - i, 4.2 - i, 3.6 - i, 5.0 + i)
    return [(x, P.AXLE_Z + z) for x, z in pts]


def build_handle():
    a0, a1 = D["Y_ARM0"], D["Y_ARM1"]
    arm = G.loft_y("ML02_Handle", G.chamfer_rings(handle_outline, -a1, -a0, 0.6, 0.6))
    sp = _disc_y("spacer", 0.0, P.AXLE_Z, P.HUB_SPACER_D / 2, -a0 - 0.1, -D["Y_SPACER0"], 0.0, 0.3, 64)
    G.union(arm, sp, _shaft("shaft", -D["Y_SPACER0"] - 0.2, 0, -1))
    # knob pin press hole, blind: the pin bottoms out with the knob sleeve free to spin
    depth = P.PIN_SHANK_L - P.KNOB_L - P.AXIAL
    hole = _hole_y("kh", lambda i: G.circle(P.HANDLE_R, P.AXLE_Z, P.WRIST_D / 2 + P.PRESS / 2 - i, 40),
                   -a1, -a1 + depth, 0.3, 0.0)
    G.cut(arm, hole)
    return arm


def knob_head_y():
    """Inner face of the knob pin's head."""
    return -D["Y_ARM1"] - P.AXIAL - P.KNOB_L


def knob_y():
    """Sleeve ends, modelled mid-play (AXIAL/2 from the arm and from the pin head)."""
    y0 = knob_head_y() + P.AXIAL / 2
    return y0, y0 + P.KNOB_L


def build_knob():
    y0, y1 = knob_y()
    ro = P.KNOB_OD / 2
    ri = (P.WRIST_D + P.RUN_DIA) / 2
    k = G.loft_y("ML02_Knob", [(y0, G.circle(P.HANDLE_R, P.AXLE_Z, ro - 0.8, 64)),
                               (y0 + 0.25, G.circle(P.HANDLE_R, P.AXLE_Z, ro - 0.35, 64)),
                               (y0 + 0.8, G.circle(P.HANDLE_R, P.AXLE_Z, ro, 64)),
                               (y1 - 0.5, G.circle(P.HANDLE_R, P.AXLE_Z, ro, 64)),
                               (y1, G.circle(P.HANDLE_R, P.AXLE_Z, ro - 0.5, 64))])
    G.cut(k, _hole_y("kb", lambda i: G.circle(P.HANDLE_R, P.AXLE_Z, ri - i, 40), y0, y1, 0.3, 0.3))
    return k


# =====================================================================================
# Rod, slider, pin
# =====================================================================================


def rod_outline(i=0.0):
    hb, hs = P.ROD_SHANK_HW
    return G.link_outline(P.ROD_L, P.ROD_BIG_R - i, P.ROD_SMALL_R - i, hb - i, hs - i, P.ROD_FILLET + i)


def build_rod():
    t = P.ROD_T / 2
    e = P.ROD_EDGE
    rod = G.loft_y("ML02_Rod", G.chamfer_rings(rod_outline, -t, t, e, e))
    rb = (P.PIN_D + P.RUN_DIA) / 2
    rs = (P.WRIST_D + P.RUN_DIA) / 2
    c = [_hole_y("bb", lambda i: G.circle(0.0, 0.0, rb - i, 48), -t, t, e, e),
         _hole_y("sb", lambda i: G.circle(P.ROD_L, 0.0, rs - i, 40), -t, t, e, e)]
    G.cut(rod, G.join_cutters("rod_bores", c))
    return rod


def slider_profile(i=0.0):
    u0, u1 = P.SLIDER_U
    rt, rb = P.SLIDER_CORNER
    return G.rrect2(u0 + i, u1 - i, D["SLIDER_Z0"] + i, P.SLIDER_TOP - i, rt - i, max(rb - i, 0.2))


def key_profile():
    """Dovetail key (z, y) for the right slider, matching groove_profile with clearances."""
    top = D["PLINTH_TOP"]
    yc = D["SLIDER_YC"]
    nk = P.GROOVE_NECK_HW - P.SLIDE
    z_neck = top - P.GROOVE_NECK_H
    off = P.DOVE * math.sqrt(2)
    fl = P.GROOVE_FLARE_HW - P.SLIDE
    # key flare line: hw(z) = GROOVE_NECK_HW + (z_neck - z) - off
    z_a = z_neck + P.GROOVE_NECK_HW - off - nk
    z_b = z_neck + P.GROOVE_NECK_HW - off - fl
    z_floor = z_neck - (P.GROOVE_FLARE_HW - P.GROOVE_NECK_HW) - 0.5 + P.GROOVE_FLOOR_GAP
    half = [(D["SLIDER_Z0"] + 1.0, nk), (z_a, nk), (z_b, fl), (z_floor, fl)]
    return [(z, yc + y) for z, y in half] + [(z, yc - y) for z, y in reversed(half)]


def build_slider():
    y0, y1 = P.SLIDER_Y
    e = P.SLIDER_EDGE
    sl = G.loft_y("ML02_Slider", G.chamfer_rings(slider_profile, y0, y1, e, e))
    G.union(sl, G.prism_x("key", key_profile(), P.KEY_U[0], P.KEY_U[1]))
    rp = (P.WRIST_D + P.PRESS) / 2
    # blind press bore from the rod side: the pin bottoms out exactly at its design depth,
    # so it cannot be pushed far enough to clamp the rod
    y_end = -D["Y_WRIST_HEAD0"] + P.PIN_SHANK_L
    G.cut(sl, _hole_y("wh", lambda i: G.circle(0.0, P.AXLE_Z, rp - i, 40), y0, y_end, 0.4, 0.0))
    return sl


def build_pin():
    """Wrist pin for the right slider: head on -Y, outboard of rod B."""
    yh = -D["Y_WRIST_HEAD0"]
    rh = P.PIN_HEAD_D / 2
    rs = P.WRIST_D / 2
    y_tip = yh + P.PIN_SHANK_L
    pin = G.loft_y("ML02_Pin", [(yh - P.PIN_HEAD_T, G.circle(0.0, P.AXLE_Z, rh - 0.4, 48)),
                                (yh - P.PIN_HEAD_T + 0.4, G.circle(0.0, P.AXLE_Z, rh, 48)),
                                (yh, G.circle(0.0, P.AXLE_Z, rh, 48))])
    sh = G.loft_y("shank", [(yh - 0.2, G.circle(0.0, P.AXLE_Z, rs, 48)),
                            (y_tip - 0.4, G.circle(0.0, P.AXLE_Z, rs, 48)),
                            (y_tip, G.circle(0.0, P.AXLE_Z, rs - 0.4, 48))])
    G.union(pin, sh)
    return pin


# =====================================================================================
# Poses
# =====================================================================================


def crank_matrix(theta):
    return (Matrix.Translation((0, 0, P.AXLE_Z)) @ Matrix.Rotation(-theta, 4, "Y")
            @ Matrix.Translation((0, 0, -P.AXLE_Z)))


def cheek_b_basis(shuttle=False):
    if shuttle:  # 180 degrees about the X axis through the axle
        return (Matrix.Translation((0, 0, P.AXLE_Z)) @ Matrix.Rotation(math.pi, 4, "X")
                @ Matrix.Translation((0, 0, -P.AXLE_Z)))
    return Matrix.Rotation(math.pi, 4, "Z")


def knob_pin_basis():
    """The wrist-pin part reused as the knob axle, on the handle tip."""
    dy = knob_head_y() - (-D["Y_WRIST_HEAD0"])
    return Matrix.Translation((P.HANDLE_R, dy, 0.0))


def rod_matrix(theta, side, p=P):
    from .params import pin_xz, rod_angle
    px, pz = pin_xz(theta, side, p)
    beta = rod_angle(theta, side, p)
    yc = (D["Y_ROD0"] + D["Y_ROD1"]) / 2 * (1 if side < 0 else -1)
    return Matrix.Translation((px, yc, pz)) @ Matrix.Rotation(-beta, 4, "Y")


def slider_matrix(theta, side, p=P):
    from .params import slider_x
    x = slider_x(theta, side, p)
    if side > 0:
        return Matrix.Translation((x, 0, 0))
    return Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.pi, 4, "Z")
