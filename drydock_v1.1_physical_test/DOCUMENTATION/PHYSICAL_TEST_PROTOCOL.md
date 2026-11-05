# DRYDOCK V1.1: physical test protocol

This protocol covers the first physical tests of V1.1. Run the tests in order: each one
assumes the previous ones passed. Record every number, even the boring ones.

**Equipment:**

- digital calipers (0.01 mm); an inside-jaw caliper or a bore gauge is better
- a small luggage scale or a push-pull force gauge (0–50 N)
- a phone camera, ideally with macro
- a flashlight
- white paper or a white tray
- a marker
- 2–5 mm indicating silica gel beads, about 60 g
- 1–3 Bambu reusable spools, plus any third-party spools you want to support

**Prints:**

- the fit-test plate (`DD011_plate4_fit_test.3mf`) for tests B–F at gauge level
- later, a full cartridge (plates 1–3) for B, E and F at product level

**Reference values from CAD** (design intent, not measurements):

| Feature | Design value |
|---|---|
| Body / cap outer diameter | 46.0 mm |
| Plug-to-bore radial clearance | 0.30 mm |
| Locked cap axial play | ≤ 0.40 mm |
| Detent torque (estimated) | 0.22–0.31 N·m |
| Detent | the last ~20° before lock, then a click |
| Hard stop | just past 90° |
| 55 mm adapter covers bores | 54.1–55.8 mm |
| Adapter insertion force (estimated) | ≈ 6 N, ≤ 11 N |
| Adapter axial hold (estimated) | ≈ 2.7 N |
| Vent slots | 1.2 mm wide |
| Body-to-bore gap at Ø55 | 4.5 mm |

Before each test, inspect the parts: no stringing in the vent slots, no elephant-foot lip
inside the socket mouths, no blobs on the plug.

---

## A. Spool compatibility (do this before printing anything)

Record everything on `SPOOL_MEASUREMENTS.md`, one sheet per spool.

1. **Bore diameter in two directions.** Take the spool's label direction as horizontal,
   then measure at 90° to it (vertical). Measure at three depths:
   - mouth A, about 3 mm in
   - mid-depth, if your caliper reaches
   - mouth B, about 3 mm in

   That is 6 numbers per spool. Out-of-round = the largest − smallest value at the same
   depth.
2. **Bore depth.** Measure flange face to flange face along the bore.
3. **Obstructions.** Shine a light through the bore and look and feel along it for:
   - ribs, clips or snap latches (where the two spool halves join)
   - a step or change of diameter
   - mouth chamfers (estimate their size)
   - mould flash

   Note the depth of each feature from mouth A. **Anything inside the zones 5–13 mm in from
   either mouth is where the adapter arms touch.**
4. **Holder check.** Confirm how this spool is held in use. The cartridge works on roller
   cradles (AMS, AMS 2 Pro, AMS HT, roller dry boxes) and in bags. It **cannot be used** on
   any holder that passes through the bore (AMS lite, spindle holders).
5. **Adapter choice.** Use the smallest measured bore at the adapter zones:

   | Measured bore | Adapter |
   |---|---|
   | 51.1–52.8 | 52 |
   | 52.6–54.3 | 53.5 |
   | 54.1–55.8 | **55** |
   | 55.6–57.3 | 56.5 |
   | 57.1–58.8 | 58 |
   | 59.1–60.8 | 60 |

**Pass:** bore 51.1–60.8 mm, out-of-round ≤ 0.6 mm, no obstruction in the adapter zones,
holder leaves the bore empty, depth ≥ 64.5 mm.

---

## B. Cartridge fit

**At gauge level (fit-test plate).** Fit the 55 mm adapter onto the cap neck. Push the cap,
adapter first, into the spool bore about 10 mm. You are testing one adapter, which is half of
a real cartridge.

1. **Insertion.** Push it in with the force gauge on the cap rim (not on the window). Record
   the peak force. It should go in smoothly, with no snag at the bore mouth.
2. **Removal.** Pull it out by the cap head with the scale. Record the peak force. One
   adapter should give about half the full-cartridge value, ≈ 1.3 N.
3. **Wobble.** With it inserted, rock the cap by hand. Note any free play (it should be
   spring-loaded, with no clunk) and whether the arms bottom out.

**At product level (full cartridge, later).** Repeat steps 1–3 with the whole cartridge,
then:

4. Insert it until it is flush, centred in the spool width (1.5 mm recess each side).
5. **Retention.** Hold the spool vertical (axis up) and tap it firmly on a desk 5 times.
   The cartridge must not move. Then put the spool on the AMS rollers and run a 15-minute
   load / unload cycle: nothing rubs or walks out.
6. **Centring.** Look along the axis: the gap between the body and the bore should look even
   all round.

**Pass:**

| Measurement | Pass |
|---|---|
| Full-cartridge insertion | ≤ 12 N, no snag |
| Removal (full cartridge) | ≥ 2.0 N |
| Removal (gauge level) | ≥ 1.0 N |
| Taps / AMS cycle | no movement |
| Clunking play | none |

**If it fails:**
- Loose: use the next adapter size *down*.
- Too tight, or a snag: use the next size *up*, and check the bore mouth for a step.

---

## C. QuickLock (double gauge + both tuning rings + cap)

The double gauge has two dots near one end. That end was printed on top (mouth up). The
other end was on the bed. **Test both ends**: they print differently.

For each end, then for the 1-dot and 3-dot rings:

1. **Insertion.** Turn the cap until the lugs drop into the three slots. Note whether it
   drops in freely, needs pressure, or scrapes.
2. **Turn to lock**, clockwise looking at the cap face. Expected feel:
   - free turning
   - a firm spot over the last ~20°
   - a click
   - a hard stop

   The cap's deep flutes line up with the V-marks on the gauge. Note any catch at the
   *start* of the turn: that is the play problem (B2 in the review).
3. **Click force.** Rate it 1–5 (1 = barely felt, 3 = deliberate, 5 = hard to turn). If you
   can, measure the torque: a luggage scale on a string wound round the 46 mm head; torque =
   force × 0.023 m.
4. **Locked checks.**
   - Pull the cap axially. It must not come out.
   - Push and pull to feel the end float (expected ≤ 0.4 mm, felt as a slight tick).
   - Try to turn past the stop with moderate force: it must not over-rotate.
5. **Unlock.** It turns back with a click and comes straight out.
6. **Tongue inspection.** Under a flashlight, watch the slit-bounded tongue on the outside of
   the socket while you pass the click. It should visibly deflect a little and spring back.
   Then, with a loupe or a phone macro, check:
   - the tongue root (the slit ends) for whitening or cracks
   - the bump for shaving, a polished flat, or curls of plastic
   - the lugs for scraped corners

**Pass:**

- drops in without force
- no catch at the start of the turn
- a distinct click, rated 2–4
- stop holds
- no pull-out when locked
- no whitening, cracking or shaving
- both gauge ends behave the same

**Choose the detent:** pick the ring (0.20 / 0.30 nominal / 0.40) whose feel is best. Write
it in the results table. Changes to apply after the test:

| Observation | Change |
|---|---|
| Scrapes on entry | `fit_radial` +0.05 |
| Catches at the start of the turn | `bearing_play` +0.05 |
| Rattles when locked | `bearing_play` −0.05 |
| Feel | `detent_interference` = the chosen ring |

Change **one** value at a time.

---

## D. Indicator window (cap + window)

1. **Install** from the inside of the cap. Ears into the three notches, seat on the lip, turn
   60° clockwise (seen from inside) using the grip bar. Note the effort and any binding.
2. **Locked checks.**
   - Shake the cap face-down, then face-up: no rattle out.
   - **Push-in test:** cap face up on the desk, inside empty. Press the window from outside
     with your thumb, then with the force gauge to **20 N**. It must not move inward more
     than about 0.2 mm, and must not unlock.
   - Push from the inside with 20 N: it must not come out of the face.
3. **Removal.** From inside, turn it back 60° and lift it out.
4. **Readability.** Put a few fresh (orange) and a few saturated (green) beads behind the
   window and view at arm's length in room light.

**Pass:** installs and removes by hand, no tools; holds 20 N each way; does not turn by
itself; colour difference obvious.

**If it fails:**
- Ears too tight: `window_fit` +0.05
- Loose: `window_fit` −0.05
- Unreadable: use the film-carrier option (C2 + clear sheet)

---

## E. Desiccant containment and airflow

**At gauge level:**

1. Cap one end of the double gauge. Fill the gauge to just below the open socket's internal
   step with 2–5 mm beads.
2. Fit the second cap from the fit plate. If you only have one cap, use the gauge with one
   end capped and the other end held closed on a flat white surface.
3. Over white paper, shake vigorously for 60 s in all orientations. Then tap it 20 times on
   the desk.
4. Count escaped beads and fragments. Look for dust.
5. Check each vent slot with a light: open, not bridged by strings or sag. Check the tongue
   slits are open.

**At product level:** repeat with the full cartridge, filled to the internal step (≈ 55 mL,
38–44 g). Also check:

- **Airflow:** hold the cartridge up to a light. You should see light through all 65 body
  slots and 20 slots in each cap face.
- **Optional humidity check (T6 of the P001 plan):** a sealed 30 L box with a hygrometer.
  Log RH every hour for 24 h with the cartridge, and repeat without it.

**Pass:**

- 0 whole beads escape
- fragments < 1 mm only, ≤ 3, and all traceable to broken beads (sieve beads over a 2 mm
  mesh first)
- all slots open
- no bead lodged in a bayonet groove after re-capping

---

## F. Durability

1. **First 10 cycles, documented.** On the chosen detent setting (bottom-end socket of the
   double gauge, or the full cartridge), one cycle = insert, lock, unlock, remove. For each
   cycle record:
   - click rating (1–5)
   - any catch
   - any new mark on the bump, tongue or lugs

   Take a macro photo of the tongue root after cycles 1, 5 and 10.
2. **200-cycle test.** Continue to 200 cycles, at roughly 5 s per cycle, with a rest every
   50 cycles. At 50, 100, 150 and 200, record:
   - click rating
   - locked end float (feel it, or measure with a dial indicator if available)
   - pull-out (it must still hold)
   - tongue root photo

**Pass at 200 cycles:**

- click still distinct (rating ≥ 2 and within 1 point of cycle 1)
- no whitening or cracks at the tongue root or slit ends
- the bump isn't flattened
- the lugs aren't rounded enough to change the feel
- end float unchanged by feel
- still holds when locked

---

## Results table

| ID | Test | Part / setting | PASS | FAIL | NOTES (numbers, photos) |
|---|---|---|---|---|---|
| A1 | Bore measured, 2 directions × 3 depths | spool # | ☐ | ☐ | |
| A2 | No obstruction in the adapter zones (5–13 mm from each mouth) | | ☐ | ☐ | |
| A3 | Holder leaves the bore empty | | ☐ | ☐ | |
| A4 | Adapter size chosen | ___ mm | ☐ | ☐ | |
| B1 | Insertion force, no snag | gauge / full | ☐ | ☐ | ___ N |
| B2 | Removal force | gauge / full | ☐ | ☐ | ___ N |
| B3 | No clunking wobble; centred | | ☐ | ☐ | |
| B4 | Taps + 15 min AMS cycle, no movement | full | ☐ | ☐ | |
| C1 | Cap drops into the bottom-end socket freely | gauge | ☐ | ☐ | |
| C2 | Cap drops into the top-end socket (2-dot end) freely | gauge | ☐ | ☐ | |
| C3 | No catch at the start of the turn (both ends) | gauge | ☐ | ☐ | |
| C4 | Detent click distinct (rating 2–4) | 0.20 / 0.30 / 0.40 | ☐ | ☐ | ratings: __ / __ / __ |
| C5 | Torque to pass the click (optional) | | ☐ | ☐ | ___ N·m |
| C6 | Hard stop holds; no over-rotation | | ☐ | ☐ | |
| C7 | Locked cap won't pull out; end float acceptable | | ☐ | ☐ | |
| C8 | Tongue flexes and springs back visibly | | ☐ | ☐ | |
| C9 | No cracking, whitening, deformation or shaving | | ☐ | ☐ | photo refs |
| D1 | Window installs and removes by hand | | ☐ | ☐ | |
| D2 | Window resists 20 N push-in | | ☐ | ☐ | |
| D3 | Window resists 20 N push-out | | ☐ | ☐ | |
| D4 | Colour change readable | | ☐ | ☐ | |
| E1 | No whole beads escape (60 s shake + 20 taps) | gauge / full | ☐ | ☐ | count: |
| E2 | All vent and tongue slits open | | ☐ | ☐ | |
| E3 | No beads in the grooves after re-capping | | ☐ | ☐ | |
| E4 | Humidity drop (optional) | | ☐ | ☐ | RH start/24 h: |
| F1 | Cycles 1–10 documented, no damage | | ☐ | ☐ | see log |
| F2 | 200 cycles: click, float and hold OK, no cracks | | ☐ | ☐ | |

### Cycle log (first 10)

| Cycle | Click 1–5 | Catch? | Marks on bump / tongue / lugs | Photo |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 50 | | | | |
| 100 | | | | |
| 150 | | | | |
| 200 | | | | |

### Parameter changes decided from testing

| Parameter | V1.1 value | New value | Reason (test ID) |
|---|---|---|---|
| fit_radial | 0.30 | | |
| bearing_play | 0.40 | | |
| detent_interference | 0.30 | | |
| window_fit | 0.15 | | |
| adapter size for Bambu spool | 55 | | |
