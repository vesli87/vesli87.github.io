#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Die beiden Bilder der Startseiten-Diaschau erzeugen.

    python3 build/hero.py hero-mpt ~/Desktop/mpt.png
    python3 build/hero.py hero     ~/Desktop/schweisser.jpg
    python3 build/hero.py --pruefen              # nur nachrechnen

Warum ein eigenes Werkzeug und nicht images.py: die Herobilder kommen nicht von
mahe-online.de, sondern werden vom Inhaber geliefert. Sie brauchen andere
Breiten (bis 2048 statt 400) und ihre Masse stehen im HTML, weil das Bild die
Seite sonst beim Laden springen laesst.

Zwei Dinge macht dieses Skript richtig, die vorher von Hand falsch waren:

1. **Nie hochskalieren.** Die Vorlage hero-mpt.jpg war 1536 px breit, im srcset
   stand trotzdem eine Stufe "2048w" - erzeugt durch Hochrechnen. Ein Browser
   auf einem feinen Bildschirm waehlt genau diese Stufe und zieht ein weich
   gerechnetes Bild auf die volle Breite. Es sieht dadurch schlechter aus als
   die kleinere, scharfe Stufe. Hier entstehen nur Stufen bis zur echten
   Breite der Vorlage.

2. **Masse aus dem Bild, nicht aus einer Konstante.** width/height standen fest
   auf 1536x1024 - fuer beide Folien. Ein Bild im Format 16:9 haette die Seite
   beim Umschalten springen lassen. Die Masse landen jetzt in
   assets/img/hero-manifest.json und render.py liest sie von dort.
"""

import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/img"
MANIFEST = OUT / "hero-manifest.json"

# Angezeigt wird das Bild hoechstens 1536 CSS-Pixel breit (.hero-inner).
# Fuer Bildschirme mit doppelter Dichte lohnt die 2048er Stufe - aber nur,
# wenn die Vorlage sie hergibt.
STUFEN = [640, 1000, 1536, 2048]
NAMEN = ("hero", "hero-mpt")


def masse(p):
    """Breite und Hoehe einer Bilddatei, ueber sips (macOS, immer vorhanden)."""
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(p)],
                       capture_output=True, text=True)
    w = h = 0
    for zeile in r.stdout.splitlines():
        if "pixelWidth" in zeile:
            w = int(zeile.split(":")[1])
        elif "pixelHeight" in zeile:
            h = int(zeile.split(":")[1])
    if not w or not h:
        sys.exit(f"Konnte die Masse von {p} nicht lesen.")
    return w, h


def lade_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text("utf-8"))
    return {}


def erzeuge(name, quelle):
    quelle = pathlib.Path(quelle).expanduser()
    if not quelle.exists():
        sys.exit(f"Vorlage nicht gefunden: {quelle}")
    if not shutil.which("cwebp"):
        sys.exit("cwebp fehlt  ->  brew install webp")

    w, h = masse(quelle)
    print(f"Vorlage: {quelle.name}  {w} × {h} px")
    if w < 1200:
        print(f"  ACHTUNG: nur {w} px breit. Das Band ist bis 1536 px breit -")
        print("  das Bild wird auf grossen Bildschirmen sichtbar weich.")

    # Rueckfall fuer Browser ohne WebP: dieselbe Vorlage als JPEG.
    # Ist die Vorlage schon ein JPEG, wird sie kopiert statt neu kodiert - sonst
    # entsteht eine zweite Generation mit sichtbarem Qualitaetsverlust, und das
    # bei einer Datei, die niemand mehr als Vorlage hat.
    #
    # Kodiert wird mit Pillow, nicht mit sips. sips mit formatOptions 88 machte
    # aus einer 1536-px-Vorlage 364 kB; Pillow mit Qualitaet 82, progressiv und
    # optimierten Huffman-Tabellen kommt bei derselben Vorlage auf 209 kB - und
    # ist dabei naeher am Original, nicht weiter weg (PSNR 52.7 statt 49.8 dB).
    # Der Grund ist die Quantisierungstabelle: die Vorlage stammt selbst aus
    # einem JPEG, und Qualitaet 82 trifft deren Tabelle fast genau, sodass beim
    # zweiten Kodieren kaum neue Rundungsfehler entstehen.
    jpg = OUT / f"{name}.jpg"
    if quelle.suffix.lower() in (".jpg", ".jpeg"):
        shutil.copyfile(quelle, jpg)
    else:
        from PIL import Image
        Image.open(quelle).convert("RGB").save(
            jpg, "JPEG", quality=82, optimize=True, progressive=True)

    gemacht = []
    for stufe in STUFEN:
        if stufe > w:
            print(f"  {stufe:5} px  uebersprungen - Vorlage ist nur {w} px breit")
            continue
        ziel = OUT / f"{name}-{stufe}.webp"
        tmp = OUT / f"_{name}-{stufe}.png"
        subprocess.run(["sips", "-Z", str(stufe), "-s", "format", "png",
                        str(quelle), "--out", str(tmp)],
                       capture_output=True, check=True)
        subprocess.run(["cwebp", "-quiet", "-q", "86", "-sharp_yuv",
                        str(tmp), "-o", str(ziel)], check=True)
        tmp.unlink()
        bw, bh = masse(ziel)
        gemacht.append(bw)
        print(f"  {stufe:5} px  ->  {ziel.name:26} {bw} × {bh}  "
              f"{ziel.stat().st_size/1024:.0f} kB")

    # Alte, zu grosse Stufen wegraeumen - sonst bleiben hochgerechnete Dateien
    # liegen und das srcset zeigt weiter darauf.
    for stufe in STUFEN:
        if stufe > w:
            alt = OUT / f"{name}-{stufe}.webp"
            if alt.exists():
                alt.unlink()
                print(f"  entfernt: {alt.name} (war hochgerechnet)")

    m = lade_manifest()
    m[name] = {"w": w, "h": h, "sizes": gemacht}
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"\nassets/img/hero-manifest.json aktualisiert: {name} = {w}×{h}, "
          f"Stufen {gemacht}")
    print("Jetzt:  python3 build/build.py && python3 build/check.py")


def pruefen():
    """Nachrechnen, ob eine Stufe groesser ist als ihre Vorlage."""
    m = lade_manifest()
    fehler = 0
    for name in NAMEN:
        q = OUT / f"{name}.jpg"
        if not q.exists():
            print(f"  {name}: keine Vorlage {q.name}")
            continue
        w, h = masse(q)
        eintrag = m.get(name)
        print(f"  {name}: Vorlage {w} × {h}"
              + (f", Manifest {eintrag['w']} × {eintrag['h']}" if eintrag else ", NICHT im Manifest"))
        for stufe in STUFEN:
            f = OUT / f"{name}-{stufe}.webp"
            if not f.exists():
                continue
            bw, bh = masse(f)
            if bw > w:
                print(f"     FEHLER {f.name}: {bw} px breit, Vorlage nur {w} px - hochgerechnet")
                fehler += 1
            else:
                print(f"     ok     {f.name}: {bw} × {bh}")
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    if "--pruefen" in sys.argv:
        pruefen()
    elif len(sys.argv) == 3 and sys.argv[1] in NAMEN:
        erzeuge(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__.strip())
