"""ORBIT v2 boards: exterior direction, and the all-printed mechanism (exploded, cutaway, lock)."""

import json
import math
import os

from PIL import Image, ImageDraw

from .board import BG, INK, MUTE, ORANGE, fit, font

GRAPH, SHUT, STEEL, WHITE = (42, 44, 48), (92, 96, 104), (176, 180, 186), (250, 249, 246)
PART_OR = (240, 74, 0)

LEGEND = [
    ("body", "Body", "One piece. Prints on its back face; the blade channel is a bridge."),
    ("wheel", "Wheel", "Thumb wheel, pinion and flange in one part; the dark face is a colour inlay. Drops in from the side."),
    ("shuttle", "Shuttle", "The rack. Slides in from the tail and keys the wheel into the body."),
    ("carriage", "Carriage", "Blade seat with the lock pawl. The wear part: reprint it, keep the rest."),
    ("blade", "Blade", "Standard 18 mm snap-off. The only part that is not printed. Seven of its eight tips are used."),
    ("tail_cap", "Tail cap", "Closes the channel. Slides on sideways on two rails, so no load along the tool can pull it off."),
    ("carry_bolt", "Carry bolt", "Push-through bolt in the tail cap. Holds the rack when the blade is parked, so the wheel cannot turn."),
]


def _dot(d, xy, n, r=24):
    x, y = xy
    d.ellipse((x - r, y - r, x + r, y + r), fill=WHITE, outline=INK, width=3)
    f = font("SemiBold", 26)
    w = d.textlength(str(n), font=f)
    d.text((x - w / 2, y - 17), str(n), font=f, fill=INK)


def _header(d, W, M, sub, line, right):
    d.text((M, 62), "02", font=font("SemiBold", 72), fill=ORANGE)
    d.text((M + 120, 62), "ORBIT", font=font("SemiBold", 72), fill=INK)
    d.text((M + 372, 92), sub, font=font("Regular", 40), fill=MUTE)
    d.text((M + 2, 152), line, font=font("Regular", 28), fill=MUTE)
    f = font("Medium", 24)
    d.text((W - M - d.textlength(right, font=f), 96), right, font=f, fill=MUTE)


def exterior(out):
    """Three-quarter, side, rear and top."""
    W, M, G = 2400, 70, 22
    img = lambda t: Image.open(os.path.join(out, f"orbit2_{t}.png")).convert("RGB")
    meta = json.load(open(os.path.join(out, "orbit2_meta.json")))
    L, Tk, Hh = meta["envelope"]
    cw = W - 2 * M
    half = (cw - G) // 2
    hero_h = int(cw * 1100 / 1800)
    row1 = int(half * 720 / 1800)
    row2 = int(cw * 420 / 1800)
    head = 210
    H = head + hero_h + G + row1 + G + row2 + M + 40
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    _header(d, W, M, "approved exterior + carry bolt", f"{L:.0f} x {Hh:.0f} x {Tk:.0f} mm  ·  six printed parts and a blade  ·  no hardware",
            "ODD LAYER  ·  final exterior review")
    y = head
    s.paste(fit(img("hero"), cw, hero_h), (M, y))
    y1 = y + hero_h + G
    s.paste(fit(img("side"), half, row1), (M, y1))
    s.paste(fit(img("back"), half, row1), (M + half + G, y1))
    y2 = y1 + row1 + G
    s.paste(fit(img("top"), cw, row2), (M, y2))
    lab = font("Medium", 22)
    for (x, yy, text) in [(M + 22, head + 18, "Three-quarter"), (M + 22, y1 + 16, "Side profile"),
                          (M + half + G + 22, y1 + 16, "Rear face"), (M + 22, y2 + 16, "Top view")]:
        d.text((x, yy), text.upper(), font=lab, fill=(70, 70, 70))
    d.text((M, H - M + 2), "Concept-stage geometry at true scale; not CAD, not printed. Surface finish is design intent, "
           "not an FDM print.", font=font("Regular", 22), fill=MUTE)
    p = os.path.join(out, "board_orbit2_exterior.png")
    s.save(p, optimize=True)
    return p


def review(out):
    """Rear three-quarter, wheel close-up and a same-scale comparison with the previous revision."""
    W, M, G = 2400, 70, 22
    img = lambda t: Image.open(os.path.join(out, f"orbit2_{t}.png")).convert("RGB")
    meta = json.load(open(os.path.join(out, "orbit2_meta.json")))
    cw = W - 2 * M
    half = (cw - G) // 2
    r1 = int(half * 1100 / 1800)
    head = 210
    # comparison strip: both at the same mm-per-pixel
    PREV_SPAN, PREV_LEN = 170.0, 170.0
    mm_px_new = (meta["span"] + 46) / 1800.0
    mm_px_old = (PREV_SPAN + 46) / 1800.0
    target = (PREV_SPAN + 46) / half                         # mm per px in the strip
    def scaled(name, mmpx):
        im = Image.open(os.path.join(out, name)).convert("RGB")
        k = mmpx / target
        return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    olds, news = scaled("orbit2_prev_side.png", mm_px_old), scaled("orbit2_side.png", mm_px_new)
    oldb, newb = scaled("orbit2_prev_back.png", mm_px_old), scaled("orbit2_back.png", mm_px_new)
    ch = max(olds.height, news.height)
    H = head + r1 + G + 60 + ch + G + ch + M + 40
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    _header(d, W, M, "what changed", "Rear three-quarter and wheel close-up, then the previous revision against this one "
            "at the same scale", "ODD LAYER  ·  final exterior review")
    y = head
    s.paste(fit(img("rear34"), half, r1), (M, y))
    s.paste(fit(img("detail"), half, r1), (M + half + G, y))
    lab = font("Medium", 22)
    d.text((M + 22, y + 18), "REAR THREE-QUARTER", font=lab, fill=(70, 70, 70))
    d.text((M + half + G + 22, y + 18), "WHEEL", font=lab, fill=(70, 70, 70))
    y1 = y + r1 + G
    f = font("SemiBold", 30)
    d.text((M, y1 + 8), f"Previous revision  ·  {PREV_LEN:.0f} mm as drawn", font=f, fill=MUTE)
    d.text((M + half + G, y1 + 8), f"This revision  ·  {meta['envelope'][0]:.0f} mm", font=f, fill=INK)
    y2 = y1 + 60

    def cell(im, x, yy):
        tile = Image.new("RGB", (half, ch), (176, 175, 171))
        tile.paste(im.crop((0, 0, min(im.width, half), min(im.height, ch))), ((half - min(im.width, half)) // 2, (ch - min(im.height, ch)) // 2))
        s.paste(tile, (x, yy))
    cell(olds, M, y2)
    cell(news, M + half + G, y2)
    cell(oldb, M, y2 + ch + G)
    cell(newb, M + half + G, y2 + ch + G)
    d.text((M, H - M + 2), "The previous revision is shown as it was drawn. Its rack would have left the nose at the last "
           "positions and its parked blade tip was not fully covered; both are corrected here.", font=font("Regular", 22), fill=MUTE)
    p = os.path.join(out, "board_orbit2_review.png")
    s.save(p, optimize=True)
    return p


# ------------------------------------------------------------------------------- lock diagram
def _lock_panel(d, ox, oy, sc, state, title, lines):
    """Section seen from above: back wall at the bottom, nose to the left. state: 0 locked,
    1 rack moved 2.5 mm (pawl lifted), 2 locked one notch forward."""
    P = lambda x, y: (ox + x * sc, oy - y * sc)
    R = lambda x0, y0, x1, y1, **k: d.rectangle((*P(x0, y1), *P(x1, y0)), **k)
    cx = 13.0 if state < 2 else 3.0
    shift = 2.5 if state == 1 else 0.0
    lift = 2.7 if state == 1 else 0.0
    X1 = 50.0
    # back wall with notches (the lock windows)
    R(0, 0, X1, 3.0, fill=GRAPH)
    for n in (4.0, 14.0, 24.0, 34.0, 44.0):   # schematic: evenly spaced working windows
        R(n - 1.75, -0.2, n + 1.75, 3.2, fill=BG)
    # blade, flat against the wall, butting the carriage
    R(0, 3.3, cx, 3.85, fill=STEEL)
    # carriage: body with a pocket; pawl arm along the wall
    R(cx, 5.3, cx + 27, 9.6, fill=PART_OR)
    R(cx, 3.3, cx + 3.0, 5.4, fill=PART_OR)
    R(cx + 23.5, 3.3, cx + 27, 5.4, fill=PART_OR)             # backstop behind the tooth
    R(cx + 6.5, 5.3, cx + 19.5, 8.6, fill=BG)                  # pocket for the shuttle tab
    root = (cx + 3.0, 4.05)
    th = math.atan2(lift, 18.0)

    def rot(x, y):
        dx, dy = x - root[0], y - root[1]
        return P(root[0] + dx * math.cos(th) - dy * math.sin(th), root[1] + dx * math.sin(th) + dy * math.cos(th))
    d.polygon([rot(cx + 3.0, 3.35), rot(cx + 22.8, 3.35), rot(cx + 22.8, 4.75), rot(cx + 3.0, 4.75)], fill=PART_OR)
    d.polygon([rot(cx + 19.6, 0.5), rot(cx + 22.4, 0.5), rot(cx + 22.4, 3.4), rot(cx + 19.6, 3.4)], fill=PART_OR)
    px, py = cx + 13.0, 6.3
    d.polygon([rot(px - 0.6, 4.7), rot(px + 0.6, 4.7), rot(px + 0.6, py), rot(px - 0.6, py)], fill=PART_OR)
    # shuttle: rack bar + tab with the V slot
    sx = cx + 13.0 + (shift if state == 1 else 0.0)
    R(0.5, 10.2, X1 - 0.5, 13.0, fill=SHUT)
    for k in range(15):
        tx = 1.6 + (shift % 3.1) + k * 3.1
        if tx + 2.2 > X1 - 0.5:
            break
        d.polygon([P(tx, 13.0), P(tx + 0.7, 14.5), P(tx + 1.5, 14.5), P(tx + 2.2, 13.0)], fill=SHUT)
    R(sx - 5.2, 5.6, sx + 5.2, 10.3, fill=SHUT)
    d.line([P(sx - 2.9, 8.3), P(sx, 6.3), P(sx + 2.9, 8.3)], fill=BG, width=int(1.7 * sc), joint="curve")
    for e in (P(sx - 2.9, 8.3), P(sx + 2.9, 8.3), P(sx, 6.3)):
        r = 0.85 * sc
        d.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=BG)
    pc = rot(px, py)
    r = 0.62 * sc
    d.ellipse((pc[0] - r, pc[1] - r, pc[0] + r, pc[1] + r), fill=PART_OR, outline=INK, width=2)

    def arrow(a, b, col=INK):
        d.line([a, b], fill=col, width=5)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s_ in (-1, 1):
            d.line([b, (b[0] - 20 * math.cos(ang + s_ * 0.45), b[1] - 20 * math.sin(ang + s_ * 0.45))], fill=col, width=5)
    f = font("Medium", 22)
    if state == 0:
        arrow(P(1.0, 5.6), P(8.5, 5.6))
        d.text(P(0.6, 8.4), "cutting force", font=f, fill=INK)
    if state == 1:
        arrow(P(46.5, 16.6), P(39.5, 16.6))
        arrow(rot(cx + 21.0, 5.6), rot(cx + 21.0, 8.0))
    if state == 2:
        arrow(P(cx + 21.0, 7.6), P(cx + 21.0, 5.2))
    d.text((ox, oy - 18.6 * sc), title, font=font("SemiBold", 30), fill=INK)
    yy = oy + 1.2 * sc
    for ln in lines:
        d.text((ox, yy), ln, font=font("Regular", 23), fill=(70, 70, 72))
        yy += 32


def mechanism(out):
    W, M, G = 2400, 70, 22
    cw = W - 2 * M
    ex = Image.open(os.path.join(out, "orbit2_exploded.png")).convert("RGB")
    cut = Image.open(os.path.join(out, "orbit2_cutaway.png")).convert("RGB")
    anchors = json.load(open(os.path.join(out, "orbit2_exploded_anchors.json")))
    cmap = json.load(open(os.path.join(out, "orbit2_cutaway_map.json")))
    ex_w = 1500
    ex_h = int(ex_w * ex.height / ex.width)
    cut_h = int(cw * cut.height / cut.width)
    lock_h = 560
    head = 210
    H = head + ex_h + G + cut_h + G + lock_h + M + 40
    s = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(s)
    _header(d, W, M, "printed mechanism", "Six printed parts. The gears only move the blade; the cutting load goes through a pawl "
            "in the body wall.", "ODD LAYER  ·  layout, not CAD")
    # exploded view + legend
    y = head
    s.paste(ex.resize((ex_w, ex_h), Image.LANCZOS), (M, y))
    d.text((M + 22, y + 18), "EXPLODED, SEEN FROM THE BACK", font=font("Medium", 22), fill=(70, 70, 70))
    lx = M + ex_w + 44
    ly = y + 30
    for i, (k, name, text) in enumerate(LEGEND, 1):
        ax, ay = anchors[k]
        _dot(d, (M + ax * ex_w, y + ay * ex_h), i)
        _dot(d, (lx + 24, ly + 24), i)
        d.text((lx + 66, ly + 4), name, font=font("SemiBold", 30), fill=INK)
        yy = ly + 46
        words, line = text.split(), ""
        for w_ in words:
            if d.textlength(line + " " + w_, font=font("Regular", 23)) > W - M - lx - 66:
                d.text((lx + 66, yy), line, font=font("Regular", 23), fill=(70, 70, 72))
                yy += 31
                line = w_
            else:
                line = (line + " " + w_).strip()
        d.text((lx + 66, yy), line, font=font("Regular", 23), fill=(70, 70, 72))
        ly = yy + 54
    # cutaway with leaders
    y2 = y + ex_h + G
    s.paste(cut.resize((cw, cut_h), Image.LANCZOS), (M, y2))
    d.text((M + 22, y2 + 18), "CUTAWAY THROUGH THE GEAR LAYER", font=font("Medium", 22), fill=(70, 70, 70))

    def cp(x, z):
        return (M + cw / 2 + (x - cmap["cx"]) / cmap["ortho"] * cw * -1, y2 + cut_h / 2 - (z - cmap["cz"]) / cmap["ortho"] * cw)
    f = font("Medium", 24)
    lb = cmap["labels"]
    for (key, tx, tz, text) in [("pinion", lb["pinion"][0] - 30, 46, "12-tooth pinion, part of the wheel"),
                                ("rack", lb["rack"][0] + 6, -24, "rack (shuttle)"),
                                ("carriage", lb["carriage"][0] + 26, 46, "carriage and pawl"),
                                ("blade", 30, -24, "blade, flat against the back wall")]:
        x, z = lb[key]
        a, b = cp(x, z), cp(tx, tz)
        d.line([a, b], fill=INK, width=3)
        d.ellipse((a[0] - 6, a[1] - 6, a[0] + 6, a[1] + 6), fill=INK)
        w_ = d.textlength(text, font=f)
        bx = b[0] - w_ / 2
        d.rectangle((bx - 12, b[1] - 20, bx + w_ + 12, b[1] + 20), fill=WHITE)
        d.text((bx, b[1] - 15), text, font=f, fill=INK)
    # lock sequence
    y3 = y2 + cut_h + G
    d.rectangle((M, y3, W - M, y3 + lock_h), fill=WHITE)
    d.text((M + 22, y3 + 18), "LOCK SEQUENCE, SECTION SEEN FROM ABOVE (BACK WALL AT THE BOTTOM, NOSE TO THE LEFT)",
           font=font("Medium", 22), fill=(70, 70, 70))
    pw = (cw - 80) / 3
    sc = (pw - 60) / 50.0
    oy = y3 + 395
    _lock_panel(d, M + 40, oy, sc, 0, "1  Locked",
                ["Pawl tooth sits in a wall window; its spring arm is relaxed.",
                 "Load path: blade, carriage, tooth, wall. No gear involved."])
    _lock_panel(d, M + 40 + pw, oy, sc, 1, "2  Roll the wheel",
                ["The rack moves 2.5 mm before the carriage does.",
                 "Its V slot lifts the pawl clear, then picks the carriage up."])
    _lock_panel(d, M + 40 + 2 * pw, oy, sc, 2, "3  Let go",
                ["The arm is meant to spring back and re-centre the rack,",
                 "dropping the tooth into the next window. Untested."])
    d.text((M, H - M + 2), "Layout and proportions only. Tooth form, fits and the spring arm are placeholders until the "
           "test coupons are printed.", font=font("Regular", 22), fill=MUTE)
    p = os.path.join(out, "board_orbit2_mechanism.png")
    s.save(p, optimize=True)
    return p


def make_all(out):
    return [exterior(out), review(out), mechanism(out)]
