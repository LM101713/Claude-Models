"""
MotionLoop ML-02 parameters. Every dimension in millimetres.

Assembly frame
    X  slide direction (left slider at -X, right slider at +X)
    Y  crank axis (the handle is on the -Y side)
    Z  up; the plinth's bottom face is Z = 0

The Y stack across the crank, from the handle side to the cap side:

    handle | tower B | cheek B | rod B | WHEEL | rod A | cheek A | tower A | cap
                          (y < 0)                      (y > 0)

Rod A drives the LEFT slider, rod B the RIGHT slider. Each rod plane contains exactly one
crank-fixed object, its own crank pin, which is what makes the layout collision-free (see
README section 2).
"""

import math


class P:
    # ---- kinematics -------------------------------------------------------------------
    CRANK_R = 8.0  # crank radius r (stroke = 2r = 16 mm)
    ROD_L = 30.0  # connecting-rod length, centre to centre (l/r = 3.75)
    AXLE_Z = 21.0  # crank axis height = slider pin height (in-line slider-crank)
    PHASE_DEG = 180.0  # pin B relative to pin A: 180 = MIRROR (default), 0 = SHUTTLE

    # ---- printed-fit clearances (0.4 mm nozzle, PETG) ----------------------------------
    RUN_DIA = 0.50  # diametral clearance, pin running in a bore (0.25 per side)
    AXIAL = 0.30  # axial gap between faces that rotate or slide against each other
    SLIDE = 0.20  # slider neck to groove wall, per side
    SLIDE_Z = 0.15  # slider underside above the plinth top (modelled mid-play)
    DOVE = 0.15  # normal gap, slider dovetail flank to groove flank
    KEY = 0.10  # D-spigot to D-hole, per side (axially captured, not a press fit)
    PRESS = 0.00  # pin shank vs press hole, nominal (FDM holes print ~0.1 undersize)
    HEX_PRESS = 0.00  # hex shaft vs hex socket across flats, nominal (as above)

    # ---- the Y stack (half-widths measured from the wheel mid-plane y = 0) ---------------
    WHEEL_T = 6.0
    ROD_T = 4.5
    CHEEK_T = 4.0
    THRUST_RING_H = 0.4  # raised thrust boss on each tower's inner face
    THRUST_RING_R = (3.4, 5.5)
    TOWER_OUT = 19.5  # tower outer face |y|

    # ---- crank wheel and cheeks ---------------------------------------------------------
    WHEEL_R = 15.5
    WHEEL_EDGE = 0.7  # 45-degree edge chamfer
    WHEEL_INDEX = (11.8, 14.4, 0.8, 0.4)  # index groove: r0, r1, width, depth
    CHEEK_R = 13.0
    CHEEK_EDGE = 0.5
    PIN_D = 6.0  # crank pin bearing diameter
    PIN_ROOT_F = 0.5  # crank pin root fillet (fits the rod bore chamfer)
    SPIGOT_D = 4.4  # D-spigot that keys the crank pin into the wheel
    SPIGOT_FLAT = 1.5  # distance from spigot axis to its flat
    SPIGOT_L = 2.8
    SPIGOT_HOLE_DEPTH = 3.0

    # ---- shafts --------------------------------------------------------------------------
    JOURNAL_D = 6.0
    HEX_AF = 4.5  # hex drive across flats (smallest section in the torque path)
    HEX_L = 2.8  # hex engagement in the cheek (leaves a 1.2 mm socket floor)
    BORE_D = 6.4  # tower bearing bore (teardrop roof for printing)

    # ---- connecting rod -----------------------------------------------------------------
    ROD_BIG_R = 6.0  # outer radius at the big end
    ROD_SMALL_R = 5.0
    ROD_SHANK_HW = (3.0, 2.5)  # shank half-width at big / small end
    ROD_FILLET = 4.0  # concave fillet, shank to boss
    ROD_EDGE = 0.45  # edge chamfer on both faces
    WRIST_D = 5.0  # wrist pin diameter

    # ---- plinth (frame) ----------------------------------------------------------------------
    L = 110.0
    W = 42.0
    CORNER_R = 13.0
    CORNER_N = 4.0  # superellipse exponent of the plan corners
    TOP_R = 2.0  # top edge radius
    FOOT_CHAMFER = 0.8  # 45-degree bottom chamfer (elephant's foot)
    PIT_X = 19.5  # crank pit half-length (rod sweep needs >= 18.0)
    PIT_FLOOR = 3.0
    PIT_EDGE = 0.6
    TOWER_HW = 7.0  # tower half-width in X; its top is a radius about the axle
    TICK_PITCH = 2.0  # engraved travel scale

    # ---- slider and dovetail ---------------------------------------------------------------
    SLIDER_Y = (-3.0, 7.0)  # RIGHT slider's |y| extent (the left one is its 180-degree copy)
    SLIDER_U = (-5.0, 14.0)  # extent along the slide axis from the wrist pin (+ = outward)
    SLIDER_TOP = 27.0  # absolute Z of the slider top (AXLE_Z + 6)
    SLIDER_CORNER = (4.5, 1.0)  # profile corner radii: top, bottom
    SLIDER_EDGE = 0.6
    KEY_U = (-2.0, 13.5)  # dovetail key extent along the slide axis
    GROOVE_NECK_HW = 2.2
    GROOVE_NECK_H = 1.2
    GROOVE_FLARE_HW = 4.5
    GROOVE_FLOOR_GAP = 0.3

    # ---- wrist / knob pin (one part, three used) -----------------------------------------
    PIN_HEAD_D = 8.5
    PIN_HEAD_T = 1.6
    PIN_SHANK_L = 12.6

    # ---- handle and cap -------------------------------------------------------------------------
    HANDLE_R = 13.0  # axle to knob axis
    ARM_T = 5.1  # leaves a 1.3 mm floor under the blind knob-pin hole
    ARM_HUB_R = 6.5
    ARM_TIP_R = 5.5
    HUB_SPACER_D = 10.0
    KNOB_OD = 9.0
    KNOB_L = 8.5
    CAP_D = 12.0
    CAP_T = 2.4

    SEG = 64  # circle resolution


def derived(p=P):
    d = {}
    d["Y_WHEEL"] = p.WHEEL_T / 2
    d["Y_ROD0"] = d["Y_WHEEL"] + p.AXIAL
    d["Y_ROD1"] = d["Y_ROD0"] + p.ROD_T
    d["Y_CHEEK0"] = d["Y_ROD1"] + p.AXIAL
    d["Y_CHEEK1"] = d["Y_CHEEK0"] + p.CHEEK_T
    d["Y_BOSS"] = d["Y_CHEEK1"] + p.AXIAL  # thrust boss face on the tower
    d["Y_TOWER0"] = d["Y_BOSS"] + p.THRUST_RING_H
    d["Y_TOWER1"] = p.TOWER_OUT
    d["Y_CAP0"] = d["Y_TOWER1"] + p.AXIAL
    d["Y_HEX_TIP"] = d["Y_CHEEK1"] - p.HEX_L
    d["PLINTH_TOP"] = p.AXLE_Z - 7.5
    d["TOWER_TOP"] = p.AXLE_Z + p.TOWER_HW
    # handle: the arm sits outside the plinth side
    d["Y_ARM0"] = p.W / 2 + 0.8
    d["Y_ARM1"] = d["Y_ARM0"] + p.ARM_T
    d["Y_SPACER0"] = d["Y_TOWER1"] + p.AXIAL
    # slider
    d["SLIDER_Z0"] = d["PLINTH_TOP"] + p.SLIDE_Z
    d["SLIDER_YC"] = sum(p.SLIDER_Y) / 2  # right slider; left is -this
    # wrist pin: head just outboard of the rod
    d["Y_WRIST_HEAD0"] = d["Y_ROD1"] + p.AXIAL
    d["PIN_STROKE"] = (p.ROD_L - p.CRANK_R, p.ROD_L + p.CRANK_R)
    d["BETA_MAX_DEG"] = math.degrees(math.asin(p.CRANK_R / p.ROD_L))
    return d


D = derived()


def slider_x(theta, side, p=P):
    """Wrist-pin X for crank angle theta (rad). side=+1 right slider (pin B), -1 left (pin A).
    Pin A is at angle theta; pin B at theta + PHASE."""
    phase = 0.0 if side < 0 else math.radians(p.PHASE_DEG)
    a = theta + phase
    px, pz = p.CRANK_R * math.cos(a), p.CRANK_R * math.sin(a)
    return px + side * math.sqrt(p.ROD_L ** 2 - pz ** 2)


def pin_xz(theta, side, p=P):
    phase = 0.0 if side < 0 else math.radians(p.PHASE_DEG)
    a = theta + phase
    return p.CRANK_R * math.cos(a), p.AXLE_Z + p.CRANK_R * math.sin(a)


def rod_angle(theta, side, p=P):
    """Angle (rad, about +Y, as atan2(dz, dx)) of the vector big end -> small end."""
    px, pz = pin_xz(theta, side, p)
    sx = slider_x(theta, side, p)
    return math.atan2(p.AXLE_Z - pz, sx - px)
