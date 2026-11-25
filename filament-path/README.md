# Odd Layer Product 001: research, product discovery and engineering specification

**Working name:** FILAMENT PATH (proposed product code FP-01)
**Phase:** research and specification only. **No CAD has been started.** Nothing gets built until the owner approves §14.
**Research date:** 2026-11-24
**Status of every design number in this document:** a specification target. Nothing here has been printed, fitted or measured on a printer.

> **Update 2026-11-25.** The owner approved the narrowed direction (external-only routing; Service Dock rejected). Their refinements are in [`REVISION_01.md`](REVISION_01.md), which supersedes the matching sections below:
>
> - R80 is provisional, with its validation experiments.
> - The shared arcs are identical on every printer.
> - Installation is tool-less.
> - The gauge and jig are gated.
> - Pull-force protocol PF-1.
> - Launch scope is P1S, H2S and H2C.
> - The final MakerWorld presentation.
>
> The measurement list in §13 is replaced by [`MEASUREMENT_GUIDE.md`](MEASUREMENT_GUIDE.md). This report is otherwise unchanged, and stays as the research record, including the limits in §2.2.

---

## Contents

1. [Executive recommendation](#1-executive-recommendation)
2. [Research methodology and sources](#2-research-methodology-and-sources)
3. [Ranked product opportunities](#3-ranked-product-opportunities)
4. [Why the winning product is superior](#4-why-the-winning-product-is-superior)
5. [Competitive product analysis](#5-competitive-product-analysis)
6. [Printer compatibility matrix](#6-printer-compatibility-matrix)
7. [Mechanical architecture](#7-mechanical-architecture)
8. [Detailed engineering specification](#8-detailed-engineering-specification)
9. [Risk assessment](#9-risk-assessment)
10. [Manufacturing and printability assessment](#10-manufacturing-and-printability-assessment)
11. [Physical testing protocol](#11-physical-testing-protocol)
12. [MakerWorld launch strategy](#12-makerworld-launch-strategy)
13. [Owner measurements and photographs still required](#13-owner-measurements-and-photographs-still-required)
14. [Final approval checklist](#14-final-approval-checklist)

---

## 1. Executive recommendation

**Build FILAMENT PATH, but not the version the brief describes.**

### What survives

The concept survives only as a narrow, specific product: a **fixed-radius, external-only routing system for the AMS-to-printer PTFE tubes**. It has four parts:

- **One shared tube part** that fits every printer: a snap-on arc that sets a minimum bend radius.
- **A small set of machine-specific anchors** that hook onto Bambu's own rear mounting features, with no adhesive and no new screws.
- **Two zero-risk tools:** a radius gauge and a square-cut tube jig.
- **A published, repeatable friction test**, so the product's main claim is a measurement rather than an adjective.

### What is rejected, and why

| Rejected | Reason |
|---|---|
| Generic PTFE clips and chain clips | The category is saturated for P1/X1 and A1. Single searches returned 8–10 near-identical models. MakerWorld gives duplicate uploads no points, and its 2025 boost changes reduce boosts for simple models. |
| Anything inside the chamber or on the toolhead tube | This is exactly where owners report existing printed guides failing: added friction, parts caught between the toolhead and the housing, homing faults. That risk is incompatible with a first product. |
| A large "modular system" with many parts | It adds part count and testing without adding owner value. |
| The "Service Dock" direction (an H2C Vortek hotend dock or tool dock) | It is not rejected forever, but it is not the lead. The audience is small (H2C only), demand evidence is weak (about 10 existing storage models, none with a visible download count, and no complaint threads asking for one), and it does not cover the P1S. |

### Why this version wins

1. **Its pain point has the strongest evidence of any routing problem.**
   - Bambu's own error-code pages blame tube routing for feed resistance: "avoid having the filament tube too long and excessively bent" (HMS 0700-2000-0002-0025).
   - More than 10 owner threads tie AMS feed errors to tube routing.
2. **Bambu publishes tube lengths but no bend radius**, so owners are guessing. Community figures range from about a 40 mm radius to a 250 mm diameter.
3. **The newest machines are underserved:** H2D, H2S, H2C, X2D and P2S. Bambu's own H2 Filament Track Switch wiki tells owners to "download a suitable AMS bracket from MakerWorld".
4. **It covers the widest range of printers** of any option here: the P1S, X1, P2S, X2D and H2 families. The parts are small, quick to print, need no supports and use little material.
5. **It cannot touch anything that moves.** It stays outside the chamber, so toolhead, cable chain, door and lid interference are excluded by design and confirmed by test, rather than managed.

### The honest downside

Routing products have a **lower demonstrated download ceiling** than storage, riser or purge-bin products:

- The best routing clips seen were about 25k downloads (counts not labelled; see §2).
- Risers and purge bins reach about 76k–106k.

**FILAMENT PATH is not the highest-ceiling category on MakerWorld; it is the strongest one for this brand.** Three reasons:

- It wins on differentiation, reliability and compatibility.
- It has very few failure modes.
- It suits a brand whose credibility rests on measured, honest engineering.

If the owner's only goal were maximum downloads at any risk, an **H2-series AMS deck / flipper** (opportunity B) has the higher ceiling. It also has a much larger structural risk and a much heavier testing load. See §3.

### What I need from the owner before CAD

- The measurements and photos in §13, mainly the rear of the P1S, H2S and H2C.
- Decisions on the checklist in §14.

---

## 2. Research methodology and sources

### 2.1 Method

Four research streams ran in parallel:

1. **H-series engineering** (H2S, H2C, H2D, and checks on the X2D and H3C).
2. **P1S / P2S / X1 engineering.**
3. **MakerWorld competitive landscape** and incentive rules.
4. **Owner complaints** (Bambu forum and wiki troubleshooting).

Each stream was told to cite a URL for every fact and to label each one as:

- **VO**: verified official (a Bambu wiki, spec, store or blog page).
- **OR**: owner-reported (forum).
- **UV**: unverified, third-party, or my inference.

### 2.2 Limits that the owner must know about

- **No page could be opened directly.** This cloud environment's network policy blocks direct fetches of bambulab.com, wiki.bambulab.com, forum.bambulab.com, makerworld.com, printables.com and reddit.com. Every fact comes from **search-engine extracts** of those pages. Short quotes are verbatim from those extracts, but I did not read whole pages or threads.
- **Reddit evidence is absent.** The search tool refuses reddit.com, so this report has no Reddit data and no upvote counts. The complaint analysis rests on forum.bambulab.com and the wiki.
- **Download counts are unlabeled and of unknown date.** MakerWorld cards show two or three numbers, and the search extracts do not say which is which. One cross-check fixes the rule: the BLV riser showed "99,588 downloads, 31,058 likes" on a mirror site and "105.9k / 33.7k" on MakerWorld, so the first, larger number is downloads. Every other count is labelled **"V-unlabeled"**, with downloads inferred by that rule, and is an **estimate**. The index date of each page is unknown.
- **"Frequency" of a complaint** means the number of distinct forum threads that surfaced in searches. It is a lower bound, not an incidence rate.
- **Where official sources disagree, both values are kept** (for example P1S height 457 vs 458 mm, and the H2S toolhead tube 580 vs 590 mm). Neither is picked.

To verify every count and number on the live pages, these hosts need to be allowed in this environment's network settings: `makerworld.com`, `wiki.bambulab.com`, `bambulab.com`, `forum.bambulab.com`. The owner can also check the key ones in a browser. §14 includes this as an approval item.

### 2.3 Key sources (selection; full URLs are cited inline throughout)

**Official, wiki.bambulab.com:**

| Page | Path |
|---|---|
| PTFE tube spec and lengths | `/en/filament-acc/acc/ptfe-tube` |
| P1S AMS 2 Pro install | `/en/p1/manual/installing-ams-2-pro-to-p1s` |
| H2D/H2C PTFE replacement | `/en/h2/maintenance/replace-ptfe-tube-on-h2d-printer` |
| H2C FAQ | `/en/h2c/manual/h2c-faq` |
| H2C AMS connection | `/en/h2c/how-to-connect-ams` |
| H2 Filament Track Switch | `/en/general/manual/filament-track-switch-h2` |
| Multi-AMS compatibility | `/en/ams/manual/multi-model-ams-compatibility-guide` |
| Feed-resistance error code | `/en/h2/troubleshooting/hmscode/0700_2000_0002_0025` |
| Assist-motor stall error codes | `/en/h2/troubleshooting/hmscode/0700_2000_0002_0021` |
| PPA/PPS printing guide | `/en/h2/manual/PPA-PPS-printing-guide` |
| H2S FAQ | `/en/h2/manual/h2s-faq` |
| H2D intro | `/en/h2/manual/h2d-intro` |
| P2S FAQ | `/en/p2s/manual/p2s-faq` |
| X2D FAQ | `/en/x2d/manual/x2d-faq` |

**Official, other domains:**

- Spec pages: bambulab.com/en/h2c/specs, /en-us/h2s/tech-specs, /en/h2d/tech-specs, /en/p2s/specs, /en-us/x2d/specs
- Store page: us.store.bambulab.com/products/p1s

**Owner forum threads:** cited per finding in §3 and §5.

**MakerWorld:** model URLs cited in §5.

**MakerWorld incentive rules:**

- makerworld.com/en/boost
- blog.bambulab.com/boosting-what-matters-rewarding-engineering-and-design-effort
- makerworld.com/exclusive-model-policy
- forum thread 172869 ("Why We're Upgrading Our Points System")

### 2.4 What is fact, estimate and hypothesis in this document

| Marker | Meaning |
|---|---|
| **[VO]** | Bambu official source (via search extract) |
| **[OR]** | Owner-reported |
| **[UV]** | Unverified or third-party |
| **[EST]** | My estimate or calculation, with the working shown |
| **[HYP]** | A design hypothesis that the physical tests in §11 must confirm or kill |
| **[MEASURE]** | Unknown. The owner must measure it (§13) |

---

## 3. Ranked product opportunities

### 3.1 Owner complaints that drive the ranking (strongest evidence first)

| # | Problem | Evidence strength | Representative sources |
|---|---|---|---|
| 1 | **Tight bends and long or loose tubes cause feed resistance and AMS errors** | Strong: 10+ threads plus official error-code pages | HMS 0700-2000-0002-0025 [VO]; forum `/t/feed-issues-ptfe-tubing-etc/251458` ("99% of the time, AMS feed errors… are due to routing of the PTFE tubing", X2D) [OR]; `/t/second-ams-2-pro-with-fts-retraction-issue-and-feed-resistance-errors/256200` ("impossibly tight bend right after the AMS") [OR]; `/t/p-1s-and-ams-2-pro-feeding-issues/253629` [OR] |
| 2 | Internal tube rubbing on the glass top lid (P1S, X1, P2S, X2D, H2D) | Strong: about 9 threads | `/t/ptfe-tube-rubbing-the-glass-cover/208725`, `/t/frayed-ptfe-feeder-tube-for-left-nozzle/258199`, `/t/ptfe-from-ams-to-x1-worn-through/87927` [OR] |
| 3 | H2 filament-buffer jams and drag; **the tube pulls the buffer connector** | Strong (H2): about 8 threads | `/t/h2d-filament-buffer-issue-journey/197630` ("pulls the buffer's internal connector toward the front, and that causes it to catch") [OR] |
| 4 | The 4-in-1 adapter shaves filament (H2C, X2D) | Moderate to strong: 4+ threads, one with 35+ replies, plus an official warning | `/t/h2c-issue-with-4-in-1-ptfe-adapter/211708` [OR]; the H2 track-switch wiki ("strongly discouraged… extra resistance") [VO] |
| 5 | Couplers and tubes popping out. Root causes: a non-square cut, the tube not fully seated, or a damaged collet | Moderate: about 8 threads | `/t/filament-pops-out-of-connector-during-load/75464`, `/t/p1s-ams2-install-problems/191448` [OR] |
| 6 | Wear at the AMS end; filament sawing through the tube wall | Moderate: 4 threads | `/t/ams-eating-ptfe-tube/257640` [OR] |
| 7 | AMS on top: vibration, units falling off (H2C), lid access, heat (P1S) | Moderate: about 7 threads | `/t/yikes-printer-shook-the-ams-off-the-top/258760` (37+ replies) [OR] |
| 8 | H2 purge chute clogging, and fumes through the chute | Strong (H2): about 7 threads | `/t/purge-bin-chute-clogging-at-top-opening/218712` [OR] |
| 9 | H2C Vortek nozzle issues | Moderate, but mostly not solvable with a printed part | `/t/frequent-clogging-of-h2c-induction-nozzles/254775` [OR] |
| 10 | **Existing printed guides make things worse** | Moderate: about 5 threads | `/t/ptfe-tube-rubbing-the-glass-cover/208725/14` ("all these PTFE guides can create feeding issues", a guide that "can get stuck between toolhead and printer housing") [OR]; `/t/p1s-ams-must-have-printable-upgrades/148944` (PTFE guides "have been known to cause homing issues") [OR] |

### 3.2 Candidates

| ID | Candidate | What it is |
|---|---|---|
| **A** | **FILAMENT PATH, external fixed-radius routing** | Snap-on arcs that set a minimum bend radius, plus anchors on official rear mounts, a gauge, a cut jig and a published friction test. Works on P1/X1, P2S/X2D and H2 |
| B | H2 AMS Deck | A vibration-damped, anti-walk AMS riser/flipper for the H2D/H2S/H2C, with top-glass access and AMS HT support |
| C | H2 low-friction merge | A printed 2-into-1 merger to replace the 4-in-1 adapter on H2C/H2D/X2D |
| D | Lid-rub fix | A glass spacer, or a guide for the internal tube, to stop it rubbing the top glass |
| E | H2 purge-chute liner, fume flap and quick-empty bin | |
| F | "Service Dock": H2C Vortek hotend dock that mounts on the printer | Desk boxes exist; no printer-mounted one was found |
| G | A1 / A1 mini accessories | The biggest third-party accessory counts seen were here (AMS Lite top mount about 173k, V-unlabeled), but the owner has no A-series printer to test on, so it is listed for completeness |

### 3.3 Scoring

Each criterion is scored 1–5, and 5 is always the favourable end: low competition, low complexity and a low testing burden all score 5. The weighted total counts **download potential twice**, because the owner ranks downloads first.

| Criterion | A Filament Path | B H2 AMS Deck | C H2 Merge | D Lid-rub | E H2 Purge | F Service Dock | G A1 |
|---|---|---|---|---|---|---|---|
| Addressable audience | 5 (every AMS owner on P/X/H) | 3 (H2, AMS on top) | 2 (H2C/H2D/X2D running 3+ AMS) | 5 | 3 (H2) | 1 (H2C only) | 5 |
| Download potential (×2) | 3 → 6 | 4 → 8 | 2 → 4 | 3 → 6 | 4 → 8 | 2 → 4 | 5 → 10 |
| Competition (5 = little) | 3 (high on P1/X1, low on H2/P2S/X2D) | 3 (a modular flipper is announced, forum `/t/260228`) | 4 | 2 | 1 (more than 12 H2 chutes) | 3 | 2 |
| Differentiation possible | 4 (radius rule, official mounts, measured data) | 3 | 5 | 2 | 2 | 3 | 2 |
| Engineering complexity (5 = simple) | 4 | 2 (carries about 10 kg, changes with each filament change) | 2 | 3 | 4 | 4 | 3 |
| Ease of printing | 5 (small parts, no supports) | 2 (wider than one bed; multi-part, heavy) | 3 | 4 | 4 | 4 | 4 |
| Compatibility potential | 5 (three anchor families, about 8 printers) | 3 (H2 frame only) | 2 | 3 | 3 | 1 | 3 |
| Physical testing (5 = easy) | 3 (needs a friction bench) | 2 (load and dynamic tests; an AMS could fall) | 1 (sits in the filament path; long abrasive wear tests) | 2 (inside the chamber, near moving parts) | 4 | 4 | 1 (no A1 to test on) |
| **Weighted total** | **35** | **26** | **23** | **27** | **29** | **24** | **30** |

**Ranking:** A (35) > G (30, but untestable on the owner's fleet) > E (29) > D (27) > B (26) > F (24) > C (23).

**The ranking holds under other weightings.** Counting downloads once, A still leads (32 vs E 25). Even with the download weight tripled, A (38) still leads G (35, which cannot be tested here) and E (33). A lead this stable means the choice does not depend on how the criteria are weighted.

### 3.4 Short verdicts

- **A, chosen.** See §4.
- **G.** Large audience, but the owner cannot test it, and A-series accessories are crowded. Revisit only if the owner gets an A1.
- **E.** Proven demand: H2 chutes and buckets reached about 76k–99k (V-unlabeled). But there are more than 12 H2 chute models, and the gap that remains (a liner or fume flap) is a feature, not a product. **Best follow-up product,** because it is cheap and low-risk.
- **D.** This is the strongest single complaint, but fixes already exist (an anti-glass-grinding mod, chain clips with about 23k–25k, glass risers). Any internal guide sits right where printed guides are reported to snag and cause homing faults. Rejected for product 001.
- **B.** It has the highest ceiling among products the owner can test. Owners keep asking for H2 flippers that also take the AMS HT. Against it:
  - A structural failure drops a loaded AMS.
  - The top is 492 × 514 mm, so the deck needs several plates.
  - Testing is heavy.
  - A competing "modular AMS flipper system" has already been announced.

  **Recommended as product 002** if A ships well. The two products complement each other, because B relies on good tube routing.
- **F, "Service Dock".** Not differentiated enough to be first: weak demand evidence, an H2C-only audience, and no P-series overlap.
- **C.** Most differentiated, but the merge point sits *in* the filament path, so the test burden and wear risk are high. It is folded into A as a *gated* option that adds **no printed surface to the filament path**: the Merge Cradle in §7.

---

## 4. Why the winning product is superior

### 4.1 It solves the problem at the right point

Most existing guides fix the *symptom* by holding the tube somewhere. FILAMENT PATH controls three things.

**1. Total wrap angle (the main friction driver).** Filament tension rises along a bend by the capstan relation:

> T_out = T_in · e^(μ·θ)

where μ is the friction coefficient of the filament against the PTFE and θ is the total wrap angle in radians.

- **The radius does not appear in this term.** Every unnecessary turn costs friction, however gentle it is.
- Example at an *assumed* μ = 0.2 [UV; to be measured, §11.3]:
  - each 90° turn multiplies tension by e^(0.2·π/2) ≈ **1.37**;
  - an avoidable loop (360°) multiplies it by about **3.5** [EST].
- **Design rule:** route with the *fewest total degrees of turn*, not just with "gentle" bends.

**2. Minimum radius (the stiffness and breakage driver).** A 1.75 mm filament bent to radius R sees a surface strain of ε = 0.875 / R.

| Radius R | Surface strain ε |
|---|---|
| 40 mm | 2.2 % |
| 50 mm | 1.75 % |
| 60 mm | 1.46 % |
| **80 mm** | **1.09 %** |
| 100 mm | 0.88 % |

Smaller radii also raise the bending moment the filament carries (M = EI/R), and the tube walls must supply that moment as contact force at the arc entry and exit. For PLA, with E ≈ 3.5 GPa [UV, typical datasheet value] and I = πd⁴/64 = 0.46 mm⁴, the moment at R80 is about 20 N·mm [EST]. This matters most for brittle fibre-filled filaments. For PPA-CF and PPS-CF, Bambu itself says not to bend the tube at the chamber edge and to route it in a spiral [VO]. **A target R of 80 mm keeps strain near 1.1 %**, below the roughly 1.5 % elastic range typical of PLA [UV]. See §8.2.

**3. Tube movement and coupler side-load.**

- **Loose tubes move.** Tubes "hanging in free air move and bind" [OR, /t/251458]. A tube that moves changes its wrap angle from print to print, which makes feeding inconsistent.
- **Side-load reaches the couplers.** A tube that pulls sideways on a coupler loads the collet; on the H2D it was reported to drag the buffer's internal connector [OR, /t/197630].
- **Design rule:** FILAMENT PATH holds every tube straight and on-axis into each coupler for at least 30 mm.

### 4.2 It avoids every failure mode owners report for existing guides

| Failure owners report for existing guides | Why FILAMENT PATH cannot do it |
|---|---|
| "caused more friction while loading" | Nothing clamps the tube and the bore is never reduced (§8.3). The product ships with a test that proves it, or it does not ship |
| "can get stuck between toolhead and printer housing" | No part goes inside the chamber or near the toolhead |
| PTFE guides "cause homing issues" | Same: nothing is near the motion system |
| Clips that rely on friction or adhesive, and come loose | Anchors hook onto Bambu's own rear mounting features; tube clips hold mechanically (§8.3–8.4) |
| Hard-mounted splitters that "constrain the path" | The Merge Cradle floats and aligns the tubes; it does not clamp the adapter |

### 4.3 It is differentiated in ways a thumbnail can show

- **The number "R80"** on the part, the thumbnail and the gauge. No competitor states a radius as a product spec, and nobody publishes a radius rule.
- **Before-and-after pull-force data** from a test any owner can repeat with a kitchen scale. This is unique in the category, and it rewards engineering effort, which the 2025 boost rules favour.
- **One listing covers about 8 printers** with machine-specific anchors. Most competing guides target one printer, so the downloads for this one would add up across all of them on one page.
- **Two useful extras** give more owners a reason to download: a radius gauge to check your current routing, and a square-cut jig that fixes the main root cause of tubes popping out.

### 4.4 Challenging my own choice

- *"It's just a curved clip."* The shared arc is simple on purpose. Four things set it apart: the radius rule, the wrap-angle routing plan per printer, the coupler strain relief and the published data. The anchors and the routing layouts for each machine are where the engineering lives. **If testing shows FILAMENT PATH routing gives no measurable friction improvement over stock routing on any of the three printers, the product should not launch as a performance product.** It could still launch honestly as "tidy, safe routing", with a much lower ceiling. That kill criterion is written into §11.10.
- *"Owners don't feel this problem until it fails."* That is true, and it is why the thumbnail must show the kink (§12).
- *"Risers download more."* Also true; see opportunity B as product 002.

---

## 5. Competitive product analysis

All counts are from search extracts, of unknown date, and V-unlabeled unless marked **V** (see §2.2).

### 5.1 Direct competitors: PTFE routing

| Model | URL | Counts | Printers | Weakness / opening |
|---|---|---|---|---|
| Better PTFE Chain Clips | URL not captured | 25.7k / 5.3k (one snapshot), 16.4k / 3.6k (another) | P1, X1 | Internal; clips onto the cable chain. Does nothing for the external path |
| Cable Chain PTFE Clip for X1/P1P/P1S | not captured | 23k / 4.7k | X1, P1 | Same |
| PTFE Tube Clip (3DTechBase) | makerworld.com/en/models/837672 | 2.9k / 2k | X1, P1, P2 | Generic |
| Hotend/Toolhead PTFE Guide v2 (K2_Kevin) | /models/152636 | not obtained | X1, P1 | Internal. This is the type owners report snagging |
| X1C/P1S/P2S/X2D Anti-Glass Grinding Mod | /models/2288882 | not obtained | X1, P1, P2S, X2D | Internal; its own listing warns the tube still touches the glass if it enters from the wrong side |
| AMS Inside PTFE Guide | /models/43132 | not obtained | AMS | Inside the AMS |
| Bend guide using about a 40 mm radius | /models/562461 | not obtained | — | The closest concept to ours. **R40 gives about 2.2 % filament strain**, twice ours (§4.1) |
| H2D PTFE tube guide; AMS 2 Pro guides; H2D lower spool guide; H2D TPU bypass | /models/1306959, 1935440, 1271301, 1468225, 1462569 | not obtained | H2D, AMS 2 Pro | **Sparse** for H2 |
| H3C PTFE Tube Guide | /models/3579864 | not obtained | H3C | Shows creators move quickly onto new printers |

**Saturation.** One search returned 8–10 near-identical P1/X1 toolhead or AMS guides, and another returned 10 distinct A1 guides. H2, P2S and X2D external routing is sparse, and none of those models had a visible count.

**Official pull.** Bambu's H2 Filament Track Switch wiki tells owners to "download a suitable AMS bracket from MakerWorld" and to keep AMS → switch at 700 mm or less [VO]. Bambu is sending its own customers to MakerWorld for exactly this kind of part.

### 5.2 Adjacent categories (they set the ceiling and the audience)

| Model | Counts | Notes |
|---|---|---|
| BLV AMS/AMS 2 Riser (benlevi) /models/19535 | **V:** 99,588 downloads / 31,058 likes (mirror); 105.9k / 33.7k | Category leader. Bambu's US store sells it as a kit. The licence was later restricted |
| AMS Flipper (Jakob_K_Design) /models/1363398 | 73k–83k | 54 print files. Other creators have built many add-ons for it |
| AMS Riser V2 (maCyo42) /models/133452 | 39.5k–46.7k | Remix of BLV |
| T-pose dual AMS riser, H2D/H2S/H2C /models/1281134 | 3.1k / 2.1k, 755 comments | H2 risers have low counts so far |
| Quick Release Poop Bucket (Wölhart) /models/2501893 | 86.5k–99.4k | P2S, X2D, H2. **Proves the H2/P2S/X2D audience can produce about 100k for a widely useful part** |
| H2D/H2S/H2C Poop Chute (CUBEIFY) /models/1265042 | 71k–76k | H2 |
| Bambu official: Scraper Grip, Bed Scraper, Spool | about 268.5k, 225.1k, 151k | First-party models set the ceiling |
| A1 AMS Lite Top Mount | 173.4k / 36.6k | The largest third-party accessory count seen |

### 5.3 What the competition tells us

1. **No competitor puts its radius, wrap angle or friction numbers in its listing.** A data-backed listing would be the first of its kind in this category.
2. **H2, P2S and X2D external routing is under-supplied,** and Bambu's own wiki sends owners looking for it.
3. **Risers and flippers attract follow-on add-ons from other creators.** FILAMENT PATH anchors could later get *compatible remix* adapters for BLV/Flipper risers, credited correctly, which reaches those communities. That is phase 2, and only where licences allow.
4. **MakerWorld rules punish near-clones.** Duplicates earn no points, models mislabelled as Original instead of Remix are taken down, and the 2025 boost rules reward complexity and quality [VO, from extracts]. One clearly original, multi-printer, data-backed listing fits those rules.

---

## 6. Printer compatibility matrix

Status key:

- **V**: verified from an official Bambu source (via search extract).
- **OR**: owner-reported.
- **C**: official sources conflict.
- **E**: estimated or derived.
- **M**: must be physically measured.
- **—**: not applicable or not researched.

Owner fleet printers are in **bold**.

### 6.1 Body and environment

| Item | **P1S** | X1C / X1E | P2S | X2D | **H2S** | **H2C** | H2D |
|---|---|---|---|---|---|---|---|
| Body W×D×H (mm) | 389×389×457 **or** 458 (C) | 389×389×457 (V) | 392×406×478 (V) | 392×406×478 (V) | 492×514×626 (V) | 492×514×626 (V) | 492×514×626 (V) |
| Weight | 12.95 kg (spec) vs about 12.59 (unboxing) (C) | 14.13 / 16 kg (V) | 14.9 kg (V) | 16.25 kg (V) | 30 kg (V) | 32.5 kg (V) | 31 kg (V) |
| Chamber heating | None; passive. About 50 °C with a 100 °C bed (OR) | X1E active to 60 °C (V) | None; "50 °C chamber" marketing (V) | 65 °C (one page says 60) (C) | Active, 65 °C max (V) | Active, 65 °C max (V) | Active, 65 °C max (V) |
| Recommended space | 500×500×950 mm (V) | — | — | — | 800×1020×1050 mm; keep 10 cm or more from the wall (V) | 600 W × 1020 D (door open) × 1100 H (1 AMS on top) (V) | 700×700×1100 mm (V) |
| Shell shared with | X1C/X1E: glass lid and door shared (V); rear panel **not** (OR) | P1S | X2D top glass is compatible (V); **not** P1S (V) | P2S | Same frame as H2D/H2C (V) | H2D frame (V/UV) | H2S/H2C |

### 6.2 Filament path (the interfaces FILAMENT PATH touches)

| Item | **P1S** | X1C / X1E | P2S | X2D | **H2S** | **H2C** | H2D |
|---|---|---|---|---|---|---|---|
| PTFE tube | 4.0 OD / 2.5 ID (V) | same (V) | same (V) | same (V) | same (V) | same (V) | same (V) |
| Couplers | Push-fit "pneumatic connectors", all one spec (V); PC4-M6 sold (V) | same | same | same | same; buffer thread M6 or M10 not found (M) | same (M) | same (M) |
| Printer inlet location | Coupler "at the upper-right corner on the back" (V); buffer "in the middle area on the back" (V); exact position (M) | Same documents as P1 (V); position (M) | New buffer snaps into a rear-panel hole; separate rear PTFE tube bracket (V); position (M) | Own buffer and own track switch (V); position (M) | Single path; buffer location described as "top cover" in one extract and "back" in another (C) (M) | **2-inlet** buffer on the back: upper channel → right (Vortek) hotend, lower → left (V); position (M) | 2-inlet buffer: upper → right, lower → left (V) |
| AMS → buffer tube | 550 mm (V) | 550 mm (V) | 600 mm (V) | AMS → switch 700, switch → buffer 115 (V) | 525 / 375 listed, ambiguous (C) | 900 mm, "recommended no less than 600" (V) | 900 mm (V) |
| Buffer → coupler / toolhead | Buffer → coupler 370 (V); toolhead tube 550 (table) vs 530 (maintenance page) (C) | 370 / 550 (V) | Buffer → toolhead 555; buffer → coupler 370 (V) | — | 590 vs 580 (C) | 610 left (white) / 590 right (grey) (V) | 610 / 590 (V) |
| Multi-AMS | AMS Hub replaces the buffer (combo ships with the Hub) (V); 4-in-1 between AMS and buffer, never reversed (V); longest tube within 3.5 m (V) | same | 4-in-1 listed for P2S (V) | Track switch (V) | 2 AMS need the 4-in-1 (V) | Up to 4 AMS 2 Pro + 8 AMS HT (V); "4-in-1 PTFE adapter II (black)", not X2D-compatible (V); 4-in-1 with only 2 AMS "strongly discouraged" (V) | 2 AMS connect directly to the 2 inlets (V) |
| Official AMS placement | "Put the AMS on top of the P1S body" (V) | same | — | — | Beside: width becomes 1100 mm (V) | Top or left; recommended: 2× AMS 2 Pro → right, AMS HT → left (V) | Top, on the glass cover plate (V) |
| Rear spool holder | 2 screws on the back (V); pitch (M) | same (V) | — | — | Upper and lower rear mounts, slide-down install, 2× M3×12 base (V); geometry (M) | same (V) (M) | same (V) |

### 6.3 Keep-out and clearance (FILAMENT PATH must stay out of all of these)

| Item | **P1S** | **H2S / H2C** (and H2D) | Status |
|---|---|---|---|
| Toolhead motion | CoreXY (UV here); cable chain to the toolhead (V) | CoreXY, two belts (V); cable chain carries the toolhead cable and the toolhead PTFE tube (V) | **FILAMENT PATH has no part inside the chamber, so nothing can reach the toolhead or cable chain** |
| Cutter | In the toolhead (V) | H2D/H2C: left and right cutter stoppers in the chamber (V); H2S: right (V) | Inside the chamber: never |
| Purge chute | Rectangular opening at the back (V); left or right not confirmed (M) | Rectangular opening at the back (V) | **Keep-out**: rear opening plus a catch zone below it |
| Exhaust | Chamber fan behind the rear panel, aligned with the vent holes (V); bounds (M) | Rear exhaust fan (V); automatic top-front vent (V) | **Keep-out**: rear grille, top-front vent |
| Top glass | Lifts off; supports the AMS (V); can slip (V) | Glass cover plate is the top; AMS sits on it (V); opening is detected (V); one unconfirmed extract says it must come off above 80 °C bed (UV) | **Never touched.** Top-glass removal must stay unobstructed |
| Front door | Glass, hinged; hinge side not confirmed (left implied by a forum title) (M) | Glass, hinged, magnetic closure (V); hinge side (M); about 506 mm front swing (E, derived) | Front of the printer: FILAMENT PATH has no parts there |
| Maintenance | Buffer: 2× M3 screws (V); rear panel needs the buffer off first (V) | Rear panel removal; buffer: rear couplers + 4× BT3×8 screws (V); purge chute from the rear (V); TH board needs the buffer out (V) | Anchors must come off by hand in under 10 s, and must not cover any screw, window or coupler collar |
| Other rear items | — | Safety-key socket on the back (V); 2 spare 4-pin ports (V); laser air pipe (V); e-stop position, lower right (OR) | Keep-out |

### 6.4 Compatibility conclusion

- **The shared arcs, gauge and cut jig fit any 4 mm OD PTFE tube.** They work on every printer above, and on A1 and AMS lite setups.
- **Anchors need three families:**
  - **P1/X1** (P1S, X1C, X1E): one design is likely. The documents are shared, but the rear panels differ (OR) [M].
  - **P2S/X2D:** shared top glass and the same body size are promising, but the rear arrangements are new and the owner has neither printer. **Not in the launch scope** unless someone measures one.
  - **H2** (H2S, H2C, H2D): one frame, and the rear mounts are documented [M].
- **Launch scope:** shared parts, plus P1/X1 anchors, plus H2 anchors. Test on the P1S, H2S and H2C. Listing wording: X1C/X1E "designed for, not tested"; P2S/X2D "shared parts only".

---

## 7. Mechanical architecture

### 7.1 Design rules (every part must obey these)

| # | Rule | Why |
|---|---|---|
| R1 | **Nothing goes inside the chamber, on the toolhead tube, on the glass lid, or on the door.** | Removes every motion, lid and door interference risk by design (§4.2) |
| R2 | **Centreline bend radius is at least 80 mm (target). A "Compact" R60 variant is allowed where the space measured in §13 forces it. Never below R50.** | Filament strain of 1.1 % at R80, 1.46 % at R60 and 1.75 % at R50 (§4.1, §8.2) |
| R3 | **Minimise total wrap angle.** Each printer layout is planned to the fewest degrees of turn between the AMS outlet and the printer inlet. | Capstan friction depends on angle, not radius (§4.1) |
| R4 | **The last 30 mm or more before any coupler is straight and within 2° of the coupler axis.** | Removes side-load on the collet. Owners report the tube dragging the H2D buffer connector |
| R5 | **The tube is never clamped.** It slides freely in its channel, and the bore is never smaller than the tube. | No reduction of the 2.5 mm bore, and no added friction |
| R6 | **Use Bambu's official tube lengths.** No cutting is required for installation; the only optional cuts are listed, within Bambu's limits (H2: AMS → buffer at least 600 mm). | Stays within official guidance, and keeps owner support claims valid |
| R7 | **Mount only on Bambu's own features** (rear spool-holder mounts, existing bracket geometry). No adhesive, no new screws, no drilling. Removal is by hand in under 10 s. | Reversible, warranty-friendly, and quick to remove when troubleshooting |
| R8 | **Never cover a coupler collar, buffer window, screw head, vent, purge opening, safety key, port or e-stop.** Coupler collars keep at least 6 mm radial clearance for a fingertip. | Maintenance access (§6.3) |
| R9 | **No printed surface touches the filament.** The filament only ever touches PTFE or Bambu's own parts. | Printed layer lines would wear and add friction. This is why module C is reduced to a cradle |

### 7.2 Modules

| Module | Code | Shared or specific | Purpose | Launch? |
|---|---|---|---|---|
| Arc 90 | FP-A90 | **Shared** | Snap-on 90° former, R80 centreline | Yes |
| Arc 45 | FP-A45 | **Shared** | 45° former for smaller direction changes | Yes |
| Arc 90 Compact | FP-A90C | **Shared** | R60 for tight spaces; only if §13 shows it is needed | Conditional |
| Lead-in | FP-L30 | **Shared** | 30 mm straight channel that sets R4 coaxiality; part of the anchors, also printable on its own | Yes |
| Anchor P1/X1 | FP-AN-P1 | P1S / X1C / X1E | Holds the arcs and lead-ins to the rear spool-holder base or coupler bracket (choice after §13) | Yes |
| Anchor H2 | FP-AN-H2 | H2S / H2C / H2D | Slides into the official upper or lower rear mount slot; passes the spool-holder function through, or sits beside it (after §13) | Yes |
| Merge Cradle | FP-MC | H2C / H2D (+ X2D later) | **Floating** holder for Bambu's own 4-in-1 adapter or track switch. Lead-ins line each inbound tube up with its port. No hard clamp | **Gated on test data** (§11.8) |
| Radius Gauge | FP-G | Universal | Card with R40/50/60/80/100 arcs and a 4 mm tube go/no-go slot, used to check existing routing | Yes |
| Square-Cut Jig | FP-CUT | Universal | Guides the owner's own razor or utility blade square across a 4 mm tube | Yes |
| Anchor P2S/X2D | FP-AN-P2 | P2S / X2D | — | Post-launch, only with measurements |

**How the modules connect.**

- Each arc has an **FP-Link** socket at each end and one in the middle.
- Anchors carry FP-Link pegs.
- FP-Link is a printed peg-and-socket joint that clicks at **15° steps** (24 positions), so the owner can set the angle in place. The X2D track-switch wiki asks owners to "adjust the angle of the tube guide holder to ensure the tube has no sharp bends" [VO], and FP-Link does that without tools.
- An arc can also **float** on the tube with no anchor, held in place along the tube by a light locating pinch (§8.3).

### 7.3 Typical configurations (to be confirmed once §13 is measured)

| Printer setup | Parts | Planned path |
|---|---|---|
| P1S, 1 AMS on top | 1× FP-AN-P1, 1–2× FP-A90 or FP-A45 | AMS rear outlet → one controlled turn down the back → R4 lead-in into the buffer's left port. **The free 550 mm length is held in one large defined bend instead of a random loop** [HYP: a lower total wrap angle than stock, to be measured] |
| P1S, AMS beside | FP-AN-P1, 1× FP-A90, 1× FP-A45 | Side → rear corner turn → lead-in |
| H2S, 1 AMS on top | FP-AN-H2, 1–2 arcs | Same principle into the single-path buffer |
| H2C, 2× AMS 2 Pro + AMS HT (Bambu's recommended topology) | FP-AN-H2, FP-MC (gated), 3–4 arcs | 2× AMS 2 Pro → cradle with lead-ins → 4-in-1 adapter II → upper inlet (right hotend); AMS HT → arc → lower inlet (left hotend) |
| H2C / H2D, 2 AMS direct (no adapter) | FP-AN-H2, 2–3 arcs | One tube to each inlet. Bambu prefers this to a 4-in-1 with two AMS units [VO] |

**Part count for a typical install:** 2–3 parts (P1S) and 3–6 parts (H2C, multi-AMS).

---

## 8. Detailed engineering specification

All dimensions are **targets for CAD**. They are finalised only after the fit coupon in §8.6 and the measurements in §13. Units are millimetres.

### 8.1 The tube being held

| Parameter | Value | Status |
|---|---|---|
| Tube OD | 4.0 | [VO] nominal. The owner measures the actual OD at 3 points on 3 tubes (§13) |
| Tube ID | 2.5 | [VO] |
| Wall | 0.75 | [EST] from OD and ID |
| Tube bending stiffness EI | about 5,300 N·mm² | [EST]: E(PTFE) about 0.5 GPa [UV typical]; I = π/64·(4⁴ − 2.5⁴) = 10.65 mm⁴ |
| Spring-back moment at R80 | about 67 N·mm | [EST] M = EI/R |

### 8.2 Bend radius selection (R2)

| Radius | Filament strain (1.75 mm) | Space a 90° turn needs | Use |
|---|---|---|---|
| R100 | 0.88 % | about 105 mm | Not offered: too much rear depth for most setups [EST] |
| **R80** | **1.09 %** | **about 85 mm** | **Default** |
| R60 | 1.46 % | about 65 mm | Compact, only if needed |
| R50 | 1.75 % | about 55 mm | Absolute floor. Never offered as standard |
| R40 | 2.19 % | about 45 mm | Below our floor. This is where the closest competitor sits |

**Why 80 and not more.** Rear depth is limited:

- Bambu asks for 10 cm or more from the wall on the H2S [VO].
- The P1S reserved space is 500 mm deep against a 389 mm body [VO].
- R80 fits a 90° turn in about 85 mm of depth [EST].

**Why not less.** Below about R60 the strain on PLA approaches its elastic limit of about 1.5 % [UV], and brittle fibre-filled filaments are at risk (Bambu's own PPA/PPS spiral-routing advice) [VO].

**Open check.** Filament already lives on the spool at the core radius. If the measured inner core radius of a Bambu spool (§13) is *above* 80 mm, filament has never been bent tighter than that before, and the R80 choice needs a second look. **[MEASURE]**

### 8.3 Arc channel cross-section (FP-A90, FP-A45, FP-A90C)

The channel **opens upward**, at 90° to the plane of the bend. It is printed flat with the opening facing up.

**Why it opens to the side, not along the bend.** A tube bent into an arc pushes on the **inner** wall at mid-arc and on the **outer** wall near the ends. Both of those walls must therefore be solid, and the snap-in opening goes on the face that carries no bending load.

| Feature | Target | Why |
|---|---|---|
| Bore Ø | **4.20** (coupon 4.10 / 4.20 / 4.30 / 4.40) | 0.2 diametral clearance over a 4.0 tube, so the tube slides freely (R5). FDM holes print undersize by an amount that depends on the slicer and printer, so the value is chosen from the coupon, not assumed |
| Snap opening | **3.40** (coupon 3.2 / 3.4 / 3.6) | 85 % of OD. The 0.6 mm interference is taken up by elastic ovalisation of the PTFE tube and flex of the lips. A wider opening loses retention; a narrower one risks marking the tube |
| Opening entry chamfer | 45°, opening to 5.0 at the top face | Lead-in so the tube snaps in with a thumb press |
| Lip geometry | 45° inward overhang above the bore centre | Prints without support (45° is the overhang limit used across Odd Layer parts) |
| Floor under bore | 1.2 (3 layers at 0.2 + 3 bottom-skin margin) | Stiff floor |
| Side walls | 1.6 (4 perimeters at 0.4) | Solid perimeters only, no infill, for consistent strength |
| Section envelope | **8.0 wide × 6.5 tall** | Compact; about 7 g per R80 90° arc (below) |
| Arc ends | 10 mm straight tangents + a bellmouth flaring to Ø5.0 with a 1.0 radius | No knife edge on the tube where it leaves the arc, which is where fretting would start |
| Locating pinch | One 5 mm zone with the opening at 3.9 | Lets a floating arc hold its position along the tube without squeezing the bore (lips only, never full circumference) [HYP, coupon] |
| Section stress from tube spring-back | about 1.3 MPa | [EST] 67 N·mm × 4 mm / about 200 mm⁴. PETG yield is about 50 MPa [UV typical], so creep at 60–65 °C is not expected; confirmed by test in §11.7 |
| Mass | about 7 g (R80 90°) | [EST] about 38 mm² section × about 145 mm path length × 1.27 g/cm³ |

**Retention targets** (to be measured; §11.5):

- Pull-off at 90° to the channel ≥ 3 N per arc.
- Axial slide force ≤ 0.5 N (the tube moves freely).

### 8.4 Anchors

**Interface: FP-Link.**

- Peg Ø6.0, socket Ø6.3. The 0.15 per side is a print-fit allowance; final value from the coupon.
- 24 detent positions at 15°, made by 3 printed bumps of 0.3 mm height in a ring of notches.
- Snap retention by a split peg with a 0.4 mm lip.
- **[HYP]** Holding torque must exceed the tube spring-back moment (about 67 N·mm, §8.1) by a factor of 3 or more.

**FP-AN-P1 (P1S / X1).**

- **Candidate mounts:** a clip-over collar on the OEM rear spool-holder base, *or* a hook-over on the coupler bracket at the upper-right rear. Both are official features [VO]; positions and dimensions are [MEASURE].
- **Preferred:** the spool-holder base. It is structural, and it does not load the coupler.
- Carries 1 lead-in (R4) aligned to the buffer's left port, and 1–2 FP-Link pegs.
- Must leave the buffer's 2 M3 screws, its 4-pin and 6-pin cables, the coupler collar and the vent holes uncovered (R8).

**FP-AN-H2 (H2S / H2C / H2D).**

- **Candidate mount:** the official upper or lower rear spool-holder mounts ("align them with the upper and lower mounts at the back… slide them down to install") [VO]; slot geometry [MEASURE].
- **Options:**
  - **(a)** a pass-through anchor that takes the slot and gives back an identical slot for the spool holder;
  - **(b)** an anchor that only uses the slot the owner doesn't need. Owners commonly use the lower slot for a purge bucket [OR].
- Carries 2 lead-ins aligned with the upper and lower buffer inlets.
- Must leave the buffer window visible. The window shows whether a tube is seated [VO].

### 8.5 FP-MC Merge Cradle (gated)

- Holds Bambu's own 4-in-1 PTFE adapter II (H2C) **without clamping it**: a 0.5 mm all-round clearance pocket with soft retaining fingers. Owners advise "Don't hard mount" splitters [OR].
- One R4 lead-in per used inbound port, coaxial with that port to within 2°.
- **[HYP]** The H2C shaving complaint comes partly from tubes entering the adapter at an angle, so filament rubs on the internal channel edges. If FILAMENT PATH alignment does not measurably reduce shaving or pull force (§11.8), the cradle is dropped from the launch.
- Dimensions all [MEASURE]: adapter body L/W/H, port spacing and port angles.

### 8.6 Fit coupon (the first print, before any part)

One plate of about 10 minutes, about 4 g, holding:

- the bore ladder 4.10–4.40;
- the opening ladder 3.2–3.6;
- the locating pinch;
- one FP-Link pair at three socket sizes (6.2 / 6.3 / 6.4).

The owner snaps in a stock tube and reports which values pass. This is the same practice HOLDFAST and DRYDOCK use. **Tolerances are taken from this print, not assumed.**

### 8.7 Tools

**FP-G Radius Gauge**

- 2.0 mm thick card, about 110 × 60 mm.
- Concave arcs R40, R50, R60, R80 and R100, each labelled in embossed text 0.6 mm deep.
- A 4.0 go / 4.3 no-go tube slot.
- Prints flat in under 15 minutes.

**FP-CUT Square-Cut Jig**

- A Ø4.25 tube bore with a 0.6 mm blade slot at 90°. Uses the owner's own single-edge razor; **no blade is supplied**.
- A 30 mm length stop.
- Prints in one piece, laid on its side, so the bore axis is horizontal and the blade slot is vertical.
- **Why it matters:** a non-square cut and an unseated tube are the main reported root causes of tubes popping out of couplers [OR]. A square, fully seated cut also keeps the collet teeth biting evenly.

### 8.8 Materials

| Use | Material | Why |
|---|---|---|
| All arcs, lead-ins, anchors (default) | **PETG** (or PETG HF) | Tg about 80 °C [UV typical] against an outside-rear environment that is near ambient, plus whatever the exhaust adds (M). Tough, slightly flexible lips, good fatigue life |
| H2 anchors if rear exhaust air exceeds about 55 °C (§13 measurement) | **ASA** | Higher heat resistance. The H2 runs active chamber heating to 65 °C [VO] |
| Gauge, cut jig | PLA or PETG | No heat or load |
| **Not allowed for arcs or anchors** | PLA | Creeps under the constant tube spring-back at warm temperatures; one riser creator also warns against PLA near AMS 2 Pro drying [OR] |

The orange accent is the bellmouth rings and the "R80" text. It is done by colour swap at a layer: one change on an AMS, which suits the H2C. The functional parts are graphite or black.

### 8.9 Print orientations and settings (all parts support-free)

| Part | Orientation | Settings |
|---|---|---|
| Arcs, lead-ins | Flat, channel opening up | 0.2 mm layers, 4 walls, 100 % solid (thin parts), 0.4 nozzle |
| Anchors | Mount face down. The final orientation is set in CAD so that any slot undercuts are printed as 45° chamfers, not bridges | 0.2 mm layers, 4 walls, 40 % gyroid |
| Gauge | Flat | 0.2 mm layers |
| Cut jig | On its side (bore axis horizontal) | The bore top is a teardrop (45° roof), so no support |

Every printer in the fleet can print every part; no part exceeds about 140 × 140 mm [EST].

### 8.10 Assembly and installation (outline; final steps after CAD)

1. Print the fit coupon and choose the bore, opening and socket values. The values are typed into one parameter file, so all parts update.
2. Unload filament from the AMS slot (or slots) in Bambu Studio or Handy.
3. Snap the anchor onto its official mount (§8.4), by hand.
4. Press the tube into the arc(s) at the planned positions. The tube stays connected to its couplers throughout.
5. Set each arc's FP-Link angle until the gauge confirms no bend is tighter than R80 and each lead-in is straight into its coupler.
6. Reload the filament and run one load/unload cycle per slot.
7. Removal is the reverse: unclip by hand, with no tools.

### 8.11 Expected failure points (design-stage)

| Failure point | Mechanism | Mitigation | Test |
|---|---|---|---|
| Arc lips | Fatigue or cracking after many snap cycles | PETG; 45° lips; coupon-chosen opening | §11.5: 50 snap cycles |
| Tube at arc ends | Fretting wear from vibration (the AMS bounces on the H2C [OR]) | Bellmouth plus a 10 mm tangent | §11.9: inspect after 100 h |
| FP-Link | Detent slips under tube spring-back | Holding torque ≥ 3× the moment | §11.5 |
| Anchors | Slot fit too loose or too tight on the official mounts | Measured geometry (§13) plus a coupon | §11.4 |
| Arcs (heat) | Radius relaxes at 60–65 °C | Low stress (about 1.3 MPa); ASA option | §11.7 |
| Merge cradle | No measurable benefit | Gated; dropped if so | §11.8 |
| Routing plan | Stock tube length doesn't fit the planned path | Optional length chart within Bambu's limits | §11.3 |

---

## 9. Risk assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **No measurable friction benefit over stock routing** | Medium | High (removes the "less resistance" claim) | Kill criterion in §11.10. Launch only with honest claims, or don't launch |
| 2 | Download ceiling lower than riser or bin products | High | Medium | Multi-printer listing, a strong before/after thumbnail, the gauge and jig as extra reasons to download, product 002 = H2 AMS Deck |
| 3 | Market data is stale or mislabelled (search extracts) | Medium | Medium | Verify the key counts on the live pages before final approval (§14) |
| 4 | Owner's routing differs from the official layouts (AMS Hub, a riser, a shelf) | High | Low | Shared parts float on the tube; anchors are optional |
| 5 | Rear mount geometry varies between batches or regions | Low to medium | Medium | Photos from the owner's fleet; a tolerance coupon; adjustable FP-Link |
| 6 | Anchor blocks maintenance | Low | Medium | R7/R8; hand removal in under 10 s; test in §11.4 |
| 7 | Bambu changes tube lengths or the buffer design | Medium | Low | Shared arcs don't depend on them; anchors are small parts that are cheap to revise |
| 8 | Look-alike copies after launch | High | Low to medium | The data, the radius rule and the multi-printer anchors are hard to copy convincingly; the listing is first in the category |
| 9 | A claim overstated in the listing | Low (by process) | High (trust) | Every claim is tied to a §11 result; "designed for, not tested" wording for untested printers |
| 10 | Licence or remix issues if risers are adapted later | Medium | Medium | Only with explicit licence permission and correct Remix labelling |

Products in this category usually fail in ways that make the printer worse: a guide snags the toolhead, a clip adds friction, a riser falls. FILAMENT PATH's rules R1, R5 and R9 remove those failure modes by design, and the residual risk is mostly commercial.

---

## 10. Manufacturing and printability assessment

| Aspect | Assessment |
|---|---|
| Supports | None on any part (§8.9) |
| Bed size | Every part fits under about 140 mm [EST], so it prints on any Bambu printer, A1 mini included |
| Print time | Arc about 12–18 min, anchor about 30–50 min, full P1S kit about 1 h, full H2C kit about 2–3 h [EST; confirmed with sliced profiles after CAD] |
| Material | About 15–25 g PETG for a P1S kit, about 35–60 g for an H2C multi-AMS kit [EST] |
| Multi-colour | Optional orange accent via one colour swap; functional parts single-colour |
| Bambu H2C features | The owner's H2C can print the accent in one job from two nozzles, with no purge tower for the colour if the accent sits on the second nozzle. Not required: every profile must also work single-nozzle |
| Hardware | **None.** No screws, magnets, bearings or adhesive. The razor for FP-CUT is the owner's own |
| Tolerance strategy | One fit coupon sets all critical fits; parameters are global; no tolerance is guessed (§8.6) |
| Print profiles to publish | One per printer family, plus a universal plate: P1/X1, H2 single (H2S), H2 multi-AMS (H2C/H2D), shared parts and tools |
| Generator | The CAD will follow the repository's pattern: one parametric script that checks fits with boolean geometry and exports STEP/STL/3MF (as in DRYDOCK) |

---

## 11. Physical testing protocol

**Nothing is called safe or validated until it passes these tests on the owner's printers.**

The test printers are the **P1S, H2S and H2C**. Every test is logged with date, firmware version, filament, slot and result. Photos are taken before and after.

### 11.0 Baseline first

Before installing anything, record each printer's **stock** routing:

- photos;
- radius-gauge readings at each bend;
- the total wrap angle estimated from photos;
- the HMS error history for the last 30 days, if available.

Every comparison below is against this baseline on the same printer.

### 11.1 Interference: toolhead, chain, door, lid

| Test | Pass |
|---|---|
| Run the full calibration (homing, bed levelling, vibration compensation) with FILAMENT PATH fitted, three times | No new errors; no new noises; the vibration-compensation run completes |
| Full-volume travel: home, then a perimeter of the whole build volume at maximum travel speed, at Z min and Z max | No contact; nothing inside the chamber changes (FILAMENT PATH has no internal parts, so this checks for a design-rule breach) |
| Front door open and close 20× | No contact with any FILAMENT PATH part |
| Top glass lift-off and replace 10×, including with the AMS removed or flipped as the owner normally does | No contact; no change to how the glass seats; on H2C the lid-open sensor behaves normally |
| AMS lid fully open 10× | No contact |

### 11.2 Retention under printer motion

| Test | Pass |
|---|---|
| 2 h print at Ludicrous speed, with AMS units on top (H2C: the setup owners report shaking the AMS off) | No part moves more than 2 mm, rotates, or detaches. Measured against tape marks |
| By hand: tug each tube sideways with about 5 N (use a luggage scale) | Tube stays in its arc |
| Bump each anchor by hand | Stays put |

### 11.3 Friction: the core claim

**Bench method** (repeatable by any owner; shown in the listing):

1. Take a 1 m length of stock tube and route it on a board in the **stock** shape, traced from the §11.0 photos. Do the same in the **FILAMENT PATH** shape.
2. Feed filament through. At the inlet end, hang a fixed back-tension mass of 200 g over a smooth edge.
3. At the outlet, hang a cup and add water until the filament *just* starts to move steadily.
4. Weigh the cup on a kitchen scale (1 g resolution). The tension ratio T_out / T_in is cup mass / 200 g.
5. Repeat 5× per shape, per filament: **PLA Basic, PETG HF, PLA-CF** (brittle reference), and **TPU for AMS** if available.
6. From the results, **estimate μ**: from a straight tube against one measured 90° bend, using the capstan relation in §4.1. That turns the μ = 0.2 assumption into a measurement.

**On-printer method:**

- 50 load/unload cycles per slot used, on each test printer.
- Record any HMS feed-resistance or assist-motor errors (0700-2000-0002-0021, -0022, -0025 and equivalents).

| Metric | Pass |
|---|---|
| Mean pull tension, FILAMENT PATH vs stock | **No worse in any filament** (FILAMENT PATH mean ≤ stock mean, and no FILAMENT PATH run above the stock maximum) |
| Claim threshold | A "less resistance" claim **only if** the mean drops by 10 % or more on at least one test printer, and only that printer's number is quoted |
| Load/unload | 0 errors in 50 cycles per slot |

### 11.4 Maintenance access

| Test | Pass |
|---|---|
| Remove all FILAMENT PATH parts by hand | Under 10 s per anchor; no tools |
| With FILAMENT PATH fitted: press and release every coupler collar; read the H2 buffer window; reach the buffer screws and the rear-panel screws | All possible without removing FILAMENT PATH |
| Purge-chute and exhaust area | Fully unobstructed (photo check) |

### 11.5 Part durability (bench)

| Test | Pass |
|---|---|
| 50 snap-in / snap-out cycles on one arc | No crack; retention still ≥ 3 N |
| Pull-off at 90° to the channel, measured with a luggage scale | ≥ 3 N |
| Axial slide | ≤ 0.5 N, and the tube moves smoothly |
| FP-Link detent with the tube at R80 for 24 h | No angle change (protractor before and after) |

### 11.6 Multi-colour printing

| Test | Pass |
|---|---|
| 4-colour print with 200 or more filament changes (P1S, H2S) | 0 feed errors; same purge result as baseline |
| H2C: print using the right Vortek hotends from both AMS 2 Pro, and the left hotend from the AMS HT, with 200 or more changes | 0 errors |

### 11.7 Heat

| Test | Pass |
|---|---|
| H2C: 4 h at a 65 °C chamber (ABS/ASA profile). Measure the air temperature at each FILAMENT PATH part with a thermometer | Record the temperature. PETG is used only if it stays below about 55 °C; otherwise switch to ASA |
| After the heat run: gauge each arc | Radius unchanged within 2 mm |

### 11.8 Merge Cradle gate (H2C)

| Test | Pass |
|---|---|
| Bench pull test (§11.3) through the 4-in-1 adapter II: random stock tube angles against FILAMENT PATH coaxial lead-ins | Mean tension lower with FILAMENT PATH |
| 100 changes on the H2C through the adapter; inspect the filament for shaving | Less or no shaving compared with baseline |
| **If either fails, the cradle is not launched.** | |

### 11.9 Long-duration reliability

| Test | Pass |
|---|---|
| 100 print-hours per test printer, with FILAMENT PATH fitted | 0 FILAMENT PATH-related errors; no part movement |
| After 100 h: inspect the tube exterior at each arc end, and the filament for marks | No visible wear groove on the tube; no new marks on the filament |

### 11.10 Kill criteria

| Result | Decision |
|---|---|
| Any interference failure in §11.1 | Fix the design, or abandon that anchor |
| Any increase in friction (§11.3) | Do not launch in that configuration |
| No measurable decrease in friction on any printer | Launch only as a "safe, tidy routing" product with no performance claim, or put the product on hold. **The owner decides; I recommend hold-and-redesign once** |

---

## 12. MakerWorld launch strategy

### 12.1 Naming

Search terms owners use, taken from forum language and competing titles: "PTFE tube guide", "AMS tube", "routing", "kink", "feed error", "bend", plus printer model names.

**Recommended title** (short, specific, searchable, with no marketing words):

> **AMS PTFE Tube Guide – Fixed R80 Bends, No Kinks | P1S · X1C · H2S · H2C · H2D**

- **Subtitle / first line:** "FILAMENT PATH by Odd Layer: tested pull-force results inside."
- **Branding:** "Odd Layer" appears once in the description and on the gauge. It is not in the title.
- **Avoid:** "Ultimate", "Pro", "Revolutionary", and "V2" at launch.

### 12.2 Thumbnail (must work at phone size)

- **Split frame, graphite background:**
  - **Left: "STOCK".** The tube with a visible tight kink behind the printer, shown with a thin dimension arrow.
  - **Right: "R80".** The same printer with the tube in the orange-accented arc. One large orange number: "R80".
  - If and only if §11.3 passes, a third line: "−XX % pull force", with the real measured number.
- **No** AI-style glow, lens flares or crowded text. At most 3 words per side.
- **The printer must be recognisable:** the H2C or P1S rear silhouette. The thumbnail shows the printer back, because that is where the problem is.

### 12.3 Main gallery (in order)

1. Thumbnail (before/after).
2. A rear view on the H2C with the multi-AMS layout labelled.
3. The P1S rear view.
4. A close-up of the arc, showing the tube snapping in.
5. The pull-test bench photo with the result chart.
6. The radius gauge being used on stock routing.
7. The fit coupon.
8. The compatibility table as an image.

### 12.4 Compatibility listing (exact wording style)

| Printer | Wording |
|---|---|
| P1S, H2S, H2C | ✅ **Tested** (date, firmware) |
| X1C, X1E, H2D | 🔷 **Designed for**: shares the documented rear routing or frame. Not tested by us |
| P2S, X2D | ⚪ Shared arcs and tools only (no anchor yet) |
| A1 / AMS lite / any 4 mm OD tube | ⚪ Shared arcs and tools work on any 4 mm tube |

### 12.5 Print profiles (one listing, several profiles)

| # | Profile |
|---|---|
| 1 | **Start here: fit coupon** (10 min) |
| 2 | P1S / X1 kit |
| 3 | H2S kit |
| 4 | H2C / H2D multi-AMS kit |
| 5 | Shared arcs only (any printer) |
| 6 | Tools: gauge and cut jig |

**Why one listing.** Downloads, boosts and ratings all add up on one page. MakerWorld's duplicate rules discourage near-identical separate uploads. A single "fits your printer" page is also easier to understand.

**Possible second listing, later:** the Square-Cut Jig on its own, if it stands up as a general tool. Only if it is clearly distinct, to avoid duplicate-model notices.

### 12.6 Description structure

1. **The problem in one line**, with the official error text quoted.
2. **What it does**, in three bullets.
3. **The test result**, with method and numbers.
4. **Compatibility table.**
5. **Install in 6 steps.**
6. **What it does NOT do:** it does not fix internal glass rubbing, and it does not change Bambu's tube lengths.
7. **Print settings.**
8. **Licence.** Proposed: Standard Digital File License or CC BY-NC-SA, for the owner to choose (§14).

### 12.7 Later variations, only after the launch is stable

- The Compact R60 set.
- P2S/X2D anchors, built from community-supplied measurements.
- Remix adapters for BLV / AMS Flipper risers, only with licence permission.
- **Product 002:** H2 AMS Deck (opportunity B), designed so FILAMENT PATH anchors fit it.

---

## 13. Owner measurements and photographs still required

**Tools:** digital calipers, a steel ruler, a phone camera, a kitchen scale (1 g), and a thermometer (any probe type). The best photos are straight-on, with a ruler in frame and the printer square to the camera.

### 13.1 All printers (P1S, H2S, H2C)

1. **Rear photos:**
   - one full straight-on photo;
   - one close-up of the filament inlet area;
   - one from the side showing how far everything sticks out.
   - All with AMS units in their normal positions, and again with the AMS removed.
2. **Current routing photos:** the stock tube path from each AMS outlet to each printer inlet, from the side and from the back, for the §11.0 baseline.
3. **PTFE tube OD:** caliper readings at 3 points on 3 different stock tubes. Note whether you see any ovality.
4. **Tube lengths as delivered:** measure each external tube actually installed.
5. **AMS outlet position** relative to the printer's rear top edge (X: left/right, Y: behind, Z: above), and the direction the outlet points, for each AMS in its usual place.
6. **Space behind the printer in your setup**, from the rear panel to the wall or obstacle.
7. **Spool inner core radius** of a Bambu spool, at the barrel surface where the first filament layer sits (checks R2, §8.2).
8. **Your actual AMS topology on each printer:** which AMS units, whether each sits on top or beside, and whether you use a buffer, an AMS Hub, a 4-in-1 adapter or a track switch.

### 13.2 P1S

9. Rear coupler: position from the top edge and right edge, collar OD, how far it sticks out from the panel, and the bracket outline with photos.
10. Filament buffer: outline, position, port spacing and port directions, and where its cables exit.
11. Rear spool-holder base: outline, profile (photo from the side with the holder removed if it comes off easily), and screw pitch.
12. Rear vent hole area: boundaries. Purge-chute opening: position, size, and whether it is on the left or right.
13. Where the internal tube exits at the top or rear, and its free length to the coupler.
14. **Door hinge side**, and the top-glass seating (photo of the edge).

### 13.3 H2S and H2C

15. Buffer inlets: position (upper and lower on the H2C), collar OD, protrusion, angle from vertical. Photo of the buffer window.
16. **Upper and lower rear spool-holder mount slots**, with the holder removed:
    - slot width;
    - undercut depth;
    - length;
    - spacing between the upper and lower slots;
    - photos straight-on and from 45°.
    - This is the single most important measurement for the H2 anchor.
17. Purge-chute opening: position and size. Exhaust grille boundaries.
18. Position of the safety-key socket, ports, e-stop (if fitted), and laser air pipe (if fitted).
19. **H2C 4-in-1 PTFE adapter II:** body L × W × H, port spacing and port angles, with photos from 3 sides. Also the track switch, if owned.
20. Whether the top glass is opened in normal use with the AMS on top, and how.
21. **Rear air temperature** on the H2C at a 65 °C chamber, after 1 h, at the buffer inlets and at the spool-holder mounts (sets PETG vs ASA, §8.8).
22. Door hinge side (H2S and H2C).

### 13.4 Optional (helps the claims)

23. HMS error history for the last 30 days on each printer (screenshots from Bambu Handy or Studio).
24. Any feed problems you have seen yourself, and on which slots.

---

## 14. Final approval checklist

Owner, please answer each item. CAD starts only when every **required** item is ✅.

| # | Decision | Required? | Options / recommendation |
|---|---|---|---|
| 1 | Approve **FILAMENT PATH (external fixed-radius routing)** as product 001 | Required | Recommended. The alternatives are E (H2 purge) or B (H2 AMS Deck) |
| 2 | Accept the explicit exclusions: no internal or toolhead guide, no glass-rub fix, no printed filament-path merger | Required | Recommended (§1, §7.1) |
| 3 | Approve the design rules R1–R9 (§7.1), especially **R80 default, R60 compact, R50 floor** | Required | |
| 4 | Launch scope: shared arcs + P1/X1 anchor + H2 anchor + gauge + cut jig; Merge Cradle gated on data; P2S/X2D post-launch | Required | Recommended |
| 5 | Anchor mount choices: P1S via the spool-holder base (vs coupler bracket); H2 via a pass-through slot (vs using only the free slot) | Required (after §13) | Recommendation after the photos |
| 6 | Materials: PETG default, ASA on H2 if the rear air exceeds about 55 °C | Required | |
| 7 | Supply the §13 measurements and photos | Required | |
| 8 | Accept the **kill criteria** (§11.10), and that no "less resistance" claim is made without data | Required | Recommended |
| 9 | Allow `makerworld.com`, `wiki.bambulab.com`, `bambulab.com` and `forum.bambulab.com` in this environment's network settings so I can verify the counts and specs on the live pages, or check the key ones yourself | Strongly advised | The data in this report comes from search extracts (§2.2) |
| 10 | Listing title, thumbnail concept and one-listing strategy (§12) | Before launch | |
| 11 | Licence choice | Before launch | Standard Digital File License or CC BY-NC-SA |
| 12 | Product 002 direction: H2 AMS Deck (B) or H2 purge liner/fume flap (E) | Optional now | B for ceiling, E for speed |

---

*Prepared for Odd Layer. Research and specification only. No geometry exists yet, and no claim in this document has been physically tested.*
