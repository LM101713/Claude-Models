# GS-05 GIFT SLIDE: physical test plan

Nothing about this design has been proven on a printer yet. Each test below has a pass criterion and the parameter to change if it fails. All parameters are in `gs/params.py`; rerun `python giftslide.py` after any change and all 120 checks run again.

Equipment: calipers, a kitchen scale (push the lid against it: grams × 0.0098 = newtons), a cheap 0.05–1 mm feeler-gauge set, a knife, and a gift card.

## T0: First print: the fit coupon (≈ 28 min, ≈ 15 g)

`models/3mf/GS05_fit_coupon_first.3mf`. Bambu PLA Basic, 0.20mm Standard @BBL A1M, textured PEI, no supports.

| Check | Pass |
|---|---|
| All four parts release cleanly; no stringing across the lid slots | yes (otherwise clear the slot with a blade and note it) |
| STD lid snaps in from the open end with one firm push | ≤ 0.5 kg on the scale |
| STD lid: click felt when leaving the closed end | 200–600 g on the scale (2–6 N) |
| STD lid: clear stop at the end of travel (12 mm on the coupon) | ≥ 2.5× the click |
| STD lid glides with no grinding between click and stop | yes |
| Lid top flush with the rim (feel with a fingernail) | within one layer |

Pick the lid using the table in `ASSEMBLY.md`. **Record which coupon lid was best: it is the most valuable single data point for the model.**

## T1: Full plate + measurements

`GS05_gift_slide_plate.3mf` with the lid chosen in T0.

| Measure | Nominal | Accept |
|---|---|---|
| Tray outside L × W × H | 91.6 × 65.0 × 7.2 | ±0.2 |
| Lid width across the lands | 60.4 | ±0.1 |
| Lid thickness | 2.8 | ±0.1 |
| Rim opening (between the lip tips) | 59.2 | ±0.15 |
| Flexure slot width (feeler) | 0.8 | ≥ 0.6, clear along its length |
| Lid flatness on glass (feeler under a corner) | 0 | ≤ 0.3 |
| Knife-section of the coupon tray across the relief track: ceiling droop | 0 | ≤ 0.2 |

## T2: Forces

Average 5 runs each. Scale reading = force.

| Event | Model (nominal) | Accept |
|---|---|---|
| Opening click | 3.6 N | 2 – 6 N |
| Closing click | 2.9 N | 1.5 – 5 N |
| Glide | ≈ 0 | < 0.5 N, no stick-slip |
| Open stop (pull until it lets go) | 11.8 N | 6 – 20 N, and > 2.5× opening |
| Snap-in | 2.3 N | < 5 N |

If the click is too firm: lower `r1_open_deg` (35 → 30). If too weak: raise `bump_p` (0.60 → 0.65). If the stop never lets go: lower `stop_deg` (60 → 55). Then compare the measured forces with the model to back out μ and E for the next revision.

## T3: Retention and abuse

| Test | Pass |
|---|---|
| Closed, card inside, shaken hard for 10 s in all orientations | stays closed |
| Closed, held upside down, tapped on the table 10× | stays closed |
| Drop from 1 m onto wood: closed, then open at the stop | nothing breaks; the lid stays in or pushes back in |
| Open at the stop, 1 kg pressed on the overhanging lid tip | no permanent set, lid doesn't pop out of the grooves |
| Twist the closed box by hand (diagonal corners) | lid stays in, still slides |

## T4: Life

500 full cycles: open to the stop, close to the click.

| Check after 100 / 500 cycles | Pass |
|---|---|
| Opening click | ≥ 70 % of the T2 value |
| Flexure slot ends | no whitening or cracks |
| Bump crest | no visible flat |

Also leave one unit closed for 2 weeks and one open at the stop for 2 weeks, then re-measure the clicks (creep check: both should be unchanged, because the beam is unloaded at rest).

## T5: Gift use

| Test | Pass |
|---|---|
| Card + 4 notes folded in quarters | lid closes and clicks normally; no note edge catches |
| Push-hole lift with the lid at the stop | card can be picked out in < 5 s by someone who has never seen the box |
| Five people handed the closed box with no instructions | ≥ 4 open it within 10 s |

## T6: Environment (optional)

Closed box at 45 °C for 1 h (a car interior in spring): it still slides and clicks, and the lid stays flat to 0.3 mm.

## T7: Other printers and materials

Coupon + full plate on at least two other printers (for example a P1S and a Prusa MK4 or Ender-3), and one other PLA brand. Record which lid each one needs. Optional: PETG (expect forces about 30 % lower).

## Publication gate

Publish on MakerWorld only when **T0–T5 pass on the A1 mini** and **T0 passes on two other printers**. Update the force numbers in `README.md` and `MAKERWORLD_LISTING.md` with measured values, and replace the print-time estimates with Bambu Studio's.

## Failure modes and where to look

| Symptom | Likely cause | Fix |
|---|---|---|
| Lid won't start into the tray | lid upside down / tilted; elephant's foot on the lid's bottom edge | flip it; Loose lid |
| Stiff along the whole travel | tight printer (c < 0.05) or the relief ceiling drooping onto the bump | Loose lid; check T1 droop |
| Click very hard, no spring feel | flexure slot printed shut or strung | clear the slot |
| No click, lid slides open by itself | loose printer | Snug lid |
| Lid pulls off too easily | loose printer, or very slippery filament | Snug lid; `stop_deg` 60 → 65 |
| Lid can't be removed even with a hard pull | sticky filament (μ near 0.58 self-locks a 60° flank) | `stop_deg` 60 → 55 |
| Lid lifts at the open end | dovetail overlap lost (walls spread or lid bowed) | check flatness; Snug lid |
