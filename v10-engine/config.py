"""
V10 display engine - single source of truth for every dimension.

HOW TO USE THIS FILE
--------------------
* All units are millimetres and degrees.
* Fit problems are fixed HERE, never by editing part geometry.
  - Press fits use crush ribs (see CRUSH) and need no tuning on a
    calibrated printer; if one is still too tight/loose, change its
    interference in CRUSH.
  - EVERY tolerance, clearance and fit allowance is in fits.py (one file).
    Test coupons T1-T6 + docs/TEST_CHECKLIST.md say which number to change.
* After changing anything run:  python build_all.py
  It regenerates every STL/STEP, preview image and drawing, and re-runs
  the self-checks at the bottom of this file.

COORDINATE SYSTEM (whole engine)
--------------------------------
* X = crankshaft axis. +X is the FRONT (drive-pulley end).
* Z = up.  Y = right when you stand at the front looking at the engine.
* Crank angles are measured in the Y-Z plane from +Z towards +Y.
  With that convention the crank turns CLOCKWISE seen from the front.
* Bank A = cylinders 1-5, on the -Y side (left, seen from the front).
  Bank B = cylinders 6-10, on the +Y side. Cylinder 1 is at the front.
"""

import math

# ---------------------------------------------------------------------------
# 1. TOLERANCES, CLEARANCES AND FITS live in fits.py (ONE file, nothing else
#    holds a clearance). Re-exported here so every part reads C.<NAME>.
# ---------------------------------------------------------------------------
from fits import *  # noqa: F401,F403  (HOLE_COMP, CLEARANCE, FIT, CRUSH*, M3_*, INSERT_*, ...)

# ---------------------------------------------------------------------------
# 2. PURCHASED HARDWARE (nominal sizes - change only if you change supplier)
# ---------------------------------------------------------------------------
BEARING_608 = dict(id=8.0, od=22.0, w=7.0)     # main bearings (2 per engine)
BEARING_686 = dict(id=6.0, od=13.0, w=5.0)     # big-end bearings (10 per engine)
# inner-ring shoulder of a 686 - anything touching the bearing side must
# stay inside this diameter so it only touches the inner ring
BEARING_686_INNER_SHOULDER = 7.5
BEARING_608_OUTER_LIP_ID = 18.5                # lip may only touch 608 outer ring

BUSHING = dict(id=3.0, od=5.0, l=4.0)          # sintered bronze 3x5x4 (standard size, 30 per engine)
WRIST_PIN = dict(d=3.0, l=20.0)                # ISO 8734 / DIN 6325 3x20 steel dowel
RAIL_DIA = 3.0                                  # ground stainless rod, cut to length
MAGNET = dict(d=6.0, h=3.0)                    # N52 6x3 disc magnets

M3_HEAD_D = 5.5         # socket head cap screw head
M3_HEAD_H = 3.0
SCREW_LENGTHS = (8, 16) # the ONLY two screw lengths in the design (M3 SHCS)
SCREW_FLOOR = 4.0       # plastic under a screw head when screwing into an insert
                        # (4 + 4 engaged in insert = M3x8)

# ---------------------------------------------------------------------------
# 3. ENGINE LAYOUT
# ---------------------------------------------------------------------------
N_CYL = 10
N_THROWS = 5
BANK_ANGLE = 90.0                     # degrees between the banks
BANK_A_ANGLE = -BANK_ANGLE / 2        # bank A axis angle (cyl 1-5, -Y side)
BANK_B_ANGLE = +BANK_ANGLE / 2        # bank B axis angle (cyl 6-10, +Y side)

# Firing order (cylinder numbers). 4-stroke: one cycle = 720 crank degrees.
FIRING_ORDER = [1, 6, 5, 10, 2, 7, 3, 8, 4, 9]
CYCLE_DEG = 720.0
FIRING_INTERVAL = CYCLE_DEG / N_CYL   # 72 deg -> even firing

STROKE = 26.0
CRANK_R = STROKE / 2                  # crank throw radius
ROD_LENGTH = 62.0                     # con-rod centre to centre
CYL_PITCH = 50.0                      # cylinder spacing along one bank (= 3 LEDs of a 60/m strip)
PISTON_DIA = 44.0                     # visual "bore" of the model
# PISTON_RADIAL_CLEARANCE: see fits.py
BORE_DIA = PISTON_DIA + 2 * PISTON_RADIAL_CLEARANCE

# Throw centres along X (throw 1 at the front / +X)
THROW_X = [(N_THROWS // 2 - k) * CYL_PITCH for k in range(N_THROWS)]

# ---------------------------------------------------------------------------
# 4. CRANKSHAFT
# ---------------------------------------------------------------------------
# Split crankpin (machined steel, one per throw). Along X from the front:
# [end A in web][shoulder][journal A][shoulder][flying web][shoulder][journal B][shoulder][end B in web]
PIN_DIA = 6.0                  # journal = 686 bore
PIN_DFLAT = 0.5                # depth of the D-flat on each pin end
PIN_END_LEN = 8.0              # length of each pin end inside a crank web
PIN_SHOULDER_D = BEARING_686_INNER_SHOULDER
PIN_SHOULDER_L = 0.75          # also the gap between rod body and web
PIN_FLYWEB_T = 1.5             # flying web between the two journals
PIN_TAP_DEPTH = 6.0            # M3 tapped depth in each pin end
# PIN_SOCKET_CLEAR: see fits.py
ROD_BODY_W = BEARING_686["w"]  # con-rod thickness = bearing width

THROW_INNER = 2 * (PIN_SHOULDER_L + BEARING_686["w"] + PIN_SHOULDER_L) + PIN_FLYWEB_T
ROD_X_OFFSET = PIN_FLYWEB_T / 2 + PIN_SHOULDER_L + BEARING_686["w"] / 2  # rod A at +, rod B at -
BANK_OFFSET = 2 * ROD_X_OFFSET        # bank A sits this much forward of bank B
PIN_LEN = 2 * PIN_END_LEN + THROW_INNER

WEB_T = 10.0                   # crank web thickness
WEB_HUB_R = 16.0               # web profile: circle around main axis
WEB_PIN_BOSS_R = 9.5           # web profile: circle around crankpin
WEB_CW_R = 24.0                # counterweight radius (max crank sweep)
WEB_CW_SPAN = 140.0            # counterweight arc (degrees)
JOURNAL_R = 17.0               # central "main journal" of each segment
SEGMENT_LEN = CYL_PITCH - THROW_INNER        # web + journal + web
END_WEB_T = 12.0               # the two end webs (carry the main shafts)
SCREW_CHANNEL_D = M3_CBORE     # access channel for crankpin screws
PIN_SCREW_FLOOR = 3.0          # web material under crankpin screw head (M3x8)
HALL_MAGNET_IN_WEB = True      # 6x3 magnet in the end-web rim (both webs are identical: fit one in each)
HALL_SENSOR_ANGLE = 180.0      # hall sensor sits straight below the crank (in the case floor) ...
HALL_SENSOR_END = "rear"       # ... under the REAR end web: its leads drop next to the controller, clear of the motor

# Main shaft (machined, identical front and rear). Built from the web outwards.
SHAFT_SPIGOT_D = 10.0
SHAFT_SPIGOT_L = 2.0
SHAFT_FLANGE_D = 28.0
SHAFT_FLANGE_T = 4.0
SHAFT_FLANGE_PCD = 20.0        # 3 x M3 bolt circle
SHAFT_FLANGE_BOLT_ANGLES = (70.0, 180.0, 290.0)   # UNEVEN on purpose: shaft fits one way only
SHAFT_ACCESS_HOLE_D = 7.0      # lets the crankpin screw pass through the flange
SHAFT_SHOULDER_D = 10.0
SHAFT_D = BEARING_608["id"]
# AXIAL_FLOAT: see fits.py
PULLEY_MAX_W = 18.0            # tallest 60T pulley we allow for (real ones are ~16 mm)
SHAFT_FLAT_DEPTH = 0.5         # flat for the pulley grub screws

# ---------------------------------------------------------------------------
# 5. CON-ROD, PISTON, GUIDE RAIL
# ---------------------------------------------------------------------------
ROD_BIG_END_WALL = 3.0         # plastic around the pressed 686 bearing (was 2.5: DFM risk A2, splitting)
ROD_BIG_END_OD = BEARING_686["od"] + 2 * ROD_BIG_END_WALL
ROD_SMALL_END_OD = BUSHING["od"] + 2 * 2.0
ROD_SHANK_W_SMALL = 7.0
ROD_SHANK_W_BIG = 10.0
ROD_FLUTE_DEPTH = 0.8

PISTON_PIN_TO_CROWN = 12.0     # compression height
PISTON_PIN_TO_SKIRT = 7.0
PISTON_CROWN_T = 3.0
PISTON_WALL_T = 2.0
# PISTON_BOSS_GAP: see fits.py
                               # crank's axial position (CRANK_DX) + print-length tolerance of the crank
VALVE_RELIEF_D = 14.0
VALVE_RELIEF_DEPTH = 0.8

# The piston is guided by ONE steel rail per cylinder, on the valley side,
# through two bronze bushings in a lug on the piston. The piston body never
# touches the bore (see docs/DESIGN_NOTES.md).
RAIL_OFFSET = 25.5             # rail distance from the cylinder axis (valley side)
LUG_OD = BUSHING["od"] + 2 * 2.0
LUG_TOP = PISTON_PIN_TO_CROWN         # lug flush with the crown, so the piston prints crown-down with no overhang
LUG_BOTTOM = -2.0
# LUG_POCKET_CLEAR: see fits.py

# ---------------------------------------------------------------------------
# 6. CRANKCASE, CYLINDER BANKS, END PLATES
# ---------------------------------------------------------------------------
FACE_DIST = 40.0               # crank axis -> bank mounting face (along bank axis)
DECK_DIST = ROD_LENGTH + CRANK_R + PISTON_PIN_TO_CROWN + 1.0   # crown 1 mm below deck at TDC
CASE_FLOOR_Z = -32.0           # underside of crankcase (sits on display base)
CASE_FLOOR_T = 4.0
CASE_INTERIOR_R = 28.0         # crank sweep 24 + 4 mm clearance
CASE_SLOT_HALF = 15.0          # con-rod slot half-width in each face (rod swing + 2 mm)
BLOCK_Y_OUT = -34.0            # bank block extent, outboard side (bank-local y)
BLOCK_Y_VALLEY = 38.0          # bank block extent, valley side
BLOCK_END_MARGIN = 30.0        # block material beyond the end cylinders (along X)
WINDOW_BOTTOM = 46.0           # cut-away window in the outboard wall (bank-local z)
WINDOW_TOP = DECK_DIST - 2.5   # leaves a 2.5 mm deck lip; more of the lit chamber shows
WINDOW_HALF_W = 17.0           # windows have a 45 deg V bottom (a gable roof on the printer)
BLOCK_SCREW_VALLEY_Y = 30.0    # 4 screws between cylinders, valley side (into the valley beam)
BLOCK_SCREW_END_Y = -20.0      # 2 screws at the block ends, outboard side (into the crankcase)
HEAD_SCREW_Y = (-17.0, 10.0)   # head screws go down the two cam lines into deck inserts (= CAM_Y)
SIDE_PANEL_MAGNET_Z = 65.0     # magnets between the windows hold the side panel
LOCATOR_D = 6.0                # printed locating pegs under each bank block
LOCATOR_H = 3.0
LOCATOR_Y = 21.0
RAIL_HOLE_DEPTH_CASE = 6.0     # rail bottom sits this deep in the valley beam
RAIL_HEAD_ENGAGE = 3.0         # rail top runs this far into a pocket in the cylinder head
END_PLATE_SPIGOT = 4.0
END_PLATE_FLANGE_T = 10.0
BEARING_LIP_T = 1.5
HALL_POCKET = dict(w=5.0, l=7.0, d=1.7)   # TO-92 (4.0 x 3.15 x 1.52) lies face-up in a pocket under the case floor
HALL_LEAD_SLOT = dict(w=4.0, l=2.0, dx=3.3)  # slot in the base top for the 3 bent leads (body cannot fall through)

# ---------------------------------------------------------------------------
# 6b. STYLING PARTS (Phase 3) - bank-local frame unless noted
# ---------------------------------------------------------------------------
HEAD_H = 28.0                  # cylinder head height above the deck
TRUMPET_FACE_Z = 96.0          # GLOBAL height of the heads' valley chamfer (horizontal)
CAM_Y = (-17.0, 10.0)          # exhaust / intake camshaft lines on the head top
CAM_R = 5.0
CAM_LOBE_R = 6.5               # lobe nose radius from the cam axis (cosmetic, static)
CAM_END_GAP = 9.0              # cams stop short of the head ends (loom turns there)
# Firing LEDs: a stock WS2812B strip, 60 LEDs/m (16.67 mm pitch), black PCB,
# 10 mm wide, IP30. CYL_PITCH = 3 LED pitches, so a 15-LED piece puts 3 LEDs
# over every bore. It lies LEDs-down in a groove in the head's deck face and
# lights the combustion chamber directly. Lead wires leave at the rear end.
LED_STRIP = dict(pitch=1000.0 / 60.0, n=15, w=10.0, t=2.1)
LED_GROOVE = dict(w=11.0, d=2.6,       # strip groove in the head deck face (LED face 0.5 mm above the deck)
                  end_wall=1.6)        # closed 1.6 mm short of both end faces: clean ends, no light leak
LED_WIRE_GROOVE = dict(w=4.4, d=3.8)   # lead pocket at each groove end, across the strip and on to the
                                       # valley side: the strip end + heat-shrink turn here (3.4 mm room
                                       # past the strip end); 3 x 24 AWG silicone (1.4 mm) as 2 + 1
COIL = dict(shaft_d=10.0, w=11.0, l=15.0, h=24.0)  # coil pack: stands up through the cam cover
COIL_SOCKET_D = 10.0                   # coil-pack socket depth in the head top
CAM_COVER = dict(y0=-33.0, y1=19.5, h=18.0, wall=3.0, chamfer=5.0, end_inset=1.0)
CAM_CAP_HALF_W = 6.0           # bearing caps: +/- this across the cam
SIDE_PANEL = dict(t=5.0, z0=44.0, z1=87.0, bulge=1.5)
PLENUM_T = 5.0                 # throttle rails (ladder frame) sit on both heads' valley chamfers
THROTTLE = dict(d=24.0, h=9.0)  # throttle-body boss under each trumpet
RAIL_W = 24.0                  # throttle rail width (= throttle body dia)
PLENUM_HALF_W = 65.0           # global y extent of the plenum floor (clears the cam covers by ~3 mm)
TRUMPET = dict(spigot_d=14.0, spigot_l=11.5, flange_d=21.0, flange_t=2.0,
               base_od=17.0, top_od=19.0, bell_od=32.0, bell_h=12.0, height=44.0, bore=12.0)
EXH_BACK_Y = -35.0             # exhaust back plane (1 mm off the head's outboard face)
EXH_PORT_Z = 102.0             # exhaust port centre height (bank-local z')
EXH_R_PRIMARY = 6.0
EXH_R_TRUNK = 9.5
EXH_OFFSET = 4.0               # tube centreline sits this far outboard of the flat back:
                               # ~85 % of each pipe is round, overhang still < 45 deg
EXH_TRUNK_Z = 124.0            # trunk centreline (z') - beside the cam cover
EXH_JOIN_DX = 46.0             # each primary joins the trunk this far behind its port (S-bend)
EXH_TAIL_X = -166.0            # tail pipe end (bank A local x) - keeps the part < 300 mm
EXH_TAIL_Z = 146.0             # short vertical stack above the bend ("periscope" exit)
EXH_FLANGE = dict(d=17.0, t=3.0)
EXH_SCREW_Z = EXH_PORT_Z - 2.0   # flange bolt sits just in front of each primary
EXH_SCREW_DX = 9.0             # ... this far forward of the port (the pipe leaves rearward)
EXH_DIP = 8.0                  # S-bend dip depth (min bend radius ~1.9x the pipe radius)
END_COVER_ZC = 30.0            # end covers: straight sides up to here, round top above

# ---------------------------------------------------------------------------
# 7a. DRIVE (Phase 2) - NEMA17 in the base, GT2 belt up to the front main shaft
# ---------------------------------------------------------------------------
# 3:1 reduction: engine 20-120 RPM = motor 60-360 RPM, where a stepper in
# StealthChop is smoothest and quietest, with 3x the torque at the crank.
PULLEY_BIG = dict(teeth=60, bore=8.0, width=16.0, hub_len=7.0, od=37.6, hub_d=25.0)   # od = pitch dia - 0.6
PULLEY_SMALL = dict(teeth=20, bore=5.0, width=16.0, hub_len=7.0, od=12.1, hub_d=16.0)
GT2_PITCH = 2.0
BELT_W = 6.0
BELT_LEN = 210.0               # GT2-6mm closed loop, 210 mm (105 teeth) - nominal
BELT_ALT_LEN = 220.0           # the motor slots also take a 220 mm loop (second source)
BELT_CENTER_FROM_HUB = 11.5    # belt centreline measured from the pulley hub face
PULLEY_GAP = 2.0               # pulley hub face to end-plate outer face
MOTOR = dict(size=42.3, length=40.0, boss_d=22.0, boss_h=2.0, shaft_d=5.0,
             shaft_len=24.0, hole_pitch=31.0)
# MOTOR_TENSION_TRAVEL: see fits.py
MOTOR_PLATE_T = 4.0            # bulkhead the motor bolts to (M3x8 into the motor)

# ---------------------------------------------------------------------------
# 7a1. FILAMENT PALETTE: <= 4 filaments, one colour per part (no multi-colour
# objects). Rename the slots when the colours are chosen; nothing else changes.
PALETTE = {
    "slot1_block":   dict(name="slot 1 (block)",   parts=("01_", "02_", "03_", "04_"), render="block"),
    "slot2_dark":    dict(name="slot 2 (dark)",    parts=("10_", "11_", "12_", "17_", "18_", "19_", "20_", "21_"), render="carbon"),
    "slot3_accent":  dict(name="slot 3 (accent)",  parts=("16_",), render="red"),
    "slot4_metal":   dict(name="slot 4 (metal)",   parts=("13_", "14_", "15_"), render="gold"),
    "hidden":        dict(name="any (hidden)",     parts=("05_", "06_", "07_", "08_", "09_"), render="crank"),
}

# 7a2. PRINTER (plates are laid out for this bed; verify against the spec page)
PRINTER = dict(name="Bambu Lab H2C", bed=(325.0, 320.0), z=325.0,   # single-nozzle mode
               dual_bed=(300.0, 320.0))                           # dual-nozzle mode (exhausts do not fit)

# 7b. DISPLAY BASE (Phase 2) - two halves joined at X=0, removable bottom panels
# ---------------------------------------------------------------------------
BASE_X = (-200.0, 200.0)
BASE_Y = (-140.0, 140.0)       # 280 wide: room for the exhaust tail pipes
BASE_TOP_Z = CASE_FLOOR_Z      # crankcase sits directly on the base top
BASE_H = 72.0
BASE_WALL = 4.0
BASE_SKIN = 5.0                # top skin thickness (carries the engine)
BASE_TOP_CHAMFER = 8.0
BASE_ENGINE_RECESS = 1.5       # crankcase sits in a shallow shadow-line pocket
PANEL_T = 3.0                  # bottom panel thickness (sits in a rabbet)
# Limited-edition plate (purchased H14, numbered 01-50) on the base front: an
# engraved 0.8 mm metal plate on adhesive transfer tape in a 1 mm recess with a
# 45 deg bevel all round (reads as a frame, prints cleanly on the vertical face).
# enabled=False gives a plain front.
EDITION_PLATE = dict(enabled=True, w=120.0, h=30.0, t=0.8, r=3.0, clear=PLATE_CLEAR, depth=1.0, tape=0.13)
BASE_JOINT_SCREWS = [(-131.0, -48.0), (131.0, -48.0), (-131.0, -92.0), (131.0, -92.0), (-50.0, -42.0), (50.0, -42.0)]  # (y, z)
BASE_JOINT_PEGS = [(-95.0, -42.0), (95.0, -42.0)]                                    # (y, z)
PANEL_SCREW_INSET = 12.0       # panel screws, from the inner corners
# Rear control panel (x = BASE_X[0]), from left to right seen from behind
CONTROLS_Z = -70.0
CONTROLS = [
    # (name, y, hole shape, size) - panel cut-outs for the purchased parts
    ("dc_jack",   75.0, "round", 11.0),     # 5.5x2.1 panel jack, 11 mm thread
    ("power",     30.0, "round", 20.2),     # 20 mm round illuminated rocker (KCD1 round: 20.2 hole)
    ("speed",    -20.0, "round", 7.2),      # 10k linear pot, M7 bushing
    ("start",    -75.0, "round", 16.2),     # 16 mm stainless momentary, ring LED
]
POT_TAB = dict(dy=-7.8, d=3.2)  # anti-rotation tab hole for the pot
CONTROL_PANEL_T = 2.5          # rear wall thinned here: DC jacks/rockers clamp panels <= 3 mm
# controller board (Phase 4): a 70 x 90 mm double-sided prototype board, hung
# components-down from 4 standoffs under the top skin of the rear half, clear
# of the backs of the rear-panel controls (w = along X, h = along Y)
PCB = dict(w=90.0, h=70.0, inset=2.5, x_center=-105.0, y_center=52.0, standoff=10.0)
HARNESS_HOLE = dict(x=-155.0, y=0.0, d=12.0)     # LED harness, hidden under the rear cover
TIE_ANCHOR_Y = -60.0           # row of cable-tie anchors along the base
TIE_ANCHOR_X = (-175.0, -115.0, -55.0, 5.0, 65.0)
# front drive cover (magnetic, tool-free belt access); the rear cover in
# Phase 3 uses the same outline and magnet pattern on the rear end plate
COVER_R = 31.0
COVER_WALL = 3.0
COVER_MAGNETS = [(0.0, 27.0), (27.0, -18.0), (-27.0, -18.0)]   # (y, z) on the end plate face
COVER_PILLAR_R = 4.0
SHADOW_GROOVE = dict(w=1.2, d=1.0, offset=1.0)   # outline groove around the engine footprint

# ---------------------------------------------------------------------------
# 7d. ELECTRONICS / FIRMWARE (Phase 4) - tools/gen_firmware_config.py turns
#     these + the crank geometry into firmware/v10_engine/engine_geometry.h
# ---------------------------------------------------------------------------
MOTOR_FULL_STEPS = 200         # 1.8 deg NEMA17
MICROSTEPS = 16                # TMC2209 interpolates each to 256 internally
ENGINE_RPM = (20.0, 120.0)     # crank speed range on the knob
IDLE_RPM = 20.0                # "idle mode" speed
HOMING_RPM = 15.0              # first turn that finds the hall magnet and parks cylinder 1 at TDC
CRANK_ACCEL_RPM_S = 15.0       # soft start / soft stop ramp (crank RPM per second)
AUTO_IDLE_MIN = 5              # no interaction for this long -> drop to idle
AUTO_SLEEP_MIN = 15            # ... and for this long -> soft stop and sleep
MOTOR_RUN_MA = 600             # RMS run current (17HS4401 is rated 1700 mA): cool motor
MOTOR_HOLD_FRACTION = 0.35     # holding current while stopped
HALL_PULSE_DEG = (2.0, 90.0)   # plausible magnet pulse width; outside -> ignored
SYNC_CORRECT_DEG = 3.0         # hall-vs-step-count error corrected silently below this
SYNC_FAULT_DEG = 8.0           # ... and a lost-step (stall / belt skip) fault above this
NO_HALL_REVS = 1.4             # crank revolutions without a magnet pass -> stall / jam fault
FLASH_DEG = 110.0              # firing flash length in crank degrees (power stroke glow)
LED_MAX_BRIGHTNESS = 170       # 0-255 cap (power + looks); 30 LEDs at this cap < 0.9 A

# ---------------------------------------------------------------------------
# 7c. PRINT SETTINGS / MATERIALS (used by the BOM generator)
# ---------------------------------------------------------------------------
LOAD_BEARING_WALLS = 4
LOAD_BEARING_INFILL = "25% gyroid"
# Production layer heights. The CAD uses them for the bridged hole steps
# (common.bridge_step: 2 layers per stage); tools/printcheck.py slices with them.
# Hidden parts (valley beam, end plates under their covers, base bottom panels)
# use 0.28 mm layers: same strength, ~30 % less printer time.
LAYER = dict(case=0.20, beam=0.28, bank=0.20, plate=0.28, crank=0.16, rod=0.12, piston=0.16,
             head=0.20, cosmetic=0.20, trumpet=0.12, exhaust=0.16, coil=0.16, base=0.20, panel=0.28)


# ===========================================================================
# DERIVED VALUES - do not edit below this line
# ===========================================================================
def _wrap(a):
    """Wrap an angle to (-180, 180]."""
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def cyl_bank(c):
    return "A" if c <= N_THROWS else "B"


def cyl_throw(c):
    """Throw index 0..4 for cylinder c (1..10). Cylinder c and c+5 share a throw."""
    return (c - 1) % N_THROWS


def bank_angle(bank):
    return BANK_A_ANGLE if bank == "A" else BANK_B_ANGLE


# Crank angle (0..720) at which each cylinder fires. Cylinder 1 fires at 0.
FIRE_ANGLE = {c: i * FIRING_INTERVAL for i, c in enumerate(FIRING_ORDER)}

# Crankpin angle for every cylinder: TDC happens when pin angle + crank angle
# equals the bank angle, so pin = bank - fire (mod 360).
PIN_ANGLE = {c: _wrap(bank_angle(cyl_bank(c)) - FIRE_ANGLE[c]) for c in range(1, N_CYL + 1)}

# Per throw: journal A (bank A rod, front) and journal B (bank B rod, rear)
THROW_PIN_A = [PIN_ANGLE[k + 1] for k in range(N_THROWS)]
THROW_PIN_B = [PIN_ANGLE[k + 1 + N_THROWS] for k in range(N_THROWS)]
SPLIT_ANGLE = _wrap(THROW_PIN_B[0] - THROW_PIN_A[0])     # 18 deg for 90 deg V / 72 deg firing
SPLIT_DIST = 2 * CRANK_R * math.sin(math.radians(abs(SPLIT_ANGLE)) / 2)

# Crank segment k joins throw k (pin B, front face) to throw k+1 (pin A, rear face)
SEGMENT_DELTA = [_wrap(THROW_PIN_A[k + 1] - THROW_PIN_B[k]) % 360.0 for k in range(N_THROWS - 1)]
SEGMENT_TYPES = sorted(set(round(d, 6) for d in SEGMENT_DELTA))

# Axial positions (X) of crank features, front half (mirror for rear)
WEB_FACE_X = THROW_X[0] + THROW_INNER / 2                 # front face of throw 1
END_WEB_OUTER_X = WEB_FACE_X + END_WEB_T
FLANGE_OUTER_X = END_WEB_OUTER_X + SHAFT_FLANGE_T

# magnet position on the end web, relative to that web's crankpin, chosen so the
# magnet passes the hall sensor exactly when cylinder 1 is at firing TDC
HALL_MAGNET_WEB_ANGLE = (HALL_SENSOR_ANGLE - THROW_PIN_A[0]) % 360.0   # front web magnet at the sensor angle at 0 deg

BANK_A_CYL_X = [x + ROD_X_OFFSET for x in THROW_X]
BANK_B_CYL_X = [x - ROD_X_OFFSET for x in THROW_X]
BLOCK_X_MIN = BANK_A_CYL_X[-1] - BLOCK_END_MARGIN        # bank A block, local X range
BLOCK_X_MAX = BANK_A_CYL_X[0] + BLOCK_END_MARGIN
CASE_HALF_LEN = max(abs(BLOCK_X_MIN), abs(BLOCK_X_MAX))  # crankcase is symmetric
END_PLATE_INNER_X = CASE_HALF_LEN - END_PLATE_SPIGOT
END_PLATE_OUTER_X = CASE_HALF_LEN + END_PLATE_FLANGE_T
# 608 sits against a lip on the OUTSIDE of each end plate (pressed in from
# inside). Front and rear shaft shoulders then trap the crank between the two
# bearings; the pulley + spacer clamp the FRONT inner ring (locating bearing),
# the rear inner ring floats by AXIAL_FLOAT, so crank-length tolerance can
# never preload the bearings.
BEARING_INNER_X = END_PLATE_OUTER_X - BEARING_LIP_T - BEARING_608["w"]
BEARING_OUTER_X = BEARING_INNER_X + BEARING_608["w"]
SHAFT_SHOULDER_L = BEARING_INNER_X - FLANGE_OUTER_X - AXIAL_FLOAT / 2
# Clamping the front inner ring pulls the crank forward until the front shaft
# shoulder touches it: the assembled crank sits CRANK_DX ahead of the nominal
# throw positions (the rods follow the crank, the pistons follow their rails;
# PISTON_BOSS_GAP takes up the difference). The rear gap is then AXIAL_FLOAT.
CRANK_DX = AXIAL_FLOAT / 2
# Hall sensor under the rear end web. The rear web is the front web turned 180
# deg about Z (crank angle psi -> -psi) and set to throw 5's pin B, so its
# magnet passes the sensor at crank angle HALL_PHI (the firmware subtracts it).
HALL_X = -(WEB_FACE_X + END_WEB_T / 2) + CRANK_DX if HALL_SENSOR_END == "rear" else WEB_FACE_X + END_WEB_T / 2 + CRANK_DX
HALL_PHI = ((HALL_SENSOR_ANGLE - ((-HALL_MAGNET_WEB_ANGLE + THROW_PIN_B[-1]) % 360.0)) % 360.0
            if HALL_SENSOR_END == "rear" else 0.0)
PULLEY_HUB_X = END_PLATE_OUTER_X + PULLEY_GAP        # both pulleys: hub face towards the engine
SPACER_T = PULLEY_HUB_X - BEARING_OUTER_X            # M04 spacer: inner ring -> pulley hub
SHAFT_END_X = PULLEY_HUB_X + 16.0 + 0.5               # shaft ends just past a 16 mm pulley
SHAFT_JOURNAL_L = SHAFT_END_X - (FLANGE_OUTER_X + SHAFT_SHOULDER_L)

# The cylinder head is located on the deck by the 5 guide-rail tops. RAIL_OFFSET
# is not 0, so the head only fits one way round.
RAIL_TOP = DECK_DIST + RAIL_HEAD_ENGAGE
RAIL_BOTTOM = FACE_DIST - RAIL_HOLE_DEPTH_CASE
RAIL_LEN = RAIL_TOP - RAIL_BOTTOM

# --- drive geometry (derived) ---
PITCH_D_BIG = PULLEY_BIG["teeth"] * GT2_PITCH / math.pi
PITCH_D_SMALL = PULLEY_SMALL["teeth"] * GT2_PITCH / math.pi
DRIVE_RATIO = PULLEY_BIG["teeth"] / PULLEY_SMALL["teeth"]


def _belt_centre(L, d1, d2):
    c = L / 4
    for _ in range(60):
        c = (L - math.pi * (d1 + d2) / 2 - (d1 - d2) ** 2 / (4 * c)) / 2
    return c


BELT_CENTRE = _belt_centre(BELT_LEN, PITCH_D_BIG, PITCH_D_SMALL)
BELT_X = PULLEY_HUB_X + BELT_CENTER_FROM_HUB
MOTOR_Z = -BELT_CENTRE                             # motor shaft axis (y = 0)
MOTOR_Z_ALT = -_belt_centre(BELT_ALT_LEN, PITCH_D_BIG, PITCH_D_SMALL)
MOTOR_SLOT_TOP = MOTOR_Z + MOTOR_TENSION_TRAVEL        # motor axis travel in the bulkhead slots
MOTOR_SLOT_BOTTOM = MOTOR_Z_ALT - MOTOR_TENSION_TRAVEL
MOTOR_PLATE_X1 = PULLEY_HUB_X - 1.0                # front face of the motor bulkhead
MOTOR_FACE_X = MOTOR_PLATE_X1 - MOTOR_PLATE_T      # motor mounting face
BASE_BOTTOM_Z = BASE_TOP_Z - BASE_H
COVER_X0 = END_PLATE_OUTER_X
COVER_X1 = max(PULLEY_HUB_X + PULLEY_MAX_W, SHAFT_END_X) + 1.5 + COVER_WALL


def hole(nominal, fit=None):
    """Printed hole diameter for a nominal size and a named fit."""
    return nominal + HOLE_COMP + (FIT[fit] if fit else 0.0)


def piston_travel(crank_deg, c):
    """Wrist-pin distance from the crank axis for cylinder c at a crank angle."""
    beta = math.radians(PIN_ANGLE[c] + crank_deg - bank_angle(cyl_bank(c)))
    r, L = CRANK_R, ROD_LENGTH
    return r * math.cos(beta) + math.sqrt(L * L - (r * math.sin(beta)) ** 2)


# ---------------------------------------------------------------------------
# SELF CHECKS - run "python config.py" to see the summary
# ---------------------------------------------------------------------------
def self_check(verbose=True):
    problems = []
    # every throw must have the same split so all crankpins are identical
    for k in range(N_THROWS):
        s = _wrap(THROW_PIN_B[k] - THROW_PIN_A[k])
        if abs(s - SPLIT_ANGLE) > 1e-6:
            problems.append(f"throw {k+1} split {s} != {SPLIT_ANGLE}")
    # even firing: TDC of consecutive cylinders in the firing order 72 deg apart
    for i, c in enumerate(FIRING_ORDER):
        nxt = FIRING_ORDER[(i + 1) % N_CYL]
        tdc_c = _wrap(bank_angle(cyl_bank(c)) - PIN_ANGLE[c]) % 360
        tdc_n = _wrap(bank_angle(cyl_bank(nxt)) - PIN_ANGLE[nxt]) % 360
        gap = (tdc_n - tdc_c) % 360
        if abs(gap - FIRING_INTERVAL % 360) > 1e-6 and abs(gap - (FIRING_INTERVAL + 360) % 360) > 1e-6:
            problems.append(f"TDC gap {c}->{nxt} = {gap}")
    # crank sweep must clear the piston skirt at BDC and the case interior
    skirt_bdc = ROD_LENGTH - CRANK_R - PISTON_PIN_TO_SKIRT
    if skirt_bdc - FACE_DIST < 1.0:
        problems.append(f"piston skirt at BDC ({skirt_bdc}) too close to face ({FACE_DIST})")
    if WEB_CW_R + 3 > CASE_INTERIOR_R:
        problems.append("counterweight too close to crankcase interior")
    if CRANK_R + ROD_BIG_END_OD / 2 + 3 > CASE_INTERIOR_R:
        problems.append("big end sweep too close to crankcase interior")
    if WEB_HUB_R < 0 or PIN_SHOULDER_D >= 8.0:
        problems.append("pin shoulder would touch 686 shield")
    if SHAFT_SHOULDER_L < 1.0:
        problems.append(f"main shaft shoulder too short ({SHAFT_SHOULDER_L:.2f})")
    if BORE_DIA + 2 * 2.5 > CYL_PITCH + 10:
        problems.append("bore too big for pitch")
    if CASE_HALF_LEN * 2 > 290:
        problems.append("crankcase longer than 290 mm")
    motor_top = MOTOR_SLOT_TOP + MOTOR["size"] / 2
    if motor_top > BASE_TOP_Z - BASE_SKIN - 1.5:
        problems.append(f"motor ({motor_top:.1f}) too close to base top skin")
    if MOTOR_SLOT_BOTTOM - MOTOR["size"] / 2 < BASE_BOTTOM_Z + PANEL_T + 3:
        problems.append("motor too close to bottom panel")
    if MOTOR_FACE_X + MOTOR["shaft_len"] < PULLEY_HUB_X + PULLEY_SMALL["width"]:
        problems.append("motor shaft too short for the small pulley")
    if SHAFT_END_X < PULLEY_HUB_X + PULLEY_BIG["width"]:
        problems.append("main shaft too short for the big pulley")
    if PISTON_BOSS_GAP < CRANK_DX + 0.5:
        problems.append("piston boss gap too small for the crank's assembled position + print tolerance")
    if SPACER_T < BEARING_LIP_T + 0.5:
        problems.append("pulley spacer shorter than the bearing lip - pulley hub would rub the end plate")
    if BASE_X[1] - BASE_X[0] > 2 * 300 or (BASE_X[1] - BASE_X[0]) / 2 > 300:
        problems.append("base half longer than 300 mm")
    ep = EDITION_PLATE
    if ep["enabled"]:
        if ep["h"] + 2 * (ep["clear"] + ep["depth"]) > BASE_H - BASE_TOP_CHAMFER - 2 * 12.0:
            problems.append("edition plate too tall for the flat of the base front")
        if ep["w"] + 2 * (ep["clear"] + ep["depth"]) > (BASE_Y[1] - BASE_Y[0]) - 2 * 40.0:
            problems.append("edition plate too wide for the base front")
        if ep["depth"] > BASE_WALL - 2.5 or ep["tape"] + ep["t"] > ep["depth"]:
            problems.append("edition plate recess: wall too thin or plate stands proud")
    if verbose:
        print("V10 config summary")
        print(f"  split crankpin angle ......... {SPLIT_ANGLE:+.1f} deg (offset {SPLIT_DIST:.2f} mm)")
        print(f"  bank offset (A ahead of B) ... {BANK_OFFSET:.2f} mm")
        print(f"  throw pin A angles ........... {[round(a,1) for a in THROW_PIN_A]}")
        print(f"  throw pin B angles ........... {[round(a,1) for a in THROW_PIN_B]}")
        print(f"  segment types (deg) .......... {SEGMENT_TYPES}  per segment {[round(d,1) for d in SEGMENT_DELTA]}")
        print(f"  crankcase length ............. {2*CASE_HALF_LEN:.1f} mm")
        print(f"  crankpin length .............. {PIN_LEN:.2f} mm")
        print(f"  main shaft shoulder length ... {SHAFT_SHOULDER_L:.2f} mm")
        print(f"  guide rail length ............ {RAIL_LEN:.1f} mm")
        print(f"  deck height .................. {DECK_DIST:.1f} mm from crank axis")
        print(f"  fire angles .................. {FIRE_ANGLE}")
        print(f"  drive ........................ {DRIVE_RATIO:.0f}:1, belt {BELT_LEN:.0f} mm, centres {BELT_CENTRE:.2f} mm, belt plane x={BELT_X:.1f}")
        print(f"  motor ........................ axis z={MOTOR_Z:.1f} ({BELT_ALT_LEN:.0f} mm belt: {MOTOR_Z_ALT:.1f}), "
              f"slots {MOTOR_SLOT_TOP:.1f}..{MOTOR_SLOT_BOTTOM:.1f}, face x={MOTOR_FACE_X:.1f}")
        print("  self-check:", "OK" if not problems else "PROBLEMS")
        for p in problems:
            print("   -", p)
    return problems


if __name__ == "__main__":
    self_check()
