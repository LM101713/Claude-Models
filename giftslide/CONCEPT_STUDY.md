# GS-05 GIFT SLIDE: concept study

This study compares sliding mechanisms for a card-sized gift holder and explains which one was chosen. It covers the brief, the competitors, seven candidate mechanisms, where the detent spring should live, and what changed once the chosen design went through validation.

## 1. The brief, restated as engineering targets

| Requirement | Target used |
|---|---|
| Hold an ID-1 card (85.60 × 53.98 × 0.76 mm) securely | Pocket with 0.8 mm clearance per side. The card must not touch the lid at any point of the travel. |
| Folded cash | ≥ 2.0 mm headroom above the card: four notes folded in quarters (≈ 0.44 mm each) |
| Satisfying slide that reveals the gift | A defined break-away click, a free glide and a firm end stop, with most of the card face uncovered |
| No metal, screws, springs or glue | Every spring is a printed PLA flexure; the parts fit together with no tools |
| One or two pieces, minimal assembly | 2 parts, one push to assemble |
| No supports | Every downward face is ≤ 45° or is a short bridge or overhang (≤ 0.7 mm) |
| ≤ 90 min, ≤ 35 g, A1 Mini (180³) | Both parts on one plate |
| PLA, tolerant of normal FDM error | Works from a tight printer (−0.15 mm per side on slots) to a loose one (+0.15), with a fit coupon and lid variants to cover the extremes |

## 2. Competitors: what to avoid

The three reference products are popular because a gift card in a box is better than a gift card in an envelope. Their weak points, as their makers describe them, are the same weak points the brief names: several screws or separate linkages, glue, and many minutes of assembly. A puzzle box also annoys some recipients more than it delights them. None of their geometry, mechanisms or styling was used here. The opportunity is one smooth, obvious action that feels engineered: *push, click, glide, stop, there's the card.*

## 3. Candidate mechanisms

| # | Concept | How it reveals | Parts | Key risk |
|---|---|---|---|---|
| A | **Matchbox**: sleeve + drawer | push the drawer out of the sleeve | 2 | The sleeve is a tube: printed flat, its roof is a ~58 mm bridge that sags onto the drawer; printed on edge, it is a 7 mm wide, 62 mm tall wall that wobbles on a bed-slinger. Double walls everywhere use the most material. |
| B | **Print-in-place captured lid** | lid slides in dovetails, printed in place | 1 | The lid's underside becomes a 55 mm bridge over the pocket, and its dovetail bevels become 45° overhangs over a 0.3 mm air gap. If that gap fuses, the gift is ruined and there is no fallback. |
| C | **Slide-top tray (dovetail lid)** | lid slides off along the long axis | 2 | Generic on its own. It needs a detent to stay shut and a stop so the lid doesn't fall off. |
| D | **Pop-up "toaster"** | slider pushes the card up out of a slot via a ramp | 2–3 | A 30–45° ramp needs ~35 mm of extra length: ~130 × 75 × 16 mm, over 40 g. Folded notes can't ride a ramp in a slot. |
| E | **Split doors** | two half-lids part from the middle | 3 | Each door has only half the engagement length, so at full travel it is barely in its groove. Three parts. |
| F | **Tambour / shutter** | flexible slatted lid rolls round the end | 1–2 | Slat hinges are fragile in PLA and need a lot of tuning. Far too complex for the payoff. |
| G | **Sequential-puzzle lid** | lid must follow an L-path or maze | 2 | This is the competitors' "annoying" niche, and the brief asks to simplify. |

### Scoring (1 = poor, 5 = excellent; weight in brackets)

| Criterion | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Print reliability, no supports (×3) | 2 | 2 | **5** | 3 | 4 | 1 | 4 |
| Tolerance to printer variation (×3) | 3 | 1 | **4** | 3 | 3 | 1 | 3 |
| Satisfying reveal (×2) | 4 | 4 | **4*** | 5 | 4 | 4 | 2 |
| Material / time budget (×2) | 2 | 4 | **5** | 1 | 4 | 3 | 4 |
| Assembly simplicity (×2) | 5 | 5 | **5** | 3 | 3 | 3 | 4 |
| Cash compatibility (×1) | 4 | 4 | **5** | 1 | 4 | 4 | 4 |
| Originality (×1) | 2 | 3 | **4*** | 4 | 3 | 4 | 1 |
| **Weighted total (max 70)** | 43 | 42 | **64** | 41 | 50 | 34 | 46 |

\* Only once C gets the detent described below. A plain slide-top box scores 3 on both.

**Choice: C, a two-piece tray with a dovetailed sliding lid.** It is the only concept in which both parts print flat on their largest face with no bridges. The tray prints floor-down: its 45° lip underside is a supported overhang. The lid prints underside-down: its dovetail bevels face upward. Every fit is lateral (XY), the direction FDM controls best, and the vertical fits sit on whole-layer heights. What C lacks is feel and retention, so section 4 is where most of the design effort went.

## 4. Where the detent spring lives

A detent needs something compliant. Six places were considered:

| Option | Verdict |
|---|---|
| Bend the whole lid plate | Too stiff: lifting the middle of a 2.8 mm × 57 mm plate by 0.4 mm takes ~20 N, and the visible top would bulge. |
| Bend a whole tray wall | Too stiff: 0.002 mm per N. A local load on a 2.6 mm wall that is 7 mm tall barely moves it. |
| Vertical fin standing on the tray floor | It would bend across the layer lines, with 5 % strain at the root. It would break. |
| Floor tongue with a post | The tongue would have to deflect below the bottom of the tray (blocked by the table). The post would also load it in torsion. |
| Cantilever cut from the lid top | Works, but leaves a U-shaped cut in the most visible face. |
| **Fixed-fixed beam along each lid edge, cut free by a slot hidden in a shadow gap** | **Chosen.** It is printed flat, so the beads run along the beam and it bends in the plane of the layers (the strongest direction for a PLA flexure). It sits inside a deliberate 1.5 mm shadow gap between lid and rim, so from above the slot reads as part of the gap. |

### How the bump meets the tray: the relief-track detent

A first version used ridges sticking out of the groove face for the bump to climb. It fails geometrically: any ridge the bump has to cross is also crossed by the rigid lid edge beside the bump, during travel or during assembly. The answer is to invert it. The **groove face itself is the ridge**, and a shallow **relief track** (0.45 mm deep) is cut into it wherever the bump should run free:

```
groove face ─────┐  parking  ┌──┐ R1 ┌──────────── travel track ───────────┐ stop ┌── entry ──┐ lead-in
                 └───────────┘  └────┘                                      └──────┘           └──╲
lid land    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                    ▲ bump (0.6 mm proud, on the flexure beam)
```

* **Parked (closed):** the bump sits in a pocket. The beam is unloaded, so nothing creeps while the gift waits under the tree.
* **R1:** a 0.6 mm crest of unrelieved face. Opening means climbing a 35° flank: the click. Closing climbs a 28° flank.
* **Travel track:** the bump runs free (0.1 mm clearance nominal), the beam is unloaded, and there is no wear.
* **Open stop:** the track ends in a 60° flank. The lid stops, held by about 12 N. A deliberate tug pulls it off for loading or cleaning.
* **Entry zone + lead-in:** pushing the lid in from the open end snaps the bump over the same face into the track (≈ 2.3 N). Once in, the lid is captive.

Nothing else on the lid ever touches a raised feature. The only lateral contacts are the land and dovetail guides, and they run on a constant surface. That separation is what makes the feel predictable.

### Why not a permanent (one-way) captive stop?

With a 75–90° stop flank the lid could never come out again. That was rejected for two reasons. Loading and cleaning are easier with the lid off. A permanent snap is also the first thing to break when someone forces it. A 60° flank gives a stop that clearly reads as *the end* (more than 3× the click force) and still gives way without damage.

## 5. What validation changed

The checks in `giftslide.py` were run after every change. The design changed in these places:

1. **Symmetric 45° bump → asymmetric bump (65° front, 45° rear).** The model showed that when two inclined faces meet, the shallower one sets the force. With a 45° bump the 60° stop flank behaved like 45°, and the stop came out at 5 N, barely more than the click. With a 65° front flank the stop is 11.8 N and the click is still set by R1.
2. **R1 flanks 42° / 30° → 35° / 28°.** The first opening click was 5.2 N nominal and 7+ N on a tight printer, too firm for a gift. It is now 3.6 N nominal and 2.0 to 5.7 N across the print-variation corners.
3. **Snug lid added.** At the "very loose printer" corner (tray +0.15, lid −0.10 per side) the Standard lid's click fell to 1.0 N. A lid 0.10 mm wider per side restores 2.0 N. A Loose lid already existed for the opposite corner.
4. **The coupon tests all three lid fits.** One 28-minute plate tells you which lid suits your printer before you print the real thing.
5. **Two false alarms fixed in the checks themselves.** The 3-D cross-check first measured the overlap across both sides of the lid. On a tight printer, the end wall stopping the lid a little further out was first counted as a collision. Both were bugs in the measurement, not in the design. They are recorded here because a check that is wrong in the optimistic direction is worse than no check.
