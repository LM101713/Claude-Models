"""
The seven printed parts of TC-03, as band stacks in the USE frame, LOCKED pose.

    upper   upper jaw (stiff top member): clamp face + groove, hinge ears, nose cheeks, detent
    blade   lower jaw: floating pressure BAR (with ridge) on an arched BOW spring
    lever   the toggle lever: arm, head (Q), crank web (P), detent peg
    bail_a  bail plate with two integral pegs (Q and K)
    bail_b  bail plate with two crush-rib holes (pressed onto the pegs)
    pin_p   lever pivot pin (pressed into the lever, runs in the cheeks)
    pin_h   hinge pin (pressed into the blade, runs in the ears)
"""

import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from . import geo as G
from . import mech as M
from .params import P, D, bar_face, bow_ratio

UP_FLIPPED = (0.0, -1.0)     # print-up seen in XZ for the parts printed upside down
R = 2.5                      # pin radius

H, Pp, K, Q = D["H"], D["P"], D["K"], D["Q"]


# =====================================================================================
# Blade
# =====================================================================================


FACE = {"f": bar_face}          # swapped for a flat face to model the loaded (locked) blade


def face(x):
    return FACE["f"](x)


def bar_poly(extra=0.0):
    x0, x1 = P.BAR_X
    xs = [x0 + (x1 - x0) * i / 60 for i in range(61)]
    top = lambda x: face(x) + extra
    bot = lambda x: face(x) - P.BAR_T
    return G.rounded(G.polyline_band(xs, top, bot), r_convex=1.5)


def bow_centre(x, bow_t=None):
    z_pin = H[1]
    return z_pin + P.BOW_RISE * bow_ratio(x)


def bow_poly(bow_t=None):
    t = P.BOW_T if bow_t is None else bow_t
    xs = [P.XP * i / 120 for i in range(121)]
    # the top stays put; a thicker (FIRM) bow grows downwards
    top = lambda x: bow_centre(x) + P.BOW_T / 2
    bot = lambda x: bow_centre(x) + P.BOW_T / 2 - t
    body = G.polyline_band(xs, top, bot)
    bosses = unary_union([G.circ(H, P.BOSS_R), G.circ(K, P.BOSS_R)])
    return G.rounded(unary_union([body, bosses]), r_concave=6.0)


def blade_base(bow_t=None, nobar=False):
    xm, w = P.BRIDGES[0], P.BRIDGE_W
    bridge = box(xm - w / 2, bow_centre(xm) + P.BOW_T / 2 - 0.5, xm + w / 2, face(xm) - P.BAR_T + 0.5)
    shape = unary_union([bow_poly(bow_t), bridge] + ([] if nobar else [bar_poly()]))
    # small fillets at the bridge only: a larger concave radius would close the slot
    shape = G.rounded(shape, r_concave=0.3)
    holes = unary_union([G.crush_hole(H, R, 0.15, P.RIB),            # hinge pin: pressed
                         G.circ(K, R + P.RUN_V)])                     # K peg: runs
    return shape.difference(holes)


def ridge_poly(h):
    """Ridge on the bar's face, height h, with 45 deg ends."""
    x0, x1 = P.BAR_X[0] + 3.0, P.BAR_X[1] - 3.0
    xs = [x0 + (x1 - x0) * i / 40 for i in range(41)]
    pts = [(x + (h if i == 0 else (-h if i == len(xs) - 1 else 0)), face(x) + h) for i, x in enumerate(xs)]
    pts += [(x, face(x) - 0.3) for x in reversed(xs)]
    return Polygon(pts).buffer(0)


def ridge_height(y):
    y = abs(y)
    if y <= P.RIDGE_TOP / 2:
        return P.RIDGE_H
    return max(0.0, P.RIDGE_H - (y - P.RIDGE_TOP / 2))


def blade_bands(bow_t=None, loaded=False, nobar=False):
    """loaded=True: the bar pressed flush against the jaw (z = 0), for the lock-pose checks
    (the bow is left undeflected, which only makes its gaps smaller)."""
    FACE["f"] = (lambda x: 0.0) if loaded else bar_face
    base = blade_base(bow_t, nobar)
    if nobar:
        FACE["f"] = bar_face
        return [(-P.BLADE_HW, P.BLADE_HW, base)]
    half = []
    ys = [0.0, P.RIDGE_TOP / 2]
    y = P.RIDGE_TOP / 2
    while y < P.RIDGE_BASE / 2 - 1e-6:
        y = min(P.RIDGE_BASE / 2, y + 0.2)
        ys.append(y)
    for a, b in zip(ys[:-1], ys[1:]):
        h = ridge_height((a + b) / 2) if a > 0 else P.RIDGE_H
        half.append((a, b, base.union(ridge_poly(h))))
    half.append((P.RIDGE_BASE / 2, P.BLADE_HW, base))
    FACE["f"] = bar_face
    return G.mirror_bands(half)


# =====================================================================================
# Lever
# =====================================================================================

ARM_END = Q[0] - P.BOSS_R - 0.7          # the full-width arm stops short of the bail plates
LEVER_TOP = P.UJ_H + P.LEVER_T
RELIEF_HW = 4.6                          # lever underside relieved over the detent fingers


def lever_arm(bottom=P.UJ_H, x_end=ARM_END):
    arm = box(P.LEVER_REAR, bottom, x_end, LEVER_TOP)
    return G.rounded(arm, r_convex=1.8)


def lever_head():
    blk = box(ARM_END - 6.0, P.UJ_H, Q[0] + 1.0, LEVER_TOP)
    return G.rounded(G.hull(blk, G.circ(Q, P.BOSS_R)), r_convex=1.5)


def lever_profile(kind):
    """kind: 'outer' (|y| 6..9), 'head' (4.6..6), 'head_rel' (3..4.6), 'web' (<3)."""
    relieved = kind in ("head_rel", "web")
    arm = lever_arm()
    if relieved:   # 0.3 mm relief over the fingers, the stop is on the outer strips
        arm = arm.difference(box(P.LEVER_REAR - 1.0, P.UJ_H - 1.0, 100.0, P.UJ_H + 0.3))
    if kind == "outer":
        return arm
    head = lever_head()
    shape = unary_union([arm, head]).difference(G.circ(Pp, P.CHEEK_R + P.AX))
    if kind == "web":
        web = G.hull(G.circ(Pp, P.CHEEK_R), G.circ(Q, 3.6))
        shape = unary_union([shape, web, G.circ(Pp, P.CHEEK_R)])
    shape = G.rounded(shape, r_concave=1.0)
    shape = shape.difference(G.teardrop(Q, R + P.RUN_T, UP_FLIPPED))
    if kind == "web":
        shape = shape.difference(G.crush_hole(Pp, R, 0.15, P.RIB, UP_FLIPPED))
    return shape


def peg_poly(y):
    """Detent peg below the lever's thumb end; barbs on its +-y faces (45 deg each side)."""
    x0, x1 = P.PEG_X - 1.5, P.PEG_X + 1.5
    y = abs(y)
    if y <= P.PEG_HW:
        return box(x0, 5.0, x1, P.UJ_H + 0.5)
    d = y - P.PEG_HW                         # 0 .. BARB
    zc, half = 6.2, 0.6 - d                  # barb: z 5.6..6.8 at the root, 6.1..6.3 at the tip
    return box(x0 + 0.2, zc - half, x1 - 0.2, zc + half)


def lever_bands():
    half = []
    ys = [0.0, P.PEG_HW] + [P.PEG_HW + P.BARB * k / 5 for k in range(1, 6)]
    for a, b in zip(ys[:-1], ys[1:]):
        half.append((a, b, unary_union([lever_profile("web"), peg_poly((a + b) / 2)])))
    half.append((ys[-1], P.LEVER_BLADE_HW, lever_profile("web")))
    half.append((P.LEVER_BLADE_HW, RELIEF_HW, lever_profile("head_rel")))
    half.append((RELIEF_HW, P.CHEEK_OUT, lever_profile("head")))
    half.append((P.CHEEK_OUT, P.BODY_HW, lever_profile("outer")))
    return G.mirror_bands(half)


# =====================================================================================
# Bail plates and pins
# =====================================================================================

PLATE_HW = 3.3


def plate_outline():
    qx, qz = Q
    kx, kz = K
    L = math.hypot(qx - kx, qz - kz)
    ang = math.degrees(math.atan2(qz - kz, qx - kx))
    shank = box(0, -PLATE_HW, L, PLATE_HW)
    from shapely import affinity
    shank = affinity.translate(affinity.rotate(shank, ang, origin=(0, 0)), kx, kz)
    shape = unary_union([shank, G.circ(Q, P.BOSS_R), G.circ(K, P.BOSS_R)])
    return G.rounded(shape, r_concave=2.5)


def bail_a_bands():
    pegs = unary_union([G.circ(Q, R), G.circ(K, R)])
    return [(-P.PLATE_OUT, -P.PLATE_IN, plate_outline()), (-P.PLATE_IN, P.PLATE_OUT, pegs)]


def bail_b_bands():
    holes = unary_union([G.crush_hole(Q, R, 0.15, P.RIB), G.crush_hole(K, R, 0.15, P.RIB)])
    return [(P.PLATE_IN, P.PLATE_OUT, plate_outline().difference(holes))]


def pin_p_bands():
    return [(-P.CHEEK_OUT, P.CHEEK_OUT, G.circ(Pp, R))]


def pin_h_bands():
    return [(-P.BODY_HW, P.BODY_HW, G.circ(H, R))]


# =====================================================================================
# Motion (2D poses) and swept envelopes
# =====================================================================================


def pose2(kind, g, st):
    """Place a profile of a moving part at state st (from mech.pose)."""
    if kind in ("lever", "pin_p"):
        return G.place2(g, -st["theta"], Pp)
    if kind in ("blade", "pin_h"):
        return G.place2(g, -st["phi"], H)
    if kind in ("bail_a", "bail_b"):
        return G.place2(g, st["bail_rot"], K, st["K"])
    return g


THETA_MAX = math.radians(190.0)    # the toggle's bottom dead centre: jaws fully open


def states(n=76, theta_max=None):
    tm = THETA_MAX if theta_max is None else theta_max
    return [M.pose(tm * i / (n - 1)) for i in range(n)]


def swept(bands_by_part, y0, y1, sts, clear):
    """Union of every moving part's profile over the motion, for bands that overlap [y0, y1]
    or come closer than the axial gap AX (faces that slide past each other need AX)."""
    geoms = []
    for kind, bands in bands_by_part.items():
        for a, b, poly in bands:
            if b <= y0 - P.AX + 1e-6 or a >= y1 + P.AX - 1e-6:
                continue
            for st in sts:
                geoms.append(pose2(kind, poly, st))
    if not geoms:
        return Polygon()
    return unary_union(geoms).buffer(clear, quad_segs=8)


# =====================================================================================
# Upper jaw
# =====================================================================================

UJ_REAR = -4.5
UJ_NOSE = ARM_END - 0.2                 # the outer bands end before the bail plates
GROOVE_TOP = P.RIDGE_H + P.GROOVE_GAP
GROOVE_EDGE = P.RIDGE_BASE / 2 - P.RIDGE_H + P.RIDGE_H + P.GROOVE_GAP * math.sqrt(2)   # z = 0


def uj_body(x_end=UJ_NOSE):
    b = box(UJ_REAR, 0.0, x_end, P.UJ_H)
    b = G.rounded(b, r_convex=1.2)
    # softer rear top corner
    cut = Polygon([(UJ_REAR - 1, P.UJ_H - 3.0), (UJ_REAR + 3.0, P.UJ_H + 1), (UJ_REAR - 1, P.UJ_H + 1)])
    return G.rounded(b.difference(cut), r_convex=1.0)


def uj_ear():
    e = G.hull(G.circ(H, P.BOSS_R), box(UJ_REAR, -2.0, P.BOSS_R, 1.0))
    e = unary_union([e, uj_body()])
    e = G.rounded(e, r_concave=3.0)
    return e.difference(G.teardrop(H, R + P.RUN_T, UP_FLIPPED))


def uj_cheek():
    c = G.hull(G.circ(Pp, P.CHEEK_R), box(Pp[0] - 9.0, 0.0, Pp[0] - 1.0, 3.0))
    c = unary_union([uj_body(), c])
    c = G.rounded(c, r_concave=2.0)
    return c.difference(G.teardrop(Pp, R + P.RUN_T, UP_FLIPPED))


def groove_depth(y):
    y = abs(y)
    top_hw = P.RIDGE_TOP / 2 + P.GROOVE_GAP * (math.sqrt(2) - 1)
    edge = top_hw + GROOVE_TOP
    if y <= top_hw:
        return GROOVE_TOP
    return max(0.0, edge - y)


def groove_poly(d):
    x0, x1 = 5.0, P.BAR_X[1] + 2.0
    return Polygon([(x0 - 0.01, -1), (x1, -1), (x1, 0), (x1 - d, d), (x0 + d, d), (x0 - 0.01, 0)])


def detent_cut(y):
    """Pocket, finger slots and the gap under the fingers, by |y| (XZ polygon to remove)."""
    y = abs(y)
    xp0, xp1 = P.PEG_X - 2.0, P.PEG_X + 2.4                # pocket (peg + swing room)
    froot = xp1 - P.FINGER_L
    pin = P.PEG_HW + P.FINGER_GAP                          # finger inner face
    fout = pin + P.FINGER_W
    sout = fout + 1.0
    z_floor = 4.6
    if y <= pin:
        return box(xp0, z_floor, xp1, P.UJ_H + 1)
    if y <= fout:          # finger band: the finger stands z 5..8, root at froot; gap below
        return unary_union([box(froot, z_floor, xp1 + 0.8, 5.0), box(xp1, z_floor, xp1 + 0.8, P.UJ_H + 1)])
    if y <= sout:
        return box(froot, z_floor, xp1 + 0.8, P.UJ_H + 1)
    return Polygon()


BUMP_TIP = P.PEG_HW + P.BARB - P.BUMP     # the bump overlaps the barb by BUMP per side


def bump_poly(y):
    """Bump on the finger's inner face, protruding to |y| = pin - BUMP (45 deg flanks)."""
    pin = P.PEG_HW + P.FINGER_GAP
    h = pin - BUMP_TIP
    d = (pin - abs(y)) / h                 # 0 at the finger face .. 1 at the bump's tip
    zc, half = 7.2, 0.6 - 0.4 * d          # ~45 deg flanks; stays below the top face (z 8)
    return box(P.PEG_X - 1.6, zc - half, P.PEG_X + 1.6, zc + half)


def upper_bands(sweep=True, n_states=76):
    sts = states(n_states) if sweep else []
    # the arm lying on top only ever lifts away from the jaw: sweep the parts of the lever
    # that sit below the jaw's top face at lock, and everything at the nose
    clip = unary_union([box(ARM_END - 8.0, -50, 200, P.UJ_H), box(ARM_END, -50, 200, 50)])
    movers = {"lever": [(a, b, p.intersection(clip)) for a, b, p in lever_bands()],
              "bail_a": bail_a_bands(), "bail_b": bail_b_bands()}
    half = []
    # centre: groove sub-bands, the detent pocket/fingers, the lever's sweep
    edges = sorted(set([0.0, P.RIDGE_TOP / 2 + P.GROOVE_GAP * (math.sqrt(2) - 1)] +
                       [round(v, 3) for v in
                        [P.RIDGE_TOP / 2 + P.GROOVE_GAP * (math.sqrt(2) - 1) + 0.2 * k for k in range(1, 10)]
                        if v < GROOVE_EDGE] + [GROOVE_EDGE, BUMP_TIP,
                                               BUMP_TIP + (P.PEG_HW + P.FINGER_GAP - BUMP_TIP) / 3,
                                               BUMP_TIP + 2 * (P.PEG_HW + P.FINGER_GAP - BUMP_TIP) / 3,
                                               P.PEG_HW + P.FINGER_GAP,
                                               P.PEG_HW + P.FINGER_GAP + P.FINGER_W,
                                               P.PEG_HW + P.FINGER_GAP + P.FINGER_W + 1.0,
                                               P.CHEEK_IN, P.CHEEK_OUT, P.PLATE_IN, P.BODY_HW]))
    edges = [e for e in edges if e <= P.BODY_HW]
    for a, b in zip(edges[:-1], edges[1:]):
        ym = (a + b) / 2
        if b <= P.CHEEK_IN + 1e-6:
            prof = uj_body()
        elif b <= P.CHEEK_OUT + 1e-6:
            prof = uj_cheek()
        elif b <= P.PLATE_IN + 1e-6:
            prof = uj_body()
        else:
            prof = uj_ear()
        gd = groove_depth(ym)
        if gd > 0:
            prof = prof.difference(groove_poly(gd))
        prof = prof.difference(detent_cut(ym))
        pin = P.PEG_HW + P.FINGER_GAP
        if BUMP_TIP - 1e-6 <= ym <= pin + 1e-6:
            prof = prof.union(bump_poly(ym))
        if sweep:
            prof = prof.difference(swept(movers, a, b, sts, 0.4))
        half.append((a, b, prof))
    return G.mirror_bands(half)
