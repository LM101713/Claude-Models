"""fits.py - THE ONE FILE for every tolerance, clearance and fit allowance.

Every printed part reads its fits from here (through config.py). When a test
coupon shows a fit is too tight or too loose, change ONE number here and
rebuild (python build_all.py). Never put a clearance number inside a part
file: tools/check_fits.py fails the build if one appears.

All values in millimetres. "Diametral" = on the diameter (both sides added
together). The test coupons (T1-T6, docs/TEST_CHECKLIST.md) tell you which
number to change and by how much.

NOTHING HERE HAS BEEN PROVEN ON A REAL PRINTER YET. The values are sensible
starting points for a 0.4 mm nozzle; the coupons exist to correct them.
"""

# ---------------------------------------------------------------------------
# A. GLOBAL HOLE UNDERSIZE COMPENSATION
# ---------------------------------------------------------------------------
# Added to the diameter of EVERY printed round hole. Printers make holes
# undersize; 0.10 is a typical start for a Bambu at 0.4 mm nozzle.
#   Coupon T1: all slip holes tight by the same amount -> raise this.
HOLE_COMP = 0.10

# Default gap between two printed parts that must slide together or just
# touch (tabs, lips, locating faces). Applied per side.
CLEARANCE = 0.20

# ---------------------------------------------------------------------------
# B. SLIP / CLEARANCE FITS (diameter offsets on top of nominal + HOLE_COMP)
# ---------------------------------------------------------------------------
#   Coupon T1 (hole ladder): one kind of slip hole wrong -> change its entry.
FIT = {
    "rail_3_slip":  +0.05,   # 3 mm guide rail sliding through a printed hole
    "shaft_8":      +0.05,   # 8 mm main shaft through printed parts (clearance)
    "insert_m3":     0.00,   # heat-set insert pilot hole (see INSERT_HOLE_DIA)
    "spigot":       +0.10,   # printed spigots / pegs / locating bosses into holes
}

# ---------------------------------------------------------------------------
# C. PRESS FITS = CRUSH RIBS (bearings, bushings, pins, magnets, trumpets...)
# ---------------------------------------------------------------------------
# The hole is CRUSH_RELIEF bigger than the part; small half-round ribs stand
# proud of the wall so their tips are `interference` smaller than the part.
# Pressing the part in flattens the ribs, so the fit is firm and centred over
# a +/-0.15 mm printer error without tuning. UNPROVEN: a 0.4 mm nozzle may
# not resolve the ribs, and PLA may crack instead of crushing.
#   Coupons T3 (bearings), T4 (bushings, wrist pins), T5 (D-pins, magnets):
#   part falls out -> raise that interference by 0.05; cracks the plastic or
#   needs a hammer -> lower it by 0.05.
CRUSH_RELIEF = 0.30            # bore oversize (diameter) behind the ribs
CRUSH_RIB_R = 0.6              # rib radius (a rib is ~2-3 extrusion lines wide)
CRUSH_LEAD = 0.8               # rib-free lead-in at each entry, so parts start square
CRUSH = {
    # name: (number of ribs, diametral interference at the rib tips)
    "bearing_608": (8, 0.30),   # 608 main bearing into end plate
    "bearing_686": (6, 0.30),   # 686 big-end bearing into con-rod
    "bushing_5":   (4, 0.25),   # 3x5x4 bronze bushing into rod / piston lug
    "pin_3":       (3, 0.20),   # 3 mm wrist pin into piston bosses
    "dpin_6":      (2, 0.30),   # D-flat crankpin end: 2 ribs push the flat home
    "magnet_6":    (4, 0.25),   # 6x3 magnet pockets
    "trumpet_14":  (6, 0.25),   # intake trumpet spigot into the head port
    "coil_10":     (4, 0.25),   # coil-pack shaft into its socket in the head top
    "rail_3":      (3, 0.05),   # guide-rail ends (valley beam + head): snug and centred
}
MAGNET_DEPTH_CLEAR = 0.3       # magnet pocket deeper than the magnet (pocket bottoms never hold it proud)

# ---------------------------------------------------------------------------
# D. SCREWS AND HEAT-SET INSERTS
# ---------------------------------------------------------------------------
#   Coupon T2 (insert ladder): insert loose / pushes out while melting ->
#   lower INSERT_HOLE_DIA by 0.1; plastic bulges / insert sits proud -> raise.
M3_CLEAR = 3.4          # through hole for an M3 screw shank (+ HOLE_COMP)
M3_CBORE = 6.2          # counterbore for the 5.5 mm head (+ HOLE_COMP)
M3_TAP = 2.5            # self-tap hole in printed prototypes only
INSERT_HOLE_DIA = 4.0   # pilot hole for M3 x 5.7 heat-set inserts (4.6 OD type)
INSERT_DEPTH = 6.5      # pilot hole depth (insert length 5.7 + melt room)
CAPTIVE_LIP_D = 2.75    # bottom-panel screw holes: 1 mm lip between thread major (3.0)
CAPTIVE_LIP_T = 1.0     #   and minor (2.46) so the M3 screw threads through once and
                        #   then stays captive in the panel. Coupon T1 row "CAP".

# ---------------------------------------------------------------------------
# E. MOVING-PART CLEARANCES (nothing printed touches anything moving)
# ---------------------------------------------------------------------------
PISTON_RADIAL_CLEARANCE = 0.8  # piston skirt to bore, per side: the piston never touches the bore
LUG_POCKET_CLEAR = 0.8         # piston guide lug to its slot in the bank, per side
PISTON_BOSS_GAP = 1.0          # rod small end side float (each side) between the piston bosses
AXIAL_FLOAT = 0.6              # crank end float at the rear (floating) bearing
PIN_SOCKET_CLEAR = 0.3         # crankpin socket deeper than the pin end (shoulder seats on the web)
RAIL_POCKET_EXTRA = 0.5        # head rail pocket deeper than the rail engagement
COIL_SHAFT_SHORT = 0.5         # coil-pack shaft shorter than its socket (body seats on the head)
COIL_COVER_HOLE_CLEAR = 1.0    # cam-cover hole around the coil-pack body, per side
TRUMPET_FRAME_HOLE_CLEAR = 1.0 # throttle-frame hole around the trumpet spigot, per side
MOTOR_BOSS_SLOT_CLEAR = 0.5    # bulkhead slot around the NEMA17 pilot boss, per side
PANEL_EDGE_CLEAR = 0.4         # bottom panel edge to its rabbet, per side
LOCATOR_DEPTH_CLEAR = 0.5      # bank locator hole deeper than the crankcase locator boss
PLATE_CLEAR = 0.3              # edition plate to its recess, per side
MOTOR_TENSION_TRAVEL = 3.0     # motor slot travel beyond each belt's nominal position (belt tension)

# ---------------------------------------------------------------------------
# F. MACHINED STEEL PARTS (drawings M01-M06) - shop tolerances, not print fits
# ---------------------------------------------------------------------------
RING_ID_CLEAR = 0.03           # M06 spacer ring bore over the 6.00 crankpin journal
# Gear backlash: NOT APPLICABLE - the engine has no gears (3:1 GT2 belt drive).
