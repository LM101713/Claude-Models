# Per-unit QC record

Print one copy per engine (or copy into a spreadsheet). Every box ticked, every
value written, signed - or the unit does not ship.

```
Serial no. ______    Build date ______    Builder ______    Firmware ______
```

## 1. Parts in (from the kit)

| Check | OK |
|---|---|
| All printed parts present, ASA, colour batch noted: ______ | [ ] |
| Flatness: crankcase, banks, heads, base halves rock-free on glass | [ ] |
| No visible print defects on show faces (heads, banks, exhausts, covers, base top) | [ ] |
| Machined parts M01 x5, M02 x2, M03 x10, M04 x1, M06 x10 present, deburred | [ ] |
| M01 journals measure 5.988-5.996 mm (sample 1 per batch) | [ ] |
| M06 rings 0.75 +/-0.02 thick, OD <= 7.5, burr-free (sample 1 per batch) | [ ] |

## 2. Sub-assemblies (from ASSEMBLY.md)

| Stage | Check | OK |
|---|---|---|
| A2 | 78 inserts flush/just below, square | [ ] |
| A3 | 46 magnets in, polarity right (every cover snaps on) | [ ] |
| A4 | 12 bearings + 30 bushings in, all turn/slide freely | [ ] |
| A5 | 10 wrist pins centred (12.0 +/- 0.3 mm both sides) | [ ] |
| B | crank: types 54-198-198-54, 16 screws striped, turns true and free | [ ] |
| C | crank in case, beam + end plates on, turns free, hall leads free | [ ] |
| D | banks, rails, heads on; 2 hand turns: smooth, silent, no piston touches a bore | [ ] |
| E | exhausts, coil packs, covers, frame, trumpets fitted, all magnets hold | [ ] |
| F | belt centred, tension 3 mm / 2 N, end float gone | [ ] |
| G | all 7 connectors latched, harnesses tied, motor coil check 1.2-1.8 ohm | [ ] |

## 3. Electrical and functional

| Check | Value | OK |
|---|---|---|
| Supply current, Ready mode (adapter meter) | ______ A (< 0.25) | [ ] |
| Supply current, 120 RPM | ______ A (< 0.6) | [ ] |
| Homing parks with piston 1 (front left) at TDC | | [ ] |
| Rotation clockwise seen from the front | | [ ] |
| LED test: 30 LEDs, cylinder order 1-6-5-10-2-7-3-8-4-9 | | [ ] |
| Knob: bottom = idle (20 RPM), top = 120 RPM, smooth in between | | [ ] |
| START: soft start, soft stop; long press = sleep; START wakes it | | [ ] |
| Fault test: pull W3 (hall) while running at 60 RPM -> fault 3 within 2 s; plug back, START clears | | [ ] |
| Noise at 120 RPM, 30 cm | ______ dBA (target < 40) | [ ] |

## 4. Burn-in (BURN_IN.md)

| Check | Value | OK |
|---|---|---|
| Burn-in log file | ________________ | |
| Result PASSED, no FAULT lines | | [ ] |
| Worst sync error | ______ deg (< 3.0) | [ ] |
| Motor case temperature after 120 RPM segment | ______ C (< 50) | [ ] |
| Torque stripes intact, no wear dust, belt OK | | [ ] |
| Run hours / lifetime faults (`status`) | ______ h / ______ | |

## 5. Final

| Check | OK |
|---|---|
| Show faces cleaned (microfibre, no solvent), no fingerprints | [ ] |
| Side panels, cam covers, end covers seated and aligned | [ ] |
| Auto-sleep left at 15 min (`status`) | [ ] |
| Adapter + correct mains cord for the customer's country, manual, packed in foam | [ ] |
| Serial number inside the rear base half matches this sheet | [ ] |
| Edition plate (H14) number = serial number, centred, no bubbles or scratches | [ ] |

```
QC passed by ______________________   Date ________   Signature ______________
```
