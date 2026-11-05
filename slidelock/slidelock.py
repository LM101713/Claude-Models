"""
ODD LAYER  SL-01  SLIDELOCK
===========================

A pocket slider fidget with a two-stage detent: light "ticks" along the travel and a
firm "lock" at each end, where the detent spring also holds the carriage against a hard
stop. The parts are:

    TRAY      chassis: floor, walls with the detent notch tracks, hard stops, flag latches
    CARRIAGE  the slider: orange thumb knob, two in-plane cantilever detent springs
    LID       top plate: slot, position marks, latch hangers

This is one parametric Blender script. It builds every part with bmesh and exact booleans,
then checks the geometry (intersections, clearances, loose shells, wall thickness,
overhangs) and simulates the detent force curve. It exports STL and 3MF, saves an editable
.blend, and (with --render) renders the product images.

Run (Blender 4.2+ or the `bpy` module, Python 3.11):

    blender -b -P slidelock.py -- --out .            # build, validate, export, save .blend
    blender -b -P slidelock.py -- --out . --render   # ...and render images
    python slidelock.py --out . --render              # same, with `pip install bpy==4.2.*`

You can also open the script in Blender's Scripting tab and press Run Script. It then builds
into the open file and writes its outputs next to the script.

Units: millimetres. 1 Blender unit = 1 mm (scene unit scale is set to 0.001 so Blender
shows mm). Assembly frame: X = slide direction, Y = width, Z = up. The tray's bottom face is
at Z = 0. The carriage is shown at the centre detent.

Status: designed and checked in CAD only. Nothing here has been printed or tested. Every
force, fit and fatigue number is a model prediction that a printed prototype must confirm
(see README.md).
"""

import argparse
import json
import math
import os
import struct
import sys
import time
import zipfile

import bpy  # noqa: E402  (bpy must be imported before bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# =====================================================================================
# 1. PARAMETERS  (every dimension in mm; edit here)
# =====================================================================================


class P:
    # ---- envelope ------------------------------------------------------------------
    L = 76.0  # overall length (slide direction)
    W = 30.0  # overall width
    H = 13.0  # body height without the knob
    CORNER_R = 12.0  # plan-view corner size
    CORNER_N = 4.0  # superellipse exponent of the corners (2 = circular; 4 = soft "squircle")
    EDGE_R = 3.0  # top and bottom edge radius (45-degree capped so it prints on the bed)

    # ---- shells --------------------------------------------------------------------
    WALL = 2.6  # side wall thickness (notches cut up to ~1.05 mm into it)
    FLOOR = 2.4  # tray floor thickness
    LID_SKIN = 2.2  # lid plate thickness
    SKIRT = 1.2  # lid skirt (outer part of the wall above the parting line)
    FIT_LID = 0.15  # radial gap between lid skirt and tray tongue
    TONGUE_GAP = 0.15  # gap between tongue top and lid ceiling (lid bears on the seam step)
    LEADIN = 0.5  # 45-degree lead-in at the top of the tray cavity (carriage insertion)
    SEAM_CHAMFER = 0.35  # V-groove at the parting line: hides lid/tray mismatch, reads as intent

    # ---- guidance ------------------------------------------------------------------
    RAIL_H = 0.4  # height of the floor and ceiling bearing rails
    FLOOR_RAIL_Y = (3.5, 7.0)  # |y| extent of the two floor rails
    CEIL_RAIL_Y = (5.6, 8.6)  # |y| extent of the two ceiling rails (clear of the slot)
    CLEAR_Z = 0.20  # carriage to rail clearance, each side
    CLEAR_SIDE = 0.20  # carriage guide pad to wall clearance, each side

    # ---- travel and detents --------------------------------------------------------
    TRAVEL = 20.0  # total knob travel (stop to stop)
    PITCH = 5.0  # detent pitch -> positions at -10, -5, 0, 5, 10
    TOOTH_X = 4.5  # tooth offset from the carriage centre (left tooth +X, right tooth -X)
    NOSE_R = 0.6  # tooth nose radius
    TOOTH_FLANK = 65.0  # tooth flank angle (deg from X); steeper than any notch flank
    MID_DEPTH = 0.70  # tooth tip penetration when seated in a mid ("tick") notch
    MID_FLANK = 35.0  # mid notch flank angle (deg from the slide axis)
    PRELOAD = 0.20  # spring deflection while seated in a mid notch (kills rattle)
    END_DEPTH = 0.90  # seated tip penetration of the end ("lock") notches
    END_FLANK_IN = 55.0  # end notch exit flank (steeper = firmer lock)
    END_FLANK_OUT = 60.0  # end notch outer flank (never reached; sets the notch shape)
    END_OVERSHOOT = 0.25  # end notch seat lies this far past the hard stop -> preload into stop
    NOTCH_FLOOR_MARGIN = 0.15  # notch bottom is truncated this far below the deepest tooth reach
    CREST_R = 0.20  # rounding of the notch crests
    APEX_R = 0.25  # rounding of the notch bottoms
    NOTCH_TOP = 9.2  # notches run full depth from the floor up to here...
    NOTCH_ROOF = 1.3  # ...then close with a 45-degree roof (no flat overhang, tongue intact)

    # ---- carriage ------------------------------------------------------------------
    CARR_L = 30.0  # carriage length; it stops against the stop walls
    SPRING_ROOT_X = 11.0  # |x| of the spring root face
    SPRING_T = 1.2  # spring thickness (standard)
    SPRING_H = 6.0  # spring height (standard)
    SPRING_GAP = 1.6  # slot behind the spring = overtravel stop
    SPRING_WALL_GAP = 0.5  # free-state gap between spring outer face and wall
    SPRING_END_GAP = 0.8  # gap between the spring's free end and the guide pad
    ROOT_FILLET = 0.6  # fillet at the spring root (slot side)
    KNOB_W = 8.0  # knob width (Y)
    KNOB_L = 11.0  # knob length (X)
    KNOB_R = 2.5  # knob corner radius
    KNOB_H = 3.6  # knob height above the lid top (at its ends)
    KNOB_FILLET = 1.5
    KNOB_SADDLE = 0.9  # depth of the concave thumb saddle
    SLOT_CLEAR = 0.5  # knob to slot clearance (never touches; the stops are inside)
    SLOT_CHAMFER = 0.5

    # ---- carriage variants: (name, spring thickness, spring height, id dimples) ------
    VARIANTS = [
        ("Soft", 1.2, 4.2, 1),
        ("Standard", 1.2, 6.0, 2),
        ("Firm", 1.4, 6.0, 3),
    ]

    # ---- hard stops and lid latches -------------------------------------------------
    STOP_T = 2.4  # stop wall thickness
    FLAG_T = 1.4  # latch flag thickness (bends in-plane)
    FLAG_Y = (-7.6, 6.6)  # flag root face .. free tip (y)
    FLAG_TOP = 8.0
    FLAG_SLOT_IN = 1.0  # floor slot gap on the deflection side (toward the stop wall)
    FLAG_SLOT_OUT = 0.6  # floor slot gap at the flag tip (anti-fusing on layer 1)
    FLAG_SLOT_TOOL = 1.2  # floor slot gap on the outer side: room for a 1 mm pin to release it
    FLAG_GAP_TO_STOP = 1.2  # flag to stop wall gap
    HOOK = 0.8  # hook protrusion
    HOOK_Y = (2.5, 6.5)
    HOOK_Z0 = 5.7  # hook lower (retaining) face
    POCKET_DEPTH = 0.8
    HANGER_T = 2.2
    HANGER_Y = (-8.5, 8.5)  # full width with a pocket each side: the lid fits either way round
    HANGER_BOTTOM = 4.6

    # ---- marks / branding -----------------------------------------------------------
    MARK_DEPTH = 0.4
    MARK_W = 0.6
    TEXT_DEPTH = 0.4
    BRAND = "ODD LAYER"
    MODEL = "SLIDELOCK  SL-01"

    # ---- materials (for mass estimates) ---------------------------------------------
    DENSITY = {"PETG": 1.27, "PLA": 1.24}
    E_MODULUS = {"PETG": 2000.0, "PLA": 3000.0}  # MPa, printed, in-plane (typical values)
    MU = 0.30  # plastic-on-plastic friction coefficient assumed for the detent model

    # ---- tessellation ---------------------------------------------------------------
    CORNER_SEG = 48
    ARC_SEG = 10


# ---- derived values ------------------------------------------------------------------
def derived(p=P):
    d = {}
    d["YC"] = p.W / 2 - p.WALL  # cavity half width
    d["CEIL"] = p.H - p.LID_SKIN  # lid ceiling height
    d["SEAM"] = p.H - p.EDGE_R  # parting line, at the tangent of the top edge radius
    d["FLOOR_RAIL_TOP"] = p.FLOOR + p.RAIL_H
    d["CEIL_RAIL_BOT"] = d["CEIL"] - p.RAIL_H
    d["CZ0"] = d["FLOOR_RAIL_TOP"] + p.CLEAR_Z  # carriage bottom
    d["CZ1"] = d["CEIL_RAIL_BOT"] - p.CLEAR_Z  # carriage top
    d["CH"] = d["CZ1"] - d["CZ0"]  # carriage frame height
    d["HALF_TRAVEL"] = p.TRAVEL / 2
    d["STOP_IN"] = p.CARR_L / 2 + p.TRAVEL / 2  # stop wall inner face |x|
    d["STOP_OUT"] = d["STOP_IN"] + p.STOP_T
    d["FLAG_X0"] = d["STOP_OUT"] + p.FLAG_GAP_TO_STOP
    d["FLAG_X1"] = d["FLAG_X0"] + p.FLAG_T
    d["HANGER_X0"] = d["FLAG_X1"] + 0.2
    d["HANGER_X1"] = d["HANGER_X0"] + p.HANGER_T
    d["TONGUE_TOP"] = d["CEIL"] - p.TONGUE_GAP
    d["KNOB_TOP"] = p.H + p.KNOB_H
    d["SLOT_W"] = p.KNOB_W + 2 * p.SLOT_CLEAR
    d["SLOT_L"] = p.KNOB_L + p.TRAVEL + 2 * p.SLOT_CLEAR
    d["SPRING_OUT"] = d["YC"] - p.SPRING_WALL_GAP  # |y| spring outer face (free)
    d["TIP_FREE"] = d["YC"] + p.MID_DEPTH + p.PRELOAD  # |y| tooth tip (free)
    d["PAD_Y"] = d["YC"] - p.CLEAR_SIDE
    d["POSITIONS"] = [
        -p.TRAVEL / 2 + i * p.PITCH for i in range(int(round(p.TRAVEL / p.PITCH)) + 1)
    ]
    return d


D = derived()

# =====================================================================================
# 2. 2D GEOMETRY
# =====================================================================================


def _sgn(v):
    return 1.0 if v >= 0 else -1.0


def plan_outline(inset=0.0, p=P, seg=None, tracks=None):
    """Plan outline (CCW): a rectangle with superellipse corners, offset inward by `inset`.

    `tracks` = (bottom_pts, top_pts) replaces the straight long sides (used for the notched
    cavity). Both lists run in the CCW direction and exclude the corner end points.
    """
    seg = seg or p.CORNER_SEG
    R, n = p.CORNER_R, p.CORNER_N
    hx, hy = p.L / 2 - R, p.W / 2 - R
    out = []
    corners = [(hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy)]
    for q, (cx, cy) in enumerate(corners):
        pts = []
        for i in range(seg + 1):
            t = (q + i / seg) * math.pi / 2
            c, s = math.cos(t), math.sin(t)
            ex = _sgn(c) * abs(c) ** (2 / n)
            ey = _sgn(s) * abs(s) ** (2 / n)
            # outward normal from the implicit gradient
            nx = _sgn(ex) * abs(ex) ** (n - 1)
            ny = _sgn(ey) * abs(ey) ** (n - 1)
            ln = math.hypot(nx, ny)
            nx, ny = nx / ln, ny / ln
            pts.append((cx + R * ex - inset * nx, cy + R * ey - inset * ny))
        out.extend(pts)
        if tracks is not None:
            if q == 0:  # after corner 0 comes the top side (traversed -x)
                out.extend(tracks[1])
            elif q == 2:  # after corner 2 comes the bottom side (traversed +x)
                out.extend(tracks[0])
    return out


def rrect(hx, hy, r, seg=8, cx=0.0, cy=0.0):
    """Rounded rectangle (CCW) with half sizes hx, hy and corner radius r."""
    r = max(0.0, min(r, hx, hy))
    pts = []
    for q, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        ccx, ccy = cx + sx * (hx - r), cy + sy * (hy - r)
        for i in range(seg + 1):
            a = (q + i / seg) * math.pi / 2
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def fillet_polyline(pts, radii, seg=None):
    """Round the interior corners of an open polyline. radii[i] applies to pts[i]."""
    seg = seg or P.ARC_SEG
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        r = radii[i]
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[i + 1])
        d1, d2 = (p0 - p1), (p2 - p1)
        l1, l2 = d1.length, d2.length
        if r <= 0 or l1 < 1e-9 or l2 < 1e-9:
            out.append(pts[i])
            continue
        d1.normalize()
        d2.normalize()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(pts[i])
            continue
        t = r / math.tan(ang / 2)
        tmax = 0.49 * min(l1, l2)
        if t > tmax:
            t = tmax
            r = t * math.tan(ang / 2)
        t1, t2 = p1 + d1 * t, p1 + d2 * t
        bis = (d1 + d2).normalized()
        c = p1 + bis * (r / math.sin(ang / 2))
        a1 = math.atan2(t1.y - c.y, t1.x - c.x)
        a2 = math.atan2(t2.y - c.y, t2.x - c.x)
        da = a2 - a1
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(seg + 1):
            a = a1 + da * k / seg
            out.append((c.x + r * math.cos(a), c.y + r * math.sin(a)))
    out.append(pts[-1])
    return out


def notch_apex(u_seat, d_seat, th1, th2, r):
    """Apex (u_a, D) of a V notch whose flanks (th1 on the -u side, th2 on the +u side, deg)
    seat a nose of radius r with its centre at u_seat and its tip `d_seat` into the wall."""
    t1, t2 = math.radians(th1), math.radians(th2)
    w = r * (1 / math.cos(t1) - 1 / math.cos(t2)) / (math.tan(t1) + math.tan(t2))
    vc = d_seat - r
    Dp = vc + r / math.cos(t1) - w * math.tan(t1)
    return u_seat - w, Dp


def wall_notches(side, p=P, d=D):
    """Notch list for one wall. side = -1 (the -Y wall, tooth at +TOOTH_X) or +1."""
    a = p.TOOTH_X if side < 0 else -p.TOOTH_X
    notches = []
    pos = d["POSITIONS"]
    for i, xc in enumerate(pos):
        u = xc + a
        if i == 0 or i == len(pos) - 1:
            sgn = -1 if i == 0 else 1  # direction toward that end
            seat = u + sgn * p.END_OVERSHOOT
            if sgn > 0:
                th1, th2 = p.END_FLANK_IN, p.END_FLANK_OUT
            else:
                th1, th2 = p.END_FLANK_OUT, p.END_FLANK_IN
            ua, Dp = notch_apex(seat, p.END_DEPTH, th1, th2, p.NOSE_R)
            notches.append(dict(kind="end", u_seat=seat, ua=ua, D=Dp, th1=th1, th2=th2,
                                floor=p.END_DEPTH + p.NOTCH_FLOOR_MARGIN))
        else:
            ua, Dp = notch_apex(u, p.MID_DEPTH, p.MID_FLANK, p.MID_FLANK, p.NOSE_R)
            notches.append(dict(kind="mid", u_seat=u, ua=ua, D=Dp, th1=p.MID_FLANK,
                                th2=p.MID_FLANK, floor=p.MID_DEPTH + p.NOTCH_FLOOR_MARGIN))
    return notches


def track_profile(notches, u0, u1, p=P):
    """Wall surface profile v(u) (v = depth into the wall) as a filleted polyline."""
    pts, radii = [(u0, 0.0)], [0.0]
    for n in sorted(notches, key=lambda k: k["ua"]):
        t1, t2 = math.tan(math.radians(n["th1"])), math.tan(math.radians(n["th2"]))
        uL, uR = n["ua"] - n["D"] / t1, n["ua"] + n["D"] / t2
        pts.append((uL, 0.0))
        radii.append(p.CREST_R)
        if n["D"] > n["floor"]:  # truncate the V into a flat-bottomed trapezoid
            f = n["floor"]
            pts += [(uL + f / t1, f), (uR - f / t2, f)]
            radii += [p.APEX_R, p.APEX_R]
        else:
            pts.append((n["ua"], n["D"]))
            radii.append(p.APEX_R)
        pts.append((uR, 0.0))
        radii.append(p.CREST_R)
    pts.append((u1, 0.0))
    radii.append(0.0)
    return fillet_polyline(pts, radii)


def cavity_tracks(p=P, d=D, depth_scale=1.0):
    """Notched long sides of the cavity outline, in CCW order, without the end points.
    depth_scale = 0 gives the same vertex list flattened onto the wall plane (for lofts)."""
    hx = p.L / 2 - p.CORNER_R
    yc = d["YC"]
    prof_m = track_profile(wall_notches(-1), -hx, hx)
    prof_p = track_profile(wall_notches(+1), -hx, hx)
    k = depth_scale
    bottom = [(u, -(yc + k * v)) for (u, v) in prof_m][1:-1]  # traversed +x
    top = [(u, yc + k * v) for (u, v) in reversed(prof_p)][1:-1]  # traversed -x
    return bottom, top, prof_m, prof_p


def edge_inset(s, R):
    """Inset of a 45-degree-capped edge radius at distance s from the face (s in 0..R)."""
    s45 = R * (1 - math.sqrt(0.5))
    if s <= s45:
        return 2 * s45 - s
    if s >= R:
        return 0.0
    return R - math.sqrt(max(0.0, R * R - (R - s) ** 2))


def edge_samples(R, n_arc=12):
    """Distances from the face at which to place rings: the chamfer (0..s45), then the arc
    from its 45-degree point down to where it meets the vertical side (s = R)."""
    s45 = R * (1 - math.sqrt(0.5))
    ss = [0.0, s45]
    for i in range(n_arc):
        a = math.radians(45 * i / n_arc)  # 0..45 deg below the 45-degree point
        ss.append(R * (1 - math.sin(a)))
    ss = sorted(set(round(s, 6) for s in ss))
    return ss


def spring_outline(t, p=P, d=D, seg=10):
    """Left (-Y) spring with its tooth, CCW. Root at -SPRING_ROOT_X, tooth at +TOOTH_X."""
    yo = -d["SPRING_OUT"]
    yi = yo + t
    xr = -p.SPRING_ROOT_X
    a = p.TOOTH_X
    r = p.NOSE_R
    xe = a + 1.6
    cy = -d["TIP_FREE"] + r
    beta = math.radians(p.TOOTH_FLANK)
    TL = (a - r * math.sin(beta), cy - r * math.cos(beta))
    TR = (a + r * math.sin(beta), cy - r * math.cos(beta))
    rise = yo - TL[1]
    BL = (TL[0] - rise / math.tan(beta), yo)
    BR = (TR[0] + rise / math.tan(beta), yo)
    assert BR[0] < xe - 0.05, "tooth runs past the spring end"
    pts = []

    def line(p0, p1, step=0.5):
        n = max(1, int(math.dist(p0, p1) / step))
        return [(p0[0] + (p1[0] - p0[0]) * k / n, p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n)]

    rf = p.ROOT_FILLET
    ro = 0.3
    # outer root flare (spring outer face meets the root block, which reaches the pad line)
    xr_in = xr - 0.3  # overlap into the root block
    pts.append((xr_in, yo - ro))
    # outer root fillet (concave; its centre lies outside the spring)
    c = (xr + ro, yo - ro)
    for k in range(seg + 1):
        ang = math.pi - (math.pi / 2) * k / seg  # 180 -> 90 deg
        pts.append((c[0] + ro * math.cos(ang), c[1] + ro * math.sin(ang)))
    pts += line((xr + ro, yo), BL)
    pts.append(BL)
    pts.append(TL)
    a1 = math.atan2(TL[1] - cy, TL[0] - a)
    a2 = math.atan2(TR[1] - cy, TR[0] - a)
    if a2 < a1:
        a2 += 2 * math.pi
    for k in range(1, seg):
        ang = a1 + (a2 - a1) * k / seg
        pts.append((a + r * math.cos(ang), cy + r * math.sin(ang)))
    pts.append(TR)
    pts.append(BR)
    pts += line(BR, (xe, yo))
    pts.append((xe, yo))
    pts.append((xe, yi))
    pts += line((xe, yi), (xr + rf, yi))[1:]
    c = (xr + rf, yi + rf)
    for k in range(seg + 1):
        ang = -math.pi / 2 - (math.pi / 2) * k / seg  # -90 -> -180 deg
        pts.append((c[0] + rf * math.cos(ang), c[1] + rf * math.sin(ang)))
    pts.append((xr_in, yi + rf))
    # de-duplicate
    clean = []
    for q in pts:
        if not clean or math.dist(q, clean[-1]) > 1e-6:
            clean.append(q)
    if math.dist(clean[0], clean[-1]) < 1e-6:
        clean.pop()
    return clean


def carriage_frame_outline(t, p=P, d=D):
    """Carriage frame (core + root blocks + guide pads), CCW, for spring thickness t."""
    hx = p.CARR_L / 2
    py = d["PAD_Y"]
    core = d["SPRING_OUT"] - t - p.SPRING_GAP
    xr = p.SPRING_ROOT_X
    xe = p.TOOTH_X + 1.6 + p.SPRING_END_GAP
    return [
        (-hx, -py), (-xr, -py), (-xr, -core), (xe, -core), (xe, -py), (hx, -py),
        (hx, py), (xr, py), (xr, core), (-xe, core), (-xe, py), (-hx, py),
    ]


def polygon_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2


# =====================================================================================
# 3. MESH HELPERS
# =====================================================================================

COLL = {}
SWEEP_MARGIN = 0.06  # extra bend applied to the springs in the sweep (tooth rotation slack)


def collection(name, parent=None):
    if name in bpy.data.collections:
        c = bpy.data.collections[name]
    else:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    COLL[name] = c
    return c


def obj_from_bm(name, bm, coll=None):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or COLL["_work"]).objects.link(ob)
    return ob


def loft(name, rings, coll=None):
    """Solid from stacked rings [(z, [(x, y), ...]), ...]; all rings same count, CCW."""
    bm = bmesh.new()
    vr = [[bm.verts.new((x, y, z)) for (x, y) in poly] for z, poly in rings]
    n = len(vr[0])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(vr[0])))
    bm.faces.new(vr[-1])
    return obj_from_bm(name, bm, coll)


def prism(name, poly, z0, z1, coll=None):
    if polygon_area(poly) < 0:
        poly = list(reversed(poly))
    return loft(name, [(z0, poly), (z1, poly)], coll)


def prism_xz(name, poly_xz, y0, y1, coll=None):
    """Prism of an XZ profile extruded along Y."""
    ob = prism(name, poly_xz, y0, y1, coll)
    # map (x, y_profile=z, z_extrude=y) -> (x, y, z)
    ob.data.transform(Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    ob.data.flip_normals()
    ob.data.update()
    return ob


def apply_bool(target, cutter, op, delete_cutter=True):
    m = target.modifiers.new("b", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.object = cutter
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear()
    old = target.data
    target.data = me
    me.name = target.name
    bpy.data.meshes.remove(old)
    if delete_cutter:
        cm = cutter.data
        bpy.data.objects.remove(cutter)
        if cm.users == 0:
            bpy.data.meshes.remove(cm)
    return target


def union(target, *others):
    for o in others:
        apply_bool(target, o, "UNION")
    return target


def cut(target, *others):
    for o in others:
        apply_bool(target, o, "DIFFERENCE")
    return target


def text_solid(name, body, size, z0, z1, cx=0.0, cy=0.0, mirror_x=False, spacing=1.0):
    cu = bpy.data.curves.new(name + "_curve", "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_character = spacing
    cu.extrude = (z1 - z0) / 2
    cu.resolution_u = 4
    ob = bpy.data.objects.new(name + "_txt", cu)
    COLL["_work"].objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    sx = -1 if mirror_x else 1
    me.transform(Matrix.Translation((cx, cy, (z0 + z1) / 2)) @ Matrix.Diagonal((sx, 1, 1, 1)))
    if mirror_x:
        me.flip_normals()
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return obj_from_bm(name, bm)


def mesh_stats(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    vol = bm.calc_volume(signed=True)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    # shells
    seen, shells = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        shells += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
    co = [v.co for v in bm.verts]
    bb = [min(c.x for c in co), min(c.y for c in co), min(c.z for c in co),
          max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)]
    area = sum(f.calc_area() for f in bm.faces)
    nf = len(bm.faces)
    bm.free()
    return dict(volume_mm3=vol, nonmanifold_edges=nonman, shells=shells, bbox=bb,
                area_mm2=area, faces=nf)


def world_tris(ob, mat=None):
    me = ob.data
    me.calc_loop_triangles()
    M = (mat or Matrix()) @ ob.matrix_world
    verts = [M @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return verts, tris


def bvh(ob, mat=None):
    v, t = world_tris(ob, mat)
    return BVHTree.FromPolygons(v, t, epsilon=0.0), v, t


# =====================================================================================
# 4. PARTS
# =====================================================================================


def outer_rings(z0, z1, bottom_round, top_round, p=P):
    """Rings for the outer skin between z0 and z1. A rounded end gets the 45-degree-capped
    edge radius; a square end (the parting line) gets the small seam chamfer."""
    R = p.EDGE_R
    c = p.SEAM_CHAMFER
    zs = {}
    if bottom_round:
        for s in edge_samples(R):
            zs[round(z0 + s, 6)] = edge_inset(s, R)
    else:
        zs[z0] = c
        zs[round(z0 + c, 6)] = 0.0
    if top_round:
        for s in edge_samples(R):
            zs[round(z1 - s, 6)] = edge_inset(s, R)
    else:
        zs[z1] = c
        zs[round(z1 - c, 6)] = 0.0
    rings = [(z, plan_outline(inset)) for z, inset in sorted(zs.items())]
    return rings


def build_tray(p=P, d=D):
    t0 = time.time()
    yc = d["YC"]
    seam = d["SEAM"]
    tray = loft("SL01_Tray", outer_rings(0.0, seam, True, False))
    # tongue (inner part of the wall above the parting line)
    tongue = prism("tongue", plan_outline(p.SKIRT + p.FIT_LID), seam - 0.5, d["TONGUE_TOP"])
    union(tray, tongue)
    # cavity: notched part, then plain part with a lead-in flare at the top
    bottom, top, _, _ = cavity_tracks()
    flat = cavity_tracks(depth_scale=0.0)
    notched = plan_outline(p.WALL, tracks=(bottom, top))
    plain = plan_outline(p.WALL, tracks=(flat[0], flat[1]))
    cav_a = loft("cav_a", [(p.FLOOR, notched), (p.NOTCH_TOP, notched),
                           (p.NOTCH_TOP + p.NOTCH_ROOF, plain)])
    cut(tray, cav_a)
    fl = p.LEADIN
    cav_b = loft("cav_b", [
        (p.NOTCH_TOP, plan_outline(p.WALL)),
        (d["TONGUE_TOP"] - fl, plan_outline(p.WALL)),
        (d["TONGUE_TOP"] + 0.01, plan_outline(p.WALL - fl - 0.01)),
        (d["TONGUE_TOP"] + 1.0, plan_outline(p.WALL - fl - 0.01)),
    ])
    cut(tray, cav_b)
    # floor slots around the latch flags
    for sx in (1, -1):
        x0 = d["FLAG_X0"] - p.FLAG_SLOT_IN
        x1 = d["FLAG_X1"] + p.FLAG_SLOT_TOOL
        y0, y1 = p.FLAG_Y[0], p.FLAG_Y[1] + p.FLAG_SLOT_OUT
        poly = rect(min(sx * x0, sx * x1), max(sx * x0, sx * x1), y0, y1)
        cut(tray, prism("fslot", poly, -1.0, p.FLOOR + 0.01))
    # stop walls
    for sx in (1, -1):
        xa, xb = sx * d["STOP_IN"], sx * d["STOP_OUT"]
        union(tray, prism("stop", rect(min(xa, xb), max(xa, xb), -(yc + 0.6), yc + 0.6),
                          p.FLOOR - 0.3, d["TONGUE_TOP"]))
    # floor rails
    for sy in (1, -1):
        y0, y1 = sorted((sy * p.FLOOR_RAIL_Y[0], sy * p.FLOOR_RAIL_Y[1]))
        union(tray, prism("frail", rect(-d["STOP_IN"] - 0.2, d["STOP_IN"] + 0.2, y0, y1),
                          p.FLOOR - 0.3, d["FLOOR_RAIL_TOP"]))
    # latch flags with their root blocks and hooks
    for sx in (1, -1):
        def X(a, b):
            return (min(sx * a, sx * b), max(sx * a, sx * b))
        x0, x1 = X(d["FLAG_X0"], d["FLAG_X1"])
        root = prism("root", rect(*X(d["STOP_OUT"] - 0.4, d["FLAG_X1"]),
                                  p.FLAG_Y[0] - 2.4, p.FLAG_Y[0]), p.FLOOR - 0.3, p.FLAG_TOP)
        flag = prism("flag", rect(x0, x1, p.FLAG_Y[0] - 0.3, p.FLAG_Y[1]), 0.0, p.FLAG_TOP)
        h0, h1 = p.HOOK_Z0, p.HOOK_Z0 + 0.4
        fx = d["FLAG_X1"]
        prof = [(fx - 0.2, h0), (fx + p.HOOK, h0), (fx + p.HOOK, h1), (fx - 0.2, h1 + p.HOOK + 0.2)]
        if sx < 0:
            prof = [(-x, z) for (x, z) in reversed(prof)]
        hook = prism_xz("hook", prof, p.HOOK_Y[0], p.HOOK_Y[1])
        union(tray, root, flag, hook)
    # bottom branding (mirrored so it reads from below)
    cut(tray, text_solid("brand", p.BRAND, 4.2, -1.0, p.TEXT_DEPTH, cy=2.6, mirror_x=True,
                         spacing=1.15))
    cut(tray, text_solid("model", p.MODEL, 2.1, -1.0, p.TEXT_DEPTH, cy=-3.2, mirror_x=True,
                         spacing=1.1))
    print(f"  tray built in {time.time() - t0:.1f}s")
    return tray


def build_lid(p=P, d=D):
    t0 = time.time()
    seam, ceil = d["SEAM"], d["CEIL"]
    lid = loft("SL01_Lid", outer_rings(seam, p.H, False, True))
    # hollow under the skin, leaving the skirt
    cut(lid, prism("under", plan_outline(p.SKIRT), seam - 1.0, ceil))
    # ceiling rails
    for sy in (1, -1):
        y0, y1 = sorted((sy * p.CEIL_RAIL_Y[0], sy * p.CEIL_RAIL_Y[1]))
        union(lid, prism("crail", rect(-d["STOP_IN"] + 0.2, d["STOP_IN"] - 0.2, y0, y1),
                         d["CEIL_RAIL_BOT"], ceil + 0.3))
    # latch hangers with pockets and lead-in chamfers
    for sx in (1, -1):
        xa, xb = sx * d["HANGER_X0"], sx * d["HANGER_X1"]
        hang = prism("hanger", rect(min(xa, xb), max(xa, xb), *p.HANGER_Y), p.HANGER_BOTTOM,
                     ceil + 0.3)
        union(lid, hang)
        hx0 = d["HANGER_X0"]
        pz0 = p.HOOK_Z0 - 0.1
        pocket = rect(hx0 - 0.5, hx0 + p.POCKET_DEPTH, pz0, pz0 + 1.6)
        lead = [(hx0 - 0.5, p.HANGER_BOTTOM - 0.5), (hx0 + 0.8 + 0.5, p.HANGER_BOTTOM - 0.5),
                (hx0 - 0.5, p.HANGER_BOTTOM + 0.8 + 0.5)]
        if sx < 0:
            pocket = [(-x, z) for (x, z) in reversed(pocket)]
            lead = [(-x, z) for (x, z) in reversed(lead)]
        cut(lid, prism_xz("pocket", pocket, p.HOOK_Y[0] - 0.5, p.HOOK_Y[1] + 0.5))
        cut(lid, prism_xz("pocket", pocket, -p.HOOK_Y[1] - 0.5, -p.HOOK_Y[0] + 0.5))
        cut(lid, prism_xz("lead", lead, p.HANGER_Y[0] - 1, p.HANGER_Y[1] + 1))
    # slot with a chamfered top edge
    sw, sl = d["SLOT_W"] / 2, d["SLOT_L"] / 2
    rr = p.KNOB_R + p.SLOT_CLEAR
    c = p.SLOT_CHAMFER
    slot = loft("slot", [
        (ceil - 1.0, rrect(sl, sw, rr, 8)),
        (p.H - c, rrect(sl, sw, rr, 8)),
        (p.H + 0.01, rrect(sl + c + 0.01, sw + c + 0.01, rr + c + 0.01, 8)),
        (p.H + 1.0, rrect(sl + c + 0.01, sw + c + 0.01, rr + c + 0.01, 8)),
    ])
    cut(lid, slot)
    # position marks beside the slot (long at the lock ends)
    y_in = sw + c + 0.6
    for i, x in enumerate(d["POSITIONS"]):
        end = i in (0, len(d["POSITIONS"]) - 1)
        ln = 2.4 if end else 1.3
        for sy in (1, -1):
            y0, y1 = sorted((sy * y_in, sy * (y_in + ln)))
            cut(lid, prism("mark", rect(x - p.MARK_W / 2, x + p.MARK_W / 2, y0, y1),
                           p.H - p.MARK_DEPTH, p.H + 1.0))
    print(f"  lid built in {time.time() - t0:.1f}s")
    return lid


def knob_rings(p=P, d=D, z0=None):
    hx, hy, r = p.KNOB_L / 2, p.KNOB_W / 2, p.KNOB_R
    zt = d["KNOB_TOP"]
    f = p.KNOB_FILLET
    rings = [(z0, rrect(hx, hy, r, 8)), (zt - f, rrect(hx, hy, r, 8))]
    for i in range(1, 7):
        a = math.radians(90 * i / 6)
        dz = f * math.sin(a)
        ins = f * (1 - math.cos(a))
        rings.append((zt - f + dz, rrect(hx - ins, hy - ins, max(r - ins, 0.3), 8)))
    # concentric top rings (so the saddle deformation stays smooth)
    for k in range(1, 7):
        ins = f + (hy - f - 0.15) * k / 6
        rings.append((zt, rrect(hx - ins, hy - ins, max(r - ins, 0.15), 8)))
    return rings


def saddle(ob, p=P, d=D):
    """Press a concave cylindrical thumb saddle (axis Y) into the knob's top."""
    zt = d["KNOB_TOP"]
    hx = p.KNOB_L / 2
    zf = zt - p.KNOB_FILLET - 0.6
    for v in ob.data.vertices:
        if v.co.z <= zf:
            continue
        w = min(1.0, (v.co.z - zf) / (zt - zf))
        g = max(0.0, 1 - (v.co.x / hx) ** 2)
        v.co.z -= p.KNOB_SADDLE * g * w * w
    ob.data.update()


def build_carriage(name, t, h, dots, p=P, d=D, separate_springs=False):
    """Carriage in ASSEMBLY coordinates, centred at x = 0."""
    z0, z1 = d["CZ0"], d["CZ1"]
    frame = prism(name, carriage_frame_outline(t), z0, z1)
    kn = loft("knob", knob_rings(z0=z1 - 0.3))
    saddle(kn)
    union(frame, kn)
    # identification dimples on the bottom (1 = Soft, 2 = Standard, 3 = Firm)
    for k in range(dots):
        x = (k - (dots - 1) / 2) * 2.4
        dimple = prism("dot", rrect(0.55, 0.55, 0.55, 6, cx=x, cy=0.0), z0 - 1.0, z0 + 0.4)
        cut(frame, dimple)
    springs = []
    for side in (-1, 1):
        poly = spring_outline(t)
        if side > 0:
            poly = [(-x, -y) for (x, y) in poly]
        springs.append(prism(f"{name}_spring{'L' if side < 0 else 'R'}", poly, z0, z0 + h))
    if separate_springs:
        return frame, springs
    union(frame, *springs)
    return frame


# =====================================================================================
# 5. DETENT MODEL
# =====================================================================================


def spring_k(t, h, L, E):
    return 3 * E * (h * t ** 3 / 12) / L ** 3


def detent_sim(t, h, E, p=P, d=D, step=0.02):
    """Quasi-static detent force model along the whole travel.

    For each carriage position the tooth nose (a circle) is pushed by its cantilever spring
    into the wall profile. Spring deflection -> spring force; the profile slope under the
    contact sets the axial force, with Coulomb friction mu on the flank. Both springs are
    summed. Returns positions, the force to push in +x and in -x, and each spring's
    deflection.
    """
    _, _, prof_m, prof_p = cavity_tracks()
    r = p.NOSE_R
    L = p.SPRING_ROOT_X + p.TOOTH_X
    k = spring_k(t, h, L, E)
    phi = math.atan(p.MU)
    tip_free = p.MID_DEPTH + p.PRELOAD

    def resample(prof):
        us = [q[0] for q in prof]
        vs = [q[1] for q in prof]
        return us, vs

    def v_at(us, vs, u):
        # linear interpolation on a monotonic-u polyline (the fillets keep u monotonic)
        lo, hi = 0, len(us) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if us[mid] <= u:
                lo = mid
            else:
                hi = mid
        u0, u1 = us[lo], us[hi]
        if u1 - u0 < 1e-12:
            return vs[lo]
        return vs[lo] + (vs[hi] - vs[lo]) * (u - u0) / (u1 - u0)

    walls = []
    for side, prof in ((-1, prof_m), (1, prof_p)):
        us, vs = resample(prof)
        walls.append((side, us, vs))

    def tip_pen(us, vs, ut):
        best = 1e9
        n = 60
        for i in range(n + 1):
            du = -r + 2 * r * i / n
            v = v_at(us, vs, ut + du) - math.sqrt(max(0.0, r * r - du * du))
            best = min(best, v)
        return best + r  # tip penetration

    xs = []
    x = -d["HALF_TRAVEL"]
    while x <= d["HALF_TRAVEL"] + 1e-9:
        xs.append(round(x, 6))
        x += step
    defl = {-1: [], 1: []}
    for side, us, vs in walls:
        a = p.TOOTH_X if side < 0 else -p.TOOTH_X
        for x in xs:
            pen = tip_pen(us, vs, x + a)
            defl[side].append(tip_free - pen)
    f_pos, f_neg = [], []
    for i, x in enumerate(xs):
        fp = fn = 0.0
        for side in (-1, 1):
            dl = defl[side]
            dd = max(dl[i], 0.0)
            if 0 < i < len(xs) - 1:
                slope = (dl[i + 1] - dl[i - 1]) / (xs[i + 1] - xs[i - 1])
            elif i == 0:
                slope = (dl[1] - dl[0]) / (xs[1] - xs[0])
            else:
                slope = (dl[-1] - dl[-2]) / (xs[-1] - xs[-2])
            Fs = k * dd
            al = math.atan(slope)
            if dd > 0:
                fp += Fs * math.tan(min(al + phi, math.radians(85)))
                fn += -Fs * math.tan(min(-al + phi, math.radians(85)))
        f_pos.append(fp)
        f_neg.append(fn)
    return dict(x=xs, f_push_pos=f_pos, f_push_neg=f_neg, defl_L=defl[-1], defl_R=defl[1],
                k=k, L=L)


def detent_summary(sim, p=P, d=D):
    xs, fp = sim["x"], sim["f_push_pos"]
    pos = d["POSITIONS"]
    out = {"k_N_per_mm": sim["k"], "beam_L_mm": sim["L"]}
    # breakaway leaving the -10 lock toward +x, and leaving a mid detent
    def peak(lo, hi, arr, fn_=max):
        vals = [f for x, f in zip(xs, arr) if lo <= x <= hi]
        return fn_(vals)
    out["lock_breakaway_N"] = peak(pos[0], pos[0] + p.PITCH / 2, fp)
    out["tick_breakaway_N"] = peak(pos[1], pos[1] + p.PITCH / 2, fp)
    out["tick_snap_N"] = peak(pos[1] - p.PITCH / 2, pos[1], fp, min)
    out["lock_snap_N"] = peak(pos[-1] - p.PITCH / 2, pos[-1], fp, min)
    out["land_drag_N"] = peak(pos[1] + 1.6, pos[1] + 2.0, fp)
    i_end = len(xs) - 1
    out["defl_at_stop_mm"] = sim["defl_L"][i_end]
    out["defl_seated_mid_mm"] = sim["defl_L"][xs.index(min(xs, key=lambda x: abs(x - pos[2])))]
    out["defl_max_mm"] = max(max(sim["defl_L"]), max(sim["defl_R"]))
    return out


# =====================================================================================
# 6. VALIDATION
# =====================================================================================


def deformed_spring_verts(spring_obj, side, tip_defl, p=P):
    """Bend a spring mesh as a tip-loaded cantilever (displacement toward the core)."""
    L = p.SPRING_ROOT_X + p.TOOTH_X
    xr = -p.SPRING_ROOT_X if side < 0 else p.SPRING_ROOT_X
    out = []
    slope_end = 1.5 * tip_defl / L
    for v in spring_obj.data.vertices:
        s = (v.co.x - xr) * (1 if side < 0 else -1)
        if s <= 0:
            dy = 0.0
        elif s <= L:
            dy = tip_defl * s * s * (3 * L - s) / (2 * L ** 3)
        else:
            dy = tip_defl + slope_end * (s - L)
        # left spring (-Y) deflects toward +Y; right toward -Y
        out.append(Vector((v.co.x, v.co.y + (dy if side < 0 else -dy), v.co.z)))
    return out


def min_dist(src_verts, tree, limit=5.0):
    best = (1e9, None)
    for v in src_verts:
        hit = tree.find_nearest(v, limit)
        if hit[0] is not None and hit[3] < best[0]:
            best = (hit[3], v.copy())
    return best


def surface_points(ob, filt=None, step=0.4, mat=None):
    """Points spread over every triangle (vertex-only sampling misses large faces)."""
    verts, tris = world_tris(ob, mat)
    pts = []
    for t in tris:
        a, b, c = (verts[i] for i in t)
        if filt is not None:
            lo = Vector([min(a[i], b[i], c[i]) for i in range(3)])
            hi = Vector([max(a[i], b[i], c[i]) for i in range(3)])
            if not filt(lo, hi):
                continue
        n = int(max((b - a).length, (c - b).length, (a - c).length) / step) + 1
        for i in range(n + 1):
            for j in range(n + 1 - i):
                pts.append(a + (b - a) * (i / n) + (c - a) * (j / n))
    return pts


def box(x=(-1e9, 1e9), y=(-1e9, 1e9), z=(-1e9, 1e9), absx=False, absy=False):
    """Triangle-bbox filter factory for surface_points (optionally on |x| / |y|)."""
    def f(lo, hi):
        def rng(a, b, ab):
            if ab:
                if a <= 0 <= b:
                    return 0.0, max(-a, b)
                return min(abs(a), abs(b)), max(abs(a), abs(b))
            return a, b
        lx, hx_ = rng(lo.x, hi.x, absx)
        ly, hy_ = rng(lo.y, hi.y, absy)
        return (lx <= x[1] and hx_ >= x[0] and ly <= y[1] and hy_ >= y[0] and
                lo.z <= z[1] and hi.z >= z[0])
    return f


def pick(pts, x=(-1e9, 1e9), y=(-1e9, 1e9), z=(-1e9, 1e9), absx=False, absy=False):
    out = []
    for q in pts:
        qx = abs(q.x) if absx else q.x
        qy = abs(q.y) if absy else q.y
        if x[0] <= qx <= x[1] and y[0] <= qy <= y[1] and z[0] <= q.z <= z[1]:
            out.append(q)
    return out


def thickness_scan(ob):
    me = ob.data
    me.calc_loop_triangles()
    verts = [ob.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    tree = BVHTree.FromPolygons(verts, tris)
    res = []
    for t in me.loop_triangles:
        if t.area < 0.02:
            continue
        c = ob.matrix_world @ t.center
        n = (ob.matrix_world.to_3x3() @ t.normal).normalized()
        o = c - n * 1e-3
        hit = tree.ray_cast(o, -n, 50.0)
        if hit[0] is None:
            continue
        if hit[1].dot(n) > -0.85:  # must exit through an opposing (near-parallel) face
            continue
        if set(tris[hit[2]]) & set(t.vertices):  # neighbouring face: a ray-at-an-edge artefact
            continue
        res.append((hit[3], tuple(round(x, 2) for x in c)))
    return res


def overhang_scan(verts, tris, z_bed=0.0, limit_deg=45.0):
    """Down-facing area steeper than limit (in print orientation), excluding the bed face."""
    lim = -math.cos(math.radians(90 - limit_deg)) - 0.01  # normal.z threshold (-0.717)
    flat, steep = [], []
    for t in tris:
        a, b, c = (verts[i] for i in t)
        n = (b - a).cross(c - a)
        area = n.length / 2
        if area < 1e-9:
            continue
        n.normalize()
        zc = (a.z + b.z + c.z) / 3
        if zc < z_bed + 0.05:
            continue
        if n.z < -0.999:
            flat.append((area, (a + b + c) / 3))
        elif n.z < lim:
            steep.append((area, (a + b + c) / 3))
    return flat, steep


def cluster(items, cell=3.0):
    """Group (area, point) items into coarse clusters for a readable report."""
    groups = {}
    for area, c in items:
        key = (round(c.x / cell), round(c.y / cell), round(c.z / 0.5))
        g = groups.setdefault(key, [0.0, [1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]])
        g[0] += area
        for i in range(3):
            g[1][i] = min(g[1][i], c[i])
            g[2][i] = max(g[2][i], c[i])
    # merge neighbours at the same z
    out = []
    for key, (area, lo, hi) in groups.items():
        merged = False
        for o in out:
            if abs(o["z"] - (lo[2] + hi[2]) / 2) < 0.3 and \
               lo[0] <= o["hi"][0] + cell and hi[0] >= o["lo"][0] - cell and \
               lo[1] <= o["hi"][1] + cell and hi[1] >= o["lo"][1] - cell:
                o["area"] += area
                o["lo"] = [min(a, b) for a, b in zip(o["lo"], lo)]
                o["hi"] = [max(a, b) for a, b in zip(o["hi"], hi)]
                merged = True
                break
        if not merged:
            out.append(dict(area=area, lo=lo, hi=hi, z=(lo[2] + hi[2]) / 2))
    return sorted(out, key=lambda o: -o["area"])


def section_polylines(ob, co, no, mat=None):
    """Cut a mesh with a plane and return the cut as a list of 3D polylines."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform((mat or Matrix()) @ ob.matrix_world)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
    cut_edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in cut_edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    used, lines = set(), []
    for start in list(adj):
        if start in used:
            continue
        line = [start]
        used.add(start)
        cur = start
        while True:
            nxt = [w for w in adj[cur] if w not in used]
            if not nxt:
                break
            cur = nxt[0]
            used.add(cur)
            line.append(cur)
        lines.append([tuple(round(c, 4) for c in v.co) for v in line])
    bm.free()
    return lines


# =====================================================================================
# 7. EXPORT
# =====================================================================================


def write_stl(path, verts, tris, name="SlideLock"):
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            a, b, c = (verts[i] for i in t)
            n = (b - a).cross(c - a)
            if n.length > 0:
                n.normalize()
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z,
                                c.x, c.y, c.z, 0))


def write_3mf(path, objects):
    """objects: list of (name, verts, tris, (tx, ty), hexcolor)."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<model unit="millimeter" xml:lang="en-US" '
           'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
           'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
           '<metadata name="Title">Odd Layer SlideLock SL-01</metadata>',
           '<metadata name="Designer">Odd Layer</metadata>',
           '<resources>', '<m:colorgroup id="100">']
    for o in objects:
        xml.append(f'<m:color color="{o[4]}"/>')
    xml.append("</m:colorgroup>")
    for i, (name, verts, tris, _, _) in enumerate(objects):
        oid = i + 1
        xml.append(f'<object id="{oid}" name="{name}" type="model" pid="100" pindex="{i}">'
                   "<mesh><vertices>")
        xml.extend(f'<vertex x="{v.x:.4f}" y="{v.y:.4f}" z="{v.z:.4f}"/>' for v in verts)
        xml.append("</vertices><triangles>")
        xml.extend(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        xml.append("</triangles></mesh></object>")
    xml.append("</resources><build>")
    for i, (_, _, _, (tx, ty), _) in enumerate(objects):
        xml.append(f'<item objectid="{i + 1}" transform="1 0 0 0 1 0 0 0 1 {tx:.3f} {ty:.3f} 0"/>')
    xml.append("</build></model>")
    ct = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          "</Types>")
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(xml))


def print_matrix(kind, p=P):
    """Assembly -> print orientation. Lid prints top-face down (flipped about X)."""
    if kind == "lid":
        return Matrix.Translation((0, 0, p.H)) @ Matrix.Rotation(math.pi, 4, "X")
    if kind == "carriage":
        return Matrix.Translation((0, 0, -D["CZ0"]))
    return Matrix()


# =====================================================================================
# 8. SCENE: materials, collections, cameras, lights, renders
# =====================================================================================


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


COLORS = {"graphite": "2B2D31", "orange": "FF6A13", "sand": "D9D3C7", "white": "EDEDEA"}


def make_material(name, hexcol, rough=0.5, layer_bump=0.12, bed_texture=False):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.45
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    # FDM layer lines: 0.2 mm period along the print Z axis (object Z for all parts here)
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 2 * math.pi / 0.2
    links.new(sep.outputs["Z"], mul.inputs[0])
    sin = nodes.new("ShaderNodeMath")
    sin.operation = "SINE"
    links.new(mul.outputs[0], sin.inputs[0])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = layer_bump
    bump.inputs["Distance"].default_value = 0.03
    height = sin.outputs[0]
    if bed_texture:
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 1.8
        noise.inputs["Detail"].default_value = 6.0
        links.new(tc.outputs["Object"], noise.inputs["Vector"])
        geo = nodes.new("ShaderNodeNewGeometry")
        sepn = nodes.new("ShaderNodeSeparateXYZ")
        links.new(geo.outputs["Normal"], sepn.inputs[0])
        absn = nodes.new("ShaderNodeMath")
        absn.operation = "ABSOLUTE"
        links.new(sepn.outputs["Z"], absn.inputs[0])
        gt = nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.98
        links.new(absn.outputs[0], gt.inputs[0])
        mixh = nodes.new("ShaderNodeMix")
        mixh.data_type = "FLOAT"
        links.new(gt.outputs[0], mixh.inputs["Factor"])
        links.new(sin.outputs[0], mixh.inputs["A"])
        links.new(noise.outputs["Fac"], mixh.inputs["B"])
        height = mixh.outputs["Result"]
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def set_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = False


def smooth_by_angle(ob, deg=35):
    me = ob.data
    for poly in me.polygons:
        poly.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(deg))
    except AttributeError:  # Blender < 4.1
        me.use_auto_smooth = True
        me.auto_smooth_angle = math.radians(deg)


def linked_copy(ob, name, coll, mat=Matrix()):
    c = bpy.data.objects.new(name, ob.data)
    c.matrix_world = mat @ ob.matrix_world
    coll.objects.link(c)
    return c


def add_camera(name, loc, target, lens=85, ortho=None, coll=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 5000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cam)
    (coll or COLL["SL01_Cameras"]).objects.link(ob)
    ob.location = loc
    d_ = Vector(target) - Vector(loc)
    ob.rotation_euler = d_.to_track_quat("-Z", "Y").to_euler()
    return ob


def add_area(name, loc, target, size, power, color=(1, 1, 1), coll=None):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size = size
    lt.energy = power
    lt.color = color
    ob = bpy.data.objects.new(name, lt)
    (coll or COLL["SL01_Lights"]).objects.link(ob)
    ob.location = loc
    d_ = Vector(target) - Vector(loc)
    ob.rotation_euler = d_.to_track_quat("-Z", "Y").to_euler()
    return ob


def build_studio():
    coll = collection("SL01_Studio")
    # seamless cyclorama: floor that curves up behind the product
    bm = bmesh.new()
    Rb = 250.0
    prof = [(-900.0, 0.0)] + [(300.0 + Rb * math.sin(math.radians(90 * i / 24)),
                               Rb - Rb * math.cos(math.radians(90 * i / 24))) for i in range(25)]
    prof.append((300.0 + Rb, 1200.0))
    rows = []
    for y in (-1200.0, 1200.0):
        rows.append([bm.verts.new((y, x, z)) for (x, z) in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    ob = obj_from_bm("SL01_Backdrop", bm, coll)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    m = bpy.data.materials.new("Backdrop")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_lin("C9C6C0")
    b.inputs["Roughness"].default_value = 0.7
    ob.data.materials.append(m)
    ob.location.z = -0.01
    return ob


def setup_render(scene, samples, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.render.image_settings.file_format = "PNG"
    w = scene.world or bpy.data.worlds.new("World")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_lin("D6D3CE")
    bg.inputs["Strength"].default_value = 0.35


# =====================================================================================
# 9. MAIN
# =====================================================================================


EXPECTED_CLEARANCE = {
    "pad_to_wall": P.CLEAR_SIDE,
    "carriage_bottom_to_floor_rail": P.CLEAR_Z,
    "carriage_top_to_ceiling_rail": P.CLEAR_Z,
    "knob_to_slot": P.SLOT_CLEAR,
    "knob_to_slot_end_at_full_travel": P.SLOT_CLEAR,
    "lid_skirt_to_tongue": P.FIT_LID,
    "lid_ceiling_to_tongue_top": P.TONGUE_GAP,
    "lid_hanger_to_tray": 0.10,   # hook lower face to pocket floor (latch play)
    "hook_tip_to_pocket_floor": 0.20,
}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--res", default="1600x1200")
    ap.add_argument("--only", default="", help="comma list of render names")
    ap.add_argument("--no-sweep", action="store_true")
    args = ap.parse_args(argv)
    out = os.path.abspath(args.out)
    for sub in ("models/stl", "models/3mf", "renders", "docs"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    T0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    collection("_work")
    report = {"params": {k: getattr(P, k) for k in dir(P) if k.isupper()},
              "derived": D, "checks": {}, "warnings": []}

    # ---------------- 2D sanity checks ----------------
    for inset in (0.0, P.SKIRT, P.SKIRT + P.FIT_LID, P.WALL, 0.586 * P.EDGE_R):
        poly = plan_outline(inset)
        # convexity: every turn must be a left turn (CCW)
        bad = 0
        for i in range(len(poly)):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % len(poly)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if cr < -1e-9:
                bad += 1
        assert bad == 0, f"plan offset {inset} is not convex ({bad} reflex vertices)"
    report["checks"]["plan_offsets_convex"] = True

    # ---------------- build parts ----------------
    print("Building parts ...")
    tray = build_tray()
    lid = build_lid()
    carriages = {}
    for name, t, h, dots in P.VARIANTS:
        carriages[name] = build_carriage(f"SL01_Carriage_{name}", t, h, dots)
    carriage = carriages["Standard"]
    # loose copies of the standard frame and springs for the motion sweep
    frame_s, springs_s = build_carriage("chk_Carriage", P.SPRING_T, P.SPRING_H, 2,
                                        separate_springs=True)

    # ---------------- per-part mesh checks ----------------
    print("Checking meshes ...")
    parts = {"Tray": tray, "Lid": lid}
    parts.update({f"Carriage_{k}": v for k, v in carriages.items()})
    pstats = {}
    for k, ob in parts.items():
        s = mesh_stats(ob)
        s["mass_PETG_g_solid"] = s["volume_mm3"] / 1000 * P.DENSITY["PETG"]
        pstats[k] = s
        if s["nonmanifold_edges"] or s["shells"] != 1:
            report["warnings"].append(f"{k}: {s['nonmanifold_edges']} non-manifold edges, "
                                      f"{s['shells']} shells")
    report["parts"] = pstats

    # ---------------- static interference (assembled, centre detent) ----------------
    print("Interference / clearance checks ...")
    tr_tree, tr_v, _ = bvh(tray)
    lid_tree, lid_v, _ = bvh(lid)
    fr_tree, fr_v, _ = bvh(frame_s)
    checks = {}
    # the lid bears on the tray at the parting line (designed contact): test interference with
    # the lid raised 0.01 mm so touching faces are not counted as intersections
    lid_up, _, _ = bvh(lid, Matrix.Translation((0, 0, 0.01)))
    checks["tray_x_lid_overlap_pairs"] = len(tr_tree.overlap(lid_up))
    lid_rot, _, _ = bvh(lid, Matrix.Translation((0, 0, 0.01)) @ Matrix.Rotation(math.pi, 4, "Z"))
    checks["tray_x_lid_rotated180_overlap_pairs"] = len(tr_tree.overlap(lid_rot))
    checks["frame_x_tray_overlap_pairs"] = len(fr_tree.overlap(tr_tree))
    checks["frame_x_lid_overlap_pairs"] = len(fr_tree.overlap(lid_tree))

    # designed clearances, measured from points spread over the faces
    d = D
    clear = {}

    where = {}

    def gap(src, filt, tree, **kw):
        pts = pick(surface_points(src, filt, 0.35), **kw)
        if not pts:
            return None
        dist, loc = min_dist(pts, tree, 12.0)
        gap.last = [round(c, 2) for c in loc] if loc is not None else None
        return dist

    clear["pad_to_wall"] = gap(frame_s, box(y=(d["PAD_Y"] - 0.01, 99), absy=True), tr_tree,
                               y=(d["PAD_Y"] - 0.01, 99), absy=True)
    where["pad_to_wall"] = gap.last
    clear["carriage_bottom_to_floor_rail"] = gap(
        frame_s, box(z=(-1, d["CZ0"] + 0.01)), tr_tree, z=(-1, d["CZ0"] + 0.01),
        y=P.FLOOR_RAIL_Y, absy=True)
    where["carriage_bottom_to_floor_rail"] = gap.last
    clear["carriage_top_to_ceiling_rail"] = gap(
        frame_s, box(z=(d["CZ1"] - 0.01, d["CZ1"] + 0.01)), lid_tree,
        z=(d["CZ1"] - 0.01, d["CZ1"] + 0.01), y=P.CEIL_RAIL_Y, absy=True)
    where["carriage_top_to_ceiling_rail"] = gap.last
    clear["knob_to_slot"] = gap(frame_s, box(z=(d["CEIL"] + 0.05, P.H + 0.3)), lid_tree,
                                z=(d["CEIL"] + 0.05, P.H + 0.3))
    where["knob_to_slot"] = gap.last
    # at full travel the carriage end lands on the stop wall (designed contact) and the knob
    # still clears the slot end
    Mend = Matrix.Translation((d["HALF_TRAVEL"], 0, 0))
    fr_end, _, _ = bvh(frame_s, Mend)
    pts = pick(surface_points(frame_s, box(x=(P.CARR_L / 2 - 0.01, 99)), 0.35, Mend),
               x=(P.CARR_L / 2 + d["HALF_TRAVEL"] - 0.01, 99))
    clear["carriage_end_on_stop_contact"] = min_dist(pts, tr_tree, 3.0)[0]
    pts = pick(surface_points(frame_s, box(z=(d["CEIL"] + 0.05, P.H + 0.3)), 0.35, Mend),
               z=(d["CEIL"] + 0.05, P.H + 0.3))
    clear["knob_to_slot_end_at_full_travel"] = min_dist(pts, lid_tree, 6.0)[0]
    checks["frame_x_tray_overlap_at_full_travel"] = len(
        bvh(frame_s, Matrix.Translation((d["HALF_TRAVEL"] - 0.01, 0, 0)))[0].overlap(tr_tree))
    sz = (d["SEAM"] + 0.25, d["CEIL"] - 0.25)
    clear["lid_skirt_to_tongue"] = gap(lid, box(z=sz), tr_tree, z=sz)
    where["lid_skirt_to_tongue"] = gap.last
    clear["lid_ceiling_to_tongue_top"] = gap(
        lid, box(z=(d["CEIL"] - 0.01, d["CEIL"] + 0.01), y=(d["YC"] - 0.5, 99), absy=True), tr_tree,
        z=(d["CEIL"] - 0.01, d["CEIL"] + 0.01), y=(d["YC"] - 0.5, 99), absy=True)
    where["lid_ceiling_to_tongue_top"] = gap.last
    clear["lid_hanger_to_tray"] = gap(
        lid, box(x=(d["HANGER_X0"] - 0.01, d["HANGER_X1"] + 0.01), y=(-9, 9), z=(0, d["CEIL"] - 0.05),
                 absx=True), tr_tree,
        x=(d["HANGER_X0"] - 0.01, d["HANGER_X1"] + 0.01), y=(-9, 9), z=(0, d["CEIL"] - 0.05), absx=True)
    where["lid_hanger_to_tray"] = gap.last
    hz = (P.HOOK_Z0 + 0.15, P.HOOK_Z0 + 0.41)
    clear["hook_tip_to_pocket_floor"] = gap(
        tray, box(x=(d["FLAG_X1"] + P.HOOK - 0.01, d["FLAG_X1"] + P.HOOK + 0.01), z=hz, absx=True),
        lid_tree, x=(d["FLAG_X1"] + P.HOOK - 0.01, d["FLAG_X1"] + P.HOOK + 0.01), z=hz, absx=True)
    where["hook_tip_to_pocket_floor"] = gap.last
    clear["lid_seam_step_contact"] = gap(lid, box(z=(d["SEAM"] - 0.001, d["SEAM"] + 0.001)), tr_tree,
                                         z=(d["SEAM"] - 0.001, d["SEAM"] + 0.001))
    where["lid_seam_step_contact"] = gap.last
    checks["clearances_mm"] = clear
    checks["clearance_locations"] = where

    # ---------------- motion sweep with springs bent to the detent model ----------------
    sims = {}
    for name, t, h, _ in P.VARIANTS:
        for mat in ("PETG", "PLA"):
            sims[(name, mat)] = detent_sim(t, h, P.E_MODULUS[mat])
    sim = sims[("Standard", "PETG")]
    report["detent"] = {f"{n}_{m}": detent_summary(s) for (n, m), s in sims.items()}
    sweep = {"positions": 0, "overlaps": 0, "min_tooth_wall_gap": 1e9, "worst": None,
             "frame_overlaps": 0}
    if not args.no_sweep:
        print("Motion sweep ...")
        xs = sim["x"]
        idx = list(range(0, len(xs), 5))
        if idx[-1] != len(xs) - 1:
            idx.append(len(xs) - 1)
        for i in idx:
            x = xs[i]
            if abs(x) > d["HALF_TRAVEL"] - 0.02:
                x = math.copysign(d["HALF_TRAVEL"] - 0.02, x)
            M = Matrix.Translation((x, 0, 0))
            ft, _, _ = bvh(frame_s, M)
            ov = len(ft.overlap(tr_tree)) + len(ft.overlap(lid_tree))
            sweep["frame_overlaps"] += 1 if ov else 0
            for sp, side, dl in ((springs_s[0], -1, sim["defl_L"][i]),
                                 (springs_s[1], 1, sim["defl_R"][i])):
                vs = [M @ v for v in deformed_spring_verts(sp, side, dl + SWEEP_MARGIN)]
                sp.data.calc_loop_triangles()
                tris = [tuple(t.vertices) for t in sp.data.loop_triangles]
                st = BVHTree.FromPolygons(vs, tris)
                o = st.overlap(tr_tree)
                if o:
                    sweep["overlaps"] += 1
                g = min_dist([v for v in vs if abs(v.y) > d["YC"] - 0.3], tr_tree, 3.0)[0]
                if g < sweep["min_tooth_wall_gap"]:
                    sweep["min_tooth_wall_gap"] = g
                    sweep["worst"] = (x, side)
            sweep["positions"] += 1
        # free-state springs at a seated mid detent: expected preload interference
        report["checks"]["spring_preload_overlap_pairs_free_state"] = len(
            bvh(springs_s[0])[0].overlap(tr_tree))
    checks["motion_sweep"] = sweep

    # spring stresses (cantilever, tip load)
    sp = {}
    for name, t, h, _ in P.VARIANTS:
        L = P.SPRING_ROOT_X + P.TOOTH_X
        defl_work = P.MID_DEPTH + P.PRELOAD
        gap = P.SPRING_GAP + (P.SPRING_T - t)  # thicker spring grows inward
        sp[name] = dict(
            t=t, h=h, L=L,
            strain_working_pct=100 * 1.5 * t * defl_work / L ** 2,
            strain_at_overtravel_stop_pct=100 * 1.5 * t * gap / L ** 2,
            overtravel_stop_mm=gap,
            k_PETG=spring_k(t, h, L, P.E_MODULUS["PETG"]),
            k_PLA=spring_k(t, h, L, P.E_MODULUS["PLA"]))
    report["springs"] = sp
    Lf = abs(P.HOOK_Y[0] + P.HOOK_Y[1]) / 2 - P.FLAG_Y[0]
    report["latch"] = dict(flag_L=Lf, flag_t=P.FLAG_T, deflection=P.HOOK - 0.2,
                           strain_pct=100 * 1.5 * P.FLAG_T * (P.HOOK - 0.2) / Lf ** 2,
                           force_N_PETG=spring_k(P.FLAG_T, P.FLAG_TOP - P.FLOOR, Lf, 2000) *
                           (P.HOOK - 0.2))

    # ---------------- wall thickness ----------------
    print("Wall thickness scan ...")
    thick = {}
    for k in ("Tray", "Lid", "Carriage_Standard"):
        res = thickness_scan(parts[k])
        res.sort()

        def engraving(c):
            return (k == "Tray" and c[2] < P.TEXT_DEPTH + 0.05 and abs(c[0]) < 24 and abs(c[1]) < 7) or \
                   (k == "Lid" and c[2] > P.H - P.MARK_DEPTH - 0.05) or \
                   (k.startswith("Carriage") and c[2] < D["CZ0"] + 0.45 and abs(c[1]) < 1)
        eng = [r for r in res if engraving(r[1])]
        res = [r for r in res if not engraving(r[1])]
        thin = [r for r in res if r[0] < 1.19]
        thick[k] = dict(samples=len(res), min=res[0][0], min_at=res[0][1],
                        thin_count=len(thin), thin_examples=thin[:12],
                        engraving_min=min((r[0] for r in eng), default=None))
    report["thickness"] = thick

    # ---------------- print orientation and overhangs ----------------
    print("Overhang scan ...")
    ovh = {}
    kinds = {"Tray": "tray", "Lid": "lid", "Carriage_Standard": "carriage"}
    for k, kind in kinds.items():
        verts, tris = world_tris(parts[k], print_matrix(kind))
        zmin = min(v.z for v in verts)
        verts = [Vector((v.x, v.y, v.z - zmin)) for v in verts]
        flat, steep = overhang_scan(verts, tris)
        ovh[k] = dict(flat_down_area=sum(a for a, _ in flat),
                      steep_area=sum(a for a, _ in steep),
                      flat_clusters=[dict(area=round(c["area"], 2),
                                          lo=[round(x, 2) for x in c["lo"]],
                                          hi=[round(x, 2) for x in c["hi"]])
                                     for c in cluster(flat)][:30],
                      steep_clusters=[dict(area=round(c["area"], 3),
                                           lo=[round(x, 2) for x in c["lo"]],
                                           hi=[round(x, 2) for x in c["hi"]])
                                      for c in cluster(steep)][:30])
    report["overhangs"] = ovh
    report["checks"].update(checks)

    # ---------------- sections for the drawings ----------------
    print("Sections ...")
    secs = {}
    allp = {"tray": tray, "lid": lid, "carriage": carriage}
    for nm, co, no in (("x0", (0, 0, 0), (1, 0, 0)), ("y0", (0, 0, 0), (0, 1, 0)),
                       ("z6", (0, 0, 6.0), (0, 0, 1)), ("x_tooth", (P.TOOTH_X, 0, 0), (1, 0, 0))):
        secs[nm] = {k: section_polylines(o, Vector(co), Vector(no)) for k, o in allp.items()}
    _, _, prof_m, prof_p = cavity_tracks()
    geo = dict(sections=secs, plan=plan_outline(0.0), plan_top=plan_outline(0.586 * P.EDGE_R),
               track_m=prof_m, track_p=prof_p, spring=spring_outline(P.SPRING_T),
               frame=carriage_frame_outline(P.SPRING_T),
               sims={f"{n}_{m}": {k: v for k, v in s.items()} for (n, m), s in sims.items()},
               derived=D, params=report["params"])
    with open(os.path.join(out, "models", "SL01_geometry.json"), "w") as f:
        json.dump(geo, f)

    # ---------------- exports ----------------
    print("Exporting ...")
    files = []
    stl_dir = os.path.join(out, "models", "stl")
    plate = []
    exports = [("SL01_Tray", tray, "tray"), ("SL01_Lid", lid, "lid")]
    exports += [(f"SL01_Carriage_{k}", v, "carriage") for k, v in carriages.items()]
    plate_xy = PLATE_XY
    colors = {"SL01_Tray": "#2B2D31", "SL01_Lid": "#2B2D31"}
    for name, ob, kind in exports:
        verts, tris = world_tris(ob, print_matrix(kind))
        zmin = min(v.z for v in verts)
        verts = [Vector((v.x, v.y, v.z - zmin)) for v in verts]
        pth = os.path.join(stl_dir, name + ".stl")
        write_stl(pth, verts, tris, name)
        files.append(os.path.relpath(pth, out))
        plate.append((name, verts, tris, plate_xy[name], colors.get(name, "#FF6A13")))
    p3 = os.path.join(out, "models", "3mf", "SL01_full_set.3mf")
    write_3mf(p3, plate)
    p3b = os.path.join(out, "models", "3mf", "SL01_starter_plate.3mf")
    write_3mf(p3b, [o for o in plate if o[0] in ("SL01_Tray", "SL01_Lid", "SL01_Carriage_Standard")])
    files += [os.path.relpath(p3, out), os.path.relpath(p3b, out)]
    report["files"] = files

    # ---------------- scene organisation ----------------
    print("Organising scene ...")
    scn = organise_scene(tray, lid, carriages, frame_s, springs_s, sim, exports, plate_xy)

    # ---------------- validation summary ----------------
    ok = True
    summ = []

    def chk(name, cond, detail):
        nonlocal ok
        ok = ok and cond
        summ.append(dict(check=name, passed=bool(cond), detail=detail))

    for k, s in pstats.items():
        chk(f"{k}: one closed manifold shell", s["shells"] == 1 and s["nonmanifold_edges"] == 0,
            f"{s['shells']} shell(s), {s['nonmanifold_edges']} non-manifold edges")
    chk("Tray and lid do not intersect", checks["tray_x_lid_overlap_pairs"] == 0,
        f"{checks['tray_x_lid_overlap_pairs']} intersecting triangle pairs (assembled; seam "
        f"contact excluded)")
    chk("Lid also fits turned 180 degrees (fool-proof assembly)",
        checks["tray_x_lid_rotated180_overlap_pairs"] == 0,
        f"{checks['tray_x_lid_rotated180_overlap_pairs']} intersecting triangle pairs")
    chk("Carriage frame does not intersect the tray at full travel",
        checks["frame_x_tray_overlap_at_full_travel"] == 0, "carriage 0.01 mm short of the stop")
    chk("Carriage frame does not intersect tray or lid (centre)",
        checks["frame_x_tray_overlap_pairs"] + checks["frame_x_lid_overlap_pairs"] == 0,
        "frame = carriage without springs")
    if not args.no_sweep:
        chk("Full-travel sweep: no rigid-part intersection", sweep["frame_overlaps"] == 0,
            f"{sweep['positions']} positions, every 0.1 mm over 20 mm")
        chk("Full-travel sweep: bent springs never cut the wall", sweep["overlaps"] == 0,
            f"min tooth-wall gap {sweep['min_tooth_wall_gap']:.3f} mm "
            f"(springs bent to the model deflection + {SWEEP_MARGIN} mm)")
    for k, v in clear.items():
        if k.endswith("contact"):
            chk(f"Designed contact {k}", v is not None and v < 0.01, f"{v:.3f} mm")
        else:
            exp = EXPECTED_CLEARANCE.get(k)
            okc = v is not None and v >= 0.08 and (exp is None or abs(v - exp) < 0.03)
            chk(f"Clearance {k}", okc, f"{v:.3f} mm" + (f" (design {exp:.2f})" if exp else ""))
    for k, s in sp.items():
        chk(f"Spring {k}: working strain < 0.8 %", s["strain_working_pct"] < 0.8,
            f"{s['strain_working_pct']:.2f} % working, {s['strain_at_overtravel_stop_pct']:.2f} % "
            f"at the overtravel stop")
    for k, o in ovh.items():
        chk(f"{k}: no unsupported overhang steeper than 45 deg", o["steep_area"] < 0.5,
            f"{o['steep_area']:.2f} mm2 steep, {o['flat_down_area']:.1f} mm2 flat down-facing "
            f"(bridges / small ledges, see clusters)")
    report["summary"] = summ
    report["all_passed"] = ok
    report["elapsed_s"] = time.time() - T0
    with open(os.path.join(out, "models", "SL01_validation.json"), "w") as f:
        json.dump(report, f, indent=1, default=lambda o: list(o) if hasattr(o, "__iter__") else str(o))
    print("\nVALIDATION")
    for s in summ:
        print(("  PASS " if s["passed"] else "  FAIL ") + s["check"] + " -- " + s["detail"])
    print(json.dumps(report["detent"]["Standard_PETG"], indent=1))

    # ---------------- studio, cameras, renders ----------------
    build_studio()
    setup_render(scene, args.samples, tuple(int(v) for v in args.res.split("x")))
    for ob in (tray, lid, *carriages.values(), *scn["cut"]):
        smooth_by_angle(ob, 32)
    txt = bpy.data.texts.new("slidelock.py")
    try:
        txt.from_string(open(os.path.abspath(__file__)).read())
    except Exception:
        pass
    shots = setup_shots(scene, scn)
    blend = os.path.join(out, "models", "SL01_SlideLock.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("saved", blend)
    if args.render:
        only = [s for s in args.only.split(",") if s]
        for name, fn in shots:
            if only and name not in only:
                continue
            t0 = time.time()
            fn()
            scene.render.filepath = os.path.join(out, "renders", name + ".png")
            bpy.ops.render.render(write_still=True)
            print(f"  rendered {name} in {time.time() - t0:.0f}s")
    print(f"done in {time.time() - T0:.0f}s")


# ---------------------------------------------------------------------------------------
# presentation: collections, cutaway, colourways, print plate, cameras and shots
# ---------------------------------------------------------------------------------------

PLATE_XY = {"SL01_Tray": (128, 162), "SL01_Lid": (128, 122), "SL01_Carriage_Standard": (128, 80),
            "SL01_Carriage_Soft": (78, 80), "SL01_Carriage_Firm": (178, 80)}
STRIPE_Z = (4.2, 4.8)  # optional "odd layer" signature stripe: a filament swap on 3 layers


def stripe_material(name, base_hex, stripe_hex, z0, z1):
    m = make_material(name, base_hex, 0.52, 0.10, bed_texture=True)
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tc.outputs["Object"], sep.inputs[0])
    a = nodes.new("ShaderNodeMath")
    a.operation = "GREATER_THAN"
    a.inputs[1].default_value = z0
    b = nodes.new("ShaderNodeMath")
    b.operation = "LESS_THAN"
    b.inputs[1].default_value = z1
    links.new(sep.outputs["Z"], a.inputs[0])
    links.new(sep.outputs["Z"], b.inputs[0])
    both = nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    links.new(a.outputs[0], both.inputs[0])
    links.new(b.outputs[0], both.inputs[1])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = hex_lin(base_hex)
    mix.inputs["B"].default_value = hex_lin(stripe_hex)
    links.new(both.outputs[0], mix.inputs["Factor"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def override_material(ob, mat):
    ob.material_slots[0].link = "OBJECT"
    ob.material_slots[0].material = mat


def move_to(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def organise_scene(tray, lid, carriages, frame_s, springs_s, sim, exports, plate_xy, p=P, d=D):
    carriage = carriages["Standard"]
    c_asm = collection("SL01_Assembly")
    c_var = collection("SL01_CarriageVariants")
    c_exp = collection("SL01_Exploded")
    c_cut = collection("SL01_Cutaway")
    c_bot = collection("SL01_BottomView")
    c_col = collection("SL01_Colourways")
    c_plate = collection("SL01_PrintPlate")
    collection("SL01_Cameras")
    collection("SL01_Lights")
    mats = {
        "g": make_material("SL_Graphite", COLORS["graphite"], 0.52, 0.10, bed_texture=True),
        "o": make_material("SL_Orange", COLORS["orange"], 0.42, 0.10),
        "og": make_material("SL_Orange_Body", COLORS["orange"], 0.45, 0.10, bed_texture=True),
        "gc": make_material("SL_Graphite_Carriage", COLORS["graphite"], 0.5, 0.10),
        "stripe": stripe_material("SL_Graphite_Stripe", COLORS["graphite"], COLORS["orange"],
                                  *STRIPE_Z),
    }
    for ob in (tray, lid):
        set_material(ob, mats["g"])
    for ob in carriages.values():
        set_material(ob, mats["o"])
    for ob in (tray, lid, carriage):
        move_to(ob, c_asm)
    for k, ob in carriages.items():
        if k != "Standard":
            move_to(ob, c_var)
            ob.location = (0, 45 if k == "Soft" else -45, 0)
    for ob in (tray, lid, *carriages.values()):
        ob["odd_layer_part"] = ob.name
        ob["status"] = "CAD only - not yet printed"
    tray["print_orientation"] = "as modelled (floor on the bed)"
    lid["print_orientation"] = "flipped: top face on the bed"
    for ob in carriages.values():
        ob["print_orientation"] = "as modelled (bottom on the bed, knob up)"

    # exploded view
    linked_copy(tray, "EXP_Tray", c_exp)
    linked_copy(carriage, "EXP_Carriage", c_exp, Matrix.Translation((0, 0, 24)))
    linked_copy(lid, "EXP_Lid", c_exp, Matrix.Translation((0, 0, 50)))

    # cutaway at mid height, carriage at the -5 tick, springs bent to the model deflection
    xc = -p.PITCH
    i = min(range(len(sim["x"])), key=lambda k: abs(sim["x"][k] - xc))
    zc = 6.6
    cut_c = bpy.data.objects.new("CUT_Carriage", frame_s.data.copy())
    c_cut.objects.link(cut_c)
    for sp, side, dl in ((springs_s[0], -1, sim["defl_L"][i]), (springs_s[1], 1, sim["defl_R"][i])):
        me = sp.data.copy()
        for v, co in zip(me.vertices, deformed_spring_verts(sp, side, dl)):
            v.co = co
        o = bpy.data.objects.new("cut_spring", me)
        c_cut.objects.link(o)
        apply_bool(cut_c, o, "UNION")
    big = rect(-60, 60, -30, 30)
    apply_bool(cut_c, prism("cutbox", big, zc, 40, c_cut), "DIFFERENCE")
    cut_c.location = (xc, 0, 0)
    set_material(cut_c, mats["o"])
    cut_t = bpy.data.objects.new("CUT_Tray", tray.data.copy())
    c_cut.objects.link(cut_t)
    apply_bool(cut_t, prism("cutbox", big, zc, 40, c_cut), "DIFFERENCE")
    set_material(cut_t, mats["g"])
    for ob in [frame_s] + springs_s:
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    if "_work" in COLL and COLL["_work"].name in bpy.data.collections:
        bpy.data.collections.remove(COLL["_work"])

    # bottom view: the assembly turned over about Y (so the engraving reads correctly)
    flip = Matrix.Translation((0, 0, p.H)) @ Matrix.Rotation(math.pi, 4, "Y")
    for ob in (tray, lid, carriage):
        linked_copy(ob, "BOT_" + ob.name, c_bot, flip)

    # colourways: core, signature stripe, inverse
    rows = [(-42, "g", "g", "o"), (0, "stripe", "g", "o"), (42, "og", "og", "gc")]
    for k, (y, mt, ml, mc) in enumerate(rows):
        M = Matrix.Translation((0, y, 0))
        a = linked_copy(tray, f"COL{k}_Tray", c_col, M)
        b = linked_copy(lid, f"COL{k}_Lid", c_col, M)
        c = linked_copy(carriage, f"COL{k}_Carriage", c_col, M @ Matrix.Translation((5.0 * (k - 1), 0, 0)))
        override_material(a, mats[mt])
        override_material(b, mats[ml])
        override_material(c, mats[mc])

    # print plate (256 x 256 mm) with the three parts in print orientation
    ob_plate = prism("PLATE_Bed", rrect(128, 128, 8, 8), -1.5, 0.0, c_plate)
    set_material(ob_plate, make_material("SL_PEI", "1B1B1D", 0.6, 0.0, bed_texture=True))
    for name, ob, kind in exports:
        if name not in ("SL01_Tray", "SL01_Lid", "SL01_Carriage_Standard"):
            continue
        tx, ty = plate_xy[name]
        verts, _ = world_tris(ob, print_matrix(kind))
        zmin = min(v.z for v in verts)
        M = Matrix.Translation((tx - 128, ty - 128, -zmin)) @ print_matrix(kind)
        c = bpy.data.objects.new("PLATE_" + name, ob.data)
        c.matrix_world = M
        c_plate.objects.link(c)

    for c in (c_var, c_exp, c_cut, c_bot, c_col, c_plate):
        c.hide_render = True
        c.hide_viewport = True
    return dict(tray=tray, lid=lid, carriage=carriage, carriages=carriages, mats=mats,
                cut=[cut_c, cut_t], cut_x=xc, coll=dict(asm=c_asm, var=c_var, exp=c_exp, cut=c_cut,
                                                        bot=c_bot, col=c_col, plate=c_plate))


def setup_shots(scene, scn):
    add_area("Key", (-160, -220, 260), (0, 0, 5), 220, 6.0e5, (1.0, 0.97, 0.93))
    add_area("Fill", (260, -60, 120), (0, 0, 5), 260, 1.6e5, (0.92, 0.95, 1.0))
    add_area("Rim", (60, 260, 180), (0, 0, 5), 160, 3.2e5, (1.0, 1.0, 1.0))
    add_area("Top", (0, 0, 420), (0, 0, 0), 300, 2.0e5)
    cams = {}
    colls = scn["coll"]
    carriage = scn["carriage"]

    def cam(name, loc, tgt, lens=85, ortho=None):
        cams[name] = add_camera("CAM_" + name, loc, tgt, lens, ortho)

    cam("01_hero", (-112, -150, 104), (2, 0, 6), 92)
    cam("02_top", (0, 0, 400), (0, 0, 0), 85, ortho=92)
    cam("03_front", (0, -420, 92), (0, 0, 7), 150)
    cam("04_bottom", (0, 0, 400), (0, 0, 0), 85, ortho=92)
    cam("05_exploded", (-165, -200, 150), (0, 0, 27), 60)
    cam("06_cutaway", (-82, -112, 118), (-2, 0, 3), 78)
    cam("07_cutaway_top", (0, 0, 400), (0, 0, 0), 85, ortho=84)
    xt = scn["cut_x"] + P.TOOTH_X
    cam("08_detent_macro", (xt - 14, -D["YC"] - 26, 38), (xt + 1.0, -D["YC"] + 1.5, 5.5), 100)
    cam("09_colourways", (-150, -205, 165), (0, 2, 3), 72)
    cam("10_print_plate", (60, -150, 170), (0, -8, 2), 60)

    def show(colls_on, carriage_x=0.0):
        for c in colls.values():
            c.hide_render = True
        for c in colls_on:
            colls[c].hide_render = False
        carriage.location = (carriage_x, 0, 0)

    def shot(name, colls_on, cx=0.0):
        def f():
            show(colls_on, cx)
            scene.camera = cams[name]
        return f

    shots = [
        ("01_hero", shot("01_hero", ["asm"], -5.0)),
        ("02_top", shot("02_top", ["asm"], 10.0)),
        ("03_front", shot("03_front", ["asm"], 0.0)),
        ("04_bottom", shot("04_bottom", ["bot"])),
        ("05_exploded", shot("05_exploded", ["exp"])),
        ("06_cutaway", shot("06_cutaway", ["cut"])),
        ("07_cutaway_top", shot("07_cutaway_top", ["cut"])),
        ("08_detent_macro", shot("08_detent_macro", ["cut"])),
        ("09_colourways", shot("09_colourways", ["col"])),
        ("10_print_plate", shot("10_print_plate", ["plate"])),
    ]
    shots[0][1]()
    return shots


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if bpy.app.background or "--out" in argv:
        main(argv)
    else:
        main([])
