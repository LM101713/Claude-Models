# Decisions log (DFM pass, overnight run)

Every decision taken without you, with reasoning, so each can be approved or
reverted in the morning. Exterior changes are in their own section with
before/after and the commit made just before them.

## Decisions from your answers (applied)

| # | Decision | Applied as |
|---|---|---|
| D1 | Keep 30 firing LEDs, keep the 4-item rear panel (12 V jack, power rocker, speed knob, START) | unchanged |
| D2 | Silent 3:1 belt, adjustable motor mount, spare belt in the BOM | belt + slotted motor mount unchanged; spare belt added to the prototype BOM |
| D3 | PLA for tests, ASA for production; critical coupons re-run in ASA | `docs/COUPON_PRINT_GUIDE.md`; coupons default to PLA in `tools/printcheck.py` |
| D4 | One colour per part, lettering/plaque as a separate part, no AMS purging on big parts | no multi-colour objects anywhere; edition plate is a purchased engraved part |
| D5 | Printed PETG crankpins/shafts first; no steel order until coupons confirm | P1/P2 stand-ins stay in the motion-test plates |
| D6 | Electronics access from underneath; base panels removable with captive screws | bottom-panel screw holes got a captive lip (`CAPTIVE_LIP_D`, `CAPTIVE_LIP_T` in fits.py, coupon T1 row CAP) |
| D7 | Hand-built board for engines 1-2, custom PCB later | board envelope in the base unchanged; PCB design deferred |
| D8 | Keep the numbered edition plate as a swappable part | unchanged (adhesive plate in a recess; swapping = peel and replace) |

## Decisions I had to make (your answers had placeholders)

| # | Open item | What I did | Why |
|---|---|---|---|
| D9 | Sound: "[yes/no, check with Scott]" | **Final answer: NO** (your decision, day 2). Sound removed from the open questions; no speaker, amplifier or audio module is designed for; the earlier "reserved space" note was deleted from ELECTRONICS.md. | Your decision. |
| D10 | Colours: all "[x]" | 4-slot palette (`config.py PALETTE`): slot 1 = block, crankcase, end plates, beam; slot 2 = heads, cam covers, side panels, end covers, base; slot 3 = coil packs; slot 4 = exhausts + trumpets. Filament is reported per slot. **Approved by you (day 2)** - slots stay until the colours are chosen. | <= 4 filaments; rename the slots, nothing else changes. |

## Design decisions during Phase 1

| # | Decision | Reasoning |
|---|---|---|
| D11 | All tolerances moved to one file, **`fits.py`**, imported by `config.py`; a lint (`tools/check_fits.py`) fails the build if a new clearance literal appears in `cad/`. | Your Phase 1 rule 1. The move changed no geometry: every STL's volume and size was compared before/after (30 parts, 0 changed). |
| D12 | Part numbers are **engraved (recessed) 0.5 mm**, not raised. | Raised text on a mating face would hold the part 0.5 mm off its neighbour. The face is a hidden/mating face chosen per part; the exact spot is found by a probe so it never lands on a hole or boss. |
| D13 | Crank segments keep their type number and gain the part number: "06-54", "07-198". | One label answers both "which part" and "which way round". |
| D14 | Coupons were split into 13 small prints (T1-T8 with b/c variants) instead of 6 larger ones. | Your 30-minute limit: the first version of T1/T3/T4/T5 sliced at 0.8-1.1 h. Smaller plates also print on the A1 Mini. |
| D15 | T3 (608) and T5 (D-pin) ladders have 3 steps (-0.10 / 0 / +0.10), the others 5. | Those two coupons must be thick (7 mm bearing, 11 mm pin socket) to be realistic; 5 steps would take over 30 min. Crush ribs tolerate +/-0.05 anyway. |
| D16 | Coupons print with 10 % infill and 3/2 top/bottom layers (T1/T2: 2 walls; crush coupons: 3 walls like the real parts). | Fits live in the walls, not the infill; this is what keeps each coupon under 30 min. Engine parts keep 4 walls / 25 %. |
| D17 | No gear-mesh coupon. | There are no gears: the drive is a GT2 belt with purchased pulleys. |
| D18 | Printer bed for all plate work = **H2C single-nozzle mode, 325 x 320 mm** (`config.PRINTER`). | The exhausts (293.5 mm) do not fit the 300 mm dual-nozzle bed. Only the coupon plate and motion-test plates are exported (rule 7: no final plates). |

| D19 | **Con-rod big-end wall 2.5 -> 3.0 mm** (`ROD_BIG_END_WALL`). **PROVISIONAL - not approved yet.** Plain-words explanation, risk and how to switch back: `docs/D19_EXPLAINED.md`. No further change depends on it. | DFM risk A2 (bearing pressed into 2.5 mm of plastic may split the eye). One number to revert. |
| D20 | Piston label on the crown underside (inside the skirt), coil-pack label on the free end of its shaft. | The skirt bottom ring (2 mm) and the elliptical coil body have no flat patch big enough; both chosen spots are hidden once assembled and are not fit surfaces. |
| D21 | Coupons print with the slicer's hole compensation OFF. | The design compensates holes itself (`HOLE_COMP`); a slicer offset on top would corrupt the ladders. Stated in COUPON_PRINT_GUIDE.md. |
| D22 | Prototype BOM covers 2 engines + 25 % spares, alternative insert/screw/belt sizes, measuring tools; no steel parts (printed PETG stand-ins first), nothing x50. | Your rules 6b and 7. |
| D23 | Verification still uses the un-engraved part shapes. | Engraving only removes 0.5 mm of material on hidden faces, so it cannot create an interference; keeping the check models label-free keeps the 95-minute check unchanged. |

| D24 | **No part number on any bed face** (rule enforced in `cad/partnum.py`). Moved: 02 valley beam -> bank B land (top face as printed); 10 head -> top of an end cam cap (under the cam cover); 12 side panel -> its upper edge face (under the exhaust header); 14/15 exhausts -> the floor of the tail-pipe outlet recess (4 mm inside the pipe mouth); 17 throttle frame -> outer side face of a rail (faces the cam cover, down in the valley); 01 crankcase -> an end face (under the end plate). Others were already off the bed. | Recessed text in the first layer makes small islands and the slicer flagged "low bed adhesion" (exhaust B, crankcase). Your task 1. The side panel and throttle frame spots are low-visibility rather than fully hidden: the only fully hidden faces of those two parts are their bed faces. |

| D25 | Look-and-feel review done from 9 render angles (`docs/LOOK_AND_FEEL_REVIEW.md`). **No exterior change applied**; the 13 ranked items (block/bank detailing, base plinth/reveal, end-cover faces, coil colour, cam-cover lines, trumpet height, exhaust finish, window chamfers, ballast plate ...) are listed for your decision. | Your task 3 rule: list only. |

## V8 redesign (stock-car V8 replaces the F1 V10 - your decision)

| # | Decision | Why / source |
|---|---|---|
| D26 | **Engine variant switch.** `config.py` and `cad/assembly.py` select `v8` (default, `ENGINE` file) or `v10`; every tool is unchanged and still runs on the frozen V10 (`ENGINE=v10`). The V10 stays at commit `7c6cc96`. | Your STEP 0 (keep the V10 recoverable) without duplicating the tooling. |
| D27 | **Crank:** cross-plane, throws 0/90/270/180 deg, odd cylinders on the +Y bank, straight crankpins with two 686 bearings each (the V10 split pin with its flying web is not needed on a V8), bank B 6.5 mm ahead of bank A (rods side by side on one pin). | Same purchased parts as the V10 (686ZZ, 3x20 pins, 608ZZ mains); the 6 deg sweep is clear. |
| D28 | **Firing order is one line** (`FIRING_ORDER` in `config_v8.py`, default 1-8-7-3-6-5-4-2 = the 4/7 swap you chose). `self_check` proves each cylinder fires at one of its own TDCs, and the firmware will be generated from the same list (`tools/gen_firmware_config.py`, next phase). | Your decision 3; one source for CAD and firmware. |
| D29 | **Windows AND lit plug boots** (your option c). `WINDOWS = True/False` switches the block windows. Strength check (numbers, not a guess): windows 34 mm wide on a 50 mm pitch leave 16 mm ligaments between them and 13 mm at the block ends, the wall they pierce is 11.2 mm thick, and 2.5 mm of deck lip stays above each window; the head-screw inserts sit 6 mm from the nearest window edge. The bank stays one solid and its print orientation (deck down) is unchanged. | Your decision 1. These are the same window sizes as the verified V10 bank. |
| D30 | **Header primaries drop BETWEEN the windows**: each pipe leaves its port straight (16 mm), bends 47 deg and drops half a cylinder pitch rearward (17 deg from vertical) into a log collector. One printable shape for all 8 (bank B is its mirror), standing on the collector spigot, nothing steeper than 45 deg. | Keeps every window visible between the pipes (option c) and reads as swept-back primaries. A real 4-into-1 merge would need supports or a CAD artist (`docs/V8_PLAN.md` 1c). |
| D31 | **Plug boots ahead of and below each port** (+15 mm, 8 mm above the deck), pressed through the flange plate into a 9 mm crush socket over a hidden LED strip (11 LEDs, every third one under a boot). Boots in the translucent slot of the palette. | Rearward of the port they would sit under the swept pipe; the 4.3 mm wall between the boot hole and the pipe hole in the flange plate is the limiting dimension. |
| D32 | **One flange plate per bank** (4 mm, 198 x 32 mm) screwed to the head with two M3x8 into horizontal heat-set inserts; the plate hides the LED strip groove and locates the 4 pipes and 4 boots. | Separate flat part = no supports; the pipes stay identical. |
| D33 | **Collector** is a straight 36 mm log along the engine with a 60 mm open tail to the rear, flat on its inboard side (85 % round) so it prints lying down; pipe tubes sit in 3 mm saddle counterbores so there is no crescent gap at the round surface. | Honest simplification you accepted in the plan. |
| D34 | **Intake is provisional**: a tall single-plane plenum (186 x 126 x 68 mm) filling the valley, 8 runner humps climbing its sides and curling over the top, throttle body on the front, two fuel rails with angled injector bosses printed with it. It is shown with bank A for proportion feedback only. Printing it (orientation / two-piece split) is open. | Your mockup feedback: "intake too small and tubular" - this one spans the valley like STYLE_ai_04/05. |
| D35 | Head is 36 mm tall (real ~3.6 in at 1:2.42), valve cover 29 mm + 7 mm oil cap, magnetic like the V10 cam cover (same 4 magnets), head screws under the cover into deck inserts. | Proportions table in `docs/V8_PLAN.md` 1b. |

## Exterior changes

V8: the whole exterior is new by your request (the F1 exterior is frozen with
the V10 at commit `7c6cc96`). Bank A exterior built first for approval - see
`docs/V8_BANK_A_REVIEW.md`.
