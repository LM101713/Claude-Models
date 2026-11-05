"""
Drawings, kinematics chart, motion strip and the validation report for ML-02 MotionLoop.

Reads models/ML02_validation.json and models/ML02_geometry.json (written by motionloop.py);
needs only numpy + matplotlib (no Blender).

    python tools/make_docs.py
"""

import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402

ROOT = os.environ.get("ML02_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")
DOCS = os.path.join(ROOT, "docs")
RENDERS = os.path.join(ROOT, "renders")

INK = "#1d1e21"
DIM = "#c2410c"
FILL = {"frame": "#5b5d63", "crank": "#e9e4da", "rod_A": "#d9d3c7", "rod_B": "#d9d3c7",
        "slider_A": "#ff6a13", "slider_B": "#ff6a13"}
WHEEL_FILL = "#ff8a45"


def load():
    with open(os.path.join(MODELS, "ML02_validation.json")) as f:
        rep = json.load(f)
    with open(os.path.join(MODELS, "ML02_geometry.json")) as f:
        geo = json.load(f)
    return rep, geo


# ---------------------------------------------------------------------------------------
# section drawing helpers
# ---------------------------------------------------------------------------------------


def _area(poly):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))


def _inside(pt, poly):
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def draw_section(ax, lines, axes, parts_filter=None, lw=0.7, fill=True):
    """lines: [{body, part, pts}] ; axes: (i, j) coordinate indices to plot."""
    i, j = axes
    by_part = {}
    for ln in lines:
        if parts_filter and not parts_filter(ln):
            continue
        key = (ln["body"], ln["part"])
        loop = [(p[i], p[j]) for p in ln["pts"]]
        if len(loop) < 3:
            continue
        by_part.setdefault(key, []).append(loop)
    for (body, part), loops in by_part.items():
        col = WHEEL_FILL if "Wheel" in part else FILL.get(body, "#bbbbbb")
        if part.endswith("Pin") and body != "crank":
            col = "#d9d3c7"
        if "Cap" in part or "Handle" in part:
            col = "#5b5d63"
        verts, codes = [], []
        for lp in loops:
            depth = sum(_inside(lp[0], o) for o in loops if o is not lp)
            ccw = _area(lp) > 0
            if (depth % 2 == 0) != ccw:
                lp = lp[::-1]
            verts += lp + [lp[0]]
            codes += [Path.MOVETO] + [Path.LINETO] * (len(lp) - 1) + [Path.CLOSEPOLY]
        if fill:
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=col, edgecolor=INK, lw=lw,
                                   alpha=0.95, zorder=2 if body == "frame" else 3))
        else:
            ax.add_patch(PathPatch(Path(verts, codes), facecolor="none", edgecolor=INK, lw=lw, zorder=4))


def dim(ax, p0, p1, text, off=(0, 0), fs=7.5, ext=True, rot=None):
    (x0, y0), (x1, y1) = p0, p1
    ox, oy = off
    a0, a1 = (x0 + ox, y0 + oy), (x1 + ox, y1 + oy)
    ax.annotate("", a0, a1, arrowprops=dict(arrowstyle="<|-|>", color=DIM, lw=0.7,
                                            shrinkA=0, shrinkB=0, mutation_scale=7), zorder=6)
    if ext and (ox or oy):
        for (x, y), (ax_, ay_) in ((p0, a0), (p1, a1)):
            ax.plot([x, ax_], [y, ay_], color=DIM, lw=0.4, zorder=5)
    mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
    if rot is None:
        rot = 90 if abs(x1 - x0) < abs(y1 - y0) else 0
    ax.text(mx, my, text, color=DIM, fontsize=fs, ha="center", va="center", rotation=rot,
            bbox=dict(fc="white", ec="none", pad=0.6), zorder=7)


def label(ax, xy, txt, xytext, fs=7):
    ax.annotate(txt, xy, xytext, fontsize=fs, color=INK, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.5), zorder=8)


# ---------------------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------------------


def drawing(rep, geo):
    P = rep["params"]
    D = rep["derived"]
    fig = plt.figure(figsize=(16.5, 11.7), dpi=150)
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1.0], height_ratios=[1.0, 1.08],
                          left=0.04, right=0.985, top=0.93, bottom=0.05, wspace=0.10, hspace=0.18)
    fig.text(0.04, 0.965, "ODD LAYER  ML-02  MOTIONLOOP", fontsize=17, weight="bold", color=INK)
    fig.text(0.04, 0.945, "General arrangement - all dimensions in mm - crank at 0 deg (pin A at +X), "
             "MIRROR wheel - sections cut from the Blender meshes - CAD only, not yet printed",
             fontsize=9, color="#555")

    # --- front section y = 0 -------------------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    ax.set_title("A  Front section near the wheel mid-plane (y = 1)", loc="left", fontsize=10)
    draw_section(ax, geo["front_y0"], (0, 2))
    za = P["AXLE_Z"]
    top = D["PLINTH_TOP"]
    L = P["L"]
    ax.axhline(za, color="#999", lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=1)
    ax.axvline(0, color="#999", lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=1)
    dim(ax, (-L / 2, 0), (L / 2, 0), f"{L:.0f}", off=(0, -7))
    dim(ax, (L / 2, 0), (L / 2, top), f"{top:.1f}", off=(5, 0))
    dim(ax, (-L / 2, 0), (-L / 2, za), f"{za:.0f} axle", off=(-6, 0))
    dim(ax, (-P["WHEEL_R"], za), (P["WHEEL_R"], za), f"Ø{2 * P['WHEEL_R']:.0f}",
        off=(0, P["WHEEL_R"] + 4))
    s0, s1 = D["PIN_STROKE"]
    xs = -(P["ROD_L"] + P["CRANK_R"])
    dim(ax, (-s1, za), (-s0, za), f"stroke {s1 - s0:.0f}", off=(0, 13))
    dim(ax, (s0, za), (s1, za), f"stroke {s1 - s0:.0f}", off=(0, 13))
    dim(ax, (P["PIT_X"], P["PIT_FLOOR"]), (P["PIT_X"], top), f"pit {top - P['PIT_FLOOR']:.1f}",
        off=(-3, 0), fs=6.5)
    label(ax, (-s0 - 3, P["SLIDER_TOP"] - 1), "slider A (left)", (-60, 36))
    label(ax, (s0 + 3, P["SLIDER_TOP"] - 1), "slider B (right)", (36, 36))
    label(ax, (-P["CRANK_R"] - 1, za + 9), "crank wheel", (-28, 40))
    label(ax, (-30, top - 2.5), "dovetail groove", (-50, -6))
    ax.set_xlim(-66, 66)
    ax.set_ylim(-14, 46)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- Y stack section x = 0 -------------------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    ax.set_title("B  Cross-section through the crank axis (x = 0)", loc="left", fontsize=10)
    draw_section(ax, geo["stack_x0"], (1, 2))
    ax.axhline(za, color="#999", lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=1)
    ys = [("wheel", D["Y_WHEEL"]), ("rod", D["Y_ROD1"]), ("cheek", D["Y_CHEEK1"]),
          ("tower", D["Y_TOWER1"])]
    y0 = -D["Y_WHEEL"]
    dim(ax, (-D["Y_WHEEL"], za + 17), (D["Y_WHEEL"], za + 17), f"{2 * D['Y_WHEEL']:.0f}", fs=6.5)
    dim(ax, (D["Y_ROD0"], za - 17.5), (D["Y_ROD1"], za - 17.5), f"{P['ROD_T']}", fs=6.5)
    dim(ax, (D["Y_CHEEK0"], za + 15), (D["Y_CHEEK1"], za + 15), f"{P['CHEEK_T']:.0f}", fs=6.5)
    dim(ax, (D["Y_TOWER0"], za + 9.5), (D["Y_TOWER1"], za + 9.5), "tower", fs=6.5)
    dim(ax, (-P["W"] / 2, 0), (P["W"] / 2, 0), f"{P['W']:.0f}", off=(0, -6))
    dim(ax, (-D["Y_ARM1"], 0), (D["Y_CAP0"] + P["CAP_T"], 0), "", off=(0, -12))
    ax.text(0, -13.6, f"{D['Y_ARM1'] + D['Y_CAP0'] + P['CAP_T']:.1f} handle arm to cap", fontsize=7,
            color=DIM, ha="center", bbox=dict(fc="white", ec="none", pad=0.5))
    label(ax, (-D["Y_ARM0"] - 2, za + 4), "handle", (-36, 40))
    label(ax, (D["Y_CAP0"] + 1, za + 3), "cap", (24, 36))
    label(ax, (D["Y_CHEEK0"] + 2, za + 11), "cheek A", (8, 43))
    label(ax, (-D["Y_CHEEK0"] - 2, za + 11), "cheek B", (-26, 43))
    label(ax, ((D["Y_ROD0"] + D["Y_ROD1"]) / 2, za - 1), "rod A", (12, 6))
    label(ax, (D["Y_BOSS"] + 0.2, za + 4.5), "thrust boss", (25, 30))
    ax.set_xlim(-40, 34)
    ax.set_ylim(-17, 46)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- plan -------------------------------------------------------------------------------------
    ax = fig.add_subplot(gs[1, 0])
    ax.set_title("C  Plan: plinth top (z = 13.2) and axle-height section (z = 21)", loc="left", fontsize=10)
    draw_section(ax, [ln for ln in geo["plan_z1"] if ln["body"] == "frame"], (0, 1), fill=True)
    draw_section(ax, [ln for ln in geo["plan_ztop"] if ln["body"] == "frame"], (0, 1), fill=False, lw=0.6)
    draw_section(ax, [ln for ln in geo["plan_zaxle"] if ln["body"] != "frame"], (0, 1))
    draw_section(ax, [ln for ln in geo["plan_zaxle"] if ln["body"] == "frame"], (0, 1))
    dim(ax, (-L / 2, -P["W"] / 2), (L / 2, -P["W"] / 2), f"{L:.0f}", off=(0, -8))
    dim(ax, (L / 2, -P["W"] / 2), (L / 2, P["W"] / 2), f"{P['W']:.0f}", off=(7, 0))
    dim(ax, (-P["PIT_X"], -D["Y_TOWER0"]), (P["PIT_X"], -D["Y_TOWER0"]), f"pit {2 * P['PIT_X']:.0f}",
        off=(0, -3.5), fs=6.5)
    dim(ax, (-L / 2, 0), (L / 2, 0), "", off=(0, 0), ext=False) if False else None
    ax.text(-L / 2 + 2, 24, "handle side (-Y) is at the bottom of this view", fontsize=7, color="#666")
    ax.set_xlim(-66, 66)
    ax.set_ylim(-40, 28)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- key data table ------------------------------------------------------------------------
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    ax.set_title("D  Key data", loc="left", fontsize=10)
    km = rep["kinematics"]["mirror"]
    ov = rep["overall"]["size"]
    rows = [
        ("Overall (full turn, incl. handle)", f"{ov[0]:.0f} x {ov[1]:.1f} x {ov[2]:.1f}"),
        ("Plinth", f"{P['L']:.0f} x {P['W']:.0f} x {top:.1f}"),
        ("Crank radius r / rod length l", f"{P['CRANK_R']:.0f} / {P['ROD_L']:.0f}  (l/r = {P['ROD_L'] / P['CRANK_R']:.2f})"),
        ("Stroke, each slider", f"{km['stroke_A']:.2f}"),
        ("Wrist-pin travel |x|", f"{D['PIN_STROKE'][0]:.0f} to {D['PIN_STROKE'][1]:.0f} from the axle"),
        ("Max rod angle / min transmission angle", f"{km['beta_max_deg']:.1f} / {km['transmission_min_deg']:.1f} deg"),
        ("Crank pin / wrist pin / journal", f"Ø{P['PIN_D']:.0f} / Ø{P['WRIST_D']:.0f} / Ø{P['JOURNAL_D']:.0f}"),
        ("Running fit (pins in bores)", f"+{P['RUN_DIA']:.2f} on diameter"),
        ("Tower bearing bore", f"Ø{P['BORE_D']} teardrop (+{P['BORE_D'] - P['JOURNAL_D']:.1f})"),
        ("Axial gaps (rotating faces)", f"{P['AXIAL']:.2f}"),
        ("Slider: neck / flank / underside", f"{P['SLIDE']:.2f} / {P['DOVE']:.2f} normal / {P['SLIDE_Z']:.2f}"),
        ("D-key spigot in wheel", f"{P['KEY']:.2f} per side"),
        ("Press fits (hex, pins)", "line-to-line nominal"),
        ("Crank wheels", "MIRROR 180 deg (default), SHUTTLE 0 deg"),
        ("Parts per set", "13 printed (9 designs), no hardware"),
        ("PETG, solid-volume upper bound", f"{rep['mass_g_petg_solid_upper_bound']:.0f} g"),
    ]
    y = 0.96
    for k, v in rows:
        ax.text(0.0, y, k, fontsize=8.6, color="#444", transform=ax.transAxes)
        ax.text(0.58, y, v, fontsize=8.6, color=INK, transform=ax.transAxes, weight="bold")
        y -= 0.058
    os.makedirs(DOCS, exist_ok=True)
    fig.savefig(os.path.join(DOCS, "ML02_drawing.png"))
    plt.close(fig)


def kinematics_chart(rep):
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4), dpi=150)
    for ax, cfg, title in ((axs[0], "mirror", "MIRROR wheel (pins 180 deg apart): both out together, both in together"),
                           (axs[1], "shuttle", "SHUTTLE wheel (pins in line): one out while the other comes in")):
        rows = rep["kinematics"][cfg]["rows_5deg"]
        th = [r[0] for r in rows]
        xa = [-r[1] for r in rows]  # outward distance, left slider
        xb = [r[2] for r in rows]
        ax.plot(th, xa, color="#2b2d31", lw=2, label="left slider: distance from axle")
        ax.plot(th, xb, color="#ff6a13", lw=2, ls="--", label="right slider: distance from axle")
        ax.set_xlim(0, 360)
        ax.set_xticks(range(0, 361, 45))
        ax.set_xlabel("crank angle (deg, pin A from +X)")
        ax.set_ylabel("wrist pin to axle (mm)")
        ax.set_title(title, loc="left", fontsize=10)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(DOCS, "ML02_kinematics.png"))
    plt.close(fig)


def motion_strip():
    names = [f"08_motion_{d:03d}.png" for d in (0, 90, 180, 270)]
    if not all(os.path.exists(os.path.join(RENDERS, n)) for n in names):
        return False
    fig, axs = plt.subplots(2, 2, figsize=(14, 7.8), dpi=150)
    for ax, n, d in zip(axs.flat, names, (0, 90, 180, 270)):
        ax.imshow(plt.imread(os.path.join(RENDERS, n)))
        ax.set_title(f"crank {d} deg", fontsize=10, loc="left")
        ax.axis("off")
    fig.suptitle("ML-02 MotionLoop: one turn of the crank, MIRROR wheel (side elevation from the cap side)",
                 fontsize=11, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(RENDERS, "08_motion_strip.png"))
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------


def report(rep):
    L = []
    w = L.append
    w("# ML-02 MotionLoop: validation report\n")
    w("Generated by `motionloop.py` (geometry checks on the Blender meshes) and "
      "`tools/make_docs.py`. **CAD only: nothing here has been printed or physically tested.**\n")
    w("## 1. Parts\n")
    w("| Part | Volume (mm³) | Shells | Non-manifold edges | Faces |")
    w("|---|---:|---:|---:|---:|")
    for k, s in rep["parts"].items():
        w(f"| {k} | {s['volume_mm3']:.0f} | {s['shells']} | {s['nonmanifold_edges']} | {s['faces']} |")
    w("\n## 2. Kinematics\n")
    w("| | MIRROR | SHUTTLE |")
    w("|---|---:|---:|")
    km, ks = rep["kinematics"]["mirror"], rep["kinematics"]["shuttle"]
    for key, lab, f in (("stroke_A", "Stroke, left slider (mm)", "{:.3f}"),
                        ("stroke_B", "Stroke, right slider (mm)", "{:.3f}"),
                        ("beta_max_deg", "Max rod angle (deg)", "{:.2f}"),
                        ("transmission_min_deg", "Min transmission angle (deg)", "{:.2f}"),
                        ("v_peak", "Peak slider speed per rad/s (mm)", "{:.2f}"),
                        ("a_peak", "Peak slider acceleration per (rad/s)² (mm)", "{:.2f}"),
                        ("rod_pose_error_mm", "Rod pose error, bore centres vs pins (mm)", "{:.1e}")):
        w(f"| {lab} | {f.format(km[key])} | {f.format(ks[key])} |")
    w(f"\nLeft wrist pin travels x = {km['range_A'][0]:.2f} … {km['range_A'][1]:.2f}; "
      f"right x = {km['range_B'][0]:.2f} … {km['range_B'][1]:.2f} (MIRROR).\n")
    w("## 3. Full-turn collision sweep\n")
    w("Every pair of bodies tested for triangle intersections at every 2° of crank rotation "
      "(180 poses per wheel); minimum gaps sampled every 10°.\n")
    w("| Pair | MIRROR hits | min gap (mm) at | SHUTTLE hits | min gap (mm) at | Designed |")
    w("|---|---:|---|---:|---|---|")
    exp = rep.get("expected_gaps", {})
    for pair in rep["sweep"].get("mirror", {}):
        if "|" not in pair:
            continue
        m, s = rep["sweep"]["mirror"][pair], rep["sweep"]["shuttle"][pair]
        e = exp.get(pair)
        es = f"{e['gap']:.2f} ({e['what']})" if e else "-"
        def g(r):
            return "> 6 (search limit)" if r["min_gap"] >= 5.999 else f"{r['min_gap']:.3f} @ {r['at_deg']:.0f}°"
        w(f"| {pair.replace('|', ' / ')} | {m['hits']} | {g(m)} | {s['hits']} | {g(s)} | {es} |")
    for cfg in ("mirror", "shuttle"):
        if cfg in rep["sweep"]:
            w(f"\nLowest point of the handle / knob over a turn ({cfg}): "
              f"z = {rep['sweep'][cfg]['handle_lowest_z']:.2f} mm above the table.")
    w("\n## 4. Fits inside the rigid assemblies (crank angle 0)\n")
    w("| Fit | Measured (mm) |")
    w("|---|---:|")
    for k, v in rep["designed_contacts"].items():
        w(f"| {k.replace('_', ' ')} | {v:.3f} |" if isinstance(v, float) else f"| {k.replace('_', ' ')} | {v} |")
    w("\n## 5. Print orientation: overhangs and walls\n")
    w("Overhangs measured in print orientation against a 45° limit (bed face excluded). "
      "'Flat' = horizontal downward faces (bridges). Wall thickness ray-cast from every face.\n")
    w("| Part | Height on bed | Flat down (mm²) | Steeper than 45° (mm²) | Min wall (mm) | Faces < 1.2 mm |")
    w("|---|---:|---:|---:|---:|---:|")
    for k, v in rep["print"].items():
        w(f"| {k} | {v['height']:.1f} | {v['flat_down_mm2']:.1f} | {v['steep_down_mm2']:.1f} | "
          f"{v['min_wall']:.2f} | {v['thin_count']} |")
    w("\nLargest flat / steep regions (print frame, mm):\n")
    for k, v in rep["print"].items():
        for kind in ("flat_clusters", "steep_clusters"):
            for c in v[kind][:3]:
                if c["area"] >= 0.5:
                    w(f"- {k}, {kind.split('_')[0]}: {c['area']:.1f} mm² at x {c['lo'][0]}…{c['hi'][0]}, "
                      f"y {c['lo'][1]}…{c['hi'][1]}, z {c['lo'][2]}…{c['hi'][2]}")
    w("\n## 6. Strength estimates (hand calculation, not tested)\n")
    st = rep["strength"]
    w(f"Load case: {st['load_case']}.\n")
    w("| Link | Stress (MPa) | Safety factor vs. conservative layer strength |")
    w("|---|---:|---:|")
    for k, v in st.items():
        if k.endswith("_MPa"):
            w(f"| {k[:-4].replace('_', ' ')} | {v:.2f} | {st['safety_factors_vs_layer_strength'].get(k, '-')} |")
    w(f"| rod Euler buckling load | {st['rod_euler_buckling_N']:.0f} N | — |")
    w("\nAssumed strengths: 20 MPa across layers in tension, 15 MPa in shear (printed PETG, "
      "deliberately conservative). E = 2.0 GPa.\n")
    w("## 7. Files\n")
    w("| File | Qty per set | Colour | Size in print orientation (mm) | Triangles |")
    w("|---|---:|---|---|---:|")
    for f in rep["files"]:
        w(f"| `{f['file']}` | {f['qty']} | {f['colour']} | {' x '.join(f'{s:.1f}' for s in f['size_mm'])} | {f['tris']} |")
    with open(os.path.join(MODELS, "ML02_validation_report.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    rep, geo = load()
    drawing(rep, geo)
    kinematics_chart(rep)
    ms = motion_strip()
    report(rep)
    print("docs written", "(with motion strip)" if ms else "(no motion renders yet)")


if __name__ == "__main__":
    main()
