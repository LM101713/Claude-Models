# FILAMENT PATH: owner measurement guide

**Purpose:** collect the dimensions and photos the specification needs before any CAD. This guide replaces the list in the original report §13. Item IDs match [`measurements_template.csv`](measurements_template.csv): fill that file in, or send the values in chat. Either way is fine.

**Most important item:** [H01, the H2 rear spool-holder mounts](#h01-h2-rear-spool-holder-mounts-critical). Without it, the H2 anchor cannot be designed.

**Time:** about 45 min for the P1S, about 60–75 min for each H2, and about 1.5 h for the H2C heat test (mostly waiting).

---

## 0. Before you start

### Tools

| Required | Helpful |
|---|---|
| Digital calipers | Phone level app |
| Steel ruler, 300 mm | Probe thermometer (for H08 only) |
| Tape measure or a length of string | Contour gauge |
| Phone camera | Low-tack painter's tape (temporary marks only; remove afterwards) |
| Sewing thread with a small weight (a plumb line) | |
| Plain paper and a soft pencil | |

### Rules

1. **Nothing is taken apart.** Don't remove or loosen any screw, and don't pry anything. The only part you may take off is one designed to come off by hand: the H2 rear spool holder, and only if it slides off with light finger force (H01-16).
2. Keep the printer **idle and cool** for every measurement except H08.
3. **Measure each caliper dimension 3 times** and write down all three readings. The spread shows how reliable the reading is.
4. **Accuracy:**

   | What | Accuracy |
   |---|---|
   | Caliper dimensions | to 0.05 mm |
   | Positions | ±1 mm |
   | Angles | ±2° |
   | Tube lengths | ±5 mm |

5. If something doesn't match this guide (a part looks different, or doesn't exist), **photograph it and describe it.** Don't guess a number. "Not found" is a useful answer.

### Photo rules

- Point the phone **straight at the feature** (perpendicular to it). Use 2× zoom from about 40–50 cm away; a wide-angle shot close up distorts sizes.
- Put a **ruler in the same plane as the feature**. The scale is only valid in that plane.
- For angles, hang the **plumb line** in the frame. It gives a true vertical.
- Use soft, even light. On glossy parts, light from the side shows edges better than a flash.
- Put a small paper label with the **item ID** in the frame, for example "H2C-H01-U-3".
- **Naming:** `PRINTER_ID_n.jpg` (for example `H2C_H01-U_3.jpg`). You can also just send the photos in chat with the ID in the message.

### Coordinates (used for every position)

Stand **behind the printer, facing its rear panel.**

```
        Z (height above the table the printer stands on)
        ^
        |      rear panel, seen from behind
        |   +---------------------------+
        |   |                           |
        |   |                           |
        |   +---------------------------+
        +---|---------------------------|-----> X
           X=0                             (measured from the side edge
       (side edge on YOUR LEFT              on your left, going right)
        as you face the back)

  Y = distance straight out from the main flat surface of the rear panel,
      towards you (negative = in front of that surface, e.g. over the top)
```

- **X reference:** hold a book or box flat against the left side panel, so the side plane extends out where your ruler can reach it.
- **Z reference:** stand the ruler on the table.
- **Y reference:** hold a straight ruler flat across the rear panel's main surface.

---

## G: all three printers (P1S, H2S, H2C; repeat per printer)

| ID | What | How |
|---|---|---|
| G01 | **Rear photo set** | (1) Full rear, straight on. (2) Close-up of the filament inlet area. (3) From the side, at rear-panel level, showing how far everything sticks out. Take all three with AMS units in their normal places, then again with the AMS lifted off, or the lid area clear if it can't be lifted |
| G02 | **Stock routing photos** | Each external tube, from the AMS outlet to the printer inlet. Photograph from the side and from behind, with the plumb line and ruler in frame. **Don't straighten or tidy the tube first:** this is the baseline |
| G03 | **Tube OD** | Calipers on 3 different stock tubes, at 3 points each. At each point, measure, rotate the tube 90°, and measure again (this shows ovality). Record all 18 readings |
| G04 | **External tube lengths** | Run string along each installed external tube, from coupler face to coupler face, then measure the string. Record which tube is which |
| G05 | **AMS outlet, position and direction** | For each AMS in its usual place: X, Y, Z of the centre of the outlet coupler. For direction, take a side photo with the plumb line, plus the angle from vertical on the level app if you have one |
| G06 | **Printer inlet, position and direction** | P1S: the buffer left port, or the AMS Hub / coupler you actually use. H2: the upper and lower buffer inlets. X, Y, Z, and direction as in G05 |
| G07 | **Tightest stock bend** | At the tightest bend in each tube, lay the ruler across the bend as a chord, touching the tube at both ends. Record the chord length **c**, and the gap **s** from the ruler to the tube at the middle (calipers' depth rod). Don't press on the tube. (I calculate R = c²/8s + s/2.) |
| G08 | **Space behind the printer** | The distance from the rear panel to the wall or nearest obstacle, in your setup |
| G09 | **AMS topology** | Write down: which AMS units (AMS 2 Pro, AMS HT, etc.); top or side; buffer, AMS Hub, 4-in-1 adapter or track switch; which AMS feeds which inlet |
| G10 | **Method check** | Measure the printer's overall width and height. I compare them with Bambu's spec (P1S 389 × 457/458 mm; H2 492 × 626 mm) to check the measuring method. **Don't adjust your numbers to match.** |
| G11 | **Spool core** (once, not per printer) | Outside diameter of a Bambu spool's barrel, where the first layer of filament sits. An empty spool is best |

---

## P: P1S only

| ID | What | How |
|---|---|---|
| P01 | **Rear coupler** (upper-right corner) | Position X, Z (centre). Collar OD (calipers). How far it sticks out from the panel. Outline of the black bracket it sits in: W × H, and gap to the panel edges. Photos straight on and from the side |
| P02 | **Filament buffer** (or AMS Hub) | Outline W × H × depth. Position (X, Z of its corners). Port spacing, centre to centre. Port directions (photo with plumb line). Where its cables leave. **Don't remove its screws.** |
| P03 | **Rear spool holder** (fixed with 2 screws; leave them alone) | Outline of its base on the panel. Thickness of the arm. **The gap between the base and the panel at its edges:** can a 2 mm card slide behind it, and where? This decides whether a clip can wrap around it. Position X, Z. Photos from the side, from above, and straight on |
| P04 | **Rear vent holes** | The boundary of the hole area (X, Z of its corners) |
| P05 | **Purge chute opening** | Position, W × H. Which side, left or right as seen from behind |
| P06 | **Internal tube exit** | Where the tube to the toolhead comes out at the top or rear (X, Z), and its free length to the coupler. Photo |
| P07 | **Door and lid** | Door hinge side, seen from the front. A close-up photo of the top glass edge where it sits on the frame |

---

## H01: H2 rear spool-holder mounts (CRITICAL)

Do this on **both the H2S and the H2C**, and on **both the upper (U) and lower (L)** mounts. Bambu's wiki says the holders "align… with the upper and lower mounts at the back… Slide them down to install" [VO, via search extract; not yet seen on the live page]. The wiki also mentions a base held by 2 × M3×12 screws [VO], but it is **not yet known** whether that base stays on the printer. **Leave all screws in place.**

### Step 1: photograph before touching anything

- `H01-U-1`: straight on, with the holder fitted and a ruler.
- `H01-U-2`: from the side, at mount level.

Do the same for L.

### Step 2: remove the holder, by hand only (H01-16)

- Try sliding it **up**, the reverse of "slide down to install".
- If it doesn't move with light finger force, **stop.** Look for a latch or tab, photograph it, and tell me. Don't force it and don't use tools.
- Record the direction it came off, roughly how firm it felt (loose / snug / firm), and whether you had to press a tab.
- Note which part stayed on the printer (the **mount**) and which part came away (the **holder**).

### Step 3: identify the type (H01-1)

Tick one, and photograph the mount with the holder off:

- (a) an undercut slot or rail (T-slot or dovetail);
- (b) keyhole holes;
- (c) a hook-over ledge;
- (d) something else (describe it).

### Step 4: measure the mount

The drawing below shows type (a). For other types, measure the same ideas: opening, inner width, depth, lip and length.

```
 CROSS-SECTION through the slot (cut horizontally, seen from above)

   rear panel surface ─────────┐   W1   ┌───────── (towards you = +Y)
                          T1 ↕ │<------>│
                  ┌────────────┘        └────────────┐
                  │                                  │  D1 = surface to floor
                  │<------------- W2 --------------->│
                  └──────────────────────────────────┘  (slot floor)

 FRONT VIEW (as you look at the rear panel)

          ┌──W1 top──┐       ← measure W1 at the top...
          │          │
          │   L1     │  engagement length (how far the holder slides)
          │          │
          └──W1 bot──┘       ← ...and at the bottom (taper)
              ▲ bottom stop
```

| ID | Dimension | How |
|---|---|---|
| H01-2 | **Position** | X of the slot centreline. Z of the top end and the bottom stop |
| H01-3 | **W1, mouth width** | Narrowest opening at the surface. Caliper **inside** jaws |
| H01-4 | **W2, inner width** | Widest point behind the lips. Inside jaws, angled in carefully. If you can't reach it, say so and rely on H02 |
| H01-5 | **D1, depth** | Rear surface to slot floor. Caliper depth rod |
| H01-6 | **T1, lip thickness** | Rear surface to the underside of the lip. If you can't reach it with the depth rod, use H02 |
| H01-7 | **Lengths** | L1, how far the holder slid. Total slot length, top to bottom |
| H01-8 | **Bottom stop** | Its shape, and its Z position. Photo |
| H01-9 | **Latch or detent** | Present or not. If present: where it is, its size, how it releases. Photo |
| H01-10 | **Taper** | W1 measured at the top and at the bottom of the slot |
| H01-11 | **Edge details** | Chamfers, ribs, visible draft angle, texture. Macro photo |
| H01-12 | **Clearances** | Distance from the slot's outer edge to the nearest other feature on each side (up, down, left, right): buffer, vents, the other mount, panel edge |
| H01-13 | **U-to-L spacing** | Distance between the same point on the upper and lower mounts (for example, the bottom stop to the bottom stop). Also the X offset between them, if any |
| H01-14 | **Paper rubbing** | Lay paper flat over the mount and rub with the side of a soft pencil, so the outline appears at 1:1. Photograph it flat with a ruler. Contour gauge profile if you have one |
| H01-15 | **Same or different?** | Are U and L identical? Are the H2S and H2C mounts identical? Compare H01-3 to H01-7 and note any difference above 0.2 mm |
| H01-16 | **Removal** | As recorded in step 2 |

**Photos with the holder off:**

- `H01-U-3`: straight on with a ruler.
- `H01-U-4`: 45° from above.
- `H01-U-5`: 45° from the side.
- `H01-U-6`: macro with the calipers in the slot, showing the reading on screen.

### Step 5: measure the holder's mating part (H02)

Measuring the outside of the holder's tongue or hook is usually more accurate than measuring inside the slot. Use **outside** jaws, 3 readings each:

- tongue width;
- tongue thickness;
- hook or lip depth;
- engagement length;
- which faces carry the load (they are often shiny from wear).

Photos:

- the holder's profile, laid on paper with a ruler (`H02-U-1`);
- a close-up of the tongue (`H02-U-2`).

### Step 6: refit the holder

Slide the holder back on exactly as it was. Check that it seats as firmly as before, and write "refitted OK".

---

## H: other H2 items (H2S and H2C)

| ID | What | How |
|---|---|---|
| H03 | **Buffer inlets** | For each inlet (upper and lower on the H2C): collar OD, how far it sticks out, and the angle from vertical (plumb-line photo). Position and size of the **buffer window**. Positions also go in G06 |
| H04 | **Keep-out areas** | Purge chute opening: position and W × H. Exhaust grille: X, Z of its corners. You may outline them temporarily with painter's tape for the photo; remove it afterwards |
| H05 | **Rear items** | X, Z of the safety-key socket, the ports, the e-stop (if fitted) and the laser air pipe (if fitted). Photo |
| H06 | **Door and lid** | Door hinge side. How you open or remove the top glass in normal use with the AMS on top |
| H07 | **H2C only: 4-in-1 PTFE adapter II** | Body L × W × H. Port spacing. Angle between the ports. Photos from 3 sides with a ruler. **The same for the track switch,** if you have one |
| H08 | **H2C only: rear air temperature** | Run the chamber at 65 °C (ABS/ASA profile or chamber preheat). After 1 h at 65 °C, hold the probe tip in the air **about 10 mm** from (a) each buffer inlet, (b) each spool-holder mount and (c) the edge of the exhaust grille, keeping it out of the grille itself. Read each point after 60 s. Record the room temperature too. Keep the cable clear of everything; nothing goes inside the printer |

---

## O: optional (helps the claims)

| ID | What |
|---|---|
| O01 | Screenshots of the last 30 days of HMS errors for each printer (Bambu Handy or Studio) |
| O02 | Any feed problems you've seen yourself: which printer, which slot, which filament |
| O03 | Is a 2 m sample of your most brittle filament available (PLA-CF, PETG-CF, PPA-CF)? Needed for experiment E3 |

---

## Sending it back

1. Fill in [`measurements_template.csv`](measurements_template.csv), or type the values in chat as `ID: value, value, value`.
2. Send the photos in chat with their IDs. I'll file them under `filament-path/measurements/`.
3. Anything you couldn't measure: list the ID and write "not reachable", "not found" or "different from guide", with a photo.

**What happens next:**

1. I check G10 against Bambu's specifications.
2. I flag any inconsistent readings.
3. I list anything that needs re-measuring.
4. Then I finalise the mechanical specification for your approval.

**No CAD before that approval.**
