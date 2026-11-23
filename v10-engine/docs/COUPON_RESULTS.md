# Coupon results (plate C1, PLA, H2S)

| Date | Coupon | Result | Action |
|---|---|---|---|
| 2026-11-13 | T1 M3 row | screw drops through | none, `M3_CLEAR` confirmed |
| 2026-11-13 | T1c CAP row | screw threads through the lip and is held | none, `CAPTIVE_LIP_D` confirmed |
| 2026-11-13 | T3 608 seats, all 3 steps | firm press, flush, no cracks, bearing spins freely | none, `CRUSH["bearing_608"]` nominal kept (all steps pass, so the nominal has margin both ways) |
| 2026-11-13 | T6 end-plate seat, both pockets | flush, no cracks, spins freely | none |
| 2026-11-13 | T4b in T4c | lug did not enter any slot in any orientation | **coupon design error**: the slots stopped 6 mm from the lug centre, T4b's web is 10 mm long. Slots lengthened (web + clearance + 1 mm), T4c re-exported; reprint T4c only (0.3 h). The real bank pocket opens into the bore and was never affected. |
| 2026-11-13 | T11 on T11b | lid piece sits on the base piece | pass |
| 2026-11-13 | T11d in T11c | spigot presses in and holds | pass, `CRUSH["trumpet_14"]` confirmed (also the header sockets) |
| 2026-11-13 | T10 by hand | PLA pipe does not bend by hand, no crack | pass for now (PLA is stiff); vice flex + drop test when there is a vice |
| 2026-11-14 | T4b in reprinted T4c | slides in every slot, no catching even in the tightest (0.6 mm per side) | pass. `LUG_POCKET_CLEAR` stays 0.8 (middle slot): the lug must never touch the bank in running, and the extra 0.2 covers ASA shrink and a bank that prints slightly warped |
| 2026-11-14 | T5 D-flat sockets with the printed P1 pin | 0.40 step firm and right, 0.30 (nominal) a bit wobbly, 0.20 loose | **changed**: `CRUSH["dpin_6"]` 0.30 -> 0.40. Rebuilds the crank segments, end webs and the damper D-bore. Re-check with the steel M01 pin when it exists (a turned pin is rounder than a printed one) |
| 2026-11-15 | T5b magnets, T3b 686 seats, T1 R3 3 mm rod | user: good fit on all | pass, current values confirmed |
| 2026-11-18 | Plate M1 (PLA, fast settings): printed shafts P2 / P2F in a 608 bearing | slides on by hand to the shoulder, spins freely, no wobble | pass: printed shaft vs bearing bore OK. 608 stock: 5 loose (2 for the end plates + 3 spare) |
| 2026-11-18 | T4 bushing ladder, 5 bronze bushings | hole 1 (0.15, loosest) the best; photo shows plastic shaved or cracked at the rim of holes 3-5 (0.25-0.35) | **changed**: `CRUSH["bushing_5"]` 0.25 -> 0.15. Rebuilds the rods (small end) and pistons (lug). Check: the bushing in hole 1 must not push out with a thumb; if it does, 0.20. ASA re-run before production |
| 2026-11-18 | T4 hole 1 (0.15, 4 ribs): thumb test + 3 mm 304 rod | bushing holds; a LOOSE bushing slides on the rod fine, the PRESSED one binds in spots and needs twisting | **changed**: the 4 ribs squeeze the 1 mm bronze wall square. `CRUSH["bushing_5"]` -> (8 ribs, 0.10). T4 reprinted with the new ladder (0.00-0.20). M2 / M3 held until it passes |
| 2026-11-18 | T4 reprint, 8 ribs, ladder 0.00-0.20 | hole 1 (0.00) too loose; hole 2 (0.05) firm, rod slides much better with slight drag | **changed**: `CRUSH["bushing_5"]` -> (8 ribs, 0.05). Oil + break-in for the drag; production rails must be ground h6 rod (the test rod is 304 craft rod) |
| 2026-11-18 | Plates M5 + M6 (PLA, fast settings): end plates on the crankcase, 608 into each end plate | both end plates locate on the crankcase ends; bearings press in and fit well | pass. Valley beam reprinted for the 60 mm rails (D79) |
| 2026-11-18 | T4d wrist-pin bar with the 3 mm 304 craft rod (dowel pins not arrived) | only hole 1 (0.10, loosest) takes the rod | **changed**: `CRUSH["pin_3"]` 0.20 -> 0.10. The motion test uses pieces of this rod as wrist pins; re-check with real 3 x 20 dowel pins (m6, a few microns over 3.00) when they come |
| 2026-11-18 | T4d with the real 3 x 20 dowel pins (found) | same as the rod: only hole 1 (0.10) | confirms `CRUSH["pin_3"]` = 0.10 |
| 2026-11-19 | Firmware on the real ESP32-DevKitC-32E (Windows, PlatformIO) | builds (30 s), uploads, boots; banner + `FAULT 4: driver does not answer on UART` with nothing connected (expected); `nvs_open NOT_FOUND` on first boot = no saved settings yet (harmless) | pass. Banner now prints the cylinder count (said V10) |
| 2026-11-19 | Plate M2 rods: 686 bearing into the big end | presses in flush, spins | pass |
| 2026-11-19 | Plate M2 rods + M3 piston lug: bronze bushing seat (8 ribs, 0.05) | needs a hammer in the rod small end and in the piston lug; pin through the pressed rod bushing drags | **fail**: thinner rings / finer layers grip harder than the T4 plate. T4e (rod small-end ladder 0.00 / -0.05 / -0.10) printing; rods (M2b) and pistons (M3) reprint with its result |
| 2026-11-19 | Dry fits: piston in bank bore; head A on bank deck; printed shafts in the end-plate 608s; knob on the front shaft | piston drops through with no rubbing; head sits flat, screw holes line up; shafts turn with slight resistance; knob fits | pass |
| 2026-11-19 | T4e run 1 (rod small ends, 0.00 / -0.05 / -0.10) | all three too loose | between 0.00 (loose) and 0.05 (hammer): T4e run 2 at 0.04 / 0.03 / 0.02 / 0.01 |
| 2026-11-19 | T4e run 2 (rod small ends, 0.04 / 0.03 / 0.02 / 0.01) | 0.01 too loose, **0.02 right**, 0.03 and 0.04 too tight | **changed**: `CRUSH["bushing_5"]` 0.05 -> 0.02 (8 ribs). Rods (M2b) and pistons (M3) reprint |
| 2026-11-19 | Plate M2b rods (bushing seat 0.02, H2C) | bushing too loose in the real rod although T4e ring 0.02 (same printer) was right: 0.01 mm steps are below what the printer resolves | **fixed with a drop of CA glue** on the bushing OD (bore kept clear). One rod lost to glue in the bore: reprint 1. Production plan: slip-fit seat + glue as a standard step, re-tested in ASA |
| 2026-11-19 | Plate M3 pistons (0.16 layer): 3 x 20 dowel pin through boss, rod bushing, boss | pin too tight in the bosses: pushed by hand it stops just past the middle, does not reach the far boss | **open**: T4d (0.20 layer coupon) passed at 0.10, the real 0.16-layer boss is tighter (same lesson as D83). Fix for engine #1: twist a 3 mm drill bit by hand through both bosses, then clamp the pin in centred. For the 50: loosen `CRUSH["pin_3"]` and test on a real-boss ladder like T4e. Lug bushings glued in 5 pistons OK |
| 2026-11-23 | T4f piston-boss wrist-pin ladder (0.05 / 0.00 / -0.05 / -0.10, printed like the piston) | station 3 (-0.05) best: pin goes through, rod swings | **changed**: `CRUSH["pin_3"]` 0.10 -> -0.05. Pistons (M3) reprint. Horizontal holes print slightly oval (sagging top), which is why the flat T4d bar read tighter |
| 2026-11-23 | Pololu D24V25F5 arrived: pin labels read | header order **EN, VIN, GND, GND, OUT** (5 pins, 2.54 mm) | recorded; the PCB rev A wire links still apply, a rev B can take it as a plug-in |

| 2026-11-23 | T2 heat-set insert ladder (3.90 / 3.95 / 4.00 / 4.05 / 4.10), PLA, iron 450 F | top row: 3.90-4.00 too tight to seat (insert won't stand, slow); **4.05 cleanest** (least bulge, insert solid), 4.10 easiest. Fin: 4.00 first to seat, 3.90 and 4.10 went in clean; tilt on 2-4 was technique | **changed**: `INSERT_HOLE_DIA` 4.00 -> 4.05 (row and fin, no split needed). Already-printed parts keep 4.00: carry the insert on the tip, 450 F |

Still to do: T1 S8 row, T1b/T1c PEG, 
T10, T11. ASA re-run of T3/T3b/T4/T4d/T5/T5b/T6 before production.
