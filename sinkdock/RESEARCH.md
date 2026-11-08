# SD-01 SINKDOCK: competitor research and market opportunity

_Research done on 2026-11-08 with web search. **MakerWorld pages could not be opened from the
build environment** (the host is not on its network allowlist), so the MakerWorld details below
come from search-result snippets: titles, short descriptions, and in a few cases rating counts
or comment excerpts. Download, like and boost counts could not be read. Open the links and check
them before relying on any number here._

## What the items actually measure

| Item | Researched size | Sources | Design value |
|---|---|---|---|
| Scrub Daddy Original | Ø 102–105 mm, 38–41 mm thick | WebstaurantStore (4 × 1.5 in), Staples (4 1/8 in), OnTime Supplies (4.13 × 1.63 in) | 46 mm bay |
| Scrub Mommy | Ø 95–105 mm, 38–41 mm thick | True Value / Do it Best (1.625 in thick), Tingstad (10 cm × 4 cm), Showcase (3.75 × 1.5 in) | 46 mm bay |
| Rectangular sponge (Scotch-Brite Heavy Duty class) | 111 × 66 × 17 mm (some listings 114 × 68, 15 mm thick) | 3M HD3-SIOC spec | 24.4 mm bay, stood on its short end |
| Dish brush (OXO Good Grips class) | about 279 mm long, about 76 mm across the head | WebstaurantStore, desertcart | handle envelope up to 32 × 26 mm (**handle cross-section not verified**) |

- **The brief assumed the Scrub Mommy is bigger than the Scrub Daddy. The sources say it isn't.**
  Both are about Ø 100–105 × 38–41 mm, so SinkDock gives them identical 46 mm bays: either sponge
  goes in either bay, and the labels are only a suggestion.
- A MakerWorld commenter (on the Clyde holder, 2408489) reports that a slot needs **at least 43 mm**
  for a standard sponge. SinkDock's 46 mm bay leaves 1.55–1.75 mm a side even for a 41 mm sponge
  plus 1.5 mm of assumed swelling.
- Scrub Daddy's own Daddy Caddy is listed at about 190 × 115 × 40 mm. It holds one sponge, uses
  two suction cups, and is $6.99 (https://scrubdaddy.com/daddy-caddy).
- No published data on how much these sponges swell when wet was found. SinkDock assumes 1.5 mm
  on every maximum dimension, and that needs a physical check.

## Competitors

### MakerWorld

| Model | What it does well | Where it falls short |
|---|---|---|
| [Simple Scrub Daddy Holder](https://www.makerworld.com/en/models/1055036) (single and double) | Drains back to the sink. Rated 5.0 from 107 ratings (snippet). PETG. | One or two sponges only, no brush, no flat sponge. About 4.7 h over 2 plates (snippet). |
| [Scrub Daddy / Mommy holder](https://makerworld.com/en/models/472248) | Cloth hanger and a detachable magnetic base | Needs suction cups, heat-set inserts and magnets |
| [Sink Caddy with Drain](https://www.makerworld.com/en/models/1233077) | The closest combo organizer: brush/cutlery bin, sponge area, adjustable dividers | About 48 h over 8 plates (snippet) |
| [Sunflower flowerpot holder](https://www.makerworld.com/en/models/1822822) | Decorative | Says it does not fit the smaller Scrub Mommy |
| [Wally the Penguin](https://makerworld.com/models/2426198) | Character design that drains through the beak | Needs supports (snippet); one sponge |
| [Clyde the Highland Cow](https://makerworld.com/models/2408489) | Character design | A commenter warns the slot is too narrow (needs at least 43 mm) |
| [V2 heel-drain remix](https://makerworld.com/models/2448360) | Drains through the foot | One sponge |
| Also seen, not inspected: [1645441](https://makerworld.com/en/models/1645441), [1244797](https://makerworld.com/en/models/1244797), [1349506](https://makerworld.com/en/models/1349506), [926827](https://makerworld.com/en/models/926827), [2695451](https://makerworld.com/en/models/2695451) | Single-sponge holders, rectangular caddies with drain holes, soap + sponge caddy, adhesive wall mount | |

### Elsewhere

- Printables: [894143 Scrub Daddy, Mommy and other sponge holder](https://www.printables.com/model/894143-scrub-daddy-mommy-and-other-sponge-holder) (PETG, no supports, drains to the sink if placed close), [1407530](https://www.printables.com/model/1407530-scrub-daddy-sink-holder), [449689 tray](https://www.printables.com/model/449689-scrub-daddy-tray), [351661](https://www.printables.com/model/351661-scrub-daddy-holder) (sits on a wire rack).
- Thangs: [Smiley Sponge Dock](https://thangs.com/designer/Makers%20Mashup/3d-model/Smiley%20Sponge%20Dock-1018056). **The name is close to "SinkDock".** Check that it doesn't cause confusion before listing.

## Common complaints about sponge holders (reviews and roundups; Reddit threads did not surface)

1. **Standing water, slime and mildew** under the sponge or in the tray. This is by far the most common complaint ("tray grew slime within days").
2. **Tipping**: light or top-heavy holders, and ledge holders that fall into the sink when loaded.
3. **Fit**: jumbo sponges don't fit, slots are too narrow, and ledge widths don't match the sink.
4. **Suction cups** come off, especially on laminate.
5. Reviewers praise open grids or ribs, an **angled spout back into the sink**, and heavy bases.

## Market opportunity

Scrub Daddy holders are an established, well-rated category on MakerWorld. The best-rated
example has 107 ratings at 5.0, and there are many character remixes. **No model found holds a
Scrub Daddy, a Scrub Mommy, a flat sponge and an upright brush in one piece, drains back into
the sink, and prints quickly.** Existing combo caddies take tens of hours over several plates.
The single-sponge holders take hours for one sponge, and several need suction cups, magnets or
inserts.

SinkDock targets that gap:

| Problem in the category | SinkDock's answer | Evidence (CAD) |
|---|---|---|
| Sponge sits in a puddle and grows slime | **V-gutter floor**: each sponge rests on its two rim edges, with an open gutter 1.7 mm deep under the round sponges. Every gutter falls 2.5° to a spout. | Water-routing simulation: 100 % of floor area drains to the spouts, no puddles (`docs/SD01_drainage_map.png`) |
| Separate drip tray, or water on the counter | Four tapered **spouts** overhang the sink, each with a **drip-break groove** underneath so drops fall instead of creeping back under | Same simulation: 0 cells drain onto the counter |
| Holder only fits one sponge brand or size | Bays sized from researched dimensions plus a swelling allowance; the Daddy and Mommy bays are interchangeable | Fit check: 1.25–2.0 mm a side for the largest items, no interference |
| Tips over | Brush cup is tight front to back (28 mm) so a brush can't lean far. Base is 160 × 70 mm. | Survives a 10° incline in every direction (worst case 12.8°), empty or loaded |
| Long prints, hardware, supports | One piece, no supports, no hardware, **≈55 g, ≈1.5 h in PLA** on an A1 mini | Slice-based estimate (confirm in the slicer) |
| Hard to clean | Open front and back on every bay, no enclosed pockets (the drainage check found one at the cup corner and it was removed), slotted cup | Drainage check, drawing |
