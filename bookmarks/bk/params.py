"""BK-01 BOOKMARKS: every dimension in one place (millimetres).

Delivered frame (the book standing on the bed, exactly as it prints and as exported):

    X  width, the front cover's long side. x = 0 is the apex of the rounded spine, on the
       left as you face the front cover; x = W is the fore-edge (page lines), on the right.
    Y  depth. y = 0 is the frontmost point of the raised lettering (the front cover faces
       -Y, toward the viewer in Bambu Studio's default view); y = D is the back cover.
    Z  height. z = 0 is the print bed, z = H is the top of the covers.

The parameters below are written in the DESIGN frame, which differs only in Y: there the
back cover is y = 0 and the art stands proud toward +Y (so "YF", "CAV_Y0" etc. count from
the back cover). geom.to_world() turns the finished part around (y -> D - y).

The customer's dimensions are the bounding box of the finished part, decoration included.
"""

# ------------------------------------------------------------------ envelope (customer spec)
W = 79.0   # 3.11 in  front width (spine apex -> fore-edge)
D = 44.5   # 1.75 in  depth (back cover -> front of the raised lettering)
H = 84.3   # 3.32 in  height

# ------------------------------------------------------------------ front-face relief stack
# All relief stands proud of the front cover plane, so the plane sits behind y = D.
PLATE_RISE = 1.0      # raised nameplate above the cover
LETTER_RISE = 0.8     # lettering above the nameplate
LETTER_INLAY = 0.6    # white lettering also goes this deep into the nameplate (opacity)
RELIEF_MAX = PLATE_RISE + LETTER_RISE           # 1.8 - the deepest relief on the part
YF = D - RELIEF_MAX                             # 42.7 - the front cover plane

GROUND_RISE = 0.6     # meadow mound
FOLIAGE_RISE = 0.9    # stems, leaves, grass
VEIN_RISE = 0.55      # leaf midribs are cut back to this (relief, not a groove)
PETAL_RISE = 1.2      # petals
CENTRE_RISE = 1.5     # flower centres sit proud of the petals

RELIEF_STEP = 0.2     # relief is built in 0.2 mm slices so every underside is 45 deg
TOP_SOFTEN = 0.25     # the outermost 0.4 mm of each relief is eased by up to this much

# ------------------------------------------------------------------ book construction
SPINE_BULGE = 3.0     # sagitta of the rounded spine (x of the cover boards' spine edge)
BOARD = 2.0           # visible thickness of each cover board at the fore-edge
SQUARE = 1.2          # cover overhang past the page block at the fore-edge ("squares")
HEAD_SQUARE = 0.8     # page block sits this far below the covers at the head (top)
EDGE_R = 0.8          # plan-view rounding of every outer vertical edge
TOP_CHAMFER = 0.5     # outer top edge chamfer
FOOT_CHAMFER = 0.4    # outer bottom edge chamfer (elephant's-foot relief)
CHAMFER_STEP = 0.1    # chamfers are built in 0.1 mm steps (well under one layer)

HINGE_X = SPINE_BULGE + 2.2   # centre of the hinge groove ("joint") on both covers
HINGE_W = 1.2
HINGE_DEPTH = 0.5

PAGE_PITCH = 1.3      # page-line grooves on the fore-edge
PAGE_GROOVE_W = 0.5
PAGE_GROOVE_DEPTH = 0.35
PAGE_SKIN = 0.8       # thickness of the separately-colourable page-edge skin
PAGE_HEAD_CAP = 0.6   # the head (top) of the page block is also page colour

# ------------------------------------------------------------------ storage compartment
WALL = 2.0            # target wall (front, back, fore-edge, measured to groove bottoms)
FLOOR = 2.4
CAV_X0 = 6.0          # spine-side wall is thicker: it carries the spine and the hinge groove
CAV_X1 = W - SQUARE - PAGE_GROOVE_DEPTH - WALL          # 75.45
CAV_Y0 = WALL                                            # 2.0
CAV_Y1 = YF - WALL                                       # 40.7
CAV_R = 2.5           # vertical inside-corner radius (= floor fillet: the cavity is one convex hull)
CAV_FLOOR_R = 2.5     # floor-to-wall fillet
CAV_LIP = 0.5         # 45 deg lead-in chamfer around the inside of the opening

# ------------------------------------------------------------------ front-cover layout
# Cover panel = the flat front cover right of the hinge groove.
PANEL_X0 = HINGE_X + HINGE_W / 2 + 0.6
PANEL_X1 = W - EDGE_R
ART_CX = 0.5 * (PANEL_X0 + PANEL_X1)                    # ~42.2 - visual centre line

PLATE_W = 56.0
PLATE_Z0 = 52.0
PLATE_Z1 = 70.0
PLATE_R = 1.4
PLATE_SIDE_BEVEL = 0.4   # bevel on the nameplate's top and sides (bottom is 45 deg)

TEXT = "Bookmarks"
TEXT_MAX_W = PLATE_W - 4.6
TEXT_MAX_H = 13.6        # tallest ascender (B, k) to baseline
TEXT_GROW = 0.12         # thicken the font outline for FDM strength
TEXT_TILT = (-3.0, 2.0, -1.5, 2.5, -2.0, 1.5, -2.5, 2.0, -1.5)   # per-letter hand-lettered tilt
TEXT_BOUNCE = (0.0, 0.35, -0.15, 0.3, -0.2, 0.25, -0.1, 0.35, 0.0)

ART_Z0 = 12.0            # bottom of the meadow
ART_Z1 = 48.5            # nothing in the meadow goes above this (clear of the nameplate)

# ------------------------------------------------------------------ printability limits
NOZZLE = 0.4
MIN_FEATURE = 0.8        # narrowest relief a 0.4 nozzle prints as two lines
MIN_GAP = 0.6            # narrowest gap kept open between relief features
OVERHANG_MAX_DEG = 45.0

# ------------------------------------------------------------------ colour regions
# name -> (description, default filament slot in the 4-colour and 2-colour projects, hex)
PARTS = {
    "body":      ("Book body: covers, spine, nameplate", "F4A6C4"),
    "pages":     ("Page edges: fore-edge skin and head of the page block", "F3E9D2"),
    "lettering": ("'Bookmarks' lettering", "FFFFFF"),
    "petals":    ("Flower petals", "FFFFFF"),
    "centres":   ("Flower centres", "F6C443"),
    "foliage":   ("Stems, leaves, meadow mound", "F4A6C4"),
}
# Colour plans: part -> filament slot, and the filament in each slot.
#   FULL  4 filaments, as briefed: pink body, white lettering + petals, yellow centres,
#         ivory page edges.
#   TRIO  3 filaments: as FULL but the page edges print white. The page edges are in
#         417 of the 421 layers, so dropping ivory removes most of the colour changes.
#   DUO   2 filaments, pink + white, lowest waste: page edges white, centres pink
#         (pink-on-white flowers). On a two-nozzle H2C each filament has its own nozzle:
#         no flushing at all.
PLANS = {
    "FULL": dict(slots=dict(body=1, pages=4, lettering=2, petals=2, centres=3, foliage=1),
                 filaments={1: ("Pink", "F4A6C4"), 2: ("White", "FFFFFF"), 3: ("Yellow", "F6C443"),
                            4: ("Ivory", "F3E9D2")},
                 nozzles={"left": (1, 3), "right": (4, 2)}),
    "TRIO": dict(slots=dict(body=1, pages=2, lettering=2, petals=2, centres=3, foliage=1),
                 filaments={1: ("Pink", "F4A6C4"), 2: ("White", "FFFFFF"), 3: ("Yellow", "F6C443")},
                 nozzles={"left": (1, 3), "right": (2,)}),
    "DUO": dict(slots=dict(body=1, pages=2, lettering=2, petals=2, centres=1, foliage=1),
                filaments={1: ("Pink", "F4A6C4"), 2: ("White", "FFFFFF")},
                nozzles={"left": (1,), "right": (2,)}),
}
PETG_DENSITY = 1.27   # g/cm3, Bambu PETG Basic


def summary():
    return dict(
        envelope=(W, D, H), front_plane=YF,
        cavity=dict(x=(CAV_X0, CAV_X1), y=(CAV_Y0, CAV_Y1), z=(FLOOR, H),
                    w=CAV_X1 - CAV_X0, d=CAV_Y1 - CAV_Y0, h=H - FLOOR),
    )
