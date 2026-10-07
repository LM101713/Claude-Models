# Sourced bill of materials for the 50-engine run (2026-10-07)

Research only: nothing was ordered. Every line says whether its price was
VERIFIED on a live product page today or ASSUMED from a search result. USD,
US vendors, buyer's country not confirmed.

## Cost per engine, all in

| | x1 pricing | x50 pricing | Source |
|---|---|---|---|
| Printed parts: 3.05 kg ASA | $91 (Bambu $29.99/kg) | $65 (Polymaker $21.24/kg at 10+) | filament VERIFIED today; mass from the CAD slice in BOM.md, the Blender exterior is not sliced yet |
| Machined parts (crankpins, shafts, rails, spacers) | $333 | $70 | BOM.md section 2, quotes ASSUMED, not re-checked today |
| Purchased hardware and electronics (31 lines) | $163 | $133 | tables below; 15 lines VERIFIED, 18 ASSUMED |
| **Materials per engine** | **$587** | **$268** | |
| **50 engines, materials** | | **about $13,400** (plus ~5 % spares, ~$14,000) | |
| Printers, 8 x Bambu H2S at $1,499 | | $12,000 one-off | VERIFIED today, base price without AMS |
| Printer time at 127 h per engine | | not costed (own machines) | |

Fastener count per engine today: 84 M3 x 8 screws, 74 inserts, 44 magnets
(BOM.md). `docs/ASSEMBLY_SIMPLIFICATION.md` takes that to 56 / 46 / 40.

## What to act on first

1. **Pololu D24V22F5 5 V regulator (E3)** is single-source and rationed today. Either pre-order 52 now or drop it for a $2-3 12 V to 5 V buck module from the electronics distributor. Recommended: drop it.
2. **Stepper 17HS4401S (E11)** is no longer listed at StepperOnline. Substitute 17HS15-1504S1 ($9.13, 1 mm shorter, same flange and 5 mm D shaft to confirm) or a generic "17HS4401" from Amazon/AliExpress.
3. **Mean Well GST25A12-P1J (E6)** has a C14 inlet, not C7, and the cord is sold separately ($3). Fix the BOM note or switch to the GST25E12 (C8 inlet).
4. **VC-3 threadlocker (H12)** is $32 a bottle, not $12. Four bottles cover the run.
5. **Polymaker ASA black** was sold out today; Bambu ASA is in stock at $29.99.
6. Fasteners from AliExpress (dowels, inserts, screws) save about $21 per engine but add 3-5 weeks; decide by the deadline.

## Line-by-line sourcing (worker research, 2026-10-07; nothing ordered)

Checked 2026-10-07. Prices USD unless stated. Buyer country not confirmed; US vendors/US shipping assumed. "VERIFIED" = read from a live product page fetched today. "ASSUMED" = search snippet, aggregator, or page would not load; treat as an estimate. Quantities in "Order for 50" come from BOM.md.

Vendors that blocked or would not render today: DigiKey (product pages return header only), Mouser (404 / timeout on 2 of 3 URLs), Amazon (robots.txt), Bolt Depot and Apex Magnets (404 on the URLs found), McMaster-Carr (not attempted; no fetchable product URL in search results).

## 1. Hardware (H1-H14)

| ID | Part / listing | Vendor + URL | Qty 1 | Qty for 50 (order qty) | Stock / lead | Status | Single-source? / alternative |
|---|---|---|---|---|---|---|---|
| H1 | NTN 608ZZC3/L627 radial ball bearing 8x22x7 double-shielded | Zoro https://www.zoro.com/i/G3333337/ | $12.49 ea | no break listed (105 pcs) | "ships in 1 day" class, item stock not shown | VERIFIED (but branded/overpriced) | Not single-source. Use generic 608ZZ 20-packs (Amazon/eBay/AliExpress, typically $8-12 per 20, ASSUMED ~$0.45 ea); cheapest route is a 100-pack from AliExpress. |
| H2 | 686ZZ 6x13x5 shielded, 10-pack | eBay listing seen in search https://www.ebay.de/itm/336266846714 (EU seller); US alt Motion https://www.motion.com/products/sku/00144583 | ASSUMED ~$0.70 ea (10-pk) | ASSUMED ~$0.40 ea at 420 pcs (AliExpress 100-pk) | unknown | ASSUMED | Generic, many makers. Amazon/AliExpress 686ZZ 10/50/100 packs. |
| H3 | Oil-impregnated bronze bushing 3x5x4 mm, 20-pack (Bambu Makers Supply ED002) | Bambu Lab US store https://us.store.bambulab.com/products/oil-impregnated-bronze-bushings | "From $1.78" per 20-pk = ~$0.09 ea | no break listed; 1320 pcs = 66 packs = ~$117 | page shows no stock flag | VERIFIED (price shown as "from") | Not single-source (eBay "self-lubricating bronze sleeve all sizes" https://www.ebay.com/itm/397332210974; AliExpress). Bambu is the easy US bundle with filament. |
| H4 | Dowel pin 3 mm x 20 mm stainless (A4), 10-pack, Zoro Select | Zoro https://www.zoro.com/i/G3411707/ | $5.39 / 10 = $0.54 ea | no break listed; 440 pcs = 44 packs = $237 | "ships in 1 day" class | VERIFIED | Not single-source. RS PRO 270-568 (RS), AliExpress 3x20 304 dowel 100-pk (ASSUMED ~$0.06-0.10 ea) is 5-8x cheaper at this volume. |
| H5 | RS PRO M3 brass heat-set insert, 4.6 mm OD, 5.7 mm long, 100-pack (RS 204-0616) | RS Ireland page https://ie.rs-online.com/web/p/products/2040616 (check us.rs-online.com for USD) | EUR 18.72 / 100 ex VAT = ~$0.20 ea | no break listed; 4070 pcs = 41 packs | In stock (8 + 1,482 units) | VERIFIED (EUR, Ireland page) | Generic part (same as ruthex / CNC Kitchen style, many makers). Amazon "ruthex M3 x 5.7 100-pk" ASSUMED ~$13 = $0.13 ea; AliExpress ASSUMED ~$0.03-0.05 ea at 4000+. |
| H6 | M3 x 0.5 x 8 mm socket head cap screw, 304 SS, pkg of 100 | Global Industrial https://www.globalindustrial.com/p/m3-x-0-5-x-8mm-socket-head-cap-screw-304-stainless-steel-pkg-of-100 | $9.80 / 100 = $0.098 ea | 25+ pkgs $9.10 = $0.091 ea (4620 pcs = 47 pkgs = $428) | Ships in 2 business days | VERIFIED | Commodity. Bolt Depot / McMaster similar; AliExpress 304 M3x8 SHCS 1000-pk ASSUMED ~$0.02 ea. |
| H7 | 6 x 3 mm N52 neodymium disc, 30-pack | Amazon https://www.amazon.com/Magnets-Magnetic-Neodymium-Acoustic-Electronics/dp/B0CD88KWDZ (page blocked to fetch) | ASSUMED ~$7 / 30 = $0.23 ea | ASSUMED ~$0.10 ea in 100-packs (2420 pcs) | unknown | ASSUMED | Commodity. K&J Magnetics (US, inch sizes; 1/4" x 1/8" D41-N52 is a near-equivalent), Apex Magnets, AliExpress 6x3 N52 100-pk. |
| H8 | Phidgets GT2 pulley 60T, 8 mm bore (TRM4105_0) | RobotShop https://www.robotshop.com/products/phidgets-gt2-pulley-w-8mm-bore-60-teeth | $4.34 | no break listed (51 pcs = $221) | In stock | VERIFIED | Generic 60T/8B pulleys exist on Amazon/AliExpress at ~$3 (ASSUMED); confirm 6 mm belt width and 2 grub screws. |
| H9 | BEMONOC 2GT 20T 5 mm bore, 6 mm belt | Amazon https://www.amazon.com/BEMONOC-Timing-Pulley-Teeth-Printer/dp/B014ID115W (robots blocked) | ASSUMED ~$2.50 | ASSUMED ~$1.60 ea in 5-packs (B078Z6YZCY) | unknown | ASSUMED | Commodity. RobotShop/Phidgets also sell 20T 5 mm. |
| H10 | GT2 closed belt 210 mm (105T), 6 mm | Amazon / AliExpress generic (no fetchable page; search only) | ASSUMED ~$2.00 | ASSUMED ~$1.20 (55 pcs, 10-packs) | unknown | ASSUMED | Commodity; 200 mm or 220 mm also stocked more widely (BOM says 220 fits the motor slots). |
| H11 | 20 mm round self-adhesive rubber feet, 3-5 mm thick | Amazon generic (not fetched) | ASSUMED ~$0.10 ea (100-pk ~$9) | ASSUMED ~$0.08 (440 pcs) | unknown | ASSUMED | Commodity. |
| H12 | Vibra-TITE VC-3 Threadmate 30 mL (ND Industries 21330) | SkyGeek https://skygeek.com/nd-industries-21330-vibra-tite-threadmate-vc-3-1-oz.html | $32.02 / bottle | 50-99: $31.47 (only 4 bottles needed - no break) | In stock | VERIFIED | Brand-specific (ND Industries) but sold by many distributors (Amazon, SC Fastening, Silmid). BOM assumed $12; real price is ~$32. |
| H13 | Clock / sewing-machine oil (1 bottle) | any (Amazon "Singer sewing machine oil 4 oz" ~ $5-8) | ASSUMED ~$6 | 1 bottle | n/a | ASSUMED | Commodity. |
| H14 | Custom engraved aluminium nameplate 120 x 30 x 0.8 mm, 3M adhesive, numbered 01-50 | Quote-based; US options seen: myassettag.com machine nameplates https://www.myassettag.com/equipment-nameplates/machine-name-plate/sku-np-0002 , pipemarker.com laser-etched aluminium nameplate https://www.pipemarker.com/products/46750/132-thick-laser-etched-aluminum-nameplate | ASSUMED ~$12 (BOM) | ASSUMED ~$5 at 52 pcs (BOM); needs a quote | quote / custom, typically 1-3 weeks | ASSUMED | Single-source per order (custom artwork). Alternatives: Etsy engravers, Alibaba nameplate factories, or print the plate (eliminates the line). |

## 2. Electronics (E1-E17)

| ID | Part / listing | Vendor + URL | Qty 1 | Qty for 50 (order qty) | Stock / lead | Status | Single-source? / alternative |
|---|---|---|---|---|---|---|---|
| E1 | Espressif ESP32-DevKitC-32E | DigiKey https://www.digikey.com/en/products/detail/espressif-systems/ESP32-DEVKITC-32E/12091810 (page would not render); aggregator https://www.digipart.com/part/ESP32-DEVKITC-32E | ASSUMED: Conrad EUR 12.99; Unikey $14.51 @100 | ASSUMED ~$14.51 (52 pcs); DigiKey/Mouser normally ~$10 | Aggregator shows 10k+ at brokers; Mouser listed | ASSUMED | Espressif-made but stocked by DigiKey, Mouser, Adafruit, Amazon. Alternative: any ESP32-WROOM-32E 38-pin clone (~$5) if pinout matches. |
| E2 | BIGTREETECH TMC2209 V1.3 | BIQU (BTT official) https://biqu.equipment/products/bigtreetech-tmc2209-stepper-motor-driver-for-3d-printer-board-vs-tmc2208 | $7.89 (sale from $9.99) | 6-pack $35.51 = $5.92 ea (52 pcs = 9 x 6-pk) | In stock | VERIFIED | BTT is the maker; also on Amazon. Alternative: Fysetc/MKS TMC2209 clones. |
| E3 | Pololu D24V22F5 5 V 2.5 A regulator | Pololu https://www.pololu.com/product/2858 | $18.95 | 5+ $17.43 (52 pcs) | "Rationed", backorders allowed | VERIFIED (price ~2x BOM estimate) | SINGLE-SOURCE and currently rationed. Alternatives: Pololu D24V25F5 / D36V28F5 (same footprint family), or a $1-2 MP1584/LM2596 buck module (set to 5 V) if you accept a trimmer. |
| E4 | TI SN74AHCT125N DIP-14 + socket | Mouser https://www.mouser.com/ProductDetail/595-SN74AHCT125N (timed out); DigiKey https://www.digikey.com/en/products/detail/texas-instruments/SN74AHCT125N/375796 (blocked) | ASSUMED ~$0.70 + $0.15 socket | ASSUMED ~$0.60 (52 pcs) | normally thousands in stock | ASSUMED | TI part, multi-distributor. Alternative: 74HCT125 from Nexperia/Diodes; or drop it by using a 3.3 V-tolerant LED level approach (see suggestions). |
| E5 | TI DRV5033AJQLPG hall switch TO-92 | Mouser https://www.mouser.com/ProductDetail/595-DRV5033AJQLPG | $0.60 | 50+ $0.389 (55 pcs = $21) | 3,385 in stock; factory 12 wk beyond | VERIFIED | TI only, but DigiKey/Mouser/LCSC stock it. Alternative: Allegro A1120/AH3144-style unipolar or any omnipolar TO-92 hall (firmware is polarity-agnostic with omnipolar). |
| E6 | Mean Well GST25A12-P1J 12 V 2.08 A desktop | Jameco https://www.jameco.com/z/GST25A12-P1J-MEAN-WELL-25-Watt-3-Wire-AC-DC-High-Reliability-Industrial-Desktop-Power-Adapter-12-Volts-2080mA-2-1mm-Plug-Level-VI_2257192.html | $14.30 (cord NOT included; Jameco 2271575 cord ~+$3) | 20+ $12.60 (51 pcs); DigiKey https://azcus.digikey.com/en/products/detail/mean-well-usa-inc/GST25A12-P1J/7703648 not fetched | 2 weeks lead time at Jameco | VERIFIED (Jameco) | Mean Well-made, multi-distributor (DigiKey, Mouser, Bravo Electro). Note GST25A uses a C14 inlet (3-wire), not C7: BOM's "C7 cord" is wrong for this SKU; GST25E/GE series are the 2-wire C7/C8 versions. |
| E7 | DC panel jack 5.5x2.1, 11 mm thread, nut | Amazon/AliExpress generic (not fetched) | ASSUMED ~$0.80 (10-pk) | ASSUMED ~$0.50 (52 pcs) | unknown | ASSUMED | Commodity (Kycon/CUI equivalents at DigiKey ~$1.50). |
| E8 | KCD1 round 20 mm illuminated rocker, 3-pin, 12 V | Amazon/AliExpress generic (not fetched) | ASSUMED ~$1.00 | ASSUMED ~$0.70 | unknown | ASSUMED | Commodity. |
| E9 | 16 mm stainless momentary 1NO, 12 V ring LED | Amazon/AliExpress generic (not fetched) | ASSUMED ~$3.50 | ASSUMED ~$2.50 (52 pcs) | unknown | ASSUMED | Commodity (many makers of the same 16 mm "metal button"). |
| E10 | 10 k linear 16 mm pot M7 + 20 mm aluminium knob | Amazon/AliExpress generic (not fetched) | ASSUMED ~$3.50 | ASSUMED ~$2.50 | unknown | ASSUMED | Commodity (Alpha/Bourns at DigiKey ~$1.50 + knob). |
| E11 | StepperOnline 17HS4401S | StepperOnline search https://www.omc-stepperonline.com/search/17HS4401S returns NO such product; closest listed: 17HS15-1504S1 (45 Ncm, 1.5 A, 42x42x39, with 1 m cable) https://www.omc-stepperonline.com/nema-17-bipolar-45ncm-63-74oz-in-1-5a-42x42x39mm-4-wires-w-1m-cable-connector-17hs15-1504s1 | $9.13 (17HS15-1504S1) | no break listed on page (StepperOnline quotes bulk by e-mail); 51 pcs | 17HS4401S: not listed (appears discontinued / renamed); 17HS15-1504S1 available | VERIFIED (substitute) / 17HS4401S NOT FOUND | 17HS4401S is a generic Chinese model number sold under many brands (Amazon, eBay, AliExpress, ~$10-13). Since the driver runs 0.6 A RMS, the 1.5 A 17HS15-1504S1 is an easy drop-in (1 mm shorter). |
| E12 | BTF-LIGHTING WS2812B 60 LED/m black PCB IP30 5 V, 5 m reel | BTF-Lighting direct https://www.btf-lighting.com/products/ws2812b-led-pixel-strip-30-60-74-96-100-144-pixels-leds-m | base variant shown $7.99 (1 m, 30/m, sale); 5 m 60/m black IP30 variant price only shown after selecting (ASSUMED ~$20-24 / 5 m = ~$4.40/m) | 10 reels: "wholesale price available for bulk order, e-mail support" - no break listed | "Stock adequate, ready to ship"; 1 free male JST-SM-style connector per strip | PARTIAL (page VERIFIED, variant price ASSUMED) | BTF is one brand of a commodity strip; Amazon BTF store, AliExpress. |
| E13 | 70 x 90 mm double-sided FR4 protoboard | Amazon/AliExpress generic (not fetched) | ASSUMED ~$0.80 | ASSUMED ~$0.40 | unknown | ASSUMED | Commodity. Alternative: a $2-4/board JLCPCB custom PCB at 50 pcs removes hand-wiring (see suggestions). |
| E14 | JST XH 2.54 kit (headers 2/3/4-pin, housings, pre-crimped leads) | Amazon/AliExpress generic (not fetched) | ASSUMED ~$3.00 / engine-set | ASSUMED ~$2.00 | unknown | ASSUMED | Commodity (JST-brand at DigiKey is ~3x the price of clones). |
| E15 | Small parts set (fuse, diodes, TVS, caps, resistors, 2N3904, headers) | DigiKey/Mouser (blocked today) or AliExpress kit | ASSUMED ~$3.50 | ASSUMED ~$2.00 | normally in stock | ASSUMED | All multi-source jellybean parts. |
| E16 | Silicone wire 20/22/24/26 AWG + 6 mm sleeve + heat-shrink + spades | Amazon generic (not fetched) | ASSUMED ~$3.00 / engine | ASSUMED ~$2.00 | unknown | ASSUMED | Commodity. |
| E17 | 100 mm cable ties x12 | Amazon generic (not fetched) | ASSUMED $0.24 | ASSUMED $0.12 (660 pcs = 1 x 1000-bag ~$6) | unknown | ASSUMED | Commodity. |

## 3. Printers and filament

| Item | Vendor + URL | Price | Bulk / combo | Stock / lead | Status |
|---|---|---|---|---|---|
| Bambu Lab H2S (printer only) | https://us.store.bambulab.com/products/h2s | $1,499.00 | AMS Combo and Laser Full Combo listed but combo prices not rendered on the page (ASSUMED unknown; secondary sources cite a $1,249 launch price, since changed - check store). Add-on bundles "up to 25% off" accessories. | Page text says "ETD: ship around October 08" and "ships from US warehouse in 1-3 business days once processed" | VERIFIED base price; combos ASSUMED |
| Bambu Lab P1S (printer only) | https://us.store.bambulab.com/products/p1s | $799.00 (marked down from $949.00) | P1S Combo (with AMS) listed, price not rendered (ASSUMED unknown) | not stated | VERIFIED base price; combo ASSUMED |
| Bambu ASA 1 kg (with spool) | https://us.store.bambulab.com/products/asa-filament | $29.99 / kg | No multi-pack discount shown; refill price not shown | not stated; free US shipping over $49 | VERIFIED |
| Polymaker ASA 1 kg (shop.polymaker.com) | https://shop.polymaker.com/products/asa (us.polymaker.com redirects here) | $24.99 / kg | Site-wide: buy 4 -5%, buy 6 -10%, buy 10 -15% (= $21.24/kg at 10+); 3 kg and 5 kg sizes listed | Black 1 kg SOLD OUT; other colours available | VERIFIED |

Filament note: BOM.md section 1 puts the engine at 3.05 kg of ASA (165 x 1 kg spools for 50 with purge and reprints); Polymaker at 15% off is ~$3,500 for the order vs Bambu ~$4,950. Polymaker black being sold out today is a schedule risk - order early or pick a second colour.

## 4. Totals (per engine, purchased parts only; US vendors as tabled above)

| | Qty 1 pricing | Qty 50 pricing |
|---|---|---|
| Hardware H1-H14 | $71.57 | $53.46 |
| Electronics E1-E17 | $91.66 | $79.50 |
| **Purchased parts per engine** | **$163.23** | **$132.96** |
| **50 engines (parts only, before spares)** | - | **$6,648** |
| 50 engines incl. the BOM's spare quantities (~+5%) | - | ~$7,000 |

Why this is above the BOM's $89.20: the BOM underestimates four lines that are now verified - Pololu regulator ($18.95 vs $11), VC-3 threadlocker ($32 vs $12 a bottle), stainless dowels from a US stock vendor ($0.54 vs $0.15), and heat-set inserts/screws from US stock vendors ($0.20/$0.09 vs $0.08/$0.06). Mean Well at $12.60 + cord is close to the BOM. Roughly 40% of the electronics total is ASSUMED (generic panel parts, kits, ESP32).

Alternative "AliExpress for fasteners" total: buying H4 dowels (~$0.08), H5 inserts (~$0.05) and H6 screws (~$0.02) from AliExpress at the 50-engine quantities cuts about $21 per engine -> ~$112 per engine, ~$5,600 for 50 (prices ASSUMED, 3-5 week shipping).

## 5. Long lead time / single source

- E3 Pololu D24V22F5: single-source, "Rationed" today, backorders allowed, $18.95. Highest risk line. Pre-order 52 early or qualify a D24V25F5 / D36V28F5 / generic 5 V buck.
- E11 17HS4401S: not listed at StepperOnline any more; substitute 17HS15-1504S1 ($9.13) or buy "17HS4401" generics from Amazon/AliExpress. Confirm the motor flange and shaft (5 mm D) match the CAD before ordering 51.
- E6 Mean Well GST25A12-P1J: 2-week lead at Jameco, cord sold separately, and it is a C14 (3-wire) adapter, not C7. Fix the BOM cord note or switch to GST25E12-P1J (2-wire, C8 inlet) if a C7 figure-8 cord is wanted.
- E5 DRV5033AJQLPG: 3,385 in stock today; factory lead 12 weeks past that. 55 pcs is fine; order in one go.
- H14 edition plate: custom artwork, quote-based, 1-3 weeks typical; the only truly single-source item (per order).
- H12 VC-3: brand-specific, in stock, but $32 a bottle not $12.
- Filament: Polymaker ASA black sold out today.
- Anything from AliExpress: 3-5 weeks, not single-source but adds schedule risk.

## 6. Consolidation suggestions (not applied to the BOM)

1. Three vendor baskets instead of ~12: (a) Bambu Lab US store - printers, ASA filament, AND the H3 bronze bushings (ED002 3x5x4, exactly the BOM size); (b) one hardware vendor for H1/H2/H4/H5/H6/H7/H11/H17-class commodities - Amazon if speed matters, AliExpress if cost matters (Zoro/Global Industrial are fine US fallbacks for dowels and screws; RS for inserts); (c) one electronics distributor (Mouser or DigiKey) for E1, E4, E5, E6, E7, E10 and the whole E15 jellybean set, plus BIQU for E2, Pololu for E3, StepperOnline for E11, BTF for E12.
2. Drop the Pololu D24V22F5 (E3, single-source, rationed, $19) by using a driver/controller board that already includes a 5 V rail: e.g. an ESP32 board with onboard 5 V buck, or a small 12 V -> 5 V 3 A module from the same distributor (~$2-3). Saves ~$16/engine and removes the riskiest line.
3. Replace the 70x90 protoboard + hand wiring (E13, most of E16, the DIP socket) with a small 2-layer PCB from JLCPCB/PCBWay (~$2-4 per board at 50 pcs). It also lets the 7 JST XH headers be the only connector family (keep XH everywhere, including the LED strips - BTF ships a JST-SM pigtail which you then don't need).
4. Pick ONE commodity pulley family: a 20T + 60T 5/8 mm bore "GT2 kit" from one Amazon/AliExpress seller with a 200 or 220 mm belt is cheaper than RobotShop Phidgets ($4.34) + separate belt; BOM already allows 220 mm.
5. Single screw size is already done (M3x8); matching M3x5.7 inserts are fine. Consider swapping the 24 bronze bushings + 8 steel dowels for printed journals if the display-speed loads allow - that removes H3 and H4 (32 parts and ~$6.50 per engine at US prices).
6. 686ZZ (8/engine) and 608ZZ (2/engine) come from the same bearing sellers; order both from one AliExpress/Amazon store in 100/500 packs.
7. Edition plate: laser-engrave a printed or anodised blank in-house, or order all 52 numbered plates in one run from one engraver (ask myassettag/pipemarker for a 50-pc quote) - unit price is driven by setup, so one run beats 50 singles.
8. Power inlet: if you keep the Mean Well GST25A (C14 inlet), buy the C13 cords in the customer's country plug from the same distributor; or switch to the GST25E (C8 inlet, figure-8 C7 cord) so the BOM note is right.

## 7. Verification summary

- Live-page VERIFIED today (price and/or stock read from a fetched product page): H1 (Zoro, not recommended), H3, H4, H5 (EUR page), H6, H8, H12, E2, E3, E5, E6, E11 (substitute part; original not found), H2S base, P1S base, Bambu ASA, Polymaker ASA = 15 lines + 4 printer/filament lines.
- PARTIAL: E12 (BTF page fetched, variant price not displayed).
- ASSUMED (search snippet / aggregator / page blocked): H2, H7, H9, H10, H11, H13, H14, E1, E4, E7, E8, E9, E10, E13, E14, E15, E16, E17 = 18 lines; plus H2S/P1S combo prices.
- Blocked vendors today: DigiKey, Mouser (2 of 3), Amazon (robots.txt), Bolt Depot (404), Apex Magnets (404). About 40 tool calls used.
