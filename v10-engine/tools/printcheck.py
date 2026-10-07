"""Print-readiness check for every exported part.

For each STL in stl/ (already in print orientation) it:
  1. slices it with PrusaSlicer using an H2S-like profile and the part's
     production settings -> print time, filament grams, cost, and the
     slicer's own stability warnings (floating bridge anchors, collapsing
     overhangs, loose extrusions, ...)
  2. runs an independent mesh check:
       * overhangs steeper than 45 deg that are not on the bed
       * bridges (flat ceilings) and their largest unsupported span
  3. writes docs/PRINT_REPORT.md and an overhang heat-map image for any
     part with findings.

    python tools/printcheck.py            # all parts
    python tools/printcheck.py 07_conrod  # one part
"""

import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import trimesh
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
from common import STL_DIR as STL  # noqa: E402   (stl/ for the V8, stl/v10/ for the V10)
PROFILE = os.path.join(ROOT, "tools", "slicer", "h2s_like.ini")
sys.path.insert(0, ROOT)
import config as C  # noqa: E402

MATERIALS = {
    #        density g/cm3, $/kg, max volumetric speed mm3/s
    "ASA":  (1.07, 25.0, 18),
    "PETG": (1.27, 20.0, 14),
    "PLA":  (1.24, 20.0, 21),
}

# production print settings per part (prefix match on the file name).
# ALL production parts are ASA: survives 90+ C (shipping, sunny windows),
# low creep under screw clamps and press fits, dimensionally stable on an
# enclosed printer, UV stable. One material = simpler production.
L = C.LAYER
SETTINGS = [
    # prefix, material, layer, perimeters, infill %, top layers, bottom layers, brim mm
    # LOAD-BEARING parts (spec: >= 4 walls and >= 25 % gyroid): crankcase, valley
    # beam, banks, end plates, crank, rods, pistons, heads, base halves.
    # Cosmetic parts: 3 walls, 15 %.
    ("T1", "PLA", 0.20, 2, 10, 3, 2, 0),        # coupons: PLA first, re-run T3-T6 in ASA before production
    ("T2", "PLA", 0.20, 2, 10, 3, 2, 0),
    ("T4d", "PLA", 0.20, 3, 10, 3, 2, 3),       # tall thin bar: 3 mm brim
    ("T9b", "PLA", 0.20, 2, 0, 3, 2, 3),        # translucent boot: 2 walls, no infill (glow), brim (10 mm footprint)
    ("T10", "PLA", 0.20, 4, 15, 5, 4, 5),       # header flex-test primary: production walls/infill in PLA, 5 mm brim (tall, 14 mm base)
    ("T", "PLA", 0.20, 3, 10, 3, 2, 0),         # crush-rib coupons keep 3 walls like the real parts
    ("01_", "ASA", L["case"], 4, 25, 5, 4, 0),       # crankcase: carries the crank and the engine weight
    ("02_", "ASA", L["beam"], 4, 25, 5, 4, 0),       # valley beam: carries the banks' valley side + rails
    ("03_", "ASA", L["bank"], 4, 25, 5, 4, 0),       # cylinder bank
    ("04_", "ASA", L["plate"], 4, 25, 5, 4, 0),      # end plate: main bearing seat
    ("05_", "ASA", L["crank"], 5, 40, 6, 5, 0),      # crank parts: stiff + some flywheel mass
    ("06_", "ASA", L["crank"], 5, 40, 6, 5, 0),
    ("07_", "ASA", L["crank"], 5, 40, 6, 5, 0),
    ("08_", "ASA", L["rod"], 4, 40, 6, 5, 0),        # con-rod: fine layers for the bearing bore
    ("09_", "ASA", L["piston"], 4, 25, 6, 5, 0),     # piston
    ("10_", "ASA", L["head"], 4, 25, 5, 4, 0),       # head: clamps the rails; top detail is under the cover
    ("11_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),   # cam cover
    ("12_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),   # side panel
    ("13_", "ASA", L["trumpet"], 3, 25, 5, 4, 0),    # trumpet: fine surface
    ("14_", "ASA", L["exhaust"], 3, 20, 5, 4, 0),    # exhaust
    ("15_", "ASA", L["exhaust"], 3, 20, 5, 4, 0),
    ("16_", "ASA", L["coil"], 3, 25, 5, 4, 3),       # coil pack: tall + small footprint -> 3 mm brim
    ("17_", "ASA", L["cosmetic"], 4, 20, 5, 4, 0),   # throttle frame
    ("18_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),   # end cover
    ("19_", "ASA", L["base"], 4, 25, 5, 4, 0),       # base halves: carry the engine
    ("20_", "ASA", L["base"], 4, 25, 5, 4, 0),
    ("21_", "ASA", L["panel"], 3, 15, 4, 3, 0),      # base panels (underneath, never seen)
    ("P1_", "PETG", 0.12, 4, 100, 5, 5, 3),
    ("P2_", "PETG", 0.16, 4, 100, 5, 5, 0),
    ("", "ASA", 0.20, 4, 25, 5, 4, 0),
]
if C.VARIANT == "v8":
    SETTINGS = [
        ("T1", "PLA", 0.20, 2, 10, 3, 2, 0), ("T2", "PLA", 0.20, 2, 10, 3, 2, 0),
        ("T4d", "PLA", 0.20, 3, 10, 3, 2, 3),
        ("T9b", "PLA", 0.20, 2, 0, 3, 2, 3),            # translucent boot: 2 walls, no infill (glow), brim
        ("T10", "PLA", 0.20, 4, 15, 5, 4, 5),           # header flex-test primary, 5 mm brim
        ("T", "PLA", 0.20, 3, 10, 3, 2, 0),
        ("01_", "ASA", L["case"], 4, 25, 5, 4, 0), ("02_", "ASA", L["beam"], 4, 25, 5, 4, 0),
        ("03_", "ASA", L["bank"], 4, 25, 5, 4, 0), ("04_", "ASA", L["plate"], 4, 25, 5, 4, 0),
        ("05_", "ASA", L["crank"], 5, 40, 6, 5, 0), ("06_", "ASA", L["crank"], 5, 40, 6, 5, 0),
        ("07_", "ASA", L["crank"], 5, 40, 6, 5, 0), ("08_", "ASA", L["crank"], 5, 40, 6, 5, 0),
        ("09_", "ASA", L["rod"], 4, 40, 6, 5, 0),       # con-rod
        ("10_", "ASA", L["piston"], 4, 25, 6, 5, 0),    # piston
        ("30", "ASA", L["head"], 4, 25, 5, 4, 0),       # heads (A and mirror B)
        ("31", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),   # valve cover + oil cap
        ("32_", "PETG", 0.16, 2, 0, 3, 2, 3),           # translucent boots (5th filament), brim
        ("33", "ASA", L["exhaust"], 4, 15, 5, 4, 5),    # primaries: production walls, standing, 5 mm brim
        ("34", "ASA", L["cosmetic"], 3, 20, 5, 4, 0),   # flange plates
        ("35", "ASA", L["exhaust"], 3, 10, 5, 4, 0),    # collectors
        ("36", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),   # intake lid / base / throttle body
        ("40_", "ASA", L["base"], 4, 20, 5, 4, 0),      # pan: carries the engine on the brackets
        ("41_", "ASA", L["panel"], 3, 15, 4, 3, 0),     # floor panel
        ("42_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),  # bellhousing
        ("43_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),  # front cover
        ("44_", "ASA", L["cosmetic"], 4, 25, 5, 4, 0),  # damper (turns on the shaft)
        ("45_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),  # accessory module
        ("46_", "ASA", L["base"], 4, 15, 5, 4, 0),      # stand plate
        ("47", "ASA", L["base"], 4, 40, 5, 4, 0),       # brackets: carry the engine
        ("48_", "ASA", L["cosmetic"], 3, 15, 5, 4, 0),  # plinth
        ("P1_", "PETG", 0.12, 4, 100, 5, 5, 3), ("P2", "PETG", 0.16, 4, 100, 5, 5, 0),
    ]


OVERHANG_NZ = -0.74      # normals pointing down more than ~42 deg from vertical walls
BRIDGE_NZ = -0.985       # essentially flat ceilings
BED_TOL = 0.05
MAX_BRIDGE = 25.0        # mm, bridges longer than this are reported
MIN_REGION_AREA = 3.0    # mm2, ignore tiny facets (hole tops, text)


def settings_for(name):
    for row in SETTINGS:
        if name.startswith(row[0]):
            return row[1:]
    raise KeyError(name)


def slice_part(path, name):
    mat, layer, per, infill, top, bot, brim = settings_for(name)
    dens, cost, mvs = MATERIALS[mat]
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "o.gcode")
        cmd = ["prusa-slicer", "--export-gcode", "--load", PROFILE,
               "--layer-height", str(layer), "--first-layer-height", "0.2",
               "--perimeters", str(per), "--fill-density", f"{infill}%",
               "--fill-pattern", "rectilinear" if infill >= 100 else "gyroid",
               "--top-solid-layers", str(top), "--bottom-solid-layers", str(bot),
               "--filament-density", str(dens), "--filament-cost", str(cost),
               "--max-volumetric-speed", str(mvs),
               "--brim-width", str(brim), "--brim-separation", "0.1",
               "--center", "160,160", "--output", out, path]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        log = p.stdout + p.stderr
        warn = ""
        m = re.search(r"Detected print stability issues:\s*\n\s*\n[^\n]*\n([^\n]+)", log)
        if m:
            warn = m.group(1).strip()
        for line in log.splitlines():
            if "outside of the print area" in line or "Empty layers" in line or "error" in line.lower():
                warn += (" | " if warn else "") + line.strip()
        t = g = c = None
        if os.path.exists(out):
            with open(out, errors="ignore") as f:
                tail = f.read()[-20000:]
            mt = re.search(r"estimated printing time \(normal mode\) = ([^\n]+)", tail)
            mg = re.search(r"total filament used \[g\] = ([\d.]+)", tail)
            mc = re.search(r"total filament cost = ([\d.]+)", tail)
            if mt:
                t = _hours(mt.group(1))
            if mg:
                g = float(mg.group(1))
            if mc:
                c = float(mc.group(1))
    return dict(material=mat, layer=layer, perimeters=per, infill=infill, brim=brim, hours=t, grams=g,
                cost=c, slicer_warning=warn)


def _hours(s):
    h = 0.0
    for v, u in re.findall(r"(\d+)([dhms])", s):
        h += int(v) * {"d": 24, "h": 1, "m": 1 / 60, "s": 1 / 3600}[u]
    return h


def mesh_check(path):
    m = trimesh.load(path, force="mesh")
    zmin = m.bounds[0][2]
    n = m.face_normals
    areas = m.area_faces
    centers = m.triangles_center
    on_bed = np.abs(m.triangles[:, :, 2] - zmin).max(axis=1) < BED_TOL
    over = (n[:, 2] < OVERHANG_NZ) & (n[:, 2] >= BRIDGE_NZ) & ~on_bed
    bridge = (n[:, 2] < BRIDGE_NZ) & ~on_bed
    res = dict(overhang_area=float(areas[over].sum()), bridge_regions=[], overhang_regions=[])

    def regions(mask):
        idx = np.nonzero(mask)[0]
        if len(idx) == 0:
            return []
        sub = m.submesh([idx], append=True)
        comps = sub.split(only_watertight=False)
        return comps

    for comp in regions(bridge):
        a = comp.area
        if a < MIN_REGION_AREA:
            continue
        polys = [Polygon(t[:, :2]) for t in comp.triangles if Polygon(t[:, :2]).area > 1e-6]
        if not polys:
            continue
        u = unary_union([p.buffer(0.01) for p in polys])
        try:
            r = shapely.maximum_inscribed_circle(u).length   # line from centre to boundary
        except Exception:
            r = 0.0
        span = 2 * r
        res["bridge_regions"].append(dict(area=round(a, 1), span=round(span, 1),
                                          z=round(float(comp.bounds[0][2] - zmin), 1),
                                          ring=_unanchored_ring(m, u, float(comp.bounds[0][2]))))
    for comp in regions(over):
        if comp.area < MIN_REGION_AREA:
            continue
        ext = comp.bounds[1] - comp.bounds[0]
        res["overhang_regions"].append(dict(area=round(comp.area, 1), size=round(float(max(ext[:2])), 1),
                                            z=round(float(comp.bounds[0][2] - zmin), 1),
                                            worst_deg=round(math.degrees(math.acos(min(1, -comp.face_normals[:, 2].min()))), 0)))
    res["bridge_regions"].sort(key=lambda r: -r["span"])
    res["overhang_regions"].sort(key=lambda r: -r["area"])
    return res, m, over, bridge


def _unanchored_ring(m, poly, z):
    """True if a flat ceiling surrounds a hole whose edge has nothing under it
    (e.g. a counterbore floor around the screw hole): the bridge lines would
    end in mid-air there. An engraved ring or a piston ring groove has solid
    material just inside its inner edge, so it is fine."""
    for g in getattr(poly, "geoms", [poly]):
        if g.geom_type != "Polygon" or not g.interiors:
            continue
        width = 2 * g.area / (g.exterior.length + sum(r.length for r in g.interiors))
        if width < 0.8:                      # a ledge of ~1 extrusion width just prints as an overhang
            continue
        for ring in g.interiors:
            inner = Polygon(ring).buffer(-0.3)
            if inner.is_empty or inner.area < 0.5:
                continue
            ext = inner.exterior if inner.geom_type == "Polygon" else max(inner.geoms, key=lambda q: q.area).exterior
            pts = [ext.interpolate(i / 16.0, normalized=True) for i in range(16)]
            q = np.array([[p.x, p.y, z - 0.15] for p in pts])
            if m.contains(q).mean() < 0.5:
                return True
    return False


def heatmap(m, over, bridge, out_png, title):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import vtk
    from render import VIEWS  # noqa: F401
    colors = np.tile(np.array([200, 200, 205], dtype=np.uint8), (len(m.faces), 1))
    colors[over] = [230, 60, 40]
    colors[bridge] = [240, 170, 30]
    pts = vtk.vtkPoints()
    for v in m.vertices:
        pts.InsertNextPoint(*v)
    polys = vtk.vtkCellArray()
    for f in m.faces:
        polys.InsertNextCell(3)
        for i in f:
            polys.InsertCellPoint(int(i))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(polys)
    arr = vtk.vtkUnsignedCharArray()
    arr.SetNumberOfComponents(3)
    for c in colors:
        arr.InsertNextTuple3(*c)
    pd.GetCellData().SetScalars(arr)
    mp = vtk.vtkPolyDataMapper()
    mp.SetInputData(pd)
    a = vtk.vtkActor()
    a.SetMapper(mp)
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.95, 0.97)
    ren.AddActor(a)
    cam = ren.GetActiveCamera()
    c = m.bounds.mean(axis=0)
    cam.SetFocalPoint(*c)
    cam.SetPosition(c[0] + 300, c[1] - 360, c[2] - 220)    # look from below: overhangs face down
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    txt = vtk.vtkTextActor()
    txt.SetInput(title + "   red = overhang >45deg, orange = bridge (view from below)")
    txt.GetTextProperty().SetFontSize(18)
    txt.GetTextProperty().SetColor(0.1, 0.1, 0.1)
    txt.SetDisplayPosition(15, 670)
    ren.AddViewProp(txt)
    w = vtk.vtkRenderWindow()
    w.SetOffScreenRendering(1)
    w.AddRenderer(ren)
    w.SetSize(1000, 700)
    w.Render()
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(w)
    f.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(out_png)
    wr.SetInputConnection(f.GetOutputPort())
    wr.Write()
    w.Finalize()


def check(names=None, qty=None, write_report=True):
    files = sorted(f for f in os.listdir(STL) if f.endswith(".stl") and not f.startswith("M0"))
    if names:
        files = [f for f in files if any(f.startswith(n) for n in names)]
    rows = []
    for f in files:
        name = f[:-4]
        if not any(name.startswith(pfx) for pfx, *_ in SETTINGS):
            print(f"  skip {name}: no print settings for this engine variant", flush=True)
            continue
        path = os.path.join(STL, f)
        s = slice_part(path, name)
        mres, m, over, bridge = mesh_check(path)
        long_bridges = [b for b in mres["bridge_regions"] if b["span"] > MAX_BRIDGE]
        big_over = [o for o in mres["overhang_regions"] if o["area"] > 25.0]
        rings = [b for b in mres["bridge_regions"] if b.get("ring")]
        mres["rings"] = rings
        flagged = bool(long_bridges or big_over or rings or s["slicer_warning"])
        if flagged:
            os.makedirs(os.path.join(ROOT, "renders", "printcheck"), exist_ok=True)
            heatmap(m, over, bridge, os.path.join(ROOT, "renders", "printcheck", f"{name}.png"), name)
        rows.append((name, s, mres, long_bridges, big_over, flagged))
        print(f"{name:32s} {s['material']:4s} {s['hours'] or 0:6.2f} h {s['grams'] or 0:7.1f} g "
              f"bridges>{MAX_BRIDGE:.0f}mm:{len(long_bridges)} overhangs>25mm2:{len(big_over)} ring-ceilings:{len(rings)} "
              f"{'| ' + s['slicer_warning'] if s['slicer_warning'] else ''}", flush=True)
    if write_report:
        import json
        data = {name: dict(material=s["material"], layer=s["layer"], walls=s["perimeters"], infill=s["infill"],
                           brim=s["brim"], hours=round(s["hours"] or 0, 3), grams=round(s["grams"] or 0, 1),
                           cost=round(s["cost"] or 0, 2), long_bridges=len(lb), big_overhangs=len(bo),
                           ring_ceilings=len(mres.get("rings", [])), slicer_warning=s["slicer_warning"],
                           bridge_spans=[b["span"] for b in lb], overhang_areas=[o["area"] for o in bo])
                for name, s, mres, lb, bo, flagged in rows}
        jpath = os.path.join(ROOT, "docs", "print_results.json")
        if names and os.path.exists(jpath):            # partial run: merge, never drop the other parts
            old = json.load(open(jpath))
            old.update(data)
            data = {k: old[k] for k in sorted(old)}
        with open(jpath, "w") as f:
            json.dump(data, f, indent=1)
        _report(data)
    return rows


def _report(data):
    lines = ["# Print-readiness report", "",
             "Generated by `tools/printcheck.py` from the exported STLs (print orientation).",
             "Times and grams are PrusaSlicer estimates with an H2S-like motion profile "
             "(`tools/slicer/h2s_like.ini`); Bambu Studio is usually within +/-20 %.", "",
             "| Part | Material | Layer | Walls | Infill | Brim | Time (h) | Filament (g) | Cost ($) | Long bridges | Big overhangs | Ring ceilings | Slicer warnings |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, s in data.items():
        lines.append(f"| {name} | {s['material']} | {s['layer']} | {s['walls']} | {s['infill']}% | "
                     f"{s['brim'] or '-'} | {s['hours']:.2f} | {s['grams']:.0f} | {s['cost']:.2f} | "
                     f"{', '.join(str(b) + 'mm' for b in s.get('bridge_spans', [])) or '-'} | "
                     f"{', '.join(str(o) + 'mm2' for o in s.get('overhang_areas', [])) or '-'} | "
                     f"{s['ring_ceilings'] or '-'} | {s['slicer_warning'] or '-'} |")
    lines += ["", "Parts with findings get an image in `renders/printcheck/` (view from below; red = "
              "overhang steeper than 45 deg, orange = flat bridge)."]
    with open(os.path.join(ROOT, "docs", "PRINT_REPORT.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    check(sys.argv[1:] or None)
