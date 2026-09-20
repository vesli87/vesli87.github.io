# Sicherheit

Diese Website ist der Auftritt von VES-TECH Swiss, einem Einzelunternehmen in
der Schweiz. Sie besteht aus vorgerenderten HTML-Dateien auf GitHub Pages – es
gibt keine eigene Datenbank, keine Kundenanmeldung und keine Kundensitzungen.
Formularnachrichten werden bei aktivierter Konfiguration durch Web3Forms
verarbeitet; optionale Webstatistik durch Cloudflare. Details stehen in der
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
  Der vertrauenswürdige Statistik-Loader lädt ausschliesslich die feste Cloudflare-Adresse.
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
* **Keine Analyse-Cookies und keine fremden Schriften.** Optionales Cloudflare
  Web Analytics lädt erst nach Zustimmung von `static.cloudflareinsights.com`
  und übermittelt Messdaten an `cloudflareinsights.com`. Ablehnen und Widerruf
  sind möglich. Der Formulardienst `api.web3forms.com` und Herstellerbilder
  von `mahe-online.de` sind ebenfalls ausdrücklich in der CSP genannt. Auf
  unbekannten 404-Pfaden wird keine Statistik geladen; die Fehlerseite sendet
  keinen Referrer. Formular-POSTs verwenden ebenfalls `no-referrer`.
* **Datensparsame Formulare.** Persönliche Angaben werden nicht in localStorage
  gespeichert. Ohne Versandkonfiguration entstehen nur E-Mail-Entwürfe. Fehler
  führen zu keiner automatischen Wiederholung und löschen die Eingaben nicht.
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

CodeQL-Befunde werden nach erreichbarem Angriffspfad geprüft. Ausführung des
bekannten Frontend-Quelltexts in den Regressionstests und beabsichtigte lokale
CLI-Ein-/Ausgabepfade sind nicht automatisch eine aus dem Internet erreichbare
Codeausführung. Das alte `build/source-snapshot.html` und Extraktionsdateien
gehören zum historischen Archiv, werden nicht ausgeliefert und dürfen nicht als
Produktionsfrontend wiederverwendet werden.

Jeder Produktionsbuild erstellt ein öffentliches Wiederherstellungsarchiv,
prüft SHA-256 und stellt es in einen leeren Testordner wieder her. GitHub hält das
separate Artefakt 90 Tage vor; ein fehlgeschlagener Deploy ist am Workflowstatus
zu erkennen. Vollständige lokale Sicherung, Grenzen und Wiederherstellung stehen
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
