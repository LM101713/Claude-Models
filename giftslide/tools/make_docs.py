#!/usr/bin/env python3
"""
GS-05 GIFT SLIDE: dimensioned drawings and detent charts (matplotlib).

Every outline is a real slice / projection of the generated solids, and every dimension is
read from gs/params.py, so the drawings cannot drift from the model.

    python tools/make_docs.py        -> docs/GS05_drawing_*.png/.pdf, docs/GS05_detent*.png
"""

import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon as MPoly  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from gs import detent as Dt  # noqa: E402
from gs import geom as G  # noqa: E402
from gs.params import LOOSE, P, SNUG  # noqa: E402

OUT = os.path.join(HERE, "docs")
INK = "#23262b"
DIM = "#1f5fa8"
TRAY_F = "#e9e4da"
LID_F = "#f2b8b5"
CUT_T = "#bdb4a3"
CUT_L = "#e7807b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})


# ------------------------------------------------------------------ section helpers


def sec_x(m, x):
    """Section of a solid at plane x = const, returned as polygons in (y, z)."""
    r = m.transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -x]], float))
    return r.slice(0.0).to_polygons()


def sec_y(m, y):
    """Section at plane y = const, polygons in (x, z)."""
    r = m.transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, -y]], float))
    return r.slice(0.0).to_polygons()


def fill(ax, polys, fc, ec=INK, lw=0.6, hatch=None, z=1):
    for p in polys:
        ax.add_patch(MPoly(np.asarray(p), closed=True, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z))


def outline(ax, polys, color=INK, lw=0.7, ls="-", z=2):
    for p in polys:
        p = np.vstack([p, p[:1]])
        ax.plot(p[:, 0], p[:, 1], color=color, lw=lw, ls=ls, zorder=z)


def dim(ax, a, b, off, text=None, fs=7.5, side=1, ext=True, arrow="<|-|>", color=DIM, tpad=0.0):
    """Linear dimension between points a and b, offset perpendicular by `off`."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    if L < 1e-9:
        return
    u = d / L
    n = np.array([-u[1], u[0]]) * side
    pa, pb = a + n * off, b + n * off
    if ext:
        for p, q in ((a, pa), (b, pb)):
            e = q + n * np.sign(off) * 0.12 * abs(off) / max(abs(off), 1e-9) * 1.0
            ax.plot([p[0] + n[0] * 0.15 * np.sign(off), e[0]], [p[1] + n[1] * 0.15 * np.sign(off), e[1]],
                    color=color, lw=0.4, zorder=5)
    ax.annotate("", xy=pb, xytext=pa, arrowprops=dict(arrowstyle=arrow, color=color, lw=0.6,
                                                       shrinkA=0, shrinkB=0, mutation_scale=7), zorder=5)
    t = text if text is not None else f"{L:.2f}".rstrip("0").rstrip(".")
    mid = (pa + pb) / 2 + n * (tpad + 0.0)
    ang = math.degrees(math.atan2(u[1], u[0]))
    if ang > 90.1 or ang < -89.9:
        ang += 180
    ax.text(mid[0], mid[1], t, color=color, fontsize=fs, ha="center", va="bottom" if side * np.sign(off) >= 0 else "top",
            rotation=ang, rotation_mode="anchor", zorder=6,
            bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))


def label(ax, xy, txt, xytext, fs=7.5, color=INK):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=fs, color=color,
                arrowprops=dict(arrowstyle="-", color=color, lw=0.5, shrinkA=0, shrinkB=1.5), zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9))


def title_block(fig, title, sheet, scale_note):
    fig.text(0.012, 0.985, "ODD LAYER", fontsize=13, weight="bold", va="top", color=INK)
    fig.text(0.095, 0.985, f"GS-05 GIFT SLIDE  ·  {title}", fontsize=13, va="top", color=INK)
    fig.text(0.988, 0.985, f"Sheet {sheet}", fontsize=10, va="top", ha="right", color=INK)
    fig.text(0.012, 0.012,
             "Units: mm. Generated from gs/params.py (all outlines are slices of the generated solids). "
             f"{scale_note}  General tolerance ±0.2 mm, as printed (0.4 mm nozzle, 0.20 mm layers, PLA). "
             "CAD-validated only: not yet printed or tested.",
             fontsize=7.5, color="#55595f")


# ------------------------------------------------------------------ sheet 1: assembly


def sheet_assembly(tray, lid):
    fig = plt.figure(figsize=(16.5, 11.7))
    title_block(fig, "Assembly: plan, sections and edge detail", "1 / 3", "Views 1:1 unless marked.")
    lidc = G.lid_placed(P, 0.0, lid_m=lid)

    # ---- plan view ----------------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.43, 0.47, 0.52])
    ax.set_title("PLAN (lid closed; dashed: lid at the open stop)", loc="left", fontsize=9, color=INK)
    fill(ax, tray.project().to_polygons(), TRAY_F, lw=0.8)
    fill(ax, lidc.project().to_polygons(), LID_F, lw=0.7, z=2)
    outline(ax, G.lid_placed(P, P.travel, lid_m=lid).project().to_polygons(), "#b14a45", 0.6, "--", 3)
    outline(ax, tray.slice(P.floor_t + 0.2).to_polygons(), "#8a8478", 0.5, ":", 2)   # pocket & hole (hidden)
    L, W = P.L, P.W
    dim(ax, (0, -W / 2), (L, -W / 2), -10, f"{L:.1f}")
    dim(ax, (0, -W / 2), (0, W / 2), 13, f"{W:.1f}")
    x0 = P.end_wall
    dim(ax, (x0, P.pocket_w / 2), (x0 + P.pocket_l, P.pocket_w / 2), 12.5, f"pocket {P.pocket_l:.1f}")
    dim(ax, (x0 + P.pocket_l, -P.pocket_w / 2), (x0 + P.pocket_l, P.pocket_w / 2), -6, f"{P.pocket_w:.2f}")
    dim(ax, (P.end_wall, -W / 2), (P.end_wall + P.travel, -W / 2), -17, f"lid travel to the open stop {P.travel:.0f}")
    label(ax, (P.push_hole_x - 3, -5.5), f"Ø{P.push_hole_d:.0f} push hole\nin the floor (hidden)", (-27, -24))
    label(ax, (P.end_wall + P.dish_x + 5, 6), f"thumb dish Ø{P.dish_d:.0f} × {P.dish_depth}", (0, 47))
    label(ax, (P.end_wall + P.beam_x0 + 22, P.panel_y + 0.4), "flexure slots, inside the shadow gap", (36, 47))
    label(ax, (P.L - 1.2, 22), "open end", (L + 6, 40))
    label(ax, (0.6, 22), "closed end", (-27, 40))
    ax.annotate("", xy=(P.L + 30, 0), xytext=(P.L + 8, 0),
                arrowprops=dict(arrowstyle="-|>", color="#b14a45", lw=1.4, mutation_scale=14))
    ax.text(P.L + 19, 2, "OPEN", color="#b14a45", fontsize=9, ha="center", weight="bold")
    for xs, nm in ((50.0, "A"),):
        ax.plot([xs, xs], [-W / 2 - 3, W / 2 + 3], color=INK, lw=0.6, ls="-.")
        ax.text(xs, W / 2 + 4, nm, ha="center", fontsize=10, weight="bold")
        ax.text(xs, -W / 2 - 3.5, nm, ha="center", fontsize=10, weight="bold", va="top")
    ax.plot([-3, P.L + 3], [0, 0], color=INK, lw=0.6, ls="-.")
    ax.text(-4.0, 1.2, "B", ha="right", va="bottom", fontsize=10, weight="bold")
    ax.set_xlim(-28, P.L + 70)
    ax.set_ylim(-W / 2 - 26, W / 2 + 22)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- section A-A --------------------------------------------------------------------
    ax = fig.add_axes([0.53, 0.60, 0.45, 0.33])
    ax.set_title("SECTION A–A (x = 50), with card", loc="left", fontsize=9, color=INK)
    fill(ax, sec_x(tray, 50.0), CUT_T, hatch="////", lw=0.6)
    fill(ax, sec_x(lidc, 50.0), CUT_L, hatch="\\\\\\\\", lw=0.6)
    fill(ax, sec_x(G.card(P), 50.0), "#24364a", lw=0.3)
    H = P.H
    dim(ax, (-W / 2, 0), (-W / 2, H), 4, f"{H:.1f}")
    dim(ax, (-P.pocket_w / 2, P.floor_t), (-P.pocket_w / 2, P.z_ledge), 3, f"{P.pocket_depth:.1f}", fs=7)
    dim(ax, (-14, 0), (-14, P.floor_t), -3, f"{P.floor_t:.1f}", fs=7)
    dim(ax, (14, P.z_ledge), (14, H), 3, f"lid {P.lid_t:.1f}", fs=7)
    dim(ax, (-W / 2, H), (W / 2, H), 4, f"{W:.1f}")
    ax.text(0, P.floor_t + P.card_t + 0.5, "card 0.76  +  2.44 headroom for folded notes", ha="center", fontsize=7,
            color="#24364a")
    ax.set_xlim(-W / 2 - 9, W / 2 + 6)
    ax.set_ylim(-3, H + 7)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- section B-B --------------------------------------------------------------------
    ax = fig.add_axes([0.53, 0.43, 0.45, 0.17])
    ax.set_title("SECTION B–B (y = 0), lid closed", loc="left", fontsize=9, color=INK)
    fill(ax, sec_y(tray, 0.0), CUT_T, hatch="////", lw=0.5)
    fill(ax, sec_y(lidc, 0.0), CUT_L, hatch="\\\\\\\\", lw=0.5)
    dim(ax, (0, H), (P.end_wall, H), 2.5, f"{P.end_wall:.1f}", fs=7)
    dim(ax, (P.L - P.open_wall, 0), (P.L, 0), -2.5, f"{P.open_wall:.1f}", fs=7)
    dim(ax, (P.end_wall, H), (P.L, H), 5.5, f"lid {P.lid_l:.1f}", fs=7)
    label(ax, (P.push_hole_x, 0.6), "push hole", (P.push_hole_x - 4, -6))
    label(ax, (P.message_x, P.floor_t - 0.2), f"'{P.message}' deboss {P.message_depth}", (P.message_x + 6, -6))
    label(ax, (P.L * 0.62, 0.2), f"logo deboss {P.logo_depth} (underside)", (P.L * 0.62 + 10, -6))
    ax.set_xlim(-4, P.L + 4)
    ax.set_ylim(-9, H + 9)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- detail C: the edge, 10:1 --------------------------------------------------------
    ax = fig.add_axes([0.03, 0.05, 0.62, 0.36])
    ax.set_title("DETAIL C: lid edge in the tray groove, at the parked detent bump (x = %.1f). Scale 10:1"
                 % P.bump_closed_x, loc="left", fontsize=9, color=INK)
    xc = P.bump_closed_x
    fill(ax, sec_x(tray, xc), CUT_T, hatch="////", lw=0.6)
    fill(ax, sec_x(lidc, xc), CUT_L, hatch="\\\\\\\\", lw=0.6)
    zs = P.z_ledge
    yf, yg, yl, ym = P.land_y, P.y_g, P.y_lip, P.panel_y
    dim(ax, (yf, zs - 0.15), (yg, zs - 0.15), -0.35, f"{P.lid_clear:.2f}", fs=7)
    dim(ax, (yg, zs + 0.6), (yg + P.relief_d, zs + 0.6), 0.0, f"relief {P.relief_d:.2f}", fs=6.5, ext=False)
    dim(ax, (yf, zs + 1.0), (yf + P.bump_p, zs + 1.0), 0.0, "", fs=6.5, ext=False)
    label(ax, (yf + P.bump_p * 0.5, zs + 0.5), f"bump {P.bump_p:.2f} proud\n(×{P.bump_h:.1f} high)", (yf + 2.2, zs - 1.6))
    dim(ax, (yg + P.relief_d, zs - 0.3), (P.W / 2, zs - 0.3), -0.55, f"{P.wall_behind:.2f}", fs=7)
    dim(ax, (ym, P.H), (yl, P.H), 0.5, f"shadow gap {yl - ym:.2f}", fs=7)
    dim(ax, (ym, P.H - 1.4), (ym + P.slot_w, P.H - 1.4), 0.0, f"slot {P.slot_w:.2f}", fs=6.5, ext=False)
    dim(ax, (P.beam_in, zs - 0.15), (yf, zs - 0.15), -1.05, f"beam {P.beam_w:.2f}", fs=7)
    dim(ax, (yl, zs + 2.9), (yf, zs + 2.9), 0.0, f"overlap {yf - yl:.2f}", fs=6.5, ext=False)
    dim(ax, (yf + 1.6, zs), (yf + 1.6, zs + P.land_h), 0.0, f"{P.land_h:.1f}", fs=6.5, ext=False)
    dim(ax, (ym - 1.0, zs), (ym - 1.0, P.H), 0.0, f"{P.lid_t:.1f}", fs=6.5, ext=False)
    dim(ax, (ym - 0.3, P.H - P.rebate_d), (ym - 0.3, P.H), 0.0, "", fs=6, ext=False)
    label(ax, (P.beam_in + 0.35, P.H - P.rebate_d), f"rebate {P.rebate_d} (beam top)", (ym - 4.2, P.H + 0.9))
    label(ax, ((yf + yl) / 2 - 0.15, zs + P.land_h + 0.45), "45° dovetail,\n0.21 normal gap", (yf - 4.2, zs + 4.0))
    label(ax, (yg + P.relief_d * 0.5, zs + P.z_junction), "0.45 ceiling overhang\n(prints unsupported)",
          (yg + 1.4, zs + 3.9))
    label(ax, (P.W / 2 - 0.3, P.H - 0.3), f"{P.top_chamfer} × 45°", (P.W / 2 + 0.6, P.H + 0.9))
    ax.set_xlim(P.panel_y - 4.5, P.W / 2 + 2.5)
    ax.set_ylim(zs - 2.4, P.H + 1.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- key data table --------------------------------------------------------------------
    ax = fig.add_axes([0.67, 0.05, 0.31, 0.35])
    ax.axis("off")
    r = Dt.summary(P)
    rows = [
        ("Parts", "Tray + Lid (2), no hardware, no glue"),
        ("Outside size", f"{P.L:.1f} × {P.W:.1f} × {P.H:.1f} mm"),
        ("Holds", f"ID-1 card {P.card_l} × {P.card_w} × {P.card_t} + notes folded in quarters"),
        ("Pocket", f"{P.pocket_l:.1f} × {P.pocket_w:.2f} × {P.pocket_depth:.1f} mm"),
        ("Lid travel", f"{P.travel:.0f} mm to a firm stop; card {72:.0f} % uncovered"),
        ("Fit, per side", f"{P.lid_clear:.2f} lateral, 0.21 normal on the 45° dovetail"),
        ("Detent beam", f"{P.beam_len:.0f} × {P.beam_w} mm fixed-fixed, k ≈ {r['k']:.1f} N/mm"),
        ("Opening click", f"≈ {r['F_open_r1']:.1f} N (model; 2.0–5.7 N over print variation)"),
        ("Closing click", f"≈ {r['F_close_r1']:.1f} N"),
        ("Open stop", f"≈ {r['F_stop']:.0f} N to pull the lid off (6–19 N)"),
        ("Fitting the lid", f"≈ {r['F_insert']:.1f} N snap-in"),
        ("Beam strain", f"{r['strain_max'] * 100:.2f} % nominal, ≤ 0.71 % worst case"),
        ("Lid variants", f"Standard · Loose (−{LOOSE:.2f}/side) · Snug (+{SNUG:.2f}/side)"),
        ("Print", "both parts flat, no supports, 0.20 mm layers"),
    ]
    y = 0.98
    ax.text(0, y, "KEY DATA", fontsize=10, weight="bold", color=INK, va="top")
    y -= 0.07
    for k, v in rows:
        ax.text(0.0, y, k, fontsize=8, color="#55595f", va="top")
        ax.text(0.33, y, v, fontsize=8, color=INK, va="top")
        y -= 0.066
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"GS05_drawing_assembly.{ext}"), dpi=170 if ext == "png" else None)
    plt.close(fig)


# ------------------------------------------------------------------ sheet 2: parts


def sheet_parts(tray, lid, lid_star):
    fig = plt.figure(figsize=(16.5, 11.7))
    title_block(fig, "Parts: lid and tray detent track", "2 / 3", "Plans 1:1, detail D 6:1.")
    # ---- lid plan -----------------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.50, 0.46, 0.44])
    ax.set_title("LID, top view (print this face up). Star variant shown dashed.", loc="left", fontsize=9, color=INK)
    fill(ax, lid.project().to_polygons(), LID_F, lw=0.8)
    outline(ax, lid.slice(P.lid_t - 0.05).to_polygons(), "#7a2a26", 0.5)
    outline(ax, lid_star.slice(P.lid_t - 0.05).to_polygons(), "#7a2a26", 0.5, "--")
    Ll = P.lid_l
    dim(ax, (0, -P.land_y), (Ll, -P.land_y), -6, f"{Ll:.1f}")
    dim(ax, (0, -P.land_y), (0, P.land_y), 5, f"{2 * P.land_y:.1f} at the land")
    dim(ax, (Ll, -P.panel_y), (Ll, P.panel_y), -5, f"top {2 * P.panel_y:.1f}")
    dim(ax, (0, P.land_y), (P.beam_x0, P.land_y), 4, f"{P.beam_x0:.0f}", fs=7)
    dim(ax, (P.beam_x0, P.land_y), (P.beam_x1, P.land_y), 4, f"flexure slot {P.beam_len:.0f} × {P.slot_w}", fs=7)
    dim(ax, (0, -P.land_y), (P.bump_x, -P.land_y), -12, f"bump centre {P.bump_x:.0f}", fs=7)
    dim(ax, (0, 0), (P.dish_x, 0), -13, f"{P.dish_x:.0f}", fs=7)
    label(ax, (P.dish_x + 4, 4), f"thumb dish Ø{P.dish_d:.0f}, {P.dish_depth} deep", (P.dish_x + 10, 17))
    label(ax, (P.star_x, P.star_r * 0.7), f"Star variant: {P.star_depth} deep\n(3 layers: swap filament → gold inlay)",
          (P.star_x - 18, 21))
    label(ax, (P.bump_x, P.land_y + 0.5), "bump", (P.bump_x + 6, P.land_y + 9))
    ax.set_xlim(-14, Ll + 14)
    ax.set_ylim(-P.land_y - 18, P.land_y + 14)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- lid end view -------------------------------------------------------------------
    ax = fig.add_axes([0.52, 0.72, 0.46, 0.20])
    ax.set_title("LID, section at the bump (x = %.0f). 2:1" % P.bump_x, loc="left", fontsize=9, color=INK)
    fill(ax, sec_x(lid, P.bump_x), CUT_L, hatch="\\\\\\\\", lw=0.5)
    dim(ax, (-P.land_y, 0), (P.land_y, 0), -1.6, f"{2 * P.land_y:.1f}")
    dim(ax, (P.land_y + P.bump_p, 0), (P.land_y + P.bump_p, P.bump_h), 1.0, f"{P.bump_h}", fs=7)
    dim(ax, (-P.land_y, 0), (-P.land_y, P.lid_t), 1.2, f"{P.lid_t}", fs=7)
    ax.set_xlim(-P.land_y - 4, P.land_y + 4)
    ax.set_ylim(-4, P.lid_t + 2)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- tray plan ----------------------------------------------------------------------
    ax = fig.add_axes([0.52, 0.36, 0.46, 0.36])
    ax.set_title("TRAY, top view: pocket, message, lip line, relief tracks (in the walls, hidden)", loc="left",
                 fontsize=9, color=INK)
    fill(ax, tray.project().to_polygons(), TRAY_F, lw=0.8)
    outline(ax, tray.slice(P.H - 0.05).to_polygons(), INK, 0.6)
    outline(ax, tray.slice(P.floor_t - 0.1).to_polygons(), "#8a8478", 0.5)
    outline(ax, tray.slice(P.z_ledge + 0.6).to_polygons(), "#1f5fa8", 0.5, ":")
    dim(ax, (0, -P.W / 2), (P.L, -P.W / 2), -5, f"{P.L:.1f}")
    dim(ax, (P.push_hole_x, 0), (P.push_hole_x, 0), 0, "")
    dim(ax, (0, -P.W / 2), (P.push_hole_x, -P.W / 2), -11, f"{P.push_hole_x:.0f}", fs=7)
    dim(ax, (0, -P.W / 2), (P.message_x, -P.W / 2), -17, f"{P.message_x:.0f}", fs=7)
    dim(ax, (P.L, -P.y_lip), (P.L, P.y_lip), -5, f"rim opening {2 * P.y_lip:.1f}")
    ax.set_xlim(-8, P.L + 14)
    ax.set_ylim(-P.W / 2 - 22, P.W / 2 + 6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- detail D: relief track profile -------------------------------------------------
    ax = fig.add_axes([0.03, 0.05, 0.94, 0.28])
    ax.set_title("DETAIL D: the detent track in each groove face, plan view, lid closed (bump parked). "
                 "Y exaggerated 6×; X true.", loc="left", fontsize=9, color=INK)
    prof = np.array(P.relief_profile())
    ys = 6.0
    xs = np.r_[prof[:, 0]]
    yy = (P.y_g + prof[:, 1] - P.y_g) * ys
    ax.fill_between(xs, yy, 4.5, color=CUT_T, hatch="////", ec=INK, lw=0.5)
    ax.plot(xs, yy, color=INK, lw=0.8)
    u, yb = Dt.bump_shape(P, 400)
    for s, col, nm in ((0.0, CUT_L, "parked"), (P.travel, "#f7c9c6", "at the open stop")):
        bx = P.bump_closed_x + s + u
        ax.fill_between(bx, (-P.lid_clear) * ys - 0.6, (-P.lid_clear + yb) * ys, color=col, ec=INK, lw=0.5)
        ax.text(P.bump_closed_x + s, (-P.lid_clear) * ys - 1.1, f"bump {nm}", ha="center", va="top", fontsize=7)
    ax.axhline(-P.lid_clear * ys, color="#b14a45", lw=0.5, ls="--")
    ax.text(P.L + 0.5, -P.lid_clear * ys, "lid land", fontsize=7, va="center", color="#b14a45")
    ax.text(P.L + 0.5, 0, "groove face", fontsize=7, va="center")
    pts = dict(zip(["s", "a0", "a1", "a2", "a3", "a4", "a5", "b0", "b1", "e1", "L", "e"], prof[:, 0]))
    notes = [
        ((pts["a1"] + pts["a2"]) / 2, "parking\npocket"),
        ((pts["a3"] + pts["a4"]) / 2, f"R1 crest\nopen {P.r1_open_deg:.0f}° / close {P.r1_close_deg:.0f}°"),
        ((pts["a5"] + pts["b0"]) / 2, f"travel track, {P.relief_d} deep: bump runs free (beam unloaded)"),
        ((pts["b0"] + pts["b1"]) / 2, f"open stop\n{P.stop_deg:.0f}° flank"),
        ((pts["b1"] + pts["e1"]) / 2, "entry\nzone"),
        ((pts["e1"] + P.L) / 2, "lead-in"),
    ]
    for i, (x, t) in enumerate(notes):
        ax.text(x, 3.9 + (1.9 if i % 2 else 0.0), t, ha="center", va="bottom", fontsize=7)
    for k in ("a1", "a3", "a5", "b0", "e1"):
        ax.plot([pts[k]] * 2, [P.relief_d * ys, 3.8], color="#9a9a9a", lw=0.4, ls=":")
        ax.text(pts[k], -3.6, f"{pts[k]:.2f}", ha="center", fontsize=6.5, color=DIM, rotation=90, va="top")
    ax.set_xlim(14, P.L + 7)
    ax.set_ylim(-7.5, 9.5)
    ax.set_yticks([])
    ax.set_xlabel("x from the closed end of the tray (mm)")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"GS05_drawing_parts.{ext}"), dpi=170 if ext == "png" else None)
    plt.close(fig)


# ------------------------------------------------------------------ sheet 3: detent charts


def sheet_detent():
    corners = {
        "nominal": (0.0, 0.0),
        "tight (tray −0.15, lid +0.05)": (-0.15, 0.05),
        "loose (tray +0.10, lid −0.05)": (0.10, -0.05),
    }
    cols = {"nominal": "#1f5fa8", "tight (tray −0.15, lid +0.05)": "#c0392b", "loose (tray +0.10, lid −0.05)": "#7f8c8d"}
    res = {k: Dt.summary(P, *v) for k, v in corners.items()}
    fig = plt.figure(figsize=(16.5, 10.0))
    title_block(fig, "Detent model: deflection and force through the travel", "3 / 3",
                "Model: fixed-fixed beam, E 3.0 GPa, μ 0.30.")
    gs = fig.add_gridspec(2, 3, left=0.05, right=0.98, top=0.92, bottom=0.08, hspace=0.32, wspace=0.22)
    zones = [("R1: leaving / entering the closed position", -0.3, 5.0),
             ("Full travel", -0.3, P.travel + 3.0),
             ("Open stop and lid removal", P.travel - 2.0, P.travel + 3.0)]
    for j, (ttl, a, b) in enumerate(zones):
        ax = fig.add_subplot(gs[0, j])
        for k, r in res.items():
            c = r["curves"]
            m = (c["s"] >= a) & (c["s"] <= b)
            ax.plot(c["s"][m], c["d"][m], color=cols[k], lw=1.2, label=k)
        ax.set_title(ttl, fontsize=9, loc="left")
        ax.set_xlabel("lid travel s (mm)")
        ax.set_ylabel("beam deflection (mm)")
        ax.grid(True, lw=0.3)
        if j == 0:
            ax.legend(fontsize=7, loc="upper right")
        ax2 = fig.add_subplot(gs[1, j])
        for k, r in res.items():
            c = r["curves"]
            m = (c["s"] >= a) & (c["s"] <= b)
            ax2.plot(c["s"][m], c["f_open"][m], color=cols[k], lw=1.2)
            ax2.plot(c["s"][m], -c["f_close"][m], color=cols[k], lw=1.0, ls="--")
        ax2.axhline(0, color=INK, lw=0.5)
        ax2.set_xlabel("lid travel s (mm)")
        ax2.set_ylabel("push needed (N): + opening, − closing (dashed)")
        ax2.grid(True, lw=0.3)
        r = res["nominal"]
        if j == 0:
            ax2.annotate(f"opening click {r['F_open_r1']:.1f} N", xy=(1.2, r["F_open_r1"]), xytext=(2.6, r["F_open_r1"] + 1.5),
                         fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.6))
            ax2.annotate(f"closing click {r['F_close_r1']:.1f} N", xy=(2.9, -r["F_close_r1"]),
                         xytext=(2.6, -r["F_close_r1"] - 2.5), fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.6))
        if j == 2:
            ax2.annotate(f"stop: {r['F_stop']:.0f} N to pull the lid off", xy=(P.travel + 0.45, r["F_stop"]),
                         xytext=(P.travel + 0.9, r["F_stop"] + 2.0), fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.6))
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"GS05_detent_model.{ext}"), dpi=150 if ext == "png" else None)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    tray, lid, lid_star = G.tray(P), G.lid(P), G.lid(P, star=True)
    sheet_assembly(tray, lid)
    sheet_parts(tray, lid, lid_star)
    sheet_detent()
    print("docs written to", OUT)


if __name__ == "__main__":
    main()
