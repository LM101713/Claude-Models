# MakerWorld listing kit: Gemscale Flexi Bat

This page has what you need to publish the bat on MakerWorld: title, description, tags,
print profiles and a photo plan. Nobody can guarantee downloads. The things that help most
are real photos, a short video of the wings moving, ready-to-print profiles, and timing.
**Post it in early to mid October** so it's live for Halloween searches.

---

## 0. Rules to follow before publishing

1. **Print it and photograph it.** MakerWorld requires at least one **real photo of the
   printed model**. Use the renders in `renders/` as extra images only.
2. **Slice for real numbers.** The print times and weights in this repo are estimates.
3. **AI disclosure.** This design and its generator were made with an AI assistant (Claude).
   Tick the "AI-Generated Content" option on the upload form, and check the current policy.
4. **Keep the name original.** "Gemscale" is this series' own name.
5. **Choose a licence** on the upload form.

---

## 1. Title

**Recommended:**
> Gemscale Flexi Bat – Print-in-Place, Folding Wings, No Supports

Alternatives:
- `Cute Flexi Bat | Articulated Wings | Halloween | Print in Place`
- `Articulated Halloween Bat – One-Piece, Supportless, Fast Print`

---

## 2. Images and video (4:3, e.g. 1600 × 1200)

1. **Real photo (cover):** the bat from above with its wings spread, on a dark background.
   Black and orange is the classic Halloween look.
2. **Face close-up photo:** ears, eyes and fangs.
3. **Build-plate photo**, to prove it prints in one piece.
4. **Video (10–20 s):** flap the wings. Also hang the keychain version upside down.
5. `promo_card.png`
6. Renders as extra images: `standard_cover_hero.png`, `standard_cover_top.png`,
   `standard_cover_face.png`, `standard_cover_plate.png`.
7. Colour ideas: `standard_pumpkin_cover_hero.png`, `standard_vampire_cover_top.png`,
   `standard_blackgold_cover_hero.png` (matches the Gemscale Dragon),
   `mini_ghost_cover_hero.png` (glow-in-the-dark idea), `mini_keyring_cover_top.png`.

---

## 3. Description (ready to paste, casual)

> 🦇 **Gemscale Flexi Bat**
>
> Meet the newest member of the Gemscale family! He's a little faceted bat that prints in
> one go, fully assembled, with no supports. Pop him off the plate, bend the joints once,
> and he's ready to flap.
>
> Both wings are jointed at the shoulder, elbow, wrist and knuckle, so they fold and spread
> like a real bat's. His belly and tail wiggle too. He has big eyes, cupped ears, tiny fangs,
> finger bones and little clawed feet.
>
> **What you get**
> - **Standard:** 16.4 cm wingspan
> - **Mini:** 11 cm wingspan, super quick to print
> - **Mini keychain:** the loop is on his tail, so he hangs upside down from your keys 🙃
> - **Looser-joint version:** for printers that run a bit tight, or for PETG
>
> **How I printed it**
> - 0.2 mm layers (the joints are made for this)
> - Supports off, no brim
> - 2 walls, 15% infill
> - My standard took about [TIME] and [G] g
>
> **When it's done**
> Bend each joint gently. The first bend frees it. If any are stuck solid, print the
> looser-joint version.
>
> **Colour tips**
> Black and orange is perfect for Halloween. For a two-tone bat without an AMS, add a colour
> change at 5.2 mm (mini: 4.7 mm). The head and body change colour and the wings stay the
> first colour. Glow-in-the-dark is fun too (use the looser-joint file).
>
> Part of the Gemscale series. Check out the Flexi Dragon and Flexi Octopus too! Post your
> makes, I'd love to see them 🦇

Fill in [TIME] and [G] from your print or slice.

---

## 4. Tags

`bat` `flexi bat` `articulated bat` `halloween` `halloween bat` `flexi` `articulated`
`print in place` `no supports` `fidget` `fidget toy` `desk toy` `cute` `spooky`
`low poly` `gem` `keychain` `A1 mini` `fast print` `gift`

**Category:** Toys & Games (pick the figures or fidget-toy sub-category if one is offered).
Halloween decor is a good secondary fit.

---

## 5. Print profiles (Bambu Studio)

| Profile name | File | Notes |
|---|---|---|
| Standard bat | `models/GemscaleBat_standard_seed7.3mf` | 0.20 mm Standard |
| Mini bat (fast) | `models/GemscaleBat_mini_seed7.3mf` | quick test print |
| Mini keychain | `models/GemscaleBat_mini_seed7_keyring.3mf` | hangs from its tail |

Optional fourth profile: **"Two-tone Halloween"**, the standard bat with a filament change
at Z = 5.2 mm (black wings, orange head). Also attach
`GemscaleBat_standard_seed7_clearance0p40.3mf` as an extra file.

How to make each profile:
1. In Bambu Studio, choose **File > Import** and load the `.3mf`.
2. Pick the printer, the **0.20mm Standard** process and your filament. Make sure
   **Support** is off.
3. Optional two-tone: move the layer slider to 5.2 mm (mini: 4.7 mm), right-click, and
   choose **Add color change**.
4. **Slice**, then check the preview for a thin gap around every knob.
5. Print it, take photos, then use **Publish > Upload print profile**.

---

## 6. Launch plan

- **Timing:** publish by mid October. Halloween models peak in the two weeks before the 31st.
- **Cross-promote** the Gemscale Dragon, Octopus and Bat from each other's descriptions.
- **Reply to every comment and "Make"** in the first week.
- Pin the wing-flapping video.

---

## 7. Making your own variants

```bash
python gemscale_bat.py --preset standard --seed 123        # different facets
python gemscale_bat.py --preset standard --clearance 0.40  # looser joints
python gemscale_bat.py --preset standard --keyring         # big keychain bat
```

Only publish variants whose `_report.txt` checks all say **PASS**, and test-print them first.
