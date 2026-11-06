"""
HF-04 HOLDFAST: every dimension, clearance and derived mechanism value.

Frames
------
USE frame (how it hangs on the wall), millimetres:
    X  horizontal, along the wall (the handle channel is centred on X = 0)
    Y  out of the wall (the wall surface is Y = 0)
    Z  up (Z = 0 is the vertical centre of the base)

The handle hangs vertically in the channel. Each roller sits in a pocket beside the channel,
on a ramp that leans DELTA degrees from vertical so the gap between ramp and handle narrows
downward. A roller that is dragged down by the handle therefore wedges harder.

Left pocket (x < 0) is defined below; the right pocket is its mirror image (x -> -x).
"""

import math

import numpy as np


class P:
    # ---- the wedge (the number that decides whether it holds) ---------------------------
    DELTA_DEG = 16.0  # ramp angle from vertical. Friction needed = tan(DELTA/2) = 0.141

    # ---- handle range -----------------------------------------------------------------
    D_RATED = (19.0, 32.0)  # rated handle diameters (mm)
    D_CLOSED = 16.0  # rollers rest at this gap with no handle (bottom stop)
    D_TOP = 35.0  # gap when the rollers reach the top stop (= keyhole position)

    # ---- roller -------------------------------------------------------------------------
    R_ROLL = 12.0  # roller radius
    T_ROLL = 20.0  # roller thickness (along Y)
    ROLL_CH_FRONT = 2.0  # 45 deg lead-in chamfer on the front rim (bed side when printed)
    ROLL_CH_BACK = 0.6  # chamfer on the back rim
    INDEX_W = 1.2  # engraved index line on the front face: width, depth, radial extent
    INDEX_D = 0.6
    INDEX_R = (3.5, 9.5)
    GRIP_N = 36  # grip roller: number of shallow ridges
    GRIP_DEPTH = 0.40  # ridge depth (crests stay at R_ROLL)

    # ---- stub (on the roller axis) and keyhole T-slot (in the back plate) ----------------
    NECK_R = 3.0
    HEAD_R = 5.0
    HEAD_CH = 0.4
    G_BACK = 0.3  # axial gap, roller back face to back-plate face
    Y_CONE0 = 5.5  # Y where the head cone starts (neck ends): 0.5 mm axial gap under the lip
    Y_HEAD_END = 3.0  # Y of the head's end face
    # back plate
    BACK_T = 7.0  # back plate thickness: its front face (pocket floor / handle rest) at Y = 7
    LIP_SLOT_HALF = 3.6  # slot half-width through the lip (neck clearance 0.6 per side)
    Y_LIP_UNDER = 5.4  # underside of the lip (lip is 1.6 thick)
    CAV_HALF = 5.7  # undercut cavity half-width (head clearance 0.7 per side)
    Y_CAV_FLOOR = 2.2  # cavity floor (2.2 mm of plate behind it)
    KEY_R = 5.8  # keyhole radius (head clearance 0.8)
    SLOT_LEAD = 0.4  # 45 deg chamfer on the slot mouth

    # ---- pocket and housings ------------------------------------------------------------
    C_POCKET = 1.0  # roller to pocket wall clearance (everywhere except the ramp)
    X_CH = 18.0  # channel half-width at the housings (36 mm channel for <= 32 mm handles)
    Y_FRONT = 28.0  # housing front face
    W_OUTER = 6.0  # solid wall behind the ramp
    W_TOP = 4.5  # wall above / below the pocket
    R_CONVEX = 4.0  # plan-view rounding of convex corners
    R_CONCAVE = 2.5  # plan-view rounding of concave corners
    R_OUTLINE = 7.0  # rounding of the base's outer corners
    CH_FRONT = 1.2  # 45 deg chamfer round every front edge
    CH_BACK = 0.6  # 45 deg chamfer round the wall-side edge (elephant-foot relief)

    # ---- mounting -------------------------------------------------------------------------
    SCREW_HOLE_D = 4.6  # clearance for 3.5-4.2 mm (#6-#8) countersunk wood screws
    SCREW_CSK_D = 9.0  # 90 deg countersink diameter at the plate face
    SCREW_INSET = 8.0  # screw centres this far inside the top / bottom edge

    # ---- tolerance variants ----------------------------------------------------------------
    LOOSE_NECK_DR = -0.3  # "Loose" roller: neck and head radii smaller by this
    LOOSE_AXIAL = 0.3  # ... and the neck longer (more axial play)

    # ---- mesh resolution ---------------------------------------------------------------------
    SEG = 192  # segments on a full circle

    # ---- materials (for mass estimates) --------------------------------------------------------
    RHO = {"PLA": 1.24, "PETG": 1.27}  # g/cm3


# =====================================================================================
# derived wedge geometry
# =====================================================================================


def unit(a):
    return np.array([math.cos(a), math.sin(a)])


class D:
    """Derived values for the LEFT pocket, in the use-frame XZ plane (x, z)."""

    delta = math.radians(P.DELTA_DEG)
    half = delta / 2.0
    mu_req = math.tan(half)  # friction coefficient the wedge asks for (both contacts)
    # u: unit vector UP the ramp (leans away from the channel as it rises)
    u = np.array([-math.sin(delta), math.cos(delta)])
    # n: ramp normal pointing into the pocket (toward the channel, slightly up)
    n = np.array([math.cos(delta), math.sin(delta)])

    rho_closed = P.D_CLOSED / 2.0
    rho_top = P.D_TOP / 2.0
    s_key = (rho_top - rho_closed) / math.sin(delta)  # roller travel, bottom stop -> keyhole
    dz_travel = s_key * math.cos(delta)
    z0 = -dz_travel / 2.0  # roller-centre height at the bottom stop (pocket centred on Z=0)
    C0 = np.array([-rho_closed - P.R_ROLL, z0])  # roller centre at the bottom stop
    P0 = C0 - P.R_ROLL * n  # ramp contact at the bottom stop

    z_top = C0[1] + dz_travel + P.R_ROLL + P.C_POCKET + P.W_TOP
    z_bot = C0[1] - P.R_ROLL - P.C_POCKET - P.W_TOP


def centre(s):
    """Left roller centre (x, z) at travel s (s = 0: bottom stop, s = s_key: keyhole)."""
    return D.C0 + s * D.u


def s_of_diameter(dia):
    """Travel at which a handle of this diameter is gripped (rollers touching it)."""
    return (dia / 2.0 - D.rho_closed) / math.sin(D.delta)


def diameter_of_s(s):
    return 2.0 * (D.rho_closed + s * math.sin(D.delta))


def roll_angle(s):
    """Roller rotation (deg) from the bottom stop, rolling without slip on the ramp."""
    return math.degrees(s / P.R_ROLL)


def grip_point(dia):
    """Use-frame contact point of the left roller on a handle of this diameter."""
    s = s_of_diameter(dia)
    c = centre(s)
    return np.array([c[0] + P.R_ROLL, 7.0 + dia / 2.0, c[1]])  # (x, y, z): equator of handle


def kinematics_table(dias=(16, 19, 22, 25, 28, 32, 35)):
    rows = []
    for d in dias:
        s = s_of_diameter(d)
        c = centre(s)
        rows.append(
            dict(
                handle_d=d,
                travel_s=s,
                roller_centre_x=c[0],
                roller_centre_z=c[1],
                grip_height_z=c[1],
                roller_turn_deg=roll_angle(s),
                margin_to_bottom_stop=s,
                margin_to_top_stop=D.s_key - s,
            )
        )
    return rows


def summary():
    return dict(
        delta_deg=P.DELTA_DEG,
        mu_required=D.mu_req,
        travel_total=D.s_key,
        travel_vertical=D.dz_travel,
        z_top=D.z_top,
        z_bot=D.z_bot,
        C0=D.C0.tolist(),
        P0=D.P0.tolist(),
    )
