# Assembly instructions

One engine, in build order. Stage A (part preparation) is batch work done ahead
of time; stages B to H are the final assembly of one engine, **about 1 h 50 min**
for a trained builder with prepared parts. Every stage ends with a checkbox
list - do not start the next stage until every box is ticked. Copy the
checkboxes into the unit's QC record (`docs/QC_CHECKLIST.md`).

Part numbers: printed `01`-`21`, machined `M01`-`M06`, purchased `H#` / `E#`
(see `docs/BOM.md`). Every screw in the engine is the same **M3 x 8** socket
head (H6) - there is no other screw size to mix up.

## Tools

| Tool | Used for |
|---|---|
| Soldering iron with an M3 heat-set insert tip, set to 245 C | inserts (ASA) |
| Bench vise with smooth aluminium soft jaws, or a small arbor press | bearings, bushings, pins, magnets |
| 2.5 mm hex driver, **adjustable torque driver 0.1-0.6 N m** (e.g. Wiha TorqueVario-S) | all M3 screws |
| 1.5 mm hex key | pulley grub screws |
| 2.5 mm pin punch | wrist pins |
| Digital caliper (with depth rod) | checks |
| Multimeter | electrical checks |
| JST XH crimp tool, wire stripper, flush cutter, heat gun | harnesses |
| USB cable for the ESP32 board + a PC with Arduino IDE or PlatformIO | firmware |
| Marker for magnet polarity, a "reference" magnet stuck to a tile | magnets |
| Lint-free cloth, isopropyl alcohol | cleaning |

## Torques and threadlocker

* Pre-coat the screws: brush **Vibra-TITE VC-3** (plastic-safe, removable) on the
  threads of a tray of M3 x 8 screws and let it dry 30 min. Use pre-coated
  screws everywhere. Do **not** use anaerobic threadlockers (Loctite 2xx): they
  crack ASA.
* Torques: screws into brass inserts **0.4 N m**; crankpin screws (into the
  steel pins) **0.15 N m** (the D-flat carries the torque, the screw only holds
  the pin in); motor screws **0.5 N m**; pulley grub screws **0.4 N m**.
* After torquing, put a dot of paint pen across each screw head and the part
  (torque stripe). QC checks the stripes are unbroken after burn-in.

---

## Stage A - part preparation (batch, ~45 min per engine)

### A1 Inspect printed parts
- [ ] Every part from `docs/PRINT_REPORT.md` is present, ASA, correct colour.
- [ ] No warping: the crankcase, banks, heads and base halves sit flat on a
      glass plate (no rocking, gap under a 0.1 mm feeler at most).
- [ ] Holes and crush ribs are clean: no stringing, no elephant foot in bores
      (trim with a deburring tool if needed, never drill a crush-rib hole).
- [ ] Brims removed from the coil packs.

### A2 Heat-set inserts (78 per engine)
Iron at 245 C, insert straight, push gently until it is **0.2 mm below flush**,
hold a flat steel block on it for 3 s while it cools.

| Part | Inserts |
|---|---|
| 01 crankcase | 16 (bank ends, end plates, base) |
| 02 valley beam | 12 |
| 03 cylinder bank | 8 each, deck face |
| 05 crank end web | 3 each, flange face |
| 10 cylinder head | 5 each, outboard face (exhaust) |
| 19 / 20 base halves | 6 joint (front half), 4 + 4 panel pillars, 4 board standoffs (rear half) |

- [ ] All 78 inserts flush or just below, square, no plastic pushed up around them.

### A3 Magnets (46 per engine)
Magnets attract only one way round, so polarity matters:
**fixed parts (heads, banks, end plates): north pole OUT. Covers: south pole OUT.**
Check each magnet against the reference magnet before pressing it in. Press
with the vise until flush (crush ribs hold them; no glue).

| Part | Magnets |
|---|---|
| 10 head (cam cover seats) | 4 each |
| 11 cam cover | 4 each |
| 03 bank (side panel seats) | 4 each |
| 12 side panel | 4 each |
| 04 end plate (end cover seats) | 3 each |
| 18 end cover | 3 each |
| 05 crank end web (hall magnet, rim pocket) | 1 each - polarity does not matter |

- [ ] Every cover snaps onto its seat and holds; none repel.

### A4 Bearings and bushings
- [ ] **Con-rods (08) x10:** press a 686ZZ (H2) into the big end, flush both
      sides. Press a bronze bushing (H3) into the small end, centred (0.5 mm in
      from each face) - use a 3 mm pin through the bushing as a guide.
- [ ] **Pistons (09) x10:** press a bronze bushing into each end of the lug
      until flush. A 3 mm rail must slide through both bushings by hand,
      freely, without play you can feel.
- [ ] **End plates (04) x2:** press a 608ZZ (H1) in from the **inside** face until
      it stops on the lip; the outer ring must sit square (check with a caliper
      depth rod at 3 points: equal within 0.05 mm).
- [ ] Every bearing turns smoothly after pressing (no notchiness).

### A5 Rods onto pistons (x10)
- [ ] Put the rod small end between the piston bosses, push a 3 x 20 wrist pin
      (H4) through with the pin punch until it is **centred: 12.0 +/- 0.3 mm deep
      on both sides** (caliper depth rod from the piston skirt surface).
- [ ] The rod swings freely on the pin and can slide 1 mm to each side.

### A6 Controller board and harnesses
Build per `docs/ELECTRONICS.md` section 4 and test it (step 6 there) before it
goes into an engine.
- [ ] Board passes the bench power-up test.
- [ ] Harnesses W1-W7 made and continuity-tested.
- [ ] Firmware flashed (12 V off, USB only); serial console shows the banner.

---

## Stage B - crankshaft (~25 min)

The crank is built front to rear:
`[front shaft]-[end web]-(pin 1)-[seg 54]-(pin 2)-[seg 198]-(pin 3)-[seg 198]-(pin 4)-[seg 54]-(pin 5)-[end web]-[rear shaft]`.
The number engraved on each segment is its type. Every joint fits one way only
(D-flats); if something does not go, it is the wrong part or turned round.

**B1 Load each crankpin (M01) x5.** On each end in turn: slide a con-rod's 686
bearing over the end onto the journal until it stops on the pin's shoulder,
then an **M06 spacer ring**. Which rod goes where:

| Pin | Journal A (front end) | Journal B (rear end) |
|---|---|---|
| 1 | rod of cylinder 1 | rod of cylinder 6 |
| 2 | cylinder 2 | cylinder 7 |
| 3 | cylinder 3 | cylinder 8 |
| 4 | cylinder 4 | cylinder 9 |
| 5 | cylinder 5 | cylinder 10 |

Mark each rod/piston with its cylinder number (paint pen on the piston's inner
skirt). The rods' fluted face points to the front on journal A and to the rear
on journal B.

**B2 Segment sub-assemblies.** For each segment, press the *rear* pin (pin 2 into
the first "54", pin 3 into the first "198", pin 4 into the second "198", pin 5
into the second "54") into the segment's **rear** socket: end A of the pin, D-flat
on the flat of the hole, vise with soft jaws, until the M06 ring is tight
against the web. Screw it from the front face (channel), 0.15 N m.

**B3 Chain them.** Press pin 1's end A into the front end web (05), screw from the
flange face. Then press the first segment sub-assembly onto pin 1's end B and
screw from that segment's rear face; repeat down the crank; finally press the
rear end web onto pin 5's end B and screw from its flange face.

**B4 Main shafts (M02) x2.** Spigot into the end web, 3 screws through the
flange (the uneven pattern fits one way). The crankpin screw sits in the
flange's access hole.

- [ ] All 10 crankpin screws and 6 flange screws torqued and striped.
- [ ] Segment types in the right order: 54 - 198 - 198 - 54 (engraved numbers).
- [ ] Every rod turns freely on its pin and has visible side clearance to the webs (0.75 mm).
- [ ] Hall magnet present in both end webs.
- [ ] Crank on V-blocks (or two 608s): main shafts run true; it turns by hand
      with no tight spot over a full turn.

## Stage C - crank into the crankcase (~20 min)

This order is checked in CAD (`tools/verify_all.py`, "assembly paths"): each
part can travel to its place without touching anything already there.

**C1 Hall sensor.** On the **rear base half (20)** top, lay the DRV5033 branded
face **up** over the lead slot, legs bent down 2 mm from the body through the
slot; solder W3 to the legs underneath (heat-shrink each joint). The crankcase
pocket covers and traps it in C5.

**C2 Crank module in.** Lower the crank with its rods and pistons (no end
plates yet) into the open top of the crankcase (01). The crank rests in the
cavity; the pistons hang out through the two long slots.

**C3 Valley beam.** Slide the valley beam (02) in from the **front end** of the
crankcase, between the two rows of rods, until it is flush with both ends.
(Lowering it from above is not possible: the piston lugs are in the way.)

**C4 End plates.** Slide an end plate (04, bearing already pressed in, lip
outside) over each main shaft until its spigot sits in the case end. Screw each
plate: 4 screws into the crankcase, 2 into the beam. Fit the M04 spacer on the
front shaft.

**C5 Onto the base.** Join the base halves (19 + 20): 2 pegs, 6 screws (inside).
Put the crankcase on the base - the hall sensor slides into the pocket under the
case floor - and screw it down from below (4 screws through the base bosses).

- [ ] The crank turns freely by hand, no tight spot; slight end float (~0.6 mm)
      at this stage is correct (it is removed in stage F).
- [ ] Hall leads not pinched (look through the base opening).

## Stage D - cylinder banks, rails, heads, LEDs (~25 min)

**D1 Banks (03) x2.** Turn the crank so the pistons of one bank are at
mid-stroke. Hold the five pistons roughly upright and lower the bank straight
down its bore axis: the lead-in chamfers find the pistons and lugs. The locator
pegs drop into the crankcase / beam. 6 screws per bank from the deck (2 into the
crankcase, 4 into the beam). Repeat for the other bank.

**D2 Rails (M03) x10.** Drop each rail into its lug pocket from the deck, through
both bronze bushings of the piston, into the hole in the valley beam (turn the
crank a few degrees if it does not find the bushing). Put one drop of light oil
(H13) on each rail. Each rail stands 3 mm proud of the deck.

- [ ] Turn the crank 2 full turns by hand: all 10 pistons run smooth and quiet,
      no piston touches its bore (look through the windows), no ticking.

**D3 LED strips (E12).** Cut two 15-LED pieces on the cut marks. Solder the lead
(W4/W5, 24 AWG silicone: red +5 V, black GND, green DIN) to the **DIN end** (the arrows point away
from it). Heat-shrink. Peel the backing and press each strip into the groove in a
head's **underside**, LEDs facing out of the groove, lead end at the end that will
be at the **rear** of the engine (bank A head: the end nearest cylinder 5; bank B
head: nearest cylinder 10). Lay the lead in the short side groove to the valley
side.

**D4 Heads (10) x2.** Lower each head onto its bank: the 5 rail tops enter the
pockets (it fits one way only - the rails are off-centre). 8 screws per head
through the cam caps.

- [ ] LED leads leave each head at the rear, valley side, not pinched.
- [ ] Crank still turns freely; pistons clear the heads at TDC (look in the windows).

## Stage E - styling parts (~15 min)

- [ ] **Exhausts (14 bank A, 15 bank B):** 5 screws each into the head inserts.
- [ ] **Coil packs (16) x10:** press into the head-top sockets.
- [ ] **Cam covers (11):** drop over the coil packs onto the heads (magnets).
- [ ] **Throttle frame (17)** on the two heads' valley faces; **trumpets (13 or
      M05) x10** through each throttle body into the head ports (firm push - crush
      ribs). They hold the frame down.
- [ ] **Side panels (12)** on the bank sides (magnets) - or leave them off to
      show the moving pistons; both look finished.

## Stage F - drive (~15 min)

**F1** Motor (E11) behind the bulkhead in the front base half, 4 screws (0.5 N m),
slots allow up/down. 20T pulley (H9) on the motor shaft, grub screw on the
shaft's flat, pulley face 1 mm from the bulkhead.

**F2** Belt (H10) over the 20T pulley, up through the slot in the base top.

**F3** 60T pulley (H8) onto the front main shaft over the belt: push the pulley
against the M04 spacer while **pulling the crank forward by its shaft** (this
takes out the end float - the front bearing is the locating bearing), tighten
both grub screws on the shaft's flat.

**F4** Tension: loosen the motor screws, push the motor **down** until the belt's
long strand deflects **3 mm under 2 N** (a 200 g weight / light finger press) at
mid-span, tighten.

- [ ] Belt runs centred on both pulleys over a full turn, does not touch the slot edges.
- [ ] Crank end float gone (< 0.1 mm by hand).

## Stage G - electronics (~15 min)

**G1** Rear panel: DC jack (E7), rocker (E8), speed pot (E10, tab in its hole),
START button (E9). Knob on the pot.

**G2** Controller board on its 4 standoffs (rear half, under the top skin,
components down, connector edge to the rear panel).

**G3** LED leads: down the rear of the V, into the rear end cover notch
position, through the harness hole into the base (6 mm braided sleeve from the V
to the base). Plug W4 -> J4 (bank A), W5 -> J5 (bank B).

**G4** Plug W1 (power), W2 (motor - coil check first, ELECTRONICS section 5), W3
(hall), W6 (knob), W7 (START). Tie every harness to the anchors within 30 mm of
the board.

- [ ] Every connector latched; no wire touches the motor or the belt.
- [ ] W2 coil resistances measured: 1-2 and 3-4 = 1.2-1.8 ohm, 1-3 open.

## Stage H - first power-up and close (~10 min)

Follow `docs/ELECTRONICS.md` section 8 (homing, service-mode LED test, TDC
check, rotation direction, speed range).

- [ ] Homing OK, parks with piston 1 (front left) at the top.
- [ ] LED test: all 30 LEDs, firing order correct.
- [ ] Clockwise rotation (seen from the front).
- [ ] 20-120 RPM smooth and quiet; START/stop soft.

Close: end covers (18) front and rear (magnets), bottom panels (21, 4 screws
each), rubber feet (H11) in the 8 rings. Write the serial number inside the rear
base half and on the QC record. Then the unit goes to burn-in (`docs/BURN_IN.md`).
