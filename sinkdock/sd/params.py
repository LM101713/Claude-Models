"""
SD-01 SINKDOCK: every dimension in one place (millimetres, degrees).

Coordinates (as printed and as used, the part never rotates):
    x  across the dock, left to right (0 .. W)
    y  front to back. y = 0 is the front of the floor, the lip sits at y < 0, the back is y = D
    z  up. The bed / counter is z = 0
"""

import math
from dataclasses import dataclass, field


# -------------------------------------------------------------------------------------
# What it holds. Researched ranges (sources in RESEARCH.md). "max" sizes drive clearance,
# "min" sizes drive retention.
# -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Item:
    name: str
    dia_or_len: tuple  # (min, max) diameter for discs, length for blocks
    thick: tuple       # (min, max) thickness
    height: tuple = (0.0, 0.0)  # (min, max) height for blocks (0 for discs)


SCRUB_DADDY = Item("Scrub Daddy Original", (102.0, 105.0), (38.0, 41.0))
SCRUB_MOMMY = Item("Scrub Mommy", (95.0, 105.0), (38.0, 41.0))
RECT_SPONGE = Item("Rectangular sponge (Scotch-Brite HD class)", (108.0, 114.0), (15.0, 20.0), (64.0, 68.0))
# stored standing on its short end: 64-68 mm along y, 108-114 mm tall
SWELL = 1.5  # allowance on every max dimension for a soaked, warm sponge (no published data: assumption)


@dataclass(frozen=True)
class Params:
    # ---- bays (inner widths, x) ----------------------------------------------------------
    bay_disc: float = 46.0      # Scrub Daddy and Scrub Mommy bays (both researched at 38-41 mm thick)
    bay_rect: float = 24.4      # flat rectangular sponge, standing on its short end (24.0 beside the cup)
    bay_brush: float = 36.0     # dish-brush cup, inner x
    wall_outer: float = 1.6     # left/right outer walls
    wall_inner: float = 1.5     # dividers: the 1.5 mm working default for a 0.4 mm nozzle

    # ---- depth (y) -----------------------------------------------------------------------
    D: float = 70.0             # floor / divider depth
    lip: float = 12.0           # spouts reach this far in front of y = 0
    spout_root: float = 6.0     # spout width at its root = bay opening + this
    spout_tip: float = 12.0     # spout width at its tip

    # ---- floor ---------------------------------------------------------------------------
    z0: float = 2.0             # floor top at the front of each gutter (the lowest point of the bay floor)
    slope_y: float = 2.5        # deg, fall from back to front (toward the sink)
    slope_x: float = 5.0        # deg, cross-fall from each bay wall down to its centre gutter
    lip_slope: float = 3.0      # deg, fall of the spout top toward its tip
    groove_y: float = 8.0       # drip-break groove under each spout: distance in front of y = 0
    groove_w: float = 1.6
    groove_d: float = 0.5       # into the underside

    # ---- dividers ------------------------------------------------------------------------
    H: float = 32.0             # divider height
    top_r: float = 14.0         # rounded top corners (front and back)
    vent_w: float = 9.5         # diamond vents (w x h): upper sides 28 deg from vertical
    vent_h: float = 20.0
    vent_zc: float = 18.5
    vent_yc: tuple = (12.0, 23.0, 34.0, 45.0, 56.0)

    # ---- front returns (sponge stops) ------------------------------------------------------
    ret_h: float = 22.0
    ret_t: float = 1.8          # in y
    ret_disc: float = 9.0       # each side, disc bays -> 28 mm opening (sponge >= 38)
    ret_rect: float = 6.7       # each side, rect bay -> 11 mm opening (sponge >= 15)

    # ---- brush cup -------------------------------------------------------------------------
    cup_in_y: float = 28.0     # tight front-to-back: limits how far a brush can lean toward the sink or wall
    cup_t: float = 1.6
    cup_h: float = 62.0
    cup_slot: float = 12.0      # vertical slot front and back: drainage + cleaning
    cup_r_out: float = 1.0     # outer vertical edges (kept small: the walls meet the cup here)
    cup_r_in: float = 3.0      # bore corners
    cup_reveal: float = 0.4     # the cup stands this proud of the walls it meets
    cup_vent_w: float = 14.0    # one tall diamond vent through each side of the cup
    cup_vent_h: float = 40.0
    cup_vent_zc: float = 31.0

    # ---- overall -------------------------------------------------------------------------
    corner_r: float = 1.0

    @property
    def tan_y(self):
        return math.tan(math.radians(self.slope_y))

    @property
    def tan_x(self):
        return math.tan(math.radians(self.slope_x))

    @property
    def tan_lip(self):
        return math.tan(math.radians(self.lip_slope))


P = Params()


def layout(p=P):
    """x extents of every wall and bay, left to right."""
    walls, bays = [], []
    x = 0.0
    order = [("Scrub Mommy", p.bay_disc, "disc"), ("Scrub Daddy", p.bay_disc, "disc"),
             ("Dish brush", p.bay_brush, "brush"), ("Rectangular sponge", p.bay_rect, "rect")]
    walls.append((x, x + p.wall_outer))
    x += p.wall_outer
    for i, (name, w, kind) in enumerate(order):
        bays.append(dict(name=name, kind=kind, x0=x, x1=x + w, xc=x + w / 2, w=w))
        x += w
        t = p.wall_outer if i == len(order) - 1 else p.wall_inner
        walls.append((x, x + t))
        x += t
    return walls, bays, x


WALLS, BAYS, W = layout()
BRUSH_I = [i for i, b in enumerate(BAYS) if b["kind"] == "brush"][0]
CUP_WALLS = (WALLS[BRUSH_I], WALLS[BRUSH_I + 1])  # the two walls the brush cup shares


def cup_y(p=P):
    """y extents of the brush cup (inner), centred in depth for stability."""
    y0 = (p.D - p.cup_in_y) / 2
    return y0, y0 + p.cup_in_y


def floor_z(x, y, bay, p=P):
    """Analytic top of the floor inside a bay."""
    return p.z0 + y * p.tan_y + abs(x - bay["xc"]) * p.tan_x


# Printers. Build volumes from the manufacturers' spec pages.
BUILD_VOLUMES = {
    "Bambu Lab A1 mini": (180.0, 180.0, 180.0),
    "Bambu Lab A1 / P1S / X1C": (256.0, 256.0, 256.0),
    "Prusa MINI+": (180.0, 180.0, 180.0),
}
TARGET_BED = "Bambu Lab A1 mini"
BED_MARGIN = 5.0  # mm each side kept clear (skirt, purge, bed clips)

# Budgets from the brief
BUDGET_G = 60.0

# Dish brush assumptions for the stability check (no verified data: see PHYSICAL_TESTING.md)
BRUSH_G = 90.0          # a heavy brush (OXO Good Grips class)
BRUSH_CG = 150.0        # centre of mass above the handle tip
BRUSH_HANDLE_T = (18.0, 26.0)   # handle thickness range considered (thinner leans further)
BRUSH_HANDLE_W = (20.0, 32.0)
TIP_LIMIT_DEG = 10.0    # incline a freestanding product must survive (the IEC 60335-1 cl. 20.1 test angle)
BUDGET_MIN = 120.0
