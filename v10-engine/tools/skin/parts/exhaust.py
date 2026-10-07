"""33 header primaries (S-curve, one shape per bank, B = mirror) and 35 tapered
collectors - same centreline maths as cad/exterior_v8.primary_geometry, from
params.json. Tubes are swept curves (128-segment profile), spigots and the
collector seat cones are exact cylinders / cones."""
import math

from .. import bpyutil as U
from .. import fitcut as F
from ..params import P
from mathutils import Vector


def _bank_pt_A(yl, zl):
    a = math.radians(-P.bank_angle_A)
    return Vector((0.0, yl * math.cos(a) - zl * math.sin(a), yl * math.sin(a) + zl * math.cos(a)))


def geometry():
    DECK, YO = P.DECK_DIST, P.BLOCK_Y_OUT
    PORT_Z = DECK + P.EXH_PORT_Z
    p0 = _bank_pt_A(YO + P.EXH_PORT_DEPTH, PORT_Z)
    t1 = (_bank_pt_A(YO - 10.0, PORT_Z) - p0).normalized()
    L1 = (-P.EXH_FLARE_Y - p0.y) / t1.y
    Q1 = p0 + t1 * L1
    jog = P.EXH_X_JOG
    Q2 = Vector((jog * P.EXH_S_X_SHARE, -P.EXH_COLLECTOR_Y, P.EXH_S_Z))
    p3 = Vector((jog, -P.EXH_COLLECTOR_Y, P.EXH_COLLECTOR_TOP_Z - P.EXH_COLLECTOR_SADDLE))
    t2 = (Q2 - Q1).normalized()
    t3 = (p3 - Q2).normalized()
    return dict(p0=p0, Q1=Q1, Q2=Q2, p3=p3, t1=t1, t2=t2, t3=t3)


def _rounded_polyline(pts, radii, n=12):
    """Sample a line-arc-line path through corner points with the given corner radii."""
    out = [pts[0]]
    cur = pts[0]
    for i in range(1, len(pts) - 1):
        Pp, Q, R = pts[i - 1], pts[i], pts[i + 1]
        t1, t2 = (Q - Pp).normalized(), (R - Q).normalized()
        beta = math.acos(max(-1.0, min(1.0, t1.dot(t2))))
        r = radii[i - 1]
        tl = r * math.tan(beta / 2)
        A, B = Q - t1 * tl, Q + t2 * tl
        centre = Q + (t2 - t1).normalized() * (r / math.cos(beta / 2))
        out.append(A)
        va, vb = A - centre, B - centre
        for k in range(1, n):
            f = k / n
            ang = beta * f
            axis = va.cross(vb).normalized()
            from mathutils import Matrix
            out.append(centre + (Matrix.Rotation(ang, 3, axis) @ va))
        out.append(B)
        cur = B
    out.append(pts[-1])
    return out


def primary():
    g = geometry()
    path = _rounded_polyline([g["p0"] + g["t1"] * 0.1, g["Q1"], g["Q2"], g["p3"]], [P.EXH_BEND_R, P.EXH_BEND_R2], n=16)
    pipe = U.tube_along("33_header_primary", [tuple(p) for p in path], P.EXH_PRIMARY_D / 2, smooth=False)
    r_sp, L_sp = P.EXH_SPIGOT_D / 2, P.EXH_SPIGOT_L
    cone_l = (P.EXH_PRIMARY_D - P.EXH_SPIGOT_D) / 2

    def along(name, start, direction, length, r, r2=None):
        c = U.cylinder(name, r, 0.0, length, 0, 0, r2=r2)
        d = Vector(direction).normalized()
        rotq = Vector((0, 0, 1)).rotation_difference(d)
        from mathutils import Matrix
        U.transform(c, Matrix.Translation(start) @ rotq.to_matrix().to_4x4())
        return c
    # round-1 critique: smooth tubes read as plastic. Weld-bead rings (0.7 mm proud, 45 deg lead-in and
    # -out so the standing print has no flat ledge) at the flange exit and at both tangent points of each
    # bend - where a real tube header is welded. Bead index maths follows _rounded_polyline's output.
    rp = P.EXH_PRIMARY_D / 2
    bead_at = [(g["p0"] + g["t1"] * (P.EXH_PORT_DEPTH + P.EXH_FLANGE_PLATE["t"] + 2.5 + 4.0), g["t1"])]
    n_arc = 16
    for i in (1, n_arc + 1, n_arc + 2, 2 * n_arc + 2):
        bead_at.append((path[i], (path[min(i + 1, len(path) - 1)] - path[i - 1]).normalized()))
    for k, (centre, tdir) in enumerate(bead_at):
        start = centre - tdir * 1.4
        U.boolean(pipe, along(f"bead{k}_in", start, tdir, 0.7, rp + 0.05, r2=rp + 0.7), "UNION")
        U.boolean(pipe, along(f"bead{k}_mid", start + tdir * 0.65, tdir, 1.5, rp + 0.7), "UNION")
        U.boolean(pipe, along(f"bead{k}_out", start + tdir * 2.1, tdir, 0.7, rp + 0.7, r2=rp + 0.05), "UNION")
    U.boolean(pipe, along("sp_head", g["p0"] + g["t1"] * 0.3, -g["t1"], L_sp + 0.3, r_sp), "UNION")
    U.boolean(pipe, along("sp_col", g["p3"] - g["t3"] * 0.3, g["t3"], L_sp + cone_l + 0.3, r_sp), "UNION")
    U.boolean(pipe, along("sp_cone", g["p3"] - g["t3"] * 0.3, g["t3"], cone_l + 0.3, P.EXH_PRIMARY_D / 2 - 0.05, r_sp), "UNION")
    U.shade(pipe)
    return pipe


def collector(bank):
    g = geometry()
    xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
    ym = 1.0 if bank == "A" else -1.0                      # bank B: the same geometry mirrored in Y, built directly
    yc, zt = -P.EXH_COLLECTOR_Y * ym, P.EXH_COLLECTOR_TOP_Z
    r0, r1 = P.EXH_COLLECTOR_R
    x_front = max(xs) + P.EXH_X_JOG + P.EXH_COLLECTOR_FRONT_MARGIN
    x_rear = P.STAND["x_offset"] - P.STAND["l"] / 2 + P.EXH_TAIL_MARGIN
    rings = []
    for i in range(9):
        f = i / 8
        x = x_rear + (x_front - x_rear) * f
        r = r1 + (r0 - r1) * f
        # ring sampling offset by 0.37 of a step (and the saddle cutters at 136 segments): with the plain
        # 128 / half-step sampling the saddle generator lines graze body ring vertices and leave a pinched vertex
        rings.append([(x, yc + r * math.cos(a), zt - r + r * math.sin(a)) for a in [2 * math.pi * (k + 0.37) / U.SEGS for k in range(U.SEGS)]])
    col = U.loft(f"35_collector_{bank}", rings)
    # nose cone and a soft rolled tail lip
    nose = U.cylinder("nose", r0, x_front - 0.1, x_front + 5.0, yc, zt - r0, "X", r2=r0 - 4.0)
    U.boolean(col, nose, "UNION")
    # skin round 4: flared tail (3 mm over 8 mm) instead of a flat cut; the bevel softens the lip
    flare = U.cylinder("tail_flare", r1 + 3.0, x_rear - 0.01, x_rear + 8.0, yc, zt - r1, "X", r2=r1 - 0.05)
    U.boolean(col, flare, "UNION")
    U.bevel_edges(col, 1.5, 3, lambda c, d: abs(c.x - x_rear) < 0.3)
    U.boolean(col, U.cylinder("tail_bore", r1 - P.EXH_TAIL_WALL, x_rear - 1, x_rear + 30.0, yc, zt - r1, "X"))
    sad = P.EXH_COLLECTOR_SADDLE
    cone_l = (P.EXH_PRIMARY_D - P.EXH_SPIGOT_D) / 2
    t3 = g["t3"]
    for x in xs:
        mouth = Vector((x + P.EXH_X_JOG, yc, zt - sad))
        from mathutils import Matrix
        rotq = Vector((0, 0, -1)).rotation_difference(t3)             # local -Z (into the socket) -> pipe end direction
        M = Matrix.Translation(mouth) @ rotq.to_matrix().to_4x4()
        bore = P.crush["trumpet_14"]
        # 136 segments (not 128): with 128 the saddle generator lines graze body ring vertices and leave a pinched vertex
        cb = U.cylinder("saddle", P.EXH_PRIMARY_D / 2 + P.CLEARANCE, -0.3, r1 + 2.0, 0, 0, segs=136)
        # conical seat: small end a touch wider than the crush bore so no two surfaces coincide
        seat = U.cylinder("seat", bore["bore"] / 2 + 0.25, -(cone_l + 0.3), -0.29, 0, 0, r2=P.EXH_PRIMARY_D / 2 + P.CLEARANCE, segs=160)
        for c in (cb, seat):
            U.transform(c, M)
            U.boolean(col, c)
        # crush socket below the seat (the seat cone is its lead-in), along the same axis
        depth0, depth1 = -(P.EXH_SPIGOT_L + cone_l + 0.5), -cone_l + 0.5
        b = U.cylinder("sock_bore", bore["bore"] / 2, depth0, depth1, 0, 0)
        U.transform(b, M)
        U.boolean(col, b)
        Rm = rotq.to_matrix()
        offsets = []
        for i in range(bore["n_ribs"]):
            a = 2 * math.pi * i / bore["n_ribs"]
            rib = U.cylinder("sock_rib", bore["rib_r"], depth0 + 0.2, -(cone_l + 0.3) - 0.2, bore["rib_centre_r"] * math.cos(a), bore["rib_centre_r"] * math.sin(a) * ym, segs=24)
            U.transform(rib, M)
            U.boolean(col, rib, "UNION")
            offsets.append(Rm @ Vector((math.cos(a), math.sin(a) * ym, 0.0)))
        # straight section: depth0 .. the seat cone's small end (-(cone_l + 0.3)); rib rings at depth0 + 0.2 and -(cone_l + 0.3) - 0.2
        d_ax, e1 = Rm @ Vector((0, 0, 1)), Rm @ Vector((1, 0, 0))
        hw = math.degrees(math.asin(bore["rib_r"] / bore["rib_centre_r"])) + 2.0
        sectors = [(F.sector_angle(d_ax, e1, off), hw) for off in offsets]
        F.note(col, "trumpet_14 bore", "bore", bore["bore"] / 2, mouth, d_ax, depth0 - 0.05, -(cone_l + 0.3) + 0.05, e1, sectors)
        F.note(col, "trumpet_14 rib tip", "tip", bore["rib_centre_r"] - bore["rib_r"], mouth, d_ax, depth0 + 0.2 - 0.05, -(cone_l + 0.3) - 0.2 + 0.05, e1,
               [(a_, 1.0) for a_, _ in sectors])
    U.shade(col)          # no vertex merge here: remove_doubles opened the socket rims
    return col


def build_all():
    return {"primary": primary(), "collector_A": collector("A"), "collector_B": collector("B")}


def placed(lib, banks=("A", "B")):
    out = []
    for bank in banks:
        xs = P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X
        for i, xc in enumerate(xs):
            p = U.copy(lib["primary"], f"header_{bank}{i+1}")
            if bank == "B":
                m = U.mirror_y(p, f"header_{bank}{i+1}")
                U.delete(p)
                p = m
            U.move(p, xc, 0, 0)
            out.append((f"header_{bank}{i+1}", p))
        out.append((f"collector_{bank}", U.copy(lib[f"collector_{bank}"], f"collector_{bank}")))
    return out
