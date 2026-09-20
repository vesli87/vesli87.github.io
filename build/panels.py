#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontpanel-Fotos des Herstellers importieren.

    python3 build/panels.py ~/Downloads/OneDrive_1_1.8.2026

Anders als build/images.py holt dieses Skript nichts aus dem Netz, sondern
übernimmt Dateien, die MAHE direkt geliefert hat. Die Originale liegen mit bis
zu 6377 px Breite vor; ausgeliefert werden 400 px und 1000 px als WebP.

Die Einträge landen im selben assets/img/manifest.json wie die Produktbilder,
mit dem Schlüssel `panels/<Dateiname>` und dem Vermerk `"local": true` — daran
erkennt render.img_tag, dass es keinen Rückfall auf mahe-online.de gibt.
"""

import json
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

OUT = C.ROOT / "assets" / "img" / "panels"
MANIFEST = C.ROOT / "assets" / "img" / "manifest.json"
# Jede Stufe nur, wenn die Vorlage wirklich so breit ist - hochskalieren macht
# Bilder nicht schaerfer, nur groesser. Welche Stufen entstanden sind, steht
# danach im Manifest, damit render.img_tag kein Bild ins srcset schreibt, das
# es nicht gibt.
#
# 3000 kam am 12.08.2026 dazu, fuer die Lupe. Sie nimmt die groesste Stufe des
# srcset (app.js::gross) und zeigt das Bild auf Wunsch in seiner natuerlichen
# Groesse. Bei 2000 px war dort Schluss, obwohl die MPT-Vorlage 3344 px breit
# ist - auf einem feinen Bildschirm wurde das Bild in der Lupe also weich, und
# genau dort schaut jemand die Maschine und den Monitor genau an.
# In die normale Auswahl geraet die Stufe nicht: der Bildschlitz ist hoechstens
# 534 px breit, bei doppelter Punktdichte also 1068 - der Browser nimmt die
# 1600er. Die 3000er laedt nur, wer die Lupe oeffnet.
SIZES = [400, 1000, 1600, 2000, 3000]


def dims(f):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(f)],
                       capture_output=True, text=True)
    w = re.search(r"pixelWidth:\s*(\d+)", r.stdout)
    h = re.search(r"pixelHeight:\s*(\d+)", r.stdout)
    return (int(w.group(1)), int(h.group(1))) if w and h else (0, 0)


def key_for(name):
    return C.slugify(pathlib.PurePosixPath(name).stem)


def ausgabe_pruefen(path):
    for entry in (path, *path.parents):
        if entry == C.ROOT:
            break
        if entry.is_symlink():
            sys.exit(f"Verknuepfung als Ausgabe nicht erlaubt: {entry}")
    if path.exists() and not path.is_file():
        sys.exit(f"Ausgabe ist keine normale Datei: {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = pathlib.Path(sys.argv[1]).expanduser().resolve()
    if not src.is_dir():
        print(f"Ordner nicht gefunden: {src}")
        sys.exit(1)

    ausgabe_pruefen(MANIFEST)
    if OUT.is_symlink():
        sys.exit(f"Verknuepfung als Ausgabe nicht erlaubt: {OUT}")
    manifest = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}

    files = sorted(f for f in src.iterdir()
                   if f.suffix.lower() in (".png", ".jpg", ".jpeg"))
    # Manufacturer filenames are not output paths. Reject ambiguous slugs
    # instead of silently making two manifest entries point at the last image.
    keys = {value['key']: name for name, value in manifest.items()
            if name.startswith('panels/')}
    for f in files:
        if f.is_symlink() or not f.is_file():
            sys.exit(f"Vorlage ist keine normale Datei: {f}")
        k = key_for(f.name)
        if not k or (k in keys and keys[k] != f"panels/{f.name}"):
            sys.exit(f"Nicht eindeutiger Bildname: {f.name}")
        keys[k] = f"panels/{f.name}"
        for target in OUT.glob(f"{k}-*.webp"):
            ausgabe_pruefen(target)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(files)} Dateien in {src.name}\n")

    for f in files:
        k = key_for(f.name)
        w, h = dims(f)
        if not w:
            print(f"  unlesbar: {f.name}")
            continue
        stufen = []
        for nenn in SIZES:
            ziel = min(nenn, w)
            if ziel not in stufen:
                stufen.append(ziel)
        for s in stufen:
            ausgabe_pruefen(OUT / f"{k}-{s}.webp")
        # Only replace existing images once every size of this input succeeded.
        # Failed conversions must not publish partial files or delete old sizes.
        with tempfile.TemporaryDirectory(prefix=".panels-", dir=OUT) as temp:
            for s in stufen:
                dst = pathlib.Path(temp) / f"{k}-{s}.webp"
                subprocess.run(["cwebp", "-quiet", "-q", "86", "-alpha_q", "90",
                                "-sharp_yuv", "-resize", str(s), "0",
                                str(f), "-o", str(dst)],
                               capture_output=True, check=True)
            for s in stufen:
                (pathlib.Path(temp) / f"{k}-{s}.webp").replace(OUT / f"{k}-{s}.webp")
        # Stufen aufraeumen, die es zu einer frueheren, groesseren Vorlage
        # einmal gab. Ohne das bleiben sie mit dem ALTEN Bildinhalt liegen:
        # am 13.08.2026 loeste eine 1672 px breite Vorlage die 3344 px breite
        # ab, und -2000.webp sowie -3000.webp standen weiter im Verzeichnis,
        # zeigten noch das alte Motiv und wurden mit ausgeliefert. hero.py
        # macht das seit jeher richtig; hier fehlte es.
        for veraltet in OUT.glob(f"{k}-*.webp"):
            try:
                breite = int(veraltet.stem.rsplit("-", 1)[1])
            except (IndexError, ValueError):
                continue
            if breite not in stufen:
                veraltet.unlink()
                print(f"    entfernt: {veraltet.name} (Stufe gibt es nicht mehr)")

        manifest[f"panels/{f.name}"] = {"key": k, "w": w, "h": h,
                                        "ratio": round(h / w, 4), "local": True,
                                        "sizes": stufen}
        print(f"  {f.name:44} {w}×{h}  ->  {k}")

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    total = sum(x.stat().st_size for x in OUT.glob("*.webp"))
    print(f"\nassets/img/panels: {len(list(OUT.glob('*.webp')))} Dateien, "
          f"{total/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
