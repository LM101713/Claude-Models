# MakerWorld listing kit: Gemscale Flexi Dragon

This page has everything you need to publish the dragon on MakerWorld: title, description,
tags, print-profile setup and a photo plan. Nobody can guarantee downloads, but the listings
that do well on MakerWorld share the same basics. They have real photos of the print, a short
video of it moving, ready-to-print Bambu profiles for popular printers, and a clear title.
This kit covers all of those.

---

## 0. Rules to follow before publishing

1. **Print it and photograph it.** Since 5 Feb 2026, MakerWorld requires at least one **real
   photo of the printed model**; listings without one can have their visibility restricted.
   The renders in `renders/` can go in as extra images only. Put your real photo first.
2. **AI disclosure.** This design and the script that generates it were made with an AI
   assistant (Claude). MakerWorld asks creators to label models that are *primarily or
   entirely AI-generated* using the "AI-Generated Content" option on the upload form.
   Mislabelled models can lose visibility or be removed. Read the current policy and label
   the model honestly; if you're unsure, disclose it. Also check the rules before applying
   to the Exclusive program, which has its own AI restrictions.
3. **Keep the name original.** Don't reuse other creators' model names (for example the
   popular "Crystal Dragon" listings). "Gemscale" is this design's own name.
4. **Choose a licence** on the upload form. Standard Digital File License or CC BY-NC are
   common choices for toys.

---

## 1. Title

**Recommended:**
> Gemscale Flexi Dragon – Articulated, Print-in-Place, No Supports, Snap-in Wings

Alternatives to A/B test later:
- `Articulated Gem Dragon | Print in Place | Fits A1 mini | No Supports`
- `Flexi Dragon with Wings – One-Piece Print-in-Place, Supportless`

Put the words people search for ("flexi", "articulated", "print in place", "dragon",
"no supports") near the start.

---

## 2. Images and video (4:3, e.g. 1600 × 1200)

Upload them in this order. The first image is your cover.

1. **Real photo (cover):** the printed dragon in an S-curve on a desk, wings in, soft daylight,
   plain background. Two-tone prints stand out in the feed.
2. **Real photo in a hand**, to show the size and invite people to touch it.
3. **Build-plate photo** straight off the printer: the curled dragon with the wings inside
   the curl. This proves it prints in one piece.
4. **Video (10–20 s)** of you wiggling the dragon. Flexi models sell on motion.
5. Renders from this repo: `standard_cover_hero.png`, `standard_cover_head.png`,
   `standard_cover_side.png`, `standard_cover_plate.png`.
6. `joint_cutaway.png`, which explains the print-in-place joint (good for the description too).
7. Colour ideas: `standard_sunset_cover_hero.png`, `standard_obsidian_cover_head.png`,
   `mini_rainbow_cover_hero.png`.

---

## 3. Description (ready to paste)

> 🐉 **Gemscale Flexi Dragon** – a faceted, low-poly dragon that prints **in one piece, fully
> assembled, with no supports**, then wiggles straight off the plate.
>
> **Why you'll like it**
> - Print-in-place joints: no assembly, no glue, no supports
> - 31 cm long, yet curls up to fit the **A1 mini (180 mm)** bed
> - Crystal dorsal fins, armoured scales, horns, four legs and a spade tail
> - **Snap-in wings** that print on the same plate and press into the shoulders
> - Joints swing ±35° and are stopped before any part can collide
> - **Two-colour trick:** one filament change at **5.2 mm** turns the scales, fins and horns
>   a second colour (works without an AMS)
>
> **Versions (print profiles)**
> - **Standard**: ~31 cm, A1 mini and bigger, about 1 h 45 min, ~35 g
> - **Mini / keychain**: ~18 cm with a keyring loop, about 42 min, ~11 g
> - **Long**: ~45 cm for 256 mm beds (A1 / P1S / X1C / P2S), about 2 h 25 min, ~46 g
>
> **Print settings**
> - 0.20 mm layer height (the joints are designed for it)
> - **Supports OFF**, brim off
> - 2 walls, 15 % infill, PLA or silk PLA
> - Keep part cooling on so the small tongue bridges come out clean
>
> **After printing**
> 1. Flex every joint gently from side to side; the first bend frees it.
> 2. Press the wing tabs into the two slots on the shoulders (a drop of glue if loose).
>
> **Tips**
> - Joints fused? Your printer runs tight. Use the included **clearance 0.40** file.
> - The mini is a quick way to test your printer before the big one.
>
> Made with a procedural Blender script, with every joint collision-checked through its full
> range before release. Post your make – I'd love to see your colour combos! 💚

(If you share the generator script, add a line saying where to find it.)

---

## 4. Tags

`dragon` `flexi dragon` `articulated dragon` `articulated` `flexi` `print in place`
`no supports` `fidget` `fidget toy` `desk toy` `toy` `wings` `low poly` `gem` `crystal`
`A1 mini` `multicolor` `keychain` `gift` `fantasy`

**Category:** Toys & Games (pick the figures or fidget-toy sub-category if one is offered).

---

## 5. Print profiles (Bambu Studio)

Every profile is another way for people to find and print the model, and "print" actions
count toward your points. Aim for these three at launch:

| Profile name | File | Printers | Notes |
|---|---|---|---|
| Standard dragon – A1 mini | `models/GemscaleDragon_standard_seed7.3mf` | A1 mini, A1, P1S, X1C, P2S, H2D | 0.20 mm Standard |
| Mini keychain dragon | `models/GemscaleDragon_mini_seed7.3mf` | any | quick test print |
| Long dragon – 256 mm | `models/GemscaleDragon_long_seed7.3mf` | A1, P1S, X1C, P2S, H2D | |

Optional fourth profile: **"Two-colour (AMS)"**, the standard dragon with a filament change
at Z = 5.2 mm. Multi-colour thumbnails get noticeably more clicks.

Also attach `GemscaleDragon_standard_seed7_clearance0p40.3mf` as an extra file (looser joints
for printers that run tight or for PETG), plus the `_wings_only` file for people who want the
wings in a different colour.

How to make each profile:
1. In Bambu Studio, choose **File > Import**, then load the `.3mf`.
2. Pick the printer, the **0.20mm Standard** process and your filament.
3. Make sure **Support** is off. Keep the defaults for everything else.
4. Optional two-colour: move the layer slider to 5.2 mm (standard) or 3.8 mm (mini),
   right-click and choose **Add color change**.
5. **Slice.** In the preview, scroll through the layers around the joints and check that you
   can see a thin gap around every knob.
6. Print it, take photos, then use **Publish > Upload print profile** to add it to your
   model with plate images and your own photos.

---

## 6. Launch plan

- **Timing:** post before the Halloween weekend. Fantasy creatures get extra attention in
  October, and dragons stay popular all year.
- **One listing, several profiles.** Don't spam near-identical listings. Later, publish a
  genuinely different variant as its own model (for example a different skin or theme).
- **Reply to every comment and "Make"** in the first week; early activity helps ranking.
- Ask makers to post photos of their colour combos, since makes feed the algorithm.
- Pin the video. Flexi toys are all about motion.

---

## 7. Making your own variants with the script

```bash
# a different, still unique, dragon
blender -b -P gemscale_dragon.py -- --preset standard --seed 123 --render

# looser joints for printers that run tight (or PETG)
blender -b -P gemscale_dragon.py -- --preset standard --clearance 0.40

# wing-less "wyrm" for a second listing
blender -b -P gemscale_dragon.py -- --preset long --no-wings --seed 99
```

Each run writes a `_report.txt` with the size, recommended settings, colour-change height
and the results of the automatic checks. Only publish variants whose report says
**RESULT: PASS**, and test-print them first.
