"""Dimensioned drawing and ratchet diagram (matplotlib)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from manifold3d import Manifold  # noqa: E402

from . import geom as G  # noqa: E402
from .params import P, knob_x  # noqa: E402

INK, ORANGE, GREY = "#2B2D31", "#FF6A13", "#C9C6C0"


def _fill(ax, cs_, fc, ec=INK, lw=0.6):
    verts, codes = [], []
    for poly in cs_.to_polygons():
        q = np.asarray(poly)
        verts += q.tolist() + [q[0].tolist()]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(q) - 1) + [Path.CLOSEPOLY]
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw))


def _dim(ax, p0, p1, text, fs=7.5):
    ax.annotate("", xy=p0, xytext=p1, arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7))
    ax.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, text, fontsize=fs, ha="center", va="center", color=INK,
            bbox=dict(fc="white", ec="none", pad=0.4))


def drawing(path, frame, key):
    fig = plt.figure(figsize=(13, 9), dpi=150)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.7, 1])
    k0, k1 = knob_x()
    xf = P.slot_l + P.lug_t_far
    # top view
    ax = fig.add_subplot(gs[0, 0])
    _fill(ax, frame.project(), "#E8E5DF")
    _fill(ax, key.project(), ORANGE + "55", ORANGE)
    _dim(ax, (0, -P.plate_w / 2 - 5), (P.slot_l, -P.plate_w / 2 - 5), f"slot {P.slot_l:.0f} (tubes to 65 wide)")
    bb = frame.bounding_box()
    _dim(ax, (bb[0], P.plate_w / 2 + 9), (bb[3], P.plate_w / 2 + 9), f"{bb[3]-bb[0]:.1f}")
    _dim(ax, (bb[3] + 5, bb[1]), (bb[3] + 5, bb[4]), f"{bb[4]-bb[1]:.1f}")
    ax.text(P.slot_l / 2, 2.2, f"nip {P.nip} (Standard) · 2.0 Loose · 1.2 Tight", fontsize=7, ha="center", color=INK)
    lx0, lx1, ly0, ly1 = G.leaf_box()
    ax.text(lx1 + 1, (ly0 + ly1) / 2 + 3, "leaf pawl\n20 x 7 x 1.2", fontsize=7, color=ORANGE)
    ax.set_aspect("equal")
    ax.set_xlim(bb[0] - 6, bb[3] + 12)
    ax.set_ylim(bb[1] - 10, bb[4] + 14)
    ax.set_title("Top: frame (grey) with the key seated (orange)", fontsize=10)
    ax.axis("off")
    # section along the axis (x-z at y = 3, through one fork tine)
    ax = fig.add_subplot(gs[1, 0])
    T = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]  # (x, y, z) -> (x, z, y)
    y = 3.5
    _fill(ax, frame.transform(T).slice(y), GREY)
    _fill(ax, key.transform(T).slice(y), ORANGE + "88", ORANGE)
    ax.set_aspect("equal")
    ax.set_xlim(k0 - 6, xf + 8)
    ax.set_ylim(-3, P.axis_z + P.r_tip + 6)
    _dim(ax, (xf + 4, 0), (xf + 4, P.axis_z), f"axis {P.axis_z:.0f}")
    _dim(ax, (k0, P.axis_z + P.r_tip + 3), (k1, P.axis_z + P.r_tip + 3), f"knob {P.knob_t:.0f}")
    ax.set_title(f"Section along the key (y = {y}): bearings {P.shaft_d + 2 * P.bore_clear:.1f} teardrop for a "
                 f"{P.shaft_d:.0f} journal", fontsize=9)
    ax.grid(alpha=0.2)
    # end view of the key
    ax = fig.add_subplot(gs[0, 1])
    T2 = [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]]  # (x, y, z) -> (y, z, x)
    _fill(ax, frame.transform(T2).project(), "#E8E5DF")
    _fill(ax, key.transform(T2).slice((k0 + k1) / 2), ORANGE + "88", ORANGE)
    _fill(ax, key.transform(T2).slice(P.slot_l / 2), "white", ORANGE)
    ax.set_aspect("equal")
    ax.set_xlim(-24, 24)
    ax.set_ylim(-2, 42)
    _dim(ax, (-P.r_tip, P.axis_z + P.r_tip + 2), (P.r_tip, P.axis_z + P.r_tip + 2), f"Ø{2 * P.r_tip:.0f}, {P.teeth} teeth")
    ax.set_title("End view: knob, lug and the open fork (gap 2.2)", fontsize=9)
    ax.grid(alpha=0.2)
    # key in print orientation
    ax = fig.add_subplot(gs[1, 1])
    from .validate import key_print
    kp = key_print(key)
    T3 = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]]
    _fill(ax, kp.transform(T3).project(), ORANGE + "55", ORANGE)
    kb = kp.bounding_box()
    _dim(ax, (kb[3] + 4, 0), (kb[3] + 4, kb[5]), f"{kb[5]:.1f}")
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_aspect("equal")
    ax.set_xlim(kb[0] - 6, kb[3] + 14)
    ax.set_ylim(-4, kb[5] + 6)
    ax.set_title("Key as printed: knob face down, fork up", fontsize=9)
    ax.grid(alpha=0.2)
    fig.suptitle("ODD LAYER TP-01 TUBEPRESS  ·  dimensions in mm", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def ratchet_diagram(path):
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150)
    ph = G.rest_phase()
    lx0, lx1, ly0, ly1 = G.leaf_box()
    for ax, (title, dphi, drop) in zip(axs, [("At rest: pawl in a tooth gap. Reverse rotation locks on the steep face", 0.0, 0.0),
                                             ("Winding: a ramp presses the pawl and leaf down 1.2 mm, then it clicks back", -10.0, 1.2)]):
        k = G.knob_profile(P, ph + dphi)
        x, y = k.exterior.xy
        ax.fill(x, y, color=ORANGE, alpha=0.35, ec=ORANGE)
        pw = G.pawl_profile(P)
        from shapely.affinity import translate
        pw = translate(pw, 0, -drop)
        x, y = pw.exterior.xy
        ax.fill(x, y, color=INK)
        # leaf (bent: simple cubic deflection shape)
        ys = np.linspace(ly0, ly1, 40)
        s = (ly1 - ys) / (ly1 - ly0)
        dz = -drop * (3 * s ** 2 - s ** 3) / 2
        ax.fill_between(ys, dz, dz + P.leaf_t, color=INK, alpha=0.8)
        ax.fill_between([ly1, ly1 + 6], [0, 0], [P.plate_t, P.plate_t], color=GREY)
        ax.axhline(0, color=GREY, lw=0.6, ls=":")
        ax.set_xlim(-10, 26)
        ax.set_ylim(-2.5, 11)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=8.5)
        ax.text(ly1 + 1, P.plate_t + 0.4, "leaf root (plate)", fontsize=7)
    axs[0].add_patch(FancyArrowPatch((-7, 9.5), (-2, 9.5), arrowstyle="-|>", mutation_scale=10, color=INK))
    axs[0].text(-9.5, 10.1, "reverse: teeth move +y", fontsize=7)
    axs[1].add_patch(FancyArrowPatch((4, 9.5), (-1, 9.5), arrowstyle="-|>", mutation_scale=10, color=INK))
    axs[1].text(-2, 10.1, "winding: teeth move -y", fontsize=7)
    fig.suptitle("TP-01 ratchet, section through the pawl (y-z plane). Leaf strain at a 1.2 mm drop: 0.54 %", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
