"""00 - Fit check piece (OPTIONAL).

All press fits in the engine use crush ribs, which tolerate normal printer
variation, so this piece is not required before building. Print it only if
you change printer, nozzle or material, or if a fit feels wrong.

Every fit used in the engine is printed five times. Crush-rib rows vary the
rib interference, slip rows vary the hole diameter, by -0.10 / -0.05 / 0 /
+0.05 / +0.10 mm around the current config value. Columns are labelled on
the plate. Find the best hole in a row and add that column's offset to the
matching entry in config.py (CRUSH interference, or FIT for slip fits).

The vertical fin at the back tests HORIZONTAL holes (as printed in the
piston pin bosses and the crank-web magnet pocket).
"""

import cadquery as cq

from common import C, box, crush_d_x, crush_params, cyl_z, polar, safe_clean

OFFSETS = (-0.10, -0.05, 0.0, 0.05, 0.10)
COL_PITCH = 28.0
X0 = 26.0                      # first column centre (room for row labels)
PLATE_T = 7.0
PLATE_W = X0 + COL_PITCH * 4 + 20
TEXT_D = 0.6

# (label, nominal diameter, fit key, depth or None for through, kind)
ROWS = [
    ("608",  C.BEARING_608["od"], "bearing_608", None, "crush"),
    ("686",  C.BEARING_686["od"], "bearing_686", None, "crush"),
    ("BU5",  C.BUSHING["od"],     "bushing_5",   None, "crush"),
    ("R3",   C.RAIL_DIA,          "rail_3_slip", None, "slip"),
    ("S8",   C.SHAFT_D,           "shaft_8",     None, "slip"),
    ("MAG",  C.MAGNET["d"],       "magnet_6",    C.MAGNET["h"] + 0.3, "crush"),
    ("INS",  C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3", C.INSERT_DEPTH, "slip"),
    ("D6",   C.PIN_DIA,           "dpin_6",      None, "dcrush"),
]
ROW_PITCH = {"608": 30.0, "686": 21.0}
DEFAULT_ROW_PITCH = 13.0


def _crush_z_custom(d_nom, z0, z1, x, y, fit, interf, entry_z):
    """Crush hole along Z with an explicit interference (for the test columns).
    The part is pressed in from entry_z; ribs stop CRUSH_LEAD short of it."""
    n, bore, rr, _ = crush_params(d_nom, fit)
    cr = (d_nom - interf) / 2 + rr
    cut = cyl_z(bore / 2, z0, z1, x, y)
    for i in range(n):
        ry, rz = polar(cr, i * 360.0 / n)
        cut = cut.cut(cyl_z(rr, z0 - 0.1, entry_z - C.CRUSH_LEAD, x + ry, y + rz))
    return cut


def _engrave(solid, text, x, y, size=4.0):
    t = (cq.Workplane("XY").workplane(offset=PLATE_T - TEXT_D)
         .center(x, y).text(text, size, TEXT_D + 0.1, halign="center", valign="center",
                             kind="bold"))
    return solid.cut(t.val())


def build():
    ys = []
    y = 8.0
    for label, *_ in ROWS:
        p = ROW_PITCH.get(label, DEFAULT_ROW_PITCH)
        ys.append(y + p / 2)
        y += p
    plate_h = y + 4.0
    plate = box(0, PLATE_W, 0, plate_h, 0, PLATE_T)

    for (label, nom, fit, depth, kind), yc in zip(ROWS, ys):
        for i, off in enumerate(OFFSETS):
            x = X0 + i * COL_PITCH
            z0 = PLATE_T - depth if depth else -1
            if kind == "crush":
                interf = C.CRUSH[fit][1] + off
                h = _crush_z_custom(nom, z0, PLATE_T + 1, x, yc, fit, interf, PLATE_T)
            elif kind == "dcrush":
                # D-hole along Z: build along X then turn upright
                h = crush_d_x(nom, C.PIN_DFLAT, -1, PLATE_T + 1, 0, 0, 90.0, entry="hi")
                h = h.rotate((0, 0, 0), (0, 1, 0), -90).translate(cq.Vector(x, yc, 0))
            else:
                d = C.hole(nom, fit) + off
                h = cyl_z(d / 2, z0, PLATE_T + 1, x, yc)
            plate = plate.cut(h)
        plate = _engrave(plate, label, 9.0, yc, 3.6)

    for i, off in enumerate(OFFSETS):
        txt = "0" if off == 0 else f"{off:+.2f}".replace("0.", ".")
        plate = _engrave(plate, txt, X0 + i * COL_PITCH, 4.0, 3.6)

    # vertical fin with horizontal holes: 5 x wrist pin (crush), 5 x magnet (crush)
    fin_t, fin_h = 9.0, 16.0
    fin = box(0, PLATE_W, plate_h, plate_h + fin_t, 0, fin_h)
    for i, off in enumerate(OFFSETS):
        x = X0 + i * COL_PITCH
        for d_nom, fit, xo, depth in ((C.WRIST_PIN["d"], "pin_3", -6, fin_t + 2),
                                       (C.MAGNET["d"], "magnet_6", 5, C.MAGNET["h"] + 0.3)):
            h = _crush_z_custom(d_nom, 0, depth, 0, 0, fit, C.CRUSH[fit][1] + off, depth)
            # turn so +Z becomes +Y, with the entry end on the fin's back face
            h = h.rotate((0, 0, 0), (1, 0, 0), -90)
            y_face = plate_h + fin_t + (0.01 if fit == "magnet_6" else 1.0)
            fin = fin.cut(h.translate(cq.Vector(x + xo, y_face - depth, 10.0)))
    part = safe_clean(plate.fuse(fin))
    part = _engrave(part, "P3  MAG (fin)", PLATE_W - 40, plate_h - 2.2, 3.0)
    return part


if __name__ == "__main__":
    from common import export
    s = build()
    print(export(s, "00_fit_check_optional"))
