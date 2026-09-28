"""00 - Tolerance test piece.

Every fit used in the engine is printed five times, at the current config
value and at -0.10 / -0.05 / +0.05 / +0.10 mm around it. Columns are
labelled on the plate. After printing, find the best hole in each row and
add its column offset to the matching FIT entry in config.py.

The vertical fin at the back tests HORIZONTAL holes (as printed in the
piston pin bosses and the crank-web magnet pocket), which come out
differently from vertical holes.
"""

import cadquery as cq

from common import C, box, cyl_z

OFFSETS = (-0.10, -0.05, 0.0, 0.05, 0.10)
COL_PITCH = 28.0
X0 = 26.0                      # first column centre (room for row labels)
PLATE_T = 7.0
PLATE_W = X0 + COL_PITCH * 4 + 20
TEXT_D = 0.6

# (label, nominal diameter, fit key, depth or None for through, pitch-split)
ROWS = [
    ("608",  C.BEARING_608["od"], "bearing_608", None),
    ("686",  C.BEARING_686["od"], "bearing_686", None),
    ("BU5",  C.BUSHING["od"],     "bushing_5",   None),
    ("R3",   C.RAIL_DIA,          "rail_3_slip", None),
    ("S8",   C.SHAFT_D,           "shaft_8",     None),
    ("MAG",  C.MAGNET["d"],       "magnet_6",    C.MAGNET["h"] + 0.2),
    ("INS",  C.INSERT_HOLE_DIA - C.HOLE_COMP, "insert_m3", C.INSERT_DEPTH),
    ("D6",   C.PIN_DIA,           "dpin_6",      None),
]
ROW_PITCH = {"608": 30.0, "686": 21.0}
DEFAULT_ROW_PITCH = 13.0


def _engrave(solid, text, x, y, size=4.0):
    t = (cq.Workplane("XY").workplane(offset=PLATE_T - TEXT_D)
         .center(x, y).text(text, size, TEXT_D + 0.1, halign="center", valign="center",
                             kind="bold"))
    return solid.cut(t.val())


def build():
    # row y positions (top of plate = first row)
    ys = []
    y = 8.0
    for label, *_ in ROWS:
        p = ROW_PITCH.get(label, DEFAULT_ROW_PITCH)
        ys.append(y + p / 2)
        y += p
    plate_h = y + 4.0
    plate = box(0, PLATE_W, 0, plate_h, 0, PLATE_T)

    for (label, nom, fit, depth), yc in zip(ROWS, ys):
        for i, off in enumerate(OFFSETS):
            d = C.hole(nom, fit) + off
            x = X0 + i * COL_PITCH
            z0 = PLATE_T - depth if depth else -1
            h = cyl_z(d / 2, z0, PLATE_T + 1, x, yc)
            if label == "D6":
                # D-flat: flat towards +y at (d/2 - PIN_DFLAT)
                flat = box(x - d, x + d, yc + d / 2 - C.PIN_DFLAT, yc + d, -2, PLATE_T + 2)
                h = h.cut(flat)
            plate = plate.cut(h)
        plate = _engrave(plate, label, 9.0, yc, 3.6)

    # column headers
    for i, off in enumerate(OFFSETS):
        txt = "0" if off == 0 else f"{off:+.2f}".replace("0.", ".")
        plate = _engrave(plate, txt, X0 + i * COL_PITCH, 4.0, 3.6)

    # vertical fin with horizontal holes: 5 x piston pin press, 5 x magnet pocket
    fin_t, fin_h = 9.0, 16.0
    fin = box(0, PLATE_W, plate_h, plate_h + fin_t, 0, fin_h)
    for i, off in enumerate(OFFSETS):
        x = X0 + i * COL_PITCH
        d_pin = C.hole(C.WRIST_PIN["d"], "pin_3_press") + off
        d_mag = C.hole(C.MAGNET["d"], "magnet_6") + off
        pin = cq.Solid.makeCylinder(d_pin / 2, fin_t + 2, cq.Vector(x - 6, plate_h - 1, 10.0), cq.Vector(0, 1, 0))
        mag = cq.Solid.makeCylinder(d_mag / 2, C.MAGNET["h"] + 0.2, cq.Vector(x + 5, plate_h + fin_t - C.MAGNET["h"] - 0.2, 10.0), cq.Vector(0, 1, 0))
        fin = fin.cut(pin).cut(mag)
    part = plate.fuse(fin).clean()
    # label the fin rows on the plate top in front of it
    part = _engrave(part, "P3  MAG (fin)", PLATE_W - 40, plate_h - 2.2, 3.0)
    return part


if __name__ == "__main__":
    from common import export
    s = build()
    print(export(s, "00_tolerance_test"))
