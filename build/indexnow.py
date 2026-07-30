#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alle URLs per IndexNow anmelden.

IndexNow ist ein offenes Protokoll: statt zu warten, bis ein Crawler
vorbeischaut, meldet die Website ihre neuen und geänderten Seiten selbst.
Beteiligt sind **Bing, Yandex, Seznam und Naver** — eine Meldung an einen der
Endpunkte wird an alle weitergereicht.

**Google nimmt an IndexNow nicht teil.** Dort führt der Weg ausschliesslich über
die Search Console (Property verifizieren, sitemap.xml einreichen).

Voraussetzung: der Schlüssel liegt unter https://<host>/<key>.txt — das legt
build.py automatisch an. Vor dem ersten Aufruf muss die Datei also live sein.

Aufruf:
    python3 build/indexnow.py            # alle URLs aus der sitemap
    python3 build/indexnow.py /faq/ /produkte/   # nur einzelne Pfade
"""

import json
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

ENDPOINT = "https://api.indexnow.org/IndexNow"
BATCH = 10000          # Obergrenze des Protokolls pro Anfrage


def sitemap_urls():
    sm = C.ROOT / "sitemap.xml"
    if not sm.exists():
        print("sitemap.xml fehlt – zuerst build.py laufen lassen.")
        sys.exit(1)
    return re.findall(r"<loc>([^<]+)</loc>", sm.read_text("utf-8"))


def main():
    if not C.INDEXNOW_KEY:
        print("INDEXNOW_KEY in core.py ist leer – nichts zu tun.")
        sys.exit(1)

    host = C.SITE.split("//", 1)[1].rstrip("/")
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    urls = [C.abs_url(a if a.startswith("/") else "/" + a) for a in args] or sitemap_urls()

    # Der Schlüssel muss öffentlich erreichbar sein, sonst lehnt der Dienst ab.
    key_url = f"{C.SITE}/{C.INDEXNOW_KEY}.txt"
    probe = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                            "--max-time", "20", key_url], capture_output=True, text=True)
    if probe.stdout.strip() != "200":
        print(f"Schlüsseldatei nicht erreichbar ({probe.stdout.strip()}): {key_url}")
        print("Erst deployen, dann erneut aufrufen.")
        sys.exit(1)

    sent = 0
    for i in range(0, len(urls), BATCH):
        chunk = urls[i:i + BATCH]
        payload = json.dumps({
            "host": host,
            "key": C.INDEXNOW_KEY,
            "keyLocation": key_url,
            "urlList": chunk,
        })
        # 403 heisst "Schlüssel ungültig". Direkt nach dem ersten Deploy kommt das
        # auch dann, wenn die Datei erreichbar ist – der Dienst hat sie schlicht
        # noch nicht geholt. Deshalb ein paar Anläufe mit Pause.
        for attempt in range(1, 5):
            r = subprocess.run(
                ["curl", "-sS", "-X", "POST", ENDPOINT,
                 "-H", "Content-Type: application/json; charset=utf-8",
                 "--max-time", "60", "-w", "\n%{http_code}", "-d", payload],
                capture_output=True, text=True)
            code = r.stdout.strip().splitlines()[-1] if r.stdout else "?"
            # 200 = angenommen, 202 = angenommen, Schlüssel wird noch geprüft
            ok = code in ("200", "202")
            if ok or code != "403":
                break
            if attempt < 4:
                print(f"  HTTP 403 – Schlüssel noch nicht abgeholt, neuer Versuch in 20 s "
                      f"({attempt}/3)")
                time.sleep(20)
        print(f"  {len(chunk)} URLs → HTTP {code} {'ok' if ok else 'FEHLER'}")
        if ok:
            sent += len(chunk)

    print(f"\n{sent}/{len(urls)} URLs an Bing, Yandex, Seznam und Naver gemeldet.")
    print("Google beteiligt sich nicht an IndexNow – dort die Search Console nutzen.")


if __name__ == "__main__":
    main()
