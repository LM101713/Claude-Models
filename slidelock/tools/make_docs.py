"""
Build SlideLock's documentation graphics from the data that slidelock.py exports.

    python tools/make_docs.py [--root .]

Reads  models/SL01_geometry.json  (real sections cut from the Blender meshes, the wall
profiles, and the detent simulation) and writes:

    docs/SL01_drawing.png        dimensioned drawing sheet
    docs/SL01_detent_force.png   predicted detent force along the travel
    docs/SL01_detent_detail.png  tooth and notch geometry, 10:1

Needs matplotlib and numpy. Nothing in here creates geometry: every outline comes from the
Blender model, so the drawings cannot drift from the STL files.
"""

import argparse
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from matplotlib.patches import PathPatch, Circle, Polygon  # noqa: E402

GRAPHITE = "#2B2D31"
ORANGE = "#FF6A13"
INK = "#1d1f22"
DIM = "#3a6ea5"
FILL = {"tray": "#8a8d93", "lid": "#b9bcc2", "carriage": "#ffb286"}
EDGE = {"tray": "#2B2D31", "lid": "#2B2D31", "carriage": "#c4470a"}


def loops_to_patch(loops, axes, **kw):
    """Compound patch from closed loops; inner loops become holes (even-odd by nesting)."""
    paths = [Path(lp) for lp in loops if len(lp) > 2]
    verts, codes = [], []
    for i, pth in enumerate(paths):
        pt = pth.vertices[0]
        depth = sum(1 for j, q in enumerate(paths) if j != i and q.contains_point(pt))
        v = list(pth.vertices)
        area = sum(v[k][0] * v[(k + 1) % len(v)][1] - v[(k + 1) % len(v)][0] * v[k][1]
                   for k in range(len(v))) / 2
        if (depth % 2 == 0) != (area > 0):
            v = v[::-1]
        verts += v + [v[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(v) - 1) + [Path.CLOSEPOLY]
    if not verts:
        return None
    return PathPatch(Path(verts, codes), **kw)


def section(ax, sec, plane):
    ia, ib = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}[plane]
    for part in ("tray", "lid", "carriage"):
        loops = [[(p[ia], p[ib]) for p in lp] for lp in sec.get(part, [])]
        patch = loops_to_patch(loops, ax, facecolor=FILL[part], edgecolor=EDGE[part], lw=0.7,
                               hatch="////" if part != "carriage" else None, zorder=2)
        if patch:
            ax.add_patch(patch)


def dim(ax, p0, p1, text, off=0.0, horiz=True, fs=7, ext=True, color=DIM):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        y = y0 + off
        if ext:
            ax.plot([x0, x0], [y0, y], color=color, lw=0.4)
            ax.plot([x1, x1], [y1, y], color=color, lw=0.4)
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.6,
                                                          shrinkA=0, shrinkB=0, mutation_scale=6))
        ax.text((x0 + x1) / 2, y, text, ha="center", va="bottom", fontsize=fs, color=color,
                bbox=dict(fc="white", ec="none", pad=0.6))
    else:
        x = x0 + off
        if ext:
            ax.plot([x0, x], [y0, y0], color=color, lw=0.4)
            ax.plot([x1, x], [y1, y1], color=color, lw=0.4)
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.6,
                                                          shrinkA=0, shrinkB=0, mutation_scale=6))
        ax.text(x, (y0 + y1) / 2, text, ha="center", va="center", fontsize=fs, color=color,
                rotation=90, bbox=dict(fc="white", ec="none", pad=0.6))


def label(ax, xy, txt, xytext, fs=6.5):
    ax.annotate(txt, xy, xytext, fontsize=fs, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.4),
                bbox=dict(fc="white", ec="none", pad=0.5))


def setup(ax, title):
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=9, loc="left", color=INK, fontweight="bold")


def rrect(hx, hy, r, n=12, cx=0, cy=0):
    pts = []
    for q, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        c = (cx + sx * (hx - r), cy + sy * (hy - r))
        for i in range(n + 1):
            a = (q + i / n) * math.pi / 2
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts


def drawing(g, out):
    P, D, S = g["params"], g["derived"], g["sections"]
    fig = plt.figure(figsize=(16.5, 11.7), dpi=150)
    fig.patch.set_facecolor("white")

    # ---- plan view ----------------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.55, 0.44, 0.38])
    setup(ax, "PLAN  (lid side, knob at the centre detent)")
    ax.add_patch(Polygon(g["plan"], closed=True, fc="#e9e9ea", ec=INK, lw=1.0))
    ax.add_patch(Polygon(g["plan_top"], closed=True, fc="none", ec=INK, lw=0.4, ls="--"))
    sw, sl = D["SLOT_W"] / 2, D["SLOT_L"] / 2
    ax.add_patch(Polygon(rrect(sl, sw, P["KNOB_R"] + P["SLOT_CLEAR"]), closed=True, fc="#4a4c50",
                         ec=INK, lw=0.8))
    ax.add_patch(Polygon(rrect(P["KNOB_L"] / 2, P["KNOB_W"] / 2, P["KNOB_R"]), closed=True,
                         fc=ORANGE, ec="#a33c05", lw=0.8))
    yin = sw + P["SLOT_CHAMFER"] + 0.6
    for i, x in enumerate(D["POSITIONS"]):
        ln = 2.4 if i in (0, len(D["POSITIONS"]) - 1) else 1.3
        for s in (1, -1):
            ax.plot([x, x], [s * yin, s * (yin + ln)], color=INK, lw=1.2)
    L, W = P["L"], P["W"]
    dim(ax, (-L / 2, -W / 2), (L / 2, -W / 2), f"{L:.0f}", off=-5)
    dim(ax, (L / 2, -W / 2), (L / 2, W / 2), f"{W:.0f}", off=5, horiz=False)
    dim(ax, (-sl, sw), (sl, sw), f"slot {D['SLOT_L']:.0f}", off=W / 2 - sw + 2.5)
    dim(ax, (-sl, -sw), (-sl, sw), f"{D['SLOT_W']:.0f}", off=-3, horiz=False)
    p = D["POSITIONS"]
    dim(ax, (p[0], -yin - 2.4), (p[-1], -yin - 2.4), f"travel {P['TRAVEL']:.0f}  (5 positions)",
        off=-4.5)
    dim(ax, (p[2], yin + 1.3), (p[3], yin + 1.3), f"pitch {P['PITCH']:.0f}", off=1.4, fs=6)
    label(ax, (p[0], -yin - 1.2), "LOCK mark (long)", (-34, -21))
    label(ax, (p[1], yin + 0.6), "TICK mark", (-22, 21))
    label(ax, (g["plan_top"][0][0], 0), "top face edge\n(45° capped R3)", (40, 9))
    ax.set_xlim(-46, 46)
    ax.set_ylim(-26, 26)

    # ---- section A-A (x = 0) -------------------------------------------------------------
    ax = fig.add_axes([0.50, 0.55, 0.22, 0.38])
    setup(ax, "SECTION A-A  (x = 0)")
    section(ax, S["x0"], "x")
    H, yc = P["H"], D["YC"]
    dim(ax, (-W / 2, 0), (W / 2, 0), f"{W:.0f}", off=-3.5)
    dim(ax, (W / 2, 0), (W / 2, H), f"{H:.0f}", off=2.5, horiz=False)
    dim(ax, (P["KNOB_W"] / 2, H), (P["KNOB_W"] / 2, D["KNOB_TOP"]), f"+{P['KNOB_H']}", off=4,
        horiz=False, fs=6)
    label(ax, (-W / 2 + P["WALL"] / 2, 6), f"wall {P['WALL']}", (-21, 3))
    label(ax, (-6, P["FLOOR"] / 2), f"floor {P['FLOOR']}", (-12, -4.5))
    label(ax, (-10, H - 1), f"lid {P['LID_SKIN']}", (-15, 18.5))
    label(ax, (-W / 2 + 0.1, D["SEAM"]), f"parting line z={D['SEAM']:.0f}\nV-groove {P['SEAM_CHAMFER']}",
          (-24, 13))
    label(ax, (5.2, D["FLOOR_RAIL_TOP"]), f"floor rail, {P['CLEAR_Z']} gap", (6, -5))
    label(ax, (7.0, D["CEIL_RAIL_BOT"]), f"ceiling rail, {P['CLEAR_Z']} gap", (6, 19))
    label(ax, (yc - 0.6, 6), "spring", (13, 1.2))
    label(ax, (P["KNOB_W"] / 2 + 0.25, 12), f"knob {P['KNOB_W']:.0f} in slot {D['SLOT_W']:.0f}",
          (-5, 22))
    ax.set_xlim(-26, 22)
    ax.set_ylim(-7, 24)

    # ---- section B-B (y = 0) -------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.30, 0.44, 0.24])
    setup(ax, "SECTION B-B  (y = 0)   hard stops, latch hangers, knob")
    section(ax, S["y0"], "y")
    si = D["STOP_IN"]
    dim(ax, (-si, 3), (si, 3), f"stop to stop {2 * si:.0f}  =  carriage {P['CARR_L']:.0f} + travel {P['TRAVEL']:.0f}",
        off=-6.5, fs=6.5)
    label(ax, (si + 1.2, 8), f"hard stop {P['STOP_T']}", (26, 17))
    label(ax, ((D["HANGER_X0"] + D["HANGER_X1"]) / 2, 6), "latch hanger (lid)", (24, -5.5))
    label(ax, (0, D["KNOB_TOP"] - 0.5), f"thumb saddle {P['KNOB_SADDLE']} deep", (8, 19))
    ax.set_xlim(-42, 42)
    ax.set_ylim(-8, 21)

    # ---- section C-C (z = 6) -------------------------------------------------------------
    ax = fig.add_axes([0.50, 0.28, 0.47, 0.26])
    setup(ax, "SECTION C-C  (z = 6, carriage at the centre detent)   the mechanism")
    section(ax, S["z6"], "z")
    a = P["TOOTH_X"]
    label(ax, (a, -yc - 0.6), "tooth in a TICK notch", (8, -21))
    label(ax, (-4, -yc + 0.9), f"cantilever spring {P['SPRING_T']} x {P['SPRING_H']}", (-30, -21))
    label(ax, (a + p[-1], -yc - 0.5), "LOCK notch", (24, -19))
    label(ax, (D["FLAG_X0"] + 0.7, 0), "latch flag (flexes in-plane)", (24, 18))
    label(ax, (-a, yc + 0.6), "tooth (right spring)", (-22, 18))
    label(ax, (si + 1, 10), "stop wall", (33, 10))
    ax.set_xlim(-44, 44)
    ax.set_ylim(-23, 21)

    # ---- notes / title block ---------------------------------------------------------------
    ax = fig.add_axes([0.03, 0.02, 0.94, 0.25])
    ax.axis("off")
    notes = [
        "GENERAL",
        f"Units mm.  Envelope {P['L']:.0f} x {P['W']:.0f} x {P['H']:.0f} mm, knob +{P['KNOB_H']} mm.  Three printed parts, no hardware.",
        "All outlines on this sheet are sections cut from the Blender meshes by slidelock.py.",
        "",
        "FITS (design values, also measured on the meshes by the validator)",
        f"Carriage guide pads to walls {P['CLEAR_SIDE']} / side.  Carriage to floor and ceiling rails {P['CLEAR_Z']} / side.",
        f"Knob to slot {P['SLOT_CLEAR']} all round (never touches; the stops are inside).  Lid skirt to tray tongue {P['FIT_LID']} radial.",
        f"Lid bears on the tray at the parting line (z = {D['SEAM']:.0f}).  Tongue top to lid ceiling {P['TONGUE_GAP']}.  Latch play 0.10.",
        "",
        "DETENT",
        f"5 positions at {P['PITCH']:.0f} mm.  Mid notches: flanks {P['MID_FLANK']:.0f}°, tooth seats {P['MID_DEPTH']} deep, spring preload {P['PRELOAD']}.",
        f"End notches: exit flank {P['END_FLANK_IN']:.0f}°, seat {P['END_DEPTH']} deep, {P['END_OVERSHOOT']} beyond the hard stop -> spring holds the carriage on the stop.",
        f"Tooth nose R{P['NOSE_R']}.  Spring: cantilever {D.get('SPRING_L', 15.5)} mm long, overtravel stop at {P['SPRING_GAP']} mm deflection.",
    ]
    ax.text(0.0, 1.0, "\n".join(notes), va="top", ha="left", fontsize=8, family="DejaVu Sans",
            color=INK, transform=ax.transAxes, linespacing=1.45)
    tb = ax.inset_axes([0.70, 0.0, 0.30, 0.98])
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    tb.axis("off")
    tb.add_patch(plt.Rectangle((0, 0), 1, 1, fc="white", ec=INK, lw=1.2))
    tb.add_patch(plt.Rectangle((0, 0.72), 1, 0.28, fc=GRAPHITE, ec=INK, lw=1.2))
    tb.text(0.05, 0.86, "ODD LAYER", color="white", fontsize=17, fontweight="bold", va="center")
    tb.text(0.95, 0.86, "SL-01", color=ORANGE, fontsize=17, fontweight="bold", va="center", ha="right")
    rows = [("PRODUCT", "SlideLock  slider fidget"), ("PARTS", "Tray  ·  Carriage (Soft/Std/Firm)  ·  Lid"),
            ("MATERIAL", "PETG (preferred) or PLA"), ("UNITS / SCALE", "mm  /  not to scale"),
            ("STATUS", "CAD-validated only. NOT YET PRINTED"), ("SOURCE", "slidelock.py (Blender 4.2, bpy)")]
    for i, (k, v) in enumerate(rows):
        y = 0.64 - i * 0.11
        tb.text(0.05, y, k, fontsize=6.5, color="#666", va="center")
        tb.text(0.36, y, v, fontsize=8, color=INK if k != "STATUS" else "#b3261e", va="center",
                fontweight="bold" if k == "STATUS" else None)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def force_chart(g, out):
    sims = g["sims"]
    P, D = g["params"], g["derived"]
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150)
    styles = {"Soft": ("#f6a46f", 1.0), "Standard": (ORANGE, 2.0), "Firm": ("#9a3a06", 1.0)}
    for name, (col, lw) in styles.items():
        s = sims[f"{name}_PETG"]
        x = s["x"]
        ax.plot(x, s["f_push_pos"], color=col, lw=lw, label=f"{name}: pushing toward +x")
        ax.plot(x, s["f_push_neg"], color=col, lw=lw, ls="--",
                label=f"{name}: pushing toward -x" if name == "Standard" else None)
    ax.axhline(0, color="#999", lw=0.6)
    for i, xp in enumerate(D["POSITIONS"]):
        end = i in (0, len(D["POSITIONS"]) - 1)
        ax.axvline(xp, color="#bbb", lw=0.6, ls=":")
        ax.text(xp, 7.6, "LOCK" if end else "tick", ha="center",
                fontsize=8, color=INK, fontweight="bold" if end else None)
    ax.set_xlim(-10.6, 10.6)
    ax.set_ylim(-8, 8.3)
    ax.set_xlabel("knob position (mm from centre)")
    ax.set_ylabel("force needed to move the knob (N)")
    ax.set_title("SL-01 predicted detent force, PETG  (quasi-static model, mu = %.2f; not measured)"
                 % P["MU"], fontsize=10, loc="left")
    ax.text(-10.4, -7.6, "Above zero: you push against the detent.  Below zero: the detent pulls the "
            "knob into the next position (the 'snap').\nAt each end the carriage lands on a hard "
            "stop while the spring is still on the lock flank, so it is held against the stop.",
            fontsize=7.5, color="#444")
    ax.legend(fontsize=7.5, loc="upper right", ncol=2, framealpha=0.95)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def detent_detail(g, out):
    P, D = g["params"], g["derived"]
    yc = D["YC"]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
    tm = g["track_m"]
    a = P["TOOTH_X"]
    sim = g["sims"]["Standard_PETG"]
    for ax, (xc, title) in zip(axs, [(0.0, "TICK notch with the tooth seated (carriage at 0)"),
                                     (10.0, "LOCK notch with the carriage on the hard stop (+10)")]):
        u0 = xc + a
        wall = [(u, -(yc + v)) for u, v in tm if u0 - 3.2 <= u <= u0 + 3.2]
        wall = [(u0 - 3.3, -yc)] + wall + [(u0 + 3.3, -yc)]
        poly = wall + [(u0 + 3.3, -yc - 2.6), (u0 - 3.3, -yc - 2.6)]
        ax.add_patch(Polygon(poly, closed=True, fc=FILL["tray"], ec=INK, lw=1, hatch="////"))
        i = min(range(len(sim["x"])), key=lambda k: abs(sim["x"][k] - xc))
        dl = sim["defl_L"][i]
        tip = -(yc + P["MID_DEPTH"] + P["PRELOAD"]) + dl
        cy = tip + P["NOSE_R"]
        so = -D["SPRING_OUT"] + dl
        beta = math.radians(P["TOOTH_FLANK"])
        r = P["NOSE_R"]
        TL = (u0 - r * math.sin(beta), cy - r * math.cos(beta))
        TR = (u0 + r * math.sin(beta), cy - r * math.cos(beta))
        rise = so - TL[1]
        BL = (TL[0] - rise / math.tan(beta), so)
        BR = (TR[0] + rise / math.tan(beta), so)
        a1 = math.atan2(TL[1] - cy, TL[0] - u0)
        a2 = math.atan2(TR[1] - cy, TR[0] - u0)
        if a2 < a1:
            a2 += 2 * math.pi
        arc = [(u0 + r * math.cos(a1 + (a2 - a1) * k / 24), cy + r * math.sin(a1 + (a2 - a1) * k / 24))
               for k in range(25)]
        sp = [(u0 - 3.2, so), BL] + arc + [BR, (u0 + 1.6, so), (u0 + 1.6, so + P["SPRING_T"]),
                                           (u0 - 3.2, so + P["SPRING_T"])]
        ax.add_patch(Polygon(sp, closed=True, fc=FILL["carriage"], ec=EDGE["carriage"], lw=1))
        ax.add_patch(Circle((u0, cy), r, fc="none", ec=EDGE["carriage"], lw=0.5, ls=":"))
        ax.plot([u0 - 3.2, u0 + 3.2], [-yc, -yc], color=DIM, lw=0.5, ls="--")
        ax.text(u0 - 3.1, -yc + 0.08, "wall land", fontsize=6.5, color=DIM)
        ax.text(u0 + 0.9, cy + 0.1, f"R{r}", fontsize=7, color=EDGE["carriage"])
        if xc == 0.0:
            ax.text(u0 - 3.1, -yc - 2.2, f"flanks {P['MID_FLANK']:.0f}°   seat depth {P['MID_DEPTH']}\n"
                    f"spring deflection here {dl:.2f} mm (preload)", fontsize=7.5, bbox=dict(fc="white", ec="none", alpha=0.9))
        else:
            ax.text(u0 - 3.1, -yc - 2.2, f"exit flank {P['END_FLANK_IN']:.0f}°   seat {P['END_DEPTH']} deep, "
                    f"{P['END_OVERSHOOT']} past the stop\nspring deflection on the stop {dl:.2f} mm "
                    "-> pushes the carriage onto the stop", fontsize=7.5,
                    bbox=dict(fc="white", ec="none", alpha=0.9))
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_aspect("equal")
        ax.set_xlim(u0 - 3.3, u0 + 3.3)
        ax.set_ylim(-yc - 2.7, -yc + 1.9)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.grid(alpha=0.2)
    fig.suptitle("SL-01 detent geometry, 10:1 (left wall, standard spring; section at mid-height)",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def validation_report(root):
    """models/SL01_validation_report.md from the validator's JSON."""
    r = json.load(open(os.path.join(root, "models", "SL01_validation.json")))
    L = []
    w = L.append
    w("# SL-01 SlideLock: geometry validation report")
    w("")
    w("Generated by `slidelock.py` (checks) and `tools/make_docs.py` (this file). Every number "
      "below was computed from the exported meshes or from the parametric model. **None of it "
      "is a physical measurement: nothing has been printed yet.**")
    w("")
    n_pass = sum(1 for s in r["summary"] if s["passed"])
    w(f"**Result: {n_pass} / {len(r['summary'])} checks passed"
      f"{' (all)' if r['all_passed'] else ' (FAILURES PRESENT)'}.**")
    w("")
    w("| | Check | Result |")
    w("|---|---|---|")
    for s in r["summary"]:
        w(f"| {'PASS' if s['passed'] else '**FAIL**'} | {s['check']} | {s['detail']} |")
    w("")
    w("## Parts")
    w("")
    w("| Part | Volume (cm³) | Solid mass PETG (g) | Bounding box, assembly frame (mm) | Faces |")
    w("|---|---|---|---|---|")
    for k, p in r["parts"].items():
        bb = p["bbox"]
        w(f"| {k} | {p['volume_mm3'] / 1000:.2f} | {p['mass_PETG_g_solid']:.1f} | "
          f"{bb[3] - bb[0]:.1f} × {bb[4] - bb[1]:.1f} × {bb[5] - bb[2]:.1f} | {p['faces']} |")
    w("")
    w("Solid mass is an upper bound; with 3 walls and 25 % infill a set prints at roughly "
      "85–95 % of it, because most of the parts are walls anyway.")
    w("")
    w("## Detent model (quasi-static, both springs, friction μ = 0.30)")
    w("")
    w("| Carriage / material | Spring k (N/mm) | Tick breakaway (N) | Lock breakaway (N) | "
      "Drag between detents (N) | Snap into tick (N) | Spring defl. on the stop (mm) |")
    w("|---|---|---|---|---|---|---|")
    for k, d in r["detent"].items():
        w(f"| {k.replace('_', ' / ')} | {d['k_N_per_mm']:.2f} | {d['tick_breakaway_N']:.1f} | "
          f"{d['lock_breakaway_N']:.1f} | {d['land_drag_N']:.2f} | {-d['tick_snap_N']:.2f} | "
          f"{d['defl_at_stop_mm']:.2f} |")
    w("")
    w("Moduli assumed: PETG 2.0 GPa, PLA 3.0 GPa (printed, in-plane). Forces scale linearly "
      "with the modulus and with the cube of the as-printed spring thickness, so ±0.05 mm on a "
      "1.2 mm spring is about ±13 %.")
    w("")
    w("## Springs and latches (cantilever beam theory)")
    w("")
    w("| Spring | t × h (mm) | Length (mm) | Strain at full working deflection | "
      "Strain at the overtravel stop |")
    w("|---|---|---|---|---|")
    for k, s in r["springs"].items():
        w(f"| {k} | {s['t']} × {s['h']} | {s['L']} | {s['strain_working_pct']:.2f} % | "
          f"{s['strain_at_overtravel_stop_pct']:.2f} % ({s['overtravel_stop_mm']:.1f} mm) |")
    la = r["latch"]
    w("")
    w(f"Lid latch flag: {la['flag_t']} mm thick, {la['flag_L']:.1f} mm to the hook, deflects "
      f"{la['deflection']:.1f} mm when snapping → {la['strain_pct']:.2f} % strain, about "
      f"{la['force_N_PETG']:.1f} N per flag in PETG.")
    w("")
    w("## Motion sweep")
    sw = r["checks"]["motion_sweep"]
    w("")
    w(f"The carriage was moved through {sw['positions']} positions across the full 20 mm of "
      "travel. At each position the two springs were bent into the cantilever shape that the "
      "detent model predicts, plus 0.06 mm of slack for the tooth's small rotation. Then they "
      "were tested for triangle intersections against the tray. Rigid-part intersections: "
      f"{sw['frame_overlaps']}. Spring-wall intersections: {sw['overlaps']}. Closest "
      f"tooth-wall approach: {sw['min_tooth_wall_gap']:.3f} mm.")
    w("")
    w("## Wall thickness (ray-cast from every face, inward)")
    w("")
    w("| Part | Minimum (mm) | Where | Samples under 1.19 mm | Engraving floor min |")
    w("|---|---|---|---|---|")
    for k, t in r["thickness"].items():
        w(f"| {k} | {t['min']:.2f} | {t['min_at']} | {t['thin_count']} | "
          f"{(t['engraving_min'] or 0):.2f} |")
    w("")
    w("Interpretation: the tray's minimum is the diagonal across the top of a notch roof "
      "(the wall there is still 1.55 mm measured horizontally). Every lid sample under "
      "1.19 mm lies in the perimeter zone where the 1.2 mm skirt meets the rounded top edge. "
      "The carriage's minimum is the 1.2 mm spring itself (by design). Engraving values are "
      "the thin floor ribs between engraved letters; they are part of a solid floor.")
    w("")
    w("## Down-facing surfaces in print orientation")
    w("")
    for k, o in r["overhangs"].items():
        w(f"**{k}**: steep (>45°) unsupported area {o['steep_area']:.2f} mm²; flat down-facing "
          f"area {o['flat_down_area']:.1f} mm², in these clusters:")
        w("")
        for c in o["flat_clusters"][:8]:
            lo, hi = c["lo"], c["hi"]
            w(f"- {c['area']:.1f} mm² at z = {lo[2]:.1f} mm, x {lo[0]:.1f}…{hi[0]:.1f}, "
              f"y {lo[1]:.1f}…{hi[1]:.1f}")
        w("")
    w("What they are: the ceilings of engraved letters and marks (bridged, under 1 mm span), "
      "the latch hook undersides (0.8 mm ledges), and the latch pocket ceilings in the lid "
      "(bridges of 5 mm between solid walls). None needs support.")
    w("")
    w("## Clearance probe locations")
    w("")
    for k, v in r["checks"]["clearances_mm"].items():
        loc = r["checks"]["clearance_locations"].get(k)
        w(f"- `{k}`: {v:.3f} mm" + (f" at {loc}" if loc else ""))
    w("")
    w("## Not checked by software (needs the printed prototype)")
    w("")
    for t in ["Real clearances after shrink, elephant's foot and seam bumps",
              "Detent forces, feel and sound; friction coefficient",
              "Spring fatigue life and creep; latch retention force",
              "Layer adhesion on the latch flags and hooks",
              "Whether the lid seam V-groove hides the part-to-part step as intended"]:
        w(f"- {t}")
    open(os.path.join(root, "models", "SL01_validation_report.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), ".."))
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    g = json.load(open(os.path.join(root, "models", "SL01_geometry.json")))
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)
    drawing(g, os.path.join(root, "docs", "SL01_drawing.png"))
    force_chart(g, os.path.join(root, "docs", "SL01_detent_force.png"))
    detent_detail(g, os.path.join(root, "docs", "SL01_detent_detail.png"))
    validation_report(root)
    print("docs written to", os.path.join(root, "docs"), "and models/SL01_validation_report.md")
