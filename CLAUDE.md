# CLAUDE.md — Arbeitsanweisung für dieses Repository

Dies ist die Website **VES-TECH Swiss** — ein dreisprachiger Katalog für das
MAHE-Schweisstechnik-Programm. Sie läuft unter `https://www.ves-tech.ch/`;
`vesli87.github.io` leitet per 301 dorthin weiter.

## Zuerst lesen

**[MASTER_PROMPT.md](MASTER_PROMPT.md)** ist die verbindliche Beschreibung des
Projekts: Architektur, Datenmodell, URL-Schema, SEO/AEO-Konzept, Designsystem und
die harten Regeln. Bei jeder inhaltlichen oder architektonischen Änderung wird es
mitgepflegt.

## Das Wichtigste in Kürze

Die 360 Inhaltsseiten, die 404-Seite und die Weiterleitungen im Repository sind **generiert**. Sie werden nie von Hand
bearbeitet — der nächste Build überschreibt jede Änderung.

```
data/*.json + build/i18n_extra.json   →   build/build.py   →   *.html
```

Bearbeitet werden also:

| Was du ändern willst | Wo |
|---|---|
| Produkt, Merkmalsliste, Kategorie | `data/P.json`, `data/CATS.json` |
| Besonderheiten eines Geräts | `data/HL_DEVICE.json` (Herstellerangaben, DE/FR/IT; dokumentierte Sprachkorrekturen in `build/mahe_copy_edits.json`) |
| Besonderheiten eines Frontpanels | `data/PANEL_HL_DEVICE.json` (ebenso) |
| Occasion: Zustand, Beschreibung, Fragen, verwandte Geräte | `data/ZUSTAND.json`, `data/OCCTEXT.json`, `data/VERWANDT.json` (DE/FR/IT) |
| Technische Daten — welche MAHE-Tabelle zu welchem Gerät | `data/SPECMAP.json` |
| Übersetzung einer Tabellenzeile / einer Fussnote | `data/SPECROW.json`, `data/SPECNOTE.json` |
| Übersetzung eines UI-Textes | `data/UI.json` |
| Übersetzung von Kategorie / Spec / Beschreibung | `data/CATTR/SUBTR/SPECK/SPECV/PDESC.json` |
| Bestehende Unterkategorie-URLs | `build/subcategory_slugs.json`; bei Textkorrekturen unverändert lassen |
| Seitentitel, meta description, FAQ | `build/i18n_extra.json` |
| AGB, Datenschutzerklärung, Impressum | `build/i18n_extra.json` → `agb_body` / `datenschutz_body` / `impressum_body`, je `[["Überschrift", "&lt;p&gt;…"], …]` in DE/FR/IT |
| Firmenadresse, Telefon, Domain | `build/core.py` → `COMPANY` / `SITE` |
| Search-Console-/Bing-Verifizierung | `build/core.py` → `GOOGLE_SITE_VERIFICATION` / `BING_SITE_VERIFICATION` |
| Auswahlhilfen je Kategorie | `data/BUYING_GUIDE.json` |
| Statistik und Zustimmung | `assets/js/analytics.js`, `build/config.public.json` |
| Aussehen | `assets/css/site.css` |
| Suche, Anfrageliste, Formulare | `assets/js/app.js` |
| Seitenaufbau / HTML-Struktur | `build/pages.py`, `build/render.py` |

## Vor dem Veröffentlichen

```bash
python3 build/build.py
python3 build/check.py
python3 build/audit.py
python3 build/verify_mahe.py   # gegen gespeicherte Herstellerdaten
node --test build/test_frontend.mjs
python3 -m unittest discover -s build -p 'test_*.py'
python3 build/security_check.py
```

Alle Prüfungen müssen **0 Fehler** melden und laufen auch in GitHub Actions, wo sie bei
einem Fehler den Deploy blockieren.

`check.py` prüft die Grundlagen: JSON-LD, tote Links, `canonical`, `hreflang`,
Titel- und Description-Dubletten, fehlende Bilder, Tag-Balance, Vollständigkeit
der Sitemap, Sprachparität.

`audit.py` geht tiefer: Überschriftenhierarchie (genau ein `h1`, keine
übersprungene Ebene), verwaiste Seiten, NAP-Konsistenz über alle Sprachen,
deutscher Text der in FR/IT stehen geblieben ist, Alt-Texte, Meta-Dubletten pro
Sprache, `lang`-Attribut. Mit `--live` zusätzlich alle Sitemap-URLs im Netz und
die Weiterleitungen.

Lokal ansehen:

```bash
python3 -m http.server 8099
```

## Regeln, die nicht verhandelbar sind

1. **Keine Preise** — überall „Preis auf Anfrage", nie ein `price` im JSON-LD.
2. **Jeder neue Text in DE, FR und IT**, Schweizer Schreibweise („ss", nicht „ß").
3. Generierte Dateien (`index.html`, `sitemap.xml`, `llms*.txt`,
   `data/products.json`, `data/search-*.json`) nie von Hand editieren.
4. `norm()` in `build/build.py` und `assets/js/app.js` müssen identisch bleiben,
   sonst findet die Suche nichts mehr.
5. Frontpanels sind **Fotos des Herstellers** (`assets/img/panels/`, importiert
   mit `build/panels.py`). Wo MAHE keines geliefert hat, bleibt der gezeichnete
   Ersatz — es wird nie eines erfunden. Zuordnung in `build/core.py::PANELS`.
6. **Keine Kopierschutz-Massnahmen einbauen** (Rechtsklick-Sperre, Textauswahl
   sperren, DevTools-Blocker, Verschleierung). Sie sind wirkungslos, schaden der
   Bedienbarkeit und der Barrierefreiheit — und Inhalt per JavaScript zu
   verstecken zerstört SEO und AEO. Der Schutz liegt in `LICENSE`, nicht im Code.
   Begründung in [MASTER_PROMPT.md](MASTER_PROMPT.md#15-was-sich-am-code-schützen-lässt--und-was-nicht).

Die vollständige Liste steht in [MASTER_PROMPT.md](MASTER_PROMPT.md#14-harte-regeln-beim-erweitern).

## Deploy

Push auf `main` → GitHub Actions baut, prüft und veröffentlicht auf GitHub Pages
(`.github/workflows/pages.yml`).

Die eigene Domain steht in der **Pages-Konfiguration**, nicht in der Datei
`CNAME` — beim Actions-Deployment wird die Datei ignoriert. `build/deploy.sh`
setzt sie automatisch, solange `EMIT_CNAME = True` in `build/core.py` steht.
Hintergrund in [MASTER_PROMPT.md](MASTER_PROMPT.md#14a-eigene-domain-und-github-pages).

Sicherung und Wiederherstellung: [BACKUP.md](BACKUP.md). Der volle lokale Backupordner
darf niemals als öffentliches Artefakt hochgeladen werden. Nur `--public-only`
ist für GitHub-Artefakte vorgesehen. Sicherheit: [SECURITY.md](SECURITY.md).
