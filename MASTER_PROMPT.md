# MASTER PROMPT — VES-TECH Swiss (v2)

> **Was das hier ist:** Die verbindliche Beschreibung der Website `www.ves-tech.ch`.
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
  - Bildfelsstrasse 24, 9552 Bronschhofen (SG), Schweiz
  - +41 76 710 91 39 · `vestechswiss@gmail.com` · Mo–Fr 07:30–17:30
  - (`info@ves-tech.ch` erst wieder eintragen, wenn die Domain samt Postfach steht)
- **Keine Preise.** Jedes Gerät zeigt „Preis auf Anfrage". Kundschaft sammelt Geräte
  in der **Anfrageliste** und schickt eine gebündelte Anfrage.
- **Dreisprachig DE / FR / IT**, Deutsch ist Standard. **Jeder** neue Text existiert in
  allen drei Sprachen. Schweizer Schreibweise: **„ss" statt „ß"** („Schweissen",
  „Wasserkühlung").
- **Domain:** aktuell `https://vesli87.github.io` (kanonisch). Die Wunschdomain
  `www.ves-tech.ch` ist **nicht registriert** (Stand 30.07.2026, geprüft bei
  nic.ch: kein Eintrag, kein A- und kein MX-Record). Umstellung später:
  `SITE` und `EMIT_CNAME` in `core.py`, dann Build und Push — GitHub Pages
  leitet github.io danach per 301 auf die eigene Domain um.

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

## 4. Datenmodell (`data/`)

| Datei | Inhalt |
|---|---|
| `P.json` | 52 Produkte: `{id, cat, sub, vt, name, img, desc, specs{}}` |
| `CATS.json` | 4 Kategorien mit `subs[]` und Icon-Key `pk` |
| `UI.json` | 88 UI-Strings × de/fr/it |
| `CATTR/SUBTR/PDESC/SPECK/SPECV.json` | Übersetzungen für Kategorie, Unterkategorie, Beschreibung, Spec-Key, Spec-Wert |
| `PROC.json` | 7 MAHE-Verfahren |
| `DLS.json` | 7 PDF-Links (⚠ `k` ist **nicht** eindeutig — Katalog und EN 1090 heissen beide `PDF`) |
| `FEAT.json` | 19 Verfahrens-Icons (blaue Kachel `#23457f`, weisses Piktogramm, orange Akzente) |
| `HL/HL_CLEAN/PANEL_HL.json` | Besonderheiten (Gerät / Cleaner / Frontpanel) |
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
- `sitemap.xml` mit `xhtml:link`-Alternates (237 URLs); Suche und Rechtstexte
  sind `noindex,follow` und stehen bewusst nicht drin
- `robots.txt` mit Sitemap-Verweis
- CSS/JS mit `?v=<hash>` — sonst liefern Browser nach einem Deploy die alte Datei

**Preis auf Anfrage im Schema:** Das `Offer` trägt bewusst **kein** `price`-Feld.
Ein erfundener Preis wäre falsch. Google zeigt dafür eine Warnung statt eines
Fehlers — das ist der korrekte Kompromiss. Niemals `"price": "0"` schreiben.

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
python3 build/images.py     # Bilder holen und optimieren (selten nötig)
python3 build/icons.py      # Favicons erzeugen (selten nötig)
python3 -m http.server 8099 # lokal ansehen: http://127.0.0.1:8099/
```

`check.py` prüft JSON-LD, tote Links, canonical, hreflang, Titel-/Description-Länge
und -Dubletten, fehlende Bilder, Tag-Balance, Sitemap-Vollständigkeit und
Sprachparität.

## 14. Harte Regeln beim Erweitern

1. **Inhalt kommt aus `data/`**, niemals direkt ins generierte HTML schreiben —
   der nächste Build überschreibt es.
2. **Keine Preise.** Immer „Preis auf Anfrage", kein `price` im JSON-LD.
3. **Jeder neue Text in DE + FR + IT**, Schweizer „ss".
4. Neue Prozess-Icons im Stil blaue Kachel `#23457f` + weisses Piktogramm,
   `tile:true`.
5. Neue Produkte folgen dem `P`-Schema; Unterkategorie in `CATS` ergänzen und
   Übersetzungen in `SUBTR`/`PDESC`/`SPECK`/`SPECV` nachziehen.
6. **Cleaner-Geräte bekommen kein erfundenes Frontpanel** — stattdessen die
   Besonderheiten aus `HL_CLEAN`.
7. Firmendaten nur in `core.py::COMPANY` ändern.
8. `norm()` in `build.py` und `app.js` müssen identisch bleiben.
9. Nach jeder Änderung: `build.py` **und** `check.py` — Ziel sind **0 Fehler**.
10. Liefert MAHE einen Screenshot mit „Besonderheiten", wird der Text **wortwörtlich**
    in `HL`/`HL_CLEAN`/`PANEL_HL` übernommen, in allen drei Sprachen.

## 15. Offene Punkte

- Web3Forms-Key eintragen (sonst `mailto:`-Fallback)
- `ves-tech.ch` registrieren (bei nic.ch frei), DNS setzen, Postfach einrichten,
  danach `SITE` + `EMIT_CNAME` + `COMPANY["email"]` umstellen
- Google Search Console und Bing Webmaster Tools verifizieren, Sitemap einreichen
- Google Business Profile für Bronschhofen anlegen (stärkster lokaler SEO-Hebel)
- Kategorie-Hero-Bilder, Verbrauchsmaterial für Cleaner, Garantieregistrierung
- Echte Datenblatt-PDFs pro Gerät statt nur Katalog und Zertifikat
