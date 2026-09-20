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
  Stile. Jedes Inline-Skript und jeder `<style>`-Block ist per `sha256` in der
  Richtlinie derselben Seite erlaubt; alles andere führt der Browser nicht aus.
  Erzeugt in [`build/render.py`](build/render.py) (`csp`, `sri_hash`).
* **Keine Ereignisattribute im HTML.** `onerror`, `onclick` und Verwandte gibt
  es nicht – sie liessen sich nicht per Hash erlauben und hätten
  `unsafe-inline` erzwungen.
* **`form-action 'self'`, `base-uri 'self'`, `object-src 'none'`,
  `frame-src 'none'`, `upgrade-insecure-requests`.**
* **HTTPS erzwungen** in der Pages-Konfiguration; `http://` und die Adresse
  ohne `www` leiten per 301 auf die kanonische Adresse um.
* **`referrer` auf `strict-origin-when-cross-origin`** – beim Klick auf ein
  Herstellerdokument erfährt die Gegenseite nur den Domainnamen.
* **Keine Analyse-Cookies und keine fremden Schriften.** Optionales Cloudflare
  Web Analytics lädt erst nach Zustimmung von `static.cloudflareinsights.com`
  und übermittelt Messdaten an `cloudflareinsights.com`. Ablehnen und Widerruf
  sind möglich. Der Formulardienst `api.web3forms.com` und Herstellerbilder
  von `mahe-online.de` sind ebenfalls ausdrücklich in der CSP genannt.
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
* **Zwei-Faktor-Anmeldung** für das GitHub-Konto, über das veröffentlicht wird.
