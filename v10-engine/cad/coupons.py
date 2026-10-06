"""Test coupons: small prints (each under 30 min) that prove every fit in
fits.py on YOUR printer before any engine part is printed.

Every hole carries its value engraved next to it (the resulting hole diameter
for slip fits, the rib interference for press fits, the pilot diameter for
inserts). Find the step that feels right; docs/TEST_CHECKLIST.md tells you
which number in fits.py to change.

  T1   hole ladder      slip fits: 3 mm rail, 8 mm shaft, M3 clearance
  T1b  test peg         two 5 mm printed pegs (for T1c)
  T1c  peg + captive    5 mm peg holes, captive-screw lip
  T2   insert ladder    heat-set insert pilots, vertical row + horizontal fin
  T3   608 seats        main-bearing crush-rib ladder (3 steps, 7 mm deep)
  T3b  686 seats        big-end bearing crush-rib ladder (5 steps)
  T4   piston guide     bronze-bushing crush ladder
  T4b  test lug         the piston's 9 mm guide lug, to slide in T4c
  T4c  lug slots        lug-slot clearance ladder
  T4d  wrist pins       wrist-pin crush ladder (horizontal holes, as in the piston)
  T5   D-pin sockets    D-flat crankpin socket ladder (3 steps, full depth)
  T5b  magnets          magnet pocket ladders, vertical row + horizontal fin
  T6   end-plate seat   the real 608 seat with its lip, nominal and -0.10
  T7   crank V-block    x2, assembly jig: both main shafts on one line
  T8   belt feeler      3.0 mm bar = belt deflection target

The engine has no gears (belt drive), so there is no gear-mesh coupon.
"""

import cadquery as cq

from common import C, box, crush_params, cyl_x, cyl_z, d_hole_x, polar, safe_clean

OFF5 = (-0.10, -0.05, 0.0, 0.05, 0.10)      # ladder steps around the fits.py value
OFF3 = (-0.10, 0.0, 0.10)
TXT_D = 0.5
LABEL_X = 10.0


def _engrave(solid, text, x, y, z_top, size=3.0):
    t = (cq.Workplane("XY").workplane(offset=z_top - TXT_D).center(x, y)
         .text(text, size, TXT_D + 0.1, halign="center", valign="center", kind="bold"))
    return solid.cut(t.val())


def _val(v):
    return f"{v:.2f}"


def _crush_custom_z(d_nom, z0, z1, x, y, fit, interf, entry_z):
    """Crush hole along Z with an explicit rib interference."""
    n, bore, rr, _ = crush_params(d_nom, fit)
    cr = (d_nom - interf) / 2 + rr
    cut = cyl_z(bore / 2, z0, z1, x, y)
    for i in range(n):
        ry, rz = polar(cr, i * 360.0 / n)
        cut = cut.cut(cyl_z(rr, z0 - 0.1, entry_z - C.CRUSH_LEAD, x + ry, y + rz))
    return cut


def _dcrush_custom_x(d_nom, x0, x1, y, z, interf, flat_dir_deg=90.0):
    """D-flat crankpin socket along X with an explicit rib interference."""
    n, bore, rr, _ = crush_params(d_nom, "dpin_6")
    cr = (d_nom - interf) / 2 + rr
    flat = d_nom / 2 - C.PIN_DFLAT + 0.05 + C.HOLE_COMP / 2
    cut = d_hole_x(bore, flat, x0, x1, y, z, flat_dir_deg)
    for a in (flat_dir_deg + 180.0 - 55.0, flat_dir_deg + 180.0 + 55.0):
        ry, rz = polar(cr, a)
        cut = cut.cut(cyl_x(rr, x0 - 0.1, x1 - C.CRUSH_LEAD, y + ry, z + rz))
    return cut


def _plate(rows, pitch_x, t, label, n_cols, margin=10.0):
    """rows: list of (row label, row pitch). Returns plate, row centres, x0, w, h.
    margin: label-to-first-hole-centre and last-hole-centre-to-edge distance."""
    x0 = LABEL_X + margin
    w = x0 + pitch_x * (n_cols - 1) + margin + 1.0
    ys, y = [], 6.0
    for _, p in rows:
        ys.append(y + p / 2)
        y += p
    h = y + 6.0
    plate = box(0, w, 0, h, 0, t)
    plate = cq.Workplane().add(plate).edges("|Z").chamfer(2.0).val()
    plate = _engrave(plate, label, w - 9.0, h - 3.5, t, 2.8)
    return plate, ys, x0, w, h


def _fin(plate, w, h, fin_t, fin_h):
    return plate.fuse(box(0, w, h, h + fin_t, 0, fin_h))


# ---------------------------------------------------------------------------
def t1_hole_ladder():
    """Slip fits: rail 3 / shaft 8 / peg 5 / M3 clearance / captive lip."""
    t, px = 4.5, 12.0
    return _t1(("R3", "S8", "M3"), "T1")


def t1c_peg_captive():
    """Slip fits: 5 mm printed peg, captive-screw lip."""
    return _t1(("PEG", "CAP"), "T1c")


def _t1(which, label):
    t, px = 4.5, 12.0
    pitches = {"R3": 10.0, "S8": 13.0, "PEG": 11.0, "M3": 10.0, "CAP": 10.0}
    rows = [(k, pitches[k]) for k in which]
    plate, ys, x0, w, h = _plate(rows, px, t, label, 5)
    specs = {"R3": (C.RAIL_DIA, "rail_3_slip"), "S8": (C.SHAFT_D, "shaft_8"),
             "PEG": (5.0, "spigot"), "M3": (C.M3_CLEAR, None)}
    for (lab, p), yc in zip(rows, ys):
        plate = _engrave(plate, lab, LABEL_X, yc, t, 2.8)
        for i, off in enumerate(OFF5):
            x = x0 + i * px
            if lab == "CAP":
                d = C.CAPTIVE_LIP_D + off
                plate = plate.cut(cyl_z(C.hole(C.M3_CLEAR) / 2, C.CAPTIVE_LIP_T, t + 1, x, yc))
                plate = plate.cut(cyl_z(d / 2, -1, t + 1, x, yc))
            else:
                nom, fit = specs[lab]
                d = C.hole(nom, fit) + off
                plate = plate.cut(cyl_z(d / 2, -1, t + 1, x, yc))
            plate = _engrave(plate, _val(d), x, yc + p / 2 - 2.0, t, 1.9)
    return safe_clean(plate)


def t1b_test_peg():
    """5.0 mm printed peg, as on the base joint (print 2)."""
    peg = cyl_z(5.0 / 2, 0, 10.0).fuse(cyl_z(5.0, 0, 2.0))
    return safe_clean(cq.Workplane().add(peg).faces(">Z").edges().chamfer(0.5).val())


def t2_insert_ladder():
    """Heat-set insert pilots INSERT_HOLE_DIA +/-: vertical row + horizontal fin."""
    t, px = C.INSERT_DEPTH + 1.5, 12.0
    rows = [("INS", 12.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T2", 5)
    yc = ys[0]
    plate = _engrave(plate, "INS", LABEL_X, yc, t, 2.8)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        d = C.INSERT_HOLE_DIA + off
        plate = plate.cut(cyl_z(d / 2, t - C.INSERT_DEPTH, t + 1, x, yc))
        plate = _engrave(plate, _val(d), x, yc + 4.0, t, 1.9)
    fin_t, fin_h = C.INSERT_DEPTH + 1.5, 12.0
    plate = _fin(plate, w, h, fin_t, fin_h)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        d = C.INSERT_HOLE_DIA + off
        plate = plate.cut(cq.Solid.makeCylinder(d / 2, C.INSERT_DEPTH + 0.5, cq.Vector(x, h + fin_t + 0.01, 6.0),
                                                cq.Vector(0, -1, 0)))
    return _engrave(safe_clean(plate), "fin = horizontal", w / 2 - 6, h - 2.6, t, 2.0)


def _bearing_ladder(label, brg, fit, offs, px, t):
    rows = [(label, brg["od"] + 8.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T3" if label == "608" else "T3b", len(offs), margin=brg["od"] / 2 + 4.0)
    yc = ys[0]
    plate = _engrave(plate, label, LABEL_X, yc, t, 2.8)
    for i, off in enumerate(offs):
        x = x0 + i * px
        interf = C.CRUSH[fit][1] + off
        plate = plate.cut(_crush_custom_z(brg["od"], -1, t + 1, x, yc, fit, interf, t))
        plate = _engrave(plate, _val(interf), x, yc + brg["od"] / 2 + 2.2, t, 1.9)
    return safe_clean(plate)


def t3_608_seats():
    return _bearing_ladder("608", C.BEARING_608, "bearing_608", OFF3, 30.0, C.BEARING_608["w"])


def t3b_686_seats():
    return _bearing_ladder("686", C.BEARING_686, "bearing_686", OFF5, 20.0, C.BEARING_686["w"])


def t4_piston_guide():
    """Bushing crush ladder (vertical) + wrist-pin crush ladder (horizontal fin)."""
    t, px = 5.0, 12.0
    rows = [("BU5", 11.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T4", 5)
    yc = ys[0]
    plate = _engrave(plate, "BU5", LABEL_X, yc, t, 2.8)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        interf = C.CRUSH["bushing_5"][1] + off
        plate = plate.cut(_crush_custom_z(C.BUSHING["od"], -1, t + 1, x, yc, "bushing_5", interf, t))
        plate = _engrave(plate, _val(interf), x, yc + 3.6, t, 1.9)
    return safe_clean(plate)


def t4d_wrist_pins():
    """Wrist-pin crush ladder: horizontal holes in a bar, as in the piston bosses."""
    px, bar_t, bar_h = 12.0, 8.0, 12.0
    x0 = LABEL_X + 10.0
    w = x0 + px * 4 + 11.0
    bar = box(0, w, 0, bar_t, 0, bar_h)
    bar = cq.Workplane().add(bar).edges("|Y").chamfer(1.0).val()
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        interf = C.CRUSH["pin_3"][1] + off
        hole = _crush_custom_z(C.WRIST_PIN["d"], 0, bar_t + 2, 0, 0, "pin_3", interf, bar_t + 2)
        hole = hole.rotate((0, 0, 0), (1, 0, 0), -90)            # +Z -> +Y, entry on the +Y face
        bar = bar.cut(hole.translate(cq.Vector(x, bar_t + 1.0 - (bar_t + 2), 6.0)))
        bar = _engrave(bar, _val(interf), x, bar_t / 2, bar_h, 1.7)
    return _engrave(safe_clean(bar), "T4d PIN3", LABEL_X - 1, bar_t / 2, bar_h, 2.0)


def t4b_test_lug():
    """The piston guide lug, as printed on the piston: LUG_OD, with a handle."""
    lug = cyl_z(C.LUG_OD / 2, 0, 12.0).fuse(box(-3.0, 3.0, 0, 10.0, 0, 12.0)).fuse(box(-6, 6, 8, 14, 0, 4))
    return safe_clean(lug)


def t4c_lug_slots():
    """Lug-slot clearance ladder (per-side clearance LUG_POCKET_CLEAR +/-0.2)."""
    t, px = 6.0, 17.0
    lug_r = C.LUG_OD / 2
    rows = [("LUG", 19.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T4c", 5)
    yc = ys[0]
    plate = _engrave(plate, "LUG", LABEL_X, yc, t, 2.8)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        clear = C.LUG_POCKET_CLEAR + 2 * off
        r = lug_r + clear
        slot = cyl_z(r, -1, t + 1, x, yc - 2.0).fuse(box(x - r, x + r, yc - 2.0, yc + 4.0, -1, t + 1))
        plate = plate.cut(slot)
        plate = _engrave(plate, _val(clear), x, yc + 7.4, t, 1.9)
    return safe_clean(plate)


def t5_dpin_sockets():
    """D-flat crankpin socket ladder (vertical D-holes, full socket depth)."""
    depth = C.PIN_END_LEN + C.PIN_SOCKET_CLEAR
    t, px = depth + 1.5, 12.0
    rows = [("D6", 12.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T5", 3)
    yc = ys[0]
    plate = _engrave(plate, "D6", LABEL_X, yc, t, 2.8)
    for i, off in enumerate(OFF3):
        x = x0 + i * px
        interf = C.CRUSH["dpin_6"][1] + off
        hole = _dcrush_custom_x(C.PIN_DIA, -1, depth, 0, 0, interf)
        hole = hole.rotate((0, 0, 0), (0, 1, 0), -90)                 # +X -> +Z, entry at the top
        plate = plate.cut(hole.translate(cq.Vector(x, yc, t + 1 - depth + 1)))
        plate = _engrave(plate, _val(interf), x, yc + 4.3, t, 1.9)
    return safe_clean(plate)


def t5b_magnets():
    """Magnet pocket ladders: vertical row + horizontal fin (web / end plate / side panel)."""
    depth = C.MAGNET["h"] + C.MAGNET_DEPTH_CLEAR
    t, px = depth + 2.0, 12.0
    rows = [("MAG", 11.0)]
    plate, ys, x0, w, h = _plate(rows, px, t, "T5b", 5)
    yc = ys[0]
    plate = _engrave(plate, "MAG", LABEL_X, yc, t, 2.8)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        interf = C.CRUSH["magnet_6"][1] + off
        plate = plate.cut(_crush_custom_z(C.MAGNET["d"], t - depth, t + 1, x, yc, "magnet_6", interf, t))
        plate = _engrave(plate, _val(interf), x, yc + 3.8, t, 1.9)
    fin_t, fin_h = depth + 2.0, 12.0
    plate = _fin(plate, w, h, fin_t, fin_h)
    for i, off in enumerate(OFF5):
        x = x0 + i * px
        interf = C.CRUSH["magnet_6"][1] + off
        hole = _crush_custom_z(C.MAGNET["d"], 0, depth, 0, 0, "magnet_6", interf, depth)
        hole = hole.rotate((0, 0, 0), (1, 0, 0), -90)                 # +Z -> +Y, entry on the outer face
        plate = plate.cut(hole.translate(cq.Vector(x, h + fin_t + 0.01 - depth, 6.0)))
    return _engrave(safe_clean(plate), "fin = horizontal", w / 2 - 6, h - 2.6, t, 2.0)


def t6_end_plate_seat():
    """The real 608 seat of the end plate: pressed in from one face against a
    lip that touches only the outer ring. Nominal and -0.10 interference."""
    t = C.BEARING_608["w"] + 2.0
    w, h = 66.0, 30.0
    blk = box(0, w, 0, h, 0, t)
    blk = cq.Workplane().add(blk).edges("|Z").chamfer(2.0).val()
    for i, (interf, lab) in enumerate(((C.CRUSH["bearing_608"][1], "nom"), (C.CRUSH["bearing_608"][1] - 0.10, "-.10"))):
        x = 16.0 + i * 34.0
        seat = _crush_custom_z(C.BEARING_608["od"], 2.0, t + 1, x, h / 2, "bearing_608", interf, t)
        blk = blk.cut(seat).cut(cyl_z(C.BEARING_608_OUTER_LIP_ID / 2, -1, 3, x, h / 2))
        blk = _engrave(blk, lab, x, 2.6, t, 2.2)
    return _engrave(safe_clean(blk), "T6", w - 7, h - 3.0, t, 2.8)


def t7_crank_vblock():
    """V-block (print 2): both main shafts rest in the Vs on a flat table while
    the crank screws are tightened, then the crank is turned to check runout."""
    w, L, hgt = 34.0, 22.0, 20.0
    blk = box(-w / 2, w / 2, 0, L, 0, hgt)
    vee = (cq.Workplane("XZ").polyline([(-10.5, hgt + 0.1), (0.0, hgt - 10.5), (10.5, hgt + 0.1)]).close()
           .extrude(-L - 2).translate(cq.Vector(0, -1, 0)).val())
    blk = blk.cut(vee)
    lab = (cq.Workplane("XZ").workplane(offset=0.5).center(0, 5.0)
           .text("T7", 3.0, TXT_D + 0.1, halign="center", valign="center", kind="bold"))
    return safe_clean(blk.cut(lab.val()))


def t8_belt_feeler():
    bar = box(0, 40.0, 0, 15.0, 0, 3.0)
    bar = cq.Workplane().add(bar).edges("|Z").chamfer(1.5).val()
    return _engrave(safe_clean(bar), "BELT 3.0", 20.0, 7.5, 3.0, 3.2)


def build_all():
    return {
        "T1_hole_ladder": (t1_hole_ladder(), 1),
        "T1b_test_peg": (t1b_test_peg(), 2),
        "T1c_peg_captive": (t1c_peg_captive(), 1),
        "T2_insert_ladder": (t2_insert_ladder(), 1),
        "T3_608_seats": (t3_608_seats(), 1),
        "T3b_686_seats": (t3b_686_seats(), 1),
        "T4_piston_guide": (t4_piston_guide(), 1),
        "T4b_test_lug": (t4b_test_lug(), 1),
        "T4c_lug_slots": (t4c_lug_slots(), 1),
        "T4d_wrist_pins": (t4d_wrist_pins(), 1),
        "T5_dpin_sockets": (t5_dpin_sockets(), 1),
        "T5b_magnets": (t5b_magnets(), 1),
        "T6_end_plate_seat": (t6_end_plate_seat(), 1),
        "T7_crank_vblock": (t7_crank_vblock(), 2),
        "T8_belt_feeler": (t8_belt_feeler(), 1),
    }
