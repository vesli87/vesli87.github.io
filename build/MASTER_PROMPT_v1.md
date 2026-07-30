# MASTER PROMPT — VES-TECH Swiss E-Shop (single-file HTML)

> **How to use this in Codex:** Attach the file `ves-tech-eshop.html` as the project base. It is the **single source of truth** and already contains 100 % of the work (HTML + CSS + JS + the embedded hero image in one file). This document describes the architecture, data model, design rules and conventions so you can **read, understand and extend** the shop without breaking anything. When you change something, keep it a **single self-contained HTML file** and follow the conventions below.

---

## 1. Product & business context
- **Site:** "VES-TECH Swiss" — a Swiss reseller of the German **MAHE** welding range (welding machines, plasma cutting, electrolytic cleaning, accessories). It is a catalog / inquiry site, **not** a webshop with checkout.
- **Company data (already in the file):**
  - Address: **Bildfelsstrasse 24, 9552 Bronschhofen (SG)**
  - Phone: **+41 76 710 91 39** (link `tel:+41767109139`)
  - Hours: **Mo–Fr 07:30–17:30**
  - Email used in code: `info@ves-tech.ch`
- **No prices.** Every product shows **"Preis auf Anfrage"**. Users add products to an **inquiry list ("Anfrageliste")** and send a request via the contact form.
- **Trilingual: DE / FR / IT.** German is the default. Language switch is in the top utility bar. **All user-facing text must exist in all three languages.**
- **Language of the UI/content = German (Swiss spelling: "ss" instead of "ß", e.g. "Schweissen", "Wasserkühlung").**

## 2. Tech constraints
- **One HTML file.** One `<style>` block, one `<script>` block. No build step, no framework, no bundler.
- External dependencies allowed: **Google Fonts** (Anton, Barlow Condensed, Bodoni Moda, Inter) and **remote MAHE product images** from `https://mahe-online.de/wp-content/uploads/...`. Everything else is inline.
- Must run by simply opening the file in a browser.
- **QA convention (do this after every change):**
  1. Extract the `<script>` and run `node --check` (must be valid JS).
  2. Run a DOM-mock harness in Node (mock `document.getElementById/createElement/querySelector...`) then `eval(script + testCode)` to verify data integrity (all `FEAT` icons exist, `fpAssign` panels valid, `relatedAcc` references valid, all translations present).
  3. Tag-balance check (count `<tag ` + `<tag>` vs `</tag>` for div/section/svg/style/script/a/ul/li/button; ignore void `<img>`).

## 3. View router (hash-less)
- `show(id)` toggles `.view.active`; helper `goView(id)`; `goHome()`.
- Views: **home, catalog (view-catalog), product (view-product), kontakt (view-kontakt), verfahren (view-verfahren), downloads (view-downloads)**.
- `goView('verfahren')` calls `renderVerfahren()`, `goView('downloads')` calls `renderDownloads()`.
- Mega menu (hamburger) routes to categories + Service/Downloads/Garantie/Verfahren/Kontakt.

## 4. i18n system
- `LANG` global ('de' | 'fr' | 'it'), default 'de'. `setLang(l)` sets it and calls `applyLang()`.
- `applyLang()` sweeps `document.querySelectorAll('[data-i18n]')` and sets `textContent = t(key)`, then re-renders catalog/product/cart and (if active) verfahren/downloads.
- `t(k)` reads from `UI[LANG][k]` (fallback DE). `UI` is built once, then **extended by several `Object.assign(UI.de/fr/it, {...})` calls** (this is the pattern used to add keys like `verf_h1`, `front_h`, `front_bes` — keep using `Object.assign` to add new keys).
- Content dictionaries (all keyed, all DE/FR/IT):
  - `CATTR` — category name translations; `catT()/catD()`.
  - `SUBTR` — subcategory translations; `subT()`.
  - `PDESC` — product short-description translations; `pDesc(p)` (falls back to `p.desc`).
  - `SPECK` — spec **key** translations; `trK()`.
  - `SPECV` — spec **value** translations; `trV()`.
- Helper translation objects for panels/highlights carry their own `{de:[],fr:[],it:[]}` arrays.

## 5. Data model

### 5.1 Categories — `CATS` (4 categories)
Each: `{id, name, sub:[...subcategory names...], pk:'<icon key>'}`.
- `schweissgeraete` — subs: **MIG / MAG, WIG / TIG, MMA, Plasma TIG** — pk `mig`
- `plasmaschneiden` — subs: **Theta, Theta Automation** — pk `plasma`
- `reinigung` — subs: **Cleaner, Signiergeräte, Dosiersystem, Elektrolyte** — pk `clean`
- `zubehoer` — subs: **Fahrwagen, Wasserkühlung, Drahtvorschubkoffer, Fernbedienungen, Werkstattausrüstung, Kabel, Brenner** — pk `gear`

### 5.2 Products — `P` (array, ~52 real MAHE products)
Schema per product:
```
{ id, cat, sub, vt, name, img, desc, specs:{ 'Key':'Value', ... } }
```
- `id` unique slug (e.g. `hypermig-x`, `hypertig-ax`, `theta-120`, `hypercleaner-st`, `r1`, `elektrodenkabel`, `mf405w`).
- `cat` = category id, `sub` = subcategory name (must match a `CATS.sub` entry).
- `vt` = variant/type label (e.g. `WIG AC/DC`, `MIG / MAG`), used by `fpAssign`/`matOf`.
- `img` = path **relative to** `https://mahe-online.de/wp-content/uploads/` (e.g. `2024/06/IMGP5943-226x300.png`). Thumbnails carry a `-WxH` suffix.
- `desc` = German short description (translations in `PDESC`).
- `specs` = ordered technical data (translated via `SPECK`/`SPECV`).

Key catalog groups (all real MAHE):
- **MIG/MAG:** HyperMIG X (flagship, real specs 10–420 A / 3~400 V / ED45%@400 A / IP23), EcoMIG, MMS.
- **WIG/TIG:** Omega AX, Beta DX, HyperTIG AX (AC/DC), HyperTIG DX (DC), Beta digital, HyperTIG AC/DC.
- **MMA:** i-1600, Delta, Delta Digital, Delta Digital DS.
- **Plasma TIG:** PlasmaTIG.
- **Theta (plasma cutting):** Theta 40/60/120/180; **Theta Automation:** Theta 60 AUT, 120 AUT.
- **Cleaner:** MiniReiniger, HyperCleaner ST (1200 W), Speed (2400 W), Plus (4000 W), CT 200 (combi TIG+clean).
- **Elektrolyte (consumables):** R1 (Rapid), RP1 (pastös), P1 (polish), N1 (neutralit), M1 (signing) — with Gebinde sizes.
- **Zubehör:** Fahrwagen (STT30/35, MPF02, MHCT01), Wasserkühlung (WK200/300/350), Drahtvorschubkoffer (DVS410/DVL420), Fernbedienungen (FRC5/RC5/RC15/RC100/RC100DS), Werkstattausrüstung (MCU1, USB2in1), Kabel (Elektrodenkabel, Massekabel), Brenner (MF405W, MF240W).

### 5.3 Images
- `SRC(path)` → `EMBED[filename]` (base64 map, currently only the hero) else `USE_LOCAL ? LOCAL+filename : REMOTE+path`. `USE_LOCAL=false`, `REMOTE='https://mahe-online.de/wp-content/uploads/'`.
- `fullImg(path)` strips the `-WxH` suffix → high-res original. **Product detail image and front-panel photos use `fullImg` for sharpness; product cards use the thumbnail for speed.**
- `imgFail(el, name, path)` fallback chain: local → remote → named placeholder (`referrerpolicy="no-referrer"`).
- **Hero image** is the customer-provided MAHE banner, embedded as a base64 **JPEG data URI** in `<img class="hero-photo">` so it renders offline/in preview. To change it, re-embed a new base64 image.

## 6. Icons

### 6.1 Process/feature icons — `FEAT` (19, "tile" style)
Each: `{ tile:true, svg:'<svg viewBox="0 0 48 48">...</svg>', de, fr, it }`.
- **Visual style = iso-oerlikon:** a **blue rounded square** `#23457f` (48×48, `rx=11`) filling the badge, with a **white pictogram** and **orange accents** `#ff5a3c`. `tile:true` → CSS `.procbadge.tile .ic{padding:0;border:0;background:transparent;overflow:hidden;aspect-ratio:1}` makes the tile fill the badge; label rendered below via `.procbadge .lb`.
- Keys: `mig` (filled MIG gun), `mma` (electrode holder), `wig` (TIG torch **with pointed tungsten electrode** — must look different from MIG), `hf` (**lightning bolt**, orange filled), `lift` (up-arrow from a line), `puls`, `doppelpuls`, `plasma`, `h2o` (water drop), `synergy` (circular arrows), `display`, `rollen` (4 rollers), `auto` (robot), `clean`, `mark`, `dose`, and `reinigen`/`beschriften`/`polieren` (blue tile + red diagonal + white tool — the "Reinigen/Polieren/Beschriften" cleaning badges).
- `deriveFeat(p)` decides which icons a product shows. Cleaner → `['reinigen','polieren','beschriften']`; electrolytes map to reinigen/polieren/beschriften; welding devices derive from `vt`/`sub`.
- `featLabel(k)` returns the localized label.

### 6.2 Category icons — `PK` (4)
`mig / plasma / clean / gear`, modern square SVG (viewBox 0 0 48 48), dark stroke `#141416` + orange accent, shown on the light homepage category cards.

### 6.3 Material chips
`matOf(p)` → subset of `ST` (Stahl), `SS` (INOX), `AL` (Aluminium); rendered as **orange-outlined pill chips** with a 2-letter badge + label. `matLabel()` localizes.

## 7. Front panels ("Fronteingabesystem")

- `FP` — panel objects: `{ n:'<name>', big:bool, img?:'<path>', tl:{de,fr,it}, ctrl:['<CTRL key>', ...] }`.
  - **HyperMIG X uses 5 real MAHE panel photos**: EcoMIG, EcoPuls (`HyperMIG_EX_Frontpanel`), Hyper (`HyperMIG_HX_Frontpanel`), Steel + Steel-Puls (`HyperMIG_SX_Frontpanel`).
  - **WIG uses drawn panels** `wig` (DC) and `wig_acdc` (AC/DC).
- `fpAssign(p)` returns the list of panel keys for a product:
  - `hypermig-x` → all 5 MIG panels.
  - other `MIG / MAG` → `['ecomig','ecopuls']`.
  - `WIG / TIG` → `['wig_acdc']` if `/ac\/dc/i.test(p.vt)` else `['wig']`.
  - `Plasma TIG` → `['wig']`; `MMA` → `['mma']`; `plasmaschneiden` → `['theta']`.
  - **Cleaner → `[]` (MAHE cleaners have NO front panel — do not invent one).**
  - accessories / electrolytes / signier / dosier → `[]`.
- `panelSVG(big)` draws a **realistic MAHE WIG control panel** (light grey body, charcoal buttons with LEDs, red digital display with A/sec/Hz/% units, AC/DC + HF + Job + Puls buttons, HYPER SPOT / ACTIVE SPOT + HyperArc Active LEDs, a large black rotary knob with an arc, and the signature **WIG current/slope curve** at the bottom: gas-pre · slope · I1 · I2 · slope · gas-post). Used when a panel has no photo.
- `PANEL_HL` — **front-system Besonderheiten** per panel key (`{de,fr,it}` arrays). e.g. `wig_acdc`: Einknopfbedienung, Übersichtliche Bedienerführung, Synergische Kennlinien, Hyper Arc Active / Hyper Spot / ActiveSpot Kennlinie serienmässig, Hochfrequenzpulsen, MAHE-MIX-PULSE (AC), Fernbedienung Ein/Aus, HF-Start oder Lift-Arc-Start, AC-Schweissen (WIG und MMA).
- `CTRL` — control-element labels (VOLT, AMP, WIG_HF, WIG_PULS, WIG_SLOPE, WIG_GAS, TAKT, MODE, PROC, WIRE, GAS, ARC, ...), each `{de,fr,it}`.

## 8. Product Besonderheiten (device-level) — MAHE-accurate
- `HL` — device Besonderheiten by **family** (`mig_hyper`, `mig_std`, `wig`, `wig_acdc`, `mma`, `plasmatig`, `theta`), `{de,fr,it}`.
- `HL_CLEAN` — cleaner Besonderheiten **by product id** (exact MAHE text incl. wattage: MiniReiniger, `hypercleaner-st` = "Leistungsstarke 1200 Watt Inverter-Stromquelle" + MAHE Pinsel-Schutz-System + Reinigen, Polieren und Markieren + Synergieprogramm für alle Verfahren + Umweltfreundlich und sicher reinigen; Speed=2400 W +Galvanisieren; Plus=4000 W; CT200=combi).
- `highlightsOf(p)` returns the device Besonderheiten: cleaner → `HL_CLEAN[p.id]`, else the family list from `HL` (WIG/TIG uses `wig_acdc` vs `wig` based on `/ac\/dc/i.test(p.vt)`), else `null`.

### 8.1 `renderFront(p)` (the "Fronteingabe" tab) — MATCHES MAHE LAYOUT
1. **Device Besonderheiten first** (heading `t('highlights')` = "Besonderheiten") from `highlightsOf(p)`.
2. If the product has panel(s): a **`t('front_h')` = "Fronteingabesystem"** section, then for each panel: title = `fp.n`, the panel **photo** (`fullImg`) or drawn `panelSVG`, and its front Besonderheiten (heading `t('front_bes')`) from `PANEL_HL`, followed by **Bedienelemente** (`t('controls')`) from `CTRL`.
3. If no panel and no highlights: fall back to feature-icon list.
- The first product tab is **relabeled** in `goProd`: "Fronteingabe" when the product has a panel, "Besonderheiten" when it doesn't (cleaner/electrolytes).

## 9. Product detail page
- Left: high-res image (`fullImg`). Right: kicker (`catT · MAHE`), **name in Bodoni Moda**, short desc, process-icon badges (`renderProcs`→`deriveFeat`), material chips, meta line (Verfügbarkeit=Auf Anfrage / Marke MAHE / Art.-Nr.), **Preis-auf-Anfrage box**, actions ("Zur Anfrageliste +", "Beratung anfragen").
- Below: 4 tabs — **Fronteingabe(/Besonderheiten) · Technische Daten · Passendes Zubehör · Downloads**. `switchTab()` toggles; default active = feat.
  - Technische Daten: `specs` table via `renderTabs`.
  - Passendes Zubehör: `relatedAcc(p)` → related product cards.
  - Downloads: product-relevant PDFs (subset of `DLS`).

## 10. Inquiry cart ("Anfrageliste")
- In-memory array (no server, no localStorage — **localStorage/sessionStorage must NOT be used in artifacts**). `renderCart()` renders the drawer; add/remove/qty; count badge in header; "Anfrage senden" opens the contact form. All quantities & names carried in memory.

## 11. Verfahren & Downloads pages
- `PROC` (7): MIS-Spritzerfrei, Doppelpuls, HyperPuls, HyperForce, HyperCold, HyperRoot, HyperUP — each `{ic:'<FEAT key>', n:{de,fr,it}, d:{de,fr,it}}`. `renderVerfahren()` builds numbered cards.
- `DLS` (7 real MAHE PDF links): Produktkatalog 2023, EN 1090 Konformitätszertifikat, and the 5 safety datasheets R1/RP1/P1/M1/N1. `renderDownloads()` builds the list. Links point to real `mahe-online.de/...pdf` files.

## 12. Design system / theme (LIGHT)
CSS variables (`:root`):
```
--bg:#ECEAE5; --bg2:#E3E0D9; --panel:#FFFFFF; --panel2:#F4F2ED;
--line:#D8D3CA; --line-soft:#E6E2DA;
--accent:#E0511A;      /* royal orange */
--accent-2:#FF8A3D;    /* light orange */
--white:#1A1A1A;       /* = main TEXT color (dark) */
--muted:#57534C; --muted-2:#847E75;
--paper:#FFFFFF; --ink:#141416; --ok:#1E9E52;
```
- **Important convention:** `--white` is used everywhere as the **text color** and holds a dark value. Never use `var(--white)` as a light background.
- **Fonts:** device/product names = **Bodoni Moda** (700, uppercase, letter-spacing); category card titles + section labels = **Barlow Condensed** (700, uppercase); body/UI = **Inter**. Anton remains loaded and is used for a few big display headings (hero heading `.disp`, catalog H1).
- **Header** white; **utility bar** light (`--bg2`); **footer** light `--bg2` with a 3px orange top border.
- **Hero** = full MAHE banner photo (dark, embedded) + bottom gradient veil + two CTA buttons; no eyebrow text (removed on purpose).
- **Dark elements kept on purpose:** the drawn control panels (real devices are dark/grey), the blue cleaning tiles (blue/red iso-oerlikon look), the dark "Anfrage" button and toast notification.

## 13. MAHE-accuracy status (content)
- **Verbatim from MAHE:** MIG (HyperMIG X + 5 panels), WIG/TIG (device + front-system Besonderheiten), Cleaner (per-model wattage & bullets).
- **MAHE-accurate from manuals/category (not a single screenshot):** MMA (Hot Start, Arc Force, Anti-Stick, Fugenhobeln, WIG Lift-Arc, basische/rutile Elektroden, fallnahtsicher, Generatorbetrieb), Theta/Plasma (Druckluft-Plasma, HSC, Pilotlichtbogen, Gittertrennen).
- **Accessories/electrolytes/cables/torches:** technical specs + process icons (MAHE lists no "Besonderheiten" for these).
- When the user provides a MAHE screenshot for any device, transcribe the "Besonderheiten" **word for word** into `HL`/`HL_CLEAN`/`PANEL_HL` in all three languages.

## 14. Roadmap (not yet built — optional next steps)
- Category hero banners (one image per category, same treatment as the main hero).
- Cleaner consumables (Karbon-Pinsel, Handgriff HLC, Polier-/Signierfilze, Weithalsbehälter).
- Zwischenschlauchpakete, Drahtvorschubrollen.
- Kontakt sub-pages (Verkauf/Einkauf/Support), Garantieregistrierung form.
- Optionally swap drawn WIG panel for the **real MAHE panel photo** (needs the image file/URL).

## 15. Hard rules for Codex when extending
1. Keep it **one self-contained HTML file**.
2. **No prices** anywhere — always "Preis auf Anfrage".
3. **All new text in DE + FR + IT** (Swiss "ss" spelling).
4. New process icons follow the **blue-tile `#23457f` + white pictogram** style with `tile:true`.
5. New products follow the `P` schema; add the subcategory to `CATS` and the translations to `SUBTR`/`PDESC`/`SPECK`/`SPECV`.
6. Cleaner-type products get **no invented front panel**; show device Besonderheiten instead.
7. Never use `localStorage`/`sessionStorage`.
8. After changes: `node --check`, DOM-mock data test, tag-balance — target **0 errors**.
9. Preserve the company data (address Bildfelsstrasse 24, 9552 Bronschhofen; phone +41 76 710 91 39).

---
**The attached `ves-tech-eshop.html` already implements all of the above. Load it as the base and continue from there.**
