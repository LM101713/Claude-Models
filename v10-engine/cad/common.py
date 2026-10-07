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


def safe_clean(shape):
    """shape.clean() merges coplanar faces, but on some complex booleans OCC
    returns an invalid solid. Keep the cleaned result only if it is valid."""
    try:
        c = shape.clean()
        if c.isValid():
            return c
    except Exception:
        pass
    return shape


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


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    return cq.Solid.makeCylinder(r, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


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


# ---------------------------------------------------------------------------
# Crush-rib press fits (see CRUSH in config.py)
# ---------------------------------------------------------------------------
def crush_params(d_nom, fit):
    n, interf = C.CRUSH[fit]
    bore = d_nom + C.HOLE_COMP + C.CRUSH_RELIEF
    rr = min(C.CRUSH_RIB_R, d_nom * 0.12)          # small holes get smaller ribs
    tip_r = (d_nom - interf) / 2
    return n, bore, rr, tip_r + rr


def _lead_cone(r, x_face, inward, axis):
    """45 deg entry chamfer, 0.4 mm, at an entry face. axis 'x' or 'z'."""
    h = 0.4
    d = cq.Vector(inward, 0, 0) if axis == "x" else cq.Vector(0, 0, inward)
    p = cq.Vector(x_face - inward * 0.01, 0, 0) if axis == "x" else cq.Vector(0, 0, x_face - inward * 0.01)
    return cq.Solid.makeCone(r + h, r, h + 0.01, p, d)


def crush_x(d_nom, x0, x1, y, z, fit, entry="both", phase=0.0):
    """Crush-rib hole cutter along X from x0 to x1 at (y, z).
    entry: which end(s) the part is pressed in from ('lo', 'hi', 'both')."""
    n, bore, rr, cr = crush_params(d_nom, fit)
    cut = cyl_x(bore / 2, x0, x1, y, z)
    lead = C.CRUSH_LEAD
    r0 = x0 + (lead if entry in ("lo", "both") else -0.1)
    r1 = x1 - (lead if entry in ("hi", "both") else -0.1)
    for i in range(n):
        ry, rz = polar(cr, phase + i * 360.0 / n)
        cut = cut.cut(cyl_x(rr, r0, r1, y + ry, z + rz))
    if entry in ("lo", "both"):
        cut = cut.fuse(move(_lead_cone(bore / 2, x0, 1, "x"), 0, y, z))
    if entry in ("hi", "both"):
        cut = cut.fuse(move(_lead_cone(bore / 2, x1, -1, "x"), 0, y, z))
    return cut


def crush_z(d_nom, z0, z1, x, y, fit, entry="both", phase=0.0):
    """Crush-rib hole cutter along Z (see crush_x)."""
    n, bore, rr, cr = crush_params(d_nom, fit)
    cut = cyl_z(bore / 2, z0, z1, x, y)
    lead = C.CRUSH_LEAD
    r0 = z0 + (lead if entry in ("lo", "both") else -0.1)
    r1 = z1 - (lead if entry in ("hi", "both") else -0.1)
    for i in range(n):
        a = math.radians(phase + i * 360.0 / n)
        cut = cut.cut(cyl_z(rr, r0, r1, x + cr * math.cos(a), y + cr * math.sin(a)))
    if entry in ("lo", "both"):
        cut = cut.fuse(move(_lead_cone(bore / 2, z0, 1, "z"), x, y, 0))
    if entry in ("hi", "both"):
        cut = cut.fuse(move(_lead_cone(bore / 2, z1, -1, "z"), x, y, 0))
    return cut


def crush_d_x(d_nom, flat_depth, x0, x1, y, z, flat_dir_deg, entry="lo"):
    """D-hole along X for a D-flat pin. The flat (facing flat_dir_deg) is the
    angular reference; two crush ribs opposite it (at +/-55 deg) push the pin's
    flat hard onto it, so the joint has no rotational play whatever the print
    tolerance."""
    n, bore, rr, cr = crush_params(d_nom, "dpin_6")
    flat = d_nom / 2 - flat_depth + 0.05 + C.HOLE_COMP / 2
    cut = d_hole_x(bore, flat, x0, x1, y, z, flat_dir_deg)
    lead = C.CRUSH_LEAD
    r0 = x0 + (lead if entry in ("lo", "both") else -0.1)
    r1 = x1 - (lead if entry in ("hi", "both") else -0.1)
    for a in (flat_dir_deg + 180.0 - 55.0, flat_dir_deg + 180.0 + 55.0):
        ry, rz = polar(cr, a)
        cut = cut.cut(cyl_x(rr, r0, r1, y + ry, z + rz))
    return cut


def bridge_step(wide_cutter, r_small, at, axis, up, layer, slot_deg=0.0):
    """Extra cutter for a hole that narrows while printing upwards (a screw
    counterbore or pin socket whose floor is a ceiling on the printer).

    A flat ring-shaped ceiling cannot be bridged cleanly: the bridge lines end
    in mid-air at the narrow hole. This turns it into two stages of anchored
    bridges, 2 layers each (the usual "bridged counterbore" technique):
      stage 1: a slot as wide as the narrow hole across the whole wide hole
               (the slicer bridges the two halves wall to wall);
      stage 2: a square as wide as the narrow hole (bridged across the slot).
    wide_cutter: cutter of the wide hole (its cross-section is reused)
    at:  (x, y, z) of the step-plane centre;  axis 'x' or 'z';  up = +1 / -1
    layer: the part's print layer height."""
    h = 2.0 * layer
    slot = rot_z(box(-60, 60, -r_small, r_small, -0.01, h), slot_deg)
    square = box(-r_small, r_small, -r_small, r_small, -0.01, 2.0 * h)

    def place(sh):
        if axis == "z":
            sh = sh if up > 0 else sh.rotate((0, 0, 0), (1, 0, 0), 180)
        else:
            sh = sh.rotate((0, 0, 0), (0, 1, 0), 90 if up > 0 else -90)
        return move(sh, *at)
    d = cq.Vector(up * 2.0 * h, 0, 0) if axis == "x" else cq.Vector(0, 0, up * 2.0 * h)
    stage1 = place(slot).intersect(wide_cutter.translate(d))
    return stage1.fuse(place(square))


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
