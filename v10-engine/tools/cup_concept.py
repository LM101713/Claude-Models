"""Cup-style production concept (Liam, 2026-10-07: "still doesn't look like a NASCAR engine, it's not
simplified, and it takes a while to make").

A fresh exterior on real small-block proportions at 1:2.42 instead of the V10-derived skin:
90 deg V8, 46 mm bore pitch, tall deck, narrow heads, long low valve covers, a single-plane intake
with runner bulges, a round air cleaner, a distributor at the back with plug wires, long 4-into-1
headers, a front drive with a cog belt (crank, dry-sump pump, water pump, alternator), a flywheel
and a shallow dry-sump pan. About 20 printed pieces; nothing inside moves except the crank shaft
that the motor turns (front pulleys and flywheel spin, LEDs pulse at the plug boots).

Frame: crank axis on X (front = +X), right bank (A) at +Y, Z up, crank centre at the origin.

    python tools/cup_concept.py --build --export          (bpyenv)
    python tools/cup_concept.py --preview                 (quick 16-sample check render)
    python tools/cup_concept.py --photo --views front_right,rear_left,above --samples 128

STLs go to cup/stl/, renders to renders/cup/.
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from skin import bpyutil as U  # noqa: E402
from skin import studio as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_STL = os.path.join(ROOT, "cup", "stl")
OUT_REN = os.path.join(ROOT, "renders", "cup")
S45 = math.sqrt(0.5)

# ---------------------------------------------------------------- dimensions (mm, model scale 1:2.42)
CUP = dict(
    pitch=46.0,             # bore spacing 4.4 in
    bank_off=4.75,          # bank A sits this far ahead, bank B this far behind
    deck=94.5,              # crank centre to deck, along the bore axis (9.0 in deck height)
    deck_half=29.0,         # half width of the block deck
    block_x=108.0,          # block front / rear faces at +-block_x
    rail_z=-31.0,           # pan rail
    side_y=57.0,            # vertical crankcase side
    valley_z=55.0,          # valley floor
    wall=2.6,               # block shell wall
    head_h=38.0, head_half=31.0, head_x=103.0, port_u=21.0,
    cover_h=30.0, cover_x=98.0,
    pan_z=-60.0,
    belt_x=(136.0, 142.0),  # belt plane
    plinth_z=(-98.0, -80.0),
)
C = CUP
HEAD_TOP = C["deck"] + C["head_h"]


def cyl_x(bank, i):
    """Bore centre x of cylinder i (0 = front) on bank 'A' or 'B'."""
    x = (1.5 - i) * C["pitch"]
    return x + (C["bank_off"] if bank == "A" else -C["bank_off"])


def bank_pt(s, x, v, u):
    """Bank-local (x, v outboard, u along the bore axis) -> engine point; s=+1 bank A, -1 bank B."""
    return Vector((x, s * S45 * (u + v), S45 * (u - v)))


def to_bank_A(obj):
    """Local (x, y=v, z=u) -> bank A engine frame."""
    return U.transform(obj, Matrix.Rotation(math.radians(-45.0), 4, 'X'))


def both_banks(obj, name, shift=True):
    """obj built in bank-local frame (cylinders at the unshifted x) -> (A, B) placed objects.
    Bank B is the mirror image, so a symmetric part is the same STL on both banks."""
    to_bank_A(obj)
    b = U.mirror_y(obj, name + "_B")
    obj.name = name + "_A"
    if shift:
        U.move(obj, dx=C["bank_off"])
        U.move(b, dx=-C["bank_off"])
    return obj, b


def cyl_dir(name, r, t0, t1, origin, direction, segs=64, r2=None):
    """Cylinder / cone from t0 to t1 along `direction` through `origin`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=t1 - t0)
    bmesh.ops.translate(bm, vec=(0, 0, (t0 + t1) / 2), verts=bm.verts)
    q = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized())
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(origin), verts=bm.verts)
    return U.from_bmesh(name, bm)


def offset_poly(pts, d):
    """Miter offset of a simple polygon (list of (y, z)); d > 0 moves the edges inward for a
    counter-clockwise polygon."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    lines = []
    for i in range(n):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % n])
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x)) * sgn          # inward normal
        lines.append((a + nrm * d, t))
    out = []
    for i in range(n):
        (p1, t1), (p2, t2) = lines[i - 1], lines[i]
        den = t1.x * t2.y - t1.y * t2.x
        if abs(den) < 1e-9:
            out.append(tuple(p2))
            continue
        s = ((p2.x - p1.x) * t2.y - (p2.y - p1.y) * t2.x) / den
        out.append(tuple(p1 + t1 * s))
    return out


def clip_halfplane(pts, a, b, c):
    """Keep the part of polygon pts (list of (y, z)) where a*y + b*z <= c (Sutherland-Hodgman)."""
    out = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def shell_cavity(name, pts, wall, x0, x1, open_below, roof_apex):
    """Cavity prism for a part printed on its open bottom: the outline offset inward by `wall`,
    run out below `open_below`, with a 45 deg peaked roof under `roof_apex` so it needs no support."""
    cav = offset_poly(pts, wall)
    cav = [(y, z if z > open_below + wall + 0.1 else open_below - 6.0) for y, z in cav]
    cav = clip_halfplane(cav, 1.0, 1.0, roof_apex)
    cav = clip_halfplane(cav, -1.0, 1.0, roof_apex)
    return U.prism(name, cav, x0 + wall, x1 - wall)


def hexagon(name, r, t0, t1, origin, direction):
    # starts 0.3 mm inside the face it sits on so the union fuses (touching faces leave a loose shell)
    return cyl_dir(name, r, t0 - 0.3, t1, origin, direction, segs=6)


# ---------------------------------------------------------------- block (1 piece, painted)
def block_outline():
    d, h = C["deck"], C["deck_half"]
    outer = bank_pt(1, 0, h, d)
    inner = bank_pt(1, 0, -h, d)
    sy, rz, vz = C["side_y"], C["rail_z"], C["valley_z"]
    # where the outer bank wall (v = +h) meets the vertical crankcase side
    knee_z = sy - S45 * 2 * h * S45 * 2 / 2  # placeholder, recomputed below
    # outer wall line: y - z = 2 * S45 * h  ->  at y = sy: z = sy - 2*S45*h
    knee_z = sy - 2 * S45 * h
    # inner wall line: z - y = 2 * S45 * h  ->  at z = vz: y = vz - 2*S45*h
    vy = vz - 2 * S45 * h
    right = [(sy, rz), (sy, knee_z), (outer.y, outer.z), (inner.y, inner.z), (vy, vz)]
    left = [(-y, z) for y, z in reversed(right)]
    return right + left


def build_block():
    pts = block_outline()
    bx = C["block_x"]
    blk = U.prism("block", pts, -bx, bx)
    # hollow shell, open at the bottom (pan side): motor and board live inside
    cav_pts = offset_poly(pts, C["wall"])
    cav_pts = [(y, z if z > C["rail_z"] + 1 else C["rail_z"] - 5) for y, z in cav_pts]
    cav = U.prism("block_cav", cav_pts, -bx + C["wall"], bx - C["wall"])
    U.boolean(blk, cav)
    # pan rail flange all round
    rail = U.rrect_prism("rail", 0, 0, 2 * bx + 4, 2 * C["side_y"] + 10, 6, C["rail_z"], C["rail_z"] + 5)
    rail_cut = U.rrect_prism("rail_cut", 0, 0, 2 * bx - 2 * C["wall"], 2 * C["side_y"] - 2 * C["wall"], 3,
                             C["rail_z"] - 1, C["rail_z"] + 6)
    U.boolean(rail, rail_cut)
    U.union([blk, rail])
    for s in (1, -1):
        # water-jacket face: three freeze plugs on the 45 deg outer wall
        mid = bank_pt(s, 0, C["deck_half"], 52.0)
        nrm = Vector((0, s * S45, -S45))
        for x in (-62.0, 0.0, 62.0):
            o = Vector((x, mid.y, mid.z))
            U.boolean(blk, cyl_dir("plug_rec", 6.6, -1.2, 1.0, o, nrm))
            U.union([blk, cyl_dir("plug_cup", 5.4, -1.2, -0.5, o, nrm)])
        # engine-mount pads on the crankcase side
        for x in (40.0, -40.0):
            pad = U.box("mount_pad", x - 11, x + 11, s * C["side_y"] - 1 if s > 0 else -C["side_y"] - 2.5,
                        C["side_y"] + 2.5 if s > 0 else -C["side_y"] + 1, -14, 6)
            U.union([blk, pad])
            for dz in (-7.0, 1.0):
                for dx in (-6.0, 6.0):
                    U.union([blk, hexagon("mount_bolt", 2.4, 0, 1.6, (x + dx, s * (C["side_y"] + 2.5), dz),
                                          (0, s, 0))])
        # oil-gallery rib along the knee
        knee_z = C["side_y"] - 2 * S45 * C["deck_half"]
        rib = cyl_dir("gallery", 3.2, -bx + 6, bx - 6, (0, s * (C["side_y"] - 0.8), knee_z - 1.0), (1, 0, 0))
        U.union([blk, rib])
    # rear: flywheel boss and crank seal housing; front: crank snout boss (shaft passes through)
    U.union([blk, U.cylinder("rear_boss", 22.0, -bx - 3, -bx + 1, 0, 0, axis="X")])
    U.boolean(blk, U.cylinder("shaft_clear", 4.4, -bx - 10, bx + 10, 0, 0, axis="X"))
    U.bevel(blk, 0.8, segments=2, angle_deg=40)
    return blk


# ---------------------------------------------------------------- heads (2 of one part)
def build_head():
    d, hh, h = C["deck"], C["head_half"], C["head_h"]
    top = d + h
    prof = [(-hh, d), (hh, d), (hh, top - 5), (hh - 5, top), (-hh + 5, top), (-hh, top - 5)]
    hx = C["head_x"]
    head = U.prism("head", prof, -hx, hx)
    U.boolean(head, shell_cavity("head_cav", prof, 2.6, -hx, hx, d, top - 2.6))
    U.bevel_edges(head, 6.0, 4, lambda c, t: abs(t.x) < 0.1 and abs(abs(c.x) - hx) < 0.01 and c.z > d + 1)
    # end faces: accessory bosses and a lifting-eye pad so the ends do not read as flat blocks
    for sx in (1, -1):
        for v, u, r in ((-15.0, d + 10.0, 4.6), (15.0, d + 10.0, 4.6), (0.0, d + 24.0, 5.4)):
            x0 = sx * hx
            U.union([head, U.cylinder("end_boss", r, min(x0 - sx, x0 + sx * 2.2), max(x0 - sx, x0 + sx * 2.2), v, u,
                                      axis="X", segs=48)])
            U.boolean(head, U.cylinder("end_tap", r * 0.42, x0 - 3, x0 + 3, v, u, axis="X", segs=32))
    # spark-plug bosses on the exhaust face, below and between the ports, angled down
    pdir = Vector((0, 0.94, -0.34))
    for i in range(4):
        x = (1.5 - i) * C["pitch"]
        o = Vector((x + 14.0, hh - 1.0, d + 11.0))
        U.union([head, cyl_dir("plug_boss", 5.2, 0, 4.2, o, pdir)])
        U.boolean(head, cyl_dir("plug_sock", 2.3, -1.0, 5.4, o + pdir * 4.2, -pdir))
    # lower head-bolt row on the exhaust face
    for x in (-92.0, -46.0, 0.0, 46.0, 92.0):
        U.union([head, U.cylinder("hb_boss", 4.6, hh - 1, hh + 1.2, x, d + 5.5, axis="Y")])
        U.union([head, hexagon("hb_bolt", 3.0, 0, 2.6, (x, hh + 1.2, d + 5.5), (0, 1, 0))])
    # exhaust ports (the header flanges land on these pads)
    for i in range(4):
        x = (1.5 - i) * C["pitch"] - 4.0
        pad = U.rrect_prism("port_pad", 0, 0, 22.0, 18.0, 4.0, -0.5, 1.2)
        U.transform(pad, Matrix.Translation((x, hh, d + C["port_u"])) @ Matrix.Rotation(math.radians(-90), 4, 'X'))
        U.union([head, pad])
    # intake-side bolt bosses (show between the runners)
    for x in (-69.0, -23.0, 23.0, 69.0):
        U.union([head, U.cylinder("ib_boss", 3.6, -hh - 1.4, -hh + 1, x, top - 9.0, axis="Y")])
    return head


# ---------------------------------------------------------------- valve covers (2 of one part)
def build_cover():
    z0 = HEAD_TOP
    hx = C["cover_x"]
    flange = U.rrect_prism("cover", 0, 0.0, 2 * hx, 60.0, 8.0, z0, z0 + 4.0)
    body = U.loft("cover_body", [U.rrect_ring(0, 0.0, 2 * hx - 6, 54.0, 9.0, z0 + 3.9),
                                 U.rrect_ring(0, 0.0, 2 * hx - 9, 51.0, 10.0, z0 + C["cover_h"] - 8),
                                 U.rrect_ring(0, 0.0, 2 * hx - 16, 44.0, 11.0, z0 + C["cover_h"])])
    U.union([flange, body])
    top = z0 + C["cover_h"]
    U.boolean(flange, U.rrect_prism("panel", 0, 0.0, 2 * hx - 60, 24.0, 6.0, top - 0.7, top + 1))
    # flange bolts, 7 per side
    for i in range(7):
        x = -hx + 14 + i * (2 * hx - 28) / 6
        for v in (-28.5, 28.5):
            U.union([flange, hexagon("cv_bolt", 2.6, z0 + 3.9, z0 + 6.2, (x, v, 0), (0, 0, 1))])
    # breathers with AN fittings, front and rear
    for x in (-hx + 34, hx - 34):
        U.union([flange, U.cylinder("br_base", 6.5, top - 1, top + 3.5, x, 0.0, segs=48)])
        U.union([flange, hexagon("br_hex", 6.8, top + 3.5, top + 6.5, (x, 0.0, 0), (0, 0, 1))])
        U.union([flange, U.cylinder("br_nip", 4.4, top + 6.5, top + 11.0, x, 0.0, segs=48)])
        U.union([flange, U.cylinder("br_lip", 5.0, top + 9.0, top + 10.0, x, 0.0, segs=48)])
    U.bevel(flange, 0.6, segments=2, angle_deg=40)
    w = 2.6
    cav = U.loft("cover_cav", [U.rrect_ring(0, 0.0, 2 * hx - 6 - 2 * w, 54.0 - 2 * w, 7.0, z0 - 1.0),
                               U.rrect_ring(0, 0.0, 2 * hx - 6 - 2 * w, 54.0 - 2 * w, 7.0, z0 + 2.0),
                               U.rrect_ring(0, 0.0, 2 * hx - 40, 6.0, 2.9, z0 + 2.0 + (54.0 - 2 * w - 6.0) / 2)])
    U.boolean(flange, cav)
    flange.name = "cover"
    return flange


# ---------------------------------------------------------------- intake + throttle body (1 piece)
INTAKE_X = (-90.0, 93.0)
PLENUM_Z = (136.0, 150.0)


def intake_outline():
    d = C["deck"]
    k = 2 * S45                           # z - y offsets of the bank lines
    gap = 0.4
    blk_line = k * C["deck_half"] + gap    # block inner wall: z = y + 41.0 (+gap)
    head_line = k * C["head_half"] + gap   # head intake face: z = y + 50.9 (+gap)
    deck_sum = 2 * S45 * d + gap          # deck plane: y + z = 133.6 (+gap)
    p0 = (C["valley_z"] - blk_line, C["valley_z"] + 0.3)
    p0 = (p0[0] + 0.3, p0[1])
    y1 = (deck_sum - blk_line) / 2
    p1 = (y1, y1 + blk_line)
    y2 = (deck_sum - head_line) / 2
    p2 = (y2, y2 + head_line)
    y3 = 64.0
    p3 = (y3, y3 + head_line)
    right = [p0, p1, p2, p3, (54.0, 126.0), (42.0, PLENUM_Z[0])]
    left = [(-y, z) for y, z in reversed(right)]
    return right + left


def build_intake():
    x0, x1 = INTAKE_X
    body = U.prism("intake", intake_outline(), x0, x1)
    U.boolean(body, shell_cavity("intake_cav", intake_outline(), 2.6, x0, x1, C["valley_z"] + 0.3, 128.0))
    U.bevel_edges(body, 3.0, 2, lambda c, t: abs(t.x) < 0.1 and (abs(c.x - x0) < 0.01 or abs(c.x - x1) < 0.01) and c.z > 100)
    # plenum
    pz0, pz1 = PLENUM_Z
    pl = U.loft("plenum", [U.rrect_ring(6, 0, 132, 86, 16, pz0 - 4), U.rrect_ring(6, 0, 128, 82, 15, pz1 - 4),
                          U.rrect_ring(6, 0, 118, 74, 13, pz1)])
    U.union([body, pl])
    # runner bulges from the plenum down to each port
    for bank, s in (("A", 1), ("B", -1)):
        for i in range(4):
            x = cyl_x(bank, i)
            xp = 6 + (x - 6) * 0.72
            pts = [(xp, s * 30.0, pz0 + 2), (xp + (x - xp) * 0.5, s * 42.0, pz0 - 3), (x, s * 52.0, 120.0),
                   (x, s * 54.0, 117.5)]
            U.union([body, U.tube_along("runner", pts, 7.2, segs=32)])
    # carb pad + square 4-barrel throttle body
    U.union([body, U.rrect_prism("pad", 6, 0, 66, 66, 6, pz1 - 1, pz1 + 4)])
    tb = U.rrect_prism("tb", 6, 0, 58, 54, 5, pz1 + 4, pz1 + 17)
    U.union([body, tb])
    # linkage boss and fuel log down each side
    U.union([body, U.cylinder("tb_shaft", 3.2, -32, 32, 6 + 31, pz1 + 10, axis="Y", segs=32)])
    for s in (1, -1):
        U.union([body, cyl_dir("fuel_log", 3.6, -64, 74, (0, s * 47.0, 132.5), (1, 0, 0), segs=32)])
        for x in (-64.0, 74.0):
            U.union([body, hexagon("fl_end", 4.6, 0, 3.0, (x, s * 47.0, 132.5), (1 if x > 0 else -1, 0, 0))])
    # water neck / thermostat housing at the front, pointing forward and up
    nx = x1 - 10.0
    U.union([body, U.rrect_prism("neck_pad", nx, 0, 22, 26, 4, 120.0, pz0 + 1)])
    ndir = Vector((0.75, 0, 0.66))
    U.union([body, cyl_dir("neck", 9.5, 0, 9.0, (nx, 0, pz0 - 2), ndir, segs=64)])
    U.union([body, cyl_dir("neck_out", 6.0, 8.0, 22.0, (nx, 0, pz0 - 2), ndir, segs=48)])
    U.union([body, cyl_dir("neck_bead", 7.0, 18.0, 19.5, (nx, 0, pz0 - 2), ndir, segs=48)])
    U.boolean(body, cyl_dir("neck_bore", 4.2, 14.0, 24.0, (nx, 0, pz0 - 2), ndir, segs=48))
    # distributor bore at the rear (the distributor drops into it)
    U.boolean(body, U.cylinder("dist_clear", 11.2, 40, 200, -101.0, 0, segs=64))
    U.bevel(body, 0.6, segments=2, angle_deg=40)
    return body


TB_TOP = PLENUM_Z[1] + 17


# ---------------------------------------------------------------- air cleaner (2 pieces)
def build_air_cleaner():
    z0 = TB_TOP
    base = U.cylinder("air_base", 66.0, z0, z0 + 2.5, 6, 0, segs=128)
    U.union([base, U.cylinder("air_lip", 64.0, z0 + 2.5, z0 + 6.0, 6, 0, segs=128)])
    el = U.cylinder("air_el", 59.0, z0 + 5.0, z0 + 27.0, 6, 0, segs=128)
    U.union([base, el])
    U.boolean(base, U.cylinder("air_cav", 55.6, z0 + 2.4, z0 + 28.0, 6, 0, segs=128))
    # pleats: shallow vertical grooves all round
    for k in range(72):
        a = 2 * math.pi * k / 72
        g = U.box("pleat", -0.7, 0.7, -1.6, 1.6, z0 + 7.0, z0 + 25.0)
        U.transform(g, Matrix.Translation((6 + 59.6 * math.cos(a), 59.6 * math.sin(a), 0)) @ Matrix.Rotation(a, 4, 'Z'))
        U.boolean(base, g)
    lid = U.cylinder("air_lid", 66.0, z0 + 27.0, z0 + 30.0, 6, 0, segs=128, r2=64.0)
    U.union([lid, U.cylinder("lid_dome", 52.0, z0 + 30.0, z0 + 31.6, 6, 0, segs=128, r2=46.0)])
    U.union([lid, U.cylinder("wing_hub", 6.0, z0 + 31.6, z0 + 37.0, 6, 0, segs=48)])
    wing = U.loft("wing", [U.rrect_ring(6, 0, 34, 4.0, 1.9, z0 + 31.6), U.rrect_ring(6, 0, 30, 3.2, 1.5, z0 + 39.0)])
    U.union([lid, wing])
    U.bevel(lid, 0.5, segments=2, angle_deg=40)
    return base, lid


# ---------------------------------------------------------------- distributor (1 piece)
DIST = Vector((-101.0, 0.0))
DIST_Z = (60.0, 150.0)
CAP_R = 20.0


def tower_pos(k):
    a = math.radians(22.5 + 45.0 * k)
    return Vector((DIST.x + 13.5 * math.cos(a), DIST.y + 13.5 * math.sin(a), DIST_Z[1] + 6.0)), a


def build_distributor():
    z0, z1 = DIST_Z
    d = U.cylinder("dist", 10.8, z0, z1 - 20, DIST.x, DIST.y, segs=64)
    U.union([d, U.cylinder("dist_clamp", 14.0, z1 - 30, z1 - 26, DIST.x, DIST.y, segs=64)])
    U.union([d, U.cylinder("dist_body", 15.0, z1 - 20, z1 - 12, DIST.x, DIST.y, segs=64)])
    U.union([d, U.cylinder("cap", CAP_R, z1 - 12, z1, DIST.x, DIST.y, segs=96, r2=CAP_R - 2.0)])
    U.union([d, U.cylinder("cap_dome", CAP_R - 2.0, z1, z1 + 3, DIST.x, DIST.y, segs=96, r2=CAP_R - 6.0)])
    for k in range(8):
        p, _ = tower_pos(k)
        U.union([d, U.cylinder("tower", 3.4, z1, p.z + 2.0, p.x, p.y, segs=32)])
    U.union([d, U.cylinder("tower_c", 3.6, z1 + 3, z1 + 10, DIST.x, DIST.y, segs=32)])
    U.bevel(d, 0.4, segments=2, angle_deg=40)
    return d


# ---------------------------------------------------------------- headers (2 mirrored pieces)
PRIM_R = 8.0
COLL_X = (-92.0, -150.0)


def header_paths():
    """Bank A primaries: port -> out -> drop to a lane -> run back to the merge."""
    d, hh = C["deck"], C["head_half"]
    mz, my = -7.0, 112.0       # merge centre
    lanes = {0: (my + 9.5, mz - 9.5), 1: (my - 9.5, mz - 9.5), 2: (my + 9.5, mz + 9.5), 3: (my - 9.5, mz + 9.5)}
    out = []
    for i in range(4):
        x = cyl_x("A", i) - 4.0
        port = bank_pt(1, x, hh + 1.2, d + C["port_u"])
        nrm = Vector((0, S45, -S45))
        p1 = port + nrm * 9.0
        ly, lz = lanes[i]
        p2 = Vector((x - 6.0, ly + 6.0, lz + 30.0))
        p3 = Vector((x - 22.0, ly, lz + 2.0))
        p4 = Vector((x - 40.0, ly, lz))
        pts = [port - nrm * 1.0, port + nrm * 3.0, p1, p2, p3, p4]
        # run rearward to the merge
        pts += [Vector((COLL_X[0] + 18.0, ly, lz)), Vector((COLL_X[0] + 2.0, ly, lz))]
        if p4.x < COLL_X[0] + 24.0:   # rearmost cylinder: no straight run
            pts = pts[:4] + [Vector((COLL_X[0] + 16.0, ly, lz)), Vector((COLL_X[0] + 2.0, ly, lz))]
        out.append(pts)
    return out, (my, mz)


def build_header():
    paths, (my, mz) = header_paths()
    hdr = None
    d, hh = C["deck"], C["head_half"]
    for i, pts in enumerate(paths):
        t = U.tube_along(f"prim{i}", [tuple(p) for p in pts], PRIM_R, segs=40)
        hdr = t if hdr is None else U.union([hdr, t])
        # port flange
        x = cyl_x("A", i) - 4.0
        fl = U.rrect_prism("flange", 0, 0, 24.0, 20.0, 4.0, 0, 3.0)
        U.transform(fl, Matrix.Translation(tuple(bank_pt(1, x, hh + 1.2, d + C["port_u"]))) @ Matrix.Rotation(math.radians(-45 - 90), 4, 'X'))
        U.union([hdr, fl])
    # merge collector: cone into the tail pipe, slip ring and outlet lip
    x0, x1 = COLL_X
    U.union([hdr, U.cylinder("merge", 21.0, x0 - 18, x0 + 2, my, mz, axis="X", segs=96, r2=21.0)])
    U.union([hdr, U.cylinder("cone", 13.0, x0 - 40, x0 - 18, my, mz, axis="X", segs=96, r2=21.0)])
    U.union([hdr, U.cylinder("tail", 13.0, x1, x0 - 40, my, mz, axis="X", segs=96)])
    U.union([hdr, U.cylinder("slip", 14.4, x0 - 46, x0 - 40, my, mz, axis="X", segs=96)])
    U.boolean(hdr, U.cylinder("tail_bore", 10.5, x1 - 1, x1 + 30, my, mz, axis="X", segs=96))
    U.union([hdr, U.cylinder("lip", 14.0, x1, x1 + 2.0, my, mz, axis="X", segs=96)])
    U.boolean(hdr, U.cylinder("lip_bore", 10.5, x1 - 1, x1 + 3, my, mz, axis="X", segs=96))
    return hdr


# ---------------------------------------------------------------- front drive
CRANK = (0.0, 0.0, 20.0)
WPUMP = (0.0, 52.0, 15.0)
DSUMP = (78.0, -42.0, 14.0)
ALT = (-64.0, 46.0, 8.0)


def build_front_cover():
    bx = C["block_x"]
    # timing cover round the crank, water-pump plate above it, joined by a neck: the painted block
    # face shows round it
    fc = U.rrect_prism("front_cover", 0, 0, 1, 1, 0.2, 0, 1)
    U.delete(fc)
    fc = U.loft("front_cover", [[(bx, y, z) for y, z, _ in U.rrect_ring(0, -2, 80, 58, 22, 0)],
                                [(bx + 6.0, y, z) for y, z, _ in U.rrect_ring(0, -2, 76, 54, 20, 0)]])
    wpl = U.cylinder("wp_plate", 25.0, bx, bx + 6.0, WPUMP[0], WPUMP[1], axis="X", segs=96, r2=23.0)
    U.union([fc, wpl, U.box("fc_neck", bx, bx + 5.0, -15.0, 15.0, 20.0, 34.0)])
    # water pump housing and snout
    wy, wz, _ = WPUMP
    U.union([fc, U.cylinder("wp_vol", 19.0, bx + 5, bx + 18, wy, wz, axis="X", segs=96, r2=16.0)])
    U.union([fc, U.cylinder("wp_snout", 8.0, bx + 18, C["belt_x"][0] - 0.5, wy, wz, axis="X", segs=48)])
    for s in (1, -1):   # outlets up to the heads
        U.union([fc, cyl_dir("wp_out", 5.5, 0, 26.0, (bx + 12, s * 10.0, wz + 8), (0, s * 0.8, 0.6), segs=40)])
        U.union([fc, cyl_dir("wp_out_lip", 6.6, 22.0, 24.0, (bx + 12, s * 10.0, wz + 8), (0, s * 0.8, 0.6), segs=40)])
    # crank snout boss
    U.union([fc, U.cylinder("seal", 13.0, bx + 5, bx + 10, 0, 0, axis="X", segs=96)])
    # dry-sump pump: three stages along X, low on the right, on a web from the cover
    py, pz, _ = DSUMP
    U.union([fc, U.box("ds_web", bx, bx + 6.0, 30.0, py, pz - 7.0, -26.0)])
    U.union([fc, U.cylinder("ds_body", 13.0, 46.0, bx + 16.0, py, pz, axis="X", segs=96)])
    for k, xb in enumerate((56.0, 74.0, 92.0)):
        U.union([fc, U.cylinder("ds_band", 14.4, xb, xb + 3.0, py, pz, axis="X", segs=96)])
        # AN fitting on top of each stage
        U.union([fc, hexagon("ds_an", 4.4, 13.0, 16.0, (xb + 8.0, py, pz), (0, 0.35, 1))])
        U.union([fc, cyl_dir("ds_nip", 2.9, 16.0, 20.0, (xb + 8.0, py, pz), (0, 0.35, 1), segs=32)])
    U.union([fc, U.cylinder("ds_nose", 7.0, bx + 16.0, C["belt_x"][0] - 0.5, py, pz, axis="X", segs=48)])
    # bolt ring
    ring = [(-34, -24), (34, -24), (36, 6), (-36, 6), (0, -27), (16, 67), (-16, 67), (19, 38), (-19, 38)]
    for y, z in ring:
        U.union([fc, hexagon("fc_bolt", 2.4, 0, 2.0, (bx + 6.0, y, z), (1, 0, 0))])
    U.boolean(fc, U.cylinder("shaft_clear", 4.4, bx - 1, bx + 30, 0, 0, axis="X"))
    U.bevel(fc, 0.5, segments=2, angle_deg=40)
    return fc


def build_alternator():
    bx = C["block_x"]
    ay, az, _ = ALT
    alt = U.cylinder("alternator", 17.0, bx + 6, C["belt_x"][0] - 6, ay, az, axis="X", segs=96)
    for k in range(18):   # cooling fins on the case
        a = 2 * math.pi * k / 18
        f = U.box("fin", bx + 8, C["belt_x"][0] - 8, -0.8, 0.8, 16.0, 18.4)
        U.transform(f, Matrix.Translation((0, ay, az)) @ Matrix.Rotation(a, 4, 'X'))
        U.union([alt, f])
    U.union([alt, U.cylinder("alt_nose", 6.0, C["belt_x"][0] - 6, C["belt_x"][0] - 0.5, ay, az, axis="X", segs=48)])
    # bracket arm back to the front cover
    U.union([alt, U.box("alt_arm", bx + 6.0, bx + 12, ay + 10, -34.0, az - 5, az + 5)])
    U.bevel(alt, 0.5, segments=2, angle_deg=40)
    return alt


def build_pulley(name, r, cogged=True):
    x0, x1 = C["belt_x"]
    p = U.cylinder(name, r + 1.4, x0, x0 + 0.9, 0, 0, axis="X", segs=96)
    U.union([p, U.cylinder(name + "_c", r, x0 + 0.9, x1 - 0.9, 0, 0, axis="X", segs=96)])
    U.union([p, U.cylinder(name + "_f", r + 1.4, x1 - 0.9, x1, 0, 0, axis="X", segs=96)])
    U.union([p, U.cylinder(name + "_hub", max(4.0, r * 0.45), x1, x1 + 2.5, 0, 0, axis="X", segs=48)])
    U.union([p, hexagon(name + "_nut", max(2.6, r * 0.24), 0, 1.6, (x1 + 2.5, 0, 0), (1, 0, 0))])
    if r > 12:
        for k in range(5):
            a = 2 * math.pi * k / 5
            U.boolean(p, U.cylinder("lh", r * 0.16, x1 - 3, x1 + 1, r * 0.62 * math.cos(a), r * 0.62 * math.sin(a), axis="X", segs=32))
    return p


def build_crank_pulley():
    bx = C["block_x"]
    p = build_pulley("crank_pulley", CRANK[2])
    U.union([p, U.cylinder("damper", 23.0, bx + 12, C["belt_x"][0] - 3, 0, 0, axis="X", segs=96)])
    U.union([p, U.cylinder("damper_hub", 9.0, bx + 10.5, C["belt_x"][0], 0, 0, axis="X", segs=64)])
    U.boolean(p, U.cylinder("dmp_groove", 24.0, bx + 18.0, bx + 19.2, 0, 0, axis="X", segs=96))
    U.union([p, U.cylinder("dmp_ring", 22.4, bx + 18.0, bx + 19.2, 0, 0, axis="X", segs=96)])
    return p


def build_belt():
    cs = [CRANK, WPUMP, DSUMP, ALT]

    def hull(extra):
        pts = []
        for y, z, r in cs:
            for k in range(96):
                a = 2 * math.pi * k / 96
                pts.append((y + (r + extra) * math.cos(a), z + (r + extra) * math.sin(a)))
        return U.convex_hull_2d(pts)
    x0, x1 = C["belt_x"]
    belt = U.prism("belt", hull(1.6), x0 + 1.0, x1 - 1.0)
    U.boolean(belt, U.prism("belt_in", hull(0.0), x0, x1))
    return belt


# ---------------------------------------------------------------- flywheel, pan, plinth
def build_flywheel():
    bx = C["block_x"]
    x0, x1 = -bx - 12.0, -bx - 4.0
    n, r0, r1 = 96, 53.0, 55.0
    pts = []
    for k in range(n):
        for j, f in enumerate((0.0, 0.2, 0.5, 0.7)):
            a = 2 * math.pi * (k + f) / n
            r = r1 if j in (1, 2) else r0
            pts.append((r * math.cos(a), r * math.sin(a)))
    fw = U.prism("flywheel", pts, x0, x0 + 4.0)
    U.union([fw, U.cylinder("fw_disc", 52.0, x0 + 3.9, x1, 0, 0, axis="X", segs=128)])
    U.boolean(fw, U.cylinder("fw_face", 40.0, x0 - 1, x0 + 1.2, 0, 0, axis="X", segs=128))
    U.union([fw, U.cylinder("fw_hub", 14.0, x0 - 2.0, x1, 0, 0, axis="X", segs=64)])
    for k in range(6):
        a = 2 * math.pi * k / 6
        U.union([fw, hexagon("fw_bolt", 2.6, 0, 1.6, (x0 - 2.0, 9.0 * math.cos(a), 9.0 * math.sin(a)), (-1, 0, 0))])
        b = math.pi / 6 + a
        U.boolean(fw, U.cylinder("fw_lh", 6.0, x0 - 1, x0 + 2.5, 30 * math.cos(b), 30 * math.sin(b), axis="X", segs=48))
    return fw


def build_pan():
    bx, rz, pz = C["block_x"], C["rail_z"], C["pan_z"]
    pan = U.rrect_prism("pan", 0, 0, 2 * bx + 4, 2 * C["side_y"] + 10, 6, rz - 4.0, rz)
    U.union([pan, U.loft("pan_body", [U.rrect_ring(0, 0, 2 * bx - 4, 2 * C["side_y"] - 6, 12, rz - 1.0),
                                      U.rrect_ring(0, 0, 2 * bx - 10, 2 * C["side_y"] - 12, 12, pz)])])
    for s in (1, -1):
        for z in (rz - 12.0, rz - 20.0):
            U.union([pan, U.box("pan_rib", -bx + 14, bx - 14, s * (C["side_y"] - 5) - 1.0, s * (C["side_y"] - 5) + 1.0, z - 0.8, z + 0.8)])
    # scavenge fittings, right side, one per pump stage
    for x in (-50.0, 0.0, 50.0):
        o = (x, C["side_y"] - 4.5, rz - 16.0)
        U.union([pan, hexagon("sc_hex", 4.4, 0, 3.0, o, (0, 1, 0))])
        U.union([pan, cyl_dir("sc_nip", 2.9, 3.0, 7.0, o, (0, 1, 0), segs=32)])
    # flange bolts
    for k in range(12):
        x = -bx + 8 + k * (2 * bx - 16) / 11
        for s in (1, -1):
            U.union([pan, hexagon("pan_bolt", 2.3, 0, 1.6, (x, s * (C["side_y"] + 2.0), rz - 4.0), (0, 0, -1))])
    U.bevel(pan, 0.5, segments=2, angle_deg=40)
    w = 2.4
    U.boolean(pan, U.loft("pan_cav", [U.rrect_ring(0, 0, 2 * bx - 4 - 2 * w, 2 * C["side_y"] - 6 - 2 * w, 10, rz + 1.0),
                                      U.rrect_ring(0, 0, 2 * bx - 4 - 2 * w, 2 * C["side_y"] - 6 - 2 * w, 10, rz - 4.1),
                                      U.rrect_ring(0, 0, 2 * bx - 10 - 2 * w, 2 * C["side_y"] - 12 - 2 * w, 10, pz + 3.0)]))
    return pan


def build_plinth():
    z0, z1 = C["plinth_z"]
    pl = U.rrect_prism("plinth", -4, 0, 316, 280, 14, z0, z1)
    U.bevel(pl, 3.0, segments=4, angle_deg=40)
    for x in (-70.0, 70.0):
        c = U.prism("cradle", [(-46, z1 - 0.5), (46, z1 - 0.5), (40, C["pan_z"]), (-40, C["pan_z"])], x - 9, x + 9)
        U.bevel(c, 1.5, segments=3, angle_deg=40)
        U.union([pl, c])
    return pl


# ---------------------------------------------------------------- non-printed: plug wires, boots, oil lines
def plug_point(bank, i):
    s = 1 if bank == "A" else -1
    d, hh = C["deck"], C["head_half"]
    x = (1.5 - i) * C["pitch"] + 14.0
    pdir = Vector((0, 0.94, -0.34))
    loc = Vector((x, hh - 1.0, d + 11.0)) + pdir * 4.2
    p = bank_pt(s, loc.x, loc.y, loc.z)
    p.x += C["bank_off"] if bank == "A" else -C["bank_off"]
    dv = bank_pt(s, 0, pdir.y, pdir.z) - bank_pt(s, 0, 0, 0)
    return p, dv.normalized()


def build_wires():
    """Eight plug wires (3 mm silicone lead, bought by the metre) and their printed boots."""
    objs = []
    order = {("A", 0): 0, ("A", 1): 1, ("A", 2): 2, ("A", 3): 3, ("B", 0): 7, ("B", 1): 6, ("B", 2): 5, ("B", 3): 4}
    for (bank, i), k in order.items():
        s = 1 if bank == "A" else -1
        tw, _ = tower_pos(k)
        plug, pdir = plug_point(bank, i)
        boot_end = plug + pdir * 10.0
        top = HEAD_TOP + C["cover_h"]
        lane = 3.4 * i
        # over the rear of the valve cover, then forward along the cover's outboard flank in a loom
        loom = bank_pt(s, 0, 33.0 + 0.0, HEAD_TOP + 9.0 - lane * 0.7)
        pts = [tw + Vector((0, 0, -1)), tw + Vector((0, 0, 10)), Vector((DIST.x + 4, s * 38.0, top - 4)),
               Vector((-96.0, loom.y - s * 6, loom.z + 14)),
               Vector((-80.0, loom.y, loom.z)),
               Vector((boot_end.x - 14.0, loom.y, loom.z)),
               Vector((boot_end.x - 2.0, (loom.y + boot_end.y) / 2, (loom.z + boot_end.z) / 2 + 4)),
               boot_end + pdir * 8.0, boot_end]
        w = U.tube_along(f"wire_{bank}{i}", [tuple(p) for p in pts], 1.5, segs=16)
        objs.append(w)
        boot = cyl_dir(f"boot_{bank}{i}", 3.3, 0.0, 12.0, plug, pdir, segs=32, r2=2.6)
        objs.append(boot)
        tb = U.cylinder(f"wire_tb{k}", 2.4, tw.z - 2, tw.z + 4, tw.x, tw.y, segs=24)
        objs.append(tb)
    return objs


def build_oil_lines():
    """Dry-sump scavenge lines from the pan fittings to the pump stages (4 mm black hose)."""
    py, pz, _ = DSUMP
    objs = []
    for k, (xb, xpan) in enumerate(zip((56.0, 74.0, 92.0), (-50.0, 0.0, 50.0))):
        a = Vector((xb + 8.0, py, pz)) + Vector((0, 0.35, 1)).normalized() * 19.0
        b = Vector((xpan, C["side_y"] - 4.5 + 6.5, C["rail_z"] - 16.0))
        pts = [a, a + Vector((0, 4, 6)), Vector(((a.x + b.x) / 2, py + 22, pz + 22 + 3 * k)), b + Vector((0, 10, 2)), b]
        objs.append(U.tube_along(f"oil_line{k}", [tuple(p) for p in pts], 2.2, segs=16))
        for p, dv in ((a, Vector((0, 0.35, 1))), (b, Vector((0, 1, 0)))):
            objs.append(cyl_dir(f"oil_fit{k}", 3.0, -1.0, 4.0, p, -dv if p is b else dv, segs=6))
    return objs


# ---------------------------------------------------------------- assembly
PRINTED = {}   # name -> (object, qty, stl name)


def place_pulley(p, y, z):
    U.move(p, dy=y, dz=z)
    return p


def build_all():
    U.reset_scene()
    t = time.time()
    placed = []

    def add(name, obj, stl=None, qty=1):
        obj.name = name
        placed.append((name, obj, stl, qty))
        print(f"  {name:22s} {time.time()-t:6.1f}s", flush=True)
        return obj

    add("block", build_block(), "c01_block")
    add("pan", build_pan(), "c02_pan")
    h = build_head()
    a, b = both_banks(h, "head")
    add("head_A", a, "c03_head", 2)
    add("head_B", b)
    cv = build_cover()
    a, b = both_banks(cv, "valve_cover")
    add("valve_cover_A", a, "c04_valve_cover", 2)
    add("valve_cover_B", b)
    add("intake", build_intake(), "c05_intake")
    base, lid = build_air_cleaner()
    add("air_base", base, "c06_air_cleaner_base")
    add("air_lid", lid, "c07_air_cleaner_lid")
    add("distributor", build_distributor(), "c08_distributor")
    hA = build_header()
    hB = U.mirror_y(hA, "header_B")
    add("header_A", hA, "c09_header_right")
    add("header_B", hB, "c10_header_left")   # exported as the exact mirror of the right-hand STL
    add("front_cover", build_front_cover(), "c11_front_cover")
    add("alternator", build_alternator(), "c12_alternator")
    add("crank_pulley", place_pulley(build_crank_pulley(), CRANK[0], CRANK[1]), "c13_crank_pulley")
    add("pulley_wp", place_pulley(build_pulley("pulley_wp", WPUMP[2]), WPUMP[0], WPUMP[1]), "c14_pulley_water")
    add("pulley_ds", place_pulley(build_pulley("pulley_ds", DSUMP[2]), DSUMP[0], DSUMP[1]), "c15_pulley_pump")
    add("pulley_alt", place_pulley(build_pulley("pulley_alt", ALT[2]), ALT[0], ALT[1]), "c16_pulley_alt")
    add("flywheel", build_flywheel(), "c17_flywheel")
    add("plinth", build_plinth(), "c18_plinth")
    add("belt", build_belt())
    for o in build_wires():
        add(o.name, o, "c19_plug_boot" if o.name == "boot_A0" else None, 8 if o.name == "boot_A0" else 1)
    for o in build_oil_lines():
        add(o.name, o)
    return placed


def export(placed):
    os.makedirs(OUT_STL, exist_ok=True)
    rows = []
    for name, obj, stl, qty in placed:
        if not stl:
            continue
        if stl == "c10_header_left":
            import trimesh
            m = trimesh.load(os.path.join(OUT_STL, "c09_header_right.stl"))
            m.apply_transform(trimesh.transformations.reflection_matrix((0, 0, 0), (0, 1, 0)))  # trimesh re-winds
            path = os.path.join(OUT_STL, stl + ".stl")
            m.export(path)
            rows.append(dict(file=stl, qty=qty, path=path, ok=bool(m.is_watertight), msg="mirror of c09_header_right",
                             size=[round(float(v), 1) for v in m.extents]))
            print("OK  " if m.is_watertight else "BAD ", rows[-1]["msg"], flush=True)
            continue
        for tol in (1e-4, 1e-3, 3e-3):
            o = U.copy(obj, name + "_exp")
            ok, msg = U.finalize(o, tol=tol)
            if ok or tol == 3e-3:
                break
            U.delete(o)
        path = os.path.join(OUT_STL, stl + ".stl")
        U.export_stl(o, path, do_finalize=False)
        bb = U.bbox(o)
        rows.append(dict(file=stl, qty=qty, path=path, ok=ok, msg=msg,
                         size=[round(bb[1] - bb[0], 1), round(bb[3] - bb[2], 1), round(bb[5] - bb[4], 1)]))
        print(("OK  " if ok else "BAD ") + msg, rows[-1]["size"], flush=True)
        U.delete(o)
    json.dump(dict(parts=rows), open(os.path.join(ROOT, "cup", "parts.json"), "w"), indent=1)
    return rows


# ---------------------------------------------------------------- look
def materials(palette):
    import skin_photo as P
    block_col = {"orange": (0.62, 0.13, 0.015), "black": (0.06, 0.065, 0.07), "blue": (0.02, 0.08, 0.30)}[palette]
    paint = P._mat("block_paint_" + palette, block_col, 0.0, 0.32, grain=(1.4, 0.18, 0.25), coat=0.6)
    rubber = P._mat("rubber", (0.015, 0.015, 0.016), 0.0, 0.7, bevel=0.0)
    wire = P._mat("wire", (0.02, 0.02, 0.022), 0.0, 0.45, bevel=0.0, coat=0.3)
    hose = P._mat("hose", (0.03, 0.03, 0.035), 0.4, 0.5, grain=(6.0, 0.6, 0.15), bevel=0.0)
    table = [
        ("block", lambda: paint), ("pan", P.machined_alu), ("head", P.cast_alu), ("valve_cover", P.wrinkle_black),
        ("intake", P.cast_alu), ("air_base", P.wrinkle_black), ("air_lid", P.machined_alu),
        ("distributor", P.wrinkle_black), ("header", P.stainless_heat), ("front_cover", P.cast_alu),
        ("alternator", P.brushed), ("crank_pulley", P.anodised_black), ("pulley", P.anodised_black),
        ("flywheel", P.dark_steel), ("plinth", P.powder_black), ("belt", lambda: rubber), ("wire_tb", lambda: rubber),
        ("wire", lambda: wire), ("boot", P.boot_glow), ("oil_line", lambda: hose), ("oil_fit", P.anodised_black),
    ]

    def pick(name):
        for pre, fn in table:
            if name.startswith(pre):
                return fn()
        return P.cast_alu()
    return pick


VIEWS = {
    "front_right": ((1.0, 0.85, 0.48), 1.0, None),
    "rear_left": ((-1.0, -0.85, 0.45), 1.0, None),
    "above": ((0.55, -0.75, 1.0), 1.15, None),
    "side": ((0.0, -1.0, 0.10), 1.0, None),
    "front": ((1.0, 0.0, 0.12), 1.0, None),
    "closeup": ((0.7, 0.55, 0.62), 1.9, (20.0, 40.0, 140.0)),
}


def render(placed, views, samples, size, palette, tag, preview=False):
    import skin_photo as P
    pick = materials(palette)
    for name, obj, _, _ in placed:
        U.set_material(obj, pick(name))
        U.shade(obj)
        for f in obj.data.polygons:     # flat caps: no smooth-shading pinch on fan-triangulated discs
            if abs(f.normal.z) > 0.999 or abs(f.normal.x) > 0.999:
                f.use_smooth = False
    bbs = [U.bbox(o) for n, o, _, _ in placed if n != "plinth"]
    bb = (min(b[0] for b in bbs), max(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs),
          min(b[4] for b in bbs), max(b[5] for b in bbs))
    floor_z = C["plinth_z"][0]
    P.studio(bb, floor_z)
    w, h = size
    os.makedirs(OUT_REN, exist_ok=True)
    out = []
    for v in views:
        direction, zoom, tgt = VIEWS[v]
        cam = S.camera(direction, bb, zoom * 1.08, lens=70.0, target=tgt)
        if not preview:
            cam.data.dof.use_dof = True
            tp = Vector(tgt or ((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
            cam.data.dof.focus_distance = (cam.location - tp).length
            cam.data.dof.aperture_fstop = 5.6 if zoom < 1.3 else 4.0
        path = os.path.join(OUT_REN, f"{v}{tag}.png")
        t0 = time.time()
        S.render(path, size=(w, h), samples=samples)
        print(f"  rendered {v} ({time.time()-t0:.0f}s)", flush=True)
        out.append(path)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--photo", action="store_true")
    ap.add_argument("--views", default="front_right")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--size", default="1600x1200")
    ap.add_argument("--palette", default="orange")
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    placed = build_all()
    if a.export:
        export(placed)
    if a.preview:
        render(placed, a.views.split(","), 16, (900, 675), a.palette, a.tag + "_preview", preview=True)
    if a.photo:
        w, h = (int(v) for v in a.size.lower().split("x"))
        render(placed, a.views.split(","), a.samples, (w, h), a.palette, a.tag)


if __name__ == "__main__":
    main(sys.argv[1:])
