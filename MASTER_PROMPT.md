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
> **363 echte, vorgerenderte Inhaltsseiten** in DE/FR/IT. Der historische Stand liegt (mit nachtraeglich abgesicherten mailto-Parametern)
> unter `build/source-snapshot.html`, die alte Fassung dieses Dokuments unter
> `build/MASTER_PROMPT_v1.md`.

---

## 1. Produkt und Geschäftskontext

- **Site:** „VES-TECH Swiss" — Beratung und Verkauf von Geräten aus dem deutschen **MAHE**-Geräteprogramm
  (Schweissgeräte, Plasmaschneiden, elektrolytische Reinigung, Zubehör).
  Katalog- und Anfrageseite, **kein** Checkout.
- **Geschäftsrolle (08.10.2026):** Die Beschaffung von MAHE-Neugeräten erfolgt
  über Schweisstechnik Scherrer AG. VES-TECH Swiss wird weder als offizieller,
  autorisierter oder exklusiver MAHE-Partner noch als Landesvertretung oder
  Direktimporteur bezeichnet. Beratung und Verkauf von MAHE-Geräten sind die
  sachliche Beschreibung. Die separat bestätigte Partnerwerkstatt in Herisau
  bleibt bestehen. Kundschaft und Leistungen in CH/LI begründen keine
  Exklusivität oder Herstellerbeauftragung; Lieferort und Ablauf werden je
  Auftrag vereinbart. Technische Herstellerangaben und Marken bleiben erhalten.
  Öffentliche Texte enthalten keine private Korrespondenz.
  Auch Preisabsätze, Service-Metadaten und Gewährleistungsabläufe dürfen
  keinen eigenen Import oder eine direkte Liefervereinbarung mit MAHE
  voraussetzen. Verfügbarkeit von Ersatzteilen und Abwicklung mit dem
  Lieferanten werden im Einzelfall geklärt; VES-TECH Swiss bleibt der
  Ansprechpartner. Die Preisbindung, vereinbarte Kostenübernahme und
  gesetzlichen Kundenrechte bleiben unverändert. Die Datenschutzerklärung
  nennt Schweisstechnik Scherrer AG als Empfänger nur für die erforderlichen
  Angaben zur angefragten Beschaffung, Lieferung oder Serviceabwicklung.
  AGB und Datenschutzerklärung tragen den Stand 08.10.2026.
- **Firmendaten** (Quelle: `build/core.py::COMPANY`, sonst nirgends hartkodiert):
  - Werkstatt und Warenannahme: St. Gallerstrasse 49, 9100 Herisau (AR) — bei der
    Partnerfirma Schweisstechnik Scherrer AG, Besuch nach Vereinbarung.
    Das ist die **Besucheradresse nach Vereinbarung** im separaten
    JSON-LD-Place `#partner-workshop` (Quelle: `build/core.py::WORKSHOP`).
    Die Organisation hat dagegen ihre Sitzadresse in Bronschhofen; die
    Partnerwerkstatt ist kein eigener VES-TECH-Laden oder eigene Filiale.
    Die allgemeinen Ortsmetadaten nennen ebenfalls den Sitz, ohne angenäherte
    Koordinaten als präzisen Unternehmensstandort auszugeben. Das Google-Unternehmensprofil
    muss die tatsächlich bestätigte Betriebsform und Adresse abbilden; die
    Partnerwerkstatt nicht automatisch als eigene Niederlassung eintragen.
    Für die laufende Verifizierung hat der Inhaber Bronschhofen bestätigt.
  - Sitz und Rechnungsadresse: Bildfeldstrasse 24, 9552 Bronschhofen (SG), Schweiz —
    nur im Impressum, in AGB/Datenschutz und auf der Kontaktseite
  - +41 76 710 91 39 · `vestechswiss@gmail.com` · telefonisch erreichbar
    Mo–Fr 07:30–17:00
  - Nach erneuter Vorgabe des Inhabers am 20.10.2026 gilt auch am Freitag
    07:30–17:00; Montag bis Donnerstag bleibt 07:30–17:00. Die Änderung gilt
    in DE/FR/IT/EN/ES auch für Impressum, Datenschutz, AGB und ContactPoint.
  - Seit dem 20.10.2026 wird die einheitliche telefonische Erreichbarkeit auf
    Wunsch des Inhabers kompakt als Mo–Fr 07:30–17:00 dargestellt, sinngemäss
    in allen fünf Sprachen und auch in den Rechtstexten.
  - Die Zeiten sind **Telefonzeiten**, keine Öffnungszeiten: sie stehen als
    `hoursAvailable` am ContactPoint, **nicht** als `openingHoursSpecification`
    am LocalBusiness — sonst kollidieren sie mit dem Unternehmensprofil.
- **Keine Preise.** Jedes Gerät zeigt „Preis auf Anfrage". Kundschaft sammelt Geräte
  in der **Anfrageliste** und schickt eine gebündelte Anfrage.
- **Fünfsprachig DE / FR / IT / EN / ES**, Deutsch ist Standard. **Jeder** neue Text existiert in
  allen fünf Sprachen. Schweizer Schreibweise: **„ss" statt „ß"** („Schweissen",
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

Die bestaetigten Firmenprofile auf Instagram (`vestechswiss`), LinkedIn
(`ves-tech-swiss`) und Facebook (`https://www.facebook.com/profile.php?id=61594862482139`)
werden seit dem 22.09.2026 zentral in
`core.py::SOCIAL_PROFILES` gepflegt. Die URLs erscheinen in DE/FR/IT als
Symbol-Links unter der Firmenmarke im Footer und als `sameAs` am
Organization-Knoten. Seit dem 19.10.2026 stehen Instagram, LinkedIn, Facebook
und WhatsApp auf Wunsch des Inhabers in einer gemeinsamen Icon-Reihe ohne
sichtbare Beschriftung. Die Links behalten einen Namen über `aria-label` und
`title`, eine sichtbare Tastaturmarkierung und 54 × 54 px grosse Klickflächen.
Auf Wunsch des Inhabers wurden die einfarbigen Bootstrap-Symbole am selben Tag
durch farbige Originale aus den offiziellen Meta- und LinkedIn-Markenpaketen
ersetzt. `assets/icons/social/` enthält PNG für Instagram, Facebook und LinkedIn
sowie das originale grüne WhatsApp-SVG. Instagram wird aus dem offiziellen
5000-px-PNG proportional auf 256 px verkleinert; die anderen drei Dateien bleiben
unverändert. Darstellung: 32 px Höhe, bei LinkedIn mit Platz für das vorhandene
Registrierungszeichen. Farben und Proportionen werden nicht per CSS verändert.
Herkunft und SHA-256 stehen in `build/social_brand_assets.json`, Markenrechte in `LICENSE`.
Es gibt keine eingebetteten Feeds, Social-SDKs oder
zusaetzlichen Trackingaufrufe. Private Profile und noch nicht bestaetigte
TikTok- oder Verzeichniseintraege werden nicht verlinkt.

Der vom Inhaber bestaetigte WhatsApp-Geschaeftskontakt steht zentral in
`COMPANY.whatsapp_href`. Kontaktseite und Footer verlinken ihn in DE/FR/IT als
normalen externen Link ohne vorbefuellten Text, Einbettung oder Referrer.
Im Footer wird derselbe Link als Icon gerendert; die Kontaktseite behält ihren
ausgeschriebenen Kontaktaufruf.
`contact_whatsapp` misst nach Statistik-Zustimmung ausschliesslich den Klick,
nicht Nachrichtentext, Telefonnummer, Versand oder Antwort. Die automatische
Messung externer Linkziele bleibt gesperrt.

Facebook-Kampagnen verwenden ausschliesslich die festen Vierer-Kombinationen in
`data/ANALYTICS_CAMPAIGNS.json`. Ein einzelner `fbclid` wird nach Zustimmung vor
Ahrefs aus der aktuellen URL entfernt und weder gespeichert noch gemessen.
Unbekannte weitere Parameter und unsichere Referrer bleiben ausgeschlossen;
Cloudflare misst diesen Einstieg weiterhin nicht. Es wird kein Meta Pixel geladen.

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
610 × index.html + sitemap.xml + robots.txt + llms.txt + llms-full.txt
    + data/products.json + data/search-{de,fr,it,en}.json
```

**Kein Framework und kein Bundler.** Der Generator benötigt Python 3.9 oder neuer.
Node.js 22 oder neuer wird nur für die Frontend-Regressionstests verwendet. Ausgeliefert wird reines HTML/CSS/JS.
Die Frontendskripte sind Initialisierungsfunktionen: im Browser starten sie sofort,
Node importiert dieselben Funktionen per CommonJS und uebergibt DOM/Storage als
Abhaengigkeiten. Keine Ausfuehrung eingelesener Quelltextstrings in den Tests.
`build/html_tools.py` liest JSON-LD mit HTMLParser und verarbeitet echte Starttags
fuer lastmod, ohne Scriptdaten, Kommentare oder redaktionelle Bytes umzuschreiben.

**Vorgerendert, nicht client-side.** Jede Seite enthält ihren vollständigen Text im
HTML. Das ist die Grundlage für SEO **und** AEO: Crawler und Antwortmaschinen lesen
denselben Inhalt wie ein Mensch, ohne JavaScript auszuführen. JavaScript ist reine
Anreicherung (Suche, Anfrageliste, Schubladen, Formulare) — ohne JS bleibt die
Website vollständig lesbar und navigierbar.

## 3. URL-Schema

| Seite | DE | FR | IT | EN | ES |
|---|---|---|---|---|---|
| Start | `/` | `/fr/` | `/it/` | `/en/` | `/es/` |
| Alle Geräte | `/produkte/` | `/fr/produits/` | `/it/prodotti/` | `/en/products/` | `/es/productos/` |
| Kategorie | `/produkte/<cat>/` | `/fr/produits/<cat>/` | `/it/prodotti/<cat>/` | `/en/products/<cat>/` | `/es/productos/<cat>/` |
| Unterkategorie | `/produkte/<cat>/<sub>/` | … | … | `/en/products/<cat>/<sub>/` | `/es/productos/<cat>/<sub>/` |
| Produkt | `/produkte/<cat>/<id>/` | … | … | `/en/products/<cat>/<id>/` | `/es/productos/<cat>/<id>/` |
| Verfahren | `/verfahren/` | `/fr/procedes/` | `/it/processi/` | `/en/processes/` | `/es/procesos/` |
| Downloads | `/downloads/` | `/fr/telechargements/` | `/it/download/` | `/en/downloads/` | `/es/descargas/` |
| Kontakt | `/kontakt/` | `/fr/contact/` | `/it/contatto/` | `/en/contact/` | `/es/contacto/` |
| FAQ | `/faq/` | `/fr/questions-frequentes/` | `/it/domande-frequenti/` | `/en/faq/` | `/es/preguntas-frecuentes/` |
| Suche | `/suche/` | `/fr/recherche/` | `/it/ricerca/` | `/en/search/` | `/es/buscar/` |
| Impressum / Datenschutz | `/impressum/`, `/datenschutz/` | … | … | `/en/legal-notice/`, `/en/privacy/` | `/es/aviso-legal/`, `/es/privacidad/` |

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
| `P.json` | 81 Produkte: `{id, cat, sub, vt, name, img, desc, specs{}}` — `specs` ist die kurze Merkmalsliste (Verfahren, Kühlung, Antrieb …), **nicht** die technische Tabelle |
| `CATS.json` | 5 Kategorien mit `subs[]` und Icon-Key `pk` |
| `UI.json` | 157 UI-Strings × de/fr/it/en |
| `CATTR/SUBTR/PDESC/SPECK/SPECV.json` | Übersetzungen für Kategorie, Unterkategorie, Beschreibung, Spec-Key, Spec-Wert |
| `PROC.json` | 19 Verfahren, Pulsvarianten und Zusatzfunktionen mit Wirkprinzip, Anwendung und Einstellung, DE/FR/IT |
| `BUYING_GUIDE.json` | Eigene Auswahlhilfen für die fünf Hauptkategorien, DE/FR/IT |
| `SUBCATEGORY_GUIDES.json` | Eigene Einleitung und 2–3 Auswahlkriterien für alle 21 eigenständigen Unterkategorien, DE/FR/IT; keine zusätzliche Plasma-TIG-Seite |
| `PRODUCT_GUIDES.json` | Belegte Auswahlhinweise für 27 Produktfamilien, mit Quellenverweisen und vollständigen DE/FR/IT-Texten |
| `GUIDE_LINKS.json` | Typisierte Referenzen auf bestehende Geräte, Kategorien, Unterkategorien, Services und Unternehmensseiten; keine neuen Kompatibilitätszusagen |
| `DLS.json` | 7 PDF-Links (⚠ `k` ist **nicht** eindeutig — Katalog und EN 1090 heissen beide `PDF`) |
| `FEAT.json` | 32 originale MAHE-Symbole mit Herstellerbild, Abmessungen und DE/FR/IT-Beschriftung |
| `HYPERMIG_CWK.json` | Quellenbelegter CWK-Vorteilsratgeber mit elf Symbolen und Optionsmatrix X/HX/EX/SX, DE/FR/IT |
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
| `search-{de,fr,it,en}.json` | **generiert** — Suchindex fürs Frontend |

Die Fachlogik aus v1 ist 1:1 nach `core.py` portiert: `deriveFeat`, `matOf`,
`highlightsOf`, `fpAssign`, `relatedAcc`, `isWater`, `trK`, `trV`.

Seit dem 07.10.2026 verlinken WK 300 und DVL 420 direkt unter ihrer
Produktbeschreibung auf die zugehoerige Geraetefamilie, sichtbar unterstrichen, sprachgleich und ohne
einen Reiter oeffnen zu muessen (`pages.py::accessory_context_html`). Grundlage
sind `P.json` und die Auswahlhinweise in `SUBCATEGORY_GUIDES.json`: Beim WK 300
bleibt die Zuordnung ausdruecklich auf **MMS 3000** begrenzt, obwohl die
verlinkte MMS-Seite auch MMS 2000 beschreibt. Beim DVL 420 werden die genaue
HyperMIG-X-Ausfuehrung und das Zwischenschlauchpaket erfragt. Dies erweitert
**nicht** die Kompatibilitaetsliste `ACC.json`. Die FR-/IT-Beschreibung des
MF240W entspricht wieder dem vorhandenen deutschen Text «fuer kleinere
Leistungsklassen»; Stromwerte oder Einschaltdauern werden nicht ergaenzt.

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

Am 19.10.2026 kam das vom Inhaber bereitgestellte `MAHE HyperMIG X Frontpanel.png`
(1541 × 1020 px) hinzu. `hypermig_x_graphic` steht bei HyperMIG X an erster Stelle
und bei der neu aufgenommenen HyperMIG TWIN vor HX. Die WebP-Stufen sind 400,
1000 und 1541 px; das Originalmotiv bleibt unverändert. Beide Herstellerseiten
führen X und HX ausdrücklich auf; EX/SX bleiben ausschliesslich bei HyperMIG X.
`PANEL_GUIDES.json` erklärt Bedienung, Anzeigen, Benutzerprofile und JOB in DE/FR/IT,
ergänzt die geprüften Herstellerlisten und wird vor dem Build validiert. Quelle für
die Bedienung ist `HyperMIG_X_TFT_10_DE.pdf`, Abschnitt 4.2: Doppelpuls ist eine
Option, JOB speichert die Betriebsart der Brennertaste nicht, bis zu acht Benutzer
sind möglich. Auf Wunsch des Inhabers entfallen die Hinweise auf beispielhafte
Bildwerte in den Galeriebeschriftungen und im Bedienratgeber in DE/FR/IT.
Eine allgemeine Nachrüstbarkeit wird nicht zugesagt. Suchindex,
`products.json::front_panels` und `llms-full.txt` enthalten
dieselben Erläuterungen. Die öffentlich sichtbaren Herstellerlinks bleiben erhalten.

Jede Galeriefolie besitzt ihren eigenen, vor dem Laden reservierten Bildrahmen
gemäss `render.dimg_klasse()`. Die Bildunterschrift steht mit kurzem Abstand
ausserhalb des Rahmens. Breite Panelbilder übernehmen dadurch nicht mehr die
Höhe des Gerätefotos; Pfeile, Miniaturen, Tastaturbedienung und die Darstellung
ohne JavaScript bleiben erhalten.

HyperMIG TWIN ist ein eigenes Produkt mit zwei Drahtvorschubkoffern und den
sichtbaren Modellspalten 300/350/400 aus Tabelle 12372. Versteckte AJAX-Spalten
450–600 werden nicht übernommen. Produktfoto: originale HX-Ausführung; das neue
X-Panel steht separat in der Galerie und im Bedienabschnitt. TWIN ist nicht mit
TwinArc gleichzusetzen. Technische Daten werden getrennt von HyperMIG X geführt;
Gewicht 95 kg, Zwischenschlauchpakete bis 20 m gemäss TWIN-Unterlagen. Der falsch
mit CWK beschriftete Datenblattlink der Herstellerseite wird nach dem tatsächlichen
PDF-Inhalt als X / HX TWIN bezeichnet (`scrape_dls.py`). Die neue Anleitung zum
Grafikpanel und die separate HX-TWIN-Anleitung sind eindeutig benannt. Der aktuelle
HyperMIG-X-Tabellenstand enthält zusätzlich die Modellspalte 550; alte Kurzwerte
zu 420 A, 76 V und 103 kg wurden mit den Herstellerwerten abgeglichen und korrigiert.

Neues Herobild: `python3 build/hero.py hero <datei>` (braucht `cwebp`, und für
eine Vorlage, die kein JPEG ist, zusätzlich `Pillow` für den JPEG-Rückfall).
Beides meldet sich mit einem Satz, wenn es fehlt. `build.py`, `check.py` und
`audit.py` kommen weiterhin mit der Standardbibliothek aus — nur die
Bildwerkzeuge, die von Hand laufen, haben Voraussetzungen.

Seit dem 19.10.2026 importiert `build/symbols.py --cwk <PDF>` elf originale
Symboltafeln aus `HyperMIG_HX_EX_SX_CWK.pdf` (08/2026, vom Inhaber geliefert).
Die Revision ist per SHA256 in `build/mahe_cwk_symbols.json` festgelegt. Die fünf
zusätzlichen Schlüssel sind `coldrootforce`, `speedcontrol`, `fourroll`, `remote`
und `spool15`; sechs vorhandene Verfahrensbilder haben neue, vollständige
Dateien `cwk-2026-*.webp`. Alte Katalogdateien bleiben erhalten. Pulse und
Double-pulse lagen im PDF jeweils über einer zweiten Symbolzeichnung: Der Import
wählt die letzte bereits vorhandene Originalzeichnung einschliesslich ihres
Grafikzustands. Es wird kein Piktogramm erfunden; Originaldatei und Marken bleiben
unverändert. Neue Dateien verhindern eine Auslieferung alter Bilder aus dem Cache.
Das CWK-Datenblatt zeigt bei der Spule ausdrücklich `< 15 kg` und `< 300 mm`.
Diese Angabe wird nur im gekennzeichneten CWK-Abschnitt ausgegeben, nicht auf
TWIN oder andere Gerätebauformen übertragen.

`HYPERMIG_CWK.json` erklärt alle elf Symbole und die Vorteile, zeigt EX-Optionen
(Puls, Doppelpuls, WIG, Fugenhobeln) und SX-Optionen (HyperPuls, HyperUP).
Aufgeführt bedeutet keine pauschale Serienausstattung; Doppelpuls ist für das
grafische X-Panel gemäss Anleitung ebenfalls als Option markiert. Die zusätzliche
WIG-Lift-Arc-Angabe der SX-Webseite wird gegenüber der fehlenden Nennung im
CWK-PDF erklärt. Die eigenen Familienmerkmale bleiben entsprechend qualifiziert.
Ein Sprunglink öffnet bei Bedarf zuerst den zugehörigen Produktreiter; Labels,
Tabindex und Tastaturbedienung bleiben dabei synchron.

`build/import_cwk_specs.py <PDF>` liest die Tabellen über die tatsächlichen
Textpositionen. X/HX/SX (PDF-Seiten 2/4/8) werden nur nach vollständiger Gleichheit
zusammengefasst, EX (Seite 6) bleibt getrennt. Die Snapshots stehen in
`build/mahe_cwk_specs.json` und werden zusätzlich zu den AJAX-Daten geladen,
damit ein Scraper-Refresh sie nicht entfernt. EX: 16/25/25 A Netzabsicherung,
X/HX/SX: jeweils 20 A. EX-Gewichte ohne Einheit bleiben im Rohbeleg erhalten,
werden aber nicht als Gewichtsangaben veröffentlicht. Der übrige Herstellerwert
wird unverändert übernommen. Suche, `products.json`, `llms-full.txt`, Quellenlinks
und Downloads enthalten die neuen Angaben und ihre Grenzen.

## 6. SEO

- `<title>` und `meta description` pro Seite einzigartig, Titel ≤ 68 Zeichen (Occasion ≤ 70, damit das Verfahren im Titel bleibt; `check.py` prüft 70)
- `canonical` auf jeder Seite, absolut
- `hreflang` de-CH / fr-CH / it-CH / en-CH + `x-default` — gegenseitig verlinkt
- Open Graph + Twitter Card, `og:image` = Produktbild bzw. Hero
  Kategorie und Unterkategorie verwenden die erste vorhandene Produktabbildung
  ihrer gefilterten Katalogliste, auch als `CollectionPage.primaryImageOfPage`.
  So erscheint bei Plasma kein allgemeines HyperMIG-Banner. Kataloguebersicht
  und allgemeine Serviceseiten behalten das gemeinsame Firmenmotiv.
- **JSON-LD als ein `@graph` pro Seite:** `Organization`+`LocalBusiness`,
  `WebSite` mit `SearchAction`, `BreadcrumbList`, neutrale Katalogeintraege als `Thing`,
  `ItemList`, `FAQPage`, `WebPage`/`CollectionPage`/`ItemPage`/`ContactPage`
- `sitemap.xml` mit `xhtml:link`-Alternates (595 URLs); Suche, Datenschutz und AGB
  sind `noindex,follow` und stehen bewusst nicht drin. Das Impressum ist indexierbar.
- `lastmod` folgt dem Inhalt jeder Seite. Asset-Versionsnummern, CSP/SRI und die
  reine Laufzeitkonfiguration `window.VT` ändern das Datum nicht. Sichtbarer
  Inhalt, Metadaten, canonical/hreflang, JSON-LD, Navigation und Asset-Pfade
  bleiben relevant. Bestehende Daten werden nicht künstlich zurückgesetzt.
- `robots.txt` mit Sitemap-Verweis
- Seit 21.10.2026 bleiben die fuenf Such-Einstiegsseiten crawlbar, damit
  Suchmaschinen ihr `noindex,follow` lesen koennen. Ergebnis-URLs mit dem
  Parameter `q` werden weiterhin vom Crawlen ausgeschlossen, sowohl als
  erster Parameter als auch nach anderen Parametern. Ein Crawl-Verbot ist
  kein Ersatz fuer `noindex` und kein Schutz privater Daten.
- `data/PRODUCT_SEO.json` enthaelt fuer alle 81 Produkte gepruefte Titel,
  vollstaendige Beschreibungen und lokalisierte Geraetearten in allen fuenf
  Sprachen. Die Metadaten werden nicht mitten im Satz abgeschnitten.
  Marken und Modellpaare bleiben erhalten, einschliesslich SAF-FRO PlasmaFix
  51 / Oerlikon PlasmaFix P+T. Die Geraeteart steht bei MAHE auch sichtbar
  ueber dem Produktnamen. `validate_editorial_guides()` stoppt den Build vor
  dem Ersetzen von Dateien bei fehlenden Produkten, Sprachen, Modellnamen,
  unvollstaendigen Beschreibungen oder zu langen Texten. Neue Produkte und
  Namensaenderungen brauchen daher passende Suchtexte.
- `data/CATEGORY_COMPARISONS.json` definiert sichtbare Vergleiche auf
  bestehenden Unterkategorien: MPT-Schneidtische und Theta-Plasmabrenner.
  Zellen stammen ausschliesslich aus den vorhandenen Produktspezifikationen,
  Beschriftungen aus `SPECK` und den vorhandenen Uebersetzungen. Keine
  berechneten Schnittdicken, erfundenen Optionen oder neuen URLs. Die
  Tabellen sind vorgerendert, mit Produktlinks, Zeilenkoepfen und einer
  per Tastatur bedienbaren Scrollregion fuer schmale Bildschirme.
- Seit 20.10.2026 enthalten die 405 Produkt-URLs zusätzlich die Bild-Erweiterung
  der Sitemap mit ihrem tatsächlich angezeigten Hauptbild. Keine UI-Symbole,
  neuen Bilddateien oder zusätzlichen Browser-Downloads. Das inhaltsabhängige
  `lastmod` bleibt unverändert; Bilder werden dadurch zur Entdeckung angeboten,
  nicht als bereits indexiert oder als Rich Result zugesagt.
- `data/SEARCH_LANDINGS.json` pflegt eigene Titel, Beschreibungen und sichtbare
  Hauptüberschriften für ausgewählte bestehende Kategorien und Unterkategorien,
  darunter Schweissgeräte, Plasma, Nahtreinigung, CNC-Schneidtische und Brenner,
  DE/FR/IT/EN/ES.
  `validate_search_landings()` prüft Sprachvollständigkeit, bestehende Ziele,
  Eindeutigkeit und Textgrenzen vor dem Ersetzen generierter Seiten. URLs,
  Produktspezifikationen und das Design bleiben unverändert.
- Verifizierungs-Tags für Google Search Console und Bing Webmaster Tools:
  Wert in `core.py` eintragen (`GOOGLE_SITE_VERIFICATION`,
  `BING_SITE_VERIFICATION`), das Tag erscheint dann auf jeder Seite.
  **Vorzuziehen ist der DNS-Weg** — ein TXT-Eintrag in der Zone bei Infomaniak.
  Er verifiziert die ganze Domain auf einmal, mit und ohne `www`, überlebt jeden
  Umbau am Generator und hängt nicht daran, dass ein Tag im `<head>` stehen
  bleibt. Die beiden Felder bleiben dann leer und im `<head>` steht kein
  Verifizierungs-Tag — das ist der gewollte Zustand, kein Versehen.
- CSS/JS mit `?v=<hash>` — sonst liefern Browser nach einem Deploy die alte Datei

**Verfahrenssymbole und Bildlinks (07.10.2026):** Die Herstellerkacheln in
`procs_block()` und der Merkmalsliste erhalten den korrekten lokalisierten
Alternativtext aus `featLabel()`. Weil derselbe Text unmittelbar daneben steht,
bleiben diese nicht interaktiven Bilder mit `aria-hidden="true"` fuer
Screenreader ausgeblendet. So entfaellt Bings Hinweis auf leere Bildtexte,
ohne die Beschriftung doppelt vorzulesen. Separate Bildlinks in der Anfrageliste
haben einen zugaenglichen Namen aus Produkt und gegebenenfalls Variante.

Die Miniaturen der MLF-100-Bildergalerie verwenden seit dem 08.10.2026 den
vollstaendigen lokalisierten Alternativtext des zugehoerigen Bildes. Sie sind
funktionale Tab-Auswahlelemente und nicht dekorativ; ihr Name haengt deshalb
nicht nur vom gekuerzten Maus-Tooltip ab. Tab-/Panel-Zuordnung, Pfeiltasten und
sichtbare Bilder bleiben unveraendert.

**Preis auf Anfrage und strukturierte Daten (07.10.2026):** Der Katalog gibt
bewusst keine `Product`-Rich-Result-Auszeichnung mehr aus. Google verlangt fuer
[Product-Snippets](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)
neben dem Namen mindestens ein echtes Angebot oder geeignete Bewertungen;
ein `Offer` braucht einen tatsaechlichen Preis. Der bisherige `Product` ohne
Angebot war deshalb fuer diese Google-Erweiterung unvollstaendig, auch wenn
schema.org allein kein solches Pflichtfeld verlangt. Niemals einen Preis von
0, eine Platzhalter-Offerte oder erfundene Bewertungen einsetzen.

`render.py::ld_catalog_item()` beschreibt den Katalogeintrag jetzt als
[`Thing`](https://schema.org/Thing). Die vorhandene `ItemPage.mainEntity`
verweist weiterhin auf dessen stabile Kennung `Produkt-URL#product`;
`mainEntityOfPage` verweist zurueck auf `Produkt-URL#webpage`. Der Fragmentname
`#product` ist eine Kennung, kein Schema-Typ. Erhalten bleiben Name,
Alternativnamen, Beschreibung, URL und Originalfoto. Die echte interne
Referenz steht als `identifier` mit `PropertyValue.propertyID: "VES-TECH"`;
nur bei hinterlegter Hersteller-Artikelnummer kommt ein zweiter Identifier
mit `propertyID: "MPN"` hinzu.

Produktbezogene Eigenschaften wie `brand`, `manufacturer`, `model`, `sku`,
`mpn`, `category`, `itemCondition` und `additionalProperty` gehoeren nicht an
den allgemeinen `Thing`-Typ und werden dort nicht ausgegeben. Ebenso wenig
bleiben versteckte `ProductModel`-Untertypen oder Preis-/Bewertungsobjekte im
Graphen. `check.py` prueft diese Grenze auch in verschachtelten Objekten.
`inLanguage` bleibt an der `ItemPage`, nicht am `Thing`.

Dies ist ein bewusster Verzicht auf Product-Rich-Results, keine Ersatzmethode
fuer deren Freischaltung. Technische Tabellen, Besonderheiten, Marken und
Modellzuordnung, Occasion-Zustand, „Preis auf Anfrage“ und die Anfrageliste
bleiben im sichtbaren HTML und im eigenstaendig versionierten
`data/products.json` erhalten. Dessen `price.model: "on-request"` ist kein
Schema.org-Angebot und kein numerischer Verkaufspreis. Liefergebiet CH/LI
bleibt am `Organization`-Knoten. Normale Indexierung wird durch eine fehlende
Product-Rich-Result-Berechtigung nicht gesperrt; die Umstellung verspricht
keine Indexierung oder Rankings. Historische Search-Console-Meldungen koennen
bis zum erneuten Crawlen und Verarbeiten bestehen bleiben.

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

**Auswahl und Navigation (19.10.2026):** Die Produkttexte aus
`PRODUCT_GUIDES.json` werden als eigener sichtbarer Abschnitt nach den
technischen Reitern ausgegeben, ohne JavaScript oder einen weiteren Reiter.
Sie erläutern den Einsatz, Unterschiede zwischen Baureihen und die Angaben
für eine konkrete Anfrage. Zahlen und Zuordnungen stammen aus dem vorhandenen
Katalog und seinen Herstellerunterlagen. Neue Leistungswerte, Bestände,
Zertifizierungen und Kundenreferenzen werden daraus nicht abgeleitet.
`GUIDE_LINKS.json` verknüpft die Auswahlhilfen mit passenden nächsten Seiten.
`core.editorial_target()` löst ausschliesslich bekannte, sprachgleiche Routen
auf; `validate_editorial_guides()` prüft die Daten vor dem Löschen generierter
Seiten. Die Herstellerzuordnung in `ACC.json` bleibt unabhängig davon.
Die Serviceübersicht erhält vorbereitende Hinweise und den Ablauf der
Geräteannahme aus `i18n_extra.json::svc_body`; Standortwerte stammen aus
`WORKSHOP`. Unternehmensseite und Impressum verlinken Kontakt und Katalog.
Unveränderte Produktseiten erhalten auch durch leere optionale Abschnitte
keine zusätzliche Leerzeile und keinen neuen Inhaltsstempel.

Damit die Geräte in ChatGPT-, Claude-, Perplexity- und Google-AI-Antworten auftauchen:

- **`/llms.txt`** — kompakte Landkarte der Website im llms.txt-Format
- **`/llms-full.txt`** — der komplette zitierfähige Inhalt in einer Datei:
  alle 81 Produkte mit Beschreibung, Besonderheiten, technischen Daten und Zubehör,
  dazu 19 erklaerte Verfahren/Funktionen und alle 10 FAQ-Antworten
- **`/data/products.json`** — maschinenlesbarer Katalog, viersprachig, mit
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

**Kompakte Benachrichtigungen (21.10.2026):** Kontaktangaben erscheinen einmal
im Text, gefolgt von der gewählten Produkt-/Variantenbezeichnung mit Menge oder
der Dienstleistung, der Kundennachricht und ausschliesslich ausgefüllten,
passenden technischen Angaben. Leere optionale Angaben, Produkt-/Seiten-URLs,
Besuchs- und Kampagnendaten entfallen. Alle fünf Sprachen verwenden dieselbe
Struktur. Der Absendername ist fest `VES-TECH Swiss`; die bereinigte Kundenadresse
steht im reservierten Web3Forms-Feld `replyto`. Zusätzliche Felder `email` und
`phone` werden nicht parallel geschickt. Die Anbieterhülle/Einleitung stammt
weiterhin von Web3Forms und ist keine eigene HTML-E-Mail-Vorlage. Der Browser
prüft die E-Mail-Gültigkeit; Name und Telefon akzeptieren keine Steuerzeichen.
Kopierbarer Fehlerentwurf und bestätigte Zusammenfassung enthalten exakt den
Geschäftstext des jeweiligen Versands. Die Datenschutzhinweise nennen nur die
tatsächlich gesendeten Geschäftsangaben.

## 11. Design

Am 19.10.2026 hat der Inhaber nach den Bildentwürfen für Startseite,
Produktdetail, Verfahren und Service den Stil **VOLT** für den kompletten
Auftritt in DE/FR/IT freigegeben. Er ersetzt den zuvor gewählten warmen Stein.
Die Umsetzung bleibt echtes vorgerendertes HTML, keine Abbildung einer Seite.

```
--bg:#F4F6F7 --bg2:#E9EDF0 --panel:#FFFFFF --panel2:#F0F3F5
--line:#B5BEC6 --accent:#FF5B0A --accent-ink:#AE3500
--ink:#14181D --muted:#52616D
```

Helle silbergraue Flächen, geometrische orange Felder und feine Leiterzüge
verbinden Elektronik, Schweissen, Schneiden, Reinigung und Automation.
`assets/icons/design/` enthält die eigenen Vektoren für Felder, Trennlinien
und neunfach skalierte Eckrahmen. Die Rahmen liegen auf einer dekorativen
Ebene; Text, Formulare und Tastaturmarkierungen werden nicht abgeschnitten.
Alle Seitentypen erhalten dieselbe Sprache, mit passenden Layouts für ihren
Inhalt. Auf Mobilgeräten bleibt der Einstiegstext auf hellem Grund.

Inter bleibt für Überschriften, Fliesstext und Bedienung; Barlow Condensed
700 für kompakte Kartenüberschriften und Anton für die Wortmarke. Alle
Schriften liegen lokal. Fliesstext ist überwiegend 16 px, Produktlead 18 px,
mobil 17 px. Die Wortmarke erhält den Zusatz SWISS. Originale Herstellerfotos,
Bedienpanels und farbige Social-Logos werden weder getönt noch neu gezeichnet.
Die Startseite zeigt HyperMIG TWIN, Theta 60 HSC und HyperCleaner ST mit echten
Links, Anfragepreis und unveränderten Herstellerabbildungen auf weissen Flächen.
Die bisherigen Hero-Dateien bleiben für Vorschau-Metadaten erhalten.

Auf Wunsch des Inhabers wechselt der grosse Produktbereich seit demselben Tag
alle **3 Sekunden**. `core.HOME_FEATURED` enthält in dieser Reihenfolge
MPT 3001, HyperMIG TWIN, HyperTIG AX, HyperTIG DX, Omega AX und Beta DX.
Omega AX und Beta DX zeigen die bestätigte Netzangabe 1~ 230 V; die HyperTIG-
Modelle bleiben bei ihren eigenen 400-V-Angaben. Jeder Eintrag behält Bild,
Produktname, Preis auf Anfrage und den sprachgleichen Produktlink gemeinsam.
Auf ausdrücklichen Wunsch des Inhabers vom 19.10.2026 zeigt der Produktwechsel
auf der Startseite in DE/FR/IT/EN keine Bildunterschrift unter der MPT-Illustration.
Der weisse Bildrahmen enthält nur das Bild und reserviert keinen Fussnotenplatz.
Seit dem 20.10.2026 entfallen auf ausdrücklichen Wunsch des Inhabers auch
die vollständigen Bildunterschriften unter MPT 3001 und MPT 2501 auf den
Produktdetailseiten in DE/FR/IT/EN/ES. Beide Einträge sind aus `IMGCAP.json`
entfernt; der normale bildabhängige Rahmen reserviert keinen Beschriftungsplatz.
Theta 60 HSC und HyperCleaner ST bleiben darunter als direkte Produktkarten.

Die Bühne reserviert den Platz aller sechs Bilder, ohne Layoutsprünge beim
Wechsel. Nur das erste Bild hat hohe Ladepriorität; die übrigen werden mit
niedriger Priorität vorgeladen. Vor/Zurück, Produktauswahl und Pause/Weiter
sind per Tastatur und Touch erreichbar. Tastaturfokus, ein Hintergrundtab
oder reduzierte Bewegung verhindern automatische Wechsel. Bei reduzierter
Bewegung kann die Person die Diaschau ausdrücklich starten. Ein manueller
Pausenwunsch bleibt erhalten. Automatische Wechsel erzeugen keine fortlaufenden
Screenreader-Meldungen; inaktive Produkte sind unsichtbar und inert.
Ohne JavaScript stehen alle Produkte statisch und mit benutzbaren Links im HTML.

Zwei neu erzeugte redaktionelle Makromotive illustrieren Elektronikdiagnose und
Schweissen unter `assets/img/design/volt-*.webp`. Sie dienen ausschliesslich als
dekorative Bilder, niemals als eigene Werkstatt-, Personen- oder Produktfotos.
Prompts, Herkunft und Abmessungen stehen in `build/volt_assets.json`.

Der Verfahrenseinstieg zeigt alle 19 Einträge mit Kurztext und Anker zur
vollständigen Erklärung. Vorhandene Herstellerzeichen bleiben erhalten;
HyperForce, HyperCold und HyperRoot nutzen das originale Kombinationssymbol.
Ohne Herstellerzeichen wird kein fiktives Zeichen ergänzt. Vergleich, FAQ,
Parameter, Quellen und alle bisherigen Anker bleiben vorgerendert erhalten.

HyperMIG X und TWIN erhalten zusätzlich einen sichtbaren, eigenen Block zum
neuen X-Panel. Bild, Bedienbeschreibung und 99 JOB-Speicher folgen den bereits
geprüften Unterlagen. Der Link öffnet den vollständigen Ratgeber im bestehenden
Produktreiter. Keine neuen Verfügbarkeits-, Nachrüst- oder Prozesszusagen.

Die Serviceübersicht enthält die vier Schritte Anfrage, Diagnose, Abstimmung
und Reparatur. Die Kontaktseite nennt Martin Veselovsky ausdrücklich als
Einzelunternehmen (FR: entreprise individuelle; IT: ditta individuale) und
unterscheidet unverändert Rechnungsadresse und Partnerwerkstatt.

Die sechs Desktop-Hauptlinks bleiben ab 1040 px sichtbar, darunter das
vollständige Menü. Orange Hover- und Fokusflächen, Suche, Anfragekorb,
Galerien, Tastaturbedienung und Formulare bleiben erhalten. Reduzierte
Bewegung wird respektiert; vorhandene Tabellen dürfen in ihrer eigenen
Region horizontal scrollen. Sicherheitsrichtlinie, Datenschutzgrenzen,
URLs, Canonicals und Sprachalternativen bleiben bestehen.

Der Produktkopf zeigt die Anfrage vor den ausführlichen Verfahrenssymbolen.
`core.quickFacts()` ergänzt höchstens drei belegte technische Eckdaten:
Jeder Wert muss in allen Spalten aller zugeordneten Herstellertabellen gleich
und bestätigt sein. Fehlende Zellen und unbestätigte Einheiten werden nicht
ergänzt; widersprüchliche CWK-Absicherungen werden nicht zusammengezogen.
Ohne Herstellertabelle werden bestehende redaktionelle Merkmale verwendet.
Der Link zur vollständigen Datentabelle öffnet deren Reiter über `#tab-tech`.
Es werden keine neuen Leistungswerte, Ausstattungszusagen oder Preise erfunden.

**Optionale Statistik mit Zustimmung.** Ahrefs und Cloudflare Web Analytics laden erst nach
aktiver Zustimmung, mit gleichwertiger Ablehnen-Option und dauerhaft erreichbaren
Datenschutzeinstellungen in der rechtlichen Fusszeile. Die Zustimmung läuft nach 180 Tagen ab. Die Anfrageliste
und die Statistik-Auswahl liegen getrennt in localStorage. Ahrefs misst den Weg
von Produktauswahl bis bestätigtem Formularversand, Cloudflare Ladezeiten.
Die neue Zustimmung ist v2; ein früherer Cloudflare-Grant gilt dafür nicht.
Registrierte Kampagnen werden maximal 24 Stunden in sessionStorage zugeordnet.
Details, Ereignisdefinitionen, SDK-Prüfsumme und Datenschutzgrenzen: README.md.

Seit dem 21.10.2026 zeigt die Einwilligung einen kurzen Einstieg «Ihre Privatsphäre»
mit gleichwertigen Aktionen «Ohne Analyse» und «Analyse erlauben».
Anbieter und Speicherfrist stehen in einem nativen Details-Bereich, die
Datenschutzerklärung bleibt direkt verlinkt. Die Einstellungen lassen sich
ohne Änderung schliessen (auch per Escape); der Fokus kehrt zur Fusszeile zurück.
Die aktuelle Auswahl wird beim erneuten Öffnen genannt. GPC/DNT verhindern
weiterhin jedes Laden; bei solchem Browsersignal wird keine erste Aufforderung
angezeigt und die gesperrte Analyse in den Einstellungen erklärt. Alle Texte
und die Datenschutzverweise gelten in DE/FR/IT/EN/ES. Umfang, Anbieter und
180-Tage-Frist bleiben unverändert, vorhandene Entscheidungen werden respektiert.

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

Die Kurzangabe zur Netzversorgung der Delta 1800 wurde am 20.10.2026 von
„230/400 V“ auf „1~ 230 V“ korrigiert. Sie muss zur einzelnen Modellspalte
1800 in `build/mahe_specs.json` passen, nicht zu anderen Delta-Baureihen.
Quelle: MAHE Delta, technisches Datenblatt und Bedienungsanleitung
(`https://mahe-online.de/delta/`, `https://mahe-online.de/wp-content/uploads/2022/07/Delta_DE.pdf`).
Die zentrale Korrektur in `data/P.json` gilt für Karten, Produktseiten und
Suchdaten in DE/FR/IT/EN/ES; historische Quellsnapshots bleiben unverändert.

## 14. Harte Regeln beim Erweitern

1. **Inhalt kommt aus `data/`**, niemals direkt ins generierte HTML schreiben —
   der nächste Build überschreibt es.
2. **Keine Preise.** Immer „Preis auf Anfrage", kein `price` im JSON-LD.
3. **Jeder neue Text in DE + FR + IT + EN + ES**, Schweizer „ss".
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
    in `HL`/`HL_CLEAN`/`PANEL_HL` übernommen, in allen konfigurierten Sprachen.
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
   Marke, die Geschäfts- und Kundenbeziehungen und der Rang bei Google.
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
- Hersteller-Artikelnummern nur bei tatsächlich hinterlegtem Originalwert.
  Eine interne Produkt-ID ist kein MPN. Seit dem 07.10.2026 stehen belegte
  Nummern als `Thing.identifier` statt `Product.mpn` im neutralen Katalogmarkup.
  Keine erfundenen Ratings für Rich Results.
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

Nachpruefung am 20.10.2026: HTML-Ueberschriften im VOLT-Regressionstest werden
mit `HTMLParser` statt mit zwei potenziell quadratischen regulaeren Ausdruecken
gelesen. Konto-Befunde und private Pruefprotokolle bleiben unter dem von Git und
Deployment ausgeschlossenen `reports/`; sie gehoeren nicht in diese oeffentliche
Projektdokumentation. Ein erfolgreicher CodeQL-Job ist nicht gleichbedeutend mit
null offenen Befunden: der Alert-Status muss gesondert geprueft werden.

Die PageSpeed-Nachpruefung ergaenzt bei MPT 3001/2501 die Bildstufen 600/800 px
und beim Schulungsdokument 720/1200 px. `build/responsive_images.py` erzeugt sie
reproduzierbar aus per SHA-256 festgelegten lokalen WebP-Mastern; vorhandene
Zoom-Originale bleiben unveraendert. `build/panels.py` behaelt die MPT-Stufen
auch bei einem erneuten Herstellerimport. `build/pages.py` beschreibt mit
`sizes` die sichtbare Bildbreite nach `object-fit:contain`, nicht nur die
breitere Rasterzelle. Das gilt in allen fuenf Sprachfassungen und aendert weder
Produktfoto noch Gestaltung. Normale Builds brauchen keinen Bildkonverter.
HTTP-Cache und fehlende Header des Pages-Hostings werden nicht durch Meta-Tags
oder einen Service Worker scheinbar behoben; Grenzen stehen in SECURITY.md.

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
- `build/local_paths.py` begrenzt CLI-Dateizugriffe auf Projekt, persoenliche
  Dokumentordner, temporaere Ablagen und `/Volumes`; in Actions zusaetzlich
  `RUNNER_TEMP`. Aufgeloeste Symlinks muessen ebenfalls darin liegen.
  Exporte haben feste SQL-/SQLite-Endungen, oeffentliche Dateiunterpfade duerfen
  keine Symlinks enthalten. Weitere Grenzen stehen in SECURITY.md/BACKUP.md.
- `build/backup.py`: lokale Quell-/Git-/Release-Sicherung oder ausdrücklich
  öffentlicher Release-Modus. SHA-256, Pfadkontrolle und reale Wiederherstellung
  gehören zur Prüfung. CI bewahrt oeffentliche Actions-Archive 7 Tage auf und
  veroeffentlicht nach erfolgreichem Deploy mit `build/release_recovery.py`
  zusaetzlich ein geprueftes Release am exakten Commit-Tag, ohne diese
  Actions-Ablauffrist. Nur oeffentliche Dateien, serverseitiger SHA-256-Abgleich,
  erneuter Restore-Test, keine Ueberschreibung vorhandener Assets. Temporaere
  Testdateien werden entfernt; keine laufend wachsenden Notebook-Backups.
  Seit 20.10.2026 hält `build/prune_recovery.py` nach erfolgreicher Veröffentlichung
  nur das aktuelle und das neueste vorherige eindeutig zugeordnete Recovery-Release.
  Vor jeder Bereinigung: vollständige Assets/Hashes, exakte Tags, erfolgreiche
  Main-Deployments, gemeinsame Historie und unveränderter Main-Stand. Fremde,
  umbenannte oder unvollständige Releases bleiben bestehen. Git-Tags und Commits
  bleiben erhalten. Ohne `--delete` wird nur der Plan angezeigt.
- Keine privaten Backups, Konfigurationen oder Kontoberichte in öffentliche
  Actions-Artefakte. Ein lokales Backup auf derselben Festplatte ist keine
  unabhängige Katastrophensicherung. Betriebsanleitung: BACKUP.md und SECURITY.md.

## 19. Sprachpflege und stabile Adressen (21.09.2026)

- Vollständige Sprachprüfung der gepflegten DE-, FR- und IT-Texte: Produktbeschreibungen,
  Merkmale, Auswahlhilfen, Dienstleistungen, FAQ, Formulare und Rechtstexte.
  Sprachkorrekturen sind keine neue rechtliche Prüfung oder Zusage technischer Eigenschaften.
- Die deutsche Einleitung beginnt mit «VES-TECH Swiss bietet Beratung und Verkauf
  von MAHE-Geräten.»; kein Doppelpunkt unmittelbar nach MAHE. Alle vier Bereiche
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
  Die ursprünglich vorgesehenen Bildunterschriften bei MPT 3001 und MPT 2501
  entfallen seit der ausdrücklichen Vorgabe vom 20.10.2026 in allen Sprachen;
  die aktuelle Darstellung ist in §11 beschrieben.


## 21. Marketing und Occasion-Bezeichnungen (22.09.2026)

- PSHB 125 hat sprachbezogene 1200 × 630 Open-Graph-/Twitter-Karten unter
  `assets/img/social/`, damit die ganze schmale Brennerfotografie sichtbar bleibt.
  `build/pshb_social_card.mjs` erzeugt SVG und PNG aus dem Originalfoto und
  `data/SOCIAL_CARDS.json`, prüft unveränderte Bildpixel und sichtbaren Bildinhalt.
  `render.product_social_image()` wählt nur diese Vorschau aus; Galerie,
  `Thing.image` und `ItemPage.primaryImageOfPage` bleiben Originalfotos.

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


## 22. Fachratgeber Schweissverfahren (19.10.2026)

`data/PROC.json` enthaelt 19 Eintraege mit stabiler `id`, Gruppe,
Herstellersymbol (optional), Kurztext, Wirkprinzip, Anwendung, Einstellhinweisen,
Geraeteverweisen und Quellenzuordnung, jeweils vollstaendig in DE/FR/IT.
`data/PROCESS_GUIDE.json` pflegt Vergleichstabelle, Inhaltsverzeichnis-Gruppen,
Parametererklaerungen, sechs sichtbare FAQ und technische Quellen.
`core.validate_process_guide()` prueft Uebersetzungen und Verweise vor dem Build.

Die drei bisherigen Verfahren-URLs bleiben bestehen. Alles ist vorgerendert;
Suchergebnisse fuehren direkt zum Prozessanker und durchsuchen den vollen Text.
`llms-full.txt` uebernimmt die Erklaerungen. Die Seite nutzt die vorhandenen
Herstellerbilder aus FEAT.img statt leerer FEAT.svg-Platzhalter. Unbelegte
Wirkungsgrad-, Zeitersparnis- und Verzugsgarantien werden nicht ergaenzt.
20-kHz-Pulsen wird ausdruecklich auf Beta DX pro/Omega AX pro bezogen; HF-Zuendung,
Pulsfrequenz, AC-Frequenz und AC-Balance werden getrennt erklaert. Quellen fuer
allgemeine Wirkprinzipien bestaetigen keine fremden MAHE-Einstellbereiche.

## 23. Vollständige englische Fassung (19.10.2026)

- EN ergänzt DE/FR/IT auf ausdrücklich gewünschten 122 eigenen Inhaltsseiten.
  Insgesamt 488 Inhaltsseiten, eine gemeinsame 404-Seite, 15 bestehende
  Weiterleitungen und die Google-Verifizierungsdatei; 476 indexierbare URLs.
  Alle bestehenden DE-/FR-/IT-Adressen bleiben erhalten. Englisch verwendet
  `/en/`, `en-CH`, die Segmente aus `SEG` und eigene Kategorie-/Unterkategorie-
  Slugs; Produkt-IDs und Prozessanker bleiben stabil.
- Die gepflegten JSON-Dateien und `i18n_extra.json` enthalten vollständige
  EN-Texte, einschliesslich aller 81 Produkte, technischen Zeilen, Merkmale,
  Bedienpanel-Ratgeber, 19 Prozesse, Auswahlhilfen, Service, FAQ, Formulare
  und Rechtstexte. Britische Schreibweise: aluminium, colour, metre, enquiry.
  WIG wird als TIG übersetzt; Modellnamen bleiben erhalten. `trV()` stellt
  Dezimalzahlen auf Englisch mit Punkt dar, ohne die Werte zu verändern.
  Hersteller-PDFs bleiben unverändert in ihren vorhandenen Sprachen; die
  Downloadbeschriftung weist auf deutschsprachige Originalunterlagen hin.
- `core.validate_translations()` prüft vor dem Löschen generierter Dateien
  fehlende Sprachfassungen, Struktur, leere Texte und Formatplatzhalter.
  Die zusätzliche Regression prüft numerische Übereinstimmung aller
  Produktbeschreibungen und technischen Tabellen sowie kritische Unterschiede
  bei Netzspannung, Polierleistung, Einschaltdauer und Pulsfrequenzen.
  Einzahlformen für Modell-/Artikelzahlen werden über `t(..., n=1)` gewählt.
- Sprachlinks behalten dieselbe Seite und geprüfte Anfrageparameter. Vier
  kleine farbige Vektorflaggen (DE/FR/IT/GB für EN) werden aus
  `assets/icons/flags/` direkt ins HTML eingefügt. Keine zusätzlichen
  Bildanfragen, Emoji-Abhängigkeit oder externe Flaggenbibliothek. Die Kürzel
  bleiben sichtbar, native Sprachnamen stehen im zugänglichen Linknamen,
  die Flaggen sind dekorativ. Mobil bleiben alle Ziele mindestens 44 px gross.
- Englisch erhält `search-en.json` mit eigenen Produkt-/Service-/Prozesstexten
  und zusätzlichen englischen Fachsynonymen. Geladen wird weiterhin nur der
  aktuelle Suchindex und erst beim Benutzen der Suche. `norm()` bleibt unverändert.
  Englische Vorschaukarte für PSHB 125 aus demselben unveränderten Originalfoto;
  `node build/pshb_social_card.mjs en` baut nur diese Sprachfassung.
- Hreflang, Sitemap, JSON-Katalog, Sprachparität, IndexNow, bekannte
  Analytikpfade, SQL-Export und öffentliche Recovery-Sicherung umfassen EN.
  Analytics- und Formulardatenschutz bleiben gleich; EN wird als eigene Sprache
  erkannt. Geschriebene Vertragsbedingungen bleiben inhaltlich erhalten,
  lediglich die Liste vorhandener Website-Sprachen umfasst nun Englisch.
- Keine Übersetzung zur Laufzeit und keine neue Framework-/JavaScript-Laufzeit.
  Gerätebilder, Fonts und `app.js` werden wiederverwendet. Ladegrössen und
  repräsentative Ansichten werden vor dem Deploy mit dem bisherigen Stand
  verglichen. Quellcode und Release-Sicherung werden nach bestandenen Checks
  am exakten Commit auf GitHub gespeichert; kein lokaler Backup-Archivzuwachs.

## 24. MAHE MG500 im Sortiment (19.10.2026)

- Neuer Katalogeintrag `mg500` unter Zubehör / Brenner in DE/FR/IT/EN.
  Herstellerquelle: `https://mahe-online.de/hypermig/`, Abschnitt Zubehör,
  Schweissbrenner / MG500. Bestätigt sind wassergekühltes MIG/MAG, 500 A
  bei 60 % Einschaltdauer, Grafikdisplay, Fernbedienung und 4 m Länge.
- Der Wert gehört zum Brenner. Keine unbekannte Gasart, Drahtabmessung,
  100-%-Belastbarkeit, Funkverbindung oder universelle Maschinenkompatibilität
  ergänzen. `ACC.json` verbindet ihn ausschliesslich mit der belegten
  HyperMIG-X-Familie; Anschluss, Steuerung und Kühlung werden konkret abgestimmt.
- Das vom Inhaber bereitgestellte vollständige Foto bleibt unverändert im Motiv.
  Lokale WebP-Stufen: 400 und 864 px, ohne Hochskalierung. Manifest mit
  Quellnachweis und SHA256; Produktfoto, Zoom, Suche und Anfrageliste verwenden
  dieselbe Aufnahme. Lokale 1200 × 630 Linkvorschauen enthalten das komplette
  Foto ohne Beschnitt und werden ausserhalb des Browsers erzeugt.
- Produktbeschreibung, Merkmalswerte und Auswahlhilfe sind in allen vier
  Sprachen gepflegt. Kategorie, Suchindizes, Anfragekatalog, Hreflang, Sitemap,
  IndexNow und Recovery nehmen den Eintrag über den normalen Build auf.
  Aktueller Umfang: 81 Produkte, 122 Inhaltsseiten je Sprache und 476 Sitemap-URLs.

## 25. Persönliche MAHE-Geräteschulung (20.10.2026)

- Das vom Inhaber bereitgestellte Schulungszertifikat für Martin Veselovsky
  erscheint auf Startseite, Über-uns-Seite und Serviceübersicht in DE/FR/IT/EN.
  Angaben in `data/TRAINING.json`: MAHE GmbH, Kreuztal, 09.07.2026,
  MH-2026-8942, Schweisstechnologie und Systemtechnik. Beschrieben werden
  Bedienung, Parametrierung, Prozesssteuerung, Wartung und Qualitätssicherung.
- Es ist eine persönliche Teilnahmebescheinigung. Daraus weder eine offizielle
  Händler-/Serviceautorisierung noch eine EN-1090-Unternehmenszertifizierung,
  Schweisserprüfung oder sonstige Akkreditierung ableiten. Das Dokument stammt
  vom Inhaber; eine unabhängige Bestätigung des Ausstellers wird nicht behauptet.
- Vollständiges Motiv ohne Beschnitt, Textänderung oder Hochskalierung; lokale
  WebP-Stufen 480/960/1448 px unter `assets/img/company/`, Manifest mit SHA256 der
  gelieferten Quelldatei. Lazy Loading und vorhandene barrierefreie Bildlupe;
  keine neue Bibliothek, kein zusätzlicher JavaScript-Code. Die Quelldatei
  verbleibt im privaten Downloadordner; Recovery enthält nur die Webfassungen.

## 26. Redaktionelle Zeichensetzung (20.10.2026)

- Der Fachgebietszeile unter der Startseitenüberschrift fehlen auf ausdrücklichen
  Wunsch des Inhabers die bisherigen Trenn- und Schlusspunkte. In DE/FR/IT/EN
  steht eine natürliche Aufzählung mit Kommas und der jeweiligen Konjunktion;
  keine abschliessende Satzinterpunktion an dieser nominalen Zeile.
- 11'390 Zeichenketten der gepflegten Datenquellen wurden auf doppelte Zeichen,
  falsche Abstände, fehlende Trennung, Satzenden und auffällige Kommas geprüft.
  Verdächtige Stellen wurden im vollständigen Satz redaktionell beurteilt.
  Rechtschreibbedingt nötige Kommas vor Konjunktionen, Dezimalzeichen,
  Abkürzungen, Adressen, Modellbezeichnungen und Herstellerwerte bleiben erhalten.
- 19 gezielte Textanpassungen betreffen Einstieg, einzelne FAQ-/Service-Sätze,
  Bildunterschriften und Auswahlhilfen. Unter anderem entfällt die englische
  Kommatrennung zwischen zusammengesetztem Subjekt und Prädikat in der
  Aluminium-FAQ. Keine pauschale Ersetzung im gesamten Katalog oder in Rechtstexten.
- Änderungen erfolgen ausschliesslich in gepflegten Quellen. Der normale Build
  aktualisiert HTML, Metadaten, Suche und lesbare Katalogexporte; keine zusätzliche
  Browserlogik, keine neuen Bilddateien und keine Änderung technischer Zahlenwerte.


## 27. Vollständige spanische Fassung (20.10.2026)

- ES ergänzt den gesamten Auftritt um 122 eigene Inhaltsseiten unter `/es/`.
  Aktuell 610 Inhaltsseiten in DE/FR/IT/EN/ES, eine gemeinsame 404-Seite,
  15 bestehende Weiterleitungen und die Google-Verifizierungsdatei; 595
  indexierbare Sitemap-URLs. Bestehende Adressen und Produkt-IDs bleiben stabil.
  Sprachkennzeichnung `es-CH`, eigene lesbare spanische Segmente in `SEG`,
  `CAT_SLUG`, `SERVICE_SEG` und `subcategory_slugs.json`.
- Vollständige gepflegte Übersetzung aller 81 Produktbeschreibungen, Merkmale,
  technischen Tabellen, Bedienpanel-Ratgeber, 19 Prozesse, Auswahlhilfen,
  Schulungsnachweise, Service, FAQ, Formulare und Rechtstexte. Modellnamen,
  Herstellerangaben, Vertragsinhalt und technische Zahlenwerte bleiben erhalten.
  Spanische Dezimalzahlen verwenden das Komma; WIG wird als TIG beschrieben.
  Die Fachgebietszeile bleibt eine natürliche Aufzählung ohne Schlusspunkt.
- Es handelt sich um ein Einzelunternehmen von Martin Veselovsky. Persönliche
  Beratung bleibt auf Deutsch, Tschechisch und Englisch angegeben; die neue
  Website-Sprache behauptet keine zusätzliche gesprochene Beratungssprache.
  Schulungszertifikat und Herstellerrollen behalten ihren bisherigen Umfang.
  Spanische Rechtstexte verlinken ihre entsprechenden spanischen Seiten.
- Fünf dekorative lokale Vektorflaggen in der Sprachauswahl; ES nutzt Rot/Gelb.
  Gleichbleibende Seiten und geprüfte Anfrageparameter werden beim Wechsel
  erhalten. Kein externer Übersetzungsdienst, keine zusätzliche Laufzeit.
  Gerätefotos, Fonts, Designsystem und Bedienlogik werden wiederverwendet.
- `search-es.json` enthält Produkte, Service und ausführliche Prozesse. Nur der
  aktuelle Suchindex lädt bei Bedarf. Spanische Fachsynonyme und identische
  Python-/JavaScript-Normalisierung für á/í/ó/ú/ñ ermöglichen die Suche mit und
  ohne Akzente. Hersteller-PDFs bleiben Originale mit sprachrichtigem Hinweis.
  Der Dokumentimport berücksichtigt alle konfigurierten Sprachen.
- `validate_translations()` prüft Struktur, Vollständigkeit und Platzhalter
  aller fünf Sprachen, einschliesslich verschachtelter gemeinsamer Metadaten.
  Regressionen prüfen Wertparität, Sprachrouten, Formulare, Suche, Analytik und
  öffentliche Wiederherstellung. Hreflang, Sitemap, JSON-/SQL-Katalog, IndexNow,
  Sprachstatistik, Vorschaukarten und Recovery-Allowlist umfassen ES.
- Quellcode liegt nach bestandenen Prüfungen auf GitHub. Das öffentliche
  Recovery-Archiv wird am exakten Commit erstellt und vor dem Deploy
  wiederhergestellt/geprüft; kein zusätzliches lokales Backup-Archiv.

## 28. Anwendungsbezogene Suche und Anfragen (21.10.2026)

- Die interne Suche durchsucht auch die bereits sichtbaren Auswahlhilfen aus
  `BUYING_GUIDE`, `SUBCATEGORY_GUIDES` und `PRODUCT_GUIDES`. Diese Texte bleiben
  im niedrig gewichteten Beschreibungsfeld. Titel, Modelle und technische
  Daten behalten ihre bisherige Gewichtung; keine versteckten Branchen-Keywords.
  Unterkategorie-Treffer zeigen ihre eigene Einleitung statt einer leeren
  Beschreibung. Die mit einem Produkt kollidierende Plasma-TIG-Unterkategorie
  wird nicht noch einmal als separater Suchtreffer ausgegeben.
- Bestehende WIG-/TIG- und Cleaner-Seiten erhalten in allen fünf Sprachen
  passende Metadaten und konkrete Auswahlkriterien für Rohrleitungsbau,
  Montage und elektrolytische Nahtreinigung. Bestehende URLs bleiben erhalten;
  keine regionalen Dubletten oder neuen Leistungs-/Zertifizierungszusagen.
  Beta DX bleibt DC/230 V, Omega AX AC/DC/230 V. Hinweise zu Rohrgeometrie,
  Stromversorgung, Brenner und Formiergas sind Qualifizierungsfragen,
  keine Zusage einer bestimmten Verfahrensfreigabe.
- Das vorhandene optionale Feld `application` wird bei Geräteanfragen und
  Automation eingeblendet. Es bleibt auf 300 Zeichen begrenzt, ohne URL-,
  Analytics- oder LocalStorage-Speicherung. Bei Zubehör oder anderen
  Servicekontexten wird ein unpassender Entwurf weiter vom Versand ausgeschlossen.
- Keine neuen Browserbibliotheken, Tracker, Schrift- oder Bilddateien. Der
  Suchindex wird unverändert erst bei Benutzung geladen. Private Kundenanalyse
  und Kampagnenentwürfe bleiben unter dem ausgeschlossenen `reports/`.
