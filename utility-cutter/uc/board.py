"""Concept boards: one sheet per concept (hero, side profile, top view, mechanism detail)."""

import os

from PIL import Image, ImageDraw, ImageFont

INTER = "/usr/share/fonts/opentype/inter/"
BG, INK, MUTE, ORANGE = (244, 243, 240), (28, 29, 32), (120, 120, 118), (255, 95, 15)

BOARDS = [
    dict(key="keel", code="01", name="KEEL", line="Raked monocoque slab  ·  press-to-slide sled  ·  steel pin in a notch ladder",
         detail="Sled, press button and the notch ladder"),
    dict(key="orbit", code="02", name="ORBIT", line="Stationary geared thumb wheel  ·  rack-driven blade  ·  hex index lock",
         detail="Thumb wheel and hex index lock"),
    dict(key="loop", code="03", name="LOOP", line="Guard frame with 40° skid  ·  toothed carriage  ·  wheel clamp",
         detail="Clamp wheel on its rail"),
]


def font(weight, size):
    for p in (INTER + f"Inter-{weight}.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fit(im, w, h):
    """Centre-crop to the target aspect, then resize."""
    r = w / h
    if im.width / im.height > r:
        nw = int(im.height * r)
        im = im.crop(((im.width - nw) // 2, 0, (im.width + nw) // 2, im.height))
    else:
        nh = int(im.width / r)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height + nh) // 2))
    return im.resize((w, h), Image.LANCZOS)


def make(out, b):
    W, M, G = 2400, 70, 22
    img = lambda tag: Image.open(os.path.join(out, f"{b['code']}_{b['key']}_{tag}.png")).convert("RGB")
    cw = W - 2 * M
    hero_h = int(cw * 1100 / 1800)
    half = (cw - G) // 2
    side = img("side")
    side_h = int(half * side.height / side.width)
    top_h = int(half * 420 / 1800)
    row_h = max(side_h, 560)
    head = 210
    H = head + hero_h + G + row_h + M + 40
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((M, 62), b["code"], font=font("SemiBold", 72), fill=ORANGE)
    d.text((M + 120, 62), b["name"], font=font("SemiBold", 72), fill=INK)
    d.text((M + 2, 152), b["line"], font=font("Regular", 28), fill=MUTE)
    t = "ODD LAYER  ·  18 mm snap-off cutter  ·  concept study"
    f = font("Medium", 24)
    d.text((W - M - d.textlength(t, font=f), 96), t, font=f, fill=MUTE)

    y = head
    sheet.paste(fit(img("hero"), cw, hero_h), (M, y))
    y += hero_h + G
    # left column: side profile over top view; right column: detail
    lab = font("Medium", 22)
    left_h = row_h
    sh = left_h - top_h - G
    sheet.paste(fit(side, half, sh), (M, y))
    sheet.paste(fit(img("top"), half, top_h), (M, y + sh + G))
    sheet.paste(fit(img("detail"), half, left_h), (M + half + G, y))
    for (x, yy, text) in [(M + 22, head + 18, "Three-quarter"), (M + 22, y + 16, "Side profile"),
                          (M + 22, y + sh + G + 14, "Top view"), (M + half + G + 22, y + 16, b["detail"])]:
        d.text((x, yy), text.upper(), font=lab, fill=(70, 70, 70))
    d.text((M, H - M + 2), "Concept-stage geometry rendered from solids at true scale. Surface finish shown is design intent, "
           "not an FDM print.", font=font("Regular", 22), fill=MUTE)
    p = os.path.join(out, f"board_{b['code']}_{b['key']}.png")
    sheet.save(p, optimize=True)
    return p


def lineup(out):
    ims = [Image.open(os.path.join(out, f"{b['code']}_{b['key']}_side.png")).convert("RGB") for b in BOARDS]
    w = 1500
    ims = [i.resize((w, int(i.height * w / i.width)), Image.LANCZOS) for i in ims]
    H = sum(i.height for i in ims)
    sheet = Image.new("RGB", (w, H), BG)
    d = ImageDraw.Draw(sheet)
    y = 0
    for b, i in zip(BOARDS, ims):
        sheet.paste(i, (0, y))
        d.text((36, y + 26), f"{b['code']}  {b['name']}", font=font("SemiBold", 34), fill=(40, 40, 42))
        y += i.height
    p = os.path.join(out, "lineup_side_profiles.png")
    sheet.save(p, optimize=True)
    return p


def make_all(out):
    return [make(out, b) for b in BOARDS] + [lineup(out)]
