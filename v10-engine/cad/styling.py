"""Phase 3 styling parts.

  10 cylinder head (x2)    11 cam cover (x2, magnetic)   12 side panel (x2, magnetic)
  13 intake trumpet (x10)  14/15 exhaust headers (A, B mirror)
  16 coil pack (x10, holds each firing LED)   17 intake plenum floor
  18 end cover (x2, magnetic; front hides the belt, rear hides the LED harness)

Everything is built in the bank-local frame of bank A (x along the crank,
y' towards the valley, z' along the bore axis), like the cylinder bank, and
placed with block.to_bank(). Each part is designed to print without supports
in the orientation given by its print_* function.
"""

import math

import cadquery as cq

import block
from common import C, box, crush_x, crush_z, cyl_x, cyl_z, move, polar, rot_x, rot_z, safe_clean

DECK = C.DECK_DIST
TOP = C.DECK_DIST + C.HEAD_H
X0, X1 = C.BLOCK_X_MIN, C.BLOCK_X_MAX
YO, YV = C.BLOCK_Y_OUT, C.BLOCK_Y_VALLEY
S_CHAMFER = C.TRUMPET_FACE_Z * math.sqrt(2.0)          # valley chamfer: y' + z' = S
CYL_X = C.BANK_A_CYL_X
BETWEEN_X = block.bank_between_x()
INS_D = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")


def _yz_prism(poly, x0, x1):
    return cq.Workplane("YZ").workplane(offset=x0).polyline(poly).close().extrude(x1 - x0).val()


def intake_port_centre():
    """(y', z') of the trumpet port centre on the valley chamfer face."""
    y_top = S_CHAMFER - TOP                 # chamfer meets the head top
    z_side = S_CHAMFER - YV                 # chamfer meets the valley side
    return (y_top + YV) / 2, (TOP + z_side) / 2


def _chamfer_dir():
    """Unit vector (y', z') pointing straight up in the engine (out of the chamfer face)."""
    return (math.sqrt(0.5), math.sqrt(0.5))


DEBUG = False


def _chk(shape, label):
    if DEBUG:
        print(f"  {label}: valid={shape.isValid()}", flush=True)
    return shape


HEAD_PEGS = C.HEAD_PEGS    # asymmetric under 180 deg: the head fits one way only


# ---------------------------------------------------------------------------
# 10 Cylinder head
# ---------------------------------------------------------------------------
def _cam_lobe(xc, yc, angle_deg, width=4.0):
    """Cosmetic cam lobe: hull of the base circle and a nose."""
    import numpy as np
    from scipy.spatial import ConvexHull
    zc = TOP + 0.5
    ny, nz = polar(C.CAM_LOBE_R - 1.5, angle_deg)
    pts = []
    for (cy, cz, r) in ((yc, zc, C.CAM_R), (yc + ny, zc + nz, 1.5)):
        pts += [(cy + r * math.cos(t), cz + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    pts = np.array(pts)
    hull = ConvexHull(pts)
    return _yz_prism([tuple(pts[i]) for i in hull.vertices], xc - width / 2, xc + width / 2)


def cylinder_head():
    head = box(X0, X1, YO, YV, DECK, TOP)
    head = cq.Workplane().add(head).edges("|Z").chamfer(3.0).val()
    head = cq.Workplane().add(head).faces("<Z").edges().chamfer(1.5).val()   # casting parting line
    # valley chamfer: an exactly horizontal face (in the engine) for the plenum
    big = 60.0
    head = head.cut(_yz_prism([(S_CHAMFER - TOP - big, TOP + big), (YV + big, TOP + big),
                               (YV + big, S_CHAMFER - YV - big)], X0 - 1, X1 + 1))
    _chk(head, "valley chamfer")
    # --- top: camshafts, lobes, bearing caps --------------------------------
    cx0, cx1 = X0 + C.CAM_END_GAP, X1 - C.CAM_END_GAP
    for yc in C.CAM_Y:
        head = head.fuse(cyl_x(C.CAM_R, cx0, cx1, yc, TOP + 0.5))
    for i, xc in enumerate(CYL_X):
        for j, yc in enumerate(C.CAM_Y):
            for k, dx in enumerate((-10.0, 10.0)):
                ang = (-30.0 + 15.0 * ((i * 3 + j * 2 + k) % 5)) * (1 if (i + j) % 2 else -1)
                head = head.fuse(_cam_lobe(xc + dx, yc, ang))
    _chk(head, "cams+lobes")
    cap_x = list(BETWEEN_X) + [cx0 + 4.0, cx1 - 4.0]
    cap_top = TOP + 0.5 + C.CAM_R + 2.0
    for xc in cap_x:
        for yc in C.CAM_Y:
            cap = box(xc - 4.5, xc + 4.5, yc - C.CAM_CAP_HALF_W, yc + C.CAM_CAP_HALF_W, TOP - 0.1, cap_top)
            cap = cq.Workplane().add(cap).edges("|X and >Z").chamfer(1.5).val()
            head = head.fuse(cap)
    _chk(head, "caps")
    # head screws down the cam lines (through the bearing caps), M3x8 into deck inserts
    for xc in BETWEEN_X:
        for yc in C.HEAD_SCREW_Y:
            head = head.cut(cyl_z(C.hole(C.M3_CBORE) / 2, DECK + C.SCREW_FLOOR, cap_top + 1, xc, yc))
            head = head.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, DECK - 1, DECK + C.SCREW_FLOOR + 0.1, xc, yc))
    _chk(head, "screws")
    # --- per cylinder: LED well, coil-pack socket, chamber details ------------
    led_top = DECK + C.LED_ROOF + C.LED["t"] + 0.3
    for xc in CYL_X:
        head = head.cut(cyl_z(C.LED_APERTURE / 2, DECK - 1, DECK + C.LED_ROOF + 0.01, xc, 0))
        head = head.cut(cyl_z((C.LED["d"] + 0.6) / 2, DECK + C.LED_ROOF, led_top + 0.01, xc, 0))
        head = head.cut(crush_z(C.COIL["shaft_d"], led_top, TOP + 0.01, xc, 0, "coil_10", entry="hi"))
        # valve faces in the chamber roof (cosmetic, 0.4 mm deep - small bridges only)
        for dx in (-9.0, 9.0):
            head = head.cut(cyl_z(6.5, DECK - 1, DECK + 0.4, xc + dx, 9.0))      # intake (valley side)
            head = head.cut(cyl_z(5.5, DECK - 1, DECK + 0.4, xc + dx, -9.0))     # exhaust
        # rail tops: snug pockets in the underside capture the guide rails
        head = head.cut(cyl_z(C.hole(C.RAIL_DIA, "rail_3_slip") / 2, DECK - 1, DECK + 2.0, xc, C.RAIL_OFFSET))
        # intake port on the valley chamfer (axis = engine vertical), crush fit for the trumpet
        py, pz = intake_port_centre()
        port = crush_z(C.TRUMPET["spigot_d"], -8.0, 0.01, 0, 0, "trumpet_14", entry="hi")
        port = port.rotate((0, 0, 0), (1, 0, 0), -45.0)                 # +Z -> engine vertical
        head = head.cut(port.translate(cq.Vector(xc, py, pz)))
        # exhaust port boss + insert on the outboard face
        head = head.fuse(cq.Solid.makeCylinder(8.5, 1.0, cq.Vector(xc, YO + 0.01, C.EXH_PORT_Z), cq.Vector(0, -1, 0)))
        head = head.cut(cq.Solid.makeCylinder(INS_D / 2, C.INSERT_DEPTH + 1.0,
                                              cq.Vector(xc + C.EXH_SCREW_DX, YO - 1.0, C.EXH_SCREW_Z), cq.Vector(0, 1, 0)))
    _chk(head, "per-cylinder")
    # --- wiring loom groove: along the coil-pack row, turning to the valley at both ends
    lw, ld = C.LOOM["w"], C.LOOM["d"]
    lx0, lx1 = X0 + C.CAM_END_GAP / 2, X1 - C.CAM_END_GAP / 2
    head = head.cut(box(lx0 - lw / 2, lx1 + lw / 2, -lw / 2, lw / 2, TOP - ld, TOP + 1))
    for lx in (lx0, lx1):
        head = head.cut(box(lx - lw / 2, lx + lw / 2, -lw / 2, YV + 1, TOP - ld, TOP + 1))
    _chk(head, "loom")
    # cam-cover magnets in the outboard strip
    for xc in (CYL_X[0], CYL_X[1], CYL_X[3], CYL_X[4]):
        head = head.cut(crush_z(C.MAGNET["d"], TOP - C.MAGNET["h"] - 0.3, TOP + 0.01, xc, -28.5, "magnet_6", entry="hi"))
    _chk(head, "magnets")
    # locating pegs into the deck
    for x, y in HEAD_PEGS:
        head = head.fuse(cyl_z(2.5, DECK - 2.5, DECK + 0.1, x, y))
    _chk(head, "pegs")
    return safe_clean(head)


def head_peg_holes():
    """Cutters for the deck (cylinder bank) that receive the head pegs."""
    out = None
    for x, y in HEAD_PEGS:
        c = cyl_z(C.hole(5.0, "spigot") / 2, DECK - 3.0, DECK + 1, x, y)
        out = c if out is None else out.fuse(c)
    return out


# ---------------------------------------------------------------------------
# 16 Coil pack (one per cylinder): holds the LED down, carries its wires
# ---------------------------------------------------------------------------
def coil_pack():
    """Local frame: shaft along -Z from z=0 (head top) down to the LED."""
    shaft_len = TOP - (DECK + C.LED_ROOF + C.LED["t"] + 0.3)
    c = C.COIL
    shaft = cyl_z(c["shaft_d"] / 2, -shaft_len, 0.01)
    body = (cq.Workplane("XY").ellipse(c["l"] / 2, c["w"] / 2).extrude(c["h"]).val())
    body = cq.Workplane().add(body).faces(">Z").edges().chamfer(1.5).val()
    part = shaft.fuse(body)
    part = part.cut(cyl_z(c["bore"] / 2, -shaft_len - 1, 6.0))                    # wire bore
    part = part.cut(cyl_z(4.6, -shaft_len - 1, -shaft_len + 1.5))                 # clears LED solder pads
    part = part.cut(box(-c["l"] / 2 - 1, 0, -c["bore"] / 2 + 0.5, c["bore"] / 2 - 0.5, 0.0, 6.0))  # side exit into the loom
    return safe_clean(part)


def print_coil(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)          # flat chamfered top on the bed, shaft up


def placed_coils(coil):
    out = []
    for bank in ("A", "B"):
        for i, xc in enumerate(CYL_X):
            out.append((f"coil_{bank}{i+1}", block.to_bank(move(coil, xc, 0, TOP), bank), "red"))
    return out


# ---------------------------------------------------------------------------
# 11 Cam cover (magnetic) - printed TOP-DOWN on the textured plate
# ---------------------------------------------------------------------------
def cam_cover():
    cc = C.CAM_COVER
    x0, x1 = X0 + cc["end_inset"], X1 - cc["end_inset"]
    y0, y1, h, w = cc["y0"], cc["y1"], cc["h"], cc["wall"]
    z0, z1 = TOP, TOP + h
    outer = box(x0, x1, y0, y1, z0, z1)
    # 45 deg chamfers on the top edges (fillets would need support upside-down)
    outer = cq.Workplane().add(outer).faces(">Z").edges().chamfer(cc["chamfer"]).val()
    outer = cq.Workplane().add(outer).edges("|Z").chamfer(2.0).val()
    cover = outer.cut(box(x0 + w, x1 - w, y0 + w, y1 - w, z0 - 1, z1 - w))
    # magnet pillars (full height, so they print attached to the top wall)
    for xc in (CYL_X[0], CYL_X[1], CYL_X[3], CYL_X[4]):
        pil = cyl_z(4.5, z0, z1 - w + 0.1, xc, -28.5).intersect(outer)
        cover = cover.fuse(pil)
        cover = cover.cut(crush_z(C.MAGNET["d"], z0 - 0.01, z0 + C.MAGNET["h"] + 0.3, xc, -28.5, "magnet_6", entry="lo"))
    # top styling: two shallow grooves framing the coil-pack row (0.6 mm, bed face)
    for yg in (-9.5, 7.5):
        cover = cover.cut(box(x0 + 12, x1 - 12, yg - 0.5, yg + 0.5, z1 - 0.6, z1 + 1))
    # the coil packs stand up through the cover (F1-style row of coils on top)
    for xc in CYL_X:
        hole_ = (cq.Workplane("XY").workplane(offset=z1 - w - 1).center(xc, 0.0)
                 .ellipse(C.COIL["l"] / 2 + 1.0, C.COIL["w"] / 2 + 1.0).extrude(w + 2).val())
        cover = cover.cut(hole_)
    return safe_clean(cover)


def print_cam_cover(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


# ---------------------------------------------------------------------------
# 12 Side panel (magnetic) - covers the cut-away windows
# ---------------------------------------------------------------------------
def side_panel():
    sp = C.SIDE_PANEL
    xa = CYL_X[-1] - C.WINDOW_HALF_W - 4.0
    xb = CYL_X[0] + C.WINDOW_HALF_W + 4.0
    yb = YO                                   # back face sits on the block
    yf = YO - sp["t"]
    panel = box(xa, xb, yf, yb, sp["z0"], sp["z1"])
    panel = cq.Workplane().add(panel).edges("|Y").fillet(4.0).val()
    panel = cq.Workplane().add(panel).faces("<Y").edges().chamfer(1.0).val()
    # one shallow barrel bulge per cylinder (reads as a cast block side)
    r = 30.0
    for xc in CYL_X:
        barrel = cyl_z(r, sp["z0"] + 4, sp["z1"] - 4, xc, yf - sp["bulge"] + r)
        slab = box(xc - 20, xc + 20, yf - sp["bulge"], yf + 0.01, sp["z0"] + 4, sp["z1"] - 4)
        panel = panel.fuse(barrel.intersect(slab))
    for xm in BETWEEN_X:
        panel = panel.cut(crush_x(C.MAGNET["d"], 0, C.MAGNET["h"] + 0.3, 0, 0, "magnet_6", entry="lo")
                          .rotate((0, 0, 0), (0, 0, 1), -90)          # axis along -Y'
                          .translate(cq.Vector(xm, yb + 0.01, C.SIDE_PANEL_MAGNET_Z)))
    return safe_clean(panel)


def print_side_panel(s):
    """Back face down, bulges up."""
    s = s.rotate((0, 0, 0), (1, 0, 0), -90)          # -Y' (outer face) -> +Z
    return s


# ---------------------------------------------------------------------------
# 13 Intake trumpet (printed version; M05 is the machined aluminium option)
# ---------------------------------------------------------------------------
def trumpet():
    """Local frame: axis +Z, underside of the flange at z=0 (sits on the throttle body)."""
    t = C.TRUMPET
    spl = C.THROTTLE["h"] + C.PLENUM_T + 7.5          # through throttle body + rail into the head port
    H, rb = t["height"], t["bell_od"] / 2
    zb = H - t["bell_h"]
    ro = t["spigot_d"] / 2
    prof = [(ro, -spl), (ro, 0.0), (t["flange_d"] / 2, 0.0), (t["flange_d"] / 2, 0.6),
            (t["base_od"] / 2, t["flange_t"]), (t["top_od"] / 2, zb),
            # outer bell: a smooth flare (a narrowing cone when printed mouth-down)
            (t["top_od"] / 2 + 1.0, zb + 4.0), (rb - 2.5, zb + 8.0), (rb - 0.6, H - 1.2), (rb, H - 0.4), (rb - 0.6, H),
            # flat lip, then the inner flare: every step <= 45 deg so it prints mouth-down
            (rb - 3.0, H), (rb - 5.5, H - 2.5), (t["bore"] / 2 + 3.0, H - 6.0), (t["bore"] / 2, zb),
            (t["bore"] / 2, 2.0), (ro - 2.5, 0.0), (ro - 2.5, -spl)]
    body = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    return safe_clean(body)


def print_trumpet(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)      # bell mouth on the bed


# ---------------------------------------------------------------------------
# 17 Intake plenum floor (global frame) - trumpets plug through it into the heads
# ---------------------------------------------------------------------------
def trumpet_positions():
    """Global (x, y) of every trumpet axis."""
    py, pz = intake_port_centre()
    out = []
    for bank in ("A", "B"):
        for xc in CYL_X:
            p = block.to_bank(cq.Vertex.makeVertex(xc, py, pz), bank)
            out.append((p.X, p.Y))
    return out


def plenum_floor():
    """Ladder frame: one throttle rail per bank (5 throttle bodies each) joined
    by cross braces over the valley. Sits on both heads' valley chamfers."""
    z0 = C.TRUMPET_FACE_Z
    t = C.PLENUM_T
    pos = trumpet_positions()
    ya = sum(y for x, y in pos[:5]) / 5          # bank A rail centre (global y)
    yb = sum(y for x, y in pos[5:]) / 5
    frame = None
    for yc, pts in ((ya, pos[:5]), (yb, pos[5:])):
        xs = [x for x, y in pts]
        rail = box(min(xs) - 20.0, max(xs) + 20.0, yc - C.RAIL_W / 2, yc + C.RAIL_W / 2, z0, z0 + t)
        rail = cq.Workplane().add(rail).edges("|Z").fillet(C.RAIL_W / 2 - 0.5).val()
        frame = rail if frame is None else frame.fuse(rail)
        for x, y in pts:
            tb = cyl_z(C.THROTTLE["d"] / 2, z0 + t - 0.01, z0 + t + C.THROTTLE["h"], x, y)
            tb = cq.Workplane().add(tb).faces(">Z").edges().chamfer(1.0).val()
            frame = frame.fuse(tb)
    for xb in (-95.0, -32.0, 32.0, 95.0):
        frame = frame.fuse(box(xb - 5.0, xb + 5.0, ya, yb, z0, z0 + t))
    for x, y in pos:
        frame = frame.cut(cyl_z((C.TRUMPET["spigot_d"] + 0.6) / 2, z0 - 1, z0 + t + C.THROTTLE["h"] + 1, x, y))
    return safe_clean(frame)


def print_plenum(s):
    return s                                        # rails flat on the bed, throttle bodies up


# ---------------------------------------------------------------------------
# 14 / 15 Exhaust headers - D-section (flat back towards the head), so the
# whole header prints flat-back-down with no supports
# ---------------------------------------------------------------------------
EXH_YC = C.EXH_BACK_Y - C.EXH_OFFSET      # exhaust tube centre plane


def _tube(points, r, tangents=None):
    """Swept round tube along a spline in the plane y' = EXH_YC."""
    yb = EXH_YC
    pts3 = [cq.Vector(x, yb, z) for x, z in points]
    path = cq.Edge.makeSpline(pts3, tangents=[cq.Vector(t[0], 0, t[1]) for t in tangents] if tangents else None)
    t0 = path.tangentAt(0)
    prof = cq.Wire.makeCircle(r, pts3[0], t0)
    return cq.Solid.sweep(prof, [], cq.Wire.assembleEdges([path]), makeSolid=True, isFrenet=False)


def exhaust_header():
    """Bank A header, bank-local frame. Collector runs to the rear (-x)."""
    rp, rt = C.EXH_R_PRIMARY, C.EXH_R_TRUNK
    zp, zt = C.EXH_PORT_Z, C.EXH_TRUNK_Z
    joins = [xc - C.EXH_JOIN_DX for xc in CYL_X]
    solid = None
    # keep only the outboard half of every piece (flat back on y' = EXH_BACK_Y);
    # cutting each piece before the union is far more robust in OCC
    half = box(C.EXH_TAIL_X - 30, X1 + 30, C.EXH_BACK_Y - 30, C.EXH_BACK_Y, zp - 30, C.EXH_TAIL_Z + 30)

    def add(s):
        nonlocal solid
        s = s.intersect(half)
        solid = s if solid is None else solid.fuse(s)

    for xc, xj in zip(CYL_X, joins):
        # S-bend: leaves the port rearward-down, dips, sweeps up into the collector.
        # A smooth function (not free spline points) keeps every bend radius
        # above ~1.9x the pipe radius, so the swept tube is always valid.
        L = xc - xj
        pts = []
        for i in range(21):
            t = i / 20.0
            pts.append((xc - L * t, zp + (zt - zp) * (3 * t * t - 2 * t ** 3)
                        - C.EXH_DIP * math.sin(math.pi * t) * (1 - t)))
        add(_tube(pts, rp))
        add(cq.Solid.makeSphere(rp, cq.Vector(xc, EXH_YC, zp)))
    # trunk: cones growing after every merge, spheres at the joins
    radii = [rp + (rt - rp) * (i + 1) / len(joins) for i in range(len(joins))]
    for i in range(len(joins) - 1):
        a, b = joins[i], joins[i + 1]
        add(cq.Solid.makeCone(radii[i], radii[i + 1], a - b, cq.Vector(a, EXH_YC, zt), cq.Vector(-1, 0, 0)))
        add(cq.Solid.makeSphere(radii[i], cq.Vector(a, EXH_YC, zt)))
    xe = joins[-1]
    # tail: straight trunk to the bend, a true quarter-circle bend (radius 2x the
    # pipe radius, so the swept tube can never fold through itself), then a
    # short vertical stack - the "periscope" exit
    rb = 2.0 * rt
    xs = C.EXH_TAIL_X + rb
    add(cq.Solid.makeSphere(rt, cq.Vector(xe, EXH_YC, zt)))
    add(cyl_x(rt, xs - 0.01, xe + 0.01, EXH_YC, zt))
    yb = EXH_YC
    arc = cq.Edge.makeThreePointArc(cq.Vector(xs, yb, zt),
                                    cq.Vector(xs - rb * math.sqrt(0.5), yb, zt + rb - rb * math.sqrt(0.5)),
                                    cq.Vector(C.EXH_TAIL_X, yb, zt + rb))
    prof = cq.Wire.makeCircle(rt, cq.Vector(xs, yb, zt), cq.Vector(-1, 0, 0))
    add(cq.Solid.sweep(prof, [], cq.Wire.assembleEdges([arc]), makeSolid=True, isFrenet=False))
    add(cyl_z(rt, zt + rb - 0.01, C.EXH_TAIL_Z, C.EXH_TAIL_X, yb))
    hdr = solid.Solids()[0] if len(solid.Solids()) == 1 else solid
    # tail-pipe opening
    hdr = hdr.cut(cyl_z(rt - 2.2, C.EXH_TAIL_Z - 12, C.EXH_TAIL_Z + 1, C.EXH_TAIL_X, EXH_YC))
    # port flanges with one bolt each (M3x8 into the head insert)
    f = C.EXH_FLANGE
    for xc in CYL_X:
        fl = (cq.Workplane("XZ").workplane(offset=-C.EXH_BACK_Y)
              .pushPoints([(xc, zp)]).circle(f["d"] / 2 + 1.0).extrude(f["t"]).val())
        fl2 = (cq.Workplane("XZ").workplane(offset=-C.EXH_BACK_Y)
               .pushPoints([(xc + C.EXH_SCREW_DX, C.EXH_SCREW_Z)]).circle(5.0).extrude(f["t"]).val())
        hdr = hdr.fuse(fl).fuse(fl2)
        hdr = hdr.cut(cq.Solid.makeCylinder(C.hole(C.M3_CLEAR) / 2, 20, cq.Vector(xc + C.EXH_SCREW_DX, C.EXH_BACK_Y + 1, C.EXH_SCREW_Z), cq.Vector(0, -1, 0)))
    return safe_clean(hdr)


def mirror_header(h):
    """Bank B header in its own bank-local frame: mirror about the block centre x."""
    xm = (CYL_X[0] + CYL_X[-1]) / 2
    return h.mirror("YZ", (xm, 0, 0))


def print_header(s):
    """Flat back down: the back plane (y' = EXH_BACK_Y, facing +y') goes onto the bed."""
    return s.rotate((0, 0, 0), (1, 0, 0), -90)      # flat back (+Y' normal) -> -Z, onto the bed


# ---------------------------------------------------------------------------
# 18 End cover (front: belt cover / rear: harness cover) - magnetic, global frame
# ---------------------------------------------------------------------------
def _end_profile(off, x0, x1):
    r = C.COVER_R - off
    zb = C.BASE_TOP_Z - 1.0
    zc = C.END_COVER_ZC
    return cyl_x(r, x0, x1, 0, zc).fuse(box(x0, x1, -r, r, zb, zc))


def end_cover():
    x0, x1, w = C.COVER_X0, C.COVER_X1, C.COVER_WALL
    outer = _end_profile(0.0, x0, x1).cut(box(x0 - 1, x1 + 1, -50, 50, C.BASE_TOP_Z - 5, C.BASE_TOP_Z))
    outer = cq.Workplane().add(outer).faces(">X").edges().chamfer(2.0).val()
    cover = outer.cut(_end_profile(w, x0 - 1, x1 - w))
    for y, z in C.COVER_MAGNETS:
        pil = cyl_x(C.COVER_PILLAR_R, x0, x1 - w + 0.1, y, z)
        # web from the pillar to the nearest outer wall (never towards the pulley)
        ang = (90.0 if y > 0 else -90.0) if abs(y) > 15.0 else 0.0
        web = (cq.Workplane().add(box(x0, x1 - w + 0.1, -C.COVER_PILLAR_R, C.COVER_PILLAR_R, 0, 12)).val()
               .rotate((0, 0, 0), (1, 0, 0), -ang).translate(cq.Vector(0, y, z)))
        cover = cover.fuse(pil.fuse(web).intersect(_end_profile(0.0, x0, x1)))
        cover = cover.cut(crush_x(C.MAGNET["d"], x0 - 0.5, x0 + C.MAGNET["h"] + 0.3, y, z, "magnet_6", entry="lo"))
    # harness notch at the top of the back edge (used at the rear)
    cover = cover.cut(box(x0 - 1, x0 + 7, -6, 6, C.FACE_DIST * math.sqrt(2) - 6, C.END_COVER_ZC + C.COVER_R + 1))
    # face detail: an engraved ring round the crank axis (prints face-down)
    ring = cyl_x(17.0, x1 - 0.7, x1 + 1, 0, 0).cut(cyl_x(15.8, x1 - 1, x1 + 2, 0, 0))
    cover = cover.cut(ring)
    return safe_clean(cover)


def print_end_cover(s):
    return s.rotate((0, 0, 0), (0, 1, 0), 90)       # outer face on the textured plate


def build_all():
    head = cylinder_head()
    hdr = exhaust_header()
    return {"head": head, "cam_cover": cam_cover(), "side_panel": side_panel(), "trumpet": trumpet(),
            "plenum": plenum_floor(), "header_A": hdr, "header_B": mirror_header(hdr),
            "coil": coil_pack(), "end_cover": end_cover()}


def placed(lib):
    out = []
    for bank in ("A", "B"):
        out.append((f"head_{bank}", block.to_bank(lib["head"], bank), "block"))
        out.append((f"cam_cover_{bank}", block.to_bank(lib["cam_cover"], bank), "carbon"))
        out.append((f"side_panel_{bank}", block.to_bank(lib["side_panel"], bank), "carbon"))
        out.append((f"exhaust_{bank}", block.to_bank(lib["header_" + bank], bank), "gold"))
    out += placed_coils(lib["coil"])
    out.append(("plenum", lib["plenum"], "carbon"))
    t = lib["trumpet"]
    for i, (x, y) in enumerate(trumpet_positions()):
        out.append((f"trumpet_{i+1}", move(t, x, y, C.TRUMPET_FACE_Z + C.PLENUM_T + C.THROTTLE["h"]), "steel"))
    out.append(("end_cover_front", lib["end_cover"], "carbon"))
    out.append(("end_cover_rear", rot_z(lib["end_cover"], 180), "carbon"))
    return out
