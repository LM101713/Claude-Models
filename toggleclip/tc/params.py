"""
Every dimension of the TC-03 ToggleClip, in mm, in the USE frame:

    x  along the clip, hinge pin H at x = 0, nose at +x
    z  up; z = 0 is the flat clamp face of the upper jaw
    y  across the clip (the bag passes through the slot along y)

The mechanism is planar (side view = XZ) and every part is a stack of flat layers along y, so
each part is described by 2D profiles in XZ plus the y-band each profile occupies.
"""

import math


class P:
    # ---------------------------------------------------------------- fits (0.4 mm nozzle)
    AX = 0.35          # axial gap between faces that slide past each other (each side)
    RUN_V = 0.20       # radial running clearance, round hole printed vertically
    RUN_T = 0.25       # radial running clearance, teardrop hole printed horizontally
    RIB = 0.12         # crush-rib interference (radial) for press-fitted pins / pegs
    PIN_D = 5.0        # every pin and peg is 5 mm
    SEG = 72           # circle resolution

    # ---------------------------------------------------------------- y stack (half widths)
    BLADE_HW = 6.0     # lower jaw ("blade"): 12 wide, constant (it prints on its side)
    LEVER_BLADE_HW = 3.0   # lever web that sits between the nose cheeks
    CHEEK_IN = 3.35        # nose cheeks of the upper jaw: |y| 3.35 .. 6.0
    CHEEK_OUT = 6.0
    PLATE_IN = 6.35        # bail plates: |y| 6.35 .. 9.0
    PLATE_OUT = 9.0
    BODY_HW = 9.0          # upper jaw body and lever arm: 18 wide

    # ---------------------------------------------------------------- side view
    UJ_H = 8.0             # upper jaw height (z 0 .. 8), the stiff member
    LEVER_T = 5.0          # lever arm thickness (z 8 .. 13 when locked, lying on the jaw)
    # blade = floating pressure BAR (top, carries the clamp face) + arched BOW spring
    # (bottom, carries the two pins), joined by ONE central bridge; a lens-shaped slot
    # separates them everywhere else
    BAR_T = 5.5
    SLOT = 0.8             # bar-to-bow slot next to the bridge (prints open with a 0.4 nozzle)
    BOW_T = 4.0            # STANDARD blade (PLA). FIRM blade (PETG): 4.6
    BOW_T_FIRM = 4.6
    BOW_RISE = 3.4         # the bow arches this far down to the pins: room for 3.3 mm of travel
    BAR_X = (7.0, 109.0)   # the bar (= the clamp zone)
    BRIDGES = (58.5,)      # one central bridge: the bow's slope is zero there
    BRIDGE_W = 8.0
    RIDGE_H, RIDGE_TOP, RIDGE_BASE = 1.2, 2.0, 4.4    # 45 deg trapezoid ridge on the bar
    GROOVE_GAP = 0.45      # normal clearance ridge-to-groove (the bag goes in here)
    PRELOAD = 1.0          # bar face above z = 0 at lock with nominal pin clearances taken up
    BAR_CROWN = 0.0
    XP = 118.0             # lever pivot x (and K)
    E_ARM = 8.5            # P -> Q, the toggle crank radius
    OVER = 10.0            # over-centre angle at the lock stop (deg)
    BOSS_R = 4.5           # boss radius round every 5 mm pin (wall 2.0)
    CHEEK_R = 4.15         # nose-cheek disc round P (must clear the Q pegs)
    PK = 9.0               # P -> K at lock: CHEEK_R + BOSS_R + AX
    LEVER_REAR = 48.0      # x of the lever's rear (thumb) end
    # click detent at the thumb end: a peg under the lever passes between two flexure fingers
    PEG_X = 52.0           # peg centre x
    PEG_HW = 1.3           # peg half-width (y); barbs reach 1.8
    BARB = 0.5
    FINGER_GAP = 0.75      # finger face to peg body (the barb tip clears it by 0.25)
    BUMP = 0.4             # finger bump: overlap with the barb per side
    FINGER_W, FINGER_L = 1.8, 18.0

    # ---------------------------------------------------------------- materials (printed, in-plane)
    E_PLA = 3000.0         # MPa, conservative for in-plane PLA perimeters
    E_PETG = 1900.0


SLOP_CHAIN = 2 * P.RUN_T + P.RUN_V      # pin clearances taken up in the toggle chain (P, Q, K)
SLOP_H = P.RUN_T                        # hinge pin clearance


def bar_face(x, pre=None, L=None):
    """Height of the bar's clamp face above z = 0 at lock in the CAD (rigid parts, zero pin
    clearance): PRELOAD plus the sag the nominal pin clearances will cause, so that with
    nominal clearances the face is level and PRELOAD above the upper jaw everywhere."""
    pre = P.PRELOAD if pre is None else pre
    L = P.XP if L is None else L
    x0, x1 = P.BAR_X
    xi = (x - x0) / (x1 - x0)
    crown = P.BAR_CROWN * 4 * xi * (1 - xi)
    return pre + crown + SLOP_H + (SLOP_CHAIN - SLOP_H) * x / L


def bow_ratio(x, L=None):
    """Deflected shape of a centre-loaded pinned beam, 0 at the pins and 1 at mid-span."""
    L = P.XP if L is None else L
    s = min(x, L - x) / L
    return max(0.0, s * (3 - 4 * s * s))


def derived():
    d = {}
    xp = P.XP
    xm = P.BRIDGES[0]
    # pins at the ends of the arched bow; the bow's top is SLOT below the (free) bar at mid-span
    zk = bar_face(xm) - P.BAR_T - P.SLOT - P.BOW_T / 2 - P.BOW_RISE
    zp = zk + P.PK                      # P straight above K at dead centre
    d["H"] = (0.0, zk)
    d["P"] = (xp, zp)
    d["K"] = (xp, zk)
    a = math.radians(P.OVER)
    d["Q"] = (xp - P.E_ARM * math.sin(a), zp + P.E_ARM * math.cos(a))
    # the CAD pose is the LOCKED pose: lever on its stop, Q 10 deg past the P-K line
    d["L_LINK"] = math.hypot(d["Q"][0] - xp, d["Q"][1] - zk)
    return d


D = derived()
