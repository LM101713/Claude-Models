"""
GS-05 GIFT SLIDE: every dimension in one place.

Coordinates (assembled, closed):
  X  along the slide. x = 0 is the closed end of the tray, x = L the open end.
     The lid opens toward +X.
  Y  across, symmetric about y = 0.
  Z  up. z = 0 is the underside of the tray.
Lid-local coordinates: x from the lid's rear end (the end against the closed end wall),
z from the lid's underside. Units: millimetres.

Everything else (geometry, checks, drawings, renders, report) reads from here.
"""

from dataclasses import dataclass, field, replace
import math


@dataclass(frozen=True)
class Params:
    # ---------------------------------------------------------------- the gift
    card_l: float = 85.60          # ISO/IEC 7810 ID-1
    card_w: float = 53.98
    card_t: float = 0.76
    card_r: float = 3.18
    pocket_clear: float = 0.80     # per side, X and Y, around the card
    pocket_depth: float = 3.20     # card + up to ~4 quarter-folded notes
    pocket_r: float = 2.5          # pocket corner radius (card corner is 3.18)

    # ---------------------------------------------------------------- tray body
    floor_t: float = 1.20          # 6 layers at 0.2 mm
    end_wall: float = 2.40         # closed-end wall (full height); the lid stops on it
    open_wall: float = 2.00        # low wall at the open end, under the lid
    corner_r: float = 4.0          # plan-view corner radius of the outer body
    top_chamfer: float = 0.60      # outer top edges
    bottom_chamfer: float = 0.40   # outer bottom edges (also kills elephant's foot)

    # ---------------------------------------------------------------- lid section
    lid_t: float = 2.80            # lid thickness = tray rim height above the ledge
    land_h: float = 1.50           # vertical guide land at the bottom of the lid edge
    rebate_d: float = 0.65         # shadow-gap rebate depth below the lid top
    lip_tip_h: float = 0.40        # vertical face of the tray lip at the top
    lip_gap_z: float = 0.30        # lip underside sits this far above the lid bevel (vertical)
    lid_clear: float = 0.25        # lateral clearance, lid land to groove face (per side)
    land_y: float = 30.20          # half-width of the lid at its land (Y_f)
    slot_w: float = 0.80           # flexure slot width
    beam_w: float = 1.30           # flexure beam width at the land
    panel_chamfer: float = 0.30    # lid top edge chamfers
    lip_chamfer: float = 0.25      # tray lip inner top edge chamfer
    land_chamfer: float = 0.25     # lid bottom outer edge (elephant's foot)
    wall_behind: float = 1.60      # wall left behind the deepest relief

    # ---------------------------------------------------------------- detent
    beam_x0: float = 3.0           # flexure slot, lid-local
    beam_x1: float = 39.0
    bump_p: float = 0.60           # bump protrusion beyond the land
    bump_flat: float = 1.00        # bump flat (crest) length
    bump_front_deg: float = 65.0   # bump flank facing +X (meets R1 and the open stop)
    bump_rear_deg: float = 45.0    # bump flank facing -X (meets R1 when closing, and the lead-in)
    bump_h: float = 1.20           # bump height (lid-local z 0..bump_h)
    relief_d: float = 0.45         # relief-track depth into the groove face
    relief_floor: float = 0.30     # relief track runs this far below the ledge
    park_back: float = 0.50        # free play behind the parked bump
    park_front: float = 0.30       # free play in front of the parked bump
    r1_open_deg: float = 35.0      # R1 flank the bump climbs when opening
    r1_flat: float = 0.60          # R1 crest
    r1_close_deg: float = 28.0     # R1 flank the bump climbs when closing
    travel: float = 62.0           # lid travel from closed to the open stop
    stop_deg: float = 60.0         # open-stop flank (60: firm stop, lid removable by a tug)
    leadin_len: float = 1.60       # lead-in ramp at the tray's open end
    leadin_d: float = 0.65

    # ---------------------------------------------------------------- user features
    push_hole_d: float = 16.0      # finger hole in the floor, lifts the card
    push_hole_x: float = 16.0
    dish_d: float = 20.0           # thumb dish on the lid
    dish_depth: float = 0.60
    dish_x: float = 13.0           # lid-local
    message: str = "FOR YOU"       # debossed in the pocket floor, under the card ("" = none)
    message_h: float = 6.0
    message_depth: float = 0.40
    message_x: float = 44.0
    logo_depth: float = 0.40       # debossed brand on the underside
    star_r: float = 6.5            # optional star on the lid (Star variant)
    star_x: float = 72.0           # lid-local
    star_depth: float = 0.60       # 3 layers, so a filament swap gives a coloured inlay

    # ---------------------------------------------------------------- material / process
    E_mpa: float = 3000.0          # printed PLA, along the beads (range used: 2500-3500)
    mu: float = 0.30               # PLA on PLA, printed surfaces (range used: 0.20-0.45)
    rho: float = 1.24              # g/cm3
    layer: float = 0.20
    first_layer: float = 0.20

    # ---------------------------------------------------------------- derived
    @property
    def pocket_l(self):
        return self.card_l + 2 * self.pocket_clear

    @property
    def pocket_w(self):
        return self.card_w + 2 * self.pocket_clear

    @property
    def z_ledge(self):
        return self.floor_t + self.pocket_depth

    @property
    def H(self):
        return self.z_ledge + self.lid_t

    @property
    def L(self):
        return self.end_wall + self.pocket_l + self.open_wall

    @property
    def lid_l(self):
        return self.L - self.end_wall

    @property
    def y_g(self):          # groove face
        return self.land_y + self.lid_clear

    @property
    def bevel_top_z(self):  # lid-local z where the lid bevel meets the rebate floor
        return self.lid_t - self.rebate_d

    @property
    def bevel_run(self):    # 45 deg bevel: horizontal run == rise
        return self.bevel_top_z - self.land_h

    @property
    def y_lip(self):        # lip tip (inner edge of the rim)
        # lip underside: z = land_h + lip_gap_z + (land_y - y)   (lid-local)
        return self.land_y + self.land_h + self.lip_gap_z - (self.lid_t - self.lip_tip_h)

    @property
    def z_junction(self):   # lid-local z where the lip underside meets the groove face
        return self.land_h + self.lip_gap_z + (self.land_y - self.y_g)

    @property
    def beam_in(self):      # inner edge of the flexure beam
        return self.land_y - self.beam_w

    @property
    def panel_y(self):      # lid main panel half-width (top face)
        return self.beam_in - self.slot_w

    @property
    def W(self):
        return 2 * (self.y_g + self.relief_d + self.wall_behind)

    @property
    def beam_len(self):
        return self.beam_x1 - self.beam_x0

    @property
    def bump_x(self):       # lid-local bump centre = beam centre
        return 0.5 * (self.beam_x0 + self.beam_x1)

    @property
    def bump_front_run(self):   # bump root extends this far ahead of the crest's front edge
        return self.bump_p / math.tan(math.radians(self.bump_front_deg))

    @property
    def bump_rear_run(self):
        return self.bump_p / math.tan(math.radians(self.bump_rear_deg))

    @property
    def bump_front(self):   # from bump centre (crest centre) to the root's front end
        return 0.5 * self.bump_flat + self.bump_front_run

    @property
    def bump_rear(self):
        return 0.5 * self.bump_flat + self.bump_rear_run

    @property
    def bump_closed_x(self):  # tray x of the bump centre when the lid is closed
        return self.end_wall + self.bump_x

    def relief_profile(self):
        """Relief-track depth d(x) along each groove face, as (x, d) breakpoints.
        The bump runs in this track; where d = 0 it has to push the beam in."""
        D = self.relief_d
        xc = self.bump_closed_x
        t = lambda deg: D / math.tan(math.radians(deg))
        a1 = xc - self.bump_rear - self.park_back           # parking pocket, full depth from a1..a2
        a0 = a1 - D                              # 45 deg entry into the pocket (never used)
        a2 = xc + self.bump_front + self.park_front
        a3 = a2 + t(self.r1_open_deg)            # R1 opening flank
        a4 = a3 + self.r1_flat                   # R1 crest
        a5 = a4 + t(self.r1_close_deg)           # R1 closing flank
        b0 = xc + self.travel + self.bump_front  # open stop flank starts at the bump's front root
        b1 = b0 + t(self.stop_deg)
        e1 = self.L - self.leadin_len
        pts = [(-1.0, 0.0), (a0, 0.0), (a1, D), (a2, D), (a3, 0.0), (a4, 0.0), (a5, D),
               (b0, D), (b1, 0.0), (e1, 0.0), (self.L + 0.001, self.leadin_d), (self.L + 3, self.leadin_d)]
        return pts


P = Params()

# Lid fit variants, chosen with the fit coupon: Loose is 0.10 mm narrower per side (for printers
# that print slots tight), Snug is 0.10 mm wider per side (for printers that print slots wide).
LOOSE = 0.10
SNUG = 0.10

# A1 Mini build volume
BED = (180.0, 180.0, 180.0)

COLOURS = {
    "tray": ("Bambu PLA Matte", "Ivory White", "F2EEE5"),
    "lid": ("Bambu PLA Matte", "Scarlet Red", "C0272D"),
    "inlay": ("Bambu PLA Basic", "Gold", "E4BD68"),
}
