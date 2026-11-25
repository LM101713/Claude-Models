# FILAMENT PATH: Revision 01, owner refinements (2026-11-25)

The owner approved the narrowed direction: an external-only, fixed-radius routing system. The Service Dock is rejected. This document records the seven refinements the owner asked for. **It supersedes the matching sections of [`README.md`](README.md).** The original report stays unchanged as the research record, including its research limits in §2.2. The evidence labels are unchanged:

| Label | Meaning |
|---|---|
| [VO] | Official |
| [OR] | Owner-reported |
| [UV] | Unverified or typical value |
| [EST] | Estimate or calculation |
| [HYP] | Hypothesis to be tested |
| [MEASURE] | Unknown until measured |

**No estimate in this revision has become a fact.** Nothing has been printed or tested.

**CAD status: not started.** CAD begins only after the owner measurements ([`MEASUREMENT_GUIDE.md`](MEASUREMENT_GUIDE.md)) are collected and the mechanical specification is finalised (§8).

---

## 1. The 80 mm radius is provisional, and here is how it is tested

R80 is a **starting hypothesis**, not a known optimum. It came from two inputs:

- a filament-strain calculation (ε = 0.875 / R) using a typical PLA elastic limit [UV];
- a rear-space estimate [EST].

Neither input has been measured. Four experiments set the final radius.

| # | Experiment | Method | What it decides |
|---|---|---|---|
| E1 | **Radius sweep** (friction) | Pull-force protocol (§5), using 180° U-lanes at **R40, R50, R60, R80, R100, R120**. Every lane has the same wrap angle, so only the radius changes. Plot the tension ratio against 1/R | **R_knee**: the smallest radius whose mean ratio lies within the session's measurement noise (2 × pooled SD) of the R120 result. Below it, bending stiffness measurably adds drag; above it, a bigger radius buys nothing |
| E2 | **Wrap-angle check** | At R80, compare a 180° lane with a 540° lane (one extra full loop). ln(ratio₅₄₀ / ratio₁₈₀) = μ·2π | Measures μ (the original report *assumed* 0.2). It also checks the claim that total wrap angle matters more than radius, which is the basis of design rule R3 |
| E3 | **Brittle-filament test** | The most brittle filament the owner has (e.g. PLA-CF or PETG-CF; PPA-CF if available). (a) Bend 5 samples slowly around decreasing radii until one snaps, and record **R_break**. (b) Hold 5 samples at each candidate radius for 24 h at room temperature and 24 h at the rear-air temperature measured in guide item H08. Check for cracks | **R_min ≥ 1.5 × R_break**. The 1.5 factor is engineering judgement: brittleness varies with moisture and age. It is recorded here as a judgement to review, not a derived value |
| E4 | **Space check** | From the guide measurements (rear clearance, AMS outlet and inlet positions) | **R_fit**: the largest radius that fits on the P1S, H2S **and** H2C |

**Decision rule.** R_final = the larger of R_knee and 1.5 × R_break, rounded up to the next 10 mm, but no larger than R_fit.

- If R_fit is smaller than the friction or breakage requirement, that conflict goes to the owner with the data. I will not silently choose.
- One radius is used for every printer (§2).

**Test hardware.**

- **TB-1 Radius Ladder:** one printed board with the six U-lanes plus the R80 540° lane. Each lane is built from stock 4/2.5 PTFE tube held in printed channels, and each has 100 mm straight vertical tails at both ends.
- TB-1 does not depend on any printer measurement.
- **Pre-CAD fallback:** E1 and E3 can start now without CAD. Wrap tube around household cylinders of caliper-measured diameter (centreline R = cylinder radius + 2.0 mm) and hold it with painter's tape. This method is less repeatable than TB-1.

See approval item A2 in §8.

---

## 2. Shared parts stay identical on all three printers

| Part | Shared or specific | Rule |
|---|---|---|
| Arc 90°, Arc 45° | **Identical files** for P1S, H2S and H2C | One radius (§1), one cross-section, one FP-Link interface |
| Lead-in (30 mm straight) | **Identical** | Built into every anchor through the same FP-Link interface. Also printable on its own |
| FP-Link peg and socket | **Identical** | The same interface on every anchor |
| Fit coupon | **Identical** | Each owner prints it on their own printer, and one parameter set drives all parts |
| Anchor P1S | Specific | Only where the P1S rear geometry requires it |
| Anchor H2 | Specific | **One design for H2S and H2C** if their rear mounts match within 0.2 mm (guide item H01-15). A second design only if they don't |
| Merge Cradle | H2C only, still gated on test data | Unchanged from the original report |

**Rule for printer differences.** Any difference between printers is solved in the **anchor**, through its geometry or the FP-Link angle. It is never solved by changing an arc.

**The separate "Compact R60" arc family is dropped.** A per-printer radius would break the identical-arc rule. If space is tight on one printer, that printer uses Arc 45° combinations or anchor geometry instead.

---

## 3. Tool-less installation, no permanent printer modification

| # | Rule |
|---|---|
| I1 | Install and remove by hand. No tools. |
| I2 | **No OEM screw is removed or loosened.** No adhesive, tape, magnets, drilling, or cutting of printer parts. |
| I3 | The only OEM part that may be removed temporarily is one Bambu designed to come off by hand, such as an H2 rear spool holder that slides off its mount (to be confirmed in guide item H01-16). It goes back unchanged. |
| I4 | **No tube cutting and no coupler disconnection is needed.** Arcs snap onto the tube where it is already installed. Tubes stay at Bambu's lengths. |
| I5 | Removal leaves no marks. Every face that touches the printer has 0.5 mm edge chamfers and no sharp corners, and it is checked for scuffs after the 100 h test. |
| I6 | Targets: **install in 5 minutes or less per printer, remove in 1 minute or less.** Both are timed in validation. |

**What this changes from the original report.**

- The P1S rear spool holder is fixed with 2 screws [VO], so an anchor may only **clip around** it or around the coupler bracket. Nothing may go under the screws.
- **Fallback:** if no tool-less anchor point exists on the P1S, the P1S kit ships as **floating arcs only**, with no anchor. That is acceptable, because the arcs work on the tube by themselves.

---

## 4. Gauge and cut jig are optional, and gated

They are included **only if all of these hold**:

| # | Gate |
|---|---|
| G1 | They are designed **after** the core parts are frozen, and they share no parameters with the core parts. |
| G2 | Each is one part, prints with no supports, takes 15 min or less and uses 5 g or less. |
| G3 | They sit on their own print profile, so the core kit is never larger because of them. |
| G4 | **Gauge:** the printed radii are checked with the chord-and-sagitta method, R = c²/(8s) + s/2, to within ±1 mm. |
| G4 | **Jig:** 10 cuts all seat fully in a coupler and sit flat against a flat surface. **If the jig does not beat a careful freehand razor cut, it is dropped.** |

Either tool is dropped if it delays the core product or fails its gate.

---

## 5. Pull-force protocol PF-1 (kitchen scale, controlled conditions)

**Purpose.** To compare the tension needed to pull filament through two tube paths: stock vs FILAMENT PATH, or one radius vs another. The comparison is relative, so anything the two conditions share cancels out.

### 5.1 Equipment

- Kitchen scale, 1 g resolution.
- Two light cups.
- Water, plus a syringe or small measuring jug.
- Two small binder clips.
- A vertical test board (TB-1, or a flat cupboard door or foam board with painter's tape for the pre-CAD fallback).
- Phone timer.
- Marker.
- Thermometer or hygrometer (recommended).

### 5.2 Controlled variables

| Variable | Control |
|---|---|
| Tube | New stock Bambu 4/2.5 mm tube, cut square. Blow it through before use. **The same piece is used for every run of a given condition** |
| Filament | Same spool for the whole session. Cut a 2 m sample from one region. Record the brand, type, colour, and whether it was dried and when |
| Filament curl and twist | Draw a marker line along the sample. The spool's natural curl lies **in the plane of the bend, curving the same way** in every run, and the line faces the same way at the inlet each time |
| Temperature and humidity | Recorded at the start and end. Test only at 18–26 °C |
| Back-tension | Inlet mass **200 g ± 1 g** (cup, water and clip weighed together) |
| Geometry | Both tails are 100 mm, straight and vertical, pointing down, held identically in both conditions. **Stock vs FILAMENT PATH comparisons use the same end positions, end directions and tube length.** (A free tube with fixed ends and length settles into the same natural shape, which is why guide items G05 and G06 capture the end positions and directions) |
| Loading rate | Coarse run first, to find the approximate threshold. Each counted run then starts at 85 % of that threshold and adds **2 g every 10 s** |
| Motion criterion | **The outlet cup descends at least 50 mm, without stopping, within 30 s of the last addition.** The cup mass at that moment is the result |
| Order | ABBA ABBA… (alternating), never all of A first |
| Repeats | **n = 5 counted runs** per condition per filament |
| Session control | A reference lane (the R120 U-lane) is run at the start and end. **If the start and end values differ by more than 5 %, the session is void** (the filament or conditions drifted) |
| Operator | The same person for a whole comparison |

### 5.3 Procedure

1. Check the scale against a known mass, for example 100 mL of water measured with a syringe (about 100 g at room temperature). Record any offset.
2. Thread the filament sample through the path. Clip the 200 g back-tension cup to the inlet end and the empty outlet cup to the outlet end. Let both hang freely.
3. Do the coarse run: add 10 g every 10 s until the motion criterion is met. Note the threshold, then discard this run.
4. For each counted run:
   1. pull the sample back by the inlet end, so the same segment is tested;
   2. check the marker line;
   3. pre-fill the outlet cup to 85 % of the coarse threshold;
   4. add 2 g every 10 s until the motion criterion is met;
   5. weigh the outlet cup with its clip, and record it.
5. **Tension ratio = outlet mass ÷ back-tension mass.**

### 5.4 Analysis

- Report the mean and standard deviation for each condition.
- **A difference counts only if it is larger than 2 × the pooled SD and larger than 5 %.**
- A "less resistance" claim on MakerWorld still needs a drop of 10 % or more on at least one tested printer. Only measured numbers are quoted, with the printer and filament named.
- The data go into `measurements/pull_force.csv` (template columns: session, date, °C, %RH, filament, condition, lane, run, back-tension g, outlet g, ratio, notes).

### 5.5 Limits stated in advance

- PF-1 measures **steady pull-through on a bench**. It is not the AMS feed force on the printer.
- The on-printer checks stay as in the original report §11.3 and §11.6: load/unload cycles and the HMS error log.
- If the real stock path is clearly three-dimensional (guide item G05/G06 shows a large left-right offset), the bench copy is an approximation. That will be stated with the result.

---

## 6. Release scope

| Printer | Status at launch |
|---|---|
| **P1S, H2S, H2C** | The only printers tagged as compatible. Tested |
| P2S, X2D | **Future targets.** Not verified; no anchor until measured on a real printer |
| X1C, X1E, H2D | Also treated as future targets in the listing tags (stricter than the original report's "designed for"). The description may say they "share Bambu's documented layout but are untested" |
| Any 4 mm OD tube | The arcs fit the tube by geometry. Performance on other printers is untested, and the listing says so |

---

## 7. MakerWorld presentation strategy (final, apart from test numbers)

### 7.1 Thumbnail: an honest before and after

**Format.** Two real photos, taken from the **same camera position**, split down the middle. No renders. The cover shows the P1S, because it has the largest audience and the most recognisable outline; the H2C is image 2.

- **Framing.** The rear-top corner where the tube leaves the AMS and drops to the printer inlet. The AMS edge and the printer's top rear corner must both be in frame, so the photo reads as "the back of a Bambu".
- **Left half, "STOCK".**
  - The real stock routing, exactly as it shipped. **No staged kink.**
  - A thin white line traces the tightest bend, labelled with its **measured** radius ("R 34", for example, if 34 mm is what was measured).
  - If the stock routing has no tight bend, the story becomes "the tube moves". In that case, use a two-exposure overlay of the tube in two positions, again with no staging.
- **Right half, "FILAMENT PATH".** The arcs fitted. The orange accent rings are visible, with a large **"R80"** (or whatever final radius is chosen) in orange.
- **Text.** At most two words per side, plus the two numbers. No arrows except the trace line. No glow, no emoji.
- **Look.** Matte graphite backdrop (black foam board) behind the printer, with one soft light from the upper left. Orange appears **only** on the parts and the radius numbers.
- **Safe area.** Keep the tube and the numbers inside the central 80 %. MakerWorld's current cover crop is [MEASURE: check it on the upload page before shooting].
- **After testing only.** A small third line, "−XX % pull force · tested on P1S", with the real number. Leave it out if the claim threshold (§5.4) is not met.

### 7.2 Gallery order

| # | Image |
|---|---|
| 1 | Cover |
| 2 | H2C rear, multi-AMS layout, labelled |
| 3 | H2S rear |
| 4 | Close-up of the tube snapping into an arc (a short clip if MakerWorld allows video) |
| 5 | Pull-test bench, with the results chart (real data only) |
| 6 | Install sequence, 4 frames |
| 7 | Fit coupon, "print this first" |
| 8 | Plate layouts per profile |
| 9 | Compatibility table |

### 7.3 Title

> **AMS PTFE Tube Guide – Fixed-Radius Bends, No Kinks | P1S · H2S · H2C**

The brand appears only in the first line of the description. Check the MakerWorld title length limit at upload [MEASURE].

### 7.4 Description draft (plain voice; the owner should edit it into their own words)

Text in `{braces}` is filled in only from real test results.

> The tube between your AMS and the back of the printer is easy to ignore until a print stops with a feed error. Bambu's own page for that error says to avoid a tube that is "too long and excessively bent". This is a small set of snap-on guides that holds that tube in a smooth, fixed curve and keeps it straight where it goes into the printer.
>
> **What it does**
> - Keeps every bend at R{R} mm or wider, with no tight kinks.
> - Holds the tube straight for the last 30 mm into each fitting, so nothing pulls sideways on the connector.
> - Stops the tube moving between prints, so the path is the same every time.
>
> **What it doesn't do**
> - Nothing goes inside the printer. It won't stop the tube rubbing on the glass lid; that's a different problem.
> - You don't cut any tube and you don't remove any screws. Bambu's tube lengths stay as they are.
>
> **Does it help?** I measured it with a kitchen scale (the method is in the last photo, so you can check yours). With {filament} on my {printer}, pulling filament through the stock routing took {X} g; through this routing it took {Y} g. If your stock routing is already smooth, expect less difference.
>
> **Tested on:** P1S, H2S and H2C. It should suit other Bambu printers that use the same 4 mm tube, but I haven't tested them. If you try it on one, a photo of the back helps me make a proper version.
>
> **Install (about 5 minutes, no tools):** print the fit test, press the tube into the arcs, clip the anchor on, and check that each bend sits in its arc.
>
> **Print:** PETG, 0.2 mm layers, 4 walls, no supports. Print the 10-minute fit test first.

---

## 8. Updated work sequence and approvals

| Phase | Work | Gate |
|---|---|---|
| A | **Owner measurements** ([`MEASUREMENT_GUIDE.md`](MEASUREMENT_GUIDE.md)) | All required items returned |
| B | Specification finalised: every dimension set from the measurements, with the **radius as a parameter** set by the rule in §1 | Owner approves the final spec |
| C | CAD of the test hardware only: TB-1 Radius Ladder and the fit coupon | — |
| D | E1–E4 and the stock baseline (PF-1) | Radius chosen by the §1 rule; the owner sees the data |
| E | Product CAD (arcs, anchors), then the gated tools | — |
| F | Validation (original report §11, updated by this revision) | Pass, or apply the kill criteria |

**Owner decisions needed now:**

- **A1.** Confirm the phase order above.
- **A2.** TB-1 doesn't depend on printer measurements. Should it be modelled in phase C as planned, or allowed to start earlier, in parallel with phase A? The pre-CAD household-cylinder fallback can start immediately either way.
- **A3.** Confirm the stricter launch tags (§6): only P1S, H2S and H2C.
