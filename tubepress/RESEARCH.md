# TP-01 TUBEPRESS: competitor research and market opportunity

_Research done on 2026-11-08 with web search. **MakerWorld pages could not be opened from the
build environment**, so the details below come from search-result snippets: titles, short
descriptions, and in a few cases download counts or comment excerpts. Snippets disagreed on some
counts. Open the links and check them before relying on any number here._

## Tubes

| Quantity | Value | Source / basis |
|---|---|---|
| Laminate tube diameters | 13.5–50 mm in standard steps (19, 22, 25, 28, 30, 32, 35, 38, 40 …) | Supplier lists |
| Flattened width ≈ π·d/2 | travel ≈ 32–40 mm · standard ≈ 47–55 mm · family ≈ 60 mm | Derived. Real-world evidence: a Printables remix exists because a design was 5 mm too narrow for a US Colgate 4.6 oz tube, and commercial squeezers are rated 51/64/76 mm. |
| Wall (one layer) | 0.20–0.35 mm (ABL 200–250 µm, some 300–350 µm) | DNP, Labelprint24 |
| Crimp seal | about 8 mm wide (one filling-machine spec); thickness not published | NEWECO. Thickness assumed 0.5–1.2 mm: **measure it** |
| Springback | Plastic and laminate tubes have "mechanical memory"; all-HDPE tubes (Colgate "Recycle Me", 2022) are the springiest | Patent US 4733800 and others, trade press |

**Design consequence:** TubePress is sized for **32–65 mm** flattened width (68 mm slot), crimps up
to 1.2 mm (2.2 mm fork gap), and needs a real one-way lock because modern tubes spring back.

## Competitors

### MakerWorld

| Model | Type | What the snippets say |
|---|---|---|
| [2144611 Print-in-place toothpaste squeezer](https://makerworld.com/en/models/2144611-print-in-place-toothpaste-squeezer) | PiP | 322 comments. The top comments say it comes off the plate **locked solid**, and the designer says to work it free. **Fused print-in-place parts are the most common failure in the category.** |
| [2144663 "Starship" PiP ratchet](https://makerworld.com/en/models/2144663) | PiP ratchet | MakerWorld Exclusive |
| [2480576 Toothpaste Squeezer (PiP)](https://makerworld.com/en/models/2480576) | PiP key | About 2.9–3.4k downloads. The creator admits the tube **"partly unwinds"** because there's no ratchet. |
| [2511178](https://makerworld.com/en/models/2511178-toothpaste-squeezer-2-0-print-in-place) / [2577440](https://makerworld.com/en/models/2577440-ratcheted-toothpaste-squeezer-print-in-place) Andrew3d series | PiP ratchet | The designer says the ratchet is "still being refined" |
| [2888749 Ergonomic toothpaste tube squeezer](https://makerworld.com/en/models/2888749-ergonomic-toothpaste-tube-squeezer) | Lever | About 773 likes and 1,920 downloads. **The handle used to snap** and was strengthened; sand the lock if it's too tight. |
| [581827 Tube squeezer roller](https://makerworld.com/en/models/581827-tube-squeezer-toothpaste-roller) | Glued 2-part | Hand slips on the grip, **a handle snapped**, the centre pole is short |
| [1283093 Stronger ratcheting squeezer](https://makerworld.com/en/models/1283093-stronger-ratcheting-toothpaste-tube-squeezer) | Ratchet | **Four separate sizes** for 35–75 mm tubes |
| [1255466 Enhanced squeezer, locking](https://makerworld.com/en/models/1255466-enhanced-toothpaste-squeezer-locking-mechanism) | Key | Wider-slot keys were added **after complaints about a tight fit** |
| [2886342 Slim slider](https://makerworld.com/en/models/2886342) | Slider | 1.5 mm slot, tubes up to 60 mm |
| [1924023 Adjustable](https://makerworld.com/en/models/1924023) | Slider | 58 mm |
| [2920330 Toothpaste saver roller](https://makerworld.com/en/models/2920330-toothpaste-saver-roller) | Wheel + ratchet | Has release buttons |
| [2423006 External gear](https://makerworld.com/en/models/2423006-toothpaste-squeezer-external-gear) | Gear lock | A comment (model not certain) says plain keys "backtrack and the tube falls out" |

### Elsewhere

- Printables: [265248 Ratchet toothpaste tube squeezer](https://www.printables.com/model/265248-ratchet-toothpaste-tube-squeezer) (the most-remixed design), [398914](https://www.printables.com/model/398914-ratcheted-toothpaste-tube-squeezer), [527118, remixed for US Colgate](https://printables.com/model/527118-ratchet-toothpaste-tube-squeezer-remixed-for-us-co), [767485 parametric](https://www.printables.com/model/767485-ratchet-tube-squeezer-modular-parametric) (advises a slot about 8 mm longer than the tube is wide: too snug damages the tube), [186262 NASA squeezer](https://printables.com/model/186262-nasa-toothpaste-squeezer).
- Commercial key and slide squeezers (Amazon reviews via mirrors): they slip on plastic tubes and slide back, the slot is too wide or too tight, and the tube doesn't hold its shape after a metal wringer is removed.
- Patents worth knowing: US 5,642,839 (flexible-tooth one-way disc), US 2,495,464 (pawl on a rack), US 4,576,314 (slotted key with a ratchet).

## Market opportunity

Toothpaste squeezers are a busy, proven MakerWorld category: thousands of downloads per model and
hundreds of comments on the top print-in-place designs. But the comments keep repeating the same
four failures:

1. Print-in-place parts fuse, and the outcome depends on the user's printer.
2. Keys without a real one-way lock unwind.
3. Slots that are too tight or too loose for a given tube, which leads to separate size variants.
4. Handles and wings that snap.

TubePress is aimed squarely at those four:

| Category failure | TubePress |
|---|---|
| PiP parts fused | **Two separately printed parts**: 0.35 mm radial bearing clearance, 0.5 mm knob gap. Nothing is printed together. |
| Unwinds | **24-tooth ratchet** with a pawl that is a leaf spring printed flat into the frame, so it flexes along the layers. Reverse backlash is under 1°. In CAD, the conservative hold torque is 1.7× the estimated tube springback in PETG. |
| Tight or loose slot; separate sizes | **One size takes 32–65 mm tubes.** The only printer-sensitive dimension, the 1.5 mm wiper slot, ships as three frame variants (1.2 / 1.5 / 2.0). |
| Snapping handles | **No wings:** a Ø34 toothed knob that is also the ratchet wheel |
| Fiddly loading | **Open fork:** pull the tube end through the slot and push the key in. The fork straddles the crimp, so there's no threading through a key slot. To take the tube out, pull the key straight out. |

Whether the open-fork loading and the wiper slot feel better than a closed-slot ratchet key is
the claim most in need of a physical test. See `PHYSICAL_TESTING.md`.

**Name check:** "TubePress" is also the name of a long-running WordPress video plugin. Consider
another listing name (for example "Odd Layer TubeKey") before publishing.
