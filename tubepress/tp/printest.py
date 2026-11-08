"""
A slicer-like filament and print-time estimator (manifold3d cross-sections).

NOT a slicer. No slicer could be installed in the build environment, so this slices the
part layer by layer and models what a slicer does with each layer:

  * wall loops: the band between the layer outline and its inward offset by loops x line width
  * top / bottom shells: core area not covered by the layers `top` above and `bottom` below
  * sparse infill: the rest of the core, at the infill density

Time = path length / effective speed for each feature, plus a fixed per-layer overhead
(travel, retraction, z move, wipe) and a slower first layer. Speeds default to the
Bambu Lab "0.20mm Standard" process for the A1 mini, capped by the filament's maximum
volumetric flow, then derated for acceleration. All of that is an assumption, so the
result is reported as a range, and the README says to confirm it in the slicer.
"""

from dataclasses import dataclass

from manifold3d import JoinType


@dataclass(frozen=True)
class Process:
    name: str = "0.20 mm Standard (0.4 nozzle)"
    layer: float = 0.20
    first_layer: float = 0.20
    lw: float = 0.42
    walls: int = 2
    top: int = 5
    bottom: int = 3
    infill: float = 0.15
    v_outer: float = 200.0
    v_inner: float = 300.0
    v_sparse: float = 270.0
    v_solid: float = 250.0
    v_first: float = 50.0
    accel_eff_walls: float = 0.50   # short, curved wall segments rarely reach set speed
    accel_eff_fill: float = 0.65
    layer_overhead_s: float = 3.0


@dataclass(frozen=True)
class Filament:
    name: str
    density: float      # g/cm3
    max_flow: float     # mm3/s


PLA = Filament("PLA (Bambu PLA Basic class)", 1.24, 21.0)
PETG = Filament("PETG (Bambu PETG Basic class)", 1.27, 13.0)


def _perim(cs_):
    tot = 0.0
    for poly in cs_.to_polygons():
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            tot += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return tot


def estimate(m, fil=PETG, pr=Process()):
    bb = m.bounding_box()
    zmin, zmax = bb[2], bb[5]
    n = int(round((zmax - zmin) / pr.layer))
    zs = [zmin + (i + 0.5) * pr.layer for i in range(n)]
    secs = [m.slice(z) for z in zs]
    j = JoinType.Miter
    vol_wall = vol_solid = vol_sparse = 0.0
    t = 0.0
    xs = pr.lw * pr.layer
    cap = fil.max_flow / xs  # mm/s ceiling from volumetric flow
    sp = {k: min(getattr(pr, k), cap) for k in ("v_outer", "v_inner", "v_sparse", "v_solid", "v_first")}
    per_layer = []
    for i, s in enumerate(secs):
        a = s.area()
        if a <= 0:
            continue
        core = s.offset(-pr.walls * pr.lw, j)
        a_core = core.area()
        a_wall = a - a_core
        outer_len = _perim(s.offset(-0.5 * pr.lw, j))
        wall_len = a_wall / pr.lw
        inner_len = max(wall_len - outer_len, 0.0)
        if i < pr.bottom or i >= n - pr.top:
            solid = core
        else:
            cover = s
            for k in list(range(i - pr.bottom, i)) + list(range(i + 1, i + 1 + pr.top)):
                cover = cover ^ secs[k]
            sparse = core ^ cover
            solid = core - sparse
        a_solid = solid.area()
        a_sparse = max(a_core - a_solid, 0.0)
        vol_wall += a_wall * pr.layer
        vol_solid += a_solid * pr.layer
        vol_sparse += a_sparse * pr.layer * pr.infill
        len_solid = a_solid / pr.lw
        len_sparse = a_sparse * pr.infill / pr.lw
        if i == 0:
            lt = (wall_len + len_solid + len_sparse) / (sp["v_first"] * pr.accel_eff_fill)
        else:
            lt = outer_len / (sp["v_outer"] * pr.accel_eff_walls) + inner_len / (sp["v_inner"] * pr.accel_eff_walls) \
                + len_solid / (sp["v_solid"] * pr.accel_eff_fill) + len_sparse / (sp["v_sparse"] * pr.accel_eff_fill)
        lt += pr.layer_overhead_s
        t += lt
        per_layer.append((zs[i], lt))
    vol = vol_wall + vol_solid + vol_sparse  # mm3
    grams = vol / 1000.0 * fil.density
    return dict(
        filament=fil.name, process=pr.name, layers=n,
        volume_cm3=vol / 1000.0, grams=grams, minutes=t / 60.0,
        grams_range=(grams * 0.92, grams * 1.10), minutes_range=(t / 60.0 * 0.8, t / 60.0 * 1.25),
        breakdown_cm3=dict(walls=vol_wall / 1000, solid=vol_solid / 1000, sparse=vol_sparse / 1000),
        solid_model_cm3=m.volume() / 1000.0,
    )
