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

Still to do: T2 inserts (soldering iron), T1 R3 / S8 rows (rods), T1b/T1c PEG, T3b (686), T4 (bushings),
T4d (pins), T5b (magnets), T10, T11. ASA re-run of T3/T3b/T4/T4d/T5/T5b/T6 before production.
