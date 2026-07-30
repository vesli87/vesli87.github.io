# VES-TECH Swiss

Dreisprachiger Katalog (DE / FR / IT) für das MAHE-Schweisstechnik-Programm.
Statische Website, gebaut aus JSON-Daten mit Python — kein Node, kein Framework,
kein Bundler.

**Live:** https://vesli87.github.io/ — die eigene Domain `www.ves-tech.ch` ist
noch nicht registriert; sobald sie auf GitHub Pages zeigt, genügen zwei Zeilen
in `build/core.py` (`SITE` und `EMIT_CNAME`).

| | |
|---|---|
| Seiten | 247 vorgerendert (52 Geräte × 3 Sprachen + Kategorien, FAQ, Verfahren, Downloads, Kontakt, Recht) |
| Gewicht | ~2,2 MB Bilder (WebP), ~40 kB CSS, ~20 kB JS |
| Suche | eigener Index mit Synonymen und Tippfehlertoleranz, ~45 kB pro Sprache |
| SEO | canonical, hreflang, JSON-LD (`Product`, `FAQPage`, `LocalBusiness`, …), Sitemap mit Alternates |
| AEO | `llms.txt`, `llms-full.txt`, `data/products.json`, KI-Crawler in `robots.txt` freigegeben |

## Entwickeln

```bash
python3 build/build.py        # alle Seiten neu erzeugen
python3 build/check.py        # QA – muss 0 Fehler melden
python3 -m http.server 8099   # http://127.0.0.1:8099/
```

Seltener nötig:

```bash
python3 build/images.py       # Produktbilder holen und als WebP optimieren
python3 build/icons.py        # Favicons und App-Icons erzeugen
```

## Struktur

```
data/                Inhalt (Single Source of Truth)
build/               Generator: core.py · render.py · pages.py · build.py · check.py
assets/css|js|img/   Auslieferung
produkte/ fr/ it/ …  generiertes HTML – nicht von Hand bearbeiten
```

## Kontaktformular

Der Versand läuft über [Web3Forms](https://web3forms.com). Access-Key eintragen:

```bash
echo '{"web3forms_key":"DEIN-KEY"}' > build/config.local.json   # lokal, gitignored
```

In GitHub: Repository → Settings → Secrets and variables → Actions →
`WEB3FORMS_KEY`. Ohne Key fallen beide Formulare automatisch auf `mailto:` zurück.

## Deploy

Push auf `main` startet `.github/workflows/pages.yml`: Build, QA, Veröffentlichung
auf GitHub Pages. Bei einem QA-Fehler wird nicht deployt.

## Weiterarbeiten

[MASTER_PROMPT.md](MASTER_PROMPT.md) beschreibt Architektur, Datenmodell und die
Regeln beim Erweitern. [CLAUDE.md](CLAUDE.md) ist die Kurzfassung für KI-Assistenten.

---

Produktdaten und Produktbilder: MAHE GmbH, Deutschland.
