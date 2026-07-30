#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schriften selbst hosten statt von Google Fonts laden.

Warum:
  * Tempo — fonts.googleapis.com und fonts.gstatic.com sind zwei zusätzliche
    DNS-Auflösungen und TLS-Handshakes, bevor der erste Buchstabe erscheint.
    Vom eigenen Host kommen sie über die bereits offene Verbindung.
  * Datenschutz — Google Fonts überträgt die IP-Adresse jedes Besuchers nach
    Irland/USA. In der Schweiz und der EU ist das heikel; selbst gehostet
    entfällt der Punkt in der Datenschutzerklärung ersatzlos.
  * Ausfallsicherheit — die Seite hängt nicht an einem fremden CDN.

Es werden nur die Subsets `latin` und `latin-ext` geladen; Kyrillisch, Griechisch
und Vietnamesisch braucht eine deutsch/französisch/italienische Website nicht.

Aufruf:  python3 build/fonts.py
Lizenz:  Anton, Barlow Condensed, Bodoni Moda und Inter stehen unter der
         SIL Open Font License 1.1 und dürfen selbst gehostet werden.
"""

import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

# Inter und Bodoni Moda werden als variable Schrift angefordert (wght@400..700
# statt einzelner Schnitte): eine Datei deckt alle Hilfsgewichte ab, statt vier
# nahezu gleich grosse Dateien zu laden. Anton hat nur einen Schnitt, Barlow
# Condensed bietet Google nicht als variable Schrift an – beide bleiben statisch.
GOOGLE_CSS = ("https://fonts.googleapis.com/css2"
              "?family=Anton"
              "&family=Barlow+Condensed:wght@600;700"
              "&family=Bodoni+Moda:opsz,wght@6..96,600..700"
              "&family=Inter:wght@400..700"
              "&display=swap")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

KEEP_SUBSETS = {"latin", "latin-ext"}
OUT = C.ROOT / "assets" / "fonts"


def fetch(url, dest=None):
    cmd = ["curl", "-sSL", "--max-time", "60", "-A", UA, url]
    if dest:
        cmd += ["-o", str(dest)]
        return subprocess.run(cmd, capture_output=True).returncode == 0
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    css = fetch(GOOGLE_CSS)
    if "@font-face" not in css:
        print("Google Fonts lieferte kein CSS – Abbruch.")
        sys.exit(1)

    # Jeder Block sieht so aus:  /* latin */\n@font-face { ... }
    blocks = re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
    out, files, skipped = [], 0, 0

    out.append("/* Selbst gehostete Schriften – erzeugt von build/fonts.py.\n"
               "   Nicht von Hand bearbeiten. Quelle: Google Fonts, SIL OFL 1.1.\n"
               "   Subsets: latin, latin-ext. */\n")

    for subset, block in blocks:
        if subset not in KEEP_SUBSETS:
            skipped += 1
            continue
        m = re.search(r"src:\s*url\((https://[^)]+\.woff2)\)", block)
        fam = re.search(r"font-family:\s*'([^']+)'", block)
        wght = re.search(r"font-weight:\s*([^;]+);", block)
        if not m or not fam:
            continue
        url = m.group(1)
        w = (wght.group(1) if wght else "400").replace(" ", "-")
        name = f"{C.slugify(fam.group(1))}-{w}-{subset}.woff2"
        if not (OUT / name).exists():
            if not fetch(url, OUT / name):
                print(f"  Download fehlgeschlagen: {name}")
                continue
        files += 1
        out.append(block.replace(url, f"/assets/fonts/{name}"))

    (OUT / "fonts.css").write_text("\n".join(out) + "\n", "utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.woff2"))
    print(f"{files} Schriftdateien, {skipped} fremde Subsets übersprungen")
    print(f"assets/fonts: {total/1024:.0f} kB + fonts.css")


if __name__ == "__main__":
    main()
