"""Cup Lite: the Cup production concept (tools/cup_concept.py) merged into six large shells for fast
printing and a one-hour assembly (Liam, 2026-10-22: "Ok yes please" to the simplification proposal).

Same outside shapes as the Cup concept; what changes is how it is split and joined:

  L1 block + pan       orange (or black), one shell, open bottom, sits on the bought base plate
  L2 top end           both heads + both valve covers + intake, one silver shell (glued to L1)
  L3 air cleaner       base + lid in one black piece, presses onto a spigot on the throttle body
  L4 / L5 headers      right and left, printed pins press into the head port pads
  L6 front drive       timing cover + water pump + dry-sump pump + alternator, one silver piece
  K  small-parts plate distributor, 4 pulleys, flywheel (black) + 8 boots (clear), per engine

No screws or inserts in the shells except four M3 inserts in the pan for the base-plate screws.
Motion: two N20 gear motors in printed sleeves inside the block, one driving the crank pulley (the
belt turns the three idlers on steel pins), one driving the flywheel. LEDs: a 4-pixel chain glued
inside each head shines through the plug bosses into the clear boots.

    python tools/cup_lite.py --export                     (bpyenv)
    python tools/cup_lite.py --photo --views front_right,rear_left,above,side,front,closeup

STLs go to cup_lite/stl/, renders to renders/cup_lite/.
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import cup_concept as CC  # noqa: E402
from skin import bpyutil as U  # noqa: E402
from skin import studio as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_STL = os.path.join(ROOT, "cup_lite", "stl")
OUT_REN = os.path.join(ROOT, "renders", "cup_lite")
C = CC.C
S45 = CC.S45
BX = C["block_x"]
PIN_R, PIN_HOLE_R = 1.5, 1.7        # printed locating pins and their holes (0.2 mm per side clearance)
DOWEL_R = 1.45                     # 3 mm steel dowel, press fit in the front drive
N20 = (12.3, 10.3)                 # N20 gear motor section + 0.3 mm clearance
PLATE_Z = (C["pan_z"] - 6.0, C["pan_z"])
WALL = 1.8                         # two 0.85 mm lines: thinner shells are most of the time saved
C["wall"] = WALL
CC.SHELL_WALL = WALL
CC.PAN_WALL = WALL


# ---------------------------------------------------------------- L1 block + pan
def build_l1():
    blk = CC.build_block()
    pan = CC.build_pan()
    U.union([blk, pan])
    # open the pan floor: the motors, board and wires come up from the base plate
    w = WALL
    U.boolean(blk, U.rrect_prism("pan_open", 0, 0, 2 * BX - 10 - 2 * w - 0.2, 2 * C["side_y"] - 12 - 2 * w - 0.2, 9.5,
                                  C["pan_z"] - 2, C["rail_z"] + 2))
    # four insert bosses on the pan walls for the base-plate screws (M3 heat-set, 4.0 mm hole)
    iy = C["side_y"] - 6 - w - 1.0 - 2.0
    for x in (-70.0, 70.0):
        for s in (1, -1):
            U.union([blk, U.cylinder("ins_boss", 5.0, C["pan_z"], C["pan_z"] + 10.0, x, s * iy, segs=48)])
            U.boolean(blk, U.cylinder("base_ins", 2.0, C["pan_z"] - 1, C["pan_z"] + 7.0, x, s * iy, segs=32))
    # N20 sleeves front and rear, on 45 deg gussets so they print without support. The front motor's
    # gearbox face sits on the inside of the front wall; the rear one goes through the rear wall into the
    # flywheel boss so its short shaft reaches the flywheel hub.
    for sx in (1, -1):
        wall_in = sx * (BX - C["wall"])
        inner = wall_in - sx * 30.0
        x0, x1 = sorted((wall_in, inner))
        sl = U.box("n20_sleeve", x0, x1, -8.2, 8.2, -7.2, 7.2)
        g = _xz_prism("n20_gusset", [(wall_in, -7.0), (wall_in, -31.0), (wall_in - sx * 24.0, -7.0)], -8.2, 8.2)
        U.union([blk, sl, g])
        face = wall_in if sx > 0 else -BX - 1.0
        b0, b1 = sorted((inner - sx * 1.0, face))
        U.boolean(blk, U.box("n20_bore", b0, b1, -N20[0] / 2, N20[0] / 2, -N20[1] / 2, N20[1] / 2))
    U.boolean(blk, U.cylinder("n20_shaft_clear", 2.6, -BX - 10, BX + 5, 0, 0, axis="X", segs=32))
    # locating tabs on each deck (fit inside the head shell walls) and an LED wire pass
    for s in (1, -1):
        cut = [U.cylinder("led_pass", 4.0, C["deck"] - 6, C["deck"] + 6, -40.0, 0.0, segs=32)]
        add = [U.box("deck_tab", xc - 10, xc + 10, -(C["head_half"] - WALL - 0.25), C["head_half"] - WALL - 0.25, C["deck"] - 0.5, C["deck"] + 3.5) for xc in (-75.0, 75.0)]
        for o in add + cut:
            CC.to_bank_A(o)
        if s < 0:
            for lst in (add, cut):
                for k, o in enumerate(lst):
                    lst[k] = U.mirror_y(o, o.name + "_B")
                    U.delete(o)
        for o in add + cut:
            U.move(o, dx=s * C["bank_off"])
        U.union([blk] + add)
        for o in cut:
            U.boolean(blk, o)
    # two pin holes in the front wall for the front drive
    for y in (-28.0, 28.0):
        U.boolean(blk, U.cylinder("fd_pin_hole", PIN_HOLE_R, BX - 4, BX + 1, y, -18.0, axis="X", segs=24))
    return blk


def _xz_prism(name, pts_xz, y0, y1):
    """Prism of an (x, z) outline extruded along Y."""
    o = U.prism(name, pts_xz, y0, y1)        # outline in (y, z), extruded along X ...
    return U.transform(o, Matrix.Rotation(math.radians(-90.0), 4, 'Z'))   # ... turned: outline on X, extrusion on -Y


# ---------------------------------------------------------------- L2 top end
def intake_outline_lite():
    """cup_concept.intake_outline with the head gap closed (the intake fuses to the heads) and the
    block gap kept (L2 must clear L1)."""
    k = 2 * S45
    gap_b, gap_h = 0.4, -0.4
    blk_line = k * C["deck_half"] + gap_b
    head_line = k * C["head_half"] + gap_h
    deck_sum = 2 * S45 * C["deck"] + gap_b
    p0 = (C["valley_z"] - blk_line + 0.3, C["valley_z"] + 0.3)
    y1 = (deck_sum - blk_line) / 2
    y2 = (deck_sum - head_line) / 2
    right = [p0, (y1, y1 + blk_line), (y2, y2 + head_line), (64.0, 64.0 + head_line), (54.0, 126.0),
             (42.0, CC.PLENUM_Z[0])]
    return right + [(-y, z) for y, z in reversed(right)]


def head_lite():
    h = CC.build_head()
    d, hh = C["deck"], C["head_half"]
    pdir = Vector((0, 0.94, -0.34))
    for i in range(4):   # light path: plug sockets run through into the hollow head
        o = Vector(((1.5 - i) * C["pitch"] + 14.0, hh - 1.0, d + 11.0)) + pdir * 4.2
        U.boolean(h, CC.cyl_dir("led_light", 1.8, 0.0, 9.0, o, -pdir, segs=24))
    return h


def port_frame(bank, i, dx):
    """Engine-frame port centre and outward normal for header pin i on `bank` (dx along x)."""
    s = 1 if bank == "A" else -1
    p = CC.bank_pt(s, CC.cyl_x(bank, i) - 4.0 + dx, C["head_half"] + 1.2, C["deck"] + C["port_u"])
    return p, Vector((0, s * S45, -S45))


def build_l2():
    old = CC.intake_outline
    CC.intake_outline = intake_outline_lite
    intake = CC.build_intake()
    CC.intake_outline = old
    h = head_lite()
    for x, v in COVER_PINS:         # valve-cover pin holes in the head roof
        U.boolean(h, U.cylinder("cv_pin_hole", PIN_HOLE_R, CC.HEAD_TOP - 4.0, CC.HEAD_TOP + 1.0, x, v, segs=24))
    ha, hb = CC.both_banks(h, "head")
    if ALL_SILVER:
        cv = build_cover_lite()
        U.move(cv, dz=-0.4)        # flange sinks 0.4 mm into the head top so the union fuses
        ca, cb = CC.both_banks(cv, "cover")
        top = U.union([intake, ha, hb, ca, cb], "top_end")
    else:
        top = U.union([intake, ha, hb], "top_end")
    # air-cleaner spigot on the throttle body
    U.union([top, U.cylinder("ac_spigot", 10.0, CC.TB_TOP - 0.3, CC.TB_TOP + 5.0, 6.0, 0.0, segs=64)])
    # header pin holes in the port pads
    for bank in ("A", "B"):
        for i in range(4):
            for dx in (-7.0, 7.0):
                p, n = port_frame(bank, i, dx)
                U.boolean(top, CC.cyl_dir("hdr_pin_hole", PIN_HOLE_R, -4.5, 0.5, p, n, segs=24))
    return top


COVER_PINS = ((-60.0, 26.0), (60.0, 26.0))     # (x, v) on one flange rim: the same STL fits bank B turned 180 deg
ALL_SILVER = False     # --all-silver: covers fused into the top end (one fewer glue step, loses the black covers)


def build_cover_lite():
    cv = CC.build_cover()
    if not ALL_SILVER:
        for x, v in COVER_PINS:
            U.union([cv, U.cylinder("cv_pin", PIN_R, CC.HEAD_TOP - 3.0, CC.HEAD_TOP + 0.5, x, v, segs=24)])
    return cv


# ---------------------------------------------------------------- L3 air cleaner (+ silver lid trim)
def build_l3():
    base, lid = CC.build_air_cleaner()
    z0 = CC.TB_TOP
    U.boolean(base, U.cylinder("ac_pocket", 10.2, z0 - 1, z0 + 5.4, 6.0, 0.0, segs=64))
    # lid locating ring on top of the element, into a groove under the lid (press fit)
    ring = U.cylinder("lid_ring", 57.5, z0 + 26.7, z0 + 29.0, 6.0, 0.0, segs=128)
    U.boolean(ring, U.cylinder("lid_ring_in", 55.3, z0 + 26, z0 + 30, 6.0, 0.0, segs=128))
    U.union([base, ring])
    groove = U.cylinder("lid_groove", 57.8, z0 + 26.5, z0 + 29.3, 6.0, 0.0, segs=128)
    U.boolean(groove, U.cylinder("lid_groove_in", 55.0, z0 + 26, z0 + 30, 6.0, 0.0, segs=128))
    U.boolean(lid, groove)
    return base, lid


# ---------------------------------------------------------------- L4 / L5 headers
def build_headers():
    a = CC.build_header()
    for i in range(4):
        for dx in (-7.0, 7.0):
            p, n = port_frame("A", i, dx)
            U.union([a, CC.cyl_dir("hdr_pin", PIN_R, -3.9, 0.5, p, n, segs=24)])
    b = U.mirror_y(a, "header_B")
    U.move(b, dx=-2 * C["bank_off"])   # bank B sits behind bank A (cup_concept left this shift out)
    return a, b


# ---------------------------------------------------------------- L6 front drive
def build_l6():
    fc = CC.build_front_cover()
    alt = CC.build_alternator()
    U.move(alt, dx=-0.4)
    U.union([fc, alt], "front_drive")
    ay, az, _ = CC.ALT        # bracket from the alternator into the water-pump plate (it was a separate part)
    U.union([fc, U.box("alt_bracket", BX + 2.0, BX + 10.0, ay + 8.0, -18.0, az - 4.0, az + 4.0)])
    for y, z, _ in (CC.WPUMP, CC.DSUMP, CC.ALT):    # 3 mm dowel holes for the idlers
        U.boolean(fc, U.cylinder("dowel_hole", DOWEL_R, C["belt_x"][0] - 10.0, C["belt_x"][0], y, z, axis="X", segs=32))
    for y in (-28.0, 28.0):
        U.union([fc, U.cylinder("fd_pin", PIN_R, BX - 2.4, BX + 0.5, y, -18.0, axis="X", segs=24)])
    U.boolean(fc, U.cylinder("hub_clear", 4.6, BX - 1, BX + 30, 0, 0, axis="X", segs=48))
    return fc


# ---------------------------------------------------------------- K: small parts
def build_kit():
    out = []
    cp = CC.place_pulley(CC.build_crank_pulley(), CC.CRANK[0], CC.CRANK[1])
    U.union([cp, U.cylinder("cp_hub", 4.0, BX + 1.0, BX + 11.0, 0, 0, axis="X", segs=48)])
    U.boolean(cp, _d_bore("cp_bore", BX + 0.5, BX + 9.0, 1))
    out.append(("crank_pulley", cp, "k01_crank_pulley", 1))
    for nm, (y, z, r), stl in (("pulley_wp", CC.WPUMP, "k02_pulley_water"), ("pulley_ds", CC.DSUMP, "k03_pulley_pump"),
                               ("pulley_alt", CC.ALT, "k04_pulley_alt")):
        p = CC.place_pulley(CC.build_pulley(nm, r), y, z)
        U.boolean(p, U.cylinder(nm + "_bore", 1.65, C["belt_x"][0] - 1, C["belt_x"][1] + 6, y, z, axis="X", segs=32))
        out.append((nm, p, stl, 1))
    fw = CC.build_flywheel()
    U.boolean(fw, _d_bore("fw_bore", -BX - 13.0, -BX - 3.0, -1))
    out.append(("flywheel", fw, "k05_flywheel", 1))
    d = CC.build_distributor()
    out.append(("distributor", d, "k06_distributor", 1))
    return out


def _d_bore(name, x0, x1, sx):
    """3 mm D-shaft bore along X (flat at y = +1.0)."""
    b = U.cylinder(name, 1.6, x0, x1, 0, 0, axis="X", segs=32)
    U.boolean(b, U.box(name + "_flat", x0 - 1, x1 + 1, 1.05, 3, -3, 3))
    return b


# ---------------------------------------------------------------- base plate (bought) + assembly
def build_plate():
    pl = U.rrect_prism("plate", 0, 0, 300.0, 230.0, 12.0, PLATE_Z[0], PLATE_Z[1] - 0.01)
    U.bevel(pl, 1.0, segments=3, angle_deg=40)
    return pl


def build_all():
    U.reset_scene()
    t = time.time()
    placed = []

    def add(name, obj, stl=None, qty=1):
        obj.name = name
        placed.append((name, obj, stl, qty))
        print(f"  {name:22s} {time.time()-t:6.1f}s", flush=True)

    blk, top = build_l1(), build_l2()
    # distributor drops in from above: clear its clamp and body, not just the shaft
    U.boolean(top, U.cylinder("dist_body_clear", 15.5, CC.DIST_Z[1] - 32.0, CC.DIST_Z[1] + 20, CC.DIST.x, CC.DIST.y, segs=64))
    U.boolean(top, U.cylinder("dist_cap_clear", 20.5, CC.DIST_Z[1] - 13.0, CC.DIST_Z[1] + 20, CC.DIST.x, CC.DIST.y, segs=64))
    add("block", blk, "l1_block_pan")
    add("top_end", top, "l2_top_end")
    base, lid = build_l3()
    add("air_cleaner", base, "l3_air_cleaner")
    add("air_lid", lid, "t02_air_cleaner_lid")
    if not ALL_SILVER:
        a, b = CC.both_banks(build_cover_lite(), "valve_cover")
        add("valve_cover_A", a, "t01_valve_cover", 2)
        add("valve_cover_B", b)
    a, b = build_headers()
    fd = build_l6()
    for o in (a, b):              # primaries started 1 mm inside the port pads: trim them to the head face
        U.boolean(o, U.copy(top))
    U.boolean(fd, U.copy(blk))    # front cover clears the pan-rail lip
    add("header_A", a, "l4_header_right")
    add("header_B", b, "l5_header_left")
    add("front_drive", fd, "l6_front_drive")
    for name, o, stl, q in build_kit():
        add(name, o, stl, q)
    add("plate", build_plate())
    add("belt", CC.build_belt())
    for o in CC.build_wires():
        add(o.name, o, "k07_plug_boot" if o.name == "boot_A0" else None, 8 if o.name == "boot_A0" else 1)
    for o in CC.build_oil_lines():
        add(o.name, o)
    return placed


def export(placed):
    os.makedirs(OUT_STL, exist_ok=True)
    rows = []
    for name, obj, stl, qty in placed:
        if not stl:
            continue
        for tol in (1e-4, 1e-3, 3e-3):
            o = U.copy(obj, name + "_exp")
            ok, msg = U.finalize(o, tol=tol)
            if ok or tol == 3e-3:
                break
            U.delete(o)
        path = os.path.join(OUT_STL, stl + ".stl")
        U.export_stl(o, path, do_finalize=False)
        bb = U.bbox(o)
        rows.append(dict(file=stl, qty=qty, path=os.path.relpath(path, ROOT), ok=ok, msg=msg,
                         size=[round(bb[1] - bb[0], 1), round(bb[3] - bb[2], 1), round(bb[5] - bb[4], 1)]))
        print(("OK  " if ok else "BAD ") + msg, rows[-1]["size"], flush=True)
        U.delete(o)
    json.dump(dict(parts=rows), open(os.path.join(ROOT, "cup_lite", "parts.json"), "w"), indent=1)
    return rows


# ---------------------------------------------------------------- look
def materials(palette):
    import skin_photo as P
    block_col = {"orange": (0.62, 0.13, 0.015), "black": (0.06, 0.065, 0.07)}[palette]
    paint = P._mat("block_print_" + palette, block_col, 0.0, 0.38, grain=(1.4, 0.18, 0.25), coat=0.3)
    rubber = P._mat("rubber", (0.015, 0.015, 0.016), 0.0, 0.7, bevel=0.0)
    wire = P._mat("wire", (0.02, 0.02, 0.022), 0.0, 0.45, bevel=0.0, coat=0.3)
    hose = P._mat("hose", (0.03, 0.03, 0.035), 0.4, 0.5, grain=(6.0, 0.6, 0.15), bevel=0.0)
    table = [
        ("block", lambda: paint), ("top_end", P.cast_alu), ("air_cleaner", P.wrinkle_black),
        ("air_lid", P.machined_alu), ("valve_cover", P.wrinkle_black),
        ("distributor", P.wrinkle_black), ("header", P.stainless_heat), ("front_drive", P.cast_alu),
        ("crank_pulley", P.anodised_black), ("pulley", P.anodised_black), ("flywheel", P.dark_steel),
        ("plate", P.powder_black), ("belt", lambda: rubber), ("wire_tb", lambda: rubber), ("wire", lambda: wire),
        ("boot", P.boot_glow), ("oil_line", lambda: hose), ("oil_fit", P.anodised_black),
    ]

    def pick(name):
        for pre, fn in table:
            if name.startswith(pre):
                return fn()
        return P.cast_alu()
    return pick


def layer_normal(name):
    """Build direction of each printed part as it sits on the bed (for --layers)."""
    if name.startswith(("valve_cover", "header")):
        s = 1 if name.endswith("_A") else -1
        if name.startswith("header"):
            s = -s
        return (0.0, s * S45, S45)
    if name.startswith("front_drive"):
        return (-1.0, 0.0, 0.0)
    if name.startswith(("crank_pulley", "pulley", "flywheel")):
        return (1.0, 0.0, 0.0)
    if name.startswith(("block", "top_end", "air_", "distributor", "boot")):
        return (0.0, 0.0, 1.0)
    return None


_LAYER_MATS = {}


def with_layers(mat, nrm, pitch=0.40):
    """Copy of `mat` with print layer lines (sine bump, `pitch` mm) across direction nrm."""
    key = (mat.name, nrm)
    if key in _LAYER_MATS:
        return _LAYER_MATS[key]
    m = mat.copy()
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    prev = b.inputs["Normal"].links[0].from_socket if b.inputs["Normal"].links else None
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = nrm
    nt.links.new(geo.outputs["Position"], dot.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 2 * math.pi / pitch
    nt.links.new(dot.outputs["Value"], mul.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = 'SINE'
    nt.links.new(mul.outputs["Value"], sn.inputs[0])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    bp.inputs["Distance"].default_value = 0.06
    nt.links.new(sn.outputs["Value"], bp.inputs["Height"])
    if prev is not None:
        nt.links.new(prev, bp.inputs["Normal"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    _LAYER_MATS[key] = m
    return m


def render(placed, views, samples, size, palette, tag, preview=False, layers=False):
    import skin_photo as P
    pick = materials(palette)
    for name, obj, _, _ in placed:
        mat = pick(name)
        nrm = layer_normal(name) if layers else None
        U.set_material(obj, with_layers(mat, nrm) if nrm else mat)
        U.shade(obj)
        for f in obj.data.polygons:
            if abs(f.normal.z) > 0.999 or abs(f.normal.x) > 0.999:
                f.use_smooth = False
    bbs = [U.bbox(o) for n, o, _, _ in placed if n != "plate"]
    bb = (min(b[0] for b in bbs), max(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs),
          min(b[4] for b in bbs), max(b[5] for b in bbs))
    P.studio(bb, PLATE_Z[0])
    os.makedirs(OUT_REN, exist_ok=True)
    out = []
    for v in views:
        direction, zoom, tgt = CC.VIEWS[v]
        cam = S.camera(direction, bb, zoom * 1.08, lens=70.0, target=tgt)
        if not preview:
            cam.data.dof.use_dof = True
            tp = Vector(tgt or ((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
            cam.data.dof.focus_distance = (cam.location - tp).length
            cam.data.dof.aperture_fstop = 5.6 if zoom < 1.3 else 4.0
        path = os.path.join(OUT_REN, f"{v}{tag}.png")
        t0 = time.time()
        S.render(path, size=size, samples=samples)
        print(f"  rendered {v} ({time.time()-t0:.0f}s)", flush=True)
        out.append(path)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--photo", action="store_true")
    ap.add_argument("--views", default="front_right")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--size", default="1600x1200")
    ap.add_argument("--palette", default="orange")
    ap.add_argument("--tag", default="")
    ap.add_argument("--all-silver", action="store_true")
    ap.add_argument("--layers", action="store_true", help="show 0.4 mm print layer lines")
    a = ap.parse_args(argv)
    global ALL_SILVER
    ALL_SILVER = a.all_silver
    placed = build_all()
    if a.export and not a.all_silver:
        export(placed)
    if a.preview:
        render(placed, a.views.split(","), 16, (900, 675), a.palette, a.tag + "_preview", preview=True, layers=a.layers)
    if a.photo:
        w, h = (int(v) for v in a.size.lower().split("x"))
        render(placed, a.views.split(","), a.samples, (w, h), a.palette, a.tag, layers=a.layers)


if __name__ == "__main__":
    main(sys.argv[1:])
