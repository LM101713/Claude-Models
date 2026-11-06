# HF-04 HOLDFAST: what still needs physical testing

**Nothing in this project has been printed.** Everything that has been checked was checked in
CAD or by hand calculation (see `ENGINEERING_REPORT.md` §7 and the validation report). This
list is what a printed prototype must show before HF-04 is published. Each item names the
assumption it tests, the method, and the pass criterion. All items: **not started.**

## Assumptions that only a print can confirm

| Assumption used in the design | Value assumed | Tested by |
|---|---|---|
| Friction, PLA/PETG roller on real handles | μ ≥ 0.2 (need 0.141) | P2 |
| Friction, roller on the ramp (rolls, does not slide) | μ ≥ 0.25 | P1, P2 |
| Holes print 0–0.2 mm small, bosses 0–0.1 mm large | as the corners | P1, P9 |
| Gravity returns the rollers every time | 70 mN along the ramp vs ≈ 6 mN resistance | P1 |
| Contact marking on steel handles is cosmetic only | p₀ just above yield onset at 1–2 kg | P4 |
| Creep is taken up by the wedge | ≥ 5 mm travel left below each rated handle | P2, P6 |
| Users manage "push in and up" | the instruction alone | P3 |

## Test plan (in order)

| # | Test | Method | Pass criterion |
|---|---|---|---|
| **P1** | **Fit and free running** | Print the fit coupon + 1 Standard roller (and 1 Loose) on at least two printers (one bed-slinger, one CoreXY), PLA and PETG. Then print a full holder. Insert both rollers; roll them end to end; hold the base upright and lift each roller to the top and release, 20×. Measure pull-out play with a feeler gauge | Head enters the keyhole by hand; slides with no perceptible force; cannot be pulled out away from the keyhole; play 0.2–0.8 mm. Rollers return to the bottom stop under gravity 20/20, from any height, in under 1 s. Record which roller each printer needs |
| **P2** | **Holding: the friction question** | Holder on a rigid board. Handles: painted steel broom (Ø22–24), PP-coated steel mop, bare wood (Ø25), aluminium (Ø19–22), fibreglass / PP garden-tool handle (Ø28–32), plus one chrome or gloss handle. Rollers: Standard and Grip. Hang 0.5, 1 and 2 kg (tool plus added weight). Mark the handle with tape, then measure slip after 1 min, 1 h and 24 h | Locks on release 20/20 attempts on every handle. Slip ≤ 0.5 mm in 24 h at 2 kg on wood, painted steel and aluminium. Any handle that fails with Standard but passes with Grip is listed in the instructions. Any that fails both is excluded in writing |
| **P3** | **Ease of use** | 5 people who have not seen it, given only the instruction "push in and up, let go; lift to remove". Count first-try successes, then 10 cycles each | ≥ 4/5 succeed first time; 10/10 afterwards. Note any confusion for the listing text |
| **P4** | **Contact marking on steel** | Steel-handled tool, 2 kg, 7 days. Inspect the roller rim under a loupe; measure the mark with a caliper. Re-run P2 at the same spot | Mark ≤ 1.5 mm across. No loss of holding. No cracking |
| **P5** | **Cycle life** | 2000 hang/remove cycles (~5 years of daily use) with a 1 kg tool, on one holder. Check every 500 | No loss of holding (P2 short version passes); rollers still roll freely and return; ramp and rim show only polish; retention play < 1.2 mm |
| **P6** | **Heat and creep** | PLA and PETG holders, 1 kg, 48 h at 45 °C (oven or a car in sun), then 24 h at room temperature | PETG: no slip > 1 mm, no visible deformation. PLA: record the result; if it fails, the "PETG for garages" advice becomes "PETG only" |
| **P7** | **Abuse** | (a) Yank the handle straight out without lifting, 20×. (b) Knock the hanging tool sideways, 20×. (c) Drop the base with rollers fitted from 1 m, 5× on different faces. (d) Load in steps on a rigid mount until something gives: record slip load and fracture load and where it breaks | (a)–(c): rollers stay in; no cracks. (d): it slips before anything breaks, and the slip load is ≥ 2× the 2 kg rating |
| **P8** | **Wall mounting** | Mount on plasterboard with standard plugs and on timber; 2 kg tool; 50 hang/remove cycles plus the P7a yank | No movement of the plate; screws do not pull through the 7 mm plate; countersinks do not crack when screws are snugged |
| **P9** | **Dimensions as printed** | Calipers / pin gauges on the parts from P1: roller Ø, neck Ø, head Ø, slot width, undercut width, keyhole Ø, back-plate thickness, ramp angle (protractor or photo) | Within the validation corners (holes −0.4…+0.2, bosses −0.1…+0.2, Z ±0.15). Ramp 16° ± 0.5° |
| **P10** | **Edge cases** | Ø19 and Ø32 handles; one oval handle; one tapered handle; a 33–35 mm handle (beyond rating); unit mounted 2° off plumb | Rated sizes hold. Out-of-rating results are noted in the listing |
| **P11** | **Feel and sound** | Subjective: insertion, the drop-and-lock, release, rollers clacking home. Seam position on the ramp and rim | Positive notes from P3 testers; no seam tick that bothers anyone (otherwise move the seam or add scarf seam advice) |

## Publication gate

Publish on MakerWorld only when **P1, P2, P3, P7 and P9 pass** on at least two printers. P4–P6
and P8 can follow with the first update, as long as the listing states the 2 kg rating and
PETG for warm locations.

Record results in a `TEST_LOG.md` next to this file: date, printer, material, roller variant,
measured values, photos, and pass/fail for each item.
