"""
TP-01 TUBEPRESS: every dimension in one place (millimetres, degrees).

Assembled coordinates (also the frame's print orientation):
    x  along the key axis. x = 0 is the inner face of the near (knob-side) lug, the far lug's
       inner face is at x = SLOT_L
    y  across the frame. The tube passes through the nip slot at y = 0
    z  up. The bottom of the frame plate is z = 0; the key axis is at z = AXIS_Z
"""

import math
from dataclasses import dataclass


# -------------------------------------------------------------------------------------
# Tubes (research ranges, RESEARCH.md)
# -------------------------------------------------------------------------------------
TUBE_FLAT_W = (32.0, 65.0)       # flattened width: travel tube .. family size
TUBE_WALL = (0.20, 0.35)         # one laminate wall
TUBE_CRIMP_T = (0.5, 1.2)        # crimp seal thickness (estimate: measure)
TUBE_CRIMP_H = 8.0               # crimp band height
TUBE_LEN = (100.0, 180.0)        # length that ends up wound


@dataclass(frozen=True)
class Params:
    # ---- frame ---------------------------------------------------------------------------
    slot_l: float = 68.0         # nip slot length = clear span between the lugs
    nip: float = 1.5             # nip slot width (the wiper): standard
    nip_chamfer: float = 0.8     # 45 deg lead-in on both edges of the nip, top and bottom
    plate_t: float = 2.4
    plate_w: float = 34.0        # y
    lug_t_near: float = 4.0
    lug_t_far: float = 4.0
    lug_w: float = 26.0          # y
    lug_wall: float = 3.2        # material above the bearing bore
    axis_z: float = 22.0
    bore_clear: float = 0.35     # radial clearance on both bearings
    corner_r: float = 3.0

    # ---- pawl (a leaf spring printed flat in the plate, under the knob) -----------------
    leaf_l: float = 20.0         # free length, along y
    leaf_w: float = 7.0          # x (wider = stiffer against buckling, same bending strain)
    leaf_t: float = 1.2          # z (6 layers at 0.2 mm)
    leaf_gap: float = 0.8        # U-cut around the leaf
    pawl_engage: float = 1.2     # how far the pawl tip reaches into the tooth gaps
    pawl_base_y: float = 4.0     # pawl post footprint along y
    knob_plate_ext: float = 3.0  # plate extends this far beyond the knob's outer face

    # ---- key -----------------------------------------------------------------------------
    shaft_d: float = 12.0
    fork_gap: float = 2.2        # open fork: takes crimps up to ~1.6 mm
    tip_chamfer: float = 1.5
    knob_gap: float = 0.5        # knob face to near lug
    knob_t: float = 8.0
    teeth: int = 24
    r_tip: float = 17.0
    tooth_depth: float = 1.5
    steep_frac: float = 0.30     # fraction of the pitch left for the root land + locking face (sets the pawl's width)
    undercut_deg: float = 4.0    # locking face leans past radial so the pawl is pulled in under load
    mark_w: float = 1.2          # index mark on the knob face (shows the fork-gap plane)
    mark_d: float = 0.6

    @property
    def r_root(self):
        return self.r_tip - self.tooth_depth


P = Params()

# Frame variants: the nip is the one dimension that depends on the printer and the tube
NIP_VARIANTS = {"Standard": 1.5, "Loose": 2.0, "Tight": 1.2}

# Material and budgets
BUDGET_G = 35.0
BUDGET_MIN = 90.0
BUILD_VOLUMES = {"Bambu Lab A1 mini": (180.0, 180.0, 180.0), "Bambu Lab A1 / P1S / X1C": (256.0, 256.0, 256.0)}
TARGET_BED = "Bambu Lab A1 mini"
BED_MARGIN = 5.0

# Material limits for the leaf (conservative fatigue-level strains)
LEAF_STRAIN_LIMIT = {"PLA": 0.008, "PETG": 0.012}
E_MPA = {"PLA": 3200.0, "PETG": 2000.0}


def knob_x(p=P):
    """x range of the knob (outside the near lug)."""
    x1 = -p.lug_t_near - p.knob_gap
    return x1 - p.knob_t, x1


def roll_radius(length, t_layer, r0):
    """Radius of a wound spiral of strip thickness t_layer over a core of radius r0."""
    return math.sqrt(r0 * r0 + length * t_layer / math.pi)
