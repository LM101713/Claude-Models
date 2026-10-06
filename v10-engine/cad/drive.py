"""Phase 2 drive: GT2 belt from a NEMA17 in the base up to the front main shaft.

Printed:   12 front drive cover (held by 3 magnets - no tools for belt service)
Machined:  M04 pulley spacer (sits between the 608 inner ring and the pulley hub)
Purchased (modelled for clearance checks and renders only): 60T and 20T GT2
pulleys, 210 mm GT2-6 closed belt, NEMA17 40 mm motor.
"""

import math

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from common import C, box, crush_x, cyl_x, move, polar, safe_clean

GROOVE = 0.8   # visual tooth relief depth on pulley renders


def _pulley(p):
    """Purchased GT2 pulley, local frame: hub face at x=0, pointing +X, axis on X."""
    hub = cyl_x(p["hub_d"] / 2, 0, p["hub_len"])
    body = cyl_x(p["od"] / 2, p["hub_len"], p["width"] - 1.0)
    fl = p["od"] / 2 + (2.7 if p["teeth"] >= 40 else 1.5)   # 60T flanges ~43 mm on real parts
    flanges = cyl_x(fl, p["hub_len"], p["hub_len"] + 1.0).fuse(cyl_x(fl, p["width"] - 1.0, p["width"]))
    s = hub.fuse(body).fuse(flanges)
    return s.cut(cyl_x(p["bore"] / 2, -1, p["width"] + 1))


def big_pulley():
    return move(_pulley(C.PULLEY_BIG), C.PULLEY_HUB_X)


def small_pulley():
    return move(_pulley(C.PULLEY_SMALL), C.PULLEY_HUB_X, 0, C.MOTOR_Z)


def spacer():
    """M04 - machined spacer ring, engine frame."""
    return cyl_x(5.75, C.BEARING_OUTER_X, C.PULLEY_HUB_X).cut(cyl_x(4.1, C.BEARING_OUTER_X - 1, C.PULLEY_HUB_X + 1))


def belt():
    """GT2 belt as a band around both pitch circles, engine frame."""
    def ring(off):
        pts = []
        for zc, d in ((0.0, C.PITCH_D_BIG), (C.MOTOR_Z, C.PITCH_D_SMALL)):
            r = d / 2 + off
            pts += [(r * math.cos(a), zc + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 120, endpoint=False)]
        pts = np.array(pts)
        h = ConvexHull(pts)
        return [tuple(pts[i]) for i in h.vertices]
    x0 = C.BELT_X - C.BELT_W / 2
    # tooth tips sit on the pulley OD (pitch - 0.3), backing 0.9 outside the pitch line
    outer = cq.Workplane("YZ").workplane(offset=x0).polyline(ring(0.9)).close().extrude(C.BELT_W).val()
    inner = cq.Workplane("YZ").workplane(offset=x0 - 1).polyline(ring(-0.29)).close().extrude(C.BELT_W + 2).val()
    return outer.cut(inner)


def motor():
    m = C.MOTOR
    s = m["size"]
    body = box(C.MOTOR_FACE_X - m["length"], C.MOTOR_FACE_X, -s / 2, s / 2, C.MOTOR_Z - s / 2, C.MOTOR_Z + s / 2)
    body = cq.Workplane().add(body).edges("|X").chamfer(4.0).val()
    boss = cyl_x(m["boss_d"] / 2, C.MOTOR_FACE_X, C.MOTOR_FACE_X + m["boss_h"], 0, C.MOTOR_Z)
    shaft = cyl_x(m["shaft_d"] / 2, C.MOTOR_FACE_X, C.MOTOR_FACE_X + m["shaft_len"], 0, C.MOTOR_Z)
    return body.fuse(boss).fuse(shaft)


# ---------------------------------------------------------------------------
# 12 Front drive cover
# ---------------------------------------------------------------------------
def _cover_profile(off, x0, x1):
    """D-shaped outline (round top around the crank, straight sides down to the base)."""
    r = C.COVER_R - off
    zb = C.BASE_TOP_Z - 1.0
    circ = cyl_x(r, x0, x1)
    rect = box(x0, x1, -r, r, zb, 0.0)
    return circ.fuse(rect)


def front_cover():
    x0, x1, w = C.COVER_X0, C.COVER_X1, C.COVER_WALL
    outer = _cover_profile(0.0, x0, x1).cut(box(x0 - 1, x1 + 1, -50, 50, C.BASE_TOP_Z - 5, C.BASE_TOP_Z))
    # soft front edge
    outer = cq.Workplane().add(outer).faces(">X").edges().chamfer(2.0).val()
    inner = _cover_profile(w, x0 - 1, x1 - w)
    cover = outer.cut(inner)
    # magnet pillars: full depth, merged into the wall, clear of the pulley flange
    for y, z in C.COVER_MAGNETS:
        pil = cyl_x(C.COVER_PILLAR_R, x0, x1 - w + 0.1, y, z)
        # bridge pillar to the wall so it is one printed solid
        ang = math.degrees(math.atan2(y, z))
        pil = pil.fuse(cq.Workplane().add(box(x0, x1 - w + 0.1, -C.COVER_PILLAR_R, C.COVER_PILLAR_R, 0, 6)).val()
                       .rotate((0, 0, 0), (1, 0, 0), -ang).translate(cq.Vector(0, y, z)))
        cover = cover.fuse(pil.intersect(_cover_profile(0.0, x0, x1)))
        cover = cover.cut(crush_x(C.MAGNET["d"], x0 - 0.5, x0 + C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR, y, z, "magnet_6", entry="lo"))
    return safe_clean(cover)


def print_cover(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)     # front face on the bed


def purchased_parts():
    return [("pulley_60T", big_pulley(), "gold"), ("pulley_20T", small_pulley(), "gold"),
            ("belt", belt(), "carbon"), ("motor", motor(), "carbon"), ("spacer_M04", spacer(), "steel")]
