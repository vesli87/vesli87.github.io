# CLAUDE.md — Arbeitsanweisung für dieses Repository

Dies ist die Website **VES-TECH Swiss** — ein dreisprachiger Katalog für das
MAHE-Schweisstechnik-Programm. Sie läuft auf `https://vesli87.github.io/`;
die Domain `www.ves-tech.ch` ist noch nicht registriert.

## Zuerst lesen

**[MASTER_PROMPT.md](MASTER_PROMPT.md)** ist die verbindliche Beschreibung des
Projekts: Architektur, Datenmodell, URL-Schema, SEO/AEO-Konzept, Designsystem und
die harten Regeln. Bei jeder inhaltlichen oder architektonischen Änderung wird es
mitgepflegt.

## Das Wichtigste in Kürze

Die 247 HTML-Seiten im Repository sind **generiert**. Sie werden nie von Hand
bearbeitet — der nächste Build überschreibt jede Änderung.

```
data/*.json + build/i18n_extra.json   →   build/build.py   →   *.html
```

Bearbeitet werden also:

| Was du ändern willst | Wo |
|---|---|
| Produkt, Spezifikation, Kategorie | `data/P.json`, `data/CATS.json` |
| Übersetzung eines UI-Textes | `data/UI.json` |
| Übersetzung von Kategorie / Spec / Beschreibung | `data/CATTR/SUBTR/SPECK/SPECV/PDESC.json` |
| Seitentitel, meta description, FAQ, Impressum, Datenschutz | `build/i18n_extra.json` |
| Firmenadresse, Telefon, Domain | `build/core.py` → `COMPANY` / `SITE` |
| Aussehen | `assets/css/site.css` |
| Suche, Anfrageliste, Formulare | `assets/js/app.js` |
| Seitenaufbau / HTML-Struktur | `build/pages.py`, `build/render.py` |

## Nach jeder Änderung — immer beides

```bash
python3 build/build.py
python3 build/check.py
```

`check.py` muss **0 Fehler** melden. Es prüft JSON-LD, tote Links, `canonical`,
`hreflang`, Titel- und Description-Dubletten, fehlende Bilder, Tag-Balance,
Vollständigkeit der Sitemap und ob alle drei Sprachen gleich viele Seiten haben.
Derselbe Check läuft in GitHub Actions und blockiert bei Fehlern den Deploy.

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
5. Cleaner-Geräte bekommen **kein** erfundenes Frontpanel.

Die vollständige Liste steht in [MASTER_PROMPT.md](MASTER_PROMPT.md#14-harte-regeln-beim-erweitern).

## Deploy

Push auf `main` → GitHub Actions baut, prüft und veröffentlicht auf GitHub Pages
(`.github/workflows/pages.yml`). Eine `CNAME`-Datei wird erst erzeugt, wenn
`EMIT_CNAME` in `build/core.py` auf `True` steht — vorher würde sie Pages auf
eine Domain umstellen, die es nicht gibt, und die Seite wäre nicht erreichbar.
