"""Dimensioned 2D drawings for the machined / cut steel parts.

All numbers come from config.py, so the drawings always match the CAD.
Output: drawings/M01_split_crankpin.png, M02_main_shaft.png, M03_guide_rail.png
and one combined PDF (drawings/machined_parts.pdf).
"""

import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import config as C  # noqa: E402

OUT = os.path.join(ROOT, "drawings")
INK = "#1b1d22"
DIM = "#1f5fbf"


def dim_h(ax, x0, x1, y, text, above=True, ext_from=None):
    """Horizontal dimension from x0 to x1 at height y."""
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8, shrinkA=0, shrinkB=0))
    if ext_from is not None:
        for x in (x0, x1):
            ax.plot([x, x], [ext_from, y], color=DIM, lw=0.4)
    ax.text((x0 + x1) / 2, y + (0.6 if above else -1.4), text, color=DIM, ha="center", fontsize=7)


def dim_v(ax, x, y0, y1, text, ext_from=None):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.8, shrinkA=0, shrinkB=0))
    if ext_from is not None:
        for y in (y0, y1):
            ax.plot([ext_from, x], [y, y], color=DIM, lw=0.4)
    ax.text(x + 0.6, (y0 + y1) / 2, text, color=DIM, va="center", fontsize=7, rotation=90)


def title_block(fig, part_no, name, material, qty, notes):
    fig.text(0.02, 0.965, f"{part_no}  {name}", fontsize=14, weight="bold", color=INK)
    fig.text(0.02, 0.935, f"Material: {material}    Qty: {qty} per engine / {qty*50} for 50 units    "
             f"Units: mm    V10 display engine (original design)", fontsize=8, color=INK)
    y = 0.10
    for n in notes:
        fig.text(0.02, y, "- " + n, fontsize=7.5, color=INK)
        y -= 0.022


def _stepped_side(ax, segments, y0=0.0):
    """Draw a turned part from (length, dia, label) list; returns x positions."""
    x = 0.0
    xs = [0.0]
    for length, dia, *_ in segments:
        ax.add_patch(Rectangle((x, y0 - dia / 2), length, dia, fill=True, fc="#d9dde3", ec=INK, lw=0.9))
        x += length
        xs.append(x)
    ax.plot([-2, x + 2], [y0, y0], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    return xs


def crankpin(pdf):
    fig = plt.figure(figsize=(11.7, 8.3))
    ax = fig.add_axes([0.05, 0.40, 0.55, 0.50])
    ax2 = fig.add_axes([0.62, 0.40, 0.35, 0.50])
    sl, bw, fw, el = C.PIN_SHOULDER_L, C.BEARING_686["w"], C.PIN_FLYWEB_T, C.PIN_END_LEN
    d, ds = C.PIN_DIA, C.PIN_SHOULDER_D
    off = C.SPLIT_DIST
    # side view: journal B side drawn offset downward by the split distance
    segs_a = [(el, d), (sl, ds), (bw, d), (sl, ds)]
    segs_b = [(sl, ds), (bw, d), (sl, ds), (el, d)]
    x = 0.0
    for L, D in segs_a:
        ax.add_patch(Rectangle((x, -D / 2), L, D, fc="#d9dde3", ec=INK, lw=0.9))
        x += L
    x_web0 = x
    web_h = ds + off
    ax.add_patch(Rectangle((x, -off - ds / 2), fw, web_h, fc="#c5cad2", ec=INK, lw=0.9))
    x += fw
    for L, D in segs_b:
        ax.add_patch(Rectangle((x, -off - D / 2), L, D, fc="#d9dde3", ec=INK, lw=0.9))
        x += L
    total = x
    ax.plot([-2, x_web0 + fw + 1], [0, 0], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    ax.plot([x_web0 - 1, total + 2], [-off, -off], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    # D-flat indication (top of end A, bottom of end B - radially outward)
    ax.plot([0, el], [d / 2 - C.PIN_DFLAT] * 2, color=INK, lw=0.9)
    ax.plot([total - el, total], [-off + d / 2 - C.PIN_DFLAT] * 2, color=INK, lw=0.9)
    # tapped holes
    for x0, yc, sgn in ((0, 0, 1), (total, -off, -1)):
        ax.add_patch(Rectangle((x0 if sgn > 0 else x0 - C.PIN_TAP_DEPTH, yc - C.M3_TAP / 2),
                               C.PIN_TAP_DEPTH, C.M3_TAP, fc="white", ec=INK, lw=0.6, ls="--"))
    top = d / 2 + 2.5
    xs = [0, el, el + sl, el + sl + bw, el + 2 * sl + bw, el + 2 * sl + bw + fw]
    labels = [f"{el:g}", f"{sl:g}", f"{bw:g} +0.10/+0.05", f"{sl:g}", f"{fw:g}"]
    for i, lab in enumerate(labels):
        dim_h(ax, xs[i], xs[i + 1], top + (1.8 if i % 2 else 0), lab, ext_from=d / 2)
    dim_h(ax, 0, total, top + 5.5, f"{total:.2f} overall", ext_from=d / 2)
    dim_v(ax, -2.5, -d / 2, d / 2, f"Ø{d:g} g6")
    dim_v(ax, el + sl + 0.2 + bw / 2 - 1.5, -ds / 2, ds / 2, "")
    ax.text(el + sl + bw / 2, -d / 2 - 2.2, f"Ø{d:g} g6 journal\n(686 bearing seat)", ha="center", fontsize=7, color=DIM)
    ax.text(el + sl / 2, -ds / 2 - 4.8, f"shoulders Ø{ds:g}", ha="center", fontsize=7, color=DIM)
    dim_v(ax, total + 2.5, -off, 0, f"{off:.3f} ±0.01")
    ax.text(el / 2, d / 2 + 0.3, "D-flat", fontsize=6.5, ha="center", color=INK)
    ax.set_xlim(-6, total + 8)
    ax.set_ylim(-off - 10, top + 9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("SIDE VIEW (end A = front journal)", fontsize=9, loc="left")

    # end view looking from end A
    r = C.CRANK_R
    a0 = 0.0
    a1 = math.radians(C.SPLIT_ANGLE)
    pa = (0.0, 0.0)
    pb = (r * math.sin(a1) - 0, r * math.cos(a1) - r)
    for (cx, cy), fl in ((pa, 0.0), (pb, C.SPLIT_ANGLE)):
        ax2.add_patch(Circle((cx, cy), ds / 2, fc="#c5cad2", ec=INK, lw=0.8))
    for (cx, cy), fl in ((pa, 0.0), (pb, C.SPLIT_ANGLE)):
        ax2.add_patch(Circle((cx, cy), d / 2, fc="#d9dde3", ec=INK, lw=0.9))
        # D-flat line (radially outward from the crank axis, which is at (0, -r))
        t = math.radians(fl)
        nx, ny = math.sin(t), math.cos(t)
        h = d / 2 - C.PIN_DFLAT
        w = math.sqrt((d / 2) ** 2 - h ** 2)
        mx, my = cx + nx * h, cy + ny * h
        ax2.plot([mx - ny * w, mx + ny * w], [my + nx * w, my - nx * w], color=INK, lw=1.2)
        ax2.add_patch(Circle((cx, cy), C.M3_TAP / 2, fc="white", ec=INK, lw=0.6))
    ax2.plot([0, 0], [-r - 2, 4], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    ax2.plot([0, pb[0] * 1.5], [-r, -r + (pb[1] + r) * 1.5], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    ax2.add_patch(Circle((0, -r), 0.4, color=INK))
    ax2.text(0.6, -r - 0.8, "crank axis (reference only)", fontsize=6.5)
    ax2.text(-6.5, 5.2, f"journal B is {C.SPLIT_ANGLE:g}° from journal A\n"
                        f"about the crank axis at R{r:g}\n"
                        f"= {off:.3f} mm centre offset", fontsize=7, color=DIM)
    ax2.text(pa[0] - 7.5, pa[1] - 1, "A", fontsize=9, weight="bold")
    ax2.text(pb[0] + 4.2, pb[1] - 1, "B", fontsize=9, weight="bold")
    ax2.set_xlim(-9, 11)
    ax2.set_ylim(-r - 3, 10)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("END VIEW from end A", fontsize=9, loc="left")
    title_block(fig, "M01", "Split crankpin", "Stainless 303 / 416 (or 1144 steel, black oxide)", 5, [
        "Both journals Ø6 g6 (-0.004/-0.012), Ra 0.4 or better - they carry the 686 bearing inner rings.",
        f"Journal centre offset {off:.3f} ±0.01 at {C.SPLIT_ANGLE:g}° about the crank axis (R{r:g}). All other dims ±0.05.",
        f"D-flats {C.PIN_DFLAT:g} deep, each facing radially AWAY from the crank axis (see end view). Flats key the pin into the printed webs.",
        f"Both ends tapped M3 x {C.PIN_TAP_DEPTH:g} deep (tap drill Ø2.5). Break all edges 0.2. Shoulder faces square to axis within 0.02.",
        "Journal B side mirrors journal A (same lengths). The side view is drawn in the plane of the offset.",
        "The part is symmetric end-for-end: it cannot be fitted the wrong way round.",
        "Suggested process: turn Ø12 bar, journal A + shoulder; re-chuck on 4.07 offset (or mill-turn) for journal B; mill the stadium web and flats.",
    ])
    fig.savefig(os.path.join(OUT, "M01_split_crankpin.png"), dpi=160)
    pdf.savefig(fig)
    plt.close(fig)


def main_shaft(pdf):
    fig = plt.figure(figsize=(11.7, 8.3))
    ax = fig.add_axes([0.05, 0.40, 0.58, 0.50])
    ax2 = fig.add_axes([0.66, 0.42, 0.32, 0.46])
    segs = [(C.SHAFT_SPIGOT_L, C.SHAFT_SPIGOT_D), (C.SHAFT_FLANGE_T, C.SHAFT_FLANGE_D),
            (C.SHAFT_SHOULDER_L, C.SHAFT_SHOULDER_D), (C.SHAFT_JOURNAL_L, C.SHAFT_D)]
    xs = _stepped_side(ax, segs)
    total = xs[-1]
    top = C.SHAFT_FLANGE_D / 2 + 3
    names = ["spigot", "flange", "shoulder", "Ø8 journal + pulley"]
    for i, (L, D) in enumerate(segs):
        dim_h(ax, xs[i], xs[i + 1], top + (2.5 if i % 2 else 0), f"{L:.2f}", ext_from=D / 2)
    dim_h(ax, 0, total, top + 6, f"{total:.2f} overall", ext_from=C.SHAFT_FLANGE_D / 2)
    x_flat = xs[3] + C.BEARING_608["w"] + 1.0
    ax.plot([x_flat, total], [C.SHAFT_D / 2 - C.SHAFT_FLAT_DEPTH] * 2, color=INK, lw=0.9)
    dim_h(ax, xs[3], x_flat, -C.SHAFT_D / 2 - 3, f"{x_flat - xs[3]:.1f}", above=False, ext_from=-C.SHAFT_D / 2)
    ax.text((x_flat + total) / 2, C.SHAFT_D / 2 + 0.6, f"flat {C.SHAFT_FLAT_DEPTH:g} deep (pulley grub screws)", fontsize=6.5, ha="center")
    for i, (L, D) in enumerate(segs):
        ax.text(xs[i] + L / 2, -D / 2 - 1.6 - (2.2 if i == 1 else 0), f"Ø{D:g}" + (" h6" if i == 3 else ""), fontsize=7, ha="center", color=DIM)
    ax.set_xlim(-4, total + 4)
    ax.set_ylim(-C.SHAFT_FLANGE_D / 2 - 7, top + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("SIDE VIEW", fontsize=9, loc="left")
    # end view of flange (from the journal side)
    R = C.SHAFT_FLANGE_D / 2
    ax2.add_patch(Circle((0, 0), R, fc="#d9dde3", ec=INK, lw=0.9))
    ax2.add_patch(Circle((0, 0), C.SHAFT_SHOULDER_D / 2, fc="#c5cad2", ec=INK, lw=0.7))
    ax2.add_patch(Circle((0, 0), C.SHAFT_D / 2, fc="#b9bec6", ec=INK, lw=0.7))
    ax2.add_patch(Circle((0, 0), C.SHAFT_FLANGE_PCD / 2, fill=False, ec=DIM, lw=0.5, ls="--"))
    for a in C.SHAFT_FLANGE_BOLT_ANGLES:
        t = math.radians(a)
        ax2.add_patch(Circle((C.SHAFT_FLANGE_PCD / 2 * math.sin(t), C.SHAFT_FLANGE_PCD / 2 * math.cos(t)),
                             C.M3_CLEAR / 2, fc="white", ec=INK, lw=0.8))
    w = C.SHAFT_ACCESS_HOLE_D / 2
    ax2.add_patch(Polygon([(-w, C.CRANK_R), (-w, R + 0.5), (w, R + 0.5), (w, C.CRANK_R)], fc="white", ec="white"))
    ax2.add_patch(Circle((0, C.CRANK_R), w, fc="white", ec=INK, lw=0.8))
    ax2.plot([-w, -w], [C.CRANK_R, math.sqrt(R * R - w * w)], color=INK, lw=0.8)
    ax2.plot([w, w], [C.CRANK_R, math.sqrt(R * R - w * w)], color=INK, lw=0.8)
    ax2.text(0, R + 1.5, f"access notch {C.SHAFT_ACCESS_HOLE_D:g} wide, R{w:g} end at {C.CRANK_R:g} from centre", ha="center", fontsize=6.5, color=DIM)
    ax2.text(-R, -R - 3.2, f"3 x Ø{C.M3_CLEAR:g} thru on PCD {C.SHAFT_FLANGE_PCD:g}\nat {', '.join(f'{a:g}°' for a in C.SHAFT_FLANGE_BOLT_ANGLES)} from the notch", fontsize=7, color=DIM)
    ax2.set_xlim(-R - 3, R + 3)
    ax2.set_ylim(-R - 7, R + 4)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("FLANGE END VIEW", fontsize=9, loc="left")
    title_block(fig, "M02", "Main shaft (front and rear identical)", "Stainless 303 (or 1045, black oxide)", 2, [
        "Ø8 journal h6 (0/-0.009) for the 608 bearing; Ra 0.8. Shoulder face square to axis within 0.02 (it locates the bearing inner ring).",
        "Flange face square to axis within 0.02; spigot Ø10 -0.02/-0.05 (locates in the printed end web). Other dims ±0.05.",
        "Flange holes are clearance holes; the UNEVEN bolt pattern (110/110/140° spacing) plus the notch makes the shaft fit the web one way only.",
        "The flat is only needed on the FRONT shaft (drive pulley). Machining it on both keeps one part number.",
        "Alternative if machining capacity is short: 8 mm h6 ground rod + commercial 8 mm rigid flange coupling (lower precision; not recommended for production).",
    ])
    fig.savefig(os.path.join(OUT, "M02_main_shaft.png"), dpi=160)
    pdf.savefig(fig)
    plt.close(fig)


def rail(pdf):
    fig = plt.figure(figsize=(11.7, 5.0))
    ax = fig.add_axes([0.05, 0.40, 0.9, 0.42])
    L, d = C.RAIL_LEN, C.RAIL_DIA
    ax.add_patch(Rectangle((0, -d / 2), L, d, fc="#d9dde3", ec=INK, lw=0.9))
    ax.plot([-2, L + 2], [0, 0], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    dim_h(ax, 0, L, d / 2 + 2, f"{L:.1f} ±0.1", ext_from=d / 2)
    dim_v(ax, L + 1.5, -d / 2, d / 2, f"Ø{d:g} h6")
    ax.set_xlim(-4, L + 8)
    ax.set_ylim(-5, 7)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.02, 0.93, "M03  Piston guide rail", fontsize=14, weight="bold", color=INK)
    fig.text(0.02, 0.88, f"Material: 3 mm ground stainless rod (h6)    Qty: 10 per engine / 500 for 50 units", fontsize=8)
    for i, n in enumerate([
        "Cut from 3 mm h6 ground stainless linear rod (not drill rod - needs corrosion resistance and a polished surface).",
        "Both ends: 0.3 x 45° chamfer, deburred so they do not scratch the bronze bushings. Length ±0.1.",
        "The rail is the ONLY thing the piston slides on (two oil-impregnated bronze bushings). Keep it clean; one drop of light oil at assembly.",
    ]):
        fig.text(0.02, 0.25 - i * 0.06, "- " + n, fontsize=7.5)
    fig.savefig(os.path.join(OUT, "M03_guide_rail.png"), dpi=160)
    pdf.savefig(fig)
    plt.close(fig)


def pulley_spacer(pdf):
    fig = plt.figure(figsize=(11.7, 5.0))
    ax = fig.add_axes([0.05, 0.35, 0.4, 0.5])
    ax2 = fig.add_axes([0.55, 0.35, 0.4, 0.5])
    od, idd, t = 11.5, 8.2, C.SPACER_T
    ax.add_patch(Rectangle((0, idd / 2), t, (od - idd) / 2, fc="#d9dde3", ec=INK))
    ax.add_patch(Rectangle((0, -od / 2), t, (od - idd) / 2, fc="#d9dde3", ec=INK))
    ax.plot([-2, t + 2], [0, 0], color=INK, lw=0.4, ls=(0, (6, 2, 1, 2)))
    dim_h(ax, 0, t, od / 2 + 1.5, f"{t:g} ±0.02", ext_from=od / 2)
    ax.set_xlim(-4, t + 6); ax.set_ylim(-9, 10); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("SECTION", fontsize=9, loc="left")
    ax2.add_patch(Circle((0, 0), od / 2, fc="#d9dde3", ec=INK))
    ax2.add_patch(Circle((0, 0), idd / 2, fc="white", ec=INK))
    ax2.text(0, -od / 2 - 1.5, f"OD {od:g} -0.1 (must stay inside the 608 inner ring)   ID {idd:g} +0.05", ha="center", fontsize=7, color=DIM)
    ax2.set_xlim(-10, 10); ax2.set_ylim(-9, 8); ax2.set_aspect("equal"); ax2.axis("off")
    fig.text(0.02, 0.93, "M04  Pulley spacer", fontsize=14, weight="bold", color=INK)
    fig.text(0.02, 0.88, "Material: stainless 303    Qty: 1 per engine / 50 for 50 units", fontsize=8)
    for i, n in enumerate([
        "Sits on the front main shaft between the 608 inner ring and the 60T pulley hub; clamps the crank's axial position.",
        "Faces flat and parallel within 0.02. Break edges 0.2. Can be parted off Ø12 bar in the same set-up as M02.",
    ]):
        fig.text(0.02, 0.2 - i * 0.06, "- " + n, fontsize=7.5)
    fig.savefig(os.path.join(OUT, "M04_pulley_spacer.png"), dpi=160)
    pdf.savefig(fig)
    plt.close(fig)


def build():
    os.makedirs(OUT, exist_ok=True)
    with PdfPages(os.path.join(OUT, "machined_parts.pdf")) as pdf:
        crankpin(pdf)
        main_shaft(pdf)
        rail(pdf)
        pulley_spacer(pdf)


if __name__ == "__main__":
    build()
    print("drawings written to", OUT)
