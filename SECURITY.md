# Sicherheit

Diese Website ist der Auftritt von VES-TECH Swiss, einem Einzelunternehmen in
der Schweiz. Sie besteht aus vorgerenderten HTML-Dateien auf GitHub Pages – es
gibt keine eigene Datenbank, keine Kundenanmeldung und keine Kundensitzungen.
Formularnachrichten werden bei aktivierter Konfiguration durch Web3Forms
verarbeitet; optionale Webstatistik durch Ahrefs und Cloudflare. Details stehen in der
Datenschutzerklärung der Website.

## Eine Lücke melden

Schreiben Sie an **vestechswiss@gmail.com** oder rufen Sie **+41 76 710 91 39**
an. Dieselben Angaben stehen maschinenlesbar in
[`/.well-known/security.txt`](https://www.ves-tech.ch/.well-known/security.txt)
nach RFC 9116.

Bitte melden Sie zuerst und veröffentlichen Sie erst danach. Eine Antwort
kommt innerhalb von fünf Arbeitstagen; eine Behebung, sobald der Weg klar ist.
Es gibt kein Bug-Bounty-Programm – dieses Projekt hat kein Budget dafür, und
ein Versprechen ohne Deckung wäre unehrlich.

Sprachen: Deutsch, Englisch, Tschechisch.

## Was hier bereits gilt

* **Content-Security-Policy ohne `unsafe-inline`.** Weder für Skripte noch für
  Stile. Jedes Inline-Skript, beide lokale JavaScript-Dateien und jeder `<style>`-Block
  sind per `sha256` in der Richtlinie derselben Seite erlaubt. Lokale Skripte
  tragen zusätzlich `integrity`; moderne Browser verwenden `strict-dynamic`.
  Der vertrauenswürdige Statistik-Loader lädt ausschliesslich feste Anbieteradressen.
  Der geprüfte Ahrefs-Tracker ist zusätzlich durch SRI auf seine Bytes begrenzt.
  Erzeugt in [`build/render.py`](build/render.py) (`csp`, `sri_hash`).
* **Keine Ereignisattribute im HTML.** `onerror`, `onclick` und Verwandte gibt
  es nicht – sie liessen sich nicht per Hash erlauben und hätten
  `unsafe-inline` erzwungen.
* **`default-src 'none'`, `form-action 'self'`, `base-uri 'none'`,
  `object-src 'none'`, `frame-src 'none'`, `worker-src 'none'`,
  explizite Quellen für benötigte Ressourcen und `upgrade-insecure-requests`.**
* **HTTPS erzwungen** in der Pages-Konfiguration; `http://` und die Adresse
  ohne `www` leiten per 301 auf die kanonische Adresse um.
* **`referrer` auf `strict-origin-when-cross-origin`** – beim Klick auf ein
  Herstellerdokument erfährt die Gegenseite nur den Domainnamen.
* **Optionale Statistik und keine fremden Schriften.** Cloudflare
  Web Analytics lädt erst nach Zustimmung von `static.cloudflareinsights.com`
  und übermittelt Messdaten an `cloudflareinsights.com`. Ablehnen und Widerruf
  sind möglich. Ahrefs lädt nach derselben neuen Zustimmung von
  `analytics.ahrefs.com`. Der Loader prüft URL, Referrer, GPC/DNT, bekannte
  Produkt-IDs und vollständige registrierte Kampagnenkombinationen. Suchtexte,
  Kundennamen, E-Mail-Adressen und Nachrichtentexte sind keine Analytics-Properties.
  Eigene Kampagnenzuordnung liegt höchstens 24 Stunden in sessionStorage;
  bei Widerruf wird sie entfernt. Der Formulardienst `api.web3forms.com` und Herstellerbilder
  von `mahe-online.de` sind ebenfalls ausdrücklich in der CSP genannt. Auf
  unbekannten 404-Pfaden wird keine Statistik geladen; die Fehlerseite sendet
  keinen Referrer. Formular-POSTs verwenden ebenfalls `no-referrer`.
* **Datensparsame Formulare.** Persönliche Angaben werden nicht in localStorage
  gespeichert. Ohne Versandkonfiguration entstehen nur E-Mail-Entwürfe. Fehler
  führen zu keiner automatischen Wiederholung und löschen die Eingaben nicht.
  E-Mail-Entwürfe mit personenbezogenem Inhalt stehen nicht in Linkattributen.
  Capture-Listener schirmen sensible Linkziele vor automatischer Analytics ab;
  explizite Formularziele enthalten keine Parameter. Die automatische
  Formularmessung ist unterbunden, nur bestätigter Versand zählt als Erfolg.
* **Aktionen im Deploy sind auf Commit-Hashes festgenagelt**, nicht auf
  Etiketten – siehe [`.github/workflows/pages.yml`](.github/workflows/pages.yml).
* **Der Deploy liefert nur die Website aus.** Eine Positivliste kopiert die
  öffentlichen Dateien in ein separates Artefakt. Build-Quellen, Rohdaten,
  Konfiguration und private Berichte sind ausgeschlossen. Das GitHub-Repository
  selbst ist öffentlich; dort dürfen keine vertraulichen Berichte eingecheckt werden.

## Was hier bewusst nicht gilt

* **Kein Kopierschutz.** Keine Rechtsklick-Sperre, keine Verschleierung, kein
  DevTools-Blocker. Solche Massnahmen sind wirkungslos, schaden der
  Bedienbarkeit und der Barrierefreiheit, und Inhalt per JavaScript zu
  verstecken zerstört die Auffindbarkeit. Der Schutz liegt in `LICENSE`.
* **Kein `X-Frame-Options`, kein `X-Content-Type-Options`, kein HSTS.** Diese
  Kopfzeilen lassen sich auf GitHub Pages nicht setzen, und `frame-ancestors`
  ignorieren Browser, wenn es aus einem `<meta>` kommt. Das ist eine Grenze der
  Plattform, keine Nachlässigkeit.
* **Cache-Laufzeit wird vom Hosting bestimmt.** GitHub Pages liefert derzeit
  `Cache-Control: max-age=600`. Ein HTML-Meta-Tag verlaengert diesen HTTP-Cache
  nicht. Laengere Cache-Laufzeiten oder zusaetzliche Sicherheits-Header brauchen
  eine passende Hosting-/Proxy-Konfiguration. Es gibt keinen Service Worker,
  der lediglich eine Cache-Warnung versteckt und dabei alte Seiten festhaelt.

## Was der Betreiber noch tun muss

* **CAA vor Änderungen abstimmen.** Zulässige Zertifizierungsstellen müssen zum
  tatsächlichen Hosting und einem eventuell späteren Cloudflare-Proxy passen.
  Ein ungeprüfter restriktiver Eintrag kann die Zertifikatserneuerung verhindern.
* **Zwei-Faktor-Anmeldung** für GitHub, Infomaniak, Cloudflare und das Firmen-Mailkonto
  aktivieren und Wiederherstellungscodes privat verwahren. Ein nicht auslesbarer
  Kontostatus ist kein Beleg, dass 2FA ausgeschaltet ist.
* **Eigene Domain im GitHub-Konto verifizieren.** Das ist ein zusätzlicher
  Eigentumsnachweis gegen Übernahme bei späterer Trennung vom Pages-Projekt.
* **Unabhängige Sicherung:** lokale Sicherung auf einem verschlüsselten externen
  Datenträger oder bei einem unabhängigen Anbieter verwahren. GitHub-Repository
  und Actions-Artefakte allein sind keine Sicherung gegen Verlust des GitHub-Kontos.


## Automatische Kontrollen und Wiederherstellung

`build/security_check.py` prüft alle Inhaltsseiten einschliesslich 404 auf die
Skript-Hashes, SRI, CSP, Inline-Ereignisse, aktive unsichere URLs und POST-Formulare.
Die öffentliche Dateiauswahl bricht vor dem Kopieren ab, wenn in verwalteten
Ordnern ein unerwarteter Dateityp oder ein Symlink vorkommt. Ein legitimer
Dateiname beweist nicht, dass ein PDF oder Bild keinen vertraulichen Inhalt hat;
neue Inhalte müssen weiterhin vor dem Commit geprüft werden.

GitHub Secret Scanning und Push Protection, CodeQL für Actions/JavaScript/Python
sowie Dependabot-Sicherheitsmeldungen sind aktiviert. Aktionen müssen auf ganze
Commit-SHAs verweisen und von GitHub stammen. Das Hauptbranch darf nicht gelöscht
oder mit Force-Push überschrieben werden; normale Veröffentlichungen bleiben
möglich. Der Deploy-Job erhält als einziger Pages-/OIDC-Schreibrechte und darf nur
`main` in die Produktionsumgebung veröffentlichen. Pull Requests laufen durch
Build und Prüfungen, ohne Veröffentlichung oder Backup-Upload.

Die CLI-Werkzeuge verwenden `build/local_paths.py`: Dateizugriffe bleiben im
Projekt, in `Desktop`, `Downloads`, `Documents`, `Pictures`, temporaeren Ordnern
oder auf externen Datentraegern unter `/Volumes`. In GitHub Actions ist auch
`RUNNER_TEMP` erlaubt. Normalisierte Pfade werden mit einer Verzeichnisgrenze
verglichen; Symlinks duerfen diese Ablagen nicht verlassen. Paket- und
Wiederherstellungsziele behalten ihre zusaetzlichen Leerordner-/Symlinkpruefungen.
SQL-Exporte akzeptieren nur `.sql`, `.sqlite`, `.db` und `.sqlite3`.

Frontendtests importieren die gleichen Initialisierungsfunktionen wie der
Browser und uebergeben ihre DOM-/Storage-Abhaengigkeiten direkt. Sie fuehren
keinen eingelesenen Quelltext mit `vm`, `eval` oder `Function` aus. JSON-LD wird
mit einem HTML-Parser gelesen; die Inhaltskennung veraendert nur echte Starttags
und bewahrt Kommentare sowie Scriptdaten. Historische v1-Kopien werden nicht
veroeffentlicht; ihre Formularwerte werden ebenfalls vollstaendig als einzelne
mailto-Parameter kodiert. CodeQL bleibt fuer alle Quelldateien eingeschaltet;
Befunde werden durch Codekorrekturen und einen neuen Scan ueberprueft.

Jeder Produktionsbuild erstellt ein öffentliches Wiederherstellungsarchiv,
prüft SHA-256 und stellt es in einen leeren Testordner wieder her. GitHub hält das
separate Artefakt 7 Tage vor; ein fehlgeschlagener Deploy ist am Workflowstatus
zu erkennen. Seit dem 19.10.2026 wird erst nach erfolgreichem Deploy zusaetzlich
ein oeffentliches Recovery-Release am exakten Commit-Tag angelegt. Es besitzt
keine Actions-Ablauffrist. Nur dieser separate Job erhaelt die dafuer erforderlichen
Repository-Schreibrechte. Er prueft die Wiederherstellung und die SHA-256-Werte
der hochgeladenen Assets; abweichende vorhandene Dateien werden nicht ersetzt.
Nach erfolgreicher Veröffentlichung bewahrt die begrenzte Release-Aufbewahrung
den aktuellen Stand und eine geprüfte Vorversion. Sie löscht ausschliesslich
eindeutig zugeordnete ältere Recovery-Releases erfolgreicher Main-Deployments,
keine Git-Historie oder fremden Veröffentlichungen. Details stehen in BACKUP.md.
Vollständige lokale Sicherung, Grenzen und Wiederherstellung stehen
in [BACKUP.md](BACKUP.md). Weder die lokale Sicherung noch die Prüfsummen sind
verschlüsselt oder digital signiert. Kontozugänge und Kunden-E-Mails sind nicht
Bestandteil des öffentlichen Releases.

## Formularmissbrauch

Der Web3Forms-Formularkey ist absichtlich öffentlich. Pflichtfelder, Limits,
Honeypot und Doppelklickschutz verbessern das Browserverhalten, verhindern aber
keine direkten HTTP-Anfragen durch einen Angreifer. Die Basisspamprüfung des
Anbieters bleibt erforderlich. Bei Missbrauch oder erschöpftem Kontingent sind
serverseitig erzwungene CAPTCHA-Prüfung bzw. ein eigener validierender Endpunkt
nötig. CAPTCHA nur zusammen mit Providerkonfiguration, CSP, Datenschutzhinweis und
barrierefreiem Versandtest integrieren; ein sichtbares Widget allein genügt nicht.

## Vorfall und Rückkehr zu einem geprüften Stand

1. Bei Verdacht den betroffenen Zugang sperren/erneuern und Anmeldeprotokolle prüfen.
   Ein offengelegter privater Schlüssel muss widerrufen werden; Löschen aus Git genügt nicht.
2. Den letzten erfolgreichen Deploy und seine Commit-ID sichern. Kein Force-Push.
3. Ein vertrauenswürdiges Backup prüfen und separat wiederherstellen, wie in BACKUP.md.
4. Bereinigten Stand mit einem neuen Commit veröffentlichen. Formulare, CSP,
   Domain/HTTPS und Links auf dem Live-Web erneut prüfen.

Technische Referenzen: [GitHub Secret Scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning),
[Domain-Verifizierung](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages),
[CSP und Skript-Hashes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src),
[Grenze von frame-ancestors in Meta-Tags](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).

## Validierter Anfragekontext (21.09.2026)

Die funktionale Anfrageliste speichert in v2 nur Produkt-ID, Options-ID und Menge.
Gespeicherte Bezeichnungen, Bilder und URLs werden nicht vertraut, sondern aus
dem aktuellen vorgerenderten Katalog abgeleitet. Unbekannte Produkte/Optionen
werden verworfen oder im Kontakt sichtbar als ungültig gekennzeichnet.
Formulardaten und lokale Erfolgszusammenfassungen bleiben ausserhalb von
localStorage und Analytics. Analytics akzeptiert nur bekannte Produkt-/Options-
oder Serviceparameter auf der Kontaktseite und sendet deren kanonische URL ohne
Query. Der gewählte Varianten-/Geräteschlüssel wird nicht gemessen.

Seit dem 19.10.2026 werden Parameternamen aus Besucher-URLs ueberhaupt nicht mehr
als Objektschluessel verwendet. Es werden nur die expliziten erlaubten Felder
ueber URLSearchParams gelesen. Unbekannte, doppelte und prototypbezogene
Parameter halten die Statistik in allen fuenf Sprachen ausgeschaltet.
