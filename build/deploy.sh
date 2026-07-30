#!/usr/bin/env bash
# VES-TECH Swiss — Repository anlegen und auf GitHub Pages veröffentlichen.
#
# Voraussetzung (einmalig, interaktiv):
#     gh auth login
#
# Danach:
#     bash build/deploy.sh
#
# Das Skript ist idempotent: existiert das Repository bereits, wird nur gepusht.

set -euo pipefail

OWNER="vesli87"
REPO="vesli87.github.io"        # user page -> läuft direkt auf https://vesli87.github.io/
VISIBILITY="--private"          # GitHub Pages aus privaten Repos braucht GitHub Pro
DOMAIN="www.ves-tech.ch"

cd "$(dirname "$0")/.."

echo "==> Build und QA"
python3 build/build.py
python3 build/check.py

echo "==> Anmeldung prüfen"
if ! gh auth status >/dev/null 2>&1; then
  echo "Nicht angemeldet. Bitte zuerst ausführen:  gh auth login"
  exit 1
fi

echo "==> Änderungen committen (falls vorhanden)"
git add -A
git diff --cached --quiet || git commit -m "Build: Seiten neu erzeugt"

# Push läuft über HTTPS mit dem OAuth-Token von gh. Der SSH-Weg braucht bei
# jedem Push die Passphrase und schlägt fehl, wenn der Schlüssel nicht im Agent
# liegt – das ist bei einem reinen Deploy-Skript nur im Weg.
echo "==> Git auf HTTPS mit gh-Token umstellen"
gh auth setup-git
REMOTE="https://github.com/$OWNER/$REPO.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "==> Repository existiert bereits – Zustand prüfen"
  git fetch origin --quiet 2>/dev/null || true
  if git rev-parse --verify --quiet origin/main >/dev/null; then
    AHEAD=$(git rev-list --count main..origin/main)
    if [ "$AHEAD" -gt 0 ]; then
      echo
      echo "STOP: origin/main hat $AHEAD Commit(s), die lokal fehlen:"
      git log --oneline main..origin/main | sed 's/^/    /'
      echo
      echo "Ein Push würde diesen Stand verwerfen. Bitte entscheiden:"
      echo "  a) Fremden Stand übernehmen und darauf aufsetzen:"
      echo "       git pull --rebase origin main && git push -u origin main"
      echo "  b) Fremden Stand bewusst verwerfen (nur wenn dort nur ein"
      echo "     Platzhalter-README liegt):"
      echo "       git push -u --force-with-lease origin main"
      exit 1
    fi
  fi
  echo "==> Pushe nach main"
  git push -u origin main
else
  echo "==> Repository anlegen und pushen"
  gh repo create "$REPO" $VISIBILITY --source=. --remote=origin --push \
     --description "VES-TECH Swiss – MAHE Schweisstechnik, dreisprachiger Katalog (DE/FR/IT)"
fi

echo "==> GitHub Pages auf den Actions-Workflow umstellen"
gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow 2>/dev/null \
  || gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow 2>/dev/null \
  || echo "   Hinweis: Pages liess sich nicht per API aktivieren."
echo "   Bei einem privaten Repository braucht GitHub Pages einen bezahlten Plan."
echo "   Falls der Deploy scheitert:  gh repo edit $OWNER/$REPO --visibility public"

echo
echo "Fertig."
echo "  Actions:  https://github.com/$OWNER/$REPO/actions"
echo "  Vorschau: https://$OWNER.github.io/"
echo
echo "Eigene Domain ($DOMAIN) – DNS beim Registrar setzen:"
echo "  CNAME  www   ->  $OWNER.github.io."
echo "  A      @     ->  185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153"
echo "Die Datei CNAME im Repository setzt die Domain in GitHub Pages automatisch."
