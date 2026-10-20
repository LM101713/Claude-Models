#!/usr/bin/env python3
"""
Cutaway Turbofan: a 3D-printable display model that shows how a jet engine works.

A high-bypass turbofan at roughly 1:10 scale (140 mm fan, 25 cm long) with a quarter of
every static casing cut away. The rotor is whole: turn the spinner and the fan, six
compressor stages and four turbine stages all turn together on one shaft, inside the
nacelle, the compressor case, the combustor and the turbine case. A stand carries the
engine and spells out the four strokes: SUCK - SQUEEZE - BANG - BLOW.

    python cutaway_turbofan.py --out models          # build, check, export everything

Everything is generated here from the numbers in section 1. Every part prints with no
supports (all blade and vane angles stay within 45 deg of the print axis) and the script
checks that, plus every running clearance of the assembled engine, before exporting.

Frames used below
  axial frame     z = distance behind the nacelle lip (the engine axis), flow goes +z.
                  The cut-away quadrant is x < 0, y < 0.
  assembly frame  x along the engine (front at x = 0), z up, base top at z = 0, viewer at -y.
                  The cut-away quadrant is the upper, viewer-facing quarter.
  print frame     each part as it sits on the bed (z up from the bed).
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from manifold3d import CrossSection, FillRule, JoinType, Manifold, Mesh, OpType

TAU = 2.0 * math.pi

# =============================================================================
# 1. DIMENSIONS (mm). Change a number here and rebuild; never edit an STL.
# =============================================================================

H_AXIS = 96.0            # engine axis height above the base top

# shaft: one printed hex shaft carries the whole rotor
SHAFT_AF = 8.0           # across flats
SHAFT_Z = (33.0, 224.0)  # front end bottoms out in the fan's blind bore
BORE_AF = 8.4            # sliding hex bore in the rotor discs (0.2 mm a side)
RIB_H = 0.35             # crush ribs in the fan and stage-1 bores (press fit)
BEARING_D = 10.0         # round plain bearings in the two static hubs (hex corners 9.24)

# running clearances
TIP_GAP = 1.0            # compressor / turbine blade tips to their casing
FAN_TIP_R = 69.5         # fan tip radius (fan case 71.2, gap 1.7)
THRUST = 0.3             # rotor-to-static thrust faces (the designed rubbing faces)

# joints between the static modules: a 45 deg V tongue in a V groove, glued
TONGUE_H, GROOVE_H = 1.2, 1.4
DOWEL_D = 1.95           # holes for 1.75 mm filament dowels (tail cone)

# cut-away quadrant (axial frame x<0, y<0) keeps static material inside this radius
KEEP_R = {"frame": 15.2, "rear_frame": 18.0}

SEG = 128                # circular segments for casings

# --- nacelle (fan cowl) -----------------------------------------------------------
NAC_Z1 = 118.0           # nacelle trailing edge; the lip is at z = 0


def nac_inner(z):
    if z <= 14.0:
        return 71.2 + 2.8 * ((14.0 - z) / 14.0) ** 2
    if z <= 52.0:
        return 71.2
    t = (z - 52.0) / (NAC_Z1 - 52.0)
    return 71.2 - 5.2 * (3 * t * t - 2 * t ** 3)


def nac_outer(z):
    if z <= 40.0:
        return 75.0 + 5.0 * math.sqrt(max(0.0, 1.0 - ((40.0 - z) / 40.0) ** 2))
    return 80.0 - 12.0 * ((z - 40.0) / (NAC_Z1 - 40.0)) ** 1.5


# --- core flow path ---------------------------------------------------------------
COWL_R = 38.0            # core cowl (inner wall of the bypass duct)


def cowl(z):
    if z <= 180.0:
        return COWL_R
    if z <= 200.0:
        return COWL_R - 2.2 * ((z - 180.0) / 20.0) ** 2
    return 35.8 - 5.6 * (z - 200.0) / 22.0


def comp_case(z):
    """Compressor casing inner radius: the core converges as the air is squeezed."""
    return 33.6 + (25.4 - 33.6) * min(1.0, max(0.0, (z - 72.0) / 54.3))


def turb_case(z):
    """Turbine casing inner radius: it opens up as the hot gas expands."""
    return 24.9 + (31.4 - 24.9) * min(1.0, max(0.0, (z - 160.0) / 38.0))


def nozzle_inner(z):
    return 31.4 - 2.7 * (z - 198.0) / 24.0


# rotor stack (axial positions). The fan and stage 1 are pressed on the shaft and
# clamp the front bearing hub between them; stages 2..T4 slide on the hex and float
# between stage 1 and the rear bearing hub.
FAN = dict(z0=30.0, z1=48.0, hub_r=22.0, blades=18, spinner_tip=6.0)
COMP = [  # (hub radius, blade count) for stages 1..6, pitch 9 mm, blades on the rear 6 mm
    (16.0, 20), (16.8, 22), (17.5, 24), (18.1, 26), (18.6, 28), (19.0, 30)]
COMP_Z0, COMP_PITCH = 72.3, 9.0
TURB = [  # (z0, z1, hub radius, blade count); stage 1 has a long drive tube through the combustor
    (161.0, 170.0, 16.0, 24), (170.0, 179.0, 16.6, 26), (179.0, 188.0, 17.2, 28),
    (188.0, 197.7, 17.8, 30)]
T1_TUBE_R = 6.5

FRAME_Z = (48.3, 72.0)    # front frame (bearing hub nose to the rear face)
M3_Z = (72.0, 130.0)      # compressor case
M4_Z = (130.0, 160.0)     # combustor
M5_Z = (160.0, 198.0)     # turbine case
M6_Z = (198.0, 222.0)     # rear frame and core nozzle
TAIL_Z = (222.0, 252.0)   # tail cone

# =============================================================================
# 2. GEOMETRY HELPERS
# =============================================================================


def polygon_area(p):
    p = np.asarray(p, float)
    return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])


def lathe(profile, segs=SEG):
    """Revolve a closed (r, z) profile around the z axis."""
    p = np.asarray(profile, float)
    if polygon_area(p) < 0:
        p = p[::-1]
    return CrossSection([p]).revolve(segs)


def curve(f, z0, z1, n=40):
    return [(f(z), z) for z in np.linspace(z0, z1, n)]


def cyl(r, z0, z1, segs=SEG):
    return Manifold.cylinder(z1 - z0, r, r, segs).translate((0, 0, z0))


def hexagon(af, n_ribs=0, rib_h=0.0):
    """Hex with flats facing +-x (corners on +-y). Optional crush ribs on each flat."""
    R = af / math.sqrt(3.0)
    hexp = [(R * math.cos(math.radians(30 + 60 * k)), R * math.sin(math.radians(30 + 60 * k)))
            for k in range(6)]
    cs = CrossSection([np.array(hexp)])
    if n_ribs:
        ribs = []
        for k in range(6):
            a = math.radians(60 * k)
            c, s = math.cos(a), math.sin(a)
            d = af / 2.0
            tri = [(d + 0.05, -0.55), (d + 0.05, 0.55), (d - rib_h, 0.0)]
            ribs.append(CrossSection([np.array([(x * c - y * s, x * s + y * c) for x, y in tri])]))
        cs = cs - CrossSection.batch_boolean(ribs, OpType.Add)
    return cs


def hex_bore(af, z0, z1, ribs=False):
    cs = hexagon(af, 6 if ribs else 0, RIB_H)
    m = cs.extrude(z1 - z0).translate((0, 0, z0))
    return m


def radial_teardrop(d, r0, r1, z, theta_deg):
    """Horizontal (in print) hole along the radius at axial position z, with a 45 deg
    pointed roof towards -z (which is up when the part prints rear-down)."""
    r = d / 2.0
    pts = [(r * math.cos(a), r * math.sin(a)) for a in np.linspace(math.radians(135), math.radians(405), 28)]
    pts.append((0.0, r * math.sqrt(2.0)))
    cs = CrossSection([np.array(pts)])          # point towards +v
    m = cs.extrude(r1 - r0).translate((0, 0, r0))
    # extrusion axis -> +x (radial), v -> -z (forward)
    m = m.rotate((0, 90, 0))                   # z->x, x->-z
    m = m.rotate((90, 0, 0))                   # y->z ... v now along +z
    m = m.mirror((0, 0, 1))                    # v along -z
    return m.translate((0, 0, z)).rotate((0, 0, theta_deg))


def union(parts):
    parts = [p for p in parts if p is not None and not p.is_empty()]
    return Manifold.batch_boolean(parts, OpType.Add) if len(parts) > 1 else parts[0]


def quadrant_cut(m, keep_r=0.0):
    cut = Manifold.cube((400.0, 400.0, 800.0)).translate((-400.0, -400.0, -300.0))
    if keep_r > 0:
        cut = cut - cyl(keep_r, -310.0, 510.0, 96)
    return m - cut


def in_cut(theta_deg):
    t = theta_deg % 360.0
    return 180.0 - 1e-6 < t < 270.0 + 1e-6


def grid_solid(P):
    """Closed solid from a structured (ni, nj, 2, 3) grid of points (a deformed box)."""
    ni, nj = P.shape[0], P.shape[1]
    idx, verts, tris = {}, [], []

    def v(i, j, k):
        key = (i, j, k)
        if key not in idx:
            idx[key] = len(verts)
            verts.append(P[i, j, k])
        return idx[key]

    def quad(a, b, c, d):
        tris.append((a, b, c))
        tris.append((a, c, d))

    for i in range(ni - 1):
        for j in range(nj - 1):
            quad(v(i, j, 0), v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0))
            quad(v(i, j, 1), v(i + 1, j, 1), v(i + 1, j + 1, 1), v(i, j + 1, 1))
    for j in range(nj - 1):
        quad(v(0, j, 0), v(0, j, 1), v(0, j + 1, 1), v(0, j + 1, 0))
        quad(v(ni - 1, j, 0), v(ni - 1, j + 1, 0), v(ni - 1, j + 1, 1), v(ni - 1, j, 1))
    for i in range(ni - 1):
        quad(v(i, 0, 0), v(i + 1, 0, 0), v(i + 1, 0, 1), v(i, 0, 1))
        quad(v(i, nj - 1, 0), v(i, nj - 1, 1), v(i + 1, nj - 1, 1), v(i + 1, nj - 1, 0))
    V = np.array(verts, dtype=np.float32)
    T = np.array(tris, dtype=np.uint32)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:
        T = T[:, ::-1].copy()
    m = Manifold(Mesh(vert_properties=V, tri_verts=T))
    assert m.status().name == "NoError", m.status()
    return m


def blade(theta0, z_le, z_te, r_root, r_tip, beta_root, beta_tip, t_root, t_tip,
          ni=7, nj=7):
    """A twisted, cambered blade or vane with flat ends at z_le and z_te.

    r_root(z), r_tip(z): radius of the root and tip lines.  beta_*: (leading, trailing)
    camber-line angle from the axis in degrees, positive = theta grows going rearward.
    Thickness is offset tangentially, so both ends stay exactly at z_le / z_te (the end on
    the bed prints flat).  |beta| <= 45 keeps every blade surface printable."""
    zs = np.linspace(z_le, z_te, nj)
    P = np.zeros((ni, nj, 2, 3))
    for i, s in enumerate(np.linspace(0.0, 1.0, ni)):
        b_le = beta_root[0] + s * (beta_tip[0] - beta_root[0])
        b_te = beta_root[1] + s * (beta_tip[1] - beta_root[1])
        t = t_root + s * (t_tip - t_root)
        r = np.array([r_root(z) + s * (r_tip(z) - r_root(z)) for z in zs])
        # integrate d(theta)/dz = tan(beta)/r along the chord on a fine grid
        zf = np.linspace(z_le, z_te, 200)
        uf = (zf - z_le) / (z_te - z_le)
        bf = np.radians(b_le + uf * (b_te - b_le))
        rf = np.interp(zf, zs, r)
        dth = np.tan(bf) / rf
        th = np.concatenate([[0.0], np.cumsum(0.5 * (dth[1:] + dth[:-1]) * np.diff(zf))])
        th -= np.interp(0.5 * (z_le + z_te), zf, th)       # stack on mid-chord
        for j, z in enumerate(zs):
            u = (z - z_le) / (z_te - z_le)
            beta = math.radians(b_le + u * (b_te - b_le))
            thick = max(1.2, t * (0.62 + 0.38 * math.sin(math.pi * u)))
            half = 0.5 * thick / math.cos(beta)
            a = math.radians(theta0) + np.interp(z, zf, th)
            c, sn = math.cos(a), math.sin(a)
            base = np.array([r[j] * c, r[j] * sn, z])
            et = np.array([-sn, c, 0.0])
            P[i, j, 0] = base - half * et
            P[i, j, 1] = base + half * et
    return grid_solid(P)


def blade_row(n, theta_offset, skip_cut=False, **kw):
    out = []
    for k in range(n):
        th = theta_offset + 360.0 * k / n
        if skip_cut and in_cut(th):
            continue
        out.append(blade(th, **kw))
    return out


def v_ring(r_c, z_face, h, direction):
    """45 deg V ring (tongue or groove) on a face at z_face, pointing in +-z."""
    return lathe([(r_c - h, z_face), (r_c + h, z_face), (r_c, z_face + direction * h)])


def const(v):
    return lambda z: v


# =============================================================================
# 3. PARTS (built in the axial frame)
# =============================================================================


class Part:
    def __init__(self, key, name, solid, kind, orient, color, qty=1, bodies=None,
                 rotor=False, note=""):
        self.key, self.name, self.solid, self.kind = key, name, solid, kind
        self.orient = orient          # "rear-down" | "front-down" | "lying" | "flat"
        self.color, self.qty, self.rotor, self.note = color, qty, rotor, note
        self.bodies = bodies or [(name, solid, color)]   # colour bodies for the 3MF


def build_fan():
    f = FAN
    t = np.linspace(0.0, 1.0, 40)
    spinner = [(f["hub_r"] * (1.0 - tt ** 1.8), f["z0"] - tt * (f["z0"] - f["spinner_tip"]))
               for tt in t]
    prof = [(0.0, f["z1"]), (f["hub_r"] - 0.6, f["z1"]), (f["hub_r"], f["z1"] - 0.6)]
    prof += spinner                                     # from the hub rim to the tip
    prof += [(0.0, f["spinner_tip"])]
    hub = lathe(prof, 160)
    blades = blade_row(f["blades"], 0.0, z_le=31.0, z_te=f["z1"],
                       r_root=const(f["hub_r"] - 0.6), r_tip=const(FAN_TIP_R),
                       beta_root=(-30.0, -5.0), beta_tip=(-45.0, -35.0),
                       t_root=2.4, t_tip=1.6, ni=9, nj=8)
    fan = union([hub] + blades) - hex_bore(BORE_AF, SHAFT_Z[0] - 0.2, f["z1"] + 1, ribs=True)
    return Part("R1", "Fan and spinner", fan, "rotor", "rear-down", "#6b7480", rotor=True,
                note="press fit on the shaft (crush ribs); the shaft bottoms out in it")


def build_comp_stage(k):
    r_h, n = COMP[k]
    z0 = COMP_Z0 + COMP_PITCH * k
    z1 = z0 + COMP_PITCH
    prof = [(0.0, z0), (r_h - 0.4, z0), (r_h, z0 + 0.4), (r_h, z1 - 0.4), (r_h - 0.4, z1), (0.0, z1)]
    if k == 0:   # clear the front frame's vane roots: chamfered nose
        prof = [(0.0, z0), (14.6, z0), (r_h, z0 + 1.4), (r_h, z1 - 0.4), (r_h - 0.4, z1), (0.0, z1)]
    hub = lathe(prof, 96)
    blades = blade_row(n, 360.0 / n * 0.5 * (k % 2), z_le=z0 + 3.0, z_te=z1,
                       r_root=const(r_h - 0.6), r_tip=lambda z: comp_case(z) - TIP_GAP,
                       beta_root=(-35.0, -15.0), beta_tip=(-45.0, -30.0),
                       t_root=1.6, t_tip=1.3)
    m = union([hub] + blades) - hex_bore(BORE_AF, z0 - 1, z1 + 1, ribs=(k == 0))
    shade = ["#9cc3ec", "#86b2e3", "#6f9fd8", "#5a8bcb", "#4877bb", "#3a64a8"][k]
    return Part(f"C{k + 1}", f"Compressor stage {k + 1}", m, "rotor", "rear-down", shade,
                rotor=True, note="press fit (crush ribs)" if k == 0 else "slides on the hex")


def build_turb_stage(k):
    z0, z1, r_h, n = TURB[k]
    if k == 0:
        zt = COMP_Z0 + COMP_PITCH * len(COMP)        # drive tube starts at stage 6's rear face
        prof = [(0.0, zt), (T1_TUBE_R, zt), (T1_TUBE_R, z0), (r_h - 1.0, z0), (r_h, z0 + 1.0),
                (r_h, z1 - 0.4), (r_h - 0.4, z1), (0.0, z1)]
        zb = zt
    else:
        prof = [(0.0, z0), (r_h - 0.4, z0), (r_h, z0 + 0.4), (r_h, z1 - 0.4), (r_h - 0.4, z1), (0.0, z1)]
        zb = z0
    hub = lathe(prof, 96)
    blades = blade_row(n, 360.0 / n * 0.5 * (k % 2), z_le=z1 - 6.0, z_te=z1,
                       r_root=const(r_h - 0.6), r_tip=lambda z: turb_case(z) - TIP_GAP,
                       beta_root=(30.0, -45.0), beta_tip=(20.0, -45.0),
                       t_root=2.0, t_tip=1.5)
    m = union([hub] + blades) - hex_bore(BORE_AF, zb - 1, z1 + 1)
    shade = ["#f0743a", "#d95a26", "#b8441b", "#923315"][k]
    name = f"Turbine stage {k + 1}" + (" (with drive tube)" if k == 0 else "")
    return Part(f"T{k + 1}", name, m, "rotor", "rear-down", shade, rotor=True,
                note="slides on the hex")


def build_shaft():
    z0, z1 = SHAFT_Z
    m = hexagon(SHAFT_AF).extrude(z1 - z0).translate((0, 0, z0))
    r0, r1 = SHAFT_AF / 2 - 0.4, SHAFT_AF / math.sqrt(3) + 0.1   # 45 deg end chamfers
    env = lathe([(0.0, z0), (r0, z0), (r1, z0 + r1 - r0), (r1, z1 - r1 + r0), (r0, z1), (0.0, z1)], 48)
    return Part("R0", "Shaft (hex 8 mm)", m ^ env, "rotor", "lying", "#e3c25a", rotor=True,
                note="prints lying on a flat")


def build_nacelle():
    z0, z1 = 0.0, NAC_Z1
    outer = curve(nac_outer, z0, z1, 60)
    inner = curve(nac_inner, z1, z0, 60)
    shell = lathe(outer + inner, 192)
    sleeve = lathe([(COWL_R + 0.3, z1), (41.0, z1), (41.0, 103.5), (39.3, 101.8),
                    (COWL_R + 0.3, 101.8)], SEG)
    ogv = blade_row(12, 15.0, skip_cut=True, z_le=102.0, z_te=z1,
                    r_root=const(40.4), r_tip=lambda z: nac_inner(z) + 0.6,
                    beta_root=(30.0, 0.0), beta_tip=(30.0, 0.0), t_root=2.2, t_tip=2.2, nj=6)
    m = quadrant_cut(union([shell, sleeve] + ogv))
    return Part("S1", "Nacelle with bypass vanes", m, "static", "rear-down", "#e9ecef",
                note="slides on from the rear and sits on the compressor case (glue)")


def build_front_frame():
    za, zb = FRAME_Z
    hub = lathe([(0.0, za), (12.5, za), (15.0, za + 2.5), (15.0, zb), (0.0, zb)], 96)
    splitter = lathe([(33.6, zb), (COWL_R, zb), (COWL_R, 63.0), (34.6, 55.0), (33.6, 56.0)], SEG)
    igv = blade_row(16, 11.25, skip_cut=True, z_le=60.0, z_te=zb,
                    r_root=const(14.6), r_tip=const(34.1),
                    beta_root=(0.0, 0.0), beta_tip=(0.0, 0.0), t_root=1.6, t_tip=1.6, nj=4)
    m = union([hub, splitter] + igv)
    m = m - v_ring(35.8, zb, GROOVE_H, -1) - cyl(BEARING_D / 2, za - 1, zb + 1, 64)
    m = quadrant_cut(m, KEEP_R["frame"])
    return Part("S2", "Front frame (splitter, inlet vanes, front bearing)", m, "static",
                "rear-down", "#cfd4da")


def build_comp_case():
    z0, z1 = M3_Z
    prof = [(COWL_R, z1), (COWL_R, z0)] + curve(comp_case, z0, z1, 30)
    m = lathe(prof, SEG) + v_ring(35.8, z0, TONGUE_H, -1)
    m = m - v_ring(35.8, z1, GROOVE_H, -1)
    return Part("S3", "Compressor case", quadrant_cut(m), "static", "rear-down", "#b9c0c8")


def build_combustor():
    z0, z1 = M4_Z
    case = lathe([(32.0, z0), (COWL_R, z0), (COWL_R, z1), (32.0, z1)], SEG)
    floor = lathe([(26.0, 157.0), (32.2, 157.0), (32.2, z1), (26.0, z1)], SEG)
    case = union([case, floor, v_ring(35.8, z0, TONGUE_H, -1)])
    case = case - v_ring(35.8, z1, GROOVE_H, -1)
    for zp in (138.0, 152.0):                     # holes for the stand's two pegs (bottom)
        case = case - radial_teardrop(4.4, 33.0, 39.0, zp, 0.0)
    # annular combustion chamber: outer liner, 45 deg dome, inner liner (one profile)
    liner_prof = [(26.0, z1), (26.0, 156.0), (27.6, 150.0), (27.6, 141.0), (18.0, 131.4),
                  (8.4, 141.0), (8.4, 149.0), (14.4, 156.0), (14.4, z1), (16.0, z1),
                  (16.0, 156.0), (10.0, 149.0), (10.0, 141.95), (18.0, 133.95), (26.0, 141.95),
                  (26.0, 150.0), (24.4, 156.0), (24.4, z1)]
    liner = lathe(liner_prof, SEG)
    holes = []
    for k in range(12):                          # dilution air holes
        a = 15.0 + 30.0 * k
        for zh, r0, r1 in ((145.0, 25.0, 29.0), (151.0, 25.0, 29.0), (145.5, 7.0, 11.5)):
            holes.append(radial_teardrop(2.4, r0, r1, zh, a))
    liner = liner - union(holes)
    nozzles = []
    for k in range(12):                          # fuel nozzles on the dome
        a = 30.0 * k
        n = (cyl(1.3, 129.6, 132.6, 20) +
             Manifold.cylinder(1.2, 1.3, 0.5, 20).mirror((0, 0, 1)).translate((0, 0, 129.6)))
        nozzles.append(n.translate((18.0, 0, 0)).rotate((0, 0, a)))
    ngv = blade_row(16, 11.25, skip_cut=True, z_le=153.0, z_te=z1,
                    r_root=const(15.5), r_tip=const(24.9),
                    beta_root=(0.0, 45.0), beta_tip=(0.0, 45.0), t_root=1.6, t_tip=1.6, nj=6)
    liner = union([liner] + nozzles + ngv)
    case, liner = quadrant_cut(case), quadrant_cut(liner)
    whole = case + liner
    return Part("S4", "Combustor (case + flame liner, two colours)", whole, "static",
                "rear-down", "#ff7a1a",
                bodies=[("Combustor case", case, "#b9c0c8"), ("Flame liner", liner, "#ff7a1a")])


def build_turb_case():
    z0, z1 = M5_Z
    prof = curve(turb_case, z0, z1, 20) + curve(cowl, z1, z0, 20)
    m = lathe(prof, SEG) + v_ring(35.8, z0, TONGUE_H, -1)
    m = m - v_ring(33.6, z1, GROOVE_H, -1)
    return Part("S5", "Turbine case", quadrant_cut(m), "static", "rear-down", "#a3abb4")


def build_rear_frame():
    z0, z1 = M6_Z
    hub = lathe([(0.0, z0), (16.3, z0), (17.8, z0 + 1.5), (15.0, z1), (0.0, z1)], 96)
    ring = lathe(curve(nozzle_inner, z0, z1, 12) + curve(cowl, z1, z0, 12), SEG)
    struts = blade_row(8, 22.5, skip_cut=True, z_le=212.0, z_te=z1,
                       r_root=const(15.6), r_tip=lambda z: nozzle_inner(z) + 0.6,
                       beta_root=(0.0, 0.0), beta_tip=(0.0, 0.0), t_root=2.0, t_tip=2.0, nj=4)
    m = union([hub, ring, v_ring(33.6, z0, TONGUE_H, -1)] + struts)
    m = m - cyl(BEARING_D / 2, z0 - 1, z1 + 1, 64)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        m = m - cyl(DOWEL_D / 2, z1 - 5.0, z1 + 1, 16).translate((10.5 * math.cos(a), 10.5 * math.sin(a), 0))
    m = quadrant_cut(m, KEEP_R["rear_frame"])
    return Part("S6", "Rear frame and core nozzle (rear bearing)", m, "static", "rear-down",
                "#a3abb4")


def build_tail_cone():
    z0, z1 = TAIL_Z
    t = np.linspace(0.0, 1.0, 30)
    prof = [(0.0, z0)] + [(15.0 * (1.0 - tt ** 1.6), z0 + tt * (z1 - z0)) for tt in t]
    m = lathe(prof, 96) - cyl(5.6, z0 - 1, z0 + 4.0, 48)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        m = m - cyl(DOWEL_D / 2, z0 - 1, z0 + 5.0, 16).translate((10.5 * math.cos(a), 10.5 * math.sin(a), 0))
    return Part("S7", "Tail cone", m, "static", "front-down", "#cfd4da",
                note="three 1.75 mm filament dowels + glue")


# =============================================================================
# 4. STAND (built in the assembly frame) AND TEXT
# =============================================================================

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BASE_X, BASE_Y, BASE_T = (-15.0, 265.0), (-112.0, 100.0), 12.0


def text_cs(s, cap, font=FONT):
    """Text as a CrossSection, cap height `cap`, centred on the origin."""
    from fontTools.pens.basePen import BasePen
    from fontTools.ttLib import TTFont

    class Flat(BasePen):
        def __init__(self, gs):
            super().__init__(gs)
            self.contours, self.cur = [], []

        def _moveTo(self, p):
            self.cur = [p]

        def _lineTo(self, p):
            self.cur.append(p)

        def _curveToOne(self, p1, p2, p3):
            p0 = self.cur[-1]
            for t in np.linspace(0, 1, 9)[1:]:
                a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
                self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                                 a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

        def _qCurveToOne(self, p1, p2):
            p0 = self.cur[-1]
            for t in np.linspace(0, 1, 7)[1:]:
                a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t * t
                self.cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))

        def _closePath(self):
            if len(self.cur) > 2:
                self.contours.append(self.cur)
            self.cur = []

        _endPath = _closePath

    f = TTFont(font)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(gs)
    gs[cmap[ord("H")]].draw(bp)
    scale = cap / bp.bounds[3]
    contours, x = [], 0.0
    for ch in s:
        g = gs[cmap[ord(ch)]]
        pen = Flat(gs)
        g.draw(pen)
        for c in pen.contours:
            contours.append(np.array([((px + x) * scale, py * scale) for px, py in c]))
        x += g.width
    cs = CrossSection(contours, FillRule.EvenOdd)
    b = cs.bounds()
    return cs.translate((-(b[0] + b[2]) / 2, -cap / 2)), b[2] - b[0]


def arrow_cs(length, width):
    return CrossSection([np.array([(-length / 2, -width / 2), (length / 2, 0.0), (-length / 2, width / 2)])])


def axial_to_assembly(m):
    return m.rotate((0, 90, 0)).translate((0, 0, H_AXIS))


# the four strokes on the front of the stand, each over the name of its section
WORDS = [("SUCK", 25.0), ("SQUEEZE", 92.0), ("BANG", 157.0), ("BLOW", 220.0)]
STATIONS = [("INTAKE + FAN", 25.0), ("COMPRESSOR", 92.0), ("COMBUSTOR", 157.0),
            ("TURBINE + EXHAUST", 220.0)]
ARROWS = (52.0, 128.0, 186.0)


def build_stand(nacelle_axial):
    x0, x1 = BASE_X
    y0, y1 = BASE_Y
    plate = CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))
    plate = plate.offset(-8.0, JoinType.Round).offset(8.0, JoinType.Round)
    base = Manifold.batch_hull([                      # slab with a 1.5 mm top chamfer
        plate.extrude(BASE_T - 1.5).translate((0, 0, -BASE_T)),
        plate.offset(-1.5, JoinType.Round).extrude(0.01).translate((0, 0, -0.01))])

    # core pylon under the combustor, with two locating pegs
    pyl = Manifold.batch_hull([
        Manifold.cube((34.0, 48.0, 0.01)).translate((128.0, -24.0, -0.5)),
        Manifold.cube((24.0, 28.0, 0.01)).translate((133.0, -14.0, 62.0))])
    core_cut = axial_to_assembly(cyl(COWL_R + 0.15, 125.0, 165.0, 192))
    pyl = pyl - core_cut
    saddle = H_AXIS - (COWL_R + 0.15)
    for xp in (138.0, 152.0):
        pyl = pyl + Manifold.cylinder(4.5, 2.0, 2.0, 32).translate((xp, 0, saddle - 0.5)) \
            + Manifold.cylinder(0.6, 2.0, 1.4, 32).translate((xp, 0, saddle + 4.0))
    # nacelle cradle
    cr = Manifold.batch_hull([
        Manifold.cube((46.0, 64.0, 0.01)).translate((42.0, -32.0, -0.5)),
        Manifold.cube((40.0, 50.0, 0.01)).translate((45.0, -25.0, 24.0))])
    nac_env = axial_to_assembly(lathe([(0.0, 30.0)] + [(nac_outer(z) + 0.2, z) for z in np.linspace(30, 95, 40)]
                                      + [(0.0, 95.0)], 256))
    cr = cr - nac_env
    stand = union([base, pyl, cr])

    # text and arrows (a separate colour body, raised 1 mm on the top face)
    letters = []
    for word, x in WORDS:
        letters.append(text_cs(word, 7.0)[0].translate((x, -91.0)))
    for x in ARROWS:
        letters.append(arrow_cs(6.0, 6.0).translate((x, -91.0)))
    for name, x in STATIONS:
        letters.append(text_cs(name, 4.0)[0].translate((x, -103.0)))
    letters.append(text_cs("HOW A JET ENGINE WORKS", 6.0)[0].translate((198.0, 78.0)))
    labels = CrossSection.batch_boolean(letters, OpType.Add).extrude(1.0)
    return stand, labels


# =============================================================================
# 5. PRINT ORIENTATION, CHECKS, EXPORT
# =============================================================================


def to_print(part):
    m = part.solid
    ab = m.bounding_box()                      # axial-frame bounds (do not reuse below)
    if part.orient == "rear-down":
        f = lambda s: s.rotate((180, 0, 0)).translate((0, 0, ab[5]))
    elif part.orient == "front-down":
        f = lambda s: s.translate((0, 0, -ab[2]))
    elif part.orient == "lying":
        f = lambda s: s.rotate((0, 90, 0))
    else:
        f = lambda s: s
    out = f(m)
    pb = out.bounding_box()
    shift = (-(pb[0] + pb[3]) / 2, -(pb[1] + pb[4]) / 2, -pb[2])
    return [(n, f(s).translate(shift), c) for n, s, c in part.bodies], out.translate(shift)


def to_trimesh(m):
    import trimesh
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts),
                           process=False)


def overhang_report(tm, limit_deg=45.0):
    """Areas facing down steeper than the limit, ignoring the bed. Flat ceilings are
    reported separately as bridges with their largest unsupported width."""
    n = tm.face_normals
    c = tm.triangles_center
    a = tm.area_faces
    off_bed = c[:, 2] > 0.05
    lim = -math.cos(math.radians(limit_deg)) - 0.02
    steep = (n[:, 2] < lim) & off_bed
    flat = steep & (n[:, 2] < -0.995)
    over = steep & ~flat
    bridges = []
    if flat.any():
        import trimesh
        sub = tm.submesh([np.where(flat)[0]], append=True)
        for comp in sub.split(only_watertight=False):
            ext = comp.bounds[1] - comp.bounds[0]
            bridges.append((float(min(ext[0], ext[1])), float(comp.area)))
    return float(a[over].sum()), sorted(bridges, reverse=True)


BED = (320.0, 320.0, 320.0)


def check_parts(parts, stand, labels):
    lines, ok = [], True

    def rep(name, passed, msg):
        nonlocal ok
        ok &= passed
        lines.append(f"[{'PASS' if passed else 'FAIL'}] {name}: {msg}")

    items = [(p.key, p.name, to_print(p)[1]) for p in parts] + [("B1", "Stand", stand.translate((0, 0, BASE_T)))]
    for key, name, m in items:
        tm = to_trimesh(m)
        comps = len(m.decompose())
        b = m.bounding_box()
        size = (b[3] - b[0], b[4] - b[1], b[5] - b[2])
        fits = size[0] <= BED[0] and size[1] <= BED[1] and size[2] <= BED[2]
        over, bridges = overhang_report(tm)
        big_bridge = max([w for w, _ in bridges], default=0.0)
        passed = (m.status().name == "NoError" and comps == 1 and fits and over < 5.0
                  and big_bridge <= 12.0)
        vol = m.volume()
        grams = (min(vol, tm.area * 0.84) * 0.85 + 0.15 * vol) * 1.27e-3   # 2 walls, 15 % infill, PETG
        rep(f"{key} {name}", passed,
            f"{size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} mm, ~{grams:.0f} g, {comps} solid, "
            f"overhang >45deg {over:.1f} mm2, widest flat ceiling {big_bridge:.1f} mm, "
            f"{m.volume() / 1000:.1f} cm3")
    return ok, lines


def rotor_envelope(rotor_parts, dz=0.05):
    """Largest radius the spinning rotor reaches in each axial bin. The radius is convex,
    so over a triangle clipped to a bin it peaks at a corner of the clipped polygon: a
    vertex inside the bin or an edge crossing one of the bin's two boundary planes."""
    zs = np.arange(0.0, 260.0, dz)
    env = np.zeros(len(zs))
    for p in rotor_parts:
        tm = to_trimesh(p.solid)
        V = tm.vertices
        rv = np.hypot(V[:, 0], V[:, 1])
        iv = np.clip(np.floor(V[:, 2] / dz).astype(int), 0, len(zs) - 1)
        np.maximum.at(env, iv, rv)
        E = tm.edges_unique
        a, b = V[E[:, 0]], V[E[:, 1]]
        lo = np.minimum(a[:, 2], b[:, 2])
        hi = np.maximum(a[:, 2], b[:, 2])
        k0 = np.ceil(lo / dz).astype(int)
        k1 = np.floor(hi / dz).astype(int)
        n = np.maximum(0, k1 - k0 + 1)
        e = np.repeat(np.arange(len(E)), n)
        k = np.concatenate([np.arange(x, x + c) for x, c in zip(k0[n > 0], n[n > 0])]) if n.sum() else np.zeros(0, int)
        zb = k * dz
        t = np.where(np.abs(b[e, 2] - a[e, 2]) > 1e-12, (zb - a[e, 2]) / (b[e, 2] - a[e, 2] + 1e-300), 0.0)
        P = a[e] + t[:, None] * (b[e] - a[e])
        rb = np.hypot(P[:, 0], P[:, 1])
        for kk in (k, k - 1):                      # the plane bounds the bins on both sides
            np.maximum.at(env, np.clip(kk, 0, len(zs) - 1), rb)
    return zs, env


def running_gaps(rotor_parts, static_parts, n_samples=150000):
    """Smallest distance in the (z, r) half-plane between each static part and the
    volume swept by the spinning rotor."""
    import trimesh
    zs, env = rotor_envelope(rotor_parts)
    dz = zs[1] - zs[0]
    out = []
    for p in static_parts:
        tm = to_trimesh(p.solid)
        pts, _ = trimesh.sample.sample_surface(tm, n_samples, seed=1)
        pts = np.vstack([pts, tm.vertices])
        zp = pts[:, 2]
        rp = np.sqrt(pts[:, 0] ** 2 + pts[:, 1] ** 2)
        best = np.full(len(pts), 1e9)
        ip = np.floor(zp / dz).astype(int)
        for off in range(-60, 61):
            j = np.clip(ip + off, 0, len(zs) - 1)
            e = env[j]
            ddz = np.maximum(0.0, np.abs(zs[j] + 0.5 * dz - zp) - 0.5 * dz)
            ddr = np.maximum(0.0, rp - e)
            inside = (rp <= e) & (ddz == 0)
            d = np.where(inside, -1.0, np.sqrt(ddz ** 2 + ddr ** 2))
            best = np.minimum(best, np.where(e > 0, d, 1e9))
        k = int(np.argmin(best))
        out.append((p.key, p.name, float(best[k]), float(zp[k]), float(rp[k])))
    return out


def check_assembly(parts, stand):
    lines, ok = [], True

    def rep(name, passed, msg):
        nonlocal ok
        ok &= passed
        lines.append(f"[{'PASS' if passed else 'FAIL'}] {name}: {msg}")

    rotor = [p for p in parts if p.rotor]
    static = [p for p in parts if not p.rotor]
    # 1. static parts must not overlap each other (joints have clearance or just touch)
    worst = (0.0, "")
    for i in range(len(static)):
        for j in range(i + 1, len(static)):
            v = (static[i].solid ^ static[j].solid).volume()
            if v > worst[0]:
                worst = (v, f"{static[i].key}/{static[j].key}")
    rep("static parts overlap", worst[0] < 0.05, f"largest overlap {worst[0]:.3f} mm3 {worst[1]}")
    # 2. rotor parts may touch each other (they are one rotor) but must not overlap,
    #    except the two crush-rib press fits on the shaft
    press = {("R0", "R1"), ("R0", "C1")}
    worst, fits = (0.0, ""), []
    for i in range(len(rotor)):
        for j in range(i + 1, len(rotor)):
            v = (rotor[i].solid ^ rotor[j].solid).volume()
            if (rotor[i].key, rotor[j].key) in press:
                fits.append(f"{rotor[i].key}/{rotor[j].key} {v:.2f} mm3")
            elif v > worst[0]:
                worst = (v, f"{rotor[i].key}/{rotor[j].key}")
    rep("rotor parts overlap", worst[0] < 0.05, f"largest overlap {worst[0]:.3f} mm3 {worst[1]}")
    rep("crush-rib press fits", len(fits) == 2 and all(float(f.split()[1]) > 0.5 for f in fits),
        "interference " + ", ".join(fits))
    # 3. running clearance: every static part against the whole spinning rotor
    for key, name, gap, z, r in running_gaps(rotor, static):
        need = THRUST - 0.06          # the 0.05 mm bins can read up to one bin short
        rep(f"running gap {key}", gap >= need,
            f"{gap:.2f} mm at z={z:.1f} r={r:.1f} ({name})")
    # 4. the engine sits in the stand without touching anything but its saddles
    eng = union([axial_to_assembly(p.solid) for p in static])
    v = (eng ^ stand).volume()
    rep("engine vs stand", v < 0.05, f"overlap {v:.3f} mm3")
    return ok, lines


def write_3mf(path, objects, title):
    """3MF with one or more objects; an object with several bodies is written as one
    object made of parts (components), so each body can get its own filament."""
    import zipfile
    res, build, oid = [], [], 1
    mats = []
    for obj_name, bodies, placement in objects:
        ids = []
        for bname, tm, color in bodies:
            if color not in mats:
                mats.append(color)
            v = "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
            t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
            res.append(f'<object id="{oid}" name="{bname}" type="model" pid="1" pindex="{mats.index(color)}">'
                       f'<mesh><vertices>\n{v}\n</vertices><triangles>\n{t}\n</triangles></mesh></object>')
            ids.append(oid)
            oid += 1
        if len(ids) == 1:
            top = ids[0]
        else:
            comps = "".join(f'<component objectid="{i}"/>' for i in ids)
            res.append(f'<object id="{oid}" name="{obj_name}" type="model"><components>{comps}</components></object>')
            top = oid
            oid += 1
        x, y = placement
        build.append(f'<item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0"/>')
    base = "".join(f'<base name="c{i}" displaycolor="{c.upper()}FF"/>' for i, c in enumerate(mats))
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
             f'<metadata name="Title">{title}</metadata>\n<resources>\n'
             f'<basematerials id="1">{base}</basematerials>\n'
             + "\n".join(res) + '\n</resources>\n<build>' + "".join(build) + '</build>\n</model>\n')
    # material ids must not collide with object ids: shift objects up by one
    model = model.replace('<basematerials id="1">', '<basematerials id="1000">').replace('pid="1"', 'pid="1000"')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def pack(items, bed=(310.0, 310.0), gap=6.0):
    """Shelf-pack (key, w, d) footprints onto plates. Returns [[(key, cx, cy)], ...]."""
    plates, cur, x, y, row_d = [], [], 0.0, 0.0, 0.0
    for key, w, d in sorted(items, key=lambda t: -t[2]):
        if x + w > bed[0]:
            x, y, row_d = 0.0, y + row_d + gap, 0.0
        if y + d > bed[1]:
            plates.append(cur)
            cur, x, y, row_d = [], 0.0, 0.0, 0.0
        cur.append((key, x + w / 2 + 5.0, y + d / 2 + 5.0))   # bed coordinates, 5 mm margin
        x += w + gap
        row_d = max(row_d, d)
    if cur:
        plates.append(cur)
    return plates


PLATES = [  # what prints together (all PETG, no supports)
    ("plate1_nacelle", ["S1"]),
    ("plate2_stand", ["B1"]),
    ("plate3_core", ["S2", "S3", "S4", "S5", "S6", "S7", "R1"]),
    ("plate4_rotor", ["R0", "C1", "C2", "C3", "C4", "C5", "C6", "T1", "T2", "T3", "T4"]),
]


def build_all(verbose=True):
    t = []
    log = (lambda s: print(s, flush=True)) if verbose else (lambda s: None)
    log("building rotor ...")
    t.append(build_shaft())
    t.append(build_fan())
    t += [build_comp_stage(k) for k in range(len(COMP))]
    t += [build_turb_stage(k) for k in range(len(TURB))]
    log("building casings ...")
    t += [build_nacelle(), build_front_frame(), build_comp_case(), build_combustor(),
          build_turb_case(), build_rear_frame(), build_tail_cone()]
    log("building stand ...")
    nac = next(p for p in t if p.key == "S1")
    stand, labels = build_stand(nac.solid)
    return t, stand, labels


def export(parts, stand, labels, results, out_dir):
    import trimesh
    os.makedirs(out_dir, exist_ok=True)
    stl_dir = os.path.join(out_dir, "stl")
    os.makedirs(stl_dir, exist_ok=True)
    printed = {}
    for p in parts:
        bodies, whole = to_print(p)
        printed[p.key] = (p.name, bodies, whole)
    sb = stand.translate((0, 0, BASE_T))
    lb = labels.translate((0, 0, BASE_T))
    cx = -(BASE_X[0] + BASE_X[1]) / 2
    cy = -(BASE_Y[0] + BASE_Y[1]) / 2
    printed["B1"] = ("Stand with labels", [("Stand", sb.translate((cx, cy, 0)), "#24272e"),
                                           ("Labels", lb.translate((cx, cy, 0)), "#f4f4f4")],
                     (sb + lb).translate((cx, cy, 0)))

    # one STL per part (print orientation) and one 3MF per print plate
    for key, (name, bodies, whole) in printed.items():
        slug = name.split(" (")[0].lower().replace(" ", "_").replace(",", "")
        to_trimesh(whole).export(os.path.join(stl_dir, f"{key}_{slug}.stl"))
    for plate, keys in PLATES:
        foot = []
        for k in keys:
            b = printed[k][2].bounding_box()
            foot.append((k, b[3] - b[0], b[4] - b[1]))
        layout = pack(foot)
        assert len(layout) == 1, f"{plate} does not fit one plate"
        objs = []
        for k, x, y in layout[0]:
            name, bodies, _ = printed[k]
            objs.append((f"{k} {name}", [(f"{k} {bn}", to_trimesh(s), c) for bn, s, c in bodies], (x, y)))
        write_3mf(os.path.join(out_dir, f"CutawayTurbofan_{plate}.3mf"), objs,
                  f"Cutaway Turbofan - {plate}")

    # the assembled engine for renders: GLB in the assembly frame + part list
    scene = trimesh.Scene()
    meta = []
    i = 0
    for p in parts:
        for bn, s, c in p.bodies:
            scene.add_geometry(to_trimesh(axial_to_assembly(s)), node_name=f"p{i}", geom_name=f"p{i}")
            meta.append(dict(key=p.key, name=bn, color=c, rotor=p.rotor, kind=p.kind))
            i += 1
    for bn, s, c in (("Stand", stand, "#24272e"), ("Labels", labels, "#f4f4f4")):
        scene.add_geometry(to_trimesh(s), node_name=f"p{i}", geom_name=f"p{i}")
        meta.append(dict(key="B1", name=bn, color=c, rotor=False, kind="stand"))
        i += 1
    scene.export(os.path.join(out_dir, "CutawayTurbofan_assembly.glb"))
    with open(os.path.join(out_dir, "CutawayTurbofan_assembly_parts.json"), "w") as fh:
        json.dump(dict(axis_height=H_AXIS, parts=meta), fh, indent=1)

    with open(os.path.join(out_dir, "CutawayTurbofan_report.txt"), "w") as fh:
        fh.write("Cutaway Turbofan - build report\n\n" + "\n".join(results) + "\n")
    print(f"wrote {out_dir}/")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default="models")
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args(argv)
    parts, stand, labels = build_all()
    results, ok = [], True
    if not args.no_check:
        print("checking printability ...", flush=True)
        ok1, l1 = check_parts(parts, stand, labels)
        print("checking the assembly ...", flush=True)
        ok2, l2 = check_assembly(parts, stand)
        results = l1 + [""] + l2
        ok = ok1 and ok2
        print("\n".join(results))
    export(parts, stand, labels, results, args.out)
    if not ok:
        print("SOME CHECKS FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
