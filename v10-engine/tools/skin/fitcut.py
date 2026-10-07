"""Fit features as cutters / bosses, every value from params.json:
crush-rib pockets (magnets, spigots, boots, rails), heat-set insert holes,
M3 clearance / counterbore pairs. 128 segments on every round feature."""
import math

from . import bpyutil as U
from .params import P

# every fit feature cut into a library part, for the STL measurement (tools/skin/measure.py):
# FITS[obj name] = [dict(label, kind 'bore'|'tip', r, p (point on axis), d (unit axis), t0, t1)]
FITS = {}


def note(obj, label, kind, r, p, d, t0, t1, e1=None, sectors=None):
    """sectors: list of (angle_deg, half_width_deg) about the axis, angle measured from e1 towards d x e1.
    A 'bore' measurement skips those sectors (the ribs sit there); a 'tip' measurement uses only them."""
    FITS.setdefault(obj.name, []).append(dict(label=label, kind=kind, r=float(r), p=[float(v) for v in p],
                                               d=[float(v) for v in d], t0=float(min(t0, t1)), t1=float(max(t0, t1)),
                                               e1=[float(v) for v in e1] if e1 is not None else None,
                                               sectors=[[float(a), float(w)] for a, w in sectors] if sectors else None))


def _axis_pd(axis, x, y):
    """(point on axis, unit axis, reference e1) for a cylinder() call with the given axis and (x, y)."""
    if axis == "X":
        return (0.0, x, y), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    if axis == "Y":
        return (x, 0.0, y), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)
    return (x, y, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)


def _offset3(axis, rx, ry):
    if axis == "X":
        return (0.0, rx, ry)
    if axis == "Y":
        return (rx, 0.0, ry)
    return (rx, ry, 0.0)


def sector_angle(d, e1, off):
    """Angle (deg) of the offset vector about axis d, from e1 towards d x e1."""
    from mathutils import Vector
    d, e1, off = Vector(d), Vector(e1), Vector(off)
    e2 = d.cross(e1)
    return math.degrees(math.atan2(off.dot(e2), off.dot(e1)))


def _crush_notes(obj, fit, c, p, d, e1, offsets, z0, z1, entry):
    """Bore + rib-tip measurement records for one crush pocket (straight section only, end rings included)."""
    lead = P.CRUSH_LEAD
    bore_r = c["bore"] / 2
    s0 = z0 + (lead + 0.01 if entry in ("lo", "both") else 0.0)
    s1 = z1 - (lead + 0.01 if entry in ("hi", "both") else 0.0)
    hw = math.degrees(math.asin(min(1.0, c["rib_r"] / c["rib_centre_r"]))) + 2.0
    sectors = [(sector_angle(d, e1, off), hw) for off in offsets]
    note(obj, f"{fit} bore", "bore", bore_r, p, d, s0 - 0.05, s1 + 0.05, e1, sectors)
    r0 = z0 + (lead + 0.05 if entry in ("lo", "both") else 0.2)
    r1 = z1 - (lead + 0.05 if entry in ("hi", "both") else 0.2)
    note(obj, f"{fit} rib tip", "tip", c["rib_centre_r"] - c["rib_r"], p, d, r0 - 0.05, r1 + 0.05, e1,
         [(a, 1.0) for a, _ in sectors])


def cut_crush(obj, fit, z0, z1, x=0.0, y=0.0, axis="Z", entry="hi"):
    """Crush-rib pocket cut INTO obj along `axis` between z0 and z1 (along-axis
    coordinates, z1 > z0): bore cut, lead-in cone at the entry, then the ribs
    added back as separate unions (keeps the exact boolean manifold)."""
    c = P.crush[fit]
    bore_r = c["bore"] / 2
    lead = P.CRUSH_LEAD
    U.boolean(obj, U.cylinder("crush_bore", bore_r, z0, z1, x, y, axis))
    if entry in ("hi", "both"):
        U.boolean(obj, U.cylinder("crush_lead", bore_r + 0.005, z1 - lead - 0.01, z1 + 0.05, x, y, axis, r2=bore_r + lead + 0.005))
    if entry in ("lo", "both"):
        U.boolean(obj, U.cylinder("crush_lead", bore_r + lead + 0.005, z0 - 0.05, z0 + lead + 0.01, x, y, axis, r2=bore_r + 0.005))
    r0 = z0 + (lead + 0.05 if entry in ("lo", "both") else 0.2)
    r1 = z1 - (lead + 0.05 if entry in ("hi", "both") else 0.2)
    offsets = []
    for i in range(c["n_ribs"]):
        a = 2 * math.pi * i / c["n_ribs"]
        rx, ry = c["rib_centre_r"] * math.cos(a), c["rib_centre_r"] * math.sin(a)
        # ribs are 0.6 mm radius: 24 segments (128 would make 0.03 mm edges the exact boolean cannot keep manifold)
        U.boolean(obj, U.cylinder("crush_rib", c["rib_r"], r0, r1, x + rx, y + ry, axis, segs=24), "UNION")
        offsets.append(_offset3(axis, rx, ry))
    p, d, e1 = _axis_pd(axis, x, y)
    _crush_notes(obj, fit, c, p, d, e1, offsets, z0, z1, entry)
    return obj


def insert_hole(name, z_face, depth_dir, x=0.0, y=0.0, axis="Z"):
    """Heat-set insert pilot hole starting at the face z_face going depth_dir (+1/-1)."""
    d = P.INSERT_DEPTH
    z0, z1 = sorted((z_face - 1.0 * depth_dir, z_face + d * depth_dir)) if depth_dir > 0 else sorted((z_face + 1.0, z_face - d))
    return U.cylinder(name, P.insert_hole / 2, z0, z1, x, y, axis)


def screw_cbore(name, z_bottom, z_top, floor, x=0.0, y=0.0, axis="Z"):
    """M3 clearance hole from z_bottom through, counterbored from z_top down to z_bottom + floor."""
    clear = U.cylinder(name + "_clear", P.hole["M3_CLEAR"] / 2, z_bottom - 1, z_top + 1, x, y, axis)
    cb = U.cylinder(name + "_cbore", P.hole["M3_CBORE"] / 2, z_bottom + floor, z_top + 1, x, y, axis)
    U.boolean(clear, cb, "UNION")
    return clear


def cut_magnet(obj, z_face, into_dir, x=0.0, y=0.0, axis="Z"):
    """6x3 magnet crush pocket opening at z_face, going into the part along into_dir."""
    depth = P.MAGNET["h"] + P.MAGNET_DEPTH_CLEAR
    if into_dir > 0:
        return cut_crush(obj, "magnet_6", z_face - 0.5, z_face + depth, x, y, axis, entry="lo")
    return cut_crush(obj, "magnet_6", z_face - depth, z_face + 0.5, x, y, axis, entry="hi")


def cut_crush_M(obj, fit, t0, t1, M, entry="hi"):
    """cut_crush along an arbitrary axis: the pocket is built along local +Z between t0 and t1
    (t1 > t0, t = 0 at the local origin) and moved by the 4x4 matrix M before cutting."""
    from mathutils import Vector
    c = P.crush[fit]
    bore_r = c["bore"] / 2
    lead = P.CRUSH_LEAD
    cutters = [(U.cylinder("crush_bore", bore_r, t0, t1, 0, 0), "DIFFERENCE")]
    if entry in ("hi", "both"):
        cutters.append((U.cylinder("crush_lead", bore_r + 0.005, t1 - lead - 0.01, t1 + 0.05, 0, 0, r2=bore_r + lead + 0.005), "DIFFERENCE"))
    if entry in ("lo", "both"):
        cutters.append((U.cylinder("crush_lead", bore_r + lead + 0.005, t0 - 0.05, t0 + lead + 0.01, 0, 0, r2=bore_r + 0.005), "DIFFERENCE"))
    r0 = t0 + (lead + 0.05 if entry in ("lo", "both") else 0.2)
    r1 = t1 - (lead + 0.05 if entry in ("hi", "both") else 0.2)
    R = M.to_3x3()
    offsets = []
    for i in range(c["n_ribs"]):
        a = 2 * math.pi * i / c["n_ribs"]
        cutters.append((U.cylinder("crush_rib", c["rib_r"], r0, r1, c["rib_centre_r"] * math.cos(a), c["rib_centre_r"] * math.sin(a), segs=24), "UNION"))
        offsets.append(R @ Vector((math.cos(a), math.sin(a), 0.0)))
    for cu, op in cutters:
        cu["fit_meta"] = ""          # logged below with the real axis instead
        U.transform(cu, M)
        U.boolean(obj, cu, op)
    p = M @ Vector((0, 0, 0))
    d = (R @ Vector((0, 0, 1))).normalized()
    e1 = (R @ Vector((1, 0, 0))).normalized()
    _crush_notes(obj, fit, c, p, d, e1, offsets, t0, t1, entry)
    return obj
