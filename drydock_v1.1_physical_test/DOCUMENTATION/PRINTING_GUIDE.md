# DRYDOCK V1.1: printing guide (Bambu Lab H2C)

> **Status of every setting below: ESTIMATED / RECOMMENDED. None of it has been validated on
> a physical print.** Nothing in this package has been printed or sliced. Nothing has been
> opened in Bambu Studio either: the 3MF files were checked with a Python 3MF reader only.
> When a setting is confirmed on your H2C, record it in the "Validated" column of the table
> at the end.

## 1. Printer configuration

| Item | Recommendation | Basis |
|---|---|---|
| Printer | Bambu Lab H2C | design target |
| Nozzle | **0.4 mm hardened steel or stainless** (the standard H2C nozzle) | all walls (1.2–2.4 mm) and vent slots (1.2 mm) are sized for 0.4 mm lines; a 0.6 mm nozzle would close the 1.2 mm slots and 0.8 mm tongue slits |
| Build plate | **Textured PEI** for all charcoal/orange parts; smooth PEI + glue stick for the clear window (glossier, clearer face) | PETG releases cleanly from textured PEI without glue |
| Slicer | Bambu Studio, H2C machine profile, **system PETG profile** (Bambu PETG HF or PETG Basic) | do not hand-edit the machine profile |
| Filament | PETG, dried (65 °C for 8 h if the spool has been open more than a few days) | wet PETG strings and blobs, which ruins 0.3 mm clearances |

## 2. PETG process settings (all estimated)

| Setting | Fit-test & structural parts | Window / blank* |
|---|---|---|
| Layer height | **0.20 mm** (the clearances were computed for 0.20 mm layer steps) | 0.20 mm (6 layers) |
| First layer | 0.20 mm | 0.20 mm |
| Wall loops | **4** | 4 |
| Top / bottom shells | 5 / 5 | solid |
| Sparse infill | 20 % gyroid (only the cap heads and gauge collars contain any) | 100 %, monotonic |
| Nozzle temperature | **250 °C** (profile default; 255 °C if layer adhesion is weak) | 255 °C |
| Bed temperature | **70 °C** | 70 °C |
| Supports | **OFF** | OFF |
| Elephant-foot compensation | **0.15 mm** (protects the socket mouth, the cap face slots and the plug fit) | 0 |
| Seam | Aligned (on the body and gauges it settles into the entry-slot corners, off the fit surfaces) | — |
| Brim | none needed | none |
| Part cooling | profile default | profile default |
| XY hole / contour compensation | **0** (the clearances already allow for FDM deviation; double compensation loosens the fit) | 0 |
| Slicer scaling | 100 %; do not pre-scale for shrinkage | 100 % |

\* **Window is optional as an indicator.** Without clear filament, print the window in PETG
HF with the same settings as the other parts. It becomes an opaque blank that seals the
face. It must still be fitted.

**Filament actually used for the first test: Bambu PETG HF**, with the system PETG HF profile
temperatures, for every part.

## 3. Orientation and supports

Every STL is exported **already in print orientation**. Import it and do not rotate it.

| Part | Orientation (as exported) | Supports | Notes |
|---|---|---|---|
| T1 double fit gauge | upright, either end down | none | slit ceilings are 14.6 mm bridges (normal for PETG) |
| T2 detent tuning rings (1 dot / 3 dots) | mouth down | none | |
| B cap | **face down** on the plate | none | 45° internal funnel and lug flanks; the window ledge is a 45° cone |
| C window / blank | flat, grip bar up | none | PETG HF (opaque blank) or clear PETG (indicator) |
| D adapter (55 mm) | flat | none | orange PETG; the spring arms become solid perimeters with 4 walls |
| A body (full cartridge) | upright, either end down | none | |
| E coupler | upright | none | expansion only |

## 4. Fit-test plate (print this first)

File: `PRINT_FILES/3mf/DD011_plate4_fit_test.3mf`. Contents (all six objects were checked
watertight, and each matches its STL by volume):

| Object in the 3MF | STL | Size (mm) | Qty |
|---|---|---|---|
| Double fit gauge, 2 dots | `DD011_T1_fit_gauge_double_2dots.stl` | 46 × 46 × 24.4 | 1 |
| Cap | `DD011_B_cap_x2.stl` | 46 × 46 × 16.9 | 1 |
| Detent ring 0.20 mm, 1 dot | `DD011_T2_detent_tuning_softer_1dot.stl` | 46 × 46 × 9.4 | 1 |
| Detent ring 0.40 mm, 3 dots | `DD011_T2_detent_tuning_firmer_3dots.stl` | 46 × 46 × 9.4 | 1 |
| Window | `DD011_C_window_x2_clear.stl` | 18 × 17.6 × 2.6 | 1 |
| 55 mm adapter | `DD011_D_adapter_55mm_x2.stl` | 51.6 × 50.8 × 3.6 | 1 |

**3MF limitations (honest):**

- It is a plain 3MF written by build123d/lib3mf, **not a Bambu Studio project**. It carries
  geometry and display colours, but no printer, filament or process settings.
- On opening, choose the H2C and PETG profiles. Assign filaments per object: charcoal for the
  gauge, rings and cap; clear for the window; orange for the adapter.
- The objects are laid out around the model origin, not centred on the H2C plate. Press
  **Arrange (A)** after import.
- If you only have one filament loaded, print the window and adapter later. Or print them in
  charcoal for the fit test: colour doesn't matter for fit, but the window must be clear to
  test readability.

## 5. Estimated filament and time

These are estimated from the solid volume of each part (PETG 1.27 g/cm³). **They are not
slicer output.** Slice for real numbers and record them below.

| Plate | Contents | Est. filament | Est. time |
|---|---|---|---|
| **Fit test (plate 4)** | gauge + cap + 2 tuning rings + window + adapter | **≈ 32 g** (charcoal 30 g, clear 0.4 g, orange 1.6 g) | **≈ 1.5–1.8 h** |
| Plate 1 | body + 2 caps | ≈ 37 g charcoal | ≈ 1.5–2 h |
| Plate 2 | 2 × 55 mm adapters | ≈ 3.2 g orange | ≈ 15 min |
| Plate 3 | 2 windows | ≈ 0.8 g clear | ≈ 10 min |
| Plate 5 | adapter set, 6 sizes | ≈ 10 g orange | ≈ 45 min |

A full cartridge (plates 1–3) is ≈ 41 g and ≈ 2–2.5 h. The silica gel is extra: 38–44 g of
2–5 mm beads.

## 6. Validation log (fill in)

| Setting | Recommended | Used on first print | Validated? (Y/N, date) | Notes |
|---|---|---|---|---|
| Nozzle | 0.4 mm | | | |
| Layer height | 0.20 | | | |
| Walls | 4 | | | |
| Nozzle / bed °C | 250 / 70 | | | |
| Elephant foot | 0.15 | | | |
| Slicer filament for fit plate (g) | ≈ 32 est. | | | |
| Slicer time for fit plate | ≈ 1.5–1.8 h est. | | | |
