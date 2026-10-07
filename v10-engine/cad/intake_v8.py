"""Stock-car V8 intake manifold - the printed version (approved proposal):

  36a intake lid   - top + flanks above the split, 8 runner ridges, molded
                     fuel-rail ribs with injector bosses, roof ribs inside,
                     4 magnet pillars; prints UPSIDE DOWN (top on the plate)
  36b intake base  - tray in the valley: lower flanks, floor, tongue, 8 runner
                     stubs into the head pockets, 4 magnet pillars; prints upright
  36c throttle body - separate, 14 mm crush spigot into the lid's front face;
                     prints bore-down (the part-open blade stands on the bed)

Engine frame. Walls 3 mm; lid and base meet on a tongue (base) inside the
lid wall with the standard clearance; held by the 4 cover magnets (6 x 3).
"""

import math

import cadquery as cq

import block
from common import C, box, crush_z, cyl_x, cyl_z, safe_clean

IT = C.INTAKE
SECS = IT["sections"]
Z0, ZTOP = SECS[0][0], SECS[-1][0]
SPLIT = IT["split_z"]
W = IT["wall"]
DECK, YV = C.DECK_DIST, C.BLOCK_Y_VALLEY


def _dim(z):
    """(width, length) of the outer envelope at height z (piecewise linear)."""
    for (za, wa, la), (zb, wb, lb) in zip(SECS, SECS[1:]):
        if za - 1e-9 <= z <= zb + 1e-9:
            f = (z - za) / (zb - za)
            return wa + f * (wb - wa), la + f * (lb - la)
    if z < SECS[0][0]:
        return SECS[0][1], SECS[0][2]
    return SECS[-1][1], SECS[-1][2]


def _wire(z, inset=0.0):
    w, l = _dim(z)
    w, l = w - 2 * inset, l - 2 * inset
    r = max(1.0, IT["r"] - inset)
    pts = [cq.Vector(-l / 2, -w / 2, z), cq.Vector(l / 2, -w / 2, z), cq.Vector(l / 2, w / 2, z), cq.Vector(-l / 2, w / 2, z)]
    wr = cq.Wire.makePolygon(pts, close=True)
    return wr.fillet2D(r, wr.Vertices())


def envelope(z0, z1, inset=0.0):
    """Lofted solid of the plenum outline between z0 and z1, offset inwards by inset."""
    zs = [z0] + [s[0] for s in SECS if z0 < s[0] < z1] + [z1]
    return cq.Solid.makeLoft([_wire(z, inset) for z in zs], ruled=True)


def _half(z0, z1):
    return box(-200, 200, -200, 200, z0, z1)


def _rounded_path(points, radii):
    from exterior_v8 import _rounded_path as rp
    return rp(points, radii)


def _ridge(xc, sgn):
    pts = [cq.Vector(xc, sgn * y, z) for y, z in IT["ridge"]]
    path = _rounded_path(pts, [IT["ridge_r"]] * (len(pts) - 2))
    d0 = (pts[1] - pts[0]).normalized()
    plane = cq.Plane(origin=pts[0].toTuple(), xDir=(1, 0, 0), normal=d0.toTuple())
    return (cq.Workplane(plane).sketch().rect(IT["runner_w"], IT["runner_h"]).vertices()
            .fillet(IT["runner_r"]).finalize().sweep(cq.Workplane().add(path)).val())


def _stub(xc, bank):
    xl = C.BANK_A_CYL_X[list(C.BANK_B_CYL_X if bank == "B" else C.BANK_A_CYL_X).index(xc)]
    pe = block.to_bank(cq.Vertex.makeVertex(xl, YV - IT["port_depth"] + 0.5, DECK + IT["port_z"]), bank)
    pe = cq.Vector(xc, pe.Y, pe.Z)
    up_in = (block.to_bank(cq.Vertex.makeVertex(0, 1.0, 0), bank).Center()
             - block.to_bank(cq.Vertex.makeVertex(0, 0, 0), bank).Center())
    plane = cq.Plane(origin=pe.toTuple(), xDir=(1, 0, 0), normal=up_in.toTuple())
    L = (SPLIT + 2.0 - pe.z) / up_in.z                    # ends just above the split, inside the base wall
    return (cq.Workplane(plane).sketch().rect(IT["runner_w"], IT["runner_h"]).vertices()
            .fillet(IT["runner_r"]).finalize().extrude(L).val())


def _pillars(z_from, z_to, magnet_at_top):
    """4 magnet pillars between z_from and z_to with a 6x3 crush pocket at one end."""
    out = []
    for x, y in IT["magnet_xy"]:
        p = cyl_z(IT["pillar_r"], min(z_from, z_to), max(z_from, z_to), x, y)
        if magnet_at_top:
            p = p.cut(crush_z(C.MAGNET["d"], z_to - C.MAGNET["h"] - C.MAGNET_DEPTH_CLEAR, z_to + 0.5, x, y, "magnet_6", entry="hi"))
        else:
            p = p.cut(crush_z(C.MAGNET["d"], z_to - 0.5, z_to + C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR, x, y, "magnet_6", entry="lo"))
        out.append(p)
    return out


# ---------------------------------------------------------------------------
def intake_lid():
    outer = envelope(SPLIT, ZTOP)
    outer = cq.Workplane().add(outer).faces(">Z").edges().fillet(IT["top_fillet"]).val()
    lid = outer
    # 8 runner ridges over the flank and top, molded fuel-rail rib with injector bosses on each flank
    for bank in ("A", "B"):
        sgn = -1 if bank == "A" else 1
        xs = C.BANK_A_CYL_X if bank == "A" else C.BANK_B_CYL_X
        for xc in xs:
            lid = lid.fuse(_ridge(xc, sgn).intersect(_half(SPLIT, ZTOP + 40)))   # ridges stop at the split line
        yr = sgn * (_dim(IT["rail_z"])[0] / 2 + IT["rail_out"])
        rail = cyl_x(IT["rail_r"], min(xs) - 12.0, max(xs) + 12.0, yr, IT["rail_z"])
        rail = cq.Workplane().add(rail).faces("<X or >X").edges().chamfer(1.5).val()
        for xc in xs:
            boss = cq.Solid.makeCylinder(IT["inj_r"], IT["inj_l"], cq.Vector(xc, yr, IT["rail_z"]), cq.Vector(0, -sgn * 0.5, -0.87))
            rail = rail.fuse(boss)
        lid = lid.fuse(rail)
    # hollow: one inner envelope cut AFTER the ridges, so nothing intrudes into the cavity (the base's tongue lives there)
    lid = lid.cut(envelope(SPLIT - 1.0, ZTOP - W, W))
    # roof ribs (stiffen the 180 mm span; also the print's bridge breakers)
    l_in = _dim(ZTOP - W)[1] - 2 * W
    n = int(l_in // IT["rib_pitch"])
    for i in range(1, n + 1):
        x = -l_in / 2 + i * l_in / (n + 1)
        rib = box(x - IT["rib_t"] / 2, x + IT["rib_t"] / 2, -100, 100, ZTOP - W - 8.0, ZTOP - W + 0.1)
        lid = lid.fuse(rib.intersect(envelope(SPLIT, ZTOP, W - 0.1)))
    # magnet pillars hanging from the roof down to the split plane (magnet at the bottom)
    for p in _pillars(ZTOP - W + 0.1, SPLIT, magnet_at_top=False):
        lid = lid.fuse(p)
    # throttle-body spigot socket in the front face (crush), along the TB axis
    tb_axis, tb_base = _tb_axis()
    sock = crush_z(IT["tb_spigot_d"], -(IT["tb_spigot_l"] + 0.5), 2.0, 0, 0, "trumpet_14", entry="hi")
    sock = sock.rotate((0, 0, 0), (0, 1, 0), 90 - IT["tb_tilt"])        # +Z -> tb axis (x forward, tilted up)
    sock = sock.rotate((0, 0, 0), (0, 0, 1), 0).translate(tb_base)
    lid = lid.cut(sock)
    return safe_clean(lid)


def print_lid(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


def intake_base():
    base = envelope(Z0, SPLIT)
    base = base.cut(envelope(Z0 + W, SPLIT + 1.0, W))
    # tongue: inner ring standing above the split, inside the lid wall
    tongue = envelope(SPLIT - 0.1, SPLIT + IT["tongue_h"], W + C.CLEARANCE)
    tongue = tongue.cut(envelope(SPLIT - 1.0, SPLIT + IT["tongue_h"] + 1.0, W + C.CLEARANCE + IT["tongue_w"]))
    base = base.fuse(tongue)
    # runner stubs into the head pockets (clipped to the base's height)
    for bank in ("A", "B"):
        xs = C.BANK_A_CYL_X if bank == "A" else C.BANK_B_CYL_X
        for xc in xs:
            base = base.fuse(_stub(xc, bank).intersect(_half(Z0 - 20, SPLIT)))
    # magnet pillars from the floor up to the split plane (magnet at the top)
    for p in _pillars(Z0 + W - 0.1, SPLIT, magnet_at_top=True):
        base = base.fuse(p.intersect(envelope(Z0, SPLIT, 0.5)))
    # harness pass-through in the floor (valley LED leads come up into the plenum, then out the back)
    base = base.cut(cyl_z(6.0, Z0 - 1, Z0 + W + 1, -40.0, 0.0))
    return safe_clean(base)


def print_base(s):
    return s


def _tb_axis():
    t = math.radians(IT["tb_tilt"])
    axis = cq.Vector(math.cos(t), 0, math.sin(t))
    # the TB seats on the lid's front face at z = tb_z
    x_face = _dim(IT["tb_z"])[1] / 2
    return axis, cq.Vector(x_face, 0, IT["tb_z"])


def throttle_body():
    axis, base = _tb_axis()
    body = cq.Solid.makeCylinder(IT["tb_d"] / 2, IT["tb_l"], base - axis * 2.0, axis)
    body = body.cut(envelope(Z0, ZTOP))                                      # rear face follows the lid's front face
    body = cq.Workplane().add(body).faces(">X").edges().chamfer(2.0).val()
    body = body.cut(cq.Solid.makeCylinder(IT["tb_bore"] / 2, IT["tb_bore_depth"] + 0.1, base + axis * (IT["tb_l"] - IT["tb_bore_depth"]), axis))
    # part-open throttle blade: a thin plate on a shaft across the bore, tilted so it stands on the bed when printed bore-down
    blade = box(-1.2, 1.2, -IT["tb_bore"] / 2 + 0.3, IT["tb_bore"] / 2 - 0.3, -IT["tb_bore"] / 2 + 0.3, IT["tb_bore"] / 2 - 0.3)
    blade = blade.rotate((0, 0, 0), (0, 0, 1), 0).rotate((0, 0, 0), (1, 0, 0), 0)
    blade = blade.rotate((0, 0, 0), (0, 1, 0), 90 - IT["tb_blade_deg"])   # lean the plate (around the shaft axis y)
    blade = blade.rotate((0, 0, 0), (0, 1, 0), -IT["tb_tilt"])            # follow the TB axis tilt
    blade = blade.translate(base + axis * (IT["tb_l"] - IT["tb_bore_depth"] / 2))
    shaft = cq.Solid.makeCylinder(1.6, IT["tb_d"] + 2, (base + axis * (IT["tb_l"] - IT["tb_bore_depth"] / 2) - cq.Vector(0, IT["tb_d"] / 2 + 1, 0)).toTuple(), (0, 1, 0))
    body = body.fuse(blade.intersect(cq.Solid.makeCylinder(IT["tb_bore"] / 2 + 1, IT["tb_l"], base, axis))).fuse(shaft)
    spig = cq.Solid.makeCylinder(IT["tb_spigot_d"] / 2, IT["tb_spigot_l"] + 2.0, (base + axis * 1.9).toTuple(), (axis * -1).toTuple())
    return safe_clean(body.fuse(spig))


def print_throttle(s):
    """Bore face down, spigot up (no ceilings; the blade stands on the bed)."""
    axis, base = _tb_axis()
    s = s.translate((base * -1).toTuple())
    # rotate the axis onto -Z
    ang = math.degrees(math.acos(max(-1, min(1, axis.dot(cq.Vector(0, 0, -1))))))
    ax = axis.cross(cq.Vector(0, 0, -1))
    s = s.rotate((0, 0, 0), ax.toTuple(), ang)
    bb = s.BoundingBox()
    return s.translate(cq.Vector(0, 0, -bb.zmin))


def build_all():
    return {"intake_lid": intake_lid(), "intake_base": intake_base(), "throttle": throttle_body()}


def placed(lib):
    return [("intake_lid", lib["intake_lid"], "block"), ("intake_base", lib["intake_base"], "block"),
            ("throttle", lib["throttle"], "steel")]
