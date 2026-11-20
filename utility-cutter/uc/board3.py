"""Architecture drawings for approval (schematic sections drawn from the layout numbers)."""

import math
import os

from PIL import Image, ImageDraw

from .board import BG, INK, MUTE, ORANGE, font

GRAPH, SHUT, STEEL, WHITE = (42, 44, 48), (92, 96, 104), (176, 180, 186), (250, 249, 246)
OR, PALE, BOLT = (240, 74, 0), (226, 224, 219), (240, 74, 0)


class Pane:
    """Millimetre drawing surface: x right, y up."""

    def __init__(self, d, ox, oy, sc):
        self.d, self.ox, self.oy, self.sc = d, ox, oy, sc

    def P(self, x, y):
        return (self.ox + x * self.sc, self.oy - y * self.sc)

    def rect(self, x0, y0, x1, y1, fill):
        self.d.rectangle((*self.P(x0, y1), *self.P(x1, y0)), fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([self.P(*p) for p in pts], fill=fill)

    def circ(self, x, y, r, fill, outline=None):
        c = self.P(x, y)
        r *= self.sc
        self.d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=fill, outline=outline, width=3)

    def arrow(self, a, b, col=INK, w=5):
        a, b = self.P(*a), self.P(*b)
        self.d.line([a, b], fill=col, width=w)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-1, 1):
            self.d.line([b, (b[0] - 18 * math.cos(ang + s * 0.45), b[1] - 18 * math.sin(ang + s * 0.45))], fill=col, width=w)

    def text(self, x, y, t, size=22, weight="Medium", fill=INK):
        self.d.text(self.P(x, y), t, font=font(weight, size), fill=fill)


def _pawl_cell(pn, kind, state):
    """One pawl in plan section. kind 'A' blocks retraction, 'B' blocks extension.
    state: 0 locked, 1 wheel rolling forward (carriage moving to the nose, left), 2 released."""
    X1 = 44.0
    cx = 14.0 if state == 0 else (9.0 if state == 1 else 4.0)
    wins = (5.0, 15.0, 25.0, 35.0)
    pn.rect(0, 0, X1, 3.0, GRAPH)
    for n in wins:
        pn.rect(n - 1.7, -0.2, n + 1.7, 3.2, WHITE)
    tx = cx + 11.0                                   # tooth centre
    lifted = state == 1                              # A rides up its own ramp; B is lifted by the rack
    dy = 2.6 if lifted else 0.0
    # carriage cage either side of the tooth, and a backbone
    pn.rect(cx, 5.6, cx + 22, 8.6, OR)
    pn.rect(cx, 3.3, cx + 8.2, 5.7, OR)
    pn.rect(tx + 1.5, 3.3, cx + 22, 5.7, OR)
    # arm + tooth
    th = math.atan2(dy, 10.0)
    root = (cx + 0.5, 4.0)

    def R(x, y):
        ddx, ddy = x - root[0], y - root[1]
        return (root[0] + ddx * math.cos(th) - ddy * math.sin(th), root[1] + ddx * math.sin(th) + ddy * math.cos(th))
    pn.rect(cx + 8.2, 3.3, tx + 1.5, 5.7, WHITE)
    pn.poly([R(cx + 0.5, 3.5), R(tx + 1.2, 3.5), R(tx + 1.2, 4.6), R(cx + 0.5, 4.6)], OR)
    if kind == "A":      # square rear face (right), ramped front
        pn.poly([R(tx - 1.2, 3.5), R(tx + 1.2, 3.5), R(tx + 1.2, 0.7), R(tx + 0.3, 0.7)], OR)
    else:                # square front face (left), ramped rear
        pn.poly([R(tx - 1.2, 3.5), R(tx + 1.2, 3.5), R(tx - 0.3, 0.7), R(tx - 1.2, 0.7)], OR)


def lock_board(out):
    W, H, M = 2400, 1330, 70
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    d.text((M, 56), "Lock", font=font("SemiBold", 64), fill=INK)
    d.text((M + 170, 80), "two opposed pawls in every window", font=font("Regular", 38), fill=MUTE)
    d.text((M, 142), "Plan sections, nose to the left, back wall at the bottom. The two teeth sit one above the other and "
           "share each window.", font=font("Regular", 26), fill=MUTE)
    cols = ["1  Locked", "2  Rolling forward", "3  Let go"]
    notes = [
        ["Both teeth seated, both spring arms relaxed.", "A stops the blade being pushed back (cutting).",
         "B stops it being pulled forward."],
        ["The rack leads by 2.5 mm and lifts B.", "A needs no lifting: it rides up its own ramp",
         "and clicks into each window as it passes."],
        ["A is already seated by its own spring.", "B drops when the rack re-centres.",
         "The cutting-direction lock never waits for the wheel."],
    ]
    cw = (W - 2 * M - 2 * 30) / 3
    sc = (cw - 40) / 44.0
    for c in range(3):
        x0 = M + c * (cw + 30)
        d.rectangle((x0, 210, x0 + cw, 1120), fill=WHITE)
        d.text((x0 + 24, 228), cols[c], font=font("SemiBold", 34), fill=INK)
        for r, kind in enumerate("AB"):
            oy = 500 + r * 290
            pn = Pane(d, x0 + 20, oy, sc)
            _pawl_cell(pn, kind, c)
            lab = "A  blocks retraction" if kind == "A" else "B  blocks extension"
            d.text((x0 + 24, oy - 12.5 * sc), lab, font=font("Medium", 24), fill=(70, 70, 72))
            if c == 0:
                if kind == "A":
                    pn.arrow((2, 7.6), (10, 7.6))
                    pn.text(1.0, 10.4, "cutting force", 20)
                else:
                    pn.arrow((12, 7.6), (4, 7.6))
                    pn.text(1.0, 10.4, "pull-out drag", 20)
            if c == 1:
                pn.arrow((38, 7.0), (31, 7.0))
        yy = 990
        for ln in notes[c]:
            d.text((x0 + 24, yy), ln, font=font("Regular", 24), fill=(70, 70, 72))
            yy += 34
    d.text((M, H - 150), "If the wheel sticks after extending, B may stay lifted: the blade could then be pulled forward, "
           "but it cannot be pushed back. If it sticks after retracting, A stays lifted until", font=font("Regular", 24), fill=MUTE)
    d.text((M, H - 116), "a cutting load pushes the carriage back onto the rack, which seats it. Proposed mechanism; "
           "not built or tested.", font=font("Regular", 24), fill=MUTE)
    p = os.path.join(out, "arch_lock.png")
    s.save(p, optimize=True)
    return p


def _tail_cell(pn, safe, parked):
    """Plan section through the tail at the height of the bolt. x along the tool (tail to the
    right), y across the thickness (back face at the bottom)."""
    T = 23.0
    split, end, bx = 22.0, 40.0, 29.0
    pn.rect(0, 0, split, 2.5, GRAPH)                       # body: back wall
    pn.rect(0, 14.3, split, T, GRAPH)                      # body: solid wheel-side half
    pn.rect(split + 0.4, 0, end, T, (66, 68, 74))          # tail cap
    pn.rect(split + 0.4, 6.9, end - 4.5, 14.6, WHITE)      # rack pocket in the cap
    rx1 = 34.6 if parked else 15.0
    if parked:                                             # rack with its notch; the land behind is the hook
        pn.rect(-2, 7.3, bx - 2.8, 14.1, SHUT)
        pn.rect(bx + 2.8, 7.3, rx1, 14.1, SHUT)
    else:
        pn.rect(-2, 7.3, rx1, 14.1, SHUT)
    sh = 3.5 if safe else 0.0
    pn.rect(bx - 2.5, -2.0 + sh, bx + 2.5, 21.5 + sh, BOLT)             # the bolt
    pn.rect(bx - 2.6, 6.9 + sh, bx + 2.6, 14.6 + sh, WHITE)             # its waist
    if safe:
        pn.rect(bx - 2.6, 14.6, bx + 2.6, 14.6 + sh, (66, 68, 74))      # waist now inside the cap wall
        pn.rect(bx - 2.5, 14.6, bx + 2.5, 14.6 + sh, (228, 226, 221))
    return bx


def tail_board(out):
    W, H, M = 2400, 1380, 70
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    d.text((M, 56), "Tail", font=font("SemiBold", 64), fill=INK)
    d.text((M + 150, 80), "carry bolt and tail-cap retention", font=font("Regular", 38), fill=MUTE)
    d.text((M, 142), "Plan sections at rack height, tail to the right, back face at the bottom. Schematic; the rails and latch are "
           "above and below this section and are not drawn.", font=font("Regular", 26), fill=MUTE)
    cells = [("Free, blade in use", False, False,
              ["Bolt pushed to the back: its waist lines up with", "the rack, which passes straight through.",
               "The cap is held by its latch."]),
             ("Free, blade parked", False, True,
              ["The rack end has entered the cap.", "The cap now cannot slide off sideways:",
               "the rack is in the way."]),
             ("Safe, blade parked", True, True,
              ["Bolt pushed to the front: its full section drops", "into a notch in the rack.",
               "The rack is held, so the wheel cannot turn."])]
    cw = (W - 2 * M - 2 * 30) / 3
    sc = (cw - 120) / 44.0
    for c, (title, safe, parked, lines) in enumerate(cells):
        x0 = M + c * (cw + 30)
        d.rectangle((x0, 210, x0 + cw, 1180), fill=WHITE)
        d.text((x0 + 24, 228), title, font=font("SemiBold", 34), fill=INK)
        pn = Pane(d, x0 + 70, 860, sc)
        bx = _tail_cell(pn, safe, parked)
        pn.text(1, 25.6, "body", 20, fill=(90, 90, 92))
        pn.text(33.0, -3.4, "tail cap", 20, fill=(90, 90, 92))
        pn.text(2, 9.8, "rack", 20, fill=WHITE)
        if safe:
            pn.text(bx - 21.5, 25.4, "bolt, proud this side", 20, fill=OR)
        else:
            pn.text(bx + 3.6, -1.6, "bolt, proud this side", 20, fill=OR)
        yy = 1000
        for ln in lines:
            d.text((x0 + 24, yy), ln, font=font("Regular", 24), fill=(70, 70, 72))
            yy += 34
    d.text((M, H - 150), "Cap: slides on across the thickness on two T-rails, so a load along the tool is carried by the "
           "rails. A press-to-release latch (relaxed when latched) stops it sliding; the parked rack", font=font("Regular", 24), fill=MUTE)
    d.text((M, H - 116), "and the engaged bolt each block it as well. To change a blade: bolt to free, one click out, "
           "press the latch, slide the cap off. Proposed; not built or tested.", font=font("Regular", 24), fill=MUTE)
    p = os.path.join(out, "arch_tail.png")
    s.save(p, optimize=True)
    return p


def stack_board(out):
    """Cross-section through the wheel axis: the layer stack that sets the 23 mm thickness."""
    from . import orbit2 as O
    W, H, M = 2400, 1300, 70
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    d.text((M, 56), "Section", font=font("SemiBold", 64), fill=INK)
    d.text((M + 270, 80), "through the wheel axis, looking from the tail", font=font("Regular", 38), fill=MUTE)
    d.text((M, 142), "Back face on the left, wheel face on the right. Drawn from the layout numbers at true proportion.",
           font=font("Regular", 26), fill=MUTE)
    d.rectangle((M, 210, W - M, H - 120), fill=WHITE)
    sc = 15.5
    pn = Pane(d, W / 2 - 80, 900, sc)          # x = y_design, y = z_design
    T = O.T
    zb, zt = -9.0, 37.2
    # body
    pn.rect(-T / 2, zb, T / 2, 26.4, GRAPH)
    pn.rect(-T / 2, 26.4, O.Y_DISC[0] - 0.1, zt, GRAPH)                    # fender (back half)
    # channel
    pn.rect(O.Y_WALL, -0.6, O.Y_GEAR[1] + 0.2, 18.6, WHITE)
    # pinion bay and wheel bay
    pn.rect(O.Y_FL[0] - 0.2, O.WZ - 11.9, O.Y_DISC[0], O.WZ + 11.9, WHITE)
    pn.rect(O.Y_DISC[0] - 0.1, O.WZ - 20.0, T / 2 + 0.2, O.WZ + 20.0, WHITE)
    # lips that keep the blade against the wall
    pn.rect(O.Y_WALL + 0.9, 16.6, O.Y_WALL + 1.9, 18.6, GRAPH)
    pn.rect(O.Y_WALL + 0.9, -0.6, O.Y_WALL + 1.9, 1.0, GRAPH)
    # blade
    pn.rect(O.BY - 0.25, 0.0, O.BY + 0.25, 18.0, STEEL)
    # carriage (between the lips)
    pn.rect(O.Y_WALL + 0.9, 1.3, O.Y_CARR, 16.3, OR)
    # window with the two teeth
    pn.rect(-T / 2 - 0.2, O.WIN_Z[0] - 0.2, O.Y_WALL, O.WIN_Z[1] + 0.2, WHITE)
    pn.rect(-T / 2 + 0.9, O.WIN_Z[0], O.Y_WALL + 0.9, O.WIN_Z[0] + 3.0, OR)
    pn.rect(-T / 2 + 0.9, O.WIN_Z[1] - 3.0, O.Y_WALL + 0.9, O.WIN_Z[1], (200, 60, 0))
    # wheel: flange, pinion, disc
    pn.rect(O.Y_FL[0], O.WZ - 9.4, O.Y_FL[1], O.WZ + 9.4, OR)
    pn.rect(O.Y_GEAR[0], O.WZ - 11.2, O.Y_DISC[0], O.WZ + 11.2, OR)
    pn.rect(O.Y_GEAR[0] + 0.1, O.RACK_Z - 6.0, O.Y_GEAR[1] - 0.1, O.RACK_Z + O.M, SHUT)   # rack, meshing from below
    pn.rect(O.Y_DISC[0], O.WZ - O.WR, O.Y_DISC[1], O.WZ + O.WR, OR)
    pn.rect(O.Y_DISC[1] - 0.9, O.WZ - 16.6, O.Y_DISC[1] - 0.3, O.WZ + 16.6, (30, 31, 34))
    f = font("Medium", 23)

    def call(x, y, tx, ty, text, right=True):
        a, b = pn.P(x, y), pn.P(tx, ty)
        d.line([a, b], fill=INK, width=3)
        d.ellipse((a[0] - 5, a[1] - 5, a[0] + 5, a[1] + 5), fill=INK)
        w = d.textlength(text, font=f)
        d.text((b[0] + 10 if right else b[0] - w - 10, b[1] - 14), text, font=f, fill=INK)
    call(-10.3, 14.0, -22, 14.0, "back wall 2.5, lock windows", False)
    call(O.BY, 12.0, -22, 20.0, "blade, 2.9 from the back face", False)
    call(-9.6, 17.6, -22, 26.0, "lip: keeps the blade on the wall", False)
    call(-7.0, 6.0, -22, 2.0, "carriage 3.3, two pawl teeth", False)
    call(-4.85, 28.0, -22, 32.0, "flange 1.1: rack keeps the wheel in", False)
    call(-1.0, 9.0, 22, 2.0, "rack 6.8 wide")
    call(-1.0, 27.0, 22, 30.0, "pinion, 12 teeth, 60 mm per turn")
    call(8.0, 38.0, 22, 38.0, "wheel disc 8.8, runs in the body bore")
    call(-6.0, 34.0, -22, 38.0, "fender over the pinion", False)
    d.text((M, H - 96), "Blade and carriage sit against the back wall; the gear train sits beside them. Clearances are "
           "listed in ARCHITECTURE.md. Proposed layout; not CAD.", font=font("Regular", 24), fill=MUTE)
    p = os.path.join(out, "arch_section.png")
    s.save(p, optimize=True)
    return p


def make_all(out):
    return [lock_board(out), tail_board(out), stack_board(out)]
