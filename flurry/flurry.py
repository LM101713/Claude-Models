#!/usr/bin/env python3
"""Odd Layer FL-05 FLURRY: print-in-place gyro snowflake ornaments.

Three nested bodies printed flat in one go: an outer ring with a hanging eyelet, a middle
gimbal ring and a snowflake core. Each inner body rides on two 45-degree cone pivots that
print inside matching cone sockets with a fixed clearance, so the ornament comes off the
bed already assembled and both stages spin freely. No supports, no hardware.

    python flurry.py            # build all six flakes, validate, export to models/

Requires: manifold3d, shapely, numpy.
"""

import json
import math
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------- parameters
T = 7.0            # thickness of every body (Z as printed)
CHAMFER = 0.6      # 45-degree edge break on all ring edges (also absorbs elephant foot)
GAP = 0.7          # radial air gap between neighbouring bodies
R_CORE = 24.0      # outer radius of the snowflake core rim
RIM_W = 3.0        # radial width of the core rim
RING_W = 5.0       # radial width of the middle and outer rings
PIN_TIP = 0.3      # flat radius on the tip of each cone pivot
PIN_PEN = 1.6      # how far a pivot reaches into its socket
PIN_EMBED = 0.6    # how far a pivot is buried in its own body
SOCKET_SHIFT = 0.5 # socket apex pushed outward by this much -> 0.35 mm normal clearance
EYE_R, EYE_HOLE = 4.4, 2.1
SEG = 180

R_MID_IN = R_CORE + GAP
R_MID_OUT = R_MID_IN + RING_W
R_OUT_IN = R_MID_OUT + GAP
R_OUT_OUT = R_OUT_IN + RING_W
R_FLAKE = R_CORE - RIM_W          # snowflake lives inside this radius

COLORS = {"outer": "#C9202B", "middle": "#E8E8EA", "core": "#F5F7FA"}


# ----------------------------------------------------------------------------- solids
def ring(r_in, r_out):
    c = CHAMFER
    prof = [(r_in + c, 0), (r_out - c, 0), (r_out, c), (r_out, T - c),
            (r_out - c, T), (r_in + c, T), (r_in, T - c), (r_in, c)]
    return CrossSection([prof]).revolve(SEG).rotate([0, 0, 0])


def cone_x(x0, x1, r1):
    """45-degree cone along +X from x0 to x1, radius r1 at x1, growing toward x0."""
    h = x1 - x0
    c = Manifold.cylinder(h, r1 + h, r1, 64)          # along +Z, wide end at z=0
    return c.rotate([0, 90, 0]).translate([x0, 0, T / 2])


def pivots(r_face, axis_deg):
    """(pins, sockets) for a body whose outer face is at r_face; pair on +/- axis."""
    tip = r_face + GAP + PIN_PEN
    pin = cone_x(r_face - PIN_EMBED, tip, PIN_TIP)
    sock = cone_x(r_face + GAP - 0.6, tip + SOCKET_SHIFT, PIN_TIP)
    pins = pin.rotate([0, 0, axis_deg]) + pin.rotate([0, 0, axis_deg + 180])
    socks = sock.rotate([0, 0, axis_deg]) + sock.rotate([0, 0, axis_deg + 180])
    return pins, socks


def to_cs(geom):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    contours = []
    for p in polys:
        p = orient(p, 1.0)
        contours.append(list(p.exterior.coords)[:-1])
        contours += [list(i.coords)[:-1] for i in p.interiors]
    return CrossSection(contours)


# ----------------------------------------------------------------------------- snowflakes
def bar(length, width, start=0.0):
    return box(start, -width / 2, length, width / 2)


def hexagon(r, rot=0.0):
    return Polygon([(r * math.cos(math.radians(rot + 60 * k)), r * math.sin(math.radians(rot + 60 * k)))
                    for k in range(6)])


def hex_ring(r, w, rot=0.0):
    return hexagon(r + w / 2, rot).difference(hexagon(r - w / 2, rot))


def six(shape, rot=0.0):
    return unary_union([affinity.rotate(shape, rot + 60 * k, origin=(0, 0)) for k in range(6)])


def branches(spec, width):
    """spec: [(distance along arm, length)], a V of two 60-degree barbs at each station."""
    out = []
    for d, l in spec:
        b = bar(l, width)
        for s in (60, -60):
            out.append(affinity.translate(affinity.rotate(b, s, origin=(0, 0)), d, 0))
    return unary_union(out)


def flake(name):
    R = R_FLAKE + 0.8                       # arms run into the rim
    arm = bar(R, 2.4)
    if name == "classic":
        g = six(unary_union([arm, branches([(9.5, 6.5), (15.0, 4.5)], 1.8)]))
        g = g.union(hexagon(4.2))
    elif name == "fern":
        g = six(unary_union([bar(R, 2.0), branches([(5.5, 6.0), (9.5, 6.0), (13.5, 4.6), (17.0, 3.0)], 1.5)]))
        g = g.union(hexagon(3.0))
    elif name == "stellar":
        g = six(unary_union([arm, branches([(16.0, 4.6)], 1.8)]))
        g = g.union(hex_ring(9.5, 2.0)).union(hexagon(3.4))
    elif name == "plate":
        short = unary_union([bar(13.0, 2.0), branches([(8.5, 4.0)], 1.6)])
        g = six(unary_union([arm, branches([(15.5, 4.2)], 1.8)])).union(six(short, 30))
        g = g.union(hexagon(7.0)).difference(hexagon(3.6, 30))
    elif name == "star":
        diamond = affinity.translate(affinity.scale(hexagon(2.6), 1.5, 0.9), 13.5, 0)
        short = unary_union([bar(13.5, 2.0), diamond])
        g = six(unary_union([arm, branches([(12.0, 5.0)], 1.8)])).union(six(short, 30))
        g = g.union(Point(0, 0).buffer(4.0, 32))
    elif name == "crystal":
        g = six(unary_union([arm, branches([(18.2, 3.0)], 1.6)]))
        g = g.union(hex_ring(6.0, 1.8)).union(hex_ring(13.5, 2.0))
    else:
        raise ValueError(name)
    return g.intersection(Point(0, 0).buffer(R, 96)).buffer(0)


FLAKES = ["classic", "fern", "stellar", "plate", "star", "crystal"]


# ----------------------------------------------------------------------------- assembly
def build(name):
    """Returns dict of the three bodies in the as-printed pose (flat, Z = 0..T)."""
    core_pins, mid_socks = pivots(R_CORE, 0)        # core spins about X inside the middle ring
    mid_pins, out_socks = pivots(R_MID_OUT, 90)     # middle spins about Y (the hanging axis)

    core = ring(R_FLAKE, R_CORE) + to_cs(flake(name)).extrude(T) + core_pins
    middle = ring(R_MID_IN, R_MID_OUT) - mid_socks + mid_pins

    eye = Point(0, R_OUT_OUT + EYE_R - 2.2).buffer(EYE_R, 48)
    eye_hole = Point(0, R_OUT_OUT + EYE_R - 2.2).buffer(EYE_HOLE, 32)
    tab = eye.difference(Point(0, 0).buffer(R_OUT_OUT - 1.0, 180)).difference(eye_hole)
    outer = ring(R_OUT_IN, R_OUT_OUT) + (to_cs(tab).extrude(T) - to_cs(eye_hole).extrude(T)) - out_socks
    return {"outer": outer, "middle": middle, "core": core}


# ----------------------------------------------------------------------------- validation
def rot_about(m, axis, deg):
    r = [deg, 0, 0] if axis == "x" else [0, deg, 0]
    return m.translate([0, 0, -T / 2]).rotate(r).translate([0, 0, T / 2])


def overhang_worst(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1)
    keep = (area > 1e-9) & (np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]) > 0.05)
    nz = n[keep, 2] / area[keep]
    # angle of the surface from horizontal for down-facing faces; 90 = vertical wall
    down = nz < -1e-6
    if not down.any():
        return 90.0
    return float(np.degrees(np.arccos(-nz[down])).min())


def validate(name, b):
    checks = []

    def ok(label, cond, detail=""):
        checks.append({"check": label, "pass": bool(cond), "detail": detail})

    for k, m in b.items():
        ok(f"{k}: one closed solid", len(m.decompose()) == 1 and m.volume() > 0,
           f"{m.volume() / 1000:.2f} cm3")
        lo, hi = m.bounding_box()[2], m.bounding_box()[5]
        ok(f"{k}: sits on the bed", abs(lo) < 1e-6 and abs(hi - T) < 1e-6, f"z {lo:.2f}..{hi:.2f}")
        oh = overhang_worst(m)
        ok(f"{k}: no overhang steeper than 45 deg", oh >= 44.5, f"worst {oh:.1f} deg from horizontal")

    pairs = [("core", "middle"), ("middle", "outer"), ("core", "outer")]
    for p, q in pairs:
        ok(f"{p}/{q}: no fusion as printed", (b[p] ^ b[q]).volume() < 1e-9)
    for p, q in pairs[:2]:
        gap = b[p].min_gap(b[q], 3.0)
        ok(f"{p}/{q}: printed clearance >= 0.30 mm", gap >= 0.30, f"{gap:.3f} mm")

    # full rotation of each stage
    worst = 0.0
    for d in range(0, 360, 10):
        worst = max(worst, (rot_about(b["core"], "x", d) ^ b["middle"]).volume())
    ok("core spins 360 deg inside middle ring", worst < 1e-9, f"max overlap {worst:.4f} mm3")
    inner = b["core"] + b["middle"]
    worst = 0.0
    for d in range(0, 360, 10):
        worst = max(worst, (rot_about(inner, "y", d) ^ b["outer"]).volume())
    ok("middle ring spins 360 deg inside outer ring", worst < 1e-9, f"max overlap {worst:.4f} mm3")
    worst = 0.0
    for d1 in range(0, 360, 30):
        for d2 in range(0, 360, 30):
            pose = rot_about(rot_about(b["core"], "x", d1), "y", d2)
            worst = max(worst, (pose ^ b["outer"]).volume())
    ok("core never touches outer ring (144 poses)", worst < 1e-9, f"max overlap {worst:.4f} mm3")

    # captivity: a 1 mm shove in any direction must be blocked by the pivots
    for p, q in pairs[:2]:
        blocked = all((b[p].translate(list(v)) ^ b[q]).volume() > 0
                      for v in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)])
        ok(f"{p} is captive in {q}", blocked)
    return checks


# ----------------------------------------------------------------------------- export
def arrays(m):
    mesh = m.to_mesh()
    return (np.asarray(mesh.vert_properties)[:, :3].astype(np.float64),
            np.asarray(mesh.tri_verts).astype(np.int64))


def write_stl(path, m):
    v, t = arrays(m)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-20
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(b"Odd Layer FL-05 FLURRY".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())


def write_3mf(path, ornaments, title):
    """ornaments: [(name, bodies dict, (x, y))]. One object per ornament with three parts,
    so each part can be given its own filament in the slicer."""
    res, items, oid = [], [], 0
    for name, bodies, (px, py) in ornaments:
        comps = []
        for part in ("outer", "middle", "core"):
            oid += 1
            v, t = arrays(bodies[part])
            vs = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
            res.append(f'<object id="{oid}" name="{name} {part}" type="model"><mesh><vertices>{vs}</vertices>'
                       f"<triangles>{ts}</triangles></mesh></object>")
            comps.append(f'<component objectid="{oid}"/>')
        oid += 1
        res.append(f'<object id="{oid}" name="FLURRY {name}" type="model"><components>{"".join(comps)}</components></object>')
        items.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {px:.3f} {py:.3f} 0"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata><metadata name="Designer">Odd Layer</metadata>'
             f"<resources>{''.join(res)}</resources><build>{''.join(items)}</build></model>")
    ct = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def scene_json(path, placed):
    """placed: [(manifold, colour)] -> compact JSON for the three.js render studio."""
    out = []
    for m, col in placed:
        v, t = arrays(m)
        out.append({"color": col, "v": np.round(v, 3).ravel().tolist(), "t": t.ravel().tolist()})
    Path(path).write_text(json.dumps(out))


def main():
    models = HERE / "models"
    (models / "stl").mkdir(parents=True, exist_ok=True)
    (models / "3mf").mkdir(parents=True, exist_ok=True)
    scenes = HERE / "render" / "scenes"
    scenes.mkdir(parents=True, exist_ok=True)

    report, built, failed = {}, {}, 0
    for name in FLAKES:
        b = build(name)
        built[name] = b
        checks = validate(name, b)
        report[name] = checks
        bad = [c for c in checks if not c["pass"]]
        failed += len(bad)
        vol = sum(m.volume() for m in b.values()) / 1000
        print(f"{name:8s} {len(checks) - len(bad)}/{len(checks)} checks  {vol:.1f} cm3")
        for c in bad:
            print("   FAIL", c["check"], c["detail"])
        write_stl(models / "stl" / f"FL05_Flurry_{name}.stl", b["outer"] + b["middle"] + b["core"])
        write_3mf(models / "3mf" / f"FL05_Flurry_{name}.3mf", [(name, b, (128, 128))], f"FL-05 FLURRY {name}")

    pitch_x, pitch_y = 76.0, 84.0
    grid = [(128 + (i % 3 - 1) * pitch_x, 124 + (0.5 - i // 3) * pitch_y) for i in range(6)]
    write_3mf(models / "3mf" / "FL05_Flurry_full_set_of_6.3mf",
              [(n, built[n], grid[i]) for i, n in enumerate(FLAKES)], "FL-05 FLURRY full set")

    size = (2 * R_OUT_OUT, R_OUT_OUT * 2 + 2 * EYE_R - 2.2, T)
    (models / "FL05_validation.json").write_text(json.dumps(
        {"size_mm": size, "clearance_mm": SOCKET_SHIFT * math.sin(math.radians(45)), "gap_mm": GAP,
         "checks": report}, indent=1))

    # render scenes
    C = COLORS
    def posed(b, a_core, a_mid, cols=C):
        inner = rot_about(b["core"], "x", a_core)
        return [(b["outer"], cols["outer"]), (rot_about(b["middle"], "y", a_mid), cols["middle"]),
                (rot_about(inner, "y", a_mid), cols["core"])]
    scene_json(scenes / "hero.json", posed(built["classic"], 28, 38, {"outer": "#C9202B", "middle": "#D9B45A", "core": "#F5F7FA"}))
    scene_json(scenes / "flat.json", posed(built["classic"], 0, 0))
    palettes = [("#C9202B", "#E8E8EA", "#F5F7FA"), ("#1F6B3A", "#D9B45A", "#F5F7FA"), ("#2B5EA8", "#E8E8EA", "#BFE3F5"),
                ("#D9B45A", "#C9202B", "#F5F7FA"), ("#F5F7FA", "#7FC8E8", "#2B5EA8"), ("#3A3D45", "#D9B45A", "#F5F7FA")]
    allsix = []
    for i, n in enumerate(FLAKES):
        cols = dict(zip(("outer", "middle", "core"), palettes[i]))
        x, y = (i % 3 - 1) * 84.0, (0.5 - i // 3) * 92.0
        allsix += [(m.translate([x, y, 0]), c) for m, c in posed(built[n], 0, 0, cols)]
    scene_json(scenes / "set.json", allsix)
    spin = []
    for i, n in enumerate(FLAKES):
        cols = dict(zip(("outer", "middle", "core"), palettes[i]))
        x, y = (i % 3 - 1) * 84.0, (0.5 - i // 3) * 92.0
        spin += [(m.translate([x, y, 0]), c) for m, c in posed(built[n], 25 + 23 * i, 20 + 17 * i, cols)]
    scene_json(scenes / "set_spin.json", spin)
    # section through the pivot axis (X) to show the cone-in-socket print-in-place joint
    cut = Manifold.cube([200, 200, 50]).translate([-100, -200, -10])
    b = built["classic"]
    scene_json(scenes / "section.json", [(b[k] - cut, C[k] if k != "core" else "#7FC8E8") for k in b])

    print("size %.1f x %.1f x %.1f mm" % size)
    print("FAILED" if failed else "ALL CHECKS PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
