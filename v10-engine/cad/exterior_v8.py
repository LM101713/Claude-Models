"""Stock-car V8 exterior. Bank-local frame (bank A convention: x along the
crank, y' towards the valley, z' along the bore from the crank axis), placed
with block.to_bank(); headers and intake are built in the engine frame.

  30 cylinder head (x2)            31 valve cover (x2, magnetic)
  32 spark-plug boot (x8, lit)     33 header primary pipe (x8, one shape)
  34 header flange plate (x2)      35 collector (x2, mirror pair)
  36 intake manifold (provisional, whole engine)

Printing: head deck-down; valve cover top-down on the textured plate; boots
and primaries standing; flange plate flat; collector lying on its flat back
(85 % round, like the V10 pipes); intake: see docs (large part, split later).
"""

import math

import cadquery as cq

import block
from common import C, box, crush_z, cyl_x, cyl_z, move, safe_clean

DECK = C.DECK_DIST
TOP = C.DECK_DIST + C.HEAD_H
X0, X1 = C.BLOCK_X_MIN, C.BLOCK_X_MAX
YO, YV = C.BLOCK_Y_OUT, C.BLOCK_Y_VALLEY
CYL_X = C.BANK_A_CYL_X
BETWEEN_X = block.bank_between_x()
INS_D = C.hole(C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3")
PORT_Z = DECK + C.EXH_PORT_Z
BOOT_X = [x + C.PLUG_BOOT["dx"] for x in CYL_X]
BOOT_Z = DECK + C.PLUG_BOOT["z"]
FP = C.EXH_FLANGE_PLATE
PLATE_SCREW_X = (X0 + FP["end_inset"] + C.HEADER_SCREW_X_INSET, X1 - FP["end_inset"] - C.HEADER_SCREW_X_INSET)
PLATE_SCREW_Z = DECK + FP["z1"] - 5.0


def _rrect_prism(cx, cy, w, h, r, z0, z1):
    """Rounded-rectangle prism along Z."""
    return (cq.Workplane("XY").workplane(offset=z0).center(cx, cy).rect(w, h).extrude(z1 - z0)
            .edges("|Z").fillet(r).val())


def _rrect_wire(cx, cy, w, h, r, z):
    pts = [cq.Vector(cx - w / 2, cy - h / 2, z), cq.Vector(cx + w / 2, cy - h / 2, z),
           cq.Vector(cx + w / 2, cy + h / 2, z), cq.Vector(cx - w / 2, cy + h / 2, z)]
    w_ = cq.Wire.makePolygon(pts, close=True)
    return w_.fillet2D(r, w_.Vertices())


def _rounded_path(points, radii):
    """Polyline through `points` with each interior corner rounded by the
    matching radius (tangent-continuous line-arc-line wire)."""
    pts = [cq.Vector(*p) if not isinstance(p, cq.Vector) else p for p in points]
    edges, cur = [], pts[0]
    for i in range(1, len(pts) - 1):
        P, Q, R = pts[i - 1], pts[i], pts[i + 1]
        t1, t2 = (Q - P).normalized(), (R - Q).normalized()
        beta = math.acos(max(-1.0, min(1.0, t1.dot(t2))))
        if beta < 1e-6:
            continue
        r = radii[i - 1]
        tl = r * math.tan(beta / 2)
        assert tl <= (Q - P).Length + 1e-6 and tl <= (R - Q).Length + 1e-6, "corner radius too big for its legs"
        A, B = Q - t1 * tl, Q + t2 * tl
        centre = Q + (t2 - t1).normalized() * (r / math.cos(beta / 2))
        M = centre + (Q - centre).normalized() * r
        if (A - cur).Length > 1e-6:
            edges.append(cq.Edge.makeLine(cur, A))
        edges.append(cq.Edge.makeThreePointArc(A, M, B))
        cur = B
    if (pts[-1] - cur).Length > 1e-6:
        edges.append(cq.Edge.makeLine(cur, pts[-1]))
    return cq.Wire.assembleEdges(edges)


def _ybore(r, x, z, depth, from_outside=False):
    """Cylinder along +Y through the flange plate at (x, z)."""
    if from_outside:
        return cq.Solid.makeCylinder(r, depth, cq.Vector(x, YO - FP["t"] - 1.0, z), cq.Vector(0, 1, 0))
    return cq.Solid.makeCylinder(r, depth + 2.0, cq.Vector(x, YO - depth - 1.0, z), cq.Vector(0, 1, 0))


def _bank_pt(yl, zl, bank="A"):
    """Bank-local (y', z') at x=0 -> engine-frame Vector."""
    v = block.to_bank(cq.Vertex.makeVertex(0, yl, zl), bank)
    return cq.Vector(0, v.Y, v.Z)


# ---------------------------------------------------------------------------
# 30 Cylinder head
# ---------------------------------------------------------------------------
def cylinder_head():
    head = box(X0, X1, YO, YV, DECK, TOP)
    head = cq.Workplane().add(head).edges("|Z").chamfer(3.0).val()
    head = cq.Workplane().add(head).faces("<Z").edges("|X").chamfer(1.5).val()     # parting line
    head = cq.Workplane().add(head).faces(">Z").edges("|X").chamfer(2.0).val()
    # valve-cover seat: 1 mm recess, cover footprint + clearance, 4 magnets
    vc = C.VC
    seat = _rrect_prism((X0 + X1) / 2, (vc["y0"] + vc["y1"]) / 2, (X1 - X0) - 2 * vc["x_inset"] + 2 * C.CLEARANCE,
                        vc["y1"] - vc["y0"] + 2 * C.CLEARANCE, vc["r"] + C.CLEARANCE, TOP - 1.0, TOP + 1)
    head = head.cut(seat)
    for xc in (CYL_X[0], CYL_X[-1], BETWEEN_X[0], BETWEEN_X[-1]):
        head = head.cut(crush_z(C.MAGNET["d"], TOP - 1.0 - C.MAGNET["h"] - C.MAGNET_DEPTH_CLEAR, TOP + 0.01,
                                xc, C.VC_MAGNET_Y, "magnet_6", entry="hi"))
    # head screws (between cylinders, two rows) down to the deck inserts, hidden under the cover
    for xc in BETWEEN_X:
        for yc in C.HEAD_SCREW_Y:
            head = head.cut(cyl_z(C.hole(C.M3_CBORE) / 2, DECK + C.SCREW_FLOOR, TOP + 1, xc, yc))
            head = head.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, DECK - 1, DECK + C.SCREW_FLOOR + 0.1, xc, yc))
    # firing-LED strip in the deck face (as the V10): groove closed short of the ends, lead pockets
    gw, gd, ew = C.LED_GROOVE["w"], C.LED_GROOVE["d"], C.LED_GROOVE["end_wall"]
    head = head.cut(box(X0 + ew, X1 - ew, -gw / 2, gw / 2, DECK - 1, DECK + gd))
    ww, wd = C.LED_WIRE_GROOVE["w"], C.LED_WIRE_GROOVE["d"]
    for xa in (X0 + ew, X1 - ew - ww):
        head = head.cut(box(xa, xa + ww, -gw / 2, YV + 1, DECK - 1, DECK + wd))
    it = C.INTAKE
    for xc in CYL_X:
        # two-valve chamber roof: one intake, one exhaust recess (cosmetic, lit)
        for yv in C.HEAD_VALVE_Y:
            head = head.cut(cyl_z(C.HEAD_VALVE_R, DECK - 1, DECK + 0.4, xc, yv))
        # guide-rail pockets (crush) with a lead-in cone
        rz1 = DECK + C.RAIL_HEAD_ENGAGE + C.RAIL_POCKET_EXTRA
        head = head.cut(crush_z(C.RAIL_DIA, DECK, rz1, xc, C.RAIL_OFFSET, "rail_3", entry="lo"))
        r_in = C.hole(C.RAIL_DIA) / 2 + C.CRUSH_RELIEF / 2
        head = head.cut(cq.Solid.makeCone(r_in + 1.0, r_in, 1.0, cq.Vector(xc, C.RAIL_OFFSET, DECK - 0.01),
                                          cq.Vector(0, 0, 1)))
        # exhaust port: 20 mm counterbore, 14 mm crush socket for the primary's spigot
        head = head.cut(cq.Solid.makeCylinder(C.EXH_PORT_D / 2, C.EXH_PORT_DEPTH + 1.0, cq.Vector(xc, YO - 1.0, PORT_Z),
                                              cq.Vector(0, 1, 0)))
        sock = crush_z(C.EXH_SPIGOT_D, 0, C.EXH_SPIGOT_L + C.EXH_PORT_DEPTH + 0.5, 0, 0, "trumpet_14", entry="lo")
        sock = sock.rotate((0, 0, 0), (1, 0, 0), -90)            # +Z -> +Y (into the head from the outboard face)
        head = head.cut(sock.translate(cq.Vector(xc, YO - 0.01, PORT_Z)))
        # intake port pocket on the valley face (the runner end sits in it)
        pocket = _rrect_prism(0, 0, it["runner_w"] + 2 * C.RUNNER_POCKET_CLEAR, it["runner_h"] + 2 * C.RUNNER_POCKET_CLEAR,
                              it["runner_r"], -it["port_depth"], 1.0)
        pocket = pocket.rotate((0, 0, 0), (1, 0, 0), -90)         # +Z -> +Y
        head = head.cut(pocket.translate(cq.Vector(xc, YV - 0.01, DECK + it["port_z"])))
    # spark-plug boot sockets (crush) over a hidden LED strip groove in the outboard face
    bs = C.BOOT_STRIP
    head = head.cut(box(X0 + 6, X1 - 6, YO - 1, YO + bs["d"], BOOT_Z - bs["w"] / 2, BOOT_Z + bs["w"] / 2))
    pb = C.PLUG_BOOT
    for xb in BOOT_X:
        sock = crush_z(pb["shaft_d"], 0, pb["shaft_l"] + bs["d"] + 0.5, 0, 0, "boot_9", entry="lo")
        sock = sock.rotate((0, 0, 0), (1, 0, 0), -90)
        head = head.cut(sock.translate(cq.Vector(xb, YO - 0.01, BOOT_Z)))
    # header flange-plate screws: horizontal inserts in the outboard face
    for xs in PLATE_SCREW_X:
        head = head.cut(cq.Solid.makeCylinder(INS_D / 2, C.INSERT_DEPTH + 1.0, cq.Vector(xs, YO - 1.0, PLATE_SCREW_Z),
                                              cq.Vector(0, 1, 0)))
    return safe_clean(head)


def print_head(s):
    return s                                 # deck face down


# ---------------------------------------------------------------------------
# 31 Valve cover (magnetic) - printed top-down on the textured plate
# ---------------------------------------------------------------------------
def valve_cover():
    """Crisp box with a 1.5 mm top edge, a shallow recessed top panel, a 5 mm
    bolt rim with hex-less bolt heads every 28 mm, knurled oil cap, 4 magnets."""
    vc = C.VC
    x0, x1 = X0 + vc["x_inset"], X1 - vc["x_inset"]
    y0, y1, h, w = vc["y0"], vc["y1"], vc["h"], vc["wall"]
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    z0, z1 = TOP - 1.0, TOP - 1.0 + h                              # sits 1 mm down in the head's seat
    outer = _rrect_prism(xm, ym, x1 - x0, y1 - y0, vc["r"], z0, z1)
    outer = cq.Workplane().add(outer).faces(">Z").edges().chamfer(vc["chamfer"]).val()
    cover = outer.cut(_rrect_prism(xm, ym, x1 - x0 - 2 * w, y1 - y0 - 2 * w, max(0.5, vc["r"] - w), z0 - 1, z1 - w))
    # recessed top panel
    pi, pd = vc["panel_inset"], vc["panel_depth"]
    cover = cover.cut(_rrect_prism(xm, ym, x1 - x0 - 2 * pi, y1 - y0 - 2 * pi, 2.0, z1 - pd, z1 + 1))
    # bolt rim: a band standing proud all round the base, with bolt heads on it
    rt, rh = vc["rim_t"], vc["rim_h"]
    rim = _rrect_prism(xm, ym, x1 - x0 + 2 * rt, y1 - y0 + 2 * rt, vc["r"] + rt, z0 + 1.0, z0 + 1.0 + rh)
    rim = rim.cut(_rrect_prism(xm, ym, x1 - x0 - 2 * w, y1 - y0 - 2 * w, max(0.5, vc["r"] - w), z0, z1))
    rim = cq.Workplane().add(rim).faces(">Z").edges().chamfer(0.8).val()
    cover = cover.fuse(rim)
    n = int((x1 - x0 - 16.0) // vc["bolt_pitch"])
    xb = [x0 + 8.0 + i * (x1 - x0 - 16.0) / n for i in range(n + 1)]
    heads = []
    for x in xb:
        for yb in (y0 - rt / 2 + 0.3, y1 + rt / 2 - 0.3):
            heads.append((x, yb))
    for yb in (ym - 10.0, ym + 10.0):
        heads += [(x0 - rt / 2 + 0.3, yb), (x1 + rt / 2 - 0.3, yb)]
    zb = z0 + 1.0 + rh
    for x, yb in heads:
        bolt = cyl_z(vc["bolt_d"] / 2, zb - 0.5, zb + 1.6, x, yb)
        bolt = cq.Workplane().add(bolt).faces(">Z").edges().chamfer(0.8).val()
        cover = cover.fuse(bolt)
    # knurled oil cap on top
    cx, cy = (X1 - 40.0 if vc["cap_x"] < 0 else X0 + 40.0), vc["cap_y"]
    cap = cyl_z(vc["cap_d"] / 2, z1 - pd - 0.5, z1 + vc["cap_h"], cx, cy)
    cap = cq.Workplane().add(cap).faces(">Z").edges().chamfer(1.5).val()
    nk = 24
    for i in range(nk):
        groove = box(-0.6, 0.6, vc["cap_d"] / 2 - 0.7, vc["cap_d"] / 2 + 1, z1 + 1.0, z1 + vc["cap_h"] - 1.6)
        groove = groove.rotate((0, 0, 0), (0, 0, 1), i * 360.0 / nk).translate(cq.Vector(cx, cy, 0))
        cap = cap.cut(groove)
    cover = cover.fuse(cap)
    # magnet pillars down to the head top
    for xc in (CYL_X[0], CYL_X[-1], BETWEEN_X[0], BETWEEN_X[-1]):
        pil = cyl_z(4.5, z0, z1 - w + 0.1, xc, C.VC_MAGNET_Y).intersect(outer)
        cover = cover.fuse(pil)
        cover = cover.cut(crush_z(C.MAGNET["d"], z0 - 0.5, z0 + C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR, xc, C.VC_MAGNET_Y,
                                  "magnet_6", entry="lo"))
    return safe_clean(cover)


def print_valve_cover(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180)


# ---------------------------------------------------------------------------
# 32 Spark-plug boot (lit): translucent, pressed through the flange plate into the head
# ---------------------------------------------------------------------------
def plug_boot():
    """Local frame: axis +Z = outboard; z=0 at the head's outboard face."""
    pb = C.PLUG_BOOT
    shaft = cyl_z(pb["shaft_d"] / 2, -pb["shaft_l"], FP["t"] + 0.01)
    body = cyl_z(pb["d"] / 2, FP["t"], FP["t"] + pb["l"])
    body = cq.Workplane().add(body).faces(">Z").edges().fillet(3.5).val()
    return safe_clean(shaft.fuse(body))


def print_boot(s):
    """Shaft end flat on the bed, dome up."""
    bb = s.BoundingBox()
    return s.translate(cq.Vector(0, 0, -bb.zmin))


# ---------------------------------------------------------------------------
# 33 Header primary pipe (one shape, x8): spigot - straight - bend - slanted drop - spigot
# ---------------------------------------------------------------------------
def primary_geometry():
    """S-curve centreline for bank A, cylinder at x=0, ENGINE frame:
    port -> straight stub (normal to the head face, 45 deg) -> bend out to the
    flare -> tuck-in run towards the collector -> short drop into the saddle."""
    p0 = _bank_pt(YO + C.EXH_PORT_DEPTH, PORT_Z)                     # start inside the port counterbore
    t1 = (_bank_pt(YO - 10.0, PORT_Z) - p0).normalized()             # outboard, 45 deg down (normal to the face)
    L1 = (-C.EXH_FLARE_Y - p0.y) / t1.y                              # straight until the flare line
    Q1 = p0 + t1 * L1
    jog = C.EXH_X_JOG
    Q2 = cq.Vector(jog * C.EXH_S_X_SHARE, -C.EXH_COLLECTOR_Y, C.EXH_S_Z)
    p3 = cq.Vector(jog, -C.EXH_COLLECTOR_Y, C.EXH_COLLECTOR_TOP_Z - C.EXH_COLLECTOR_SADDLE)
    t2 = (Q2 - Q1).normalized()
    t3 = (p3 - Q2).normalized()
    def turn(a, b):
        return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))
    tl1 = C.EXH_BEND_R * math.tan(math.radians(turn(t1, t2)) / 2)
    tl2 = C.EXH_BEND_R2 * math.tan(math.radians(turn(t2, t3)) / 2)
    return dict(points=[p0, Q1, Q2, p3], radii=[C.EXH_BEND_R, C.EXH_BEND_R2], t1=t1, t2=t2, t3=t3,
                stub=L1 - tl1, run=(Q2 - Q1).Length - tl1 - tl2, drop=(p3 - Q2).Length - tl2,
                turn1=turn(t1, t2), turn2=turn(t2, t3),
                # angles from the print vertical when standing on the collector spigot (t3 vertical)
                print_angles=dict(stub=turn(t1, t3), run=turn(t2, t3), drop=0.0),
                drop_slant_deg=math.degrees(math.atan2(math.hypot(t3.x, t3.y), -t3.z)),
                p0=p0, p3=p3)


def primary_pipe():
    g = primary_geometry()
    assert g["stub"] >= C.EXH_STUB_MIN, f"header stub too short: {g['stub']:.1f} mm"
    assert g["run"] > 2.0 and g["drop"] > 2.0, "header S-curve legs too short for the bend radii"
    path = _rounded_path(g["points"], g["radii"])
    prof = cq.Workplane(cq.Plane(origin=g["p0"].toTuple(), xDir=(1, 0, 0), normal=g["t1"].toTuple()))
    pipe = prof.circle(C.EXH_PRIMARY_D / 2).sweep(cq.Workplane().add(path), transition="round").val()
    sp_head = cq.Solid.makeCylinder(C.EXH_SPIGOT_D / 2, C.EXH_SPIGOT_L + 0.3, (g["p0"] + g["t1"] * 0.3).toTuple(),
                                    (g["t1"] * -1).toTuple())
    sp_col = cq.Solid.makeCylinder(C.EXH_SPIGOT_D / 2, C.EXH_SPIGOT_L + 0.3, (g["p3"] - g["t3"] * 0.3).toTuple(),
                                   g["t3"].toTuple())
    return safe_clean(pipe.fuse(sp_head).fuse(sp_col))


def _rotate_vec(shape, a, b):
    """Rotate `shape` by the rotation that takes direction a onto direction b."""
    a, b = cq.Vector(*a).normalized() if not isinstance(a, cq.Vector) else a.normalized(), \
        cq.Vector(*b).normalized() if not isinstance(b, cq.Vector) else b.normalized()
    axis = a.cross(b)
    if axis.Length < 1e-9:
        if a.dot(b) > 0:
            return shape
        perp = cq.Vector(1, 0, 0) if abs(a.x) < 0.9 else cq.Vector(0, 1, 0)
        return shape.rotate((0, 0, 0), a.cross(perp).toTuple(), 180)
    ang = math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))
    return shape.rotate((0, 0, 0), axis.toTuple(), ang)


def print_primary(s):
    """Stand the pipe on its collector spigot: the final drop is vertical, the
    tuck-in run and the stub lean (angles in primary_geometry()['print_angles'])."""
    g = primary_geometry()
    s = _rotate_vec(s, g["t3"], (0, 0, -1))         # pipe end direction -> straight down
    bb = s.BoundingBox()
    return s.translate(cq.Vector(0, 0, -bb.zmin))


# ---------------------------------------------------------------------------
# 34 Header flange plate: one bar over the four ports, holes for pipes and boots
# ---------------------------------------------------------------------------
def flange_plate():
    plate = box(X0 + FP["end_inset"], X1 - FP["end_inset"], YO - FP["t"], YO, DECK + FP["z0"], DECK + FP["z1"])
    plate = cq.Workplane().add(plate).edges("|Y").chamfer(2.0).val()
    for xc in CYL_X:
        plate = plate.cut(_ybore(C.EXH_PRIMARY_D / 2 + C.CLEARANCE, xc, PORT_Z, FP["t"]))
    for xb in BOOT_X:
        plate = plate.cut(_ybore(C.PLUG_BOOT["shaft_d"] / 2 + C.CLEARANCE, xb, BOOT_Z, FP["t"]))
    for xs in PLATE_SCREW_X:
        plate = plate.cut(_ybore(C.hole(C.M3_CLEAR) / 2, xs, PLATE_SCREW_Z, FP["t"]))
        plate = plate.cut(_ybore(C.hole(C.M3_CBORE) / 2, xs, PLATE_SCREW_Z, FP["t"] - C.SCREW_FLOOR + 1.0 + 1.0,
                                 from_outside=True))
    return safe_clean(plate)


def print_plate(s):
    return s.rotate((0, 0, 0), (1, 0, 0), -90)            # outboard face up, flat on the bed


# ---------------------------------------------------------------------------
# 35 Collector: straight log collector along X beside the pan, tail to the rear
# ---------------------------------------------------------------------------
def collector(bank):
    """ENGINE frame. Tapered log collector hanging from a horizontal top line
    (so all 4 saddle sockets are at one height and the primaries stay one
    shape), nose at the front, open tail to the rear inside the stand
    footprint. Flat on the inboard side so it prints lying down. Built for
    bank A's side (-y); bank B is the mirror."""
    g = primary_geometry()
    xs = C.BANK_A_CYL_X if bank == "A" else C.BANK_B_CYL_X
    yc, zt = -C.EXH_COLLECTOR_Y, C.EXH_COLLECTOR_TOP_Z
    r0, r1 = C.EXH_COLLECTOR_R
    x_front = max(xs) + C.EXH_X_JOG + C.EXH_COLLECTOR_FRONT_MARGIN
    x_rear = -C.STAND["l"] / 2 + C.EXH_TAIL_MARGIN
    assert x_rear < min(xs) + C.EXH_X_JOG - r1, "collector tail too short for the last socket"
    def ring(x, r):
        return cq.Wire.makeCircle(r, cq.Vector(x, yc, zt - r), cq.Vector(1, 0, 0))
    tube = cq.Solid.makeLoft([ring(x_rear, r1), ring(x_front, r0)], ruled=True)
    nose = cq.Solid.makeCone(r0, r0 - 4.0, 5.0, cq.Vector(x_front, yc, zt - r0), cq.Vector(1, 0, 0))
    tube = tube.fuse(nose)
    tube = cq.Workplane().add(tube).faces("<X").edges().chamfer(2.0).val()
    # inboard flat at 82 % of the local radius all along the taper (print bed face; hidden by the pan)
    k = C.EXH_COLLECTOR_FLAT
    flat = (cq.Workplane("XY").workplane(offset=zt - 2 * r1 - 1)
            .polyline([(x_rear - 1, yc + k * r1), (x_front + 6, yc + k * r0), (x_front + 6, yc + r1 + 1), (x_rear - 1, yc + r1 + 1)])
            .close().extrude(2 * r1 + 2).val())
    tube = tube.cut(flat)
    r_tail = r1 - C.EXH_TAIL_WALL
    assert r_tail < k * r1 - 0.3, "tail bore would break through the inboard flat"
    tube = tube.cut(cq.Solid.makeCylinder(r_tail, 30.0, cq.Vector(x_rear - 1, yc, zt - r1), cq.Vector(1, 0, 0)))
    sad = C.EXH_COLLECTOR_SADDLE
    for x in xs:
        mouth = cq.Vector(x + C.EXH_X_JOG, yc, zt - sad)                # = pipe end p3 for this cylinder
        cb = cyl_z(C.EXH_PRIMARY_D / 2 + C.CLEARANCE, -0.3, r1 + 2.0)       # saddle counterbore for the tube
        sock = crush_z(C.EXH_SPIGOT_D, -(C.EXH_SPIGOT_L + 0.5), 0.01, 0, 0, "trumpet_14", entry="hi")
        cut = _rotate_vec(cb.fuse(sock), (0, 0, -1), g["t3"]).translate(mouth)   # socket depth along the pipe end
        tube = tube.cut(cut)
    out = safe_clean(tube)
    return out if bank == "A" else out.mirror("XZ")


def print_collector(s):
    """Flat back down."""
    bb = s.BoundingBox()
    sgn = 1 if bb.ymin + bb.ymax > 0 else -1
    s = s.rotate((0, 0, 0), (1, 0, 0), -90 * sgn)          # inboard flat -> -Z
    bb = s.BoundingBox()
    return s.translate(cq.Vector(0, 0, -bb.zmin))


# ---------------------------------------------------------------------------
# 36 Intake manifold (provisional, ENGINE frame): tall single-plane plenum
#    filling the valley, 8 runner humps climbing its sides, throttle body, rails
# ---------------------------------------------------------------------------
def intake():
    it = C.INTAKE
    wires = [_rrect_wire(0, 0, l, w, it["r"], z) for z, w, l in it["sections"]]
    plenum = cq.Solid.makeLoft(wires, ruled=True)
    plenum = cq.Workplane().add(plenum).faces(">Z").edges().fillet(it["top_fillet"]).val()
    out = plenum
    rails = None
    for bank in ("A", "B"):
        sgn = -1 if bank == "A" else 1
        xs = C.BANK_A_CYL_X if bank == "A" else C.BANK_B_CYL_X
        up_in = _bank_pt(1.0, 0, bank) - _bank_pt(0, 0, bank)          # +y' of this bank in engine coords
        for xc, xl in zip(xs, C.BANK_A_CYL_X):
            pe = block.to_bank(cq.Vertex.makeVertex(xl, YV - it["port_depth"] + 0.5, DECK + it["port_z"]), bank)
            pe = cq.Vector(xc, pe.Y, pe.Z)                              # runner end, inside the head pocket
            plane = cq.Plane(origin=pe.toTuple(), xDir=(1, 0, 0), normal=up_in.toTuple())
            prof = cq.Workplane(plane).sketch().rect(it["runner_w"], it["runner_h"]).vertices().fillet(it["runner_r"]).finalize()
            runner = prof.extrude(it["stub_len"]).val()                 # hidden stub into the plenum body
            pts = [cq.Vector(xc, sgn * y, z) for y, z in it["ridge"]]
            path = _rounded_path(pts, [it["ridge_r"]] * (len(pts) - 2))
            d0 = (pts[1] - pts[0]).normalized()
            plane = cq.Plane(origin=pts[0].toTuple(), xDir=(1, 0, 0), normal=d0.toTuple())
            ridge = (cq.Workplane(plane).sketch().rect(it["runner_w"], it["runner_h"]).vertices()
                     .fillet(it["runner_r"]).finalize().sweep(cq.Workplane().add(path)).val())
            runner = runner.fuse(ridge)
            out = out.fuse(runner)
        # fuel rail with 4 injector bosses angled into the runners (printed with the manifold for now)
        rail = cyl_x(it["rail_d"] / 2, min(xs) - 12.0, max(xs) + 12.0, sgn * it["rail_y"], it["rail_z"])
        rail = cq.Workplane().add(rail).faces("<X or >X").edges().chamfer(1.5).val()
        for xc in xs:
            boss = cq.Solid.makeCylinder(it["inj_d"] / 2, 16.0, cq.Vector(xc, sgn * it["rail_y"], it["rail_z"]),
                                         cq.Vector(0, -sgn * 0.75, 0.66))
            rail = rail.fuse(boss)
        rails = rail if rails is None else rails.fuse(rail)
    out = out.fuse(rails)
    # throttle body on the front face, tilted up
    t = math.radians(it["tb_tilt"])
    d = cq.Vector(math.cos(t), 0, math.sin(t))
    base = cq.Vector(it["sections"][-1][2] / 2 - 6.0, 0, it["tb_z"])
    tb = cq.Solid.makeCylinder(it["tb_d"] / 2, it["tb_l"], base, d)
    tb = cq.Workplane().add(tb).faces(">X").edges().chamfer(2.0).val()
    tb = tb.cut(cq.Solid.makeCylinder(it["tb_bore"] / 2, 12.0, base + d * (it["tb_l"] - 11.9), d))
    blade = box(-1.0, 1.0, -it["tb_bore"] / 2, it["tb_bore"] / 2, -1.5, 1.5)
    blade = blade.rotate((0, 0, 0), (0, 1, 0), -it["tb_tilt"]).translate(base + d * (it["tb_l"] - 6.0))
    out = out.fuse(tb).fuse(blade)
    return safe_clean(out)


# ---------------------------------------------------------------------------
def build_all():
    return {"head": cylinder_head(), "valve_cover": valve_cover(), "boot": plug_boot(), "primary": primary_pipe(),
            "plate": flange_plate(), "collector_A": collector("A"), "collector_B": collector("B"),
            "intake": intake()}


def placed(lib, banks=("A", "B"), with_intake=True):
    """(name, shape, colour) in the engine frame."""
    out = []
    boot0 = lib["boot"].rotate((0, 0, 0), (1, 0, 0), 90)               # local +Z -> -y' (outboard)
    for bank in banks:
        tb = lambda s: block.to_bank(s, bank)
        out.append((f"head_{bank}", tb(lib["head"]), "block"))
        out.append((f"valve_cover_{bank}", tb(lib["valve_cover"]), "carbon"))
        out.append((f"header_plate_{bank}", tb(lib["plate"]), "steel"))
        xs = C.BANK_A_CYL_X if bank == "A" else C.BANK_B_CYL_X
        pipe = lib["primary"] if bank == "A" else lib["primary"].mirror("XZ")
        for i, xc in enumerate(xs):
            out.append((f"boot_{bank}{i+1}", tb(move(boot0, BOOT_X[i], YO, BOOT_Z)), "white"))
            out.append((f"header_{bank}{i+1}", move(pipe, xc), "steel"))
        out.append((f"collector_{bank}", lib[f"collector_{bank}"], "steel"))
    if with_intake:
        out.append(("intake", lib["intake"], "block"))
    return out
