"""Offscreen preview renderer (VTK). Turns CadQuery shapes into PNG images.

    render([(shape, "steel"), (shape2, "red")], "out.png", view="iso")
"""

import math
import os

import vtk

PALETTE = {
    "case":    (0.20, 0.21, 0.23),   # dark graphite (ASA)
    "block":   (0.72, 0.73, 0.75),   # satin aluminium look
    "crank":   (0.55, 0.56, 0.60),
    "steel":   (0.80, 0.81, 0.84),
    "rod":     (0.62, 0.63, 0.66),
    "piston":  (0.86, 0.86, 0.84),
    "bronze":  (0.80, 0.55, 0.25),
    "red":     (0.78, 0.10, 0.10),
    "blue":    (0.15, 0.35, 0.75),
    "gold":    (0.85, 0.68, 0.25),
    "white":   (0.93, 0.93, 0.93),
    "carbon":  (0.12, 0.12, 0.13),
    "orange":  (0.95, 0.45, 0.10),
    "green":   (0.20, 0.60, 0.30),
}

VIEWS = {
    # camera direction (from target towards camera) and up vector
    "iso":    ((1.0, -1.2, 0.9), (0, 0, 1)),
    "iso2":   ((-1.0, 1.1, 0.8), (0, 0, 1)),
    "front":  ((1.0, 0.0, 0.0), (0, 0, 1)),
    "rear":   ((-1.0, 0.0, 0.0), (0, 0, 1)),
    "side":   ((0.0, -1.0, 0.0), (0, 0, 1)),
    "top":    ((0.0, 0.0, 1.0), (0, 1, 0)),
    "bottom": ((0.0, 0.0, -1.0), (0, 1, 0)),
    "frontiso": ((1.0, -0.6, 0.5), (0, 0, 1)),
}


def _polydata(shape, tol=0.08):
    verts, tris = shape.tessellate(tol, 0.3)
    pts = vtk.vtkPoints()
    for v in verts:
        pts.InsertNextPoint(v.x, v.y, v.z)
    cells = vtk.vtkCellArray()
    for t in tris:
        tri = vtk.vtkTriangle()
        for i in range(3):
            tri.GetPointIds().SetId(i, t[i])
        cells.InsertNextCell(tri)
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(pd)
    normals.SetFeatureAngle(35)
    normals.SplittingOn()
    normals.Update()
    return normals.GetOutput()


def render(items, path, view="iso", size=(1400, 1000), title=None, zoom=1.0,
           edges=False, bg=((0.97, 0.97, 0.98), (0.80, 0.82, 0.86))):
    """items: list of (cadquery Shape, colour name or rgb tuple[, opacity])."""
    ren = vtk.vtkRenderer()
    ren.SetBackground(*bg[1])
    ren.SetBackground2(*bg[0])
    ren.GradientBackgroundOn()
    bounds = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    for it in items:
        shape, col = it[0], it[1]
        opacity = it[2] if len(it) > 2 else 1.0
        if shape is None:
            continue
        rgb = PALETTE.get(col, col) if isinstance(col, str) else col
        pd = _polydata(shape)
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(pd)
        a = vtk.vtkActor()
        a.SetMapper(m)
        p = a.GetProperty()
        p.SetColor(*rgb)
        p.SetOpacity(opacity)
        p.SetAmbient(0.18)
        p.SetDiffuse(0.75)
        p.SetSpecular(0.35)
        p.SetSpecularPower(30)
        if edges:
            p.EdgeVisibilityOn()
            p.SetEdgeColor(0.2, 0.2, 0.2)
        ren.AddActor(a)
        b = pd.GetBounds()
        for i in range(3):
            bounds[2 * i] = min(bounds[2 * i], b[2 * i])
            bounds[2 * i + 1] = max(bounds[2 * i + 1], b[2 * i + 1])

    # lights: key, fill, rim
    ren.RemoveAllLights()
    for pos, inten in (((1, -1, 2), 0.85), ((-1.5, 1, 0.5), 0.35), ((0, 2, -1), 0.25)):
        lt = vtk.vtkLight()
        lt.SetLightTypeToCameraLight()
        lt.SetPosition(*pos)
        lt.SetFocalPoint(0, 0, 0)
        lt.SetIntensity(inten)
        ren.AddLight(lt)

    cx = (bounds[0] + bounds[1]) / 2
    cy = (bounds[2] + bounds[3]) / 2
    cz = (bounds[4] + bounds[5]) / 2
    diag = math.sqrt((bounds[1] - bounds[0]) ** 2 + (bounds[3] - bounds[2]) ** 2 + (bounds[5] - bounds[4]) ** 2)
    d, up = VIEWS[view] if isinstance(view, str) else view
    n = math.sqrt(sum(c * c for c in d))
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx + d[0] / n * diag * 2.2, cy + d[1] / n * diag * 2.2, cz + d[2] / n * diag * 2.2)
    cam.SetViewUp(*up)
    cam.SetViewAngle(24)
    ren.ResetCamera(bounds)
    cam.Zoom(1.15 * zoom)

    if title:
        txt = vtk.vtkTextActor()
        txt.SetInput(title)
        tp = txt.GetTextProperty()
        tp.SetFontSize(26)
        tp.SetColor(0.15, 0.15, 0.18)
        tp.BoldOn()
        txt.SetDisplayPosition(24, size[1] - 50)
        ren.AddActor2D(txt)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.Render()
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(win)
    f.Update()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = vtk.vtkPNGWriter()
    w.SetFileName(path)
    w.SetInputConnection(f.GetOutputPort())
    w.Write()
    win.Finalize()
    return path
