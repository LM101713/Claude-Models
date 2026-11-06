"""
HF-04 HOLDFAST: engineering diagrams for the docs (matplotlib, from the real geometry).

    python tools/make_docs.py          -> docs/HF04_*.png

Front views are drawn as you see the part on the wall (looking at the wall), so the use-frame
X axis points to the viewer's LEFT. Sections come from slicing the exact solids.
"""

import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon as MplPoly  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from hf import geom as G  # noqa: E402
from hf import validate as V  # noqa: E402
from hf.params import D, P, centre, roll_angle, s_of_diameter  # noqa: E402

OUT = os.path.join(HERE, "docs")
GRAPH, ORANGE, WOOD, INK, MUTED, GRID = "#2B2D31", "#FF6A13", "#C99A68", "#1E1F22", "#7A7D84", "#D9D6D0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def fv(pts):
    """use-frame (X, Z) -> front view (viewer's x = -X)."""
    a = np.atleast_2d(np.asarray(pts, float)).copy()
    a[:, 0] *= -1
    return a


def poly_patch(ax, poly, **kw):
    ax.add_patch(MplPoly(fv(np.array(poly.exterior.coords)), closed=True, **kw))
    for hole in poly.interiors:
        ax.add_patch(MplPoly(fv(np.array(hole.coords)), closed=True, fc="white", ec=kw.get("ec", INK), lw=kw.get("lw", 1)))


def dim(ax, p0, p1, text, off=(0, 0), color=INK, fs=8, arrow="<->"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=arrow, mutation_scale=8, color=color, lw=0.8, shrinkA=0, shrinkB=0))
    mx, my = (p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1]
    ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


# =====================================================================================
# 1. the wedge: geometry and forces
# =====================================================================================


def wedge_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    outline = G.base_outline()
    hl = G.housing_left()
    poly_patch(ax, outline, fc="#EDEBE7", ec=MUTED, lw=0.8)
    for h in (hl, G.mirror_x(hl)):
        poly_patch(ax, h, fc="#5A5D63", ec=GRAPH, lw=1.0)
    d = 25.0
    s = s_of_diameter(d)
    ax.add_patch(MplPoly(fv([(-d / 2, -60), (d / 2, -60), (d / 2, 60), (-d / 2, 60)]), fc=WOOD, ec="#8C6A45", lw=0.8, alpha=0.9))
    for side in (-1, 1):
        c = centre(s) * np.array([1 if side < 0 else -1, 1])
        c0 = centre(0.0) * np.array([1 if side < 0 else -1, 1])
        ck = centre(D.s_key) * np.array([1 if side < 0 else -1, 1])
        for cc, ls, a in ((c0, ":", 0.8), (ck, ":", 0.8)):
            ax.add_patch(Circle(fv(cc)[0], P.R_ROLL, fc="none", ec=MUTED, ls=ls, lw=0.8))
        ax.add_patch(Circle(fv(c)[0], P.R_ROLL, fc=ORANGE, ec="#B4470B", lw=1.0))
        ax.plot(*fv([c0, ck]).T, color="#B4470B", lw=0.8, ls="--")
    # forces on the LEFT roller (use frame), drawn at the viewer's right
    c = centre(s)
    H = c + np.array([P.R_ROLL, 0])
    Rm = c - P.R_ROLL * D.n
    ax.plot(*fv([H, Rm]).T, color=INK, lw=1.0)
    N = 9.0
    ax.add_patch(FancyArrowPatch(fv(H)[0], fv(H + [-N, 0])[0], arrowstyle="-|>", mutation_scale=12, color="#1F6FB2", lw=1.6))
    ax.add_patch(FancyArrowPatch(fv(H)[0], fv(H + [0, -N * D.mu_req * 2.2])[0], arrowstyle="-|>", mutation_scale=12, color="#1F6FB2", lw=1.6))
    ax.text(*fv(H + [-N - 1, 2.2])[0], "N", color="#1F6FB2", fontsize=10, ha="right")
    ax.text(*fv(H + [1.2, -N * D.mu_req * 2.2 - 1.2])[0], "F = N·tan 8°", color="#1F6FB2", fontsize=9, ha="right",
            bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.85))
    # ramp angle
    p0 = D.P0 - 6 * D.u
    p1 = D.P0 + 44 * D.u
    ax.plot(*fv([p0, p1]).T, color=ORANGE, lw=2.2)
    v0 = p0 + np.array([0, 40])
    ax.plot(*fv([p0, v0]).T, color=MUTED, lw=0.8, ls="--")
    arc_t = np.linspace(math.pi / 2, math.pi / 2 + D.delta, 20)
    arc = p0 + 30 * np.column_stack([np.cos(arc_t), np.sin(arc_t)])
    ax.plot(*fv(arc).T, color=INK, lw=0.8)
    ax.text(*fv(p0 + 33 * np.array([math.cos(math.pi / 2 + D.delta / 2), math.sin(math.pi / 2 + D.delta / 2)]))[0],
            f"{P.DELTA_DEG:.0f}°", fontsize=10, ha="center")
    mid = (H + Rm) / 2
    ax.annotate("contact chord: 8° off the normal\nat both contacts", xy=fv(mid)[0], xytext=(44, 40), fontsize=8,
                color=INK, ha="left", arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    ax.text(0, -46, f"Ø{d:.0f} handle", ha="center", fontsize=9, color="#5B4128")
    ax.text(fv(centre(0.0))[0][0] + 0, D.z_bot - 6.5,
            "dotted: bottom stop (16 mm gap) and keyhole (35 mm gap)", ha="center", fontsize=8, color=MUTED)
    ax.set_xlim(-62, 78)
    ax.set_ylim(-52, 44)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("HF-04 HOLDFAST · the wedge, front view (as seen on the wall)", loc="left", fontsize=12, color=INK)
    txt = (f"Each roller is squeezed between the handle and a ramp leaning {P.DELTA_DEG:.0f}° from vertical.\n"
           f"With no moment on a free roller, the two contact forces act along the chord, {P.DELTA_DEG / 2:.0f}° off each normal,\n"
           f"so each contact needs friction ≥ tan {P.DELTA_DEG / 2:.0f}° = {D.mu_req:.3f}. Any load is held once that is met: the weight\n"
           f"only raises N (N = W / (2·{D.mu_req:.3f}) = 3.6 W per roller). Lifting the handle reverses F and the rollers roll free.")
    fig.text(0.06, 0.03, txt, fontsize=9, color=INK, va="bottom")
    fig.savefig(os.path.join(OUT, "HF04_wedge.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


# =====================================================================================
# 2. fit section across the slot, through the roller axis
# =====================================================================================


def section(m, s):
    """Slice a use-frame solid with the plane through centre(s) normal to the ramp direction u.
    Returns polygons in (across-slot toward the channel, Y) coordinates."""
    c = centre(s)
    n3 = np.array([D.n[0], 0, D.n[1]])
    u3 = np.array([D.u[0], 0, D.u[1]])
    y3 = np.array([0, 1.0, 0])
    R = np.vstack([n3, y3, u3])  # rows: new x, new y, new z (n x Y = u: proper rotation)
    t = -R @ np.array([c[0], 0, c[1]])
    mat = np.hstack([R, t[:, None]])
    mm = m.transform(mat.tolist())
    cs = mm.slice(0.0)
    return [np.array(p) for p in cs.to_polygons()]


def fill_polys(ax, polys, fc, ec, lw=0.8, z=1):
    # even-odd: draw outer loops filled, holes white (simple, matches our sections)
    for p in polys:
        area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
        ax.add_patch(MplPoly(p, closed=True, fc=fc if area > 0 else "white", ec=ec, lw=lw, zorder=z + (0 if area > 0 else 0.5)))


def fit_section():
    base = G.build_base(engrave=False)
    roller = G.build_roller()
    s = 14.0
    rl = V.place(roller, s, -1, dn=0.0)
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
    for k, ax in enumerate(axs):
        fill_polys(ax, section(base, s), "#6E7179", GRAPH, 0.8, 1)
        fill_polys(ax, section(rl, s), "#FFB27F", "#B4470B", 0.8, 3)
        ax.set_aspect("equal")
        ax.set_facecolor("white")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    ax = axs[0]
    ax.set_xlim(-22, 22)
    ax.set_ylim(-2, 31)
    ax.axhline(0, color=MUTED, lw=1.2)
    ax.text(-21, -1.4, "wall", fontsize=8, color=MUTED)
    ax.set_title("Section across the slot, through the roller axis (roller at mid travel)", loc="left", fontsize=11)
    dim(ax, (-12.0, 17.5), (12.0, 17.5), "roller Ø24", (0, 1.1))
    ax.annotate("ramp: rolling contact", xy=(-12.0, 13), xytext=(-21, 25), fontsize=8,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    ax.annotate("1.0 mm clearance\nto the pocket wall on this side", xy=(12.6, 26), xytext=(5, 29.6), fontsize=8,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    ax.text(14.5, 3.0, "channel side →", fontsize=8, color=MUTED)
    ax = axs[1]
    ax.set_xlim(-8.5, 8.5)
    ax.set_ylim(1.2, 9.6)
    ax.set_title("Detail: stub in the keyhole T-slot (all clearances in mm, nominal)", loc="left", fontsize=11)
    yu, yb = P.BACK_T, P.BACK_T + P.G_BACK
    dim(ax, (P.NECK_R, 6.2), (P.LIP_SLOT_HALF, 6.2), "", (0, 0), fs=7)
    ax.text(P.LIP_SLOT_HALF + 0.15, 6.55, f"{P.LIP_SLOT_HALF - P.NECK_R:.1f} neck", fontsize=8)
    dim(ax, (P.HEAD_R, 3.2), (P.CAV_HALF, 3.2), "", fs=7)
    ax.text(P.CAV_HALF + 0.2, 3.1, f"{P.CAV_HALF - P.HEAD_R:.1f} head", fontsize=8)
    dim(ax, (-6.6, yu), (-6.6, yb), "", fs=7)
    ax.text(-8.3, yb + 0.5, f"{P.G_BACK:.1f} back gap", fontsize=8)
    dim(ax, (-P.LIP_SLOT_HALF, 4.6), (-P.HEAD_R, 4.6), "", fs=7)
    ax.text(-8.3, 4.15, f"{P.HEAD_R - P.LIP_SLOT_HALF:.1f} lip overlap\n(retention)", fontsize=8)
    gap_fwd = (P.LIP_SLOT_HALF + P.Y_LIP_UNDER) - (P.Y_CONE0 + P.NECK_R)
    ax.text(0.0, 1.55, f"head cone to lip underside: {gap_fwd:.1f} axial (pull-out play) · both 45°, no supports",
            fontsize=8, ha="center", color=INK)
    ax.text(-8.2, 9.15, "keyhole Ø11.6 at the top end of the slot lets the Ø10 head in", fontsize=8, color=MUTED)
    fig.text(0.05, 0.02, "Sliced from the exact solids. Holes on FDM printers usually print 0.1-0.2 mm small: the "
             "printer-variation check rebuilds this joint with those errors (see the validation report).",
             fontsize=8, color=MUTED)
    fig.savefig(os.path.join(OUT, "HF04_fit_section.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


# =====================================================================================
# 3. charts
# =====================================================================================


def charts():
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    d = np.linspace(P.D_CLOSED, P.D_TOP, 100)
    s = np.array([s_of_diameter(x) for x in d])
    z = np.array([centre(x)[1] for x in s])
    ax = axs[0]
    ax.axvspan(*P.D_RATED, color=ORANGE, alpha=0.10, lw=0)
    ax.plot(d, z, color=GRAPH, lw=1.8, label="grip height z (mm)")
    ax.plot(d, s, color=ORANGE, lw=1.8, label="roller travel s (mm)")
    ax2 = ax.twinx()
    ax2.plot(d, [roll_angle(x) for x in s], color=MUTED, lw=1.2, ls="--")
    ax.plot([], [], color=MUTED, lw=1.2, ls="--", label="roller turn (°, right axis)")
    ax2.set_ylabel("roller turn (°)")
    ax.set_xlabel("handle diameter (mm)")
    ax.set_title("Handle size → roller position", loc="left")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.text(25.5, -14, "rated 19-32 mm", color=ORANGE, fontsize=8, ha="center")
    ax.grid(color=GRID, lw=0.6)

    ax = axs[1]
    mu = np.linspace(0.05, 0.45, 100)
    ax.plot(mu, mu / D.mu_req, color=GRAPH, lw=1.8)
    ax.axhline(1.0, color="#B3261E", lw=1.0)
    ax.axvline(D.mu_req, color="#B3261E", lw=0.8, ls=":")
    ax.text(D.mu_req + 0.005, 2.6, f"needs μ ≥ {D.mu_req:.3f}", color="#B3261E", fontsize=8, rotation=90, va="top")
    for lo, hi, lab, yy in ((0.20, 0.30, "PLA on painted steel / PP (indicative)", 0.45), (0.30, 0.45, "PLA on wood / aluminium (indicative)", 0.75)):
        ax.axvspan(lo, hi, ymin=yy - 0.1, ymax=yy, color=ORANGE, alpha=0.18, lw=0)
        ax.text((lo + hi) / 2, (yy - 0.05) * 3.2, lab, fontsize=7, ha="center", va="center")
    ax.set_ylim(0, 3.2)
    ax.set_xlabel("static friction, handle vs roller (μ)")
    ax.set_ylabel("friction margin")
    ax.set_title("Will it hold? (literature ranges, not measured)", loc="left")
    ax.grid(color=GRID, lw=0.6)

    ax = axs[2]
    W = np.linspace(1, 35, 100)
    N = W / (2 * D.mu_req)
    E_pla, nu = 3500.0, 0.36
    for lab, (E2, nu2), col in (("steel handle, Ø19", (200000.0, 0.3), "#B3261E"), ("wood / plastic, Ø25", (3000.0, 0.38), GRAPH)):
        Es = 1 / ((1 - nu**2) / E_pla + (1 - nu2**2) / E2)
        dd = 19.0 if "19" in lab else 25.0
        Re = math.sqrt(P.R_ROLL * dd / 2)
        a = (3 * N * Re / (4 * Es)) ** (1 / 3)
        ax.plot(W / 9.81, 3 * N / (2 * np.pi * a * a), color=col, lw=1.6, label=lab)
    ax.axhspan(80, 110, color=ORANGE, alpha=0.15, lw=0)
    ax.text(2.6, 95, "first local yield in the rim:\np0 ≈ 1.6 σy (σy 50-70 MPa)", fontsize=7, ha="center", va="center")
    ax.axvline(2.0, color=MUTED, lw=0.8, ls="--")
    ax.text(2.05, 15, "2 kg rating", fontsize=7, color=MUTED)
    ax.set_xlabel("tool weight (kg)")
    ax.set_ylabel("peak contact pressure, elastic (MPa)")
    ax.set_title("Roller-to-handle contact (Hertz)", loc="left")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.grid(color=GRID, lw=0.6)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "HF04_charts.png"), dpi=160)
    plt.close(fig)


# =====================================================================================
# 4. dimensioned drawing
# =====================================================================================


def drawing():
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.4), gridspec_kw=dict(width_ratios=[1.6, 0.7]))
    ax = axs[0]
    o = G.base_outline()
    hl = G.housing_left()
    poly_patch(ax, o, fc="#EDEBE7", ec=INK, lw=1.0)
    for h in (hl, G.mirror_x(hl)):
        poly_patch(ax, h, fc="#B9BBC0", ec=INK, lw=0.9)
    for side in (-1, 1):
        a = centre(-0.6)
        b = centre(D.s_key + 0.6)
        ring = G.stadium_ring(a, b, P.LIP_SLOT_HALF, 24)
        ring[:, 0] *= (1 if side < 0 else -1)
        ax.add_patch(MplPoly(fv(ring), fc="none", ec=INK, lw=0.6, ls="--"))
        k = centre(D.s_key) * np.array([1 if side < 0 else -1, 1])
        ax.add_patch(Circle(fv(k)[0], P.KEY_R, fc="none", ec=INK, lw=0.6, ls="--"))
    for x, z in G.screw_positions():
        ax.add_patch(Circle((x, z), P.SCREW_HOLE_D / 2, fc="white", ec=INK, lw=0.8))
        ax.add_patch(Circle((x, z), P.SCREW_CSK_D / 2, fc="none", ec=INK, lw=0.6))
    xb0, zb0, xb1, zb1 = o.bounds
    dim(ax, (xb0, zb1 + 6), (xb1, zb1 + 6), f"{xb1 - xb0:.1f}")
    dim(ax, (xb1 + 6, zb0), (xb1 + 6, zb1), f"{zb1 - zb0:.1f}")
    dim(ax, (-P.X_CH, zb0 - 6), (P.X_CH, zb0 - 6), f"channel {2 * P.X_CH:.0f}")
    zs = [z for _, z in G.screw_positions()]
    dim(ax, (9, zs[1]), (9, zs[0]), f"{zs[0] - zs[1]:.1f}\nscrews", (5.5, 0))
    ax.text(0, zs[0] + 6.0, "2 × countersunk Ø3.5-4 mm\n(#6-#8) wood screws", ha="center", fontsize=7.5)
    ax.text(0, zb0 - 13.5, f"V outline: outer edges parallel to the {P.DELTA_DEG:.0f}° ramps", ha="center", fontsize=8, color=MUTED)
    ax.set_xlim(xb0 - 10, xb1 + 18)
    ax.set_ylim(zb0 - 18, zb1 + 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Front view (dashed: T-slots and keyholes in the back plate)", loc="left", fontsize=11)
    # side profile: slice the base through a housing (plane x = -35)
    ax = axs[1]
    base = G.build_base(engrave=False)
    for xcut, col, lab in ((-30.0, "#B9BBC0", "through a housing"), (0.0, "#6E7179", "through the channel")):
        R = np.array([[0, 1.0, 0], [0, 0, 1.0], [1.0, 0, 0]])  # (Y, Z, X): proper rotation
        mm = base.transform(np.hstack([R, np.array([[0], [0], [-xcut]])]).tolist())
        for p in mm.slice(0.0).to_polygons():
            p = np.array(p)
            ax.add_patch(MplPoly(p, closed=True, fc=col, ec=INK, lw=0.8, alpha=0.95 if xcut < 0 else 0.9))
    dim(ax, (0, D.z_bot - 6), (P.Y_FRONT, D.z_bot - 6), f"{P.Y_FRONT:.0f}")
    ax.text(P.BACK_T + 1, D.z_top + 4, f"back plate {P.BACK_T:.0f}", fontsize=8)
    ax.axvline(0, color=MUTED, lw=1.5)
    ax.text(-1.5, D.z_top + 4, "wall", fontsize=8, color=MUTED, ha="right")
    ax.set_xlim(-12, 40)
    ax.set_ylim(D.z_bot - 12, D.z_top + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Side sections (x = -30 light, x = 0 dark)", loc="left", fontsize=11)
    fig.savefig(os.path.join(OUT, "HF04_drawing.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    wedge_diagram()
    fit_section()
    charts()
    drawing()
    print("docs written to", OUT)
