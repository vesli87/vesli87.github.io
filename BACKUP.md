# VES-TECH: Sicherung und Wiederherstellung

Die Website lässt sich aus Git, den Produktdaten und den Bildern neu bauen. Das
allein sichert jedoch weder Kontozugänge noch lokale Konfiguration oder
Kundenkorrespondenz. `build/backup.py` trennt deshalb eine lokale Projektsicherung
von einem ausdrücklich öffentlichen Release-Archiv. Python 3.9+ und Git genügen;
es werden keine zusätzlichen Pakete, Cloudkonten oder kostenpflichtigen Dienste
benötigt.

## Was gesichert wird

| Bestandteil | Lokale Projektsicherung | Öffentliches Release |
|---|---|---|
| `public-site.tar.gz` | Ja | Ja |
| `source.tar.gz` | Ja | Nein |
| `repository.bundle` | Ja | Nein |
| `manifest.json`, `SHA256SUMS` | Ja | Ja |
| Lokale Konfiguration, Reports, Zugangsdaten | Nein | Nein |

`public-site.tar.gz` enthält ausschliesslich erlaubte Webdateien: das fertig
gebaute HTML, öffentliche Such-/Produktdaten, Bilder, CSS, JavaScript,
Verifizierungsdateien und `.well-known/security.txt`. Es entsteht aus dem
öffentlichen Paket von `build/package_site.py`. Der eigene Filter des
Backupwerkzeugs prüft die Dateipfade erneut.

`source.tar.gz` enthält den gegenwärtigen Inhalt der von Git **verfolgten**
Dateien, einschliesslich noch nicht committeter Änderungen. Verfolgte und lokal
gelöschte Dateien bleiben auch nach der Wiederherstellung gelöscht. Unverfolgte
Dateien sind ausgeschlossen. Neue, geprüfte Quelldateien daher vor der Sicherung
gezielt zu Git hinzufügen oder committen; nicht ungeprüft `git add .` verwenden.
Der Indexzustand wird nicht separat gesichert: offene Änderungen erscheinen nach
der Wiederherstellung als Änderungen gegenüber dem gesicherten Commit.

`repository.bundle` enthält die lokal vorhandene, über Git-Referenzen und `HEAD`
erreichbare Historie mit Branches und Tags. Es holt **nicht** automatisch neue
Remote-Branches. Reflog und unerreichbare, bereits verwaiste Objekte sind keine
Bestandteile dieser Sicherung. Ein flacher Git-Klon wird für die volle Sicherung
abgewiesen. Git-Konfiguration, lokale Hooks, Anmeldetoken und Remote-Zugangsdaten
werden nicht kopiert. Das öffentliche `.claude/launch.json` mit dem lokalen
Vorschaukommando darf in der Quellsicherung bleiben; private Assistenten- und
Kontoeinstellungen sind ausgeschlossen.

Die volle Sicherung ist für die lokale Ablage bestimmt und wird **nie** als
öffentliches GitHub-Artefakt oder als Teil der Website hochgeladen. Selbst bei
einem öffentlichen Repository kann sie noch unveröffentlichte Arbeitsstände
enthalten.

## Lokale Sicherung erstellen

Vorher die gewünschten Änderungen prüfen und einen konsistenten Stand bauen:

```sh
git status --short
python3 build/build.py
python3 build/check.py
python3 build/audit.py
python3 build/backup.py create --output reports/backups/2026-09-20-geprueft
```

Der Zielordner darf noch nicht existieren. Bereits vorhandene Sicherungen werden
nie überschrieben. Innerhalb des Projekts sind nur neue Unterordner von
`reports/backups/` als Sicherungsziel erlaubt; dieser Bereich ist von Git und
Deployment ausgeschlossen. Für weitere Sicherungen einen neuen Namen verwenden.
Die Erzeugung prüft anschliessend automatisch alle Prüfsummen, Archivpfade und das
Git-Bundle. Ein unvollständiger Lauf hinterlässt keine scheinbar gültige Sicherung.

Auch ein expliziter Pfad ausserhalb des Projekts ist möglich. Ein Ordner unter
`/tmp` eignet sich für einen Wiederherstellungstest, **nicht** für dauerhafte
Aufbewahrung.

## Öffentliches Release für GitHub Actions

Nach dem normalen Build und dessen Prüfungen kann CI das bereits begrenzte
öffentliche Paket übernehmen:

```sh
python3 build/backup.py create --public-only \
  --public-dir "$RUNNER_TEMP/site" \
  --output "$RUNNER_TEMP/public-backup"
```

Dieser Modus benötigt kein Git-Repository und erzeugt genau drei Dateien:
`public-site.tar.gz`, `manifest.json`, `SHA256SUMS`. Sein Manifest enthält keine
Repository-, Account- oder Konfigurationsmetadaten. Nur dieser Ordner darf als
öffentliches Sicherungsartefakt hochgeladen werden. Der Pages-Upload verwendet
weiterhin den gewöhnlichen Websiteordner, nicht das Backup-Archiv.

Der Workflow erzeugt bei jedem Push auf `main` ein geprüftes öffentliches
Sicherungsarchiv, führt einen Wiederherstellungstest aus und bewahrt das Archiv
eines erfolgreichen Deployments für 90 Tage auf. Auch ein manuell gestarteter
Workflow verwendet diese Prüfungen. Artefakte können durch Ablauf, manuelles Löschen oder Verlust des
GitHub-Kontos verschwinden. GitHub-Repository und GitHub-Artefakte sind dieselbe
Anbieterabhängigkeit, keine unabhängige Zweitsicherung.

## Sicherung prüfen

```sh
python3 build/backup.py verify reports/backups/2026-09-20-geprueft
```

Das Werkzeug kontrolliert SHA-256 für alle Komponenten und jede archivierte
Datei, Dateigrössen, erlaubte Pfade, eindeutige Dateinamen und bei einer lokalen
Projektsicherung die Vollständigkeit des Git-Bundles. Pfade mit `..`, absolute
Pfade, Windows-Laufwerkspfade, Symlinks, Hardlinks, Geräte, FIFO-Dateien und doppelte
Archivmitglieder werden verworfen. Grössen- und Dateianzahllimits begrenzen die
Dekomprimierung. Verbotene private Pfade in der Git-Historie führen schon beim
Erstellen zum Abbruch, selbst wenn die Datei später gelöscht wurde.

Die Dateinamenprüfung ersetzt keine inhaltliche Prüfung neuer Quelldateien auf
Geheimnisse. Ein Token in einer gewöhnlich benannten Datei wird nicht allein
anhand seines Namens erkannt. SHA-256 erkennt Beschädigung, ist aber keine digitale
Signatur: Wer Archiv, Manifest und Prüfsummen gemeinsam austauscht, kann auch neue
Prüfsummen erzeugen. Sicherungen aus einer vertrauenswürdigen Ablage verwenden.

## Wiederherstellung testen oder durchführen

Zuerst prüfen, dann in einen **neuen oder leeren** Ordner wiederherstellen:

```sh
python3 build/backup.py restore reports/backups/2026-09-20-geprueft \
  --output /tmp/ves-tech-wiederherstellung
```

Eine lokale Projektsicherung erzeugt:

- `repository/`: Quellstand und lokale Git-Historie;
- `public-site/`: das exakt archivierte öffentliche Release.

Eine öffentliche Sicherung erzeugt nur `public-site/`. Sie kann den sichtbaren
Webauftritt wiederherstellen, ersetzt aber keine Quellcode-Historie für die
weitere Bearbeitung. Der vorhandene Arbeitsordner und die Live-Website werden
nicht verändert. Bestehende Dateien im Ziel werden nie überschrieben.

Die Wiederherstellung entpackt Dateien einzeln mit kontrollierten Pfaden und
übernimmt weder fremde Eigentümer noch spezielle Dateirechte. Git wird ohne
Checkout der historischen Dateien initialisiert; das Archiv liefert den
Arbeitsstand. Alle enthaltenen Referenzen bleiben verfügbar. `HEAD` steht bewusst
auf dem gesicherten Commit, ohne einen bestehenden Branch zu verschieben. Zum
Weiterarbeiten einen eigenen Branch anlegen:

```sh
cd /tmp/ves-tech-wiederherstellung/repository
git status --short
git switch -c recovery/gepruefter-stand
python3 build/build.py
python3 build/check.py
python3 build/audit.py
```

Der neue Build verwendet die vorhandene öffentliche Konfiguration. Weil private
Konfiguration bewusst fehlt, kann das Kontaktformular bis zur erneuten Einrichtung
nur einen E-Mail-Entwurf anbieten. Der unveränderte archivierte Ordner
`public-site/` bleibt daneben als Beleg des gesicherten Releases erhalten.
Vor einer erneuten Veröffentlichung Versandkonfiguration, Domain, Hosting und
Verifizierung prüfen. Das Werkzeug führt keinen Push und keinen Live-Deploy aus.
Eine erneute GitHub-Verbindung wird bewusst manuell mit der sauberen Repository-URL
konfiguriert, ohne Zugangstoken in der URL.

## Was separat verwahrt werden muss

- `build/config.local.json`, sofern benötigt, ausschliesslich in einer geeigneten
  privaten, verschlüsselten Sicherung oder im Passwortmanager;
- die Einrichtung des Actions-Secrets `WEB3FORMS_KEY` und der Zugang zu Web3Forms;
- GitHub, Cloudflare, Google/Bing und Infomaniak: Zugang, Zwei-Faktor-Wiederherstellung
  und Eigentumsnachweise;
- DNS-Zone und Hostingkonfiguration sowie geschäftliche E-Mails und Kundenunterlagen.

GitHub-Secrets sind kein auslesbares Backup. Das Tool behauptet deshalb ausdrücklich
nicht, diese Daten wiederherstellen zu können. Der im Browser sichtbare
Web3Forms-Formularkey und der Cloudflare-Beacon-Token sind öffentliche
Frontend-Konfiguration; administrative API-Schlüssel gehören niemals ins Projekt.

Bei der Einrichtung am 20.09.2026 wurde kein aktives Time-Machine-Ziel und kein
angeschlossener externer Sicherungsdatenträger festgestellt. Die lokale Sicherung
ist **nicht verschlüsselt**. Beschränkte Ordnerrechte ersetzen keine Verschlüsselung.
Eine Kopie auf derselben Festplatte fällt bei einem Defekt oder Verlust des
Rechners zusammen mit dem Original aus. Die lokale Sicherung und GitHub verbessern
die Wiederherstellbarkeit, erfüllen damit aber noch keine
3-2-1-Strategie. Mindestens eine geprüfte Kopie sollte zusätzlich auf einem vom
Arbeitsrechner und GitHub unabhängigen, vom Inhaber verwalteten Datenträger liegen.
Dieses Werkzeug richtet einen solchen Speicher nicht heimlich ein und bucht keinen
Dienst. Alte Sicherungen werden nicht automatisch gelöscht.

Ein Wiederherstellungstest gehört nach grösseren Änderungen an Generator,
Dateistruktur oder Deployment dazu. Der Test ist erst erfolgreich, wenn die
Prüfsummen stimmen, die Historie lesbar ist und der wiederhergestellte Quellstand
Build, Seitenprüfung und Audit besteht.
