"""
HF-04 HOLDFAST: CAD validation.

Everything here is computed on the exact solids (manifold3d booleans, min-gap queries and ray
casts) plus hand-calculation models. NOTHING here is a physical test. The report says so.
"""

import contextlib
import math
import os

import numpy as np
from shapely.geometry import Polygon

from . import geom as G
from .params import D, P, centre, diameter_of_s, roll_angle, s_of_diameter

EPS_VOL = 1e-3  # mm3: any boolean overlap above this is a collision
CONTACT_GAP = 0.02  # rollers / handle are placed this far off their designed contact faces


# =====================================================================================
# placement helpers
# =====================================================================================


def place(roller, s, side, dn=CONTACT_GAP, dy=0.0):
    """Roller at travel s, lifted dn off its ramp (along the ramp normal) and moved dy in Y."""
    m = G.roller_to_use(roller, s, side)
    nx, nz = D.n
    return m.translate([nx * dn * (1 if side < 0 else -1), dy, nz * dn])


def overlap(a, b):
    return (a ^ b).volume()


def gap(a, b, search=6.0):
    return a.min_gap(b, search)


def slab_y(m, y_lo=None, y_hi=None):
    if y_lo is not None:
        m = m.trim_by_plane([0, 1, 0], y_lo)
    if y_hi is not None:
        m = m.trim_by_plane([0, -1, 0], -y_hi)
    return m


def ramp_zone(depth=3.0):
    """Thin solid covering both ramp faces (so other wall clearances can be measured)."""
    p0, u, n = D.P0, D.u, D.n
    a, b = p0 - 80 * u, p0 + 80 * u
    poly = Polygon([a + 0.05 * n, b + 0.05 * n, b - depth * n, a - depth * n])
    left = G.chamfered_prism(G.XZ(poly), P.BACK_T - 0.05, 60.0)
    left = G.xz_to_use(left)
    return left + left.mirror([1, 0, 0])


@contextlib.contextmanager
def variant(**kw):
    old = {k: getattr(P, k) for k in kw}
    for k, v in kw.items():
        setattr(P, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(P, k, v)


# =====================================================================================
# part checks
# =====================================================================================


def part_report(name, m, print_frame):
    lo, hi = np.array(m.bounding_box()[:3]), np.array(m.bounding_box()[3:])
    comps = len(m.decompose())
    mesh = print_frame.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts)
    oh = overhang_scan(v, t)
    th = thickness_scan(print_frame)
    return dict(
        name=name,
        status=m.status().name,
        volume_mm3=m.volume(),
        surface_mm2=m.surface_area(),
        genus=m.genus(),
        shells=comps,
        tris=m.num_tri(),
        size_use=(hi - lo).tolist(),
        print_height=float(v[:, 2].max() - v[:, 2].min()),
        bed_area_mm2=oh["bed_area"],
        overhang=oh,
        thickness=th,
    )


def overhang_scan(v, t, limit_deg=45.0, tol_deg=1.0):
    """Downward faces in print orientation (bed face excluded)."""
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    nrm = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    nrm = nrm / (2 * area[:, None] + 1e-12)
    zmin = v[:, 2].min()
    zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    on_bed = (np.abs(zc - zmin) < 1e-3) & (nrm[:, 2] < -0.999)
    down_ang = np.degrees(np.arccos(np.clip(-nrm[:, 2], -1, 1)))  # 0 = facing straight down
    # a face is an overhang if it faces down more steeply than (90 - limit) from vertical
    ang_from_vertical = 90.0 - down_ang  # 0 = vertical wall, 90 = flat ceiling
    downward = nrm[:, 2] < -1e-6
    steep = downward & ~on_bed & (ang_from_vertical > limit_deg + tol_deg)
    flat_all = downward & ~on_bed & (ang_from_vertical > 89.0)
    engr = flat_all & (zc - zmin < 0.7)  # ceilings of marks engraved into the bed face
    flat = flat_all & ~engr
    at45 = downward & ~on_bed & (np.abs(ang_from_vertical - limit_deg) <= tol_deg)
    regions = []
    for mask, label in ((engr, "engraving ceiling on bed face"), (flat, "flat (bridge)"),
                        (steep & ~flat_all, f"steeper than {limit_deg:.0f} deg")):
        if mask.any():
            cen = (a[mask] + b[mask] + c[mask]) / 3
            regions.append(
                dict(
                    kind=label,
                    area_mm2=float(area[mask].sum()),
                    z_range=[float(cen[:, 2].min()), float(cen[:, 2].max())],
                    max_span_hint_mm=float(np.ptp(cen[:, 0]) if mask.sum() > 1 else 0),
                )
            )
    return dict(
        bed_area=float(area[on_bed].sum()),
        flat_area=float(area[flat].sum()),
        engraving_ceiling_area=float(area[engr].sum()),
        steep_area=float(area[steep & ~flat_all].sum()),
        at_45_area=float(area[at45].sum()),
        regions=regions,
    )


def thickness_scan(m, n_samples=2500, max_len=30.0, seed=1):
    """Wall thickness by ray casting inward from sampled faces (normal through the part)."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    nrm = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    nrm = nrm / (2 * area[:, None] + 1e-12)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(t), size=min(n_samples, len(t)), replace=False, p=area / area.sum())
    th = []
    for i in idx:
        p = (a[i] + b[i] + c[i]) / 3
        o = p - 0.01 * nrm[i]
        e = p - max_len * nrm[i]
        hits = m.ray_cast(o.tolist(), e.tolist())
        if hits:
            th.append(hits[0].distance * max_len + 0.01)
    th = np.array(th)
    return dict(
        samples=int(len(th)),
        min=float(th.min()) if len(th) else None,
        p01=float(np.percentile(th, 1)) if len(th) else None,
        below_0p8=int((th < 0.8).sum()),
        below_1p2=int((th < 1.2).sum()),
    )


# =====================================================================================
# mechanism checks
# =====================================================================================


def stub_of(roller_use_frame):
    """The stub of a placed roller: everything behind the roller's back face."""
    return slab_y(roller_use_frame, None, P.BACK_T + P.G_BACK - 0.01)


def body_of(roller_use_frame):
    return slab_y(roller_use_frame, P.BACK_T + P.G_BACK - 0.01, None)


def travel_sweep(base, roller, step=0.5):
    """Roller on its ramp at every travel position, both sides."""
    plate = slab_y(base, None, P.BACK_T)
    walls = slab_y(base, P.BACK_T + 0.1, None)
    walls_nr = walls - ramp_zone()
    rows = []
    s_vals = list(np.arange(0.0, D.s_key + 1e-9, step))
    if s_vals[-1] < D.s_key - 1e-6:
        s_vals.append(D.s_key)
    for s in s_vals:
        row = dict(s=float(s), handle_d=diameter_of_s(s))
        for side in (-1, +1):
            r = place(roller, s, side)
            st, bd = stub_of(r), body_of(r)
            k = "L" if side < 0 else "R"
            row[f"{k}_overlap"] = overlap(r, base)
            row[f"{k}_gap_ramp"] = gap(bd, walls)
            row[f"{k}_gap_walls"] = gap(bd, walls_nr)
            row[f"{k}_gap_back"] = gap(bd, plate)
            row[f"{k}_gap_stub"] = gap(st, base)
        rows.append(row)
    return rows


def forward_play(base, roller, s, side=-1, t_max=40.0):
    """How far (mm) the roller can be pulled straight out (+Y) before it is stopped.

    Marches along the pull-out path (fine steps first) and refines the first contact."""
    r0 = place(roller, s, side)
    t_prev, t = 0.0, 0.0
    while t <= t_max + 1e-9:
        if overlap(r0.translate([0, t, 0]), base) > EPS_VOL:
            lo, hi = t_prev, t
            for _ in range(12):
                mid = (lo + hi) / 2
                if overlap(r0.translate([0, mid, 0]), base) > EPS_VOL:
                    hi = mid
                else:
                    lo = mid
            return lo
        t_prev = t
        t += 0.05 if t < 3.0 else 0.5
    return math.inf


def _path_clear(base, r0, t_max, step=0.5):
    t = 0.0
    while t <= t_max + 1e-9:
        if overlap(r0.translate([0, t, 0]), base) > EPS_VOL:
            return False
        t += step
    return True


def retention_table(base, roller, s_list=None):
    if s_list is None:
        s_list = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 29.0, D.s_key - 3.0, D.s_key - 1.5, D.s_key]
    rows = []
    for s in s_list:
        fp = forward_play(base, roller, s)
        rows.append(dict(s=float(s), handle_d=diameter_of_s(s), forward_play=fp,
                         retained=bool(math.isfinite(fp))))
    return rows


def assembly_path(base, roller, side=-1, step=0.25, lift=40.0):
    """Insert the stub through the keyhole (straight in along -Y), then roll down the ramp."""
    hits = []
    worst = math.inf
    t = lift
    while t >= -1e-9:
        r = place(roller, D.s_key, side, dy=t)
        ov = overlap(r, base)
        if ov > EPS_VOL:
            hits.append(("insert", float(t), ov))
        if t < 6:
            worst = min(worst, gap(stub_of(r), base, 3.0))
        t -= step
    s = D.s_key
    while s >= -1e-9:
        r = place(roller, s, side)
        ov = overlap(r, base)
        if ov > EPS_VOL:
            hits.append(("roll", float(s), ov))
        s -= step
    return dict(hits=hits, min_stub_gap_insert=worst, steps_insert=int(lift / step) + 1,
                steps_roll=int(D.s_key / step) + 1)


def handle_checks(base, roller, dias=(19.0, 22.0, 25.0, 28.0, 32.0, 35.0)):
    walls = slab_y(base, P.BACK_T + 0.1, None)
    rows = []
    for d in dias:
        h = G.handle(d, -150, 150, gap=CONTACT_GAP)
        s = s_of_diameter(d + 2 * CONTACT_GAP)
        rl, rr = place(roller, s, -1), place(roller, s, +1)
        yc = P.BACK_T + CONTACT_GAP + d / 2
        y_flat = (P.BACK_T + P.G_BACK + P.ROLL_CH_BACK, P.BACK_T + P.G_BACK + P.T_ROLL - P.ROLL_CH_FRONT)
        rows.append(
            dict(
                handle_d=d,
                travel_s=s,
                rated=P.D_RATED[0] <= d <= P.D_RATED[1],
                handle_base_overlap=overlap(h, base),
                handle_roller_overlap=overlap(h, rl) + overlap(h, rr),
                roller_base_overlap=overlap(rl, base) + overlap(rr, base),
                gap_handle_to_housings=gap(h, walls, 10.0),
                gap_handle_to_rollers=min(gap(h, rl), gap(h, rr)),
                grip_height_z=float(centre(s)[1]),
                contact_y=yc,
                contact_inside_flat=bool(y_flat[0] + 0.5 <= yc <= y_flat[1] - 0.5),
                contact_margin_front=y_flat[1] - yc,
                roller_turn_deg=roll_angle(s),
            )
        )
    return rows


def insertion_path(base, dias=(19.0, 25.0, 32.0), y_from=60.0, step=1.0):
    """The handle travels in from the front to the back plate: the channel must let it pass."""
    out = []
    for d in dias:
        worst = math.inf
        y = y_from
        hit = False
        while y >= CONTACT_GAP - 1e-9:
            h = G.handle(d, -150, 150, gap=y)
            if overlap(h, base) > EPS_VOL:
                hit = True
            if y < 20:
                worst = min(worst, gap(h, slab_y(base, P.BACK_T + 0.5, None), 10.0))
            y -= step
        out.append(dict(handle_d=d, collides=hit, min_gap_to_housings=worst))
    return out


# =====================================================================================
# printer-variation corners (geometry rebuilt with the dimensional errors applied)
# =====================================================================================


CORNERS = {
    "nominal": {},
    "tight printer (holes -0.2, bosses +0.1, lip +0.1 thick)": dict(
        LIP_SLOT_HALF=P.LIP_SLOT_HALF - 0.1,
        CAV_HALF=P.CAV_HALF - 0.1,
        KEY_R=P.KEY_R - 0.1,
        NECK_R=P.NECK_R + 0.05,
        HEAD_R=P.HEAD_R + 0.05,
        Y_LIP_UNDER=P.Y_LIP_UNDER - 0.1,
        Y_CAV_FLOOR=P.Y_CAV_FLOOR + 0.1,
    ),
    "very tight (holes -0.4, bosses +0.2, Z +-0.15)": dict(
        LIP_SLOT_HALF=P.LIP_SLOT_HALF - 0.2,
        CAV_HALF=P.CAV_HALF - 0.2,
        KEY_R=P.KEY_R - 0.2,
        NECK_R=P.NECK_R + 0.1,
        HEAD_R=P.HEAD_R + 0.1,
        Y_LIP_UNDER=P.Y_LIP_UNDER - 0.15,
        Y_CAV_FLOOR=P.Y_CAV_FLOOR + 0.15,
    ),
    "loose printer (holes +0.2, bosses -0.1)": dict(
        LIP_SLOT_HALF=P.LIP_SLOT_HALF + 0.1,
        CAV_HALF=P.CAV_HALF + 0.1,
        KEY_R=P.KEY_R + 0.1,
        NECK_R=P.NECK_R - 0.05,
        HEAD_R=P.HEAD_R - 0.05,
    ),
}


def corner_checks(loose_roller=False):
    """Rebuild the slot and the stub with each corner's errors; re-run fit, path and retention."""
    rows = []
    for name, kw in CORNERS.items():
        with variant(**kw):
            base = G.build_base(engrave=False)
            roller = G.build_roller(loose=loose_roller)
            path = assembly_path(base, roller, step=0.5, lift=12.0)
            sweep_hits = 0
            min_stub = math.inf
            for s in np.linspace(0.6, D.s_key - 0.6, 12):
                r = place(roller, s, -1)
                if overlap(r, base) > EPS_VOL:
                    sweep_hits += 1
                min_stub = min(min_stub, gap(stub_of(r), base, 3.0))
            ret = [forward_play(base, roller, s, t_max=12.0) for s in (0.0, 15.0, D.s_key - 3.0)]
            lip_overlap = P.HEAD_R - P.LIP_SLOT_HALF
            rows.append(
                dict(
                    corner=name,
                    roller="Loose" if loose_roller else "Standard",
                    assembly_hits=len(path["hits"]),
                    sweep_hits=sweep_hits,
                    min_stub_gap_in_travel=min_stub,
                    forward_play=[None if not math.isfinite(x) else x for x in ret],
                    retained=all(math.isfinite(x) for x in ret),
                    head_over_lip_radial=lip_overlap,
                )
            )
    return rows


# =====================================================================================
# hand-calculation models (not tests)
# =====================================================================================


def mech_models(roller_vol, base_vol):
    half = D.half
    mu_req = D.mu_req
    E_pla, nu_pla = 3500.0, 0.36
    Es = {"steel / aluminium handle": (200000.0, 0.30), "wood / plastic handle": (3000.0, 0.38)}
    loads = [5.0, 10.0, 20.0, 30.0]
    L_line = P.T_ROLL - P.ROLL_CH_FRONT - P.ROLL_CH_BACK
    Estar_pp = 1.0 / (2 * (1 - nu_pla**2) / E_pla)
    rows = []
    for W in loads:
        N = W / (2 * mu_req)  # normal force at each handle contact (in plane)
        F_chord = N / math.cos(half)
        row = dict(weight_N=W, weight_kg=W / 9.81, N_handle=N, F_ramp=F_chord)
        for label, (E2, nu2) in Es.items():
            Estar = 1.0 / ((1 - nu_pla**2) / E_pla + (1 - nu2**2) / E2)
            out = {}
            for d in (19.0, 32.0):
                Re = math.sqrt(P.R_ROLL * d / 2)
                a = (3 * N * Re / (4 * Estar)) ** (1 / 3)
                out[d] = dict(a=a, p0=3 * N / (2 * math.pi * a * a))
            row[f"hertz_{label}"] = out
        q = F_chord / L_line
        b = math.sqrt(4 * q * P.R_ROLL / (math.pi * Estar_pp))
        row["ramp_line_load_N_per_mm"] = q
        row["ramp_p0_MPa"] = 2 * q / (math.pi * b)
        # prying of the two housings across the channel (back plate in bending)
        lever = P.BACK_T + 16.0 - P.BACK_T / 2  # worst case: 32 mm handle, contact 23 mm out
        H = D.z_top - D.z_bot
        H_eff = H - 2 * 12.0  # screw countersinks / slot cavity removed from the section
        Zs = H_eff * P.BACK_T**2 / 6
        row["prying_bending_MPa"] = N * lever / Zs + N / (H_eff * P.BACK_T)
        # stub retention if the handle is yanked straight out without lifting (mu = 0.4)
        Fy = 0.4 * N
        row["yank_force_on_stub_N"] = Fy
        row["neck_tension_MPa"] = Fy / (math.pi * P.NECK_R**2)
        row["head_bearing_MPa"] = Fy / (math.pi * (P.HEAD_R**2 - P.LIP_SLOT_HALF**2))
        # screws: the plate pivots on its bottom edge
        zt, zb = G.screw_positions()[0][1], G.screw_positions()[1][1]
        arm_t, arm_b = zt - D.z_bot, zb - D.z_bot
        M = W * (P.BACK_T + 16.0)
        row["top_screw_pullout_N"] = M * arm_t / (arm_t**2 + arm_b**2)
        row["screw_shear_each_N"] = W / 2
        rows.append(row)

    # roller weight and the gravity return
    def mass(vol, wall_frac=0.55, infill=0.25, rho=P.RHO["PLA"]):
        return vol / 1000.0 * rho * (wall_frac + (1 - wall_frac) * infill)

    m_roll = mass(roller_vol)
    g_along = m_roll / 1000 * 9.81 * math.cos(D.delta)
    margins = {f"{mu:.2f}": mu / mu_req for mu in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40)}
    return dict(
        mu_required=mu_req,
        friction_margin_by_mu=margins,
        load_table=rows,
        roller_mass_g_est=m_roll,
        roller_gravity_along_ramp_N=g_along,
        base_mass_g_est=mass(base_vol, 0.45, 0.20),
        line_contact_length=L_line,
    )


# =====================================================================================
# exported-file check (independent of manifold3d: reads the STL bytes back)
# =====================================================================================


def stl_file_check(path):
    """Re-read a binary STL, weld vertices by exact float32 position, and check that every
    edge is shared by exactly two faces in opposite directions; count connected bodies and
    zero-volume bodies (slivers a slicer would report as extra objects)."""
    import struct

    with open(path, "rb") as fh:
        fh.read(80)
        n = struct.unpack("<I", fh.read(4))[0]
        rec = np.frombuffer(fh.read(50 * n), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("x", "<u2")])
    v = rec["v"].reshape(-1, 3)
    uniq, inv = np.unique(v, axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    e = np.vstack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    key = np.sort(e, axis=1)
    _, idx, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    bad_count = int((cnt != 2).sum())
    # orientation: each undirected edge must appear once in each direction
    directed = np.unique(e, axis=0).shape[0]
    bad_orient = int(len(e) - directed)
    # bodies: union-find over faces sharing an edge
    parent = np.arange(len(f))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    face_of_edge = np.tile(np.arange(len(f)), 3)
    order = np.argsort(idx, kind="stable")
    si = idx[order]
    for k in range(1, len(order)):
        if si[k] == si[k - 1]:
            a, b = find(face_of_edge[order[k]]), find(face_of_edge[order[k - 1]])
            if a != b:
                parent[a] = b
    roots = np.array([find(i) for i in range(len(f))])
    bodies = np.unique(roots)
    a, b, c = (uniq[f[:, i]].astype(float) for i in range(3))
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    zero = sum(1 for r in bodies if abs(vol6[roots == r].sum()) / 6 < 1e-3)
    return dict(file=os.path.basename(path), triangles=int(n), non_manifold_edges=bad_count,
                misoriented_edges=bad_orient, bodies=int(len(bodies)), zero_volume_bodies=int(zero),
                volume_mm3=float(vol6.sum() / 6))
