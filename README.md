# VES-TECH Swiss

Fünfsprachiger Katalog (DE / FR / IT / EN / ES) für MAHE-Geräte und ausgewählte Occasionen.
Statische Website aus JSON und Python, ohne Framework oder Bundler.

**Live:** https://www.ves-tech.ch/ · Hosting: GitHub Pages · DNS: Infomaniak.

| Bereich | Stand |
|---|---|
| Katalog | 81 Produkte, 5 Kategorien, 5 Sprachen |
| Seiten | 610 Inhaltsseiten, 404-Seite, 15 Weiterleitungen und Verifizierungsdatei |
| Sitemap | 595 indexierbare URLs mit Sprachalternativen |
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
Sie importieren die produktiven Initialisierungsfunktionen direkt und verwenden
keine dynamische Ausfuehrung eingelesenen JavaScripts. `build/html_tools.py`
verarbeitet HTML/JSON-LD mit dem Standardparser. `build/local_paths.py` begrenzt
die CLI-Dateipfade auf die in [SECURITY.md](SECURITY.md) beschriebenen Ablagen.
`verify_mahe.py` vergleicht mit den gespeicherten Herstellerdaten; `--fresh`
aktualisiert diese aus dem Netz. Änderungen an Herstellerdaten vor Übernahme prüfen.
`audit.py --live` prüft zusätzlich die öffentlich erreichbaren Sitemap-URLs.

## Struktur

Der freigegebene Stil **VOLT** gilt seit dem 19.10.2026 für den gesamten
Auftritt in DE/FR/IT/EN/ES: helle technische Flächen, orange Leiterzüge und
skalierbare Eckrahmen. Originale Gerätefotos bleiben unverändert. Startseite,
Produktdetails mit X-Panel, alle 19 Verfahrensübersichten, Service und Kontakt
nutzen die gemeinsamen Vorlagen. Die neuen dekorativen Makromotive und ihre
Herkunft sind in `build/volt_assets.json` dokumentiert. Details: §11 in MASTER_PROMPT.md.
Der grosse Produktbereich wechselt alle 3 Sekunden zwischen MPT 3001,
HyperMIG TWIN, HyperTIG AX/DX sowie Omega AX und Beta DX (je 230 V).
`core.HOME_FEATURED` pflegt die Reihenfolge für alle Sprachen. Direktauswahl,
Vor/Zurück, Pause, Tastaturfokus und reduzierte Bewegung werden unterstützt.

- `data/`: gepflegte Produktdaten, Übersetzungen, `BUYING_GUIDE.json` für
  Hauptkategorien und `SUBCATEGORY_GUIDES.json` für 21 eigenständige Unterkategorien.
- `data/PROC.json`, `PROCESS_GUIDE.json`: 19 erklaerte Schweissverfahren/Funktionen,
  Vergleich, Parameter und FAQ in DE/FR/IT/EN/ES mit Herstellerquellen.
- `build/core.py`, `render.py`, `pages.py`, `build.py`: Generator.
- `assets/css/site.css`, `assets/js/app.js`, `assets/js/analytics.js`: Frontend.
- `produkte/`, `fr/`, `it/`, `en/`, `es/` und andere Seiten: generiert, nicht von Hand ändern.
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
Ein einzelner `fbclid`-Parameter wird nach Zustimmung vor dem Laden von Ahrefs
aus der aktuellen Browseradresse entfernt. Sein Wert wird weder gespeichert noch
übertragen. Alle übrigen Parameter müssen weiterhin der geprüften Kombination
entsprechen; doppelte `fbclid`-Werte und Referrer mit dieser Kennung bleiben
ausgeschlossen. Die ursprüngliche URL kann weiterhin im normalen HTTP-Zugriff
des Webservers stehen; die Bereinigung betrifft die optionale Browseranalytik.
Cloudflare behält die vollständige Query-Sperre, da sein Beacon keine gemeinsame
URL-Bereinigung unterstützt. Das gilt auch für Einstiege mit entferntem `fbclid`.
Beide Zahlenreihen deshalb getrennt auswerten.

Der Browser merkt sich nach Zustimmung den ersten bekannten Kampagnenkontakt
und die bereinigte Einstiegsseite in `sessionStorage`, höchstens 24 Stunden.
Kein Besucherprofil und keine eigene Personenkennung. Beim Versand wird dieser
Kontext der geschäftlichen Anfrage beigefügt. Name, E-Mail, Telefonnummer und
Freitext gehen ausschliesslich an den Versanddienst, nicht in Analytics-Properties.
Ein Mailentwurf liegt nicht mehr als automatisch messbares `href` im DOM.

Die Ereignisse `product_view`, `inquiry_add`, `inquiry_open`, `inquiry_start`,
`inquiry_submit`, `inquiry_success`, `inquiry_error`, `contact_email`,
`contact_phone`, `contact_whatsapp`, `product_consult` und `download_click` müssen in Ahrefs als
gleichnamige Custom Events eingerichtet sein. `inquiry_success` entsteht nur
nach `success === true` von Web3Forms, einmal pro erfolgreichem Versand.
Ein Klick, Mailentwurf oder Versandversuch ist keine bestätigte Anfrage.
`contact_whatsapp` zählt nur den Klick auf den festen Geschäftskontakt aus
`COMPANY.whatsapp_href`, nach Statistik-Zustimmung. Telefonnummer, Linkziel und
Nachrichtentext werden dabei nicht übertragen. Der normale externe Link öffnet
WhatsApp auch ohne Statistik; er enthält keinen vorbefüllten Text und übermittelt
keinen Referrer. Die automatische externe Linkmessung bleibt gesperrt.
Ein WhatsApp-Klick bestätigt weder eine gesendete Nachricht noch eine Antwort.
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

Alle 84 Sprachfassungen der eigenständigen Unterkategorien erhalten eine eigene
Einleitung und konkrete Auswahlkriterien aus `SUBCATEGORY_GUIDES.json`. Die
Plasma-TIG-URL bleibt die vorhandene Produktseite, ohne zusätzliche Dublette.
Startseite, Unternehmensseite und Verfahrensübersicht verlinken passende
Service- und Mikroplasma-Seiten direkt im sichtbaren Hauptinhalt.

`PRODUCT_GUIDES.json` ergänzt 27 Produktfamilien mit konkreten Auswahlhinweisen
in DE/FR/IT/EN/ES. Sie stehen ausserhalb geschlossener Reiter im HTML; die deutsche
Fassung erscheint auch in `llms-full.txt`. `GUIDE_LINKS.json` verbindet diese
Hinweise und die bestehenden Kategoriehilfen mit sprachgleichen Geräten und
Dienstleistungen. Die Referenzen werden vor dem Ersetzen generierter Dateien
validiert. Sie erweitern keine Hersteller-Kompatibilitätsliste.
Die Serviceübersicht erläutert Anfragevorbereitung, Auftragsklärung und
Geräteannahme in der Partnerwerkstatt. Unternehmensseite und Impressum führen
direkt zu Katalog und Kontakt. Verfügbarkeit und Herstellerdaten bleiben in
ihren bestehenden Quellen; diese Inhalte versprechen keine Indexierung.

Inhalte und Auswahlhilfen stehen bereits im HTML. Produktdaten enthalten keine
erfundenen Hersteller-Artikelnummern, Preise oder Bewertungen. Ohne ein echtes
Angebot oder geeignete Bewertungen sind Google-Produkt-Rich-Results nicht
verfügbar; das verhindert die normale Indexierung nicht.
Seit dem 07.10.2026 gibt der Katalog deshalb bewusst keine `Product`-Auszeichnung
aus. Eine `ItemPage` verweist auf einen neutralen `Thing` mit Namen,
Beschreibung, Originalfoto und echter Katalogreferenz. Technische Daten,
Marken-/Modellzuordnung und Zustand bleiben im sichtbaren HTML und im
JSON-Katalog erhalten. Dies entfernt die unvollständige Product-Deklaration,
verspricht aber keine Indexierung oder Rich Results; historische Google-Meldungen
aktualisieren sich erst nach erneutem Crawlen und Verarbeiten.
`llms.txt`, `llms-full.txt` und `data/products.json` sind zusätzliche Datenzugänge,
keine Zusage auf KI-Zitate oder Rankings. Der JSON-Katalog ist ein eigenes Format
(`schema_version`), das JSON-LD steht auf den HTML-Seiten.

Die Sitemap enthält 595 indexierbare URLs; Suche, Datenschutz und AGB bleiben
ausgeschlossen, das Impressum ist indexierbar. `lastmod` bleibt bei reinen
Änderungen an CSP/SRI, Asset-Versionsnummern und der Laufzeitkonfiguration stabil.
Inhalte, SEO-Metadaten, JSON-LD, Navigation und geänderte Asset-Pfade werden
weiterhin als Seitenänderung erkannt.

## Veröffentlichen

PSHB-125- und MG500-Linkvorschauen verwenden eine eigene 1200 × 630 Karte pro Sprache,
damit soziale Netzwerke den Kopf der schmalen Brennerfotografie nicht abschneiden.
`node build/pshb_social_card.mjs` erzeugt die PSHB-SVG-/PNG-Karten;
`node build/mg500_social_card.mjs` baut die MG500-PNGs aus dem vollständigen
bereitgestellten Foto und `data/SOCIAL_CARDS.json`. Beide verwenden Sharp nur
beim manuellen Asset-Build und fügen keine Browser-Abhängigkeit hinzu.
Nach dem visuellen Prüfen werden die PNGs mitgespeichert. Produktgalerie und
JSON-LD verwenden weiterhin das ursprüngliche Foto.

Push auf `main` startet `.github/workflows/pages.yml`. Build, Seitenprüfungen,
Herstellerdaten-Abgleich und Regressionstests müssen bestehen.
`build/package_site.py` kopiert nur öffentliche Dateien in ein separates Artefakt;
Build-Quellen, Rohdaten, lokale Konfiguration und Berichte werden nicht hochgeladen.
Der Quellcode selbst liegt in einem öffentlichen GitHub-Repository.
Pull Requests werden ebenfalls geprüft, veröffentlichen jedoch nichts.
Jeder Produktionsbuild erstellt zusaetzlich eine 90 Tage aufbewahrte oeffentliche
Sicherung und testet deren Wiederherstellung vor dem Deploy. Nach erfolgreichem
Deploy legt `build/release_recovery.py` dieselbe gepruefte Sicherung als
versioniertes GitHub Release ohne Actions-Ablauffrist ab. Quellcode ist am exakten
Tag verfuegbar. Die Sicherung laeuft auf dem Runner und sammelt keine grossen
Kopien auf dem Notebook; Einzelheiten und Grenzen stehen in `BACKUP.md`.
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
