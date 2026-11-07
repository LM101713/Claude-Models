"""BK-01 BOOKMARKS: a realistic set of bookmarks for the fit test and the hero render.

Each prop is a solid box (the bookmark's envelope) placed standing in the compartment the
way a customer would drop it in. The validator requires zero interference between every
prop and the part, and the renders show exactly these solids.
"""

from manifold3d import Manifold

from . import params as P
from .geom import to_world

# name, material, (width X, thickness Y, length Z), centre (x, y), lean about Y (deg),
# lean about X (deg), twist about Z (deg)
SET = [
    ("fabric_floral", "fabric", (50.8, 1.6, 165.0), (34.0, 8.0), -4.0, 0.0, 2.0),    # 2 x 6.5 in ribbon-embroidered
    ("wood_engraved", "wood", (40.0, 3.2, 150.0), (52.0, 28.5), 6.0, -1.5, -3.0),   # thick laser-cut wood
    ("leather_strap", "leather", (25.0, 2.6, 140.0), (47.0, 18.0), 3.0, 2.0, 4.0),   # folded leather
    ("card_classic", "card", (50.8, 0.6, 152.4), (37.0, 35.5), -2.0, -1.5, 0.0),     # 2 x 6 in card stock
]


def placed(size, cxy, lean_y, lean_x, twist, floor_clear=0.3):
    w, t, L = size
    b = Manifold.cube([w, t, L], center=True).rotate([lean_x, lean_y, twist])
    zmin = b.bounding_box()[2]
    return b.translate([cxy[0], cxy[1], P.FLOOR + floor_clear - zmin])


def bookmark_set():
    out = []
    for name, mat, size, cxy, ly, lx, tw in SET:
        m = to_world(placed(size, cxy, ly, lx, tw))
        bb = m.bounding_box()
        d = dict(name=name, mat=mat, size=size, solid=m)
        if name == "fabric_floral":
            d["tassel"] = (bb[0] + 4.0, P.D - cxy[1], bb[5] - 3.0)
        out.append(d)
    return out


def standard_gauge():
    """The worst-case single bookmark: a 2.0 x 7 in (50.8 x 178 mm) card, upright, centred,
    plus a 3 mm-thick 50.8 mm-wide block (a stack of ~6 cards or a thick wooden one)."""
    cx = 0.5 * (P.CAV_X0 + P.CAV_X1)
    cy = 0.5 * (P.CAV_Y0 + P.CAV_Y1)
    return to_world(placed((50.8, 3.0, 178.0), (cx, cy), 0.0, 0.0, 0.0))
