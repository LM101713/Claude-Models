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
STL = os.path.join(ROOT, "stl")
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
SETTINGS = [
    # prefix, material, layer, perimeters, infill %, top layers, bottom layers
    ("00_", "PLA", 0.20, 3, 15, 4, 3),
    ("01_", "ASA", 0.20, 4, 15, 5, 4),     # crankcase: mostly hidden, mass not needed
    ("02_", "ASA", 0.20, 4, 25, 5, 4),     # valley beam: carries the banks' valley side
    ("03_", "ASA", 0.20, 4, 20, 5, 4),     # cylinder bank
    ("04_", "ASA", 0.20, 4, 25, 5, 4),     # end plate: bearing seat
    ("05_", "ASA", 0.16, 5, 40, 6, 5),     # crank parts: stiff + some flywheel mass
    ("06_", "ASA", 0.16, 5, 40, 6, 5),
    ("07_", "ASA", 0.16, 5, 40, 6, 5),
    ("08_", "ASA", 0.12, 4, 40, 6, 5),     # con-rod: fine layers for the bearing bore
    ("09_", "ASA", 0.12, 4, 25, 6, 5),     # piston: fine layers, visible
    ("10_", "ASA", 0.16, 4, 20, 6, 5),     # head: visible detail
    ("11_", "ASA", 0.20, 3, 15, 5, 4),     # cam cover: cosmetic
    ("12_", "ASA", 0.20, 3, 15, 5, 4),     # side panel: cosmetic
    ("13_", "ASA", 0.12, 3, 25, 5, 4),     # trumpet: fine surface
    ("14_", "ASA", 0.16, 3, 20, 5, 4),     # exhaust
    ("15_", "ASA", 0.16, 3, 20, 5, 4),
    ("16_", "ASA", 0.16, 3, 25, 5, 4),     # coil pack
    ("17_", "ASA", 0.20, 4, 20, 5, 4),     # throttle frame
    ("18_", "ASA", 0.20, 3, 15, 5, 4),     # end cover: cosmetic
    ("19_", "ASA", 0.20, 4, 15, 5, 4),     # base halves: big, mostly shell
    ("20_", "ASA", 0.20, 4, 15, 5, 4),
    ("21_", "ASA", 0.20, 3, 15, 4, 3),     # base panels
    ("P1_", "PETG", 0.12, 4, 100, 5, 5),
    ("P2_", "PETG", 0.16, 4, 100, 5, 5),
    ("", "ASA", 0.20, 4, 25, 5, 4),
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
    mat, layer, per, infill, top, bot = settings_for(name)
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
    return dict(material=mat, layer=layer, perimeters=per, infill=infill, hours=t, grams=g,
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
                                          z=round(float(comp.bounds[0][2] - zmin), 1)))
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
        path = os.path.join(STL, f)
        s = slice_part(path, name)
        mres, m, over, bridge = mesh_check(path)
        long_bridges = [b for b in mres["bridge_regions"] if b["span"] > MAX_BRIDGE]
        big_over = [o for o in mres["overhang_regions"] if o["area"] > 25.0]
        flagged = bool(long_bridges or big_over or s["slicer_warning"])
        if flagged:
            os.makedirs(os.path.join(ROOT, "renders", "printcheck"), exist_ok=True)
            heatmap(m, over, bridge, os.path.join(ROOT, "renders", "printcheck", f"{name}.png"), name)
        rows.append((name, s, mres, long_bridges, big_over, flagged))
        print(f"{name:32s} {s['material']:4s} {s['hours'] or 0:6.2f} h {s['grams'] or 0:7.1f} g "
              f"bridges>{MAX_BRIDGE:.0f}mm:{len(long_bridges)} overhangs>25mm2:{len(big_over)} "
              f"{'| ' + s['slicer_warning'] if s['slicer_warning'] else ''}", flush=True)
    if write_report:
        _report(rows, qty or {})
    return rows


def _report(rows, qty):
    lines = ["# Print-readiness report", "",
             "Generated by `tools/printcheck.py` from the exported STLs (print orientation).",
             "Times and grams are PrusaSlicer estimates with an H2S-like motion profile "
             "(`tools/slicer/h2s_like.ini`); Bambu Studio is usually within +/-20 %.", "",
             "| Part | Material | Layer | Walls | Infill | Time (h) | Filament (g) | Cost ($) | Long bridges | Big overhangs | Slicer warnings |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, s, mres, lb, bo, flagged in rows:
        lines.append(f"| {name} | {s['material']} | {s['layer']} | {s['perimeters']} | {s['infill']}% | "
                     f"{(s['hours'] or 0):.2f} | {(s['grams'] or 0):.0f} | {(s['cost'] or 0):.2f} | "
                     f"{', '.join(str(b['span']) + 'mm' for b in lb) or '-'} | "
                     f"{', '.join(str(o['area']) + 'mm2' for o in bo) or '-'} | {s['slicer_warning'] or '-'} |")
    lines += ["", "Parts with findings get an image in `renders/printcheck/` (view from below; red = "
              "overhang steeper than 45 deg, orange = flat bridge)."]
    with open(os.path.join(ROOT, "docs", "PRINT_REPORT.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    check(sys.argv[1:] or None)
