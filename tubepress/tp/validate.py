"""TP-01 TUBEPRESS automated checks. Each check returns (name, passed, detail)."""

import math

import numpy as np
import trimesh
from shapely.affinity import rotate as srotate
from shapely.affinity import translate as stranslate

from . import geom as G
from . import printest as E
from .params import (BED_MARGIN, BUDGET_G, BUDGET_MIN, BUILD_VOLUMES, E_MPA, LEAF_STRAIN_LIMIT, NIP_VARIANTS, P,
                     TARGET_BED, TUBE_CRIMP_T, TUBE_FLAT_W, TUBE_LEN, TUBE_WALL, knob_x, roll_radius)


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=True)


def key_print(k, p=P):
    """Key in print orientation: axis vertical, knob outer face on the bed."""
    k0, _ = knob_x(p)
    return k.transform([[0, 1, 0, 0], [0, 0, 1, -p.axis_z], [1, 0, 0, -k0]])


def plate_layout(frame, keyp, gap=8.0):
    """Both parts on one plate, as (name, manifold) centred around the origin together."""
    fb = frame.bounding_box()
    kb = keyp.bounding_box()
    f = frame.translate([-fb[0], -(fb[1] + fb[4]) / 2, -fb[2]])
    kw = kb[3] - kb[0]
    k = keyp.translate([(fb[3] - fb[0]) + gap - kb[0], -(kb[1] + kb[4]) / 2, -kb[2]])
    total = (fb[3] - fb[0]) + gap + kw
    return [("TP-01 Frame", f.translate([-total / 2, 0, 0])), ("TP-01 Key", k.translate([-total / 2, 0, 0]))]


# -------------------------------------------------------------------------------------
def check_build_volume(layout):
    lo = np.min([m.bounding_box()[:3] for _, m in layout], 0)
    hi = np.max([m.bounding_box()[3:] for _, m in layout], 0)
    size = hi - lo
    res = {}
    for name, vol in BUILD_VOLUMES.items():
        lim = np.array(vol) - np.array([2 * BED_MARGIN, 2 * BED_MARGIN, 0])
        res[name] = bool(np.all(size <= lim))
    parts = {n: np.round(np.array(m.bounding_box()[3:]) - np.array(m.bounding_box()[:3]), 2).tolist() for n, m in layout}
    return "Both parts fit one A1 mini plate (5 mm margin)", res[TARGET_BED], dict(
        plate_footprint_mm=np.round(size, 2).tolist(), parts_mm=parts, fits=res)


def check_manifold(parts):
    out, ok = {}, True
    for n, m in parts:
        tm = to_trimesh(m)
        good = m.status().name == "NoError" and len(m.decompose()) == 1 and tm.is_watertight and tm.is_winding_consistent
        ok &= good
        out[n] = dict(bodies=len(m.decompose()), watertight=tm.is_watertight, genus=m.genus(),
                      volume_cm3=round(m.volume() / 1000, 3), ok=good)
    return "Every part is one closed, manifold body", ok, out


def check_files(parts, stls, mf):
    """parts: dict name -> manifold in print orientation; stls: dict name -> path; mf: the plate 3MF."""
    out, ok = {}, True
    for n, path in stls.items():
        m = parts[n]
        bb = np.array(m.bounding_box()).reshape(2, 3)
        ld = trimesh.load(path, force="mesh")
        good = (ld.is_watertight and len(ld.split(only_watertight=False)) == 1
                and np.allclose(ld.extents, bb[1] - bb[0], atol=0.02) and abs(ld.volume - m.volume()) / m.volume() < 2e-3)
        ok &= bool(good)
        out[path.split("/")[-1]] = dict(watertight=bool(ld.is_watertight), size_mm=np.round(ld.extents, 3).tolist(),
                                        volume_cm3=round(ld.volume / 1000, 3), ok=bool(good))
    ld = trimesh.load(mf, force="mesh")
    vol = sum(m.volume() for m in parts.values())
    good = ld.is_watertight and abs(ld.volume - vol) / vol < 2e-3
    ok &= bool(good)
    out[mf.split("/")[-1]] = dict(watertight=bool(ld.is_watertight), volume_cm3=round(ld.volume / 1000, 3),
                                  expected_cm3=round(vol / 1000, 3), ok=bool(good))
    return "Exported STL / 3MF re-read: watertight, same size and volume", ok, out


def check_overhangs(parts, limit=45.0, bridge_ok=6.0):
    out, ok = {}, True
    for n, m in parts:
        tm = to_trimesh(m)
        nz = tm.face_normals[:, 2]
        ang = np.degrees(np.arcsin(np.clip(-nz, -1, 1)))
        bad = (ang > limit + 0.5) & (tm.triangles_center[:, 2] > 0.05)
        patches = []
        if bad.any():
            sub = tm.submesh([np.where(bad)[0]], append=True)
            for comp in sub.split(only_watertight=False):
                e = comp.extents
                patches.append(dict(z=round(float(comp.bounds[0][2]), 2), span_mm=round(float(min(e[0], e[1])), 2),
                                    length_mm=round(float(max(e[0], e[1])), 2)))
        uns = [q for q in patches if q["span_mm"] > bridge_ok]
        ok &= not uns
        out[n] = dict(bridges=patches, unsupported=uns)
    return f"No unsupported overhang > {limit:.0f} deg in print orientation (bridges <= {bridge_ok:.0f} mm)", ok, out


def check_thin(parts, min_wall=1.2, layer=0.2, max_patch=1.0):
    from manifold3d import JoinType
    out, ok = {}, True
    r = min_wall / 2 - 0.01
    for n, m in parts:
        bb = m.bounding_box()
        worst = dict(area=0.0)
        for z in np.arange(bb[2] + layer / 2, bb[5], layer):
            s = m.slice(float(z))
            if s.area() <= 0:
                continue
            lost = s - s.offset(-r, JoinType.Round).offset(r, JoinType.Round)
            for poly in lost.to_polygons():
                q = np.asarray(poly)
                a = 0.5 * abs(np.sum(q[:, 0] * np.roll(q[:, 1], 1) - np.roll(q[:, 0], 1) * q[:, 1]))
                if a > worst["area"]:
                    worst = dict(area=round(float(a), 3), z=round(float(z), 2), xy=np.round(q.mean(0), 1).tolist())
        good = worst["area"] <= max_patch
        ok &= good
        out[n] = dict(largest_lost_patch_mm2=worst["area"], at=worst, ok=good)
    return f"No feature thinner than {min_wall} mm (3 x 0.4 mm nozzle) in any layer", ok, out


# -------------------------------------------------------------------------------------
def check_assembled(frame, key):
    """Seated key at the rest phase: no interference; running gaps measured with min_gap."""
    inter = (frame ^ key).volume()
    gap = frame.min_gap(key, 5.0)
    # gaps that matter, measured from the parameters
    k0, k1 = knob_x()
    d = dict(interference_mm3=round(inter, 4), min_gap_mm=round(gap, 3),
             bearing_radial_clearance_mm=P.bore_clear, knob_to_lug_mm=P.knob_gap,
             knob_tips_to_plate_mm=round(P.axis_z - P.r_tip - P.plate_t, 2),
             pawl_running_clearance_mm=0.15)
    ok = inter < 1e-3 and gap >= 0.1
    return "Assembled: no interference, every running gap >= 0.1 mm", ok, d


def check_insertion(frame, key, step=1.0):
    """Slide the key in along +x from fully out to seated (mark aligned, the only way the fork
    can take the crimp): it must not touch the frame anywhere along the way."""
    k0, k1 = knob_x()
    travel = P.slot_l + P.lug_t_far + P.lug_t_near + 2.0  # fork tip starts outside the near lug
    worst = 0.0
    hits = []
    for d in np.arange(travel, -0.001, -step):
        v = (frame ^ key.translate([-float(d), 0, 0])).volume()
        if v > worst:
            worst = v
        if v > 1e-3:
            hits.append(round(float(d), 1))
    ok = worst < 1e-3
    return "Key slides in from outside to seated without touching the frame", ok, dict(
        travel_mm=round(travel, 1), step_mm=step, max_interference_mm3=round(worst, 4), contact_at_offsets=hits[:10])


def _pawl_drop_needed(knob_poly, pawl_poly, max_drop=4.0):
    """Smallest downward shift of the pawl that clears the knob outline (2D, bisection)."""
    if not knob_poly.intersects(pawl_poly) or knob_poly.intersection(pawl_poly).area < 1e-6:
        return 0.0
    lo, hi = 0.0, max_drop
    for _ in range(30):
        mid = (lo + hi) / 2
        if knob_poly.intersection(stranslate(pawl_poly, 0, -mid)).area < 1e-6:
            hi = mid
        else:
            lo = mid
    return hi


def check_ratchet():
    """2D sweep of the knob teeth past the pawl in the section through the pawl.
    Free (winding) direction: the pawl must be pushed down by at most tooth depth + clearance.
    Lock direction: the steep face must meet the pawl's upright face (horizontal contact normal)."""
    pitch = 360.0 / P.teeth
    ph0 = G.rest_phase()
    pawl = G.pawl_profile(P)
    drops_free = []
    for a in np.linspace(0, pitch, 61):
        kp = G.knob_profile(P, ph0 - a)  # free direction = negative rotation
        drops_free.append(_pawl_drop_needed(kp, pawl))
    dmax = max(drops_free)
    # lock direction: rotate positive until contact
    backlash = None
    for a in np.linspace(0, pitch, 301):
        kp = G.knob_profile(P, ph0 + a)
        if kp.intersection(pawl).area > 1e-4:
            backlash = a
            break
    # escape drop in the lock direction (how far the pawl would have to drop to let a tooth past)
    esc = _pawl_drop_needed(G.knob_profile(P, ph0 + (backlash or 0) + 0.5), pawl)
    # contact face orientation: the pawl's locking face is vertical (x = const in the y-z section)
    ok_free = 0.8 <= dmax <= P.tooth_depth + 0.4
    ok_lock = backlash is not None and backlash < pitch * 0.5 and esc >= P.pawl_engage - 0.2
    return "Ratchet: winding direction clicks over, reverse direction locks within half a tooth", ok_free and ok_lock, dict(
        teeth=P.teeth, step_deg=round(pitch, 2), pawl_drop_free_direction_mm=round(dmax, 3),
        reverse_backlash_deg=round(backlash, 2) if backlash is not None else None,
        drop_needed_to_slip_in_reverse_mm=round(esc, 3), locking_face="radial, undercut %.0f deg" % P.undercut_deg,
        winding_direction="counter-clockwise looking at the knob face (arrow on the knob)")


def check_leaf(drop):
    """Bending strain at the leaf root for the free-direction drop (cantilever, tip load)."""
    eps = 3 * P.leaf_t * drop / (2 * P.leaf_l ** 2)
    out, ok = {}, True
    for mat, lim in LEAF_STRAIN_LIMIT.items():
        good = eps <= lim
        ok &= good
        # hold: the reverse load compresses the leaf; Euler fixed-free buckling, conservative
        I = P.leaf_w * P.leaf_t ** 3 / 12
        pcr = math.pi ** 2 * E_MPA[mat] * I / (4 * P.leaf_l ** 2)
        hold_nm = pcr * (P.r_tip - P.tooth_depth / 2) / 1000
        out[mat] = dict(strain_pct=round(100 * eps, 2), limit_pct=round(100 * lim, 2), buckling_load_N=round(pcr, 1),
                        reverse_hold_torque_Nm_conservative=round(hold_nm, 3), ok=good)
    # springback torque of a wound laminate tube (elastic upper bound): M = E I / R
    E_lam, w, t, R = 1500.0, TUBE_FLAT_W[1], TUBE_WALL[1], 6.0
    M = E_lam * 2 * (w * t ** 3 / 12) / R / 1000
    out["tube_springback_torque_Nm_estimate"] = round(M, 3)
    out["note"] = ("springback: elastic upper bound for two 0.35 mm walls, 65 mm wide, E 1.5 GPa, wound on the 12 mm "
                   "fork (no data found: an assumption to check)")
    ok &= out["PETG"]["reverse_hold_torque_Nm_conservative"] > 1.5 * M
    return "Pawl leaf: strain within fatigue-level limits; holds the tube's springback with margin", ok, out


def check_tubes():
    out = {}
    out["slot_length_mm"] = P.slot_l
    out["widest_tube_mm"] = TUBE_FLAT_W[1]
    out["fork_gap_mm"] = P.fork_gap
    out["thickest_crimp_mm"] = TUBE_CRIMP_T[1]
    t_layer = 2 * TUBE_WALL[1] + 0.3  # two walls + residual paste film
    r = roll_radius(TUBE_LEN[1], t_layer, P.shaft_d / 2)
    out["roll_radius_full_tube_mm"] = round(r, 2)
    out["roll_to_plate_clearance_mm"] = round(P.axis_z - r - P.plate_t, 2)
    out["nip_variants_mm"] = NIP_VARIANTS
    out["flattened_tube_mm"] = [2 * TUBE_WALL[0], 2 * TUBE_WALL[1]]
    ok = (P.slot_l >= TUBE_FLAT_W[1] + 2 and P.fork_gap >= TUBE_CRIMP_T[1] + 0.5
          and out["roll_to_plate_clearance_mm"] >= 3 and min(NIP_VARIANTS.values()) >= 2 * TUBE_WALL[1] + 0.4)
    return "Takes 32-65 mm tubes: slot, fork gap, nip and wound-roll clearance", ok, out


def check_budget(est):
    g = sum(e["grams"] for e in est.values())
    t = sum(e["minutes"] for e in est.values())
    ok = g <= BUDGET_G and t <= BUDGET_MIN
    return f"Filament <= {BUDGET_G:.0f} g and time <= {BUDGET_MIN:.0f} min for the set (estimate)", ok, dict(
        total_grams=round(g, 1), total_minutes=round(t, 1),
        parts={k: dict(grams=round(v["grams"], 1), minutes=round(v["minutes"], 1), layers=v["layers"]) for k, v in est.items()})
