# MASTER PROMPT — VES-TECH Swiss (v2)

> **Was das hier ist:** Die verbindliche Beschreibung der Website VES-TECH Swiss
> (`https://www.ves-tech.ch`).
> Wer (Mensch oder KI) an diesem Projekt arbeitet, liest zuerst dieses Dokument und
> hält sich an die Regeln in Abschnitt 14. Das Dokument lebt **im Repository** und
> wird bei jeder architektonischen Änderung mitgepflegt.
>
> **v1 → v2:** Version 1 war eine einzelne HTML-Datei mit Client-Side-Rendering
> (`ves-tech-eshop.html`, ~440 kB, eine URL für die ganze Seite). Das war für eine
> Vorschau in Ordnung, für eine echte Website aber nicht: Suchmaschinen und
> Antwortmaschinen sahen genau **eine** Seite ohne Inhalt. v2 erzeugt daraus
> **360 echte, vorgerenderte Inhaltsseiten** in DE/FR/IT. Der alte Stand liegt unverändert
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
    Das ist die **Besucheradresse nach Vereinbarung** im JSON-LD und in
    `geo.*` (Quelle: `build/core.py::WORKSHOP`). Das Google-Unternehmensprofil
    muss die tatsächlich bestätigte Betriebsform und Adresse abbilden; die
    Partnerwerkstatt nicht automatisch als eigene Niederlassung eintragen.
    Für die laufende Verifizierung hat der Inhaber Bronschhofen bestätigt.
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

Die bestaetigten Firmenprofile auf Instagram (`vestechswiss`) und LinkedIn
(`ves-tech-swiss`) werden seit dem 22.09.2026 zentral in
`core.py::SOCIAL_PROFILES` gepflegt. Die URLs erscheinen in DE/FR/IT als
lesbare Textlinks unter der Firmenmarke im Footer und als `sameAs` am
Organization-Knoten. Es gibt keine eingebetteten Feeds, Social-SDKs oder
zusaetzlichen Trackingaufrufe. Private Profile und noch nicht bestaetigte
Facebook-, TikTok- oder Verzeichniseintraege werden nicht verlinkt.

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
360 × index.html + sitemap.xml + robots.txt + llms.txt + llms-full.txt
    + data/products.json + data/search-{de,fr,it}.json
```

**Kein Framework und kein Bundler.** Der Generator benötigt Python 3.9 oder neuer.
Node.js 22 oder neuer wird nur für die Frontend-Regressionstests verwendet. Ausgeliefert wird reines HTML/CSS/JS.

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
| `P.json` | 79 Produkte: `{id, cat, sub, vt, name, img, desc, specs{}}` — `specs` ist die kurze Merkmalsliste (Verfahren, Kühlung, Antrieb …), **nicht** die technische Tabelle |
| `CATS.json` | 5 Kategorien mit `subs[]` und Icon-Key `pk` |
| `UI.json` | 88 UI-Strings × de/fr/it |
| `CATTR/SUBTR/PDESC/SPECK/SPECV.json` | Übersetzungen für Kategorie, Unterkategorie, Beschreibung, Spec-Key, Spec-Wert |
| `PROC.json` | 7 MAHE-Verfahren |
| `BUYING_GUIDE.json` | Eigene Auswahlhilfen für die fünf Hauptkategorien, DE/FR/IT |
| `SUBCATEGORY_GUIDES.json` | Eigene Einleitung und 2–3 Auswahlkriterien für alle 21 eigenständigen Unterkategorien, DE/FR/IT; keine zusätzliche Plasma-TIG-Seite |
| `DLS.json` | 7 PDF-Links (⚠ `k` ist **nicht** eindeutig — Katalog und EN 1090 heissen beide `PDF`) |
| `FEAT.json` | 19 Verfahrens-Icons (blaue Kachel `#23457f`, weisses Piktogramm, orange Akzente) |
| `PANEL_HL_DEVICE.json` | **Besonderheiten je Frontpanel**, wörtlich von MAHE aus dem Tab Fronteingabesysteme, DE/FR/IT |
| `HL_DEVICE.json` | **Besonderheiten je Gerät**, wörtlich von mahe-online.de, DE/FR/IT — hat Vorrang vor allem anderen |
| `HL/HL_CLEAN/PANEL_HL.json` | Besonderheiten als Rückfall (Familie / Cleaner / Frontpanel) |
| `SPECMAP.json` | **Technische Daten**: Produkt → Tabelle(n) in `build/mahe_specs.json` |
| `SPECROW.json` | Zeilenbeschriftungen dieser Tabellen, DE → FR/IT |
| `SPECNOTE.json` | Fussnoten unter den Tabellen (der Stern in `450*`), DE/FR/IT |
| `FP.json`, `CTRL.json`, `PANEL_DRAWN.json` | Fronteingabesysteme, Bedienelemente, gezeichnete Panels |
| `ZUSTAND.json` | **Zustand einer Occasion** (Grad + Text DE/FR/IT), sichtbar auf der Seite und als `itemCondition` |
| `OCCTEXT.json` | **Beschreibung und Fragen einer Occasion**, DE/FR/IT: Abschnitte unter den Reitern, Fragen zusätzlich als `FAQPage` |
| `VERWANDT.json` | Verwandte Produkte (Neugerät ↔ Occasion derselben Technik), Karten unter der Detailseite |
| `DLOCC.json`, `IMGCAP.json` | Prospekte der Occasionen (lokal unter `assets/dl/`), Bildunterschrift zum Hauptbild |
| `products.json` | **generiert** — öffentlicher, maschinenlesbarer Katalog |
| `search-{de,fr,it}.json` | **generiert** — Suchindex fürs Frontend |

Die Fachlogik aus v1 ist 1:1 nach `core.py` portiert: `deriveFeat`, `matOf`,
`highlightsOf`, `fpAssign`, `relatedAcc`, `isWater`, `trK`, `trV`.

Bei Theta 60 HSC und AUT folgen Kurzmerkmale und Besonderheiten dem auf beiden
Herstellerseiten verlinkten [MAHE-Datenblatt, Seite 2](https://mahe-online.de/wp-content/uploads/2022/07/Theta_60_HSC.pdf):
Trennschnitt **< 35 mm**, empfohlener Schnitt **< 25 mm**. Die widersprüchlichen
40-mm-Kurzangaben sowie «max.»/«über» aus Herstellertexten werden nicht als
zusätzliche Leistung übernommen; die eng begrenzten Abweichungen stehen in
`verify_mahe.py::BEWUSST`. Die importierte technische Tabelle bleibt unverändert.

Bei MPT 3001 und MPT 2501 lautet der Steuerungspunkt in der Merkmalsliste
seit dem 21.09.2026 auf ausdrückliche Vorgabe des Inhabers «Steuerung über das
System CNC von MAHE», mit entsprechender FR-/IT-Fassung. Die Herkunft dieser
gezielten Textkorrektur ist in `HL_DEVICE.json::src` dokumentiert.
Seit dem 22.09.2026 verwendet auch die Auswahlhilfe fuer Schneidtische in
`SUBCATEGORY_GUIDES.json` diese vom Inhaber gewuenschte Bezeichnung; die
weiteren technischen Angaben bleiben unveraendert.

Die Occasion-Auswahlhilfe bezeichnet die PlasmaFix-Anlagen nicht pauschal
als Oerlikon. Bei Mikroplasma erklaert ein eigenes Auswahlkriterium die
Positionen im gemeinsamen Foto auf der PlasmaFix-51-Produktseite:
Oerlikon PlasmaFix P+T links/rechts, SAF-FRO PlasmaFix 51 in der Mitte.
Quelle sind `IMGCAP.json` und `INQUIRY_OPTIONS.json`. Daraus wird keine
aktuelle Stueckzahl oder Reservierung abgeleitet; die Verfuegbarkeit bleibt
ausschliesslich im datierten Verfuegbarkeitsfeld gepflegt.

## 5. Bilder

`build/images.py` lädt die Originale **einmalig** von `mahe-online.de`, skaliert sie
und legt sie als WebP ins Repo (`assets/img/p/<key>-400.webp` und `-1000.webp`,
zusammen 2,2 MB für 51 Bilder). Gründe: Ladezeit (Originale sind bis 4 MB),
kontrollierbare Bild-URLs und Bildgrössen und Ausfallsicherheit.
Ein CSP-freigegebener Error-Listener lädt im Notfall wieder vom Hersteller.
`assets/img/manifest.json` hält die Abmessungen für `width`/`height` (gegen CLS).

Neue Bilder: `python3 build/images.py` (braucht Netz und `cwebp`), danach `build.py`.

Das gemeinsame Theta-HSC-Bedienpanel verwendet seit dem 21.09.2026 die vom
Inhaber bereitgestellte und zur Veröffentlichung ausgewählte Grafik
`Theta Display.png` (1774 × 887 px). `data/FP.json::theta_hsc` verweist auf diesen
Import aus `build/panels.py`; er gilt für Theta 60/120/180 HSC und Theta 60/120 AUT.
Das Motiv bleibt unverändert, die WebP-Stufen sind 400, 1000, 1600 und 1774 px.
Der neue Dateiname verhindert alte Bilder aus dem Browsercache; Theta 40 behält
sein eigenes Panel. Die gelieferte Grafik ist keine neue technische Spezifikation.

Für die Reinigungstechnik wurden am selben Tag vier weitere vom Inhaber
bereitgestellte Grafiken importiert: `HyperCleaner CT200 FrontPanel.png`,
`HyperCleaner CT200 SYN FrontPanel.png`, `Hypercleaner ST Speed FrontPanel.png`
und `MLF100 Frontpanel.png`. CT 200 behält zwei getrennte Panelabbildungen;
ST Speed und MLF 100 erhalten erstmals eine eigene Zuordnung in `core.PANELS`.
Die Namen und Alternativtexte werden über `fpName()` in DE/FR/IT ausgegeben.
Die Grafiken werden nicht hochskaliert und begründen keine neuen technischen
Leistungsangaben. MiniReiniger, ST und ST Plus behalten ihre eigenen Panels.

Neues Herobild: `python3 build/hero.py hero <datei>` (braucht `cwebp`, und für
eine Vorlage, die kein JPEG ist, zusätzlich `Pillow` für den JPEG-Rückfall).
Beides meldet sich mit einem Satz, wenn es fehlt. `build.py`, `check.py` und
`audit.py` kommen weiterhin mit der Standardbibliothek aus — nur die
Bildwerkzeuge, die von Hand laufen, haben Voraussetzungen.

## 6. SEO

- `<title>` und `meta description` pro Seite einzigartig, Titel ≤ 68 Zeichen (Occasion ≤ 70, damit das Verfahren im Titel bleibt; `check.py` prüft 70)
- `canonical` auf jeder Seite, absolut
- `hreflang` de-CH / fr-CH / it-CH + `x-default` — gegenseitig verlinkt
- Open Graph + Twitter Card, `og:image` = Produktbild bzw. Hero
- **JSON-LD als ein `@graph` pro Seite:** `Organization`+`LocalBusiness`+`Store`,
  `WebSite` mit `SearchAction`, `BreadcrumbList`, `Product` ohne erfundene Angebote,
  `ItemList`, `FAQPage`, `WebPage`/`CollectionPage`/`ItemPage`/`ContactPage`
- `sitemap.xml` mit `xhtml:link`-Alternates (351 URLs); Suche, Datenschutz und AGB
  sind `noindex,follow` und stehen bewusst nicht drin. Das Impressum ist indexierbar.
- `lastmod` folgt dem Inhalt jeder Seite. Asset-Versionsnummern, CSP/SRI und die
  reine Laufzeitkonfiguration `window.VT` ändern das Datum nicht. Sichtbarer
  Inhalt, Metadaten, canonical/hreflang, JSON-LD, Navigation und Asset-Pfade
  bleiben relevant. Bestehende Daten werden nicht künstlich zurückgesetzt.
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

Die Occasion-Beschreibungen (`prod_desc_occ`) sind eigenständige, vollständige
Kurztexte für DE/FR/IT: Modell, Mikroplasma, Revision, Herisau und Kontakt auf
Anfrage. Sie hängen keine lange Produktbeschreibung an, die mitten im Satz
abgeschnitten würde. Das verbessert die Suchvorschau, ist aber keine Zusage
für Crawling oder Indexierung durch eine Suchmaschine.

## 7. AEO / AIO (Antwortmaschinen)

Damit die Geräte in ChatGPT-, Claude-, Perplexity- und Google-AI-Antworten auftauchen:

- **`/llms.txt`** — kompakte Landkarte der Website im llms.txt-Format
- **`/llms-full.txt`** — der komplette zitierfähige Inhalt in einer Datei:
  alle 79 Produkte mit Beschreibung, Besonderheiten, technischen Daten und Zubehör,
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
- Ergebnisseite `/suche/?q=…` mit Geräten, Dienstleistungen, Kategorien, Verfahren und Downloads

## 9. Anfrageliste

`localStorage` unter `vt.cart.v2` (Migration bekannter `vt.cart.v1`-Einträge), mit `try/catch` abgesichert (private Fenster
werfen). Menge pro Position, Persistenz über Seitenwechsel, Zähler im Header.
Erfolgreiches direktes Absenden entfernt nur die tatsächlich abgesendeten Mengen.
Während des Versands hinzugefügte Mengen bleiben erhalten. Bei Fehlern und beim
E-Mail-Entwurf bleibt die Liste erhalten. Defekte Speichereinträge werden verworfen.

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

**Optionale Statistik mit Zustimmung.** Ahrefs und Cloudflare Web Analytics laden erst nach
aktiver Zustimmung, mit gleichwertiger Ablehnen-Option und dauerhaft erreichbaren
Statistik-Einstellungen. Die Zustimmung läuft nach 180 Tagen ab. Die Anfrageliste
und die Statistik-Auswahl liegen getrennt in localStorage. Ahrefs misst den Weg
von Produktauswahl bis bestätigtem Formularversand, Cloudflare Ladezeiten.
Die neue Zustimmung ist v2; ein früherer Cloudflare-Grant gilt dafür nicht.
Registrierte Kampagnen werden maximal 24 Stunden in sessionStorage zugeordnet.
Details, Ereignisdefinitionen, SDK-Prüfsumme und Datenschutzgrenzen: README.md.

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
   in Überschriften der Mittelpunkt („3000 × 1500 mm · Theta 060 · MyPlasm CNC").
   **Ausnahme, vom Inhaber am 03.09.2026 entschieden:** in der Überschrift der
   zweiten Startseiten-Folie steht kein Mittelpunkt mehr. Sie heisst „MAHE MPT
   Plasmaschneidtisch CNC" — dieselbe Reihenfolge wie in FR und IT („table de
   découpe plasma CNC", „tavolo di taglio al plasma CNC"). So braucht sie
   weder Mittelpunkt noch Bindestrich und bleibt trotzdem richtiges Deutsch;
   die Zwischenfassung „CNC Plasmaschneidtisch" verstiess gegen 3b. Ebenso
   entfiel der Mittelpunkt in `trust_h3` („EN 1090 geprüft & dokumentiert").
   Der Mittelpunkt bleibt dort, wo er zwei Angaben trennt, die sonst
   ineinanderlaufen: im Untertitel der Folie und im Muster „Kategorie · MAHE"
   der Kategorieüberschriften (53 Stellen).
3a-bis. **Kein Schlusspunkt in Überschriften und Schauzeilen.** Vom Inhaber am
   03.09.2026 durchgehend entschieden. Betroffen waren `prog_h2` („Direkt zum
   richtigen Verfahren"), `k_h1` („Direkter Draht zum Techniker") und ihre FR-
   und IT-Fassungen. Im Banner `assets/img/hero.jpg` gilt dasselbe: dort sind
   die Punkte aus „Leistung Präzision Qualität", aus „Für professionelle
   Ergebnisse" und aus dem Claim „MAHE WIR SCHWEISSEN QUALITÄT" herausretuschiert.
   Fliesstext behält seine Satzzeichen — die Regel gilt für Überschriften,
   Schauzeilen und Bildtexte, nicht für Sätze.
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

### 15a. Sicherheitsstand (20.09.2026)

Statisches HTML ohne eigene Datenbank und ohne Kundenkonto. Der Browser versendet
Kontaktangaben bei aktivierter Konfiguration an Web3Forms. Ahrefs und Cloudflare Web Analytics
sind separate, zustimmungspflichtige Browserdienste. Details und Grenzen
stehen in [SECURITY.md](SECURITY.md), die aktuelle Einrichtung in [README.md](README.md).

- CSP ohne `unsafe-inline`; erlaubte Inline-Bootdaten und Styles sind gehasht.
  Der Bildrückfall verwendet einen Error-Listener, keine Ereignisattribute.
- Script-JSON maskiert `<`, damit auch eine Zeichenfolge `</script>` keine
  zusätzlichen HTML-Elemente öffnen kann.
- Persistierte Anfragelisten werden validiert; Mengen sind ganzzahlig von 1 bis 99.
  Suchtreffer werden als Text maskiert, bevor sichere Hervorhebungen entstehen.
- GitHub Actions hat standardmässig nur Leserechte; Schreibrechte für Pages und
  OIDC erhält ausschliesslich der Deploy-Job. Öffentliche Dateien werden separat
  zusammengestellt. Private Konfiguration und Berichte werden nicht veröffentlicht.
- GitHub Pages erlaubt keine eigenen Sicherheitsheader. Ein späterer Proxy muss
  HTTPS, DNS und erreichbare Crawler erhalten; nicht blind Namenserver umstellen.
- CAA mit allen tatsächlich verwendeten Zertifikatsdiensten abstimmen. Keine
  pauschale Einschränkung auf eine CA vor einer Hosting-/Proxy-Entscheidung.

## 16. Betrieb und weitere Inhalte

- Google Search Console ist für `https://www.ves-tech.ch/` eingerichtet, mit
  erfolgreicher Sitemap. Kontometriken und konkrete Audit-Ergebnisse gehören
  ausschliesslich in lokale `reports/`, nicht ins öffentliche Repository.
- Bing wurde mit dem Firmenkonto hinzugefügt und verifiziert; die Sitemap wurde
  eingereicht. `BING_SITE_VERIFICATION` erhalten, damit der Nachweis gültig bleibt.
- Web3Forms wurde auf dem Firmenkonto aktiviert. Der Formularkey liegt lokal
  in `config.local.json` und als `WEB3FORMS_KEY` in GitHub Actions. Das kostenlose
  Kontingent ist im Dashboard zu kontrollieren; keine automatischen Bezahl-Upgrades.
- Cloudflare Web Analytics ist live geprüft und muss nach jedem Integrationswechsel
  auf dem Live-Web geprüft werden. Es zählt nur zustimmende, nicht blockierte
  Browser auf den zugelassenen Seiten. Ahrefs zählt `inquiry_success` ausschliesslich
  nach bestätigtem Web3Forms-Versand; keine automatische Verkaufszählung.
- Für lokale Auffindbarkeit vorhandenes Google-Unternehmensprofil und reale
  Werkstatt-/Besucherangaben abgleichen. Kein doppeltes Profil und kein erfundener Standort.
- **Echte Kundenstimmen:** `data/REF.json` ist vorbereitet und leer; Anzeige und
  Review-Auszeichnung erst mit dokumentierter Freigabe. Keine erfundenen Referenzen.
- Nächste Inhalte: reale Reparaturbeispiele, Originalfotos und konkrete Fragen aus
  Kundenkontakten. Keine Massenproduktion nahezu identischer Orts- oder Produktseiten.

## 17. Erweiterungen vom 20.09.2026

- `data/BUYING_GUIDE.json`: eigene, dreisprachige Auswahlhilfen für alle fünf
  Hauptkategorien. Im sichtbaren HTML und in der deutschen `llms-full.txt`-Fassung.
- `Product.mpn` nur bei tatsächlich hinterlegter Hersteller-Artikelnummer.
  Eine interne Produkt-ID ist kein MPN. Keine erfundenen Ratings für Rich Results.
- `data/products.json` hat ein eigenes versioniertes Format und kein irreführendes
  schema.org-`@context`. Namen und Occasion-Zustand werden mit ausgeliefert.
- Bing-Verifizierung erfolgt aktuell per `msvalidate.01` aus `core.py`; Tag erhalten.
- Cloudflare-Beacon-Konfiguration ist öffentlich, administrative API-Tokens sind
  niemals Bestandteil des Projekts. Keine DNS-Umstellung durch diese Integration.
- `build/package_site.py` baut das öffentliche Artefakt aus einer Positivliste.
  Quellcode-Repository ist öffentlich; Berichte mit Kontodaten bleiben unter
  `reports/` und werden weder committet noch ausgeliefert.
- Dialoge sperren den Hintergrund, halten den Tastaturfokus und geben ihn zurück.
  Formulare begrenzen Laufzeiten, vermeiden doppelte Anfragen und erhalten
  Kundeneingaben bei Fehlern. Suchen können nach einem Netzwerkfehler erneut laden.
- Ohne Web3Forms-Key ist ein E-Mail-Entwurf kein abgeschickter Kundenkontakt.
  Die Oberfläche und die technischen Datenschutzhinweise sagen das ausdrücklich.
- `llms.txt` ist eine Zusatzdatei. Laut [Google](https://developers.google.com/search/docs/appearance/ai-features)
  benötigen AI Overviews/AI Mode keine speziellen KI-Dateien oder Schema-Typen.
  Hilfreiche Inhalte, Indexierbarkeit, belegte Aussagen und interne Links haben Vorrang.


## 18. Sicherheits- und Wiederherstellungsprüfung (20.09.2026)

- Skripte werden mit CSP-Hashes und SRI an ihre tatsächlichen Bytes gebunden.
  `strict-dynamic` vertraut nur diesen Startpunkten; die Cloudflare-Adresse im
  vertrauenswürdigen Loader bleibt fest. Keine fremden Skript-URLs aus Benutzereingaben.
- Die 404-Seite setzt `no-referrer`. Statistik lädt nur bei passendem Canonical
  und niemals auf unbekannten Pfaden. Formular-POSTs senden keinen Referrer.
- `build/security_check.py` gehört zu den verbindlichen Prüfungen vor jedem Deploy.
- `build/package_site.py` validiert Dateitypen und Pfade vor dem Kopieren, folgt
  keinen Symlinks und überschreibt keine vorhandenen Deployment-Verzeichnisse.
- GitHub: CodeQL, Secret Scanning/Push Protection, Dependabot, nur offizielle
  Actions mit vollständigem SHA; `main` gegen Löschen/Force-Push geschützt.
- `build/backup.py`: lokale Quell-/Git-/Release-Sicherung oder ausdrücklich
  öffentlicher Release-Modus. SHA-256, Pfadkontrolle und reale Wiederherstellung
  gehören zur Prüfung. CI bewahrt öffentliche Release-Archive 90 Tage auf.
- Keine privaten Backups, Konfigurationen oder Kontoberichte in öffentliche
  Actions-Artefakte. Ein lokales Backup auf derselben Festplatte ist keine
  unabhängige Katastrophensicherung. Betriebsanleitung: BACKUP.md und SECURITY.md.

## 19. Sprachpflege und stabile Adressen (21.09.2026)

- Vollständige Sprachprüfung der gepflegten DE-, FR- und IT-Texte: Produktbeschreibungen,
  Merkmale, Auswahlhilfen, Dienstleistungen, FAQ, Formulare und Rechtstexte.
  Sprachkorrekturen sind keine neue rechtliche Prüfung oder Zusage technischer Eigenschaften.
- Die deutsche Einleitung beginnt mit «VES-TECH Swiss ist Ihr Schweizer Händler
  für MAHE.»; kein Doppelpunkt unmittelbar nach MAHE. Alle vier Bereiche
  Schweissen, Schneiden, Reinigen und Automation bleiben sichtbar.
- `build/mahe_copy_edits.json` dokumentiert einzeln geprüfte, vollständige
  Herstellerformulierungen vor und nach der sprachlichen Korrektur. Der Abgleich
  akzeptiert ausschliesslich diese konkreten Zuordnungen; technische Zahlen,
  Modelle und ungeprüfte neue Herstellerangaben werden nicht pauschal normalisiert.
- Die 66 veröffentlichten Sprachadressen der 22 Unterkategorien stehen in
  `build/subcategory_slugs.json`. Sichtbare Bezeichnungen in `SUBTR` dürfen
  verbessert werden, ohne Links, Canonicals oder Sitemap-Adressen zu ändern.
  Neue Unterkategorien nach Veröffentlichung ebenfalls in der Karte festhalten.
- `core.SEARCH_POPULAR` ist die gemeinsame Quelle für Suchvorschläge im HTML
  und im Suchindex. Fachbegriffe und Regionen werden pro Sprache ausgegeben;
  Strassennamen, Modellbezeichnungen und Artikelnummern bleiben erhalten.
- Der Dokumentenimport übersetzt das allgemeine Wort «Signiergerät» in
  HCS-Titeln, damit ein erneuter Import keine deutschen Textreste zurückbringt.
- Die ausdrücklich gewählten MPT-Heroüberschriften aus §14.3a bleiben erhalten.
- HyperCleaner ST Speed: 2400 W beim Polieren (100 % Einschaltdauer), ST Plus:
  4000 W beim Polieren (30 %). Grundlage ist die MAHE-Betriebsanleitung
  `HyperCleaner-STSpeed_STPlus_25_DE_EN_ES.pdf`, §7.1/7.2, gedruckte Seite 15.
  `SPECNOTE` erläutert die getrennten Reinigungsleistungen. Die widersprechende
  3600-W-Webodräžka des Plus wird als präzise `BEWUSST`-Ausnahme dokumentiert;
  diese sachliche Korrektur ist kein Teil der sprachlichen Normalisierung.

## 20. Produktwahl und Geschäftsanfragen (21.09.2026)

- `data/INQUIRY_OPTIONS.json`: belegte MMS-/EcoMIG-Varianten und drei
  identifizierte PlasmaFix-51-Geräte, mit DE/FR/IT-Beschriftung und getrenntem
  datiertem Verfügbarkeitsnachweis. Keine Preise, Reservierungen oder erfundenen
  Hersteller-Artikelnummern. Zentrale Validierung in `core.inquiry_options()`.
- `window.VT.inquiryCatalog` ist der feste aktuelle Katalog für die funktionale
  Anfrageliste und den direkten Kontakt. Kein Suchindex-Fetch und keine Statistik
  nötig, um Produkt, Variante, Einzelgerät und deren sichere URL zu erhalten.
- `vt.cart.v2` speichert nur ID, Options-ID und Menge. Namen und URLs stammen aus
  dem aktuellen Katalog. Alte v1-Positionen werden geprüft und migriert.
  Varianten bleiben getrennt; ein konkretes Einzelgerät hat höchstens Menge 1.
- Kontakt-URLs erlauben ein bekanntes Produkt mit optionalem `option` oder eine
  bekannte `service`-Kennung. Sichtbarer Kontext und Geschäftsnachricht bleiben
  von Analytics unabhängig. Freitext wird nicht überschrieben.
- Der Suchindex enthält zusätzlich `services`; Python/JS verwenden dieselbe
  Normalisierung. Exakte Servicenamen müssen zu den echten Serviceseiten führen.
- Kleine optionale Qualifizierungsfelder ergänzen das Formular. Keine Kontakte
  oder Freitexte in URL, Analytics oder localStorage. Erfolgszusammenfassungen
  existieren nur lokal nach bestätigtem Versand.
- `node --test build/test_*.mjs` umfasst Frontend und Query-Datenschutzregressionen;
  `test_inquiry.py` prüft Register, sichere Ausgabe und Servicerouten.
- Produkt-/Kategoriezahlen bezeichnen Katalogeinträge, nicht Lagerbestand.
  Die MPT-Illustration erhält eine sichtbare Bildunterschrift.


## 21. Marketing und Occasion-Bezeichnungen (22.09.2026)

- Verifizierte Firmenprofile werden zentral über `SOCIAL_PROFILES` in
  `build/core.py` geführt; Fusszeile und `Organization.sameAs` verwenden
  dieselben URLs. Keine externen Social-Media-Embeds.
- Die Fusszeile nennt das ganze MAHE-Programm: Schweissen, Schneiden, Reinigen
  und Automatisieren. Service am Partnerstandort Herisau AR nach Vereinbarung.
- Occasion-Kacheln nennen Katalog-Modellreihen ohne pauschale Herstellermarke
  oder Lagerzusage. Die drei Geräte bei PlasmaFix 51 / P+T sind links und rechts
  Oerlikon PlasmaFix P+T, in der Mitte SAF-FRO PlasmaFix 51. Einstiegstexte und
  FAQs müssen diese Unterscheidung in DE/FR/IT erhalten.
- Produktanfragen verwenden die bestehenden Einzelgeräte-Options-IDs; sie
  stellen keine Reservierung dar. MPT-Auswahlhilfen nennen gemäss der
  ausdrücklichen Korrektur des Inhabers das System CNC von MAHE.
- Die Fremdmarkenprüfung akzeptiert zusätzlich vollständig zugeordnete Namen
  aus geprüften Einzelgeräte-Beschriftungen. MAHE bleibt als Ausnahme verboten;
  fehlende und unbekannte Herstellerzuordnungen werden weiterhin abgewiesen.
