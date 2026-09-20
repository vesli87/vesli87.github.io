# VES-TECH Swiss

Dreisprachiger Katalog (DE / FR / IT) für MAHE-Geräte und ausgewählte Occasionen.
Statische Website aus JSON und Python, ohne Framework oder Bundler.

**Live:** https://www.ves-tech.ch/ · Hosting: GitHub Pages · DNS: Infomaniak.

| Bereich | Stand |
|---|---|
| Katalog | 79 Produkte, 5 Kategorien, 3 Sprachen |
| Seiten | 360 Inhaltsseiten, 404-Seite, 15 Weiterleitungen und Verifizierungsdatei |
| Sitemap | 351 indexierbare URLs mit Sprachalternativen |
| Suche | Lokaler Suchindex mit Synonymen und Tippfehlertoleranz |
| SEO | Individuelle Metadaten, canonical, hreflang, JSON-LD, Sitemap, IndexNow |
| Beratung | Auswahlhilfen je Hauptkategorie, produktbezogenes Kontaktformular, Anfrageliste |
| Statistik | Optionales Cloudflare Web Analytics nach Zustimmung |

## Entwickeln und prüfen

```bash
python3 build/build.py
python3 build/check.py
python3 build/audit.py
python3 build/verify_mahe.py
node --test build/test_frontend.mjs
python3 -m unittest discover -s build -p 'test_*.py'
python3 -m http.server 8099 --bind 127.0.0.1
```

Der Generator benötigt Python 3.9 oder neuer und die Standardbibliothek.
Die Frontend-Regressionstests benötigen Node.js 22 oder neuer, keine npm-Pakete.
`verify_mahe.py` vergleicht mit den gespeicherten Herstellerdaten; `--fresh`
aktualisiert diese aus dem Netz. Änderungen an Herstellerdaten vor Übernahme prüfen.
`audit.py --live` prüft zusätzlich die öffentlich erreichbaren Sitemap-URLs.

## Struktur

- `data/`: gepflegte Produktdaten, Übersetzungen und `BUYING_GUIDE.json`.
- `build/core.py`, `render.py`, `pages.py`, `build.py`: Generator.
- `assets/css/site.css`, `assets/js/app.js`, `assets/js/analytics.js`: Frontend.
- `produkte/`, `fr/`, `it/` und andere Seiten: generiert, nicht von Hand ändern.
- `reports/`: lokale, vertrauliche Auswertungen, von Git und Deployment ausgeschlossen.

## Formulare und Statistik

Konfiguration: Umgebungsvariable, danach `build/config.local.json`, danach
`build/config.public.json`. Die Vorlage steht in `build/config.example.json`.
Ein explizit leerer lokaler Wert deaktiviert die entsprechende öffentliche Vorgabe.

Für direktes Versenden über [Web3Forms](https://web3forms.com) wird
`web3forms_key` lokal oder das GitHub-Actions-Secret `WEB3FORMS_KEY` benötigt.
Ohne Key bereitet das Formular einen E-Mail-Entwurf vor; der Kunde muss ihn selbst
versenden. Bei einem Übertragungsfehler bleiben die Angaben zum Kopieren erhalten.
Persönliche Formularangaben werden nicht in localStorage gespeichert.
Der Web3Forms-Formularkey steht technisch im ausgelieferten Frontend und ist kein
privater API-Schlüssel. Administrative Zugangsdaten gehören niemals hierher.

`cloudflare_analytics_token` ist der öffentliche Beacon-Token, kein Cloudflare
API-Token. Er steht in `build/config.public.json`, damit der automatische Build
nicht die Integration entfernt. Optional überschreibt ihn
`CLOUDFLARE_ANALYTICS_TOKEN`. Statistik lädt ausschliesslich auf der Produktionsdomain
und nach Zustimmung. Ablehnen und Widerrufen sind möglich. Suchseiten, URLs und
Referrer mit Parametern sowie GPC/DNT werden berücksichtigt. Keine Kontaktinhalte
werden als Statistik-Ereignisse verschickt. Auswahl gilt höchstens 180 Tage.
Wegen Zustimmung, Browserblockern und Ausschlüssen ist dies keine Vollzählung.

Web Analytics misst Besuche und Ladezeiten. Es ersetzt keine Messung bestätigter
Kundenanfragen. Cloudflare DNS, Proxy und Sicherheitsanalysen sind eine separate
Integration und werden durch den Beacon nicht eingeschaltet.

## SEO und AEO

Inhalte und Auswahlhilfen stehen bereits im HTML. Produktdaten enthalten keine
erfundenen Hersteller-Artikelnummern, Preise oder Bewertungen. Ohne ein echtes
Angebot oder geeignete Bewertungen sind Google-Produkt-Rich-Results nicht
verfügbar; das verhindert die normale Indexierung nicht.
`llms.txt`, `llms-full.txt` und `data/products.json` sind zusätzliche Datenzugänge,
keine Zusage auf KI-Zitate oder Rankings. Der JSON-Katalog ist ein eigenes Format
(`schema_version`), das JSON-LD steht auf den HTML-Seiten.

## Veröffentlichen

Push auf `main` startet `.github/workflows/pages.yml`. Build, Seitenprüfungen,
Herstellerdaten-Abgleich und Regressionstests müssen bestehen.
`build/package_site.py` kopiert nur öffentliche Dateien in ein separates Artefakt;
Build-Quellen, Rohdaten, lokale Konfiguration und Berichte werden nicht hochgeladen.
Der Quellcode selbst liegt in einem öffentlichen GitHub-Repository.
Nach dem Deploy meldet IndexNow geänderte URLs; Google verwendet die Sitemap.

## Weiterarbeiten

[MASTER_PROMPT.md](MASTER_PROMPT.md) beschreibt Architektur und Inhaltsregeln.
[CLAUDE.md](CLAUDE.md) ist die Kurzfassung für Assistenten.
[SECURITY.md](SECURITY.md) erläutert technische Schutzmassnahmen und Grenzen.

Produktdaten und Herstellerbilder bleiben Eigentum der jeweiligen Rechteinhaber.
