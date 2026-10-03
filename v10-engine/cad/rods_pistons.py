"""Con-rods, pistons, guide rails and the slider-crank kinematics.

Piston guidance (important): a piston on a pivoting con-rod MUST be guided
along the cylinder axis by something, otherwise it simply flops over. Here
each piston carries a lug on its valley side with two sintered-bronze
bushings that slide on a fixed 3 mm stainless rail. The piston body and
skirt keep PISTON_RADIAL_CLEARANCE from the bore all the way round, so the
only sliding contact in the cylinder is bronze-on-steel.
"""

import math

import cadquery as cq

from common import C, box, crush_x, crush_z, cyl_x, cyl_z, move, polar, rot_x, rot_z, safe_clean

L = C.ROD_LENGTH
R = C.CRANK_R


# ---------------------------------------------------------------------------
# Con-rod. Local frame: big-end centre at origin, small end at +Z, thickness
# along X (centred on x=0).
# ---------------------------------------------------------------------------
def conrod():
    t = C.ROD_BODY_W
    rb = C.ROD_BIG_END_OD / 2
    rs = C.ROD_SMALL_END_OD / 2
    big = cyl_x(rb, -t / 2, t / 2)
    small = cyl_x(rs, -t / 2, t / 2, 0, L)
    wb, ws = C.ROD_SHANK_W_BIG / 2, C.ROD_SHANK_W_SMALL / 2
    shank = (cq.Workplane("YZ").workplane(offset=-t / 2)
             .polyline([(-wb, 0), (wb, 0), (ws, L), (-ws, L)]).close().extrude(t).val())
    rod = big.fuse(small).fuse(shank)
    # shallow flute on the top face only (H-beam look). The bed face stays
    # flat: a flute there would print as a long unsupported bridge.
    z0, z1 = rb + 2.0, L - rs - 1.5
    fw = lambda z: (wb + (ws - wb) * z / L) - 1.8
    poly = [(-fw(z0), z0), (fw(z0), z0), (fw(z1), z1), (-fw(z1), z1)]
    flute = (cq.Workplane("YZ").workplane(offset=t / 2 - C.ROD_FLUTE_DEPTH).polyline(poly).close()
             .extrude(C.ROD_FLUTE_DEPTH + 0.1).val())
    rod = rod.cut(flute)
    rod = rod.cut(crush_x(C.BEARING_686["od"], -t / 2 - 0.01, t / 2 + 0.01, 0, 0, "bearing_686", entry="both"))
    rod = rod.cut(crush_x(C.BUSHING["od"], -t / 2 - 0.01, t / 2 + 0.01, 0, L, "bushing_5", entry="both"))
    return safe_clean(rod)


# ---------------------------------------------------------------------------
# Piston. Local frame: wrist-pin axis along X through the origin, cylinder
# axis +Z (crown up), guide lug on +Y.
# ---------------------------------------------------------------------------
def piston():
    rp = C.PISTON_DIA / 2
    top = C.PISTON_PIN_TO_CROWN
    bot = -C.PISTON_PIN_TO_SKIRT
    body = cyl_z(rp, bot, top)
    body = body.cut(cyl_z(rp - C.PISTON_WALL_T, bot - 0.1, top - C.PISTON_CROWN_T))
    # pin bosses from the small-end side gap out to the wall
    x_in = C.ROD_BODY_W / 2 + C.PISTON_BOSS_GAP
    for s in (-1, 1):
        lo, hi = sorted((s * x_in, s * (rp - 0.5)))
        boss = cyl_x(4.5, lo, hi).fuse(box(lo, hi, -4.5, 4.5, 0, top - C.PISTON_CROWN_T + 0.1))
        body = body.fuse(boss)
    # guide lug
    ro = C.LUG_OD / 2
    lug = cyl_z(ro, C.LUG_BOTTOM, C.LUG_TOP, 0, C.RAIL_OFFSET)
    lug = lug.fuse(box(-3.0, 3.0, rp - C.PISTON_WALL_T + 0.5, C.RAIL_OFFSET, C.LUG_BOTTOM, C.LUG_TOP))
    # 0.6 mm lead-in chamfer on the lug top (it enters its pocket with the crown)
    lug = lug.cut(cyl_z(ro + 1.0, C.LUG_TOP - 0.6, C.LUG_TOP + 1.0, 0, C.RAIL_OFFSET).cut(
        cq.Solid.makeCone(ro, ro - 1.6, 1.6, cq.Vector(0, C.RAIL_OFFSET, C.LUG_TOP - 0.6), cq.Vector(0, 0, 1))))
    body = body.fuse(lug)
    # two bushings, pressed in from each end of the lug
    body = body.cut(crush_z(C.BUSHING["od"], C.LUG_BOTTOM - 0.01, C.LUG_TOP + 0.01, 0, C.RAIL_OFFSET,
                            "bushing_5", entry="both", phase=45.0))
    # wrist-pin hole (light press in both bosses)
    # wrist-pin hole: crush ribs in both bosses, plain clearance through the middle
    for s_ in (-1, 1):
        lo, hi = sorted((s_ * (C.ROD_BODY_W / 2 + C.PISTON_BOSS_GAP), s_ * (rp + 0.5)))
        body = body.cut(crush_x(C.WRIST_PIN["d"], lo, hi, 0, 0, "pin_3", entry="both", phase=90.0))
    # crown: 45 deg top chamfer, 2 cosmetic ring grooves, 4 valve reliefs
    keep = cq.Solid.makeCone(rp, rp - 1.6, 1.6, cq.Vector(0, 0, top - 0.6), cq.Vector(0, 0, 1))
    body = body.cut(cyl_z(rp + 1.0, top - 0.6, top + 1.0).cut(keep))
    for zg in (top - 2.5, top - 4.3):
        ring = cyl_z(rp + 1, zg - 0.4, zg + 0.4).cut(cyl_z(rp - 0.45, zg - 0.5, zg + 0.5))
        body = body.cut(ring)
    vr = C.VALVE_RELIEF_D / 2
    for x in (-9.5, 9.5):
        for y, d in ((9.0, vr + 0.6), (-9.0, vr - 0.4)):     # intake (valley) side bigger
            body = body.cut(cyl_z(d, top - C.VALVE_RELIEF_DEPTH, top + 1, x, y))
    return safe_clean(body)


def bushing():
    return cyl_z(C.BUSHING["od"] / 2, 0, C.BUSHING["l"]).cut(cyl_z(C.BUSHING["id"] / 2, -1, C.BUSHING["l"] + 1))


def bearing(b):
    return cyl_x(b["od"] / 2, -b["w"] / 2, b["w"] / 2).cut(cyl_x(b["id"] / 2, -b["w"], b["w"]))


def wrist_pin():
    return cyl_x(C.WRIST_PIN["d"] / 2, -C.WRIST_PIN["l"] / 2, C.WRIST_PIN["l"] / 2)


def rail():
    return cyl_z(C.RAIL_DIA / 2, C.RAIL_BOTTOM, C.RAIL_TOP)


# ---------------------------------------------------------------------------
# Kinematics
# ---------------------------------------------------------------------------
def cyl_x_pos(c):
    k = C.cyl_throw(c)
    return C.BANK_A_CYL_X[k] if C.cyl_bank(c) == "A" else C.BANK_B_CYL_X[k]


def slider(c, phi):
    """Return (pin_angle_global, wrist_dist, rod_angle_global) for cylinder c."""
    psi_b = C.bank_angle(C.cyl_bank(c))
    pin = C.PIN_ANGLE[c] + phi
    beta = math.radians(pin - psi_b)
    s = R * math.cos(beta) + math.sqrt(L * L - (R * math.sin(beta)) ** 2)
    gamma = math.degrees(math.atan2(-R * math.sin(beta), s - R * math.cos(beta)))
    return pin, s, psi_b + gamma


def piston_frame(shape, bank, psi_b, x, wy, wz):
    """Piston-local (lug on +Y) -> engine, for a piston whose pin is at (x, wy, wz)."""
    if bank == "B":
        shape = rot_z(shape, 180)
    return move(rot_x(shape, psi_b), x, wy, wz)


def moving_parts(lib, phi):
    """(name, shape, colour) for rods, pistons, bearings, bushings and pins."""
    out = []
    bush_x = lib["bush"].rotate((0, 0, 0), (0, 1, 0), 90).translate(cq.Vector(-C.BUSHING["l"] / 2, 0, 0))
    for c in range(1, C.N_CYL + 1):
        bank = C.cyl_bank(c)
        x = cyl_x_pos(c)
        pin, s, rod_ang = slider(c, phi)
        py, pz = polar(R, pin)
        xr = x + C.CRANK_DX            # rods ride on the crank (assembled position), pistons on their rails
        out.append((f"rod_{c}", move(rot_x(lib["rod"], rod_ang), xr, py, pz), "rod"))
        out.append((f"bearing686_{c}", move(lib["b686"], xr, py, pz), "steel"))
        psi_b = C.bank_angle(bank)
        wy, wz = polar(s, psi_b)
        out.append((f"piston_{c}", piston_frame(lib["piston"], bank, psi_b, x, wy, wz), "piston"))
        out.append((f"wristpin_{c}", piston_frame(lib["wpin"], bank, psi_b, x, wy, wz), "steel"))
        out.append((f"bush_small_{c}", piston_frame(bush_x, bank, psi_b, xr, wy, wz), "bronze"))
        for i, zb in enumerate((C.LUG_TOP - C.BUSHING["l"], C.LUG_BOTTOM)):
            b = move(lib["bush"], 0, C.RAIL_OFFSET, zb)
            out.append((f"bush_lug_{c}_{i}", piston_frame(b, bank, psi_b, x, wy, wz), "bronze"))
    return out


def static_rails(lib):
    out = []
    for c in range(1, C.N_CYL + 1):
        bank = C.cyl_bank(c)
        r = move(lib["rail"], 0, C.RAIL_OFFSET, 0)
        out.append((f"rail_{c}", piston_frame(r, bank, C.bank_angle(bank), cyl_x_pos(c), 0, 0), "steel"))
    return out


def build_all():
    return {
        "rod": conrod(),
        "piston": piston(),
        "bush": bushing(),
        "b686": bearing(C.BEARING_686),
        "wpin": wrist_pin(),
        "rail": rail(),
    }


def print_rod(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -90)     # lying flat, fluted face up


def print_piston(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)     # crown on the bed
