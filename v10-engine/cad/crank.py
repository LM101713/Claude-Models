"""Crankshaft parts.

The crank is BUILT UP, like a real roller-bearing racing crank, so that each
con-rod can carry a one-piece ball bearing on its big end:

  [main shaft]-[end web]-(pin 1)-[segment A]-(pin 2)-[segment B]-(pin 3)
               -[segment B]-(pin 4)-[segment A]-(pin 5)-[end web]-[main shaft]

* Crankpins are machined steel SPLIT pins: two 6 mm journals offset by 18 deg
  joined by a thin flying web. That offset is what makes a 90 deg V10 fire
  evenly every 72 deg (see docs/DESIGN_NOTES.md).
* Each pin end has a D-flat that keys it into a D-hole in the printed web, so
  the crank can only be assembled one way and every joint is rigid.
* Each pin end is pulled home by one M3x8 screw into its tapped end.
* Only two segment shapes exist (54 deg and 198 deg between their pins).

All builders return shapes in a LOCAL frame; the place_* helpers put them into
the engine frame (crank angle 0) and print_* helpers lay them on the bed.
"""

import math

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from common import C, box, bridge_step, crush_d_x, crush_z, cyl_x, move, polar, rot_x, rot_z, safe_clean

R = C.CRANK_R


# ---------------------------------------------------------------------------
# 2D profile helpers (Y-Z plane, extruded along X)
# ---------------------------------------------------------------------------
def _circle_pts(cy, cz, r, n=96):
    return [(cy + r * math.cos(t), cz + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def _hull_prism(circles, x0, x1):
    """Convex hull of circles [(angle, radius_from_axis, circle_r)] extruded X0->X1."""
    pts = []
    for ang, rad, cr in circles:
        cy, cz = polar(rad, ang)
        pts += _circle_pts(cy, cz, cr)
    pts = np.array(pts)
    hull = ConvexHull(pts)
    poly = [tuple(pts[i]) for i in hull.vertices]
    return (cq.Workplane("YZ").workplane(offset=x0).polyline(poly).close()
            .extrude(x1 - x0).val())


def _sector_prism(center_deg, span_deg, radius, x0, x1, n=48):
    pts = [(0.0, 0.0)]
    for t in np.linspace(center_deg - span_deg / 2, center_deg + span_deg / 2, n):
        pts.append(polar(radius, t))
    return (cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close()
            .extrude(x1 - x0).val())


def web_prism(pin_deg, x0, x1, extra_bosses=()):
    """Crank web: hub + pin boss (+ screw-channel bosses) + counterweight."""
    circles = [(0.0, 0.0, C.WEB_HUB_R), (pin_deg, R, C.WEB_PIN_BOSS_R)]
    circles += [(a, R, 5.8) for a in extra_bosses]
    body = _hull_prism(circles, x0, x1)
    cw = _sector_prism(pin_deg + 180.0, C.WEB_CW_SPAN, C.WEB_CW_R, x0, x1)
    web = safe_clean(body.fuse(cw))
    # round every corner of the profile (R3) - machined-billet look, no sharp tips
    face = cq.Workplane().add(web).faces("<X").val()
    wire = face.outerWire().offset2D(-3.0, "arc")[0].offset2D(3.0, "arc")[0]
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), cq.Vector(x1 - x0, 0, 0))


# All crank parts print with -X up (segments front-face down, end webs
# flange-face down), see print_segment / print_end_web.
PRINT_UP = -1


def _pin_socket(pin_deg, face_x, direction, channel_to_x):
    """Cutter for one crankpin socket: D-hole (PIN_END_LEN + PIN_SOCKET_CLEAR
    deep from face_x into the part, direction=-1 means the part lies at
    x < face_x), M3 clearance through the floor, and a head channel out to
    channel_to_x. The pin's machined shoulder seats on the web face; the pin
    end never touches the socket floor."""
    y, z = polar(R, pin_deg)
    x_face = face_x
    x_bot = face_x + direction * (C.PIN_END_LEN + C.PIN_SOCKET_CLEAR)
    x_floor = x_bot + direction * C.PIN_SCREW_FLOOR
    lo, hi = sorted((x_face - direction * 0.2, x_bot))
    # D-hole with crush ribs: the pin's flat (facing radially out, pin_deg)
    # is pushed onto the hole's flat, so the joint has no rotational play
    dhole = crush_d_x(C.PIN_DIA, C.PIN_DFLAT, lo, hi, y, z, pin_deg,
                      entry="hi" if direction < 0 else "lo")
    lo, hi = sorted((x_bot, x_floor))
    r_clear = C.hole(C.M3_CLEAR) / 2
    cut = dhole.fuse(cyl_x(r_clear, lo - 0.1, hi + 0.1, y, z))
    lo, hi = sorted((x_floor, channel_to_x + direction * 0.2))
    channel = cyl_x(C.hole(C.SCREW_CHANNEL_D) / 2, lo, hi, y, z)
    cut = cut.fuse(channel)
    # whichever wide hole lies BELOW the floor on the printer gets a bridged
    # ceiling (the other one opens upwards and needs nothing)
    if direction == PRINT_UP:
        cut = cut.fuse(bridge_step(dhole, r_clear, (x_bot, y, z), "x", PRINT_UP, C.LAYER["crank"],
                                   slot_deg=pin_deg))
    else:
        cut = cut.fuse(bridge_step(channel, r_clear, (x_floor, y, z), "x", PRINT_UP, C.LAYER["crank"],
                                   slot_deg=pin_deg))
    return cut


# ---------------------------------------------------------------------------
# Printed parts
# ---------------------------------------------------------------------------
def segment(delta_deg):
    """Crank segment, local frame: front face at x=0 (holds pin B of the throw
    in front, at angle 0), rear face at x=-SEGMENT_LEN (holds pin A of the
    throw behind, at angle delta)."""
    L = C.SEGMENT_LEN
    wt = C.WEB_T
    front = web_prism(0.0, -wt, 0.0, extra_bosses=(delta_deg,))
    rear = web_prism(delta_deg, -L, -L + wt, extra_bosses=(0.0,))
    journal = cyl_x(C.JOURNAL_R, -L + wt - 0.01, -wt + 0.01)
    part = front.fuse(rear).fuse(journal)

    # 45 deg support cone under the rear web (it is the top web when printing
    # front-face-down), so the segment prints with no supports.
    cone_h = C.WEB_CW_R - C.JOURNAL_R
    x_under = -L + wt
    cone = cq.Solid.makeCone(C.JOURNAL_R, C.WEB_CW_R + 0.01, cone_h,
                             cq.Vector(x_under + cone_h, 0, 0), cq.Vector(-1, 0, 0))
    under = web_prism(delta_deg, x_under, x_under + cone_h, extra_bosses=(0.0,))
    part = part.fuse(cone.intersect(under))

    # decorative 45 deg groove round the journal (reads as two webs + journal)
    xm = (-L + wt + cone_h - wt) / 2
    g = (cq.Workplane("XY").polyline([(xm - 1.6, C.JOURNAL_R + 0.1), (xm + 1.6, C.JOURNAL_R + 0.1),
                                      (xm, C.JOURNAL_R - 1.5)]).close()
         .revolve(360, (0, 0, 0), (1, 0, 0)).val())
    part = part.cut(g)

    # sockets: front pin (angle 0) with screw channel out of the rear face,
    # rear pin (angle delta) with screw channel out of the front face
    part = part.cut(_pin_socket(0.0, 0.0, -1, -L))
    part = part.cut(_pin_socket(delta_deg, -L, +1, 0.0))
    # engraved type number on the rear face (top face when printing) so the
    # two segment types cannot be mixed up at assembly
    label = (cq.Workplane("ZY").workplane(offset=L - 0.6)
             .text(f"{delta_deg:.0f}", 6.0, 0.7, halign="center", valign="center", kind="bold"))
    part = part.cut(label.val())
    return safe_clean(part)


def end_web():
    """End web, local frame: throw face at x=0 (crankpin at angle 0, socket
    going +X), flange face at x=END_WEB_T (main shaft bolts on here)."""
    t = C.END_WEB_T
    part = web_prism(0.0, 0.0, t)
    part = part.cut(_pin_socket(0.0, 0.0, +1, t))
    # main shaft spigot and 3 heat-set inserts
    part = part.cut(cyl_x(C.hole(C.SHAFT_SPIGOT_D, "spigot") / 2, t - C.SHAFT_SPIGOT_L - 0.5, t + 1))
    for a in C.SHAFT_FLANGE_BOLT_ANGLES:
        y, z = polar(C.SHAFT_FLANGE_PCD / 2, a)
        part = part.cut(cyl_x(C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3") / 2,
                              t - C.INSERT_DEPTH, t + 1, y, z))
    # hall-sensor magnet: radial pocket in the counterweight rim
    if C.HALL_MAGNET_IN_WEB:
        pocket = crush_z(C.MAGNET["d"], C.WEB_CW_R - C.MAGNET["h"] - 0.3, C.WEB_CW_R + 0.5,
                         t / 2, 0, "magnet_6", entry="hi")
        part = part.cut(rot_x(pocket, C.HALL_MAGNET_WEB_ANGLE))   # built at angle 0, turned into place
    return safe_clean(part)


# ---------------------------------------------------------------------------
# Machined parts (also exported as printable prototypes)
# ---------------------------------------------------------------------------
def split_crankpin():
    """Split crankpin, local frame: centred on x=0, journal A (front, +X) axis
    at crank angle 0 radius R, journal B (rear) at angle SPLIT_ANGLE.

    Shoulders only on the INSIDE of each journal (next to the flying web): the
    686 bearing slides on over the end, then an M06 spacer ring, then the end
    goes into the web. The ring clamps the bearing inner ring against the
    shoulder and keeps the rod 0.75 mm off the web face."""
    s = C.SPLIT_ANGLE
    ya, za = polar(R, 0.0)
    yb, zb = polar(R, s)
    half_web = C.PIN_FLYWEB_T / 2
    sl = C.PIN_SHOULDER_L
    bw = C.BEARING_686["w"]
    rp = C.PIN_DIA / 2
    rs = C.PIN_SHOULDER_D / 2
    x_j0 = half_web + sl               # journal start
    x_j1 = x_j0 + bw                   # journal end
    x_e0 = x_j1 + sl                   # end (in web) start
    x_e1 = x_e0 + C.PIN_END_LEN

    def one_side(y, z, sign, flat_deg):
        def seg(r, a, b):
            lo, hi = sorted((sign * a, sign * b))
            return cyl_x(r, lo, hi, y, z)
        p = seg(rs, half_web - 0.01, x_j0)
        p = p.fuse(seg(rp, x_j0 - 0.01, x_e0 + 0.01))      # journal + spacer-ring seat, one diameter
        end = seg(rp, x_e0 - 0.01, x_e1)
        # D-flat, facing radially away from the crank axis
        lo, hi = sorted((sign * x_e0, sign * (x_e1 + 1)))
        flat = box(lo, hi, -5, 5, rp - C.PIN_DFLAT, rp + 5)
        flat = move(rot_x(flat, flat_deg), 0, y, z)
        end = end.cut(flat)
        tap_lo, tap_hi = sorted((sign * (x_e1 - C.PIN_TAP_DEPTH), sign * (x_e1 + 1)))
        end = end.cut(cyl_x(C.M3_TAP / 2, tap_lo, tap_hi, y, z))
        return p.fuse(end)

    a_side = one_side(ya, za, +1, 0.0)
    b_side = one_side(yb, zb, -1, s)
    web = _hull_prism([(0.0, R, rs), (s, R, rs)], -half_web, half_web)
    return safe_clean(a_side.fuse(b_side).fuse(web))


def spacer_ring():
    """M06 bearing spacer ring, local frame: axis X, x from 0 to PIN_SHOULDER_L."""
    return cyl_x(C.PIN_SHOULDER_D / 2, 0, C.PIN_SHOULDER_L).cut(cyl_x(C.PIN_DIA / 2 + 0.03, -1, 1 + C.PIN_SHOULDER_L))


def pin_rings():
    """The two spacer rings of one crankpin, in the pin's local frame."""
    sl, bw = C.PIN_SHOULDER_L, C.BEARING_686["w"]
    x_j1 = C.PIN_FLYWEB_T / 2 + sl + bw
    ya, za = polar(R, 0.0)
    yb, zb = polar(R, C.SPLIT_ANGLE)
    ring = spacer_ring()
    return move(ring, x_j1, ya, za), move(ring, -x_j1 - sl, yb, zb)


def main_shaft():
    """Main shaft, local frame: flange face that seats on the end web at x=0,
    spigot into the web at x<0, shaft running to +X. Crankpin access notch
    at angle 0."""
    x = 0.0
    part = cyl_x(C.SHAFT_SPIGOT_D / 2, -C.SHAFT_SPIGOT_L, 0.01)
    part = part.fuse(cyl_x(C.SHAFT_FLANGE_D / 2, 0.0, C.SHAFT_FLANGE_T))
    x = C.SHAFT_FLANGE_T
    part = part.fuse(cyl_x(C.SHAFT_SHOULDER_D / 2, x - 0.01, x + C.SHAFT_SHOULDER_L))
    x += C.SHAFT_SHOULDER_L
    part = part.fuse(cyl_x(C.SHAFT_D / 2, x - 0.01, x + C.SHAFT_JOURNAL_L))
    # flat for pulley grub screws on the outboard part, at angle 0
    x_flat0 = x + C.BEARING_608["w"] + 1.0
    flat = box(x_flat0, x + C.SHAFT_JOURNAL_L + 1, -5, 5, C.SHAFT_D / 2 - C.SHAFT_FLAT_DEPTH, 10)
    part = part.cut(flat)
    for a in C.SHAFT_FLANGE_BOLT_ANGLES:
        y, z = polar(C.SHAFT_FLANGE_PCD / 2, a)
        part = part.cut(cyl_x(C.M3_CLEAR / 2, -1, C.SHAFT_FLANGE_T + 1, y, z))
    y, z = polar(R, 0.0)
    part = part.cut(cyl_x(C.SHAFT_ACCESS_HOLE_D / 2, -1, C.SHAFT_FLANGE_T + 1, y, z))
    part = part.cut(box(-1, C.SHAFT_FLANGE_T + 1, -C.SHAFT_ACCESS_HOLE_D / 2, C.SHAFT_ACCESS_HOLE_D / 2, R, 30))
    return safe_clean(part)


# ---------------------------------------------------------------------------
# Placement in the engine (crank angle phi, degrees)
# ---------------------------------------------------------------------------
def placed_parts(parts, phi=0.0):
    """Return a list of (name, shape) for the whole crank at crank angle phi.
    parts: dict with 'segA', 'segB', 'end', 'pin', 'shaft' local shapes."""
    out = []
    for k in range(C.N_THROWS):
        pin = rot_x(parts["pin"], C.THROW_PIN_A[k] + phi)
        out.append((f"crankpin_{k+1}", move(pin, C.THROW_X[k])))
        for tag, ring in zip("ab", parts["rings"]):
            out.append((f"crankpin_ring_{k+1}{tag}", move(rot_x(ring, C.THROW_PIN_A[k] + phi), C.THROW_X[k])))
    for k in range(C.N_THROWS - 1):
        d = C.SEGMENT_DELTA[k]
        key = "segA" if abs(d - C.SEGMENT_TYPES[0]) < 1e-6 else "segB"
        s = rot_x(parts[key], C.THROW_PIN_B[k] + phi)
        out.append((f"segment_{k+1}{k+2}", move(s, C.THROW_X[k] - C.THROW_INNER / 2)))
    # front end web + shaft
    ew = rot_x(parts["end"], C.THROW_PIN_A[0] + phi)
    out.append(("end_web_front", move(ew, C.WEB_FACE_X)))
    sh = rot_x(parts["shaft"], C.THROW_PIN_A[0] + phi)
    out.append(("main_shaft_front", move(sh, C.END_WEB_OUTER_X)))
    # rear: mirror by 180 deg about Z (angle psi -> -psi), then set the angle
    ew_r = rot_x(rot_z(parts["end"], 180), C.THROW_PIN_B[-1] + phi)
    out.append(("end_web_rear", move(ew_r, -C.WEB_FACE_X)))
    sh_r = rot_x(rot_z(parts["shaft"], 180), C.THROW_PIN_B[-1] + phi)
    out.append(("main_shaft_rear", move(sh_r, -C.END_WEB_OUTER_X)))
    # assembled position: the front clamp pulls the crank forward by CRANK_DX
    return [(n, move(s, C.CRANK_DX)) for n, s in out]


def build_all():
    return {
        "segA": segment(C.SEGMENT_TYPES[0]),
        "segB": segment(C.SEGMENT_TYPES[1]),
        "end": end_web(),
        "pin": split_crankpin(),
        "rings": pin_rings(),
        "ring": spacer_ring(),
        "shaft": main_shaft(),
    }


# print orientations (flat face down, axis vertical)
def print_segment(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)      # front face (x=0) onto the bed


def print_end_web(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)      # flange face (x = END_WEB_T) down: flat shaft seat


def print_pin(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90)


def print_shaft(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90)     # flange down
