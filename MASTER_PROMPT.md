# MASTER PROMPT — VES-TECH Swiss (v2)

> **Was das hier ist:** Die verbindliche Beschreibung der Website VES-TECH Swiss
> (`vesli87.github.io`, später `www.ves-tech.ch`).
> Wer (Mensch oder KI) an diesem Projekt arbeitet, liest zuerst dieses Dokument und
> hält sich an die Regeln in Abschnitt 14. Das Dokument lebt **im Repository** und
> wird bei jeder architektonischen Änderung mitgepflegt.
>
> **v1 → v2:** Version 1 war eine einzelne HTML-Datei mit Client-Side-Rendering
> (`ves-tech-eshop.html`, ~440 kB, eine URL für die ganze Seite). Das war für eine
> Vorschau in Ordnung, für eine echte Website aber nicht: Suchmaschinen und
> Antwortmaschinen sahen genau **eine** Seite ohne Inhalt. v2 erzeugt daraus
> **247 echte, vorgerenderte Seiten** in DE/FR/IT. Der alte Stand liegt unverändert
> unter `build/source-snapshot.html`, die alte Fassung dieses Dokuments unter
> `build/MASTER_PROMPT_v1.md`.

---

## 1. Produkt und Geschäftskontext

- **Site:** „VES-TECH Swiss" — Schweizer Partner für das deutsche **MAHE**-Geräteprogramm
  (Schweissgeräte, Plasmaschneiden, elektrolytische Reinigung, Zubehör).
  Katalog- und Anfrageseite, **kein** Checkout.
- **Firmendaten** (Quelle: `build/core.py::COMPANY`, sonst nirgends hartkodiert):
  - Werkstatt und Warenannahme: St. Gallerstrasse 49, 9100 Herisau (AR) — bei der
    Partnerfirma Schweisstechnik Scherrer AG, Besuch nach Vereinbarung.
    Das ist die **Besucheradresse**: sie steht im JSON-LD, in `geo.*` und im
    Google-Unternehmensprofil, und die drei müssen übereinstimmen
    (Quelle: `build/core.py::WORKSHOP`).
  - Sitz und Rechnungsadresse: Bildfeldstrasse 24, 9552 Bronschhofen (SG), Schweiz —
    nur im Impressum, in AGB/Datenschutz und auf der Kontaktseite
  - +41 76 710 91 39 · `vestechswiss@gmail.com` · telefonisch erreichbar
    Mo–Do 07:30–17:00 · Fr 07:30–11:30
  - Die Zeiten sind **Telefonzeiten**, keine Öffnungszeiten: sie stehen als
    `hoursAvailable` am ContactPoint, **nicht** als `openingHoursSpecification`
    am LocalBusiness — sonst kollidieren sie mit dem Unternehmensprofil.
- **Keine Preise.** Jedes Gerät zeigt „Preis auf Anfrage". Kundschaft sammelt Geräte
  in der **Anfrageliste** und schickt eine gebündelte Anfrage.
- **Dreisprachig DE / FR / IT**, Deutsch ist Standard. **Jeder** neue Text existiert in
  allen drei Sprachen. Schweizer Schreibweise: **„ss" statt „ß"** („Schweissen",
  „Wasserkühlung").
- **Domain:** `https://www.ves-tech.ch` (kanonisch), registriert bei Infomaniak,
  DNS-Zone ebenfalls dort (ns11/ns12.infomaniak.ch), A-Records auf GitHub Pages.
  `vesli87.github.io` leitet per 301 dorthin um. Gesetzt über `SITE` und
  `EMIT_CNAME` in `core.py`; die eigene Domain steht in der Pages-Konfiguration,
  nicht in der Datei `CNAME` (siehe 14a).
- **E-Mail:** `vestechswiss@gmail.com`. Entscheidung des Inhabers vom
  05.08.2026. Eine Adresse `info@ves-tech.ch` war vorbereitet und wurde wieder
  verworfen; sie hätte ein Postfach bei Infomaniak und einen **MX-Eintrag** in
  der DNS-Zone gebraucht. Ohne MX fällt ein sendender Server auf den A-Record
  zurück, und der zeigt auf GitHub Pages, das keine Mail annimmt. Wer die
  Adresse eines Tages doch umstellt, prüft zuerst `dig +short MX ves-tech.ch`
  und setzt den SPF-Eintrag von `v=spf1 -all` auf den Mailserver um — der
  jetzige Wert bedeutet „diese Domain versendet keine Mail", was zur
  Gmail-Adresse passt.

## 2. Architektur

```
data/*.json           ← Single Source of Truth (Produkte, Kategorien, Übersetzungen)
build/i18n_extra.json ← SEO-/AEO-Texte, FAQ, Rechtstexte (von Hand gepflegt)
        │
        ├─ build/core.py     Konfiguration, Daten, i18n, Fachlogik, URL-Schema
        ├─ build/render.py   HTML-Bausteine, JSON-LD, <head>
        ├─ build/pages.py    Seitenvorlagen
        └─ build/build.py    schreibt alles raus
        │
        ▼
247 × index.html + sitemap.xml + robots.txt + llms.txt + llms-full.txt
    + data/products.json + data/search-{de,fr,it}.json
```

**Kein Framework, kein Node, kein Bundler.** Der Build läuft mit der Python-3-Version,
die auf jedem Mac vorinstalliert ist. Ausgeliefert wird reines HTML/CSS/JS.

**Vorgerendert, nicht client-side.** Jede Seite enthält ihren vollständigen Text im
HTML. Das ist die Grundlage für SEO **und** AEO: Crawler und Antwortmaschinen lesen
denselben Inhalt wie ein Mensch, ohne JavaScript auszuführen. JavaScript ist reine
Anreicherung (Suche, Anfrageliste, Schubladen, Formulare) — ohne JS bleibt die
Website vollständig lesbar und navigierbar.

## 3. URL-Schema

| Seite | DE | FR | IT |
|---|---|---|---|
| Start | `/` | `/fr/` | `/it/` |
| Alle Geräte | `/produkte/` | `/fr/produits/` | `/it/prodotti/` |
| Kategorie | `/produkte/<cat>/` | `/fr/produits/<cat>/` | `/it/prodotti/<cat>/` |
| Unterkategorie | `/produkte/<cat>/<sub>/` | … | … |
| Produkt | `/produkte/<cat>/<id>/` | … | … |
| Verfahren | `/verfahren/` | `/fr/procedes/` | `/it/processi/` |
| Downloads | `/downloads/` | `/fr/telechargements/` | `/it/download/` |
| Kontakt | `/kontakt/` | `/fr/contact/` | `/it/contatto/` |
| FAQ | `/faq/` | `/fr/questions-frequentes/` | `/it/domande-frequenti/` |
| Suche | `/suche/` | `/fr/recherche/` | `/it/ricerca/` |
| Impressum / Datenschutz | `/impressum/`, `/datenschutz/` | … | … |

Kategorie-Slugs sind **pro Sprache übersetzt** (`schweissgeraete` / `postes-de-soudage`
/ `saldatrici`), Produkt-Slugs bleiben in allen Sprachen die Produkt-ID (Markennamen
übersetzt man nicht). Definiert in `core.py::SEG` und `core.py::CAT_SLUG`.
Der Sprachumschalter verlinkt **immer** auf dieselbe Seite in der anderen Sprache.

⚠ **Unterkategorie und Produkt können dieselbe URL beanspruchen.** Die
Unterkategorie „Plasma TIG" ergibt den Slug `plasma-tig` — genau wie das Produkt
mit der ID `plasma-tig`. Beide wollten `/produkte/schweissgeraete/plasma-tig/`;
geschrieben wurde die zuletzt erzeugte Seite (das Produkt), die Kategorieseite
verschwand still, und die URL stand **zweimal in der sitemap**. Seit dem
05.08.2026 lässt `build.py` die Kategorieseite in so einem Fall aus — die
Unterkategorie enthält ohnehin nur dieses eine Gerät, und die Produkt-URL ist
verlinkt und indexiert, die ändert man nicht. `check.py` meldet doppelte
`<loc>`-Einträge jetzt als Fehler.

## 4. Datenmodell (`data/`)

| Datei | Inhalt |
|---|---|
| `P.json` | 52 Produkte: `{id, cat, sub, vt, name, img, desc, specs{}}` — `specs` ist die kurze Merkmalsliste (Verfahren, Kühlung, Antrieb …), **nicht** die technische Tabelle |
| `CATS.json` | 4 Kategorien mit `subs[]` und Icon-Key `pk` |
| `UI.json` | 88 UI-Strings × de/fr/it |
| `CATTR/SUBTR/PDESC/SPECK/SPECV.json` | Übersetzungen für Kategorie, Unterkategorie, Beschreibung, Spec-Key, Spec-Wert |
| `PROC.json` | 7 MAHE-Verfahren |
| `DLS.json` | 7 PDF-Links (⚠ `k` ist **nicht** eindeutig — Katalog und EN 1090 heissen beide `PDF`) |
| `FEAT.json` | 19 Verfahrens-Icons (blaue Kachel `#23457f`, weisses Piktogramm, orange Akzente) |
| `PANEL_HL_DEVICE.json` | **Besonderheiten je Frontpanel**, wörtlich von MAHE aus dem Tab Fronteingabesysteme, DE/FR/IT |
| `HL_DEVICE.json` | **Besonderheiten je Gerät**, wörtlich von mahe-online.de, DE/FR/IT — hat Vorrang vor allem anderen |
| `HL/HL_CLEAN/PANEL_HL.json` | Besonderheiten als Rückfall (Familie / Cleaner / Frontpanel) |
| `SPECMAP.json` | **Technische Daten**: Produkt → Tabelle(n) in `build/mahe_specs.json` |
| `SPECROW.json` | Zeilenbeschriftungen dieser Tabellen, DE → FR/IT |
| `SPECNOTE.json` | Fussnoten unter den Tabellen (der Stern in `450*`), DE/FR/IT |
| `FP.json`, `CTRL.json`, `PANEL_DRAWN.json` | Fronteingabesysteme, Bedienelemente, gezeichnete Panels |
| `products.json` | **generiert** — öffentlicher, maschinenlesbarer Katalog |
| `search-{de,fr,it}.json` | **generiert** — Suchindex fürs Frontend |

Die Fachlogik aus v1 ist 1:1 nach `core.py` portiert: `deriveFeat`, `matOf`,
`highlightsOf`, `fpAssign`, `relatedAcc`, `isWater`, `trK`, `trV`.

## 5. Bilder

`build/images.py` lädt die Originale **einmalig** von `mahe-online.de`, skaliert sie
und legt sie als WebP ins Repo (`assets/img/p/<key>-400.webp` und `-1000.webp`,
zusammen 2,2 MB für 51 Bilder). Gründe: Ladezeit (Originale sind bis 4 MB),
Bild-SEO (nur selbst gehostete Bilder ranken) und Ausfallsicherheit.
Das `onerror`-Attribut lädt im Notfall wieder vom Hersteller.
`assets/img/manifest.json` hält die Abmessungen für `width`/`height` (gegen CLS).

Neue Bilder: `python3 build/images.py` (braucht Netz und `cwebp`), danach `build.py`.

## 6. SEO

- `<title>` und `meta description` pro Seite einzigartig, Titel ≤ 68 Zeichen
- `canonical` auf jeder Seite, absolut
- `hreflang` de-CH / fr-CH / it-CH + `x-default` — gegenseitig verlinkt
- Open Graph + Twitter Card, `og:image` = Produktbild bzw. Hero
- **JSON-LD als ein `@graph` pro Seite:** `Organization`+`LocalBusiness`+`Store`,
  `WebSite` mit `SearchAction`, `BreadcrumbList`, `Product` mit `Offer`,
  `ItemList`, `FAQPage`, `WebPage`/`CollectionPage`/`ItemPage`/`ContactPage`
- `sitemap.xml` mit `xhtml:link`-Alternates (327 URLs); Suche und Rechtstexte
  sind `noindex,follow` und stehen bewusst nicht drin
- `robots.txt` mit Sitemap-Verweis
- Verifizierungs-Tags für Google Search Console und Bing Webmaster Tools:
  Wert in `core.py` eintragen (`GOOGLE_SITE_VERIFICATION`,
  `BING_SITE_VERIFICATION`), das Tag erscheint dann auf jeder Seite.
  **Vorzuziehen ist der DNS-Weg** — ein TXT-Eintrag in der Zone bei Infomaniak.
  Er verifiziert die ganze Domain auf einmal, mit und ohne `www`, überlebt jeden
  Umbau am Generator und hängt nicht daran, dass ein Tag im `<head>` stehen
  bleibt. Die beiden Felder bleiben dann leer und im `<head>` steht kein
  Verifizierungs-Tag — das ist der gewollte Zustand, kein Versehen.
- CSS/JS mit `?v=<hash>` — sonst liefern Browser nach einem Deploy die alte Datei

**Preis auf Anfrage im Schema:** Der `Product`-Knoten trägt **gar keinen
`offers`-Knoten**. Bis zum 05.08.2026 stand dort ein `Offer` mit
`priceCurrency: "CHF"`, aber ohne `price`. Eine Währung ohne Betrag ist kein
Angebot, sondern ein halbes: Ahrefs meldete auf **231 Seiten** einen
schema.org-Validierungsfehler, und Google zeigt ein Offer ohne Preis ohnehin
nicht an. Der Knoten kostete also 231 Fehlermeldungen und brachte nichts.

Ein erfundener Preis kommt nicht in Frage — die Regel „keine Preise" ist der
Kern dieses Katalogs. Niemals `"price": "0"` schreiben. `check.py` erzwingt
beides: kein `offers` und kein `price` am Produkt.

Was das Angebot ausmacht, steht weiterhin da: sichtbar „Preis auf Anfrage" auf
jeder Seite, das Liefergebiet CH/LI am `Organization`-Knoten, und die
Anfrageliste als Weg zum Angebot. `seller` gehört **nicht** an `Product` —
das ist eine Eigenschaft von `Offer`.

**Länge der `meta description`:** `pages.py::clip` kürzt auf **155** Zeichen.
Der Wert stand auf 165; damit lagen 179 von 345 Seiten über der Grenze, ab der
Google abschneidet (pixelabhängig, in der Praxis 155–160 Zeichen). Auch
handgeschriebene Beschreibungen in `i18n_extra.json` bleiben darunter.

## 7. AEO / AIO (Antwortmaschinen)

Damit die Geräte in ChatGPT-, Claude-, Perplexity- und Google-AI-Antworten auftauchen:

- **`/llms.txt`** — kompakte Landkarte der Website im llms.txt-Format
- **`/llms-full.txt`** — der komplette zitierfähige Inhalt in einer Datei:
  alle 52 Geräte mit Beschreibung, Besonderheiten, technischen Daten und Zubehör,
  dazu die 7 Verfahren und alle 10 FAQ-Antworten
- **`/data/products.json`** — maschinenlesbarer Katalog, dreisprachig, mit
  Verkäuferangaben und Lizenzhinweis
- **`robots.txt` erlaubt KI-Crawler ausdrücklich** (GPTBot, OAI-SearchBot, ClaudeBot,
  PerplexityBot, Google-Extended, Applebot-Extended, CCBot u. a.). Das ist eine
  bewusste geschäftliche Entscheidung: Sichtbarkeit in KI-Antworten ist erwünscht.
  Wer das nicht will, entfernt den Block in `build/build.py::AI_AGENTS`.
- **FAQ mit 10 echten Fragen** je Sprache, als `FAQPage` ausgezeichnet — genau die
  Form, die Antwortmaschinen zitieren.
- Jede Antwort ist **eigenständig zitierfähig**: Firmenname, Ort und konkrete Zahlen
  stehen im Antworttext, nicht nur im Kontext.

## 8. Suche

Index wird beim ersten Tastendruck geladen (`data/search-<lang>.json`, ~45 kB).

- Normalisierung: Kleinschreibung, `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, Akzente,
  Satzzeichen weg. **`build.py::norm` und `app.js::norm` müssen identisch bleiben.**
- Drei Gewichtungsfelder pro Eintrag: `t1` Name/ID, `t2` Typ/Kategorie/Werkstoff,
  `t3` Beschreibung/Spezifikation/Besonderheiten
- Synonyme DE/FR/IT (`wig↔tig`, `alu↔aluminium`, `inox↔chromstahl↔edelstahl`,
  `fahrwagen↔wagen↔trolley`, …) — Treffer über Synonym zählt 0,82×
- Tippfehlertoleranz per Levenshtein auf dem Namen (Distanz 1 bis 5 Zeichen, sonst 2)
- Mehrwortsuche als UND; werden nicht alle Wörter getroffen, sinkt der Score auf 0,4×
- „Meinten Sie …?" aus dem Vokabular des Index
- Dropdown mit Tastatursteuerung (↑/↓/Enter/Esc), `role=combobox` + `role=listbox`,
  Trefferhervorhebung; `/` fokussiert das Suchfeld
- Ergebnisseite `/suche/?q=…` mit Geräten, Kategorien, Verfahren und Downloads

## 9. Anfrageliste

`localStorage` unter `vt.cart.v1`, mit `try/catch` abgesichert (private Fenster
werfen). Menge pro Position, Persistenz über Seitenwechsel, Zähler im Header.
Absenden leert die Liste.

> v1 verbot `localStorage` — das war eine Einschränkung der Artefakt-Vorschau.
> Auf einer echten Website ist die Speicherung funktional notwendig und in der
> Datenschutzerklärung beschrieben.

## 10. Formulare

Kontaktformular und Anfrageliste senden über **Web3Forms**
(`build/config.local.json` → `web3forms_key`, in CI das Secret `WEB3FORMS_KEY`).
Ohne Key fällt beides automatisch auf `mailto:` zurück — die Website funktioniert
also auch ohne Konfiguration.
Enthalten: Pflichtfeldprüfung mit Meldung am Feld (`aria-invalid` +
`aria-describedby`), Honeypot gegen Bots, Zustände „sendet/erfolgreich/Fehler".

## 11. Design

Unverändert aus v1, heller Auftritt:

```
--bg:#ECEAE5  --bg2:#E3E0D9  --panel:#FFFFFF  --panel2:#F4F2ED
--line:#D8D3CA --accent:#E0511A --accent-2:#FF8A3D
--white:#1A1A1A   /* ist die TEXTfarbe und dunkel – nie als heller Hintergrund */
--muted:#57534C --ink:#141416
```

Schriften: Gerätenamen **Bodoni Moda**, Labels/Titel **Barlow Condensed**,
Fliesstext **Inter**, grosse Display-Überschriften **Anton**.
Bewusst dunkel bleiben: gezeichnete Bedienpanels, blaue Reinigungs-Kacheln,
Anfrage-Button, Toast.

**Kein Cookie-Banner.** Die Website setzt keine Tracking-Cookies; die Anfrageliste
im `localStorage` ist technisch notwendig. Sobald Analytics dazukommt, braucht es
einen Banner mit echter Ablehnen-Option.

## 12. Barrierefreiheit

Skip-Link, `aria-expanded` an Menü und Schubladen, Fokus-Rückgabe beim Schliessen,
Tabs mit `role=tab`/`tabpanel` und Pfeiltasten, sichtbarer Fokusring,
`<noscript>`-Regel, die alle Tab-Inhalte ausklappt, Formularfehler am Feld,
`alt`-Texte aus Produktname + Beschreibung.

## 13. Befehle

```bash
python3 build/build.py      # alle Seiten neu erzeugen
python3 build/check.py      # QA – muss 0 Fehler melden
python3 build/audit.py      # Tiefenprüfung (--live prüft zusätzlich das Netz)
python3 build/images.py     # Bilder holen und optimieren (selten nötig)
python3 build/icons.py      # Favicons erzeugen (selten nötig)
python3 -m http.server 8099 # lokal ansehen: http://127.0.0.1:8099/
```

`check.py` prüft JSON-LD, tote Links, canonical, hreflang, Titel-/Description-Länge
und -Dubletten, fehlende Bilder, Tag-Balance, Sitemap-Vollständigkeit und
Sprachparität.

`audit.py` prüft, was einem Build-Check entgeht, Menschen und Suchmaschinen aber
auffällt: Überschriftenhierarchie, verwaiste Seiten, NAP-Konsistenz über alle
Sprachen, deutschen Text der in FR/IT stehen geblieben ist, Alt-Texte,
Meta-Dubletten je Sprache und das `lang`-Attribut. Beide laufen in CI.

## 14. Harte Regeln beim Erweitern

1. **Inhalt kommt aus `data/`**, niemals direkt ins generierte HTML schreiben —
   der nächste Build überschreibt es.
2. **Keine Preise.** Immer „Preis auf Anfrage", kein `price` im JSON-LD.
3. **Jeder neue Text in DE + FR + IT**, Schweizer „ss".
3a. **Kein Gedankenstrich im sichtbaren Text.** Wo „… und Automation – vom
   Techniker …" stand, steht jetzt ein Komma, ein Doppelpunkt, eine Klammer oder
   ein eigener Satz. In der Schriftgrösse des Fliesstextes wirkt der Strich auf
   dem Telefon wie ein Trennstrich mitten im Satz. Bei Aufzählungen der Form
   „Begriff – Erklärung" steht der Doppelpunkt („Hot-Start: sichere Zündung"),
   in Überschriften der Mittelpunkt („MAHE MPT · CNC-Plasmaschneidtisch").
   **Bis-Striche bleiben:** „10 – 420 A", „25–90 mm²", „Mo–Do 07:30–17:00",
   „Name A–Z", „Ziff. 2–4 UWG" — das sind Messwerte, Zeiten und Verweise, kein
   Satzzeichen. Ebenso bleibt `core.py::SPEC_EMPTY`: ein „–" in einer
   Tabellenzelle heisst „gibt es an diesem Modell nicht".
3b. **Kein hängender Bindestrich** (Ergänzungsstrich) in eigenen Texten. Aus
   „MAHE-Schweiss-, Schneid-, Reinigungs- und Automationssysteme" wurde „Alle
   Anlagen von MAHE zum Schweissen, Schneiden, Reinigen und Automatisieren";
   aus „Prüf- und Konformitätspaket" wurde „Paket für Prüfung und Konformität".
   Ausgeschrieben steht dasselbe da, nur ruhiger. **Normale
   Kompositum-Bindestriche bleiben** — `VES-TECH`, „E-Mail",
   „CNC-Plasmaschneidtisch", „MAHE-Geräteprogramm": ohne sie wäre es falsches
   Deutsch. Nicht angefasst werden ausserdem `HL*.json` und
   `PANEL_HL_DEVICE.json` (wörtlich von MAHE, `verify_mahe.py` gleicht sie ab),
   der amtliche Name „Eidgenössischer Datenschutz- und
   Öffentlichkeitsbeauftragter" und „DC+ und DC- Schweissen" — Letzteres ist
   die Polarität, kein Bindestrich.
3c. **MAHE ist mehr als Schweisstechnik.** Der Hersteller baut auch
   Schneidtechnik (Plasma, CNC-Schneidtische), elektrolytische Reinigung und
   Automation. Wo die Firma oder das Programm als Ganzes beschrieben wird —
   `home_h1`, `hero_lead`, `org_desc`, `tagline`, `kontakt_desc` — werden alle
   vier genannt. „Händler für MAHE-Schweisstechnik" verkauft das eigene
   Programm unter Wert.
4. Neue Prozess-Icons im Stil blaue Kachel `#23457f` + weisses Piktogramm,
   `tile:true`.
5. Neue Produkte folgen dem `P`-Schema; Unterkategorie in `CATS` ergänzen und
   Übersetzungen in `SUBTR`/`PDESC`/`SPECK`/`SPECV` nachziehen.
6. **Frontpanels nie erfinden.** Seit dem 31.07.2026 liegen 41 Panel-Fotos
   direkt von MAHE vor (`build/panels.py` importiert sie nach
   `assets/img/panels/`, Zuordnung in `core.py::PANELS`). Wo der Hersteller
   keines geliefert hat, bleibt der gezeichnete Ersatz aus `PANEL_DRAWN.json`
   oder es werden nur die Besonderheiten gezeigt. Der frühere Sonderfall
   „Cleaner bekommen kein Panel“ entfällt — für sie gibt es jetzt echte Fotos.
7. Firmendaten nur in `core.py::COMPANY` ändern.
8. `norm()` in `build.py` und `app.js` müssen identisch bleiben.
9. Nach jeder Änderung: `build.py` **und** `check.py` — Ziel sind **0 Fehler**.
10. **Besonderheiten kommen von MAHE, nicht von uns.** `build/scrape_mahe.py`
    holt sie von mahe-online.de und legt sie unter `build/mahe_besonderheiten.json`
    ab; übernommen werden sie von Hand nach `data/HL_DEVICE.json`, damit kein
    Text am falschen Gerät landet. Offensichtliche Tippfehler des Herstellers
    („Relegung", „Syniergie", „Reiningen", „Funkcion") werden korrigiert und `ß`
    wird zu `ss` — ein fremder Fehler sieht auf unserer Seite aus wie unserer.
11. Liefert MAHE einen Screenshot mit „Besonderheiten", wird der Text **wortwörtlich**
    in `HL`/`HL_CLEAN`/`PANEL_HL` übernommen, in allen drei Sprachen.
12. **Technische Daten kommen ebenfalls von MAHE** und stehen als Tabelle mit
    einer Spalte je Modellvariante auf der Seite — genau so, wie der Hersteller
    sie zeigt. `build/scrape_specs.py` holt sie, `data/SPECMAP.json` ordnet sie
    einem Produkt zu, `build/verify_mahe.py` vergleicht anschliessend **jede
    einzelne Zelle** mit der Herstellerseite. Zwei Fallen dabei:
    * Der Spaltenschlüssel ist nicht die Spaltenüberschrift. Bei der
      HyperTIG AX heisst die erste Variantenspalte intern `240`, angezeigt
      wird `250`. Wer nur die AJAX-Daten nimmt, schreibt die falsche
      Modellnummer an die Spalte.
    * Die AJAX-Antwort enthält Spalten, die MAHE gar nicht zeigt — Reste
      früherer Baureihen. Übernommen wird nur, was in der Konfiguration
      `visible` ist.

## 14a. Eigene Domain und GitHub Pages

Die Website wird über einen **GitHub-Actions-Workflow** veröffentlicht
(`build_type: workflow`). Dabei gilt eine Besonderheit, die viel Suchzeit kostet:

> **Die Datei `CNAME` im Repository wird ignoriert.** Sie konfiguriert die
> eigene Domain nur beim Deployment aus einem Branch. Beim Actions-Deployment
> muss die Domain in der Pages-Konfiguration stehen, sonst antwortet sie mit
> „Site not found".

```bash
gh api -X PUT repos/vesli87/vesli87.github.io/pages -f cname=www.ves-tech.ch
gh workflow run pages.yml     # danach einmal neu deployen
```

`build/deploy.sh` erledigt das automatisch, sobald `EMIT_CNAME = True` steht.
Die `CNAME`-Datei bleibt trotzdem im Build – sie schadet nicht und wäre nötig,
falls je auf Branch-Deployment zurückgewechselt wird.

Nach dem Setzen der Domain stellt GitHub ein Let's-Encrypt-Zertifikat aus. Das
dauert einige Minuten bis Stunden; solange schlägt HTTPS fehl. Das ist normal
und erledigt sich von selbst.

**Danach muss „Enforce HTTPS" eingeschaltet werden — es geht nicht von selbst
an.** Bis zum 05.08.2026 stand `https_enforced: false`, obwohl das Zertifikat
längst `approved` war. Folge: jede Seite war zusätzlich unverschlüsselt über
`http://` erreichbar, Crawler nahmen diese Fassung (Ahrefs meldete darüber eine
503), und die Datenschutzerklärung behauptete zu Unrecht, es werde
ausschliesslich über HTTPS ausgeliefert.

```bash
gh api repos/vesli87/vesli87.github.io/pages --jq '.https_enforced'
echo '{"https_enforced": true}' | gh api -X PUT repos/vesli87/vesli87.github.io/pages --input -
```

Danach leitet `http://www.ves-tech.ch/…` mit 301 auf `https://…` um.
`audit.py --live` prüft genau das.

**Zur 503 selbst:** GitHub Pages drosselt schnelles paralleles Crawlen mit
`503 Service unavailable`. Das ist keine kaputte Seite — dieselbe URL antwortet
Sekunden später mit 200. `audit.py` fasst deshalb bei 5xx und 429 zweimal nach
und fragt mit sechs statt zwölf Verbindungen. Wer einen 503-Bericht eines
Crawlers bekommt, prüft die URL zuerst einzeln, bevor er etwas ändert.

**Eine einzige gedrosselte Seite erzeugt im Bericht vier rote Punkte.** Am
05.08.2026 gemessen: `5XX page` 1, `5XX page in sitemap` 1, `Indexable page
became non-indexable` 1 und `Hreflang to redirect or broken page` **2** — die
beiden anderen Sprachfassungen, die per hreflang auf die gedrosselte Seite
zeigen. Es sieht nach vier Fehlern aus und ist einer, und der ist keiner.
Gegenprobe: alle 345 hreflang-Ziele einzeln abgefragt, alle 200.

**Externe Links immer auf das Endziel setzen, nie auf eine Weiterleitung.**
Zwei Fälle sind am 05.08.2026 aufgefallen und behoben:

| Link | leitete um auf | stand auf |
|---|---|---|
| `schweisstechnik-scherrer.ch` (301) | `www.schweisstechnik-scherrer.ch` | 6 Seiten |
| `edoeb.admin.ch` (302) | `edoeb.admin.ch/de` | 3 Datenschutzseiten |

Der zweite ist jetzt pro Sprache gesetzt (`/de`, `/fr`, `/it`) — das ist auch für
Lesende besser, sie landen in ihrer Sprache. Prüfen lässt sich das so:

```bash
grep -rho 'href="https\?://[^"]*"' --include=index.html . | sed 's/href="//;s/"$//' \
  | grep -v ves-tech.ch | sort -u \
  | while read u; do echo "$(curl -sS -o /dev/null -w '%{http_code}' "$u")  $u"; done | grep -v '^2'
```

**Dasselbe gilt für mahe-online.de.** Ein Ahrefs-Lauf meldete 45 externe 4xx —
alles Bedienungsanleitungen und Datenblätter beim Hersteller, alle mit
`429 Too many requests`. Einzeln und mit Pause abgefragt antworteten am
05.08.2026 **alle 64** verlinkten MAHE-Dokumente mit 200. Prüfskript:

```bash
grep -rho 'href="\(https://mahe-online\.de[^"]*\)"' --include=index.html . \
  | sed 's/href="//;s/"$//' | sort -u \
  | while read u; do echo "$(curl -sIL -o /dev/null -w '%{http_code}' "$u")  $u"; sleep 0.4; done
```

## 15. Was sich am Code schützen lässt — und was nicht

Eine Website liefert ihren Code an jeden Browser aus, der sie öffnet. HTML, CSS
und JavaScript **müssen** beim Besucher ankommen, sonst gäbe es nichts
anzuzeigen. Alles, was so tut, als würde es das verhindern, ist Fassade:

| Massnahme | Wirkung | Preis |
|---|---|---|
| Rechtsklick sperren | `Strg+U`, `curl`, DevTools — in Sekunden umgangen | Text nicht markierbar, kaputte Bedienung, Barrierefreiheit weg |
| Textauswahl sperren | dito | Kundschaft kann Telefonnummer nicht kopieren |
| DevTools-Blocker | umgangen, sobald JavaScript aus ist | Seite bricht bei manchen Nutzern |
| JavaScript verschleiern | Aufwand für den Kopierer: Minuten | grösserer Download, schwerer zu warten |
| Inhalt per JS nachladen | Crawler sehen nichts mehr | **zerstört SEO und AEO vollständig** |

Die letzte Zeile ist der Kern: Sichtbarkeit in Suchmaschinen und Kopierschutz
sind gegenläufig. Google muss den Text lesen können — und was Google lesen kann,
kann jeder lesen. Für eine Katalogseite, deren Zweck Auffindbarkeit ist, gewinnt
die Sichtbarkeit.

**Was tatsächlich schützt:**

1. **Urheberrecht.** `LICENSE` im Repository und der Hinweis im Impressum machen
   die Rechtslage eindeutig. Das ist der einzige Schutz, der vor Gericht zählt.
2. **Repository privat stellen.** Dann ist der Quellcode nicht mehr einsehbar —
   die ausgelieferte Website bleibt es naturgemäss. Setzt GitHub Pro voraus
   (Pages aus privaten Repositories ist kostenpflichtig).
3. **Das, was wirklich Wert hat, liegt ohnehin nicht im Code:** die Domain, die
   Marke, die MAHE-Partnerschaft, die Kundenbeziehungen und der Rang bei Google.
   Wer die Dateien kopiert, hat davon nichts.

### 15a. Sicherheitsstand (geprüft am 05.08.2026)

Kopierschutz ist das eine, Sicherheit das andere — und dort lässt sich wirklich
etwas tun. Stand nach der Prüfung:

**Gut, weil die Bauart es hergibt.** Kein Server, keine Datenbank, kein
Anmelden, kein Node und kein Paket aus dem Netz. Damit fallen die häufigsten
Einfallstore weg: SQL-Injection, Rechteausweitung, verwundbare Abhängigkeiten,
kompromittierte npm-Pakete. Der gesamte Bestand wird beim Build erzeugt und
liegt statisch da.

**Geprüft und in Ordnung:**

| Punkt | Befund |
|---|---|
| Zugangsdaten in der Git-Historie | keine, nie eine `.env` eingecheckt |
| GITHUB_TOKEN im Workflow | `contents: read`, Standard auf `read` |
| Fremde GitHub-Actions | nur offizielle `actions/*` |
| SPF | `v=spf1 -all` — die Domain versendet keine Mail |
| DMARC | `v=DMARC1; p=reject` — schärfste Stufe |
| `target="_blank"` | alle 579 mit `rel="noopener"` |
| XSS über `?q=` | `esc()` vor dem Hervorheben, Überschrift als `textContent` |

**Behoben am 05.08.2026:**

- **Content-Security-Policy** als `<meta>` (siehe `render.py::CSP`) und
  `<meta name="referrer" content="strict-origin-when-cross-origin">`.
- **Anfrageliste gehärtet.** Die Liste liegt im `localStorage` und wurde per
  `innerHTML` gezeichnet. `esc()` maskiert Anführungszeichen, aber nicht das
  Schema — ein `href="javascript:…"` wäre anklickbarer Schadcode geblieben.
  Neu prüft `safeUrl()` in `app.js`, dass eine Adresse ein eigener Pfad oder
  `https` ist, sonst wird `#` daraus. Die Menge geht als `parseInt` ins HTML,
  nicht als Zeichenkette. Gegenprobe mit manipuliertem `localStorage`:
  0 eingeschleuste Skripte.
- Das letzte `style="…"`-Attribut ist in eine Klasse gewandert.

**Was auf GitHub Pages nicht geht.** Eigene HTTP-Kopfzeilen lassen sich dort
nicht setzen. Es fehlen deshalb dauerhaft `X-Frame-Options`,
`X-Content-Type-Options` und `HSTS`; `frame-ancestors` wirkt im `<meta>` nicht.
Praktisch heisst das: die Seite lässt sich in einen fremden Rahmen setzen. Für
einen Katalog ohne Anmeldung ist das hinnehmbar. Wer es abstellen will, braucht
ein Hosting mit eigenen Kopfzeilen (z. B. Infomaniak oder Cloudflare davor).

**Zwei offene Punkte, bewusst nicht erledigt:**

1. **`'unsafe-inline'` in der CSP.** 306 Seiten tragen ein `onerror`-Attribut am
   Bild (Rückfall auf mahe-online.de). Ereignis-Attribute lassen sich nicht per
   Hash erlauben. Wer den Rückfall nach `app.js` verlegt — ein
   `error`-Lauscher in der Aufsetzphase —, kann `'unsafe-inline'` streichen und
   die Richtlinie wird deutlich schärfer.
2. **CAA-Eintrag fehlt.** Ohne ihn darf jede Zertifizierungsstelle ein
   Zertifikat für `ves-tech.ch` ausstellen. Mit einem CAA-Eintrag nur noch die
   eingetragene. Bei Infomaniak in der DNS-Zone:
   `ves-tech.ch. CAA 0 issue "letsencrypt.org"` (GitHub Pages nutzt Let's
   Encrypt). Prüfen: `dig +short CAA ves-tech.ch`.

## 16. Offene Punkte

- **Web3Forms-Key eintragen.** Bis dahin gehen Anfragen über das Mailprogramm.
  Seit dem 05.08.2026 ist dieser Rückfall brauchbar: statt nur `mailto:`
  aufzurufen und „Mailprogramm geöffnet“ zu melden, bleibt die fertige Anfrage
  mit Adresse und Kopierknopf sichtbar stehen. Damit geht nichts mehr verloren,
  wenn kein Mailkonto eingerichtet ist. Ersetzt aber keinen echten Versand:
  Konto auf web3forms.com, Schlüssel nach `build/config.local.json` als
  `{"web3forms_key": "…"}` — die Datei steht in `.gitignore`.
- Google Search Console und Bing Webmaster Tools verifizieren, Sitemap einreichen.
  Weg: Domain-Property in der Search Console anlegen, den TXT-Eintrag im
  Infomaniak-Manager **zusätzlich** zum bestehenden SPF-Eintrag setzen (mehrere
  TXT-Records am Zonenapex sind erlaubt — den SPF dabei nicht überschreiben),
  danach in den Bing Webmaster Tools „Import aus Google Search Console“ wählen;
  eine zweite Verifizierung entfällt. Das ist zugleich die einzige Besucher-
  messung, die ohne Änderung an der Datenschutzerklärung auskommt: sie zählt
  bei Google und Bing, nicht auf dem Gerät der Besucher. Die Zusage
  „keine Analyse- oder Statistikwerkzeuge“ bleibt damit wahr.
- Google Business Profile für Bronschhofen anlegen (stärkster lokaler SEO-Hebel)
- Kategorie-Hero-Bilder (die vier Kategorieseiten zeigen nur Text),
  Verbrauchsmaterial für Cleaner, Garantieregistrierung
- **Echte Kundenstimmen.** `data/REF.json` ist vorbereitet und leer; der Block
  auf der Startseite und die `Review`-Auszeichnung erscheinen erst, wenn dort
  ein Eintrag mit `"freigabe": true` steht. Erfundene Referenzen kommen nicht
  hinein — die Begründung steht in der Datei. Nach einer erledigten Reparatur
  kurz fragen, ob man zwei Sätze zitieren darf.
- **CAA-Eintrag** in der DNS-Zone (siehe 15a)
- **`'unsafe-inline'` aus der CSP** — dafür den Bildrückfall aus dem
  `onerror`-Attribut nach `app.js` verlegen (siehe 15a)

Erledigt und deshalb gestrichen: eigene Domain samt DNS, Datenblatt-PDFs je
Gerät (64 Dokumente für 27 Geräte in `data/DLDEV.json`), erzwungenes HTTPS,
Servicebereich mit eigenen Seiten.
