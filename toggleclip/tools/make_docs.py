"""
Charts, the side-view drawing and the validation report for TC-03 (matplotlib + shapely only).

    python tools/make_docs.py
"""

import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402

from tc import geo as G  # noqa: E402
from tc import mech as M  # noqa: E402
from tc import parts as PT  # noqa: E402
from tc.params import P, D  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
ORANGE, GRAPH, SAND, BLUE = "#FF6A13", "#2B2D31", "#B9A98A", "#3A6EA5"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def clamp_chart(rep):
    rows = rep["mechanics"]["clamp"]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax = axs[0]
    for case, c, ls in (("PLA, Standard blade", ORANGE, "-"), ("PETG, Firm blade", BLUE, "-"),
                        ("PETG, Standard blade", BLUE, ":"), ("PLA, Firm blade", ORANGE, ":")):
        for sl, alpha in ((1.0, 1.0),):
            pts = [(r["bag"], r["clamp_N"]) for r in rows if r["case"] == case and r["slop"] == sl and r["bag"] > 0]
            lo = [r["clamp_N"] for r in rows if r["case"] == case and r["slop"] == 1.4 and r["bag"] > 0]
            hi = [r["clamp_N"] for r in rows if r["case"] == case and r["slop"] == 0.4 and r["bag"] > 0]
            x = [p[0] for p in pts]
            ax.plot(x, [p[1] for p in pts], ls, color=c, lw=2, label=case)
            if ls == "-":
                ax.fill_between(x, lo, hi, color=c, alpha=0.15, lw=0)
    ax.set_xlabel("bag thickness between the jaws (mm)")
    ax.set_ylabel("total clamp force (N)")
    ax.set_title("Clamp force (band: pin clearances 0.4x to 1.4x nominal)")
    ax.legend(frameon=False, fontsize=9)
    ax.set_ylim(0, None)
    ax.grid(alpha=0.25)
    ax = axs[1]
    P.BOW_T = 4.0
    for t, c in ((0.3, SAND), (1.0, ORANGE), (2.0, GRAPH)):
        r = M.locked(t, P.E_PLA, 1.0)
        ax.plot(r["x"], r["q"] / (2 * P.BLADE_HW), color=c, lw=2, label=f"bag {t} mm: {r['total']:.1f} N")
    ax.axvline(P.BRIDGES[0], color="0.6", lw=0.8, ls="--")
    ax.text(P.BRIDGES[0] + 1, 0.005, "bridge", color="0.45", fontsize=8)
    ax.set_xlabel("x along the clip (mm), hinge at 0")
    ax.set_ylabel("contact pressure (N/mm$^2$)")
    ax.set_title("Pressure along the bar (PLA, Standard, nominal clearances)")
    ax.legend(frameon=False, fontsize=9)
    ax.set_ylim(0, None)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "TC03_clamp_force.png"), dpi=150)
    plt.close(fig)


def stroke_chart(rep):
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax = axs[0]
    for name, c in (("PLA_bag0.5", ORANGE), ("PLA_bag2.0", GRAPH), ("PETG_bag0.5", BLUE)):
        s = np.array(rep["mechanics"]["stroke"][name])
        ax.plot(s[:, 0], s[:, 3], color=c, lw=2, label=name.replace("_", ", ").replace("bag", "bag "))
    det = rep["detent"]["PLA"]["thumb_N"]
    ax.axvspan(0.4, 1.6, color=ORANGE, alpha=0.12)
    ax.annotate(f"click detent: ~{det:.1f} N\n(PLA, both directions)", xy=(1.0, 0.0), xytext=(18, -0.25),
                fontsize=9, arrowprops=dict(arrowstyle="->", color="0.4"))
    ax.axvline(rep["mechanics"]["dead_centre_deg"], color="0.5", ls="--", lw=0.8)
    ax.text(rep["mechanics"]["dead_centre_deg"] + 0.8, ax.get_ylim()[1] * 0.85 if ax.get_ylim()[1] > 0 else 0.1,
            "dead centre", fontsize=8, color="0.4")
    ax.axhline(0, color="0.3", lw=0.6)
    ax.set_xlabel("lever angle from locked (deg)")
    ax.set_ylabel("thumb force from the toggle alone (N)")
    ax.set_title("Toggle: push needed (+) / pulls itself shut (-)")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    ax = axs[1]
    op = np.array(rep["mechanics"]["opening"])
    ax.plot(op[:, 0], op[:, 1], color=ORANGE, lw=2, label=f"at the nose end of the clamp zone (x = {P.BAR_X[1]:.0f})")
    ax.plot(op[:, 0], op[:, 2], color=GRAPH, lw=2, label="30 mm from the hinge")
    ax.set_xlabel("lever angle from locked (deg)")
    ax.set_ylabel("gap between the jaws (mm)")
    ax.set_title("Jaw opening")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "TC03_lever_stroke.png"), dpi=150)
    plt.close(fig)


def drawing():
    B = {"upper": PT.upper_bands(n_states=40), "blade": PT.blade_bands(), "lever": PT.lever_bands(),
         "bail_a": PT.bail_a_bands(), "bail_b": PT.bail_b_bands(), "pin_p": PT.pin_p_bands(), "pin_h": PT.pin_h_bands()}
    col = {"upper": GRAPH, "blade": SAND, "lever": ORANGE, "bail_a": "#55585E", "bail_b": "#55585E",
           "pin_p": "#7FBF9F", "pin_h": "#7FBF9F"}

    def prof(bands, y):
        for a, b, p in bands:
            if a <= y < b:
                return p
        return Polygon()

    fig, axs = plt.subplots(3, 1, figsize=(13, 12.5))
    for ax, (title, y, th, layers) in zip(axs, (
            ("Section on the centre line (y = 0), locked: lever, crank web, ridge in groove, detent peg", 0.05, 0.0,
             ["upper", "blade", "lever", "pin_p", "pin_h", "bail_a"]),
            ("Section through a bail plate and a hinge ear (y = 7.5), locked", 7.6, 0.0, ["upper", "bail_b", "bail_a", "pin_h", "lever"]),
            ("Centre line, lever lifted 150 deg: jaws open", 0.05, 150.0, ["upper", "blade", "lever", "pin_p", "pin_h", "bail_a"]))):
        st = M.pose(math.radians(th))
        for k in layers:
            g = PT.pose2(k, prof(B[k], y), st)
            for p in G.as_polys(g):
                xs, zs = p.exterior.xy
                ax.fill(xs, zs, color=col[k], alpha=0.85 if k != "upper" else 0.75, lw=0.6, ec="k")
                for h in p.interiors:
                    xs, zs = h.xy
                    ax.fill(xs, zs, color="w", lw=0.4, ec="k")
        for nm, pt in (("H", D["H"]), ("P", D["P"]), ("K", st["K"]), ("Q", st["Q"])):
            ax.plot(*pt, "+", color="k", ms=7)
            ax.text(pt[0] + 1.2, pt[1] + 1.2, nm, fontsize=9, weight="bold")
        ax.set_aspect("equal")
        ax.set_xlim(-10, 135)
        ax.set_ylim(-19, 31)
        ax.set_title(title, fontsize=10, loc="left")
        ax.grid(alpha=0.2)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
    ax = axs[0]
    # a few dimensions
    def dim(x0, x1, z, txt):
        ax.annotate("", (x0, z), (x1, z), arrowprops=dict(arrowstyle="<->", lw=0.8))
        ax.text((x0 + x1) / 2, z + 0.8, txt, ha="center", fontsize=8)
    dim(0, P.XP, 24, f"H - P {P.XP:.0f}")
    dim(P.BAR_X[0], P.BAR_X[1], 18, f"clamp zone {P.BAR_X[1] - P.BAR_X[0]:.0f}")
    ax.text(120, -17.5, f"PK {P.PK}   PQ {P.E_ARM}   QK {D['L_LINK']:.2f}   over-centre {P.OVER:.0f} deg", fontsize=8, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "TC03_drawing.png"), dpi=130)
    plt.close(fig)


def report(rep):
    L = ["# TC-03 ToggleClip - validation report", "",
         "Generated by `toggleclip.py` and `tools/make_docs.py`. **CAD only: nothing has been printed or",
         "physically tested.** Every number below is a model prediction.", ""]
    L += ["## Meshes", "", "| Part | Volume mm3 | Shells | Genus | Triangles |", "|---|---:|---:|---:|---:|"]
    for k, v in rep["mesh"].items():
        L.append(f"| {k} | {v['volume_mm3']:.0f} | {v['components']} | {v['genus']} | {v['triangles']} |")
    a0, a1, n = rep["sweep_degs"]
    L += ["", f"## Clearance sweep: every part pair, lever {a0:.0f} to {a1:.0f} deg in {n} steps", "",
          "Exact 2D distances between posed band profiles (the mechanism is planar and layered). Press",
          "fits are excluded here (see the 3D check). For the blade against the upper jaw, the bar",
          "(the spring's contact face) is excluded: it is pressed against the jaw whenever the jaws",
          "are near closed; its fit is checked in the locked pose below.", "",
          "| Pair | Min gap mm | At deg |", "|---|---:|---:|"]
    for k, v in sorted(rep["sweep"].items(), key=lambda kv: kv[1]["min_gap"]):
        if v["min_gap"] > 50:
            continue
        L.append(f"| {k.replace('|', ' / ')} | {v['min_gap']:.3f} | {v['at_deg']} |")
    L += ["", "The 0.000 between lever and upper jaw is the designed stop (the lever lying on the jaw).", ""]
    if rep.get("sweep_firm_blade"):
        L += ["Same sweep with the **Firm** blade fitted (pairs involving the blade):", "",
              "| Pair | Min gap mm | At deg |", "|---|---:|---:|"]
        for k, v in sorted(rep["sweep_firm_blade"].items(), key=lambda kv: kv[1]["min_gap"]):
            if v["min_gap"] < 50:
                L.append(f"| {k.replace('|', ' / ')} | {v['min_gap']:.3f} | {v['at_deg']} |")
        L.append("")
    L += ["## Locked pose", ""]
    for k, v in rep["lock_fit"].items():
        L.append(f"- {k.replace('_', ' ')}: {v['min_gap']:.3f} mm")
    L += [f"- 3D boolean overlaps (mm3), locked assembly with the bar pressed flush: {rep['lock_3d_overlaps_mm3']}",
          "  (only the three crush-rib press fits)",
          f"- Face contacts (overlap thinner than 0.01 mm, from polygon chords): {rep.get('lock_3d_contacts_mm', {})}"
          " (the lever lying on its stop)", ""]
    L += ["## Detent", ""]
    for m, v in rep["detent"].items():
        L.append(f"- {m}: finger {v['finger_k_N_per_mm']} N/mm, {v['finger_force_N']} N each, push through "
                 f"{v['push_N']} N at the peg = {v['thumb_N']} N at the thumb pad; finger stress {v['finger_stress_MPa']} MPa")
    L += ["", "## Clamp force (PLA = 3.0 GPa, PETG = 1.9 GPa effective)", "",
          "| Case | Clearances | Bag mm | Clamp N | Link N | Bow MPa |", "|---|---:|---:|---:|---:|---:|"]
    for r in rep["mechanics"]["clamp"]:
        if r["bag"] in (0.3, 1.0, 2.0):
            L.append(f"| {r['case']} | {r['slop']}x | {r['bag']} | {r['clamp_N']} | {r['link_N']} | {r['bow_MPa']} |")
    L += ["", f"Dead centre at {rep['mechanics']['dead_centre_deg']:.1f} deg of lever lift (the lock stop is at 0).", ""]
    L += ["## Strength (hand checks, abuse loads)", "", "| Item | Stress MPa | Allowable MPa | SF |", "|---|---:|---:|---:|"]
    for s in rep["strength"]:
        L.append(f"| {s['item']} | {s['stress_MPa']} | {s['allow_MPa']} | {s['SF']} |")
    L += ["", "## Printability (print orientation, slicing every 0.2 mm)", ""]
    for k, v in rep["print"].items():
        L.append(f"### {v['file']}  ({v['size_mm'][0]} x {v['size_mm'][1]} x {v['size_mm'][2]} mm, "
                 f"{'fits' if v['fits_220'] else 'DOES NOT FIT'} 220 x 220)")
        L.append(f"Orientation: {v['orientation']}.")
        if v["overhangs"]:
            L.append("Unsupported regions (material not carried by the layer below grown 45 deg):")
            for o in v["overhangs"][:6]:
                L.append(f"- z {o['z']} mm: {o['area_mm2']} mm2, span {o['span']} x {o['length']} mm at {o['at']}")
        else:
            L.append("No unsupported regions.")
        if v["thin_lt_1p2"]:
            L.append("Profile regions thinner than 1.2 mm: " + "; ".join(
                f"{t['area']} mm2 at x,z {t['at']} (y {t['y']})" for t in v["thin_lt_1p2"][:4]))
        L.append("")
    with open(os.path.join(ROOT, "models", "TC03_validation_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")


def main():
    os.makedirs(DOCS, exist_ok=True)
    rep = json.load(open(os.path.join(ROOT, "models", "TC03_validation.json")))
    clamp_chart(rep)
    stroke_chart(rep)
    drawing()
    report(rep)
    print("docs written")


if __name__ == "__main__":
    main()
