# MakerWorld listing kit: Gemscale Flexi Octopus

This page has what you need to publish the octopus on MakerWorld: title, description, tags,
print profiles and a photo plan. Nobody can guarantee downloads. The things that help most
on MakerWorld are real photos, a short video of it moving, ready-to-print Bambu profiles and
a clear title. **Fast, small prints also get printed more often**, which is why the octopus
comes in a ~40 min mini version.

---

## 0. Rules to follow before publishing

1. **Print it and photograph it.** MakerWorld requires at least one **real photo of the
   printed model** (since 5 Feb 2026). Listings without one can lose visibility. Use the
   renders in `renders/` as extra images only, and put your real photo first.
2. **Slice for real numbers.** The print times and weights in this repo are estimates. Put
   the numbers Bambu Studio gives you in the description and profiles.
3. **AI disclosure.** This design and its generator were made with an AI assistant (Claude).
   Label the model honestly with the "AI-Generated Content" option on the upload form, and
   check the current policy, including before applying to the Exclusive program.
4. **Keep the name original.** "Gemscale" is this series' own name. Don't reuse other
   creators' model names.
5. **Choose a licence** on the upload form. The Standard Digital File License or CC BY-NC
   are common for toys.

---

## 1. Title

**Recommended:**
> Gemscale Flexi Octopus – Print-in-Place, No Supports, Fast Print

Alternatives to A/B test later:
- `Cute Flexi Octopus | Articulated | Print in Place | 40 min Mini`
- `Articulated Gem Octopus – One-Piece, Supportless, Fits Any Bed`

Put the words people search for ("flexi", "octopus", "print in place", "no supports",
"articulated") near the start.

---

## 2. Images and video (4:3, e.g. 1600 × 1200)

Upload them in this order. The first image is your cover.

1. **Real photo (cover):** the printed octopus on a desk or in your hand, plain background,
   daylight. Silk or two-tone prints stand out in the feed.
2. **Close-up photo** of the face and eyes.
3. **Build-plate photo** straight off the printer, to prove it prints in one piece.
4. **Video (10–20 s)** of the tentacles wiggling. Flexi toys sell on motion.
5. `promo_card.png`: a 4:3 card with the headline features.
6. Renders as extra images: `standard_cover_hero.png`, `standard_cover_top.png`,
   `standard_cover_face.png`, `standard_cover_plate.png`.
7. Colour ideas: `standard_blackgold_cover_hero.png` (matches the Gemscale Dragon),
   `standard_galaxy_cover_hero.png`, `mini_cover_hero.png` (ocean), `mini_cover_plate.png`.

---

## 3. Description (ready to paste)

> 🐙 **Gemscale Flexi Octopus**: a cute, faceted octopus that prints **in one piece, fully
> assembled, with no supports**, then wiggles straight off the plate.
>
> **Why you'll like it**
> - Print-in-place joints: no assembly, no glue, no supports
> - Gem-cut mantle, big round eyes, and eight tentacles with curly spiral tips
> - **Fast:** the mini prints in about 40 minutes
> - Small footprint: fits every bed, A1 mini included
> - Every joint swings ±35° and is collision-checked through its full range
> - **Two-tone trick:** one filament change at **6.4 mm** (mini: 5.0 mm) gives the head a
>   second colour. No AMS needed.
>
> **Versions (print profiles)**
> - **Standard**: 106 mm across, 40 joints, about [TIME] and [G] g
> - **Mini**: 65 mm across, 24 joints, about [TIME] and [G] g
> - **Mini keychain**: the mini with a keyring hole through the head
>
> **Print settings**
> - 0.20 mm layer height (the joints are designed for it)
> - **Supports OFF**, brim off
> - 2 walls, 15 % infill, PLA or silk PLA
> - Keep part cooling on so the small joint bridges come out clean
>
> **After printing**
> Bend each tentacle joint gently from side to side. The first bend frees it.
>
> **Tips**
> - Joints fused? Your printer runs tight. Use the included **clearance 0.40** file.
> - Want it multicolour? Split to parts in Bambu Studio and colour the head and each ring of
>   tentacle segments.
>
> Part of the Gemscale series. Check out the Gemscale Flexi Dragon too! Post your make.
> I'd love to see your colours! 💜

Fill in [TIME] and [G] from your slices.

---

## 4. Tags

`octopus` `flexi octopus` `articulated octopus` `articulated` `flexi` `print in place`
`no supports` `fidget` `fidget toy` `desk toy` `toy` `cute` `ocean` `sea creature`
`low poly` `gem` `A1 mini` `fast print` `keychain` `gift`

**Category:** Toys & Games (pick the figures or fidget-toy sub-category if one is offered).

---

## 5. Print profiles (Bambu Studio)

| Profile name | File | Printers | Notes |
|---|---|---|---|
| Standard octopus | `models/GemscaleOctopus_standard_seed7.3mf` | any | 0.20 mm Standard |
| Mini octopus (fast) | `models/GemscaleOctopus_mini_seed7.3mf` | any | quick test print |
| Mini keychain | `models/GemscaleOctopus_mini_seed7_keyring.3mf` | any | |

Optional fourth profile: **"Two-tone head"**, the standard octopus with a filament change at
Z = 6.4 mm. Multicolour thumbnails get noticeably more clicks.

Also attach `GemscaleOctopus_standard_seed7_clearance0p40.3mf` as an extra file with looser
joints.

How to make each profile:
1. In Bambu Studio, choose **File > Import** and load the `.3mf`.
2. Pick the printer, the **0.20mm Standard** process and your filament.
3. Make sure **Support** is off. Keep the defaults for everything else.
4. Optional two-tone: move the layer slider to 6.4 mm (mini: 5.0 mm), right-click, and choose
   **Add color change**.
5. **Slice.** In the preview, scroll through the layers near the joints and check that you
   can see a thin gap around every knob.
6. Print it, take photos, then use **Publish > Upload print profile**.

---

## 6. Launch plan

- **Cross-promote:** link the octopus from the dragon listing and the dragon from the
  octopus. A named series helps both.
- **One listing, several profiles.** Don't post near-identical listings.
- **Reply to every comment and "Make"** in the first week. Early activity helps ranking.
- Pin the video.

---

## 7. Making your own variants

```bash
python gemscale_octopus.py --preset standard --seed 123        # different mantle facets
python gemscale_octopus.py --preset standard --clearance 0.40  # looser joints
python gemscale_octopus.py --preset mini --keyring             # keychain
```

Each run writes a `_report.txt`. Only publish variants whose checks all say **PASS**, and
test-print them first.
