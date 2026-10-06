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
| D9 | **Sound: "[yes/no, check with Scott]"** | Left sound OUT of the design. Reserved space in the rear base half for a 28 mm speaker + small audio module (noted in `ELECTRONICS.md`); nothing cut into any part. | Adding a speaker grille would be an exterior change; the interior has room, so it can be added later without reprinting anything but the rear base half. Safest reversible option. |
| D10 | **Colours: all "[x]"** | 4-slot palette: slot 1 = block + crankcase + end plates + beam (light grey in renders), slot 2 = heads, cam covers, side panels, end covers, base (black), slot 3 = coil packs (red), slot 4 = exhausts + trumpets (metallic grey/gold). Filament totals are reported per slot. | Keeps to <= 4 filaments as you asked; matches the renders you have seen. Rename the slots in `config.py PALETTE` when you choose colours; nothing else changes. |

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

| D19 | **Con-rod big-end wall 2.5 -> 3.0 mm** (`ROD_BIG_END_WALL` in config.py; rod eye 19 -> 20 mm). | DFM risk A2: a steel bearing pressed into 2.5 mm of plastic may split the eye. The rod is inside the crankcase (visible only through the windows, 1 mm bigger eye is not noticeable). The full-rotation clearance scan re-ran with it - see MORNING_SUMMARY for the smallest gaps. Reversible: one number. |
| D20 | Piston label on the crown underside (inside the skirt), coil-pack label on the free end of its shaft. | The skirt bottom ring (2 mm) and the elliptical coil body have no flat patch big enough; both chosen spots are hidden once assembled and are not fit surfaces. |
| D21 | Coupons print with the slicer's hole compensation OFF. | The design compensates holes itself (`HOLE_COMP`); a slicer offset on top would corrupt the ladders. Stated in COUPON_PRINT_GUIDE.md. |
| D22 | Prototype BOM covers 2 engines + 25 % spares, alternative insert/screw/belt sizes, measuring tools; no steel parts (printed PETG stand-ins first), nothing x50. | Your rules 6b and 7. |
| D23 | Verification still uses the un-engraved part shapes. | Engraving only removes 0.5 mm of material on hidden faces, so it cannot create an interference; keeping the check models label-free keeps the 95-minute check unchanged. |

## Exterior changes

None so far. (Any exterior change gets: a commit before it, a before/after
description here, and the reason.)
