# VES-TECH Swiss

Dreisprachiger Katalog (DE / FR / IT) für MAHE-Geräte und ausgewählte Occasionen.
Statische Website aus JSON und Python, ohne Framework oder Bundler.

**Live:** https://www.ves-tech.ch/ · Hosting: GitHub Pages · DNS: Infomaniak.

| Bereich | Stand |
|---|---|
| Katalog | 79 Produkte, 5 Kategorien, 3 Sprachen |
| Seiten | 360 Inhaltsseiten, 404-Seite, 15 Weiterleitungen und Verifizierungsdatei |
| Sitemap | 351 indexierbare URLs mit Sprachalternativen |
| Suche | Lokaler Suchindex mit Produkten, Dienstleistungen, Synonymen und Tippfehlertoleranz |
| SEO | Individuelle Metadaten, canonical, hreflang, JSON-LD, Sitemap, IndexNow |
| Beratung | Auswahlhilfen je Hauptkategorie, produktbezogenes Kontaktformular, Anfrageliste |
| Statistik | Ahrefs für Produktinteresse und bestätigte Anfragen; Cloudflare für Ladezeiten, beide nach Zustimmung |

## Entwickeln und prüfen

```bash
python3 build/build.py
python3 build/check.py
python3 build/audit.py
python3 build/security_check.py
python3 build/verify_mahe.py
node --test build/test_*.mjs
python3 -m unittest discover -s build -p 'test_*.py'
python3 -m http.server 8099 --bind 127.0.0.1
```

Der Generator benötigt Python 3.9 oder neuer und die Standardbibliothek.
Die Frontend-Regressionstests benötigen Node.js 22 oder neuer, keine npm-Pakete.
`verify_mahe.py` vergleicht mit den gespeicherten Herstellerdaten; `--fresh`
aktualisiert diese aus dem Netz. Änderungen an Herstellerdaten vor Übernahme prüfen.
`audit.py --live` prüft zusätzlich die öffentlich erreichbaren Sitemap-URLs.

## Struktur

- `data/`: gepflegte Produktdaten, Übersetzungen, `BUYING_GUIDE.json` für
  Hauptkategorien und `SUBCATEGORY_GUIDES.json` für 21 eigenständige Unterkategorien.
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

`cloudflare_analytics_token` und `ahrefs_analytics_key` sind öffentliche
Websitekennungen, keine administrativen API-Schlüssel. Sie stehen in
`build/config.public.json`; optional überschreiben `CLOUDFLARE_ANALYTICS_TOKEN`
und `AHREFS_ANALYTICS_KEY` die Werte. Statistik lädt ausschliesslich auf der
Produktionsdomain und nach Zustimmung. Die Auswahl gilt höchstens 180 Tage.
Die neue Zustimmung `vt.analytics.consent.v2` erklärt beide Anbieter. Eine alte
Cloudflare-Zustimmung wird nicht übernommen, eine gültige Ablehnung bleibt gültig.
Ablehnen, Widerruf, DNT und GPC werden berücksichtigt. Wegen Zustimmung,
Browserblockern und bewussten Ausschlüssen ist die Statistik keine Vollzählung.

Ahrefs erhält nur geprüfte kanonische Seitenadressen, bekannte Produkt-IDs und
feste Ereigniswerte. Vier UTM-Werte müssen gemeinsam einem Eintrag in
`data/ANALYTICS_CAMPAIGNS.json` entsprechen. Unbekannte Parameter, Fragmente,
Suchseiten und unsichere Referrer verhindern das Laden. `?product=` mit optionalem `option=` ist nur für bekannte Produktkombinationen
auf der Kontaktseite erlaubt. `?service=` akzeptiert nur die vier bekannten
Dienstleistungen. Diese Parameter werden nicht als URL übertragen, Optionen
werden nicht an die Analytik gesendet.
Cloudflare behält die vollständige Query-Sperre, da sein Beacon keine gemeinsame
URL-Bereinigung unterstützt. Beide Zahlenreihen deshalb getrennt auswerten.

Der Browser merkt sich nach Zustimmung den ersten bekannten Kampagnenkontakt
und die bereinigte Einstiegsseite in `sessionStorage`, höchstens 24 Stunden.
Kein Besucherprofil und keine eigene Personenkennung. Beim Versand wird dieser
Kontext der geschäftlichen Anfrage beigefügt. Name, E-Mail, Telefonnummer und
Freitext gehen ausschliesslich an den Versanddienst, nicht in Analytics-Properties.
Ein Mailentwurf liegt nicht mehr als automatisch messbares `href` im DOM.

Die Ereignisse `product_view`, `inquiry_add`, `inquiry_open`, `inquiry_start`,
`inquiry_submit`, `inquiry_success`, `inquiry_error`, `contact_email`,
`contact_phone`, `product_consult` und `download_click` müssen in Ahrefs als
gleichnamige Custom Events eingerichtet sein. `inquiry_success` entsteht nur
nach `success === true` von Web3Forms, einmal pro erfolgreichem Versand.
Ein Klick, Mailentwurf oder Versandversuch ist keine bestätigte Anfrage.
Auch eine bestätigte Anfrage ist noch kein qualifizierter Lead oder Verkauf.
Angebote und tatsächliche Aufträge werden separat privat geführt.

Ahrefs wird mit geprüfter SRI-Prüfsumme geladen. Ändert der Anbieter den Tracker,
bleibt diese Messung bis zur erneuten Prüfung aus; Formulare funktionieren weiter.
Bei Updates Datenschutzgrenzen und tatsächlich gesendete SDK-Payloads erneut
testen, nicht lediglich die Prüfsumme ersetzen. Automatische Linkmessung ist
auf bekannte eigene Pfade begrenzt, automatische Formularmessung deaktiviert.
Vor Zustimmung werden keine Interaktionen gepuffert. Nach Zustimmung ist die
kurze Lade-Warteschlange auf 30 Ereignisse begrenzt.

Cloudflare misst insbesondere Ladezeiten. Cloudflare DNS, Proxy und
Sicherheitsanalysen sind separate Integrationen und werden nicht eingeschaltet.
Kontometriken, Kampagnenberichte und die private Verkaufsliste liegen nur unter
`reports/`; sie gehören weder in Git noch in das öffentliche Websitepaket.

## SEO und AEO

Alle 63 Sprachfassungen der eigenständigen Unterkategorien erhalten eine eigene
Einleitung und konkrete Auswahlkriterien aus `SUBCATEGORY_GUIDES.json`. Die
Plasma-TIG-URL bleibt die vorhandene Produktseite, ohne zusätzliche Dublette.
Startseite, Unternehmensseite und Verfahrensübersicht verlinken passende
Service- und Mikroplasma-Seiten direkt im sichtbaren Hauptinhalt.

Inhalte und Auswahlhilfen stehen bereits im HTML. Produktdaten enthalten keine
erfundenen Hersteller-Artikelnummern, Preise oder Bewertungen. Ohne ein echtes
Angebot oder geeignete Bewertungen sind Google-Produkt-Rich-Results nicht
verfügbar; das verhindert die normale Indexierung nicht.
`llms.txt`, `llms-full.txt` und `data/products.json` sind zusätzliche Datenzugänge,
keine Zusage auf KI-Zitate oder Rankings. Der JSON-Katalog ist ein eigenes Format
(`schema_version`), das JSON-LD steht auf den HTML-Seiten.

Die Sitemap enthält 351 indexierbare URLs; Suche, Datenschutz und AGB bleiben
ausgeschlossen, das Impressum ist indexierbar. `lastmod` bleibt bei reinen
Änderungen an CSP/SRI, Asset-Versionsnummern und der Laufzeitkonfiguration stabil.
Inhalte, SEO-Metadaten, JSON-LD, Navigation und geänderte Asset-Pfade werden
weiterhin als Seitenänderung erkannt.

## Veröffentlichen

Push auf `main` startet `.github/workflows/pages.yml`. Build, Seitenprüfungen,
Herstellerdaten-Abgleich und Regressionstests müssen bestehen.
`build/package_site.py` kopiert nur öffentliche Dateien in ein separates Artefakt;
Build-Quellen, Rohdaten, lokale Konfiguration und Berichte werden nicht hochgeladen.
Der Quellcode selbst liegt in einem öffentlichen GitHub-Repository.
Pull Requests werden ebenfalls geprüft, veröffentlichen jedoch nichts.
Jeder Produktionsbuild erstellt zusätzlich eine 90 Tage aufbewahrte öffentliche
Release-Sicherung und testet deren Wiederherstellung vor dem Deploy.
Lokale Projektsicherung und Wiederherstellung: [BACKUP.md](BACKUP.md).
Nach dem Deploy meldet IndexNow geänderte URLs; Google verwendet die Sitemap.

## Weiterarbeiten

[MASTER_PROMPT.md](MASTER_PROMPT.md) beschreibt Architektur und Inhaltsregeln.
[CLAUDE.md](CLAUDE.md) ist die Kurzfassung für Assistenten.
[SECURITY.md](SECURITY.md) erläutert technische Schutzmassnahmen und Grenzen.

Produktdaten und Herstellerbilder bleiben Eigentum der jeweiligen Rechteinhaber.

Sicherheit und Betrieb: CSP/SRI und öffentliche Dateigrenzen werden in CI geprüft.
CodeQL, Secret Scanning/Push Protection und Dependabot unterstützen die Kontrolle;
`main` ist gegen Löschung und Force-Push geschützt. Details und verbleibende
Plattform-/Kontogrenzen stehen in [SECURITY.md](SECURITY.md).

## Präzise Anfragen und Occasionen

`data/INQUIRY_OPTIONS.json` enthält ausschliesslich belegte Varianten und
identifizierte Einzelgeräte. Der vorgerenderte, übersetzte Laufzeitkatalog ist
unabhängig vom Suchindex und von der Statistik. Der Produktkontext einer Anfrage
bleibt erhalten, wenn die Suche ausfällt oder der Besucher Statistik ablehnt.
Freitext wird nicht mit automatisch eingefügtem Produkttext überschrieben.

Die funktionale Anfrageliste verwendet `vt.cart.v2`: Produkt-ID, Options-ID und
Menge, ohne Namen oder Kontaktdaten. Bekannte Einträge aus v1 werden migriert;
Namen, Bilder und Links werden aus dem aktuellen Katalog neu abgeleitet. Zwei
Varianten bleiben getrennte Positionen; ein identifiziertes Einzelgerät lässt
sich höchstens einmal anfragen. Die Auswahl ist keine Reservierung.

Die Verfügbarkeit der PlasmaFix-51-Geräte steht mit Bestätigungsdatum separat in
`INQUIRY_OPTIONS.json`. Foto-Positionen dienen der Identifikation, nicht als
Erfindung separater Detailfotos oder Zustandsnachweise. Bei einem Verkauf die
verifizierte Verfügbarkeit und nötigenfalls die angebotenen Optionen aktualisieren.

Optionale Angaben zu Werkstoff, Anschluss, Fehlerbild oder Termin bleiben nur
im Formular und in der geschäftlichen Nachricht. Nach bestätigter Übermittlung
erscheint eine lokale kopierbare Zusammenfassung; sie ist keine zusätzliche
E-Mail-Bestätigung. Varianten, Gerätepositionen und Formulardetails werden nicht
an Ahrefs oder Cloudflare gesendet.
