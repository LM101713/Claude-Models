#!/usr/bin/env python3
"""Dimensioned section drawings of DRYDOCK P001, cut from the real CAD (trimesh section).

    python render/drawing.py      -> renders/09_section_drawing.png, renders/10_bayonet_detail.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import drydock as dd  # noqa: E402
from build123d import Rot  # noqa: E402

OUT = HERE.parent / "renders"
FILL = {"charcoal": "#3a3d44", "orange": "#ff6a13", "clear": "#9fd3e6"}
EDGE = {"charcoal": "#111316", "orange": "#a43c00", "clear": "#3b7c95"}


def to_mesh(shape):
    v, t = shape.tessellate(0.01, 0.1)
    return trimesh.Trimesh(np.array([(p.X, p.Y, p.Z) for p in v]), np.array(t))


def section_polys(mesh):
    """Cut with the XZ plane (y=0); return shapely polygons in (x, z)."""
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    if sec is None:
        return []
    # map 3D (x, 0, z) -> 2D (x, z) explicitly so the axes stay put
    T = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
    planar, _ = sec.to_2D(to_2D=T)
    return list(planar.polygons_full)


def draw_parts(ax, asm):
    for shape, col, _ in asm:
        for poly in section_polys(to_mesh(shape)):
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color=FILL[col], ec=EDGE[col], lw=0.6, zorder=2)
            for hole in poly.interiors:
                hx, hy = hole.xy
                ax.fill(hx, hy, color="white", ec=EDGE[col], lw=0.6, zorder=3)


def dim(ax, p0, p1, text, off=(0, 0), horiz=True, fs=8.5, color="#1b4f9c"):
    (x0, y0), (x1, y1) = p0, p1
    ox, oy = off
    a0, a1 = (x0 + ox, y0 + oy), (x1 + ox, y1 + oy)
    ax.annotate("", a0, a1, arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.8,
                                              shrinkA=0, shrinkB=0, mutation_scale=7), zorder=6)
    for (px, py), (qx, qy) in ((p0, a0), (p1, a1)):
        ax.plot([px, qx], [py, qy], color=color, lw=0.4, zorder=5)
    mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
    ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color, zorder=7,
            rotation=0 if horiz else 90, bbox=dict(fc="white", ec="none", pad=0.6))


def main():
    P = dd.Params()
    D = P.d()
    parts = dd.build_parts(P, sizes=[P.spool_bore])
    L = D["L_body"]
    # turn the locked assembly -90 deg so a lug sits in the cut plane on the +x side
    asm = [(Rot(0, 0, -P.travel_deg) * s, c, l) for s, c, l in dd.assembly(P, parts, explode=0.0)]

    fig, ax = plt.subplots(figsize=(11, 13), dpi=150)
    draw_parts(ax, asm)
    ax.axvline(0, color="#888", lw=0.6, ls=(0, (8, 3, 2, 3)), zorder=1)
    zt, zb = L + D["cap_out"], -D["cap_out"]
    Ro = D["R_o"]
    g = dd.adapter_geometry(P, P.spool_bore)
    # overall
    dim(ax, (-Ro, zb), (-Ro, zt), f"{zt - zb:.1f}  overall", off=(-14, 0), horiz=False)
    dim(ax, (-Ro, 0), (-Ro, L), f"{L:.1f}  body", off=(-7, 0), horiz=False)
    dim(ax, (-Ro, zt), (Ro, zt), f"Ø{P.body_od:.1f}  body / cap / adapter ring", off=(0, 6))
    dim(ax, (-P.spool_bore / 2, zb), (P.spool_bore / 2, zb),
        f"Ø{P.spool_bore:.1f} spool bore (adapter springs from Ø{2 * g['R_t']:.1f} free)", off=(0, -7))
    dim(ax, (Ro, 0), (Ro, -D["neck_len"]), f"{D['neck_len']:.1f}", off=(9, 0), horiz=False)
    dim(ax, (Ro, -D["neck_len"]), (Ro, zb), f"{P.head_height:.1f}", off=(9, 0), horiz=False)
    dim(ax, (-D["R_s"], L - 2), (D["R_s"], L - 2), f"Ø{2 * D['R_s']:.1f} socket", off=(0, 0), fs=8)
    dim(ax, (-D["R_i"], L / 2), (D["R_i"], L / 2), f"Ø{2 * D['R_i']:.1f} chamber,  wall {P.wall:.1f}", off=(0, 0), fs=8)
    dim(ax, (-D["R_pi"], 2.0), (D["R_pi"], 2.0), f"Ø{2 * D['R_pi']:.1f} fill opening", off=(0, 0), fs=8)
    dim(ax, (-D["R_ap"], zb + 0.5), (D["R_ap"], zb + 0.5), f"Ø{P.window_aperture:.0f} window", off=(0, -3), fs=8)
    fl = L - D["collar_total"]
    ax.plot([-D["R_i"], D["R_i"]], [fl, fl], color="#d0021b", lw=0.8, ls="--", zorder=8)
    ax.text(0, fl + 0.8, "fill line", color="#d0021b", ha="center", fontsize=8, zorder=8)
    ax.set_aspect("equal")
    ax.set_xlim(-48, 48)
    ax.set_ylim(zb - 14, zt + 12)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("DRYDOCK P001  ·  section through the axis, caps locked, 55 mm adapters  (mm)\n"
                 "left: groove + entry slot side    right: lug engaged in groove", fontsize=10)
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "09_section_drawing.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # bayonet detail (r, z), bottom end, right side
    fig, ax = plt.subplots(figsize=(9, 8), dpi=170)
    draw_parts(ax, asm)
    ax.set_ylim(-5, 11)
    ax.set_aspect("equal")
    zc = D["z_c"]
    ax.set_xlim(14.0, 28.5)
    kw = dict(fontsize=9, color="#1b4f9c", bbox=dict(fc="white", ec="none", pad=1.0),
              arrowprops=dict(arrowstyle="-", color="#1b4f9c", lw=0.6))
    ax.annotate(f"lug: {P.lug_radial} proud, {P.lug_tip_height} at tip,\n{P.flank_deg:.0f}° flanks; "
                f"{P.lug_count} × {P.lug_width_deg:.0f}°, {P.travel_deg:.0f}° turn",
                (20.2, zc), (14.1, 10.0), **kw)
    ax.annotate(f"radial clearance {P.fit_radial}\nplug wall {P.plug_wall}", (19.4, 6.9), (14.1, 7.6), **kw)
    ax.annotate(f"skin {D['R_o'] - D['R_g']:.2f} over groove", (22.0, zc), (23.4, 6.5), **kw)
    ax.annotate(f"lip {P.lip} at the bore;\nbearing-flank play {P.bearing_play}", (20.0, 1.3), (23.4, 1.8), **kw)
    ax.annotate("neck face seats on the rim", (20.6, -0.05), (23.4, -0.9), **kw)
    kw2 = dict(kw); kw2["color"] = "#a43c00"; kw2["arrowprops"] = dict(arrowstyle="-", color="#a43c00", lw=0.6)
    ax.annotate("adapter ring, trapped\n(0.3 axial play)", (22.6, -2.4), (23.4, -3.4), **kw2)
    ax.annotate("lock mark", (22.7, 1.5), (23.4, 4.0), **kw)
    ax.set_xticks(np.arange(14, 29, 1)); ax.set_yticks(np.arange(-5, 12, 1))
    ax.tick_params(labelsize=7)
    ax.grid(color="#ddd", lw=0.4, zorder=0)
    ax.set_xlabel("radius (mm)", fontsize=8); ax.set_ylabel("z from body rim (mm), +z into the body", fontsize=8)
    ax.set_title("QuickLock detail, locked, lug in the cut plane", fontsize=10)
    fig.savefig(OUT / "10_bayonet_detail.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote drawings")


if __name__ == "__main__":
    main()
