"""T11 fit coupons for the two press fits the Blender skin introduced (decision
D48): the intake lid / base tongue and the 14 mm throttle-body spigot socket.
Straight 40 mm sections with the real wall, tongue, clearance and crush
numbers from params.json - the curved envelope does not change the fit class.
Print in PLA with the C1 plate; T10 (a real primary) also presses into T11c."""
from .. import bpyutil as U
from .. import fitcut as F
from ..params import P

L = 40.0                  # coupon length along x


def t11_tongue_lid():
    """Lid wall section: W thick, 12 tall, with a 6 mm lip so it stands and can be pulled off."""
    W = P.INTAKE["wall"]
    piece = U.box("T11_tongue_lid", 0.0, L, 0.0, W, 0.0, 12.0)
    U.boolean(piece, U.box("lip", 0.0, L, 0.0, W + 6.0, 12.0, 15.0), "UNION")
    U.shade(piece)
    return piece


def t11b_tongue_base():
    """Base wall section with the tongue: wall W thick, tongue (tongue_w) standing tongue_h above the
    split, set W + CLEARANCE in from the outer face exactly as 36B does it."""
    it = P.INTAKE
    W, c = it["wall"], P.CLEARANCE
    piece = U.box("T11b_tongue_base", 0.0, L, 0.0, W, 0.0, 8.0)
    U.boolean(piece, U.box("foot", 0.0, L, 0.0, 10.0, 0.0, 2.0), "UNION")
    # 2 mm root ledge inside the wall top joins the tongue to the wall (the tongue stands CLEARANCE inboard of it)
    U.boolean(piece, U.box("tongue_root", 0.0, L, W - 0.1, W + c + it["tongue_w"], 6.0, 8.0), "UNION")
    U.boolean(piece, U.box("tongue", 0.0, L, W + c, W + c + it["tongue_w"], 8.0 - 0.1, 8.0 + it["tongue_h"]), "UNION")
    U.shade(piece)
    return piece


def t11c_tb_socket():
    """30 x 30 x 14 block with the throttle body's 14 mm crush socket (trumpet_14 fit, tb_spigot_l deep)."""
    it = P.INTAKE
    blk = U.box("T11c_tb_socket", -15.0, 15.0, -15.0, 15.0, 0.0, 14.0)
    U.bevel_edges(blk, 1.0, 1, lambda c, d: abs(c.z - 14.0) < 0.2 and abs(d.z) < 0.1)
    F.cut_crush(blk, "trumpet_14", 14.0 - it["tb_spigot_l"] - 0.5, 14.0 + 1.0, 0.0, 0.0, entry="hi")
    U.shade(blk)
    return blk


def t11d_tb_pin():
    """Test spigot: the throttle body's spigot diameter and length on a 20 mm handle disc."""
    it = P.INTAKE
    pin = U.cylinder("T11d_tb_pin", 10.0, 0.0, 3.0, 0, 0)
    sp = U.cylinder("pin", it["tb_spigot_d"] / 2, 2.9, 3.0 + it["tb_spigot_l"], 0, 0)
    U.bevel_edges(sp, 0.6, 1, lambda c, d: abs(c.z - (3.0 + it["tb_spigot_l"])) < 0.2 and abs(d.z) < 0.1)
    U.boolean(pin, sp, "UNION")
    U.shade(pin)
    return pin


def build_all():
    return {"t11_lid": t11_tongue_lid(), "t11b_base": t11b_tongue_base(), "t11c_socket": t11c_tb_socket(), "t11d_pin": t11d_tb_pin()}
