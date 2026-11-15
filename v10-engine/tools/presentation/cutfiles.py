"""Display case cut files (DXF, mm) for test cuts on the shop's lasers / plasma.

Draft sizes: the engine footprint comes from tools/presentation/concept.py; the sheet
thicknesses below are ASSUMED until the shop says what it stocks. Change them and re-run:
    python3.13 tools/presentation/cutfiles.py
Writes cutfiles/display_case/*.dxf, preview.png and README.md.

Layers in every DXF: CUT (through cut, red), ENGRAVE (score / raster, blue), NOTE (do not cut).
"""
import os
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cutfiles", "display_case")

# ---- assumed stock (mm); 1/4" acrylic, 3/4" wood, 1/2" steel, 1.5 mm brass ----
T_ACR = 6.35
T_WOOD = 19.05
T_STEEL = 12.7
T_BRASS = 1.5
KERF_CLEAR = 0.4          # per side, slip fits between cut parts

# ---- engine envelope (concept.py ENG + GAP) ----
ENG_W, ENG_D, ENG_H = 300.0, 240.0, 306.0
GAP = 30.0
IN_W, IN_D, IN_H = ENG_W + 2 * GAP, ENG_D + 2 * GAP, ENG_H + GAP   # cover inside
CV_W, CV_D = IN_W + 2 * T_ACR, IN_D + 2 * T_ACR                    # cover outside
RIM = 25.0                                                         # base border outside the cover
B_W, B_D = CV_W + 2 * RIM, CV_D + 2 * RIM
R_CORNER = 8.0

PARTS = []   # (filename, material, qty, machine, outline fn)


def rrect(msp, cx, cy, w, h, r, layer="CUT"):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    if r <= 0:
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})
        return
    b = 0.41421356  # bulge for a 90 deg arc
    pts = [(x0 + r, y0, 0), (x1 - r, y0, b), (x1, y0 + r, 0), (x1, y1 - r, b),
           (x1 - r, y1, 0), (x0 + r, y1, b), (x0, y1 - r, 0), (x0, y0 + r, b)]
    msp.add_lwpolyline(pts, format="xyb", close=True, dxfattribs={"layer": layer})


def hole(msp, x, y, d, layer="CUT"):
    msp.add_circle((x, y), d / 2, dxfattribs={"layer": layer})


def note(msp, x, y, text, h=6):
    msp.add_text(text, height=h, dxfattribs={"layer": "NOTE"}).set_placement((x, y))


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for n, c in (("CUT", 1), ("ENGRAVE", 5), ("NOTE", 8)):
        doc.layers.add(n, color=c)
    return doc


CORNER_HOLES = [(sx * (B_W / 2 - RIM / 2), sy * (B_D / 2 - RIM / 2)) for sx in (-1, 1) for sy in (-1, 1)]
STEEL_W, STEEL_D = B_W - 2 * 60, B_D - 2 * 60


def base_bottom(msp):
    rrect(msp, 0, 0, B_W, B_D, R_CORNER)
    for x, y in CORNER_HOLES:
        hole(msp, x, y, 4.5)                     # #8 wood screws up into the layers
        hole(msp, x, y, 15.0, "ENGRAVE")         # felt foot mark
    note(msp, -B_W / 2, -B_D / 2 - 14, "BASE 1 bottom - wood %.2f" % T_WOOD)


def base_pocket(msp):
    rrect(msp, 0, 0, B_W, B_D, R_CORNER)
    rrect(msp, 0, 0, STEEL_W + 2 * KERF_CLEAR, STEEL_D + 2 * KERF_CLEAR, 4.0)   # pocket for the steel weight
    for x, y in CORNER_HOLES:
        hole(msp, x, y, 4.5)
    note(msp, -B_W / 2, -B_D / 2 - 14, "BASE 2 pocket - wood %.2f (steel weight drops in)" % T_WOOD)


def base_deck(msp):
    rrect(msp, 0, 0, B_W, B_D, R_CORNER)
    # cover groove is made by the frame layer above; engine stand bolts: positions TBD
    for x, y in [(sx * 120, sy * 90) for sx in (-1, 1) for sy in (-1, 1)]:
        hole(msp, x, y, 5.5, "ENGRAVE")          # mark only until the stand bolt pattern is fixed
    for x, y in CORNER_HOLES:
        hole(msp, x, y, 4.5)
    note(msp, -B_W / 2, -B_D / 2 - 14, "BASE 3 deck - wood %.2f (engine bolt marks = TBD)" % T_WOOD)


def base_frame(msp):
    rrect(msp, 0, 0, B_W, B_D, R_CORNER)
    rrect(msp, 0, 0, CV_W + 2 * KERF_CLEAR, CV_D + 2 * KERF_CLEAR, 0)          # cover drops into this
    for x, y in CORNER_HOLES:
        hole(msp, x, y, 4.5)
        hole(msp, x, y, 9.0, "ENGRAVE")          # countersink mark
    note(msp, -B_W / 2, -B_D / 2 - 14, "BASE 4 cover frame - wood %.2f" % T_WOOD)


def steel_weight(msp):
    rrect(msp, 0, 0, STEEL_W, STEEL_D, 4.0)
    note(msp, -STEEL_W / 2, -STEEL_D / 2 - 14, "STEEL WEIGHT - %.1f plate, hidden (plasma ok)" % T_STEEL)


# cover: top panel sits on the 4 walls; front/back walls full width, side walls between them
def cover_top(msp):
    rrect(msp, 0, 0, CV_W, CV_D, 0)
    note(msp, -CV_W / 2, -CV_D / 2 - 14, "COVER top - acrylic %.2f" % T_ACR)


H_WALL = IN_H


def cover_front(msp):
    rrect(msp, 0, 0, CV_W, H_WALL, 0)
    note(msp, -CV_W / 2, -H_WALL / 2 - 14, "COVER front/back x2 - acrylic, protect film ON")


def cover_side(msp):
    rrect(msp, 0, 0, IN_D, H_WALL, 0)
    note(msp, -IN_D / 2, -H_WALL / 2 - 14, "COVER side x2 - acrylic (fits between front/back)")


PL_W, PL_H = 140.0, 40.0


N_ENGINES = 50


def name_plate(msp, num=None):
    rrect(msp, 0, 0, PL_W, PL_H, 3.0)
    hole(msp, -PL_W / 2 + 8, 0, 2.5)
    hole(msp, PL_W / 2 - 8, 0, 2.5)
    msp.add_text("NAME / LOGO TBD", height=9, dxfattribs={"layer": "ENGRAVE"}).set_placement(
        (0, 0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    note(msp, -PL_W / 2, -PL_H / 2 - 12, "NAME PLATE - brass %.1f (fiber laser)" % T_BRASS)


PARTS = [
    ("01_base_bottom.dxf", "wood %.2f" % T_WOOD, 1, "CO2", base_bottom, (B_W, B_D)),
    ("02_base_pocket.dxf", "wood %.2f" % T_WOOD, 1, "CO2", base_pocket, (B_W, B_D)),
    ("03_base_deck.dxf", "wood %.2f" % T_WOOD, 1, "CO2", base_deck, (B_W, B_D)),
    ("OPTIONAL_04_base_cover_frame.dxf", "wood %.2f" % T_WOOD, 1, "CO2", base_frame, (B_W, B_D)),
    ("05_steel_weight.dxf", "steel %.1f" % T_STEEL, 1, "plasma", steel_weight, (STEEL_W, STEEL_D)),
    ("OPTIONAL_06_cover_top.dxf", "clear acrylic %.2f" % T_ACR, 1, "CO2", cover_top, (CV_W, CV_D)),
    ("OPTIONAL_07_cover_front_back.dxf", "clear acrylic %.2f" % T_ACR, 2, "CO2", cover_front, (CV_W, H_WALL)),
    ("OPTIONAL_08_cover_side.dxf", "clear acrylic %.2f" % T_ACR, 2, "CO2", cover_side, (IN_D, H_WALL)),
    ("09_name_plate.dxf", "brass %.1f" % T_BRASS, 1, "fiber", name_plate, (PL_W, PL_H)),
]


def preview(paths):
    fig, axes = plt.subplots(3, 3, figsize=(15, 13))
    for ax, (fn, mat, q, mach, _, _) in zip(axes.flat, PARTS):
        doc = ezdxf.readfile(os.path.join(OUT, fn))
        for e in doc.modelspace():
            col = {"CUT": "#c00", "ENGRAVE": "#06c"}.get(e.dxf.layer)
            if col is None:
                continue
            if e.dxftype() == "CIRCLE":
                ax.add_patch(plt.Circle((e.dxf.center.x, e.dxf.center.y), e.dxf.radius, fill=False, color=col, lw=1))
            elif e.dxftype() == "LWPOLYLINE":
                from ezdxf import path as _p; pts = [(v.x, v.y) for v in _p.make_path(e).flattening(0.5)]
                xs, ys = zip(*pts)
                ax.plot(xs + (xs[0],), ys + (ys[0],), color=col, lw=1.2)
            elif e.dxftype() == "TEXT":
                ax.text(e.dxf.insert.x, e.dxf.insert.y, e.dxf.text, color=col, ha="center", va="center", fontsize=8)
        ax.set_aspect("equal")
        ax.autoscale_view()
        ax.margins(0.08)
        ax.set_title("%s\n%s, qty %d, %s" % (fn, mat, q, mach), fontsize=10)
        ax.tick_params(labelsize=7)
    fig.suptitle("Display case test cuts (mm)   red = cut   blue = engrave/mark", fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "preview.png"), dpi=110)


def readme():
    lines = [
        "# Display case cut files (TEST CUT DRAFT)",
        "",
        "Not final. Sheet thicknesses are guesses until the shop confirms what it stocks;",
        "change them at the top of `tools/presentation/cutfiles.py` and re-run.",
        "",
        "Units mm. DXF layers: **CUT** (through), **ENGRAVE** (score/mark), **NOTE** (don't cut).",
        "",
        "| File | Material | Qty | Machine | Size (mm) |",
        "|---|---|---|---|---|",
    ]
    for fn, mat, q, mach, _, (w, h) in PARTS:
        lines.append("| %s | %s | %d | %s | %.0f x %.0f |" % (fn, mat, q, mach, w, h))
    lines += [
        "",
        "**Plan (D65/D66): engine on a custom wood base with a brass name plate (not numbered). The clear cover",
        "(OPTIONAL_ files) is NOT being made unless Scott asks for it.**",
        "",
        "## How it goes together",
        "- Wood layers 1-4 stack and screw together through the 4 corner holes (glue too).",
        "  Layer 2's pocket holds the steel weight; layer 4's opening is where the cover sits.",
        "- Cover: front/back are full width, sides fit between them, top sits on all four.",
        "  Acrylic cement (Weld-On 4/16). Leave protective film on until glued.",
        "- Engine bolt marks on layer 3 are placeholders: the stand bolt pattern is set later.",
        "",
        "Envelope: inside cover %.0f x %.0f x %.0f, base %.0f x %.0f x %.0f." % (
            IN_W, IN_D, IN_H, B_W, B_D, 4 * T_WOOD),
        "",
        "Cheap first test: cut 06 + one 08 + 09 only, check acrylic edge quality and the engrave.",
    ]
    open(os.path.join(OUT, "README.md"), "w").write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn, mat, q, mach, fnc, _ in PARTS:
        doc = new_doc()
        fnc(doc.modelspace())
        doc.saveas(os.path.join(OUT, fn))
    preview(PARTS)
    readme()
    print("wrote", len(PARTS), "DXF to", OUT)


if __name__ == "__main__":
    main()
