"""Animated GIF of the mechanism turning, with the firing cylinder highlighted.

    python tools/animate.py [frames]
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import assembly  # noqa: E402
import config as C  # noqa: E402
import render  # noqa: E402


def firing_now(phi, window=36.0):
    """Cylinders within `window` deg after their firing TDC at crank angle phi (0..720)."""
    out = []
    for c, a in C.FIRE_ANGLE.items():
        d = (phi - a) % C.CYCLE_DEG
        if d < window:
            out.append(c)
    return out


def main(frames=30):
    tmp = os.path.join(ROOT, "renders", "_anim")
    os.makedirs(tmp, exist_ok=True)
    imgs = []
    step = C.CYCLE_DEG / frames              # a full 720 deg 4-stroke cycle
    for i in range(frames):
        phi = i * step
        fire = firing_now(phi)
        items = []
        for n, s, col in assembly.engine(phi % 360.0, with_blocks=False):
            if n.startswith(("crankcase", "end_plate")):
                continue
            if n.startswith("piston_") and int(n.split("_")[1]) in fire:
                col = "orange"
            items.append((s, col))
        p = os.path.join(tmp, f"f{i:03d}.png")
        render.render(items, p, view=((1.0, -0.9, 0.75), (0, 0, 1)), size=(900, 640), zoom=1.25,
                      title=f"crank {phi:5.1f} deg   firing: cyl {', '.join(map(str, fire))}")
        imgs.append(Image.open(p).convert("P", palette=Image.ADAPTIVE, colors=128))
        print("frame", i, flush=True)
    out = os.path.join(ROOT, "renders", "30_mechanism_cycle.gif")
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=120, loop=0, optimize=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print("wrote", out)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
