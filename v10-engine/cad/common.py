"""Shared CadQuery helpers: placement, export and small feature builders."""

import math
import os
import sys

import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config as C  # noqa: E402

STL_DIR = os.path.join(ROOT, "stl")
RENDER_DIR = os.path.join(ROOT, "renders")
DRAWING_DIR = os.path.join(ROOT, "drawings")


def polar(r, deg):
    """(y, z) of a point at radius r and crank angle deg (from +Z towards +Y)."""
    a = math.radians(deg)
    return r * math.sin(a), r * math.cos(a)


def rot_x(shape, deg):
    """Rotate so that a feature at crank angle psi ends up at psi + deg."""
    return shape.rotate((0, 0, 0), (1, 0, 0), -deg)


def rot_z(shape, deg):
    return shape.rotate((0, 0, 0), (0, 0, 1), deg)


def move(shape, x=0.0, y=0.0, z=0.0):
    return shape.translate(cq.Vector(x, y, z))


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    """Solid cylinder along X from x0 to x1 centred at (y, z)."""
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def d_hole_x(d, flat_from_center, x0, x1, y, z, flat_dir_deg):
    """D-shaped hole along X. The flat is perpendicular to flat_dir_deg
    (crank-angle convention) at flat_from_center from the hole centre."""
    c = cyl_x(d / 2, x0, x1, y, z)
    # keep-out box that removes the part of the circle beyond the flat
    big = d
    cut = box(x0 - 1, x1 + 1, -big, big, flat_from_center, flat_from_center + big)
    cut = rot_x(cut, flat_dir_deg)  # box is built pointing at +Z (angle 0)
    cut = move(cut, 0, y, z)
    return c.cut(cut)


def export(shape, name):
    """Write <name>.stl and <name>.step into the stl folder."""
    os.makedirs(STL_DIR, exist_ok=True)
    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    stl = os.path.join(STL_DIR, name + ".stl")
    step = os.path.join(STL_DIR, name + ".step")
    cq.exporters.export(cq.Workplane().add(shape), stl, tolerance=0.02, angularTolerance=0.15)
    cq.exporters.export(cq.Workplane().add(shape), step)
    return stl, step


def bbox_size(shape):
    bb = shape.BoundingBox()
    return bb.xlen, bb.ylen, bb.zlen


def check_printable_size(shape, name, limit=300.0):
    sx, sy, sz = bbox_size(shape)
    ok = max(sx, sy, sz) <= limit
    return ok, f"{name}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm {'OK' if ok else 'TOO BIG'}"
