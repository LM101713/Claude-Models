"""Render the V8 moving core with the exterior of ONE bank (A) for the approval
gate, each view side by side with the matching reference image.

    python cad/render_v8_bank.py          -> renders/v8_bankA/
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.modules.setdefault("pan_v8", None)          # pan / stand not designed yet

from PIL import Image, ImageDraw  # noqa: E402

import assembly_v8 as A  # noqa: E402
import exterior_v8 as E  # noqa: E402
import render  # noqa: E402

COLOURS = {                                     # approved palette, approximated for the preview
    "head": (0.70, 0.71, 0.73), "valve_cover": (0.11, 0.11, 0.12), "header_plate": (0.62, 0.63, 0.65),
    "header": (0.84, 0.84, 0.82), "collector": (0.84, 0.84, 0.82), "boot": (0.98, 0.80, 0.40),
    "intake": (0.70, 0.71, 0.73), "crankcase": (0.70, 0.71, 0.73), "valley": (0.70, 0.71, 0.73),
    "bank": (0.70, 0.71, 0.73), "end": (0.70, 0.71, 0.73),
}

VIEWS = {
    "ref1_closeup_34_above": ((0.55, -1.0, 0.75), 2.0, "STYLE_ai_01.png"),
    "ref2_rear_left_34": ((-1.0, -0.9, 0.45), 1.0, "STYLE_ai_02.png"),
    "ref3_front_right_34": ((1.0, 0.9, 0.45), 1.0, "STYLE_ai_03.png"),
    "ref4_side_left": ((0.0, -1.0, 0.12), 1.0, "STYLE_ai_04.png"),
    "ref5_front": ((1.0, 0.0, 0.15), 1.0, "STYLE_ai_05.png"),
    "x1_bankA_low_34": ((0.7, -1.0, 0.35), 1.3, None),
    "x2_bankA_headers": ((0.2, -1.0, -0.25), 1.4, None),
    "x3_top": ((0.0, 0.0, 1.0), 1.0, None),
}


def colour(name):
    for k, c in COLOURS.items():
        if name.startswith(k):
            return c
    return {"steel": "steel", "crank": "crank"}.get(name, "steel")


def scene(phi=0.0, with_intake=True):
    L = A.libs()
    items = []
    for n, s, c in A.engine(phi):
        items.append((s, colour(n) if n.startswith(A.STATIC) else c))
    for n, s, _ in E.placed(L["style"], banks=("A",), with_intake=with_intake):
        if n.startswith("boot"):
            items.append((s, colour(n), 0.85))
        else:
            items.append((s, colour(n)))
    return items


def main():
    out = os.path.join(ROOT, "renders", "v8_bankA")
    os.makedirs(out, exist_ok=True)
    items = scene(20.0)
    size = (1448, 1086)
    for name, (direction, zoom, ref) in VIEWS.items():
        path = os.path.join(out, name + ".png")
        render.render(items, path, view=(direction, (0, 0, 1)) if name != "x3_top" else (direction, (1, 0, 0)),
                      size=size, zoom=zoom, title=f"V8 bank A exterior + moving core - {name} (no pan / stand / front yet)")
        if ref:
            a = Image.open(path).convert("RGB")
            b = Image.open(os.path.join(ROOT, "references", ref)).convert("RGB").resize(size)
            comp = Image.new("RGB", (size[0] * 2 + 20, size[1] + 40), (255, 255, 255))
            comp.paste(a, (0, 40))
            comp.paste(b, (size[0] + 20, 40))
            d = ImageDraw.Draw(comp)
            d.text((10, 12), f"CAD (bank A only)  -  {name}", fill=(0, 0, 0))
            d.text((size[0] + 30, 12), f"reference {ref} (AI-generated, style only)", fill=(0, 0, 0))
            comp.save(os.path.join(out, name + "_vs_ref.png"))
        print("wrote", path, flush=True)
    render.render(scene(20.0, with_intake=False), os.path.join(out, "x4_no_intake_34.png"),
                  view=((0.55, -1.0, 0.75), (0, 0, 1)), size=size, zoom=1.2,
                  title="V8 bank A exterior without the provisional intake")
    print("done")


if __name__ == "__main__":
    main()
