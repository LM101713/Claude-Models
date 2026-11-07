"""
GS-05 GIFT SLIDE automated checks.

Every check returns (group, name, value, limit, ok). Geometry checks use the real solids
(manifold3d booleans and slices); the detent checks use detent.py, which reads the real beam
section and the real relief profile. None of this replaces a physical print: see TEST_PLAN.md.
"""

import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

from . import detent as Dt
from . import estimate as Est
from . import geom as G
from .params import BED, LOOSE, P, SNUG

TOL_VOL = 1e-3   # mm3: anything below this is numerical noise


class Checks:
    def __init__(self):
        self.rows = []
        self.data = {}

    def add(self, group, name, value, limit, ok, note=""):
        self.rows.append(dict(group=group, name=name, value=value, limit=limit, ok=bool(ok), note=note))
        return ok

    @property
    def passed(self):
        return all(r["ok"] for r in self.rows)


# ------------------------------------------------------------------ helpers


def width_of(sec):
    """Largest inscribed width of a 2-D region (2 x the largest erosion that leaves something)."""
    if sec.is_empty() or sec.area() < 1e-6:
        return 0.0
    lo, hi = 0.0, 20.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if sec.offset(-mid, JoinType.Miter).area() > 1e-6:
            lo = mid
        else:
            hi = mid
    return 2 * lo


def downward_regions(m, nz_max=-0.75, z_min=0.05):
    """Faces that point down more steeply than ~41 deg from horizontal and are not on the bed,
    grouped by height. Returns [(z, area, inscribed width)]."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    area2 = np.linalg.norm(n, axis=1)
    nz = n[:, 2] / np.maximum(area2, 1e-12)
    zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    sel = (nz < nz_max) & (zc > z_min) & (area2 > 1e-9)
    out = []
    if not sel.any():
        return out
    levels = np.round(zc[sel], 2)
    for z in sorted(set(levels)):
        idx = np.where(sel)[0][levels == z]
        polys = [np.array([a[i, :2], b[i, :2], c[i, :2]]) for i in idx]
        cr = lambda q: (q[1, 0] - q[0, 0]) * (q[2, 1] - q[0, 1]) - (q[1, 1] - q[0, 1]) * (q[2, 0] - q[0, 0])
        sec = CrossSection([q if cr(q) > 0 else q[::-1] for q in polys if abs(cr(q)) > 1e-12])
        out.append((float(z), float(sec.area()), width_of(sec)))
    return out


def needed_shift(bump_m, tray_m):
    """Smallest inward (-Y) shift of the bump that clears the tray: the beam deflection the
    3-D geometry demands, measured by bisection on real booleans."""
    if (bump_m ^ tray_m).volume() < TOL_VOL:
        return 0.0
    lo, hi = 0.0, 1.5
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if (bump_m.translate((0, -mid, 0)) ^ tray_m).volume() < TOL_VOL:
            hi = mid
        else:
            lo = mid
    return hi


def intersect_vol(a, b):
    return (a ^ b).volume()


def overlap_y_depth(a, b):
    """Lateral depth of the overlap on the +Y side only."""
    half = Manifold.cube((400, 100, 100)).translate((-100, 0.0, -50))
    i = (a ^ b) ^ half
    if i.volume() < TOL_VOL:
        return 0.0
    bb = i.bounding_box()
    return bb[4] - bb[1]


# ------------------------------------------------------------------ the checks


def run(p=P, quick=False):
    C = Checks()
    tray = G.tray(p)
    lid = G.lid(p)
    lid_nb = G.lid(p, bumps=False)
    lid_star = G.lid(p, star=True)
    inlay = G.star_inlay(p)
    lid_loose = G.lid(p, dy=-LOOSE)
    lid_snug = G.lid(p, dy=SNUG)
    cp = G.coupon_params(p)
    c_tray = G.tray(cp, logo=False, window=True, push_hole=False, message="")
    c_lid = G.lid(cp, window=True, tag="STD")
    c_lid_loose = G.lid(cp, dy=-LOOSE, window=True, tag="LOOSE")
    c_lid_snug = G.lid(cp, dy=SNUG, window=True, tag="SNUG")
    card = G.card(p)
    parts = dict(tray=tray, lid=lid, lid_star=lid_star, star_inlay=inlay, lid_loose=lid_loose, lid_snug=lid_snug,
                 coupon_tray=c_tray, coupon_lid=c_lid, coupon_lid_loose=c_lid_loose, coupon_lid_snug=c_lid_snug)
    C.data["parts"] = parts

    # ---------------------------------------------------------- A. solids
    for k, m in parts.items():
        ok = m.status().name == "NoError" and len(m.decompose()) == 1 and m.volume() > 0
        C.add("A solids", f"{k}: valid closed solid, one body", f"{m.volume() / 1000:.2f} cm3",
              "manifold, 1 body", ok)

    # ---------------------------------------------------------- B. build volume
    for k, m in parts.items():
        bb = m.bounding_box()
        dims = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
        C.add("B build volume", f"{k}: size", "%.1f x %.1f x %.2f mm" % dims, "<= 180 x 180 x 180",
              all(d <= lim for d, lim in zip(dims, BED)) and bb[2] > -1e-6)
    plate_w = (tray.bounding_box()[4] - tray.bounding_box()[1]) + (lid.bounding_box()[4] - lid.bounding_box()[1]) + 6
    C.add("B build volume", "tray + lid on one A1 mini plate (side by side, 6 mm gap)",
          f"{p.L:.1f} x {plate_w:.1f} mm", "<= 180 x 180", plate_w <= 175 and p.L <= 175)

    # ---------------------------------------------------------- C. assembly through the travel
    s_list = np.round(np.r_[np.arange(0.0, p.travel + 0.01, 0.5 if not quick else 2.0), p.travel], 3)
    worst_rigid = 0.0
    for s in s_list:
        worst_rigid = max(worst_rigid, intersect_vol(G.lid_placed(p, s, lid_m=lid_nb), tray))
    C.add("C assembly", f"lid body (without bumps) vs tray, {len(s_list)} positions 0..{p.travel:.0f} mm",
          f"{worst_rigid:.4f} mm3", "0 (no collision)", worst_rigid < TOL_VOL)
    # printer-variation corners in 3-D (rigid lid body, the bumps are the detent's business)
    for name, (tdy, ldy, lid_var) in {
        "tight print (tray -0.15, lid +0.05)": (-0.15, 0.05, 0.0),
        "very tight print + Loose lid": (-0.20, 0.10, -LOOSE),
        "very loose print + Snug lid": (0.15, -0.10, SNUG),
    }.items():
        t_c = G.tray(p, dy=tdy, logo=False, message="")
        l_c = G.lid(p, dy=ldy + lid_var, bumps=False)
        s0 = max(0.0, -tdy)   # a tight end wall stops the lid that much further out
        w = max(intersect_vol(G.lid_placed(p, s, lid_m=l_c), t_c) for s in (s0, p.travel / 2, p.travel))
        C.add("C assembly", f"{name}: lid body vs tray at closed / mid / open", f"{w:.4f} mm3", "0", w < TOL_VOL)
    # as sliced: each 0.2 mm layer of each part is its mid-plane section; same-band overlap = fused
    worst_gap, worst_ov = 9.0, 0.0
    for s in (0.3, p.travel / 2, p.travel):   # 0.3: lid off the end wall it closes against
        lp = G.lid_placed(p, s, lid_m=lid_nb)
        z = p.z_ledge + p.layer / 2
        while z < p.H:
            tr_s, ld_s = tray.slice(z), lp.slice(z)
            worst_ov = max(worst_ov, (tr_s ^ ld_s).area())
            lo, hi = 0.0, 1.0
            for _ in range(14):
                mid = 0.5 * (lo + hi)
                if (tr_s.offset(mid, JoinType.Miter) ^ ld_s).area() > 1e-6:
                    hi = mid
                else:
                    lo = mid
            worst_gap = min(worst_gap, lo)
            z += p.layer
    C.add("C assembly", "as sliced (0.2 mm layers): lid and tray never share a layer region", f"{worst_ov:.4f} mm2",
          "0", worst_ov < 1e-4)
    C.add("C assembly", "as sliced: smallest in-layer gap, lid to tray", f"{worst_gap:.2f} mm", ">= 0.10 mm",
          worst_gap >= 0.10)
    C.data["sliced_gap"] = worst_gap
    # bump-only contact must match the detent model
    s_model, d_model = Dt.deflection(p)
    probe = [0.0, 0.6, 1.4, 2.0, 2.6, 3.2, 30.0, p.travel - 1.0, p.travel + 0.3, p.travel + 0.8]
    worst_err, rows = 0.0, []
    bump3 = G.bump(p, 0.0, +1)
    for s in probe:
        d3 = needed_shift(G.lid_placed(p, s, lid_m=bump3), tray)
        d1 = float(np.interp(s, s_model, d_model))
        rows.append((s, d3, d1))
        worst_err = max(worst_err, abs(d3 - d1))
    C.data["bump_crosscheck"] = rows
    C.add("C assembly", "bump overlap in 3-D equals the 1-D detent model (10 positions)",
          f"max error {worst_err:.3f} mm", "<= 0.03 mm", worst_err <= 0.03)
    parked = overlap_y_depth(G.lid_placed(p, 0.0, lid_m=lid), tray)
    C.add("C assembly", "closed: bump parked, beam unloaded (no creep while stored)", f"{parked:.3f} mm", "0",
          parked < 1e-3)
    at_stop = float(np.interp(p.travel - 0.2, s_model, d_model))
    C.add("C assembly", "open: bump against the stop, beam unloaded", f"{at_stop:.3f} mm", "0", at_stop < 1e-3)
    # card
    card_hits = intersect_vol(card, tray)
    card_lid = max(intersect_vol(card, G.lid_placed(p, s, lid_m=lid)) for s in (0.0, p.travel / 2, p.travel))
    C.add("C assembly", "card sits in the pocket without touching the tray", f"{card_hits:.4f} mm3", "0",
          card_hits < TOL_VOL)
    C.add("C assembly", "card clear of the lid at closed / mid / open", f"{card_lid:.4f} mm3", "0", card_lid < TOL_VOL)
    head = p.pocket_depth - p.card_t
    C.add("C assembly", "headroom over the card (folded notes)", f"{head:.2f} mm",
          ">= 2.0 mm (4 notes folded in quarters)", head >= 2.0)
    # exposure at the open stop
    card_sec = card.slice(p.floor_t + 0.3)
    lid_open = G.lid_placed(p, p.travel, lid_m=lid).slice(p.z_ledge + 0.5)
    exposed = (card_sec - lid_open).area() / card_sec.area()
    C.data["exposed"] = exposed
    C.add("C assembly", "card face uncovered at the open stop", f"{exposed * 100:.0f} %", ">= 65 %", exposed >= 0.65)
    hole_ok = p.push_hole_x + p.push_hole_d / 2 < p.end_wall + p.travel - 2
    C.add("C assembly", "push hole is under the uncovered part of the card",
          f"hole x {p.push_hole_x - p.push_hole_d / 2:.0f}..{p.push_hole_x + p.push_hole_d / 2:.0f}",
          f"< lid edge at x {p.end_wall + p.travel:.1f}", hole_ok)
    engage = p.lid_l - p.travel
    C.add("C assembly", "lid still engaged in the grooves at the open stop", f"{engage:.1f} mm", ">= 25 mm",
          engage >= 25)

    # ---------------------------------------------------------- D. the section
    c = p.lid_clear
    C.add("D section", "lateral clearance, land to groove face (per side)", f"{c:.2f} mm", "0.20..0.30", 0.2 <= c <= 0.3)
    gap_n = p.lip_gap_z / math.sqrt(2)
    C.add("D section", "normal gap, lid bevel to lip underside", f"{gap_n:.2f} mm", ">= 0.18", gap_n >= 0.18)
    overlap = p.land_y - p.y_lip
    C.add("D section", "dovetail overlap (lid edge under the lip, per side)", f"{overlap:.2f} mm", ">= 0.5 mm",
          overlap >= 0.5)
    shadow = p.y_lip - p.panel_y
    C.add("D section", "shadow gap at the lid edge (hides the flexure slot)", f"{shadow:.2f} mm", "1.0..2.0",
          1.0 <= shadow <= 2.0)
    under_tip = (p.lid_t - p.lip_tip_h) - p.bevel_top_z
    C.add("D section", "beam top clears the lip tip", f"{under_tip:.2f} mm", ">= 0.2", under_tip >= 0.2)
    C.add("D section", "bump top under the relief-track ceiling", f"{p.z_junction - p.bump_h:.2f} mm", ">= 0.25",
          p.z_junction - p.bump_h >= 0.25)
    C.add("D section", "relief-track ceiling overhang (printed, unsupported)", f"{p.relief_d:.2f} mm", "<= 0.5",
          p.relief_d <= 0.5)
    C.add("D section", "wall behind the relief track", f"{p.wall_behind:.2f} mm", ">= 1.2 (3 lines)",
          p.wall_behind >= 1.2)
    C.add("D section", "flexure beam width (at the land)", f"{p.beam_w:.2f} mm", ">= 1.2 (3 lines)", p.beam_w >= 1.2)
    C.add("D section", "flexure slot width", f"{p.slot_w:.2f} mm", ">= 0.6 (prints open)", p.slot_w >= 0.6)
    ledge = p.y_g - p.pocket_w / 2
    C.add("D section", "ledge the lid rides on (per side)", f"{ledge:.2f} mm", ">= 2.0", ledge >= 2.0)
    C.add("D section", "floor under the debossed message / logo", f"{p.floor_t - max(p.message_depth, p.logo_depth):.2f} mm",
          ">= 0.8", p.floor_t - max(p.message_depth, p.logo_depth) >= 0.8 - 1e-9)
    # the debossed message (top of floor) and logo (bottom) must not overlap in X
    msg_x = (p.message_x - p.message_h / 2, p.message_x + p.message_h / 2)
    logo_x = (p.L * 0.62 - 3.4 - 1.5, p.L * 0.62 + 3.2 + 2.2)
    sep = max(logo_x[0] - msg_x[1], msg_x[0] - logo_x[1])
    C.add("D section", "message and logo debosses do not stack", f"{sep:.1f} mm apart", "> 1 mm", sep > 1.0)

    # ---------------------------------------------------------- E. detent across printer variation
    corners = {
        "nominal": (0.0, 0.0),
        "tight (tray -0.15, lid +0.05)": (-0.15, 0.05),
        "tight lid (tray -0.05, lid +0.10)": (-0.05, 0.10),
        "loose (tray +0.10, lid -0.05)": (0.10, -0.05),
        "very tight (tray -0.20, lid +0.10) + Loose lid": (-0.20, 0.10 - LOOSE),
        "very loose (tray +0.15, lid -0.10) + Snug lid": (0.15, -0.10 + SNUG),
    }
    res = {k: Dt.summary(p, *v) for k, v in corners.items()}
    C.data["detent"] = res
    nom = res["nominal"]
    C.data["beam"] = Dt.beam(p)
    for k, r in res.items():
        C.add("E detent", f"{k}: opening click (break-away)", f"{r['F_open_r1']:.1f} N", "1.5..7 N",
              1.5 <= r["F_open_r1"] <= 7.0)
        C.add("E detent", f"{k}: open stop", f"{r['F_stop']:.1f} N", ">= 5 N and > 2x click",
              r["F_stop"] >= 5.0 and r["F_stop"] > 2 * r["F_open_r1"])
        C.add("E detent", f"{k}: worst beam strain", f"{r['strain_max'] * 100:.2f} %", "<= 1.0 %", r["strain_max"] <= 0.010)
        C.add("E detent", f"{k}: lid clearance / running drag", f"c {r['clear']:.2f} mm, {r['F_run']:.2f} N",
              "c >= 0.05, drag <= 0.6 N", r["clear"] >= 0.049 and r["F_run"] <= 0.6)
        C.add("E detent", f"{k}: slot room left at full deflection", f"{r['slot_room']:.2f} mm", ">= 0.15",
              r["slot_room"] >= 0.15)
    C.add("E detent", "nominal: travel to the open stop", f"{nom['travel_to_stop']:.1f} mm",
          f"{p.travel:.0f} +/- 1", abs(nom["travel_to_stop"] - p.travel) <= 1.0)
    C.add("E detent", "nominal: closing click", f"{nom['F_close_r1']:.1f} N", "1..6 N", 1.0 <= nom["F_close_r1"] <= 6.0)
    C.add("E detent", "nominal: snap-in force when fitting the lid", f"{nom['F_insert']:.1f} N", "<= 8 N",
          nom["F_insert"] <= 8)
    # material spread at nominal geometry
    spread = {}
    for E in (2500, 3500):
        for mu in (0.2, 0.45):
            r = Dt.summary(p, 0, 0, E=E, mu=mu)
            spread[(E, mu)] = r
    C.data["spread"] = spread
    lo = min(r["F_open_r1"] for r in spread.values())
    hi = max(r["F_open_r1"] for r in spread.values())
    C.add("E detent", "nominal geometry, E 2.5-3.5 GPa, mu 0.20-0.45: opening click", f"{lo:.1f}..{hi:.1f} N",
          "1.5..7 N", lo >= 1.5 and hi <= 7.0)
    weight_n = lid.volume() / 1000 * p.rho * 9.81e-3
    C.add("E detent", "retention vs the lid's own weight", f"{nom['F_open_r1'] / weight_n:.0f} x",
          ">= 10 x (survives being shaken)", nom["F_open_r1"] / weight_n >= 10)
    loose = Dt.summary(p, 0.0, -LOOSE)
    C.add("E detent", "Loose lid on a nominal tray: opening click / stop", f"{loose['F_open_r1']:.1f} / {loose['F_stop']:.1f} N",
          "click >= 1.5 N, stop >= 5 N", loose["F_open_r1"] >= 1.5 and loose["F_stop"] >= 5)
    snug = Dt.summary(p, 0.0, SNUG)
    C.add("E detent", "Snug lid on a nominal tray: clearance / opening click", f"c {snug['clear']:.2f} mm, {snug['F_open_r1']:.1f} N",
          "c >= 0.05, click <= 7 N", snug["clear"] >= 0.049 and snug["F_open_r1"] <= 7)
    # without the variants, what does the Standard lid do at the extreme corners? (informational)
    C.data["unfixed_extremes"] = {k: Dt.summary(p, *v) for k, v in
                                  {"very tight, Standard lid": (-0.20, 0.10), "very loose, Standard lid": (0.15, -0.10)}.items()}

    # the fit coupon must behave like the real thing
    cs_ = Dt.summary(cp)
    worst_c = max(intersect_vol(G.lid_placed(cp, s, lid_m=G.lid(cp, bumps=False, window=True)), c_tray)
                  for s in np.arange(0.0, cp.travel + 0.01, 1.0))
    C.add("E detent", "fit coupon: lid body vs tray over its travel", f"{worst_c:.4f} mm3", "0", worst_c < TOL_VOL)
    C.add("E detent", "fit coupon: same click / stop as the full part",
          f"{cs_['F_open_r1']:.1f} / {cs_['F_stop']:.1f} N (full: {nom['F_open_r1']:.1f} / {nom['F_stop']:.1f})",
          "within 0.2 N", abs(cs_["F_open_r1"] - nom["F_open_r1"]) < 0.2 and abs(cs_["F_stop"] - nom["F_stop"]) < 0.2)
    C.add("E detent", "fit coupon: travel to its stop", f"{cs_['travel_to_stop']:.1f} mm", f"{cp.travel:.0f} +/- 1",
          abs(cs_["travel_to_stop"] - cp.travel) <= 1)

    # ---------------------------------------------------------- F. printability
    for k in ("tray", "lid", "lid_star", "coupon_tray", "coupon_lid"):
        regs = downward_regions(parts[k])
        C.data[f"overhang_{k}"] = regs
        bad = [(z, a, w) for z, a, w in regs if w > 0.7 and not (k.endswith("tray") and z <= p.logo_depth + 0.01)]
        bridges = [(z, a, w) for z, a, w in regs if k.endswith("tray") and z <= p.logo_depth + 0.01]
        worst_bridge = max([w for _, _, w in bridges], default=0.0)
        C.add("F print", f"{k}: unsupported flat overhangs wider than 0.7 mm", f"{len(bad)}",
              "0 (no supports)", len(bad) == 0,
              "; ".join(f"z={z:.2f} w={w:.2f}" for z, a, w in regs[:6]))
        if bridges:
            C.add("F print", f"{k}: widest bridge over the debossed logo", f"{worst_bridge:.2f} mm", "<= 3 mm",
                  worst_bridge <= 3.0)

    # ---------------------------------------------------------- G. mass and time
    est = {k: Est.estimate(parts[k], k) for k in ("tray", "lid", "coupon_tray", "coupon_lid")}
    C.data["estimate"] = est
    grams = est["tray"]["grams"] + est["lid"]["grams"]
    mins = est["tray"]["print_min"] + est["lid"]["print_min"] + Est.PROCESS["start_overhead_min"]
    C.add("G budget", "filament, tray + lid (estimate)", f"{grams:.1f} g", "<= 35 g", grams <= 35)
    C.add("G budget", "print time, tray + lid on one plate incl. start (estimate)", f"{mins:.0f} min",
          "<= 90 min", mins <= 90)
    cmins = est["coupon_tray"]["print_min"] + 3 * est["coupon_lid"]["print_min"] + Est.PROCESS["start_overhead_min"]
    cgr = est["coupon_tray"]["grams"] + 3 * est["coupon_lid"]["grams"]
    C.data["coupon_plate"] = dict(minutes=cmins, grams=cgr)
    C.add("G budget", "fit coupon plate: tray + Standard, Loose and Snug lids (estimate)", f"{cmins:.0f} min, {cgr:.0f} g",
          "<= 35 min", cmins <= 35)
    return C
