"""Stock-car V8 front end:

  43 front cover      - magnetic shell on the front end plate (3 magnets, V10
                        pattern) over the 60T pulley and belt, with a clearance
                        hole for the front main shaft; prints front face down
  44 harmonic damper  - turns with the crank: crush-fit D-bore on the longer
                        front shaft (M02F) outside the cover; prints flat
  45 accessory module - ONE static printed part: back plate, water-pump
                        pulley + snout, alternator body + pulley, idler, and
                        the flat belt band around them and around the damper
                        (1.2 mm off it); held on the cover by 3 magnets; prints
                        on its back plate, everything else stands up

Engine frame, +X = front.
"""

import math

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from common import C, box, crush_d_x, crush_x, cyl_x, safe_clean

FC = C.FRONT_COVER
DM = C.DAMPER
AC = C.ACCESSORY
X0, X1 = C.COVER_X0, C.COVER_X1


def _outline_wire(off, x):
    """Rounded cover outline in the YZ plane at x, offset inwards by off."""
    pts = []
    for z, hw in FC["outline"]:
        pts.append((hw - off, z + (off if z == FC["outline"][0][0] else 0)))
    top_z = FC["outline"][-1][0] - off
    pts[-1] = (FC["outline"][-1][1] - off, top_z)
    right = pts
    left = [(-y, z) for y, z in reversed(right)]
    poly = [cq.Vector(x, y, z) for y, z in right + left]
    w = cq.Wire.makePolygon(poly, close=True)
    return w.fillet2D(max(1.0, FC["r"] - off), w.Vertices())


def _outline_solid(off, x0, x1):
    f = cq.Face.makeFromWires(_outline_wire(off, x0))
    return cq.Solid.extrudeLinear(f, cq.Vector(x1 - x0, 0, 0))


def front_cover():
    w = FC["wall"]
    outer = _outline_solid(0.0, X0, X1)
    outer = cq.Workplane().add(outer).faces(">X").edges().chamfer(2.0).val()
    cover = outer.cut(_outline_solid(w, X0 - 1, X1 - w))
    # cast-look parting groove and bolt dimples RECESSED into the front face (it prints face-down, flat)
    groove = _outline_solid(4.0, X1 - 1.0, X1 + 1).cut(_outline_solid(5.2, X1 - 2, X1 + 2))
    cover = cover.cut(groove)
    wire = _outline_wire(2.0, X1)
    for i in range(FC["n_bolts"]):
        p = wire.positionAt(i / FC["n_bolts"] + 0.03)
        cover = cover.cut(cyl_x(FC["bolt_r"], X1 - 1.0, X1 + 1, p.y, p.z))
    # shaft clearance hole
    cover = cover.cut(cyl_x(C.SHAFT_D / 2 + FC["shaft_clear"], X1 - w - 1, X1 + 2))
    # magnet pillars on the end plate pattern (same 3 as the V10 cover)
    for y, z in C.COVER_MAGNETS:
        pil = cyl_x(C.COVER_PILLAR_R, X0, X1 - w + 0.1, y, z)
        ang = math.degrees(math.atan2(y, z))
        pil = pil.fuse(cq.Workplane().add(box(X0, X1 - w + 0.1, -C.COVER_PILLAR_R, C.COVER_PILLAR_R, 0, 8)).val()
                       .rotate((0, 0, 0), (1, 0, 0), -ang).translate(cq.Vector(0, y, z)))
        cover = cover.fuse(pil.intersect(_outline_solid(0.0, X0, X1)))
        cover = cover.cut(crush_x(C.MAGNET["d"], X0 - 0.5, X0 + C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR, y, z, "magnet_6", entry="lo"))
    # bosses inside the front wall for the accessory module's magnets
    for y, z in FC["module_magnets"]:
        boss = cyl_x(C.COVER_PILLAR_R + 0.5, X1 - w - 5.0, X1 - w + 0.1, y, z)
        cover = cover.fuse(boss)
        cover = cover.cut(crush_x(C.MAGNET["d"], X1 - C.MAGNET["h"] - C.MAGNET_DEPTH_CLEAR, X1 + 0.5, y, z, "magnet_6", entry="hi"))
    return safe_clean(cover)


def print_cover(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90)     # front face on the bed (bolt heads/rim up? no: face down is flat)


def damper():
    x0, x1 = C.DAMPER_X0, C.DAMPER_X0 + DM["t"]
    d = cyl_x(DM["d"] / 2, x0, x1)
    d = cq.Workplane().add(d).faces(">X").edges().chamfer(1.5).val()
    d = cq.Workplane().add(d).faces("<X").edges().chamfer(1.0).val()
    # "rubber ring" groove on the front face and the hub step
    d = d.cut(cyl_x(DM["groove_r"] + DM["groove_w"] / 2, x1 - DM["groove_d"], x1 + 1).cut(
        cyl_x(DM["groove_r"] - DM["groove_w"] / 2, x1 - DM["groove_d"] - 1, x1 + 2)))
    hub = cyl_x(DM["hub_d"] / 2, x1 - 0.1, x1 + DM["hub_h"])
    hub = cq.Workplane().add(hub).faces(">X").edges().chamfer(0.8).val()
    d = d.fuse(hub)
    for i in range(DM["n_holes"]):
        a = math.radians(i * 360.0 / DM["n_holes"] + 30.0)
        d = d.cut(cyl_x(DM["hole_r"], x1 - 2.0, x1 + 3, 0.6 * DM["d"] / 2 * math.cos(a), 0.6 * DM["d"] / 2 * math.sin(a)))
    # timing mark notch on the rim
    d = d.cut(box(x1 - 3.0, x1 + 3, -0.8, 0.8, DM["d"] / 2 - 1.5, DM["d"] / 2 + 1))
    # D-bore with crush ribs on the shaft flat (flat faces +Z at crank angle 0)
    d = d.cut(crush_d_x(C.SHAFT_D, C.SHAFT_FLAT_DEPTH, x0 - 1, x1 + 3, 0, 0, 0.0, entry="both"))
    return safe_clean(d)


def print_damper(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90).translate((0, 0, 0))   # back face down


def _band_polygon(off):
    """Convex hull around the damper and the accessory pulleys, in the YZ plane."""
    circles = [(0.0, 0.0, DM["d"] / 2 + AC["band_gap"])] + [(y, z, r) for _, y, z, r in AC["pulleys"]]
    pts = []
    for y, z, r in circles:
        rr = r + off
        pts += [(y + rr * math.cos(a), z + rr * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 180, endpoint=False)]
    pts = np.array(pts)
    h = ConvexHull(pts)
    return [tuple(pts[i]) for i in h.vertices]


def _yz_prism(poly, x0, x1):
    return cq.Workplane("YZ").workplane(offset=x0).polyline(poly).close().extrude(x1 - x0).val()


def _disc(y, z, r, x0, x1):
    return cyl_x(r, x0, x1, y, z)


def _arm(p, q, w, x0, x1):
    """Flat bar between two (y, z) points."""
    dy, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dy, dz)
    ny, nz = -dz / L * w / 2, dy / L * w / 2
    poly = [(p[0] + ny, p[1] + nz), (q[0] + ny, q[1] + nz), (q[0] - ny, q[1] - nz), (p[0] - ny, p[1] - nz)]
    return _yz_prism(poly, x0, x1)


def accessory_module():
    """One printed part: slim back plate (a disc behind every pulley + arms
    between them), pulleys with bosses, pump housing, alternator body, belt band."""
    t = AC["plate_t"]
    px0, px1 = X1 + 0.3, X1 + 0.3 + t                      # back plate flat on the cover's (flush) front face
    mx0 = px0                                                # magnet pockets open in the plate's back
    pul = {name: (y, z, r) for name, y, z, r in AC["pulleys"]}
    mod = None
    for name, (y, z, r) in pul.items():
        d = _disc(y, z, r + AC["plate_margin"], px0, px1)
        mod = d if mod is None else mod.fuse(d)
    for a, b in AC["arms"]:
        (ya, za, _), (yb, zb, _) = pul[a], pul[b]
        mod = mod.fuse(_arm((ya, za), (yb, zb), AC["arm_w"], px0, px1))
    mod = mod.cut(cyl_x(DM["d"] / 2 + 3.0, px0 - 1, px1 + 1))            # clear the turning damper
    # belt band
    bx0 = X1 + AC["band_x0"]
    band = _yz_prism(_band_polygon(AC["band_t"]), bx0, bx0 + AC["band_w"]).cut(_yz_prism(_band_polygon(0.0), bx0 - 1, bx0 + AC["band_w"] + 1))
    mod = mod.fuse(band)
    # pulleys with a shallow groove, on bosses from the plate
    py0, py1 = X1 + AC["pulley_x0"], X1 + AC["pulley_x0"] + AC["pulley_t"]
    for name, (y, z, r) in pul.items():
        p = cyl_x(r, py0, py1, y, z)
        p = cq.Workplane().add(p).faces(">X").edges().chamfer(1.0).val()
        groove = cyl_x(r + 1, bx0, bx0 + AC["band_w"], y, z).cut(cyl_x(r - 1.0, bx0 - 1, bx0 + AC["band_w"] + 1, y, z))
        p = p.cut(groove)
        p = p.fuse(cyl_x(r * 0.35, py1 - 0.1, py1 + 1.5, y, z))      # hub nut
        if name == "alt":
            body = cyl_x(AC["alt_body"]["r"], AC["alt_body"]["x0"], AC["alt_body"]["x1"], y, z)
            body = cq.Workplane().add(body).faces("<X or >X").edges().chamfer(2.0).val()
            for i in range(12):                                            # cooling slots in the rear face
                body = body.cut(box(AC["alt_body"]["x0"] - 1, AC["alt_body"]["x0"] + 2.0, -1.2, 1.2,
                                    AC["alt_body"]["r"] * 0.45, AC["alt_body"]["r"] * 0.8)
                                .rotate((0, 0, 0), (1, 0, 0), i * 30.0).translate(cq.Vector(0, y, z)))
            mod = mod.fuse(body)
        elif name == "pump":
            mod = mod.fuse(cyl_x(AC["pump_snout_r"], px1 - 0.1, py0 + 0.1, y, z))      # pump snout behind the pulley
        else:
            mod = mod.fuse(cyl_x(AC["idler_boss_r"], px1 - 0.1, py0 + 0.1, y, z))
        mod = mod.fuse(p)
    # magnets to the cover's front-wall bosses
    for y, z in FC["module_magnets"]:
        mod = mod.fuse(cyl_x(C.COVER_PILLAR_R + 0.5, mx0, px1 + 2.0, y, z))
        mod = mod.cut(crush_x(C.MAGNET["d"], mx0 - 0.5, mx0 + C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR, y, z, "magnet_6", entry="lo"))
    return safe_clean(mod)


def print_module(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)      # back plate down


def build_all():
    return {"front_cover": front_cover(), "damper": damper(), "accessory": accessory_module()}


def placed(lib, phi=0.0):
    return [("front_cover", lib["front_cover"], "block"),
            ("damper", lib["damper"].rotate((0, 0, 0), (1, 0, 0), -(C.THROW_PIN_A[0] + phi)), "carbon"),
            ("accessory", lib["accessory"], "carbon")]
