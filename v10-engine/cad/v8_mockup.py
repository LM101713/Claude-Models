"""ROUGH PROPORTION MOCKUP of the stock-car V8 - masses only, for comparison
with the reference images. Not a part design: nothing here is printable or
checked. Same engine frame as the V10: X = crank axis (+X front), Z up, Y right.

    python cad/v8_mockup.py      -> renders/v8_mockup/*.png + dimension summary

Proportions come from a real Cup-style small-block scaled so the model bore
equals the existing 44 mm piston (real bore 4.185 in = 106.3 mm -> scale 1 : 2.33),
NOT from the AI images (which are used for style only).
"""

import math
import os
import sys

import cadquery as cq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

SCALE = 44.0 / 106.3                     # model / real (reuses the V10 piston)
IN = 25.4 * SCALE                        # one real inch in model mm


def inch(v):
    return v * IN


# ---- real-engine proportions (Cup-style small block, generic) ---------------
BORE_PITCH = 50.0                        # keep the LED-strip pitch (real 4.400 in = 47.9 model: +4 %)
N_CYL = 4                                # per bank
BANK_ANGLE = 90.0
DECK_H = inch(9.0)                       # crank centre to deck (real 9.000 in)
BLOCK_L = N_CYL * BORE_PITCH + 2 * 24.0  # 248 mm
BANK_W = inch(5.2)                       # bank block width across the deck
HEAD_H = inch(3.6)
HEAD_W = inch(5.4)
VC_L, VC_W, VC_H = inch(19.0), inch(4.6), inch(2.8)
VC_R = 6.0                               # valve-cover corner radius (the "soft rectangle")
OIL_CAP_D, OIL_CAP_H = inch(2.6), inch(0.7)
PAN_L, PAN_W, PAN_D = BLOCK_L - 10.0, inch(11.5), inch(7.5)
CASE_R = inch(5.0)                       # crankcase lower round
PLENUM_L, PLENUM_W, PLENUM_H = inch(11.0), inch(6.5), inch(3.2)
RUNNER_D = inch(2.0)
TB_D, TB_L = inch(3.8), inch(2.4)
PRIMARY_D = inch(1.875)
COLLECTOR_D = inch(3.5)
DAMPER_D, DAMPER_T = inch(7.0), inch(1.1)
PULLEY_D, PULLEY_T = inch(3.4), inch(0.9)
ALT_D, ALT_L = inch(5.2), inch(5.5)
BELL_D, BELL_T = inch(14.0), inch(1.6)
FRONT_COVER_T = inch(0.7)
BASE_L, BASE_W, BASE_T = 380.0, 250.0, 10.0
BRACKET_H = 55.0                         # pan bottom above the base plate

Z_CRANK = PAN_D + BRACKET_H + BASE_T     # crank axis height above the table
X_FRONT = BLOCK_L / 2
X_REAR = -BLOCK_L / 2


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cyl(r, h, p, d):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*p), cq.Vector(*d))


def rot_x(s, deg):
    return s.rotate((0, 0, 0), (1, 0, 0), deg)


def rounded_box(x0, x1, y0, y1, z0, z1, r, edges="|Z"):
    s = box(x0, x1, y0, y1, z0, z1)
    return cq.Workplane().add(s).edges(edges).fillet(r).val()


def to_engine(sign, yl, zl):
    """Bank-local (y, z) -> engine (y, z). Bank A (sign=-1) leans to -Y."""
    a = math.radians(-sign * BANK_ANGLE / 2)
    return yl * math.cos(a) - zl * math.sin(a), yl * math.sin(a) + zl * math.cos(a)


def bank(sign):
    """One bank: block prism + head + valve cover + oil cap, in the engine frame.
    Built along +Z (bore axis) then rotated +/-45 deg about X."""
    y0, y1 = -BANK_W / 2, BANK_W / 2
    blk = box(X_REAR, X_FRONT, y0 - 4, y1 + 4, inch(2.6), DECK_H)
    blk = cq.Workplane().add(blk).edges("|X").chamfer(3.0).val()
    head = rounded_box(X_REAR + 4, X_FRONT - 4, -HEAD_W / 2, HEAD_W / 2, DECK_H, DECK_H + HEAD_H, 2.5, "|X")
    vc = rounded_box(-VC_L / 2, VC_L / 2, -VC_W / 2, VC_W / 2, DECK_H + HEAD_H, DECK_H + HEAD_H + VC_H, VC_R)
    vc = cq.Workplane().add(vc).faces(">Z").edges().fillet(4.0).val()
    cap = cyl(OIL_CAP_D / 2, OIL_CAP_H, (VC_L / 2 - inch(4.0), -VC_W / 2 + inch(1.4), DECK_H + HEAD_H + VC_H - 0.5), (0, 0, 1))
    # exhaust flanges on the outboard face of the head, one per cylinder
    flanges = None
    yo = sign * HEAD_W / 2                      # outboard face of the head, bank-local
    for i in range(N_CYL):
        x = X_REAR + 24.0 + BORE_PITCH * (i + 0.5)
        f = box(x - 14, x + 14, min(yo, yo + sign * 4.0) - 0.5, max(yo, yo + sign * 4.0) + 0.5,
                DECK_H + 6, DECK_H + HEAD_H - 6)
        flanges = f if flanges is None else flanges.fuse(f)
    parts = {"block": blk, "head": head.fuse(flanges), "valve_cover": vc.fuse(cap)}
    ang = -sign * BANK_ANGLE / 2              # bank A (-Y) leans to -Y
    return {k: rot_x(v, ang) for k, v in parts.items()}


def crankcase():
    body = cyl(CASE_R, BLOCK_L, (X_REAR, 0, 0), (1, 0, 0))
    upper = box(X_REAR, X_FRONT, -CASE_R, CASE_R, 0, inch(3.5))
    body = body.fuse(upper)
    skirt = box(X_REAR, X_FRONT, -PAN_W / 2 + 8, PAN_W / 2 - 8, -CASE_R - 6, 0)
    return body.fuse(skirt)


def oil_pan():
    z1 = -CASE_R - 6
    z0 = z1 - PAN_D
    pan = rounded_box(-PAN_L / 2, PAN_L / 2, -PAN_W / 2, PAN_W / 2, z0, z1, 10.0)
    pan = cq.Workplane().add(pan).faces("<Z").edges().fillet(8.0).val()
    # ribs: vertical fins on both long sides, repeated every 20 mm
    for i in range(int(PAN_L // 20) - 1):
        x = -PAN_L / 2 + 20 + i * 20
        for s in (-1, 1):
            rib = box(x - 1.5, x + 1.5, s * PAN_W / 2 - (2.5 if s > 0 else -0.5) - (0 if s > 0 else 2.0),
                      s * PAN_W / 2 + (0.5 if s > 0 else 2.5), z0 + 8, z1 - 4)
            pan = pan.fuse(rib)
    rail = box(-PAN_L / 2 - 4, PAN_L / 2 + 4, -PAN_W / 2 - 4, PAN_W / 2 + 4, z1 - 5, z1)
    return pan.fuse(rail)


def intake():
    z_valley = DECK_H * math.cos(math.radians(45)) + 6.0           # roughly the head's inner face height
    zp0 = z_valley + inch(1.6)
    plenum = rounded_box(-PLENUM_L / 2, PLENUM_L / 2, -PLENUM_W / 2, PLENUM_W / 2, zp0, zp0 + PLENUM_H, 8.0)
    plenum = cq.Workplane().add(plenum).faces(">Z").edges().fillet(5.0).val()
    runners = None
    for i in range(N_CYL):
        x = X_REAR + 24.0 + BORE_PITCH * (i + 0.5)
        for s in (-1, 1):
            # runner: from the plenum's lower side, curving out and down onto the head's inner face
            ye, ze = to_engine(s, -s * HEAD_W / 2, DECK_H + HEAD_H * 0.55)
            y_start = s * (PLENUM_W / 2 - 4)
            z_start = zp0 + PLENUM_H * 0.35
            path = (cq.Workplane("YZ", origin=(x, 0, 0))
                    .spline([(y_start, z_start), (s * (PLENUM_W / 2 + 14), z_start - 6),
                             (ye - s * 2, ze + 4), (ye, ze)], includeCurrent=False))
            prof = (cq.Workplane("XZ", origin=(x, y_start, z_start)).circle(RUNNER_D / 2))
            r = prof.sweep(path, transition="round").val()
            runners = r if runners is None else runners.fuse(r)
    # throttle body on the front face, tilted up 15 deg
    tb = cyl(TB_D / 2, TB_L, (PLENUM_L / 2 - 2, 0, zp0 + PLENUM_H * 0.55), (math.cos(math.radians(15)), 0, math.sin(math.radians(15))))
    tb = tb.cut(cyl(TB_D / 2 - 3.0, TB_L + 2, (PLENUM_L / 2 - 2, 0, zp0 + PLENUM_H * 0.55),
                    (math.cos(math.radians(15)), 0, math.sin(math.radians(15)))))
    rails = None
    for s in (-1, 1):
        fr = cyl(inch(0.75) / 2, VC_L * 0.9, (-VC_L * 0.45, s * (PLENUM_W / 2 + 26), z_valley + 18), (1, 0, 0))
        rails = fr if rails is None else rails.fuse(fr)
    return {"plenum": plenum.fuse(runners), "throttle_body": tb, "fuel_rails": rails}


def headers(sign):
    """4 primaries: out of the head's outboard face at port height, then down
    and under the block into one collector beside the oil pan, tail to the rear."""
    yo = sign * (HEAD_W / 2 + 4.0)
    zo = DECK_H + HEAD_H * 0.45
    ny, nz = to_engine(sign, sign * 1.0, 0.0)             # outboard normal of the bank
    col_y = sign * (PAN_W / 2 + 34.0)
    col_z = -CASE_R - 18.0
    out = None
    for i in range(N_CYL):
        x = X_REAR + 24.0 + BORE_PITCH * (i + 0.5)
        y0, z0 = to_engine(sign, yo, zo)
        p0 = (x, y0, z0)
        p1 = (x, y0 + ny * 34, z0 + nz * 34)
        p2 = (x - 6, y0 + ny * 50 + sign * 14, z0 - 30)
        p3 = (x - 14 + (i - 1.5) * 4, col_y + sign * 2, col_z + COLLECTOR_D / 2 + 4)
        path = cq.Workplane("XY").spline([p0, p1, p2, p3], includeCurrent=False)
        prof = cq.Workplane(cq.Plane(origin=p0, xDir=(1, 0, 0), normal=(0, ny, nz))).circle(PRIMARY_D / 2)
        prim = prof.sweep(path, transition="round").val()
        out = prim if out is None else out.fuse(prim)
    x_c0 = X_REAR + 24.0 + BORE_PITCH * 0.5 - 30
    collector = cyl(COLLECTOR_D / 2, N_CYL * BORE_PITCH + 20, (x_c0, col_y, col_z), (1, 0, 0))
    tail = cyl(COLLECTOR_D / 2, 55.0, (x_c0, col_y, col_z), (-1, 0, -0.15))
    return out.fuse(collector).fuse(tail)


def front_cover():
    x0 = X_FRONT
    cover = box(x0, x0 + FRONT_COVER_T, -inch(7.5), inch(7.5), -CASE_R, inch(6.5))
    cover = cq.Workplane().add(cover).edges("|X").fillet(10.0).val()
    damper = cyl(DAMPER_D / 2, DAMPER_T, (x0 + FRONT_COVER_T + 14, 0, 0), (1, 0, 0))
    damper = damper.cut(cyl(DAMPER_D / 2 - 6, 2.0, (x0 + FRONT_COVER_T + 14 + DAMPER_T - 2, 0, 0), (1, 0, 0)))
    snout = cyl(inch(1.6), 16, (x0 + FRONT_COVER_T, 0, 0), (1, 0, 0))
    wp_out = cyl(inch(0.9), 30, (x0 + FRONT_COVER_T, 0, inch(4.5)), (1, 0, 0))
    idl1 = cyl(PULLEY_D / 2, PULLEY_T, (x0 + FRONT_COVER_T + 14, -inch(4.6), inch(3.6)), (1, 0, 0))
    idl2 = cyl(PULLEY_D / 2, PULLEY_T, (x0 + FRONT_COVER_T + 14, inch(2.2), inch(4.2)), (1, 0, 0))
    alt = cyl(ALT_D / 2, ALT_L, (x0 - inch(1.0), inch(7.2), inch(6.0)), (1, 0, 0))
    alt_p = cyl(inch(1.3), PULLEY_T, (x0 - inch(1.0) + ALT_L, inch(7.2), inch(6.0)), (1, 0, 0))
    return {"front_cover": cover.fuse(snout).fuse(wp_out), "damper": damper, "pulleys": idl1.fuse(idl2).fuse(alt_p), "alternator": alt}


def bellhousing():
    bell = cyl(BELL_D / 2, BELL_T, (X_REAR - BELL_T, 0, 0), (1, 0, 0))
    hub = cyl(inch(2.4), 6, (X_REAR - BELL_T - 6, 0, 0), (1, 0, 0))
    return bell.fuse(hub)


def base():
    z0 = -Z_CRANK
    plate = rounded_box(-BASE_L / 2, BASE_L / 2, -BASE_W / 2, BASE_W / 2, z0, z0 + BASE_T, 6.0)
    brackets = None
    pan_z = -CASE_R - 6 - PAN_D
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sx * (PAN_L / 2 - 30)
            # angled bracket: foot on the plate, leaning in to the pan side
            foot = box(x - 20, x + 20, sy * (PAN_W / 2 + 40) - 18, sy * (PAN_W / 2 + 40) + 18, z0 + BASE_T, z0 + BASE_T + 8)
            leg = (cq.Workplane("YZ", origin=(x - 20, 0, 0))
                   .polyline([(sy * (PAN_W / 2 + 58), z0 + BASE_T), (sy * (PAN_W / 2 + 22), z0 + BASE_T),
                              (sy * (PAN_W / 2 - 1), pan_z + 26), (sy * (PAN_W / 2 + 7), pan_z + 30)]).close()
                   .extrude(40).val())
            b = foot.fuse(leg)
            brackets = b if brackets is None else brackets.fuse(b)
    return {"base_plate": plate, "brackets": brackets}


def build():
    parts = []
    for sign in (-1, 1):
        for k, v in bank(sign).items():
            parts.append((f"{k}_{'A' if sign < 0 else 'B'}", v, {"block": "block", "head": "block", "valve_cover": "carbon"}[k]))
        parts.append((f"headers_{'A' if sign < 0 else 'B'}", headers(sign), "steel"))
    parts.append(("crankcase", crankcase(), "block"))
    parts.append(("oil_pan", oil_pan(), "block"))
    for k, v in intake().items():
        parts.append((k, v, {"plenum": "block", "throttle_body": "steel", "fuel_rails": "carbon"}[k]))
    for k, v in front_cover().items():
        parts.append((k, v, {"front_cover": "block", "damper": "carbon", "pulleys": "carbon", "alternator": "block"}[k]))
    parts.append(("bellhousing", bellhousing(), "block"))
    for k, v in base().items():
        parts.append((k, v, "carbon"))
    return parts


VIEWS = {
    # name: (camera direction from target, up) ~ matching the five reference images
    "ref1_closeup_34_above": ((0.55, -1.0, 0.75), (0, 0, 1)),
    "ref2_rear_left_34": ((-1.0, -0.9, 0.45), (0, 0, 1)),
    "ref3_front_right_34": ((1.0, 0.9, 0.45), (0, 0, 1)),
    "ref4_side_left": ((0.0, -1.0, 0.12), (0, 0, 1)),
    "ref5_front": ((1.0, 0.0, 0.15), (0, 0, 1)),
    "extra_top": ((0.0, 0.0, 1.0), (1, 0, 0)),
}


def main():
    import render
    out = os.path.join(ROOT, "renders", "v8_mockup")
    os.makedirs(out, exist_ok=True)
    parts = build()
    items = [(s, c) for _, s, c in parts]
    for name, view in VIEWS.items():
        zoom = 2.2 if name.startswith("ref1") else 1.0
        render.render(items, os.path.join(out, name + ".png"), view=view, size=(1448, 1086), zoom=zoom,
                      title=f"V8 proportion mockup - {name} (masses only, not a design)")
    comp = cq.Compound.makeCompound([s for _, s, _ in parts])
    bb = comp.BoundingBox()
    eng = cq.Compound.makeCompound([s for n, s, _ in parts if n not in ("base_plate", "brackets")]).BoundingBox()
    print(f"scale 1:{1 / SCALE:.2f}  (1 in = {IN:.1f} mm)")
    print(f"engine incl. headers/bell: {eng.xlen:.0f} long x {eng.ylen:.0f} wide x {eng.zlen:.0f} tall mm")
    print(f"with base: {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm;  block {BLOCK_L:.0f} long, deck height {DECK_H:.0f}, bore pitch {BORE_PITCH}")
    print(f"valve cover {VC_L:.0f} x {VC_W:.0f} x {VC_H:.0f}; pan {PAN_L:.0f} x {PAN_W:.0f} x {PAN_D:.0f}; damper {DAMPER_D:.0f}; bell {BELL_D:.0f}; TB {TB_D:.0f}")
    for n, s, _ in parts:
        b = s.BoundingBox()
        print(f"  {n:16s} {b.xlen:6.1f} x {b.ylen:6.1f} x {b.zlen:6.1f}")


if __name__ == "__main__":
    main()
