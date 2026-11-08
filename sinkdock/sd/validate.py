"""SD-01 SINKDOCK automated checks. Every check returns (name, passed, detail dict)."""

import math

import numpy as np
import trimesh
from manifold3d import JoinType, Manifold

from . import geom as G
from . import printest as E
from .params import (BAYS, BED_MARGIN, BRUSH_CG, BRUSH_G, BRUSH_HANDLE_T, BRUSH_HANDLE_W, BUDGET_G, BUDGET_MIN,
                     BUILD_VOLUMES, CUP_WALLS, P, RECT_SPONGE, SCRUB_DADDY, TIP_LIMIT_DEG,
                     SCRUB_MOMMY, SWELL, TARGET_BED, W, WALLS, cup_y)


def to_trimesh(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    t = np.asarray(mesh.tri_verts).astype(np.int64)
    return trimesh.Trimesh(v, t, process=True)


# -------------------------------------------------------------------------------------
def check_build_volume(m):
    bb = np.array(m.bounding_box()).reshape(2, 3)
    size = bb[1] - bb[0]
    res = {}
    ok_all = True
    for name, vol in BUILD_VOLUMES.items():
        lim = np.array(vol) - np.array([2 * BED_MARGIN, 2 * BED_MARGIN, 0])
        ok = bool(np.all(size <= lim))
        res[name] = dict(fits=ok, limit_xy_after_margin=lim[:2].round(1).tolist())
        if name == TARGET_BED:
            ok_all = ok
    return "Fits the build volume (A1 mini, 5 mm margin each side)", ok_all, dict(size_mm=size.round(2).tolist(), printers=res)


def check_manifold(m):
    tm = to_trimesh(m)
    bodies = len(m.decompose())
    deg = int(np.sum(tm.area_faces < 1e-10))
    ok = m.status().name == "NoError" and bodies == 1 and tm.is_watertight and tm.is_winding_consistent and deg == 0
    return "One closed, manifold, consistently wound body", ok, dict(
        status=m.status().name, bodies=bodies, watertight=tm.is_watertight,
        winding_consistent=tm.is_winding_consistent, degenerate_faces=deg, genus=m.genus(),
        triangles=m.num_tri(), volume_cm3=round(m.volume() / 1000, 3))


def check_files(m, paths):
    """Re-read every exported file and compare it with the model in memory."""
    ref_bb = np.array(m.bounding_box()).reshape(2, 3)
    ref_size = ref_bb[1] - ref_bb[0]
    ref_vol = m.volume()
    out, ok = {}, True
    for p in paths:
        loaded = trimesh.load(p, force="mesh")
        size = loaded.extents
        vol = loaded.volume
        bodies = len(loaded.split(only_watertight=False))
        good = (loaded.is_watertight and bodies == 1 and np.allclose(size, ref_size, atol=0.02)
                and abs(vol - ref_vol) / ref_vol < 2e-3)
        ok &= bool(good)
        out[p.split("/")[-1]] = dict(watertight=bool(loaded.is_watertight), bodies=bodies,
                                     size_mm=np.round(size, 3).tolist(), volume_cm3=round(vol / 1000, 3), ok=bool(good))
    return "Exported STL / 3MF re-read: watertight, one body, same size and volume", ok, out


def check_overhangs(m, limit_deg=45.0, bridge_ok_mm=6.0):
    """Down-facing surfaces steeper than the limit (from vertical), excluding the bed layer.
    Horizontal ceilings narrower than bridge_ok_mm are allowed as short bridges."""
    tm = to_trimesh(m)
    n = tm.face_normals
    z = tm.triangles_center[:, 2]
    ang = np.degrees(np.arcsin(np.clip(-n[:, 2], -1, 1)))  # 0 = vertical wall, 90 = ceiling
    bad = (ang > limit_deg + 0.5) & (z > 0.05)
    area = float(tm.area_faces[bad].sum())
    # classify: each connected patch of bad faces measured by its narrowest plan dimension
    patches = []
    if bad.any():
        sub = tm.submesh([np.where(bad)[0]], append=True)
        for comp in sub.split(only_watertight=False):
            ext = comp.extents
            patches.append(dict(z=round(float(comp.bounds[0][2]), 2), span_mm=round(float(min(ext[0], ext[1])), 2),
                                length_mm=round(float(max(ext[0], ext[1])), 2)))
    unsupported = [p for p in patches if p["span_mm"] > bridge_ok_mm]
    vent = G.vent_overhang_deg(P.vent_w, P.vent_h)
    cupv = G.vent_overhang_deg(P.cup_vent_w, P.cup_vent_h)
    return f"No unsupported overhang > {limit_deg:.0f} deg (bridges <= {bridge_ok_mm:.0f} mm allowed)", not unsupported, dict(
        downfacing_area_mm2=round(area, 1), bridges=patches, unsupported=unsupported,
        divider_vent_overhang_deg=round(vent, 1), cup_vent_overhang_deg=round(cupv, 1))


def check_thin_features(m, min_wall=1.2, layer=0.2, max_patch=1.0):
    """Morphological opening of every layer by min_wall/2: anything that disappears is thinner
    than min_wall. Rounding a square outside corner loses (1 - pi/4) r^2 (about 0.08 mm2 here),
    so a lost patch only counts when it is larger than max_patch mm2."""
    bb = m.bounding_box()
    r = min_wall / 2 - 0.01
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
                worst = dict(area=float(a), z=float(z), xy=q.mean(0).round(1).tolist())
    ok = worst["area"] <= max_patch
    return f"No feature thinner than {min_wall} mm (3 x 0.4 mm nozzle)", ok, dict(
        largest_lost_patch_mm2=round(worst["area"], 3), at=worst,
        designed_min_wall_mm=min(P.wall_inner, P.wall_outer, P.cup_t))


# -------------------------------------------------------------------------------------
def placed_items(size="max"):
    """Proxies of every item at rest, as (name, manifold, bay)."""
    out = []
    pick = 1 if size == "max" else 0
    swell = SWELL if size == "max" else 0.0
    for b in BAYS:
        if b["kind"] == "disc":
            it = SCRUB_MOMMY if b["name"] == "Scrub Mommy" else SCRUB_DADDY
            d, t = it.dia_or_len[pick] + swell, it.thick[pick] + swell
            x, y, z = G.rest_disc(b, d, t)
            out.append((it.name, G.disc_sponge(d, t).translate([x, y, z + 0.05]), b, dict(dia=d, thick=t, centre=(x, y, z))))
        elif b["kind"] == "rect":
            it = RECT_SPONGE
            L, t, h = it.height[pick] + swell, it.thick[pick] + swell, it.dia_or_len[pick] + swell
            x, y, z = G.rest_rect(b, L, t, h)
            out.append((it.name, G.rect_sponge(L, t, h).translate([x, y + 0.05, z + 0.05]), b, dict(len=L, thick=t, height=h)))
        else:
            y0, y1 = cup_y()
            hw, ht = BRUSH_HANDLE_W[1], BRUSH_HANDLE_T[1]  # largest handle envelope considered
            br = G.brush_proxy(handle_w=hw, handle_t=ht, handle_len=180)
            yc = (y0 + y1) / 2
            fz = P.z0 + (yc + ht / 2) * P.tan_y + (hw / 2) * P.tan_x + 0.05  # handle tip resting on the V floor
            out.append((f"Dish brush ({hw:.0f} x {ht:.0f} mm handle envelope)", br.translate([b["xc"], yc, fz]), b,
                        dict(handle=(hw, ht))))
    return out


def check_fit(m):
    res, ok = {}, True
    for name, prox, b, info in placed_items("max"):
        inter = (prox ^ m).volume()
        beside_cup = b["x1"] == CUP_WALLS[0][0] or b["x0"] == CUP_WALLS[1][1]
        narrow = b["w"] - (P.cup_reveal if beside_cup else 0.0)  # narrowest point: beside the cup's reveal
        if b["kind"] in ("disc", "rect"):
            side = (narrow - info["thick"]) / 2
        else:
            side = (b["w"] - info["handle"][0]) / 2
        good = inter < 1.0 and side >= 1.0
        ok &= good
        res[name] = dict(bay_mm=b["w"], narrowest_mm=round(narrow, 2) if b["kind"] != "brush" else b["w"], item_mm=info.get("thick", info.get("handle")), side_clearance_mm=round(side, 2),
                         interference_mm3=round(inter, 3), ok=good)
    return f"Largest researched items (+{SWELL} mm swell) fit with clearance, no interference", ok, res


def check_retention():
    """Front openings narrower than the thinnest researched item, so nothing slides out."""
    res, ok = {}, True
    for b in BAYS:
        if b["kind"] == "brush":
            continue
        it = RECT_SPONGE if b["kind"] == "rect" else SCRUB_MOMMY
        opening = G.bay_opening(b)
        margin = it.thick[0] - opening
        good = margin >= 4.0
        ok &= good
        res[b["name"]] = dict(opening_mm=round(opening, 2), thinnest_item_mm=it.thick[0], margin_mm=round(margin, 2), ok=good)
    res["Dish brush"] = dict(cup_slot_mm=P.cup_slot, note="slot narrower than any plausible handle (>= 18 mm)")
    return "Front openings retain the thinnest sponges (>= 4 mm margin)", ok, res


def check_gutter_lift():
    """The V floor holds each sponge on its two rim edges, leaving an open gutter under it."""
    res = {}
    for b in BAYS:
        if b["kind"] == "brush":
            continue
        it = RECT_SPONGE if b["kind"] == "rect" else SCRUB_DADDY
        t = it.thick[0]
        res[b["name"]] = dict(gutter_depth_under_item_mm=round((t / 2) * P.tan_x, 2))
    ok = all(v["gutter_depth_under_item_mm"] >= 0.6 for v in res.values())
    return "Open gutter under every sponge (>= 0.6 mm)", ok, res


# -------------------------------------------------------------------------------------
def heightmap(m, step=0.5):
    tm = to_trimesh(m)
    bb = tm.bounds
    xs = np.arange(bb[0][0] - 1, bb[1][0] + 1, step)
    ys = np.arange(bb[0][1] - 1, bb[1][1] + 1, step)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    org = np.stack([X.ravel(), Y.ravel(), np.full(X.size, 200.0)], 1)
    dirs = np.tile([0, 0, -1.0], (len(org), 1))
    loc, idx, _ = tm.ray.intersects_location(org, dirs, multiple_hits=False)
    Z = np.full(X.size, np.nan)
    Z[idx] = loc[:, 2]
    return xs, ys, Z.reshape(X.shape)


def check_drainage(m, step=0.5, wet_max_z=12.0):
    """Steepest-descent water routing on the real top surface (ray-cast height map).
    Every wet cell (any surface below wet_max_z: bay floors, cup floor, spouts) must run off the
    part in front of y = 0 (into the sink). Ending in a local minimum is a puddle; running off at
    y >= 0 means water on the counter."""
    xs, ys, Z = heightmap(m, step)
    nx, ny = Z.shape
    wet = np.isfinite(Z) & (Z < wet_max_z)
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    nxt = {}
    fate = np.zeros((nx, ny), dtype=np.int8)  # 0 flows on, 1 sink, 2 counter, 3 puddle
    for i in range(nx):
        for j in range(ny):
            if not wet[i, j]:
                continue
            z = Z[i, j]
            best, bi, off = 0.0, None, False
            for di, dj in nb:
                a, b = i + di, j + dj
                d = step * math.hypot(di, dj)
                if a < 0 or b < 0 or a >= nx or b >= ny or not np.isfinite(Z[a, b]):
                    s, o = 1e6 / d, True    # falls off the part
                else:
                    s, o = (z - Z[a, b]) / d, False
                if s > best + 1e-12:
                    best, bi, off = s, (a, b), o
            # an edge only spills water when no on-part neighbour is lower (it runs on otherwise)
            if off:
                lower = [(i + di, j + dj) for di, dj in nb
                         if 0 <= i + di < nx and 0 <= j + dj < ny and np.isfinite(Z[i + di, j + dj])
                         and Z[i + di, j + dj] < z - 1e-9]
                if lower:
                    bi = min(lower, key=lambda c: Z[c] + 0.0)
                    bi = max(lower, key=lambda c: (z - Z[c]) / (step * math.hypot(c[0] - i, c[1] - j)))
                    off = False
            if bi is None:
                fate[i, j] = 3
            elif off:
                yy = ys[min(max(bi[1], 0), ny - 1)]
                fate[i, j] = 1 if yy < 0 else 2
            else:
                nxt[(i, j)] = bi
    for start in list(nxt):
        if fate[start]:
            continue
        path, cur, seen = [], start, set()
        while fate[cur] == 0:
            if cur in seen:
                fate[cur] = 3
                break
            seen.add(cur)
            path.append(cur)
            cur = nxt[cur]
        for c in path:
            fate[c] = fate[cur]
    n_wet = int(wet.sum())
    n_sink = int((fate == 1).sum())
    n_counter = int((fate == 2).sum())
    n_puddle = int((fate == 3).sum())
    # where do the puddle / counter cells sit?
    bad = np.argwhere((fate == 2) | (fate == 3))
    where = []
    for i, j in bad[:12]:
        where.append((round(float(xs[i]), 1), round(float(ys[j]), 1), round(float(Z[i, j]), 2)))
    # outlets: x extents of the water leaving each spout
    ok = n_counter == 0 and n_puddle == 0
    return "Water on every floor surface runs off the spouts into the sink (no puddles, none onto the counter)", ok, dict(
        grid_mm=step, wet_cells=n_wet, to_sink=n_sink, to_counter=n_counter, puddle=n_puddle, first_bad_cells=where,
        _maps=(xs, ys, Z, fate))


def check_openings(m):
    """The drain path through each bay front (between the returns) and the cup slots is open at
    floor level: measure the clear width of every gap in a slice just above the floor."""
    res, ok = {}, True
    for b in BAYS:
        if b["kind"] == "brush":
            y0, y1 = cup_y()
            for label, yy in (("cup front slot", y0 - P.cup_t / 2), ("cup back slot", y1 + P.cup_t / 2)):
                zf = P.z0 + yy * P.tan_y + (P.cup_slot / 2) * P.tan_x + 0.4
                gap = _gap_at(m, b, yy, zf)
                good = gap >= P.cup_slot - 0.15
                ok &= good
                res[f"{b['name']} {label}"] = dict(clear_mm=round(gap, 2), ok=good)
            continue
        yy = P.ret_t / 2
        zf = P.z0 + yy * P.tan_y + G.bay_opening(b) / 2 * P.tan_x + 0.4
        gap = _gap_at(m, b, yy, zf)
        good = gap >= G.bay_opening(b) - 0.15  # 0.05 mm sampling at each edge
        ok &= good
        res[b["name"]] = dict(clear_mm=round(gap, 2), designed_mm=round(G.bay_opening(b), 2), ok=good)
    return "Drain openings are clear at floor level", ok, res


def _gap_at(m, b, y, z):
    """Clear width along x around the bay centre at (y, z)."""
    xs = np.arange(b["x0"] - 2, b["x1"] + 2, 0.05)
    tm = to_trimesh(m)
    inside = tm.contains(np.stack([xs, np.full_like(xs, y), np.full_like(xs, z)], 1))
    c = np.argmin(np.abs(xs - b["xc"]))
    if inside[c]:
        return 0.0
    lo = c
    while lo > 0 and not inside[lo - 1]:
        lo -= 1
    hi = c
    while hi < len(xs) - 1 and not inside[hi + 1]:
        hi += 1
    return float(xs[hi] - xs[lo])


# -------------------------------------------------------------------------------------
def brush_lean_offsets(p=P):
    """Worst-case horizontal offset of the brush's centre of mass from the cup axis.
    The handle tip sits against one wall at the floor and the handle leans on the opposite rim:
    the axis runs from (c - g/2, 0) to (c + g/2, h), g = cup bore - handle, h = rim above the
    floor, so at the CG height the offset is g * (CG/h - 1/2)."""
    y0, y1 = cup_y(p)
    h = p.cup_h - (p.z0 + ((y0 + y1) / 2) * p.tan_y)
    gy = p.cup_in_y - BRUSH_HANDLE_T[0]
    gx = p.bay_brush - BRUSH_HANDLE_W[0]
    k = BRUSH_CG / h - 0.5
    return gy * k, gx * k, math.degrees(math.atan2(gy, h)), math.degrees(math.atan2(gx, h))


def check_stability(m, est):
    """Static tip-over angles. Support polygon = the body behind y = 0 (the spouts are assumed to
    overhang the sink, so they give no support). Dock mass from the print estimate at the
    centroid of the solid model; sponge masses wet; the brush at its worst lean in each direction."""
    tm = to_trimesh(m)
    c = tm.center_mass
    y0, y1 = cup_y()
    cy_cup = (y0 + y1) / 2
    bx = [b for b in BAYS if b["kind"] == "brush"][0]["xc"]
    dy, dx, ay, ax_ = brush_lean_offsets()
    sponge = {}
    for name, prox, b, info in placed_items("max"):
        if b["kind"] == "brush":
            continue
        g = 45.0 if b["kind"] == "disc" else 25.0
        cc = to_trimesh(prox).center_mass
        sponge[name] = (g, cc[0], cc[1], cc[2])
    dock = (est["grams"], c[0], c[1], c[2])
    leans = {"back": (bx, cy_cup + dy), "forward": (bx, cy_cup - dy), "left": (bx - dx, cy_cup), "right": (bx + dx, cy_cup)}
    out, ok = {}, True
    worst_all = 90.0
    for loadname, extra in (("empty dock + brush", {}), ("fully loaded (wet sponges)", sponge)):
        for lean, (bxx, byy) in leans.items():
            L = {"dock": dock, "brush": (BRUSH_G, bxx, byy, BRUSH_CG), **extra}
            M = sum(v[0] for v in L.values())
            cx = sum(v[0] * v[1] for v in L.values()) / M
            cyy = sum(v[0] * v[2] for v in L.values()) / M
            cz = sum(v[0] * v[3] for v in L.values()) / M
            tips = {"back": math.degrees(math.atan2(P.D - cyy, cz)), "forward": math.degrees(math.atan2(cyy, cz)),
                    "left": math.degrees(math.atan2(cx, cz)), "right": math.degrees(math.atan2(W - cx, cz))}
            t = tips[lean]
            worst_all = min(worst_all, t)
            key = f"{loadname}, brush leaning {lean}"
            out[key] = dict(total_g=round(M), cg_mm=[round(cx, 1), round(cyy, 1), round(cz, 1)],
                            tip_angle_toward_lean_deg=round(t, 1))
    ok = worst_all >= TIP_LIMIT_DEG
    out["brush_assumptions"] = dict(mass_g=BRUSH_G, cg_above_tip_mm=BRUSH_CG, handle_thickness_min_mm=BRUSH_HANDLE_T[0],
                                    max_lean_front_back_deg=round(ay, 1), max_lean_side_deg=round(ax_, 1),
                                    cg_offset_front_back_mm=round(dy, 1), cg_offset_side_mm=round(dx, 1))
    out["worst_tip_angle_deg"] = round(worst_all, 1)
    out["criterion"] = f">= {TIP_LIMIT_DEG} deg in every direction (IEC 60335-1 cl. 20.1 incline angle)"
    return f"Does not tip on a {TIP_LIMIT_DEG:.0f} deg incline, empty or loaded, brush at its worst lean", ok, out


def check_budget(est_pla, est_petg):
    ok = est_pla["grams"] <= BUDGET_G and est_pla["minutes"] <= BUDGET_MIN and est_petg["grams"] <= BUDGET_G
    return f"Filament <= {BUDGET_G:.0f} g, print time <= {BUDGET_MIN:.0f} min (estimate, PLA; PETG time reported)", ok, dict(
        PLA=dict(grams=round(est_pla["grams"], 1), minutes=round(est_pla["minutes"], 1),
                 grams_range=[round(v, 1) for v in est_pla["grams_range"]],
                 minutes_range=[round(v) for v in est_pla["minutes_range"]]),
        PETG=dict(grams=round(est_petg["grams"], 1), minutes=round(est_petg["minutes"], 1),
                  grams_range=[round(v, 1) for v in est_petg["grams_range"]],
                  minutes_range=[round(v) for v in est_petg["minutes_range"]],
                  meets_time_target=est_petg["minutes"] <= BUDGET_MIN),
        breakdown_cm3={k: round(v, 2) for k, v in est_pla["breakdown_cm3"].items()},
        layers=est_pla["layers"])


def run_all(m, files):
    est_pla = E.estimate(m, E.PLA)
    est_petg = E.estimate(m, E.PETG)
    checks = [
        check_build_volume(m),
        check_manifold(m),
        check_files(m, files),
        check_overhangs(m),
        check_thin_features(m),
        check_fit(m),
        check_retention(),
        check_gutter_lift(),
        check_openings(m),
        check_drainage(m),
        check_stability(m, est_pla),
        check_budget(est_pla, est_petg),
    ]
    return checks, est_pla, est_petg
