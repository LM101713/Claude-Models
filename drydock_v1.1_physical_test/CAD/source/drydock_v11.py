#!/usr/bin/env python3
"""
DRYDOCK V1.1 (development): Prototype 001 with the corrections from the V1.1 design review.
See DESIGN_REVIEW.md next to this file. Prototype 001 itself is untouched in ../drydock.py.

Changes from P001 (each is a parameter or a small local feature, not a redesign):
  R1  bayonet clearances re-sized for FDM tolerance stacks (fit 0.30, tip 0.35, flank play 0.40,
      slot 0.40) and lug height 1.3 so engagement over the lip stays 1.0 mm
  R2  detent interference set from FEA + tolerance stack; fit-test set brackets it
  R3  lead-in ramp on each lug's leading bearing flank (no catch on the slot edge)
  R4  lock marks / index flutes moved off the loaded lip onto the stop webs
  R5  thicker head wall under the index flutes; chamfer at the plug root; bigger mouth chamfer
  R6  twist-lock window, retained in both directions (P001 relied on crush-rib friction inward)
  R7  adapter bump lead-ins sized for the full spring travel (P001 0.45 mm < 0.55-1.0 mm travel)
  R8  fit-test plate: double-ended gauge (both print orientations), detent tuning rings,
      cap + window + adapter

Parametric CAD in build123d (OpenCascade B-rep). One script builds every part from the
parameters in `Params`, checks the fits by real boolean geometry, and exports STEP, STL and 3MF.

    pip install -r requirements.txt
    python drydock.py                        # build, validate, export everything to ./models
    python drydock.py --set body_od=47 --set spool_bore=56   # change any parameter
    python drydock.py --params my.json       # or load overrides from a JSON file
    python drydock.py --quick                # build + export, skip the slow fit sweeps

Coordinate conventions
----------------------
Socket frame: the rim (end face) of a body socket is z = 0 and the body interior is +z.
A cap or coupler half is built in this same frame, so it is already "installed" when placed
as-is; its lugs sit at angles 0/120/240 deg when unlocked and turn +90 deg (counter-clockwise
seen from +z, i.e. CLOCKWISE seen from outside, looking at the cap face) to lock.
The second end of the body is the first end turned 180 deg about X (a rotation, not a mirror),
so both ends have the same handedness and the same cap fits either end.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from build123d import (Axis, Box, Color, Cylinder, Mesher, Plane, Polygon, Pos, Rot, Compound,
                       export_step, export_stl, extrude, revolve, Part)

try:
    from shapely.geometry import LineString, LinearRing
    from shapely.ops import unary_union
except ImportError:  # only the wordmark needs shapely
    LineString = None

HERE = Path(__file__).resolve().parent


# ======================================================================================
# PARAMETERS: every dimension lives here. Lengths in mm, angles in degrees.
# ======================================================================================
@dataclass
class Params:
    # ---- spool (preliminary assumptions; MEASURE YOUR SPOOL) ---------------------------
    spool_bore: float = 55.0          # hub bore diameter the default adapter is made for
    spool_width: float = 67.0         # flange-to-flange width; cartridge must not protrude
    length_margin: float = 3.0        # total cartridge length = spool_width - this

    # ---- cartridge body ---------------------------------------------------------------
    body_od: float = 46.0             # outside diameter of body, cap heads and adapter rings
    wall: float = 2.0                 # vented wall thickness
    socket_bore: float = None         # bore of each end socket; default body_od - 7.0 (= 39.0)
    rim_chamfer: float = 0.6          # outer chamfer at each body rim (forms a V parting line)
    mouth_chamfer: float = 0.8        # lead-in chamfer at the socket bore (R5: was 0.5)
    collar_extra: float = 1.0         # solid collar left below the groove before the taper

    # ---- QuickLock bayonet ------------------------------------------------------------
    lug_count: int = 3
    lug_width_deg: float = 14.0       # angular width of each lug
    lug_radial: float = 1.3           # how far a lug stands proud of the plug (R1: was 1.2)
    lug_tip_height: float = 2.0       # axial height of the lug at its tip
    flank_deg: float = 45.0           # flank angle from the radial plane (45 = printable)
    fit_radial: float = 0.30          # plug-to-socket radial clearance (R1: was 0.20)
    lug_tip_clear: float = 0.35       # lug tip to groove floor, radial (R1: was 0.25)
    bearing_play: float = 0.40        # axial play on the load-bearing flank (R1: was 0.20)
    inner_play: float = 0.50          # axial play on the inner flank
    slot_clear: float = 0.40          # entry-slot side clearance (R1: was 0.30)
    stop_clear: float = 0.30          # gap between lug and hard stop when fully turned
    lip: float = 2.0                  # axial thickness of the retaining lip at the bore
    travel_deg: float = 90.0          # quarter turn
    detent_interference: float = 0.30  # R2: tongue deflection at the bump (was 0.25 on the rigid collar)
    detent_halfwidth_deg: float = 6.0  # half-width of the detent bump
    plug_wall: float = 1.6
    plug_tip_gap: float = 0.4         # plug tip to collar taper
    plug_root_chamfer: float = 0.4    # R5: fills the sharp neck-face / plug corner
    lug_lead_depth: float = 0.4       # R3: lead-in on the leading bearing flank of each lug
    lug_lead_deg: float = 4.0
    index_offset_deg: float = 15.0    # R4: index flutes / lock marks sit 15 deg past the lugs (on the webs)
    detent_tuning: tuple = (-0.1, 0.1)  # R8: offsets for the two detent tuning rings
    # R2: the detent bump sits on a spring tongue cut in the collar skin (P001: on the rigid
    # collar, so the whole anchored plug had to flex: FEA 570 N/mm per lug -> ~8 N.m to turn)
    tongue_start_deg: float = 52.0    # tongue root (angle from the lug's entry position)
    tongue_end_deg: float = 88.0      # tongue free end, just past the bump (keeps slit bridges < 15 mm)
    tongue_slit: float = 0.8          # slit width around the tongue
    tongue_thickness: float = 9.0     # radial; >= skin means no outer relief (full skin, 2.15 mm)

    # ---- caps -------------------------------------------------------------------------
    head_height: float = 5.5          # grip head, including the face plate
    face_thickness: float = 2.4
    head_wall: float = 2.4             # R5: was 2.2
    neck_od: float = None             # the adapter ring rides on this; default body_od - 4.0 (= 42.0)
    base_chamfer: float = 0.8         # cap face edge (on the bed: chamfer, not fillet)
    head_top_chamfer: float = 0.4
    flute_count: int = 24
    flute_radius: float = 1.0
    flute_depth: float = 0.45
    index_flute_depth: float = 0.6    # R5: was 0.9 (left 1.3 mm of head wall)
    face_slot_count: int = 20
    face_slot_width: float = 1.2
    face_slot_r_in: float = 10.8
    face_slot_r_out: float = 18.2

    # ---- moisture indicator window ------------------------------------------------------
    window_aperture: float = 14.0     # clear viewing diameter through the cap face
    # R6 twist-lock window: disc + 3 ears; ears turn under a 45-deg ledge on the inside of the face
    window_body_r: float = 8.3
    window_ear_r: float = 9.3
    window_ear_deg: float = 30.0
    window_turn_deg: float = 60.0
    window_fit: float = 0.15          # radial clearance, disc and ears
    window_grip_h: float = 1.4        # grip bar on the inner face, to turn it from inside
    window_diameter: float = 18.0     # window disc diameter
    window_thickness: float = 1.2
    window_radial_clear: float = 0.10
    window_seat_depth: float = 1.4    # recess depth from the inside of the face plate
    window_ribs: int = 6              # crush ribs that keep the window from falling inward
    window_rib_interference: float = 0.15
    film_thickness: float = 0.5       # for the optional film-window retainer ring

    # ---- vents ------------------------------------------------------------------------
    vent_width: float = 1.2           # < bead size. 1.2 mm retains beads of 1.5 mm and up
    vent_rows: int = 2
    vent_per_row: int = 40            # positions per row before the label panel removes some
    vent_row_gap: float = 2.0         # solid hoop band between rows
    vent_margin: float = 0.8          # solid band between vents and collar tapers
    label_sector_deg: float = 72.0    # vent-free panel for the wordmark
    label_angle_deg: float = 180.0

    # ---- wordmark ---------------------------------------------------------------------
    brand_text: str = "DRYDOCK"
    text_height: float = 4.2
    text_letter_width: float = 2.75
    text_tracking: float = 1.15
    text_stroke: float = 0.72
    text_depth: float = 0.45
    lock_mark_depth: float = 0.6
    lock_mark_width: float = 1.6
    lock_mark_length: float = 3.0

    # ---- spool adapters ---------------------------------------------------------------
    adapter_thickness: float = 3.6
    adapter_axial_play: float = 0.3   # neck length = adapter thickness + this
    adapter_radial_clear: float = 0.20
    adapter_arms: int = 3
    arm_thickness: float = 1.5        # radial thickness of each spring arm
    arm_length: float = 10.5          # arc length of the free arm
    arm_root: float = 3.0             # arc length of the root spoke
    bump_height: float = 0.7
    bump_width: float = 3.6           # arc length of the contact bump
    preload: float = 0.55             # nominal radial spring deflection in the target bore
    arm_gap_min: float = 1.0          # minimum gap under the arm (and overload stop gap)
    bump_chamfer: float = 0.45        # (P001 value, unused in V1.1)
    bump_leadin: float = 1.15         # R7: radial depth of the insertion lead-in (>= max spring travel)
    bump_leadin_deg: float = 35.0     # R7: lead-in angle from the axis
    adapter_sizes: tuple = (52.0, 53.5, 55.0, 56.5, 58.0, 60.0)

    # ---- tessellation -------------------------------------------------------------------
    stl_tolerance: float = 0.01
    stl_angular: float = 0.1

    # ---- derived ------------------------------------------------------------------------
    def d(self):
        """Derived dimensions. Everything downstream reads these, never literals."""
        D = {}
        D["R_o"] = self.body_od / 2
        D["R_i"] = D["R_o"] - self.wall
        D["R_s"] = (self.socket_bore or self.body_od - 7.0) / 2
        D["R_p"] = D["R_s"] - self.fit_radial
        D["R_pi"] = D["R_p"] - self.plug_wall
        D["R_lt"] = D["R_p"] + self.lug_radial
        D["R_g"] = D["R_lt"] + self.lug_tip_clear
        D["tanf"] = math.tan(math.radians(self.flank_deg))
        D["tip_half"] = self.lug_tip_height / 2
        # lug half-height at radius r (both flanks at flank_deg)
        D["hl"] = lambda r: D["tip_half"] + (D["R_lt"] - r) * D["tanf"]
        D["z_c"] = self.lip + D["hl"](D["R_s"]) + self.bearing_play          # lug centre, socket frame
        D["groove_end"] = D["z_c"] + D["hl"](D["R_s"]) + self.inner_play    # groove inner flank at bore
        D["collar"] = D["groove_end"] + self.collar_extra                    # straight collar length
        D["taper"] = (D["R_i"] - D["R_s"])                                  # 45 deg taper length
        D["collar_total"] = D["collar"] + D["taper"]
        D["plug_len"] = D["collar"] - self.plug_tip_gap
        D["neck_len"] = self.adapter_thickness + self.adapter_axial_play
        D["R_neck"] = (self.neck_od or self.body_od - 4.0) / 2
        D["cap_out"] = self.head_height + D["neck_len"]                     # cap length outside the rim
        D["L_total"] = self.spool_width - self.length_margin
        D["L_body"] = D["L_total"] - 2 * D["cap_out"]
        D["R_hi"] = D["R_o"] - self.head_wall                               # head cavity radius at face
        D["ang_slot"] = math.degrees(self.slot_clear / D["R_lt"])
        D["ang_stop"] = math.degrees(self.stop_clear / D["R_lt"])
        D["lug_half"] = self.lug_width_deg / 2
        D["web_deg"] = (360 / self.lug_count - self.travel_deg - self.lug_width_deg
                        - D["ang_slot"] - D["ang_stop"])
        D["R_win"] = self.window_diameter / 2
        D["R_rec"] = D["R_win"] + self.window_radial_clear
        D["R_ap"] = self.window_aperture / 2
        return D

    def check(self):
        D = self.d()
        problems = []
        if D["web_deg"] < 8:
            problems.append(f"bayonet web between grooves only {D['web_deg']:.1f} deg: "
                            "reduce lug width, lug count or travel")
        if D["R_o"] - D["R_g"] < 1.8:
            problems.append(f"skin outside the groove is {D['R_o'] - D['R_g']:.2f} mm (< 1.8)")
        if self.plug_wall < 1.2:
            problems.append("plug wall < 1.2 mm")
        if D["L_body"] < 2 * D["collar_total"] + 10:
            problems.append("body too short for two sockets plus a vent band")
        if D["R_hi"] < self.face_slot_r_out + 0.8:
            problems.append("face slots run past the head cavity")
        if D["R_neck"] - D["R_p"] < 1.0:
            problems.append("neck shoulder bearing on the rim is < 1 mm wide")
        return problems


# ======================================================================================
# small geometry helpers
# ======================================================================================
def rz_revolve(pts, arc=360.0, start=0.0):
    """Revolve a closed (r, z) polygon about Z. arc/start in degrees (CCW about +Z)."""
    face = Plane.XZ * Polygon(*pts, align=None)
    solid = revolve(face, Axis.Z, arc)
    return Rot(0, 0, start) * solid if start else solid


def ccw(pts):
    """Polygon points in counter-clockwise order, so a face built from them has a +Z normal
    and extrudes upward (a clockwise outline silently extrudes the other way)."""
    pts = list(pts)
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts[::-1] if area < 0 else pts


def xy_extrude(pts, z0, z1):
    face = Polygon(*ccw(pts), align=None)
    return Pos(0, 0, z0) * extrude(face, z1 - z0)


def polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def arc_pts(r, a0, a1, n=None):
    n = n or max(4, int(abs(a1 - a0) / 1.5) + 1)
    return [polar(r, a0 + (a1 - a0) * i / n) for i in range(n + 1)]


def sector(r0, r1, a0, a1):
    """Annular sector polygon in XY."""
    return arc_pts(r1, a0, a1) + arc_pts(r0, a1, a0)


def union_all(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes:
        return None
    out = shapes[0]
    if len(shapes) > 1:
        out = out.fuse(*shapes[1:]).clean()
    return out


def cut_all(base, tools):
    tools = [t for t in tools if t is not None]
    if not tools:
        return base
    return base.cut(*tools).clean()


def as_part(shape):
    """Return a single Solid if the result is one body, else the compound."""
    sols = shape.solids()
    return sols[0] if len(sols) == 1 else shape


def flip_end(shape, z_offset):
    """Second end of a body: rotate 180 deg about X (keeps handedness) and lift."""
    return Pos(0, 0, z_offset) * (Rot(180, 0, 0) * shape)


# ======================================================================================
# QuickLock bayonet: lugs (male) and socket cut (female)
# ======================================================================================
def lug(P: Params, angle_deg: float):
    """One lug in the socket frame, centred at angle_deg, unlocked position."""
    D = P.d()
    r_root = D["R_p"] - 0.4                      # sink the root into the plug wall
    a = D["lug_half"]
    ch = 0.45                                    # plan-view chamfer on the tip corners (rides the detent)
    cha = math.degrees(ch / D["R_lt"])
    plan = ([polar(r_root, -a), polar(D["R_lt"] - ch, -a)]
            + arc_pts(D["R_lt"], -a + cha, a - cha)
            + [polar(D["R_lt"] - ch, a), polar(r_root, a)])
    zc, hl = D["z_c"], D["hl"]
    prism = xy_extrude(plan, zc - hl(r_root) - 0.1, zc + hl(r_root) + 0.1)
    trap = rz_revolve([(r_root, zc - hl(r_root)), (D["R_lt"], zc - D["tip_half"]),
                       (D["R_lt"], zc + D["tip_half"]), (r_root, zc + hl(r_root))])
    body = prism & trap
    # R3: lead-in on the leading (+theta) bearing flank, a 4-step staircase rising to
    # lug_lead_depth at the leading face, so a lug that meets the lip edge (negative play from
    # tolerances) rides under it instead of catching on the slot edge
    if P.lug_lead_depth > 0:
        cuts = []
        steps = 4
        for j in range(steps):
            d = P.lug_lead_depth * (j + 1) / steps
            a0 = a - P.lug_lead_deg + P.lug_lead_deg * j / steps
            r0, r1 = D["R_p"], D["R_lt"] + 0.2
            fl = lambda r: zc - (D["tip_half"] + (D["R_lt"] - r) * D["tanf"]) + d
            prof = [(r0, zc - 6), (r1, zc - 6), (r1, fl(r1)), (r0, fl(r0))]
            cuts.append(rz_revolve(prof, a + 0.5 - a0, a0))
        body = cut_all(body, cuts)
    return Rot(0, 0, angle_deg) * body


def socket_cutter(P: Params, detent=None):
    """Everything removed from one body end (socket frame): grooves with detent bumps left in,
    entry slots, and the external lock marks."""
    D = P.d()
    zc, hl, tf = D["z_c"], D["hl"], D["tanf"]
    r_in = D["R_s"] - 0.6
    Rg = D["R_g"]
    # groove (r,z) profile: lug profile grown by the plays; flanks extended to the floor
    zb = lambda r: zc - (D["tip_half"] + P.bearing_play + (D["R_lt"] - r) * tf)
    zi = lambda r: zc + (D["tip_half"] + P.inner_play + (D["R_lt"] - r) * tf)
    gprof = [(r_in, zb(r_in)), (Rg, zb(Rg)), (Rg, zi(Rg)), (r_in, zi(r_in))]
    a = D["lug_half"]
    g0 = -(a + D["ang_slot"])                               # groove start (entry-slot side)
    g1 = P.travel_deg + a + D["ang_stop"]                    # groove end = hard stop
    slot_half = a + D["ang_slot"]
    sprof = [(r_in, -1.0), (Rg, -1.0), (Rg, zc), (r_in, zc)]
    # detent bump: cosine hump left standing on the groove floor just before the locked pocket
    h = P.lug_tip_clear + (P.detent_interference if detent is None else detent)
    ab = P.detent_halfwidth_deg
    tb = P.travel_deg - a - 0.3 - ab                        # bump centre (lug trailing edge clears it)
    hump = []
    n = 24
    for i in range(n + 1):
        t = -ab + 2 * ab * i / n
        r = Rg - h * (0.5 + 0.5 * math.cos(math.pi * t / ab))
        hump.append(polar(r, tb + t))
    hump = [polar(Rg + 0.6, tb + ab + 0.5)] + hump[::-1] + [polar(Rg + 0.6, tb - ab - 0.5)]
    hump = hump[::-1]
    bump = xy_extrude(hump, zb(r_in) - 1, zi(r_in) + 1)

    tools = []
    # R2 detent spring tongue (per lug): slits above/below the groove floor band and at the free
    # end, plus a shallow outer relief so the tongue is tongue_thickness thick
    zt0, zt1 = zb(Rg), zi(Rg)
    sl = P.tongue_slit
    Ro = D["R_o"]
    t_a0, t_a1 = P.tongue_start_deg, P.tongue_end_deg
    end_w = math.degrees(sl / (Rg + 1.0))
    slit_lo = rz_revolve([(Rg - 0.01, zt0 - sl), (Ro + 1, zt0 - sl), (Ro + 1, zt0), (Rg - 0.01, zt0)],
                         t_a1 + end_w - t_a0, t_a0)
    slit_hi = rz_revolve([(Rg - 0.01, zt1), (Ro + 1, zt1), (Ro + 1, zt1 + sl), (Rg - 0.01, zt1 + sl)],
                         t_a1 + end_w - t_a0, t_a0)
    slit_end = rz_revolve([(Rg - 0.01, zt0 - sl), (Ro + 1, zt0 - sl), (Ro + 1, zt1 + sl), (Rg - 0.01, zt1 + sl)],
                          end_w, t_a1)
    relief_r = Rg + P.tongue_thickness
    relief = rz_revolve([(relief_r, zt0 - sl), (Ro + 1, zt0 - sl), (Ro + 1, zt1 + sl), (relief_r, zt1 + sl)],
                        t_a1 + end_w - t_a0, t_a0) if relief_r < Ro - 0.05 else None
    tongue_tools = [x for x in (slit_lo, slit_hi, slit_end, relief) if x is not None]
    for k in range(P.lug_count):
        base = 360.0 * k / P.lug_count
        tools += [Rot(0, 0, base) * x for x in tongue_tools]
    for k in range(P.lug_count):
        base = 360.0 * k / P.lug_count
        groove = rz_revolve(gprof, g1 - g0, base + g0)
        groove = groove - (Rot(0, 0, base) * bump)
        slot = rz_revolve(sprof, 2 * slot_half, base - slot_half)
        tools += [groove, slot]
    # lock marks: small V-notches on the outside at each locked lug position
    for k in range(P.lug_count):
        ang = 360.0 * k / P.lug_count + P.travel_deg + P.index_offset_deg   # R4: on the web
        w, dpt = P.lock_mark_width, P.lock_mark_depth
        tri = [(D["R_o"] + 0.5, -w / 2 - 0.5), (D["R_o"] - dpt, 0.0), (D["R_o"] + 0.5, w / 2 + 0.5)]
        mark = Rot(0, 0, ang) * xy_extrude(tri, -1.0, P.lock_mark_length)
        tools.append(mark)
    return tools


# ======================================================================================
# wordmark: a custom stroke alphabet (no font files, identical output on every machine)
# ======================================================================================
def _glyph_lines(ch, w, h):
    r = min(w, h) * 0.5
    def arc(cx, cy, rad, a0, a1, n=14):
        return [(cx + rad * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + rad * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    rr = w * 0.48
    if ch == "D":
        return [[(0, 0), (0, h), (w - rr, h)] + arc(w - rr, h - rr, rr, 90, 0)
                + [(w, rr)] + arc(w - rr, rr, rr, 0, -90) + [(0, 0)]]
    if ch == "R":
        mid = h * 0.47
        br = (h - mid) / 2
        return [[(0, 0), (0, h), (w - br, h)] + arc(w - br, h - br, br, 90, -90) + [(0, mid)],
                [(w * 0.42, mid), (w, 0)]]
    if ch == "Y":
        m = h * 0.45
        return [[(0, h), (w / 2, m), (w, h)], [(w / 2, m), (w / 2, 0)]]
    if ch == "O":
        return [[(rr, 0), (w - rr, 0)] + arc(w - rr, rr, rr, -90, 0) + [(w, h - rr)]
                + arc(w - rr, h - rr, rr, 0, 90) + [(rr, h)] + arc(rr, h - rr, rr, 90, 180)
                + [(0, rr)] + arc(rr, rr, rr, 180, 270)]
    if ch == "C":
        return [[(w, h - rr * 0.35)] + arc(w - rr, h - rr, rr, 20, 90)[1:] + [(rr, h)]
                + arc(rr, h - rr, rr, 90, 180) + [(0, rr)] + arc(rr, rr, rr, 180, 270)
                + [(w - rr, 0)] + arc(w - rr, rr, rr, -90, -20)[:-1] + [(w, rr * 0.35)]]
    if ch == "K":
        m = h * 0.45
        return [[(0, 0), (0, h)], [(w, h), (0, m * 0.9)], [(w * 0.38, m * 1.02), (w, 0)]]
    raise ValueError(f"no glyph for {ch!r}")


def glyph_polygons(ch, P: Params):
    """Return shapely polygons for one glyph, origin at bottom-left of the glyph box."""
    w, h, s = P.text_letter_width, P.text_height, P.text_stroke
    # draw the centreline inset by half a stroke so the outer edge lands on the glyph box
    lines = _glyph_lines(ch, w - s, h - s)
    shapes = []
    for ln in lines:
        closed = len(ln) > 3 and math.dist(ln[0], ln[-1]) < 1e-6
        geom = LinearRing(ln[:-1]) if closed else LineString(ln)
        shapes.append(geom.buffer(s / 2, cap_style=2, join_style=2, mitre_limit=2.0))
    poly = unary_union(shapes)
    from shapely.affinity import translate
    poly = translate(poly, s / 2, s / 2)
    return list(poly.geoms) if hasattr(poly, "geoms") else [poly]


def wordmark_cutters(P: Params, z_mid):
    """Engraving tools for the wordmark wrapped round the body, one glyph at a time
    (each glyph is <3 mm wide, so its chord error on R23 is < 0.05 mm)."""
    if LineString is None:
        print("  (shapely missing: wordmark skipped)")
        return []
    D = P.d()
    R = D["R_o"]
    text = P.brand_text
    total = len(text) * P.text_letter_width + (len(text) - 1) * P.text_tracking
    tools = []
    s = -total / 2
    for ch in text:
        cx = s + P.text_letter_width / 2
        ang = P.label_angle_deg + math.degrees(cx / R)       # reads left-to-right from outside
        for poly in glyph_polygons(ch, P):
            outer = [(x - P.text_letter_width / 2, y - P.text_height / 2)
                     for x, y in list(poly.exterior.coords)[:-1]]
            prism = extrude(Polygon(*ccw(outer), align=None), P.text_depth + 1.0)
            for hole in poly.interiors:
                hp = [(x - P.text_letter_width / 2, y - P.text_height / 2)
                      for x, y in list(hole.coords)[:-1]]
                prism = prism - extrude(Polygon(*ccw(hp), align=None), P.text_depth + 1.0)
            # local glyph frame: x = CCW tangent, y = +Z, normal = radially outward, so the
            # glyph reads correctly from outside; the prism runs from R - depth outward
            a = math.radians(ang)
            r0 = R - P.text_depth
            pl = Plane(origin=(r0 * math.cos(a), r0 * math.sin(a), z_mid),
                       x_dir=(-math.sin(a), math.cos(a), 0),
                       z_dir=(math.cos(a), math.sin(a), 0))
            tools.append(pl.location * prism)
        s += P.text_letter_width + P.text_tracking
    return tools


# ======================================================================================
# PARTS
# ======================================================================================
def make_body(P: Params, length=None):
    """Main cartridge body: an open vented tube with an identical QuickLock socket at each end.
    Printed upright, either end down."""
    D = P.d()
    L = length or D["L_body"]
    Ro, Ri, Rs = D["R_o"], D["R_i"], D["R_s"]
    c, t, ch, mc = D["collar"], D["taper"], P.rim_chamfer, P.mouth_chamfer
    prof = [(Rs + mc, 0), (Ro - ch, 0), (Ro, ch), (Ro, L - ch), (Ro - ch, L), (Rs + mc, L),
            (Rs, L - mc), (Rs, L - c), (Ri, L - c - t), (Ri, c + t), (Rs, c), (Rs, mc)]
    body = rz_revolve(prof)

    tools = socket_cutter(P)
    tools += [flip_end(tl, L) for tl in tools]

    # vent slots: elongated hexagons (pointed ends at 45 deg, so no bridges anywhere)
    z0 = D["collar_total"] + P.vent_margin
    z1 = L - D["collar_total"] - P.vent_margin
    rows = P.vent_rows
    slot_len = (z1 - z0 - (rows - 1) * P.vent_row_gap) / rows
    w = P.vent_width
    tip = w / 2                                  # 45 deg point
    pitch = 360.0 / P.vent_per_row
    half_label = P.label_sector_deg / 2
    vent_count = 0
    slot_area = 0.0
    for row in range(rows):
        za = z0 + row * (slot_len + P.vent_row_gap)
        zb = za + slot_len
        hexa = [(-w / 2, za + tip), (0, za), (w / 2, za + tip), (w / 2, zb - tip), (0, zb),
                (-w / 2, zb - tip)]
        prism = Plane.YZ * Polygon(*hexa, align=None)            # in the YZ plane, extrude along X
        prism = Pos(Ri - 0.6, 0, 0) * extrude(prism, Ro - Ri + 1.2)
        for k in range(P.vent_per_row):
            ang = k * pitch + (pitch / 2 if row % 2 else 0)
            dl = (ang - P.label_angle_deg + 180) % 360 - 180
            if abs(dl) < half_label:
                continue
            tools.append(Rot(0, 0, ang) * prism)
            vent_count += 1
            slot_area += w * (slot_len - 2 * tip) + w * tip     # rectangle + two triangles
    tools += wordmark_cutters(P, (z0 + z1) / 2)
    body = cut_all(body, tools)
    body = as_part(body)
    body.label = "body"
    info = dict(length=L, vent_slots=vent_count, vent_slot_length=slot_len,
                vent_open_area_mm2=slot_area, vent_band=(z0, z1))
    return body, info


def make_cap(P: Params):
    """QuickLock end cap in the socket frame (seat at z=0, face at z=-cap_out).
    Printed face-down; nothing overhangs more than 45 deg."""
    D = P.d()
    Ro, Rn, Rp, Rpi, Rhi = D["R_o"], D["R_neck"], D["R_p"], D["R_pi"], D["R_hi"]
    Hc, Ln, Lp = D["cap_out"], D["neck_len"], D["plug_len"]
    zf = -Hc
    zfi = zf + P.face_thickness                  # inside of the face plate
    zcone = zfi + (Rhi - Rpi)                    # 45 deg funnel down to the plug bore
    bc, tc, pc = P.base_chamfer, P.head_top_chamfer, 0.5
    prof = [(0, zf), (Ro - bc, zf), (Ro, zf + bc), (Ro, -Ln - tc), (Ro - tc, -Ln), (Rn, -Ln),
            (Rn, 0), (Rp + P.plug_root_chamfer, 0), (Rp, P.plug_root_chamfer),
            (Rp, Lp - pc), (Rp - pc, Lp), (Rpi, Lp), (Rpi, zcone), (Rhi, zfi), (0, zfi)]
    cap = rz_revolve(prof)
    adds = [lug(P, 360.0 * k / P.lug_count) for k in range(P.lug_count)]
    cap = union_all([cap] + adds)

    tools = []
    # face vents: radial slots between the window boss and the head cavity
    w = P.face_slot_width
    ro, ri = P.face_slot_r_out, P.face_slot_r_in
    slot2d = [(ri, -w / 2), (ro - w / 2, -w / 2), (ro, 0), (ro - w / 2, w / 2), (ri, w / 2)]
    slot = xy_extrude(slot2d, zf - 1, zfi + 0.5)
    off = 180.0 / P.face_slot_count
    for k in range(P.face_slot_count):
        tools.append(Rot(0, 0, off + 360.0 * k / P.face_slot_count) * slot)
    # R6 twist-lock window: aperture through the lip; disc recess; ear pockets that run under
    # a 45-degree ledge (a boss on the inside of the face); notches let the ears in
    lip_t = P.face_thickness - P.window_seat_depth
    tools.append(Pos(0, 0, zf - 1 + (P.face_thickness + 2) / 2) * Cylinder(D["R_ap"], P.face_thickness + 2))
    wb, we, fit = P.window_body_r + P.window_fit, P.window_ear_r + P.window_fit, P.window_fit
    z_lip = zf + lip_t
    boss_top = zfi + (we - wb) + 0.6
    tools.append(Pos(0, 0, (z_lip + boss_top + 1) / 2) * Cylinder(wb, boss_top + 1 - z_lip))
    ea = P.window_ear_deg / 2 + math.degrees(fit / we) + 1.0
    zc0 = z_lip + P.window_thickness + 0.2 - (we - P.window_ear_r)   # ledge 0.2 above the ear tips
    pocket = [(wb - 0.5, z_lip), (we, z_lip), (we, zc0), (wb, zc0 + (we - wb)), (wb - 0.5, zc0 + (we - wb))]
    notch = [(wb - 0.5, z_lip), (we, z_lip), (we, boss_top + 1), (wb - 0.5, boss_top + 1)]
    win_tools = []
    for k in range(3):
        c0 = 120.0 * k
        win_tools.append(rz_revolve(pocket, P.window_turn_deg + 2 * ea, c0 - ea))
        win_tools.append(rz_revolve(notch, 2 * ea, c0 - ea))
    # grip flutes; the three over the lugs are deeper and act as index marks
    head_h = P.head_height
    for k in range(P.flute_count):
        ang = 360.0 * k / P.flute_count
        is_index = any(abs(((ang - 360.0 * j / P.lug_count - P.index_offset_deg) + 180) % 360 - 180) < 1e-6
                       for j in range(P.lug_count))
        dep = P.index_flute_depth if is_index else P.flute_depth
        rf = P.flute_radius
        fl = Pos(*polar(Ro + rf - dep, ang), zf + head_h / 2) * Cylinder(rf, head_h + 2)
        tools.append(fl)
    # the ledge boss is added before the window cuts so they can run through it
    boss = rz_revolve([(wb - 0.2, zfi - 0.5), (wb + 2.2, zfi - 0.5), (wb + 2.2, boss_top),
                       (wb - 0.2, boss_top)])
    cap = union_all([cap, boss])
    cap = cut_all(cap, tools + win_tools)
    cap = as_part(cap)
    cap.label = "cap"
    return cap


def _window_plan(P: Params, r_in=0.0):
    """Disc with three ears (plan view), as a solid of thickness 1 at z 0..1 (scaled later)."""
    parts = [rz_revolve([(r_in, 0), (P.window_body_r, 0), (P.window_body_r, 1), (r_in, 1)])]
    for k in range(3):
        c0 = 120.0 * k
        parts.append(xy_extrude(sector(P.window_body_r - 0.4, P.window_ear_r,
                                       c0 - P.window_ear_deg / 2, c0 + P.window_ear_deg / 2), 0, 1))
    return union_all(parts)


def make_window(P: Params):
    """R6 twist-lock window. Fit it from the inside of the cap: ears into the notches, push onto
    the lip, turn 60 deg clockwise (seen from inside) with a fingertip on the grip bar."""
    t = P.window_thickness
    disc = [rz_revolve([(0, 0), (P.window_body_r, 0), (P.window_body_r, t), (0, t)])]
    for k in range(3):
        c0 = 120.0 * k
        disc.append(xy_extrude(sector(P.window_body_r - 0.4, P.window_ear_r,
                                      c0 - P.window_ear_deg / 2, c0 + P.window_ear_deg / 2), 0, t))
    # grip bar across the inner face (printed on top), with 45 deg ends
    gh, gw = P.window_grip_h, 1.2
    L = 2 * (P.window_body_r - 1.2)
    bar = Pos(0, 0, t) * extrude(Polygon(*ccw([(-L / 2, -gw / 2), (L / 2, -gw / 2), (L / 2 - 0.01, gw / 2),
                                                (-L / 2 + 0.01, gw / 2)]), align=None), gh)
    win = as_part(union_all(disc + [Rot(0, 0, 60) * bar]))
    win.label = "window"
    return win


def make_film_retainer(P: Params):
    """Optional film window: if no clear filament, cut a Ø16.6 mm disc from clear PET/PC sheet
    (blister packaging), lay it on the lip, then twist this carrier ring in on top of it."""
    D = P.d()
    t = P.window_thickness - P.film_thickness
    parts = [rz_revolve([(D["R_ap"], 0), (P.window_body_r, 0), (P.window_body_r, t), (D["R_ap"], t)])]
    for k in range(3):
        c0 = 120.0 * k
        parts.append(xy_extrude(sector(P.window_body_r - 0.4, P.window_ear_r,
                                       c0 - P.window_ear_deg / 2, c0 + P.window_ear_deg / 2), 0, t))
        # two grip nubs to turn it
        parts.append(Pos(*polar((D["R_ap"] + P.window_body_r) / 2, c0 + 60), t + 0.6) * Cylinder(0.6, 1.2))
    ring = as_part(union_all(parts))
    ring.label = "film_retainer"
    return ring


def make_coupler(P: Params):
    """Expansion coupler: a double-ended plug that joins two bodies rim-to-rim."""
    D = P.d()
    Rp, Rpi, Lp = D["R_p"], D["R_pi"], D["plug_len"]
    pc = 0.5
    prof = [(Rpi, -Lp), (Rp - pc, -Lp), (Rp, -Lp + pc), (Rp, Lp - pc), (Rp - pc, Lp), (Rpi, Lp)]
    tube = rz_revolve(prof)
    lugs = [lug(P, 360.0 * k / P.lug_count) for k in range(P.lug_count)]
    lugs += [Rot(180, 0, 0) * l for l in lugs]
    c = as_part(union_all([tube] + lugs))
    c.label = "coupler"
    return c


def adapter_geometry(P: Params, bore: float):
    D = P.d()
    Ro = D["R_o"]
    R_t = bore / 2 + P.preload                  # free (undeflected) contact radius
    R_bo = R_t - P.bump_height
    R_bi = R_bo - P.arm_thickness
    return dict(R_t=R_t, R_bo=R_bo, R_bi=R_bi, gap=R_bi - Ro,
                R_mid=(R_bo + R_bi) / 2)


def make_adapter(P: Params, bore: float):
    """Spool centring adapter: a flush base ring trapped on the cap neck, with three
    cantilever spring arms that take up spool-to-spool bore variation.
    bore=0 makes the plain flush ring (no arms)."""
    D = P.d()
    Ro, t = D["R_o"], P.adapter_thickness
    Ra = D["R_neck"] + P.adapter_radial_clear
    ring = rz_revolve([(Ra, 0), (Ro, 0), (Ro, t), (Ra, t)])
    if bore <= 0:
        ring = rz_revolve([(Ra, 0), (Ro - 0.4, 0), (Ro, 0.4), (Ro, t - 0.4), (Ro - 0.4, t), (Ra, t)])
        ring.label = "adapter_flush"
        return ring
    g = adapter_geometry(P, bore)
    if g["gap"] < P.arm_gap_min - 1e-6:
        raise ValueError(f"bore {bore} too small for spring arms (gap {g['gap']:.2f} mm); "
                         "use the flush ring or a larger body clearance")
    parts = [ring]
    deg = lambda L, r: math.degrees(L / r)
    for k in range(P.adapter_arms):
        base = 360.0 * k / P.adapter_arms + 30.0
        a_root = deg(P.arm_root, g["R_mid"])
        a_arm = deg(P.arm_length, g["R_mid"])
        # root spoke and arm
        parts.append(xy_extrude(sector(Ro - 0.5, g["R_bo"], base, base + a_root), 0, t))
        parts.append(xy_extrude(sector(g["R_bi"], g["R_bo"], base + a_root - 0.5,
                                       base + a_root + a_arm), 0, t))
        # contact bump at the free end (cosine profile)
        a_b = deg(P.bump_width, g["R_bo"])
        tb = base + a_root + a_arm - a_b / 2
        pts = []
        n = 20
        for i in range(n + 1):
            u = -1 + 2 * i / n
            r = g["R_bo"] + P.bump_height * (0.5 + 0.5 * math.cos(math.pi * u))
            pts.append(polar(r, tb + u * a_b / 2))
        pts += [polar(g["R_bo"] - 0.3, tb + a_b / 2), polar(g["R_bo"] - 0.3, tb - a_b / 2)]
        parts.append(xy_extrude(pts, 0, t))
        # overload stop: a pad on the base ring under the arm tip, so the arm can never be
        # forced more than arm_gap_min inward (protects it if the wrong size is forced in)
        r_pad = g["R_bi"] - P.arm_gap_min
        if r_pad > Ro + 0.2:
            parts.append(xy_extrude(sector(Ro - 0.5, r_pad, tb - a_b / 2, tb + a_b / 2), 0, t))
    ad = union_all(parts)
    # lead-in chamfer on the contact bumps (top and bottom), done as a revolved envelope
    # R7: lead-in deeper than the full spring travel (P001: 0.45 mm < 0.55-1.0 mm travel, so the
    # bump's square shoulder met the bore mouth). 35 deg from the axis on both faces.
    c = P.bump_leadin
    ca = c / math.tan(math.radians(P.bump_leadin_deg))
    if 2 * ca > t - 0.2:
        raise ValueError("adapter too thin for the requested lead-in")
    Rt = g["R_t"]
    k = 0.2 / c * ca
    env = rz_revolve([(0, -0.01), (Rt - c, -0.01), (Rt + 0.2, ca + k), (Rt + 0.2, t - ca - k),
                      (Rt - c, t + 0.01), (0, t + 0.01)])
    ad = as_part(ad & env)
    ad.label = f"adapter_{bore:g}"
    return ad


def _dimples(P: Params, n, z):
    D = P.d()
    out = []
    for i in range(n):
        ang = 200 + 8 * (i - (n - 1) / 2)
        out.append(Pos(*polar(D["R_o"], ang), z) * (Rot(0, 90, ang) * Cylinder(0.75, 1.0)))
    return out


def make_fit_gauge(P: Params, detent=None, dimples=1):
    """Single-socket detent tuning ring (R8). `detent` overrides detent_interference.
    Dimples on the outside identify it: 1 = softer, 3 = firmer (the double gauge has 2)."""
    D = P.d()
    Ro, Rs = D["R_o"], D["R_s"]
    H = D["collar"] + 1.5
    prof = [(Rs + P.mouth_chamfer, 0), (Ro - P.rim_chamfer, 0), (Ro, P.rim_chamfer), (Ro, H),
            (Rs, H), (Rs, P.mouth_chamfer)]
    g = cut_all(rz_revolve(prof), socket_cutter(P, detent) + _dimples(P, dimples, H - 0.9))
    g = as_part(g)
    g.label = "fit_gauge"
    return g


def make_fit_gauge_double(P: Params):
    """R8 main fit gauge: a short body with BOTH sockets (one prints mouth-down, one mouth-up,
    exactly as on the real body) and one row of real vent slots for a bead-escape test."""
    D = P.d()
    Ro, Ri, Rs = D["R_o"], D["R_i"], D["R_s"]
    c, t, ch, mc = D["collar"], D["taper"], P.rim_chamfer, P.mouth_chamfer
    vent_len = 4.0
    L = 2 * D["collar_total"] + vent_len + 2 * P.vent_margin
    prof = [(Rs + mc, 0), (Ro - ch, 0), (Ro, ch), (Ro, L - ch), (Ro - ch, L), (Rs + mc, L),
            (Rs, L - mc), (Rs, L - c), (Ri, L - c - t), (Ri, c + t), (Rs, c), (Rs, mc)]
    body = rz_revolve(prof)
    tools = socket_cutter(P)
    tools += [flip_end(tl, L) for tl in tools]
    w = P.vent_width
    za = D["collar_total"] + P.vent_margin
    zb = za + vent_len
    hexa = [(-w / 2, za + w / 2), (0, za), (w / 2, za + w / 2), (w / 2, zb - w / 2), (0, zb), (-w / 2, zb - w / 2)]
    prism = Pos(Ri - 0.6, 0, 0) * extrude(Plane.YZ * Polygon(*hexa, align=None), Ro - Ri + 1.2)
    for k in range(P.vent_per_row):
        tools.append(Rot(0, 0, k * 360.0 / P.vent_per_row + 4.5) * prism)
    tools += _dimples(P, 2, L - 3.0)
    g = as_part(cut_all(body, tools))
    g.label = "fit_gauge_double"
    return g, L


# ======================================================================================
# VALIDATION (real boolean geometry, not renders)
# ======================================================================================
def vol(shape):
    try:
        return max(0.0, shape.volume) if shape is not None else 0.0
    except Exception:
        return 0.0


def inter_vol(a, b):
    try:
        r = a & b
        return sum(s.volume for s in r.solids()) if r is not None else 0.0
    except Exception as e:  # pragma: no cover
        return float("nan")


def ring_point_load_compliance(R, t, b, n, E):
    """Radial deflection per unit load at each of n equal inward point loads on a thin free
    ring (Castigliano, bending only). M(phi) = (F R / 2)(cos phi / sin a - 1/a), a = pi/n."""
    a = math.pi / n
    I = b * t ** 3 / 12
    N = 2000
    s = 0.0
    for i in range(N):
        ph = (i + 0.5) * a / N
        m = 0.5 * (math.cos(ph) / math.sin(a) - 1 / a)
        s += m * m * a / N
    return 2 * R ** 3 * s / (E * I)     # mm per N


def validate(P: Params, parts, quick=False, log=print):
    D = P.d()
    out = {}
    body, cap, coupler, window = parts["body"], parts["cap"], parts["coupler"], parts["window"]
    L = D["L_body"]
    # clip the body to the bottom socket region for fast fit sweeps
    region = Pos(0, 0, 6) * Cylinder(D["R_o"] + 2, 12 + 0.01)
    sock = body & region
    plug_region = Pos(0, 0, 5) * Cylinder(D["R_o"] + 2, 10)
    capp = cap & plug_region                       # neck, plug and lugs
    res = {}

    # 1) assembled, unlocked and locked: zero interference
    res["cap_unlocked_seated"] = inter_vol(sock, capp)
    res["cap_locked_seated"] = inter_vol(sock, Rot(0, 0, P.travel_deg) * capp)
    # 2) insertion path at the unlocked angle
    ins = []
    for dz in [-9, -7, -5, -3, -2, -1, -0.5]:
        ins.append((dz, inter_vol(sock, Pos(0, 0, dz) * capp)))
    res["insertion_path"] = ins
    # 3) rotation sweep, seated
    sweep = []
    if not quick:
        angles = [0, 10, 20, 30, 40, 50, 60, 65, 70, 72.5, 75, 77.5, 80, 82.5, 85, 87.5, 90, 91.0]
        for a in angles:
            sweep.append((a, inter_vol(sock, Rot(0, 0, a) * capp)))
        # over-rotation: the hard stop
        for a in [P.travel_deg + D["ang_stop"] + 1.0, P.travel_deg + 4.0]:
            sweep.append((a, inter_vol(sock, Rot(0, 0, a) * capp)))
    res["rotation_sweep"] = sweep
    # 4) pull test: locked cap pulled outward must hit the lip; unlocked must come free
    pulls = []
    for dz in [-(P.bearing_play - 0.05), -(P.bearing_play + 0.15), -0.8]:
        pulls.append((dz, inter_vol(sock, Pos(0, 0, dz) * (Rot(0, 0, P.travel_deg) * capp))))
    res["pull_locked"] = pulls
    res["pull_unlocked_minus0p8"] = inter_vol(sock, Pos(0, 0, -0.8) * capp)

    # 5) top end uses the same cap turned over
    top_region = Pos(0, 0, L - 6) * Cylinder(D["R_o"] + 2, 12.01)
    sock_top = body & top_region
    cap_top = flip_end(Rot(0, 0, P.travel_deg) * capp, L)
    res["top_cap_locked_seated"] = inter_vol(sock_top, cap_top)
    res["top_cap_pull_0p4"] = inter_vol(sock_top, Pos(0, 0, P.bearing_play + 0.2) * cap_top)   # name kept for the report

    # 6) adapters on the neck, window in its seat
    ad = parts["adapters"][P.spool_bore] if P.spool_bore in parts["adapters"] else \
        next(iter(parts["adapters"].values()))
    ad_pl = Pos(0, 0, -D["neck_len"] + P.adapter_axial_play / 2) * ad
    res["adapter_vs_cap"] = inter_vol(cap, ad_pl)
    res["adapter_vs_body"] = inter_vol(sock, ad_pl)
    lip_t = P.face_thickness - P.window_seat_depth
    win_pl = Pos(0, 0, -D["cap_out"] + lip_t) * window
    tw = P.window_turn_deg
    res["window_unlocked_seated"] = inter_vol(cap, win_pl)
    res["window_install_path"] = [(dz, inter_vol(cap, Pos(0, 0, dz) * win_pl)) for dz in (0.5, 1.0, 2.0, 3.0)]
    res["window_turn_sweep"] = [(a, inter_vol(cap, Rot(0, 0, a) * win_pl)) for a in (0, 15, 30, 45, tw)]
    wl = Rot(0, 0, tw) * win_pl
    res["window_locked_push_in_0p5"] = inter_vol(cap, Pos(0, 0, 0.5) * wl)
    res["window_locked_push_out_0p2"] = inter_vol(cap, Pos(0, 0, -0.2) * wl)
    res["window_unlocked_lift_out_3"] = inter_vol(cap, Pos(0, 0, 3.0) * win_pl)
    rib_expected = 0.0
    # 7) coupler between two bodies, both locked
    sock2 = flip_end(sock, 0.0)                            # a second body end, rim at z=0, facing -z
    cpl_locked = Rot(0, 0, P.travel_deg) * coupler
    res["coupler_vs_bodyA"] = inter_vol(sock, cpl_locked)
    # body B faces body A rim-to-rim; it is turned 2*travel relative to A once both joints lock
    res["coupler_vs_bodyB"] = inter_vol(Rot(0, 0, 2 * P.travel_deg) * sock2, cpl_locked)
    out["fits"] = res

    # mechanics estimates
    E = 2000.0   # MPa, PETG (printed, conservative)
    Rm = D["R_p"] - P.plug_wall / 2
    comp = ring_point_load_compliance(Rm, P.plug_wall, D["plug_len"], P.lug_count, E)
    out["plug_ring_compliance_mm_per_N_free"] = comp
    # R2: detent spring = tongue (cantilever, load at the bump) in series with the plug ring.
    # Plug ring stiffness from the 3D FEA (analysis/plug_fea.py): 570 N/mm per lug, anchored.
    k_plug = 570.0
    zb_ = D["z_c"] - (D["tip_half"] + P.bearing_play + (D["R_lt"] - D["R_g"]) * D["tanf"])
    zi_ = D["z_c"] + (D["tip_half"] + P.inner_play + (D["R_lt"] - D["R_g"]) * D["tanf"])
    h_t = zi_ - zb_
    t_t = min(P.tongue_thickness, D["R_o"] - D["R_g"])
    r_mid = D["R_g"] + t_t / 2
    tb = P.travel_deg - D["lug_half"] - 0.3 - P.detent_halfwidth_deg
    a_arm = math.radians(tb - P.tongue_start_deg) * r_mid
    I_t = h_t * t_t ** 3 / 12
    k_t = 3 * E * I_t / a_arm ** 3
    k_eff = 1 / (1 / k_t + 1 / k_plug)
    out["tongue"] = dict(height=h_t, thickness=t_t, load_arm_mm=a_arm,
                         k_tongue_N_per_mm=k_t, k_plug_fea_N_per_mm=k_plug, k_eff_N_per_mm=k_eff,
                         strain_at_nominal_pct=100 * 3 * t_t * (P.detent_interference + 0.1) / (2 * a_arm ** 2))
    comp = 1 / k_eff
    F_det = P.detent_interference / comp
    out["detent_force_per_lug_N_free_ring"] = F_det
    mu = 0.25
    ramp = math.atan(math.pi * (P.lug_tip_clear + P.detent_interference) /
                     (2 * math.radians(P.detent_halfwidth_deg) * D["R_g"]))
    out["detent_ramp_deg"] = math.degrees(ramp)
    T = P.lug_count * F_det * math.tan(ramp + math.atan(mu)) * D["R_g"] / 1000
    out["detent_torque_Nm_free_ring"] = T
    # pull-off with 45 deg flanks: plug must collapse inward by the lug engagement
    engage = D["R_lt"] - D["R_s"] - 0.0
    Fr = engage * k_plug          # lugs bear on the rigid lip: the plug ring (FEA) must collapse
    tf = math.tan(math.radians(P.flank_deg))
    Fa = P.lug_count * Fr * (1 + mu * tf) / (tf - mu) if tf > mu else float("inf")
    out["lug_radial_engagement_mm"] = engage
    out["pull_off_N_free_ring_lower_bound"] = Fa
    # adapter arm spring
    arms = {}
    for bore in P.adapter_sizes:
        g = adapter_geometry(P, bore)
        I = P.adapter_thickness * P.arm_thickness ** 3 / 12
        Lb = P.arm_length + P.bump_width / 2
        k = 3 * E * I / Lb ** 3
        d_max = min(P.arm_gap_min, g["gap"])          # overload stop (or the base ring itself)
        d_min = 0.15                                   # still gripping
        strain = lambda dd: 100 * 3 * P.arm_thickness * dd / (2 * Lb ** 2)
        arms[bore] = dict(
            free_contact_dia=2 * g["R_t"], k_N_per_mm=k, F_nominal_N=k * P.preload,
            F_max_N=k * d_max, strain_nominal_pct=strain(P.preload), strain_max_pct=strain(d_max),
            fits_bores=(round(bore + 2 * (P.preload - d_max), 2), round(bore + 2 * (P.preload - d_min), 2)),
            axial_retention_N=2 * P.adapter_arms * k * P.preload * 0.25,
            gap_under_arm=g["gap"])
    out["adapter_arms"] = arms
    return out


def mesh_checks(stl_dir: Path, overhang_deg=45.0):
    """Printability checks on the exported STLs, in print orientation (as exported, z up).
    - watertight / single body
    - overhang: downward faces steeper than `overhang_deg` from vertical, not on the bed
    - local wall thickness: rays cast inward from random surface points (percentiles)"""
    try:
        import numpy as np
        import trimesh
    except ImportError:
        return {"skipped": "trimesh not installed"}
    out = {}
    lim = -math.cos(math.radians(90 - overhang_deg)) - 0.02   # n_z below this = overhang
    rng = np.random.default_rng(1)
    for f in sorted(stl_dir.glob("*.stl")):
        m = trimesh.load(f)
        n = m.face_normals
        cz = m.triangles_center[:, 2]
        bad = (n[:, 2] < lim) & (cz > 0.05)
        area = float(m.area_faces[bad].sum())
        # size of the largest connected overhang patch
        largest = 0.0
        widest = 0.0
        bridges = []
        if bad.any():
            sub = m.submesh([np.nonzero(bad)[0]], append=True)
            comps = sub.split(only_watertight=False) or [sub]
            loose = []
            for c in comps:
                v = c.vertices
                rr = np.hypot(v[:, 0], v[:, 1])
                ang = np.unwrap(np.sort(np.arctan2(v[:, 1], v[:, 0])))
                arc = float((ang.max() - ang.min()) * rr.mean())
                # a bridge: a flat ceiling across a wall (radial span <= 2.6 mm) spanning <= 16 mm
                # between two supports, like the tongue slits; everything else is an overhang
                if float(rr.max() - rr.min()) <= 2.6 and float(c.area) > 2.0 and arc <= 16.0:
                    bridges.append(dict(span_mm=round(arc, 1), depth_mm=round(float(rr.max() - rr.min()), 2)))
                else:
                    loose.append(c)
            if loose:
                largest = max(float(c.area) for c in loose)
                widest = max(float(min(c.extents[:2])) for c in loose)
        pts, fi = trimesh.sample.sample_surface(m, 6000, seed=1)
        dirs = -m.face_normals[fi]
        locs, idx_ray, _ = m.ray.intersects_location(pts + dirs * 1e-3, dirs, multiple_hits=False)
        d = np.linalg.norm(locs - pts[idx_ray], axis=1) if len(locs) else np.array([0.0])
        out[f.stem] = dict(watertight=bool(m.is_watertight), bodies=len(m.split(only_watertight=False)),
                           volume_cm3=float(m.volume) / 1000, overhang_area_mm2=area,
                           largest_overhang_patch_mm2=largest, overhang_patch_min_extent_mm=widest,
                           bridges=bridges,
                           wall_p1=float(np.percentile(d, 1)), wall_p5=float(np.percentile(d, 5)),
                           wall_median=float(np.median(d)))
    return out


# ======================================================================================
# volumes, desiccant, airflow, print estimates
# ======================================================================================
def capacity(P: Params, parts, body_info):
    D = P.d()
    L = D["L_body"]
    zA = -D["cap_out"] + P.face_thickness
    zB = L + D["cap_out"] - P.face_thickness
    cyl = Pos(0, 0, (zA + zB) / 2) * Cylinder(D["R_i"] - 0.01, zB - zA)
    capA = parts["cap"]
    capB = flip_end(parts["cap"], L)
    lip_t = P.face_thickness - P.window_seat_depth
    winA = Pos(0, 0, -D["cap_out"] + lip_t) * parts["window"]
    winB = flip_end(winA, L)
    cav = cyl - parts["body"] - capA - capB - winA - winB
    total = sum(s.volume for s in cav.solids())
    fill_line = L - D["collar_total"]
    fill = cav & (Pos(0, 0, (zA + fill_line) / 2) * Cylinder(D["R_o"] + 5, fill_line - zA))
    fill_v = sum(s.volume for s in fill.solids())
    # face vent area (both caps), slot area of the body
    face_slot_area = P.face_slot_count * P.face_slot_width * (P.face_slot_r_out - P.face_slot_r_in
                                                              - P.face_slot_width / 4)
    return dict(cavity_ml=total / 1000, fill_to_line_ml=fill_v / 1000, fill_line_z=fill_line,
                body_vent_area_mm2=body_info["vent_open_area_mm2"],
                face_vent_area_mm2=2 * face_slot_area,
                window_view_area_mm2=2 * math.pi * D["R_ap"] ** 2)


def print_estimates(volume_mm3, layer_area_hint=None):
    """Rough PETG estimate from solid volume. NOT slicer output."""
    rho = 1.27
    grams = volume_mm3 / 1000 * rho * 1.03          # 3% for seams/flow
    minutes = 3.0 + volume_mm3 / 8.0 / 60.0 * 1.6   # ~8 mm3/s effective, x1.6 small-feature slowdown
    return grams, minutes


# ======================================================================================
# export
# ======================================================================================
COLORS = {"charcoal": (0.16, 0.17, 0.19), "orange": (1.0, 0.42, 0.05), "clear": (0.85, 0.92, 0.95)}


def export_all(P: Params, parts, outdir: Path, log=print):
    stl_dir, step_dir, mf_dir = outdir / "stl", outdir / "step", outdir / "3mf"
    for d in (stl_dir, step_dir, mf_dir):
        d.mkdir(parents=True, exist_ok=True)
    D = P.d()
    # print orientation = as built for every part (body: socket frame; cap: face down;
    # adapters/window: flat; coupler: upright). Just drop each onto z=0.
    def on_bed(s):
        bb = s.bounding_box()
        return Pos(-0 * bb.min.X, 0, -bb.min.Z) * s
    items = {
        "DD011_A_body": parts["body"],
        "DD011_B_cap_x2": parts["cap"],
        "DD011_C_window_x2_clear": parts["window"],
        "DD011_C2_film_window_retainer_x2_optional": parts["film_retainer"],
        "DD011_E_coupler_expansion": parts["coupler"],
        "DD011_T1_fit_gauge_double_2dots": parts["fit_gauge"],
        **{f"DD011_T2_detent_tuning_{'softer_1dot' if d < 0 else 'firmer_3dots'}": g
           for d, g in parts["fit_tune"].items()},
        "DD011_D_adapter_flush_x2": parts["adapter_flush"],
    }
    for bore, ad in parts["adapters"].items():
        items[f"DD011_D_adapter_{bore:g}mm_x2"] = ad
    written = {}
    for name, shape in items.items():
        s = on_bed(shape)
        export_stl(s, str(stl_dir / f"{name}.stl"), tolerance=P.stl_tolerance,
                   angular_tolerance=P.stl_angular)
        export_step(s, str(step_dir / f"{name}.step"))
        written[name] = s
    # assembled STEP (locked, default adapter) for CAD import
    asm = assembly(P, parts, explode=0.0)
    export_step(Compound(children=[s for s, _, _ in asm]), str(step_dir / "DD011_assembly_locked.step"))

    # plates (plain 3MF; pick your printer/filament profiles on import in Bambu Studio)
    def plate(fname, entries):
        m = Mesher()
        for shape, color, x, y in entries:
            s = on_bed(shape)
            bb = s.bounding_box()
            s = Pos(x - (bb.min.X + bb.max.X) / 2, y - (bb.min.Y + bb.max.Y) / 2, 0) * s
            s.color = Color(*color)
            s.label = f"part{len(entries)}_{x}_{y}"
            m.add_shape(s, linear_deflection=P.stl_tolerance, angular_deflection=P.stl_angular)
        m.write(str(mf_dir / fname))
    ch, orc, clr = COLORS["charcoal"], COLORS["orange"], COLORS["clear"]
    cap = parts["cap"]
    plate("DD011_plate1_charcoal_body_caps.3mf",
          [(parts["body"], ch, 0, 0), (cap, ch, 60, 0), (cap, ch, -60, 0)])
    default_ad = parts["adapters"].get(P.spool_bore)
    plate("DD011_plate2_orange_adapters_%gmm.3mf" % P.spool_bore,
          [(default_ad, orc, -40, 0), (default_ad, orc, 40, 0)])
    plate("DD011_plate3_clear_windows.3mf",
          [(parts["window"], clr, -15, 0), (parts["window"], clr, 15, 0)])
    plate("DD011_plate4_fit_test.3mf",
          [(parts["fit_gauge"], ch, -55, 0), (cap, ch, 0, 0)]
          + [(g, ch, 55, -27 + 54 * i) for i, g in enumerate(parts["fit_tune"].values())]
          + [(parts["window"], clr, -55, 45), (default_ad, orc, 0, 55)])
    sizes = list(parts["adapters"].items())
    plate("DD011_plate5_orange_adapter_set.3mf",
          [(ad, orc, -100 + 70 * (i % 3), -35 + 70 * (i // 3)) for i, (b, ad) in enumerate(sizes)])
    return written


def assembly(P: Params, parts, explode=0.0, angle=None, bore=None, extra_module=False):
    """List of (shape, color_name, label) in the global frame. explode spreads parts along Z."""
    D = P.d()
    L = D["L_body"]
    a = P.travel_deg if angle is None else angle
    bore = P.spool_bore if bore is None else bore
    ad = parts["adapters"].get(bore, parts["adapter_flush"])
    lip_t = P.face_thickness - P.window_seat_depth
    e = explode
    win = Rot(0, 0, P.window_turn_deg) * (Pos(0, 0, -D["cap_out"] + lip_t) * parts["window"])
    adp = Pos(0, 0, -D["neck_len"] + P.adapter_axial_play / 2) * ad
    out = []
    # bottom end (socket frame == global)
    out.append((Pos(0, 0, -2.2 * e) * (Rot(0, 0, a) * parts["cap"]), "charcoal", "cap"))
    out.append((Pos(0, 0, -3.4 * e) * (Rot(0, 0, a) * win), "clear", "window"))
    out.append((Pos(0, 0, -1.1 * e) * adp, "orange", "adapter"))
    out.append((parts["body"], "charcoal", "body"))
    top = L
    if extra_module:
        out.append((Pos(0, 0, L + 0.6 * e) * flip_end(Rot(0, 0, a) * parts["coupler"], 0),
                    "charcoal", "coupler"))
        out.append((Pos(0, 0, L + 1.2 * e) * (Rot(0, 0, -2 * a) * parts["body"]), "charcoal", "body2"))
        top = 2 * L
        e_off = 1.2 * e
    else:
        e_off = 0
    out.append((Pos(0, 0, e_off + 2.2 * e) * flip_end(Rot(0, 0, a) * parts["cap"], top), "charcoal", "cap"))
    out.append((Pos(0, 0, e_off + 3.4 * e) * flip_end(Rot(0, 0, a) * win, top), "clear", "window"))
    out.append((Pos(0, 0, e_off + 1.1 * e) * flip_end(adp, top), "orange", "adapter"))
    return out


def build_parts(P: Params, log=print, sizes=None):
    t0 = time.time()
    parts = {}
    parts["body"], parts["body_info"] = make_body(P)
    log(f"  body        {time.time() - t0:5.1f}s")
    parts["cap"] = make_cap(P)
    log(f"  cap         {time.time() - t0:5.1f}s")
    parts["window"] = make_window(P)
    parts["film_retainer"] = make_film_retainer(P)
    parts["coupler"] = make_coupler(P)
    parts["fit_gauge"], parts["fit_gauge_len"] = make_fit_gauge_double(P)
    parts["fit_tune"] = {d: make_fit_gauge(P, P.detent_interference + d, 1 if d < 0 else 3)
                         for d in P.detent_tuning}
    parts["adapter_flush"] = make_adapter(P, 0)
    parts["adapters"] = {}
    for b in (sizes or P.adapter_sizes):
        try:
            parts["adapters"][b] = make_adapter(P, b)
        except ValueError as e:
            log(f"  SKIPPED adapter {b:g} mm: {e}")
    log(f"  all parts   {time.time() - t0:5.1f}s")
    return parts


def parse_overrides(P: Params, sets, json_path):
    over = {}
    if json_path:
        over.update(json.loads(Path(json_path).read_text()))
    for s in sets or []:
        k, v = s.split("=", 1)
        over[k.strip()] = json.loads(v) if v.strip()[0] in "[{\"" else v
    fields = {f.name: f for f in dataclasses.fields(P)}
    for k, v in over.items():
        if k not in fields:
            sys.exit(f"unknown parameter {k!r}")
        cur = getattr(P, k)
        if cur is None:
            cur = 0.0
        if isinstance(cur, bool):
            v = str(v).lower() in ("1", "true", "yes")
        elif isinstance(cur, int):
            v = int(v)
        elif isinstance(cur, float):
            v = float(v)
        elif isinstance(cur, tuple):
            v = tuple(float(x) for x in (v if isinstance(v, list) else str(v).split(",")))
        setattr(P, k, v)
    if P.spool_bore not in P.adapter_sizes:
        P.adapter_sizes = tuple(sorted(set(P.adapter_sizes) | {P.spool_bore}))
    return P


def write_report_md(P: Params, report, path: Path):
    """Human-readable validation report with explicit pass criteria."""
    D = P.d()
    f = report["validation"]["fits"]
    v = report["validation"]
    lines = ["# DRYDOCK V1.1: validation report (generated by drydock.py)", "",
             "Every number here is computed from the CAD geometry by this run. Fit checks are "
             "boolean intersections of the real B-rep solids (volume of overlap in mm³). "
             "Force numbers are hand-calculation estimates, not test results. "
             "**Nothing here replaces a physical print-and-fit test.**", ""]
    eps = 1e-3
    checks = []
    def chk(name, ok, detail):
        checks.append((name, "PASS" if ok else "**FAIL**", detail))
    chk("Cap seats unlocked with no interference", f["cap_unlocked_seated"] < eps, f"{f['cap_unlocked_seated']:.4f} mm³")
    chk("Cap locked (turned %g°) with no interference" % P.travel_deg, f["cap_locked_seated"] < eps, f"{f['cap_locked_seated']:.4f} mm³")
    chk("Straight insertion path is clear", all(x < eps for _, x in f["insertion_path"]),
        ", ".join(f"{dz:g} mm: {x:.3f}" for dz, x in f["insertion_path"]))
    sw = f["rotation_sweep"]
    if sw:
        free = [x for a, x in sw if a <= 65]
        det = [x for a, x in sw if 68 <= a <= 86]
        pocket = [x for a, x in sw if 87.4 <= a <= P.travel_deg + 1e-6]
        stop = [x for a, x in sw if a > P.travel_deg + D["ang_stop"] + 0.5]
        chk("Free rotation 0–65°", all(x < eps for x in free), "max %.4f mm³" % max(free))
        chk("Detent bump engages before lock (deliberate interference)", max(det) > 0.1,
            "peak %.2f mm³ overlap = %.2f mm radial plug flex" % (max(det), P.detent_interference))
        chk("Locked pocket is clear (lug sits between bump and stop)", all(x < eps for x in pocket),
            "max %.4f mm³" % max(pocket))
        chk("Hard stop prevents over-rotation", all(x > 0.5 for x in stop),
            ", ".join(f"{a:.1f}°: {x:.2f} mm³" for a, x in sw if a > P.travel_deg + D['ang_stop'] + 0.5))
    pl = f["pull_locked"]
    chk("Locked cap: free within the designed axial play", pl[0][1] < eps, f"lift {-pl[0][0]:.2f} mm: {pl[0][1]:.4f} mm³")
    chk("Locked cap: lug bears on the lip when pulled", all(x > 0.5 for _, x in pl[1:]),
        ", ".join(f"lift {-dz:.2f} mm: {x:.2f} mm³" for dz, x in pl[1:]))
    chk("Unlocked cap pulls straight out", f["pull_unlocked_minus0p8"] < eps, f"{f['pull_unlocked_minus0p8']:.4f} mm³")
    chk("Same cap locks on the second (rotated) end", f["top_cap_locked_seated"] < eps and f["top_cap_pull_0p4"] > 0.5,
        f"seated {f['top_cap_locked_seated']:.4f}, pulled {f['top_cap_pull_0p4']:.2f} mm³")
    chk("Adapter clears the cap neck and body rim", f["adapter_vs_cap"] < eps and f["adapter_vs_body"] < eps,
        f"{f['adapter_vs_cap']:.4f} / {f['adapter_vs_body']:.4f} mm³")
    chk("Window drops onto its seat from inside (ears through the notches)",
        f["window_unlocked_seated"] < eps and all(x < eps for _, x in f["window_install_path"]),
        ", ".join(f"+{dz:g} mm: {x:.3f}" for dz, x in f["window_install_path"]))
    chk("Window turns %g° freely to lock" % P.window_turn_deg, all(x < eps for _, x in f["window_turn_sweep"]),
        ", ".join(f"{a:g}°: {x:.3f}" for a, x in f["window_turn_sweep"]))
    chk("Locked window cannot be pushed into the cartridge", f["window_locked_push_in_0p5"] > 0.2,
        f"pushed 0.5 mm inward: {f['window_locked_push_in_0p5']:.2f} mm³ (ears hit the ledge)")
    chk("Locked window cannot be pushed out of the face", f["window_locked_push_out_0p2"] > 0.2,
        f"pushed 0.2 mm outward: {f['window_locked_push_out_0p2']:.2f} mm³ (disc hits the lip)")
    chk("Unlocked window lifts out (replaceable)", f["window_unlocked_lift_out_3"] < eps,
        f"{f['window_unlocked_lift_out_3']:.3f} mm³")
    chk("Expansion coupler locks into both bodies", f["coupler_vs_bodyA"] < eps and f["coupler_vs_bodyB"] < eps,
        f"{f['coupler_vs_bodyA']:.4f} / {f['coupler_vs_bodyB']:.4f} mm³")
    mc = report.get("mesh_checks", {})
    if mc:
        chk("Every exported STL is watertight and one body",
            all(m["watertight"] and m["bodies"] == 1 for m in mc.values()), f"{len(mc)} files")
        worst = max(mc.values(), key=lambda m: m["largest_overhang_patch_mm2"])
        chk("No unsupported overhang patch > 2 mm² (45° rule, print orientation)",
            all(m["largest_overhang_patch_mm2"] < 2.0 for m in mc.values()),
            "largest patch %.2f mm² (engraved-letter ceilings, 0.45 mm deep)" % worst["largest_overhang_patch_mm2"])
        nb = [(n, b) for n, m in mc.items() for b in m.get("bridges", [])]
        if nb:
            chk("Bridges (flat ceilings supported at both ends) span ≤ 16 mm", all(b["span_mm"] <= 16 for _, b in nb),
                "%d tongue-slit ceilings, longest %.1f mm span, %.2f mm deep" % (
                    len(nb), max(b["span_mm"] for _, b in nb), max(b["depth_mm"] for _, b in nb)))
    lines += ["## Pass/fail summary", "", "| Check | Result | Measured |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in checks]
    lines += ["", "## Rotation sweep (cap vs body socket, overlap in mm³)", "",
              "| angle ° | " + " | ".join(f"{a:g}" for a, _ in sw) + " |",
              "|---|" + "---|" * len(sw),
              "| overlap | " + " | ".join(f"{x:.2f}" for _, x in sw) + " |", "",
              "0–65°: free. 70–85°: the plug flexes over the detent bump (felt as a firm spot, then a click). "
              "87.5–90°: locked pocket. Past 90.8°: hard stop.", ""]
    lines += ["## Mechanics estimates (hand calculations, PETG E = 2000 MPa, μ = 0.25)", "",
              f"- Plug ring compliance (free thin ring, {P.lug_count} point loads): {v['plug_ring_compliance_mm_per_N_free']:.4f} mm/N. "
              "The real plug is fixed to the neck at one end, so it is stiffer than this: forces below are **lower bounds**.",
              f"- Detent (V1.1 spring tongue, {v['tongue']['thickness']:.2f} × {v['tongue']['height']:.2f} mm, load arm {v['tongue']['load_arm_mm']:.1f} mm): "
              f"k = {v['tongue']['k_tongue_N_per_mm']:.0f} N/mm in series with the plug ({v['tongue']['k_plug_fea_N_per_mm']:.0f} N/mm, FEA) "
              f"= {v['tongue']['k_eff_N_per_mm']:.0f} N/mm. At the nominal {P.detent_interference} mm: {v['detent_force_per_lug_N_free_ring']:.1f} N per lug, "
              f"≈ {v['detent_torque_Nm_free_ring']:.2f} N·m to pass the bump (ramp {v['detent_ramp_deg']:.0f}°). "
              "With the printed interference expected to run ~0.1 mm above nominal, see DESIGN_REVIEW.md for the range.",
              f"- Pull-off with the cap locked: the plug (FEA {570:.0f} N/mm per lug) would have to collapse {v['lug_radial_engagement_mm']:.1f} mm at every lug "
              f"(≈ {v['pull_off_N_free_ring_lower_bound']:.0f} N by linear elasticity), far beyond what PETG takes: pull-off is limited by "
              "material failure, not by the 45° flanks. The cartridge weighs < 1 N.", "",
              "| Adapter | free contact Ø | fits bores | spring k | force/arm nominal | strain nominal / max | axial hold (2 adapters) |",
              "|---|---|---|---|---|---|---|"]
    for b, a in v["adapter_arms"].items():
        lines.append(f"| {float(b):g} mm | {a['free_contact_dia']:.1f} | {a['fits_bores'][0]:.1f}–{a['fits_bores'][1]:.1f} | "
                     f"{a['k_N_per_mm']:.2f} N/mm | {a['F_nominal_N']:.1f} N | {a['strain_nominal_pct']:.2f} % / {a['strain_max_pct']:.2f} % | "
                     f"{a['axial_retention_N']:.1f} N |")
    c = report["capacity"]
    lines += ["", "## Capacity and airflow", "",
              f"- Internal cavity (both caps on, windows in): **{c['cavity_ml']:.1f} mL**",
              f"- Usable fill (to the internal step below the top socket): **{c['fill_to_line_ml']:.1f} mL** "
              f"≈ {c['fill_to_line_ml'] * 0.70:.0f}–{c['fill_to_line_ml'] * 0.80:.0f} g of silica gel beads (bulk 0.70–0.80 g/mL)",
              f"- Water it can hold at equilibrium (Type A gel, ~10 % of its mass at 20 % RH, ~20 % at 40 % RH): "
              f"≈ {c['fill_to_line_ml'] * 0.75 * 0.10:.1f} g at 20 % RH, ≈ {c['fill_to_line_ml'] * 0.75 * 0.20:.1f} g at 40 % RH",
              f"- Open vent area: body {c['body_vent_area_mm2']:.0f} mm² ({report['body_info']['vent_slots']} slots), "
              f"cap faces {c['face_vent_area_mm2']:.0f} mm², total {c['body_vent_area_mm2'] + c['face_vent_area_mm2']:.0f} mm²",
              f"- Window viewing area: {c['window_view_area_mm2']:.0f} mm² (two Ø{P.window_aperture:g} windows)", ""]
    lines += ["## Bead containment (largest gap on every path out)", "",
              f"- Body vent slots: {P.vent_width} mm wide · cap face slots: {P.face_slot_width} mm",
              f"- Plug to socket: {P.fit_radial} mm radial · cap lift when locked: {P.bearing_play} mm",
              f"- Window to recess: {P.window_radial_clear} mm radial · body-to-body joint (coupler): ≤ {2 * P.bearing_play} mm",
              f"- Smallest bead that cannot escape: about {P.vent_width + 0.3:.1f} mm (slot width plus print variation). "
              "Use 2–5 mm beads.", ""]
    if mc:
        lines += ["## Printability (exported STLs, print orientation)", "",
                  "| File | watertight | bodies | volume cm³ | overhang mm² (>45°) | wall p1 / p5 / median mm |",
                  "|---|---|---|---|---|---|"]
        for n, m in mc.items():
            lines.append(f"| {n} | {m['watertight']} | {m['bodies']} | {m['volume_cm3']:.2f} | {m['overhang_area_mm2']:.1f} | "
                         f"{m['wall_p1']:.2f} / {m['wall_p5']:.2f} / {m['wall_median']:.2f} |")
        lines += ["", "Wall p1 values under 1.2 mm come from chamfer edges, crush ribs and the 0.45 mm-deep lettering, "
                  "not from structural walls. Designed minimum structural walls: vent wall "
                  f"{P.wall} mm, plug {P.plug_wall} mm, skin over groove {D['R_o'] - D['R_g']:.2f} mm, adapter arm {P.arm_thickness} mm, "
                  f"window lip {P.face_thickness - P.window_seat_depth:.1f} mm.", ""]
    if "parts" in report:
        lines += ["## Print estimates (from solid volume, PETG 1.27 g/cm³; NOT slicer output)", "",
                  "| File | volume cm³ | ≈ grams | ≈ minutes (alone) | size mm |", "|---|---|---|---|---|"]
        for n, p in report["parts"].items():
            lines.append(f"| {n} | {p['volume_mm3'] / 1000:.2f} | {p['est_grams']:.1f} | {p['est_minutes']:.0f} | "
                         + " × ".join(f"{x:.1f}" for x in p["bbox"]) + " |")
    path.write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", help="override a parameter: name=value")
    ap.add_argument("--params", help="JSON file of parameter overrides")
    ap.add_argument("--out", default=str(HERE / "models"))
    ap.add_argument("--quick", action="store_true", help="skip the slow rotation sweep")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args()
    P = parse_overrides(Params(), a.set, a.params)
    probs = P.check()
    for p in probs:
        print("PARAMETER WARNING:", p)
    D = P.d()
    print(f"DRYDOCK V1.1: total length {D['L_total']:.1f} mm, body {D['L_body']:.1f} mm, OD {P.body_od} mm")
    parts = build_parts(P)
    outdir = Path(a.out)
    report = {"params": {k: v for k, v in dataclasses.asdict(P).items()},
              "derived": {k: v for k, v in D.items() if not callable(v)},
              "parameter_warnings": probs}
    if not a.no_export:
        written = export_all(P, parts, outdir)
        report["parts"] = {}
        for name, s in written.items():
            bb = s.bounding_box()
            g, m = print_estimates(s.volume)
            report["parts"][name] = dict(volume_mm3=s.volume, bbox=[bb.size.X, bb.size.Y, bb.size.Z],
                                         est_grams=g, est_minutes=m)
        report["mesh_checks"] = mesh_checks(outdir / "stl")
    print("validating fits (boolean geometry)...")
    report["validation"] = validate(P, parts, quick=a.quick)
    report["capacity"] = capacity(P, parts, parts["body_info"])
    report["body_info"] = parts["body_info"]
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "DD011_report.json").write_text(json.dumps(report, indent=2, default=str))
    write_report_md(P, report, outdir / "DD011_validation_report.md")
    print(json.dumps(report["validation"]["fits"], indent=1, default=str))
    print(json.dumps(report["capacity"], indent=1))
    return parts, report


if __name__ == "__main__":
    main()
