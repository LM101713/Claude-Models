# TP-01 TUBEPRESS: what still needs a physical test

**Status: the design is checked in CAD only.** Nothing has been printed. TubePress has more
unknowns than SinkDock because it is a mechanism that loads a real tube. The three "Gate" items
must pass before the model is published.

## Print

| # | Test | Pass |
|---|---|---|
| P1 | Slice `TP01_set_A1mini_plate.3mf` (A1 mini, 0.20 mm Standard, PLA and PETG) | ≤ 35 g and ≤ 90 min for the set. The estimate is about 17 g and 54–64 min. |
| P2 | **Gate:** the key prints 84.5 mm tall on its knob. On a bed-slinger (A1 mini), check that the two tines print straight and that their tips line up | Tines straight to ±0.3 mm. If they wobble, slow the outer wall for the top 30 mm, or print the key on its own. |
| P3 | Leaf pawl prints free of the plate | The 0.8 mm cut round the leaf is clear. The leaf flexes down by hand and springs back. |
| P4 | Bearings: teardrop bores with 0.35 mm radial clearance | The key turns freely by hand in both bores with no tube loaded |

## Mechanism

| # | Test | Pass |
|---|---|---|
| M1 | Ratchet feel with no tube | Clicks every 15° counter-clockwise (looking at the knob), locks clockwise. Count 24 clicks per turn. |
| M2 | **Gate:** springback hold. Wind a full tube to half-used, let go, wait 24 h | The knob hasn't moved back. The CAD estimate puts springback at up to 0.12 N·m against a conservative pawl hold of 0.20 N·m (PETG); both are estimates. |
| M3 | Leaf fatigue: 500 turns (12,000 clicks) | No crack and no lost click. Design strain at the leaf root is 0.54 %. |
| M4 | Reverse abuse: twist the knob backwards hard | Either it holds, or the leaf buckles and slips without breaking. Record which. |

## Tubes (bring at least four)

Use a travel tube, a standard Colgate or Crest, a Sensodyne, and a family-size or all-HDPE tube.
Measure each tube's flat width and crimp thickness.

| # | Test | Pass |
|---|---|---|
| T1 | Loading: tube end up through the slot, push the key in with the mark vertical | Loads in under 15 s without tools, for every tube |
| T2 | **Gate:** winding force through the Standard (1.5 mm) slot | Winds with a comfortable finger-and-thumb twist, and empties the tube to the shoulder. If it's too stiff, try the Loose frame (2.0). If paste is left in the flat part, try the Tight frame (1.2). Record which variant suits which tube. |
| T3 | Tube damage | No tears at the crimp or at the slot's edges after emptying a tube |
| T4 | Removal: pull the key straight out | The roll slides off the fork and the frame slides off the tube |
| T5 | Widest and narrowest tubes | A 65 mm family tube fits the 68 mm slot. A 32 mm travel tube winds straight (it may sit off-centre in the slot). |

## Notes for the listing

- The winding direction is counter-clockwise looking at the knob; there's an arrow on the knob face.
- Line up the slot mark on the knob face with the tube before pushing the key in.
- Print in PETG or PLA; PETG leaves the leaf more fatigue margin (strain limit 1.2 % vs 0.8 %).
