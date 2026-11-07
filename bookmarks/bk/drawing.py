"""BK-01 BOOKMARKS: dimensioned engineering drawing (matplotlib), cut from the real solid.

Sheet 1 (BK01_drawing.png / .pdf), third-angle projection, millimetres [inches]:
    front view with the artwork, top view, right (fore-edge) view,
    section A-A (horizontal, z = 40) and section B-B (vertical, x = 40), title block.
Sheet 2 (BK01_colour_regions.png): the six colour regions and the three colour plans.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from . import params as P  # noqa: E402
from .validate import section  # noqa: E402

INK = "#1d1d22"
DIM = "#2b4fa8"
CUT = "#d9d4cc"
PINK = "#F4A6C4"


def _polys(g):
    if g.is_empty:
        return []
    return [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.geom_type == "Polygon"]


def to_shape(cs):
    outers, holes = [], []
    for r in cs.to_polygons():
        r = np.asarray(r)
        if len(r) < 3:
            continue
        a = 0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1])
        (outers if a > 0 else holes).append(Polygon(r).buffer(0))
    g = unary_union(outers) if outers else Polygon()
    return g.difference(unary_union(holes)) if holes else g


def project(m, view):
    """Silhouette in drawing coordinates (u right, v up) for 'front', 'top', 'right'."""
    if view == "front":    # looking +Y: u = x, v = z
        # rotate -90 about X: (x, y, z) -> (x, z, -y)
        return to_shape(m.rotate([-90, 0, 0]).project())
    if view == "top":      # looking down, front cover (y = 0) at the bottom: u = x, v = y
        return to_shape(m.project())
    if view == "right":    # looking -X, front cover on the left: u = y, v = z
        # rotate -90 about Z: (x, y) -> (y, -x); then -90 about X: (x', y', z) -> (x', z, -y')
        return to_shape(m.rotate([0, 0, -90]).rotate([-90, 0, 0]).project())
    raise ValueError(view)


def patch(ax, g, fc="none", ec=INK, lw=0.8, z=2, hatch=None, alpha=1.0):
    for p in _polys(g):
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            c = np.asarray(ring.coords)
            verts += list(c)
            codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, hatch=hatch, alpha=alpha))


def dim(ax, a, b, off, text=None, side=1, fs=6.5, ext=True):
    """Linear dimension between points a and b, offset `off` perpendicular to a-b."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = np.linalg.norm(d)
    n = np.array([-d[1], d[0]]) / L * off
    pa, pb = a + n, b + n
    if ext:
        for p, q in ((a, pa), (b, pb)):
            e = (q - p) / (np.linalg.norm(q - p) + 1e-9)
            ax.plot([p[0] + e[0] * 0.8, q[0] + e[0] * 1.2], [p[1] + e[1] * 0.8, q[1] + e[1] * 1.2], color=DIM, lw=0.4, zorder=5)
    ax.annotate("", pa, pb, arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.6, shrinkA=0, shrinkB=0,
                                            mutation_scale=6), zorder=6)
    t = text if text is not None else f"{L:.1f} [{L / 25.4:.2f}]"
    mid = (pa + pb) / 2
    ang = np.degrees(np.arctan2(d[1], d[0]))
    if ang > 90 or ang < -90:
        ang += 180
    nn = n / (np.linalg.norm(n) + 1e-9)
    ax.text(*(mid + nn * 1.6), t, color=DIM, fontsize=fs, ha="center", va="center", rotation=ang, zorder=7,
            bbox=dict(fc="white", ec="none", pad=0.4))


def label(ax, xy, text, fs=8, **kw):
    ax.text(*xy, text, fontsize=fs, color=INK, ha="center", va="center", weight="bold", **kw)


def note(ax, xy, text, fs=5.8, ha="left"):
    ax.text(*xy, text, fontsize=fs, color=INK, ha=ha, va="top", family="DejaVu Sans")


def draw_all(result, out):
    os.makedirs(out, exist_ok=True)
    full = result["full"]
    a2 = result["art"]
    m = a2["meadow"]

    fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_xlim(-30, 420)
    ax.set_ylim(-110, 175)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---------------- placements (drawing mm, scale 1:1 on a 450 x 320 field)
    FX, FZ = 0, 0             # front view origin
    TX, TZ = 0, 110           # top view origin (above the front view)
    RX, RZ = 120, 0           # right view origin
    AX_, AZ = 205, 110        # section A-A
    BX, BZ = 205, 0           # section B-B

    from shapely import affinity

    def at(g, x, z):
        return affinity.translate(g, x, z)

    # FRONT
    fr = project(full, "front")
    patch(ax, at(fr, FX, FZ), fc="#fbe6ee", lw=1.0)
    for g, lw in ((a2["plate"], 0.6), (a2["text"], 0.5), (m["petals"], 0.35), (m["centres"], 0.35),
                  (m["foliage"], 0.3), (m["ground"], 0.3)):
        patch(ax, at(g, FX, FZ), lw=lw, z=3)
    ax.plot([FX + P.HINGE_X] * 2, [FZ + 0.5, FZ + P.H - 0.5], color=INK, lw=0.4)
    label(ax, (FX + P.W / 2, FZ - 26), "FRONT")
    dim(ax, (FX, FZ), (FX + P.W, FZ), -12)
    dim(ax, (FX, FZ), (FX, FZ + P.H), 12)
    px0, px1 = P.ART_CX - P.PLATE_W / 2, P.ART_CX + P.PLATE_W / 2
    dim(ax, (FX + px0, FZ + P.PLATE_Z1), (FX + px1, FZ + P.PLATE_Z1), 5, fs=5.5)
    dim(ax, (FX + px1, FZ + P.PLATE_Z0), (FX + px1, FZ + P.PLATE_Z1), -4, fs=5.5)
    dim(ax, (FX + P.W, FZ + P.PLATE_Z1), (FX + P.W, FZ + P.H), -7, fs=5.5)
    dim(ax, (FX + P.W, FZ), (FX + P.W, FZ + P.ART_Z0), -7, fs=5.5)
    dim(ax, (FX, FZ + P.H), (FX + P.HINGE_X, FZ + P.H), 4, text=f"{P.HINGE_X:.1f}", fs=5.5)
    note(ax, (FX - 26, FZ - 32),
         "Artwork: raised nameplate +1.0, lettering +0.8 above it (white 1.4 deep incl. 0.6 inlay),\n"
         "petals +1.2, centres +1.5, stems/leaves +0.9 (midribs +0.55), mound +0.6.\n"
         "All relief undersides are 45 deg (built in 0.2 mm steps): no supports.\n"
         "Lettering: Bubblegum Sans (SIL OFL), 51.6 x 9.7, min stroke 1.25.")

    # TOP (front cover at the bottom of the view)
    tp = project(full, "top")
    patch(ax, at(tp, TX, TZ), fc="#fbe6ee", lw=1.0)
    rim = section(full, P.H - P.HEAD_SQUARE - 0.05)
    patch(ax, at(rim, TX, TZ), lw=0.5, z=3)
    label(ax, (TX + P.W / 2, TZ + P.D + 14), "TOP (front cover at the bottom)")
    dim(ax, (TX, TZ), (TX, TZ + P.D), 10)
    note(ax, (TX + P.W + 4, TZ + P.D - 2),
         "Opening at the page head:\n70.45 x 39.7 (0.5 x 45 deg\nlead-in), cavity below it\n69.45 x 38.7, R2.5 corners.\n"
         "Page block sits 0.8 below\nthe boards at the head.")

    # RIGHT (fore-edge)
    rt = project(full, "right")
    patch(ax, at(rt, RX, RZ), fc="#fbf4e6", lw=1.0)
    label(ax, (RX + P.D / 2, RZ - 26), "RIGHT (fore-edge)")
    dim(ax, (RX, RZ), (RX + P.D, RZ), -12)
    # page lines
    for y in np.arange(P.D - P.YF + P.BOARD + 0.9, P.D - P.BOARD - 0.6, P.PAGE_PITCH):
        ax.plot([RX + y] * 2, [RZ + 0.6, RZ + P.H - P.HEAD_SQUARE - 0.4], color=INK, lw=0.15, zorder=3)
    note(ax, (RX - 2, RZ - 32), "Fore-edge: page block recessed 1.2 (\"squares\"),\n"
         f"{result['n_pages']} page grooves 0.5 wide x 0.35 deep, pitch 1.3.\nRelief on the left (front cover faces -Y).")

    # SECTION A-A (z = 40), front cover at the bottom
    sa = at(section(full, 40.0), AX_, AZ)
    patch(ax, sa, fc=CUT, lw=0.8, hatch="////")
    label(ax, (AX_ + P.W / 2, AZ + P.D + 14), "SECTION A-A  (z = 40, front cover at the bottom)")
    # drawing v = AZ + y_world; the world y of the front cavity face is D - CAV_Y1
    yw_front, yw_back = P.D - P.CAV_Y1, P.D - P.CAV_Y0
    yd = lambda yw: AZ + yw  # noqa: E731
    dim(ax, (AX_ + P.CAV_X0, yd(20)), (AX_ + P.CAV_X1, yd(20)), 0, fs=6)
    dim(ax, (AX_ + P.CAV_X1 - 14, yd(yw_front)), (AX_ + P.CAV_X1 - 14, yd(yw_back)), 0, fs=6)
    dim(ax, (AX_ + 10, yd(P.D - P.YF)), (AX_ + 10, yd(yw_front)), 4, text="2.0", fs=5)
    dim(ax, (AX_ + 10, yd(yw_back)), (AX_ + 10, yd(P.D)), 4, text="2.0", fs=5)
    dim(ax, (AX_ + P.CAV_X1, yd(20)), (AX_ + P.W - P.SQUARE - P.PAGE_GROOVE_DEPTH, yd(20)), 7,
        text="2.0", fs=5)
    dim(ax, (AX_, yd(20)), (AX_ + P.CAV_X0, yd(20)), 7, text="6.0", fs=5)

    # SECTION B-B (x = 40): rotating +90 about Y maps (x, y, z) -> (z, y, -x), so the plane
    # x = 40 becomes height -40; the slice comes out in (z, y), swapped to drawing (y, z)
    g = to_shape(full.rotate([0, 90, 0]).slice(-40.0))
    g = affinity.affine_transform(g, [0, 1, 1, 0, 0, 0])
    patch(ax, at(g, BX, BZ), fc=CUT, lw=0.8, hatch="////")
    label(ax, (BX + P.D / 2, BZ - 26), "SECTION B-B  (x = 40)")
    dim(ax, (BX + P.D + 0, BZ), (BX + P.D, BZ + P.FLOOR), -6, text="2.4", fs=5.5)
    dim(ax, (BX + P.D - P.CAV_Y0, BZ + P.FLOOR), (BX + P.D - P.CAV_Y0, BZ + P.H), 5, fs=6)
    dim(ax, (BX + P.D - P.CAV_Y1, BZ - 2), (BX + P.D - P.CAV_Y0, BZ - 2), -8, fs=6)
    dim(ax, (BX, BZ + P.H), (BX + (P.D - P.YF), BZ + P.H), 4, text="1.8 relief", fs=5)
    note(ax, (BX - 2, BZ - 32), "Floor 2.4, R2.5 floor fillet, walls 2.0.\nUsable depth 81.9 from the opening.")

    # cutting-plane marks on the front view
    ax.plot([FX - 4, FX + P.W + 4], [FZ + 40, FZ + 40], color="#b33", lw=0.5, ls=(0, (8, 2, 2, 2)))
    ax.text(FX - 6, FZ + 40, "A", color="#b33", fontsize=7, ha="right", va="center", weight="bold")
    ax.plot([FX + 40, FX + 40], [FZ - 4, FZ + P.H + 4], color="#b33", lw=0.5, ls=(0, (8, 2, 2, 2)))
    ax.text(FX + 40, FZ + P.H + 6, "B", color="#b33", fontsize=7, ha="center", va="bottom", weight="bold")

    # ---------------- title block
    tb = box(300, -105, 418, -40)
    patch(ax, tb, lw=1.0)
    lines = [("BK-01  BOOKMARKS", 11, "bold"), ("Book-shaped bookmark holder", 7.5, "normal"),
             ("Envelope 79.0 x 44.5 x 84.3 mm  [3.11 x 1.75 x 3.32 in]", 6.5, "normal"),
             ("Units mm [in] | Third-angle projection | Scale 1:1 on A3", 6, "normal"),
             ("General tolerance +/-0.2 (FDM). Print upright, open top up.", 6, "normal"),
             ("Material: PETG, 0.4 nozzle, 0.2 layer | 6 colour regions", 6, "normal"),
             ("Solid volume 58.5 cm3 (about 74 g PETG)", 6, "normal"),
             ("Generated by bookmarks.py - sheet 1 of 2", 5.5, "normal")]
    y = -46
    for t, fs, w in lines:
        ax.text(304, y, t, fontsize=fs, weight=w, color=INK, va="top")
        y -= 7.6 if fs > 7 else 6.6
    # mini 3D-ish legend of inch equivalents
    note(ax, (300, -10), "Key dimensions\n"
         "Compartment  69.45 x 38.7 x 81.9 deep  [2.73 x 1.52 x 3.22 in]\n"
         "Walls 2.0 (spine side 4.2-6.0), floor 2.4\n"
         "Fits standard 2 x 6-7 in bookmarks (50.8 wide) with 18 mm to spare\n"
         "Front relief max 1.8 (inside the 44.5 envelope)")

    fig.savefig(os.path.join(out, "BK01_drawing.png"), dpi=200, facecolor="white")
    fig.savefig(os.path.join(out, "BK01_drawing.pdf"), facecolor="white")
    plt.close(fig)
    colour_sheet(result, out)
    print("drawing written")


def colour_sheet(result, out):
    """Front view coloured three ways: the three shipped colour plans."""
    a2 = result["art"]
    m = a2["meadow"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 6.2))
    regions = dict(lettering=a2["text"], petals=m["petals"], centres=m["centres"],
                   foliage=unary_union([m["foliage"], m["ground"]]))
    for ax, (plan, spec) in zip(axs, P.PLANS.items()):
        col = {k: "#" + spec["filaments"][spec["slots"][k]][1] for k in P.PARTS}
        ax.add_patch(plt.Rectangle((0, 0), P.W, P.H, fc=col["body"], ec=INK, lw=0.8))
        ax.add_patch(plt.Rectangle((P.W - 2.5, 0), 2.5, P.H - P.HEAD_SQUARE, fc=col["pages"], ec=INK, lw=0.4))
        patch(ax, a2["plate"], fc=col["body"], lw=0.6)
        for k, g in regions.items():
            patch(ax, g, fc=col[k], ec="#7a5060", lw=0.25, z=3)
        ax.set_xlim(-2, P.W + 2)
        ax.set_ylim(-2, P.H + 2)
        ax.set_aspect("equal")
        ax.axis("off")
        fl = ", ".join(f"F{s} {n}" for s, (n, h) in spec["filaments"].items())
        ax.set_title(f"{plan}  ({len(spec['filaments'])} filaments)\n{fl}", fontsize=10)
    fig.suptitle("BK-01 colour plans (front view; page-edge colour shown as the strip on the right)", fontsize=11)
    fig.savefig(os.path.join(out, "BK01_colour_plans.png"), dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
